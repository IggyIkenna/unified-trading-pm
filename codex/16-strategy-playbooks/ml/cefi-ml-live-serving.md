---
doc_type: codex-ssot
title: CeFi ML Live-Serving Architecture
summary:
  Live ML inference contract for the May-23 CeFi archetype — runs in the standalone ml-inference-service (NOT
  features-service; SUPERSEDED note), cache-busts on MODEL_PROMOTED via ML_MODEL_COORDINATION_TOPIC, stamps
  model_version + model_artefact_uri on every downstream event for per-trade traceability, and defines the ML
  data_freshness callback (max of inference/promotion/feature-lag).
status: superseded
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [alerting-service, execution-service, features-service, strategy-service]
scope: [engineer, admin]
tags: [ml, cefi, live-trading, features, execution, model-tier, data-freshness]
related:
  [
    ../../04-architecture/batch-live-architecture.md,
    ../../04-architecture/instrument-lifecycle-cache-delta-hot-reload.md,
    ../../05-infrastructure/live-pipeline-architecture.md,
    ../../15-runbooks/alerting/ml-alerting-rules.md,
  ]
created: 2026-05-08
authoritative_for: []
referenced_by: [/codex/15-runbooks/alerting/ml-alerting-rules.md]
owner:
last_reviewed:
code_refs:
---

# CeFi ML Live-Serving Architecture

> **STATUS** — Design doc landed 2026-05-08 by Tab 2 of Ikenna's 6-tab work-split, in service of the
> [`cefi_ml_may_23_2026.epic.md`](../../../plans/archive/cefi_ml_may_23_2026.epic.md) success criteria "Live ML
> inference active" + "Model-version traceability per trade". Wiring lands on the Harsh side per the cross-side
> handshake; this doc is the contract.

> **🟡 SUPERSEDED 2026-05-12 — live ML inference orchestrator is `ml-inference-service` (standalone), NOT
> features-service.** The "no parallel ML inference path" claim below predates the architecture-v2 split. Operator
> disposition (2026-05-12 ML-2 BIG-finding triage): canonical = `ml-inference-service` per code reality + v2 archetype
> docs. features-service compute path runs FEATURE computation; ML inference happens in the dedicated
> `ml-inference-service`. See `ml-and-features-master_2026_05_07.md` + `ml-inference-service` source for live flow.

## TL;DR

Live ML inference for the May-23 CeFi LIVE archetype runs in the dedicated **`ml-inference-service`** (standalone
orchestrator; NOT features-service). features-service publishes `FEATURE_COMPUTED` events; `ml-inference-service`
consumes them, loads the champion model from the registry, emits inference events that strategy-service consumes. Per
[`batch-live-architecture.md`](../../04-architecture/batch-live-architecture.md): live + batch share the same component
interactions; only the execution-fill source differs. Three durable artefacts make this work:

1. **Model artefact registry** — UAC SSOT for model paths per (asset_group, model_family). UTL `model_registry.py`
   reads + caches. Bucket name resolves via `resolve_bucket_name(cloud=..., kind="ml-models-store", env=...)` per
   **Bucket-name SSOT (b+)** — never inline `gs://uts-models-{cloud}/...` (QG STEP 5.69 enforces). Canonical kind =
   `ml-models-store-{pid}`.
2. **Hot-reload of model artefacts** — mirror the
   [`InstrumentLifecycleCacheDeltaReloader`](../../04-architecture/instrument-lifecycle-cache-delta-hot-reload.md)
   pattern: subscribe to `streaming.models.refresh_trigger`, diff registry, hot-reload affected models without service
   restart.
3. **Model-version traceability per trade** — every `FEATURE_COMPUTED` event + every strategy decision tag includes
   `model_version` + `model_artefact_uri` so the audit trail covers every signal back to the deterministic artefact.

## Path templates (UAC SSOT)

`unified_api_contracts.canonical.crosscutting.model_registry.MODEL_PATH_TEMPLATES` is the canonical mapping (greenfield;
ships in the Harsh ml-features-phase2a wave). Bucket name resolves via
`resolve_bucket_name(kind="ml-models-store", ...)` — paths below are object-key-only shapes:

```python
# Object-key shape (bucket resolved via resolve_bucket_name at read-time):
MODEL_PATH_TEMPLATES: dict[tuple[AssetGroup, str], str] = {
    ("cefi", "lgbm_carry_basis"): "cefi/lgbm_carry_basis/{version}/model.txt",
    ("cefi", "lgbm_funding_arb"): "cefi/lgbm_funding_arb/{version}/model.txt",
    ("defi", "lgbm_lst_yield"):   "defi/lgbm_lst_yield/{version}/model.txt",
    # ...
}
# Full URI built at read-time:
#   bucket = resolve_bucket_name(cloud=cloud_provider, kind="ml-models-store", env=env)
#   uri = f"gs://{bucket}/{MODEL_PATH_TEMPLATES[(ag, family)].format(version=v)}"
```

`{version}` is the semver of the model artefact (separate from service semver — model artefacts have their own
versioning). Cloud + env resolved at read-time from `UnifiedCloudConfig` per workspace cloud-agnostic rule.

## Live-serving flow

```
features-service (live mode, asset-scoped flavor):

  consume `streaming.{asset_group}.candle_computed` (CandleComputedEvent from MDPS)
        │
        ▼
  compute features via existing feature_calculator graph
        │
        ▼
  if asset_group has live ML models:
    load model from registry (cached; refresh on `streaming.models.refresh_trigger`)
        │
        ▼
    run inference; emit `FEATURE_COMPUTED` event with:
      - feature payload
      - model_version
      - model_artefact_uri
      - inference_latency_ms
        │
        ▼
  publish to `streaming.{asset_group}.feature_computed`

strategy-service (live mode):

  consume `streaming.{asset_group}.feature_computed`
        │
        ▼
  decide; emit strategy decision event with:
      - decision payload
      - model_version (passed through from FEATURE_COMPUTED)
      - model_artefact_uri (same)
        │
        ▼
  forward to execution-service
```

## Hot-reload of model artefacts

> **🟡 LIFT 2026-05-12 (ML-3 PRE_CUTOVER, slot 8 audit)** — design intent below was a `ModelArtefactReloader` mirroring
> `InstrumentLifecycleCacheDeltaReloader` subscribing to `streaming.models.refresh_trigger`. **Implementation reality is
> simpler**: `ml-inference-service/ml_inference_service/app/core/model_promotion_subscriber.py` subscribes to the
> Pub/Sub topic `ml_model_coordination_events` (constant `ML_MODEL_COORDINATION_TOPIC`), listens for `MODEL_PROMOTED`
> events, and on receipt **clears the in-memory model cache** (no delta-diff, no snapshot dispatch); `ModelLoader` then
> lazily reloads from the new `artifact_gcs_path` on the next inference call. Codex describes the cache-bust mechanism
> (current); the design-intent delta-reloader is a POST_CUTOVER upgrade tracked in ML-18 (hot-reload-mechanisms matrix).

### Current — cache-bust on `MODEL_PROMOTED`

```python
# ml-inference-service/ml_inference_service/app/core/model_promotion_subscriber.py
ML_MODEL_COORDINATION_TOPIC = "ml_model_coordination_events"

# On MODEL_PROMOTED event arrival:
#   1. ModelPromotionSubscriber.handle_event() → clears ModelLoader's in-memory cache.
#   2. Next inference call lazily loads new artefact_gcs_path via ModelRegistry.
#   3. Per-event audit + observability via standard alerting-service routing.
```

`MODEL_PROMOTED` carries `(model_family, new_version, artifact_gcs_path)`. No delta-diff is computed; the next call to
`ModelLoader.load(model_family, version)` finds an empty cache and re-reads the artefact from GCS through
`ModelRegistry`. Strategy-service config still decides WHICH `job_id` is the champion; the subscriber bridges UAC's
promotion-event into the inference service's runtime cache lifecycle.

### Design-intent (POST_CUTOVER upgrade tracked in ML-18)

