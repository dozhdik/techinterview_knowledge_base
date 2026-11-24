"""Build and search corpus-derived descriptors and potential questions."""
from collections import Counter, defaultdict
from contextlib import closing
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path
import json
import math
import os
import re
import sqlite3
import tempfile

from .passage_index import DOMAINS, EXCLUDED, FENCE, INDEX as PASSAGE_INDEX, corpus_key, markdown_blocks
from .content import has_material
from .parser import parse_directory
from .query import normalize, terms
from .vector_store import DEFAULT_INDEX, DEFAULT_MODEL, VectorIndexError, _embedder, source_fingerprint

INDEX = Path("_data/representation_index.sqlite3")
VERSION = 1
CHANNEL_WEIGHTS = {"metadata": .32, "questions": .36}
MODES = ("off", "metadata", "questions", "combined")
FIELDS = {
    "aliases": 2.2, "purpose": 1.8, "problems_solved": 1.6, "use_cases": 1.10,
    "properties": 1.0, "mechanism": 1.10, "limits": .90, "interview": .52,
}
# Deeper headings take precedence, then their nearest recognisable ancestor.
_ROLES = (
    ("use_cases", r"когда (?:использ|примен|выбира)|применение|(?:практический )?пример|use cases"),
    ("limits", r"ограничен|границ|недостат|типичн\w+ ошиб|что проверить"),
    ("problems_solved", r"постановка задачи|условие|задача$|суть ошибки|проблем"),
    ("purpose", r"определение|назначение|что (?:это|такое)|зачем|цель|подход$|идея паттерна|суть навыка"),
    ("properties", r"главное|характерист|преимуществ|суть (?:выбора|компромисса)|сравнен"),
    ("mechanism", r"как (?:это|работ|устро|примен)|реализац|алгоритм|модель данных|подход к|шаг"),
)
_TEMPLATES = {
    "purpose": "Какой подход подходит для следующего назначения? {text}",
    "problems_solved": "Как решают следующую задачу? {text}",
    "use_cases": "Какой инструмент уместен в таком сценарии? {text}",
    "properties": "Что обладает следующими свойствами? {text}",
    "mechanism": "Для какой технологии характерен такой механизм? {text}",
    "limits": "При каком подходе важно учитывать такое ограничение? {text}",
}
_LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)|\[\[[A-Z]+-[A-Z]+-\d+\]\]")


@dataclass(frozen=True)
class Descriptor:
    kind: str
    text: str
    origin: str
    heading: tuple[str, ...] = ()
    position: int | None = None


@dataclass(frozen=True)
class PotentialQuestion:
    text: str
    template: str
    origin: str
    heading: tuple[str, ...] = ()
    position: int | None = None


def _role(headings):
    for heading in reversed(headings):
        for kind, regex in _ROLES:
            if re.search(regex, normalize(heading)):
                return kind
    return None


def _plain(block):
    return _LINK.sub(lambda match: match[1] or "", block).replace("**", "").replace("`", "")


def _excerpt(block):
    if FENCE.match(block) or block.lstrip().startswith(("|", "┌", "│")):
        return ""
    lines = [_plain(line).strip() for line in block.splitlines() if line.strip()]
    text = " ".join(re.sub(r"^\s*(?:[-*+] |\d+\. |\[[ xX]\] )", "", line) for line in lines[:3])
    sentences = re.split(r"(?<=[.!?])\s+(?=[А-ЯA-ZЁ])", text)
    text = " ".join(sentences[:2])
    words = text.split()
    return " ".join(words[:52]) if len(terms(text)) >= 5 else ""


def _aliases(title, tags):
    parts = re.split(r"[()]|\s+[—–]\s+|\s+/\s+", title)
    for part in dict.fromkeys(v.strip() for v in parts if v.strip() and terms(v)):
        yield Descriptor("aliases", part, "yaml.title")
    for tag in dict.fromkeys(tags):
        if terms(tag):
            yield Descriptor("aliases", tag, "yaml.tags")


