---
id: ARCH-TRADEOFF-018
title: Active-Passive vs Active-Active по регионам
domain: arch
category: tradeoff
tags:
- multi_region
- disaster_recovery
- availability
difficulty: middle
roles:
- all_roles
interview_stage:
- system_design
frequency: medium
related:
- ARCH-COMPONENT-029
- ARCH-COMPONENT-008
prerequisites:
- ARCH-TRADEOFF-011
sources:
- 'Google Cloud Architecture Center: Reliability pillar — https://docs.cloud.google.com/architecture/framework/reliability'
author: Команда TechInterview
version: '1.1'
date_created: '2026-11-23'
date_updated: '2026-11-23'
status: review
---

# Active-Passive vs Active-Active по регионам

## Суть выбора

В active-passive один регион обслуживает основную нагрузку; active-active несколько регионов принимают запросы.

## Главное

- Active-passive проще для записи, но переключение требует времени.
- active-active уменьшает расстояние до пользователя, усложняя конфликты.
- Нужны план восстановления и тесты.

## Как устроено

Active-Passive держит резервный регион для переключения; Active-Active обслуживает пользователей из нескольких регионов одновременно. Второй режим повышает доступность и близость к пользователю ценой сложного согласования записей.

## Практический пример

Сервис чтения каталога может работать в обоих регионах; операции с единым балансом требуют продуманного владельца записи или механизма согласования.

## Ограничения

Проверьте RPO, RTO и поведение при разделении регионов. «Активен» не означает готовность к аварии без регулярных учений переключения и синхронизации данных.

## На собеседовании

Укажите RTO, RPO и правила владения записью в разных регионах.

## Связанные темы

- [[ARCH-TRADEOFF-011]] — сначала повторить: Строгая vs eventual consistency.
- [[ARCH-COMPONENT-029]] — Резервное копирование и восстановление.
- [[ARCH-COMPONENT-008]] — Database Replication.

## Источник

- Google Cloud Architecture Center: Reliability pillar — https://docs.cloud.google.com/architecture/framework/reliability
