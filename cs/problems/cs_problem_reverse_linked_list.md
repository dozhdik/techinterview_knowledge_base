---
id: CS-PROBLEM-006
title: Reverse Linked List
domain: cs
category: problem
tags:
- linked_lists
- pointers
- coding
difficulty: junior
roles:
- all_roles
interview_stage:
- coding
frequency: medium
related:
- CS-CONCEPT-011
- CS-PATTERN-006
prerequisites: []
sources:
- Cormen et al. Introduction to Algorithms, 4th ed. (CLRS).
author: Команда TechInterview
version: '1.1'
date_created: '2026-11-23'
date_updated: '2026-11-23'
status: review
aliases:
  - "Разворот связного списка"
---

# Reverse Linked List

## Условие

Нужно развернуть односвязный список и вернуть новую голову.

## Главное

- Храните prev, current и next.
- Перед сменой ссылки сохраните исходный next.
- Время O(n), дополнительная память O(1).

## Как это работает

На каждом шаге сохраните next, перенаправьте current.next на prev и сдвиньте все три указателя. Старый head после обработки становится хвостом, а prev — новой головой.

## Пример

Для 1→2→3 последовательные шаги дадут 1→null, затем 2→1, затем 3→2; возвращается узел 3.

## Границы и ошибки

Не меняйте ссылку до сохранения next, иначе потеряете остаток списка. Пустой список и один узел должны возвращаться без особых побочных эффектов.

## На собеседовании

Проверьте пустой список, один узел и потерю хвоста при перепривязке.

## Связанные темы

- [[CS-CONCEPT-011]] — Связный список.
- [[CS-PATTERN-006]] — Two Pointers для массива.

## Источник

- Cormen et al. Introduction to Algorithms, 4th ed. (CLRS).
