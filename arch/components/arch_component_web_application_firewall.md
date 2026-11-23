---
id: ARCH-COMPONENT-021
title: Web Application Firewall
domain: arch
category: component
tags:
- waf
- security
- http
difficulty: middle
roles:
- all_roles
interview_stage:
- system_design
frequency: high
related:
- ARCH-COMPONENT-013
- ARCH-COMPONENT-004
prerequisites:
- CS-CONCEPT-030
sources:
- 'Google Cloud Architecture Center: Well-Architected Framework — https://docs.cloud.google.com/architecture/framework'
author: Команда TechInterview
version: '1.1'
date_created: '2026-11-23'
date_updated: '2026-11-23'
status: review
---

# Web Application Firewall

## Назначение

WAF фильтрует часть нежелательных HTTP-запросов перед приложением.

## Главное

- Правила бывают сигнатурными и поведенческими.
- Возможны ложные блокировки.
- WAF не устраняет уязвимость в коде.

## Как устроено

WAF анализирует HTTP-трафик до приложения и применяет правила к известным опасным шаблонам, частоте запросов или источникам. Его ставят перед публичными маршрутами.

## Практический пример

Правило ограничивает массовые попытки входа на /login, пока приложение продолжает проверять учётные данные и права пользователей.

## Ограничения

WAF не исправляет уязвимости кода и может блокировать легитимный запрос. Тестируйте правила на реальном трафике, отслеживайте ложные срабатывания и имейте путь быстрого отката.

## На собеседовании

Поставьте WAF на границе и объясните, как контролировать ложные срабатывания.

## Связанные темы

- [[CS-CONCEPT-030]] — сначала повторить: HTTP: запрос и ответ.
- [[ARCH-COMPONENT-013]] — Reverse Proxy.
- [[ARCH-COMPONENT-004]] — API Gateway.

## Источник

- Google Cloud Architecture Center: Well-Architected Framework — https://docs.cloud.google.com/architecture/framework
