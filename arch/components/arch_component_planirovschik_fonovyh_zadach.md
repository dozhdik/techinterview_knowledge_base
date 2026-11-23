---
id: ARCH-COMPONENT-015
title: Планировщик фоновых задач
domain: arch
category: component
tags:
- scheduler
- jobs
- reliability
difficulty: middle
roles:
- all_roles
interview_stage:
- system_design
frequency: high
related:
- ARCH-DESIGNPAT-001
- ARCH-COMPONENT-003
prerequisites: []
sources:
- 'Google Cloud Architecture Center: Well-Architected Framework — https://docs.cloud.google.com/architecture/framework'
author: Команда TechInterview
version: '1.1'
date_created: '2026-11-23'
date_updated: '2026-11-23'
status: review
---

# Планировщик фоновых задач

## Назначение

Планировщик запускает периодические или отложенные задания вне пользовательского запроса.

## Главное

- Нужны учёт пропущенных запусков и повторов.
- Несколько воркеров могут стартовать одно задание.
- Идемпотентность снижает вред дублей.

## Как устроено

Планировщик хранит задания и назначает исполнителям время запуска или повторения. Исполнитель отдельно подтверждает результат; при сбоях возможен повтор задачи, поэтому действие должно быть идемпотентным.

## Практический пример

Ночью задача пересчитывает отчёт. После падения исполнителя планировщик возвращает незавершённое задание в очередь, не теряя его навсегда.

## Ограничения

«Запустить ровно один раз» трудно гарантировать при сетевых сбоях. Определите задержку, допустимые дубли, дедлайн и политику задач, пропущенных во время простоя.

## На собеседовании

Объясните, где хранится расписание и кто отвечает за повтор после сбоя.

## Связанные темы

- [[ARCH-DESIGNPAT-001]] — Идемпотентный обработчик.
- [[ARCH-COMPONENT-003]] — Message Queue (Очередь сообщений).

## Источник

- Google Cloud Architecture Center: Well-Architected Framework — https://docs.cloud.google.com/architecture/framework
