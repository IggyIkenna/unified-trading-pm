#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Find plans that should be in archive/ but are sitting in plans/active/:
#   (1) Filenames in plans/active/ containing "SUPERSEDED"
#   (2) Plans whose body references a *_SUPERSEDED_* epic slug as their parent_epic
#       (indicates the plan is orphaned by a superseded epic and likely stale)
#   (3) A plan listed in ANOTHER active plan's `supersedes:` frontmatter that is itself
#       still `status: active` in plans/active/ — the consolidation closed-out the body
#       banner + the new plan's supersedes: list but forgot to flip the source's status,
#       so it masquerades as live. (Added 2026-06-25 after the operator caught 7 cicd
#       source plans sitting status:active for a day with no tooling flag.)
# Registered `soft` in run_hygiene_sweep.sh → a non-zero exit surfaces as a ⚠️ SOFT_WARN
# (visible, non-blocking). Exits non-zero when any plan is flagged, 0 when clean.
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

  fm_file=$(mktemp "${TMPDIR:-/tmp}/sup_check_XXXXXX")
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

# (3) Plans listed in another active plan's `supersedes:` but still status: active
#     (handles both the multi-line YAML list and the inline `supersedes: <slug>` form;
#      entries may be a bare slug, an `issues/<slug>` subpath, or a `plans/active/…md` path,
#      with an optional trailing "(parenthetical)" note — all normalised to a slug under
#      plans/active/.)
for f in "$PM_DIR/plans/active"/*.md; do
  name="$(basename "$f")"
  [ "$name" = "INDEX.md" ] && continue
  [[ "$name" == _* ]] && continue

  sup_raw=$(awk '
    NR==1 && /^---[[:space:]]*$/ { infm=1; next }
    infm && /^---[[:space:]]*$/ { exit }
    infm && /^supersedes:/ {
      rest=$0; sub(/^supersedes:[[:space:]]*/, "", rest)
      if (rest != "") { print rest } else { insup=1 }
      next
    }
    insup && /^[[:space:]]+-[[:space:]]/ {
      s=$0; sub(/^[[:space:]]*-[[:space:]]*/, "", s); print s; next
    }
    insup && /^[^[:space:]]/ { insup=0 }
  ' "$f")

  [ -z "$sup_raw" ] && continue

  while IFS= read -r entry; do
    [ -z "$entry" ] && continue
    slug="${entry%%(*}"                          # drop trailing " (parenthetical…)"
    slug="$(echo "$slug" | sed 's/[[:space:]]*$//')"  # trim trailing whitespace
    slug="${slug#plans/active/}"                 # strip a leading plans/active/ path prefix
    slug="${slug%.md}"                           # strip a trailing .md
    [ -z "$slug" ] && continue

    target="$PM_DIR/plans/active/${slug}.md"
    [ -f "$target" ] || continue                 # already moved to archive (or never active) → fine

    tstatus=$(awk 'NR==1{next} /^---$/{exit} /^status:/{sub(/status:[[:space:]]*/,"");gsub(/[[:space:]]+$/,"");print;exit}' "$target")
    if [ "$tstatus" = "active" ]; then
      echo "  SUPERSEDED_BUT_ACTIVE  ${slug}.md  (listed in supersedes: of $name but still status: active — flip to superseded or archive)"
      FOUND=$(( FOUND + 1 ))
    fi
  done <<< "$sup_raw"
done

echo ""
if [ "$FOUND" -gt 0 ]; then
  echo "⚠️  check_superseded_in_active: ${FOUND} plan(s) flagged (soft check — review before archiving)"
  exit 1
fi

[ "$QUIET" != "--quiet" ] && echo "✅ check_superseded_in_active: no superseded plans in active/"
exit 0
