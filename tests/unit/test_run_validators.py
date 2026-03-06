"""Unit tests for scripts/run_validators.py."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch


def _load_run_validators_module():
    import importlib.util

    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "scripts" / "run_validators.py"
    spec = importlib.util.spec_from_file_location("run_validators", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestRunChecklistValidator:
    def test_skip_when_configs_not_found(self) -> None:
        mod = _load_run_validators_module()
        with patch.object(mod, "WORKSPACE_ROOT", Path("/nonexistent")):
            result = mod.run_checklist_validator()
        assert result == 0

    def test_skip_when_script_not_found(self, tmp_path: Path) -> None:
        mod = _load_run_validators_module()
        configs = tmp_path / "configs"
        configs.mkdir()
        with (
            patch.object(mod, "PM_ROOT", tmp_path),
            patch.object(mod, "VALIDATORS_DIR", tmp_path / "validators"),
        ):
            result = mod.run_checklist_validator(configs_path=configs)
        assert result == 0


class TestRunManifestValidator:
    def test_skip_when_manifest_not_found(self) -> None:
        mod = _load_run_validators_module()
        with patch.object(mod, "PM_ROOT", Path("/nonexistent")):
            result = mod.run_manifest_validator()
        assert result == 0


class TestRunPlanLinksValidator:
    def test_skip_when_script_not_found(self, tmp_path: Path) -> None:
        mod = _load_run_validators_module()
        with (
            patch.object(mod, "PM_ROOT", tmp_path),
            patch.object(mod, "WORKSPACE_ROOT", tmp_path),
            patch.object(mod, "VALIDATORS_DIR", tmp_path / "validators"),
        ):
            result = mod.run_plan_links_validator()
        assert result == 0


class TestMain:
    def test_main_scope_all_mocks_subprocess(self, tmp_path: Path) -> None:
        mod = _load_run_validators_module()
        validators = tmp_path / "validators"
        validators.mkdir()
        (validators / "validate_checklist_phase9.py").touch()
        (validators / "validate_workspace_manifest.py").touch()
        (validators / "validate_plan_links.py").touch()
        (tmp_path / "workspace-manifest.json").write_text("{}")
        (tmp_path / "plans" / "active").mkdir(parents=True)
        (tmp_path / "deployment-service" / "configs").mkdir(parents=True)
        with (
            patch.object(mod, "PM_ROOT", tmp_path),
            patch.object(mod, "WORKSPACE_ROOT", tmp_path),
            patch.object(mod, "VALIDATORS_DIR", validators),
            patch("subprocess.run", return_value=MagicMock(returncode=0)),
            patch.object(sys, "argv", ["run_validators.py", "--scope", "all"]),
        ):
            result = mod.main()
        assert result == 0

    def test_main_scope_checklist_only(self, tmp_path: Path) -> None:
        mod = _load_run_validators_module()
        configs = tmp_path / "configs"
        configs.mkdir()
        validators = tmp_path / "validators"
        validators.mkdir()
        (validators / "validate_checklist_phase9.py").touch()
        with (
            patch.object(mod, "PM_ROOT", tmp_path),
            patch.object(mod, "VALIDATORS_DIR", validators),
            patch("subprocess.run", return_value=MagicMock(returncode=0)),
            patch.object(sys, "argv", ["run_validators.py", "--scope", "checklist", "--configs", str(configs)]),
        ):
            result = mod.main()
        assert result == 0
