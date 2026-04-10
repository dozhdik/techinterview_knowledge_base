---
id: "ARCH-TRADEOFF-003"
title: "Consistency vs Latency"
domain: "arch"
category: "tradeoff"
tags:
  - consistency
  - latency
  - distributed_systems
  - replication
  - tradeoffs
difficulty: "senior"
roles:
  - "backend"
  - "devops"
  - "data_engineer"
  - "all_roles"
interview_stage:
  - "system_design"
  - "phone_screen"
frequency: "medium"
related:
  - "ARCH-COMPONENT-008"
  - "ARCH-TRADEOFF-002"
  - "ARCH-TRADEOFF-004"
prerequisites: []
sources:
  - "Martin Kleppmann — Designing Data-Intensive Applications"
  - "CAP Theorem resources"
  - "Google Spanner Paper"
author: "Инженер знаний №2"
version: "1.0"
date_created: "2026-04-10"
date_updated: "2026-04-10"
status: "review"
---

# Consistency vs Latency

## Суть компромисса
Компромисс между consistency и latency возникает в распределённых системах тогда, когда для более свежих и согласованных данных нужно больше координации между узлами, а координация почти всегда стоит времени. Если система ждёт подтверждений от нескольких реплик, проверяет quorum или требует read-after-write guarantees, задержка ответа растёт. Если же система отвечает быстро с ближайшей реплики или из локального кеша, возрастает риск stale reads и временных расхождений. Нельзя честно обещать одновременно минимальную latency, сильную согласованность и дешёвую геораспределённость без серьёзной цены. Поэтому сильный инженер не выбирает “всегда consistency” или “всегда latency”, а определяет, где stale data допустимы, а где они ломают бизнес.

## Вариант A
### Преимущества
- Более свежие и предсказуемые данные
- Проще reasoning о корректности бизнес-логики
- Лучше подходит для критичных операций: деньги, остатки, permissions
- Уменьшает число аномалий read-after-write и conflicting state

### Недостатки
- Более высокая latency
- Больше coordination overhead
- Хуже переносит сетевые проблемы и региональные задержки
- Может снижать availability при жёстких требованиях к согласованности

### Когда выбирать
- платежи и финансовые операции
- управление остатками, квотами, лимитами
- критичные ACL и permission checks
- сценарии, где stale data приводят к прямой бизнес-ошибке

## Вариант B
### Преимущества
- Быстрый ответ пользователю
- Лучше user experience на read-heavy path
- Выше throughput и проще масштабирование по регионам
- Хорошо подходит для кэшей, recommendations, social feeds и presence

### Недостатки
- Возможны stale reads
- Сложнее объяснять consistency guarantees
- Требуются механизмы reconciliation и правильные ожидания от системы
- Некоторые баги проявляются только под нагрузкой и в гонках

### Когда выбирать
- social feed
- presence / online status
- рекомендации и персонализация
- autocomplete, search ranking, analytics dashboards
- read-heavy сценарии, где небольшая устарелость допустима

## Сравнительная таблица
| Критерий | Вариант A | Вариант B |
|----------|-----------|-----------|
| Свежесть данных | Выше | Ниже |
| Время ответа | Хуже | Лучше |
| Throughput | Ниже | Выше |
| Геораспределённость | Сложнее | Проще |
| Fit для критичных операций | Лучше | Хуже |
| Tolerance к stale reads | Низкая | Высокая |

## Реальные примеры
- **Платёжная система**: выбирают более высокую consistency, потому что двойное списание или некорректный баланс недопустимы.
- **Social feed**: выбирают низкую latency, потому что пользователь не заметит, если один пост появится на секунду позже, но заметит тормозящий интерфейс.
- **Presence в чате**: обычно выбирают низкую latency и eventual consistency, потому что точность до миллисекунды не стоит дорогой координации.
- **Глобальная база с quorum reads/writes**: выбирают повышенную consistency там, где ошибка данных дороже, чем замедление ответа.

## Как обсуждать на собеседовании
Плохой ответ — это бросить “CAP theorem” и думать, что на этом разговор закончен. Нормальный ответ должен быть прикладным: какие именно операции требуют strong guarantees, какие можно обслуживать с replica или cache, где нужен read-your-writes, а где eventual consistency достаточно. Сильный кандидат говорит не абстрактно, а через примеры: баланс счёта — одно, лента новостей — другое. Ещё лучше — явно показать, что в одной системе могут coexist разные guarantees для разных путей: write path строже, read path быстрее. Если ты этого не проговариваешь, значит ты обсуждаешь лозунг, а не архитектуру.

## Связанные темы
- [[ARCH-COMPONENT-008]] — database replication напрямую создаёт компромисс между свежестью данных и задержкой
- [[ARCH-TRADEOFF-002]] — async-коммуникация часто увеличивает eventual consistency, но помогает latency и resilience
- [[ARCH-TRADEOFF-004]] — sharding и масштабирование тоже влияют на consistency model
