---
title: "E2E Test: position-balance-monitor-service"
service: position-balance-monitor-service
date: 2026-03-22
status: pending
---

# E2E Test: position-balance-monitor-service

Follows `procedure.md`. Pipeline position: #13 — L6 monitoring layer.

## Service Overview

**Authoritative position source.** Reconciles exchange-reported positions vs filled orders. At startup (live mode), runs
a blocking `StartupReconciler` pass that queries exchange REST APIs for current positions and balances, then publishes
initial position state so strategy-service knows current holdings. Live mode consumes fill events via PubSub, runs a
periodic reconciliation loop, and serves an API (uvicorn) for position queries. Batch mode runs a one-time
reconciliation pass and exits.

**Upstream:** execution-service (order_lifecycle_events via GCS/PubSub fill events)

**Downstream:** strategy-service (position_state), risk-and-exposure-service (position_snapshots), alerting-service
(balance_discrepancy_alerts), client-reporting-api (position_balance_reports)

## Operations

| Operation | What it does                                                        | Expected output                              |
| --------- | ------------------------------------------------------------------- | -------------------------------------------- |
| `monitor` | Reconcile expected positions (from fills) vs actual (from exchange) | Reconciliation snapshots, discrepancy alerts |

Single operation, two modes:

| Mode    | Behaviour                                                                                                 |
| ------- | --------------------------------------------------------------------------------------------------------- |
| `batch` | One-time reconciliation of all active positions, then exit                                                |
| `live`  | Startup recon, fill event consumer (PubSub), periodic recon loop, API server (uvicorn), runs indefinitely |

## CLI Flags

| Flag                   | Type   | Default | Notes                                           |
| ---------------------- | ------ | ------- | ----------------------------------------------- |
| `--operation`          | choice | (req)   | Only `monitor`                                  |
| `--mode`               | choice | (req)   | `batch` or `live`                               |
| `--start-date`         | str    | None    | Batch mode date range                           |
| `--end-date`           | str    | None    | Batch mode date range                           |
| `--interval`           | int    | 5       | Reconciliation interval in minutes (live mode)  |
| `--dry-run`            | flag   | false   | No writes                                       |
| `--skip-startup-recon` | flag   | false   | Skip startup reconciliation (dev/exchange-down) |

## Uniqueness Notes

- **No `--asset-group` flag** -- monitors all positions across all venues. Not category-partitioned.
- **Startup reconciliation** (Stream A): live mode runs `StartupReconciler` before accepting new data. Queries exchange
  REST for current positions + balances. If critical discrepancies found, logs warning but starts in degraded state
  (does not block). Skip with `--skip-startup-recon`.
- **Exchange bootstrap**: `_bootstrap_exchange_state()` seeds initial position and balance state from exchange REST so
  the in-memory tracker starts from exchange truth, not empty state. Errors are swallowed (non-fatal).
- **Mock mode**: `PositionBalanceMonitorServiceConfig.is_mock_mode()` redirects to `run_mock_pipeline()` early, before
  CLI arg parsing.
- **Event sink selection**: PubSub for live mode (topology = pubsub), GCS for batch mode.
- **API server**: live mode starts uvicorn on `config.api_host:config.api_port`.

## Test Matrix

### Phase 1: Startup Validation

| #   | Env vars                                                                        | Expected                  | Status |
| --- | ------------------------------------------------------------------------------- | ------------------------- | ------ |
| 1.1 | `CLOUD_PROVIDER=gcp ENVIRONMENT=dev CLOUD_MOCK_MODE=false TESTNET_MODE=mainnet` | OK                        |        |
| 1.2 | `CLOUD_PROVIDER=local ENVIRONMENT=dev CLOUD_MOCK_MODE=true`                     | OK (mock mode redirect)   |        |
| 1.3 | `CLOUD_PROVIDER=gcp ENVIRONMENT=staging TESTNET_MODE=testnet`                   | OK                        |        |
| 1.4 | `CLOUD_PROVIDER=azure`                                                          | STARTUP_VALIDATION_FAILED |        |
| 1.5 | `TESTNET_MODE=sandbox`                                                          | STARTUP_VALIDATION_FAILED |        |
| 1.6 | `CLOUD_MOCK_MODE=maybe`                                                         | Pydantic validation error |        |

### Phase 2: Dry-Run (no writes)

| #   | Operation | Mode  | Flags                            | Expected                                                        | Status |
| --- | --------- | ----- | -------------------------------- | --------------------------------------------------------------- | ------ |
| 2.1 | monitor   | batch | `--dry-run`                      | Initializes components, no DB/GCS writes                        |        |
| 2.2 | monitor   | live  | `--dry-run --skip-startup-recon` | Starts consumer + API, no writes, no recon                      |        |
| 2.3 | monitor   | live  | `--dry-run`                      | Startup recon attempted (may fail without exchange), API starts |        |

