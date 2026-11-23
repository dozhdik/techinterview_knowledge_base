---
id: ARCH-COMPONENT-025
title: Обработчик потоковых событий
domain: arch
category: component
tags:
- stream_processing
- events
- analytics
difficulty: middle
roles:
- all_roles
interview_stage:
- system_design
frequency: high
related:
- ARCH-TRADEOFF-013
- ARCH-SYSDESIGN-011
prerequisites:
- ARCH-COMPONENT-003
sources:
- Kleppmann. Designing Data-Intensive Applications, 2017.
author: Команда TechInterview
version: '1.1'
date_created: '2026-11-23'
date_updated: '2026-11-23'
status: review
---

# Обработчик потоковых событий

## Назначение

Потоковый обработчик непрерывно преобразует события и считает агрегаты.

## Главное

- Состояние и checkpoint помогают восстановиться.
- event time отличается от времени обработки.
- Поздние события меняют оконный результат.

## Как устроено

Обработчик потоковых событий читает упорядоченные порции данных, обновляет состояние и фиксирует прогресс обработки. Окна по времени события позволяют агрегировать данные, пришедшие не строго по порядку.

## Практический пример

Поток кликов агрегируется по минутам для панели метрик. Опоздавшее событие может изменить уже показанный счётчик, если окно ещё открыто.

## Ограничения

Нужно определить допустимое опоздание, повторную обработку и восстановление состояния после сбоя. Время обработки и время события дают разные результаты.

## На собеседовании

Для метрики за пять минут задайте правило обработки опоздавших событий.

## Связанные темы

- [[ARCH-COMPONENT-003]] — сначала повторить: Message Queue (Очередь сообщений).
- [[ARCH-TRADEOFF-013]] — Batch vs Stream Processing.
- [[ARCH-SYSDESIGN-011]] — Сервис аналитики событий.

## Источник

- Kleppmann. Designing Data-Intensive Applications, 2017.
