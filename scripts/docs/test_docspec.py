#!/usr/bin/env python3
"""Unit tests for docspec — the frontmatter validator (3-state logic + enums + precedence).

Run: .venv/bin/python -m pytest scripts/docs/test_docspec.py -q

# Epic: agent_operating_framework_master
# Lifecycle: permanent
"""

from __future__ import annotations

import docspec
from docspec import Sev, Violation, validate_frontmatter

REG = docspec.Registries(
    vms=frozenset({"harsh_pc", "vm-defi", "NA"}),
    epics=frozenset({"agent_operating_framework_master", "defi_master"}),
    repos=frozenset({"mtds", "instruments-service"}),
)


def _fields(vs: list[Violation], sev: Sev) -> set[str]:
    return {v.field for v in vs if v.severity == sev}


def _valid_plan() -> dict:
    return {
        "doc_type": "plan",
        "title": "x",
        "summary": "does x",
        "status": "active",
        "nature": "process",
        "asset_group": ["defi"],
        "stage": ["meta"],
        "repos": ["mtds"],
        "scope": ["engineer", "admin"],
        "tags": ["a"],
        "related": [],
        "created": "2026-06-24",
        "parent_epic": "defi_master",
        "assigned_vm": "vm-defi",
        "execution_scope": "orchestrator-agent",
        "priority": "P1",
        "estimate_class": "infra",
        "estimate_baseline_ai_days": 2,
        "estimate_calibrated_ai_days": 1,
    }


def test_valid_plan_no_hard():
    assert _fields(validate_frontmatter("plan", _valid_plan(), REG), Sev.HARD) == set()


def test_missing_required_is_hard():
    fm = _valid_plan()
    del fm["summary"]
    assert "summary" in _fields(validate_frontmatter("plan", fm, REG), Sev.HARD)


def test_present_but_empty_required_is_soft():
    fm = _valid_plan()
    fm["summary"] = None  # present, empty
    vs = validate_frontmatter("plan", fm, REG)
    assert "summary" not in _fields(vs, Sev.HARD)
    assert "summary" in _fields(vs, Sev.SOFT)


def test_empty_optional_is_ok():
    fm = _valid_plan()
    fm["source"] = None  # optional, empty -> fine
    vs = validate_frontmatter("plan", fm, REG)
    assert "source" not in _fields(vs, Sev.HARD)
    assert "source" not in _fields(vs, Sev.SOFT)


def test_bad_enum_is_hard():
    fm = _valid_plan()
    fm["asset_group"] = ["defi", "bogus"]
    assert "asset_group" in _fields(validate_frontmatter("plan", fm, REG), Sev.HARD)


def test_assigned_vm_na_is_valid():
    fm = _valid_plan()
    fm["assigned_vm"] = "NA"
    assert "assigned_vm" not in _fields(validate_frontmatter("plan", fm, REG), Sev.HARD)


def test_assigned_vm_unknown_is_hard():
    fm = _valid_plan()
    fm["assigned_vm"] = "vm-nope"
    assert "assigned_vm" in _fields(validate_frontmatter("plan", fm, REG), Sev.HARD)


def test_assigned_vm_empty_is_hard():
    fm = _valid_plan()
    fm["assigned_vm"] = None
    assert "assigned_vm" in _fields(validate_frontmatter("plan", fm, REG), Sev.HARD)


def test_plan_assigned_vm_not_cross_checked_against_epic():
    # plan supersedes epic: a plan's assigned_vm is validated only against the registry,
    # never against its parent_epic's vm -> no mismatch violation exists.
    fm = _valid_plan()
    fm["assigned_vm"] = "harsh_pc"  # differs from defi_master's vm-defi; must be fine
    assert "assigned_vm" not in _fields(validate_frontmatter("plan", fm, REG), Sev.HARD)


def test_na_literal_on_non_assigned_vm_is_soft():
    fm = _valid_plan()
    fm["locked_by"] = "NA"
    assert "locked_by" in _fields(validate_frontmatter("plan", fm, REG), Sev.SOFT)


def test_issue_resolved_by_conditional():
    base = {
        "doc_type": "issue",
        "title": "x",
        "summary": "s",
        "status": "open",
        "nature": "notes",
        "asset_group": ["meta"],
        "stage": ["meta"],
        "repos": [],
        "scope": ["engineer", "admin"],
        "tags": [],
        "related": [],
        "created": "2026-06-24",
        "parent_epic": "defi_master",
        "priority": "P2",
        "source": ["audit"],
    }
    # open -> resolved_by not required
    assert "resolved_by" not in _fields(validate_frontmatter("issue", base, REG), Sev.HARD)
    # resolved -> resolved_by becomes required
    resolved = {**base, "status": "resolved"}
    assert "resolved_by" in _fields(validate_frontmatter("issue", resolved, REG), Sev.HARD)


def test_cursor_rule_only_needs_doc_type():
    assert validate_frontmatter("cursor-rule", {"doc_type": "cursor-rule"}, REG) == []
    assert _fields(validate_frontmatter("cursor-rule", {}, REG), Sev.HARD) == {"doc_type"}


def test_status_enum_is_per_type_soft():
    # 'active' is valid for a plan; for an issue it's a SOFT "normalize" warning (deferred content), not HARD
    plan = _valid_plan()
    assert "status" not in _fields(validate_frontmatter("plan", plan, REG), Sev.HARD)
    issue = {**_valid_plan(), "doc_type": "issue", "status": "active"}
    vs = validate_frontmatter("issue", issue, REG)
    assert "status" not in _fields(vs, Sev.HARD)
    assert "status" in _fields(vs, Sev.SOFT)


def test_optional_assigned_vm_empty_is_ok():
    # issue assigned_vm is OPTIONAL -> empty is fine (neither HARD nor SOFT)
    issue = {
        "doc_type": "issue",
        "title": "x",
        "summary": "s",
        "status": "open",
        "nature": "notes",
        "asset_group": ["meta"],
        "stage": ["meta"],
        "repos": [],
        "scope": ["engineer"],
        "tags": [],
        "related": [],
        "created": "2026-06-24",
        "parent_epic": "defi_master",
        "priority": "P2",
        "source": ["audit"],
        "assigned_vm": None,
    }
    vs = validate_frontmatter("issue", issue, REG)
    assert "assigned_vm" not in _fields(vs, Sev.HARD)
    assert "assigned_vm" not in _fields(vs, Sev.SOFT)


def test_unknown_doc_type_is_hard():
    assert _fields(validate_frontmatter(None, {}, REG), Sev.HARD) == {"doc_type"}
