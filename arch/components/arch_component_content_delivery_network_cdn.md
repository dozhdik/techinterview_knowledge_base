---
id: "ARCH-COMPONENT-005"
title: "CDN (Content Delivery Network)"
domain: "arch"
category: "component"
tags:
  - cdn
  - caching
  - performance
  - scalability
  - must_know
  - core
difficulty: "junior"
roles:
  - backend
  - frontend
  - fullstack
  - devops
  - all_roles
interview_stage:
  - system_design
frequency: "high"
related:
  - "ARCH-COMPONENT-002"   # Cache (реляция: CDN — распределённый кеш)
  - "ARCH-COMPONENT-001"   # Load Balancer (часто используется вместе)
  - "ARCH-TRADEOFF-001"    # Consistency vs Availability (кеш и актуальность)
  - "ARCH-SYSDESIGN-005"   # URL Shortener (CDN для редиректов)
prerequisites:
  - "CS-CONCEPT-028"       # Компьютерные сети
  - "ARCH-COMPONENT-002"   # Cache (базовое понимание кеширования)
sources:
  - "Kleppmann M. Designing Data-Intensive Applications. Chapter 11. O'Reilly, 2017."
  - "Xu A. System Design Interview – An Insider's Guide. Chapter 4: Cache. ByteByteGo, 2020."
  - "Cloudflare Learning Center. What is a CDN? https://www.cloudflare.com/learning/cdn/what-is-a-cdn/"
author: "Инженер знаний №2"
version: "1.0"
date_created: "2026-04-09"
date_updated: "2026-11-23"
status: "review"
---

# CDN (Content Delivery Network)

## Определение
CDN (Content Delivery Network) — географически распределённая сеть серверов (edge nodes), которая кэширует и доставляет статический и динамический контент пользователям с ближайшего к ним узла, снижая задержку и нагрузку на исходный сервер.

## Назначение
- **Снижение latency**: доставка контента с edge-узла ближе к пользователю
- **Разгрузка origin**: уменьшение трафика и запросов к основному серверу
- **Повышение доступности**: распределённая архитектура устойчива к сбоям
- **Защита от атак**: DDoS mitigation, WAF на уровне edge

## Типы CDN

| Тип | Описание | Примеры | Когда использовать |
| --- | --- | --- | --- |
| Static CDN | Кэширование статики (изображения, CSS, JS) | Cloudflare, AWS CloudFront (static) | Веб-сайты, лендинги, блоги |
| Dynamic CDN | Ускорение динамического контента через оптимизацию маршрута | Cloudflare Argo, AWS CloudFront (dynamic) | API, персонализированный контент |
| Video CDN | Оптимизация для потокового видео (HLS, DASH) | Akamai, AWS Media Services | YouTube-like сервисы, стриминг |
| API CDN | Кэширование ответов API с TTL | Fastly, Varnish на edge | Публичные API, read-heavy endpoints |

## Алгоритмы доставки контента

| Алгоритм | Описание | Когда использовать |
| --- | --- | --- |
| Geo-based routing | Запрос идёт на ближайший по геолокации узел | Глобальная аудитория, снижение latency |
| Anycast routing | Один IP анонсируется из многих локаций, BGP направляет к ближайшему | DDoS защита, высокая доступность |
| Latency-based routing | Выбор узла по реальной задержке (RTT) | Динамический контент, чувствительный к latency |
| Cache hierarchy | L1 (edge) → L2 (regional) → Origin | Большие объёмы контента, экономия bandwidth |

## Архитектура (упрощённая схема)
                ┌─────────────────┐
                │   Пользователи  │
                │  (по всему миру)│
                └────────┬────────┘
                         │
                ┌────────▼────────┐
                │       DNS       │
                │ (Geo-resolution)│
                └────────┬────────┘
                         │
    ┌────────────────────┼────────────────────┐
    ▼                    ▼                    ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ Edge Node EU  │ │ Edge Node US  │ │ Edge Node AS  │
│ (cache hit)   │ │ (cache miss)  │ │ (cache hit)   │
└───────┬───────┘ └───────┬───────┘ └───────┬───────┘
        │                 │                 │
        │                 ▼                 │
        │         ┌─────────────────┐       │
        │         │ Origin Server   │       │
        │         │ (your app)      │       │
        │         └─────────────────┘       │
        │                 │                 │
        ▼                 ▼                 ▼
[Контент доставлен с edge] [Контент закэширован на edge]

## Проблемы и решения

### 1. Cache Invalidation (Актуализация контента)
**Проблема**: Пользователи видят устаревший контент после обновления на origin

**Решения**:
- **TTL-based**: автоматическое истечение кеша через N секунд
- **Purge API**: программная очистка кеша по URL/path/tag
- **Versioned URLs**: `style.v2.css` → новый хеш = новый кеш

### 2. Cache Stampede на edge
**Проблема**: Множество узлов одновременно запрашивают origin при истечении TTL

**Решения**:
- **Stale-while-revalidate**: отдавать устаревший кеш пока обновляется фон
- **Request coalescing**: объединять параллельные запросы к origin
- **Probabilistic early expiration**: случайное добавление к TTL

### 3. Dynamic Content Acceleration
**Проблема**: Персонализированный контент нельзя кэшировать на edge

**Решения**:
- **Route optimization**: выбор оптимального пути до origin (Anycast, BGP)
- **TCP optimizations**: keep-alive, congestion control на edge
- **Partial caching**: кэширование общих частей ответа

## Когда использовать

✅ **Хорошие сценарии**:
- Статический контент (изображения, CSS, JS, видео)
- Глобальная аудитория (пользователи в разных регионах)
- Пиковые нагрузки (защита origin от трафика)
- Публичные API с read-heavy паттерном

❌ **Плохие сценарии**:
- Контент, который должен быть всегда актуальным (< 1s freshness)
- Маленькая аудитория в одном регионе (оверинжиниринг)
- Частые изменения контента (низкий cache hit ratio)

## Связанные темы

- [[ARCH-COMPONENT-002]] — Cache (CDN — распределённый кеш, extends)
- [[ARCH-COMPONENT-001]] — Load Balancer (часто используется вместе, relates_to)
- [[ARCH-TRADEOFF-001]] — Consistency vs Availability (кеш и актуальность, relates_to)
- [[ARCH-SYSDESIGN-005]] — URL Shortener (CDN для редиректов, applied_in)

## Источники

1. Kleppmann M. Designing Data-Intensive Applications. Chapter 11. O'Reilly, 2017.
2. Xu A. System Design Interview – An Insider's Guide. Chapter 4. ByteByteGo, 2020.
3. Cloudflare Learning Center. What is a CDN? https://www.cloudflare.com/learning/cdn/
4. AWS CloudFront Documentation. https://docs.aws.amazon.com/cloudfront/
