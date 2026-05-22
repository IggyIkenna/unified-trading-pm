# Float Isolation Analysis (Phase 3 Gate)

**Date**: 2026-03-13 **Audit reference**: 2026-03-11 full parallel audit, section 5 (FAIL)

## Executive Summary

94 float fields exist in `unified-internal-contracts/features.py`, all annotated with `# float-ok` comments and category
tags (financial-ratio, volatility-pct, time-based). These fields are **not imported** by execution-service or
strategy-service source code, meaning the feature schema floats do **not** leak into execution paths via direct import.

However, the execution-service **live engine** (`engine/live/`) uses `float` for price, quantity, and unrealized PnL in
its live position tracking. This is a genuine execution-path float concern separate from the features.py issue.

## Detailed Findings

### 1. unified-internal-contracts/features.py (94 float fields)

All 94 fields carry `# float-ok` inline annotations with semantic categories:

| Category        | Count | Examples                                      |
| --------------- | ----- | --------------------------------------------- |
| financial-ratio | ~55   | rsi_14, macd, momentum_5, funding_rate        |
| volatility-pct  | ~25   | rv_5, parkinson_5, atm_iv, butterfly_25d      |
| time-based      | ~4    | hours_to_next_4h_close, hours_to_weekly_close |

**Risk**: LOW. Features are ML/analytics inputs, not trade execution values. Two validator methods (`SpotFeatures`,
`DerivativesFeatures`) coerce float input via `str()` to Decimal to avoid IEEE 754 drift -- this is a defense-in-depth
measure.

**Isolation verification**: Neither execution-service nor strategy-service import `FeatureSnapshot`, `SpotFeatures`,
`DerivativesFeatures`, `MultiTimeframeFeatures`, `MicrostructureFeatures`, or `CrossAssetFeatures` from their source
directories. Features flow through the ML pipeline (feature-calculator-library -> features-\* services) and never enter
the execution or risk path directly.

### 2. unified-feature-calculator-library (extensive float usage)

All float usage is in NumPy/pandas statistical computations (z-scores, skew, quantiles, normalization). These are
intermediate analytics values that produce the feature schema fields above. Not on any execution path.

**Risk**: NONE for execution isolation.

### 3. execution-service

#### 3a. Backtest + Services layer: Decimal-safe

Core financial modules use `Decimal` throughout:

- `services/position_tracker.py` -- all amounts, prices, PnL in `Decimal`
- `services/funding_rate_tracker.py` -- position sizes, rates, payments in `Decimal`
- `services/gas_cost_model.py` -- gas prices, costs in `Decimal`
- `services/instruction_alpha_calculator.py` -- benchmark_price, market_price in `Decimal` (but output `alpha_bps` and
  `alpha_usd` are `float` after `round()`)

#### 3b. Live engine: FLOAT LEAK (P1 concern)

**`engine/live/positions.py`** uses float for:

- `quantity: float`
- `current_price: float = 0.0`
- `average_entry_price: float | None`
- `unrealized_pnl: float | None`

**`engine/live/router.py`** uses float for:

- `fee_cost: float`
- `quantity: float`
- `price: float`

**`engine/execution_alpha/__init__.py`** uses float for:

- `quantity: float`
- `price: float`

These are on the **live execution path** -- real trades with real money. Float rounding errors accumulate over many
trades. This is the genuine concern flagged by audit section 5.

#### 3c. Instruction validator: float inputs

`validation/instruction_validator.py` accepts `entry_price: float | None`, `stop_loss: float | None`,
`take_profit: float | None`. These are converted from upstream data and used for validation only (not PnL calculation).

**Risk**: MEDIUM. Validation thresholds could be affected by float precision, but only for edge cases near exact price
levels.

#### 3d. Results layer: float for reporting

`results/position_manager.py` converts Decimal to float for reporting output. `results/result_formatter.py` uses float
for display formatting.

**Risk**: LOW. Reporting is read-only; no round-trip back to execution.

### 4. strategy-service

#### 4a. Backtest engine: Decimal-safe

`engine/backtest/backtest_engine.py` uses `Decimal` throughout for equity, PnL, positions, stop-loss, take-profit. All
config values are converted via `Decimal(str(...))` pattern.

#### 4b. Config layer: float for parameters

`strategy_service/config.py` has 22 float annotations for configuration parameters: `health_factor_min`, `ltv_max`,
`max_leverage`, `initial_capital`, `entry_zscore`, `exit_zscore`, `min_edge_pct`, etc.

**Risk**: LOW-MEDIUM. Config values are read once and used as thresholds/parameters. The backtest engine converts them
to Decimal before use. However, if a strategy uses config float values in live calculations without conversion,
precision could drift.

#### 4c. PnL models: Mixed

`models/pnl.py` core fields (`delta_amount`, `delta_usd`) use `Decimal`. Metadata dicts use
`dict[str, str | int | float | bool | None]` -- float in metadata is acceptable (non-critical).

### 5. Other repos (sports.py, deployment.py, etc.)

Float fields in `sports.py` (latitude, longitude, ratings, xG) and `deployment.py` (progress_pct) are non-financial and
pose no risk.

## Risk Matrix

| Location                                 | Float Count | Execution Path? | Risk   | Action Required?          |
| ---------------------------------------- | ----------- | --------------- | ------ | ------------------------- |
| UIC features.py                          | 94          | No              | LOW    | No (float-ok annotated)   |
| feature-calculator-library               | ~80         | No              | NONE   | No                        |
| execution-service engine/live/           | 7           | YES             | HIGH   | YES -- migrate to Decimal |
| execution-service engine/execution_alpha | 2           | YES             | HIGH   | YES -- migrate to Decimal |
| execution-service validation/            | 3           | Partial         | MEDIUM | Consider migration        |
| execution-service results/               | ~5          | No (read-only)  | LOW    | No                        |
| strategy-service config                  | 22          | Indirect        | LOW    | No (converted at use)     |
| strategy-service models/pnl metadata     | ~6          | No              | NONE   | No                        |

## Recommendations

1. **P1**: Migrate `execution_service/engine/live/positions.py` from float to Decimal for quantity, price, and
   unrealized_pnl fields. This is the highest-risk float usage in the entire system.

2. **P1**: Migrate `execution_service/engine/live/router.py` fee_cost, quantity, price to Decimal.

3. **P2**: Migrate `execution_service/engine/execution_alpha/__init__.py` quantity/price to Decimal.

4. **P3**: Review `instruction_alpha_calculator.py` output path -- `alpha_bps` and `alpha_usd` are converted to float
   via `float()` after Decimal computation. Consider keeping as Decimal through the output chain.

5. **No action needed**: features.py float fields are correctly isolated from execution paths. The `# float-ok`
   annotations are accurate.

## Gate Verdict

**Features.py isolation: VERIFIED** -- 94 float fields do not reach execution paths.

**Live engine isolation: NOT VERIFIED** -- 9 float fields in `engine/live/` and `engine/execution_alpha/` are on active
execution paths and need Decimal migration before the Phase 3 gate can pass.
