---
id: CS-CONCEPT-031
title: TLS и HTTPS
domain: cs
category: concept
tags:
- tls
- https
- security
difficulty: middle
roles:
- all_roles
interview_stage:
- coding
frequency: high
related:
- CS-CONCEPT-030
- ARCH-COMPONENT-014
prerequisites:
- CS-CONCEPT-028
sources:
- 'Kurose and Ross. Computer Networking: A Top-Down Approach, 8th ed.'
author: Команда TechInterview
version: '1.1'
date_created: '2026-11-23'
date_updated: '2026-11-23'
status: review
---

# TLS и HTTPS

## Определение

TLS защищает соединение: проверяет сторону сервера по сертификату и шифрует передаваемые данные.

## Главное

- HTTPS — HTTP поверх TLS.
- Сертификат связывает имя сервера с ключом.
- TLS не исправляет ошибки авторизации приложения.

## Как это работает

TLS проверяет сертификат сервера и согласует защищённый канал; затем HTTP передаётся внутри этого канала как HTTPS. Проверка имени хоста и цепочки доверия защищает от подмены сервера.

## Пример

При обращении к https://example.com клиент проверяет сертификат для example.com до передачи чувствительных данных. После установления соединения содержимое запросов шифруется.

## Границы и ошибки

HTTPS не делает приложение безопасным само по себе: уязвимости авторизации и вредоносный контент остаются возможными. Просроченный сертификат или неверное имя должны приводить к ошибке проверки.

## На собеседовании

Опишите проверку сертификата и почему отключать её в продакшене опасно.

## Связанные темы

- [[CS-CONCEPT-028]] — сначала повторить: TCP и UDP.
- [[CS-CONCEPT-030]] — HTTP: запрос и ответ.
- [[ARCH-COMPONENT-014]] — Сервис аутентификации и авторизации.

## Источник

- Kurose and Ross. Computer Networking: A Top-Down Approach, 8th ed.
