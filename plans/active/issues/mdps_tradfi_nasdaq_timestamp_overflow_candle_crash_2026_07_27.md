---
doc_type: issue
title:
  MDPS TRADFI candle derivation crashes on a corrupted raw-tick timestamp (year 58317) — IBIT/ETHA all timeframes fail
summary: >-
  Real-VM proof-sweep of `/plans/archive/issues/mdps_derivative_ticker_candle_schema_violation_2026_07_20.md` todo 3
  found `TRADFI:NASDAQ:trades` (day=2026-05-07, auto-day) failing ALL 7 timeframes for BOTH instruments in the scoped
  batch (`IBIT`, `ETHA` — Bitcoin/Ethereum spot ETFs) with `Out of bounds nanosecond timestamp: 58317-01-15 ...` — a
  corrupted/garbage raw-tick timestamp value overflowing pandas' `datetime64[ns]` range (max ~2262), crashing candle
  aggregation before any parquet write. Distinct bug class from the derivative_ticker schema-violation issue: this is a
  raw-tick DATA-QUALITY defect, not a schema/contract gap, and it correctly reports failure (exit_code=1) — the
  observability half of the original issue does NOT reproduce here.
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-data-processing-service, market-tick-data-service]
scope: [engineer, admin]
tags: [data-correctness, mdps, candles, tradfi, timestamp, data-quality]
related:
  [
    /plans/archive/issues/mdps_derivative_ticker_candle_schema_violation_2026_07_20.md,
    /plans/active/data_pipeline_check_mdps_features_2026_07_20.md,
  ]
created: 2026-07-27
parent_epic: infrastructure_master
priority: P1
source:
  [
    "/plans/archive/issues/mdps_derivative_ticker_candle_schema_violation_2026_07_20.md todo 3, dispatched task
    mdps_derivative_ticker_candle_schema_violation-002, slot-10 2026-07-27, real VM
    mdps-backfill-tradfi-pipelinecheck-20260727-114131-44d2d0",
  ]
assigned_vm: planning
execution_scope: orchestrator-agent
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.3
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
locked_since:
context_scope: [/plans/archive/issues/mdps_derivative_ticker_candle_schema_violation_2026_07_20.md, /plans/active/data_pipeline_check_mdps_features_2026_07_20.md, market-data-processing-service/market_data_processing_service/app/adapters/base_adapter.py, market-data-processing-service/market_data_processing_service/app/adapters/tradfi/trades_adapter.py]
---

# MDPS TRADFI candles crash on a corrupted raw-tick timestamp (year 58317)

## What I found

Running
`/data-pipeline-check-mdps --asset-group TRADFI --venue NASDAQ --data-types trades --legs force --require-captured --auto-day`
on a real VM (`mdps-backfill-tradfi-pipelinecheck-20260727-114131-44d2d0`, day slid to 2026-05-07 via `--auto-day`):
**0/2 instruments succeeded, exit_code=1** (correctly non-zero — this run does NOT reproduce the original issue's
silent-success bug). Both instruments in the scoped batch failed identically across ALL 7 timeframes:

```
[trades] NASDAQ:EQUITY:IBIT: 15s: Out of bounds nanosecond timestamp: 58317-01-15 08:57:34; 1m: ...; 5m: ...; 15m: ...; 1h: ...; 4h: ...; 24h: ...
[trades] NASDAQ:EQUITY:ETHA: 15s: Out of bounds nanosecond timestamp: 58317-01-15 20:33:32; 1m: ...; 5m: ...; 15m: ...; 1h: ...; 4h: ...; 24h: ...
```

`IBIT` and `ETHA` are Bitcoin- and Ethereum-spot ETFs respectively. `58317-01-15` is far beyond pandas' `datetime64[ns]`
representable range (year ~2262 max) — this is a garbage/corrupted raw timestamp value somewhere in the input tick data
(likely a sentinel/overflow value from the upstream vendor, or a unit-conversion bug reading a non-nanosecond epoch
value as nanoseconds), not a real trade timestamp. The aggregator has no bounds-check/guard before constructing the
pandas timestamp, so one bad row crashes the ENTIRE instrument's candle derivation for every timeframe rather than being
dropped/flagged as a single bad-row anomaly.

## Why it matters

- **Different bug class from the derivative_ticker issue**: that was a schema/contract gap; this is raw-tick
  data-quality reaching an unguarded aggregation path. The candle-schema proof-sweep's job (confirm the
  derivative_ticker fix generalizes) doesn't directly implicate this, but the sweep exists precisely to catch "other
  data_types/venues might have their OWN distinct problems," and this is exactly that.
- **A single corrupted tick can zero out an entire instrument's candle output** for every timeframe — no partial credit,
  no honest-absence handling for the specific bad row, just a hard crash. If this timestamp corruption is systemic to
  the source feed (not a one-off), it silently blocks TRADFI candle backfill for affected instruments.
- **Correctly reports failure** (exit_code=1, `attempted_failed` manifest semantics apply) — unlike the original issue,
  there is no "looks green" observability gap here; this is purely a data-quality/robustness gap.

## Recommended decision

