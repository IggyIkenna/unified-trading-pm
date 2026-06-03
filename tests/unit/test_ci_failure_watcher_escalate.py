"""Hermetic unit tests for ci_failure_watcher.conflict_prs_to_escalate (item C).

The selector is a PURE function over (stuck PR dicts, already-escalated set) — no
network / no ``gh`` — so it tests the close-the-loop routing rules directly (SSOT),
not a replica. Covers: only CONFLICTING/DIRTY qualify (BLOCKED does not), the
idempotency set suppresses re-dispatch, and an empty input is a no-op.

Operator-approved 2026-06-02 (cicd_contract_hardening_2026_06_01.md § C).
"""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path


def _load_module() -> types.ModuleType:
    """Load ci_failure_watcher with its sibling import stubbed (mirrors the classify test)."""
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
_select = MOD.conflict_prs_to_escalate  # type: ignore[attr-defined]


def _pr(repo: str, number: int, state: str) -> dict:
    return {
        "repo": repo,
        "number": number,
        "state": state,
        "head": "live-defi-rollout",
        "base": "staging",
        "age_min": 40,
    }


class TestConflictPrsToEscalate:
    def test_conflicting_and_dirty_qualify(self) -> None:
        stuck = [_pr("mtds", 1, "CONFLICTING"), _pr("deployment-service", 2, "DIRTY")]
        out = _select(stuck, already_escalated=set())
        assert {s["number"] for s in out} == {1, 2}

    def test_blocked_is_not_a_conflict(self) -> None:
        # BLOCKED is a gate/review wall, not a merge conflict — never auto-escalated.
        out = _select([_pr("mtds", 3, "BLOCKED")], already_escalated=set())
        assert out == []

    def test_already_escalated_is_suppressed(self) -> None:
        stuck = [_pr("mtds", 1, "CONFLICTING"), _pr("strategy-service", 4, "DIRTY")]
        out = _select(stuck, already_escalated={("mtds", 1)})
        assert {s["number"] for s in out} == {4}

    def test_empty_input_is_noop(self) -> None:
        assert _select([], already_escalated=set()) == []

    def test_mixed_states_only_conflicts(self) -> None:
        stuck = [
            _pr("a", 1, "CONFLICTING"),
            _pr("b", 2, "BLOCKED"),
            _pr("c", 3, "DIRTY"),
        ]
        out = _select(stuck, already_escalated=set())
        assert {s["number"] for s in out} == {1, 3}
