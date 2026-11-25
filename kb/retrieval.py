"""Independent BM25 and dense retrieval with rank fusion and extractive answers."""
import functools
import json
import math
import os
import re
import sqlite3
import threading
from collections import Counter, defaultdict
from dataclasses import asdict, replace
from contextlib import closing
from pathlib import Path
from time import perf_counter

from .evidence import DEFAULT_DEPTH, EvidenceScorer, acronyms, choose_sections, lacks_referent, resolve_acronyms
from .entities import MODES, entity_index, inherit, roles
from .extractive import ExtractiveResult, direct_search
from .passage_index import INDEX, VERSION, Passage, close_code_fence, corpus_key
from .qa_reader import apply_reader
from .properties import LABELS, QUANTITATIVE
from .query import Query, facets, information_needs, terms, with_facet_context
from .representation import CHANNEL_WEIGHTS
from .search import requested_card_ids
from .titles import title_index
from .vector_store import VectorIndexError, _embedder, source_fingerprint

POOL = 30
MAX_FACETS = 8
FIELD_WEIGHTS = (2.6, 1.4, 1.5, 1.0)
RRF_K = 12
DENSE_WEIGHTS = 0.45
_LOCK = threading.Lock()


class Retrieval:
    def __init__(self, metadata, passages, vectors):
        import numpy as np

        self.metadata = metadata
        self.passages = passages
        self.matrix = np.concatenate(vectors, axis=0)
        self.starts = np.cumsum([0, *[len(v) for v in vectors[:-1]]])
        self.cards = defaultdict(list)
        self.postings = defaultdict(dict)
        self.parent = defaultdict(list)
        fields = [tuple(map(terms, (p.title, " ".join(p.heading), " ".join(p.tags), p.text)))
                  for p in passages]
        self.body_terms = [frozenset(values[3]) for values in fields]
        self.name_terms = {}
        self.title_terms = {}
        average = [max(1, sum(len(f[j]) for f in fields) / len(fields)) for j in range(4)]
        card_frequency = defaultdict(set)
        self.card_terms = defaultdict(set)
        for ix, (p, four_fields) in enumerate(zip(passages, fields)):
            self.cards[p.card_id].append(ix)
            self.parent[p.card_id, p.section].append(ix)
            self.name_terms.setdefault(p.card_id, frozenset(four_fields[0] + four_fields[2]))
            self.title_terms.setdefault(p.card_id, frozenset(four_fields[0]))
            for j, words in enumerate(four_fields):
                for term, count in Counter(words).items():
                    weight = FIELD_WEIGHTS[j] * count / (.65 + .35 * len(words) / average[j])
                    self.postings[term][ix] = self.postings[term].get(ix, 0) + weight
                    card_frequency[term].add(p.card_id)
                    self.card_terms[p.card_id].add(term)
        self.idf = {term: math.log(1 + (len(self.cards) - len(cards) + .5) / (len(cards) + .5))
                    for term, cards in card_frequency.items()}
        self.title_cards = defaultdict(set)
        for card, name in self.title_terms.items():
            for word in name:
                self.title_cards[word].add(card)
        self.named_terms = frozenset(self.title_cards)
        self.section_text = {key: "\n\n".join(passages[i].text for i in indices)
                             for key, indices in self.parent.items()}
        self.section_terms = {key: frozenset().union(*(self.body_terms[i] for i in indices))
                              for key, indices in self.parent.items()}
        self.acronyms = acronyms({card: passages[indices[0]].title for card, indices in self.cards.items()})

    def lexical(self, query):
        import numpy as np

        scores = np.zeros(len(self.passages))
        for term in query.tokens:
            for ix, tf in self.postings.get(term, {}).items():
                scores[ix] += self.idf[term] * 2.2 * tf / (1.2 + tf)
        return scores

    def _query_vector(self, query):
        before = perf_counter()
        prompt = self.metadata.get("query_prefix", "") + query.normalized
        vector = _embedder("sentence-transformers", self.metadata["model"]).embed_query(prompt)
        return vector, perf_counter() - before

    def _dense_values(self, vector):
        import numpy as np

        values = self.matrix @ np.asarray(vector, dtype=self.matrix.dtype)
        return np.maximum.reduceat(values, self.starts)

    def dense(self, query):
        vector, duration = self._query_vector(query)
        return self._dense_values(vector), duration

    def _pool(self, scores, allowed, minimum):
        cards = {}
        for ix in sorted(allowed, key=lambda i: (-scores[i], i)):
            if scores[ix] <= minimum or len(cards) >= POOL:
                break
            cards.setdefault(self.passages[ix].card_id, ix)
        return cards

    def rank(self, query, method, domain=None, links=False, reranker=None, *,
             representations=None, representation_mode="off", entity_weights=None):
        begin = perf_counter()
        allowed = [i for i, p in enumerate(self.passages) if not domain or p.domain == domain]
        lexical = self.lexical(query)
        dense_query = representations is not None and representation_mode in ("questions", "combined")
        if dense_query:
            if representations.metadata["model"] != self.metadata["model"] or self.metadata.get("query_prefix"):
                raise VectorIndexError("Индексы исходных блоков и вопросов должны использовать одну MiniLM.")
            vector, embedding = self._query_vector(query)
            dense = self._dense_values(vector) if method != "bm25" else lexical * 0
        else:
            dense, embedding = self.dense(query) if method != "bm25" else (lexical * 0, 0)
        bm25 = self._pool(lexical, allowed, 0)
        semantic = self._pool(dense, allowed, -2) if method != "bm25" else {}
        rrf = defaultdict(float)
        channels = ((bm25, 1.0), (semantic, DENSE_WEIGHTS))
        if method == "bm25":
            channels = channels[:1]
        elif method == "dense":
            channels = channels[1:]
        additional = {}
        if representations is not None and representation_mode != "off":
            allowed_cards = {self.passages[i].card_id for i in allowed}
            if representation_mode in ("metadata", "combined"):
                additional["metadata"] = representations.lexical(query, allowed_cards, POOL)
            if dense_query:
                additional["questions"] = representations.dense(vector, allowed_cards, POOL)
            channels += tuple((dict.fromkeys(key for key, _, _ in rows), CHANNEL_WEIGHTS[name])
                              for name, rows in additional.items())
        for channel, weight in channels:
            for rank, card in enumerate(channel, 1):
                rrf[card] += weight / (RRF_K + rank)
        rerank_started = perf_counter()
        base = sorted(rrf, key=lambda card: (-rrf[card], card))
        if links:
            # One hop from the top two, with both dense and lexical evidence.
            for seed in base[:2]:
                p = self.passages[self.cards[seed][0]]
                for target in (p.related + p.prerequisites)[:8]:
                    if target in bm25 and target in semantic:
                        rrf[target] += 0.002
        weights = {term: self.idf.get(term, 3.0) for term in query.tokens}
        total_weight = sum(weights.values()) or 1

        global_cards = set(rrf)
        entity_weights = entity_weights or {}
        for card in entity_weights:
            rrf.setdefault(card, 0.)
        evidence = {}
        for card in rrf:
            pos = self.cards[card]
            cos = max(float(dense[i]) for i in pos)
            match = sum(w for word, w in weights.items() if word in self.card_terms[card]) / total_weight
            named = self.name_terms[card]
            coverage_title = len(named.intersection(query.tokens)) / max(1, len(query.tokens))
            evidence[card] = (cos, match)
            if method == "hybrid":
                rrf[card] += .015 * match + .013 * coverage_title
                if "definition" in query.intents and self.title_terms[card] == weights.keys():
                    rrf[card] += .06
        global_ranking = sorted(global_cards, key=lambda card: (-rrf[card], card))
        for card, boost in entity_weights.items():
            rrf[card] += boost
        rank = sorted(rrf, key=lambda card: (-rrf[card], card))
        reranker_scores = {}
        if reranker is not None and rank:
            leaders = rank[:12]
            pairs = []
            for card in leaders:
                ix = bm25.get(card, semantic.get(card))
                if ix is None:
                    ix = max(self.cards[card], key=lambda i: dense[i])
                p = self.passages[ix]
                pairs.append((query.normalized, f"{p.title} {' / '.join(p.heading)}\n{p.text}"))
            scores = reranker.predict(pairs, batch_size=12, show_progress_bar=False)
            reranker_scores = {card: float(score) for card, score in zip(leaders, scores)}
            rank = sorted(leaders, key=lambda card: -reranker_scores[card]) + rank[len(leaders):]
        return rank, evidence, lexical, dense, {
            "bm25": [(c, round(float(lexical[i]), 4)) for c, i in bm25.items()],
            "dense": [(c, round(float(dense[i]), 4)) for c, i in semantic.items()],
            "fusion": base, "reranked": rank, "cross_encoder_scores": reranker_scores,
            "global_ranking": global_ranking,
            "entity_candidates": [{"id": card, "boost": value, "new": card not in global_cards,
                                   "global_position": global_ranking.index(card) + 1 if card in global_cards else None,
                                   "position": rank.index(card) + 1}
                                  for card, value in entity_weights.items()],
            "representations": {
                name: [{"card": key, "score": round(value, 4), "provenance": origin}
                       for key, value, origin in rows]
                for name, rows in additional.items()
            },
            "seconds": {"embedding": embedding, "retrieval": rerank_started - begin - embedding,
                        "rerank": perf_counter() - rerank_started},
        }

    def warm_up(self):
        """Load the query encoder and run one forward pass."""
        self._query_vector(Query.parse("поиск по базе знаний"))

    def related_cards(self, debug, limit=3):
        """Suggest original cards for unanswered facets using two relevance signals."""
        if limit <= 0:
            return
        used = set(debug["sources"])
        missing = set(debug["unanswered"])
        suggested = set()
        for part in debug["parts"]:
            if part["query"] not in missing or part.get("reason") in {"unspecified_referent", "unknown_card_id"}:
                continue
            anchors = {term for term in part["terms"] if len(term) >= 3 and self.idf.get(term, 0) >= 1.6}
            for card, (cosine, coverage) in part["evidence"][:DEFAULT_DEPTH]:
                if card in used or card in suggested or cosine < .49 or coverage < .30:
                    continue
                named = anchors & self.name_terms[card] & self.card_terms[card]
                strong_body = cosine >= .60 and coverage >= .64 and len(anchors & self.card_terms[card]) >= 2
                overview = card in part.get("overview_cards", ())
                if named or strong_body or overview:
                    suggested.add(card)
                    yield card
                    if len(suggested) >= limit:
                        return

    def _compose(self, blocks):
        """Deduplicate exact blocks while retaining distinct excerpts of long sections."""
        groups = defaultdict(dict)
        for block in blocks:
            p = self.passages[block.index]
            group = groups[p.card_id, p.section]
            if block.whole:
                group.clear()
                group[block.index] = block
            elif not any(chosen.whole for chosen in group.values()):
                group.setdefault(block.index, block)
        return [sorted(group.values(), key=lambda block: self.passages[block.index].position)
                for group in groups.values()]

    def ask(self, question, units, method="hybrid", domain=None, links=False, reranker=None, *,
            depth=DEFAULT_DEPTH, reader=None, qa_mode="off", representations=None, representation_mode="off",
            entity_mode="off"):
        if direct := direct_search(question, units, domain):
            return direct
        if entity_mode not in MODES:
            raise ValueError(f"Неизвестный режим Entity Linking: {entity_mode}")
        grouped = defaultdict(list)
        diagnostics = []
        selections = []
        timings = Counter(embedding=0.0, retrieval=0.0, rerank=0.0, extract=0.0, qa=0.0)
        rankings = []
        by_id = {unit.id: unit for unit in units}
        parts = facets(question)
        overflow = parts[MAX_FACETS:]
        previous = None
        previous_mentions = ()
        missing_ids = set()
        observe = entity_mode != "off" or bool(requested_card_ids(question))
        index = entity_index(title_index(units)) if observe else None
        cursor = 0
        for part in parts[:MAX_FACETS]:
            started = perf_counter()
            offset = question.find(part, cursor) if observe else 0
            if offset >= 0:
                cursor = offset + len(part)
            needs = information_needs(part) if observe else ()
            explicit_ids = requested_card_ids(part) if observe else ()
            mentions = roles(index.link(part, units, domain), part.casefold(), needs) if index else ()
            if not mentions and index:
                mentions = inherit(part, previous_mentions)
            if mentions and not mentions[0].inherited:
                previous_mentions = mentions
            explicit_context = any(mention.match_type == "id" for mention in mentions)
            use_entities = entity_mode in ("retrieve", "evidence") or explicit_context
            weighted = {}
            owners = set()
            if use_entities:
                for mention in mentions:
                    key = mention.selected
                    if key not in self.cards or key not in by_id:
                        continue
                    weights = {"primary": .021, "comparison": .015, "additional": .009, "context": .004}
                    boost = .045 if mention.match_type == "id" else weights.get(mention.role, 0.)
                    if mention.match_type == "inflected":
                        boost *= .75
                    weighted[key] = max(weighted.get(key, 0.), boost)
                    if mention.role != "context":
                        owners.add(key)
            unresolved = set(explicit_ids) - weighted.keys()
            missing_ids.update(unresolved)
            search_part = part
            replace_names = explicit_ids or (use_entities and mentions and mentions[0].inherited)
            if replace_names:
                for mention in mentions:
                    if mention.selected and mention.match_type == "id" and mention.text:
                        search_part = search_part.replace(mention.text, mention.canonical_name)
                    elif mention.inherited:
                        search_part += " " + mention.canonical_name
            bare = resolve_acronyms(Query.parse(search_part), self.acronyms, self)
            if replace_names:
                bare = replace(bare, raw=part)
            query = with_facet_context(bare, previous) if search_part == part else bare
            if not query.normalized:
                continue
            if query is bare and search_part == part:
                previous = bare
            elif explicit_ids and weighted:
                previous = bare
            if observe:
                timings["entity_linking"] += perf_counter() - started
            needs_clarification = lacks_referent(bare) and query is bare
            rank_options = {}
            if representations is not None and representation_mode != "off":
                rank_options.update(representations=representations, representation_mode=representation_mode)
            if weighted:
                rank_options["entity_weights"] = weighted
            ranked, evidence, lexical, dense, details = self.rank(query, method, domain, links, reranker, **rank_options)
            rankings.append(ranked)
            timings.update(details["seconds"])
            started = perf_counter()
            evidence_needs = needs if weighted and (entity_mode == "evidence" or explicit_context) else ()
            scorer = EvidenceScorer(self, query, [card for card in ranked if card in by_id],
                                    evidence, lexical, dense, depth, method,
                                    needs=evidence_needs, owners=owners, required_cards=weighted)
            candidates = scorer.candidates()
            qa_start = perf_counter()
            qa = {}
            if not needs_clarification:
                candidates, qa = apply_reader(reader, qa_mode, scorer, candidates)
            qa_elapsed = perf_counter() - qa_start
            timings["qa"] += qa_elapsed
            failed_id = bool(unresolved) and not weighted
            chosen = [] if needs_clarification or failed_id else choose_sections(candidates, scorer)
            if chosen and not scorer.has_answer_material(chosen):
                details["reason"] = "overview_without_answer"
                details["overview_cards"] = list(dict.fromkeys(self.passages[b.index].card_id for b in chosen))
                chosen = []
            elif not chosen:
                details["reason"] = ("unknown_card_id" if failed_id else
                                     "unspecified_referent" if needs_clarification else "insufficient_evidence")
            selections.append((part, scorer, details, chosen))
            details["checked_candidates"] = [
                {"card": c.card, "score": round(c.score, 4), "reason": c.reason,
                 "section": list(self.passages[c.blocks[0].index].heading) if c.blocks else [],
                 **({"properties": sorted(set().union(*(b.properties for b in c.blocks[:4])))}
                    if evidence_needs else {})}
                for c in candidates
            ]
            timings["extract"] += perf_counter() - started - qa_elapsed
            details.update(query=part, normalized=query.normalized, terms=query.tokens, qa=qa,
                           intents=query.intents, evidence=[(c, evidence[c]) for c in ranked[:10]])
            if observe:
                details["entities"] = [asdict(replace(mention, start=mention.start + max(0, offset),
                                                      end=mention.end + max(0, offset)))
                                       if mention.start is not None else asdict(mention) for mention in mentions]
                details["information_needs"] = needs
                details["checked_entity_cards"] = list(weighted)
                details["invalid_card_ids"] = sorted(unresolved)
                details["properties"] = sorted(set().union(*(block.properties for block in chosen)))
            diagnostics.append(details)
        before = perf_counter()
        composed = self._compose(b for _, _, _, chosen in selections for b in chosen)
        retained = [b for group in composed for b in group]
        missing = []
        for part, scorer, details, chosen in selections:
            # The same original excerpt may survive in a complete parent section.
            visible = any(self.passages[a.index].card_id == self.passages[b.index].card_id
                          and self.passages[a.index].section == self.passages[b.index].section
                          and a.text in b.text for a in chosen for b in retained)
            if visible:
                required = scorer.needs & QUANTITATIVE
                facet_blocks = [block for block in retained if any(
                    self.passages[block.index].card_id == self.passages[item.index].card_id
                    and self.passages[block.index].section == self.passages[item.index].section
                    for item in chosen)]
                available = frozenset().union(*(block.properties for block in facet_blocks))
                deficits = [LABELS[k] for k in sorted(required - available)]
                if "comparison" in scorer.needs and len(scorer.owners) > 1:
                    confirmed = {card for card in scorer.owners if any(
                        self.passages[b.index].card_id == card or (
                            self.title_terms[card] and self.title_terms[card] <= b.terms)
                        for b in facet_blocks)}
                    details["comparison_coverage"] = sorted(confirmed)
                    if confirmed != scorer.owners:
                        deficits.append("сведения об обеих сравниваемых сущностях")
                if deficits:
                    details["uncovered_properties"] = deficits
                    missing.append(part + " (" + ", ".join(deficits) + ")")
                continue
            if (details.get("reason") not in {"unspecified_referent", "unknown_card_id"}
                    and any(scorer.has_answer_material([block]) and scorer.covers(block) for block in retained)):
                details["reason"] = "covered_in_selected_sections"
            else:
                missing.append(part)

        selected = []
        for group in composed:
            p = self.passages[group[0].index]
            texts = [close_code_fence(re.sub(r"\[\[([A-Z]+-[A-Z]+-\d+)\]\]", "", b.text)) for b in group]
            grouped[p.card_id].append((p.heading, "\n\n".join(texts)))
            selected.extend({"id": p.card_id, "heading": p.heading,
                             "position": self.passages[b.index].position, "text": b.text,
                             **({"properties": sorted(b.properties)} if b.properties else {})} for b in group)
        rendered = []
        for card, picked in grouped.items():
            rendered.append("# " + by_id[card].title)
            for heading, text in picked:
                subtitle = " / ".join(heading)
                rendered.append((f"## {subtitle}\n\n" if subtitle else "") + text)
        if missing and grouped:
            rendered.append("Найден частичный ответ. Для следующих частей вопроса подходящего фрагмента не найдено:\n\n"
                            + "\n".join(f"- {part}" for part in missing))
        if missing_ids:
            rendered.append("Карточки отсутствуют в доступной базе: " + ", ".join(sorted(missing_ids)) + ".")
        if overflow:
            rendered.append("Отправьте оставшиеся части отдельным сообщением:\n\n"
                            + "\n".join(f"- {part}" for part in overflow))
        clarification = any(d.get("reason") == "unspecified_referent" for d in diagnostics)
        if not grouped and clarification:
            rendered.insert(0, "Уточните, о каком этапе, шаге или ситуации идёт речь.")
        answer = ExtractiveResult("\n\n".join(rendered), [by_id[c] for c in grouped]) if rendered else None
        if grouped:
            state = "partial" if missing or overflow or missing_ids else "complete"
        elif clarification or overflow:
            state = "clarification"
        elif (any(part.get("reason") == "overview_without_answer" for part in diagnostics)
              or any(cos >= .49 and coverage >= .30
                     for part in diagnostics if part.get("reason") != "unknown_card_id"
                     for _, (cos, coverage) in part["evidence"])):
            state = "related_only"
        else:
            state = "absent"
        timings["extract"] += perf_counter() - before
        rank = list(dict.fromkeys(r[i] for i in range(max(map(len, rankings), default=0))
                                  for r in rankings if len(r) > i))
        return answer, {"query": question, "parts": diagnostics, "ranked_cards": rank, "state": state,
                        "selected": selected, "sources": list(grouped), "unanswered": missing + overflow,
                        "deferred": overflow, "seconds": dict(timings)}