def _without_title(text, alias_values):
    rewritten = text
    for alias in sorted(alias_values, key=len, reverse=True):
        if len(alias) >= 3:
            rewritten = re.sub(r"(?<!\w)" + re.escape(alias) + r"(?!\w)", "этот подход", rewritten,
                               flags=re.I)
    rewritten = re.sub(r"\(\s*этот подход\s*\)", "", rewritten, flags=re.I)
    return " ".join(rewritten.split()) if len(terms(rewritten)) >= 5 else text


def project(unit):
    """Derive search-only fields from one card, without an evaluation input."""
    aliases = list(_aliases(unit.title, unit.tags))
    descriptors = aliases.copy()
    value_roles = " ".join(dict.fromkeys((*unit.roles, *unit.interview_stage)))
    if value_roles:
        descriptors.append(Descriptor("interview", value_roles, "yaml.roles+interview_stage"))
    if unit.category == "question" and unit.title.rstrip().endswith("?"):
        title_question = unit.title
        template = "literal_title"
    else:
        subject = unit.title.rstrip().rstrip("?")
        title_question = f"Как объяснить назначение и применение темы «{subject}»?"
        template = "title_and_purpose"
    questions = [PotentialQuestion(title_question, template, "yaml.title")]
    seen = set()
    by_kind = defaultdict(list)
    for heading, position, _, text in markdown_blocks(unit.content):
        if any(EXCLUDED.match(h) for h in heading):
            continue
        kind = _role(heading)
        if kind is None:
            continue
        excerpt = _excerpt(text)
        if not excerpt or normalize(excerpt) in seen:
            continue
        # One representative per heading prevents long sections from crowding
        # out other aspects of a card.
        if any(d.heading == heading for d in by_kind[kind]) or len(by_kind[kind]) >= 2:
            continue
        seen.add(normalize(excerpt))
        by_kind[kind].append(Descriptor(kind, excerpt, "markdown", heading, position))
    for kind, values in by_kind.items():
        descriptors.extend(values)
        source = values[0]
        # Preserve the actual content after a purpose-oriented question frame.
        # Mask title forms, but leave technical words that occur only in the body.
        clause = _without_title(source.text, {d.text for d in aliases if d.origin == "yaml.title"})
        questions.append(PotentialQuestion(_TEMPLATES[kind].format(text=clause), kind,
                                           source.origin, source.heading, source.position))
    links = {"related": unit.related, "prerequisites": unit.prerequisites}
    return descriptors, questions, links


def _source_units(root):
    for domain in DOMAINS:
        path = root / domain
        if path.is_dir():
            for unit in parse_directory(path, skip_errors=False):
                if unit.status != "draft" and has_material(unit):
                    yield unit


def _bounded_question(encoder, text):
    tokenizer = encoder.tokenizer
    limit = encoder.max_seq_length - tokenizer.num_special_tokens_to_add()
    offsets = tokenizer(text, add_special_tokens=False, truncation=True, max_length=limit,
                        return_offsets_mapping=True)["offset_mapping"]
    return text[:offsets[-1][1]] if offsets else text


