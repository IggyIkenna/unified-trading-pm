#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""check_cron_branch_override_parity — reject a manifest/cron-override registry drift.

Mirrors agent-orchestrator's `test_integration_branch_matches_manifest` (its own parity
gate for registry (A), `_REPO_INTEGRATION_BRANCH`) for registry (C):
`scripts/dev/cron-branch-overrides.txt`, read only by `slot-cron-ff-pull.sh`, never
auto-derived from `workspace-manifest.json` like the other two registries.

Why this exists (unified_trading_ci_ff_pull_cron_branch_override_gap_2026_08_17): the
manifest declared `unified-trading-ci`'s `integration_branch: main` since 2026-08-07, and
registry (A) picked that up on 2026-08-08 (`agent-orchestrator@8b4c737`), but this file
never got a matching row. Every 5-minute `--all-slots` cron tick (laptop + orchestrator VM)
then defaulted `unified-trading-ci` to `live-defi-rollout` and fast-forward-merged that
branch's content into slots' local `main` — harmless while the two branches stayed
FF-compatible, then a fleet-wide FM5 branch-quarantine storm (~30 slots, every 5 min) the
moment they genuinely forked. This guard makes that exact class of drift fail QG instead of
waiting for a live incident to surface it again.

Exit 0 = every non-default manifest row has a matching, agreeing override-file row (and
vice versa). Exit 1 = drift found (prints what to add/fix/remove). Exit 2 = unreadable
input.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DEFAULT_INTEGRATION_BRANCH = "live-defi-rollout"


def _parse_overrides(text: str) -> dict[str, str]:
    """repo -> branch, from `scripts/dev/cron-branch-overrides.txt`'s own format."""
    overrides: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split()
        if len(parts) != 2:
            continue
        repo, branch = parts
        overrides[repo] = branch
    return overrides


def _expected_from_manifest(manifest: dict) -> dict[str, str]:
    """repo -> branch, for every repo whose manifest entry is NOT the default."""
    repositories = manifest["repositories"]
    return {
        repo: str(entry["integration_branch"])
        for repo, entry in repositories.items()
        if isinstance(entry, dict)
        and entry.get("integration_branch")
        and str(entry["integration_branch"]) != DEFAULT_INTEGRATION_BRANCH
    }


def check(manifest_path: Path, overrides_path: Path) -> list[str]:
    """Return a list of human-readable violations; empty means parity holds."""
    manifest = json.loads(manifest_path.read_text())
    overrides = _parse_overrides(overrides_path.read_text())
    expected = _expected_from_manifest(manifest)
    repositories = manifest["repositories"]

    violations: list[str] = []

    missing = {repo: branch for repo, branch in expected.items() if repo not in overrides}
    for repo, branch in sorted(missing.items()):
        violations.append(
            f"'{repo}' declares integration_branch={branch!r} in workspace-manifest.json but has no row in "
            f"{overrides_path.name} -- slot-cron-ff-pull.sh will silently default it to "
            f"{DEFAULT_INTEGRATION_BRANCH!r} (add: '{repo} {branch}')"
        )

    wrong = {
        repo: (branch, expected[repo])
        for repo, branch in overrides.items()
        if repo in expected and branch != expected[repo]
    }
    for repo, (here, want) in sorted(wrong.items()):
        violations.append(f"'{repo}' row says {here!r} but workspace-manifest.json says {want!r} -- fix the mismatch")

    stale = {repo: branch for repo, branch in overrides.items() if repo in repositories and repo not in expected}
    for repo, branch in sorted(stale.items()):
        violations.append(
            f"'{repo}' has a {overrides_path.name} row ({branch!r}) but its manifest entry is the default "
            f"({DEFAULT_INTEGRATION_BRANCH!r}) -- remove the stale row"
        )

    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="reject a manifest/cron-override registry drift")
    root = Path(__file__).resolve().parents[2]
    parser.add_argument("--manifest", type=Path, default=root / "workspace-manifest.json")
    parser.add_argument("--overrides", type=Path, default=root / "scripts" / "dev" / "cron-branch-overrides.txt")
    args = parser.parse_args(argv)

    try:
        violations = check(args.manifest, args.overrides)
    except (OSError, json.JSONDecodeError, KeyError) as exc:
        print(f"❌ check_cron_branch_override_parity: could not read input: {exc}", file=sys.stderr)
        return 2

    if not violations:
        return 0

    print("❌ scripts/dev/cron-branch-overrides.txt has drifted from workspace-manifest.json:", file=sys.stderr)
    for v in violations:
        print(f"  - {v}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
