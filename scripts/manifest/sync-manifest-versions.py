#!/usr/bin/env python3.13
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""Sync manifest versions section with pyproject.toml versions.

Reads workspace-manifest.json and for each repo reads its pyproject.toml
to compare the current version against manifest["versions"][repo].

Reports:
  MISSING: <repo>  pyproject=<v>   (repo not in manifest versions section)
  DRIFT:   <repo>  manifest=<v>  pyproject=<v>  (version mismatch)

With --apply: writes pyproject.toml version into manifest["versions"][repo]
for any missing or drifted repo and rewrites workspace-manifest.json.

Usage:
    python sync-manifest-versions.py
    python sync-manifest-versions.py --apply

Exit: 0 = clean (or successfully fixed), 1 = drift found (dry run).
"""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path
from typing import cast

SCRIPT_DIR = Path(__file__).resolve().parent
PM_ROOT = SCRIPT_DIR.parent.parent
MANIFEST_PATH = PM_ROOT / "workspace-manifest.json"

# Workspace root is one level above PM root
WORKSPACE_ROOT = PM_ROOT.parent

JsonDict = dict[str, object]

# Repo types that have no pyproject.toml (skip silently)
_UI_TYPES = {"ui"}


def _jdict(val: object) -> JsonDict | None:
    if isinstance(val, dict):
        return cast(JsonDict, val)
    return None


def _jstr(val: object, default: str = "") -> str:
    return str(val) if val is not None else default


def load_json(path: Path) -> JsonDict:
    with open(path) as f:
        return cast(JsonDict, json.load(f))


def get_repo_path(manifest: JsonDict, repo_name: str) -> Path:
    """Return the filesystem path for a repo, honouring folder_name when present."""
    repos_raw = _jdict(manifest.get("repositories")) or {}
    entry = _jdict(repos_raw.get(repo_name)) or {}
    folder = entry.get("folder_name")
    if isinstance(folder, str) and folder:
        return WORKSPACE_ROOT / folder
    return WORKSPACE_ROOT / repo_name


def get_repo_type(manifest: JsonDict, repo_name: str) -> str:
    repos_raw = _jdict(manifest.get("repositories")) or {}
    entry = _jdict(repos_raw.get(repo_name)) or {}
    return _jstr(entry.get("type"))


def read_pyproject_version(repo_path: Path) -> str | None:
    """Return version string from pyproject.toml, or None if not present/parseable."""
    pyproject = repo_path / "pyproject.toml"
    if not pyproject.is_file():
        return None
    with open(pyproject, "rb") as f:
        data = tomllib.load(f)
    project = data.get("project")
    if not isinstance(project, dict):
        return None
    version = project.get("version")
    if not isinstance(version, str) or not version:
        return None
    return version


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync manifest versions section with pyproject.toml versions.")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write fixes into workspace-manifest.json (dry-run by default).",
    )
    args = parser.parse_args()
    apply_fixes: bool = cast(bool, args.apply)

    if not MANIFEST_PATH.is_file():
        print(f"ERROR: Manifest not found: {MANIFEST_PATH}", file=sys.stderr)
        return 1

    manifest = load_json(MANIFEST_PATH)
    repos_raw = _jdict(manifest.get("repositories")) or {}
    manifest_versions_raw = _jdict(manifest.get("versions")) or {}
    # Build a mutable dict[str, str] of current manifest versions
    manifest_versions: dict[str, str] = {k: _jstr(v) for k, v in manifest_versions_raw.items() if isinstance(v, str)}

    drift_items: list[tuple[str, str | None, str]] = []  # (repo, manifest_v, pyproject_v)

    for repo_name in sorted(repos_raw):
        repo_type = get_repo_type(manifest, repo_name)
        if repo_type in _UI_TYPES:
            # UI repos have no pyproject.toml — skip without noise
            continue

        repo_path = get_repo_path(manifest, repo_name)
        pyproject_version = read_pyproject_version(repo_path)

        if pyproject_version is None:
            # pyproject.toml absent or has no version — skip (could be infra/non-Python repo)
            continue

        manifest_v = manifest_versions.get(repo_name)
        if manifest_v is None:
            drift_items.append((repo_name, None, pyproject_version))
        elif manifest_v != pyproject_version:
            drift_items.append((repo_name, manifest_v, pyproject_version))

    if not drift_items:
        print("OK: manifest versions section is aligned with all pyproject.toml versions.")
        return 0

    # Report drift
    for repo_name, manifest_v, pyproject_v in drift_items:
        if manifest_v is None:
            print(f"MISSING: {repo_name}  pyproject={pyproject_v}")
        else:
            print(f"DRIFT:   {repo_name}  manifest={manifest_v}  pyproject={pyproject_v}")

    if not apply_fixes:
        print(
            f"\n{len(drift_items)} version drift(s) found.  Re-run with --apply to fix.",
            file=sys.stderr,
        )
        return 1

    # Apply: update manifest["versions"] with pyproject versions
    # Preserve the existing structure — update in-place
    versions_section = manifest.get("versions")
    if not isinstance(versions_section, dict):
        manifest["versions"] = {}
        versions_section = cast(dict[str, object], manifest["versions"])

    for repo_name, _manifest_v, pyproject_v in drift_items:
        versions_section[repo_name] = pyproject_v
        action = "added" if _manifest_v is None else "updated"
        print(f"  {action}: {repo_name} -> {pyproject_v}")

    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"\nApplied {len(drift_items)} fix(es) to {MANIFEST_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
