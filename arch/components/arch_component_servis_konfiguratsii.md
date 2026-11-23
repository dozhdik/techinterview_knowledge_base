---
id: ARCH-COMPONENT-019
title: Сервис конфигурации
domain: arch
category: component
tags:
- configuration
- operations
difficulty: middle
roles:
- all_roles
interview_stage:
- system_design
frequency: high
related:
- ARCH-COMPONENT-018
- ARCH-COMPONENT-027
prerequisites: []
sources:
- 'Google Cloud Architecture Center: Well-Architected Framework — https://docs.cloud.google.com/architecture/framework'
author: Команда TechInterview
version: '1.1'
date_created: '2026-11-23'
date_updated: '2026-11-23'
status: review
---

# Сервис конфигурации

## Назначение

Централизованная конфигурация хранит параметры приложений по средам и версиям.

## Главное

- Изменения должны иметь историю.
- Критичные параметры требуют проверки и отката.
- Секреты лучше хранить отдельно.

## Как устроено

Сервис конфигурации хранит параметры, которые используют несколько экземпляров приложения, и раздаёт версии настроек. Клиенты могут кешировать последнюю корректную версию и обновляться по событию или опросу.

## Практический пример

Лимит запросов меняют централизованно без ручного редактирования десятков серверов; приложения применяют новую версию после проверки формата.

## Ограничения

Неверная настройка может повлиять сразу на весь парк. Нужны валидация, аудит изменений, поэтапное распространение и отделение секретов от обычных параметров.

## На собеседовании

Опишите, как сервис узнаёт об обновлении и что произойдёт при потере хранилища.

## Связанные темы

- [[ARCH-COMPONENT-018]] — Сервис feature flags.
- [[ARCH-COMPONENT-027]] — Менеджер секретов.

## Источник

- Google Cloud Architecture Center: Well-Architected Framework — https://docs.cloud.google.com/architecture/framework
