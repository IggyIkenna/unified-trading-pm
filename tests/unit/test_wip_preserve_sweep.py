"""Tests for scripts/dev/wip_preserve_sweep.py
(wip_preserve_refs_silently_unrecovered_2026_07_29.md, `[SCRIPT] P1` todo 1).

Exercises the real git subprocess paths against synthetic bare-remote repos — same
pattern as agent-orchestrator's tests/test_orphan_still_orphaned_verifier.py.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts" / "dev"))

from wip_preserve_sweep import (
    discover_all_clones,
    discover_repo_representatives,
    sweep_local_clone,
    sweep_remote_repo,
)

BASE = "live-defi-rollout"


def _git(repo: Path, *args: str) -> str:
    res = subprocess.run(
        ["git", "-c", "safe.bareRepository=all", *args],
        cwd=str(repo),
        capture_output=True,
        text=True,
        check=True,
    )
    return res.stdout.strip()


def _init_seeded_clone(tmp_path: Path, name: str) -> tuple[Path, Path]:
    bare = tmp_path / f"{name}.git"
    bare.mkdir(parents=True, exist_ok=True)
    _git(bare, "init", "--bare", "-b", BASE)

    clone = tmp_path / name
    clone.mkdir(parents=True, exist_ok=True)
    _git(clone, "init", "-b", BASE)
    _git(clone, "config", "user.email", "test@odum.dev")
    _git(clone, "config", "user.name", "test")
    (clone / "file.txt").write_text("seed\n")
    _git(clone, "add", "-A")
    _git(clone, "commit", "-m", "seed")
    _git(clone, "remote", "add", "origin", str(bare))
    _git(clone, "push", "-u", "origin", BASE)
    return clone, bare


def _push_wip_preserve_branch(clone: Path, branch: str, *, content: str) -> str:
    """Commit on a detached throwaway branch and push it under refs/heads/wip-preserve/,
    without moving the clone's own checked-out branch."""
    start = _git(clone, "rev-parse", "HEAD")
    _git(clone, "checkout", "--detach", start)
    (clone / "wip.txt").write_text(content)
    _git(clone, "add", "-A")
    _git(clone, "commit", "-m", f"wip: {branch}")
    sha = _git(clone, "rev-parse", "HEAD")
    _git(clone, "push", "origin", f"HEAD:refs/heads/{branch}")
    _git(clone, "checkout", BASE)
    return sha


# --------------------------------------------------------------------------
# sweep_remote_repo
# --------------------------------------------------------------------------


def test_remote_branch_ancestor_reports_would_delete_in_dry_run(tmp_path: Path) -> None:
    clone, _bare = _init_seeded_clone(tmp_path, "repo_a")
    sha = _push_wip_preserve_branch(clone, "wip-preserve/orchestrator-slot-1-abc123", content="preserved work\n")
    # fast-forward the base branch to literally include that same commit sha —
    # the only way the wip-preserve branch's tip becomes a real ancestor
    _git(clone, "merge", "--ff-only", sha)
    _git(clone, "push", "origin", BASE)

    results = sweep_remote_repo(clone, base_branch=BASE, apply=False)
    assert len(results) == 1
    assert results[0].sha == sha
    assert results[0].is_ancestor is True
    assert results[0].action == "would-delete"

    # dry-run must not have touched the remote branch
    ls = _git(clone, "ls-remote", "--heads", "origin", "refs/heads/wip-preserve/*")
    assert "wip-preserve/orchestrator-slot-1-abc123" in ls


def test_remote_branch_ancestor_deleted_with_apply(tmp_path: Path) -> None:
    clone, _bare = _init_seeded_clone(tmp_path, "repo_b")
    sha = _push_wip_preserve_branch(clone, "wip-preserve/orchestrator-slot-2-def456", content="preserved work\n")
    _git(clone, "merge", "--ff-only", sha)
    _git(clone, "push", "origin", BASE)

    results = sweep_remote_repo(clone, base_branch=BASE, apply=True)
    assert len(results) == 1
    assert results[0].action == "deleted"

    ls = _git(clone, "ls-remote", "--heads", "origin", "refs/heads/wip-preserve/*")
    assert "wip-preserve/orchestrator-slot-2-def456" not in ls


