---
id: ARCH-DESIGNPAT-004
title: Bulkhead
domain: arch
category: designpat
tags:
- bulkhead
- isolation
- reliability
difficulty: middle
roles:
- all_roles
interview_stage:
- system_design
frequency: medium
related:
- ARCH-DESIGNPAT-003
- ARCH-COMPONENT-028
prerequisites: []
sources:
- 'Google Cloud Architecture Center: Reliability pillar — https://docs.cloud.google.com/architecture/framework/reliability'
author: Команда TechInterview
version: '1.1'
date_created: '2026-11-23'
date_updated: '2026-11-23'
status: review
---

# Bulkhead

## Идея паттерна

Bulkhead выделяет отдельные лимиты ресурсов для разных видов нагрузки.

## Главное

- Один перегруженный маршрут не должен исчерпать все потоки.
- Лимиты нужны и на очередь.
- Отказ части функций может сохранить главное.

## Как устроено

Bulkhead отделяет ресурсы разных операций или зависимостей: отдельные пулы потоков, соединений или лимиты параллельных запросов. Перегрузка одного пути тогда не съедает все ресурсы процесса.

## Практический пример

Медленный сервис рекомендаций занимает свой небольшой пул, а оформление заказа сохраняет доступ к собственному пулу и не ждёт освобождения общих воркеров.

## Ограничения

Изоляция уменьшает максимальную совместно используемую ёмкость. Подберите размеры пулов по нагрузке и определите поведение при заполнении очереди.

## На собеседовании

Разделите пулы для оплаты и рекомендаций и опишите поведение при перегрузке.

## Связанные темы

- [[ARCH-DESIGNPAT-003]] — Circuit Breaker.
- [[ARCH-COMPONENT-028]] — Пул соединений с БД.

## Источник

- Google Cloud Architecture Center: Reliability pillar — https://docs.cloud.google.com/architecture/framework/reliability
