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

from .extractive import ExtractiveResult
from .passage_index import INDEX, VERSION, Passage, close_code_fence, corpus_key
from .query import Query, facets, terms
from .vector_store import VectorIndexError, _embedder, source_fingerprint

POOL = 30
FIELD_WEIGHTS = (2.6, 1.4, 1.5, 1.0)
RRF_K = 12
DENSE_WEIGHTS = 0.45
MIN_DENSE = 0.49
MIN_UNANCHORED = 0.57
MIN_UNANCHORED_GAP = 0.012
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
        average = [max(1, sum(len(f[j]) for f in fields) / len(fields)) for j in range(4)]
        card_frequency = defaultdict(set)
        self.card_terms = defaultdict(set)
        for ix, (p, four_fields) in enumerate(zip(passages, fields)):
            self.cards[p.card_id].append(ix)
            self.parent[p.card_id, p.section].append(ix)
            for j, words in enumerate(four_fields):
                for term, count in Counter(words).items():
                    weight = FIELD_WEIGHTS[j] * count / (.65 + .35 * len(words) / average[j])
                    self.postings[term][ix] = self.postings[term].get(ix, 0) + weight
                    card_frequency[term].add(p.card_id)
                    self.card_terms[p.card_id].add(term)
        self.idf = {term: math.log(1 + (len(self.cards) - len(cards) + .5) / (len(cards) + .5))
                    for term, cards in card_frequency.items()}

    def lexical(self, query):
        import numpy as np

        scores = np.zeros(len(self.passages))
        for term in query.tokens:
            for ix, tf in self.postings.get(term, {}).items():
                scores[ix] += self.idf[term] * 2.2 * tf / (1.2 + tf)
        return scores

    def dense(self, query):
        import numpy as np

        before = perf_counter()
        vector = _embedder("sentence-transformers", self.metadata["model"]).embed_query(query.normalized)
        duration = perf_counter() - before
        values = self.matrix @ np.asarray(vector, dtype=self.matrix.dtype)
        return np.maximum.reduceat(values, self.starts), duration

    def _pool(self, scores, allowed, minimum):
        cards = {}
        for ix in sorted(allowed, key=lambda i: (-scores[i], i)):
            if scores[ix] <= minimum or len(cards) >= POOL:
                break
            cards.setdefault(self.passages[ix].card_id, ix)
        return cards

    def rank(self, query, method, domain=None, links=False, reranker=None):
        begin = perf_counter()
        allowed = [i for i, p in enumerate(self.passages) if not domain or p.domain == domain]
        lexical = self.lexical(query)
        dense, embedding = self.dense(query) if method != "bm25" else (lexical * 0, 0)
        bm25 = self._pool(lexical, allowed, 0)
        semantic = self._pool(dense, allowed, -2) if method != "bm25" else {}
        rrf = defaultdict(float)
        channels = ((bm25, 1.0), (semantic, DENSE_WEIGHTS))
        if method == "bm25":
            channels = channels[:1]
        elif method == "dense":
            channels = channels[1:]
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
        def coverage(card):
            present = self.card_terms[card]
            weights = {term: self.idf.get(term, 3.0) for term in query.tokens}
            return sum(w for t, w in weights.items() if t in present) / (sum(weights.values()) or 1)

        evidence = {}
        for card in rrf:
            pos = self.cards[card]
            cos = max(float(dense[i]) for i in pos)
            match = coverage(card)
            named = set(terms(self.passages[pos[0]].title + " " + " ".join(self.passages[pos[0]].tags)))
            coverage_title = len(named.intersection(query.tokens)) / max(1, len(query.tokens))
            evidence[card] = (cos, match)
            if method == "hybrid":
                rrf[card] += .015 * match + .013 * coverage_title
                if "definition" in query.intents and set(terms(self.passages[pos[0]].title)) == set(query.tokens):
                    rrf[card] += .06
        rank = sorted(rrf, key=lambda card: (-rrf[card], card))
        reranker_scores = {}
        if reranker is not None and rank:
            leaders = rank[:12]
            pairs = []
            for card in leaders:
                ix = bm25.get(card, semantic.get(card))
                p = self.passages[ix]
                pairs.append((query.normalized, f"{p.title} {' / '.join(p.heading)}\n{p.text}"))
            scores = reranker.predict(pairs, batch_size=12, show_progress_bar=False)
            reranker_scores = {card: float(score) for card, score in zip(leaders, scores)}
            rank = sorted(leaders, key=lambda card: -reranker_scores[card]) + rank[len(leaders):]
        return rank, evidence, lexical, dense, {
            "bm25": [(c, round(float(lexical[i]), 4)) for c, i in bm25.items()],
            "dense": [(c, round(float(dense[i]), 4)) for c, i in semantic.items()],
            "fusion": base, "reranked": rank, "cross_encoder_scores": reranker_scores,
            "seconds": {"embedding": embedding, "retrieval": rerank_started - begin - embedding,
                        "rerank": perf_counter() - rerank_started},
        }

    def _accept(self, card, evidence, rankings, method, query):
        cosine, coverage = evidence[card]
        runner = max((evidence[c][0] for c in rankings if c != card), default=-1)
        if method == "bm25":
            return coverage >= .62
        if method == "dense":
            return cosine >= MIN_UNANCHORED and cosine - runner >= MIN_UNANCHORED_GAP
        if "definition" in query.intents and coverage < .55:
            return False
        return ((coverage >= .52 and cosine >= MIN_DENSE)
                or (coverage >= .78 and cosine >= .36)
                or (cosine >= MIN_UNANCHORED and cosine - runner >= MIN_UNANCHORED_GAP))

    def _select(self, card, query, lexical, dense, method):
        def score(i):
            p = self.passages[i]
            return (.36 * math.log1p(lexical[i]) if method != "dense" else 0) + (
                float(dense[i]) if method != "bm25" else 0) + .16 * query.heading_signal(" ".join(p.heading))

        indices = sorted(self.cards[card], key=lambda i: (-score(i), i))
        selected = []
        seen = set()
        sections = set()
        limit = 4000
        for ix in indices:
            p = self.passages[ix]
            if p.section in sections or (selected and score(ix) < score(indices[0]) * .7):
                continue
            # Return a complete parent section when compact, otherwise the matching
            # complete paragraph, list, table or code block.
            parent = self.parent[card, p.section]
            all_text = "\n\n".join(self.passages[i].text for i in parent)
            text = all_text if len(all_text) <= 1450 else p.text
            key = re.sub(r"\s+", " ", text).casefold()
            if key in seen or len(text) > limit:
                continue
            selected.append((p, text))
            seen.add(key)
            sections.add(p.section)
            limit -= len(text)
            if len(selected) >= 3:
                break
        return sorted(selected, key=lambda item: item[0].position)

    def ask(self, question, units, method="hybrid", domain=None, links=False, reranker=None):
        grouped = defaultdict(list)
        used_positions = set()
        missing = []
        diagnostics = []
        timings = Counter(embedding=0.0, retrieval=0.0, rerank=0.0, extract=0.0)
        rankings = []
        by_id = {unit.id: unit for unit in units}
        for part in facets(question):
            query = Query.parse(part)
            if not query.normalized:
                continue
            ranked, evidence, lexical, dense, details = self.rank(query, method, domain, links, reranker)
            rankings.append(ranked)
            timings.update(details["seconds"])
            before = perf_counter()
            best = ranked[0] if ranked else None
            if best not in by_id or not self._accept(best, evidence, ranked, method, query):
                missing.append(part)
                details["reason"] = "insufficient_evidence"
            else:
                blocks = self._select(best, query, lexical, dense, method)
                if not blocks:
                    missing.append(part)
                    details["reason"] = "no_complete_block"
                for p, text in blocks:
                    if (best, p.position) not in used_positions:
                        grouped[best].append((p, text))
                        used_positions.add((best, p.position))
            timings["extract"] += perf_counter() - before
            diagnostics.append({"query": part, "normalized": query.normalized, "terms": query.tokens,
                                "intents": query.intents, "evidence": [(c, evidence[c]) for c in ranked[:10]],
                                **details})
        before = perf_counter()
        rendered = []
        for card, picked in grouped.items():
            rendered.append("# " + by_id[card].title)
            for p, text in picked:
                subtitle = " / ".join(p.heading)
                clean = close_code_fence(re.sub(r"\[\[([A-Z]+-[A-Z]+-\d+)\]\]", "", text))
                rendered.append((f"## {subtitle}\n\n" if subtitle else "") + clean)
        if missing and grouped:
            rendered.append("Найден частичный ответ. Для следующих частей вопроса подходящего фрагмента не найдено:\n\n"
                            + "\n".join(f"- {part}" for part in missing))
        answer = ExtractiveResult("\n\n".join(rendered), [by_id[c] for c in grouped]) if grouped else None
        timings["extract"] += perf_counter() - before
        rank = list(dict.fromkeys(r[i] for i in range(max(map(len, rankings), default=0))
                                  for r in rankings if len(r) > i))
        return answer, {"query": question, "parts": diagnostics, "ranked_cards": rank,
                        "selected": [{"id": c, "heading": p.heading, "position": p.position, "text": t}
                                     for c, blocks in grouped.items() for p, t in blocks],
                        "sources": list(grouped), "unanswered": missing, "seconds": dict(timings)}


@functools.lru_cache(maxsize=2)
def _load(root, stamp, fingerprint):
    import numpy as np

    with closing(sqlite3.connect(root / INDEX)) as conn:
        meta = json.loads(conn.execute("SELECT value FROM metadata").fetchone()[0])
        if meta["version"] != VERSION or meta["corpus_sha256"] != corpus_key(root):
            raise VectorIndexError("Индекс фрагментов устарел. Выполните passage-build.")
        rows = conn.execute("SELECT data, vector FROM passages").fetchall()
    passages = [Passage(**json.loads(row[0])) for row in rows]
    vectors = [np.frombuffer(row[1], dtype="<f4").reshape(-1, meta["dimensions"]) for row in rows]
    return Retrieval(meta, passages, vectors)


def get_engine(root):
    root = Path(root).resolve()
    stat = (root / INDEX).stat()
    fingerprint = source_fingerprint(root)
    with _LOCK:
        return _load(root, (stat.st_ino, stat.st_ctime_ns, stat.st_size), fingerprint)


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
