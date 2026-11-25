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


def test_distinct_blocks_from_one_long_section_survive_composition(monkeypatch):
    text_a = "Альфа задаёт правило группировки. " + " ".join(f"элемент{i}" for i in range(190))
    text_b = "Бета задаёт способ сортировки. " + " ".join(f"операция{i}" for i in range(190))
    passages = [
        Passage("A", "Справочник", "cs", "concept", [], ("Подробности",), 0, 1, text_a, [], []),
        Passage("A", "Справочник", "cs", "concept", [], ("Подробности",), 2500, 1, text_b, [], []),
    ]
    diagonal = np.eye(2, dtype=np.float32)
    engine = Retrieval({"model": "test"}, passages, [diagonal[:1], diagonal[1:]])
    monkeypatch.setattr(engine, "dense", lambda q: (
        np.array([.91, .05]) if q.normalized == "альфа" else np.array([.05, .91]), 0))
    units = [SimpleNamespace(id="A", title="Справочник")]

    answer, debug = engine.ask("Альфа; Бета", units)
    assert text_a in answer.answer and text_b in answer.answer
    assert answer.answer.count("## Подробности") == 1
    assert [b["position"] for b in debug["selected"]] == [0, 2500]
    assert debug["unanswered"] == []


def test_facets_are_not_silently_dropped(monkeypatch):
    engine = _engine()
    monkeypatch.setattr(engine, "dense", lambda q: (np.array([.91, .05]), 0))
    units = [SimpleNamespace(id="A", title="Кэш"), SimpleNamespace(id="B", title="Очередь")]
    words = ["Кэш", "Очередь", "Кэш", "Кэш", "Кэш", "Кэш", "Кэш", "Кэш", "Девятая", "Десятая"]

    answer, debug = engine.ask("; ".join(words), units)
    assert len(facets("; ".join(words))) == 10
    assert len(debug["parts"]) == 8
    assert debug["deferred"] == ["Девятая", "Десятая"]
    assert all(word in answer.answer for word in words[-2:])


def test_dependent_complexity_facet_keeps_the_subject():
    from kb.query import with_facet_context

    subject = Query.parse("Что такое очередь?")
    complexity = with_facet_context(Query.parse("Какая сложность?"), subject)
    assert "очеред" in complexity.normalized
    assert "quantity" in complexity.intents
    explicit = Query.parse("Какая сложность BFS?")
    assert with_facet_context(explicit, subject) is explicit


def test_an_indexed_abbreviation_uses_context_and_keeps_ambiguity():
    from kb.evidence import resolve_acronyms

    passages = [
        Passage("L", "Load Balancer", "arch", "concept", [], ("Описание",), 0, 0,
                "Входящий трафик и серверы", [], []),
        Passage("B", "Local Buffer", "cs", "concept", [], ("Описание",), 0, 0,
                "LB хранит байты в памяти", [], []),
    ]
    diagonal = np.eye(2, dtype=np.float32)
    engine = Retrieval({"model": "test"}, passages, [diagonal[:1], diagonal[1:]])
    expanded = resolve_acronyms(Query.parse("LB для входящего трафика и серверов"), engine.acronyms, engine)

    assert {"load", "balancer"} <= set(expanded.tokens)
    bare = Query.parse("LB")
    assert resolve_acronyms(bare, engine.acronyms, engine) is bare


def test_reader_checks_source_offsets_and_cannot_override_missing_specific_detail():
    from kb.evidence import Candidate, SectionEvidence
    from kb.qa_reader import Span, apply_reader

    a = SectionEvidence(0, "Фрагмент объясняет тему.", frozenset(), frozenset({"тем"}), .7)
    b = SectionEvidence(1, "Конкретный исходный ответ.", frozenset(), frozenset({"тем"}), .7)
    candidates = [Candidate("A", 1.1, False, "unsupported_specific_detail", (a,)),
                  Candidate("B", .8, False, "insufficient_section_evidence", (b,))]
    calls = []
    def score(question, contexts):
        calls.append(contexts)
        return [Span(0, 9, 5.0)]
    reader = SimpleNamespace(score=score)
    scorer = SimpleNamespace(query=Query.parse("Тема"), cover=lambda words: .5,
                             priority=lambda c: (c.admitted, c.score))

    result, debug = apply_reader(reader, "all", scorer, candidates)
    assert calls == [[b.text]]
    assert result[0].card == "B" and result[0].admitted
    assert not result[1].admitted
    assert debug[1]["span"] == [0, 9]


def test_related_cards_use_original_evidence_and_exclude_answer_sources():
    engine = _engine()
    engine.idf.update({"очередь": 2., "планы": 2.})
    debug = {"sources": ["A"], "unanswered": ["про очередь"], "parts": [{
        "query": "про очередь", "terms": ("очередь", "планы"), "reason": "insufficient_evidence",
        "evidence": [("A", (.9, .9)), ("B", (.54, .38))],
    }]}
    assert list(engine.related_cards(debug)) == ["B"]
    debug["parts"][0]["terms"] = ("планы",)
    assert list(engine.related_cards(debug)) == []
    debug["parts"][0]["reason"] = "unspecified_referent"
    debug["parts"][0]["terms"] = ("очередь",)
    assert list(engine.related_cards(debug)) == []
