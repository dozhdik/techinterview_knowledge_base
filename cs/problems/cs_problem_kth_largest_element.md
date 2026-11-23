---
id: CS-PROBLEM-011
title: Kth Largest Element
domain: cs
category: problem
tags:
- heap
- top_k
- coding
difficulty: junior
roles:
- all_roles
interview_stage:
- coding
frequency: medium
related:
- CS-CONCEPT-014
- CS-PATTERN-009
prerequisites: []
sources:
- Cormen et al. Introduction to Algorithms, 4th ed. (CLRS).
author: Команда TechInterview
version: '1.1'
date_created: '2026-11-23'
date_updated: '2026-11-23'
status: review
---

# Kth Largest Element

## Условие

Нужно найти k-й по величине элемент массива без обязательной полной сортировки.

## Главное

- Куча размера k даёт O(n log k) и O(k) памяти.
- quickselect в среднем O(n), но имеет худший случай O(n²) без специальных мер.

## Как это работает

Один способ — min-heap из k элементов: всё меньше вершины отбрасывается. Альтернатива quickselect переставляет элементы вокруг опорного и ищет нужный ранг без полной сортировки.

## Пример

Для [3,2,1,5,6,4] и k=2 ответ 5. В куче после прохода остаются два крупнейших числа, и её вершина равна 5.

## Границы и ошибки

Проверьте диапазон k и политику дубликатов. Quickselect имеет среднее O(n), но обычный выбор опорного не гарантирует это в худшем случае.

## На собеседовании

Уточните, считаются ли дубликаты отдельными позициями в ранжировании.

## Связанные темы

- [[CS-CONCEPT-014]] — Куча и приоритетная очередь.
- [[CS-PATTERN-009]] — Top K через кучу.

## Источник

- Cormen et al. Introduction to Algorithms, 4th ed. (CLRS).
