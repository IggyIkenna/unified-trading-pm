#!/usr/bin/env python3
"""
rollout-quality-gates-ci-workflows.py

Propagates three CI/CD fixes to all Python-stack repos' quality-gates.yml:

  1. `export PATH="$(pwd)/.venv/bin:$PATH"` in the "Run quality gates" run block
  2. `CLOUD_MOCK_MODE: "true"` in the "Run quality gates" env block
  3. `--no-fix` flag on the `bash scripts/quality-gates.sh` invocation

Repos that are UI-only (stack: ui) are skipped — they use npm/vitest, not
Python quality-gates.sh. Repos without a quality-gates.yml are reported as
MISSING. Repos that already have all three fixes are reported as SKIP.

Usage:
    python rollout-quality-gates-ci-workflows.py [--dry-run] [--repo REPO_NAME]

Options:
    --dry-run    Print what would change without writing any files.
    --repo       Process a single repo by name.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import cast

# ── Constants ─────────────────────────────────────────────────────────────────

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
MANIFEST_PATH = WORKSPACE_ROOT / "unified-trading-pm" / "workspace-manifest.json"

# Stacks that are pure TypeScript/UI — no Python quality-gates.sh
SKIP_STACKS = {"ui"}

# Repos with non-standard quality-gates.yml that we should not touch
SKIP_REPOS = {
    "unified-trading-pm",  # Uses working-directory + source .venv/bin/activate (special PM structure)
    "unified-trading-codex",  # Has no "Run quality gates" step — custom bash/python syntax checks
}

PATH_EXPORT = 'export PATH="$(pwd)/.venv/bin:$PATH"'
CLOUD_MOCK_ENV_KEY = "CLOUD_MOCK_MODE"
CLOUD_MOCK_ENV_VAL = '"true"'
NO_FIX_FLAG = "--no-fix"

# ── YAML-aware helpers (text-based — preserves comments and formatting) ───────


def _find_step_span(content: str, step_name: str) -> tuple[int, int] | None:
    """Return (start, end) byte offsets of a named step in the YAML text.

    Locates `- name: <step_name>` and returns the span from that line up to
    (but not including) the next `      - name:` at the same indentation or
    end of file.
    """
    # Match the step header line
    pattern = re.compile(
        r"^( {6,8})- name: " + re.escape(step_name) + r"\s*$",
        re.MULTILINE,
    )
    m = pattern.search(content)
    if not m:
        return None

    step_indent = len(m.group(1))
    start = m.start()

    # Find next sibling step (same indentation `- name:`) after this one
    next_step = re.compile(
        r"^" + " " * step_indent + r"- name:",
        re.MULTILINE,
    )
    nxt = next_step.search(content, m.end())
    end = nxt.start() if nxt else len(content)
    return start, end


def _ensure_path_export(step_text: str) -> tuple[str, bool]:
    """Prepend `export PATH=...` to the run block if not present."""
    if PATH_EXPORT in step_text:
        return step_text, False

    # Find `run: |` or `run: bash ...` line
    run_block = re.compile(r"(^( +)run: \|\n)", re.MULTILINE)
    m = run_block.search(step_text)
    if m:
        # Multiline run block — insert after `run: |`
        inner_indent = m.group(2) + "  "
        insert_pos = m.end()
        new_text = step_text[:insert_pos] + inner_indent + PATH_EXPORT + "\n" + step_text[insert_pos:]
        return new_text, True

    # Single-line `run: bash scripts/...`
    single_run = re.compile(r"(^( +)run: (bash .+)$)", re.MULTILINE)
    m = single_run.search(step_text)
    if m:
        indent = m.group(2)
        original_cmd = m.group(3)
        replacement = f"{indent}run: |\n{indent}  {PATH_EXPORT}\n{indent}  {original_cmd}"
        new_text = step_text[: m.start()] + replacement + step_text[m.end() :]
        return new_text, True

    return step_text, False


def _ensure_cloud_mock_env(step_text: str) -> tuple[str, bool]:
    """Add CLOUD_MOCK_MODE: "true" to the step env block if not present."""
    if CLOUD_MOCK_ENV_KEY in step_text:
        return step_text, False

    # Look for existing `env:` block inside the step
    env_block = re.compile(r"(^( +)env:\n)", re.MULTILINE)
    m = env_block.search(step_text)
    if m:
        indent = m.group(2)
        inner_indent = indent + "  "
        insert_pos = m.end()
        new_text = (
            step_text[:insert_pos]
            + inner_indent
            + f"{CLOUD_MOCK_ENV_KEY}: {CLOUD_MOCK_ENV_VAL}\n"
            + step_text[insert_pos:]
        )
        return new_text, True

    # No env block — insert one before `run:`
    run_line = re.compile(r"(^( +)run:)", re.MULTILINE)
    m = run_line.search(step_text)
    if m:
        indent = m.group(2)
        inner_indent = indent + "  "
        insert_pos = m.start()
        env_block_text = (
            f"{indent}env:\n"
            f"{inner_indent}{CLOUD_MOCK_ENV_KEY}: {CLOUD_MOCK_ENV_VAL}\n"
            f'{inner_indent}GCP_PROJECT_ID: "test-project"\n'
        )
        new_text = step_text[:insert_pos] + env_block_text + step_text[insert_pos:]
        return new_text, True

    return step_text, False


def _ensure_no_fix_flag(step_text: str) -> tuple[str, bool]:
    """Add --no-fix to the quality-gates.sh invocation if not present."""
    if NO_FIX_FLAG in step_text:
        return step_text, False

    # Match `bash scripts/quality-gates.sh` line with optional existing flags
    pattern = re.compile(r"(bash scripts/quality-gates\.sh)( --[^\n]*)?")
    m = pattern.search(step_text)
    if m:
        existing_flags = m.group(2) or ""
        replacement = f"{m.group(1)} {NO_FIX_FLAG}{existing_flags}"
        new_text = step_text[: m.start()] + replacement + step_text[m.end() :]
        return new_text, True

    return step_text, False


def fix_workflow(content: str) -> tuple[str, list[str]]:
    """Apply all three fixes to the workflow content. Return (new_content, changes)."""
    span = _find_step_span(content, "Run quality gates")
    if span is None:
        return content, []

    start, end = span
    step_text = content[start:end]
    changes: list[str] = []

    step_text, changed = _ensure_cloud_mock_env(step_text)
    if changed:
        changes.append("added CLOUD_MOCK_MODE env var")

    step_text, changed = _ensure_path_export(step_text)
    if changed:
        changes.append("added PATH export")

    step_text, changed = _ensure_no_fix_flag(step_text)
    if changed:
        changes.append("added --no-fix flag")

    if not changes:
        return content, []

    new_content = content[:start] + step_text + content[end:]
    return new_content, changes


def validate_yaml(path: Path) -> bool:
    """Return True if the file parses as valid YAML."""
    try:
        import yaml  # type: ignore[import-untyped]

        with path.open() as f:
            yaml.safe_load(f)
        return True
    except Exception as exc:
        print(f"  YAML VALIDATION FAILED: {exc}", file=sys.stderr)
        return False


# ── Main ──────────────────────────────────────────────────────────────────────


class _ParsedArgs(argparse.Namespace):
    dry_run: bool
    repo: str


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", dest="dry_run", help="Show changes without writing files")
    parser.add_argument("--repo", default="", help="Process a single repo by name")
    args = parser.parse_args(namespace=_ParsedArgs())

    dry_run: bool = args.dry_run
    target_repo: str = args.repo

    if dry_run:
        print("DRY RUN mode — no files will be written\n")

    # Load manifest
    with MANIFEST_PATH.open() as f:
        manifest: dict[str, object] = cast(dict[str, object], json.load(f))
    repos: dict[str, dict[str, object]] = cast(dict[str, dict[str, object]], manifest.get("repositories") or {})

    # If single-repo mode, restrict list
    if target_repo:
        if target_repo not in repos:
            print(f"ERROR: repo '{target_repo}' not found in manifest", file=sys.stderr)
            sys.exit(1)
        repos = {target_repo: repos[target_repo]}

    stats = {"fixed": 0, "skipped": 0, "missing": 0, "already_ok": 0, "error": 0}
    fixed_repos: list[str] = []

    for repo_name, repo_info in sorted(repos.items()):
        stack: str = cast(str, repo_info.get("stack") or repo_info.get("type") or "")

        # Skip pure UI repos
        if stack in SKIP_STACKS:
            print(f"SKIP  {repo_name} (stack={stack}, UI-only)")
            stats["skipped"] += 1
            continue

        # Skip special-case repos
        if repo_name in SKIP_REPOS:
            print(f"SKIP  {repo_name} (manually excluded — non-standard workflow)")
            stats["skipped"] += 1
            continue

        workflow_path = WORKSPACE_ROOT / repo_name / ".github" / "workflows" / "quality-gates.yml"

        if not workflow_path.exists():
            print(f"MISS  {repo_name} (no quality-gates.yml found)")
            stats["missing"] += 1
            continue

        content = workflow_path.read_text()

        # Quick pre-check: does step exist?
        if "Run quality gates" not in content:
            print(f"SKIP  {repo_name} (no 'Run quality gates' step — special workflow)")
            stats["skipped"] += 1
            continue

        new_content, changes = fix_workflow(content)

        if not changes:
            print(f"OK    {repo_name} (all fixes already present)")
            stats["already_ok"] += 1
            continue

        changes_str = ", ".join(changes)
        if dry_run:
            print(f"WOULD FIX  {repo_name}: {changes_str}")
            stats["fixed"] += 1
            fixed_repos.append(repo_name)
            continue

        # Write the fixed content
        workflow_path.write_text(new_content)

        # Validate YAML
        if not validate_yaml(workflow_path):
            print(f"ERROR {repo_name}: YAML invalid after fix — reverting", file=sys.stderr)
            workflow_path.write_text(content)  # revert
            stats["error"] += 1
            continue

        print(f"FIXED {repo_name}: {changes_str}")
        stats["fixed"] += 1
        fixed_repos.append(repo_name)

    # Summary
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Fixed:      {stats['fixed']}")
    print(f"  Already OK: {stats['already_ok']}")
    print(f"  Skipped:    {stats['skipped']}")
    print(f"  Missing:    {stats['missing']}")
    print(f"  Errors:     {stats['error']}")
    print()
    if fixed_repos:
        print("Repos that were fixed:")
        for r in fixed_repos:
            print(f"  {r}")


if __name__ == "__main__":
    main()
