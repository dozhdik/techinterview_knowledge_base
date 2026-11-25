"""Language normalization and lightweight query features for retrieval."""
import re
import unicodedata
from dataclasses import dataclass, replace

from .search import _question_words


def normalize(value):
    return " ".join(unicodedata.normalize("NFKC", value).casefold().replace("ё", "е").split())


def terms(value):
    return _question_words(normalize(value))


_INTENTS = {
    "definition": (r"что такое|что означает|\bdefine\b|what is", "определение", "назначение", "суть"),
    "comparison": (r"отлича|сравн|\bvs\b|difference|вместо", "сравнен", "компромисс", "выбор", "вариант"),
    "complexity": (r"сложност|памят|o\(", "сложност", "характеристик", "главное", "границ"),
    "limits": (r"ошиб|недостат|преимуществ|ограничен", "ошиб", "ограничен", "недостат", "преимуществ", "границ"),
    "practice": (r"пример|реализ|примен|когда|как (?:сделать|решить)", "пример", "примен", "шаблон", "когда", "подход"),
    "mechanism": (r"как|почему|зачем|how|why", "как", "суть", "подход", "главное", "алгоритм"),
    "procedure": (r"\b(?:по шагам|в каком порядке|как (?:найти|решить|посчитать|вычислить|реализовать|"
                  r"развернуть|восстановить|выбрать|проверить|обнаружить|получить|сохранить|"
                  r"отсортировать|построить|организовать)|алгоритм|инвариант|how to|steps)\b",
                  "подход", "как", "алгоритм", "реализац", "шаг"),
    "design": (r"\b(?:спроектир\w*|design a|архитектур\w+ решени\w*|разработать систем\w*)\b",
               "шаг", "требован", "архитектур", "модель данных"),
    "quantity": (r"\b(?:сколько|какова сложность|какая сложность|асимптотик\w*|"
                 r"как\w* (?:времен\w*|пространственн\w+) сложность|how (?:long|much|many))\b",
                 "сложност", "характеристик", "главное"),
}


_INFORMATION = {
    "definition": r"\b(?:что (?:такое|означает)|определен\w*|what is|define)\b",
    "mechanism": r"\b(?:как (?:работает|устроен\w*|действует)|механизм|принцип работы|почему|зачем|how does|why)\b",
    "time_complexity": r"\b(?:временн(?:ая|ой|ую|ые|ым|ых|ом)|асимптотик\w* по времени|сложность по времени|time complexity|сколько времени (?:занимает|требуется))\b",
    "space_complexity": r"\b(?:пространственн\w*|(?:расход\w*|потреблен\w*|дополнительн\w*|ограничить) памят\w*|сколько [^?;]{0,30}памят\w*|памят\w* (?:нужн\w*|занима\w*)|space complexity|memory usage|auxiliary space)\b",
    "procedure": r"\b(?:порядок действий|пошагов\w*|по шагам|как (?:найти|посчитать|сохранить|восстановить|проверить|подготовиться|провести)|steps|how to)\b",
    "implementation": r"\b(?:реализ\w*|псевдокод\w*|напиши\w* код|алгоритм действий|implement\w*|pseudocode)\b",
    "comparison": r"\b(?:отлич\w*|разниц\w*|сравн\w*|соотносятся|вместо|по-разному|vs|versus|difference|compare)\b",
    "advantages": r"\b(?:преимуществ\w*|плюсы|выгода|benefits?|advantages?)\b",
    "disadvantages": r"\b(?:недостат\w*|минусы|потери|disadvantages?|drawbacks?)\b",
    "limitations": r"\b(?:ограничен\w*|нельзя|не подходит|границ\w* применимости|limitations?)\b",
    "use_cases": r"\b(?:когда (?:лучше|уместн\w*|стоит|использ\w*|примен\w*|выбира\w*)|сценари\w* примен\w*|use cases?|when to use)\b",
    "pitfalls": r"\b(?:ошиб\w*|подводн\w* камн\w*|pitfalls?|gotchas?)\b",
    "example": r"\b(?:пример\w*|покажи на|проиллюстрируй|examples?)\b",
    "design": r"\b(?:спроектир\w*|проектировани\w*|архитектур\w+ решени\w*|design a)\b",
    "interview": r"\b(?:собеседован\w*|интервью\w*|рекрутер\w*|interview\w*)\b",
}


def information_needs(value):
    cleaned = normalize(value)
    found = [name for name, pattern in _INFORMATION.items() if re.search(pattern, cleaned)]
    if "сложность" in cleaned and not {"time_complexity", "space_complexity"}.intersection(found):
        found.extend(("time_complexity", "space_complexity"))
    return tuple(found or ("unknown",))


@dataclass(frozen=True)
class Query:
    raw: str
    normalized: str
    tokens: tuple
    intents: tuple

    @classmethod
    def parse(cls, value):
        cleaned = normalize(value)
        return cls(value, cleaned, tuple(dict.fromkeys(terms(cleaned))),
                   tuple(name for name, (pattern, *_) in _INTENTS.items() if re.search(pattern, cleaned)))

    def heading_signal(self, heading):
        heading = normalize(heading)
        return any(substring in heading for name in self.intents if name not in {"procedure", "design", "quantity"}
                   for substring in _INTENTS[name][1:])


_COORDINATED_FACETS = re.compile(
    r"\s+(?:и|а также|and)\s+"
    r"(?=(?:как|почему|зачем|что|когда|какие|какая|какова|сколько|how|why|what|when)\s)"
    r"(?!(?:как|почему|зачем|что|когда|how|why|what|when)\s+(?:это|он[аи]?|it|this|they)\b)", re.I
)


def facets(question):
    # An explicitly delimited question may introduce another topic. A short
    # coordinated clause keeps the subject and its qualifiers in the same search.
    result = []
    for phrase in re.split(r"[;?]\s*", question):
        breaks = list(_COORDINATED_FACETS.finditer(phrase))
        start = 0
        for match, stop in zip(breaks, [m.start() for m in breaks[1:]] + [len(phrase)]):
            if len(terms(phrase[match.end():stop])) < 3:
                continue
            result.append(phrase[start:match.start()].strip())
            start = match.end()
        result.append(phrase[start:].strip())
    return [part for part in result if part] or [question]


_FOLLOW_UP = re.compile(
    r"^\s*(?:а\s+)?(?:(?:какая|какова)\s+(?:(?:временн\w+|пространственн\w+)\s+)?сложность"
    r"|сколько (?:времени|памяти) (?:это |он[ао]? )?(?:занимает|требует)"
    r"|(?:как|почему|зачем|что|когда)\s+(?:это|он[аи]?|оно)\b"
    r"|(?:how|why|what|when)\s+(?:does it|is it|is this|does this)\b)", re.I
)


def with_facet_context(query, previous):
    """Keep explicitly dependent subquestions attached to their previous subject."""
    match = _FOLLOW_UP.search(query.raw)
    if previous is None or not match:
        return query
    tail = terms(query.raw[match.end():])
    if tail and ("quantity" in query.intents or len(tail) > 3):
        return query
    return replace(query, normalized=f"{query.normalized}. {previous.normalized}",
                   tokens=tuple(dict.fromkeys((*query.tokens, *previous.tokens))))
