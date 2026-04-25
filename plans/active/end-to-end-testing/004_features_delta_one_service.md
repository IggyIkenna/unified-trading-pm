---
title: "E2E Test: features-delta-one-service"
service: features-delta-one-service
date: 2026-03-22
status: pending
---

# E2E Test: features-delta-one-service

Follows `procedure.md`. Pipeline position: #4 (L3 features layer -- depends on processed OHLCV candles from upstream).

## Runtime Topology

- **Cluster:** features (L3)
- **Upstream:** market-data-processing-service (processed_candles_ohlcv via GCS), instruments-service
  (instruments_universe via GCS)
- **Downstream:** ml-training-service, ml-inference-service, features-cross-instrument-service,
  features-multi-timeframe-service
- **Schedule:** Batch = date-range historical compute; Live = Pub/Sub subscriber computing features on candle events
- **Computes:** returns, spreads, rolling stats, momentum indicators, VWAP, candlestick patterns, market structure,
  microstructure, funding/OI (CEFI/DEFI), futures basis (TRADFI), swing outcome targets

## Operations

| Operation      | What it does                                          | Expected output                           |
| -------------- | ----------------------------------------------------- | ----------------------------------------- |
| `compute`      | Batch/incremental feature computation from OHLCV data | Parquet per instrument per date per group |
| `compute-live` | Live streaming feature computation via Pub/Sub        | Features emitted on each candle event     |

## Feature Groups

| Group                   | Category  | Description                                                |
| ----------------------- | --------- | ---------------------------------------------------------- |
| `technical_indicators`  | All       | Combined technical indicator suite                         |
| `moving_averages`       | All       | SMA, EMA, WMA variants                                     |
| `oscillators`           | All       | RSI, MACD, Stochastic                                      |
| `volatility_realized`   | All       | Realized volatility measures                               |
| `momentum`              | All       | Rate of change, momentum indicators                        |
| `volume_analysis`       | All       | Volume profile, OBV                                        |
| `vwap`                  | All       | Volume-weighted average price                              |
| `candlestick_patterns`  | All       | Pattern recognition (doji, hammer, etc.)                   |
| `market_structure`      | All       | Support/resistance, trend structure                        |
| `returns`               | All       | Log returns, simple returns                                |
| `round_numbers`         | All       | Proximity to round price levels                            |
| `streaks`               | All       | Consecutive up/down bar streaks                            |
| `temporal`              | All       | Time-of-day, day-of-week features                          |
| `economic_events`       | All       | Economic calendar proximity                                |
| `microstructure`        | All       | Book data (book_snapshot_5 for CEFI/DEFI, tbbo for TRADFI) |
| `funding_oi`            | CEFI/DEFI | Perpetual funding rates and open interest                  |
| `liquidations`          | CEFI/DEFI | Liquidation event features                                 |
| `futures_basis`         | TRADFI    | Futures basis and term structure                           |
| `volume_flow`           | TRADFI    | Uptick/downtick volume flow analysis                       |
| `targets`               | All       | ML training targets                                        |
| `swing_outcome_targets` | All       | Swing high/low outcome targets for ML                      |
| `ALL`                   | All       | Run all applicable groups for the category                 |

## Frontend API Requirements

The unified-trading-api serves feature data endpoints that the UI consumes:

- `GET /analytics/features` -- feature values for strategy health charts
- Feature importance displays in strategy-ui and trading-analytics-ui
- Strategy health charts showing feature drift and staleness

**E2E validation:** After batch compute completes, verify that the output parquet schema is compatible with what the
analytics API reads. In real mode (Tier 2), the API reads from the actual GCS output of this service.

## Known Issues to Audit (from instruments-service)

