"""Hermetic unit tests for flow_health_reporter.compute_flow_health (plan § G).

Pure reducer over already-gathered per-repo dicts — no gh / no network. Covers:
the four offender triggers (FAILING, stale staging-lock, stuck-PR, main-behind-staging),
the all-clear case, and that normal LDR-ahead drift does NOT trip a false positive.
"""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path


def _load_module() -> types.ModuleType:
    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "scripts" / "repo-management" / "flow_health_reporter.py"
    stub = types.ModuleType("pin_branch_protection_rulesets")
    stub.ORG = "IggyIkenna"  # type: ignore[attr-defined]
    stub.REPOS = []  # type: ignore[attr-defined]
    sys.modules.setdefault("pin_branch_protection_rulesets", stub)
    spec = importlib.util.spec_from_file_location("flow_health_reporter", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


MOD = _load_module()
_compute = MOD.compute_flow_health  # type: ignore[attr-defined]

_THRESH = {"stuck_min": 60, "lock_stale_min": 25, "promote_stuck_behind": 40}


def _state(repo: str, **kw) -> dict:
    base = {
        "repo": repo,
        "ci_status": "MAIN_GREEN",
        "main_behind_staging": 0,
        "staging_behind_ldr": 0,
        "main_behind_ldr": 0,
        "oldest_stuck_min": -1,
        "staging_locked_min": -1,
    }
    base.update(kw)
    return base


class TestComputeFlowHealth:
    def test_all_clear(self) -> None:
        v = _compute([_state("a"), _state("b")], **_THRESH)
        assert v["blocked"] is False
        assert v["offenders"] == []

    def test_failing_ci_status_blocks(self) -> None:
        v = _compute([_state("a", ci_status="FAILING")], **_THRESH)
        assert v["blocked"] is True
        assert v["offenders"][0]["repo"] == "a"
        assert any("FAILING" in r for r in v["offenders"][0]["reasons"])

    def test_stale_staging_lock_blocks(self) -> None:
        v = _compute([_state("a", staging_locked_min=30)], **_THRESH)
        assert v["blocked"] is True
        assert any("locked" in r for r in v["offenders"][0]["reasons"])

    def test_fresh_staging_lock_is_ok(self) -> None:
        # locked but under threshold (a SIT run in progress) — not an offender.
        v = _compute([_state("a", staging_locked_min=10)], **_THRESH)
        assert v["blocked"] is False

    def test_stuck_pr_blocks(self) -> None:
        v = _compute([_state("a", oldest_stuck_min=90)], **_THRESH)
        assert v["blocked"] is True
        assert any("stuck PR" in r for r in v["offenders"][0]["reasons"])

    def test_main_behind_staging_blocks(self) -> None:
        v = _compute([_state("a", main_behind_staging=50)], **_THRESH)
        assert v["blocked"] is True
        assert any("behind staging" in r for r in v["offenders"][0]["reasons"])

    def test_normal_ldr_ahead_drift_is_not_a_false_positive(self) -> None:
        # LDR far ahead of staging/main is the NORMAL integration-axis state — must NOT trip.
        v = _compute([_state("a", staging_behind_ldr=300, main_behind_ldr=300)], **_THRESH)
        assert v["blocked"] is False

    def test_multiple_offenders_aggregate(self) -> None:
        v = _compute(
            [_state("a", ci_status="FAILING"), _state("b"), _state("c", oldest_stuck_min=120)],
            **_THRESH,
        )
        assert v["blocked"] is True
        assert {o["repo"] for o in v["offenders"]} == {"a", "c"}
