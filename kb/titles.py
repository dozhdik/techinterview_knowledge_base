"""Conservative exact name lookup over the current Markdown corpus."""
import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache


# Preserve technical punctuation within names such as C++, C#, .NET and Node.js.
_SEPARATORS = re.compile(r"""[«»„“”"'‘’()\[\]{},:/\-‐‑‒–—―]+""")
_PARENTHETICAL = re.compile(r"^([^()]+?)[ \t]+\(([^()]+)\)")
_COMPARISON = re.compile(r"\b(?:vs|versus|между|отлич\w*|сравнен\w*)\b", re.I)
_DEFINITION = re.compile(
    r"^##[ \t]+(определение|назначение|суть концепции|что такое [^\n]+)[ \t]*\n\s*([^#\n][^\n]*)",
    re.I | re.M,
)
_ABBREVIATION = re.compile(r"(?=[A-Z0-9/-]{2,12}$)[A-Z][A-Z0-9]*(?:[/-][A-Z0-9]+)*")
_HEADING = re.compile(r"\A#\s+([^\n]+)")
_INTRO_ABBREVIATION = re.compile(r"^([A-Z][A-Z0-9/-]*)[ :]+(?=[А-Яа-яЁё(—–])")


def normalize_title(value):
    normalized = unicodedata.normalize("NFKC", value).casefold().replace("ё", "е")
    return " ".join(_SEPARATORS.sub(" ", normalized).split()).rstrip(".!? ")


def _is_abbreviation(value):
    return bool(_ABBREVIATION.fullmatch(value) and sum(char.isupper() for char in value) >= 2)


def _name(value):
    name = value.strip()
    return ("abbreviation" if _is_abbreviation(name) else "alias"), name


def _names(title, content):
    """Read names presented as headings or as explicit definitions."""
    if heading := _HEADING.match(content):
        yield _name(heading[1])

    # A comparison can have a full title without giving either topic a new name.
    if _COMPARISON.search(title):
        return
    group = _PARENTHETICAL.fullmatch(title)
    if group:
        yield _name(group[1])
        for name in group[2].split(","):
            yield _name(name)

    definition = _DEFINITION.search(content)
    if not definition:
        return
    heading, intro = definition.groups()
    intro = intro.replace("**", "").replace("`", "")
    title_key = normalize_title(title)
    if acronym := _INTRO_ABBREVIATION.match(intro):
        short = acronym[1]
        title_tokens = title_key.split()
        if (_is_abbreviation(short) and short.casefold() in title_tokens
                and (normalize_title(heading) == f"что такое {short.casefold()}"
                     or (title_tokens[0] == short.casefold()
                         and not any(_is_abbreviation(token) and token != short for token in title.split())))):
            yield "abbreviation", short

    pair = _PARENTHETICAL.match(intro)
    if not pair:
        return
    base, alternatives = pair[1].strip(), [name.strip() for name in pair[2].split(",")]
    # Match the subject from the title so that incidental mentions remain searchable
    # only through ordinary retrieval.
    subject = normalize_title(group[1]) if group else title_key
    names = {normalize_title(base), *(normalize_title(base + " " + name) for name in alternatives)}
    if subject in names:
        yield _name(base)
        for name in alternatives:
            yield _name(name)


@dataclass(frozen=True)
class TitleMatch:
    kind: str
    ids: tuple[str, ...]


class TitleIndex:
    def __init__(self, records):
        self.names = {kind: defaultdict(set) for kind in ("title", "alias", "abbreviation")}
        self.domains = {}
        for card, domain, title, content, aliases, abbreviations in records:
            self.domains[card] = domain
            full = normalize_title(title)
            if full:
                self.names["title"][full].add(card)
            for kind, name in (*_names(title, content), *(("alias", name) for name in aliases),
                               *(("abbreviation", name) for name in abbreviations)):
                key = normalize_title(name)
                if key != full and any(ch.isalpha() for ch in key):
                    self.names[kind][key].add(card)

    def match(self, value, domain=None):
        key = normalize_title(value)

        def candidates(kind):
            return {card for card in self.names[kind].get(key, ()) if not domain or self.domains[card] == domain}

        if full := candidates("title"):
            return TitleMatch("title", tuple(sorted(full)))
        aliases, abbreviations = candidates("alias"), candidates("abbreviation")
        if both := aliases | abbreviations:
            return TitleMatch("alias" if aliases else "abbreviation", tuple(sorted(both)))
        return None


@lru_cache(maxsize=4)
def _title_index(records):
    return TitleIndex(records)


def title_index(units):
    return _title_index(tuple((u.id, getattr(u, "domain", ""), u.title, getattr(u, "content", ""),
                               tuple(getattr(u, "aliases", ())), tuple(getattr(u, "abbreviations", ())))
                              for u in units))
