# Session 5: Mock/Real Code Convergence

> **2026-03-24:** Historical session charter. API names below were updated to the **consolidated** surface
> (**`unified-trading-api`**, **`auth-api`**) where they referred to standalone repos now under **`archive/`**. See
> **`archive/README.md`** and **`scripts/dev/ui-api-mapping.json`**.

## Services & Repos Affected

> **DO NOT work on these repos in other sessions — they are owned by this session.**

| Repo                              | What Changes                                                       | Risk |
| --------------------------------- | ------------------------------------------------------------------ | ---- |
| market-data-processing-service    | Replace inline resample with real CandleProcessingService          | MED  |
| features-volatility-service       | Replace inline Parkinson/Yang-Zhang with real VolatilityCalculator | MED  |
| features-onchain-service          | Replace inline lending rate math with real onchain calculator      | MED  |
| features-cross-instrument-service | Replace inline correlation/regime with real calculator             | MED  |
| features-multi-timeframe-service  | Replace inline RSI/ATR with real MTF orchestrator                  | MED  |
| features-commodity-service        | Replace inline momentum/regime with real PriceMomentumFactor       | MED  |
| ml-inference-service              | Replace inline feature synthesis with real inference pipeline      | MED  |
| risk-and-exposure-service         | Replace inline position building with real RiskPositionBuilder     | MED  |
| position-balance-monitor-service  | Replace inline aggregation with real PositionTracker               | MED  |
| pnl-attribution-service           | Replace inline PnL construction with real PnL input builder        | MED  |
| alerting-service                  | Replace inline threshold eval with real evaluator                  | LOW  |

## The Problem

11 service mock providers have their own inline math that DUPLICATES the service's real domain logic. If you change a
calculator, the mock doesn't change — it has its own copy. This defeats the entire purpose of mock mode.

### Current State (per citadel audit)

| Service                   | Own Math Lines    | What It Duplicates                                           |
| ------------------------- | ----------------- | ------------------------------------------------------------ |
| market-data-processing    | 1 line (resample) | `CandleProcessingService` / `aggregate_from_15s_efficient`   |
| features-volatility       | 18 lines          | `VolatilityCalculator` (Parkinson, Yang-Zhang estimators)    |
| features-onchain          | 8 lines           | Onchain feature calculator (lending rates from index deltas) |
| features-cross-instrument | 13 lines          | Cross-instrument calculator (rolling correlations, regime)   |
| features-multi-timeframe  | 9 lines           | MTF orchestrator (RSI, ATR, EMA at multiple timeframes)      |
| features-commodity        | 16 lines          | `PriceMomentumFactor` + commodity calculator                 |
| ml-inference              | 7 lines           | Real inference pipeline (model.predict with real features)   |
| risk-and-exposure         | 28 lines          | `RiskPositionBuilder` (position construction from fills)     |
| position-balance-monitor  | 12 lines          | `PositionTracker` (signed-quantity aggregation)              |
| pnl-attribution           | 21 lines          | PnL input builder (fill→PnL input construction)              |
| alerting                  | 7 lines           | Threshold evaluator (OK/WARNING/CRITICAL classification)     |

## Plans Covered

| Plan   | Phases                      | Todos Remaining | Reference                                                |
| ------ | --------------------------- | --------------- | -------------------------------------------------------- |
| Plan B | Phase 1 (service callbacks) | ~20 todos       | plans/active/plan_b_config_hot_reload_2026_03_21.md |
| Plan C | Phase 1 (fix API mock gaps) | ~5 todos        | plans/active/plan_c_domain_data_api_2026_03_21.md   |

## What's Already Done (Don't Redo)

- All 21 services HAVE mock_data_provider.py files (created this session)
- 3 services are correct: instruments-service, market-tick-data-service (generate synthetic input — required deviation),
  features-delta-one (imports CALCULATOR_REGISTRY)
- features-calendar-service imports real TemporalFeatures calculator (correct)
- features-sports-service imports real process_sports_record (correct)
- ml-training-service imports MockFeatureProvider + ModelTrainer (mostly correct)
- strategy-service imports CeFiMomentumStrategy (mostly correct)
- execution-service imports MatchingEngine from matching-engine-library (correct)
- batch-live-reconciliation-service imports real deviation detection (correct)
- trading-agent-service imports real ranker (mostly correct)

