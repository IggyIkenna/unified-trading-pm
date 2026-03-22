---
title: "E2E Test: strategy-service"
service: strategy-service
date: 2026-03-22
status: pending
---

# E2E Test: strategy-service

Follows `procedure.md`. Pipeline position: #14 (L5 strategy/execution layer).

## Upstream Dependencies

| Source                           | Data                  | Transport  |
| -------------------------------- | --------------------- | ---------- |
| ml-inference-service             | predictions           | GCS        |
| market-data-processing-service   | processed_market_data | GCS        |
| features (live)                  | live features         | PubSub     |
| position-balance-monitor-service | position_state        | GCS/PubSub |

## Downstream Consumers

| Consumer          | Data                 | Transport  |
| ----------------- | -------------------- | ---------- |
| execution-service | trade_signals_orders | GCS/PubSub |

## Also Receives

| Source           | Data                     | Transport |
| ---------------- | ------------------------ | --------- |
| alerting-service | circuit_breaker_commands | PubSub    |

## Operations

strategy-service does not use `--operation`. The CLI is `--mode batch` only. Strategies are configured per-strategy via
config files and `--strategies` argument, not per-category. The EventDrivenStrategyEngine is parameterised by
subscription config: 50+ strategies via config expansion (13 archetypes x 5 asset classes).

| Mode    | What it does                                                          | Expected output                    |
| ------- | --------------------------------------------------------------------- | ---------------------------------- |
| `batch` | Backtest: replay historical data through strategy engine              | Parquet with signals, PnL, metrics |
| (live)  | Not yet implemented. Will consume features + predictions in real time | Trade signals emitted via PubSub   |

## CLI Arguments

```
--mode batch                          # REQUIRED (only choice currently)
--category CEFI|TRADFI|DEFI|ALL       # default: ALL (resolves default instruments/strategies)
--instruments BTC ETH SOL SPY         # shortcuts or full canonical IDs
--strategies MOM_MACD AAVE_LENDING    # strategy types
--timeframes 5m 15m 1h               # default: 5m
--start-date YYYY-MM-DD              # REQUIRED
--end-date YYYY-MM-DD                # REQUIRED
--environment local-dev|staging|production  # default: production
--output-mode fast|report             # default: report (full parquet)
--config-gcs gs://...                 # GCS path to strategy config JSON
--load-execution-results              # load actual fills for enhanced PnL
--dry-run                             # no GCS writes
--force                               # re-run even if results exist
--max-workers N                       # default: 4
--max-results N                       # max output files per shard
--skip-dependency-check               # skip upstream dependency validation
--no-fail-on-missing-deps             # warn only on missing upstream data
--run-tag batch|t1-recon              # GCS output prefix tag
--project-id                          # GCP project (default: from config)
--verbose                             # detailed progress bars
--log-level DEBUG|INFO|WARNING|ERROR  # default: INFO
```

## Service-Specific Notes

- **No `--operation` flag** -- strategy-service uses `--mode` only (`batch`). It does not use ServiceCLI dispatch.
- **No `--category` as a routing axis** -- `--category` exists but only selects default instruments/strategies. It does
  not route to different handler classes or pipelines. CEFI/TRADFI resolve to MOM_MACD, DEFI resolves to
  AAVE_LENDING/BASIS_TRADE/STAKED_BASIS/RECURSIVE_STAKED_BASIS.
- **Mock mode redirect** -- when `CLOUD_MOCK_MODE=true`, the service immediately redirects to `run_mock_pipeline()` and
  returns `{"status": "ok", "mock_mode": True}`. The normal CLI path is skipped entirely.
- **50+ strategies** -- 13 archetypes x 5 asset classes. Config expansion happens at runtime. The demo must show all 50+
  accessible via the API with PnL time-series for equity curves.
- **Circuit breaker** -- must be honored. Alerting-service sends `circuit_breaker_commands` via PubSub. Strategy engine
  must halt signal generation when circuit breaker is active.
- **Startup validation** -- validates GCS bucket access (`strategy-store-{project_id}`) before proceeding. Skipped in
  `--dry-run` mode.
- **Pre-crash checkpoint** -- `register_pre_crash_handlers("strategy-service")` saves state on SIGTERM/SIGKILL.

## Frontend API Surface

| Endpoint                                  | Method | What it feeds                             |
| ----------------------------------------- | ------ | ----------------------------------------- |
| `GET /analytics/strategies`               | GET    | Strategy list with summary metrics        |
| `GET /analytics/strategy-configs`         | GET    | Strategy config definitions (50+)         |
| `GET /analytics/strategies/{id}`          | GET    | Strategy detail: equity curve, PnL series |
| `POST /analytics/strategies/{id}/promote` | POST   | Promote strategy to live                  |
| `POST /analytics/strategies/{id}/scale`   | POST   | Scale strategy allocation                 |
| `POST /risk/circuit-breaker`              | POST   | Trigger/release circuit breaker           |

