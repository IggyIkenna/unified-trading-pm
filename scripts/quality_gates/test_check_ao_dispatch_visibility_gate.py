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

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from check_ao_dispatch_visibility_gate import _summarize


def _report(
    disk_open: int,
    backlog_open: int,
    excluded: list[dict[str, object]],
    ineffective: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    """Mirrors one `DocReport` as `dispatch_visibility_report --json` emits it.

    `ineffective` is always present in the payload (the report dataclass has the field), so it is
    emitted here unconditionally — `_summarize` deliberately KeyErrors on a payload missing it
    rather than defaulting to zero. See `test_summarize_requires_the_ineffective_key`.
    """
    return {
        "plan_ref": "plans/active/x.md",
        "disk_open": disk_open,
        "backlog_open": backlog_open,
        "excluded": excluded,
        "ineffective": ineffective if ineffective is not None else [],
    }


def test_summarize_no_exclusions() -> None:
    summary = _summarize([_report(3, 3, [])])
    assert summary == {
        "docs": 1,
        "accidental_exclusions": 0,
        "declared_exclusions": 0,
        "zero_dispatchable_docs": 0,
        "ineffective_declarations": 0,
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
        "ineffective_declarations": 0,
    }


def test_summarize_counts_ineffective_declarations() -> None:
    """The third axis (added 2026-08-09): a todo that DISPATCHED while declaring a hold in a
    token the dispatcher does not know. It is not an exclusion at all, so it must be counted
    independently of accidental/declared — a check that only inspects excluded todos is
    structurally blind to it (blocked_prerequisites_marker_not_in_non_dispatchable_regex_2026_07_28.md)."""
    report = _report(
        2,
        2,
        [],
        ineffective=[
            {"description": "[REVIEW] P2. BLOCKED-PREREQUISITES — gate stamp", "token": "BLOCKED-PREREQUISITES"}
        ],
    )
    summary = _summarize([report])
    assert summary["ineffective_declarations"] == 1
    assert summary["accidental_exclusions"] == 0
    assert summary["declared_exclusions"] == 0


def test_summarize_requires_the_ineffective_key() -> None:
    """A report lacking `ineffective` is a STALE SIBLING, not a zero.

    Defaulting the count to 0 would report "no ineffective declarations" for a corpus that was
    never measured for them — the same silent-false-negative this gate exists to eliminate, and a
    banned empty-collection fallback besides. `_run_report` refuses such a payload loudly before
    `_summarize` ever sees it; this pins that `_summarize` itself does not paper over the gap.
    """
    with pytest.raises(KeyError):
        _summarize([{"plan_ref": "p.md", "disk_open": 1, "backlog_open": 1, "excluded": []}])
