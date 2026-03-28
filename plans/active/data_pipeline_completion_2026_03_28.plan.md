---
title: "Data Pipeline Completion — remaining items from instruments + MTDS + features sessions"
owner: agent
priority: P0
locked_by: live-defi-rollout
locked_since: 2026-03-28
readiness:
  code: C1
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

- [ ] [AGENT] P0. Commit uncommitted work across 9 repos (linter changes, prior session diffs)
- [ ] [AGENT] P0. Fix GCS path date format: `day=2026-03-23T00:00:00+00:00` → `day=2026-03-23`
  - In MTDS orchestrator `process_ticks()`: normalize date to `str(date)[:10]` before passing to
    StreamingParquetWriter gcs_path

## Phase 2: Remaining adapters (P1)

- [ ] [AGENT] P1. Kalshi adapter `download_batch()` — same pattern as Polymarket
  - Load condition_ids from GCS instruments JSON
  - Fetch trades via Kalshi Data API
  - Stream to writer
- [ ] [AGENT] P1. Hyperliquid historical tick data via S3 archive
  - Batch mode: download from `s3://hyperliquid-archive/` (L2 book + asset contexts)
  - Live mode: REST API (already exists in `hyperliquid_adapter.py`)
  - Wire into MTDS routing for HYPERLIQUID venue
  - Aster: similar pattern if public archive exists, else REST only
- [ ] [AGENT] P1. Polymarket instruments: convert to parquet output (currently JSON)
  - instruments-service prediction adapter should write parquet like all other categories
  - Remove JSON fallback in PolymarketAdapter._load_condition_ids_from_gcs

## Phase 3: Features pipeline (P1)

- [ ] [AGENT] P1. Futures roll adjuster: wire into features-delta-one-service as preprocessing
  - `futures_roll_adjuster.py` exists with ratio-based back-adjustment
  - Needs to run before feature computation on TradFi futures candles
  - Input: per-contract candles from MDPS. Output: continuous adjusted series.
  - Configure: roll calendar per product (ES, CL, GC, etc.)
- [ ] [AGENT] P1. Session times utility in UAC (stateless, no extra instrument columns)
  - `from unified_api_contracts import is_trading_hours, get_session_times`
  - Uses `exchange_calendars` internally, handles DST
  - Features services call this to distinguish expected gaps from anomalies
  - CME: Sunday 5pm CT – Friday 4pm CT (22hr session)
  - NYSE/NASDAQ: 9:30am – 4pm ET (6.5hr session)
  - Crypto/DeFi: always returns True (24/7)
- [ ] [AGENT] P1. Verify staleness_seconds flows end-to-end with real Deribit options data
  - Run MDPS on Deribit options_chain tick data
  - Check CandleOutput has staleness_seconds populated
  - Run vol service — verify stale options excluded from surface fit

## Phase 4: Caching + efficiency (P2)

- [ ] [AGENT] P2. URDI adapter caching — fetch once, slice per date
  - Tardis: single API call returns all instruments with availableSince/availableTo.
    Cache at preflight, slice per target date in-memory.
  - DeFi (The Graph): single query returns all pools with createdAtTimestamp.
    Cache at preflight, filter by createdAt ≤ target_date.
  - Databento: point-in-time snapshot. Cache per run (daily batch = 1 fetch).
  - Hyperliquid/Aster: cache at preflight (24/7 crypto, list doesn't change within batch)
  - Implementation: `get_instruments_cached()` on BaseReferenceDataAdapter (TTL cache, already stubbed)
- [ ] [AGENT] P2. DeFi GraphQL token-address filtering
  - Add `DEFI_MAJOR_ASSET_ADDRESSES` to UAC: symbol → Ethereum contract address (55 entries)
  - Update Uniswap V2/V3/V4 adapters: `where: { token0_in: [...], token1_in: [...] }`
  - Update Balancer: `where: { tokenList_contains: [...] }`
  - Update Curve: similar token filter
  - For lending (Aave, Morpho): `where: { reserve_in: [...] }`
  - Result: only relevant pools returned from subgraph, no client-side filtering

## Phase 5: MTDS plan completion (mark done)

- [ ] [AGENT] P0. Update MTDS streaming sharding plan readiness to C2
  - Mark phases 1-5 as complete (streaming writer, adapter routing, CLI, e2e)
  - Close BINANCE-FUTURES timeout issue (fixed with 600s timeout)
  - Update DeFi status from PENDING to PASS (Alchemy key resolved)
  - Mark readiness: code=C2, deployment=D0, business=B0

## Success Criteria

- All 12 venues in MTDS E2E audit PASS (currently 11/12, Kalshi remaining)
- GCS paths use YYYY-MM-DD format (no ISO datetime)
- Futures roll adjuster produces continuous ES series for features
- Session times utility used by at least one features service
- staleness_seconds visible in options candle parquet output
- URDI adapter caching: batch run for 30-day date range makes 1 API call (not 30)
