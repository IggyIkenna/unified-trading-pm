# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""Unit tests for reconcile_release_tags.py's STALL Slack-routing + self-audit (2026-08-02).

Pins: a synthetic stall produces exactly one alert block naming the repo(s) + staleness; a
no-stall run produces no block; a prev-stalled repo that clears (and was affirmatively
re-measured, not merely unmeasured) produces exactly one RESOLVED block; an unmeasured repo is
carried forward and never treated as cleared; and the all-repos-unreadable degenerate case is a
hard FATAL, not a quiet zero-work success (the exact silent-failure class the source doc named).
"""

from __future__ import annotations

import json
from pathlib import Path

import reconcile_release_tags as rrt

# ── _build_stall_block ───────────────────────────────────────────────────────────


def test_no_stall_produces_no_block() -> None:
    assert rrt._build_stall_block({}) == ""


def test_synthetic_multi_repo_stall_produces_exactly_one_block_naming_repos() -> None:
    stalled = {
        "repo-a": "3 unreleased commit(s) on main; newest tag v1.0.0 is 5.0d old",
        "repo-b": "1 unreleased commit(s) on main; newest tag v2.0.0 is 4.0d old",
    }
    block = rrt._build_stall_block(stalled)
    lines = block.split("\n")
    assert lines[0] == rrt._STALL_DEDUP_KEY  # stable dedup key on line 1
    message = lines[1]
    # ONE alert, not one per repo: both repos named in the SAME message body.
    assert "repo-a" in message
    assert "repo-b" in message
    assert "5.0d old" in message
    assert "4.0d old" in message
    assert message.count("RELEASE TAG STALL") == 1


# ── clear-diff (state persistence + cleared block) ───────────────────────────────


def test_state_round_trip(tmp_path: Path) -> None:
    path = str(tmp_path / "state.json")
    rrt._write_state(path, {"repo-a": "was stalled"})
    assert rrt._load_state(path) == {"repo-a": "was stalled"}


def test_load_missing_state_is_empty() -> None:
    assert rrt._load_state("/nonexistent/path/state.json") == {}


def test_load_corrupt_state_is_empty(tmp_path: Path) -> None:
    path = tmp_path / "state.json"
    path.write_text("not json{{{", encoding="utf-8")
    assert rrt._load_state(str(path)) == {}


def test_repo_that_clears_produces_exactly_one_resolved_block(tmp_path: Path) -> None:
    state_in = str(tmp_path / "in.json")
    state_out = str(tmp_path / "out.json")
    cleared_out = str(tmp_path / "cleared.txt")
    rrt._write_state(state_in, {"repo-a": "3 unreleased commit(s)..."})

    # This run: repo-a is affirmatively healthy now (not in `stalled`, not in `unresolved`).
    rrt._emit_stall_clear_diff({}, set(), state_in, state_out, cleared_out)

    block = Path(cleared_out).read_text(encoding="utf-8")
    lines = block.split("\n")
    assert lines[0].startswith(f"{rrt._STALL_DEDUP_KEY}-cleared:")
    assert "repo-a" in lines[1]
    assert "STALL CLEARED" in lines[1]
    # State carries forward as empty (nothing stalled, nothing unresolved).
    assert json.loads(Path(state_out).read_text(encoding="utf-8")) == {"stalled": {}}


def test_no_stall_transition_produces_no_cleared_block(tmp_path: Path) -> None:
    state_in = str(tmp_path / "in.json")
    state_out = str(tmp_path / "out.json")
    cleared_out = str(tmp_path / "cleared.txt")
    rrt._write_state(state_in, {})  # nothing was stalled last run

    rrt._emit_stall_clear_diff({}, set(), state_in, state_out, cleared_out)

    assert Path(cleared_out).read_text(encoding="utf-8") == ""  # 0-byte == cleared=false


def test_unmeasured_repo_is_carried_forward_never_treated_as_cleared(tmp_path: Path) -> None:
    """A transient API-miss this run must NOT masquerade as a clear (mirrors
    promotion_lag_monitor.py's `_cleared_keys` unmeasured-exclusion)."""
    state_in = str(tmp_path / "in.json")
    state_out = str(tmp_path / "out.json")
    cleared_out = str(tmp_path / "cleared.txt")
    rrt._write_state(state_in, {"repo-a": "3 unreleased commit(s)..."})

    # repo-a's compare probe failed this run (API miss) — NOT affirmatively healthy.
    rrt._emit_stall_clear_diff({}, {"repo-a"}, state_in, state_out, cleared_out)

    assert Path(cleared_out).read_text(encoding="utf-8") == ""  # no false clear
    # repo-a is carried forward into the persisted state, not dropped.
    assert json.loads(Path(state_out).read_text(encoding="utf-8")) == {
        "stalled": {"repo-a": "3 unreleased commit(s)..."}
    }


def test_still_stalled_repo_not_double_counted_as_cleared(tmp_path: Path) -> None:
    state_in = str(tmp_path / "in.json")
    state_out = str(tmp_path / "out.json")
    cleared_out = str(tmp_path / "cleared.txt")
    rrt._write_state(state_in, {"repo-a": "was stalled", "repo-b": "was stalled"})

    # repo-a clears; repo-b is still stalled this run.
    rrt._emit_stall_clear_diff({"repo-b": "still stalled"}, set(), state_in, state_out, cleared_out)

    block = Path(cleared_out).read_text(encoding="utf-8")
    assert "repo-a" in block
    assert "repo-b" not in block.split("\n")[1]  # only repo-a named in the cleared line
    assert "1 repo(s) still stalled" in block


def test_cleared_dedup_key_distinct_per_set() -> None:
    key_a = rrt._cleared_dedup_key(["repo-a"])
    key_b = rrt._cleared_dedup_key(["repo-a", "repo-b"])
    assert key_a != key_b  # distinct clear-sets each get their own dedup lane


# ── self-audit: all-repos-unreadable is FATAL, not a quiet success ───────────────


def test_reconcile_fails_when_every_considered_repo_is_unreadable(tmp_path: Path, monkeypatch) -> None:
    manifest = {"repositories": {"repo-a": {}, "repo-b": {}}}
    mpath = tmp_path / "workspace-manifest.json"
    mpath.write_text(json.dumps(manifest), encoding="utf-8")

    # Simulate a broken GH_TOKEN: every repo's main pyproject read fails.
    monkeypatch.setattr(rrt, "_main_pyproject", lambda owner, repo: None)

    rc = rrt.reconcile("IggyIkenna", mpath, dry_run=True, max_creates=0, fail_on_stall=False)
    assert rc == 1  # FATAL regardless of --fail-on-stall — this is a broken check, not a stall verdict


def test_reconcile_succeeds_when_only_some_repos_unreadable(tmp_path: Path, monkeypatch) -> None:
    """A UI/archived repo genuinely having no pyproject is normal, NOT the broken-lookup signal —
    only ALL-considered-repos-unreadable is fatal."""
    manifest = {"repositories": {"repo-a": {}, "repo-b": {}}}
    mpath = tmp_path / "workspace-manifest.json"
    mpath.write_text(json.dumps(manifest), encoding="utf-8")

    def _fake(owner: str, repo: str) -> str | None:
        return None if repo == "repo-a" else 'dynamic = ["version"]\n[tool.hatch.version]\nsource = "vcs"\n'

    monkeypatch.setattr(rrt, "_main_pyproject", _fake)
    monkeypatch.setattr(rrt, "_highest_existing_tag", lambda owner, repo: ((1, 0, 0), True))
    monkeypatch.setattr(rrt, "_commits_ahead_of_tag", lambda owner, repo, tag: 0)
    monkeypatch.setattr(rrt, "_newest_tag_age_days", lambda owner, repo, tag: 0.5)

    rc = rrt.reconcile("IggyIkenna", mpath, dry_run=True, max_creates=0, fail_on_stall=False)
    assert rc == 0


# ── _reconcile_dynamic_repo: API failure must never read as "confirmed zero tags" ─────────────
# (2026-08-12, deployment_api_release_tag_stall_false_positive_2026_08_12.md): a transient
# `gh api repos/.../tags` failure was misclassified as "dynamic versioning but NO v* tag exists
# at all" — a false CRITICAL for a repo that had a brand-new tag pushed 32 minutes earlier.


def test_dynamic_repo_api_failure_is_unresolved_not_stalled(monkeypatch) -> None:
    monkeypatch.setattr(rrt, "_highest_existing_tag", lambda owner, repo: (None, False))
    bucket, tag_ref, detail = rrt._reconcile_dynamic_repo("IggyIkenna", "deployment-api")
    assert bucket == "unresolved"
    assert tag_ref == ""
    assert detail == ""


def test_dynamic_repo_confirmed_zero_tags_is_still_stalled(monkeypatch) -> None:
    monkeypatch.setattr(rrt, "_highest_existing_tag", lambda owner, repo: (None, True))
    bucket, _tag_ref, detail = rrt._reconcile_dynamic_repo("IggyIkenna", "deployment-api")
    assert bucket == "stalled"
    assert detail == "dynamic versioning but NO v* tag exists at all"
