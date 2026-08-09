---
doc_type: codex-ssot
title: Live Pipeline Architecture — MTDS / MDPS / features-service
summary:
  "Entry-point doc for the live (websocket-streaming) pipeline: three-tier MTDS → MDPS → features-service on the SAME
  code path as batch (only the trigger swaps Cloud Scheduler → Redis Stream events). UTC-midnight alignment makes
  reconciliation a GROUP BY pipeline_mode. Covers topology, trigger cascade, 4-category live gap semantics
  (stale-not-missing), StreamingHealthSnapshot alerting tiers + circuit breakers, and shipped UTL streaming primitives."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [alerting-service, deployment-api, deployment-service, deployment-ui, execution-service, features-service]
scope: [engineer, admin]
tags: [live-trading, mtds, mdps, features, pipeline-mode, reconciliation, infrastructure]
related:
  [
    /codex/05-infrastructure/replay-subsystem.md,
    /codex/05-infrastructure/live-deployment-monitoring.md,
    /codex/02-data/pipeline-mode-partition.md,
    /codex/04-architecture/batch-live-architecture.md,
  ]
created: 2026-05-08
authoritative_for: [live streaming pipeline topology]
referenced_by:
  [
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/pipeline-mode-partition.md,
    /codex/03-observability/coordination-events.md,
    /codex/03-observability/lifecycle-events.md,
    /codex/04-architecture/README.md,
    /codex/04-architecture/alerting-batch-live.md,
    /codex/04-architecture/batch-live-architecture.md,
    /codex/04-architecture/cefi-batch-live.md,
  ]
owner:
last_reviewed: 2026-09-06
code_refs:
---

# Live Pipeline Architecture — MTDS / MDPS / features-service

