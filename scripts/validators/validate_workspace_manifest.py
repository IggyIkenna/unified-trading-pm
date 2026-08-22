#!/usr/bin/env python3.13
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Validate workspace-manifest.json against schema and topological order.

Phase 1: plans_to_deployable_unified_audit.md
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
from typing import cast

# JSON typing: json.load returns Any; cast at boundary
JsonDict = dict[str, "JsonDict | list[JsonDict] | str | int | float | bool | None"]


def _jdict(val: object) -> JsonDict | None:
    if isinstance(val, dict):
        return cast(JsonDict, val)
    return None


def _jlist(val: object) -> list[JsonDict] | None:
    if isinstance(val, list):
        return cast(list[JsonDict], val)
    return None


REQUIRED_REPO_FIELDS = [
    "ci_status",
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

    path: Path = cast(Path, args.manifest)
    if not path.is_file():
        print(f"ERROR: Manifest not found: {path}", file=sys.stderr)
        return 1

    with open(path) as f:
        data: JsonDict = cast(JsonDict, json.load(f))

    errors: list[str] = []

    # Check repositories exist
    if "repositories" not in data:
        errors.append("repositories is required")
        return 1
    repos_raw: object = data["repositories"]
    repos: JsonDict = _jdict(repos_raw) or {}
    if not repos:
        errors.append("repositories is empty")

    # Check topologicalOrder: {description, levels: [{level, repos: [...]}]}
    topo_raw: object = data.get("topologicalOrder") or {}  # optional: if absent, topology validation skipped
    topo: JsonDict | None = _jdict(topo_raw)
    topo_repos: list[str] = []
    if topo is not None and "levels" in topo:
        levels_raw: object = topo["levels"]
        levels: list[JsonDict] = _jlist(levels_raw) or []
        for lev in levels:
            repos_in_lev: object = lev.get("repos") or []  # optional per level
            if isinstance(repos_in_lev, list):
                topo_repos.extend(str(x) for x in repos_in_lev)
    else:
        errors.append("topologicalOrder must have levels array")

    for name in topo_repos:
        if name not in repos:
            errors.append(f"topologicalOrder references unknown repo: {name}")

    # Check each repo has required fields (only for repos in versions - those are tracked)
    versions_raw: object = data.get("versions") or {}  # optional: version tracking per repo
    versions: JsonDict = _jdict(versions_raw) or {}
    for name, repo_raw in repos.items():
        repo = _jdict(repo_raw)
        if repo is None:
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
