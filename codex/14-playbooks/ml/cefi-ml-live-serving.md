---
scope: [engineer, admin]
---

# CeFi ML Live-Serving Architecture

> **STATUS** — Design doc landed 2026-05-08 by Tab 2 of Ikenna's 6-tab work-split, in service of the
> [`cefi_ml_may_23_2026.epic.md`](../../../plans/archive/cefi_ml_may_23_2026.epic.md) success criteria
> "Live ML inference active" + "Model-version traceability per trade". Wiring lands on the Harsh side
> per the cross-side handshake; this doc is the contract.

## TL;DR

Live ML inference for the May-23 CeFi LIVE archetype runs on the SAME features-service compute path as batch (per
[`batch-live-symmetry.md`](../../04-architecture/batch-live-symmetry.md) — no parallel ML inference path). Three
durable artefacts make this work:

1. **Model artefact registry** — UAC SSOT for `gs://uts-models-{cloud}/{asset_group}/{family}/{version}/model.{ext}`
   path templates per (asset_group, model_family). UTL `model_registry.py` reads + caches.
2. **Hot-reload of model artefacts** — mirror the
   [`InstrumentLifecycleCacheDeltaReloader`](../../04-architecture/instrument-lifecycle-cache-delta-hot-reload.md)
   pattern: subscribe to `streaming.models.refresh_trigger`, diff registry, hot-reload affected models without
   service restart.
3. **Model-version traceability per trade** — every `FEATURE_COMPUTED` event + every strategy decision tag includes
   `model_version` + `model_artefact_uri` so the audit trail covers every signal back to the deterministic artefact.

## Path templates (UAC SSOT)

`unified_api_contracts.canonical.crosscutting.model_registry.MODEL_PATH_TEMPLATES` is the canonical mapping (greenfield;
ships in the Harsh ml-features-phase2a wave). Shape:

```python
MODEL_PATH_TEMPLATES: dict[tuple[AssetGroup, str], str] = {
    ("cefi", "lgbm_carry_basis"): "gs://uts-models-{cloud}/cefi/lgbm_carry_basis/{version}/model.txt",
    ("cefi", "lgbm_funding_arb"): "gs://uts-models-{cloud}/cefi/lgbm_funding_arb/{version}/model.txt",
    ("defi", "lgbm_lst_yield"):   "gs://uts-models-{cloud}/defi/lgbm_lst_yield/{version}/model.txt",
    # ...
}
```

`{cloud}` is filled at read-time from `UnifiedCloudConfig().cloud_provider` per workspace cloud-agnostic rule. `{version}`
is the semver of the model artefact (separate from service semver — model artefacts have their own versioning).

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

Same pattern as `ApiKeyReloader` + `InstrumentLifecycleCacheDeltaReloader`:

```python
from unified_trading_library.instrument_lifecycle_cache_delta_reloader import (
    InstrumentLifecycleCacheDeltaReloader,
    CatalogDelta,
)

# A new reloader is added in UTL: ModelArtefactReloader (parallel to the instrument-lifecycle one).
# It diffs `model_registry` snapshots between refresh-trigger events and dispatches
# `(ModelDelta, new_registry)` to subscribers (per-asset-group features-service workers
# re-load the affected models in-process).
```

Subscribed by the features-service compute worker; diffs new vs old model registry; on `added` / `modified` model
artefacts, downloads the new artefact + atomically swaps the in-memory model. `removed` models stop emitting features
for that model_family. The reloader carries the same `(CatalogDelta, snapshot)` shape the instrument-lifecycle one
uses, so the two share test fixtures.

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
- **Don't bypass hot-reload.** Restarting features-service to swap a model breaks the live cascade — replay catches
  up but the gap is pageable.
- **Don't omit `model_version` from any downstream event.** Audit trail requires it everywhere.
- **Don't bake the model into the Docker image.** Image is service-version; model is a separate artefact lifecycle.
- **Don't use a different inference path for batch vs live.** Same code, same registry, same model_version stamping —
  per "Batch = Live: Unified Pipeline Architecture" workspace rule.

## Cross-references

- Epic: [`cefi_ml_may_23_2026.epic.md`](../../../plans/archive/cefi_ml_may_23_2026.epic.md)
- Plan: [`live_pipeline_mtds_mdps_features_2026_05_08`](../../../plans/active/live_pipeline_mtds_mdps_features_2026_05_08.md)
- Sibling: [`ml-alerting-rules.md`](../alerting/ml-alerting-rules.md)
- Foundation:
  [`../../04-architecture/batch-live-symmetry.md`](../../04-architecture/batch-live-symmetry.md),
  [`../../04-architecture/instrument-lifecycle-cache-delta-hot-reload.md`](../../04-architecture/instrument-lifecycle-cache-delta-hot-reload.md),
  [`../../05-infrastructure/live-pipeline-architecture.md`](../../05-infrastructure/live-pipeline-architecture.md)
