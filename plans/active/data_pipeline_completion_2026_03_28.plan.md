---
title: "Data Pipeline Completion — remaining items from instruments + MTDS + features sessions"
owner: agent
priority: P0
locked_by: live-defi-rollout
locked_since: 2026-03-28
readiness:
  code: C2
  deployment: D0
  business: B0
---

# Data Pipeline Completion

## Context

The instruments-service and market-tick-data-service sessions (2026-03-27/28) delivered:
- InstrumentRecord schema slimdown (36 → 22 fields)
- Per-instrument asset_class from UAC registry
- Streaming downloads with StreamingParquetWriter (17M rows validated)
- E2E audit: 11/12 PASS across CeFi, TradFi, DeFi, Sports, Prediction
- staleness_seconds on options LOCF for vol surface quality
- VIX index via Yahoo Finance

This plan covers remaining items to reach full pipeline readiness.

## Phase 1: Cleanup (P0 — next session start)

- [x] [AGENT] P0. Commit uncommitted work across 9 repos (linter changes, prior session diffs)
- [x] [AGENT] P0. Fix GCS path date format: `day=2026-03-23T00:00:00+00:00` → `day=2026-03-23`
  - Already fixed: orchestrator line 131 normalizes to `str(date)[:10]`

## Phase 2: Remaining adapters (P1)

- [x] [AGENT] P1. Kalshi adapter `download_batch()` — same pattern as Polymarket
  - Added `get_trades()`, `get_trades_batch()`, `download_batch()` to KalshiAdapter
  - Cursor-based pagination on `GET /markets/{ticker}/trades`
  - Loads tickers from instruments-service GCS, streams to writer
- [x] [AGENT] P1. Hyperliquid historical tick data via S3 archive
  - Restored HyperliquidS3Downloader from git history (335 lines)
  - Wired into MTDS routing (umi_tick_provider.py) for HYPERLIQUID venue
  - Fetches trades from `hl-mainnet-node-data` + funding/OI from `hyperliquid-archive`
  - Aster: REST only (no public S3 archive)
- [x] [AGENT] P1. Polymarket instruments: convert to parquet output (currently JSON)
  - Already handled: instruments-service orchestrator writes parquet via DataSink
  - MTDS adapter handles both parquet and JSON fallback

## Phase 3: Features pipeline (P1)

- [x] [AGENT] P1. Futures roll adjuster: wire into features-delta-one-service as preprocessing
  - Import and call `FuturesRollAdjuster` in orchestrator `_process_instrument()`
  - Applied before feature computation for TRADFI category on futures_basis/technical/momentum
  - Shard-level failure isolation: returns original candles on error
- [x] [AGENT] P1. Session times utility in UAC (stateless, no extra instrument columns)
  - Created `unified_api_contracts/registry/session_times.py`
  - `from unified_api_contracts import is_trading_hours, get_session_times`
  - Uses `zoneinfo` (stdlib) for DST-correct timezone conversions
  - CME: Sunday 5pm CT – Friday 4pm CT (22hr session, daily 4-5pm break)
  - NYSE/NASDAQ: 9:30am – 4pm ET (6.5hr session)
  - Crypto/DeFi: always returns True (24/7)
- [ ] [AGENT] P1. Verify staleness_seconds flows end-to-end with real Deribit options data
  - Run MDPS on Deribit options_chain tick data
  - Check CandleOutput has staleness_seconds populated
  - Run vol service — verify stale options excluded from surface fit

## Phase 4: Caching + efficiency (P2)

- [x] [AGENT] P2. URDI adapter caching — fetch once, slice per date
  - Already implemented: `get_instruments_cached()` on BaseReferenceDataAdapter
  - TTL cache (1h default), per instrument_type filter key
  - Subclasses inherit; Tardis adapter already uses it
- [x] [AGENT] P2. DeFi GraphQL token-address filtering
  - Added `DEFI_MAJOR_ASSET_ADDRESSES` (34 entries) and `DEFI_MAJOR_ASSET_ADDRESS_LIST` to UAC
  - Updated Uniswap V2/V3/V4: `token0_in/token1_in` address filtering in `_query_pools()`
  - Updated Aave: `underlyingAsset_in` filtering via `_build_reserves_query()`
  - Morpho: already filters `chainId_in: [1]`, address filter not supported by API
  - Result: only relevant pools/reserves returned from subgraph

## Phase 5: MTDS plan completion (mark done)

- [x] [AGENT] P0. Update MTDS streaming sharding plan readiness to C2
  - All phases 1-5 marked complete
  - BINANCE-FUTURES timeout fixed (600s timeout)
  - DeFi Alchemy key resolved
  - Readiness: code=C2, deployment=D0, business=B0

## Success Criteria

- All 12 venues in MTDS E2E audit PASS (currently 11/12, Kalshi remaining)
- GCS paths use YYYY-MM-DD format (no ISO datetime)
- Futures roll adjuster produces continuous ES series for features
- Session times utility used by at least one features service
- staleness_seconds visible in options candle parquet output
- URDI adapter caching: batch run for 30-day date range makes 1 API call (not 30)
