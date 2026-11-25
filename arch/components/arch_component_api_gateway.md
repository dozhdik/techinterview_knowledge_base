---
id: "ARCH-COMPONENT-004"
title: "API Gateway"
domain: "arch"
category: "component"
tags:
  - api_gateway
  - microservices
  - routing
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
  - "ARCH-COMPONENT-001"   # Load Balancer (часто используется вместе)
  - "ARCH-COMPONENT-002"   # Cache (может кешировать ответы)
  - "ARCH-COMPONENT-003"   # Message Queue (асинхронная обработка)
  - "ARCH-TRADEOFF-003"    # Monolith vs Microservices (связанный компромисс)
  - "ARCH-SYSDESIGN-005"   # URL Shortener (пример использования)
prerequisites:
  - "CS-CONCEPT-028"       # Компьютерные сети
  - "ARCH-COMPONENT-001"   # Load Balancer
sources:
  - "Kleppmann M. Designing Data-Intensive Applications. Chapter 11. O'Reilly, 2017."
  - "Xu A. System Design Interview – An Insider's Guide. Chapter 6: API Gateway. ByteByteGo, 2020."
  - "Microservices.io. API Gateway Pattern. https://microservices.io/patterns/apigateway.html"
author: "Инженер знаний №2"
version: "1.0"
date_created: "2026-04-09"
date_updated: "2026-11-23"
status: "review"
aliases:
  - "Шлюз API"
  - "API-шлюз"
---

# API Gateway

## Определение
API Gateway — компонент распределённой системы, который выступает единой точкой входа для клиентских запросов в микросервисную архитектуру, обеспечивая маршрутизацию, аутентификацию, rate limiting, трансформацию протоколов и агрегацию ответов.

## Назначение
- **Единая точка входа**: клиенты общаются с одним эндпоинтом, не зная внутренней структуры сервисов
- **Маршрутизация**: перенаправление запросов к соответствующим микросервисам
- **Безопасность**: аутентификация, авторизация, SSL-терминация, защита от атак
- **Оптимизация**: rate limiting, кэширование, компрессия, агрегация ответов
- **Наблюдаемость**: централизованное логирование, метрики, трейсинг

## Типы API Gateway

| Тип | Описание | Примеры | Когда использовать |
| --- | --- | --- | --- |
| Basic Gateway | Простая маршрутизация + аутентификация | Kong Basic, Express Gateway | Небольшие проекты, быстрый старт |
| Full-Featured | Маршрутизация + rate limiting + кэш + трансформация | Kong, Apigee, AWS API Gateway | Продакшн-системы, много сервисов |
| Service Mesh Gateway | Интеграция с service mesh (Istio, Linkerd) | Istio Ingress Gateway | Сложные микросервисные системы |
| BFF (Backend for Frontend) | Отдельный gateway под каждый тип клиента | Custom implementation | Мобильное + веб + десктоп приложения |

## Ключевые функции

| Функция | Описание | Пример реализации |
| --- | --- | --- |
| Routing | Перенаправление /users → User Service, /orders → Order Service | Path-based routing, header-based routing |
| Authentication | Проверка JWT, OAuth, API keys | JWT validation, OAuth2 proxy |
| Rate Limiting | Ограничение запросов на клиент/ключ | Token bucket, fixed window |
| Caching | Кэширование частых ответов | Redis, in-memory cache |
| Request/Response Transformation | Конвертация форматов, версионирование | JSON ↔ XML, v1 → v2 mapping |
| Aggregation | Объединение ответов нескольких сервисов | GraphQL, custom aggregator |
| Circuit Breaker | Защита от каскадных сбоев | Hystrix, Resilience4j |
| Logging & Monitoring | Централизованный сбор метрик | Prometheus, ELK stack |

## Архитектура (упрощённая схема)
                ┌─────────────────┐
                │   Клиенты       │
                │ (Web, Mobile)   │
                └────────┬────────┘
                         │
                ┌────────▼────────┐
                │   API Gateway   │
                │  ┌───────────┐  │
                │  │ Auth      │  │
                │  │ Routing   │  │
                │  │ Rate Limit│  │
                │  │ Cache     │  │
                │  └───────────┘  │
                └───────┬─────────┘
                        │
    ┌───────────────────┼───────────────────┐
    ▼                   ▼                   ▼
┌──────────────┐ ┌───────────────┐ ┌───────────────┐
│ User Service │ │ Order Service │ │Product Service│
└───────┬──────┘ └───────┬───────┘ └───────┬───────┘
        │                │                 │
        ▼                ▼                 ▼
   [Database]       [Database]     [Cache + Database]

## Проблемы и решения

### 1. Single Point of Failure
**Проблема**: Если gateway падает — недоступна вся система

**Решения**:
- Горизонтальное масштабирование (несколько инстансов + LB)
- Health checks + auto-failover
- Graceful degradation (возвращать кэшированные ответы)

### 2. Performance Bottleneck
**Проблема**: Все запросы проходят через gateway → задержки

**Решения**:
- Асинхронная обработка (non-blocking I/O)
- Кэширование частых запросов
- Оптимизация цепочек вызовов (aggregation)

### 3. Configuration Complexity
**Проблема**: Много правил маршрутизации, сложно поддерживать

**Решения**:
- Declarative configuration (YAML/JSON)
- GitOps подход (конфиги в репозитории)
- Dynamic reload без перезапуска

### 4. Versioning & Backward Compatibility
**Проблема**: Как поддерживать старые версии API при обновлении сервисов

**Решения**:
- URL versioning: /v1/users, /v2/users
- Header-based versioning: Accept: application/vnd.api.v2+json
- Gateway трансформирует запросы между версиями

## Когда использовать

**Хорошие сценарии**:
- Микросервисная архитектура (10+ сервисов)
- Несколько типов клиентов (web, mobile, third-party)
- Нужна централизованная аутентификация/авторизация
- Требуется rate limiting и защита от атак

**Плохие сценарии**:
- Монолитное приложение (over-engineering)
- Очень низкие требования к latency (< 5ms)
- Маленькая команда, нет ресурсов на поддержку

## Сравнение с Load Balancer

| Критерий | Load Balancer | API Gateway |
| --- | --- | --- |
| Уровень работы | L4 (TCP) или L7 (HTTP) | Только L7 (HTTP/HTTPS) |
| Основная задача | Распределение нагрузки | Маршрутизация + бизнес-логика |
| Понимание контента | Минимальное (заголовки) | Глубокое (тело запроса, JWT) |
| Аутентификация | Нет (или базовая) | Полная (JWT, OAuth, API keys) |
| Трансформация | Нет | Да (форматы, версионирование) |

## Связанные темы

- [[ARCH-COMPONENT-001]] — Load Balancer (часто используется вместе)
- [[ARCH-COMPONENT-002]] — Cache (кеширование на уровне gateway)
- [[ARCH-COMPONENT-003]] — Message Queue (асинхронная обработка через gateway)
- [[ARCH-TRADEOFF-003]] — Monolith vs Microservices (контекст применения)
- [[ARCH-SYSDESIGN-005]] — URL Shortener (пример использования gateway)

## Источники

1. Kleppmann M. Designing Data-Intensive Applications. Chapter 11. O'Reilly, 2017.
2. Xu A. System Design Interview – An Insider's Guide. Chapter 6. ByteByteGo, 2020.
3. Microservices.io. API Gateway Pattern. https://microservices.io/patterns/apigateway.html
4. Kong Documentation. https://docs.konghq.com/
