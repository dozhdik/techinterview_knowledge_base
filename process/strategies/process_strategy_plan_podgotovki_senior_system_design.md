---
id: PROC-STRATEGY-008
title: План подготовки Senior System Design
domain: process
category: strategy
tags:
- senior
- system_design
- preparation
difficulty: middle
roles:
- all_roles
interview_stage:
- phone_screen
- coding
frequency: medium
related:
- PROC-FRAMEWORK-003
- ARCH-SYSDESIGN-005
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

# План подготовки Senior System Design

## Цель

Подготовка senior-кандидата требует практики открытых архитектурных задач и решений под ограничения.

## Главное

- Тренируйте оценку нагрузки.
- Обсуждайте отказоустойчивость и наблюдаемость.
- Защищайте компромиссы числами и допущениями.

## Как применять

Для senior system design тренируйте требования, численные оценки, границы сервисов, данные, отказоустойчивость и эксплуатацию. После решения проводите собственный разбор слабых мест и проверку допущений.

## Пример

На задаче платежей отдельно продумайте дубликаты, восстановление после сбоя провайдера и наблюдаемость, затем попросите коллегу найти контрпример.

## Что проверить

Не сводите подготовку к рисованию стандартной схемы с очередью и кешем. Оценивайте, как решение меняется при другой нагрузке и бизнес-инвариантах.

## На собеседовании

Разберите два-три кейса с разными паттернами нагрузки и проведите пробное интервью.

## Связанные темы

- [[PROC-STAGE-004]] — сначала повторить: System Design Interview (Интервью по проектированию систем).
- [[PROC-FRAMEWORK-003]] — Фреймворк решения System Design задачи.
- [[ARCH-SYSDESIGN-005]] — URL Shortener (TinyURL/bit.ly).

## Источник

- McDowell. Cracking the Coding Interview, 6th ed., 2015.
