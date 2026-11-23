---
id: CS-PROBLEM-007
title: Binary Tree Level Order Traversal
domain: cs
category: problem
tags:
- trees
- bfs
- coding
difficulty: junior
roles:
- all_roles
interview_stage:
- coding
frequency: medium
related:
- CS-CONCEPT-013
- CS-CONCEPT-016
prerequisites:
- CS-CONCEPT-001
sources:
- Cormen et al. Introduction to Algorithms, 4th ed. (CLRS).
author: Команда TechInterview
version: '1.1'
date_created: '2026-11-23'
date_updated: '2026-11-23'
status: review
---

# Binary Tree Level Order Traversal

## Условие

Нужно вернуть значения дерева по уровням слева направо.

## Главное

- BFS кладёт корень в очередь.
- Фиксируйте размер очереди перед обработкой слоя.
- Время O(n), память до O(w), где w — максимальная ширина.

## Как это работает

Для каждого уровня зафиксируйте длину очереди до добавления детей. Ровно столько узлов относятся к текущему уровню, даже если во время обработки очередь уже выросла.

## Пример

Для дерева с корнем 1 и детьми 2,3 результат [[1],[2,3]]. После извлечения корня оба ребёнка попадают в очередь следующего слоя.

## Границы и ошибки

При пустом дереве ответ пустой. Время O(n); очередь может хранить целый широкий уровень, поэтому память оценивают максимальной шириной, а не только высотой.

## На собеседовании

Проверьте пустое дерево и объясните, почему рекурсивная глубина тут не нужна.

## Связанные темы

- [[CS-CONCEPT-001]] — сначала повторить: Бинарное дерево поиска.
- [[CS-CONCEPT-013]] — Очередь и deque.
- [[CS-CONCEPT-016]] — Поиск в ширину BFS.

## Источник

- Cormen et al. Introduction to Algorithms, 4th ed. (CLRS).
