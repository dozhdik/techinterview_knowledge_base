---
id: "ARCH-SYSDESIGN-003"
title: "Search Autocomplete"
domain: "arch"
category: "sysdesign"
tags:
  - system_design
  - search
  - autocomplete
  - low_latency
  - indexing
difficulty: "senior"
roles:
  - "backend"
  - "fullstack"
  - "data_engineer"
  - "all_roles"
interview_stage:
  - "system_design"
frequency: "medium"
related:
  - "ARCH-COMPONENT-007"
  - "ARCH-TRADEOFF-001"
prerequisites: []
sources:
  - "Alex Xu — System Design Interview"
  - "Elasticsearch Documentation"
  - "OpenSearch Documentation"
author: "Инженер знаний №2"
version: "1.0"
date_created: "2026-04-10"
date_updated: "2026-04-10"
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
