---
id: ARCH-COMPONENT-023
title: Оркестратор контейнеров
domain: arch
category: component
tags:
- containers
- kubernetes
- deployment
difficulty: middle
roles:
- all_roles
interview_stage:
- system_design
frequency: high
related:
- ARCH-COMPONENT-022
- ARCH-TRADEOFF-016
prerequisites:
- ARCH-COMPONENT-012
sources:
- 'Google Cloud Architecture Center: Well-Architected Framework — https://docs.cloud.google.com/architecture/framework'
author: Команда TechInterview
version: '1.1'
date_created: '2026-11-23'
date_updated: '2026-11-23'
status: review
aliases:
  - "Container Orchestrator"
  - "Оркестрация контейнеров"
---

# Оркестратор контейнеров

## Назначение

Оркестратор размещает и перезапускает контейнеры, управляя желаемым состоянием приложения.

## Главное

- Проверки готовности отделяют работающий процесс от готового к трафику.
- Масштабирование требует ресурсов.
- stateful-сервисы нуждаются в постоянном хранилище.

## Как устроено

Оркестратор размещает контейнеры по узлам, перезапускает упавшие экземпляры и поддерживает желаемое количество реплик. Проверки готовности отделяют запущенный процесс от экземпляра, способного принимать трафик.

## Практический пример

Если один узел потерян, экземпляры сервиса запускаются на других узлах. Во время выкладки новая реплика начинает получать запросы только после readiness-проверки.

## Ограничения

Оркестрация не делает состояние приложения автоматически устойчивым. Хранилище, миграции, лимиты ресурсов и завершение соединений требуют отдельного проектирования.

## На собеседовании

Объясните, что происходит с запросом во время rolling update.

## Связанные темы

- [[ARCH-COMPONENT-012]] — сначала повторить: Service Discovery.
- [[ARCH-COMPONENT-022]] — Ingress-контроллер.
- [[ARCH-TRADEOFF-016]] — Serverless vs Containers.

## Источник

- Google Cloud Architecture Center: Well-Architected Framework — https://docs.cloud.google.com/architecture/framework
