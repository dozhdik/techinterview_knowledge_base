import asyncio
import io
import json

import pytest

from kb import rag
from kb.vector_store import VectorHit


@pytest.fixture
def inline_thread(monkeypatch):
    async def run_inline(function, *args, **kwargs):
        return function(*args, **kwargs)

    monkeypatch.setattr(rag.asyncio, "to_thread", run_inline)


def test_completion_request_uses_context_and_model(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["payload"] = json.loads(request.data)
        captured["authorization"] = request.get_header("Authorization")
        captured["timeout"] = timeout
        return io.BytesIO(json.dumps({"choices": [{"message": {"content": "Ответ [[CS-CONCEPT-009]]"}}]}).encode())

    monkeypatch.setattr(rag, "urlopen", fake_urlopen)
    config = rag.RagConfig(base_url="http://localhost:11434/v1", model="local-model",
                           api_key="test-token", timeout_seconds=12)
    answer = rag._request_completion(config, "Что такое хеш-таблица?", "Контекст карточки")
    assert answer == "Ответ [[CS-CONCEPT-009]]"
    assert captured["url"] == "http://localhost:11434/v1/chat/completions"
    assert captured["payload"]["model"] == "local-model"
    assert "Контекст карточки" in captured["payload"]["messages"][1]["content"]
    assert captured["authorization"] == "Bearer test-token"
    assert captured["timeout"] == 12


def test_generated_answer_rejects_unknown_citation(monkeypatch, inline_thread):
    hit = VectorHit(chunk_id="CS-CONCEPT-009:000", card_id="CS-CONCEPT-009",
                    title="Хеш-таблица", domain="cs", category="concept",
                    status="review", source_path="cs/hash.md", text="Хеш-таблица хранит ключи.",
                    score=0.8, related=[], sources=[])
    monkeypatch.setattr(rag, "_request_completion",
                        lambda config, question, context: "Неверная ссылка [[CS-CONCEPT-999]]")
    config = rag.RagConfig(base_url="http://localhost:11434/v1", model="test")
    with pytest.raises(rag.RagError, match="ссылок"):
        asyncio.run(rag.generate("Что такое хеш-таблица?", [hit], config))


@pytest.mark.parametrize("answer", [
    "Ответ [[CS-CONCEPT-009]] и [[CS-CONCEPT-999]]",
    "Ответ [[CS-CONCEPT-009]] и [[несуществующая карточка]]",
    "Ответ [[CS-CONCEPT-009]] и [[CS-CONCEPT-999",
    "Ответ без ссылки",
    "[[CS-CONCEPT-009]]",
])
def test_rejects_any_invalid_reference(monkeypatch, inline_thread, answer):
    hit = VectorHit(chunk_id="CS-CONCEPT-009:000", card_id="CS-CONCEPT-009",
                    title="Хеш-таблица", domain="cs", category="concept",
                    status="review", source_path="cs/hash.md", text="Текст",
                    score=0.8, related=[], sources=[])
    monkeypatch.setattr(rag, "_request_completion", lambda *args: answer)
    with pytest.raises(rag.RagError, match="ссылок"):
        asyncio.run(rag.generate("Вопрос", [hit], rag.RagConfig("http://localhost/v1", "test")))


def test_missing_index_is_not_created_implicitly(tmp_path, monkeypatch, inline_thread):
    monkeypatch.setattr(rag, "build_index", lambda *args, **kwargs: pytest.fail("implicit build"))
    with pytest.raises(rag.RagError, match="индекс недоступен"):
        asyncio.run(rag.retrieve(tmp_path, "вопрос", [], rag.RagConfig("http://localhost/v1", "test")))
    assert not (tmp_path / "_data" / "vector_index.sqlite3").exists()


def test_single_bracket_reference_is_normalized_and_checked(monkeypatch, inline_thread):
    hit = VectorHit(chunk_id="CS-CONCEPT-009:000", card_id="CS-CONCEPT-009",
                    title="Хеш-таблица", domain="cs", category="concept",
                    status="review", source_path="cs/hash.md", text="Текст",
                    score=0.8, related=[], sources=[])
    config = rag.RagConfig("http://localhost/v1", "test")
    monkeypatch.setattr(rag, "_request_completion", lambda *args: "Пояснение [CS-CONCEPT-009]")
    result = asyncio.run(rag.generate("Вопрос", [hit], config))
    assert result.answer == "Пояснение"
    monkeypatch.setattr(rag, "_request_completion", lambda *args: "Пояснение [CS-CONCEPT-999]")
    with pytest.raises(rag.RagError, match="ссылок"):
        asyncio.run(rag.generate("Вопрос", [hit], config))


def test_truncated_completion_is_rejected(monkeypatch):
    response = {"choices": [{"finish_reason": "length", "message": {"content": "Ответ [[CS-CONCEPT-009]]"}}]}
    monkeypatch.setattr(rag, "urlopen", lambda *args, **kwargs: io.BytesIO(json.dumps(response).encode()))
    with pytest.raises(rag.RagError, match="обрезан"):
        rag._request_completion(rag.RagConfig("http://localhost/v1", "test"), "Вопрос", "Контекст")
