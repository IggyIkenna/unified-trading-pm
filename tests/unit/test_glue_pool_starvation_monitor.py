"""Unit tests for the pure decision logic in scripts/cicd/glue_pool_starvation_monitor.py.

The monitor's whole reason to exist is the incident where a 16h total `glue`-pool collapse
surfaced NO alert at all (silent_failures_surfacing_as_generic_promotion_lag_2026_07_17.md). These
tests cover the "cheapest honest signal" contract from that issue doc.

Two detection modes tested:
  Mode 1 (STARVED): a `glue`-labelled job queued past threshold pages ONLY when the pool is
    genuinely idle (zero glue jobs in progress) — a busy-but-alive pool must never be misread.
  Mode 2 (STALLED): an `in_progress` workflow run has individual glue jobs still `queued` past
    the busy-queued threshold — pool oversubscribed, lone runner tied up. Root incident: 2026-08-03
    instruments-service run 30800087100 (1h45m stall, invisible to mode 1).
"""

from __future__ import annotations

import datetime as dt
import importlib.util
import types
from pathlib import Path


def _load_module() -> types.ModuleType:
    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "scripts" / "cicd" / "glue_pool_starvation_monitor.py"
    spec = importlib.util.spec_from_file_location("glue_pool_starvation_monitor", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


GPS = _load_module()

NOW = dt.datetime(2026, 7, 26, 12, 0, 0, tzinfo=dt.UTC)


def _run(run_id: int, created_at_iso: str, name: str = "some-workflow") -> dict[str, object]:
    return {
        "id": run_id,
        "name": name,
        "html_url": f"https://github.com/IggyIkenna/unified-trading-pm/actions/runs/{run_id}",
        "created_at": created_at_iso,
    }


def _job(name: str, status: str = "queued", labels: list[str] | None = None) -> dict[str, object]:
    return {"name": name, "status": status, "labels": labels if labels is not None else ["self-hosted", "glue"]}


# ── is_glue_job — exact-membership, "glue-writer" must never satisfy "glue" ─────────────────────


def test_is_glue_job_true_for_glue_label() -> None:
    assert GPS.is_glue_job(["self-hosted", "glue"]) is True


def test_is_glue_job_false_for_glue_writer_disjoint_pool() -> None:
    assert GPS.is_glue_job(["self-hosted", "glue-writer"]) is False


def test_is_glue_job_false_for_hosted_runner() -> None:
    assert GPS.is_glue_job(["ubuntu-latest"]) is False


def test_is_glue_job_false_for_non_list() -> None:
    assert GPS.is_glue_job(None) is False


# ── find_starved_glue_jobs — the synthetic starved case + the healthy-pool non-cases ────────────


def test_starved_case_fires_when_queued_past_threshold_and_pool_idle() -> None:
    """The synthetic case the issue doc's Done-when calls out: aged-out queued job, 0 in-progress."""
    queued_at = (NOW - dt.timedelta(minutes=45)).isoformat().replace("+00:00", "Z")
    run = _run(1, queued_at)
    glue_jobs = [_job("build")]
    starved = GPS.find_starved_glue_jobs([(run, glue_jobs)], in_progress_glue_count=0, threshold_min=20.0, now=NOW)
    assert len(starved) == 1
    assert starved[0]["run_id"] == 1
    assert starved[0]["age_min"] == 45.0


def test_healthy_pool_fires_nothing_when_glue_job_is_in_progress() -> None:
    """A busy-but-alive pool (something IS in progress) must never read as starved."""
    queued_at = (NOW - dt.timedelta(minutes=45)).isoformat().replace("+00:00", "Z")
    run = _run(1, queued_at)
    glue_jobs = [_job("build")]
    starved = GPS.find_starved_glue_jobs([(run, glue_jobs)], in_progress_glue_count=1, threshold_min=20.0, now=NOW)
    assert starved == []


def test_healthy_pool_fires_nothing_when_under_threshold() -> None:
    """Fresh backlog (under the age threshold) is normal, not starvation."""
    queued_at = (NOW - dt.timedelta(minutes=5)).isoformat().replace("+00:00", "Z")
    run = _run(1, queued_at)
    glue_jobs = [_job("build")]
    starved = GPS.find_starved_glue_jobs([(run, glue_jobs)], in_progress_glue_count=0, threshold_min=20.0, now=NOW)
    assert starved == []


def test_healthy_pool_fires_nothing_with_no_queued_runs() -> None:
    starved = GPS.find_starved_glue_jobs([], in_progress_glue_count=0, threshold_min=20.0, now=NOW)
    assert starved == []


def test_starved_ignores_jobs_no_longer_queued() -> None:
    """A job whose status moved on (e.g. cancelled) between the run-level and job-level fetch is
    not a starvation signal — only a still-`queued` job counts."""
    queued_at = (NOW - dt.timedelta(minutes=45)).isoformat().replace("+00:00", "Z")
    run = _run(1, queued_at)
    glue_jobs = [_job("build", status="cancelled")]
    starved = GPS.find_starved_glue_jobs([(run, glue_jobs)], in_progress_glue_count=0, threshold_min=20.0, now=NOW)
    assert starved == []


def test_starved_ignores_run_with_unparseable_created_at() -> None:
    run = {"id": 1, "name": "x", "html_url": "", "created_at": "not-a-timestamp"}
    glue_jobs = [_job("build")]
    starved = GPS.find_starved_glue_jobs([(run, glue_jobs)], in_progress_glue_count=0, threshold_min=20.0, now=NOW)
    assert starved == []


def test_multiple_starved_jobs_across_runs() -> None:
    queued_at = (NOW - dt.timedelta(minutes=30)).isoformat().replace("+00:00", "Z")
    run1 = _run(1, queued_at)
    run2 = _run(2, queued_at)
    starved = GPS.find_starved_glue_jobs(
        [(run1, [_job("build")]), (run2, [_job("test"), _job("lint")])],
        in_progress_glue_count=0,
        threshold_min=20.0,
        now=NOW,
    )
    assert len(starved) == 3


# ── find_stalled_glue_jobs — mode 2 (pool oversubscribed) ───────────────────────────────────────


def test_stalled_case_fires_when_in_progress_run_has_aged_queued_glue_job() -> None:
    """Mode 2 synthetic case from the Done-when: queued-behind-busy case fires exactly one alert."""
    created_at = (NOW - dt.timedelta(minutes=130)).isoformat().replace("+00:00", "Z")
    run = _run(42, created_at, "quality-gates-v2")
    queued_glue = [_job("QG slice (tests)", status="queued")]
    stalled = GPS.find_stalled_glue_jobs([(run, queued_glue)], busy_queued_min=120.0, now=NOW)
    assert len(stalled) == 1
    assert stalled[0]["run_id"] == 42
    assert stalled[0]["age_min"] == 130.0


def test_stalled_case_fires_nothing_when_under_busy_queued_threshold() -> None:
    """Normally-queued job (well under 120m) must not page — short delays are routine."""
    created_at = (NOW - dt.timedelta(minutes=10)).isoformat().replace("+00:00", "Z")
    run = _run(43, created_at, "quality-gates-v2")
    queued_glue = [_job("QG slice (tests)", status="queued")]
    stalled = GPS.find_stalled_glue_jobs([(run, queued_glue)], busy_queued_min=120.0, now=NOW)
    assert stalled == []


def test_stalled_case_fires_nothing_when_no_queued_glue_jobs() -> None:
    """An in_progress run with all glue jobs running should not fire mode 2."""
    created_at = (NOW - dt.timedelta(minutes=200)).isoformat().replace("+00:00", "Z")
    run = _run(44, created_at, "quality-gates-v2")
    in_progress_glue = [_job("QG slice (tests)", status="in_progress")]
    stalled = GPS.find_stalled_glue_jobs([(run, in_progress_glue)], busy_queued_min=120.0, now=NOW)
    assert stalled == []


def test_stalled_ignores_run_with_unparseable_created_at() -> None:
    run = {"id": 45, "name": "x", "html_url": "", "created_at": "bad-ts"}
    stalled = GPS.find_stalled_glue_jobs([(run, [_job("job")])], busy_queued_min=120.0, now=NOW)
    assert stalled == []


def test_stalled_fires_multiple_jobs_in_one_run() -> None:
    created_at = (NOW - dt.timedelta(minutes=150)).isoformat().replace("+00:00", "Z")
    run = _run(46, created_at)
    queued_glue = [_job("QG slice (tests)", status="queued"), _job("QG slice (checks)", status="queued")]
    stalled = GPS.find_stalled_glue_jobs([(run, queued_glue)], busy_queued_min=120.0, now=NOW)
    assert len(stalled) == 2


# ── build_report ──────────────────────────────────────────────────────────────────────────────


def test_build_report_healthy_names_no_alert() -> None:
    report = GPS.build_report([], [], threshold_min=20.0, busy_queued_min=120.0)
    assert "healthy" in report
    assert "starved" not in report.lower()
    assert "stalled" not in report.lower()


def test_build_report_starved_names_the_job_and_age() -> None:
    starved = [{"run_id": 1, "run_name": "x", "job_name": "build", "html_url": "https://x", "age_min": 45.0}]
    report = GPS.build_report(starved, [], threshold_min=20.0, busy_queued_min=120.0)
    assert "starved" in report.lower()
    assert "build" in report
    assert "45.0" in report


def test_build_report_stalled_names_the_job_and_age() -> None:
    stalled = [
        {"run_id": 2, "run_name": "qg", "job_name": "QG slice (tests)", "html_url": "https://y", "age_min": 130.0}
    ]
    report = GPS.build_report([], stalled, threshold_min=20.0, busy_queued_min=120.0)
    assert "stalled" in report.lower()
    assert "QG slice (tests)" in report
    assert "130.0" in report


def test_build_report_both_modes_present_when_both_fire() -> None:
    starved = [{"run_id": 1, "run_name": "x", "job_name": "build", "html_url": "", "age_min": 45.0}]
    stalled = [{"run_id": 2, "run_name": "qg", "job_name": "QG slice", "html_url": "", "age_min": 130.0}]
    report = GPS.build_report(starved, stalled, threshold_min=20.0, busy_queued_min=120.0)
    assert "starved" in report.lower()
    assert "stalled" in report.lower()


def test_build_report_truncates_at_ten_and_says_how_many_more() -> None:
    starved = [
        {"run_id": i, "run_name": "x", "job_name": f"job-{i}", "html_url": "", "age_min": 30.0} for i in range(13)
    ]
    report = GPS.build_report(starved, [], threshold_min=20.0, busy_queued_min=120.0)
    assert "3 more" in report


# ── parse_iso ─────────────────────────────────────────────────────────────────────────────────


def test_parse_iso_handles_z_suffix() -> None:
    parsed = GPS.parse_iso("2026-07-26T11:15:00Z")
    assert parsed is not None
    assert parsed.year == 2026 and parsed.hour == 11


def test_parse_iso_returns_none_for_garbage() -> None:
    assert GPS.parse_iso("not-a-date") is None
    assert GPS.parse_iso(None) is None
    assert GPS.parse_iso(123) is None
