---
title: "E2E Test: execution-service"
service: execution-service
date: 2026-03-22
status: pending
---

# E2E Test: execution-service

Follows `procedure.md`. Pipeline position: #15 (L5 strategy/execution layer).

## Upstream Dependencies

| Source                   | Data                     | Transport  |
| ------------------------ | ------------------------ | ---------- |
| strategy-service         | trade_signals_orders     | GCS/PubSub |
| market-tick-data-service | live_market_feed         | PubSub/WS  |
| alerting-service         | circuit_breaker_commands | PubSub     |
| instruments-service      | instruments_universe     | GCS        |

## Downstream Consumers

| Consumer                         | Data                   | Transport  |
| -------------------------------- | ---------------------- | ---------- |
| position-balance-monitor-service | order_lifecycle_events | PubSub/GCS |
| pnl-attribution-service          | execution results      | GCS        |
| unified-trading-api              | order/fill data        | GCS/API    |
| alerting-service                 | order_rejection_spikes | PubSub     |

## Operations

| Operation        | Mode  | What it does                                                    | Expected output                          |
| ---------------- | ----- | --------------------------------------------------------------- | ---------------------------------------- |
| `backtest`       | batch | Replay historical signals through matching-engine-library       | Simulated fills, PnL, TCA metrics        |
| `live_execution` | live  | Execute real orders via UTEI (CeFi), UDEI (DeFi), USEI (Sports) | Order lifecycle events, fills, positions |

## CLI Arguments

execution-service uses ServiceCLI with `add_category_arg=False` (documented exception). It also supports legacy
subcommands (`backtest`, `batch-backtest`, `benchmark-compare`).

### ServiceCLI mode

```
--operation backtest|live_execution    # REQUIRED
--mode batch|live                      # REQUIRED
--start-date YYYY-MM-DD               # batch mode
--end-date YYYY-MM-DD                 # batch mode
--dry-run                              # no real orders/writes
--force                                # re-run even if results exist
--log-level DEBUG|INFO|WARNING|ERROR   # default: INFO
--interval N                           # minutes (live mode, default: 15)
--config PATH                          # config path for single backtest
--configs PATH [PATH ...]             # config paths for batch backtest
--parallel N                           # parallel workers (default: 4)
--data-source gcs|local                # data source (default: gcs)
--output-dir PATH                      # output directory for results
--skip-recovery                        # skip OrderRecoveryEngine on live startup
```

### Legacy subcommands (also supported)

```
python -m execution_service backtest --config ... --start ... --end ...
python -m execution_service batch-backtest --configs ... --start ... --end ...
python -m execution_service benchmark-compare --config ... --start ... --end ...
```

## Service-Specific Notes

- **CRITICAL SERVICE -- handles real money.** Testnet mode MANDATORY for live testing. Never use mainnet in E2E testing.
  Always `TESTNET_MODE=testnet` for `live_execution`.
- **No `--asset-group`** -- routing is based on instruction content. CeFi orders route to UTEI adapters, DeFi operations
  (SWAP, LEND, BORROW, STAKE, UNSTAKE) route to UDEI connectors, Sports operations (BET, CANCEL_BET) route to USEI
  adapters.
- **Backtest uses matching-engine-library** -- no exchange connection needed. Simulates fills internally.
- **Live uses UTEI/UDEI/USEI** -- real adapter connections to exchanges/protocols/sportsbooks. Credentials fetched from
  Secret Manager at runtime.
- **Order recovery on live startup** -- `OrderRecoveryEngine` runs after circuit-breaker init, before STARTED event.
  Checks for orphaned orders on venues (default: binance, deribit, hyperliquid). Skippable via `--skip-recovery`.
- **Circuit breaker + kill switch** -- must be honored. Alerting-service sends `circuit_breaker_commands`. Live
  execution must halt immediately when triggered.
- **DeFi error classification** -- 13 structured error codes in UDEI `DefiErrorCode`. Execution-service routes on code
  prefix: FAIL (abort), RETRY (exponential backoff), SKIP (continue to next instruction).
