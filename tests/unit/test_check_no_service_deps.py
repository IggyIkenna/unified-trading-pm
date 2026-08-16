"""Unit tests for scripts/validation/check-no-service-deps.py."""

from __future__ import annotations

import importlib.util
import json
import types
from pathlib import Path

import pytest


def _load_module() -> types.ModuleType:
    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "scripts" / "validation" / "check-no-service-deps.py"
    spec = importlib.util.spec_from_file_location("check_no_service_deps", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


MOD = _load_module()


# ── Tests: get_service_repos ─────────────────────────────────────────────


class TestGetServiceRepos:
    def test_extracts_service_repos(self, tmp_path: Path) -> None:
        manifest = tmp_path / "workspace-manifest.json"
        manifest.write_text(
            json.dumps(
                {
                    "repositories": {
                        "execution-service": {"type": "service"},
                        "unified-trading-library": {"type": "library"},
                        "strategy-service": {"type": "service"},
                    }
                }
            )
        )
        result = MOD.get_service_repos(manifest)
        assert result == {"execution-service", "strategy-service"}

    def test_empty_repositories(self, tmp_path: Path) -> None:
        manifest = tmp_path / "workspace-manifest.json"
        manifest.write_text(json.dumps({"repositories": {}}))
        result = MOD.get_service_repos(manifest)
        assert result == set()

    def test_includes_api_and_batch_service_flavours(self, tmp_path: Path) -> None:
        # REGRESSION (utl_uac_reuse 2026-06-11): the gate previously matched only
        # type=="service", so api-service / batch-service repos (deployment-api,
        # batch-live-reconciliation-service) were never treated as services →
        # deployment-api -> strategy-service slipped past silently.
        manifest = tmp_path / "workspace-manifest.json"
        manifest.write_text(
            json.dumps(
                {
                    "repositories": {
                        "execution-service": {"type": "service"},
                        "deployment-api": {"type": "api-service"},
                        "batch-live-reconciliation-service": {"type": "batch-service"},
                        "client-reporting-api": {"type": "api"},
                        "unified-trading-library": {"type": "library"},
                        "deployment-service": {"type": "infrastructure"},
                    }
                }
            )
        )
        result = MOD.get_service_repos(manifest)
        assert result == {
            "execution-service",
            "deployment-api",
            "batch-live-reconciliation-service",
            "client-reporting-api",
        }
        # infrastructure / library are NOT services
        assert "unified-trading-library" not in result
        assert "deployment-service" not in result


# ── Tests: get_current_repo_name ─────────────────────────────────────────


class TestGetCurrentRepoName:
    def test_extracts_name_from_pyproject(self, tmp_path: Path) -> None:
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "execution-service"\nversion = "1.0.0"\n')
        result = MOD.get_current_repo_name(tmp_path)
        assert result == "execution-service"

    def test_returns_none_when_no_pyproject(self, tmp_path: Path) -> None:
        result = MOD.get_current_repo_name(tmp_path)
        assert result is None

    def test_handles_single_quoted_name(self, tmp_path: Path) -> None:
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[project]\nname = 'my-service'\n")
        result = MOD.get_current_repo_name(tmp_path)
        assert result == "my-service"

    def test_stops_at_next_section(self, tmp_path: Path) -> None:
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[project]\nversion = '1.0.0'\n[tool.ruff]\nname = 'ruff-name'\n")
        result = MOD.get_current_repo_name(tmp_path)
        assert result is None

    def test_returns_none_when_no_name_in_project(self, tmp_path: Path) -> None:
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[project]\nversion = '1.0.0'\n")
        result = MOD.get_current_repo_name(tmp_path)
        assert result is None


# ── Tests: get_path_deps ─────────────────────────────────────────────────


class TestGetPathDeps:
    def test_extracts_path_deps(self, tmp_path: Path) -> None:
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            '[project]\nname = "my-service"\n\n'
            "[tool.uv.sources]\n"
            '"unified-trading-library" = { path = "../unified-trading-library" }\n'
            '"market-tick-data-service" = { path = "../market-tick-data-service" }\n'
        )
        result = MOD.get_path_deps(pyproject)
        assert "unified-trading-library" in result
        assert "market-tick-data-service" in result

    def test_no_uv_sources(self, tmp_path: Path) -> None:
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "my-service"\n')
        result = MOD.get_path_deps(pyproject)
        assert result == []

    def test_stops_at_next_section(self, tmp_path: Path) -> None:
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            '[tool.uv.sources]\n"dep-a" = { path = "../dep-a" }\n[tool.ruff]\n"dep-b" = { path = "../dep-b" }\n'
        )
        result = MOD.get_path_deps(pyproject)
        assert "dep-a" in result
        assert "dep-b" not in result

    def test_extracts_dotted_table_form(self, tmp_path: Path) -> None:
        # REGRESSION (utl_uac_reuse 2026-06-11): the gate parsed ONLY the flat
        # [tool.uv.sources] header. mdps used the DOTTED [tool.uv.sources.<dep>]
        # table form, so its market-tick-data-service path dep was never seen.
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            '[build-system]\nrequires = ["hatchling"]\n\n'
            "[tool.uv.sources.unified-trading-library]\n"
            'path = "../unified-trading-library"\n'
            "editable = true\n\n"
            "[tool.uv.sources.market-tick-data-service]\n"
            'path = "../market-tick-data-service"\n'
            "editable = true\n\n"
            '[project]\nname = "market-data-processing-service"\n'
        )
        result = MOD.get_path_deps(pyproject)
        assert "unified-trading-library" in result
        assert "market-tick-data-service" in result

    def test_extracts_flat_table_form_deployment_api_style(self, tmp_path: Path) -> None:
        # REGRESSION: the real deployment-api shape — flat header with a
        # strategy-service path dep that must be detected.
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            '[project]\nname = "deployment-api"\n\n'
            "[tool.uv.sources]\n"
            'unified-trading-library = { path = "../unified-trading-library", editable = true}\n'
            'strategy-service = { path = "../strategy-service", editable = true}\n\n'
            "[tool.ruff]\nline-length = 120\n"
        )
        result = MOD.get_path_deps(pyproject)
        assert "strategy-service" in result
        assert "unified-trading-library" in result

    def test_dotted_table_closed_by_next_section(self, tmp_path: Path) -> None:
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[tool.uv.sources.dep-a]\npath = "../dep-a"\n\n[tool.ruff]\nsome-key = "../not-a-dep"\n')
        result = MOD.get_path_deps(pyproject)
        assert result == ["dep-a"]


