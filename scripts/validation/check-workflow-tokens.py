#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Check GitHub Actions workflows for cross-repo operations using GITHUB_TOKEN.

Cross-repo checkouts and artifact downloads require GH_PAT (a PAT with repo scope)
because GITHUB_TOKEN is scoped to the current repo only. Using GITHUB_TOKEN on a
cross-repo operation returns 404 from the GitHub REST API.

Checks:
  - actions/checkout with `repository:` set to a different repo → must use GH_PAT
  - actions/download-artifact with `repository:` set → must use GH_PAT
  - dawidd6/action-download-artifact with `repo:` set → must use GH_PAT

Usage:
    python3 check-workflow-tokens.py [--dir PATH]   # default: .github/workflows/
    python3 check-workflow-tokens.py --workspace    # all repos in workspace
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import cast


def _find_violations(workflow_file: Path) -> list[str]:
    violations: list[str] = []
    try:
        lines = workflow_file.read_text(encoding="utf-8").splitlines()
    except OSError:
        return violations

    # Simple state machine: track whether we're inside a `with:` block that has
    # a cross-repo `repository:` or `repo:` key, and whether GITHUB_TOKEN is used.
    in_with = False
    with_indent = 0
    has_cross_repo = False
    has_github_token = False
    with_start_line = 0

    for i, raw in enumerate(lines, 1):
        stripped = raw.strip()
        indent = len(raw) - len(raw.lstrip())

        if stripped.startswith("#"):
            continue

        # Detect `with:` block start
        if stripped == "with:":
            # Start tracking new with block
            in_with = True
            with_indent = indent
            has_cross_repo = False
            has_github_token = False
            with_start_line = i
            continue

        if in_with:
            # End of with block when indent returns to with_indent or less
            # (next non-empty, non-comment line at same/lower indent means block ended)
            if stripped and indent <= with_indent and stripped != "with:":
                # Check previous block for violations
                if has_cross_repo and has_github_token:
                    violations.append(
                        f"  Line ~{with_start_line}: cross-repo operation uses GITHUB_TOKEN — replace with GH_PAT"
                    )
                in_with = False
                has_cross_repo = False
                has_github_token = False

                # Could be a new with: block
                if stripped == "with:":
                    in_with = True
                    with_indent = indent
                    with_start_line = i
                continue

            # Inside with block
            if "repository:" in stripped or stripped.startswith("repo:"):
                # Check if it's cross-repo (contains a '/' — org/repo pattern)
                val = stripped.split(":", 1)[1].strip().strip("'\"")
                if "/" in val or "${{" in val:
                    has_cross_repo = True

            if "GITHUB_TOKEN" in stripped and (
                "token:" in stripped or "github-token:" in stripped or "github_token:" in stripped
            ):
                has_github_token = True

    # Handle EOF while still in with block
    if in_with and has_cross_repo and has_github_token:
        violations.append(f"  Line ~{with_start_line}: cross-repo operation uses GITHUB_TOKEN — replace with GH_PAT")

    return violations


def check_dir(workflows_dir: Path) -> int:
    if not workflows_dir.is_dir():
        return 0
    total = 0
    for yml in sorted(workflows_dir.glob("*.yml")):
        violations = _find_violations(yml)
        if violations:
            print(f"\n{yml.relative_to(workflows_dir.parents[1])}:")
            for v in violations:
                print(v)
            total += len(violations)
    return total


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dir", default=".github/workflows", help="Workflows directory to check (default: .github/workflows)"
    )
    parser.add_argument("--workspace", action="store_true", help="Check all repos in the workspace")
    args = parser.parse_args()

    if cast(bool, args.workspace):
        workspace_root = Path(__file__).resolve().parents[3]
        total = 0
        for repo_dir in sorted(workspace_root.iterdir()):
            if not repo_dir.is_dir():
                continue
            if repo_dir.name.startswith(".") or repo_dir.name in ("node_modules", ".venv", ".venv-workspace"):
                continue
            wf_dir = repo_dir / ".github" / "workflows"
            total += check_dir(wf_dir)
        if total:
            print(
                f"\n{total} cross-repo GITHUB_TOKEN violation(s) found. Use secrets.GH_PAT for cross-repo operations."
            )
            return 1
        print("No cross-repo GITHUB_TOKEN violations found.")
        return 0
    else:
        wf_dir = Path(cast(str, args.dir))
        total = check_dir(wf_dir)
        if total:
            print(
                f"\n{total} cross-repo GITHUB_TOKEN violation(s) found. Use secrets.GH_PAT for cross-repo operations."
            )
            return 1
        return 0


if __name__ == "__main__":
    sys.exit(main())
