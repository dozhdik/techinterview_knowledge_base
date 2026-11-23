---
id: ARCH-COMPONENT-018
title: Сервис feature flags
domain: arch
category: component
tags:
- feature_flags
- deployment
- reliability
difficulty: middle
roles:
- all_roles
interview_stage:
- system_design
frequency: high
related:
- ARCH-TRADEOFF-016
- ARCH-COMPONENT-019
prerequisites: []
sources:
- 'Google Cloud Architecture Center: Well-Architected Framework — https://docs.cloud.google.com/architecture/framework'
author: Команда TechInterview
version: '1.1'
date_created: '2026-11-23'
date_updated: '2026-11-23'
status: review
---

# Сервис feature flags

## Назначение

Feature flags включают поведение для выбранных пользователей без нового развёртывания кода.

## Главное

- Правила могут обновляться динамически.
- Недоступность сервиса флагов требует безопасного значения.
- Старые флаги нужно удалять.

## Как устроено

Feature flag отделяет выпуск кода от включения поведения. Правило может зависеть от пользователя, процента трафика или окружения; изменение правила позволяет быстро откатить эксперимент.

## Практический пример

Новый алгоритм рекомендаций сначала включают для небольшой группы, сравнивают метрики и постепенно расширяют долю пользователей.

## Ограничения

Флаги усложняют тестирование комбинаций и могут остаться навсегда. Для критичного выключателя продумайте значение по умолчанию при недоступном сервисе флагов.

## На собеседовании

Покажите постепенное включение функции и критерий отката.

## Связанные темы

- [[ARCH-TRADEOFF-016]] — Serverless vs Containers.
- [[ARCH-COMPONENT-019]] — Сервис конфигурации.

## Источник

- Google Cloud Architecture Center: Well-Architected Framework — https://docs.cloud.google.com/architecture/framework
