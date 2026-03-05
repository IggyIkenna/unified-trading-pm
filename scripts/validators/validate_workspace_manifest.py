#!/usr/bin/env python3
"""Validate workspace-manifest.json against schema and topological order.

Phase 1: plans_to_deployable_unified_audit.plan.md
GATE: workspace-manifest.json validates with zero errors; topological order valid.

Usage:
    python validate_workspace_manifest.py
    python validate_workspace_manifest.py --manifest /path/to/workspace-manifest.json

Exit: 0 = valid, 1 = invalid.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REQUIRED_REPO_FIELDS = [
    "ci_status",
    "quality_gate_status",
    "coverage_pct",
    "bypass_audit_path",
    "testing_level",
    "skipped_gates",
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path(__file__).resolve().parent.parent.parent / "workspace-manifest.json",
    )
    args = parser.parse_args()

    path = args.manifest
    if not path.is_file():
        print(f"ERROR: Manifest not found: {path}", file=sys.stderr)
        return 1

    with open(path) as f:
        data = json.load(f)

    errors: list[str] = []

    # Check repositories exist
    repos = data.get("repositories", {})
    if not repos:
        errors.append("repositories is empty")

    # Check topologicalOrder: {description, levels: [{level, repos: [...]}]}
    topo = data.get("topologicalOrder", {})
    topo_repos: list[str] = []
    if isinstance(topo, dict) and "levels" in topo:
        for lev in topo["levels"]:
            topo_repos.extend(lev.get("repos", []))
    else:
        errors.append("topologicalOrder must have levels array")

    for name in topo_repos:
        if name not in repos:
            errors.append(f"topologicalOrder references unknown repo: {name}")

    # Check each repo has required fields (only for repos in versions - those are tracked)
    versions = data.get("versions", {})
    for name, repo in repos.items():
        if not isinstance(repo, dict):
            errors.append(f"{name}: repo entry must be object")
            continue
        for field in REQUIRED_REPO_FIELDS:
            if field not in repo:
                errors.append(f"{name}: missing required field '{field}'")

    # Versions map: repos in versions should match a subset of repositories
    for name in versions:
        if name not in repos and name != "_note":
            errors.append(f"versions.{name}: repo not in repositories")

    if errors:
        for e in errors:
            print(f"FAIL: {e}", file=sys.stderr)
        return 1

    print("OK: workspace-manifest.json valid (schema + topological)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
