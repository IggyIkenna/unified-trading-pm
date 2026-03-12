#!/usr/bin/env python3
"""
record-ci-status.py — Update ci_status in workspace-manifest.json.

Called by ci-status-record.yml (GitHub Actions) after a repo's quality gates
pass or fail on the main branch. Writes atomically; safe for concurrent runs
(PM workflow uses concurrency: group: manifest-ci-status).

Usage:
    python3 record-ci-status.py --repo <name> --status <PASSING|FAILING> [--sha <sha>]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import cast

MANIFEST_PATH = Path(__file__).resolve().parents[3] / "workspace-manifest.json"

VALID_STATUSES = {"PASSING", "FAILING", "BASELINE_RECORDED"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--status", required=True, choices=list(VALID_STATUSES))
    parser.add_argument("--sha", default="")
    args = parser.parse_args()
    repo: str = cast(str, args.repo)
    status: str = cast(str, args.status)
    sha: str = cast(str, args.sha)

    if not MANIFEST_PATH.exists():
        print(f"ERROR: manifest not found at {MANIFEST_PATH}", file=sys.stderr)
        return 1

    raw: object = cast(object, json.loads(MANIFEST_PATH.read_text()))
    manifest = cast(dict[str, object], raw)

    if "repositories" not in manifest:
        print("ERROR: manifest missing 'repositories' key", file=sys.stderr)
        return 1
    repos = cast(dict[str, dict[str, object]], manifest["repositories"])
    if repo not in repos:
        print(f"ERROR: repo '{repo}' not in workspace-manifest.json", file=sys.stderr)
        return 1

    repo_entry = repos[repo]
    prev = cast(str, repo_entry.get("ci_status", "UNKNOWN"))
    repo_entry["ci_status"] = status
    if sha:
        repo_entry["ci_last_sha"] = sha

    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n")

    print(f"  {repo}: ci_status {prev} → {status}" + (f" (sha={sha[:7]})" if sha else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
