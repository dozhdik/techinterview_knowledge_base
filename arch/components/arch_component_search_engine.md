---
id: "ARCH-COMPONENT-007"
title: "Search Engine"
domain: "arch"
category: "component"
tags:
  - search
  - full_text_search
  - indexing
  - distributed_systems
  - scalability
  - must_know
  - core
difficulty: "senior"
roles:
  - "backend"
  - "fullstack"
  - "data_engineer"
  - "all_roles"
interview_stage:
  - "system_design"
frequency: "medium"
related:
  - "ARCH-SYSDESIGN-003"
  - "ARCH-COMPONENT-006"
  - "ARCH-TRADEOFF-001"
prerequisites: []
sources:
  - "Martin Kleppmann — Designing Data-Intensive Applications"
  - "Elasticsearch Documentation"
  - "OpenSearch Documentation"
author: "Инженер знаний №2"
version: "1.0"
date_created: "2026-04-10"
date_updated: "2026-04-11"
status: "review"
---

# Search Engine

## Назначение
Search Engine — это компонент для полнотекстового поиска, фильтрации и ранжирования документов по текстовым запросам. Он нужен там, где обычная SQL-база уже не даёт ни нужной скорости, ни качества поиска. В архитектуре систем search engine обычно отвечает за поиск по товарам, документам, сообщениям, логам и knowledge base, а не за транзакционное хранение исходных данных.

## Как работает
Поисковый движок строит инвертированный индекс, в котором каждому термину соответствует список документов, где он встречается. Когда данные создаются или изменяются в основной системе, они индексируются в search engine синхронно или, чаще, асинхронно через очередь или pipeline обработки событий. Во время запроса движок токенизирует пользовательский ввод, нормализует текст, применяет analyzers, filters, stemming и затем ищет совпадения по индексу. После этого результаты ранжируются по релевантности, популярности, полям документа и другим сигналам. В распределённом режиме индекс делится на shard-ы, а для отказоустойчивости дублируется на replica-шарды. Это даёт хорошую масштабируемость на чтение и поиск, но создаёт отдельную проблему поддержки актуальности индекса. Search engine почти никогда не является source of truth: первичные данные обычно лежат в SQL, NoSQL или object storage, а search хранит индексированное представление для быстрого retrieval.

## Ключевые характеристики
- **Тип**: поисковый индекс / полнотекстовый поисковый движок
- **Масштабируемость**: горизонтальная
- **Консистентность**: чаще eventual

## Популярные реализации
- Elasticsearch
- OpenSearch
- Apache Solr
- Meilisearch
- Typesense

## Когда использовать
- полнотекстовый поиск по товарам, статьям, документам, сообщениям
- поиск по логам и observability данным
- autocomplete, suggestions, ranking и faceted search
- поиск по knowledge base, help center, каталогу вакансий или профилям

## Когда НЕ использовать
- когда нужен source of truth для транзакционных данных
- когда достаточно простого точного lookup по ключу в обычной БД
- когда команда не готова поддерживать отдельный search cluster
- когда объём данных мал и SQL справляется без проблем

## Trade-offs
| За | Против |
|----|--------|
| Очень быстрый full-text search | Не является primary storage |
| Есть ranking, stemming, analyzers | Добавляет отдельный operational complexity |
| Хорошо масштабируется | Индекс может отставать от source of truth |
| Поддерживает фильтры и агрегации | Нужны reindex и careful schema evolution |
| Подходит для autocomplete и typo tolerance | Дороже по памяти и диску, чем простая БД |

## Типичные вопросы на собеседовании
1. Почему нельзя просто сделать `LIKE '%query%'` в SQL?
2. Что такое inverted index и почему он быстрее для поиска?
3. Почему search engine не должен быть source of truth?
4. Как синхронизировать search index с основной базой?
5. Что делать при изменении mapping и необходимости reindex?
6. Как решать проблему stale index и eventual consistency?

## Связанные компоненты
- [[ARCH-SYSDESIGN-003]] — автодополнение поверх инвертированного или префиксного индекса
- [[ARCH-COMPONENT-006]] — файлы в object storage, в индексе — метаданные и извлечённый текст
- [[ARCH-TRADEOFF-001]] — форма поискового API (REST, BFF, при необходимости GraphQL)
