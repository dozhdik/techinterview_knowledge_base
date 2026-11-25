---
id: CS-CONCEPT-029
title: DNS и разрешение имён
domain: cs
category: concept
tags:
- dns
- networking
difficulty: middle
roles:
- all_roles
interview_stage:
- coding
frequency: high
related:
- CS-CONCEPT-030
- ARCH-COMPONENT-011
prerequisites:
- CS-CONCEPT-028
sources:
- 'Kurose and Ross. Computer Networking: A Top-Down Approach, 8th ed.'
author: Команда TechInterview
version: '1.1'
date_created: '2026-11-23'
date_updated: '2026-11-23'
status: review
aliases:
  - "Domain Name System"
  - "Система доменных имён"
abbreviations:
  - "DNS"
---

# DNS и разрешение имён

## Определение

DNS переводит доменное имя в записи, например адреса A и AAAA, через иерархию серверов.

## Главное

- Ответы кешируются согласно TTL.
- Запись CNAME указывает на другое имя.
- Обновление записи не мгновенно видно всем клиентам.

## Как это работает

Клиент запрашивает запись имени у резолвера, который использует кеш или обращается к DNS-серверам. Ответы имеют TTL; типы A и AAAA дают адреса, CNAME задаёт псевдоним, а не адрес сервиса напрямую.

## Пример

При открытии example.com браузеру нужен IP-адрес. Повторный запрос может обслужиться из кеша до истечения TTL, поэтому смена DNS-записи не становится видимой всем сразу.

## Границы и ошибки

DNS-ответ не гарантирует доступность узла и не заменяет проверку соединения. При миграции сервиса учитывайте TTL и кеширование на разных уровнях.

## На собеседовании

Опишите цепочку от браузера до рекурсивного резолвера и влияние кеша.

## Связанные темы

- [[CS-CONCEPT-028]] — сначала повторить: TCP и UDP.
- [[CS-CONCEPT-030]] — HTTP: запрос и ответ.
- [[ARCH-COMPONENT-011]] — DNS-резолвер.

## Источник

- Kurose and Ross. Computer Networking: A Top-Down Approach, 8th ed.
