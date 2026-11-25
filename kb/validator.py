import re
from dataclasses import dataclass, field
from collections import defaultdict

from .parser import KnowledgeUnit
from .titles import normalize_title, title_index


VALID_DOMAINS = {"cs", "arch", "process", "global"}

VALID_CATEGORIES = {
    "concept", "problem", "pattern", "question", "cheatsheet", "pitfall",
    "component", "designpat", "sysdesign", "tradeoff", "checklist",
    "stage", "behavioral", "strategy", "company", "softskill",
    "framework", "glossary", "cross", "profile", "matrix",
    "trajectory", "onto",
}

VALID_DIFFICULTIES = {"junior", "middle", "senior", "staff"}

VALID_FREQUENCIES = {"high", "medium", "low", ""}

VALID_STATUSES = {"draft", "review", "approved"}

VALID_ROLES = {
    "backend", "frontend", "fullstack", "devops",
    "data_engineer", "mobile", "ml_engineer", "all_roles",
}

VALID_INTERVIEW_STAGES = {
    "phone_screen", "coding", "system_design",
    "behavioral", "take_home", "team_match", "offer", "hr_screening",
}

ID_PATTERN = re.compile(r"^[A-Z]+-[A-Z]+-\d+$")


@dataclass
class ValidationIssue:
    unit_id:   str
    field:     str
    severity:  str
    message:   str

    def __str__(self) -> str:
        icon = "❌" if self.severity == "error" else "⚠️ "
        return f"{icon} [{self.unit_id}] {self.field}: {self.message}"


