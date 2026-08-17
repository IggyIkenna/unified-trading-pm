"""Unit tests for write_template_drift_verdicts.py — the detect_template_drift.py --json ->
verdict_store CAS-write driver wired into template-drift-daily-check.{sh,service,timer}.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

_DRIVER = Path(__file__).resolve().parents[2] / "scripts" / "cicd" / "write_template_drift_verdicts.py"
_spec = importlib.util.spec_from_file_location("write_template_drift_verdicts", _DRIVER)
assert _spec and _spec.loader
_mod = importlib.util.module_from_spec(_spec)
sys.modules["write_template_drift_verdicts"] = _mod
_spec.loader.exec_module(_mod)

run_checker = _mod.run_checker
derive_verdict = _mod.derive_verdict
write_verdicts = _mod.write_verdicts


class TestRunChecker:
    def test_parses_report_list_from_json_stdout(self):
        stdout = '[{"repo": "repo-a", "type": "service", "clean": true, "items": []}]'
        fake_result = MagicMock(returncode=0, stdout=stdout, stderr="")
        with patch.object(subprocess, "run", return_value=fake_result) as run_mock:
            reports = run_checker(python_executable="python3")
        assert reports == [{"repo": "repo-a", "type": "service", "clean": True, "items": []}]
        called_args = run_mock.call_args[0][0]
        assert "--json" in called_args

    def test_exit_code_1_is_a_valid_errors_found_result(self):
        """The checker exits 1 when any repo has drift errors — the driver must not treat that as
        a crash, only an unexpected exit code."""
        stdout = (
            '[{"repo": "repo-a", "type": "service", "clean": false, '
            '"items": [{"severity": "error", "check": "x", "message": "y"}]}]'
        )
        fake_result = MagicMock(returncode=1, stdout=stdout, stderr="")
        with patch.object(subprocess, "run", return_value=fake_result):
            reports = run_checker(python_executable="python3")
        assert reports[0]["clean"] is False

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
        """A schema-drifted checker output (e.g. a dict, matching version-coherence's shape by
        mistake) must fail loud, never silently write zero verdicts."""
        fake_result = MagicMock(returncode=0, stdout='{"repos": {}}', stderr="")
        with patch.object(subprocess, "run", return_value=fake_result):
            try:
                run_checker(python_executable="python3")
            except RuntimeError as err:
                assert "JSON list" in str(err)
            else:
                raise AssertionError("expected RuntimeError")


class TestDeriveVerdict:
    def test_clean_report_has_no_items(self):
        verdict, reasons = derive_verdict({"repo": "a", "clean": True, "items": []})
        assert verdict == "CLEAN"
        assert reasons == []

    def test_warn_only_items_yield_warn(self):
        verdict, reasons = derive_verdict(
            {
                "repo": "a",
                "clean": False,
                "items": [{"severity": "warn", "check": "ssot-comment", "message": "missing"}],
            }
        )
        assert verdict == "WARN"
        assert reasons == ["[ssot-comment] missing"]

    def test_any_error_item_yields_error_even_with_warnings_present(self):
        verdict, reasons = derive_verdict(
            {
                "repo": "a",
                "clean": False,
                "items": [
                    {"severity": "warn", "check": "ssot-comment", "message": "missing"},
                    {"severity": "error", "check": "missing-var-X", "message": "X not set"},
                ],
            }
        )
        assert verdict == "ERROR"
        assert len(reasons) == 2


class TestWriteVerdicts:
    def test_writes_every_repo_and_counts_success(self):
        calls: list[tuple[str, str, str]] = []

        def fake_set_verdict(collection, key, verdict, **kwargs):
            calls.append((collection, key, verdict))
            return None, verdict

        reports = [
            {"repo": "repo-a", "clean": True, "items": []},
            {"repo": "repo-b", "clean": False, "items": [{"severity": "error", "check": "x", "message": "y"}]},
        ]
        with patch.object(_mod.verdict_store, "set_verdict", side_effect=fake_set_verdict):
            written, errors = write_verdicts(reports, checked_at="2026-08-17T10:00:00Z")
        assert written == 2
        assert errors == 0
        assert ("template_drift_verdicts", "repo-a", "CLEAN") in calls
        assert ("template_drift_verdicts", "repo-b", "ERROR") in calls

    def test_one_repo_failure_does_not_block_the_rest(self):
        """Shard-level isolation: a single Firestore write failure must not blank the other repos'
        writes (mirrors the workspace-wide no-raise-in-per-shard-loop rule)."""

        def fake_set_verdict(collection, key, verdict, **kwargs):
            if key == "repo-bad":
                raise RuntimeError("boom")
            return None, verdict

        reports = [
            {"repo": "repo-bad", "clean": True, "items": []},
            {"repo": "repo-good", "clean": True, "items": []},
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
            written, errors = write_verdicts([{"clean": True, "items": []}], checked_at="2026-08-17T10:00:00Z")
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
                [{"repo": "repo-a", "clean": True, "items": []}],
                checked_at="2026-08-17T10:00:00Z",
                project_id="my-proj",
            )
        assert captured["project_id"] == "my-proj"
