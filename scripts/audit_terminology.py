"""List declared and inferred names for every card and summarize editorial coverage."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from kb.entities import entity_index
from kb.parser import parse_directory
from kb.titles import _DEFINITION, name_keys, normalize_title, title_index
from kb.validator import validate_all

LANGUAGES = (("ru", re.compile(r"[а-яё]{2,}", re.I)), ("en", re.compile(r"[a-z]{2,}", re.I)))


def audit(root):
    cards = [u for domain in ("cs", "arch", "process") for u in parse_directory(root / domain, skip_errors=False)]
    indexed = title_index(cards)
    aliases = defaultdict(set)
    abbreviations = defaultdict(set)
    for field, owner_names in (("alias", aliases), ("abbreviation", abbreviations)):
        for name, owners in indexed.names[field].items():
            for cid in owners:
                owner_names[cid].add(name)

    rows = []
    for u in cards:
        names = {normalize_title(u.title), *aliases[u.id]}
        flags = {key: any(pattern.search(name) for name in names) for key, pattern in LANGUAGES}
        definition = _DEFINITION.search(u.content)
        intro = re.split(r"\s+[—–]\s+|\s+[-:]\s+", definition[2], maxsplit=1)[0] if definition else ""
        intro_keys = name_keys(intro)
        # Only detect labels at the beginning, rather than mentions anywhere in the definition.
        explicit_subject = any(keys and intro_keys[:len(keys)] == keys
                               for name in names | abbreviations[u.id] if (keys := name_keys(name)))
        rows.append({
            "id": u.id, "domain": u.domain, "title": u.title,
            "aliases": u.aliases, "abbreviations": u.abbreviations,
            "search_aliases": sorted(aliases[u.id]), "search_abbreviations": sorted(abbreviations[u.id]),
            "ru_form": flags["ru"], "en_form": flags["en"],
            "english_title": bool(LANGUAGES[1][1].search(u.title) and not LANGUAGES[0][1].search(u.title)),
            "explicit_definition_subject": explicit_subject,
        })

    def summary(group):
        return {
            "cards": len(group), "cards_with_aliases": sum(bool(r["aliases"]) for r in group),
            "cards_with_abbreviations": sum(bool(r["abbreviations"]) for r in group),
            "cards_with_any_declared_names": sum(bool(r["aliases"] or r["abbreviations"]) for r in group),
            "alias_count": sum(len(r["aliases"]) for r in group),
            "abbreviation_count": sum(len(r["abbreviations"]) for r in group),
            "cards_with_indexed_variants": sum(bool(r["search_aliases"] or r["search_abbreviations"]) for r in group),
            "ru_forms": sum(r["ru_form"] for r in group), "en_forms": sum(r["en_form"] for r in group),
            "both_scripts": sum(r["ru_form"] and r["en_form"] for r in group),
            "english_titles": sum(r["english_title"] for r in group),
            "english_titles_with_ru_form": sum(r["english_title"] and r["ru_form"] for r in group),
            "definition_subject": sum(r["explicit_definition_subject"] for r in group),
        }

    validation = validate_all(cards)
    inferred = {name[0].upper(): sorted(forms["inferred_abbreviation"])
                for name, forms in entity_index(indexed).entries.items() if "inferred_abbreviation" in forms}
    return {"inferred_ambiguities": inferred, "overall": summary(rows), "domains": {
        d: summary([r for r in rows if r["domain"] == d]) for d in sorted({u.domain for u in cards})
    }, "terminology_issues": [vars(issue) for issue in validation.issues
                              if issue.field in {"title", "aliases", "abbreviations"}], "cards": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(json.dumps(audit(args.root), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
