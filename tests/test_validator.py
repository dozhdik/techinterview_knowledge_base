"""
tests/test_validator.py

Тесты для kb/validator.py
Запуск: python -m pytest tests/test_validator.py -v
"""

import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from kb.parser import KnowledgeUnit
from kb.validator import (
    ValidationResult,
    ValidationIssue,
    validate_unit,
    validate_all,
    validate_file,
)


# ---------------------------------------------------------------------------
# Вспомогательные функции
# ---------------------------------------------------------------------------

def make_unit(**kwargs) -> KnowledgeUnit:
    """Создаёт валидную единицу знаний, поля можно переопределить через kwargs."""
    defaults = dict(
        id="CS-CONCEPT-001",
        title="Test Unit",
        domain="cs",
        category="concept",
        difficulty="junior",
        tags=["arrays", "must_know"],
        roles=["all_roles"],
        interview_stage=["coding"],
        frequency="high",
        related=[],
        prerequisites=[],
        sources=["CLRS 4th Edition"],
        author="Инженер знаний №1",
        version="1.0",
        date_created="2025-01-01",
        date_updated="2025-01-01",
        status="approved",
        file_path="/tmp/test.md",
        content="# Test\n\nЭто тестовая единица знаний с достаточным содержимым.",
    )
    defaults.update(kwargs)
    return KnowledgeUnit(**defaults)


def make_md_file(content: str) -> str:
    """Создаёт временный .md файл, возвращает путь."""
    f = tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    )
    f.write(content)
    f.close()
    return f.name


VALID_MD = """\
---
id: "CS-CONCEPT-099"
title: "Тестовая концепция"
domain: "cs"
category: "concept"
difficulty: "middle"
tags:
  - arrays
roles:
  - "backend"
interview_stage:
  - "coding"
frequency: "high"
related: []
prerequisites: []
sources:
  - "CLRS 4th Edition"
author: "Тест"
version: "1.0"
date_created: "2025-01-01"
date_updated: "2025-01-01"
status: "approved"
---

# Тестовая концепция

Это достаточно длинное содержимое для прохождения валидации контента.
"""


# ---------------------------------------------------------------------------
# Тесты: ValidationResult
# ---------------------------------------------------------------------------

class TestValidationResult:

    def test_is_valid_when_no_errors(self):
        result = ValidationResult()
        assert result.is_valid is True

    def test_not_valid_when_has_errors(self):
        result = ValidationResult()
        result.add_error("CS-001", "id", "test error")
        assert result.is_valid is False

    def test_errors_property(self):
        result = ValidationResult()
        result.add_error("CS-001", "id", "error")
        result.add_warning("CS-001", "title", "warning")
        assert len(result.errors) == 1
        assert len(result.warnings) == 1

    def test_warnings_dont_invalidate(self):
        result = ValidationResult()
        result.add_warning("CS-001", "sources", "no sources")
        assert result.is_valid is True

    def test_print_report_no_issues(self, capsys):
        result = ValidationResult()
        result.print_report()
        assert "✅" in capsys.readouterr().out

    def test_print_report_with_issues(self, capsys):
        result = ValidationResult()
        result.add_error("CS-001", "id", "bad id")
        result.print_report()
        captured = capsys.readouterr().out
        assert "❌" in captured


# ---------------------------------------------------------------------------
# Тесты: validate_unit — успешные сценарии
# ---------------------------------------------------------------------------

class TestValidateUnitSuccess:

    def test_valid_unit_has_no_errors(self):
        unit = make_unit()
        result = validate_unit(unit)
        assert result.is_valid

    def test_all_valid_domains(self):
        for domain in ["cs", "arch", "process", "global"]:
            unit = make_unit(domain=domain)
            result = validate_unit(unit)
            errors = [e for e in result.errors if e.field == "domain"]
            assert errors == [], f"Domain '{domain}' не должен давать ошибку"

    def test_all_valid_difficulties(self):
        for diff in ["junior", "middle", "senior", "staff"]:
            unit = make_unit(difficulty=diff)
            result = validate_unit(unit)
            errors = [e for e in result.errors if e.field == "difficulty"]
            assert errors == []

    def test_all_valid_categories(self):
        for cat in ["concept", "problem", "sysdesign", "behavioral", "glossary"]:
            unit = make_unit(category=cat)
            result = validate_unit(unit)
            errors = [e for e in result.errors if e.field == "category"]
            assert errors == []


# ---------------------------------------------------------------------------
# Тесты: validate_unit — ошибки в полях
# ---------------------------------------------------------------------------

