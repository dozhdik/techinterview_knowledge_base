import asyncio
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from kb.conversation import Conversation, ConversationTurn, DialogueState, HISTORY_LIMIT
from kb.extractive import ExtractiveResult
from main import _load_units
from web import server


@pytest.fixture(scope="module")
def dialogue():
    return Conversation(_load_units())


def restore(dialogue, *questions):
    return dialogue.restore([ConversationTurn(question=q) for q in questions])


def test_followups_and_explicit_switch(dialogue):
    first = restore(dialogue, "Что такое BFS?")
    for q in ("Как он работает?", "А какая сложность?", "Как его реализовать?", "Когда его нельзя применять?"):
        r = dialogue.resolve(q, first)
        assert r.required_cards == ("CS-CONCEPT-016",)
        assert r.question == q and "Поиск в ширину BFS" in r.search_query
    independent = dialogue.resolve("Как подготовиться к поведенческому собеседованию?", first)
    assert independent.search_query == independent.question and not independent.required_cards
    new = dialogue.resolve("Что такое хеш-таблица?", first)
    assert new.kind == "topic_switch"
    r = dialogue.resolve("А как в ней разрешаются коллизии?", new.updated)
    assert r.required_cards == ("CS-CONCEPT-009",)


def test_comparison_plural_singular_and_return(dialogue):
    start = restore(dialogue, "Что такое BFS?")
    comparison = dialogue.resolve("А чем он отличается от DFS?", start)
    assert comparison.kind == "comparison"
    assert set(comparison.required_cards) == {"CS-CONCEPT-016", "CS-CONCEPT-017"}
    both = dialogue.resolve("Какова сложность обоих?", comparison.updated)
    assert both.required_cards == comparison.required_cards
    unclear = dialogue.resolve("А когда его использовать?", comparison.updated)
    assert unclear.kind == "clarification" and unclear.required_cards == ()
    assert unclear.candidates == comparison.required_cards
    assert "CS-CONCEPT-016" in unclear.clarification and "CS-CONCEPT-017" in unclear.clarification
    resumed = dialogue.resolve("Вернёмся к предыдущей теме. Какая у неё сложность?",
                               restore(dialogue, "Что такое BFS?", "Что такое STAR?"))
    assert resumed.kind == "return" and resumed.required_cards == ("CS-CONCEPT-016",)


@pytest.mark.parametrize("state", ["complete", "partial", "absent"])
def test_source_does_not_own_topic_even_after_bad_result(dialogue, state):
    before = dialogue.restore([ConversationTurn(question="Что такое BFS?", state=state,
                                  source_ids=["ARCH-COMPONENT-001", "CS-CONCEPT-9999"])])
    assert before.inferred == ("ARCH-COMPONENT-001",) and before.source_ids == before.inferred
    assert before.search_state == state
    assert dialogue.resolve("А какая сложность?", before).required_cards == ("CS-CONCEPT-016",)
    unknown = dialogue.restore([ConversationTurn(question="Что такое неизвестный объект?",
                                   source_ids=["ARCH-COMPONENT-001"],state=state)])
    assert not unknown.active
    assert dialogue.resolve("А какие у него преимущества?", unknown).clarification


def test_old_title_cannot_override_current_corpus(dialogue):
    from dataclasses import replace

    original = next(u for u in dialogue.units if u.id == "CS-CONCEPT-016")
    changed = replace(original, title="Текущее описание", content="# Текущее описание\n\nОбновлённый материал.")
    new = Conversation([changed])
    past = new.restore([ConversationTurn(question=original.title,source_ids=[original.id])])
    assert past.inferred == (original.id,) and not past.active
    assert new.resolve("Какая у него сложность?", past).clarification


def test_api_validates_history_bounds_and_preserves_empty_payload():
    assert not server.AskRequest(question="Новый вопрос").context
    assert not server.AskRequest(question="Новый вопрос", context=[]).context
    with pytest.raises(ValidationError):
        server.AskRequest(question="Новый вопрос", context=[dict(question="Вопрос")]* (HISTORY_LIMIT + 1))
    with pytest.raises(ValidationError):
        ConversationTurn(question="Вопрос", source_ids=["X" * 49])
    with pytest.raises(ValidationError):
        ConversationTurn(question="X" * 1001)


def test_api_stream_and_followup_keep_shared_context_separate(monkeypatch, dialogue):
    monkeypatch.setenv("RAG_ENABLED","false")
    monkeypatch.setattr(server, "load_units", lambda: dialogue.units)
    requests=[]
    def backend(root, query, units, *, context_ids=()):
        requests.append((query, context_ids))
        picked= [u for u in units if u.id in context_ids]
        return ExtractiveResult("Фрагмент из источника", picked), "complete", []
    monkeypatch.setattr(server,"structural_search",backend)
    async def check():
        request = server.AskRequest(question="А какая сложность?", context=[dict(question="Что такое BFS?")])
        first = await server.ask(request)
        response = await server.ask_stream(request)
        final = [json.loads(line) async for line in response.body_iterator][-1]
        assert final == {"type":"final", **first.model_dump()}
        assert requests[0] == requests[1] and requests[0][1] == ("CS-CONCEPT-016",)
        assert request.question == "А какая сложность?"
        await server.ask(server.AskRequest(question=request.question))
        assert requests[-1] == (request.question, ())
        unclear = await server.ask(server.AskRequest(question="Когда его использовать?", context=[
            dict(question="Расскажи про BFS и DFS.")]))
        assert unclear.search_state=="clarification" and not unclear.sources
    asyncio.run(check())


def test_frozen_dialogues_cover_all_splits_and_use_current_ids(dialogue):
    data=json.loads((Path(__file__).resolve().parents[1]/"evaluation/dialogues.json").read_text())
    assert len(data)>=30 and {d["split"] for d in data}=={"dev","holdout"}
    assert {d["domain"] for d in data} >= {"cs","arch","process"}
    for d in data:
        assert 3<=len(d["turns"])<=7
        for turn in d["turns"]:
            assert set(turn["entities"]) <= dialogue.cards.keys()
            assert {s["id"] for s in turn["sources"]} <= dialogue.cards.keys()
