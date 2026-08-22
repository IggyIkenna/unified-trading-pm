#!/usr/bin/env python3.13
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Extract dependencies from all pyproject.toml files and generate a derived manifest.

Reads workspace-manifest.json for repo list and topological order, then parses each
repo's pyproject.toml to extract:
  - Internal deps (path deps from [tool.uv.sources] or inline path = "...")
  - External deps (PyPI packages with version specs)

Outputs: unified-trading-pm/derived-dependency-manifest.json

Usage:
    python generate-derived-manifest.py
    python generate-derived-manifest.py -o /path/to/output.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tomllib
from pathlib import Path
from typing import Any, cast

SCRIPT_DIR = Path(__file__).resolve().parent
PM_ROOT = SCRIPT_DIR.parent.parent
WORKSPACE_ROOT = Path(os.environ.get("WORKSPACE_ROOT", str(PM_ROOT.parent)))
MANIFEST_PATH = PM_ROOT / "workspace-manifest.json"
CONSTRAINTS_PATH = PM_ROOT / "workspace-constraints.toml"
DEFAULT_OUTPUT = PM_ROOT / "derived-dependency-manifest.json"

INTERNAL_PREFIXES = ("unified-", "unified_", "execution-algo", "matching-engine")


def load_manifest() -> dict[str, Any]:
    with open(MANIFEST_PATH) as f:
        return cast(dict[str, Any], json.load(f))


_WORKSPACE_REPO_NAMES_CACHE: set[str] | None = None


def _workspace_repo_names() -> set[str]:
    """Workspace repo names from workspace-manifest.json (cached).

    Used by ``is_internal_package`` to recognize bare service names like
    ``execution-service`` / ``strategy-service`` that don't match the legacy
    ``INTERNAL_PREFIXES`` heuristic.
    """
    global _WORKSPACE_REPO_NAMES_CACHE
    if _WORKSPACE_REPO_NAMES_CACHE is None:
        manifest = load_manifest()
        names: set[str] = set()
        topo_raw = manifest.get("topologicalOrder")
        if isinstance(topo_raw, dict):
            levels_raw = topo_raw.get("levels")
            if isinstance(levels_raw, list):
                for level in cast(list[dict[str, Any]], levels_raw):
                    for r in level.get("repos", []) or []:  # noqa: qg-empty-fallback
                        if isinstance(r, str):
                            names.add(normalize_pkg_name(r))
        _WORKSPACE_REPO_NAMES_CACHE = names
    return _WORKSPACE_REPO_NAMES_CACHE


def _level_sort_key(lvl: dict[str, Any]) -> int:
    raw = lvl.get("level")
    return int(raw) if isinstance(raw, (int, float)) else 999


def get_topological_order(manifest: dict[str, Any]) -> list[str]:
    topo_raw = manifest.get("topologicalOrder")
    if not isinstance(topo_raw, dict):
        return []
    levels_raw = topo_raw.get("levels")
    if not isinstance(levels_raw, list):
        return []
    ordered: list[str] = []
    for level in sorted(levels_raw, key=_level_sort_key):
        repos = level.get("repos")
        if isinstance(repos, list):
            for r in repos:
                if isinstance(r, str):
                    ordered.append(r)
    return ordered


def get_repo_folder_path(manifest: dict[str, Any], repo_name: str) -> Path:
    repos = manifest.get("repositories")
    if isinstance(repos, dict):
        entry = repos.get(repo_name)
        if isinstance(entry, dict) and isinstance(entry.get("folder_name"), str):
            return WORKSPACE_ROOT / entry["folder_name"]
    return WORKSPACE_ROOT / repo_name


def normalize_pkg_name(name: str) -> str:
    base = re.sub(r"\[.*?\]", "", name)
    return base.lower().replace("_", "-").strip()


