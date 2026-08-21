---
doc_type: plan
title: fixed-grid-config-refactor-2026-03-21
summary: Split ML training, strategy, and execution backtest configs into Fixed (lookup keys) vs Grid (combinatoric search)
  tiers. Target-type-specific params move from top-level fields into per-type dicts. Enables unified mass backtesting across
  TradFi/CeFi/DeFi/Sports without nonsensical cross-products.
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [execution-service, strategy-service, unified-trading-pm]
scope: [engineer, admin]
tags: [ml, strategy, execution, config, backtest, grid, architecture]
related: []
created: "2026-03-21"
type: code
epic: epic-code-completion
priority: P0
owner: human
locked_by:
locked_since:
completion_gates: { code: C4, deployment: none, business: none }
repo_gates:
  - { repo: unified-internal-contracts, code: C0, deployment: none, business: none }
  - { repo: unified-ml-interface, code: C0, deployment: none, business: none }
  - { repo: unified-config-interface, code: C0, deployment: none, business: none }
  - { repo: ml-training-service, code: C0, deployment: none, business: none }
  - { repo: strategy-service, code: C0, deployment: none, business: none }
  - { repo: execution-service, code: C0, deployment: none, business: none }
  - { repo: unified-domain-client, code: C0, deployment: none, business: none }
  - { repo: ml-inference-service, code: C0, deployment: none, business: none }
  - { repo: unified-trading-pm, code: none, deployment: none, business: none, readiness_note: Plan + codex docs only. }
depends_on: [uniform-ml-pipeline-sports-migration-2026-03-20]
---

# Fixed vs Grid Config Refactor — Mass Backtesting Architecture

## Context

### Problem

All three backtesting services (ML training, strategy, execution) use **flat cartesian grids** for config generation.
This produces nonsensical combinations (e.g., `swing_lookback_window` applied to a `clv` target type) and prevents
unified mass backtesting across asset classes.

### Solution: Two-Tier Config Architecture

**Tier 1 — Fixed selections** (lookup keys, not gridded):

- Instrument, timeframe, pipeline_depth (1-stage vs 2-stage meta), model_candidates, cv_strategy, target_type,
  strategy_mode

**Tier 2 — Grid dimensions** (per-type parameter bags, combinatoric search):

- Per `target_type`: swing_high → {swing_lookback_window, std_dev_threshold}; clv → {odds_time_bucket,
  closing_line_window}
- Per `strategy_mode`: momentum → {prediction_threshold, stop_loss}; value_betting → {min_edge_pct, stake_sizing}
- Per `instruction_type.algorithm`: TRADE.ALMGREN_CHRISS → {horizon_secs, risk_aversion}

Grid only explodes within the relevant parameter space. Fixed selections determine which parameter bags are active.

### Strategy → Execution Contract (Already Correct)

The execution config schema already uses `execution: {instruction_type: {algorithm, params}}`. One config, multiple
algos keyed by instruction type. **No refactor needed for the cross-service contract.** This plan restructures the grid
generation and config schemas, not the runtime contracts.

### What Changes

1. `ModelVariantConfig`: swing_lookback_window/std_dev_threshold/breakout_threshold → `target_params: dict`
2. `TrainingGridConfig`: split into fixed + grid_dimensions with per-target-type param bags
3. `TargetGenerator`: factory reads params from target_params dict (partially done — extend)
4. Strategy grid: per-strategy-mode param bags (extend existing grid_generator.py)
5. Execution grid: already scoped by instruction_type — add per-algo grid generation

## Execution DAG

```
Phase 1 (T0: UIC schemas) ──► Phase 2 (T1: UMI + UCI) ──► Phase 3a (ml-training) ──► Phase 4 (QG sweep)
                                                      ├──► Phase 3b (strategy)    ──┤
                                                      └──► Phase 3c (execution)   ──┘
```

---

## Phase 1: unified-internal-contracts (T0) — Schemas

