---
scope: [engineer, admin]
---

# Batch = Live: Unified Pipeline Architecture

This document describes the unified pipeline architecture where batch (backtest) and live execution share the same code
path. The only difference is the fill source: matching engine for batch, real venue for live.

---

## Principle

Batch and live use the **same code path, same component interactions, same risk checks**. There is no such thing as a
"live-only strategy" or a "batch-only strategy." 99% of the code is identical. The only seam that differs is the
execution fill source.

This applies to ALL categories: CeFi, DeFi, TradFi, sports, prediction markets.

---

## Component Interaction Diagram

```
Strategy-Service -----> Execution-Service -----> Position-Balance-Monitor -----> PnL-Attribution -----> Risk-and-Exposure
     ^                        |                          |                            |                         |
     |                        |                          |                            |                         |
     +--- risk limits --------+                          +--- positions --------------+                         |
     |                                                                                                          |
     +--- exposure limits ------------------------------------------------------------------------------------------+
```

In batch mode, all five services are co-located (same process or local network). In live mode, they communicate via
PubSub. The interaction contract is identical in both modes.

Data flow:

1. **Strategy-Service** generates execution instructions from features + ML predictions
2. **Execution-Service** fills the instruction (matching engine in batch, real venue in live)
3. **Position-Balance-Monitor** updates positions from fills
4. **PnL-Attribution** computes realized and unrealized P&L
5. **Risk-and-Exposure** enforces limits and feeds back to Strategy-Service

---

## Two Execution Modes

Defined in UAC as `BatchExecutionMode` (`unified_api_contracts.internal.BatchExecutionMode`):

### BENCHMARK (strategy alpha isolation)

- Always fills at the **requested price** (exact odds for sports, exact limit price for CeFi/DeFi)
- Zero execution alpha by definition
- Zero commission, zero slippage, zero latency impact
- Purpose: isolate **strategy P&L** from execution quality
- This is the default for strategy development and backtesting

### SIMULATED (execution alpha measurement)

- Fills through the **matching engine** with realistic assumptions
- For CeFi: order book depth simulation (L1/L2), latency modelling, maker/taker fees
- For DeFi: AMM constant-product math (`x*y=k`), gas costs, MEV impact
- For sports: commission rates per venue, slight odds spread (+/-0.5%) simulating market impact
- Purpose: measure **execution alpha** = live fills P&L minus benchmark fills P&L

The matching engine lives in `execution-service/execution_service/matching_engine/`. Book type matchers:

| Matcher            | Category | Model                                           |
| ------------------ | -------- | ----------------------------------------------- |
| `L0Matcher`        | Sports   | Top-of-book (scraped bookmaker odds)            |
| `L1Matcher`        | TradFi   | Trades with aggressor side                      |
| `L2Matcher`        | CeFi     | Order book depth with 5 levels                  |
| `AMMMatcher`       | DeFi     | Constant product swaps                          |
| `BenchmarkMatcher` | All      | Always fill at requested price (benchmark mode) |

---

## Strategy Alpha vs Execution Alpha

**Strategy alpha** is the P&L attributable to the strategy's signal quality. Measured using BENCHMARK mode fills (always
fill at requested price). If a strategy generates good signals, it will show positive P&L even with zero execution
optimisation.

**Execution alpha** is the P&L difference between live fills and benchmark fills. It measures how much the execution
layer adds (or loses) relative to the idealised fill. Computed as:

```
execution_alpha = live_fills_pnl - benchmark_fills_pnl
```

This separation is critical because:

- Strategy developers optimise signal quality without worrying about execution mechanics
- Execution engineers optimise fill quality without conflating it with signal quality
- A strategy with positive strategy alpha but negative execution alpha needs execution improvement, not signal rework
- A strategy with negative strategy alpha is fundamentally unprofitable regardless of execution quality

---

## Sports-Specific Notes

### SportsMatchingEngine

Located at `execution_service/matching_engine/sports_matching.py`. Handles the full bet lifecycle:

1. `place_bet(BetOrder)` -- returns `CanonicalFill` (fill_id = bet_id, price = odds, quantity = stake)
2. `settle(bet_id, outcome)` -- settles individual bet (WON/LOST/VOID)
3. `settle_fixture(fixture_id, winning_selection)` -- settles all bets for a fixture
4. `settle_all(results)` -- batch settle by fixture results dict
5. `get_portfolio_summary()` -- returns `PortfolioSummary` with total_bets, wins, losses, ROI, bankroll

### Bets as Positions

Sports bets are positions: open on placement, closed on settlement. A bet on "HOME @ 2.50" is a position with
`instrument_id=fixture_id`, `side=BUY`, `price=2.50`, `quantity=stake`. It stays open until the fixture settles. This
maps directly to the position-balance-monitor's position lifecycle.