def extract_pkg_name(dep_spec: str) -> str:
    if " @ " in dep_spec:
        return dep_spec.split(" @ ", 1)[0].strip()
    for sep in [">=", "<=", "!=", "==", ">", "<", "~=", "[", ";"]:
        idx = dep_spec.find(sep)
        if idx > 0:
            return dep_spec[:idx].strip()
    return dep_spec.strip()


def is_internal_package(name: str) -> bool:
    norm = normalize_pkg_name(name)
    if any(norm.startswith(p.replace("_", "-")) for p in INTERNAL_PREFIXES):
        return True
    # Also recognize workspace repos by exact name match (covers service repos like
    # execution-service / strategy-service / risk-and-exposure-service that don't
    # match the legacy unified-/execution-algo/matching-engine prefixes).
    return norm in _workspace_repo_names()


def parse_pyproject(repo_path: Path) -> tuple[dict[str, str], dict[str, list[str]]]:
    pyproject = repo_path / "pyproject.toml"
    if not pyproject.is_file():
        return {}, {}

    with open(pyproject, "rb") as f:
        data = cast(dict[str, Any], tomllib.load(f))

    deps_raw: list[str] = []
    project = data.get("project")
    if isinstance(project, dict):
        raw = project.get("dependencies")
        if isinstance(raw, list):
            deps_raw.extend(str(d) for d in raw)
        # No optional-dependencies — all repos use flat [project.dependencies] only

    uv_sources: dict[str, str] = {}
    tool = data.get("tool")
    if isinstance(tool, dict):
        uv = tool.get("uv")
        if isinstance(uv, dict):
            sources = uv.get("sources")
            if isinstance(sources, dict):
                for k, v in sources.items():
                    if isinstance(v, dict) and isinstance(v.get("path"), str):
                        uv_sources[normalize_pkg_name(k)] = v["path"]

    internal_deps: dict[str, str] = dict.fromkeys(uv_sources, "path")
    external_deps: dict[str, list[str]] = {}

    for dep in deps_raw:
        if "path" in dep and ("../" in dep or "..\\\\" in dep):
            m = re.match(r"([a-zA-Z0-9_-]+)\s*=", dep)
            if m:
                internal_deps[normalize_pkg_name(m.group(1))] = "path"
            continue
        name = extract_pkg_name(dep)
        norm = normalize_pkg_name(name)
        if norm in uv_sources or is_internal_package(name):
            internal_deps[norm] = dep
        else:
            if norm not in external_deps:
                external_deps[norm] = []
            external_deps[norm].append(dep)

    return internal_deps, external_deps


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()
    output_path = Path(cast(str, args.output))

    if not MANIFEST_PATH.is_file():
        print(f"ERROR: Manifest not found: {MANIFEST_PATH}", file=sys.stderr)
        sys.exit(1)

    manifest = load_manifest()
    topo_order = get_topological_order(manifest)
    repos_data: dict[str, dict[str, Any]] = {}

    for repo_name in topo_order:
        repo_path = get_repo_folder_path(manifest, repo_name)
        if not repo_path.is_dir():
            repos_data[repo_name] = {"skipped": True, "reason": "not a directory"}
            continue
        internal, external = parse_pyproject(repo_path)
        repos_data[repo_name] = {
            "internal_deps": dict(sorted(internal.items())),
            "external_deps": {k: list(set(v)) for k, v in sorted(external.items())},
            "internal_count": len(internal),
            "external_count": len(external),
        }

    constraints: dict[str, str] = {}
    if CONSTRAINTS_PATH.is_file():
        with open(CONSTRAINTS_PATH, "rb") as f:
            cdata = cast(dict[str, Any], tomllib.load(f))
        deps = cdata.get("dependencies")
        if isinstance(deps, dict):
            constraints = {k: str(v) for k, v in deps.items()}

    derived = {
        "description": "Derived from pyproject.toml. Compare to workspace-manifest.json.",
        "source": "scripts/manifest/generate-derived-manifest.py",
        "repositories": repos_data,
        "canonical_external_constraints": constraints,
    }
    output_path.write_text(json.dumps(derived, indent=2) + "\n")
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
