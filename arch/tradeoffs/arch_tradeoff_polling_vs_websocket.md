---
id: ARCH-TRADEOFF-008
title: Polling vs WebSocket
domain: arch
category: tradeoff
tags:
- polling
- websocket
- realtime
difficulty: middle
roles:
- all_roles
interview_stage:
- system_design
frequency: medium
related:
- ARCH-SYSDESIGN-001
- ARCH-SYSDESIGN-015
prerequisites:
- CS-CONCEPT-030
sources:
- 'MDN Web Docs: Overview of HTTP — https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Overview'
author: Команда TechInterview
version: '1.1'
date_created: '2026-11-23'
date_updated: '2026-11-23'
status: review
---

# Polling vs WebSocket

## Суть выбора

Polling периодически опрашивает сервер; WebSocket поддерживает длительное двустороннее соединение.

## Главное

- Polling проще при редких изменениях.
- WebSocket уменьшает задержку доставки, но требует управления соединениями.
- reconnect должен восстанавливать состояние.

## Как устроено

Polling периодически спрашивает сервер об изменениях; WebSocket держит двустороннее соединение открытым. Polling проще реализовать и восстанавливать, но пустые запросы расходуют ресурсы при высокой частоте.

## Практический пример

Панель с обновлением раз в минуту может использовать polling. Для чата с частыми сообщениями постоянное соединение уменьшает задержку доставки.

## Ограничения

У WebSocket нужны reconnect, heartbeat, авторизация соединения и масштабирование множества открытых каналов. При выборе оцените частоту событий, число клиентов и допустимую задержку.

## На собеседовании

На чате сравните число соединений, частоту событий и допустимую задержку.

## Связанные темы

- [[CS-CONCEPT-030]] — сначала повторить: HTTP: запрос и ответ.
- [[ARCH-SYSDESIGN-001]] — Chat System.
- [[ARCH-SYSDESIGN-015]] — Совместное редактирование документа.

## Источник

- MDN Web Docs: Overview of HTTP — https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Overview
