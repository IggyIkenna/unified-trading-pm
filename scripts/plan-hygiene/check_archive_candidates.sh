#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
# Find plans in plans/active/ where open todo count == 0 and done todo count > 0.
# Prints candidates — does NOT archive. Operator reviews and archives manually.
# Usage: bash scripts/plan-hygiene/check_archive_candidates.sh

set -euo pipefail
PM_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
CANDIDATES=0

echo "Archive candidates (0 open todos, all work done):"
echo ""

for f in "$PM_DIR/plans/active"/*.md; do
  name="$(basename "$f")"
  [ "$name" = "INDEX.md" ] && continue
  [ "$name" = "task_template.md" ] && continue
  [[ "$name" == *.HANDOVER.md ]] && continue

  open=$(grep -cP "^\s*- \[ \]" "$f" 2>/dev/null || true)
  done=$(grep -cP "^\s*- \[x\]" "$f" 2>/dev/null || true)
  open="${open:-0}"
  done="${done:-0}"

  if [ "$open" -eq 0 ] && [ "$done" -gt 0 ]; then
    status=$(grep "^status:" "$f" 2>/dev/null | head -1 | sed 's/status: //' || echo "unknown")
    echo "  $name  done=${done}  status=${status}"
    CANDIDATES=$(( CANDIDATES + 1 ))
  fi
done

echo ""
if [ "$CANDIDATES" -eq 0 ]; then
  echo "No archive candidates found."
else
  echo "$CANDIDATES candidate(s). Archive with: git mv plans/active/<file> plans/archive/\$(date +%Y_%m)/"
fi
