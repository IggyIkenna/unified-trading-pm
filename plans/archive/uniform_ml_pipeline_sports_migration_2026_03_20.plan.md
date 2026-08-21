---
doc_type: plan
title: uniform-ml-pipeline-sports-migration-2026-03-20
summary: Uniform 5+1 phase training pipeline (TradFi/CeFi/DeFi/Sports); CosmicTrader sports migration into UTS. Phase 1
  SSOT is unified-internal-contracts (not UCI). HyperparameterConfig discriminated union requires explicit model_type —
  no implicit default; migrate all serialized configs.
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ml, sports, pipeline, migration, architecture]
related: []
created: '2026-03-21'
type: code
epic: epic-code-completion
priority: P0
owner: human
locked_by:
locked_since:
completion_gates: {code: C4, deployment: none, business: none}
repo_gates:
- {repo: unified-internal-contracts, code: C0, deployment: none, business: none}
- {repo: unified-ml-interface, code: C0, deployment: none, business: none}
- {repo: unified-sports-reference-interface, code: C0, deployment: none, business: none}
- {repo: unified-feature-orchestration-library, code: C0, deployment: none, business: none}
- {repo: unified-config-interface, code: C0, deployment: none, business: none, readiness_note: Sports ML config only; no UAC domain re-exports.}
- {repo: matching-engine-library, code: C0, deployment: none, business: none}
- {repo: features-sports-service, code: C0, deployment: none, business: none}
- {repo: ml-training-service, code: C0, deployment: none, business: none}
- {repo: ml-inference-service, code: C0, deployment: none, business: none}
- {repo: unified-trading-pm, code: none, deployment: none, business: none, readiness_note: Sharding / topology manifests if updated.}
depends_on: [sports-schema-allocation-restructuring]
---

# Uniform ML Pipeline + CosmicTrader Sports Migration

## Context

Create a uniform 5+1 phase training pipeline across all asset classes (TradFi, CeFi, DeFi, Sports) while integrating
CosmicTrader's sports domain intelligence into UTS. Each phase is a separate batch deployment instance. Key decisions:
global model (all leagues, `league_id` as categorical), pooled horizons (Star Lizard approach — one base model,
per-horizon meta-models), both regression + classification, configurable meta-input strategy.

Full design doc: `/Users/ikennaigboaka/.claude/plans/dapper-bubbling-kazoo.md`

## Execution DAG

```
Phase 1 (unified-internal-contracts) → Phase 2a/2b/2c (PARALLEL) → Phase 2d (FSS) → Phase 3 (ml-training) → Phase 4 (ml-inference) → Phase 5 (integration)
```

---

## Chunk 1: Contracts + Interfaces + Domain Logic

### Phase 1: unified-internal-contracts (T0)

- [ ] [AGENT] P0. Add `TrainingPhase` StrEnum to `ml.py`: FEATURE_SELECTION, HYPERPARAMETER_TUNING, BASE_RESULTS,
      META_LEARNING, META_RESULTS, CROSS_PIPELINE
- [ ] [AGENT] P0. Extend `TargetType` enum: add CLV, XG, HT_DELTA, CLV_META, XG_META
- [ ] [AGENT] P0. Extend `ModelType` enum: add CATBOOST, HUBER, POISSON_GLM, RIDGE, ENSEMBLE
- [ ] [AGENT] P0. Generalize `HyperparameterConfig` → discriminated union: LightGBMHyperparams | XGBoostHyperparams |
      CatBoostHyperparams | HuberHyperparams | PoissonGLMHyperparams | RidgeHyperparams. Require explicit `model_type`
      in all configs; migrate stored configs that omit it (no silent default).
- [ ] [AGENT] P0. Add `EnsembleConfig` + `EnsembleMember` Pydantic models
- [ ] [AGENT] P0. Add `TrainingPipelineConfig` Pydantic model with: asset_group, task_type (regression/classification),
      multi_model, pool_horizons, meta_input_strategy (residual/signal_vector), validation_granularity
      (seasonal/quarterly/monthly/yearly), competition_phase_filter, evaluation_metrics, selection_metric,
      pipeline_dependencies, walk_forward_folds, train_test_ratio, time_horizons
- [ ] [AGENT] P1. Update `__init__.py` exports for all new types
- [ ] [AGENT] P1. Add tests for discriminated union deserialization, TrainingPipelineConfig validation
- [ ] [SCRIPT] P0. QG gate: `cd unified-internal-contracts && bash scripts/quality-gates.sh`

### Phase 2a: unified-ml-interface (T1) — PARALLEL with 2b, 2c

