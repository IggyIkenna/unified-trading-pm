---
title: "MTDS Streaming Sharding — venue×data_type batch downloads with memory management"
owner: agent
priority: P0
locked_by: live-defi-rollout
locked_since: 2026-03-27
readiness:
  code: C0
  deployment: D0
  business: B0
---

# MTDS Streaming Sharding

## Problem

market-tick-data-service cannot download tick data for any venue. The `umi_tick_provider.py` calls
`adapter.download_batch(date, data_types)` but UMI CeFi/TradFi adapters don't implement this method. Additionally, large
venues (Binance trades = multi-GB per day) will OOM if loaded entirely into memory.

## Context

### Current state (broken)

- `umi_tick_provider.py` calls `adapter.download_batch(date, data_types)` on all adapters
- UMI CeFi adapters (Binance, Bybit, etc.) have `download_market_data(exchange, symbol, data_type, date)` —
  per-instrument
- UMI TardisAdapter has `download_csv(exchange, data_type, date)` — already batch per venue+data_type
- UMI DatabentoAdapter has `download_batch(dataset, symbols, data_type, date)` — batch per dataset+data_type
- DeFi BaseDefiAdapter has `download_batch(date, data_types)` — added this session, loads instruments from GCS
- Sports OddsApiAdapter has `download_batch(date, data_types)` — works

### Target architecture

- **Shard = venue × data_type** (e.g. BINANCE-SPOT/trades, CME/trades, AAVEV3-ETHEREUM/rate_indices)
- One API call per shard (batch — all instruments for that venue+data_type in one call)
- Streaming writes: download in chunks, flush to GCS per chunk, clear memory
- GCS path: `raw_tick_data/by_date/day={date}/venue={venue}/data_type={type}/ticks.parquet`
- CLI filter: `--instrument-ids BTC-USDT,ETH-USDT` to slice for testing or resource limits

### Data volume estimates (single day)

| Venue           | Data type    | Approx size | Instruments |
| --------------- | ------------ | ----------- | ----------- |
| BINANCE-SPOT    | trades       | 2-5 GB      | 48          |
| BINANCE-FUTURES | trades       | 3-8 GB      | 33          |
| DERIBIT         | trades       | 500 MB-1 GB | 2,117       |
| CME             | trades       | 200-500 MB  | 304         |
| NYSE            | trades       | 1-3 GB      | 212         |
| AAVEV3-ETHEREUM | rate_indices | 10 MB       | 51          |

### Storage pattern (confirmed from git history ~Feb 9 2026)

- **Instruments:** one parquet per venue — all instrument types together (options chain = single file, not one per
  option)
- **Tick data:** one parquet per venue×data_type shard — all instruments for that combo in one file
- **instrument_ids filter:** `VENUE:TYPE:SYMBOL` format, parsed to extract venue, applied pre/post download

### Memory budget

Target: **< 2 GB peak RSS** per shard. Stream in 50 MB chunks via local temp file + PyArrow row group appending. Temp
file grows on disk (SSD), uploaded to GCS at close, then deleted.

## Execution phases

```
Phase 1: Core streaming infrastructure (UTL)
    ↓
Phase 2: CeFi — Tardis download_batch + streaming (UMI)
    ↓  (parallel)
Phase 2b: TradFi — Databento download_batch + streaming (UMI)
    ↓  (parallel)
Phase 2c: DeFi — already wired, verify streaming
    ↓
Phase 3: MTDS orchestrator — shard by venue×data_type (MTDS)
    ↓
Phase 4: CLI --instrument-ids filter + --data-types filter
    ↓
Phase 5: Verify all venues via CLI
```

## Phase 1: Streaming write infrastructure (UTL)

**Goal:** A `StreamingParquetWriter` in UTL that accepts DataFrame chunks and writes a **single parquet file** to GCS —
not multiple part files. Uses a local temp file with PyArrow row group appending, then uploads once to GCS at close.

