---
id: CS-PROBLEM-009
title: Coin Change
domain: cs
category: problem
tags:
- dynamic_programming
- coding
difficulty: junior
roles:
- all_roles
interview_stage:
- coding
frequency: medium
related:
- CS-CONCEPT-020
- CS-PATTERN-011
prerequisites: []
sources:
- Cormen et al. Introduction to Algorithms, 4th ed. (CLRS).
author: Команда TechInterview
version: '1.1'
date_created: '2026-11-23'
date_updated: '2026-11-23'
status: review
aliases:
  - "Размен монет"
---

# Coin Change

## Условие

Даны номиналы и сумма; требуется минимальное число монет или признак невозможности.

## Главное

- dp[s] хранит минимум для суммы s.
- dp[0]=0.
- Перебор монет для каждого s даёт O(amount × number_of_coins).

## Как это работает

Пусть dp[s] — минимальное число монет для суммы s, а dp[0]=0. Для каждой достижимой суммы перебирайте номиналы и обновляйте ответ из dp[s-coin]+1.

## Пример

Для номиналов [1,3,4] и суммы 6 оптимально 3+3: жадный выбор 4+1+1 использует три монеты вместо двух.

## Границы и ошибки

Если сумма недостижима, возвращайте признак невозможности, а не бесконечность. Сложность O(amount × число номиналов) по времени и O(amount) по памяти.

## На собеседовании

Покажите пример, где жадный выбор крупнейшей монеты ошибается.

## Связанные темы

- [[CS-CONCEPT-020]] — Динамическое программирование.
- [[CS-PATTERN-011]] — Динамическое программирование: одно измерение.

## Источник

- Cormen et al. Introduction to Algorithms, 4th ed. (CLRS).
