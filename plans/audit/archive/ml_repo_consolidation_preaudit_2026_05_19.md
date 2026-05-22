---
title: "ml-service repo consolidation — Phase 0 pre-audit manifest"
created: 2026-05-19
author: slot-1 sub-agent (read-only audit)
source:
  - plans/active/ml_repo_consolidation_2026_05_19.md (Phase 0 todo: phase-0-pre-audit-manifest)
  - ml-training-service @ live-defi-rollout (workspace .tabs/1)
  - ml-inference-service @ live-defi-rollout (workspace .tabs/1)
locked_by: live-defi-rollout
---

> **🟡 COVERED BY** [../ml_repo_consolidation_2026_05_19.md](../ml_repo_consolidation_2026_05_19.md) — this is the Phase
> 0 pre-audit diagnostic artefact for the named consolidation plan (slot-1 triage 2026-05-20). Stays in issues/ until
> parent closes, then archives with it. Note: future Phase-0 artefacts should land in `plans/audit/`, mirroring the
> mega-audit's C-audit location convention.

> **Scope**: read-only artifact driving every later phase of `ml_repo_consolidation_2026_05_19.md`. This file enumerates
> per source repo (`ml-training-service`, `ml-inference-service`) the full module / consumer / dependency surface that
> the subtree-merge into the NEW `ml-service` repo will touch.

> **TL;DR for orchestrator**:
>
> - **(b) external Python imports of source packages: 0 hits**. Workspace-wide grep verified. Subtree-merge has no
>   external import-rewrite blast radius.
> - **(g) dependency union: 35 unique distribution names**. Training-only-heavy stack
>   (sklearn/xgboost/lightgbm/catboost/optuna/shap/ta-lib/matplotlib/joblib/boto3/pyarrow/db-dtypes) drives ~70% of the
>   ml-training image weight. Inference-only stack is leaner — sse-starlette + onnxruntime + opentelemetry. Optional-dep
>   `[project.optional-dependencies] training = [...]` split is REQUIRED (per plan Phase 4 (h)) to keep live-inference
>   Docker image lean. Estimated inference-only baseline: ~16 runtime deps vs union 35 → roughly 55-60% smaller.
> - **(h) topic-name constants are shared between training (publisher) and inference (subscriber)** —
>   `ML_MODEL_COORDINATION_TOPIC` (= `"ml_model_coordination_events"`) is defined as a STRING LITERAL in BOTH repos and
>   ALSO in `ml_training_service/cli/handlers/__init__.py`. **NO rename needed** (the topic-name is a wire-protocol
>   constant, not a service-name); both publishers and subscribers can keep the same literal post-consolidation.
> - **(f) `config_reloaders.py` files are NEAR-IDENTICAL between the two repos** (verified via `diff -u` — modulo
>   `Settings` vs `InferenceConfig` typing). Prime UTL lift candidate per plan Phase 5.

---

## (a) Per-source-repo module / class / function inventory + post-merge sub-package landing

Source-package roots:

- `ml-training-service/ml_training_service/` → `ml-service/ml_service/training/`
- `ml-inference-service/ml_inference_service/` → `ml-service/ml_service/inference/`

### ml-training-service → `ml_service/training/`

