import asyncio
import functools
import json
import logging
import os
import re
import time
from contextlib import aclosing
import sys
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response, StreamingResponse
from pydantic import BaseModel, Field


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
KB_ROOT = BASE_DIR.parent

if __package__ in (None, ""):
    sys.path.insert(0, str(KB_ROOT))

from kb.extractive import search_and_extract
from kb.parser import parse_directory
from kb.content import has_material
from kb.search import requested_card_ids, search_question
from kb.rag import (INSUFFICIENT_CONTEXT, RagConfig, RagError, generate, retrieve,
                    prepare_context, validate_answer)
from kb.citation_stream import CitationFilter
from kb.ollama_stream import stream_chat
from kb.vector_store import source_fingerprint


@functools.lru_cache(maxsize=4)
def _load_units_cached(root, fingerprint):
    return tuple(unit for domain in ("cs", "arch", "process", "global")
                 if (root / domain).is_dir()
                 for unit in parse_directory(root / domain))


def load_units():
    start = time.perf_counter()
    units = list(_load_units_cached(KB_ROOT, source_fingerprint(KB_ROOT)))
    logging.getLogger("uvicorn.error").info("rag_load_cards_seconds=%.3f", time.perf_counter() - start)
    return units


logger = logging.getLogger("uvicorn.error")

