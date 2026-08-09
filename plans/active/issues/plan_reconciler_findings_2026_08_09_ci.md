---
doc_type: issue
title: "plan_reconciler daily deep reconciliation run — ci tranche, 2026-08-09"
summary: >-
  Run-findings doc for plan_reconciler dispatch agt-c80749 (slot 15, 2026-08-09), sharded to the `ci` topic tranche per
  the 2026-08-06 operator ruling (Sun-Fri per-tranche shards, Saturday whole-corpus). Corpus: 59 active+issue docs
  tagged `asset_group: ci` (~1.85MB); 24 (41%) are in the 12h grace window and read-only this run, leaving 35 non-grace
  docs (~1.16MB) as the actionable set. Normative refs (PLAN_FORMAT.md/task_template.md/INDEX.md/ACTIVE_INDEX.md) and
  codex stay in scope per the sharded-run contract.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan_reconciler, reconciliation, plan-hygiene, findings, scheduled, ci]
related: []
created: "2026-08-09"
parent_epic: plan_hygiene_master
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.5
assigned_role: review
assigned_vm: planning
execution_scope: orchestrator-agent
locked_by: plan_reconciler
locked_since: "2026-08-09"
supersedes:
superseded_by:
resolved_by:
source: "slot 15, plan_reconciler agt-c80749, 2026-08-09"
context_scope:
  [
    unified-trading-pm/scripts/plan-hygiene/run_hygiene_sweep.sh,
    unified-trading-pm/scripts/plan-hygiene/check_archive_candidates.sh,
    unified-trading-pm/agents/plan_reconciler.md,
    unified-trading-pm/cursor-configs/skills/plan-reconcile/SKILL.md,
  ]
drift_direction: advance-code
depends_on: []
---

# plan_reconciler run — 2026-08-09 (agt-c80749, ci tranche)

## Scope + method

- `TRANCHE=ci` supplied → sharded run over `asset_group: ci` docs only (the 2026-08-06 operator-ruled Sun-Fri
  per-tranche cadence). Normative refs + codex stay in scope per the sharded-run contract even though this is a topic
  shard.
- Corpus: 59 active+issue docs tagged `asset_group: ci` (~1.85MB total).
- Grace set (newest commit <12h old at run start, 2026-08-09T02:54Z): 24 of 59 docs (41%). Read-only context this run.
- Non-grace actionable set: 35 docs (~1.16MB), batched into 5 hunter batches (~235KB each).
- `ci_consolidated_closeout_2026_07_25.md` (the tranche's former epic hub) is already archived
  (`plans/archive/2026_07/`) — `asset_group: ci` is filtered directly per the SKILL's tranche mechanism, no live epic
  hub dependency.
- 3 non-grace ci docs carry `locked_by: live-defi-rollout` (real locks, never auto-archived/unlocked this run):
  `ui_build_warm_cache_2026_06_17.md`, `issues/quickmerge_environment_autodetect_forces_dev_off_main_2026_07_25.md`,
  `issues/uac_value_only_config_change_breaks_utl_untested_2026_07_20.md`.

## Flips verified

_(populated in STEP 5)_

## Archived (verified-done, unlocked, non-grace)

_(populated in STEP 5)_

## Contradictions

_(populated in STEP 4/5)_

## Doc-drift

_(populated in STEP 4/6)_

## Hygiene fixes

_(populated in STEP 5)_

## Filed

_(populated in STEP 6)_

## Archive candidates (operator review)

_(populated in STEP 5)_

## Refuted (dropped by verify)

_(populated in STEP 4)_

## Coverage (hunters / batches / docs)

_(populated in STEP 7)_

## Plans not reached

_(populated if applicable)_