- [ ] [AGENT] P0. Add `StreamingParquetWriter` to `unified_trading_library/io/streaming_writer.py`
  - Constructor: `StreamingParquetWriter(bucket, gcs_path, flush_threshold_mb=50)`
  - Method: `write_chunk(df: pd.DataFrame)` — converts to PyArrow table, appends as row group to local temp file
  - Method: `close() -> int` — uploads the single temp file to GCS, deletes local temp, returns bytes written
  - Uses `tempfile.NamedTemporaryFile` for local staging — no memory accumulation
  - PyArrow `ParquetWriter.write_table()` appends row groups to a single file (native support)
  - One file in GCS: `day={date}/venue={venue}/data_type={type}/ticks.parquet`
  - Uses `get_storage_client().upload_file()` for the final GCS upload
- [ ] [AGENT] P0. Export from UTL `__init__.py`

**Output:** One parquet file per shard in GCS. Peak memory = one chunk (~50MB DataFrame) at any time. The local temp
file grows on disk but is deleted after upload.

## Phase 2: UMI adapter download_batch() — CeFi via Tardis

**Goal:** TardisAdapter gets `download_batch(venue, date, data_type, instrument_ids=None)` that streams CSV data and
yields DataFrame chunks.

- [ ] [AGENT] P0. Add `download_batch()` to UMI `TardisAdapter` in `adapters/tradfi/tardis_adapter.py`
  - Signature: `async def download_batch(self, date, data_types, instrument_ids=None) -> pd.DataFrame`
  - Internally calls `download_csv(exchange, data_type, date)` per data_type
  - Tardis CSV download is already streamed by the SDK — the response is a file path
  - Read the CSV in chunks (`pd.read_csv(path, chunksize=100_000)`)
  - If `instrument_ids` provided, filter each chunk to only those symbols
  - Concatenate chunks into final DataFrame (or yield for streaming)
  - Maps canonical venue names to Tardis exchange names via VenueMapping
- [ ] [AGENT] P0. Update `umi_tick_provider.py` CeFi routing to use TardisAdapter directly
  - Route BINANCE-SPOT/FUTURES, BYBIT, OKX, DERIBIT, COINBASE, UPBIT → TardisAdapter
  - Pass canonical venue → Tardis exchange name translation
  - Pass `instrument_ids` filter if provided

**Success:**
`python3 -m market_tick_data_service --operation download --mode batch --category CEFI --venues BINANCE-SPOT --data-types trades --start-date 2026-03-23`
downloads trades and writes to GCS.

## Phase 2b: UMI adapter download_batch() — TradFi via Databento (PARALLEL with Phase 2)

- [ ] [AGENT] P0. Add `download_batch(date, data_types, instrument_ids=None) -> pd.DataFrame` to UMI `DatabentoAdapter`
  - Wraps existing `timeseries.get_range()` calls
  - Uses `TRADFI_DATABENTO_INSTRUMENTS` from UAC to get symbols per dataset
  - One call per dataset × data_type
  - `instrument_ids` filter applied post-fetch
- [ ] [AGENT] P0. Update `umi_tick_provider.py` TradFi routing
  - Route CME, ICE, NYSE, NASDAQ → DatabentoAdapter
  - Map venue → dataset via UAC registry

**Success:** `--category TRADFI --venues CME --data-types trades` works.

## Phase 2c: DeFi verification (PARALLEL with Phase 2)

- [ ] [AGENT] P1. Verify `BaseDefiAdapter.download_batch()` works end-to-end for AAVEV3-ETHEREUM
  - Instruments loaded from GCS (instruments-service output)
  - `download_market_data()` called per instrument
  - Results aggregated into DataFrame
- [ ] [AGENT] P1. Add `instrument_ids` filter support to `BaseDefiAdapter.download_batch()`

**Success:** `--category DEFI --venues AAVEV3-ETHEREUM --data-types rate_indices` works.

## Phase 3: MTDS orchestrator — venue×data_type sharding

**Goal:** Orchestrator processes one shard (venue×data_type) at a time, not all data_types together.

- [ ] [AGENT] P0. Refactor `process_ticks()` to iterate `(venue, data_type)` pairs
  - Current: one `fetch_tick_data_for_venue(venue, date, data_types=[...])` call
  - New: for each venue, for each data_type, call `fetch_tick_data_for_venue(venue, date, data_types=[dt])`
  - Concurrency: up to 4 shards in parallel (Semaphore)
  - Each shard writes to `day={date}/venue={venue}/data_type={type}/ticks.parquet`
