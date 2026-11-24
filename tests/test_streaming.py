import asyncio
import json

import pytest

from kb.citation_stream import CitationFilter
from kb.rag import RagConfig, RagError, prepare_context, validate_answer
from kb.vector_store import VectorHit
from web import server


def hit(card_id="CS-CONCEPT-009", text="Хеш-таблица хранит ключи."):
    return VectorHit(chunk_id=card_id + ":000", card_id=card_id, title="Хеш-таблица", domain="cs",
                     category="concept", status="review", source_path="cs/hash.md", text=text,
                     score=0.8, related=[], sources=[])


def test_split_citations_never_appear_in_stream():
    f = CitationFilter()
    output = "".join(f.feed(part) for part in ["Ответ [", "[CS-CON", "CEPT-009]", "] далее ", "[CS-", "CONCEPT-009", "]!"])
    output += f.feed("", final=True)
    assert output == "Ответ  далее !"
    assert CitationFilter().feed("Текст [[CS-CON", final=True) == "Текст "


def test_validate_before_removing_and_deduplicate():
    answer = validate_answer("Ответ [[CS-CONCEPT-009]], пример [CS-CONCEPT-009].", [hit()])
    assert answer.answer == "Ответ, пример."
    assert validate_answer("Текст. ID: [[CS-CONCEPT-009]]", [hit()]).answer == "Текст."
    assert [h.card_id for h in answer.hits] == ["CS-CONCEPT-009"]
    with pytest.raises(RagError):
        validate_answer("Текст [[CS-CONCEPT-009]] [[CS-CONCEPT-999]]", [hit()])


def test_context_respects_conservative_budget():
    config = RagConfig("http://local/v1", "model", num_ctx=4096, num_predict=512)
    context, included = prepare_context("Вопрос", [hit(text="данные " * 3000)], config)
    from kb.rag import SYSTEM_PROMPT
    assert included and context
    assert len((SYSTEM_PROMPT + "Вопрос" + context).encode()) + config.num_predict + 128 <= config.num_ctx


def run_stream(monkeypatch, pieces, reason="stop"):
    monkeypatch.setenv("RAG_ENABLED", "true")
    monkeypatch.setenv("RAG_BASE_URL", "http://local/v1")
    monkeypatch.setenv("RAG_MODEL", "test")
    monkeypatch.setattr(server, "load_units", lambda: [])
    async def retrieve(*args):
        return [hit()]
    async def stream(*args):
        for part in pieces:
            yield {"message": {"content": part}, "done": False}
        yield {"done": True, "done_reason": reason}
    async def inline(function, *args, **kwargs):
        return function(*args, **kwargs)
    monkeypatch.setattr(server, "retrieve", retrieve)
    monkeypatch.setattr(server, "stream_chat", stream)
    monkeypatch.setattr(server.asyncio, "to_thread", inline)
    async def run():
        response = await server.ask_stream(server.AskRequest(question="Что такое хеш-таблица?"))
        return [json.loads(line) async for line in response.body_iterator]
    return asyncio.run(run())


def test_stream_stages_validate_then_emit_sources(monkeypatch):
    events = run_stream(monkeypatch, ["Хеш хранит ключи ", "[[CS-CON", "CEPT-009]]", "."])
    assert [e["stage"] for e in events if e["type"] == "stage"] == ["search", "context", "generation", "verify"]
    assert "[[" not in "".join(e["text"] for e in events if e["type"] == "delta")
    final = events[-1]
    assert final["type"] == "final" and final["is_rag_enabled"]
    assert final["answer"] == "Хеш хранит ключи."
    assert [s["id"] for s in final["sources"]] == ["CS-CONCEPT-009"]


def test_invalid_and_truncated_stream_are_not_success(monkeypatch):
    events = run_stream(monkeypatch, ["Текст [[CS-CONCEPT-999]]"])
    assert events[-1]["type"] == "error"
    events = run_stream(monkeypatch, ["Текст [[CS-CONCEPT-009]]"], "length")
    assert events[-1]["type"] == "truncated" and not events[-1]["is_rag_enabled"]


