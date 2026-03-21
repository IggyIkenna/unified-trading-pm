---
title: "Strategy-Service Legacy Backtest Engine — Dead Architecture"
created: 2026-03-21
source_session: session_2_config_services coverage analysis
locked_by: live-defi-rollout
locked_since: 2026-03-21
---

# Strategy-Service Legacy Backtest Engine — Dead Architecture

## What

strategy-service contains 882 lines of legacy backtest code at 0% coverage:

- `engine/core/backtest/backtest_service.py` (150L)
- `engine/core/backtest/accurate_backtest_service.py` (225L)
- `engine/core/backtest/comprehensive_backtest_service.py` (347L)
- `engine/core/backtest/full_pipeline_backtest_service.py` (160L)

Plus `engine/backtest/backtest_engine.py` with its own `FillSimulator` (candle-based fill simulation at OPEN price with
OCO exits).

## Why This Is Wrong

The live/batch alignment architecture says:

1. **Strategy-service** generates `StrategyInstruction` → publishes to execution-service
2. **Execution-service** handles fills in both modes:
   - **Live**: real exchange via UTEI adapters
   - **Batch**: matching-engine-library (L2Matcher, L1Matcher, AMMMatcher — proper order-book matching)
3. Execution-service returns `CanonicalFill` back to strategy-service
4. Strategy-service tracks running P&L from received fills

In batch mode, strategy-service should receive **zero-alpha benchmark fills** (bought at the price you saw — no
slippage). Execution-service adds its own alpha via real order-book simulation. The two combine for total P&L with alpha
attribution.

strategy-service's internal `FillSimulator` duplicates what execution-service already does, but worse (candle-based vs
order-book-based). It's the old "strategy does everything" monolith approach.

## Evidence

- `FillSource` protocol already exists with two implementations:
  - `SimulatedFillSource` — **legacy** (internal fill simulation)
  - `ExchangeFillSource` — **correct** (receives fills from execution-service via PubSub)
- execution-service already has NautilusTrader-based backtest engine with proper matching
- The batch handler says: `"This is a placeholder for the full backtest/live engine dispatch"`
- These files blocked strategy-service from hitting 70% coverage (882 lines at 0%)
- Had a circular import (`fill_source ↔ backtest_engine`) — fixed with lazy import in Session 2

## Action

- [ ] Delete `engine/core/backtest/` directory (4 legacy backtest services)
- [ ] Delete `SimulatedFillSource` from `engine/fill_source.py`
- [ ] Delete `engine/backtest/fill_simulator.py` and `engine/backtest/flash_loan_simulator.py`
- [ ] Wire batch handler to send `StrategyInstruction` to execution-service and receive `CanonicalFill` via
      `ExchangeFillSource`
- [ ] Keep `BacktestEngine` only if it's the NautilusTrader integration bridge (check if duplicated in
      execution-service)
- [ ] After deletion: strategy-service coverage should jump past 70% naturally

## Impact

- ~882 lines of dead code removed
- Coverage jumps from 67% → ~78%+ (removing dead denominator)
- Eliminates architectural confusion (where does backtest live?)
- Aligns with live/batch alignment principle: strategy code path identical in both modes