**CRITICAL FOR DEMO**: 50+ strategies must be accessible via API, with PnL time-series for equity curves.

## Test Matrix

### Phase 1: Startup Validation

| #   | Env vars                                                                        | Expected                  | Status |
| --- | ------------------------------------------------------------------------------- | ------------------------- | ------ |
| 1.1 | `CLOUD_PROVIDER=gcp ENVIRONMENT=dev CLOUD_MOCK_MODE=false TESTNET_MODE=mainnet` | OK                        |        |
| 1.2 | `CLOUD_PROVIDER=local ENVIRONMENT=dev CLOUD_MOCK_MODE=true`                     | OK (mock redirect)        |        |
| 1.3 | `CLOUD_PROVIDER=gcp ENVIRONMENT=staging TESTNET_MODE=testnet`                   | OK                        |        |
| 1.4 | `CLOUD_PROVIDER=azure`                                                          | STARTUP_VALIDATION_FAILED |        |
| 1.5 | `TESTNET_MODE=sandbox`                                                          | STARTUP_VALIDATION_FAILED |        |
| 1.6 | `CLOUD_MOCK_MODE=maybe`                                                         | Pydantic validation error |        |
| 1.7 | `LOG_LEVEL=TRACE`                                                               | Invalid LOG_LEVEL exit    |        |

### Phase 2: Dry-Run (batch, real data, no writes)

| #   | Category | Strategies                                             | Expected                                    | Status |
| --- | -------- | ------------------------------------------------------ | ------------------------------------------- | ------ |
| 2.1 | CEFI     | MOM_MACD (BTC, ETH, SOL)                               | Fetch features + predictions, no GCS writes |        |
| 2.2 | TRADFI   | MOM_MACD (SPY)                                         | Fetch features + predictions, no GCS writes |        |
| 2.3 | DEFI     | AAVE*LENDING, BASIS_TRADE, STAKED_BASIS, RECURSIVE*... | Fetch onchain features, no GCS writes       |        |
| 2.4 | ALL      | All defaults (5 strategies, 4 instruments)             | Full sweep, no GCS writes                   |        |
| 2.5 | CEFI     | MOM_MACD + `--skip-dependency-check`                   | Skips upstream validation, runs anyway      |        |
| 2.6 | CEFI     | MOM_MACD + `--no-fail-on-missing-deps`                 | Warns on missing upstream, continues        |        |

### Phase 3: Real Writes (dev, CSV sampling on)

| #   | Category | Strategies                      | GCS check                            | Status |
| --- | -------- | ------------------------------- | ------------------------------------ | ------ |
| 3.1 | CEFI     | MOM_MACD                        | Verify parquet in `strategy-store-*` |        |
| 3.2 | TRADFI   | MOM_MACD                        | Verify parquet in `strategy-store-*` |        |
| 3.3 | DEFI     | AAVE_LENDING                    | Verify parquet in `strategy-store-*` |        |
| 3.4 | ALL      | All defaults                    | Verify all output files              |        |
| 3.5 | CEFI     | MOM_MACD + `--output-mode fast` | Verify JSON summary output           |        |

### Phase 4: Category Sweep

**Note**: `--category` in strategy-service selects default instruments and strategies, not routing pipelines. All
categories still go through the same strategy engine. The purpose here is to verify each category resolves to the
correct instruments and strategies.

| #   | Category   | Expected instruments         | Expected strategies                                       | Status |
| --- | ---------- | ---------------------------- | --------------------------------------------------------- | ------ |
| 4.1 | CEFI       | BTC, ETH, SOL                | MOM_MACD                                                  |        |
| 4.2 | TRADFI     | SPY                          | MOM_MACD                                                  |        |
| 4.3 | DEFI       | (empty -- strategy-specific) | AAVE_LENDING, BASIS_TRADE, STAKED_BASIS, RECURSIVE_STAKED |        |
| 4.4 | ALL        | BTC, ETH, SOL, SPY           | MOM_MACD, AAVE_LENDING, BASIS_TRADE, STAKED/RECURSIVE     |        |
| 4.5 | SPORTS     | (not in choices)             | Should reject or handle gracefully                        |        |
| 4.6 | PREDICTION | (not in choices)             | Should reject or handle gracefully                        |        |

### Phase 5: Live Mode

strategy-service currently only supports `--mode batch`. Live mode is not yet implemented.

| #   | What                    | Expected                                               | Status |
| --- | ----------------------- | ------------------------------------------------------ | ------ |
| 5.1 | `--mode live`           | Rejected by argparse (`choices=["batch"]`)             |        |
| 5.2 | Future: PubSub consume  | (not yet) Features + predictions consumed in real time | N/A    |
| 5.3 | Future: signal emission | (not yet) Trade signals published to execution-service | N/A    |