- **Mock mode redirect** -- when `CLOUD_MOCK_MODE=true`, redirects to `run_mock_pipeline()` and exits.
- **Event sink routing** -- mock mode uses `LocalFsEventSink`, PubSub messaging uses `PubSubEventSink`, otherwise
  `GCSEventSink`.

## Frontend API Surface

| Endpoint                            | Method | What it feeds                              |
| ----------------------------------- | ------ | ------------------------------------------ |
| `GET /execution/orders`             | GET    | Order list with status, fills, timestamps  |
| `POST /execution/orders`            | POST   | Manual trading -- submit order directly    |
| `GET /positions/active`             | GET    | Active positions with unrealised PnL       |
| `WebSocket /execution/live`         | WS     | Live order updates (fill, partial, reject) |
| `GET /execution/analytics/tca`      | GET    | Transaction cost analysis                  |
| `GET /execution/analytics/algo`     | GET    | Algo performance metrics                   |
| `GET /execution/analytics/slippage` | GET    | Slippage analysis per venue/instrument     |

## SECURITY REQUIREMENTS

**NEVER use mainnet in testing. Always `TESTNET_MODE=testnet` for live execution testing.**

- All live execution E2E tests MUST set `TESTNET_MODE=testnet`
- Verify TESTNET_MODE is logged in startup output before proceeding
- DeFi tests use Tenderly fork or Sepolia testnet -- never mainnet
- CeFi tests use Binance testnet / OKX testnet -- never production API keys
- Sports tests use sandbox/test endpoints

## Test Matrix

### Phase 1: Startup Validation

| #   | Env vars                                                                        | Expected                  | Status |
| --- | ------------------------------------------------------------------------------- | ------------------------- | ------ |
| 1.1 | `CLOUD_PROVIDER=gcp ENVIRONMENT=dev CLOUD_MOCK_MODE=false TESTNET_MODE=testnet` | OK                        |        |
| 1.2 | `CLOUD_PROVIDER=local ENVIRONMENT=dev CLOUD_MOCK_MODE=true`                     | OK (mock redirect)        |        |
| 1.3 | `CLOUD_PROVIDER=gcp ENVIRONMENT=staging TESTNET_MODE=testnet`                   | OK                        |        |
| 1.4 | `CLOUD_PROVIDER=azure`                                                          | STARTUP_VALIDATION_FAILED |        |
| 1.5 | `TESTNET_MODE=sandbox`                                                          | STARTUP_VALIDATION_FAILED |        |
| 1.6 | `CLOUD_MOCK_MODE=maybe`                                                         | Pydantic validation error |        |
| 1.7 | `LOG_LEVEL=TRACE`                                                               | Invalid LOG_LEVEL exit    |        |
| 1.8 | `TESTNET_MODE=mainnet` + `--operation live_execution`                           | **MUST WARN** or block    |        |

### Phase 2: Dry-Run (backtest, no writes)

| #   | Operation      | Mode  | Expected                                           | Status |
| --- | -------------- | ----- | -------------------------------------------------- | ------ |
| 2.1 | backtest       | batch | Load signals from strategy-service, simulate fills |        |
| 2.2 | backtest       | batch | `--dry-run` -- no GCS writes                       |        |
| 2.3 | backtest       | batch | `--config` single config file                      |        |
| 2.4 | backtest       | batch | `--configs` multiple config files, `--parallel 2`  |        |
| 2.5 | live_execution | live  | `--dry-run` -- connect but do not submit orders    |        |
| 2.6 | live_execution | live  | `--skip-recovery` -- skip OrderRecoveryEngine      |        |

### Phase 3: Real Writes (dev, testnet only)

| #   | Operation      | Mode  | What                                  | GCS check                  | Status |
| --- | -------------- | ----- | ------------------------------------- | -------------------------- | ------ |
| 3.1 | backtest       | batch | Full backtest with GCS output         | Verify results parquet     |        |
| 3.2 | backtest       | batch | `--data-source local` with local data | Verify local output        |        |
| 3.3 | backtest       | batch | `--output-dir ./results/`             | Verify custom output dir   |        |
| 3.4 | live_execution | live  | Testnet order (TESTNET_MODE=testnet)  | Verify order lifecycle GCS |        |

