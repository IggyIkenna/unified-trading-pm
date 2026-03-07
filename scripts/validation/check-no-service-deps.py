#!/usr/bin/env python3.13
"""
Check that a service repo does not depend on another service repo as a path dependency.

Services must import only libraries (T0-T3); interaction is via messaging/APIs/storage
per runtime topology DAG (runtime-topology.yaml). Importing another service as a package
is a violation.

Usage:
    From service repo root: python unified-trading-pm/scripts/check-no-service-deps.py
    Or with REPO_ROOT set:  REPO_ROOT=/path/to/workspace python check-no-service-deps.py
    (run from the service repo directory containing pyproject.toml)

Exit: 0 if OK (not a service, or no service deps); 1 if service has path dep on another service.
"""

import json
import os
import sys
from pathlib import Path
from typing import cast


def find_manifest() -> Path | None:
    """Locate workspace-manifest.json (REPO_ROOT/unified-trading-pm or walk up from cwd)."""
    repo_root = os.environ.get("REPO_ROOT")
    if repo_root:
        p = Path(repo_root) / "unified-trading-pm" / "workspace-manifest.json"
        if p.exists():
            return p
    cwd = Path.cwd()
    for d in [cwd, *cwd.parents]:
        manifest = d / "unified-trading-pm" / "workspace-manifest.json"
        if manifest.exists():
            return manifest
    return None


def get_service_repos(manifest_path: Path) -> set[str]:
    """Return set of repo names that have type == 'service'."""
    data = cast(dict[str, object], json.loads(manifest_path.read_text()))
    repos = cast(dict[str, dict[str, str]], data.get("repositories") or {})
    return {name for name, meta in repos.items() if meta.get("type") == "service"}


def get_current_repo_name(project_root: Path) -> str | None:
    """Infer current repo name from pyproject.toml [project] name (e.g. execution-service)."""
    pyproject = project_root / "pyproject.toml"
    if not pyproject.exists():
        return None
    raw = pyproject.read_text()
    # Simple line-based; avoid toml dependency
    in_project = False
    for line in raw.splitlines():
        if line.strip() == "[project]":
            in_project = True
            continue
        if in_project and line.strip().startswith("name"):
            # name = "execution-service" or name = 'execution-service'
            parts = line.split("=", 1)
            if len(parts) == 2:
                name = parts[1].strip().strip("\"'")
                return name
            break
        if in_project and line.startswith("["):
            break
    return None


def get_path_deps(pyproject_path: Path) -> list[str]:
    """Return list of path dependency names from [tool.uv.sources] (key = dep name when value has path = ../)."""
    text = pyproject_path.read_text()
    deps: list[str] = []
    in_uv_sources = False
    for line in text.splitlines():
        if line.strip() == "[tool.uv.sources]":
            in_uv_sources = True
            continue
        if in_uv_sources:
            if line.strip().startswith("["):
                break
            # "market-tick-data-service" = { path = "../market-tick-data-service" } or name = "../repo"
            if "=" in line and ("path" in line or line.strip().startswith("#") is False):
                key_part = line.split("=")[0].strip().strip("\"'")
                if key_part and not key_part.startswith("#"):
                    # Value has path = "../..." -> this key is a path dep
                    rest = line[line.find("=") + 1 :].strip()
                    if "path" in rest or "../" in rest or "..\\" in rest:
                        if key_part not in deps:
                            deps.append(key_part)
    return deps


def main() -> int:
    project_root = Path.cwd()
    pyproject = project_root / "pyproject.toml"
    if not pyproject.exists():
        # Not a Python project; skip
        return 0

    manifest_path = find_manifest()
    if not manifest_path:
        print("check-no-service-deps: workspace-manifest.json not found; skipping.", file=sys.stderr)
        return 0

    service_repos = get_service_repos(manifest_path)
    current = get_current_repo_name(project_root)
    if not current or current not in service_repos:
        # Current repo is not a service; no check
        return 0

    path_deps = get_path_deps(pyproject)
    other_services = [d for d in path_deps if d in service_repos and d != current]
    if other_services:
        print(
            f"Service '{current}' must not depend on other"
            f" services as path deps. Found: {other_services}."
            " Use messaging per runtime topology"
            " (runtime-topology.yaml).",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
