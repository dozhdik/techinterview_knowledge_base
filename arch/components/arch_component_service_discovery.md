---
id: ARCH-COMPONENT-012
title: Service Discovery
domain: arch
category: component
tags:
- service_discovery
- microservices
difficulty: middle
roles:
- all_roles
interview_stage:
- system_design
frequency: high
related:
- ARCH-COMPONENT-001
- ARCH-COMPONENT-023
prerequisites:
- ARCH-TRADEOFF-003
sources:
- 'Google Cloud Architecture Center: Well-Architected Framework — https://docs.cloud.google.com/architecture/framework'
author: Команда TechInterview
version: '1.1'
date_created: '2026-11-23'
date_updated: '2026-11-23'
status: review
aliases:
  - "Обнаружение сервисов"
  - "Обнаружение служб"
---

# Service Discovery

## Назначение

Обнаружение сервисов помогает приложению найти актуальные адреса экземпляров другого сервиса.

## Главное

- Реестр должен учитывать появление и исчезновение экземпляров.
- health check исключает нездоровые цели.
- Клиентская и серверная балансировка отличаются местом выбора.

## Как устроено

Service Discovery сопоставляет логическое имя сервиса с доступными экземплярами. Реестр обновляется при запуске, остановке и проверках здоровья; клиент или прокси выбирает адрес для вызова.

## Практический пример

Вместо фиксированного IP сервис заказов обращается к имени payment-service, а discovery возвращает работающие экземпляры после масштабирования.

## Ограничения

Устаревшие записи и задержки health-check могут направлять трафик на недоступный узел. Нужны таймауты, повтор с ограничением и ясное поведение при пустом списке.

## На собеседовании

Покажите, как адрес меняется при перезапуске контейнера.

## Связанные темы

- [[ARCH-TRADEOFF-003]] — сначала повторить: Monolith vs Microservices.
- [[ARCH-COMPONENT-001]] — Load Balancer (Балансировщик нагрузки).
- [[ARCH-COMPONENT-023]] — Оркестратор контейнеров.

## Источник

- Google Cloud Architecture Center: Well-Architected Framework — https://docs.cloud.google.com/architecture/framework
