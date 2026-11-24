import argparse
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
KB_ROOT = SCRIPT_DIR


def _load_units(skip_errors: bool = True):
    from kb.parser import parse_directory

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


def cmd_search(args) -> None:
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


def cmd_validate(args) -> None:
    from kb.validator import validate_all, validate_file

    if args.file:
        print(f"🔍 Валидация файла: {args.file}\n")
        result = validate_file(args.file)
        result.print_report()
        sys.exit(0 if result.is_valid else 1)
    else:
        units = _load_units(skip_errors=True)
        if not units:
            return
        print(f"🔍 Валидация БЗ: {len(units)} единиц знаний...\n")
        result = validate_all(units)
        result.print_report()
        sys.exit(0 if result.is_valid else 1)


def cmd_registry(args) -> None:
    from kb.registry import generate_registry

    units = _load_units()
    if not units:
        return

    output = args.output or str(KB_ROOT / "_meta" / "id_registry.md")
    registry = generate_registry(units, output)
    registry.print_stats()


def cmd_new(args) -> None:
    from kb.generator import generate_unit, list_templates
    from kb.registry import Registry

    if args.list_templates:
        list_templates()
        return

    required = ["title", "domain", "category", "difficulty"]
    missing = [f"--{r}" for r in required if not getattr(args, r, None)]
    if missing:
        print(f"❌ Не указаны обязательные параметры: {', '.join(missing)}")
        print("   Используй --list-templates чтобы увидеть доступные категории.")
        sys.exit(1)

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


def cmd_stats(args) -> None:
    from kb.parser import summary
    from kb.registry import Registry
    from kb.validator import validate_all

    units = _load_units()
    if not units:
        return

    summary(units)

    print()
    registry = Registry.build(units)
    registry.print_stats()

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


def cmd_vector_build(args) -> None:
    from kb.vector_store import VectorIndexError, build_index

    try:
        result = build_index(KB_ROOT, args.index, args.backend, args.model, args.max_chars)
    except (VectorIndexError, ValueError) as exc:
        print(f"Ошибка построения индекса: {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"Индекс: {result['path']}")
    print(f"Backend: {result['backend']} ({result['model']})")
    print(f"Карточек: {result['cards']}, фрагментов: {result['chunks']}")
    print(f"Обновлено фрагментов: {result['updated']}, удалено: {result['removed']}")


def cmd_vector_status(args) -> None:
    from kb.vector_store import VectorIndexError, index_status

    try:
        result = index_status(KB_ROOT, args.index)
    except VectorIndexError as exc:
        print(f"Ошибка индекса: {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"Индекс: {result['path']}")
    print(f"Backend: {result['backend']} ({result['model']})")
    print(f"Размерность: {result['dimensions']}")
    print(f"Карточек: {result['cards']}, фрагментов: {result['chunks']}")
    print(f"Актуальность: {'актуален' if result['fresh'] else 'требует обновления'}")


def cmd_vector_search(args) -> None:
    from kb.vector_store import VectorIndexError, search_index

    try:
        results = search_index(KB_ROOT, args.question, args.index,
                               args.limit, args.domain, args.min_score)
    except VectorIndexError as exc:
        print(f"Ошибка поиска: {exc}", file=sys.stderr)
        sys.exit(1)
    if not results:
        print("Совпадений нет.")
        return
    for hit in results:
        print(f"{hit.score:.3f}  {hit.chunk_id}  {hit.title}")
        print(f"  {hit.source_path}")
        print(f"  {hit.text[:220].replace(chr(10), ' ')}")


def cmd_passage_build(args) -> None:
    import json

    from kb.passage_index import build
    print(json.dumps(build(KB_ROOT), ensure_ascii=False, indent=2))


def cmd_search_diagnose(args) -> None:
    import json
    from time import perf_counter

    from kb.retrieval import configured_reranker, get_engine
    started = perf_counter()
    engine = get_engine(KB_ROOT)
    ready = perf_counter()
    answer, debug = engine.ask(args.question, _load_units(), domain=args.domain,
                               links=args.links, reranker=configured_reranker())
    debug["answer"] = answer.answer if answer else None
    debug["seconds"]["startup"] = ready - started
    debug["seconds"]["total"] = perf_counter() - started
    print(json.dumps(debug, ensure_ascii=False, indent=2))


def cmd_search_benchmark(args) -> None:
    import json

    from kb.search_benchmark import evaluate
    report = evaluate(KB_ROOT, _load_units(), args.cases, args.split, args.method,
                      args.output, args.reranker)
    print(json.dumps({k: report[k] for k in ("overall", "warm", "by_domain", "by_type")},
                     ensure_ascii=False, indent=2))


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

    p_vector_build = subparsers.add_parser(
        "vector-build", help="Построить или обновить локальный векторный индекс"
    )
    p_vector_build.add_argument("--index", help="Путь к SQLite-индексу")
    p_vector_build.add_argument("--backend", choices=("hash", "sentence-transformers"),
                                default="hash", help="Способ получения векторов")
    p_vector_build.add_argument("--model", help="Имя модели Sentence Transformers")
    p_vector_build.add_argument("--max-chars", type=int, default=1400,
                                help="Максимальный размер фрагмента в символах")
    p_vector_build.set_defaults(func=cmd_vector_build)

    p_vector_search = subparsers.add_parser(
        "vector-search", help="Найти фрагменты гибридным поиском"
    )
    p_vector_search.add_argument("question", help="Поисковый вопрос")
    p_vector_search.add_argument("--index", help="Путь к SQLite-индексу")
    p_vector_search.add_argument("--limit", type=int, default=5)
    p_vector_search.add_argument("--domain", choices=("cs", "arch", "process", "global"))
    p_vector_search.add_argument("--min-score", type=float, default=0.0,
                                 help="Минимальное косинусное сходство фрагмента")
    p_vector_search.set_defaults(func=cmd_vector_search)

    p_vector_status = subparsers.add_parser(
        "vector-status", help="Проверить состояние векторного индекса"
    )
    p_vector_status.add_argument("--index", help="Путь к SQLite-индексу")
    p_vector_status.set_defaults(func=cmd_vector_status)

    build_passages = subparsers.add_parser("passage-build", help="Обновить структурный индекс Markdown")
    build_passages.set_defaults(func=cmd_passage_build)

    diagnose = subparsers.add_parser("search-diagnose", help="Показать этапы гибридного поиска")
    diagnose.add_argument("question")
    diagnose.add_argument("--domain", choices=("cs", "arch", "process", "global"))
    diagnose.add_argument("--links", action="store_true")
    diagnose.set_defaults(func=cmd_search_diagnose)

    benchmark = subparsers.add_parser("search-benchmark", help="Оценить поиск по размеченным запросам")
    benchmark.add_argument("--cases", type=Path, default=KB_ROOT / "evaluation/search_cases.json")
    benchmark.add_argument("--split", choices=("development", "test", "all"), default="test")
    benchmark.add_argument("--method", choices=("legacy", "bm25", "dense", "plain_rrf", "hybrid", "links",
                                              "cross_encoder"), default="hybrid")
    benchmark.add_argument("--reranker", help="Локальный каталог модели Cross-Encoder")
    benchmark.add_argument("--output", type=Path, required=True)
    benchmark.set_defaults(func=cmd_search_benchmark)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
