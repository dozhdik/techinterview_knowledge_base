"""
kb/search.py

Поиск по базе знаний TechInterview.

Поддерживает:
- поиск по тегам
- поиск по домену (cs / arch / process / global)
- поиск по категории (concept / problem / sysdesign и т.д.)
- поиск по уровню сложности (junior / middle / senior / staff)
- поиск по роли (backend / frontend и т.д.)
- поиск по этапу собеседования (coding / behavioral и т.д.)
- полнотекстовый поиск по заголовку и содержимому
- комбинированный поиск (несколько фильтров одновременно)
"""

from dataclasses import dataclass, field
from typing import Optional

from .parser import KnowledgeUnit


# ---------------------------------------------------------------------------
# Dataclass — параметры поиска
# ---------------------------------------------------------------------------

@dataclass
class SearchQuery:
    """
    Параметры поискового запроса.
    Все поля необязательные — указывай только нужные фильтры.

    Пример:
        query = SearchQuery(domain="cs", difficulty="junior", tags=["arrays"])
    """
    domain:           Optional[str]       = None  # cs | arch | process | global
    category:         Optional[str]       = None  # concept | problem | sysdesign | ...
    difficulty:       Optional[str]       = None  # junior | middle | senior | staff
    role:             Optional[str]       = None  # backend | frontend | ...
    interview_stage:  Optional[str]       = None  # coding | behavioral | ...
    tags:             list[str]           = field(default_factory=list)
    text:             Optional[str]       = None  # полнотекстовый поиск
    status:           Optional[str]       = None  # draft | review | approved
    frequency:        Optional[str]       = None  # high | medium | low


# ---------------------------------------------------------------------------
# Dataclass — результат поиска
# ---------------------------------------------------------------------------

@dataclass
class SearchResult:
    """Один результат поиска с информацией о релевантности."""
    unit:      KnowledgeUnit
    score:     int    # очки релевантности (чем больше — тем лучше совпадение)
    matched:   list[str] = field(default_factory=list)  # что именно совпало

    def __repr__(self) -> str:
        return (
            f"SearchResult(id={self.unit.id!r}, "
            f"title={self.unit.title!r}, score={self.score})"
        )


# ---------------------------------------------------------------------------
# Основные функции поиска
# ---------------------------------------------------------------------------

def search(
    units: list[KnowledgeUnit],
    query: SearchQuery,
) -> list[SearchResult]:
    """
    Ищет единицы знаний по заданным критериям.
    Возвращает список SearchResult, отсортированный по релевантности (score).

    Пример:
        units = parse_directory(".")
        results = search(units, SearchQuery(domain="cs", difficulty="junior"))
        for r in results:
            print(r.unit.id, r.unit.title)
    """
    results = []

    for unit in units:
        score, matched = _score_unit(unit, query)
        if score > 0:
            results.append(SearchResult(unit=unit, score=score, matched=matched))

    # Сортируем по убыванию релевантности
    results.sort(key=lambda r: r.score, reverse=True)
    return results


def _score_unit(
    unit: KnowledgeUnit,
    query: SearchQuery,
) -> tuple[int, list[str]]:
    """
    Вычисляет очки релевантности единицы знаний для данного запроса.
    Возвращает (score, matched_fields).
    score == 0 означает что единица не соответствует запросу.
    """
    score = 0
    matched = []

    # --- Фильтры — при несовпадении сразу исключаем (score=0) ---

    # domain — точное совпадение
    if query.domain is not None:
        if unit.domain != query.domain:
            return 0, []
        score += 10
        matched.append(f"domain={unit.domain}")

    # category — точное совпадение
    if query.category is not None:
        if unit.category != query.category:
            return 0, []
        score += 10
        matched.append(f"category={unit.category}")

    # difficulty — точное совпадение
    if query.difficulty is not None:
        if unit.difficulty != query.difficulty:
            return 0, []
        score += 10
        matched.append(f"difficulty={unit.difficulty}")

    # role — единица подходит если содержит "all_roles" или указанную роль
    if query.role is not None:
        if "all_roles" not in unit.roles and query.role not in unit.roles:
            return 0, []
        score += 8
        matched.append(f"role={query.role}")

    # interview_stage — точное совпадение в списке
    if query.interview_stage is not None:
        if query.interview_stage not in unit.interview_stage:
            return 0, []
        score += 8
        matched.append(f"stage={query.interview_stage}")

    # status — точное совпадение
    if query.status is not None:
        if unit.status != query.status:
            return 0, []
        score += 5
        matched.append(f"status={unit.status}")

    # frequency — точное совпадение
    if query.frequency is not None:
        if unit.frequency != query.frequency:
            return 0, []
        score += 5
        matched.append(f"frequency={unit.frequency}")

    # tags — единица должна содержать ВСЕ указанные теги
    if query.tags:
        for tag in query.tags:
            if tag not in unit.tags:
                return 0, []
            score += 5
            matched.append(f"tag={tag}")

    # --- Полнотекстовый поиск (мягкий — влияет только на score) ---
    if query.text:
        text_lower = query.text.lower()
        title_lower = unit.title.lower()
        content_lower = unit.content.lower()

        # Совпадение в заголовке — высокий вес
        if text_lower in title_lower:
            score += 20
            matched.append(f"title contains '{query.text}'")

        # Совпадение в ID
        elif text_lower in unit.id.lower():
            score += 15
            matched.append(f"id contains '{query.text}'")

        # Совпадение в тегах
        elif any(text_lower in tag for tag in unit.tags):
            score += 10
            matched.append(f"tag contains '{query.text}'")

        # Совпадение в содержимом
        elif text_lower in content_lower:
            score += 5
            matched.append(f"content contains '{query.text}'")

        # Если текстовый поиск задан но ничего не нашли — исключаем
        else:
            return 0, []

    # Если не задано ни одного фильтра — возвращаем все единицы с базовым score
    if score == 0:
        score = 1
        matched.append("no filters (match all)")

    return score, matched


# ---------------------------------------------------------------------------
# Удобные функции-обёртки для частых случаев
# ---------------------------------------------------------------------------

def search_by_domain(
    units: list[KnowledgeUnit],
    domain: str,
) -> list[SearchResult]:
    """Возвращает все единицы знаний указанного домена."""
    return search(units, SearchQuery(domain=domain))


def search_by_difficulty(
    units: list[KnowledgeUnit],
    difficulty: str,
) -> list[SearchResult]:
    """Возвращает все единицы знаний указанного уровня сложности."""
    return search(units, SearchQuery(difficulty=difficulty))


def search_by_tag(
    units: list[KnowledgeUnit],
    tag: str,
) -> list[SearchResult]:
    """Возвращает все единицы знаний с указанным тегом."""
    return search(units, SearchQuery(tags=[tag]))


def search_by_role(
    units: list[KnowledgeUnit],
    role: str,
) -> list[SearchResult]:
    """Возвращает все единицы знаний релевантные для указанной роли."""
    return search(units, SearchQuery(role=role))


def search_by_text(
    units: list[KnowledgeUnit],
    text: str,
) -> list[SearchResult]:
    """Полнотекстовый поиск по заголовку, ID, тегам и содержимому."""
    return search(units, SearchQuery(text=text))


# ---------------------------------------------------------------------------
# Вывод результатов
# ---------------------------------------------------------------------------

def print_results(results: list[SearchResult], verbose: bool = False) -> None:
    """
    Выводит результаты поиска в консоль.

    Параметры:
        results — список SearchResult
        verbose — если True, выводит дополнительную информацию
    """
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
