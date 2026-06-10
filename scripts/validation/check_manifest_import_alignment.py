#!/usr/bin/env python3
"""Validate workspace-manifest.json dependencies match actual Python imports.

For each repo: validate dependencies[] match actual Python imports.
Fail when:
  (a) repo declares dep X in manifest but does not import it
  (b) repo imports Y (from unified_* or workspace sibling) but does not declare it

Excludes: tests/, scripts/, .github/, conftest.py
Maps manifest dep name (e.g. "unified-domain-client") to import package (e.g. "unified_domain_client").

Usage:
    python check_manifest_import_alignment.py [--repo PATH] [--workspace-root PATH]

Exit: 0 if aligned, 1 if misaligned, 2 on usage error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# tests/ EXCLUDED (2026-06-10, reconciling the code with the docstring which always said
# "Excludes: tests/"): the prior in-code comment ("tests/ included because flat deps means
# test-only deps are in [project.dependencies]") conflated EXTERNAL pip deps (where flat-deps
# does put test deps in [project.dependencies]) with INTERNAL manifest repo edges — a
# tests-only import of a workspace SIBLING (e.g. deployment-service tests importing
# deployment_api fixtures) must NOT force a manifest dependencies[] edge: it would create
# false build/DAG edges (and reverse edges = cycles). Source-tree imports remain fully scanned.
# Incident: the parity gap blocked the FROM-digest pilot ship (ci_local_qg_parity P2).
EXCLUDE_SEGMENTS = {"tests", "scripts", ".github", ".venv", "venv", "__pycache__", "build"}
EXCLUDE_FILENAMES = {"conftest.py"}

# Patterns for Python imports
FROM_IMPORT_RE = re.compile(r"^\s*from\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)\s+import")
IMPORT_RE = re.compile(r"^\s*import\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)")


def manifest_name_to_import(name: str) -> str:
    """Map manifest repo name (e.g. unified-domain-client) to import package (e.g. unified_domain_client)."""
    return name.replace("-", "_")


def should_skip_path(rel_path: Path) -> bool:
    """Return True if path should be excluded from scanning."""
    parts = rel_path.parts
    if any(seg in parts for seg in EXCLUDE_SEGMENTS):
        return True
    return rel_path.name in EXCLUDE_FILENAMES


def extract_imports_from_file(file_path: Path) -> set[str]:
    """Extract top-level package names from import statements in a Python file."""
    packages: set[str] = set()
    try:
        content = file_path.read_text(encoding="utf-8")
    except (OSError, ValueError):
        return packages
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("#"):
            continue
        for pattern in (FROM_IMPORT_RE, IMPORT_RE):
            m = pattern.match(line)
            if m:
                full = m.group(1)
                top_level = full.split(".")[0]
                packages.add(top_level)
                break
    return packages


def scan_repo_imports(repo_path: Path) -> set[str]:
    """Scan all .py files in repo (excluding tests/, scripts/, .github/, conftest.py) for imports."""
    all_packages: set[str] = set()
    for py_path in repo_path.rglob("*.py"):
        try:
            rel = py_path.relative_to(repo_path)
        except ValueError:
            continue
        if should_skip_path(rel):
            continue
        all_packages |= extract_imports_from_file(py_path)
    return all_packages


def get_workspace_sibling_imports(manifest_repos: dict) -> set[str]:
    """Return set of import package names for all workspace sibling repos."""
    return {manifest_name_to_import(name) for name in manifest_repos}


def filter_workspace_imports(imports: set[str], sibling_imports: set[str]) -> set[str]:
    """Return only imports that are workspace siblings (unified_* or in sibling set)."""
    result: set[str] = set()
    for pkg in imports:
        if pkg.startswith("unified_") or pkg in sibling_imports:
            result.add(pkg)
    return result


def get_same_repo_packages(repo_path: Path) -> set[str]:
    """Return top-level package names that exist in this repo (same-repo imports)."""
    packages: set[str] = set()
    for candidate in [repo_path, repo_path / "src"]:
        if not candidate.is_dir():
            continue
        for child in candidate.iterdir():
            if child.is_dir() and not child.name.startswith("."):
                init = child / "__init__.py"
                if init.exists():
                    packages.add(child.name)
    return packages


def check_repo(
    repo_name: str,
    repo_path: Path,
    declared_deps: set[str],
    sibling_imports: set[str],
) -> tuple[bool, list[str]]:
    """Check a single repo. Return (ok, list of error messages)."""
    errors: list[str] = []
    declared_imports = {manifest_name_to_import(d) for d in declared_deps}

    if not repo_path.is_dir():
        return True, []  # Skip missing repos

    py_files = list(repo_path.rglob("*.py"))
    if not py_files:
        return True, []  # No Python, skip

    actual_imports = scan_repo_imports(repo_path)
    workspace_imports = filter_workspace_imports(actual_imports, sibling_imports)
    self_import = manifest_name_to_import(repo_name)
    same_repo_packages = get_same_repo_packages(repo_path)

    # (a) Declared but not imported
    for decl in declared_imports:
        if decl not in workspace_imports:
            errors.append(f"{repo_name}: declares dep {decl.replace('_', '-')} but does not import it")

    # (b) Imported but not declared (exclude self-imports and same-repo packages)
    for imp in workspace_imports:
        if imp == self_import or imp in same_repo_packages:
            continue
        if imp not in declared_imports:
            errors.append(f"{repo_name}: imports {imp} but does not declare it in manifest")

    return len(errors) == 0, errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate manifest dependencies match actual Python imports")
    parser.add_argument(
        "--repo",
        type=Path,
        help="Check only this repo path (e.g. ../execution-service)",
    )
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=None,
        help="Workspace root (default: parent of unified-trading-pm)",
    )
    args = parser.parse_args()

    pm_dir = Path(__file__).resolve().parent.parent.parent
    workspace_root = args.workspace_root or pm_dir.parent
    manifest_path = pm_dir / "workspace-manifest.json"

    if not manifest_path.exists():
        print(f"Error: manifest not found: {manifest_path}", file=sys.stderr)
        return 2

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        print(f"Error: failed to load manifest: {e}", file=sys.stderr)
        return 2

    repos = manifest.get("repositories", {})  # noqa: qg-empty-fallback
    if not repos:
        print("Error: no repositories in manifest", file=sys.stderr)
        return 2

    sibling_imports = get_workspace_sibling_imports(repos)

    if args.repo:
        repo_path = Path(args.repo).resolve()
        if not repo_path.is_dir():
            print(f"Error: repo path not found: {repo_path}", file=sys.stderr)
            return 2
        repo_name = repo_path.name
        cfg = repos.get(repo_name)
        if not cfg:
            print(f"Error: repo {repo_name} not in manifest", file=sys.stderr)
            return 2
        declared = {d["name"] for d in cfg.get("dependencies", []) if isinstance(d, dict) and d.get("name")}  # noqa: qg-empty-fallback
        ok, errors = check_repo(repo_name, repo_path, declared, sibling_imports)
        if not ok:
            for e in errors:
                print(e, file=sys.stderr)
            return 1
        return 0

    all_errors: list[str] = []
    for repo_name, cfg in repos.items():
        repo_path = workspace_root / repo_name
        declared = {d["name"] for d in cfg.get("dependencies", []) if isinstance(d, dict) and d.get("name")}  # noqa: qg-empty-fallback
        ok, errors = check_repo(repo_name, repo_path, declared, sibling_imports)
        all_errors.extend(errors)

    if all_errors:
        for e in all_errors:
            print(e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
