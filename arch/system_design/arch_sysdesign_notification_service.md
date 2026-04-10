---
id: "ARCH-SYSDESIGN-002"
title: "Notification Service"
domain: "arch"
category: "sysdesign"
tags:
  - system_design
  - notifications
  - messaging
  - queues
  - event_driven
difficulty: "middle"
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
  - "Firebase Cloud Messaging Documentation"
author: "Инженер знаний №2"
version: "1.0"
date_created: "2026-04-10"
date_updated: "2026-04-10"
status: "review"
---

# Notification Service

## Постановка задачи
Нужно спроектировать сервис уведомлений, который отправляет пользователям сообщения по нескольким каналам: push, email, SMS и in-app notifications. Система должна принимать события от других сервисов, учитывать пользовательские настройки и надёжно доставлять уведомления даже при всплесках нагрузки. На собеседовании эта задача проверяет, понимает ли кандидат разницу между ingestion, orchestration и delivery.

## Шаг 1: Уточнение требований
### Функциональные требования
1. Поддержка нескольких каналов доставки: push, email, SMS, in-app
2. Приём событий от upstream-сервисов
3. Проверка пользовательских настроек и opt-in/opt-out
4. Шаблоны сообщений и персонализация
5. Retry при временных ошибках внешних провайдеров
6. История отправок и статусов доставки
7. Rate limiting и дедупликация уведомлений

### Нефункциональные требования
1. Высокая availability
2. Хорошая устойчивость к burst traffic
3. Асинхронная обработка большинства уведомлений
4. Наблюдаемость: метрики, логи, tracing
5. Возможность легко добавлять новые каналы доставки

### Уточняющие вопросы интервьюеру
1. Нужны ли гарантии exactly-once? — обычно это слишком дорого, и чаще реально нужен at-least-once + idempotency
2. Какие каналы обязательны в первой версии? — нельзя проектировать одинаково email, SMS и push, будто это один transport
3. Нужны ли quiet hours, user preferences и приоритеты уведомлений? — это влияет на orchestration layer
4. Какой SLA на доставку и насколько критичны задержки? — transactional notifications и marketing campaigns проектируются по-разному
5. Нужна ли поддержка fallback-каналов? — например, если push не доставлен, отправлять email или SMS

### Допущения
- 50 млн уведомлений в день
- нагрузка bursty: пики при массовых событиях, рассылках и product triggers
- большинство уведомлений доставляется асинхронно
- внешние провайдеры могут быть недоступны или rate-limited
- сильная консистентность между генерацией события и доставкой не требуется

## Шаг 2: Capacity Estimation
- **Пользователи**: 10 млн DAU / 100 млн зарегистрированных пользователей
- **Запросы**: средняя запись ~600 RPS, пиковая в разы выше; чтения ниже и в основном связаны с историей, статусами и настройками
- **Хранилище**: десятки TB/год на delivery logs, шаблоны, preferences и audit trail, в зависимости от retention policy

## Шаг 3: High-Level Design
```text
[Producer Services] → [Notification API] → [Queue / Event Bus]
                                         ↓
                               [Orchestrator / Rules Engine]
                           ↙           ↓            ↘
                  [Push Worker]   [Email Worker]   [SMS Worker]
                      ↓               ↓               ↓
                 [FCM/APNS]   [Email Provider]   [SMS Provider]

                    [Template Service]   [User Preferences Store]
                             ↓                   ↓
                     [Delivery Log Store]   [Rate Limit / Dedup Layer]
