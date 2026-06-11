#!/usr/bin/env python3
"""
Check schema provenance: local BaseModel/TypedDict/dataclass definitions should live in
unified-api-contracts (includes unified_api_contracts.internal, formerly unified-internal-contracts).
Flags violations.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

WORKSPACE_ROOT = Path("/Users/ikennaigboaka/Code/unified-trading-system-repos")
MANIFEST_PATH = WORKSPACE_ROOT / "unified-trading-pm" / "workspace-manifest.json"

EXCLUDED_REPOS = {"unified-api-contracts"}

# Build/dependency dirs that NEVER contain repo source schemas — EXCLUDED from the walk so the
# scan never descends into them (these hold third-party / generated code, not repo source). A
# plain repo_path.rglob("*.py") would still enumerate every .venv file — ~14k on a big repo —
# before discarding them per-path. (Naming: these dirs are excluded, not "pruned"/removed.)
EXCLUDE_DIR_NAMES = frozenset(
    {".venv", ".venv-workspace", "venv", "build", "dist", "node_modules", "__pycache__", ".git"}
)


def iter_source_py(repo_path: Path) -> list[Path]:
    """All repo `.py` files, EXCLUDING EXCLUDE_DIR_NAMES dirs (os.walk never descends into them)."""
    out: list[Path] = []
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIR_NAMES]
        out.extend(Path(root) / fn for fn in files if fn.endswith(".py"))
    return out

# Patterns for schema definitions
CLASS_BASEMODEL_RE = re.compile(r"class\s+(\w+)\s*\(\s*[^)]*BaseModel\s*[^)]*\)")
CLASS_TYPEDDICT_RE = re.compile(r"class\s+(\w+)\s*\(\s*[^)]*TypedDict\s*[^)]*\)")
CLASS_DATACLASS_RE = re.compile(r"@\s*dataclass\s*\n\s*class\s+(\w+)\s*\(", re.MULTILINE)
CLASS_DATACLASS_NO_PAREN_RE = re.compile(r"@\s*dataclass\s*\n\s*class\s+(\w+)\s*:", re.MULTILINE)

# Import from UAC/UIC
IMPORT_UAC_UIC_RE = re.compile(
    r"from\s+(unified_api_contracts|unified_api_contracts.internal)(?:\.\w+)?\s+import\s+([^;\n]+)",
    re.MULTILINE,
)


def should_exclude_file(rel_path: str) -> bool:
    """Exclude tests/, scripts/, .venv, build/, output_schemas.py, __init__.py.

    scripts/ is excluded per CLAUDE.md "Schema provenance" rule ("(scripts/ excluded)") — script-internal
    report dataclasses (smoke-matrix CellResult/SmokeReport, pipeline-completeness Result/DateStatus/etc.)
    are NOT domain schemas; pyrightconfig.json + most other QG checks already exclude scripts/. (Harsh slot-2
    Q1.2, 2026-05-11.)
    """
    parts = Path(rel_path).parts
    if "tests" in parts or "scripts" in parts or any(p in EXCLUDE_DIR_NAMES for p in parts):
        return True
    if rel_path.endswith("__init__.py"):
        return True
    return "output_schemas.py" in rel_path


def has_schema_provenance_exempt(filepath: Path) -> bool:
    """Exempt files with # SCHEMA_PROVENANCE_EXEMPT anywhere in the file.

    (Was: first 20 lines only — Harsh slot-1 Q6 fix 2026-05-11: a `# SCHEMA_PROVENANCE_EXEMPT`
    marker near a specific class def, not just in the header, should also exempt the file.)
    """
    try:
        text = filepath.read_text(encoding="utf-8")
        for line in text.splitlines():
            if "SCHEMA_PROVENANCE_EXEMPT" in line and "#" in line:
                return True
    except OSError:
        pass
    return False


def find_schema_definitions(content: str) -> list[str]:
    """Extract schema class names from file content.

    Skips: (a) underscore-prefixed (private) classes — `class _Foo` is service-internal by
    convention; (b) any class whose declaration header carries a `# CORRECT-LOCAL` marker —
    mirrors the `base-service.sh` inline rg-checks (STEP 5.9 / lines ~799-823 / ~1061+) which
    `grep -v '#.*CORRECT-LOCAL'` on the matched class line. (Harsh slot-1 Q6 fix, 2026-05-11 —
    so the per-line `# CORRECT-LOCAL` marker is honored consistently across every QG schema check,
    matching the operator's Q3-A1 disposition: features-service-only types stay local with the marker.
    Harsh slot-2 follow-up 2026-05-12 — the header may span multiple physical lines
    (`class Foo(\n    BM,\n):  # CORRECT-LOCAL ...`); scan the whole header block, not just
    the `class <name>` line, so multi-line signatures honor the marker too.)
    """
    found: set[str] = set()
    lines = content.splitlines()

    def _decl_header(name: str) -> str:
        """Return the full class-declaration header text (start line through the body `:`).

        Handles single-line (`class Foo(BM):  # marker`) and multi-line
        (`class Foo(\n    BaseModel,\n):  # marker`) signatures alike.
        """
        for i, ln in enumerate(lines):
            if not re.search(rf"\bclass\s+{re.escape(name)}\b", ln):
                continue
            block = [ln]
            j = i
            while not ln.split("#", 1)[0].rstrip().endswith(":") and j + 1 < len(lines):
                j += 1
                ln = lines[j]
                block.append(ln)
            return "\n".join(block)
        return ""

    for pat in (CLASS_BASEMODEL_RE, CLASS_TYPEDDICT_RE, CLASS_DATACLASS_RE, CLASS_DATACLASS_NO_PAREN_RE):
        for m in pat.finditer(content):
            name = m.group(1)
            if name.startswith("_"):
                continue
            if "CORRECT-LOCAL" in _decl_header(name):
                continue
            found.add(name)
    return sorted(found)


def collect_uac_uic_imports(py_files: list[Path], repo_path: Path) -> set[str]:
    """All names imported from UAC / UAC.internal across the repo — collected in ONE pass.

    Replaces the former per-schema `schema_imported_from_uac_uic()` which re-walked + re-read the
    ENTIRE repo for every schema name found (O(files * schemas) -> e.g. 157 s on execution-service).
    Same semantics: a name in this set was imported from UAC/UIC by some non-excluded file.
    """
    names: set[str] = set()
    for py_file in py_files:
        rel = py_file.relative_to(repo_path)
        if should_exclude_file(str(rel)):
            continue
        try:
            text = py_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for m in IMPORT_UAC_UIC_RE.finditer(text):
            for part in m.group(2).split(","):
                name = part.strip().split(" as ")[0].strip()
                if name:
                    names.add(name)
    return names


def scan_repo(repo_path: Path, repo_name: str) -> list[tuple[str, str]]:
    """Scan repo for local schema definitions. Return [(file, class_name), ...] for violations."""
    violations: list[tuple[str, str]] = []
    if not repo_path.is_dir():
        return violations

    py_files = iter_source_py(repo_path)  # walk ONCE, .venv/build/etc pruned at the dir level
    # Collect every UAC/UIC-imported name ONCE up front (was an O(n²) full-repo re-walk per schema).
    uac_uic_imported = collect_uac_uic_imports(py_files, repo_path)

    for py_file in py_files:
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

        for schema_name in find_schema_definitions(content):
            # Don't flag a locally-defined type that is ALSO imported from UAC/UIC somewhere in the
            # repo (the local def shadows the canonical — a "use the import" cleanup, not a
            # self-declared-schema violation). O(1) membership vs the old per-schema full re-walk.
            if schema_name in uac_uic_imported:
                continue
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
        names = [k for k in repos if not k.startswith("_")]
    if not names:
        vers = m.get("versions", {})  # noqa: qg-empty-fallback
        names = [k for k in vers if not k.startswith("_")]
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
