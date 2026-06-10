"""Unit tests for ci_failure_watcher core detection functions.

Covers build_report (failing/recovered/stuck/resolved arms), write_github_output,
detect_transitions, detect_stuck_prs, detect_resolved_prs, _run_is_billing_block,
and detect_billing_block — all with gh_json mocked (no network).

Complements the billing, escalate, auto-recover, and classify test files.
"""

from __future__ import annotations

import datetime as _dt
import importlib.util
import os
import sys
import types
from pathlib import Path
from unittest.mock import patch

import pytest

# ── Module loader ──────────────────────────────────────────────────────────────


def _load_module() -> types.ModuleType:
    repo_root = Path(__file__).resolve().parents[2]
    watcher_path = repo_root / "scripts" / "repo-management" / "ci_failure_watcher.py"
    stub = types.ModuleType("pin_branch_protection_rulesets")
    stub.ORG = "IggyIkenna"  # type: ignore[attr-defined]
    stub.REPOS = []  # type: ignore[attr-defined]
    sys.modules.setdefault("pin_branch_protection_rulesets", stub)
    spec = importlib.util.spec_from_file_location("ci_failure_watcher_core", watcher_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


MOD = _load_module()

# Fixed "now" so all age calculations are deterministic
NOW = _dt.datetime(2026, 6, 10, 12, 0, 0, tzinfo=_dt.UTC)
# 30 min ago — inside any fresh_hours >= 1 window
RECENT_TS = "2026-06-10T11:30:00Z"
# 48 h ago — outside any fresh_hours <= 24 window
OLD_TS = "2026-06-08T12:00:00Z"


# ── build_report: failing/recovered/stuck/resolved arms ───────────────────────


class TestBuildReportTransitions:
    def _fail_t(self, repo: str = "mtds", workflow: str = "quality-gates-v2") -> dict:
        return {
            "kind": "failing",
            "repo": repo,
            "branch": "main",
            "workflow": workflow,
            "conclusion": "failure",
            "url": "https://github.com/run/1",
            "pusher_name": "github-actions[bot]",
            "pusher_role": "automation",
        }

    def _rec_t(self, repo: str = "mtds") -> dict:
        return {
            "kind": "recovered",
            "repo": repo,
            "branch": "main",
            "workflow": "quality-gates-v2",
            "conclusion": "success",
            "url": "https://github.com/run/2",
            "pusher_name": "ikennaigboaka",
            "pusher_role": "human",
        }

    def test_failing_triggers_critical_alert(self) -> None:
        alert, severity, report = MOD.build_report([self._fail_t()], [], [], None)
        assert alert is True
        assert severity == "CRITICAL"
        assert "STARTED FAILING" in report
        assert "quality-gates-v2" in report

    def test_failing_includes_pusher(self) -> None:
        _, _, report = MOD.build_report([self._fail_t()], [], [], None)
        assert "automation" in report

    def test_multiple_failing(self) -> None:
        transitions = [self._fail_t("mtds"), self._fail_t("execution-service")]
        _, severity, report = MOD.build_report(transitions, [], [], None)
        assert severity == "CRITICAL"
        assert "2 workflow(s)" in report

    def test_recovered_only_is_info(self) -> None:
        _alert, severity, report = MOD.build_report([self._rec_t()], [], [], None)
        # recovered alone → no page (INFO), but alert flag is True so output is emitted
        assert severity == "INFO"
        assert "RECOVERED" in report

    def test_failing_and_recovered_together(self) -> None:
        alert, severity, report = MOD.build_report([self._fail_t(), self._rec_t()], [], [], None)
        assert alert is True
        assert severity == "CRITICAL"
        assert "STARTED FAILING" in report
        assert "RECOVERED" in report

    def test_empty_returns_info_no_alert(self) -> None:
        alert, severity, report = MOD.build_report([], [], [], None)
        assert alert is False
        assert severity == "INFO"
        assert "No CI transitions" in report


class TestBuildReportStuck:
    def _stuck(self, state: str = "BLOCKED", auto_merge: bool = True) -> dict:
        return {
            "repo": "mtds",
            "number": 42,
            "head": "live-defi-rollout",
            "base": "staging",
            "state": state,
            "age_min": 45,
            "auto_merge": auto_merge,
            "url": "https://github.com/pr/42",
        }

    def test_stuck_pr_triggers_critical_alert(self) -> None:
        alert, severity, report = MOD.build_report([], [self._stuck()], [], None)
        assert alert is True
        assert severity == "CRITICAL"
        assert "STUCK" in report
        assert "42" in report

    def test_stuck_with_auto_merge_off(self) -> None:
        _, _, report = MOD.build_report([], [self._stuck(auto_merge=False)], [], None)
        assert "auto-merge OFF" in report

    def test_conflicting_stuck(self) -> None:
        _, _, report = MOD.build_report([], [self._stuck("CONFLICTING")], [], None)
        assert "CONFLICTING" in report


class TestBuildReportResolved:
    def _resolved(self, merged: bool = True) -> dict:
        return {
            "repo": "mtds",
            "number": 10,
            "head": "live-defi-rollout",
            "base": "staging",
            "merged": merged,
            "url": "https://github.com/pr/10",
        }

    def test_resolved_bookend_is_info(self) -> None:
        _alert, severity, report = MOD.build_report([], [], [self._resolved()], None)
        assert severity == "INFO"
        assert "RESOLVED" in report

    def test_merged_verb(self) -> None:
        _, _, report = MOD.build_report([], [], [self._resolved(merged=True)], None)
        assert "merged" in report

    def test_closed_not_merged_verb(self) -> None:
        _, _, report = MOD.build_report([], [], [self._resolved(merged=False)], None)
        assert "closed" in report

    def test_resolved_alone_sets_alert_true(self) -> None:
        # resolved alone → alert=True (so output is emitted) but INFO severity
        alert, _, _ = MOD.build_report([], [], [self._resolved()], None)
        assert alert is True


# ── write_github_output ────────────────────────────────────────────────────────


class TestWriteGithubOutput:
    def test_no_env_var_is_noop(self) -> None:
        saved = os.environ.pop("GITHUB_OUTPUT", None)
        try:
            # Must not raise
            MOD.write_github_output(True, "CRITICAL", "test report")
        finally:
            if saved is not None:
                os.environ["GITHUB_OUTPUT"] = saved

    def test_writes_to_output_file(self, tmp_path: Path) -> None:
        out_file = tmp_path / "output.txt"
        os.environ["GITHUB_OUTPUT"] = str(out_file)
        try:
            MOD.write_github_output(True, "CRITICAL", "my report line")
        finally:
            del os.environ["GITHUB_OUTPUT"]
        content = out_file.read_text()
        assert "alert=true" in content
        assert "severity=CRITICAL" in content
        assert "my report line" in content

    def test_false_alert_written(self, tmp_path: Path) -> None:
        out_file = tmp_path / "output2.txt"
        os.environ["GITHUB_OUTPUT"] = str(out_file)
        try:
            MOD.write_github_output(False, "INFO", "all clear")
        finally:
            del os.environ["GITHUB_OUTPUT"]
        content = out_file.read_text()
        assert "alert=false" in content
        assert "severity=INFO" in content

    def test_multiline_report_uses_heredoc_delimiters(self, tmp_path: Path) -> None:
        out_file = tmp_path / "output3.txt"
        os.environ["GITHUB_OUTPUT"] = str(out_file)
        try:
            MOD.write_github_output(True, "CRITICAL", "line1\nline2")
        finally:
            del os.environ["GITHUB_OUTPUT"]
        content = out_file.read_text()
        assert "report<<__RPT__" in content
        assert "__RPT__" in content


# ── detect_transitions ─────────────────────────────────────────────────────────


class TestDetectTransitions:
    def _run(
        self,
        conclusion: str,
        created: str,
        status: str = "completed",
        sha: str = "abc123",
    ) -> dict:
        return {
            "workflowName": "quality-gates-v2",
            "conclusion": conclusion,
            "status": status,
            "createdAt": created,
            "url": "https://github.com/run/1",
            "databaseId": 1,
            "event": "push",
            "headSha": sha,
        }

    def test_success_to_failure_is_failing_transition(self) -> None:
        runs = [
            self._run("failure", RECENT_TS),
            self._run("success", OLD_TS),
        ]
        with (
            patch.object(MOD, "gh_json", return_value=runs),
            patch.object(MOD, "classify_pusher", return_value=("bot", "automation")),
        ):
            result = MOD.detect_transitions("mtds", "main", 25, NOW, 2.0)
        assert len(result) == 1
        assert result[0]["kind"] == "failing"
        assert result[0]["repo"] == "mtds"

    def test_failure_to_success_is_recovered_transition(self) -> None:
        runs = [
            self._run("success", RECENT_TS),
            self._run("failure", OLD_TS),
        ]
        with (
            patch.object(MOD, "gh_json", return_value=runs),
            patch.object(MOD, "classify_pusher", return_value=("ikenna", "human")),
        ):
            result = MOD.detect_transitions("mtds", "main", 25, NOW, 2.0)
        assert len(result) == 1
        assert result[0]["kind"] == "recovered"

    def test_steady_failure_no_transition(self) -> None:
        runs = [
            self._run("failure", RECENT_TS),
            self._run("failure", OLD_TS),
        ]
        with (
            patch.object(MOD, "gh_json", return_value=runs),
            patch.object(MOD, "classify_pusher", return_value=("bot", "automation")),
        ):
            result = MOD.detect_transitions("mtds", "main", 25, NOW, 2.0)
        assert result == []

    def test_steady_success_no_transition(self) -> None:
        runs = [
            self._run("success", RECENT_TS),
            self._run("success", OLD_TS),
        ]
        with patch.object(MOD, "gh_json", return_value=runs):
            result = MOD.detect_transitions("mtds", "main", 25, NOW, 2.0)
        assert result == []

    def test_gh_json_non_list_returns_empty(self) -> None:
        with patch.object(MOD, "gh_json", return_value=None):
            result = MOD.detect_transitions("mtds", "main", 25, NOW, 2.0)
        assert result == []

    def test_in_flight_run_is_skipped(self) -> None:
        # Only one in-flight run → no completed runs → no transitions
        runs = [self._run("", RECENT_TS, status="in_progress")]
        with patch.object(MOD, "gh_json", return_value=runs):
            result = MOD.detect_transitions("mtds", "main", 25, NOW, 2.0)
        assert result == []

    def test_stale_latest_run_no_transition(self) -> None:
        # Latest run is 4 hours old; fresh_hours=2 → stale
        stale_ts = "2026-06-10T07:50:00Z"
        runs = [
            self._run("failure", stale_ts),
            self._run("success", OLD_TS),
        ]
        with patch.object(MOD, "gh_json", return_value=runs):
            result = MOD.detect_transitions("mtds", "main", 25, NOW, 2.0)
        assert result == []

    def test_single_run_no_prev_no_transition_on_success(self) -> None:
        runs = [self._run("success", RECENT_TS)]
        with patch.object(MOD, "gh_json", return_value=runs):
            result = MOD.detect_transitions("mtds", "main", 25, NOW, 2.0)
        assert result == []

    def test_single_failing_run_no_prev_triggers_transition(self) -> None:
        # With no previous run, prev_failed=False → success→failure flip (prev was None)
        runs = [self._run("failure", RECENT_TS)]
        with (
            patch.object(MOD, "gh_json", return_value=runs),
            patch.object(MOD, "classify_pusher", return_value=("bot", "automation")),
        ):
            result = MOD.detect_transitions("mtds", "main", 25, NOW, 2.0)
        assert len(result) == 1
        assert result[0]["kind"] == "failing"


# ── detect_stuck_prs ───────────────────────────────────────────────────────────


class TestDetectStuckPrs:
    def _pr(
        self,
        state: str = "BLOCKED",
        is_draft: bool = False,
        auto_merge: bool = True,
        head: str = "live-defi-rollout",
        age_minutes: int = 40,
        rollup: list | None = None,
        commits: list | None = None,
    ) -> dict:
        created = (NOW - _dt.timedelta(minutes=age_minutes)).strftime("%Y-%m-%dT%H:%M:%SZ")
        return {
            "number": 99,
            "title": "test PR",
            "mergeStateStatus": state,
            "isDraft": is_draft,
            "autoMergeRequest": {} if auto_merge else None,
            "createdAt": created,
            "headRefName": head,
            "url": "https://github.com/pr/99",
            "statusCheckRollup": rollup if rollup is not None else [],
            "commits": commits if commits is not None else [],
        }

    def test_blocked_promotion_pr_is_stuck(self) -> None:
        # gh_json called for each base (staging, main) — return PR for first, [] for second
        with patch.object(MOD, "gh_json", side_effect=[[self._pr()], []]):
            result = MOD.detect_stuck_prs("mtds", 30, NOW)
        assert len(result) == 1
        assert result[0]["state"] == "BLOCKED"

    def test_clean_state_pr_not_stuck(self) -> None:
        with patch.object(MOD, "gh_json", side_effect=[[self._pr(state="CLEAN")], []]):
            result = MOD.detect_stuck_prs("mtds", 30, NOW)
        assert result == []

    def test_draft_pr_skipped(self) -> None:
        with patch.object(MOD, "gh_json", side_effect=[[self._pr(is_draft=True)], []]):
            result = MOD.detect_stuck_prs("mtds", 30, NOW)
        assert result == []

    def test_too_recent_not_stuck(self) -> None:
        # PR only 10 min old; stuck_minutes=30
        with patch.object(MOD, "gh_json", side_effect=[[self._pr(age_minutes=10)], []]):
            result = MOD.detect_stuck_prs("mtds", 30, NOW)
        assert result == []

    def test_non_promotion_head_no_auto_merge_skipped(self) -> None:
        pr = self._pr(auto_merge=False, head="feature/my-feat")
        with patch.object(MOD, "gh_json", side_effect=[[pr], []]):
            result = MOD.detect_stuck_prs("mtds", 30, NOW)
        assert result == []

    def test_promotion_head_without_auto_merge_still_stuck(self) -> None:
        # staging head is in _PROMOTION_HEADS → qualifies even without auto-merge
        pr = self._pr(auto_merge=False, head="staging", state="BLOCKED")
        with patch.object(MOD, "gh_json", side_effect=[[pr], []]):
            result = MOD.detect_stuck_prs("mtds", 30, NOW)
        assert len(result) == 1

    def test_failed_check_detected_in_rollup(self) -> None:
        rollup = [{"name": "quality-gates-v2", "conclusion": "FAILURE", "state": "FAILURE"}]
        pr = self._pr(rollup=rollup)
        with patch.object(MOD, "gh_json", side_effect=[[pr], []]):
            result = MOD.detect_stuck_prs("mtds", 30, NOW)
        assert result[0]["failed_check"] is True

    def test_v2_present_in_rollup_detected(self) -> None:
        rollup = [{"name": "quality-gates-v2", "conclusion": "SUCCESS", "state": "SUCCESS"}]
        pr = self._pr(rollup=rollup)
        with patch.object(MOD, "gh_json", side_effect=[[pr], []]):
            result = MOD.detect_stuck_prs("mtds", 30, NOW)
        assert result[0]["v2_present"] is True

    def test_head_commit_message_extracted(self) -> None:
        commits = [
            {"messageHeadline": "chore: bump deps", "messageBody": "", "oid": "dead1234"},
        ]
        pr = self._pr(commits=commits)
        with patch.object(MOD, "gh_json", side_effect=[[pr], []]):
            result = MOD.detect_stuck_prs("mtds", 30, NOW)
        assert result[0]["head_message"] == "chore: bump deps"
        assert result[0]["head_oid"] == "dead1234"

    def test_gh_json_none_skips_base(self) -> None:
        with patch.object(MOD, "gh_json", side_effect=[None, None]):
            result = MOD.detect_stuck_prs("mtds", 30, NOW)
        assert result == []

    def test_result_includes_all_fields(self) -> None:
        pr = self._pr()
        with patch.object(MOD, "gh_json", side_effect=[[pr], []]):
            result = MOD.detect_stuck_prs("mtds", 30, NOW)
        r = result[0]
        for field in ("repo", "base", "number", "state", "auto_merge", "age_min", "url", "failed_check", "v2_present"):
            assert field in r, f"missing field: {field}"


# ── detect_resolved_prs ────────────────────────────────────────────────────────


class TestDetectResolvedPrs:
    def _pr(self, head: str = "live-defi-rollout", age_hours: float = 0.2, merged: bool = True) -> dict:
        closed = (NOW - _dt.timedelta(hours=age_hours)).strftime("%Y-%m-%dT%H:%M:%SZ")
        return {
            "number": 5,
            "title": "merge PR",
            "state": "closed",
            "mergedAt": closed if merged else None,
            "closedAt": closed,
            "headRefName": head,
            "url": "https://github.com/pr/5",
        }

    def test_recently_merged_promotion_pr_resolved(self) -> None:
        with patch.object(MOD, "gh_json", side_effect=[[self._pr()], []]):
            result = MOD.detect_resolved_prs("mtds", 0.5, NOW)
        assert len(result) == 1
        assert result[0]["merged"] is True

    def test_non_promotion_head_excluded(self) -> None:
        with patch.object(MOD, "gh_json", side_effect=[[self._pr(head="feature/x")], []]):
            result = MOD.detect_resolved_prs("mtds", 0.5, NOW)
        assert result == []

    def test_too_old_excluded(self) -> None:
        # PR closed 2 hours ago; resolved_hours=0.5
        with patch.object(MOD, "gh_json", side_effect=[[self._pr(age_hours=2.0)], []]):
            result = MOD.detect_resolved_prs("mtds", 0.5, NOW)
        assert result == []

    def test_closed_not_merged(self) -> None:
        with patch.object(MOD, "gh_json", side_effect=[[self._pr(merged=False)], []]):
            result = MOD.detect_resolved_prs("mtds", 0.5, NOW)
        assert len(result) == 1
        assert result[0]["merged"] is False

    def test_staging_head_also_qualifies(self) -> None:
        pr = self._pr(head="staging")
        with patch.object(MOD, "gh_json", side_effect=[[pr], []]):
            result = MOD.detect_resolved_prs("mtds", 0.5, NOW)
        assert len(result) == 1

    def test_gh_json_none_skips(self) -> None:
        with patch.object(MOD, "gh_json", side_effect=[None, None]):
            result = MOD.detect_resolved_prs("mtds", 0.5, NOW)
        assert result == []

    def test_missing_closed_at_skipped(self) -> None:
        pr = self._pr()
        pr["closedAt"] = None
        with patch.object(MOD, "gh_json", side_effect=[[pr], []]):
            result = MOD.detect_resolved_prs("mtds", 0.5, NOW)
        assert result == []


# ── _run_is_billing_block ──────────────────────────────────────────────────────


class TestRunIsBillingBlock:
    def _jobs_resp(self, steps: list | None = None, job_id: int = 101) -> dict:
        return {"jobs": [{"id": job_id, "steps": steps if steps is not None else [], "conclusion": "failure"}]}

    def test_zero_step_job_with_billing_annotation(self) -> None:
        anns = [{"message": "your spending limit needs to be increased"}]

        def _gh(args: list[str]) -> dict | list | None:
            if "jobs" in " ".join(args):
                return self._jobs_resp()
            return anns

        with patch.object(MOD, "gh_json", side_effect=_gh):
            assert MOD._run_is_billing_block("mtds", 12345) is True

    def test_job_with_steps_not_billing(self) -> None:
        with patch.object(MOD, "gh_json", return_value=self._jobs_resp(steps=[{"name": "s1"}])):
            assert MOD._run_is_billing_block("mtds", 12345) is False

    def test_gh_json_non_dict_returns_false(self) -> None:
        with patch.object(MOD, "gh_json", return_value=None):
            assert MOD._run_is_billing_block("mtds", 12345) is False

    def test_jobs_key_not_list_returns_false(self) -> None:
        with patch.object(MOD, "gh_json", return_value={"jobs": "bad"}):
            assert MOD._run_is_billing_block("mtds", 12345) is False

    def test_empty_job_list_returns_false(self) -> None:
        with patch.object(MOD, "gh_json", return_value={"jobs": []}):
            assert MOD._run_is_billing_block("mtds", 12345) is False

    def test_structural_billing_when_annotations_unreadable(self) -> None:
        # All jobs have 0 steps, annotations return None (fine-grained PAT 403)
        # → structural billing signature (not annotations_readable + all zero-step)
        def _gh(args: list[str]) -> dict | list | None:
            if "jobs" in " ".join(args):
                return {
                    "jobs": [
                        {"id": 1, "steps": [], "conclusion": "failure"},
                        {"id": 2, "steps": [], "conclusion": "failure"},
                    ]
                }
            return None  # annotations unreadable

        with patch.object(MOD, "gh_json", side_effect=_gh):
            assert MOD._run_is_billing_block("mtds", 12345) is True

    def test_non_billing_annotation_returns_false(self) -> None:
        anns = [{"message": "Process completed with exit code 1"}]

        def _gh(args: list[str]) -> dict | list | None:
            if "jobs" in " ".join(args):
                return self._jobs_resp()
            return anns

        with patch.object(MOD, "gh_json", side_effect=_gh):
            assert MOD._run_is_billing_block("mtds", 12345) is False


# ── detect_billing_block ───────────────────────────────────────────────────────


class TestDetectBillingBlock:
    def _run(self, conclusion: str = "failure", status: str = "completed") -> dict:
        return {
            "databaseId": 42,
            "conclusion": conclusion,
            "status": status,
            "createdAt": RECENT_TS,
            "url": "https://github.com/run/42",
            "workflowName": "quality-gates-v2",
        }

    def test_billing_block_found(self) -> None:
        with (
            patch.object(MOD, "gh_json", return_value=[self._run()]),
            patch.object(MOD, "_run_is_billing_block", return_value=True),
        ):
            result = MOD.detect_billing_block(["mtds"], NOW, 2.0)
        assert result is not None
        assert result["repo"] == "mtds"
        assert result["workflow"] == "quality-gates-v2"

    def test_no_billing_block_returns_none(self) -> None:
        with (
            patch.object(MOD, "gh_json", return_value=[self._run()]),
            patch.object(MOD, "_run_is_billing_block", return_value=False),
        ):
            result = MOD.detect_billing_block(["mtds"], NOW, 2.0)
        assert result is None

    def test_successful_run_not_checked(self) -> None:
        with (
            patch.object(MOD, "gh_json", return_value=[self._run(conclusion="success")]),
            patch.object(MOD, "_run_is_billing_block") as mock_billing,
        ):
            result = MOD.detect_billing_block(["mtds"], NOW, 2.0)
        assert result is None
        mock_billing.assert_not_called()

    def test_in_flight_run_not_checked(self) -> None:
        with (
            patch.object(MOD, "gh_json", return_value=[self._run(status="in_progress")]),
            patch.object(MOD, "_run_is_billing_block") as mock_billing,
        ):
            result = MOD.detect_billing_block(["mtds"], NOW, 2.0)
        assert result is None
        mock_billing.assert_not_called()

    def test_stale_run_not_checked(self) -> None:
        stale_run = {
            "databaseId": 42,
            "conclusion": "failure",
            "status": "completed",
            "createdAt": OLD_TS,  # 48h ago → stale with fresh_hours=2
            "url": "u",
            "workflowName": "quality-gates-v2",
        }
        with (
            patch.object(MOD, "gh_json", return_value=[stale_run]),
            patch.object(MOD, "_run_is_billing_block") as mock_billing,
        ):
            result = MOD.detect_billing_block(["mtds"], NOW, 2.0)
        assert result is None
        mock_billing.assert_not_called()

    def test_gh_json_none_skips_repo(self) -> None:
        with patch.object(MOD, "gh_json", return_value=None):
            result = MOD.detect_billing_block(["mtds"], NOW, 2.0)
        assert result is None

    def test_short_circuits_on_first_match(self) -> None:
        # Two repos; first one is a billing block → should return without checking second
        with (
            patch.object(MOD, "gh_json", return_value=[self._run()]),
            patch.object(MOD, "_run_is_billing_block", return_value=True) as mock_billing,
        ):
            result = MOD.detect_billing_block(["mtds", "execution-service"], NOW, 2.0)
        assert result is not None
        # _run_is_billing_block called exactly ONCE (first repo short-circuits)
        assert mock_billing.call_count == 1
