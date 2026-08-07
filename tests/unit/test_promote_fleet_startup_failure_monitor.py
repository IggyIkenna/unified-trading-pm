"""Unit tests for the pure decision logic in
scripts/cicd/promote_fleet_startup_failure_monitor.py.

The monitor's whole reason to exist is the 2026-07-30 incident where both
`ldr-to-main-promote-fleet.yml` and `ldr-to-main-promote.yml` returned `startup_failure` on EVERY
tick for ~10h+ with nothing paging (see
plans/archive/issues/ldr_to_main_promote_workflows_sustained_startup_failure_2026_07_30.md,
resolved 2026-07-31). These tests cover the "N consecutive startup_failure runs" contract: a
single failure must never page, a streak that meets the threshold must, and a streak shorter than
the threshold (even if every run so far matches) must not.

Also covers the 2026-08-07 hardening (root incident #2 —
plans/active/issues/ldr_to_main_promote_fleet_queued_run_cancelled_livelock_2026_08_07.md): a run
stuck in `status: queued` forever never reaches `completed`, so it is invisible to the streak
check above — `stuck_queued_runs` is the structurally separate "queued too long" signal that class
of livelock needed and had zero coverage for at the time.
"""

from __future__ import annotations

import datetime as dt
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


def _queued_run(run_id: int, created_at: str, event: str = "schedule", name: str = "wf") -> dict[str, object]:
    return {
        "id": run_id,
        "name": name,
        "status": "queued",
        "event": event,
        "created_at": created_at,
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


# ── parse_iso ─────────────────────────────────────────────────────────────────────────────────


def test_parse_iso_handles_z_suffix() -> None:
    parsed = PFM.parse_iso("2026-08-07T11:56:22Z")
    assert parsed == dt.datetime(2026, 8, 7, 11, 56, 22, tzinfo=dt.UTC)


def test_parse_iso_none_on_missing_or_malformed() -> None:
    assert PFM.parse_iso(None) is None
    assert PFM.parse_iso("") is None
    assert PFM.parse_iso("not-a-timestamp") is None
    assert PFM.parse_iso(12345) is None


# ── stuck_queued_runs — the 2026-08-07 zombie-queued hardening ──────────────────────────────────


def test_stuck_queued_runs_flags_run_older_than_threshold() -> None:
    """The actual incident shape: created_at 11:56:22Z, still queued hours later."""
    now = dt.datetime(2026, 8, 7, 17, 42, 0, tzinfo=dt.UTC)
    runs = [_queued_run(31176101874, "2026-08-07T11:56:22Z")]
    out = PFM.stuck_queued_runs(runs, threshold_min=30.0, now=now)
    assert len(out) == 1
    assert out[0]["id"] == 31176101874
    assert out[0]["_age_min"] > 340  # ~346 min


def test_stuck_queued_runs_does_not_flag_recent_queue() -> None:
    """A run queued 5 minutes ago is normal cold-start/busy-period behavior, not a livelock."""
    now = dt.datetime(2026, 8, 7, 12, 5, 0, tzinfo=dt.UTC)
    runs = [_queued_run(1, "2026-08-07T12:00:00Z")]
    assert PFM.stuck_queued_runs(runs, threshold_min=30.0, now=now) == []


def test_stuck_queued_runs_boundary_is_exclusive() -> None:
    """Exactly at the threshold must not page — only strictly older."""
    now = dt.datetime(2026, 8, 7, 12, 30, 0, tzinfo=dt.UTC)
    runs = [_queued_run(1, "2026-08-07T12:00:00Z")]
    assert PFM.stuck_queued_runs(runs, threshold_min=30.0, now=now) == []


def test_stuck_queued_runs_empty_input() -> None:
    assert PFM.stuck_queued_runs([], threshold_min=30.0, now=dt.datetime.now(dt.UTC)) == []


def test_stuck_queued_runs_skips_unparseable_created_at() -> None:
    """Fail-safe: never page on a malformed/missing timestamp."""
    now = dt.datetime(2026, 8, 7, 17, 42, 0, tzinfo=dt.UTC)
    runs = [{"id": 1, "created_at": None}, {"id": 2, "created_at": "garbage"}]
    assert PFM.stuck_queued_runs(runs, threshold_min=30.0, now=now) == []


def test_stuck_queued_runs_only_flags_the_stale_one() -> None:
    now = dt.datetime(2026, 8, 7, 12, 45, 0, tzinfo=dt.UTC)
    runs = [
        _queued_run(1, "2026-08-07T12:40:00Z"),  # 5 min old — fine
        _queued_run(2, "2026-08-07T11:00:00Z"),  # 105 min old — stuck
    ]
    out = PFM.stuck_queued_runs(runs, threshold_min=30.0, now=now)
    assert [r["id"] for r in out] == [2]


# ── build_report — queued_stuck section, additive to the existing streak report ─────────────────


def test_build_report_healthy_mentions_queued_threshold_and_no_stuck() -> None:
    report = PFM.build_report("IggyIkenna/unified-trading-pm", {}, threshold=3)
    assert "healthy" in report
    assert "STUCK" not in report
    assert "ZOMBIE-QUEUED" not in report


def test_build_report_names_zombie_queued_run_and_age() -> None:
    now = dt.datetime(2026, 8, 7, 17, 42, 0, tzinfo=dt.UTC)
    queued_runs = [_queued_run(31176101874, "2026-08-07T11:56:22Z")]
    stuck = PFM.stuck_queued_runs(queued_runs, threshold_min=30.0, now=now)
    queued_stuck = {"ldr-to-main-promote-fleet.yml": stuck}
    report = PFM.build_report(
        "IggyIkenna/unified-trading-pm", {}, threshold=3, queued_stuck=queued_stuck, queued_threshold_min=30.0
    )
    assert "ZOMBIE-QUEUED" in report
    assert "ldr-to-main-promote-fleet.yml" in report
    assert "31176101874" in report
    assert "STUCK" not in report  # the startup_failure-streak section must not also fire


def test_build_report_can_show_both_conditions_independently() -> None:
    findings = {"ldr-to-main-promote.yml": [_run(i, "startup_failure") for i in range(3, 0, -1)]}
    now = dt.datetime(2026, 8, 7, 17, 42, 0, tzinfo=dt.UTC)
    queued_runs = [_queued_run(99, "2026-08-07T11:00:00Z")]
    queued_stuck = {"ldr-to-main-promote-fleet.yml": PFM.stuck_queued_runs(queued_runs, 30.0, now)}
    report = PFM.build_report("IggyIkenna/unified-trading-pm", findings, threshold=3, queued_stuck=queued_stuck)
    assert "STUCK" in report
    assert "ZOMBIE-QUEUED" in report
    assert "ldr-to-main-promote.yml" in report
    assert "ldr-to-main-promote-fleet.yml" in report


def test_build_report_no_queued_stuck_arg_behaves_like_before() -> None:
    """Backward-compat: callers that never pass queued_stuck (old call shape) still work."""
    findings = {
        "ldr-to-main-promote-fleet.yml": [
            _run(3, "startup_failure"),
            _run(2, "startup_failure"),
            _run(1, "startup_failure"),
        ]
    }
    report = PFM.build_report("IggyIkenna/unified-trading-pm", findings, threshold=3)
    assert "STUCK" in report
    assert "3 straight" in report
    assert "ZOMBIE-QUEUED" not in report
