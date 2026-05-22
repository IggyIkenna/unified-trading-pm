#!/usr/bin/env bash
# Validate frontmatter in plans/active/ and plans/epics/.
# Checks: --- on own first line, required fields, no deprecated fields.
# Usage: bash scripts/plan-hygiene/check_frontmatter.sh [--quiet]
# Exit 0 = clean. Exit 1 = violations found.

set -euo pipefail
QUIET="${1:-}"
PM_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
FAILURES=0

REQUIRED_PLAN_FIELDS=("parent_epic" "title" "priority" "status" "estimate_class" "estimate_baseline_ai_days" "estimate_calibrated_ai_days" "locked_by")
DEPRECATED_FIELDS=("slug" "deadline" "owner" "asset_group" "horizon" "operator" "companion_to" "companion_plans" "spawned_from" "parent_plan" "related_codex" "overview")
REQUIRED_EPIC_FIELDS=("name" "title" "priority" "status")

check_file() {
  local f="$1"
  local kind="$2"  # "plan" or "epic"
  local name
  name="$(basename "$f")"
  local errs=()

  # First line must be exactly ---
  local first
  first=$(head -1 "$f")
  if [ "$first" != "---" ]; then
    errs+=("jammed frontmatter: first line is '$first' not '---'")
  fi

  # Extract frontmatter block only (lines between the two --- delimiters) to a
  # temp file. Using a temp file avoids SIGPIPE when grep -q exits early on large
  # frontmatter blocks piped via echo "$var" with set -o pipefail.
  local fm_file
  fm_file=$(mktemp /tmp/fm_check_XXXXXX)
  awk 'NR==1{next} /^---$/{exit} {print}' "$f" > "$fm_file"

  # Check required fields
  local required=()
  if [ "$kind" = "plan" ]; then
    required=("${REQUIRED_PLAN_FIELDS[@]}")
  else
    required=("${REQUIRED_EPIC_FIELDS[@]}")
  fi

  for field in "${required[@]}"; do
    if ! grep -q "^${field}:" "$fm_file" 2>/dev/null; then
      errs+=("missing required field: ${field}")
    fi
  done

  # Check deprecated fields (frontmatter block only)
  for field in "${DEPRECATED_FIELDS[@]}"; do
    if grep -q "^${field}:" "$fm_file" 2>/dev/null; then
      errs+=("deprecated field present: ${field}")
    fi
  done

  rm -f "$fm_file"

  if [ "${#errs[@]}" -gt 0 ]; then
    echo "  $name:"
    for e in "${errs[@]}"; do
      echo "    - $e"
    done
    FAILURES=$(( FAILURES + 1 ))
  fi
}

echo "Checking plans/active/..."
for f in "$PM_DIR/plans/active"/*.md; do
  name="$(basename "$f")"
  [ "$name" = "INDEX.md" ] && continue
  [ "$name" = "task_template.md" ] && continue
  [[ "$name" == _* ]] && continue           # _agent_pings.md etc
  [[ "$name" == *.HANDOVER.md ]] && continue
  check_file "$f" "plan"
done

echo "Checking plans/epics/ (non-superseded)..."
for f in "$PM_DIR/plans/epics"/*.md; do
  name=$(basename "$f")
  [[ "$name" == *SUPERSEDED* ]] && continue
  [ "$name" = "README.md" ] && continue
  check_file "$f" "epic"
done

echo ""
if [ "$FAILURES" -gt 0 ]; then
  echo "❌ check_frontmatter: ${FAILURES} file(s) with violations"
  exit 1
else
  [ "$QUIET" != "--quiet" ] && echo "✅ check_frontmatter: all files clean"
  exit 0
fi
