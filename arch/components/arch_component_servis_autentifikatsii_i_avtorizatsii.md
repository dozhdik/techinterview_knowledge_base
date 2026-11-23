---
id: ARCH-COMPONENT-014
title: Сервис аутентификации и авторизации
domain: arch
category: component
tags:
- authentication
- authorization
- security
difficulty: middle
roles:
- all_roles
interview_stage:
- system_design
frequency: high
related:
- ARCH-COMPONENT-004
- ARCH-SYSDESIGN-009
prerequisites:
- CS-CONCEPT-031
sources:
- 'Google Cloud Architecture Center: Well-Architected Framework — https://docs.cloud.google.com/architecture/framework'
author: Команда TechInterview
version: '1.1'
date_created: '2026-11-23'
date_updated: '2026-11-23'
status: review
---

# Сервис аутентификации и авторизации

## Назначение

Сервис устанавливает личность пользователя и проверяет его право на действие.

## Главное

- Аутентификация отвечает кто это.
- Авторизация отвечает что разрешено.
- Токены требуют срока жизни и проверки подписи.

## Как устроено

Аутентификация устанавливает, кто делает запрос, а авторизация — что этому субъекту разрешено. Сервис выдаёт или проверяет учётные данные, но каждое защищённое действие должно проверять права.

## Практический пример

Пользователь входит в систему и получает токен. При запросе /orders/42 сервер проверяет не только подпись токена, но и право видеть именно заказ 42.

## Ограничения

Действительный токен не означает доступ к любому ресурсу. Учитывайте отзыв прав, срок жизни токена, хранение секретов и аудит чувствительных операций.

## На собеседовании

В решении отделите вход пользователя от проверки доступа к конкретному ресурсу.

## Связанные темы

- [[CS-CONCEPT-031]] — сначала повторить: TLS и HTTPS.
- [[ARCH-COMPONENT-004]] — API Gateway.
- [[ARCH-SYSDESIGN-009]] — Платёжный сервис.

## Источник

- Google Cloud Architecture Center: Well-Architected Framework — https://docs.cloud.google.com/architecture/framework
