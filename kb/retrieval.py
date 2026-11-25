"""Independent BM25 and dense retrieval with rank fusion and extractive answers."""
import functools
import json
import math
import os
import re
import sqlite3
import threading
from collections import Counter, defaultdict
from contextlib import closing
from pathlib import Path
from time import perf_counter

from .evidence import DEFAULT_DEPTH, EvidenceScorer, acronyms, choose_sections, lacks_referent, resolve_acronyms
from .extractive import ExtractiveResult
from .passage_index import INDEX, VERSION, Passage, close_code_fence, corpus_key
from .qa_reader import apply_reader
from .query import Query, facets, terms, with_facet_context
from .representation import CHANNEL_WEIGHTS
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
             representations=None, representation_mode="off"):
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
            if part["query"] not in missing or part.get("reason") == "unspecified_referent":
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
            depth=DEFAULT_DEPTH, reader=None, qa_mode="off", representations=None, representation_mode="off"):
        grouped = defaultdict(list)
        diagnostics = []
        selections = []
        timings = Counter(embedding=0.0, retrieval=0.0, rerank=0.0, extract=0.0, qa=0.0)
        rankings = []
        by_id = {unit.id: unit for unit in units}
        parts = facets(question)
        overflow = parts[MAX_FACETS:]
        previous = None
        for part in parts[:MAX_FACETS]:
            bare = resolve_acronyms(Query.parse(part), self.acronyms, self)
            query = with_facet_context(bare, previous)
            if not query.normalized:
                continue
            if query is bare:
                previous = bare
            needs_clarification = lacks_referent(bare) and query is bare
            if representations is None or representation_mode == "off":
                ranked, evidence, lexical, dense, details = self.rank(query, method, domain, links, reranker)
            else:
                ranked, evidence, lexical, dense, details = self.rank(
                    query, method, domain, links, reranker,
                    representations=representations, representation_mode=representation_mode,
                )
            rankings.append(ranked)
            timings.update(details["seconds"])
            started = perf_counter()
            scorer = EvidenceScorer(self, query, [card for card in ranked if card in by_id],
                                    evidence, lexical, dense, depth, method)
            candidates = scorer.candidates()
            qa_start = perf_counter()
            qa = {}
            if not needs_clarification:
                candidates, qa = apply_reader(reader, qa_mode, scorer, candidates)
            qa_elapsed = perf_counter() - qa_start
            timings["qa"] += qa_elapsed
            chosen = [] if needs_clarification else choose_sections(candidates, scorer)
            if chosen and not scorer.has_answer_material(chosen):
                details["reason"] = "overview_without_answer"
                details["overview_cards"] = list(dict.fromkeys(self.passages[b.index].card_id for b in chosen))
                chosen = []
            elif not chosen:
                details["reason"] = "unspecified_referent" if needs_clarification else "insufficient_evidence"
            selections.append((part, scorer, details, chosen))
            details["checked_candidates"] = [
                {"card": c.card, "score": round(c.score, 4), "reason": c.reason,
                 "section": list(self.passages[c.blocks[0].index].heading) if c.blocks else []}
                for c in candidates
            ]
            timings["extract"] += perf_counter() - started - qa_elapsed
            details.update(query=part, normalized=query.normalized, terms=query.tokens, qa=qa,
                           intents=query.intents, evidence=[(c, evidence[c]) for c in ranked[:10]])
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
                continue
            if (details.get("reason") != "unspecified_referent"
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
                             "position": self.passages[b.index].position, "text": b.text} for b in group)
        rendered = []
        for card, picked in grouped.items():
            rendered.append("# " + by_id[card].title)
            for heading, text in picked:
                subtitle = " / ".join(heading)
                rendered.append((f"## {subtitle}\n\n" if subtitle else "") + text)
        if missing and grouped:
            rendered.append("Найден частичный ответ. Для следующих частей вопроса подходящего фрагмента не найдено:\n\n"
                            + "\n".join(f"- {part}" for part in missing))
        if overflow:
            rendered.append("Отправьте оставшиеся части отдельным сообщением:\n\n"
                            + "\n".join(f"- {part}" for part in overflow))
        clarification = any(d.get("reason") == "unspecified_referent" for d in diagnostics)
        if not grouped and clarification:
            rendered.insert(0, "Уточните, о каком этапе, шаге или ситуации идёт речь.")
        answer = ExtractiveResult("\n\n".join(rendered), [by_id[c] for c in grouped]) if rendered else None
        if grouped:
            state = "partial" if missing or overflow else "complete"
        elif clarification or overflow:
            state = "clarification"
        elif (any(part.get("reason") == "overview_without_answer" for part in diagnostics)
              or any(cos >= .49 and coverage >= .30
                     for part in diagnostics for _, (cos, coverage) in part["evidence"])):
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
