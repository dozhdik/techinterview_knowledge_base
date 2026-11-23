---
id: ARCH-COMPONENT-011
title: DNS-резолвер
domain: arch
category: component
tags:
- dns
- networking
difficulty: middle
roles:
- all_roles
interview_stage:
- system_design
frequency: high
related:
- CS-CONCEPT-029
- ARCH-COMPONENT-001
prerequisites: []
sources:
- 'Kurose and Ross. Computer Networking: A Top-Down Approach, 8th ed.'
author: Команда TechInterview
version: '1.1'
date_created: '2026-11-23'
date_updated: '2026-11-23'
status: review
---

# DNS-резолвер

## Назначение

Рекурсивный резолвер получает DNS-записи для клиента и кеширует результат до истечения TTL.

## Главное

- Снижает число запросов к авторитетным серверам.
- TTL влияет на скорость смены адреса.
- Отсутствие записи тоже может кешироваться.

## Как устроено

Резолвер принимает запрос имени, проверяет кеш и при необходимости запрашивает авторитативные сведения через DNS-инфраструктуру. TTL управляет сроком хранения ответа и влияет на скорость смены адреса.

## Практический пример

При переезде API на новый адрес клиенты могут некоторое время обращаться по старой записи, пока не истечёт TTL на их резолверах.

## Ограничения

DNS не проверяет здоровье приложения. Для отказоустойчивости отдельно нужны мониторинг, балансировка и план поведения клиентов при устаревшем ответе.

## На собеседовании

В схеме распределения трафика объясните, почему смена DNS не обеспечивает мгновенный failover.

## Связанные темы

- [[CS-CONCEPT-029]] — DNS и разрешение имён.
- [[ARCH-COMPONENT-001]] — Load Balancer (Балансировщик нагрузки).

## Источник

- Kurose and Ross. Computer Networking: A Top-Down Approach, 8th ed.
