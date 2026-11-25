---
id: "CS-CONCEPT-040"
title: "Составной B-tree индекс и порядок столбцов"
domain: "cs"
category: "concept"
difficulty: "middle"
status: "review"
tags: [database, sql, postgresql, index, btree, composite_index]
roles: [backend, data_engineer]
interview_stage: [coding, system_design]
frequency: "medium"
related: ["CS-CONCEPT-025", "CS-CONCEPT-032", "CS-QUESTION-006"]
prerequisites: ["CS-CONCEPT-032"]
sources:
  - "PostgreSQL Documentation: Multicolumn Indexes — https://www.postgresql.org/docs/current/indexes-multicolumn.html"
  - "PostgreSQL Documentation: Using EXPLAIN — https://www.postgresql.org/docs/current/using-explain.html"
author: "Редакция базы знаний"
version: "1.0"
date_created: "2026-11-24"
date_updated: "2026-11-24"
aliases:
  - "Composite B-tree Index"
  - "Многоколоночный B-tree индекс"
---

# Составной B-tree индекс и порядок столбцов

## Определение

Составной индекс содержит ключ из нескольких столбцов. В B-tree записи упорядочиваются сначала по первому столбцу ключа, затем по следующему при равенстве предыдущих. Поэтому порядок столбцов влияет на диапазон индекса, который придётся просмотреть.

## Как это работает

Для PostgreSQL B-tree ограничения равенства на ведущих столбцах и ограничение диапазона на первом следующем столбце обычно наиболее эффективно сужают диапазон сканирования. Условие по более позднему столбцу может проверяться через индекс, но само по себе не всегда так же хорошо уменьшает просматриваемую область. Возможности оптимизатора и доступность skip scan зависят от версии и статистики; план нужно проверять на своей версии PostgreSQL.

## Пример

```sql
CREATE INDEX orders_customer_created_idx
    ON orders (customer_id, created_at);

EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM orders
WHERE customer_id = 42 AND created_at >= DATE '2026-01-01';
```

Равенство по `customer_id` и диапазон по `created_at` соответствуют порядку ключа. Для запроса только по `created_at` этот же индекс не обязательно будет лучшим выбором: решение зависит от распределения данных, статистики и версии СУБД.

## Границы и ошибки

- Индекс не гарантирует использование: оптимизатор может выбрать последовательное сканирование, если оно оценивается дешевле.
- Дополнительные индексы занимают место и увеличивают работу при записи; оценивайте их по реальной нагрузке.
- Не обобщайте правило ведущих столбцов на все типы индексов и все СУБД: здесь речь о B-tree PostgreSQL.
- `EXPLAIN ANALYZE` действительно выполняет запрос; для изменяющих данных команд учитывайте побочные эффекты.

## Связанные темы

- [[CS-CONCEPT-025]] — B-tree.
- [[CS-CONCEPT-032]] — индексы реляционной БД.
- [[CS-QUESTION-006]] — когда индекс не ускоряет запрос.

## Источники

- PostgreSQL: [Multicolumn Indexes](https://www.postgresql.org/docs/current/indexes-multicolumn.html).
- PostgreSQL: [Using EXPLAIN](https://www.postgresql.org/docs/current/using-explain.html).
