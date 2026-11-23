from pathlib import Path

import pytest

from kb.vector_store import VectorIndexError, build_index, index_status, search_index


def _card(path, card_id, title, body, status="review"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\nid: {card_id}\ntitle: {title}\ndomain: cs\ncategory: concept\n"
        f"difficulty: middle\nstatus: {status}\ntags: [test]\n"
        f"related: []\nprerequisites: []\nsources: [test]\n---\n\n"
        f"# {title}\n\n## Определение\n\n{body}\n",
        encoding="utf-8",
    )


def test_build_search_update_and_remove(tmp_path):
    first = tmp_path / "cs" / "concepts" / "hash.md"
    second = tmp_path / "cs" / "concepts" / "queue.md"
    draft = tmp_path / "cs" / "concepts" / "draft.md"
    _card(first, "CS-CONCEPT-001", "Хеш-таблица", "Хеш-таблица хранит пары ключ и значение.")
    _card(second, "CS-CONCEPT-002", "Очередь", "Очередь выдаёт элементы в порядке FIFO.")
    _card(draft, "CS-CONCEPT-003", "Черновик", "Этот материал не должен попадать в индекс.", "draft")
    index = tmp_path / "index.sqlite3"

    built = build_index(tmp_path, index)
    assert built["cards"] == 2
    assert built["updated"] == 2
    assert index_status(tmp_path, index)["fresh"] is True
    hits = search_index(tmp_path, "хеш таблица", index, limit=1)
    assert hits[0].card_id == "CS-CONCEPT-001"
    assert hits[0].source_path == "cs/concepts/hash.md"
    assert build_index(tmp_path, index)["updated"] == 0

    _card(first, "CS-CONCEPT-001", "Хеш-таблица", "Хеш-таблица поддерживает быстрый поиск по ключу.")
    assert index_status(tmp_path, index)["fresh"] is False
    with pytest.raises(VectorIndexError, match="изменились"):
        search_index(tmp_path, "хеш таблица", index)
    assert build_index(tmp_path, index)["updated"] == 1

    second.unlink()
    result = build_index(tmp_path, index)
    assert result["cards"] == 1
    assert result["removed"] == 1


def test_chunking_excludes_reference_sections(tmp_path):
    path = tmp_path / "cs" / "concepts" / "long.md"
    body = "\n\n".join("Полезное объяснение поиска по графу. " * 6 for _ in range(7))
    _card(path, "CS-CONCEPT-001", "Поиск в графе", body)
    path.write_text(path.read_text(encoding="utf-8")
                    + "\n## Связанные темы\n\n- [[CS-CONCEPT-999]]\n"
                    + "\n## Источник\n\n- Тестовый источник\n", encoding="utf-8")
    result = build_index(tmp_path, tmp_path / "index.sqlite3", max_chars=300)
    assert result["chunks"] > 1
    hits = search_index(tmp_path, "поиск граф", tmp_path / "index.sqlite3", limit=20)
    assert hits
    assert all("CS-CONCEPT-999" not in hit.text for hit in hits)
    assert all("Тестовый источник" not in hit.text for hit in hits)
    assert all(len(hit.text) <= 300 for hit in hits)
