#!/bin/bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# §13 — No Unimplemented Stubs
# Checks: NotImplementedError, TODO, FIXME, HACK, STUB, placeholder in production source.
# Usage: bash unified-trading-pm/scripts/audit/s13-stubs.sh [--repo <repo-name>]
# With no --repo, runs across entire workspace.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$SCRIPT_DIR/lib.sh"
cd "$WORKSPACE_ROOT"

echo "=== §13 No Unimplemented Stubs ==="

TARGET="."
if [[ "${1:-}" == "--repo" && -n "${2:-}" ]]; then
  TARGET="$2"
  echo "    (scoped to: $TARGET)"
fi

stub_hits=$(rg \
  'raise NotImplementedError|# TODO|# FIXME|# HACK|# STUB|# placeholder' \
  --type py \
  --glob '!.venv*' --glob '!**/.venv*/**' \
  --glob '!**/tests/**' --glob '!**/test_*' \
  --glob '!**/archive/**' --glob '!**/*.egg-info/**' \
  -n "$TARGET" 2>/dev/null || true)

if [ -z "$stub_hits" ]; then
  emit "§13" "zero stub/TODO/FIXME/NotImplementedError in prod" "PASS" "none"
  audit_summary
  exit 0
fi

stub_count=$(echo "$stub_hits" | wc -l | tr -d ' ')

# Break down by category for evidence
nie_count=$(echo "$stub_hits" | grep -c 'NotImplementedError' || true)
todo_count=$(echo "$stub_hits" | grep -c 'TODO\|FIXME\|HACK' || true)
stub_marker_count=$(echo "$stub_hits" | grep -c '# STUB\|# placeholder' || true)

if [ "$stub_count" -le 10 ]; then
  emit "§13" "stub count ≤10 (each needs active plan todo)" "WARN" \
    "$stub_count total — NotImplementedError:$nie_count TODO/FIXME/HACK:$todo_count STUB/placeholder:$stub_marker_count"
  echo ""
  echo "  Full list (check each has plan todo):"
  echo "$stub_hits" | head -20 | sed 's/^/    /'
else
  emit "§13" "stub count ≤10 (each needs active plan todo)" "FAIL" \
    "$stub_count total (>10 threshold) — NotImplementedError:$nie_count TODO/FIXME/HACK:$todo_count"
  echo ""
  echo "  First 20 hits:"
  echo "$stub_hits" | head -20 | sed 's/^/    /'
fi

audit_summary