- [ ] [AGENT] P0. Update `config_schema.py` VALID_CATEGORIES: add "sports"
- [ ] [AGENT] P0. Update `config_schema.py` VALID_MODEL_TYPES: add "huber", "poisson_glm", "ridge", "ensemble"
- [ ] [AGENT] P0. Update `config_schema.py` VALID_TARGET_TYPES: add "clv", "xg", "ht_delta", "clv_meta", "xg_meta"
- [ ] [AGENT] P0. Update `config_schema.py` VALID_TIMEFRAMES: add "T-24h", "T-12h", "T-6h", "T-3h", "T-1h", "T-15m",
      "T-0", "HT"
- [ ] [AGENT] P0. Update `models.py` HyperparameterConfig dataclass to generic wrapper delegating to
      unified-internal-contracts discriminated union
- [ ] [AGENT] P0. Update `models.py` ModelVariantConfig + `_detect_category()` for sports instrument_id
      (SPORTS:FOOTBALL:ALL, SPORTS:FOOTBALL:39)
- [ ] [AGENT] P0. Update `config_schema.py` generate_model_id() / parse_model_id() to handle sports format
- [ ] [AGENT] P1. Create `metrics/sports.py`: port CosmicTrader's football_metrics.py — Poisson NLL, RPS, Brier score,
      Log Loss H/D/A, xG→match outcome probabilities
- [ ] [AGENT] P1. Update tests for all new categories, model types, target types, timeframes, sports model ID gen/parse
- [ ] [SCRIPT] P0. QG gate: `cd unified-ml-interface && bash scripts/quality-gates.sh`

### Phase 2b: USRI + UFOL + UCI (T1) — PARALLEL with 2a, 2c

- [ ] [AGENT] P0. Create `unified_sports_reference_interface/competition_phase.py`: port CosmicTrader's
      classify_competition_phase() — NORMAL_LEAGUE, LEAGUE_SPLIT, PLAYOFF, DECIDER, TOURNAMENT classification
- [ ] [AGENT] P0. Create `unified_feature_orchestration_library/anti_leakage.py`: port CosmicTrader's
      validate_no_leakage() — before_date temporal enforcement, cross-service (all 8 feature services should use it)
- [ ] [AGENT] P1. Create `unified_config_interface/sports_ml_config.py`: SportsMLConfig with feature config presets
      (travel thresholds, weather thresholds, EWMA halflifes, odds horizons, lineup cutoff minutes)
- [ ] [AGENT] P1. Create `unified_config_interface/sports_feature_config.py`: feature calculator configs migrated from
      CosmicTrader's features/config.py
- [ ] [AGENT] P1. Add tests for competition_phase, anti_leakage, sports configs
- [ ] [SCRIPT] P0. QG gate: `cd unified-sports-reference-interface && bash scripts/quality-gates.sh`
- [ ] [SCRIPT] P0. QG gate: `cd unified-feature-orchestration-library && bash scripts/quality-gates.sh`
- [ ] [SCRIPT] P0. QG gate: `cd unified-config-interface && bash scripts/quality-gates.sh`

### Phase 2c: matching-engine-library (T2) — PARALLEL with 2a, 2b

- [ ] [AGENT] P0. Create `matching_engine_library/sports_matching.py`: SportsMatchingEngine — bet placement simulation,
      odds matching, settlement logic. Follows PaperMatchingEngine pattern for financial. Execution-service uses this in
      BATCH mode for backtesting.
- [ ] [AGENT] P1. Add tests for SportsMatchingEngine (bet placement, partial fill, settlement)
- [ ] [SCRIPT] P0. QG gate: `cd matching-engine-library && bash scripts/quality-gates.sh`

### Phase 2d: features-sports-service (T3) — depends on 2b (UFOL anti_leakage)

- [ ] [AGENT] P0. Create `calculators/weather_calculator.py`: port CosmicTrader's weather.py — Open-Meteo integration
      (temp, wind, humidity, cloud cover, severity scoring)
- [ ] [AGENT] P0. Wire anti_leakage from UFOL into FSS engine — all calculators get before_date parameter
- [ ] [AGENT] P1. Enrich `odds_calculator.py`: expand from 4-5 features → 20+ (implied probs, vig%, bookmaker
      disagreement, odds movement, best odds, variance). Fix .iterrows() → vectorized.
- [ ] [AGENT] P1. Enrich `poisson_xg_calculator.py`: expand features (strength ratings, Poisson-xG blend, scipy.poisson
      PMF). Fix .iterrows() → vectorized.
- [ ] [AGENT] P1. Enrich `h2h_calculator.py`: expand features (venue-specific H2H, xG history, BTTS rate, goal timing
      patterns). Fix .iterrows() → vectorized.
- [ ] [AGENT] P1. Enrich `halftime_calculator.py`: expand from ~10 to 70+ features (HT performance vs expected,
      momentum, 2nd half predictions, cards impact)
- [ ] [AGENT] P1. Enrich `team_form.py`: expand features (form momentum, goals std/trend, home/away splits, conversion
      rate)