- [ ] [AGENT] P0. Wire `StreamingParquetWriter` into the write path
  - All shards use StreamingParquetWriter — adapters call `writer.write_chunk(df)` per chunk
  - `writer.close()` uploads the single parquet to GCS and cleans up the temp file
  - Small shards (DeFi ~10 MB) just write one chunk then close — no overhead
- [ ] [AGENT] P0. Update ManifestWriter to track per-shard availability
  - Index now has `(date, venue, data_type) → record_count`

**Success:** MTDS processes BINANCE-SPOT/trades as one shard, BINANCE-SPOT/book_snapshot_5 as another, without exceeding
2 GB RSS.

## Phase 4: CLI --instrument-ids filter

- [ ] [AGENT] P0. Add `--instrument-ids` argument to MTDS CLI
  - Accepts comma-separated list: `--instrument-ids BTC-USDT,ETH-USDT`
  - Passed through to `process_ticks()` → `fetch_tick_data_for_venue()` → adapter
  - Adapter filters to only those instruments (pre-download where API supports it, post-download otherwise)
- [ ] [AGENT] P1. Add `--max-instruments` argument for resource-limited runs
  - `--max-instruments 5` → only process first 5 instruments per venue (for testing)

**Success:** `--venues BINANCE-SPOT --data-types trades --instrument-ids BTC-USDT,ETH-USDT` downloads only BTC and ETH
trades.

## Phase 5: End-to-end verification

- [ ] [AGENT] P0. CeFi: BINANCE-SPOT/trades (1 instrument via --instrument-ids BTC-USDT)
- [ ] [AGENT] P0. CeFi: DERIBIT/trades (1 instrument via --instrument-ids BTC-PERPETUAL)
- [ ] [AGENT] P0. CeFi: HYPERLIQUID/trades (1 instrument)
- [ ] [AGENT] P0. TradFi: CME/trades (1 instrument via --instrument-ids ES)
- [ ] [AGENT] P0. TradFi: NYSE/trades (1 instrument via --instrument-ids AAPL)
- [ ] [AGENT] P0. DeFi: AAVEV3-ETHEREUM/rate_indices
- [ ] [AGENT] P0. DeFi: UNISWAPV3-ETHEREUM/trades (if available)
- [ ] [AGENT] P1. Sports: ODDS_API (already works)
- [ ] [AGENT] P1. Prediction: POLYMARKET/trades

**Success:** All venues produce non-empty parquet in GCS with correct schema.

## Pre-audit manifest

| Repo                     | Files affected                       | Action                                  |
| ------------------------ | ------------------------------------ | --------------------------------------- |
| unified-market-interface | adapters/tradfi/tardis_adapter.py    | Add download_batch()                    |
| unified-market-interface | adapters/tradfi/databento_adapter.py | Add download_batch()                    |
| unified-market-interface | adapters/defi/base_defi_adapter.py   | Add instrument_ids filter               |
| market-tick-data-service | adapters/umi_tick_provider.py        | Rewrite routing for all categories      |
| market-tick-data-service | engine/orchestrator.py               | Shard by venue×data_type                |
| market-tick-data-service | cli/main.py or **main**.py           | Add --instrument-ids, --max-instruments |
| unified-trading-library  | io/streaming_writer.py               | New: StreamingParquetWriter             |
| unified-trading-library  | manifest_writer.py                   | Add data_type to availability index     |

## Risks

1. **Tardis CSV download size** — Binance trades can be 5+ GB/day. Streaming read + chunked GCS write mitigates this but
   network bandwidth is the bottleneck (~5 min for 5 GB on fast connection).
2. **Databento rate limits** — monthly unlimited plan, but concurrent requests may hit transient 429s. Existing retry
   logic in UMI handles this.
3. **DeFi RPC rate limits** — Aave rate_indices queries The Graph + Alchemy RPC per instrument. 51 instruments × 24
   sample blocks = 1,224 RPC calls. May need throttling.
