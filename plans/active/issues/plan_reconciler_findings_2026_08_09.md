---
doc_type: issue
title: "plan_reconciler daily deep reconciliation run — defi tranche, 2026-08-09"
summary: >-
  Run-findings doc for plan_reconciler dispatch agt-8af81b (slot 2, 2026-08-09), sharded to the `defi` tranche per the
  operator's 2026-08-06 sharding ruling. Corpus: 104 asset_group:defi-tagged docs (55 active/issue docs, 49 in the 12h
  grace window and read-only this run) + the defi_master epic + normative refs (PLAN_FORMAT.md / task_template.md /
  INDEX.md / ACTIVE_INDEX.md), which stay in scope for every shard.
status: open
nature: issue
asset_group: [defi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan_reconciler, reconciliation, plan-hygiene, findings, scheduled, defi]
related: []
created: "2026-08-09"
parent_epic: plan_hygiene_master
priority: P2
estimate_class: research
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 1.2
assigned_role: review
assigned_vm: planning
execution_scope: orchestrator-agent
locked_by: plan_reconciler
locked_since: "2026-08-09"
supersedes:
superseded_by:
resolved_by:
source: "slot 2, plan_reconciler agt-8af81b, 2026-08-09"
context_scope:
  [
    unified-trading-pm/scripts/plan-hygiene/run_hygiene_sweep.sh,
    unified-trading-pm/scripts/plan-hygiene/check_archive_candidates.sh,
    unified-trading-pm/agents/plan_reconciler.md,
    unified-trading-pm/cursor-configs/skills/plan-reconcile/SKILL.md,
  ]
---

# plan_reconciler run — defi tranche — 2026-08-09

Dispatch `agt-8af81b`, slot 2, tranche=defi. STEP 1 complete: all repos FF-clean to `origin/live-defi-rollout`,
`run_hygiene_sweep.sh --ci` ran clean-exit (2 hard failures, both out-of-tranche — see Coverage). Grace set: 49/104
defi-tagged docs <12h old (read-only context this run); 55 non-grace docs (~2.0MB) are the actionable set, batched into
7 hunter batches + 3 cross-cutting hunters (reconciler / codex-alignment / mechanical-adjudicator+parent_epic) for
STEP 3.

## Flips verified

_(populated in STEP 5)_

## Contradictions

_(populated in STEP 4/5)_

## Doc-drift

- `agents/plan_reconciler.md` STEP 1's discard-side-effect snippet names
  `plans/active/master_to_live_defi_2026_05_23.md` as the `--ci` regen target — that doc is already archived
  (`plans/archive/2026_07/master_to_live_defi_2026_05_23.md`). The live regen side-effect this run actually landed on
  `plans/active/INDEX.md` + `plans/archive/2026_07/active_plan_inventory_dashboard_2026_07_24.md` (discarded via
  `git checkout --`, confirmed clean tree before STEP 2b branch work began). Small stale-reference finding in a role
  file outside `plans/**` — I cannot edit it (HARD LIMITS: no touching files outside `plans/**` except reading); noting
  here for a human/follow-up to correct the STEP 1 snippet's named path.

## Hygiene fixes

_(populated in STEP 5)_

## Filed

_(populated in STEP 6)_

## Archive candidates (operator review)

_(populated in STEP 5f)_

## Refuted (dropped by verify)

_(populated in STEP 4)_

## Coverage (hunters / batches / docs)

- **Corpus**: 104 `asset_group:defi` docs (grep `^asset_group:.*defi` over `plans/active/` incl. `issues/`) — 49 grace
  (<12h, read-only), 55 non-grace (actionable), ~2.0MB. Plus `plans/epics/defi_master.md` (34 declared children) and the
  4 normative refs (corpus-wide every shard).
- **Out-of-tranche hygiene hard-fails observed (not fixed by this shard — belong to `ao`/`ci`/`cross-cutting` shards)**:
  - `check_archive_candidates.sh`: 3 new candidates vs `origin/main` —
    `ao_done_gate_no_carveout_for_red_gate_evidence_only_closure_2026_07_28.md` (asset_group=ao),
    `notify_slack_yml_fleet_rollout_scope_contradiction_2026_08_08.md` (asset_group=ci),
    `provenance_marker_broken_by_history_rewrite_blocks_promotion_2026_08_06.md` (asset_group=cross-cutting).
  - `check_effort_signal_ratchet.py`: 218 > baseline 217 — the 1 new doc is
    `test_impact_fleet_wide_measurement_and_rollout_2026_08_03.md` (asset_group=ci).
- Hunter/batch/verify counts: _(populated as STEP 3/4 complete)_

## Plans not reached

_(populated if context runs low before all confirmed items are applied)_
