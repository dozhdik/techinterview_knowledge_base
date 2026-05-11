"""
server.py — FastAPI-сервер для веб-MVP базы знаний TechInterview.

Запуск:
    python3 web/server.py
    # или
    uvicorn web.server:app --reload --port 8000

Открыть: http://localhost:8000
"""

import random
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response, FileResponse
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Пути
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent          # web/
STATIC_DIR = BASE_DIR / "static"                    # web/static/
KB_ROOT = BASE_DIR.parent                           # корень репозитория

# ---------------------------------------------------------------------------
# Приложение
# ---------------------------------------------------------------------------

app = FastAPI(title="TechInterview Knowledge Base", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Pydantic-модели (структура совместима с будущей RAG-системой)
# ---------------------------------------------------------------------------

class AskRequest(BaseModel):
    question: str


class SourceItem(BaseModel):
    title: str
    id: str
    url: str


class AskResponse(BaseModel):
    status: str                 # "success" | "error"
    answer: str                 # Markdown-текст ответа
    sources: list[SourceItem]   # список карточек из БЗ
    confidence: float           # 0.0–1.0, уверенность модели
    is_rag_enabled: bool        # false в MVP, true после подключения RAG


# ---------------------------------------------------------------------------
# Мок-данные (заменяются RAG на этапе 2)
# ---------------------------------------------------------------------------

_MOCK_ANSWERS = [
    {
        "answer": (
            "## Хеш-таблица (Hash Table)\n\n"
            "Структура данных, реализующая ассоциативный массив. "
            "Обеспечивает **O(1)** в среднем для операций вставки, удаления и поиска.\n\n"
            "### Ключевые моменты\n"
            "- Коллизии решаются через **chaining** или **open addressing**\n"
            "- Load factor > 0.75 → rehashing\n"
            "- В Python — встроенный `dict`\n\n"
            "### Сложность\n"
            "| Операция | Average | Worst |\n"
            "|----------|---------|-------|\n"
            "| Insert   | O(1)    | O(n)  |\n"
            "| Search   | O(1)    | O(n)  |\n"
            "| Delete   | O(1)    | O(n)  |"
        ),
        "sources": [
            {"title": "Хеш-таблица", "id": "CS-CONCEPT-009", "url": "#"},
            {"title": "Когда hash table перестаёт быть O(1)", "id": "CS-QUESTION-002", "url": "#"},
        ],
        "confidence": 0.92,
    },
    {
        "answer": (
            "## URL Shortener — System Design\n\n"
            "Классическая задача на System Design интервью.\n\n"
            "### Компоненты\n"
            "1. **API Gateway** — принимает запросы\n"
            "2. **Hash-функция** — генерирует короткий код (Base62, 6–8 символов)\n"
            "3. **БД** — хранит маппинг `short → long`\n"
            "4. **Cache (Redis)** — ускоряет redirect\n"
            "5. **CDN** — для глобального распределения\n\n"
            "### Оценка нагрузки\n"
            "- 100M URL/день → ~1200 write RPS\n"
            "- Read/Write ratio ≈ 100:1 → ~120K read RPS"
        ),
        "sources": [
            {"title": "URL Shortener (TinyURL/bit.ly)", "id": "ARCH-SYSDESIGN-005", "url": "#"},
            {"title": "Cache (Кеширование)", "id": "ARCH-COMPONENT-002", "url": "#"},
            {"title": "API Gateway", "id": "ARCH-COMPONENT-004", "url": "#"},
        ],
        "confidence": 0.88,
    },
    {
        "answer": (
            "## Метод STAR для behavioral-вопросов\n\n"
            "Структурированный фреймворк для ответов на поведенческие вопросы.\n\n"
            "- **S**ituation — опиши контекст и ситуацию\n"
            "- **T**ask — какая задача стояла перед тобой\n"
            "- **A**ction — что конкретно ты сделал\n"
            "- **R**esult — каков был результат (в цифрах, если возможно)\n\n"
            "> Пример: *«Расскажите о конфликте в команде»* → "
            "опиши ситуацию → твою роль → действия → итог."
        ),
        "sources": [
            {"title": "Метод STAR", "id": "PROC-FRAMEWORK-001", "url": "#"},
            {"title": "Расскажите о конфликте в команде", "id": "PROC-BEHAVIORAL-002", "url": "#"},
        ],
        "confidence": 0.95,
    },
]


def get_mock_answer(question: str) -> dict:
    """
    Возвращает мок-ответ на основе ключевых слов в вопросе.

    # TODO: RAG INTEGRATION — заменить эту функцию на вызов rag_search(question):
    #
    #   from rag.pipeline import rag_search
    #   return rag_search(question)
    #
    # rag_search должна:
    #   1. Векторизовать question через sentence-transformers
    #   2. Найти top-k карточек в ChromaDB/Qdrant
    #   3. Передать контекст + вопрос в LLM (OpenAI/Anthropic/local)
    #   4. Вернуть dict с полями answer, sources, confidence
    """
    q = question.lower()

    if any(w in q for w in ["hash", "хеш", "словарь", "dict"]):
        return _MOCK_ANSWERS[0]
    if any(w in q for w in ["url", "shortener", "tinyurl", "систем", "design", "дизайн"]):
        return _MOCK_ANSWERS[1]
    if any(w in q for w in ["star", "behavioral", "поведен", "конфликт", "расскажи"]):
        return _MOCK_ANSWERS[2]

    # Дефолтный ответ — случайный мок
    return random.choice(_MOCK_ANSWERS)


# ---------------------------------------------------------------------------
# Эндпоинты
# ---------------------------------------------------------------------------

@app.get("/", include_in_schema=False)
async def serve_index():
    return HTMLResponse((STATIC_DIR / "index.html").read_text(encoding="utf-8"))


@app.post("/api/ask", response_model=AskResponse)
async def ask(request: AskRequest) -> AskResponse:
    """
    Принимает вопрос пользователя, возвращает ответ из БЗ.

    MVP: возвращает мок-ответ.
    Этап 2: здесь будет вызов RAG-пайплайна.
    """
    if not request.question.strip():
        return AskResponse(
            status="error",
            answer="Пожалуйста, введите вопрос.",
            sources=[],
            confidence=0.0,
            is_rag_enabled=False,
        )

    # TODO: RAG INTEGRATION — заменить get_mock_answer на rag_search
    result = get_mock_answer(request.question)

    return AskResponse(
        status="success",
        answer=result["answer"],
        sources=[SourceItem(**s) for s in result["sources"]],
        confidence=result["confidence"],
        is_rag_enabled=False,  # TODO: RAG INTEGRATION — установить True после подключения
    )


# ---------------------------------------------------------------------------
# Статика — кастомный роутер без anyio/threadpool (обход битого sniffio в venv)
# ---------------------------------------------------------------------------

MIME_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css":  "text/css; charset=utf-8",
    ".js":   "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".png":  "image/png",
    ".ico":  "image/x-icon",
    ".svg":  "image/svg+xml",
    ".woff2": "font/woff2",
}

