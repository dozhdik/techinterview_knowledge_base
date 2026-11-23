import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from kb.parser import KnowledgeUnit
from kb.registry import (
    RegistryEntry,
    Registry,
    generate_registry,
)


def make_unit(**kwargs) -> KnowledgeUnit:
    defaults = dict(
        id="CS-CONCEPT-001",
        title="Hash Table",
        domain="cs",
        category="concept",
        difficulty="junior",
        tags=["hash_tables"],
        roles=["all_roles"],
        interview_stage=["coding"],
        frequency="high",
        related=[],
        prerequisites=[],
        sources=["CLRS"],
        author="Test",
        version="1.0",
        date_created="2025-01-01",
        date_updated="2025-01-01",
        status="approved",
        file_path="/repo/cs/concepts/cs_concept_hash_table.md",
        content="# Test content that is long enough.",
    )
    defaults.update(kwargs)
    return KnowledgeUnit(**defaults)


def make_collection() -> list[KnowledgeUnit]:
    return [
        make_unit(id="CS-CONCEPT-001", title="Hash Table",
                  domain="cs", category="concept",
                  difficulty="junior", status="approved",
                  file_path="/repo/cs/concepts/cs_concept_hash_table.md"),
        make_unit(id="CS-CONCEPT-002", title="Binary Tree",
                  domain="cs", category="concept",
                  difficulty="middle", status="approved",
                  file_path="/repo/cs/concepts/cs_concept_binary_tree.md"),
        make_unit(id="CS-PROBLEM-001", title="Two Sum",
                  domain="cs", category="problem",
                  difficulty="junior", status="draft",
                  file_path="/repo/cs/problems/cs_problem_two_sum.md"),
        make_unit(id="ARCH-SYSDESIGN-001", title="URL Shortener",
                  domain="arch", category="sysdesign",
                  difficulty="middle", status="approved",
                  file_path="/repo/arch/system_design/arch_sysdesign_url_shortener.md"),
        make_unit(id="PROC-BEHAVIORAL-001", title="Tell Me About Yourself",
                  domain="process", category="behavioral",
                  difficulty="junior", status="review",
                  file_path="/repo/process/behavioral/proc_behavioral_tell_about_yourself.md"),
    ]


class TestRegistryEntry:

    def test_to_md_row_contains_id(self):
        entry = RegistryEntry(
            id="CS-CONCEPT-001",
            title="Hash Table",
            domain="cs",
            category="concept",
            difficulty="junior",
            status="approved",
            file_path="/repo/cs/concepts/cs_concept_hash_table.md",
        )
        row = entry.to_md_row()
        assert "CS-CONCEPT-001" in row
        assert "Hash Table" in row
        assert "cs" in row

    def test_to_md_row_is_table_format(self):
        entry = RegistryEntry(
            id="CS-CONCEPT-001", title="Test",
            domain="cs", category="concept",
            difficulty="junior", status="approved",
            file_path="/repo/cs/test.md",
        )
        row = entry.to_md_row()
        assert row.startswith("|")
        assert row.endswith("|")


class TestRegistryBuild:

    def test_build_creates_correct_count(self):
        units = make_collection()
        registry = Registry.build(units)
        assert len(registry.entries) == len(units)

    def test_build_entries_sorted_by_id(self):
        units = make_collection()
        registry = Registry.build(units)
        ids = [e.id for e in registry.entries]
        assert ids == sorted(ids)

    def test_build_empty_list(self):
        registry = Registry.build([])
        assert len(registry.entries) == 0

    def test_build_entry_fields(self):
        units = [make_unit(
            id="CS-CONCEPT-001", title="Hash Table",
            domain="cs", category="concept",
            difficulty="junior", status="approved",
        )]
        registry = Registry.build(units)
        entry = registry.entries[0]
        assert entry.id == "CS-CONCEPT-001"
        assert entry.title == "Hash Table"
        assert entry.domain == "cs"
        assert entry.category == "concept"
        assert entry.difficulty == "junior"
        assert entry.status == "approved"


class TestRegistryDuplicates:

    def test_no_duplicates_in_valid_collection(self):
        registry = Registry.build(make_collection())
        assert not registry.has_duplicates()

    def test_finds_duplicates(self):
        units = [
            make_unit(id="CS-CONCEPT-001", file_path="/repo/file1.md"),
            make_unit(id="CS-CONCEPT-001", file_path="/repo/file2.md"),
        ]
        registry = Registry.build(units)
        assert registry.has_duplicates()

    def test_find_duplicates_returns_correct_ids(self):
        units = [
            make_unit(id="CS-CONCEPT-001", file_path="/repo/file1.md"),
            make_unit(id="CS-CONCEPT-001", file_path="/repo/file2.md"),
            make_unit(id="CS-CONCEPT-002", file_path="/repo/file3.md"),
        ]
        registry = Registry.build(units)
        dupes = registry.find_duplicates()
        assert "CS-CONCEPT-001" in dupes
        assert "CS-CONCEPT-002" not in dupes
        assert len(dupes["CS-CONCEPT-001"]) == 2

    def test_no_duplicates_returns_empty_dict(self):
        registry = Registry.build(make_collection())
        assert registry.find_duplicates() == {}


