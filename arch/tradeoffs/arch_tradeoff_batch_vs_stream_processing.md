---
id: ARCH-TRADEOFF-013
title: Batch vs Stream Processing
domain: arch
category: tradeoff
tags:
- batch
- streaming
- analytics
difficulty: middle
roles:
- all_roles
interview_stage:
- system_design
frequency: medium
related:
- ARCH-COMPONENT-025
- ARCH-COMPONENT-026
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

# Batch vs Stream Processing

## Суть выбора

Batch обрабатывает накопленные данные порциями; stream считает по мере поступления событий.

## Главное

- Batch обычно проще повторить и пересчитать.
- stream уменьшает задержку результата, но усложняет состояние и поздние события.
- Один продукт может использовать оба.

## Как устроено

Batch обрабатывает конечный набор данных по расписанию; stream обрабатывает непрерывные события близко ко времени поступления. Batch проще повторить целиком, stream быстрее обновляет результат, но сложнее при опоздании событий.

## Практический пример

Ночной отчёт по продажам можно строить пакетно. Для обнаружения мошенничества по текущим транзакциям нужна обработка с меньшей задержкой.

## Ограничения

Сравните цену инфраструктуры, требуемую свежесть и способ пересчёта при ошибке. Даже потоковым системам часто нужен пакетный backfill исторических данных.

## На собеседовании

Уточните SLA свежести отчёта, прежде чем выбирать обработку.

## Связанные темы

- [[ARCH-COMPONENT-003]] — сначала повторить: Message Queue (Очередь сообщений).
- [[ARCH-COMPONENT-025]] — Обработчик потоковых событий.
- [[ARCH-COMPONENT-026]] — Хранилище аналитических данных.

## Источник

- Kleppmann. Designing Data-Intensive Applications, 2017.
