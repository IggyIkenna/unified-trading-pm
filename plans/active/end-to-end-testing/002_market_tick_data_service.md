---
title: "E2E Test: market-tick-data-service"
service: market-tick-data-service
date: 2026-03-22
status: pending
---

# E2E Test: market-tick-data-service

Follows `procedure.md`. Pipeline position: #2 (depends on instruments-service for universe).

## Runtime Topology

- **Cluster:** data_pipeline (L1-L2)
- **Upstream:** instruments-service (instruments_universe via GCS/PubSub) (orderbook_stream)
- **Schedule:** Batch = date-range historical download; Live = persistent WebSocket connections to exchanges
- **Sharding:** `--shard-index` / `--total-shards` for parallel batch download

## Operations

| Operation                | What it does                                 | Expected output                           |
| ------------------------ | -------------------------------------------- | ----------------------------------------- |
| `download`               | Download historical tick data from venues    | Parquet per venue per date per data type  |
| `instruments`            | List/inspect instruments available at venues | Console output: instrument details        |
| `missing-tick-reports`   | Identify gaps in downloaded tick data        | Report of missing date/venue combinations |
| `missing-candle-reports` | Identify gaps in candle data                 | Report of missing candle data             |
| `download-missing-data`  | Fill gaps identified by missing-data reports | Parquet files for missing ranges          |

## Data Types

The service downloads multiple data types per venue: `trades`, `liquidations`, `derivative_ticker`, `book_snapshot_5`,
`options_chain`.

## Frontend API Requirements

The unified-trading-api serves market data endpoints that the UI consumes:

- `GET /market-data/candles` — OHLCV candlestick data (historical)
- `GET /market-data/orderbook` — order book depth (20 bid + 20 ask levels)
- WebSocket `ws://localhost:8030/ws` — live price ticks (500-2000ms intervals)

**E2E validation:** After batch download completes, verify that the data format is compatible with what the API seeds
into MockStateStore. In real mode (Tier 2), the API reads from the actual GCS output of this service.

## Known Issues to Audit (from instruments-service)

| Issue                               | Audit check                                          | How to verify                                     |
| ----------------------------------- | ---------------------------------------------------- | ------------------------------------------------- |
| #1 `load_dotenv(override=True)`     | Check `cli/main.py` for `override=True`              | `rg "load_dotenv.*override" --type py`            |
| #2 `--dry-run` not enforced         | Check if dry-run actually prevents GCS writes        | Run with `--dry-run`, check no GCS files created  |
| #6 Asyncio nesting                  | Check `DownloadOperation` for nested `asyncio.run()` | Known issue — uses `run_in_executor`              |
| #8 PREDICTION category fallthrough  | Check category routing with unknown category         | `--asset-group PREDICTION` should skip gracefully |
| #3 Hardcoded bucket names in `.env` | Check `.env` for `*_GCS_BUCKET_*`                    | Remove if present, use UCI `get_bucket_name()`    |
| #7 Raw API keys in `.env`           | Check for plaintext API keys                         | Only SM reference names allowed                   |

## Test Matrix

### Phase 1: Startup Validation

| #   | Env vars                                                                        | Expected                                 | Status |
| --- | ------------------------------------------------------------------------------- | ---------------------------------------- | ------ |
| 1.1 | `CLOUD_PROVIDER=gcp ENVIRONMENT=dev CLOUD_MOCK_MODE=false TESTNET_MODE=mainnet` | OK                                       |        |
| 1.2 | `CLOUD_PROVIDER=local ENVIRONMENT=dev CLOUD_MOCK_MODE=true`                     | OK                                       |        |
| 1.3 | `CLOUD_PROVIDER=gcp ENVIRONMENT=staging TESTNET_MODE=testnet`                   | OK                                       |        |
| 1.4 | `CLOUD_PROVIDER=aws ENVIRONMENT=dev CLOUD_MOCK_MODE=false`                      | OK (if AWS creds present) or clear error |        |
| 1.5 | `CLOUD_PROVIDER=azure`                                                          | STARTUP_VALIDATION_FAILED                |        |
| 1.6 | `TESTNET_MODE=sandbox`                                                          | STARTUP_VALIDATION_FAILED                |        |
| 1.7 | `CLOUD_MOCK_MODE=maybe`                                                         | Pydantic validation error                |        |

### Phase 2: Dry-Run (batch, real data sources, no writes)

| #   | Operation            | Category   | Expected                                          | Status |
| --- | -------------------- | ---------- | ------------------------------------------------- | ------ |
| 2.1 | download             | CEFI       | Fetch from Tardis REST, no GCS writes             |        |
| 2.2 | download             | TRADFI     | Fetch from Databento, no GCS writes               |        |
| 2.3 | download             | DEFI       | Fetch from Hyperliquid REST, no GCS writes        |        |
| 2.4 | download             | SPORTS     | Should skip gracefully (tick data N/A for sports) |        |
| 2.5 | download             | PREDICTION | Should skip gracefully (not implemented)          |        |
| 2.6 | missing-tick-reports | CEFI       | Report generated, no writes                       |        |
| 2.7 | instruments          | CEFI       | Instrument list printed to console                |        |

### Phase 3: Real Writes (dev, CSV sampling on)

