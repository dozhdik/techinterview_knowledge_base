---
id: ARCH-COMPONENT-027
title: Менеджер секретов
domain: arch
category: component
tags:
- secrets
- security
- operations
difficulty: middle
roles:
- all_roles
interview_stage:
- system_design
frequency: high
related:
- ARCH-COMPONENT-014
- ARCH-COMPONENT-019
prerequisites: []
sources:
- 'Google Cloud Architecture Center: Well-Architected Framework — https://docs.cloud.google.com/architecture/framework'
author: Команда TechInterview
version: '1.1'
date_created: '2026-11-23'
date_updated: '2026-11-23'
status: review
aliases:
  - "Secrets Manager"
---

# Менеджер секретов

## Назначение

Менеджер секретов хранит пароли, ключи и токены с контролем доступа и ротацией.

## Главное

- Секрет не должен попадать в логи.
- Доступ выдаётся по минимально нужным правам.
- Ротация требует обновления потребителей.

## Как устроено

Менеджер секретов хранит пароли, ключи и токены отдельно от исходного кода и выдаёт их по правам доступа. Ротация меняет секрет без публикации нового значения в репозитории.

## Практический пример

Сервис получает пароль к БД при запуске с разрешением только на нужное окружение. После ротации старый пароль отзывается по согласованному плану.

## Ограничения

Шифрование хранилища не заменяет контроль доступа. Следите за секретами в логах, дампах, переменных процесса и за поведением сервиса при недоступности менеджера.

## На собеседовании

Объясните, как приложение получает ключ при старте и что делать при компрометации.

## Связанные темы

- [[ARCH-COMPONENT-014]] — Сервис аутентификации и авторизации.
- [[ARCH-COMPONENT-019]] — Сервис конфигурации.

## Источник

- Google Cloud Architecture Center: Well-Architected Framework — https://docs.cloud.google.com/architecture/framework
