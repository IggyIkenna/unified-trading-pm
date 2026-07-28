"""Unit tests for write_version_coherence_verdicts.py — the assert_version_coherence.py --json ->
verdict_store CAS-write driver wired into version-coherence-check.yml.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

_DRIVER = Path(__file__).resolve().parents[2] / "scripts" / "cicd" / "write_version_coherence_verdicts.py"
_spec = importlib.util.spec_from_file_location("write_version_coherence_verdicts", _DRIVER)
assert _spec and _spec.loader
_mod = importlib.util.module_from_spec(_spec)
sys.modules["write_version_coherence_verdicts"] = _mod
_spec.loader.exec_module(_mod)

run_checker = _mod.run_checker
write_verdicts = _mod.write_verdicts


class TestRunChecker:
    def test_parses_repos_from_json_stdout(self):
        stdout = '{"repos": {"repo-a": {"verdict": "OK", "reasons": []}}}'
        fake_result = MagicMock(returncode=0, stdout=stdout, stderr="")
        with patch.object(subprocess, "run", return_value=fake_result) as run_mock:
            repos = run_checker(python_executable="python3")
        assert repos == {"repo-a": {"verdict": "OK", "reasons": []}}
        # --warn-only default true, --json always present
        called_args = run_mock.call_args[0][0]
        assert "--json" in called_args
        assert "--warn-only" in called_args

    def test_warn_only_false_omits_flag(self):
        fake_result = MagicMock(returncode=0, stdout='{"repos": {}}', stderr="")
        with patch.object(subprocess, "run", return_value=fake_result) as run_mock:
            run_checker(warn_only=False, python_executable="python3")
        called_args = run_mock.call_args[0][0]
        assert "--warn-only" not in called_args

    def test_exit_code_1_is_a_valid_violations_found_result(self):
        """--warn-only forces exit 0 always, but a non-warn-only run legitimately exits 1 on
        violations — the driver must not treat that as a crash."""
        stdout = '{"repos": {"repo-a": {"verdict": "VERSION_SPLIT", "reasons": ["x"]}}}'
        fake_result = MagicMock(returncode=1, stdout=stdout, stderr="")
        with patch.object(subprocess, "run", return_value=fake_result):
            repos = run_checker(warn_only=False, python_executable="python3")
        assert repos["repo-a"]["verdict"] == "VERSION_SPLIT"

    def test_unexpected_exit_code_raises(self):
        fake_result = MagicMock(returncode=2, stdout="", stderr="boom")
        with patch.object(subprocess, "run", return_value=fake_result):
            try:
                run_checker(python_executable="python3")
            except RuntimeError as err:
                assert "boom" in str(err)
            else:
                raise AssertionError("expected RuntimeError")


class TestWriteVerdicts:
    def test_writes_every_repo_and_counts_success(self):
        calls: list[tuple[str, str, str]] = []

        def fake_set_verdict(collection, key, verdict, **kwargs):
            calls.append((collection, key, verdict))
            return None, verdict

        with patch.object(_mod.verdict_store, "set_verdict", side_effect=fake_set_verdict):
            written, errors = write_verdicts(
                {"repo-a": {"verdict": "OK", "reasons": []}, "repo-b": {"verdict": "VERSION_SPLIT", "reasons": ["x"]}},
                checked_at="2026-07-27T10:00:00Z",
            )
        assert written == 2
        assert errors == 0
        assert ("version_coherence_verdicts", "repo-a", "OK") in calls
        assert ("version_coherence_verdicts", "repo-b", "VERSION_SPLIT") in calls

    def test_one_repo_failure_does_not_block_the_rest(self):
        """Shard-level isolation: a single Firestore write failure must not blank the other repos'
        writes (mirrors the workspace-wide no-raise-in-per-shard-loop rule)."""

        def fake_set_verdict(collection, key, verdict, **kwargs):
            if key == "repo-bad":
                raise RuntimeError("boom")
            return None, verdict

        with patch.object(_mod.verdict_store, "set_verdict", side_effect=fake_set_verdict):
            written, errors = write_verdicts(
                {
                    "repo-bad": {"verdict": "OK", "reasons": []},
                    "repo-good": {"verdict": "OK", "reasons": []},
                },
                checked_at="2026-07-27T10:00:00Z",
            )
        assert written == 1
        assert errors == 1

    def test_missing_verdict_field_defaults_to_ok(self):
        calls: list[str] = []

        def fake_set_verdict(collection, key, verdict, **kwargs):
            calls.append(verdict)
            return None, verdict

        with patch.object(_mod.verdict_store, "set_verdict", side_effect=fake_set_verdict):
            write_verdicts({"repo-a": {}}, checked_at="2026-07-27T10:00:00Z")
        assert calls == ["OK"]

    def test_project_id_forwarded(self):
        captured: dict[str, object] = {}

        def fake_set_verdict(collection, key, verdict, **kwargs):
            captured.update(kwargs)
            return None, verdict

        with patch.object(_mod.verdict_store, "set_verdict", side_effect=fake_set_verdict):
            write_verdicts({"repo-a": {"verdict": "OK"}}, checked_at="2026-07-27T10:00:00Z", project_id="my-proj")
        assert captured["project_id"] == "my-proj"
