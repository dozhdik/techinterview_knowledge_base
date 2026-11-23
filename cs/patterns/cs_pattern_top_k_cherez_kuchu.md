---
id: CS-PATTERN-009
title: Top K через кучу
domain: cs
category: pattern
tags:
- top_k
- heap
difficulty: middle
roles:
- all_roles
interview_stage:
- coding
frequency: high
related:
- CS-CONCEPT-014
- CS-PROBLEM-011
prerequisites:
- CS-CONCEPT-022
sources:
- Cormen et al. Introduction to Algorithms, 4th ed. (CLRS).
author: Команда TechInterview
version: '1.1'
date_created: '2026-11-23'
date_updated: '2026-11-23'
status: review
---

# Top K через кучу

## Идея паттерна

Куча из k элементов помогает удерживать k лучших кандидатов при потоке данных.

## Главное

- Мини-куча хранит текущий top k.
- Сложность обработки n элементов O(n log k).
- Для одного разового ответа возможен quickselect.

## Как это работает

Min-heap размера k удерживает k наибольших уже просмотренных элементов: вершина является наименьшей из выбранных. Новый элемент меньше вершины можно отбросить, больший — заменить.

## Пример

Для поиска трёх крупнейших чисел в потоке не нужно сортировать весь вход: храните только три кандидата и обновляйте их за O(log 3) на элемент.

## Границы и ошибки

Если k близко к n, полная сортировка может быть проще. Уточните, как считать дубликаты и что делать при k=0 или k больше числа элементов.

## На собеседовании

Выберите подход с учётом размера k и необходимости потоковой обработки.

## Связанные темы

- [[CS-CONCEPT-022]] — сначала повторить: Асимптотическая сложность Big O.
- [[CS-CONCEPT-014]] — Куча и приоритетная очередь.
- [[CS-PROBLEM-011]] — Kth Largest Element.

## Источник

- Cormen et al. Introduction to Algorithms, 4th ed. (CLRS).
