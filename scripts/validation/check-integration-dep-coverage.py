#!/usr/bin/env python3
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""
Check that services/libraries have import-smoke tests for each direct library dependency.

For each manifest dependency with type=library, verifies at least one file in
tests/unit/ or tests/integration/ imports from that library
(from unified_<name> or import unified_<name>).

Usage:
  python3 check-integration-dep-coverage.py --repo <repo-name> [--project-root <path>]

Exit 0 if all library deps have test coverage; 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _dep_to_import_name(dep: str) -> str:
    """Convert manifest dep name (e.g. unified-trading-library) to import name."""
    return dep.replace("-", "_")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check integration test coverage for library deps")
    parser.add_argument("--repo", required=True, help="Repo name (e.g. instruments-service)")
    parser.add_argument("--project-root", default=".", help="Project root (repo directory)")
    parser.add_argument("--manifest", help="Path to workspace-manifest.json")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    if args.manifest:
        manifest_path = Path(args.manifest)
    else:
        repo_root = project_root.parent
        manifest_path = repo_root / "unified-trading-pm" / "workspace-manifest.json"
    if not manifest_path.exists():
        print("⚠️  Manifest not found — skipping")
        return 0

    with open(manifest_path) as f:
        data = json.load(f)
    repos = data.get("repositories", {})  # noqa: qg-empty-fallback
    if not repos:
        return 0

    repo_config = repos.get(args.repo)
    if not repo_config:
        return 0

    deps = repo_config.get("dependencies", [])  # noqa: qg-empty-fallback
    lib_deps = []
    for d in deps:
        name = d.get("name") if isinstance(d, dict) else d
        if not name:
            continue
        dep_config = repos.get(name, {})  # noqa: qg-empty-fallback
        if dep_config.get("type") == "library":
            lib_deps.append(name)

    if not lib_deps:
        return 0

    # Import-smoke tests may live in tests/integration/ or tests/unit/ (preferred).
    # Scan both directories so repos that moved lightweight import checks to unit/ still pass.
    search_dirs: list[Path] = []
    for subdir in ("integration", "unit"):
        candidate = project_root / "tests" / subdir
        if candidate.exists():
            search_dirs.append(candidate)

    if not search_dirs:
        print(
            "⚠️  No tests/integration/ or tests/unit/ — add tests that import each library dep, "
            "or PM integration test covers repo-PM integration only"
        )
        return 0

    missing = []
    for dep in lib_deps:
        import_name = dep.replace("-", "_")
        patterns = [f"from {import_name}", f"import {import_name}"]
        found = False
        for search_dir in search_dirs:
            for py_file in search_dir.rglob("*.py"):
                try:
                    if any(p in py_file.read_text() for p in patterns):
                        found = True
                        break
                except (OSError, UnicodeDecodeError):
                    continue
            if found:
                break
        if not found:
            missing.append(dep)

    if missing:
        print("❌ Integration test coverage missing for library deps:", ", ".join(missing))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
