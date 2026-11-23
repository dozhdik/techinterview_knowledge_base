---
id: CS-PROBLEM-005
title: Two Sum
domain: cs
category: problem
tags:
- arrays
- hash_tables
- coding
difficulty: junior
roles:
- all_roles
interview_stage:
- coding
frequency: medium
related:
- CS-CONCEPT-009
- CS-CONCEPT-002
prerequisites: []
sources:
- Cormen et al. Introduction to Algorithms, 4th ed. (CLRS).
author: Команда TechInterview
version: '1.1'
date_created: '2026-11-23'
date_updated: '2026-11-23'
status: review
---

# Two Sum

## Условие

Даны массив и цель; требуется найти два разных индекса, сумма значений которых равна цели.

## Главное

- Хеш-таблица хранит ранее встреченные значения.
- Для текущего x ищут target-x.
- Среднее время O(n), память O(n).

## Как это работает

Просматривая массив слева направо, для каждого x ищите target-x среди ранее виденных значений. Проверка до добавления текущего x исключает использование одного индекса дважды.

## Пример

Для [2,7,11,15] и цели 9: после 2 в словаре лежит 2→0; при 7 находится дополнение 2, ответ — индексы 0 и 1.

## Границы и ошибки

При [3,3] и цели 6 нужны два разных индекса. Хеш-таблица даёт среднее O(n) время, но требует O(n) памяти; подход с сортировкой меняет задачу сохранения исходных индексов.

## На собеседовании

Проверьте дубликаты, например 3+3, и не используйте один индекс дважды.

## Связанные темы

- [[CS-CONCEPT-009]] — Хеш-таблица.
- [[CS-CONCEPT-002]] — Массив и динамический массив.

## Источник

- Cormen et al. Introduction to Algorithms, 4th ed. (CLRS).
