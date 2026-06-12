#!/usr/bin/env bash
# Plan hygiene sweep — run by Ikenna and Harsh on the planning VM as a morning step.
# Runs all checks in sequence; prints a PASS/FAIL table.
# Hard checks: todo regression, frontmatter. Soft checks: line caps, archive candidates.
# Usage: bash scripts/plan-hygiene/run_hygiene_sweep.sh [--ci|--precommit]
#   --ci:        exit 1 on any hard failure (for cron/CI); default is interactive (always exits 0)
#   --precommit: lean, fast, LOCAL-only gate for the prek hook (fires on staged plans/**) —
#                runs ONLY the three local hard checks (frontmatter / todo-format / runbook-fields),
#                NO origin fetch (todo-regression), NO soft/advisory checks, NO inventory regen, so a
#                plan-touching commit is gated in <1s. The origin-compare + advisory checks stay at
#                the daily cron / CI sweep, never pre-commit. Exit 1 on any hard failure.

set -uo pipefail
CI_MODE="${1:-}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PM_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

# ── --precommit: lean STAGED-FILES-ONLY local gate (prek hook) — bypass the heavy sweep body ──
# Validates ONLY the files THIS commit stages, so a pre-existing violation in an unrelated
# plan (e.g. another agent's WIP) never blocks your commit (RULE-11 blast-radius safety). Portable
# for macOS bash 3.2 (no mapfile). Gates all three staged-capable HARD checks: frontmatter +
# todo-format on staged plans/**, runbook-fields on staged codex/15-runbooks/incidents/**.
if [ "$CI_MODE" = "--precommit" ]; then
  STAGED_PLANS=()
  STAGED_RUNBOOKS=()
  while IFS= read -r line; do
    case "$line" in
      plans/*.md) STAGED_PLANS+=("$PM_DIR/$line") ;;
      codex/15-runbooks/incidents/*.md) STAGED_RUNBOOKS+=("$PM_DIR/$line") ;;
    esac
  done < <(git -C "$PM_DIR" diff --cached --name-only --diff-filter=ACM -- plans/ codex/15-runbooks/incidents/ 2>/dev/null)
  if [ "${#STAGED_PLANS[@]}" -eq 0 ] && [ "${#STAGED_RUNBOOKS[@]}" -eq 0 ]; then
    echo "plan-hygiene pre-commit: no staged plan/runbook files — skip."
    exit 0
  fi
  PF=0
  if [ "${#STAGED_PLANS[@]}" -gt 0 ]; then
    "$SCRIPT_DIR/check_frontmatter.sh" --quiet "${STAGED_PLANS[@]}" && echo "  ✅ Frontmatter (staged plans)" || { echo "  ❌ Frontmatter validity (staged plans)"; PF=$(( PF + 1 )); }
    "$SCRIPT_DIR/check_todo_format.sh" --quiet "${STAGED_PLANS[@]}" && echo "  ✅ Todo format (staged plans)" || { echo "  ❌ Todo format (staged plans)"; PF=$(( PF + 1 )); }
  fi
  if [ "${#STAGED_RUNBOOKS[@]}" -gt 0 ]; then
    python3 "$SCRIPT_DIR/check_runbook_fields.py" --quiet "${STAGED_RUNBOOKS[@]}" && echo "  ✅ Runbook fields (staged runbooks)" || { echo "  ❌ Runbook governance fields (staged runbooks)"; PF=$(( PF + 1 )); }
  fi
  if [ "$PF" -gt 0 ]; then
    echo "❌ plan-hygiene pre-commit: $PF hard failure(s) in STAGED files — fix before commit (fixable frontmatter: python3 scripts/plan-hygiene/fix_frontmatter.py; todo format: bash scripts/plan-hygiene/fix_todo_format.sh)."
    exit 1
  fi
  echo "✅ plan-hygiene pre-commit: staged files clean."
  exit 0
fi

HARD_FAIL=0
SOFT_WARN=0
RESULTS=()

run_check() {
  local label="$1"
  local kind="$2"   # hard | soft
  shift 2
  local cmd=("$@")

  if "${cmd[@]}" --quiet 2>/dev/null; then
    RESULTS+=("  ✅ PASS  [$kind]  $label")
  else
    if [ "$kind" = "hard" ]; then
      RESULTS+=("  ❌ FAIL  [$kind]  $label")
      HARD_FAIL=$(( HARD_FAIL + 1 ))
    else
      RESULTS+=("  ⚠️  WARN  [$kind]  $label")
      SOFT_WARN=$(( SOFT_WARN + 1 ))
    fi
  fi
}

echo "========================================"
echo " Plan Hygiene Sweep — $(date -u '+%Y-%m-%d %H:%M UTC')"
echo "========================================"
echo ""

run_check "Todo regression vs origin"       hard "$SCRIPT_DIR/check_todo_regression.sh"
run_check "Frontmatter validity"             hard "$SCRIPT_DIR/check_frontmatter.sh"
run_check "Todo format (priority + canonical)" hard "$SCRIPT_DIR/check_todo_format.sh"
run_check "Runbook governance fields"        hard python3 "$SCRIPT_DIR/check_runbook_fields.py"
run_check "Line caps (500 soft/1000 hard)"   soft "$SCRIPT_DIR/check_line_caps.sh"
run_check "Estimate sanity (±20% drift)"     soft "$SCRIPT_DIR/check_estimate_sanity.sh"
run_check "Superseded plans in active/"      soft "$SCRIPT_DIR/check_superseded_in_active.sh"
run_check "Codex path refs resolve"          soft "$SCRIPT_DIR/check_codex_refs.sh"
run_check "Parent-epic alignment (keyword)"  soft python3 "$SCRIPT_DIR/check_parent_epic_alignment.py"
run_check "CLAUDE↔SUB_AGENT topic parity"    soft "$SCRIPT_DIR/check_claude_subagent_parity.sh"

# Archive candidates is informational — always "passes"
echo ""
echo "--- Archive candidates ---"
bash "$SCRIPT_DIR/check_archive_candidates.sh" || true

# Model-tier coverage is informational — surfaces opus-candidates + plans on the
# silent Sonnet default for human review (SSOT: codex/06-coding-standards/model-tier-selection.md).
echo ""
echo "--- Model-tier coverage (advisory) ---"
cd "$PM_DIR" && python3 scripts/plans/audit_model_tier.py 2>&1 \
  | grep -E "active plans:|declare model_tier:|opus-candidates:|mismatch:|⬅ OPUS" || true

echo ""
echo "--- Results ---"
for r in "${RESULTS[@]}"; do
  echo "$r"
done

echo ""
echo "--- Inventory regenerator ---"
cd "$PM_DIR" && python3 scripts/plans/regenerate_active_plan_inventory.py 2>&1 | tail -5 || echo "⚠️ regenerator failed"

echo ""
echo "========================================"
echo " Hard failures: $HARD_FAIL  |  Soft warnings: $SOFT_WARN"
echo "========================================"

if [ "$CI_MODE" = "--ci" ] && [ "$HARD_FAIL" -gt 0 ]; then
  echo ""
  echo "❌ Sweep FAILED — fix hard failures before proceeding."
  exit 1
fi

if [ "$HARD_FAIL" -gt 0 ]; then
  echo ""
  echo "⚠️  Fix hard failures before picking up new work."
fi

exit 0
