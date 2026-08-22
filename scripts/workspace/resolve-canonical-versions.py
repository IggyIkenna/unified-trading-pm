#!/usr/bin/env python3.13
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Compute canonical version ranges for all external workspace dependencies.

Reads all pyproject.toml files from repos in topological order (workspace-manifest.json),
collects external dependency specs, picks the tightest constraint per package, and writes
unified-trading-pm/workspace-constraints.toml plus a short report.

WARNING: This script DERIVES the canonical from repo state. Do NOT use it to "fix"
dependency alignment — that would let a few repos dictate the workspace standard.
When alignment fails, use fix_external_dependency_alignment.py to update repos to match
the existing canonical. Use this script only for intentional sync (e.g. migration).

Usage:
    python resolve-canonical-versions.py              # write workspace-constraints.toml + report to stdout
    python resolve-canonical-versions.py -o report.txt  # write report to file
"""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path
from typing import cast

type DepSpec = str
type TomlDict = dict[str, object]

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
MANIFEST_PATH = WORKSPACE_ROOT / "unified-trading-pm" / "workspace-manifest.json"
CONSTRAINTS_FILE = WORKSPACE_ROOT / "unified-trading-pm" / "workspace-constraints.toml"

# Single canonical uv version pin (lockfile determinism — uv.lock's `revision = 3` serialization is
# tied to this version; an unpinned uv reformats the lock on any `uv lock` run, even with identical
# deps). This is the ONE place the literal is defined workspace-wide. Shell/YAML consumers that can't
# import this module extract it via: grep -oP '^UV_VERSION = "\K[^"]+' resolve-canonical-versions.py
# SSOT: plans/active/uv_lockfile_determinism_2026_06_02.md.
UV_VERSION = "0.10.8"


def load_manifest() -> TomlDict:
    with open(MANIFEST_PATH) as f:
        return cast(TomlDict, json.load(f))


def _level_sort_key(lvl: TomlDict) -> int:
    raw = lvl.get("level")
    return int(cast(int, raw)) if isinstance(raw, int) else 999


def get_topological_order(manifest: TomlDict) -> list[str]:
    topo_raw = manifest.get("topologicalOrder")
    if not isinstance(topo_raw, dict):
        return []
    topo = cast(TomlDict, topo_raw)
    levels_raw = topo.get("levels")
    if not isinstance(levels_raw, list):
        return []
    levels = [cast(TomlDict, lvl) for lvl in levels_raw if isinstance(lvl, dict)]
    ordered: list[str] = []
    for level in sorted(levels, key=_level_sort_key):
        repos_raw = level.get("repos")
        if not isinstance(repos_raw, list):
            continue
        for repo in repos_raw:
            if isinstance(repo, str):
                ordered.append(repo)
    return ordered


def get_repo_folder_path(manifest: TomlDict, repo_name: str) -> Path:
    repos_raw = manifest.get("repositories")
    if isinstance(repos_raw, dict):
        entry = repos_raw.get(repo_name)
        if isinstance(entry, dict):
            folder = entry.get("folder_name")
            if isinstance(folder, str):
                return WORKSPACE_ROOT / folder
    return WORKSPACE_ROOT / repo_name


def parse_pyproject(repo_path: Path) -> tuple[list[DepSpec], dict[str, str]]:
    pyproject_path = repo_path / "pyproject.toml"
    if not pyproject_path.is_file():
        return [], {}
    with open(pyproject_path, "rb") as f:
        data = cast(TomlDict, tomllib.load(f))
    project = cast(TomlDict, data.get("project")) if isinstance(data.get("project"), dict) else {}
    deps: list[DepSpec] = []
    raw_deps = project.get("dependencies")
    if isinstance(raw_deps, list):
        deps = [str(d) for d in raw_deps]
    optional = (
        cast(TomlDict, project.get("optional-dependencies"))
        if isinstance(project.get("optional-dependencies"), dict)
        else {}
    )
    dev_deps_raw = optional.get("dev")
    if isinstance(dev_deps_raw, list):
        deps.extend(str(d) for d in dev_deps_raw)
    uv_sources: dict[str, str] = {}
    tool = cast(TomlDict, data.get("tool")) if isinstance(data.get("tool"), dict) else {}
    uv = cast(TomlDict, tool.get("uv")) if isinstance(tool.get("uv"), dict) else {}
    sources_raw = uv.get("sources")
    if isinstance(sources_raw, dict):
        for dep_name, source_info in sources_raw.items():
            if isinstance(source_info, dict) and isinstance(source_info.get("path"), str):
                uv_sources[dep_name] = str(source_info["path"])
    return deps, uv_sources


def normalize_pkg_name(name: str) -> str:
    return name.lower().replace("-", "_").replace(".", "_")


def extract_pkg_name(dep_spec: DepSpec) -> str:
    for sep in [">=", "<=", "!=", "==", ">", "<", "~=", "[", ";"]:
        idx = dep_spec.find(sep)
        if idx > 0:
            return dep_spec[:idx].strip()
    return dep_spec.strip()


def collect_external_deps(repos: list[str], manifest: TomlDict) -> dict[str, list[DepSpec]]:
    external_deps: dict[str, list[DepSpec]] = {}
    internal_names: set[str] = set()
    for repo_name in repos:
        repo_path = get_repo_folder_path(manifest, repo_name)
        if not repo_path.is_dir():
            continue
        deps, uv_sources = parse_pyproject(repo_path)
        for dep_name in uv_sources:
            internal_names.add(normalize_pkg_name(dep_name))
        for dep_spec in deps:
            norm = normalize_pkg_name(extract_pkg_name(dep_spec))
            if norm in internal_names:
                continue
            if norm not in external_deps:
                external_deps[norm] = []
            external_deps[norm].append(dep_spec)
    return external_deps


def pick_tightest_constraint(specs: list[DepSpec]) -> DepSpec:
    if len(specs) == 1:
        return specs[0]
    unique = list(set(specs))
    if len(unique) == 1:
        return unique[0]
    return sorted(unique, key=lambda s: (len(s), s), reverse=True)[0]


def main() -> None:
    parser = argparse.ArgumentParser(description="Resolve canonical external dependency versions")
    parser.add_argument("-o", "--report", metavar="FILE", help="Write human-readable report to file")

    class Args(argparse.Namespace):
        report: str | None = None

    args = parser.parse_args(namespace=Args())
    report_path: Path | None = Path(args.report) if args.report is not None else None

    if not MANIFEST_PATH.is_file():
        print(f"ERROR: Manifest not found: {MANIFEST_PATH}", file=sys.stderr)
        sys.exit(1)

    manifest = load_manifest()
    topo_order = get_topological_order(manifest)
    external_deps = collect_external_deps(topo_order, manifest)

    canonical: dict[str, str] = {}
    report_lines: list[str] = [
        "Package | Current specs (across repos) | Canonical",
        "-------|-----------------------------|----------",
    ]
    for norm_name in sorted(external_deps):
        specs = external_deps[norm_name]
        chosen = pick_tightest_constraint(specs)
        canonical[norm_name] = chosen
        unique_specs = sorted(set(specs))
        specs_str = "; ".join(unique_specs) if len(unique_specs) <= 3 else f"{len(unique_specs)} variants"
        report_lines.append(f"{norm_name} | {specs_str} | {chosen}")

    toml_lines = [
        "# Workspace canonical external dependency ranges",
        "# Generated by resolve-canonical-versions.py — do not edit by hand.",
        "# All repos should use these ranges; propagate via propagate-canonical-versions.py",
        "",
        "[dependencies]",
    ]
    for name in sorted(canonical):
        key = f'"{name}"' if "[" in name or "]" in name else name
        toml_lines.append(f'{key} = "{canonical[name]}"')
    toml_lines.append("")
    CONSTRAINTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONSTRAINTS_FILE.write_text("\n".join(toml_lines))
    print(f"Wrote {CONSTRAINTS_FILE} ({len(canonical)} packages)")

    report_text = "\n".join(report_lines)
    if report_path is not None:
        report_path.write_text(report_text)
        print(f"Report written to {report_path}")
    else:
        print("\n--- Report ---\n")
        print(report_text)


if __name__ == "__main__":
    main()
