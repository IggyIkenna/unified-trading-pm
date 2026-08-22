#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Check that no plan or issue doc with a TERMINAL status is still sitting in
plans/active/ or plans/active/issues/ instead of plans/archive/.

Operator finding 2026-07-25: `codex/11-project-management/issue-doc-lifecycle.md`
already documents this as a HARD, review-blocking rule for issue docs ("Banner-
marked + still in active/issues/ — dual-tracking... archive immediately") and
ships an audit recipe to catch it — but that recipe grepped for a `^resolved:`
frontmatter key that no longer exists in the live schema (docspec.py moved to
`status: resolved` + `resolved_by:` long ago). The stale recipe silently caught
ZERO of the real violations, which is exactly how ~42 resolved issue docs and 13
terminal-status plans accumulated in plans/active/ undetected. This script is the
corrected, MACHINE-ENFORCED version of that recipe, extended to cover the
parallel (previously unenforced, CLAUDE.md-only-documented) plan-side rule.

Terminal states per docspec.py's STATUS_BY_TYPE:
  - issue: resolved, false-positive, superseded   (open/blocked are NOT terminal)
  - plan:  complete, superseded, cancelled          (draft/active/blocked/paused are NOT terminal)

A doc in that state, physically still under plans/active/ (or plans/active/issues/
for issue docs) rather than plans/archive/, is a violation — exactly the
dual-tracking anti-pattern issue-doc-lifecycle.md already calls review-blocking,
now also applied to plans per CLAUDE.md's own archival-ritual rule.

SHRINKING ratchet (same shape as check_ag_closeout_linkage.py / check_reference_paths.py)
— NOT zero-tolerance from day 1. The backlog this found (~55 docs) is real,
pre-existing debt being swept by a dedicated AO plan, not something to block CI
over immediately. A live count EXCEEDING the baseline means a NEW terminal-status
doc landed without being archived, which IS mechanically wrong — fix by archiving
it (git mv to plans/archive/[issues/], add the 🟢 RESOLVED/status banner, fix every
referrer corpus-wide per CLAUDE.md's archival ritual), never by raising the number.

Usage:
  python3 scripts/plan-hygiene/check_terminal_status_archived.py [--quiet] [--update-baseline]
  python3 scripts/plan-hygiene/check_terminal_status_archived.py --only <path> [<path> ...]
Exit 0 if the violation count is <= baseline. NEVER hand-raise a baseline entry.

``--only <paths>`` (added 2026-08-07, precommit migration): checks ONLY the given
files instead of globbing the whole corpus — no baseline/ratchet involved, since a
file YOU are actively staging with a terminal status and no plans/archive/ path is
unconditionally wrong regardless of what the rest of the fleet's backlog looks
like. This is what makes it safe to run from run_hygiene_sweep.sh --precommit: the
full corpus-wide mode above (67s+ full sweep) has real, currently-nonzero
pre-existing debt (other agents' unarchived docs) that would false-block every
commit if run as a blocking precommit gate — `--only` sidesteps that because
"is this ratchet under baseline" ever enters the picture. Mirrors
check_finalize_plan_coverage.py --only, the same pattern this precommit hook
already uses elsewhere for the same reason. Caught a real self-inflicted
violation same-session, 2026-08-07 (escalation_watchdog_retune_and_reconcile
issue doc committed status:resolved + all todos done, never archived).
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "docs"))
import docspec

PM_DIR = Path(__file__).resolve().parents[2]
BASELINE_PATH = Path(__file__).resolve().parent / "terminal_status_archived_baseline.yaml"

ISSUE_TERMINAL = frozenset({"resolved", "false-positive", "superseded"})
PLAN_TERMINAL = frozenset({"complete", "superseded", "cancelled"})


def _doc_type_and_terminal(relpath: str) -> tuple[str, frozenset[str]] | None:
    """Which terminal-set applies to this path, or None if it's not a plan/issue
    doc this check cares about (e.g. already under plans/archive/, or outside
    plans/ entirely)."""
    if relpath.startswith("plans/active/issues/"):
        return "issue", ISSUE_TERMINAL
    if relpath.startswith("plans/active/"):
        return "plan", PLAN_TERMINAL
    return None


def _check_one(p: Path) -> str | None:
    """Violation string for a single doc, or None if it's fine/not-applicable.
    Shared by the corpus-wide glob and the --only single-file path so the two
    modes can never silently diverge on what counts as a violation."""
    relpath = p.relative_to(PM_DIR).as_posix()
    if docspec.is_exempt(relpath):
        return None
    kind = _doc_type_and_terminal(relpath)
    if kind is None:
        return None
    doc_type, terminal = kind
    if not p.is_file():
        return None
    text = p.read_text(encoding="utf-8")
    fm, _body = docspec.parse_frontmatter(text)
    if fm is None:
        return None
    if fm.get("doc_type") != doc_type:
        return None
    locked_by = fm.get("locked_by")
    if locked_by:
        # A locked doc cannot be archived without a human `[unlock-plan]` (HARD RULE) —
        # counting it as a violation would make this ratchet un-satisfiable by any
        # autonomous agent, mirroring the same exclusion check_archive_candidates.sh
        # already applies (added 2026-07-30 after 2 independent locked+terminal docs
        # surfaced the gap: check_archive_candidates.sh excluded them, this script didn't).
        return None
    status = fm.get("status")
    if status in terminal:
        return f"{relpath}: status={status} (doc_type={doc_type}) — should be in plans/archive/"
    return None


def scan_dir(rel_dir: str, doc_type: str, terminal: frozenset[str]) -> list[str]:
    base = PM_DIR / rel_dir
    violations: list[str] = []
    if not base.is_dir():
        return violations
    for p in sorted(base.glob("*.md")):
        v = _check_one(p)
        if v is not None:
            violations.append(v)
    return violations


def _run_only(paths: list[str], quiet: bool) -> int:
    """Precommit-scoped mode: check exactly the given files, no baseline/ratchet.
    A staged doc that's terminal-status-and-unarchived is unconditionally wrong —
    the rest of the fleet's pre-existing backlog is irrelevant to that fact."""
    violations = []
    for raw in paths:
        p = Path(raw)
        if not p.is_absolute():
            p = Path.cwd() / p
        # Resolve symlinks before relative_to() in _check_one(): PM_DIR is built via
        # Path(__file__).resolve(), but an unresolved `p` (Path.cwd() reflects the shell's
        # un-resolved $PWD, e.g. macOS /var/... vs the real /private/var/...) makes
        # p.relative_to(PM_DIR) raise ValueError even though both point at the same file.
        # Hit live 2026-08-12 running --precommit from a /var/folders/... worktree.
        p = p.resolve()
        v = _check_one(p)
        if v is not None:
            violations.append(v)

    if not quiet:
        for v in violations:
            print(f"  DUAL-TRACK  {v}")

    n = len(violations)
    print(f"{'✅' if n == 0 else '❌'} check_terminal_status_archived (--only): {n} violation(s) in staged files")
    return 0 if n == 0 else 1


def main() -> int:
    quiet = "--quiet" in sys.argv
    update = "--update-baseline" in sys.argv

    if "--only" in sys.argv:
        idx = sys.argv.index("--only")
        return _run_only(sys.argv[idx + 1 :], quiet)

    violations = scan_dir("plans/active/issues", "issue", ISSUE_TERMINAL) + scan_dir(
        "plans/active", "plan", PLAN_TERMINAL
    )

    baseline = load_baseline()
    n = len(violations)
    ok = n <= baseline

    if not quiet:
        print("Terminal-status-archived check (plans/active + plans/active/issues):")
        print()
        for v in sorted(violations):
            print(f"  DUAL-TRACK  {v}")
        print()

    print(f"{'✅' if ok else '❌'} check_terminal_status_archived: {n} violation(s) (baseline {baseline})")

    if update:
        write_baseline(n, baseline)
        print(f"Baseline updated: {min(n, baseline or n)}")

    return 0 if ok else 1


def load_baseline() -> int:
    if not BASELINE_PATH.exists():
        return 0
    raw = yaml.safe_load(BASELINE_PATH.read_text(encoding="utf-8")) or {}
    return int(raw.get("violation_count", 0))


def write_baseline(n: int, existing: int) -> None:
    new_count = min(n, existing) if existing else n
    BASELINE_PATH.write_text(
        "# Baseline for check_terminal_status_archived.py — no plan/issue doc with a\n"
        "# TERMINAL status (issue: resolved/false-positive/superseded; plan: complete/\n"
        "# superseded/cancelled) may sit in plans/active/ or plans/active/issues/ instead\n"
        "# of plans/archive/ (operator finding 2026-07-25 — issue-doc-lifecycle.md's own\n"
        "# archive-on-resolve rule had a dead audit recipe and ~55 docs accumulated\n"
        "# unarchived; see issue_and_plan_archival_backlog_sweep_2026_07_25.md).\n"
        "#\n"
        "# This is a SHRINKING ratchet. violation_count is the number of pre-existing\n"
        "# unarchived terminal-status docs the gate tolerates. A live count EXCEEDING\n"
        "# this fails the check — a NEW terminal-status doc landed without being\n"
        "# archived, fix it (archive it), don't raise the number. LOWER it (re-run\n"
        "# --update-baseline) as the backlog sweep archives docs. NEVER hand-raise it.\n"
        f"violation_count: {new_count}\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())