class TestValidateUnitErrors:

    def test_invalid_id_format(self):
        unit = make_unit(id="bad-id")
        result = validate_unit(unit)
        errors = [e for e in result.errors if e.field == "id"]
        assert len(errors) == 1

    def test_valid_id_format(self):
        unit = make_unit(id="CS-CONCEPT-042")
        result = validate_unit(unit)
        errors = [e for e in result.errors if e.field == "id"]
        assert errors == []

    def test_empty_id(self):
        unit = make_unit(id="")
        result = validate_unit(unit)
        errors = [e for e in result.errors if e.field == "id"]
        assert len(errors) == 1

    def test_empty_title(self):
        unit = make_unit(title="")
        result = validate_unit(unit)
        errors = [e for e in result.errors if e.field == "title"]
        assert len(errors) == 1

    def test_invalid_domain(self):
        unit = make_unit(domain="unknown")
        result = validate_unit(unit)
        errors = [e for e in result.errors if e.field == "domain"]
        assert len(errors) == 1

    def test_invalid_category(self):
        unit = make_unit(category="superduper")
        result = validate_unit(unit)
        errors = [e for e in result.errors if e.field == "category"]
        assert len(errors) == 1

    def test_invalid_difficulty(self):
        unit = make_unit(difficulty="god")
        result = validate_unit(unit)
        errors = [e for e in result.errors if e.field == "difficulty"]
        assert len(errors) == 1


# ---------------------------------------------------------------------------
# Тесты: validate_unit — предупреждения
# ---------------------------------------------------------------------------

class TestValidateUnitWarnings:

    def test_empty_content_gives_warning(self):
        unit = make_unit(content="")
        result = validate_unit(unit)
        warnings = [w for w in result.warnings if w.field == "content"]
        assert len(warnings) == 1

    def test_short_content_gives_warning(self):
        unit = make_unit(content="# Hi")
        result = validate_unit(unit)
        warnings = [w for w in result.warnings if w.field == "content"]
        assert len(warnings) == 1

    def test_no_sources_gives_warning(self):
        unit = make_unit(sources=[])
        result = validate_unit(unit)
        warnings = [w for w in result.warnings if w.field == "sources"]
        assert len(warnings) == 1

    def test_invalid_role_gives_warning(self):
        unit = make_unit(roles=["superrole"])
        result = validate_unit(unit)
        warnings = [w for w in result.warnings if w.field == "roles"]
        assert len(warnings) == 1

    def test_invalid_stage_gives_warning(self):
        unit = make_unit(interview_stage=["telepathy"])
        result = validate_unit(unit)
        warnings = [w for w in result.warnings if w.field == "interview_stage"]
        assert len(warnings) == 1

    def test_invalid_status_gives_warning(self):
        unit = make_unit(status="published")
        result = validate_unit(unit)
        warnings = [w for w in result.warnings if w.field == "status"]
        assert len(warnings) == 1

    def test_invalid_frequency_gives_warning(self):
        unit = make_unit(frequency="always")
        result = validate_unit(unit)
        warnings = [w for w in result.warnings if w.field == "frequency"]
        assert len(warnings) == 1


# ---------------------------------------------------------------------------
# Тесты: validate_all
# ---------------------------------------------------------------------------

class TestValidateAll:

    def test_valid_collection_passes(self):
        units = [
            make_unit(id="CS-CONCEPT-001"),
            make_unit(id="CS-CONCEPT-002"),
            make_unit(id="ARCH-COMPONENT-001", domain="arch", category="component"),
        ]
        result = validate_all(units)
        assert result.is_valid

    def test_duplicate_ids_give_error(self):
        units = [
            make_unit(id="CS-CONCEPT-001"),
            make_unit(id="CS-CONCEPT-001"),
        ]
        result = validate_all(units)
        errors = [e for e in result.errors if e.field == "id" and "Дублир" in e.message]
        assert len(errors) > 0

    def test_broken_related_reference_gives_warning(self):
        units = [
            make_unit(id="CS-CONCEPT-001", related=["CS-CONCEPT-999"]),
        ]
        result = validate_all(units)
        warnings = [w for w in result.warnings if w.field == "related"]
        assert len(warnings) == 1

    def test_valid_related_reference_no_warning(self):
        units = [
            make_unit(id="CS-CONCEPT-001", related=["CS-CONCEPT-002"]),
            make_unit(id="CS-CONCEPT-002"),
        ]
        result = validate_all(units)
        warnings = [w for w in result.warnings if w.field == "related"]
        assert warnings == []

    def test_broken_prerequisites_gives_warning(self):
        units = [
            make_unit(id="CS-CONCEPT-001", prerequisites=["CS-CONCEPT-999"]),
        ]
        result = validate_all(units)
        warnings = [w for w in result.warnings if w.field == "prerequisites"]
        assert len(warnings) == 1

    def test_empty_list_passes(self):
        result = validate_all([])
        assert result.is_valid

    def test_multiple_errors_collected(self):
        units = [
            make_unit(id="bad-id", domain="wrong", difficulty="god"),
        ]
        result = validate_all(units)
        assert len(result.errors) >= 3


# ---------------------------------------------------------------------------
# Тесты: validate_file
# ---------------------------------------------------------------------------

class TestValidateFile:

    def test_valid_file_passes(self):
        path = make_md_file(VALID_MD)
        result = validate_file(path)
        assert result.is_valid
        os.unlink(path)

    def test_nonexistent_file_gives_error(self):
        result = validate_file("nonexistent.md")
        assert not result.is_valid
        assert any(i.field == "file" for i in result.errors)

    def test_file_without_frontmatter_gives_error(self):
        path = make_md_file("# No frontmatter here")
        result = validate_file(path)
        assert not result.is_valid
        os.unlink(path)
