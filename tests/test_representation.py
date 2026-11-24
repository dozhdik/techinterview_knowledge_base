from types import SimpleNamespace

import pytest

from kb.passage_index import Passage
from kb.query import Query
from kb.representation import DEFAULT_MODEL, build, project
from kb.retrieval import Retrieval

np = pytest.importorskip("numpy")


def test_projection_records_provenance_for_title_sections_and_links():
    content = (
        "# Карточка\n\n## Назначение\n\n"
        "Очередь (Queue) сглаживает пики поступления событий перед записью.\n\n"
        "## Когда применять\n\n"
        "Полезно, когда обработчики не успевают принимать все события.\n\n"
        "## Связанные материалы\n\n"
        "[[ARCH-COMPONENT-005]]"
    )
    unit = SimpleNamespace(title="Очередь (Queue)", category="component", tags=["сообщения"],
                           roles=["backend"], interview_stage=["system-design"], content=content,
                           related=["ARCH-COMPONENT-005"], prerequisites=[])
    descriptors, questions, links = project(unit)
    assert ("Queue", "yaml.title") in {(d.text, d.origin) for d in descriptors}
    assert ("сообщения", "yaml.tags") in {(d.text, d.origin) for d in descriptors}
    assert any(d.kind == "use_cases" for d in descriptors)
    assert links == {"related": ["ARCH-COMPONENT-005"], "prerequisites": []}
    purpose = next(q for q in questions if q.template == "purpose")
    assert purpose.heading == ("Назначение",)
    assert content[purpose.position:].startswith("Очередь (Queue)")
    assert "сглаживает пики" in purpose.text
    assert "ARCH-COMPONENT-005" not in " ".join(q.text for q in questions)


def test_experimental_index_cannot_overwrite_working_index(tmp_path):
    path = tmp_path / "_data" / "passage_index.sqlite3"
    path.parent.mkdir()
    path.write_bytes(b"working index")
    alias = tmp_path / "alias.sqlite3"
    alias.symlink_to(path)
    with pytest.raises(ValueError, match="отдельный индекс"):
        build(tmp_path, alias)
    assert path.read_bytes() == b"working index"


def engine_with_queue(heading, source):
    passage = Passage("A", "Очередь", "cs", "concept", [], (heading,), 0, 1, source, [], [])
    engine = Retrieval({"model": DEFAULT_MODEL}, [passage], [np.array([[1, 0]], dtype="float32")])
    return engine, [SimpleNamespace(id="A", title=passage.title)]


def test_new_search_channels_share_the_original_query_vector(monkeypatch):
    engine, _ = engine_with_queue("Определение", "Очередь хранит сообщения до получения.")
    embedded = []
    query_vector = [1, 0]

    def embed(query):
        embedded.append(query.normalized)
        return query_vector, 0

    def question_scores(vector, allowed, limit):
        assert vector is query_vector
        assert allowed == {"A"}
        return [("A", .97, {"text": "поисковая подсказка", "origin": "yaml.title"})]

    monkeypatch.setattr(engine, "_query_vector", embed)
    repr_index = SimpleNamespace(
        metadata={"model": DEFAULT_MODEL},
        dense=question_scores,
        lexical=lambda *args: [("A", 10., None)],
    )
    ranked, evidence, _, _, diagnostics = engine.rank(
        Query.parse("Очередь"), "hybrid", representations=repr_index, representation_mode="combined",
    )
    assert ranked == ["A"]
    assert embedded == ["очередь"]
    assert set(diagnostics["representations"]) == {"metadata", "questions"}
    assert evidence["A"] == (1., 1.)


def test_search_only_text_cannot_supply_an_answer(monkeypatch):
    engine, units = engine_with_queue("Определение", "Очередь хранит сообщения до получения.")
    monkeypatch.setattr(engine, "_query_vector", lambda q: ([.1, 0], 0))
    repr_index = SimpleNamespace(
        metadata={"model": DEFAULT_MODEL},
        dense=lambda *args: [("A", .99, {"text": "Как измерить расстояние до Луны?"})],
        lexical=lambda *args: [("A", 25., None)],
    )
    answer, diagnostics = engine.ask("Как измерить расстояние до Луны?", units, representations=repr_index,
                                     representation_mode="combined")
    assert diagnostics["ranked_cards"] == ["A"]
    assert diagnostics["state"] == "absent"
    assert not diagnostics["selected"]
    assert answer is None


def test_problem_statement_is_not_an_answer_to_how_to_solve_it(monkeypatch):
    engine, units = engine_with_queue("Условие", "Требуется настроить ограничение размера очереди.")
    monkeypatch.setattr(engine, "dense", lambda q: (np.array([.99]), 0))
    answer, diagnostics = engine.ask("Как настроить ограничение размера очереди?", units)
    assert answer is None
    assert diagnostics["state"] == "related_only"
    assert diagnostics["parts"][0]["reason"] == "overview_without_answer"


def test_fourth_holdout_mentions_only_real_source_sections():
    from pathlib import Path
    import json

    from kb.extractive import _sections
    from main import _load_units

    root = Path(__file__).resolve().parents[1]
    cases = json.loads((root / "evaluation/search_holdout_iteration4.json").read_text())
    units = {unit.id: unit for unit in _load_units()}
    assert len({case["query"] for case in cases}) == len(cases)
    for case in cases:
        assert bool(case["relevant"]) == (case["status"] in ("full", "partial"))
        for reference in case["relevant"]:
            headings = set(dict(_sections(units[reference["id"]].content)))
            assert set(reference["sections"]) <= headings
