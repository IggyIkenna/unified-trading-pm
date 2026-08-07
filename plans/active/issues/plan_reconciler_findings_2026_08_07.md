---
doc_type: issue
title: "plan_reconciler run findings — 2026-08-07 — tranche: prediction (agt-e7f024)"
summary: >-
  Run-findings doc / progress journal for the 2026-08-07 `plan_reconciler` deep reconciliation pass, sharded to the
  `prediction` topic tranche (dispatch agt-e7f024, slot 9). Scope: the 26 primary prediction-tranche docs (25 active
  plans/issues + the predictions_master epic hub) plus the corpus-wide normative refs (PLAN_FORMAT.md, task_template.md,
  INDEX.md, ACTIVE_INDEX.md) and codex as evidence. Appended to as the run progresses.
status: open
nature: issue
asset_group: [prediction]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-hygiene, plan-reconcile, reconciliation, prediction, sharded-run]
related: [/plans/epics/predictions_master.md, /plans/active/prediction_consolidated_closeout_2026_07_18.md]
created: 2026-08-07
author: plan_reconciler
parent_epic: predictions_master
priority: P2
assigned_vm: NA
execution_scope: local-only
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: NA
drift_direction: none
source: "plan_reconciler autonomous run, 2026-08-07, slot-9, dispatch agt-e7f024, tranche=prediction"
depends_on: []
resolved_by:
locked_by:
context_scope:
  [
    /plans/epics/predictions_master.md,
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
    /plans/PLAN_FORMAT.md,
    /plans/active/task_template.md,
  ]
supersedes:
superseded_by:
---

# plan_reconciler run — 2026-08-07 — tranche: prediction

## Run context

- Dispatch: `agt-e7f024`, slot 9, `POST /api/plan-health/dispatch {"mode": "reconcile", "tranche": "prediction"}`.
- **PM_REPO_PATH note**: the boot message's `$PM_REPO_PATH` pointed at the canonical ROOT clone
  (`/home/ubuntu/unified-trading-system-repos/unified-trading-pm`), which the same boot message's own GUARDRAIL marks
  READ-ONLY ("root-clone reads are READ-ONLY. ALL work happens inside your assigned slot directory"). The root clone was
  also independently confirmed dirty (checked out on a different agent's `plan_reconciler/agt-a304c9` branch with
  staged/untracked files) — clearly another in-flight session. This run instead operates entirely in the slot-local
  sibling clone `.tabs/9/unified-trading-pm` (own `.git`, on `live-defi-rollout`, verified clean at start), consistent
  with `agents/RULES.md` §1. Flagging this as a dispatch-payload discrepancy worth fixing at the source (see Filed).
- **Scope derivation**: primary prediction-tranche docs = `parent_epic: predictions_master` OR filename prefix
  `prediction_`/`predictions_` OR single-AG `asset_group: [prediction]`. 26 docs (25 active plans/issues + the
  `predictions_master` epic). Excluded as NOT primary (cross-tagged but owned elsewhere): 4 `sports_*` docs + 1 sports
  issue doc (parent_epic: sports_master, sports-first tag — sports tranche's job); ~18 genuinely cross-AG docs (4-6
  asset_groups spanning cefi/defi/tradfi/sports/prediction, parent_epic in {agent_operating_framework_master,
  infrastructure_master, instruments_master, manifest_master, cefi_master}) — read as context when cited by a prediction
  doc, never treated as owned/fixable by this shard. Normative refs (`PLAN_FORMAT.md`, `task_template.md`, `INDEX.md`,
  `ACTIVE_INDEX.md`) + codex stay in scope as evidence per the skill's sharded-run contract.
- **Phase-0 entry hygiene sweep** (`run_hygiene_sweep.sh --ci --no-regen`): 4 hard failures corpus-wide (reference-path
  ratchet 83/92 over baseline 81/86, AG-closeout-linkage 77 orphans over baseline 69, terminal-status-archived 5
  violations over baseline 0, archive-candidates 11 over baseline 0) + 1 soft warning (delete/VM-launch tagging).
  **Checked every itemized violation against the prediction-tranche doc list: ZERO overlap** — none of the 5
  terminal-status docs, 11 archive-candidates, or the `check_ag_closeout_linkage.py` orphan list name a prediction doc;
  the 3 `check_reference_paths.py` hits naming "prediction" are all under `plans/audit/**` (outside this skill's audited
  corpus of `plans/{active,active/issues,epics}`). These 4 hard-gate failures are corpus-wide standing conditions owned
  by other tranches' reconciler runs / `/archive-candidates-audit` — noted here for the record, not this shard's job to
  fix, consistent with the sharded-run contract (audit your own tranche's docs).
- **Grace set** (newest commit <12h old — read-only this run, 7 of 26):
  `ag_closeout_audit_prediction_parked_2026_07_31.md` (5h),
  `features_delta_one_dependency_checker_prediction_bucket_token_wrong_2026_07_27.md` (5h),
  `kalshi_execution_credential_secret_name_mismatch_2026_07_26.md` (8h),
  `prediction_phantom_reconciler_wipes_bundle_atom_2026_07_10.md` (5h), `prediction_consolidated_closeout_2026_07_18.md`
  (5h), `prediction_satellite_ao_dispatch_batch4_2026_07_26.md` (2h),
  `prediction_satellite_ao_dispatch_batch7_2026_08_04.md` (9h).

## Flips verified

(none yet)

## Contradictions

(none yet)

## Doc-drift

(none yet)

## Hygiene fixes

(none yet)

## Filed

(none yet)

## Archive candidates (operator review)

(none yet)

## Refuted (dropped by verify)

(none yet)

## Coverage (hunters / batches / docs)

(none yet — Phase 1 not yet dispatched)

## Plans not reached

(none yet)
