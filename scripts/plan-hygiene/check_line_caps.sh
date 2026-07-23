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
# Usage: bash scripts/plan-hygiene/check_line_caps.sh [--quiet]
# Exit 0 = no hard violations. Exit 1 = one or more plans over cap (1000L non-umbrella, 2000L umbrella).

set -euo pipefail
QUIET="${1:-}"
PM_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
HARD_FAILURES=0
UMBRELLA_CAP=2000

echo "Line-count check (soft=500, hard=1000, umbrella cap=${UMBRELLA_CAP}):"
echo ""

for f in "$PM_DIR/plans/active"/*.md; do
  name="$(basename "$f")"
  [ "$name" = "INDEX.md" ] && continue
  [[ "$name" == _* ]] && continue           # _agent_pings.md etc
  [[ "$name" == *.HANDOVER.md ]] && continue

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
if [ "$HARD_FAILURES" -gt 0 ]; then
  echo "❌ check_line_caps: ${HARD_FAILURES} plan(s) over cap (1000L hard / ${UMBRELLA_CAP}L umbrella)"
  exit 1
else
  [ "$QUIET" != "--quiet" ] && echo "✅ check_line_caps: no hard violations"
  exit 0
fi
