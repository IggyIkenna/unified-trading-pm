---
doc_type: plan
title: ml-pipeline-revolution
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: []
related: []
created: '2026-04-14'
remaining_todos_consolidated_into: consolidated_ml_advanced_pipeline_2026_04_15
superseded_by: [consolidated_ml_advanced_pipeline_2026_04_15.md]
reconciliation_status: superseded_by_consolidator
reconciliation_date: 2026-04-25
overview: P&L-aware training, confidence calibration, incremental learning, transfer learning, neural nets, multi-task training, hierarchical models, feature importance feedback, Bayesian optimization
type: code
epic: epic-code-completion
locked_by: live-defi-rollout
locked_since: 2026-04-11
completion_gates: {code: C5, deployment: none, business: B3}
repo_gates:
- {repo: unified-api-contracts, code: C0, deployment: none, business: none}
- {repo: unified-trading-library, code: C0, deployment: none, business: none}
- {repo: ml-training-service, code: C0, deployment: none, business: none}
- {repo: ml-inference-service, code: C0, deployment: none, business: none}
- {repo: strategy-service, code: C0, deployment: none, business: none}
depends_on: []
todos:
- {id: p1-uac-ml-schemas, content: '- [ ] [AGENT] P0. Extend UAC internal ML schemas with calibration, training scope, and cost-aware types

    Add to `unified_api_contracts/internal/domain/ml/schemas.py`:

    - `CalibrationMethod` enum: `ISOTONIC`, `PLATT`, `TEMPERATURE`, `NONE`

    - `CalibrationConfig` model: method, validation_fraction (0.15), store_calibrator (True)

    - `CalibrationResult` model: method, ece_before, ece_after, calibrator_path

    - `TrainingScope` enum: `PER_INSTRUMENT`, `PER_CATEGORY`, `GLOBAL`

    - `TrainingObjective` enum: `CLASSIFICATION`, `REGRESSION`, `PNL_AWARE`, `SHARPE_MAXIMIZING`

    - `IncrementalTrainingConfig` model: warm_start (bool), decay_weight (float), regime_trigger_threshold (float)

    - `FeatureImportanceDrift` model: model_id, feature_name, rank_before, rank_after, importance_before, importance_after

    - Add `calibration_config`, `training_scope`, `training_objective`, `incremental_config` fields to `TrainingPipelineConfig`

    - Add `calibrated_confidence`, `calibration_method` fields to `InferenceResult`

    - Extend `VALID_MODEL_TYPES` in UTL config_schema.py to include `tabnet`, `tft`

    ', status: todo, note: 'PARALLEL with p1-utl-calibration, p1-utl-pnl-objective, p1-utl-bayesian'}
- {id: p1-utl-calibration, content: '- [ ] [AGENT] P0. Build calibration module in UTL ml/calibration.py

    `ProbabilityCalibrator` class:

    - `fit(y_true: ndarray, y_prob: ndarray, method: CalibrationMethod) -> None` — fits isotonic/Platt/temperature

    - `transform(y_prob: ndarray) -> ndarray` — applies calibration

    - `ece(y_true: ndarray, y_prob: ndarray, n_bins: int = 15) -> float` — Expected Calibration Error

    - `reliability_diagram(y_true, y_prob) -> dict` — bin_edges, bin_accs, bin_confs for plotting

    - `save(path: str)` / `load(path: str)` — joblib serialization alongside model artifact

    Implementation: sklearn.calibration.CalibratedClassifierCV (isotonic), sklearn.linear_model.LogisticRegression (Platt), custom temperature scaling

    ', status: todo, note: PARALLEL with p1-uac-ml-schemas}
- {id: p1-utl-pnl-objective, content: '- [ ] [AGENT] P0. Build P&L-aware training objectives in UTL ml/pnl_objectives.py

    Custom loss functions for LightGBM/XGBoost:

    - `pnl_weighted_logloss(y_true, y_pred, trade_cost, expected_pnl)` — asymmetric loss penalizing false positives more when cost > expected alpha

    - `sharpe_feval(y_true, y_pred, returns)` — custom evaluation function maximizing Sharpe ratio of predicted trades

    - `asymmetric_mse(y_true, y_pred, cost_ratio)` — for regression targets, penalize underprediction of costs

    LightGBM integration: return `(grad, hess)` tuple for custom objective, `(metric_name, value, is_higher_better)` for feval

    XGBoost integration: same interface via `obj` and `feval` params

    ', status: todo, note: PARALLEL with p1-utl-calibration}
- {id: p1-utl-bayesian, content: '- [ ] [AGENT] P1. Build Bayesian optimization wrapper in UTL ml/bayesian_optimizer.py

    `BayesianHyperparamOptimizer`:

    - Wraps optuna (already in TrainingPipelineConfig.tuning_method)

    - `optimize(objective_fn, param_space: dict, n_trials: int, timeout: int) -> dict` — returns best params

    - `param_space_from_model_type(model_type: ModelType) -> dict` — default search spaces per model type

    - Pruning: optuna.pruners.MedianPruner for early stopping of bad trials

    - Storage: optuna.storages.RDBStorage or in-memory for CI

    - Walk-forward-aware: objective_fn receives train/val splits, not random splits

    ', status: todo, note: PARALLEL with p1-utl-pnl-objective}
- {id: p1-utl-feature-importance, content: '- [ ] [AGENT] P1. Build feature importance monitor in UTL ml/feature_importance_monitor.py

    `FeatureImportanceMonitor`:

    - `compute_shap(model, X: DataFrame, sample_size: int = 1000) -> DataFrame` — SHAP values per feature

    - `compute_drift(current_importances: dict, baseline_importances: dict) -> list[FeatureImportanceDrift]` — rank/value changes

    - `flag_deprecated(importances: dict, threshold: float = 0.001, n_consecutive: int = 3) -> list[str]` — features consistently below threshold

    - `top_k_features(importances: dict, k: int = 20) -> list[str]`

    - Store importance history in GCS for tracking across retrains

    ', status: todo, note: PARALLEL with p1-utl-bayesian}
- {id: p1-qg, content: '- [ ] [AGENT] P0. Run quality-gates.sh on UAC, UTL — all pass

    ', status: todo, note: SEQUENTIAL — gate before Phase 2}
- {id: p2-calibration-integration, content: '- [ ] [AGENT] P0. Wire calibration into uniform_training_pipeline.py Phase 3

    After base model training in `_phase_base_results()`:

    1. Split validation fold into calibration/test (using config.calibration_config.validation_fraction)

    2. Fit ProbabilityCalibrator on calibration split

    3. Transform test predictions with calibrator

    4. Compute ECE before/after, add to PhaseResult.metrics

    5. Save calibrator alongside model artifact in GCS (model.joblib + calibrator.joblib)

    6. Add CalibrationResult to PhaseResult

    ', status: todo, note: 'PARALLEL with p2-pnl-training, p2-bayesian-tuning, p2-incremental'}
- {id: p2-pnl-training, content: '- [ ] [AGENT] P0. Wire P&L-aware objectives into model_trainer_factory.py

    In `get_trainer()`:

    - If `training_objective == PNL_AWARE`: pass custom loss function to LightGBM/XGBoost via `objective` param

    - If `training_objective == SHARPE_MAXIMIZING`: pass sharpe_feval as `feval` param

    - Requires trade cost data: extend `CloudFeatureProvider` to load spread/fee data alongside features

    - Add `trade_cost_column` and `expected_pnl_column` to TrainingPipelineConfig for cost-aware training

    ', status: todo, note: PARALLEL with p2-calibration-integration}
- {id: p2-bayesian-tuning, content: '- [ ] [AGENT] P1. Replace grid search with Bayesian optimization in Phase 2

    In `_phase_hyperparameter_tuning()`:

    - If `config.tuning_method == "optuna"` (already default): use BayesianHyperparamOptimizer

    - Walk-forward objective: each trial runs walk-forward CV, returns mean validation metric

    - Pruning: stop trials that perform worse than median after 2 folds

    - Keep grid search as fallback (`tuning_method == "grid"`)

    - Update hyperparam_grid_handler.py to use Bayesian path

    ', status: todo, note: PARALLEL with p2-calibration-integration}
- {id: p2-incremental, content: '- [ ] [AGENT] P1. Add incremental training mode to uniform_training_pipeline.py

    New method `_run_incremental()`:

    - Load previous model from GCS via model_registry

    - Use LightGBM `init_model` / XGBoost `xgb_model` for warm-starting

    - Apply exponential decay weighting to training data (recent data weighted higher)

    - Validate incrementally-trained model against same thresholds

    - If validation passes, save as new version; if fails, trigger full retrain

    - Add `IncrementalTrainingConfig` to pipeline config

    ', status: todo, note: PARALLEL with p2-bayesian-tuning}
- {id: p2-transfer-learning, content: '- [ ] [AGENT] P1. Add global/cross-asset training scope to pipeline

    In uniform_training_pipeline.py:

    - If `training_scope == GLOBAL`: load features for ALL instruments in category, encode instrument_id as categorical

    - If `training_scope == PER_CATEGORY`: load all instruments in category, no instrument encoding (shared model)

    - CloudFeatureProvider.load_all_instruments(category) — new method loading from all instrument subdirs

    - Feature validation: ensure all instruments have same feature columns (union with NaN fill for missing)

    - Model ID format for global: `{CATEGORY}_GLOBAL_{target}_{model_type}_{TF}_V{N}`

    ', status: todo, note: PARALLEL with p2-incremental}
- {id: p2-multi-task, content: '- [ ] [AGENT] P1. Add multi-target joint training option

    New `MultiTaskTrainer` in ml-training-service/app/training/:

    - Trains single model predicting multiple targets simultaneously (swing_high + swing_low + direction)

    - LightGBM: train separate models sharing same feature selection (cheaper version)

    - For true MTL: use shared feature backbone + separate output heads (requires neural trainer)

    - Config: `multi_target: list[TargetType]` in TrainingPipelineConfig

    - Output: one model artifact per target, shared feature set

    ', status: todo, note: PARALLEL with p2-transfer-learning}
- {id: p2-feature-importance-feedback, content: '- [ ] [AGENT] P1. Wire feature importance monitor into Phase 3 post-training

    After `_phase_base_results()`:

    1. Compute SHAP values using FeatureImportanceMonitor.compute_shap()

    2. Compare against baseline importances from previous training run

    3. Flag drifted features (rank change > 30%)

    4. Flag deprecated features (importance < 0.001 for 3+ consecutive runs)

    5. Store importance history to GCS: `gs://models/{model_id}/importance_history/{training_period}.json`

    6. Emit MODEL_FEATURE_DRIFT event if drift detected

    ', status: todo, note: PARALLEL with p2-multi-task}
- {id: p2-qg, content: '- [ ] [AGENT] P0. Run quality-gates.sh on ml-training-service — pass

    ', status: todo, note: SEQUENTIAL — gate before Phase 3}
- {id: p3-calibration-inference, content: '- [ ] [AGENT] P0. Apply calibration at inference time in ml-inference-service

    In `engine/model_loader.py`:

    - Load calibrator.joblib alongside model.joblib from GCS

    - Cache calibrator in memory alongside model

    In `engine/orchestrator.py`:

    - After `model.predict_proba()`, apply `calibrator.transform()` if calibrator exists

    - Set `InferenceResult.calibrated_confidence` and `calibration_method`

    - Fallback: if no calibrator, use raw predict_proba (backwards compatible)

    ', status: todo, note: 'PARALLEL with p3-shap-inference, p3-hierarchical'}
- {id: p3-shap-inference, content: '- [ ] [AGENT] P1. Add optional SHAP explanation to inference responses

    In `engine/orchestrator.py`:

    - If `InferenceRequest.explain == True`: compute SHAP for this prediction

    - Return top 10 feature contributions in `InferenceResult.feature_importance`

    - Use TreeExplainer for tree models (fast, O(TLD) per prediction)

    - Cache explainer alongside model (compute once, reuse)

    - Add `explain: bool = False` to InferenceRequest schema in UAC

    ', status: todo, note: PARALLEL with p3-calibration-inference}
- {id: p3-hierarchical, content: '- [ ] [AGENT] P1. Support hierarchical model loading (Level 0-2)

    In `engine/model_loader.py`:

    - Level 0: validity/quality model (from feature validity engine — already exists)

    - Level 1: per-domain base model (current behavior)

    - Level 2: cross-domain meta-model (loads predictions from Level 1 models as features)

    - Add `model_hierarchy_level: int = 1` to InferenceRequest

    - For Level 2: orchestrator calls Level 1 for all subscribed models, feeds to Level 2 model

    - Level 3 (portfolio allocation) is strategy-service concern, not inference

    ', status: todo, note: PARALLEL with p3-shap-inference}
- {id: p3-qg, content: '- [ ] [AGENT] P0. Run quality-gates.sh on ml-inference-service — pass

    ', status: todo, note: SEQUENTIAL — gate before Phase 4}
- {id: p4-strategy-calibrated-signals, content: '- [ ] [AGENT] P0. Update strategy-service to consume calibrated confidences

    In strategy engines that use ML signals:

    - Read `calibrated_confidence` from InferenceResult (fall back to `confidence` if missing)

    - Kelly sizing: use calibrated probability for edge calculation: `edge = calibrated_p * odds - 1`

    - Add minimum calibration quality gate: if `ece > 0.1`, attenuate position size by 50%

    - Log calibration method alongside signal for attribution

    ', status: todo, note: PARALLEL with p4-cost-aware-strategy}
- {id: p4-cost-aware-strategy, content: '- [ ] [AGENT] P1. Add cost-aware signal filtering in strategy-service

    Before generating execution instruction:

    - Estimate trade cost: spread + commission + slippage estimate (from execution-service health API)

    - Compare expected alpha (from ML signal confidence * historical edge) vs estimated cost

    - If cost > alpha * cost_threshold_ratio (default 0.5): skip trade, emit TRADE_COST_FILTERED event

    - Add `cost_threshold_ratio` to strategy config

    ', status: todo, note: PARALLEL with p4-strategy-calibrated-signals}
- {id: p4-qg, content: '- [ ] [AGENT] P0. Run quality-gates.sh on strategy-service — pass

    ', status: todo, note: SEQUENTIAL — gate before Phase 5}
- {id: p5-final-qg, content: '- [ ] [AGENT] P0. Final QG on all repos: UAC, UTL, ml-training-service, ml-inference-service, strategy-service

    ', status: todo, note: SEQUENTIAL — final validation}
isProject: false
---

> **SUPERSEDED 2026-04-25 by
> [consolidated_ml_advanced_pipeline_2026_04_15.md](./consolidated_ml_advanced_pipeline_2026_04_15.md).** Original scope
> retained for history. Frontmatter `remaining_todos_consolidated_into:` was already present; this commit formalises it
> as canonical `superseded_by:` and adds this banner. See `_reconciliation_evidence_map_2026_04_25.md` for evidence.

# ML Pipeline Revolution

## Context

The current ML pipeline is production-grade for tree-based swing classification but lacks key capabilities that
institutional quant systems use to generate more money. This plan addresses the 9 highest-impact deltas identified in
the 2026-04-11 delta analysis.

### Execution DAG

```
Phase 1 (PARALLEL) ─────────────────────────────────────────
  ├── [UAC] ML schema extensions (calibration, scope, objectives)
  ├── [UTL] ProbabilityCalibrator
  ├── [UTL] P&L-aware objectives
  ├── [UTL] BayesianHyperparamOptimizer
  └── [UTL] FeatureImportanceMonitor
          │
       QG Gate (UAC + UTL)
          │
Phase 2 (PARALLEL within, SEQUENTIAL after P1) ─────────────
  ├── [ml-training] Wire calibration into Phase 3
  ├── [ml-training] Wire P&L-aware objectives
  ├── [ml-training] Replace grid search with Bayesian
  ├── [ml-training] Add incremental training mode
  ├── [ml-training] Add global/cross-asset training scope
  ├── [ml-training] Add multi-target joint training
  └── [ml-training] Wire feature importance feedback
          │
       QG Gate (ml-training-service)
          │
Phase 3 (PARALLEL within, SEQUENTIAL after P2) ─────────────
  ├── [ml-inference] Apply calibration at inference
  ├── [ml-inference] SHAP explanation support
  └── [ml-inference] Hierarchical model loading
          │
       QG Gate (ml-inference-service)
          │
Phase 4 (PARALLEL within, SEQUENTIAL after P3) ─────────────
  ├── [strategy] Consume calibrated confidences + Kelly fix
  └── [strategy] Cost-aware signal filtering
          │
       QG Gate (strategy-service)
          │
Phase 5 (SEQUENTIAL) ───────────────────────────────────────
  └── Final QG on all 5 repos
```

### Pre-Audit Manifest

| Repo         | File                                  | Symbol                        | Action                                                                                |
| ------------ | ------------------------------------- | ----------------------------- | ------------------------------------------------------------------------------------- |
| UAC          | internal/domain/ml/schemas.py         | TrainingPipelineConfig        | Add calibration_config, training_scope, training_objective, incremental_config fields |
| UAC          | internal/domain/ml/schemas.py         | InferenceResult               | Add calibrated_confidence, calibration_method fields                                  |
| UAC          | internal/domain/ml/schemas.py         | InferenceRequest              | Add explain field                                                                     |
| UTL          | ml/config_schema.py                   | VALID_MODEL_TYPES             | Add tabnet, tft                                                                       |
| UTL          | ml/**init**.py                        | -                             | Export new modules                                                                    |
| ml-training  | app/core/uniform_training_pipeline.py | \_phase_base_results          | Add calibration step                                                                  |
| ml-training  | app/core/uniform_training_pipeline.py | \_phase_hyperparameter_tuning | Bayesian path                                                                         |
| ml-training  | app/training/model_trainer_factory.py | get_trainer                   | P&L-aware objective injection                                                         |
| ml-inference | engine/model_loader.py                | ModelLoader                   | Load calibrator alongside model                                                       |
| ml-inference | engine/orchestrator.py                | InferenceOrchestrator         | Apply calibration, SHAP                                                               |
| strategy     | engine/strategies/\*/                 | BaseStrategy subclasses       | Use calibrated_confidence                                                             |

### Success Criteria

- **Code:** quality-gates.sh passes on all 5 repos, basedpyright clean
- **Test:** Calibration ECE < 0.05 on test data; Bayesian finds better params than grid in fewer trials; incremental
  model within 5% of full retrain accuracy
- **Business (B3):** Kelly sizing with calibrated probabilities improves simulated Sharpe by >10%; P&L-aware training
  reduces false-positive trades by >15%; cost-aware filtering eliminates negative-EV trades
