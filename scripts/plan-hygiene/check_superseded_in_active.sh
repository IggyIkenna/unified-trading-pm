#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
# Find plans that should be in archive/ but are sitting in plans/active/:
#   (1) Filenames in plans/active/ containing "SUPERSEDED"
#   (2) Plans whose body references a *_SUPERSEDED_* epic slug as their parent_epic
#       (indicates the plan is orphaned by a superseded epic and likely stale)
# Soft check — exits 0 always (informational).
# Usage: bash scripts/plan-hygiene/check_superseded_in_active.sh [--quiet]

set -euo pipefail
QUIET="${1:-}"
PM_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
FOUND=0

[ "$QUIET" != "--quiet" ] && echo "Superseded-in-active check:"
[ "$QUIET" != "--quiet" ] && echo ""

# (1) Filenames with SUPERSEDED
for f in "$PM_DIR/plans/active"/*.md; do
  name="$(basename "$f")"
  if [[ "$name" == *SUPERSEDED* ]]; then
    echo "  FILENAME  $name  (contains SUPERSEDED — should be in archive/)"
    FOUND=$(( FOUND + 1 ))
  fi
done

# (2) Plans whose parent_epic references a superseded epic file
for f in "$PM_DIR/plans/active"/*.md; do
  name="$(basename "$f")"
  [ "$name" = "INDEX.md" ] && continue
  [[ "$name" == _* ]] && continue
  [[ "$name" == *.HANDOVER.md ]] && continue

  fm_file=$(mktemp /tmp/sup_check_XXXXXX)
  awk 'NR==1{next} /^---$/{exit} {print}' "$f" > "$fm_file"
  parent=$(grep "^parent_epic:" "$fm_file" 2>/dev/null | sed 's/parent_epic: *//' | tr -d '"' || true)
  rm -f "$fm_file"

  [ -z "$parent" ] && continue

  # Check if a *SUPERSEDED* epic file exists for this slug
  if ls "$PM_DIR/plans/epics/"*"${parent}"*"SUPERSEDED"*.md 2>/dev/null | grep -q .; then
    echo "  PARENT_SUPERSEDED  $name  (parent_epic: $parent is superseded)"
    FOUND=$(( FOUND + 1 ))
  fi
done

echo ""
if [ "$FOUND" -gt 0 ]; then
  echo "⚠️  check_superseded_in_active: ${FOUND} plan(s) flagged (soft check — review before archiving)"
else
  [ "$QUIET" != "--quiet" ] && echo "✅ check_superseded_in_active: no superseded plans in active/"
fi

exit 0
