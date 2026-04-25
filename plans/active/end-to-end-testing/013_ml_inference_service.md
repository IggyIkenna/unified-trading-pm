---
title: "E2E Test: ml-inference-service"
service: ml-inference-service
date: 2026-03-22
status: pending
---

# E2E Test: ml-inference-service

Follows `procedure.md`. Pipeline position: #13 (L4 ML layer). Supports both **batch** and **live** modes.

## Upstream Dependencies

- ml-training-service -- model artifacts (pickled LightGBM models) from `model_artifacts_registry` in GCS
- ALL feature services (delta-one, volatility, onchain, calendar, cross-instrument, multi-timeframe, sports, commodity)
  -- live features for inference (batch: GCS parquet; live: PubSub)

## Downstream Consumers

- strategy-service -- consumes predictions via GCS (batch) or PubSub (live)

## Operations

| Operation | What it does                             | Expected output                          |
| --------- | ---------------------------------------- | ---------------------------------------- |
| `infer`   | Load model(s), run inference on features | Prediction parquet/JSON to GCS or PubSub |

Single operation, dual mode:

- **batch**: reads feature parquet from GCS, writes prediction parquet to GCS
- **live**: subscribes to PubSub for real-time features, emits predictions via PubSub. Supports hot-reload of model
  versions without restart (human approval via Telegram triggers `ModelPromotionSubscriber`).

## Key CLI Arguments (beyond standard axes)

| Argument                      | Type        | Default              | Notes                                                           |
| ----------------------------- | ----------- | -------------------- | --------------------------------------------------------------- |
| `--start-date` / `--end-date` | date        | --                   | Required for batch mode only                                    |
| `--asset-group`               | multi       | from MarketCategory  | `CEFI`, `TRADFI`, `DEFI`, `PREDICTION`, `ALL` (excludes SPORTS) |
| `--instrument-ids`            | list        | default per category | `BTC ETH SOL SPY` (shortcuts) or full IDs                       |
| `--timeframes`                | list        | `1h 4h`              | Timeframes to run inference on                                  |
| `--target-types`              | choice list | `ALL`                | `swing_high`, `swing_low`, `ALL`                                |
| `--model-ids`                 | list        | auto (latest)        | Specific model IDs to load                                      |
| `--model-versions`            | list        | auto (latest)        | Specific model versions                                         |
| `--project-id`                | str         | from config          | GCP project ID override                                         |
| `--environment`               | choice      | `production`         | `local-dev`, `staging`, `production`                            |
| `--output-dir`                | str         | GCS                  | Local output override                                           |
| `--max-workers`               | int         | `4`                  | Parallel inference workers                                      |
| `--max-results`               | int         | none                 | Max output files per shard                                      |
| `--run-tag`                   | str         | `batch`              | GCS prefix tag (e.g. `t1-recon`)                                |
| `--verbose`                   | flag        | false                | Progress bars                                                   |
| `--skip-dependency-check`     | flag        | false                | Skip upstream dep validation                                    |
| `--no-fail-on-missing-deps`   | flag        | default true         | Warn only on missing upstream                                   |

## Test Matrix

### Phase 1: Startup Validation

| #   | Env vars                                                                        | Expected                    | Status |
| --- | ------------------------------------------------------------------------------- | --------------------------- | ------ |
| 1.1 | `CLOUD_PROVIDER=gcp ENVIRONMENT=dev CLOUD_MOCK_MODE=false TESTNET_MODE=mainnet` | OK                          |        |
| 1.2 | `CLOUD_PROVIDER=local ENVIRONMENT=dev CLOUD_MOCK_MODE=true`                     | OK                          |        |
| 1.3 | `CLOUD_PROVIDER=gcp ENVIRONMENT=staging TESTNET_MODE=testnet`                   | OK                          |        |
| 1.4 | `CLOUD_PROVIDER=azure`                                                          | STARTUP_VALIDATION_FAILED   |        |
| 1.5 | `TESTNET_MODE=sandbox`                                                          | STARTUP_VALIDATION_FAILED   |        |
| 1.6 | `CLOUD_MOCK_MODE=maybe`                                                         | Pydantic validation error   |        |
| 1.7 | `InferHandler.validate_config()` with valid buckets                             | "Startup validation passed" |        |
| 1.8 | `InferHandler.validate_config()` with inaccessible bucket                       | Returns False, logged       |        |

### Phase 2: Dry-Run (batch, real data, no writes)

**Prerequisite:** Models must exist in GCS from ml-training-service E2E (012). If not, use `--skip-dependency-check`.

| #   | Operation | Category | Flags                                                                                                    | Expected                                     | Status |
| --- | --------- | -------- | -------------------------------------------------------------------------------------------------------- | -------------------------------------------- | ------ |
| 2.1 | infer     | CEFI     | `--instrument-ids BTC --timeframes 1h --start-date 2025-06-01 --end-date 2025-06-07 --dry-run`           | Config validated, model found, no GCS writes |        |
| 2.2 | infer     | TRADFI   | `--instrument-ids SPY --timeframes 1h --start-date 2025-06-01 --end-date 2025-06-07 --dry-run`           | Config validated, no GCS writes              |        |
| 2.3 | infer     | ALL      | `--timeframes 1h --start-date 2025-06-01 --end-date 2025-06-07 --dry-run`                                | All instruments resolved, no GCS writes      |        |
| 2.4 | infer     | CEFI     | `--instrument-ids BTC --target-types swing_high --start-date 2025-06-01 --end-date 2025-06-07 --dry-run` | Single target type validated                 |        |

