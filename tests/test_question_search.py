import pytest

from kb.parser import KnowledgeUnit
from kb.search import search_question


def unit(id, title, content="", tags=None, file_path=""):
    return KnowledgeUnit(id=id, title=title, domain="cs", category="concept",
                         difficulty="junior", content=content, tags=tags or [],
                         file_path=file_path)


@pytest.mark.parametrize("question", [
    "Как устроена хеш-таблица?", "Что такое хеш таблицы?", "What is a hash table?",
])
def test_question_finds_topic_instead_of_whole_sentence(question):
    card = unit("CS-CONCEPT-009", "Хеш-таблица", "Коллизии и вставка элементов.")
    unrelated = unit("CS-CONCEPT-001", "Бинарное дерево")
    assert search_question([unrelated, card], question)[0].unit is card


def test_title_beats_incidental_mention():
    incidental = unit("CS-CONCEPT-001", "Другой алгоритм", "BFS и DFS")
    comparison = unit("CS-QUESTION-003", "Чем BFS отличается от DFS")
    results = search_question([incidental, comparison], "Чем BFS отличается от DFS?")
    assert results[0].unit is comparison


def test_tags_and_filename_are_searchable():
    card = unit("ARCH-COMPONENT-002", "Кеширование", tags=["caching"],
                file_path="arch/components/arch_component_cache_redis_memcached.md")
    assert search_question([card], "Redis")[0].unit is card
    assert search_question([card], "caching")[0].unit is card


@pytest.mark.parametrize("question", ["", "   ", "?!", "как это", "Квантовая запутанность"])
def test_no_match_does_not_return_arbitrary_card(question):
    card = unit("CS-CONCEPT-001", "Рекурсия", "Не запутаться в рекурсии.")
    assert search_question([card], question) == []


def test_explicit_id_has_priority_and_missing_id_does_not_fall_back():
    card = unit("CS-CONCEPT-009", "Хеш-таблица")
    assert search_question([card], "Расскажи про cs-concept-009")[0].unit is card
    assert search_question([card], "Расскажи про CS-CONCEPT-999") == []


@pytest.mark.parametrize("question", [
    "Что такое дерево Меркла?", "Что такое квантовый компьютер?",
    "Дай определение Kubernetes", "Что такое Bloom filter?",
])
def test_missing_definition_does_not_match_general_word_or_body_mention(question):
    cards = [
        unit("CS-CONCEPT-001", "Бинарное дерево", "Квантовый компьютер и дерево Меркла."),
        unit("ARCH-COMPONENT-002", "Кеш", "Bloom filter и Kubernetes упомянуты здесь."),
    ]
    assert search_question(cards, question) == []


def test_results_are_limited_and_empty_database_is_supported():
    cards = [unit(f"CS-CONCEPT-{i:03}", "Алгоритмы") for i in range(5)]
    assert len(search_question(cards, "алгоритм", limit=2)) == 2
    assert search_question(cards, "алгоритм", limit=0) == []
    assert search_question([], "алгоритм") == []
