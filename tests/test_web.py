import asyncio
import json

import pytest
import yaml

from kb import rag
from web import server


def request(path, payload=None):
    messages = []
    body = json.dumps(payload).encode() if payload is not None else b""

    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(message):
        messages.append(message)

    scope = {"type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1",
             "method": "POST" if payload is not None else "GET", "scheme": "http",
             "path": path, "raw_path": path.encode(), "query_string": b"",
             "root_path": "", "headers": [(b"content-type", b"application/json")],
             "client": ("127.0.0.1", 1234), "server": ("test", 80)}
    asyncio.run(server.app(scope, receive, send))
    status = next(m["status"] for m in messages if m["type"] == "http.response.start")
    content = b"".join(m.get("body", b"") for m in messages if m["type"] == "http.response.body")
    return status, content


@pytest.fixture
def knowledge_base(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "KB_ROOT", tmp_path)

    def write_card(id, title, content, domain="cs"):
        path = tmp_path / domain / f"{id}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        metadata = {"id": id, "title": title, "domain": domain,
                    "category": "concept", "difficulty": "junior", "status": "review"}
        path.write_text("---\n" + yaml.safe_dump(metadata, allow_unicode=True)
                        + "---\n" + content, encoding="utf-8")
        return path

    return write_card


@pytest.fixture
def inline_rag_thread(monkeypatch):
    async def run_inline(function, *args, **kwargs):
        return function(*args, **kwargs)

    monkeypatch.setattr(rag.asyncio, "to_thread", run_inline)


@pytest.mark.parametrize("id,title,question,domain", [
    ("CS-CONCEPT-009", "Хеш-таблица", "Как устроена хеш-таблица?", "cs"),
    ("ARCH-SYSDESIGN-005", "URL Shortener", "Спроектируй URL Shortener", "arch"),
    ("PROC-FRAMEWORK-001", "Метод STAR", "Расскажи про метод STAR", "process"),
    ("GLB-GLOSSARY-001", "Latency", "Что такое latency?", "global"),
])
def test_answer_comes_from_card_and_source_opens(knowledge_base, id, title, question, domain):
    content = f"# {title}\n\nМатериал, существующий только в этой карточке."
    knowledge_base(id, title, content, domain)
    status, body = request("/api/ask", {"question": question})
    assert status == 200
    answer = json.loads(body)
    assert content in answer["answer"]
    assert answer["confidence"] is None
    assert answer["is_rag_enabled"] is False
    assert answer["sources"] == [{"id": id, "title": title, "url": f"/cards/{id}"}]
    assert request(answer["sources"][0]["url"])[0] == 200
    status, body = request(f"/api/units/{id}")
    assert status == 200
    data = json.loads(body)
    assert data["content"] == content
    assert "file_path" not in data


def test_changes_and_deletions_are_visible_without_restart(knowledge_base):
    path = knowledge_base("CS-CONCEPT-009", "Хеш-таблица", "Первый текст")
    assert "Первый текст" in json.loads(request("/api/ask", {"question": "хеш таблица"})[1])["answer"]
    knowledge_base("CS-CONCEPT-009", "Хеш-таблица", "Обновлённый текст")
    assert "Обновлённый текст" in json.loads(request("/api/ask", {"question": "хеш таблица"})[1])["answer"]
    path.unlink()
    assert json.loads(request("/api/ask", {"question": "хеш таблица"})[1])["sources"] == []
    assert request("/api/units/CS-CONCEPT-009")[0] == 404


def test_unknown_question_returns_no_sources(knowledge_base):
    knowledge_base("CS-CONCEPT-009", "Хеш-таблица", "Словарь с коллизиями.")
    status, body = request("/api/ask", {"question": "Квантовая запутанность"})
    assert status == 200
    data = json.loads(body)
    assert data["status"] == "not_found"
    assert data["sources"] == []
    assert "пока нет" in data["answer"]


