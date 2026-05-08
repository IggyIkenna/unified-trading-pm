---
scope: [engineer, admin]
---

# Live Pipeline Architecture — MTDS / MDPS / features-service

> **STATUS** — entry-point doc for the live (websocket-streaming) pipeline activated for the 2026-05-23 DeFi cutover.
> Full design + phased work plan in
> [`plans/active/live_pipeline_mtds_mdps_features_2026_05_08.plan.md`](../../plans/active/live_pipeline_mtds_mdps_features_2026_05_08.plan.md).
> Dependent prerequisites:
> [`features_repo_consolidation_2026_05_08`](../../plans/active/features_repo_consolidation_2026_05_08.plan.md) +
> [`gcs_migration_bundle_pipeline_mode_2026_05_08`](../../plans/active/gcs_migration_bundle_pipeline_mode_2026_05_08.plan.md).
> If this doc disagrees with the active plans, the plans win — flag conflicts to the user.

## TL;DR

Three-tier live pipeline: **MTDS → MDPS → features-service**. Same code path as batch (per
[`batch-live-symmetry.md`](../04-architecture/batch-live-symmetry.md) — the live activation does NOT introduce a new
data path; it only swaps the trigger source from Cloud Scheduler to Redis Stream events). UTC midnight alignment
end-to-end ensures batch ↔ live reconciliation is a `GROUP BY pipeline_mode` over the same manifest. Service-start
order doesn't matter — every service syncs at the next aligned candle boundary.

## Topology

| Layer                            | Deployment shape                                                                 | Why                                                                                                                                                                 |
| -------------------------------- | -------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **MTDS**                         | Standalone cluster, sharded by the v5 shard SSOT (per asset_group matrix)        | Websocket connection-pool concerns (CloudFront, per-key throttling, IP redundancy) don't compose with compute                                                       |
| **MDPS + features-asset-scoped** | Colocated per asset_group on one box                                             | Shared local memory; in-process MDPS→features handoff is a perf optimisation (deferred post-May-23)                                                                 |
| **features-cross-cutting**       | Separate flavor of the consolidated `features-service` image, standalone box(es) | Subscribes to multiple asset_group streams; required for cross-instrument + cross-asset-group features (e.g. `lst_yield_vs_eth_spot`, `perp_funding_vs_spot_basis`) |
| **Replay subsystem**             | Separate process, parameterised by `--start --end --shard-key`                   | Fills gap windows from intraday restarts; smooth handoff to live via watermark KV                                                                                   |

## Sharding

**No new shard axes for live.** The v5 shard atom matrix from
[`availability-manifest-and-data-status.md`](../02-data/availability-manifest-and-data-status.md) applies identically to
live. Connection pool size per shard is an orthogonal config knob — does NOT appear in the manifest.

## Storage layout

`pipeline_mode={batch_databento, batch_tardis, batch_ccxt, ..., live_websocket}` is a hive partition column added to
every parquet path during the GCS migration bundle. Same parquet schema, same `available_at` semantics, same row-key
shape. UAC `SOURCE_PRIORITY` does the live-vs-batch fan-in at read time. Reconciliation is a SQL
`GROUP BY pipeline_mode` over the same `_index/availability_index.parquet`. See
[`pipeline-mode-partition.md`](../02-data/pipeline-mode-partition.md) for full migration + reader-fallback contract.

## Trigger cascade

```
MTDS (per shard)
  ├─ UTCAlignedScheduler fires at every aligned 15s boundary + grace
  └─ XADD streaming.{ag}.candle_boundary_crossed CandleBoundaryCrossedEvent
       ↓
MDPS consumer group "mdps"
  ├─ XREADGROUP → fetch flushed tick parquet → aggregate OHLCV
  ├─ Multi-timeframe cascade: 1m derived from 4× 15s candles (NOT raw ticks — same path as batch)
  └─ XADD streaming.{ag}.candle_computed CandleComputedEvent (with ServiceEmissionPolicy flag)
       ↓
features-service-asset-scoped consumer group "features-asset-scoped-{ag}"
  ├─ Look up which feature_groups have required_inputs satisfied (UAC DAG SSOT)
  ├─ Compute features with LookaheadBiasError strict-mode gate
  └─ XADD streaming.{ag}.features_computed FeaturesComputedEvent
       ↓
features-service-cross-cutting consumer group "features-cross-cutting"
  ├─ Subscribes to MULTIPLE asset_groups' streams
  ├─ Watermark + grace fan-in (default 500ms intra-zone)
  └─ XADD streaming.cross_cutting.features_computed FeaturesComputedEvent
```

## UTC midnight alignment + service-start-order independence

Live = batch by construction. MTDS waits for the next aligned candle boundary on startup; never emits partial windows.
Boots at 14:23:07.4 UTC for timeframe="15s" → first emission at 14:23:16.0 UTC for window [14:23:00, 14:23:15]. Any
service can boot in any order; they all sync at the next aligned boundary. Mid-day restart loses some live data; the
replay subsystem fills the gap.