- [ ] [AGENT] P0. Add `TargetTypeParams` Pydantic model to `domain/ml/schemas.py`: Frozen BaseModel with
      `target_type: str` + `params: dict[str, int | float | str | bool]`. Known param sets documented in docstring:
  - swing_high/swing_low: swing_lookback_window (int), std_dev_threshold (float), breakout_threshold (float)
  - clv: odds_time_bucket (str), closing_line_window_minutes (int), min_odds_bookmakers (int)
  - xg: regression_target (str), max_goals_for_probs (int), include_opponent_strength (bool)
  - ht_delta: ht_state_features (list), prediction_horizon (str)
  - cross_venue_spread: compression_threshold (float)

- [ ] [AGENT] P0. Refactor `ModelVariantConfig` in `domain/ml/schemas.py`: Remove `swing_lookback_window`,
      `std_dev_threshold`, `breakout_threshold` as top-level fields. Add
      `target_params: dict[str, int | float | str | bool] = {}`. Add `get_target_param(key: str, default: T) -> T`
      helper method. Add backwards-compat `@model_validator(mode="before")` that migrates old flat fields into
      target_params.

- [ ] [AGENT] P0. Add `StrategyModeParams` Pydantic model to `domain/strategy_service/`: Same pattern:
      `strategy_mode: str` + `params: dict[str, int | float | str | bool]`. Known param sets:
  - momentum: prediction_threshold, stop_loss_pct, take_profit_pct, max_position_size_usd
  - mean_reversion: entry_z_score, exit_z_score, lookback_period
  - value_betting: min_edge_pct, stake_sizing (str), stake_amount/stake_pct (float)
  - stat_arb: cointegration_lookback, entry_zscore, exit_zscore, hedge_ratio_window

- [ ] [AGENT] P0. Add `FixedConfig` / `GridDimensions` base schemas to `domain/ml/schemas.py`: `FixedConfig`:
      instrument_id, timeframe, target_type, model_type, pipeline_depth (int, 1-6), cv_strategy (str:
      "date"/"seasonal"), initial_capital (float). `GridDimensions`: target_type_params (dict[str, dict[str, list]]),
      strategy_mode_params (dict[str, dict[str, list]]), execution_algo_params (dict[str, dict[str, dict[str, list]]]).
      Both frozen Pydantic BaseModels. These are the SSOT schemas — services extend them.

- [ ] [AGENT] P1. Update `__init__.py` exports + tests for all new types.

- [ ] [SCRIPT] P0. QG gate: `cd unified-internal-contracts && bash scripts/quality-gates.sh`

---

## Phase 2a: unified-ml-interface (T1) — PARALLEL with 2b

- [ ] [AGENT] P0. Refactor `ModelVariantConfig` in `models.py`: Mirror UIC changes: remove
      swing_lookback_window/std_dev_threshold/breakout_threshold as top-level. Add
      `target_params: dict[str, int | float | str | bool] = {}`. Update `to_dict()` / `from_dict()` with backwards
      compat (flat → target_params migration). Update `generate_model_id()` to include target_params hash suffix.

- [ ] [AGENT] P0. Update `ModelMetadata` in `models.py`: `swing_lookback_window` / `std_dev_threshold` /
      `breakout_threshold` properties now delegate to `variant_config.target_params.get(...)` with defaults.

- [ ] [AGENT] P1. Update all UMI tests for new ModelVariantConfig shape.

- [ ] [SCRIPT] P0. QG gate: `cd unified-ml-interface && bash scripts/quality-gates.sh`

### Phase 2b: unified-config-interface (T1) — PARALLEL with 2a

- [ ] [AGENT] P0. Refactor `MLTrainingConfig` in `ml_config.py`: Remove `swing_lookback_windows` as top-level field. Add
      `default_target_type_params: dict[str, dict[str, list]]` with default presets:

  ```python
  {"swing_high": {"swing_lookback_window": [2,3,5,10,20,50], "std_dev_threshold": [1.0,1.5,2.0,2.5]},
   "swing_low": {"swing_lookback_window": [2,3,5,10,20,50], "std_dev_threshold": [1.0,1.5,2.0,2.5]}}
  ```

  Backwards compat: if `swing_lookback_windows` set via env, auto-populate into default_target_type_params.