### Phase 3: Real Writes (dev, batch mode)

| #   | Operation | Category | Config                             | GCS check                                    | Status |
| --- | --------- | -------- | ---------------------------------- | -------------------------------------------- | ------ |
| 3.1 | infer     | CEFI     | BTC, 1h, 1-week window             | Prediction parquet in GCS predictions bucket |        |
| 3.2 | infer     | TRADFI   | SPY, 1h, 1-week window             | Prediction parquet in GCS                    |        |
| 3.3 | infer     | ALL      | All instruments, 1h, 1-week window | Predictions for all instruments in GCS       |        |
| 3.4 | infer     | CEFI     | BTC, 1h, `--run-tag t1-recon`      | Predictions under `t1-recon/` prefix         |        |

After each run, **verify predictions in GCS**:

```python
from google.cloud import storage
client = storage.Client(project='central-element-323112')
bucket = client.bucket('<predictions-bucket>')
blobs = list(bucket.list_blobs(prefix='batch/', max_results=20))
print(f'Prediction files: {len(blobs)}')
for b in blobs[:10]:
    print(f'  {b.name} ({b.size:,} bytes)')
```

### Phase 4: Category Sweep

**Note:** ml-inference-service categories are derived from `MarketCategory` excluding SPORTS. Includes CEFI, TRADFI,
DEFI, PREDICTION, ALL.

| #   | Category   | Expected instruments                | Expected behavior                            | Status |
| --- | ---------- | ----------------------------------- | -------------------------------------------- | ------ |
| 4.1 | CEFI       | BTC, ETH, SOL (3 instruments)       | Load CEFI models, produce predictions        |        |
| 4.2 | TRADFI     | SPY (1 instrument)                  | Load TRADFI model, produce predictions       |        |
| 4.3 | DEFI       | Default DEFI instruments            | Load DEFI models (may be empty if no models) |        |
| 4.4 | PREDICTION | Default PREDICTION instruments      | Load PREDICTION models (may be empty)        |        |
| 4.5 | ALL        | All instruments from all categories | Load all models, produce all predictions     |        |
| 4.6 | SPORTS     | Excluded from CATEGORIES list       | Rejected by argparse or handled gracefully   |        |

### Phase 5: Live Mode

ml-inference-service supports live mode. In live mode it:

1. Subscribes to PubSub for real-time feature updates
2. Loads models from GCS model registry
3. Runs inference on each incoming feature batch
4. Publishes predictions to PubSub for strategy-service
5. `ModelPromotionSubscriber` listens for model promotion events (hot-reload)

| #   | What                                               | Expected                                                         | Status |
| --- | -------------------------------------------------- | ---------------------------------------------------------------- | ------ |
| 5.1 | `--operation infer --mode live --asset-group CEFI` | Subscribes to PubSub, loads models, waits for features           |        |
| 5.2 | Model loading                                      | Latest model version loaded from GCS model registry              |        |
| 5.3 | PubSub subscription                                | Feature subscription established, logs "subscribed"              |        |
| 5.4 | Event logging                                      | UEI events: STARTED, VALIDATION_STARTED/COMPLETED, per-inference |        |
| 5.5 | Graceful shutdown                                  | Ctrl-C -> STOPPED event, clean PubSub unsubscribe                |        |
| 5.6 | Model hot-reload                                   | `ModelPromotionSubscriber` active, logs "subscriber started"     |        |
| 5.7 | GracefulShutdownHandler                            | Registered, handles SIGTERM/SIGINT                               |        |
| 5.8 | Pre-crash checkpoint                               | `register_pre_crash_handlers()` called                           |        |

#### Phase 5b: Mock/Real A/B Comparison

| #    | What                   | Mock mode                                                          | Real mode                           | Status |
| ---- | ---------------------- | ------------------------------------------------------------------ | ----------------------------------- | ------ |
| 5b.1 | infer BTC 1h (batch)   | `CLOUD_MOCK_MODE=true` triggers `run_mock_pipeline()`              | `CLOUD_MOCK_MODE=false` (real GCS)  |        |
| 5b.2 | Output structure match | Same prediction structure (instrument, target, probability)        | Same structure, real model outputs  |        |
| 5b.3 | Mock pipeline redirect | `InferenceConfig().is_mock_mode()` triggers mock path              | Normal ServiceCLI/InferHandler path |        |
| 5b.4 | Live mock vs real      | Mock mode returns early with `{"status": "ok", "mock_mode": True}` | Real PubSub subscription            |        |

### Phase 6: Mock Mode (scenario testing)