| Module path (current)                                               | Post-merge path                                                                | Public classes / functions                                                                                                                                                                                                                                                                                                                                                                                                                         |
| ------------------------------------------------------------------- | ------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ml_training_service/__init__.py`                                   | `ml_service/training/__init__.py`                                              | Re-exports: `Settings`, `TrainingConfig`, `get_settings`, `ModelVariantConfig`, `TrainingData`, `ModelMetadata`, `FeatureSelectionResult`, `HyperparameterConfig`                                                                                                                                                                                                                                                                                  |
| `ml_training_service/__main__.py`                                   | `ml_service/training/__main__.py`                                              | `python -m ml_service.training` entry (collapses to single `python -m ml_service --operation train` post Phase 4)                                                                                                                                                                                                                                                                                                                                  |
| `ml_training_service/config.py`                                     | `ml_service/training/config.py` (or merged into `ml_service/common/config.py`) | `Settings(MLTrainingConfig)`, `TrainingConfig`, `get_settings()`, `update_settings()`                                                                                                                                                                                                                                                                                                                                                              |
| `ml_training_service/config_reloaders.py`                           | merged into `ml_service/common/config_reloaders.py`                            | `get_active_instruments()`, `get_active_venues()`, `_on_instruments_reload()`, `_on_venues_reload()`, `start_domain_config_reloaders()`, `stop_domain_config_reloaders()` — **DUPLICATED in inference**; lift candidate                                                                                                                                                                                                                            |
| `ml_training_service/auth_s2s.py`                                   | `ml_service/common/auth_s2s.py`                                                | `verify_service_token` (uses `create_s2s_auth_dependency("ml-training-service")` — rename to `"ml-service"` post-merge)                                                                                                                                                                                                                                                                                                                            |
| `ml_training_service/metrics.py`                                    | `ml_service/training/metrics.py`                                               | Prometheus counters — namespace `ml_training_service_*` (rename post-merge)                                                                                                                                                                                                                                                                                                                                                                        |
| `ml_training_service/adapters/feature_data_adapter.py`              | `ml_service/training/adapters/feature_data_adapter.py`                         | `FeatureDataAdapter`                                                                                                                                                                                                                                                                                                                                                                                                                               |
| `ml_training_service/api/main.py`                                   | merged into `ml_service/api/main.py`                                           | `set_last_training_date()`, `_data_freshness()`, `create_app()` (FastAPI app + `make_health_router` from UTL)                                                                                                                                                                                                                                                                                                                                      |
| `ml_training_service/api/training_control_api.py`                   | `ml_service/training/api/training_control_api.py`                              | `_apply_action()`, `_persist_audit_log()`, `get_audit_log()`, `get_archetype_status()`, `control_training()`                                                                                                                                                                                                                                                                                                                                       |
| `ml_training_service/app/core/cloud_feature_provider.py`            | `ml_service/training/app/core/cloud_feature_provider.py`                       | `CloudFeatureProvider`, `_build_features_table_name()`, etc. — **TRAINING+INFERENCE both have a cloud feature provider; potential lift**                                                                                                                                                                                                                                                                                                           |
| `ml_training_service/app/core/config_loader.py`                     | `ml_service/training/app/core/config_loader.py`                                | `TrainingGridConfig`, `ConfigLoader`                                                                                                                                                                                                                                                                                                                                                                                                               |
| `ml_training_service/app/core/cross_asset_training_pipeline.py`     | `ml_service/training/app/core/cross_asset_training_pipeline.py`                | `PerAssetEvaluation`, `CrossAssetResult`, `CrossAssetTrainingPipeline`                                                                                                                                                                                                                                                                                                                                                                             |
| `ml_training_service/app/core/cross_venue_spread.py`                | `ml_service/training/app/core/cross_venue_spread.py`                           | `compute_cross_venue_spread_target()`                                                                                                                                                                                                                                                                                                                                                                                                              |
| `ml_training_service/app/core/data_filters.py`                      | `ml_service/training/app/core/data_filters.py`                                 | `filter_market_hours()` + helpers                                                                                                                                                                                                                                                                                                                                                                                                                  |
| `ml_training_service/app/core/defi_target_generator.py`             | `ml_service/training/app/core/defi_target_generator.py`                        | `FundingRateTargetBuilder`, `LendingRateTargetBuilder`, `ImpermanentLossTargetBuilder`                                                                                                                                                                                                                                                                                                                                                             |
| `ml_training_service/app/core/dependency_checker.py`                | `ml_service/training/app/core/dependency_checker.py`                           | `DependencyChecker(BaseDependencyChecker)`, `check_dependencies()` — **duplicated in inference (different class body)**                                                                                                                                                                                                                                                                                                                            |
| `ml_training_service/app/core/family_router.py`                     | `ml_service/training/app/core/family_router.py`                                | `FamilyRouter`, `get_family_router()`, `_build_sports_router()`, `_build_tradfi_router()`                                                                                                                                                                                                                                                                                                                                                          |
| `ml_training_service/app/core/feature_selector.py`                  | `ml_service/training/app/core/feature_selector.py`                             | `FeatureSelector`                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| `ml_training_service/app/core/feature_validator.py`                 | `ml_service/training/app/core/feature_validator.py`                            | `FeatureValidator`, `_HaltValidationResult`, `_FeatureValidationResult`                                                                                                                                                                                                                                                                                                                                                                            |
| `ml_training_service/app/core/gcs_feature_reader.py`                | `ml_service/training/app/core/gcs_feature_reader.py`                           | `ParallelGCSFeatureReader`, `_peek_parquet_column_names()`                                                                                                                                                                                                                                                                                                                                                                                         |
| `ml_training_service/app/core/global_feature_selector.py`           | `ml_service/training/app/core/global_feature_selector.py`                      | `GlobalFeatureSelector`                                                                                                                                                                                                                                                                                                                                                                                                                            |
| `ml_training_service/app/core/instrument_utils.py`                  | `ml_service/training/app/core/instrument_utils.py`                             | `InstrumentKey`, `parse_instrument_id()`, `validate_instrument_id()`, `extract_base_asset()`, `extract_symbol_simple()`, `build_instrument_id()`, `get_available_instrument_ids_from_features()`, `_CloudServiceProtocol`                                                                                                                                                                                                                          |
| `ml_training_service/app/core/manifest_gap_handler.py`              | `ml_service/training/app/core/manifest_gap_handler.py`                         | `apply_manifest_quality_flags()` + helpers                                                                                                                                                                                                                                                                                                                                                                                                         |
| `ml_training_service/app/core/mock_feature_generator.py`            | `ml_service/training/app/core/mock_feature_generator.py`                       | `MockFeatureGenerator`, `get_feature_columns()`, `get_target_column()`, `get_swing_mask_column()`, `generate_mock_training_data()`                                                                                                                                                                                                                                                                                                                 |
| `ml_training_service/app/core/mock_feature_provider.py`             | `ml_service/training/app/core/mock_feature_provider.py`                        | `MockFeatureProvider`                                                                                                                                                                                                                                                                                                                                                                                                                              |
| `ml_training_service/app/core/sports_model_config.py`               | `ml_service/training/app/core/sports_model_config.py`                          | `SportsModelSpec`                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| `ml_training_service/app/core/sports_target_generator.py`           | `ml_service/training/app/core/sports_target_generator.py`                      | `XGTargetBuilder`, `CLVTargetBuilder`, `HTXGTargetBuilder`, `HTCLVTargetBuilder`, `MetaTargetBuilder`, `SportsTargetOrchestrator`, `CLVTargetGenerator`, `XGTargetGenerator`, `HTDeltaTargetGenerator`, `strip_target_leakage()`                                                                                                                                                                                                                   |
| `ml_training_service/app/core/target_generator.py`                  | `ml_service/training/app/core/target_generator.py`                             | `TargetGenerator`                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| `ml_training_service/app/core/target_generator_factory.py`          | `ml_service/training/app/core/target_generator_factory.py`                     | `get_target_generator()`, `get_sports_target_orchestrator()`, `build_defi_targets()`                                                                                                                                                                                                                                                                                                                                                               |
| `ml_training_service/app/core/training_orchestrator.py`             | `ml_service/training/app/core/training_orchestrator.py`                        | `TrainingOrchestrator`, `_create_training_script()`, `_reap_completed_processes()`, `_combine_enhanced_metrics()`, `_ActiveProcessEntry`                                                                                                                                                                                                                                                                                                           |
| `ml_training_service/app/core/uniform_training_pipeline.py`         | `ml_service/training/app/core/uniform_training_pipeline.py`                    | `UniformTrainingPipeline`, `PhaseResult`, `IncrementalResult`, `PipelineResult`, `_HyperparamsWithCustomFns`                                                                                                                                                                                                                                                                                                                                       |
| `ml_training_service/app/core/validation_service.py`                | `ml_service/training/app/core/validation_service.py`                           | `MLValidationService`, `create_ml_validation_service()`                                                                                                                                                                                                                                                                                                                                                                                            |
| `ml_training_service/app/core/walk_forward_validator.py`            | `ml_service/training/app/core/walk_forward_validator.py`                       | `WalkForwardValidator`, `WalkForwardFold`, `create_walk_forward_splits()`                                                                                                                                                                                                                                                                                                                                                                          |
| `ml_training_service/app/training/cascade_meta_model_trainer.py`    | `ml_service/training/app/training/cascade_meta_model_trainer.py`               | `CascadeMetaModelTrainer`                                                                                                                                                                                                                                                                                                                                                                                                                          |
| `ml_training_service/app/training/data_preparation.py`              | `ml_service/training/app/training/data_preparation.py`                         | `DataPreparation`                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| `ml_training_service/app/training/ensemble_trainer.py`              | `ml_service/training/app/training/ensemble_trainer.py`                         | `EnsembleTrainer`, `EnsembleResult`                                                                                                                                                                                                                                                                                                                                                                                                                |
| `ml_training_service/app/training/hyperparameter_tuning.py`         | `ml_service/training/app/training/hyperparameter_tuning.py`                    | `HyperparameterTuner`, `get_search_space()`, `_build_hyperparams()`                                                                                                                                                                                                                                                                                                                                                                                |
| `ml_training_service/app/training/leverage_distribution_trainer.py` | `ml_service/training/app/training/leverage_distribution_trainer.py`            | `LeverageDistributionTrainer`, `WalkForwardConfig`, `CalibrationMetrics`, `TrainingResult`                                                                                                                                                                                                                                                                                                                                                         |
| `ml_training_service/app/training/model_trainer.py`                 | `ml_service/training/app/training/model_trainer.py`                            | `ModelTrainer`                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| `ml_training_service/app/training/model_trainer_factory.py`         | `ml_service/training/app/training/model_trainer_factory.py`                    | `LightGBMTrainer`, `SklearnTrainer`, `XGBoostTrainer`, `CatBoostTrainer`, `BaseTrainerProtocol`, `TrainResult`, `get_trainer()`                                                                                                                                                                                                                                                                                                                    |
| `ml_training_service/app/training/regime_conditional_trainer.py`    | `ml_service/training/app/training/regime_conditional_trainer.py`               | `train_regime_conditional_models()`, `has_regime_columns()`, `_get_regime_mask()`                                                                                                                                                                                                                                                                                                                                                                  |
| `ml_training_service/app/training/shap_explainer.py`                | `ml_service/training/app/training/shap_explainer.py`                           | `ShapExplainer`                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| `ml_training_service/app/training/signal_vector_meta_trainer.py`    | `ml_service/training/app/training/signal_vector_meta_trainer.py`               | `SignalVectorMetaModelTrainer`, `MetaModelResult`, `MetaFeatureOrthogonalityChecker`                                                                                                                                                                                                                                                                                                                                                               |
| `ml_training_service/app/training/sports_ensemble_trainer.py`       | `ml_service/training/app/training/sports_ensemble_trainer.py`                  | `SportsModel2ATrainer`, `SportsModel2AResult`, `_build_model_2a_ensemble_config()`                                                                                                                                                                                                                                                                                                                                                                 |
| `ml_training_service/backtest_v2/walk_forward.py`                   | `ml_service/training/backtest_v2/walk_forward.py`                              | `PurgedWalkForwardSplit`, `PurgedWalkForwardSplitter`, `build_default_splitter()`                                                                                                                                                                                                                                                                                                                                                                  |
| `ml_training_service/backtest_v2/model_artifact.py`                 | `ml_service/training/backtest_v2/model_artifact.py`                            | `CalibrationCurvePoint`, `HeldOutMetrics`, `ModelArtifactMetadata`                                                                                                                                                                                                                                                                                                                                                                                 |
| `ml_training_service/backtest_v2/artifact_naming.py`                | `ml_service/training/backtest_v2/artifact_naming.py`                           | `ModelFamily(StrEnum)`, `ParsedArtifactRef`, `build_model_artifact_ref()`, `parse_model_artifact_ref()`                                                                                                                                                                                                                                                                                                                                            |
| `ml_training_service/backtest_v2/runner.py`                         | `ml_service/training/backtest_v2/runner.py`                                    | `GroupARunner`, `GroupATrainingResult`, `_FoldFitResult`, `_aggregate_fold_metrics()`                                                                                                                                                                                                                                                                                                                                                              |
| `ml_training_service/cli/main.py`                                   | merged into `ml_service/cli/main.py`                                           | `main()`, `run_cli()`, `_add_ml_training_args()`, `_get_mock_pipeline()`, `get_earliest_valid_ml_date()`                                                                                                                                                                                                                                                                                                                                           |
| `ml_training_service/cli/parser.py`                                 | `ml_service/training/cli/parser.py` (shared CLI under `ml_service/cli/`)       | `create_parser()`, `validate_args()`, `resolve_instruments()`, `resolve_target_types()` + 11 helpers                                                                                                                                                                                                                                                                                                                                               |
| `ml_training_service/cli/handlers/__init__.py`                      | `ml_service/training/cli/handlers/__init__.py`                                 | `get_handler_for_mode()`, `_emit_model_trained_event()` (publishes MODEL_TRAINED to `ml_model_coordination_events` topic), `TrainModeHandler`, `EvaluateModeHandler`, `GridSearchModeHandler`, `PreSelectionModeHandler`, `HyperparamGridModeHandler`, `FinalTrainingModeHandler`, `PipelineModeHandler`, `_MLTrainingModeHandler`, `_generate_experiment_id()`, `_validate_startup()`, `_write_experiment_metrics()`, `_print_training_summary()` |
| `ml_training_service/cli/handlers/base_handler.py`                  | `ml_service/training/cli/handlers/base_handler.py`                             | `BaseHandler` (ABC), `HandlerResult`                                                                                                                                                                                                                                                                                                                                                                                                               |
| `ml_training_service/cli/handlers/pipeline_handler.py`              | `ml_service/training/cli/handlers/pipeline_handler.py`                         | `PipelineHandler(BaseHandler)`                                                                                                                                                                                                                                                                                                                                                                                                                     |
| `ml_training_service/cli/handlers/evaluate_handler.py`              | `ml_service/training/cli/handlers/evaluate_handler.py`                         | `EvaluateHandler(BaseHandler)`                                                                                                                                                                                                                                                                                                                                                                                                                     |
| `ml_training_service/cli/handlers/grid_search_handler.py`           | `ml_service/training/cli/handlers/grid_search_handler.py`                      | `GridSearchHandler(BaseHandler)`                                                                                                                                                                                                                                                                                                                                                                                                                   |
| `ml_training_service/cli/handlers/hyperparam_grid_handler.py`       | `ml_service/training/cli/handlers/hyperparam_grid_handler.py`                  | `HyperparamGridHandler(BaseHandler)`, `_GridResult(TypedDict)`                                                                                                                                                                                                                                                                                                                                                                                     |
| `ml_training_service/cli/handlers/preselection_handler.py`          | `ml_service/training/cli/handlers/preselection_handler.py`                     | `PreSelectionHandler(BaseHandler)`                                                                                                                                                                                                                                                                                                                                                                                                                 |
| `ml_training_service/cli/handlers/train_handler.py`                 | `ml_service/training/cli/handlers/train_handler.py`                            | `TrainHandler(BaseHandler)`                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `ml_training_service/cli/handlers/final_training_handler.py`        | `ml_service/training/cli/handlers/final_training_handler.py`                   | `FinalTrainingHandler(BaseHandler)`                                                                                                                                                                                                                                                                                                                                                                                                                |
| `ml_training_service/engine/orchestrator.py`                        | `ml_service/training/engine/orchestrator.py`                                   | `TrainingEngine`                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| `ml_training_service/engine/mock_data_provider.py`                  | `ml_service/training/engine/mock_data_provider.py`                             | `run_mock_pipeline()` (defines `SERVICE_NAME = "ml-training-service"` — rename to `"ml-service"`)                                                                                                                                                                                                                                                                                                                                                  |
| `ml_training_service/engine/validation/dependency_checker.py`       | `ml_service/training/engine/validation/dependency_checker.py`                  | (per-engine validator)                                                                                                                                                                                                                                                                                                                                                                                                                             |
| `ml_training_service/ml/model_registry.py`                          | `ml_service/training/ml/model_registry.py`                                     | `ModelRegistry`, `StorableModel(Protocol)`, `PredictableModel(Protocol)`, `_ManifestVersionEntry`, `_ManifestModelEntry`, `_ManifestDict`, `_check_emission_policy()`, `_get_cloud_config()`, `_safe_joblib_load()`, `_build_version_entry()`, `_period_to_date()` — **lift candidate: see Phase 5; same model registry concept appears in inference via `ModelLoader`**                                                                           |
| `ml_training_service/ml/config_schema.py`                           | `ml_service/training/ml/config_schema.py`                                      | `validate_ml_config()`, `generate_model_id()`, `parse_model_id()`, `_validate_enum_fields()`, `_validate_model_id_format()`, `_validate_training_period()`                                                                                                                                                                                                                                                                                         |
| `ml_training_service/ml/models.py`                                  | `ml_service/training/ml/models.py`                                             | `ModelVariantConfig`, `TrainingData`, `ModelMetadata`, `FeatureSelectionResult`, `HyperparameterConfig` (re-exports from `__init__`)                                                                                                                                                                                                                                                                                                               |

### ml-inference-service → `ml_service/inference/`

| Module path (current)                                           | Post-merge path                                                                                                                                      | Public classes / functions                                                                                                                                                                                           |
| --------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ml_inference_service/__init__.py`                              | `ml_service/inference/__init__.py`                                                                                                                   | `__version__ = "0.1.0"` only                                                                                                                                                                                         |
| `ml_inference_service/__main__.py`                              | `ml_service/inference/__main__.py`                                                                                                                   | re-exports `run_cli`                                                                                                                                                                                                 |
| `ml_inference_service/config.py`                                | `ml_service/inference/config.py` (or merged into `ml_service/common/config.py`)                                                                      | `InferenceConfig(UnifiedCloudConfig)`, `get_config()`, `update_config()`                                                                                                                                             |
| `ml_inference_service/config_reloaders.py`                      | merged into `ml_service/common/config_reloaders.py` (NEAR-IDENTICAL to training; lift candidate)                                                     | same six callables as training                                                                                                                                                                                       |
| `ml_inference_service/auth_s2s.py`                              | merged into `ml_service/common/auth_s2s.py`                                                                                                          | `verify_service_token = create_s2s_auth_dependency("ml-inference-service")` — rename to `"ml-service"`                                                                                                               |
| `ml_inference_service/metrics.py`                               | `ml_service/inference/metrics.py`                                                                                                                    | Prometheus counters — `ml_inference_service_records_processed_total`, `ml_inference_service_processing_latency_seconds` (rename namespace)                                                                           |
| `ml_inference_service/types.py`                                 | `ml_service/inference/types.py` (consider lifting `PredictionEventDict` / `PredictionMetadata` / `FeatureVector` / `ModelMetadata` to UAC — see (e)) | `PredictionEventDict`, `PredictionMetadata`, `CliHandlerConfig`, `InferenceResultDict`, `FeatureVector`, `ModelMetadata`, `InferenceConfiguration`, `CatalogReportDict`, `CLIArgsDict`                               |
| `ml_inference_service/pre_crash_checkpoint.py`                  | `ml_service/common/pre_crash_checkpoint.py` (cross-cutting; lift to UTL candidate)                                                                   | `register_pre_crash_handlers()`, `_checkpoint_and_exit()`, `_build_signal_handler()`, `_memory_watchdog()`                                                                                                           |
| `ml_inference_service/adapters/storage_adapter.py`              | `ml_service/inference/adapters/storage_adapter.py`                                                                                                   | `StorageAdapter`                                                                                                                                                                                                     |
| `ml_inference_service/api/main.py`                              | merged into `ml_service/api/main.py`                                                                                                                 | `set_last_inference_date()`, `_data_freshness()`, `create_app()`                                                                                                                                                     |
| `ml_inference_service/api/prediction_stream.py`                 | `ml_service/inference/api/prediction_stream.py`                                                                                                      | `enqueue_prediction()`, `_prediction_event_generator()`, `make_prediction_sse_router()`                                                                                                                              |
| `ml_inference_service/io/loader.py`                             | `ml_service/inference/io/loader.py`                                                                                                                  | `FeatureSubscriber` (different from `app/core/feature_subscriber.py:FeatureSubscriber` — collision warning)                                                                                                          |
| `ml_inference_service/app/core/feature_subscriber.py`           | `ml_service/inference/app/core/feature_subscriber.py`                                                                                                | `FeatureSubscriber`, `CacheStats(TypedDict)`, `_check_mock_mode()` — **NAME COLLISION with `io/loader.py:FeatureSubscriber`; rename one during merge**                                                               |
| `ml_inference_service/app/core/cascade_prediction_publisher.py` | `ml_service/inference/app/core/cascade_prediction_publisher.py`                                                                                      | `CascadePredictionPublisher`, `_serialize_snapshot()`, `_serialize_cascade_event()`. Defines `CASCADE_TOPIC_NAME = "cascade_predictions"` (matches strategy-service `cascade_subscriber.py`)                         |
| `ml_inference_service/app/core/date_validation.py`              | `ml_service/inference/app/core/date_validation.py`                                                                                                   | `get_earliest_valid_inference_date()`, `should_skip_inference_date()`                                                                                                                                                |
| `ml_inference_service/app/core/dependency_checker.py`           | `ml_service/inference/app/core/dependency_checker.py`                                                                                                | `DependencyChecker(BaseDependencyChecker)` — **duplicated class name from training**                                                                                                                                 |
| `ml_inference_service/app/core/manifest_inference_guard.py`     | `ml_service/inference/app/core/manifest_inference_guard.py`                                                                                          | `check_manifest_for_inference()`, `_filter_to_day()`, `_classify_day_rows()`                                                                                                                                         |
| `ml_inference_service/app/core/model_promotion_subscriber.py`   | `ml_service/inference/app/core/model_promotion_subscriber.py`                                                                                        | `ModelPromotionSubscriber`, `_parse_model_promotion()`. Defines `ML_MODEL_COORDINATION_TOPIC = "ml_model_coordination_events"` — **same literal as training's publisher**                                            |
| `ml_inference_service/app/core/mtf_feature_subscriber.py`       | `ml_service/inference/app/core/mtf_feature_subscriber.py`                                                                                            | `MtfFeatureSubscriber`, `MtfFeatureCache`, `_parse_mtf_payload()`. Defines `MTF_TOPIC_NAMES`                                                                                                                         |
| `ml_inference_service/app/core/prediction_publisher.py`         | `ml_service/inference/app/core/prediction_publisher.py`                                                                                              | `PredictionPublisher`, `_check_emission_policy()`, `_filter_by_emission_policy()`, `_check_mock_mode()`                                                                                                              |
| `ml_inference_service/app/inference/batch_inference.py`         | `ml_service/inference/app/inference/batch_inference.py`                                                                                              | `BatchInferenceHandler`                                                                                                                                                                                              |
| `ml_inference_service/app/inference/cascade_inference.py`       | `ml_service/inference/app/inference/cascade_inference.py`                                                                                            | `CascadeInferenceMode`                                                                                                                                                                                               |
| `ml_inference_service/app/inference/ensemble_inference.py`      | `ml_service/inference/app/inference/ensemble_inference.py`                                                                                           | `EnsembleInferenceEngine`, `EnsembleConfig`, `EnsembleInferenceResult`, `load_ensemble_models()`, `combine_predictions()`, `_ModelRegistry(Protocol)`, `_HasPredict(Protocol)`                                       |
| `ml_inference_service/app/inference/inference_shap.py`          | `ml_service/inference/app/inference/inference_shap.py`                                                                                               | `InferenceTimeSHAPCalculator`, `SHAPResult`, `SHAPFeature`, `_ShapExplainer(Protocol)`                                                                                                                               |
| `ml_inference_service/app/inference/live_inference.py`          | `ml_service/inference/app/inference/live_inference.py`                                                                                               | `LiveInferenceHandler`                                                                                                                                                                                               |
| `ml_inference_service/app/inference/meta_signal_inference.py`   | `ml_service/inference/app/inference/meta_signal_inference.py`                                                                                        | `MetaSignalInferenceEngine`, `_PredictableModel(Protocol)`                                                                                                                                                           |
| `ml_inference_service/app/inference/prediction_cache.py`        | `ml_service/inference/app/inference/prediction_cache.py`                                                                                             | `PredictionCache`                                                                                                                                                                                                    |
| `ml_inference_service/app/inference/sports_adapter.py`          | `ml_service/inference/app/inference/sports_adapter.py`                                                                                               | `SportsInferenceAdapter`, `SportsSignal`, `_SportsFeatureLoader(Protocol)`, `_HasPredict(Protocol)`                                                                                                                  |
| `ml_inference_service/cli/main.py`                              | merged into `ml_service/cli/main.py`                                                                                                                 | `run_cli()`, `_add_inference_args()`, `_get_mock_pipeline()`, `InferHandler(BaseModeHandler)`, `MLInferenceBatchModeHandler(BaseModeHandler)`                                                                        |
| `ml_inference_service/cli/parser.py`                            | `ml_service/inference/cli/parser.py` (shared CLI under `ml_service/cli/`)                                                                            | `resolve_instrument_ids()`, `resolve_target_types()`, `_extract_category()`, `_resolve_shortcuts()`, `_default_instruments_for_category()`                                                                           |
| `ml_inference_service/cli/handlers/__init__.py`                 | `ml_service/inference/cli/handlers/__init__.py`                                                                                                      | `get_handler_for_operation()`, `get_handler_for_mode()`                                                                                                                                                              |
| `ml_inference_service/cli/handlers/batch_handler.py`            | `ml_service/inference/cli/handlers/batch_handler.py`                                                                                                 | `BatchHandler`                                                                                                                                                                                                       |
| `ml_inference_service/cli/handlers/live_handler.py`             | `ml_service/inference/cli/handlers/live_handler.py`                                                                                                  | `LiveHandler`                                                                                                                                                                                                        |
| `ml_inference_service/engine/drift_monitor.py`                  | `ml_service/inference/engine/drift_monitor.py`                                                                                                       | `DriftMonitor`, `_ModelAccuracyTracker`, `_AccuracySample`                                                                                                                                                           |
| `ml_inference_service/engine/mock_data_provider.py`             | `ml_service/inference/engine/mock_data_provider.py`                                                                                                  | `run_mock_pipeline()` (defines `SERVICE_NAME = "ml-inference-service"`, `UPSTREAM_SERVICE = "ml-training-service"` — rename both to `"ml-service"`)                                                                  |
| `ml_inference_service/engine/model_loader.py`                   | `ml_service/inference/engine/model_loader.py`                                                                                                        | `ModelLoader`, `load_model_from_path()`, `_PredictorProtocol(Protocol)` — **counterpart to training's `ModelRegistry`; lift to UTL candidate**                                                                       |
| `ml_inference_service/engine/orchestrator.py`                   | `ml_service/inference/engine/orchestrator.py`                                                                                                        | `InferenceOrchestrator`, `DistributedInferenceResult(TypedDict)`, `_PredictableModel(Protocol)`, `inference_result_to_ml_prediction()`, `build_model_scorecard()`, `_infer_asset_group()`, `_coerce_feature_count()` |
| `ml_inference_service/engine/schemas.py`                        | `ml_service/inference/engine/schemas.py`                                                                                                             | `PredictionEvent`, `BatchInferenceRequest`, `BatchInferenceResult`, `inference_result_to_prediction_event()`, `combine_prediction_events()` — **lift candidate: cross-service wire schema (see (e))**                |

