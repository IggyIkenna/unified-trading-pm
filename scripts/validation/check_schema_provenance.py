#!/usr/bin/env python3
"""
Check schema provenance: local BaseModel/TypedDict/dataclass definitions should live in
unified-api-contracts or unified-internal-contracts. Flags violations.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

WORKSPACE_ROOT = Path("/Users/ikennaigboaka/Code/unified-trading-system-repos")
MANIFEST_PATH = WORKSPACE_ROOT / "unified-trading-pm" / "workspace-manifest.json"

EXCLUDED_REPOS = {"unified-api-contracts", "unified-internal-contracts"}

# Patterns for schema definitions
CLASS_BASEMODEL_RE = re.compile(r"class\s+(\w+)\s*\(\s*[^)]*BaseModel\s*[^)]*\)")
CLASS_TYPEDDICT_RE = re.compile(r"class\s+(\w+)\s*\(\s*[^)]*TypedDict\s*[^)]*\)")
CLASS_DATACLASS_RE = re.compile(r"@\s*dataclass\s*\n\s*class\s+(\w+)\s*\(", re.MULTILINE)
CLASS_DATACLASS_NO_PAREN_RE = re.compile(r"@\s*dataclass\s*\n\s*class\s+(\w+)\s*:", re.MULTILINE)

# Import from UAC/UIC
IMPORT_UAC_UIC_RE = re.compile(
    r"from\s+(unified_api_contracts|unified_internal_contracts)(?:\.\w+)?\s+import\s+([^;\n]+)",
    re.MULTILINE,
)


def should_exclude_file(rel_path: str) -> bool:
    """Exclude tests/, .venv, build/, output_schemas.py, __init__.py."""
    parts = Path(rel_path).parts
    if "tests" in parts or ".venv" in parts or "build" in parts:
        return True
    if rel_path.endswith("__init__.py"):
        return True
    if "output_schemas.py" in rel_path:
        return True
    return False


def has_schema_provenance_exempt(filepath: Path) -> bool:
    """Exempt files with # SCHEMA_PROVENANCE_EXEMPT in first 20 lines."""
    try:
        text = filepath.read_text(encoding="utf-8")
        for line in text.splitlines()[:20]:
            if "SCHEMA_PROVENANCE_EXEMPT" in line and "#" in line:
                return True
    except OSError:
        pass
    return False


def find_schema_definitions(content: str) -> list[str]:
    """Extract schema class names from file content."""
    found: set[str] = set()
    for pat in (CLASS_BASEMODEL_RE, CLASS_TYPEDDICT_RE, CLASS_DATACLASS_RE, CLASS_DATACLASS_NO_PAREN_RE):
        for m in pat.finditer(content):
            found.add(m.group(1))
    return sorted(found)


def schema_imported_from_uac_uic(repo_path: Path, schema_name: str) -> bool:
    """Check if schema_name is imported from unified_api_contracts or unified_internal_contracts anywhere in repo."""
    for py_file in repo_path.rglob("*.py"):
        rel = py_file.relative_to(repo_path)
        if should_exclude_file(str(rel)):
            continue
        try:
            text = py_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for m in IMPORT_UAC_UIC_RE.finditer(text):
            imports_str = m.group(2)
            for part in imports_str.split(","):
                part = part.strip()
                name = part.split(" as ")[0].strip()
                if name == schema_name:
                    return True
    return False


def scan_repo(repo_path: Path, repo_name: str) -> list[tuple[str, str]]:
    """Scan repo for local schema definitions. Return [(file, class_name), ...] for violations."""
    violations: list[tuple[str, str]] = []
    if not repo_path.is_dir():
        return violations

    for py_file in repo_path.rglob("*.py"):
        rel = py_file.relative_to(repo_path)
        rel_str = str(rel)
        if should_exclude_file(rel_str):
            continue
        if has_schema_provenance_exempt(py_file):
            continue
        try:
            content = py_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        schemas = find_schema_definitions(content)
        for schema_name in schemas:
            violations.append((rel_str, schema_name))

    return violations


def load_repos_from_manifest(manifest_path: Path | None = None) -> list[str]:
    """Load repo names from workspace-manifest.json."""
    path = manifest_path or MANIFEST_PATH
    with open(path, encoding="utf-8") as f:
        m = json.load(f)
    repos = m.get("repositories", [])  # noqa: qg-empty-fallback
    if isinstance(repos, list):
        names = [
            r.get("name", r) if isinstance(r, dict) else r
            for r in repos
            if (r.get("name", r) if isinstance(r, dict) else r) and not str(r).startswith("_")
        ]
    else:
        names = [k for k in repos.keys() if not k.startswith("_")]
    if not names:
        vers = m.get("versions", {})  # noqa: qg-empty-fallback
        names = [k for k in vers.keys() if not k.startswith("_")]
    return names


def main() -> int:
    parser = argparse.ArgumentParser(description="Check schema provenance (UAC/UIC)")
    parser.add_argument("--repo", type=str, help="Single repo name")
    parser.add_argument("--all", action="store_true", help="Scan all repos")
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=WORKSPACE_ROOT,
        help="Workspace root path",
    )
    args = parser.parse_args()

    if not args.repo and not args.all:
        parser.error("Specify --repo NAME or --all")

    workspace_root = args.workspace_root

    manifest = workspace_root / "unified-trading-pm" / "workspace-manifest.json"
    if not manifest.exists():
        print(f"Error: manifest not found: {manifest}", file=sys.stderr)
        return 2

    repos = load_repos_from_manifest(manifest)
    repos = [r for r in repos if r not in EXCLUDED_REPOS]

    if args.repo:
        if args.repo not in repos and args.repo not in EXCLUDED_REPOS:
            print(f"Error: repo '{args.repo}' not in manifest", file=sys.stderr)
            return 2
        repos = [args.repo] if args.repo not in EXCLUDED_REPOS else []

    all_violations: list[tuple[str, str, str]] = []
    for repo_name in repos:
        repo_path = workspace_root / repo_name
        violations = scan_repo(repo_path, repo_name)
        for file_path, class_name in violations:
            all_violations.append((repo_name, file_path, class_name))

    for repo_name, file_path, class_name in all_violations:
        print(f"{repo_name}:{file_path}:{class_name}")

    return 1 if all_violations else 0


if __name__ == "__main__":
    sys.exit(main())
