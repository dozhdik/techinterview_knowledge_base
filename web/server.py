import sys
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel, Field


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
KB_ROOT = BASE_DIR.parent

if __package__ in (None, ""):
    sys.path.insert(0, str(KB_ROOT))

from kb.parser import parse_directory
from kb.content import has_material
from kb.search import requested_card_ids, search_question
from kb.rag import RagConfig, RagError, generate, retrieve


def load_units():
    return [unit for domain in ("cs", "arch", "process", "global")
            if (KB_ROOT / domain).is_dir()
            for unit in parse_directory(KB_ROOT / domain)]


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

    units = load_units()
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
                + "Материал из базы знаний:\n\n" + ready[0].content,
                sources=[SourceItem(title=unit.title, id=unit.id, url=f"/cards/{unit.id}")
                         for unit in ready[:3]],
            )
        return AskResponse(
            status="not_ready" if unfinished and not missing else "not_found",
            answer=" ".join(notices) + " Проверьте ID или спросите о другой теме.",
            sources=[],
        )

    rag_notice = ""
    try:
        rag_config = RagConfig.from_env()
        if rag_config:
            hits = await retrieve(KB_ROOT, request.question, units, rag_config)
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
    except RagError:
        rag_notice = "Генерация сейчас недоступна; показываю материал карточки.\n\n"

    results = search_question(units, request.question)
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


@app.get("/api/units/{unit_id}")
async def get_unit(unit_id: str):
    units = load_units()
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
