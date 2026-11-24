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
    спроектируй подготовиться отвечать выбирать каждый чем отличается принцип работы следует
    выбрать проекта дай дайте определение определению определении
    определите покажи покажите карточку термин понятие означает значит
    отличие отличия отличий отличаются сравни сравните разница них
    лучше стоит использовать пример примеры
    the a an and or to of in on is are how what when why does do can i define
    difference between versus vs compare differ from
""".split())
_RUSSIAN_ENDINGS = (
    "иями", "ами", "ями", "ого", "ему", "ому", "ыми", "ими", "ией",
    "ий", "ый", "ой", "ая", "яя", "ое", "ее", "ые", "ие", "ов", "ев",
    "ом", "ем", "ам", "ям", "ах", "ях", "ую", "юю", "а", "я", "ы", "и", "у", "ю", "е", "о",
)


_TECHNICAL_ALIASES = {
    "bfs": ("поиск в ширину", "обход в ширину", "обход графа в ширину",
            "breadth first search", "breadth first traversal"),
    "dfs": ("поиск в глубину", "обход в глубину", "обход графа в глубину",
            "depth first search", "depth first traversal"),
    "bst": ("бинарное дерево поиска", "двоичное дерево поиска", "binary search tree"),
    "binarysearch": ("бинарный поиск", "binary search"),
    "scaling": ("масштабирование", "scaling"),
    "hashmap": ("хеш таблица", "хэш таблица", "hash table", "hash tables", "hash map"),
    "bloomfilter": ("фильтр блума", "bloom filter"),
    "dsu": ("disjoint set union", "union find", "система непересекающихся множеств"),
    "cdn": ("content delivery network", "сеть доставки контента"),
    "ttl": ("time to live", "время жизни записи"),
    "mvcc": ("multiversion concurrency control", "многоверсионное управление конкурентным доступом"),
    "cap": ("теорема cap", "cap theorem"),
}


def _stem_words(text: str) -> list[str]:
    terms = []
    for word in re.findall(r"[a-zа-я0-9]+", text.lower().replace("ё", "е")):
        if word in _QUESTION_STOP_WORDS or word.isdigit():
            terms.append(word)
            continue
        word = {"hash": "хеш", "хэш": "хеш", "table": "таблиц", "tables": "таблиц"}.get(word, word)
        if re.fullmatch(r"[а-я]+", word):
            for ending in _RUSSIAN_ENDINGS:
                if word.endswith(ending) and len(word) - len(ending) >= 3:
                    word = word[:-len(ending)]
                    break
        terms.append(word)
    return terms


_ALIAS_TO_TERM = {
    tuple(_stem_words(alias)): term
    for term, aliases in _TECHNICAL_ALIASES.items()
    for alias in aliases
}
_ALIAS_LENGTHS = sorted({len(alias) for alias in _ALIAS_TO_TERM}, reverse=True)


def _question_words(text: str) -> list[str]:
    words = _stem_words(text)
    terms = []
    offset = 0
    while offset < len(words):
        for length in _ALIAS_LENGTHS:
            term = _ALIAS_TO_TERM.get(tuple(words[offset:offset + length]))
            if term:
                offset += length
                break
        else:
            term = words[offset]
            offset += 1
        if len(term) >= 2 and not term.isdigit() and term not in _QUESTION_STOP_WORDS:
            if not terms or term != terms[-1] or term not in _TECHNICAL_ALIASES:
                terms.append(term)
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
    return _matches_named_definition(words, title, filename, tags)


def _matches_named_definition(words, title, filename, tags):
    if len(words) == 1:
        return words[0] in set(title) | set(filename) | tags
    width = len(words)
    return (any(title[i:i + width] == words for i in range(len(title) - width + 1))
            or any(filename[i:i + width] == words for i in range(len(filename) - width + 1))
            or set(words).issubset(tags))


def lexical_chunk_scores(question, chunks, tags_by_card):
    words = _question_words(question)
    terms = set(words)
    if not terms:
        return [None] * len(chunks)

    titles = {}
    bodies = {}
    passages = []
    for card_id, title, text in chunks:
        if card_id not in titles:
            titles[card_id] = _question_words(title)
            bodies[card_id] = set()
        passage = terms & _question_terms(text)
        bodies[card_id].update(passage)
        passages.append(passage)
    tags = {card_id: _question_terms(" ".join(tags_by_card.get(card_id, ()))) for card_id in titles}
    names = {card_id: set(title) | tags[card_id] for card_id, title in titles.items()}
    frequency = Counter(term for card_id in titles for term in terms & (names[card_id] | bodies[card_id]))
    weights = {term: 1 + log((len(titles) + 1) / (frequency[term] + 1)) for term in terms}
    total_weight = sum(weights.values())
    topics = terms & _TECHNICAL_ALIASES.keys()
    definition = _is_definition_question(question)
    results = []
    for (card_id, _, _), passage in zip(chunks, passages):
        title = titles[card_id]
        title_matches = terms & set(title)
        named_matches = terms & names[card_id]
        matched = named_matches | bodies[card_id]
        coverage = sum(weights[term] for term in matched) / total_weight
        partial_comparison = len(topics) > 1 and bool(topics & named_matches)
        if (not matched
                or topics and not topics & matched
                or coverage < 0.55 and not partial_comparison
                or definition and not _matches_named_definition(words, title, [], tags[card_id])):
            results.append(None)
            continue
        if not named_matches and (coverage < 0.75 or topics - matched or not any(
                frequency[term] <= max(1, len(titles) * 0.1) for term in passage
        )):
            results.append(None)
            continue

        if words == title:
            priority = 4
        elif terms <= title_matches:
            priority = 3
        elif partial_comparison and title and set(title) <= topics:
            priority = 2
        else:
            priority = int(bool(named_matches))
        score = sum(
            weights[term] * (
                (0.85 if term in title_matches else 0.6 if term in named_matches else 0.1)
                + (0.15 if term in passage else 0)
            )
            for term in matched
        ) / total_weight
        results.append((priority, score))
    return results


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
