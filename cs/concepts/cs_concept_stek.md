---
id: CS-CONCEPT-012
title: Стек
domain: cs
category: concept
tags:
- stack
- data_structures
difficulty: middle
roles:
- all_roles
interview_stage:
- coding
frequency: high
related:
- CS-PROBLEM-001
- CS-CONCEPT-017
prerequisites: []
sources:
- Cormen et al. Introduction to Algorithms, 4th ed. (CLRS).
author: Команда TechInterview
version: '1.1'
date_created: '2026-11-23'
date_updated: '2026-11-23'
status: review
---

# Стек

## Определение

Стек выдаёт элементы в порядке LIFO: последним пришёл — первым ушёл.

## Главное

- push и pop обычно O(1).
- Подходит для скобок и обхода DFS.
- Переполнение рекурсивного стека зависит от глубины вызовов.

## Как это работает

Стек поддерживает push, pop и просмотр вершины. Он удобен там, где последняя открытая операция завершается первой: вложенные вызовы, скобки, возврат по пути поиска.

## Пример

При проверке «([])» открывающие скобки помещают в стек, а закрывающую сравнивают с вершиной. После обработки строки стек должен быть пустым.

## Границы и ошибки

Проверяйте pop на пустом стеке и оставшиеся открывающие скобки. Рекурсивный вызов тоже расходует стек, поэтому глубокий вход может привести к переполнению.

## На собеседовании

Покажите стек на примере проверки скобок и назовите крайний случай пустого стека.

## Связанные темы

- [[CS-PROBLEM-001]] — Valid Parentheses.
- [[CS-CONCEPT-017]] — Поиск в глубину DFS.

## Источник

- Cormen et al. Introduction to Algorithms, 4th ed. (CLRS).
