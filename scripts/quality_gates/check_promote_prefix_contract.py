#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""
Contract checker: the promote-branch PREFIX is a load-bearing string shared by three files.

WHY THIS EXISTS (2026-08-10). `run_hygiene_sweep.sh` disables `--diff-base` for every
DIFF_BASE_REF-consuming ratchet when the run is a promotion PR, detected purely by branch NAME::

    if [ -n "$CI_MODE" ] && [[ ! "${GITHUB_HEAD_REF-}" =~ ^promote/ ]] && ...

That is a NAMING contract with the two bots that open promote PRs, not a structural one. If the
promote branch prefix is ever renamed in those bots and not here, the regex silently stops
matching, every one of those ratchets silently reverts to diff-scoping against an `origin/main`
that a stalled promotion keeps pushing further behind, and the pipeline deadlocks again --- with
NO test failing and no error anywhere, because a gate that fails to recognise a promote PR just
looks like an ordinary red gate.

That deadlock is not hypothetical: it cost 22 hours and 1180 unpromoted commits on 2026-08-10, and
the tell (a violation count that GROWS across distinct HEADs -- 51->53->55 docs, 116->151->181
todos) reads as ordinary corpus growth unless you already know to look for it. See
/plans/active/issues/na_corpus_ratchet_diff_base_vs_lagging_main_deadlocks_promotion_2026_08_10.md

So: assert all three agree. Renaming the prefix now breaks THIS check --- loudly, in one place,
with the full list of files to update --- instead of silently disarming four ratchets.

Exit codes:
  0 -- every producer and consumer agrees on the prefix (pass)
  1 -- a producer/consumer disagrees, or an expected site is missing (fail)
  2 -- IO error
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

PM = Path(__file__).resolve().parent.parent.parent

# The one true prefix. Changing it here alone is NOT enough --- every site below must change too,
# which is exactly the point of this check.
PROMOTE_PREFIX = "promote/"

# (path, regex that must match, human description of what the site does)
SITES: list[tuple[str, str, str]] = [
    (
        ".github/workflows/ldr-to-main-promote.yml",
        r'PROMOTE_HEAD="promote/\$REPO/',
        "PM's own promote bot builds the head ref",
    ),
    (
        "scripts/cicd/ldr_to_main_fleet_promote.sh",
        r'PROMOTE_HEAD="promote/\$REPO/',
        "the fleet promote bot builds the head ref",
    ),
    (
        "scripts/plan-hygiene/run_hygiene_sweep.sh",
        r'GITHUB_HEAD_REF-\}"\s*=~\s*\^promote/',
        "the hygiene sweep detects a promote PR to skip --diff-base",
    ),
    (
        ".github/workflows/quality-gates-v2.yml",
        r"cancel-in-progress:\s*\$\{\{\s*!startsWith\(github\.head_ref,\s*'promote/'\)",
        "quality-gates-v2 exempts promote PRs from cancel-in-progress so a 70-135 min "
        "tests leg can outlive the promote bot's ~15 min head refresh",
    ),
]


def main() -> int:
    quiet = "--quiet" in sys.argv
    problems: list[str] = []

    for rel, pattern, what in SITES:
        path = PM / rel
        if not path.is_file():
            problems.append(f"{rel}: MISSING --- {what}")
            continue
        try:
            text = path.read_text()
        except OSError as exc:  # pragma: no cover - IO edge
            print(f"❌ check_promote_prefix_contract: cannot read {rel}: {exc}", file=sys.stderr)
            return 2
        if not re.search(pattern, text):
            problems.append(f"{rel}: no site matching /{pattern}/ --- {what}")

    # The sweep must gate the SHARED DIFF_BASE_REF, not just one consumer. Gating a single check
    # leaves its siblings (reference-paths / archive-candidates / effort-ratchet) diff-scoped
    # against a lagging main --- measured 2026-08-10: check_reference_paths hard-failed the
    # promote path for exactly this reason AFTER the NA-corpus check had already been gated.
    sweep = PM / "scripts/plan-hygiene/run_hygiene_sweep.sh"
    if sweep.is_file():
        text = sweep.read_text()
        m = re.search(r'^DIFF_BASE_REF=""\n(?:.*\n){0,6}?.*GITHUB_HEAD_REF', text, re.M)
        if not m:
            problems.append(
                "scripts/plan-hygiene/run_hygiene_sweep.sh: the promote gate is NOT on the shared "
                "DIFF_BASE_REF assignment --- gating one consumer leaves its siblings deadlockable"
            )

    if problems:
        print("❌ check_promote_prefix_contract: promote-prefix contract broken:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        print(
            f"\n  The promote branch prefix ({PROMOTE_PREFIX!r}) is shared by the promote bots and by\n"
            "  run_hygiene_sweep.sh's promote detection. If you renamed it, update EVERY site listed\n"
            "  above (and PROMOTE_PREFIX in this file) in the SAME change. A half-rename silently\n"
            "  disarms the promote gate on all four diff-scoped ratchets and re-creates the\n"
            "  2026-08-10 LDR->main deadlock with no other test failing.",
            file=sys.stderr,
        )
        return 1

    if not quiet:
        print(f"✅ check_promote_prefix_contract: {len(SITES)} site(s) agree on {PROMOTE_PREFIX!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
