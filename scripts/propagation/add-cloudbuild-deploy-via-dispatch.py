#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""
Add deploy-via-dispatch comment to service cloudbuild.yaml files.

Services that deploy via central deployment-service (not inline deploy step)
should add this comment to suppress the STEP 5.17 advisory:
  "cloudbuild.yaml has no deploy/notify-deployment step"

Usage:
    python3 scripts/propagation/add-cloudbuild-deploy-via-dispatch.py [--dry-run] [--repo NAME]
    python3 scripts/propagation/add-cloudbuild-deploy-via-dispatch.py --all  # add to all with cloudbuild

Repos are read from workspace-manifest.json. Repos with deploy_via_dispatch: true
in manifest get the comment. If --all, add to any repo with cloudbuild.yaml that
lacks deploy/notify-deployment step and doesn't already have the comment.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PM_ROOT = SCRIPT_DIR.parent.parent
WORKSPACE_ROOT = PM_ROOT.parent
MANIFEST = PM_ROOT / "workspace-manifest.json"

COMMENT = "# deploy-via-dispatch — deployed via central deployment-service, not inline\n"
COMMENT_PATTERN = re.compile(r"#\s*deploy-via-dispatch|#\s*deploys-via-dispatch", re.I)


def has_deploy_step(content: str) -> bool:
    """True if cloudbuild has deploy or notify-deployment step."""
    return bool(re.search(r'id:\s*["\']?(deploy|notify-deployment)', content) or "gcloud run deploy" in content)


def has_deploy_via_dispatch_comment(content: str) -> bool:
    """True if cloudbuild already has deploy-via-dispatch comment."""
    return bool(COMMENT_PATTERN.search(content))


def insert_comment(content: str) -> str:
    """Insert deploy-via-dispatch comment after first line (title)."""
    lines = content.split("\n")
    insert_at = 2
    for i, line in enumerate(lines[:5]):
        if "Cloud Build" in line or (i > 0 and line.strip().startswith("#")):
            insert_at = i + 1
            break
    before = "\n".join(lines[:insert_at])
    rest = "\n".join(lines[insert_at:])
    if before and not before.endswith("\n"):
        before += "\n"
    return before + COMMENT + rest


def get_deploy_via_dispatch_repos() -> set[str]:
    """Repos with deploy_via_dispatch: true in manifest."""
    if not MANIFEST.exists():
        return set()
    data = json.loads(MANIFEST.read_text())
    repos = set()
    for name, meta in data.get("repos", {}).items():  # noqa: qg-empty-fallback
        if isinstance(meta, dict) and meta.get("deploy_via_dispatch"):
            repos.add(name)
    return repos


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Print changes, do not write")
    parser.add_argument("--repo", type=str, help="Limit to single repo")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Add to all repos with cloudbuild that lack deploy step (and don't have comment)",
    )
    args = parser.parse_args()

    if args.all:
        target_repos = None
    elif args.repo:
        target_repos = {args.repo}
    else:
        target_repos = get_deploy_via_dispatch_repos()
        if not target_repos:
            print(
                "No repos with deploy_via_dispatch in manifest. Use --all or --repo NAME.",
                file=sys.stderr,
            )
            return 1

    modified = 0
    for repo_dir in sorted(WORKSPACE_ROOT.iterdir()):
        if not repo_dir.is_dir():
            continue
        name = repo_dir.name
        if name.startswith(".") or name == "unified-trading-pm":
            continue
        if target_repos is not None and name not in target_repos:
            continue
        cloudbuild = repo_dir / "cloudbuild.yaml"
        if not cloudbuild.exists():
            continue
        if args.all:
            content = cloudbuild.read_text()
            if has_deploy_step(content) or has_deploy_via_dispatch_comment(content):
                continue

        content = cloudbuild.read_text()
        if has_deploy_via_dispatch_comment(content):
            continue
        if args.all and has_deploy_step(content):
            continue

        new_content = insert_comment(content)
        if new_content == content:
            continue
        if args.dry_run:
            print(f"[dry-run] Would add deploy-via-dispatch to {name}/cloudbuild.yaml")
            modified += 1
        else:
            cloudbuild.write_text(new_content)
            print(f"Patched {name}/cloudbuild.yaml")
            modified += 1

    print(f"Done. Modified {modified} file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
