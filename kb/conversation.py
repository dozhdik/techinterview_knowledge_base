"""Resolve a bounded, client-supplied sequence of questions against current cards."""
import re
from dataclasses import dataclass
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from .content import has_material
from .entities import Mention, entity_index, roles
from .query import information_needs, normalize
from .search import card_open_ids
from .titles import title_index

HISTORY_LIMIT = 6
TOPIC_LIMIT = 4
Health = Literal["complete", "partial", "related_only", "absent", "clarification"]
CardId = Annotated[str, Field(min_length=1, max_length=48)]
_MENTION = re.compile(r"\b(?:он(?:а|о|и)?|его|ее|их|ему|ей|им|нему|ней|нем|них|нее|него|"
                      r"ним|ними|это|эт(?:от|а|о|и|ом|ой|ого|ому)|обоих|оба|обе|it|its|them|they|both)\b")
_PLURAL = re.compile(r"\b(?:они|их|них|ними|обоих|оба|обе|them|they|both)\b")
_PREVIOUS = re.compile(r"\b(?:предыдущ\w*|прежн\w* тем\w*|previous)\b")
_SWITCH = re.compile(r"^(?:теперь|сменим тему|поговорим о|перейдем к|new topic)\b")
_RETURN = re.compile(r"^\s*(?:а\s+)?(?:вернемся|вернись|возвращаясь|back to)\s+к?\s*", re.I)
_ELABORATE = re.compile(r"^(?:а\s+)?(?:поподробнее|подробнее|продолж(?:и|ай)|можно подробнее|explain more)$")
_SHORT = re.compile(
    r"^(?:а\s+)?(?:как(?:\s+(?:это\s+)?(?:работает|устроен[ао]?|реализовать|применить|решить|использовать))"
    r"|(?:покажи|покажите|приведи|приведите|дай|дайте)\s+(?:на\s+)?пример(?:е)?(?:\s+(?:кода|реализации))?"
    r"|(?:каков[аы]?|какая|какие|какое|какой|в чем|что насчет)\s+(?:(?:временн\w*|пространственн\w*)\s+)?"
    r"(?:сложность|ограничения|недостатки|преимущества|ошибки|разница|принцип работы)"
    r"|сколько\s+(?:нужно\s+)?(?:дополнительной\s+)?(?:памяти|времени)(?:\s+(?:требуется|нужно))?"
    r"|когда\s+(?:лучше\s+)?(?:применять|использовать)|почему|зачем)$"
)
_SETTING = re.compile(r"\b(?:в|на|между|для)(?:\s+[\w-]+)?$")
_DEICTIC = re.compile(r"\b(?:в этом (?:случае|подходе)|при этом)\b")


