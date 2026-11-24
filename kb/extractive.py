"""Build answers from complete, unchanged sections of retrieved cards."""
import logging
import re
import sqlite3
import time
from dataclasses import dataclass

from .rag import RagConfig, RagError, _retrieve_sync
from .parser import ParseError
from .vector_store import VectorIndexError
from .search import _question_terms


@dataclass(frozen=True)
class ExtractiveResult:
    answer: str
    units: list


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
    start = time.perf_counter()
    config = RagConfig(base_url='http://127.0.0.1/v1', model='unused')
    try:
        hits = _retrieve_sync(root, question, config)
    except (VectorIndexError, ParseError, sqlite3.DatabaseError, OSError, ValueError) as exc:
        raise RagError(f"Гибридный поиск недоступен: {exc}") from exc
    result = form_answer(question, units, hits)
    logging.getLogger('uvicorn.error').info('extractive_total_seconds=%.3f hits=%d', time.perf_counter()-start, len(hits))
    return result
