#!/usr/bin/env python3.13
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""
Check that a service repo does not depend on another service repo as a path dependency,
and (WARN-only, informational) flag a raw import of another service's package.

Services must import only libraries (T0-T3); interaction is via messaging/APIs/storage
per runtime topology DAG (runtime-topology.yaml). A `[tool.uv.sources]` path dep on another
service is a hard failure. A raw `import <other_service>` / `from <other_service> import ...`
statement (source or tests) is additive-hardening belt-and-suspenders (utl_reuse_phase9,
2026-07-13): printed as [WARN] but does not fail the gate, since the fleet already carries
~39 pre-existing, individually-reviewed/tracked raw cross-service imports (see
`find_raw_service_imports`'s caller in `main()` for why hard-failing those isn't safe yet).

Usage:
    From service repo root: python unified-trading-pm/scripts/check-no-service-deps.py
    Or with REPO_ROOT set:  REPO_ROOT=/path/to/workspace python check-no-service-deps.py
    (run from the service repo directory containing pyproject.toml)

Exit: 0 if OK (not a service, or no path-dep service violations — raw-import hits warn only);
1 if service has a path dep on another service.
"""

import ast
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


_EXCLUDED_DIR_NAMES: frozenset[str] = frozenset(
    {".venv", "venv", "node_modules", "build", "dist", "__pycache__", ".git"}
)

# (current, other_repo) pairs whose raw cross-service import is HARD-FAILED rather than
# WARN-only, unlike the general fleet scan below. strategy-service -> market-tick-data-service
# is the "normalisation rule" (2026-08-16 operator ruling,
# /plans/active/venue_readiness_and_registry_hardening_2026_08_16.md): strategy-service must
# read market data only through features-service / market-data-processing-service, so it always
# receives a normalised candle-like shape — never MTDS directly. Verified 2026-08-16: zero
# pre-existing hits for this pair, so hard-failing it carries no baseline-remediation cost
# (unlike the general raw-import scan, which stays WARN-only pending the ~39-violation
# fleet-wide remediation pass tracked separately).
_HARD_FAILED_PAIRS: frozenset[tuple[str, str]] = frozenset({("strategy-service", "market-tick-data-service")})


def _service_package_name(repo_name: str) -> str:
    """Map a dash-cased repo name (manifest key) to its importable python package name."""
    return repo_name.replace("-", "_")


def _iter_py_files(root: Path) -> list[Path]:
    """Yield every .py file under root, skipping venvs/build/vcs directories."""
    return [p for p in root.rglob("*.py") if not any(part in _EXCLUDED_DIR_NAMES for part in p.relative_to(root).parts)]


def find_raw_service_imports(project_root: Path, other_service_packages: dict[str, str]) -> list[tuple[str, int, str]]:
    """Scan every .py file under project_root for a raw import of another service's package.

    ``other_service_packages`` maps importable-package-name -> repo-name for every OTHER
    service repo (the current repo is excluded by the caller). Catches both plain
    ``import <pkg>`` and ``from <pkg>[.sub] import ...`` — belt-and-suspenders alongside the
    ``[tool.uv.sources]`` path-dep check above, since today every live violation also carries
    a path dep. Static AST-based (no dynamic ``importlib.import_module(...)`` detection).
    """
    violations: list[tuple[str, int, str]] = []
    for py_file in _iter_py_files(project_root):
        try:
            tree = ast.parse(py_file.read_text(), filename=str(py_file))
        except (SyntaxError, UnicodeDecodeError, OSError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0]
                    if top in other_service_packages:
                        violations.append(
                            (str(py_file.relative_to(project_root)), node.lineno, other_service_packages[top])
                        )
            elif isinstance(node, ast.ImportFrom) and node.module:
                top = node.module.split(".")[0]
                if top in other_service_packages:
                    violations.append(
                        (str(py_file.relative_to(project_root)), node.lineno, other_service_packages[top])
                    )
    return violations


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

    violations_found = False

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
        violations_found = True

    # Raw-import scan is WARN-only for now, not blocking: a fleet probe (utl_reuse_phase9,
    # 2026-07-13) found ~39 pre-existing raw cross-service imports in tests/source across
    # deployment-service/execution-service/strategy-service/features-service, each already
    # reviewed/tracked (service_contract_map.py forbidden_exceptions, deprecation_ledger.yaml,
    # or an explicit sanctioned-deep-import noqa marker + rationale comment) — none carry a
    # path dep, so the (hard-fail) check above never saw them. Hard-failing here today would break those
    # repos' quality-gates.sh with no way to distinguish "new accidental coupling" from
    # "already-sanctioned debt." Mirrors how the path-dep gate itself was rolled out: land the
    # detector, remediate/baseline what it finds, THEN flip to hard-fail (see item 1 above) —
    # that remediation pass is out of this ticket's scope (touches repos this plan doesn't
    # own) and is tracked as a follow-up, not silently skipped.
    other_service_packages = {_service_package_name(name): name for name in service_repos if name != current}
    for file, lineno, other_repo in sorted(find_raw_service_imports(project_root, other_service_packages)):
        if (current, other_repo) in _HARD_FAILED_PAIRS:
            print(
                f"[FAIL] Service '{current}' must not import service '{other_repo}' directly"
                f" (normalisation rule): {file}:{lineno}. Read market data through"
                " features-service or market-data-processing-service instead.",
                file=sys.stderr,
            )
            violations_found = True
        else:
            print(
                f"[WARN] Service '{current}' raw-imports service '{other_repo}':"
                f" {file}:{lineno}. If new, use messaging per runtime topology (runtime-topology.yaml)"
                " instead — if intentional/tracked debt, this is informational only for now.",
                file=sys.stderr,
            )

    return 1 if violations_found else 0


if __name__ == "__main__":
    sys.exit(main())
