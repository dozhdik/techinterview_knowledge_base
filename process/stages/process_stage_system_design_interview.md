---
id: "PROC-STAGE-004"
title: "System Design Interview (Интервью по проектированию систем)"
domain: "process"
category: "stage"
tags:
  - system_design
  - architecture
  - scalability
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
  - "PROC-STAGE-003"   # Coding Interview (предыдущий этап)
  - "PROC-FRAMEWORK-003"   # System Design Approach
  - "ARCH-SYSDESIGN-005"   # URL Shortener (пример задачи)
prerequisites:
  - "PROC-STAGE-003"   # Coding Interview
sources:
  - "Xu A. System Design Interview – An Insider's Guide. ByteByteGo, 2020."
  - "Kleppmann M. Designing Data-Intensive Applications. O'Reilly, 2017."
author: "Инженер знаний №3"
version: "1.0"
date_created: "2026-04-09"
date_updated: "2026-04-09"
status: "review"
aliases:
  - "Собеседование по проектированию систем"
---

# System Design Interview (Интервью по проектированию систем)

## Определение
System Design Interview — этап, где кандидат проектирует масштабируемую систему по заданным требованиям. Проверяет архитектурное мышление, умение принимать trade-off решения и работать с неопределённостью.

## Формат
- **Длительность:** 45-60 минут
- **Формат:** Video call + Whiteboard / Diagram tool
- **Участники:** кандидат + 1-2 инженера
- **Задача:** 1 открытая задача (например, «Спроектируйте URL shortener»)

## Что оценивают

**Архитектурное мышление (30%):**
- Умение декомпозировать проблему
- Выбор компонентов и обоснование
- Понимание масштаба и ограничений

**Technical Knowledge (25%):**
- Знание компонентов (cache, LB, DB, queue)
- Понимание trade-offs (SQL vs NoSQL, consistency vs availability)
- Capacity estimation (back-of-the-envelope)

**Коммуникация (25%):**
- Умение задавать уточняющие вопросы
- Объяснение решений и альтернатив
- Реакция на фидбек

**Практичность (20%):**
- Реалистичность предложений
- Учёт bottleneck'ов
- План масштабирования

## Структура решения (5 шагов)

**1. Clarify Requirements (5-10 мин)**
- Функциональные требования: что система должна делать
- Нефункциональные: latency, availability, consistency
- Уточняющие вопросы: масштаб, пользователи, ограничения
- Допущения: зафиксировать ключевые предположения

**2. Capacity Estimation (5 мин)**
- Оценить: QPS, storage, bandwidth
- Пример: 100M users → ~40 writes/sec, 4000 reads/sec
- Back-of-the-envelope расчёты

**3. High-Level Design (10 мин)**
- Нарисовать основные компоненты и связи
- Client → LB → API → Services → DB/Cache
- Обосновать выбор каждого компонента

**4. Deep Dive (15-20 мин)**
- Детализировать 1-2 ключевых аспекта:
  • Data model и схема БД
  • API design (endpoints, payload)
  • Scaling strategy (sharding, replication)
  • Caching strategy (что, где, как кэшировать)

**5. Trade-offs & Bottlenecks (5-10 мин)**
- Обсудить альтернативы и почему выбран этот путь
- Выявить bottleneck'ы и как их решать
- Что можно добавить при наличии времени

## Типичные задачи

**Для Middle:**
- URL Shortener
- Rate Limiter
- Notification Service
- Chat System (basic)

**Для Senior:**
- Twitter/Instagram Feed
- Video Streaming (YouTube)
- Ride Sharing (Uber)
- Distributed Key-Value Store

## Чек-лист подготовки

**Компоненты систем:**
- [ ] Load Balancer, API Gateway
- [ ] Cache (Redis, CDN), Message Queue (Kafka)
- [ ] SQL vs NoSQL, sharding, replication
- [ ] Consistent hashing, CAP theorem

**Практика:**
- [ ] Разобрать 5-7 задач из System Design Primer
- [ ] Тренировать capacity estimation
- [ ] Практиковать объяснение вслух
- [ ] Изучить engineering blogs (Netflix, Uber)

**Перед интервью:**
- [ ] Подготовить маркер/инструмент для диаграмм
- [ ] Повторить ключевые trade-offs
- [ ] Подготовить вопросы интервьюеру

## Типичные ошибки

❌ **Сразу рисовать архитектуру без уточнений**
- Пропускают этап clarifying questions
- ✅ Сначала задать вопросы, зафиксировать требования

❌ **Игнорировать масштаб**
- Проектируют для 1000 пользователей, а не 100M
- ✅ Сделать capacity estimation в начале

❌ **Не обсуждать trade-offs**
- «Выбрал Redis, потому что крутой»
- ✅ «Выбрал Redis потому что... альтернатива была... но не подошла потому что...»

❌ **Уходить в детали слишком рано**
- Начинают проектировать схему БД до high-level дизайна
- ✅ Сначала общая картина, потом углубление

❌ **Молча рисовать**
- Интервьюер не понимает ход мыслей
- ✅ Постоянно комментировать: «сейчас я добавлю..., потому что...»

## Критерии прохождения

✅ **Прошёл (Strong Hire):**
- Чёткие требования и допущения
- Рабочий high-level design
- Глубокий deep dive с обоснованием
- Обсуждение trade-offs и bottleneck'ов

⚠️ **На грани (Weak Hire):**
- Пропустил capacity estimation
- Поверхностный deep dive
- Слабое обоснование решений

❌ **Не прошёл (No Hire):**
- Не смог сформулировать требования
- Нереалистичная архитектура
- Фундаментальные пробелы в компонентах

## Уровни ожиданий

| Уровень | Ожидания |
|---------|----------|
| **Middle** | Рабочий high-level design, 1 deep dive, базовые trade-offs |
| **Senior** | Полный цикл, несколько deep dive, масштабирование, отказоустойчивость |
| **Staff+** | Кросс-системное мышление, организационные аспекты, долгосрочная эволюция |

## Что дальше?

После system design → Behavioral Interview → Team Match / Offer

## Связанные темы

- [[PROC-STAGE-003]] — Coding Interview (предыдущий этап)
- [[PROC-FRAMEWORK-003]] — System Design Approach (методика)
- [[ARCH-SYSDESIGN-005]] — URL Shortener (пример задачи)
- [[ARCH-COMPONENT-001]] — Load Balancer (компонент)
- [[ARCH-TRADEOFF-006]] — SQL vs NoSQL (компромисс)

## Источники

1. Xu A. System Design Interview – An Insider's Guide. 2020.
2. Kleppmann M. Designing Data-Intensive Applications. 2017.
3. System Design Primer. https://github.com/donnemartin/system-design-primer
