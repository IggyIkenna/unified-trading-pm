---
doc_type: plan
title:
  Colocated feature pipeline — in-memory DAG handoff, parquet consolidation, read-time pruning, basedpyright strictness
  restore
summary:
  Land deferred colocated feature pipeline I/O efficiency items (in-memory DAG handoff, parquet consolidation, column
  pruning) and restore features-service basedpyright strictness.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [features-service]
scope: [engineer, admin]
tags: [features, pipeline, in-memory, parquet, basedpyright, efficiency, colocated]
related:
  [
    /plans/epics/features_and_ml_master.md,
    /plans/archive/2026_06/features_calc_efficiency_and_correctness_2026_05_27.md,
  ]
created: "2026-06-21"
parent_epic: features_and_ml_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P3
estimate_class: design
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 3.0
last_updated: 2026-07-27
locked_by: live-defi-rollout
locked_since: 2026-06-21
supersedes:
superseded_by:
depends_on:
source:
assigned_role: data_engineering
drift_direction: advance-code
---

# Colocated feature pipeline — in-memory handoff + I/O efficiency + basedpyright strictness restore

> **MIGRATED FROM:** `features_calc_efficiency_and_correctness_2026_05_27.md` (archived 2026-06-21). That plan shipped
> the feature-calc efficiency + correctness work; these four items were deferred there (1.3b/1.4/1.5b behind a "revisit
> after end-to-end" gate, and 1.7e behind an operator "dedicated session" gate) with placeholder/un-filed successors.
> Consolidated here so they have a real owning plan.

## Objective

Land the deferred colocated-feature-pipeline I/O efficiency items (in-memory DAG handoff, one-parquet-per-(day,fg,tf)
consolidation, read-time column pruning) **and** restore features-service basedpyright strictness (the `reportUnknown*`
severities were weakened to `"none"`, masking 574 errors).

## Todos

> **Status update (2026-07-27, vintage-audit re-verification):** items 1.4, 1.3b, and 1.7e were confirmed extracted
> verbatim into `plans/active/cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md` (part 1 of 2, ~L113-125), as a
> single combined `[DESIGN] P2` todo ("Land colocated feature pipeline in-memory DAG handoff + parquet consolidation +
> basedpyright strictness restore") with its own done-when criteria. **Marked SUPERSEDED-BY-BATCH1 below** so nobody
> dispatches both copies — the 3 checkboxes below stay open here as the bookkeeping record until batch1 executes and
> ships, at which point flip both this doc's and batch1's copies together citing the same commit sha(s). Item 1.5b
> (column pruning) was NOT migrated anywhere — confirmed still genuinely gated (see its own note below).

- [ ] [DESIGN] P3. **1.4 — feature dependency DAG handoff in-memory** — pass derived feature frames between calculators
      in-process instead of round-tripping through parquet, so a colocated feature run computes the dependency DAG once.
      Repo: features-service. **MIGRATED FROM:** `features_calc_efficiency_and_correctness` item 1.4.
      **SUPERSEDED-BY-BATCH1 (2026-07-27):** dispatched verbatim in
      `plans/active/cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md` (~L113-125, part of the combined
      in-memory-DAG-handoff todo) — do not dispatch a second copy from here.
- [ ] [REFACTOR] P3. **1.3b — one parquet per (day, feature_group, timeframe)** — consolidate the per-instrument parquet
      fan-out into a single file per (day,fg,tf) to cut object count + selective-read list cost. Repo: features-service.
      **MIGRATED FROM:** item 1.3b. **SUPERSEDED-BY-BATCH1 (2026-07-27):** dispatched verbatim in
      `plans/active/cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md` (~L113-125, part of the combined todo) —
      do not dispatch a second copy from here.
- [ ] [REFACTOR] P3. **1.5b — column pruning at the delta_one read** — push column selection down so a delta_one read
      materialises only the requested feature columns. Revisit after the end-to-end pipeline is green. Repo:
      features-service. **MIGRATED FROM:** item 1.5b. **NOT migrated anywhere (confirmed 2026-07-27) — stays open here,
      still genuinely gated.** Its gate, `plans/active/features_service_e2e_pipeline_test_2026_05_26.md`, had its
      2026-05-26 ROLLOUT-AGENT HOLD lifted 2026-07-27 (operator decision) — but that plan is still `status: active` with
      real open Track-1 remainder (items 1 and 7 of its 7-item reconciliation are "still genuinely open", per its own
      2026-07-27 note), i.e. it has NOT reached a fully-closed end-to-end-green state yet. Re-check that plan's status
      before dispatching this item; do not force it open on a stale HOLD-banner reading, but do not dispatch it while
      the gate doc is still active with open remainder either.
- [ ] [CODE] P2. **1.7e — restore features-service basedpyright strictness (574 errors masked)** — the
      `reportUnknownMemberType` / `reportUnknownVariableType` / `reportUnknownArgumentType` (+ 6 more) severities were
      set to `"none"` in `features-service/pyrightconfig.json`/`pyproject.toml`, hiding ~574 errors. Restore them to
      `error` (or a ratcheted budget) and burn down the errors in a dedicated session. NOTE: distinct from
      `codex_violations_ratchet_to_five` (that gate is the CODEX_MAX_VIOLATIONS lint budget + file-size splits, NOT the
      basedpyright-severity weakening). Repo: features-service. **MIGRATED FROM:** item 1.7e (no prior home).
      **SUPERSEDED-BY-BATCH1 (2026-07-27):** dispatched verbatim in
      `plans/active/cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md` (~L113-125, part of the combined todo) —
      do not dispatch a second copy from here.

## Success criteria

- In-memory DAG handoff + parquet consolidation + read-time pruning land with features-service `quality-gates.sh` green
  and a measured I/O reduction (object count / read bytes) on a sample (day, fg, tf).
- features-service basedpyright `reportUnknown*` severities back to `error` (or a downward-only ratchet) with the 574
  errors burned down; no new suppressions added.

## Temporary states + their canonical follow-up plans

- (none — this IS the canonical follow-up for the archived `features_calc_efficiency_and_correctness` deferrals.)
