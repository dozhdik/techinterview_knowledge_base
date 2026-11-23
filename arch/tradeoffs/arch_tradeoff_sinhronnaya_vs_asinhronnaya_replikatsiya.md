---
id: ARCH-TRADEOFF-010
title: Синхронная vs асинхронная репликация
domain: arch
category: tradeoff
tags:
- replication
- consistency
- latency
difficulty: middle
roles:
- all_roles
interview_stage:
- system_design
frequency: medium
related:
- ARCH-COMPONENT-008
- ARCH-TRADEOFF-002
prerequisites:
- ARCH-COMPONENT-009
sources:
- Kleppmann. Designing Data-Intensive Applications, 2017.
author: Команда TechInterview
version: '1.1'
date_created: '2026-11-23'
date_updated: '2026-11-23'
status: review
---

# Синхронная vs асинхронная репликация

## Суть выбора

Синхронная репликация ждёт подтверждения реплики; асинхронная отвечает раньше и может отставать.

## Главное

- Синхронность улучшает гарантию сохранения подтверждённой записи ценой задержки и доступности.
- Асинхронность повышает скорость записи.
- failover требует учёта lag.

## Как устроено

Синхронная запись ждёт подтверждения реплики до ответа клиенту, снижая риск потери подтверждённой записи. Асинхронная отвечает раньше, но реплика может отставать и при аварии не иметь последних данных.

## Практический пример

Для критичной записи баланса выбирают более строгую гарантию; для журнала просмотров допустим небольшой replication lag ради скорости.

## Ограничения

Синхронность может уменьшать доступность при недоступной реплике. При failover заранее определите RPO, порядок выбора нового primary и судьбу неподтверждённых операций.

## На собеседовании

Спросите, сколько подтверждённых записей допустимо потерять при аварии.

## Связанные темы

- [[ARCH-COMPONENT-009]] — сначала повторить: Реляционная база данных.
- [[ARCH-COMPONENT-008]] — Database Replication.
- [[ARCH-TRADEOFF-002]] — Consistency vs Latency.

## Источник

- Kleppmann. Designing Data-Intensive Applications, 2017.
