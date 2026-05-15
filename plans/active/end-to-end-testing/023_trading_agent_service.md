---
title: "E2E Test: trading-agent-service"
service: trading-agent-service
date: 2026-03-22
status: pending
---

# E2E Test: trading-agent-service

Follows `procedure.md`. Pipeline position: **Overlay/Orchestrator** (sits above the full trading pipeline). This service
ties together market data, features, signals, strategy ranking, execution, fill verification, P&L, and autonomous
commentary into a multi-loop agent architecture.

## Architecture Overview

- **Entry point**: `trading_agent_service/__main__.py` -> `asyncio.run(_main())`
- **Orchestrator**: `MicroLoopOrchestrator` runs all loops concurrently via `asyncio.gather(return_exceptions=True)`
- **Loops**: 8 micro-loops per commodity (L1-L7b) + 1 shared L8 commentary loop
- **Config**: `TradingAgentConfig` extends `UnifiedCloudConfig` (Pydantic). Loop cadences, risk gates, service URLs.
- **Mock mode**: `CLOUD_MOCK_MODE=true` -> `run_mock_pipeline()` (loads upstream seed data, runs REAL ranking, writes
  decisions)
- **Kill switch**: Checked in L3 before each trade decision (cloud flag key). Orchestrator does not stop loops -- only
  trade submissions are blocked.

## Loop Architecture

| Loop | Name            | Cadence (default) | What it does                                                    |
| ---- | --------------- | ----------------- | --------------------------------------------------------------- |
| L1   | Data Refresh    | 300s              | Triggers features-service (commodity family) cache refresh      |
| L2   | Signal          | 120s              | Recomputes/subscribes to CommoditySignal updates (SignalCache)  |
| L3   | Trade Decision  | 300s              | Evaluates new trades: risk gate -> strategy ranking -> submit   |
| L5   | Exit Management | 60s               | Checks open positions for exit conditions                       |
| L6   | Fill Verify     | 60s               | Reconciles fills with execution-service                         |
| L7a  | P&L Fast        | 10s               | Fast unrealized P&L snapshot                                    |
| L7b  | P&L Full        | 120s              | Full P&L reconciliation                                         |
| L8   | Commentary      | 300s              | Cross-commodity autonomous commentary (Anthropic API, optional) |

Note: L4 is not present in the codebase (intentional gap in numbering).

## Key Components

- **StrategyRanker** (`ranker.py`): Pure function. Scores strategies against CommoditySignal (regime fit, signal
  threshold, conviction base). Returns ranked list.
- **TradeLedger** (`trade_ledger.py`): Ephemeral in-memory trade lifecycle tracker. SUBMITTED -> FILLED -> CLOSED.
  Rebuilt from execution-service on restart. Uses `Decimal` for financial values.
- **AgentProfile** / **StrategySpec** (`spec.py`): Per-commodity strategy catalog with regime fit, DTE targets,
  profit/stop-loss thresholds.
- **SignalCache** (`l2_signal.py`): Shared signal state between L2 producer and L3 consumer.
- **BaseLoop** (`base_loop.py`): Abstract async loop with drift-corrected scheduling, fault isolation, stop signal.

## Operations

| Operation     | What it does                                          | Mode |
| ------------- | ----------------------------------------------------- | ---- |
| Live agent    | Run all loops for enabled commodities (default)       | Live |
| Mock pipeline | Load upstream seed data, run ranking, write decisions | Mock |

## Test Matrix

### Phase 1: Startup Validation

