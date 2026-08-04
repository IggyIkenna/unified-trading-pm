"""Regression coverage for
plans/active/issues/fix_frontmatter_strips_required_author_field_from_issue_docs_2026_08_04.md:

`DEPRECATED_PLAN_FIELDS` includes `author` (a legitimate deprecated field for `doc_type: plan`
docs, whose canonical schema has no `author` field), but `remove_deprecated_fields()` was applied
unconditionally to every doc under `plans/active/` — including `plans/active/issues/*.md` — even
though `unified-trading-pm/agents/RULES.md` § 4.5 "Findings Closure" REQUIRES `author` on every
`doc_type: issue` doc. `fix_active_plan()` now gates the removal set on the doc's own `doc_type`.

Guards, most-important first:
  * An issue doc's `author:` field survives a `fix_active_plan()` pass.
  * Other genuinely-deprecated fields (e.g. `owner`) still get stripped from an issue doc — the
    gate is scoped to the collision set, not a blanket exemption.
  * A plan doc's `author:` field is still removed (no regression to the pre-existing behavior the
    deprecation was originally added for).
"""

from __future__ import annotations

import importlib.util
import types
from pathlib import Path


def _load_module() -> types.ModuleType:
    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "scripts" / "plan-hygiene" / "fix_frontmatter.py"
    spec = importlib.util.spec_from_file_location("fix_frontmatter", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


FF = _load_module()

_ISSUE_DOC = (
    "---\n"
    "doc_type: issue\n"
    "title: sample issue\n"
    "summary: sample\n"
    "status: open\n"
    "nature: issue\n"
    "asset_group: [meta]\n"
    "stage: [meta]\n"
    "repos: []\n"
    "scope: [engineer]\n"
    "tags: []\n"
    "related: []\n"
    "created: 2026-08-04\n"
    "author: slot-9\n"
    "owner: someone\n"
    "parent_epic: infrastructure_master\n"
    "assigned_vm: NA\n"
    "execution_scope: local-only\n"
    "priority: P2\n"
    "drift_direction: advance-code\n"
    "depends_on: []\n"
    "locked_by:\n"
    "locked_since:\n"
    "---\n"
    "\nbody\n"
)

_PLAN_DOC = _ISSUE_DOC.replace("doc_type: issue", "doc_type: plan").replace("title: sample issue", "title: sample plan")


def test_issue_doc_author_field_survives(tmp_path: Path) -> None:
    doc = tmp_path / "sample_issue_2026_08_04.md"
    doc.write_text(_ISSUE_DOC)
    FF.fix_active_plan(doc)
    after = doc.read_text()
    assert "author: slot-9\n" in after


def test_issue_doc_other_deprecated_fields_still_stripped(tmp_path: Path) -> None:
    doc = tmp_path / "sample_issue_2026_08_04.md"
    doc.write_text(_ISSUE_DOC)
    FF.fix_active_plan(doc)
    after = doc.read_text()
    assert "owner: someone\n" not in after


def test_plan_doc_author_field_still_removed(tmp_path: Path) -> None:
    doc = tmp_path / "sample_plan_2026_08_04.md"
    doc.write_text(_PLAN_DOC)
    FF.fix_active_plan(doc)
    after = doc.read_text()
    assert "author: slot-9\n" not in after


def test_deprecated_set_excludes_issue_required_fields() -> None:
    """Direct unit check on the computed set, independent of the end-to-end file I/O path."""
    effective = FF.DEPRECATED_PLAN_FIELDS - FF.ISSUE_REQUIRED_FIELDS
    assert "author" not in effective
    assert "owner" in effective  # not a required issue field — stays deprecated
