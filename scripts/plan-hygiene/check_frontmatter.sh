#!/usr/bin/env bash
# Validate frontmatter in plans/active/ and plans/epics/.
# Checks: --- on own first line, required fields, no deprecated fields.
# Usage: bash scripts/plan-hygiene/check_frontmatter.sh [--quiet]
# Exit 0 = clean. Exit 1 = violations found.

set -euo pipefail
PM_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
FAILURES=0

# Args: --quiet (flag) + an optional explicit file list. When files are passed, validate
# ONLY those (the prek hook's STAGED plans) — staged-files-only so a commit is never blocked
# by a pre-existing violation in a plan it does not touch. No files given → full-corpus glob
# (the cron / CI / interactive behaviour, unchanged).
QUIET=""
FILES=()
for arg in "$@"; do
  case "$arg" in
    --quiet) QUIET="--quiet" ;;
    *) FILES+=("$arg") ;;
  esac
done

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

should_skip() {  # shared skip rules (INDEX/template/_*/HANDOVER/SUPERSEDED/README)
  local n="$1"
  [ "$n" = "INDEX.md" ] && return 0
  [ "$n" = "task_template.md" ] && return 0
  [ "$n" = "README.md" ] && return 0
  [[ "$n" == _* ]] && return 0
  [[ "$n" == *.HANDOVER.md ]] && return 0
  [[ "$n" == *SUPERSEDED* ]] && return 0
  return 1
}

if [ "${#FILES[@]}" -gt 0 ]; then
  # Staged-files-only mode (prek hook): check just the passed plan files. Classify each by
  # its directory; only DIRECT children of plans/active (plan) and plans/epics (epic) are
  # frontmatter-checked — matching the corpus globs (plans/active/issues/ etc. are exempt).
  for f in "${FILES[@]}"; do
    case "$f" in /*) ;; *) f="$PM_DIR/$f" ;; esac   # normalize relative → absolute for matching
    [ -f "$f" ] || continue
    name="$(basename "$f")"
    should_skip "$name" && continue
    case "$f" in
      */plans/active/*.md)
        rel="${f##*/plans/active/}"; [[ "$rel" == */* ]] && continue
        check_file "$f" "plan" ;;
      */plans/epics/*.md)
        rel="${f##*/plans/epics/}"; [[ "$rel" == */* ]] && continue
        check_file "$f" "epic" ;;
    esac
  done
else
  echo "Checking plans/active/..."
  for f in "$PM_DIR/plans/active"/*.md; do
    name="$(basename "$f")"
    should_skip "$name" && continue
    check_file "$f" "plan"
  done

  echo "Checking plans/epics/ (non-superseded)..."
  for f in "$PM_DIR/plans/epics"/*.md; do
    name=$(basename "$f")
    should_skip "$name" && continue
    check_file "$f" "epic"
  done
fi

echo ""
if [ "$FAILURES" -gt 0 ]; then
  echo "❌ check_frontmatter: ${FAILURES} file(s) with violations"
  exit 1
else
  [ "$QUIET" != "--quiet" ] && echo "✅ check_frontmatter: all files clean"
  exit 0
fi
