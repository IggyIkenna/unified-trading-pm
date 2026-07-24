#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
# Report plans exceeding line-count caps.
# Soft cap: 500L (warn). Hard cap: 1000L (fail).
# Umbrella cap: 2000L (fail) — RAISED from unlimited to 2000L (operator ruling 2026-07-23: umbrella
# plans are legitimately large trackers, but "exempt" previously meant NO ceiling at all, which let
# an umbrella plan grow unboundedly without ever failing hygiene. 2000L is still generous (2x the
# non-umbrella hard cap) but is a real ceiling — an umbrella plan over 2000L should be split, not
# left to grow forever.
# Exemption: plans with locked_by AND >100 todos (umbrella plans like writegate), OR plans that
# explicitly declare `umbrella: true` in frontmatter (added 2026-06-09). The explicit marker is
# for prose-heavy catalogue/coordinator/L3-owner plans (e.g. the per-asset-group manifest
# canonicalisation catalogues) that are legitimately large in CONTEXT but carry <100 todos, so the
# todo-count proxy misses them. `umbrella: true` is auditable (grep it) — the hygiene reviewer
# rejects a bogus marker; it is NOT a free pass to skip splitting genuinely-splittable plans.
# Usage: bash scripts/plan-hygiene/check_line_caps.sh [--quiet] [--update-baseline] [file ...]
# No files given -> full-corpus glob, gated by the shrinking-ratchet baseline (see below).
# Files given -> check ONLY those (the prek hook's STAGED plans), no baseline involved: a file
# THIS commit touches must not be over cap, full stop (RULE-11 blast-radius safety, same
# convention as check_frontmatter.sh's optional file-list arg) — pre-existing debt in files
# you're not editing is a corpus-wide concern, not this commit's.
# Exit 0 (full-corpus mode) = HARD-failure count <= baseline (see line_caps_baseline.yaml).
# Exit 1 = count exceeds baseline — a NEW plan crossed the cap, or an existing one got worse.
# This is a SHRINKING ratchet (same pattern as check_reference_paths.py/reference_paths_baseline.yaml):
# pre-existing debt from before the baseline was seeded is tolerated so this check can be a real
# hard gate without immediately blocking the shared pipeline over violations nobody introduced today.
# --update-baseline: after fixing a flagged plan, persist the new (lower) count (full-corpus mode
# only). Refuses to raise the baseline — if the live count is higher than what's on disk, the run
# still fails.

set -euo pipefail
QUIET=""
UPDATE_BASELINE=""
FILES=()
for _arg in "$@"; do
  case "$_arg" in
    --quiet) QUIET="--quiet" ;;
    --update-baseline) UPDATE_BASELINE="1" ;;
    *) FILES+=("$_arg") ;;
  esac
done
PM_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
HARD_FAILURES=0
UMBRELLA_CAP=2000
BASELINE_PATH="$(dirname "$0")/line_caps_baseline.yaml"
BASELINE_COUNT="$(grep -E '^hard_count:' "$BASELINE_PATH" | sed -E 's/^hard_count:[[:space:]]*//')"
BASELINE_COUNT="${BASELINE_COUNT:-0}"
SCOPED=""
[ "${#FILES[@]}" -gt 0 ] && SCOPED="1"

echo "Line-count check (soft=500, hard=1000, umbrella cap=${UMBRELLA_CAP}):"
echo ""

if [ -n "$SCOPED" ]; then
  TARGETS=("${FILES[@]}")
else
  TARGETS=("$PM_DIR/plans/active"/*.md)
fi

for f in "${TARGETS[@]}"; do
  name="$(basename "$f")"
  [ "$name" = "INDEX.md" ] && continue
  [[ "$name" == _* ]] && continue           # _agent_pings.md etc
  [[ "$name" == *.HANDOVER.md ]] && continue
  [ -f "$f" ] || continue                   # a staged file can be a deletion (no longer on disk)

  lines=$(wc -l < "$f")
  todos=$(grep -c "^- \[.\]" "$f" 2>/dev/null || true)
  todos="${todos:-0}"
  locked=$(awk 'NR==1{next} /^---$/{exit} /^locked_by:/{found=1} END{print (found?"yes":"no")}' "$f")
  umbrella=$(awk 'NR==1{next} /^---$/{exit} /^umbrella:[[:space:]]*true/{found=1} END{print (found?"yes":"no")}' "$f")

  # Umbrella exemption from the 500/1000 caps, but NOT from a ceiling — capped at $UMBRELLA_CAP.
  if [ "$umbrella" = "yes" ] || { [ "$locked" = "yes" ] && [ "$todos" -gt 100 ]; }; then
    if [ "$lines" -gt "$UMBRELLA_CAP" ]; then
      echo "  HARD    $name  ${lines}L  todos=${todos}  (umbrella, over ${UMBRELLA_CAP}L cap — split it)"
      HARD_FAILURES=$(( HARD_FAILURES + 1 ))
    else
      [ "$QUIET" != "--quiet" ] && [ "$lines" -gt 1000 ] && echo "  EXEMPT  $name  ${lines}L  todos=${todos}  (umbrella, under ${UMBRELLA_CAP}L cap)"
    fi
    continue
  fi

  if [ "$lines" -gt 1000 ]; then
    echo "  HARD    $name  ${lines}L  todos=${todos}"
    HARD_FAILURES=$(( HARD_FAILURES + 1 ))
  elif [ "$lines" -gt 500 ]; then
    echo "  SOFT    $name  ${lines}L  todos=${todos}"
  fi
done

echo ""

if [ -n "$SCOPED" ]; then
  if [ "$HARD_FAILURES" -gt 0 ]; then
    echo "❌ check_line_caps: ${HARD_FAILURES} staged plan(s) over cap — split before committing"
    exit 1
  fi
  [ "$QUIET" != "--quiet" ] && echo "✅ check_line_caps: staged plan(s) within cap"
  exit 0
fi

if [ "$UPDATE_BASELINE" = "1" ]; then
  if [ "$HARD_FAILURES" -gt "$BASELINE_COUNT" ]; then
    echo "❌ check_line_caps: refusing to raise baseline from ${BASELINE_COUNT} to ${HARD_FAILURES} — fix the new/worse violation(s) instead"
    exit 1
  fi
  sed -i.bak -E "s/^hard_count:.*/hard_count: ${HARD_FAILURES}/" "$BASELINE_PATH" && rm -f "${BASELINE_PATH}.bak"
  echo "Baseline updated: hard_count=${HARD_FAILURES} (was ${BASELINE_COUNT})"
  exit 0
fi

if [ "$HARD_FAILURES" -gt "$BASELINE_COUNT" ]; then
  echo "❌ check_line_caps: ${HARD_FAILURES} plan(s) over cap (baseline ${BASELINE_COUNT}) — a NEW violation landed, see plans/active/issues/plan_line_cap_remediation_2026_07_23.md"
  exit 1
elif [ "$HARD_FAILURES" -gt 0 ]; then
  [ "$QUIET" != "--quiet" ] && echo "✅ check_line_caps: ${HARD_FAILURES} pre-existing violation(s), within baseline (${BASELINE_COUNT}) — not a regression"
  exit 0
else
  [ "$QUIET" != "--quiet" ] && echo "✅ check_line_caps: no hard violations"
  exit 0
fi
