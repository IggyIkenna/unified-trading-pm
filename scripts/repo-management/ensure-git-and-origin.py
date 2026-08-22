#!/usr/bin/env python3.13
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""
Ensure every manifest repo that exists as a workspace folder has .git and origin.
Run from workspace root. Creates GitHub remote URL IggyIkenna/<folder>.git;
push will work once the repo exists on GitHub (create via gh repo create or GitHub UI).
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import cast

logger = logging.getLogger(__name__)
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
MANIFEST_PATH = WORKSPACE_ROOT / "unified-trading-pm" / "workspace-manifest.json"
DEFAULT_OWNER = "IggyIkenna"


def get_folders_from_manifest() -> list[tuple[str, str]]:
    """Return [(manifest_key, folder_name)] for repos that have a folder in workspace."""
    with open(MANIFEST_PATH) as f:
        manifest = cast(dict[str, object], json.load(f))
    repos = cast(dict[str, dict[str, str]], (manifest.get("repositories") or {}))
    out: list[tuple[str, str]] = []
    for name, data in repos.items():
        folder = str(data.get("folder_name", name))
        path = WORKSPACE_ROOT / folder
        if path.exists() and path.is_dir():
            out.append((name, folder))
    return sorted(out, key=lambda x: x[1])


def has_git(repo_path: Path) -> bool:
    return (repo_path / ".git").exists()


def get_origin(repo_path: Path) -> str | None:
    try:
        r = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        logger.debug("Suppressed %s during get origin: %s", type(e).__name__, e)
        pass
    return None


def git_init(repo_path: Path) -> tuple[bool, str]:
    try:
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True, timeout=10)
        # default branch main
        subprocess.run(
            ["git", "branch", "-M", "main"],
            cwd=repo_path,
            check=True,
            capture_output=True,
            timeout=5,
        )
        return True, "initialized"
    except subprocess.CalledProcessError as e:
        return False, str(e)


def add_origin(repo_path: Path, folder: str, owner: str = DEFAULT_OWNER) -> tuple[bool, str]:
    url = f"git@github.com:{owner}/{folder}.git"
    try:
        subprocess.run(
            ["git", "remote", "add", "origin", url],
            cwd=repo_path,
            check=True,
            capture_output=True,
            timeout=5,
        )
        return True, url
    except subprocess.CalledProcessError as e:
        raw_stderr = cast(bytes | str | None, e.stderr)
        stderr_text = raw_stderr.decode(errors="replace") if isinstance(raw_stderr, bytes) else str(raw_stderr or "")
        if "already exists" in stderr_text:
            return True, "already set"
        return False, str(e)


def main() -> int:
    dry = "--dry-run" in sys.argv
    folders = get_folders_from_manifest()
    if not folders:
        print("No manifest repos found as folders.", file=sys.stderr)
        return 1
    inited: list[str] = []
    origins_added: list[str] = []
    errors: list[tuple[str, str]] = []
    for _name, folder in folders:
        path = WORKSPACE_ROOT / folder
        if not has_git(path):
            if dry:
                print(f"  [dry] would git init: {folder}")
            else:
                ok, msg = git_init(path)
                if ok:
                    inited.append(folder)
                else:
                    errors.append((folder, f"git init: {msg}"))
        if get_origin(path) is None:
            if dry:
                print(f"  [dry] would add origin: {folder} -> git@github.com:{DEFAULT_OWNER}/{folder}.git")
            else:
                ok, msg = add_origin(path, folder)
                if ok:
                    origins_added.append(folder)
                else:
                    errors.append((folder, msg))
    if dry:
        print(f"\nWould process {len(folders)} manifest repos.")
        return 0
    if inited:
        print("Git inited:", ", ".join(inited))
    if origins_added:
        print("Origin added:", ", ".join(origins_added))
    if errors:
        for folder, msg in errors:
            print(f"  {folder}: {msg}", file=sys.stderr)
        return 1
    if not inited and not origins_added:
        print("All manifest repos already have .git and origin.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
