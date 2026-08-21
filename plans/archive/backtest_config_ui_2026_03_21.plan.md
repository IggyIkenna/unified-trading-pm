---
doc_type: plan
title: backtest-config-ui-2026-03-21
summary: UI for configuring and launching mass backtests using the Fixed vs Grid two-tier architecture. Three tabs (ML,
  Strategy, Execution), fixed param dropdowns, grid param range sliders, shard count preview, and GCS config upload.
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [execution-service, strategy-service]
scope: [engineer, admin]
tags: [ui, backtest, config, grid]
related: []
created: '2026-03-21'
type: code
epic: epic-code-completion
priority: P1
owner: human
completion_gates: {code: C4, deployment: none, business: none}
repo_gates:
- {repo: trading-analytics-ui, code: C0, deployment: none, business: none, readiness_note: Most likely home for this UI. Could also be a new backtest-config-ui.}
depends_on: [fixed-grid-config-refactor-2026-03-21]
---

# Backtest Config UI — Plan Doc

## UX Concept

### Layout: Three Tabs

```
┌──────────────────┬──────────────────┬──────────────────┐
│  ML Training     │  Strategy        │  Execution       │
└──────────────────┴──────────────────┴──────────────────┘
```

Each tab has two sections:

#### Section 1: Fixed Parameters (Dropdowns)

- **Instrument**: dropdown (BTC-USDT, SPORTS:FOOTBALL:39, SPY-USD, ...)
- **Timeframe**: dropdown (5m, 1h, 4h, seasonal)
- **Target Type**: dropdown (swing_high, swing_low, clv, xg, ht_delta)
- **Model Type**: dropdown (lightgbm, xgboost, ensemble, ...)
- **Pipeline Depth**: dropdown (3=base, 5=meta, 6=cross)
- **CV Strategy**: dropdown (date, seasonal)
- **Strategy Mode**: dropdown (momentum, mean_reversion, value_betting, ...)
- **Initial Capital**: number input

#### Section 2: Grid Parameters (Range Sliders)

- **Context-sensitive**: selecting `target_type=swing_high` shows:
  - `swing_lookback_window`: range slider [2 ──●────●── 50]
  - `std_dev_threshold`: range slider [0.5 ──●──●── 3.0]
  - `breakout_threshold`: range slider [0.5 ──●── 2.0]
- Selecting `target_type=clv` shows:
  - `odds_time_bucket`: multi-select (T-60m, T-24h, T-12h, ...)
  - `closing_line_window_minutes`: range slider [5 ──●── 60]
- Selecting `strategy_mode=momentum` shows:
  - `prediction_threshold`: range slider [0.5 ──●──●── 0.8]
  - `stop_loss_pct`: range slider [0.01 ──●── 0.05]
- **Single value = fixed**: slide to a point → that param is not gridded
- **Range = grid**: slide to a range → generates combinatoric grid

#### Footer: Preview + Submit

- **Shard count**: "This experiment will generate **288 shards**" (live calculation)
- **Estimated time**: based on shard count × average shard duration
- **Submit**: generates `BacktestExperimentConfig` JSON → uploads to GCS → triggers batch run

### Data Flow

```
UI (React) → BacktestExperimentConfig JSON
  → POST /api/backtest/experiment (backtest-api or execution-service API)
  → Validates config (BacktestExperimentConfig.model_validate)
  → Uploads individual shard configs to GCS
  → Triggers batch Cloud Run jobs (one per shard)
  → Returns experiment_id for tracking
```

### API Contract

```typescript
// POST /api/backtest/experiment
interface BacktestExperimentRequest {
  fixed: {
    instrument_id: string;
    timeframe: string;
    target_type: string;
    model_type: string;
    pipeline_depth: number;
    cv_strategy: string;
    strategy_mode: string;
    initial_capital: number;
  };
  grid: {
    target_type_params: Record<string, (number | string | boolean)[]>;
    strategy_mode_params: Record<string, (number | string | boolean)[]>;
    execution_algo_params: Record<string, Record<string, Record<string, (number | string | boolean)[]>>>;
  };
  walk_forward_folds: number;
  start_date?: string;
  end_date?: string;
}

// Response
interface BacktestExperimentResponse {
  experiment_id: string;
  shard_count: number;
  shard_config_paths: string[]; // GCS paths
  status: "submitted" | "error";
}
```

### Implementation Notes

- Use existing `STRATEGY_MODE_VALID_PARAMS` from strategy-service to drive which sliders appear
- Use `TargetType` enum values from UIC to populate dropdowns
- Grid param ranges could be loaded from `default_target_type_params` in UCI (MLTrainingConfig)
- Shard count = product of all grid dimension list lengths (calculated client-side)
- The API endpoint should reuse `BacktestExperimentConfig` from UIC for validation

## Todos

- [ ] [AGENT] P0. Identify which UI repo hosts this (trading-analytics-ui vs new repo).
- [ ] [AGENT] P0. Design React component: BacktestConfigPanel with 3 tabs.
- [ ] [AGENT] P0. Implement FixedParamsSection with dropdowns for all fixed config fields.
- [ ] [AGENT] P0. Implement GridParamsSection with context-sensitive range sliders.
- [ ] [AGENT] P0. Implement shard count preview (live calculation from grid dimensions).
- [ ] [AGENT] P0. Add API endpoint for experiment submission (POST /api/backtest/experiment).
- [ ] [AGENT] P1. Add experiment tracking UI (status, progress, results per shard).
- [ ] [SCRIPT] P0. QG gate on UI repo.
