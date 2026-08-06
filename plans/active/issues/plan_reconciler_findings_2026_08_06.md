---
doc_type: issue
title: Prediction-tranche /plan-reconcile run (2026-08-06, agt-65e60a) — findings + fixes
summary: >-
  Sharded plan_reconciler daily deep-reconciliation pass scoped to the `prediction` topic tranche (52-doc corpus: 17
  primary prediction plans, 27 issue docs, 8 cross-tagged with sports/cefi/defi/tradfi). Multi-agent fan-out DETECT
  (epic/topic/mechanical/missed-flip/AO-dispatch-readiness/zero-checkbox hunters) followed by adversarial VERIFY
  (independent refuter + confirmer per candidate) before any fix applied. This doc is both the run's progress journal
  and its human-readable report — updated incrementally as checkpoints land.
status: open
nature: issue
asset_group: [prediction]
stage: [meta]
scope: [engineer, admin]
repos: [unified-trading-pm]
tags: [prediction, plan-reconcile, plan_reconciler, contradiction, codex-alignment, audit, sharded]
related: [plans/active/prediction_consolidated_closeout_2026_07_18.md, cursor-configs/skills/plan-reconcile/SKILL.md]
created: 2026-08-06
parent_epic: predictions_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
source:
  'scheduled dispatch — POST /api/plan-health/dispatch {"mode": "reconcile", "tranche": "prediction"},
  dispatch_id=agt-65e60a'
locked_by:
drift_direction: advance-code
depends_on: []
resolved_by:
---

# Prediction-tranche plan_reconciler run — 2026-08-06 (agt-65e60a)

Scope: `asset_group` frontmatter containing `prediction` across `plans/active/*.md` + `plans/active/issues/*.md` (52
docs). Normative refs (`PLAN_FORMAT.md`/`task_template.md`/`INDEX.md`/`ACTIVE_INDEX.md`) and codex stay in scope per the
sharded-run contract. 17/52 docs are in the 12h GRACE WINDOW (read-only context this run, listed below) — newest git
change <12h old at run start (2026-08-06 20:33 UTC).

**Grace set (read-only this run):** ag_closeout_audit_rollout_2026_07_25.md,
issues/ag_closeout_audit_prediction_parked_2026_07_31.md,
issues/coverage_floor_registries_no_cross_propagation_2026_07_17.md,
issues/features_delta_one_dependency_checker_prediction_bucket_token_wrong_2026_07_27.md,
issues/instrument_availability_hive_migration_unrecognized_shapes_and_content_mismatch_2026_08_03.md,
issues/instrument_availability_league_and_question_group_partition_shapes_2026_08_03.md,
issues/instruments_docs_audit_outstanding_items_2026_07_08.md, issues/instruments_remaining_work_audit_2026_07_10.md,
issues/kalshi_execution_credential_secret_name_mismatch_2026_07_26.md,
issues/mtds_qg_red_uac_capability_declaration_drift_2026_08_05.md,
issues/prediction_phantom_reconciler_wipes_bundle_atom_2026_07_10.md, prediction_consolidated_closeout_2026_07_18.md,
prediction_satellite_ao_dispatch_batch4_2026_07_26.md, prediction_satellite_ao_dispatch_batch6_2026_07_29.md,
prediction_satellite_ao_dispatch_batch7_2026_08_04.md, prediction_satellite_ao_dispatch_batch7_2026_08_04_finalize.md,
sports_predictions_live_mode_activation_readiness_2026_07_21.md.

**Corpus-wide mechanical hygiene checks (ref-paths/ag-closeout-linkage/terminal-status-archived/archive-candidates) were
run and checked for prediction-tranche hits: ZERO** — the 4 corpus-wide hard failures on today's sweep all land in other
tranches (verified by grep against each check's itemized output). This tranche's own hygiene contribution is clean;
findings below come from the contradiction/false-unchecked/zero-checkbox sweep phases instead.

## Flips verified

(updated as STEP 5 applies confirmed missed-flips)

## Contradictions

(updated as STEP 4 confirms candidates)

## Doc-drift

(updated as STEP 4 confirms plan↔codex drift)

## Hygiene fixes

(updated as STEP 5 applies mechanical fixes)

## Filed

(updated as STEP 6 routes hard items)

## Archive candidates (operator review)

(updated as STEP 5f identifies verified-done unlocked plans)

## Refuted (dropped by verify)

(updated as STEP 4 drops unconfirmed candidates)

## Coverage (hunters / batches / docs)

(updated at STEP 7)

## Plans not reached

(updated if context runs low before full coverage)
