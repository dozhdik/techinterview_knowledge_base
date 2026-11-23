---
id: ARCH-COMPONENT-017
title: Сбор метрик, логов и трассировок
domain: arch
category: component
tags:
- observability
- metrics
- logging
difficulty: middle
roles:
- all_roles
interview_stage:
- system_design
frequency: high
related:
- ARCH-SYSDESIGN-012
- ARCH-COMPONENT-001
prerequisites: []
sources:
- 'Google Cloud Architecture Center: Reliability pillar — https://docs.cloud.google.com/architecture/framework/reliability'
author: Команда TechInterview
version: '1.1'
date_created: '2026-11-23'
date_updated: '2026-11-23'
status: review
---

# Сбор метрик, логов и трассировок

## Назначение

Наблюдаемость объединяет числовые метрики, журналы событий и трассы запросов.

## Главное

- Метрики показывают тенденцию.
- Логи дают детали ошибки.
- Трасса связывает путь запроса через сервисы.

## Как устроено

Метрики показывают численное состояние, логи фиксируют отдельные события, трассировки связывают путь запроса через сервисы. Общие идентификаторы запроса помогают перейти от всплеска ошибок к конкретному вызову.

## Практический пример

Рост p95 задержки виден на графике; trace показывает медленный запрос к БД, а лог с тем же trace ID раскрывает ошибку параметра.

## Ограничения

Сбор всего подряд дорог и может раскрыть персональные данные. Определите полезные сигналы, срок хранения, выборку трасс и правила удаления чувствительной информации.

## На собеседовании

Укажите latency, error rate и saturation для критического API и объясните алерт.

## Связанные темы

- [[ARCH-SYSDESIGN-012]] — Платформа логирования.
- [[ARCH-COMPONENT-001]] — Load Balancer (Балансировщик нагрузки).

## Источник

- Google Cloud Architecture Center: Reliability pillar — https://docs.cloud.google.com/architecture/framework/reliability
