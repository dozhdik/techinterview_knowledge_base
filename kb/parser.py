import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class KnowledgeUnit:

    id: str
    title: str
    domain: str
    category: str
    difficulty: str

    tags: list[str]              = field(default_factory=list)
    roles: list[str]             = field(default_factory=list)
    interview_stage: list[str]   = field(default_factory=list)
    frequency: str               = ""
    related: list[str]           = field(default_factory=list)
    prerequisites: list[str]     = field(default_factory=list)
    sources: list[str]           = field(default_factory=list)
    author: str                  = ""
    version: str                 = "1.0"
    date_created: str            = ""
    date_updated: str            = ""
    status: str                  = "draft"

    file_path: str               = ""
    content: str                 = ""

    def __repr__(self) -> str:
        return f"KnowledgeUnit(id={self.id!r}, title={self.title!r})"


class ParseError(Exception):
    pass


_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)", re.DOTALL)

REQUIRED_FIELDS = {"id", "title", "domain", "category", "difficulty"}

VALID_DOMAINS     = {"cs", "arch", "process", "global"}
VALID_CATEGORIES  = {
    "concept", "problem", "pattern", "question", "cheatsheet", "pitfall",
    "component", "designpat", "sysdesign", "tradeoff", "checklist",
    "stage", "behavioral", "strategy", "company", "softskill",
    "framework", "glossary", "cross", "profile", "matrix",
    "trajectory", "onto",
}
VALID_DIFFICULTIES = {"junior", "middle", "senior", "staff"}


def _extract_frontmatter(raw: str, file_path: str) -> tuple[dict, str]:
    match = _FRONTMATTER_RE.match(raw)
    if not match:
        raise ParseError(
            f"{file_path}: YAML-фронтматтер не найден. "
            f"Файл должен начинаться с '---'."
        )

    yaml_str = match.group(1)
    content  = match.group(2).strip()

    try:
        metadata = yaml.safe_load(yaml_str) or {}
    except yaml.YAMLError as e:
        raise ParseError(f"{file_path}: Ошибка парсинга YAML — {e}")

    return metadata, content


def _validate_required(metadata: dict, file_path: str) -> None:
    missing = REQUIRED_FIELDS - metadata.keys()
    if missing:
        raise ParseError(
            f"{file_path}: Отсутствуют обязательные поля: {sorted(missing)}"
        )


def _to_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    return [str(value)]


def _build_unit(metadata: dict, content: str, file_path: str) -> KnowledgeUnit:
    return KnowledgeUnit(
        id             = str(metadata.get("id", "")),
        title          = str(metadata.get("title", "")),
        domain         = str(metadata.get("domain", "")),
        category       = str(metadata.get("category", "")),
        difficulty     = str(metadata.get("difficulty", "")),
        tags           = _to_list(metadata.get("tags")),
        roles          = _to_list(metadata.get("roles")),
        interview_stage= _to_list(metadata.get("interview_stage")),
        frequency      = str(metadata.get("frequency", "")),
        related        = _to_list(metadata.get("related")),
        prerequisites  = _to_list(metadata.get("prerequisites")),
        sources        = _to_list(metadata.get("sources")),
        author         = str(metadata.get("author", "")),
        version        = str(metadata.get("version", "1.0")),
        date_created   = str(metadata.get("date_created", "")),
        date_updated   = str(metadata.get("date_updated", "")),
        status         = str(metadata.get("status", "draft")),
        file_path      = file_path,
        content        = content,
    )


def parse_file(file_path: str | Path) -> KnowledgeUnit:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Файл не найден: {file_path}")
    if path.suffix != ".md":
        raise ParseError(f"Ожидается .md файл, получен: {path.suffix}")

    raw = path.read_text(encoding="utf-8")
    metadata, content = _extract_frontmatter(raw, str(path))
    _validate_required(metadata, str(path))

    return _build_unit(metadata, content, str(path.resolve()))


def parse_directory(root_dir: str | Path, skip_errors: bool = True) -> list[KnowledgeUnit]:
    root = Path(root_dir)
    if not root.is_dir():
        raise NotADirectoryError(f"Не является директорией: {root_dir}")

    SKIP_NAMES = {"readme", "contributing", "changelog", "index"}
    SKIP_DIRS = {"_meta", "venv"}

    units = []
    errors = []

    for md_file in sorted(root.rglob("*.md")):
        if any(part in SKIP_DIRS for part in md_file.parts):
            continue

        if md_file.stem.lower() in SKIP_NAMES:
            continue

        try:
            unit = parse_file(md_file)
            units.append(unit)
        except (ParseError, Exception) as e:
            if skip_errors:
                errors.append((str(md_file), str(e)))
            else:
                raise

    if errors:
        print(f"⚠️  Пропущено файлов с ошибками: {len(errors)}")
        for path, msg in errors:
            print(f"   {path}: {msg}")

    return units


def parse_file_safe(file_path: str | Path) -> Optional[KnowledgeUnit]:
    try:
        return parse_file(file_path)
    except Exception:
        return None


def summary(units: list[KnowledgeUnit]) -> None:
    if not units:
        print("Единиц знаний не найдено.")
        return

    from collections import Counter

    domains    = Counter(u.domain    for u in units)
    categories = Counter(u.category  for u in units)
    statuses   = Counter(u.status    for u in units)

    print(f"📚 Всего единиц знаний: {len(units)}")
    print()
    print("По доменам:")
    for domain, count in sorted(domains.items()):
        print(f"  {domain:<10} {count}")
    print()
    print("По категориям (топ-10):")
    for cat, count in categories.most_common(10):
        print(f"  {cat:<15} {count}")
    print()
    print("По статусу:")
    for status, count in sorted(statuses.items()):
        print(f"  {status:<10} {count}")
