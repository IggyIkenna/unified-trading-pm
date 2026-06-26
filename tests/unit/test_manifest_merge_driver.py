"""Unit tests for scripts/cicd/manifest_merge_driver.py.

Covers the deterministic conflict classes the driver must resolve during the version-bump
rebase-retry push loop, and the fail-safe escalation on genuine non-version divergence.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

_DRIVER_PATH = Path(__file__).resolve().parents[2] / "scripts" / "cicd" / "manifest_merge_driver.py"
_spec = importlib.util.spec_from_file_location("manifest_merge_driver", _DRIVER_PATH)
assert _spec and _spec.loader
mmd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mmd)


def _merge(base: dict, ours: dict, theirs: dict) -> tuple[dict, bool]:
    return mmd.merge3(base, ours, theirs)


def test_disjoint_version_keys_both_kept() -> None:
    base = {"versions": {"a": "1.0.0", "b": "1.0.0"}}
    ours = {"versions": {"a": "1.1.0", "b": "1.0.0"}}
    theirs = {"versions": {"a": "1.0.0", "b": "1.2.0"}}
    merged, conflict = _merge(base, ours, theirs)
    assert conflict is False
    assert merged["versions"] == {"a": "1.1.0", "b": "1.2.0"}


def test_same_key_both_bumped_max_semver_wins() -> None:
    base = {"versions": {"a": "1.2.0"}}
    ours = {"versions": {"a": "1.2.543"}}
    theirs = {"versions": {"a": "1.2.544"}}
    merged, conflict = _merge(base, ours, theirs)
    assert conflict is False
    assert merged["versions"]["a"] == "1.2.544"


def test_semver_numeric_not_lexical() -> None:
    base = {"versions": {"a": "0.9.0"}}
    ours = {"versions": {"a": "0.9.0"}}
    theirs = {"versions": {"a": "0.10.0"}}
    merged, _ = _merge(base, ours, theirs)
    assert merged["versions"]["a"] == "0.10.0"


def test_breaking_pending_list_unioned() -> None:
    base = {"staging_status": {"breaking_pending": ["x"]}}
    ours = {"staging_status": {"breaking_pending": ["x", "y"]}}
    theirs = {"staging_status": {"breaking_pending": ["x", "z"]}}
    merged, conflict = _merge(base, ours, theirs)
    assert conflict is False
    assert merged["staging_status"]["breaking_pending"] == ["x", "y", "z"]


def test_one_side_unchanged_takes_other() -> None:
    base = {"versions": {"a": "1.0.0"}, "staging_versions": {"a": "1.0.0"}}
    ours = {"versions": {"a": "1.0.0"}, "staging_versions": {"a": "1.1.0"}}
    theirs = {"versions": {"a": "1.0.0"}, "staging_versions": {"a": "1.0.0"}}
    merged, conflict = _merge(base, ours, theirs)
    assert conflict is False
    assert merged["staging_versions"]["a"] == "1.1.0"


def test_genuine_nonversion_conflict_escalates() -> None:
    base = {"staging_status": {"locked_reason": "none"}}
    ours = {"staging_status": {"locked_reason": "major bump a"}}
    theirs = {"staging_status": {"locked_reason": "major bump b"}}
    _, conflict = _merge(base, ours, theirs)
    assert conflict is True


def test_new_key_added_by_one_side_kept() -> None:
    base = {"versions": {"a": "1.0.0"}}
    ours = {"versions": {"a": "1.0.0"}, "staging_commits": {"a": {"version": "1.1.0"}}}
    theirs = {"versions": {"a": "1.1.0"}}
    merged, conflict = _merge(base, ours, theirs)
    assert conflict is False
    assert merged["versions"]["a"] == "1.1.0"
    assert merged["staging_commits"] == {"a": {"version": "1.1.0"}}


def test_deletion_honored_when_other_side_unchanged() -> None:
    base = {"versions": {"a": "1.0.0", "stale": "0.1.0"}}
    ours = {"versions": {"a": "1.1.0", "stale": "0.1.0"}}
    theirs = {"versions": {"a": "1.0.0"}}  # theirs deleted "stale"
    merged, conflict = _merge(base, ours, theirs)
    assert conflict is False
    assert "stale" not in merged["versions"]
    assert merged["versions"]["a"] == "1.1.0"


def test_end_to_end_files(tmp_path: Path) -> None:
    base = tmp_path / "base.json"
    ours = tmp_path / "ours.json"
    theirs = tmp_path / "theirs.json"
    base.write_text(json.dumps({"versions": {"a": "1.2.0", "b": "1.0.0"}}))
    ours.write_text(json.dumps({"versions": {"a": "1.2.543", "b": "1.0.0"}}))
    theirs.write_text(json.dumps({"versions": {"a": "1.2.544", "b": "1.1.0"}}))
    # Invoke main() via an argv shim (git calls the driver as `driver %O %A %B`).
    import sys

    argv = sys.argv
    try:
        sys.argv = ["manifest_merge_driver.py", str(base), str(ours), str(theirs)]
        assert mmd.main() == 0
    finally:
        sys.argv = argv
    result = json.loads(ours.read_text())
    assert result["versions"] == {"a": "1.2.544", "b": "1.1.0"}
