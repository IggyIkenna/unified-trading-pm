#!/usr/bin/env python3.13
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""
Create GitHub repos (if missing) and add datadodo + CosmicTrader as admin.
Uses GH_PAT or GITHUB_TOKEN (same as instruments-service / Cloud Build).
Run from workspace root.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import urllib.error
import urllib.request
from http.client import HTTPResponse
from typing import cast

logger = logging.getLogger(__name__)
# Token: GH_PAT, GITHUB_TOKEN, or gh auth token (GitHub CLI — run gh auth login if prompted)
GITHUB_API = "https://api.github.com"
OWNER = "IggyIkenna"
COLLABORATORS = ("datadodo", "CosmicTrader")
PERMISSION = "admin"

# Repos to ensure exist (create if 404)
REPOS_TO_CREATE = [
    "deployment-ui",
    "execution-results-api",
    "features-sports-service",
    "strategy-ui",
    "unified-sports-execution-interface",
    "features-cross-instrument-service",
    "features-multi-timeframe-service",
    "unified-defi-execution-interface",
    "unified-feature-calculator-library",
    "unified-position-interface",
    "client-reporting-api",
]

# Short descriptions from manifest / convention
DESCRIPTIONS: dict[str, str] = {
    "client-reporting-api": "Client reporting API — FastAPI + OAuth; proxies pnl-attribution-service",
    "deployment-ui": "Deployment management UI — orchestrator status, Cloud Build logs",
    "execution-results-api": "Execution results API — FastAPI backend for backtest/execution UIs",
    "features-sports-service": "Sports features service — match/player/referee/venue/weather/H2H features",
    "strategy-ui": "Strategy configuration and deployment UI",
    "unified-sports-execution-interface": "Sports execution interface — BaseSportsAdapter, Betfair, Pinnacle",
    "features-cross-instrument-service": "Cross-instrument feature aggregation service",
    "unified-defi-execution-interface": "DeFi execution interface — Tier 2 library",
    "unified-feature-calculator-library": "Feature calculator library — Tier 2",
    "unified-position-interface": "Position interface — per-client position feeds",
    "features-multi-timeframe-service": (
        "Multi-timeframe feature service — tf_momentum | tf_structure | tf_vol | tf_session"
    ),
}


def get_token() -> str | None:
    token = os.environ.get("GH_PAT") or os.environ.get("GITHUB_TOKEN")
    if token:
        return token
    try:
        out = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if out.returncode == 0 and out.stdout:
            return out.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        logger.debug("Suppressed %s during get token: %s", type(e).__name__, e)
        pass
    return None


def api_request(
    token: str,
    method: str,
    path: str,
    data: dict[str, str | bool] | None = None,
) -> tuple[int, str]:
    """Return (status_code, body_or_message)."""
    url = f"{GITHUB_API}{path}" if path.startswith("/") else f"{GITHUB_API}/{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json",
        },
    )
    try:
        resp = cast(HTTPResponse, urllib.request.urlopen(req, timeout=30))  # nosec B310 — URL is GitHub API hardcoded https endpoint
        return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, (e.read().decode() if e.fp else str(e))
    except (OSError, ValueError) as e:
        return -1, str(e)


def repo_exists(token: str, repo: str) -> bool:
    code, _ = api_request(token, "GET", f"/repos/{OWNER}/{repo}")
    return code == 200


def create_repo(token: str, repo: str, description: str) -> tuple[bool, str]:
    code, body = api_request(
        token,
        "POST",
        "/user/repos",
        {"name": repo, "private": True, "description": description},
    )
    if code in (201, 202):
        return True, "created"
    if code == 422 and "name already exists" in body.lower():
        return True, "already exists"
    return False, f"HTTP {code}: {body[:200]}"


def add_collaborator(token: str, repo: str, username: str) -> tuple[bool, str]:
    code, body = api_request(
        token,
        "PUT",
        f"/repos/{OWNER}/{repo}/collaborators/{username}",
        {"permission": PERMISSION},
    )
    if code in (204, 200, 201):
        return True, "ok" if code != 201 else "invitation sent"
    if code == 422 and "already exists" in body.lower():
        return True, "already added"
    return False, f"HTTP {code}: {body[:150]}"


def main() -> int:
    dry = "--dry-run" in sys.argv
    token = get_token()
    if not token and not dry:
        print("No GitHub token. Either:", file=sys.stderr)
        print("  1. Run:  gh auth login   (then re-run this script)", file=sys.stderr)
        print("  2. Or set:  export GH_PAT=ghp_...  or  export GITHUB_TOKEN=ghp_...", file=sys.stderr)
        return 1

    created: list[str] = []
    create_failed: list[tuple[str, str]] = []
    collab_failed: list[tuple[str, str, str]] = []

    assert token is not None  # Validated above
    for repo in REPOS_TO_CREATE:
        desc = DESCRIPTIONS.get(repo, f"Unified Trading System — {repo}")
        if dry:
            print(f"  [dry] would ensure repo: {OWNER}/{repo}")
            continue
        if repo_exists(token, repo):
            print(f"  {repo}: exists")
        else:
            ok, msg = create_repo(token, repo, desc)
            if ok:
                created.append(repo)
                print(f"  {repo}: {msg}")
            else:
                create_failed.append((repo, msg))
                print(f"  {repo}: FAIL — {msg}", file=sys.stderr)

    if dry:
        print(f"\nWould ensure {len(REPOS_TO_CREATE)} repos and add {COLLABORATORS} as admin.")
        return 0

    # Add collaborators to all REPOS_TO_CREATE (whether we just created or already existed)
    for repo in REPOS_TO_CREATE:
        if repo in [r for r, _ in create_failed]:
            continue
        for user in COLLABORATORS:
            ok, msg = add_collaborator(token, repo, user)
            if ok:
                print(f"  {repo} {user}: {msg}")
            else:
                collab_failed.append((repo, user, msg))
                print(f"  {repo} {user}: FAIL — {msg}", file=sys.stderr)

    if created:
        print(f"\nCreated: {', '.join(created)}")
    if create_failed:
        print(f"Create failed: {len(create_failed)}", file=sys.stderr)
    if collab_failed:
        print(f"Collaborator failed: {len(collab_failed)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
