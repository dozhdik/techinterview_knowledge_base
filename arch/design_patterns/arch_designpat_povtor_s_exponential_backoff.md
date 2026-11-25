---
id: ARCH-DESIGNPAT-002
title: Повтор с exponential backoff
domain: arch
category: designpat
tags:
- retry
- backoff
- reliability
difficulty: middle
roles:
- all_roles
interview_stage:
- system_design
frequency: medium
related:
- ARCH-DESIGNPAT-001
- ARCH-DESIGNPAT-009
prerequisites: []
sources:
- 'Google Cloud Architecture Center: Reliability pillar — https://docs.cloud.google.com/architecture/framework/reliability'
author: Команда TechInterview
version: '1.1'
date_created: '2026-11-23'
date_updated: '2026-11-23'
status: review
aliases:
  - "Exponential Backoff Retry"
  - "Повтор с экспоненциальной задержкой"
---

# Повтор с exponential backoff

## Идея паттерна

После временной ошибки клиент повторяет запрос с растущими паузами и случайным разбросом.

## Главное

- Повторяйте только безопасные операции или используйте ключ идемпотентности.
- Ограничьте число попыток.
- Общий deadline важнее каждой отдельной паузы.

## Как устроено

При временной ошибке клиент повторяет попытку с растущей паузой, ограниченным числом попыток и случайным разбросом. Jitter снижает вероятность одновременного повторного всплеска от множества клиентов.

## Практический пример

После 503 сервис ждёт 100 мс, затем около 200 мс и 400 мс, но прекращает попытки по общему deadline.

## Ограничения

Не повторяйте бездумно неидемпотентную операцию: запрос мог успешно выполниться перед потерей ответа. Ошибки валидации обычно не исчезнут от повторения.

## На собеседовании

Разберите, почему одновременный повтор тысяч клиентов усиливает перегрузку.

## Связанные темы

- [[ARCH-DESIGNPAT-001]] — Идемпотентный обработчик.
- [[ARCH-DESIGNPAT-009]] — Бюджет времени и deadline.

## Источник

- Google Cloud Architecture Center: Reliability pillar — https://docs.cloud.google.com/architecture/framework/reliability
