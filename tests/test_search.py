import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from kb.parser import KnowledgeUnit
from kb.search import (
    SearchQuery,
    SearchResult,
    search,
    search_by_domain,
    search_by_difficulty,
    search_by_tag,
    search_by_role,
    search_by_text,
    print_results,
)


def make_unit(**kwargs) -> KnowledgeUnit:
    defaults = dict(
        id="CS-CONCEPT-001",
        title="Hash Table",
        domain="cs",
        category="concept",
        difficulty="junior",
        tags=["hash_tables", "must_know", "arrays"],
        roles=["backend", "fullstack"],
        interview_stage=["coding", "phone_screen"],
        frequency="high",
        related=[],
        prerequisites=[],
        sources=["CLRS"],
        author="Test",
        version="1.0",
        date_created="2025-01-01",
        date_updated="2025-01-01",
        status="approved",
        file_path="/tmp/test.md",
        content="Это содержимое единицы знаний про хеш-таблицы и алгоритмы.",
    )
    defaults.update(kwargs)
    return KnowledgeUnit(**defaults)


def make_collection() -> list[KnowledgeUnit]:
    return [
        make_unit(
            id="CS-CONCEPT-001", title="Hash Table",
            domain="cs", category="concept", difficulty="junior",
            tags=["hash_tables", "must_know"],
            roles=["all_roles"],
            interview_stage=["coding"],
            frequency="high", status="approved",
        ),
        make_unit(
            id="CS-PROBLEM-001", title="Two Sum",
            domain="cs", category="problem", difficulty="junior",
            tags=["arrays", "hash_tables"],
            roles=["backend"],
            interview_stage=["coding"],
            frequency="high", status="approved",
        ),
        make_unit(
            id="CS-CONCEPT-002", title="Binary Tree",
            domain="cs", category="concept", difficulty="middle",
            tags=["trees", "must_know"],
            roles=["all_roles"],
            interview_stage=["coding", "phone_screen"],
            frequency="medium", status="approved",
        ),
        make_unit(
            id="ARCH-SYSDESIGN-001", title="URL Shortener",
            domain="arch", category="sysdesign", difficulty="middle",
            tags=["databases", "caching", "must_know"],
            roles=["backend", "fullstack"],
            interview_stage=["system_design"],
            frequency="high", status="approved",
        ),
        make_unit(
            id="PROC-BEHAVIORAL-001", title="Tell Me About Yourself",
            domain="process", category="behavioral", difficulty="junior",
            tags=["communication", "frequently_asked"],
            roles=["all_roles"],
            interview_stage=["behavioral", "hr_screening"],
            frequency="high", status="draft",
        ),
        make_unit(
            id="ARCH-TRADEOFF-001", title="SQL vs NoSQL",
            domain="arch", category="tradeoff", difficulty="senior",
            tags=["databases", "tradeoffs"],
            roles=["backend", "data_engineer"],
            interview_stage=["system_design"],
            frequency="medium", status="approved",
        ),
    ]


class TestSearchQuery:

    def test_default_query_all_none(self):
        q = SearchQuery()
        assert q.domain is None
        assert q.difficulty is None
        assert q.tags == []
        assert q.text is None

    def test_query_with_params(self):
        q = SearchQuery(domain="cs", difficulty="junior", tags=["arrays"])
        assert q.domain == "cs"
        assert q.difficulty == "junior"
        assert q.tags == ["arrays"]


class TestSearchByDomain:

    def test_filters_by_domain(self):
        units = make_collection()
        results = search(units, SearchQuery(domain="cs"))
        assert all(r.unit.domain == "cs" for r in results)

    def test_domain_arch(self):
        units = make_collection()
        results = search(units, SearchQuery(domain="arch"))
        assert len(results) == 2
        assert all(r.unit.domain == "arch" for r in results)

    def test_domain_process(self):
        units = make_collection()
        results = search(units, SearchQuery(domain="process"))
        assert len(results) == 1

    def test_nonexistent_domain_returns_empty(self):
        units = make_collection()
        results = search(units, SearchQuery(domain="unknown"))
        assert results == []

    def test_wrapper_function(self):
        units = make_collection()
        results = search_by_domain(units, "cs")
        assert all(r.unit.domain == "cs" for r in results)


class TestSearchByDifficulty:

    def test_filters_junior(self):
        units = make_collection()
        results = search(units, SearchQuery(difficulty="junior"))
        assert all(r.unit.difficulty == "junior" for r in results)
        assert len(results) == 3

    def test_filters_middle(self):
        units = make_collection()
        results = search(units, SearchQuery(difficulty="middle"))
        assert len(results) == 2

    def test_filters_senior(self):
        units = make_collection()
        results = search(units, SearchQuery(difficulty="senior"))
        assert len(results) == 1

    def test_wrapper_function(self):
        units = make_collection()
        results = search_by_difficulty(units, "junior")
        assert all(r.unit.difficulty == "junior" for r in results)


class TestSearchByTags:

    def test_single_tag(self):
        units = make_collection()
        results = search(units, SearchQuery(tags=["hash_tables"]))
        assert len(results) == 2
        assert all("hash_tables" in r.unit.tags for r in results)

    def test_multiple_tags_AND_logic(self):
        units = make_collection()
        results = search(units, SearchQuery(tags=["hash_tables", "arrays"]))
        assert len(results) == 1
        assert results[0].unit.id == "CS-PROBLEM-001"

    def test_nonexistent_tag_returns_empty(self):
        units = make_collection()
        results = search(units, SearchQuery(tags=["nonexistent_tag"]))
        assert results == []

    def test_wrapper_function(self):
        units = make_collection()
        results = search_by_tag(units, "must_know")
        assert all("must_know" in r.unit.tags for r in results)


