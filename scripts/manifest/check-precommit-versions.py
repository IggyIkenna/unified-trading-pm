#!/usr/bin/env python3.13
"""Validate pre-commit hook revisions against canonical versions in workspace-constraints.toml.

For each repo in workspace-manifest.json, checks .pre-commit-config.yaml:
  - ruff hook rev matches canonical ruff version (e.g. v0.15.0)
  - pre-commit-hooks rev matches canonical (v6.0.0)
  - Library repos have a 'bump-library-version' local hook
  - .git/hooks/pre-commit exists (hook is installed)

With --apply:
  - Updates ruff rev to canonical in .pre-commit-config.yaml
  - Updates pre-commit-hooks rev to canonical
  - Adds bump-library-version hook block to library repos that are missing it
  - Runs `pre-commit install` for repos missing .git/hooks/pre-commit

Usage:
    python check-precommit-versions.py
    python check-precommit-versions.py --apply

Exit: 0 = all clean (or successfully fixed), 1 = issues found (dry run).
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import cast

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
PM_ROOT = SCRIPT_DIR.parent.parent
MANIFEST_PATH = PM_ROOT / "workspace-manifest.json"
CONSTRAINTS_PATH = PM_ROOT / "workspace-constraints.toml"
WORKSPACE_ROOT = PM_ROOT.parent

JsonDict = dict[str, object]

# Canonical pre-commit-hooks rev (hardcoded; ruff comes from constraints.toml)
CANONICAL_PRECOMMIT_HOOKS_REV = "v6.0.0"

# Template for the bump-library-version local hook block
_BUMP_HOOK_BLOCK = """\
  - repo: local
    hooks:
      - id: bump-library-version
        name: Auto-bump library version
        entry: bash scripts/bump-library-version.sh
        language: system
        pass_filenames: false
        stages: [commit]
