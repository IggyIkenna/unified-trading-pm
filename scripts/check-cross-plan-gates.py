#!/usr/bin/env python3
"""check-cross-plan-gates.py — Verify inter-plan dependency gates are met.

Reads active plans from plans/active/ and checks hardcoded inter-plan
dependencies. Returns non-zero if any gate is blocking.

Usage:
    python3 scripts/check-cross-plan-gates.py

Exit codes:
    0 — All gates pass
    1 — One or more gates are blocking
    2 — Error reading plan files
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

PM_ROOT = Path(__file__).resolve().parent.parent
PLANS_DIR = PM_ROOT / "plans" / "active"

# ── Inter-plan gate definitions ──────────────────────────────────────────────
# Each gate is a dict with:
#   - name: human-readable gate name
#   - description: why this gate exists
#   - source_plan_pattern: regex to match the source plan filename
#   - source_todo_ids: list of todo IDs that must be "done" in the source plan
#   - blocked_plan_pattern: regex to match the blocked plan filename
#   - blocked_todo_ids: list of todo IDs that are blocked (informational)

# Inter-plan gates: a hard dependency where one plan's todos must complete before
# another's can start. Add an entry per real cross-plan dependency.
#
# 2026-06-07: the sole historical gate (`defi-keys-phase1-blocks-cicd-backfill`) was
# REMOVED — it was permanently BLOCKED/false-positive: both plans it referenced
# (`defi_keys_data_integration`, `cicd_code_rollout`) are ARCHIVED (the secret
# provisioning + backfill long since shipped), and its `source_plan_pattern` carried a
# `.md.md$` double-extension typo so it never matched a live plan anyway. With no real
# active cross-plan hard-dependency today, GATES is empty (the checker exits 0). Re-add
# entries here only for a genuine "plan A todo blocks plan B todo" relationship.
GATES: list[dict[str, str | list[str]]] = []


def find_plan_file(pattern: str) -> Path | None:
    """Find the first plan file matching the regex pattern."""
    regex = re.compile(pattern)
    for plan_file in sorted(PLANS_DIR.glob("*.md")):
        if regex.search(plan_file.name):
            return plan_file
    return None


def extract_todo_statuses(plan_path: Path) -> dict[str, str]:
    """Extract {todo_id: status} from a plan file's YAML frontmatter + todos."""
    content = plan_path.read_text()
    statuses: dict[str, str] = {}

    # Match todo blocks: "- id: <id>" followed by "status: <status>"
    # Works for both YAML frontmatter style and inline style
    id_pattern = re.compile(r"^\s*-\s*id:\s*(\S+)", re.MULTILINE)
    status_pattern = re.compile(r"^\s*status:\s*(\S+)", re.MULTILINE)

    lines = content.split("\n")
    current_id: str | None = None

    for line in lines:
        id_match = id_pattern.match(line)
        if id_match:
            current_id = id_match.group(1)
            continue

        if current_id is not None:
            status_match = status_pattern.match(line)
            if status_match:
                statuses[current_id] = status_match.group(1)
                current_id = None

    return statuses


def check_gate(gate: dict[str, str | list[str]]) -> tuple[bool, str]:
    """Check a single gate. Returns (passed, message)."""
    name = str(gate["name"])
    source_pattern = str(gate["source_plan_pattern"])
    source_ids = gate["source_todo_ids"]
    assert isinstance(source_ids, list)

    source_plan = find_plan_file(source_pattern)
    if source_plan is None:
        return False, f"GATE '{name}': source plan not found (pattern: {source_pattern})"

    statuses = extract_todo_statuses(source_plan)

    incomplete: list[str] = []
    for todo_id in source_ids:
        status = statuses.get(todo_id, "not-found")
        if status != "done":
            incomplete.append(f"  - {todo_id}: {status}")

    if incomplete:
        blocked_ids = gate.get("blocked_todo_ids", [])  # noqa: qg-empty-fallback
        assert isinstance(blocked_ids, list)
        msg_lines = [
            f"GATE BLOCKED: '{name}'",
            f"  Source plan: {source_plan.name}",
            f"  Description: {gate['description']}",
            f"  Incomplete prerequisites ({len(incomplete)}/{len(source_ids)}):",
            *incomplete,
            f"  Blocked tasks: {', '.join(str(b) for b in blocked_ids)}",
        ]
        return False, "\n".join(msg_lines)

    return True, f"GATE PASSED: '{name}' — all {len(source_ids)} prerequisites are done"


def main() -> int:
    """Run all gate checks. Returns 0 if all pass, 1 if any block."""
    if not PLANS_DIR.is_dir():
        print(f"ERROR: Plans directory not found: {PLANS_DIR}", file=sys.stderr)
        return 2

    print(f"Checking {len(GATES)} inter-plan gates...")
    print(f"Plans directory: {PLANS_DIR}")
    print()

    all_passed = True
    for gate in GATES:
        passed, message = check_gate(gate)
        if passed:
            print(f"  [PASS] {message}")
        else:
            print(f"  [BLOCKED] {message}")
            all_passed = False
        print()

    if all_passed:
        print("All gates passed.")
        return 0

    print("One or more gates are BLOCKED. Blocked tasks cannot proceed.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
