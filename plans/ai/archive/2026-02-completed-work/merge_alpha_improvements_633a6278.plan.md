---
name: Merge Alpha Improvements
overview: Merge valuable code fixes, documentation, and tests from alpha-improvements into main, plus port Streamlit visualizer features to React UI for a single unified interface.
todos:
  - id: copy-algo-docs
    content: Copy ALGORITHM_MARKET_ASSUMPTIONS.md and ALPHA_CALCULATION_ASSUMPTIONS.md from alpha to main
    status: pending
  - id: copy-spec-docs
    content: Copy docs/specs/ALGORITHM_PARAMS.md and docs/EXEC_ALGORITHM_ROUTING_FIX.md from alpha
    status: pending
  - id: copy-test-scripts
    content: Copy entire tests/algos/ directory from alpha to main
    status: pending
  - id: fix-twap-params
    content: Apply TWAP parameter override bug fix to signal_driven_v3.py
    status: pending
  - id: port-signals-alpha
    content: Port Signals & Alpha view from Streamlit to Analysis.tsx
    status: pending
  - id: port-equity-curve
    content: Port Equity Curve visualization to Analysis.tsx
    status: pending
  - id: port-timeline
    content: Port Timeline view to DeepDive.tsx
    status: pending
  - id: create-algo-comparison
    content: Create new AlgorithmComparison.tsx page for multi-algorithm comparison
    status: pending
  - id: port-price-signals
    content: Add Price + Signals combined chart to React UI
    status: pending
isProject: false
---

# Merge Alpha-Improvements: Best of Both + Unified React UI

## Summary of Changes

This plan merges alpha-improvements into main by:

1. **Copying documentation and tests** (no conflicts)
2. **Applying critical code fixes** (TWAP parameter override bug)
3. **Porting Streamlit features to React** (unified UI)

---

## Part 1: Documentation & Tests (Copy from Alpha)

### Files to Copy


| Source (alpha-improvements)                                      | Destination |
| ---------------------------------------------------------------- | ----------- |
| `execution_services/algorithms/ALGORITHM_MARKET_ASSUMPTIONS.md`  | Same path   |
| `execution_services/algorithms/ALPHA_CALCULATION_ASSUMPTIONS.md` | Same path   |
| `docs/specs/ALGORITHM_PARAMS.md`                                 | Same path   |
| `docs/EXEC_ALGORITHM_ROUTING_FIX.md`                             | Same path   |
| `tests/algos/*` (entire directory)                               | Same path   |


These are **new files** that don't exist in main - no conflicts.

---

## Part 2: Critical Code Fixes (Merge from Alpha)

### TWAP Parameter Override Bug Fix (CRITICAL)

**File:** `execution_services/backtest/actors/signal_driven_v3.py`

**Problem:** Config parameters (`horizon_secs`, `interval_secs`) were being overridden by dynamic calculations, causing all backtests to produce identical results regardless of config.

**Fix from alpha (lines 899-946):**

```python
# Only calculate dynamic horizon if config doesn't provide horizon_secs
config_has_horizon = "horizon_secs" in base_params and base_params.get("horizon_secs") is not None

if not config_has_horizon:
    # Calculate dynamic horizon only if config doesn't specify it
    ...
else:
    # Config provides horizon_secs - use it and respect config interval_secs
```

**Action:** Cherry-pick this specific fix into main's `signal_driven_v3.py`

---

## Part 3: Port Streamlit Features to React UI

### Current State Comparison


| Feature                   | Streamlit (alpha) | React (main)                    | Action     |
| ------------------------- | ----------------- | ------------------------------- | ---------- |
| Run Backtest              | Yes               | Yes (RunBacktest.tsx)           | Keep React |
| Load Results              | Yes               | Yes (LoadResults.tsx)           | Keep React |
| Config Browser            | Yes               | Yes (ConfigBrowser.tsx)         | Keep React |
| Config Generator          | Yes               | Yes (ConfigGenerator.tsx)       | Keep React |
| Market Tick Data          | Yes               | Yes (MarketTickData.tsx)        | Keep React |
| Instrument Definitions    | No                | Yes (InstrumentDefinitions.tsx) | Keep React |
| **Price + Signals Chart** | Yes               | No                              | **PORT**   |
| **Signals & Alpha View**  | Yes               | No                              | **PORT**   |
| **Equity Curve**          | Yes               | No                              | **PORT**   |
| **Timeline View**         | Yes               | No                              | **PORT**   |
| **Algorithm Comparison**  | Yes               | No                              | **PORT**   |


### Features to Port to React

#### 1. Price + Signals Chart

- Combined price chart with signal markers (BUY/SELL arrows)
- TP/SL levels shown on chart
- Entry/exit price visualization
- **Target:** Add as tab in `DeepDive.tsx` or new `SignalChart.tsx`

#### 2. Signals & Alpha View

- Signal summary table
- Execution alpha breakdown (entry alpha, exit alpha, net alpha)
- Volume-weighted alpha calculation display
- **Target:** Add as tab in `Analysis.tsx`

#### 3. Equity Curve

- Portfolio equity over time
- Drawdown visualization
- **Target:** Add as tab in `Analysis.tsx`

#### 4. Timeline View

- Order/fill timeline visualization
- Time-based event markers
- **Target:** Add as tab in `DeepDive.tsx`

#### 5. Algorithm Comparison

- Compare multiple algorithms side-by-side
- Entry price improvement analysis
- Batch comparison across runs
- **Target:** New `AlgorithmComparison.tsx` page

---

## Part 4: Code Architecture Decision

### Algorithm Routing Pattern

**Alpha approach:** `on_order_accepted()` safety nets + `scheduled` flag
**Main approach:** `_spawn_xxx_child_fresh()` fresh cache lookups

**Recommendation:** Keep main's approach (cleaner code), but add the documented pattern to `EXEC_ALGORITHM_ROUTING_FIX.md` for reference.

---

## Implementation Order

1. Copy documentation files from alpha to main
2. Copy `tests/algos/` directory from alpha to main
3. Apply TWAP parameter override fix to `signal_driven_v3.py`
4. Port Signals & Alpha view to React `Analysis.tsx`
5. Port Equity Curve to React `Analysis.tsx`
6. Port Timeline view to React `DeepDive.tsx`
7. Create new `AlgorithmComparison.tsx` page
8. Add Price + Signals chart to React
9. Delete Streamlit visualizer (not needed)

---

## Files Summary


| Action | Path                                                             |
| ------ | ---------------------------------------------------------------- |
| COPY   | `execution_services/algorithms/ALGORITHM_MARKET_ASSUMPTIONS.md`  |
| COPY   | `execution_services/algorithms/ALPHA_CALCULATION_ASSUMPTIONS.md` |
| COPY   | `docs/specs/ALGORITHM_PARAMS.md`                                 |
| COPY   | `docs/EXEC_ALGORITHM_ROUTING_FIX.md`                             |
| COPY   | `tests/algos/*`                                                  |
| FIX    | `execution_services/backtest/actors/signal_driven_v3.py`         |
| PORT   | Signals & Alpha → `Analysis.tsx`                                 |
| PORT   | Equity Curve → `Analysis.tsx`                                    |
| PORT   | Timeline → `DeepDive.tsx`                                        |
| CREATE | `AlgorithmComparison.tsx`                                        |
| SKIP   | `visualizer/` (Streamlit - not needed)                           |


