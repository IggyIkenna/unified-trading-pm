#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# update-pm-plan-status.sh — Update a todo's status in a .md file
#
# Usage:
#   bash scripts/update-pm-plan-status.sh --service SERVICE_NAME --todo TODO_ID --status STATUS [--notes "notes text"]
#   bash scripts/update-pm-plan-status.sh --service SERVICE_NAME --todo TODO_ID --status STATUS [--plan PLAN_FILE]
#
# Options:
#   --service   Service/repo name (used to find plan file if --plan not given)
#   --todo      Todo ID (matches `- id: <todo_id>` in YAML frontmatter)
#   --status    New status: pending | in_progress | completed | done | blocked
#   --notes     Optional notes to append under the todo (replaces existing notes)
#   --plan      Full path to plan file (overrides auto-discovery by service name)
#   --dry-run   Print what would change without modifying any file
#
# Auto-discovery: Searches plans/active/ for a plan whose filename contains SERVICE_NAME.
# If multiple plans match, all are searched for the todo.
#
# Exit codes:
#   0 — Successfully updated
#   1 — Todo not found in any plan
#   2 — Missing required arguments
#
# Example (from a service repo's GHA workflow):
#   bash unified-trading-pm/scripts/update-pm-plan-status.sh \
#     --service execution-service --todo p0-execution-engine --status completed \
#     --notes "QG passed 2026-03-09, commit abc1234"

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PM_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PLANS_DIR="$PM_ROOT/plans/active"

# ── PARSE ARGUMENTS ───────────────────────────────────────────────────────────
SERVICE_NAME=""
TODO_ID=""
NEW_STATUS=""
NOTES=""
PLAN_FILE=""
DRY_RUN=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --service)
      SERVICE_NAME="$2"
      shift 2
      ;;
    --todo)
      TODO_ID="$2"
      shift 2
      ;;
    --status)
      NEW_STATUS="$2"
      shift 2
      ;;
    --notes)
      NOTES="$2"
      shift 2
      ;;
    --plan)
      PLAN_FILE="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    *)
      echo "Unknown argument: $1"
      exit 2
      ;;
  esac
done

# ── VALIDATE REQUIRED ARGS ────────────────────────────────────────────────────
if [ -z "$TODO_ID" ] || [ -z "$NEW_STATUS" ]; then
  echo "❌ --todo and --status are required."
  echo ""
  echo "Usage: bash $0 --service <name> --todo <id> --status <status> [--notes <text>] [--plan <path>] [--dry-run]"
  exit 2
fi

VALID_STATUSES="pending|in_progress|completed|done|blocked|todo"
if ! echo "$NEW_STATUS" | grep -qE "^($VALID_STATUSES)$"; then
  echo "❌ --status must be one of: $VALID_STATUSES"
  exit 2
fi

# ── FIND TARGET PLAN FILE(S) ──────────────────────────────────────────────────
CANDIDATES=()
if [ -n "$PLAN_FILE" ]; then
  if [ ! -f "$PLAN_FILE" ]; then
    echo "❌ Plan file not found: $PLAN_FILE"
    exit 1
  fi
  CANDIDATES=("$PLAN_FILE")
