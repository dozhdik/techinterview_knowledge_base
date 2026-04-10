---
id: "ARCH-TRADEOFF-007"
title: "Synchronous vs Asynchronous Communication"
domain: "arch"
category: "tradeoff"
tags:
  - communication
  - distributed_systems
  - messaging
  - event_driven
  - tradeoffs
  - must_know
  - core
difficulty: "middle"
roles:
  - "backend"
  - "devops"
  - "all_roles"
interview_stage:
  - "system_design"
  - "phone_screen"
frequency: "medium"
related:
  - "ARCH-SYSDESIGN-001"
  - "ARCH-SYSDESIGN-002"
  - "ARCH-TRADEOFF-003"
prerequisites: []
sources:
  - "Martin Kleppmann — Designing Data-Intensive Applications"
  - "Enterprise Integration Patterns"
  - "Kafka Documentation"
author: "Инженер знаний №2"
version: "1.0"
date_created: "2026-04-10"
date_updated: "2026-04-11"
status: "review"
---

# Synchronous vs Asynchronous Communication

## Суть компромисса
Компромисс между synchronous и asynchronous communication — это выбор между простотой request-response модели и устойчивостью распределённой системы под нагрузкой и сбоями. Синхронное взаимодействие проще для reasoning: сервис А вызывает сервис Б и сразу получает результат. Асинхронное взаимодействие развязывает компоненты, лучше переносит пики и сбои downstream-сервисов, но усложняет наблюдаемость, порядок обработки, retries и guarantees доставки. Нельзя честно получить одновременно и минимальную связанность, и мгновенный ответ, и простую отладку, и идеальную устойчивость. Поэтому выбор зависит от того, что важнее: немедленный ответ клиенту или способность системы жить при деградации частей.

## Вариант A
### Преимущества
- Простая ментальная модель: запрос → обработка → ответ
- Клиент сразу знает результат операции
- Проще дебажить, трассировать и тестировать end-to-end path
- Хорошо подходит для read path и user-facing запросов
- Меньше промежуточной инфраструктуры

### Недостатки
- Сильная связность между сервисами
- Один медленный downstream тянет вниз весь запрос
- Выше риск cascading failures
- Плохо переносит burst traffic
- Тяжелее переживает временную недоступность зависимостей

### Когда выбирать
- операции, где клиенту нужен результат сразу
- синхронные query-сценарии: получить профиль, баланс, страницу товара
- маленькие и средние системы с умеренной нагрузкой
- участки, где eventual consistency бизнесу не подходит

## Вариант B
### Преимущества
- Сервисы становятся слабее связаны друг с другом
- Очереди и event bus помогают буферизовать пики нагрузки
- Система лучше переживает временные сбои downstream
- Удобно для background jobs, fan-out и side effects
- Позволяет масштабировать обработчики независимо

### Недостатки
- Сложнее понять полный жизненный цикл операции
- Появляется eventual consistency
- Нужны idempotency, retries, DLQ и deduplication
- Сложнее observability и debugging
- Результат операции клиент видит не сразу или вообще через другой канал

### Когда выбирать
- уведомления, email, SMS, push
- event-driven workflows
- фоновые задачи и тяжёлую постобработку
- интеграции с внешними сервисами, которым нельзя доверять latency и uptime
- fan-out сценарии и массовую обработку событий

## Сравнительная таблица
| Критерий | Вариант A | Вариант B |
|----------|-----------|-----------|
| Простота reasoning | Выше | Ниже |
| Мгновенный ответ клиенту | Да | Обычно нет |
| Связанность сервисов | Выше | Ниже |
| Устойчивость к пикам | Ниже | Выше |
| Устойчивость к сбоям зависимостей | Ниже | Выше |
| Debugging | Проще | Сложнее |
| Consistency | Чаще сильнее | Чаще eventual |
| Operational complexity | Ниже | Выше |

## Реальные примеры
- **User profile service**: часто выбирают synchronous communication, потому что пользователь ждёт ответ прямо сейчас и операция обычно read-only.
- **Notification pipeline**: почти всегда выбирают asynchronous communication, потому что отправка email/push не должна блокировать бизнес-операцию.
- **Order placement**: часто используют гибрид — синхронно подтверждают приём заказа, а оплату, уведомления, аналитику и downstream side effects обрабатывают асинхронно.

## Как обсуждать на собеседовании
Слабый ответ — это догматичное “асинхронщина всегда лучше, потому что микросервисы”. Это ерунда. Сильный ответ — признать, что почти все реальные системы гибридные. User-facing critical path часто синхронный, потому что клиент ждёт результат. Heavy side effects и интеграции — асинхронные, потому что иначе система становится хрупкой. Ещё сильнее выглядит ответ, где кандидат проговаривает последствия: при async-модели нужны idempotency keys, retry policy, dead-letter queue, monitoring lag и понятные delivery guarantees. Если ты это не озвучил, значит ты описал не архитектуру, а картинку.

## Связанные темы
- [[ARCH-SYSDESIGN-001]] — chat system сочетает synchronous client interaction и asynchronous delivery pipeline
- [[ARCH-SYSDESIGN-002]] — notification service почти всегда строится на asynchronous processing
- [[ARCH-TRADEOFF-003]] — consistency vs latency тесно связан с выбором sync/async модели
