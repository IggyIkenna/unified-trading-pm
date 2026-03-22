---
title: "E2E Test: market-data-processing-service"
service: market-data-processing-service
date: 2026-03-22
status: pending
---

# E2E Test: market-data-processing-service

Follows `procedure.md`. Pipeline position: #3 (depends on market-tick-data-service for raw ticks).

## Runtime Topology

- **Cluster:** data_pipeline (L1-L2)
- **Upstream:** market-tick-data-service (raw_tick_data via GCS/PubSub/in_memory)
- **Downstream:** features-delta-one-service, features-volatility-service, features-cross-instrument-service,
  features-commodity-service, features-sports-service, risk-and-exposure-service, strategy-service, market-data-api (all
  via processed_candles_ohlcv)
- **Schedule:** Batch = process date-range of raw ticks into OHLCV candles; Live = continuous timer-aligned candle
  processing via PubSub
- **Sharding:** `--max-results` for limiting instruments per shard

## Operations

| Operation | What it does                               | Expected output                              |
| --------- | ------------------------------------------ | -------------------------------------------- |
| `process` | Aggregate raw tick data into OHLCV candles | Parquet candle files per instrument per date |
| `list`    | List available instruments/categories      | Console output                               |

## Candle Processing

Aggregates raw trades into standardised OHLCV candles at multiple timeframes (1m, 5m, 15m, 1h, 4h, 1d). Output feeds
directly into all 7 feature services and the strategy service.

## Frontend API Requirements

- `GET /market-data/candles` — returns OHLCV data for charts. The API in mock mode seeds 200 candles per instrument per
  interval.
- WebSocket candle updates — live mode appends new candles to the stream.
- **E2E validation:** Candle output schema must match what unified-trading-api expects. Verify column names:
  `timestamp, open, high, low, close, volume, instrument_id, interval`.

## Known Issues to Audit (from instruments-service)

| Issue                           | Audit check                                  | How to verify                           |
| ------------------------------- | -------------------------------------------- | --------------------------------------- |
| #1 `load_dotenv(override=True)` | Check entry point                            | `rg "load_dotenv.*override" --type py`  |
| #2 `--dry-run` not enforced     | Run with `--dry-run`, check no writes        | Verify "UCI dry-run mode ACTIVE" logged |
| #6 Asyncio nesting              | Check if candle processing nests event loops | Run batch, watch for RuntimeError       |
| #8 Category fallthrough         | `--category PREDICTION`                      | Should skip gracefully                  |
| #3 Hardcoded bucket names       | Check `.env`                                 | Remove `*_GCS_BUCKET_*` vars            |

## Test Matrix

### Phase 1: Startup Validation

| #   | Env vars                                                                        | Expected                  | Status |
| --- | ------------------------------------------------------------------------------- | ------------------------- | ------ |
| 1.1 | `CLOUD_PROVIDER=gcp ENVIRONMENT=dev CLOUD_MOCK_MODE=false TESTNET_MODE=mainnet` | OK                        |        |
| 1.2 | `CLOUD_PROVIDER=local ENVIRONMENT=dev CLOUD_MOCK_MODE=true`                     | OK                        |        |
| 1.3 | `CLOUD_PROVIDER=aws ENVIRONMENT=dev CLOUD_MOCK_MODE=true`                       | OK                        |        |
| 1.4 | `CLOUD_PROVIDER=azure`                                                          | STARTUP_VALIDATION_FAILED |        |
| 1.5 | `CLOUD_MOCK_MODE=maybe`                                                         | Pydantic validation error |        |

### Phase 2: Dry-Run (batch, reads upstream tick data, no writes)

| #   | Operation | Category | Expected                                               | Status |
| --- | --------- | -------- | ------------------------------------------------------ | ------ |
| 2.1 | process   | cefi     | Reads raw ticks from GCS, aggregates candles, no write |        |
| 2.2 | process   | tradfi   | Reads Databento raw ticks, aggregates, no write        |        |
| 2.3 | process   | defi     | Reads DeFi tick data, aggregates, no write             |        |
| 2.4 | list      | cefi     | Lists available instruments                            |        |

