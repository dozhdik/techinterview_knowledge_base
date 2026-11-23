---
id: ARCH-DESIGNPAT-007
title: CQRS
domain: arch
category: designpat
tags:
- cqrs
- read_model
- architecture
difficulty: middle
roles:
- all_roles
interview_stage:
- system_design
frequency: medium
related:
- ARCH-COMPONENT-016
- ARCH-TRADEOFF-011
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

# CQRS

## Идея паттерна

CQRS разделяет модель записи команд и модель чтения запросов, если их требования сильно различаются.

## Главное

- Проекция чтения обновляется с задержкой.
- Усложняются синхронизация и отладка.
- Для простого CRUD разделение обычно избыточно.

## Как устроено

CQRS разделяет модель команд, меняющих состояние, и модель чтения, оптимизированную под запросы. Проекция чтения обновляется из событий или изменений основной модели.

## Практический пример

Заказ создаётся через транзакционную команду, а отдельная поисковая проекция собирает удобную карточку заказа для интерфейса.

## Ограничения

Разделение добавляет инфраструктуру и задержку между записью и чтением. Объясните пользователю и приложению гарантию read-your-writes, если проекция обновляется асинхронно.

## На собеседовании

Назовите ожидаемую задержку между записью и появлением в read-модели.

## Связанные темы

- [[ARCH-COMPONENT-009]] — сначала повторить: Реляционная база данных.
- [[ARCH-COMPONENT-016]] — Шина событий.
- [[ARCH-TRADEOFF-011]] — Строгая vs eventual consistency.

## Источник

- Kleppmann. Designing Data-Intensive Applications, 2017.
