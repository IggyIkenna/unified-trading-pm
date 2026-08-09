---
doc_type: plan
title: Cross-cutting satellite AO batch 5 — finalize (reconcile source doc + archive)
summary: >-
  Gated closeout for `cross_cutting_satellite_ao_dispatch_batch5_2026_08_09.md` — machine-held via `depends_on` +
  `gate_on_depends: true` until both todos are done. Reconciles `features_service_e2e_pipeline_test_2026_05_26.md`'s
  checkboxes, then archives the batch doc via the standard 6-step ritual.
status: complete
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [cross-cutting, ao-dispatch, close-out, batch-5, satellite-docs, archival]
related:
  [
    /plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch5_2026_08_09.md,
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
    /plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch5_2026_08_09.md,
    /plans/active/features_service_e2e_pipeline_test_2026_05_26.md,
  ]
---

# Cross-cutting satellite AO batch 5 — finalize

> **ARCHIVED 2026-08-09 -- COMPLETE.** Both todos done. Todo 1 reconciled the source doc's 2 EXTRACTED pointers; todo 2
> archived `cross_cutting_satellite_ao_dispatch_batch5_2026_08_09.md` via the standard 6-step ritual, alongside this
> finalize doc, in the same commit set. Successor: none.

> **Machine-gated (historical) on `cross_cutting_satellite_ao_dispatch_batch5_2026_08_09.md`** (`depends_on` +
> `gate_on_depends: true`). `sequential: true` because archival (todo 2) had to run after reconciliation (todo 1).

## Todos

- [x] ✅ [REVIEW] P1. Reconciled `features_service_e2e_pipeline_test_2026_05_26.md`'s checkboxes against batch 5's 2
      now-done todos — flipped both corresponding "Open Track-1 todos" checkboxes (Phase A staked-basis e2e; DEFERRED
      fan-out MDPS 1h/BITGET-SPOT audit) with verified evidence cited (dry-run + `IS_TEST_RUN` write results,
      deployment-service@8f1feb4eb9e4, the 3 issue docs), and updated the matching 2026-07-27 banner items 1 + 6 to
      match. Corrected the STALE `usdc_idle_yield_apy_bps` checkbox — confirm-half was already RESOLVED per the doc's
      own 2026-08-08 round5-cross-cutting-audit note, checkbox text now scopes it to the genuinely-open wiring half
      only. Re-checked remaining open todos: 2 remain (Phase B MDPS top-up P0; the yield-stub wiring half P2) — NOT 0,
      so `status` stays `active` per the gate. — unified-trading-pm (this commit).
- [x] ✅ [DOC] P1. Archived `cross_cutting_satellite_ao_dispatch_batch5_2026_08_09.md` via the standard 6-step ritual:
      (1) verified both deferred remaining-work items from the source doc's todo 2 are already real `- [ ]` todos in
      their own filed issue docs (vm_tarball_setuptools_scm..., mdps_1h_candle_backfill_blocked...) — no prose deferral
      to migrate; (2) archive banner added to both this doc and the source doc; (3) codex-alignment check — the shipped
      `--timeframes` narrow-scope filter on `launch-mdps-backfill-vm.sh` (deployment-service@8f1feb4eb9e4) mirrors the
      launcher's existing `--data-types`/`--venues` pattern already documented generically in
      `/codex/05-infrastructure/vm-launcher-runbook.md` — no new contract, no codex change needed; (4) fixed every
      corpus referrer carrying a formal leading-slash path to the source doc: 3 issue docs' `related:` fields
      (vm_tarball_setuptools_scm_pretend_version_below_uac_floor_breaks_all_vm_launches,
      mdps_1h_candle_backfill_blocked_upstream_mtds_raw_tick_gap_bitget,
      onchain_staking_apy_bps_single_day_annualization_noise) repointed to the archive path; the source doc's own bare
      filename citations in `features_service_e2e_pipeline_test_2026_05_26.md`'s prose evidence lines were left
      unchanged (out of `check_reference_paths.py`'s scope — historical citations, same precedent as batch3's archival);
      `INDEX.md`/`active_plan_inventory_dashboard...md` are both auto-regenerated, no hand-edit needed; (5) `locked_by`
      confirmed empty on both docs; (6) both docs moved to `plans/archive/2026_08/` in this commit. — unified-trading-pm
      (this commit).

## Progress Log

- **2026-08-09 (slot 31, data_engineering)**: Todo 1 (reconciliation) was already done on arrival. Executed todo 2 — the
  6-step archival ritual — per this commit's own todo-flip evidence above. Both docs (`...batch5_2026_08_09.md` and this
  finalize doc) moved to `plans/archive/2026_08/` in the same commit set.