---

## (b) External callsites importing `ml_training_service.*` / `ml_inference_service.*` — workspace-wide grep

**Result: ZERO external Python imports of either source package.** Fact-report 2026-05-19 was correct.

Verification commands:

```bash
cd .tabs/1 && rg -n --type py --glob '!.venv*' --glob '!build' --glob '!dist' \
  --glob '!ml-training-service/**' --glob '!ml-inference-service/**' \
  '(from|import)\s+(ml_training_service|ml_inference_service)(\.|\s|$)'
# returns: <no output>
```

**Substring hits that are NOT Python imports of source packages** (treated as false positives, all confirmed):

| File:line                                                                                      | Match                                                                                                                                                   | Why not a real import                                                                                                                                                                                         |
| ---------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `unified-api-contracts/unified_api_contracts/internal/__init__.py:486`                         | `from unified_api_contracts.internal.domain.ml_inference_service import (...)`                                                                          | UAC namespace literally happens to contain the substring `ml_inference_service`; it is an internal UAC sub-package (`internal.domain.ml_inference_service`), NOT a Python import of the inference source repo |
| `unified-api-contracts/tests/internal/...` (multiple)                                          | same UAC namespace tests                                                                                                                                | UAC self-test of its own internal domain layer                                                                                                                                                                |
| `strategy-service/tests/unit/test_signal_vector.py:15`                                         | `from unified_api_contracts.internal.domain.ml_inference_service import CascadePredictionEvent`                                                         | Imports from UAC, not the inference repo. CascadePredictionEvent now lives in UAC                                                                                                                             |
| `system-integration-tests/tests/integration/test_batch_live_symmetry.py:88-96`                 | string literals `"ml_inference_service"`, `"ml_inference_service/cli/handlers/batch_handler.py"`, `"ml_training_service/cli/handlers/train_handler.py"` | Path constants — **MUST UPDATE post-merge**: rewrite to `"ml_service/inference/..."` and `"ml_service/training/..."`                                                                                          |
| `system-integration-tests/tests/abbreviated/test_contract_normalization.py:25`                 | UAC internal namespace import                                                                                                                           | UAC, not source repo                                                                                                                                                                                          |
| `deployment-api/tests/unit/test_route_services.py:118`                                         | function name `test_ml_training_service_has_one_bucket`                                                                                                 | Test name string only; references service-name routing                                                                                                                                                        |
| `unified-trading-library/unified_trading_library/synthetic/harness.py:167`                     | shell-command literal `"python -m ml_inference_service.cli.main ..."`                                                                                   | **MUST UPDATE post-merge**: rewrite to `"python -m ml_service --operation batch-inference ..."`                                                                                                               |
| `unified-trading-pm/scripts/openapi/generate_unified_spec.py:75-76`                            | tuple entries `("ml-inference-service", "ml_inference_service.api.main", "app"), ("ml-training-service", "ml_training_service.api.main", "app")`        | **MUST UPDATE post-merge**: collapse to one entry `("ml-service", "ml_service.api.main", "app")`                                                                                                              |
| `unified-trading-pm/scripts/openapi/generate_config_registry.py:64`                            | tuple entry `("ml-inference-service", "ml_inference_service.config", "InferenceConfig")`                                                                | **MUST UPDATE post-merge**                                                                                                                                                                                    |
| `unified-trading-system-ui/context/internal-contracts/schemas/domain/ml_inference_service/...` | Vendored copy of UAC internal `ml_inference_service` namespace                                                                                          | Vendored UAC — refreshed by separate script, not a real consumer of source repo                                                                                                                               |

