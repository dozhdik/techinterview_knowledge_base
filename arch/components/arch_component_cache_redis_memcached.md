---
id: "ARCH-COMPONENT-002"
title: "Cache (Кеширование)"
domain: "arch"
category: "component"
tags:
  - caching
  - performance
  - scalability
  - must_know
  - core
difficulty: "junior"
roles:
  - backend
  - fullstack
  - devops
  - all_roles
interview_stage:
  - system_design
  - coding
frequency: "high"
related:
  - "ARCH-COMPONENT-001"   # Load Balancer (часто используется вместе)
  - "ARCH-COMPONENT-004"   # API Gateway (может кешировать на уровне gateway)
  - "ARCH-TRADEOFF-001"    # Consistency vs Availability (кеш влияет на консистентность)
prerequisites:
  - "CS-CONCEPT-009"       # Hash Table (структура данных для кеша)
sources:
  - "Kleppmann M. Designing Data-Intensive Applications. Chapter 6: Replication & Chapter 11: Stream Processing. O'Reilly, 2017."
  - "Xu A. System Design Interview – An Insider's Guide. Chapter 4: Cache. ByteByteGo, 2020."
  - "Redis Documentation. https://redis.io/docs/"
author: "Инженер знаний №2"
version: "1.0"
date_created: "2026-04-09"
date_updated: "2026-11-23"
status: "review"
aliases:
  - "Кэширование"
  - "Caching"
---

# Cache (Кеширование)

## Определение
Cache (кеш) — компонент распределённой системы для временного хранения часто запрашиваемых данных в быстрой памяти с целью снижения задержки, уменьшения нагрузки на основные источники данных (БД) и повышения общей производительности системы.

## Назначение
- **Снижение latency**: доступ к данным из памяти (O(1)) вместо диска или сети
- **Уменьшение нагрузки**: защита БД от избыточных запросов (cache hit)
- **Повышение масштабируемости**: возможность обслуживать больше RPS
- **Улучшение UX**: быстрый отклик приложения для пользователя

## Типы кеширования

### По месту размещения

| Тип | Описание | Примеры | Когда использовать |
| --- | --- | --- | --- |
| Client-side | Кеш на стороне клиента (браузер, мобильное приложение) | Browser Cache, LocalStorage, CDN | Статичный контент, редко меняющиеся данные |
| Server-side (Application) | Кеш внутри приложения | In-memory cache (HashMap), Guava Cache | Данные, специфичные для инстанса |
| Server-side (Distributed) | Выделенный кеш-сервис | Redis, Memcached | Общие данные между инстансами, масштабируемость |
| Database | Встроенный кеш БД | Query Cache (MySQL), Buffer Pool | Часто выполняемые запросы |
| CDN | Географически распределённый кеш | Cloudflare, AWS CloudFront | Статика (изображения, CSS, JS) для глобальной аудитории |

### По стратегии обновления

| Стратегия | Описание | Плюсы | Минусы |
| --- | --- | --- | --- |
| Cache-aside (Lazy Loading) | Приложение сначала проверяет кеш, при miss — читает из БД и записывает в кеш | Простота, данные загружаются только по запросу | Первый запрос всегда медленный (cache miss) |
| Write-through | Запись одновременно в кеш и БД | Консистентность, быстрый последующий read | Высокая задержка записи |
| Write-behind (Write-back) | Запись сначала в кеш, асинхронно в БД | Низкая задержка записи | Риск потери данных при сбое |
| Refresh-ahead | Активное обновление кеша до истечения TTL | Всегда актуальные данные | Сложность реализации, нагрузка |

## Алгоритмы вытеснения (Eviction Policies)

| Алгоритм | Описание | Когда использовать |
| --- | --- | --- |
| LRU (Least Recently Used) | Вытесняет давно не используемые элементы | Общий случай, хорошая эвристика |
| LFU (Least Frequently Used) | Вытесняет редко используемые элементы | Когда важна частота, а не время |
| FIFO (First In First Out) | Вытесняет по порядку добавления | Простые сценарии |
| Random | Случайный выбор | Когда все элементы равновероятны |
| TTL (Time To Live) | Автоматическое истечение по времени | Временные данные, сессии |

## Проблемы и решения

### 1. Cache Invalidation (Актуализация кеша)
**Проблема**: данные в кеше устарели относительно БД

**Решения**:
- **TTL**: автоматическое истечение через N секунд
- **Manual invalidation**: явная очистка при обновлении
- **Versioned keys**: `user:123:v1` → `user:123:v2`

### 2. Cache Stampede (Thundering Herd)
**Проблема**: множество запросов одновременно попадают на БД при истечении кеша

**Решения**:
- **Probabilistic early expiration**: случайное добавление к TTL
- **Locking**: блокировка на время обновления кеша
- **Background refresh**: асинхронное обновление

### 3. Cache Penetration
**Проблема**: запросы к несуществующим ключам постоянно попадают в БД

**Решения**:
- **Bloom Filter**: проверка существования ключа
- **Cache null values**: кеширование факта отсутствия

## Когда использовать

✅ **Хорошие сценарии**:
- Read-heavy workload (много чтений, мало записей)
- Дорогие вычисления или запросы
- Данные, которые редко меняются
- Пиковые нагрузки (защита БД)

❌ **Плохие сценарии**:
- Данные постоянно меняются (низкий cache hit ratio)
- Write-heavy workload
- Данные должны быть всегда актуальны (строгая консистентность)

## Связанные темы

- [[ARCH-COMPONENT-001]] — Load Balancer (распределение нагрузки на кеш-кластер)
- [[ARCH-COMPONENT-003]] — Message Queue (асинхронное обновление кеша)
- [[ARCH-TRADEOFF-001]] — Consistency vs Availability (компромисс при кешировании)
- [[CS-CONCEPT-009]] — Hash Table (структура данных для in-memory кеша)

## Источники

1. Kleppmann M. Designing Data-Intensive Applications. Chapter 6. O'Reilly, 2017.
2. Xu A. System Design Interview – An Insider's Guide. Chapter 4. ByteByteGo, 2020.
3. Redis Documentation. https://redis.io/docs/
4. Martin Fowler. Caching Patterns. https://martinfowler.com/bliki/CachingPattern.html