class ConversationTurn(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    source_ids: list[CardId] = Field(default_factory=list, max_length=8)
    state: Health | None = None


@dataclass(frozen=True)
class DialogueState:
    active: tuple[str, ...] = ()
    explicit: tuple[str, ...] = ()
    ambiguous: tuple[str, ...] = ()
    recent: tuple[tuple[str, ...], ...] = ()
    intents: tuple[str, ...] = ()
    source_ids: tuple[str, ...] = ()
    inferred: tuple[str, ...] = ()
    domains: tuple[str, ...] = ()
    search_state: Health | None = None


@dataclass(frozen=True)
class Resolution:
    kind: str
    reason: str
    question: str
    search_query: str
    mentions: tuple[Mention, ...]
    explicit: tuple[str, ...]
    inherited: tuple[str, ...]
    candidates: tuple[str, ...]
    intents: tuple[str, ...]
    prior: DialogueState
    updated: DialogueState
    clarification: str = ""

    @property
    def required_cards(self):
        return self.updated.active if self.inherited and not self.clarification else ()


def _unique(ids):
    return tuple(dict.fromkeys(ids))[:TOPIC_LIMIT]


class Conversation:
    def __init__(self, units):
        self.units = units
        self.cards = {u.id: u for u in units}
        self.names = title_index(units)
        self.linker = entity_index(self.names)

    def _ready(self, ids):
        return _unique(cid for key in ids if (cid := key.upper()) in self.cards
                       and getattr(self.cards[cid], "status", None) != "draft"
                       and has_material(self.cards[cid]))

    def remember(self, resolution, source_ids=(), search_state=None):
        updated = resolution.updated
        sources = self._ready(source_ids)
        return DialogueState(
            active=updated.active, explicit=updated.explicit, ambiguous=updated.ambiguous,
            recent=updated.recent, intents=updated.intents, source_ids=sources,
            inferred=tuple(cid for cid in sources if cid not in updated.active),
            domains=updated.domains, search_state=search_state,
        )

    def restore(self, history):
        state = DialogueState()
        for turn in history[-HISTORY_LIMIT:]:
            choice = self.resolve(turn.question, state)
            state = self.remember(choice, turn.source_ids, turn.state)
        return state

    def resolve(self, question, prior):
        normalized = normalize(question).strip(" .?!")
        intents = information_needs(question)
        mentions = roles(self.linker.link(question, self.units), normalized, intents)
        exact = card_open_ids(question)
        match = self.names.topic(question) if not exact else None
        if exact or match:
            choices = self._ready(exact or match.ids)
            ambiguous = choices if match and len(choices) > 1 else ()
            explicit = () if ambiguous else choices
            intents = ("direct_lookup",)
        else:
            subjects = tuple(m for m in mentions if m.selected and m.role != "context")
            if any(m.confirmed and m.match_type != "inflected" for m in subjects):
                # An inflected common noun inside the setting need not be a topic of its own.
                subjects = tuple(m for m in subjects if m.match_type != "inflected" or
                                 m.role != "additional" or not _SETTING.search(normalize(question[:m.start])))
            explicit = _unique(m.selected for m in subjects)
            ambiguous = _unique(cid for m in mentions if m.ambiguous and m.role != "context" for cid in m.card_ids)

        referent = bool(_MENTION.search(normalized) or _DEICTIC.search(normalized))
        return_to_previous = bool(_RETURN.match(normalized) and _PREVIOUS.search(normalized))
        previous = next((group for group in reversed(prior.recent)
                         if set(group) != set(prior.active)), ())
        short = bool(_SHORT.fullmatch(normalized))
        elaborate = bool(_ELABORATE.fullmatch(normalized))
        compare = "comparison" in intents
        plural = bool(_PLURAL.search(normalized))
        # A possessive in an independent request may describe the user's own data.
        dependent = not (exact or match) and (referent or short or elaborate or return_to_previous)
        kind = "standalone"
        reason = "independent_question"
        inherited = ()
        active = explicit
        search_query = question
        clarification = ""
        candidates = ambiguous

        if return_to_previous and not explicit:
            inherited = previous if len(previous) == 1 else ()
            kind, reason = "return", "previous_distinct_topic"
        elif compare and _PREVIOUS.search(normalized) and not explicit:
            inherited = _unique((*prior.active, *previous)) if len(prior.active) == len(previous) == 1 else ()
            kind, reason = "comparison", "current_and_previous_topic"
        elif compare and referent and explicit and not ambiguous:
            old = tuple(cid for cid in prior.active if cid not in explicit)
            inherited = old if len(old) == 1 and len(prior.active) == 1 else ()
            kind, reason = "comparison", "current_with_named_entity"
        elif dependent and not explicit and not ambiguous:
            inherited = prior.active if not prior.ambiguous and (
                len(prior.active) == 1 and not plural or len(prior.active) > 1 and plural) else ()
            kind, reason = ("continuation", "continue_previous_explanation") if elaborate else (
                "followup", "plural_reference" if plural else "single_reference")
        elif prior.active and (explicit and set(explicit) != set(prior.active) or
                               _SWITCH.search(normalized)):
            kind, reason = "topic_switch", "new_explicit_entity" if explicit else "explicit_switch_without_link"

        needs_clarification = (kind in {"followup", "continuation", "comparison", "return"} and not inherited)
        if needs_clarification or (ambiguous and not explicit and (dependent or match is not None)):
            candidates = ambiguous or prior.ambiguous or prior.active
            if not candidates:
                clarification = "Уточните, о какой технологии или карточке идёт речь."
            else:
                names = "; ".join(f"{self.cards[cid].title} ({cid})" for cid in candidates)
                clarification = f"Уточните, какую из тем вы имеете в виду: {names}."
            kind, reason = "clarification", "ambiguous_reference" if candidates else "missing_topic"
            active = prior.active
            ambiguous = prior.ambiguous or ambiguous
        elif inherited:
            active = _unique((*inherited, *explicit))
            topic = " и ".join(self.cards[cid].title for cid in inherited)
            original = question.rstrip(" .?!")
            if kind == "return":
                _, delimiter, tail = question.partition(".")
                original = tail.strip().rstrip(" ?!.") if delimiter and tail.strip() else "Что такое"
            elif elaborate:
                original = ("Какова сложность" if set(prior.intents) & {"time_complexity", "space_complexity"}
                            else "Как работает")
            if plural and len(active) > 1 and not compare:
                original = "Сравни: " + original
            search_query = f"{original} — {topic}"
        elif not explicit and not ambiguous and prior.active:
            reason = "independent_question_clears_topic"

        recent = prior.recent
        if active and (not recent or set(recent[-1]) != set(active)):
            recent = (*recent, active)[-HISTORY_LIMIT:]
        updated = DialogueState(
            active=active, explicit=explicit, ambiguous=ambiguous, recent=recent,
            intents=intents, domains=_unique(self.cards[cid].domain for cid in (*active, *ambiguous)),
        )
        return Resolution(kind, reason, question, search_query, mentions, explicit, inherited,
                          candidates, intents, prior, updated, clarification)
