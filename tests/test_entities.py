import json
from pathlib import Path

import pytest

from kb.entities import inherit, link_entities, roles
from kb.extractive import direct_search
from kb.parser import KnowledgeUnit, parse_directory
from kb.passage_index import DOMAINS
from kb.properties import supported
from kb.query import information_needs
from kb.search import card_open_ids

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def cards():
    return [unit for domain in DOMAINS for unit in parse_directory(ROOT / domain)]


@pytest.mark.parametrize(("text", "needle", "card"), [
    ("Зачем Breadth-First Search хранит очередь?", "Breadth-First Search", "CS-CONCEPT-016"),
    ("Как устроен бинарный поиск в отсортированном массиве при равенстве?", "бинарный поиск в отсортированном массиве", "CS-CONCEPT-018"),
    ("Какие расходы связаны со стеком?", "стеком", "CS-CONCEPT-012"),
    ("What are the trade-offs of using a Load Balancer?", "Load Balancer", "ARCH-COMPONENT-001"),
    ("В чём польза CDN для клиента?", "CDN", "ARCH-COMPONENT-005"),
    ("Как считается результат после Team Match?", "Team Match", "PROC-STAGE-006"),
    ("Когда имеет смысл использовать поведенческое интервью?", "поведенческое интервью", "PROC-STAGE-005"),
    ("Почему элемент myBFSName работает?", "", None),
    ("Как вести переговоры в контексте eu-south-2?", "", None),
    ("Как быстро отсеивать отсутствующие значения?", "", None),
])
def test_recognition_in_natural_queries(cards, text, needle, card):
    found = link_entities(text,cards)
    if needle:
        mention = next(m for m in found if m.text == needle)
        assert text[mention.start:mention.end] == needle
        assert mention.selected == card
    else:
        assert not found


def test_supported_comparison_and_independent_context(cards):
    q = "Чем BFS отличается от DFS?"
    mentions = roles(link_entities(q,cards),q,information_needs(q))
    assert [m.role for m in mentions] == ["comparison"] * 2
    inherited = inherit("Сколько памяти у него?", mentions)
    assert all(m.inherited and m.start is None for m in inherited)
    assert not inherit("Как подготовиться к интервью?", mentions)
    q = "Как разгрузить API Gateway с помощью Load Balancer?"
    assert [m.role for m in roles(link_entities(q,cards),q,information_needs(q))] == ["primary", "context"]


def sample(card, title, **kwargs):
    return KnowledgeUnit(card, title, "cs", "concept", "junior",
                         status="review", content=f"# {title}\n\nЭто содержание.", **kwargs)


def test_punctuation_boundaries_and_ambiguous_authoritative_forms():
    units = [sample("CS-CONCEPT-301","C++",abbreviations=["ZZ"]),
             sample("CS-CONCEPT-302","C#",abbreviations=["ZZ"]),
             sample("CS-CONCEPT-303",".NET"), sample("CS-CONCEPT-304","C",tags=["noise"])]
    q = "Как отличаются Ｃ＋＋, C#, C и .NET? Какая роль ZZ и noise?"
    mentions = link_entities(q,units)
    assert [(m.text,m.selected) for m in mentions[:4]] == [
        ("Ｃ＋＋","CS-CONCEPT-301"),("C#","CS-CONCEPT-302"),("C","CS-CONCEPT-304"),(".NET","CS-CONCEPT-303")]
    assert mentions[-1].ambiguous and mentions[-1].selected is None
    assert mentions[-1].card_ids == ("CS-CONCEPT-301","CS-CONCEPT-302")
    assert not link_entities("Чем особенен C++17?", units)


def test_inferred_abbreviation_is_ambiguous_without_support(cards):
    result = link_entities("Как настраивают SD?",cards)
    assert len(result) == 1 and result[0].ambiguous
    assert not link_entities("Как настраивают sd?",cards)
    direct = link_entities("Какая сложность алгоритма CS-CONCEPT-016?",cards)
    assert len(direct)==1 and direct[0].match_type == "id" and direct[0].selected == "CS-CONCEPT-016"
    unknown = link_entities("Какая сложность CS-CONCEPT-9999?",cards)
    assert unknown[0].selected is None and unknown[0].card_ids == ("CS-CONCEPT-9999",)


def test_lookup_and_content_id_are_distinct(cards):
    ids = ["CS-CONCEPT-016","CS-CONCEPT-017","CS-CONCEPT-018","CS-CONCEPT-019"]
    assert card_open_ids("Открой карточки " + " и ".join(ids)) == ids
    result, info = direct_search(", ".join(ids),cards)
    assert info["state"] == "partial" and len(result.units)==3 and ids[3] in result.answer
    assert info["deferred"] == ids[3:]
    assert direct_search("Какая сложность алгоритма " + ids[0],cards) is None
    assert direct_search("Сравни " + " и ".join(ids[:2]),cards) is None


def test_intents_and_distinct_source_properties():
    needs = information_needs("Какая временная и пространственная сложность?")
    assert set(needs) >= {"time_complexity","space_complexity"}
    assert {"implementation","pitfalls"} <= set(information_needs("Как реализовать поиск и какие ошибки возникают?"))
    assert supported("Отправлено 95% задач.") == frozenset()
    assert "space_complexity" not in information_needs("Как потоки процесса разделяют память?")
    assert "time_complexity" not in information_needs("Как устроен breaker, когда сервис временно недоступен?")
    assert "space_complexity" not in supported("Время работы — O(n).")
    assert "time_complexity" not in supported("Вспомогательная память — O(n).")
    assert {"time_complexity","space_complexity"} <= supported("Время O(n); дополнительная память O(1).")


def test_frozen_gold_has_consistent_spans_and_real_ids(cards):
    rows = json.loads((ROOT/"evaluation/entity_holdout.json").read_text())
    ids = {u.id for u in cards}
    assert 60 <= len(rows) <= 80
    for case in rows:
        for mark in case["mentions"]:
            assert case["query"][mark["start"]:mark["end"]] == mark["text"]
            assert set(mark["card_ids"]) <= ids



def test_numeric_property_must_be_about_the_linked_subject():
    from types import SimpleNamespace

    from kb.evidence import EvidenceScorer

    scorer = EvidenceScorer.__new__(EvidenceScorer)
    scorer.engine = SimpleNamespace(title_terms={"A": {"algorithm"}})
    scorer.owners = {"A"}
    scorer.context = {}
    scorer.entity_scope = {}
    scorer.needs = {"space_complexity"}
    source = "Дополнительная память — O(n)."
    assert not scorer._properties("B", source, "Оценка", {"sort"})
    assert scorer._properties("B", source, "Оценка", {"algorithm"}) == {"space_complexity"}
