# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Rollout update-dependency-version.yml to all repos that have dependencies.

Reads workspace-manifest.json to find repos with dependencies, then copies
the template workflow into each repo's .github/workflows/ directory.

Usage:
    python3 scripts/propagation/rollout-dependency-update-workflow.py [--dry-run] [--repo REPO_NAME]

Options:
    --dry-run   Show what would be done without writing files
    --repo      Only rollout to a specific repo name
"""

import argparse
import json
from pathlib import Path
from typing import cast

type JsonDict = dict[str, object]


def _jdict(val: object) -> JsonDict | None:
    if isinstance(val, dict):
        return cast(JsonDict, val)
    return None


MANIFEST_PATH = Path(__file__).parent.parent.parent / "workspace-manifest.json"
TEMPLATE_PATH = Path(__file__).parent / "templates" / "update-dependency-version.yml"
WORKSPACE_ROOT = Path(__file__).parent.parent.parent.parent  # one level above unified-trading-pm


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    parser.add_argument("--repo", help="Only rollout to this repo name")
    args = parser.parse_args()

    with open(MANIFEST_PATH) as f:
        manifest = cast(JsonDict, json.load(f))
    template = TEMPLATE_PATH.read_text()
    repos_raw = _jdict(manifest.get("repositories"))
    repositories = cast(dict[str, JsonDict], repos_raw) if repos_raw is not None else {}
    dry_run = cast(bool, args.dry_run)
    repo_filter = cast(str | None, args.repo)

    target_repos = [
        name
        for name, data in repositories.items()
        if data.get("dependencies") and (repo_filter is None or name == repo_filter)
    ]

    print(f"Repos with dependencies: {len(target_repos)}")
    if repo_filter is not None and repo_filter not in target_repos:
        print(f"ERROR: {repo_filter} not found or has no dependencies in manifest.")
        return

    updated = 0
    skipped = 0
    for repo_name in target_repos:
        repo_path = WORKSPACE_ROOT / repo_name
        workflow_dir = repo_path / ".github" / "workflows"
        target_path = workflow_dir / "update-dependency-version.yml"

        if not repo_path.exists():
            print(f"  SKIP {repo_name}: directory not found at {repo_path}")
            skipped += 1
            continue

        if not workflow_dir.exists():
            if dry_run:
                print(f"  [dry-run] Would create {workflow_dir}")
            else:
                workflow_dir.mkdir(parents=True, exist_ok=True)

        if target_path.exists():
            existing = target_path.read_text()
            if existing == template:
                print(f"  UP-TO-DATE {repo_name}")
                skipped += 1
                continue

        if dry_run:
            print(f"  [dry-run] Would write {target_path}")
        else:
            target_path.write_text(template)
            print(f"  WROTE {repo_name}: {target_path}")
        updated += 1

    action = "Would update" if dry_run else "Updated"
    print(f"\n{action} {updated} repos, skipped {skipped}.")
    if not dry_run and updated > 0:
        print("\nNext: commit changes in each updated repo (or use a bulk commit script).")


if __name__ == "__main__":
    main()
