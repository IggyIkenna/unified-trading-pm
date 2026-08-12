---
doc_type: codex-ssot
title: "Cross-Cutting: Benchmark Fills Contract"
summary:
  The benchmark-fills contract that keeps batch=live honest — every execution algo exposes a deterministic
  benchmark_fill() (zero market-impact, zero timing alpha). Batch mode REPLACES real fills with it (exec_alpha=0), live
  mode computes it ALONGSIDE so execution_alpha = (real − benchmark)/benchmark bps. Defines per-algo + per-action-type +
  per-category benchmark reference tables, determinism requirements, and QG conformance enforcement.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service, market-tick-data-service]
scope: [engineer, admin]
tags: [strategy, execution, reconciliation, backtest, verification, live-trading]
related:
  [
    /codex/09-strategy/architecture-v2/cross-cutting/execution-policies.md,
    ../../../04-architecture/backtest-groups.md,
    ../../../04-architecture/strategy-execution-protocol.md,
    ../axes/edge-methods.md,
  ]
created: 2026-04-17
authoritative_for: [benchmark-fills contract (batch=live seam + execution-alpha measurement)]
referenced_by:
  [
    /codex/04-architecture/backtest-groups.md,
    /codex/04-architecture/batch-live-architecture.md,
    /codex/04-architecture/execution-policy.md,
    /codex/04-architecture/strategy-execution-protocol.md,
    /codex/09-strategy/README.md,
    /codex/09-strategy/architecture-v2/README.md,
    /codex/09-strategy/architecture-v2/archetypes/ml-directional-continuous.md,
    /codex/09-strategy/architecture-v2/axes/edge-methods.md,
  ]
owner:
last_reviewed: 2026-05-18
code_refs:
---

# Cross-Cutting: Benchmark Fills Contract

> **What it is:** The contract that lets batch mode and live mode share the same code path. Every execution algo exposes
> a `benchmark_fill()` function that returns a deterministic fill "as if" there was zero market impact and zero timing
> alpha. In batch mode, benchmark fills REPLACE real fills; in live mode, benchmark fills are computed ALONGSIDE real
> fills so `execution_alpha = real - benchmark` is measurable continuously.
>
> **Why it matters:** Without this contract, batch and live diverge. Standalone backtest engines that settle inline
> (e.g., `fill = stake * odds`) bypass the service mesh, produce incomparable P&L, and miss position/risk/execution
> feedback loops. The benchmark fills contract is the seam that keeps batch=live honest.

## The core idea

```
STRATEGY  ──  emits StrategyInstruction
    │
    ▼
EXECUTION ──  resolves execution_policy → algo
    │
    ▼
ALGO      ──  computes child orders
    │
    ▼
       ┌──────────────────────────┬───────────────────────────┐
       │  Batch mode              │  Live mode                │
       │  ──────────────          │  ──────────────           │
       │  venue.simulate(child)   │  venue.submit(child)      │
       │    ▼                     │    ▼                      │
       │  benchmark_fill()        │  real fill from venue     │
       │    ▼                     │    ▼                      │
       │  fill result             │  fill result              │
       │                          │                           │
       │  strategy_alpha =        │  strategy_alpha =         │
       │   benchmark_pnl          │   benchmark_pnl           │
       │  exec_alpha = 0          │  exec_alpha = real - benchmark │
       └──────────────────────────┴───────────────────────────┘
```

Strategy code, risk checks, position tracking, PBMS interactions, allocator directives — **all identical** across the
two modes. The only difference is which `venue.` method is called.

## What a benchmark fill is

A benchmark fill for an algo is the answer to: _"if this order were filled with zero market impact and at the benchmark
reference price, what would the fill look like?"_

| Algo                     | Benchmark reference                          |
| ------------------------ | -------------------------------------------- |
| `MARKET_SWEEP`           | mid price at order arrival                   |
| `LIMIT_BEST`             | same-side BBO at placement; fills if touched |
| `TWAP(window)`           | time-weighted mid over the window            |
| `VWAP(window)`           | volume-weighted mid over the window          |
| `ICEBERG`                | passive target + shift for queue position    |
| `QUOTE_LOOP` (MM)        | mid at each quote update                     |
| `MEV_PROTECTED_SWAP`     | pool mid at the target block                 |
| `ATOMIC_MULTI_LEG`       | per-leg benchmarks summed                    |
| `DELTA_HEDGE_CONTINUOUS` | per-tick mid                                 |
| `LIQUIDATION_FLASH_LOAN` | liquidation-bonus payout at target block     |

