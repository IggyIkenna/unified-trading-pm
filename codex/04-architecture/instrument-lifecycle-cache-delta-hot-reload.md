---
scope: [engineer, admin]
---

# Instrument Lifecycle = Event-Publish + Downstream Cache-Delta Hot-Reload (workspace pattern)

> **STATUS** — Workspace pattern doc codified during the live-pipeline activation 2026-05-08. Work plan in
> [`plans/active/live_pipeline_mtds_mdps_features_2026_05_08.plan.md`](../../plans/active/live_pipeline_mtds_mdps_features_2026_05_08.plan.md)
> Phase 10. Coordinated with
> [`instruments_live_master_2026_05_08`](../../plans/epics/instruments_live_master_2026_05_08.plan.md). If this doc
> disagrees with the active plans, the plans win.

## TL;DR

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

| Service              | `on_added`                                                        | `on_removed`                                               | `on_changed`                                                                 |
| -------------------- | ----------------------------------------------------------------- | ---------------------------------------------------------- | ---------------------------------------------------------------------------- |
| **MTDS**             | Subscribe new instrument's WS feed (or REST poll fallback)        | Unsubscribe + flush in-flight buffers                      | Refresh per-instrument config (e.g. tick size, contract size for new expiry) |
| **MDPS**             | Refresh case-A vs case-D classifier registry                      | Refresh classifier (delisted instruments now case A')      | Refresh classifier + propagate any contract-shape changes                    |
| **features-service** | Re-validate UAC `required_inputs` DAG for affected feature_groups | Drop in-progress features for delisted instruments cleanly | Re-validate DAG; affected features may need recompute                        |

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

- `instruments_live_master_2026_05_08` owns the publish-side (verifies/adds the event publication if missing).
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
  [`live_pipeline_mtds_mdps_features_2026_05_08`](../../plans/active/live_pipeline_mtds_mdps_features_2026_05_08.plan.md)
  Phase 10.
- Plan: [`instruments_live_master_2026_05_08`](../../plans/epics/instruments_live_master_2026_05_08.plan.md) —
  publish-side owner.
- Pattern reference: `unified-trading-library/unified_trading_library/api_key_reloader.py` — same shape for API keys.
- Sibling: [`../05-infrastructure/live-pipeline-architecture.md`](../05-infrastructure/live-pipeline-architecture.md) —
  uses this pattern for live MTDS/MDPS/features instrument lifecycle propagation.
