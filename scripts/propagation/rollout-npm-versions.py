#!/usr/bin/env python3.13
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Enforce canonical npm devDependency versions across all UI repos.

Reads unified-trading-pm/workspace-npm-constraints.json and workspace-manifest.json,
then for each UI repo (type='ui'): checks package.json devDependencies against the
canonical constraints and reports mismatches. With --apply, updates package.json in place.

This is the npm analogue of propagate-canonical-versions.py for Python pyproject.toml files.

Usage:
    python3 rollout-npm-versions.py              # dry run — print mismatches only
    python3 rollout-npm-versions.py --apply      # write updated package.json files
    python3 rollout-npm-versions.py --repo NAME  # check/apply a single repo only
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

type JsonDict = dict[str, object]


class _Args(argparse.Namespace):
    repo: str | None
    apply: bool


SCRIPT_DIR = Path(__file__).resolve().parent
PM_ROOT = SCRIPT_DIR.parent.parent
WORKSPACE_ROOT = PM_ROOT.parent
MANIFEST_PATH = PM_ROOT / "workspace-manifest.json"
CONSTRAINTS_PATH = PM_ROOT / "workspace-npm-constraints.json"

SKIP_STATUSES = frozenset({"deprecated", "archived", "deleted"})


def parse_semver(spec: str) -> tuple[int, int, int]:
    """Extract numeric version from a semver range spec like '^2.0.0', '~1.3.0', '>=16.0.0'.
    Returns (major, minor, patch) tuple for comparison. Returns (0,0,0) if unparseable."""
    m = re.search(r"(\d+)\.(\d+)\.(\d+)", spec)
    if m:
        return int(m.group(1)), int(m.group(2)), int(m.group(3))
    m2 = re.search(r"(\d+)\.(\d+)", spec)
    if m2:
        return int(m2.group(1)), int(m2.group(2)), 0
    return (0, 0, 0)


def version_is_below_canonical(repo_spec: str, canonical_spec: str) -> bool:
    """Return True only if the repo's version floor is strictly older than the canonical floor.
    A repo with '^4.2.1' vs canonical '^4.2.0' is NOT below (it's equal-or-newer) → False.
    A repo with '^14.1.2' vs canonical '^16.3.2' IS below → True."""
    # If specs are identical, skip
    if repo_spec == canonical_spec:
        return False
    # Extract prefix (^ ~ >= > = none)
    repo_v = parse_semver(repo_spec)
    canon_v = parse_semver(canonical_spec)
    return repo_v < canon_v


def load_json(path: Path) -> JsonDict:
    with path.open() as f:
        return json.load(f)  # type: ignore[no-any-return]


def write_json(path: Path, data: JsonDict) -> None:
    with path.open("w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def get_ui_repos(manifest: JsonDict, only_repo: str | None) -> list[str]:
    repos_raw = manifest.get("repositories")
    repos: JsonDict = repos_raw if isinstance(repos_raw, dict) else {}  # type: ignore[assignment]
    result: list[str] = []
    for name, info in repos.items():
        if not isinstance(info, dict):
            continue
        if info.get("status") in SKIP_STATUSES:
            continue
        if info.get("type") != "ui":
            continue
        if only_repo and name != only_repo:
            continue
        result.append(name)
    return sorted(result)


def check_repo(
    repo_name: str,
    constraints: dict[str, str],
    apply: bool,
) -> list[str]:
    """Check (and optionally fix) one UI repo. Returns list of mismatch messages."""
    pkg_path = WORKSPACE_ROOT / repo_name / "package.json"
    if not pkg_path.exists():
        print(f"  ⚠️  {repo_name}: package.json not found — repo may not be cloned (skipped)")
        return []

    pkg: JsonDict = load_json(pkg_path)
    dev_deps: dict[str, str] = {}
    raw_dev = pkg.get("devDependencies")
    if isinstance(raw_dev, dict):
        dev_deps = {k: str(v) for k, v in raw_dev.items()}

    mismatches: list[str] = []
    updated = False

    for package, canonical_spec in constraints.items():
        if package not in dev_deps:
            # Package not present — skip (repo may intentionally not use it)
            continue
        current = dev_deps[package]
        # Only flag if the repo's version floor is strictly OLDER than the canonical floor.
        # Repos with newer patch/minor versions are OK — do not downgrade them.
        if version_is_below_canonical(current, canonical_spec):
            mismatches.append(f"  {repo_name}/{package}: {current!r} → {canonical_spec!r}")
            if apply:
                dev_deps[package] = canonical_spec
                updated = True

    if apply and updated and isinstance(pkg.get("devDependencies"), dict):
        pkg["devDependencies"] = dev_deps  # type: ignore[assignment]
        write_json(pkg_path, pkg)

    return mismatches


def main() -> int:
    parser = argparse.ArgumentParser(description="Enforce canonical npm devDependency versions across UI repos")
    parser.add_argument("--apply", action="store_true", help="Write updated package.json files")
    parser.add_argument("--repo", type=str, default=None, help="Process only this repo")
    args = parser.parse_args(namespace=_Args())

    if not MANIFEST_PATH.exists():
        print(f"❌ Manifest not found: {MANIFEST_PATH}", file=sys.stderr)
        return 1
    if not CONSTRAINTS_PATH.exists():
        print(f"❌ Constraints not found: {CONSTRAINTS_PATH}", file=sys.stderr)
        return 1

    manifest = load_json(MANIFEST_PATH)
    constraints_doc = load_json(CONSTRAINTS_PATH)
    raw_constraints = constraints_doc.get("devDependencies")
    if not isinstance(raw_constraints, dict):
        print("❌ workspace-npm-constraints.json missing 'devDependencies' key", file=sys.stderr)
        return 1
    constraints: dict[str, str] = {k: str(v) for k, v in raw_constraints.items()}

    ui_repos = get_ui_repos(manifest, args.repo)
    if not ui_repos:
        print("⚠️  No UI repos found in manifest (type='ui')", file=sys.stderr)
        return 0

    mode = "APPLY" if args.apply else "DRY RUN"
    print(f"🔍 npm version check ({mode}) — {len(ui_repos)} UI repo(s)")
    print(f"   Constraints: {CONSTRAINTS_PATH.name}  ({len(constraints)} packages)")
    print()

    all_mismatches: list[str] = []
    for repo in ui_repos:
        mismatches = check_repo(repo, constraints, apply=args.apply)
        all_mismatches.extend(mismatches)

    if not all_mismatches:
        print("✅ All UI repos match canonical npm constraints")
        return 0

    if args.apply:
        print(f"✅ Applied {len(all_mismatches)} version update(s):")
        for m in all_mismatches:
            print(m)
        print()
        print("  Next: run npm install in updated repos (or run-all-setup.sh --rollout-first)")
    else:
        print(f"❌ {len(all_mismatches)} version mismatch(es) found:")
        for m in all_mismatches:
            print(m)
        print()
        print("  Fix: python3 unified-trading-pm/scripts/propagation/rollout-npm-versions.py --apply")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
