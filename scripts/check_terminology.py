"""Run the editorial terminology benchmark against an existing local server."""
import argparse
import json
from pathlib import Path
import sys
from time import perf_counter
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]


def replay(url, cases):
    rows = []
    for case in cases:
        payload = {"question": case["query"]}
        request = Request(f"{url.rstrip('/')}/api/ask", data=json.dumps(payload).encode(),
                          headers={"Content-Type": "application/json"})
        start = perf_counter()
        with urlopen(request, timeout=60) as response:
            answer = json.load(response)
        ms = (perf_counter() - start) * 1000
        if answer["is_rag_enabled"] or answer["search_notice"]:
            raise RuntimeError("Тест требует готового структурного поиска в экстрактивном режиме.")
        rows.append({"id": case["id"], "ms": ms, "body": answer})
    return rows


def direct_cases(legacy_root):
    sys.path.insert(0, str(ROOT))
    from kb.content import has_material
    from kb.parser import parse_directory
    from kb.titles import title_index

    def read_cards(folder):
        return [u for domain in ("cs", "arch", "process") for u in parse_directory(folder / domain)
                if u.status != "draft" and has_material(u)]

    entries = [("declared", name, u.id) for u in read_cards(ROOT) for name in (*u.aliases, *u.abbreviations)]
    if legacy_root:
        legacy = read_cards(legacy_root)
        names = title_index(legacy)
        for u in legacy:
            entries.extend(("legacy", name, u.id) for name in (
                u.title, u.title.lower(), u.title.upper(), "  " + "   ".join(u.title.split()) + "  ",
                f"«{u.title}»!", u.id,
            ))
        for kind in ("alias", "abbreviation"):
            entries.extend(("legacy", name, next(iter(ids))) for name, ids in names.names[kind].items()
                           if len(ids) == 1 and name not in names.names["title"])
    return [{"id": f"{kind}-{index}", "query": query, "expected_ids": [cid]}
            for index, (kind, query, cid) in enumerate(entries, 1)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--cases", type=Path)
    group.add_argument("--declared", action="store_true", help="Check current YAML names")
    group.add_argument("--with-legacy", type=Path, metavar="BASELINE_CORPUS",
                       help="Check current YAML names and the old direct queries")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.declared or args.with_legacy:
        cases = direct_cases(args.with_legacy)
    else:
        path = args.cases or ROOT / "evaluation/terminology_holdout.json"
        cases = json.loads(path.read_text(encoding="utf-8"))
    rows = replay(args.url, cases)
    args.output.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Проверено {len(rows)} запросов.")
    if args.declared or args.with_legacy:
        failed = [r["id"] for case, r in zip(cases, rows)
                  if r["body"]["search_state"] != "complete"
                  or [s["id"] for s in r["body"]["sources"]] != case["expected_ids"]]
        if failed:
            raise SystemExit(f"Не прошли прямую проверку: {', '.join(failed)}")


if __name__ == "__main__":
    main()
