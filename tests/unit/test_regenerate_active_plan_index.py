"""Unit tests for scripts/plans/regenerate_active_plan_index.py.

Covers the fix for plan_reconciler sports-tranche finding 1
(plans/active/issues/plan_reconciler_findings_sports_2026_08_10.md):
parse_frontmatter()'s block-scalar continuation-line consumption silently
appended a `# comment ...` line verbatim into the raw asset_group value,
and parse_asset_groups()'s naive `raw.strip("[]"); raw.split(",")` then
shattered the comment prose on its internal commas into garbage tokens.

These tests prove:
- a continuation line with a trailing `# comment` is stripped to just the
  bracket-list value before aggregation;
- the original (no-comment) multi-line case still works correctly;
- parse_asset_groups() receives clean, comma-separated group tokens even
  when the original doc had inline commentary on continuation lines.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "plans" / "regenerate_active_plan_index.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("regenerate_active_plan_index", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


# ---------------------------------------------------------------------------
# parse_frontmatter — commented continuation lines
# ---------------------------------------------------------------------------


class TestParseFrontmatterCommentedContinuation:
    """The exact bug: a multi-line asset_group: whose continuation line carries
    a trailing `# comment` with internal commas should parse to clean group
    tokens, not garbage."""

    def test_single_group_with_inline_comment(self) -> None:
        """`[sports] # corrected 2026-07-25 ... -- was [cross-cutting], a genuine mistag`."""
        mod = _load_module()
        text = """---
asset_group:
  [sports] # corrected 2026-07-25 (ag-closeout-audit orthogonality fix) -- was [cross-cutting], a genuine mistag:
  # 100% sports-specific (FixturesBrowser.tsx, fixtures_browser.py, sports fixture catalogue), no cross-AG mechanism
doc_type: plan
---
"""
        fm = mod.parse_frontmatter(text)
        assert "asset_group" in fm
        # The comment prose must be stripped — only the bracket-list tokens remain.
        groups = mod.parse_asset_groups(fm["asset_group"])
        assert groups == ["sports"]

    def test_multi_group_with_inline_comment(self) -> None:
        """`[sports, prediction, defi, meta] # prediction+defi added 2026-08-04 ...`."""
        mod = _load_module()
        text = """---
asset_group:
  [sports, prediction, defi, meta] # prediction+defi added 2026-08-04 by /ag-closeout-audit sports tranche: sports'
  # own remaining work is 100% closed (see Progress Log), but the doc's 2 genuinely-open residual checkboxes are
  # prediction- and defi-scoped
doc_type: plan
---
"""
        fm = mod.parse_frontmatter(text)
        groups = mod.parse_asset_groups(fm["asset_group"])
        assert sorted(groups) == sorted(["sports", "prediction", "defi", "meta"])

    def test_no_comment_multi_line_still_works(self) -> None:
        """Original (no-comment) multi-line case — single bracket list on one
        continuation line — is unaffected."""
        mod = _load_module()
        text = """---
asset_group:
  [sports, prediction]
doc_type: plan
---
"""
        fm = mod.parse_frontmatter(text)
        groups = mod.parse_asset_groups(fm["asset_group"])
        assert sorted(groups) == sorted(["sports", "prediction"])

    def test_comment_only_continuation_line_is_dropped(self) -> None:
        """A continuation line that is *only* a comment (e.g. `  # some note`)
        should be stripped to empty and not contribute a garbage token."""
        mod = _load_module()
        text = """---
asset_group:
  [sports]
  # this line is purely a comment — no bracket value on it
doc_type: plan
---
"""
        fm = mod.parse_frontmatter(text)
        groups = mod.parse_asset_groups(fm["asset_group"])
        assert groups == ["sports"]


# ---------------------------------------------------------------------------
# parse_frontmatter — other block-scalar shapes (regression)
# ---------------------------------------------------------------------------


class TestParseFrontmatterBlockScalarRegression:
    """Ensure the fix doesn't break existing block-scalar parsing."""

    def test_summary_folded_scalar(self) -> None:
        mod = _load_module()
        text = """---
summary: >-
  This is a long summary
  that spans multiple lines
doc_type: plan
---
"""
        fm = mod.parse_frontmatter(text)
        assert "summary" in fm
        assert "long summary" in fm["summary"]
        assert "multiple lines" in fm["summary"]

    def test_bare_empty_value_multi_line(self) -> None:
        mod = _load_module()
        text = """---
related:
  /plans/active/foo.md
  /plans/active/bar.md
doc_type: plan
---
"""
        fm = mod.parse_frontmatter(text)
        assert "related" in fm
        assert "foo.md" in fm["related"]
        assert "bar.md" in fm["related"]


# ---------------------------------------------------------------------------
# parse_asset_groups — edge cases
# ---------------------------------------------------------------------------


class TestParseAssetGroups:
    def test_empty(self) -> None:
        mod = _load_module()
        assert mod.parse_asset_groups("") == []

    def test_brackets_empty(self) -> None:
        mod = _load_module()
        assert mod.parse_asset_groups("[]") == []

    def test_single(self) -> None:
        mod = _load_module()
        assert mod.parse_asset_groups("[defi]") == ["defi"]

    def test_multi(self) -> None:
        mod = _load_module()
        assert mod.parse_asset_groups("[defi, cross-cutting]") == [
            "defi",
            "cross-cutting",
        ]

    def test_bare_no_brackets(self) -> None:
        mod = _load_module()
        assert mod.parse_asset_groups("sports") == ["sports"]

    def test_trailing_comment_already_stripped(self) -> None:
        """parse_asset_groups receives the already-stripped value from
        parse_frontmatter — this test just proves it handles clean input."""
        mod = _load_module()
        assert mod.parse_asset_groups("[sports, tradfi]") == ["sports", "tradfi"]
