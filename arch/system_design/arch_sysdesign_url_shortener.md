---
id: "ARCH-SYSDESIGN-005"
title: "URL Shortener (TinyURL/bit.ly)"
domain: "arch"
category: "sysdesign"
tags:
  - system_design
  - databases
  - caching
  - api_design
  - must_know
  - core
difficulty: "middle"
roles:
  - backend
  - fullstack
  - devops
  - all_roles
interview_stage:
  - system_design
frequency: "high"
related:
  - "ARCH-COMPONENT-001"
  - "ARCH-COMPONENT-002"
  - "ARCH-COMPONENT-004"
  - "ARCH-TRADEOFF-001"
  - "ARCH-TRADEOFF-002"
prerequisites:
  - "ARCH-COMPONENT-001"
  - "ARCH-COMPONENT-002"
sources:
  - "Xu A. System Design Interview – An Insider's Guide. Chapter 8. ByteByteGo, 2020."
  - "The System Design Primer by Donne Martin. https://github.com/donnemartin/system-design-primer"
author: "Инженер знаний №2"
version: "1.0"
date_created: "2026-04-09"
date_updated: "2026-04-09"
status: "approved"
---

# URL Shortener (TinyURL/bit.ly)

## Постановка задачи
Спроектируйте сервис для сокращения URL-адресов. Пользователь вводит длинный URL, получает короткий ключ. При переходе по короткому URL происходит редирект на оригинальный.

## Шаг 1: Уточнение требований

### Функциональные требования
1. Генерация уникального короткого URL по длинному
2. Редирект с короткого URL на оригинальный
3. Опционально: кастомный alias, TTL, аналитика кликов

### Нефункциональные требования
1. Высокая доступность (> 99.9%)
2. Низкая задержка редиректа (< 100ms p99)
3. Короткие URL не должны быть предсказуемыми
4. Масштабируемость до миллиардов записей

### Уточняющие вопросы
1. Какой ожидаемый трафик? (→ capacity estimation)
2. Какая длина короткого URL? (→ пространство ключей)
3. Нужна ли аналитика? (→ дополнительные компоненты)
4. Какой TTL по умолчанию? (→ стратегия очистки)

### Допущения
- 100M новых URL/месяц
- Соотношение чтение:запись = 100:1
- Хранение 5 лет
- Средняя длина URL: 200 байт

## Шаг 2: Capacity Estimation

Запись: 100M/месяц ≈ 40 URL/сек
Чтение: 40 × 100 = 4000 redirects/сек
Хранилище (5 лет): 6B записей × 216 байт ≈ 1.3 TB
Пространство ключей (7 символов Base62): 62^7 ≈ 3.5T (достаточно)

## Шаг 3: High-Level Design

Основные компоненты:
1. **API Servers** (stateless): обработка запросов на создание и редирект
2. **ID Generator**: генерация уникальных коротких ключей
3. **Database**: хранение маппинга short → long URL
4. **Cache (Redis)**: кеш для hot URLs (80/20 правило)
5. **Load Balancer**: распределение нагрузки

Поток данных:
- Write path: Client → LB → API → ID Generator → Database
- Read path: Client → LB → API → Cache (hit) / Database (miss) → Redirect

## Шаг 4: Deep Dive

### 4.1 Генерация короткого URL

| Подход | Плюсы | Минусы | Когда выбирать |
|--------|-------|--------|---------------|
| Hash + обрезка | Детерминированный | Коллизии, нужна проверка | Небольшие системы |
| Counter + Base62 | Гарантированная уникальность | Предсказуемость, SPOF | Внутренние сервисы |
| Pre-generated keys (KGS) | Быстро, нет коллизий | Доп. инфраструктура | Продакшн, масштаб |

**Выбор**: Key Generation Service (KGS) — лучший баланс для масштабируемой системы.

### 4.2 Caching Strategy
- Cache hot URLs в Redis (LRU eviction)
- Read path: Cache → DB
- Ожидаемый cache hit ratio: ~80%
- TTL в кеше: совпадает с TTL URL или 24h

## Шаг 5: Trade-offs и альтернативы

| Решение | За | Против | Когда выбирать |
|---------|----|--------|---------------|
| SQL (PostgreSQL) | ACID, надёжность | Сложнее шардить | < 1B записей |
| NoSQL (DynamoDB) | Горизонтальное масштабирование | Eventual consistency | > 1B записей |
| 301 Redirect | Меньше нагрузки | Нет аналитики | Без аналитики |
| 302 Redirect | Можно считать клики | Больше запросов | С аналитикой |

## Шаг 6: Bottlenecks и решения

1. **ID Generator — SPOF**: → KGS с pre-generated keys, два пула (used/unused)
2. **Database — нагрузка на запись**: → Шардинг по short_key (hash или range)
3. **Hot URLs**: → Multi-tier caching (CDN → Redis → DB)
4. **Expired URLs**: → Lazy cleanup + periodic background job

## Критерии оценки интервьюером

| Уровень | Ожидания |
|---------|----------|
| Middle | Чёткие требования, capacity estimation, рабочий high-level design, один deep dive |
| Senior | Всё выше + trade-offs, масштабирование, отказоустойчивость, несколько deep dive |

## Типичные ошибки кандидатов

- Пропускают capacity estimation и сразу рисуют архитектуру
- Не обсуждают коллизии при генерации ключей
- Забывают о кешировании (read-heavy система!)
- Не уточняют 301 vs 302
- Не продумывают TTL и очистку expired URLs

## Связанные темы

- [[ARCH-COMPONENT-001]] — Load Balancer (applied_in)
- [[ARCH-COMPONENT-002]] — Cache (applied_in)
- [[ARCH-COMPONENT-004]] — API Gateway (applied_in)
- [[ARCH-TRADEOFF-001]] — SQL vs NoSQL (applied_in)
- [[ARCH-TRADEOFF-002]] — Consistency vs Availability (relates_to)
- [[PROC-FRAMEWORK-003]] — Фреймворк решения SD задачи (is_part_of)

## Источники

1. Xu A. System Design Interview – An Insider's Guide. Chapter 8. ByteByteGo, 2020.
2. The System Design Primer — URL Shortener. https://github.com/donnemartin/system-design-primer