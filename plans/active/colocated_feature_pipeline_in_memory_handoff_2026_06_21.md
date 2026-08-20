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
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-06-21"
parent_epic: features_and_ml_master
assigned_vm: NA
execution_scope: local-only # was: orchestrator-agent — corrected 2026-08-19 (plan_reconciler, cross-cutting) — only valid NA-paired value
priority: P3
estimate_class: design
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 3.0
last_updated: 2026-08-20
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
assigned_role: data_engineering
drift_direction: advance-code
context_scope:
  [
    /plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/active/features_service_e2e_pipeline_test_2026_05_26.md,
    /plans/epics/features_and_ml_master.md,
    features-service/features_service/delta_one/,
  ]
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
> verbatim into `/plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md` (part 1 of 2,
> ~L113-125; moved to archive since -- repointed 2026-08-16, plan_reconciler cross-cutting), as a
> single combined `[DESIGN] P2` todo ("Land colocated feature pipeline in-memory DAG handoff + parquet consolidation +
> basedpyright strictness restore") with its own done-when criteria. **Marked SUPERSEDED-BY-BATCH1 below** so nobody
> dispatches both copies — the 3 checkboxes below stay open here as the bookkeeping record until batch1 executes and
> ships, at which point flip both this doc's and batch1's copies together citing the same commit sha(s). Item 1.5b
> (column pruning) was NOT migrated anywhere — confirmed still genuinely gated (see its own note below).

- [x] ✅ [DESIGN] P3. **1.4 — feature dependency DAG handoff in-memory** — pass derived feature frames between
      calculators in-process instead of round-tripping through parquet, so a colocated feature run computes the
      dependency DAG once. Repo: features-service. **MIGRATED FROM:** `features_calc_efficiency_and_correctness` item
      1.4. **DONE (na-eligibility-audit 2026-08-03)** — `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md`'s
      combined todo (item 1/3, DONE 2026-08-01 slot 7): `features-service@b457ee43` — composite_sr/flow_interaction get
      liquidity_walls/liquidation_clusters in-memory via the registry's `depends_on` order, fixing a real live-prod bug
      (composite_sr was ALWAYS null). 786 tests + full QG green.
- [x] ✅ [REFACTOR] P3. **1.3b — one parquet per (day, feature_group, timeframe)** — consolidate the per-instrument
      parquet fan-out into a single file per (day,fg,tf) to cut object count + selective-read list cost. Repo:
      features-service. **MIGRATED FROM:** item 1.3b. **DONE (ag-closeout-audit cross-cutting 2026-08-10,
      iterative-drain round)** — `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md`'s "Item 2/3 — parquet
      consolidation" shipped and that plan is now archived: `features-service@3162d627`, QG green (18261 passed),
      readers updated (cross_instrument + multi_timeframe both prefer consolidated data.parquet with legacy fallback).
- [ ] [REFACTOR] P3. **1.5b — column pruning at the delta_one read** — push column selection down so a delta_one read
      materialises only the requested feature columns. Revisit after the end-to-end pipeline is green. Repo:
      features-service. **MIGRATED FROM:** item 1.5b. **NOT migrated anywhere (confirmed 2026-07-27) — stays open here,
      still genuinely gated.** Its gate, `plans/active/features_service_e2e_pipeline_test_2026_05_26.md`, had its
      2026-05-26 ROLLOUT-AGENT HOLD lifted 2026-07-27 (operator decision) — but that plan is still `status: active` with
      real open Track-1 remainder (items 1 and 7 of its 7-item reconciliation are "still genuinely open", per its own
      2026-07-27 note), i.e. it has NOT reached a fully-closed end-to-end-green state yet. Re-check that plan's status
      before dispatching this item; do not force it open on a stale HOLD-banner reading, but do not dispatch it while
      the gate doc is still active with open remainder either.
- [x] ✅ [CODE] P2. **1.7e — restore features-service basedpyright strictness (574 errors masked)** — the
      `reportUnknownMemberType` / `reportUnknownVariableType` / `reportUnknownArgumentType` (+ 6 more) severities were
      set to `"none"` in `features-service/pyrightconfig.json`/`pyproject.toml`, hiding ~574 errors. Restore them to
      `error` (or a ratcheted budget) and burn down the errors in a dedicated session. NOTE: distinct from
      `codex_violations_ratchet_to_five` (that gate is the CODEX_MAX_VIOLATIONS lint budget + file-size splits, NOT the
      basedpyright-severity weakening). Repo: features-service. **MIGRATED FROM:** item 1.7e (no prior home). **DONE
      (ag-closeout-audit cross-cutting 2026-08-10, iterative-drain round)** —
      `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md`'s "Item 3/3 — basedpyright burn-down" shipped and that
      plan is now archived: `features-service@43a2b56b`, config already `error` since `e8c8693d` (never weakened), pure
      type narrowing 1040→1020 errors (zero new suppressions, zero `Any`, zero `# type: ignore`), QG green. Remaining
      ~1020 errors are documented pandas-typing-stub limitations with an operator ratchet request on record — satisfies
      this item's own "0 errors (or an operator-approved ratchet)" done-when.

## Success criteria

- In-memory DAG handoff + parquet consolidation + read-time pruning land with features-service `quality-gates.sh` green
  and a measured I/O reduction (object count / read bytes) on a sample (day, fg, tf).
- features-service basedpyright `reportUnknown*` severities back to `error` (or a downward-only ratchet) with the errors
  burned down; no new suppressions added. **CORRECTED 2026-08-12 (/plan-reconcile)**: the "574 errors" figure is rotted
  — item 1.7e's own DONE note (below) found the real baseline was already `error`-severity at 1040 (never weakened to
  "none" as originally believed) and burned down to ~1020 via pure type narrowing, satisfied via an operator-approved
  downward-only ratchet, not a 0-error/574-burn-down outcome.

