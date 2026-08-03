"""Unit tests for the pure decision logic in
scripts/cicd/promote_fleet_startup_failure_monitor.py.

The monitor's whole reason to exist is the 2026-07-30 incident where both
`ldr-to-main-promote-fleet.yml` and `ldr-to-main-promote.yml` returned `startup_failure` on EVERY
tick for ~10h+ with nothing paging (see
plans/archive/issues/ldr_to_main_promote_workflows_sustained_startup_failure_2026_07_30.md,
resolved 2026-07-31). These tests cover the "N consecutive startup_failure runs" contract: a
single failure must never page, a streak that meets the threshold must, and a streak shorter than
the threshold (even if every run so far matches) must not.
"""

from __future__ import annotations

import importlib.util
import types
from pathlib import Path


def _load_module() -> types.ModuleType:
    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "scripts" / "cicd" / "promote_fleet_startup_failure_monitor.py"
    spec = importlib.util.spec_from_file_location("promote_fleet_startup_failure_monitor", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


PFM = _load_module()


def _run(run_id: int, conclusion: str | None, name: str = "wf") -> dict[str, object]:
    return {
        "id": run_id,
        "name": name,
        "conclusion": conclusion,
        "html_url": f"https://github.com/IggyIkenna/unified-trading-pm/actions/runs/{run_id}",
    }


# ── leading_run_of ────────────────────────────────────────────────────────────────────────────


def test_leading_run_of_returns_full_prefix_when_all_match() -> None:
    runs = [_run(3, "startup_failure"), _run(2, "startup_failure"), _run(1, "startup_failure")]
    out = PFM.leading_run_of(runs, "startup_failure")
    assert len(out) == 3


def test_leading_run_of_stops_at_first_mismatch() -> None:
    runs = [_run(4, "startup_failure"), _run(3, "startup_failure"), _run(2, "success"), _run(1, "startup_failure")]
    out = PFM.leading_run_of(runs, "startup_failure")
    assert [r["id"] for r in out] == [4, 3]


def test_leading_run_of_empty_when_newest_run_does_not_match() -> None:
    runs = [_run(2, "success"), _run(1, "startup_failure")]
    out = PFM.leading_run_of(runs, "startup_failure")
    assert out == []


def test_leading_run_of_empty_input() -> None:
    assert PFM.leading_run_of([], "startup_failure") == []


# ── is_stuck — the synthetic 3+-streak case + the non-cases ─────────────────────────────────────


def test_stuck_fires_on_exact_threshold_streak() -> None:
    runs = [_run(3, "startup_failure"), _run(2, "startup_failure"), _run(1, "startup_failure")]
    assert PFM.is_stuck(runs, threshold=3) is True


def test_stuck_fires_on_longer_than_threshold_streak() -> None:
    runs = [_run(i, "startup_failure") for i in range(5, 0, -1)]
    assert PFM.is_stuck(runs, threshold=3) is True


def test_not_stuck_when_streak_shorter_than_threshold() -> None:
    """Two consecutive failures with a real run history is noise, not a standing outage."""
    runs = [
        _run(4, "startup_failure"),
        _run(3, "startup_failure"),
        _run(2, "success"),
        _run(1, "startup_failure"),
    ]
    assert PFM.is_stuck(runs, threshold=3) is False


def test_not_stuck_when_fewer_runs_than_threshold_even_if_all_match() -> None:
    """Insufficient history must never be mistaken for a confirmed streak."""
    runs = [_run(2, "startup_failure"), _run(1, "startup_failure")]
    assert PFM.is_stuck(runs, threshold=3) is False


def test_not_stuck_on_healthy_fleet() -> None:
    runs = [_run(3, "success"), _run(2, "success"), _run(1, "success")]
    assert PFM.is_stuck(runs, threshold=3) is False


def test_not_stuck_on_empty_runs() -> None:
    assert PFM.is_stuck([], threshold=3) is False


def test_single_startup_failure_is_never_stuck() -> None:
    """A lone transient startup_failure (GitHub-side blip) must not page."""
    runs = [_run(3, "startup_failure"), _run(2, "success"), _run(1, "success")]
    assert PFM.is_stuck(runs, threshold=3) is False


# ── build_report ─────────────────────────────────────────────────────────────────────────────


def test_build_report_healthy_names_no_alert() -> None:
    report = PFM.build_report("IggyIkenna/unified-trading-pm", {}, threshold=3)
    assert "healthy" in report
    assert "STUCK" not in report


def test_build_report_names_the_stuck_workflow_and_streak_length() -> None:
    findings = {
        "ldr-to-main-promote-fleet.yml": [
            _run(3, "startup_failure"),
            _run(2, "startup_failure"),
            _run(1, "startup_failure"),
        ]
    }
    report = PFM.build_report("IggyIkenna/unified-trading-pm", findings, threshold=3)
    assert "STUCK" in report
    assert "ldr-to-main-promote-fleet.yml" in report
    assert "3 straight" in report


def test_build_report_names_both_workflows_when_both_stuck() -> None:
    findings = {
        "ldr-to-main-promote-fleet.yml": [_run(i, "startup_failure") for i in range(3, 0, -1)],
        "ldr-to-main-promote.yml": [_run(i, "startup_failure") for i in range(3, 0, -1)],
    }
    report = PFM.build_report("IggyIkenna/unified-trading-pm", findings, threshold=3)
    assert "ldr-to-main-promote-fleet.yml" in report
    assert "ldr-to-main-promote.yml" in report