## Live gap semantics — stale-not-missing

Apply the existing 4-category empty-output tree (per
[`availability-manifest-and-data-status.md`](../02-data/availability-manifest-and-data-status.md) "Four-category
empty-output decision") to live emissions:

| Situation                                                 | Action                                                                                                 |
| --------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| WS connected, no trades, catalog alive (cefi/defi/tradfi) | Zero-activity bar `O=H=L=C=prior_LTP, vol=0`, fresh                                                    |
| WS connected, no trades, catalog delisted/non-trading     | `record_empty(reason=EXPECTED_*)`, no candle                                                           |
| WS disconnected mid-window                                | Emit candle with `data_freshness=STALE`, `ServiceEmissionPolicy.PUBLISHED_DEGRADED`, carry-forward LTP |
| WS dead >N consecutive windows                            | Stop emitting; alert; downstream sees absence + last STALE flag → trips circuit breaker                |

`PUBLISHED_DEGRADED` → strategy refuses NEW signals, allows EXIT signals. Stale-not-missing rule preserves operational
continuity under transient feed degradation.

## Health-API + alerting integration

Health-API is QG-enforced as ERROR per workspace STEP 5.62. Live-pipeline extends the `data_freshness` callback with:

- `last_candle_emitted_at` per `(venue, data_type, timeframe)`
- `staleness_seconds` per shard
- `degraded_ratio_60s`
- `cluster_pct_skipped_60s`

alerting-service polls + subscribes to event streams + applies tiered alerts + drives circuit breakers wired to
strategy-service via a dedicated `streaming.alerting.circuit_breaker` stream. Three actions: `stop_new_signals` /
`force_exit_only` / `halt_strategy`. See [`alerting-batch-live.md`](../04-architecture/alerting-batch-live.md) for tier
table.

## Instrument lifecycle = event-publish + cache-delta hot-reload

instruments-service publishes `INSTRUMENT_CACHE_REFRESH_TRIGGER` after every successful catalog refresh. Downstream MTDS
/ MDPS / features-service consume + diff their cache + hot-reload affected state. Same pattern as `ApiKeyReloader`. NOT
a new dedicated stream type. See
[`instrument-lifecycle-cache-delta-hot-reload.md`](../04-architecture/instrument-lifecycle-cache-delta-hot-reload.md).

## Replay subsystem

Separate process (NOT folded into MTDS) that reads historical batch sources + emits replay events through the same Redis
Streams the live pipeline uses. Smooth handoff to live via per-shard `replay_watermark.{ag}.{shard_key}` Redis KV. See
[`replay-subsystem.md`](./replay-subsystem.md).

## VM topology + launchers

Per workspace VM launcher SSOT rule. Launchers under `deployment-service/scripts/vm/`:

- `launch-mtds-live-{asset_group}.sh`
- `launch-mdps-features-live-{asset_group}.sh` (combined MDPS+features-asset-scoped per asset_group)
- `launch-features-cross-cutting.sh`
- `launch-replay-cascade.sh`

VM-name prefixes registered in `VM_PREFIX_TO_BUCKET`: `mtds-live-`, `mdps-features-live-`, `features-xc-`, `replay-`.

## Anti-patterns

- Don't emit partial candles on MTDS startup — UTC alignment scheduler blocks until next aligned boundary.
- Don't compute 1m candle from raw ticks in live mode — derive from 4× 15s candles (same path as batch).
- Don't skip a candle when WS disconnects mid-window — emit STALE + PUBLISHED_DEGRADED. Stale-not-missing.
- Don't add an `INSTRUMENT_LIFECYCLE_CHANGED` parallel stream — use the cache-delta hot-reload pattern.
- Don't introduce `pipeline_mode=replay` — replay writes to `pipeline_mode=live_websocket` with original-time
  `available_at`.

## Cross-references

- Plan:
  [`live_pipeline_mtds_mdps_features_2026_05_08`](../../plans/active/live_pipeline_mtds_mdps_features_2026_05_08.plan.md)
- Pre-req plan:
  [`features_repo_consolidation_2026_05_08`](../../plans/active/features_repo_consolidation_2026_05_08.plan.md)
- Pre-req plan:
  [`gcs_migration_bundle_pipeline_mode_2026_05_08`](../../plans/active/gcs_migration_bundle_pipeline_mode_2026_05_08.plan.md)
- Sibling docs: [`replay-subsystem.md`](./replay-subsystem.md),
  [`../02-data/pipeline-mode-partition.md`](../02-data/pipeline-mode-partition.md),
  [`../04-architecture/instrument-lifecycle-cache-delta-hot-reload.md`](../04-architecture/instrument-lifecycle-cache-delta-hot-reload.md)
- Foundation docs: [`../04-architecture/batch-live-symmetry.md`](../04-architecture/batch-live-symmetry.md),
  [`../04-architecture/batch-live-pipeline.md`](../04-architecture/batch-live-pipeline.md),
  [`../02-data/availability-manifest-and-data-status.md`](../02-data/availability-manifest-and-data-status.md)
