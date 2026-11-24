"""Reproducible evaluation on editorial relevance judgments."""
import hashlib
import json
import math
import platform
import resource
import statistics
from collections import defaultdict
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from time import perf_counter

from .evidence import DEFAULT_DEPTH
from .extractive import form_answer
from .vector_store import _index_snapshot, search_index


def _metrics(case, ranked, answer, used):
    expected = {item["id"]: item["grade"] for item in case["relevant"]}
    ids = list(dict.fromkeys(ranked))
    targets = set(expected)
    result = {}
    if targets:
        for k in (1, 3, 5):
            result[f"precision@{k}"] = len(set(ids[:k]) & targets) / k
        for k in (5, 10):
            result[f"recall@{k}"] = len(set(ids[:k]) & targets) / len(targets)
            def dcg(grades):
                return sum((2 ** grade - 1) / math.log2(i + 2) for i, grade in enumerate(grades))
            result[f"ndcg@{k}"] = dcg([expected.get(i, 0) for i in ids[:k]]) / dcg(sorted(expected.values(), reverse=True)[:k])
        result["mrr"] = next((1 / (i + 1) for i, key in enumerate(ids) if key in targets), 0)
        labels = case["relevant"]
        checks = [(label, fact) for label in labels for fact in label.get("facts", ())]
        if checks:
            result["fact_proxy"] = sum(label["id"] in used and fact.casefold() in answer.casefold()
                                       for label, fact in checks) / len(checks)
        result["section_proxy"] = sum(label["id"] in used and any(
            ("## " + section).casefold() in answer.casefold() for section in label["sections"]
        ) for label in labels) / len(labels)
        if checks:
            result["full_coverage_proxy"] = float(result["fact_proxy"] == 1 and result["section_proxy"] == 1)
        result["relevant_sources"] = len(targets & set(used)) / max(1, len(used))
        result["extra_sources"] = float(bool(set(used) - targets))
        result["answered"] = float(bool(used))
    else:
        result["correct_abstention"] = float(not used)
        result["false_positive"] = float(bool(used))
    return result


def summarize(rows):
    values = defaultdict(list)
    timings = defaultdict(list)
    for row in rows:
        for key, value in row["metrics"].items():
            values[key].append(value)
        for key, value in row["seconds"].items():
            timings[key].append(value)
    return {"count": len(rows), "metrics": {k: round(statistics.mean(v), 4) for k, v in values.items()},
            "seconds": {k: {"median": round(statistics.median(v), 5),
                            "p95": round(sorted(v)[math.ceil(len(v) * .95) - 1], 5)}
                        for k, v in timings.items()}}


def evaluate(root, units, cases_path, split, method, output=None, reranker_path=None, *,
             index_path=None, depth=DEFAULT_DEPTH, qa_path=None, qa_mode="off"):
    load_start = perf_counter()
    cases = json.loads(Path(cases_path).read_text())
    cases = [case for case in cases if split == "all" or case["split"] == split]
    if not cases:
        raise ValueError("Нет запросов для выбранной выборки")
    engine = None
    reranker = None
    reader = None
    if method == "legacy":
        status, tags = _index_snapshot(root, None)
    else:
        from .retrieval import get_engine, load_reranker
        engine = get_engine(root, index_path)
        status = engine.metadata
        if qa_mode != "off":
            from .qa_reader import load_reader

            if not qa_path:
                raise ValueError("QA требует локального каталога модели.")
            reader = load_reader(qa_path)
        if method == "cross_encoder":
            if not reranker_path:
                raise ValueError("Для cross_encoder нужен --reranker с локальной моделью")
            reranker = load_reranker(reranker_path)
    cold_setup = perf_counter() - load_start
    rows = []
    for case in cases:
        start = perf_counter()
        q = case["query"]
        if method == "legacy":
            started = perf_counter()
            hits = search_index(root, q, limit=30, _snapshot=(status, tags))
            ranking_seconds = perf_counter() - started
            seen = set()
            relevant = []
            counts = defaultdict(int)
            for hit in hits:
                key = hit.card_id
                if key not in seen and len(seen) >= 3 or counts[key] >= 3:
                    continue
                seen.add(key)
                counts[key] += 1
                relevant.append(hit)
                if len(relevant) >= 6:
                    break
            started = perf_counter()
            result = form_answer(q, units, relevant)
            ranking = [hit.card_id for hit in hits]
            times = {"retrieval_including_embedding": ranking_seconds, "extract": perf_counter() - started}
        else:
            result, info = engine.ask(q, units, method="hybrid" if method in ("links", "cross_encoder") else method,
                                      links=method == "links", reranker=reranker, depth=depth,
                                      reader=reader, qa_mode=qa_mode)
            ranking = info["ranked_cards"]
            times = info["seconds"]
        answer = result.answer if result else ""
        used = [u.id for u in result.units] if result else []
        rows.append({"query": q, "domain": case["domain"], "type": case.get("type", case.get("status", "unknown")),
                     "ranking": list(dict.fromkeys(ranking))[:10], "sources": used, "answer": answer,
                     "seconds": {**times, "total": perf_counter() - start},
                     "metrics": _metrics(case, ranking, answer, used)})
    try:
        encoder_version = version("sentence-transformers")
    except PackageNotFoundError:
        encoder_version = None
    report = {"method": method, "split": split, "python": platform.python_version(),
              "sentence_transformers": encoder_version,
              "cases_sha256": hashlib.sha256(Path(cases_path).read_bytes()).hexdigest(),
              "index": status, "cold_setup_seconds": cold_setup, "first_query_seconds": rows[0]["seconds"]["total"],
              "peak_rss_mib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
              "overall": summarize(rows), "warm": summarize(rows[1:]), "queries": rows}
    if engine is not None:
        from .retrieval import FIELD_WEIGHTS, RRF_K, POOL, DENSE_WEIGHTS
        report["retrieval_index"] = engine.metadata
        report["config"] = dict(field_weights=FIELD_WEIGHTS, rrf_k=RRF_K, candidate_pool=POOL,
                                dense_weight=DENSE_WEIGHTS, evidence_depth=depth, qa_mode=qa_mode)
    if reranker_path:
        weights = Path(reranker_path) / "model.safetensors"
        report["reranker"] = {"directory": str(reranker_path)}
        if weights.is_file():
            with weights.open("rb") as stream:
                report["reranker"]["weights_sha256"] = hashlib.file_digest(stream, "sha256").hexdigest()
    for field in ("domain", "type"):
        groups = defaultdict(list)
        for row in rows:
            groups[row[field]].append(row)
        report[f"by_{field}"] = {key: summarize(group) for key, group in groups.items()}
    if output:
        Path(output).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    return report
