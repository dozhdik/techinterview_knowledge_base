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
