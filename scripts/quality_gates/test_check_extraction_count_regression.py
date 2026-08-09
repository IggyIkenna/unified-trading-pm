# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""Unit tests for check_extraction_count_regression.py.

Formalizes the manual "fresh count LOWER than committed baseline = DO NOT commit"
checkpoint from venv_workspace_openapi_regen_batch11_findings_2026_08_09.md.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from check_extraction_count_regression import main  # type: ignore[import-not-found]


def _git(repo_root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo_root), *args], check=True, capture_output=True)


def _make_repo(tmp_path: Path) -> Path:
    repo_root = tmp_path / "unified-api-contracts"
    (repo_root / "openapi").mkdir(parents=True)
    _git(repo_root, "init", "-q")
    _git(repo_root, "config", "user.email", "test@example.com")
    _git(repo_root, "config", "user.name", "test")
    return repo_root


def _commit_files(repo_root: Path, config_registry: dict[str, object], openapi_spec: dict[str, object]) -> None:
    (repo_root / "openapi" / "config-registry.json").write_text(json.dumps(config_registry), encoding="utf-8")
    (repo_root / "openapi" / "unified-trading-system.openapi.json").write_text(
        json.dumps(openapi_spec), encoding="utf-8"
    )
    _git(repo_root, "add", "-A")
    _git(repo_root, "commit", "-q", "-m", "baseline")


def _write_fresh(repo_root: Path, config_registry: dict[str, object], openapi_spec: dict[str, object]) -> None:
    (repo_root / "openapi" / "config-registry.json").write_text(json.dumps(config_registry), encoding="utf-8")
    (repo_root / "openapi" / "unified-trading-system.openapi.json").write_text(
        json.dumps(openapi_spec), encoding="utf-8"
    )


_BASELINE_REGISTRY = {
    "_meta": {"total_configs": 30, "total_repos": 14},
    "configs_by_repo": {f"repo-{i}": [] for i in range(14)},
}
_BASELINE_SPEC = {
    "paths": {f"/p{i}": {} for i in range(628)},
    "components": {"schemas": {f"S{i}": {} for i in range(353)}},
}


def test_no_regression_when_counts_hold_or_rise(tmp_path: Path) -> None:
    repo_root = _make_repo(tmp_path)
    _commit_files(repo_root, _BASELINE_REGISTRY, _BASELINE_SPEC)

    fresh_registry = {
        "_meta": {"total_configs": 31, "total_repos": 15},
        "configs_by_repo": {f"repo-{i}": [] for i in range(15)},
    }
    _write_fresh(repo_root, fresh_registry, _BASELINE_SPEC)

    rc = main(["--repo-root", str(repo_root)])
    assert rc == 0


def test_regression_on_dropped_total_repos_fails(tmp_path: Path) -> None:
    repo_root = _make_repo(tmp_path)
    _commit_files(repo_root, _BASELINE_REGISTRY, _BASELINE_SPEC)

    # Mirrors the exact batch11 failure mode: total_configs UP, total_repos DOWN.
    fresh_registry = {
        "_meta": {"total_configs": 30, "total_repos": 9},
        "configs_by_repo": {f"repo-{i}": [] for i in range(9)},
    }
    _write_fresh(repo_root, fresh_registry, _BASELINE_SPEC)

    rc = main(["--repo-root", str(repo_root)])
    assert rc == 1


def test_regression_on_dropped_openapi_paths_fails(tmp_path: Path) -> None:
    repo_root = _make_repo(tmp_path)
    _commit_files(repo_root, _BASELINE_REGISTRY, _BASELINE_SPEC)

    fresh_spec = {"paths": {"/only-one": {}}, "components": {"schemas": {}}}
    _write_fresh(repo_root, _BASELINE_REGISTRY, fresh_spec)

    rc = main(["--repo-root", str(repo_root)])
    assert rc == 1


def test_warn_only_exits_zero_despite_regression(tmp_path: Path) -> None:
    repo_root = _make_repo(tmp_path)
    _commit_files(repo_root, _BASELINE_REGISTRY, _BASELINE_SPEC)

    fresh_registry = {"_meta": {"total_configs": 1, "total_repos": 1}, "configs_by_repo": {"repo-0": []}}
    _write_fresh(repo_root, fresh_registry, _BASELINE_SPEC)

    rc = main(["--repo-root", str(repo_root), "--warn-only"])
    assert rc == 0


def test_new_file_with_no_baseline_is_not_a_regression(tmp_path: Path) -> None:
    repo_root = tmp_path / "unified-api-contracts"
    (repo_root / "openapi").mkdir(parents=True)
    _git(repo_root, "init", "-q")
    _git(repo_root, "config", "user.email", "test@example.com")
    _git(repo_root, "config", "user.name", "test")
    # Commit something unrelated so HEAD exists, but never commit the tracked files.
    (repo_root / "README.md").write_text("x", encoding="utf-8")
    _git(repo_root, "add", "-A")
    _git(repo_root, "commit", "-q", "-m", "init")

    _write_fresh(repo_root, _BASELINE_REGISTRY, _BASELINE_SPEC)

    rc = main(["--repo-root", str(repo_root)])
    assert rc == 0


def test_missing_fresh_output_errors(tmp_path: Path) -> None:
    repo_root = _make_repo(tmp_path)
    _commit_files(repo_root, _BASELINE_REGISTRY, _BASELINE_SPEC)
    (repo_root / "openapi" / "config-registry.json").unlink()

    rc = main(["--repo-root", str(repo_root)])
    assert rc == 2


def test_not_a_git_repo_errors(tmp_path: Path) -> None:
    repo_root = tmp_path / "not-a-repo"
    repo_root.mkdir()
    rc = main(["--repo-root", str(repo_root)])
    assert rc == 2