### Phase 3: Real Writes (dev)

| #   | Operation | Category | GCS check                                    | Status |
| --- | --------- | -------- | -------------------------------------------- | ------ |
| 3.1 | process   | cefi     | Verify OHLCV parquet per instrument per date |        |
| 3.2 | process   | tradfi   | Verify in TRADFI bucket                      |        |
| 3.3 | process   | defi     | Verify in DEFI bucket                        |        |

### Phase 4: Category Sweep (MANDATORY)

| #   | Category   | Expected                                 | Status |
| --- | ---------- | ---------------------------------------- | ------ |
| 4.1 | cefi       | Process CeFi raw ticks → OHLCV candles   |        |
| 4.2 | tradfi     | Process TradFi raw ticks → OHLCV candles |        |
| 4.3 | defi       | Process DeFi raw ticks → OHLCV candles   |        |
| 4.4 | sports     | Explicit skip or "not applicable" log    |        |
| 4.5 | prediction | Explicit skip or "not applicable" log    |        |

### Phase 5: Live Mode (timer-aligned continuous processing)

Live mode processes incoming ticks into candles in real-time, triggered by PubSub subscription.

| #   | What                           | Expected                                          | Status |
| --- | ------------------------------ | ------------------------------------------------- | ------ |
| 5.1 | `--mode live --category cefi`  | Subscribes to PubSub, processes incoming ticks    |        |
| 5.2 | Timer alignment                | Candles close at aligned intervals (1m, 5m, etc.) |        |
| 5.3 | PubSub transport active        | "Subscribed to topic" logged                      |        |
| 5.4 | Graceful shutdown              | Ctrl-C → flush partial candle, clean exit         |        |
| 5.5 | Co-located in_memory transport | When on same VM as MTDS, uses in_memory transport |        |

### Phase 5b: Mock vs Real A/B Testing

| #    | What                                | Expected                                           | Status |
| ---- | ----------------------------------- | -------------------------------------------------- | ------ |
| 5b.1 | Process mock tick data in mock mode | Same candle schema, local sink                     |        |
| 5b.2 | Process real tick data in real mode | Same candle schema, GCS sink                       |        |
| 5b.3 | Compare candle schemas              | Identical: timestamp, O, H, L, C, V, instrument_id |        |
| 5b.4 | Switch via `CLOUD_MOCK_MODE`        | Only data source changes, not processing logic     |        |

### Phase 6: Mock Mode

| #   | Scenario              | What it tests                                 | Expected                                | Status |
| --- | --------------------- | --------------------------------------------- | --------------------------------------- | ------ |
| 6.1 | `--scenario default`  | Normal mock candle processing                 | Mock tick data → candles, local sink    |        |
| 6.2 | `--scenario stress`   | High cardinality (many instruments/intervals) | No OOM, all candles written             |        |
| 6.3 | Missing upstream data | No tick data for a venue                      | Skip venue, log warning, continue       |        |
| 6.4 | Corrupt tick data     | Malformed parquet from upstream               | Error logged per file, others processed |        |
| 6.5 | AWS provider          | `CLOUD_PROVIDER=aws CLOUD_MOCK_MODE=true`     | S3 sink path, same candle format        |        |
| 6.6 | Max-results limiting  | `--max-results 5`                             | Only 5 instruments processed            |        |

### Phase 7: Observability

| #   | Check                   | Expected                                      | Status |
| --- | ----------------------- | --------------------------------------------- | ------ |
| 7.1 | ServiceRuntime log line | All dimensions logged                         |        |
| 7.2 | UEI events              | STARTED, per-instrument COMPLETED, COMPLETED  |        |
| 7.3 | Shard-level isolation   | One instrument failure doesn't crash others   |        |
| 7.4 | Candle quality metrics  | Count of candles per interval logged          |        |
| 7.5 | Error classification    | ADAPTER_FETCH_FAILED for upstream read errors |        |

## Issues Found

| Issue | Severity | Fixed? |
| ----- | -------- | ------ |

## Next Service

After market-data-processing-service passes all phases → proceed to `004_features_delta_one_service.md`