@functools.lru_cache(maxsize=2)
def _load(root, index, stamp, fingerprint):
    import numpy as np

    with closing(sqlite3.connect(index)) as conn:
        meta = json.loads(conn.execute("SELECT value FROM metadata").fetchone()[0])
        if meta["version"] != VERSION or meta["corpus_sha256"] != corpus_key(root):
            raise VectorIndexError("Индекс фрагментов устарел. Выполните passage-build.")
        rows = conn.execute("SELECT data, vector FROM passages").fetchall()
    passages = [Passage(**json.loads(row[0])) for row in rows]
    vectors = [np.frombuffer(row[1], dtype="<f4").reshape(-1, meta["dimensions"]) for row in rows]
    return Retrieval(meta, passages, vectors)


def get_engine(root, index_path=None):
    root = Path(root).resolve()
    index = Path(index_path).resolve() if index_path else root / INDEX
    stat = index.stat()
    fingerprint = source_fingerprint(root)
    with _LOCK:
        return _load(root, index, (stat.st_ino, stat.st_ctime_ns, stat.st_size), fingerprint)


@functools.lru_cache(maxsize=1)
def load_reranker(directory):
    from sentence_transformers import CrossEncoder

    directory = Path(directory).resolve()
    if not directory.is_dir():
        raise ValueError("Укажите локальный каталог Cross-Encoder")
    return CrossEncoder(str(directory), local_files_only=True, device="cpu", max_length=256)


def configured_reranker():
    directory = os.getenv("KB_RERANKER_PATH")
    return load_reranker(directory) if directory else None
