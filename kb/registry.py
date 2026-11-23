from dataclasses import dataclass, field
from collections import defaultdict
from pathlib import Path

from .parser import KnowledgeUnit


@dataclass
class RegistryEntry:
    id:         str
    title:      str
    domain:     str
    category:   str
    difficulty: str
    status:     str
    file_path:  str

    def to_md_row(self) -> str:
        short_path = self.file_path.replace("\\", "/")
        for prefix in ["cs/", "arch/", "process/", "global/", "_meta/"]:
            idx = short_path.find(prefix)
            if idx != -1:
                short_path = short_path[idx:]
                break
        return (
            f"| {self.id} | {self.title} | {self.domain} | "
            f"{self.category} | {self.difficulty} | {self.status} | "
            f"`{short_path}` |"
        )


@dataclass
class Registry:
    entries: list[RegistryEntry] = field(default_factory=list)


    @classmethod
    def build(cls, units: list[KnowledgeUnit]) -> "Registry":
        entries = [
            RegistryEntry(
                id=u.id,
                title=u.title,
                domain=u.domain,
                category=u.category,
                difficulty=u.difficulty,
                status=u.status,
                file_path=u.file_path,
            )
            for u in sorted(units, key=lambda u: u.id)
        ]
        return cls(entries=entries)


    def find_duplicates(self) -> dict[str, list[str]]:
        id_to_paths: dict[str, list[str]] = defaultdict(list)
        for entry in self.entries:
            id_to_paths[entry.id].append(entry.file_path)
        return {
            id_: paths
            for id_, paths in id_to_paths.items()
            if len(paths) > 1
        }

    def has_duplicates(self) -> bool:
        return len(self.find_duplicates()) > 0

    def get_by_id(self, id_: str) -> RegistryEntry | None:
        for entry in self.entries:
            if entry.id == id_:
                return entry
        return None

    def exists(self, id_: str) -> bool:
        return self.get_by_id(id_) is not None


    def next_id(self, domain: str, category: str) -> str:
        domain_codes = {
            "cs":      "CS",
            "arch":    "ARCH",
            "process": "PROC",
            "global":  "GLB",
        }
        domain_code   = domain_codes.get(domain.lower(), domain.upper())
        category_code = category.upper()
        prefix = f"{domain_code}-{category_code}-"

        existing_numbers = []
        for entry in self.entries:
            if entry.id.startswith(prefix):
                try:
                    number = int(entry.id[len(prefix):])
                    existing_numbers.append(number)
                except ValueError:
                    pass

        next_number = max(existing_numbers, default=0) + 1
        return f"{prefix}{next_number:03d}"


    def stats(self) -> dict:
        by_domain: dict[str, int] = defaultdict(int)
        by_category: dict[str, int] = defaultdict(int)
        by_status: dict[str, int] = defaultdict(int)
        by_difficulty: dict[str, int] = defaultdict(int)

        for entry in self.entries:
            by_domain[entry.domain]       += 1
            by_category[entry.category]   += 1
            by_status[entry.status]       += 1
            by_difficulty[entry.difficulty] += 1

        return {
            "total":         len(self.entries),
            "by_domain":     dict(by_domain),
            "by_category":   dict(by_category),
            "by_status":     dict(by_status),
            "by_difficulty": dict(by_difficulty),
            "duplicates":    len(self.find_duplicates()),
        }


    def to_markdown(self) -> str:
        stats = self.stats()
        lines = [
            "# Реестр идентификаторов",
            "",
            "Автоматически сгенерированный реестр всех единиц знаний БЗ TechInterview.",
            "",
            "## Статистика",
            "",
            f"- **Всего единиц знаний:** {stats['total']}",
        ]

        lines.append("- **По доменам:**")
        for domain, count in sorted(stats["by_domain"].items()):
            lines.append(f"  - `{domain}`: {count}")

        lines.append("- **По статусам:**")
        for status, count in sorted(stats["by_status"].items()):
            lines.append(f"  - `{status}`: {count}")

        if stats["duplicates"] > 0:
            lines.append(
                f"\n⚠️ **Обнаружены дублирующиеся ID: {stats['duplicates']}**"
            )

        lines += [
            "",
            "## Таблица идентификаторов",
            "",
            "| ID | Название | Домен | Категория | Сложность | Статус | Файл |",
            "|---|---|---|---|---|---|---|",
        ]

        for entry in self.entries:
            lines.append(entry.to_md_row())

        lines.append("")
        return "\n".join(lines)


    def save(self, output_path: str | Path = "_meta/id_registry.md") -> None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_markdown(), encoding="utf-8")
        print(f"✅ Реестр сохранён: {path} ({len(self.entries)} записей)")

    def print_stats(self) -> None:
        stats = self.stats()
        print(f"📋 Реестр идентификаторов")
        print(f"   Всего единиц знаний: {stats['total']}")
        print()
        print("   По доменам:")
        for domain, count in sorted(stats["by_domain"].items()):
            print(f"     {domain:<12} {count}")
        print()
        print("   По статусам:")
        for status, count in sorted(stats["by_status"].items()):
            print(f"     {status:<12} {count}")
        print()
        if stats["duplicates"] > 0:
            print(f"   ⚠️  Дублирующихся ID: {stats['duplicates']}")
            for id_, paths in self.find_duplicates().items():
                print(f"     {id_}: {paths}")
        else:
            print("   ✅ Дублирующихся ID не найдено")


def generate_registry(
    units: list[KnowledgeUnit],
    output_path: str | Path = "_meta/id_registry.md",
) -> Registry:
    registry = Registry.build(units)
    registry.save(output_path)
    return registry