| #   | Env vars                                                              | Expected                          | Status |
| --- | --------------------------------------------------------------------- | --------------------------------- | ------ |
| 1.1 | `CLOUD_PROVIDER=gcp ENVIRONMENT=dev CLOUD_MOCK_MODE=false`            | Config loads, commodities=[NG,CL] |        |
| 1.2 | `CLOUD_PROVIDER=local ENVIRONMENT=dev CLOUD_MOCK_MODE=true`           | Mock mode detected                |        |
| 1.3 | `CLOUD_PROVIDER=azure`                                                | Validation error                  |        |
| 1.4 | `ENABLED_COMMODITIES='["BTC","ETH"]'`                                 | Custom commodity list parsed      |        |
| 1.5 | `LOG_LEVEL=INVALID`                                                   | SystemExit with valid values      |        |
| 1.6 | `LOG_LEVEL=DEBUG`                                                     | Debug logging enabled             |        |
| 1.7 | `MIN_SIGNAL_STRENGTH=0.5 MIN_REGIME_CONFIDENCE=0.8`                   | Risk gates tightened              |        |
| 1.8 | `MAX_DAILY_LOSS_PCT=1.0 MAX_WEEKLY_LOSS_PCT=3.0 MAX_DRAWDOWN_PCT=5.0` | Loss limits tightened             |        |
| 1.9 | `L8_COMMENTARY_ENABLED=true ANTHROPIC_API_KEY=` (empty)               | L8 enabled but key missing        |        |

### Phase 2: Mock Pipeline (no network, no writes to cloud)

Mock mode runs the REAL strategy ranking engine against synthetic data. Verify the full mock pipeline:

| #    | What                           | Expected                                                                            | Status |
| ---- | ------------------------------ | ----------------------------------------------------------------------------------- | ------ |
| 2.1  | `CLOUD_MOCK_MODE=true` run     | `run_mock_pipeline()` invoked                                                       |        |
| 2.2  | Mock signals generated         | 3 signals: BTC (trending), ETH (volatile), SOL (mean-reverting)                     |        |
| 2.3  | Mock strategy catalog          | 3 strategies: STRADDLE, STRANGLE, CALENDAR_SPREAD                                   |        |
| 2.4  | Risk gate with default metrics | Passes (leverage=3.0, drawdown=0.02)                                                |        |
| 2.5  | Risk gate with high leverage   | Blocked (leverage > 9)                                                              |        |
| 2.6  | Risk gate with high drawdown   | Blocked (drawdown > 0.12)                                                           |        |
| 2.7  | BTC ranking result             | TRADE: BTC_STRADDLE_TRENDING (regime=TRENDING)                                      |        |
| 2.8  | ETH ranking result             | TRADE: BTC_STRANGLE_VOLATILE (regime=VOLATILE)                                      |        |
| 2.9  | SOL ranking result             | TRADE: BTC_CALENDAR_MEAN_REVERTING (regime=MEAN_REVERTING)                          |        |
| 2.10 | Seed output                    | `.local-dev-cache/mock-seed/trading-agent-service/decisions/decisions.json` written |        |
| 2.11 | Seed marker                    | `.seed-complete` marker with metadata                                               |        |
| 2.12 | Idempotency                    | Second run skips (marker exists)                                                    |        |
| 2.13 | Upstream dependency check      | `_upstream_available()` checks strategy + risk seed dirs                            |        |

### Phase 3: Strategy Ranker Unit Verification

Pure function testing -- no network, no cloud:

| #   | Signal                                         | Expected                                         | Status |
| --- | ---------------------------------------------- | ------------------------------------------------ | ------ |
| 3.1 | TRENDING regime, signal=0.65                   | STRADDLE selected (regime_fit match)             |        |
| 3.2 | VOLATILE regime, signal=0.45                   | STRANGLE selected                                |        |
| 3.3 | MEAN_REVERTING regime, signal=0.25             | CALENDAR_SPREAD selected                         |        |
| 3.4 | TRENDING regime, signal=0.10 (below threshold) | No strategy qualifies (score=0)                  |        |
| 3.5 | Unknown regime (no fit)                        | Empty list returned                              |        |
| 3.6 | Empty catalog                                  | Empty list returned                              |        |
| 3.7 | Multiple strategies match same regime          | Sorted by score descending, then conviction_base |        |
| 3.8 | `select_top_strategy` returns best or None     | Single best strategy or None                     |        |

### Phase 4: TradeLedger Lifecycle

In-memory ledger correctness -- no network:

