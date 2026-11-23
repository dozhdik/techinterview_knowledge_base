from dataclasses import dataclass, field
from collections import Counter
from math import log
import re
from pathlib import Path
from typing import Optional

from .parser import KnowledgeUnit


@dataclass
class SearchQuery:
    domain:           Optional[str]       = None
    category:         Optional[str]       = None
    difficulty:       Optional[str]       = None
    role:             Optional[str]       = None
    interview_stage:  Optional[str]       = None
    tags:             list[str]           = field(default_factory=list)
    text:             Optional[str]       = None
    status:           Optional[str]       = None
    frequency:        Optional[str]       = None


@dataclass
class SearchResult:
    unit:      KnowledgeUnit
    score:     int
    matched:   list[str] = field(default_factory=list)

    def __repr__(self) -> str:
        return (
            f"SearchResult(id={self.unit.id!r}, "
            f"title={self.unit.title!r}, score={self.score})"
        )


def search(
    units: list[KnowledgeUnit],
    query: SearchQuery,
) -> list[SearchResult]:
    results = []

    for unit in units:
        score, matched = _score_unit(unit, query)
        if score > 0:
            results.append(SearchResult(unit=unit, score=score, matched=matched))

    results.sort(key=lambda r: r.score, reverse=True)
    return results


_QUESTION_STOP_WORDS = set("""
    а без быть в во вот вы где да для до его ее есть еще же за зачем и из или их
    к как какая какие какой когда кто ли мне на над не но о об он она они от по
    под при про с со так там то такое у что это этой этот я
    расскажи расскажите объясни объясните устроен устроена устроены работает
    спроектируй подготовиться отвечать выбирать каждый чем отличается
    выбрать проекта дай дайте определение определению определении
    определите покажи покажите карточку термин понятие означает значит
    the a an and or to of in on is are how what when why does do can i define
""".split())
_RUSSIAN_ENDINGS = (
    "иями", "ами", "ями", "ого", "ему", "ому", "ыми", "ими", "ией",
    "ий", "ый", "ой", "ая", "яя", "ое", "ее", "ые", "ие", "ов", "ев",
    "ом", "ем", "ам", "ям", "ах", "ях", "ую", "юю", "а", "я", "ы", "и", "у", "ю", "е", "о",
)


def _question_words(text: str) -> list[str]:
    terms = []
    for word in re.findall(r"[a-zа-я0-9]+", text.lower().replace("ё", "е")):
        if len(word) < 2 or word.isdigit() or word in _QUESTION_STOP_WORDS:
            continue
        word = {"hash": "хеш", "хэш": "хеш", "table": "таблиц", "tables": "таблиц"}.get(word, word)
        if re.fullmatch(r"[а-я]+", word):
            for ending in _RUSSIAN_ENDINGS:
                if word.endswith(ending) and len(word) - len(ending) >= 3:
                    word = word[:-len(ending)]
                    break
        terms.append(word)
    return terms


def _question_terms(text: str) -> set[str]:
    return set(_question_words(text))


def requested_card_ids(question: str) -> list[str]:
    return list(dict.fromkeys(re.findall(r"\b[A-Z]+-[A-Z]+-\d+\b", question.upper())))


def _is_definition_question(question: str) -> bool:
    return bool(re.search(r"\b(?:что\s+такое|что\s+значит|дай(?:те)?\s+определение|"
                          r"определение\s+|what\s+is|define\s+)", question.lower()))


def _has_named_definition(unit: KnowledgeUnit, words: list[str], tags: set[str]) -> bool:
    if not words:
        return False
    title = _question_words(unit.title)
    filename = _question_words(Path(unit.file_path).stem)
    if len(words) == 1:
        return words[0] in set(title) | set(filename) | tags
    width = len(words)
    return (any(title[i:i + width] == words for i in range(len(title) - width + 1))
            or any(filename[i:i + width] == words for i in range(len(filename) - width + 1))
            or set(words).issubset(tags))