The original design specified a `ModelArtefactReloader` parallel to `InstrumentLifecycleCacheDeltaReloader` — diffing
`model_registry` snapshots, dispatching `(ModelDelta, new_registry)` to subscribers, sharing fixtures with the
instrument-lifecycle reloader. **This is NOT shipped**; the cache-bust path above is what ships for May-23 cutover.
Upgrade to delta-shape is tracked in `plans/archive/issues/codex_audit_ml_2026_05_12.md` ML-18 (POST_CUTOVER).

## Model-version traceability per trade

Every event in the live-pipeline cascade after the inference step carries `model_version` + `model_artefact_uri`:

- `FEATURE_COMPUTED` event (UAC `events.streaming.FeatureComputedEvent` — extend if not yet present)
- Strategy decision event (UAC `events.strategy.DecisionEmittedEvent` — extend)
- Execution-service order intent (UAC `events.execution.OrderIntentEvent` — extend)
- Position-balance-monitor fill event (UAC `events.position.FillRecordedEvent` — extend)

This makes the audit trail self-describing: starting from any fill, walk back through the events and find the exact
model artefact that drove the decision. P&L attribution per model_version (master plan Group F item) computes by
grouping fills by `model_version` + summing realised P&L.

## Anti-patterns

- **Don't load model artefacts from local disk.** Always via the registry — local disk drifts.
- **Don't bypass hot-reload.** Restarting features-service to swap a model breaks the live cascade — replay catches up
  but the gap is pageable.
- **Don't omit `model_version` from any downstream event.** Audit trail requires it everywhere.
- **Don't bake the model into the Docker image.** Image is service-version; model is a separate artefact lifecycle.
- **Don't use a different inference path for batch vs live.** Same code, same registry, same model_version stamping —
  per "Batch = Live: Unified Pipeline Architecture" workspace rule.

## `data_freshness` callback semantics (ml-inference-service)

> **ADD 2026-05-12 (ML-11 PRE_CUTOVER, slot 8 audit)** — the workspace STEP 5.62 rule requires every `api/main.py` to
> wire `make_health_router` with a `data_freshness` callback. `ml-inference-service` imports `make_health_router` but
> codex never defined what "fresh" means for an ML service. This section is the contract.

For `ml-inference-service`, **freshness** is the minimum of three timestamps:

1. **Last successful inference batch** — most-recent `FEATURE_COMPUTED` event consumed + scored (signals the
   consume-and-score loop is alive end-to-end). Stale if older than `expected_cadence * 1.5` per
   `(asset_group, model_family)`.
2. **Last `MODEL_PROMOTED` event processed** — most-recent promotion handled by `ModelPromotionSubscriber` (signals the
   hot-reload path is alive; stale if the topic has unconsumed messages older than 60s).
3. **Feature-event lag** — `now() - last_FEATURE_COMPUTED.available_at` (signals upstream is producing; stale if
   > `expected_cadence` of the slowest live model_family on the same VM).

The `data_freshness` callback returns the **maximum** of those three lags. `ML_SIGNAL_STALE` (per `ml-alerting-rules.md`
Rule 1) is the live alert that fires when the callback's lag exceeds the per-archetype threshold. The callback is also
the verifier the `make_health_router` GET `/healthz` endpoint reports and the deployment-UI freshness column reads.

## Cross-references

- Epic: [`cefi_ml_may_23_2026.epic.md`](../../../plans/archive/cefi_ml_may_23_2026.epic.md)
- Plan:
  [`live_pipeline_mtds_mdps_features_2026_05_08`](../../../plans/active/live_pipeline_mtds_mdps_features_2026_05_08.md)
- Sibling: [`ml-alerting-rules.md`](../../15-runbooks/alerting/ml-alerting-rules.md)
- Foundation: [`../../04-architecture/batch-live-architecture.md`](../../04-architecture/batch-live-architecture.md)
  (single SSOT),
  [`../../04-architecture/instrument-lifecycle-cache-delta-hot-reload.md`](../../04-architecture/instrument-lifecycle-cache-delta-hot-reload.md),
  [`../../05-infrastructure/live-pipeline-architecture.md`](../../05-infrastructure/live-pipeline-architecture.md)
