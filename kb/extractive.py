"""Build answers from complete, unchanged sections of retrieved cards."""
import logging
import re
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path

from .rag import RagConfig, RagError, _retrieve_sync
from .parser import ParseError
from .vector_store import VectorIndexError
from .content import has_material
from .search import _question_terms, requested_card_ids
from .titles import title_index


@dataclass(frozen=True)
class ExtractiveResult:
    answer: str
    units: list


def direct_search(question, units, domain=None):
    """Resolve an ID or an entire card name before retrieving passages."""
    ids = requested_card_ids(question)
    match = title_index(units).match(question, domain) if not ids else None
    if not ids and not match:
        return None
    kind, keys = ("id", tuple(ids)) if ids else (match.kind, match.ids)
    by_id = {u.id.upper(): u for u in units if not domain or getattr(u, "domain", None) == domain}
    cards = [by_id[key] for key in keys if key in by_id]
    available = [u for u in cards if getattr(u, "status", None) != "draft"
                 and getattr(u, "content", "") and has_material(u)]
    missing = [key for key in keys if key not in by_id]
    unavailable = [u.id for u in cards if u not in available]
    notices = []
    if missing:
        notices.append("Карточки пока нет в базе: " + ", ".join(missing) + ".")
    if unavailable:
        notices.append("Материал ещё не заполнен или находится в черновике: " + ", ".join(unavailable) + ".")

    if not ids and len(available) > 1:
        status, state = "success", "clarification"
        text = "Уточните, какую карточку открыть, указав её ID. По этому названию найдены:\n\n" + "\n".join(
            f"- {u.title} ({u.domain}, {u.id})" for u in available)
        ranked, sources = [], []
    elif available:
        status, state = "success", "partial" if notices and ids else "complete"
        sources = available[:3]
        ranked = [u.id for u in sources]
        contents = [re.sub(r"\[\[[A-Z]+-[A-Z]+-\d+\]\]", "", u.content) for u in sources]
        text = "\n\n".join([*(notices if ids else []), "Материал из базы знаний:", *contents])
    else:
        status, state = ("not_ready", "absent") if unavailable and not missing else ("not_found", "absent")
        text = " ".join(notices) + " Проверьте ID или спросите о другой теме."
        ranked, sources = [], []

    return ExtractiveResult(text, sources), {
        "query": question, "lookup": {"kind": kind, "status": status, "candidates": list(keys)},
        "ranked_cards": ranked, "state": state, "parts": [], "selected": [],
        "sources": [u.id for u in sources], "unanswered": [], "deferred": [], "seconds": {},
    }


def _sections(content):
    # Only level-two headings delimit sections; fenced code blocks remain intact.
    sections = []
    lines = content.splitlines(keepends=True)
    heading, body, fenced = None, [], False
    for line in lines:
        if re.match(r'^\s*```', line):
            fenced = not fenced
        match = None if fenced else re.match(r'^##\s+(.+?)\s*$', line)
        if match:
            if heading and ''.join(body).strip():
                sections.append((heading, ''.join(body).strip()))
            heading, body = match.group(1), []
        elif heading:
            body.append(line)
    if heading and ''.join(body).strip():
        sections.append((heading, ''.join(body).strip()))
    return sections


def _priority(question, heading, text):
    q = question.lower()
    h = heading.lower()
    if any(x in h for x in ('связанные', 'источник', 'что дальше', 'литература')):
        return -1
    score = len(_question_terms(question) & _question_terms(heading + ' ' + text))
    if any(x in h for x in ('определение', 'короткий ответ', 'главное')):
        score += 8
    if any(x in h for x in ('суть компромисса', 'сравнительная таблица')):
        score += 10
    if any(x in h for x in ('суть концепции', 'как это работает', 'как работает')):
        score += 7
    if any(x in q for x in ('сложност', 'o(1)', 'времен', 'памят')) and any(x in h for x in ('характеристик', 'сложност', 'границ')):
        score += 8
    if any(x in q for x in ('подготов', 'готовиться', 'собеседован')) and any(x in h for x in ('готов', 'подготов', 'собеседован')):
        score += 12
    if any(x in q for x in ('пример', 'примен', 'использ', 'когда')) and any(x in h for x in ('пример', 'примен', 'использ', 'суть', 'ограничен')):
        score += 5
    return score