**Action implications**:

1. No `from ml_training_service.*` / `from ml_inference_service.*` rewrites needed in any external repo.
2. Three non-import callsites need string updates during Phase 4 (`harness.py`, `generate_unified_spec.py`,
   `generate_config_registry.py`, plus `test_batch_live_symmetry.py` path-literal tuples).
3. UAC `internal.domain.ml_inference_service` namespace is preserved as-is (it is the home of `CascadePredictionEvent`,
   `feature_snapshot.*`, etc., already promoted out of the source repo). Post-merge, the inference sub-package will
   continue to import from `unified_api_contracts.internal.domain.ml_inference_service` — no rename required at the UAC
   side (the literal coincidence is harmless).

---

## (c) Scripts inventory per source repo + post-merge home

### ml-training-service/scripts/

| File                         | Post-merge home                                                             | Notes                                                                                                                                                                      |
| ---------------------------- | --------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `pre-flight-audit.sh`        | `ml-service/scripts/pre-flight-audit.sh`                                    | Standard workspace pattern                                                                                                                                                 |
| `quality-gates.sh`           | `ml-service/scripts/quality-gates.sh`                                       | Per-service QG entrypoint; **REGENERATE** from workspace template via `rollout-workflow-templates.sh` (do NOT subtree-copy verbatim — base-service.sh import path changes) |
| `quality_gates/` (subdir)    | `ml-service/scripts/quality_gates/`                                         | Per-service QG step overrides — copy as-is                                                                                                                                 |
| `quickmerge.sh`              | `ml-service/scripts/quickmerge.sh`                                          | **REGENERATE** from template                                                                                                                                               |
| `seed_mock_data.py`          | `ml-service/scripts/seed_mock_data_training.py` (rename to avoid collision) | Repo-specific mock seed                                                                                                                                                    |
| `setup-workspace.sh`         | `ml-service/scripts/setup-workspace.sh`                                     | Regenerate from template                                                                                                                                                   |
| `setup.sh`                   | `ml-service/scripts/setup.sh`                                               | Regenerate from template                                                                                                                                                   |
| `profile_column_pushdown.py` | `ml-service/scripts/training/profile_column_pushdown.py`                    | Training-specific perf script                                                                                                                                              |

### ml-inference-service/scripts/

| File                      | Post-merge home                                           | Notes                           |
| ------------------------- | --------------------------------------------------------- | ------------------------------- |
| `pre-flight-audit.sh`     | (dropped — duplicate with training)                       | Keep training's                 |
| `quality-gates.sh`        | (dropped — single QG at ml-service root)                  |                                 |
| `quality_gates/` (subdir) | `ml-service/scripts/quality_gates/inference/`             | Merge with training's overrides |
| `quickmerge.sh`           | (dropped)                                                 |                                 |
| `seed_mock_data.py`       | `ml-service/scripts/seed_mock_data_inference.py` (rename) |                                 |
| `setup-workspace.sh`      | (dropped)                                                 |                                 |
| `setup.sh`                | (dropped)                                                 |                                 |

---

## (d) Tests inventory per source repo + post-merge home

### ml-training-service/tests/ → `ml-service/tests/training/`

- `tests/__init__.py`, `tests/conftest.py` → `tests/training/conftest.py` (fixtures: **prefix on collision** with
  inference fixtures, e.g. `training_<fixture>`)
- `tests/e2e/` (`__init__.py`, `test_mock_training_e2e.py`, `test_training_e2e.py`) → `tests/training/e2e/`
- `tests/integration/` (`test_integration_complete_pipeline.py`, `test_shap_integration.py`,
  `test_unified_deps_functional.py`, `test_uniform_pipeline_integration.py`) → `tests/training/integration/`
- `tests/smoke/` (`test_force_symmetry.py`, `test_phase_5d_runlist.py`, `test_shard_combinatorics.py`,
  `test_strict_writer_enforcement.py`) → `tests/training/smoke/`
- `tests/unit/backtest_v2/` (`test_artifact_naming.py`, `test_runner.py`, `test_walk_forward.py`) →
  `tests/training/unit/backtest_v2/`
- `tests/unit/ml/` (`test_config_schema.py`, `test_models.py`) → `tests/training/unit/ml/`
- `tests/unit/` (~50 files: `test_base_handler.py`, `test_cascade_meta_model_trainer.py`, `test_cli_*.py`,
  `test_cloud_*.py`, `test_config_*.py`, `test_cost_sensitive_weights.py`, `test_cross_asset_training.py`,
  `test_cross_venue_spread_target.py`, `test_data_filters.py`, `test_data_preparation.py`,
  `test_defi_target_generator.py`, `test_emission_policy.py`, `test_evaluate_handler.py`, `test_event_logging.py`,
  `test_family_router.py`, `test_feature_*.py`, `test_gcs_feature_reader_column_pushdown.py`,
  `test_global_feature_selector.py`, `test_grid_search_handler.py`, `test_horizon_gate_shield.py`,
  `test_hyperparameter_tuner.py`, `test_incremental_training.py`, `test_instrument_utils.py`,
  `test_leverage_distribution_trainer.py`, `test_library_deps_integration.py`, `test_manifest_gap_handler.py`,
  `test_mock_feature_*.py`, `test_model_registry_*.py`, `test_model_trainer*.py`, `test_models.py`,
  `test_pipeline_e2e.py`, `test_pipeline_handler.py`, `test_regime_conditional_trainer.py`, `test_schema_robustness.py`,
  `test_service_startup.py`, `test_shap_explainer.py`, `test_signal_vector_meta_trainer.py`,
  `test_sports_feature_provider.py`, `test_sports_target_*.py`, `test_target_generator.py`,
  `test_tradfi_market_hours.py`, `test_training_control_api.py`, `test_training_orchestrator_utils.py`,
  `test_uniform_training_pipeline.py`, `test_validation_service.py`, `test_walk_forward_validator.py`) →
  `tests/training/unit/`
- Top-level `tests/test_*.py` (~30 legacy files not in `unit/`: `test_cloud_feature_provider.py`, `test_config.py`,
  `test_data_preparation*.py`, `test_feature_selector*.py`, `test_feature_validator.py`, `test_final_coverage_boost.py`,
  `test_global_feature_selector*.py`, `test_hyperparameter_tuning.py`, `test_model_registry*.py`,
  `test_model_trainer*.py`, `test_models.py`, `test_smoke_training.py`, `test_target_generator*.py`,
  `test_training_orchestrator*.py`) → `tests/training/unit/legacy/` (preserve coverage; flag for consolidation
  post-cutover if duplicates with `tests/unit/`)

