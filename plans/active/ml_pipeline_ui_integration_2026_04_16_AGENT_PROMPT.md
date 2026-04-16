# Agent Prompt: ML Pipeline → UI Integration

Copy this entire prompt to start a new Claude Code session.

---

## Task

Execute the plan at `unified-trading-pm/plans/active/ml_pipeline_ui_integration_2026_04_16.plan.md`. This connects the ML training pipeline (which is proven working) to the UI through API endpoints, with tier-aligned mock/real mode switching.

## Critical Context

Read these FIRST before any code changes:
1. `.claude/CLAUDE.md` — workspace rules
2. The plan file above — 7 phases, 15 items with exact file paths
3. Memory file: check `memory/project_ml_ui_integration_handoff_2026_04_16.md` in the Claude memory directory for detailed context on every item including GCS bucket names, file paths, bugs found, and what was already fixed

## What's Already Done

The ML training pipeline was validated end-to-end (2026-04-16):
- LightGBM trains on 42K samples with 58 features ✅
- Walk-forward validation with 2 folds ✅
- SHAP explanations generated (6 plots + 3 CSVs) ✅
- Model saved to GCS `ml-models-store-central-element-323112` ✅
- Classification report with accuracy metrics ✅

8 bugs were fixed in the ML pipeline during E2E testing. All committed. See memory for details.

## What Needs Doing

### Phase 1 (Do First — Prerequisites):
1. Write mock features to GCS `mock/` prefix (not just in-memory)
2. Write SHAP artifacts to GCS (not local /tmp/)
3. Create `ml-training-artifacts-central-element-323112` bucket
4. Fix mock swing target distribution (move `filter_to_swing_events` before `_resolve_selected_features`)

### Phase 2 (Config):
5. Make `train_test_split_date` default to "auto" (80% of date range)
6. Add MIN_TEST_SAMPLES guard to walk-forward splitter

### Phase 3 (Bulk Work — 16 API Endpoints):
7. Add all missing ML endpoints to `unified-trading-api/routes/ml.py`
   - Training job management (POST/GET/cancel)
   - Run analysis (SHAP + metrics bundle, compare runs)
   - Model registry (list, promote, versions)
   - Grid config CRUD
   - Pipeline status, monitoring, governance, alerts, config, features, datasets, validation

   Pattern: check `get_mock_mode()` — mock returns static data, real reads from GCS.
   UI hooks are in `unified-trading-system-ui/hooks/api/use-ml-models.ts` (25 hooks, 5 existing).

### Phase 4 (Inference):
8. Verify ml-inference-service loads trained model and produces predictions
9. Align inference mock mode with training mock mode (read from `mock/` GCS prefix)

### Phase 5 (Tier Alignment):
10. Verify dev-tiers.sh sets correct env vars for ML at each tier
11. Test ML UI pages render with mock and real API data

### Phase 6 (GCS Paths):
12. Audit all buckets for old `day-` format, migrate to `day=`

### Phase 7 (E2E):
13. Full mock pipeline: generate → train → infer → API → UI
14. Full real pipeline (after MDPS candle uploads work)

## Key File Locations

| What | Path |
|------|------|
| ML training handler | `ml-training-service/ml_training_service/cli/handlers/train_handler.py` |
| Training orchestrator | `ml-training-service/ml_training_service/app/core/training_orchestrator.py` |
| Mock feature generator | `ml-training-service/ml_training_service/app/core/mock_feature_generator.py` |
| Feature provider (mock path) | `ml-training-service/ml_training_service/app/core/cloud_feature_provider.py` |
| SHAP explainer | `ml-training-service/ml_training_service/app/training/shap_explainer.py` |
| Data preparation (split) | `ml-training-service/ml_training_service/app/training/data_preparation.py` |
| Model trainer (eval) | `ml-training-service/ml_training_service/app/training/model_trainer.py` |
| Walk-forward validator | `ml-training-service/ml_training_service/app/core/walk_forward_validator.py` |
| ML API routes | `unified-trading-api/unified_trading_api/routes/ml.py` |
| UI ML hooks | `unified-trading-system-ui/hooks/api/use-ml-models.ts` |
| UI ML pages | `unified-trading-system-ui/app/(platform)/services/research/ml/` |
| Deployment ML API | `deployment-service/deployment_service/api/routes/ml_experiments.py` |
| Inference model loader | `ml-inference-service/ml_inference_service/engine/model_loader.py` |
| Inference batch handler | `ml-inference-service/ml_inference_service/cli/handlers/batch_handler.py` |
| Tier startup script | `unified-trading-system-ui/scripts/dev-tiers.sh` |
| UTL Feature Group Registry | `unified-trading-library/unified_trading_library/feature_service_base/feature_group_registry.py` |

## GCS Buckets (project: central-element-323112)

| Bucket | Status | Contains |
|--------|--------|----------|
| `ml-models-store-central-element-323112` | EXISTS | model.joblib, metadata.json, manifest.json |
| `ml-training-artifacts-central-element-323112` | NEEDS CREATION | experiments/, grid_configs/, shap/ |
| `ml-predictions-store-central-element-323112` | EXISTS | predictions/by_date/ |
| `features-delta-one-cefi-central-element-323112` | EXISTS (migrated) | by_date/day=.../feature_group=.../ |

## Rules Reminder

- `uv pip install` not `pip install`
- No `os.getenv()` — use `UnifiedCloudConfig`
- No `try/except ImportError`
- `logger.warning("%s", msg)` not `logger.warning(msg)`
- `bash scripts/quality-gates.sh` for tests (per-repo .venv)
- `bash scripts/quickmerge.sh "message" --agent` for commits
- Editable installs — code changes take effect immediately
- Each subdirectory is an independent git repo

## Execution Strategy

Phases 1-2 first (prerequisites). Then Phase 3 in parallel with Phase 4 (biggest work). Phase 5 after Phase 3. Phase 7 last.

For Phase 3 (16 endpoints): implement mock mode first (static responses matching UI hook expectations), then wire real mode (GCS reads). Test each endpoint individually before integration testing.
