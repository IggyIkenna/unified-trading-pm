---
doc_type: issue
title: "Plan reconciler findings — prediction tranche 2026-08-11"
summary: "Daily deep reconciliation pass for the prediction tranche (sharded run, DISPATCH_ID=agt-9625bc). Large grace set — most prediction docs touched in last 12h. Non-grace prediction-primary docs with open todos: 7."
status: active
nature: audit
asset_group: [prediction]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [plan_reconciler, reconciliation, prediction, sharded]
related: [plan_reconciler.md]
created: 2026-08-11
author: plan_reconciler
source: agt-9625bc
locked_by: plan_reconciler
---

# Plan reconciler findings — prediction tranche 2026-08-11

**Run**: `agt-9625bc`, sharded (prediction only), 2026-08-11
**Corpus**: 79 docs matching `asset_group:.*prediction` (including multi-AG docs); ~50 non-grace docs reached by grep
**Grace set**: Large — most prediction docs modified <12h ago. READ-ONLY this run.

## Hygiene sweep (Phase 0)

2 hard failures (ratchet gates, not prediction-specific):
- ❌ No prettier proseWrap continuation-padding (ratchet)
- ❌ assigned_vm:NA corpus size (docs + open todos, ratchet)

292 active plans, 0 orphans, 67% done overall, 255 cal AI-days left.

## Non-grace prediction-primary docs (writable this run)

| Doc | Age | Status | VM | Open | Done | Locked |
|-----|-----|--------|----|------|------|--------|
| prediction_satellite_ao_dispatch_batch7_2026_08_04_finalize.md | 109h | active | planning | 2 | 0 | no |
| prediction_phase_e_football_arb_live_2026_07_24.md | 17h | active | - | 3 | 2 | no |
| prediction_phase_c_data_status_ui_2026_07_24.md | 17h | active | - | 2 | 2 | no |
| prediction_phase_d_formal_smoke_and_backfill_2026_07_24.md | 17h | active | - | 5 | 6 | no |
| predictions_ml_walk_forward_and_arb_2026_06_20.md | 17h | active | NA | 4 | 5 | locked_by: live-defi-rollout |
| data_completion_prediction_2026_07_15.md | 17h | active | NA | 18 | 5 | locked_by: (empty) |
| prediction_capture_incident_remediation_2026_07_06.md | 12h | active | - | 7 | 15 | no |

## Flips verified

(To be populated)

## Contradictions

(To be populated)

## Doc-drift

(To be populated)

## Hygiene fixes

(To be populated)

## Filed

(To be populated)

## Archive candidates (operator review)

(To be populated)

## Refuted (dropped by verify)

(To be populated)

## Coverage (hunters / batches / docs)

(To be populated)

## Plans not reached

(To be populated)

## Codex corrections applied (mechanical, evidence-cited)

(To be populated)
