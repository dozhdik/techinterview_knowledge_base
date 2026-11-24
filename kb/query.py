"""Language normalization and lightweight query features for retrieval."""
import re
import unicodedata
from dataclasses import dataclass

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
}


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
        return any(substring in heading for name in self.intents for substring in _INTENTS[name][1:])


def facets(question):
    # Keep comparative phrases intact. Split only clauses with their own clear question.
    parts = re.split(
        r"[;?]\s*|\s+(?:и|а также|and)\s+(?=(?:как|почему|зачем|что|когда|какие|сколько|how|why|what|when)\s)",
        question, flags=re.I,
    )
    return [part.strip() for part in parts if part.strip()][:4] or [question]