### ml-inference-service/tests/ → `ml-service/tests/inference/`

- `tests/__init__.py`, `tests/conftest.py` → `tests/inference/conftest.py` (prefix on collision)
- `tests/e2e/` (`test_inference_e2e.py`, `test_mock_inference_e2e.py`) → `tests/inference/e2e/`
- `tests/integration/` (`test_features_ml_contract.py`, `test_features_pipeline_paths.py`,
  `test_features_pipeline_paths_mtf.py`, `test_inference_pipeline.py`, `test_model_loading.py`,
  `test_prediction_pipeline_integration.py`, `test_unified_deps_functional.py`) → `tests/inference/integration/`
- `tests/perf/` (`conftest.py`, `test_memory_gate.py`) → `tests/inference/perf/` — **only ml-inference-service has a
  `perf/` layer**; per-family layout means `PYTEST_UNIT_DIR="tests/"` override required in merged `quality-gates.sh`
  (per CLAUDE.md PYTEST_UNIT_DIR override rule)
- `tests/smoke/` (`test_shard_combinatorics.py`, `test_strict_writer_enforcement.py`) → `tests/inference/smoke/`
- `tests/unit/` (~40 files: `test_auth_and_api.py`, `test_batch_inference.py`, `test_calibration_pipeline.py`,
  `test_cascade_inference.py`, `test_cascade_publisher.py`, `test_cloud_agnostic_paths.py`, `test_confidence_scores.py`,
  `test_config.py`, `test_config_reloaders.py`, `test_date_validation.py`, `test_dependency_checker.py`,
  `test_emission_policy_per_strategy_signal.py`, `test_engine_validation.py`, `test_ensemble_and_sports.py`,
  `test_event_logging.py`, `test_feature_subscriber_helpers.py`, `test_inference_shap.py`, `test_io_loader.py`,
  `test_library_deps_integration.py`, `test_lifecycle_events.py`, `test_manifest_inference_guard.py`,
  `test_meta_signal_inference.py`, `test_mock_data_provider.py`, `test_model_loader.py`, `test_model_loader_helpers.py`,
  `test_model_promotion_subscriber.py`, `test_models.py`, `test_orchestrator_helpers.py`,
  `test_pre_crash_checkpoint.py`, `test_prediction_cache.py`, `test_prediction_event_proba.py`,
  `test_prediction_publisher_cloud.py`, `test_prediction_publisher_helpers.py`, `test_prediction_stream.py`,
  `test_schema_robustness.py`, `test_service_startup.py`, `test_storage_adapter.py`) → `tests/inference/unit/`

**Fixture collision risk** (Phase 4 (f) mandates prefixing): both repos have `tests/conftest.py`,
`tests/unit/__init__.py`, `tests/smoke/test_shard_combinatorics.py`, `tests/smoke/test_strict_writer_enforcement.py`,
`tests/unit/test_config.py`, `tests/unit/test_event_logging.py`, `tests/unit/test_library_deps_integration.py`,
`tests/unit/test_models.py`, `tests/unit/test_schema_robustness.py`, `tests/unit/test_service_startup.py`. After
splitting under `tests/training/` and `tests/inference/`, the filenames no longer collide BUT shared fixtures inside
`conftest.py` may — apply `training_<fix>` / `inference_<fix>` prefix rule per Phase 4 (f).

---

## (e) UAC / UTL symbols redefined locally

Symbols that appear local to source repos but represent cross-service concerns (lift candidates to UAC or UTL):

| Local definition                                                          | Repo:file:line                                                                                                                                                                                         | Class / function | Recommended home                                                                                                                                                                                                                           |
| ------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Local TypedDict / dataclass that already has a UAC twin                   | `ml_inference_service/types.py` (`PredictionEventDict`, `PredictionMetadata`, `FeatureVector`, `ModelMetadata`)                                                                                        | TypedDicts       | Audit against `unified_api_contracts.internal.domain.ml_inference_service.*` — if UAC twin exists, drop local; if not, lift to UAC `internal.domain.ml_inference_service` per Phase 1                                                      |
| Wire-protocol topic-name constant (shared between publisher + subscriber) | `ml_training_service/cli/handlers/__init__.py:57` AND `ml_inference_service/app/core/model_promotion_subscriber.py:28` both declare `ML_MODEL_COORDINATION_TOPIC = "ml_model_coordination_events"`     | string constant  | Lift to UAC `unified_api_contracts.canonical.crosscutting.events.topics` (or similar). Single source of truth across publisher + subscriber. **DEFER if scope-creep**; both literals already match exactly so cutover is safe without lift |
| Wire-protocol cascade topic                                               | `ml_inference_service/app/core/cascade_prediction_publisher.py:25` AND `strategy-service/strategy_service/adapters/cascade_subscriber.py:30` both declare `CASCADE_TOPIC_NAME = "cascade_predictions"` | string constant  | Same lift candidate as above — cross-repo duplication                                                                                                                                                                                      |
| MTF subscriber topic list                                                 | `ml_inference_service/app/core/mtf_feature_subscriber.py:41` `MTF_TOPIC_NAMES`                                                                                                                         | list constant    | Lift to UAC topic registry if features-service publishes from a matching constant; otherwise keep                                                                                                                                          |
| PredictionEvent wire shape                                                | `ml_inference_service/engine/schemas.py:23` `class PredictionEvent` + `inference_result_to_prediction_event()`                                                                                         | dataclass        | **strategy-service consumes prediction events** — verify if a UAC contract already exists; if not, lift to UAC `internal.domain.ml_inference_service` per Phase 1                                                                          |
| BatchInferenceRequest / BatchInferenceResult                              | `ml_inference_service/engine/schemas.py:244,257`                                                                                                                                                       | dataclasses      | Internal API shape — keep local unless it crosses the wire to strategy-service                                                                                                                                                             |
| Cascade event already UAC-promoted (sanity check)                         | `unified_api_contracts/internal/domain/ml_inference_service/cascade_prediction.py` exists                                                                                                              | dataclass        | ✅ Already in UAC. Inference repo imports it; OK                                                                                                                                                                                           |
| Model-trained event payload                                               | `ml_training_service/cli/handlers/__init__.py:191` `_emit_model_trained_event()` builds a `dict[str, object]` payload inline                                                                           | dict literal     | Lift to UAC `internal.domain.ml_training_service.model_promotion.ModelTrainedEvent` (currently no UAC type — Phase 1 finding). Symmetric to inference's `model_promotion_subscriber.py` deserialiser                                       |
| Ensemble metadata used at predict-time                                    | `ml_inference_service/app/inference/ensemble_inference.py:34` `EnsembleConfig` + `EnsembleInferenceResult`                                                                                             | dataclass        | Shared between training fit-time + inference predict-time? — verify; if training writes EnsembleConfig and inference reads it, lift to UAC                                                                                                 |
| Manifest dict shape                                                       | `ml_training_service/ml/model_registry.py:91,98` `_ManifestModelEntry`, `_ManifestDict`                                                                                                                | TypedDict        | Already marked `# CORRECT-LOCAL: internal manifest shape, not a cross-service domain contract` — keep local; do NOT lift                                                                                                                   |

---

## (f) Cross-package helper duplication across BOTH source repos (lift-to-UTL candidates)

Verified via direct `diff -u` and grep audit:

| Helper / pattern                                                                                                                                                                                             | Both repos?                                                                                                                                                                                 | Diff                                                                                                                                     | Lift target                                                                                                                                | Priority                           |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------- | --- |
| `config_reloaders.py` (full file: `get_active_instruments()`, `get_active_venues()`, `_on_instruments_reload()`, `_on_venues_reload()`, `start_domain_config_reloaders()`, `stop_domain_config_reloaders()`) | YES (both)                                                                                                                                                                                  | Near-identical — only `Settings` ↔ `InferenceConfig` typing + docstring service name + `details.service` string in CONFIG_CHANGED event | UTL `unified_trading_library.config_reloaders` (generic-over-config-type)                                                                  | **P0 — lift in Phase 5**           |
| `ServiceBootstrap(...)` invocation block in `cli/main.py`                                                                                                                                                    | YES (both)                                                                                                                                                                                  | Different service name + handler dispatch                                                                                                | Already a UTL helper (used as-is); just consolidate one invocation in `ml_service/cli/main.py`                                             | n/a (already in UTL)               |
| `make_health_router(...)` in `api/main.py`                                                                                                                                                                   | YES (both)                                                                                                                                                                                  | Different `service_name`, different `data_freshness` callback                                                                            | Already UTL helper; consolidate per Phase 4 (c)                                                                                            | n/a                                |
| `_check_emission_policy()`                                                                                                                                                                                   | YES (`ml_training_service/ml/model_registry.py:47`, `ml_inference_service/app/core/prediction_publisher.py:40`)                                                                             | Slightly different signatures                                                                                                            | UTL `unified_trading_library.emission_policy` (if not already) — verify                                                                    | P1                                 |
| `_check_mock_mode()`                                                                                                                                                                                         | YES (`ml_inference_service/app/core/prediction_publisher.py:109`, `ml_inference_service/app/core/feature_subscriber.py:34`)                                                                 | Same function within inference; potentially also in training mock_data_provider                                                          | UTL `unified_trading_library.testing.mock_mode`                                                                                            | P2                                 |
| `DependencyChecker(BaseDependencyChecker)`                                                                                                                                                                   | YES (both, in `app/core/dependency_checker.py`)                                                                                                                                             | Different class bodies (training checks features+manifest, inference checks model+features)                                              | Keep both (different responsibilities); only the base class (`BaseDependencyChecker`) is in UTL                                            | n/a                                |
| Cloud feature provider                                                                                                                                                                                       | YES (training: `app/core/cloud_feature_provider.py:CloudFeatureProvider`; inference: not exact same class but `app/core/feature_subscriber.py:FeatureSubscriber` reads features from cloud) | Different IO patterns (training reads bulk historical; inference reads live + cache)                                                     | Possible shared `CloudFeatureReader` base in UTL; **DEFER post-cutover** unless trivial                                                    | P3                                 |
| Kill-switch bus subscriber boilerplate                                                                                                                                                                       | NOT FOUND in either repo (grep `KillSwitch                                                                                                                                                  | kill_switch` returns 0)                                                                                                                  | n/a                                                                                                                                        | n/a — DROP from Phase 5 lift list  | n/a |
| `ManifestFreshnessCache` adoption                                                                                                                                                                            | NEITHER repo uses it (grep returns hits only in UTL itself). Both repos read manifests via their own paths                                                                                  | n/a                                                                                                                                      | **PHASE 0 FINDING (NEW)**: ml-service is a candidate for ManifestFreshnessCache adoption post-merge. Capture as deferred follow-up in plan | DEFERRED — capture as P2 plan todo |
| `ModelRegistry` (training) vs `ModelLoader` (inference)                                                                                                                                                      | YES (counterparts)                                                                                                                                                                          | Different concerns: registry writes + reads metadata + manifest; loader reads + caches model files                                       | Lift unified `MlModelRegistry` to UTL per plan Phase 5 spec                                                                                | **P1 — Phase 5**                   |
| `pre_crash_checkpoint.py` (`register_pre_crash_handlers()`, `_memory_watchdog()`)                                                                                                                            | ONLY inference has it                                                                                                                                                                       | n/a                                                                                                                                      | Lift to UTL `unified_trading_library.lifecycle.pre_crash` (cross-cutting; benefits all services)                                           | P2 — DEFERRED candidate            |

