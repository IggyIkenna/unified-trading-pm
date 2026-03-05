# NautilusTrader Removal Plan

**Context**: Remove NautilusTrader dependency and use our own execution algorithm implementation. Algorithms are simple (TWAP, VWAP, Adaptive, etc.) and we can implement them exactly how we want.

---

## Nautilus Usage Analysis

### File Count

| Component                    | Files         | What It Uses                                                                                                  | Replacement                                         |
| ---------------------------- | ------------- | ------------------------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| **algorithms/impl/**         | 4 files       | ExecAlgorithm, spawn_market, submit_order, cache, clock, Order, Bar, BarType, InstrumentId, Quantity, Price   | execution-algo-library + our BaseExecutionAlgorithm |
| **algorithms/registry.py**   | 1 file        | ExecAlgorithmConfig, ExecAlgorithm                                                                            | Our registry with our base                          |
| **backtest/engine.py**       | 1 file        | BacktestNode, ParquetDataCatalog, InstrumentId, Venue, OrderBookDeltas, is_backtest_force_stop                | **BLOCKER** - Our own backtest engine               |
| **backtest/node_builder.py** | 1 file        | BacktestEngineConfig, BacktestRunConfig, ImportableExecAlgorithmConfig, ImportableStrategyConfig, BuiltinTWAP | Our config builder                                  |
| **backtest/actors/**         | 4 files       | Strategy, StrategyConfig, Bar, TradeTick, OrderFilled, PositionOpened, PositionClosed                         | Our strategy/actor layer                            |
| **data/**                    | 7 files       | ParquetDataCatalog, TradeTick, Bar, OrderBookDeltas, InstrumentId, BacktestDataConfig                         | Our catalog + data types                            |
| **engine/**                  | 3 files       | ParquetDataCatalog, Bar, InstrumentId                                                                         | Our catalog                                         |
| **instruments/factory.py**   | 1 file        | ParquetDataCatalog                                                                                            | Our instrument factory                              |
| **tests/**                   | 6 files       | Bar, BarType, Quantity, ClientOrderId, OrderStatus, TradeTick, AggressorSide                                  | api-contracts/nautilus mocks                        |
| **Total**                    | **21+ files** |                                                                                                               |                                                     |

### What Nautilus Provides (By Category)

| Nautilus Component                 | Usage                                                    | Replacement                                                                 |
| ---------------------------------- | -------------------------------------------------------- | --------------------------------------------------------------------------- |
| **ExecAlgorithm** base class       | 4 algorithm impls inherit                                | Our `BaseExecutionAlgorithm` (simple interface)                             |
| **spawn_market()**                 | Create child market order from parent                    | Our `create_child_order()` returning `ChildOrder`                           |
| **submit_order()**                 | Send order to venue                                      | `OrderAdapter` (unified-trade-execution-interface)                          |
| **cache**                          | order(), instrument(), bar(), trade_tick(), order_book() | Our `ExecutionContext` (dict/dataclass with market data)                    |
| **clock**                          | utc_now(), set_time_alert(), cancel_timer()              | `datetime.now(timezone.utc)` + `asyncio.create_task()` or `threading.Timer` |
| **Order, Position, Instrument**    | Nautilus model types                                     | api-contracts/nautilus schemas OR our own                                   |
| **Bar, BarType, BarSpecification** | OHLCV data                                               | Our `OHLCVBar` dataclass                                                    |
| **TradeTick**                      | Last trade price                                         | Our `TradeTick` dataclass                                                   |
| **ParquetDataCatalog**             | Store/query backtest data                                | Our Parquet catalog (PyArrow) OR keep Nautilus format for compatibility     |
| **BacktestNode**                   | Event loop, tick processing, order matching              | **Our own backtest engine** (largest effort)                                |

---

## What We Already Have

### 1. api-contracts/nautilus/ (Mocks)

- `schemas.py`: Order, Position, Instrument, Fill, Account (Pydantic)
- `cache.py`: Cache Protocol, MockCache
- `clock.py`: Clock Protocol, MockClock
- `mocks.py`: Factory functions

**Status**: Exists but execution-service tests still import from `nautilus_trader` directly. Can be used for algorithm unit tests.

### 2. unified-trade-execution-interface

- `BaseOrderAdapter`: place_order(), cancel_order(), get_order_status()
- `CanonicalOrder`, `ExecutionResult`, `ExecutionStatus`
- execution-service has `OrderAdapter` that delegates to this

**Status**: Ready for live order submission. Not used by backtest (backtest uses Nautilus's internal submit_order).

### 3. execution-algo-library (Pure Logic, NO Nautilus)

- **Algorithms**: TWAPAlgorithm, VWAPAlgorithm, AdaptiveTWAPCalculator, AlmgrenChrissCalculator
- **Schemas**: ChildOrder, AlgoConfig, TWAPConfig, VWAPConfig, etc.
- **Base**: ExecutionAlgorithm (async execute(), get_child_orders())

**Status**: Pure Python, zero Nautilus. execution-service already uses `AdaptiveTWAPCalculator` via `algo_library_adapter`. Can expand usage.

### 4. Our Own Order Types, Position Tracking

- execution-service has models for instructions, operations
- unified-trade-execution-interface has CanonicalOrder

---

## Replacement Strategy

### Phase 1: Replace Algorithm Base (2-3 weeks)

**Remove**: `ExecAlgorithm` base class, Nautilus algorithm configs

**Add**: Our own `BaseExecutionAlgorithm` in execution-service (or execution-algo-library)

```python
# execution_service/algorithms/base.py
from execution_algo_library import ChildOrder

class ExecutionContext:
    """Replaces Nautilus cache + clock."""
    def __init__(self, *, orders: dict, instruments: dict, bars: dict, trade_ticks: dict, clock_now):
        self.orders = orders
        self.instruments = instruments
        self.bars = bars
        self.trade_ticks = trade_ticks
        self.clock_now = clock_now

    def order(self, client_order_id: str): ...
    def instrument(self, instrument_id: str): ...
    def bar(self, bar_type: str): ...
    def trade_tick(self, instrument_id: str): ...

class BaseExecutionAlgorithm:
    """Simple interface - no Nautilus."""
    def on_order(self, order: OrderLike, context: ExecutionContext, submit_fn: Callable) -> None:
        """Handle parent order, schedule and submit child orders via submit_fn."""
        raise NotImplementedError
```

**Interface for algorithms**:

- Input: Parent order (our schema), ExecutionContext (market data), submit_fn (callback to submit child)
- Output: None (algorithms call submit_fn for each child order)

**Migration**: Refactor adaptive_twap, vwap, almgren_chriss, hybrid_optimal to use our base. Each algorithm:

1. Uses execution-algo-library for schedule calculation (AdaptiveTWAPCalculator, etc.)
2. Uses our ExecutionContext for market data (bars, ticks)
3. Uses submit_fn (or OrderAdapter) for order submission
4. Uses asyncio/scheduler for timing instead of clock.set_time_alert

### Phase 2: Replace Order Submission (1 week)

**Remove**: `spawn_market()`, `submit_order()` (Nautilus methods)

**Use**:

- **Live**: `OrderAdapter` (unified-trade-execution-interface) - already exists
- **Backtest**: Our backtest engine's simulated order router (see Phase 4)

**Note**: Phase 2 is intertwined with Phase 1. Algorithms need a submit abstraction that works for both live (real venue) and backtest (simulated).

### Phase 3: Replace Timing (1 week)

**Remove**: `clock.set_time_alert()`, `clock.cancel_timer()`, `clock.utc_now()`

**Use**:

- `datetime.now(timezone.utc)` for current time
- `asyncio.create_task(asyncio.sleep(interval); callback())` for scheduled slices
- Or `threading.Timer` for sync context
- Store timer handles for cancellation (e.g., `_pending_timers: dict[str, asyncio.Task]`)

### Phase 4: Replace Backtest Engine (6-10 weeks) — **BLOCKER**

**Remove**: BacktestNode, ParquetDataCatalog (Nautilus), Strategy (Nautilus), InstrumentId, Venue

**Options**:

| Option                                                   | Effort            | Risk   | Recommendation                                         |
| -------------------------------------------------------- | ----------------- | ------ | ------------------------------------------------------ |
| **A) Build our own backtest engine**                     | 6-10 weeks        | Medium | Full control, no Nautilus                              |
| **B) Keep Nautilus for backtest only**                   | 0 weeks (Phase 4) | Low    | Hybrid: our algorithms for live, Nautilus for backtest |
| **C) Use different library** (e.g., Backtrader, Zipline) | 4-6 weeks         | High   | Different API, may not fit                             |

**What our backtest engine would need**:

1. **Event loop**: Process ticks/bars in time order
2. **Data catalog**: Parquet storage (we can keep Nautilus's Parquet schema for data compatibility, or define our own)
3. **Order matching**: L1_MBP (mid-price from bars) or L2_MBP (order book simulation)
4. **Strategy/actor layer**: Signal-driven logic (our signal_driven_v3 equivalent)
5. **ExecAlgorithm integration**: Our algorithms receive orders, submit children, engine simulates fills
6. **Result extraction**: Timeline, PnL, execution alpha (we have ResultExtractor, TimelineBuilder)

**Data flow today**:

- GCS → UCSDataLoader → our converter → ParquetDataCatalog (Nautilus format) → BacktestNode
- We could: GCS → our loader → our catalog (Parquet, our schema) → our engine

**ParquetDataCatalog**: Nautilus uses a specific Parquet layout. We have two choices:

1. **Keep Nautilus format**: Build our engine to read Nautilus Parquet (less work on data pipeline)
2. **Our format**: Define our Parquet schema, update converter to write our format (cleaner long-term)

---

## Benefits of Removal

1. **Simpler**: No external framework, just our code
2. **Faster**: No Nautilus overhead (~90MB wheel, Rust components)
3. **Flexible**: Implement exactly what we need (TWAP, VWAP, Adaptive, etc.)
4. **Testable**: No Nautilus mocks needed; use api-contracts/nautilus or our types
5. **Maintainable**: We control the code; no upstream breaking changes
6. **Dependency reduction**: Remove nautilus-trader (and its transitive deps) from pyproject.toml

---

## LOC Impact (Estimate)

| Category                          | Remove                           | Add                        | Net      |
| --------------------------------- | -------------------------------- | -------------------------- | -------- |
| Algorithm Nautilus wrappers       | ~1,200                           | ~400 (our base + adapters) | -800     |
| Backtest engine (if we build)     | ~800 (node_builder, engine glue) | ~2,500 (our engine)        | +1,700   |
| Data catalog                      | ~200 (PatchedParquetDataCatalog) | ~300 (our catalog)         | +100     |
| Tests (Nautilus imports)          | ~150                             | ~100 (api-contracts)       | -50      |
| **Total (full removal)**          | **~2,350**                       | **~3,300**                 | **+950** |
| **Total (hybrid: keep backtest)** | **~1,200**                       | **~400**                   | **-800** |

---

## Effort Estimate

| Phase                    | Scope                                         | Duration       |
| ------------------------ | --------------------------------------------- | -------------- |
| **Phase 1**              | Replace algorithm base, refactor 4 algorithms | 2-3 weeks      |
| **Phase 2**              | Replace order submission (with Phase 1)       | (included)     |
| **Phase 3**              | Replace timing (with Phase 1)                 | (included)     |
| **Phase 4a**             | Keep Nautilus for backtest only (hybrid)      | 0 weeks        |
| **Phase 4b**             | Build our own backtest engine                 | 6-10 weeks     |
| **Total (Hybrid)**       | Phases 1-3 only                               | **3-4 weeks**  |
| **Total (Full removal)** | Phases 1-4b                                   | **9-14 weeks** |

---

## Risks

| Risk                              | Mitigation                                                                                    |
| --------------------------------- | --------------------------------------------------------------------------------------------- |
| **Backtest engine bugs**          | Start with L1_MBP only (simpler); add L2_MBP later. Extensive unit tests for fill simulation. |
| **Data format migration**         | Option: Keep reading Nautilus Parquet format initially; migrate schema later.                 |
| **Regression in execution alpha** | Compare our engine results vs Nautilus on same data; add regression tests.                    |
| **Timing/scheduling edge cases**  | Replicate Nautilus's timer behavior in tests; document any differences.                       |

---

## Recommendation

### Option 1: Hybrid (Recommended for near-term)

**Remove Nautilus from algorithms only. Keep Nautilus for backtest.**

- **Phases 1-3**: Replace ExecAlgorithm, spawn_market, submit_order, cache, clock with our own
- **Challenge**: Our algorithms must still work inside Nautilus's backtest. That means we need an **adapter layer**: our algorithms produce ChildOrders, and a thin Nautilus ExecAlgorithm wrapper converts them to Nautilus orders and calls spawn_market/submit_order.
- **Benefit**: Live path uses our code entirely. Backtest continues to work. Lower risk.
- **Effort**: 3-4 weeks

**Implementation**: Create `NautilusExecAlgorithmAdapter` that:

1. Wraps our `BaseExecutionAlgorithm` (e.g., AdaptiveTWAPOurs)
2. On Nautilus `on_order`: calls our algorithm with ExecutionContext (built from Nautilus cache/clock)
3. Our algorithm yields ChildOrder objects
4. Adapter converts each ChildOrder to Nautilus order via spawn_market, calls submit_order

This way: our algorithm logic is Nautilus-free; only the adapter touches Nautilus.

### Option 2: Full Removal (Long-term)

**Remove Nautilus entirely, including backtest.**

- **Phase 4b**: Build our own backtest engine
- **Benefit**: Zero Nautilus dependency. Full control.
- **Effort**: 9-14 weeks total
- **When**: After hybrid is stable, or if Nautilus becomes a blocking issue (e.g., Python 3.14 incompatibility, license change).

### Option 3: Defer Backtest Replacement

**Remove Nautilus from live path now. Build backtest engine later.**

- **Phases 1-3**: Same as hybrid, but live-only. Backtest keeps current Nautilus algorithms.
- **Result**: Two algorithm implementations temporarily (Nautilus ExecAlgorithms for backtest, our algorithms for live). Tech debt until Phase 4b.
- **Not recommended**: Doubles algorithm maintenance.

---

## Next Steps

1. **Decide**: Hybrid vs full removal
2. **If hybrid**: Design `NautilusExecAlgorithmAdapter` and our `BaseExecutionAlgorithm` interface
3. **If full**: Create epic for backtest engine; break into tasks (event loop, data catalog, order matching, strategy layer)
4. **Spike**: Prototype one algorithm (e.g., AdaptiveTWAP) with our base + adapter to validate approach
