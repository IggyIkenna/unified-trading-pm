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
- [ ] [DATA] P2. **market-tick-data-service** — trace the corrupted `58317-01-15` timestamp back to its raw source
      object (`NASDAQ:EQUITY:IBIT`/`ETHA`, day=2026-05-07) to determine if this is a one-off vendor glitch or a systemic
      unit/encoding bug (e.g. an epoch-microseconds value misread as epoch-nanoseconds, or a sentinel/NULL value not
      filtered) — if systemic, the fix belongs in the CAPTURE path, not just as an MDPS-side guard.
- [ ] [SCRIPT] P2. Once the guard lands, re-run the same scoped cell (and ideally a few more NASDAQ instruments) to
      confirm the candle path now degrades gracefully instead of failing outright.

## Progress Log

- **context-scout 2026-08-03**: populated/refreshed context_scope (4 entries).
