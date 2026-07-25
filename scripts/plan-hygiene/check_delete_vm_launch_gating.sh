#!/usr/bin/env bash
# Epic: agent_operating_framework_master
# Lifecycle: permanent
# Delete-when: NA
# Delete/VM-launch todo-tagging gate (task_template.md §3 finding O, 2026-07-25) — a scoped
# /plan-reconcile pass across all 5 AGs' AO-dispatch batches found 8 of ~15 batch docs contain a
# GCS delete/--apply mutation and 5 contain a VM launch, with no systematic check that each is
# correctly tagged (only that SOME [OPERATOR] tag existed somewhere in the doc). This is a cheap,
# MECHANICAL soft-warn signal only — it cannot judge whether a todo's self-justification is actually
# sound (that is content judgment, not regex-decidable); real adjudication is /plan-reconcile's
# AO-dispatch-readiness hunter (delete-risk / VM-launch-risk tagging consistency). This script's job
# is narrower: flag a CANDIDATE todo for that hunter (or a human) to look at, never to block a commit
# on its own — hence `soft`, unlike the hard structural gates in run_hygiene_sweep.sh.
# Scope: only AO-dispatched docs (assigned_vm: planning) — a LOCAL/human plan's deletes/VM-launches
# are run by a human directly, so tagging discipline doesn't apply the same way.
# Usage: check_delete_vm_launch_gating.sh [--quiet] [files...]
#   no files -> scans every plans/active/*.md with `assigned_vm: planning` in its frontmatter
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PM_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

QUIET=0
FILES=()
for a in "$@"; do
  case "$a" in
    --quiet) QUIET=1 ;;
    *) FILES+=("$a") ;;
  esac
done
if [ "${#FILES[@]}" -eq 0 ]; then
  while IFS= read -r f; do
    grep -q '^assigned_vm: planning' "$f" 2>/dev/null && FILES+=("$f")
  done < <(find "$PM_DIR/plans/active" -maxdepth 1 -name '*.md' 2>/dev/null)
fi

# Signal a todo is delete/VM-launch-risky: a GCS delete/--apply mutation, or launching a VM.
RISK_PAT='(--apply|gcs_delete_object|gsutil rm|gcloud storage rm| delete \+ | delete/purge|launch-[a-z-]+\.sh|gcloud compute instances create)'
# Signal it's already covered: an explicit operator gate, a stated safe-idempotent-pattern phrase, or
# the risky verb explicitly negated (dry-run-only / no --apply / read-only / diagnose-only work).
SAFE_PAT='(\[OPERATOR\]|delete-safety-protocol|idempotent|copy.{0,10}verify.{0,10}delete|human-only|already-established|no operator gate needed|Operator-owned|dry-run|no \`?--apply\`?|without \`?--apply\`?|read-only|no new VM launch|BLOCKED-OPERATOR)'

RC=0
for f in "${FILES[@]}"; do
  [ -f "$f" ] || continue
  # Extract each todo block: a "- [ ]" line through the next "- [ ]"/"- [x]"/blank-then-heading line.
  BLOCK=""
  FLAGGED=""
  while IFS= read -r line; do
    if [[ "$line" =~ ^-\ \[\ \] ]]; then
      if [ -n "$BLOCK" ] && [[ "$BLOCK" =~ $RISK_PAT ]] && ! [[ "$BLOCK" =~ $SAFE_PAT ]]; then
        FLAGGED="${FLAGGED}$(printf '%s\n' "$BLOCK" | head -1)"$'\n'
      fi
      BLOCK="$line"
    elif [[ "$line" =~ ^[[:space:]] ]] && [ -n "$BLOCK" ]; then
      BLOCK="${BLOCK}"$'\n'"${line}"
    else
      if [ -n "$BLOCK" ] && [[ "$BLOCK" =~ $RISK_PAT ]] && ! [[ "$BLOCK" =~ $SAFE_PAT ]]; then
        FLAGGED="${FLAGGED}$(printf '%s\n' "$BLOCK" | head -1)"$'\n'
      fi
      BLOCK=""
    fi
  done < "$f"
  if [ -n "$BLOCK" ] && [[ "$BLOCK" =~ $RISK_PAT ]] && ! [[ "$BLOCK" =~ $SAFE_PAT ]]; then
    FLAGGED="${FLAGGED}$(printf '%s\n' "$BLOCK" | head -1)"$'\n'
  fi
  if [ -n "$FLAGGED" ]; then
    RC=1
    if [ "$QUIET" -eq 0 ]; then
      echo "⚠️  candidate delete/VM-launch todo(s) with no [OPERATOR] tag or safe-pattern justification in $f:"
      printf '%s' "$FLAGGED" | sed 's/^/    /'
    fi
  fi
done

if [ "$RC" -eq 0 ] && [ "$QUIET" -eq 0 ]; then
  echo "✅ every delete/VM-launch todo in ${#FILES[@]} AO-dispatched plan(s) is tagged or self-justified"
fi
exit "$RC"
