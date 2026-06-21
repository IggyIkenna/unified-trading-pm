---
title: "MDPS adapter protocol pandas→polars + Phase-6 _publish_emission_check scalability"
parent_epic: mtds_mdps_master
priority: P3
status: active
execution_scope: orchestrator-agent
estimate_class: refactor
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 2.0
locked_by: live-defi-rollout
locked_since: 2026-06-21
related_plans:
  - ../epics/mtds_mdps_master.md
  - ../archive/2026_06/mdps_pure_polars_migration_2026_05_28.md
---

# MDPS adapter protocol pandas→polars + Phase-6 emission-check scalability

> **MIGRATED FROM:** `mdps_pure_polars_migration_2026_05_28.md` (archived 2026-06-21). The MDPS engine is pure-Polars
> end-to-end (that plan shipped + is codex-LOCKED in `codex/06-coding-standards/data-engine-selection.md`). These two
> items were deferred there under an explicit operator directive ("adapter output stays pandas for now, migrate later"
> + Phase-6 "DO NOT TOUCH YET — scope after an operator option-pick") and are tracked here so they are not lost.

## Objective

Complete the pandas→polars migration at the **adapter boundary** (the engine is already pure-Polars) and resolve the
Phase-6 emission-check scalability question — both operator-gated follow-ups carved out of the completed pure-polars
migration.

## Todos

- [ ] [REFACTOR] P3. **All 18 adapters' `process_to_candles(df, ...)` signature → Polars** — the MDPS compute engine is
      pure-Polars but the ~18 source adapters still emit/accept pandas at the `process_to_candles` seam, forcing a
      pandas↔polars conversion per shard. Thread the polars frame through the adapter protocol so the conversion is
      dropped. Operator-directed as a LATER migration ("pandas output is okay for now"). Repo: market-data-processing-service
      (adapter protocol + the 18 adapter implementations). **MIGRATED FROM:** `mdps_pure_polars_migration` item 3.6.
- [ ] [DESIGN] P3. **Phase-6 `_publish_emission_check` scalability — operator option-pick required** — the per-shard
      emission-policy check (`_publish_emission_check`) was flagged "DO NOT TOUCH YET" in the pure-polars plan pending an
      operator decision on the scalability approach (it materialises the availability index per call). Surface the
      option set (in-process TTL cache vs batched pre-flight vs incremental index), get the operator pick, then implement.
      Repo: market-data-processing-service. **MIGRATED FROM:** `mdps_pure_polars_migration` Phase 6.

## Success criteria

- Adapter protocol carries a polars frame end-to-end; the pandas↔polars per-shard conversion is removed; MDPS
  `quality-gates.sh` green.
- `_publish_emission_check` approach selected by the operator + implemented; no per-call full-index materialisation
  regression (per-shard memory gate stays green).

## Temporary states + their canonical follow-up plans

- (none — both items are the canonical follow-up for the archived `mdps_pure_polars_migration` deferrals.)
