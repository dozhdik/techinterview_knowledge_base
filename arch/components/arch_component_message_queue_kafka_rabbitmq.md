---
id: "ARCH-COMPONENT-003"
title: "Message Queue (Очередь сообщений)"
domain: "arch"
category: "component"
tags:
  - message_queue
  - async_processing
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
  - "ARCH-COMPONENT-001"   # Load Balancer (масштабирование потребителей)
  - "ARCH-COMPONENT-002"   # Cache (асинхронное обновление кеша)
  - "ARCH-COMPONENT-004"   # API Gateway (очередь для rate limiting)
  - "ARCH-TRADEOFF-001"    # Consistency vs Availability (eventual consistency)
prerequisites:
  - "CS-CONCEPT-028"       # Компьютерные сети
  - "CS-CONCEPT-013"       # Связный список (очередь как структура)
sources:
  - "Kleppmann M. Designing Data-Intensive Applications. Chapter 11: Stream Processing. O'Reilly, 2017."
  - "Xu A. System Design Interview – An Insider's Guide. Chapter 5: Message Queues. ByteByteGo, 2020."
  - "Kafka Documentation. https://kafka.apache.org/documentation/"
author: "Инженер знаний №2"
version: "1.0"
date_created: "2026-04-09"
date_updated: "2026-11-23"
status: "review"
aliases:
  - "Очередь сообщений"
  - "Message Queuing"
---

# Message Queue (Очередь сообщений)

## Определение
Message Queue (очередь сообщений) — компонент распределённой системы для асинхронной передачи данных между сервисами (producer → consumer), обеспечивающий decoupling, масштабируемость и надёжность обработки событий.

## Назначение
- **Асинхронная обработка**: разделение процессов отправки и обработки сообщений
- **Decoupling**: producer и consumer не знают друг о друге
- **Буферизация**: сглаживание пиковых нагрузок (load leveling)
- **Надёжность**: гарантированная доставка, retry механизмы
- **Масштабируемость**: независимое масштабирование producer/consumer

## Типы очередей

### По модели доставки

| Тип | Описание | Примеры | Когда использовать |
| --- | --- | --- | --- |
| Point-to-Point | Сообщение потребляется одним consumer | RabbitMQ, AWS SQS | Задачи, которые должны быть выполнены один раз |
| Pub/Sub | Сообщение доставляется всем подписчикам | Kafka, Redis Pub/Sub, AWS SNS | Broadcast событий, реальное время |

### По гарантии доставки

| Гарантия | Описание | Trade-off |
| --- | --- | --- |
| At most once | Сообщение может быть потеряно, но не дублируется | Низкая надёжность, высокая скорость |
| At least once | Сообщение не теряется, но может дублироваться | Надёжность, нужна идемпотентность |
| Exactly once | Сообщение доставляется ровно один раз | Сложность, производительность |

## Популярные реализации

| Система | Тип | Особенности | Use cases |
| --- | --- | --- | --- |
| **RabbitMQ** | Point-to-Point | AMQP protocol, routing, durable queues | Task queues, RPC |
| **Apache Kafka** | Pub/Sub | High throughput, log-based, partitioning | Event streaming, analytics |
| **AWS SQS** | Point-to-Point | Managed service, интеграция с AWS | Cloud-native apps |
| **Redis Pub/Sub** | Pub/Sub | In-memory, low latency | Real-time notifications |

## Архитектура (Producer-Consumer pattern)

            ┌─────────────┐
            │  Producer   │
            └──────┬──────┘
                   │
                   ▼
            ┌─────────────┐
            │Message Queue│
            │  (RabbitMQ) │
            └─────────────┘
                   │
    ┌──────────────┼──────────────┐
    ▼              ▼              ▼
┌───────────┐ ┌───────────┐ ┌───────────┐
│Consumer 1 │ │ Consumer 2│ │ Consumer 3│
└───────────┘ └───────────┘ └───────────┘

## Сценарии использования

### 1. Асинхронная обработка задач
**Пример**: Пользователь загружает видео → очередь → background worker конвертирует в разные форматы

**Преимущества**:
- Быстрый ответ пользователю
- Обработка в фоне
- Масштабирование workers

### 2. Event-driven архитектура
**Пример**: Order Service → событие "OrderCreated" → Notification Service, Inventory Service, Analytics Service

**Преимущества**:
- Loose coupling между сервисами
- Легко добавлять новых потребителей
- Fault isolation

### 3. Load leveling (сглаживание пиков)
**Пример**: Flash sale → 10000 запросов/сек → очередь → обработка по 1000/сек

**Преимущества**:
- Защита БД от перегрузки
- Предсказуемая нагрузка
- Graceful degradation

### 4. Retry и Dead Letter Queue
**Пример**: Отправка email → неудача → retry через 5 мин → DLQ после 3 попыток

**Преимущества**:
- Автоматическое восстановление
- Не теряются сообщения
- Отдельная обработка ошибок

## Проблемы и решения

### 1. Message Ordering
**Проблема**: Сообщения могут приходить не по порядку

**Решения**:
- Kafka: partitioning по key (один key → один partition → порядок сохраняется)
- RabbitMQ: single consumer queue
- Trade-off: масштабируемость vs порядок

### 2. Duplicate Messages
**Проблема**: At-least-once delivery → дубликаты

**Решения**:
- Идемпотентность consumer (проверка по message_id)
- Deduplication на уровне БД (unique constraint)
- Idempotent operations (PUT вместо POST)

### 3. Poison Pill Messages
**Проблема**: Сообщения, которые всегда падают при обработке

**Решения**:
- Dead Letter Queue (DLQ) после N попыток
- Alerting на DLQ
- Manual inspection и fix

### 4. Consumer Lag
**Проблема**: Consumers не успевают обрабатывать

**Решения**:
- Horizontal scaling (больше consumers)
- Оптимизация обработки
- Partitioning (Kafka)


## Когда использовать
✅ **Хорошие сценарии**:
- Асинхронная обработка (email, notifications)
- Интеграция микросервисов
- Сглаживание пиковых нагрузок
- Event sourcing, CQRS
- Background jobs

❌ **Плохие сценарии**:
- Синхронный request-response (лучше REST/gRPC)
- Низкая задержка критична (< 10ms)
- Простые приложения (over-engineering)

## Связанные темы

- [[ARCH-COMPONENT-001]] — Load Balancer (масштабирование consumers)
- [[ARCH-COMPONENT-002]] — Cache (асинхронное обновление)
- [[ARCH-COMPONENT-004]] — API Gateway (rate limiting через очередь)
- [[ARCH-TRADEOFF-001]] — Consistency vs Availability (eventual consistency)
- [[ARCH-SYSDESIGN-002]] — Notification Service (применение очереди)


## Источники
1. Kleppmann M. Designing Data-Intensive Applications. Chapter 11. O'Reilly, 2017.
2. Xu A. System Design Interview – An Insider's Guide. Chapter 5. ByteByteGo, 2020.
3. Kafka Documentation. https://kafka.apache.org/documentation/
4. RabbitMQ Patterns. https://www.rabbitmq.com/getstarted.html
