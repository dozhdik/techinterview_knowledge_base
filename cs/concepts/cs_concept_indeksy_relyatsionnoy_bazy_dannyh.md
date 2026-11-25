---
id: CS-CONCEPT-032
title: Индексы реляционной базы данных
domain: cs
category: concept
tags:
- indexes
- sql
- databases
difficulty: middle
roles:
- all_roles
interview_stage:
- coding
frequency: high
related:
- CS-CONCEPT-025
- CS-QUESTION-006
prerequisites:
- CS-CONCEPT-035
sources:
- 'PostgreSQL documentation: Transaction Isolation — https://www.postgresql.org/docs/current/transaction-iso.html'
author: Команда TechInterview
version: '1.1'
date_created: '2026-11-23'
date_updated: '2026-11-23'
status: review
aliases:
  - "Relational Database Indexes"
---

# Индексы реляционной базы данных

## Определение

Индекс ускоряет поиск нужных строк ценой дополнительного хранения и обслуживания при изменениях.

## Главное

- B-tree полезен для равенства и диапазонов.
- Составной индекс зависит от порядка столбцов и запроса.
- План запроса нужно проверять через EXPLAIN.

## Как это работает

Индекс хранит структуру поиска по значениям столбца и ссылки на строки. Планировщик выбирает между индексным и последовательным чтением по статистике и ожидаемой стоимости, а не по факту наличия индекса.

## Пример

Для WHERE user_id = 42 индекс по user_id может избежать просмотра всей таблицы. Для ORDER BY created_at составной индекс пригодится только при подходящем порядке столбцов и условиях.

## Границы и ошибки

Индекс занимает место и обновляется при записи. Если фильтр возвращает большую долю таблицы, последовательное чтение может быть быстрее; проверяйте план EXPLAIN и реальные измерения.

## На собеседовании

Покажите, почему индекс не гарантирует ускорение выборки большей части таблицы.

## Связанные темы

- [[CS-CONCEPT-035]] — сначала повторить: ACID-свойства транзакций.
- [[CS-CONCEPT-025]] — B-tree и индекс базы данных.
- [[CS-QUESTION-006]] — Когда индекс не ускоряет SQL-запрос.

## Источник

- PostgreSQL documentation: Transaction Isolation — https://www.postgresql.org/docs/current/transaction-iso.html
