"""Unit tests for scripts/validation/check-cursor-plan-format.py."""

from __future__ import annotations

import importlib.util
import types
from pathlib import Path


def _load_module() -> types.ModuleType:
    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "scripts" / "validation" / "check-cursor-plan-format.py"
    spec = importlib.util.spec_from_file_location("check_cursor_plan_format", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


MOD = _load_module()


# ── Tests: _find_plans_dir ─────────────────────────────────────────────────


class TestFindPlansDir:
    def test_returns_first_existing_candidate(self, tmp_path: Path) -> None:
        plans_dir = tmp_path / "plans" / "cursor-plans"
        plans_dir.mkdir(parents=True)
        result = MOD._find_plans_dir(tmp_path)
        assert result == plans_dir

    def test_returns_pm_subdirectory_candidate(self, tmp_path: Path) -> None:
        plans_dir = tmp_path / "unified-trading-pm" / "plans" / "cursor-plans"
        plans_dir.mkdir(parents=True)
        result = MOD._find_plans_dir(tmp_path)
        assert result == plans_dir

    def test_returns_default_when_none_exist(self, tmp_path: Path) -> None:
        result = MOD._find_plans_dir(tmp_path)
        # Should return the first candidate even if it doesn't exist
        assert "cursor-plans" in str(result)


# ── Tests: _parse_frontmatter ──────────────────────────────────────────────


class TestParseFrontmatter:
    def test_valid_frontmatter(self) -> None:
        content = """---
name: My Plan
overview: This is a plan
isProject: true
todos:
  - id: 1
    content: Do something
    status: pending
---
# Plan body
"""
        data, rest = MOD._parse_frontmatter(content)
        assert data is not None
        assert data["name"] == "My Plan"
        assert data["overview"] == "This is a plan"
        assert data["isProject"] == "true"
        assert "# Plan body" in rest

    def test_no_frontmatter(self) -> None:
        content = "# Just a markdown file\nSome content"
        data, rest = MOD._parse_frontmatter(content)
        assert data is None
        assert rest == content

    def test_incomplete_frontmatter(self) -> None:
        content = "---\nname: test\n# no closing ---\nsome content"
        data, rest = MOD._parse_frontmatter(content)
        assert data is None

    def test_empty_frontmatter_returns_none(self) -> None:
        # The regex requires at least one line between --- markers
        content = "---\n---\nBody"
        data, rest = MOD._parse_frontmatter(content)
        # An empty frontmatter block has no lines between ---, which the regex cannot match
        assert data is None

    def test_minimal_frontmatter(self) -> None:
        content = "---\nname: x\n---\nBody"
        data, rest = MOD._parse_frontmatter(content)
        assert data is not None
        assert data["name"] == "x"

    def test_comments_in_frontmatter(self) -> None:
        content = "---\n# This is a comment\nname: test\n---\nBody"
        data, rest = MOD._parse_frontmatter(content)
        assert data is not None
        assert data["name"] == "test"

    def test_quoted_values_stripped(self) -> None:
        content = "---\nname: \"My Plan\"\noverview: 'An overview'\n---\nBody"
        data, _ = MOD._parse_frontmatter(content)
        assert data is not None
        assert data["name"] == "My Plan"
        assert data["overview"] == "An overview"

    def test_todos_detection(self) -> None:
        content = "---\ntodos:\n  - id: 1\n    content: foo\n---\nBody"
        data, _ = MOD._parse_frontmatter(content)
        assert data is not None
        assert data["todos"] == "present"

    def test_todos_without_id_content(self) -> None:
        content = "---\ntodos:\n  - something\n---\nBody"
        data, _ = MOD._parse_frontmatter(content)
        assert data is not None
        assert data["todos"] is None


# ── Tests: validate_plan ───────────────────────────────────────────────────


class TestValidatePlan:
    def test_valid_plan(self, tmp_path: Path) -> None:
        plan = tmp_path / "test.md.md"
        plan.write_text(
            "---\n"
            "name: Test Plan\n"
            "overview: A test plan\n"
            "isProject: true\n"
            "todos:\n"
            "  - id: 1\n"
            "    content: Do something\n"
            "    status: pending\n"
            "---\n"
            "# Body\n"
        )
        errors = MOD.validate_plan(plan)
        assert not errors

    def test_missing_frontmatter(self, tmp_path: Path) -> None:
        plan = tmp_path / "no-fm.md.md"
        plan.write_text("# No frontmatter\nJust a plan.")
        errors = MOD.validate_plan(plan)
        assert len(errors) >= 1
        assert any("frontmatter" in e for e in errors)

    def test_missing_name(self, tmp_path: Path) -> None:
        plan = tmp_path / "no-name.md.md"
        plan.write_text(
            "---\noverview: A plan\nisProject: true\ntodos:\n  - id: 1\n    content: foo\n    status: done\n---\nBody\n"
        )
        errors = MOD.validate_plan(plan)
        assert any("name" in e for e in errors)

    def test_missing_overview(self, tmp_path: Path) -> None:
        plan = tmp_path / "no-overview.md.md"
        plan.write_text(
            "---\nname: Plan\nisProject: true\ntodos:\n  - id: 1\n    content: foo\n    status: done\n---\nBody\n"
        )
        errors = MOD.validate_plan(plan)
        assert any("overview" in e for e in errors)

    def test_missing_isProject(self, tmp_path: Path) -> None:
        plan = tmp_path / "no-isproject.md.md"
        plan.write_text(
            "---\nname: Plan\noverview: An overview\ntodos:\n  - id: 1\n    content: foo\n    status: done\n---\nBody\n"
        )
        errors = MOD.validate_plan(plan)
        assert any("isProject" in e for e in errors)

    def test_missing_todos(self, tmp_path: Path) -> None:
        plan = tmp_path / "no-todos.md.md"
        plan.write_text("---\nname: Plan\noverview: An overview\nisProject: true\n---\nBody without todos list\n")
        errors = MOD.validate_plan(plan)
        assert any("todos" in e.lower() for e in errors)

    def test_unreadable_file(self, tmp_path: Path) -> None:
        plan = tmp_path / "unreadable.md.md"
        # File doesn't exist
        errors = MOD.validate_plan(plan)
        assert len(errors) == 1
        assert "cannot read" in errors[0]
