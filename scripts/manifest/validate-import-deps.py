#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Validate service import hygiene:

1. Every direct import of an internal library must have a corresponding
   [project.dependencies] + [tool.uv.sources] entry.
2. Services MUST NOT import directly from banned libraries (config/cloud/events
   interfaces) — use unified-trading-library re-exports instead.

Usage:
    python validate-import-deps.py          # report only
    python validate-import-deps.py --fix    # auto-add missing deps + sources
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[3]  # workspace root

# Map Python import name → package name in pyproject.toml
INTERNAL_PACKAGES: dict[str, str] = {
    "unified_trading_library": "unified-trading-library",
    "unified_api_contracts": "unified-api-contracts",
    "unified_trading_library.cloud_interface": "unified-cloud-interface",
    "unified_trading_library.config_interface": "unified-config-interface",
    "unified_trading_library.events": "unified-events-interface",
    "unified_market_interface": "unified-market-interface",
    "unified_reference_data_interface": "unified-reference-data-interface",
}

# =========================================================================
# BANNED DIRECT IMPORTS — services must use UTL re-exports instead
# =========================================================================
BANNED_DIRECT_IMPORTS: frozenset[str] = frozenset(
    {
        "unified_trading_library.config_interface",
        "unified_trading_library.cloud_interface",
        "unified_trading_library.events",
    }
)

# Per-service allowed direct deps (beyond UTL/UAC/UIC)
# deployment-service is fully exempt — not listed here, handled by EXEMPT_REPOS
ALLOWED_DIRECT_DEPS: dict[str, frozenset[str]] = {
    "instruments-service": frozenset({"unified_reference_data_interface"}),
    "market-tick-data-service": frozenset({"unified_market_interface"}),
    "market-data-processing-service": frozenset({"unified_market_interface"}),
    "features-sports-service": frozenset(
        {
            "unified_market_interface",
            "unified_reference_data_interface",
        }
    ),
    "features-calendar-service": frozenset(set()),
    "features-commodity-service": frozenset({"unified_api_contracts"}),
    "features-cross-instrument-service": frozenset({"unified_api_contracts"}),
    "features-delta-one-service": frozenset(set()),
    "features-multi-timeframe-service": frozenset({"unified_api_contracts"}),
    "features-onchain-service": frozenset({"unified_api_contracts"}),
    "features-volatility-service": frozenset(set()),
    "execution-service": frozenset(set()),
    "ml-inference-service": frozenset(set()),
    "ml-training-service": frozenset(set()),
    "position-balance-monitor-service": frozenset(set()),
    "strategy-service": frozenset(set()),
}

# Fully exempt repos — not checked for banned imports at all
EXEMPT_REPOS: frozenset[str] = frozenset(
    {
        "deployment-service",
        "deployment-api",
    }
)

FIX = "--fix" in sys.argv