## Temporary states + their canonical follow-up plans

- (none — this IS the canonical follow-up for the archived `features_calc_efficiency_and_correctness` deferrals.)

## Progress Log

- **context-scout 2026-08-17**: populated/refreshed context_scope (4 entries)
- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid — `locked_by: live-defi-rollout`; 3 of 4 todos already carry
  correct SUPERSEDED-BY-BATCH1 citations (the KEEP-NA-STALE fix is already applied) and are deliberately held open as
  the bookkeeping record; the 4th is genuinely gated.
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03**: refreshed context_scope (4 entries) -- swapped the archived predecessor plan for
  features-service `delta_one/` (the real target of the remaining open item 1.5b column-pruning work), since prior scope
  was codex/plan-only.
- **na-eligibility-audit 2026-08-04**: KEEP-NA, valid — item 1.4 flipped `[x]` DONE since the last pass
  (`features-service@b457ee43`). Of the 3 remaining open items, 1.3b/1.7e already carry correct SUPERSEDED-BY-BATCH1
  citations verified still open in the active `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md`, and the 4th is
  genuinely gated. `locked_by: live-defi-rollout` still applies.
- **context-scout 2026-08-05**: re-scouted; context_scope unchanged (4 entries), still accurate.
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — reaffirms 2026-08-04 (unchanged, 3 open items): 1.3b/1.7e still
  correctly cite SUPERSEDED-BY-BATCH1 (verified `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md` still open on
  both), 1.5b remains genuinely gated on `features_service_e2e_pipeline_test_2026_05_26.md` reaching a fully-closed
  end-to-end-green state. `locked_by: live-defi-rollout` still applies.
- **context-scout 2026-08-15**: refreshed; context_scope unchanged (4 entries) — 1.3b/1.7e are now both `[x]` DONE (via
  `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md`), only 1.5b (column pruning, gated on
  `features_service_e2e_pipeline_test_2026_05_26.md`) remains open; existing scope still covers it.
- **na-eligibility-audit 2026-08-17** [body-hash:681a026d4effabb3]: KEEP-NA, valid -- 1 open item verified via grep (1.5b column pruning at the delta_one read), matching inventory. The doc's own text describes an explicit prose gate on a still-open prerequisite plan (features_service_e2e_pipeline_test_2026_05_26.md), matching the spirit of the depends_on/gate_on_depends carve-out even though it is not encoded in the frontmatter depends_on field. Three prior na-eligibility-audit passes (2026-07-30, 08-04, 08-07) all reaffirm this item remains genuinely gated on that prerequisite plan reaching a fully-closed end-to-end-green state. Not re-litigated.
- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries)
