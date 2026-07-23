---
doc_type: codex-ssot
title: Fixed vs Grid Config — Mass Backtesting Architecture
summary:
  Two-tier backtest config — Tier-1 fixed selections (lookup keys) select the active parameter space, Tier-2 per-type
  parameter bags grid only valid params — shared across ML training, strategy, and execution services.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service, strategy-service, unified-api-contracts]
scope: [engineer, admin]
tags: [ml, strategy, execution, backfill, uac]
related:
  [/codex/04-architecture/backtest-groups.md, /codex/09-strategy/architecture-v2/cross-cutting/execution-policies.md]
created: 2026-03-27
authoritative_for: [fixed-vs-grid two-tier backtest config architecture]
referenced_by:
owner:
last_reviewed: 2026-05-17
code_refs:
---

# Fixed vs Grid Config — Mass Backtesting Architecture

**SSOT for backtest configuration structure across ML training, strategy, and execution services.**

## Two-Tier Architecture

Backtest configs use a two-tier structure. This applies uniformly regardless of asset class (TradFi, CeFi, DeFi,
Sports).

### Tier 1 — Fixed Selections (Lookup Keys)

Picked once per experiment. Not gridded. They determine which parameter space is active.

| Field             | Type         | Examples                            | Purpose                          |
| ----------------- | ------------ | ----------------------------------- | -------------------------------- |
| `instrument_id`   | `str`        | `BTC-USDT`, `SPORTS:FOOTBALL:39`    | What to predict on               |
| `timeframe`       | `str`        | `5m`, `1h`, `seasonal`              | Prediction interval              |
| `target_type`     | `TargetType` | `swing_high`, `clv`, `xg`           | What outcome to classify/regress |
| `model_type`      | `ModelType`  | `lightgbm`, `ensemble`              | Algorithm                        |
| `pipeline_depth`  | `int`        | `3` (base), `5` (meta), `6` (cross) | How many phases to run           |
| `cv_strategy`     | `str`        | `date`, `seasonal`                  | Walk-forward split method        |
| `strategy_mode`   | `str`        | `momentum`, `value_betting`         | How to act on predictions        |
| `initial_capital` | `float`      | `100000.0`                          | Starting equity                  |

### Tier 2 — Grid Dimensions (Per-Type Parameter Bags)

Combinatoric search within the parameter space selected by Tier 1. Each target type, strategy mode, and execution
algorithm has its own parameter bag. Only relevant params are gridded.

#### Per Target Type

| Target Type                | Valid Params                                                                               |
| -------------------------- | ------------------------------------------------------------------------------------------ |
| `swing_high` / `swing_low` | `swing_lookback_window` (int), `std_dev_threshold` (float), `breakout_threshold` (float)   |
| `clv`                      | `odds_time_bucket` (str), `closing_line_window_minutes` (int), `min_odds_bookmakers` (int) |
| `xg`                       | `regression_target` (str), `max_goals_for_probs` (int), `include_opponent_strength` (bool) |
| `ht_delta`                 | `prediction_horizon` (str)                                                                 |
| `cross_venue_spread`       | `compression_threshold` (float)                                                            |

#### Per Strategy Mode

| Strategy Mode            | Valid Params                                                                        |
| ------------------------ | ----------------------------------------------------------------------------------- |
| `momentum`               | `prediction_threshold`, `stop_loss_pct`, `take_profit_pct`, `max_position_size_usd` |
| `mean_reversion`         | `entry_z_score`, `exit_z_score`, `lookback_period`                                  |
| `value_betting`          | `min_edge_pct`, `stake_sizing`, `stake_amount`, `stake_pct`, `max_bet_absolute`     |
| `stat_arb`               | `cointegration_lookback`, `entry_zscore`, `exit_zscore`, `hedge_ratio_window`       |
| `pure_lending` / `basis` | (no griddable params)                                                               |

#### Per Execution Algorithm

Algo params are keyed by `instruction_type → algorithm`:

