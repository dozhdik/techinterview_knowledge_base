---
id: ARCH-TRADEOFF-009
title: Push vs Pull в доставке событий
domain: arch
category: tradeoff
tags:
- push
- pull
- events
difficulty: middle
roles:
- all_roles
interview_stage:
- system_design
frequency: medium
related:
- ARCH-SYSDESIGN-002
- ARCH-COMPONENT-003
prerequisites:
- ARCH-TRADEOFF-007
sources:
- Kleppmann. Designing Data-Intensive Applications, 2017.
author: Команда TechInterview
version: '1.1'
date_created: '2026-11-23'
date_updated: '2026-11-23'
status: review
---

# Push vs Pull в доставке событий

## Суть выбора

При push отправитель доставляет события потребителю; при pull потребитель сам запрашивает доступные события.

## Главное

- Push снижает задержку при готовом получателе.
- pull даёт больше контроля над темпом обработки.
- Обе схемы требуют политики повторов.

## Как устроено

Push доставляет события получателю по инициативе отправителя, а Pull позволяет потребителю запрашивать новые данные в собственном темпе. Выбор влияет на задержку, контроль нагрузки и хранение непрочитанных событий.

## Практический пример

Уведомление в чат отправляют активному клиенту сразу, а после восстановления соединения клиент запрашивает пропущенную историю с последнего известного ID.

## Ограничения

Push без буфера теряет события при офлайн-клиенте; Pull с редким опросом увеличивает задержку. Для надёжной доставки часто сочетают оба пути.

## На собеседовании

Выберите вариант для уведомлений и для медленного пакетного потребителя.

## Связанные темы

- [[ARCH-TRADEOFF-007]] — сначала повторить: Synchronous vs Asynchronous Communication.
- [[ARCH-SYSDESIGN-002]] — Notification Service.
- [[ARCH-COMPONENT-003]] — Message Queue (Очередь сообщений).

## Источник

- Kleppmann. Designing Data-Intensive Applications, 2017.