"""

# Ruff pre-commit repo URL
_RUFF_REPO = "https://github.com/astral-sh/ruff-pre-commit"
_PRECOMMIT_HOOKS_REPO = "https://github.com/pre-commit/pre-commit-hooks"


def _jdict(val: object) -> JsonDict | None:
    if isinstance(val, dict):
        return cast(JsonDict, val)
    return None


def _jstr(val: object, default: str = "") -> str:
    return str(val) if val is not None else default


def load_json(path: Path) -> JsonDict:
    with open(path) as f:
        return cast(JsonDict, json.load(f))


def load_constraints(path: Path) -> dict[str, str]:
    """Read workspace-constraints.toml and return {pkg_key: version_spec}."""
    if not path.is_file():
        return {}
    with open(path, "rb") as f:
        data = tomllib.load(f)
    deps = data.get("dependencies")
    if not isinstance(deps, dict):
        return {}
    return {k: str(v) for k, v in deps.items()}


def extract_canonical_ruff_version(constraints: dict[str, str]) -> str | None:
    """Return the pinned ruff version as a rev string (e.g. 'v0.15.0').

    workspace-constraints.toml stores ruff as: ruff = "ruff==0.15.0"
    We extract '0.15.0' and prefix with 'v'.
    """
    ruff_spec = constraints.get("ruff") or ""
    # Match exact pin: ==X.Y.Z
    m = re.search(r"==(\d+\.\d+\.\d+)", ruff_spec)
    if m:
        return f"v{m.group(1)}"
    return None


def get_repo_path(manifest: JsonDict, repo_name: str) -> Path:
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


def load_precommit_config(repo_path: Path) -> list[object] | None:
    """Load .pre-commit-config.yaml repos list, or None if file absent or invalid."""
    config_path = repo_path / ".pre-commit-config.yaml"
    if not config_path.is_file():
        return None
    try:
        with open(config_path) as f:
            data = cast(dict[str, object], yaml.safe_load(f))
    except yaml.YAMLError as e:
        print(f"  WARNING: skipping {repo_path.name}/.pre-commit-config.yaml — YAML parse error: {e}", file=sys.stderr)
        return None
    if not isinstance(data, dict):
        return None
    repos = data.get("repos")
    if not isinstance(repos, list):
        return []
    return repos


def find_repo_entry(repos: list[object], url: str) -> JsonDict | None:
    """Find a repo entry by URL in the repos list."""
    for entry in repos:
        entry_d = _jdict(entry)
        if entry_d and _jstr(entry_d.get("repo")) == url:
            return entry_d
    return None


def has_bump_library_hook(repos: list[object]) -> bool:
    """Return True if a local hook with id=bump-library-version exists."""
    for entry in repos:
        entry_d = _jdict(entry)
        if not entry_d:
            continue
        if _jstr(entry_d.get("repo")) != "local":
            continue
        hooks_raw = entry_d.get("hooks")
        if not isinstance(hooks_raw, list):
            continue
        for hook in hooks_raw:
            hook_d = _jdict(hook)
            if hook_d and _jstr(hook_d.get("id")) == "bump-library-version":
                return True
    return False


def update_rev_in_file(config_path: Path, repo_url: str, new_rev: str) -> bool:
    """Update the rev for a given repo URL in .pre-commit-config.yaml.

    Uses text manipulation to preserve formatting and comments.
    Returns True if a change was made.
    """
    content = config_path.read_text()
    lines = content.splitlines(keepends=True)
    in_target_repo = False
    changed = False
    new_lines: list[str] = []

    for line in lines:
        # Detect start of the target repo block
        if re.search(r"repo:\s*" + re.escape(repo_url), line):
            in_target_repo = True
            new_lines.append(line)
            continue

        # Detect start of a different repo block (reset flag)
        if in_target_repo and re.match(r"\s*-\s+repo:", line):
            in_target_repo = False

        if in_target_repo and re.match(r"\s+rev:", line):
            old_line = line
            new_line = re.sub(r"(rev:\s*).*", rf"\g<1>{new_rev}", line)
            if new_line != old_line:
                changed = True
            new_lines.append(new_line)
            in_target_repo = False  # rev only appears once per block
            continue

        new_lines.append(line)

    if changed:
        config_path.write_text("".join(new_lines))
    return changed


def add_bump_library_hook(config_path: Path) -> None:
    """Prepend the bump-library-version local hook block after the repos: key."""
    content = config_path.read_text()
    lines = content.splitlines(keepends=True)
    new_lines: list[str] = []
    inserted = False
    for line in lines:
        new_lines.append(line)
        # Insert the hook block right after the first hook entry in repos:
        # Strategy: insert before the first "  - repo:" line (after repos:)
        if not inserted and re.match(r"^repos:", line):
            new_lines.append(_BUMP_HOOK_BLOCK)
            inserted = True
    config_path.write_text("".join(new_lines))


def run_precommit_install(repo_path: Path) -> bool:
    """Install the git pre-commit hook in the repo. Returns True on success.

    prek is the canonical workspace runner (migrated from pre-commit 2026-06-03); fall
    back to `pre-commit install` only where prek is not yet on PATH.
    """
    for runner in ("prek", "pre-commit"):
        if shutil.which(runner) is None:
            continue
        result = subprocess.run(
            [runner, "install"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate pre-commit hook revisions across all repos.")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply fixes: update revs, add bump hook, run pre-commit install.",
    )
    args = parser.parse_args()
    apply_fixes: bool = cast(bool, args.apply)

    if not MANIFEST_PATH.is_file():
        print(f"ERROR: Manifest not found: {MANIFEST_PATH}", file=sys.stderr)
        return 1

    manifest = load_json(MANIFEST_PATH)
    repos_raw = _jdict(manifest.get("repositories")) or {}

    constraints = load_constraints(CONSTRAINTS_PATH)
    canonical_ruff_rev = extract_canonical_ruff_version(constraints)
    if canonical_ruff_rev is None:
        print(
            "ERROR: Could not determine canonical ruff version from workspace-constraints.toml",
            file=sys.stderr,
        )
        return 1

    issues: list[str] = []
    fixes_applied = 0

    for repo_name in sorted(repos_raw):
        repo_type = get_repo_type(manifest, repo_name)
        repo_path = get_repo_path(manifest, repo_name)

        if not repo_path.is_dir():
            continue

        config_path = repo_path / ".pre-commit-config.yaml"
        repos_list = load_precommit_config(repo_path)

        if repos_list is None:
            # No .pre-commit-config.yaml — skip (not every repo may have one)
            continue

        # --- Check ruff rev ---
        ruff_entry = find_repo_entry(repos_list, _RUFF_REPO)
        if ruff_entry is not None:
            actual_ruff_rev = _jstr(ruff_entry.get("rev"))
            if actual_ruff_rev != canonical_ruff_rev:
                msg = f"RUFF_REV:  {repo_name}  actual={actual_ruff_rev!r}  canonical={canonical_ruff_rev!r}"
                if apply_fixes:
                    changed = update_rev_in_file(config_path, _RUFF_REPO, canonical_ruff_rev)
                    if changed:
                        print(f"  fixed ruff rev in {repo_name}: {actual_ruff_rev} -> {canonical_ruff_rev}")
                        fixes_applied += 1
                    else:
                        issues.append(msg + "  (fix attempted but no change made)")
                else:
                    issues.append(msg)

        # --- Check pre-commit-hooks rev ---
        hooks_entry = find_repo_entry(repos_list, _PRECOMMIT_HOOKS_REPO)
        if hooks_entry is not None:
            actual_hooks_rev = _jstr(hooks_entry.get("rev"))
            if actual_hooks_rev != CANONICAL_PRECOMMIT_HOOKS_REV:
                msg = (
                    f"HOOKS_REV: {repo_name}  actual={actual_hooks_rev!r}  canonical={CANONICAL_PRECOMMIT_HOOKS_REV!r}"
                )
                if apply_fixes:
                    changed = update_rev_in_file(config_path, _PRECOMMIT_HOOKS_REPO, CANONICAL_PRECOMMIT_HOOKS_REV)
                    if changed:
                        print(
                            f"  fixed pre-commit-hooks rev in {repo_name}: "
                            f"{actual_hooks_rev} -> {CANONICAL_PRECOMMIT_HOOKS_REV}"
                        )
                        fixes_applied += 1
                    else:
                        issues.append(msg + "  (fix attempted but no change made)")
                else:
                    issues.append(msg)

        # --- Check bump-library-version hook (library repos only) ---
        if repo_type == "library" and not has_bump_library_hook(repos_list):
            msg = f"NO_BUMP_HOOK: {repo_name}  (library repo missing bump-library-version hook)"
            if apply_fixes:
                add_bump_library_hook(config_path)
                print(f"  added bump-library-version hook to {repo_name}")
                fixes_applied += 1
            else:
                issues.append(msg)

        # --- Check .git/hooks/pre-commit exists ---
        git_hook = repo_path / ".git" / "hooks" / "pre-commit"
        if not git_hook.exists():
            msg = f"HOOK_NOT_INSTALLED: {repo_name}  (.git/hooks/pre-commit missing)"
            if apply_fixes:
                success = run_precommit_install(repo_path)
                if success:
                    print(f"  ran pre-commit install in {repo_name}")
                    fixes_applied += 1
                else:
                    issues.append(msg + "  (pre-commit install failed)")
            else:
                issues.append(msg)

    if not issues and fixes_applied == 0:
        print(f"OK: All pre-commit configs aligned (ruff={canonical_ruff_rev}, hooks={CANONICAL_PRECOMMIT_HOOKS_REV}).")
        return 0

    if apply_fixes:
        if issues:
            print(f"\n{len(issues)} issue(s) could not be auto-fixed:", file=sys.stderr)
            for issue in issues:
                print(f"  {issue}", file=sys.stderr)
            return 1
        print(f"\nApplied {fixes_applied} fix(es).")
        return 0

    for issue in issues:
        print(issue)
    print(
        f"\n{len(issues)} pre-commit issue(s) found.  Re-run with --apply to fix.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
