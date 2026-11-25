import asyncio
import re
from dataclasses import replace
from pathlib import Path

import pytest

from kb.extractive import direct_search
from kb.parser import KnowledgeUnit, parse_directory, parse_file
from kb.passage_index import DOMAINS
from kb.retrieval import Retrieval
from kb.search import SearchQuery, search
from kb.titles import normalize_title, title_index

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def corpus():
    return [card for domain in DOMAINS for card in parse_directory(ROOT / domain)
            if card.status != "draft"]


@pytest.mark.parametrize("form", ["title", "lower", "upper", "spaces", "punctuation", "id"])
def test_direct_requests_cover_all_available_cards(corpus, form):
    from kb.content import has_material

    engine = Retrieval.__new__(Retrieval)
    for card in filter(has_material, corpus):
        name = card.title
        question = {
            "title": name, "lower": name.lower(), "upper": name.upper(),
            "spaces": "\t  " + "   ".join(name.split()) + "  ",
            "punctuation": f'«{name}»!',
            "id": card.id,
        }[form]
        result, details = engine.ask(question, corpus)
        match = title_index(corpus).match(question) if form != "id" else None
        if match and len(match.ids) > 1:
            assert details["state"] == "clarification" and not result.units
            continue
        assert details["lookup"]["kind"] == ("id" if form == "id" else "title"), question
        assert details["ranked_cards"][0] == card.id, question
        assert result.units == [card], question
        original = re.sub(r"\[\[[A-Z]+-[A-Z]+-\d+\]\]", "", card.content)
        assert result.answer.endswith(original), question
        assert search(corpus, SearchQuery(text=question))[0].unit.id == card.id, question


def test_aliases_and_abbreviations_from_the_real_corpus(corpus):
    index = title_index(corpus)
    for kind in ("alias", "abbreviation"):
        for name, cards in index.names[kind].items():
            if name in index.names["title"] or len(cards) != 1:
                continue
            result, details = direct_search(name.lower(), corpus)
            assert details["lookup"]["kind"] == kind
            assert [card.id for card in result.units] == sorted(cards), name


def unit(id, title, *, domain="cs", **attributes):
    return KnowledgeUnit(id, title, domain, "concept", "junior", status="review",
                         content=f"# {title}\n\n## Определение\n\nМатериал карточки.", **attributes)


def test_exact_title_normalization_preserves_names_order_and_technical_symbols():
    first = unit("CS-CONCEPT-001", "Язык: C++")
    second = unit("CS-CONCEPT-002", "Язык C#")
    for name in ('«ЯЗЫК  :  Ｃ＋＋»?', "Язык — C++"):
        assert direct_search(name, [first, second])[0].units == [first]
    assert normalize_title(".NET") != normalize_title("NET")
    assert direct_search("C++ язык", [first, second]) is None
    assert direct_search("Язык C", [first, second]) is None


def test_collisions_take_domain_and_full_name_priority_into_account():
    units = [
        unit("CS-CONCEPT-001", "Обход", abbreviations=["ALG"]),
        unit("ARCH-COMPONENT-001", "Обход", domain="arch", aliases=["ALG"]),
        unit("CS-CONCEPT-003", "Поиск", aliases=["Обход"]),
    ]
    for query, ids in (("Обход", {"CS-CONCEPT-001", "ARCH-COMPONENT-001"}),
                       ("ALG", {"CS-CONCEPT-001", "ARCH-COMPONENT-001"})):
        result, details = direct_search(query, units)
        assert details["state"] == "clarification" and result.units == []
        assert set(details["lookup"]["candidates"]) == ids
    assert direct_search("Обход", units, domain="cs")[0].units == [units[0]]
    assert direct_search("ALG", units, domain="arch")[0].units == [units[1]]
    assert direct_search("ALG", units, domain="process") is None


