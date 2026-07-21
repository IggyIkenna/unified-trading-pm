"""Unit tests for the self-hosted glue-runner starvation detector in ci_failure_watcher.

Covers detect_glue_starvation (the IO detector), _glue_runner_counts (label-shape parsing) and the
glue branch of build_alert_items (the pure per-condition mapper feeding the matrix notify). All
gh/network calls are mocked.

WHY THIS EXISTS: once PM's glue workflows run on the self-hosted pools, a dead VM is SILENT —
GitHub keeps accepting dispatches, the jobs sit `queued`, and every other detector here watches for
FAILURES. A queued job is not a failure until GitHub kills it at 24h, by which point the ci_status
transitions are lost. SSOT: plans/active/github_actions_ci_cost_reduction_2026_07_15.md.
"""

from __future__ import annotations

import datetime as _dt
import importlib.util
import sys
import types
from pathlib import Path
from unittest.mock import patch


def _load_module() -> types.ModuleType:
    repo_root = Path(__file__).resolve().parents[2]
    watcher_path = repo_root / "scripts" / "repo-management" / "ci_failure_watcher.py"
    stub = types.ModuleType("pin_branch_protection_rulesets")
    stub.ORG = "IggyIkenna"  # type: ignore[attr-defined]
    stub.REPOS = []  # type: ignore[attr-defined]
    sys.modules.setdefault("pin_branch_protection_rulesets", stub)
    spec = importlib.util.spec_from_file_location("ci_failure_watcher_glue", watcher_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


MOD = _load_module()
NOW = _dt.datetime(2026, 7, 16, 12, 0, 0, tzinfo=_dt.UTC)

STALE_TS = "2026-07-16T11:40:00Z"  # 20 min before NOW -> past the 10-min threshold
FRESH_TS = "2026-07-16T11:57:00Z"  # 3 min before NOW  -> under the threshold


def _run(ts: str, run_id: int = 101) -> dict:
    return {
        "databaseId": run_id,
        "createdAt": ts,
        "workflowName": "ci-status-update",
        "url": f"https://github.com/IggyIkenna/unified-trading-pm/actions/runs/{run_id}",
    }


def _router(
    *,
    runs: list[dict] | None,
    jobs: list[dict] | None = None,
    runners: list[dict] | None = None,
):
    """Route mocked gh_json calls by argv shape (run list / runs-jobs / runners)."""

    def _side_effect(args: list[str]):
        if args[0] == "run" and args[1] == "list":
            return runs
        if args[0] == "api" and args[1].endswith("/jobs"):
            return {"jobs": jobs or [], "total_count": len(jobs or [])}
        if args[0] == "api" and args[1].endswith("/actions/runners"):
            return {"runners": runners or [], "total_count": len(runners or [])}
        raise AssertionError(f"unexpected gh call: {args}")

    return _side_effect


def _runner(name: str, label: str, *, status: str = "online", busy: bool = False) -> dict:
    # runners API: labels are OBJECTS ({id, name, type}) — cf. the jobs API's plain strings.
    return {
        "name": name,
        "status": status,
        "busy": busy,
        "labels": [{"id": 1, "name": "self-hosted", "type": "read-only"}, {"id": 2, "name": label, "type": "custom"}],
    }


# ── detect_glue_starvation ──────────────────────────────────────────────────────


class TestDetectGlueStarvation:
    def test_no_queued_runs_is_none(self) -> None:
        with patch.object(MOD, "gh_json", side_effect=_router(runs=[])):
            assert MOD.detect_glue_starvation(NOW) is None

    def test_gh_failure_is_none(self) -> None:
        """Best-effort: a gh error must never page (and never raise)."""
        with patch.object(MOD, "gh_json", side_effect=_router(runs=None)):
            assert MOD.detect_glue_starvation(NOW) is None

    def test_queued_under_threshold_is_none(self) -> None:
        """A job queued 3 min is normal scheduling latency, not an outage."""
        with patch.object(MOD, "gh_json", side_effect=_router(runs=[_run(FRESH_TS)])):
            assert MOD.detect_glue_starvation(NOW) is None

    def test_hosted_job_queued_does_not_page(self) -> None:
        """THE false-positive guard: a HOSTED job queueing on GitHub's capacity is not our outage.

        Without the label check this would page every time GitHub is slow — training the operator to
        ignore the alarm that exists to tell them the VM died.
        """
        jobs = [{"status": "queued", "labels": ["ubuntu-latest"]}]
        with patch.object(MOD, "gh_json", side_effect=_router(runs=[_run(STALE_TS)], jobs=jobs)):
            assert MOD.detect_glue_starvation(NOW) is None

    def test_glue_job_queued_with_zero_runners_online_diagnoses_vm_down(self) -> None:
        jobs = [{"status": "queued", "labels": ["self-hosted", "glue"]}]
        with patch.object(MOD, "gh_json", side_effect=_router(runs=[_run(STALE_TS)], jobs=jobs, runners=[])):
            out = MOD.detect_glue_starvation(NOW)
        assert out is not None
        assert out["count"] == 1
        assert out["oldest_min"] == 20
        assert "down" in out["diagnosis"]
        assert "ci-status-update" in out["workflows"]

    def test_glue_job_queued_with_runners_online_diagnoses_wedged(self) -> None:
        """Runners online but nothing draining is a DIFFERENT fault than a dead VM — say so."""
        jobs = [{"status": "queued", "labels": ["self-hosted", "glue"]}]
        runners = [_runner("glue-planning-1", "glue", busy=True)]
        with patch.object(MOD, "gh_json", side_effect=_router(runs=[_run(STALE_TS)], jobs=jobs, runners=runners)):
            out = MOD.detect_glue_starvation(NOW)
        assert out is not None
        assert "wedged" in out["diagnosis"]
        assert "down" not in out["diagnosis"]

    def test_writer_pool_label_also_detected(self) -> None:
        """glue-writer is a DISJOINT label — it must be watched too, not just `glue`."""
        jobs = [{"status": "queued", "labels": ["self-hosted", "glue-writer"]}]
        with patch.object(MOD, "gh_json", side_effect=_router(runs=[_run(STALE_TS)], jobs=jobs, runners=[])):
            assert MOD.detect_glue_starvation(NOW) is not None

    def test_running_job_is_not_starved(self) -> None:
        """Only QUEUED jobs count — an in-progress job is the pool working, not starving."""
        jobs = [{"status": "in_progress", "labels": ["self-hosted", "glue"]}]
        with patch.object(MOD, "gh_json", side_effect=_router(runs=[_run(STALE_TS)], jobs=jobs)):
            assert MOD.detect_glue_starvation(NOW) is None


# ── _glue_runner_counts ─────────────────────────────────────────────────────────


class TestGlueRunnerCounts:
    def test_counts_online_and_idle_per_disjoint_label(self) -> None:
        runners = [
            _runner("glue-planning-1", "glue"),  # online, idle
            _runner("glue-planning-2", "glue", busy=True),  # online, busy
            _runner("glue-planning-3", "glue", status="offline"),  # offline
            _runner("writer-planning-1", "glue-writer"),  # online, idle
        ]
        with patch.object(MOD, "gh_json", side_effect=_router(runs=[], runners=runners)):
            counts = MOD._glue_runner_counts()
        assert counts["glue"] == (2, 1)  # 2 online, 1 idle
        assert counts["glue-writer"] == (1, 1)

    def test_gh_failure_returns_zeros_not_raise(self) -> None:
        with patch.object(MOD, "gh_json", return_value=None):
            counts = MOD._glue_runner_counts()
        assert counts == {"glue": (0, 0), "glue-writer": (0, 0)}


# ── build_alert_items (pure) ────────────────────────────────────────────────────


class TestBuildAlertItemsGlue:
    def test_no_starvation_emits_no_glue_item(self) -> None:
        items = MOD.build_alert_items([], [], [], None, None, None, None)
        assert not [i for i in items if i["key"] == "glue-runners-starved"]

    def test_starvation_emits_critical_item_on_the_15min_renag(self) -> None:
        starvation = {
            "count": 3,
            "oldest_min": 42,
            "url": "https://github.com/x/y/actions/runs/1",
            "workflows": "ci-status-update, cloud-build-router",
            "runner_state": "glue 0 online/0 idle · glue-writer 0 online/0 idle",
            "diagnosis": "0 runners ONLINE → the glue VM is down or the runner service is stopped.",
        }
        items = MOD.build_alert_items([], [], [], None, None, None, starvation)
        glue = [i for i in items if i["key"] == "glue-runners-starved"]
        assert len(glue) == 1
        item = glue[0]
        assert item["severity"] == "CRITICAL"
        # Operator 2026-07-16: page LOUDLY every 15 min until fixed.
        assert item["cooldown_min"] == MOD.RENAG_GLUE_STARVED_MIN == 15
        # The message must carry the diagnosis, the stakes, and the fix — a page you can act on.
        assert "42m" in item["message"]
        assert "24h" in item["message"]
        assert "glue 0 online/0 idle" in item["message"]
        assert "systemctl restart" in item["message"]
        # Fleet-wide condition (spans whatever repos dispatch to the shared pool) — no single
        # subject repo.
        assert item["repo"] == ""

    def test_single_pool_item_not_one_per_job(self) -> None:
        """Every starved job shares one root cause — per-job items would be pure noise."""
        starvation = {
            "count": 37,
            "oldest_min": 90,
            "url": "",
            "workflows": "a, b, c",
            "runner_state": "glue 0 online/0 idle",
            "diagnosis": "0 runners ONLINE → the glue VM is down or the runner service is stopped.",
        }
        items = MOD.build_alert_items([], [], [], None, None, None, starvation)
        assert len([i for i in items if i["key"] == "glue-runners-starved"]) == 1
