---
id: ARCH-TRADEOFF-019
title: Object Storage vs Block Storage
domain: arch
category: tradeoff
tags:
- object_storage
- block_storage
difficulty: middle
roles:
- all_roles
interview_stage:
- system_design
frequency: medium
related:
- ARCH-COMPONENT-006
- ARCH-SYSDESIGN-007
prerequisites:
- ARCH-COMPONENT-009
sources:
- 'Google Cloud Architecture Center: Well-Architected Framework — https://docs.cloud.google.com/architecture/framework'
author: Команда TechInterview
version: '1.1'
date_created: '2026-11-23'
date_updated: '2026-11-23'
status: review
aliases:
  - "Объектное и блочное хранилища"
  - "Object Storage versus Block Storage"
---

# Object Storage vs Block Storage

## Суть выбора

Object storage обращается к объектам по ключу и API; block storage предоставляет блочное устройство файловой системе или БД.

## Главное

- Object storage удобен для файлов и масштабного хранения.
- block storage поддерживает низкоуровневые произвольные записи.
- Семантика обновления различается.

## Как устроено

Object storage адресует объекты по ключу через API и хорошо подходит для файлов и резервных копий. Block storage предоставляет блочное устройство файловой системе или БД и ближе к обычному диску сервера.

## Практический пример

Фото пользователей удобно хранить как объекты и выдавать через CDN. Диск для файлов БД требует блочного доступа, подходящей задержки и правил резервирования.

## Ограничения

Сравнивайте не только цену за гигабайт, но и стоимость запросов, задержку, модель обновления и требования приложения. Объектное хранилище нельзя считать прямой заменой диска БД.

## На собеседовании

Выберите хранилище для пользовательских фото и для диска базы данных.

## Связанные темы

- [[ARCH-COMPONENT-009]] — сначала повторить: Реляционная база данных.
- [[ARCH-COMPONENT-006]] — Blob Storage.
- [[ARCH-SYSDESIGN-007]] — Файловое хранилище.

## Источник

- Google Cloud Architecture Center: Well-Architected Framework — https://docs.cloud.google.com/architecture/framework
