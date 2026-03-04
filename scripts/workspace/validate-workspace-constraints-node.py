#!/usr/bin/env python3
"""Validate UI package.json deps against workspace-constraints-node.json.

Checks that Node/frontend repos use versions within canonical ranges.
SSOT: unified-trading-pm/workspace-constraints-node.json.

Usage:
    python validate-workspace-constraints-node.py
    python validate-workspace-constraints-node.py --repo deployment-ui

Exit: 0 = aligned or no constraints; 1 = drift or error.
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
CONSTRAINTS_PATH = PM_ROOT / "workspace-constraints-node.json"


def in_range(actual: str, canonical: str) -> bool:
    """Heuristic: actual satisfies canonical range."""
    if not canonical or "file:" in str(actual):
        return True
    actual_clean = re.sub(r"^[\^~]", "", str(actual))
    canon_clean = re.sub(r"^[\^~]", "", str(canonical))
    if actual_clean == canon_clean:
        return True
    m = re.match(r"^(\d+)\.(\d+)\.(\d+)", canon_clean)
    if not m:
        return True
    canon_major = int(m.group(1))
    m2 = re.match(r"^(\d+)\.(\d+)\.(\d+)", actual_clean)
    if not m2:
        return True
    actual_major = int(m2.group(1))
    if str(canonical).startswith("^"):
        return actual_major >= canon_major
    return True


def load_constraints() -> dict[str, dict[str, str]]:
    """Load dependencies and devDependencies from workspace-constraints-node.json."""
    if not CONSTRAINTS_PATH.is_file():
        return {}
    data = json.loads(CONSTRAINTS_PATH.read_text(encoding="utf-8"))
    result: dict[str, dict[str, str]] = {}
    for key in ("dependencies", "devDependencies"):
        if key in data and isinstance(data[key], dict):
            result[key] = {k: str(v) for k, v in data[key].items()}
    return result


def check_package(repo_path: Path, constraints: dict[str, dict[str, str]]) -> list[str]:
    """Check one package.json; return list of drift messages."""
    pkg_path = repo_path / "package.json"
    if not pkg_path.is_file():
        return []
    pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
    drifts: list[str] = []
    for dep_type in ("dependencies", "devDependencies"):
        if dep_type not in constraints:
            continue
        canon = constraints[dep_type]
        deps = pkg.get(dep_type) or {}
        for name, actual in deps.items():
            if name.startswith("@unified-trading/") or "file:" in str(actual):
                continue
            if name in canon and not in_range(str(actual), canon[name]):
                drifts.append(f"{repo_path.name}: {name} {actual} outside canonical {canon[name]}")
    return drifts


def find_ui_repos() -> list[Path]:
    """Find UI repos from manifest or workspace."""
    manifest_path = PM_ROOT / "workspace-manifest.json"
    if manifest_path.is_file():
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        repos = data.get("repositories") or {}
        ui_repos = []
        for name, meta in repos.items():
            if isinstance(meta, dict) and meta.get("type") == "ui":
                path = WORKSPACE_ROOT / name
                if (path / "package.json").is_file():
                    ui_repos.append(path)
        if ui_repos:
            return ui_repos
    return [
        d
        for d in WORKSPACE_ROOT.iterdir()
        if d.is_dir() and (d / "package.json").is_file() and "node_modules" not in str(d) and d.name != "src"
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Node deps against workspace-constraints-node.json")
    parser.add_argument("--repo", help="Check only this repo")
    parser.add_argument("-q", "--quiet", action="store_true")
    args = parser.parse_args()

    if not CONSTRAINTS_PATH.is_file():
        print(f"ERROR: {CONSTRAINTS_PATH} not found", file=sys.stderr)
        return 1

    constraints = load_constraints()
    if not constraints:
        print("ERROR: No dependencies in workspace-constraints-node.json", file=sys.stderr)
        return 1

    repos = [WORKSPACE_ROOT / args.repo] if args.repo else find_ui_repos()
    if args.repo and not repos[0].is_dir():
        print(f"ERROR: Repo {args.repo} not found", file=sys.stderr)
        return 1

    all_drifts = []
    for repo in sorted(repos, key=lambda p: p.name):
        all_drifts.extend(check_package(repo, constraints))

    if all_drifts:
        for d in all_drifts:
            print(d, file=sys.stderr)
        return 1
    if not args.quiet:
        print("Node constraints OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
