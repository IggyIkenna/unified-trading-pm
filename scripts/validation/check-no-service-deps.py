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
        # REPO_ROOT is authoritative when set: return its manifest or None — do NOT fall
        # through to the cwd-parent walk, which can spuriously match a stray
        # /tmp/unified-trading-pm/ left by another process (flake fix — the test sets
        # REPO_ROOT to an empty tmp dir + chdirs under /private/tmp and expects None).
        p = Path(repo_root) / "unified-trading-pm" / "workspace-manifest.json"
        return p if p.exists() else None
    cwd = Path.cwd()
    for d in [cwd, *cwd.parents]:
        manifest = d / "unified-trading-pm" / "workspace-manifest.json"
        if manifest.exists():
            return manifest
    return None


# A deployable SERVICE is any repo whose manifest type marks it as a runtime
# service. The gate must treat all of these as "services that may not depend on
# another service": plain ``service`` PLUS the API/batch flavours (``api-service``
# / ``batch-service`` / ``api``). Missing the flavours let real violations
# (e.g. deployment-api -> strategy-service) slip past the gate silently.
_SERVICE_REPO_TYPES: frozenset[str] = frozenset({"service", "api-service", "batch-service", "api"})


def get_service_repos(manifest_path: Path) -> set[str]:
    """Return set of repo names whose manifest type is a deployable-service flavour."""
    data = cast(dict[str, object], json.loads(manifest_path.read_text()))
    repos = cast(dict[str, dict[str, str]], data.get("repositories") or {})
    return {name for name, meta in repos.items() if meta.get("type") in _SERVICE_REPO_TYPES}


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
    """Return path-dependency names declared in ``[tool.uv.sources]``.

    Handles BOTH the FLAT inline form and the DOTTED table-header form, since
    repos use either:

        # FLAT (deployment-api style)
        [tool.uv.sources]
        strategy-service = { path = "../strategy-service", editable = true }

        # DOTTED (market-data-processing-service style)
        [tool.uv.sources.market-tick-data-service]
        path = "../market-tick-data-service"
        editable = true

    Parsing only the flat header (the original bug) let every dotted-form path
    dep slip past the gate silently.
    """
    text = pyproject_path.read_text()
    deps: list[str] = []
    in_uv_sources_flat = False
    dotted_dep: str | None = None  # current [tool.uv.sources.<dep>] table, if any
    for raw_line in text.splitlines():
        line = raw_line.strip()
        # DOTTED table header: [tool.uv.sources.<dep-name>]
        if line.startswith("[tool.uv.sources.") and line.endswith("]"):
            in_uv_sources_flat = False
            dotted_dep = line[len("[tool.uv.sources.") : -1].strip().strip("\"'")
            continue
        # FLAT table header: [tool.uv.sources]
        if line == "[tool.uv.sources]":
            in_uv_sources_flat = True
            dotted_dep = None
            continue
        # Any other table header closes the current uv.sources context.
        if line.startswith("[") and line.endswith("]"):
            in_uv_sources_flat = False
            dotted_dep = None
            continue
        # Inside a DOTTED table: a ``path = "../..."`` line confirms a path dep.
        if dotted_dep is not None:
            if ("path" in line or "../" in line or "..\\" in line) and dotted_dep not in deps:
                deps.append(dotted_dep)
            continue
        # Inside the FLAT table: ``<dep> = { path = "../..." }``.
        if in_uv_sources_flat and "=" in line and not line.startswith("#"):
            key_part = line.split("=", 1)[0].strip().strip("\"'")
            rest = line.split("=", 1)[1].strip()
            if key_part and ("path" in rest or "../" in rest or "..\\" in rest) and key_part not in deps:
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
