# База знаний TechInterview

CLI-инструмент для управления базой знаний по подготовке к техническим собеседованиям в сфере IT.

---

## Содержание

- [Установка](#установка)
- [Структура проекта](#структура-проекта)
- [Формат файлов](#формат-файлов)
- [Команды CLI](#команды-cli)
  - [search — поиск](#search--поиск)
  - [validate — валидация](#validate--валидация)
  - [registry — реестр](#registry--реестр)
  - [new — создание](#new--создание)
  - [stats — статистика](#stats--статистика)
- [Типичные сценарии](#типичные-сценарии)
- [Устранение проблем](#устранение-проблем)

---

## Установка

### Требования

- Python 3.10+
- Git

### Шаг 1 — Клонирование репозитория

```bash
git clone https://github.com/dozhdik/techinterview_knowledge_base.git
cd techinterview_knowledge_base
```

### Шаг 2 — Установка зависимостей

```bash
pip3 install pyyaml pytest --break-system-packages
```

### Шаг 3 — Проверка установки

```bash
python3 main.py --help
```

Ожидаемый вывод:

```
usage: main.py [-h] КОМАНДА ...

CLI для работы с базой знаний TechInterview

positional arguments:
  КОМАНДА
    search    Поиск по базе знаний
    validate  Валидация БЗ
    registry  Генерация реестра идентификаторов
    new       Создание новой единицы знаний
    stats     Статистика по БЗ
```

### Шаг 4 — Запуск тестов

```bash
python3 -m pytest tests/ -v
```

Ожидаемый результат: `177 passed`

---

## Структура проекта

```
techinterview_knowledge_base/
├── main.py              # точка входа CLI
├── requirements.txt     # зависимости
├── kb/                  # Python-пакет
│   ├── __init__.py
│   ├── parser.py        # чтение .md файлов
│   ├── validator.py     # валидация метаданных
│   ├── search.py        # поиск по БЗ
│   ├── registry.py      # реестр идентификаторов
│   └── generator.py     # генерация новых файлов
├── tests/               # 177 тестов
├── cs/                  # ПО «Фундаментальные основы CS»
├── arch/                # ПО «Архитектура систем»
├── process/             # ПО «Процесс собеседования»
├── global/              # Глобальная предметная область
└── _meta/               # Служебные файлы
```

---

## Формат файлов

Каждая единица знаний — отдельный `.md` файл с YAML-фронтматтером в начале.

### Обязательные поля

| Поле         | Допустимые значения                              |
|--------------|--------------------------------------------------|
| `id`         | Формат `ДОМЕН-КАТЕГОРИЯ-НН`, например `CS-CONCEPT-017` |
| `title`      | Название единицы знаний                          |
| `domain`     | `cs` \| `arch` \| `process` \| `global`          |
| `category`   | `concept` \| `problem` \| `sysdesign` \| `behavioral` \| ... |
| `difficulty` | `junior` \| `middle` \| `senior` \| `staff`      |

### Необязательные поля

| Поле             | Описание                                                       |
|------------------|----------------------------------------------------------------|
| `tags`           | Список тегов                                                   |
| `roles`          | `backend` \| `frontend` \| `fullstack` \| `devops` \| `data_engineer` \| `mobile` \| `ml_engineer` \| `all_roles` |
| `interview_stage`| `coding` \| `behavioral` \| `system_design` \| `phone_screen` \| `take_home` \| `hr_screening` \| `offer` |
| `frequency`      | `high` \| `medium` \| `low`                                    |
| `related`        | Список ID связанных документов                                 |
| `prerequisites`  | Список ID документов-пререквизитов                             |
| `sources`        | Список источников                                              |
| `author`         | Имя автора                                                     |
| `status`         | `draft` \| `review` \| `approved`                             |

### Пример файла

```yaml
---
id: "CS-CONCEPT-017"
title: "Хеш-таблица (Hash Table)"
domain: "cs"
category: "concept"
tags:
  - hash_tables
  - must_know
difficulty: "junior"
roles:
  - "all_roles"
interview_stage:
  - "coding"
frequency: "high"
related:
  - "CS-CONCEPT-003"
sources:
  - "CLRS 4th Edition, Chapter 11"
author: "Инженер знаний №1"
status: "approved"
---

# Хеш-таблица (Hash Table)

## Определение
Структура данных, реализующая ассоциативный массив...
```

---

## Команды CLI

Все команды запускаются из корневой папки проекта:

```bash
python3 main.py <команда> [параметры]
```

Справка по любой команде:

```bash
python3 main.py <команда> --help
```

---

### search — поиск

Поиск единиц знаний по фильтрам и тексту. Результаты сортируются по релевантности.

```bash
python3 main.py search [параметры]
```

#### Параметры

| Параметр        | Описание                                                     |
|-----------------|--------------------------------------------------------------|
| `--domain`      | Домен: `cs` \| `arch` \| `process` \| `global`               |
| `--category`    | Категория: `concept` \| `problem` \| `sysdesign` \| ...       |
| `--difficulty`  | Сложность: `junior` \| `middle` \| `senior` \| `staff`        |
| `--role`        | Роль: `backend` \| `frontend` \| `fullstack` \| `devops` \| ... |
| `--stage`       | Этап: `coding` \| `behavioral` \| `system_design` \| ...     |
| `--tag`         | Тег (можно указать несколько — AND-логика)                   |
| `--text`        | Полнотекстовый поиск по заголовку, ID, тегам и содержимому   |
| `--status`      | Статус: `draft` \| `review` \| `approved`                    |
| `--frequency`   | Частота: `high` \| `medium` \| `low`                         |
| `--verbose`     | Подробный вывод: score и matched-поля                        |

#### Примеры

```bash
# Все CS-единицы для Junior
python3 main.py search --domain cs --difficulty junior

# Поиск по тексту
python3 main.py search --text "бинарное дерево"

# Несколько тегов (AND-логика — должны присутствовать оба)
python3 main.py search --tag arrays --tag must_know

# Задачи для backend на этапе coding
python3 main.py search --domain cs --category problem --role backend --stage coding

# Системный дизайн уровня middle с подробным выводом
python3 main.py search --domain arch --category sysdesign --difficulty middle --verbose

# Только утверждённые материалы
python3 main.py search --status approved --frequency high
```

---

### validate — валидация

Проверяет корректность метаданных и перекрёстных ссылок. Возвращает код выхода `1` при ошибках.

```bash
python3 main.py validate [--file ПУТЬ]
```

#### Параметры

| Параметр      | Описание                                                              |
|---------------|-----------------------------------------------------------------------|
| `--file / -f` | Путь к конкретному файлу. Если не указан — валидируется вся БЗ       |

#### Что проверяется

- Формат ID (`ДОМЕН-КАТЕГОРИЯ-НН`)
- Допустимые значения `domain`, `category`, `difficulty`, `frequency`, `status`
- Корректность `roles` и `interview_stage`
- Наличие источников и непустой контент (предупреждения)
- Уникальность ID во всей БЗ
- Корректность ссылок в `related` и `prerequisites`

#### Примеры

```bash
# Валидация всей БЗ
python3 main.py validate

# Валидация одного файла
python3 main.py validate --file cs/concepts/data_structures/cs_concept_hash_table.md
```

---

### registry — реестр

Генерирует файл `_meta/id_registry.md` со сводной таблицей всех единиц знаний.

```bash
python3 main.py registry [--output ПУТЬ]
```

#### Параметры

| Параметр        | Описание                                                     |
|-----------------|--------------------------------------------------------------|
| `--output / -o` | Путь к выходному файлу. По умолчанию: `_meta/id_registry.md`|

#### Примеры

```bash
# Генерация в папку по умолчанию
python3 main.py registry

# Сохранение в другое место
python3 main.py registry --output docs/registry.md
```

---

### new — создание

Создаёт новый `.md` файл по шаблону. Автоматически генерирует ID и кладёт файл в правильную папку.

```bash
python3 main.py new --title НАЗВАНИЕ --domain ДОМЕН --category КАТЕГОРИЯ --difficulty УРОВЕНЬ [параметры]
```

#### Параметры

| Параметр            | Описание                                                     |
|---------------------|--------------------------------------------------------------|
| `--title`           | Название новой единицы знаний (обязательно)                  |
| `--domain`          | Домен: `cs` \| `arch` \| `process` \| `global` (обязательно)|
| `--category`        | Категория (обязательно). Список: `--list-templates`          |
| `--difficulty`      | Уровень: `junior` \| `middle` \| `senior` \| `staff` (обязательно) |
| `--author`          | Имя автора. По умолчанию: «Инженер знаний»                  |
| `--dry-run`         | Показать результат без создания файла                        |
| `--list-templates`  | Показать список всех доступных шаблонов                      |

#### Список шаблонов

```bash
python3 main.py new --list-templates
```

| Категория    | Куда создаётся файл          |
|--------------|------------------------------|
| `concept`    | `cs/concepts/`               |
| `problem`    | `cs/problems/`               |
| `pattern`    | `cs/patterns/`               |
| `cheatsheet` | `cs/cheatsheets/`            |
| `pitfall`    | `*/pitfalls/`                |
| `component`  | `arch/components/`           |
| `sysdesign`  | `arch/system_design/`        |
| `tradeoff`   | `arch/tradeoffs/`            |
| `designpat`  | `arch/design_patterns/`      |
| `behavioral` | `process/behavioral/`        |
| `stage`      | `process/stages/`            |
| `strategy`   | `process/strategies/`        |
| `framework`  | `process/frameworks/`        |
| `checklist`  | `*/checklists/`              |
| `glossary`   | `*/glossary/`                |

#### Примеры

```bash
# Создать карточку концепции
python3 main.py new --title "Binary Search" --domain cs \
                    --category concept --difficulty junior \
                    --author "Инженер знаний №1"

# Создать разбор системного дизайна
python3 main.py new --title "Twitter Feed" --domain arch \
                    --category sysdesign --difficulty senior

# Посмотреть что будет создано без записи файла
python3 main.py new --title "Hash Table" --domain cs \
                    --category concept --difficulty junior --dry-run
```

> **После создания файла:** откройте его, заполните секции с `<!-- TODO: ... -->`,
> добавьте теги и источники, смените `status: "draft"` на `"review"`,
> затем запустите `python3 main.py validate`.

---

### stats — статистика

Выводит сводную статистику по всем единицам знаний.

```bash
python3 main.py stats [--validate]
```

#### Параметры

| Параметр     | Описание                                           |
|--------------|----------------------------------------------------|
| `--validate` | Также запустить валидацию и показать краткий отчёт |

#### Примеры

```bash
# Базовая статистика
python3 main.py stats

# Статистика + краткая валидация
python3 main.py stats --validate
```

---

## Типичные сценарии

### Добавить новую единицу знаний

```bash
# 1. Создать файл по шаблону
python3 main.py new --title "Sliding Window" --domain cs \
                    --category pattern --difficulty junior

# 2. Заполнить содержимое
nano cs/patterns/cs_pattern_sliding_window.md

# 3. Проверить корректность
python3 main.py validate --file cs/patterns/cs_pattern_sliding_window.md

# 4. Обновить реестр
python3 main.py registry
```

### Проверить состояние всей БЗ

```bash
python3 main.py stats --validate
```

### Найти материалы для подготовки

```bash
# Все задачи уровня Junior для Backend
python3 main.py search --domain cs --category problem \
                       --difficulty junior --role backend

# Must-know темы для coding interview
python3 main.py search --tag must_know --stage coding

# Всё по динамическому программированию
python3 main.py search --text "dynamic programming" --verbose
```

---

## Устранение проблем

| Проблема | Решение |
|----------|---------|
| `No module named pytest` | `pip3 install pytest pyyaml --break-system-packages` |
| `Команда python не найдена` | Используйте `python3` вместо `python` |
| `externally-managed-environment` | Добавьте `--break-system-packages` к команде pip3 |
| `Единицы знаний не найдены` | Убедитесь что запускаете `main.py` из корня проекта, где лежат `cs/`, `arch/`, `process/` |
| `YAML-фронтматтер не найден` | Файл должен начинаться точно с `---` без пробелов перед |
| `Отсутствуют обязательные поля` | Проверьте что `id`, `title`, `domain`, `category`, `difficulty` присутствуют в фронтматтере |
| `Дублирующийся ID` | Запустите `python3 main.py registry` для поиска дублей |



Contributors: Alexander, Mikalay, Pavlo