app = FastAPI(title="TechInterview Knowledge Base", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    question: str = Field(max_length=1000)


class SourceItem(BaseModel):
    title: str
    id: str
    url: str


class AskResponse(BaseModel):
    status: str
    answer: str
    sources: list[SourceItem]
    confidence: float | None = None
    is_rag_enabled: bool = False


@app.get("/", include_in_schema=False)
async def serve_index():
    return HTMLResponse((STATIC_DIR / "index.html").read_text(encoding="utf-8"))


@app.post("/api/ask", response_model=AskResponse)
async def ask(request: AskRequest) -> AskResponse:
    if not request.question.strip():
        return AskResponse(status="error", answer="Пожалуйста, введите вопрос.", sources=[])

    units = await asyncio.to_thread(load_units)
    requested_ids = requested_card_ids(request.question)
    if requested_ids:
        by_id = {unit.id.upper(): unit for unit in units}
        missing = [card_id for card_id in requested_ids if card_id not in by_id]
        unfinished = [card_id for card_id in requested_ids
                      if card_id in by_id and not has_material(by_id[card_id])]
        ready = [by_id[card_id] for card_id in requested_ids
                 if card_id in by_id and has_material(by_id[card_id])]
        notices = []
        if missing:
            notices.append("Карточки пока нет в базе: " + ", ".join(missing) + ".")
        if unfinished:
            notices.append("Материал ещё не заполнен: " + ", ".join(unfinished) + ".")
        if ready:
            return AskResponse(
                status="success",
                answer=("\n\n".join(notices) + "\n\n" if notices else "")
                + "Материал из базы знаний:\n\n" + re.sub(r"\[\[[A-Z]+-[A-Z]+-\d+\]\]", "", ready[0].content),
                sources=[SourceItem(title=unit.title, id=unit.id, url=f"/cards/{unit.id}")
                         for unit in ready[:3]],
            )
        return AskResponse(
            status="not_ready" if unfinished and not missing else "not_found",
            answer=" ".join(notices) + " Проверьте ID или спросите о другой теме.",
            sources=[],
        )

    rag_notice = ""
    if os.getenv("RAG_ENABLED", "").strip().lower() not in ("1", "true", "yes"):
        try:
            extracted = await asyncio.to_thread(search_and_extract, KB_ROOT, request.question, units)
        except (RagError, OSError, ValueError) as exc:
            logger.warning("Hybrid search unavailable: %s", exc)
            rag_notice = "Семантический индекс недоступен; показаны результаты текстового поиска.\n\n"
        else:
            if extracted is None:
                return AskResponse(status="not_found", answer="Подходящих материалов в базе знаний не найдено.", sources=[])
            return AskResponse(status="success", answer=extracted.answer,
                sources=[SourceItem(title=unit.title, id=unit.id, url=f"/cards/{unit.id}") for unit in extracted.units])
    try:
        rag_config = RagConfig.from_env() if os.getenv("RAG_ENABLED", "").strip().lower() in ("1", "true", "yes") else None
        if rag_config:
            hits = await retrieve(KB_ROOT, request.question, units, rag_config)
            if not hits:
                return AskResponse(
                    status="not_found",
                    answer="В найденных материалах нет достаточного ответа на вопрос. Уточните тему.",
                    sources=[],
                )
            if hits:
                rag_result = await generate(request.question, hits, rag_config)
                if rag_result is None:
                    return AskResponse(
                        status="not_found",
                        answer="В найденных материалах нет достаточного ответа на вопрос. Уточните тему.",
                        sources=[],
                    )
                source_hits = list({hit.card_id: hit for hit in rag_result.hits}.values())
                return AskResponse(
                    status="success", answer=rag_result.answer,
                    sources=[SourceItem(title=hit.title, id=hit.card_id,
                                        url=f"/cards/{hit.card_id}") for hit in source_hits],
                    is_rag_enabled=True,
                )
    except RagError as exc:
        logger.warning("RAG unavailable: %s", exc)
        rag_notice = ("Ответ модели обрезан; показываю материал карточки.\n\n"
                      if "обрезан" in str(exc) else
                      "Генерация сейчас недоступна; показываю материал карточки.\n\n")

    results = await asyncio.to_thread(search_question, units, request.question)
    if not results:
        return AskResponse(
            status="not_found",
            answer=(rag_notice + "Подходящего определения или карточки пока нет в базе знаний. "
                    "Уточните название темы или укажите ID карточки."),
            sources=[],
        )

    if not has_material(results[0].unit):
        return AskResponse(
            status="not_ready",
            answer=(f"Карточка «{results[0].unit.title}» ({results[0].unit.id}) есть в базе, "
                    "но её материал пока не заполнен. Попробуйте другую тему."),
            sources=[],
        )

    return AskResponse(
        status="success",
        answer=rag_notice + "Материал из базы знаний:\n\n" + results[0].unit.content,
        sources=[SourceItem(title=r.unit.title, id=r.unit.id,
                            url=f"/cards/{r.unit.id}") for r in results
                 if has_material(r.unit)],
    )


def _event(kind, **values):
    return json.dumps({"type": kind, **values}, ensure_ascii=False) + "\n"


def _fallback(units, question):
    results = search_question(units, question)
    if not results:
        return AskResponse(status="not_found", answer="Подходящего материала в базе знаний нет.", sources=[])
    if not has_material(results[0].unit):
        return AskResponse(status="not_ready", answer="Материал карточки пока не заполнен.", sources=[])
    return AskResponse(status="success", answer="Генерация недоступна; материал из базы знаний:\n\n" + results[0].unit.content,
                       sources=[SourceItem(title=r.unit.title, id=r.unit.id, url=f"/cards/{r.unit.id}")
                                for r in results if has_material(r.unit)])


@app.post("/api/ask/stream")
async def ask_stream(request: AskRequest):
    async def events():
        started = time.perf_counter()
        units = []
        provisional = False
        try:
            yield _event("stage", stage="search", message="Поиск информации…")
            units = await asyncio.to_thread(load_units)
            config = RagConfig.from_env() if os.getenv("RAG_ENABLED", "").strip().lower() in ("1", "true", "yes") else None
            if not request.question.strip() or requested_card_ids(request.question) or not config:
                result = await ask(request)
                yield _event("final", **result.model_dump())
                return
            hits = await retrieve(KB_ROOT, request.question, units, config)
            if not hits:
                yield _event("final", status="not_found", answer="В базе знаний недостаточно информации для ответа.", sources=[], is_rag_enabled=False)
                return
            yield _event("stage", stage="context", message="Формирование контекста…")
            context_start = time.perf_counter()
            context, included = prepare_context(request.question, hits, config)
            logger.info("rag_context_seconds=%.3f", time.perf_counter() - context_start)
            if not context:
                yield _event("final", status="not_found", answer="Недостаточно места для контекста.", sources=[], is_rag_enabled=False)
                return
            yield _event("stage", stage="generation", message="Генерация ответа…")
            raw = ""
            prefix = ""
            filter_ = CitationFilter()
            done = None
            generation_start = time.perf_counter()
            async with aclosing(stream_chat(config, request.question, context, [hit.card_id for hit in included])) as upstream:
                async for item in upstream:
                    if item.get("error"):
                        raise RagError("Ollama: " + str(item["error"]))
                    message = item.get("message") or {}
                    if not isinstance(message, dict) or not isinstance(message.get("content", ""), str):
                        raise RagError("Ollama вернул некорректный текст")
                    content = message.get("content", "")
                    if content:
                        raw += content
                        # Do not expose an incomplete refusal marker as ordinary text.
                        if prefix is not None:
                            prefix += content
                            if INSUFFICIENT_CONTEXT.startswith(prefix):
                                continue
                            content, prefix = prefix, None
                        visible = filter_.feed(content)
                        if visible:
                            if not provisional:
                                logger.info("rag_first_visible_seconds=%.3f", time.perf_counter() - started)
                            provisional = True
                            yield _event("delta", text=visible)
                    if item.get("done"):
                        done = item
                        break
            if done is None:
                raise RagError("Ollama завершил поток без подтверждения окончания")
            logger.info("rag_generation_seconds=%.3f ollama_metrics=%s", time.perf_counter() - generation_start,
                        {k: done.get(k) for k in ("load_duration", "prompt_eval_count", "prompt_eval_duration", "eval_count", "eval_duration", "total_duration")})
            yield _event("stage", stage="verify", message="Проверка источников…")
            verify_start = time.perf_counter()
            try:
                result = validate_answer(raw.strip(), included, context)
            except RagError:
                if done.get("done_reason") == "length":
                    yield _event("truncated", status="truncated", answer="", sources=[], is_rag_enabled=False,
                                 message="Ответ обрезан и его источники не удалось проверить.")
                    return
                raise
            logger.info("rag_verify_seconds=%.3f", time.perf_counter() - verify_start)
            if result is None:
                if done.get("done_reason") == "length":
                    yield _event("truncated", status="truncated", answer="", sources=[], is_rag_enabled=False,
                                 message="Ответ модели обрезан по ограничению длины.")
                else:
                    yield _event("final", status="not_found", answer="В найденных материалах недостаточно информации для ответа.", sources=[], is_rag_enabled=False)
                return
            source_hits = list({hit.card_id: hit for hit in result.hits}.values())
            sources = [SourceItem(title=hit.title, id=hit.card_id, url=f"/cards/{hit.card_id}").model_dump() for hit in source_hits]
            if done.get("done_reason") == "length":
                yield _event("truncated", status="truncated", answer=result.answer, sources=sources, is_rag_enabled=False,
                             message="Ответ обрезан по ограничению длины и может быть неполным.")
                return
            yield _event("final", status="success", answer=result.answer, sources=sources, is_rag_enabled=True)
        except RagError as exc:
            logger.warning("RAG stream unavailable: %s", exc)
            if provisional:
                yield _event("error", message="Ответ не прошёл проверку или генерация прервалась. Попробуйте ещё раз.")
            else:
                result = await asyncio.to_thread(_fallback, units, request.question)
                yield _event("final", **result.model_dump())
        finally:
            logger.info("rag_total_seconds=%.3f", time.perf_counter() - started)

    return StreamingResponse(events(), media_type="application/x-ndjson", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.get("/api/units/{unit_id}")
async def get_unit(unit_id: str):
    units = await asyncio.to_thread(load_units)
    unit = next((u for u in units if u.id == unit_id), None)
    if unit is None:
        raise HTTPException(status_code=404, detail="Карточка не найдена")
    if not has_material(unit):
        raise HTTPException(status_code=409, detail="Материал карточки пока не заполнен")
    return {"id": unit.id, "title": unit.title, "domain": unit.domain,
            "difficulty": unit.difficulty, "status": unit.status,
            "content": unit.content}


@app.get("/cards/{unit_id}", include_in_schema=False)
async def serve_card(unit_id: str):
    page = (STATIC_DIR / "card.html").read_text(encoding="utf-8")
    try:
        await get_unit(unit_id)
    except HTTPException as exc:
        message = ("Карточка не найдена. Она могла быть удалена или ещё не добавлена."
                   if exc.status_code == 404 else "Материал этой карточки пока не заполнен.")
        return HTMLResponse(page.replace("Загрузка карточки…", message), status_code=exc.status_code)
    return HTMLResponse(page)


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


if __name__ == "__main__":
    uvicorn.run("web.server:app", host="0.0.0.0", port=8000, reload=True, app_dir=str(KB_ROOT))
