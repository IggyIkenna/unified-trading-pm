#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""STEP 5.91 — Entity-registry CI gate.

Any commit that adds or removes values from entity-registry constants
(DATA_TYPES_BY_ASSET_GROUP, VENUES_BY_ASSET_GROUP, PROTOCOL_LAUNCH_DATES,
LST_TOKEN_GENESIS, PREDICTION_GROUPS, *_LAUNCH_DATES, *_GENESIS_DATES)
MUST also include one of:
  (a) A CSV path under unified-trading-pm/audits/entity_lifecycle/ in the
      commit message (evidence of running entity-lifecycle-cleanup.sh), OR
  (b) The tag [entity-skip-cleanup] with operator-explained reason.

Fails if neither evidence is present when entity registries were touched.

SSOT: plans/epics/infrastructure_master.md "Manifest cleanup HARD RULE" section.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

_REGISTRY_SYMBOLS = [
    "DATA_TYPES_BY_ASSET_GROUP",
    "VENUES_BY_ASSET_GROUP",
    "PROTOCOL_LAUNCH_DATES",
    "LST_TOKEN_GENESIS",
    "PREDICTION_GROUPS",
]
_LAUNCH_DATES_PAT = re.compile(r"\b\w+_LAUNCH_DATES\b")
_GENESIS_DATES_PAT = re.compile(r"\b\w+_GENESIS_DATES\b")

_AUDIT_CSV_PAT = re.compile(r"audits/entity_lifecycle/")
_SKIP_TAG = "[entity-skip-cleanup]"


def _git(*args: str, cwd: Path | None = None) -> str:
    result = subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        cwd=str(cwd) if cwd else None,
    )
    return result.stdout


def _get_diff_content(repo_root: Path) -> str:
    """Get content of the most-recent commit diff for UAC + registry paths."""
    return _git("diff", "HEAD~1", "HEAD", "--", ".", cwd=repo_root)


def _get_staged_diff(repo_root: Path) -> str:
    return _git("diff", "--staged", "--", ".", cwd=repo_root)


def _diff_touches_registry(diff: str) -> bool:
    for line in diff.splitlines():
        if not line.startswith(("+", "-")) or line.startswith(("+++", "---")):
            continue
        for sym in _REGISTRY_SYMBOLS:
            if sym in line:
                return True
        if _LAUNCH_DATES_PAT.search(line) or _GENESIS_DATES_PAT.search(line):
            return True
    return False


def _get_commit_body(repo_root: Path) -> str:
    return _git("log", "-1", "--format=%B", cwd=repo_root)


def _has_cleanup_evidence(commit_body: str) -> bool:
    if _SKIP_TAG in commit_body:
        return True
    return bool(_AUDIT_CSV_PAT.search(commit_body))


def main(argv: list[str] | None = None) -> int:
    args = argv or sys.argv[1:]
    repo_root = Path(args[0]) if args else Path.cwd()

    if not (repo_root / ".git").is_dir():
        # Not a git repo — skip check.
        print(f"STEP 5.91: skipped (no .git at {repo_root})")
        return 0

    # Check both staged changes (pre-commit) and last commit.
    staged_diff = _get_staged_diff(repo_root)
    committed_diff = _get_diff_content(repo_root)

    staged_hits = _diff_touches_registry(staged_diff)
    committed_hits = _diff_touches_registry(committed_diff)

    if not staged_hits and not committed_hits:
        print("STEP 5.91: No entity-registry changes detected — skipped.")
        return 0

    commit_body = _get_commit_body(repo_root)
    if _has_cleanup_evidence(commit_body):
        print("STEP 5.91: Entity-registry changes found + cleanup evidence present in commit.")
        return 0

    # Fail — entity registry changed but no evidence.
    print(
        "STEP 5.91 FAIL: Entity-registry constant(s) were modified but no cleanup evidence found.\n"
        "  One of the following is required in the commit message:\n"
        "  (a) A path matching 'audits/entity_lifecycle/' — run:\n"
        "      bash unified-trading-pm/scripts/lifecycle/entity-lifecycle-cleanup.sh \\\n"
        "          --mode remove --entity-type <col> --entity-key <val>\n"
        "      then attach the output CSV path in your commit body.\n"
        "  (b) [entity-skip-cleanup] tag with operator-explained reason.\n"
        "  SSOT: plans/epics/infrastructure_master.md 'Manifest cleanup HARD RULE'"
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
