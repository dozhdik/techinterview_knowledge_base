---
id: CS-CONCEPT-036
title: Транзакция и commit/rollback
domain: cs
category: concept
tags:
- transactions
- databases
difficulty: middle
roles:
- all_roles
interview_stage:
- coding
frequency: high
related:
- CS-CONCEPT-035
- CS-CONCEPT-006
prerequisites: []
sources:
- 'PostgreSQL documentation: Transaction Isolation — https://www.postgresql.org/docs/current/transaction-iso.html'
author: Команда TechInterview
version: '1.1'
date_created: '2026-11-23'
date_updated: '2026-11-23'
status: review
aliases:
  - "Database Transactions and Commit/Rollback"
  - "Транзакции базы данных и фиксация/откат"
---

# Транзакция и commit/rollback

## Определение

Транзакция объединяет операции в единицу работы с фиксацией или откатом.

## Главное

- Commit делает изменения постоянными по гарантиям СУБД.
- rollback отменяет незавершённые изменения.
- Длинные транзакции удерживают ресурсы.

## Как это работает

Транзакция объединяет несколько операций до commit или rollback. До commit изменения могут быть видимы самой транзакции, а для других сессий правила задаёт уровень изоляции.

## Пример

Создание заказа и резервирование остатка выполняют в одной транзакции: при ошибке резерва rollback отменяет создание. После commit приложение получает подтверждение согласованного состояния.

## Границы и ошибки

Не держите транзакцию открытой во время долгого сетевого вызова: это удерживает блокировки и версии. Отправку внешнего сообщения согласуйте отдельно, например через outbox.

## На собеседовании

На переводе денег покажите необходимость атомарного изменения двух счетов.

## Связанные темы

- [[CS-CONCEPT-035]] — ACID-свойства транзакций.
- [[CS-CONCEPT-006]] — Уровни изоляции транзакций в БД.

## Источник

- PostgreSQL documentation: Transaction Isolation — https://www.postgresql.org/docs/current/transaction-iso.html