@app.get("/{full_path:path}", include_in_schema=False)
async def serve_static(full_path: str) -> Response:
    # Нормализуем путь и предотвращаем path traversal
    try:
        target = (STATIC_DIR / full_path).resolve()
        target.relative_to(STATIC_DIR.resolve())
    except ValueError:
        return Response(status_code=403)

    if target.is_dir():
        target = target / "index.html"

    if not target.exists():
        index = STATIC_DIR / "index.html"
        return HTMLResponse(index.read_text(encoding="utf-8"))

    mime = MIME_TYPES.get(target.suffix, "application/octet-stream")
    if "text" in mime or "javascript" in mime or "json" in mime:
        return Response(content=target.read_text(encoding="utf-8"), media_type=mime)
    return Response(content=target.read_bytes(), media_type=mime)


# ---------------------------------------------------------------------------
# Точка входа
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True, app_dir=str(BASE_DIR))


# ===========================================================================
# КАК ПОДКЛЮЧИТЬ RAG НА ЭТАПЕ 2
# ===========================================================================
#
# 1. Установить зависимости:
#       pip install langchain chromadb sentence-transformers openai
#    или для локальной LLM:
#       pip install langchain qdrant-client sentence-transformers ollama
#
# 2. Создать файл rag/pipeline.py:
#
#       from kb.parser import parse_directory          # уже есть в проекте!
#       from sentence_transformers import SentenceTransformer
#       import chromadb
#
#       def build_index():
#           units = parse_directory("cs") + parse_directory("arch") + parse_directory("process")
#           # векторизовать unit.content, сохранить в ChromaDB
#           ...
#
#       def rag_search(question: str) -> dict:
#           # 1. embed question
#           # 2. similarity search в ChromaDB → top-k units
#           # 3. передать в LLM с промптом
#           # 4. вернуть {"answer": "...", "sources": [...], "confidence": 0.9}
#           ...
#
# 3. В этом файле заменить:
#       result = get_mock_answer(request.question)
#    на:
#       from rag.pipeline import rag_search
#       result = await rag_search(request.question)
#
# 4. Установить is_rag_enabled=True в AskResponse.
#
# ===========================================================================
