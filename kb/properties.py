"""Signals from the source block for the information explicitly requested."""
import re

NUMBER = re.compile(r"\b[OoОо]\s*\([^)]{1,32}\)|\d+\s*(?:байт\w*|bytes?|KiB|MiB|ГиБ|мс|сек\w*|ms)\b", re.I)
TIME = re.compile(r"\b(?:врем\w*|time|операци\w+ в худш\w*|шаг\w*|(?:средн\w*|худш\w*|лучш\w*|амортизир\w*) сложност\w*)\b", re.I)
SPACE = re.compile(r"\b(?:памят\w*|memory|space|пространственн\w+)\b", re.I)
PROSE = {
    "procedure": r"\b(?:сначала|затем|шаг\w*|после этого|repeat|then)\b",
    "implementation": r"\x60{3}|\b(?:псевдокод|реализац\w*|инициализ\w*|храните|обновля\w*|initialize)\b",
    "advantages": r"\b(?:преимуществ\w*|выигрыш\w*|плюс\w*|снижает|уменьшает)\b",
    "disadvantages": r"\b(?:недостат\w*|минус\w*|издерж\w*|дороже|нагрузка)\b",
    "limitations": r"\b(?:границ\w*|ограничен\w*|нельзя|не гарантиру\w*|не подход\w*|только при)\b",
    "use_cases": r"\b(?:примен\w*|подходит|использу\w*|полез\w*|сценар\w*)\b",
    "pitfalls": r"\b(?:ошиб\w*|избегайте|нельзя|проверяйте|опас\w*)\b",
    "example": r"\b(?:пример\w*|например|пусть|допустим)\b",
}


def supported(text, heading=""):
    found = {name for name, pattern in PROSE.items() if re.search(pattern, text, re.I)}
    for clause in re.split(r"[\n;]|(?<=[.)])\s+(?=[А-ЯЁA-Z])", text):
        for value in NUMBER.finditer(clause):
            vicinity = clause[max(0, value.start()-85):value.end()+25]
            time = list(TIME.finditer(vicinity))
            space = list(SPACE.finditer(vicinity))
            if time or space:
                marker = value.start() - max(0, value.start()-85)
                closest = lambda matches: min((abs(m.start()-marker) for m in matches), default=999)
                found.add("time_complexity" if closest(time) < closest(space) else "space_complexity")
            elif SPACE.search(heading) and not TIME.search(heading):
                found.add("space_complexity")
            elif TIME.search(heading) and not SPACE.search(heading):
                found.add("time_complexity")
    return frozenset(found)


QUANTITATIVE = frozenset(("time_complexity", "space_complexity"))
LABELS = {"time_complexity": "временная сложность", "space_complexity": "пространственная сложность"}
