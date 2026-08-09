---
doc_type: plan
title: Cross-cutting satellite AO batch 5 — finalize (reconcile source doc + archive)
summary: >-
  Gated closeout for `cross_cutting_satellite_ao_dispatch_batch5_2026_08_09.md` — machine-held via `depends_on` +
  `gate_on_depends: true` until both todos are done. Reconciles `features_service_e2e_pipeline_test_2026_05_26.md`'s
  checkboxes, then archives the batch doc via the standard 6-step ritual.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [cross-cutting, ao-dispatch, close-out, batch-5, satellite-docs, archival]
related:
  [
    /plans/active/cross_cutting_satellite_ao_dispatch_batch5_2026_08_09.md,
    /plans/active/features_service_e2e_pipeline_test_2026_05_26.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: features_and_ml_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [cross_cutting_satellite_ao_dispatch_batch5_2026_08_09]
gate_on_depends: true
source: >-
  Satellite-batch-extraction sweep 2026-08-09, per `task_template.md` §4's finalize-plan-coverage rule.
assigned_role: data_engineering
effort: high
sequential: true
drift_direction: advance-code
context_scope:
  [
    /plans/active/cross_cutting_satellite_ao_dispatch_batch5_2026_08_09.md,
    /plans/active/features_service_e2e_pipeline_test_2026_05_26.md,
  ]
---

# Cross-cutting satellite AO batch 5 — finalize

> **Machine-gated on `cross_cutting_satellite_ao_dispatch_batch5_2026_08_09.md`** (`depends_on` +
> `gate_on_depends: true`). `sequential: true` because archival (todo 2) must run after reconciliation (todo 1).

## Todos

- [x] ✅ [REVIEW] P1. Reconciled `features_service_e2e_pipeline_test_2026_05_26.md`'s checkboxes against batch 5's 2
      now-done todos — flipped both corresponding "Open Track-1 todos" checkboxes (Phase A staked-basis e2e; DEFERRED
      fan-out MDPS 1h/BITGET-SPOT audit) with verified evidence cited (dry-run + `IS_TEST_RUN` write results,
      deployment-service@8f1feb4eb9e4, the 3 issue docs), and updated the matching 2026-07-27 banner items 1 + 6 to
      match. Corrected the STALE `usdc_idle_yield_apy_bps` checkbox — confirm-half was already RESOLVED per the doc's
      own 2026-08-08 round5-cross-cutting-audit note, checkbox text now scopes it to the genuinely-open wiring half
      only. Re-checked remaining open todos: 2 remain (Phase B MDPS top-up P0; the yield-stub wiring half P2) — NOT 0,
      so `status` stays `active` per the gate. — unified-trading-pm (this commit).
- [ ] [DOC] P1. Archive `cross_cutting_satellite_ao_dispatch_batch5_2026_08_09.md` via the standard 6-step ritual once
      todo 1 is done: archive banner → codex-alignment check → fix every corpus referrer → clear `locked_by` (confirm
      already empty). Done when: the plan is moved to `plans/archive/2026_08/`, every referrer resolves to the new path,
      and this finalize doc archives alongside it in the same commit.

## Progress Log
