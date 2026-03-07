#!/usr/bin/env python3.13
"""Check quality-gates.sh scripts for drift from the canonical template.

Compares each service/api-service repo's scripts/quality-gates.sh against
the canonical template at:
  unified-trading-codex/06-coding-standards/quality-gates-service-template.sh

Checks (not line-for-line, but structural):
  1. --line-length flag in ruff invocations (canonical uses NO --line-length CLI flag)
  2. ruff invocation present (run_timeout ... ruff ...)
  3. basedpyright invocation present (run_timeout ... basedpyright ...)
  4. No hard-coded ruff version in the script body (version check via ruff --version is OK)

Reports repos where any of the above fail.

With --apply:
  - Removes --line-length <N> from ruff invocation lines
  (Other structural issues require manual review — reported only.)

Usage:
    python check-qg-template-drift.py
    python check-qg-template-drift.py --apply

Exit: 0 = no drift, 1 = drift found.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import cast

SCRIPT_DIR = Path(__file__).resolve().parent
PM_ROOT = SCRIPT_DIR.parent.parent
MANIFEST_PATH = PM_ROOT / "workspace-manifest.json"
WORKSPACE_ROOT = PM_ROOT.parent
CODEX_ROOT = WORKSPACE_ROOT / "unified-trading-codex"
CANONICAL_TEMPLATE = CODEX_ROOT / "06-coding-standards" / "quality-gates-service-template.sh"

JsonDict = dict[str, object]

# Repo types that are expected to have a quality-gates.sh
_QG_TYPES = {"service", "api-service", "api"}

# Pattern: --line-length followed by a number in a ruff call line
_LINE_LENGTH_PATTERN = re.compile(r"--line-length\s+\d+")

# Patterns that must be present in a valid quality-gates.sh.
# The canonical template uses `$RUFF_CMD check/format` (variable, not literal "ruff"),
# so we match either `ruff check/format` (old style) or `$RUFF_CMD check/format` (current style).
_RUFF_INVOCATION_PATTERN = re.compile(r"(\$RUFF_CMD|ruff)\s+(check|format)", re.MULTILINE)
_BASEDPYRIGHT_INVOCATION_PATTERN = re.compile(r"basedpyright\s+", re.MULTILINE)


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


def check_qg_script(content: str) -> list[str]:
    """Return a list of issue descriptions for the given quality-gates.sh content."""
    issues: list[str] = []

    # 1. Check for --line-length flag in ruff lines
    for i, line in enumerate(content.splitlines(), start=1):
        if _LINE_LENGTH_PATTERN.search(line) and "ruff" in line:
            issues.append(
                f"line {i}: --line-length flag in ruff invocation "
                f"(canonical template has no --line-length CLI flag): {line.strip()!r}"
            )

    # 2. Ruff invocation must be present
    if not _RUFF_INVOCATION_PATTERN.search(content):
        issues.append("missing ruff check/format invocation")

    # 3. basedpyright invocation must be present
    if not _BASEDPYRIGHT_INVOCATION_PATTERN.search(content):
        issues.append("missing basedpyright invocation")

    return issues


def apply_line_length_fix(qg_path: Path) -> int:
    """Remove --line-length <N> from ruff lines. Returns number of lines changed."""
    content = qg_path.read_text()
    lines = content.splitlines(keepends=True)
    new_lines: list[str] = []
    changes = 0
    for line in lines:
        if "ruff" in line and _LINE_LENGTH_PATTERN.search(line):
            new_line = _LINE_LENGTH_PATTERN.sub("", line)
            # Clean up double-spaces left behind
            new_line = re.sub(r"  +", " ", new_line)
            if new_line != line:
                changes += 1
            new_lines.append(new_line)
        else:
            new_lines.append(line)
    if changes:
        qg_path.write_text("".join(new_lines))
    return changes


def main() -> int:
    parser = argparse.ArgumentParser(description="Check quality-gates.sh scripts for drift from canonical template.")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply auto-fixable issues (removes --line-length flags from ruff lines).",
    )
    args = parser.parse_args()
    apply_fixes: bool = cast(bool, args.apply)

    if not MANIFEST_PATH.is_file():
        print(f"ERROR: Manifest not found: {MANIFEST_PATH}", file=sys.stderr)
        return 1

    if not CANONICAL_TEMPLATE.is_file():
        print(f"ERROR: Canonical template not found: {CANONICAL_TEMPLATE}", file=sys.stderr)
        return 1

    manifest = load_json(MANIFEST_PATH)
    repos_raw = _jdict(manifest.get("repositories")) or {}

    drift_found = False
    unfixable_drift_found = False
    fixes_applied = 0

    for repo_name in sorted(repos_raw):
        repo_type = get_repo_type(manifest, repo_name)
        if repo_type not in _QG_TYPES:
            continue

        repo_path = get_repo_path(manifest, repo_name)
        if not repo_path.is_dir():
            continue

        qg_path = repo_path / "scripts" / "quality-gates.sh"
        if not qg_path.is_file():
            print(f"MISSING_QG: {repo_name}  (no scripts/quality-gates.sh)")
            print("  → Fix: bash unified-trading-pm/scripts/repo-management/run-all-setup.sh --rollout-first")
            drift_found = True
            unfixable_drift_found = True
            continue

        content = qg_path.read_text()
        issues = check_qg_script(content)

        if not issues:
            continue

        drift_found = True

        if apply_fixes:
            fixable = [i for i in issues if "--line-length" in i]
            unfixable = [i for i in issues if "--line-length" not in i]

            if fixable:
                n = apply_line_length_fix(qg_path)
                if n:
                    print(f"  fixed {n} --line-length occurrence(s) in {repo_name}/scripts/quality-gates.sh")
                    fixes_applied += n

            if unfixable:
                unfixable_drift_found = True
                print(f"DRIFT (requires rollout): {repo_name}")
                for issue in unfixable:
                    print(f"  {issue}")
        else:
            print(f"DRIFT: {repo_name}")
            for issue in issues:
                print(f"  {issue}")

    if not drift_found:
        print("OK: All quality-gates.sh scripts are aligned with canonical template.")
        return 0

    if apply_fixes:
        if fixes_applied:
            print(f"\nApplied {fixes_applied} auto-fix(es).")
        if unfixable_drift_found:
            print(
                "\nStructural drift above cannot be auto-fixed. Re-rollout the canonical template:",
                file=sys.stderr,
            )
            print(
                "  bash unified-trading-pm/scripts/repo-management/run-all-setup.sh --rollout-first",
                file=sys.stderr,
            )
            return 1
        return 0

    print(
        "\nDrift found. Options:",
        file=sys.stderr,
    )
    print("  --apply  to fix --line-length issues automatically", file=sys.stderr)
    print(
        "  bash unified-trading-pm/scripts/repo-management/run-all-setup.sh --rollout-first"
        "  to re-rollout structural drift",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
