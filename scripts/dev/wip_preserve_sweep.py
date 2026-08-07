#!/usr/bin/env python3
# Epic: orchestrator_master
# Lifecycle: permanent
# Delete-when: NA
"""Daily fleet-wide `refs/wip-preserve/**` sweep
(wip_preserve_refs_silently_unrecovered_2026_07_29.md, `[SCRIPT] P1` todo 1 — operator
rulings 2026-08-06).

Two ref namespaces exist and are NOT interchangeable (the AO code documents the split at
``agent-orchestrator/server/worktree_clean_check/_orphan_verify.py:258-264``):

  - **Remote tier** (``refs/heads/wip-preserve/*``) — pushed branches, durable and visible
    from any clone of a repo. Measured 2026-08-06: 1,912 branches across 25 repos, none ever
    cleaned up. Runnable from a SINGLE representative clone per repo (remote state is shared).
    For each branch: if its tip is an ancestor of ``origin/<base_branch>``, the commit stays
    reachable via the base branch — deleting the backup branch cannot lose anything by
    construction, so it is auto-deleted with ``--apply``. Not an ancestor -> reported, NEVER
    touched (see the "wolf-crying trap" in the source doc: an aged ref can be safely
    superseded by DIFFERENT-sha content a human already re-shipped, which this script does
    not attempt to detect — it only proves the cheap, unambiguous side of the decision).

  - **Local-only tier** (``refs/wip-preserve/cascade-*``) — created by
    ``quickmerge.sh``'s ``cascade_dep_branch()`` via ``git update-ref``, NEVER pushed. Only 3
    found across 81 scanned clones on 2026-08-06, but this is the dangerous tier: invisible to
    every other host, destroyed with the clone. Must be checked on EVERY clone individually
    (no single representative). This script only REPORTS this tier — rescuing it (pushing to
    the durable namespace before it can be lost) is a separate todo
    (``wip_preserve_refs_silently_unrecovered_2026_07_29.md``'s sibling `[SCRIPT] P1`).

Read-only by default. Pass ``--apply`` to actually delete ancestor-proven remote branches —
without it, every action is reported as ``would-delete``/``reported`` and nothing is mutated.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

_LS_REMOTE_TIMEOUT_S = 30
_FETCH_TIMEOUT_S = 120
_GIT_TIMEOUT_S = 15
_TEMP_REF_PREFIX = "refs/wip-preserve-sweep-tmp"


def _run(args: list[str], cwd: Path, *, timeout: int = _GIT_TIMEOUT_S) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=str(cwd), capture_output=True, text=True, check=False, timeout=timeout)


@dataclass(frozen=True)
class RemoteBranchResult:
    repo: str
    branch: str
    sha: str
    is_ancestor: bool
    action: str  # "deleted" | "delete-failed" | "would-delete" | "reported"

    def as_dict(self) -> dict[str, object]:
        return {
            "repo": self.repo,
            "branch": self.branch,
            "sha": self.sha,
            "is_ancestor": self.is_ancestor,
            "action": self.action,
        }


@dataclass(frozen=True)
class LocalRefResult:
    repo: str
    clone: str
    ref: str
    sha: str

    def as_dict(self) -> dict[str, object]:
        return {"repo": self.repo, "clone": self.clone, "ref": self.ref, "sha": self.sha}


@dataclass
class SweepReport:
    remote: list[RemoteBranchResult] = field(default_factory=list)
    local: list[LocalRefResult] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def deleted_count(self) -> int:
        return sum(1 for r in self.remote if r.action == "deleted")

    @property
    def would_delete_count(self) -> int:
        return sum(1 for r in self.remote if r.action == "would-delete")

    @property
    def needs_review_count(self) -> int:
        """Genuinely-orphaned remote branches (never auto-touched) + every local-only ref
        (never auto-touched by this script, ever) — the set a human should actually look at."""
        return sum(1 for r in self.remote if not r.is_ancestor) + len(self.local)

    def as_dict(self) -> dict[str, object]:
        return {
            "remote": {
                "total_branches": len(self.remote),
                "deleted": self.deleted_count,
                "would_delete": self.would_delete_count,
                "needs_review": sum(1 for r in self.remote if not r.is_ancestor),
                "results": [r.as_dict() for r in self.remote],
            },
            "local": {
                "total_refs": len(self.local),
                "results": [r.as_dict() for r in self.local],
            },
            "errors": self.errors,
            "needs_review_count": self.needs_review_count,
        }


def discover_repo_representatives(workspace_root: Path) -> dict[str, Path]:
    """One clone per repo name — the root canonical clone when present, else the first
    ``.tabs/*/<repo>`` clone found. Remote branch state is shared across every clone of the
    same repo, so the remote sweep only ever needs to touch ONE."""
    reps: dict[str, Path] = {}
    if not workspace_root.is_dir():
        return reps
    for child in sorted(workspace_root.iterdir()):
        if child.is_dir() and child.name != ".tabs" and (child / ".git").exists():
            reps[child.name] = child
    tabs = workspace_root / ".tabs"
    if tabs.is_dir():
        for slot_dir in sorted(tabs.iterdir()):
            if not slot_dir.is_dir():
                continue
            for repo_dir in sorted(slot_dir.iterdir()):
                if repo_dir.is_dir() and (repo_dir / ".git").exists():
                    reps.setdefault(repo_dir.name, repo_dir)
    return reps


def discover_all_clones(workspace_root: Path) -> list[Path]:
    """Every repo clone this host can see — root canonical clones AND every
    ``.tabs/*/<repo>`` slot clone. Local-only ``cascade-*`` refs are per-clone (created via a
    local-only ``git update-ref``, never pushed), so unlike the remote tier there is no single
    representative — every clone must be checked individually."""
    clones: list[Path] = []
    if not workspace_root.is_dir():
        return clones
    for child in sorted(workspace_root.iterdir()):
        if child.is_dir() and child.name != ".tabs" and (child / ".git").exists():
            clones.append(child)
    tabs = workspace_root / ".tabs"
    if tabs.is_dir():
        for slot_dir in sorted(tabs.iterdir()):
            if not slot_dir.is_dir():
                continue
            for repo_dir in sorted(slot_dir.iterdir()):
                if repo_dir.is_dir() and (repo_dir / ".git").exists():
                    clones.append(repo_dir)
    return clones


def _parse_ls_remote(stdout: str) -> list[tuple[str, str]]:
    branches: list[tuple[str, str]] = []
    for line in stdout.splitlines():
        parts = line.split("\t")
        if len(parts) == 2 and parts[1].strip().startswith("refs/heads/wip-preserve/"):
            branches.append((parts[0].strip(), parts[1].strip()))
    return branches


def sweep_remote_repo(
    repo_path: Path, *, base_branch: str, remote: str = "origin", apply: bool
) -> list[RemoteBranchResult]:
    """Remote-tier sweep for one repo, from one representative clone.

    Fetches every ``refs/heads/wip-preserve/*`` branch's commit object into a throwaway local
    namespace (cleaned up before returning) purely so ``git merge-base --is-ancestor`` has
    something local to check against — never checks out, resets, or mutates the clone's own
    branch/working tree state.
    """
    repo_name = repo_path.name
    ls = _run(
        ["git", "ls-remote", "--heads", remote, "refs/heads/wip-preserve/*"], repo_path, timeout=_LS_REMOTE_TIMEOUT_S
    )
    if ls.returncode != 0:
        raise RuntimeError(f"git ls-remote failed: {ls.stderr.strip()[:200]}")
    branches = _parse_ls_remote(ls.stdout)
    if not branches:
        return []

    fetch_base = _run(["git", "fetch", "--quiet", remote, base_branch], repo_path, timeout=_FETCH_TIMEOUT_S)
    if fetch_base.returncode != 0:
        raise RuntimeError(f"git fetch {remote} {base_branch} failed: {fetch_base.stderr.strip()[:200]}")

    temp_refs: list[str] = []
    refspecs: list[str] = []
    for _sha, ref in branches:
        branch_name = ref[len("refs/heads/") :]
        temp_ref = f"{_TEMP_REF_PREFIX}/{branch_name.replace('/', '-')}"
        temp_refs.append(temp_ref)
        refspecs.append(f"+{ref}:{temp_ref}")
    fetch_branches = _run(["git", "fetch", "--quiet", remote, *refspecs], repo_path, timeout=_FETCH_TIMEOUT_S)
    if fetch_branches.returncode != 0:
        # best-effort: some refspecs may still have resolved even on a partial failure
        # (e.g. one branch deleted between ls-remote and fetch) — proceed and let the
        # per-branch cat-file/merge-base checks below fail individually for those.
        pass

    base_ref = f"{remote}/{base_branch}"
    results: list[RemoteBranchResult] = []
    try:
        for sha, ref in branches:
            branch_name = ref[len("refs/heads/") :]
            temp_ref = f"{_TEMP_REF_PREFIX}/{branch_name.replace('/', '-')}"
            exists = _run(["git", "cat-file", "-e", f"{temp_ref}^{{commit}}"], repo_path)
            if exists.returncode != 0:
                # couldn't materialize the commit object locally — report only, never guess
                results.append(
                    RemoteBranchResult(
                        repo=repo_name, branch=branch_name, sha=sha, is_ancestor=False, action="reported"
                    )
                )
                continue
            ancestor = _run(["git", "merge-base", "--is-ancestor", temp_ref, base_ref], repo_path)
            is_ancestor = ancestor.returncode == 0
            if is_ancestor:
                if apply:
                    delete = _run(["git", "push", remote, "--delete", branch_name], repo_path, timeout=_FETCH_TIMEOUT_S)
                    action = "deleted" if delete.returncode == 0 else "delete-failed"
                else:
                    action = "would-delete"
            else:
                action = "reported"
            results.append(
                RemoteBranchResult(repo=repo_name, branch=branch_name, sha=sha, is_ancestor=is_ancestor, action=action)
            )
    finally:
        for temp_ref in temp_refs:
            _run(["git", "update-ref", "-d", temp_ref], repo_path)
    return results


def sweep_local_clone(repo_path: Path) -> list[LocalRefResult]:
    """Local-only-tier sweep for one clone: every ``refs/wip-preserve/cascade-*`` ref, reported
    only — this script never deletes or pushes a local-only ref (that is the sibling rescue
    todo's job)."""
    result = _run(
        ["git", "for-each-ref", "--format=%(refname) %(objectname)", "refs/wip-preserve/cascade-*"], repo_path
    )
    if result.returncode != 0:
        return []
    out: list[LocalRefResult] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) != 2:
            continue
        ref, sha = parts
        out.append(LocalRefResult(repo=repo_path.name, clone=str(repo_path), ref=ref, sha=sha))
    return out


def run_sweep(workspace_root: Path, *, base_branch: str, apply: bool) -> SweepReport:
    report = SweepReport()

    for repo_name, repo_path in discover_repo_representatives(workspace_root).items():
        try:
            report.remote.extend(sweep_remote_repo(repo_path, base_branch=base_branch, apply=apply))
        except subprocess.TimeoutExpired:
            report.errors.append(f"{repo_name}: remote sweep timed out")
        except RuntimeError as exc:
            report.errors.append(f"{repo_name}: remote sweep failed ({exc})")

    for clone in discover_all_clones(workspace_root):
        try:
            report.local.extend(sweep_local_clone(clone))
        except subprocess.TimeoutExpired:
            report.errors.append(f"{clone}: local sweep timed out")

    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workspace-root", type=Path, default=Path.home() / "unified-trading-system-repos")
    ap.add_argument("--base-branch", default="live-defi-rollout")
    ap.add_argument(
        "--apply", action="store_true", help="actually delete ancestor-proven remote branches (default: dry-run)"
    )
    ap.add_argument("--json", action="store_true", help="print the machine-readable report to stdout")
    args = ap.parse_args(argv)

    report = run_sweep(args.workspace_root, base_branch=args.base_branch, apply=args.apply)

    summary = report.as_dict()
    summary["generated_at"] = datetime.now(UTC).isoformat()
    summary["base_branch"] = args.base_branch
    summary["apply"] = args.apply

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        mode = "APPLY" if args.apply else "DRY-RUN"
        print(f"==== wip-preserve sweep ({mode}) ====")
        print(
            f"remote: {len(report.remote)} branch(es) — deleted={report.deleted_count} "
            f"would-delete={report.would_delete_count}"
        )
        print(f"local-only: {len(report.local)} ref(s) — reported, never touched")
        print(f"needs review: {report.needs_review_count}")
        if report.errors:
            print(f"errors: {len(report.errors)}")
            for err in report.errors:
                print(f"  ! {err}", file=sys.stderr)

    return 1 if report.needs_review_count > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
