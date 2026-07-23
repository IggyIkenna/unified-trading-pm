---
doc_type: codex-ssot
title: Instrument Lifecycle = Event-Publish + Downstream Cache-Delta Hot-Reload (workspace pattern)
summary:
  Instrument-lifecycle propagation = catalog-refresh event publish + downstream cache-delta hot-reload —
  instruments-service publishes a refresh trigger, MTDS/MDPS/features diff their cache and fire
  on_added/on_removed/on_changed callbacks.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [features-service, instruments-service, strategy-service, unified-trading-library]
scope: [engineer, admin]
tags: [instruments, mtds, mdps, features, pipeline-mode, self-healing]
related:
  [
    /codex/05-infrastructure/live-pipeline-architecture.md,
    /codex/04-architecture/instruments-live-architecture.md,
    /codex/06-coding-standards/config-reloader-pattern.md,
  ]
created: 2026-05-08
authoritative_for: [instrument-lifecycle cache-delta hot-reload workspace pattern]
referenced_by:
  [
    /codex/04-architecture/batch-live-architecture.md,
    /codex/04-architecture/live-strategy-config-hot-reload.md,
    /codex/05-infrastructure/live-pipeline-architecture.md,
    /codex/16-strategy-playbooks/ml/cefi-ml-live-serving.md,
    plans/epics/instruments_master.md,
  ]
owner:
last_reviewed: 2026-05-13
code_refs:
---

# Instrument Lifecycle = Event-Publish + Downstream Cache-Delta Hot-Reload (workspace pattern)

## Two reload mechanisms across the workspace (ML-18 matrix, 2026-05-13)

The workspace has **two distinct hot-reload mechanisms** that share the cache-delta shape but differ in trigger +
payload + consumer. Codified here so future designs reuse the matching mechanism per use case:

| Aspect                   | Mechanism 1 — Instrument-lifecycle delta-reloader                                                 | Mechanism 2 — Model Pub/Sub cache-bust                                                |
| ------------------------ | ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| **Trigger source**       | instruments-service catalog refresh (cron + on-demand)                                            | ml-training-service post-training run + model-registry write                          |
| **Pub/Sub topic**        | `streaming.{asset_group}.instrument_cache_refresh_trigger`                                        | `streaming.ml.model_registry_cache_bust`                                              |
| **Payload shape**        | `INSTRUMENT_CACHE_REFRESH_TRIGGER` event with catalog-version hash                                | `MODEL_REGISTRY_CACHE_BUST` event with `(model_family, training_run_id)`              |
| **Consumer-side state**  | In-memory catalog dict + per-instrument subscription state                                        | UTL `ModelRegistry` instance cache + warm-loaded model artefacts                      |
| **Delta strategy**       | Fetch new catalog, compute (added/removed/changed) deltas, hot-reload affected subscription state | Invalidate cached entry for `(model_family, training_run_id)`, re-load on next access |
| **Latency budget**       | <30s end-to-end (instrument-day grain)                                                            | <60s (model warm-load is heavier)                                                     |
| **Downstream consumers** | MTDS / MDPS / features-service (each maintains own cache)                                         | strategy-service (`ML_DIRECTIONAL` archetypes), features-\* (ML-derived calculators)  |
| **Doc**                  | This file (continues below)                                                                       | UTL `ml/model_registry.py` docstrings + `catalogue-ml-model.md`                       |

Both mechanisms compose with `ApiKeyReloader` / `start_domain_config_reloaders` — "service is effectively a config"
applies uniformly. Reference: Sweep 3 of
[`codex_doc_currency_and_consolidation_post_cutover_2026_05_12.md`](../../plans/archive/codex_doc_currency_and_consolidation_post_cutover_2026_05_12.md).

---

> **STATUS** — Workspace pattern doc codified during the live-pipeline activation 2026-05-08. Work plan in
> [`plans/active/live_pipeline_mtds_mdps_features_2026_05_08.md`](../../plans/active/live_pipeline_mtds_mdps_features_2026_05_08.md)
> Phase 10. Coordinated with [`instruments_master`](../../plans/epics/instruments_master.md). If this doc disagrees with
> the active plans, the plans win.

## TL;DR

> **Producer note (2026-07-03):** the daily catalog refresh upstream of this trigger is now the **incremental** rollup
> (prev catalogue + trailing-window upsert, plan `instruments_catalogue_incremental_rollup_2026_06_29`) — the published
> artifact is still the FULL cumulative frame (schema/shape unchanged), and steady-state deltas stay naturally small
> (window `available_to` updates + new listings), so the delta contract below is unaffected.