### Phase 5b: Mock/Real A/B

Compare mock pipeline output vs real pipeline output to verify mock data fidelity:

| #    | What                                | Expected                                            | Status |
| ---- | ----------------------------------- | --------------------------------------------------- | ------ |
| 5b.1 | Mock mode (`CLOUD_MOCK_MODE=true`)  | Redirects to `run_mock_pipeline()`, returns ok      |        |
| 5b.2 | Real mode (`CLOUD_MOCK_MODE=false`) | Full CLI path, real GCS reads/writes                |        |
| 5b.3 | Schema parity                       | Mock output schema matches real output schema       |        |
| 5b.4 | Mock strategy count                 | Mock produces signals for all 50+ strategy configs  |        |
| 5b.5 | Mock PnL time-series                | Mock output includes equity curve data per strategy |        |

### Phase 6: Mock Mode (scenario testing)

| #   | Scenario                         | What it tests                             | Expected                                 | Status |
| --- | -------------------------------- | ----------------------------------------- | ---------------------------------------- | ------ |
| 6.1 | `CLOUD_MOCK_MODE=true`           | Mock pipeline redirect                    | Immediate return, no cloud calls         |        |
| 6.2 | Mock with `--verbose`            | Mock still respects verbose flag          | Additional logging in mock path          |        |
| 6.3 | Mock output schema               | Mock data matches expected parquet schema | Downstream execution-service can consume |        |
| 6.4 | Missing upstream features (real) | No features in GCS for date range         | Clear error or empty signals, no crash   |        |
| 6.5 | Missing ML predictions (real)    | No predictions available                  | Strategy runs without ML overlay, warns  |        |
| 6.6 | Circuit breaker active           | `circuit_breaker_commands` received       | Signal generation halted                 |        |
| 6.7 | `--load-execution-results`       | Load actual fills from execution-service  | Enhanced PnL with slippage               |        |

### Phase 7: Observability

| #   | Check                         | Expected                                                       | Status |
| --- | ----------------------------- | -------------------------------------------------------------- | ------ |
| 7.1 | ServiceRuntime log line       | Transport and storage protocol logged at startup               |        |
| 7.2 | UEI events                    | STARTED, VALIDATION*\*, MODE_INITIALIZED, PROCESSING*\*        |        |
| 7.3 | Lifecycle events              | DATA_INGESTION, PREDICTION_LOADING, STRATEGY_EXECUTION         |        |
| 7.4 | Correlation ID                | All events include `correlation_id`                            |        |
| 7.5 | GracefulShutdownHandler       | Ctrl-C during backtest -> clean exit, STOPPED event            |        |
| 7.6 | Pre-crash checkpoint          | SIGTERM saves state via `register_pre_crash_handlers`          |        |
| 7.7 | Memory watchdog               | `setup_service_observability` with `memory_threshold_pct=85.0` |        |
| 7.8 | Dry-run enforcement           | `--dry-run` skips startup validation and GCS writes            |        |
| 7.9 | `load_dotenv(override=False)` | Shell env vars win over .env file                              |        |

## Known Issues Audit

Check these patterns from prior services:

| Pattern                           | What to check                                         | Status |
| --------------------------------- | ----------------------------------------------------- | ------ |
| `load_dotenv(override=True)`      | Must be `override=False` -- confirmed in main.py      |        |
| Hardcoded bucket names            | `strategy-store-{project_id}` -- derived, not env var |        |
| asyncio nesting                   | Handler uses sync path (no asyncio.run inside)        |        |
| Category routing fallthrough      | DEFI returns empty instruments (intended)             |        |
| SPORTS/PREDICTION in `--category` | Not in CATEGORIES choices -- verify argparse rejects  |        |
| `--dry-run` enforcement           | Skips `_validate_startup`, check no GCS writes happen |        |
| Mock mode bypass                  | `is_mock_mode()` skips entire CLI path                |        |

## AWS Testing

strategy-service does not directly interact with AWS services. All cloud interaction goes through UCI abstractions. AWS
testing is not applicable unless `CLOUD_PROVIDER=aws` is configured.

| #   | What                 | Expected                            | Status |
| --- | -------------------- | ----------------------------------- | ------ |
| A.1 | `CLOUD_PROVIDER=aws` | UCI routes to S3 backend            |        |
| A.2 | S3 bucket resolution | `strategy-store-{project_id}` on S3 |        |

## Issues Found

(logged in `plans/active/issues/service_control_surface_issues_2026_03_21.md`)

| Issue | Severity | Fixed? |
| ----- | -------- | ------ |
|       |          |        |

## Next Service

After strategy-service passes all phases -> proceed to `015_execution_service.md`
