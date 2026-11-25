---
id: ARCH-COMPONENT-029
title: Резервное копирование и восстановление
domain: arch
category: component
tags:
- backup
- recovery
- reliability
difficulty: middle
roles:
- all_roles
interview_stage:
- system_design
frequency: high
related:
- ARCH-COMPONENT-008
- ARCH-TRADEOFF-018
prerequisites:
- ARCH-COMPONENT-009
sources:
- 'Google Cloud Architecture Center: Reliability pillar — https://docs.cloud.google.com/architecture/framework/reliability'
author: Команда TechInterview
version: '1.1'
date_created: '2026-11-23'
date_updated: '2026-11-23'
status: review
aliases:
  - "Backup and Restore"
---

# Резервное копирование и восстановление

## Назначение

Резервная копия сохраняет данные для восстановления после удаления, ошибки или отказа.

## Главное

- RPO задаёт допустимую потерю данных.
- RTO задаёт время восстановления.
- Успешное копирование без проверки восстановления не доказывает готовность.

## Как устроено

Резервная копия сохраняет данные отдельно от работающего хранилища, а процедура восстановления возвращает их в согласованное состояние. Политика задаётся через RPO — допустимую потерю данных — и RTO — допустимое время восстановления.

## Практический пример

Ежедневная полная копия и журнал изменений позволяют восстановиться к нужному моменту, если сами копии доступны после аварии основного региона.

## Ограничения

Наличие файлов копии не доказывает восстановимость. Регулярно пробуйте восстановление, проверяйте права доступа, шифрование, срок хранения и совместимость версий.

## На собеседовании

Спросите, нужна ли точка во времени и как часто проводится тест восстановления.

## Связанные темы

- [[ARCH-COMPONENT-009]] — сначала повторить: Реляционная база данных.
- [[ARCH-COMPONENT-008]] — Database Replication.
- [[ARCH-TRADEOFF-018]] — Active-Passive vs Active-Active по регионам.

## Источник

- Google Cloud Architecture Center: Reliability pillar — https://docs.cloud.google.com/architecture/framework/reliability
