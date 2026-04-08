---
id: "PROC-STAGE-003"
title: "Coding Interview (Техническое интервью по кодированию)"
domain: "process"
category: "stage"
tags:
  - coding
  - technical_interview
  - algorithms
  - must_know
  - core
difficulty: "middle"
roles:
  - all_roles
interview_stage:
  - coding
frequency: "high"
related:
  - "PROC-STAGE-002"   # Phone Screen (предыдущий этап)
  - "PROC-FRAMEWORK-002"   # Problem Solving Framework
  - "PROC-PITFALL-003"   # Типичные ошибки на coding interview
prerequisites:
  - "PROC-STAGE-002"   # Phone Screen
sources:
  - "McDowell G.L. Cracking the Coding Interview. CareerCup, 2015."
  - "LeetCode. Interview Preparation. https://leetcode.com/explore/interview/"
author: "Инженер знаний №3"
version: "1.0"
date_created: "2026-04-09"
date_updated: "2026-04-09"
status: "draft"
---

# Coding Interview (Техническое интервью по кодированию)

## Определение
Coding Interview — основной технический этап, где кандидат решает алгоритмические задачи под наблюдением инженера. Проверяет problem-solving skills, знание структур данных и алгоритмов, качество кода.

## Формат
- **Длительность:** 45-60 минут
- **Формат:** Video call + Shared Editor
- **Инструменты:** CoderPad, CodeSignal, HackerRank
- **Задач:** 1-2 (зависит от сложности)

## Что оценивают

**Problem Solving (35%):**
- Понимание задачи
- Выбор правильного подхода
- Оптимизация решения

**Technical Knowledge (25%):**
- Знание структур данных
- Знание алгоритмов
- Применение паттернов

**Coding (25%):**
- Чистота и читаемость
- Правильность реализации
- Обработка edge cases

**Communication (15%):**
- Объяснение хода мыслей
- Реакция на подсказки
- Ответы на вопросы

## Типичные задачи по категориям

**Arrays & Strings (30%):**
- Two Sum, Three Sum
- Best Time to Buy and Sell Stock
- Product of Array Except Self
- Longest Substring Without Repeating Characters

**Trees & Graphs (25%):**
- Binary Tree Level Order Traversal
- Validate BST
- Number of Islands
- Lowest Common Ancestor

**Dynamic Programming (20%):**
- Climbing Stairs
- Coin Change
- Longest Increasing Subsequence
- Word Break

**Linked Lists (10%):**
- Reverse Linked List
- Merge Two Sorted Lists
- Linked List Cycle

**Heaps & Intervals (10%):**
- Merge Intervals
- Top K Frequent Elements
- Kth Largest Element

## Алгоритм решения задачи

**1. UNDERSTAND (5 мин)**
- Переформулировать задачу своими словами
- Задать уточняющие вопросы:
  • Входные данные (формат, ограничения)
  • Выходные данные
  • Edge cases
- Привести 2-3 примера

**2. EXAMPLES (3 мин)**
- Написать примеры input/output
- Включить edge cases:
  • Пустой input
  • Один элемент
  • Отрицательные числа
  • Дубликаты

**3. BRUTE FORCE (5 мин)**
- Описать наивное решение
- Написать псевдокод
- Проанализировать сложность: Time и Space
- Объяснить почему не оптимально

**4. OPTIMIZE (7 мин)**
- Найти bottleneck
- Применить паттерн/структуру данных
- Описать оптимизированный подход
- Пересчитать сложность

**5. CODE & TEST (25 мин)**
- Написать чистый код
- Комментировать сложные части
- Протестировать на примерах
- Исправить баги

## Уровни сложности

| Уровень | Задачи | Темы |
|---------|--------|------|
| **Junior** | Easy → Medium | Arrays, Strings, Hash Tables, Basic Trees |
| **Middle** | Medium | DP основы, Graphs, Heaps, Advanced Patterns |
| **Senior** | Medium → Hard | Complex DP, Optimization, System Design + Coding |

## Чек-лист подготовки

**Технические темы:**
- [ ] Arrays & Strings (основные операции)
- [ ] Hash Tables (когда использовать)
- [ ] Two Pointers паттерн
- [ ] Sliding Window паттерн
- [ ] Binary Search
- [ ] BFS/DFS для деревьев и графов
- [ ] Dynamic Programming (основы)
- [ ] Time/Space complexity (Big O)

**Практика:**
- [ ] Решить 50-75 задач на LeetCode
- [ ] 40% Easy, 50% Medium, 10% Hard
- [ ] Практиковаться объяснять решение вслух
- [ ] Использовать online editor (без autocomplete)

**Перед интервью:**
- [ ] Подготовить тихое место
- [ ] Протестировать shared editor
- [ ] Иметь бумагу и ручку для заметок
- [ ] Подготовить вопросы интервьюеру

## Типичные ошибки

❌ **Молча писать код**
- 15 минут тишины, потом «всё, готово»
- ✅ Постоянно комментировать действия

❌ **Сразу писать оптимальное решение**
- Пытаться сразу придумать O(n)
- ✅ Начать с brute force, затем оптимизировать

❌ **Не задавать уточняющие вопросы**
- Сразу писать код без понимания
- ✅ «Массив отсортирован?», «Могут ли быть дубликаты?»

❌ **Игнорировать edge cases**
- Код работает только на идеальных данных
- ✅ Проверить: пустой массив, null, очень большие числа

❌ **Не тестировать код**
- «Надеюсь, что работает»
- ✅ Протестировать на 2-3 примерах включая edge cases

## Критерии прохождения

✅ **Прошёл (Strong Hire/Hire):**
- Решил задачу правильно
- Объяснил ход мыслей
- Учёл edge cases
- Проанализировал сложность
- Задал хорошие вопросы

⚠️ **На грани (Weak Hire):**
- Решил с подсказками
- Код работает но не оптимален
- Плохо объяснял

❌ **Не прошёл (No Hire):**
- Не решил задачу
- Фундаментальные пробелы в знаниях
- Не мог объяснить подход

## Что дальше?

После coding interview → System Design Interview (для Middle+) → Behavioral Interview → Offer

## Связанные темы

- [[PROC-STAGE-002]] — Phone Screen (предыдущий этап)
- [[PROC-STAGE-004]] — System Design Interview (следующий этап)
- [[PROC-FRAMEWORK-002]] — Problem Solving Framework
- [[CS-PATTERN-001]] — Two Pointers
- [[CS-PATTERN-002]] — Sliding Window

## Источники

1. McDowell G.L. Cracking the Coding Interview. 2015.
2. LeetCode. Interview Preparation.
3. NeetCode. Problem Patterns.