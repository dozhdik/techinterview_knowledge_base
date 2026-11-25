---
id: ARCH-DESIGNPAT-003
title: Circuit Breaker
domain: arch
category: designpat
tags:
- circuit_breaker
- reliability
difficulty: middle
roles:
- all_roles
interview_stage:
- system_design
frequency: medium
related:
- ARCH-DESIGNPAT-004
- ARCH-COMPONENT-017
prerequisites:
- ARCH-DESIGNPAT-009
sources:
- 'Google Cloud Architecture Center: Reliability pillar — https://docs.cloud.google.com/architecture/framework/reliability'
author: Команда TechInterview
version: '1.1'
date_created: '2026-11-23'
date_updated: '2026-11-23'
status: review
aliases:
  - "Прерыватель цепи"
---

# Circuit Breaker

## Идея паттерна

Circuit breaker временно прекращает вызовы отказавшей зависимости после порога ошибок.

## Главное

- Закрытое состояние пропускает запросы.
- Открытое быстро отказывает.
- Пробное полузакрытое проверяет восстановление.

## Как устроено

Circuit breaker наблюдает ошибки вызовов и временно прекращает обращаться к зависимому сервису после порога отказов. Через паузу пробные запросы проверяют восстановление.

## Практический пример

Если платёжный провайдер не отвечает, сервис быстро возвращает контролируемую ошибку вместо накопления ожидающих запросов. После восстановления путь открывается постепенно.

## Ограничения

Неверный порог создаёт ложные отключения или не защищает от каскада. Circuit breaker не заменяет таймауты и ограничение параллелизма.

## На собеседовании

Назовите fallback и объясните, как не считать ошибки пользователя сбоем зависимости.

## Связанные темы

- [[ARCH-DESIGNPAT-009]] — сначала повторить: Бюджет времени и deadline.
- [[ARCH-DESIGNPAT-004]] — Bulkhead.
- [[ARCH-COMPONENT-017]] — Сбор метрик, логов и трассировок.

## Источник

- Google Cloud Architecture Center: Reliability pillar — https://docs.cloud.google.com/architecture/framework/reliability
