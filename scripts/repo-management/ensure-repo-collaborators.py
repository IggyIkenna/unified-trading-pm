#!/usr/bin/env python3.13
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""
Ensure GitHub users datadodo and CosmicTrader have admin (read/write) access
on all repos in the workspace. Uses GitHub REST API; token: GH_PAT or GITHUB_TOKEN.
Run from workspace root or pass WORKSPACE_ROOT.
"""

from __future__ import annotations

import logging
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from http.client import HTTPResponse
from pathlib import Path
from typing import cast

logger = logging.getLogger(__name__)
# Script lives at .../unified-trading-pm/scripts/repo-management/ensure-repo-collaborators.py
# Workspace root = parent of unified-trading-pm (contains all 55 repos)
WORKSPACE_ROOT = os.environ.get(
    "WORKSPACE_ROOT",
    str(Path(__file__).resolve().parent.parent.parent.parent),
)
COLLABORATORS = ("datadodo", "CosmicTrader")
PERMISSION = "admin"  # read/write + manage repo settings
GITHUB_API = "https://api.github.com"


def get_origin_url(repo_path: Path) -> str | None:
    """Get origin remote URL for a git repo."""
    try:
        out = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        logger.debug("Suppressed %s during get origin url: %s", type(e).__name__, e)
        pass
    return None


def parse_owner_repo(url: str) -> tuple[str, str] | None:
    """Parse owner/repo from git URL. Returns (owner, repo) or None."""
    # git@github.com:owner/repo.git or https://github.com/owner/repo or https://github.com/owner/repo.git
    m = re.match(r"(?:git@github\.com:|https?://github\.com/)([^/]+)/([^/\s]+?)(?:\.git)?$", url)
    if m:
        return (m.group(1), m.group(2))
    return None


def collect_repos(root: Path) -> list[tuple[str, str]]:
    """Collect (owner, repo) for every directory under root that has .git and origin."""
    repos: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    root = Path(root).resolve()
    if not root.is_dir():
        return repos
    for d in sorted(root.iterdir()):
        if not d.is_dir() or d.name.startswith("."):
            continue
        git_dir = d / ".git"
        if not git_dir.exists():
            continue
        url = get_origin_url(d)
        if not url:
            continue
        parsed = parse_owner_repo(url)
        if parsed and parsed not in seen:
            seen.add(parsed)
            repos.append(parsed)
    return repos


def add_collaborator(
    token: str,
    owner: str,
    repo: str,
    username: str,
    permission: str = "admin",
) -> tuple[bool, str]:
    """Add or update collaborator. Returns (success, message)."""
    url = f"{GITHUB_API}/repos/{owner}/{repo}/collaborators/{username}"
    data = f'{{"permission":"{permission}"}}'.encode()
    req = urllib.request.Request(
        url,
        data=data,
        method="PUT",
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json",
        },
    )
    try:
        resp = cast(HTTPResponse, urllib.request.urlopen(req, timeout=30))  # nosec B310 — URL is GitHub API hardcoded https endpoint
        # 204 = no content, added/updated
        if resp.status in (204, 200):
            return True, "ok"
        return False, f"status {resp.status}"
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        if e.code == 204:
            return True, "ok"
        if e.code == 422 and ("already exists" in body.lower() or "request" in body.lower()):
            # might already be collaborator with same permission
            return True, "already added"
        return False, f"HTTP {e.code}: {body[:200]}"
    except (OSError, ValueError) as e:
        return False, str(e)


def main() -> int:
    dry_run = "--dry-run" in sys.argv
    root = Path(WORKSPACE_ROOT)
    repos = collect_repos(root)
    if not repos:
        print("No git repos with origin found under", root, file=sys.stderr)
        return 1

    print(f"Found {len(repos)} repos under {root}.")
    if dry_run:
        for owner, repo in repos:
            print(f"  {owner}/{repo}")
        print("Run without --dry-run and GH_PAT (or GITHUB_TOKEN) set to add collaborators.")
        return 0

    token = os.environ.get("GH_PAT") or os.environ.get("GITHUB_TOKEN")
    if not token:
        print("GH_PAT or GITHUB_TOKEN is not set. Set one and re-run.", file=sys.stderr)
        return 1

    print(f"Ensuring {COLLABORATORS} have {PERMISSION} access.")
    failed: list[tuple[str, str, str, str]] = []
    for owner, repo in repos:
        full = f"{owner}/{repo}"
        for user in COLLABORATORS:
            ok, msg = add_collaborator(token, owner, repo, user, PERMISSION)
            if ok:
                print(f"  {full}  {user}: {msg}")
            else:
                print(f"  {full}  {user}: FAIL - {msg}", file=sys.stderr)
                failed.append((owner, repo, user, msg))

    if failed:
        print(f"\n{len(failed)} failures.", file=sys.stderr)
        return 1
    print("\nAll collaborators set.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
