---
scope: [engineer, ml-engineer, admin]
---

# ML experiment lifecycle

## Why a separate manifest

The data manifest (`unified_trading_library.manifest_writer.ManifestWriter`) is the SSOT for "what data exists and at
what state" — keyed by `(asset_group, venue, chain, data_type, instrument_type, ..., day)`. Models are not data; a model
is a **fitted artifact** plus the training context (input features, hyperparameters, seed, training window). Training
artifacts have a different lifecycle (created → validated → champion → retired) and a different identity (model_family +
version + training_period) than data shards. Tracking them in the data manifest mixes axes and breaks both schemas.

This doc names the **ML manifest** that lives alongside the data manifest.

## ML manifest schema

| Column                | Type       | Description                                                                      |
| --------------------- | ---------- | -------------------------------------------------------------------------------- |
| job_id                | str        | Unique per training run (`<model_family>__<training_period>__<git_sha>__<seed>`) |
| model_family          | str        | UAC enum (e.g. `xgb_directional_5m`, `lightgbm_volatility_15m`)                  |
| version               | str        | Semver; bumped per re-fit                                                        |
| training_period       | str        | `YYYY-MM-DD..YYYY-MM-DD`                                                         |
| inputs_feature_groups | list[str]  | UAC `feature_group` enum members consumed                                        |
| hyperparameters       | str (json) | Frozen at training-start                                                         |
| seed                  | int        | Reproducibility seed                                                             |
| status                | enum       | `training` / `validated` / `champion` / `shadow` / `retired`                     |
| started_at            | timestamp  | Training start                                                                   |
| completed_at          | timestamp  | Training end (nullable while running)                                            |
| validation_metrics    | str (json) | Out-of-sample backtest metrics                                                   |
| artifact_uri          | str        | GCS URI of the fitted model artifact                                             |
| git_sha               | str        | Git SHA of the training code                                                     |

Path: `gs://{pid}-ml-artifacts/manifest/_index/ml_manifest.parquet`.

## Job-id contract

`job_id` is the primary key. Every artifact in `gs://{pid}-ml-artifacts/{model_family}/{version}/{job_id}/` has a
matching ML-manifest row. Inference services (ml-inference-service / strategy-service) read by `job_id` to load the
champion model; never by file-path scan.

## Lifecycle states

```
training → validated → (shadow → champion → retired)
                           │
                           └── retired (failed validation)
```

- **training** — `record_started` writes the row with `status=training` + `started_at`. Subsequent failures emit
  `ML_TRAINING_FAILED` and flip status to `retired`.
- **validated** — out-of-sample backtest passes target metrics. Available to be promoted.
- **shadow** — running in parallel to champion; signals logged but not traded.
- **champion** — actively driving live trades (referenced by strategy-service config).
- **retired** — superseded or failed; artifact retained for audit; not loaded by inference.

Promotion (`validated → shadow → champion`) is a config change in strategy-service, not a manifest write. The ML
manifest reflects training state; strategy-service config decides which job_id is live.

## Live = batch

Batch backtests load by `job_id` via the ML manifest the same way live inference loads. No path-scan, no per-mode
fallback. A job_id either has a manifest row + an artifact at the canonical URI, or it does not exist as far as the
system is concerned.

## Cross-references

- Data lineage (data manifest companion):
  [`../02-data/data-lineage-MTDS-features-ml.md`](../02-data/data-lineage-MTDS-features-ml.md)
- Availability manifest schema:
  [`../02-data/availability-manifest-and-data-status.md`](../02-data/availability-manifest-and-data-status.md)
- Strategy summary: [`../09-strategy/strategy-summary.md`](../09-strategy/strategy-summary.md)
- Live = batch: [`batch-live-architecture.md`](batch-live-architecture.md) (single SSOT)
- Live config hot-reload (champion swap): [`live-strategy-config-hot-reload.md`](live-strategy-config-hot-reload.md)
