---
id: ARCH-TRADEOFF-016
title: Serverless vs Containers
domain: arch
category: tradeoff
tags:
- serverless
- containers
- deployment
difficulty: middle
roles:
- all_roles
interview_stage:
- system_design
frequency: medium
related:
- ARCH-COMPONENT-023
- ARCH-COMPONENT-018
prerequisites: []
sources:
- 'Google Cloud Architecture Center: Well-Architected Framework — https://docs.cloud.google.com/architecture/framework'
author: Команда TechInterview
version: '1.1'
date_created: '2026-11-23'
date_updated: '2026-11-23'
status: review
---

# Serverless vs Containers

## Суть выбора

Serverless берёт на себя часть управления запуском функций; контейнеры дают более прямой контроль над окружением и временем жизни.

## Главное

- Serverless удобен для событийной нагрузки.
- Ограничения холодного старта и времени выполнения зависят от платформы.
- Контейнеры требуют эксплуатации.

## Как устроено

Serverless запускает код по событиям и скрывает часть управления серверами; контейнеры дают больше контроля над временем жизни процесса и настройкой среды. Оплата и масштабирование зависят от профиля нагрузки и провайдера.

## Практический пример

Нерегулярная обработка загруженных файлов может быть удобна в serverless; постоянно нагруженный API со специфичными библиотеками проще контролировать в контейнерах.

## Ограничения

Сравните холодный старт, ограничения времени выполнения, стоимость при постоянной нагрузке и переносимость. Оба варианта требуют мониторинга и корректной обработки ошибок.

## На собеседовании

Сравните стоимость при редкой и постоянной нагрузке, не объявляя универсального победителя.

## Связанные темы

- [[ARCH-COMPONENT-023]] — Оркестратор контейнеров.
- [[ARCH-COMPONENT-018]] — Сервис feature flags.

## Источник

- Google Cloud Architecture Center: Well-Architected Framework — https://docs.cloud.google.com/architecture/framework
