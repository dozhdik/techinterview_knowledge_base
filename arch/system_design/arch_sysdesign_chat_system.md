---
id: "ARCH-SYSDESIGN-001"
title: "Chat System"
domain: "arch"
category: "sysdesign"
tags:
  - system_design
  - chat
  - realtime
  - websockets
  - messaging
  - must_know
  - core
difficulty: "senior"
roles:
  - "backend"
  - "fullstack"
  - "devops"
  - "all_roles"
interview_stage:
  - "system_design"
frequency: "high"
related:
  - "ARCH-COMPONENT-006"
  - "ARCH-COMPONENT-008"
  - "ARCH-TRADEOFF-002"
  - "ARCH-TRADEOFF-003"
prerequisites: []
sources:
  - "Xu A. System Design Interview — An Insider's Guide. ByteByteGo, 2020+"
  - "Kleppmann M. Designing Data-Intensive Applications. O'Reilly, 2017"
  - "IETF RFC 6455 — The WebSocket Protocol"
author: "Инженер знаний №2"
version: "1.0"
date_created: "2026-04-10"
date_updated: "2026-04-11"
status: "review"
---

# Chat System

## Постановка задачи
Нужно спроектировать систему обмена сообщениями в реальном времени для 1:1 и групповых чатов. Пользователи должны отправлять и получать сообщения с низкой задержкой, видеть историю переписки и получать сообщения на нескольких устройствах. На собеседовании эта задача обычно проверяет умение разделять realtime path, storage path и delivery semantics.

## Шаг 1: Уточнение требований
### Функциональные требования
1. Поддержка 1:1 чатов и групповых чатов
2. Отправка и получение сообщений в реальном времени
3. Хранение истории сообщений
4. Статусы сообщений: sent, delivered, read
5. Поддержка нескольких устройств на пользователя
6. Вложения через внешний storage
7. Offline delivery и push-уведомления

### Нефункциональные требования
1. Низкая latency доставки сообщений
2. Высокая availability
3. Масштабируемость на большое число одновременных соединений
4. Надёжное хранение истории
5. Допустима eventual consistency для presence и части read receipts

### Уточняющие вопросы интервьюеру
1. Нужны ли end-to-end encryption и message ordering? — это сильно меняет архитектуру и ограничения на серверную обработку
2. Какой размер групповых чатов? — fan-out для группы на 50 участников и на 100 000 участников проектируется по-разному
3. Нужен ли поиск по истории сообщений? — тогда может понадобиться отдельный search index
4. Какие гарантии доставки требуются? — at-most-once, at-least-once или effectively-once
5. Нужны ли voice/video calls? — это уже другой класс системы и нельзя притворяться, что это “просто ещё один тип сообщения”

### Допущения
- 20 млн MAU, 2 млн DAU
- 200 млн сообщений в день
- средний размер текстового сообщения около 500 байт
- вложения хранятся отдельно в blob storage
- для presence допустима eventual consistency
- для истории критична durability, но не обязательна глобальная strong consistency между регионами

## Шаг 2: Capacity Estimation
- **Пользователи**: 2 млн DAU / 20 млн MAU
- **Запросы**: в среднем около 2 300 RPS на запись сообщений, пиково 10 000–20 000 RPS; чтение выше из-за sync истории, delivery status и reconnect
- **Хранилище**: ~100 GB/день только текст сообщений без учёта индексов, метаданных и вложений; ~36+ TB/год только под raw text storage

## Шаг 3: High-Level Design
```text
[Client] → [Load Balancer] → [WebSocket Gateway]
                                    ↓
                              [Chat Service]
                           ↙        ↓        ↘
                [Message DB]   [Message Broker]   [Presence Store]
                     ↓                ↓
              [Read Replicas]   [Delivery Workers]
                                    ↓
                           [Push Notification Service]

                 [Blob Storage] ← attachments / media
```

## Шаг 4: Модель данных
- **Пользователь и устройства**: сущности `user`, `device` (push token, platform); один пользователь — несколько устройств.
- **Чаты**: `conversation` (direct / group), `membership` (`user_id`, `conversation_id`, роль).
- **Сообщения**: серверный `message_id`, опционально `client_message_id` для идемпотентности; `conversation_id`, `sender_id`, текст или ссылка на объект в blob storage, `created_at`. Крупные вложения — только ссылка и метаданные в OLTP.
- **Статусы**: sent / delivered / read — отдельные записи или поток событий; для UX часто допустима eventual consistency.
- **Presence**: KV или отдельное хранилище с TTL.

Типичное **шардирование** — по `conversation_id`, чтобы история одного чата была локальной для запросов «лента сообщений».

## Шаг 5: API
- **REST**: список чатов, создание чата, пагинация истории (курсор `before` / `after`), выдача pre-signed URL для загрузки вложения.
- **WebSocket**: подписка на события пользователя/устройства — `new_message`, подтверждения, опционально typing/presence.
- **Идемпотентность отправки**: клиент передаёт `client_message_id`; сервер отклоняет повтор при том же ключе.

## Шаг 6: Углубление по компонентам
- **WebSocket Gateway**: stateless за балансировщиком со sticky session; при обрыве — REST-догрузка пропущенных сообщений.
- **Chat Service**: проверка членства, запись в БД, публикация события в брокер для fan-out и push.
- **Message Broker** (Kafka и т.п.): событие «новое сообщение» для групповых чатов и асинхронной доставки.
- **Delivery Workers**: размножение на получателей, вызов push, обновление badge/unread.
- **Message DB**: индекс `(conversation_id, created_at)`; **read replicas** для тяжёлого чтения истории.

## Шаг 7: Масштабирование
- Горизонтально масштабируются gateway, chat service, workers; БД — шардирование и/или реплики.
- Очень большие группы: отдельный fan-out pipeline и лимиты на размер группы или деградация до «уведомление + ленивая догрузка».
- Multi-region: сложнее глобальный порядок и поиск; часто активный регион на чат или eventual merge.

## Шаг 8: Отказы и надёжность
- Доставка через брокер: **at-least-once** + дедуп по `client_message_id` / `message_id`.
- Для «прочитал своё сообщение сразу после отправки» — чтение с primary или синхронная реплика критичного пути (см. [[ARCH-TRADEOFF-003]]).
- DLQ и алерты для сообщений, не доставленных после N retry.

## Шаг 9: Наблюдаемость
- Метрики: число активных WebSocket, задержка до первого ack, lag consumer-групп, ошибки push, RPS REST.
- Логи и трассировка с `correlation_id` / `conversation_id` / `message_id`.

## Шаг 10: Резюме
Разделены три пути: низкая задержка realtime (WebSocket), долговечное хранение (БД + blob), асинхронный fan-out и push (брокер + workers). На интервью важно проговорить ordering (per-chat vs global), E2E encryption (если требуется) и компромиссы [[ARCH-TRADEOFF-002]] / [[ARCH-TRADEOFF-003]].
