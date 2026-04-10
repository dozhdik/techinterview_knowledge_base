---
id: "ARCH-SYSDESIGN-004"
title: "Search Autocomplete"
domain: "arch"
category: "sysdesign"
tags:
  - system_design
  - search
  - autocomplete
  - low_latency
  - indexing
  - must_know
  - core
difficulty: "senior"
roles:
  - "backend"
  - "fullstack"
  - "data_engineer"
  - "all_roles"
interview_stage:
  - "system_design"
frequency: "high"
related:
  - "ARCH-COMPONENT-007"
  - "ARCH-TRADEOFF-001"
  - "ARCH-TRADEOFF-003"
prerequisites: []
sources:
  - "Xu A. System Design Interview — An Insider's Guide. ByteByteGo, 2020+"
  - "Elastic. Elasticsearch Guide — suggesters and completion"
  - "OpenSearch Project. Documentation — search and aggregations"
author: "Инженер знаний №2"
version: "1.0"
date_created: "2026-04-10"
date_updated: "2026-04-11"
status: "review"
---

# Search Autocomplete

## Постановка задачи
Нужно спроектировать сервис autocomplete, который подсказывает пользователю поисковые запросы в реальном времени по мере ввода текста. Подсказки должны возвращаться быстро, быть релевантными и выдерживать большой read-heavy трафик. На собеседовании эта задача проверяет, понимает ли кандидат разницу между low-latency lookup, ranking и offline/nearline обновлением индекса.

## Шаг 1: Уточнение требований
### Функциональные требования
1. Подсказки по префиксу введённой строки
2. Сортировка подсказок по популярности и релевантности
3. Ограничение количества возвращаемых вариантов
4. Поддержка нескольких языков и локалей
5. Фильтрация нежелательных, токсичных или запрещённых подсказок
6. Возможность обновлять популярные запросы со временем
7. Опционально — typo tolerance и персонализация

### Нефункциональные требования
1. Очень низкая latency ответа
2. Высокая масштабируемость на чтение
3. Высокая availability
4. Хороший cache hit ratio
5. Допустима eventual consistency для обновления популярных подсказок

### Уточняющие вопросы интервьюеру
1. Нужна ли персонализация? — персонализированный autocomplete заметно сложнее и требует user-specific signals
2. Насколько критична свежесть популярных запросов? — realtime и hourly batch дают очень разную архитектуру
3. Нужна ли fuzzy matching / typo tolerance? — это сильно влияет на структуру индекса и стоимость запроса
4. Есть ли multi-language support? — это меняет токенизацию, ranking и storage
5. Что важнее: latency или качество ranking? — нельзя одновременно бесконечно усложнять ranking и держать сверхнизкую задержку

### Допущения
- 5 млн DAU
- 100 млн поисковых запросов в день
- один пользователь генерирует несколько autocomplete-запросов на один поисковый сеанс
- основная нагрузка — чтение
- обновление популярных подсказок делается batch или near-real-time pipeline
- базовая версия не требует сильной персонализации

## Шаг 2: Capacity Estimation
- **Пользователи**: 5 млн DAU / 50 млн MAU
- **Запросы**: десятки тысяч RPS на чтение в пике; записи редкие и в основном идут через pipeline пересчёта popularity data
- **Хранилище**: от десятков до сотен GB на prefix index, popularity stats, language-specific dictionaries и служебные структуры; рост зависит от числа локалей и retention сырых query logs

## Шаг 3: High-Level Design
```text
[Client] → [Load Balancer] → [Autocomplete API]
                                   ↓
                                 [Cache]
                                   ↓
                        [Prefix Index / Trie Store]
                                   ↓
                         [Ranking / Filtering Layer]

      [Query Logs] → [Analytics Pipeline] → [Top Queries Builder]
                                         ↓
                                 [Index Rebuild / Update]
```

## Шаг 4: Модель данных и индекс
- **Префиксный индекс**: trie / radix tree в памяти (сервис или shared cache) **или** completion suggester в [[ARCH-COMPONENT-007]] (Elasticsearch/OpenSearch).
- **К каждому префиксу** — топ-N кандидатов с весами (частота, CTR, ручной boost, фильтры по локали).
- **Сырые логи запросов** — в объектном хранилище/warehouse для offline-пайплайна; агрегаты популярности — в БД или KV.

## Шаг 5: API
- `GET /suggest?prefix=&locale=&limit=` — только чтение; строгие таймауты (например 50–100 ms budget).
- Заголовки кеширования или edge-cache для горячих префиксов; при персонализации — отдельный путь с user id и без публичного кеша.

## Шаг 6: Углубление по компонентам
- **Cache** (Redis / CDN): ключ `(locale, prefix)`; короткий TTL для баланса свежести и hit ratio.
- **Ranking layer**: объединение popularity, безопасности (blocklist), бизнес-правил; тяжёлые сигналы — offline.
- **Analytics pipeline**: batch или stream (Flink/Spark) — подсчёт top queries; публикация снапшота для сборки индекса.
- **Index rebuild**: blue/green или dual index + alias switch, чтобы не ломать чтение при обновлении.

## Шаг 7: Масштабирование
- Горизонтально: stateless API + репликация read-only копий trie/сегментов индекса по регионам.
- Шардирование по первому символу/локали при очень большом словаре.

## Шаг 8: Отказы и компромиссы
- Индекс отстаёт от реальности — допустимо для подсказок (**eventual consistency**, см. [[ARCH-TRADEOFF-003]]).
- Деградация: при падении индекса — ответ из кеша или пустой/статический fallback.
- Typo-tolerance удорожает запрос; для низкой latency часто отключают на первом тире.

## Шаг 9: Наблюдаемость
- p95/p99 latency, cache hit rate, размер индекса, задержка пайплайна популярности, доля заблокированных подсказок.

## Шаг 10: Резюме
Критичный путь — **O(length of prefix)** lookup + лёгкий ranking. Тяжёлая аналитика вынесена offline. Форма API и кеширование связаны с [[ARCH-TRADEOFF-001]]; баланс свежести подсказок и задержки — с [[ARCH-TRADEOFF-003]].
