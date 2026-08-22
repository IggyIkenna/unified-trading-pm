#!/usr/bin/env python3.13
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""
Roll out Prettier to all repositories via pre-commit hooks.

Reads workspace-manifest.json from workspace root, iterates over repositories,
and for each repo with .pre-commit-config.yaml:
- Skips if mirrors-prettier already present (idempotent)
- Inserts SSOT Prettier block after ruff block if ruff exists
- Inserts Prettier block as first repos entry if no ruff block

For repos without .pre-commit-config.yaml: creates minimal config with Prettier
and basic hooks when --create-if-missing is set.

Usage:
    python3 scripts/propagation/rollout-prettier-unified.py [--dry-run] [--repo NAME] [--create-if-missing]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import cast

type JsonDict = dict[str, object]


def _jdict(val: object) -> JsonDict | None:
    if isinstance(val, dict):
        return cast(JsonDict, val)
    return None


def _jstr(val: object, default: str = "") -> str:
    return str(val) if val is not None else default


# Paths relative to script location
SCRIPT_DIR = Path(__file__).resolve().parent
PM_ROOT = SCRIPT_DIR.parent.parent
WORKSPACE_ROOT = PM_ROOT.parent
MANIFEST_PATH = WORKSPACE_ROOT / "unified-trading-pm" / "workspace-manifest.json"

# SSOT Prettier block (from add-prettier-to-pre-commit-hooks.md)
PRETTIER_BLOCK = """
  # Prettier - TypeScript/JSON/Markdown formatter
  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v4.0.0-alpha.8
    hooks:
      - id: prettier
        name: Format with Prettier
        types_or: [ts, tsx, javascript, jsx, json, markdown, yaml]
        additional_dependencies:
          - prettier@3.6.2
"""

# Minimal pre-commit config for repos without one (Prettier + basic hooks)
MINIMAL_PRECOMMIT_TEMPLATE = """# Pre-commit hooks - auto-format on commit
# Setup: pip install prek && prek install

repos:
  # Prettier - TypeScript/JSON/Markdown formatter
  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v4.0.0-alpha.8
    hooks:
      - id: prettier
        name: Format with Prettier
        types_or: [ts, tsx, javascript, jsx, json, markdown, yaml]
        additional_dependencies:
          - prettier@3.6.2

  # Basic file checks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v6.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-toml
      - id: check-added-large-files
        args: ["--maxkb=1000"]
"""

SKIP_STATUSES = frozenset({"deprecated", "archived", "deleted"})


def has_prettier(content: str) -> bool:
    """Return True if mirrors-prettier is already in the config."""
    return "mirrors-prettier" in content


def has_ruff(content: str) -> bool:
    """Return True if ruff-pre-commit block exists."""
    return "astral-sh/ruff-pre-commit" in content or "ruff-pre-commit" in content


def find_insert_position(content: str) -> int:
    """
    Find the line index where to insert the Prettier block.
    Returns index of the line to insert BEFORE (so insert at start of that line).
    """
    lines = content.split("\n")
    if has_ruff(content):
        # Insert after ruff block: find next "- repo:" at top-level after ruff
        in_ruff = False
        for i, line in enumerate(lines):
            if "ruff-pre-commit" in line:
                in_ruff = True
            elif (in_ruff and re.match(r"^\s{0,2}- repo:", line)) or (
                in_ruff and line.strip() and not line.startswith((" ", "\t"))
            ):
                return i
        return len(lines)
    # No ruff: insert as first repos entry (before first "- repo:")
    for i, line in enumerate(lines):
        if re.match(r"^\s*- repo:", line):
            return i
    return 0


def insert_prettier_block(content: str) -> str:
    """Insert Prettier block at the correct position. Idempotent guard is caller's job."""
    if has_prettier(content):
        return content
    pos = find_insert_position(content)
    lines = content.split("\n")
    block_lines = PRETTIER_BLOCK.strip().split("\n")
    new_lines = [*lines[:pos], "", *block_lines, "", *lines[pos:]]
    return "\n".join(new_lines)


