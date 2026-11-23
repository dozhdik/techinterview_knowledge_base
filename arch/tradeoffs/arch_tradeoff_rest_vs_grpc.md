---
id: ARCH-TRADEOFF-012
title: REST vs gRPC
domain: arch
category: tradeoff
tags:
- rest
- grpc
- api
difficulty: middle
roles:
- all_roles
interview_stage:
- system_design
frequency: medium
related:
- ARCH-COMPONENT-004
- ARCH-TRADEOFF-004
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

# REST vs gRPC

## Суть выбора

REST через HTTP с JSON удобен для публичных интерфейсов; gRPC использует описанные схемой сообщения и RPC.

## Главное

- gRPC помогает типизированным межсервисным вызовам.
- Браузерная поддержка требует дополнительных решений.
- Версионирование контрактов важно в обоих случаях.

## Как устроено

REST обычно выражает ресурсы через HTTP-методы и удобен для публичного API; gRPC задаёт контракт сообщений и процедур и часто применяется между внутренними сервисами. Формат, инструменты и требования клиентов влияют на выбор.

## Практический пример

Внешнее API для браузера отдаёт JSON по HTTP, а внутренний сервис использует строго типизированный контракт для частых вызовов.

## Ограничения

gRPC не гарантирует быструю систему само по себе. Учтите поддержку браузеров и прокси, наблюдаемость, версионирование схемы и ограничения стриминга.

## На собеседовании

Выберите протокол исходя из клиентов, наблюдаемости и частоты вызовов.

## Связанные темы

- [[CS-CONCEPT-030]] — сначала повторить: HTTP: запрос и ответ.
- [[ARCH-COMPONENT-004]] — API Gateway.
- [[ARCH-TRADEOFF-004]] — REST vs GraphQL.

## Источник

- Google Cloud Architecture Center: Well-Architected Framework — https://docs.cloud.google.com/architecture/framework