| #    | Operation                          | Expected                                       | Status |
| ---- | ---------------------------------- | ---------------------------------------------- | ------ |
| 4.1  | `record_open(trade)`               | Trade in `_open` dict                          |        |
| 4.2  | `record_fill(id, price)`           | Status=FILLED, entry_price set                 |        |
| 4.3  | `record_partial_fill(id, price)`   | Status=PARTIALLY_FILLED, first fill price kept |        |
| 4.4  | `record_close(id, exit_price)`     | Moved to `_closed`, pnl_realized computed      |        |
| 4.5  | `record_cancel(id)`                | Status=CANCELLED, moved to `_closed`           |        |
| 4.6  | `update_pnl(id, unrealized)`       | `pnl_unrealized` updated for open trade        |        |
| 4.7  | `all_open_trades()`                | Returns only non-closed trades                 |        |
| 4.8  | `open_trades_for_commodity("BTC")` | Filtered by commodity                          |        |
| 4.9  | `reset()`                          | Both `_open` and `_closed` cleared             |        |
| 4.10 | Fill for unknown instruction_id    | Warning logged, no crash                       |        |
| 4.11 | Close for unknown instruction_id   | Warning logged, no crash                       |        |
| 4.12 | Cancel for unknown instruction_id  | Silently ignored                               |        |
| 4.13 | P&L uses Decimal (not float)       | No float rounding errors                       |        |

### Phase 5: Live Mode (requires downstream services)

Live mode starts the MicroLoopOrchestrator with all loops. For local testing, downstream service URLs can be empty
(loops will log errors but not crash -- fault isolation).

| #    | What                                    | Expected                                          | Status |
| ---- | --------------------------------------- | ------------------------------------------------- | ------ |
| 5.1  | Start with `CLOUD_MOCK_MODE=false`      | Orchestrator starts all loops                     |        |
| 5.2  | Loop count for 2 commodities            | 14 per-commodity loops (7 x 2) + optional L8      |        |
| 5.3  | Loop startup log lines                  | Each loop logs cadence at startup                 |        |
| 5.4  | Drift correction                        | If cycle > target, next sleep shortened           |        |
| 5.5  | Fault isolation                         | One loop exception doesn't crash others           |        |
| 5.6  | SIGINT graceful shutdown                | `stop_all()` called, loops finish current cycle   |        |
| 5.7  | SIGTERM graceful shutdown               | Same as SIGINT                                    |        |
| 5.8  | L3 kill switch                          | Trade submissions blocked when kill switch active |        |
| 5.9  | Loop with empty service URL             | Logs connection error, continues next cycle       |        |
| 5.10 | `L8_COMMENTARY_ENABLED=false` (default) | L8 loop not added to orchestrator                 |        |
| 5.11 | `L8_COMMENTARY_ENABLED=true`            | L8 loop added, requires ANTHROPIC_API_KEY         |        |

### Phase 5b: Mock vs Real A/B

| #    | Config                                | Expected                                          | Status |
| ---- | ------------------------------------- | ------------------------------------------------- | ------ |
| 5b.1 | `CLOUD_MOCK_MODE=true`                | Mock pipeline runs, decisions written to seed dir |        |
| 5b.2 | `CLOUD_MOCK_MODE=false`               | Live orchestrator starts all loops                |        |
| 5b.3 | Mock pipeline with upstream seed data | Reads from strategy-service + risk seed dirs      |        |
| 5b.4 | Mock pipeline without upstream data   | Uses fallback synthetic signals + risk metrics    |        |

### Phase 6: BaseLoop Mechanics

Verify the abstract loop base class behaviors:

| #   | Scenario                            | Expected                                         | Status |
| --- | ----------------------------------- | ------------------------------------------------ | ------ |
| 6.1 | `run_once()` completes in < cadence | Sleeps for remainder of cadence                  |        |
| 6.2 | `run_once()` takes > cadence        | Drift correction: sleep=0, debug log             |        |
| 6.3 | `run_once()` raises ValueError      | CRITICAL log, loop continues                     |        |
| 6.4 | `run_once()` raises TypeError       | CRITICAL log, loop continues                     |        |
| 6.5 | `stop()` called                     | `_running=False`, loop exits after current cycle |        |
| 6.6 | CancelledError from event loop      | Normal shutdown path                             |        |

### Phase 7: Observability

