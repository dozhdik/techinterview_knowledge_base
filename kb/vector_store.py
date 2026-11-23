import hashlib
import json
import math
import re
import sqlite3
from array import array
from contextlib import closing, contextmanager
from dataclasses import dataclass
from pathlib import Path

from .content import has_material
from .parser import parse_directory


DEFAULT_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
DEFAULT_INDEX = Path("_data/vector_index.sqlite3")
HASH_DIMENSIONS = 1024
SCHEMA_VERSION = "1"


class VectorIndexError(Exception):
    pass


@dataclass(frozen=True)
class VectorHit:
    chunk_id: str
    card_id: str
    title: str
    domain: str
    category: str
    status: str
    source_path: str
    text: str
    score: float
    related: list[str]
    sources: list[str]


class HashEmbedder:
    backend = "hash"
    model = f"word-char-hash-v1-{HASH_DIMENSIONS}"

    def embed_documents(self, texts):
        return [self._embed(text) for text in texts]

    def embed_query(self, text):
        return self._embed(text)

    def _embed(self, text):
        vector = [0.0] * HASH_DIMENSIONS
        words = re.findall(r"[a-zа-яё0-9]+", text.lower().replace("ё", "е"))
        for word in words:
            if len(word) < 3:
                continue
            self._add(vector, "w:" + word, 2.0)
            padded = "^" + word + "$"
            for width in (3, 4):
                for offset in range(len(padded) - width + 1):
                    self._add(vector, "c:" + padded[offset:offset + width], 0.4)
        return _normalize(vector)

    @staticmethod
    def _add(vector, feature, weight):
        digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
        slot = int.from_bytes(digest[:4], "little") % HASH_DIMENSIONS
        vector[slot] += weight if digest[4] & 1 else -weight


class SentenceTransformerEmbedder:
    backend = "sentence-transformers"

    def __init__(self, model=DEFAULT_MODEL):
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise VectorIndexError(
                "Для семантических векторов установите sentence-transformers "
                "и повторите построение индекса."
            ) from exc
        self.model = model
        try:
            self.encoder = SentenceTransformer(model)
        except Exception as exc:
            raise VectorIndexError(f"Не удалось загрузить модель {model}: {exc}") from exc

    def embed_documents(self, texts):
        encode = getattr(self.encoder, "encode_document", self.encoder.encode)
        return [_normalize(row.tolist() if hasattr(row, "tolist") else row)
                for row in encode(texts)]

    def embed_query(self, text):
        encode = getattr(self.encoder, "encode_query", self.encoder.encode)
        row = encode([text])[0]
        return _normalize(row.tolist() if hasattr(row, "tolist") else row)


def _normalize(values):
    values = [float(value) for value in values]
    magnitude = math.sqrt(sum(value * value for value in values))
    return [value / magnitude for value in values] if magnitude else values


def _embedder(backend, model=None):
    if backend == "hash":
        embedder = HashEmbedder()
        if model and model != embedder.model:
            raise VectorIndexError(f"Неизвестная версия hash-векторов: {model}")
        return embedder
    if backend == "sentence-transformers":
        return SentenceTransformerEmbedder(model or DEFAULT_MODEL)
    raise VectorIndexError(f"Неизвестный backend: {backend}")


def _split_text(content, max_chars):
    content = content.strip()
    if len(content) <= max_chars:
        return [content]
    sections = re.split(r"(?=^## )", content, flags=re.MULTILINE)
    chunks = []
    for section in sections:
        section = section.strip()
        if not section:
            continue
        if section.startswith("# ") and "\n" not in section:
            continue
        if len(section) <= max_chars:
            chunks.append(section)
            continue
        lines = section.split("\n\n")
        heading = lines[0] if lines[0].startswith("## ") else ""
        current = heading
        for paragraph in lines[1:] if heading else lines:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            if len(current) + len(paragraph) + 2 > max_chars and current != heading:
                chunks.append(current)
                current = heading
            if len(paragraph) + len(heading) + 2 <= max_chars:
                current = (current + "\n\n" + paragraph).strip()
            else:
                available = max_chars - len(heading) - 2
                for start in range(0, len(paragraph), available):
                    part = paragraph[start:start + available]
                    if current != heading:
                        chunks.append(current)
                    current = (heading + "\n\n" + part).strip()
        if current and current != heading:
            chunks.append(current)
    return chunks


