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

This check hard-fails on ANY `plans/archive/**/<stem>.md` file whose active twin
(same basename, anywhere under `plans/active/**`) ALSO exists in the same
revision's tree — i.e. any surviving create-only duplicate pair, whether just
introduced by a bad commit or carried as pre-existing debt. Run against HEAD it
flags the current corpus; run with `--commit <sha>` it flags the specific
create-only commit.

Coverage widened 2026-08-10 (was: `plans/archive/issues/` vs `plans/active/issues/`
only). Real archivals land in DATED directories — `plans/archive/2026_08/issues/X.md`,
`plans/archive/2026_08/X.md` — none of which the original path-substitution matched,
so the guard reported a clean corpus while 10 live duplicate pairs sat on origin,
3 of them still feeding 5 phantom todos into the AO dispatch backlog. Matching by
basename rather than by mirrored path is what closes that hole. Two exemptions keep
the signal honest: `ALLOWED_DUPLICATE_STEMS` (a shrinking ratchet of pre-existing
pairs with recorded verdicts) and redirect stubs (an intentional pair — see
`_is_redirect_stub`).

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

import re
import subprocess
import sys
from pathlib import Path

PM_DIR = Path(__file__).resolve().parents[2]

# SHRINKING RATCHET. Pre-existing duplicate pairs, each with a recorded verdict, carried so that
# widening this guard's path coverage (2026-08-10) does not turn the fleet red on debt it merely
# made visible -- per the "a stricter gate must be one the whole fleet already passes" rule. A pair
# NOT listed here fails immediately, so no NEW duplicate can hide behind a shrinking total. Entries
# are only ever REMOVED (when the pair is genuinely reconciled), never added: if you are about to
# add one, you are papering over a fresh create-only archival instead of fixing it.
#
# Per-pair verdicts and the reconciliation plan live in
# plans/active/issues/safe_doc_push_isolation_drops_rename_deletions_2026_08_10.md § "Full sweep".
ALLOWED_DUPLICATE_STEMS: frozenset[str] = frozenset(
    {
        # Both LOCKED (`locked_by: plan_reconciler`) in the active copy yet archived anyway.
        # Deleting the active copy would silently complete a human-only unlock -- operator-gated.
        "plan_reconciler_findings_2026_08_06.md",
        "plan_reconciler_findings_tradfi_2026_08_09.md",
        # Active copy is a NEWER, independently-authored /ag-closeout-audit report written at a slug
        # that had already been archived; neither side is a stale copy of the other.
        "ag_closeout_audit_cefi_parked_2026_08_10.md",
        "ag_closeout_audit_prediction_parked_2026_08_10.md",
        "ag_closeout_audit_tradfi_parked_2026_08_10.md",
        # Active copy carries unique content the archive lacks (verification notes / frontmatter);
        # needs a content merge, not a delete.
        "ao_satellite_ao_dispatch_batch2_2026_07_30.md",
        "infra_satellite_ao_dispatch_batch7_2026_08_04.md",
        # An archived snapshot of the generated active-plan index; both copies are intentional.
        "INDEX.md",
    }
)

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


def _active_by_stem(rev: str) -> dict[str, str]:
    """Every `plans/active/**/*.md` at `rev`, keyed by basename.

    Keyed by BASENAME, not by a path substitution, because an archived doc does not sit at a
    mirror of its active path: `plans/active/issues/X.md` archives to `plans/archive/2026_08/
    issues/X.md`, and `plans/active/X.md` to `plans/archive/2026_08/X.md`. The original
    implementation only ever compared `plans/archive/issues/` against `plans/active/issues/`,
    so it was structurally blind to every DATED archive directory -- which is where essentially
    all real archivals land. Measured 2026-08-10: 10 live duplicate pairs existed on origin and
    this guard reported 0, because not one of them sat under the undated `plans/archive/issues/`.
    """
    by_stem: dict[str, str] = {}
    for path in sorted(_rev_tree(rev, "plans/active")):
        if path.endswith(".md"):
            by_stem[Path(path).name] = path
    return by_stem


def _is_redirect_stub(rev: str, path: str) -> bool:
    """True if the ACTIVE copy is a deliberate redirect stub, not an un-deleted duplicate.

    A stub is the sanctioned way to keep an archived doc's old path resolvable when a referrer
    cannot be repointed yet (e.g. the referrer is over `check_line_caps.sh`'s hard cap, where a
    same-line path swap is a modify-with-deletion and so is rejected). Such a pair is INTENDED
    and must not be reported, or the guard trains people to ignore it.
    Live example: plans/active/issues/promote_ref_orphaned_on_manual_pr_close_2026_08_06.md.
    """
    try:
        text = _git("show", f"{rev}:{path}")
    except RuntimeError:
        return False
    head = text[:2000]
    return bool(re.search(r'^title:\s*["\']?MOVED\b', head, re.MULTILINE)) or "Redirect stub" in head


def _tree_duplicates(rev: str) -> list[str]:
    """Archive paths at `rev` whose active twin (same basename) also exists at `rev`."""
    active = _active_by_stem(rev)
    dups: list[str] = []
    for archive_path in sorted(_rev_tree(rev, "plans/archive")):
        if not archive_path.endswith(".md"):
            continue
        stem = Path(archive_path).name
        twin = active.get(stem)
        if twin is None:
            continue
        if stem in ALLOWED_DUPLICATE_STEMS:
            continue
        if _is_redirect_stub(rev, twin):
            continue
        dups.append(f"{archive_path}  (live twin: {twin})")
    return dups


def _tree_has(rev: str, path: str) -> bool:
    try:
        _git("cat-file", "-e", f"{rev}:{path}")
        return True
    except RuntimeError:
        return False


def _commit_duplicates(sha: str) -> list[str]:
    """Create-only archive paths added by `sha`: the commit added plans/archive/**/<stem>.md while
    an active twin with the same basename existed in the parent AND still exists in the commit tree.
    """
    parent = sha + "^"
    try:
        _git("rev-parse", "--verify", parent)
    except RuntimeError:
        return []  # root commit: no parent to compare
    diff = _git("diff-tree", "-r", "--name-status", "-M", "--no-commit-id", sha)
    parent_active = _active_by_stem(parent)
    dups: list[str] = []
    for line in diff.splitlines():
        parts = line.split("\t")
        if not parts:
            continue
        status = parts[0]
        if status.startswith("A") and len(parts) >= 2:
            new_path = parts[1]
            if not new_path.startswith("plans/archive/") or not new_path.endswith(".md"):
                continue
            stem = Path(new_path).name
            if stem in ALLOWED_DUPLICATE_STEMS:
                continue
            twin = parent_active.get(stem)
            if twin is None:
                continue
            if _tree_has(sha, twin) and not _is_redirect_stub(sha, twin):
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
