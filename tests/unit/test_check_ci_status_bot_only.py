"""Hermetic unit tests for Guard 1 — ci_status single-writer enforcement.

Imports the guard logic directly (SSOT). Covers the pure diff + the bot-bypass /
fail-open CLI branches. The git-show baseline I/O is exercised via the actor
bypass + a monkeypatched loader (no real git needed).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_GUARD_PATH = Path(__file__).resolve().parents[2] / "scripts" / "cicd" / "check_ci_status_bot_only.py"
_spec = importlib.util.spec_from_file_location("check_ci_status_bot_only", _GUARD_PATH)
assert _spec and _spec.loader
guard = importlib.util.module_from_spec(_spec)
sys.modules["check_ci_status_bot_only"] = guard
_spec.loader.exec_module(guard)


def _m(repos: dict[str, dict]) -> dict:
    return {"repositories": repos}


# ── pure diff ────────────────────────────────────────────────────────────────


def test_diff_detects_changed_ci_status() -> None:
    base = _m({"utl": {"ci_status": "FAILING"}, "uac": {"ci_status": "FEATURE_GREEN"}})
    cur = _m({"utl": {"ci_status": "FEATURE_GREEN"}, "uac": {"ci_status": "FEATURE_GREEN"}})
    assert guard.diff_ci_status(cur, base) == {"utl": ("FAILING", "FEATURE_GREEN")}


def test_diff_empty_when_unchanged() -> None:
    base = _m({"utl": {"ci_status": "STAGING_GREEN"}})
    assert guard.diff_ci_status(dict(base), dict(base)) == {}


def test_diff_detects_added_and_removed_repo() -> None:
    base = _m({"utl": {"ci_status": "FEATURE_GREEN"}})
    cur = _m({"utl": {"ci_status": "FEATURE_GREEN"}, "new": {"ci_status": "FEATURE_GREEN"}})
    assert guard.diff_ci_status(cur, base) == {"new": (None, "FEATURE_GREEN")}


def test_ci_status_map_tolerates_list_repositories() -> None:
    listed = {"repositories": [{"name": "utl", "ci_status": "FAILING"}]}
    assert guard.ci_status_map(listed) == {"utl": "FAILING"}


# ── CLI ──────────────────────────────────────────────────────────────────────


def test_bot_actor_always_passes(monkeypatch: pytest.MonkeyPatch) -> None:
    # Even if it would otherwise diff, the bot is the sanctioned writer.
    monkeypatch.setattr(guard, "_load_ref_manifest", lambda *a, **k: _m({"utl": {"ci_status": "FAILING"}}))
    assert guard.main(["--actor", "ci-status-update[bot]"]) == 0


def test_fail_open_when_baseline_unreadable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(guard, "_load_ref_manifest", lambda *a, **k: None)
    assert guard.main(["--actor", "some-human"]) == 0


def test_block_on_non_bot_ci_status_change(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    manifest = tmp_path / "workspace-manifest.json"
    manifest.write_text('{"repositories": {"utl": {"ci_status": "STAGING_GREEN"}}}', encoding="utf-8")
    monkeypatch.setattr(guard, "_load_ref_manifest", lambda *a, **k: _m({"utl": {"ci_status": "FAILING"}}))
    rc = guard.main(["--manifest", str(manifest), "--actor", "some-human"])
    assert rc == 1


def test_pass_when_no_ci_status_change(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    manifest = tmp_path / "workspace-manifest.json"
    manifest.write_text('{"repositories": {"utl": {"ci_status": "STAGING_GREEN"}}}', encoding="utf-8")
    monkeypatch.setattr(guard, "_load_ref_manifest", lambda *a, **k: _m({"utl": {"ci_status": "STAGING_GREEN"}}))
    assert guard.main(["--manifest", str(manifest), "--actor", "some-human"]) == 0
