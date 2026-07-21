"""Tests for flap suppression (L1573) and zero-check-run alert (L1581).

Covers:
  - _is_flapping(): the standalone oscillation detector
  - detect_transitions(): flapping flag propagation
  - detect_currently_failing(): flapping flag propagation
  - build_report(): flapping section; zero_checks tag in stuck-PR line
  - build_alert_items(): ci-flap: key (WARNING / RENAG_FLAPPING_MIN) and
    zero-checks: key (CRITICAL) paths
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
    spec = importlib.util.spec_from_file_location("ci_failure_watcher_flap", watcher_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


MOD = _load_module()

NOW = _dt.datetime(2026, 6, 27, 12, 0, 0, tzinfo=_dt.UTC)
RECENT_TS = "2026-06-27T11:30:00Z"  # 30 min ago


def _run(conclusion: str, created: str = RECENT_TS, status: str = "completed") -> dict:
    return {
        "workflowName": "quality-gates-v2",
        "conclusion": conclusion,
        "status": status,
        "createdAt": created,
        "url": "https://github.com/run/1",
        "databaseId": 1,
        "headSha": "abc123",
        "event": "push",
    }


# ── _is_flapping ──────────────────────────────────────────────────────────────


class TestIsFlapping:
    def test_fewer_than_3_runs_returns_false(self) -> None:
        runs = [
            {"conclusion": "failure"},
            {"conclusion": "success"},
        ]
        assert MOD._is_flapping(runs, threshold=1) is False

    def test_exactly_3_runs_stable_failure_no_flap(self) -> None:
        runs = [
            {"conclusion": "failure"},
            {"conclusion": "failure"},
            {"conclusion": "failure"},
        ]
        assert MOD._is_flapping(runs, threshold=3) is False

    def test_3_oscillating_runs_below_threshold_not_flapping(self) -> None:
        # fail→success→fail = 2 transitions; threshold=3 → not flapping
        runs = [
            {"conclusion": "failure"},
            {"conclusion": "success"},
            {"conclusion": "failure"},
        ]
        assert MOD._is_flapping(runs, threshold=3) is False

    def test_5_oscillating_runs_meets_threshold(self) -> None:
        # fail→success→fail→success→fail = 4 transitions; threshold=3 → flapping
        runs = [
            {"conclusion": "failure"},
            {"conclusion": "success"},
            {"conclusion": "failure"},
            {"conclusion": "success"},
            {"conclusion": "failure"},
        ]
        assert MOD._is_flapping(runs, threshold=3) is True

    def test_threshold_boundary_equal(self) -> None:
        # exactly 3 transitions; threshold=3 → True (>= not >)
        runs = [
            {"conclusion": "failure"},
            {"conclusion": "success"},
            {"conclusion": "failure"},
            {"conclusion": "success"},
        ]
        assert MOD._is_flapping(runs, threshold=3) is True

    def test_missing_conclusion_treated_as_non_failing(self) -> None:
        # None is not in _FAIL_CONCLUSIONS so it counts as success side;
        # oscillation: fail→None→fail = 2 transitions; threshold=2 → True
        runs = [
            {"conclusion": "failure"},
            {"conclusion": None},
            {"conclusion": "failure"},
        ]
        assert MOD._is_flapping(runs, threshold=2) is True

    def test_stable_success_sequence_not_flapping(self) -> None:
        runs = [{"conclusion": "success"} for _ in range(5)]
        assert MOD._is_flapping(runs, threshold=3) is False

    def test_default_threshold_integration(self) -> None:
        # Matches constants: FLAP_DETECT_RUNS=5, FLAP_TRANSITION_THRESHOLD=3
        assert MOD.FLAP_DETECT_RUNS == 5
        assert MOD.FLAP_TRANSITION_THRESHOLD == 3
        # 4 transitions in 5 runs → flapping
        runs = [
            {"conclusion": "failure"},
            {"conclusion": "success"},
            {"conclusion": "failure"},
            {"conclusion": "success"},
            {"conclusion": "failure"},
        ]
        assert MOD._is_flapping(runs, MOD.FLAP_TRANSITION_THRESHOLD) is True


# ── detect_transitions: flapping flag ────────────────────────────────────────


class TestDetectTransitionsFlapping:
    def _oscillating_runs(self) -> list[dict]:
        """5 recent runs alternating fail/success → _is_flapping=True with default threshold=3."""
        conclusions = ["failure", "success", "failure", "success", "failure"]
        # Must be sorted newest-first; give each a slightly different timestamp
        base = _dt.datetime(2026, 6, 27, 11, 30, tzinfo=_dt.UTC)
        runs = []
        for i, c in enumerate(conclusions):
            ts = (base - _dt.timedelta(minutes=i * 5)).strftime("%Y-%m-%dT%H:%M:%SZ")
            runs.append(
                {
                    "workflowName": "quality-gates-v2",
                    "conclusion": c,
                    "status": "completed",
                    "createdAt": ts,
                    "url": "https://github.com/run/1",
                    "databaseId": i + 1,
                    "headSha": f"sha{i}",
                    "event": "push",
                }
            )
        return runs

    def test_flapping_flag_true_when_oscillating(self) -> None:
        runs = self._oscillating_runs()
        # latest (index 0) is failure, prev (index 1) is success → failing transition
        with (
            patch.object(MOD, "gh_json", return_value=runs),
            patch.object(MOD, "classify_pusher", return_value=("bot", "automation")),
        ):
            result = MOD.detect_transitions("mtds", "main", 25, NOW, 2.0)
        assert len(result) == 1
        assert result[0]["kind"] == "failing"
        assert result[0]["flapping"] is True

    def test_flapping_flag_false_when_stable_failure(self) -> None:
        # Only 2 runs: both failures → not enough for _is_flapping (< 3 runs)
        runs = [
            _run("failure", RECENT_TS),
            _run("success", "2026-06-27T11:00:00Z"),
        ]
        with (
            patch.object(MOD, "gh_json", return_value=runs),
            patch.object(MOD, "classify_pusher", return_value=("bot", "automation")),
        ):
            result = MOD.detect_transitions("mtds", "main", 25, NOW, 2.0)
        assert len(result) == 1
        assert result[0]["flapping"] is False

    def test_recovered_transition_carries_flapping_flag(self) -> None:
        # latest=success, prev=failure, but oscillating history → recovered + flapping
        conclusions = ["success", "failure", "success", "failure", "success"]
        base = _dt.datetime(2026, 6, 27, 11, 30, tzinfo=_dt.UTC)
        runs = []
        for i, c in enumerate(conclusions):
            ts = (base - _dt.timedelta(minutes=i * 5)).strftime("%Y-%m-%dT%H:%M:%SZ")
            runs.append(
                {
                    "workflowName": "quality-gates-v2",
                    "conclusion": c,
                    "status": "completed",
                    "createdAt": ts,
                    "url": "https://github.com/run/2",
                    "databaseId": i + 10,
                    "headSha": f"sha{i}",
                    "event": "push",
                }
            )
        with (
            patch.object(MOD, "gh_json", return_value=runs),
            patch.object(MOD, "classify_pusher", return_value=("bot", "automation")),
        ):
            result = MOD.detect_transitions("mtds", "main", 25, NOW, 2.0)
        assert len(result) == 1
        assert result[0]["kind"] == "recovered"
        assert result[0]["flapping"] is True


# ── detect_currently_failing: flapping flag ───────────────────────────────────


class TestDetectCurrentlyFailingFlapping:
    def _oscillating_runs(self) -> list[dict]:
        conclusions = ["failure", "success", "failure", "success", "failure"]
        base = _dt.datetime(2026, 6, 27, 11, 30, tzinfo=_dt.UTC)
        runs = []
        for i, c in enumerate(conclusions):
            ts = (base - _dt.timedelta(minutes=i * 5)).strftime("%Y-%m-%dT%H:%M:%SZ")
            runs.append(
                {
                    "workflowName": "quality-gates-v2",
                    "conclusion": c,
                    "status": "completed",
                    "createdAt": ts,
                    "url": "https://github.com/run/1",
                    "databaseId": i + 1,
                    "headSha": "sha",
                    "event": "push",
                }
            )
        return runs

    def test_flapping_flag_set_on_currently_failing(self) -> None:
        runs = self._oscillating_runs()
        with (
            patch.object(MOD, "gh_json", return_value=runs),
            patch.object(MOD, "classify_pusher", return_value=("bot", "automation")),
        ):
            result = MOD.detect_currently_failing("mtds", "main", 25, NOW, window_hours=6.0)
        assert len(result) == 1
        assert result[0]["flapping"] is True

    def test_flapping_flag_false_for_stable_failure(self) -> None:
        # Single run: only 1 run, < 3 → _is_flapping returns False
        runs = [
            {
                "workflowName": "quality-gates-v2",
                "conclusion": "failure",
                "status": "completed",
                "createdAt": RECENT_TS,
                "url": "https://github.com/run/1",
                "databaseId": 1,
                "headSha": "sha",
                "event": "push",
            }
        ]
        with (
            patch.object(MOD, "gh_json", return_value=runs),
            patch.object(MOD, "classify_pusher", return_value=("bot", "automation")),
        ):
            result = MOD.detect_currently_failing("mtds", "main", 25, NOW, window_hours=6.0)
        assert len(result) == 1
        assert result[0]["flapping"] is False


# ── build_report: flapping section ───────────────────────────────────────────


class TestBuildReportFlapping:
    def _flapping_fail_t(self, repo: str = "mtds") -> dict:
        return {
            "kind": "failing",
            "repo": repo,
            "branch": "main",
            "workflow": "quality-gates-v2",
            "conclusion": "failure",
            "url": "https://github.com/run/1",
            "pusher_name": "bot",
            "pusher_role": "automation",
            "flapping": True,
        }

    def _flapping_rec_t(self, repo: str = "mtds") -> dict:
        return {
            "kind": "recovered",
            "repo": repo,
            "branch": "main",
            "workflow": "quality-gates-v2",
            "conclusion": "success",
            "url": "https://github.com/run/2",
            "pusher_name": "bot",
            "pusher_role": "automation",
            "flapping": True,
        }

    def _stable_fail_t(self) -> dict:
        return {
            "kind": "failing",
            "repo": "mtds",
            "branch": "main",
            "workflow": "quality-gates-v2",
            "conclusion": "failure",
            "url": "https://github.com/run/3",
            "pusher_name": "ikennaigboaka",
            "pusher_role": "human",
            "flapping": False,
        }

    def test_flapping_transitions_excluded_from_failing_section(self) -> None:
        # A flapping=True failing transition should NOT appear in the "STARTED FAILING" section
        _alert, _severity, report = MOD.build_report([self._flapping_fail_t()], [], [], None)
        assert "STARTED FAILING" not in report

    def test_flapping_section_appears_in_report(self) -> None:
        _alert, _severity, report = MOD.build_report([self._flapping_fail_t()], [], [], None)
        assert "FLAPPING" in report

    def test_flapping_only_does_not_trigger_critical(self) -> None:
        # Flapping alone is informational — severity should be INFO, not CRITICAL
        _alert, severity, _report = MOD.build_report([self._flapping_fail_t()], [], [], None)
        assert severity == "INFO"

    def test_flapping_alert_flag_is_true(self) -> None:
        # The alert flag is True so Slack output is emitted (channel notices flapping)
        alert, _severity, _report = MOD.build_report([self._flapping_fail_t()], [], [], None)
        assert alert is True

    def test_stable_failure_plus_flapping_is_critical(self) -> None:
        transitions = [self._stable_fail_t(), self._flapping_fail_t()]
        _alert, severity, report = MOD.build_report(transitions, [], [], None)
        assert severity == "CRITICAL"
        assert "STARTED FAILING" in report
        assert "FLAPPING" in report

    def test_flapping_recovered_excluded_from_recovered_section(self) -> None:
        _alert, _severity, report = MOD.build_report([self._flapping_rec_t()], [], [], None)
        assert "RECOVERED" not in report
        assert "FLAPPING" in report

    def test_flapping_count_in_section_header(self) -> None:
        transitions = [self._flapping_fail_t("mtds"), self._flapping_fail_t("execution-service")]
        _alert, _severity, report = MOD.build_report(transitions, [], [], None)
        assert "2 workflow(s) FLAPPING" in report

    def test_flapping_entry_shows_workflow_name(self) -> None:
        _alert, _severity, report = MOD.build_report([self._flapping_fail_t()], [], [], None)
        assert "quality-gates-v2" in report

    def test_flapping_return_includes_flapping_in_final_flag(self) -> None:
        # flapping alone drives the return tuple's first element True
        result, _, _ = MOD.build_report([self._flapping_fail_t()], [], [], None)
        assert result is True


# ── build_report: zero_checks tag on stuck PRs ───────────────────────────────


class TestBuildReportZeroChecks:
    def _stuck(self, zero_checks: bool = False) -> dict:
        return {
            "repo": "mtds",
            "base": "staging",
            "number": 42,
            "head": "live-defi-rollout",
            "state": "BLOCKED",
            "auto_merge": True,
            "age_min": 50,
            "url": "https://github.com/pr/42",
            "failed_check": False,
            "v2_present": False,
            "v2_action_required": False,
            "head_message": "feat: add thing",
            "head_oid": "abc123",
            "zero_checks": zero_checks,
        }

    def test_zero_checks_tag_appears_in_report(self) -> None:
        _, _, report = MOD.build_report([], [self._stuck(zero_checks=True)], [], None)
        assert "ZERO CHECK RUNS" in report

    def test_normal_stuck_pr_has_no_zero_checks_tag(self) -> None:
        _, _, report = MOD.build_report([], [self._stuck(zero_checks=False)], [], None)
        assert "ZERO CHECK RUNS" not in report

    def test_zero_checks_still_shows_pr_info(self) -> None:
        _, _, report = MOD.build_report([], [self._stuck(zero_checks=True)], [], None)
        assert "#42" in report


# ── build_alert_items: flapping path ─────────────────────────────────────────


class TestBuildAlertItemsFlapping:
    def _flapping_failing(self) -> dict:
        return {
            "kind": "failing",
            "repo": "mtds",
            "branch": "main",
            "workflow": "quality-gates-v2",
            "conclusion": "failure",
            "url": "https://github.com/run/1",
            "pusher_name": "bot",
            "pusher_role": "automation",
            "age_min": 15,
            "flapping": True,
        }

    def _stable_failing(self) -> dict:
        return {
            "kind": "failing",
            "repo": "mtds",
            "branch": "main",
            "workflow": "quality-gates-v2",
            "conclusion": "failure",
            "url": "https://github.com/run/2",
            "pusher_name": "ikennaigboaka",
            "pusher_role": "human",
            "age_min": 20,
            "flapping": False,
        }

    def test_flapping_item_uses_ci_flap_key(self) -> None:
        items = MOD.build_alert_items([self._flapping_failing()], [], [], [], None)
        keys = [i["key"] for i in items]
        assert any(k.startswith("ci-flap:") for k in keys)

    def test_flapping_item_severity_is_warning(self) -> None:
        items = MOD.build_alert_items([self._flapping_failing()], [], [], [], None)
        flap_items = [i for i in items if i["key"].startswith("ci-flap:")]
        assert len(flap_items) == 1
        assert flap_items[0]["severity"] == "WARNING"

    def test_flapping_item_cooldown_is_renag_flapping_min(self) -> None:
        items = MOD.build_alert_items([self._flapping_failing()], [], [], [], None)
        flap_items = [i for i in items if i["key"].startswith("ci-flap:")]
        assert flap_items[0]["cooldown_min"] == MOD.RENAG_FLAPPING_MIN

    def test_flapping_key_includes_repo_branch_workflow(self) -> None:
        items = MOD.build_alert_items([self._flapping_failing()], [], [], [], None)
        flap_items = [i for i in items if i["key"].startswith("ci-flap:")]
        assert "mtds" in flap_items[0]["key"]
        assert "main" in flap_items[0]["key"]

    def test_flapping_message_contains_flapping_label(self) -> None:
        items = MOD.build_alert_items([self._flapping_failing()], [], [], [], None)
        flap_items = [i for i in items if i["key"].startswith("ci-flap:")]
        assert "FLAPPING" in flap_items[0]["message"]

    def test_flapping_item_carries_subject_repo(self) -> None:
        items = MOD.build_alert_items([self._flapping_failing()], [], [], [], None)
        flap_items = [i for i in items if i["key"].startswith("ci-flap:")]
        assert flap_items[0]["repo"] == "mtds"

    def test_stable_failing_uses_ci_fail_key_not_flap(self) -> None:
        items = MOD.build_alert_items([self._stable_failing()], [], [], [], None)
        keys = [i["key"] for i in items]
        assert not any(k.startswith("ci-flap:") for k in keys)
        assert any(k.startswith("ci-fail:") for k in keys)

    def test_stable_failing_severity_is_critical(self) -> None:
        items = MOD.build_alert_items([self._stable_failing()], [], [], [], None)
        fail_items = [i for i in items if i["key"].startswith("ci-fail:")]
        assert fail_items[0]["severity"] == "CRITICAL"


# ── build_alert_items: zero_checks path ──────────────────────────────────────


class TestBuildAlertItemsZeroChecks:
    def _stuck(self, zero_checks: bool = False) -> dict:
        return {
            "repo": "mtds",
            "base": "staging",
            "number": 55,
            "head": "live-defi-rollout",
            "state": "BLOCKED",
            "auto_merge": True,
            "age_min": 45,
            "url": "https://github.com/pr/55",
            "failed_check": False,
            "v2_present": False,
            "v2_action_required": False,
            "head_message": "feat: thing",
            "head_oid": "deadbeef",
            "zero_checks": zero_checks,
        }

    def test_zero_checks_uses_distinct_key(self) -> None:
        items = MOD.build_alert_items([], [], [self._stuck(zero_checks=True)])
        keys = [i["key"] for i in items]
        assert any(k.startswith("zero-checks:") for k in keys)

    def test_zero_checks_is_critical(self) -> None:
        items = MOD.build_alert_items([], [], [self._stuck(zero_checks=True)])
        zc = [i for i in items if i["key"].startswith("zero-checks:")]
        assert len(zc) == 1
        assert zc[0]["severity"] == "CRITICAL"

    def test_zero_checks_message_explains_the_condition(self) -> None:
        items = MOD.build_alert_items([], [], [self._stuck(zero_checks=True)])
        zc = [i for i in items if i["key"].startswith("zero-checks:")]
        msg = zc[0]["message"]
        assert "ZERO CHECK RUNS" in msg or "zero" in msg.lower()

    def test_normal_stuck_uses_stuck_pr_key(self) -> None:
        items = MOD.build_alert_items([], [], [self._stuck(zero_checks=False)])
        keys = [i["key"] for i in items]
        assert any(k.startswith("stuck-pr:") for k in keys)
        assert not any(k.startswith("zero-checks:") for k in keys)

    def test_normal_stuck_severity_is_critical(self) -> None:
        items = MOD.build_alert_items([], [], [self._stuck(zero_checks=False)])
        stuck = [i for i in items if i["key"].startswith("stuck-pr:")]
        assert stuck[0]["severity"] == "CRITICAL"

    def test_zero_checks_key_includes_repo_and_number(self) -> None:
        items = MOD.build_alert_items([], [], [self._stuck(zero_checks=True)])
        zc = [i for i in items if i["key"].startswith("zero-checks:")]
        assert "mtds" in zc[0]["key"]

    def test_zero_checks_item_carries_subject_repo(self) -> None:
        items = MOD.build_alert_items([], [], [self._stuck(zero_checks=True)])
        zc = [i for i in items if i["key"].startswith("zero-checks:")]
        assert zc[0]["repo"] == "mtds"
        assert "55" in zc[0]["key"]