## The Fix — Principles

### 1. ZERO inline math in mock providers

The mock_data_provider.py should contain ONLY:

- File I/O (read upstream seed data, write output)
- Service domain logic IMPORTS (from the service's own modules)
- Data format conversion (DataFrame → service input format)

It should contain ZERO:

- numpy/pandas calculations (no `.rolling()`, `.mean()`, `.std()`, `.resample()`)
- Manual formulas (no Parkinson estimator, no z-score, no signed-quantity math)
- Reimplemented business logic

### 2. Same code path for mock and real

The mock provider should call the EXACT SAME function the real pipeline calls. The only difference is WHERE the input
comes from:

- Real: GCS/PubSub/exchange API
- Mock: local seed Parquet files

```python
# WRONG — duplicates service logic:
def run_mock_pipeline():
    df = read_upstream_parquet()
    vol = df['close'].pct_change().rolling(20).std() * np.sqrt(252)  # INLINE MATH
    write_output(vol)

# RIGHT — calls real service code:
def run_mock_pipeline():
    df = read_upstream_parquet()
    from my_service.calculators.volatility import VolatilityCalculator
    calculator = VolatilityCalculator(config=default_config())
    result = calculator.calculate_features(df)  # REAL CODE
    write_output(result)
```

### 3. Response schema identical

The mock output Parquet must have the EXACT same columns, types, and structure as real output. If the real pipeline
writes columns `[timestamp, instrument_key, realized_vol_20d, realized_vol_60d, vol_of_vol]`, mock must write the same
columns. Don't invent new column names.

To verify: read the service's output schema definition (usually in `schemas/output_schemas.py` or the orchestration
service's writer). Match it exactly.

### 4. Error handling shared

If the service has error classification (classify_venue_error, shard-level failure isolation), mock mode should exercise
the same error paths. Don't skip error handling in mock — that's where bugs hide.

### 5. Statefulness shared

If the service maintains state (running totals, rolling windows, position books), mock mode should use the SAME state
management classes. Don't rebuild state tracking inline.

## Execution Order

For each of the 11 services:

### Step 1: Find the real calculator/processor

```bash
# Example for features-volatility-service:
grep -rn "class.*Calculator\|def calculate_features\|def compute" \
  features-volatility-service/features_volatility_service/ \
  --include="*.py" --glob '!.venv*' --glob '!tests*' --glob '!engine/mock*'
```

### Step 2: Read the real calculator's input/output signature

What DataFrame columns does it expect as input? What does it return? What config does it need?

### Step 3: Read the current mock_data_provider.py

Identify every line of inline math. Note what it's trying to compute.

### Step 4: Replace inline math with real calculator import

```python
# Delete the inline math
# Import the real calculator
# Call it with mock input data
# Write the output in the same format
```

### Step 5: Verify output schema matches

```python
# Read real output schema
from my_service.schemas.output_schemas import FEATURE_SCHEMA
# Verify mock output has same columns
assert set(mock_output.columns) >= set(FEATURE_SCHEMA.keys())
```

### Step 6: Commit per service

`fix(features-volatility-service): replace inline vol estimators with real VolatilityCalculator in mock mode`

## Per-Service Fix Guide

### market-data-processing-service

- **Inline math**: `ticks_df.resample(freq).agg(**ohlcv_agg)` (1 line)
- **Should import**:
  `from market_data_processing_service.app.calculators.fast_candle_aggregation import aggregate_from_15s_efficient` or
  `from market_data_processing_service.app.calculators.polars_candle_engine import create_ohlcv_candles_polars`
- **Challenge**: These functions expect 15s base candles or raw tick LazyFrames. Our mock ticks are individual trades.
  May need to first create 15s candles from ticks (which IS what the real pipeline does), then aggregate up.
- **Real pipeline flow**: raw ticks → 15s candles (timeframe_candles.py) → aggregate to 1m/5m/1h/4h/1d
  (fast_candle_aggregation.py)

### features-volatility-service

- **Inline math**: 18 lines — Parkinson high-low estimator, Yang-Zhang open-close estimator, vol-of-vol, regime z-scores
- **Should import**:
  `from features_volatility_service.app.calculators.volatility_calculator import VolatilityCalculator` (or whatever the
  real class is)
- **Find it**: `grep -rn "class.*Calculator\|class.*Estimator" features-volatility-service/`

### features-onchain-service

- **Inline math**: 8 lines — lending rate APY from rate index changes, annualization
- **Should import**: The real onchain calculator that computes rates from liquidity_index/variable_borrow_index
- **Find it**: `grep -rn "def.*lending_rate\|def.*compute.*rate\|class.*Calculator" features-onchain-service/`

### features-cross-instrument-service

- **Inline math**: 13 lines — rolling correlations at windows 20/50, vol z-score regime, return skew/kurtosis
- **Should import**: Real cross-instrument calculator
- **Find it**: `grep -rn "class.*Calculator\|def.*correlation\|def.*regime" features-cross-instrument-service/`

### features-multi-timeframe-service

- **Inline math**: 9 lines — RSI (gain/loss rolling), ATR, EMA slope at synthetic timeframes
- **Should import**: Real MTF calculator/orchestrator
- **Find it**: `grep -rn "class.*Calculator\|class.*Orchestrat\|def.*compute" features-multi-timeframe-service/`

### features-commodity-service

- **Inline math**: 16 lines — 20-day rolling return z-score, tanh normalization, vol regime
- **Should import**: `from features_commodity_service.calculators.price_momentum import PriceMomentumFactor` (or
  equivalent)
- **Find it**: `grep -rn "class.*Factor\|class.*Calculator\|def.*compute" features-commodity-service/`

### ml-inference-service

- **Inline math**: 7 lines — synthetic feature vector generation (should load real features from upstream)
- **Should import**: Real inference pipeline that loads model + features → predict
- **Find it**: `grep -rn "class.*Predictor\|class.*Inference\|def.*predict\|def.*infer" ml-inference-service/`

### risk-and-exposure-service

- **Inline math**: 28 lines — position construction from fills (signed quantity, average cost, notional)
- **Should import**: `from risk_and_exposure_service.engine.risk_position_builder import RiskPositionBuilder` or
  equivalent
- **Note**: Already imports `compute_risk_metrics` — the gap is the POSITION BUILDING step before calling it
- **Find it**:
  `grep -rn "class.*PositionBuilder\|class.*Position.*Tracker\|def.*build.*position" risk-and-exposure-service/`

### position-balance-monitor-service

- **Inline math**: 12 lines — signed-quantity aggregation with cost-basis tracking
- **Should import**: `from position_balance_monitor_service.engine.position_tracker import PositionTracker` or
  equivalent
- **Find it**: `grep -rn "class.*Tracker\|class.*Aggregat\|def.*aggregate.*position" position-balance-monitor-service/`

### pnl-attribution-service

- **Inline math**: 21 lines — fill→PnL input construction (realized/unrealized split, entry/exit matching)
- **Should import**: Real PnL input builder
- **Note**: Already imports `compute_pnl_breakdown` — the gap is building the INPUT to that function
- **Find it**: `grep -rn "class.*PnL\|class.*Attribution\|def.*build.*pnl\|def.*compute.*pnl" pnl-attribution-service/`

### alerting-service

- **Inline math**: 7 lines — threshold evaluation (leverage > 3 → CRITICAL, etc.)
- **Should import**: Real threshold evaluator from alerting service's own rules engine
- **Find it**: `grep -rn "def.*threshold\|def.*evaluate\|class.*Rule\|class.*Evaluator" alerting-service/`

## Key Rules

- uv pip install not pip install
- Never run pytest directly — use bash scripts/quality-gates.sh
- Do NOT run quickmerge — only git add + git commit
- basedpyright not pyright (with run_timeout 120)
- If a service's real calculator has cloud dependencies (GCS config reads), mock those specific I/O calls — don't
  replace the entire calculator
- Shard-level failure isolation: try/except per instrument/shard, never raise inside loops

## Success Criteria

- [ ] All 11 services have ZERO inline math in mock_data_provider.py
- [ ] Every mock provider imports from the service's own modules (not from numpy/pandas directly for domain logic)
- [ ] Output schema matches real output (same columns, same types)
- [ ] Changing a real calculator changes mock output (verified by running mock before and after a trivial change)
- [ ] All affected repos pass quality-gates.sh
