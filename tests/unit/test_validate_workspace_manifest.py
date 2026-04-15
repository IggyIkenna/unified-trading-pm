"""Unit tests for scripts/validators/validate_workspace_manifest.py."""

from __future__ import annotations

import importlib.util
import json
import types
from pathlib import Path

import pytest


def _load_module() -> types.ModuleType:
    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "scripts" / "validators" / "validate_workspace_manifest.py"
    spec = importlib.util.spec_from_file_location("validate_workspace_manifest", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


MOD = _load_module()


# ── Helpers ──────────────────────────────────────────────────────────────


def _make_valid_manifest() -> dict[str, object]:
    """Create a minimal valid workspace-manifest.json structure."""
    return {
        "repositories": {
            "execution-service": {
                "ci_status": "PASSING",
                "coverage_pct": 80,
                "bypass_audit_path": "",
                "testing_level": "unit",
                "skipped_gates": [],
            },
            "unified-trading-library": {
                "ci_status": "PASSING",
                "coverage_pct": 90,
                "bypass_audit_path": "",
                "testing_level": "unit",
                "skipped_gates": [],
            },
        },
        "topologicalOrder": {
            "description": "Build order",
            "levels": [
                {"level": 0, "repos": ["unified-trading-library"]},
                {"level": 1, "repos": ["execution-service"]},
            ],
        },
        "versions": {},
    }


# ── Tests: _jdict / _jlist ──────────────────────────────────────────────


class TestJsonHelpers:
    def test_jdict_with_dict(self) -> None:
        assert MOD._jdict({"a": 1}) == {"a": 1}

    def test_jdict_with_non_dict(self) -> None:
        assert MOD._jdict("string") is None
        assert MOD._jdict([1, 2]) is None
        assert MOD._jdict(None) is None

    def test_jlist_with_list(self) -> None:
        assert MOD._jlist([1, 2]) == [1, 2]

    def test_jlist_with_non_list(self) -> None:
        assert MOD._jlist("string") is None
        assert MOD._jlist({"a": 1}) is None


# ── Tests: main ──────────────────────────────────────────────────────────


class TestMain:
    def test_valid_manifest(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        manifest = tmp_path / "workspace-manifest.json"
        manifest.write_text(json.dumps(_make_valid_manifest()))
        monkeypatch.setattr("sys.argv", ["validate_workspace_manifest.py", "--manifest", str(manifest)])
        result = MOD.main()
        assert result == 0

    def test_missing_manifest(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        manifest = tmp_path / "nonexistent.json"
        monkeypatch.setattr("sys.argv", ["validate_workspace_manifest.py", "--manifest", str(manifest)])
        result = MOD.main()
        assert result == 1

    def test_missing_repositories(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        manifest = tmp_path / "workspace-manifest.json"
        manifest.write_text(json.dumps({"topologicalOrder": {}}))
        monkeypatch.setattr("sys.argv", ["validate_workspace_manifest.py", "--manifest", str(manifest)])
        result = MOD.main()
        assert result == 1

    def test_empty_repositories(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        manifest = tmp_path / "workspace-manifest.json"
        data = _make_valid_manifest()
        data["repositories"] = {}
        manifest.write_text(json.dumps(data))
        monkeypatch.setattr("sys.argv", ["validate_workspace_manifest.py", "--manifest", str(manifest)])
        result = MOD.main()
        assert result == 1

    def test_missing_required_field(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        manifest = tmp_path / "workspace-manifest.json"
        data = _make_valid_manifest()
        # Remove a required field from one repo
        del data["repositories"]["execution-service"]["coverage_pct"]  # type: ignore[union-attr]
        manifest.write_text(json.dumps(data))
        monkeypatch.setattr("sys.argv", ["validate_workspace_manifest.py", "--manifest", str(manifest)])
        result = MOD.main()
        assert result == 1

    def test_topo_order_references_unknown_repo(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        manifest = tmp_path / "workspace-manifest.json"
        data = _make_valid_manifest()
        data["topologicalOrder"]["levels"].append(  # type: ignore[union-attr]
            {"level": 2, "repos": ["nonexistent-service"]}
        )
        manifest.write_text(json.dumps(data))
        monkeypatch.setattr("sys.argv", ["validate_workspace_manifest.py", "--manifest", str(manifest)])
        result = MOD.main()
        assert result == 1

    def test_versions_references_unknown_repo(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        manifest = tmp_path / "workspace-manifest.json"
        data = _make_valid_manifest()
        data["versions"] = {"ghost-repo": "1.0.0"}
        manifest.write_text(json.dumps(data))
        monkeypatch.setattr("sys.argv", ["validate_workspace_manifest.py", "--manifest", str(manifest)])
        result = MOD.main()
        assert result == 1

    def test_versions_note_key_ok(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        manifest = tmp_path / "workspace-manifest.json"
        data = _make_valid_manifest()
        data["versions"] = {"_note": "version tracking info"}
        manifest.write_text(json.dumps(data))
        monkeypatch.setattr("sys.argv", ["validate_workspace_manifest.py", "--manifest", str(manifest)])
        result = MOD.main()
        assert result == 0

    def test_missing_topo_levels(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        manifest = tmp_path / "workspace-manifest.json"
        data = _make_valid_manifest()
        data["topologicalOrder"] = {"description": "no levels"}
        manifest.write_text(json.dumps(data))
        monkeypatch.setattr("sys.argv", ["validate_workspace_manifest.py", "--manifest", str(manifest)])
        result = MOD.main()
        assert result == 1