### CanonicalFill Mapping

`SportsMatchingEngine.place_bet()` returns a standard `CanonicalFill` from UAC:

- `fill_id` = bet UUID
- `instrument_id` = fixture_id
- `side` = BUY (backing a selection)
- `price` = odds (benchmark) or adjusted odds (simulated)
- `quantity` = stake
- `fee` = 0 (benchmark) or stake \* venue commission rate (simulated)

This ensures sports fills flow through the same position-tracking and PnL-attribution pipeline as CeFi/DeFi fills.

### Walk-Forward Capital Carryover

`run_walk_forward()` in strategy-service passes season N's `final_capital` (from the engine's `PortfolioSummary`) as
season N+1's `initial_capital`. Capital compounds across seasons through the engine, not through a separate tracking
variable.

---

## Anti-Patterns (Fixed)

These violations of the batch=live principle were identified and corrected:

1. **Inline settlement** -- Computing `returned = stake * odds` directly in the backtest loop instead of routing through
   `SportsMatchingEngine.settle_all()`. Fixed: all settlement goes through the engine.

2. **Custom P&L calculation** -- Backtest engines that computed their own P&L instead of reading from
   `PortfolioSummary.total_pnl`. Fixed: `BacktestResult` reads P&L from the engine summary.

3. **Manual position tracking** -- Maintaining a separate list of open/closed bets outside the engine. Fixed: engine
   owns the bet lifecycle (`_open_bets` / `_settled_bets`). The `BankrollState` in strategy-service is retained only for
   staking context (compute_stake needs it) and max drawdown tracking, not for settlement.

4. **Category-specific backtest engines** -- Building a standalone sports backtest that bypasses execution-service.
   Fixed: `strategy_service.engine.strategies.sports.backtest_engine` imports and uses
   `execution_service.matching_engine.sports_matching.SportsMatchingEngine`.

5. **Batch-only or live-only strategies** -- Treating batch and live as fundamentally different code paths. Fixed: the
   same strategy code runs in both modes; only the execution fill source changes.

---

## Instruments-live exception

Instruments-service runs live but does NOT use a `pipeline_mode=live` partition — instruments are reference data, not
ticks. Live-mode writes to the **same GCS path** as batch; T+1 is a retrospective audit, not a parallel backfill.
Detail: [`instruments-live-architecture.md`](instruments-live-architecture.md) +
[`instruments-preflight-chain.md`](instruments-preflight-chain.md). Live = batch invariant for instruments is mechanical
(same schema, same `available_at`, same code path; only source adapter swapped).

---

## References

- **Code-path symmetry**: [`batch-live-symmetry.md`](batch-live-symmetry.md) (UTC midnight alignment, `pipeline_mode`
  partition for ticks, instruments-as-reference-data section)
- **Live pipeline architecture**:
  [`../05-infrastructure/live-pipeline-architecture.md`](../05-infrastructure/live-pipeline-architecture.md) (MTDS
  standalone + MDPS+features-asset-scoped colocated topology, Redis Stream cascade)
- **Replay subsystem**: [`../05-infrastructure/replay-subsystem.md`](../05-infrastructure/replay-subsystem.md) (smooth
  handoff replay → live)
- **Pipeline-mode partition (data, not instruments)**:
  [`../02-data/pipeline-mode-partition.md`](../02-data/pipeline-mode-partition.md)
- **Instruments live = batch**: [`instruments-live-architecture.md`](instruments-live-architecture.md)
- **Auto-recovery + kill-switches**: [`autonomous-recovery-matrix.md`](autonomous-recovery-matrix.md)
- **Alerting parity**: [`alerting-batch-live.md`](alerting-batch-live.md)
- **Strategy hot-reload**: [`live-strategy-config-hot-reload.md`](live-strategy-config-hot-reload.md)
- **Cloud switch**: [`seamless-cloud-switch.md`](seamless-cloud-switch.md)
- **Matching engine**: `execution-service/execution_service/matching_engine/`
  - Sports: `sports_matching.py` (`SportsMatchingEngine`, `BetOrder`, `PortfolioSummary`)
  - Unified: `engine.py` (`MatchingEngine`, `BookType`, matchers)
- **Backtest engine**: `strategy-service/strategy_service/engine/strategies/sports/backtest_engine.py`
- **BatchExecutionMode**: `unified-api-contracts/unified_api_contracts/internal/execution.py` (`BENCHMARK` and
  `SIMULATED` enum values)
- **E2E validation**: `e2e-testing/tests/integration/test_unified_sports_backtest.py`
