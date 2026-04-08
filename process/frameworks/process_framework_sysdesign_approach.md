---
id: "PROC-FRAMEWORK-003"
title: "Фреймворк решения System Design задачи"
domain: "process"
category: "framework"
tags:
  - system_design
  - problem_solving
  - архитектура
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
  - "PROC-STAGE-004"
  - "ARCH-SYSDESIGN-001"
  - "PROC-PITFALL-004"
prerequisites:
  - "PROC-STAGE-003"
sources:
  - "Xu A. System Design Interview – An Insider's Guide. ByteByteGo, 2020."
  - "The System Design Primer by Donne Martin. https://github.com/donnemartin/system-design-primer"
author: "Инженер знаний №3"
version: "1.0"
date_created: "2026-04-09"
date_updated: "2026-04-09"
status: "draft"
---

# Фреймворк решения System Design задачи

## Что это
Универсальный 6-шаговый подход к решению задач по проектированию систем на собеседовании. Помогает структурировать мышление, не пропускать ключевые аспекты и демонстрировать интервьюеру системный подход.

## Зачем использовать
- Не начинать рисовать архитектуру без понимания требований
- Показать, что ты умеешь декомпозировать сложные системы
- Уменьшить вероятность упущения важных компонентов
- Демонстрировать коммуникацию и trade-off мышление на всём протяжении

## 6 шагов фреймворка

### 1. CLARIFY (Уточнение требований) — 5-10 мин
**Что делать:**
- Задать вопросы про функциональные требования: что система должна делать
- Уточнить нефункциональные: latency, availability, consistency, масштаб
- Зафиксировать допущения (если интервьюер не отвечает)

**Фразы-помощники:**
- «Какой ожидаемый масштаб: пользователей, запросов в секунду?»
- «Нужна ли строгая консистентность или eventual consistency допустима?»
- «Какие SLA по latency?»

### 2. ESTIMATE (Capacity estimation) — 3-5 мин
**Что делать:**
- Оценить: DAU/MAU, RPS (чтение/запись), storage за период
- Использовать back-of-the-envelope расчёты
- Пример: 100M пользователей → ~40 writes/sec, 4000 reads/sec

**Формулы-шпаргалки:**
- Записей в день = пользователи × действия/пользователя
- Storage = записи × размер записи × дни хранения
- RPS = записи в день / 86400

### 3. HIGH-LEVEL DESIGN (Архитектура) — 10 мин
**Что делать:**
- Нарисовать основные компоненты и связи
- Client → LB → API Gateway → Services → DB/Cache/Queue
- Обосновать выбор каждого компонента

**Типовые компоненты:**
- Load Balancer, API Gateway
- Cache (Redis, CDN), Message Queue (Kafka)
- SQL/NoSQL DB, Blob Storage, Search Engine

### 4. DEEP DIVE (Детализация) — 15-20 мин
**Что делать:**
- Выбрать 1-2 ключевых аспекта для углубления:
  • Data model и схема БД
  • API design (endpoints, payload, versioning)
  • Scaling strategy (sharding, replication, consistent hashing)
  • Caching strategy (что, где, как кэшировать, eviction policy)

**Фразы-помощники:**
- «Давайте углубимся в модель данных, потому что...»
- «Для масштабирования я предлагаю шардировать по... потому что...»

### 5. TRADE-OFFS (Компромиссы) — 5-10 мин
**Что делать:**
- Обсудить альтернативы и почему выбран этот путь
- Выявить bottleneck'ы и как их решать
- Упомянуть, что можно добавить при наличии времени

**Примеры trade-offs:**
- SQL vs NoSQL: consistency vs scalability
- 301 vs 302 redirect: caching vs analytics
- Sync vs async: simplicity vs responsiveness

### 6. WRAP-UP (Завершение) — 2-3 мин
**Что делать:**
- Кратко резюмировать архитектуру
- Упомянуть мониторинг, alerting, graceful degradation
- Спросить, хочет ли интервьюер углубиться в другой аспект

## Типичные ошибки

❌ **Сразу рисовать архитектуру без уточнений**
✅ Сначала задать вопросы, зафиксировать требования

❌ **Игнорировать масштаб**
✅ Сделать capacity estimation в начале

❌ **Не обсуждать trade-offs**
✅ «Выбрал Redis потому что... альтернатива была... но не подошла потому что...»

❌ **Уходить в детали слишком рано**
✅ Сначала общая картина, потом углубление

❌ **Молча рисовать**
✅ Постоянно комментировать: «сейчас я добавлю..., потому что...»

## Адаптация под уровни

**Middle:**
- Ожидается рабочий high-level design, 1 deep dive, базовые trade-offs
- Достаточно показать понимание компонентов и их взаимодействия

**Senior:**
- Полный цикл, несколько deep dive, масштабирование, отказоустойчивость
- Ожидается обсуждение организационных аспектов и долгосрочной эволюции

**Staff+:**
- Кросс-системное мышление, влияние на несколько команд
- Стратегические решения, баланс между perfect и ship-it

## Связанные темы

- [[PROC-STAGE-004]] — System Design Interview (applied_in)
- [[ARCH-SYSDESIGN-001]] — URL Shortener (exemplifies)
- [[ARCH-COMPONENT-001]] — Load Balancer (relates_to)
- [[PROC-PITFALL-004]] — Ошибка: пропуск capacity estimation (warns_about)

## Источники

1. Xu A. System Design Interview – An Insider's Guide. 2020.
2. The System Design Primer. https://github.com/donnemartin/system-design-primer
3. Kleppmann M. Designing Data-Intensive Applications. 2017.