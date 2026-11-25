---
id: PROC-FRAMEWORK-010
title: Postmortem без поиска виноватых
domain: process
category: framework
tags:
- postmortem
- learning
- reliability
difficulty: middle
roles:
- all_roles
interview_stage:
- behavioral
frequency: high
related:
- PROC-BEHAVIORAL-009
- PROC-SOFTSKILL-007
prerequisites: []
sources:
- 'Google Cloud Architecture Center: Reliability pillar — https://docs.cloud.google.com/architecture/framework/reliability'
author: Команда TechInterview
version: '1.1'
date_created: '2026-11-23'
date_updated: '2026-11-23'
status: review
aliases:
  - "Blameless Postmortem"
  - "Разбор инцидента без поиска виноватых"
---

# Postmortem без поиска виноватых

## Подход

Разбор сбоя фиксирует факты, влияние, причины и меры против повторения.

## Главное

- Отделите таймлайн от предположений.
- Ищите системные причины.
- Каждому действию назначьте владельца и проверку результата.

## Как применять

Postmortem отделяет фактическую временную шкалу от предположений, показывает влияние на пользователей и разбирает системные условия сбоя. Результатом становятся действия с владельцами и сроками.

## Пример

После падения из-за неверной настройки фиксируют обнаружение, откат, причину прохождения настройки без проверки и задачу добавить валидацию перед выкладкой.

## Что проверить

Поиск виновного мешает сообщать о рисках. Но отсутствие обвинений не отменяет ответственности за выполнение конкретных последующих действий.

## На собеседовании

На интервью расскажите, что команда изменила после инцидента.

## Связанные темы

- [[PROC-BEHAVIORAL-009]] — Ошибка в продакшене.
- [[PROC-SOFTSKILL-007]] — Ответственность за результат.

## Источник

- Google Cloud Architecture Center: Reliability pillar — https://docs.cloud.google.com/architecture/framework/reliability
