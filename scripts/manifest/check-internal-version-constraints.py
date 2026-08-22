#!/usr/bin/env python3.13
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Validate that internal dep version constraints are satisfiable.

For every repo in workspace-manifest.json that declares internal dependencies,
verifies that the dep's current local version (from its own pyproject.toml) actually
satisfies the declared version constraint.

This catches issues like:
  - UMI declares unified-api-contracts>=1.0.0,<2.0.0 but UAC is at 0.1.3
  - Any >=X.Y.Z lower bound higher than the dep's current version

Also detects per-repo extras conflicts by running uv pip install --dry-run for
every repo with a pyproject.toml (catches intra-package issues like
gcsfs vs fsspec in UTL).

Exit: 0 = all constraints satisfiable, 1 = one or more issues found.

Usage:
    python check-internal-version-constraints.py
    python check-internal-version-constraints.py --skip-dry-run   # skip expensive uv check
    python check-internal-version-constraints.py --dry-run-only   # skip version check
    python check-internal-version-constraints.py --apply          # fix unsatisfiable constraints
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import NamedTuple, cast

SCRIPT_DIR = Path(__file__).resolve().parent
PM_ROOT = SCRIPT_DIR.parent.parent
WORKSPACE_ROOT = PM_ROOT.parent
MANIFEST_PATH = PM_ROOT / "workspace-manifest.json"


# ---------------------------------------------------------------------------
# Packaging-compatible version comparison (no external deps — stdlib only)
# ---------------------------------------------------------------------------


def _parse_version(v: str) -> tuple[int, ...]:
    """Parse a PEP 440-style version string into a comparable tuple."""
    v = v.strip().split("+")[0].split("a")[0].split("b")[0].split("rc")[0]
    try:
        return tuple(int(x) for x in v.split("."))
    except ValueError:
        return (0,)


def _satisfies(version: str, constraint: str) -> bool:
    """Return True if version satisfies the constraint string.

    Supports >= and < operators only (sufficient for our patterns).
    Multi-constraint: 'a,b' — all must pass.
    """
    ver = _parse_version(version)
    for part in constraint.split(","):
        part = part.strip()
        if part.startswith(">="):
            if ver < _parse_version(part[2:]):
                return False
        elif part.startswith("<"):
            if ver >= _parse_version(part[1:]):
                return False
        elif part.startswith("==") and ver != _parse_version(part[2:]):
            return False
    return True


def _derive_safe_constraint(version: str) -> str:
    """Derive a safe, satisfiable version constraint from the dep's current version.

    For version 0.x.y → '>=0.x.0,<1.0.0'
    For version N.x.y (N>=1) → '>=N.x.0,<N+1.0.0'

    This is always satisfiable by the given version.
    """
    parts = _parse_version(version)
    major = parts[0] if len(parts) > 0 else 0
    minor = parts[1] if len(parts) > 1 else 0
    upper = f"{major + 1}.0.0"
    return f">={major}.{minor}.0,<{upper}"


class Issue(NamedTuple):
    repo: str
    dep: str
    constraint: str
    current_version: str
    kind: str  # "version_unsatisfiable" | "install_conflict"
    detail: str
    # Where the constraint lives — for auto-fix routing
    source: str  # "manifest" (default)


def _get_repo_version(repo_name: str) -> str | None:
    """Read the version from a repo's pyproject.toml."""
    pyproject = WORKSPACE_ROOT / repo_name / "pyproject.toml"
    if not pyproject.is_file():
        return None
    try:
        with open(pyproject, "rb") as f:
            data = cast(dict[str, dict[str, object]], tomllib.load(f))
        proj = data.get("project") or {}
        v = proj.get("version") or ""
        return str(v) if v else None
    except (OSError, tomllib.TOMLDecodeError, KeyError, ValueError):
        return None


def check_internal_version_constraints(manifest: dict[str, object]) -> list[Issue]:
    """Check A: every internal dep constraint must be satisfied by the dep's current version."""
    repos = manifest.get("repositories") or {}
    assert isinstance(repos, dict)
    issues: list[Issue] = []

    for repo_name, repo_data in repos.items():
        assert isinstance(repo_data, dict)
        deps = repo_data.get("dependencies") or []
        assert isinstance(deps, list)
        for dep in deps:
            # Manifest supports two forms: dict {name, version} or bare string (name only)
            if isinstance(dep, str):
                dep_name, constraint = dep, ""
            elif isinstance(dep, dict):
                dep_name = str(dep.get("name") or "")
                constraint = str(dep.get("version") or "")
            else:
                continue
            # Bare-string deps have no version constraint to check
            if not dep_name or not constraint:
                continue

            # Only check internal deps (repos that exist in the manifest)
            if dep_name not in repos:
                continue

            current_version = _get_repo_version(dep_name)
            if current_version is None:
                continue  # can't check without pyproject.toml

            if not _satisfies(current_version, constraint):
                issues.append(
                    Issue(
                        repo=repo_name,
                        dep=dep_name,
                        constraint=constraint,
                        current_version=current_version,
                        kind="version_unsatisfiable",
                        detail=(
                            f"{dep_name}=={current_version} does not satisfy "
                            f"{dep_name}{constraint} declared by {repo_name}"
                        ),
                        source="manifest",
                    )
                )

    return issues


