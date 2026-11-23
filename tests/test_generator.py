import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from kb.generator import (
    generate_unit,
    list_templates,
    _title_to_slug,
    TEMPLATES,
    DOMAIN_TO_DIR,
    CATEGORY_TO_SUBDIR,
)
from kb.registry import Registry
from kb.parser import parse_file


class TestTitleToSlug:

    def test_latin_title(self):
        assert _title_to_slug("Hash Table") == "hash_table"

    def test_multiword(self):
        assert _title_to_slug("Binary Search Tree") == "binary_search_tree"

    def test_cyrillic(self):
        slug = _title_to_slug("Хеш-таблица")
        assert slug != ""
        assert " " not in slug
        assert slug == slug.lower()

    def test_special_chars_removed(self):
        slug = _title_to_slug("Two Sum (Easy)")
        assert "(" not in slug
        assert ")" not in slug

    def test_multiple_spaces(self):
        slug = _title_to_slug("Hash   Table")
        assert "__" not in slug

    def test_empty_title(self):
        slug = _title_to_slug("")
        assert slug == "untitled"

    def test_lowercase(self):
        slug = _title_to_slug("HASH TABLE")
        assert slug == slug.lower()


class TestGenerateUnitDryRun:

    def test_returns_tuple(self):
        path, content = generate_unit(
            title="Hash Table",
            domain="cs",
            category="concept",
            difficulty="junior",
            author="Test",
            dry_run=True,
        )
        assert isinstance(path, str)
        assert isinstance(content, str)

    def test_content_has_frontmatter(self):
        _, content = generate_unit(
            title="Hash Table",
            domain="cs",
            category="concept",
            difficulty="junior",
            author="Test",
            dry_run=True,
        )
        assert content.startswith("---")
        assert "id:" in content
        assert "title:" in content
        assert "domain:" in content

    def test_content_has_title_in_body(self):
        _, content = generate_unit(
            title="Hash Table",
            domain="cs",
            category="concept",
            difficulty="junior",
            author="Test",
            dry_run=True,
        )
        assert "Hash Table" in content

    def test_file_not_created_in_dry_run(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path, _ = generate_unit(
                title="Hash Table",
                domain="cs",
                category="concept",
                difficulty="junior",
                author="Test",
                root_dir=tmpdir,
                dry_run=True,
            )
            assert not os.path.exists(path)

    def test_path_contains_domain_dir(self):
        path, _ = generate_unit(
            title="Hash Table",
            domain="cs",
            category="concept",
            difficulty="junior",
            author="Test",
            dry_run=True,
        )
        assert "cs" in path

    def test_path_contains_category_subdir(self):
        path, _ = generate_unit(
            title="Hash Table",
            domain="cs",
            category="concept",
            difficulty="junior",
            author="Test",
            dry_run=True,
        )
        assert "concepts" in path

    def test_filename_has_md_extension(self):
        path, _ = generate_unit(
            title="Hash Table",
            domain="cs",
            category="concept",
            difficulty="junior",
            author="Test",
            dry_run=True,
        )
        assert path.endswith(".md")

    def test_correct_domain_in_frontmatter(self):
        _, content = generate_unit(
            title="URL Shortener",
            domain="arch",
            category="sysdesign",
            difficulty="middle",
            author="Test",
            dry_run=True,
        )
        assert 'domain: "arch"' in content

    def test_correct_category_in_frontmatter(self):
        _, content = generate_unit(
            title="URL Shortener",
            domain="arch",
            category="sysdesign",
            difficulty="middle",
            author="Test",
            dry_run=True,
        )
        assert 'category: "sysdesign"' in content

    def test_correct_difficulty_in_frontmatter(self):
        _, content = generate_unit(
            title="URL Shortener",
            domain="arch",
            category="sysdesign",
            difficulty="middle",
            author="Test",
            dry_run=True,
        )
        assert 'difficulty: "middle"' in content

    def test_author_in_frontmatter(self):
        _, content = generate_unit(
            title="Hash Table",
            domain="cs",
            category="concept",
            difficulty="junior",
            author="Инженер знаний №1",
            dry_run=True,
        )
        assert "Инженер знаний №1" in content

    def test_status_is_draft(self):
        _, content = generate_unit(
            title="Hash Table",
            domain="cs",
            category="concept",
            difficulty="junior",
            author="Test",
            dry_run=True,
        )
        assert 'status: "draft"' in content


class TestGenerateUnitWithRegistry:

    def test_uses_registry_for_id(self):
        from kb.parser import KnowledgeUnit

        def make_unit(id_, domain="cs", category="concept"):
            return KnowledgeUnit(
                id=id_, title="Test", domain=domain, category=category,
                difficulty="junior", tags=[], roles=[], interview_stage=[],
                frequency="", related=[], prerequisites=[], sources=[],
                author="", version="1.0", date_created="", date_updated="",
                status="draft", file_path="", content="",
            )

        units = [make_unit("CS-CONCEPT-001"), make_unit("CS-CONCEPT-002")]
        registry = Registry.build(units)

        _, content = generate_unit(
            title="Binary Tree",
            domain="cs",
            category="concept",
            difficulty="junior",
            author="Test",
            registry=registry,
            dry_run=True,
        )
        assert 'id: "CS-CONCEPT-003"' in content

    def test_without_registry_id_is_todo(self):
        _, content = generate_unit(
            title="Test",
            domain="cs",
            category="concept",
            difficulty="junior",
            author="Test",
            registry=None,
            dry_run=True,
        )
        assert "TODO" in content


class TestGenerateUnitCreatesFile:

    def test_file_created(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path, _ = generate_unit(
                title="Hash Table",
                domain="cs",
                category="concept",
                difficulty="junior",
                author="Test",
                root_dir=tmpdir,
                dry_run=False,
            )
            assert os.path.exists(path)

    def test_created_file_is_parseable(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path, _ = generate_unit(
                title="Hash Table",
                domain="cs",
                category="concept",
                difficulty="junior",
                author="Test",
                root_dir=tmpdir,
                dry_run=False,
            )
            unit = parse_file(path)
            assert unit.title == "Hash Table"
            assert unit.domain == "cs"
            assert unit.category == "concept"

    def test_creates_parent_dirs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path, _ = generate_unit(
                title="URL Shortener",
                domain="arch",
                category="sysdesign",
                difficulty="middle",
                author="Test",
                root_dir=tmpdir,
                dry_run=False,
            )
            assert os.path.exists(path)
            assert "system_design" in path


class TestTemplates:

    @pytest.mark.parametrize("category,expected_section", [
        ("concept",   "## Определение"),
        ("problem",   "## Условие"),
        ("sysdesign", "## Постановка задачи"),
        ("behavioral","## Структура ответа (STAR)"),
        ("pitfall",   "## Пример ошибки"),
        ("tradeoff",  "## Суть компромисса"),
        ("glossary",  "## Определение"),
        ("cheatsheet","## Ключевые факты"),
        ("component", "## Назначение"),
        ("stage",     "## Описание этапа"),
        ("pattern",   "## Суть паттерна"),
        ("checklist", "## Перед началом"),
        ("strategy",  "## Цель"),
    ])
    def test_template_has_expected_section(self, category, expected_section):
        _, content = generate_unit(
            title="Test Unit",
            domain="cs" if category in ["concept", "problem", "pattern",
                                         "cheatsheet", "pitfall"] else
                   "arch" if category in ["component", "sysdesign",
                                           "tradeoff", "checklist"] else
                   "process",
            category=category,
            difficulty="junior",
            author="Test",
            dry_run=True,
        )
        assert expected_section in content

    def test_all_template_categories_exist(self):
        for category in ["concept", "problem", "sysdesign", "behavioral",
                         "pitfall", "tradeoff", "glossary", "cheatsheet",
                         "component", "stage", "pattern", "checklist", "strategy"]:
            assert category in TEMPLATES, f"Шаблон для '{category}' не найден"


class TestListTemplates:

    def test_list_templates_runs(self, capsys):
        list_templates()
        captured = capsys.readouterr().out
        assert "concept" in captured
        assert "sysdesign" in captured
        assert "behavioral" in captured


class TestMappings:

    def test_all_domains_have_dir(self):
        for domain in ["cs", "arch", "process", "global"]:
            assert domain in DOMAIN_TO_DIR

    def test_key_categories_have_subdir(self):
        for cat in ["concept", "problem", "sysdesign", "behavioral",
                    "component", "tradeoff", "stage", "strategy"]:
            assert cat in CATEGORY_TO_SUBDIR
