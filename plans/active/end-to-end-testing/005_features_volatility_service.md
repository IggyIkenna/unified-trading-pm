---
title: "E2E Test: features-volatility-service"
service: features-volatility-service
date: 2026-03-22
status: pending
---

# E2E Test: features-volatility-service

Follows `procedure.md`. Pipeline position: #5 (L3 features layer -- depends on processed OHLCV candles from upstream).

## Runtime Topology

- **Cluster:** features (L3)
- **Upstream:** market-data-processing-service (processed_candles_ohlcv via GCS), instruments-service
  (instruments_universe via GCS)
- **Downstream:** ml-training-service, ml-inference-service, features-cross-instrument-service
- **Schedule:** Batch = date-range historical compute; Live = interval-based periodic recomputation (default 15 min)
- **Computes:** options implied vol, options term structure, futures basis, futures term structure, vol surfaces, skew
  metrics

## Operations

| Operation | What it does                                     | Expected output                           |
| --------- | ------------------------------------------------ | ----------------------------------------- |
| `compute` | Compute volatility features (batch or live mode) | Parquet per instrument per date per group |

**Note:** This service has a single `compute` operation that dispatches to batch or live based on `--mode`. Unlike
features-delta-one-service which has separate `compute` and `compute-live` operations, volatility uses one operation
with mode-based routing via `VolatilityComputeHandler._dispatch()`.

## Feature Groups

| Group                    | Category     | Description                                |
| ------------------------ | ------------ | ------------------------------------------ |
| `options_iv`             | CEFI, TRADFI | Options implied volatility (Deribit, CBOE) |
| `options_term_structure` | CEFI, TRADFI | Options vol term structure across expiries |
| `futures_basis`          | All          | Futures basis and cost-of-carry            |
| `futures_term_structure` | All          | Futures curve shape across tenors          |
| `ALL`                    | All          | Run all applicable groups for the category |

**Category restrictions:** `options_iv` and `options_term_structure` are restricted to CEFI and TRADFI categories only.
`validate_args()` raises ValueError if used with DEFI.

## Frontend API Requirements

The unified-trading-api serves volatility data endpoints that the UI consumes:

- Vol surface charts in trading-analytics-ui (3D surface: strike x expiry x IV)
- Risk dashboard vol metrics (realized vs implied, term structure slope)
- Strategy health charts showing vol regime indicators

**E2E validation:** After batch compute completes, verify that the output parquet schema is compatible with what the
analytics API reads. In real mode (Tier 2), the API reads from the actual GCS output of this service.

## Known Issues to Audit (from instruments-service)

| Issue                               | Audit check                                               | How to verify                                                               |
| ----------------------------------- | --------------------------------------------------------- | --------------------------------------------------------------------------- |
| #1 `load_dotenv(override=True)`     | Check `cli/service_entry.py` for `override=True`          | `rg "load_dotenv.*override" --type py`                                      |
| #2 `--dry-run` not enforced         | Check if dry-run actually prevents GCS writes             | Run with `--dry-run`, check no GCS files created                            |
| #6 Asyncio nesting                  | Check VolatilityComputeHandler for nested `asyncio.run()` | Run and check for event loop errors                                         |
| #8 PREDICTION category fallthrough  | Check category routing with unknown category              | `--asset-group PREDICTION` should be rejected by parser (not in CATEGORIES) |
| #3 Hardcoded bucket names in `.env` | Check `.env` for `*_GCS_BUCKET_*`                         | Remove if present, use UCI `get_bucket_name()`                              |
| #7 Raw API keys in `.env`           | Check for plaintext API keys                              | Only SM reference names allowed                                             |

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

| #   | Operation | Category | Feature group          | Expected                                                                  | Status |
| --- | --------- | -------- | ---------------------- | ------------------------------------------------------------------------- | ------ |
| 2.1 | compute   | CEFI     | options_iv             | Read options data, compute IV surface, no writes                          |        |
| 2.2 | compute   | TRADFI   | options_term_structure | Read TRADFI options, compute term structure, no writes                    |        |
| 2.3 | compute   | CEFI     | futures_basis          | Read futures data, compute basis, no writes                               |        |
| 2.4 | compute   | DEFI     | futures_basis          | Read DEFI futures, compute basis, no writes                               |        |
| 2.5 | compute   | CEFI     | ALL                    | All feature groups computed, no writes                                    |        |
| 2.6 | compute   | DEFI     | options_iv             | Should be rejected by validate_args() (options_iv not available for DEFI) |        |

### Phase 3: Real Writes (dev, CSV sampling on)

| #   | Operation | Category | Feature group          | GCS check                                | Status |
| --- | --------- | -------- | ---------------------- | ---------------------------------------- | ------ |
| 3.1 | compute   | CEFI     | options_iv             | Verify parquet per instrument per date   |        |
| 3.2 | compute   | TRADFI   | options_term_structure | Verify parquet in TRADFI features bucket |        |
| 3.3 | compute   | CEFI     | futures_basis          | Verify parquet in CEFI features bucket   |        |
| 3.4 | compute   | CEFI     | ALL                    | Verify all feature groups written        |        |

### Phase 4: Category Sweep (MANDATORY)

