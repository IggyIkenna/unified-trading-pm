---
title: "MDPS prediction schema contract: missing columns in candle DataFrame"
created: 2026-05-23
author: slot-7
source:
  - "batch 111916 prediction VMs: mdps-prediction-{2025,2026}-20260523-111916"
  - "logs: StreamingParquetWriter pre-write validation failed: [schema_violation] column 'chain' missing from dataframe;
    [schema_violation] column 'condition_id' missing from dataframe; [schema_violation] column 'ts_event' missing from
    dataframe; [schema_violation] column 'trade_count' has dtype 'int32', expected 'int64'; [schema_violation] column
    'timeframe' missing from dataframe"
locked_by: live-defi-rollout
parent_epic: plans/epics/mtds_mdps_master.md
---

## What I found

All 4 prediction MDPS VMs (batch 20260523-111916) failed because `StreamingParquetWriter` pre-write validation rejected
the candle DataFrame.

The `PREDICTION_MARKET` ohlcv contract (registered in UAC `_candle_contracts.py` with `include_chain=True`,
`anchor_col=condition_id`, `nullable_ohlcv=True`) requires these columns:

- `instrument_id` ✓
- `venue` ✓
- `chain` ✗ — NOT produced by `CefiTradesAdapter`
- `condition_id` ✗ — NOT produced (adapter produces `symbol`)
- `ts_event` ✗ — NOT produced (adapter produces `timestamp`)
- `open/high/low/close/volume/trade_count` ✓ — but `trade_count` is int32 ✗ (expected int64)
- `timeframe` ✗ — NOT produced

Root cause: `PredictionTradesAdapter` inherits from `CefiTradesAdapter`, which produces a generic `CandleOutput`. The
adapter doesn't add prediction-specific columns (`chain`, `condition_id`, `ts_event`, `timeframe`), and the
`canonical_writer.write_candle_parquet()` had no enrichment step for prediction.

## Why it matters

All prediction candles (Polymarket) fail to write — 0 rows captured for the entire prediction asset group.
MDPS-3.3.Pred-V gate cannot clear.

## Fix applied

Added `_enrich_prediction_candles()` helper to `market_data_processing_service/app/core/canonical_writer.py` and called
it inside `write_candle_parquet()` after `_stamp_candle_available_at()` and before `lookup_mdps_contract()`. The
enrichment:

1. Adds `chain` from `_infer_chain()` result (already computed)
2. Copies `symbol` → `condition_id`
3. Copies `timestamp` → `ts_event`
4. Adds `timeframe` = `tf` (the normalised timeframe string)
5. Casts `trade_count` int32 → int64

Status: code fix committed to MDPS, tarball rebuild required, batch 111916 VMs to be replaced with new tarball.

## Recommended decision

No operator decision needed — fix is clear, scope is single repo. Post-fix: rebuild tarball, terminate batch 111916 VMs,
relaunch with new tarball. Verify MDPS-3.3.Pred-V.
