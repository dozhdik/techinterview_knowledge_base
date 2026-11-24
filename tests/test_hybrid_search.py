import asyncio

import pytest
import yaml

from kb import rag, vector_store


PARAPHRASE = "Чем отличается поиск в ширину от поиска в глубину?"
COMPARISON = "Чем BFS отличается от DFS и когда выбирать каждый из них"


class FakeSemanticEmbedder:
    backend = "sentence-transformers"
    model = vector_store.DEFAULT_MODEL

    def embed_documents(self, texts):
        return [[1.0, 0.0] if "Sharding" in text else [0.2, 0.979795897]
                for text in texts]

    def embed_query(self, text):
        return [1.0, 0.0]


@pytest.fixture
def indexed_cards(tmp_path, monkeypatch):
    cards = [
        ("CS-QUESTION-003", "cs", COMPARISON, ["graphs"], "BFS идёт по уровням. DFS обходит ветви."),
        ("CS-CONCEPT-016", "cs", "Поиск в ширину", [], "Обход использует очередь."),
        ("CS-CONCEPT-017", "cs", "Поиск в глубину", [], "Обход использует стек."),
        ("CS-CONCEPT-018", "cs", "Бинарный поиск", [], "Делим диапазон пополам."),
        ("ARCH-TRADEOFF-005", "arch", "Sharding", [], "Шардинг распределяет записи."),
        ("ARCH-COMPONENT-007", "arch", "Поисковый сервис", ["inverted_index"],
         "Токенизация разбивает текст. Лемматизация приводит слова к начальной форме."),
    ]
    for card_id, domain, title, tags, text in cards:
        metadata = {
            "id": card_id, "title": title, "domain": domain, "category": "concept",
            "difficulty": "middle", "status": "review", "tags": tags,
            "related": ["CS-CONCEPT-016"] if card_id == "CS-QUESTION-003" else [],
            "sources": ["Тестовый источник"],
        }
        folder = tmp_path / domain
        folder.mkdir(exist_ok=True)
        (folder / f"{card_id}.md").write_text(
            "---\n" + yaml.safe_dump(metadata, allow_unicode=True) + "---\n" + text,
            encoding="utf-8",
        )
    monkeypatch.setattr(vector_store, "_embedder", lambda backend, model: FakeSemanticEmbedder())
    vector_store.build_index(tmp_path, backend="sentence-transformers")
    return tmp_path


@pytest.mark.parametrize("question", [COMPARISON, PARAPHRASE])
def test_comparison_ranks_before_high_cosine_unrelated_card(indexed_cards, question):
    hits = vector_store.search_index(indexed_cards, question, limit=3)
    assert hits[0].card_id == "CS-QUESTION-003"
    assert {hit.card_id for hit in hits[1:]} == {"CS-CONCEPT-016", "CS-CONCEPT-017"}
    assert hits[0].score == pytest.approx(0.2)
    assert hits[0].related == ["CS-CONCEPT-016"]
    assert hits[0].sources == ["Тестовый источник"]


@pytest.mark.parametrize("question,expected", [
    ("BFS", "CS-CONCEPT-016"),
    ("Что такое breadth-first search?", "CS-CONCEPT-016"),
    ("Что такое обход графа в глубину?", "CS-CONCEPT-017"),
    ("inverted index", "ARCH-COMPONENT-007"),
])
def test_aliases_and_tags_are_searchable(indexed_cards, question, expected):
    assert vector_store.search_index(indexed_cards, question, limit=1)[0].card_id == expected


@pytest.mark.parametrize("question", ["Квантовая запутанность", "Поиск марсианских кристаллов"])
def test_no_topic_match_returns_empty_even_with_high_cosine(indexed_cards, question):
    assert vector_store.search_index(indexed_cards, question) == []


def test_domain_and_explicit_cosine_filters(indexed_cards):
    assert vector_store.search_index(indexed_cards, PARAPHRASE, domain="arch") == []
    assert vector_store.search_index(indexed_cards, "inverted index", domain="arch")[0].domain == "arch"
    assert vector_store.search_index(indexed_cards, COMPARISON, min_score=0.5) == []


def test_body_only_match_needs_vector_support(indexed_cards, monkeypatch):
    assert vector_store.search_index(indexed_cards, "Лемматизация") == []
    monkeypatch.setattr(FakeSemanticEmbedder, "embed_query", lambda self, text: [0.6, 0.8])
    assert vector_store.search_index(indexed_cards, "Лемматизация")[0].card_id == "ARCH-COMPONENT-007"
    assert vector_store.search_index(indexed_cards, "Что такое лемматизация?") == []


def test_rag_retrieves_relevant_cards_using_existing_index(indexed_cards, monkeypatch):
    async def inline(function, *args):
        return function(*args)

    def fail_build(*args, **kwargs):
        pytest.fail("RAG must reuse the fresh index")

    monkeypatch.setattr(rag.asyncio, "to_thread", inline)
    monkeypatch.setattr(rag, "build_index", fail_build)
    config = rag.RagConfig(base_url="http://model.test/v1", model="test-model")
    hits = asyncio.run(rag.retrieve(indexed_cards, PARAPHRASE, [], config))
    assert hits[0].card_id == "CS-QUESTION-003"
    assert {hit.card_id for hit in hits} == {"CS-QUESTION-003", "CS-CONCEPT-016", "CS-CONCEPT-017"}
    assert asyncio.run(rag.retrieve(indexed_cards, "Поиск марсианских кристаллов", [], config)) == []


def test_rag_rejects_backend_mismatch_without_rebuilding(indexed_cards, monkeypatch):
    def fail_build(*args, **kwargs):
        pytest.fail("RAG must not change the existing index backend")

    monkeypatch.setattr(rag, "build_index", fail_build)
    config = rag.RagConfig(base_url="http://model.test/v1", model="test", embedding_backend="hash")
    with pytest.raises(rag.RagError, match="Backend индекса"):
        rag._retrieve_sync(indexed_cards, PARAPHRASE, config)


def test_binary_search_question_ignores_generic_words(indexed_cards):
    hits = vector_store.search_index(indexed_cards, "Объясни принцип работы бинарного поиска")
    assert hits[0].card_id == "CS-CONCEPT-018"
