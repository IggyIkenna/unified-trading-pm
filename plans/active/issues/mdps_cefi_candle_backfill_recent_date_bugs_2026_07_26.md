---
doc_type: issue
title:
  Three MDPS cefi candle-building bugs found while backfilling on-chain-perp venues (memory-scaling OOM,
  derivative_ticker schema gap, book_snapshot_5 column mismatch)
summary: >-
  Discovered while executing cefi_satellite_ao_dispatch_batch1-001 (extend MDPS candle-building to
  ASTER/HYPERLIQUID/LIGHTER-ZKSYNC/EXTENDED-STARKNET + backfill). Three independent, code-level bugs surfaced in
  market-data-processing-service's candle-building path, all reproducible against real prod data, none specific to the 4
  target venues (they'd affect any high-volume/high-instrument-count CeFi venue's candle backfill). Filed here per the
  findings-closure hard rule rather than left as prose in the source plan's Progress Log.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-data-processing-service, unified-api-contracts]
scope: [engineer]
tags: [mdps, candle, ohlcv, memory, oom, schema-contract, book-snapshot, backfill]
related:
  [
    /plans/active/cefi_satellite_ao_dispatch_batch1_2026_07_25.md,
    /plans/active/issues/mdps_cefi_candle_manifest_never_emitted_2026_07_26.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-26"
author: slot-6
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 1.5
assigned_role: data_engineering
drift_direction: advance-code
source: >-
  Discovered 2026-07-26 while executing cefi_satellite_ao_dispatch_batch1-001 (slot 6). All three measured against real
  prod data on live SPOT VMs (mdps-backfill-cefi-20260726-*), not inferred.
locked_by:
locked_since:
resolved_by:
---

# MDPS cefi candle-building: three backfill-blocking bugs

## What I found

### Bug 1 — per-day memory scaling: a SINGLE real day for ONE venue can exceed 32GB RAM (most severe, P1)

Backfilling HYPERLIQUID `trades` candles for `day=2026-07-19` alone (177 tradable instruments, all 7 timeframes
`15s..24h`) on a `e2-standard-8` (32GB RAM) VM was killed by the kernel OOM-killer at `rc=137` after RSS climbed
monotonically through the aggregation cascade: 17.1 → 20.1 → 24.8 → 26.2 → 27.1 GiB (58.5% → 88.6% mem) before being
killed. This reproduced identically on TWO separate VM launches for the same date/venue (once as part of a 7-day window,
once in isolation) — not a fluke. A 2-instrument-scoped run (`--instrument-ids` narrowed to BTC/ETH only) for the SAME
date completed with a comfortable ~1.5-2.4GB RSS, confirming the scaling is roughly linear in instrument count and the
full 177-instrument sweep is what exceeds the ceiling, not the date range. Separately, a MULTI-day run (30-day + 7-day
windows) also OOM'd, but only reached ~2-4 days in before crashing — consistent with per-day memory not being released
between dates (each date's full instrument sweep pushes it over the edge sooner as the process's baseline footprint
grows). Suspected root cause: the candle aggregator likely holds every tradable instrument's data (or a large fraction
of it) in memory simultaneously per date rather than streaming/chunking per-instrument or per-batch;
`cefi_wire_bridge: loaded 429129 catalogue rows` is reloaded once per date-invocation, which may also not be released.

### Bug 2 — `derivative_ticker` candle building fails for ALL HYPERLIQUID instruments sampled (P2)

Every sampled HYPERLIQUID instrument (8/8: ADA/AVAX/BNB/DOGE/FIL/LTC/MATIC/SOL-PERP) failed
`derivative_ticker`→`deriv_ohlcv_1m` candle building with
`[CRITICAL] No SchemaContract registered for asset_group='cefi' instrument_type='UNKNOWN' data_type='deriv_ohlcv_1m' venue='HYPERLIQUID'`
plus a companion `SCHEMA_VALIDATION_FAILED` (NOT-NULLABLE OHLC columns getting 4320 NaN/null values) at the `15s` tier.
The `instrument_type='UNKNOWN'` in the error (vs the expected `perpetual`) suggests a resolution bug, not necessarily a
genuinely-missing contract. Does NOT affect the `trades`→`quote_volume` path (the ADV-reader-relevant data_type).

