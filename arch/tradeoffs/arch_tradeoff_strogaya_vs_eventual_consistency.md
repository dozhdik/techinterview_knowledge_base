---
id: ARCH-TRADEOFF-011
title: Строгая vs eventual consistency
domain: arch
category: tradeoff
tags:
- consistency
- replication
- tradeoffs
difficulty: middle
roles:
- all_roles
interview_stage:
- system_design
frequency: medium
related:
- ARCH-TRADEOFF-001
- ARCH-DESIGNPAT-007
prerequisites:
- ARCH-COMPONENT-008
sources:
- Kleppmann. Designing Data-Intensive Applications, 2017.
author: Команда TechInterview
version: '1.1'
date_created: '2026-11-23'
date_updated: '2026-11-23'
status: review
---

# Строгая vs eventual consistency

## Суть выбора

Строгая модель упрощает рассуждение о последнем значении; eventual допускает временное расхождение реплик.

## Главное

- Строгие гарантии требуют координации.
- eventual подходит, если задержка синхронизации приемлема.
- Важно явно назвать инвариант операции.

## Как устроено

Strong consistency обещает чтение согласованного актуального состояния при оговорённых условиях; eventual consistency допускает временное расхождение копий с последующей сходимостью. Цена сильной гарантии — координация между узлами.

## Практический пример

Остаток последнего товара нельзя безопасно продавать по устаревшей реплике, а число лайков может некоторое время различаться у пользователей.

## Ограничения

Не называйте всю систему «strong» или «eventual» без указания операции. Различайте чтение после собственной записи, порядок обновлений и поведение при сетевом разделении.

## На собеседовании

Разделите показ лайков и списание денег по требованиям к чтению после записи.

## Связанные темы

- [[ARCH-COMPONENT-008]] — сначала повторить: Database Replication.
- [[ARCH-TRADEOFF-001]] — Consistency vs Availability (CAP theorem).
- [[ARCH-DESIGNPAT-007]] — CQRS.

## Источник

- Kleppmann. Designing Data-Intensive Applications, 2017.
