"""Passage evidence, abstention and diversity for extractive retrieval."""
from dataclasses import dataclass, replace
from functools import lru_cache
import math
import re

from .properties import QUANTITATIVE, supported
from .query import normalize, terms
from .titles import name_keys, name_stem

DEFAULT_DEPTH = 5
# Match requests for exact details where a general explanation is insufficient.
_PRECISE = re.compile(
    r"\b(?:синтаксис|квот\w*|проходн\w*|по шагам|пошагов\w*|в какое время|вычислить вероятность|флаг\w+\s+cli|параметр\w*|"
    r"точн\w+\s+(?:числ\w*|балл\w*|значени\w*)|какие\s+команд\w*|"
    r"what flag|exact (?:limit|score|syntax)|which parameter)\b", re.I
)
_PRIVATE_DETAIL = re.compile(r"\b(?:закрыт|внутренн)\w* (?:портал|систем|критери|правил)\w*", re.I)
_OVERVIEW = re.compile(r"^(?:задача|постановка задачи|условие|на собеседовании|что оценивают|для кого этот план|цель проверки)$")
_DEICTIC = re.compile(r"\b(?:этот|этом|этого|этому|этой|это|этим|this|that)\s+(?:этап\w*|шаг\w*|случа\w*|способ\w*|stage|step)\b", re.I)

_PROCEDURE_HEADING = re.compile(r"^(?:шаг|подход к|как (?:это|устро|работ|примен|провод)|алгоритм|реализац|архитектур)")
_EXAMPLE_HEADING = re.compile(r"^(?:практический )?пример|^типов\w+ задач")
_NUMERIC = re.compile(r"O\s*\([^)]{1,28}\)|\d+(?:[.,]\d+)?\s*(?:[×%]|мс\b|сек\w*|мин\w*|байт\w*|ГиБ\b)", re.I)
_EXACT_VALUE = re.compile(r"\b(?:како[йе] (?:числов\w+|точн\w+) (?:предел|значение|лимит)"
                          r"|точн\w+ (?:квот\w*|лимит\w*|формул\w*|цен\w*)"
                          r"|каков[аы]? (?:квот\w*|цен\w*)|какой (?:[a-z]+[- ])?флаг"
                          r"|сколько (?:секунд|байтов|очков|баллов)|how many (?:seconds|bytes))\b", re.I)


@lru_cache(maxsize=4096)
def _name_tokens(text):
    return tuple(map(name_stem, name_keys(text)))


def _contains_name(text, name):
    tokens = _name_tokens(text)
    return any(tokens[pos:pos + len(name)] == name for pos in range(len(tokens) - len(name) + 1))


@dataclass(frozen=True)
class SectionEvidence:
    index: int
    text: str
    terms: frozenset
    matched: frozenset
    score: float
    whole: bool = False
    properties: frozenset = frozenset()


@dataclass(frozen=True)
class Candidate:
    card: str
    score: float
    admitted: bool
    reason: str
    blocks: tuple