- [ ] [AGENT] P2. Enrich remaining calculators (league, season_context, referee, venue_context, goal_timing,
      advanced_stats) with CosmicTrader's additional feature formulas
- [ ] [AGENT] P1. Verify output schemas match ml-training-service expectations
- [ ] [SCRIPT] P0. QG gate: `cd features-sports-service && bash scripts/quality-gates.sh`

---

## Chunk 2: Training + Inference + Integration

### Phase 3: ml-training-service (T3)

- [ ] [AGENT] P0. Create `app/training/model_trainer_factory.py`: ModelTrainerFactory — given ModelType, returns
      appropriate trainer (LightGBMTrainer, XGBoostTrainer, CatBoostTrainer, HuberTrainer, PoissonGLMTrainer,
      RidgeTrainer). Common interface: train(X, y, hyperparams) → model, predict(model, X) → predictions,
      evaluate(model, X, y) → metrics
- [ ] [AGENT] P0. Rename existing `model_trainer.py` ModelTrainer → LightGBMTrainer
- [ ] [AGENT] P0. Create `app/training/ensemble_trainer.py`: EnsembleTrainer — takes EnsembleConfig, iterates over base
      models via factory, combines predictions with configured weights, optionally trains meta-model on base predictions
      (stacking)
- [ ] [AGENT] P0. Create `app/core/uniform_training_pipeline.py`: UniformTrainingPipeline — orchestrates 5+1 phases
      driven by TrainingPipelineConfig. Phase 1 uses existing GlobalFeatureSelector. Phase 2 uses generalized
      HyperparameterTuner. Phase 3 does walk-forward fit_predict. Phase 4-5 optional meta-learning. Phase 6 optional
      cross-pipeline.
- [ ] [AGENT] P0. Add season-based split_strategy to `app/core/walk_forward_validator.py`: split_strategy="date"
      (existing) or "season" (sports). Season-based uses season column, not date ranges.
- [ ] [AGENT] P0. Create `app/core/sports_target_generator.py`: CLVTargetGenerator (closing odds drift),
      XGTargetGenerator (actual goals as regression target), HTDeltaTargetGenerator (FT xG - HT state)
- [ ] [AGENT] P0. Generalize `app/training/hyperparameter_tuning.py` HyperparameterTuner for all model types (not just
      LightGBM)
- [ ] [AGENT] P1. Update `ml/config_schema.py` VALID\_\* lists to mirror UML-interface changes
- [ ] [AGENT] P1. Add tests: 5-phase pipeline with sports mock data, 3-phase financial mock data with explicit
      model_type, ensemble training with 3+ model types, season-based walk-forward
- [ ] [SCRIPT] P0. QG gate: `cd ml-training-service && bash scripts/quality-gates.sh`

### Phase 4: ml-inference-service (T3)

- [ ] [AGENT] P0. Create `app/inference/ensemble_inference.py`: load multiple base models, run each, combine predictions
      with stored weights. Supports both financial (classification) and sports (regression) task types.
- [ ] [AGENT] P0. Add sports inference adapter: takes fixture_id → loads features from FSS GCS outputs → runs ensemble
      base models → optionally runs meta-model → returns BettingSignal (CLV, xG, HT delta predictions)
- [ ] [AGENT] P0. Generalize model loader for multi-model types: joblib for sklearn models (Huber, Ridge, Poisson GLM),
      native loading for LightGBM/XGBoost/CatBoost
- [ ] [AGENT] P1. Add tests for ensemble inference, sports adapter, multi-model-type loading
- [ ] [SCRIPT] P0. QG gate: `cd ml-inference-service && bash scripts/quality-gates.sh`

### Phase 5: Integration Validation

- [ ] [SCRIPT] P0. QG sweep: run quality-gates.sh on all 10 affected repos
- [ ] [AGENT] P0. Integration test: sports 5-phase pipeline end-to-end with mock data (feature selection →
      hyperparameter tuning → base results → meta-learning → meta results)
- [ ] [AGENT] P0. Integration test: financial 3-phase pipeline with existing swing_high/swing_low configs after explicit
      model_type migration
- [ ] [AGENT] P1. Update `unified-trading-pm/configs/sharding.ml-training-service.yaml`: add sports dimensions
      (operation: train_sports_base/train_sports_meta, target_type: clv/xg/ht_delta)
- [ ] [AGENT] P2. Integration test: cross-pipeline stacking (Phase 6 — CLV predictions as features for xG pipeline)

---

## Success Criteria

- Sports training config drives 5-phase pipeline producing CLV/xG/HT models
- Financial training config drives 3-phase pipeline (backward compat) or 5-phase
- Models from any phase loadable and servable by ml-inference-service
- No regressions in existing financial ML tests
- All 10 affected repos pass quality-gates.sh
- SportsMatchingEngine simulates bet placement/settlement for backtesting
- Anti-leakage enforcement active in features-sports-service via UFOL
