# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Rollout canonical quickmerge.sh symlink to all repos in workspace-manifest.json.

Replaces any existing scripts/quickmerge.sh (file or stale symlink) with a symlink
pointing to ../../unified-trading-pm/scripts/quickmerge.sh.

Why symlinks instead of copies:
  - Each repo's quality-gates.yml already clones PM to ../unified-trading-pm before
    running any scripts, so PM is always on disk in the same relative position both
    locally (workspace sibling) and in CI (cloned sibling).
  - Symlinks mean a change to PM's quickmerge.sh is immediately live in all repos
    with no rollout needed. The CI workflow (rollout-quickmerge.yml) only needs to
    run once to set up the symlink; after that it becomes a no-op.

Usage:
    python3 scripts/propagation/rollout-quickmerge.py [--dry-run] [--repo REPO_NAME]

Options:
    --dry-run   Show what would be done without writing files
    --repo      Only rollout to a specific repo name
"""

import argparse
import json
from pathlib import Path
from typing import cast

type JsonDict = dict[str, object]

MANIFEST_PATH = Path(__file__).parent.parent.parent / "workspace-manifest.json"
WORKSPACE_ROOT = Path(__file__).parent.parent.parent.parent

# Symlink target — relative from scripts/quickmerge.sh in each repo:
#   scripts/ → repo-root/ → workspace-root/ → unified-trading-pm/scripts/quickmerge.sh
SYMLINK_TARGET = Path("../../unified-trading-pm/scripts/quickmerge.sh")

# PM manages its own quickmerge.sh — skip it in rollout
SKIP_REPOS = {"unified-trading-pm"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    parser.add_argument("--repo", help="Only rollout to this repo name")
    args = parser.parse_args()

    with open(MANIFEST_PATH) as f:
        manifest = cast(JsonDict, json.load(f))

    repos_raw = manifest.get("repositories")
    repositories: dict[str, JsonDict] = cast(dict[str, JsonDict], repos_raw) if isinstance(repos_raw, dict) else {}
    dry_run = cast(bool, args.dry_run)
    repo_filter = cast(str | None, args.repo)

    target_repos = [
        name for name in repositories if name not in SKIP_REPOS and (repo_filter is None or name == repo_filter)
    ]

    print(f"Target repos: {len(target_repos)}")
    if repo_filter is not None and repo_filter not in target_repos:
        print(f"ERROR: {repo_filter} not found in manifest or in skip list.")
        return

    updated = 0
    skipped = 0
    not_found = 0

    for repo_name in target_repos:
        repo_path = WORKSPACE_ROOT / repo_name
        if not repo_path.exists():
            print(f"  NOT FOUND {repo_name}")
            not_found += 1
            continue

        scripts_dir = repo_path / "scripts"
        target_path = scripts_dir / "quickmerge.sh"

        # Already a correct symlink — nothing to do
        if target_path.is_symlink() and target_path.readlink() == SYMLINK_TARGET:
            print(f"  UP-TO-DATE {repo_name}")
            skipped += 1
            continue

        if not scripts_dir.exists():
            if dry_run:
                print(f"  [dry-run] Would create {scripts_dir}")
            else:
                scripts_dir.mkdir(parents=True, exist_ok=True)

        if dry_run:
            verb = (
                "replace symlink"
                if target_path.is_symlink()
                else "replace file"
                if target_path.exists()
                else "create symlink"
            )
            print(f"  [dry-run] Would {verb} → {SYMLINK_TARGET} in {repo_name}")
        else:
            if target_path.exists() or target_path.is_symlink():
                target_path.unlink()
            target_path.symlink_to(SYMLINK_TARGET)
            print(f"  SYMLINKED {repo_name}")
        updated += 1

    action = "Would update" if dry_run else "Updated"
    print(f"\n{action} {updated} repos, skipped {skipped}, not found {not_found}.")


if __name__ == "__main__":
    main()
