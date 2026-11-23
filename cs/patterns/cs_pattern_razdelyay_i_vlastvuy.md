---
id: CS-PATTERN-010
title: Разделяй и властвуй
domain: cs
category: pattern
tags:
- divide_and_conquer
- recursion
difficulty: middle
roles:
- all_roles
interview_stage:
- coding
frequency: high
related:
- CS-CONCEPT-019
- CS-CONCEPT-010
prerequisites:
- CS-CONCEPT-021
sources:
- Cormen et al. Introduction to Algorithms, 4th ed. (CLRS).
author: Команда TechInterview
version: '1.1'
date_created: '2026-11-23'
date_updated: '2026-11-23'
status: review
---

# Разделяй и властвуй

## Идея паттерна

Подход делит задачу на меньшие независимые части и объединяет решения.

## Главное

- Есть стоимость разбиения и слияния.
- Рекуррентная оценка описывает время.
- Примеры — Merge Sort и Quick Sort.

## Как это работает

Задачу делят на меньшие независимые части, решают их и объединяют ответы. Время зависит не только от глубины рекурсии, но и от стоимости деления и объединения на каждом уровне.

## Пример

Merge Sort делит массив пополам и линейно сливает результаты. Бинарный поиск тоже уменьшает область, но продолжает только в одной половине.

## Границы и ошибки

Не всякое рекурсивное решение является эффективным divide and conquer: перекрывающиеся подзадачи могут многократно пересчитываться и требуют мемоизации.

## На собеседовании

Назовите базу рекурсии и оцените память, включая стек вызовов.

## Связанные темы

- [[CS-CONCEPT-021]] — сначала повторить: Рекурсия и стек вызовов.
- [[CS-CONCEPT-019]] — Сортировка слиянием Merge Sort.
- [[CS-CONCEPT-010]] — Quick Sort.

## Источник

- Cormen et al. Introduction to Algorithms, 4th ed. (CLRS).