| #   | Scenario                    | What it tests                                      | Expected                                      | Status |
| --- | --------------------------- | -------------------------------------------------- | --------------------------------------------- | ------ |
| 6.1 | `CLOUD_MOCK_MODE=true`      | Full mock pipeline via `run_mock_pipeline()`       | Mock predictions generated, no GCS needed     |        |
| 6.2 | Missing model artifacts     | Model not found in GCS for instrument/version      | Clear error: "model not found", not a crash   |        |
| 6.3 | Stale model version         | Model exists but is older than feature schema      | Warning logged, inference proceeds            |        |
| 6.4 | Missing upstream features   | Feature parquet not available for date range       | Clear error, skip instrument, continue others |        |
| 6.5 | Corrupted model pickle      | Invalid/truncated pickle file in GCS               | Graceful error, shard-level isolation         |        |
| 6.6 | Feature schema mismatch     | Features have different columns than model expects | Clear error with column diff, not a crash     |        |
| 6.7 | `--skip-dependency-check`   | Bypass upstream dependency validation              | Proceeds without checking feature freshness   |        |
| 6.8 | `--no-fail-on-missing-deps` | Warn but continue on missing features              | Warning logged, continues with available data |        |
| 6.9 | config_source check         | `CLOUD_MOCK_MODE=true CLOUD_PROVIDER=local`        | `config_source=local`, no GCS reads           |        |

### Phase 7: Observability

| #    | Check                      | Expected                                                          | Status |
| ---- | -------------------------- | ----------------------------------------------------------------- | ------ |
| 7.1  | ServiceRuntime log line    | All dimensions logged (operation=infer, mode, category)           |        |
| 7.2  | UEI events                 | STARTED, VALIDATION_STARTED, VALIDATION_COMPLETED, STOPPED/FAILED |        |
| 7.3  | correlation_id             | UUID correlation_id in STARTED event                              |        |
| 7.4  | Dry-run warning            | "DRY RUN" + "UCI dry-run mode ACTIVE" logged                      |        |
| 7.5  | Shard-level isolation      | One instrument failure doesn't crash others                       |        |
| 7.6  | Error counting             | `error_count` > 0 triggers FAILED event + exit(1)                 |        |
| 7.7  | Pre-crash handlers         | `register_pre_crash_handlers()` active                            |        |
| 7.8  | Model promotion subscriber | Active in live mode, logs subscription status                     |        |
| 7.9  | Observability setup        | `setup_service_observability()` called at import                  |        |
| 7.10 | Event sink selection       | PubSub sink for pubsub messaging, GCS sink otherwise              |        |

## Known Issues Audit

Check these patterns (from instruments-service E2E findings):

| Pattern                         | What to check                                                         | Status |
| ------------------------------- | --------------------------------------------------------------------- | ------ |
| `load_dotenv(override=True)`    | Already `override=False` in main.py -- verify                         |        |
| `--dry-run` enforcement         | `validate_config()` returns True early on dry-run -- verify no writes |        |
| Bucket resolution               | Uses `build_bucket()` and config template -- not routing_key          |        |
| asyncio nesting                 | `InferHandler.run()` is async, `BatchHandler.handle()` is sync        |        |
| Category routing                | SPORTS excluded from CATEGORIES list -- verify argparse rejection     |        |
| `os.getenv()` usage             | Check for raw `os.getenv()` vs `UnifiedCloudConfig`                   |        |
| `.env` credential paths         | No placeholder credential paths in `.env`                             |        |
| Module-level side effects       | `setup_service_observability()` runs at import time -- verify safe    |        |
| `get_config()` at module level  | `config = get_config()` at module scope -- verify no crash on import  |        |
| Live mode shutdown              | `GracefulShutdownHandler` + PubSub cleanup on SIGTERM                 |        |
| Model hot-reload race condition | `ModelPromotionSubscriber` swaps model while inference in progress    |        |

## AWS Testing

| #   | What                              | Expected                              | Status |
| --- | --------------------------------- | ------------------------------------- | ------ |
| A.1 | `CLOUD_PROVIDER=aws` (no creds)   | Startup validation fails cleanly      |        |
| A.2 | `CLOUD_PROVIDER=aws` (with creds) | S3 model loading + prediction storage |        |

## Frontend API Surface

ml-inference-service feeds the ML Inference UI via these API endpoints:

| Endpoint                     | What it provides                                    | Verify                                          |
| ---------------------------- | --------------------------------------------------- | ----------------------------------------------- |
| `GET /ml/predictions`        | Prediction results with confidence scores           | instrument, target_type, probability, timestamp |
| `GET /ml/models`             | Model registry with live status (loaded/idle/error) | model_id, version, status, loaded_at            |
| Prediction confidence charts | Time series of prediction probabilities             | Chart data matches GCS predictions              |
| Model monitoring dashboards  | Inference latency, error rates, model drift         | Metrics consistent with observability logs      |

After a successful inference run, verify the prediction endpoints return fresh data.

## Issues Found

(logged in `plans/active/issues/service_control_surface_issues_2026_03_21.md`)

| Issue | Severity | Fixed? |
| ----- | -------- | ------ |
|       |          |        |

## Next Service

After ml-inference-service passes all phases -> proceed to `014_strategy_service.md`
