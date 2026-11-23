import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from kb.parser import (
    KnowledgeUnit,
    ParseError,
    parse_file,
    parse_directory,
    parse_file_safe,
    summary,
)


def make_md(content: str, suffix=".md") -> str:
    f = tempfile.NamedTemporaryFile(
        mode="w", suffix=suffix, delete=False, encoding="utf-8"
    )
    f.write(content)
    f.close()
    return f.name


VALID_MD = """\
---
id: "CS-CONCEPT-017"
title: "Хеш-таблица (Hash Table)"
domain: "cs"
category: "concept"
difficulty: "junior"
tags:
  - hash_tables
  - must_know
roles:
  - "all_roles"
interview_stage:
  - "coding"
frequency: "high"
related:
  - "CS-CONCEPT-003"
prerequisites:
  - "CS-CONCEPT-003"
sources:
  - "CLRS 4th Edition, Chapter 11"
author: "Инженер знаний №1"
version: "1.0"
date_created: "2025-03-01"
date_updated: "2025-03-01"
status: "approved"
---

# Хеш-таблица (Hash Table)

## Определение
Структура данных с O(1) поиском.
"""


class TestParseFileSuccess:

    def test_returns_knowledge_unit(self):
        path = make_md(VALID_MD)
        unit = parse_file(path)
        assert isinstance(unit, KnowledgeUnit)
        os.unlink(path)

    def test_id_parsed(self):
        path = make_md(VALID_MD)
        unit = parse_file(path)
        assert unit.id == "CS-CONCEPT-017"
        os.unlink(path)

    def test_title_parsed(self):
        path = make_md(VALID_MD)
        unit = parse_file(path)
        assert unit.title == "Хеш-таблица (Hash Table)"
        os.unlink(path)

    def test_domain_parsed(self):
        path = make_md(VALID_MD)
        unit = parse_file(path)
        assert unit.domain == "cs"
        os.unlink(path)

    def test_tags_are_list(self):
        path = make_md(VALID_MD)
        unit = parse_file(path)
        assert isinstance(unit.tags, list)
        assert "hash_tables" in unit.tags
        os.unlink(path)

    def test_related_parsed(self):
        path = make_md(VALID_MD)
        unit = parse_file(path)
        assert "CS-CONCEPT-003" in unit.related
        os.unlink(path)

    def test_content_extracted(self):
        path = make_md(VALID_MD)
        unit = parse_file(path)
        assert "Хеш-таблица" in unit.content
        assert "---" not in unit.content.split("\n")[0]
        os.unlink(path)

    def test_file_path_stored(self):
        path = make_md(VALID_MD)
        unit = parse_file(path)
        assert unit.file_path != ""
        os.unlink(path)

    def test_status_default_if_missing(self):
        md = VALID_MD.replace('status: "approved"\n', "")
        path = make_md(md)
        unit = parse_file(path)
        assert unit.status == "draft"
        os.unlink(path)


class TestParseFileErrors:

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            parse_file("non_existent_file.md")

    def test_wrong_extension(self):
        path = make_md(VALID_MD, suffix=".txt")
        with pytest.raises(ParseError):
            parse_file(path)
        os.unlink(path)

    def test_no_frontmatter(self):
        path = make_md("# Просто заголовок\n\nБез фронтматтера.")
        with pytest.raises(ParseError):
            parse_file(path)
        os.unlink(path)

    def test_missing_required_field_id(self):
        md = VALID_MD.replace('id: "CS-CONCEPT-017"\n', "")
        path = make_md(md)
        with pytest.raises(ParseError) as exc_info:
            parse_file(path)
        assert "id" in str(exc_info.value)
        os.unlink(path)

    def test_missing_required_field_title(self):
        md = VALID_MD.replace('title: "Хеш-таблица (Hash Table)"\n', "")
        path = make_md(md)
        with pytest.raises(ParseError):
            parse_file(path)
        os.unlink(path)

    def test_invalid_yaml(self):
        bad_yaml = "---\nid: [unclosed bracket\n---\n# Content"
        path = make_md(bad_yaml)
        with pytest.raises(ParseError):
            parse_file(path)
        os.unlink(path)


class TestParseFileSafe:

    def test_returns_unit_on_valid(self):
        path = make_md(VALID_MD)
        unit = parse_file_safe(path)
        assert unit is not None
        assert unit.id == "CS-CONCEPT-017"
        os.unlink(path)

    def test_returns_none_on_error(self):
        result = parse_file_safe("nonexistent.md")
        assert result is None

    def test_returns_none_on_bad_yaml(self):
        path = make_md("---\nbad: [yaml\n---\n# hi")
        result = parse_file_safe(path)
        assert result is None
        os.unlink(path)


class TestParseDirectory:

    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def _write(self, filename: str, content: str):
        path = os.path.join(self.tmpdir, filename)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def _make_unit_md(self, unit_id: str, domain: str = "cs") -> str:
        return f"""\
---
id: "{unit_id}"
title: "Test Unit {unit_id}"
domain: "{domain}"
category: "concept"
difficulty: "junior"
---

# Test
"""

    def test_loads_valid_files(self):
        self._write("cs/unit1.md", self._make_unit_md("CS-CONCEPT-001"))
        self._write("cs/unit2.md", self._make_unit_md("CS-CONCEPT-002"))
        units = parse_directory(self.tmpdir)
        assert len(units) == 2

    def test_skips_readme(self):
        self._write("README.md", "# README")
        self._write("cs/unit1.md", self._make_unit_md("CS-CONCEPT-001"))
        units = parse_directory(self.tmpdir)
        assert len(units) == 1

    def test_skips_index(self):
        self._write("index.md", "# Index")
        self._write("cs/unit1.md", self._make_unit_md("CS-CONCEPT-001"))
        units = parse_directory(self.tmpdir)
        assert len(units) == 1

    def test_skips_errors_by_default(self):
        self._write("bad.md", "# No frontmatter")
        self._write("good.md", self._make_unit_md("CS-CONCEPT-001"))
        units = parse_directory(self.tmpdir, skip_errors=True)
        assert len(units) == 1

    def test_raises_on_error_when_skip_false(self):
        self._write("bad.md", "# No frontmatter")
        with pytest.raises(Exception):
            parse_directory(self.tmpdir, skip_errors=False)

    def test_not_a_directory(self):
        with pytest.raises(NotADirectoryError):
            parse_directory("/nonexistent/path")

    def test_returns_correct_domains(self):
        self._write("cs/unit.md",   self._make_unit_md("CS-CONCEPT-001", "cs"))
        self._write("arch/unit.md", self._make_unit_md("ARCH-COMP-001",  "arch"))
        units = parse_directory(self.tmpdir)
        domains = {u.domain for u in units}
        assert domains == {"cs", "arch"}


class TestSummary:

    def test_summary_runs_without_error(self, capsys):
        path = make_md(VALID_MD)
        units = [parse_file(path)]
        summary(units)
        captured = capsys.readouterr()
        assert "1" in captured.out
        os.unlink(path)

    def test_summary_empty(self, capsys):
        summary([])
        captured = capsys.readouterr()
        assert "не найдено" in captured.out