---

## (g) Per-repo `pyproject.toml` dependency union — version conflicts + optional-deps split

### Runtime dependency union (combining both `[project.dependencies]` lists)

| Distribution                             | Training           | Inference          | Union resolution                                                                                                                   | Split tier                                             |
| ---------------------------------------- | ------------------ | ------------------ | ---------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------ |
| `fastapi`                                | `>=0.115.0,<1.0.0` | `>=0.115.0,<1.0.0` | identical                                                                                                                          | core (both)                                            |
| `uvicorn`                                | `>=0.34.0,<1.0.0`  | `>=0.34.0,<1.0.0`  | identical                                                                                                                          | core                                                   |
| `sse-starlette`                          | –                  | `>=1.6.1,<2.0.0`   | inference-only                                                                                                                     | inference                                              |
| `numpy`                                  | `>=2.3.0,<2.4.0`   | `>=2.3.0,<2.4.0`   | identical                                                                                                                          | core                                                   |
| `pandas`                                 | `>=2.3.0,<3.0.0`   | `>=2.3.0,<3.0.0`   | identical                                                                                                                          | core                                                   |
| `polars`                                 | `>=1.37.0,<2.0.0`  | –                  | training-only                                                                                                                      | training                                               |
| `pyarrow`                                | `>=23.0.0,<24.0.0` | –                  | training-only                                                                                                                      | training                                               |
| `db-dtypes`                              | `>=1.5.0,<2.0.0`   | –                  | training-only (BigQuery dtypes)                                                                                                    | training                                               |
| `pydantic`                               | `>=2.12.5,<3.0.0`  | `>=2.12.5,<3.0.0`  | identical                                                                                                                          | core                                                   |
| `pydantic-settings`                      | `>=2.12.0,<3.0.0`  | `>=2.12.0,<3.0.0`  | identical                                                                                                                          | core                                                   |
| `scikit-learn`                           | `>=1.5.0,<2.0.0`   | `>=1.5.0,<2.0.0`   | identical — used at predict-time too (calibration, scaler unpickle)                                                                | core (both)                                            |
| `lightgbm`                               | `>=4.0.0,<5.0.0`   | `>=4.0.0,<5.0.0`   | identical — inference loads LightGBM models                                                                                        | core (both)                                            |
| `xgboost`                                | `>=2.0.0,<4.0.0`   | –                  | training-only                                                                                                                      | training                                               |
| `catboost`                               | `>=1.2.0,<2.0.0`   | –                  | training-only                                                                                                                      | training                                               |
| `onnxruntime`                            | –                  | `>=1.18.0,<2.0.0`  | inference-only                                                                                                                     | inference                                              |
| `ta-lib`                                 | `>=0.6.8,<1.0.0`   | –                  | training-only                                                                                                                      | training                                               |
| `python-dateutil`                        | `>=2.8.2,<3.0.0`   | `>=2.8.2,<3.0.0`   | identical                                                                                                                          | core                                                   |
| `tqdm`                                   | `>=4.66.0,<5.0.0`  | –                  | training-only                                                                                                                      | training                                               |
| `optuna`                                 | `>=4.0.0,<5.0.0`   | –                  | training-only (hyperparam)                                                                                                         | training                                               |
| `shap`                                   | `>=0.46.0,<1.0.0`  | `>=0.51.0,<1.0.0`  | **CONFLICT**: training `>=0.46`, inference `>=0.51`. Resolution: union `>=0.51.0,<1.0.0` (both satisfied; matches inference floor) | core if SHAP-at-predict is enabled, else training-only |
| `joblib`                                 | `>=1.3.0,<2.0.0`   | –                  | training-only                                                                                                                      | training                                               |
| `matplotlib`                             | `>=3.9.0,<4.0.0`   | –                  | training-only (training visualisations)                                                                                            | training                                               |
| `psutil`                                 | `>=6.0.0,<7.0.0`   | `>=6.0.0,<7.0.0`   | identical                                                                                                                          | core                                                   |
| `prometheus-client`                      | `>=0.20.0,<1.0.0`  | `>=0.20.0,<1.0.0`  | identical                                                                                                                          | core                                                   |
| `requests`                               | `>=2.33.0,<3.0.0`  | `>=2.33.0,<3.0.0`  | identical                                                                                                                          | core                                                   |
| `aiohttp`                                | `>=3.13.4,<4.0.0`  | `>=3.13.4,<4.0.0`  | identical                                                                                                                          | core                                                   |
| `boto3`                                  | `>=1.40.70,<2.0.0` | –                  | training-only (AWS S3 writes)                                                                                                      | training (or core if inference also writes to S3)      |
| `aiobotocore`                            | `>=2.11.0,<3.0.0`  | –                  | training-only                                                                                                                      | training                                               |
| `pillow`                                 | `>=12.2.0,<13.0.0` | –                  | training-only                                                                                                                      | training                                               |
| `opentelemetry-api`                      | –                  | `>=1.27.0,<2.0.0`  | inference-only (live-mode tracing)                                                                                                 | inference                                              |
| `opentelemetry-sdk`                      | –                  | `>=1.27.0,<2.0.0`  | inference-only                                                                                                                     | inference                                              |
| `opentelemetry-exporter-otlp-proto-grpc` | –                  | `>=1.27.0,<2.0.0`  | inference-only                                                                                                                     | inference                                              |
| `opentelemetry-instrumentation-fastapi`  | –                  | `>=0.48b0,<1.0.0`  | inference-only                                                                                                                     | inference                                              |
| `unified-trading-library`                | `>=0.3.0,<1.0.0`   | `>=0.1.0,<1.0.0`   | union: `>=0.3.0,<1.0.0` (matches training floor)                                                                                   | core                                                   |
| `unified-api-contracts`                  | `>=0.1.0,<1.0.0`   | `>=0.1.0,<1.0.0`   | identical                                                                                                                          | core                                                   |

### Dev/test dependency union (same `[project.dependencies]` list, dev-marker tools)

`pytest` (`>=9.0.3,<10.0.0`), `pytest-cov` (`>=7.0.0,<8.0.0`), `pytest-socket` (`>=0.7.0,<1.0.0`), `pytest-asyncio`
(training `>=0.25.0,<2.0.0`, inference `>=0.25.0,<2.0.0` — identical), `pytest-mock` (`>=3.15.0,<4.0.0`),
`pytest-timeout` (`>=2.4.0,<3.0.0`), `pytest-xdist` (`>=3.6.0,<4.0.0`), `ruff==0.15.0`, `basedpyright==1.38.2`,
`pip-audit` (`>=2.7.0,<3.0.0`), `bandit` (`>=1.7.0,<2.0.0`), `pygments` (`>=2.20.0,<3.0.0`).

Training-only dev: `mypy` (`>=1.13.0,<2.0.0`). Inference-only dev: `pandas-stubs` (`>=2.2.0,<3.0.0`), `types-requests`
(`>=2.32.0,<3.0.0`).

### Version conflicts requiring explicit resolution

1. **`shap`**: training `>=0.46.0`, inference `>=0.51.0` → resolve at `>=0.51.0,<1.0.0` (compatible with both APIs;
   verified — both repos use the same SHAP API).
2. **`unified-trading-library`**: training `>=0.3.0`, inference `>=0.1.0` → resolve at `>=0.3.0,<1.0.0`.

### Recommended Phase 2 (c) / Phase 4 (h) optional-deps split

Per workspace's "flat deps only" rule (CLAUDE.md § "Dependencies + builds: Flat deps only — one `[project.dependencies]`
per `pyproject.toml`. No extras."), the workspace standard is **flat dependencies, no extras**. However, the
consolidation plan Phase 4 (h) explicitly authorises `[project.optional-dependencies] training = [...]` for Docker layer
separation — this is a **DEFENSIBLE EXCEPTION** justified by the inference-vs-training image-weight differential.

Recommended split:

```toml
[project.dependencies]   # ~16 core (runtime + inference)
fastapi, uvicorn, sse-starlette, numpy, pandas, pydantic, pydantic-settings, scikit-learn,
lightgbm, onnxruntime, python-dateutil, psutil, shap, requests, aiohttp, prometheus-client,
opentelemetry-api, opentelemetry-sdk, opentelemetry-exporter-otlp-proto-grpc,
opentelemetry-instrumentation-fastapi, unified-trading-library, unified-api-contracts

[project.optional-dependencies]
training = [           # ~11 extras only when training image is built
  "polars", "pyarrow", "db-dtypes", "xgboost", "catboost", "ta-lib", "tqdm", "optuna",
  "joblib", "matplotlib", "boto3", "aiobotocore", "pillow",
]
```

**Estimated Docker image weight delta (rough)**: training-only stack adds approximately:

- `xgboost` ~150MB compiled
- `catboost` ~120MB
- `optuna` ~25MB
- `ta-lib` ~5MB (C library + Python bindings; needs system `libta-lib` apt-pkg)
- `polars` ~80MB
- `pyarrow` ~100MB
- `boto3`+`aiobotocore`+deps ~80MB
- `shap` (if heavy variant kept) ~50MB
- `matplotlib` ~80MB
- `pillow` ~30MB
- joblib + tqdm + db-dtypes ~10MB combined