| #   | Operation             | Category | Data types              | GCS check                         | Status |
| --- | --------------------- | -------- | ----------------------- | --------------------------------- | ------ |
| 3.1 | download              | CEFI     | trades, book_snapshot_5 | Verify parquet per venue per date |        |
| 3.2 | download              | TRADFI   | trades                  | Verify parquet in TRADFI bucket   |        |
| 3.3 | download              | DEFI     | trades                  | Verify parquet in DEFI bucket     |        |
| 3.4 | download-missing-data | CEFI     | trades                  | Verify gap-fill writes            |        |

### Phase 4: Category Sweep (MANDATORY)

| #   | Category   | Expected venues/sources                | Expected behaviour                             | Status |
| --- | ---------- | -------------------------------------- | ---------------------------------------------- | ------ |
| 4.1 | CEFI       | Tardis (17+ exchanges)                 | Download from multiple exchanges, GCS verified |        |
| 4.2 | TRADFI     | Databento (CME, ICE, NASDAQ)           | Download equities/futures tick data            |        |
| 4.3 | DEFI       | Hyperliquid, on-chain RPCs             | DeFi tick data (perp prices, pool events)      |        |
| 4.4 | SPORTS     | Explicit "not supported" or empty skip | Clear log, no crash, no fallthrough            |        |
| 4.5 | PREDICTION | Explicit "not supported" or empty skip | Clear log, no crash                            |        |

### Phase 5: Live Mode (WebSocket streaming)

This service's live mode is the REAL live mode — persistent WebSocket connections to exchanges.

| #   | What                                                  | Expected                                                     | Status |
| --- | ----------------------------------------------------- | ------------------------------------------------------------ | ------ |
| 5.1 | `--operation download --mode live --asset-group CEFI` | WebSocket connections to Binance, OKX, etc. via UMI adapters |        |
| 5.2 | Testnet WebSocket connections                         | Connect to Binance testnet WS, OKX testnet                   |        |
| 5.3 | PubSub transport (live mode)                          | Tick data published to PubSub topics                         |        |
| 5.4 | Graceful shutdown on Ctrl-C                           | All WS connections closed, no partial writes                 |        |
| 5.5 | Circuit breaker on connection failure                 | Single venue disconnect doesn't crash others                 |        |
| 5.6 | Reconnection with exponential backoff                 | After disconnect, auto-reconnects                            |        |

### Phase 5b: Mock vs Real A/B Testing

**Principle:** Same service code, different data source. Mock mode points to pre-generated data; real mode points to
actual venue APIs. The service should produce identical output structure regardless.

| #    | What                               | Expected                                                   | Status |
| ---- | ---------------------------------- | ---------------------------------------------------------- | ------ |
| 5b.1 | Run batch CEFI in mock mode        | Reads mock data, writes to local sink, same parquet schema |        |
| 5b.2 | Run batch CEFI in real mode        | Reads from Tardis, writes to GCS, same parquet schema      |        |
| 5b.3 | Compare output schemas             | Identical column names, types, partitioning                |        |
| 5b.4 | Switch data source via CLI/env var | `CLOUD_MOCK_MODE=true` vs `false` — same code path         |        |

### Phase 6: Mock Mode (local, no credentials)

| #   | Scenario                  | What it tests                             | Expected                                        | Status |
| --- | ------------------------- | ----------------------------------------- | ----------------------------------------------- | ------ |
| 6.1 | `--scenario default`      | Normal mock tick data                     | Mock data generated, local sink                 |        |
| 6.2 | `--scenario stress`       | High volume tick data (10x normal)        | Service handles memory, no OOM                  |        |
| 6.3 | Venue disconnect          | Simulate one exchange going down          | Other exchanges continue, error event logged    |        |
| 6.4 | Empty instrument universe | No instruments from upstream              | Service starts, logs "no instruments", exits 0  |        |
| 6.5 | Stale instrument data     | Instruments from 7 days ago               | Service warns about staleness, continues        |        |
| 6.6 | Sharding: shard 0 of 3    | `--shard-index 0 --total-shards 3`        | Processes ~1/3 of venues, writes only its shard |        |
| 6.7 | Sharding: shard 2 of 3    | `--shard-index 2 --total-shards 3`        | Processes remaining ~1/3 of venues              |        |
| 6.8 | AWS cloud provider        | `CLOUD_PROVIDER=aws CLOUD_MOCK_MODE=true` | Uses S3 sink (mocked), same output format       |        |

### Phase 7: Observability

| #   | Check                   | Expected                                             | Status |
| --- | ----------------------- | ---------------------------------------------------- | ------ |
| 7.1 | ServiceRuntime log line | All dimensions logged at startup                     |        |
| 7.2 | UEI events              | STARTED, per-venue COMPLETED/FAILED, final COMPLETED |        |
| 7.3 | Shard-level isolation   | One venue failure doesn't crash others               |        |
| 7.4 | Dry-run warning         | "DRY RUN" + "UCI dry-run mode ACTIVE" logged         |        |
| 7.5 | Error classification    | ADAPTER_FETCH_FAILED events for failed venues        |        |
| 7.6 | Memory watchdog         | Active for live mode (long-running)                  |        |
| 7.7 | Download progress       | Per-venue/per-date progress logged                   |        |

## Issues Found

(log in `plans/archive/issues/service_control_surface_issues_2026_03_21.md`)

| Issue | Severity | Fixed? |
| ----- | -------- | ------ |

## Next Service

After market-tick-data-service passes all phases → proceed to `003_market_data_processing_service.md`
