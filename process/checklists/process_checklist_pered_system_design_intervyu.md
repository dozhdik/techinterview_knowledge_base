---
id: PROC-CHECKLIST-004
title: Перед System Design интервью
domain: process
category: checklist
tags:
- system_design
- checklist
- preparation
difficulty: junior
roles:
- all_roles
interview_stage:
- phone_screen
- coding
frequency: medium
related:
- PROC-FRAMEWORK-003
- PROC-FRAMEWORK-008
prerequisites:
- PROC-STAGE-004
sources:
- McDowell. Cracking the Coding Interview, 6th ed., 2015.
author: Команда TechInterview
version: '1.1'
date_created: '2026-11-23'
date_updated: '2026-11-23'
status: review
---

# Перед System Design интервью

## Цель проверки

Чек-лист помогает быстро перейти от условий к архитектурному обсуждению.

## Главное

- Повторите оценку нагрузки и порядок уточнения требований.
- Подготовьте блок-схему.
- Освежите кэш, очереди и хранение.

## Как применять

Подготовьте порядок ответа: требования, оценка нагрузки, API и модель данных, общий дизайн, узкие места и отказоустойчивость. Выберите несколько знакомых систем для тренировки полного объяснения.

## Пример

На задаче URL Shortener сначала уточните объём чтений и срок жизни ссылок, затем обсудите генерацию ключа, хранилище и кеш.

## Что проверить

Не начинайте с выбора технологии без требований. Оставьте время на вопросы интервьюера и честно обозначайте допущения по нагрузке.

## На собеседовании

Попросите уточнить ожидаемый масштаб и главный критерий успеха системы.

## Связанные темы

- [[PROC-STAGE-004]] — сначала повторить: System Design Interview (Интервью по проектированию систем).
- [[PROC-FRAMEWORK-003]] — Фреймворк решения System Design задачи.
- [[PROC-FRAMEWORK-008]] — Проверка архитектурного решения.

## Источник

- McDowell. Cracking the Coding Interview, 6th ed., 2015.
