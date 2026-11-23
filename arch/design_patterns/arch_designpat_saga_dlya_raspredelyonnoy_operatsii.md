---
id: ARCH-DESIGNPAT-005
title: Saga для распределённой операции
domain: arch
category: designpat
tags:
- saga
- transactions
- microservices
difficulty: middle
roles:
- all_roles
interview_stage:
- system_design
frequency: medium
related:
- ARCH-DESIGNPAT-006
- ARCH-SYSDESIGN-014
prerequisites:
- CS-CONCEPT-036
sources:
- Kleppmann. Designing Data-Intensive Applications, 2017.
author: Команда TechInterview
version: '1.1'
date_created: '2026-11-23'
date_updated: '2026-11-23'
status: review
---

# Saga для распределённой операции

## Идея паттерна

Saga разбивает операцию между сервисами на локальные транзакции с компенсациями.

## Главное

- Компенсация не всегда равна точному откату.
- Промежуточные состояния видимы.
- Шаги должны выдерживать повторы.

## Как устроено

Saga разбивает распределённую операцию на локальные транзакции и определяет компенсирующее действие для выполненных шагов. Координатор или цепочка событий фиксирует прогресс.

## Практический пример

Оформление заказа резервирует товар, затем списывает деньги. Если оплата не прошла, компенсация снимает резерв, а заказ помечается отменённым.

## Ограничения

Компенсация не всегда является точной «отменой»: письмо или внешний перевод нельзя просто стереть. Учитывайте повторы, порядок и наблюдаемость промежуточных состояний.

## На собеседовании

На оформлении заказа опишите резервирование, оплату и компенсацию при отказе.

## Связанные темы

- [[CS-CONCEPT-036]] — сначала повторить: Транзакция и commit/rollback.
- [[ARCH-DESIGNPAT-006]] — Transactional Outbox.
- [[ARCH-SYSDESIGN-014]] — Бронирование мест.

## Источник

- Kleppmann. Designing Data-Intensive Applications, 2017.
