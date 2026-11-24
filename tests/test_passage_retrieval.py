from types import SimpleNamespace

import pytest

np = pytest.importorskip("numpy")

from kb.passage_index import Passage, close_code_fence, markdown_blocks
from kb.query import Query, facets
from kb.retrieval import Retrieval


def test_markdown_blocks_keep_nested_headings_and_complete_fences():
    source = "# Карточка\n\n## Пример\n\n### Код\n\n~~~python\n## comment\nprint(1)\n~~~\n\n| A |\n| --- |\n| 1 |"
    blocks = list(markdown_blocks(source))
    assert len(blocks) == 2
    heading, pos, section, code = blocks[0]
    assert heading == ("Пример", "Код")
    assert source[pos:pos + len(code)] == code
    assert code.endswith("~~~")
    assert blocks[1][2] == section
    assert blocks[1][3].endswith("| 1 |")


def test_close_code_fence_when_rendering_excerpts():
    source = "Вводный абзац\n\n````text\n```\nпример"
    assert close_code_fence(source) == source + "\n````"
    complete = source + "\n`````"
    assert close_code_fence(complete) == complete


def test_unicode_and_compound_split():
    assert Query.parse("  ＢＦＳ  ").tokens == ("bfs",)
    assert facets("Чем BFS отличается от DFS?") == ["Чем BFS отличается от DFS"]
    assert len(facets("Как получить адрес; как повторить запрос?")) == 2


def _engine():
    passages = [
        Passage("A", "Кэш", "cs", "concept", [], ("Пример",), 0, 1, "Кэш хранит результат.", [], []),
        Passage("B", "Очередь", "arch", "component", [], ("Определение",), 0, 1, "Очередь хранит сообщения.", [], []),
    ]
    return Retrieval({"model": "test"}, passages,
                     [np.array([[1.0, 0.0]], dtype=np.float32), np.array([[0.0, 1.0]], dtype=np.float32)])


def test_dense_candidates_have_no_lexical_gate(monkeypatch):
    engine = _engine()
    monkeypatch.setattr(engine, "dense", lambda query: (np.array([.2, .9]), 0))
    units = [SimpleNamespace(id=p.card_id, title=p.title) for p in engine.passages]
    answer, debug = engine.ask("Доставка", units)
    assert debug["parts"][0]["bm25"] == []
    assert debug["parts"][0]["dense"][0][0] == "B"
    assert answer.units == [units[1]]


def test_compound_answer_merges_matched_sources_and_marks_missing(monkeypatch):
    engine = _engine()
    monkeypatch.setattr(engine, "dense", lambda query: (
        np.array([.9, .1]) if "кэш" in query.normalized else
        np.array([.1, .9]) if "очеред" in query.normalized else np.array([.1, .1]), 0))
    units = [SimpleNamespace(id=p.card_id, title=p.title) for p in engine.passages]
    answer, info = engine.ask("Кэш; очередь; неизвестное", units)
    assert [u.id for u in answer.units] == ["A", "B"]
    assert info["unanswered"] == ["неизвестное"]
    assert "частичный ответ" in answer.answer
    only_cs, _ = engine.ask("Очередь", units, domain="cs")
    assert only_cs is None


def test_benchmark_judgments_reference_real_sections_and_disjoint_cards():
    import json
    from pathlib import Path

    from kb.extractive import _sections
    from main import _load_units

    root = Path(__file__).resolve().parents[1]
    cases = json.loads((root / "evaluation/search_cases.json").read_text())
    units = {u.id: u for u in _load_units()}
    by_split = {"development": set(), "test": set()}
    assert len({case["query"] for case in cases}) >= 150
    for case in cases:
        assert case["sufficient"] == bool(case["relevant"])
        for label in case["relevant"]:
            by_split[case["split"]].add(label["id"])
            sections = dict(_sections(units[label["id"]].content))
            for heading in label["sections"]:
                assert heading in sections
                assert all(f.casefold() in sections[heading].casefold() for f in label["facts"])
    assert not by_split["development"].intersection(by_split["test"])
