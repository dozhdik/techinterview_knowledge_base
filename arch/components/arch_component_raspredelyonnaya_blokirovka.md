---
id: ARCH-COMPONENT-020
title: Распределённая блокировка
domain: arch
category: component
tags:
- distributed_lock
- concurrency
- reliability
difficulty: middle
roles:
- all_roles
interview_stage:
- system_design
frequency: high
related:
- ARCH-DESIGNPAT-001
- CS-CONCEPT-027
prerequisites:
- CS-CONCEPT-007
sources:
- Kleppmann. Designing Data-Intensive Applications, 2017.
- 'Redis Documentation: Distributed Locks — https://redis.io/docs/latest/manual/patterns/distributed-locks/'
author: Команда TechInterview
version: '1.1'
date_created: '2026-11-23'
date_updated: '2026-11-23'
status: review
aliases:
  - "Distributed Lock"
  - "Distributed Locking"
---

# Распределённая блокировка

## Назначение

Распределённая блокировка координирует несколько процессов, работающих с одним ресурсом.

## Главное

- Аренда имеет срок действия.
- Просроченный владелец может продолжить работу.
- fencing token защищает ресурс от старого владельца.

## Как устроено

Распределённая блокировка координирует процессы на разных узлах через общее хранилище. Аренда с TTL ограничивает время удержания, а fencing token помогает отвергать действия владельца с устаревшей арендой.

## Практический пример

Два воркера хотят обновить один отчёт: только один получает аренду. Если он завис и аренда истекла, второй продолжает работу с новым номером владения.

## Ограничения

Один TTL не гарантирует корректность: старый воркер может проснуться после истечения аренды. Для критичных записей нужна проверка fencing token в защищаемом ресурсе.

## На собеседовании

Поясните, почему одна блокировка не заменяет идемпотентность и транзакцию.

## Связанные темы

- [[CS-CONCEPT-007]] — сначала повторить: Deadlock: условия возникновения, обнаружение и предотвращение.
- [[ARCH-DESIGNPAT-001]] — Идемпотентный обработчик.
- [[CS-CONCEPT-027]] — Mutex и семафор.

## Источник

- Kleppmann. Designing Data-Intensive Applications, 2017.
- Redis Documentation: Distributed Locks — https://redis.io/docs/latest/manual/patterns/distributed-locks/
