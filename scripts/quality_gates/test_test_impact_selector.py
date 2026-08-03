# Epic: deployment_and_user_management_master
# Lifecycle: permanent
# Delete-when: NA
"""Golden-set regression tests for test_impact_selector.py.

Fixture repo with a known import graph, a known verified dynamic-dispatch
file, a known multi-level conftest.py tree, and a known cross-cutting
manifest — asserting the selector's exact expected output for every safe
case AND every escape-hatch category, per
test_impact_fleet_wide_measurement_and_rollout_2026_08_03.md Phase 2 todo 3's
done-when ("wired into the SAME repo's own quality-gates.sh so a regression
in the selector itself is caught the same way any other code regression").
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
import yaml
from test_impact_selector import classify_diff  # type: ignore[import-not-found]


def _write(root: Path, rel_path: str, content: str) -> Path:
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text(textwrap.dedent(content).lstrip())
    return path


def _make_fixture_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    _write(repo, "pkg/__init__.py", "")
    _write(repo, "pkg/base.py", "def base_fn(): return 1\n")
    _write(
        repo,
        "pkg/mid.py",
        """
        from pkg.base import base_fn

        def mid_fn(): return base_fn() + 1
        """,
    )
    # verified dynamic-dispatch mechanism (matches the real trade_execution/__init__.py shape)
    _write(
        repo,
        "pkg/dispatch/__init__.py",
        """
        import importlib

        def __getattr__(name: str) -> object:
            module = importlib.import_module(f"pkg.dispatch.{name}_impl")
            return module
        """,
    )
    _write(repo, "pkg/dispatch/widget_impl.py", "VALUE = 1\n")
    # top-level conftest (high-level — whole suite)
    _write(repo, "tests/conftest.py", "")
    # leaf-level conftest (subtree only)
    _write(repo, "tests/family_a/conftest.py", "")
    _write(
        repo,
        "tests/family_a/test_family_a_thing.py",
        """
        def test_thing():
            assert True
        """,
    )
    _write(
        repo,
        "tests/test_mid.py",
        """
        from pkg.mid import mid_fn

        def test_mid_fn():
            assert mid_fn() == 2
        """,
    )
    _write(repo, "workspace-manifest.json", "{}")
    _write(repo, "pkg/broken.py", "def f(:\n")
    return repo


def _write_allowlist(tmp_path: Path) -> Path:
    allowlist = {
        "repos": {
            "fixture-repo": {
                "dynamic_dispatch_paths": [
                    {"path": "pkg/dispatch/", "verified_at": "pkg/dispatch/__init__.py:1"},
                ],
            },
        },
        "cross_cutting_manifests": ["workspace-manifest.json"],
    }
    path = tmp_path / "allowlist.yaml"
    _ = path.write_text(yaml.safe_dump(allowlist))
    return path


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    return _make_fixture_repo(tmp_path)


@pytest.fixture
def allowlist(tmp_path: Path) -> dict[str, object]:
    path = _write_allowlist(tmp_path)
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(raw, dict)
    return raw


# ── Safe case: narrows correctly ─────────────────────────────────────────────


def test_self_contained_change_narrows_to_the_dependent_test(repo: Path, allowlist: dict[str, object]) -> None:
    result = classify_diff(repo, "fixture-repo", [repo / "pkg/base.py"], allowlist)
    assert result.run_full_suite is False
    assert result.narrowed_test_files == {repo / "tests/test_mid.py"}


# ── Escape hatch: high-level conftest.py ────────────────────────────────────


def test_high_level_conftest_forces_full_suite(repo: Path, allowlist: dict[str, object]) -> None:
    result = classify_diff(repo, "fixture-repo", [repo / "tests/conftest.py"], allowlist)
    assert result.run_full_suite is True
    assert "high-level conftest" in result.reason


# ── Escape hatch: leaf-level conftest.py — subtree only, NOT full suite ─────


def test_leaf_level_conftest_narrows_to_its_subtree(repo: Path, allowlist: dict[str, object]) -> None:
    result = classify_diff(repo, "fixture-repo", [repo / "tests/family_a/conftest.py"], allowlist)
    assert result.run_full_suite is False
    assert result.narrowed_test_files == {repo / "tests/family_a/test_family_a_thing.py"}


# ── Escape hatch: cross-cutting manifest ────────────────────────────────────


def test_cross_cutting_manifest_forces_full_suite(repo: Path, allowlist: dict[str, object]) -> None:
    result = classify_diff(repo, "fixture-repo", [repo / "workspace-manifest.json"], allowlist)
    assert result.run_full_suite is True
    assert "cross-cutting manifest" in result.reason


# ── Escape hatch: verified dynamic-dispatch allowlist path ──────────────────


def test_verified_dynamic_dispatch_path_forces_full_suite(repo: Path, allowlist: dict[str, object]) -> None:
    result = classify_diff(repo, "fixture-repo", [repo / "pkg/dispatch/widget_impl.py"], allowlist)
    assert result.run_full_suite is True
    assert "dynamic-dispatch" in result.reason


# ── Escape hatch: unclassified dynamic dispatch (fail-closed even if the
# allowlist hasn't been told about it yet) ──────────────────────────────────


def test_unallowlisted_dynamic_dispatch_still_fails_closed(tmp_path: Path, allowlist: dict[str, object]) -> None:
    repo = _make_fixture_repo(tmp_path)
    surprise = _write(
        repo,
        "pkg/surprise_dispatch.py",
        """
        import importlib

        def load(name):
            return importlib.import_module(name)
        """,
    )
    result = classify_diff(repo, "fixture-repo", [surprise], allowlist)
    assert result.run_full_suite is True
    assert "unallowlisted dynamic-dispatch" in result.reason


# ── Escape hatch: unparseable file ───────────────────────────────────────────


def test_unparseable_changed_file_forces_full_suite(repo: Path, allowlist: dict[str, object]) -> None:
    result = classify_diff(repo, "fixture-repo", [repo / "pkg/broken.py"], allowlist)
    assert result.run_full_suite is True
    assert "cannot parse" in result.reason


# ── Escape hatch: shared-dependency repo (UTL/UAC) — always full suite ─────


def test_shared_dependency_repo_always_full_suite(repo: Path, allowlist: dict[str, object]) -> None:
    result = classify_diff(repo, "unified-trading-library", [repo / "pkg/base.py"], allowlist)
    assert result.run_full_suite is True
    assert "shared-dependency repo" in result.reason


# ── No changed files ─────────────────────────────────────────────────────────


def test_no_changed_files_does_not_run_full_suite(repo: Path, allowlist: dict[str, object]) -> None:
    result = classify_diff(repo, "fixture-repo", [], allowlist)
    assert result.run_full_suite is False
    assert result.narrowed_test_files == frozenset()