def _collect(root, max_chars):
    records = []
    for domain in ("cs", "arch", "process", "global"):
        folder = root / domain
        if not folder.is_dir():
            continue
        for unit in parse_directory(folder, skip_errors=False):
            if unit.status == "draft" or not has_material(unit):
                continue
            source_path = str(Path(unit.file_path).relative_to(root))
            content = re.sub(
                r"(?ms)^## (?:Связанные темы|Связанные задачи и концепции|"
                r"Источники|Источник)\s*\n.*?(?=^## |\Z)", "", unit.content
            ).strip()
            for number, text in enumerate(_split_text(content, max_chars)):
                embedding_text = f"{unit.title}\n{unit.title}\n{text}\n{' '.join(unit.tags)}"
                record = {
                    "chunk_id": f"{unit.id}:{number:03d}",
                    "card_id": unit.id,
                    "title": unit.title,
                    "domain": unit.domain,
                    "category": unit.category,
                    "status": unit.status,
                    "source_path": source_path,
                    "text": text,
                    "related": unit.related,
                    "sources": unit.sources,
                    "embedding_text": embedding_text,
                }
                record["record_hash"] = hashlib.sha256(
                    json.dumps(record, sort_keys=True, ensure_ascii=False).encode("utf-8")
                ).hexdigest()
                records.append(record)
    if len({record["chunk_id"] for record in records}) != len(records):
        raise VectorIndexError("Повторяющиеся ID карточек или фрагментов")
    return records


def _digest(records):
    joined = "\n".join(record["chunk_id"] + record["record_hash"] for record in records)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def _connect(index_path):
    connection = sqlite3.connect(index_path)
    connection.row_factory = sqlite3.Row
    connection.execute("CREATE TABLE IF NOT EXISTS index_info (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    connection.execute("""CREATE TABLE IF NOT EXISTS chunks (
        chunk_id TEXT PRIMARY KEY, card_id TEXT NOT NULL, title TEXT NOT NULL,
        domain TEXT NOT NULL, category TEXT NOT NULL, status TEXT NOT NULL,
        source_path TEXT NOT NULL, text TEXT NOT NULL, related TEXT NOT NULL,
        sources TEXT NOT NULL, record_hash TEXT NOT NULL, embedding BLOB NOT NULL
    )""")
    connection.execute("CREATE INDEX IF NOT EXISTS chunks_domain ON chunks(domain)")
    connection.execute("CREATE INDEX IF NOT EXISTS chunks_card_id ON chunks(card_id)")
    return connection


@contextmanager
def _database(index_path):
    connection = _connect(index_path)
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def _info(connection):
    return {row["key"]: row["value"] for row in connection.execute("SELECT key, value FROM index_info")}


def build_index(root, index_path=None, backend="hash", model=None, max_chars=1400):
    root = Path(root).resolve()
    index_path = Path(index_path) if index_path else root / DEFAULT_INDEX
    if max_chars < 200:
        raise ValueError("max_chars должен быть не меньше 200")
    records = _collect(root, max_chars)
    if not records:
        raise VectorIndexError("Нет заполненных карточек для индексации")
    embedder = _embedder(backend, model)
    dimensions = len(embedder.embed_query("проверка"))
    if dimensions < 1:
        raise VectorIndexError("Модель вернула пустой вектор запроса")
    index_path.parent.mkdir(parents=True, exist_ok=True)
    with _database(index_path) as connection:
        info = _info(connection)
        compatible = (info.get("schema_version") == SCHEMA_VERSION
                      and info.get("backend") == embedder.backend
                      and info.get("model") == embedder.model
                      and info.get("max_chars") == str(max_chars))
        if not compatible:
            connection.execute("DELETE FROM chunks")
        existing = {row["chunk_id"]: row["record_hash"] for row in
                    connection.execute("SELECT chunk_id, record_hash FROM chunks")}
        changed = [record for record in records
                   if existing.get(record["chunk_id"]) != record["record_hash"]]
        for offset in range(0, len(changed), 32):
            batch = changed[offset:offset + 32]
            vectors = embedder.embed_documents([record["embedding_text"] for record in batch])
            if len(vectors) != len(batch):
                raise VectorIndexError("Модель вернула неверное число векторов")
            for record, vector in zip(batch, vectors):
                if len(vector) != dimensions or not all(math.isfinite(value) for value in vector):
                    raise VectorIndexError("Модель вернула вектор неверной размерности или с некорректными значениями")
                connection.execute("""INSERT OR REPLACE INTO chunks VALUES
                    (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
                    record["chunk_id"], record["card_id"], record["title"],
                    record["domain"], record["category"], record["status"],
                    record["source_path"], record["text"],
                    json.dumps(record["related"], ensure_ascii=False),
                    json.dumps(record["sources"], ensure_ascii=False),
                    record["record_hash"], array("f", vector).tobytes(),
                ))
        active = {record["chunk_id"] for record in records}
        removed = len(existing.keys() - active)
        for chunk_id in existing.keys() - active:
            connection.execute("DELETE FROM chunks WHERE chunk_id = ?", (chunk_id,))
        for key, value in {
            "schema_version": SCHEMA_VERSION,
            "backend": embedder.backend,
            "model": embedder.model,
            "max_chars": str(max_chars),
            "source_digest": _digest(records),
            "dimensions": str(dimensions),
        }.items():
            connection.execute("INSERT OR REPLACE INTO index_info VALUES (?, ?)", (key, value))
    return {"cards": len({record["card_id"] for record in records}),
            "chunks": len(records), "updated": len(changed), "removed": removed,
            "backend": embedder.backend, "model": embedder.model,
            "path": str(index_path)}


