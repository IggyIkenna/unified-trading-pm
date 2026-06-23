#!/usr/bin/env python3
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""
rollout-quality-gates-ci-workflows.py

Propagates CI/CD fixes to all repos' quality-gates.yml.

Default mode — patches existing workflow in-place:
  1. `export PATH="$(pwd)/.venv/bin:$PATH"` in the "Run quality gates" run block
  2. `CLOUD_MOCK_MODE: "true"` in the "Run quality gates" env block
  3. `--no-fix` flag on the `bash scripts/quality-gates.sh` invocation
  4. Composite action ref pinned to active_feature_branch from workspace-manifest.json

--workflow-call mode — replaces the entire file with a minimal workflow_call
  thin caller that delegates all steps to the reusable workflows in PM:
    python-quality-gates.yml  (Python service/api/library repos)
    ui-quality-gates.yml      (UI repos, type=ui)
  dep_repos is populated from manifest transitive dependencies (walked from dependencies[]).
  Transitive deps are required for path deps (e.g. unified-api-contracts via unified-internal-contracts).
  The branch ref in uses: is the same active_feature_branch so the reusable
  workflow definition is loaded from the current feature branch.

Usage:
    python rollout-quality-gates-ci-workflows.py [--dry-run] [--repo REPO_NAME]
                                                  [--action-ref REF] [--workflow-call]

Options:
    --dry-run         Print what would change without writing any files.
    --repo            Process a single repo by name.
    --action-ref      Override the ref (default: active_feature_branch from manifest).
    --workflow-call   Replace workflows with workflow_call thin callers.
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

# UI repos use vitest/playwright but still call scripts/quality-gates.sh for
# linting/type checks — they need the same CI env vars as Python service repos.
SKIP_STACKS: set[str] = set()

# Repos with non-standard quality-gates.yml that we should not touch
SKIP_REPOS = {
    "unified-trading-pm",  # Uses working-directory + source .venv/bin/activate (special PM structure)
    "unified-trading-codex",  # Has no "Run quality gates" step — custom bash/python syntax checks
}

ACTION_USES_RE = re.compile(r"(uses:\s+IggyIkenna/unified-trading-pm/\.github/actions/[^\s@]+)@(\S+)")

PATH_EXPORT = 'export PATH="$(pwd)/.venv/bin:$PATH"'
CLOUD_MOCK_ENV_KEY = "CLOUD_MOCK_MODE"
CLOUD_MOCK_ENV_VAL = '"true"'
CLOUD_PROVIDER_KEY = "CLOUD_PROVIDER"
CLOUD_PROVIDER_VAL = '"local"'
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
    """Add CLOUD_MOCK_MODE, CLOUD_PROVIDER to the step env block if not present."""
    changed = False

    # Look for existing `env:` block inside the step
    env_block_re = re.compile(r"(^( +)env:\n)", re.MULTILINE)
    m = env_block_re.search(step_text)

    if m:
        # env block already exists — insert missing keys after `env:`
        indent = m.group(2)
        inner_indent = indent + "  "
        insert_pos = m.end()
        additions = ""
        if CLOUD_MOCK_ENV_KEY not in step_text:
            additions += inner_indent + f"{CLOUD_MOCK_ENV_KEY}: {CLOUD_MOCK_ENV_VAL}\n"
        if CLOUD_PROVIDER_KEY not in step_text:
            additions += inner_indent + f"{CLOUD_PROVIDER_KEY}: {CLOUD_PROVIDER_VAL}\n"
        if additions:
            step_text = step_text[:insert_pos] + additions + step_text[insert_pos:]
            changed = True
    elif CLOUD_MOCK_ENV_KEY not in step_text:
        # No env block — insert one before `run:`
        run_line = re.compile(r"(^( +)run:)", re.MULTILINE)
        m2 = run_line.search(step_text)
        if m2:
            indent = m2.group(2)
            inner_indent = indent + "  "
            insert_pos = m2.start()
            env_block_text = (
                f"{indent}env:\n"
                f"{inner_indent}{CLOUD_MOCK_ENV_KEY}: {CLOUD_MOCK_ENV_VAL}\n"
                f"{inner_indent}{CLOUD_PROVIDER_KEY}: {CLOUD_PROVIDER_VAL}\n"
                f'{inner_indent}GCP_PROJECT_ID: "test-project"\n'
            )
            step_text = step_text[:insert_pos] + env_block_text + step_text[insert_pos:]
            changed = True

    return step_text, changed


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


ON_BLOCK_RE = re.compile(r"^on:\n(?:[ \t]+.*\n)*", re.MULTILINE)

UI_TYPE = "ui"
WORKFLOW_CALL_PYTHON = "python-quality-gates.yml"
WORKFLOW_CALL_UI = "ui-quality-gates.yml"


def _extract_on_block(content: str) -> str:
    """Return the raw `on:` YAML block from a workflow, or a sensible default."""
    m = ON_BLOCK_RE.search(content)
    return m.group(0).rstrip() if m else "on:\n  pull_request:\n    branches: [main]\n  push:\n    branches: [main]"


def _transitive_dep_names(repo_name: str, repos: dict[str, dict[str, object]]) -> set[str]:
    """Return transitive dependency names for a repo.

    CI clone needs all transitive path deps (e.g. unified-api-contracts via unified-internal-contracts).
    """
    seen: set[str] = set()

    def walk(name: str) -> None:
        if name in seen:
            return
        seen.add(name)
        info = repos.get(name, {})
        deps_list: list[object] = cast(list[object], info.get("dependencies") or [])
        for d in deps_list:
            dep_name = d["name"] if isinstance(d, dict) else str(d)  # type: ignore[index]
            if dep_name != "unified-trading-pm":
                walk(dep_name)

    walk(repo_name)
    seen.discard(repo_name)
    return seen