@pytest.mark.parametrize("question", [
    "Дай определение Kubernetes", "Что такое квантовый компьютер?",
    "Что такое дерево Меркла?", "Что такое Bloom filter?",
])
def test_missing_definition_does_not_use_incidental_mentions(knowledge_base, question):
    knowledge_base("CS-CONCEPT-001", "Бинарное дерево", "Компьютер использует дерево Меркла.")
    knowledge_base("ARCH-COMPONENT-002", "Кеш", "Bloom filter и Kubernetes упоминаются здесь.", "arch")
    data = json.loads(request("/api/ask", {"question": question})[1])
    assert data["status"] == "not_found"
    assert data["sources"] == []


def test_unknown_id_is_named_and_mixed_ids_are_reported(knowledge_base):
    knowledge_base("CS-CONCEPT-009", "Хеш-таблица", "Текст готовой карточки.")
    missing = json.loads(request("/api/ask", {"question": "CS-CONCEPT-999"})[1])
    assert missing["status"] == "not_found"
    assert "CS-CONCEPT-999" in missing["answer"]
    assert missing["sources"] == []
    mixed = json.loads(request("/api/ask", {"question": "CS-CONCEPT-009 и CS-CONCEPT-999"})[1])
    assert mixed["status"] == "success"
    assert "CS-CONCEPT-999" in mixed["answer"]
    assert "Текст готовой карточки." in mixed["answer"]
    assert [source["id"] for source in mixed["sources"]] == ["CS-CONCEPT-009"]


@pytest.mark.parametrize("question", ["Что такое Quick Sort?", "CS-CONCEPT-010"])
def test_unfinished_card_is_reported_without_template(knowledge_base, question):
    template = "# Quick Sort\n\n## Определение\n<!-- TODO: заполнить -->\n\n- **Сложность**: O(?)"
    knowledge_base("CS-CONCEPT-010", "Quick Sort", template)
    data = json.loads(request("/api/ask", {"question": question})[1])
    assert data["status"] == "not_ready"
    assert data["sources"] == []
    assert "ещё не заполнен" in data["answer"] or "пока не заполнен" in data["answer"]
    assert "TODO" not in data["answer"]
    assert request("/api/units/CS-CONCEPT-010")[0] == 409
    status, body = request("/cards/CS-CONCEPT-010")
    assert status == 409
    assert "пока не заполнен" in body.decode()


def test_empty_database(knowledge_base):
    assert json.loads(request("/api/ask", {"question": "BFS"})[1])["sources"] == []


def test_empty_question(knowledge_base):
    status, body = request("/api/ask", {"question": "   "})
    assert status == 200
    assert json.loads(body)["status"] == "error"


@pytest.mark.parametrize("payload", [{}, {"question": None}, {"question": "x" * 1001}])
def test_invalid_request_is_rejected(payload):
    assert request("/api/ask", payload)[0] == 422


@pytest.mark.parametrize("path", ["/api/units/CS-CONCEPT-999", "/cards/CS-CONCEPT-999"])
def test_unknown_source_returns_404(knowledge_base, path):
    status, body = request(path)
    assert status == 404
    if path.startswith("/cards/"):
        assert "Карточка не найдена" in body.decode()


@pytest.mark.parametrize("path", ["/", "/js/app.js", "/js/chat.js", "/js/card.js", "/css/styles.css"])
def test_static_assets_are_available(path):
    status, body = request(path)
    assert status == 200
    assert body


