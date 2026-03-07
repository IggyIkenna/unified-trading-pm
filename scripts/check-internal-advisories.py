#!/usr/bin/env python3.13
"""Check repo dependencies against internal vulnerability advisories.

Reads unified-trading-pm/security/internal-advisories.yaml and fails if any
resolved dependency (from uv.lock) matches an advisory that isn't fixed.

Usage:
    python check-internal-advisories.py [--advisories path] [--lock path]
    Called from quality-gates.sh after pip-audit.

Exit: 0 = clean, 1 = violation found.
"""

from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path
from typing import cast

import yaml
from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.version import InvalidVersion, Version


def load_advisories(path: Path) -> list[dict[str, object]]:
    """Load advisories from YAML. Returns list of advisory dicts."""
    with open(path, encoding="utf-8") as f:
        data = cast(dict[str, object] | None, yaml.safe_load(f))
    advisories_raw = data.get("advisories") if isinstance(data, dict) else []
    advisories_list = list(advisories_raw) if isinstance(advisories_raw, list) else []
    return cast(list[dict[str, object]], advisories_list)


def load_resolved_versions(lock_path: Path) -> dict[str, str]:
    """Parse uv.lock and return package name -> version mapping."""
    with open(lock_path, "rb") as f:
        data = cast(dict[str, object], tomllib.load(f))
    result: dict[str, str] = {}
    raw_pkgs = data.get("package") or []
    pkgs: list[dict[str, object]] = [p for p in (raw_pkgs if isinstance(raw_pkgs, list) else []) if isinstance(p, dict)]
    for pkg in pkgs:
        name = pkg.get("name")
        version = pkg.get("version")
        if isinstance(name, str) and isinstance(version, str):
            result[name] = version
    return result


def check_advisory(
    pkg_name: str,
    pkg_version: str,
    advisory: dict[str, object],
) -> bool:
    """Return True if the package version matches the advisory (vulnerable)."""
    adv_pkg = advisory.get("package")
    if not isinstance(adv_pkg, str) or adv_pkg != pkg_name:
        return False
    spec_str = advisory.get("affected_versions")
    if not isinstance(spec_str, str):
        return False
    try:
        spec = SpecifierSet(spec_str)
        ver = Version(pkg_version)
        if not spec.contains(ver):
            return False
    except (InvalidVersion, InvalidSpecifier):
        return False
    fixed_in = advisory.get("fixed_in")
    if isinstance(fixed_in, str):
        try:
            fixed_ver = Version(fixed_in)
            if ver >= fixed_ver:
                return False  # Already fixed
        except (InvalidVersion, InvalidSpecifier):
            pass
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Check deps against internal advisories")
    parser.add_argument(
        "--advisories",
        type=Path,
        default=None,
        help="Path to internal-advisories.yaml",
    )
    parser.add_argument(
        "--lock",
        type=Path,
        default=Path("uv.lock"),
        help="Path to uv.lock",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Repo root (for resolving relative paths)",
    )
    args = parser.parse_args()

    repo_root = Path(cast(Path, args.repo_root)).resolve()
    lock_arg = Path(cast(Path, args.lock))
    lock_path = (repo_root / lock_arg) if not lock_arg.is_absolute() else lock_arg
    if not lock_path.exists():
        return 0  # No lock file — skip (e.g. non-Python repo)

    adv_path: Path
    if cast(Path | None, args.advisories) is None:
        pm_scripts = Path(__file__).resolve().parent
        pm_root = pm_scripts.parent
        adv_path = pm_root / "security" / "internal-advisories.yaml"
    else:
        adv_path = Path(cast(Path, args.advisories))
        if not adv_path.is_absolute():
            adv_path = repo_root / adv_path

    if not adv_path.exists():
        print(f"Advisories file not found: {adv_path}", file=sys.stderr)
        return 0  # No advisories — skip

    advisories: list[dict[str, object]] = load_advisories(adv_path)  # type: ignore[reportAny]
    if not advisories:
        return 0

    resolved = load_resolved_versions(lock_path)
    violations: list[tuple[str, str, dict[str, object]]] = []

    for adv in advisories:
        pkg = adv.get("package")
        if not isinstance(pkg, str):
            continue
        ver = resolved.get(pkg)
        if ver is None:
            continue
        if check_advisory(pkg, ver, adv):
            violations.append((pkg, ver, adv))

    if violations:
        print(
            "Internal advisory violation(s) — see unified-trading-pm/security/internal-advisories.yaml",
            file=sys.stderr,
        )
        for pkg, ver, adv in violations:
            adv_id = adv.get("id") or "?"
            severity = adv.get("severity") or "?"
            desc = adv.get("description") or ""
            print(f"  {pkg}=={ver} — {adv_id} ({severity}): {desc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