> **STATUS** — entry-point doc for the live (websocket-streaming) pipeline activated for the 2026-05-23 DeFi cutover.
> Full design + phased work plan in
> [`/plans/archive/2026_05/live_pipeline_mtds_mdps_features_2026_05_08.md`](../..//plans/archive/2026_05/live_pipeline_mtds_mdps_features_2026_05_08.md).
> Dependent prerequisites:
> [`features_repo_consolidation_2026_05_08`](../../plans/archive/features_repo_consolidation_2026_05_08.plan.md) +
> [`gcs_migration_bundle_pipeline_mode_2026_05_08`](../../plans/archive/2026_05/gcs_migration_bundle_pipeline_mode_2026_05_08.md).
> If this doc disagrees with the active plans, the plans win — flag conflicts to the user.

## TL;DR

Three-tier live pipeline: **MTDS → MDPS → features-service**. Same code path as batch (per
[`batch-live-architecture.md`](/codex/04-architecture/batch-live-architecture.md) (single SSOT) — the live activation
does NOT introduce a new data path; it only swaps the trigger source from Cloud Scheduler to Redis Stream events). UTC
midnight alignment end-to-end ensures batch ↔ live reconciliation is a `GROUP BY pipeline_mode` over the same manifest.
Service-start order doesn't matter — every service syncs at the next aligned candle boundary.

## Topology

| Layer                            | Deployment shape                                                                 | Why                                                                                                                                                                 |
| -------------------------------- | -------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **MTDS**                         | Standalone cluster, sharded by the v5 shard SSOT (per asset_group matrix)        | Websocket connection-pool concerns (CloudFront, per-key throttling, IP redundancy) don't compose with compute                                                       |
| **MDPS + features-asset-scoped** | Colocated per asset_group on one box                                             | Shared local memory; in-process MDPS→features handoff is a perf optimisation (deferred post-cutover; see `mtds_mdps_master.md`)                                     |
| **features-cross-cutting**       | Separate flavor of the consolidated `features-service` image, standalone box(es) | Subscribes to multiple asset_group streams; required for cross-instrument + cross-asset-group features (e.g. `lst_yield_vs_eth_spot`, `perp_funding_vs_spot_basis`) |
| **Replay subsystem**             | Separate process, parameterised by `--start --end --shard-key`                   | Fills gap windows from intraday restarts; smooth handoff to live via watermark KV                                                                                   |

## Sharding

**No new shard axes for live.** The v5 shard atom matrix from
[`availability-manifest-and-data-status.md`](/codex/02-data/availability-manifest-and-data-status.md) applies
identically to live. Connection pool size per shard is an orthogonal config knob — does NOT appear in the manifest.

## Storage layout

`pipeline_mode={batch_databento, batch_tardis, batch_ccxt, ..., live_websocket}` is a hive partition column added to
every parquet path during the GCS migration bundle. Same parquet schema, same `available_at` semantics, same row-key
shape. UAC `SOURCE_PRIORITY` does the live-vs-batch fan-in at read time. Reconciliation is a SQL
`GROUP BY pipeline_mode` over the same `_index/availability_index.parquet`. See
[`pipeline-mode-partition.md`](/codex/02-data/pipeline-mode-partition.md) for full migration + reader-fallback contract.

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

**Not every live-captured `data_type` enters this cascade.** `CandleBoundaryCrossedEvent.data_type` is typed against the
MDPS candle-schema `DataType` enum, which only covers `data_type`s with a registered MDPS `CandleAdapterRegistry` entry.
`LiveWebsocketRunner` checks `is_candle_boundary_eligible(data_type)` before publishing and no-ops otherwise — e.g.
`depth_of_book_10` (L2 order-book microstructure) has no candle adapter and is consumed directly by
`market_tick_data_service.derived.book_microstructure_compute`, never entering the MTDS→MDPS boundary-event path at all.
See `cefi_depth_of_book_10_live_capture_only_binance_producing_rows_2026_08_09.md` (archived) for the incident this
codified.

## UTC midnight alignment + service-start-order independence

Live = batch by construction. MTDS waits for the next aligned candle boundary on startup; never emits partial windows.
Boots at 14:23:07.4 UTC for timeframe="15s" → first emission at 14:23:16.0 UTC for window [14:23:00, 14:23:15]. Any
service can boot in any order; they all sync at the next aligned boundary. Mid-day restart loses some live data; the
replay subsystem fills the gap.

## Live gap semantics — stale-not-missing

Apply the existing 4-category empty-output tree (per
[`availability-manifest-and-data-status.md`](/codex/02-data/availability-manifest-and-data-status.md) "Four-category
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

The data-freshness snapshot is computed via the UTL primitive
`unified_trading_library.streaming.compute_streaming_health(redis_client, stream_name=, consumer_group=, watermark_key=)`
which returns a frozen `StreamingHealthSnapshot` with `last_event_age_seconds` (from `XREVRANGE`),
`consumer_lag_pending` (from `XPENDING`), `replay_watermark` (from per-shard `replay_watermark.{shard_key}` KV), and
`zero_activity_bar_rate` (fraction of recent events flagged `data_freshness=ZERO_ACTIVITY_BAR` per the four-category
empty-output decision rule D). Services consume the snapshot directly in their `make_health_router(data_freshness=...)`
callback — no per-service re-implementation.

alerting-service polls + subscribes to event streams + applies tiered alerts + drives circuit breakers wired to
strategy-service via a dedicated `streaming.alerting.circuit_breaker` stream. Three actions: `stop_new_signals` /
`force_exit_only` / `halt_strategy`. See [`alerting-batch-live.md`](/codex/04-architecture/alerting-batch-live.md) for
tier table.

### Live-pipeline alerting tier-up — concrete rule wiring

Three tiers of severity, each consuming `StreamingHealthSnapshot` fields. Tier 2 + 3 are wired through Tab 5's
KillSwitchBus rule structure (alerting-service `triggers_kill_switch=True` flag); tier 1 is page-only.

| Tier | Trigger condition                                                      | Source field                                | Action                                                      |
| ---- | ---------------------------------------------------------------------- | ------------------------------------------- | ----------------------------------------------------------- |
| 1    | `last_event_age_seconds > 30` OR `zero_activity_bar_rate > 0.05`       | `StreamingHealthSnapshot`                   | Page on-call (tier 1 alerting-service rule, no kill)        |
| 2    | `consumer_lag_pending > 1000` for 60s OR `last_event_age_seconds > 60` | `StreamingHealthSnapshot` + duration window | KILL_SWITCH_STREAM_LAG → halts all execution-service trades |
| 3    | No events on any active shard for > 5min                               | Cross-shard aggregate                       | KILL_SWITCH_PIPELINE_DEAD → halts all strategies + alerts   |

`StreamingHealthSnapshot` is the cross-cutting input to all three rules — alerting-service rule definitions reference
the field names verbatim so changing the snapshot shape is a deliberate, reviewable delta. Reference rule definitions
land in alerting-service rule structure (Tab 5 owns); this doc is the design contract.

## Instrument lifecycle = event-publish + cache-delta hot-reload

instruments-service publishes `INSTRUMENT_CACHE_REFRESH_TRIGGER` after every successful catalog refresh. Downstream MTDS
/ MDPS / features-service consume + diff their cache + hot-reload affected state. Same pattern as `ApiKeyReloader`. NOT
a new dedicated stream type. See
[`instrument-lifecycle-cache-delta-hot-reload.md`](/codex/04-architecture/instrument-lifecycle-cache-delta-hot-reload.md).

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

## UTL primitives shipped 2026-05-08 (Tab 2 live-pipeline activation)

Concrete UTL helpers landed for the May-23 cutover:

| UTL module                                                                                                | Purpose                                                                                                                      | Plan phase                       |
| --------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- | -------------------------------- |
| `unified_trading_library.streaming.compute_streaming_health` + `StreamingHealthSnapshot`                  | Health-API `data_freshness` snapshot — last-event-age, consumer-lag, replay-watermark, zero-activity-bar rate                | Phase 8 (UTL@d08c50c3)           |
| `unified_trading_library.streaming.StreamPublisher` / `StreamConsumerGroup`                               | Redis Streams XADD + MAXLEN producer + XREADGROUP + XACK + XAUTOCLAIM consumer (Pydantic-event-agnostic)                     | Phase 2A (UTL@f24e651b)          |
| `unified_trading_library.streaming.ReplayPublisher` / `ReplayWatermarkKV`                                 | Replay-cascade publisher preserving original `period_end` + per-shard watermark KV guarding double-publish                   | Phase 2C (UTL@f24e651b)          |
| `unified_trading_library.streaming.UTCAlignedScheduler` / `BoundaryTick`                                  | UTC-aligned timeframe scheduler firing on closed boundaries with grace window (NTP-tolerant)                                 | Phase 2B (UTL@8c67df5d)          |
| `unified_trading_library.instrument_lifecycle_cache_delta_reloader.InstrumentLifecycleCacheDeltaReloader` | Hot-reload primitive mirroring `ApiKeyReloader` — diffs catalog snapshots + dispatches `(CatalogDelta, snapshot)` callbacks  | Phase 10 (UTL@54d658e8)          |
| `unified_trading_library.honest_coverage_ratchet.assert_no_regression` + `compute_coverage_table`         | Workspace QG ratchet — fails CI on per-(asset_group, data_type) coverage regression > 0.5pp OR floor breach (default 99pp)   | Writegate Phase 5 (UTL@59996210) |
| `unified_trading_library.batch_live_reconciler.reconcile_shard` + `BatchLiveReconciliationReport`         | Master-plan Group F readiness gate — proves batch=live for the cutover; verdicts MATCH / ROW_COUNT / SCHEMA / VALUE mismatch | Phase 12 (UTL@908b1647)          |

UAC top-level facade extended at UAC@b02335d to surface `PipelineMode` + `is_batch` / `is_live` / `source_string_for` /
`pipeline_mode_for_source` per Citadel Import Rules. UTL streaming package facade extended at UTL@858f3c84 to publish
`StreamPublisher` / `StreamConsumerGroup` / `ReplayPublisher` / `ReplayWatermarkKV` from a single import surface.

## Phase 4 + 5 + 6 design contracts shipped 2026-05-11 (Tab 4 slot 4 design-ahead)

The streaming-aggregation + features-runner class signatures are landed as **design-only stubs** ahead of Phase 7 of
`features_repo_consolidation_2026_05_08` (Harsh slot 2). Consumers (MDPS `cli/main.py` + the consolidated
features-service CLI) compile against the published shapes; method bodies raise `NotImplementedError` until the gating
plan unblocks implementation. Shipped 2026-05-11 by Ikenna slot 4.

| Design contract                                                                                        | Purpose                                                                                                                                                                                                                                                                                                         | Plan phase                            |
| ------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------- |
| `unified_api_contracts.events.streaming.FeaturesComputedEvent`                                         | Features-service per-(feature_family, feature_group, shard) compute emission. Mirrors `CandleComputedEvent`'s data-freshness + emission-outcome propagation rules; per-shard fields nullable for cross-instrument families.                                                                                     | Phase 5.1.d (UAC@`e55651b`)           |
| `unified_trading_library.streaming.MDPSStreamingAggregator` + `AggregatorConfig`                       | Per-asset-group MDPS streaming cluster contract. Subscribes to `streaming.{ag}.candle_boundary_crossed` → fetches ticks → aggregates OHLCV → writes via candle_writer → emits `CandleComputedEvent`. Live = batch cascade + 4-category gap semantics + RSS-pause integration + cluster validation propagation.  | Phase 4 (UTL@`58bfbbeb`)              |
| `unified_trading_library.streaming.TickFetcher` / `InstrumentCatalogGate` / `TimeframeDAG`             | Caller-supplied Protocols for the aggregator's per-event decision tree.                                                                                                                                                                                                                                         | Phase 4 (UTL@`58bfbbeb`)              |
| `unified_trading_library.feature_service_base.AssetScopedFeaturesRunner` + `AssetScopedRunnerConfig`   | One-VM-per-asset_group features-service live runner. Subscribes to `streaming.{ag}.candle_computed` → resolves which feature_groups in family fire → computes via write-gate → publishes `FeaturesComputedEvent`.                                                                                               | Phase 5 (UTL@`58bfbbeb`)              |
| `unified_trading_library.feature_service_base.CrossCuttingFeaturesRunner` + `CrossCuttingRunnerConfig` | Cross-asset-group fan-in runner via `WatermarkAlignmentFanin`. Emits cross-instrument features (e.g. `cross_instrument.lst_yield_vs_eth_spot` for `carry_staked_basis`, `cross_instrument.perp_funding_vs_spot_basis` for `ARBITRAGE_PRICE_DISPERSION`). Degraded propagation + clock-skew rules per Phase 6.2. | Phase 6 (UTL@`58bfbbeb`)              |
| `deployment_api.routes.data_status.LiveStatusRow` + `LiveStatusResponse` + `GET /api/data-status/live` | Phase 11.1 endpoint contract — pivots manifest by `pipeline_mode=live_websocket` + joins per-shard health (staleness, degraded-ratio-60s, cluster-pct-skipped-60s, last-candle-emitted-at). Returns empty until Phase 5/6 live producers ship.                                                                  | Phase 11.1 (deployment-api@`7d95dc9`) |
| `deployment-ui` `<LiveDataStatusTab/>` scaffold                                                        | Phase 11.3 component — renders the 4 states (loading / empty / populated / error) against the Phase 11.1 endpoint. Re-uses existing card / badge primitives.                                                                                                                                                    | Phase 11.3 (deployment-ui@`f3204ce`)  |

**Why design-only.** Phase 4 + 5 + 6 implementation needs the consolidated features-service deployable
(`features_repo_consolidation_2026_05_08` Phase 7) so the asset-scoped runner can subscribe to the per-asset-group
`streaming.{ag}.candle_computed` stream + import the family registry. Shipping the class signatures now lets MDPS +
features-service author the per-service callsites (`live_aggregator.py` + `features_service/live/`) against the stable
shapes; the methods get unblocked once consolidation lands. Phase 11 design-ahead lets deployment-ui wire the new tab
into the tabs surface (per `deployment_ui_lifecycle_tabs_2026_05_08`) without waiting for the live producer.

### Multi-timeframe cascade rule (Phase 4.2)

The 1m candle MUST derive from 4× 15s candles, NOT from raw ticks re-aggregated. Aggregator waits for `parent_fanout()`
(corrected 2026-07-31, was cited as a `parent_timeframe_fanout` field — the real symbol is
`market_data_processing_service.app.core.live_aggregator`'s `parent_fanout(parent: str) -> int` method; the counts
themselves check out: 4 for 1m-from-15s, 5 for 5m-from-1m, 3 for 15m-from-5m, 4 for 1h-from-15m, 24 for 1d-from-1h)
`CandleComputedEvent` emissions for a shard → feeds them through the SAME aggregation function as batch's
`_process_standard_timeframe` → emits the parent. **Live = batch symmetry — re-aggregating ticks for parent timeframes
diverges live from batch (batch uses cascade) and produces silent OHLCV drift across the timeframe DAG.**

### 4-category live gap semantics (Phase 4.3)

Mirrors CLAUDE.md "Four-category empty-output decision" with a WS-specific Cat (B') replacement for the batch
upstream-bias category. Five emission decisions, every per-event tree resolves to one:

| Category | Trigger                                                                   | Action                                                                                                                                                          |
| -------- | ------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **A**    | WS connected, ticks present                                               | FRESH emit, `emission_outcome=PUBLISHED_OK`, `data_freshness=FRESH`                                                                                             |
| **D**    | WS connected, no ticks, catalog says alive AND venue calendar says open   | Carried bar (O=H=L=C=prior_LTP, vol=0); shipped marker `staleness_seconds>0 + trade_count==0` (legacy label `data_freshness=ZERO_ACTIVITY_BAR`), `PUBLISHED_OK` |
| **A'**   | WS connected, no ticks, catalog says delisted/pre-listing OR venue closed | No emission; manifest `record_empty(reason=EXPECTED_*)` per writegate taxonomy                                                                                  |
| **B'/C** | WS disconnected mid-window OR malformed ticks filtered                    | STALE emit (carry-forward LTP), `data_freshness=STALE`, `emission_outcome=PUBLISHED_DEGRADED`                                                                   |
| **E**    | WS dead > `ws_dead_max_windows` (default 4) consecutive windows           | Stop emitting; alerting-service tier-1 fires CRITICAL                                                                                                           |

> **Marker reconciliation (B2, 2026-06-02):** the category-D carried bar's **as-shipped** identifying signal is
> `staleness_seconds > 0` AND `trade_count == 0` (dense forward-fill via MDPS `_finalize_session_grid`, 2026-06-02), NOT
> a standalone `zero_activity` flag (no code consumers). The `data_freshness=ZERO_ACTIVITY_BAR` label is the original
> design name retained for continuity. Prediction Category-D instead emits NaN-OHLC (nullable-OHLCV) bars. SSOT:
> `/codex/02-data/honest-absence-downstream-handling.md` § "Zero-activity-bar shape" banner +
> `/codex/06-coding-standards/adapter-finalization-contract.md`.

The catalog-aware `InstrumentCatalogGate` Protocol distinguishes A / D / A'. The aggregator NEVER emits a
`CandleComputedEvent` for Cat (A') — manifest's `record_empty` carries the absence signal; downstream consumers read the
manifest, not the absence of events. NaN placeholder bars are banned (per CLAUDE.md "Honest absence vs fake
placeholders").

### Cross-cutting fan-in propagation (Phase 6.2)

`CrossCuttingFeaturesRunner` uses `WatermarkAlignmentFanin` (shipped at UTL@858f3c84) to align multi-stream inputs to
the target window. Default grace = 500ms intra-zone. Outcome propagation:

| Upstream state                           | Output                                                                                        |
| ---------------------------------------- | --------------------------------------------------------------------------------------------- |
| All inputs FRESH                         | `PUBLISHED_OK`                                                                                |
| One stream `PUBLISHED_DEGRADED`          | `PUBLISHED_DEGRADED` (degraded propagation)                                                   |
| One stream missing > grace, critical     | `STALE_DATA` with `policy_decision_reason` naming the missing input                           |
| One stream missing > grace, non-critical | `PUBLISHED_OK` with NaN-fill for the missing column (per UAC required_inputs DAG declaration) |
| Clock-skew between streams               | Fan-in emits at LATEST watermark (conservative — never look-ahead)                            |

Per-family deployment matrix (Phase 5.3):

- `onchain` — colocated with defi MDPS.
- `sports` — colocated with sports MDPS.
- `commodity` — colocated with tradfi MDPS.
- `delta_one` / `volatility` — colocated with the asset_group of the underlying instruments (typically split into
  multiple VMs: delta_one-cefi, delta_one-defi, delta_one-tradfi).
- `multi_timeframe` — colocated with each asset_group's MDPS (lightweight, follows the candle stream natively).
- `calendar` / `cross_instrument` — run cross-cutting per `CrossCuttingFeaturesRunner` (their `required_inputs` span
  asset_groups uniformly).

### Phase 11 deployment-UI live tab surface

`GET /api/data-status/live` is a manifest-pivot-by-`pipeline_mode=live_websocket` endpoint joining per-shard health from
the consumer service's `make_health_router(data_freshness=...)` callback (Phase 8 already shipped at UTL@d08c50c3).
`LiveStatusRow` shard-key axes mirror v5 manifest exactly; the per-shard health metrics are:

- `staleness_seconds` — wall-clock seconds since last `CandleComputedEvent` for the shard. Maps to alerting tier 1 rule
  (`> 30`) per the alerting-tier table above.
- `degraded_ratio_60s` — fraction of last-60s emissions with `emission_outcome=PUBLISHED_DEGRADED`. Higher means more WS
  reconnects + carry-forward LTP bars (stale-not-missing rule firing).
- `cluster_pct_skipped_60s` — for bundled shards (options_chain / futures_chain / prediction canonical-question-group /
  sports per-fixture-bundle), fraction of expected_root_clusters that did NOT receive a CandleComputed in the last 60s.
  0 for non-bundled.
- `last_candle_emitted_at` — most recent `CandleComputedEvent.available_at` for the shard.

`capture_status` uses the 4-state writegate Phase 3.D.5 taxonomy (`captured` / `empty_confirmed` / `attempted_failed` /
`expected_unattempted`) — same closed set as the batch manifest, so the live tab can render the same
`TypedReasonBadges` + `FailurePillarStack` + `LeafSchemaModal` widgets as `DataStatusTab` (Phase 4 writegate widgets
reused per Phase 11.3 design).

Phase 11.4 ("Deploy live cluster") action fires the launchers under `deployment-service/scripts/vm/`
(`launch-mtds-live-{asset_group}.sh` + `launch-mdps-features-live-{asset_group}.sh` per Phase 13). Until the launchers
ship, the Deploy-Missing button degrades to "no launcher registered" per the workspace deploy-missing convention.

## Scenario tap points

Scenarios ride the **same prod codepath** as live + batch — per the reuse-prod-codepath principle in
[`/codex/04-architecture/scenario-injection-architecture.md`](/codex/04-architecture/scenario-injection-architecture.md).
Overlay mutations inject at exactly one of seven pipeline-tap layers (`ScenarioOverlayLayer` enum in UAC):

| Layer      | Pipeline boundary in this architecture                                     | Pre-cutover wire status           |
| ---------- | -------------------------------------------------------------------------- | --------------------------------- |
| `RAW_TICK` | MTDS adapter `_post_fetch` hook (tick / book / funding rows)               | DEFERRED — Phase 3.A post-cutover |
| `FEATURE`  | MDPS feature-layer hook (after honest-absence guard in orchestrator.py)    | DEFERRED — Phase 3.B post-cutover |
| `FEATURE`  | features-service `_compute_*` exit (per-calculator tap)                    | DEFERRED — Phase 3.C post-cutover |
| `SIGNAL`   | strategy-service `signal_generator` emit boundary                          | DEFERRED — Phase 3.D post-cutover |
| `ORDER`    | execution-service order submit + matching-engine adversarial mode          | **WIRED** — Phase 3.E pre-cutover |
| `EVENT`    | Cross-cutting event stream injection (chain-slot / venue-halt / tx-status) | DEFERRED — post-cutover           |
| `MANIFEST` | ManifestWriter `record_*` hook (phantom-row or honest-empty injection)     | DEFERRED — Phase 3.G post-cutover |

**Reuse-prod-codepath note**: the harness does NOT instantiate a parallel backtest engine. It observes the unified
pipeline (MTDS → MDPS → features-\* → strategy-service ↔ position-balance + risk +
execution-service-in-matching-engine-mode) with one well-bounded overlay layer per run. `synthetic=true` metadata on
every emitted event distinguishes scenario-fire from real-fire so alerting-service suppresses paging while still
recording the event.

All layers except `ORDER` are post-cutover scope per
[`simulation_scenarios_post_cutover_2026_06_01.md`](../../plans/archive/2026_05/simulation_scenarios_post_cutover_2026_06_01.md).
For the full authoring guide, mutation types, and outcome-assertion categories, see
[`/codex/04-architecture/scenario-injection-architecture.md`](/codex/04-architecture/scenario-injection-architecture.md).

## Anti-patterns

- Don't emit partial candles on MTDS startup — UTC alignment scheduler blocks until next aligned boundary.
- Don't compute 1m candle from raw ticks in live mode — derive from 4× 15s candles (same path as batch).
- Don't skip a candle when WS disconnects mid-window — emit STALE + PUBLISHED_DEGRADED. Stale-not-missing.
- Don't add an `INSTRUMENT_LIFECYCLE_CHANGED` parallel stream — use the cache-delta hot-reload pattern.
- Don't introduce `pipeline_mode=replay` — replay writes to `pipeline_mode=live_websocket` with original-time
  `available_at`.

## Cross-references

- Plan:
  [`live_pipeline_mtds_mdps_features_2026_05_08`](../..//plans/archive/2026_05/live_pipeline_mtds_mdps_features_2026_05_08.md)
- Pre-req plan:
  [`features_repo_consolidation_2026_05_08`](../../plans/archive/features_repo_consolidation_2026_05_08.plan.md)
- Pre-req plan:
  [`gcs_migration_bundle_pipeline_mode_2026_05_08`](../../plans/archive/2026_05/gcs_migration_bundle_pipeline_mode_2026_05_08.md)
- Sibling docs: [`replay-subsystem.md`](./replay-subsystem.md),
  [`/codex/02-data/pipeline-mode-partition.md`](/codex/02-data/pipeline-mode-partition.md),
  [`/codex/04-architecture/instrument-lifecycle-cache-delta-hot-reload.md`](/codex/04-architecture/instrument-lifecycle-cache-delta-hot-reload.md)
- Foundation docs:
  [`/codex/04-architecture/batch-live-architecture.md`](/codex/04-architecture/batch-live-architecture.md)
- Scenario injection:
  [`/codex/04-architecture/scenario-injection-architecture.md`](/codex/04-architecture/scenario-injection-architecture.md)
  — tap-layer enum + reuse-prod-codepath contract (single SSOT — replaces former batch-live-pipeline.md +
  batch-live-symmetry.md),
  [`/codex/02-data/availability-manifest-and-data-status.md`](/codex/02-data/availability-manifest-and-data-status.md)
