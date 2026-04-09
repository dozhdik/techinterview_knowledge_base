---
id: "PROC-STAGE-002"
title: "Phone Screen (Технический телефонный скрининг)"
domain: "process"
category: "stage"
tags:
  - phone_screen
  - technical_interview
  - coding
  - must_know
  - core
difficulty: "junior"
roles:
  - all_roles
interview_stage:
  - phone_screen
  - coding
frequency: "high"
related:
  - "PROC-STAGE-001"   # HR Screening (предыдущий этап)
  - "PROC-STAGE-003"   # Coding Interview (следующий этап)
  - "PROC-FRAMEWORK-002"   # Problem Solving Framework
prerequisites:
  - "PROC-STAGE-001"   # HR Screening
sources:
  - "McDowell G.L. Cracking the Coding Interview. CareerCup, 2015."
  - "LeetCode Discuss. Phone Screen Interview Experiences."
author: "Инженер знаний №3"
version: "1.0"
date_created: "2026-04-09"
date_updated: "2026-04-09"
status: "approved"
---

# Phone Screen (Технический телефонный скрининг)

## Определение
Phone Screen — технический скрининг, проводимый инженером или техлидом. Цель: проверка базовых технических знаний и навыков решения задач перед полноценным technical interview.

## Формат
- **Длительность:** 30-45 минут
- **Формат:** Phone / Video call + Shared Editor
- **Инструменты:** CoderPad, CodeSignal, Google Docs
- **Участники:** кандидат + инженер/техлид

## Что оценивают

**Технические навыки:**
- Базовые алгоритмы и структуры данных
- Умение писать работающий код
- Понимание сложности алгоритмов (Big O)

**Problem-solving:**
- Подход к решению задач
- Умение декомпозировать проблему
- Оптимизация решений

**Коммуникация:**
- Способность объяснять ход мыслей
- Умение задавать уточняющие вопросы
- Реакция на подсказки

## Типичные вопросы

**Технические:**
- «Расскажите о вашем опыте с [технология из JD]»
- «Объясните [концепцию] простыми словами» (REST, индексы в БД, процесс vs поток)

**Coding задачи:**
- Сложность: Easy → Easy/Medium
- Количество: 1-2 задачи
- Время: 20-25 минут на задачу

**Частые темы:**
- Arrays & Strings, Hash Tables, Two Pointers
- Sliding Window, Binary Search, Basic BFS/DFS

**Примеры задач:**
- Two Sum, Valid Palindrome, Maximum Subarray

## Алгоритм решения задачи

1. **ПОНЯТЬ (2-3 мин):** Переформулировать, задать вопросы, привести примеры
2. **ПОДУМАТЬ (3-5 мин):** Brute force → оптимизация, озвучивать ход мыслей
3. **КОДИТЬ (10-15 мин):** Чистый код, комментарии, объяснять действия
4. **ТЕСТИРОВАТЬ (3-5 мин):** Примеры + edge cases (пустой массив, null)
5. **СЛОЖНОСТЬ (2 мин):** Time O(...), Space O(...)

## Чек-лист подготовки

**Темы:**
- [ ] Arrays & Strings, Hash Tables
- [ ] Two Pointers, Sliding Window
- [ ] Binary Search, Basic BFS/DFS
- [ ] Big O notation

**Практика:**
- [ ] 20-30 задач Easy на LeetCode
- [ ] 10-15 задач Medium
- [ ] Объяснять решения вслух

**Перед интервью:**
- [ ] Тихое место, хороший интернет
- [ ] Протестировать shared editor
- [ ] Подготовить вопросы интервьюеру

## Типичные ошибки

❌ **Молча писать код** — интервьюер не видит ход мыслей
✅ Комментировать каждый шаг

❌ **Сразу писать оптимальное решение** — пропускаешь brute force
✅ Начать с наивного, затем оптимизировать

❌ **Не задавать уточняющие вопросы** — пишешь код без понимания
✅ «Массив отсортирован?», «Могут ли быть дубликаты?»

❌ **Игнорировать edge cases** — код падает на пустом входе
✅ Проверить: пустой массив, null, очень большие числа

## Критерии прохождения

✅ **Прошёл:** Решил правильно, объяснил ход мыслей, учёл edge cases, проанализировал сложность

⚠️ **На грани:** Решил с подсказками, код работает но не оптимален

❌ **Не прошёл:** Не решил, фундаментальные пробелы, не мог объяснить подход

## Что дальше?

Phone Screen → Coding Interview (45-60 мин) → System Design / Behavioral

## Связанные темы

- [[PROC-STAGE-001]] — HR Screening (предыдущий этап)
- [[PROC-STAGE-003]] — Coding Interview (следующий этап)
- [[PROC-FRAMEWORK-002]] — Problem Solving Framework
- [[CS-PATTERN-001]] — Two Pointers
- [[CS-PATTERN-002]] — Sliding Window

## Источники

1. McDowell G.L. Cracking the Coding Interview. 2015.
2. LeetCode Discuss. Phone Screen Interview Experiences.