def search_question(
    units: list[KnowledgeUnit], question: str, limit: int = 3,
) -> list[SearchResult]:
    if limit <= 0:
        return []
    requested_ids = set(requested_card_ids(question))
    if requested_ids:
        return [SearchResult(unit=u, score=100, matched=["id"])
                for u in units if u.id.upper() in requested_ids][:limit]

    query_words = _question_words(question)
    query_terms = set(query_words)
    if not query_terms:
        return []
    documents = [(_question_terms(u.title + " " + Path(u.file_path).stem), _question_terms(" ".join(u.tags)),
                  _question_terms(u.content)) for u in units]
    frequency = Counter(term for fields in documents for term in set.union(*fields))
    results = []
    for unit, (title, tags, content) in zip(units, documents):
        matched = query_terms & (title | tags | content)
        coverage = len(matched) / len(query_terms)
        if coverage < 0.75 or not matched & (title | tags):
            continue
        if _is_definition_question(question) and not _has_named_definition(unit, query_words, tags):
            continue
        score = sum(
            (8 if term in title else 4 if term in tags else 1)
            * (1 + log((len(units) + 1) / (frequency[term] + 1)))
            for term in matched
        ) * coverage
        results.append(SearchResult(unit=unit, score=round(score * 100), matched=sorted(matched)))
    results.sort(key=lambda result: (-result.score, result.unit.id))
    return results[:limit]


def _score_unit(
    unit: KnowledgeUnit,
    query: SearchQuery,
) -> tuple[int, list[str]]:
    score = 0
    matched = []


    if query.domain is not None:
        if unit.domain != query.domain:
            return 0, []
        score += 10
        matched.append(f"domain={unit.domain}")

    if query.category is not None:
        if unit.category != query.category:
            return 0, []
        score += 10
        matched.append(f"category={unit.category}")

    if query.difficulty is not None:
        if unit.difficulty != query.difficulty:
            return 0, []
        score += 10
        matched.append(f"difficulty={unit.difficulty}")

    if query.role is not None:
        if "all_roles" not in unit.roles and query.role not in unit.roles:
            return 0, []
        score += 8
        matched.append(f"role={query.role}")

    if query.interview_stage is not None:
        if query.interview_stage not in unit.interview_stage:
            return 0, []
        score += 8
        matched.append(f"stage={query.interview_stage}")

    if query.status is not None:
        if unit.status != query.status:
            return 0, []
        score += 5
        matched.append(f"status={unit.status}")

    if query.frequency is not None:
        if unit.frequency != query.frequency:
            return 0, []
        score += 5
        matched.append(f"frequency={unit.frequency}")

    if query.tags:
        for tag in query.tags:
            if tag not in unit.tags:
                return 0, []
            score += 5
            matched.append(f"tag={tag}")

    if query.text:
        text_lower = query.text.lower()
        title_lower = unit.title.lower()
        content_lower = unit.content.lower()

        if text_lower in title_lower:
            score += 20
            matched.append(f"title contains '{query.text}'")

        elif text_lower in unit.id.lower():
            score += 15
            matched.append(f"id contains '{query.text}'")

        elif any(text_lower in tag for tag in unit.tags):
            score += 10
            matched.append(f"tag contains '{query.text}'")

        elif text_lower in content_lower:
            score += 5
            matched.append(f"content contains '{query.text}'")

        else:
            return 0, []

    if score == 0:
        score = 1
        matched.append("no filters (match all)")

    return score, matched


def search_by_domain(
    units: list[KnowledgeUnit],
    domain: str,
) -> list[SearchResult]:
    return search(units, SearchQuery(domain=domain))


def search_by_difficulty(
    units: list[KnowledgeUnit],
    difficulty: str,
) -> list[SearchResult]:
    return search(units, SearchQuery(difficulty=difficulty))


def search_by_tag(
    units: list[KnowledgeUnit],
    tag: str,
) -> list[SearchResult]:
    return search(units, SearchQuery(tags=[tag]))


def search_by_role(
    units: list[KnowledgeUnit],
    role: str,
) -> list[SearchResult]:
    return search(units, SearchQuery(role=role))


def search_by_text(
    units: list[KnowledgeUnit],
    text: str,
) -> list[SearchResult]:
    return search(units, SearchQuery(text=text))


def print_results(results: list[SearchResult], verbose: bool = False) -> None:
    if not results:
        print("🔍 Ничего не найдено.")
        return

    print(f"🔍 Найдено: {len(results)}\n")
    for i, result in enumerate(results, 1):
        unit = result.unit
        print(f"{i:>3}. [{unit.id}] {unit.title}")
        print(f"       {unit.domain} / {unit.category} / {unit.difficulty}")
        if verbose:
            print(f"       score={result.score} | matched: {', '.join(result.matched)}")
            if unit.tags:
                print(f"       tags: {', '.join(unit.tags[:5])}")
        print()
