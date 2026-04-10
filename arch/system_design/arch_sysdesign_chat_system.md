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
difficulty: "senior"
roles:
  - "backend"
  - "fullstack"
  - "devops"
  - "all_roles"
interview_stage:
  - "system_design"
frequency: "medium"
related:
  - "ARCH-COMPONENT-006"
  - "ARCH-COMPONENT-008"
  - "ARCH-TRADEOFF-002"
  - "ARCH-TRADEOFF-003"
prerequisites: []
sources:
  - "Alex Xu — System Design Interview"
  - "Martin Kleppmann — Designing Data-Intensive Applications"
  - "WebSocket RFC 6455"
author: "Инженер знаний №2"
version: "1.0"
date_created: "2026-04-10"
date_updated: "2026-04-10"
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
