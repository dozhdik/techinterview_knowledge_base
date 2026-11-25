"""Send the 318 established scenarios to a running local TechInterview server."""
import argparse
import json
from math import ceil
from pathlib import Path
from statistics import median
from time import perf_counter
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]


def load_cases():
    report = (ROOT / "RAG_TEST.md").read_text()
    first = json.loads(report.split("```json\n", 1)[1].split("\n```", 1)[0])
    yield from first
    for iteration in (2, 3, 4):
        file = ROOT / "evaluation" / f"search_holdout_iteration{iteration}.json"
        yield from json.loads(file.read_text())


def run(base_url):
    rows = []
    for case in load_cases():
        request = Request(
            base_url.rstrip("/") + "/api/ask",
            data=json.dumps({"question": case["query"]}).encode(),
            headers={"Content-Type": "application/json"},
        )
        started = perf_counter()
        with urlopen(request, timeout=60) as response:
            result = json.load(response)
        elapsed_ms = (perf_counter() - started) * 1000
        if result["is_rag_enabled"]:
            raise RuntimeError("Проверка рассчитана на экстрактивный режим.")
        answered = {item["id"] for item in result["sources"]}
        suggested = {item["id"] for item in result["related_materials"]}
        if answered & suggested:
            raise AssertionError(f"Источники и рекомендации пересекаются для {case['id']}")
        rows.append({"id": case["id"], "expected": case["status"], "milliseconds": elapsed_ms,
                     "body": result})
    return rows


def summarize(rows):
    samples = sorted(row["milliseconds"] for row in rows)
    positives = [row for row in rows if row["expected"] in ("full", "partial")]
    negatives = [row for row in rows if row["expected"] == "absent"]
    return {
        "cases": len(rows),
        "latency_median_ms": round(median(samples), 2),
        "latency_p95_ms": round(samples[ceil(len(samples) * .95) - 1], 2),
        "refusals_on_positive": sum(not row["body"]["sources"] for row in positives),
        "positives": len(positives),
        "answers_on_negative": sum(bool(row["body"]["sources"]) for row in negatives),
        "negatives": len(negatives),
        "with_related_materials": sum(bool(row["body"]["related_materials"]) for row in rows),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    rows = run(args.url)
    summary = {"regression": summarize(rows[:267]), "holdout": summarize(rows[267:]),
               "overall": summarize(rows)}
    args.output.write_text(json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
