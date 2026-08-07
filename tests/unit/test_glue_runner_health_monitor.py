"""Unit tests for the pure decision logic in scripts/cicd/glue_runner_health_monitor.py.

The monitor's whole reason to exist is the 2026-08-06 incident where the LDR→main fleet promoter
stalled 3+ hours because the `glue` runner pool ran at 25% capacity (2 of 4 runners online) while
the scheduler cancelled every queued run before a runner picked it up
(fleet_promoter_glue_runner_stall_2026_08_06.md). These tests cover the "count online glue runners,
page below threshold" contract: a depleted pool fires, a healthy pool fires nothing, and the
`glue-writer` pool is never miscounted as `glue`.
"""

from __future__ import annotations

import importlib.util
import types
from pathlib import Path


def _load_module() -> types.ModuleType:
    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "scripts" / "cicd" / "glue_runner_health_monitor.py"
    spec = importlib.util.spec_from_file_location("glue_runner_health_monitor", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


GRH = _load_module()


def _runner(name: str, status: str = "online", labels: list[str] | None = None) -> dict[str, object]:
    return {
        "name": name,
        "status": status,
        "busy": False,
        "labels": [{"name": lbl} for lbl in (labels if labels is not None else ["self-hosted", "glue"])],
    }


# ── is_glue_runner — exact-membership, "glue-writer" must never satisfy "glue" ───────────────────


def test_is_glue_runner_true_for_glue_label() -> None:
    assert GRH.is_glue_runner(_runner("glue-ip-1-1")) is True


def test_is_glue_runner_false_for_glue_writer_disjoint_pool() -> None:
    assert GRH.is_glue_runner(_runner("writer-ip-1-1", labels=["self-hosted", "glue-writer"])) is False


def test_is_glue_runner_false_for_runner_without_labels() -> None:
    assert GRH.is_glue_runner({"name": "ghost", "status": "online", "busy": False, "labels": []}) is False


def test_is_glue_runner_false_for_non_list_labels() -> None:
    assert GRH.is_glue_runner({"name": "ghost", "status": "online", "busy": False, "labels": "glue"}) is False


# ── count_online_glue_runners ──────────────────────────────────────────────────────────────────


def test_counts_only_online_glue_runners_excluding_writers() -> None:
    runners = [
        _runner("glue-ip-1-1", "online"),
        _runner("glue-ip-1-2", "offline"),
        _runner("writer-ip-1-1", "online", labels=["self-hosted", "glue-writer"]),
        _runner("hosted", "online", labels=["ubuntu-latest"]),
    ]
    assert GRH.count_online_glue_runners(runners) == 1


def test_zero_online_when_no_glue_runners() -> None:
    assert GRH.count_online_glue_runners([]) == 0


def test_all_glue_runners_online() -> None:
    runners = [_runner("glue-ip-1-1"), _runner("glue-ip-1-2"), _runner("glue-ip-1-3")]
    assert GRH.count_online_glue_runners(runners) == 3


# ── offline_glue_runner_names ──────────────────────────────────────────────────────────────────


def test_lists_only_offline_glue_runner_names() -> None:
    runners = [
        _runner("glue-ip-1-1", "online"),
        _runner("glue-ip-1-2", "offline"),
        _runner("glue-ip-1-3", "offline"),
        _runner("writer-ip-1-1", "offline", labels=["self-hosted", "glue-writer"]),
    ]
    assert GRH.offline_glue_runner_names(runners) == ["glue-ip-1-2", "glue-ip-1-3"]


# ── build_report ──────────────────────────────────────────────────────────────────────────────


def test_build_report_healthy_names_no_alert() -> None:
    report = GRH.build_report(online=3, offline=[], min_online=3, total=3)
    assert "healthy" in report
    assert "depleted" not in report.lower()


def test_build_report_depleted_names_online_and_threshold() -> None:
    report = GRH.build_report(online=2, offline=["glue-ip-1-3"], min_online=3, total=3)
    assert "depleted" in report.lower()
    assert "2/3" in report
    assert "glue-ip-1-3" in report


def test_build_report_depleted_with_no_offline_names_the_shrink_case() -> None:
    report = GRH.build_report(online=1, offline=[], min_online=3, total=1)
    assert "depleted" in report.lower()
    assert "shrunk" in report.lower()
