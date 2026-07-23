#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
# Plan hygiene sweep — run by Ikenna and Harsh on the planning VM as a morning step.
# Runs all checks in sequence; prints a PASS/FAIL table.
# Hard checks: todo regression, frontmatter. Soft checks: line caps, archive candidates.
# Usage: bash scripts/plan-hygiene/run_hygiene_sweep.sh [--ci] [--no-regen] [--precommit]
#   --ci:        exit 1 on any hard failure (for cron/CI); default is interactive (always exits 0)
#   --no-regen:  skip the active-plan inventory regeneration step. Use when the sweep is called
#                from a READ-ONLY context (e.g. plan-reconciler STEP 1 input gather) where dirtying
#                master_to_live_defi_2026_05_23.md is undesirable. Flags may be combined: --ci --no-regen.
#   --precommit: lean, fast, LOCAL-only gate for the prek hook (fires on staged plans/**) —
#                runs ONLY the three local hard checks (frontmatter / todo-format / runbook-fields),
#                NO origin fetch (todo-regression), NO soft/advisory checks, NO inventory regen, so a
#                plan-touching commit is gated in <1s. The origin-compare + advisory checks stay at
#                the daily cron / CI sweep, never pre-commit. Exit 1 on any hard failure.

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PM_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

CI_MODE=""
NO_REGEN=""
for _arg in "$@"; do
  case "$_arg" in
    --ci)        CI_MODE="--ci" ;;
    --no-regen)  NO_REGEN="1" ;;
    --precommit) CI_MODE="--precommit" ;;
  esac
done

