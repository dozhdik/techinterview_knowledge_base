---
id: ARCH-DESIGNPAT-008
title: Cache-aside
domain: arch
category: designpat
tags:
- cache_aside
- caching
difficulty: middle
roles:
- all_roles
interview_stage:
- system_design
frequency: medium
related:
- ARCH-COMPONENT-002
- ARCH-TRADEOFF-015
prerequisites:
- ARCH-COMPONENT-009
sources:
- 'MDN Web Docs: HTTP caching — https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Caching'
author: Команда TechInterview
version: '1.1'
date_created: '2026-11-23'
date_updated: '2026-11-23'
status: review
---

# Cache-aside

## Идея паттерна

Приложение сначала читает кеш, а при промахе загружает данные из источника и кладёт их в кеш.

## Главное

- При изменении данных кеш нужно инвалидировать.
- TTL ограничивает срок устаревания.
- Одновременные промахи могут перегрузить БД.

## Как устроено

При cache-aside приложение сначала читает кеш, затем при промахе получает данные из БД и кладёт результат в кеш. После изменения данных приложение удаляет или обновляет соответствующий ключ.

## Практический пример

Карточка товара часто читается: первый запрос идёт в БД, остальные — в кеш. После смены цены удаляют старое значение, чтобы следующий запрос перечитал БД.

## Ограничения

Между изменением БД и инвалидацией возможно устаревшее чтение. TTL ограничивает срок ошибки, но не заменяет политику согласованности для критичных данных.

## На собеседовании

На чтении профиля покажите cache hit, miss и обновление после записи.

## Связанные темы

- [[ARCH-COMPONENT-009]] — сначала повторить: Реляционная база данных.
- [[ARCH-COMPONENT-002]] — Cache (Кеширование).
- [[ARCH-TRADEOFF-015]] — Кеширование vs свежесть данных.

## Источник

- MDN Web Docs: HTTP caching — https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Caching
