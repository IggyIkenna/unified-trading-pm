#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
# Find plan/issue docs with 0 open todos and >0 done todos, still sitting in plans/active/ or
# plans/active/issues/ instead of plans/archive/ (a done doc whose status/archival was simply
# never flipped — the recurring gap CLAUDE.md's archival rule calls out: "A plan with every todo
# done + unlocked MUST be archived immediately (HARD RULE, recurring gap)"). This is DISTINCT from
# check_terminal_status_archived.py, which only catches a doc whose status ALREADY says
# resolved/complete but never got physically moved — this check catches the doc BEFORE that,
# where status was never flipped away from open/active at all.
#
# Was purely informational (`|| true` in run_hygiene_sweep.sh), never scanned plans/active/
# issues/ at all, AND used `grep -P` (Perl regex) — which silently fails with "invalid option"
# on plain BSD grep (macOS default /usr/bin/grep) outside an interactive shell that happens to
# alias grep to a PCRE-capable tool. That meant every non-interactive invocation (CI, prek,
# run_hygiene_sweep.sh's own subprocess, plain `bash check_archive_candidates.sh`) silently saw
# EVERY file's counts default to empty/0 via the `|| true` fallback, regardless of the real
# corpus — i.e. this check has likely NEVER actually found a real candidate outside an
# interactive session with a PCRE-aliased grep, since it was first written. THREE real gaps,
# all found + fixed 2026-07-29 (see
# plans/archive/issues/code_quick_cross_repo_fix_backlog_2026_07_28.md's Progress Log for the
# investigation): (1) advisory-only, (2) missing plans/active/issues/, (3) non-portable `-P`.
# Now uses portable POSIX ERE (`grep -E` + `[[:space:]]`, works on both BSD and GNU grep) and is
# a SHRINKING ratchet, same shape as check_terminal_status_archived.py / check_line_caps.sh /
# check_na_corpus_ratchet.py: pre-existing candidates are tolerated so this can be a real hard
# gate without blocking the shared pipeline over debt nobody introduced today. A live count
# EXCEEDING the baseline means a NEW done-but-unarchived doc landed — fix it (run the canonical
# archival ritual: flip status to a terminal value, add the archive banner, git mv to
# plans/archive/[issues/], fix every corpus referrer), never raise the number.
#
# locked_by docs are excluded from the count (they cannot be archived without [unlock-plan]
# regardless of todo state, so flagging them would be a false positive the operator can't act on).
#
# Docs gating a `depends_on` + `gate_on_depends: true` finalize plan are ALSO excluded (found
# 2026-07-29, plan_health escalation triage): the `<X>_finalize_<date>.md` companion pattern
# (cefi/ao/prediction/tradfi/sports satellite_ao_dispatch batches, bucket-fold plans, etc. all use
# it) makes archiving the base plan ITS OWN gated todo — the finalize plan reconciles source docs
# + re-checks deferred items FIRST, then archives the base plan as its last step. A base plan with
# 0 open todos of its own but a still-active finalize companion isn't forgotten, it's mid-chain;
# flagging it is the same false-positive shape as an un-actionable locked_by doc.
#
# Usage: bash scripts/plan-hygiene/check_archive_candidates.sh [--quiet] [--update-baseline]
# Exit 0 = candidate count <= baseline. Exit 1 = count exceeds baseline (a NEW candidate appeared).
# --update-baseline: after archiving flagged docs, persist the new (lower) count. Refuses to raise
# the baseline — if the live count is higher than what's on disk, the run still fails.

set -uo pipefail
QUIET=""
UPDATE_BASELINE=""
for _arg in "$@"; do
  case "$_arg" in
    --quiet) QUIET="1" ;;
    --update-baseline) UPDATE_BASELINE="1" ;;
  esac
done

PM_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
BASELINE_PATH="$(dirname "$0")/archive_candidates_baseline.yaml"
BASELINE_COUNT="$(grep -E '^candidate_count:' "$BASELINE_PATH" 2>/dev/null | sed -E 's/^candidate_count:[[:space:]]*//')"
BASELINE_COUNT="${BASELINE_COUNT:-0}"

CANDIDATES=0
FOUND=()

