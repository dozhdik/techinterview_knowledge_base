---
id: ARCH-COMPONENT-016
title: Шина событий
domain: arch
category: component
tags:
- events
- messaging
- microservices
difficulty: middle
roles:
- all_roles
interview_stage:
- system_design
frequency: high
related:
- ARCH-COMPONENT-003
- ARCH-DESIGNPAT-006
prerequisites:
- ARCH-TRADEOFF-007
sources:
- Kleppmann. Designing Data-Intensive Applications, 2017.
author: Команда TechInterview
version: '1.1'
date_created: '2026-11-23'
date_updated: '2026-11-23'
status: review
aliases:
  - "Event Bus"
---

# Шина событий

## Назначение

Шина распространяет события об изменениях между независимыми потребителями.

## Главное

- Продюсер публикует факт, а не команду для каждого подписчика.
- Порядок и доставка зависят от брокера.
- Схема события требует версионирования.

## Как устроено

Шина событий доставляет сообщения между производителями и подписчиками, уменьшая прямую связанность сервисов. Потребитель обрабатывает событие асинхронно и хранит собственное состояние.

## Практический пример

После события OrderCreated отдельные обработчики отправляют уведомление и обновляют аналитику; сервис заказа не ждёт завершения обоих действий.

## Ограничения

Порядок, повторная доставка и изменение схемы события требуют явного контракта. Событие описывает уже произошедший факт и не заменяет синхронный ответ там, где он необходим.

## На собеседовании

На событии создания заказа назовите потребителей и их поведение при повторной доставке.

## Связанные темы

- [[ARCH-TRADEOFF-007]] — сначала повторить: Synchronous vs Asynchronous Communication.
- [[ARCH-COMPONENT-003]] — Message Queue (Очередь сообщений).
- [[ARCH-DESIGNPAT-006]] — Transactional Outbox.

## Источник

- Kleppmann. Designing Data-Intensive Applications, 2017.
