#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""fix-gh-actions-pm-clone.py — Add unified-trading-pm clone to all GH Actions quality-gates.yml.

All quality-gates.sh stubs source:
    ${WORKSPACE_ROOT}/unified-trading-pm/scripts/quality-gates-base/base-service.sh
    (or base-library.sh / base-ui.sh)

In GH Actions, WORKSPACE_ROOT = parent of the checked-out repo directory. unified-trading-pm must
be cloned to ../ (sibling of the repo checkout) for the source line to resolve.

This script patches every .github/workflows/quality-gates.yml that:
  - calls "bash scripts/quality-gates.sh"
  - does NOT already clone unified-trading-pm

Two patterns are handled:
  Pattern A — has an existing "Checkout dependencies" step with git clone lines
              → adds unified-trading-pm clone after the last "|| true" clone line
  Pattern B — no git clone step at all
              → inserts a new "Clone build scripts" step before "Run quality gates"

Usage:
    python3 fix-gh-actions-pm-clone.py [--dry-run] [--repo <name>]
    python3 fix-gh-actions-pm-clone.py --dry-run       # preview all changes
    python3 fix-gh-actions-pm-clone.py                  # apply all changes
    python3 fix-gh-actions-pm-clone.py --repo alerting-service  # single repo
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]

PM_CLONE_LINE = (
    '            (git clone -b "$BRANCH" '
    '"https://x-access-token:${GH_PAT}@github.com/IggyIkenna/unified-trading-pm.git" '
    "../unified-trading-pm 2>/dev/null \\\n"
    "              || git clone -b main "
    '"https://x-access-token:${GH_PAT}@github.com/IggyIkenna/unified-trading-pm.git" '
    "../unified-trading-pm 2>/dev/null) || true\n"
)

NEW_CLONE_STEP = (
    "      - name: Clone build scripts\n"
    "        env:\n"
    "          GH_PAT: ${{ secrets.GH_PAT }}\n"
    "          DEP_BRANCH: ${{ github.head_ref || github.ref_name }}\n"
    "        run: |\n"
    '          BRANCH="${DEP_BRANCH:-main}"\n'
    '          (git clone -b "$BRANCH"'
    ' "https://x-access-token:${GH_PAT}@github.com/IggyIkenna/unified-trading-pm.git"'
    " ../unified-trading-pm 2>/dev/null \\\n"
    "            || git clone -b main"
    ' "https://x-access-token:${GH_PAT}@github.com/IggyIkenna/unified-trading-pm.git"'
    " ../unified-trading-pm 2>/dev/null) || true\n"
    '          echo "unified-trading-pm cloned for quality-gates base scripts"\n'
    "\n"
)


def patch_workflow(path: Path, dry_run: bool) -> str:
    """Patch one workflow file. Returns 'patched', 'already_ok', or 'no_qg'."""
    text = path.read_text()

    # Skip if doesn't call quality-gates.sh
    if "scripts/quality-gates.sh" not in text:
        return "no_qg"

    # Skip if unified-trading-pm already present
    if "unified-trading-pm" in text:
        return "already_ok"

    lines = text.splitlines(keepends=True)

    # ── Pattern A: existing git clone block ──────────────────────────────────
    # Find last line that looks like a git clone ending with "|| true"
    last_clone_idx = -1
    for i, line in enumerate(lines):
        if re.search(r"git clone.*\|\| true", line):
            last_clone_idx = i

    if last_clone_idx >= 0:
        new_lines = [*lines[: last_clone_idx + 1], PM_CLONE_LINE, *lines[last_clone_idx + 1 :]]
        new_text = "".join(new_lines)
        if not dry_run:
            path.write_text(new_text)
        return "patched_A"

    # ── Pattern B: no existing clone step — insert before "Run quality gates" ──
    # Find the "- name: Run quality gates" step
    target_pattern = re.compile(r"^(\s*)- name: Run quality gates\b", re.MULTILINE)
    match = target_pattern.search(text)
    if match:
        insert_pos = match.start()
        new_text = text[:insert_pos] + NEW_CLONE_STEP + text[insert_pos:]
        if not dry_run:
            path.write_text(new_text)
        return "patched_B"

    # Fallback: append before last step in file
    return "unknown_pattern"


class _ParsedArgs(argparse.Namespace):
    dry_run: bool
    repo: str


def main() -> None:
    parser = argparse.ArgumentParser(description="Add unified-trading-pm clone to GH Actions workflows")
    parser.add_argument("--dry-run", action="store_true", dest="dry_run", help="Preview changes without writing")
    parser.add_argument("--repo", default="", help="Only process this one repo")
    args = parser.parse_args(namespace=_ParsedArgs())

    if args.repo:
        workflow_files = [WORKSPACE_ROOT / args.repo / ".github" / "workflows" / "quality-gates.yml"]
    else:
        workflow_files = sorted(WORKSPACE_ROOT.glob("*/.github/workflows/quality-gates.yml"))

    counts = {"patched_A": 0, "patched_B": 0, "already_ok": 0, "no_qg": 0, "unknown_pattern": 0, "missing": 0}

    for wf_path in workflow_files:
        repo = wf_path.parts[-4]  # .../repo/.github/workflows/quality-gates.yml
        if not wf_path.exists():
            print(f"  [MISS]   {repo} — file not found")
            counts["missing"] += 1
            continue

        result = patch_workflow(wf_path, dry_run=args.dry_run)
        counts[result] += 1

        if result == "patched_A":
            verb = "DRY-RUN would patch" if args.dry_run else "Patched"
            print(f"  [A]      {repo} — {verb}: added unified-trading-pm to existing clone step")
        elif result == "patched_B":
            verb = "DRY-RUN would insert" if args.dry_run else "Patched"
            print(f"  [B]      {repo} — {verb}: inserted new 'Clone build scripts' step")
        elif result == "already_ok":
            print(f"  [OK]     {repo} — already clones unified-trading-pm")
        elif result == "no_qg":
            print(f"  [SKIP]   {repo} — does not call quality-gates.sh")
        elif result == "unknown_pattern":
            print(f"  [WARN]   {repo} — unknown pattern; manual fix needed")

    print()
    print(
        f"Results: patched_A={counts['patched_A']}  patched_B={counts['patched_B']}  "
        f"already_ok={counts['already_ok']}  no_qg={counts['no_qg']}  "
        f"unknown={counts['unknown_pattern']}  missing={counts['missing']}"
    )

    if args.dry_run:
        print("\n(dry-run — no files written)")
    else:
        total_patched = counts["patched_A"] + counts["patched_B"]
        print(f"\n✅ Patched {total_patched} workflow(s).")
        if counts["unknown_pattern"]:
            print(f"⚠️  {counts['unknown_pattern']} repo(s) have unknown patterns — fix manually.")
        sys.exit(1 if counts["unknown_pattern"] else 0)


if __name__ == "__main__":
    main()