### Bug 3 — `book_snapshot_5` column-name mismatch for HYPERLIQUID (P2)

HYPERLIQUID's raw `book_snapshot_5` columns are named `bid_px_00`/`ask_px_00` (etc., 5 levels), not the
`bid_price_0`/`ask_price_0` the book-candle aggregator expects (`WARNING Missing bid_price_0 or ask_price_0 columns`).
This makes the aggregator treat the shard as "no valid rows" and attempt `record_empty(reason=SOURCE_RETURNED_ZERO)`
without `FetchEvidence` — correctly REFUSED by the UTL Phase-1 KEYSTONE honest-absence gate
(`UnprovenHonestAbsenceError`), so no bad data lands, but the shard is never candle-built either. Worth checking
LIGHTER-ZKSYNC/EXTENDED-STARKNET for the same `bid_px_NN`/`ask_px_NN` naming convention since they may share the same
on-chain-CLOB wire format.

## Why it matters

- Bug 1 makes ANY multi-instrument, high-volume-venue CeFi candle backfill on the default `e2-standard-8` launcher
  unreliable — not just for these 4 venues. It will recur for BITGET/BINANCE/etc. tardis-sourced venues too if their
  instrument counts are similarly large, though the full-range 2024-dated backfill (fewer historical instruments) has
  run 80+ days cleanly so far, suggesting the ceiling is instrument-count-dependent and mostly a problem for
  CURRENT/recent-date backfills.
- Bugs 2/3 are narrower (specific data_types) but silently drop real candle coverage for those data_types/venues without
  a loud, actionable alert beyond a WARNING/CRITICAL log line — worth a proper fix so `derivative_ticker` and
  `book_snapshot_5` candle coverage isn't permanently zero for HYPERLIQUID.

## Recommended decision

- [ ] [DATA] P1. **Fix MDPS's per-day candle-aggregation memory scaling.** Root-cause why processing all tradable
      instruments for one CeFi venue/date exceeds 32GB RAM (suspected: no per-instrument streaming/chunking, or the
      instruments catalogue/wire-bridge cache growing unbounded across the date-loop). Either add per-instrument
      batching/streaming to the aggregator, or make the backfill launcher scale machine type to instrument count. Repo:
      market-data-processing-service. **Done when**: a full (all-instrument) HYPERLIQUID `trades` candle backfill for
      one high-volume recent day completes on the standard launcher without OOM, with a regression test/benchmark
      recorded.
- [ ] [DATA] P2. **Fix HYPERLIQUID `derivative_ticker`→`deriv_ohlcv_1m` candle building.** Root-cause the
      `instrument_type='UNKNOWN'` resolution (should resolve `perpetual`) for HYPERLIQUID `derivative_ticker` rows, then
      either fix the resolution or register the missing
      `unified_api_contracts.internal.schemas.contracts.     CONTRACT_REGISTRY` entry for `deriv_ohlcv_1m`. Repos:
      market-data-processing-service (+ unified-api-contracts if a new contract is needed). **Done when**: a real
      `derivative_ticker` backfill for at least one HYPERLIQUID instrument produces a valid `deriv_ohlcv_1m` candle with
      no SchemaContract/validation error.
- [ ] [DATA] P2. **Fix the `book_snapshot_5` column-name mapping for on-chain-perp venues.** Map HYPERLIQUID's (and
      check LIGHTER-ZKSYNC/EXTENDED-STARKNET's) `bid_px_NN`/`ask_px_NN` raw columns to the `bid_price_0`/`ask_price_0`
      the book-candle aggregator expects. Repo: market-data-processing-service. **Done when**: a real `book_snapshot_5`
      backfill for at least one HYPERLIQUID instrument produces a valid candle instead of the "Missing bid_price_0"
      warning + refused honest-absence write.