When instruments-service publishes a catalog refresh, downstream services (MTDS / MDPS / features-service) maintain
their own catalog cache + diff against the new catalog + hot-reload affected state. Same shape as `ApiKeyReloader` /
`start_domain_config_reloaders`. **NOT a new dedicated stream type.** "Service is effectively a config" — the same
pattern applies to instrument lifecycle, API keys, throttle config, and any other slow-moving config the service
consumes.

## The pattern

```
instruments-service                              MTDS / MDPS / features-service (each downstream)
─────────────────────                            ──────────────────────────────────────────────
catalog refresh runs                               on startup: load current catalog from GCS into in-memory cache
  ↓                                                subscribe to streaming.{ag}.instrument_cache_refresh_trigger
write parquet to GCS                                          ↓
  ↓                                                ┌───────────┴───────────┐
publish INSTRUMENT_CACHE_REFRESH_TRIGGER  ─────►   │ on event: fetch new   │
event with row counts (added/removed/changed)      │ catalog parquet from  │
                                                   │ GCS, diff vs cache    │
                                                   ├───────────────────────┤
                                                   │ if delta is empty:    │
                                                   │   no callbacks fire   │
                                                   │ if added:             │
                                                   │   on_added(list[...]) │
                                                   │ if removed:           │
                                                   │   on_removed(list)    │
                                                   │ if changed:           │
                                                   │   on_changed(list)    │
                                                   └───────────────────────┘
```

## What "service is effectively a config" means

Distinguish two classes of state:

| Class                  | Examples                                                                                                   | Refresh strategy                                                                     |
| ---------------------- | ---------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| **Hot-reload-capable** | Instrument catalog, API keys, per-venue throttle config, feature_group flag toggles, alerting rule configs | Cache-delta hot-reload pattern (this doc) — service stays up, mutates state in-place |
| **Redeploy-required**  | UAC schema columns, calculator code, contract enum values, source_priority, environment variables          | Restart the service (or roll deployment); no in-flight mutation                      |

Hot-reloadable state has a publisher + subscribers. Redeploy-required state has no publisher because the implication of
changing it is "code-changed; new image; bounce." The two classes never overlap in a single service contract — a config
field is either one or the other, never both.

## Why NOT a dedicated `INSTRUMENT_LIFECYCLE_CHANGED` stream

Three reasons (this was the path-not-taken in the original 2026-05-08 design discussion; the user corrected the framing
to the cache-delta pattern):

1. **instruments-service already publishes refresh events.** Adding a parallel `INSTRUMENT_LIFECYCLE_CHANGED` stream
   duplicates the SSOT.
2. **The downstream concern is "what changed since I last looked"** — a delta question. Streaming each lifecycle
   transition as its own event multiplies network chatter without giving downstream consumers more information than a
   single "catalog refreshed; here's the row count delta" event does.
3. **The existing `ApiKeyReloader` pattern already handles this exact shape** for API keys. Reusing the pattern means
   one helper to learn + maintain + test, not two.

## The reloader helper (UTL `InstrumentCacheDeltaReloader`)

```python
from unified_trading_library.instrument_cache.cache_delta_reloader import InstrumentCacheDeltaReloader

reloader = InstrumentCacheDeltaReloader(
    asset_group=AssetGroup.DEFI,
    on_added=lambda added: subscribe_websocket_for(added),
    on_removed=lambda removed: unsubscribe_and_flush(removed),
    on_changed=lambda changed: refresh_classifier_for(changed),
)
reloader.start()  # subscribes to stream + spawns background reader thread
# ... service runs ...
reloader.stop()
```

## Per-service callback semantics

The summary table below lists the high-level callback responsibilities. Per Phase 10 of
[`live_pipeline_mtds_mdps_features_2026_05_08.md`](../../plans/active/live_pipeline_mtds_mdps_features_2026_05_08.md)
which shipped 2026-05-11 with `InstrumentLifecycleCacheDeltaReloader` (UTL@`54d658e8`), the per-service implementation
details + Protocol surface are documented in the expanded tables further down this section.

