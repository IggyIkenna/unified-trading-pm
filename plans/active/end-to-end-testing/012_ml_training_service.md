---
title: "E2E Test: ml-training-service"
service: ml-training-service
date: 2026-03-22
status: pending
---

# E2E Test: ml-training-service

Follows `procedure.md`. Pipeline position: #12 (L4 ML layer). **BATCH ONLY** -- ML training never runs in live mode.

## Upstream Dependencies

- ALL feature services (delta-one, volatility, onchain, calendar, cross-instrument, multi-timeframe, sports, commodity)
  -- feature parquet files in GCS per category/timeframe
- instruments-service -- instrument registry for resolving instrument IDs

## Downstream Consumers

- ml-inference-service -- consumes model artifacts (pickled LightGBM models, feature importance JSON, metrics) from
  `model_artifacts_registry` in GCS

## Operations

| Operation             | What it does                                       | Expected output                                                     |
| --------------------- | -------------------------------------------------- | ------------------------------------------------------------------- |
| `train`               | Train LightGBM model(s) for specified instruments  | Pickled model + feature importance + metrics to GCS                 |
| `evaluate`            | Evaluate existing model on held-out data           | Evaluation metrics JSON to GCS                                      |
| `grid-search`         | Hyperparameter grid search                         | Best params JSON + all trial results to GCS                         |
| `pre-selection`       | Feature pre-selection (stage 1)                    | Selected feature list to GCS                                        |
| `hyperparameter-grid` | Optuna hyperparameter tuning (stage 2)             | Tuned params to GCS                                                 |
| `final-training`      | Final model training with selected features+params | Production model artifact to GCS                                    |
| `pipeline`            | Full 5+1 phase uniform pipeline                    | All of the above in sequence (depth controlled by --pipeline-depth) |

## Key CLI Arguments (beyond standard axes)

| Argument                             | Type       | Default          | Notes                                                |
| ------------------------------------ | ---------- | ---------------- | ---------------------------------------------------- |
| `--start-date` / `--end-date`        | date (req) | --               | Training window (YYYY-MM-DD), both required          |
| `--asset-group`                      | choice     | `ALL`            | `CEFI`, `TRADFI`, `ALL`                              |
| `--stage`                            | choice     | `full`           | `feature-selection`, `hyperparameter-tuning`, `full` |
| `--instruments`                      | list       | all per category | `BTC ETH SOL SPY` (shortcuts)                        |
| `--timeframes`                       | list       | `1h 4h`          | `1m 5m 15m 1h 4h 1d`                                 |
| `--target-types`                     | list       | `ALL`            | `swing_high`, `swing_low`, `ALL`                     |
| `--swing-lookback-windows`           | int list   | `5 10 20`        | From `[2, 3, 5, 10, 20, 50]`                         |
| `--task-type`                        | choice     | `classification` | `classification` or `regression`                     |
| `--pipeline-depth`                   | int        | `3`              | `3` = phases 1-3, `5` = 1-5, `6` = 1-6               |
| `--walk-forward-folds`               | int        | `5`              | Min 2                                                |
| `--skip-walk-forward`                | flag       | false            | Use simple train/test split                          |
| `--optuna-trials`                    | int        | `50`             | Hyperparameter search budget                         |
| `--feature-selection-samples`        | int        | `25000`          | Samples for feature selection                        |
| `--target-feature-count`             | int        | `300`            | Features after selection                             |
| `--max-workers`                      | int        | `4`              | Parallel training workers                            |
| `--use-mock-data`                    | flag       | false            | Skip GCS, use generated mock data                    |
| `--output-dir`                       | str        | GCS              | Local output override                                |
| `--experiment-id`                    | str        | auto-generated   | Experiment tracking ID                               |
| `--config-file`                      | str        | none             | JSON config (local or GCS path)                      |
| `--grid-config`                      | str        | none             | Named grid config from GCS                           |
| `--model-type`                       | str        | `lightgbm`       | Base model type for pipeline                         |
| `--strict-exit` / `--no-strict-exit` | flag       | true             | Exit 1 if ANY variant fails                          |
| `--skip-dependency-check`            | flag       | false            | Skip upstream dep validation                         |

## Test Matrix

### Phase 1: Startup Validation

| #   | Env vars                                                                        | Expected                  | Status |
| --- | ------------------------------------------------------------------------------- | ------------------------- | ------ |
| 1.1 | `CLOUD_PROVIDER=gcp ENVIRONMENT=dev CLOUD_MOCK_MODE=false TESTNET_MODE=mainnet` | OK                        |        |
| 1.2 | `CLOUD_PROVIDER=local ENVIRONMENT=dev CLOUD_MOCK_MODE=true`                     | OK                        |        |
| 1.3 | `CLOUD_PROVIDER=gcp ENVIRONMENT=staging TESTNET_MODE=testnet`                   | OK                        |        |
| 1.4 | `CLOUD_PROVIDER=azure`                                                          | STARTUP_VALIDATION_FAILED |        |
| 1.5 | `TESTNET_MODE=sandbox`                                                          | STARTUP_VALIDATION_FAILED |        |
| 1.6 | `CLOUD_MOCK_MODE=maybe`                                                         | Pydantic validation error |        |
| 1.7 | `--mode live` rejected                                                          | Error: mode must be batch |        |

