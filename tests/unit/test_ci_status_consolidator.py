"""Unit tests for scripts/cicd/ci_status_consolidator.py (the pure projection; no Firestore).

``get_all`` (the Firestore read) is exercised in CI / the hourly cron, not here. These tests
pin ``project()`` — the manifest mutation that copies the Firestore aggregate into
``repositories.*.ci_status`` / ``codebase_health`` only when a value actually differs.
"""

from __future__ import annotations

import importlib.util
import types
from pathlib import Path


def _load_module() -> types.ModuleType:
    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "scripts" / "cicd" / "ci_status_consolidator.py"
    spec = importlib.util.spec_from_file_location("ci_status_consolidator", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


MOD = _load_module()


def _wrap(repos: dict[str, dict[str, object]]) -> dict[str, object]:
    """Manifest wrapper; tests keep + assert on the ``repos`` dict reference (typed)."""
    return {"repositories": repos}


class TestProject:
    def test_differing_status_is_projected(self) -> None:
        repos: dict[str, dict[str, object]] = {"alerting-service": {"ci_status": "FEATURE_GREEN"}}
        fs = {"alerting-service": {"status": "MAIN_GREEN"}}
        changes = MOD.project(_wrap(repos), fs)
        assert changes == [("alerting-service", "ci_status", "FEATURE_GREEN", "MAIN_GREEN")]
        assert repos["alerting-service"]["ci_status"] == "MAIN_GREEN"

    def test_matching_status_is_noop(self) -> None:
        repos: dict[str, dict[str, object]] = {"alerting-service": {"ci_status": "MAIN_GREEN"}}
        fs = {"alerting-service": {"status": "MAIN_GREEN"}}
        assert MOD.project(_wrap(repos), fs) == []

    def test_repo_absent_from_firestore_is_untouched(self) -> None:
        repos: dict[str, dict[str, object]] = {"alerting-service": {"ci_status": "MAIN_GREEN"}}
        assert MOD.project(_wrap(repos), {}) == []
        assert repos["alerting-service"]["ci_status"] == "MAIN_GREEN"

    def test_firestore_repo_absent_from_manifest_is_ignored(self) -> None:
        repos: dict[str, dict[str, object]] = {"alerting-service": {"ci_status": "MAIN_GREEN"}}
        fs = {"some-removed-repo": {"status": "MAIN_GREEN"}}
        assert MOD.project(_wrap(repos), fs) == []

    def test_empty_status_does_not_blank(self) -> None:
        repos: dict[str, dict[str, object]] = {"alerting-service": {"ci_status": "MAIN_GREEN"}}
        fs = {"alerting-service": {"status": ""}}
        assert MOD.project(_wrap(repos), fs) == []
        assert repos["alerting-service"]["ci_status"] == "MAIN_GREEN"

    def test_sets_ci_status_when_field_missing(self) -> None:
        repos: dict[str, dict[str, object]] = {"alerting-service": {}}
        fs = {"alerting-service": {"status": "MAIN_GREEN"}}
        changes = MOD.project(_wrap(repos), fs)
        assert changes == [("alerting-service", "ci_status", None, "MAIN_GREEN")]
        assert repos["alerting-service"]["ci_status"] == "MAIN_GREEN"

    def test_codebase_health_projected_when_changed(self) -> None:
        repos: dict[str, dict[str, object]] = {"alerting-service": {"ci_status": "MAIN_GREEN"}}
        fs = {"alerting-service": {"status": "MAIN_GREEN", "codebase_health": {"coverage_pct": 81.2}}}
        changes = MOD.project(_wrap(repos), fs)
        assert ("alerting-service", "codebase_health", "<blob>", "<blob>") in changes
        assert repos["alerting-service"]["codebase_health"] == {"coverage_pct": 81.2}

    def test_codebase_health_noop_when_equal(self) -> None:
        health = {"coverage_pct": 81.2}
        repos: dict[str, dict[str, object]] = {
            "alerting-service": {"ci_status": "MAIN_GREEN", "codebase_health": dict(health)}
        }
        fs = {"alerting-service": {"status": "MAIN_GREEN", "codebase_health": dict(health)}}
        assert MOD.project(_wrap(repos), fs) == []

    def test_non_dict_repositories_is_safe(self) -> None:
        assert MOD.project({"repositories": []}, {"x": {"status": "MAIN_GREEN"}}) == []
