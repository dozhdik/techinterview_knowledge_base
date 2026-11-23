---
id: ARCH-COMPONENT-013
title: Reverse Proxy
domain: arch
category: component
tags:
- reverse_proxy
- networking
difficulty: middle
roles:
- all_roles
interview_stage:
- system_design
frequency: high
related:
- ARCH-COMPONENT-004
- ARCH-COMPONENT-001
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

# Reverse Proxy

## Назначение

Обратный прокси принимает запросы клиентов и пересылает их внутренним сервисам.

## Главное

- Может завершать TLS.
- Маршрутизирует по пути и хосту.
- Нуждается в лимитах и таймаутах.

## Как устроено

Reverse proxy принимает входящие соединения и пересылает запросы внутренним сервисам. Он может завершать TLS, маршрутизировать по пути или хосту и ограничивать запросы до приложения.

## Практический пример

Запросы /api/ идут к backend, а /assets/ — к статическому хранилищу. Клиент видит один публичный адрес, хотя внутри несколько сервисов.

## Ограничения

Прокси становится важным узлом отказа: нужны мониторинг и несколько экземпляров. Заголовки с исходным IP и схемой следует доверять только от известных прокси.

## На собеседовании

Разделите функции reverse proxy, API Gateway и балансировщика в выбранной схеме.

## Связанные темы

- [[CS-CONCEPT-030]] — сначала повторить: HTTP: запрос и ответ.
- [[ARCH-COMPONENT-004]] — API Gateway.
- [[ARCH-COMPONENT-001]] — Load Balancer (Балансировщик нагрузки).

## Источник

- MDN Web Docs: Overview of HTTP — https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Overview