elif [ -n "$SERVICE_NAME" ]; then
  # Search for plans containing SERVICE_NAME in filename
  while IFS= read -r -d '' f; do
    CANDIDATES+=("$f")
  done < <(find "$PLANS_DIR" -name "*${SERVICE_NAME}*" -name "*.md" -print0 2>/dev/null)
  # Also search all plans for the todo id if no filename match
  if [ ${#CANDIDATES[@]} -eq 0 ]; then
    while IFS= read -r -d '' f; do
      if grep -q "^\s*- id: $TODO_ID" "$f" 2>/dev/null; then
        CANDIDATES+=("$f")
      fi
    done < <(find "$PLANS_DIR" -name "*.md" -print0 2>/dev/null)
  fi
else
  # No service or plan — search all plans for the todo id
  while IFS= read -r -d '' f; do
    if grep -q "^\s*- id: $TODO_ID" "$f" 2>/dev/null; then
      CANDIDATES+=("$f")
    fi
  done < <(find "$PLANS_DIR" -name "*.md" -print0 2>/dev/null)
fi

if [ ${#CANDIDATES[@]} -eq 0 ]; then
  echo "❌ Could not find any plan file for service='$SERVICE_NAME', todo='$TODO_ID'"
  exit 1
fi

# ── UPDATE TODO STATUS IN PLAN ────────────────────────────────────────────────
UPDATED=false
for plan in "${CANDIDATES[@]}"; do
  if ! grep -q "^\s*- id: $TODO_ID" "$plan" 2>/dev/null; then
    continue
  fi

  echo "📋 Found todo '$TODO_ID' in: $(basename "$plan")"

  if [ "$DRY_RUN" = true ]; then
    OLD_STATUS=$(grep -A2 "^\s*- id: $TODO_ID" "$plan" | grep "status:" | head -1 | sed 's/.*status: //')
    echo "   Would change: status: $OLD_STATUS → status: $NEW_STATUS"
    [ -n "$NOTES" ] && echo "   Would set notes: $NOTES"
    UPDATED=true
    continue
  fi

  # Use Python for reliable YAML-adjacent line editing (status line follows id line)
  python3 - "$plan" "$TODO_ID" "$NEW_STATUS" "$NOTES" <<'PYEOF'
import sys
import re

plan_file, todo_id, new_status, notes = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]

with open(plan_file) as f:
    content = f.read()

lines = content.splitlines(keepends=True)
updated_lines = []
i = 0
found = False

while i < len(lines):
    line = lines[i]
    # Detect the todo id line
    id_match = re.match(r'^(\s*)- id:\s*' + re.escape(todo_id) + r'\s*$', line)
    if id_match:
        found = True
        indent = id_match.group(1)
        updated_lines.append(line)
        i += 1
        # Scan ahead: find the `status:` line within this todo block
        # A new todo starts with `  - id:` (same or lower indent level)
        block_lines = []
        status_replaced = False
        notes_start = None
        notes_end = None

        while i < len(lines):
            next_line = lines[i]
            # End of this todo block: new id at same indent level, or less-indented line
            if re.match(r'^' + re.escape(indent) + r'- id:', next_line) and block_lines:
                break
            if re.match(r'^---', next_line):
                break
            block_lines.append((i, next_line))
            # Track notes block boundaries
            notes_match = re.match(r'^(\s+)notes:\s*', next_line)
            if notes_match and notes_start is None:
                notes_start = len(block_lines) - 1
                notes_indent = notes_match.group(1)
            elif notes_start is not None and notes_end is None:
                # notes ends when indent reduces or new key starts at same or lower level
                if not next_line.startswith(notes_indent + ' ') and not re.match(r'^\s*$', next_line):
                    notes_end = len(block_lines) - 1
            i += 1

        # Rebuild block: replace status, optionally replace notes
        new_block = []
        for idx, (orig_i, bline) in enumerate(block_lines):
            status_match = re.match(r'^(\s+)status:\s*\S+', bline)
            if status_match and not status_replaced:
                new_block.append(f'{status_match.group(1)}status: {new_status}\n')
                status_replaced = True
            else:
                new_block.append(bline)

        # If status not found in block, append it
        if not status_replaced:
            new_block.append(f'{indent}    status: {new_status}\n')

        # Handle notes replacement if provided
        if notes:
            # Find existing notes and replace, or append
            note_lines = []
            note_indent = indent + '    '
            has_notes = any(re.match(r'^\s+notes:', bl) for _, bl in block_lines)
            final_block = []
            in_notes = False
            notes_written = False
            for bline in new_block:
                if re.match(r'^\s+notes:', bline) and not notes_written:
                    in_notes = True
                    final_block.append(f'{note_indent}notes: |\n')
                    final_block.append(f'{note_indent}  {notes}\n')
                    notes_written = True
                elif in_notes:
                    # Skip old note content lines (indented under notes:)
                    if bline.startswith(note_indent + '  ') or bline.startswith(note_indent + '\t'):
                        continue
                    else:
                        in_notes = False
                        final_block.append(bline)
                else:
                    final_block.append(bline)
            if not notes_written:
                final_block.append(f'{note_indent}notes: |\n')
                final_block.append(f'{note_indent}  {notes}\n')
            new_block = final_block

        updated_lines.extend(new_block)
        continue  # i already advanced past block

    updated_lines.append(line)
    i += 1

if not found:
    print(f"ERROR: todo id '{todo_id}' not found in {plan_file}", file=sys.stderr)
    sys.exit(1)

with open(plan_file, 'w') as f:
    f.writelines(updated_lines)

print(f"OK: Updated status → {new_status}" + (f" with notes" if notes else ""))
PYEOF

  echo "   ✅ Status updated to: $NEW_STATUS in $(basename "$plan")"
  UPDATED=true
done

if [ "$UPDATED" = false ]; then
  echo "❌ Todo '$TODO_ID' not found in any candidate plan file."
  exit 1
fi

# ── AUTO-COMMIT TO PM BRANCH ──────────────────────────────────────────────────
if [ "$DRY_RUN" = false ]; then
  cd "$PM_ROOT"
  if [ -n "$(git status --porcelain plans/active/ 2>/dev/null)" ]; then
    git add plans/active/
    COMMIT_SERVICE="${SERVICE_NAME:-unknown}"
    git commit -m "chore(plans): mark ${COMMIT_SERVICE}/${TODO_ID} as ${NEW_STATUS}

Auto-updated by update-pm-plan-status.sh

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>" --quiet
    echo "   ✅ Committed plan update to PM"
  else
    echo "   ℹ️  No plan changes to commit (already up to date)"
  fi
fi

echo ""
echo "✅ Done: todo '$TODO_ID' → $NEW_STATUS"