- [ ] [AGENT] P0. Add `StrategyGridConfig` schema to new `strategy_grid_config.py`: `fixed: FixedStrategyConfig`
      (strategy_mode, ml_model_id, initial_capital, execution_mode). `grid: dict[str, dict[str, list]]`
      (per-strategy-mode params). Validation: grid keys must be valid param names for the fixed.strategy_mode.

- [ ] [AGENT] P1. Add `ExecutionGridConfig` schema to `execution_config_schema.py`: `fixed: FixedExecutionConfig`
      (venue, instruction_types). `grid: dict[str, dict[str, dict[str, list]]]` (instruction_type → algo → param lists).
      Extends existing `execution: {instruction_type: {algorithm, params}}` pattern.

- [ ] [AGENT] P1. Update tests.

- [ ] [SCRIPT] P0. QG gate: `cd unified-config-interface && bash scripts/quality-gates.sh`

---

## Phase 3a: ml-training-service (T3) — PARALLEL with 3b, 3c

- [ ] [AGENT] P0. Refactor `TrainingGridConfig` in `app/core/config_loader.py`: Split into `fixed` and `grid` sections:

  ```python
  @dataclass
  class TrainingGridConfig:
      # FIXED — picked once
      name: str
      instruments: list[str]
      timeframes: list[str]
      target_types: list[str]
      model_types: list[str]
      pipeline_depth: int = 3  # phases 1-3 base, 4-5 meta, 6 cross
      cv_strategy: str = "date"
      walk_forward_folds: int = 5

      # GRID — per target_type, combinatoric search
      target_type_params: dict[str, dict[str, list]]
      # e.g. {"swing_high": {"swing_lookback_window": [5,10], "std_dev_threshold": [1.5]}}

      @property
      def total_variants(self) -> int:
          # For each instrument × timeframe × target_type:
          #   product of that target_type's param lists
          ...
  ```

  Remove flat `swing_lookback_windows`, `std_dev_thresholds`, `breakout_thresholds`. Update `PRODUCTION_GRID`,
  `DEVELOPMENT_GRID`, `TEST_GRID` presets.

- [ ] [AGENT] P0. Update variant generation in `training_orchestrator.py`: Currently iterates
      `product(instruments, timeframes, lookback_windows, ...)`. Change to: for each (instrument, timeframe,
      target_type), expand that target_type's param grid. Each combo → ModelVariantConfig with target_params dict.

- [ ] [AGENT] P0. Update `TargetGenerator` to read from `target_params`: `_select_outcome_column()` reads
      `variant_config.target_params["swing_lookback_window"]` instead of `variant_config.swing_lookback_window`. Add
      KeyError guard with clear message.

- [ ] [AGENT] P0. Update all CLI handlers that reference `swing_lookback_windows` / `--swing-lookback-windows`: CLI flag
      becomes `--target-params` (JSON string) or kept as `--swing-lookback-windows` but auto-mapped into
      target_type_params for swing_high/swing_low target types.

- [ ] [AGENT] P1. Update `grid_search_handler.py`, `train_handler.py`, `preselection_handler.py`, `evaluate_handler.py`,
      `final_training_handler.py` for new config shape.

- [ ] [AGENT] P1. Update all tests (57+ files touched in earlier rename — same files need updating).

- [ ] [SCRIPT] P0. QG gate: `cd ml-training-service && bash scripts/quality-gates.sh`

### Phase 3b: strategy-service (T3) — PARALLEL with 3a, 3c

- [ ] [AGENT] P0. Extend `grid_generator.py` with per-strategy-mode grid support: Accept `StrategyGridConfig` (from
      UCI). For each strategy_mode, only grid that mode's params. Output: list of flat configs (same as today), but
      generated from structured input.

- [ ] [AGENT] P0. Add strategy mode param validation: When strategy_mode = "momentum", only accept
      {prediction_threshold, stop_loss_pct, take_profit_pct, ...}. When strategy_mode = "value_betting", only accept
      {min_edge_pct, stake_sizing, stake_amount, ...}. Reject unknown params for a given mode.

