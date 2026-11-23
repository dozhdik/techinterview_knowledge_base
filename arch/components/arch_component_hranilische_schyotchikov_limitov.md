---
id: ARCH-COMPONENT-024
title: Хранилище счётчиков лимитов
domain: arch
category: component
tags:
- rate_limiter
- counters
- redis
difficulty: middle
roles:
- all_roles
interview_stage:
- system_design
frequency: high
related:
- ARCH-SYSDESIGN-003
- ARCH-COMPONENT-002
prerequisites:
- ARCH-COMPONENT-020
sources:
- Kleppmann. Designing Data-Intensive Applications, 2017.
author: Команда TechInterview
version: '1.1'
date_created: '2026-11-23'
date_updated: '2026-11-23'
status: review
---

# Хранилище счётчиков лимитов

## Назначение

Хранилище лимитов фиксирует число запросов в окне времени или состояние алгоритма token bucket.

## Главное

- Операции проверки и обновления должны быть согласованными.
- Разделение по ключу снижает горячие точки.
- TTL удаляет устаревшие записи.

## Как устроено

Хранилище лимитов держит счётчики запросов по ключу и времени. Атомарное изменение состояния нужно, чтобы параллельные экземпляры API не пропускали больше запросов, чем задано политикой.

## Практический пример

Для ключа user:42 система считает обращения за минуту и возвращает отказ после порога. TTL удаляет старое окно без ручной очистки.

## Ограничения

При сбое общего хранилища выберите fail-open или fail-closed по риску продукта. Горячие ключи и часы разных узлов могут исказить результат.

## На собеседовании

На распределённом rate limiter объясните гонку двух одновременных запросов.

## Связанные темы

- [[ARCH-COMPONENT-020]] — сначала повторить: Распределённая блокировка.
- [[ARCH-SYSDESIGN-003]] — Rate Limiter (Ограничитель запросов).
- [[ARCH-COMPONENT-002]] — Cache (Кеширование).

## Источник

- Kleppmann. Designing Data-Intensive Applications, 2017.
