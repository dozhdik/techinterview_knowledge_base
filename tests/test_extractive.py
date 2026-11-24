import asyncio
from types import SimpleNamespace

from kb import extractive
from web import server


def test_complete_sections_preserve_code_and_remove_service_ids():
    unit = SimpleNamespace(id='CS-TEST-001', title='Поиск', content='''# Поиск

## Определение

Определение алгоритма.

## Как это работает

Полное предложение.

```python
print("ok")
```

## Источники

[[CS-TEST-002]]
''')
    result = extractive.form_answer('Как это работает?', [unit], [SimpleNamespace(card_id=unit.id)])
    assert 'Полное предложение.' in result.answer
    assert '```python\nprint("ok")\n```' in result.answer
    assert 'Источники' not in result.answer and '[[CS-' not in result.answer
    assert result.units == [unit]


def test_no_hits_returns_none():
    assert extractive.form_answer('неизвестно', [], []) is None


def test_default_api_uses_extractive_even_with_model_environment(monkeypatch):
    monkeypatch.setenv('RAG_BASE_URL', 'http://unavailable/v1')
    monkeypatch.setenv('RAG_MODEL', 'unused')
    monkeypatch.delenv('RAG_ENABLED', raising=False)
    unit = SimpleNamespace(id='CS-TEST-001', title='Тест')
    monkeypatch.setattr(server, 'load_units', lambda: [unit])
    monkeypatch.setattr(server, 'search_and_extract', lambda *args: extractive.ExtractiveResult('## Определение\n\nТекст.', [unit]))
    async def inline(function, *args): return function(*args)
    monkeypatch.setattr(server.asyncio, 'to_thread', inline)
    monkeypatch.setattr(server, 'generate', lambda *args: (_ for _ in ()).throw(AssertionError('LLM called')))
    result = asyncio.run(server.ask(server.AskRequest(question='Что такое тест?')))
    assert result.answer.endswith('Текст.') and not result.is_rag_enabled
    assert [s.id for s in result.sources] == ['CS-TEST-001']


def test_index_row_cache_invalidates_after_sqlite_change(tmp_path):
    import sqlite3
    from kb.vector_store import _cached_rows
    path = tmp_path / 'index.sqlite3'
    with sqlite3.connect(path) as db:
        db.execute('CREATE TABLE chunks (domain TEXT, text TEXT)')
        db.execute('INSERT INTO chunks VALUES (?, ?)', ('cs', 'старый'))
    def read():
        stat = path.stat()
        return _cached_rows(str(path), 'cs', stat.st_mtime_ns, stat.st_ctime_ns, stat.st_size)
    assert read()[0]['text'] == 'старый'
    assert read() is read()
    with sqlite3.connect(path) as db:
        db.execute('UPDATE chunks SET text=?', ('новый материал',))
    assert read()[0]['text'] == 'новый материал'


def test_scaling_synonym_and_generic_question_word():
    from kb.search import _question_terms
    assert 'scaling' in _question_terms('Когда следует выбирать горизонтальное масштабирование?')
    assert 'следует' not in _question_terms('Когда следует выбирать горизонтальное масштабирование?')