| Issue                               | Audit check                                                        | How to verify                                                               |
| ----------------------------------- | ------------------------------------------------------------------ | --------------------------------------------------------------------------- |
| #1 `load_dotenv(override=True)`     | Check `cli/main.py` for `override=True`                            | `rg "load_dotenv.*override" --type py`                                      |
| #2 `--dry-run` not enforced         | Check if dry-run actually prevents GCS writes                      | Run with `--dry-run`, check no GCS files created                            |
| #6 Asyncio nesting                  | Check ComputeHandler/ComputeLiveHandler for nested `asyncio.run()` | Run and check for event loop errors                                         |
| #8 PREDICTION category fallthrough  | Check category routing with unknown category                       | `--asset-group PREDICTION` should be rejected by parser (not in CATEGORIES) |
| #3 Hardcoded bucket names in `.env` | Check `.env` for `*_GCS_BUCKET_*`                                  | Remove if present, use UCI `get_bucket_name()`                              |
| #7 Raw API keys in `.env`           | Check for plaintext API keys                                       | Only SM reference names allowed                                             |

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

| #   | Operation | Category | Feature group         | Expected                                               | Status |
| --- | --------- | -------- | --------------------- | ------------------------------------------------------ | ------ |
| 2.1 | compute   | CEFI     | technical_indicators  | Read candles from GCS, compute features, no writes     |        |
| 2.2 | compute   | TRADFI   | futures_basis         | Read TRADFI candles, compute basis features, no writes |        |
| 2.3 | compute   | DEFI     | funding_oi            | Read DEFI candles, compute funding/OI, no writes       |        |
| 2.4 | compute   | CEFI     | ALL                   | All feature groups computed, no writes                 |        |
| 2.5 | compute   | CEFI     | microstructure        | Read book_snapshot_5 data, compute microstructure      |        |
| 2.6 | compute   | TRADFI   | microstructure        | Read tbbo data, compute microstructure                 |        |
| 2.7 | compute   | CEFI     | swing_outcome_targets | Compute ML swing targets, no writes                    |        |

### Phase 3: Real Writes (dev, CSV sampling on)

| #   | Operation | Category | Feature group        | GCS check                                | Status |
| --- | --------- | -------- | -------------------- | ---------------------------------------- | ------ |
| 3.1 | compute   | CEFI     | technical_indicators | Verify parquet per instrument per date   |        |
| 3.2 | compute   | TRADFI   | futures_basis        | Verify parquet in TRADFI features bucket |        |
| 3.3 | compute   | DEFI     | funding_oi           | Verify parquet in DEFI features bucket   |        |
| 3.4 | compute   | CEFI     | ALL                  | Verify all feature groups written        |        |

### Phase 4: Category Sweep (MANDATORY)

| #   | Category   | Expected behaviour                                                                                    | Status |
| --- | ---------- | ----------------------------------------------------------------------------------------------------- | ------ |
| 4.1 | CEFI       | All feature groups computed (including funding_oi, liquidations, microstructure with book_snapshot_5) |        |
| 4.2 | TRADFI     | All TRADFI groups computed (including futures_basis, volume_flow, microstructure with tbbo)           |        |
| 4.3 | DEFI       | All DEFI groups computed (including funding_oi, liquidations)                                         |        |
| 4.4 | SPORTS     | Rejected by parser (SPORTS not in CATEGORIES list). Clear error, no crash                             |        |
| 4.5 | PREDICTION | Rejected by parser (PREDICTION not in CATEGORIES list). Clear error, no crash                         |        |

**Category-specific validation:** CEFI/DEFI-specific groups (`funding_oi`, `liquidations`) must reject TRADFI.
TRADFI-specific groups (`futures_basis`, `volume_flow`) must reject CEFI/DEFI. Verify via `validate_args()`.

### Phase 5: Live Mode (Pub/Sub candle subscriber)

This service's live mode (`compute-live`) subscribes to Pub/Sub candle events and computes features on each new candle.