# ── --precommit: lean STAGED-FILES-ONLY local gate (prek hook) — bypass the heavy sweep body ──
# Validates ONLY the files THIS commit stages, so a pre-existing violation in an unrelated
# plan (e.g. another agent's WIP) never blocks your commit (RULE-11 blast-radius safety). Portable
# for macOS bash 3.2 (no mapfile). Gates the staged-capable HARD checks: frontmatter + todo-format
# on staged plans/**, frontmatter-schema on ALL staged codex/** (parity with CI's lint-codex slice,
# which schema-checks the whole corpus), runbook-fields on staged codex/15-runbooks/incidents/**.
if [ "$CI_MODE" = "--precommit" ]; then
  # --precommit never regenerates inventory (read-only by design)
  STAGED_PLANS=()
  STAGED_RUNBOOKS=()
  STAGED_CODEX=()
  while IFS= read -r line; do
    case "$line" in
      plans/*.md) STAGED_PLANS+=("$PM_DIR/$line") ;;
      codex/*.md)
        # EVERY staged codex doc gets the frontmatter-schema gate (below); runbook incidents
        # ALSO get the runbook-fields gate. Order-independent — a doc can be in both lists.
        STAGED_CODEX+=("$PM_DIR/$line")
        case "$line" in codex/15-runbooks/incidents/*.md) STAGED_RUNBOOKS+=("$PM_DIR/$line") ;; esac
        ;;
    esac
  done < <(git -C "$PM_DIR" diff --cached --name-only --diff-filter=ACM -- plans/ codex/ 2>/dev/null)
  if [ "${#STAGED_PLANS[@]}" -eq 0 ] && [ "${#STAGED_RUNBOOKS[@]}" -eq 0 ] && [ "${#STAGED_CODEX[@]}" -eq 0 ]; then
    echo "plan-hygiene pre-commit: no staged plan/runbook/codex files — skip."
    exit 0
  fi
  PF=0
  if [ "${#STAGED_PLANS[@]}" -gt 0 ]; then
    "$SCRIPT_DIR/check_frontmatter.sh" --quiet "${STAGED_PLANS[@]}" && echo "  ✅ Frontmatter validity (staged plans)" || { echo "  ❌ Frontmatter validity (staged plans)"; PF=$(( PF + 1 )); }
    # Value-level schema gate (required NON-EMPTY fields + epic resolution) on the SAME staged
    # plans. check_frontmatter.sh above is presence-only ('---' + deprecated-field), so without this
    # a docs(plans): commit (which takes prek only, NOT full QG) can land a plan/issue doc missing
    # required status/priority on the integration branch — where it then blocks EVERY full QG run
    # fleet-wide. Running the schema check here closes that bypass at commit time. SSOT: check_frontmatter_schema.py.
    python3 "$SCRIPT_DIR/check_frontmatter_schema.py" --quiet "${STAGED_PLANS[@]}" && echo "  ✅ Frontmatter schema (staged plans)" || { echo "  ❌ Frontmatter schema — missing/empty required field (staged plans)"; PF=$(( PF + 1 )); }
    "$SCRIPT_DIR/check_todo_format.sh" --quiet "${STAGED_PLANS[@]}" && echo "  ✅ Todo format (staged plans)" || { echo "  ❌ Todo format (staged plans)"; PF=$(( PF + 1 )); }
    # Conflict-marker gate — catches committed git markers incl. mid-line + prettier-mangled
    # (`> > > > > > >`) forms the other checks miss (see check_conflict_markers.sh, 2026-06-21).
    "$SCRIPT_DIR/check_conflict_markers.sh" --quiet "${STAGED_PLANS[@]}" && echo "  ✅ No conflict markers (staged plans)" || { echo "  ❌ Conflict marker(s) in staged plans — resolve before commit"; PF=$(( PF + 1 )); }
    # Prettier emphasis-mangling gate — blocks landing underscore-identifiers rewritten as
    # asterisks by prettier <3.9.5 (data*type, asset*group, ...). Backstop to the >=3.9.5
    # version guard in scripts/hooks/prettier-autostage.sh. SSOT + repair recipe:
    # plans/active/issues/prettier_emphasis_mangling_corpus_corruption_2026_07_14.md
    "$SCRIPT_DIR/check_prettier_mangling.sh" --quiet "${STAGED_PLANS[@]}" && echo "  ✅ No prettier mangling (staged plans)" || { echo "  ❌ Prettier emphasis-mangling in staged plans — run: bash scripts/plan-hygiene/check_prettier_mangling.sh <file> for lines + see the corruption issue doc for the repair recipe"; PF=$(( PF + 1 )); }
  fi
  if [ "${#STAGED_RUNBOOKS[@]}" -gt 0 ]; then
    python3 "$SCRIPT_DIR/check_runbook_fields.py" --quiet "${STAGED_RUNBOOKS[@]}" && echo "  ✅ Runbook fields (staged runbooks)" || { echo "  ❌ Runbook governance fields (staged runbooks)"; PF=$(( PF + 1 )); }
  fi
  if [ "${#STAGED_CODEX[@]}" -gt 0 ]; then
    # The SAME value-level schema gate CI's lint-codex slice runs over the WHOLE codex corpus,
    # scoped here to THIS commit's staged codex docs. Closes the prek bypass for codex/** (not just
    # plans/**): a docs commit (prek-only, NOT full QG) that adds/edits a codex doc with a
    # missing/empty required field (e.g. a codex-ssot lacking a present-but-empty `referenced_by`)
    # used to land on the integration branch and then fail EVERY full QG fleet-wide. SSOT:
    # check_frontmatter_schema.py (the exact checker the lint-codex slice invokes).
    python3 "$SCRIPT_DIR/check_frontmatter_schema.py" --quiet "${STAGED_CODEX[@]}" && echo "  ✅ Frontmatter schema (staged codex)" || { echo "  ❌ Frontmatter schema — missing/empty required field (staged codex)"; PF=$(( PF + 1 )); }
    "$SCRIPT_DIR/check_conflict_markers.sh" --quiet "${STAGED_CODEX[@]}" && echo "  ✅ No conflict markers (staged codex)" || { echo "  ❌ Conflict marker(s) in staged codex — resolve before commit"; PF=$(( PF + 1 )); }
    "$SCRIPT_DIR/check_prettier_mangling.sh" --quiet "${STAGED_CODEX[@]}" && echo "  ✅ No prettier mangling (staged codex)" || { echo "  ❌ Prettier emphasis-mangling in staged codex — see plans/active/issues/prettier_emphasis_mangling_corpus_corruption_2026_07_14.md for the repair recipe"; PF=$(( PF + 1 )); }
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
run_check "No conflict markers (mid-line + mangled)" hard "$SCRIPT_DIR/check_conflict_markers.sh"
run_check "No prettier emphasis-mangling"    hard "$SCRIPT_DIR/check_prettier_mangling.sh"
# depends_on was SEEDED by fix_frontmatter.py but never VALIDATED — nothing checked the graph
# itself. A cycle (A->B->A) gates archival forever (CLAUDE.md: depends_on gates archival), so
# neither plan can ever close: silent permanent stasis, no error. Whole-graph check, so it lives
# in the full sweep, not the staged-files-only --precommit path. Corpus proven clean (0 cycles,
# 0 self-deps) before this was made hard. SSOT: check_depends_on_graph.py.
run_check "depends_on DAG (cycles + self-deps)" hard python3 "$SCRIPT_DIR/check_depends_on_graph.py" --quiet
# Reference path convention (/plans/... + /codex/... leading-slash, operator ruling
# 2026-07-23) — a shrinking-ratchet baseline (reference_paths_baseline.yaml), same shape
# as the fallback-import/DTZ ratchets: hard-fails only on a NEW violation above the
# pre-existing count, never on the corpus's existing debt. Supersedes check_codex_refs.sh's
# narrower existence-only scope (kept below for its standalone fast path).
run_check "Reference path convention (/plans, /codex — ratchet)" hard python3 "$SCRIPT_DIR/check_reference_paths.py" --quiet
run_check "Line caps (500 soft/1000 hard/2000 umbrella)" soft "$SCRIPT_DIR/check_line_caps.sh"
run_check "Estimate sanity (±20% drift)"     soft "$SCRIPT_DIR/check_estimate_sanity.sh"
run_check "Superseded plans in active/"      soft "$SCRIPT_DIR/check_superseded_in_active.sh"
run_check "Codex path refs resolve (legacy, subset of the ratchet check above)" soft "$SCRIPT_DIR/check_codex_refs.sh"
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
if [ -n "$NO_REGEN" ]; then
  echo "  ⏭  skipped (--no-regen)"
else
  cd "$PM_DIR" && python3 scripts/plans/regenerate_active_plan_inventory.py 2>&1 | tail -5 || echo "⚠️ regenerator failed"
fi

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