| Service              | `on_added`                                                        | `on_removed`                                               | `on_changed`                                                                 |
| -------------------- | ----------------------------------------------------------------- | ---------------------------------------------------------- | ---------------------------------------------------------------------------- |
| **MTDS**             | Subscribe new instrument's WS feed (or REST poll fallback)        | Unsubscribe + flush in-flight buffers                      | Refresh per-instrument config (e.g. tick size, contract size for new expiry) |
| **MDPS**             | Refresh case-A vs case-D classifier registry                      | Refresh classifier (delisted instruments now case A')      | Refresh classifier + propagate any contract-shape changes                    |
| **features-service** | Re-validate UAC `required_inputs` DAG for affected feature_groups | Drop in-progress features for delisted instruments cleanly | Re-validate DAG; affected features may need recompute                        |

### MTDS — `CatalogDelta` callback wiring (Phase 10 detail)

MTDS instantiates `InstrumentLifecycleCacheDeltaReloader` per asset_group in `live_mode` startup and wires three
discrete callbacks. Each callback receives `(CatalogDelta, snapshot)` where `CatalogDelta` is a frozen dataclass with
`added: tuple[InstrumentRow, ...]`, `removed: tuple[InstrumentRow, ...]`,
`changed: tuple[tuple[InstrumentRow, InstrumentRow], ...]` (`(old, new)` pairs).

| Callback site                             | Signature                                                    | Behaviour                                                                                                                                                                                                                                    |
| ----------------------------------------- | ------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `live/ws_subscription_manager.on_added`   | `(delta: CatalogDelta, snapshot: InstrumentCatalog) -> None` | For each `added` instrument, call `ws_client.subscribe(venue, instrument_id)`. WS adapter routes by venue per `unified_api_contracts.market.SOURCE_PRIORITY`; falls back to REST poll if WS unavailable.                                     |
| `live/ws_subscription_manager.on_removed` | `(delta, snapshot) -> None`                                  | For each `removed` instrument, call `ws_client.unsubscribe(venue, instrument_id)` + flush in-flight tick buffer to GCS via `record_captured` before final-tick window closes.                                                                |
| `live/instrument_config_cache.on_changed` | `(delta, snapshot) -> None`                                  | For each `(old, new)` pair, refresh `tick_size` / `contract_size` / `expiry_date` / `settlement_currency` in the live config cache. New expiry → spawn new contract WS subscription; old `expiry_date < now` → unsubscribe expired contract. |

### MDPS — `CatalogDelta` callback wiring (Phase 10 detail)

MDPS uses the catalog to drive the case-A-vs-D classifier (per CLAUDE.md "Four-category empty-output decision") that
decides whether a zero-source-response window is `record_empty(reason=EXPECTED_INSTRUMENT_DELISTED)` (case A) or
`record_captured` with a zero-activity bar (case D — instrument alive but illiquid).

| Callback site                             | Signature                   | Behaviour                                                                                                                                                                                                                                                                                                                                                                                                                              |
| ----------------------------------------- | --------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `live/catalog_classifier.on_added`        | `(delta, snapshot) -> None` | Add new instrument to `_alive_set` keyed by `(venue, instrument_id, day)`. The classifier reads `_alive_set` per write-gate; presence routes to case D, absence routes to case A.                                                                                                                                                                                                                                                      |
| `live/catalog_classifier.on_removed`      | `(delta, snapshot) -> None` | Remove instrument from `_alive_set`. Subsequent zero-source-response windows for this instrument route to case A (record_empty reason `EXPECTED_INSTRUMENT_DELISTED`).                                                                                                                                                                                                                                                                 |
| `live/aggregator_config_cache.on_changed` | `(delta, snapshot) -> None` | For each `(old, new)` pair where contract-shape fields differ (`tick_size`, `lot_size`, `settlement_currency`, `multiplier`), refresh the per-instrument aggregator config. Aggregation function (`compute_ohlcv_bar` etc.) reads these for tick-to-candle normalisation; stale values produce silently wrong OHLCV. Cluster-validation propagates: new expiry → new entry in `expected_root_clusters` map for the bundled-shard root. |

### features-service — `CatalogDelta` callback wiring (Phase 10 detail)

features-service consumes the catalog to validate UAC `feature_group → required_inputs` DAG completeness per
asset-scoped runner. When an instrument is added/removed/changed mid-day, the DAG validity for any feature_group
touching that instrument can flip.

| Callback site                                  | Signature                   | Behaviour                                                                                                                                                                                                                                                                                                                                         |
| ---------------------------------------------- | --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `live/feature_dag_validator.on_added`          | `(delta, snapshot) -> None` | For each `added` instrument, walk every feature_group's `required_inputs` set; if any input matches `(asset_group, venue, instrument_id, data_type)`, mark feature_group as `now_satisfied` (was previously skipped with `DEPENDENCIES_MISSING_CONTINUE`). Next CandleComputed event fires the feature for this instrument.                       |
| `live/feature_dag_validator.on_removed`        | `(delta, snapshot) -> None` | For each `removed` instrument, drop in-progress feature compute state cleanly (cancel pending tasks, flush partial outputs as `record_failed` with `error_reason=INSTRUMENT_DELISTED_MID_COMPUTE`, propagate `data_freshness=STALE` for any cross-instrument features whose inputs included this instrument).                                     |
| `live/cross_instrument_input_cache.on_changed` | `(delta, snapshot) -> None` | For each `(old, new)` pair, refresh cross-instrument feature input mappings (e.g. `cross_instrument.lst_yield_vs_eth_spot` referencing `defi.lido.steth_yield` — if Lido's contract address changes mid-day, the cross-cutting runner needs the new address). Propagates to `WatermarkAlignmentFanin` upstream-stream registration if applicable. |

### Reloader invocation pattern (per service)

Each consumer service mounts the reloader as part of `ServiceBootstrap` startup:

```python
from unified_trading_library.instrument_lifecycle_cache_delta_reloader import (
    InstrumentLifecycleCacheDeltaReloader,
)
from unified_trading_library.events import EventSubscriber

# In service startup:
reloader = InstrumentLifecycleCacheDeltaReloader(
    asset_group="cefi",
    storage_client=storage_client,
    on_added=ws_subscription_manager.on_added,
    on_removed=ws_subscription_manager.on_removed,
    on_changed=instrument_config_cache.on_changed,
)
subscriber = EventSubscriber(topic="instrument-cache-refresh-trigger", project_id=...)
async for event in subscriber.subscribe():
    if event.event_name == "INSTRUMENT_CACHE_REFRESH_TRIGGER":
        await reloader.on_refresh_event(event)
```

The reloader fetches the new catalog snapshot from GCS, diffs against the previous in-memory snapshot, builds the
`CatalogDelta`, and dispatches the three callbacks in order: `on_added` → `on_changed` → `on_removed`. Order matters for
two reasons: (1) `on_added` may need to subscribe a feed BEFORE `on_changed` refreshes that instrument's config; (2)
`on_removed` runs last so its `flush_in_flight` calls don't fight `on_added`'s new subscriptions on the same underlying
WS connection.

## Failure modes + retry

- **GCS fetch failure on event**: reloader logs + retries with exponential backoff + does NOT crash the service. The
  next refresh trigger will succeed (instruments-service runs on its existing cadence; missing one event isn't
  catastrophic).
- **Diff failure (e.g. new schema field the cache doesn't know about)**: log loud, raise; this IS catastrophic —
  redeploy-required class accidentally arrived as hot-reload class. Operator-intervention path.
- **Callback raises**: caught + logged + service continues. The reloader has done its job (it produced the diff);
  callback failures are the consumer's concern.

## Cross-service coordination during the May-23 cutover

instruments-service publish-side and downstream consume-side are coordinated:

- `instruments_master` owns the publish-side (verifies/adds the event publication if missing).
- `live_pipeline_mtds_mdps_features_2026_05_08` Phase 10 owns the consume-side (UTL helper + per-service wiring).

Banner each plan with the other to keep the work coordinated.

## Anti-patterns

- **Don't add an `INSTRUMENT_LIFECYCLE_CHANGED` parallel stream.** Use this pattern.
- **Don't poll instruments-service catalog from each downstream service.** That's wasteful — events drive cache refresh,
  polls don't.
- **Don't conflate hot-reload-capable state with redeploy-required state.** A config field is one or the other; mixed
  semantics confuse operators.
- **Don't catch + ignore reloader failures silently.** GCS fetch retries are fine; diff failures are loud.

## Cross-references

- Plan:
  [`live_pipeline_mtds_mdps_features_2026_05_08`](../../plans/active/live_pipeline_mtds_mdps_features_2026_05_08.md)
  Phase 10.
- Plan: [`instruments_master`](../../plans/epics/instruments_master.md) — publish-side owner.
- Pattern reference: `unified-trading-library/unified_trading_library/api_key_reloader.py` — same shape for API keys.
- Sibling:
  [`/codex/05-infrastructure/live-pipeline-architecture.md`](/codex/05-infrastructure/live-pipeline-architecture.md) —
  uses this pattern for live MTDS/MDPS/features instrument lifecycle propagation.
