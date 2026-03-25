#!/usr/bin/env python3
"""Validate that every direct import of an internal library has a corresponding
[project.dependencies] entry AND [tool.uv.sources] editable entry.

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
    "unified_internal_contracts": "unified-internal-contracts",
    "unified_cloud_interface": "unified-cloud-interface",
    "unified_config_interface": "unified-config-interface",
    "unified_events_interface": "unified-events-interface",
    "unified_market_interface": "unified-market-interface",
    "unified_reference_data_interface": "unified-reference-data-interface",
    "unified_trade_execution_interface": "unified-trade-execution-interface",
    "unified_defi_execution_interface": "unified-defi-execution-interface",
    "unified_sports_execution_interface": "unified-sports-execution-interface",
    "unified_sports_reference_interface": "unified-sports-reference-interface",
    "unified_position_interface": "unified-position-interface",
    "unified_features_interface": "unified-features-interface",
    "unified_feature_calculator_library": "unified-feature-calculator-library",
    "unified_feature_orchestration_library": "unified-feature-orchestration-library",
    "unified_ml_interface": "unified-ml-interface",
    "unified_domain_client": "unified-domain-client",
    "matching_engine_library": "matching-engine-library",
    "execution_algo_library": "execution-algo-library",
}

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
        except Exception:
            pass
    return imported


def get_declared_deps(pyproject: dict) -> set[str]:
    """Return set of package names in [project.dependencies]."""
    deps = pyproject.get("project", {}).get("dependencies", [])
    names: set[str] = set()
    for d in deps:
        name = d.split(">=")[0].split("<=")[0].split("==")[0].split("<")[0].split(">")[0].strip()
        names.add(name)
    return names


def get_uv_sources(pyproject: dict) -> set[str]:
    """Return set of package names in [tool.uv.sources]."""
    return set(pyproject.get("tool", {}).get("uv", {}).get("sources", {}).keys())


def fix_pyproject(pyproject_path: Path, missing_deps: list[str], missing_sources: list[str]) -> None:
    """Add missing deps and uv sources to pyproject.toml."""
    text = pyproject_path.read_text()

    for pkg in missing_deps:
        dep_line = f'    "{pkg}>=0.1.0,<1.0.0",'
        marker = '"unified-trading-library'
        if marker in text:
            idx = text.index(marker)
            end = text.index("\n", idx)
            text = text[:end + 1] + dep_line + "\n" + text[end + 1:]

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
    repos = manifest.get("repositories", {})

    total_issues = 0

    for repo_name in sorted(repos):
        repo_dir = WORKSPACE / repo_name
        if not repo_dir.is_dir() or not (repo_dir / "pyproject.toml").exists():
            continue
        if not repo_name.endswith("-service"):
            continue

        src_dir = repo_dir / repo_name.replace("-", "_")
        if not src_dir.exists():
            continue

        imported = scan_imports(src_dir)
        if not imported:
            continue

        with open(repo_dir / "pyproject.toml", "rb") as f:
            pyproject = tomllib.load(f)

        declared = get_declared_deps(pyproject)
        sources = get_uv_sources(pyproject)

        missing_deps = []
        missing_sources = []

        for imp in sorted(imported):
            pkg = INTERNAL_PACKAGES[imp]
            if pkg not in declared:
                missing_deps.append(pkg)
            if pkg not in sources:
                missing_sources.append(pkg)

        if missing_deps or missing_sources:
            total_issues += len(missing_deps) + len(missing_sources)
            if FIX:
                fix_pyproject(repo_dir / "pyproject.toml", missing_deps, missing_sources)
                print(f"  [FIXED] {repo_name}: +{len(missing_deps)} deps, +{len(missing_sources)} sources")
            else:
                print(f"  {repo_name}:")
                for d in missing_deps:
                    print(f"    [DEP]    {d}")
                for s in missing_sources:
                    print(f"    [SOURCE] {s}")

    if total_issues == 0:
        print("OK: All services have deps + uv sources for every direct internal import.")
        return 0

    if FIX:
        print(f"\n  Fixed {total_issues} issue(s) across services.")
        return 0

    print(f"\n  {total_issues} issue(s) found. Run with --fix to auto-add.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