## Who owns the reference price — TWO benchmarks, not one

> **Reconciliation added 2026-08-12** after an operator ruling that _"strategy sends the ref price, execution layer
> marks underlying against it either statically or updates as UL moves"_ appeared to conflict with the per-algo table
> above. It does not conflict — it names a **different** benchmark. Both exist and they measure different things.

The table above makes the benchmark reference a function of the ALGO (`TWAP(window)` → time-weighted mid over the
window). But the algo is execution's choice, and the window has not happened yet when the instruction is emitted — so
strategy **cannot** know that benchmark at send time. The resolution is that there are two benchmarks with two owners,
which is already how attribution is layered in code:

| Benchmark               | Owner             | Reference                                                         | What it measures                                                           |
| ----------------------- | ----------------- | ----------------------------------------------------------------- | -------------------------------------------------------------------------- |
| **Strategy benchmark**  | strategy-service  | the ref price strategy SENDS (last/mid of the instrument at send) | Strategy alpha — and it is what a standalone backtest was measured against |
| **Execution benchmark** | execution-service | the per-algo reference in the table above                         | Execution quality against the algo's own fair standard                     |

This is not a new idea being introduced here; it is what `execution-service/execution_service/pnl_attribution/rows.py`
already implements — rows are built from a PAIR of (benchmark, live) `MatchResult`s, splitting a **STRATEGY layer**
(benchmark-fill decomposition at benchmark price) from an **EXECUTION layer** (`live_fill − benchmark_fill` residual →
`SLIPPAGE`, `FEES`). The benchmark fill itself is `BenchmarkMatcher` with `BookType.ALPHA_ZERO`, always-fill.

**Why the distinction is load-bearing rather than pedantic.** Measuring a TWAP execution against an arrival price
conflates execution skill with market drift over the window; measuring strategy alpha against a per-algo TWAP benchmark
makes a strategy's measured edge depend on an execution choice it did not make. Keeping them separate is also precisely
what licenses a **strategy-only backtest**: the STRATEGY layer is computable at the strategy's own benchmark price with
no execution-service involvement at all.

**Open decision (operator):** whether the strategy-sent ref price is authoritative for the strategy layer — recommended,
since it is the assumption the backtest was measured against — or advisory with `BenchmarkMatcher` deriving both. Until
this lands, note that execution derives its own benchmark, so **the two sides could disagree on the benchmark itself**
while every individual number still looks correct. Tracked:
`/plans/active/service_config_ownership_and_instruction_contract_2026_08_12.md` § G3.

## Per-action-type benchmarks

Different action types have different reference pricing:

| Action            | Benchmark quantity                                   |
| ----------------- | ---------------------------------------------------- |
| TRADE (spot/perp) | mid price at arrival or TWAP over window             |
| SWAP (DeFi)       | pool mid at target block                             |
| LEND              | deposit at observed APY at arrival                   |
| BORROW            | borrow at observed APY at arrival                    |
| STAKE             | stake at observed reward rate                        |
| UNSTAKE           | unstake at observed exit queue time + principal      |
| QUOTE             | passive fill at BBO with queue-position probability  |
| TRANSFER          | zero-cost transfer completes instantly               |
| BRIDGE            | bridge at median historical bridge latency           |
| ATOMIC            | sum of legs; if any leg's benchmark fails → fail all |
| CANCEL            | no-op (cancels are free)                             |

## Determinism requirements

Benchmark fills MUST be deterministic given:

- Instruction id + content
- Market state snapshot (orderbook, ticker, pool reserves, APYs, bookmaker odds)
- Venue state snapshot
- Config version

Running batch mode twice over the same data MUST produce identical benchmark fills. This is how backtest reproducibility
is guaranteed.

## Batch vs live fill assertions

**Batch mode**:

