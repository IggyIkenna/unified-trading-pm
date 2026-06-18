#!/usr/bin/env python3
# Epic: infrastructure_master
# Lifecycle: permanent
"""Frozen-lock floor guardrail — every EXTERNAL dep's uv.lock pin must satisfy its
pyproject [project.dependencies] range (the failure-mode-B catcher for 1.5b).

Since CI + local QG install via `uv sync --frozen` (Phase 1.5b of
dependency_promotion_range_pins_and_major_bump_sit_2026_06_09.md), the committed uv.lock is
the EXACT installed set. If a pyproject dep FLOOR is bumped but the lock is not regenerated,
the stale lock pins a below-floor version and `--frozen` ships it verbatim (the fund-admin
`python-multipart 0.0.29` CVE case the plan describes). This gate BLOCKS that: for every
external dep declared in `[project.dependencies]`, the lock's pinned version must satisfy the
declared specifier.

Deliberately NOT `uv lock --check`: that hard-fails on ANY pyproject<->lock delta INCLUDING
the cosmetic semver-agent CI-side root `version =` bump — a treadmill that would fight the
bot on every promotion. This gate IGNORES the root version and internal editable `unified-*`
deps (resolved from the on-disk sibling, so their lock version is cosmetic) and checks ONLY
that each external pin is in-range.

Conservative by design (a fleet-wide gate must not false-fail): the HARD failure is only a
pin that is present in the lock AND violates the declared range. A dep declared but absent
from the lock is a WARN (it may be an env-marker / platform-gated dep) — surfaced, not blocked.

Usage:  check_lock_satisfies_pyproject.py [--repo .]
Exit 0 = every external pin satisfies its declared range (or no lock / no deps).
Exit 1 = a pin in the lock VIOLATES its declared floor/ceiling — regenerate: `uv lock`.
"""

from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path

from packaging.requirements import InvalidRequirement, Requirement
from packaging.utils import canonicalize_name
from packaging.version import InvalidVersion, Version

INTERNAL_PREFIX = "unified-"


def load_lock_pkgs(lock_path: Path) -> dict[str, tuple[str, bool]]:
    """canonical pkg name -> (pinned version, is_local_source).

    is_local_source = the lock entry is an editable / path / directory / virtual source, so its
    version is COSMETIC (resolved from the on-disk sibling, not installed from a registry). This
    covers every internal sibling — both `unified-*` libraries AND service-named editables (e.g.
    e2e-testing / system-integration-tests depend on execution-service, strategy-service as editable
    path sources for cross-service tests). Such deps are skipped: --frozen installs the on-disk copy,
    so the lock's pinned version is not what ships.
    """
    data = tomllib.loads(lock_path.read_text())
    pkgs: dict[str, tuple[str, bool]] = {}
    packages = data.get("package")
    if not isinstance(packages, list):
        return pkgs
    for pkg in packages:
        if not isinstance(pkg, dict):
            continue
        name = pkg.get("name")
        ver = pkg.get("version")
        src = pkg.get("source")
        is_local = isinstance(src, dict) and any(k in src for k in ("editable", "path", "directory", "virtual"))
        if isinstance(name, str) and isinstance(ver, str):
            pkgs[canonicalize_name(name)] = (ver, is_local)
    return pkgs


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


def check_repo(root: Path) -> tuple[list[str], list[str]]:
    """Return (violations, warnings) for one repo."""
    pyproject = root / "pyproject.toml"
    lock = root / "uv.lock"
    if not pyproject.is_file() or not lock.is_file():
        return [], []
    pkgs = load_lock_pkgs(lock)
    violations: list[str] = []
    warnings: list[str] = []
    for req in load_declared_deps(pyproject):
        cname = canonicalize_name(req.name)
        if cname.startswith(INTERNAL_PREFIX):
            continue  # internal unified-* dep — editable, lock version cosmetic (fast path)
        if not req.specifier:
            continue  # no constraint to violate
        entry = pkgs.get(cname)
        if entry is None:
            warnings.append(f"{req.name}: declared {req.specifier} but absent from uv.lock (marker dep?)")
            continue
        pin, is_local = entry
        if is_local:
            continue  # editable/path/directory source (internal sibling, incl. service-named) — resolved on-disk
        try:
            in_range = req.specifier.contains(Version(pin), prereleases=True)
        except InvalidVersion:
            continue  # a non-PEP440 pin (local/url dep) — out of scope
        if not in_range:
            violations.append(f"{req.name}: lock pins {pin} which VIOLATES declared {req.specifier}")
    return violations, warnings


def main() -> int:
    ap = argparse.ArgumentParser(description="Frozen-lock floor guardrail (uv.lock pin in pyproject range)")
    ap.add_argument("--repo", default=".", help="repo root containing pyproject.toml + uv.lock")
    args = ap.parse_args()
    root = Path(args.repo).resolve()

    violations, warnings = check_repo(root)
    for warn in warnings:
        print(f"⚠️  frozen-lock floor: {warn}")
    if violations:
        print(f"❌ frozen-lock floor guardrail: {len(violations)} external pin(s) violate the pyproject range:")
        for viol in violations:
            print(f"   - {viol}")
        print("   `uv sync --frozen` ships the lock pin EXACTLY, so a below-floor pin reaches production.")
        print("   Fix: `uv lock` here, commit pyproject.toml + uv.lock TOGETHER (atomic floor+lock).")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
