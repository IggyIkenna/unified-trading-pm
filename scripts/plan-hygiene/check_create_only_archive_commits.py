#!/usr/bin/env python3
# Epic: plan_hygiene_master
# Lifecycle: permanent
# Delete-when: NA
"""Create-only archival-commit guard.

Detects the `git commit --only` partial-commit hazard root-caused in
plans/archive/issues/git_commit_only_drops_rename_deletions_create_only_archive_2026_08_06.md (resolved 2026-08-08):
a `git mv plans/active/issues/X.md plans/archive/issues/X.md` followed by
`git commit --only -m "..." -- plans/archive/issues/X.md` commits the ADD side of
the rename but silently EXCLUDES the DELETE side (the old path is not in the
`--only` path list). The archive file lands while the live
`plans/active/issues/X.md` twin survives — the "create-only" shape. The two copies
then diverge (5 live pairs already have, 15-34 diff lines each), and nothing in
the ship path catches it: `check_reference_paths.py` / `find_moved_doc_referrers.sh`
only look forward from the surviving path.

This check hard-fails on ANY `plans/archive/issues/<stem>.md` file whose
`plans/active/issues/<stem>.md` twin ALSO exists in the same revision's tree —
i.e. any surviving create-only duplicate pair, whether just introduced by a bad
commit or carried as pre-existing debt. Run against HEAD it flags the current
corpus (the 5 known duplicates); run with `--commit <sha>` it flags the specific
create-only commit.

Sanctioned fix pointer (the two-path `--only` fix): route the archival commit
through `scripts/dev/safe-doc-push.sh` (plain full-staged-set commit) or, if a
bare `git commit --only` is used, list BOTH old and new paths; then run a
post-commit `git status --porcelain` confirming no staged deletions were left
uncommitted.

Usage:
  python3 scripts/plan-hygiene/check_create_only_archive_commits.py [--quiet] [--rev <rev>]
  python3 scripts/plan-hygiene/check_create_only_archive_commits.py --commit <sha> [--quiet]
Exit 1 if any create-only duplicate pair is detected; 0 otherwise.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PM_DIR = Path(__file__).resolve().parents[2]

FIX_POINTER = (
    "create-only archival commit (git commit --only -- <new-path> dropped the rename delete). "
    "Redo the archival via `scripts/dev/safe-doc-push.sh` (plain full-staged-set commit) or, if a bare "
    "`git commit --only` is used, list BOTH old and new paths; then verify `git status --porcelain` shows "
    "no staged deletions left uncommitted. SSOT: "
    "plans/archive/issues/git_commit_only_drops_rename_deletions_create_only_archive_2026_08_06.md"
)


def _git(*args: str) -> str:
    """Run a read-only git command against the PM repo and return stdout."""
    proc = subprocess.run(
        ["git", "-C", str(PM_DIR), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout


def _rev_tree(rev: str, path: str) -> set[str]:
    """Files under `path` present in the tree of `rev` (archive vs active split done by caller)."""
    out = _git("ls-tree", "-r", "--name-only", rev, "--", path)
    return {line for line in out.splitlines() if line}


def _tree_duplicates(rev: str) -> list[str]:
    """Archive-issue paths at `rev` whose active twin also exists at `rev`."""
    archive = _rev_tree(rev, "plans/archive/issues")
    active = _rev_tree(rev, "plans/active/issues")
    dups: list[str] = []
    for archive_path in sorted(archive):
        twin = archive_path.replace("plans/archive/issues/", "plans/active/issues/", 1)
        if twin in active:
            dups.append(archive_path)
    return dups


def _tree_has(rev: str, path: str) -> bool:
    try:
        _git("cat-file", "-e", f"{rev}:{path}")
        return True
    except RuntimeError:
        return False


def _commit_duplicates(sha: str) -> list[str]:
    """Create-only archive paths added by `sha`: commit added plans/archive/issues/<stem>.md while
    plans/active/issues/<stem>.md existed in the parent AND still exists in the commit tree."""
    parent = sha + "^"
    try:
        _git("rev-parse", "--verify", parent)
    except RuntimeError:
        return []  # root commit: no parent to compare
    diff = _git("diff-tree", "-r", "--name-status", "-M", "--no-commit-id", sha)
    dups: list[str] = []
    for line in diff.splitlines():
        parts = line.split("\t")
        if not parts:
            continue
        status = parts[0]
        if status.startswith("A") and len(parts) >= 2:
            new_path = parts[1]
            if not new_path.startswith("plans/archive/issues/") or not new_path.endswith(".md"):
                continue
            stem = new_path[len("plans/archive/issues/") : -len(".md")]
            twin = f"plans/active/issues/{stem}.md"
            if _tree_has(parent, twin) and _tree_has(sha, twin):
                dups.append(f"{sha} added {new_path} while {twin} survives in the commit tree")
    return dups


def main() -> int:
    quiet = "--quiet" in sys.argv
    commit = ""
    rev = "HEAD"
    args = sys.argv[1:]
    if "--commit" in args:
        idx = args.index("--commit")
        if idx + 1 >= len(args):
            print("check_create_only_archive_commits: --commit requires a <sha> argument", file=sys.stderr)
            return 2
        commit = args[idx + 1]
    elif "--rev" in args:
        idx = args.index("--rev")
        if idx + 1 >= len(args):
            print("check_create_only_archive_commits: --rev requires a <rev> argument", file=sys.stderr)
            return 2
        rev = args[idx + 1]

    violations = _commit_duplicates(commit) if commit else _tree_duplicates(rev)

    if not quiet:
        print("Create-only archival-commit guard:")
        print()
        for v in sorted(violations):
            print(f"  CREATE-ONLY  {v}")
        print()

    if violations:
        print(
            f"❌ check_create_only_archive_commits: {len(violations)} create-only archive/active "
            f"duplicate pair(s) detected. Fix: {FIX_POINTER}"
        )
        return 1

    if not quiet:
        print(f"✅ check_create_only_archive_commits: no create-only archive/active duplicate pairs at {commit or rev}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
