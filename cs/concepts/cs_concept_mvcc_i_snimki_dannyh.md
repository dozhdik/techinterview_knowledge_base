---
id: CS-CONCEPT-034
title: MVCC и снимки данных
domain: cs
category: concept
tags:
- mvcc
- transactions
- databases
difficulty: middle
roles:
- all_roles
interview_stage:
- coding
frequency: high
related:
- CS-CONCEPT-006
- CS-CONCEPT-036
prerequisites:
- CS-CONCEPT-035
sources:
- 'PostgreSQL documentation: Transaction Isolation — https://www.postgresql.org/docs/current/transaction-iso.html'
- 'PostgreSQL Documentation: MVCC — https://www.postgresql.org/docs/current/mvcc.html'
author: Команда TechInterview
version: '1.1'
date_created: '2026-11-23'
date_updated: '2026-11-23'
status: review
---

# MVCC и снимки данных

## Определение

MVCC хранит версии строк, чтобы чтения и записи могли сосуществовать с меньшим числом блокировок.

## Главное

- Транзакция видит версии по правилам уровня изоляции.
- Старые версии требуют очистки.
- MVCC сам по себе не устраняет все аномалии.

## Как это работает

MVCC хранит несколько версий строк; транзакция читает версии, видимые её снимку, вместо блокировки каждого чтения записью. Правила видимости зависят от СУБД и уровня изоляции.

## Пример

Читатель начинает запрос до обновления строки и видит прежнюю версию, пока писатель создаёт новую. После завершения транзакций устаревшие версии можно очистить.

## Границы и ошибки

MVCC сам по себе не гарантирует serializable и не отменяет конфликтующие записи. Долгие транзакции могут удерживать старые версии и увеличивать стоимость очистки.

## На собеседовании

Свяжите снимок с Repeatable Read и объясните, почему важны долгие транзакции.

## Связанные темы

- [[CS-CONCEPT-035]] — сначала повторить: ACID-свойства транзакций.
- [[CS-CONCEPT-006]] — Уровни изоляции транзакций в БД.
- [[CS-CONCEPT-036]] — Транзакция и commit/rollback.

## Источник

- PostgreSQL documentation: Transaction Isolation — https://www.postgresql.org/docs/current/transaction-iso.html
- PostgreSQL Documentation: MVCC — https://www.postgresql.org/docs/current/mvcc.html
