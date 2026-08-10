---
doc_type: plan
title: Cross-cutting satellite AO batch 11 — finalize (reconcile source doc + archive)
summary: >-
  Gated closeout for `cross_cutting_satellite_ao_dispatch_batch11_2026_08_09.md` — machine-held via `depends_on` +
  `gate_on_depends: true` until all 11 todos are done. Reconciles the source doc's checkboxes (incl. the flagged
  stale-Kalshi-checkbox re-verification), then archives the batch doc via the standard 6-step ritual.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [cross-cutting, ao-dispatch, close-out, batch-11, satellite-docs, archival]
related:
  [
    /plans/active/cross_cutting_satellite_ao_dispatch_batch11_2026_08_09.md,
    /plans/active/mtds_venue_backfill_and_ops_hardening_residuals_2026_07_24.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.32
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [cross_cutting_satellite_ao_dispatch_batch11_2026_08_09]
gate_on_depends: true
source: >-
  round11 RECLASSIFY + satellite-batch-extraction sweep 2026-08-09, per `task_template.md` §4's finalize-plan-coverage
  rule.
assigned_role: data_engineering
effort: medium
sequential: true
drift_direction: advance-code
context_scope:
  [
    /plans/active/cross_cutting_satellite_ao_dispatch_batch11_2026_08_09.md,
    /plans/active/mtds_venue_backfill_and_ops_hardening_residuals_2026_07_24.md,
  ]
---

# Cross-cutting satellite AO batch 11 — finalize

> **Machine-gated on `cross_cutting_satellite_ao_dispatch_batch11_2026_08_09.md`** (`depends_on` +
> `gate_on_depends: true`). `sequential: true` because archival (todo 2) must run after reconciliation (todo 1).

## Todos

- [ ] [REVIEW] P2. Reconcile `mtds_venue_backfill_and_ops_hardening_residuals_2026_07_24.md`'s checkboxes against batch
      11's 11 now-done todos — flip each corresponding checkbox, citing the shipped commit(s)/evidence (verify before
      citing; do not assume batch 11's wording matches the source doc's exact todo verbatim, re-read both). Also
      re-verify the flagged "Wire Kalshi into the pipeline" checkbox against current manifest state (per batch 11's
      "Flagged, not extracted" section) and flip or annotate it accordingly. Re-check for 0 remaining open todos in the
      source doc after flipping (unlikely — it has ~10 other genuinely credential/dependency/design-gated open items);
      do not archive the source doc unless it genuinely reaches 0. Done when: the source doc's corresponding checkboxes
      (incl. the Kalshi one) are flipped or annotated with verified evidence.
- [ ] [DOC] P2. Archive `cross_cutting_satellite_ao_dispatch_batch11_2026_08_09.md` via the standard 6-step ritual once
      todo 1 is done: archive banner → codex-alignment check → fix every corpus referrer → clear `locked_by` (confirm
      already empty). Done when: the plan is moved to `plans/archive/2026_08/`, every referrer resolves to the new path,
      and this finalize doc archives alongside it in the same commit.

## Progress Log
