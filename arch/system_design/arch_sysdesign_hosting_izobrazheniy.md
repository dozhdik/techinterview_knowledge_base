---
id: ARCH-SYSDESIGN-017
title: Хостинг изображений
domain: arch
category: sysdesign
tags:
- images
- cdn
- storage
difficulty: senior
roles:
- all_roles
interview_stage:
- system_design
frequency: high
related:
- ARCH-COMPONENT-005
- ARCH-COMPONENT-006
prerequisites:
- ARCH-SYSDESIGN-007
sources:
- 'Google Cloud Architecture Center: Well-Architected Framework — https://docs.cloud.google.com/architecture/framework'
author: Команда TechInterview
version: '1.1'
date_created: '2026-11-23'
date_updated: '2026-11-23'
status: review
aliases:
  - "Image Hosting"
---

# Хостинг изображений

## Задача

Нужно загружать изображения, создавать варианты размеров и быстро их раздавать.

## Главное

- Оригинал хранится в object storage.
- Ресайз выполняется фоново или при первом запросе.
- CDN кеширует готовые варианты.

## Как устроено

Загрузка изображения отделяет оригинал, производные размеры и метаданные. Очередь запускает обработку превью, CDN доставляет готовые файлы, а права проверяются до выдачи приватного ресурса.

## Практический пример

Пользователь загружает фото: сервис сохраняет оригинал, создаёт миниатюру и возвращает ссылку, когда обработка завершена.

## Ограничения

Проверяйте реальный формат файла, размер и вредоносный контент. Удаление должно учитывать оригинал, производные файлы и кеш CDN.

## Что оценить

Уточните размер исходных файлов, число вариантов превью, частоту загрузок и долю скачиваний через CDN. Разделите синхронную проверку принятого файла и асинхронное создание производных изображений, чтобы пользователь видел честный статус обработки.

## На собеседовании

Назовите ограничения формата и размера, а также способ защиты от повторной обработки.

## Связанные темы

- [[ARCH-SYSDESIGN-007]] — сначала повторить: Файловое хранилище.
- [[ARCH-COMPONENT-005]] — CDN (Content Delivery Network).
- [[ARCH-COMPONENT-006]] — Blob Storage.

## Источник

- Google Cloud Architecture Center: Well-Architected Framework — https://docs.cloud.google.com/architecture/framework
