"""Passage evidence, abstention and diversity for extractive retrieval."""
from dataclasses import dataclass
import math
import re

from .query import normalize, terms

DEFAULT_DEPTH = 5
# Match requests for exact details where a general explanation is insufficient.
_PRECISE = re.compile(
    r"\b(?:синтаксис|квот\w*|проходн\w*|по шагам|пошагов\w*|в какое время|вычислить вероятность|флаг\w+\s+cli|параметр\w*|"
    r"точн\w+\s+(?:числ\w*|балл\w*|значени\w*)|какие\s+команд\w*|"
    r"what flag|exact (?:limit|score|syntax)|which parameter)\b", re.I
)
_OVERVIEW = re.compile(r"^(?:задача|постановка задачи|условие|на собеседовании|что оценивают|для кого этот план|цель проверки)$")
_DEICTIC = re.compile(r"\b(?:этот|этом|этого|этому|этой|это|этим|this|that)\s+(?:этап\w*|шаг\w*|случа\w*|способ\w*|stage|step)\b", re.I)


@dataclass(frozen=True)
class SectionEvidence:
    index: int
    text: str
    terms: frozenset
    matched: frozenset
    score: float


@dataclass(frozen=True)
class Candidate:
    card: str
    score: float
    admitted: bool
    reason: str
    blocks: tuple


class EvidenceScorer:
    def __init__(self, engine, query, ranked, evidence, lexical, dense, depth, method):
        import numpy as np

        self.engine = engine
        self.query = query
        self.ranked = ranked[:depth]
        self.evidence = evidence
        self.lexical = lexical
        self.dense = dense
        self.method = method
        self.weights = {word: min(engine.idf.get(word, 3.1), 3.1) for word in query.tokens}
        self.total = sum(self.weights.values()) or 1.0
        self.known = {word for word in self.weights if word in engine.idf}
        top = max((evidence[c][0] for c in ranked), default=0.0)
        median = float(np.median(dense))
        # A query-relative semantic signal is used for section ordering. The
        # admission decision also uses an absolute floor for each encoder family.
        self.median = median
        self.scale = max(.08, top - median)
        self.e5 = bool(engine.metadata.get("query_prefix"))
        self.peak = top
        leading = sorted((evidence[c][0] for c in ranked), reverse=True)[:2]
        self.next_peak = leading[1] if len(leading) == 2 else median
        self.precise = bool(_PRECISE.search(query.normalized) or re.search(r"\b\d+\.\d+\b", query.raw))
        self.lex_peak = max(float(lexical.max()), 1.0)
        self.titles = engine.name_terms
        self.anchors = {token for word in re.findall(r"\b[A-Z]{2,6}\b", query.raw)
                        for token in terms(word) if token in engine.named_terms}
        self.strong_unknown = {
            token for word in re.findall(r"\b[A-Za-z][A-Za-z0-9_]{2,}\b", query.raw)
            if "_" in word or re.search(r"[a-z][A-Z]|[A-Z]{2,}[a-z]|[a-z]\d", word)
            or (word.isupper() and len(word) >= 3)
            for token in terms(word) if token in self.weights and token not in self.known
        }

    def cover(self, observed):
        return sum(self.weights.get(w, 0.0) for w in observed) / self.total

    def _blocks(self, card):
        engine = self.engine
        sections = {}
        for ix in engine.cards[card]:
            passage = engine.passages[ix]
            body = engine.body_terms[ix]
            names = self.titles[card]
            match = frozenset(body & self.weights.keys())
            local = self.cover(match)
            lexical = math.log1p(float(self.lexical[ix])) / math.log1p(self.lex_peak)
            sem = (float(self.dense[ix]) - self.median) / self.scale
            score = .53 * sem + .23 * local + .16 * lexical
            score += .11 * self.query.heading_signal(" ".join(passage.heading))
            heading = normalize(passage.heading[-1]) if passage.heading else ""
            definition = "definition" in self.query.intents
            if _OVERVIEW.match(heading) and not definition:
                score -= .14
            if not definition and ("mechanism" in self.query.intents or "practice" in self.query.intents):
                if heading.startswith(("как это", "как устроен", "как работает", "как примен", "реализац",
                                       "подход к", "архитектур", "алгоритм", "модель данных")):
                    score += .08
            if definition and self.weights and self.weights.keys() <= names:
                score += .13 * any(normalize(h).startswith(("определ", "что такое", "суть", "назнач")) for h in passage.heading)
            previous = sections.get(passage.section)
            if previous is None or score > previous[0]:
                sections[passage.section] = (score, ix)
        output = []
        for section, (score, ix) in sections.items():
            passage = engine.passages[ix]
            parent = engine.section_text[card, section]
            text = parent if len(parent) <= 1550 else passage.text
            body = engine.section_terms[card, section] if text == parent else engine.body_terms[ix]
            match = frozenset((body | set(terms(" ".join(passage.heading)))) & self.weights.keys())
            if len(text) <= 3500:
                output.append(SectionEvidence(ix, text, body, match, score))
        return tuple(sorted(output, key=lambda b: (-b.score, b.index)))

    def assess(self, card, position):
        blocks = self._blocks(card)
        cosine, coverage = self.evidence[card]
        names = self.titles[card]
        named = self.cover(names & self.weights.keys())
        exact = bool(self.weights and self.weights.keys() <= names)
        best_coverage = max((self.cover(b.matched) for b in blocks[:4]), default=0)
        relative = (cosine - self.median) / self.scale
        lexical_position = max((self.lexical[b.index] for b in blocks), default=0) / self.lex_peak
        gap = self.peak - cosine
        strength = (.46 * relative + .32 * coverage + .32 * best_coverage + .20 * named
                    + .13 * lexical_position + .19 / (position + 1))
        if self.anchors:
            strength += .19 * len(self.anchors & names) / len(self.anchors)
        if exact and "definition" in self.query.intents:
            strength += .20
        semantic_floor = .86 if self.e5 else .49
        lexical_floor = .82 if self.e5 else .36
        strong_semantic = .90 if self.e5 else .62
        reason = "sufficient_section"
        if not blocks or not self.weights:
            reason = "no_section"
        elif self.strong_unknown or (self.precise and (coverage < .79 or best_coverage < .56)):
            reason = "unsupported_specific_detail"
        elif exact and cosine >= lexical_floor:
            pass
        elif self.method == "bm25":
            if coverage < .60 or best_coverage < .22:
                reason = "insufficient_lexical_evidence"
        elif ((cosine >= semantic_floor and coverage >= .35 and best_coverage >= .13)
              or (cosine >= lexical_floor and coverage >= .73 and best_coverage >= .29)
              or (cosine >= strong_semantic and gap <= .025 and coverage >= .17
                  and (best_coverage >= .085 or named >= .11))
              or (not self.known and cosine >= (.92 if self.e5 else .72)
                  and cosine - self.next_peak >= .08)):
            pass
        else:
            reason = "insufficient_section_evidence"
        return Candidate(card, strength, reason == "sufficient_section", reason, blocks)

    def candidates(self):
        definition = "definition" in self.query.intents

        def priority(candidate):
            exact_title = self.weights.keys() == self.engine.title_terms[candidate.card]
            return (candidate.admitted and definition and exact_title, candidate.score)

        return sorted((self.assess(card, i) for i, card in enumerate(self.ranked)), key=priority, reverse=True)

    def covers(self, block):
        """A directly matched section can answer a facet selected elsewhere."""
        passage = self.engine.passages[block.index]
        if not self.weights or self.strong_unknown or self.precise:
            return False
        return self.cover(block.terms | self.titles[passage.card_id]) >= .85 and self.cover(block.terms) >= .42