### Phase 4: Category Sweep (instruction-based routing)

execution-service has no `--asset-group` flag. Routing is based on the instruction content in the trade signals. This
phase tests that each instruction type routes to the correct adapter.

| #   | Instruction type  | Expected adapter | Expected behavior                          | Status |
| --- | ----------------- | ---------------- | ------------------------------------------ | ------ |
| 4.1 | CeFi BUY/SELL     | UTEI             | Order submitted to CeFi exchange (testnet) |        |
| 4.2 | DeFi SWAP         | UDEI (Uniswap)   | Swap via SwapRouter02 (Tenderly/Sepolia)   |        |
| 4.3 | DeFi LEND         | UDEI (Aave)      | Supply to Aave pool (Tenderly/Sepolia)     |        |
| 4.4 | DeFi BORROW       | UDEI (Aave)      | Borrow from Aave pool (Tenderly/Sepolia)   |        |
| 4.5 | DeFi STAKE        | UDEI             | Stake operation (Tenderly/Sepolia)         |        |
| 4.6 | DeFi UNSTAKE      | UDEI             | Unstake operation (Tenderly/Sepolia)       |        |
| 4.7 | Sports BET        | USEI             | Bet placement (sandbox)                    |        |
| 4.8 | Sports CANCEL_BET | USEI             | Bet cancellation (sandbox)                 |        |
| 4.9 | Unknown type      | N/A              | Clear error, no crash, no fallthrough      |        |

### Phase 5: Live Mode (TESTNET ONLY)

**SECURITY: Every test in this phase MUST have `TESTNET_MODE=testnet` set. Verify in logs before proceeding.**

| #   | What                                     | Expected                                                 | Status |
| --- | ---------------------------------------- | -------------------------------------------------------- | ------ |
| 5.1 | `--operation live_execution --mode live` | Connects to testnet venues, awaits signals               |        |
| 5.2 | Order recovery on startup                | `OrderRecoveryEngine` checks binance/deribit/hyperliquid |        |
| 5.3 | `--skip-recovery`                        | Recovery skipped, logged                                 |        |
| 5.4 | Testnet order submission                 | Order placed on testnet, fill received                   |        |
| 5.5 | Circuit breaker trigger                  | Signal received -> execution halted immediately          |        |
| 5.6 | Circuit breaker release                  | Execution resumes after release                          |        |
| 5.7 | Graceful shutdown (Ctrl-C)               | Clean exit, STOPPED event, no orphaned orders            |        |
| 5.8 | DeFi live execution (Tenderly fork)      | Swap/lend on Tenderly fork, tx hash returned             |        |

### Phase 5b: Mock/Real A/B

| #    | What                                    | Expected                                              | Status |
| ---- | --------------------------------------- | ----------------------------------------------------- | ------ |
| 5b.1 | Mock mode (`CLOUD_MOCK_MODE=true`)      | Redirects to `run_mock_pipeline()`, exits cleanly     |        |
| 5b.2 | Real backtest (`CLOUD_MOCK_MODE=false`) | Full matching-engine simulation                       |        |
| 5b.3 | Schema parity                           | Mock output schema matches real backtest output       |        |
| 5b.4 | Event sink routing (mock)               | Uses `LocalFsEventSink` at `.local-dev-cache/events/` |        |
| 5b.5 | Event sink routing (pubsub)             | Uses `PubSubEventSink` when messaging=pubsub          |        |
| 5b.6 | Event sink routing (gcs)                | Uses `GCSEventSink` as fallback                       |        |

### Phase 6: Mock Mode (scenario testing)