def test_rag_answer_uses_index_and_cited_card(knowledge_base, monkeypatch, inline_rag_thread):
    path = knowledge_base("CS-CONCEPT-009", "Хеш-таблица",
                          "# Хеш-таблица\n\nХеш-таблица хранит пары ключ и значение.")
    monkeypatch.setenv("RAG_ENABLED", "true")
    monkeypatch.setenv("RAG_BASE_URL", "http://model.test/v1")
    monkeypatch.setenv("RAG_MODEL", "test-model")
    contexts = []

    def complete(config, question, context):
        contexts.append(context)
        return "Хеш-таблица хранит пары ключ и значение. [[CS-CONCEPT-009]]"

    monkeypatch.setattr(rag, "_request_completion", complete)
    rag.build_index(server.KB_ROOT, backend="hash")
    result = json.loads(request("/api/ask", {"question": "Что такое хеш-таблица?"})[1])
    assert result["status"] == "success"
    assert result["is_rag_enabled"] is True
    assert result["sources"] == [{"id": "CS-CONCEPT-009", "title": "Хеш-таблица",
                                   "url": "/cards/CS-CONCEPT-009"}]
    assert "Хеш-таблица хранит пары" in contexts[0]

    path.write_text(path.read_text(encoding="utf-8").replace("ключ и значение", "ключи и значения"),
                    encoding="utf-8")
    request("/api/ask", {"question": "Что такое хеш-таблица?"})
    assert "ключи и значения" in contexts[-1]


def test_rag_abstains_and_skips_unknown_topics(knowledge_base, monkeypatch, inline_rag_thread):
    knowledge_base("CS-CONCEPT-009", "Хеш-таблица", "Хеш-таблица хранит ключи.")
    monkeypatch.setenv("RAG_ENABLED", "true")
    monkeypatch.setenv("RAG_BASE_URL", "http://model.test/v1")
    monkeypatch.setenv("RAG_MODEL", "test-model")
    calls = []

    def complete(config, question, context):
        calls.append(question)
        return rag.INSUFFICIENT_CONTEXT

    monkeypatch.setattr(rag, "_request_completion", complete)
    rag.build_index(server.KB_ROOT, backend="hash")
    result = json.loads(request("/api/ask", {"question": "Что такое хеш-таблица?"})[1])
    assert result["status"] == "not_found"
    assert result["sources"] == []
    assert result["is_rag_enabled"] is False
    unknown = json.loads(request("/api/ask", {"question": "Квантовая запутанность"})[1])
    assert unknown["status"] == "not_found"
    assert len(calls) == 1


def test_rag_provider_failure_preserves_card_answer(knowledge_base, monkeypatch, inline_rag_thread):
    knowledge_base("CS-CONCEPT-009", "Хеш-таблица", "Материал про хеш-таблицу.")
    monkeypatch.setenv("RAG_ENABLED", "true")
    monkeypatch.setenv("RAG_BASE_URL", "http://model.test/v1")
    monkeypatch.setenv("RAG_MODEL", "test-model")

    def fail(config, question, context):
        raise rag.RagError("Сервис генерации недоступен")

    monkeypatch.setattr(rag, "_request_completion", fail)
    rag.build_index(server.KB_ROOT, backend="hash")
    result = json.loads(request("/api/ask", {"question": "Что такое хеш-таблица?"})[1])
    assert result["status"] == "success"
    assert result["is_rag_enabled"] is False
    assert "Материал про хеш-таблицу" in result["answer"]
    assert "Генерация сейчас недоступна" in result["answer"]


def test_explicit_id_keeps_exact_card_response_with_rag_configured(knowledge_base, monkeypatch):
    knowledge_base("CS-CONCEPT-009", "Хеш-таблица", "Точное содержимое карточки.")
    monkeypatch.setenv("RAG_ENABLED", "true")
    monkeypatch.setenv("RAG_BASE_URL", "http://model.test/v1")
    monkeypatch.setenv("RAG_MODEL", "test-model")

    def unexpected(config, question, context):
        raise AssertionError("Генератор не должен вызываться для точного ID")

    monkeypatch.setattr(rag, "_request_completion", unexpected)
    result = json.loads(request("/api/ask", {"question": "CS-CONCEPT-009"})[1])
    assert result["status"] == "success"
    assert result["is_rag_enabled"] is False
    assert "Точное содержимое карточки" in result["answer"]


