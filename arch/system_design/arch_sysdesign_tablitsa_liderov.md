---
id: ARCH-SYSDESIGN-013
title: Таблица лидеров
domain: arch
category: sysdesign
tags:
- leaderboard
- ranking
- caching
difficulty: senior
roles:
- all_roles
interview_stage:
- system_design
frequency: high
related:
- ARCH-COMPONENT-002
- ARCH-COMPONENT-009
prerequisites:
- ARCH-DESIGNPAT-001
sources:
- 'Google Cloud Architecture Center: Well-Architected Framework — https://docs.cloud.google.com/architecture/framework'
author: Команда TechInterview
version: '1.1'
date_created: '2026-11-23'
date_updated: '2026-11-23'
status: review
aliases:
  - "Leaderboard"
---

# Таблица лидеров

## Задача

Нужно быстро показывать позиции игроков и обновлять счёт после событий.

## Главное

- Храните текущий счёт отдельно от истории.
- Структура ранжирования поддерживает top N.
- Правила равенства очков должны быть заранее определены.

## Как устроено

Для рейтинга система принимает изменение счёта и поддерживает упорядоченное представление с быстрым получением верхних позиций и ранга пользователя. Обновления из событий должны иметь уникальный ID.

## Практический пример

После завершения игры счёт увеличивается один раз; клиент получает top-10 и позицию игрока на странице.

## Ограничения

Уточните правило при равных очках и период сброса рейтинга. Для глобального рейтинга важны горячие записи, задержка обновления и согласование лидербордов по регионам.

## Что оценить

Уточните число активных игроков, частоту изменения счёта и запросы на top-K и личный ранг. Для сезонного рейтинга опишите отдельный ключ периода и момент закрытия сезона, чтобы старые события не меняли уже опубликованный итог.

## На собеседовании

Уточните период сброса рейтинга и согласованность после нового результата.

## Связанные темы

- [[ARCH-DESIGNPAT-001]] — сначала повторить: Идемпотентный обработчик.
- [[ARCH-COMPONENT-002]] — Cache (Кеширование).
- [[ARCH-COMPONENT-009]] — Реляционная база данных.

## Источник

- Google Cloud Architecture Center: Well-Architected Framework — https://docs.cloud.google.com/architecture/framework