def choose_sections(candidates, scorer):
    """Use relevance minus overlap and require novel evidence for cross-card blocks."""
    options = [c for c in candidates if c.admitted]
    if not options:
        return []
    first = options[0]
    pool = [(c, b) for c in options[:3] for b in c.blocks[:5]]
    lead = first.blocks[0]
    chosen = [lead]
    covered = set(lead.matched)
    budget = 3500 - len(lead.text)
    engine = scorer.engine
    main = engine.passages[lead.index]
    while len(chosen) < 3 and budget > 0:
        choices = []
        for c, b in pool:
            if b in chosen or len(b.text) > budget:
                continue
            novelty = scorer.cover(b.matched - covered)
            overlap = max((len(b.terms & s.terms) / max(1, min(len(b.terms), len(s.terms))) for s in chosen), default=0)
            if c != first:
                p = engine.passages[b.index]
                connected = (p.card_id in main.related or p.card_id in main.prerequisites
                             or main.card_id in p.related or main.card_id in p.prerequisites)
                if p.domain != main.domain and not connected:
                    continue
                if novelty < .18 or c.score < first.score - .13 or b.score < .56 * lead.score:
                    continue
            if overlap >= .69 or b.score < .65 * lead.score:
                continue
            # Do not return a generic title-only section when a useful block is already present.
            if b.score < .78 * lead.score and novelty < .08:
                continue
            choices.append((b.score + .33 * novelty - .22 * overlap, -b.index, b))
        if not choices:
            break
        _, _, best = max(choices)
        chosen.append(best)
        budget -= len(best.text)
        covered.update(best.matched)
    return sorted(chosen, key=lambda b: (engine.passages[b.index].card_id != first.card, b.index))


def acronyms(titles):
    """Derive abbreviations from capitalised English names already in the corpus."""
    phrase = r"\b[A-Z][a-z]+(?:[- ][A-Z][a-z]+){1,3}\b"
    associations = {}
    for card, title in titles.items():
        for name in re.findall(phrase, title):
            initials = "".join(word[0].casefold() for word in re.split(r"[- ]", name))
            name_terms = tuple(terms(name))
            if name_terms:
                associations.setdefault(initials, {})[name_terms] = card
    return associations


def resolve_acronyms(query, associations, engine):
    from dataclasses import replace

    words = re.findall(r"\b[A-Z]{2,5}\b", query.raw)
    tokens = set(query.tokens)
    expansions = {}
    for word in words:
        short = word.casefold()
        options = associations.get(short)
        if not options or short in engine.idf:
            continue
        matching = [name for name, card in options.items()
                    if len((tokens - {short}) & engine.card_terms[card]) >= 2]
        if len(matching) == 1:
            expansions[short] = matching[0]
    if not expansions:
        return query
    expanded = tuple(dict.fromkeys(v for w in query.tokens for v in expansions.get(w, (w,))))
    return replace(query, tokens=expanded, normalized=query.normalized+" "+" ".join(
        " ".join(v) for v in expansions.values()
    ))


def lacks_referent(query):
    return bool(_DEICTIC.search(query.raw) and len(query.tokens) <= 3)
