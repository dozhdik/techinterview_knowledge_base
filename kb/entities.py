"""Link mentions to current cards using authoritative names and bounded variants."""
from collections import defaultdict
from dataclasses import dataclass, replace
from functools import lru_cache
import re

from .content import has_material
from .search import requested_card_ids
from .titles import (WORD, _DEFINITION, name_keys as _keys, name_stem as _stem,
                     name_word as _word, normalize_title, title_index)

MODES = ("off", "link", "retrieve", "evidence")
_INTERRUPTION = re.compile(r"[;!?\n]")
_CONTEXT = re.compile(r"\b(?:с помощью|при помощи|посредством|при использовании|using|with the help of)\b")
_REFERENT = re.compile(r"\b(?:у него|у нее|у них|его|ее|их|самого|при этом|он[аи]?|это|does it|it use|its)\b")
_KIND_ORDER = ("title", "alias", "abbreviation", "definition_name", "inferred_abbreviation")


@dataclass(frozen=True)
class Mention:
    text: str
    canonical_name: str
    start: int | None
    end: int | None
    card_ids: tuple[str, ...]
    selected: str | None
    match_type: str
    ambiguous: bool
    domain: str | None
    role: str = "additional"
    inherited: bool = False
    confirmed: bool = False


class EntityIndex:
    def __init__(self, names):
        self.confirmed = names.confirmed
        self.confirmed_inflections = names.inflections
        self.records = {card: (title, domain) for card, domain, title, *_ in names.records}
        self.entries = defaultdict(lambda: defaultdict(set))
        for kind, entries in names.names.items():
            for name, ids in entries.items():
                self.entries[_keys(name)][kind].update(ids)
        for card, _, title, content, *_ in names.records:
            intro = _DEFINITION.search(content)
            # Leading names in a titled definition and labels before colons are
            # useful beyond whole-title search. Conjunction components need prose support.
            definition = _keys(intro[2]) if intro else ()
            primary = re.split(r":|\s+(?:для|в|на)\s+", title, maxsplit=1, flags=re.I)[0]
            parts = re.split(r"\s+и\s+", primary, maxsplit=1, flags=re.I)
            for part in parts:
                key = _keys(part)
                if not key or not any(len(token) >= 3 for token in key):
                    continue
                if definition and any(definition[i:i+len(key)] == key for i in range(len(definition))):
                    self.entries[key]["definition_name"].add(card)
            # An inflected implementation phrase can still name a documented
            # structure when its title explicitly names the structure.
            if len(parts) == 2 and intro and _keys(parts[0]) == definition[:len(_keys(parts[0]))]:
                for part in parts:
                    if key := _keys(part):
                        self.entries[key]["definition_name"].add(card)
        from .evidence import acronyms

        for short, expansions in acronyms({key: title for key, (title, _) in self.records.items()}).items():
            owners = set().union(*expansions.values())
            if len(expansions) > 1 and len(owners) > 1:
                self.entries[(short,)]["inferred_abbreviation"].update(owners)
        self.inflections = defaultdict(set)
        for key in self.entries:
            if any(re.fullmatch(r"[а-я]{4,}", token) for token in key):
                self.inflections[tuple(map(_stem, key))].add(key)
        self.width = max(map(len, self.entries), default=0)
        self.initials = {key[0] for key in self.entries if key} | {key[0] for key in self.inflections if key}

    def _matches(self, tokens, observed):
        key = tuple(tokens)
        if key in self.entries:
            entries = self.entries[key]
            strong = set().union(*(entries[k] for k in _KIND_ORDER[:3] if k in entries))
            candidates = strong or set().union(*(v for k, v in entries.items() if k != "inferred_abbreviation"))
            if observed.isupper() and "inferred_abbreviation" in entries:
                candidates.update(entries["inferred_abbreviation"])
            if candidates:
                return next(k for k in _KIND_ORDER if entries.get(k)), candidates
        variants = self.inflections.get(tuple(map(_stem, key)), ())
        if variants:
            authoritative = set().union(*(cards for variant in variants
                                           for kind, cards in self.entries[variant].items()
                                           if kind in _KIND_ORDER[:3]))
            ids = authoritative or set().union(*(cards for variant in variants
                                                 for kind, cards in self.entries[variant].items()
                                                 if kind != "inferred_abbreviation"))
            if ids:
                return "inflected", ids
        return None

    def _mention(self, text, start, end, kind, ids, cards, context):
        usable = sorted(key for key in ids if key in cards and getattr(cards[key], "status", None) != "draft"
                        and getattr(cards[key], "content", "") and has_material(cards[key]))
        if not usable and kind != "id":
            return None
        selected = usable[0] if len(usable) == 1 else None
        if len(usable) > 1 and kind != "id":
            scores = sorted(((len(context & set(map(_stem, _keys(self.records[key][0])))), key)
                             for key in usable), reverse=True)
            if scores[0][0] >= 2 and scores[0][0] > scores[1][0]:
                selected = scores[0][1]
        keys = _keys(text)
        declared = (self.confirmed_inflections.get(tuple(map(_stem, keys)), ())
                    if kind == "inflected" else self.confirmed.get(keys, ()))
        confirmed = kind == "id" or bool(usable and set(usable) <= set(declared))
        canonical, domain = self.records[selected] if selected else (normalize_title(text), None)
        return Mention(text, canonical, start, end, tuple(usable or sorted(ids)), selected,
                       kind, len(usable) > 1 and selected is None, domain, confirmed=confirmed)

    def link(self, text, units, domain=None):
        cards = {unit.id: unit for unit in units if not domain or getattr(unit, "domain", None) == domain}
        words = list(WORD.finditer(text))
        keys = [_word(word[0]) for word in words]
        context = set(map(_stem, keys))
        mentions = []
        for key in requested_card_ids(text):
            for match in re.finditer(r"(?<![\w-])" + re.escape(key) + r"(?![\w-]|\.[0-9])", text, re.I):
                mentions.append(self._mention(match[0], *match.span(), "id", {key}, cards, context))
        occupied = [(m.start, m.end) for m in mentions]
        i = 0
        while i < len(words):
            if keys[i] not in self.initials and _stem(keys[i]) not in self.initials:
                i += 1
                continue
            end_limit = min(i + self.width, len(words))
            matches = []
            for j in range(end_limit, i, -1):
                start, end = words[i].start(), words[j-1].end()
                if any(start < b and end > a for a, b in occupied) or _INTERRUPTION.search(text, start, end):
                    continue
                raw = text[start:end]
                found = self._matches(keys[i:j], raw)
                if not found:
                    continue
                item = self._mention(raw, start, end, *found, cards, context - set(map(_stem, keys[i:j])))
                if item:
                    matches.append((item, j))
                    if item.selected:
                        break
            if matches:
                item, j = next(((m, j) for m, j in matches if m.selected), matches[0])
                mentions.append(item)
                i = j
            else:
                i += 1
        return tuple(sorted(mentions, key=lambda m: m.start))


@lru_cache(maxsize=4)
def entity_index(names):
    return EntityIndex(names)


def link_entities(text, units, domain=None):
    return entity_index(title_index(units)).link(text, units, domain)


def roles(mentions, text, intents):
    boundary = _CONTEXT.search(text)
    comparison = "comparison" in intents
    return tuple(replace(mention, role=(
        "ambiguous" if mention.ambiguous else
        "context" if boundary and mention.start is not None and mention.start >= boundary.end() else
        "comparison" if comparison else
        "primary" if len(mentions) == 1 or (boundary and i == 0) else "additional"
    )) for i, mention in enumerate(mentions))


def inherit(text, previous):
    if not previous or not _REFERENT.search(_word(text)):
        return ()
    return tuple(replace(m, text="", start=None, end=None, inherited=True)
                 for m in previous if m.selected and m.role != "context")