| #   | What                                                                                           | Expected                                                      | Status |
| --- | ---------------------------------------------------------------------------------------------- | ------------------------------------------------------------- | ------ |
| 5.1 | `--operation compute-live --mode live --asset-group CEFI --feature-group technical_indicators` | Subscribes to candle events, computes features per candle     |        |
| 5.2 | PubSub transport (live mode)                                                                   | Features published to downstream PubSub topics                |        |
| 5.3 | Graceful shutdown on Ctrl-C                                                                    | Clean exit, LiveHandler.cleanup() called, no partial writes   |        |
| 5.4 | Event logging                                                                                  | UEI events: STARTED, per-instrument COMPLETED/FAILED, STOPPED |        |
| 5.5 | Circuit breaker on processing failure                                                          | Single instrument failure doesn't crash others                |        |

### Phase 5b: Mock vs Real A/B Testing

**Principle:** Same service code, different data source. Mock mode uses pre-generated seed data via
`run_mock_pipeline()`; real mode reads actual OHLCV candles from GCS. The service should produce identical output
structure regardless.

| #    | What                               | Expected                                                                | Status |
| ---- | ---------------------------------- | ----------------------------------------------------------------------- | ------ |
| 5b.1 | Run batch CEFI in mock mode        | `run_mock_pipeline()` called, writes to local sink, same parquet schema |        |
| 5b.2 | Run batch CEFI in real mode        | Reads from GCS candles, writes to GCS, same parquet schema              |        |
| 5b.3 | Compare output schemas             | Identical column names, types, partitioning                             |        |
| 5b.4 | Switch data source via CLI/env var | `CLOUD_MOCK_MODE=true` vs `false` -- same code path                     |        |

### Phase 6: Mock Mode (local, no credentials)

| #   | Scenario                         | What it tests                                     | Expected                                                         | Status |
| --- | -------------------------------- | ------------------------------------------------- | ---------------------------------------------------------------- | ------ |
| 6.1 | `--scenario default`             | Normal mock feature computation                   | Mock data generated via `run_mock_pipeline()`, local sink        |        |
| 6.2 | `--scenario stress`              | High cardinality instruments (10x normal)         | Service handles memory, writes succeed                           |        |
| 6.3 | Missing upstream candles         | No processed_candles_ohlcv for date range         | Service logs "no upstream data", exits 0 or warns                |        |
| 6.4 | Stale upstream data              | Candles from 7+ days ago only                     | Service warns about staleness, continues                         |        |
| 6.5 | Invalid feature group + category | `--feature-group funding_oi --asset-group TRADFI` | `validate_args()` raises ValueError, clean exit                  |        |
| 6.6 | Preflight only                   | `--preflight-only`                                | Lookback candle count validated, no processing                   |        |
| 6.7 | Skip dependency check            | `--skip-dependency-check`                         | Warning logged, processing continues without upstream validation |        |
| 6.8 | AWS cloud provider               | `CLOUD_PROVIDER=aws CLOUD_MOCK_MODE=true`         | Uses S3 sink (mocked), same output format                        |        |

### Phase 7: Observability

| #   | Check                   | Expected                                                          | Status |
| --- | ----------------------- | ----------------------------------------------------------------- | ------ |
| 7.1 | ServiceRuntime log line | All dimensions logged at startup                                  |        |
| 7.2 | UEI events              | STARTED, VALIDATION_STARTED, VALIDATION_COMPLETED, STOPPED/FAILED |        |
| 7.3 | Shard-level isolation   | One instrument failure doesn't crash others                       |        |
| 7.4 | Dry-run warning         | "DRY RUN" + "UCI dry-run mode ACTIVE" logged                      |        |
| 7.5 | Error classification    | ADAPTER_FETCH_FAILED events for failed instruments                |        |
| 7.6 | Memory watchdog         | "Memory watchdog started" logged at startup                       |        |
| 7.7 | Processing progress     | Per-instrument/per-group progress logged                          |        |
| 7.8 | GracefulShutdownHandler | Registered at startup, handles SIGTERM/SIGINT                     |        |

## Issues Found

(log in `plans/issues/service_control_surface_issues_2026_03_21.md`)

| Issue | Severity | Fixed? |
| ----- | -------- | ------ |

## Next Service

After features-delta-one-service passes all phases -> proceed to `005_features_volatility_service.md`
