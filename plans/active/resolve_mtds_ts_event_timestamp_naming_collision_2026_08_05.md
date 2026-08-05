---
doc_type: plan
title: Resolve MTDS `ts_event`→`timestamp` naming collision (scope the fix)
summary: >-
  Scope the resolution of the MTDS column-alias naming collision (`ts_event` aliased to `timestamp`) that forces MDPS
  and other downstream readers to infer timestamp units via a magnitude heuristic rather than from the column name. The
  alias has been live since 2026-04-16 and a 2026-06-10 census found 24/24 sampled TradFi OHLCV parquets using the
  `timestamp` name — changing it has a broad blast radius. This plan catalogs all consumers, picks an approach, and
  dispatches the migration in phases.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [market-tick-data-service, market-data-processing-service, features-service, unified-trading-library]
scope: [engineer, admin]
tags: [data-correctness, naming-collision, timestamp, ts_event, MTDS, MDPS, tradfi, databento]
related:
  [
    /plans/active/issues/mdps_tradfi_nasdaq_timestamp_overflow_candle_crash_2026_07_27.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch5_2026_07_29.md,
  ]
created: 2026-08-05
last_updated:
author: slot-4 (data_engineering)
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0.8
estimate_calibrated_ai_days: 0.32
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  [
    /plans/active/issues/mdps_tradfi_nasdaq_timestamp_overflow_candle_crash_2026_07_27.md todo 3,
    "slot-4 dispatched task mdps_tradfi_nasdaq_timestamp_overflow_candle_crash-004",
  ]
---

# Resolve MTDS `ts_event`→`timestamp` naming collision — scoping plan

## What this is

MTDS's `_COLUMN_ALIASES` in `symbol_rules.py:60-61` renames Databento's `ts_event` → `timestamp` before writing raw tick
parquet. This erases the unit signal: `ts_event` = nanoseconds, `timestamp` = microseconds. MDPS's timestamp-column
priority order (`ts_init > local_timestamp > ts_event > timestamp`) then falls through to the generic `timestamp`
fallback (priority 4), and the unit-inference path must rely on a magnitude heuristic (`base_adapter.py:307-314`,
`canonical_writer_shaping.py:703-704`, `candle_write_mixin.py:538-551`) rather than the column name.

The magnitude heuristic WORKS (shipped `market-data-processing-service@f179c96`), but it's a band-aid — the durable root
cause is the shared column name `timestamp` meaning different units for CeFi/Tardis (µs) vs TradFi/Databento (ns).

## Blast-radius survey (2026-08-05)

### Source of the alias

- **MTDS `symbol_rules.py:60-61`**: `_COLUMN_ALIASES = {"ts_event": "timestamp", "size": "amount"}`
- **MTDS `symbol_rules.py:94-106`**: `_apply_column_aliases()` — renames columns non-destructively
- **MTDS `partitioned_writer.py:290,378`**: two callsites applying aliases before write

The alias has been live since **2026-04-16** (>16 months of parquet on disk carrying the aliased name).

### Consumers that depend on the `timestamp` column name

| Consumer                | File(s)                                                            | Dependency                                                  | Impact if alias removed                                        |
| ----------------------- | ------------------------------------------------------------------ | ----------------------------------------------------------- | -------------------------------------------------------------- |
| **MDPS**                | `base_adapter.py:213-232` (`_get_local_timestamp_column`)          | Priority 4 fallback (`timestamp`)                           | LOW — `ts_event` at priority 3 would catch ns values correctly |
| **MDPS**                | `base_adapter.py:234-329` (`_convert_to_processing_dt`)            | Unit inference for generic `timestamp`                      | LOW — correctly infers ns from `ts_event` at line 272-278      |
| **MDPS**                | `canonical_writer_shaping.py:695-726`                              | Already handles both `ts_event` and `timestamp` names       | NONE — dual-path already present                               |
| **MDPS**                | `adapter_utils.py:59-89`                                           | `ts_event`/`ts_init` → ns special-casing                    | NONE — already checks for `ts_event` by name                   |
| **MDPS**                | `ohlcv_passthrough.py:310-329`                                     | Explicitly aware of alias; uses `bar_edge` marker, not name | NONE — already name-agnostic for edge detection                |
| **UTL**                 | `timestamp_validation.py:250` (`detect_timestamp_column_and_unit`) | Column-name-aware unit detection                            | LOW — already handles `ts_event`                               |
| **features-service**    | `cross_instrument/engine/raw_data_loader.py`                       | Reads raw tick parquet (generic column access)              | MEDIUM — needs audit of column-name assumptions                |
| **features-service**    | `calendar/adapters/mtds_fred_reader.py`                            | Reads MTDS-written FRED parquet                             | MEDIUM — needs audit                                           |
| **e2e-testing**         | `scripts/paper_trading/_fetch_spx_databento.py:96`                 | Reads `ts_event` directly (bypasses MTDS)                   | NONE                                                           |
| **e2e-testing**         | `scripts/validation/validate_shards_4pillar.py:139`                | Lists `ts_event` as native time column                      | NONE                                                           |
| **instruments-service** | `scripts/aggregate_legacy_es_opt_trades.py:162-163`                | Reads `ts_event` directly (bypasses MTDS)                   | NONE                                                           |

