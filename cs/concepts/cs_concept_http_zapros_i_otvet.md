---
id: CS-CONCEPT-030
title: 'HTTP: запрос и ответ'
domain: cs
category: concept
tags:
- http
- api
- networking
difficulty: middle
roles:
- all_roles
interview_stage:
- coding
frequency: high
related:
- CS-CONCEPT-031
- ARCH-COMPONENT-004
prerequisites:
- CS-CONCEPT-028
sources:
- 'MDN Web Docs: Overview of HTTP — https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Overview'
author: Команда TechInterview
version: '1.1'
date_created: '2026-11-23'
date_updated: '2026-11-23'
status: review
aliases:
  - "Hypertext Transfer Protocol"
  - "Протокол передачи гипертекста"
abbreviations:
  - "HTTP"
---

# HTTP: запрос и ответ

## Определение

HTTP описывает обмен запросом и ответом между клиентом и сервером.

## Главное

- Метод и путь задают операцию и ресурс.
- Код состояния описывает результат.
- Заголовки передают метаданные и правила кеширования.

## Как это работает

HTTP-запрос состоит из метода, адреса, заголовков и необязательного тела; ответ содержит статус, заголовки и тело. Семантика метода и коды статусов помогают клиенту понять результат операции.

## Пример

GET /cards/CS-CONCEPT-009 получает карточку; ответ 200 содержит материал, 404 означает, что карточка не найдена. Для создания ресурса обычно используют POST с телом запроса.

## Границы и ошибки

Не путайте транспортный успех с бизнес-успехом: статус и формат тела нужно согласовать. Кеширование, повтор запросов и идемпотентность зависят от метода и конкретного API-контракта.

## На собеседовании

Разделите идемпотентность метода и фактическую идемпотентность бизнес-операции.

## Связанные темы

- [[CS-CONCEPT-028]] — сначала повторить: TCP и UDP.
- [[CS-CONCEPT-031]] — TLS и HTTPS.
- [[ARCH-COMPONENT-004]] — API Gateway.

## Источник

- MDN Web Docs: Overview of HTTP — https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Overview
