# Гайд по использованию CLI в терминале

Полное руководство по всем командам базы знаний TechInterview с примерами использования.

---

## Содержание

- [Быстрый старт](#быстрый-старт)
- [Общие правила](#общие-правила)
- [search — поиск по БЗ](#search--поиск-по-бз)
- [validate — валидация](#validate--валидация)
- [registry — реестр ID](#registry--реестр-id)
- [new — создание единицы знаний](#new--создание-единицы-знаний)
- [stats — статистика](#stats--статистика)
- [Комбинирование команд](#комбинирование-команд)
- [Шпаргалка](#шпаргалка)

---

## Быстрый старт

```bash
# Перейди в папку проекта
cd ~/techinterview_knowledge_base

# Активируй окружение (если используешь venv)
source venv/bin/activate

# Убедись что всё работает
python3 main.py --help
```

---

## Общие правила

**Все команды запускаются из корневой папки проекта:**
```bash
# Правильно — ты находишься в корне
~/techinterview_knowledge_base$ python3 main.py search --domain cs

# Неправильно — ты в другой папке
~/$ python3 techinterview_knowledge_base/main.py search --domain cs
```

**Справка по любой команде:**
```bash
python3 main.py --help                # список всех команд
python3 main.py search --help         # справка по search
python3 main.py validate --help       # справка по validate
python3 main.py new --help            # справка по new
python3 main.py registry --help       # справка по registry
python3 main.py stats --help          # справка по stats
```

**Допустимые значения параметров:**

| Параметр        | Допустимые значения |
|-----------------|---------------------|
| `--domain`      | `cs` · `arch` · `process` · `global` |
| `--difficulty`  | `junior` · `middle` · `senior` · `staff` |
| `--status`      | `draft` · `review` · `approved` |
| `--frequency`   | `high` · `medium` · `low` |
| `--role`        | `backend` · `frontend` · `fullstack` · `devops` · `data_engineer` · `mobile` · `ml_engineer` · `all_roles` |
| `--stage`       | `coding` · `behavioral` · `system_design` · `phone_screen` · `take_home` · `hr_screening` · `offer` |

---

## search — поиск по БЗ

Находит единицы знаний по заданным критериям. Все фильтры работают по принципу AND — чем больше фильтров, тем уже выборка.

### Полный синтаксис

```
python3 main.py search
    [--domain ДОМЕН]
    [--category КАТЕГОРИЯ]
    [--difficulty УРОВЕНЬ]
    [--role РОЛЬ]
    [--stage ЭТАП]
    [--tag ТЕГ]           # можно повторять
    [--text ТЕКСТ]
    [--status СТАТУС]
    [--frequency ЧАСТОТА]
    [--verbose]
```

---

### Поиск по домену

```bash
# Все единицы знаний по Computer Science
python3 main.py search --domain cs

# Все по архитектуре
python3 main.py search --domain arch

# Все по процессу собеседования
python3 main.py search --domain process

# Глобальная предметная область
python3 main.py search --domain global
```

---

### Поиск по категории

```bash
# Все концепции
python3 main.py search --category concept

# Все алгоритмические задачи
python3 main.py search --category problem

# Все разборы system design
python3 main.py search --category sysdesign

# Все behavioral-вопросы
python3 main.py search --category behavioral

# Все паттерны решения задач
python3 main.py search --category pattern

# Все trade-off карточки
python3 main.py search --category tradeoff

# Все шпаргалки
python3 main.py search --category cheatsheet

# Все типичные ошибки
python3 main.py search --category pitfall

# Все компоненты систем
python3 main.py search --category component

# Все этапы собеседования
python3 main.py search --category stage

# Все стратегии подготовки
python3 main.py search --category strategy

# Все чек-листы
python3 main.py search --category checklist

# Все глоссарные статьи
python3 main.py search --category glossary
```

---

### Поиск по уровню сложности

```bash
# Только Junior-материалы
python3 main.py search --difficulty junior

# Только Middle
python3 main.py search --difficulty middle

# Только Senior
python3 main.py search --difficulty senior

# Только Staff+
python3 main.py search --difficulty staff
```

---

### Поиск по роли

```bash
# Материалы для backend-разработчика
python3 main.py search --role backend

# Для frontend
python3 main.py search --role frontend

# Для fullstack
python3 main.py search --role fullstack

# Для DevOps/SRE
python3 main.py search --role devops

# Для Data Engineer
python3 main.py search --role data_engineer

# Для Mobile
python3 main.py search --role mobile

# Для ML Engineer
python3 main.py search --role ml_engineer
```

> Единицы с `all_roles` попадают в результаты при любой роли.

---

### Поиск по этапу собеседования

```bash
# Материалы для coding interview
python3 main.py search --stage coding

# Для behavioral interview
python3 main.py search --stage behavioral

# Для system design interview
python3 main.py search --stage system_design

# Для phone screen
python3 main.py search --stage phone_screen

# Для take-home задания
python3 main.py search --stage take_home

# Для HR-скрининга
python3 main.py search --stage hr_screening

# Для переговоров по офферу
python3 main.py search --stage offer
```

---

### Поиск по тегам

Тег указывается через `--tag`. Можно указывать несколько раз — сработает AND-логика (единица должна содержать **все** указанные теги).

```bash
# Всё с тегом must_know
python3 main.py search --tag must_know

# Всё с тегом arrays
python3 main.py search --tag arrays

# Единицы у которых есть И arrays, И must_know
python3 main.py search --tag arrays --tag must_know

# Три тега одновременно
python3 main.py search --tag hash_tables --tag must_know --tag core

# Часто спрашиваемые вопросы
python3 main.py search --tag frequently_asked

# Динамическое программирование
python3 main.py search --tag dynamic_programming
```

---

### Полнотекстовый поиск

Параметр `--text` ищет совпадения в заголовке, ID, тегах и содержимом файла. Поиск регистронезависимый.

```bash
# Поиск по слову в заголовке
python3 main.py search --text "хеш"

# Поиск по английскому термину
python3 main.py search --text "binary search"

# Поиск по части слова
python3 main.py search --text "граф"

# Поиск по аббревиатуре
python3 main.py search --text "BFS"

# Поиск по имени алгоритма
python3 main.py search --text "Dijkstra"

# Поиск по русскому тексту
python3 main.py search --text "сортировка"
```

> Совпадение в заголовке даёт больше очков релевантности, чем в содержимом — такие результаты будут выше в списке.

---

### Поиск по статусу и частоте

```bash
# Только утверждённые единицы
python3 main.py search --status approved

# Только черновики
python3 main.py search --status draft

# Единицы на проверке
python3 main.py search --status review

# Часто спрашиваемые на собеседованиях
python3 main.py search --frequency high

# Иногда спрашиваемые
python3 main.py search --frequency medium

# Редко, но важно знать
python3 main.py search --frequency low
```

---

### Подробный вывод (--verbose)

Флаг `--verbose` добавляет в вывод очки релевантности и список совпавших полей.

```bash
python3 main.py search --domain cs --difficulty junior --verbose
```

Пример вывода с `--verbose`:
```
🔍 Найдено: 3

  1. [CS-CONCEPT-017] Хеш-таблица (Hash Table)
         cs / concept / junior
         score=20 | matched: domain=cs, difficulty=junior, title contains 'hash'

  2. [CS-PROBLEM-008] Two Sum
         cs / problem / junior
         score=20 | matched: domain=cs, difficulty=junior
         tags: arrays, hash_tables, must_know
```

---

### Комбинированный поиск (несколько фильтров)

```bash
# Задачи по CS уровня Junior для backend-разработчика на coding interview
python3 main.py search --domain cs --category problem --difficulty junior \
                       --role backend --stage coding

# Must-know концепции уровня Middle, часто спрашиваемые
python3 main.py search --category concept --difficulty middle \
                       --tag must_know --frequency high

# Утверждённые system design задачи уровня Senior
python3 main.py search --domain arch --category sysdesign \
                       --difficulty senior --status approved

# Behavioral-вопросы для всех ролей, часто задаваемые на behavioral interview
python3 main.py search --category behavioral --stage behavioral \
                       --frequency high --status approved

# Подробный поиск по тексту с фильтром по домену
python3 main.py search --domain cs --text "динамическое программирование" --verbose
```

---

## validate — валидация

Проверяет корректность метаданных в файлах. Если найдены ошибки — возвращает код выхода `1`.

### Полный синтаксис

```
python3 main.py validate
    [--file ПУТЬ_К_ФАЙЛУ]
```

---

### Валидация всей базы знаний

```bash
python3 main.py validate
```

Проверяет все файлы в папках `cs/`, `arch/`, `process/`, `global/`.

Пример вывода без ошибок:
```
🔍 Валидация БЗ: 89 единиц знаний...

✅ Валидация пройдена — проблем не найдено.
```

Пример вывода с ошибками:
```
🔍 Валидация БЗ: 89 единиц знаний...

❌ Ошибок: 2
  ❌ [CS-CONCEPT-001] id: Неверный формат 'bad-id'. Ожидается: ДОМЕН-КАТЕГОРИЯ-НН
  ❌ [ARCH-001] domain: Недопустимое значение 'architecture'.

⚠️  Предупреждений: 3
  ⚠️  [CS-PROBLEM-005] sources: Источники не указаны.
  ⚠️  [PROC-BEHAVIORAL-002] related: Ссылка на несуществующий ID 'CS-999'.
  ⚠️  [CS-CONCEPT-010] content: Тело документа пустое (заглушка).

❌ Валидация не пройдена: 2 ошибок.
```

---

### Валидация одного файла

```bash
# По относительному пути
python3 main.py validate --file cs/concepts/data_structures/cs_concept_hash_table.md

# По абсолютному пути
python3 main.py validate --file /home/alexander/techinterview_knowledge_base/cs/concepts/data_structures/cs_concept_hash_table.md

# Короткая форма параметра
python3 main.py validate -f cs/concepts/data_structures/cs_concept_hash_table.md
```

---

### Что именно проверяется

| Проверка | Тип | Описание |
|----------|-----|----------|
| Формат ID | Ошибка | Должен соответствовать `ДОМЕН-КАТЕГОРИЯ-НН` |
| Значение `domain` | Ошибка | Только `cs`, `arch`, `process`, `global` |
| Значение `category` | Ошибка | Только из допустимого списка |
| Значение `difficulty` | Ошибка | Только `junior`, `middle`, `senior`, `staff` |
| Уникальность ID | Ошибка | Не должно быть двух файлов с одинаковым ID |
| Значение `roles` | Предупреждение | Роль должна быть из допустимого списка |
| Значение `interview_stage` | Предупреждение | Этап должен быть из допустимого списка |
| Значение `status` | Предупреждение | Только `draft`, `review`, `approved` |
| Значение `frequency` | Предупреждение | Только `high`, `medium`, `low` |
| Ссылки в `related` | Предупреждение | ID должен существовать в БЗ |
| Ссылки в `prerequisites` | Предупреждение | ID должен существовать в БЗ |
| Наличие источников | Предупреждение | Поле `sources` не должно быть пустым |
| Непустой контент | Предупреждение | Тело файла не должно быть пустым или очень коротким |

> **Ошибки** — критические нарушения, нужно исправить.
> **Предупреждения** — рекомендации, не блокируют работу.

---

## registry — реестр ID

Генерирует файл `_meta/id_registry.md` — сводную таблицу всех единиц знаний с их ID.

### Полный синтаксис

```
python3 main.py registry
    [--output ПУТЬ]
```

---

### Примеры использования

```bash
# Генерация в папку по умолчанию (_meta/id_registry.md)
python3 main.py registry

# Сохранение в другое место
python3 main.py registry --output docs/all_units.md

# Короткая форма параметра
python3 main.py registry -o _meta/id_registry.md
```

---

### Что создаётся

Файл `_meta/id_registry.md` содержит:
- Статистику по доменам и статусам
- Предупреждение о дублирующихся ID (если есть)
- Полную таблицу всех единиц: ID · Название · Домен · Категория · Сложность · Статус · Файл

Пример вывода в консоли:
```
✅ Реестр сохранён: _meta/id_registry.md (89 записей)
📋 Реестр идентификаторов
   Всего единиц знаний: 89

   По доменам:
     arch           12
     cs             45
     global          8
     process        24

   По статусам:
     approved       41
     draft          48

   ✅ Дублирующихся ID не найдено
```

> **Совет:** запускай `registry` после каждого добавления новых единиц знаний, чтобы реестр оставался актуальным.

---

## new — создание единицы знаний

Создаёт новый `.md` файл по шаблону в правильной папке. Автоматически определяет следующий свободный ID.

### Полный синтаксис

```
python3 main.py new
    --title НАЗВАНИЕ
    --domain ДОМЕН
    --category КАТЕГОРИЯ
    --difficulty УРОВЕНЬ
    [--author АВТОР]
    [--dry-run]
    [--list-templates]
```

---

### Просмотр доступных шаблонов

```bash
python3 main.py new --list-templates
```

Вывод:
```
📄 Доступные шаблоны (категории):
  behavioral      → behavioral/
  cheatsheet      → cheatsheets/
  checklist       → checklists/
  company         → companies/
  component       → components/
  concept         → concepts/
  cross           → cross_domain/
  designpat       → design_patterns/
  framework       → frameworks/
  glossary        → glossary/
  matrix          → competency_matrix/
  onto            → ontology/
  pattern         → patterns/
  pitfall         → pitfalls/
  problem         → problems/
  profile         → role_profiles/
  question        → questions/
  softskill       → softskills/
  stage           → stages/
  strategy        → strategies/
  sysdesign       → system_design/
  tradeoff        → tradeoffs/
  trajectory      → trajectories/
```

---

### Создание карточки концепции CS

```bash
python3 main.py new \
  --title "Binary Search" \
  --domain cs \
  --category concept \
  --difficulty junior \
  --author "Инженер знаний №1"
```

Вывод:
```
✅ Создан файл: cs/concepts/cs_concept_binary_search.md
   ID: CS-CONCEPT-018 | cs / concept / junior
```

---

### Создание алгоритмической задачи

```bash
python3 main.py new \
  --title "Two Sum" \
  --domain cs \
  --category problem \
  --difficulty junior
```

---

### Создание паттерна решения задач

```bash
python3 main.py new \
  --title "Fast and Slow Pointers" \
  --domain cs \
  --category pattern \
  --difficulty middle
```

---

### Создание разбора system design

```bash
python3 main.py new \
  --title "Twitter Feed" \
  --domain arch \
  --category sysdesign \
  --difficulty senior \
  --author "Инженер знаний №2"
```

---

### Создание компонента системы

```bash
python3 main.py new \
  --title "Redis Cache" \
  --domain arch \
  --category component \
  --difficulty middle
```

---

### Создание trade-off карточки

```bash
python3 main.py new \
  --title "SQL vs NoSQL" \
  --domain arch \
  --category tradeoff \
  --difficulty middle
```

---

### Создание behavioral-вопроса

```bash
python3 main.py new \
  --title "Tell Me About Yourself" \
  --domain process \
  --category behavioral \
  --difficulty junior \
  --author "Инженер знаний №3"
```

---

### Создание стратегии подготовки

```bash
python3 main.py new \
  --title "План подготовки 1 месяц" \
  --domain process \
  --category strategy \
  --difficulty junior
```

---

### Создание шпаргалки

```bash
python3 main.py new \
  --title "Big O Notation" \
  --domain cs \
  --category cheatsheet \
  --difficulty junior
```

---

### Создание глоссарной статьи

```bash
python3 main.py new \
  --title "Latency" \
  --domain global \
  --category glossary \
  --difficulty junior
```

---

### Dry-run — посмотреть без создания файла

Флаг `--dry-run` показывает путь и содержимое будущего файла, не создавая его:

```bash
python3 main.py new \
  --title "Hash Table" \
  --domain cs \
  --category concept \
  --difficulty junior \
  --dry-run
```

Вывод:
```
🔍 Dry run — файл не создан: cs/concepts/cs_concept_hash_table.md
```

---

### Что делать после создания файла

```bash
# 1. Открой созданный файл
nano cs/concepts/cs_concept_hash_table.md
# или
code cs/concepts/cs_concept_hash_table.md

# 2. Заполни поля отмеченные # TODO:
#    - добавь теги
#    - укажи sources
#    - напиши содержимое

# 3. Смени статус с "draft" на "review"

# 4. Проверь файл
python3 main.py validate --file cs/concepts/cs_concept_hash_table.md

# 5. Обнови реестр
python3 main.py registry
```

---

## stats — статистика

Показывает количество единиц знаний по доменам, категориям, уровням сложности и статусам.

### Полный синтаксис

```
python3 main.py stats
    [--validate]
```

---

### Базовая статистика

```bash
python3 main.py stats
```

Пример вывода:
```
📚 Всего единиц знаний: 89

По доменам:
  arch         12
  cs           45
  global        8
  process      24

По категориям (топ-10):
  concept         28
  problem         15
  behavioral       9
  sysdesign        7
  pitfall          6
  pattern          5
  tradeoff         5
  component        4
  glossary         4
  cheatsheet       3

По статусу:
  approved      41
  draft         48
```

---

### Статистика с валидацией

```bash
python3 main.py stats --validate
```

К обычному выводу добавится краткий отчёт:
```
🔍 Запуск валидации...
   Ошибок:         0
   Предупреждений: 12
   ✅ Критических ошибок нет.
```

---

## Комбинирование команд

### Проверить и сразу обновить реестр

```bash
python3 main.py validate && python3 main.py registry
```

Команда после `&&` выполнится только если валидация прошла без ошибок.

---

### Создать файл и сразу проверить его

```bash
python3 main.py new --title "Heap" --domain cs --category concept --difficulty middle && \
python3 main.py validate --file cs/concepts/cs_concept_heap.md
```

---

### Полный цикл добавления новой единицы знаний

```bash
# Создать
python3 main.py new --title "Merge Sort" --domain cs --category concept --difficulty middle

# Открыть и заполнить
nano cs/concepts/cs_concept_merge_sort.md

# Проверить
python3 main.py validate --file cs/concepts/cs_concept_merge_sort.md

# Обновить реестр
python3 main.py registry

# Убедиться что всё хорошо
python3 main.py stats --validate
```

---

### Найти черновики и посмотреть их список

```bash
python3 main.py search --status draft
```

---

### Найти все незаполненные единицы в CS

```bash
python3 main.py search --domain cs --status draft
```

---

## Шпаргалка

```bash
# ── ПОИСК ──────────────────────────────────────────────────────────────────

python3 main.py search --domain cs                           # всё по CS
python3 main.py search --domain arch                         # всё по архитектуре
python3 main.py search --domain process                      # всё по процессу
python3 main.py search --difficulty junior                   # только Junior
python3 main.py search --difficulty middle                   # только Middle
python3 main.py search --category concept                    # все концепции
python3 main.py search --category problem                    # все задачи
python3 main.py search --category sysdesign                  # весь system design
python3 main.py search --category behavioral                 # все behavioral-вопросы
python3 main.py search --role backend                        # для backend
python3 main.py search --stage coding                        # для coding interview
python3 main.py search --stage system_design                 # для system design
python3 main.py search --tag must_know                       # обязательно к знанию
python3 main.py search --tag must_know --stage coding        # must_know для coding
python3 main.py search --text "binary search"                # по тексту
python3 main.py search --status approved                     # только утверждённые
python3 main.py search --frequency high                      # часто спрашивают
python3 main.py search --domain cs --difficulty junior --verbose  # подробно

# ── ВАЛИДАЦИЯ ──────────────────────────────────────────────────────────────

python3 main.py validate                                     # вся БЗ
python3 main.py validate --file ПУТЬ_К_ФАЙЛУ                 # один файл
python3 main.py validate -f ПУТЬ_К_ФАЙЛУ                     # короткая форма

# ── РЕЕСТР ─────────────────────────────────────────────────────────────────

python3 main.py registry                                     # сохранить в _meta/
python3 main.py registry --output docs/registry.md          # в другое место

# ── СОЗДАНИЕ ───────────────────────────────────────────────────────────────

python3 main.py new --list-templates                         # список шаблонов
python3 main.py new --title "..." --domain cs --category concept --difficulty junior
python3 main.py new --title "..." --domain arch --category sysdesign --difficulty senior
python3 main.py new --title "..." --domain process --category behavioral --difficulty middle
python3 main.py new ... --dry-run                            # без создания файла

# ── СТАТИСТИКА ─────────────────────────────────────────────────────────────

python3 main.py stats                                        # базовая статистика
python3 main.py stats --validate                             # + краткая валидация

# ── СПРАВКА ────────────────────────────────────────────────────────────────

python3 main.py --help
python3 main.py search --help
python3 main.py validate --help
python3 main.py new --help
python3 main.py registry --help
python3 main.py stats --help
```