def test_upstream_connection_closes_on_cancellation():
    from kb.ollama_stream import stream_chat

    async def scenario():
        disconnected = asyncio.Event()
        async def serve(reader, writer):
            await reader.readuntil(b"\r\n\r\n")
            # Request payload is small; drain it before waiting for connection close.
            await reader.read(4096)
            packet = json.dumps({"message": {"content": "Начало"}, "done": False}).encode() + b"\n"
            writer.write(b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n" +
                         f"{len(packet):x}\r\n".encode() + packet + b"\r\n")
            await writer.drain()
            if await reader.read() == b"":
                disconnected.set()
            writer.close()
        listener = await asyncio.start_server(serve, "127.0.0.1", 0)
        port = listener.sockets[0].getsockname()[1]
        generator = stream_chat(RagConfig(f"http://127.0.0.1:{port}/v1", "test"), "q", "context")
        try:
            assert (await anext(generator))["message"]["content"] == "Начало"
            await generator.aclose()
            await asyncio.wait_for(disconnected.wait(), 3)
        finally:
            listener.close()
            await listener.wait_closed()
    asyncio.run(scenario())


def test_cached_embedder_reuses_instance(monkeypatch):
    from kb import vector_store
    vector_store._cached_embedder.cache_clear()
    calls = []
    monkeypatch.setattr(vector_store, "SentenceTransformerEmbedder", lambda model: calls.append(model) or object())
    first = vector_store._embedder("sentence-transformers", "model")
    second = vector_store._embedder("sentence-transformers", "model")
    assert first is second and calls == ["model"]
    vector_store._cached_embedder.cache_clear()


def test_truncated_without_citation_reports_length(monkeypatch):
    events = run_stream(monkeypatch, ["Незавершённый ответ"], "length")
    assert events[-1]["type"] == "truncated"
    assert not events[-1]["sources"] and not events[-1]["is_rag_enabled"]


def test_card_cache_invalidates_on_change(tmp_path, monkeypatch):
    from kb import vector_store
    folder = tmp_path / "cs"
    folder.mkdir()
    path = folder / "card.md"
    path.write_text("one", encoding="utf-8")
    before = vector_store.source_fingerprint(tmp_path)
    path.write_text("two changed", encoding="utf-8")
    assert vector_store.source_fingerprint(tmp_path) != before
    path.unlink()
    assert vector_store.source_fingerprint(tmp_path) != before


def test_unsupported_decimal_is_rejected_even_with_valid_source():
    with pytest.raises(RagError, match="числовые"):
        validate_answer("Порог 0.7 [[CS-CONCEPT-009]]", [hit()], "В контексте порог не указан.")
    result = validate_answer("Порог 0,7 [[CS-CONCEPT-009]]", [hit()], "Порог 0.7.")
    assert result.answer == "Порог 0,7"


def test_truncated_refusal_marker_is_not_reported_as_complete(monkeypatch):
    events = run_stream(monkeypatch, ["НЕДОСТАТОЧНО_ДАННЫХ"], "length")
    assert events[-1]["type"] == "truncated"


def test_nonstream_native_uses_same_validation(monkeypatch):
    from kb import ollama_stream, rag
    async def stream(*args):
        yield {"message": {"content": "Хеш хранит ключи [[CS-CONCEPT-009]]"}, "done": False}
        yield {"done": True, "done_reason": "stop"}
    monkeypatch.setattr(ollama_stream, "stream_chat", stream)
    config = RagConfig("http://local/v1", "test", native_api=True)
    result = asyncio.run(rag.generate("Что такое хеш?", [hit()], config))
    assert result.answer == "Хеш хранит ключи" and result.hits[0].card_id == "CS-CONCEPT-009"
