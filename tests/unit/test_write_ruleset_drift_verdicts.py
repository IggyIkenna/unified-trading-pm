"""Unit tests for write_ruleset_drift_verdicts.py — the
verify_branch_protection_check_names.py --json -> verdict_store CAS-write driver wired into
ruleset-drift-alert.yml.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

_DRIVER = Path(__file__).resolve().parents[2] / "scripts" / "cicd" / "write_ruleset_drift_verdicts.py"
_spec = importlib.util.spec_from_file_location("write_ruleset_drift_verdicts", _DRIVER)
assert _spec and _spec.loader
_mod = importlib.util.module_from_spec(_spec)
sys.modules["write_ruleset_drift_verdicts"] = _mod
_spec.loader.exec_module(_mod)

run_checker = _mod.run_checker
derive_verdict = _mod.derive_verdict
write_verdicts = _mod.write_verdicts


class TestRunChecker:
    def test_parses_report_list_from_json_stdout(self):
        stdout = (
            '[{"repo": "repo-a", "default_branch": "main", "default_branch_ok": true, '
            '"main_required": ["Quality Gates (repo-a) / quality-gates-v2"], "main_ok": true, '
            '"staging_required": null, "staging_ok": true, "drift": false}]'
        )
        fake_result = MagicMock(returncode=0, stdout=stdout, stderr="")
        with patch.object(subprocess, "run", return_value=fake_result) as run_mock:
            reports = run_checker(python_executable="python3")
        assert reports[0]["repo"] == "repo-a"
        assert reports[0]["drift"] is False
        called_args = run_mock.call_args[0][0]
        assert "--json" in called_args

    def test_exit_code_1_is_a_valid_drift_found_result(self):
        """The checker exits 1 when any repo has drift — the driver must not treat that as a
        crash, only an unexpected exit code."""
        stdout = (
            '[{"repo": "repo-a", "default_branch": "main", "default_branch_ok": true, '
            '"main_required": [], "main_ok": false, "staging_required": null, "staging_ok": true, '
            '"drift": true}]'
        )
        fake_result = MagicMock(returncode=1, stdout=stdout, stderr="")
        with patch.object(subprocess, "run", return_value=fake_result):
            reports = run_checker(python_executable="python3")
        assert reports[0]["drift"] is True

    def test_unexpected_exit_code_raises(self):
        fake_result = MagicMock(returncode=2, stdout="", stderr="boom")
        with patch.object(subprocess, "run", return_value=fake_result):
            try:
                run_checker(python_executable="python3")
            except RuntimeError as err:
                assert "boom" in str(err)
            else:
                raise AssertionError("expected RuntimeError")

    def test_non_list_payload_raises(self):
        """A schema-drifted checker output (e.g. a dict) must fail loud, never silently write zero
        verdicts."""
        fake_result = MagicMock(returncode=0, stdout='{"repos": {}}', stderr="")
        with patch.object(subprocess, "run", return_value=fake_result):
            try:
                run_checker(python_executable="python3")
            except RuntimeError as err:
                assert "JSON list" in str(err)
            else:
                raise AssertionError("expected RuntimeError")


class TestDeriveVerdict:
    def test_clean_report_has_no_reasons(self):
        verdict, reasons = derive_verdict(
            {
                "repo": "a",
                "default_branch": "main",
                "default_branch_ok": True,
                "main_required": ["x"],
                "main_ok": True,
                "staging_required": None,
                "staging_ok": True,
                "drift": False,
            }
        )
        assert verdict == "CLEAN"
        assert reasons == []

    def test_default_branch_drift_yields_drift_verdict_and_reason(self):
        verdict, reasons = derive_verdict(
            {
                "repo": "a",
                "default_branch": "live-defi-rollout",
                "default_branch_ok": False,
                "main_required": None,
                "main_ok": True,
                "staging_required": None,
                "staging_ok": True,
                "drift": True,
            }
        )
        assert verdict == "DRIFT"
        assert any("default_branch" in r for r in reasons)

    def test_main_context_drift_yields_drift_verdict_and_reason(self):
        verdict, reasons = derive_verdict(
            {
                "repo": "a",
                "default_branch": "main",
                "default_branch_ok": True,
                "main_required": ["stale-context"],
                "main_ok": False,
                "staging_required": None,
                "staging_ok": True,
                "drift": True,
            }
        )
        assert verdict == "DRIFT"
        assert any("main required-contexts" in r for r in reasons)

    def test_staging_context_drift_yields_drift_verdict_and_reason(self):
        verdict, reasons = derive_verdict(
            {
                "repo": "a",
                "default_branch": "main",
                "default_branch_ok": True,
                "main_required": ["x"],
                "main_ok": True,
                "staging_required": ["stale-context"],
                "staging_ok": False,
                "drift": True,
            }
        )
        assert verdict == "DRIFT"
        assert any("staging required-contexts" in r for r in reasons)


class TestWriteVerdicts:
    def test_writes_every_repo_and_counts_success(self):
        calls: list[tuple[str, str, str]] = []

        def fake_set_verdict(collection, key, verdict, **kwargs):
            calls.append((collection, key, verdict))
            return None, verdict

        reports = [
            {"repo": "repo-a", "default_branch_ok": True, "main_ok": True, "staging_ok": True, "drift": False},
            {"repo": "repo-b", "default_branch_ok": False, "main_ok": True, "staging_ok": True, "drift": True},
        ]
        with patch.object(_mod.verdict_store, "set_verdict", side_effect=fake_set_verdict):
            written, errors = write_verdicts(reports, checked_at="2026-08-17T10:00:00Z")
        assert written == 2
        assert errors == 0
        assert ("ruleset_drift_verdicts", "repo-a", "CLEAN") in calls
        assert ("ruleset_drift_verdicts", "repo-b", "DRIFT") in calls

    def test_one_repo_failure_does_not_block_the_rest(self):
        """Shard-level isolation: a single Firestore write failure must not blank the other repos'
        writes (mirrors the workspace-wide no-raise-in-per-shard-loop rule)."""

        def fake_set_verdict(collection, key, verdict, **kwargs):
            if key == "repo-bad":
                raise RuntimeError("boom")
            return None, verdict

        reports = [
            {"repo": "repo-bad", "default_branch_ok": True, "main_ok": True, "staging_ok": True, "drift": False},
            {"repo": "repo-good", "default_branch_ok": True, "main_ok": True, "staging_ok": True, "drift": False},
        ]
        with patch.object(_mod.verdict_store, "set_verdict", side_effect=fake_set_verdict):
            written, errors = write_verdicts(reports, checked_at="2026-08-17T10:00:00Z")
        assert written == 1
        assert errors == 1

    def test_missing_repo_field_is_skipped(self):
        calls: list[str] = []

        def fake_set_verdict(collection, key, verdict, **kwargs):
            calls.append(key)
            return None, verdict

        with patch.object(_mod.verdict_store, "set_verdict", side_effect=fake_set_verdict):
            written, errors = write_verdicts(
                [{"default_branch_ok": True, "main_ok": True, "staging_ok": True, "drift": False}],
                checked_at="2026-08-17T10:00:00Z",
            )
        assert calls == []
        assert written == 0
        assert errors == 0

    def test_project_id_forwarded(self):
        captured: dict[str, object] = {}

        def fake_set_verdict(collection, key, verdict, **kwargs):
            captured.update(kwargs)
            return None, verdict

        with patch.object(_mod.verdict_store, "set_verdict", side_effect=fake_set_verdict):
            write_verdicts(
                [{"repo": "repo-a", "default_branch_ok": True, "main_ok": True, "staging_ok": True, "drift": False}],
                checked_at="2026-08-17T10:00:00Z",
                project_id="my-proj",
            )
        assert captured["project_id"] == "my-proj"