```python
assert fill.source == FillSource.BENCHMARK
assert fill.execution_alpha_bps == 0
assert fill.price == algo.benchmark_fill(market_state).price
```

**Live mode**:

```python
assert fill.source == FillSource.VENUE
assert fill.execution_alpha_bps is not None
assert fill.benchmark_price is not None
assert fill.execution_alpha_bps == (fill.price - fill.benchmark_price) / fill.benchmark_price * 10_000  # sign per action direction
```

## Strategy P&L isolation

**Group B backtest** (strategy alpha) uses benchmark fills exclusively → strategy P&L reflects ONLY the alpha of the
decision logic, not execution quality. When comparing archetype variants or threshold configs, the confounder of
execution quality is removed.

**Group C backtest** (execution alpha) feeds the **same StrategyInstruction stream** into the matching engine with
realistic microstructure and measures `execution_alpha = matching_engine_fill - benchmark_fill`. Execution policy
optimization uses Group C.

## Live execution alpha measurement

For every real fill, the system also computes the benchmark fill. Continuous running totals:

```
cumulative_execution_alpha_bps = Σ (real_fill_price - benchmark_price) / benchmark_price * 10_000 (signed)
```

Reported per:

- Strategy instance
- Archetype
- Venue
- Execution policy version
- Algo name
- Per-day / per-week windows

Used for: execution policy tuning, venue selection feedback, algo A/B tests.

## Category-specific benchmarks

### CeFi spot / perp

Mid at instruction arrival. TWAP benchmark uses exchange ticker mids at each second during the window.

### DeFi swap

Pool mid at the _target block_ (block when tx would have landed with zero delay). For MEV-protected, use pool mid at the
block when a bundle would have realistically been included.

### Sports book

Bookmaker's offered price at the moment the bet arrives — **no** market-impact discount (bookmakers rarely move on a
single bet from us; at size, this assumption breaks and we need a bookmaker-specific impact model, deferred).

### Prediction markets

CLOB mid at request; for Polymarket, mid of best bid/ask at tx inclusion block.

### TradFi

IBKR NBBO at arrival. For basket trades, per-leg NBBO; aggregated with leg weights.

### Options

Vol surface mid at arrival (IV); converted to price via surface pricer. For multi-leg (straddle), per-leg mid summed.

### LP (Uniswap V3)

Benchmark is the "idealized LP" that captured pool fees at TVL-weighted share with zero gas cost and perfect boundaries.
Real-world LP differs by boundary misses + gas + IL — that's the execution alpha.

### Carry / funding

Benchmark is the published funding rate payment at the funding-snapshot time. Real capture may differ by position-size
edge cases (partial rate tier).

## Failure modes

- **Benchmark references missing data** (stale ticker, missing orderbook snapshot) → emit `BENCHMARK_FILL_DATA_GAP`
  event; skip P&L attribution for that fill; record in audit
- **Benchmark diverges wildly from real** (>2σ from historical) → emit `EXEC_ALPHA_OUTLIER` event for investigation
- **Benchmark fill deterministic check fails** (same inputs, different output) → critical bug, halt backtest

## Contract enforcement

Every algo implementation MUST:

1. Declare `benchmark_fill(market_state, instruction) -> FillResult`
2. Declare `benchmark_inputs(instruction) -> List[MarketStateRef]`
3. Pass conformance tests: identical outputs on identical inputs
4. Include the benchmark price on every live fill emission

Enforced at QG: test-suite validates all registered algos.

## Not in this doc

- **Algo implementations** — execution-service/algo_library/
- **Market state snapshotting** — market-tick-data-service + execution-service historical replay harness
- **Batch data orchestration** — backtest runners, 3 groups
- **PnL attribution at account level** — PBMS + risk-and-exposure-service
- **Category-specific cost models** — [execution-policies.md](execution-policies.md)

## Cross-references

- Execution policies: [execution-policies.md](execution-policies.md)
- Backtest groups: [../../../04-architecture/backtest-groups.md](../../../04-architecture/backtest-groups.md)
- Strategy-execution protocol:
  [../../../04-architecture/strategy-execution-protocol.md](../../../04-architecture/strategy-execution-protocol.md)
- Batch=live architecture: `/codex/04-architecture/batch-live-architecture.md`
