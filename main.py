"""
main.py

CLI-интерфейс базы знаний TechInterview.

Команды:
    search      — поиск по базе знаний
    validate    — валидация всей БЗ или одного файла
    registry    — генерация реестра идентификаторов
    new         — создание новой единицы знаний
    stats       — статистика по БЗ

Примеры:
    python3 main.py search --domain cs --difficulty junior
    python3 main.py search --tag arrays --text "binary search"
    python3 main.py validate
    python3 main.py validate --file cs/concepts/data_structures/cs_concept_hash_table.md
    python3 main.py registry
    python3 main.py new --title "Binary Search" --domain cs --category concept --difficulty junior
    python3 main.py stats
"""

import argparse
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Определяем корень БЗ — папка где лежат cs/, arch/, process/, global/
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
KB_ROOT = SCRIPT_DIR  # main.py лежит рядом с cs/, arch/ и т.д.


def _load_units(skip_errors: bool = True):
    """Загружает все единицы знаний из БЗ."""
    from kb.parser import parse_directory

    # Ищем только в папках доменов БЗ, не трогая venv и системные папки
    KB_DOMAINS = ["cs", "arch", "process", "global", "_meta"]
    units = []
    for domain_dir in KB_DOMAINS:
        domain_path = KB_ROOT / domain_dir
        if domain_path.is_dir():
            domain_units = parse_directory(domain_path, skip_errors=skip_errors)
            units.extend(domain_units)

    if not units:
        print("⚠️  Единицы знаний не найдены. Проверь путь к БЗ.")
    return units


# ---------------------------------------------------------------------------
# Команда: search
# ---------------------------------------------------------------------------

def cmd_search(args) -> None:
    """Поиск по базе знаний."""
    from kb.search import SearchQuery, search, print_results

    units = _load_units()
    if not units:
        return

    query = SearchQuery(
        domain          = args.domain,
        category        = args.category,
        difficulty      = args.difficulty,
        role            = args.role,
        interview_stage = args.stage,
        tags            = args.tag or [],
        text            = args.text,
        status          = args.status,
        frequency       = args.frequency,
    )

    results = search(units, query)
    print_results(results, verbose=args.verbose)


# ---------------------------------------------------------------------------
# Команда: validate
# ---------------------------------------------------------------------------

def cmd_validate(args) -> None:
    """Валидация БЗ или отдельного файла."""
    from kb.validator import validate_all, validate_file

    if args.file:
        # Валидация одного файла
        print(f"🔍 Валидация файла: {args.file}\n")
        result = validate_file(args.file)
        result.print_report()
        sys.exit(0 if result.is_valid else 1)
    else:
        # Валидация всей БЗ
        units = _load_units(skip_errors=True)
        if not units:
            return
        print(f"🔍 Валидация БЗ: {len(units)} единиц знаний...\n")
        result = validate_all(units)
        result.print_report()
        sys.exit(0 if result.is_valid else 1)


# ---------------------------------------------------------------------------
# Команда: registry
# ---------------------------------------------------------------------------

def cmd_registry(args) -> None:
    """Генерация реестра идентификаторов."""
    from kb.registry import generate_registry

    units = _load_units()
    if not units:
        return

    output = args.output or str(KB_ROOT / "_meta" / "id_registry.md")
    registry = generate_registry(units, output)
    registry.print_stats()


# ---------------------------------------------------------------------------
# Команда: new
# ---------------------------------------------------------------------------

def cmd_new(args) -> None:
    """Создание новой единицы знаний."""
    from kb.generator import generate_unit, list_templates
    from kb.registry import Registry

    # Если запрошен список шаблонов
    if args.list_templates:
        list_templates()
        return

    # Проверяем обязательные аргументы
    required = ["title", "domain", "category", "difficulty"]
    missing = [f"--{r}" for r in required if not getattr(args, r, None)]
    if missing:
        print(f"❌ Не указаны обязательные параметры: {', '.join(missing)}")
        print("   Используй --list-templates чтобы увидеть доступные категории.")
        sys.exit(1)

    # Строим реестр для генерации ID
    units = _load_units(skip_errors=True)
    registry = Registry.build(units) if units else None

    author = args.author or "Инженер знаний"

    path, _ = generate_unit(
        title      = args.title,
        domain     = args.domain,
        category   = args.category,
        difficulty = args.difficulty,
        author     = author,
        registry   = registry,
        root_dir   = KB_ROOT,
        dry_run    = args.dry_run,
    )

    if args.dry_run:
        print(f"🔍 Dry run — файл не создан: {path}")


# ---------------------------------------------------------------------------
# Команда: stats
# ---------------------------------------------------------------------------