class EvidenceScorer:
    def __init__(self, engine, query, ranked, evidence, lexical, dense, depth, method, *, needs=(), owners=(), required_cards=(), context=None, entity_scope=None, alternatives=(), literal_topic=""):
        import numpy as np

        self.engine = engine
        self.query = query
        self.ranked = list(dict.fromkeys((*ranked[:depth], *required_cards)))
        self.evidence = evidence
        self.lexical = lexical
        self.dense = dense
        self.method = method
        self.needs = frozenset(needs)
        self.owners = frozenset(owners)
        self.context = context or {}
        self.entity_scope = entity_scope or {}
        self.explicit_name_terms = set(terms(" ".join(alternatives)))
        self.literal_topic = tuple(map(name_stem, name_keys(literal_topic)))
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
        self.exact_value = bool(_EXACT_VALUE.search(query.raw))
        self.private_detail = bool(_PRIVATE_DETAIL.search(query.normalized))
        self.precise = bool(self.exact_value or self.private_detail or _PRECISE.search(query.normalized)
                            or re.search(r"\b\d+\.\d+\b", query.raw))
        intents = set(query.intents)
        if intents & {"design", "procedure"}:
            self.budget = (5, 6100, 2250)
        elif "comparison" in intents or "complexity" in intents:
            self.budget = (4, 4700, 1900)
        elif "definition" in intents or "quantity" in intents or self.exact_value:
            self.budget = (2, 2200, 1150)
        else:
            self.budget = (3, 3500, 1550)
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

    def _matches_context(self, card, vocabulary):
        return (card in self.context or
                any(anchor <= vocabulary for anchors in self.context.values() for anchor in anchors))

    def names_entity(self, owner, text):
        aliases = self.entity_scope.get(owner, ())
        return any(_contains_name(text, alias) for alias in aliases)

    def _about_entity(self, card, text):
        if card in self.entity_scope:
            return True
        title = self.engine.passages[self.engine.cards[card][0]].title
        return any(self.names_entity(owner, title) or self.names_entity(owner, text)
                   for owner in self.entity_scope)

    def complete_comparison(self, chosen, candidates):
        available = {candidate.card: candidate for candidate in candidates if candidate.admitted}
        limit, budget, _ = self.budget
        for owner in self.entity_scope:
            if any(self.engine.passages[block.index].card_id == owner or self.names_entity(owner, block.text)
                   for block in chosen) or owner not in available:
                continue
            block = available[owner].blocks[0]
            if len(chosen) >= limit:
                # Keep the lead and reserve one slot for the other side.
                chosen = chosen[:-1]
            if sum(len(item.text) for item in chosen) + len(block.text) <= budget:
                chosen = [*chosen, block]
        return chosen

    def _properties(self, card, text, headings, vocabulary):
        found = supported(text, headings) & self.needs
        if self.entity_scope and card not in self.entity_scope:
            # A number or property about a different subject in the same section
            # does not establish a claim about the named entity.
            fragments = re.split(r"(?<=[.!?])\s+|\n", text)
            title = self.engine.passages[self.engine.cards[card][0]].title
            if not any(self.names_entity(owner, title) for owner in self.entity_scope):
                found = frozenset().union(*(supported(fragment, "") & found for fragment in fragments
                                            if any(self.names_entity(owner, fragment) for owner in self.entity_scope)))
        if found & QUANTITATIVE and self.owners and card not in self.owners and not self.entity_scope:
            if not (self.context and self._matches_context(card, vocabulary)) and not any(self.engine.title_terms[owner] and self.engine.title_terms[owner] <= vocabulary
                       for owner in self.owners):
                found -= QUANTITATIVE
        return found

    def _blocks(self, card):
        engine = self.engine
        sections = {}
        block_limit, char_limit, parent_limit = self.budget
        intents = set(self.query.intents)
        procedural = bool(intents & {"procedure", "design"})
        definition = "definition" in intents
        example_requested = bool(re.search(r"\b(?:пример|example)\b", self.query.raw, re.I))
        for ix in engine.cards[card]:
            passage = engine.passages[ix]
            body = engine.body_terms[ix]
            heading = normalize(passage.heading[-1]) if passage.heading else ""
            headings = " ".join(passage.heading)
            match = frozenset(body & self.weights.keys())
            lexical = math.log1p(float(self.lexical[ix])) / math.log1p(self.lex_peak)
            sem = (float(self.dense[ix]) - self.median) / self.scale
            score = .53 * sem + .23 * self.cover(match) + .16 * lexical
            score += .11 * self.query.heading_signal(headings)
            if _OVERVIEW.match(heading) and not definition:
                score -= .19
            if not definition and (procedural or intents & {"mechanism", "practice"}):
                if _PROCEDURE_HEADING.match(heading) or "шаг " in normalize(headings):
                    score += .13 if procedural else .08
                if procedural and not example_requested and any(_EXAMPLE_HEADING.match(normalize(h))
                                                                  for h in passage.heading):
                    score -= .16
            if definition and self.weights and self.weights.keys() <= self.titles[card]:
                score += .13 * any(normalize(h).startswith(("определ", "что такое", "суть", "назнач"))
                                   for h in passage.heading)
            if intents & {"quantity", "complexity"} and _NUMERIC.search(passage.text):
                score += .10
            if self.needs:
                support = self._properties(card, passage.text, headings, body)
                score += .19 * len(support & QUANTITATIVE) + .07 * len(support - QUANTITATIVE)
                if support and card in self.owners:
                    score += .09
            if "comparison" in intents and len(self.anchors) > 1:
                score += .10 * len(self.anchors & body) / len(self.anchors)
            sections.setdefault(passage.section, []).append((score, ix))
        output = []
        for section, scored in sections.items():
            scored.sort(reverse=True)
            parent = engine.section_text[card, section]
            whole = len(parent) <= parent_limit
            for score, ix in scored[:1 if whole else min(block_limit, 3)]:
                passage = engine.passages[ix]
                text = parent if whole else passage.text
                body = engine.section_terms[card, section] if whole else engine.body_terms[ix]
                match = frozenset((body | set(terms(" ".join(passage.heading)))) & self.weights.keys())
                if self.literal_topic and not _contains_name(passage.title + " " + text, self.literal_topic):
                    continue
                if self.entity_scope and not self._about_entity(card, text):
                    continue
                if self.context and card not in self.entity_scope and not self._matches_context(card, body | self.engine.title_terms[card]):
                    continue
                if len(text) <= char_limit:
                    properties = self._properties(card, text, " ".join(passage.heading), body) if self.needs else frozenset()
                    output.append(SectionEvidence(ix, text, body, match, score, whole, properties))
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
        required = self.needs & QUANTITATIVE
        coverage_props = frozenset()
        if self.needs:
            coverage_props = frozenset().union(*(block.properties for block in blocks[:4]))
            strength += .13 * len(coverage_props & self.needs)
            if (card in self.owners and blocks and
                    (self.needs & {"definition", "mechanism", "comparison"} or coverage_props)):
                strength += .14
        reason = "sufficient_section"
        if not blocks or not self.weights:
            reason = "no_section"
        elif (self.strong_unknown or (self.private_detail and not any(_PRIVATE_DETAIL.search(b.text) for b in blocks[:4]))
              or (self.precise and (coverage < .79 or best_coverage < .56))
              or (self.exact_value and not any(_NUMERIC.search(b.text) for b in blocks[:4]))):
            reason = "unsupported_specific_detail"
        elif required and not coverage_props & required:
            reason = "missing_requested_property"
        elif ((card in self.context or card in self.entity_scope) and required and required <= coverage_props
              and cosine >= lexical_floor and best_coverage >= .13 and not self.precise):
            pass
        elif (card in self.entity_scope and len(self.entity_scope) > 1 and "comparison" in self.needs
              and cosine >= lexical_floor and best_coverage >= .13 and not self.precise):
            pass
        elif (card in self.entity_scope and self.query.intents == ("definition",)
              and self.weights.keys() <= self.explicit_name_terms):
            pass
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

    def priority(self, candidate):
        exact_title = self.weights.keys() == self.engine.title_terms[candidate.card]
        return (candidate.admitted and "definition" in self.query.intents and exact_title, candidate.score)

    def candidates(self):
        return sorted((self.assess(card, i) for i, card in enumerate(self.ranked)),
                      key=self.priority, reverse=True)

    def has_answer_material(self, blocks):
        """A stated task alone is thematic evidence for a request about a mechanism."""
        if not {"mechanism", "procedure", "design", "quantity"} & set(self.query.intents):
            return True
        if "definition" in self.query.intents:
            return True
        for block in blocks:
            path = self.engine.passages[block.index].heading
            if path and normalize(path[-1]) in {"условие", "задача", "постановка задачи", "цель проверки"}:
                continue
            if path and normalize(path[-1]) == "подход" and re.search(
                    r"\b(?:должен|должна|нужен|нужно|необходимо)\b", block.text, re.I):
                if not re.search(r"[.!?]\s+\S", block.text.strip()):
                    continue
            return True
        return False

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
    block_limit, char_limit, _ = getattr(scorer, "budget", (3, 3500, 1550))
    pool = [(c, b) for c in options for b in c.blocks[:block_limit + 2]]
    lead = first.blocks[0]
    chosen = [lead]
    covered = set(lead.matched)
    properties = set(lead.properties)
    budget = char_limit - len(lead.text)
    engine = scorer.engine
    main = engine.passages[lead.index]
    while len(chosen) < block_limit and budget > 0:
        choices = []
        for c, b in pool:
            if b in chosen or len(b.text) > budget:
                continue
            novelty = scorer.cover(b.matched - covered)
            new_property = bool((b.properties - properties) & QUANTITATIVE)
            p = engine.passages[b.index]
            if c != first and len({engine.passages[item.index].card_id for item in chosen}) >= 3:
                if all(engine.passages[item.index].card_id != p.card_id for item in chosen):
                    continue
            overlap = max((len(b.terms & s.terms) / max(1, min(len(b.terms), len(s.terms))) for s in chosen), default=0)
            if c != first:
                connected = (p.card_id in main.related or p.card_id in main.prerequisites
                             or main.card_id in p.related or main.card_id in p.prerequisites)
                if p.domain != main.domain and not connected:
                    continue
                if not new_property and (novelty < .22 or c.score < first.score - .13 or b.score < .68 * lead.score):
                    continue
            if not new_property and (overlap >= .69 or b.score < .65 * lead.score):
                continue
            # Do not return a generic title-only section when a useful block is already present.
            if not new_property and b.score < .78 * lead.score and novelty < .08:
                continue
            choices.append((b.score + .33 * novelty - .22 * overlap + .35 * new_property, -b.index, b))
        if not choices:
            break
        _, _, best = max(choices)
        chosen.append(best)
        budget -= len(best.text)
        covered.update(best.matched)
        properties.update(best.properties)
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
                associations.setdefault(initials, {}).setdefault(name_terms, set()).add(card)
    return associations


