#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Check that every codex/... path referenced in plans/active/ and plans/epics/ exists on disk.
# Soft check — exits 0 if broken refs found (informational); exit 1 only on script error.
# Usage: bash scripts/plan-hygiene/check_codex_refs.sh [--quiet]
# Exit 0 always (soft). Prints broken refs.

set -euo pipefail
QUIET="${1:-}"
PM_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
BROKEN=0
CHECKED=0
SEEN_FILE=$(mktemp "${TMPDIR:-/tmp}/codex_seen_XXXXXX")
trap 'rm -f "$SEEN_FILE"' EXIT

# Extract unique codex paths from plan + epic bodies (outside frontmatter)
extract_refs() {
  local f="$1"
  awk 'NR==1{next} /^---$/{found=1; next} found{print}' "$f" \
    | grep -oE 'codex/[0-9]{2}-[a-z-]+/[a-zA-Z0-9_./-]+\.md' \
    | sort -u
}

check_file() {
  local f="$1"
  while IFS= read -r ref; do
    [ -z "$ref" ] && continue
    CHECKED=$(( CHECKED + 1 ))
    full="$PM_DIR/$ref"
    if [ ! -f "$full" ] && ! grep -qxF "$ref" "$SEEN_FILE" 2>/dev/null; then
      echo "$ref" >> "$SEEN_FILE"
      echo "  BROKEN  $ref"
      echo "          referenced in: $(basename "$f")"
      BROKEN=$(( BROKEN + 1 ))
    fi
  done < <(extract_refs "$f")
}

[ "$QUIET" != "--quiet" ] && echo "Codex reference check (plans/active/ + plans/epics/):"
[ "$QUIET" != "--quiet" ] && echo ""

for f in "$PM_DIR/plans/active"/*.md; do
  name="$(basename "$f")"
  [ "$name" = "INDEX.md" ] && continue
  [[ "$name" == _* ]] && continue
  [[ "$name" == *.HANDOVER.md ]] && continue
  check_file "$f"
done

for f in "$PM_DIR/plans/epics"/*.md; do
  name="$(basename "$f")"
  [[ "$name" == *SUPERSEDED* ]] && continue
  [ "$name" = "README.md" ] && continue
  check_file "$f"
done

echo ""
if [ "$BROKEN" -gt 0 ]; then
  echo "⚠️  check_codex_refs: ${BROKEN} broken ref(s) found (${CHECKED} checked)"
else
  [ "$QUIET" != "--quiet" ] && echo "✅ check_codex_refs: all ${CHECKED} refs resolve (soft check)"
fi

exit 0
