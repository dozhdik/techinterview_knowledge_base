---
id: CS-PROBLEM-010
title: Longest Substring Without Repeating Characters
domain: cs
category: problem
tags:
- strings
- sliding_window
- coding
difficulty: junior
roles:
- all_roles
interview_stage:
- coding
frequency: medium
related:
- CS-PATTERN-007
- CS-CONCEPT-009
prerequisites: []
sources:
- Cormen et al. Introduction to Algorithms, 4th ed. (CLRS).
author: Команда TechInterview
version: '1.1'
date_created: '2026-11-23'
date_updated: '2026-11-23'
status: review
---

# Longest Substring Without Repeating Characters

## Условие

Нужно найти длину самой длинной подстроки без повторяющихся символов.

## Главное

- Окно хранит текущую подстроку.
- При повторе сдвигайте левую границу за прошлое вхождение.
- Время O(n) при словаре позиций.

## Как это работает

Держите левую границу окна и словарь последней позиции символа. При повторе перемещайте left на максимум текущей позиции и следующей после прошлого вхождения.

## Пример

Для строки «abba» после второго b окно становится «b», а не возвращается к первому a; максимальная длина равна 2.

## Границы и ошибки

Не сдвигайте левую границу назад, если прежнее появление уже вне окна. Пустая строка даёт 0; уточните, считаются ли символы Unicode как кодовые точки или другая единица.

## На собеседовании

Проверьте пустую строку и повтор, расположенный уже вне окна.

## Связанные темы

- [[CS-PATTERN-007]] — Sliding Window для подстрок.
- [[CS-CONCEPT-009]] — Хеш-таблица.

## Источник

- Cormen et al. Introduction to Algorithms, 4th ed. (CLRS).
