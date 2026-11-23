---
id: PROC-STRATEGY-007
title: План подготовки Middle Backend
domain: process
category: strategy
tags:
- backend
- preparation
- system_design
difficulty: middle
roles:
- all_roles
interview_stage:
- phone_screen
- coding
frequency: medium
related:
- ARCH-COMPONENT-009
- ARCH-COMPONENT-002
prerequisites:
- PROC-FRAMEWORK-003
sources:
- McDowell. Cracking the Coding Interview, 6th ed., 2015.
author: Команда TechInterview
version: '1.1'
date_created: '2026-11-23'
date_updated: '2026-11-23'
status: review
---

# План подготовки Middle Backend

## Цель

Для backend-роли среднего уровня нужны алгоритмы, БД и объяснение проектных решений.

## Главное

- Отработайте транзакции и индексы.
- Разберите API, кеш и очереди.
- Подготовьте истории о сделанных компромиссах.

## Как применять

План для middle backend должен сочетать кодирование, SQL, транзакции, сетевые API и простые архитектурные решения. После каждой темы переходите от определения к вопросу «какую проблему это решает и какой ценой».

## Пример

Разберите один медленный SQL-запрос через EXPLAIN, затем объясните, почему индекс помог или не помог; отдельно потренируйте схему кеширования API.

## Что проверить

Не оставляйте system design на последний день. Уровень middle обычно требует объяснить компромисс, а не просто перечислить знакомые инструменты.

## На собеседовании

За каждую архитектурную тему сформулируйте требования, выбранное решение и известный риск.

## Связанные темы

- [[PROC-FRAMEWORK-003]] — сначала повторить: Фреймворк решения System Design задачи.
- [[ARCH-COMPONENT-009]] — Реляционная база данных.
- [[ARCH-COMPONENT-002]] — Cache (Кеширование).

## Источник

- McDowell. Cracking the Coding Interview, 6th ed., 2015.
