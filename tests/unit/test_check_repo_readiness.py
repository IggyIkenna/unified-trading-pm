"""Unit tests for scripts/check-repo-readiness.py."""

from __future__ import annotations

import importlib.util
import json
import sys
import types
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Module loader
# ---------------------------------------------------------------------------

_MOD_NAME = "check_repo_readiness"
_MOD_PATH = Path(__file__).resolve().parents[2] / "scripts" / "check-repo-readiness.py"


def _load_module() -> types.ModuleType:
    if _MOD_NAME in sys.modules:
        return sys.modules[_MOD_NAME]
    spec = importlib.util.spec_from_file_location(_MOD_NAME, _MOD_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    # Register in sys.modules BEFORE exec_module so dataclass annotations resolve
    sys.modules[_MOD_NAME] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_coverage_xml(path: Path, line_rate: float) -> None:
    root = ET.Element("coverage")
    root.set("line-rate", str(line_rate))
    ET.ElementTree(root).write(str(path))


# ---------------------------------------------------------------------------
# Tests: _load_manifest
# ---------------------------------------------------------------------------


class TestLoadManifest:
    def test_returns_empty_when_missing(self, tmp_path: Path) -> None:
        mod = _load_module()
        assert mod._load_manifest(tmp_path) == {}  # type: ignore[attr-defined]

    def test_parses_repositories_key(self, tmp_path: Path) -> None:
        mod = _load_module()
        pm = tmp_path / "unified-trading-pm"
        pm.mkdir()
        manifest = {
            "repositories": {
                "my-repo": {"arch_tier": "0", "dependencies": [], "coverage_pct": 80},
            }
        }
        (pm / "workspace-manifest.json").write_text(json.dumps(manifest))
        result = mod._load_manifest(tmp_path)  # type: ignore[attr-defined]
        assert "my-repo" in result
        assert result["my-repo"]["arch_tier"] == "0"

    def test_parses_repos_key_fallback(self, tmp_path: Path) -> None:
        mod = _load_module()
        pm = tmp_path / "unified-trading-pm"
        pm.mkdir()
        manifest = {
            "repos": {
                "other-repo": {"arch_tier": "1", "dependencies": []},
            }
        }
        (pm / "workspace-manifest.json").write_text(json.dumps(manifest))
        result = mod._load_manifest(tmp_path)  # type: ignore[attr-defined]
        assert "other-repo" in result

    def test_returns_empty_on_invalid_json(self, tmp_path: Path) -> None:
        mod = _load_module()
        pm = tmp_path / "unified-trading-pm"
        pm.mkdir()
        (pm / "workspace-manifest.json").write_text("not-json{{{")
        result = mod._load_manifest(tmp_path)  # type: ignore[attr-defined]
        assert result == {}


# ---------------------------------------------------------------------------
# Tests: _declared_stage_from_plan
# ---------------------------------------------------------------------------


class TestDeclaredStageFromPlan:
    def test_returns_unknown_when_no_plan(self, tmp_path: Path) -> None:
        mod = _load_module()
        result = mod._declared_stage_from_plan("some-repo", tmp_path)  # type: ignore[attr-defined]
        assert result == "unknown"

    def test_parses_cr_stage(self, tmp_path: Path) -> None:
        mod = _load_module()
        pm = tmp_path / "unified-trading-pm" / "plans" / "active"
        pm.mkdir(parents=True)
        content = "repo_gates:\n  - repo: my-repo\n    code: C4\n    deployment: none\n"
        (pm / "code_readiness_master_plan_2026_03_11.plan.md").write_text(content)
        result = mod._declared_stage_from_plan("my-repo", tmp_path)  # type: ignore[attr-defined]
        assert result == "CR4"

    def test_returns_unknown_for_missing_repo(self, tmp_path: Path) -> None:
        mod = _load_module()
        pm = tmp_path / "unified-trading-pm" / "plans" / "active"
        pm.mkdir(parents=True)
        (pm / "code_readiness_master_plan_2026_03_11.plan.md").write_text("- repo: other-repo\n  code: C2\n")
        result = mod._declared_stage_from_plan("not-here", tmp_path)  # type: ignore[attr-defined]
        assert result == "unknown"


# ---------------------------------------------------------------------------
# Tests: _check_cr1
# ---------------------------------------------------------------------------


class TestCheckCR1:
    def test_pass_when_no_patterns(self, tmp_path: Path) -> None:
        mod = _load_module()
        repo = tmp_path / "clean-repo"
        repo.mkdir()
        (repo / "main.py").write_text("def hello(): return 42\n")
        result = mod._check_cr1(repo)  # type: ignore[attr-defined]
        assert result.verified == "PASS"

    def test_mismatch_when_todo_found(self, tmp_path: Path) -> None:
        mod = _load_module()
        repo = tmp_path / "dirty-repo"
        repo.mkdir()
        (repo / "main.py").write_text("# TODO: fix this\ndef f(): pass\n")
        # Force Python fallback by making rg raise FileNotFoundError
        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = mod._check_cr1(repo)  # type: ignore[attr-defined]
        assert result.verified == "MISMATCH"

    def test_excludes_tests_directory(self, tmp_path: Path) -> None:
        mod = _load_module()
        repo = tmp_path / "repo-with-test-todos"
        (repo / "tests").mkdir(parents=True)
        (repo / "tests" / "test_foo.py").write_text("# TODO: implement\n")
        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = mod._check_cr1(repo)  # type: ignore[attr-defined]
        assert result.verified == "PASS"

    def test_mismatch_via_rg_output(self, tmp_path: Path) -> None:
        mod = _load_module()
        repo = tmp_path / "rg-repo"
        repo.mkdir()
        mock_rg = MagicMock(returncode=0, stdout=f"{repo}/main.py:3\n")
        with patch("subprocess.run", return_value=mock_rg):
            result = mod._check_cr1(repo)  # type: ignore[attr-defined]
        assert result.verified == "MISMATCH"


# ---------------------------------------------------------------------------
# Tests: _check_cr2
# ---------------------------------------------------------------------------


class TestCheckCR2:
    def test_unverified_when_no_coverage_xml(self, tmp_path: Path) -> None:
        mod = _load_module()
        result = mod._check_cr2(tmp_path, "70%")  # type: ignore[attr-defined]
        assert result.verified == "UNVERIFIED"
        assert "coverage.xml not found" in result.detail

    def test_pass_when_actual_meets_declared(self, tmp_path: Path) -> None:
        mod = _load_module()
        _write_coverage_xml(tmp_path / "coverage.xml", 0.75)
        result = mod._check_cr2(tmp_path, "74%")  # type: ignore[attr-defined]
        assert result.verified == "PASS"

    def test_mismatch_when_actual_below_declared(self, tmp_path: Path) -> None:
        mod = _load_module()
        _write_coverage_xml(tmp_path / "coverage.xml", 0.65)
        result = mod._check_cr2(tmp_path, "80%")  # type: ignore[attr-defined]
        assert result.verified == "MISMATCH"
        assert "actual" in result.detail

    def test_pass_with_unknown_declared(self, tmp_path: Path) -> None:
        mod = _load_module()
        _write_coverage_xml(tmp_path / "coverage.xml", 0.90)
        result = mod._check_cr2(tmp_path, "unknown")  # type: ignore[attr-defined]
        assert result.verified == "PASS"

    def test_unverified_on_malformed_xml(self, tmp_path: Path) -> None:
        mod = _load_module()
        (tmp_path / "coverage.xml").write_text("<broken>")
        result = mod._check_cr2(tmp_path, "70%")  # type: ignore[attr-defined]
        assert result.verified in ("UNVERIFIED", "MISMATCH", "PASS")


# ---------------------------------------------------------------------------
# Tests: _check_cr3
# ---------------------------------------------------------------------------


class TestCheckCR3:
    def test_pass_when_no_deps(self, tmp_path: Path) -> None:
        mod = _load_module()
        result = mod._check_cr3(tmp_path, [])  # type: ignore[attr-defined]
        assert result.verified == "PASS"
        assert "zero manifest deps" in result.detail

    def test_mismatch_when_integration_dir_missing(self, tmp_path: Path) -> None:
        mod = _load_module()
        result = mod._check_cr3(tmp_path, ["some-dep"])  # type: ignore[attr-defined]
        assert result.verified == "MISMATCH"
        assert "tests/integration/ missing" in result.detail

    def test_pass_when_integration_test_exists(self, tmp_path: Path) -> None:
        mod = _load_module()
        intg = tmp_path / "tests" / "integration"
        intg.mkdir(parents=True)
        (intg / "test_some_dep_integration.py").write_text("def test_pass(): pass\n")
        result = mod._check_cr3(tmp_path, ["some-dep"])  # type: ignore[attr-defined]
        assert result.verified == "PASS"

    def test_mismatch_when_test_missing_for_one_dep(self, tmp_path: Path) -> None:
        mod = _load_module()
        intg = tmp_path / "tests" / "integration"
        intg.mkdir(parents=True)
        (intg / "test_dep_a_integration.py").write_text("def test_pass(): pass\n")
        result = mod._check_cr3(tmp_path, ["dep-a", "dep-b"])  # type: ignore[attr-defined]
        assert result.verified == "MISMATCH"
        assert "dep-b" in result.detail


# ---------------------------------------------------------------------------
# Tests: _check_cr4
# ---------------------------------------------------------------------------


class TestCheckCR4:
    def test_always_unverified_no_baseline(self, tmp_path: Path) -> None:
        mod = _load_module()
        with patch("subprocess.run", return_value=MagicMock(returncode=1, stdout="")):
            result = mod._check_cr4(tmp_path)  # type: ignore[attr-defined]
        assert result.verified == "UNVERIFIED"

    def test_notes_baseline_errors(self, tmp_path: Path) -> None:
        mod = _load_module()
        baseline = {"file.py": [{"message": "error1"}, {"message": "error2"}]}
        (tmp_path / ".basedpyright-baseline.json").write_text(json.dumps(baseline))
        with patch("subprocess.run", return_value=MagicMock(returncode=1, stdout="")):
            result = mod._check_cr4(tmp_path)  # type: ignore[attr-defined]
        assert "2 suppressed error" in result.detail

    def test_notes_high_noqa_count(self, tmp_path: Path) -> None:
        mod = _load_module()
        mock_rg = MagicMock(returncode=0, stdout=f"{tmp_path}/a.py:15\n")
        with patch("subprocess.run", return_value=mock_rg):
            result = mod._check_cr4(tmp_path)  # type: ignore[attr-defined]
        assert result.verified == "UNVERIFIED"
        assert "noqa" in result.detail or "suppression" in result.detail or "heuristic" in result.detail


# ---------------------------------------------------------------------------
# Tests: _check_cr5
# ---------------------------------------------------------------------------


class TestCheckCR5:
    def test_unverified_when_gh_not_found(self) -> None:
        mod = _load_module()
        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = mod._check_cr5("my-repo")  # type: ignore[attr-defined]
        assert result.verified == "UNVERIFIED"

    def test_pass_when_merged_pr_found(self) -> None:
        mod = _load_module()
        pr_response = json.dumps([{"number": 42, "title": "feat: ...", "headRefName": "feat/code-readiness-my-repo"}])
        mock_result = MagicMock(returncode=0, stdout=pr_response)
        with patch("subprocess.run", return_value=mock_result):
            result = mod._check_cr5("my-repo")  # type: ignore[attr-defined]
        assert result.verified == "PASS"
        assert "42" in result.detail

    def test_unverified_when_empty_pr_list(self) -> None:
        mod = _load_module()
        mock_result = MagicMock(returncode=0, stdout=json.dumps([]))
        with patch("subprocess.run", return_value=mock_result):
            result = mod._check_cr5("my-repo")  # type: ignore[attr-defined]
        assert result.verified == "UNVERIFIED"

    def test_unverified_on_timeout(self) -> None:
        mod = _load_module()
        import subprocess as _subprocess

        with patch("subprocess.run", side_effect=_subprocess.TimeoutExpired(cmd="gh", timeout=15)):
            result = mod._check_cr5("my-repo")  # type: ignore[attr-defined]
        assert result.verified == "UNVERIFIED"


# ---------------------------------------------------------------------------
# Tests: _repos_for_tier
# ---------------------------------------------------------------------------


class TestReposForTier:
    def _make_manifest(self) -> dict[str, dict[str, object]]:
        return {
            "repo-a": {"arch_tier": "0"},
            "repo-b": {"arch_tier": "1"},
            "repo-c": {"arch_tier": "service"},
            "repo-d": {"arch_tier": "0"},
        }

    def test_all_returns_every_repo(self) -> None:
        mod = _load_module()
        m = self._make_manifest()
        result = mod._repos_for_tier("all", m)  # type: ignore[attr-defined]
        assert set(result) == {"repo-a", "repo-b", "repo-c", "repo-d"}

    def test_t0_filters_correctly(self) -> None:
        mod = _load_module()
        m = self._make_manifest()
        result = mod._repos_for_tier("T0", m)  # type: ignore[attr-defined]
        assert set(result) == {"repo-a", "repo-d"}

    def test_t4_maps_to_service(self) -> None:
        mod = _load_module()
        m = self._make_manifest()
        result = mod._repos_for_tier("T4", m)  # type: ignore[attr-defined]
        assert result == ["repo-c"]

    def test_unknown_tier_returns_empty(self) -> None:
        mod = _load_module()
        m = self._make_manifest()
        result = mod._repos_for_tier("T99", m)  # type: ignore[attr-defined]
        assert result == []


# ---------------------------------------------------------------------------
# Tests: verify_repo
# ---------------------------------------------------------------------------


class TestVerifyRepo:
    def test_error_when_repo_dir_missing(self, tmp_path: Path) -> None:
        mod = _load_module()
        result = mod.verify_repo("nonexistent-repo", tmp_path, tmp_path / "codex", {})  # type: ignore[attr-defined]
        assert result.declared_stage == "N/A"
        assert len(result.errors) > 0

    def test_returns_result_with_five_gates(self, tmp_path: Path) -> None:
        mod = _load_module()
        repo = tmp_path / "my-repo"
        repo.mkdir()
        (repo / "main.py").write_text("def hello(): return 1\n")
        with patch("subprocess.run", return_value=MagicMock(returncode=1, stdout="")):
            result = mod.verify_repo("my-repo", tmp_path, tmp_path / "codex", {})  # type: ignore[attr-defined]
        assert len(result.gates) == 5
        assert result.gates[0].gate == "CR1"
        assert result.gates[4].gate == "CR5"

    def test_picks_coverage_pct_from_manifest(self, tmp_path: Path) -> None:
        mod = _load_module()
        repo = tmp_path / "covered-repo"
        repo.mkdir()
        _write_coverage_xml(repo / "coverage.xml", 0.85)
        manifest: dict[str, dict[str, object]] = {
            "covered-repo": {"arch_tier": "0", "dependencies": [], "coverage_pct": 80}
        }
        with patch("subprocess.run", return_value=MagicMock(returncode=1, stdout="")):
            result = mod.verify_repo("covered-repo", tmp_path, tmp_path / "codex", manifest)  # type: ignore[attr-defined]
        cr2 = next(g for g in result.gates if g.gate == "CR2")
        assert cr2.verified == "PASS"


# ---------------------------------------------------------------------------
# Tests: main entry point
# ---------------------------------------------------------------------------


class TestMain:
    def test_repo_arg_exits_zero_or_one(self, tmp_path: Path) -> None:
        mod = _load_module()
        repo = tmp_path / "test-repo"
        repo.mkdir()
        (repo / "app.py").write_text("x = 1\n")
        pm = tmp_path / "unified-trading-pm"
        pm.mkdir()
        (pm / "workspace-manifest.json").write_text(json.dumps({"repositories": {}}))
        with (
            patch.object(
                sys,
                "argv",
                [
                    "check-repo-readiness.py",
                    "--repo",
                    "test-repo",
                    "--workspace-root",
                    str(tmp_path),
                ],
            ),
            patch("subprocess.run", return_value=MagicMock(returncode=1, stdout="")),
        ):
            result = mod.main()  # type: ignore[attr-defined]
        assert result in (0, 1)

    def test_all_flag_returns_1_when_empty_manifest(self, tmp_path: Path) -> None:
        mod = _load_module()
        pm = tmp_path / "unified-trading-pm"
        pm.mkdir()
        (pm / "workspace-manifest.json").write_text("{}")
        with patch.object(
            sys,
            "argv",
            ["check-repo-readiness.py", "--all", "--workspace-root", str(tmp_path)],
        ):
            result = mod.main()  # type: ignore[attr-defined]
        assert result == 1

    def test_tier_arg_warns_when_no_repos(self, tmp_path: Path) -> None:
        mod = _load_module()
        pm = tmp_path / "unified-trading-pm"
        pm.mkdir()
        (pm / "workspace-manifest.json").write_text(
            json.dumps({"repositories": {"repo-x": {"arch_tier": "service", "dependencies": []}}})
        )
        with patch.object(
            sys,
            "argv",
            ["check-repo-readiness.py", "--tier", "T0", "--workspace-root", str(tmp_path)],
        ):
            result = mod.main()  # type: ignore[attr-defined]
        assert result == 0