Total: roughly **700-800MB** of training-only weight on top of inference baseline. Inference-only image weight (core
deps) roughly **400-500MB** including base Python + UTL + UAC + fastapi/uvicorn + numpy/pandas/sklearn/lightgbm +
onnxruntime

- opentelemetry stack. Split therefore yields **~55-60% leaner** live-inference image vs naive flat-union build. **The
  plan's <30% image regression cap (Phase 4 (h)) is achievable only with the split.**

**HOWEVER** — this split contradicts the workspace "flat deps only" rule. Recommend Phase 4 (h) explicitly cite this
exception in the merged repo's `pyproject.toml` (e.g.
`# EXCEPTION: optional-dependencies allowed for training vs inference Docker layer separation. See plan ml_repo_consolidation_2026_05_19.md Phase 4 (h).`)
AND update CLAUDE.md `### Dependencies + builds` line to acknowledge ml-service as a sanctioned exception. **Capture as
plan todo for Phase 7 codex update.**

---

## (h) Hardcoded service-name strings + pub/sub topic constants + env-var prefixes + GCS subpaths + terraform refs + cursor-configs / codex refs

### Service-name string literals inside source repos (post-merge: most → `"ml-service"`, some stay specific)

**ml-training-service**:

- `ml_training_service/cli/main.py:291` `service_name="ml-training-service"` (ServiceBootstrap)
- `ml_training_service/api/main.py:46` `service_name="ml-training-service"` (make_health_router)
- `ml_training_service/engine/orchestrator.py:75,110` `service_name="ml-training-service"` (event emission)
- `ml_training_service/engine/mock_data_provider.py:35,275,286` `SERVICE_NAME: Final[str] = "ml-training-service"`
- `ml_training_service/ml/model_registry.py:44,64,350` `_SERVICE_NAME: str = "ml-training-service"` +
  `service_name="ml-training-service"`
- `ml_training_service/auth_s2s.py:5` `verify_service_token = create_s2s_auth_dependency("ml-training-service")`
- `ml_training_service/config_reloaders.py` `"service": "ml-training-service"` in CONFIG_CHANGED event details
- `ml_training_service/metrics.py` Prometheus namespace `ml_training_service_*`

**ml-inference-service**:

- `ml_inference_service/cli/main.py:361` `service_name="ml-inference-service"`
- `ml_inference_service/api/main.py:46` `service_name="ml-inference-service"`
- `ml_inference_service/engine/mock_data_provider.py:38,39` `SERVICE_NAME: Final[str] = "ml-inference-service"`,
  `UPSTREAM_SERVICE: Final[str] = "ml-training-service"`
- `ml_inference_service/engine/mock_data_provider.py:319,329,339` `service_name="ml-inference-service"`
- `ml_inference_service/engine/model_loader.py:75` `service_name="ml-inference-service"`
- `ml_inference_service/cli/handlers/batch_handler.py:256` `service_name="ml-inference-service"`
- `ml_inference_service/app/core/prediction_publisher.py:37,65,211,302` `_SERVICE_NAME: str = "ml-inference-service"` +
  `service_name="ml-inference-service"`
- `ml_inference_service/app/core/dependency_checker.py:28` `SERVICE_NAME = "ml-inference-service"`
- `ml_inference_service/app/core/feature_subscriber.py:268` docstring reference
- `ml_inference_service/auth_s2s.py` `create_s2s_auth_dependency("ml-inference-service")`
- `ml_inference_service/config.py:24` `default="ml-inference-service"`
- `ml_inference_service/engine/schemas.py:35,123,162` `service="ml-inference-service"` (PredictionEvent default)
- `ml_inference_service/metrics.py` Prometheus namespace `ml_inference_service_*`

**Post-merge action**: rename all to `"ml-service"`. For event emissions where the originating sub-pipeline is
operationally distinct (e.g. PredictionEvent.service field for downstream consumers), keep a `sub_service` discriminator
(`"training"` / `"inference"`) on the event payload but the umbrella `service` becomes `"ml-service"`. **This is the
single biggest source-rename surface in Phase 4 (a).**

### Pub/sub topic-name constants (CRITICAL — model promotion topic compatibility)

**Topic-name constants are wire-protocol values, not service-name strings.** Renaming the service does NOT require
renaming topics. The plan Phase 0 (h) explicitly flagged "topic-name compatibility decisions land here" — verdict: **NO
TOPIC-NAME RENAME REQUIRED.** Both the training-side publisher and inference-side subscriber already share an identical
string literal, and strategy-service's cascade subscriber matches the inference cascade publisher.

| Topic                          | Publisher                                                                   | Subscriber                                                                     | Constant                                                                                             |
| ------------------------------ | --------------------------------------------------------------------------- | ------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------- |
| `ml_model_coordination_events` | `ml_training_service/cli/handlers/__init__.py:57,225` (MODEL_TRAINED event) | `ml_inference_service/app/core/model_promotion_subscriber.py:28,108,162,170`   | `ML_MODEL_COORDINATION_TOPIC = "ml_model_coordination_events"` — **identical literal in both repos** |
| `cascade_predictions`          | `ml_inference_service/app/core/cascade_prediction_publisher.py:25`          | `strategy-service/strategy_service/adapters/cascade_subscriber.py:30`          | `CASCADE_TOPIC_NAME = "cascade_predictions"` — **identical literal in both repos**, cross-repo wire  |
| `mtf_features.*`               | features-service (TBV)                                                      | `ml_inference_service/app/core/mtf_feature_subscriber.py:41` `MTF_TOPIC_NAMES` | List of strings; verify features-service publishes from a matching list                              |

**Phase 4 atomic-sequencing concern**: the plan's foot-gun "model promotion topic-name changes invalidate ml-inference's
`model_promotion_subscriber` until subscribers + publishers align" is **MOOT** because no topic renames are needed. Both
topic literals match exactly and survive the consolidation intact. The Phase 4 (b) atomic-sequencing concern is
therefore demoted from CRITICAL to LOW-RISK.

### Env-var prefixes

`grep -n 'ML_TRAINING_SERVICE_\|ML_INFERENCE_SERVICE_' ml-training-service ml-inference-service` returns 0 hits inside
source code — **no env-var prefix renames needed in source.** Env-var-prefix references may exist in:

- `unified-trading-library/unified_trading_library/config_interface/auth/service_access_matrix.yaml` (uses service-NAME
  keys, not env-prefixes; see below).
- VM launcher scripts in `deployment-service/scripts/vm/` (TBV during Phase 4 (h) sweep).

### GCS bucket subpaths + model registry references

| File                                                                                                                                     | Pattern                                                                                                                                 | Action                                                                                                                                                                                                                                |
| ---------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `batch-live-reconciliation-service/docs/GCS_PATHS.md:10,13`                                                                              | `live/events/{date}/ml-inference-service/` and `t1-recon/events/{date}/ml-inference-service/`                                           | Path SSOT — **MUST UPDATE post-cutover or maintain alias** (live data already written under this prefix); recommend continue writing to `ml-inference-service/` for batch-live symmetry; post-cutover migrate via a hard cutover plan |
| `trading-agent-service/docs/GCS_PATHS.md:19`                                                                                             | `gs://{bucket_name}/ml-inference/{date}/{commodity}/predictions_*.json`                                                                 | Path uses generic `ml-inference/` prefix, NOT `ml-inference-service/` — already service-name-agnostic; OK                                                                                                                             |
| `deployment-service/deployment_service/shard_builder.py:28-29`                                                                           | `"ml-training-service": ["ml-models-store", "ml-configs-store"]`, `"ml-inference-service": ["ml-predictions-store", "ml-models-store"]` | Update post-merge to a single `"ml-service"` key with union bucket list                                                                                                                                                               |
| GCS bucket names referenced: `ml-models-store`, `ml-configs-store`, `ml-predictions-store`                                               | Bucket SSOT lives in `deployment-service/configs/cloud-providers.yaml` (out of scope to rename)                                         | Keep bucket names; just collapse the `shard_builder` mapping                                                                                                                                                                          |
| `unified-trading-library/unified_trading_library/config_interface/auth/service_access_matrix.yaml:61,62,115,116,124,125,...,209,213,217` | Service-name keys + access entries for `ml-training-service` and `ml-inference-service`                                                 | **MUST UPDATE post-merge**: collapse to single `ml-service` entry with union of training+inference access rules; consumers in S2S auth dispatch will fail if entries removed before service name rename                               |

### Deployment / terraform / CI refs

**Terraform** (`deployment-service/terraform/`):

- `terraform/cloud-build/aws/main.tf:87-95` AWS CloudBuild blocks for both
- `terraform/cloud-build/gcp/main.tf:73-80` GCP CloudBuild blocks for both
- `terraform/services/ml-training-service/{aws,gcp}/` directory (own backend.tf, main.tf, variables.tf, outputs.tf,
  terraform.tfvars.example)
- `terraform/services/ml-inference-service/{aws,gcp}/` directory (same set of files)
- `terraform/shared/aws/main.tf:89-90`, `terraform/shared/gcp/main.tf:44-45` — both names in shared infra service list
- `terraform/modules/shared-infrastructure/gcp/variables.tf:29-30` — both names in default service list
- `terraform/modules/shared-infrastructure/gcp/main.tf:203,238,263,288` — both names in labels
- `terraform/gcp/t1_batch_scheduler.tf:35,158-159` — inference-specific T1 batch scheduler
- `cloud-build/refresh-tarballs.cloudbuild.yaml:116-117` — both names in tarball refresh list
- `deployment_service/dependencies.py:535` — `"ML": ["ml-training-service", "ml-inference-service"]`

**Action**: terraform service directories must be renamed to `ml-service/` and the dual-service patterns collapsed to
single `ml-service` references. AWS/GCP backend state files will need migration (operator-action; pings ledger entry).
This is Phase 7 (archive source repos) / Phase 8 (deployment cutover) scope.

**CI** (`.github/workflows/`):

- Per-repo workflows under `ml-training-service/.github/workflows/*` and `ml-inference-service/.github/workflows/*`
- Will be regenerated from `unified-trading-pm/scripts/workflow-templates/` per Phase 2 (g) of the plan

### `unified-trading-pm/` references

- `unified-trading-pm/cursor-configs/unified-trading-system-repos.code-workspace` — both repos listed in `folders` for
  each of the 8 tab worktrees (16 references total). **MUST UPDATE post-merge**: replace each pair with a single
  `ml-service` entry per tab.