# ── Tests: find_manifest ─────────────────────────────────────────────────


class TestFindManifest:
    def test_finds_via_repo_root_env(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        pm_dir = tmp_path / "unified-trading-pm"
        pm_dir.mkdir()
        manifest = pm_dir / "workspace-manifest.json"
        manifest.write_text("{}")
        monkeypatch.setenv("REPO_ROOT", str(tmp_path))
        result = MOD.find_manifest()
        assert result == manifest

    def test_returns_none_when_not_found(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("REPO_ROOT", str(tmp_path))
        monkeypatch.chdir(tmp_path)
        result = MOD.find_manifest()
        assert result is None


# ── Tests: _service_package_name ─────────────────────────────────────────


class TestServicePackageName:
    def test_dashes_become_underscores(self) -> None:
        assert MOD._service_package_name("strategy-service") == "strategy_service"

    def test_no_dashes_unchanged(self) -> None:
        assert MOD._service_package_name("mlservice") == "mlservice"


# ── Tests: find_raw_service_imports ──────────────────────────────────────
# REGRESSION-GUARD (utl_reuse_phase9, 2026-07-13, additive-hardening deferred item):
# this scanner is WARN-only in main() — a fleet probe found ~39 pre-existing, already
# reviewed/tracked raw cross-service imports (tests + a few source files across
# deployment-service/execution-service/strategy-service/features-service), none of
# which carry a path dep, so hard-failing on them today would break those repos'
# quality-gates.sh with no way to tell "new accidental coupling" from "sanctioned debt."


class TestFindRawServiceImports:
    def test_detects_plain_import(self, tmp_path: Path) -> None:
        (tmp_path / "mod.py").write_text("import strategy_service\n")
        result = MOD.find_raw_service_imports(tmp_path, {"strategy_service": "strategy-service"})
        assert result == [("mod.py", 1, "strategy-service")]

    def test_detects_from_import(self, tmp_path: Path) -> None:
        (tmp_path / "mod.py").write_text("from strategy_service.engine import foo\n")
        result = MOD.find_raw_service_imports(tmp_path, {"strategy_service": "strategy-service"})
        assert result == [("mod.py", 1, "strategy-service")]

    def test_ignores_own_package_not_in_map(self, tmp_path: Path) -> None:
        # Caller excludes `current` from other_service_packages before calling; simulate
        # that here by simply not including it in the map.
        (tmp_path / "mod.py").write_text("import execution_service\n")
        result = MOD.find_raw_service_imports(tmp_path, {"strategy_service": "strategy-service"})
        assert result == []

    def test_ignores_library_imports(self, tmp_path: Path) -> None:
        (tmp_path / "mod.py").write_text("from unified_trading_library import get_params\n")
        result = MOD.find_raw_service_imports(tmp_path, {"strategy_service": "strategy-service"})
        assert result == []

    def test_ignores_substring_package_name(self, tmp_path: Path) -> None:
        # `strategy_service_utils` must NOT match `strategy_service` (exact top-level
        # component match only, not a substring/prefix match).
        (tmp_path / "mod.py").write_text("import strategy_service_utils\n")
        result = MOD.find_raw_service_imports(tmp_path, {"strategy_service": "strategy-service"})
        assert result == []

    def test_excludes_venv_directory(self, tmp_path: Path) -> None:
        venv_dir = tmp_path / ".venv" / "lib"
        venv_dir.mkdir(parents=True)
        (venv_dir / "vendored.py").write_text("import strategy_service\n")
        result = MOD.find_raw_service_imports(tmp_path, {"strategy_service": "strategy-service"})
        assert result == []

    def test_skips_unparseable_file(self, tmp_path: Path) -> None:
        (tmp_path / "broken.py").write_text("this is not : valid python (((\n")
        result = MOD.find_raw_service_imports(tmp_path, {"strategy_service": "strategy-service"})
        assert result == []

    def test_no_violations_returns_empty_list(self, tmp_path: Path) -> None:
        (tmp_path / "mod.py").write_text("import os\nimport sys\n")
        result = MOD.find_raw_service_imports(tmp_path, {"strategy_service": "strategy-service"})
        assert result == []


# ── Tests: main (end-to-end, WARN-only raw-import behaviour) ─────────────


def _make_workspace(tmp_path: Path) -> Path:
    """Build a fake workspace: unified-trading-pm/workspace-manifest.json declaring
    svc-a + svc-b as services; caller adds svc-a's own pyproject.toml + source."""
    pm_dir = tmp_path / "unified-trading-pm"
    pm_dir.mkdir()
    (pm_dir / "workspace-manifest.json").write_text(
        json.dumps({"repositories": {"svc-a": {"type": "service"}, "svc-b": {"type": "service"}}})
    )
    return tmp_path


class TestMainWarnOnlyRawImport:
    def test_raw_import_warns_but_exit_zero(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        workspace = _make_workspace(tmp_path)
        svc_a = workspace / "svc-a"
        svc_a.mkdir()
        (svc_a / "pyproject.toml").write_text('[project]\nname = "svc-a"\n')
        (svc_a / "app.py").write_text("import svc_b\n")
        monkeypatch.setenv("REPO_ROOT", str(workspace))
        monkeypatch.chdir(svc_a)
        exit_code = MOD.main()
        captured = capsys.readouterr()
        assert exit_code == 0
        assert "[WARN]" in captured.err
        assert "svc-b" in captured.err

    def test_path_dep_still_hard_fails(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        workspace = _make_workspace(tmp_path)
        svc_a = workspace / "svc-a"
        svc_a.mkdir()
        (svc_a / "pyproject.toml").write_text(
            '[project]\nname = "svc-a"\n\n[tool.uv.sources]\nsvc-b = { path = "../svc-b" }\n'
        )
        monkeypatch.setenv("REPO_ROOT", str(workspace))
        monkeypatch.chdir(svc_a)
        exit_code = MOD.main()
        captured = capsys.readouterr()
        assert exit_code == 1
        assert "[WARN]" not in captured.err
        assert "path deps" in captured.err

    def test_no_violations_clean_exit(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        workspace = _make_workspace(tmp_path)
        svc_a = workspace / "svc-a"
        svc_a.mkdir()
        (svc_a / "pyproject.toml").write_text('[project]\nname = "svc-a"\n')
        (svc_a / "app.py").write_text("import os\n")
        monkeypatch.setenv("REPO_ROOT", str(workspace))
        monkeypatch.chdir(svc_a)
        exit_code = MOD.main()
        captured = capsys.readouterr()
        assert exit_code == 0
        assert captured.err == ""


# ── Tests: main — strategy-service -> MTDS is HARD-FAILED (normalisation rule) ───
# The "normalisation rule" (2026-08-16 operator ruling,
# /plans/active/venue_readiness_and_registry_hardening_2026_08_16.md): strategy-service
# must never import market-tick-data-service directly. This one pair is hard-failed;
# every other raw cross-service import pair stays WARN-only (see class above).


def _make_strategy_mtds_workspace(tmp_path: Path) -> Path:
    pm_dir = tmp_path / "unified-trading-pm"
    pm_dir.mkdir()
    (pm_dir / "workspace-manifest.json").write_text(
        json.dumps(
            {
                "repositories": {
                    "strategy-service": {"type": "service"},
                    "market-tick-data-service": {"type": "service"},
                }
            }
        )
    )
    return tmp_path


class TestMainHardFailedNormalisationRule:
    def test_strategy_service_importing_mtds_hard_fails(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        workspace = _make_strategy_mtds_workspace(tmp_path)
        strategy = workspace / "strategy-service"
        strategy.mkdir()
        (strategy / "pyproject.toml").write_text('[project]\nname = "strategy-service"\n')
        (strategy / "engine.py").write_text("from market_tick_data_service.market_interface import CanonicalTick\n")
        monkeypatch.setenv("REPO_ROOT", str(workspace))
        monkeypatch.chdir(strategy)
        exit_code = MOD.main()
        captured = capsys.readouterr()
        assert exit_code == 1
        assert "[FAIL]" in captured.err
        assert "normalisation rule" in captured.err
        assert "[WARN]" not in captured.err

    def test_other_service_importing_mtds_still_warn_only(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # Only the (strategy-service, market-tick-data-service) pair is hard-failed —
        # e.g. features-service reading MTDS directly stays WARN-only, unaffected.
        pm_dir = tmp_path / "unified-trading-pm"
        pm_dir.mkdir()
        (pm_dir / "workspace-manifest.json").write_text(
            json.dumps(
                {
                    "repositories": {
                        "features-service": {"type": "service"},
                        "market-tick-data-service": {"type": "service"},
                    }
                }
            )
        )
        features = tmp_path / "features-service"
        features.mkdir()
        (features / "pyproject.toml").write_text('[project]\nname = "features-service"\n')
        (features / "engine.py").write_text("import market_tick_data_service\n")
        monkeypatch.setenv("REPO_ROOT", str(tmp_path))
        monkeypatch.chdir(features)
        exit_code = MOD.main()
        captured = capsys.readouterr()
        assert exit_code == 0
        assert "[WARN]" in captured.err
        assert "[FAIL]" not in captured.err
