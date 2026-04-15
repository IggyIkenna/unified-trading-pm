"""Unit tests for scripts/validators/validate_codex_refs.py."""

from __future__ import annotations

import importlib.util
import types
from pathlib import Path

import pytest


def _load_module() -> types.ModuleType:
    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "scripts" / "validators" / "validate_codex_refs.py"
    spec = importlib.util.spec_from_file_location("validate_codex_refs", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


MOD = _load_module()


# ── Tests: _jdict / _jlist / _jstr helpers ───────────────────────────────


class TestJsonHelpers:
    def test_jdict_with_dict(self) -> None:
        assert MOD._jdict({"key": "val"}) == {"key": "val"}

    def test_jdict_with_non_dict(self) -> None:
        assert MOD._jdict([1, 2]) is None
        assert MOD._jdict("str") is None
        assert MOD._jdict(None) is None

    def test_jlist_with_list(self) -> None:
        assert MOD._jlist([1, 2]) == [1, 2]

    def test_jlist_with_non_list(self) -> None:
        assert MOD._jlist({"a": 1}) is None
        assert MOD._jlist("str") is None

    def test_jstr_with_value(self) -> None:
        assert MOD._jstr("hello") == "hello"
        assert MOD._jstr(42) == "42"

    def test_jstr_with_none(self) -> None:
        assert MOD._jstr(None) == ""
        assert MOD._jstr(None, "default") == "default"


# ── Tests: _clean_path ──────────────────────────────────────────────────


class TestCleanPath:
    def test_strips_fragment(self) -> None:
        assert MOD._clean_path("path/to/file#section") == "path/to/file"

    def test_strips_backticks(self) -> None:
        assert MOD._clean_path("`path/to/file`") == "path/to/file"

    def test_strips_trailing_whitespace(self) -> None:
        assert MOD._clean_path("  path/to/file  ") == "path/to/file"

    def test_strips_ssot_suffix(self) -> None:
        assert MOD._clean_path("path/to/file (SSOT)") == "path/to/file"

    def test_strips_section_refs(self) -> None:
        result = MOD._clean_path("path/to/file (§ section)")
        assert result == "path/to/file"


# ── Tests: extract_codex_paths ────────────────────────────────────────────


class TestExtractCodexPaths:
    def test_extracts_codex_prefix(self) -> None:
        paths = MOD.extract_codex_paths("CODEX: 06-coding-standards/cli-convention.md")
        assert any("06-coding-standards/cli-convention.md" in p for p in paths)

    def test_extracts_see_codex_backtick(self) -> None:
        paths = MOD.extract_codex_paths("See codex: `06-coding-standards/cli-convention.md`")
        assert any("06-coding-standards/cli-convention.md" in p for p in paths)

    def test_skips_non_codex_prefixes(self) -> None:
        paths = MOD.extract_codex_paths("CODEX: unified-trading-pm/scripts/something.sh")
        assert paths == []

    def test_skips_cursor_paths(self) -> None:
        paths = MOD.extract_codex_paths("CODEX: .cursor/something.mdc")
        assert paths == []

    def test_strips_unified_trading_codex_prefix(self) -> None:
        paths = MOD.extract_codex_paths("CODEX: unified-trading-codex/06-coding-standards/cli-convention.md")
        assert any("06-coding-standards/cli-convention.md" in p for p in paths)

    def test_empty_line_returns_empty(self) -> None:
        paths = MOD.extract_codex_paths("")
        assert paths == []


# ── Tests: resolve_codex_path ─────────────────────────────────────────────


class TestResolveCodexPath:
    def test_direct_file(self, tmp_path: Path) -> None:
        codex_root = tmp_path / "codex"
        codex_root.mkdir()
        doc = codex_root / "06-coding-standards" / "cli-convention.md"
        doc.parent.mkdir(parents=True)
        doc.write_text("# CLI convention\n")
        result = MOD.resolve_codex_path("06-coding-standards/cli-convention.md", codex_root)
        assert result is not None

    def test_file_with_md_extension_added(self, tmp_path: Path) -> None:
        codex_root = tmp_path / "codex"
        codex_root.mkdir()
        doc = codex_root / "06-coding-standards" / "something.md"
        doc.parent.mkdir(parents=True)
        doc.write_text("# doc\n")
        result = MOD.resolve_codex_path("06-coding-standards/something", codex_root)
        assert result is not None

    def test_directory_reference(self, tmp_path: Path) -> None:
        codex_root = tmp_path / "codex"
        subdir = codex_root / "06-coding-standards"
        subdir.mkdir(parents=True)
        result = MOD.resolve_codex_path("06-coding-standards", codex_root)
        assert result is not None

    def test_fallback_basename_search(self, tmp_path: Path) -> None:
        codex_root = tmp_path / "codex"
        doc = codex_root / "06-coding-standards" / "my-doc"
        doc.mkdir(parents=True)
        result = MOD.resolve_codex_path("some/other/my-doc", codex_root)
        assert result is not None

    def test_returns_none_when_not_found(self, tmp_path: Path) -> None:
        codex_root = tmp_path / "codex"
        codex_root.mkdir()
        result = MOD.resolve_codex_path("nonexistent/path.md", codex_root)
        assert result is None


# ── Tests: main ──────────────────────────────────────────────────────────


class TestMain:
    def test_skips_when_codex_not_found(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            "sys.argv",
            ["validate_codex_refs.py", "--workspace-root", str(tmp_path)],
        )
        result = MOD.main()
        assert result == 0
