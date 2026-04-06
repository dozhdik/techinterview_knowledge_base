# Contributing — Правила добавления и редактирования единиц знаний

Это руководство описывает как правильно добавлять новые и редактировать существующие единицы знаний в базе знаний TechInterview.

---

## Содержание

- [Кто за что отвечает](#кто-за-что-отвечает)
- [Перед началом работы](#перед-началом-работы)
- [Добавление новой единицы знаний](#добавление-новой-единицы-знаний)
- [Редактирование существующей единицы](#редактирование-существующей-единицы)
- [Правила оформления метаданных](#правила-оформления-метаданных)
- [Правила написания контента](#правила-написания-контента)
- [Система статусов](#система-статусов)
- [Правила именования файлов](#правила-именования-файлов)
- [Перекрёстные ссылки](#перекрёстные-ссылки)
- [Контроль качества](#контроль-качества)
- [Частые ошибки](#частые-ошибки)

---

## Кто за что отвечает

| Роль | Зона ответственности |
|------|----------------------|
| Инженер знаний №1 | Предметная область `cs/` — фундаментальные основы Computer Science |
| Инженер знаний №2 | Предметная область `arch/` — проектирование и архитектура |
| Инженер знаний №3 | Предметная область `process/` — процесс собеседования и soft skills |
| Все участники совместно | Папка `global/` — глобальная предметная область и интеграция |

---

## Перед началом работы

### 1. Убедись что репозиторий актуален

```bash
git pull origin main
```

### 2. Проверь текущее состояние БЗ

```bash
python3 main.py stats --validate
```

### 3. Посмотри реестр чтобы не создать дублирующийся ID

```bash
python3 main.py registry
cat _meta/id_registry.md
```

---

## Добавление новой единицы знаний

### Шаг 1 — Создать файл по шаблону

Используй команду `new` — она автоматически создаст файл в правильной папке с нужным ID:

```bash
python3 main.py new \
  --title "Название единицы" \
  --domain cs \
  --category concept \
  --difficulty junior \
  --author "Инженер знаний №1"
```

Список всех доступных категорий:

```bash
python3 main.py new --list-templates
```

### Шаг 2 — Заполнить метаданные

Открой созданный файл и заполни YAML-фронтматтер:

```bash
nano cs/concepts/cs_concept_название.md
```

Обязательно укажи:
- корректные `tags` (убери заглушку `# TODO`)
- `roles` — для каких ролей актуальна эта единица
- `interview_stage` — на каком этапе спрашивают
- `frequency` — насколько часто встречается на собеседованиях
- `sources` — минимум один авторитетный источник
- `related` — ID связанных единиц (можно оставить пустым поначалу)

### Шаг 3 — Написать содержимое

Заполни все секции тела документа по шаблону. Секции с `<!-- TODO: ... -->` — обязательны к заполнению. Не оставляй файл с незаполненными TODO.

### Шаг 4 — Сменить статус

После заполнения смени `status: "draft"` на `status: "review"`:

```yaml
status: "review"
```

### Шаг 5 — Проверить файл

```bash
python3 main.py validate --file путь/к/файлу.md
```

Исправь все ошибки. Предупреждения тоже желательно устранить.

### Шаг 6 — Обновить реестр

```bash
python3 main.py registry
```

### Шаг 7 — Закоммитить изменения

```bash
git add .
git commit -m "feat(cs): добавлена карточка концепции Binary Search [CS-CONCEPT-018]"
git push origin main
```

---

## Редактирование существующей единицы

### Когда можно редактировать чужую единицу

- Исправление опечаток и грамматических ошибок
- Добавление перекрёстных ссылок (`related`, `prerequisites`)
- Обновление источников
- Исправление технических неточностей (с комментарием в коммите)

### Когда нужно согласование

- Изменение основного содержимого
- Изменение уровня сложности (`difficulty`)
- Изменение категории (`category`)
- Удаление разделов

### Порядок редактирования

```bash
# 1. Открой файл
nano путь/к/файлу.md

# 2. Внеси изменения

# 3. Обнови дату в метаданных
# date_updated: "YYYY-MM-DD"  ← поставь сегодняшнюю дату

# 4. Проверь
python3 main.py validate --file путь/к/файлу.md

# 5. Закоммить
git add путь/к/файлу.md
git commit -m "fix(cs): исправлена сложность алгоритма в CS-CONCEPT-017"
```

---

## Правила оформления метаданных

### Формат ID

```
ДОМЕН-КАТЕГОРИЯ-НН
```

| Домен | Код |
|-------|-----|
| Computer Science | `CS` |
| Архитектура | `ARCH` |
| Процесс собеседования | `PROC` |
| Глобальная ПО | `GLB` |

Примеры корректных ID:
```
CS-CONCEPT-017
CS-PROBLEM-008
ARCH-SYSDESIGN-001
ARCH-TRADEOFF-003
PROC-BEHAVIORAL-012
GLB-PROFILE-002
```

Примеры **некорректных** ID:
```
cs-concept-17       ← строчные буквы
CS-CONCEPT-17       ← номер без ведущего нуля
CS_CONCEPT_017      ← подчёркивания вместо дефисов
concept-017         ← нет домена
```

### Обязательные поля

Все пять полей обязательны в каждом файле:

```yaml
id: "CS-CONCEPT-017"
title: "Хеш-таблица (Hash Table)"
domain: "cs"
category: "concept"
difficulty: "junior"
```

### Допустимые значения полей

**domain:**
```
cs | arch | process | global
```

**category:**
```
concept | problem | pattern | question | cheatsheet | pitfall
component | designpat | sysdesign | tradeoff | checklist
stage | behavioral | strategy | company | softskill
framework | glossary | cross | profile | matrix | trajectory | onto
```

**difficulty:**
```
junior | middle | senior | staff
```

**roles:**
```
backend | frontend | fullstack | devops
data_engineer | mobile | ml_engineer | all_roles
```

**interview_stage:**
```
phone_screen | coding | system_design
behavioral | take_home | team_match | offer | hr_screening
```

**frequency:**
```
high | medium | low
```

**status:**
```
draft | review | approved
```

### Теги

Используй теги из установленной таксономии (`_meta/tag_taxonomy.md`). Не придумывай произвольные теги — это ломает поиск. Основные группы тегов:

```yaml
# Техническая тема
tags:
  - arrays
  - hash_tables
  - dynamic_programming
  - graphs
  - trees

# Приоритет
tags:
  - must_know
  - core
  - advanced
  - nice_to_have

# Частота
tags:
  - frequently_asked
  - occasionally_asked
  - rare_but_important
```

### Источники

Каждая единица знаний должна иметь минимум один источник. Приоритет источников:

1. Фундаментальные учебники (CLRS, Tanenbaum, Kleppmann и т.д.)
2. Официальная документация технологий
3. Engineering blogs крупных компаний (Google, Meta, Netflix, Uber)
4. Рецензируемые ресурсы (System Design Primer, NeetCode)

```yaml
# Правильно
sources:
  - "Cormen T.H. et al. Introduction to Algorithms (CLRS), 4th Edition, Chapter 11"
  - "Python Documentation. Built-in Types: dict. https://docs.python.org/3/..."

# Неправильно
sources:
  - "Интернет"
  - "Лекция"
```

---

## Правила написания контента

### Язык

- Основной язык — русский
- Технические термины пишутся на английском с русским пояснением при первом упоминании
- Примеры кода — псевдокод или Python

```markdown
# Правильно
Хеш-таблица (Hash Table) — структура данных...
Применяется паттерн Sliding Window (скользящее окно).

# Неправильно
Hash table — это структура данных...
```

### Примеры кода

Код пишется на Python как lingua franca. Исключение — если тема специфична для другого языка.

```python
# Хорошо: лаконично, с комментариями
def two_sum(nums: list[int], target: int) -> list[int]:
    seen = {}  # значение → индекс
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []
```

### Структура секций

Не пропускай секции из шаблона. Если секция не применима — напиши об этом явно:

```markdown
## Визуальное представление
Для данного алгоритма визуальное представление в виде ASCII-диаграммы не применимо.
Рекомендуется изучить анимацию на visualgo.net.
```

### Глубина детализации по уровням

Секция «Уровень по глубине» обязательна:

```markdown
## Уровень по глубине

- **Junior**: знать определение, average-case сложности, уметь использовать в задачах
- **Middle**: понимать устройство (chaining vs open addressing), load factor, rehashing
- **Senior**: знать конкурентные реализации, consistent hashing, выбирать с обоснованием
```

---

## Система статусов

| Статус | Значение | Кто устанавливает |
|--------|----------|-------------------|
| `draft` | Файл создан, контент не заполнен или заполнен частично | Автоматически при создании |
| `review` | Контент заполнен, ожидает проверки | Инженер знаний после заполнения |
| `approved` | Проверено, готово к использованию | Другой участник команды |

### Правило проверки

Единица переходит в `approved` только после проверки **другим** участником команды. Нельзя самому устанавливать `approved` для своих единиц.

```bash
# Проверить все единицы на review
python3 main.py search --status review
```

---

## Правила именования файлов

Формат имени файла:

```
{домен}_{категория}_{slug}.md
```

Где `slug` — название в snake_case на латинице:

```bash
# CS
cs_concept_hash_table.md
cs_problem_two_sum.md
cs_pattern_sliding_window.md

# Arch
arch_sysdesign_url_shortener.md
arch_component_load_balancer.md
arch_tradeoff_sql_vs_nosql.md

# Process
process_behavioral_tell_about_yourself.md
process_stage_coding_interview.md
process_framework_star.md
```

Команда `new` генерирует правильное имя автоматически.

**Нельзя:**
- Использовать кириллицу в именах файлов
- Использовать пробелы (только подчёркивания)
- Использовать заглавные буквы
- Менять имя файла после создания без обновления реестра

---

## Перекрёстные ссылки

### Формат ссылок

```yaml
related:
  - "CS-CONCEPT-003"   # Массив
  - "CS-PROBLEM-008"   # Two Sum

prerequisites:
  - "CS-CONCEPT-003"   # Массив
```

### Типы связей (указывай в комментарии)

| Тип | Описание | Пример |
|-----|----------|--------|
| `depends_on` | Зависит от | Dijkstra → Priority Queue |
| `extends` | Расширяет | BST → AVL Tree |
| `relates_to` | Тематически связан | Hash Table → Hash Function |
| `applied_in` | Применяется в | Hash Table → URL Shortener |
| `exemplifies` | Является примером | Two Sum → Two Pointers Pattern |
| `alternative_to` | Альтернативный подход | BFS → DFS |

```yaml
# Хорошо — с комментариями
related:
  - "CS-CONCEPT-018"   # Хеш-функция (depends_on)
  - "CS-CONCEPT-003"   # Массив (relates_to)
  - "CS-PROBLEM-008"   # Two Sum (applied_in)

# Плохо — непонятно зачем ссылка
related:
  - "CS-CONCEPT-018"
  - "CS-CONCEPT-003"
```

### Проверка ссылок

```bash
# Валидация проверит все ссылки автоматически
python3 main.py validate
```

---

## Контроль качества

### Перед каждым коммитом

```bash
# 1. Проверить изменённые файлы
python3 main.py validate --file путь/к/файлу.md

# 2. Проверить всю БЗ
python3 main.py validate

# 3. Обновить реестр
python3 main.py registry

# 4. Запустить тесты
python3 -m pytest tests/ -v
```

### Формат коммитов

```
тип(домен): краткое описание [ID]

feat(cs): добавлена карточка концепции Binary Search [CS-CONCEPT-018]
feat(arch): добавлен разбор URL Shortener [ARCH-SYSDESIGN-001]
feat(process): добавлен behavioral-вопрос Tell Me About Yourself [PROC-BEHAVIORAL-001]
fix(cs): исправлена временная сложность в Hash Table [CS-CONCEPT-017]
update(arch): обновлены источники в Load Balancer [ARCH-COMPONENT-001]
review(process): статус approved для STAR Method [PROC-FRAMEWORK-001]
```

Типы коммитов:

| Тип | Описание |
|-----|----------|
| `feat` | Новая единица знаний |
| `fix` | Исправление ошибки в существующей |
| `update` | Обновление содержимого или источников |
| `review` | Смена статуса после проверки |
| `refactor` | Переработка структуры без изменения смысла |

---

## Частые ошибки

### ❌ Неправильный формат ID

```yaml
# Неправильно
id: "cs-concept-017"     # строчные буквы
id: "CS-CONCEPT-17"      # нет ведущего нуля
id: "CS_CONCEPT_017"     # подчёркивания

# Правильно
id: "CS-CONCEPT-017"
```

### ❌ Неизвестное значение поля

```yaml
# Неправильно
domain: "computer_science"
difficulty: "easy"
status: "done"

# Правильно
domain: "cs"
difficulty: "junior"
status: "approved"
```

### ❌ Произвольные теги

```yaml
# Неправильно — тег не из таксономии
tags:
  - очень_важно
  - для_собеседования
  - хеш

# Правильно — теги из _meta/tag_taxonomy.md
tags:
  - hash_tables
  - must_know
  - core
```

### ❌ Ссылка на несуществующий ID

```yaml
# Неправильно — если CS-CONCEPT-999 не существует
related:
  - "CS-CONCEPT-999"
```

Проверяй ссылки через `python3 main.py validate`.

### ❌ Файл без источников

```yaml
# Неправильно
sources: []

# Правильно
sources:
  - "CLRS 4th Edition, Chapter 11: Hash Tables"
```

### ❌ Статус approved без проверки

Нельзя самостоятельно ставить `approved` своим единицам — только другой участник команды после проверки.

### ❌ Кириллица в имени файла

```bash
# Неправильно
cs_concept_хеш_таблица.md

# Правильно
cs_concept_hash_table.md
```
