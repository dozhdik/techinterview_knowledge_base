"""Versioned SQLite index for Markdown blocks and their parent sections."""
import hashlib
import json
import os
import re
import sqlite3
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

from .content import has_material
from .parser import parse_directory
from .vector_store import DEFAULT_MODEL, _embedder, source_fingerprint

INDEX = Path("_data/passage_index.sqlite3")
VERSION = 1
DOMAINS = ("cs", "arch", "process", "global")
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
EXCLUDED = re.compile(r"^(?:Связанн|Источни|Литература|References|Что дальше)", re.I)


@dataclass(frozen=True)
class Passage:
    card_id: str
    title: str
    domain: str
    category: str
    tags: list
    heading: tuple
    position: int
    section: int
    text: str
    related: list
    prerequisites: list


def markdown_blocks(content):
    headings = []
    buffer = []
    fence = None
    offset = 0
    start = 0
    section = 0

    def block():
        return (tuple(title for _, title in headings), start, section, "".join(buffer).strip("\n"))

    for line in content.splitlines(keepends=True):
        match = HEADING.match(line) if fence is None else None
        marker = FENCE.match(line)
        if match:
            if buffer:
                yield block()
                buffer.clear()
            depth = len(match[1])
            headings = [(n, title) for n, title in headings if n < depth]
            if depth > 1:
                headings.append((depth, match[2]))
            section += 1
        elif marker:
            symbol = marker[1]
            if fence is None:
                if buffer:
                    yield block()
                    buffer.clear()
                start = offset
                fence = symbol
                buffer.append(line)
            else:
                buffer.append(line)
                if symbol[0] == fence[0] and len(symbol) >= len(fence) and not line[marker.end():].strip():
                    fence = None
                    yield block()
                    buffer.clear()
        elif fence is None and not line.strip():
            if buffer:
                yield block()
                buffer.clear()
        else:
            if not buffer:
                start = offset
            buffer.append(line)
        offset += len(line)
    if buffer:
        yield block()


def close_code_fence(markdown):
    """Keep an unclosed source fence from consuming the rest of an answer."""
    fence = None
    for line in markdown.splitlines():
        marker = FENCE.match(line)
        if marker is None:
            continue
        symbol = marker[1]
        if fence is None:
            fence = symbol
        elif symbol[0] == fence[0] and len(symbol) >= len(fence) and not line[marker.end():].strip():
            fence = None
    return f"{markdown}\n{fence}" if fence else markdown


def corpus_key(root):
    digest = hashlib.sha256()
    for name, *_ in source_fingerprint(root):
        digest.update(name.encode())
        digest.update(hashlib.sha256((root / name).read_bytes()).digest())
    return digest.hexdigest()


def _records(root):
    for domain in DOMAINS:
        if not (root / domain).is_dir():
            continue
        for unit in parse_directory(root / domain, skip_errors=False):
            if unit.status == "draft" or not has_material(unit):
                continue
            for headings, pos, section, text in markdown_blocks(unit.content):
                if not text.strip() or any(EXCLUDED.match(h) for h in headings):
                    continue
                yield Passage(unit.id, unit.title, unit.domain, unit.category, unit.tags, headings,
                              pos, section, text, unit.related, unit.prerequisites)


def embedding_windows(passage, tokenizer, limit, passage_prefix=''):
    prefix = passage_prefix + f"{passage.title}. {' / '.join(passage.heading)}. "
    prefix_ids = tokenizer(prefix, add_special_tokens=False)["input_ids"][:limit // 3]
    ids = tokenizer(passage.text, add_special_tokens=False, verbose=False)["input_ids"]
    prefix = tokenizer.decode(prefix_ids)
    budget = limit - tokenizer.num_special_tokens_to_add() - len(prefix_ids) - 8
    windows = []
    # Only the embedding surrogate is split. The original block is kept intact.
    for offset in range(0, len(ids) or 1, budget):
        part = ids[offset:offset + budget]
        text = prefix + " " + tokenizer.decode(part)
        while len(tokenizer(text)["input_ids"]) > limit:
            part = part[:-1]
            text = prefix + " " + tokenizer.decode(part)
        windows.append(text)
    return windows


def build(root, path=None, model=DEFAULT_MODEL, *, e5=False):
    import numpy as np

    root = Path(root).resolve()
    path = Path(path) if path is not None else root / INDEX
    path.parent.mkdir(parents=True, exist_ok=True)
    digest = corpus_key(root)
    embedder = _embedder("sentence-transformers", model)
    encoder = embedder.encoder
    max_tokens = int(encoder.max_seq_length)
    query_prefix, passage_prefix = ("query: ", "passage: ") if e5 else ("", "")
    previous = {}
    if path.is_file():
        with sqlite3.connect(path) as conn:
            meta = json.loads(conn.execute("SELECT value FROM metadata").fetchone()[0])
            if (meta["version"], meta["model"], meta["max_tokens"], meta.get("query_prefix", "")) == (
                    VERSION, model, max_tokens, query_prefix):
                if meta["corpus_sha256"] == digest:
                    return {**meta, "updated": 0}
                previous = dict(conn.execute("SELECT fingerprint, vector FROM passages"))
    records = list(_records(root))
    entries = [(p, hashlib.sha256(json.dumps(asdict(p), ensure_ascii=False, sort_keys=True).encode()).hexdigest())
               for p in records]
    changed = [(p, key) for p, key in entries if key not in previous]
    for offset in range(0, len(changed), 64):
        batch = changed[offset:offset + 64]
        windows = [embedding_windows(p, encoder.tokenizer, max_tokens, passage_prefix) for p, _ in batch]
        vectors = encoder.encode([w for group in windows for w in group], normalize_embeddings=True)
        start = 0
        for (_, key), group in zip(batch, windows):
            vector = np.asarray(vectors[start:start + len(group)], dtype="<f4")
            previous[key] = vector.tobytes()
            start += len(group)
    if corpus_key(root) != digest:
        raise ValueError("Карточки изменились во время индексации")
    meta = dict(version=VERSION, model=model, max_tokens=max_tokens, corpus_sha256=digest,
                dimensions=int(encoder.get_sentence_embedding_dimension()), cards=len({p.card_id for p in records}),
                passages=len(records))
    if e5:
        meta.update(query_prefix=query_prefix, passage_prefix=passage_prefix)
    fd, name = tempfile.mkstemp(dir=path.parent, suffix=".sqlite3")
    os.close(fd)
    try:
        with sqlite3.connect(name) as conn:
            conn.execute("CREATE TABLE metadata(value TEXT)")
            conn.execute("INSERT INTO metadata VALUES (?)", (json.dumps(meta),))
            conn.execute("CREATE TABLE passages(fingerprint TEXT, data TEXT, vector BLOB)")
            conn.executemany("INSERT INTO passages VALUES (?, ?, ?)",
                             ((key, json.dumps(asdict(p), ensure_ascii=False), previous[key]) for p, key in entries))
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)
    return {**meta, "updated": len(changed)}
