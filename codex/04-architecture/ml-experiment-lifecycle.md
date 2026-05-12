---
scope: [engineer, ml-engineer, admin]
---

# ML experiment lifecycle

> **🟡 LIFT 2026-05-12 (ML-6 PRE_CUTOVER, slot 8 audit)** — the ML-manifest parquet schema in this doc is the
> **design intent**, NOT what ships. **Implementation reality**: UTL `ModelRegistry` (`unified-trading-library/
> unified_trading_library/ml/model_registry.py`) uses a **JSON index** at `model_registry/manifest.json`
> (constant `MANIFEST_PATH`), and ml-training / ml-inference reference models by `(variant_config, training_period |
> model_version)` — **NOT by `job_id`**. The `data-lineage-MTDS-features-ml.md` v7 manifest-shard list adds a
> `job_id` column at the data-manifest layer, so a partial overlap exists, but no `ml_manifest.parquet` artefact is
> written. Operator decision pending: (a) build the parquet ML-manifest as designed below + retrofit `ModelRegistry`,
> OR (b) rewrite this doc around the JSON-index reality + the data-manifest `job_id` column. Tracked in
> `plans/active/issues/codex_audit_ml_2026_05_12.md` ML-6.

## ML Hard Rules (LIFT 2026-05-12 from `_archived_pre_v2/cross-cutting/ml-pipeline.md`, ML-13 PRE_CUTOVER)

The archived pre-v2 ml-pipeline doc enumerated 3 Hard Rules not mirrored anywhere active. Lifted here per slot 8
audit ML-13 so the archived doc can be cleanly hard-bannered or deleted.

1. **ML models are signals, not decisions.** A model emits a directional / volatility / event-probability
   prediction. Strategy-service consumes the prediction and decides whether to act on it — the model never trades
   directly. This separation is what makes paper / live / shadow / batch all share the same inference path.
2. **Training and inference are separate services.** `ml-training-service` produces artefacts in the registry;
   `ml-inference-service` (standalone, NOT features-service — see ML-2 SUPERSEDED banner in
   `../16-strategy-playbooks/ml/cefi-ml-live-serving.md`) consumes them. Crossing the seam (e.g. running inference
   inside the training service, or training in the inference service) breaks the artefact-versioning contract.
3. **No model goes live without human approval.** Promotion `validated → shadow → champion` is a strategy-service
   config change with a documented runbook (see ML-10 follow-up: `15-runbooks/ml/promote-model-to-champion.md`
   pending). The model-promotion subscriber consumes `MODEL_PROMOTED` events; arming the promotion is operator-only.

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

Path: `{bucket}/manifest/_index/ml_manifest.parquet` where `bucket =
resolve_bucket_name(cloud=..., kind="ml-models-store", env=...)` per **Bucket-name SSOT (b+)** (see CLAUDE.md
§ "Bucket-name SSOT (b+)"). Canonical kind = `ml-models-store-{pid}` (matches UTL `ModelRegistry`). Never inline
`gs://{pid}-ml-artifacts/...` — QG STEP 5.69 enforces.

## Job-id contract

`job_id` is the primary key. Every artifact under `{bucket}/{model_family}/{version}/{job_id}/` (bucket resolved via
`resolve_bucket_name(kind="ml-models-store", ...)`) has a matching ML-manifest row. Inference services (ml-inference-service / strategy-service) read by `job_id` to load the
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
