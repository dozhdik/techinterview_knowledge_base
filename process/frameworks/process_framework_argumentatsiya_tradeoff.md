---
id: PROC-FRAMEWORK-006
title: Аргументация trade-off
domain: process
category: framework
tags:
- tradeoffs
- communication
- system_design
difficulty: middle
roles:
- all_roles
interview_stage:
- behavioral
frequency: high
related:
- ARCH-TRADEOFF-006
- PROC-FRAMEWORK-003
prerequisites:
- PROC-FRAMEWORK-005
sources:
- McDowell. Cracking the Coding Interview, 6th ed., 2015.
author: Команда TechInterview
version: '1.1'
date_created: '2026-11-23'
date_updated: '2026-11-23'
status: review
---

# Аргументация trade-off

## Подход

Объяснение выбора должно связывать требование, варианты и цену каждого варианта.

## Главное

- Назовите решающее ограничение.
- Сравните два подхода по одинаковым критериям.
- Сформулируйте риск и способ проверки.

## Как применять

Сначала назовите требование и варианты, затем критерии сравнения: согласованность, задержка, стоимость, сложность работы и риски. Завершите выбором для заданных условий и сигналом, когда его пересмотреть.

## Пример

Для чтения каталога кеш полезен при допустимой устарелости; для финального списания такой же кеш не должен быть единственным источником истины.

## Что проверить

Не называйте один вариант «лучшим» вне контекста. Покажите потерянное свойство и как продукт выдерживает эту цену.

## На собеседовании

Для SQL vs NoSQL покажите нагрузку, схему данных и требования к согласованности.

## Связанные темы

- [[PROC-FRAMEWORK-005]] — сначала повторить: Уточнение требований перед решением.
- [[ARCH-TRADEOFF-006]] — SQL vs NoSQL.
- [[PROC-FRAMEWORK-003]] — Фреймворк решения System Design задачи.

## Источник

- McDowell. Cracking the Coding Interview, 6th ed., 2015.