- `unified-trading-pm/codex/11-project-management/epics/cefi-epic.yaml:153,159`, `defi-epic.yaml:148,152`,
  `sports-epic.yaml:115,119`, `tradfi-epic.yaml:116,122` — epic repo-lists reference both; collapse to `ml-service`
  post-archive
- `unified-trading-pm/codex/README.md:90-91` — architecture diagram mentions both service boxes; update diagram
- `unified-trading-pm/codex/DEPRECATED_UIS_NOTICE.md:12` — historical reference; OK to leave
- `unified-trading-pm/scripts/openapi/generate_unified_spec.py:75-76` — see (b)
- `unified-trading-pm/scripts/openapi/generate_config_registry.py:64` — see (b)
- 455 total matches in `cursor-configs/` + `codex/` (`rg -c`). Bulk update is a Phase 7 codex-sweep operation — capture
  as plan todo: **P1 docs(codex): collapse `ml-training-service` + `ml-inference-service` references to `ml-service`
  (455 file:line hits)**.

### Other workspace-level references (informational, do NOT rewrite from this plan)

- `execution-service/configs/expected_start_dates.yaml:382,407` — service-start-date config (used by deployment
  heartbeat); update post-archive
- `execution-service/docs/ARCHITECTURE.md:71,77,89,94` — diagram refs
- `market-tick-data-service/configs/expected_start_dates.yaml:387,412` — same as execution-service
- `market-tick-data-service/docs/SHAHRIYAR_DEPLOYMENT_INFRA_SPEC.md:44-45` — doc list
- `e2e-testing/scripts/{cefi,tradfi,sports,prediction}/run-full-pipeline.sh` — every full-pipeline runner enumerates
  `ml-training-service:ml_training_service:train:` and `ml-inference-service:ml_inference_service:predict:` tuples
  (entry-format `service_repo:python_pkg:cli_command:`). **MUST UPDATE post-merge** to
  `ml-service:ml_service.training:train:` and `ml-service:ml_service.inference:predict:` (or new operation taxonomy).
- `e2e-testing/scripts/common/verify-protocols.sh:53,105` — port-mapping list; update for ml-service single port
- `e2e-testing/docs/E2E_PIPELINE_GUIDE.md:274,285,297` — L5 service-name table; update
- `e2e-testing/docs/cefi/per-strategy-acceptance.md:238,248,249,270` — acceptance text; update
- `strategy-service/README.md:39`, `strategy-service/docs/DEPENDENCIES.md:8,23,29,78,93-94,119` — dependency docs;
  update
- `system-integration-tests/README.md:132,149` — service inventory table; update
- `market-data-processing-service/docs/DEPENDENCIES.md:99-100` — dependency doc list
- `unified-trading-library/QUALITY_GATE_BYPASS_AUDIT.md:118`, `unified-trading-library/docs/DEPENDENCIES.md:38-39` — doc
  refs
- `trading-agent-service/README.md:44`, `trading-agent-service/docs/GCS_PATHS.md:19` — dependency text
- `batch-live-reconciliation-service/docs/GCS_PATHS.md:10,13` — see GCS subpaths above
- `deployment-service/scripts/bootstrap/bootstrap_{gcp,aws}.sh` — commented-out deploy lines (informational)
- `deployment-service/tools/check_ml_dependencies_by_mode.py:5` — docstring ref
- `unified-api-contracts/openapi/unified-trading-system.openapi.yaml:18875-22521` — OpenAPI tags `ml-inference-service`
  and `ml-training-service` + health/readiness paths. **REGENERATE post-merge** via PM script
  `generate_unified_spec.py`.
- `unified-api-contracts/docs/UAC_ADOPTION_MATRIX.md:155-156` — adoption matrix rows for both repos; collapse to one
- `unified-api-contracts/unified_api_contracts/internal/testing/scenarios/seed_spec.yaml:267,269,274` — seed spec
  references; update

**None of these are review-blocking for Phase 0**; they are downstream consumer updates owned by Phase 7 / Phase 8 of
the consolidation plan.

---

## Discovery / nice-to-have callouts (capture into plan as P2/P3 todos)

> Per CLAUDE.md "Capture Discoveries As Plan Todos Immediately" HARD RULE, the following side-discoveries are reported
> here for the orchestrator to fold into `ml_repo_consolidation_2026_05_19.md` as `**DEFERRED**` / `**NICE-TO-HAVE**`
> todos.

1. **P2 `**NICE-TO-HAVE**`**: ml-service is a candidate for `ManifestFreshnessCache` adoption (UTL
   `unified_trading_library.manifest_freshness.ManifestFreshnessCache`). Neither source repo currently uses it.
   Post-merge consolidation phase. Provenance: this pre-audit § (f).
2. **P2 `**NICE-TO-HAVE**`**: lift wire-protocol topic-name constants (`ML_MODEL_COORDINATION_TOPIC`,
   `CASCADE_TOPIC_NAME`, `MTF_TOPIC_NAMES`) to UAC `unified_api_contracts.canonical.crosscutting.events.topics` (or
   equivalent). Currently duplicated as string literals between publisher/subscriber repos. Provenance: this pre-audit §
   (e), (h).
3. **P1**: lift `pre_crash_checkpoint.py` (`register_pre_crash_handlers()`, `_memory_watchdog()`) from inference repo to
   UTL `unified_trading_library.lifecycle.pre_crash` — cross-cutting utility benefits every service. Provenance: this
   pre-audit § (f).
4. **P1 `[BLOCKED-OPERATOR-DECISION]`**: Phase 4 (h) `[project.optional-dependencies] training = [...]` split violates
   workspace's "flat deps only" rule per CLAUDE.md `### Dependencies + builds`. Document the exception explicitly in (a)
   `ml-service/pyproject.toml` comment AND (b) CLAUDE.md acknowledging ml-service as sanctioned exception. Provenance:
   this pre-audit § (g).
5. **P1**: codex / cursor-configs / docs sweep — 455 file:line hits across `unified-trading-pm/cursor-configs/` +
   `unified-trading-pm/codex/` reference the two source-repo names. Owned by Phase 7 post-archive codex-sweep operation.
   Provenance: this pre-audit § (h).
6. **P2 `**NICE-TO-HAVE**`**: `ml_inference_service.api.prediction_stream` SSE endpoint is INFERENCE-only; the merged
   `make_health_router` call in Phase 4 (c) must continue routing `/stream/predictions` via the inference sub-app router
   (not a global ml-service router).
7. **P0 `[NAME-COLLISION-FIX]`**: `ml_inference_service/io/loader.py:FeatureSubscriber` and
   `ml_inference_service/app/core/feature_subscriber.py:FeatureSubscriber` are two distinct classes with the same name
   in the same package. Rename one during Phase 4 (a) (suggest `IoFeatureSubscriber` for `io/loader.py:24`). Provenance:
   this pre-audit § (a) inference table row 2.
8. **P2**: `tests/perf/` exists only in inference repo. Merged `quality-gates.sh` must set `PYTEST_UNIT_DIR="tests/"`
   per CLAUDE.md PYTEST_UNIT_DIR override rule to collect both `tests/training/unit/` and
   `tests/inference/{unit,perf}/`.
9. **P1**: Legacy top-level `ml-training-service/tests/test_*.py` files (~30) duplicate the structured
   `tests/unit/test_*.py` set. Consolidation post-merge — Phase 7 cleanup. Provenance: this pre-audit § (d).
10. **P2**: `verify_service_token` from `auth_s2s.py` is built per-repo via
    `create_s2s_auth_dependency("ml-{training,inference}-service")`. Post-merge → single
    `create_s2s_auth_dependency("ml-service")` BUT downstream callers in deployment-api / strategy-service etc. may pass
    the old service names in S2S tokens. Audit S2S token issuance + verification cutover. Provenance: this pre-audit §
    (h).

---

## Summary statistics

- Source modules to merge: **45 in ml-training-service** + **40 in ml-inference-service** = **85 Python modules**
- Source test files to merge: **~95 in ml-training-service** + **~38 in ml-inference-service** = **~133 test files**
- Source scripts to merge: 8 + 7 = 15 (deduplicate to ~10 post-merge)
- External Python imports of source packages to rewrite: **0 (zero)**
- External non-Python string references to rewrite (PM + UAC + UTL + e2e-testing + deployment + docs): **~80-100
  files**, mostly bulk-substitutable via `sed`
- pyproject dependency union: **35 distinct distributions** (16 core + 11 training-only + 8 inference-only after
  recommended split)
- Version conflicts requiring resolution: 2 (`shap`, `unified-trading-library`)
- Topic-name renames required: **0 (zero)** — wire-protocol literals already match across publisher + subscriber
- ServiceBootstrap consolidation points: 2 → 1
- make_health_router consolidation points: 2 → 1
- config_reloaders.py consolidation: 2 near-identical files → 1 merged
- UTL lift candidates identified: 4 (config_reloaders, MlModelRegistry, pre_crash_checkpoint, ManifestFreshnessCache
  adoption)
- UAC lift candidates identified: 3 (topic-name constants, ModelTrainedEvent payload, PredictionEvent if not already)
- Plan-todo discoveries captured: 10 (see Discovery section above)

---

## Verification commands (re-runnable)

```bash
# (b) — confirm zero external Python imports
cd .tabs/1 && rg -n --type py --glob '!.venv*' --glob '!build' --glob '!dist' \
  --glob '!ml-training-service/**' --glob '!ml-inference-service/**' \
  '(from|import)\s+(ml_training_service|ml_inference_service)(\.|\s|$)'

# (f) — confirm config_reloaders are near-identical
diff -u ml-training-service/ml_training_service/config_reloaders.py \
        ml-inference-service/ml_inference_service/config_reloaders.py

# (h) — service-name string literal scan inside source
cd .tabs/1 && rg -n 'ml[-_]training[-_]service|ml[-_]inference[-_]service' \
  ml-training-service/ml_training_service ml-inference-service/ml_inference_service

# (h) — topic-name constant verification
cd .tabs/1 && rg -n 'ML_MODEL_COORDINATION_TOPIC|CASCADE_TOPIC_NAME' --type py

# (h) — workspace-wide non-source-repo refs
cd .tabs/1 && rg -n 'ml-(training|inference)-service|ml_(training|inference)_service' \
  --glob '!ml-training-service/**' --glob '!ml-inference-service/**' --glob '!.venv*' \
  | wc -l
```