def test_region_is_sent_to_search_and_exact_ids_still_route(knowledge_base, monkeypatch):
    from kb.extractive import ExtractiveResult

    knowledge_base("ARCH-COMPONENT-001", "Балансировщик", "# Балансировщик\n\n## Назначение\n\nРаздаёт трафик.", domain="arch")
    queries = []

    def lookup(root, question, units):
        queries.append(question)
        return ExtractiveResult("Раздаёт трафик.", units), "complete", []

    monkeypatch.setattr(server, "structural_search", lookup)
    question = "Как выбрать балансировщик для eu-south-2 и OpenSSL-3.5?"
    data = json.loads(request("/api/ask", {"question": question})[1])
    assert data["search_state"] == "complete" and queries == [question]

    exact = json.loads(request("/api/ask", {"question": "Открой [[arch-component-001]]"})[1])
    assert exact["sources"][0]["id"] == "ARCH-COMPONENT-001"
    missing = json.loads(request("/api/ask", {"question": "ARCH-COMPONENT-1000"})[1])
    assert missing["status"] == "not_found" and "ARCH-COMPONENT-1000" in missing["answer"]
    assert queries == [question]


def test_related_materials_keep_empty_answer_sources(knowledge_base, monkeypatch):
    knowledge_base("ARCH-COMPONENT-001", "Балансировщик", "# Балансировщик\n\n## Назначение\n\nРаздаёт трафик.", domain="arch")
    monkeypatch.setattr(server, "structural_search", lambda root, q, units: (None, "related_only", units))
    data = json.loads(request("/api/ask", {"question": "Вопрос о балансировщике"})[1])
    assert data["status"] == "not_found" and data["sources"] == []
    assert data["search_state"] == "related_only"
    assert data["related_materials"] == [{
        "id": "ARCH-COMPONENT-001", "title": "Балансировщик", "description": "Раздаёт трафик.",
        "domain": "arch", "url": "/cards/ARCH-COMPONENT-001",
    }]


def test_lifespan_warms_once_and_requests_wait_for_readiness(knowledge_base, monkeypatch):
    from kb.extractive import ExtractiveResult

    knowledge_base("CS-CONCEPT-001", "Тест", "Текст.")

    async def scenario():
        proceed = asyncio.Event()
        count = 0

        async def prepare(state):
            nonlocal count
            count += 1
            await proceed.wait()
            state.status = "ready"

        monkeypatch.setattr(server, "_prepare", prepare)
        monkeypatch.setattr(server, "structural_search",
                            lambda root, q, units: (ExtractiveResult("Текст.", units), "complete", []))
        async with server.lifespan(server.app):
            assert (await server.health()).status_code == 503
            responses = [asyncio.create_task(server.ask(server.AskRequest(question="Вопрос"))) for _ in range(2)]
            await asyncio.sleep(0)
            assert all(not pending.done() for pending in responses)
            proceed.set()
            assert all(response.search_state == "complete" for response in await asyncio.gather(*responses))
            assert (await server.health()).status_code == 200
        assert count == 1

    asyncio.run(scenario())


@pytest.mark.parametrize("error,fragment", [
    (FileNotFoundError("index"), "индекс отсутствует"),
    (server.VectorIndexError("Индекс фрагментов устарел."), "индекс нужно обновить"),
    (server.VectorIndexError("Model load failed"), "кеш MiniLM"),
])
def test_failed_preparation_reports_reason_without_retry(knowledge_base, monkeypatch, error, fragment):
    knowledge_base("CS-CONCEPT-001", "Тест", "Текст.")
    calls = []

    def fail():
        calls.append(error)
        raise error

    def unexpected(*args):
        pytest.fail("Preparing a failed index again")

    monkeypatch.setattr(server, "_warm_search", fail)
    monkeypatch.setattr(server, "structural_search", unexpected)

    async def scenario():
        async with server.lifespan(server.app):
            for _ in range(2):
                response = await server.ask(server.AskRequest(question="Тест"))
                assert response.status == "success" and fragment in response.search_notice
            health = await server.health()
            assert health.status_code == 503 and json.loads(health.body)["status"] == "degraded"

    asyncio.run(scenario())
    assert calls == [error]
