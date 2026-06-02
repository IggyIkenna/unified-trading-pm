#!/usr/bin/env bash
# Deterministic plan-health digest builder (for the daily Plan Health Agent GHA).
#
# Does ALL the heavy lifting deterministically — plan counts, the canonical hygiene
# sweep (frontmatter / todo-format / line-caps / SSOT plan formatting), and the
# archive-candidate × locked_by cross-reference — so the downstream Haiku agent only
# has to do the ONE thing a script cannot: cross-plan contradiction detection.
#
# Outputs:
#   - $1 (digest file, default plan_health_digest.md): full markdown report
#   - stdout: a single line "SUMMARY=<one-liner>" suitable for a Slack/CI message
#
# Counts are SCRIPTED here (never let the LLM guess "104 vs 107 plans").
#
# Usage: bash scripts/plan-hygiene/build_health_digest.sh [digest_out.md]
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PM_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PM_DIR" || exit 1
DIGEST="${1:-plan_health_digest.md}"

# ── Deterministic counts ────────────────────────────────────────────────────
ACTIVE_TOP=$(find plans/active -maxdepth 1 -name '*.md' 2>/dev/null | wc -l | tr -d ' ')
ACTIVE_ALL=$(find plans/active -name '*.md' 2>/dev/null | wc -l | tr -d ' ')
ISSUES=$(find plans/active/issues -name '*.md' 2>/dev/null | wc -l | tr -d ' ')

# ── Canonical hygiene sweep (frontmatter / todo-format / line-caps / etc.) ──
SWEEP=$(bash "$SCRIPT_DIR/run_hygiene_sweep.sh" 2>&1)
HARD=$(printf '%s\n' "$SWEEP" | sed -n 's/.*Hard failures: \([0-9]*\).*/\1/p' | tail -1)
SOFT=$(printf '%s\n' "$SWEEP" | sed -n 's/.*Soft warnings: \([0-9]*\).*/\1/p' | tail -1)
HARD="${HARD:-?}"; SOFT="${SOFT:-?}"
RESULTS=$(printf '%s\n' "$SWEEP" | grep -E '✅ PASS|❌ FAIL|⚠️  WARN' || true)
INV=$(printf '%s\n' "$SWEEP" | grep 'Regenerated inventory:' | tail -1)

# ── Archive candidates × locked_by cross-reference (fully deterministic) ─────
CANDIDATES=$(printf '%s\n' "$SWEEP" | grep 'status=active' | awk '{print $1}')
CAND_COUNT=$(printf '%s\n' "$CANDIDATES" | grep -c . || true)
LOCKED=0; UNLOCKED=0; UNLOCKED_LIST=""
while IFS= read -r f; do
  [ -z "$f" ] && continue
  path="plans/active/$f"
  [ -f "$path" ] || path=$(find plans/active -name "$f" 2>/dev/null | head -1)
  [ -f "$path" ] || continue
  if grep -qE '^locked_by:[[:space:]]*\S' "$path"; then
    LOCKED=$((LOCKED + 1))
  else
    UNLOCKED=$((UNLOCKED + 1))
    UNLOCKED_LIST="${UNLOCKED_LIST}- ${f}"$'\n'
  fi
done <<< "$CANDIDATES"

# ── INDEX.md ↔ active-plans reconciliation (deterministic) ──────────────────
# INDEX.md itself is NOT a plan, but it should accurately list the active plan set.
# Flag drift: active plans missing from the index, and index entries pointing at a
# plan that no longer lives in plans/active/ (top-level, excluding INDEX/template).
INDEX="plans/active/INDEX.md"
MISSING_FROM_INDEX=""
STALE_IN_INDEX=""
INDEX_DRIFT=0
if [ -f "$INDEX" ]; then
  # Active plan files actually on disk (exclude non-plan files: INDEX, template,
  # README, and ledgers / scratch files like _agent_pings.md).
  ACTIVE_FILES=$(find plans/active -maxdepth 1 -name '*.md' \
    ! -name 'INDEX.md' ! -name 'task_template.md' ! -name 'README*.md' ! -name '_*.md' \
    -exec basename {} \; | sort -u)
  # Markdown-link targets in INDEX whose path does NOT point at the archive → active refs.
  INDEX_ACTIVE_REFS=$(grep -oE '\]\([^)]+\.md\)' "$INDEX" \
    | sed -E 's/^\]\(//; s/\)$//' | grep -v 'archive' | xargs -n1 basename 2>/dev/null | sort -u)

  while IFS= read -r f; do
    [ -z "$f" ] && continue
    grep -qxF "$f" <<< "$INDEX_ACTIVE_REFS" || { MISSING_FROM_INDEX="${MISSING_FROM_INDEX}- ${f}"$'\n'; INDEX_DRIFT=$((INDEX_DRIFT + 1)); }
  done <<< "$ACTIVE_FILES"

  while IFS= read -r f; do
    [ -z "$f" ] && continue
    [ -f "plans/active/$f" ] || { STALE_IN_INDEX="${STALE_IN_INDEX}- ${f}"$'\n'; INDEX_DRIFT=$((INDEX_DRIFT + 1)); }
  done <<< "$INDEX_ACTIVE_REFS"
fi

# ── Write the markdown digest ───────────────────────────────────────────────
{
  echo "## Plan Health — deterministic digest"
  echo ""
  echo "**Active plans:** ${ACTIVE_TOP} top-level (${ACTIVE_ALL} incl. subdirs; ${ISSUES} in issues/)"
  echo ""
  echo "**Hygiene sweep:** ${HARD} hard failure(s) · ${SOFT} soft warning(s)"
  echo ""
  echo '```'
  echo "${RESULTS}"
  echo '```'
  echo ""
  echo "**Inventory:** ${INV:-n/a}"
  echo ""
  echo "**Archive candidates (all todos done):** ${CAND_COUNT} — ${LOCKED} locked / ${UNLOCKED} archivable"
  if [ "${UNLOCKED}" -gt 0 ]; then
    echo ""
    echo "Archivable now (complete + unlocked):"
    echo ""
    printf '%s' "${UNLOCKED_LIST}"
  fi
  echo ""
  echo "**INDEX.md ↔ active-plans drift:** ${INDEX_DRIFT}"
  if [ -n "${MISSING_FROM_INDEX}" ]; then
    echo ""
    echo "Active plans missing from INDEX.md:"
    echo ""
    printf '%s' "${MISSING_FROM_INDEX}"
  fi
  if [ -n "${STALE_IN_INDEX}" ]; then
    echo ""
    echo "INDEX.md entries with no matching active plan (stale):"
    echo ""
    printf '%s' "${STALE_IN_INDEX}"
  fi
} > "$DIGEST"

# ── One-line summary for Slack / CI message ─────────────────────────────────
echo "SUMMARY=${ACTIVE_TOP} active plans | hygiene ${HARD} hard / ${SOFT} soft | ${CAND_COUNT} archive-candidate(s) (${LOCKED} locked, ${UNLOCKED} archivable) | INDEX drift ${INDEX_DRIFT}"