### The MTDS `size`→`amount` alias

`_COLUMN_ALIASES` also contains `"size": "amount"`. This alias has ZERO known correctness impact (no unit-disambiguation
problem), but any approach that removes the `ts_event` alias should handle `size`→`amount` consistently (either keep it
or remove it too).

## Recommended approach: Add `ts_event` alongside `timestamp`, phase out alias over time

**Why not just remove the alias outright**: 16+ months of on-disk parquet carry the `timestamp` name. A hard cutover
breaks every reader that hasn't been audited, and the blast radius includes features-service (production features
pipeline), e2e-testing, and possibly client-reporting-api scripts.

**Phase 1 — Dual-write (MTDS, near-zero risk):**

- [ ] [DATA] P1. **market-tick-data-service** — in `_apply_column_aliases`, instead of RENAMING `ts_event` →
      `timestamp`, ADD a `ts_event` column alongside `timestamp` (copy the values). The `timestamp` column stays for
      backward compatibility; new `ts_event` column carries the unit signal. Unit test: verify both columns present +
      equal values after alias application.

**Phase 2 — MDPS migrates to `ts_event` priority (already structurally ready):**

- [ ] [DATA] P2. **market-data-processing-service** — verify `_get_local_timestamp_column` (priority 3 = `ts_event`)
      correctly picks up the new column for TradFi instruments. The magnitude heuristic in `_convert_to_processing_dt`
      becomes dead code for the TradFi path but stays as a safety net. Verify with a real TradFi parquet read (IBIT or
      ETHA, day=2026-05-07) that the ns unit is correctly inferred from column name alone. Add a regression assertion.

**Phase 3 — Audit and migrate remaining consumers:**

- [ ] [DATA] P2. **features-service** — audit `raw_data_loader.py`, `mtds_fred_reader.py`, and any cross-instrument
      calculator that reads raw tick columns by name. Confirm no consumer hardcodes `timestamp` column access that would
      break if `ts_event` becomes the canonical name. File findings as follow-up todos in this plan.
- [ ] [DATA] P3. **all repos** — grep for `["']timestamp["']` column-access patterns in any reader of MTDS-written raw
      tick parquet (exclude MDPS which is handled in Phase 2). Catalog any hardcoded `timestamp`→`ts_event` assumptions.

**Phase 4 — Remove the alias (after all consumers confirmed migrated, ≥2 weeks after Phase 1 lands):**

- [ ] [DATA] P3. **market-tick-data-service** — remove `"ts_event": "timestamp"` from `_COLUMN_ALIASES`, remove the
      dual-write copy logic from Phase 1. The `size`→`amount` alias is kept (no correctness impact, separate concern).
      Gate: all Phase 3 audit todos must be done + verified before this is unblocked.

## Codex SSOTs

- `/codex/02-data/tradfi-databento-sourcing-ssot.md` — Databento column semantics
- `/codex/02-data/pipeline-mode-partition.md` — pipeline_mode/source-aware paths

## Progress Log

- **2026-08-05 (slot-4, data_engineering)**: Scoping plan created. Surveyed all consumers of the `timestamp` column
  across the fleet (MTDS, MDPS, UTL, features-service, e2e-testing, instruments-service). Confirmed the alias has been
  live since 2026-04-16; 2026-06-10 census found 24/24 sampled parquets carry `timestamp` name. Recommended phased
  approach: dual-write `ts_event` + `timestamp` (Phase 1) → migrate MDPS (Phase 2) → audit remaining consumers (Phase 3)
  → remove alias (Phase 4).