| #   | Category   | Expected behaviour                                                                                      | Status |
| --- | ---------- | ------------------------------------------------------------------------------------------------------- | ------ |
| 4.1 | CEFI       | All feature groups computed (options_iv, options_term_structure, futures_basis, futures_term_structure) |        |
| 4.2 | TRADFI     | All feature groups computed (options from CBOE, futures from CME/ICE)                                   |        |
| 4.3 | DEFI       | Only futures_basis and futures_term_structure computed; options groups rejected                         |        |
| 4.4 | SPORTS     | Rejected by parser (SPORTS not in CATEGORIES list). Clear error, no crash                               |        |
| 4.5 | PREDICTION | Rejected by parser (PREDICTION not in CATEGORIES list). Clear error, no crash                           |        |

**Category-specific validation:** `options_iv` and `options_term_structure` must reject DEFI category. Verify via
`validate_args()` which checks `category not in ["CEFI", "TRADFI"]` for these groups.

### Phase 5: Live Mode (interval-based periodic recomputation)

This service's live mode recomputes volatility features on a periodic interval (default 15 minutes). It uses the same
`compute` operation with `--mode live`.

| #   | What                                                                                          | Expected                                                      | Status |
| --- | --------------------------------------------------------------------------------------------- | ------------------------------------------------------------- | ------ |
| 5.1 | `--operation compute --mode live --asset-group CEFI --feature-group options_iv --interval 15` | Periodic recomputation every 15 minutes                       |        |
| 5.2 | Interval alignment                                                                            | Runs on schedule, processes latest candle data                |        |
| 5.3 | Graceful shutdown on Ctrl-C                                                                   | Clean exit, LiveHandler.cleanup() called                      |        |
| 5.4 | Event logging                                                                                 | UEI events: STARTED, per-instrument COMPLETED/FAILED, STOPPED |        |
| 5.5 | Custom interval                                                                               | `--interval 5` runs every 5 minutes instead of 15             |        |

### Phase 5b: Mock vs Real A/B Testing

**Principle:** Same service code, different data source. Mock mode uses pre-generated seed data via
`run_mock_pipeline()`; real mode reads actual options/futures data from GCS. The service should produce identical output
structure regardless.

| #    | What                               | Expected                                                                | Status |
| ---- | ---------------------------------- | ----------------------------------------------------------------------- | ------ |
| 5b.1 | Run batch CEFI in mock mode        | `run_mock_pipeline()` called, writes to local sink, same parquet schema |        |
| 5b.2 | Run batch CEFI in real mode        | Reads from GCS candles, writes to GCS, same parquet schema              |        |
| 5b.3 | Compare output schemas             | Identical column names, types, partitioning                             |        |
| 5b.4 | Switch data source via CLI/env var | `CLOUD_MOCK_MODE=true` vs `false` -- same code path                     |        |

### Phase 6: Mock Mode (local, no credentials)

| #   | Scenario                         | What it tests                                   | Expected                                                         | Status |
| --- | -------------------------------- | ----------------------------------------------- | ---------------------------------------------------------------- | ------ |
| 6.1 | `--scenario default`             | Normal mock volatility computation              | Mock data generated via `run_mock_pipeline()`, local sink        |        |
| 6.2 | `--scenario stress`              | High cardinality instruments (10x normal)       | Service handles memory, writes succeed                           |        |
| 6.3 | Missing upstream candles         | No processed_candles_ohlcv for date range       | Service logs "no upstream data", exits 0 or warns                |        |
| 6.4 | Stale upstream data              | Candles from 7+ days ago only                   | Service warns about staleness, continues                         |        |
| 6.5 | Invalid feature group + category | `--feature-group options_iv --asset-group DEFI` | `validate_args()` raises ValueError, clean exit                  |        |
| 6.6 | Deprecated mode: incremental     | `--mode incremental`                            | Normalised to `live` with deprecation warning                    |        |
| 6.7 | Skip dependency check            | `--skip-dependency-check`                       | Warning logged, processing continues without upstream validation |        |
| 6.8 | AWS cloud provider               | `CLOUD_PROVIDER=aws CLOUD_MOCK_MODE=true`       | Uses S3 sink (mocked), same output format                        |        |
| 6.9 | Run tag override                 | `--run-tag t1-recon`                            | GCS output prefix uses `t1-recon/` instead of `batch/`           |        |

### Phase 7: Observability

| #    | Check                   | Expected                                                          | Status |
| ---- | ----------------------- | ----------------------------------------------------------------- | ------ |
| 7.1  | ServiceRuntime log line | All dimensions logged at startup                                  |        |
| 7.2  | UEI events              | STARTED, VALIDATION_STARTED, VALIDATION_COMPLETED, STOPPED/FAILED |        |
| 7.3  | Shard-level isolation   | One instrument failure doesn't crash others                       |        |
| 7.4  | Dry-run warning         | "DRY RUN" + "UCI dry-run mode ACTIVE" logged                      |        |
| 7.5  | Error classification    | ADAPTER_FETCH_FAILED events for failed instruments                |        |
| 7.6  | Memory watchdog         | "Memory watchdog started" logged at startup                       |        |
| 7.7  | Processing progress     | Per-instrument/per-group progress logged                          |        |
| 7.8  | GracefulShutdownHandler | Registered at startup, handles SIGTERM/SIGINT                     |        |
| 7.9  | Correlation ID          | UUID correlation_id in all UEI events                             |        |
| 7.10 | GCSEventSink            | Events written to GCS event sink bucket                           |        |

## Issues Found

(log in `plans/archive/issues/service_control_surface_issues_2026_03_21.md`)

| Issue | Severity | Fixed? |
| ----- | -------- | ------ |

## Next Service

After features-volatility-service passes all phases -> proceed to `006_features_calendar_service.md`
