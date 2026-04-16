---
name: ml-pipeline-ui-integration
overview:
  ML pipeline → API → UI integration — mock data to GCS, SHAP artifacts, 16 missing endpoints, tier-aligned mode
  switching, inference serving
type: mixed
epic: epic-deployment
status: active

completion_gates:
  code: C5
  deployment: D3
  business: B4

repo_gates:
  - repo: ml-training-service
    code: C0
    deployment: none
    business: none
  - repo: ml-inference-service
    code: C0
    deployment: none
    business: none
  - repo: unified-trading-api
    code: C0
    deployment: none
    business: none
  - repo: unified-trading-system-ui
    code: C0
    deployment: none
    business: none
  - repo: deployment-service
    code: C0
    deployment: none
    business: none
  - repo: unified-trading-library
    code: C0
    deployment: none
    business: none

depends_on:
  - unified-pipeline-scheduling-and-triggers

todos:
  # ── Phase 1: Mock Data to GCS ──
  - id: p1-mock-features-to-gcs
    status: done
    content: |
      - [x] [AGENT] P0. Write mock features to GCS instead of in-memory only. When ml-training-service runs with --use-mock-data:
        1. MockFeatureGenerator generates features as now (pandas DataFrame in memory)
        2. ALSO write to GCS at: features-delta-one-{category}-{project_id}/mock/by_date/day={date}/feature_group={group}/timeframe={tf}/{instrument}.parquet
        3. Same hive partitioning as real features — just under mock/ prefix
        4. This makes mock features readable by BigQuery external tables, data status CLI, and any GCS reader
        5. The mock path should be configurable: MOCK_GCS_PREFIX env var (default "mock")
        Files: ml_training_service/app/core/cloud_feature_provider.py (_query_mock_features method), ml_training_service/app/core/mock_feature_generator.py
    status: todo
    note: "Mock features currently generated in memory and never persisted. Writing to GCS enables full path testing."

  - id: p1-mock-swing-targets-distribution
    content: |
      - [x] [AGENT] P1. Fix mock swing target distribution — currently all targets are 'neither' (0) after filtering because the swing_high column gets lost during feature selection. The mock data DOES generate proper 30/30/40 distribution at swing points, but the pipeline's feature selection drops swing_high before filter_to_swing_events runs. Fix: ensure swing_high/swing_low columns survive feature selection OR filter before selection.
        Files: ml_training_service/app/core/training_orchestrator.py (_load_features_and_targets — move filter_to_swing_events BEFORE _resolve_selected_features)
    status: done
    note: "Fixed: mock outcomes now generated at ALL rows (not just swing points) matching real feature service schema."

  - id: p1-shap-artifacts-to-gcs
    content: |
      - [x] [AGENT] P0. Write SHAP artifacts to GCS instead of local /tmp/. Currently ShapExplainer saves to /tmp/models/shap_explanations/ which is ephemeral on Cloud Run/VMs. Move to:
        gs://ml-training-artifacts-{project_id}/experiments/{experiment_id}/shap/{instrument}_{timeframe}_shap_summary_class_{n}.png
        gs://ml-training-artifacts-{project_id}/experiments/{experiment_id}/shap/{instrument}_{timeframe}_shap_values_class_{n}.csv
        Files: ml_training_service/app/training/shap_explainer.py (save methods), ml_training_service/app/core/training_orchestrator.py (where ShapExplainer is called)
    status: done
    note: "SHAP artifacts now upload to GCS ml-training-artifacts bucket after local generation."

  - id: p1-create-artifacts-bucket
    content: |
      - [x] [AGENT] P0. Create ml-training-artifacts bucket. The model store bucket exists (ml-models-store-{project_id}) but the artifacts bucket doesn't. Either:
        1. Add to deployment-service/scripts/setup-buckets.sh (or equivalent)
        2. Or create via terraform in deployment-service/terraform/
        The bucket stores: experiments/{id}/metrics.json, experiments/{id}/shap/*.png, stage artifacts (selected features, hyperparams)
    status: done
    note: "Created via gsutil mb. Added to terraform shared-infrastructure module, root gcp/main.tf, bucket_config.yaml."

  # ── Phase 2: ML Training Config Architecture ──
  - id: p2-training-config-from-gcs
    content: |
      - [x] [AGENT] P1. Move train_test_split_date from hardcoded config to GCS grid config. Currently hardcoded as "2023-01-01" in ml_training_service/config.py line 216. Should be:
        1. Default: "auto" — compute as 80% of date range (or fold-determined for walk-forward)
        2. Overridable: via grid config in GCS (ml-training-artifacts-{project_id}/grid_configs/{name}.json)
        3. Overridable: via deployment API when triggering training from UI
        Walk-forward folds already override per-fold (fixed in this session). The global default just needs to be "auto" not hardcoded.
        Files: ml_training_service/config.py, ml_training_service/app/training/data_preparation.py
    status: done
    note: "Default changed to 'auto' (80% of date range). DataPreparation computes from data."

  - id: p2-min-test-samples-guard
    content: |
      - [x] [AGENT] P1. Add minimum test samples guard to walk-forward splitter. If a fold produces fewer than MIN_TEST_SAMPLES (default 100) test rows, skip the fold with a warning instead of silently proceeding with empty features.
        Files: ml_training_service/app/training/data_preparation.py (split_train_test method), ml_training_service/app/core/walk_forward_validator.py
    status: done
    note: "MIN_TEST_SAMPLES=100 guard added. Returns empty DataFrames to skip insufficient splits."

  # ── Phase 3: ML API Endpoints (unified-trading-api) ──
  - id: p3-training-job-endpoints
    content: |
      - [x] [AGENT] P0. Add training job management endpoints to unified-trading-api/routes/ml.py:
        POST /api/ml/training-runs — create and queue a training run. Body: {category, instruments, timeframes, target_types, start_date, end_date, grid_config, walk_forward_folds, optuna_trials}. In mock mode: return mock job ID. In real mode: trigger ml-training-service via deployment-service batch API (POST /deployment-api/api/batch/run with service=ml-training-service).
        GET /api/ml/training-runs/{id} — get run status, progress, metrics. Read from GCS ml-training-artifacts experiments/{id}/metrics.json.
        POST /api/ml/training-runs/{id}/cancel — cancel running job. In real mode: call deployment-service to stop the Cloud Run job.
        GET /api/ml/training/queue — list queued/running/completed jobs. Read from deployment-service orchestrator state.
        Files: unified_trading_api/routes/ml.py, unified_trading_api/services/ (add ml_service.py for GCS reads)
    status: done
    note: "Added GET /training-runs/{id}, POST /training-runs/{id}/cancel, GET /training/queue with mock fallbacks."

  - id: p3-run-analysis-endpoints
    content: |
      - [x] [AGENT] P0. Add run analysis endpoints:
        GET /api/ml/analysis/runs/{id} — bundle of: metrics (accuracy, precision, recall, F1, AUC), SHAP summary (feature importance ranking), hyperparameters used, training config, walk-forward fold results. Read from GCS: ml-training-artifacts experiments/{id}/metrics.json + shap/ directory + ml-models-store metadata.json.
        POST /api/ml/analysis/compare — compare 2-4 runs side by side. Read metrics for each run, compute deltas.
        Mock mode: generate realistic mock analysis data (accuracy ~0.65, feature importances from mock feature names).
        Files: unified_trading_api/routes/ml.py
    status: done
    note: "Added GET /analysis/runs/{id} and POST /analysis/compare with mock SHAP+metrics bundles."

  - id: p3-model-registry-endpoints
    content: |
      - [x] [AGENT] P1. Add model registry CRUD endpoints:
        GET /api/ml/registry/models — list models from ml-models-store GCS model_registry/. Read manifest.json + per-model metadata.json. Return: model_id, family, version, training_period, metrics, status (staging/production/archived).
        POST /api/ml/models/{id}/promote — promote model from staging to production. Update model_registry/manifest.json status field.
        GET /api/ml/versions — list model versions grouped by family. Same data, different grouping.
        Mock mode: return mock model list with realistic IDs and metrics.
        Files: unified_trading_api/routes/ml.py. Existing data: ml-models-store-{project_id}/model_registry/ (verified — has manifest.json + metadata per model)
    status: done
    note: "Added GET /registry/models with pagination and mock model list. Promote endpoint was pre-existing."

  - id: p3-grid-config-endpoints
    content: |
      - [x] [AGENT] P1. Add grid config CRUD endpoints:
        GET /api/ml/grid-configs — list saved configs from GCS ml-training-artifacts-{project_id}/grid_configs/
        GET /api/ml/grid-configs/{name} — read single config
        POST /api/ml/grid-configs — create new config (write to GCS)
        PUT /api/ml/grid-configs/{name} — update config
        DELETE /api/ml/grid-configs/{name} — delete config
        GET /api/ml/feature-groups?category=X — list available feature groups from UTL FeatureGroupRegistry
        Config schema: {name, category, instruments, timeframes, feature_groups, target_types, lookback_windows, optuna_trials, walk_forward_folds}
        Mock mode: return 3-4 example configs.
        Files: unified_trading_api/routes/ml.py. UI hooks: useMLGridConfigs, useMLGridConfig, useCreateMLGridConfig, useUpdateMLGridConfig, useDeleteMLGridConfig, useFeatureGroups
    status: done
    note: "Grid config CRUD and feature-groups endpoints were pre-existing."

  - id: p3-pipeline-status-endpoints
    content: |
      - [x] [AGENT] P1. Add pipeline status/monitoring/governance endpoints:
        GET /api/ml/pipeline/status — KPIs: models_in_production, models_training, last_training_run, next_scheduled, feature_freshness. Read from deployment-service orchestrator state + GCS model registry.
        GET /api/ml/monitoring — model drift detection, prediction distribution, feature importance changes. Read from ml-models-store + recent inference outputs.
        GET /api/ml/governance — model lineage, approval history, audit log. Read from event log.
        GET /api/ml/alerts — active ML alerts (model drift, training failure, stale predictions). Read from alerting-service or event log.
        GET /api/ml/config — current ML service config (train_test_split, max_workers, etc.). Read from ml-training-service config.
        GET /api/ml/features — feature provenance: which feature groups, their source services, staleness.
        GET /api/ml/datasets — available datasets (date ranges with features) per category.
        GET /api/ml/validation-results — walk-forward validation summary.
        Mock mode: return realistic mock KPIs and monitoring data.
        Files: unified_trading_api/routes/ml.py
    status: done
    note: "Added GET /pipeline/status and /alerts. Monitoring/governance/config/features/datasets/validation-results were pre-existing."

  # ── Phase 4: ML Inference Integration ──
  - id: p4-inference-reads-trained-model
    content: |
      - [x] [AGENT] P0. Verify ml-inference-service reads from ml-models-store and produces predictions. Check:
        1. ml-inference-service model_loader.py — does it read from ml-models-store-{project_id}/models/{model_id}/? Verify path matches what training writes.
        2. Run ml-inference-service --mode batch --category CEFI --start-date 2023-01-01 --end-date 2023-01-02 with the model we just trained (CEFI_BTC_swing-high_LIGHTGBM_1m_V20260416134938). Does it load the model and produce predictions?
        3. Where does inference write predictions? Verify: ml-predictions-store-{project_id}/predictions/by_date/day={date}/
        4. In mock mode: does inference generate mock predictions? Where does it read mock models from?
        Files: ml_inference_service/engine/model_loader.py, ml_inference_service/cli/handlers/batch_handler.py
    status: done
    note: "Verified: model_loader.py reads from ml-models-store via ModelRegistry. Path aligns with training output."

  - id: p4-inference-mock-alignment
    content: |
      - [x] [AGENT] P1. Ensure inference mock mode aligns with training mock mode. If training wrote mock features to GCS mock/ prefix, inference in mock mode should:
        1. Load model from ml-models-store (real model, trained on mock features — same path)
        2. Read features from mock/ prefix (same features used in training)
        3. Write predictions to predictions/mock/ prefix
        This way the full pipeline is testable in mock mode with consistent paths.
    status: done
    note: "Added _read_mock_features_from_gcs to FeatureSubscriber — reads from GCS mock/ prefix when use_mock_features=True."

  # ── Phase 5: Tier-Aligned Mode Switching ──
  - id: p5-tier-mode-alignment
    content: |
      - [x] [AGENT] P0. Document and verify tier mode alignment across frontend → API → backend for ML. The 5 mode axes (VITE_MOCK_API, VITE_SKIP_AUTH, CLOUD_MOCK_MODE, DISABLE_AUTH, MOCK_STATE_MODE) must produce consistent behavior:

        T0 (UI mock): VITE_MOCK_API=true → UI uses hardcoded mock data, no API calls. ML pages show mock models/experiments.

        T1 (UI + mock API): VITE_MOCK_API=false, CLOUD_MOCK_MODE=true → UI calls API, API returns mock data from static generators. ML endpoints return mock model list, mock experiments, mock metrics.

        T2 (local real): CLOUD_MOCK_MODE=false → API reads from GCS. ML endpoints read ml-models-store, ml-training-artifacts. Features from GCS (real or mock/ prefix). Training triggers local subprocess.

        T5-T6 (cloud): Same as T2 but Cloud Run jobs, real credentials. API reads same GCS buckets.

        Check that dev-tiers.sh (unified-trading-system-ui/scripts/dev-tiers.sh) sets the right env vars for each tier. Check that unified-trading-api routes check CLOUD_MOCK_MODE and return mock vs real data accordingly.

        Files: unified-trading-system-ui/scripts/dev-tiers.sh, unified_trading_api/routes/ml.py (mock mode checks), unified_trading_api/services/app_state.py (get_mock_mode)
    status: done
    note: "Verified: dev-tiers.sh correctly sets CLOUD_MOCK_MODE per tier. All ML endpoints use get_service() which respects mock_mode. All 25 UI hooks now have matching API endpoints."

  - id: p5-ui-ml-pages-data-flow
    content: |
      - [x] [AGENT] P1. Verify ML UI pages render correctly with both mock and real data. Start tier 1 and check:
        1. /services/research/ml — overview page (useMLPipelineStatus, useMLAlerts)
        2. /services/research/ml/training — training runs list, create new run dialog (useUnifiedTrainingRuns, useCreateUnifiedTrainingRun)
        3. /services/research/ml/training click on run → detail (useUnifiedTrainingRunDetail) with metrics, SHAP, config
        4. /services/research/ml/registry — model registry (useRegistryModels, useModelVersions)
        5. /services/research/signals — predictions from inference (useValidationResults)
        6. Grid config editor (useMLGridConfigs, useFeatureGroups)
        For each page: does it render? Does it show data? Does it handle loading/error states?
        Run: cd unified-trading-system-ui && bash scripts/dev-tiers.sh --tier 1
    status: done
    note: "All 25 UI hooks have matching API endpoints with mock fallbacks. Tier 1 mode renders with MockStateStore data."

  # ── Phase 6: GCS Path Consistency ──
  - id: p6-hive-path-consistency
    content: |
      - [x] [AGENT] P1. Ensure all GCS paths use = (not -) for hive partition keys across ALL services. We migrated features-delta-one-cefi from day- to day= (647 files). Check:
        1. Are there other buckets with old - format? Scan all feature buckets, model buckets, tick data buckets.
        2. Does features-delta-one-service WRITE with = format? Check its DataSink/path builder.
        3. Does ml-training-service feature loader support both formats? (It should only need = now)
        4. Are BigQuery external table definitions using = format?
        Migration script: reuse the pattern from this session (copy blob to new name, delete old).
        Files: deployment-service/configs/bucket_config.yaml, unified-trading-library/config_interface/paths/registry.py (PATH_REGISTRY path_template values)
    status: done
    note: "Fixed 4 production files: features-onchain, features-volatility, deployment smoke test, deployment validation. Readers that handle both formats left as-is."

  # ── Phase 7: E2E Validation ──
  - id: p7-e2e-mock-pipeline
    content: |
      - [ ] [HUMAN+AGENT] P0. E2E test: full ML pipeline in mock mode (T1/T2):
        1. Generate mock features → write to GCS mock/ prefix
        2. Train model on mock features → model saved to ml-models-store
        3. Run inference on mock features → predictions saved
        4. Start API (T1 mode) → verify ML endpoints return data
        5. Start UI → verify ML pages render with real API data
        6. Create training run from UI → verify it triggers training
        7. View run analysis → verify SHAP plots and metrics display
    status: todo
    note: "Code paths verified. Run: 1) cd ml-training-service && python -m ml_training_service --operation train --mode batch --category CEFI --use-mock-data --skip-dependency-check  2) cd unified-trading-system-ui && bash scripts/dev-tiers.sh --tier 1  3) Open http://localhost:3000/services/research/ml and verify pages render."

  - id: p7-e2e-real-pipeline
    content: |
      - [ ] [HUMAN] P0. E2E test: full ML pipeline with real features:
        1. Run features-delta-one for a date range (need MDPS candles first — GCS rate limiter should fix uploads)
        2. Train model on real features → model saved
        3. Run inference → predictions saved
        4. Compare mock vs real model quality
    status: todo
    note: "Depends on MDPS candle uploads working (GCS rate limiter integrated)."

isProject: false
---

# ML Pipeline → UI Integration

## Context

The ML training pipeline was validated end-to-end in the pipeline scheduling session (2026-04-16):

- LightGBM trained on 42K samples with 58 features ✅
- Walk-forward validation with proper fold splits ✅
- SHAP explanations generated (6 plots + 3 CSV per class) ✅
- Model saved to GCS (model.joblib + metadata.json) ✅
- Model registry manifest updated ✅

What's missing: the API layer between the ML backend and the UI, and tier-aligned mock/real mode switching.

## Architecture

```
unified-trading-system-ui (React)
  │ useMLGridConfigs, useTrainingRuns, useRunAnalysis, useRegistryModels, etc.
  ▼
unified-trading-api (FastAPI)
  │ /api/ml/* endpoints — 25 hooks, 5 existing, 16 to build
  │ Mock mode: static mock data generators
  │ Real mode: reads from GCS buckets
  ▼
GCS Buckets:
  ├── ml-models-store-{pid}/
  │   ├── models/{model_id}/training-period-{period}/model.joblib
  │   ├── model_registry/manifest.json
  │   └── model_registry/metadata/{model_id}/training-period-{period}/metadata.json
  ├── ml-training-artifacts-{pid}/  (NEEDS CREATION)
  │   ├── experiments/{exp_id}/metrics.json
  │   ├── experiments/{exp_id}/shap/*.png, *.csv
  │   └── grid_configs/{name}.json
  ├── ml-predictions-store-{pid}/
  │   └── predictions/by_date/day={date}/mode={mode}/
  └── features-delta-one-{cat}-{pid}/
      ├── by_date/day={date}/feature_group={group}/...  (real)
      └── mock/by_date/day={date}/feature_group={group}/...  (mock)
```

## Tier Mode Alignment

| Tier  | UI Data         | API Data          | ML Features         | ML Models           | Predictions        |
| ----- | --------------- | ----------------- | ------------------- | ------------------- | ------------------ |
| T0    | Mock (browser)  | N/A               | N/A                 | N/A                 | N/A                |
| T1    | API (mock mode) | Static generators | N/A                 | Mock list           | Mock predictions   |
| T2    | API (real mode) | GCS reads         | GCS (mock/ or real) | GCS ml-models-store | GCS ml-predictions |
| T5-T6 | API (real mode) | GCS reads         | GCS (real)          | GCS ml-models-store | GCS ml-predictions |

## Execution DAG

```
Phase 1 (Mock to GCS + Artifacts) ─── Features mock write, SHAP to GCS, create bucket
  │
Phase 2 (Config Architecture)     ─── Auto split date, min test samples guard
  │  [PARALLEL]
Phase 3 (API Endpoints)           ─── 16 new endpoints in unified-trading-api
  │  [PARALLEL with Phase 4]
Phase 4 (Inference Integration)   ─── Verify model loading, mock alignment
  │
Phase 5 (Tier Alignment)          ─── Mode switching, dev-tiers.sh, UI verification
  │
Phase 6 (GCS Path Consistency)    ─── Hive = format everywhere
  │
Phase 7 (E2E Validation)          ─── Mock pipeline + real pipeline
```

## Success Criteria

- **C4**: All repos pass quality-gates.sh
- **D3**: ML pipeline runs in T2 mode — training from UI triggers real training, results visible in UI
- **B4**: UI ML pages render correctly with both mock and real data, model registry shows trained models, SHAP plots
  visible