def test_remote_branch_not_ancestor_is_reported_never_touched(tmp_path: Path) -> None:
    clone, _bare = _init_seeded_clone(tmp_path, "repo_c")
    _push_wip_preserve_branch(clone, "wip-preserve/orchestrator-slot-3-ghi789", content="never landed anywhere\n")
    # base branch advances WITHOUT the preserved content ever landing
    (clone / "other.txt").write_text("unrelated work\n")
    _git(clone, "add", "-A")
    _git(clone, "commit", "-m", "unrelated")
    _git(clone, "push", "origin", BASE)

    results = sweep_remote_repo(clone, base_branch=BASE, apply=True)
    assert len(results) == 1
    assert results[0].is_ancestor is False
    assert results[0].action == "reported"

    ls = _git(clone, "ls-remote", "--heads", "origin", "refs/heads/wip-preserve/*")
    assert "wip-preserve/orchestrator-slot-3-ghi789" in ls


def test_remote_sweep_no_branches_returns_empty(tmp_path: Path) -> None:
    clone, _bare = _init_seeded_clone(tmp_path, "repo_d")
    assert sweep_remote_repo(clone, base_branch=BASE, apply=False) == []


def test_remote_sweep_cleans_up_temp_refs(tmp_path: Path) -> None:
    clone, _bare = _init_seeded_clone(tmp_path, "repo_e")
    _push_wip_preserve_branch(clone, "wip-preserve/cascade-repo_e-aaa111", content="x\n")

    sweep_remote_repo(clone, base_branch=BASE, apply=False)

    leftover = _git(clone, "for-each-ref", "--format=%(refname)", "refs/wip-preserve-sweep-tmp/")
    assert leftover == ""


# --------------------------------------------------------------------------
# sweep_local_clone
# --------------------------------------------------------------------------


def test_local_sweep_finds_cascade_ref_never_touches_it(tmp_path: Path) -> None:
    clone, _bare = _init_seeded_clone(tmp_path, "repo_f")
    (clone / "local.txt").write_text("local-only work\n")
    _git(clone, "add", "-A")
    _git(clone, "commit", "-m", "local-only wip")
    sha = _git(clone, "rev-parse", "HEAD")
    _git(clone, "reset", "--hard", "HEAD~1")  # simulate quickmerge's cascade_dep_branch: commit exists
    _git(clone, "update-ref", "refs/wip-preserve/cascade-repo_f-aaa111", sha)

    results = sweep_local_clone(clone)
    assert len(results) == 1
    assert results[0].ref == "refs/wip-preserve/cascade-repo_f-aaa111"
    assert results[0].sha == sha

    # never pushed, never deleted — purely local and untouched
    ls = _git(clone, "ls-remote", "origin", "refs/wip-preserve/*")
    assert ls == ""
    still_there = _git(clone, "for-each-ref", "--format=%(refname)", "refs/wip-preserve/cascade-*")
    assert "refs/wip-preserve/cascade-repo_f-aaa111" in still_there


def test_local_sweep_no_refs_returns_empty(tmp_path: Path) -> None:
    clone, _bare = _init_seeded_clone(tmp_path, "repo_g")
    assert sweep_local_clone(clone) == []


# --------------------------------------------------------------------------
# discovery helpers
# --------------------------------------------------------------------------


def test_discover_repo_representatives_prefers_root_clone(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    root_clone, _ = _init_seeded_clone(workspace, "svc")
    tabs = workspace / ".tabs" / "3"
    tabs.mkdir(parents=True)
    slot_clone, _ = _init_seeded_clone(tabs, "svc")

    reps = discover_repo_representatives(workspace)
    assert reps["svc"] == root_clone
    assert reps["svc"] != slot_clone


def test_discover_repo_representatives_falls_back_to_slot_clone(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    tabs = workspace / ".tabs" / "3"
    tabs.mkdir(parents=True)
    slot_clone, _ = _init_seeded_clone(tabs, "svc")

    reps = discover_repo_representatives(workspace)
    assert reps["svc"] == slot_clone


def test_discover_all_clones_covers_root_and_every_slot(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _root_clone, bare = _init_seeded_clone(workspace, "svc")
    tabs3 = workspace / ".tabs" / "3"
    tabs3.mkdir(parents=True)
    _git(tabs3, "clone", str(bare), "svc")
    tabs7 = workspace / ".tabs" / "7"
    tabs7.mkdir(parents=True)
    _git(tabs7, "clone", str(bare), "svc")

    clones = discover_all_clones(workspace)
    names_and_parents = {(c.name, c.parent.name) for c in clones}
    assert ("svc", "workspace") in names_and_parents
    assert ("svc", "3") in names_and_parents
    assert ("svc", "7") in names_and_parents
    assert len(clones) == 3


def test_discover_helpers_missing_workspace_root_returns_empty(tmp_path: Path) -> None:
    missing = tmp_path / "does-not-exist"
    assert discover_repo_representatives(missing) == {}
    assert discover_all_clones(missing) == []