def index_status(root, index_path=None):
    root = Path(root).resolve()
    index_path = Path(index_path) if index_path else root / DEFAULT_INDEX
    if not index_path.exists():
        raise VectorIndexError(f"Индекс не найден: {index_path}. Сначала выполните vector-build.")
    with _database(index_path) as connection:
        info = _info(connection)
        if info.get("schema_version") != SCHEMA_VERSION:
            raise VectorIndexError("Версия векторного индекса устарела. Перестройте индекс.")
        count = connection.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        cards = connection.execute("SELECT COUNT(DISTINCT card_id) FROM chunks").fetchone()[0]
    records = _collect(root, int(info["max_chars"]))
    return {"path": str(index_path), "backend": info["backend"],
            "model": info["model"], "dimensions": int(info["dimensions"]),
            "max_chars": int(info["max_chars"]),
            "cards": cards, "chunks": count,
            "fresh": info["source_digest"] == _digest(records)}


def search_index(root, question, index_path=None, limit=5, domain=None, min_score=0.0):
    if not question.strip() or limit < 1:
        return []
    status = index_status(root, index_path)
    if not status["fresh"]:
        raise VectorIndexError("Карточки изменились после индексации. Выполните vector-build.")
    embedder = _embedder(status["backend"], status["model"])
    query_vector = embedder.embed_query(question)
    if not any(query_vector):
        return []
    with closing(sqlite3.connect(status["path"])) as connection:
        connection.row_factory = sqlite3.Row
        if domain:
            rows = connection.execute("SELECT * FROM chunks WHERE domain = ?", (domain,))
        else:
            rows = connection.execute("SELECT * FROM chunks")
        hits = []
        for row in rows:
            vector = array("f")
            vector.frombytes(row["embedding"])
            if len(vector) != len(query_vector):
                raise VectorIndexError("Размерность векторов не совпадает. Перестройте индекс.")
            score = sum(left * right for left, right in zip(vector, query_vector))
            if score < min_score:
                continue
            hits.append(VectorHit(
                chunk_id=row["chunk_id"], card_id=row["card_id"],
                title=row["title"], domain=row["domain"],
                category=row["category"], status=row["status"],
                source_path=row["source_path"], text=row["text"],
                score=score, related=json.loads(row["related"]),
                sources=json.loads(row["sources"]),
            ))
    hits.sort(key=lambda hit: (-hit.score, hit.chunk_id))
    return hits[:limit]