def check_per_repo_install(manifest: dict[str, object], skip_repos: set[str] | None = None) -> list[Issue]:
    """Check B: run uv pip install --dry-run for each repo to catch extras conflicts."""
    repos = manifest.get("repositories") or {}
    assert isinstance(repos, dict)
    issues: list[Issue] = []
    skip = skip_repos or set()

    # Only check repos with a local pyproject.toml (Python packages)
    for repo_name in repos:
        if repo_name in skip:
            continue
        pyproject = WORKSPACE_ROOT / repo_name / "pyproject.toml"
        if not pyproject.is_file():
            continue

        # Check installability of the package with all deps (flat — no extras)
        result = subprocess.run(
            ["uv", "pip", "install", "--dry-run", f"-e{WORKSPACE_ROOT / repo_name}"],
            capture_output=True,
            text=True,
            cwd=str(WORKSPACE_ROOT / repo_name),
        )
        if result.returncode != 0:
            stderr = result.stderr.strip()
            # Filter out benign warnings, only keep actual resolution errors
            error_lines = [
                line
                for line in stderr.splitlines()
                if "error" in line.lower() or "cannot" in line.lower() or "conflict" in line.lower()
            ]
            if error_lines:
                issues.append(
                    Issue(
                        repo=repo_name,
                        dep="(extras resolution)",
                        constraint="(base deps)",
                        current_version="",
                        kind="install_conflict",
                        detail="\n".join(error_lines[:5]),
                        source="manifest",
                    )
                )

    return issues


# ---------------------------------------------------------------------------
# Auto-fix: update workspace-manifest.json and optionally pyproject.toml
# ---------------------------------------------------------------------------


def _fix_manifest_constraint(
    manifest_path: Path,
    repo_name: str,
    dep_name: str,
    new_constraint: str,
) -> bool:
    """Update the version field in workspace-manifest.json for a specific dep entry.

    Returns True if a change was written.
    """
    with open(manifest_path) as f:
        manifest: dict[str, object] = cast(dict[str, object], json.load(f))

    repos = manifest.get("repositories") or {}
    if not isinstance(repos, dict):
        return False
    repo_data = repos.get(repo_name)
    if not isinstance(repo_data, dict):
        return False
    deps = repo_data.get("dependencies") or []
    if not isinstance(deps, list):
        return False

    changed = False
    for dep in deps:
        if isinstance(dep, dict) and dep.get("name") == dep_name:
            old = dep.get("version") or ""
            if old != new_constraint:
                dep["version"] = new_constraint
                changed = True
                print(f"    manifest: [{repo_name}] {dep_name}: {old!r} → {new_constraint!r}")

    if changed:
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")

    return changed


def _fix_pyproject_constraint(
    pyproject_path: Path,
    dep_name: str,
    old_constraint: str,
    new_constraint: str,
) -> bool:
    """Update the version constraint for dep_name in a pyproject.toml dependencies list.

    Handles both `dep-name>=X` and `dep_name>=X` forms (dash/underscore).
    Returns True if a change was written.
    """
    text = pyproject_path.read_text()

    # Match dep name (dash or underscore interchangeable) followed by old_constraint
    # in a quoted string context, e.g. "dep-name>=1.0.0,<2.0.0"
    dep_pattern = dep_name.replace("-", "[-_]")
    old_escaped = re.escape(old_constraint)
    pattern = re.compile(
        r'("' + dep_pattern + r"(?:\[[^\]]*\])?)" + old_escaped + r'"',
        re.IGNORECASE,
    )

    new_text, count = pattern.subn(lambda m: m.group(1) + new_constraint + '"', text)
    if count == 0:
        return False

    pyproject_path.write_text(new_text)
    print(
        f"    pyproject: {pyproject_path.parent.name}/pyproject.toml: "
        f"{dep_name}{old_constraint!r} → {dep_name}{new_constraint!r}"
    )
    return True


