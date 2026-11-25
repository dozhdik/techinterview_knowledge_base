---
id: CS-PROBLEM-012
title: Shortest Path in Unweighted Graph
domain: cs
category: problem
tags:
- graphs
- bfs
- shortest_path
difficulty: junior
roles:
- all_roles
interview_stage:
- coding
frequency: medium
related:
- CS-CONCEPT-016
- CS-QUESTION-004
prerequisites:
- CS-CONCEPT-015
sources:
- Cormen et al. Introduction to Algorithms, 4th ed. (CLRS).
author: Команда TechInterview
version: '1.1'
date_created: '2026-11-23'
date_updated: '2026-11-23'
status: review
aliases:
  - "Кратчайший путь в невзвешенном графе"
---

# Shortest Path in Unweighted Graph

## Условие

Нужно найти минимальное число рёбер от исходной вершины до целевой.

## Главное

- BFS исследует расстояния по возрастанию.
- Массив родителей восстанавливает путь.
- Время O(V+E) на списках смежности.

## Как это работает

BFS начинает с исходной вершины и назначает расстояние соседу при первом посещении. Родитель позволяет восстановить маршрут, проходя от цели назад к старту.

## Пример

Если A связано с B и C, а B связано с D, BFS найдёт маршрут A→B→D длиной два ребра. Вершину D можно остановить после первого обнаружения.

## Границы и ошибки

Взвешенные рёбра требуют другой алгоритм; несколько одинаковых кратчайших путей допустимы. Если цель недостижима, не возвращайте фиктивную длину ноль.

## На собеседовании

Если рёбра имеют разные веса, обычный BFS уже не даёт правильный ответ.

## Связанные темы

- [[CS-CONCEPT-015]] — сначала повторить: Граф: представления и обход.
- [[CS-CONCEPT-016]] — Поиск в ширину BFS.
- [[CS-QUESTION-004]] — Когда выбирать BFS, а когда Дейкстру.

## Источник

- Cormen et al. Introduction to Algorithms, 4th ed. (CLRS).