### Phase 2: Dry-Run (batch, real data, no writes)

Use short date range and single instrument to keep runs fast on M5 MacBook.

| #   | Operation     | Category | Flags                                                                                                           | Expected                                 | Status |
| --- | ------------- | -------- | --------------------------------------------------------------------------------------------------------------- | ---------------------------------------- | ------ |
| 2.1 | train         | CEFI     | `--instruments BTC --timeframes 1h --start-date 2025-06-01 --end-date 2025-06-15 --dry-run --skip-walk-forward` | Config validated, no GCS writes          |        |
| 2.2 | train         | TRADFI   | `--instruments SPY --timeframes 1h --start-date 2025-06-01 --end-date 2025-06-15 --dry-run --skip-walk-forward` | Config validated, no GCS writes          |        |
| 2.3 | evaluate      | CEFI     | `--instruments BTC --timeframes 1h --start-date 2025-06-01 --end-date 2025-06-15 --dry-run`                     | Needs existing model, validates config   |        |
| 2.4 | pipeline      | CEFI     | `--instruments BTC --timeframes 1h --pipeline-depth 3 --start-date 2025-06-01 --end-date 2025-06-15 --dry-run`  | Pipeline config validated, no GCS writes |        |
| 2.5 | pre-selection | CEFI     | `--instruments BTC --timeframes 1h --start-date 2025-06-01 --end-date 2025-06-15 --dry-run`                     | Feature selection config validated       |        |
| 2.6 | grid-search   | CEFI     | `--instruments BTC --timeframes 1h --optuna-trials 5 --start-date 2025-06-01 --end-date 2025-06-15 --dry-run`   | Grid search config validated             |        |

### Phase 3: Real Writes (dev, small dataset first)

**COMPUTE WARNING:** ML training is CPU/memory-heavy. Start with the smallest possible config:

- Single instrument (BTC)
- Single timeframe (1h)
- Short date range (2 weeks)
- `--skip-walk-forward` (no cross-validation)
- `--feature-selection-samples 1000` (reduced)
- `--optuna-trials 3` (minimal)
- `--max-workers 2` (MacBook-safe)

| #   | Operation | Category | Config                                     | GCS check                            | Status |
| --- | --------- | -------- | ------------------------------------------ | ------------------------------------ | ------ |
| 3.1 | train     | CEFI     | BTC, 1h, 2-week window, skip-walk-forward  | Model artifact in GCS model registry |        |
| 3.2 | train     | TRADFI   | SPY, 1h, 2-week window, skip-walk-forward  | Model artifact in GCS model registry |        |
| 3.3 | pipeline  | CEFI     | BTC, 1h, pipeline-depth 3, reduced samples | All pipeline outputs in GCS          |        |
| 3.4 | evaluate  | CEFI     | BTC, 1h (requires model from 3.1)          | Evaluation metrics JSON in GCS       |        |

### Phase 4: Category Sweep

**Note:** ml-training-service supports `CEFI`, `TRADFI`, and `ALL` only. DEFI and SPORTS categories are NOT in the
parser's CATEGORIES list. The service should reject or handle gracefully.

| #   | Category   | Expected instruments               | Expected behavior                          | Status |
| --- | ---------- | ---------------------------------- | ------------------------------------------ | ------ |
| 4.1 | CEFI       | BTC, ETH, SOL (3 instruments)      | Train models, artifacts to GCS             |        |
| 4.2 | TRADFI     | SPY (1 instrument)                 | Train models, artifacts to GCS             |        |
| 4.3 | ALL        | BTC, ETH, SOL, SPY (4 instruments) | Train all, artifacts to GCS                |        |
| 4.4 | DEFI       | Not in CATEGORIES list             | Rejected by argparse or handled gracefully |        |
| 4.5 | SPORTS     | Not in CATEGORIES list             | Rejected by argparse or handled gracefully |        |
| 4.6 | PREDICTION | Not in CATEGORIES list             | Rejected by argparse or handled gracefully |        |

After each run, **verify model artifacts in GCS**:

```python
from google.cloud import storage
client = storage.Client(project='central-element-323112')
bucket = client.bucket('<model-artifacts-bucket>')
blobs = list(bucket.list_blobs(prefix='models/', max_results=20))
print(f'Model artifacts: {len(blobs)}')
for b in blobs[:10]:
    print(f'  {b.name} ({b.size:,} bytes)')
```

### Phase 5: Live Mode

**NOT APPLICABLE.** ml-training-service is batch-only. `MODES = ["batch"]` in parser.py.

| #   | What                    | Expected                              | Status |
| --- | ----------------------- | ------------------------------------- | ------ |
| 5.1 | `--mode live` rejected  | argparse error: invalid choice 'live' |        |
| 5.2 | `--mode batch` accepted | Normal batch execution                |        |

#### Phase 5b: Mock/Real A/B Comparison

Run the same small training job in both mock and real mode, compare outputs:

