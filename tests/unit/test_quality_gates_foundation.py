"""
Unit tests for unified-trading-pm foundation scripts.

Covers:
  - scripts/manifest/generate_canonical_dependency_manifest.py (load_constraints, SVG generation)
  - scripts/manifest/generate_workspace_dag.py (re-exports from tests/test_generate_workspace_dag.py)
  - scripts/manifest/sbom-store.py (argument validation, env-var guards)
  - workspace-manifest.json (schema validation)
  - pyproject.toml (required fields)
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import tomllib
from pathlib import Path

import pytest

# ── Paths ─────────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_SCRIPT = REPO_ROOT / "scripts" / "manifest" / "generate_canonical_dependency_manifest.py"
DAG_SCRIPT = REPO_ROOT / "scripts" / "manifest" / "generate_workspace_dag.py"
SBOM_SCRIPT = REPO_ROOT / "scripts" / "manifest" / "sbom-store.py"
WORKSPACE_MANIFEST = REPO_ROOT / "workspace-manifest.json"
PYPROJECT = REPO_ROOT / "pyproject.toml"


def _load_module(path: Path, module_name: str):
    """Load a Python script as a module without executing its __main__ block."""
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


# ── pyproject.toml ─────────────────────────────────────────────────────────────


class TestPyproject:
    def test_pyproject_exists(self):
        assert PYPROJECT.exists(), "pyproject.toml must exist"

    def test_required_fields(self):
        with open(PYPROJECT, "rb") as f:
            data = tomllib.load(f)
        assert "project" in data, "[project] table required"
        assert "name" in data["project"]
        assert "version" in data["project"]
        assert "requires-python" in data["project"]

    def test_python_version_is_313(self):
        with open(PYPROJECT, "rb") as f:
            data = tomllib.load(f)
        req = data["project"]["requires-python"]
        assert "3.13" in req, f"requires-python must target 3.13, got: {req}"

    def test_ruff_line_length(self):
        with open(PYPROJECT, "rb") as f:
            data = tomllib.load(f)
        assert data.get("tool", {}).get("ruff", {}).get("line-length") == 120


# ── workspace-manifest.json ────────────────────────────────────────────────────


class TestWorkspaceManifest:
    def test_manifest_exists(self):
        assert WORKSPACE_MANIFEST.exists(), "workspace-manifest.json must exist"

    def test_manifest_is_valid_json(self):
        with open(WORKSPACE_MANIFEST) as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_manifest_has_repositories(self):
        with open(WORKSPACE_MANIFEST) as f:
            data = json.load(f)
        assert "repositories" in data, "manifest must have 'repositories' key"
        assert len(data["repositories"]) > 0

    def test_each_repo_has_required_keys(self):
        """repositories is a dict: {repo_name: {arch_tier: ..., type: ...}}"""
        with open(WORKSPACE_MANIFEST) as f:
            data = json.load(f)
        required_keys = {"arch_tier"}
        for name, repo in data["repositories"].items():
            assert isinstance(repo, dict), f"Repo {name} entry must be a dict"
            missing = required_keys - set(repo.keys())
            assert not missing, f"Repo {name} missing keys: {missing}"

    def test_arch_tiers_are_valid(self):
        valid_tiers = {
            "0",
            "1",
            "2",
            "3",
            "service",
            "api",
            "ui",
            "pm",
            "deprecated",
            "devops",
            "infrastructure",
            "integration",
        }
        with open(WORKSPACE_MANIFEST) as f:
            data = json.load(f)
        for name, repo in data["repositories"].items():
            tier = repo.get("arch_tier", "")
            assert tier in valid_tiers, f"Repo {name} has invalid arch_tier: {tier!r}"


# ── generate_canonical_dependency_manifest.py ─────────────────────────────────


class TestGenerateCanonicalDependencyManifest:
    def test_script_exists(self):
        assert MANIFEST_SCRIPT.exists()

    def test_load_constraints_returns_dict_when_file_missing(self, tmp_path, monkeypatch):
        """load_constraints() must return {} gracefully when constraints file is absent."""
        mod = _load_module(MANIFEST_SCRIPT, "gen_manifest")
        monkeypatch.setattr(mod, "CONSTRAINTS_PATH", tmp_path / "nonexistent.toml")
        result = mod.load_constraints()
        assert isinstance(result, dict)
        assert result == {}

    def test_load_constraints_parses_toml(self, tmp_path, monkeypatch):
        toml_content = b'[dependencies]\npandas = ">=2.0,<3.0"\nnumpy = ">=1.26"\n'
        f = tmp_path / "workspace-constraints.toml"
        f.write_bytes(toml_content)
        mod = _load_module(MANIFEST_SCRIPT, "gen_manifest2")
        monkeypatch.setattr(mod, "CONSTRAINTS_PATH", f)
        result = mod.load_constraints()
        assert "pandas" in result
        assert "numpy" in result

    def test_box_width_minimum(self):
        mod = _load_module(MANIFEST_SCRIPT, "gen_manifest3")
        assert hasattr(mod, "BOX_MIN_W")
        assert mod.BOX_MIN_W >= 80

    def test_svg_width_constant(self):
        mod = _load_module(MANIFEST_SCRIPT, "gen_manifest4")
        assert hasattr(mod, "SVG_W")
        assert mod.SVG_W > 0


# ── sbom-store.py ──────────────────────────────────────────────────────────────


class TestSbomStore:
    def test_script_exists(self):
        assert SBOM_SCRIPT.exists()

    def test_exits_nonzero_without_args(self):
        """main() must exit 1 when no file arg is given."""
        mod = _load_module(SBOM_SCRIPT, "sbom_store")
        original_argv = sys.argv[:]
        sys.argv = ["sbom-store.py"]
        try:
            with pytest.raises(SystemExit) as exc:
                mod.main()
            assert exc.value.code != 0
        finally:
            sys.argv = original_argv

    def test_exits_zero_when_file_missing(self, tmp_path):
        """main() must exit 0 (soft skip) when the audit file doesn't exist."""
        mod = _load_module(SBOM_SCRIPT, "sbom_store2")
        original_argv = sys.argv[:]
        sys.argv = ["sbom-store.py", str(tmp_path / "nonexistent.json")]
        try:
            with pytest.raises(SystemExit) as exc:
                mod.main()
            assert exc.value.code == 0
        finally:
            sys.argv = original_argv

    def test_exits_zero_when_no_project_id(self, tmp_path, monkeypatch):
        """main() must skip (exit 0) gracefully when GCP_PROJECT_ID is not set."""
        audit_file = tmp_path / "audit.json"
        audit_file.write_text("[]")
        monkeypatch.delenv("GCP_PROJECT_ID", raising=False)
        mod = _load_module(SBOM_SCRIPT, "sbom_store3")
        original_argv = sys.argv[:]
        sys.argv = ["sbom-store.py", str(audit_file)]
        try:
            with pytest.raises(SystemExit) as exc:
                mod.main()
            assert exc.value.code == 0
        finally:
            sys.argv = original_argv


# ── scripts/_workspace-lib.sh reachable ───────────────────────────────────────


class TestWorkspaceLibExists:
    def test_workspace_lib_sh_exists(self):
        lib = REPO_ROOT / "scripts" / "_workspace-lib.sh"
        assert lib.exists(), "_workspace-lib.sh must exist (used by all repos)"

    def test_quickmerge_sh_exists(self):
        qm = REPO_ROOT / "scripts" / "quickmerge.sh"
        assert qm.exists(), "quickmerge.sh must exist"

    def test_quality_gates_sh_exists(self):
        qg = REPO_ROOT / "scripts" / "quality-gates.sh"
        assert qg.exists(), "quality-gates.sh must exist"

    def test_quickmerge_is_executable(self):
        qm = REPO_ROOT / "scripts" / "quickmerge.sh"
        assert os.access(qm, os.X_OK), "quickmerge.sh must be executable"

    def test_quality_gates_is_executable(self):
        qg = REPO_ROOT / "scripts" / "quality-gates.sh"
        assert os.access(qg, os.X_OK), "quality-gates.sh must be executable"