| #    | Check                          | Expected                                             | Status |
| ---- | ------------------------------ | ---------------------------------------------------- | ------ |
| 7.1  | UEI setup                      | `setup_events(service_name=..., mode="live")` called |        |
| 7.2  | Tracing setup                  | `setup_tracing(config.service_name)` called          |        |
| 7.3  | Orchestrator start log         | "MicroLoopOrchestrator starting N loops: [names]"    |        |
| 7.4  | Per-loop start log             | "Loop 'L1_data_refresh' started (cadence=300.0s)"    |        |
| 7.5  | Ledger open/close logs         | Instruction ID, strategy, commodity logged           |        |
| 7.6  | Ranker debug logs              | "No strategies matched" when score=0 for all         |        |
| 7.7  | Mock pipeline logs             | "MOCK MODE: redirecting to mock pipeline"            |        |
| 7.8  | Shutdown log                   | "Shutdown signal received -- stopping loops."        |        |
| 7.9  | Loop exception log             | "Loop 'X' terminated with exception: ..." (CRITICAL) |        |
| 7.10 | Loop exception in orchestrator | Logged per-loop, other loops unaffected              |        |

## Known Issues Audit

Before testing, check for these patterns known from other service E2E tests:

| Pattern                           | Applies?  | Notes                                                                                                                 |
| --------------------------------- | --------- | --------------------------------------------------------------------------------------------------------------------- |
| `load_dotenv(override=True)`      | Check     | Not visible in **main**.py -- verify config loading                                                                   |
| `os.getenv()` direct calls        | Check     | mock_data_provider.py uses `os.environ.get("WORKSPACE_ROOT")` -- bootstrap exception for workspace root               |
| Asyncio nesting                   | No        | All loops are async-native, orchestrator uses `asyncio.gather`                                                        |
| Float precision in P&L            | Checked   | TradeLedger uses `Decimal` -- correct                                                                                 |
| Signal race condition             | Check     | SignalCache shared between L2 (writer) and L3 (reader)                                                                |
| Ledger not persisted              | By design | Ephemeral cache, rebuilt from execution-service on restart                                                            |
| Missing L4                        | By design | Intentional gap in loop numbering                                                                                     |
| `os.environ.get` in mock provider | Check     | `_get_workspace_root()` uses `os.environ.get` for WORKSPACE_ROOT -- acceptable bootstrap exception for mock seed path |

## AWS Testing

trading-agent-service is cloud-agnostic at the loop level (communicates with downstream services via HTTP URLs). Cloud
provider only matters for config loading:

| #   | What                               | Expected                               | Status |
| --- | ---------------------------------- | -------------------------------------- | ------ |
| A.1 | `CLOUD_PROVIDER=aws` + live mode   | Loops start, URLs still HTTP           |        |
| A.2 | `CLOUD_PROVIDER=aws` + mock mode   | Mock pipeline works (local filesystem) |        |
| A.3 | `CLOUD_PROVIDER=local` + mock mode | Same as A.2                            |        |

## Frontend API Surface

trading-agent-service feeds agent status and decision data to the frontend:

| Data                         | UI Location          | What the frontend displays                            |
| ---------------------------- | -------------------- | ----------------------------------------------------- |
| Loop health / status         | Agent Dashboard      | Per-loop running/stopped, cadence, last cycle time    |
| Strategy ranking results     | Strategy Ranking     | Ranked strategies per commodity, scores, regime fit   |
| Trade decisions (TRADE/HOLD) | Autonomous Decisions | Decision log: commodity, action, strategy, score      |
| TradeLedger state            | Open Trades          | Active trades: instruction_id, status, unrealized P&L |
| Closed trades                | Trade History        | Closed trades: entry/exit price, realized P&L         |
| Risk gate status             | Risk Dashboard       | Leverage, drawdown, daily/weekly loss checks          |
| L8 Commentary                | Commentary Feed      | AI-generated market commentary per cycle              |
| Signal cache                 | Signal Monitor       | Per-commodity: master_signal, regime, confidence      |

## Issues Found

(logged in `plans/archive/issues/service_control_surface_issues_2026_03_21.md`)

| Issue      | Severity | Fixed? |
| ---------- | -------- | ------ |
| (none yet) |          |        |

## Next Service

After trading-agent-service passes all phases -> testing complete for this batch. Return to the service order in
`procedure.md` for remaining services.
