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

- [x] ✅ [REVIEW] P2. Reconcile `mtds_venue_backfill_and_ops_hardening_residuals_2026_07_24.md`'s checkboxes against
      batch 11's 11 now-done todos — flipped all 11 corresponding checkboxes + the Kalshi checkbox (12 total), each
      citing the actual shipped commit(s)/verification evidence (re-read both docs; matched by content, not verbatim
      wording). Re-verified "Wire Kalshi into the pipeline" against CURRENT code (not just the two cited docs):
      confirmed `kalshi.py` fully implements RSA-PSS signing + MTDS carries `get_trades_with_status` + 4 live WS
      connectors + a bulk-ingest script — flipped as done. Re-checked remaining open count: **9 open todos remain**
      (genuinely credential/dependency/design-gated) — source doc does NOT reach 0, does NOT archive. Repo:
      unified-trading-pm (docs).
- [ ] [DOC] P2. Archive `cross_cutting_satellite_ao_dispatch_batch11_2026_08_09.md` via the standard 6-step ritual once
      todo 1 is done: archive banner → codex-alignment check → fix every corpus referrer → clear `locked_by` (confirm
      already empty). Done when: the plan is moved to `plans/archive/2026_08/`, every referrer resolves to the new path,
      and this finalize doc archives alongside it in the same commit.

## Progress Log

- **2026-08-11 (slot 3, backend_engineer)**: todo 1 done — reconciled all 11 batch-11 done-todos + the flagged Kalshi
  checkbox against `mtds_venue_backfill_and_ops_hardening_residuals_2026_07_24.md`. Source doc has 9 open todos
  remaining (genuinely gated), so it does not archive. Todo 2 (archive batch-11 itself) is now unblocked — next.
