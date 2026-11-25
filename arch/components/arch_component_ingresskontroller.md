---
id: ARCH-COMPONENT-022
title: Ingress-контроллер
domain: arch
category: component
tags:
- ingress
- kubernetes
- networking
difficulty: middle
roles:
- all_roles
interview_stage:
- system_design
frequency: high
related:
- ARCH-COMPONENT-023
- ARCH-COMPONENT-013
prerequisites:
- ARCH-COMPONENT-001
sources:
- 'Google Cloud Architecture Center: Well-Architected Framework — https://docs.cloud.google.com/architecture/framework'
- 'Kubernetes Documentation: Ingress Controllers — https://kubernetes.io/docs/concepts/services-networking/ingress-controllers/'
author: Команда TechInterview
version: '1.1'
date_created: '2026-11-23'
date_updated: '2026-11-23'
status: review
aliases:
  - "Ingress Controller"
  - "Контроллер Ingress"
---

# Ingress-контроллер

## Назначение

Ingress-контроллер применяет правила входящего HTTP-трафика к сервисам кластера.

## Главное

- Маршрутизирует по хосту и пути.
- Может завершать TLS.
- Конфигурация и возможности зависят от реализации.

## Как устроено

Ingress-контроллер в Kubernetes реализует правила входящего HTTP-трафика для сервисов кластера. Он связывает внешнюю точку входа с маршрутизацией по имени хоста и пути.

## Практический пример

Запросы api.example.com направляются к API-сервису, а web.example.com — к фронтенду; TLS может завершаться на входе.

## Ограничения

Ingress не решает авторизацию бизнес-операций. Реальное поведение зависит от контроллера; проверьте таймауты, размер запросов и способ выдачи сертификатов.

## На собеседовании

Разделите внешний балансировщик и маршрутизацию внутри кластера.

## Связанные темы

- [[ARCH-COMPONENT-001]] — сначала повторить: Load Balancer (Балансировщик нагрузки).
- [[ARCH-COMPONENT-023]] — Оркестратор контейнеров.
- [[ARCH-COMPONENT-013]] — Reverse Proxy.

## Источник

- Google Cloud Architecture Center: Well-Architected Framework — https://docs.cloud.google.com/architecture/framework
- Kubernetes Documentation: Ingress Controllers — https://kubernetes.io/docs/concepts/services-networking/ingress-controllers/