def test_draft_tag_and_yaml_alternatives(tmp_path):
    path = tmp_path / "test.md"
    path.write_text("""---
id: CS-CONCEPT-007
title: Алгоритм разбиения
domain: cs
category: concept
difficulty: junior
status: review
tags: [граф]
aliases: [Partition algorithm]
abbreviations: [PA]
---
# Алгоритм разбиения

## Определение

Краткий материал.
""")
    card = parse_file(path)
    assert direct_search("Partition algorithm", [card])[0].units == [card]
    assert direct_search("pa", [card])[0].units == [card]
    assert direct_search("граф", [card]) is None
    assert direct_search("Алгоритм разбиения", [replace(card, status="draft")])[1]["lookup"]["status"] == "not_ready"
    assert direct_search("PA", [replace(card, content="<!-- TODO -->")])[1]["lookup"]["status"] == "not_ready"


@pytest.mark.parametrize("question", [
    "Что такое BFS?",
    "Какая сложность BFS?",
    "Чем BFS отличается от DFS?",
    "Поиск в ширину BFS; что такое очередь?",
    "Сравните поиск в ширину BFS и DFS",
    "O(1)",
    "1",
])
def test_full_title_is_not_matched_inside_other_queries(corpus, question):
    assert direct_search(question, corpus) is None


def test_cli_diagnose_direct_title_without_index(monkeypatch, capsys):
    import json

    from main import build_parser

    card = unit("CS-CONCEPT-001", "Неизвестный индекс")
    monkeypatch.setattr("main._load_units", lambda: [card])
    monkeypatch.setattr("kb.retrieval.get_engine", lambda *a: pytest.fail("Требуется только исходная карточка"))
    args = build_parser().parse_args(["search-diagnose", "«неизвестный индекс»", "--domain", "cs"])
    args.func(args)
    result = json.loads(capsys.readouterr().out)
    assert result["lookup"]["kind"] == "title" and result["ranked_cards"] == [card.id]


def test_api_and_stream_direct_title_before_generation_config(monkeypatch):
    import json

    from web import server

    card = unit("CS-CONCEPT-001", "N-дерево")
    monkeypatch.setenv("RAG_ENABLED", "true")
    monkeypatch.setattr(server, "load_units", lambda: [card])
    monkeypatch.setattr(server.RagConfig, "from_env", lambda: pytest.fail("Генерация не нужна"))

    async def run():
        request = server.AskRequest(question="  «n—дерево» !  ")
        actual = await server.ask(request)
        streamed = await server.ask_stream(request)
        events = [json.loads(line) async for line in streamed.body_iterator]
        assert events[-1] == {"type": "final", **actual.model_dump()}
        assert actual.sources[0].id == card.id and actual.answer.endswith(card.content)

    asyncio.run(run())


def test_comparison_card_matches_its_complete_title(corpus):
    question = "Чем BFS отличается от DFS и когда выбирать каждый из них?"
    result, details = direct_search(question, corpus)
    assert details["lookup"]["kind"] == "title"
    assert [unit.id for unit in result.units] == ["CS-QUESTION-003"]


def test_api_refreshes_title_index_after_edit(tmp_path, monkeypatch):
    from web import server

    folder = tmp_path / "cs"
    folder.mkdir()
    card = folder / "test.md"

    def write(name):
        card.write_text(f"---\nid: CS-CONCEPT-001\ntitle: {name}\ndomain: cs\ncategory: concept\n"
                        f"difficulty: junior\nstatus: review\n---\n# {name}\n\nТекст карточки.")

    monkeypatch.setenv("RAG_ENABLED", "false")
    monkeypatch.setattr(server, "KB_ROOT", tmp_path)
    monkeypatch.setattr(server, "structural_search", lambda *args: (None, "absent", []))

    async def check():
        write("Первый заголовок")
        opened = await server.ask(server.AskRequest(question="Первый заголовок"))
        assert [source.id for source in opened.sources] == ["CS-CONCEPT-001"]
        write("Заголовок после обновления")
        previous = await server.ask(server.AskRequest(question="Первый заголовок"))
        current = await server.ask(server.AskRequest(question="Заголовок после обновления"))
        assert previous.status == "not_found"
        assert current.sources[0].title == "Заголовок после обновления"

    asyncio.run(check())
