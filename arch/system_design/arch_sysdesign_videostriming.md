---
id: ARCH-SYSDESIGN-008
title: Видеостриминг
domain: arch
category: sysdesign
tags:
- video_streaming
- cdn
- scalability
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
  - "Video Streaming"
  - "Потоковое видео"
---

# Видеостриминг

## Задача

Нужно доставлять видео разным устройствам и скоростям сети.

## Главное

- Исходный файл транскодируют в варианты качества.
- Сегменты раздают через CDN.
- Плеер адаптирует битрейт по состоянию сети.

## Как устроено

Исходное видео загружают в хранилище и перекодируют в несколько профилей качества. Манифест и короткие сегменты позволяют клиенту менять качество по текущей скорости сети; CDN размещает сегменты ближе к зрителю.

## Практический пример

При слабой сети плеер выбирает более низкий битрейт следующего сегмента, сохраняя воспроизведение вместо долгой буферизации.

## Ограничения

Различайте потоковую доставку и хранение оригинала. Важны время подготовки после загрузки, стоимость перекодирования, доступность манифеста и права на контент.

## Что оценить

Оцените суммарные часы видео, число одновременных зрителей, средний битрейт и долю просмотров через CDN. Эти параметры определяют объём хранения производных версий и исходящий трафик; отдельно оцените задержку от загрузки ролика до готовности первого профиля.

## На собеседовании

Разделите путь загрузки и путь просмотра, оцените стоимость хранения вариантов.

## Связанные темы

- [[ARCH-SYSDESIGN-007]] — сначала повторить: Файловое хранилище.
- [[ARCH-COMPONENT-005]] — CDN (Content Delivery Network).
- [[ARCH-COMPONENT-006]] — Blob Storage.

## Источник

- Google Cloud Architecture Center: Well-Architected Framework — https://docs.cloud.google.com/architecture/framework
