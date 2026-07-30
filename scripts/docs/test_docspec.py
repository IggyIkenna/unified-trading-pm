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
    roles=frozenset({"data_engineering", "infra", "backend-engineer", "ui-developer", "review"}),
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


def test_blank_assigned_vm_is_a_hard_violation_on_an_issue():
    # blank_assigned_vm_dispatch_classification_gap_2026_07_26.md: assigned_vm on an issue is now
    # REQUIRED (was OPTIONAL, which let 58 active docs sit genuinely unclassified LOCAL-vs-AO-
    # dispatchable and invisible to this gate). NA and a real vm-id are both valid; blank is not.
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
    assert "assigned_vm" in _fields(vs, Sev.HARD)


def test_na_assigned_vm_is_ok_on_an_issue():
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
        "assigned_vm": "NA",
    }
    vs = validate_frontmatter("issue", issue, REG)
    assert "assigned_vm" not in _fields(vs, Sev.HARD)
    assert "assigned_vm" not in _fields(vs, Sev.SOFT)


def test_assigned_vm_key_absent_entirely_is_a_hard_violation_on_an_issue():
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
    }
    vs = validate_frontmatter("issue", issue, REG)
    assert "assigned_vm" in _fields(vs, Sev.HARD)


def test_assigned_role_absent_is_ok():
    # elective: absent is fine (plan predates the field / never got one) — not HARD, not SOFT
    vs = validate_frontmatter("plan", _valid_plan(), REG)
    assert "assigned_role" not in _fields(vs, Sev.HARD)
    assert "assigned_role" not in _fields(vs, Sev.SOFT)


def test_assigned_role_known_role_is_ok():
    fm = _valid_plan()
    fm["assigned_role"] = "data_engineering"
    assert "assigned_role" not in _fields(validate_frontmatter("plan", fm, REG), Sev.HARD)


def test_assigned_role_unknown_role_is_hard():
    fm = _valid_plan()
    fm["assigned_role"] = "data-pipeline-engineer"  # not a role: value under agents/*.md
    assert "assigned_role" in _fields(validate_frontmatter("plan", fm, REG), Sev.HARD)


def test_unknown_doc_type_is_hard():
    assert _fields(validate_frontmatter(None, {}, REG), Sev.HARD) == {"doc_type"}


def _valid_codex_ssot() -> dict:
    return {
        "doc_type": "codex-ssot",
        "title": "x",
        "summary": "does x",
        "status": "current",
        "nature": "ssot",
        "asset_group": ["defi"],
        "stage": ["meta"],
        "repos": [],
        "scope": ["engineer"],
        "tags": ["a"],
        "related": [],
        "created": "2026-06-24",
        "authoritative_for": ["x topic"],
        "referenced_by": [],
        "owner": None,
        "last_reviewed": None,
        "code_refs": [],
    }


def test_elective_absent_is_ok():
    vs = validate_frontmatter("codex-ssot", _valid_codex_ssot(), REG)
    assert "implementation_status" not in _fields(vs, Sev.HARD)
    assert "implementation_status" not in _fields(vs, Sev.SOFT)


def test_elective_valid_value_is_ok():
    fm = _valid_codex_ssot()
    fm["implementation_status"] = "code-shipped"
    vs = validate_frontmatter("codex-ssot", fm, REG)
    assert "implementation_status" not in _fields(vs, Sev.HARD)
    assert "implementation_status" not in _fields(vs, Sev.SOFT)


def test_elective_bad_enum_is_hard():
    fm = _valid_codex_ssot()
    fm["implementation_status"] = "half-baked"
    assert "implementation_status" in _fields(validate_frontmatter("codex-ssot", fm, REG), Sev.HARD)


def test_nature_issue_is_valid():
    fm = _valid_plan()
    fm["doc_type"] = "issue"
    fm["nature"] = "issue"
    fm["source"] = ["x"]
    assert "nature" not in _fields(validate_frontmatter("issue", fm, REG), Sev.HARD)


def test_declared_doc_type_contradicting_path_is_hard():
    fm = _valid_plan()  # declares doc_type: plan
    vs = validate_frontmatter("issue", fm, REG)  # path says issue
    assert any(v.field == "doc_type" and v.severity == Sev.HARD and "contradicts" in v.message for v in vs)


def test_declared_doc_type_matching_path_is_ok():
    fm = _valid_plan()
    vs = validate_frontmatter("plan", fm, REG)
    assert "doc_type" not in _fields(vs, Sev.HARD)


def test_detect_folded_date_fields_catches_the_actual_corruption_signature():
    # The exact reproduced signature from
    # prek_patch_cache_replays_stale_diff_onto_unrelated_files_2026_07_29.md: an unquoted bare
    # continuation directly under `last_updated:` on an ISSUE doc — a doc_type where `last_updated`
    # isn't even schema-modeled, so validate_frontmatter() alone never looks at it.
    raw = (
        "\nlast_updated:\n"
        '  2026-06-27 "2026-07-30" # cleaned up a merge-conflict-corrupted multi-date runaway scalar\n'
        "  # some trailing comment continuation line\n"
        "parent_epic: defi_master\n"
    )
    vs = docspec.detect_folded_date_fields(raw)
    assert "last_updated" in _fields(vs, Sev.HARD)


def test_detect_folded_date_fields_does_not_flag_deliberate_quoted_annotation():
    # The established, legitimate corpus convention (defi_code_codex_drift_2026_05_27.md,
    # uac_data_type_validity_combinator_fragmentation_2026_07_07.md) — first continuation line
    # opens with a quote, so it is NOT this bug's shape and must not be flagged.
    raw = "\nlast_updated:\n  '2026-07-10 (was: 2026-06-27 -- verify-rerun-2 finding 50)'\nparent_epic: defi_master\n"
    assert docspec.detect_folded_date_fields(raw) == []


def test_detect_folded_date_fields_ignores_clean_single_line_value():
    raw = "\nlast_updated: 2026-06-27\nparent_epic: defi_master\n"
    assert docspec.detect_folded_date_fields(raw) == []


def test_detect_folded_date_fields_ignores_block_list_continuation():
    # A continuation that opens with `-` is a YAML block-sequence item, not a folded scalar — must
    # not be misclassified even directly under a date-kind field name (contrived shape, but proves
    # the `-`/`[`/`{` skip-list actually gates on the continuation line, not just the field name).
    raw = "\nlast_updated:\n  - 2026-06-27\nparent_epic: defi_master\n"
    assert docspec.detect_folded_date_fields(raw) == []
