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
  # Separate, filter-unrestricted detection of "did this commit touch plans/ at all" — deliberately
  # NOT the --diff-filter=ACM loop above, because a plan ARCHIVAL is a `git mv` and git's default
  # rename detection reports that as status R, which --diff-filter=ACM excludes. A pure archival
  # commit (git mv plans/active/X.md -> plans/archive/.../X.md, no other plan file touched) would
  # leave STAGED_PLANS empty and skip the whole precommit gate below — exactly the commit shape that
  # needs the broken-link check (see the corpus-wide link check below).
  PLANS_TOUCHED=""
  if git -C "$PM_DIR" diff --cached --name-only -- plans/ 2>/dev/null | grep -q .; then
    PLANS_TOUCHED=1
  fi
  if [ "${#STAGED_PLANS[@]}" -eq 0 ] && [ "${#STAGED_RUNBOOKS[@]}" -eq 0 ] && [ "${#STAGED_CODEX[@]}" -eq 0 ] && [ -z "$PLANS_TOUCHED" ]; then
    echo "plan-hygiene pre-commit: no staged plan/runbook/codex files — skip."
    exit 0
  fi
  PF=0
  if [ -n "$PLANS_TOUCHED" ]; then
    # Corpus-wide broken-link check (not staged-files-only — a link's target can be ANY plan under
    # plans/active/ or plans/archive/, not just the files this commit stages). Fires on every commit
    # that adds/edits/renames anything under plans/, which is exactly what makes this the fast local
    # failure for the archiving agent instead of a fleet-wide QG-red discovered days later by an
    # unrelated worker (unified-trading-pm/plans/active/issues/
    # consolidated_closeout_plans_stale_archive_referrer_links_fleetwide_qg_block_2026_07_25.md).
    python3 "$SCRIPT_DIR/../validators/validate_plan_links.py" --quiet --workspace-root "$(dirname "$PM_DIR")" \
      && echo "  ✅ No broken links (plans/active/*.md, corpus-wide)" \
      || { echo "  ❌ Broken relative link(s) in plans/active/*.md — a referenced doc likely moved/archived without its referrers' paths being updated (CLAUDE.md § 'Plans' archival ritual step 5: 'update every referrer's path corpus-wide')"; PF=$(( PF + 1 )); }
  fi
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
    # Line-cap gate on staged plans ONLY — absolute bar (same model as frontmatter/todo-format
    # above, not a baseline delta): if a plan you're touching is over cap, split/trim it before
    # this commit lands, regardless of whether YOUR edit made it worse. No origin fetch, so it
    # stays in the <1s precommit budget. The corpus-wide ratchet (line_caps_baseline.yaml) is a
    # separate, full-sweep-only check for debt in files nobody is actively editing.
    "$SCRIPT_DIR/check_line_caps.sh" --quiet "${STAGED_PLANS[@]}" && echo "  ✅ Line caps (staged plans)" || { echo "  ❌ Line cap exceeded in a staged plan — split it (bash scripts/plan-hygiene/check_line_caps.sh <file> for detail)"; PF=$(( PF + 1 )); }
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
# Broken relative links (plans/active/*.md -> a doc that moved to plans/archive/... without the
# referrer's path being updated) — the same check the --precommit fast path runs on any staged
# plans/ change, run here too so the operator's daily sweep catches drift from commits that landed
# before this gate existed. SSOT: validate_plan_links.py (also invoked fleet-wide by every repo's
# quality-gates.sh via run_validators.py — this is the LOCAL, fast-failure counterpart).
run_check "No broken links (plans/active/*.md, corpus-wide)" hard python3 "$SCRIPT_DIR/../validators/validate_plan_links.py"
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
# AG-closeout linkage (operator request 2026-07-25) — every single-asset-group plan/issue
# doc must have a findable path (related: graph, either direction, or a body-text mention)
# to its AG's consolidated closeout plan, so a finding can never silently become an
# orphan nothing will ever pick up. Same shrinking-ratchet shape as the two checks above
# (ag_closeout_linkage_baseline.yaml): hard-fails only on a NEW orphan, never on debt.
run_check "AG-closeout linkage (single-AG docs -> consolidated closeout, ratchet)" hard python3 "$SCRIPT_DIR/check_ag_closeout_linkage.py" --quiet
# Terminal-status-archived (operator finding 2026-07-25) — no plan/issue doc with a TERMINAL
# status (issue: resolved/false-positive/superseded; plan: complete/superseded/cancelled) may
# sit in plans/active/ or plans/active/issues/ instead of plans/archive/ — this is
# codex/11-project-management/issue-doc-lifecycle.md's archive-on-resolve rule, now
# machine-enforced after its manual audit recipe was found to be silently dead (grepped a
# frontmatter field the schema no longer has). Same shrinking-ratchet shape as the two checks
# above (terminal_status_archived_baseline.yaml): hard-fails only on a NEW unarchived
# terminal-status doc, never on the pre-existing backlog being cleared by
# terminal_status_archival_backlog_sweep_2026_07_25.md.
run_check "Terminal-status-archived (plan/issue docs -> plans/archive/, ratchet)" hard python3 "$SCRIPT_DIR/check_terminal_status_archived.py" --quiet
# Line caps (plans 500 soft/1000 hard; epics 2000 hard flat, NO umbrella-exemption escape hatch —
# operator ruling 2026-07-24) — flipped from advisory to a real hard gate 2026-07-24 via the SAME
# shrinking-ratchet shape as the reference-path check above (line_caps_baseline.yaml): hard-fails
# only on a NEW over-cap plan/epic (or an existing one getting worse) above the pre-existing count,
# never on the debt plan_line_cap_remediation_2026_07_23.md didn't finish cleaning up. Lower the
# baseline as each remaining flagged plan/epic is split/trimmed; it should reach 0.
run_check "Line caps (plans 500/1000, epics 2000 — no exemption, ratchet)" hard "$SCRIPT_DIR/check_line_caps.sh" --quiet
run_check "Estimate sanity (±20% drift)"     soft "$SCRIPT_DIR/check_estimate_sanity.sh"
run_check "Superseded plans in active/"      soft "$SCRIPT_DIR/check_superseded_in_active.sh"
run_check "Codex path refs resolve (legacy, subset of the ratchet check above)" soft "$SCRIPT_DIR/check_codex_refs.sh"
run_check "Parent-epic alignment (keyword)"  soft python3 "$SCRIPT_DIR/check_parent_epic_alignment.py"
run_check "CLAUDE↔SUB_AGENT topic parity"    soft "$SCRIPT_DIR/check_claude_subagent_parity.sh"
# Delete/VM-launch todo tagging (task_template.md §3 finding O, 2026-07-25) — mechanical candidate
# signal only, feeds /plan-reconcile's AO-dispatch-readiness hunter for real judgment; soft because
# a regex cannot decide whether a self-justification is actually sound.
run_check "Delete/VM-launch todo tagging (AO plans, candidate signal)" soft "$SCRIPT_DIR/check_delete_vm_launch_gating.sh"

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