@dataclass
class ValidationResult:
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def errors(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def add_error(self, unit_id: str, field: str, message: str) -> None:
        self.issues.append(ValidationIssue(unit_id, field, "error", message))

    def add_warning(self, unit_id: str, field: str, message: str) -> None:
        self.issues.append(ValidationIssue(unit_id, field, "warning", message))

    def print_report(self) -> None:
        if not self.issues:
            print("✅ Валидация пройдена — проблем не найдено.")
            return

        if self.errors:
            print(f"\n❌ Ошибок: {len(self.errors)}")
            for issue in self.errors:
                print(f"  {issue}")

        if self.warnings:
            print(f"\n⚠️  Предупреждений: {len(self.warnings)}")
            for issue in self.warnings:
                print(f"  {issue}")

        print()
        if self.is_valid:
            print("✅ Критических ошибок нет (есть предупреждения).")
        else:
            print(f"❌ Валидация не пройдена: {len(self.errors)} ошибок.")


_GENERAL_NAMES = {
    "алгоритм", "буфер", "данные", "задача", "интервью", "компонент", "метод",
    "паттерн", "поиск", "программа", "процесс", "сервис", "система", "сортировка",
    "структура данных", "технология", "шаблон", "algorithm", "component", "data",
    "data structure", "method", "pattern", "search", "service", "system",
}


def _validate_names(result, unit, uid):
    seen = {normalize_title(unit.title): "title"}
    for field in ("aliases", "abbreviations"):
        for name in getattr(unit, field):
            key = normalize_title(name)
            if not key or not any(char.isalpha() for char in key):
                result.add_error(uid, field, "Пустое терминологическое значение.")
            elif key in seen:
                result.add_warning(uid, field, f"'{name}' повторяет значение поля {seen[key]}.")
            elif key in _GENERAL_NAMES:
                result.add_warning(uid, field, f"'{name}' выглядит слишком общим обозначением.")
            seen.setdefault(key, field)


def validate_unit(unit: KnowledgeUnit) -> ValidationResult:
    result = ValidationResult()
    uid = unit.id or unit.file_path

    if not unit.id:
        result.add_error(uid, "id", "Поле не заполнено.")
    elif not ID_PATTERN.match(unit.id):
        result.add_error(
            uid, "id",
            f"Неверный формат '{unit.id}'. Ожидается: ДОМЕН-КАТЕГОРИЯ-НН "
            f"(например CS-CONCEPT-017)."
        )

    if not unit.title:
        result.add_error(uid, "title", "Поле не заполнено.")
    elif len(unit.title) < 3:
        result.add_warning(uid, "title", "Слишком короткое название.")

    _validate_names(result, unit, uid)

    if unit.domain not in VALID_DOMAINS:
        result.add_error(
            uid, "domain",
            f"Недопустимое значение '{unit.domain}'. "
            f"Допустимые: {sorted(VALID_DOMAINS)}."
        )

    if unit.category not in VALID_CATEGORIES:
        result.add_error(
            uid, "category",
            f"Недопустимое значение '{unit.category}'. "
            f"Допустимые: {sorted(VALID_CATEGORIES)}."
        )

    if unit.difficulty not in VALID_DIFFICULTIES:
        result.add_error(
            uid, "difficulty",
            f"Недопустимое значение '{unit.difficulty}'. "
            f"Допустимые: {sorted(VALID_DIFFICULTIES)}."
        )

    if unit.frequency and unit.frequency not in VALID_FREQUENCIES:
        result.add_warning(
            uid, "frequency",
            f"Недопустимое значение '{unit.frequency}'. "
            f"Допустимые: {sorted(VALID_FREQUENCIES - {''})}."
        )

    if unit.status not in VALID_STATUSES:
        result.add_warning(
            uid, "status",
            f"Недопустимое значение '{unit.status}'. "
            f"Допустимые: {sorted(VALID_STATUSES)}."
        )

    for role in unit.roles:
        if role not in VALID_ROLES:
            result.add_warning(
                uid, "roles",
                f"Неизвестная роль '{role}'. "
                f"Допустимые: {sorted(VALID_ROLES)}."
            )

    for stage in unit.interview_stage:
        if stage not in VALID_INTERVIEW_STAGES:
            result.add_warning(
                uid, "interview_stage",
                f"Неизвестный этап '{stage}'. "
                f"Допустимые: {sorted(VALID_INTERVIEW_STAGES)}."
            )

    if not unit.content:
        result.add_warning(uid, "content", "Тело документа пустое (заглушка).")
    elif len(unit.content.strip()) < 50:
        result.add_warning(uid, "content", "Тело документа очень короткое (< 50 символов).")

    if not unit.sources:
        result.add_warning(uid, "sources", "Источники не указаны.")

    return result


def validate_all(units: list[KnowledgeUnit]) -> ValidationResult:
    result = ValidationResult()

    id_to_units: dict[str, list[KnowledgeUnit]] = defaultdict(list)
    for unit in units:
        id_to_units[unit.id].append(unit)

    all_ids = set(id_to_units.keys())
    names = title_index(units).names

    for unit in units:
        uid = unit.id or unit.file_path

        unit_result = validate_unit(unit)
        result.issues.extend(unit_result.issues)

        title_key = normalize_title(unit.title)
        if duplicates := names["title"].get(title_key, set()) - {uid}:
            result.add_warning(uid, "title", f"Название совпадает с {', '.join(sorted(duplicates))}.")

        for field in ("aliases", "abbreviations"):
            for name in getattr(unit, field):
                key = normalize_title(name)
                if titles := names["title"].get(key, set()) - {uid}:
                    result.add_warning(uid, field, f"'{name}' совпадает с названием {', '.join(sorted(titles))}.")
                if aliases := (names["alias"].get(key, set()) | names["abbreviation"].get(key, set())) - {uid}:
                    result.add_warning(uid, field, f"Неоднозначное обозначение '{name}': {', '.join(sorted(aliases | {uid}))}.")

        if len(id_to_units[unit.id]) > 1:
            paths = [u.file_path for u in id_to_units[unit.id]]
            result.add_error(
                uid, "id",
                f"Дублирующийся ID. Встречается в файлах: {paths}."
            )

        for ref_id in unit.related:
            if ref_id not in all_ids:
                result.add_warning(
                    uid, "related",
                    f"Ссылка на несуществующий ID '{ref_id}'."
                )

        for ref_id in unit.prerequisites:
            if ref_id not in all_ids:
                result.add_warning(
                    uid, "prerequisites",
                    f"Ссылка на несуществующий ID '{ref_id}'."
                )

    return result


def validate_file(file_path: str) -> ValidationResult:
    from .parser import parse_file, ParseError

    result = ValidationResult()
    try:
        unit = parse_file(file_path)
        return validate_unit(unit)
    except ParseError as e:
        result.add_error(file_path, "parse", str(e))
        return result
    except FileNotFoundError as e:
        result.add_error(file_path, "file", str(e))
        return result
