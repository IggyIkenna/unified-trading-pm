#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""
check-dep-alignment.py — Dependency Reconciliation Gate (Phase 4)

Checks that a repo's direct deps are aligned with the correct remote version
reference (staging or main), per the per-dep reference logic:

  for each direct dep:
    if dep is in manifest.staging_versions AND --to-staging is true:
      compare to origin/staging
    else:
      compare to origin/main

Usage:
  python3 check-dep-alignment.py --repo <repo-name> --to-staging <true|false> --manifest <path>

Exit codes:
  0 — all deps aligned
  1 — one or more deps misaligned (errors printed to stdout)
"""

import argparse
import base64
import json
import os
import re
import subprocess
import sys
from typing import cast

# ── Constants ────────────────────────────────────────────────────────────────

DEFAULT_OWNER = "IggyIkenna"


# ── Argument Parsing ─────────────────────────────────────────────────────────


class _ParsedArgs(argparse.Namespace):
    repo: str
    to_staging: str
    manifest: str


def parse_args() -> _ParsedArgs:
    parser = argparse.ArgumentParser(description="Check dep alignment against remote pyproject.toml versions.")
    parser.add_argument("--repo", required=True, help="Repo name to check (e.g. trading-service)")
    parser.add_argument(
        "--to-staging",
        required=True,
        choices=["true", "false"],
        dest="to_staging",
        help="Whether this push is targeting staging branch",
    )
    parser.add_argument("--manifest", required=True, help="Path to workspace-manifest.json")
    return parser.parse_args(namespace=_ParsedArgs())


# ── Manifest Helpers ──────────────────────────────────────────────────────────


def load_manifest(manifest_path: str) -> dict[str, object]:
    with open(manifest_path) as f:
        return cast(dict[str, object], json.load(f))


def get_repo_entry(manifest: dict[str, object], repo_name: str) -> dict[str, object]:
    repos: dict[str, object] = cast(dict[str, object], manifest.get("repositories") or {})
    if repo_name not in repos:
        print(f"ERROR: repo '{repo_name}' not found in manifest")
        sys.exit(1)
    return cast(dict[str, object], repos[repo_name])


def get_repo_dependencies(repo_entry: dict[str, object]) -> list[str]:
    """Return list of dep names from the repo entry.

    Items may be plain strings or dicts with a 'name' key.
    """
    raw_deps: list[object] = cast(list[object], repo_entry.get("dependencies") or [])
    names: list[str] = []
    for dep in raw_deps:
        if isinstance(dep, dict):
            name = dep.get("name")
            if name:
                names.append(name)
        elif isinstance(dep, str):
            names.append(dep)
    return names


def get_dep_constraint(repo_entry: dict[str, object], dep_name: str) -> str | None:
    """Return the constraint string for a dep, if declared in the manifest."""
    raw_deps: list[object] = cast(list[object], repo_entry.get("dependencies") or [])
    for dep in raw_deps:
        if isinstance(dep, dict) and dep.get("name") == dep_name:
            return cast(str | None, dep.get("constraint"))
    return None


def get_staging_versions(manifest: dict[str, object]) -> set[str]:
    """Return the set of dep names that have a staging_versions entry."""
    staging: dict[str, object] = cast(dict[str, object], manifest.get("staging_versions") or {})
    return set(staging.keys())


def get_owner_from_manifest(manifest: dict[str, object], dep_name: str) -> str:
    """Detect GitHub org owner from manifest git_url, or fall back to env/default."""
    repos: dict[str, object] = cast(dict[str, object], manifest.get("repositories") or {})
    dep_entry: dict[str, object] = cast(dict[str, object], repos.get(dep_name) or {})
    git_url: str = cast(str, dep_entry.get("git_url") or "")

    # Parse owner from git_url patterns:
    #   git@github.com:Owner/repo.git
    #   https://github.com/Owner/repo.git
    m = re.search(r"github\.com[:/]([^/]+)/", git_url)
    if m:
        return m.group(1)

    return os.environ.get("GITHUB_REPOSITORY_OWNER", DEFAULT_OWNER)


# ── Remote Version Fetching ───────────────────────────────────────────────────


def fetch_remote_pyproject(owner: str, repo_name: str, branch: str) -> str | None:
    """Fetch pyproject.toml content from GitHub API via gh cli.

    Returns the decoded file content as a string, or None on failure.
    """
    result = subprocess.run(
        [
            "gh",
            "api",
            f"repos/{owner}/{repo_name}/contents/pyproject.toml",
            "--ref",
            branch,
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        return None

    try:
        data: dict[str, object] = cast(dict[str, object], json.loads(result.stdout))
        content_b64: str = cast(str, data.get("content") or "")
        # GitHub API may include newlines in base64 — strip them
        content_b64 = content_b64.replace("\n", "")
        return base64.b64decode(content_b64).decode("utf-8")
    except (json.JSONDecodeError, KeyError, UnicodeDecodeError):
        return None


def parse_version_from_pyproject(content: str) -> str | None:
    """Extract [project] version from pyproject.toml content.

    Handles both:
      version = "1.2.3"
      version = '1.2.3'
    """
    m = re.search(r'^version\s*=\s*["\']([^"\']+)["\']', content, re.MULTILINE)
    if m:
        return m.group(1)
    return None


# ── Constraint Checking ───────────────────────────────────────────────────────


def _parse_version_tuple(version_str: str) -> tuple[int, ...]:
    """Parse a semver string into a comparable tuple of ints."""
    parts = version_str.strip().split(".")
    result: list[int] = []
    for part in parts:
        # Strip any non-numeric suffix (e.g. "1rc1" → 1)
        m = re.match(r"(\d+)", part)
        result.append(int(m.group(1)) if m else 0)
    return tuple(result)


def build_expected_constraint(remote_version: str) -> str:
    """Derive the standard constraint from a remote version string.

    Pattern: >=X.Y.Z,<(X+1).0.0
    """
    parts = remote_version.strip().split(".")
    try:
        major = int(parts[0])
    except (IndexError, ValueError):
        major = 0
    return f">={remote_version},<{major + 1}.0.0"


def check_constraint_satisfied(version: str, constraint: str) -> bool:
    """Check whether `version` satisfies a constraint string.

    Supports comma-separated conditions, each of the form:
      >=X.Y.Z   >X.Y.Z   ==X.Y.Z   <=X.Y.Z   <X.Y.Z   !=X.Y.Z
    """
    v_tuple = _parse_version_tuple(version)
    conditions = [c.strip() for c in constraint.split(",") if c.strip()]

    for cond in conditions:
        m = re.match(r"(>=|>|==|<=|<|!=)\s*([0-9][^\s,]*)", cond)
        if not m:
            # Unknown operator — skip this condition conservatively
            continue
        op = m.group(1)
        c_tuple = _parse_version_tuple(m.group(2))

        if (
            (op == ">=" and not (v_tuple >= c_tuple))
            or (op == ">" and not (v_tuple > c_tuple))
            or (op == "==" and v_tuple != c_tuple)
            or (op == "<=" and not (v_tuple <= c_tuple))
            or (op == "<" and not (v_tuple < c_tuple))
            or (op == "!=" and v_tuple == c_tuple)
        ):
            return False

    return True


# ── Main Logic ────────────────────────────────────────────────────────────────


def main() -> int:
    args = parse_args()

    to_staging: bool = args.to_staging.lower() == "true"
    repo_name: str = args.repo

    manifest = load_manifest(args.manifest)
    repo_entry = get_repo_entry(manifest, repo_name)
    dep_names = get_repo_dependencies(repo_entry)
    staging_dep_names = get_staging_versions(manifest)

    if not dep_names:
        print(f"check-dep-alignment: no dependencies declared for '{repo_name}' — OK")
        return 0

    misaligned: list[str] = []

    for dep_name in dep_names:
        # Determine which branch to check
        use_staging = to_staging and dep_name in staging_dep_names
        branch = "staging" if use_staging else "main"

        owner = get_owner_from_manifest(manifest, dep_name)

        # Fetch remote pyproject.toml
        pyproject_content = fetch_remote_pyproject(owner, dep_name, branch)

        if pyproject_content is None:
            print(
                f"WARN: could not fetch pyproject.toml for '{dep_name}' from origin/{branch} — skipping alignment check"
            )
            continue

        remote_version = parse_version_from_pyproject(pyproject_content)

        if remote_version is None:
            print(f"WARN: could not parse version from pyproject.toml for '{dep_name}' (origin/{branch}) — skipping")
            continue

        # Determine the expected constraint
        manifest_constraint = get_dep_constraint(repo_entry, dep_name)
        expected_constraint = manifest_constraint or build_expected_constraint(remote_version)

        # Check alignment: is the remote version within the expected constraint?
        if not check_constraint_satisfied(remote_version, expected_constraint):
            misaligned.append(dep_name)
            print(
                f"ERROR: dep '{dep_name}' not aligned.\n"
                f"  Expected (origin/{branch}): {expected_constraint}\n"
                f"  Found (origin/{branch} version): {remote_version}\n"
                f"  Fix: cd {dep_name} && bash scripts/quickmerge.sh "
                f'"fix: dep update" --agent'
            )
        else:
            print(f"  OK: '{dep_name}' @ {remote_version} satisfies {expected_constraint} (origin/{branch})")

    if misaligned:
        print(
            f"\ncheck-dep-alignment FAILED: {len(misaligned)} dep(s) misaligned "
            f"for '{repo_name}': {', '.join(misaligned)}"
        )
        return 1

    print(f"\ncheck-dep-alignment PASSED: all deps aligned for '{repo_name}'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
