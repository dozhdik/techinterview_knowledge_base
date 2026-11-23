---
id: CS-CONCEPT-013
title: Очередь и deque
domain: cs
category: concept
tags:
- queue
- deque
- data_structures
difficulty: middle
roles:
- all_roles
interview_stage:
- coding
frequency: high
related:
- CS-CONCEPT-016
- CS-PROBLEM-007
prerequisites: []
sources:
- 'Python documentation: Data Structures — https://docs.python.org/3/tutorial/datastructures.html'
author: Команда TechInterview
version: '1.1'
date_created: '2026-11-23'
date_updated: '2026-11-23'
status: review
---

# Очередь и deque

## Определение

Очередь работает по FIFO; deque эффективно добавляет и удаляет элементы с обоих концов.

## Главное

- enqueue и dequeue обычно O(1).
- BFS использует очередь фронта.
- Обычный список с удалением начала может стоить O(n).

## Как это работает

FIFO-очередь добавляет элемент в хвост и извлекает из головы; deque поддерживает обе стороны. Для O(1) операций используют связную структуру или кольцевой буфер, а не сдвиг элементов обычного массива.

## Пример

В BFS стартовую вершину ставят в очередь, затем извлекают её и добавляют ещё не посещённых соседей. Так вершины обрабатываются по расстоянию в рёбрах.

## Границы и ошибки

Не путайте очередь с приоритетной очередью: последняя выбирает по ключу, а не по времени добавления. Пустая очередь и повторное добавление вершины требуют явной обработки.

## На собеседовании

На графе объясните, почему очередь даёт обход по уровням.

## Связанные темы

- [[CS-CONCEPT-016]] — Поиск в ширину BFS.
- [[CS-PROBLEM-007]] — Binary Tree Level Order Traversal.

## Источник

- Python documentation: Data Structures — https://docs.python.org/3/tutorial/datastructures.html
