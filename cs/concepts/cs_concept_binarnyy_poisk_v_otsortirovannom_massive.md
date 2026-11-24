---
id: CS-CONCEPT-018
title: Бинарный поиск в отсортированном массиве
domain: cs
category: concept
tags:
- binary_search
- arrays
- complexity
difficulty: middle
roles:
- all_roles
interview_stage:
- coding
frequency: high
related:
- CS-PATTERN-005
- CS-PITFALL-003
prerequisites:
- CS-CONCEPT-002
sources:
- Cormen et al. Introduction to Algorithms, 4th ed. (CLRS).
- "Python documentation: bisect — https://docs.python.org/3/library/bisect.html"
author: Команда TechInterview
version: '1.1'
date_created: '2026-11-23'
date_updated: '2026-11-24'
status: review
---

# Бинарный поиск в отсортированном массиве

## Определение

Бинарный поиск сокращает упорядоченный диапазон вдвое после каждого сравнения.

## Главное

- Время O(log n).
- Инвариант границ определяет ответ.
- Для первого подходящего элемента используют поиск левой границы.

## Как это работает

На каждом шаге поддерживается диапазон, в котором ещё может находиться ответ. Сравнение со средним элементом исключает половину диапазона; вариант «первый подходящий» сохраняет инвариант границы.

## Реализация левой границы

Для отсортированного по возрастанию массива ищем первый индекс, где значение не меньше `target`. Поддерживаем полуоткрытый диапазон `[left, right)`: всё левее `left` уже меньше цели, а ответ может находиться в диапазоне до `right` включительно как позиция вставки.

```python
def lower_bound(values, target):
    left, right = 0, len(values)
    while left < right:
        middle = left + (right - left) // 2
        if values[middle] < target:
            left = middle + 1
        else:
            right = middle
    return left
```

Функция возвращает `len(values)`, если подходящего элемента нет. Пустой массив возвращает 0. В итеративной реализации при доступе к элементу массива за O(1) нужно O(log n) сравнений и O(1) дополнительной памяти. Для проверки точного совпадения после поиска нужно дополнительно убедиться, что индекс меньше длины массива и элемент равен цели.

## Пример

В массиве [2, 4, 4, 7] поиск первого значения не меньше 4 возвращает индекс 1, а не любой индекс со значением 4.

## Границы и ошибки

До запуска проверьте сортировку и соглашение о границах: [left, right) или [left, right]. При дубликатах обычный поиск не обещает первое вхождение; пустой массив требует корректного завершения.

## На собеседовании

Проговорите, что массив отсортирован, и проверьте пустой массив и дубликаты.

## Связанные темы

- [[CS-CONCEPT-002]] — сначала повторить: Массив и динамический массив.
- [[CS-PATTERN-005]] — Binary Search на ответ (по пространству ответа).
- [[CS-PITFALL-003]] — Ошибка на границах бинарного поиска.

## Источник

- Cormen et al. Introduction to Algorithms, 4th ed. (CLRS).
- Python documentation: [bisect — Array bisection algorithm](https://docs.python.org/3/library/bisect.html).