def scan_imports(src_dir: Path) -> set[str]:
    """Return set of internal import names used in source."""
    imported: set[str] = set()
    for f in src_dir.rglob("*.py"):
        try:
            tree = ast.parse(f.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    top = node.module.split(".")[0]
                    if top in INTERNAL_PACKAGES:
                        imported.add(top)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        top = alias.name.split(".")[0]
                        if top in INTERNAL_PACKAGES:
                            imported.add(top)
        except (OSError, UnicodeDecodeError, SyntaxError):
            pass
    return imported


def scan_banned_imports(src_dir: Path) -> list[tuple[Path, int, str]]:
    """Return list of (file, line, module) for banned direct imports."""
    violations: list[tuple[Path, int, str]] = []
    for f in src_dir.rglob("*.py"):
        try:
            tree = ast.parse(f.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    top = node.module.split(".")[0]
                    if top in BANNED_DIRECT_IMPORTS:
                        violations.append((f, node.lineno, top))
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        top = alias.name.split(".")[0]
                        if top in BANNED_DIRECT_IMPORTS:
                            violations.append((f, node.lineno, top))
        except (OSError, UnicodeDecodeError, SyntaxError):
            pass
    return violations


def get_declared_deps(pyproject: dict) -> set[str]:
    """Return set of package names in [project.dependencies]."""
    deps = pyproject.get("project", {}).get("dependencies", [])  # noqa: qg-empty-fallback
    names: set[str] = set()
    for d in deps:
        name = d.split(">=")[0].split("<=")[0].split("==")[0].split("<")[0].split(">")[0].strip()
        names.add(name)
    return names


def get_uv_sources(pyproject: dict) -> set[str]:
    """Return set of package names in [tool.uv.sources]."""
    return set(pyproject.get("tool", {}).get("uv", {}).get("sources", {}).keys())  # noqa: qg-empty-fallback


def fix_pyproject(pyproject_path: Path, missing_deps: list[str], missing_sources: list[str]) -> None:
    """Add missing deps and uv sources to pyproject.toml."""
    text = pyproject_path.read_text()

    for pkg in missing_deps:
        dep_line = f'    "{pkg}>=0.1.0,<1.0.0",'
        marker = '"unified-trading-library'
        if marker in text:
            idx = text.index(marker)
            end = text.index("\n", idx)
            text = text[: end + 1] + dep_line + "\n" + text[end + 1 :]

    for pkg in missing_sources:
        source_block = f'\n[tool.uv.sources.{pkg}]\npath = "../{pkg}"\neditable = true\n'
        for marker in ["[tool.basedpyright]", "[project]"]:
            if marker in text:
                idx = text.index(marker)
                text = text[:idx] + source_block + "\n" + text[idx:]
                break

    pyproject_path.write_text(text)


def main() -> int:
    import tomllib

    manifest_path = WORKSPACE / "unified-trading-pm" / "workspace-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    repos = manifest.get("repositories", {})  # noqa: qg-empty-fallback

    dep_issues = 0
    banned_violations = 0

    for repo_name in sorted(repos):
        repo_dir = WORKSPACE / repo_name
        if not repo_dir.is_dir() or not (repo_dir / "pyproject.toml").exists():
            continue
        if not repo_name.endswith("-service") and not repo_name.endswith("-api"):
            continue
        if repo_name in EXEMPT_REPOS:
            continue

        src_dir = repo_dir / repo_name.replace("-", "_")
        if not src_dir.exists():
            continue

        imported = scan_imports(src_dir)
        if not imported:
            continue

        # --- Check 1: Banned direct imports (config/cloud/events) ---
        violations = scan_banned_imports(src_dir)
        if violations:
            banned_violations += len(violations)
            print(f"  {repo_name}: {len(violations)} BANNED direct import(s):")
            for fpath, line, mod in violations[:5]:
                rel = fpath.relative_to(repo_dir)
                print(f"    {rel}:{line} — from {mod} (use unified_trading_library instead)")
            if len(violations) > 5:
                print(f"    ... and {len(violations) - 5} more")

        # --- Check 2: Missing deps/sources for allowed imports ---
        with open(repo_dir / "pyproject.toml", "rb") as f:
            pyproject = tomllib.load(f)

        declared = get_declared_deps(pyproject)
        sources = get_uv_sources(pyproject)

        missing_deps = []
        missing_sources = []

        for imp in sorted(imported):
            # Skip banned imports — they should be removed, not declared
            if imp in BANNED_DIRECT_IMPORTS:
                continue
            pkg = INTERNAL_PACKAGES[imp]
            if pkg not in declared:
                missing_deps.append(pkg)
            if pkg not in sources:
                missing_sources.append(pkg)

        if missing_deps or missing_sources:
            dep_issues += len(missing_deps) + len(missing_sources)
            if FIX:
                fix_pyproject(repo_dir / "pyproject.toml", missing_deps, missing_sources)
                print(f"  [FIXED] {repo_name}: +{len(missing_deps)} deps, +{len(missing_sources)} sources")
            else:
                print(f"  {repo_name}:")
                for d in missing_deps:
                    print(f"    [DEP]    {d}")
                for s in missing_sources:
                    print(f"    [SOURCE] {s}")

    # Summary
    total = dep_issues + banned_violations

    if banned_violations:
        print(f"\n  FAIL: {banned_violations} banned direct import(s) found.")
        print("  Services must import from unified_trading_library, not split libraries.")

    if dep_issues == 0 and banned_violations == 0:
        print("OK: All services have correct deps and no banned direct imports.")
        return 0

    if FIX and dep_issues and not banned_violations:
        print(f"\n  Fixed {dep_issues} dep issue(s). No banned imports found.")
        return 0

    print(f"\n  {total} issue(s) found. Banned imports must be fixed manually (use UTL).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