| #    | Scenario                               | What it tests                                       | Expected                                     | Status |
| ---- | -------------------------------------- | --------------------------------------------------- | -------------------------------------------- | ------ |
| 6.1  | `CLOUD_MOCK_MODE=true`                 | Mock pipeline redirect                              | Immediate return, no cloud calls             |        |
| 6.2  | Missing strategy signals               | No signals in GCS for date range                    | Empty results, clear log, no crash           |        |
| 6.3  | Malformed trade signal                 | Invalid instruction in signal file                  | Error classified, logged, skipped            |        |
| 6.4  | DeFi tx revert                         | Simulated revert from UDEI                          | Error classified (TX_REVERTED), FAIL routing |        |
| 6.5  | DeFi slippage exceeded                 | Simulated slippage from UDEI                        | SLIPPAGE_EXCEEDED code, RETRY routing        |        |
| 6.6  | DeFi insufficient collateral           | Simulated Aave rejection                            | INSUFFICIENT_COLLATERAL, FAIL routing        |        |
| 6.7  | Venue connection failure               | Exchange unreachable                                | ADAPTER_FETCH_FAILED event, shard isolation  |        |
| 6.8  | Circuit breaker mid-execution          | Breaker triggered while processing batch            | Remaining signals skipped, clean exit        |        |
| 6.9  | Legacy subcommand: `backtest`          | `python -m execution_service backtest --config ...` | Dispatches correctly                         |        |
| 6.10 | Legacy subcommand: `batch-backtest`    | `python -m execution_service batch-backtest ...`    | Dispatches correctly                         |        |
| 6.11 | Legacy subcommand: `benchmark-compare` | `python -m execution_service benchmark-compare ...` | Dispatches correctly                         |        |

### Phase 7: Observability

| #    | Check                         | Expected                                                      | Status |
| ---- | ----------------------------- | ------------------------------------------------------------- | ------ |
| 7.1  | Topology protocols logged     | `messaging=X, storage=Y` at startup                           |        |
| 7.2  | UEI events                    | STARTED, STOPPED/FAILED with correlation_id                   |        |
| 7.3  | Operation/mode in STARTED     | `operation=backtest, mode=batch` in event details             |        |
| 7.4  | Correlation ID propagation    | All events share same UUID                                    |        |
| 7.5  | Order recovery logging        | Recovery engine results logged (or skip logged)               |        |
| 7.6  | Pre-crash checkpoint          | `register_pre_crash_handlers("execution-service")` active     |        |
| 7.7  | DeFi error classification     | Reverts mapped to DefiErrorCode, emitted as structured events |        |
| 7.8  | Shard-level isolation         | One venue failure does not crash other venue processing       |        |
| 7.9  | `load_dotenv(override=False)` | `.env.mock` loaded with `override=False`                      |        |
| 7.10 | Graceful shutdown             | KeyboardInterrupt -> STOPPED event, clean exit                |        |

### Phase 8: Backtest Chain Validation (strategy → execution → PnL)

Verify the execution-service backtest produces output that downstream services can consume, and that backtest simulation
applies realistic DeFi assumptions.

#### 8a: Strategy Instruction Consumption

| #    | What                                                    | Expected                                                                | Status |
| ---- | ------------------------------------------------------- | ----------------------------------------------------------------------- | ------ |
| 8a.1 | Load StrategyInstructions from strategy-service         | Instructions read from `strategy-store-*/backtest/` GCS path            |        |
| 8a.2 | All instruction types routed                            | CeFi BUY/SELL → matching-engine, DeFi SWAP/LEND/BORROW/STAKE → UDEI sim |        |
| 8a.3 | Instruction count consumed = instruction count produced | Zero dropped instructions (or explicit skip with logged reason)         |        |
| 8a.4 | Strategy ID preserved                                   | `strategy_id` from instruction propagated to fill output                |        |

#### 8b: DeFi Backtest Realistic Assumptions

| #    | What                          | Expected                                                                      | Status |
| ---- | ----------------------------- | ----------------------------------------------------------------------------- | ------ |
| 8b.1 | Gas cost modeling             | Each DeFi fill includes `gas_cost_usd` field (not zero)                       |        |
| 8b.2 | Slippage modeling             | Fill price differs from instruction price by slippage model                   |        |
| 8b.3 | Pool depth / liquidity impact | Large orders have proportionally worse fills (AMM curve simulation)           |        |
| 8b.4 | MEV exposure modeling         | Sandwich/frontrun cost estimated for swaps (optional but flagged)             |        |
| 8b.5 | Protocol fee attribution      | Aave/Uniswap protocol fees included in fill cost                              |        |
| 8b.6 | Multi-step DeFi operations    | RECURSIVE_STAKED_BASIS generates N sequential fills (stake→borrow→swap→stake) |        |

