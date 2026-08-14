#!/usr/bin/env bash
# Epic: agent_operating_framework_master
# Lifecycle: permanent
# Delete-when: NA
# Cheap, mechanical PROXY for "does this todo cite anything a worker can grep for" —
# tool_call_batching_authoring_gap_2026_08_14 (operator ask: "maybe theres ways to
# script more of this into lint/qg indeed").
#
# WHY THIS IS DELIBERATELY WARN-ONLY, NEVER BLOCKING (operator: "without blocking
# intended behaviour"): a todo with no backtick-quoted span is NOT necessarily bad —
# genuinely novel one-file investigations, administrative todos ("file a follow-up
# issue doc"), and operator-facing asks legitimately cite nothing grep-able. This is
# the SAME "mechanical pre-filter, not authoritative" role
# check_delete_vm_launch_gating.sh already plays for delete/VM-launch-risk tagging
# (see plan-reconcile SKILL.md hunter 5) — a human or an LLM hunter still judges each
# hit; the script only surfaces candidates cheaply so that judgment isn't the FIRST
# line of defense.
#
# What it flags: a todo's FIRST PHYSICAL LINE (task_template.md §3 — only line 1
# reaches the dispatcher) containing NO backtick-quoted span at all — task_template.md's
# own convention cites every symbol/table/endpoint/path in backticks
# (`_sweep_account`, `deepseek_message_usage`), so an entirely backtick-free todo is a
# real (if imperfect) proxy for "names a mechanism/symptom but nothing a worker can
# grep for", which guarantees an exploratory Read/Grep round-trip before any edit is
# possible (tool-call-batching.md's "authoring-time" section).
#
# Usage: bash scripts/plan-hygiene/check_todo_specificity.sh [--quiet] [file ...]
# ALWAYS exits 0 — this is advisory, never a commit blocker. Explicit file list
# (staged mode, mirrors check_todo_format.sh) scans only those files; no files given
# -> full-corpus glob.

set -uo pipefail
PM_DIR="$(cd "$(dirname "$0")/../.." && pwd)"

QUIET=""
FILES=()
for arg in "$@"; do
  case "$arg" in
    --quiet) QUIET="--quiet" ;;
    *) FILES+=("$arg") ;;
  esac
done

SCAN_GLOBS=(
  "$PM_DIR/plans/active/*.md"
  "$PM_DIR/plans/active/issues/*.md"
)

ALLOWLIST_BASENAMES=("_agent_pings.md" "task_template.md")

is_allowlisted() {
  local name="$1"
  for a in "${ALLOWLIST_BASENAMES[@]}"; do
    [ "$name" = "$a" ] && return 0
  done
  return 1
}

# A todo body containing at least one backtick-quoted span — the citation convention
# task_template.md itself uses for every symbol/table/endpoint/path reference.
HAS_BACKTICK_SPAN_RE='`[^`]+`'

FLAGGED_COUNT=0
FLAGGED_REPORT=()

SCAN_FILES=()
if [ "${#FILES[@]}" -gt 0 ]; then
  for f in ${FILES[@]+"${FILES[@]}"}; do
    case "$f" in /*) ;; *) f="$PM_DIR/$f" ;; esac
    [ -f "$f" ] || continue
    case "$f" in "$PM_DIR"/plans/active/*.md) SCAN_FILES+=("$f") ;; esac
  done
else
  for glob in "${SCAN_GLOBS[@]}"; do
    for f in $glob; do
      [ -f "$f" ] && SCAN_FILES+=("$f")
    done
  done
fi

for f in ${SCAN_FILES[@]+"${SCAN_FILES[@]}"}; do
    base="$(basename "$f")"
    is_allowlisted "$base" && continue
    name="${f#$PM_DIR/}"
    lineno=0
    while IFS= read -r line; do
      lineno=$(( lineno + 1 ))
      [[ "$line" == "- [ ] "* ]] || continue
      body="${line#- \[ \] }"
      # Skip disposition-marked todos (DEFERRED-BY-DESIGN / BLOCKED-ON / etc.) and
      # [OPERATOR]-gated ones — these are administrative by nature, citing a symbol
      # is not the point.
      case "$body" in
        *DEFERRED*|*BLOCKED-ON:*|*"[OPERATOR]"*) continue ;;
      esac
      if [[ "$body" =~ $HAS_BACKTICK_SPAN_RE ]]; then
        continue
      fi
      FLAGGED_REPORT+=("$name:$lineno: $line")
      FLAGGED_COUNT=$(( FLAGGED_COUNT + 1 ))
    done < "$f"
done

if [ "$FLAGGED_COUNT" -eq 0 ]; then
  [ "$QUIET" != "--quiet" ] && echo "✅ check_todo_specificity: every open todo cites at least one backtick-quoted symbol/path"
  exit 0
fi

echo "⚠️  check_todo_specificity: $FLAGGED_COUNT todo(s) cite no backtick-quoted symbol/file/table — likely needs an exploratory Grep before any edit is possible (advisory only, see script header)"
if [ "$QUIET" != "--quiet" ]; then
  echo "Not every hit is a real defect — a genuinely novel investigation or admin todo may legitimately cite nothing."
  echo "Judge each one; SSOT: /codex/06-coding-standards/tool-call-batching.md \"Authoring-time\" section."
  echo ""
  for r in "${FLAGGED_REPORT[@]}"; do echo "  $r"; done
fi

exit 0