def process_repo(
    repo_name: str,
    repo_info: JsonDict,
    workspace_root: Path,
    dry_run: bool,
    create_if_missing: bool,
) -> bool:
    """Process a single repository. Returns True on success."""
    status = repo_info.get("status", "active")
    if status in SKIP_STATUSES:
        print(f"\n⏭️ Skipping {repo_name} (status={status})")
        return True

    repo_path = workspace_root / repo_name
    if not repo_path.exists():
        print(f"\n⚠️ {repo_name}: directory not found at {repo_path}")
        return False

    precommit_path = repo_path / ".pre-commit-config.yaml"

    if not precommit_path.exists():
        if create_if_missing:
            if dry_run:
                print(f"\n  [dry-run] Would create {precommit_path} with Prettier + basic hooks")
            else:
                precommit_path.write_text(MINIMAL_PRECOMMIT_TEMPLATE)
                print(f"\n✅ {repo_name}: Created .pre-commit-config.yaml with Prettier")
            return True
        print(f"\n⏭️ Skipping {repo_name}: no .pre-commit-config.yaml (use --create-if-missing)")
        return True

    content = precommit_path.read_text()
    if has_prettier(content):
        print(f"\n⏭️ Skipping {repo_name}: already has Prettier")
        return True

    new_content = insert_prettier_block(content)
    if new_content == content:
        print(f"\n⏭️ Skipping {repo_name}: no change (unexpected)")
        return True

    if dry_run:
        print(f"\n  [dry-run] Would add Prettier block to {repo_name}/.pre-commit-config.yaml")
        return True

    precommit_path.write_text(new_content)
    print(f"\n✅ {repo_name}: Added Prettier block to .pre-commit-config.yaml")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Roll out Prettier to pre-commit hooks")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without writing")
    parser.add_argument("--repo", type=str, help="Process only this repository")
    parser.add_argument(
        "--create-if-missing",
        action="store_true",
        help="Create .pre-commit-config.yaml for repos that don't have one",
    )
    args = parser.parse_args()

    if not MANIFEST_PATH.exists():
        print(f"❌ Manifest not found: {MANIFEST_PATH}")
        return 1

    with open(MANIFEST_PATH) as f:
        manifest = cast(JsonDict, json.load(f))

    repos_raw = _jdict(manifest.get("repositories"))
    repositories: dict[str, JsonDict] = cast(dict[str, JsonDict], repos_raw) if repos_raw else {}
    dry_run = cast(bool, args.dry_run)
    create_if_missing = cast(bool, args.create_if_missing)
    repo_filter = cast(str | None, args.repo)
    if repo_filter is not None:
        if repo_filter not in repositories:
            print(f"❌ Repository not in manifest: {repo_filter}")
            return 1
        repositories = {repo_filter: repositories[repo_filter]}

    print("🚀 Rolling out Prettier (unified)")
    print(f"📁 Workspace: {WORKSPACE_ROOT}")
    print(f"📋 Repositories: {len(repositories)}")
    if dry_run:
        print("🔍 Dry run — no files will be written")
    if create_if_missing:
        print("📄 Will create .pre-commit-config.yaml for repos without one")

    success = 0
    errors = 0
    for repo_name in sorted(repositories.keys()):
        try:
            if process_repo(
                repo_name,
                repositories[repo_name],
                WORKSPACE_ROOT,
                dry_run,
                create_if_missing,
            ):
                success += 1
            else:
                errors += 1
        except (OSError, ValueError) as e:
            print(f"  ❌ Error: {e}")
            errors += 1

    print("\n🎉 Rollout complete!")
    print(f"  ✅ Success: {success}")
    print(f"  ❌ Errors: {errors}")

    return 1 if errors > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
