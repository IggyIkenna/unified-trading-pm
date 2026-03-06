"""Rollout canonical version-bump.yml to all repos in workspace-manifest.json.

Overwrites any existing version-bump.yml with the canonical template.
The template uses GH_PAT for cross-repo dispatch and github.event.repository.name
so it works for any repo without modification.

Usage:
    python3 scripts/propagation/rollout-version-bump-workflow.py [--dry-run] [--repo REPO_NAME]

Options:
    --dry-run   Show what would be done without writing files
    --repo      Only rollout to a specific repo name
"""

import argparse
import json
from pathlib import Path
from typing import TypeAlias, cast

JsonDict: TypeAlias = dict[str, object]


def _jdict(val: object) -> JsonDict | None:
    if isinstance(val, dict):
        return cast(JsonDict, val)
    return None


def _jstr(val: object, default: str = "") -> str:
    return str(val) if val is not None else default


MANIFEST_PATH = Path(__file__).parent.parent.parent / "workspace-manifest.json"
TEMPLATE_PATH = Path(__file__).parent / "templates" / "version-bump.yml"
WORKSPACE_ROOT = Path(__file__).parent.parent.parent.parent  # one level above unified-trading-pm

# These repos don't have pyproject.toml and should not get version-bump.yml
SKIP_REPOS = {"unified-trading-pm"}  # PM manages itself


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    parser.add_argument("--repo", help="Only rollout to this repo name")
    args = parser.parse_args()

    with open(MANIFEST_PATH) as f:
        manifest = cast(JsonDict, json.load(f))
    template = TEMPLATE_PATH.read_text()
    repos_raw = _jdict(manifest.get("repositories"))
    repositories = cast(dict[str, JsonDict], repos_raw) if repos_raw else {}
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
            print(f"  NOT FOUND {repo_name}: directory not found at {repo_path}")
            not_found += 1
            continue

        workflow_dir = repo_path / ".github" / "workflows"
        target_path = workflow_dir / "version-bump.yml"

        if target_path.exists():
            existing = target_path.read_text()
            if existing == template:
                print(f"  UP-TO-DATE {repo_name}")
                skipped += 1
                continue

        if not workflow_dir.exists():
            if dry_run:
                print(f"  [dry-run] Would create {workflow_dir}")
            else:
                workflow_dir.mkdir(parents=True, exist_ok=True)

        if dry_run:
            print(f"  [dry-run] Would write {target_path}")
        else:
            target_path.write_text(template)
            print(f"  WROTE {repo_name}")
        updated += 1

    action = "Would update" if dry_run else "Updated"
    print(f"\n{action} {updated} repos, skipped {skipped}, not found {not_found}.")


if __name__ == "__main__":
    main()
