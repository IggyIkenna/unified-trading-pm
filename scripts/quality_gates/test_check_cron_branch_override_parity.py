# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Unit tests for check_cron_branch_override_parity.py.

Pure-Python, no filesystem outside pytest's tmp_path -- mirrors
agent-orchestrator's test_branch_state_integration_branch_parity.py in shape
(missing/wrong/stale row detection) but exercises the standalone QG-checker
form (check() + main()) rather than the pytest-fixture form.
"""

from __future__ import annotations

import json
from pathlib import Path

from check_cron_branch_override_parity import (  # type: ignore[import-not-found]
    DEFAULT_INTEGRATION_BRANCH,
    check,
    main,
)


def _write_manifest(tmp_path: Path, repositories: dict) -> Path:
    manifest_path = tmp_path / "workspace-manifest.json"
    manifest_path.write_text(json.dumps({"repositories": repositories}, indent=2) + "\n")
    return manifest_path


def _write_overrides(tmp_path: Path, rows: dict) -> Path:
    overrides_path = tmp_path / "cron-branch-overrides.txt"
    lines = ["# comment", ""] + [f"{repo} {branch}" for repo, branch in rows.items()]
    overrides_path.write_text("\n".join(lines) + "\n")
    return overrides_path


def test_default_branch_repo_needs_no_row(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path, {"agent-orchestrator": {"integration_branch": DEFAULT_INTEGRATION_BRANCH}})
    overrides = _write_overrides(tmp_path, {})
    assert check(manifest, overrides) == []


def test_missing_row_is_a_violation(tmp_path: Path) -> None:
    """The exact 2026-08-17 incident shape: manifest declares non-default, override file has nothing."""
    manifest = _write_manifest(tmp_path, {"unified-trading-ci": {"integration_branch": "main"}})
    overrides = _write_overrides(tmp_path, {})
    violations = check(manifest, overrides)
    assert len(violations) == 1
    assert "unified-trading-ci" in violations[0]
    assert "no row" in violations[0]


def test_matching_row_has_no_violation(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path, {"unified-trading-ci": {"integration_branch": "main"}})
    overrides = _write_overrides(tmp_path, {"unified-trading-ci": "main"})
    assert check(manifest, overrides) == []


def test_wrong_branch_is_a_violation(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path, {"unified-trading-ci": {"integration_branch": "main"}})
    overrides = _write_overrides(tmp_path, {"unified-trading-ci": "develop"})
    violations = check(manifest, overrides)
    assert len(violations) == 1
    assert "'develop'" in violations[0] and "'main'" in violations[0]


def test_stale_row_for_default_branch_repo_is_a_violation(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path, {"agent-orchestrator": {"integration_branch": DEFAULT_INTEGRATION_BRANCH}})
    overrides = _write_overrides(tmp_path, {"agent-orchestrator": "main"})
    violations = check(manifest, overrides)
    assert len(violations) == 1
    assert "stale row" in violations[0] or "remove" in violations[0]


def test_row_for_repo_not_in_manifest_is_not_a_violation(tmp_path: Path) -> None:
    """A row for a repo the manifest doesn't even mention isn't THIS checker's problem."""
    manifest = _write_manifest(tmp_path, {})
    overrides = _write_overrides(tmp_path, {"some-external-thing": "main"})
    assert check(manifest, overrides) == []


def test_main_exits_zero_on_parity(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path, {"unified-trading-ci": {"integration_branch": "main"}})
    overrides = _write_overrides(tmp_path, {"unified-trading-ci": "main"})
    assert main(["--manifest", str(manifest), "--overrides", str(overrides)]) == 0


def test_main_exits_one_on_drift(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path, {"unified-trading-ci": {"integration_branch": "main"}})
    overrides = _write_overrides(tmp_path, {})
    assert main(["--manifest", str(manifest), "--overrides", str(overrides)]) == 1


def test_main_exits_two_on_unreadable_manifest(tmp_path: Path) -> None:
    missing = tmp_path / "does-not-exist.json"
    overrides = _write_overrides(tmp_path, {})
    assert main(["--manifest", str(missing), "--overrides", str(overrides)]) == 2


def test_live_manifest_and_overrides_have_parity() -> None:
    """End-to-end smoke against the real repo files -- this IS the regression gate."""
    root = Path(__file__).resolve().parents[2]
    manifest = root / "workspace-manifest.json"
    overrides = root / "scripts" / "dev" / "cron-branch-overrides.txt"
    assert check(manifest, overrides) == []