def _dep_repos_for(repo_name: str, repo_info: dict[str, object], repos: dict[str, dict[str, object]]) -> str:
    """Return space-separated transitive dep repo names for CI clone step."""
    names = _transitive_dep_names(repo_name, repos)
    return " ".join(sorted(names))


def generate_workflow_call_yaml(
    repo_name: str,
    repo_info: dict[str, object],
    repos: dict[str, dict[str, object]],
    existing_content: str,
    action_ref: str,
) -> str:
    """Generate a minimal workflow_call thin caller for this repo."""
    is_ui = cast(str, repo_info.get("type") or "") == UI_TYPE
    on_block = _extract_on_block(existing_content)
    reusable = WORKFLOW_CALL_UI if is_ui else WORKFLOW_CALL_PYTHON
    uses_line = f"uses: IggyIkenna/unified-trading-pm/.github/workflows/{reusable}@{action_ref}"

    if is_ui:
        with_block = '      node-version: "22"'
    else:
        dep_repos = _dep_repos_for(repo_name, repo_info, repos)
        with_block = f'      dep_repos: "{dep_repos}"' if dep_repos else '      dep_repos: ""'

    return (
        f"name: Quality Gates\n\n"
        f"{on_block}\n\n"
        f"jobs:\n"
        f"  quality-gates:\n"
        f"    {uses_line}\n"
        f"    with:\n"
        f"{with_block}\n"
        f"    secrets:\n"
        f"      GH_PAT: ${{{{ secrets.GH_PAT }}}}\n"
        f"      GCP_PROJECT_ID: ${{{{ secrets.GCP_PROJECT_ID }}}}\n"
    )


def _ensure_action_ref(content: str, target_ref: str) -> tuple[str, bool]:
    """Replace any composite action @<ref> with @target_ref throughout the file."""
    new_content, count = ACTION_USES_RE.subn(
        lambda m: f"{m.group(1)}@{target_ref}" if m.group(2) != target_ref else m.group(0),
        content,
    )
    return new_content, count > 0


def fix_workflow(content: str, action_ref: str = "main") -> tuple[str, list[str]]:
    """Apply all three fixes to the workflow content. Return (new_content, changes)."""
    changes: list[str] = []

    # Fix 1: composite action ref (file-level, not step-scoped)
    content, changed = _ensure_action_ref(content, action_ref)
    if changed:
        changes.append(f"pinned composite action ref to @{action_ref}")

    # Fixes 2-4: scoped to "Run quality gates" step
    span = _find_step_span(content, "Run quality gates")
    if span is None:
        return content, changes

    start, end = span
    step_text = content[start:end]

    step_text, changed = _ensure_cloud_mock_env(step_text)
    if changed:
        changes.append("added CLOUD_MOCK_MODE/CLOUD_PROVIDER env vars")

    step_text, changed = _ensure_path_export(step_text)
    if changed:
        changes.append("added PATH export")

    step_text, changed = _ensure_no_fix_flag(step_text)
    if changed:
        changes.append("added --no-fix flag")

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
    action_ref: str
    workflow_call: bool


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", dest="dry_run", help="Show changes without writing files")
    parser.add_argument("--repo", default="", help="Process a single repo by name")
    parser.add_argument(
        "--action-ref",
        default="",
        dest="action_ref",
        help="Composite action ref to pin (default: active_feature_branch from manifest)",
    )
    parser.add_argument(
        "--workflow-call",
        action="store_true",
        dest="workflow_call",
        help="Replace workflows with minimal workflow_call thin callers",
    )
    args = parser.parse_args(namespace=_ParsedArgs())

    dry_run: bool = args.dry_run
    target_repo: str = args.repo

    if dry_run:
        print("DRY RUN mode — no files will be written\n")

    # Load manifest
    with MANIFEST_PATH.open() as f:
        manifest: dict[str, object] = cast(dict[str, object], json.load(f))
    all_repos: dict[str, dict[str, object]] = cast(dict[str, dict[str, object]], manifest.get("repositories") or {})
    repos = dict(all_repos)

    # Resolve action ref: CLI arg > manifest active_feature_branch > "main"
    action_ref: str = args.action_ref or cast(str, manifest.get("active_feature_branch") or "") or "main"
    print(f"Composite action ref: @{action_ref}")

    # If single-repo mode, restrict list (all_repos kept for transitive dep walk)
    if target_repo:
        if target_repo not in all_repos:
            print(f"ERROR: repo '{target_repo}' not found in manifest", file=sys.stderr)
            sys.exit(1)
        repos = {target_repo: all_repos[target_repo]}

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

        if args.workflow_call:
            # Generate a brand-new minimal workflow_call thin caller
            new_content = generate_workflow_call_yaml(repo_name, repo_info, all_repos, content, action_ref)
            if new_content == content:
                print(f"OK    {repo_name} (already workflow_call thin caller)")
                stats["already_ok"] += 1
                continue
            changes_str = "replaced with workflow_call thin caller"
        else:
            # Quick pre-check: does step exist?
            if "Run quality gates" not in content:
                print(f"SKIP  {repo_name} (no 'Run quality gates' step — special workflow)")
                stats["skipped"] += 1
                continue

            new_content, changes = fix_workflow(content, action_ref)
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