def cmd_stats(args) -> None:
    """Статистика по базе знаний."""
    from kb.parser import summary
    from kb.registry import Registry
    from kb.validator import validate_all

    units = _load_units()
    if not units:
        return

    # Общая статистика
    summary(units)

    # Статистика реестра
    print()
    registry = Registry.build(units)
    registry.print_stats()

    # Краткий отчёт по валидации
    if args.validate:
        print()
        print("🔍 Запуск валидации...")
        result = validate_all(units)
        print(f"   Ошибок:         {len(result.errors)}")
        print(f"   Предупреждений: {len(result.warnings)}")
        if result.is_valid:
            print("   ✅ Критических ошибок нет.")
        else:
            print("   ❌ Есть критические ошибки. Запусти validate для деталей.")


# ---------------------------------------------------------------------------
# Парсер аргументов
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="CLI для работы с базой знаний TechInterview",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры:
  python3 main.py search --domain cs --difficulty junior
  python3 main.py search --tag arrays --text "binary search" --verbose
  python3 main.py validate
  python3 main.py validate --file cs/concepts/data_structures/cs_concept_hash_table.md
  python3 main.py registry
  python3 main.py new --title "Binary Search" --domain cs --category concept --difficulty junior
  python3 main.py new --list-templates
  python3 main.py stats
  python3 main.py stats --validate
        """,
    )

    subparsers = parser.add_subparsers(dest="command", metavar="КОМАНДА")
    subparsers.required = True

    # ------------------------------------------------------------------
    # search
    # ------------------------------------------------------------------
    p_search = subparsers.add_parser(
        "search",
        help="Поиск по базе знаний",
        description="Поиск единиц знаний по фильтрам и тексту.",
    )
    p_search.add_argument("--domain",     help="Домен: cs | arch | process | global")
    p_search.add_argument("--category",   help="Категория: concept | problem | sysdesign | ...")
    p_search.add_argument("--difficulty", help="Сложность: junior | middle | senior | staff")
    p_search.add_argument("--role",       help="Роль: backend | frontend | fullstack | ...")
    p_search.add_argument("--stage",      help="Этап: coding | behavioral | system_design | ...")
    p_search.add_argument("--tag",        action="append", metavar="ТЕГ",
                          help="Тег (можно указать несколько: --tag arrays --tag must_know)")
    p_search.add_argument("--text",       help="Полнотекстовый поиск")
    p_search.add_argument("--status",     help="Статус: draft | review | approved")
    p_search.add_argument("--frequency",  help="Частота: high | medium | low")
    p_search.add_argument("--verbose", "-v", action="store_true",
                          help="Подробный вывод (score, matched)")
    p_search.set_defaults(func=cmd_search)

    # ------------------------------------------------------------------
    # validate
    # ------------------------------------------------------------------
    p_validate = subparsers.add_parser(
        "validate",
        help="Валидация БЗ",
        description="Проверка корректности метаданных и перекрёстных ссылок.",
    )
    p_validate.add_argument(
        "--file", "-f",
        help="Путь к конкретному файлу (если не указан — валидируется вся БЗ)"
    )
    p_validate.set_defaults(func=cmd_validate)

    # ------------------------------------------------------------------
    # registry
    # ------------------------------------------------------------------
    p_registry = subparsers.add_parser(
        "registry",
        help="Генерация реестра идентификаторов",
        description="Генерирует _meta/id_registry.md со всеми ID базы знаний.",
    )
    p_registry.add_argument(
        "--output", "-o",
        help="Путь к выходному файлу (по умолчанию: _meta/id_registry.md)"
    )
    p_registry.set_defaults(func=cmd_registry)

    # ------------------------------------------------------------------
    # new
    # ------------------------------------------------------------------
    p_new = subparsers.add_parser(
        "new",
        help="Создание новой единицы знаний",
        description="Создаёт .md файл по шаблону с заполненным фронтматтером.",
    )
    p_new.add_argument("--title",       help="Название единицы знаний")
    p_new.add_argument("--domain",      help="Домен: cs | arch | process | global")
    p_new.add_argument("--category",    help="Категория: concept | problem | sysdesign | ...")
    p_new.add_argument("--difficulty",  help="Сложность: junior | middle | senior | staff")
    p_new.add_argument("--author",      help="Имя автора (по умолчанию: Инженер знаний)")
    p_new.add_argument("--dry-run",     action="store_true",
                       help="Показать что будет создано без реального создания файла")
    p_new.add_argument("--list-templates", action="store_true",
                       help="Показать список доступных шаблонов")
    p_new.set_defaults(func=cmd_new)

    # ------------------------------------------------------------------
    # stats
    # ------------------------------------------------------------------
    p_stats = subparsers.add_parser(
        "stats",
        help="Статистика по БЗ",
        description="Выводит статистику по всем единицам знаний.",
    )
    p_stats.add_argument(
        "--validate", action="store_true",
        help="Также запустить валидацию и показать краткий отчёт"
    )
    p_stats.set_defaults(func=cmd_stats)

    return parser


# ---------------------------------------------------------------------------
# Точка входа
# ---------------------------------------------------------------------------

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