# Precompute every slug named in some doc's `depends_on: [...]` WHERE that doc also declares
# `gate_on_depends: true` — a single O(n) pass instead of an O(n^2) nested scan. Space-padded so
# the main loop's substring test below can't false-match a slug that's a suffix of another.
GATED_SLUGS=" "
for g in "$PM_DIR/plans/active"/*.md "$PM_DIR/plans/active/issues"/*.md; do
  [ -f "$g" ] || continue
  grep -qE '^gate_on_depends:[[:space:]]*true' "$g" 2>/dev/null || continue
  deps_line="$(grep -E '^depends_on:' "$g" 2>/dev/null | head -1)"
  [ -z "$deps_line" ] && continue
  for slug in $(echo "$deps_line" | grep -oE '[A-Za-z0-9_-]+'); do
    [ "$slug" = "depends_on" ] && continue
    GATED_SLUGS="${GATED_SLUGS}${slug} "
  done
done

for f in "$PM_DIR/plans/active"/*.md "$PM_DIR/plans/active/issues"/*.md; do
  [ -f "$f" ] || continue
  name="$(basename "$f")"
  [ "$name" = "INDEX.md" ] && continue
  [ "$name" = "task_template.md" ] && continue
  case "$name" in
    *.HANDOVER.md) continue ;;
    _*) continue ;;
  esac

  locked_by="$(grep -E '^locked_by:' "$f" 2>/dev/null | head -1 | sed -E 's/^locked_by:[[:space:]]*//')"
  [ -n "$locked_by" ] && continue

  slug="${name%.md}"
  case "$GATED_SLUGS" in
    *" ${slug} "*) continue ;;
  esac

  open_count="$(grep -cE '^[[:space:]]*- \[ \]' "$f" 2>/dev/null)"
  open_count="${open_count:-0}"
  done_count="$(grep -cE '^[[:space:]]*- \[x\]' "$f" 2>/dev/null)"
  done_count="${done_count:-0}"

  if [ "$open_count" -eq 0 ] && [ "$done_count" -gt 0 ]; then
    status="$(grep '^status:' "$f" 2>/dev/null | head -1 | sed 's/status: //')"
    status="${status:-unknown}"
    FOUND+=("${f#"$PM_DIR"/}  done=${done_count}  status=${status}")
    CANDIDATES=$(( CANDIDATES + 1 ))
  fi
done

if [ -z "$QUIET" ]; then
  echo "Archive candidates (0 open todos, all work done, unlocked):"
  echo ""
  if [ "${#FOUND[@]}" -gt 0 ]; then
    for line in "${FOUND[@]}"; do
      echo "  $line"
    done
  fi
  echo ""
fi

OK=1
[ "$CANDIDATES" -gt "$BASELINE_COUNT" ] && OK=0

if [ -z "$QUIET" ]; then
  if [ "$OK" -eq 1 ]; then
    echo "✅ check_archive_candidates: ${CANDIDATES} candidate(s) (baseline ${BASELINE_COUNT})"
  else
    echo "❌ check_archive_candidates: ${CANDIDATES} candidate(s) (baseline ${BASELINE_COUNT}) — a NEW done-but-unarchived doc landed. Archive it: flip status to a terminal value, add the archive banner, git mv to plans/archive/[issues/], fix corpus referrers. Never raise the baseline."
  fi
fi

if [ -n "$UPDATE_BASELINE" ]; then
  NEW_COUNT="$CANDIDATES"
  if [ "$BASELINE_COUNT" -gt 0 ] && [ "$NEW_COUNT" -gt "$BASELINE_COUNT" ]; then
    NEW_COUNT="$BASELINE_COUNT"
  fi
  cat > "$BASELINE_PATH" <<EOF
# Baseline for check_archive_candidates.sh — no plan/issue doc with 0 open todos and >0 done
# todos (and not locked_by someone) may sit in plans/active/ or plans/active/issues/ indefinitely
# without being archived (operator finding 2026-07-29 — see
# plans/archive/issues/code_quick_cross_repo_fix_backlog_2026_07_28.md's Progress Log for the
# investigation: three real gaps — advisory-only (\`|| true\`), never scanned
# plans/active/issues/, and non-portable \`grep -P\` that silently failed outside an interactive
# PCRE-aliased shell).
#
# This is a SHRINKING ratchet (same shape as terminal_status_archived_baseline.yaml /
# line_caps_baseline.yaml / na_corpus_baseline.yaml). candidate_count is the number of
# pre-existing done-but-unarchived docs the gate tolerates. A live count EXCEEDING this fails the
# check — a NEW one landed without being archived, fix it (archive it), don't raise the number.
# LOWER it (re-run --update-baseline) as candidates get archived. NEVER hand-raise it.
candidate_count: ${NEW_COUNT}
EOF
  [ -z "$QUIET" ] && echo "Baseline updated: ${NEW_COUNT}"
fi

exit $(( 1 - OK ))
