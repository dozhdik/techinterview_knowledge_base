---
id: CS-PATTERN-007
title: Sliding Window для подстрок
domain: cs
category: pattern
tags:
- sliding_window
- strings
difficulty: middle
roles:
- all_roles
interview_stage:
- coding
frequency: high
related:
- CS-PROBLEM-010
- CS-PATTERN-004
prerequisites:
- CS-CONCEPT-009
sources:
- Cormen et al. Introduction to Algorithms, 4th ed. (CLRS).
author: Команда TechInterview
version: '1.1'
date_created: '2026-11-23'
date_updated: '2026-11-23'
status: review
---

# Sliding Window для подстрок

## Идея паттерна

Скользящее окно поддерживает свойства непрерывного фрагмента при движении границ.

## Главное

- Правая граница расширяет окно.
- Левая восстанавливает инвариант.
- При монотонном движении обеих границ время часто O(n).

## Как это работает

Окно задают полуоткрытым диапазоном [left, right). Правую границу расширяют, пока условие выполняется; при нарушении левую сдвигают и обновляют состояние, например счётчик символов.

## Пример

Для самой длинной подстроки без повторов храните последнее положение символа. При повторе сдвигайте left только вперёд, иначе уже исключённый символ ошибочно вернётся в окно.

## Границы и ошибки

Проверяйте пустую строку и повтор за пределами текущего окна. Оценка O(n) требует, чтобы каждая граница проходила строку не более одного раза.

## На собеседовании

На уникальной подстроке покажите, когда передвигать левую границу.

## Связанные темы

- [[CS-CONCEPT-009]] — сначала повторить: Хеш-таблица.
- [[CS-PROBLEM-010]] — Longest Substring Without Repeating Characters.
- [[CS-PATTERN-004]] — Prefix Sum и range query паттерны.

## Источник

- Cormen et al. Introduction to Algorithms, 4th ed. (CLRS).