def apply_fixes(issues: list[Issue]) -> int:
    """Apply safe auto-fixes for version_unsatisfiable issues.

    Safe fix: derive constraint from dep's current local version (always satisfiable).
    Updates:
      1. workspace-manifest.json dep entry version field
      2. pyproject.toml of the declaring repo (if it has matching constraint)

    Returns count of issues fixed.
    """
    fixed = 0
    for issue in issues:
        if issue.kind != "version_unsatisfiable":
            continue  # install_conflict requires manual fix

        new_constraint = _derive_safe_constraint(issue.current_version)
        print(f"  Fixing [{issue.repo}] {issue.dep}: {issue.constraint!r} → {new_constraint!r}")

        # Fix 1: workspace-manifest.json
        _fix_manifest_constraint(MANIFEST_PATH, issue.repo, issue.dep, new_constraint)

        # Fix 2: pyproject.toml of the declaring repo (best effort)
        pyproject = WORKSPACE_ROOT / issue.repo / "pyproject.toml"
        if pyproject.is_file():
            _fix_pyproject_constraint(pyproject, issue.dep, issue.constraint, new_constraint)

        fixed += 1

    return fixed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply", action="store_true", help="Fix unsatisfiable constraints in manifest and pyproject.toml"
    )
    parser.add_argument("--skip-dry-run", action="store_true", help="Skip uv pip install --dry-run per-repo check")
    parser.add_argument(
        "--dry-run-only", action="store_true", help="Skip version constraint check, only run uv dry-run"
    )
    parser.add_argument("--skip-repos", nargs="*", default=[], help="Repo names to skip for dry-run check")
    args = parser.parse_args()
    apply_fix: bool = cast(bool, args.apply)
    skip_dry_run: bool = cast(bool, args.skip_dry_run)
    dry_run_only: bool = cast(bool, args.dry_run_only)
    skip_repos: list[str] = cast(list[str], args.skip_repos)

    if not MANIFEST_PATH.is_file():
        print(f"ERROR: {MANIFEST_PATH} not found", file=sys.stderr)
        return 1

    with open(MANIFEST_PATH) as f:
        manifest: dict[str, object] = cast(dict[str, object], json.load(f))

    all_issues: list[Issue] = []

    # Check A: internal version constraint satisfiability
    if not dry_run_only:
        version_issues = check_internal_version_constraints(manifest)
        all_issues.extend(version_issues)
        if version_issues:
            print(f"  Found {len(version_issues)} unsatisfiable internal version constraint(s):")
            for issue in version_issues:
                print(f"    [{issue.repo}] {issue.detail}")
        else:
            print("  Internal version constraints: all satisfiable")

    # Check B: per-repo install dry-run
    if not skip_dry_run:
        print("  Running per-repo install dry-run (checks extras conflicts)...")
        skip = set(skip_repos)
        install_issues = check_per_repo_install(manifest, skip_repos=skip)
        all_issues.extend(install_issues)
        if install_issues:
            print(f"  Found {len(install_issues)} repo(s) with install conflicts:")
            for issue in install_issues:
                print(f"    [{issue.repo}] {issue.detail}")
        else:
            print("  Per-repo install dry-run: all repos resolve cleanly")

    if not all_issues:
        print("  OK: all internal version constraints satisfied; all repos install cleanly")
        return 0

    version_issues_only = [i for i in all_issues if i.kind == "version_unsatisfiable"]
    install_issues_only = [i for i in all_issues if i.kind == "install_conflict"]

    if apply_fix:
        if version_issues_only:
            print(f"\n  Applying safe fixes for {len(version_issues_only)} unsatisfiable constraint(s)...")
            fixed = apply_fixes(version_issues_only)
            print(f"  Fixed {fixed} constraint(s) in manifest and pyproject.toml.")
        if install_issues_only:
            print(f"\n  {len(install_issues_only)} install conflict(s) require manual fix (extras resolution).")
        # Re-run check to confirm
        with open(MANIFEST_PATH) as f:
            manifest = cast(dict[str, object], json.load(f))
        remaining = check_internal_version_constraints(manifest)
        if remaining:
            print(f"\n  {len(remaining)} constraint(s) still unsatisfiable after fix:")
            for issue in remaining:
                print(f"    [{issue.repo}] {issue.detail}")
            return 1
        if not install_issues_only:
            print("  OK: all constraints now satisfiable.")
            return 0
        return 1

    fixable = len(version_issues_only)
    manual = len(install_issues_only)
    print(
        f"\n  {len(all_issues)} issue(s) found — "
        f"{fixable} auto-fixable (run with --apply), "
        f"{manual} require manual fix."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