### Phase 3: Real Writes (dev environment)

| #   | Operation | Mode  | Check                                                                | Status |
| --- | --------- | ----- | -------------------------------------------------------------------- | ------ |
| 3.1 | monitor   | batch | Reconciliation snapshots written to store                            |        |
| 3.2 | monitor   | batch | Reconciliation summary logged (total/matched/discrepancies/critical) |        |
| 3.3 | monitor   | live  | Fill event consumer starts, API responds on configured port          |        |
| 3.4 | monitor   | live  | Reconciliation loop runs at configured interval                      |        |

### Phase 4: Category Sweep

**Not applicable.** This service has no `--asset-group` flag. It monitors all positions across all venues regardless of
category. The relevant sweep is venue-level:

| #   | Venue scope        | Expected                                                     | Status |
| --- | ------------------ | ------------------------------------------------------------ | ------ |
| 4.1 | CeFi venues        | Positions from Binance/OKX/etc reconciled                    |        |
| 4.2 | TradFi venues      | Positions from IBKR reconciled                               |        |
| 4.3 | DeFi venues        | DeFi wallet positions reconciled (if exchange adapter wired) |        |
| 4.4 | No positions found | Empty reconciliation, clean exit (batch) or idle (live)      |        |
| 4.5 | Mixed venues       | Cross-venue reconciliation produces combined snapshot        |        |

### Phase 5: Live Mode

This is a primary live-mode service. Live mode is the core use case.

| #    | What                              | Expected                                                                | Status |
| ---- | --------------------------------- | ----------------------------------------------------------------------- | ------ |
| 5.1  | `--operation monitor --mode live` | Startup recon runs, fill consumer starts, API starts, recon loop starts |        |
| 5.2  | Startup reconciliation            | Queries exchange REST, populates tracker with current state             |        |
| 5.3  | `--skip-startup-recon`            | Skips recon, logs "skipped via flag"                                    |        |
| 5.4  | Fill event consumption            | PubSub fill events update position tracker                              |        |
| 5.5  | Reconciliation loop               | Runs every N minutes (default 5), compares expected vs actual           |        |
| 5.6  | Discrepancy detection             | Mismatches logged as warnings, events emitted                           |        |
| 5.7  | API server                        | uvicorn serves position queries on configured host:port                 |        |
| 5.8  | Graceful shutdown (Ctrl-C)        | Fill consumer stopped, recon task cancelled, API server stopped, exit 0 |        |
| 5.9  | Exchange bootstrap failure        | Non-fatal: logged as warning, service continues                         |        |
| 5.10 | Critical discrepancies at startup | Service starts in degraded state, logs warning with count               |        |

#### Phase 5b: Mock vs Real A/B

| #    | Axis           | Mock (`CLOUD_MOCK_MODE=true`)                   | Real (`CLOUD_MOCK_MODE=false`)                           | Status |
| ---- | -------------- | ----------------------------------------------- | -------------------------------------------------------- | ------ |
| 5b.1 | Data source    | `run_mock_pipeline()` — pre-generated seed data | Exchange REST APIs + PubSub fill events                  |        |
| 5b.2 | Event sink     | Local sink (no PubSub/GCS credentials needed)   | PubSub (live) or GCS (batch) based on topology           |        |
| 5b.3 | Exchange calls | Mock pipeline bypasses exchange entirely        | AccountQueryClient queries real exchange REST            |        |
| 5b.4 | API server     | Mock pipeline may not start API                 | uvicorn serves on configured port                        |        |
| 5b.5 | Reconciliation | Mock pipeline handles internally                | ReconciliationEngine compares fills vs exchange balances |        |

### Phase 6: Mock Mode (scenario testing)

| #   | Scenario                      | What it tests                                | Expected                                         | Status |
| --- | ----------------------------- | -------------------------------------------- | ------------------------------------------------ | ------ |
| 6.1 | `CLOUD_MOCK_MODE=true`        | Mock pipeline redirect                       | `run_mock_pipeline()` called, no exchange access |        |
| 6.2 | Mock + batch                  | Mock mode triggers before CLI parsing        | Clean exit with mock data                        |        |
| 6.3 | Mock + live                   | Mock mode triggers before CLI parsing        | Clean exit with mock data                        |        |
| 6.4 | Exchange API unavailable      | `--skip-startup-recon` in live mode          | Bootstrap skipped, fill events populate state    |        |
| 6.5 | Bootstrap failure (non-fatal) | Exchange REST returns error during bootstrap | Warning logged, service continues                |        |
| 6.6 | Reconciliation loop error     | Exception during periodic reconciliation     | Logged, retries after 60s, does not crash        |        |
| 6.7 | No active positions           | Empty position store                         | Reconciliation completes with 0 snapshots        |        |