- [x] ✅ [DATA] P1. **market-data-processing-service** — locate the candle aggregator's timestamp construction path for
      TRADFI trades and add a bounds-check (or a coercion using `errors="coerce"`+drop) before the
      `pd.Timestamp`/`datetime64[ns]` conversion, so ONE corrupted tick is dropped/flagged as a per-row anomaly
      (increment a `dropped_out_of_bounds_timestamp` counter, emit a WARNING) rather than crashing the whole
      instrument's derivation. Add a regression test with a synthetic corrupted-timestamp row proving the crash no
      longer propagates. — market-data-processing-service@c10425d. Root-cause fix in the shared
      `BaseCandleAdapter._convert_to_processing_dt`/`_series_to_datetime` (`errors="coerce"` alone is insufficient — a
      float64 column carrying one absurd magnitude raises a raw `OverflowError` before pandas' own coerce logic runs, so
      the raw numeric column is bounds-pre-filtered to NaN before `pd.to_datetime`); `TradfiTradesAdapter` drops rows
      whose `processing_dt` coerced to NaT, logging `dropped_out_of_bounds_timestamp` with the instrument_id, before
      deriving `main_date`/`interval_idx`. Regression test `test_corrupted_out_of_bounds_timestamp_dropped_not_crashed`
      added (verified it reproduces the exact `OverflowError` crash pre-fix, passes post-fix). Full `quality-gates.sh`
      green (sentinel=c10425d716e5... — full SHA `c10425d3aaaebc11ce912d77075b677b78971ea0`).
- [x] ✅ [DATA] P2. **DONE 2026-08-03 (slot-12, `data_engineering`).** Traced the corrupted `58317-01-15` timestamp to
      its raw source. **Verified directly against the real prod object** (not guessed):
      `gs://market-data-tick-tradfi-prd-central-element-323112/raw_tick_data/by_date/day=2026-05-07/pipeline_mode=batch_databento/asset_group=tradfi/venue=NASDAQ/instrument_type=equity/data_type=trades/NASDAQ:EQUITY:{IBIT,ETHA}-USD.parquet`
      — downloaded + inspected both files. The `timestamp` column (`uint64`) is 100% clean in both: every row falls in
      `1,778,140,803,454,358,407 .. 1,778,198,339,652,082,432` ns-since-epoch (correctly ≈2026-05-06/07). **This is NOT
      a vendor glitch or a raw-source sentinel/NULL** — the raw Databento capture is uncorrupted. **Root cause is a
      downstream unit-misread in MDPS, and it is confirmed SYSTEMIC (not a one-off)**: MTDS's `_apply_column_aliases`
      (`market-tick-data-service/market_tick_data_service/engine/orchestrator/symbol_rules.py:61,95-100`) renames
      Databento's true-nanosecond `ts_event` → the generic `timestamp` column name at write time, to unify
      TradFi/Databento with CeFi/Tardis's native `timestamp` column (which is genuinely **microseconds**). MDPS's
      `_get_local_timestamp_column` (`market-data-processing-service/.../app/adapters/base_adapter.py:213`) picks the
      timestamp column by name priority (`ts_init > local_timestamp > ts_event > timestamp`) — because the `ts_event`
      name was erased, IBIT/ETHA rows land on the generic `timestamp` fallback (priority 4), which
      `_convert_to_processing_dt`/`_series_to_datetime` (pre-fix) unit-inferred as µs for anything not named
      `ts_init`/`ts_event`. A genuine ns value (~1.778e18) read as µs and multiplied by 1000 → ~1.778e21 ns → year
      ≈58,300s. **Math check**: R≈1.778e18 as ns → correct (2026-05-07); as µs (the bug) → R×1000 ≈1.778e21 ns → year
      ≈58,300 (matches the reported `58317`); as ms/s the magnitude would be even further off and doesn't match — only
      the ns-read-as-µs interpretation reproduces the observed value. **Confirmed systemic via a second independent
      occurrence, same day**: the identical mechanism was already root-caused + fixed for CME combo `ESM6-ESU6` on this
      same `2026-05-07` date (`/plans/active/tradfi_satellite_ao_dispatch_batch5_2026_07_29.md` lines 865-899,
      `market-data-processing-service@f179c96` — added a `>= 1e18 → unit="ns"` magnitude-heuristic branch to
      `_convert_to_processing_dt`, verified live in `base_adapter.py` lines 285-314). Since IBIT/ETHA's raw values are
      also ~1.778e18 (crosses the same `>=1e18` threshold), **the already-shipped `f179c96` fix generically covers this
      exact crash too** — it's magnitude-based, not an instrument allowlist, so it protects any future TradFi row
      hitting the same collision. **Residual architectural risk (not yet fixed, filed as a new tracked todo below)**:
      the durable root cause is the shared column name `timestamp` meaning different units for CeFi/Tardis (µs) vs
      TradFi/Databento (ns) — the current fix is a robust magnitude heuristic, not a resolution of that cross-repo
      naming collision. Evidence: gcloud-verified raw GCS parquet (both instruments, zero anomalous rows);
      `market-data-processing-service@f179c96` (`git log` confirmed); `base_adapter.py:285-314` (current unit-detection
      logic confirmed present).
- [ ] [DATA] P3. **market-tick-data-service or market-data-processing-service** — resolve the underlying naming
      collision so unit-detection no longer depends on a magnitude heuristic: either MTDS stops aliasing Databento's
      `ts_event` → generic `timestamp` for TradFi (preserve the unit-signaling column name through to MDPS), or MDPS's
      column-priority/unit map becomes schema/vendor-aware (keyed off `pipeline_mode`/`source`, not column name +
      magnitude). Scope this as its own plan — cross-repo (MTDS write-schema change has consumers beyond MDPS; check
      features-service and any other reader of the `timestamp` column before changing the alias).
- [ ] [SCRIPT] P2. Once the guard lands, re-run the same scoped cell (and ideally a few more NASDAQ instruments) to
      confirm the candle path now degrades gracefully instead of failing outright.

## Progress Log

- **context-scout 2026-08-03**: populated/refreshed context_scope (4 entries).
