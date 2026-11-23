---
id: ARCH-DESIGNPAT-006
title: Transactional Outbox
domain: arch
category: designpat
tags:
- outbox
- events
- transactions
difficulty: middle
roles:
- all_roles
interview_stage:
- system_design
frequency: medium
related:
- ARCH-COMPONENT-003
- ARCH-DESIGNPAT-001
prerequisites:
- CS-CONCEPT-036
sources:
- Kleppmann. Designing Data-Intensive Applications, 2017.
- 'AWS Prescriptive Guidance: Transactional Outbox — https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html'
author: Команда TechInterview
version: '1.1'
date_created: '2026-11-23'
date_updated: '2026-11-23'
status: review
---

# Transactional Outbox

## Идея паттерна

Transactional outbox записывает событие в ту же БД-транзакцию, что и изменение бизнес-данных.

## Главное

- Отдельный процесс публикует событие из outbox.
- Доставка может повторяться.
- Потребитель должен выдерживать дубли.

## Как устроено

Transactional Outbox записывает бизнес-изменение и сообщение для отправки в одной локальной транзакции БД. Отдельный процесс публикует сообщение и отмечает его обработанным.

## Практический пример

При создании заказа запись orders и outbox_event появляются вместе. Даже если брокер временно недоступен, отправитель повторит публикацию позже.

## Ограничения

Сообщение может быть опубликовано повторно, если сбой случился после публикации до отметки. Потребители должны быть идемпотентными; следите за задержкой outbox.

## На собеседовании

Покажите, почему запись в БД и публикация в брокер без outbox может разойтись.

## Связанные темы

- [[CS-CONCEPT-036]] — сначала повторить: Транзакция и commit/rollback.
- [[ARCH-COMPONENT-003]] — Message Queue (Очередь сообщений).
- [[ARCH-DESIGNPAT-001]] — Идемпотентный обработчик.

## Источник

- Kleppmann. Designing Data-Intensive Applications, 2017.
- AWS Prescriptive Guidance: Transactional Outbox — https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html
