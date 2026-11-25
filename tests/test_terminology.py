from pathlib import Path

import pytest

from kb.conversation import Conversation, ConversationTurn
from kb.entities import link_entities
from kb.extractive import direct_search
from kb.parser import KnowledgeUnit, ParseError, parse_directory, parse_file
from kb.query import Query, canonical_tokens, unlinked_topic
from kb.validator import validate_all

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def corpus():
    return [unit for domain in ("cs", "arch", "process") for unit in parse_directory(ROOT / domain)]


@pytest.mark.parametrize(("query", "card"), [
    ("быстрая сортировка", "CS-CONCEPT-010"),
    ("алгоритм быстрой сортировки", "CS-CONCEPT-010"),
    ("структура данных хеш-таблица", "CS-CONCEPT-009"),
    ("Метод двоичного поиска", "CS-CONCEPT-018"),
    ("Паттерн транзакционного outbox", "ARCH-DESIGNPAT-006"),
])
def test_whole_topic_normalizes_outer_label_and_case(corpus, query, card):
    answer, debug = direct_search(query, corpus)
    assert debug["state"] == "complete" and [unit.id for unit in answer.units] == [card]


def test_property_and_comparison_keep_their_request(corpus):
    question = "Какая сложность быстрой сортировки?"
    assert direct_search(question, corpus) is None
    mentions = link_entities(question, corpus)
    assert len(mentions) == 1 and mentions[0].selected == "CS-CONCEPT-010" and mentions[0].confirmed
    assert {"сложность", "quick", "sort"} <= set(canonical_tokens(question, mentions))
    q = "Чем быстрая сортировка отличается от сортировки слиянием?"
    assert direct_search(q, corpus) is None
    assert {m.selected for m in link_entities(q, corpus) if m.confirmed} == {"CS-CONCEPT-010", "CS-CONCEPT-019"}
    assert direct_search("алгоритм быстрой сортировки; сложность?", corpus) is None


def test_direct_topic_can_switch_chats_without_using_earlier_source(corpus):
    conversation = Conversation(corpus)
    prior = conversation.restore([ConversationTurn(question="Что такое BFS?", source_ids=["CS-CONCEPT-005"])])
    choice = conversation.resolve("алгоритм быстрой сортировки", prior)
    assert choice.kind == "topic_switch" and choice.explicit == ("CS-CONCEPT-010",)
    continuation = conversation.resolve("Какая у неё сложность?", choice.updated)
    assert continuation.required_cards == ("CS-CONCEPT-010",)


def make_unit(card, title, **fields):
    return KnowledgeUnit(card, title, "cs", "concept", "middle", status="review",
                         content=f"# {title}\n\n## Определение\n\nОпределение содержит исходный материал.",
                         **fields)


def test_collisions_warn_and_exact_title_has_priority():
    one = make_unit("CS-CONCEPT-991", "Первая тема", aliases=["Вторая тема", "Общий термин", "", "метод"],
                    abbreviations=["XY"])
    two = make_unit("CS-CONCEPT-992", "Вторая тема", aliases=["Общий термин"], abbreviations=["XY", "xy"])
    result = validate_all([one, two])
    assert any(issue.field == "aliases" for issue in result.errors)
    for expected in ("названием", "Неоднозначное", "повторяет", "слишком общим"):
        assert any(expected in issue.message for issue in result.warnings)
    for question in ("Общий термин", "XY"):
        answer, debug = direct_search(question, [one, two])
        assert debug["state"] == "clarification" and not answer.units
    assert direct_search("Вторая тема", [one, two])[1]["sources"] == [two.id]


def test_parser_rejects_invalid_yaml_type(tmp_path):
    path = tmp_path / "card.md"
    path.write_text("---\nid: CS-CONCEPT-991\ntitle: Первая тема\ndomain: cs\ncategory: concept\n"
                    "difficulty: middle\naliases: одно имя\n---\n# Первая тема\n", encoding="utf-8")
    with pytest.raises(ParseError, match="aliases"):
        parse_file(path)


def test_unlinked_topic_gate_ignores_descriptive_questions():
    assert unlinked_topic(Query.parse("Как работает пирамидальная сортировка?")) == "пирамидальная сортировка?"
    assert not unlinked_topic(Query.parse("Что хранит результат?"))
    assert not unlinked_topic(Query.parse("Как работает поиск в распределённой системе?"))
