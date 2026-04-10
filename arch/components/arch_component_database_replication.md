---
id: "ARCH-COMPONENT-008"
title: "Database Replication"
domain: "arch"
category: "component"
tags:
  - databases
  - replication
  - high_availability
  - scalability
  - consistency
  - must_know
  - core
difficulty: "senior"
roles:
  - "backend"
  - "devops"
  - "data_engineer"
  - "all_roles"
interview_stage:
  - "system_design"
frequency: "medium"
related:
  - "ARCH-TRADEOFF-003"
  - "ARCH-TRADEOFF-004"
  - "ARCH-SYSDESIGN-001"
  - "ARCH-SYSDESIGN-002"
prerequisites: []
sources:
  - "Martin Kleppmann — Designing Data-Intensive Applications"
  - "PostgreSQL Documentation — Replication"
  - "MySQL Documentation — Replication"
author: "Инженер знаний №2"
version: "1.0"
date_created: "2026-04-10"
date_updated: "2026-04-11"
status: "review"
---

# Database Replication

## Назначение
Database Replication — это механизм копирования данных из одного экземпляра базы данных в один или несколько других экземпляров. Он нужен для повышения доступности, отказоустойчивости и масштабирования чтения. В архитектуре распределённых систем репликация помогает переживать сбои отдельных узлов и разгружать primary node за счёт read replicas.

## Как работает
В типичной схеме primary-replica основной узел принимает записи, а один или несколько replica-узлов получают изменения и применяют их у себя. Репликация может быть synchronous, когда primary ждёт подтверждения от replica, или asynchronous, когда primary отвечает клиенту сразу, а реплики догоняют позже. При асинхронной репликации уменьшается latency записи, но появляется replication lag и риск stale reads. При синхронной репликации выше согласованность, но хуже latency и доступность при сетевых проблемах. Репликация может использовать журнал транзакций, binlog, WAL или поток изменений, в зависимости от конкретной СУБД. Реплики часто используются для read-heavy нагрузки, резервного копирования и failover. При падении primary одна из реплик может быть promoted в новый primary, вручную или автоматически. Репликация повышает устойчивость системы, но сама по себе не решает проблему write scaling и усложняет эксплуатацию, особенно в multi-region сценариях.

## Ключевые характеристики
- **Тип**: механизм репликации базы данных
- **Масштабируемость**: горизонтальная для чтения, ограниченная для записи
- **Консистентность**: strong или eventual, в зависимости от модели репликации

## Популярные реализации
- PostgreSQL Streaming Replication
- MySQL Replication
- MongoDB Replica Set
- Cassandra Replication
- Redis Replication

## Когда использовать
- когда система read-heavy и primary не справляется с чтением
- когда нужна высокая доступность и failover
- когда нужно отделить аналитические или фоновые чтения от боевого primary
- когда требуется disaster recovery или multi-AZ deployment

## Когда НЕ использовать
- когда основная проблема — write throughput, а не чтение
- когда система не может терпеть stale reads вообще
- когда команда не готова к operational complexity failover и lag management
- когда replication добавляют как “магическое решение всех проблем БД”

## Trade-offs
| За | Против |
|----|--------|
| Повышает availability | Добавляет replication lag |
| Масштабирует чтение | Не решает write scaling полностью |
| Позволяет failover | Усложняет эксплуатацию |
| Даёт резервные копии и redundancy | Возможны stale reads |
| Полезна для multi-AZ | Сложнее debugging и consistency guarantees |

## Типичные вопросы на собеседовании
1. Чем synchronous replication отличается от asynchronous replication?
2. Что такое replication lag и как он влияет на чтения?
3. Почему read replica не решает проблему масштабирования записи?
4. Как происходит failover при падении primary?
5. Когда нужна репликация, а когда уже пора делать sharding?
6. Какие риски появляются в multi-primary replication?

## Связанные компоненты
- [[ARCH-TRADEOFF-003]] — согласованность чтений против задержки записи
- [[ARCH-TRADEOFF-004]] — репликация часто идёт до шардирования
- [[ARCH-SYSDESIGN-001]] — история чатов и read path
- [[ARCH-SYSDESIGN-002]] — чтение логов доставки и настроек