### Phase 7: Observability

| #   | Check                    | Expected                                                                            | Status |
| --- | ------------------------ | ----------------------------------------------------------------------------------- | ------ |
| 7.1 | ServiceRuntime log line  | `operation=monitor, mode=batch/live` logged at startup                              |        |
| 7.2 | UEI lifecycle events     | STARTED, SERVICE_STARTED at boot; STOPPED/SERVICE_STOPPED at exit                   |        |
| 7.3 | Correlation ID           | UUID generated and attached to all lifecycle events                                 |        |
| 7.4 | Shard-level isolation    | Exchange bootstrap failure does not crash service                                   |        |
| 7.5 | Memory watchdog          | `memory_threshold_pct=85.0` configured in observability setup                       |        |
| 7.6 | Tracing enabled          | `enable_tracing=True` in observability setup                                        |        |
| 7.7 | Reconciliation events    | EXCHANGE*BOOTSTRAP_COMPLETED/FAILED, VALIDATION*\_, PROCESSING\_\_, PERSISTENCE\_\* |        |
| 7.8 | Graceful shutdown events | STOPPED + SERVICE_STOPPED emitted on KeyboardInterrupt                              |        |
| 7.9 | Error events             | FAILED + SERVICE_ERROR with error details on fatal exception                        |        |

## Known Issues Audit

Check for these patterns found in earlier services:

| Pattern                      | Check                                                                             | Status |
| ---------------------------- | --------------------------------------------------------------------------------- | ------ |
| `load_dotenv(override=True)` | Must be `override=False` — shell intent wins                                      |        |
| `--dry-run` enforcement      | Batch mode respects dry-run (no DB/store writes)                                  |        |
| `os.getenv()` usage          | Only allowed in config-bootstrap context                                          |        |
| asyncio nesting              | `main()` calls `asyncio.run()` twice (startup recon + handler) -- potential issue |        |
| Mock mode bypass             | Mock check happens before `parse_args()` -- args are ignored in mock mode         |        |
| PubSub topic hardcoded       | `"position-balance-monitor-service-events"` -- should come from config?           |        |
| Global mutable state         | `_fill_consumer` and `_reconciliation_task` are module globals                    |        |

### asyncio Double-Run Warning

`main()` calls `asyncio.run(_reconciler.run())` for startup reconciliation, then `asyncio.run(handler.run_live(args))`
for the main handler. Two sequential `asyncio.run()` calls in the same process. This works because each creates/destroys
its own event loop, but verify no shared state (e.g. open connections) leaks between them.

## AWS Testing

| #   | Test                                    | Expected                             | Status |
| --- | --------------------------------------- | ------------------------------------ | ------ |
| A.1 | `CLOUD_PROVIDER=aws` startup validation | OK if AWS credentials configured     |        |
| A.2 | Event sink selection with AWS topology  | S3-based event sink (not PubSub/GCS) |        |
| A.3 | AWS without credentials                 | Clear error, not silent fallback     |        |

## Frontend API Integration

The position-balance-monitor-service API (uvicorn, live mode) feeds frontend endpoints:

| Endpoint                           | What it serves                             | Check                                         |
| ---------------------------------- | ------------------------------------------ | --------------------------------------------- |
| `GET /positions/active`            | Current active positions across all venues | Returns position list with venue, symbol, qty |
| `GET /positions/active?mode=live`  | Live-updated positions (from fill events)  | Reflects recent fills within seconds          |
| `GET /positions/active?mode=batch` | Last batch reconciliation snapshot         | Returns snapshot from most recent batch run   |
| Position balance display           | Per-venue breakdown of expected vs actual  | Discrepancy amounts shown when mismatched     |
| Discrepancy alerts                 | Balance mismatches exceeding threshold     | Alert events emitted to alerting-service      |
| WebSocket position updates         | Real-time position changes                 | If supported: verify WS pushes on fill events |

## Issues Found

(logged in `plans/archive/issues/service_control_surface_issues_2026_03_21.md`)

| Issue      | Severity | Fixed? |
| ---------- | -------- | ------ |
| (none yet) |          |        |

## Next Service

After position-balance-monitor-service passes all phases, proceed to `019_risk_management_service.md`
