#!/usr/bin/env python3
# Epic: plan_hygiene_master
# Lifecycle: permanent
# Delete-when: NA
"""Auto-heal a create-only archive/active duplicate pair resurrected by the main→LDR backmerge.

WHY (found live 2026-08-11, ci_reconcile session): `main-backmerge-to-ldr` does a plain
`git merge --no-ff --no-edit origin/main` (or the explicit-base `git merge-tree` path). Git's
merge has no notion of "this file was archived (renamed) on LDR after `main` last saw it" unless
its rename-detection heuristic correlates the delete with the archived copy's content closely
enough — for a heavily-edited archival (frontmatter status/dates changed, body reconciled) it
often doesn't. The merge then just unions both trees: `main`'s untouched `plans/active/<X>.md`
survives alongside LDR's `plans/archive/.../<X>.md`, silently resurrecting an already-archived
doc as a live duplicate. This is invisible to `check_no_silent_revert_loss` in the backmerge
workflow (that safety net only compares against LDR's immediate parent commit — an archival from
days/weeks earlier is out of its window) and was previously only caught downstream, hours later,
by `check_create_only_archive_commits.py` on an unrelated commit's promote-PR test-merge — by
which point it blocks a random innocent commit, not the backmerge that caused it.

WHAT THIS DOES: runs the exact same duplicate-pair detection `check_create_only_archive_commits.py`
uses, and for every pair found, deletes the resurrected `plans/active/**` twin — keeping the
archived copy, which is definitionally the more current one (LDR already decided to archive it;
`main` was just stale). Never touches the archive-path side, never guesses when a pair is
ambiguous (delegates entirely to the same `ALLOWED_DUPLICATE_STEMS` / redirect-stub exemptions the
checker already trusts, so a deliberately-kept pair is never disturbed). Intended to run as a
backmerge post-merge step, staging deletions for the caller to fold into the merge commit before
push — the LDR tip should never observe the resurrected duplicate, not even for one commit.

Usage: python3 scripts/plan-hygiene/fix_backmerge_archive_resurrection.py
  Exit 0 always (informational — deletions are staged via `git rm`, nothing is committed here;
  the caller decides whether to amend the in-progress merge or create a follow-up commit). Prints
  each path removed; prints nothing and exits 0 if the tree is already clean.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_create_only_archive_commits import PM_DIR, _tree_duplicates


def main() -> int:
    violations = _tree_duplicates("HEAD")
    if not violations:
        return 0
    for v in sorted(violations):
        # v is "<archive_path>  (live twin: <active_path>)" — see _tree_duplicates.
        twin = v.split("(live twin: ", 1)[1].rstrip(")")
        proc = subprocess.run(
            ["git", "-C", str(PM_DIR), "rm", "--quiet", "--", twin],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            print(f"WARN: could not remove resurrected duplicate {twin}: {proc.stderr.strip()}", file=sys.stderr)
            continue
        print(f"fix_backmerge_archive_resurrection: removed resurrected duplicate {twin} (kept {v.split('  (')[0]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
