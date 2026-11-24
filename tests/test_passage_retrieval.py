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


def test_answer_checks_a_lower_ranked_card_without_accepting_a_distractor(monkeypatch):
    engine = _engine()
    units = [SimpleNamespace(id=p.card_id, title=p.title) for p in engine.passages]
    zero = np.zeros(2)
    def rank(query, *args):
        return ["A", "B"], {"A": (.54, 0), "B": (.51, 1)}, zero, np.array([.54, .51]), {"seconds": {}}
    monkeypatch.setattr(engine, "rank", rank)

    answer, debug = engine.ask("Что такое очередь?", units)
    assert [unit.id for unit in answer.units] == ["B"]
    assert debug["parts"][0]["checked_candidates"][0]["reason"] == "sufficient_section"


def test_selected_passage_covers_second_facet_without_a_false_warning(monkeypatch):
    engine = _engine()
    units = [SimpleNamespace(id=p.card_id, title=p.title) for p in engine.passages]
    monkeypatch.setattr(engine, "dense", lambda q: (
        np.array([.9, .1]) if q.normalized == "кэш" else np.zeros(2), 0))

    answer, debug = engine.ask("Кэш; что хранит результат?", units)
    assert answer.units == [units[0]]
    assert debug["unanswered"] == []
    assert debug["parts"][1]["reason"] == "covered_in_selected_sections"
    assert answer.answer.count("Кэш хранит результат.") == 1


def test_dependent_clause_keeps_context_and_missing_referent_asks_to_clarify(monkeypatch):
    assert len(facets("Почему этот подход сложен и как это влияет на вставку?")) == 1
    engine = _engine()
    monkeypatch.setattr(engine, "dense", lambda q: (np.array([.2, .8]), 0))
    units = [SimpleNamespace(id=p.card_id, title=p.title) for p in engine.passages]

    answer, debug = engine.ask("Как подготовиться к этому этапу?", units)
    assert not answer.units
    assert "Уточните" in answer.answer
    assert debug["parts"][0]["reason"] == "unspecified_referent"


def test_specific_missing_detail_does_not_use_a_similar_card(monkeypatch):
    engine = _engine()
    monkeypatch.setattr(engine, "dense", lambda q: (np.array([.93, .2]), 0))
    units = [SimpleNamespace(id=p.card_id, title=p.title) for p in engine.passages]

    answer, debug = engine.ask("Какой точный параметр CacheFlag надо задать для кеша?", units)
    assert answer is None
    assert {c["reason"] for c in debug["parts"][0]["checked_candidates"]} == {
        "unsupported_specific_detail"
    }


def test_one_facet_can_select_a_complementary_block_from_another_card():
    from dataclasses import replace

    from kb.evidence import Candidate, SectionEvidence, choose_sections

    engine = _engine()
    engine.passages[1] = replace(engine.passages[1], domain=engine.passages[0].domain)
    first = SectionEvidence(0, "Кэш ускоряет чтение.", frozenset({"кэш", "чтени"}), frozenset({"чтени"}), .9)
    second = SectionEvidence(1, "Очередь разносит запись.", frozenset({"очередь", "запис"}), frozenset({"запис"}), .8)
    repeated = SectionEvidence(1, first.text, first.terms, first.matched, .86)
    scorer = SimpleNamespace(engine=engine, cover=lambda hits: len(hits) / 2)
    options = (Candidate("A", .96, True, "", (first,)),
               Candidate("B", .91, True, "", (repeated, second)))

    assert choose_sections(options, scorer) == [first, second]



def test_definition_prefers_exact_title_to_a_related_card_with_same_tag(monkeypatch):
    from dataclasses import replace

    engine = _engine()
    passages = [engine.passages[0], replace(engine.passages[1], tags=["кэш"])]
    engine = Retrieval(engine.metadata, passages,
                       [np.array([[1, 0]], dtype=np.float32), np.array([[0, 1]], dtype=np.float32)])
    monkeypatch.setattr(engine, "dense", lambda q: (np.array([.64, .84]), 0))
    units = [SimpleNamespace(id=p.card_id, title=p.title) for p in passages]

    answer, _ = engine.ask("Что такое кэш?", units)
    assert answer.units == [units[0]]


def test_benchmark_accepts_section_labels_without_literal_fact_proxies():
    from kb.search_benchmark import _metrics

    case = {"relevant": [{"id": "A", "grade": 2, "sections": ["Определение"]}]}
    result = _metrics(case, ["A"], "## Определение\n\nФрагмент", ["A"])

    assert result["precision@1"] == 1
    assert result["section_proxy"] == 1
    assert "fact_proxy" not in result