class TestRegistryLookup:

    def test_get_by_id_found(self):
        registry = Registry.build(make_collection())
        entry = registry.get_by_id("CS-CONCEPT-001")
        assert entry is not None
        assert entry.id == "CS-CONCEPT-001"

    def test_get_by_id_not_found(self):
        registry = Registry.build(make_collection())
        entry = registry.get_by_id("XX-UNKNOWN-999")
        assert entry is None

    def test_exists_true(self):
        registry = Registry.build(make_collection())
        assert registry.exists("CS-CONCEPT-001") is True

    def test_exists_false(self):
        registry = Registry.build(make_collection())
        assert registry.exists("XX-UNKNOWN-999") is False


class TestRegistryNextId:

    def test_next_id_after_existing(self):
        units = [
            make_unit(id="CS-CONCEPT-001"),
            make_unit(id="CS-CONCEPT-002"),
        ]
        registry = Registry.build(units)
        next_id = registry.next_id("cs", "concept")
        assert next_id == "CS-CONCEPT-003"

    def test_next_id_first_in_category(self):
        registry = Registry.build(make_collection())
        next_id = registry.next_id("process", "strategy")
        assert next_id == "PROC-STRATEGY-001"

    def test_next_id_format(self):
        registry = Registry.build(make_collection())
        next_id = registry.next_id("arch", "component")
        parts = next_id.split("-")
        assert len(parts) == 3
        assert parts[0] == "ARCH"
        assert parts[1] == "COMPONENT"
        assert parts[2].isdigit()

    def test_next_id_zero_padded(self):
        registry = Registry.build([])
        next_id = registry.next_id("cs", "concept")
        assert next_id == "CS-CONCEPT-001"

    def test_next_id_skips_gaps(self):
        units = [
            make_unit(id="CS-CONCEPT-001"),
            make_unit(id="CS-CONCEPT-005"),
        ]
        registry = Registry.build(units)
        next_id = registry.next_id("cs", "concept")
        assert next_id == "CS-CONCEPT-006"


class TestRegistryStats:

    def test_stats_total(self):
        units = make_collection()
        registry = Registry.build(units)
        stats = registry.stats()
        assert stats["total"] == len(units)

    def test_stats_by_domain(self):
        registry = Registry.build(make_collection())
        stats = registry.stats()
        assert stats["by_domain"]["cs"] == 3
        assert stats["by_domain"]["arch"] == 1
        assert stats["by_domain"]["process"] == 1

    def test_stats_by_status(self):
        registry = Registry.build(make_collection())
        stats = registry.stats()
        assert stats["by_status"]["approved"] == 3
        assert stats["by_status"]["draft"] == 1
        assert stats["by_status"]["review"] == 1

    def test_stats_no_duplicates(self):
        registry = Registry.build(make_collection())
        stats = registry.stats()
        assert stats["duplicates"] == 0

    def test_stats_with_duplicates(self):
        units = [
            make_unit(id="CS-CONCEPT-001", file_path="/f1.md"),
            make_unit(id="CS-CONCEPT-001", file_path="/f2.md"),
        ]
        registry = Registry.build(units)
        stats = registry.stats()
        assert stats["duplicates"] == 1


class TestRegistryToMarkdown:

    def test_to_markdown_is_string(self):
        registry = Registry.build(make_collection())
        md = registry.to_markdown()
        assert isinstance(md, str)

    def test_to_markdown_has_header(self):
        registry = Registry.build(make_collection())
        md = registry.to_markdown()
        assert "# Реестр идентификаторов" in md

    def test_to_markdown_has_stats(self):
        registry = Registry.build(make_collection())
        md = registry.to_markdown()
        assert "Статистика" in md
        assert "5" in md

    def test_to_markdown_has_table(self):
        registry = Registry.build(make_collection())
        md = registry.to_markdown()
        assert "| ID |" in md
        assert "CS-CONCEPT-001" in md

    def test_to_markdown_all_ids_present(self):
        units = make_collection()
        registry = Registry.build(units)
        md = registry.to_markdown()
        for unit in units:
            assert unit.id in md

    def test_to_markdown_warns_about_duplicates(self):
        units = [
            make_unit(id="CS-CONCEPT-001", file_path="/f1.md"),
            make_unit(id="CS-CONCEPT-001", file_path="/f2.md"),
        ]
        registry = Registry.build(units)
        md = registry.to_markdown()
        assert "дублир" in md.lower()


class TestRegistrySave:

    def test_save_creates_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = os.path.join(tmpdir, "_meta", "id_registry.md")
            registry = Registry.build(make_collection())
            registry.save(output)
            assert os.path.exists(output)

    def test_save_file_content(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = os.path.join(tmpdir, "_meta", "id_registry.md")
            registry = Registry.build(make_collection())
            registry.save(output)
            content = open(output, encoding="utf-8").read()
            assert "CS-CONCEPT-001" in content

    def test_generate_registry(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = os.path.join(tmpdir, "_meta", "id_registry.md")
            units = make_collection()
            registry = generate_registry(units, output)
            assert isinstance(registry, Registry)
            assert os.path.exists(output)

    def test_print_stats_runs(self, capsys):
        registry = Registry.build(make_collection())
        registry.print_stats()
        captured = capsys.readouterr().out
        assert "Реестр" in captured
        assert "5" in captured