```
execution_algo_params = {
    "TRADE": {"ALMGREN_CHRISS": {"horizon_secs": [300, 600], "risk_aversion": [0.3, 0.5]}},
    "SWAP": {"SMART_ORDER_ROUTER": {"max_slippage_bps": [50, 100]}}
}
```

## Schema Location (SSOT)

| Schema                                  | Repo                              | File                        |
| --------------------------------------- | --------------------------------- | --------------------------- |
| `BacktestFixedConfig`                   | unified-api-contracts (internal/) | `domain/ml/schemas.py`      |
| `GridDimensions`                        | unified-api-contracts (internal/) | `domain/ml/schemas.py`      |
| `BacktestExperimentConfig`              | unified-api-contracts (internal/) | `domain/ml/schemas.py`      |
| `ModelVariantConfig.target_params`      | unified-api-contracts (internal/) | `domain/ml/schemas.py`      |
| `TrainingGridConfig.target_type_params` | ml-training-service               | `app/core/config_loader.py` |
| `STRATEGY_MODE_VALID_PARAMS`            | strategy-service                  | `cli/grid_generator.py`     |
| `generate_per_algo_grid_configs`        | execution-service                 | `config/grid_utils.py`      |

## How It Works

```
User picks Fixed selections (Tier 1)
  │
  ├── target_type = "swing_high"  →  grid: {swing_lookback_window: [5,10], std_dev_threshold: [1.5,2.0]}
  ├── strategy_mode = "momentum"  →  grid: {prediction_threshold: [0.55,0.6], stop_loss_pct: [0.02]}
  └── execution algo = ALMGREN_CHRISS  →  grid: {horizon_secs: [300,600]}
                                              │
                                              ▼
                                    2 × 2 × 2 × 2 × 2 = 32 shards
                                    Each shard runs independently
```

## How Services Chain

```
ML training (BacktestExperimentConfig)
  → trains model per shard
  → outputs: model_id + predictions
       │
       ▼
Strategy (uses model_id as input)
  → generates strategy instructions per shard
  → outputs: StrategyInstruction list
       │
       ▼
Execution (uses instructions as input)
  → executes with algo params per shard
  → outputs: fills, PnL, alpha metrics
```

## Adding a New Target Type

1. Add the value to `TargetType` enum in `unified_api_contracts/internal/domain/ml/schemas.py`
2. Document its valid params in this file's "Per Target Type" table
3. Create a target generator in `ml-training-service/app/core/` that reads from `variant_config.target_params`
4. Add default param presets to `unified-config-interface/ml_config.py` `default_target_type_params`

## Adding a New Strategy Mode

1. Add the mode to `strategy-service/strategy_service/config.py` `default_mode` description
2. Add the mode + valid params to `STRATEGY_MODE_VALID_PARAMS` in `cli/grid_generator.py`
3. Implement the strategy logic in `strategy-service/strategy_service/engine/`

## Adding a New Execution Algorithm

1. Add the algorithm to `execution-service/execution_service/algorithms/`
2. Register it in `ALGORITHM_SETS` in `grid_generator_models.py`
3. The per-algo grid generator (`config/grid_utils.py`) picks it up automatically

## Why Not Flat Cartesian

A flat cartesian product of all dimensions produces nonsensical combinations:

- `swing_lookback_window=5` with `target_type=clv` (CLV has no swing lookback)
- `min_edge_pct=5.0` with `strategy_mode=momentum` (momentum has no edge concept)
- `horizon_secs=300` with `instruction_type=ZERO_ALPHA` (lending has no execution algo)

The per-type parameter bag pattern ensures only valid combinations are generated.

## Backwards Compatibility

All `ModelVariantConfig` constructors still accept flat kwargs (`swing_lookback_window=5, std_dev_threshold=1.5`). A
`model_validator` (Pydantic) or `from_dict()` migration (dataclass) moves them into `target_params` automatically. This
means old serialized configs, old CLI invocations, and old test fixtures all keep working.