def resolve_acronyms(query, associations, engine):
    expansions = {}
    for word in re.findall(r"\b[A-Z]{2,5}\b", query.raw):
        short = word.casefold()
        options = associations.get(short, {})
        if short not in query.tokens or not options:
            continue
        context = set(query.tokens) - {short}
        # Also consider explicitly named senses that already contain the short form.
        covered = set().union(*options.values())
        senses = {phrase: set(cards) for phrase, cards in options.items()}
        direct = engine.title_cards.get(short, set()) - covered
        if direct:
            senses[(short,)] = direct
        def support(cards):
            overlaps = (context & engine.card_terms[card] for card in cards)
            return max((sum(engine.idf.get(t, 0) for t in hits), len(hits)) for hits in overlaps)

        ranked = sorted(((support(cards), phrase) for phrase, cards in senses.items()), reverse=True)
        if not ranked:
            continue
        (weight, count), phrase = ranked[0]
        if count >= 2 and (len(ranked) == 1 or weight - ranked[1][0][0] >= 1):
            if phrase != (short,):
                expansions[short] = phrase
    if not expansions:
        return query
    expanded = tuple(dict.fromkeys(v for w in query.tokens for v in expansions.get(w, (w,))))
    return replace(query, tokens=expanded, normalized=query.normalized + " " + " ".join(
        " ".join(v) for v in expansions.values()
    ))


def lacks_referent(query):
    return bool(_DEICTIC.search(query.raw) and len(query.tokens) <= 3)