#### 8c: Fill Output Schema for Downstream

| #    | What                                             | Expected                                                                                                                 | Status |
| ---- | ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------ | ------ |
| 8c.1 | Fill schema matches PnL-attribution expectation  | `PnlDomainAdapter.read_fills()` can parse execution backtest output                                                      |        |
| 8c.2 | Fill schema matches position-tracker expectation | `FillEventMessage` can be constructed from backtest fill records                                                         |        |
| 8c.3 | Required columns present                         | `fill_id`, `order_id`, `strategy_id`, `instrument`, `side`, `quantity`, `price`, `fee`, `gas_cost`, `timestamp`, `venue` |        |
| 8c.4 | GCS path convention                              | Fills written to `execution_fills/day=YYYY-MM-DD/` (same layout as live fills)                                           |        |
| 8c.5 | Backtest vs live fill schema parity              | Backtest fill schema is a superset of live fill schema (extra: `simulated=true`, `slippage_model`)                       |        |

#### 8d: TCA Metrics from Backtest

| #    | What                              | Expected                                                       | Status |
| ---- | --------------------------------- | -------------------------------------------------------------- | ------ |
| 8d.1 | Implementation shortfall computed | Per-fill: arrival_price - fill_price                           |        |
| 8d.2 | VWAP comparison                   | Execution VWAP vs market VWAP for backtest period              |        |
| 8d.3 | Algo performance summary          | Per-strategy: total slippage, avg execution time, fill rate    |        |
| 8d.4 | DeFi-specific TCA                 | Gas cost as % of trade value, protocol fee breakdown, MEV cost |        |

#### 8e: Grid Backtest Support

| #    | What                                 | Expected                                                                    | Status |
| ---- | ------------------------------------ | --------------------------------------------------------------------------- | ------ |
| 8e.1 | Batch backtest with multiple configs | `--configs config1.json config2.json ...` runs all, writes separate results |        |
| 8e.2 | Parallel execution                   | `--parallel 4` runs 4 backtests concurrently                                |        |
| 8e.3 | Grid result isolation                | Each config's fills written to separate subdirectory                        |        |
| 8e.4 | Aggregate TCA across grid            | Summary TCA comparing execution quality across config variants              |        |

## Known Issues Audit

| Pattern                      | What to check                                                 | Status |
| ---------------------------- | ------------------------------------------------------------- | ------ |
| `load_dotenv(override=True)` | `.env.mock` uses `override=False` -- confirmed in main.py     |        |
| No `--asset-group` flag      | `add_category_arg=False` -- documented exception, verify      |        |
| asyncio nesting              | `asyncio.run(handler.run())` -- handler must not nest asyncio |        |
| Order recovery failure       | Non-fatal (`logger.warning`) -- does not block startup        |        |
| Mainnet guard                | `TESTNET_MODE=mainnet` + `live_execution` must warn/block     |        |
| DeFi credential injection    | UDEI keys from Secret Manager, not env vars                   |        |
| Circuit breaker honoring     | Live execution must halt on breaker command                   |        |
| Event sink selection         | Correct sink chosen based on mock/pubsub/gcs                  |        |
| Subcommand dispatch          | Legacy subcommands still work alongside ServiceCLI            |        |

## AWS Testing

| #   | What                 | Expected                        | Status |
| --- | -------------------- | ------------------------------- | ------ |
| A.1 | `CLOUD_PROVIDER=aws` | UCI routes to S3 backend        |        |
| A.2 | S3 event sink        | Events written to S3 bucket     |        |
| A.3 | AWS Secret Manager   | Credentials fetched from AWS SM |        |

## Issues Found

(logged in `plans/active/issues/service_control_surface_issues_2026_03_21.md`)

| Issue | Severity | Fixed? |
| ----- | -------- | ------ |
|       |          |        |

## Next Service

After execution-service passes all phases -> proceed to `016_pnl_attribution_service.md`