def form_answer(question, units, hits):
    by_id = {unit.id: unit for unit in units}
    top = next((hit for hit in hits if hit.card_id in by_id), None)
    if not top:
        return None
    unit = by_id[top.card_id]
    sections = _sections(unit.content)
    ranked = sorted(enumerate(sections), key=lambda item: (-_priority(question, *item[1]), item[0]))
    chosen, seen, used = [], set(), 0
    for index, (heading, text) in ranked:
        if _priority(question, heading, text) < 0 or len(chosen) >= 3:
            continue
        key = re.sub(r'\s+', ' ', text).strip().casefold()
        if key in seen or used + len(text) > 12000:
            continue
        # Remove only wiki ID markers, retaining all other original text.
        text = re.sub(r'\[\[[A-Z]+-[A-Z]+-\d+\]\]', '', text)
        chosen.append((index, heading, text))
        seen.add(key)
        used += len(text)
    if not chosen:
        return None
    chosen.sort()
    answer = '# ' + unit.title + '\n\n' + '\n\n'.join(f'## {heading}\n\n{text}' for _, heading, text in chosen)
    return ExtractiveResult(answer=answer, units=[unit])


def search_and_extract(root, question, units):
    from .passage_index import INDEX
    start = time.perf_counter()
    if (Path(root) / INDEX).is_file():
        try:
            result, _, _ = structural_search(root, question, units)
            return result
        except (VectorIndexError, sqlite3.DatabaseError, OSError, ValueError) as exc:
            logging.getLogger("uvicorn.error").warning("Структурный индекс недоступен: %s", exc)
    config = RagConfig(base_url='http://127.0.0.1/v1', model='unused')
    try:
        hits = _retrieve_sync(root, question, config)
    except (VectorIndexError, ParseError, sqlite3.DatabaseError, OSError, ValueError) as exc:
        raise RagError(f"Гибридный поиск недоступен: {exc}") from exc
    result = form_answer(question, units, hits)
    logging.getLogger('uvicorn.error').info('extractive_total_seconds=%.3f hits=%d', time.perf_counter()-start, len(hits))
    return result


def card_description(unit):
    """Return the first short prose paragraph under a source description heading."""
    headings = {
        "определение", "назначение", "короткий ответ", "суть концепции", "суть навыка",
        "суть паттерна", "идея паттерна", "подход", "идея", "что это такое",
    }
    for heading, text in _sections(unit.content):
        name = heading.strip().casefold()
        if name not in headings and not name.startswith("что такое "):
            continue
        paragraph = text.split("\n\n", 1)[0].strip()
        if not paragraph or paragraph.startswith(("-", "*", "|", "`", "#", "<", ">")):
            continue
        description = re.sub(r"\s+", " ", paragraph)
        if len(description) > 240:
            description = description[:240].rsplit(" ", 1)[0] + "…"
        return description
    return None


def structural_search(root, question, units):
    """Return the extracted answer, evidence state and separate suggestions."""
    from .retrieval import configured_reranker, get_engine

    start = time.perf_counter()
    engine = get_engine(root)
    result, debug = engine.ask(question, units, reranker=configured_reranker())
    by_id = {unit.id: unit for unit in units}
    related = [by_id[card] for card in engine.related_cards(debug) if card in by_id]
    state = debug["state"]
    if state in ("related_only", "absent"):
        state = "related_only" if related else "absent"
    logging.getLogger("uvicorn.error").info("search_seconds=%s total=%.3f",
                                           debug["seconds"], time.perf_counter() - start)
    return result, state, related