- [ ] [AGENT] P1. Update batch_handler.py and live_handler.py to accept new StrategyGridConfig shape.

- [ ] [AGENT] P1. Update tests.

- [ ] [SCRIPT] P0. QG gate: `cd strategy-service && bash scripts/quality-gates.sh`

### Phase 3c: execution-service (T3) — PARALLEL with 3a, 3b

- [ ] [AGENT] P0. Extend backtest grid generation to use per-algo param grids: Input: `ExecutionGridConfig` from UCI.
      For each instruction_type → algorithm, grid that algorithm's params. Output: list of flat execution configs (same
      shape as today).

- [ ] [AGENT] P1. Update config_loader.py to accept ExecutionGridConfig as alternative to flat config.

- [ ] [AGENT] P1. Update tests.

- [ ] [SCRIPT] P0. QG gate: `cd execution-service && bash scripts/quality-gates.sh`

---

## Phase 4: Downstream Consumers + Validation

- [ ] [AGENT] P0. Update unified-domain-client: any references to ModelVariantConfig.swing_lookback_window →
      target_params access pattern. Update integration tests.

- [ ] [AGENT] P0. Update ml-inference-service: orchestrator.py ModelVariantConfig construction → use target_params dict.

- [ ] [SCRIPT] P0. Full QG sweep on all 8 affected repos.

- [ ] [AGENT] P1. Workspace-wide grep verification: no bare `swing_lookback_window` as top-level ModelVariantConfig
      field access (should all be via target_params or backwards-compat property).

- [ ] [AGENT] P1. Write codex doc: `unified-trading-/codex/04-architecture/fixed-grid-config.md` documenting the
      two-tier pattern, per-type param bags, and how to add new target types / strategy modes.

---

## Phase 5: Codex SSOT + UI Plan Docs

- [ ] [AGENT] P0. Write codex doc: `unified-trading-/codex/04-architecture/fixed-grid-config.md`
  - Two-tier architecture: Fixed (lookup keys) vs Grid (combinatoric search)
  - Per-target-type param bags: what params each target_type accepts
  - Per-strategy-mode param bags: what params each strategy_mode accepts
  - Per-algo param bags: what params each execution algo accepts
  - How to add a new target_type / strategy_mode / algo
  - How services chain: ML output → strategy input → execution input
  - Why flat cartesian is wrong (nonsensical cross-products)

- [ ] [AGENT] P0. Update `unified-trading-codex/00-SSOT-INDEX.md`: Add entry pointing to
      `04-architecture/fixed-grid-config.md` as SSOT for backtest config structure.

- [ ] [AGENT] P1. Write UI plan doc: `unified-trading-pm/plans/archive/backtest_config_ui_2026_03_21.plan.md` (plan doc
      only — NO UI code changes). UX concept:
  - Three tabs: Machine Learning | Strategy | Execution
  - Each tab has two sections: Fixed Parameters (dropdowns) and Grid Parameters (range sliders)
  - Fixed params are dropdowns: instrument, timeframe, target_type, model_type, strategy_mode, pipeline_depth
  - Grid params are range sliders: slide to select a range → grids that range; slide to single value → fixed
  - Grid params shown are context-sensitive: selecting target_type=swing_high shows swing_lookback_window slider,
    selecting target_type=clv shows odds_time_bucket dropdown
  - Preview: shows total shard count (product of all grid dimension lengths)
  - Submit: generates BacktestExperimentConfig JSON, uploads to GCS, triggers batch run

---

## Success Criteria

- TrainingGridConfig accepts per-target-type param bags, not flat cartesian
- StrategyGridConfig accepts per-strategy-mode param bags
- ExecutionGridConfig accepts per-algo param bags (keyed by instruction_type)
- A `swing_high` grid never applies `odds_time_bucket`; a `clv` grid never applies `swing_lookback_window`
- Backwards compat: old flat configs still deserialize (validator migrates to target_params)
- All 8 repos pass quality-gates.sh
- Existing tests pass with minimal changes (backwards compat validators handle old shape)
