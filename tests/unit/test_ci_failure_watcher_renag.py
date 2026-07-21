"""Unit tests for the Phase 5 re-nag layer in ci_failure_watcher.

Covers detect_currently_failing (current-state detector that lets a still-red workflow
re-surface) and build_alert_items (the pure per-condition mapper that feeds the matrix
notify). All gh/network calls are mocked. SSOT: alert_quality_overhaul_2026_06_18 § Phase 5.
"""

from __future__ import annotations

import datetime as _dt
import importlib.util
import os
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
    spec = importlib.util.spec_from_file_location("ci_failure_watcher_renag", watcher_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


MOD = _load_module()
NOW = _dt.datetime(2026, 6, 19, 12, 0, 0, tzinfo=_dt.UTC)


# ── _wf_slug ────────────────────────────────────────────────────────────────────


class TestWfSlug:
    def test_lowercases_and_dashes_non_alnum(self) -> None:
        assert MOD._wf_slug("Quality Gates v2") == "quality-gates-v2"

    def test_strips_edge_dashes_and_collapses(self) -> None:
        assert MOD._wf_slug("  CI / Build  ").startswith("ci")
        assert not MOD._wf_slug("CI/Build").startswith("-")

    def test_empty_falls_back(self) -> None:
        assert MOD._wf_slug("") == "wf"


# ── detect_currently_failing ─────────────────────────────────────────────────────


class TestDetectCurrentlyFailing:
    def _runs(self, conclusion: str, created: str) -> list[dict]:
        return [
            {
                "workflowName": "quality-gates-v2",
                "conclusion": conclusion,
                "status": "completed",
                "createdAt": created,
                "url": "https://github.com/run/1",
                "databaseId": 1,
                "headSha": "abc",
            }
        ]

    def test_currently_failing_within_window_is_reported(self) -> None:
        runs = self._runs("failure", "2026-06-19T11:30:00Z")  # 30 min ago
        with (
            patch.object(MOD, "gh_json", return_value=runs),
            patch.object(MOD, "classify_pusher", return_value=("bot", "automation")),
        ):
            out = MOD.detect_currently_failing("mtds", "main", 25, NOW, window_hours=6.0)
        assert len(out) == 1
        assert out[0]["kind"] == "failing"
        assert out[0]["workflow"] == "quality-gates-v2"
        assert out[0]["age_min"] == 30

    def test_green_latest_is_not_reported(self) -> None:
        runs = self._runs("success", "2026-06-19T11:30:00Z")
        with (
            patch.object(MOD, "gh_json", return_value=runs),
            patch.object(MOD, "classify_pusher", return_value=("bot", "automation")),
        ):
            out = MOD.detect_currently_failing("mtds", "main", 25, NOW, window_hours=6.0)
        assert out == []

    def test_failure_older_than_window_is_not_resurfaced(self) -> None:
        runs = self._runs("failure", "2026-06-19T04:00:00Z")  # 8 h ago, window 6 h
        with (
            patch.object(MOD, "gh_json", return_value=runs),
            patch.object(MOD, "classify_pusher", return_value=("bot", "automation")),
        ):
            out = MOD.detect_currently_failing("mtds", "main", 25, NOW, window_hours=6.0)
        assert out == []

    def test_latest_run_wins_over_older_failing(self) -> None:
        # Newest run is green → not failing even though an older run failed.
        runs = [
            {
                "workflowName": "qg",
                "conclusion": "failure",
                "status": "completed",
                "createdAt": "2026-06-19T10:00:00Z",
                "url": "u1",
                "databaseId": 1,
                "headSha": "a",
            },
            {
                "workflowName": "qg",
                "conclusion": "success",
                "status": "completed",
                "createdAt": "2026-06-19T11:45:00Z",
                "url": "u2",
                "databaseId": 2,
                "headSha": "b",
            },
        ]
        with (
            patch.object(MOD, "gh_json", return_value=runs),
            patch.object(MOD, "classify_pusher", return_value=("bot", "automation")),
        ):
            out = MOD.detect_currently_failing("mtds", "main", 25, NOW, window_hours=6.0)
        assert out == []

    def test_non_list_response_is_safe(self) -> None:
        with patch.object(MOD, "gh_json", return_value=None):
            assert MOD.detect_currently_failing("mtds", "main", 25, NOW, window_hours=6.0) == []


# ── build_alert_items ────────────────────────────────────────────────────────────


class TestBuildAlertItems:
    def _fail(self) -> dict:
        return {
            "repo": "mtds",
            "branch": "main",
            "workflow": "quality-gates-v2",
            "conclusion": "failure",
            "url": "https://github.com/run/1",
            "pusher_name": "bot",
            "pusher_role": "automation",
            "age_min": 75,
        }

    def _stuck(self) -> dict:
        return {
            "repo": "mtds",
            "number": 42,
            "head": "live-defi-rollout",
            "base": "staging",
            "state": "BLOCKED",
            "auto_merge": True,
            "age_min": 35,
            "url": "https://github.com/pr/42",
        }

    def test_empty_yields_empty_list(self) -> None:
        assert MOD.build_alert_items([], [], [], [], None) == []

    def test_failing_item_key_and_cooldown(self) -> None:
        items = MOD.build_alert_items([self._fail()], [], [], [], None)
        assert len(items) == 1
        it = items[0]
        assert it["key"] == "ci-fail:mtds:main:quality-gates-v2"
        assert it["cooldown_min"] == MOD.RENAG_WORKFLOW_FAIL_MIN == 60
        assert it["severity"] == "CRITICAL"
        assert "<https://github.com/run/1|run>" in it["message"]
        # This watcher itself always runs as unified-trading-pm — the item must carry the real
        # subject repo explicitly so notify-slack.yml can stamp a distinct subject_repo.
        assert it["repo"] == "mtds"

    def test_failing_item_renders_reason_when_enriched(self) -> None:
        f = self._fail()
        f["failed_jobs"] = ["typecheck"]
        f["log_excerpt"] = "boom"
        items = MOD.build_alert_items([f], [], [], [], None)
        assert "↳ failed: typecheck" in items[0]["message"]
        assert "boom" in items[0]["message"]

    def test_stuck_item_key_and_cooldown(self) -> None:
        items = MOD.build_alert_items([], [], [self._stuck()], [], None)
        assert items[0]["key"] == "stuck-pr:mtds:42"
        assert items[0]["cooldown_min"] == MOD.RENAG_STUCK_PR_MIN == 20
        assert "<https://github.com/pr/42|open PR>" in items[0]["message"]
        assert items[0]["repo"] == "mtds"

    def test_billing_item_is_fleet_frozen_cooldown(self) -> None:
        billing = {"repo": "mtds", "workflow": "qg", "url": "https://github.com/run/9"}
        items = MOD.build_alert_items([], [], [], [], billing)
        assert items[0]["key"] == "ci-billing-block"
        assert items[0]["cooldown_min"] == MOD.RENAG_FLEET_FROZEN_MIN == 20
        assert "BILLING BLOCK" in items[0]["message"]
        # Fleet-wide condition (blocks ALL repos) — no single subject repo.
        assert items[0]["repo"] == ""

    def test_recovered_bookend_short_cooldown_distinct_key(self) -> None:
        rec = {"repo": "mtds", "branch": "main", "workflow": "qg", "url": "u"}
        items = MOD.build_alert_items([], [rec], [], [], None)
        assert items[0]["key"] == "ci-recovered:mtds:main:qg"
        assert items[0]["cooldown_min"] == MOD.BOOKEND_COOLDOWN_MIN == 5
        assert items[0]["severity"] == "INFO"
        assert items[0]["repo"] == "mtds"

    def test_resolved_bookend(self) -> None:
        res = {"repo": "mtds", "number": 7, "head": "live-defi-rollout", "base": "main", "merged": True, "url": "u"}
        items = MOD.build_alert_items([], [], [], [res], None)
        assert items[0]["key"] == "resolved-pr:mtds:7"
        assert items[0]["severity"] == "INFO"
        assert "merged" in items[0]["message"]
        assert items[0]["repo"] == "mtds"

    def test_billing_sorts_first(self) -> None:
        billing = {"repo": "mtds", "workflow": "qg", "url": "u"}
        items = MOD.build_alert_items([self._fail()], [], [self._stuck()], [], billing)
        assert items[0]["key"] == "ci-billing-block"


# ── write_github_output: alerts line ─────────────────────────────────────────────


class TestWriteGithubOutputAlerts:
    def test_alerts_line_written_as_compact_json(self, tmp_path) -> None:
        out = tmp_path / "gh_output"
        items = [
            {"key": "ci-fail:mtds:main:qg", "severity": "CRITICAL", "cooldown_min": 60, "url": "u", "message": "x\ny"}
        ]
        with patch.dict(os.environ, {"GITHUB_OUTPUT": str(out)}):
            MOD.write_github_output(True, "CRITICAL", "report", items)
        text = out.read_text(encoding="utf-8")
        # one line, no literal newline inside the JSON (message \n is escaped)
        alerts_line = next(ln for ln in text.splitlines() if ln.startswith("alerts="))
        assert '"ci-fail:mtds:main:qg"' in alerts_line
        assert "\\n" in alerts_line  # message newline escaped, stayed single-line

    def test_alerts_defaults_to_empty_array(self, tmp_path) -> None:
        out = tmp_path / "gh_output"
        with patch.dict(os.environ, {"GITHUB_OUTPUT": str(out)}):
            MOD.write_github_output(False, "INFO", "report", None)
        assert "alerts=[]" in out.read_text(encoding="utf-8")