class TestSearchByRole:

    def test_all_roles_matches_any_role(self):
        units = make_collection()
        results = search(units, SearchQuery(role="frontend"))
        ids = [r.unit.id for r in results]
        assert "CS-CONCEPT-001" in ids

    def test_specific_role(self):
        units = make_collection()
        results = search(units, SearchQuery(role="data_engineer"))
        ids = [r.unit.id for r in results]
        assert "ARCH-TRADEOFF-001" in ids

    def test_nonexistent_role_returns_only_all_roles(self):
        units = make_collection()
        results = search(units, SearchQuery(role="quantum_engineer"))
        assert all("all_roles" in r.unit.roles for r in results)

    def test_wrapper_function(self):
        units = make_collection()
        results = search_by_role(units, "backend")
        assert len(results) > 0


class TestSearchByStage:

    def test_coding_stage(self):
        units = make_collection()
        results = search(units, SearchQuery(interview_stage="coding"))
        assert all("coding" in r.unit.interview_stage for r in results)

    def test_system_design_stage(self):
        units = make_collection()
        results = search(units, SearchQuery(interview_stage="system_design"))
        ids = [r.unit.id for r in results]
        assert "ARCH-SYSDESIGN-001" in ids
        assert "ARCH-TRADEOFF-001" in ids

    def test_behavioral_stage(self):
        units = make_collection()
        results = search(units, SearchQuery(interview_stage="behavioral"))
        assert len(results) == 1
        assert results[0].unit.id == "PROC-BEHAVIORAL-001"


class TestSearchByText:

    def test_search_in_title(self):
        units = make_collection()
        results = search(units, SearchQuery(text="Hash Table"))
        assert len(results) >= 1
        assert results[0].unit.id == "CS-CONCEPT-001"

    def test_search_case_insensitive(self):
        units = make_collection()
        results_lower = search(units, SearchQuery(text="hash table"))
        results_upper = search(units, SearchQuery(text="HASH TABLE"))
        assert len(results_lower) == len(results_upper)

    def test_search_in_content(self):
        units = make_collection()
        results = search(units, SearchQuery(text="алгоритмы"))
        assert len(results) >= 1

    def test_search_no_match_returns_empty(self):
        units = make_collection()
        results = search(units, SearchQuery(text="квантовые вычисления xyz"))
        assert results == []

    def test_title_match_scores_higher_than_content(self):
        units = make_collection()
        results = search(units, SearchQuery(text="hash"))
        if len(results) >= 2:
            assert results[0].score >= results[1].score

    def test_wrapper_function(self):
        units = make_collection()
        results = search_by_text(units, "Tree")
        assert any(r.unit.id == "CS-CONCEPT-002" for r in results)


class TestCombinedSearch:

    def test_domain_and_difficulty(self):
        units = make_collection()
        results = search(units, SearchQuery(domain="cs", difficulty="junior"))
        assert all(r.unit.domain == "cs" for r in results)
        assert all(r.unit.difficulty == "junior" for r in results)

    def test_domain_and_category(self):
        units = make_collection()
        results = search(units, SearchQuery(domain="arch", category="sysdesign"))
        assert len(results) == 1
        assert results[0].unit.id == "ARCH-SYSDESIGN-001"

    def test_domain_tag_difficulty(self):
        units = make_collection()
        results = search(units, SearchQuery(
            domain="cs",
            difficulty="junior",
            tags=["hash_tables"]
        ))
        assert len(results) >= 1
        assert all(r.unit.domain == "cs" for r in results)

    def test_combined_no_match(self):
        units = make_collection()
        results = search(units, SearchQuery(domain="cs", difficulty="staff"))
        assert results == []

    def test_status_filter(self):
        units = make_collection()
        results = search(units, SearchQuery(status="draft"))
        assert len(results) == 1
        assert results[0].unit.id == "PROC-BEHAVIORAL-001"

    def test_frequency_filter(self):
        units = make_collection()
        results = search(units, SearchQuery(frequency="medium"))
        assert len(results) == 2


class TestEdgeCases:

    def test_empty_units_list(self):
        results = search([], SearchQuery(domain="cs"))
        assert results == []

    def test_empty_query_returns_all(self):
        units = make_collection()
        results = search(units, SearchQuery())
        assert len(results) == len(units)

    def test_results_sorted_by_score(self):
        units = make_collection()
        results = search(units, SearchQuery(domain="cs"))
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_search_result_has_matched_info(self):
        units = make_collection()
        results = search(units, SearchQuery(domain="cs", tags=["must_know"]))
        assert all(len(r.matched) > 0 for r in results)


class TestPrintResults:

    def test_prints_found_count(self, capsys):
        units = make_collection()
        results = search(units, SearchQuery(domain="cs"))
        print_results(results)
        captured = capsys.readouterr().out
        assert "Найдено" in captured

    def test_prints_nothing_found(self, capsys):
        print_results([])
        captured = capsys.readouterr().out
        assert "Ничего не найдено" in captured

    def test_verbose_shows_score(self, capsys):
        units = make_collection()
        results = search(units, SearchQuery(domain="cs"))
        print_results(results, verbose=True)
        captured = capsys.readouterr().out
        assert "score=" in captured
