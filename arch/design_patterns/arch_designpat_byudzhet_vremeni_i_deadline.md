---
id: ARCH-DESIGNPAT-009
title: Бюджет времени и deadline
domain: arch
category: designpat
tags:
- timeouts
- latency
- reliability
difficulty: middle
roles:
- all_roles
interview_stage:
- system_design
frequency: medium
related:
- ARCH-DESIGNPAT-002
- ARCH-DESIGNPAT-003
prerequisites: []
sources:
- 'Google Cloud Architecture Center: Reliability pillar — https://docs.cloud.google.com/architecture/framework/reliability'
author: Команда TechInterview
version: '1.1'
date_created: '2026-11-23'
date_updated: '2026-11-23'
status: review
---

# Бюджет времени и deadline

## Идея паттерна

Deadline ограничивает общее время запроса через цепочку сервисов.

## Главное

- Каждый дочерний вызов получает остаток времени.
- Таймаут без отмены оставляет бесполезную работу.
- Ретраи расходуют общий бюджет.

## Как устроено

Общий deadline задаёт максимальное время всей операции; каждый вложенный вызов получает только оставшийся бюджет. Таймаут отдельного сервиса должен быть меньше или равен оставшемуся времени.

## Практический пример

Для ответа за 800 мс после 300 мс на БД остаётся 500 мс на внешнюю зависимость и формирование ответа. Повторять запрос ещё 700 мс уже бессмысленно.

## Ограничения

Без передачи deadline цепочка сервисов может продолжать работу после отказа клиента. Учитывайте очереди, повторы и отмену, а не только сетевой timeout.

## На собеседовании

Посчитайте, сколько времени остаётся второй попытке после первой задержки.

## Связанные темы

- [[ARCH-DESIGNPAT-002]] — Повтор с exponential backoff.
- [[ARCH-DESIGNPAT-003]] — Circuit Breaker.

## Источник

- Google Cloud Architecture Center: Reliability pillar — https://docs.cloud.google.com/architecture/framework/reliability