| #    | What                   | Mock mode                                                  | Real mode                                   | Status |
| ---- | ---------------------- | ---------------------------------------------------------- | ------------------------------------------- | ------ |
| 5b.1 | train BTC 1h (small)   | `CLOUD_MOCK_MODE=true --use-mock-data`                     | `CLOUD_MOCK_MODE=false` (real GCS features) |        |
| 5b.2 | Output structure match | Same artifact structure (model, metrics, importance)       | Same structure, different values            |        |
| 5b.3 | Mock pipeline redirect | `Settings().is_mock_mode()` triggers `run_mock_pipeline()` | Normal ServiceCLI path                      |        |

### Phase 6: Mock Mode (scenario testing)

| #   | Scenario                    | What it tests                                   | Expected                                        | Status |
| --- | --------------------------- | ----------------------------------------------- | ----------------------------------------------- | ------ |
| 6.1 | `--use-mock-data`           | Mock data provider generates synthetic features | Training completes with mock data, local output |        |
| 6.2 | `CLOUD_MOCK_MODE=true`      | Full mock pipeline via `run_mock_pipeline()`    | Mock pipeline runs, no GCS credentials needed   |        |
| 6.3 | Missing upstream features   | Feature files missing in GCS for date range     | Clear error: "upstream features not found"      |        |
| 6.4 | Corrupted feature file      | Feature parquet with wrong schema               | Graceful error, not a crash                     |        |
| 6.5 | Empty feature file          | 0-row parquet for an instrument                 | Skip instrument, log warning, continue others   |        |
| 6.6 | `--skip-dependency-check`   | Bypass upstream dependency validation           | Proceeds without checking feature freshness     |        |
| 6.7 | `--no-fail-on-missing-deps` | Warn but continue on missing upstream features  | Warning logged, continues with available data   |        |
| 6.8 | config_source check         | `CLOUD_MOCK_MODE=true CLOUD_PROVIDER=local`     | `config_source=local`, no GCS reads             |        |

### Phase 7: Observability

| #   | Check                      | Expected                                                | Status |
| --- | -------------------------- | ------------------------------------------------------- | ------ |
| 7.1 | ServiceRuntime log line    | All dimensions logged (operation, mode=batch, category) |        |
| 7.2 | UEI events                 | STARTED, COMPLETED per training job                     |        |
| 7.3 | Experiment tracking        | experiment_id in logs and GCS metadata                  |        |
| 7.4 | Dry-run warning            | "DRY RUN" + "UCI dry-run mode ACTIVE" logged            |        |
| 7.5 | Shard-level isolation      | One instrument failure doesn't crash others             |        |
| 7.6 | Memory watchdog            | Active for large training jobs                          |        |
| 7.7 | Training metrics logged    | Accuracy, loss, feature importance summary in logs      |        |
| 7.8 | Walk-forward fold progress | Per-fold metrics logged when walk-forward enabled       |        |

## Known Issues Audit

Check these patterns (from instruments-service E2E findings):

| Pattern                      | What to check                                                        | Status |
| ---------------------------- | -------------------------------------------------------------------- | ------ |
| `load_dotenv(override=True)` | Must be `override=False` -- shell intent wins                        |        |
| `--dry-run` enforcement      | Verify no GCS writes when dry-run active                             |        |
| Bucket resolution            | Uses `get_bucket_name()` not `routing_key=`                          |        |
| asyncio nesting              | ServiceCLI wraps `asyncio.run()` -- handlers must not nest           |        |
| Category routing             | Unsupported categories (DEFI, SPORTS, PREDICTION) handled explicitly |        |
| `os.getenv()` usage          | Should use `UnifiedCloudConfig`, not raw `os.getenv()`               |        |
| `.env` credential paths      | No placeholder credential paths in `.env`                            |        |
| Strict exit behavior         | `--strict-exit` (default) exits 1 on ANY variant failure             |        |
| Mock mode redirect           | `Settings().is_mock_mode()` check runs before ServiceCLI build       |        |

## AWS Testing

| #   | What                              | Expected                         | Status |
| --- | --------------------------------- | -------------------------------- | ------ |
| A.1 | `CLOUD_PROVIDER=aws` (no creds)   | Startup validation fails cleanly |        |
| A.2 | `CLOUD_PROVIDER=aws` (with creds) | S3 model artifact storage works  |        |

## Frontend API Surface

ml-training-service feeds the ML Training UI via these API endpoints:

| Endpoint                | What it provides                              | Verify                            |
| ----------------------- | --------------------------------------------- | --------------------------------- |
| `GET /ml/experiments`   | List of training experiments with metadata    | experiment_id, status, timestamps |
| `GET /ml/training-jobs` | Training job history with params and results  | operation, category, metrics      |
| `GET /ml/models`        | Model registry (trained models with versions) | model_id, version, accuracy, size |

After a successful training run, verify these endpoints return the new experiment/model.

## Issues Found

(logged in `plans/active/issues/service_control_surface_issues_2026_03_21.md`)

| Issue | Severity | Fixed? |
| ----- | -------- | ------ |
|       |          |        |

## Next Service

After ml-training-service passes all phases -> proceed to `013_ml_inference_service.md`
