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
