# Epic: agent_operating_framework_master
# Lifecycle: permanent
# Delete-when: NA
"""Unit tests for check_ao_dispatch_visibility_gate.py.

Only exercises the ratchet/summary arithmetic (`_summarize`, baseline load/compare) on
canned report JSON — the actual parsing/declared-classification logic lives in
agent-orchestrator's `server.dispatch_visibility_report` (agent-orchestrator's own
dependencies, e.g. pydantic, are not available in this repo's environment) and is
covered by agent-orchestrator/tests/test_dispatch_visibility_report.py, including the
four known trigger shapes. This file covers the half of the gate that lives here: no
sibling-repo access, so it runs in every environment including bare CI.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from check_ao_dispatch_visibility_gate import _summarize


def _report(disk_open: int, backlog_open: int, excluded: list[dict[str, object]]) -> dict[str, object]:
    return {"plan_ref": "plans/active/x.md", "disk_open": disk_open, "backlog_open": backlog_open, "excluded": excluded}


def test_summarize_no_exclusions() -> None:
    summary = _summarize([_report(3, 3, [])])
    assert summary == {
        "docs": 1,
        "accidental_exclusions": 0,
        "declared_exclusions": 0,
        "zero_dispatchable_docs": 0,
    }


def test_summarize_splits_declared_vs_accidental() -> None:
    reports = [
        _report(
            3,
            1,
            [
                {"description": "a", "declared": True},
                {"description": "b", "declared": False},
            ],
        )
    ]
    summary = _summarize(reports)
    assert summary["accidental_exclusions"] == 1
    assert summary["declared_exclusions"] == 1
    assert summary["zero_dispatchable_docs"] == 0


def test_summarize_counts_zero_dispatchable_docs() -> None:
    reports = [
        _report(2, 0, [{"description": "a", "declared": True}, {"description": "b", "declared": False}]),
        _report(2, 2, []),
    ]
    summary = _summarize(reports)
    assert summary["docs"] == 2
    assert summary["zero_dispatchable_docs"] == 1


def test_summarize_empty_report_list() -> None:
    summary = _summarize([])
    assert summary == {
        "docs": 0,
        "accidental_exclusions": 0,
        "declared_exclusions": 0,
        "zero_dispatchable_docs": 0,
    }
