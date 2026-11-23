---
id: ARCH-TRADEOFF-015
title: Кеширование vs свежесть данных
domain: arch
category: tradeoff
tags:
- caching
- freshness
- consistency
difficulty: middle
roles:
- all_roles
interview_stage:
- system_design
frequency: medium
related:
- ARCH-COMPONENT-002
- ARCH-DESIGNPAT-008
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

# Кеширование vs свежесть данных

## Суть выбора

Кеш снижает задержку и нагрузку, но может вернуть устаревшее значение.

## Главное

- TTL ограничивает возраст записи лишь при выполнении условий обновления.
- Инвалидация делает систему сложнее.
- Критичные инварианты проверяют в источнике истины.

## Как устроено

Кеш сокращает нагрузку и задержку чтения, сохраняя копию данных ближе к клиенту. Чем дольше живёт копия, тем выше риск прочитать устаревшее состояние после записи.

## Практический пример

Каталог товаров может жить в кеше минуты, а остаток последней единицы товара проверяется в основном хранилище перед оплатой.

## Ограничения

Определите допустимую устарелость по операциям, TTL и инвалидацию. Cache stampede при массовом истечении ключей требует защиты отдельным механизмом.

## На собеседовании

Для профиля и остатка товара задайте разные требования к свежести.

## Связанные темы

- [[ARCH-COMPONENT-009]] — сначала повторить: Реляционная база данных.
- [[ARCH-COMPONENT-002]] — Cache (Кеширование).
- [[ARCH-DESIGNPAT-008]] — Cache-aside.

## Источник

- MDN Web Docs: HTTP caching — https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Caching
