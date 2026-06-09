"""Hermetic unit tests for ci_failure_watcher.auto_recover_stuck_prs (the "better fix").

``auto_recover_stuck_prs`` close+reopens the EXACT v2-never-reported deadlock signature
(BLOCKED + no failed check + v2 absent from the rollup) so it re-fires quality-gates-v2 with
no worker/orchestrator dependency. In ``dry_run`` it performs no ``gh`` calls and just returns
the selected set, so we test the gate directly (SSOT) — never touching a genuinely-failing PR
(v2 ran red → escalate instead), a v2-in-flight PR (no loop), or a non-promotion head.

Operator-requested 2026-06-09 ("is there not a better fix than escalating?").
"""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path


def _load_module() -> types.ModuleType:
    repo_root = Path(__file__).resolve().parents[2]
    watcher_path = repo_root / "scripts" / "repo-management" / "ci_failure_watcher.py"

    stub = types.ModuleType("pin_branch_protection_rulesets")
    stub.ORG = "IggyIkenna"  # type: ignore[attr-defined]
    stub.REPOS = []  # type: ignore[attr-defined]
    sys.modules.setdefault("pin_branch_protection_rulesets", stub)

    spec = importlib.util.spec_from_file_location("ci_failure_watcher", watcher_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


MOD = _load_module()
_recover = MOD.auto_recover_stuck_prs  # type: ignore[attr-defined]


def _pr(number: int, *, state: str, failed_check: bool, v2_present: bool, head: str = "live-defi-rollout") -> dict:
    return {
        "repo": "mtds",
        "number": number,
        "state": state,
        "failed_check": failed_check,
        "v2_present": v2_present,
        "head": head,
        "base": "staging",
        "age_min": 40,
    }


class TestAutoRecoverStuckPrs:
    def test_v2_never_reported_deadlock_qualifies(self) -> None:
        # BLOCKED because the required check is MISSING (not failed), v2 absent → close+reopen.
        out = _recover([_pr(1, state="BLOCKED", failed_check=False, v2_present=False)], dry_run=True)
        assert {s["number"] for s in out} == {1}

    def test_v2_present_is_left_alone(self) -> None:
        # v2 is in the rollup (in-flight) — recovering would loop; do nothing.
        out = _recover([_pr(2, state="BLOCKED", failed_check=False, v2_present=True)], dry_run=True)
        assert out == []

    def test_genuine_failure_is_left_for_escalate(self) -> None:
        # A check actually ran red — close+reopen wouldn't fix it; escalate path owns this.
        out = _recover([_pr(3, state="BLOCKED", failed_check=True, v2_present=False)], dry_run=True)
        assert out == []

    def test_non_blocked_state_is_left_alone(self) -> None:
        out = _recover([_pr(4, state="CONFLICTING", failed_check=False, v2_present=False)], dry_run=True)
        assert out == []

    def test_non_promotion_head_is_left_alone(self) -> None:
        out = _recover([_pr(5, state="BLOCKED", failed_check=False, v2_present=False, head="feat/x")], dry_run=True)
        assert out == []

    def test_empty_input_is_noop(self) -> None:
        assert _recover([], dry_run=True) == []
