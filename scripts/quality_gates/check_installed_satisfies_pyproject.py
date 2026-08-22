#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Installed-distribution floor guardrail — every EXTERNAL dep's INSTALLED version (in the venv
this script itself runs under) must satisfy its pyproject [project.dependencies] range.

`check_lock_satisfies_pyproject.py` (the 1.5b frozen-lock gate) verifies the *lock file* pin is
in-range, but a correctly-resolved lock does not guarantee the *installed venv* matches it: a venv
built before a floor bump and never re-synced (`uv sync`) keeps its stale distribution even though
`uv.lock` and `pyproject.toml` both already agree on the new floor. This is the exact root cause of
`stale_service_venvs_below_declared_fastapi_floor_2026_08_11.md` — 20 of 21 fastapi-carrying venvs
in one slot were pinned+locked to `>=0.137.0` but had 0.136.3 physically installed, an
environment-provisioning defect invisible to the lock-only gate.

Run this WITH the target venv's own interpreter (`.venv/bin/python`) so `importlib.metadata` reads
that venv's actually-installed distributions, not the caller's.

Usage:  .venv/bin/python check_installed_satisfies_pyproject.py [--repo .]
Exit 0 = every external dep's installed version satisfies its declared range (or isn't installed).
Exit 1 = an installed distribution VIOLATES its declared floor/ceiling — run: uv sync --frozen.
"""

from __future__ import annotations

import argparse
import sys
import tomllib
from importlib import metadata
from pathlib import Path

from packaging.requirements import InvalidRequirement, Requirement
from packaging.utils import canonicalize_name
from packaging.version import InvalidVersion, Version

INTERNAL_PREFIX = "unified-"


def load_declared_deps(pyproject_path: Path) -> list[Requirement]:
    data = tomllib.loads(pyproject_path.read_text())
    project = data.get("project")
    deps = project.get("dependencies") if isinstance(project, dict) else None
    reqs: list[Requirement] = []
    if not isinstance(deps, list):
        return reqs
    for dep in deps:
        if not isinstance(dep, str):
            continue
        try:
            reqs.append(Requirement(dep))
        except InvalidRequirement:
            continue  # an unparseable dep line is not this gate's concern
    return reqs


def load_local_source_names(lock_path: Path) -> set[str]:
    """Canonical names of every lock entry with an editable/path/directory/virtual source.

    Mirrors check_lock_satisfies_pyproject.py's load_lock_pkgs is_local detection: covers every
    internal sibling — both unified-* libraries AND service-named editables (e.g. e2e-testing /
    system-integration-tests depend on execution-service, strategy-service as editable path
    sources for cross-service tests). Those installs resolve from the on-disk sibling (often a
    shallow/content-first clone with no tags, so hatch-vcs/setuptools-scm falls back to a
    0.1.dev1+g<hash> version) — not from a registry pin, so this gate's floor check doesn't apply.
    """
    if not lock_path.is_file():
        return set()
    data = tomllib.loads(lock_path.read_text())
    packages = data.get("package")
    names: set[str] = set()
    if not isinstance(packages, list):
        return names
    for pkg in packages:
        if not isinstance(pkg, dict):
            continue
        name = pkg.get("name")
        src = pkg.get("source")
        is_local = isinstance(src, dict) and any(k in src for k in ("editable", "path", "directory", "virtual"))
        if is_local and isinstance(name, str):
            names.add(canonicalize_name(name))
    return names


def check_repo(root: Path) -> tuple[list[str], list[str]]:
    """Return (violations, warnings) for one repo, read against THIS interpreter's installed set."""
    pyproject = root / "pyproject.toml"
    if not pyproject.is_file():
        return [], []
    local_sources = load_local_source_names(root / "uv.lock")
    violations: list[str] = []
    warnings: list[str] = []
    for req in load_declared_deps(pyproject):
        cname = canonicalize_name(req.name)
        if cname.startswith(INTERNAL_PREFIX):
            continue  # internal unified-* dep — editable install, version resolved on-disk
        if cname in local_sources:
            continue  # service-named editable/path sibling — resolved on-disk, floor N/A
        if not req.specifier:
            continue  # no constraint to violate
        try:
            installed = metadata.version(cname)
        except metadata.PackageNotFoundError:
            warnings.append(f"{req.name}: declared {req.specifier} but not installed in this venv (marker dep?)")
            continue
        try:
            in_range = req.specifier.contains(Version(installed), prereleases=True)
        except InvalidVersion:
            continue  # a non-PEP440 installed version — out of scope
        if not in_range:
            violations.append(f"{req.name}: installed {installed} which VIOLATES declared {req.specifier}")
    return violations, warnings


def main() -> int:
    ap = argparse.ArgumentParser(description="Installed-distribution floor guardrail (venv package vs pyproject range)")
    ap.add_argument("--repo", default=".", help="repo root containing pyproject.toml")
    args = ap.parse_args()
    root = Path(args.repo).resolve()

    violations, warnings = check_repo(root)
    for warn in warnings:
        print(f"⚠️  installed floor: {warn}")
    if violations:
        print(f"❌ installed-distribution floor guardrail: {len(violations)} package(s) violate the pyproject range:")
        for viol in violations:
            print(f"   - {viol}")
        print("   The venv this ran under is stale against its own pyproject/lock — re-sync it: `uv sync --frozen`.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
