#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
set -euo pipefail

# check-plan-gate.sh — Check if all todo items with a given prefix are marked done in a plan file.
#
# Usage:
#   bash scripts/agents/check-plan-gate.sh <plan_file> <prefix>
#
# Returns 0 if ALL items matching the prefix are done, 1 otherwise.
#
# Example:
#   bash scripts/agents/check-plan-gate.sh plans/active/some-plan.md "phase1-"
#
# The script reads YAML frontmatter todos and checks items whose id starts with <prefix>.
# A todo is "done" if it has "done: true" or "status: done".

PLAN_FILE="${1:?Usage: check-plan-gate.sh <plan_file> <prefix>}"
PREFIX="${2:?Usage: check-plan-gate.sh <plan_file> <prefix>}"

if [ ! -f "$PLAN_FILE" ]; then
  echo "ERROR: Plan file not found: $PLAN_FILE"
  exit 1
fi

python3 - "$PLAN_FILE" "$PREFIX" << 'PYEOF'
import sys
import re

plan_file = sys.argv[1]
prefix = sys.argv[2]

with open(plan_file) as f:
    content = f.read()

# Extract YAML frontmatter (between --- markers)
fm_match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
if not fm_match:
    print(f"ERROR: No YAML frontmatter found in {plan_file}")
    sys.exit(1)

frontmatter = fm_match.group(1)

# Parse todos manually (no yaml dep) — look for lines like:
#   - id: phase1-something
#     done: true
# or
#   - id: phase1-something
#     status: done
lines = frontmatter.splitlines()

matching_items: list[dict[str, str]] = []
current_item: dict[str, str] = {}

for line in lines:
    stripped = line.strip()
    # New list item
    if stripped.startswith("- id:"):
        if current_item:
            matching_items.append(current_item)
        item_id = stripped.split(":", 1)[1].strip().strip("\"'")
        current_item = {"id": item_id}
    elif current_item:
        if stripped.startswith("done:"):
            current_item["done"] = stripped.split(":", 1)[1].strip().strip("\"'").lower()
        elif stripped.startswith("status:"):
            current_item["status"] = stripped.split(":", 1)[1].strip().strip("\"'").lower()
        # If we hit a new top-level key that's not part of a todo item, flush
        elif not stripped.startswith("-") and ":" in stripped and not stripped.startswith("#"):
            # Could be a new key at the same indent level
            pass

if current_item:
    matching_items.append(current_item)

# Filter to items matching prefix
filtered = [item for item in matching_items if item.get("id", "").startswith(prefix)]

if not filtered:
    print(f"No todo items found with prefix '{prefix}' in {plan_file}")
    sys.exit(1)

# Check if all are done
not_done: list[str] = []
for item in filtered:
    is_done = item.get("done") == "true" or item.get("status") == "done"
    status_str = "DONE" if is_done else "NOT DONE"
    print(f"  {item['id']}: {status_str}")
    if not is_done:
        not_done.append(item["id"])

print()
if not_done:
    print(f"GATE FAILED: {len(not_done)}/{len(filtered)} items with prefix '{prefix}' are not done:")
    for item_id in not_done:
        print(f"  - {item_id}")
    sys.exit(1)
else:
    print(f"GATE PASSED: all {len(filtered)} items with prefix '{prefix}' are done.")
    sys.exit(0)
PYEOF
