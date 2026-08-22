#!/usr/bin/env python3.13
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Propagate workspace canonical dependency versions to all repo pyproject.toml files.

Reads unified-trading-pm/workspace-constraints.toml and workspace-manifest.json (topological order),
then for each repo with pyproject.toml: replaces version specs for constrained packages with the
canonical spec, leaves [tool.uv.sources] and other sections unchanged, and runs uv lock.

Usage:
    python propagate-canonical-versions.py              # dry run (print changes only)
    python propagate-canonical-versions.py --apply      # write pyproject.toml and run uv lock
    python propagate-canonical-versions.py --apply --commit  # also git add/commit per repo
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import cast

type TomlDict = dict[str, object]

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
MANIFEST_PATH = WORKSPACE_ROOT / "unified-trading-pm" / "workspace-manifest.json"
CONSTRAINTS_PATH = WORKSPACE_ROOT / "unified-trading-pm" / "workspace-constraints.toml"


def load_manifest() -> TomlDict:
    with open(MANIFEST_PATH) as f:
        return cast(TomlDict, json.load(f))


def _level_sort_key(lvl: TomlDict) -> int:
    raw = lvl.get("level")
    return int(cast(int, raw)) if isinstance(raw, int) else 999


def get_topological_order(manifest: TomlDict) -> list[str]:
    topo_raw = manifest.get("topologicalOrder")
    if not isinstance(topo_raw, dict):
        return []
    topo = cast(TomlDict, topo_raw)
    levels_raw = topo.get("levels")
    if not isinstance(levels_raw, list):
        return []
    levels = [cast(TomlDict, lvl) for lvl in levels_raw if isinstance(lvl, dict)]
    ordered: list[str] = []
    for level in sorted(levels, key=_level_sort_key):
        repos_raw = level.get("repos")
        if not isinstance(repos_raw, list):
            continue
        for repo in repos_raw:
            if isinstance(repo, str):
                ordered.append(repo)
    return ordered


def get_repo_folder_path(manifest: TomlDict, repo_name: str) -> Path:
    repos_raw = manifest.get("repositories")
    if isinstance(repos_raw, dict):
        entry = repos_raw.get(repo_name)
        if isinstance(entry, dict):
            folder = entry.get("folder_name")
            if isinstance(folder, str):
                return WORKSPACE_ROOT / folder
    return WORKSPACE_ROOT / repo_name


def normalize_pkg_name(name: str) -> str:
    return name.lower().replace("-", "_").replace(".", "_")


def load_constraints() -> dict[str, str]:
    """Load [dependencies] from workspace-constraints.toml. Keys normalized."""
    if not CONSTRAINTS_PATH.is_file():
        return {}
    with open(CONSTRAINTS_PATH, "rb") as f:
        data = cast(TomlDict, tomllib.load(f))
    deps_raw = data.get("dependencies")
    if not isinstance(deps_raw, dict):
        return {}
    return {normalize_pkg_name(k): str(v) for k, v in deps_raw.items()}


# Match a dependency line: "name>=... or "name==... or 'name>=...
_SPEC_PATTERN = re.compile(r'^(\s*["\'])([^"\']+)(["\']\s*,?\s*)$')


def _replace_dep_spec(line: str, constraints: dict[str, str]) -> str:
    """If line is a dependency spec and package is in constraints, replace spec; else return line."""
    m = _SPEC_PATTERN.match(line)
    if not m:
        return line
    prefix, pkg_spec, suffix = m.group(1), m.group(2), m.group(3)
    # Split on the EARLIEST operator position across ALL operators — never the first
    # operator scanned. A ceiling-first spec ("fastapi<1.0.0,>=0.115.0") leads with "<",
    # so scanning ">=" first and splitting there would take "fastapi<1.0.0," as the package
    # name → miss the constraint → silently return the spec unchanged (the latent bug).
    positions = [idx for sep in (">=", "<=", "!=", "==", ">", "<", "~=") if (idx := pkg_spec.find(sep)) > 0]
    if not positions:
        return line
    pkg_name = pkg_spec[: min(positions)].strip()
    norm = normalize_pkg_name(pkg_name)
    if norm in constraints:
        return f"{prefix}{constraints[norm]}{suffix}"
    return line


def update_pyproject_content(content: str, constraints: dict[str, str]) -> str:
    """Replace dependency specs on any line that looks like a dep spec and is in constraints."""
    lines = content.splitlines(keepends=True)
    return "".join(_replace_dep_spec(line, constraints) for line in lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Propagate canonical versions to repo pyproject.toml files")
    parser.add_argument("--apply", action="store_true", help="Write changes and run uv lock")
    parser.add_argument("--commit", action="store_true", help="Git add and commit (implies --apply)")
    args = parser.parse_args()
    do_apply = cast(bool, args.apply) or cast(bool, args.commit)
    do_commit = cast(bool, args.commit)

    if not CONSTRAINTS_PATH.is_file():
        print(f"ERROR: Constraints file not found: {CONSTRAINTS_PATH}", file=sys.stderr)
        print("Run resolve-canonical-versions.py first.", file=sys.stderr)
        sys.exit(1)
    if not MANIFEST_PATH.is_file():
        print(f"ERROR: Manifest not found: {MANIFEST_PATH}", file=sys.stderr)
        sys.exit(1)

    constraints = load_constraints()
    manifest = load_manifest()
    topo_order = get_topological_order(manifest)

    updated: list[str] = []
    for repo_name in topo_order:
        repo_path = get_repo_folder_path(manifest, repo_name)
        pyproject = repo_path / "pyproject.toml"
        if not pyproject.is_file():
            continue
        content = pyproject.read_text()
        new_content = update_pyproject_content(content, constraints)
        if new_content != content:
            updated.append(repo_name)
            if do_apply:
                pyproject.write_text(new_content)
                print(f"  Updated {repo_name}/pyproject.toml")
                lock_file = repo_path / "uv.lock"
                if lock_file.is_file() or True:
                    r = subprocess.run(
                        ["uv", "lock"],
                        cwd=repo_path,
                        capture_output=True,
                        text=True,
                    )
                    if r.returncode != 0:
                        print(f"    WARNING: uv lock failed: {r.stderr}", file=sys.stderr)
                    else:
                        print("    uv lock OK")
                if do_commit:
                    subprocess.run(["git", "add", "pyproject.toml", "uv.lock"], cwd=repo_path, check=False)
                    subprocess.run(
                        ["git", "commit", "-m", "chore: align dependencies to workspace canonical versions"],
                        cwd=repo_path,
                        check=False,
                    )
            else:
                print(f"  Would update {repo_name}/pyproject.toml")
    if not updated:
        print("No repos needed updates.")
    elif not do_apply:
        print(f"\n{len(updated)} repo(s) would be updated. Run with --apply to write and run uv lock.")


if __name__ == "__main__":
    main()
