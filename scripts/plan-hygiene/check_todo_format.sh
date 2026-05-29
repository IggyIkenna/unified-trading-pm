#!/usr/bin/env bash
# Detect non-canonical todos in plans/active/.
#
# Canonical form: - [ ] [TAG] P<0-3>. <description>
#                 - [ ] [TAG] [UI] P<0-3>. ...        (multi-tag legal per CLAUDE.md UI HARD RULE)
#                 - [ ] [TAG] P<0-3>.<sub-id>. ...    (sub-priority allowed; e.g. P0.7.)
#
# Note: regen_backlog_from_plan.py is permissive — it ingests ANY "- [ ]" line and
# extracts `\bP[0-3]\b` from anywhere in the body. So non-canonical lines are NOT
# silently skipped — but they lose priority signal when no P-tag exists, and they
# create display-inconsistency in the dashboard/inventory.
#
# This check flags two severities:
#   ❌ NO_PRIORITY  — no P<0-3> anywhere in the line (priority defaults to None;
#                    dispatcher de-prioritizes). Hard hygiene failure.
#   ⚠️  NON_CANONICAL — has priority but format isn't the canonical
#                    `[TAG] P<n>.` (e.g. `[TAG][P<n>]`, `[P<n>][TAG]`, or `🟠 [TAG] P<n>.`).
#                    Soft hygiene warning.
#
# Usage: bash scripts/plan-hygiene/check_todo_format.sh [--quiet]
# Exit 0 = all canonical or only style warnings. Exit 1 = at least one NO_PRIORITY.

set -uo pipefail
QUIET="${1:-}"
PM_DIR="$(cd "$(dirname "$0")/../.." && pwd)"

SCAN_GLOBS=(
  "$PM_DIR/plans/active/*.md"
  "$PM_DIR/plans/active/issues/*.md"
)

ALLOWLIST_BASENAMES=("_agent_pings.md")

is_allowlisted() {
  local name="$1"
  if [ "${#ALLOWLIST_BASENAMES[@]}" -eq 0 ]; then return 1; fi
  for a in "${ALLOWLIST_BASENAMES[@]}"; do
    [ "$name" = "$a" ] && return 0
  done
  return 1
}

# Canonical line, sans leading "- [ ] ":
# Optional leading emoji+space (operator visual-status markers — regen tolerant).
# Optional second tag (multi-tag legal per CLAUDE.md UI HARD RULE).
CANONICAL_BODY_RE='^([^[:alnum:][:space:][]+ )?\[[A-Z][A-Z0-9_-]*\] ?(\[[A-Z][A-Z0-9_-]*\] ?)?P[0-3](\.[0-9]+)*\.'
# Any P-tag anywhere (regen ingestion test).
# NOTE: bash's =~ uses BSD regex; no \b word-boundary support. Use char-class boundaries.
# Matches: " P0 ", "P0.", "[P0]", "P0,", "P0\n" etc.
HAS_PRIORITY_RE='(^|[^A-Za-z])P[0-3]([^A-Za-z0-9]|$)'

NO_PRIORITY_COUNT=0
NON_CANONICAL_COUNT=0
NO_PRIORITY_REPORT=()
NON_CANONICAL_REPORT=()

for glob in "${SCAN_GLOBS[@]}"; do
  for f in $glob; do
    [ -f "$f" ] || continue
    base="$(basename "$f")"
    is_allowlisted "$base" && continue
    name="${f#$PM_DIR/}"
    lineno=0
    while IFS= read -r line; do
      lineno=$(( lineno + 1 ))
      [[ "$line" == "- [ ] "* ]] || continue
      body="${line#- \[ \] }"
      if [[ "$body" =~ $CANONICAL_BODY_RE ]]; then
        continue
      fi
      # Non-canonical. Further split: has priority somewhere vs. has none.
      if [[ "$body" =~ $HAS_PRIORITY_RE ]]; then
        NON_CANONICAL_REPORT+=("$name:$lineno: $line")
        NON_CANONICAL_COUNT=$(( NON_CANONICAL_COUNT + 1 ))
      else
        NO_PRIORITY_REPORT+=("$name:$lineno: $line")
        NO_PRIORITY_COUNT=$(( NO_PRIORITY_COUNT + 1 ))
      fi
    done < "$f"
  done
done

TOTAL=$(( NO_PRIORITY_COUNT + NON_CANONICAL_COUNT ))

if [ "$TOTAL" -eq 0 ]; then
  [ "$QUIET" != "--quiet" ] && echo "✅ check_todo_format: all unchecked todos canonical"
  exit 0
fi

if [ "$NO_PRIORITY_COUNT" -gt 0 ]; then
  echo "❌ check_todo_format: $NO_PRIORITY_COUNT todo(s) missing P-priority — regen assigns priority=None"
  if [ "$QUIET" != "--quiet" ]; then
    for r in "${NO_PRIORITY_REPORT[@]}"; do echo "  $r"; done
    echo ""
  fi
fi
if [ "$NON_CANONICAL_COUNT" -gt 0 ]; then
  echo "⚠️  check_todo_format: $NON_CANONICAL_COUNT todo(s) non-canonical (priority captured but format off)"
  if [ "$QUIET" != "--quiet" ]; then
    echo "Common patterns and fixes:"
    echo "  '[TAG][P<n>]'    → '[TAG] P<n>.'"
    echo "  '[TAG] [P<n>]'   → '[TAG] P<n>.'"
    echo "  '[P<n>][TAG]'    → '[TAG] P<n>.'"
    echo "  '<emoji> [TAG]'  → strip emoji prefix or keep (regen tolerant)"
    echo ""
    echo "Auto-fixer: bash scripts/plan-hygiene/fix_todo_format.sh"
    echo ""
    for r in "${NON_CANONICAL_REPORT[@]}"; do echo "  $r"; done
  fi
fi

# Hard fail only on NO_PRIORITY (the real signal-loss bug).
[ "$NO_PRIORITY_COUNT" -gt 0 ] && exit 1 || exit 0
