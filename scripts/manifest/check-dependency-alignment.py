#!/usr/bin/env python3
"""Check dependency alignment: derived manifest vs workspace-manifest.json.

Compares:
  1. Internal deps: pyproject.toml (derived) vs manifest repositories.<repo>.dependencies
  2. External deps: pyproject.toml vs workspace-constraints.toml / canonical-dependency-manifest.json

Run generate-derived-manifest.py first.

Usage:
    python check-dependency-alignment.py
    python check-dependency-alignment.py --repo instruments-service
    python check-dependency-alignment.py --json

Exit: 0 = aligned, 1 = misalignments found.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
PM_ROOT = SCRIPT_DIR.parent.parent
DERIVED_PATH = PM_ROOT / "derived-dependency-manifest.json"
MANIFEST_PATH = PM_ROOT / "workspace-manifest.json"
CANONICAL_PATH = PM_ROOT / "canonical-dependency-manifest.json"


def load_json(path: Path) -> dict[str, Any]:
    with open(path) as f:
        return json.load(f)


def normalize(name: str) -> str:
    return name.lower().replace("_", "-").strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", help="Check single repo only")
    parser.add_argument("--json", action="store_true", help="Machine-readable output")
    args = parser.parse_args()

    if not DERIVED_PATH.is_file():
        print(f"ERROR: Run generate-derived-manifest.py first. Missing: {DERIVED_PATH}", file=sys.stderr)
        return 1
    if not MANIFEST_PATH.is_file():
        print(f"ERROR: Manifest not found: {MANIFEST_PATH}", file=sys.stderr)
        return 1

    derived = load_json(DERIVED_PATH)
    manifest = load_json(MANIFEST_PATH)
    canonical: dict[str, str] = {}
    if CANONICAL_PATH.is_file():
        c = load_json(CANONICAL_PATH)
        for p in c.get("externalPackages", []):
            canonical[normalize(p["name"])] = p.get("versionRange", "")

    repos = derived.get("repositories", {})
    if args.repo:
        repos = {k: v for k, v in repos.items() if k == args.repo}
        if not repos:
            print(f"ERROR: Repo not found: {args.repo}", file=sys.stderr)
            return 1

    issues: list[dict[str, Any]] = []
    manifest_repos = manifest.get("repositories", {})

    for repo_name, data in repos.items():
        if data.get("skipped"):
            continue
        manifest_entry = manifest_repos.get(repo_name, {})
        manifest_deps = {
            normalize(d["name"]): d.get("version", "")
            for d in manifest_entry.get("dependencies", [])
            if isinstance(d, dict) and "name" in d
        }

        derived_internal = data.get("internal_deps", {})
        derived_external = data.get("external_deps", {})

        for dep in derived_internal:
            if dep not in manifest_deps:
                issues.append({"repo": repo_name, "type": "internal_in_pyproject_not_manifest", "dep": dep})
        for dep in manifest_deps:
            if dep not in derived_internal:
                issues.append({"repo": repo_name, "type": "internal_in_manifest_not_pyproject", "dep": dep})

        for pkg, specs in derived_external.items():
            if pkg in canonical:
                canon_spec = canonical[pkg]
                for spec in specs:
                    if spec != canon_spec:
                        issues.append(
                            {
                                "repo": repo_name,
                                "type": "external_version_mismatch",
                                "dep": pkg,
                                "pyproject_spec": spec,
                                "canonical_spec": canon_spec,
                            }
                        )

    if args.json:
        print(json.dumps({"aligned": len(issues) == 0, "issues": issues, "count": len(issues)}, indent=2))
    else:
        if not issues:
            print("OK: All dependencies aligned with manifest and canonical constraints.")
            return 0
        print(f"Found {len(issues)} misalignment(s):\n")
        for i in issues:
            print(f"  [{i['repo']}] {i['type']}: {i['dep']}")
            if "pyproject_spec" in i:
                print(f"    pyproject: {i['pyproject_spec']}")
                print(f"    canonical: {i['canonical_spec']}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
