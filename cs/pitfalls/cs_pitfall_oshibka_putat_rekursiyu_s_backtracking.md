---
id: "CS-PITFALL-001"
title: "Ошибка: путать рекурсию с backtracking"
domain: "cs"
category: "pitfall"
tags:
  - recursion
  - backtracking
  - algorithms
  - must_know
difficulty: "middle"
roles:
  - "all_roles"
interview_stage:
  - "coding"
  - "phone_screen"
frequency: "medium"
related:
  - "CS-PATTERN-002"
prerequisites: []
sources:
  - "Cormen T.H. et al. Introduction to Algorithms (CLRS), 4th Edition"
  - "Kleinberg J., Tardos É. Algorithm Design"
  - "LeetCode Discuss / Backtracking (вторичные разборы)"
author: "Инженер знаний №1"
version: "1.0"
date_created: "2026-04-08"
date_updated: "2026-04-09"
status: "review"
---

# Ошибка: путать рекурсию с backtracking

## Описание

Кандидат видит рекурсивную задачу и сразу называет решение backtracking, хотя на самом деле использует обычную рекурсию или DFS без выбора, проверки ограничений и отката состояния. Это ошибка, потому что backtracking — не синоним рекурсии. Backtracking — это более узкий паттерн: рекурсивный перебор с ветвлением, проверкой допустимости и возвратом назад после пробного выбора.

## На каком этапе возникает

- **Coding interview**
- **Задачи на permutations, combinations, subsets, N-Queens, word search, generate parentheses**
- **Любые задачи, где кандидат слышал слово “рекурсия” и начинает называть всё подряд backtracking**

## Почему это проблема

Для интервьюера это сигнал, что кандидат знает термин, но не понимает его границы. Обычная рекурсия может просто вычислять функцию, спускаться по дереву или обходить структуру. Backtracking же предполагает:
- наличие множества вариантов выбора;
- построение частичного решения;
- проверку, можно ли продолжать;
- откат состояния после возврата из ветви.

Если кандидат не различает эти вещи, он хуже распознаёт паттерны задач и часто выбирает слишком тяжёлый или слишком запутанный подход. В интервью это быстро проявляется: человек либо не может объяснить, где именно происходит pruning, либо вообще не делает undo и просто пишет рекурсивный код наугад.

## Пример ошибки

Кандидат говорит:

> “Это задача на backtracking, потому что тут есть рекурсия.”

И показывает что-то вроде:

```python
def factorial(n):
    if n == 0:
        return 1
    return n * factorial(n - 1)