def build(root, path=None):
    import numpy as np

    root = Path(root).resolve()
    path = Path(path).resolve() if path is not None else root / INDEX
    if path in {(root / DEFAULT_INDEX).resolve(), (root / PASSAGE_INDEX).resolve()}:
        raise ValueError("Укажите отдельный индекс поисковых представлений.")
    digest = corpus_key(root)
    cards = []
    questions = []
    for unit in _source_units(root):
        descriptors, prompts, links = project(unit)
        cards.append((unit.id, unit.domain, json.dumps([asdict(d) for d in descriptors],
                    ensure_ascii=False), json.dumps(links, ensure_ascii=False)))
        questions.extend((unit.id, q) for q in prompts)
    if not cards:
        raise ValueError("В корпусе нет доступных карточек.")
    encoder = _embedder("sentence-transformers", DEFAULT_MODEL).encoder
    inputs = [_bounded_question(encoder, q.text) for _, q in questions]
    vectors = encoder.encode(inputs, batch_size=32, normalize_embeddings=True, show_progress_bar=False)
    vectors = np.asarray(vectors, dtype="<f4")
    if digest != corpus_key(root):
        raise ValueError("Карточки изменились во время построения поискового представления.")
    meta = dict(version=VERSION, model=DEFAULT_MODEL, corpus_sha256=digest, dimensions=vectors.shape[1],
                cards=len(cards), questions=len(questions), max_tokens=encoder.max_seq_length)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, suffix=".sqlite3")
    os.close(fd)
    try:
        with closing(sqlite3.connect(name)) as db, db:
            db.execute("CREATE TABLE metadata(value TEXT NOT NULL)")
            db.execute("INSERT INTO metadata VALUES (?)", (json.dumps(meta),))
            db.execute("CREATE TABLE cards(id TEXT PRIMARY KEY, domain TEXT, descriptors TEXT, links TEXT)")
            db.execute("CREATE TABLE questions(card_id TEXT, provenance TEXT, model_input TEXT, vector BLOB)")
            db.executemany("INSERT INTO cards VALUES (?, ?, ?, ?)", cards)
            db.executemany("INSERT INTO questions VALUES (?, ?, ?, ?)", (
                (card, json.dumps(asdict(q), ensure_ascii=False), word_input, vector.tobytes())
                for (card, q), word_input, vector in zip(questions, inputs, vectors, strict=True)))
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)
    return meta


class Representations:
    def __init__(self, metadata, cards, questions):
        import numpy as np

        self.metadata = metadata
        self.postings = defaultdict(dict)
        expanded = []
        for key, descriptors in cards:
            field_words = defaultdict(list)
            for d in json.loads(descriptors):
                field_words[d["kind"]].extend(terms(d["text"]))
            expanded.append((key, field_words))
        averages = {f: max(1., sum(len(words[f]) for _, words in expanded) / len(expanded)) for f in FIELDS}
        for key, fields in expanded:
            for field, words in fields.items():
                norm = .65 + .35 * len(words) / averages[field]
                for token, count in Counter(words).items():
                    posting = self.postings[token]
                    posting[key] = posting.get(key, 0.) + FIELDS[field] * count / norm
        self.idf = {token: math.log1p((len(cards) - len(rows) + .5) / (len(rows) + .5))
                    for token, rows in self.postings.items()}
        width = metadata["dimensions"]
        self.question_cards = [r[0] for r in questions]
        self.questions = [json.loads(r[1]) for r in questions]
        self.matrix = np.stack([np.frombuffer(row[2], dtype="<f4").reshape(width) for row in questions])

    def lexical(self, query, allowed, limit):
        scores = Counter()
        for token in query.tokens:
            for key, tf in self.postings.get(token, {}).items():
                if key in allowed:
                    scores[key] += self.idf[token] * 2.2 * tf / (1.2 + tf)
        return [(key, value, None) for key, value in sorted(scores.items(), key=lambda hit: (-hit[1], hit[0]))[:limit]]

    def dense(self, vector, allowed, limit):
        import numpy as np

        words = self.matrix @ np.asarray(vector, dtype=self.matrix.dtype)
        best = {}
        for i in np.argsort(-words, kind="stable"):
            key = self.question_cards[i]
            if key in allowed and key not in best:
                best[key] = (key, float(words[i]), self.questions[i])
                if len(best) >= limit:
                    break
        return list(best.values())


@lru_cache(maxsize=2)
def _load(root, path, stamp, fingerprint):
    with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as db:
        meta = json.loads(db.execute("SELECT value FROM metadata").fetchone()[0])
        if (meta["version"] != VERSION or meta["model"] != DEFAULT_MODEL
                or meta["corpus_sha256"] != corpus_key(root)):
            raise VectorIndexError("Поисковое представление устарело. Выполните representation-build.")
        cards = db.execute("SELECT id, descriptors FROM cards ORDER BY id").fetchall()
        questions = db.execute("SELECT card_id, provenance, vector FROM questions ORDER BY rowid").fetchall()
    return Representations(meta, cards, questions)


def get_representation(root, path=None):
    root = Path(root).resolve()
    path = Path(path).resolve() if path is not None else root / INDEX
    info = path.stat()
    return _load(root, path, (info.st_ino, info.st_ctime_ns, info.st_size), source_fingerprint(root))
