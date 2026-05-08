---
name: live-pipeline-mtds-mdps-features-2026-05-08
overview:
  Activate the live (websocket-streaming) pipeline for MTDS → MDPS → features-service across all five asset_groups
  ahead of the 2026-05-23 DeFi cutover. Topology: MTDS as a standalone cluster (websocket connection-pool concerns
  isolated from compute); MDPS + features-service-asset-scoped colocated per asset_group with in-process MDPS→features
  handoff; features-service-cross-cutting as a separate flavor of the same consolidated image, subscribing to multiple
  asset_groups' Redis Streams. Cascade: MTDS emits `CANDLE_BOUNDARY_CROSSED` on Redis Streams every aligned 15s with a
  small grace window; MDPS aggregates ticks → emits `CANDLE_COMPUTED`; features-service consumes `CANDLE_COMPUTED` and
  runs feature_groups whose UAC `required_inputs` DAG is satisfied. UTC midnight alignment is enforced end-to-end so
  batch-vs-live reconciliation is purely a `pipeline_mode=` GROUP-BY (no partial-candle cleanup; services boot at any
  order and sync at the next aligned boundary). Gap semantics extend the existing 4-category tree to live with the
  stale-not-missing rule wired to `ServiceEmissionPolicy.PUBLISHED_DEGRADED` (strategy refuses new signals on degraded,
  allows exits, fully blocks on `BLOCKED`). Health-API (already QG-enforced as ERROR per workspace STEP 5.62) extends
  with `last_candle_emitted_at` / `staleness_seconds` / `degraded_ratio_60s` / `cluster_pct_skipped_60s`; alerting-
  service polls + subscribes + drives circuit breakers wired to strategy-service. Instrument-lifecycle change handling
  uses the event-publish + downstream cache-delta hot-reload pattern (mirrors `ApiKeyReloader` — NOT a new dedicated
  stream). Replay subsystem covers intraday-restart gap windows with smooth handoff to live at the next aligned
  boundary. Pre-requisite: `features_repo_consolidation_2026_05_08` reaches Phase 7 (8 repos archived, consolidated
  features-service deployable) before Phase 5 here.
type: code
epic: epic-deployment
status: active

asset_group: cross-cutting
priority: P0
deadline: 2026-05-23
parent: master_to_live_defi_2026_05_23
locked_by: live-defi-rollout
locked_since: 2026-05-08
last_updated: 2026-05-08

completion_gates:
  code: C5
  deployment: D3
  business: B4

repo_gates:
  - repo: unified-api-contracts
    code: C0
    deployment: none
    business: none
  - repo: unified-trading-library
    code: C0
    deployment: none
    business: none
  - repo: market-tick-data-service
    code: C0
    deployment: none
    business: none
  - repo: market-data-processing-service
    code: C0
    deployment: none
    business: none
  - repo: features-service
    code: C0
    deployment: none
    business: none
  - repo: instruments-service
    code: C0
    deployment: none
    business: none
  - repo: alerting-service
    code: C0
    deployment: none
    business: none
  - repo: strategy-service
    code: C0
    deployment: none
    business: none
  - repo: deployment-api
    code: C0
    deployment: none
    business: none
  - repo: deployment-ui
    code: C0
    deployment: none
    business: none
  - repo: deployment-service
    code: C0
    deployment: none
    business: none
  - repo: unified-trading-pm
    code: C0
    deployment: none
    business: none

depends_on:
  - features-repo-consolidation-2026-05-08
  - gcs-migration-bundle-pipeline-mode-2026-05-08
  - alerting-service-live-rules-2026-05-07
  - writegate-honest-coverage-endtoend-2026-05-06
  - instruments-live-master-2026-05-08

todos:
  - id: phase-0-pre-audit-live-pipeline
    content: |
      - [x] [AGENT] P0. Phase 0 — Pre-audit manifest for the live pipeline. Produce
        `unified-trading-pm/plans/active/issues/live_pipeline_preaudit_2026_05_08.md` enumerating:
        (a) every existing MTDS adapter that already has a websocket / streaming code path (not all venues do —
            CCXT REST-only venues need a poll fallback), and per-venue connection-pool / rate-limit / IP-redundancy
            constraints (CloudFront cooldowns for Lighter / Pacifica per `feedback_lighter_pacifica_cloudfront_quirks`,
            singleton-lock pattern for SFI / prediction-API venues, per-key throttling for Bybit/Binance);
        (b) every site in MTDS / MDPS / features-* that currently writes to GCS — confirm every write path is
            already migrated to `ManifestWriter.record_captured` / `record_empty` / `record_failed` /
            `record_expected_empty` per writegate Phase 2 (so the `pipeline_mode` column propagates without
            adapter-by-adapter touchwork);
        (c) the MTDS RSS-pause + `ParallelPerSymbolRunner` integration status (per
            `project_mtds_parallelization_fix_2026_05_07` memory: as of 2026-05-07 the wiring agent was dispatched
            but RSS-pause integration was PENDING — verify before Phase 3 starts that the pause hook is wired,
            otherwise add a sub-todo here);
        (d) every existing event published by MTDS / MDPS / features-* / instruments-service — catalog
            per-service event names + payloads + `unified_api_contracts.events.*` registration status, so Phase 1
            knows which events are NEW vs which already exist;
        (e) every consumer of `ServiceEmissionPolicy` shipped 2026-05-08 (UAC@58c3b61 slice (a) + UTL@1a7e1d4b)
            — Phase 8 wires the policy decision into MDPS / features candle emission paths, but the consumer
            list (strategy-service / position-balance-monitor / risk-and-exposure / pnl-attribution) needs an
            explicit row-by-row mapping;
        (f) every existing usage of `ApiKeyReloader` / `start_domain_config_reloaders` so Phase 10's
            instrument-cache-delta hot-reload pattern can mirror the exact shape;
        (g) every existing Redis dependency in the workspace — `grep -rn "redis\." across all repos — and
            whether any are using Streams or just KV; Phase 2 needs to know whether to add `redis>=5.0` (Streams
            require ≥5) to UTL's deps or whether it's already present.
        Output committed under `plans/active/issues/`. Subsequent phases reference the artifact.
    status: done
    note: "PM@12483f5b — 408-line audit doc shipped 2026-05-08 by tab2-pre-audit sub-agent. Covers all 7 audit subsections (a-g) with file:line / commit-sha / count evidence + 10 cross-cutting Phase-3-13 sub-todos + per-consumer wire-in tables for Phases 8 + 10. Notable: MTDS RSS-pause WIRED 2026-05-08 (cli/main.py:103-128) — auto-memory `project_mtds_parallelization_fix_2026_05_07` 'RSS-pause PENDING' claim is now stale; `redis>=5.0` already declared in UTL pyproject."

  - id: phase-1-uac-streaming-events
    content: |
      - [x] [AGENT] P0. Phase 1 — UAC streaming event types. PARALLEL with Phase 2A.

        Site: `unified-api-contracts/unified_api_contracts/events/streaming.py` (NEW module).

        New event types as Pydantic models extending the existing `EmissionLifecycleEvent` shape from
        UAC@58c3b61:

        ```python
        class CandleBoundaryCrossedEvent(BaseModel):
            event_type: Literal["CANDLE_BOUNDARY_CROSSED"]
            asset_group: AssetGroup
            venue: str
            chain: str | None
            instrument_id: str | None
            data_type: DataType
            instrument_type: str | None
            league_id: str | None
            timeframe: str   # "15s", "1m", "5m", ...
            period_start: datetime  # UTC, aligned to timeframe boundary
            period_end: datetime    # UTC, aligned (period_start + timeframe)
            tick_count: int         # number of source ticks captured for the window
            available_at: datetime  # when MTDS finalised the window (= period_end + grace)
            data_freshness: Literal["FRESH", "STALE"]  # STALE if WS reconnect mid-window
            pipeline_mode: PipelineMode                  # always "live_websocket" for this event
            correlation_id: str
            vm_name: str

        class CandleComputedEvent(BaseModel):
            event_type: Literal["CANDLE_COMPUTED"]
            # same shard-key columns as CandleBoundaryCrossedEvent
            ...
            row_count: int          # rows in the emitted candle parquet (1 per window for OHLCV)
            available_at: datetime  # when MDPS finalised the candle (= window_close + aggregation latency)
            data_freshness: Literal["FRESH", "STALE", "ZERO_ACTIVITY_BAR"]
            emission_policy: ServiceEmissionPolicy   # PUBLISHED_OK / PUBLISHED_DEGRADED / STALE_DATA / BLOCKED
            policy_decision_reason: str | None
            pipeline_mode: PipelineMode
            correlation_id: str
            vm_name: str

        class InstrumentCacheRefreshTriggerEvent(BaseModel):
            event_type: Literal["INSTRUMENT_CACHE_REFRESH_TRIGGER"]
            # Published by instruments-service after every successful catalog refresh.
            # Downstream MTDS / MDPS / features-service consume this + diff their cache.
            # Shape mirrors EmissionLifecycleEvent so existing event subscribers don't need a new code path.
            asset_group: AssetGroup
            catalog_refresh_at: datetime       # when the catalog parquet was finalised
            row_count_total: int
            row_count_added_since_last: int    # 0 if no delta — consumers skip cache refresh
            row_count_removed_since_last: int
            correlation_id: str
            vm_name: str
        ```

        `PipelineMode` StrEnum lives at `unified_api_contracts/canonical/crosscutting/pipeline_mode.py` (NEW —
        coordinated with `gcs_migration_bundle_pipeline_mode_2026_05_08` Phase 1A; one of the two plans owns
        this enum, recommend the migration plan owns it because it ships first chronologically).

        Tests `unified-api-contracts/tests/unit/test_streaming_events.py`:
        (1) JSON serialization round-trip for all 3 events;
        (2) `period_end - period_start == parse_timeframe(timeframe)` invariant on CandleBoundaryCrossedEvent;
        (3) `data_freshness` closed-set values exactly;
        (4) `emission_policy` defaults to `PUBLISHED_OK` when not specified.

        QG: UAC quality-gates.sh clean.
    status: done
    note: "UAC@8bc3f2a (PipelineMode SSOT) + UAC@b643c9a (Phase 1 streaming events: CandleBoundaryCrossedEvent / CandleComputedEvent / InstrumentCacheRefreshTriggerEvent + EmissionOutcome closed-set + parse_timeframe + 17 unit tests) + UAC@b02335d (top-level facade: PipelineMode + is_batch / is_live / source_string_for / pipeline_mode_for_source surfaced from `unified_api_contracts` per Citadel Import Rules). Module at `unified_api_contracts/events/streaming.py`. CandleComputedEvent carries BOTH `emission_policy` (POLICY) AND orthogonal `emission_outcome` (OUTCOME — PUBLISHED_OK / PUBLISHED_DEGRADED / STALE_DATA / BLOCKED). All events default `pipeline_mode` to LIVE_WEBSOCKET. **QG state 2026-05-08 PM (RESOLVED)**: foreign blockers cleared — ORACLE_COVERAGE_START shipped at UAC@3adee82 (Tab 1 DeFi-launch); EN DASH at alerting/thresholds.py:60 already replaced by HYPHEN-MINUS. Issue `plans/active/issues/uac_utl_qg_blockers_2026_05_08.md` marked RESOLVED."

  - id: phase-2a-utl-redis-streams-client
    content: |
      - [x] [AGENT] P0. Phase 2A — UTL Redis Streams client wrapper. PARALLEL with Phase 1.

        Site: `unified-trading-library/unified_trading_library/streaming/redis_stream.py` (NEW).

        Helper API (matches existing UTL helper-shape, e.g. `ApiKeyReloader`, `ManifestWriter`):

        ```python
        class StreamPublisher:
            def __init__(self, *, redis_url: str, stream_name: str, max_len_approx: int = 100_000): ...
            def publish(self, event: BaseModel) -> str: ...   # returns Redis stream ID; XADD with MAXLEN ~
            def close(self) -> None: ...

        class StreamConsumerGroup:
            def __init__(self, *, redis_url: str, stream_name: str, group_name: str, consumer_name: str,
                         deserialize_to: type[BaseModel]): ...
            def read_blocking(self, *, count: int = 10, block_ms: int = 5_000) -> list[tuple[str, BaseModel]]:
                # XREADGROUP, blocking up to block_ms; returns list of (stream_id, deserialized_event).
                ...
            def ack(self, stream_ids: list[str]) -> None: ...   # XACK
            def claim_pending(self, *, idle_threshold_ms: int = 60_000) -> list[tuple[str, BaseModel]]:
                # XAUTOCLAIM — recover crashed consumers' pending messages after idle_threshold_ms.
                ...
            def close(self) -> None: ...
        ```

        Stream-name convention: `streaming.{asset_group}.{event_type}` (lowercase, dot-separated). Group
        names per consumer service: `mdps`, `features-asset-scoped`, `features-cross-cutting`. Consumer
        names per VM: `${VM_NAME}` (matches workspace per-VM-shard-isolation convention).

        Tests `unified-trading-library/tests/unit/test_redis_stream.py` using `fakeredis>=2.20`:
        (1) publish + read round-trip;
        (2) consumer group fan-out — two consumers in different groups both receive every message;
        (3) consumer group load-balance — two consumers in the SAME group split the messages;
        (4) ack semantics — un-acked messages remain in the pending list;
        (5) `claim_pending` recovers messages from a stalled consumer after the idle threshold;
        (6) `MAXLEN ~` trim — stream length stays bounded under load.

        Add `redis>=5.0` and `fakeredis>=2.20` (test-only — but workspace flat-deps rule means it goes in
        `[project.dependencies]` not `[project.optional-dependencies.test]`) to UTL pyproject if Phase 0 § (g)
        confirms they're not already present.

        QG: UTL quality-gates.sh clean.
    status: done
    note: "UTL@f24e651b — `unified_trading_library/streaming/redis_stream.py` (StreamPublisher + StreamConsumerGroup; XADD + MAXLEN ~ + XREADGROUP + XACK + XAUTOCLAIM + idempotent XGROUP CREATE) + `replay.py`. 6 unit tests via fakeredis. Event-class-agnostic (generic BaseModel TypeVar). fakeredis>=2.20 added to pyproject (flat-deps). `redis>=5.0` already present. Companion UTL@87134364 added pipeline_mode kwarg to ManifestWriter (gcs_migration plan Phase 1B). UTL QG blocked by foreign UAC breakage at conftest import — see `plans/active/issues/uac_utl_qg_blockers_2026_05_08.md`."

  - id: phase-2b-utl-utc-aligned-scheduler
    content: |
      - [x] [AGENT] P0. Phase 2B — UTL UTC-aligned timeframe scheduler. SEQUENTIAL after Phase 2A.

        Site: `unified-trading-library/unified_trading_library/streaming/utc_aligned_scheduler.py` (NEW).

        Helper:
        ```python
        class UTCAlignedScheduler:
            """
            Fires a callback at every aligned timeframe boundary, with grace window for late ticks.

            On startup, BLOCKS until the next aligned boundary — never fires for partial windows.
            E.g. UTCAlignedScheduler(timeframe="15s", grace_seconds=1.0) booted at 14:23:07.4 UTC fires
            its first callback at 14:23:16.0 UTC for window [14:23:00, 14:23:15] (period closed at
            14:23:15 + 1s grace).
            """
            def __init__(self, *, timeframe: str, grace_seconds: float = 1.0,
                         on_boundary: Callable[[BoundaryTick], None]): ...
            async def run_forever(self) -> None: ...
            def stop(self) -> None: ...

        @dataclass(frozen=True)
        class BoundaryTick:
            timeframe: str
            period_start: datetime  # UTC, aligned
            period_end: datetime    # UTC, aligned
            wall_clock_at_fire: datetime  # period_end + grace
        ```

        Tests `unified-trading-library/tests/unit/test_utc_aligned_scheduler.py` using `freezegun`:
        (1) booted at 14:23:07.4 UTC for timeframe="15s" — first callback fires at 14:23:16.0 UTC;
        (2) `period_start` + `period_end` always aligned to the timeframe (00, 15, 30, 45 for 15s; 00 for 1m);
        (3) on stop, `run_forever` returns cleanly without firing pending callbacks;
        (4) clock-jump (NTP sync skews wall-clock) — assert next-fire-time recomputed against new wall-clock;
        (5) timeframe parsing — supports "15s", "1m", "5m", "15m", "1h", "1d" (canonical workspace set).

        QG: UTL quality-gates.sh clean.
    status: done
    note: "UTL@8c67df5d — `unified_trading_library/streaming/utc_aligned_scheduler.py` ships UTCAlignedScheduler async class + BoundaryTick frozen dataclass; supports 15s/1m/5m/15m/1h/1d timeframes; recomputes next-fire time against datetime.now(UTC) each iteration (NTP-tolerant); 5 tests via freezegun. UTL@858f3c84 — package `unified_trading_library.streaming.__init__.py` now publishes UTCAlignedScheduler + BoundaryTick + StreamPublisher + StreamConsumerGroup + ReplayPublisher + ReplayWatermarkKV from one import surface (Citadel facade pattern)."

  - id: phase-2c-utl-replay-cascade-helpers
    content: |
      - [x] [AGENT] P1. Phase 2C — UTL replay-cascade helpers. PARALLEL with Phase 2B.

        Site: `unified-trading-library/unified_trading_library/streaming/replay.py` (NEW).

        Helper:
        ```python
        class ReplayPublisher:
            """
            Publishes historical CandleBoundaryCrossedEvent / CandleComputedEvent to the live Redis Stream
            for downstream replay. Stamps event timestamps to ORIGINAL window times (not replay-execution
            time), preserving the live-pipeline semantics. Coordinates handoff to the live publisher via a
            per-shard `replay_watermark` Redis key — replay owns the stream up to the watermark; live takes
            over at the next aligned boundary past the watermark.
            """
            def __init__(self, *, stream_publisher: StreamPublisher,
                         watermark_kv: ReplayWatermarkKV): ...
            def publish_window(self, event: CandleBoundaryCrossedEvent | CandleComputedEvent) -> None: ...
            def finalize(self, *, target_period_end: datetime) -> None:
                """Flag replay complete up to `target_period_end`; live consumer at the same shard takes over
                at the next aligned boundary."""

        class ReplayWatermarkKV:
            """Per-shard Redis KV: replay_watermark.{asset_group}.{shard_key} → ISO timestamp."""
            def get(self, shard_key: str) -> datetime | None: ...
            def set(self, shard_key: str, period_end: datetime) -> None: ...
        ```

        Tests `unified-trading-library/tests/unit/test_replay.py` using `fakeredis`:
        (1) publish_window round-trip with original-time timestamps preserved;
        (2) finalize sets the watermark KV and live consumer at the same shard sees the watermark;
        (3) double-publish protection — replay + live racing on the same window emits ONLY ONE event
            (consumer-side dedupe via the watermark KV check; live publisher refuses to publish for
            period_end ≤ replay_watermark);
        (4) replay tail at watermark — replay finalize at 14:23:00 + live publisher firing at 14:23:15
            both seen by consumer with no gap and no duplicate.

        QG: UTL quality-gates.sh clean.
    status: done
    note: "UTL@f24e651b — `unified_trading_library/streaming/replay.py` ships ReplayPublisher.publish_window (preserves original period_end + refuses publish for period_end ≤ current_watermark) + ReplayPublisher.finalize (advances per-shard watermark KV; rejects backwards) + ReplayWatermarkKV at `replay_watermark.{shard_key}` → ISO-8601 UTC. 4 unit tests via fakeredis (publish-window round-trip, finalize-advance, double-publish-protection, watermark-tail-handoff). UTL@858f3c84 lifted ReplayPublisher + ReplayWatermarkKV into the `unified_trading_library.streaming` package surface."

  - id: phase-3-mtds-streaming-rollout
    content: |
      - [ ] [AGENT] P0. Phase 3 — MTDS websocket streaming rollout per asset_group. SEQUENTIAL after Phase 1 + 2.

        Site: `market-tick-data-service/market_tick_data_service/adapters/*.py` and
        `market_tick_data_service/cli/main.py`.

        3.1 — Add a `--mode live` operational mode to MTDS CLI (current operations are batch-oriented per
             writegate plan). Live-mode dispatch routes to a NEW `live_runner.py` that:
             (a) wires `UTCAlignedScheduler` per `(asset_group, venue, data_type, timeframe)` shard atom from
                 the v5 SSOT;
             (b) opens websocket connections per shard via the existing per-venue adapter;
             (c) buffers ticks in-memory until the scheduler fires the boundary callback;
             (d) at boundary fire, packages the buffered ticks → emits `CandleBoundaryCrossedEvent` via
                 `StreamPublisher` to `streaming.{asset_group}.candle_boundary_crossed`;
             (e) writes the buffered ticks to GCS at the `pipeline_mode=live_websocket` partition (intra-day
                 5-15min flush cadence per `gcs_migration_bundle_pipeline_mode_2026_05_08` Phase 4 contract);
             (f) records to manifest via `record_captured` / `record_empty` per the existing 4-category tree.

        3.2 — Per-asset_group websocket adapters: verify each adapter's existing reconnect logic respects
             the WS-disconnect → STALE flag rule. On reconnect mid-window: emit the current window with
             `data_freshness="STALE"` + `emission_policy=PUBLISHED_DEGRADED`; do NOT skip the window
             (stale-not-missing rule per CLAUDE.md live-pipeline architecture memory + the live gap-semantics
             4-category tree).

        3.3 — Connection pool sizing per shard via NEW config `mtds_live_pool_size_per_shard` (default 1, can
             be tuned per venue for IP/key redundancy under CloudFront throttling). Pool size is per-shard
             config, NOT a manifest dimension (per workspace shard-SSOT rule — stays in v5 atom).

        3.4 — `INSTRUMENT_CACHE_REFRESH_TRIGGER` consumer in MTDS: subscribe to the
             `streaming.{asset_group}.instrument_cache_refresh_trigger` group → on receive, diff the current
             catalog cache against the new GCS catalog → subscribe new instruments / drop delisted ones.
             Implementation pattern mirrors `ApiKeyReloader` (Phase 10 codifies the cross-service pattern).

        3.5 — Per-venue rollout sequence (from highest-tick-volume to lowest, so we de-risk the heavy paths
             first):
             a. defi (chain × protocol shards — relatively low tick rate but the May-23 critical path);
             b. cefi spot/perp (highest tick rate, per-instrument or `(venue, N instrument)` chunk shard);
             c. cefi options/futures (bundled per-root; cluster validation must propagate through the
                live emission per writegate Phase 1A enforcement);
             d. tradfi (Databento WS where available; REST poll fallback for ETFs);
             e. sports (per `(source, league_id)` shard — odds_api WS where available; REST poll otherwise);
             f. prediction (per `(venue, canonical_question_group)` shard).

        Each rollout sub-step ships its own commit + smoke launch per workspace "no fire-and-forget VM
        launches" rule (event-verification protocol mandatory: STARTED within 60s, hourly progress events,
        STOPPED/FAILED on exit + non-empty metadata).

        Tests under `market-tick-data-service/tests/unit/test_live_runner.py` per asset_group + 6 per-venue
        smoke tests `tests/integration/test_live_smoke_<venue>.py` (skipped on CI without secrets, run
        manually pre-rollout).

        QG: MTDS quality-gates.sh clean per asset_group rollout.

        **Coordination**: `mtds_databento_path_streaming_2026_05_07` is for batch-side Databento streaming
        (path=tempfile + chunked to_df). Live-mode tradfi (3.5d) MAY use a different code path —
        Databento has a WS endpoint distinct from get_range. Phase 3.5d agent reads that plan's audit
        notes before designing the tradfi WS adapter; banner mutually.
    status: todo
    note: ""

  - id: phase-4-mdps-streaming-aggregation
    content: |
      - [ ] [AGENT] P0. Phase 4 — MDPS streaming aggregation cluster per asset_group. SEQUENTIAL after Phase 3.

        Site: `market-data-processing-service/market_data_processing_service/cli/main.py` +
        `live_workers.py` + a NEW `live_aggregator.py`.

        4.1 — Add `--mode live` to MDPS CLI dispatching to `live_aggregator.py`:
             (a) `StreamConsumerGroup` per `(asset_group, venue, data_type)` shard subscribes to
                 `streaming.{asset_group}.candle_boundary_crossed` with `group_name="mdps"`;
             (b) on each `CandleBoundaryCrossedEvent`, fetch the just-flushed tick parquet from GCS
                 (intra-day flush per Phase 3.1.e — path is deterministic from event payload);
             (c) aggregate ticks → produce OHLCV for the timeframe;
             (d) write the candle to GCS at `pipeline_mode=live_websocket` per
                 `gcs_migration_bundle_pipeline_mode_2026_05_08`;
             (e) emit `CandleComputedEvent` to `streaming.{asset_group}.candle_computed` with
                 `emission_policy` from the shipped `ServiceEmissionPolicy` SSOT (UAC@58c3b61 + UTL@1a7e1d4b).

        4.2 — Multi-timeframe cascade rule (CRITICAL — live=batch symmetry): the 1m candle MUST be derived
             from the 4× 15s candles, NOT from raw ticks. Same code path as batch. Implementation:
             `live_aggregator.py` waits for 4× CandleComputed{15s} events for a given shard → feeds them
             through the SAME aggregation function as batch's `_process_standard_timeframe` →
             emits CandleComputed{1m}. This rule extends to all parent timeframes (5m from 5×1m, 15m from
             3×5m, 1h from 4×15m) per the workspace timeframe DAG.

        4.3 — Live gap semantics (4-category tree applied per emission decision):
             (A) WS connected, no trades, catalog says alive → zero-activity bar (O=H=L=C=prior_LTP, vol=0)
                 with `data_freshness=ZERO_ACTIVITY_BAR`, `emission_policy=PUBLISHED_OK`;
             (A') WS connected, no trades, catalog says delisted/non-trading → no candle emitted; manifest
                 `record_empty(reason=EXPECTED_*)` per writegate taxonomy;
             (B/C) WS disconnected mid-window or malformed ticks → emit candle with
                 `data_freshness=STALE`, `emission_policy=PUBLISHED_DEGRADED`, carry-forward LTP. Stale-not-
                 missing rule;
             (D) WS dead >N consecutive windows → stop emitting CandleComputed for the shard; alerting-
                 service (Phase 9) fires CRITICAL.

        4.4 — RSS-pause integration: live-aggregator subscribes to `ResourceProfiler.on_memory_warning` per
             `mdps_streaming_and_backpressure_2026_05_07` Phase 2 contract — on warning, pause new
             `XREADGROUP` calls + drain in-flight aggregations cleanly. Coordinate with that plan's agent
             so the backpressure shape is identical between batch and live.

        4.5 — Cluster validation propagates for bundled shards (options_chain / futures_chain / sports
             per-fixture-bundle / prediction canonical-question-group) via `record_captured`'s required
             `expected_root_clusters` + `cluster_extractor` kwargs per writegate Phase 1A.

        Tests `market-data-processing-service/tests/unit/test_live_aggregator.py`:
        (1) candle_boundary → candle_computed round-trip with full window;
        (2) timeframe cascade — 4× 15s emission triggers 1× 1m emission with derived OHLCV;
        (3) zero-activity bar — empty window produces ZERO_ACTIVITY_BAR candle with prior_LTP;
        (4) stale window — WS reconnect mid-window produces PUBLISHED_DEGRADED candle;
        (5) catalog-delisted — instrument-cache says delisted, no candle emitted, manifest record_empty;
        (6) cluster validation — bundled shard without expected_root_clusters raises
            MissingClusterValidationError (writegate Phase 1A enforcement preserved).

        QG: MDPS quality-gates.sh clean.

        **Coordination**: `mdps_streaming_and_backpressure_2026_05_07` Phase 1 ships the
        `open_candle_writer` / `close_candle_writer` UTL lifecycle. Phase 4 of THIS plan re-uses that
        lifecycle for live aggregation writes (same shard atomicity contract, same per-VM tempfile +
        rename, same single-`record_captured` per shard). That plan must reach its Phase 1.2 (MDPS
        callsite migration) before Phase 4 here lands.
    status: todo
    note: ""

  - id: phase-5-features-asset-scoped-flavor
    content: |
      - [ ] [AGENT] P0. Phase 5 — features-service asset-scoped flavor (live-mode). SEQUENTIAL after
        Phase 4 + features-repo-consolidation Phase 7.

        Site: `features-service/features_service/cli/main.py` + a NEW `features_service/live/`.

        5.1 — Add `--mode live` to consolidated features-service CLI per
             `codex/06-coding-standards/cli-convention.md`. Live-mode dispatch:
             (a) `StreamConsumerGroup` subscribed to
                 `streaming.{asset_group}.candle_computed` with
                 `group_name="features-asset-scoped-{asset_group}"`;
             (b) on each `CandleComputedEvent`, look up which feature_groups in the loaded family have
                 `required_inputs` satisfied for this `(timeframe, shard_key, available_at)`;
             (c) compute features → write to GCS at `pipeline_mode=live_websocket` per migration plan;
             (d) emit a `FeaturesComputedEvent` (NEW UAC event extending the streaming module) so cross-
                 cutting features (Phase 6) can fan-in.

        5.2 — Asset-scoped deployment topology: ONE features-service VM per asset_group, colocated with
             that asset_group's MDPS VM. In-process MDPS→features handoff is OPTIONAL for the May-23
             cutover (Redis Stream hop is the contract; in-process is a perf optimisation). Initial
             rollout uses Redis Stream hop only — in-process optimisation lands post-May-23 if benchmarks
             show the Redis hop is the latency bottleneck.

        5.3 — Per-family deployment matrix:
             (a) `onchain` family — colocated with defi MDPS;
             (b) `sports` family — colocated with sports MDPS;
             (c) `commodity` family — colocated with tradfi MDPS;
             (d) `delta_one`, `volatility` — colocated with the asset_group of the underlying instruments
                 (typically split into multiple VMs: delta_one-cefi, delta_one-defi, delta_one-tradfi);
             (e) `multi_timeframe` — colocated with each asset_group's MDPS (lightweight, follows the
                 candle stream natively);
             (f) `calendar` — runs cross-cutting per Phase 6 because calendar events apply across asset
                 groups uniformly;
             (g) `cross_instrument` — runs cross-cutting per Phase 6 by definition.

        5.4 — `LookaheadBiasError` enforcement on every live compute: per the UTL lift in
             `features_repo_consolidation` Phase 5, every input row must satisfy
             `input.available_at <= target_ts - horizon`. Strict-mode raise; failed rows route to
             `record_failed(LookaheadBiasError(...))` with error_reason populated.

        Tests `features-service/tests/integration/test_live_asset_scoped.py`:
        (1) candle_computed → features_computed round-trip per family;
        (2) per-family `required_inputs` DAG enforcement — feature_group with unsatisfied input doesn't
            fire (`PREFLIGHT_SKIPPED` event with `reason=DEPENDENCIES_MISSING_CONTINUE`);
        (3) lookahead-bias guard — synthetic input with `available_at > target_ts - horizon` raises;
        (4) `emission_policy` propagates from CandleComputed{degraded} → FeaturesComputed{degraded}.

        QG: features-service quality-gates.sh clean.

        **Coordination**: STRICT BLOCKER on `features_repo_consolidation_2026_05_08` Phase 7 (8 source
        repos archived, consolidated repo deployable). Banner that plan with
        `🔴 BLOCKER FOR live_pipeline Phase 5`.
    status: todo
    note: ""

  - id: phase-6-features-cross-cutting-flavor
    content: |
      - [ ] [AGENT] P0. Phase 6 — features-service cross-cutting flavor. SEQUENTIAL after Phase 5.

        Site: `features-service/features_service/live/cross_cutting_runner.py` (NEW).

        6.1 — One cross-cutting features-service VM (or 2 for redundancy) subscribes to MULTIPLE
             `streaming.{asset_group}.candle_computed` + `features_computed` streams. The consumer-group
             name `features-cross-cutting` is unique per VM so each cross-cutting box reads independently
             (no load-balancing within the cross-cutting group; we want every box to see every event for
             feature recomputation).

        6.2 — Watermark + grace fan-in helper (per `features_repo_consolidation` Phase 5 lift to UTL —
             `WatermarkAlignmentFanin`): a cross-instrument feature waiting on N upstream streams emits
             when `min(stream_watermarks) > target_window_close + grace`. Default grace=500ms intra-zone.
             If one stream hits `PUBLISHED_DEGRADED` or doesn't arrive within grace, the cross-cutting
             feature also publishes `PUBLISHED_DEGRADED` (or `STALE_DATA` if the missing input is critical
             per the feature_group's DAG declaration).

        6.3 — Critical cross-cutting features for May-23 cutover:
             (a) `cross_instrument.lst_yield_vs_eth_spot` — needed for `carry_staked_basis` archetype.
                 Inputs: defi.uniswap_v3.eth_usdt + defi.lido.steth_yield + defi.jito.jitosol_yield (Solana,
                 Pyth-routed per CLAUDE.md DeFi pipeline section) + defi.marinade.msol_yield;
             (b) `cross_instrument.perp_funding_vs_spot_basis` — needed for `leveraged_funding_arb`
                 archetype. Inputs: cefi.bybit.btcusdt_perp_funding + cefi.bybit.btcusdt_spot +
                 cefi.binance.btcusdt_perp_funding + cefi.binance.btcusdt_spot.
             Both must be live + emitting CandleComputed at 15s cadence by 2026-05-21 (smoke + tune
             window).

        6.4 — Cross-asset-group features fan-in: a cross-cutting feature whose UAC `required_inputs` DAG
             spans multiple asset_groups (e.g. cefi + defi for ETH price-discovery) consumes from each
             asset_group's stream + uses the watermark fan-in to align inputs to the target window.

        Tests `features-service/tests/integration/test_live_cross_cutting.py`:
        (1) two-stream fan-in within grace → FeaturesComputedEvent emits with PUBLISHED_OK;
        (2) one-stream missing > grace → FeaturesComputedEvent emits with STALE_DATA + missing input
            flagged in `policy_decision_reason`;
        (3) one-stream PUBLISHED_DEGRADED → output PUBLISHED_DEGRADED (degraded propagation);
        (4) clock-skew between streams → fan-in still emits at the LATEST watermark (conservative).

        QG: features-service quality-gates.sh clean.
    status: todo
    note: ""

  - id: phase-7-replay-subsystem
    content: |
      - [ ] [AGENT] P0. Phase 7 — Replay subsystem. PARALLEL with Phase 6 (different code path).

        Site: NEW launcher `deployment-service/scripts/vm/launch-replay-cascade.sh` + NEW MTDS+MDPS+features
        replay entry-points.

        7.1 — Replay producer (MTDS-side): `market-tick-data-service/market_tick_data_service/replay/runner.py`
             takes `--mode replay --start <ISO> --end <ISO> --asset-group <ag> --shard-key <key>` and:
             (a) fetches the historical batch source (Databento / Tardis / exchange REST snapshot — same
                 sources as backfill);
             (b) iterates the historical window in aligned timeframe boundaries;
             (c) per boundary, builds a `CandleBoundaryCrossedEvent` with `available_at` stamped to the
                 ORIGINAL window's live-arrival time (per CLAUDE.md `available_at` is-per-row-write-time
                 rule + the source-priority semantic), NOT replay-execution time;
             (d) publishes via `ReplayPublisher` (Phase 2C) to the same Redis Stream the live producer uses;
             (e) finalizes the watermark KV at `replay_watermark.{asset_group}.{shard_key}` = end of
                 replay window.

        7.2 — Replay consumer (MDPS + features) reuses the SAME `live_aggregator.py` / `live/cross_cutting_runner.py`
             code path — replay events flow through the same `XREADGROUP` calls. Consumer doesn't know or
             care whether an event is replay or live; only the timestamps differ. Live publisher (MTDS in
             Phase 3) checks the watermark KV before publishing — refuses to publish for
             `period_end <= replay_watermark` to avoid double-publish at the handoff boundary.

        7.3 — Smooth handoff contract:
             - Replay catches up to `now - epsilon`;
             - Replay finalizes watermark at `now - epsilon`;
             - Live publisher's next-aligned-boundary check sees the watermark + skips emission for any
               `period_end <= watermark`;
             - First live emission is at the next aligned boundary past `now - epsilon`;
             - Consumer sees a continuous stream with no gap and no duplicate.

        7.4 — Multi-hour-outage backstop: if replay can't catch up to live (e.g. multi-hour outage caused
             a >24h gap), the replay finalizer halts at the historical-source coverage limit + emits a
             `REPLAY_BACKSTOP_REACHED` event. Strategy-service Phase 9 wires this to a manual-intervention
             gate — operator must explicitly resume after batch backfill catches up.

        Tests `market-tick-data-service/tests/integration/test_replay_runner.py` + corresponding
        `features-service/tests/integration/test_replay_consumer.py`:
        (1) replay produces N-window stream; consumer aggregates exactly N candles;
        (2) handoff smoothness — replay finalizes at T1, live producer fires at T1 + timeframe; consumer
            sees N+1 candles with no gap and no duplicate;
        (3) double-publish protection — replay + live racing within the watermark grace produces ONLY
            one event per shard-window;
        (4) backstop trigger — replay window > coverage limit emits `REPLAY_BACKSTOP_REACHED`.

        QG: MTDS + features-service quality-gates.sh clean.

        **Operationally**: replay VMs use the same launcher template as live VMs but with `--mode replay
        --start --end --shard-key` flags; register `replay-` VM-name prefix in `VM_PREFIX_TO_BUCKET` per
        workspace VM-naming rule.
    status: todo
    note: ""

  - id: phase-8-health-api-extension
    content: |
      - [x] [AGENT] P0. Phase 8 — Health-API extension across MTDS / MDPS / features-service.
        PARALLEL with Phase 7.

        Health-API is already QG-enforced as ERROR per CLAUDE.md "Service Infrastructure Requirements"
        STEP 5.62: every service has `api/main.py` with `make_health_router` from UTL with a
        `data_freshness` callback. Phase 8 extends the callback to expose live-pipeline-specific fields:

        8.1 — Add to UTL `make_health_router` `data_freshness` callback contract:
             ```python
             {
               "service": "<service_name>",
               "loaded_shards": [...],   # list of (asset_group, venue, data_type, ...) keys
               "shards": {
                 "<shard_key>": {
                   "last_candle_emitted_at": "<ISO>" | null,
                   "staleness_seconds": <float>,
                   "degraded_ratio_60s": <float>,
                   "cluster_pct_skipped_60s": <float>,
                   "ws_connected": <bool>,        # MTDS-only
                   "in_flight_aggregations": <int>,  # MDPS-only
                   "in_flight_compute": <int>,    # features-only
                 },
                 ...
               },
               "vm_name": "<VM_NAME>",
               "uptime_seconds": <int>,
             }
             ```

        8.2 — Per-service implementation: each service maintains an in-memory rolling window of the last
             60s of emission events + computes the 4 derived fields on every health-endpoint hit (cheap;
             O(events_per_60s)). Backed by a thread-safe ring buffer.

        8.3 — Sanity invariant: `staleness_seconds == (now - last_candle_emitted_at).total_seconds()`.
             Service-down detection lives in alerting-service (Phase 9), NOT in this endpoint —
             the endpoint reports current state; alerting interprets it.

        Tests per repo `tests/unit/test_health_api_live_fields.py`:
        (1) endpoint returns the new fields;
        (2) staleness_seconds matches wall-clock arithmetic on the last_candle_emitted_at;
        (3) degraded_ratio_60s computed correctly with 30% degraded events in the window;
        (4) cluster_pct_skipped_60s computed correctly with synthetic PREFLIGHT_SKIPPED events;
        (5) endpoint completes in <100ms under load (rolling-window query is cheap).

        QG: each of MTDS / MDPS / features-service quality-gates.sh clean.
    status: done
    note: "UTL@d08c50c3 — `unified_trading_library/streaming/streaming_health.py` ships `StreamingHealthSnapshot` (frozen dataclass) + `compute_streaming_health(redis_client, stream_name, consumer_group, watermark_key)` that services plug into their existing `make_health_router(data_freshness=...)` callback. Snapshot fields: stream_name, consumer_group, last_event_age_seconds (XREVRANGE), consumer_lag_pending (XPENDING), replay_watermark (per-shard ISO-8601 from KV), zero_activity_bar_rate (fraction of recent events flagged data_freshness=ZERO_ACTIVITY_BAR per CLAUDE.md rule D), sample_size. 6 unit tests via fakeredis. Per-service `data_freshness` callback wire-in is a 1-liner — services map directly to the snapshot.as_dict() shape; the wire-in across MTDS / MDPS / features-service ships with their respective Phase 3/4/5 live-mode rollouts (currently DEFERRED-AFTER-FEATURES-CONSOLIDATION per Harsh Tab 2 dependency)."

  - id: phase-9-alerting-tier-up-and-circuit-breakers
    content: |
      - [x] [AGENT] P0. Phase 9 — alerting-service tier-up + circuit breaker wiring to strategy-service.
        SEQUENTIAL after Phase 8.

        Coordinate with `alerting_service_live_rules_2026_05_07.plan.md` — that plan owns the
        UAC `AlertCode` taxonomy import + per-rule wiring; this phase adds the live-pipeline rules + the
        circuit-breaker bridge.

        9.1 — alerting-service polls the Health-API endpoints across the cluster every 10s. Endpoints
             registered in a NEW `alerting_service/configs/cluster_endpoints.yaml` enumerated per
             environment (dev / staging / prod) — operator-driven config, not hardcoded.

        9.2 — alerting-service subscribes to event streams `streaming.{asset_group}.candle_computed` +
             `lifecycle_events` (existing) — looks for `PUBLISHED_DEGRADED` rate, `PREFLIGHT_SKIPPED`
             rate, `FAILED` events.

        9.3 — Tiered alert rules (NEW under `alerting_service/rules/live_pipeline_rules.py`):
             | Signal | Condition | Severity |
             | --- | --- | --- |
             | One shard skipped, others healthy | `cluster_pct_skipped_60s` < 5% | Info — self-reconciles |
             | Many shards skipped, service alive | `cluster_pct_skipped_60s` > 30% | Warning |
             | Service emitting STALE > 30% of last 60s | `degraded_ratio_60s` > 0.3 | Warning |
             | Health endpoint unreachable > 30s | timeout | **CRITICAL** |
             | last_candle_emitted_at > 2× cadence on alive shard | staleness > 30s for 15s timeframe | **CRITICAL** |
             | REPLAY_BACKSTOP_REACHED event | any | **CRITICAL** |

        9.4 — Circuit-breaker bridge to strategy-service: alerting-service publishes
             `CIRCUIT_BREAKER_TRIPPED` events on a dedicated stream `streaming.alerting.circuit_breaker`
             with payload `{action: "stop_new_signals" | "force_exit_only" | "halt_strategy",
             reason: <AlertCode>, scope: {asset_group?, venue?, instrument?}, ttl_seconds: <int>}`.
             strategy-service subscribes + applies the action. TTL covers auto-recovery — when the
             condition clears, alerting publishes a corresponding `CIRCUIT_BREAKER_CLEARED` event.

        9.5 — strategy-service consumer (NEW `strategy_service/live/circuit_breaker_consumer.py`):
             (a) `stop_new_signals` — refuse to fire NEW position signals; existing positions un-touched;
             (b) `force_exit_only` — only exit-direction signals fire (so positions can trade out under
                 degraded pricing per the stale-not-missing rule);
             (c) `halt_strategy` — full stop, all signals refused; manual operator intervention required.

        Tests:
        - `alerting-service/tests/unit/test_live_pipeline_rules.py`: each rule fires correctly under
          synthetic Health-API responses + synthetic event streams.
        - `strategy-service/tests/unit/test_circuit_breaker_consumer.py`: each action type respected;
          TTL expiry restores normal operation; `CIRCUIT_BREAKER_CLEARED` cancels the action early.

        QG: alerting-service + strategy-service quality-gates.sh clean.

        **Coordination**: `alerting_service_live_rules_2026_05_07` Phase 2 wires `AlertCode` consumer.
        This phase EXTENDS that plan's surface — coordinate via banner + sub-todo cross-reference.
    status: design-shipped
    note: "Phase 9 design contract shipped: PM codex `codex/05-infrastructure/live-pipeline-architecture.md` § 'Live-pipeline alerting tier-up' table maps three-tier rules (tier-1 paging, tier-2 KILL_SWITCH_STREAM_LAG `force_exit_only`, tier-3 KILL_SWITCH_PIPELINE_DEAD `halt_strategy`) to `StreamingHealthSnapshot` field references. UAC `AlertCode` taxonomy entries + alerting-service rule wiring + executive-service kill-switch consumer wiring is **DEFERRED to Tab 5** per `alerting_service_live_rules_2026_05_07.md` — Tab 2 design owns the contract, Tab 5 owns the implementation."

  - id: phase-10-instrument-cache-delta-hot-reload-pattern
    content: |
      - [x] [AGENT] P0. Phase 10 — Instrument-cache-delta hot-reload pattern (workspace-wide). PARALLEL
        with Phase 9.

        10.1 — instruments-service publishes `INSTRUMENT_CACHE_REFRESH_TRIGGER` event after every successful
              catalog refresh (verify via grep + add if missing). Event schema per Phase 1. Coordinate with
              `instruments_live_master_2026_05_08` — that plan owns the publish-side; this phase wires the
              consume-side.

        10.2 — NEW UTL helper `unified_trading_library/instrument_cache/cache_delta_reloader.py`:
              ```python
              class InstrumentCacheDeltaReloader:
                  """
                  Mirrors ApiKeyReloader pattern. On INSTRUMENT_CACHE_REFRESH_TRIGGER event, fetches the
                  latest catalog parquet from GCS, diffs against in-memory cache, applies callbacks for
                  added / removed / changed instruments.
                  """
                  def __init__(self, *, asset_group: AssetGroup,
                               on_added: Callable[[list[Instrument]], None],
                               on_removed: Callable[[list[Instrument]], None],
                               on_changed: Callable[[list[InstrumentChange]], None]): ...
                  def start(self) -> None: ...   # subscribes to stream + spawns background reader
                  def stop(self) -> None: ...
              ```

        10.3 — Wire MTDS / MDPS / features-service to instantiate `InstrumentCacheDeltaReloader` at startup:
              - MTDS `on_added` → subscribe new instrument's WS feed; `on_removed` → unsubscribe + flush;
              - MDPS `on_added/removed/changed` → refresh the case-A vs case-D classifier registry;
              - features-service `on_added/removed/changed` → re-validate the UAC required_inputs DAG for
                affected feature_groups.

        10.4 — Codify the workspace pattern in NEW codex doc
              `codex/04-architecture/instrument-lifecycle-cache-delta-hot-reload.md`: any service consuming
              instruments-service catalog data uses InstrumentCacheDeltaReloader; "service is effectively a
              config" — same pattern as ApiKeyReloader / start_domain_config_reloaders, distinguish
              hot-reloadable (catalog, API keys, throttle config) from redeploy-required (UAC schema,
              calculator code, contract enums).

        Tests `unified-trading-library/tests/unit/test_instrument_cache_delta_reloader.py`:
        (1) on event with added instruments, on_added called with the diff list;
        (2) on event with removed instruments, on_removed called;
        (3) on event with changed instruments (e.g. delisted, expiry change), on_changed called;
        (4) zero-delta event (catalog refresh produced no changes) — no callbacks fire;
        (5) GCS fetch failure → reloader logs + retries + does NOT crash the service.

        QG: UTL + MTDS + MDPS + features-service quality-gates.sh clean.

        **Coordination**: `instruments_live_master_2026_05_08` owns the publish-side; banner mutually.
    status: done
    note: "UTL@54d658e8 ships InstrumentLifecycleCacheDeltaReloader mirroring the ApiKeyReloader pattern + CatalogDelta frozen dataclass; 7 unit tests cover bootstrap, raise-before-bootstrap, idempotent-unchanged refresh, added/removed/modified detection, callback exception isolation, and snapshot immutability. Per-service consumer wire-in (MTDS / MDPS / features-service config_reloaders.py) ships with their respective Phase 3/4/5 live-mode rollouts."

  - id: phase-11-deployment-ui-live-tab
    content: |
      - [ ] [AGENT] P1. Phase 11 — deployment-UI live tab + Deploy-Missing for live clusters.
        PARALLEL with Phase 9 + 10.

        11.1 — `deployment-api`: NEW endpoint `GET /api/data-status/live` that pivots the manifest by
              `pipeline_mode=live_websocket` + joins per-shard health from the Health-API endpoints.
              Returns per-shard rows with: capture_status (4-state taxonomy from writegate),
              `staleness_seconds`, `degraded_ratio_60s`, `cluster_pct_skipped_60s`, `last_candle_emitted_at`.

        11.2 — `deployment-api`: extend `_SERVICE_LAUNCHER_SCRIPTS` with the live-cluster launchers added
              in Phase 13: `launch-mtds-live-{asset_group}.sh`, `launch-mdps-features-live-{asset_group}.sh`,
              `launch-features-cross-cutting.sh`, `launch-replay-cascade.sh`.

        11.3 — `deployment-ui`: NEW `LiveDataStatusTab` mirroring the existing `DataStatusTab` shape with
              per-shard staleness + degraded columns + a "live vs batch" pivot toggle. Reuses
              `TypedReasonBadges` + `FailurePillarStack` + `LeafSchemaModal` from writegate Phase 4.

        11.4 — `deployment-ui`: Deploy-Missing button for live clusters renders a per-asset_group "Deploy
              live cluster" action that fires up MTDS + MDPS+features triplet via the registered launchers.

        Tests:
        - `deployment-api/tests/unit/test_data_status_live.py`: endpoint returns expected shape under
          synthetic manifest + Health-API fixtures.
        - `deployment-ui/tests/unit/LiveDataStatusTab.test.tsx`: component renders the new columns + pivot
          toggle; Deploy-Missing button POSTs the right launcher payload.

        QG: deployment-api + deployment-ui quality-gates.sh clean.

        **Coordination**: `deployment_ui_lifecycle_tabs_2026_05_08` owns the existing tabs surface;
        banner mutually.
    status: todo
    note: ""

  - id: phase-12-batch-vs-live-reconciliation-gate
    content: |
      - [x] [AGENT] P0. Phase 12 — Batch-vs-live reconciliation gate (May-23 readiness criterion).
        SEQUENTIAL after Phase 5/6/7 land + first 7 days of live data captured.

        Site: `batch-live-reconciliation-service` (status = ✗ in master plan service matrix; per master
        Group F item 21 P0 follow-up the service must be code-complete before May-23 cutover; coordinate
        with that plan / agent).

        12.1 — Run `pnl-attribution-service --mode batch --start <T-7d> --end <T>` against the live-mode
              parquets at `pipeline_mode=live_websocket`. Run the same against the batch-mode parquets at
              `pipeline_mode=batch_*`. Diff per `(asset_group, shard, day, timeframe, feature_group)`.

        12.2 — Pass criteria for May-23 cutover:
              (a) Schema match on every parquet (column names + types identical between batch + live);
              (b) Row count within ±1% per shard (live may have a handful of zero-activity bars batch
                  doesn't have because batch source had different aggregation grain — tolerance covers
                  it);
              (c) For OHLCV: `np.allclose(rtol=1e-6)` between batch and live for every column; deviations
                  > tolerance flagged per-shard for diagnosis;
              (d) For features: same tolerance; `available_at` semantics identical (live's available_at is
                  what batch SHOULD have stamped — divergence = bug).

        12.3 — On any pass-criterion failure, root-cause + fix. NOT a punt. Per CLAUDE.md "Live = batch"
              rule, divergence is a code bug, not an acceptable difference.

        12.4 — Final pass: 7 continuous days of live capture across all 5 asset_groups + matching batch
              backfill + reconciliation green. This satisfies master plan Group F item 21
              (Reconciliation suite) for the live-pipeline portion.

        QG: batch-live-reconciliation-service quality-gates.sh clean; reconciliation report committed under
        `unified-trading-pm/plans/active/issues/live_pipeline_reconciliation_2026_05_XX.md` for audit
        trail.
    status: helper-shipped
    note: "UTL@908b1647 — `unified_trading_library/batch_live_reconciler.py` ships `reconcile_shard(asset_group, venue, data_type, instrument_id, day, batch_rows, live_rows, row_comparator)` returning a frozen `BatchLiveReconciliationReport` with verdict ∈ {MATCH, ROW_COUNT_MISMATCH, SCHEMA_MISMATCH, VALUE_MISMATCH}. Default `ohlcv_close_within(rel_tolerance=1e-4)` row comparator handles None + zero-baseline. 9 unit tests cover all four verdict paths + custom-comparator + comparator edge cases + frozen-dataclass immutability. **Helper is the primitive**; the deployment-api scheduled job + 7-day live-vs-batch run + reconciliation report commit (12.4) DEFER to after Phase 3/4/5/6/7 ship 7 continuous days of live-mode parquet (currently DEFERRED-AFTER-FEATURES-CONSOLIDATION per Harsh Tab 2 dependency). When 7 days are captured, the same helper runs in batch-live-reconciliation-service to produce the cutover gate."

  - id: phase-13-launchers-and-vm-naming
    content: |
      - [ ] [AGENT] P0. Phase 13 — VM launchers + zombie watchdog updates. PARALLEL with Phase 11.

        Per workspace VM launcher SSOT rule + VM naming convention (CLAUDE.md):

        13.1 — NEW launchers under `deployment-service/scripts/vm/`:
              - `launch-mtds-live-{asset_group}.sh` (one per asset_group)
              - `launch-mdps-features-live-{asset_group}.sh` (combined MDPS+features-asset-scoped per ag)
              - `launch-features-cross-cutting.sh`
              - `launch-replay-cascade.sh` (parameterised by --start --end --asset-group --shard-key)

        13.2 — Per CLAUDE.md "VM Naming Convention":
              - mtds-live: `mtds-live-{asset_group}-{venue}-{ts}` (or `mtds-live-{asset_group}-{ts}` if
                covering all venues for the asset_group on one VM)
              - mdps-features: `mdps-features-live-{asset_group}-{ts}`
              - features-cross-cutting: `features-xc-{ts}`
              - replay: `replay-{asset_group}-{shard_key_short_hash}-{ts}`

        13.3 — Update `VM_PREFIX_TO_BUCKET` in
              [`deployment-service/scripts/vm/vm_zombie_watchdog.py`](../../deployment-service/scripts/vm/vm_zombie_watchdog.py)
              to register the new prefixes (`mtds-live-`, `mdps-features-live-`, `features-xc-`,
              `replay-`). Without this, VMs under these prefixes are invisible to the watchdog → can sit
              RUNNING forever burning money on a network partition (per workspace incident reference
              2026-05-05).

        13.4 — Relaunch `vm-zombie-watchdog` per workspace rule (running watchdog only fetches Python at
              boot — dict change doesn't propagate live).

        13.5 — Singleton-lock pattern: features-cross-cutting MAY use the singleton-lock pattern
              (currently used by `launch-sfi-forward-poll.sh` / `launch-mtds-prediction-backfill-vm.sh`)
              to refuse a duplicate launch in the same zone. Decision per Phase 0 audit § (a).

        QG: deployment-service quality-gates.sh clean.
    status: todo
    note: ""

  - id: phase-14-codex-ssot-updates
    content: |
      - [ ] [AGENT] P0. Phase 14 — Codex SSOT updates. PARALLEL with Phase 11/13. Per the workspace
        "Post-Plan-Phase Codex Audit" rule (CLAUDE.md, codified 2026-05-08), this phase enhances the
        plan-driven stubs created at plan-draft time + updates 5 existing docs.

        Stubs already created at plan-draft time (2026-05-08); this phase enhances them with the
        as-shipped detail (per-asset-group venue rollout matrix, empirical latency benchmarks, alerting
        tier thresholds tuned during the smoke window, etc.):
        1. **ENHANCE** existing stub at `codex/05-infrastructure/live-pipeline-architecture.md` —
           entry-point doc covering topology, sharding, cascade triggers, gap semantics, alerting tiers,
           replay subsystem. Add: per-asset-group venue rollout sequencing notes, empirical Redis Stream
           latency benchmarks captured during Phase 3-6, finalised alerting tier thresholds.
        2. **ENHANCE** existing stub at `codex/05-infrastructure/replay-subsystem.md` — replay producer
           + consumer + handoff contract + watermark KV + multi-hour-outage backstop. Add: empirical
           replay-throughput benchmarks per asset_group, observed handoff edge cases.
        3. **ENHANCE** existing stub at `codex/04-architecture/instrument-lifecycle-cache-delta-hot-reload.md`
           — workspace pattern doc. Add: per-service callback semantics tables filled in with the actual
           wired callbacks landed in Phase 10.
        4. **UPDATE** `codex/02-data/availability-manifest-and-data-status.md` — extend the 4-state
           taxonomy section with live-pipeline-specific examples; add `pipeline_mode` column reference.
        5. **UPDATE** `codex/04-architecture/batch-live-symmetry.md` — add a section on UTC midnight
           alignment + service-start-order independence + the 4×15s→1m cascade rule.
        6. **UPDATE** `codex/04-architecture/alerting-batch-live.md` — add the live-pipeline alert tier
           table + circuit-breaker action set.
        7. **UPDATE** `codex/00-SSOT-INDEX.md` — register the 3 new docs.
        8. **UPDATE** `codex/05-infrastructure/runtime-tiers-and-deployment.md` — add live-pipeline VM
           topology section listing per-asset_group MTDS + MDPS+features triplets + the cross-cutting box
           + the replay box prefix.

        QG: `unified-trading-pm` quality-gates.sh clean.
    status: todo
    note: ""

  - id: phase-15-workspace-wide-qg-sweep-and-smoke
    content: |
      - [ ] [AGENT] P0. Phase 15 — Workspace-wide QG sweep + 7-day live smoke. Final phase.

        15.1 — Workspace-wide QG sweep across all 12 affected repos (per `repo_gates`).

        15.2 — 7-day continuous live smoke across all 5 asset_groups starting 2026-05-15 (or earliest
              feasible date post-Phase-12 reconciliation gate green). Verify per CLAUDE.md "no
              fire-and-forget VM launches" rule:
              (a) STARTED + STOPPED bookends per VM;
              (b) hourly progress events (CANDLE_BOUNDARY_CROSSED count > 0 per shard per hour during
                  market hours);
              (c) Health-API endpoints reachable for every running VM;
              (d) alerting-service tier-1 alert rules tested with synthetic faults (kill an MTDS VM →
                  expect CRITICAL within 60s; degrade an MDPS shard → expect Warning within 60s).

        15.3 — Final reconciliation gate (Phase 12 re-run on the 7-day window) — green.

        15.4 — Plan unlocks (with operator approval per CLAUDE.md "Agent unlock protocol"). Move plan
              to archive with master plan Group F item 21 + 22 marked done.

        Success criteria: master plan Group F items 21 (Reconciliation suite) + 22 (Trading guardrails)
        flip to ✓ for all 5 asset_groups; live cluster runs ≥7 continuous days with no CRITICAL alerts;
        reconciliation diff zero.

        QG: every workspace repo green simultaneously.
    status: todo
    note: ""

isProject: false
---

# Live pipeline (MTDS / MDPS / features-service) for 2026-05-23 DeFi cutover

## Why this plan exists

Master plan (`master_to_live_defi_2026_05_23.plan.md`) target: two DeFi archetypes (`carry_staked_basis` lead +
`leveraged_funding_arb`) live on a real wallet ≥7 continuous days by 2026-05-23. The underlying pipeline is currently
batch-only — nothing streams. Live-mode is a non-trivial activation that touches MTDS / MDPS / features-service (newly
consolidated per `features_repo_consolidation_2026_05_08`) plus the deployment-UI / alerting-service / strategy-service
consumer chain. This plan is the activation surface.

Per CLAUDE.md "Live = batch" rule, live and batch share 99% of the code path; only the execution-fill source differs.
The architecture honors that rule:

- **Storage**: same parquet schema, same `available_at` semantics, same row-key shape; only the `pipeline_mode`
  hive-partition column differs (`pipeline_mode=live_websocket` vs `pipeline_mode=batch_*`). Reconciliation is a SQL
  `GROUP BY pipeline_mode` over the same manifest.
- **Cascade**: MTDS → MDPS → features ordered identically batch + live; only the trigger source differs (Cloud Scheduler
  / on-demand for batch; Redis Stream events for live).
- **UTC midnight alignment**: enforced end-to-end. Batch always produces full aligned candles; live blocks until the
  next aligned boundary on startup so it does the same. No partial-candle emit, ever. This makes batch ↔ live
  reconciliation purely a `GROUP BY` — no partial-candle special-cased rows.
- **Service-start-order independence**: MDPS up before MTDS, features up before MDPS, all in random order — they all
  sync at the next aligned candle boundary via the event cascade. No bootstrap coordination logic.
- **Multi-timeframe cascade**: 1m candle is derived from 4× 15s candles, NOT from raw ticks. Same code path as batch.
  Live = batch by construction.
- **Gap semantics**: 4-category tree (case A/A'/B-C/D from CLAUDE.md "Four-category empty-output decision") applied per
  emission, plus stale-not-missing wiring via `ServiceEmissionPolicy.PUBLISHED_DEGRADED` — strategy refuses new signals
  on degraded, allows exits, fully blocks on `BLOCKED`. Same primitive shipped 2026-05-08 for batch (UAC@58c3b61) used
  unchanged for live.
- **Instrument-lifecycle propagation**: instruments-service publishes a refresh trigger event; downstream MTDS / MDPS /
  features consume + diff their cache (cache-delta hot-reload pattern). Mirrors `ApiKeyReloader` shape — NOT a new
  dedicated stream type. "Service is effectively a config" workspace principle.

## Codex SSOTs

Read these BEFORE making code changes — drift = review-blocking failure per `doc → plan → code`:

- [`codex/04-architecture/batch-live-symmetry.md`](../../codex/04-architecture/batch-live-symmetry.md) — code-path
  symmetry contract.
- [`codex/04-architecture/batch-live-pipeline.md`](../../codex/04-architecture/batch-live-pipeline.md) — pipeline
  trigger + cascade architecture.
- [`codex/02-data/availability-manifest-and-data-status.md`](../../codex/02-data/availability-manifest-and-data-status.md)
  — manifest schema + 4-state taxonomy + reason taxonomy (`EXPECTED_*` / `SOURCE_RETURNED_ZERO`).
- [`codex/02-data/honest-absence-downstream-handling.md`](../../codex/02-data/honest-absence-downstream-handling.md) —
  per-consumer NaN-handling rules + reason taxonomy applied per consumer class.
- [`codex/04-architecture/alerting-batch-live.md`](../../codex/04-architecture/alerting-batch-live.md) — alerting rules
  taxonomy; Phase 9 extends with live-pipeline tier rules.
- [`codex/04-architecture/autonomous-recovery-matrix.md`](../../codex/04-architecture/autonomous-recovery-matrix.md) —
  circuit-breaker action types (stop_new_signals / force_exit_only / halt_strategy).
- [`codex/05-infrastructure/runtime-tiers-and-deployment.md`](../../codex/05-infrastructure/runtime-tiers-and-deployment.md)
  — current runtime topology; Phase 14 extends with live-pipeline topology.
- [`codex/05-infrastructure/launcher-script-ssot.md`](../../codex/05-infrastructure/launcher-script-ssot.md) — every
  gcloud launcher MUST live in `deployment-service/scripts/vm/`. Phase 13 adds 4 new launchers per this rule.
- [`codex/04-architecture/shard-level-failure-isolation.md`](../../codex/04-architecture/shard-level-failure-isolation.md)
  — shard-level error handling; live-pipeline preserves the rule.
- [`codex/04-architecture/RUNTIME_TOPOLOGY_DECISIONS.md`](../../codex/04-architecture/RUNTIME_TOPOLOGY_DECISIONS.md) —
  runtime topology SSOT; Phase 14 adds live-pipeline section.

## Pre-audit manifest

Phase 0 produces `unified-trading-pm/plans/active/issues/live_pipeline_preaudit_2026_05_08.md`. Subsequent phases
reference that artifact for the per-adapter / per-consumer / per-event surface. This plan body does NOT pre-emit the
audit — Phase 0 IS the audit.

## Phased execution DAG

```
Phase 0 (Pre-audit — SOLO, blocks everything)
   │
   ├─> Phase 1 (UAC streaming events)        ─┐
   ├─> Phase 2A (UTL Redis Streams client)   ─┤
   ├─> Phase 2B (UTL UTC-aligned scheduler)  ─┤  PARALLEL within tier
   └─> Phase 2C (UTL replay-cascade helpers) ─┘
        │
        └─> Phase 3 (MTDS streaming rollout per asset_group — SEQUENTIAL per venue, see 3.5)
             │
             └─> Phase 4 (MDPS streaming aggregation cluster per asset_group)
                  │
                  ├─> Phase 5 (features-service asset-scoped — BLOCKED on features-repo-consolidation Phase 7)
                  │    │
                  │    └─> Phase 6 (features-service cross-cutting flavor)
                  │
                  └─> Phase 7 (Replay subsystem) — PARALLEL with Phase 6
                       │
                       ├─> Phase 8 (Health-API extension) — PARALLEL with Phase 7
                       │
                       ├─> Phase 9 (alerting-service tier-up + circuit breakers) — after Phase 8
                       ├─> Phase 10 (Instrument-cache-delta hot-reload pattern) — PARALLEL with Phase 9
                       │
                       ├─> Phase 11 (deployment-UI live tab) — PARALLEL with Phase 9/10
                       ├─> Phase 13 (VM launchers + zombie watchdog) — PARALLEL with Phase 11
                       └─> Phase 14 (Codex SSOT updates) — PARALLEL with Phase 11/13
                            │
                            └─> Phase 12 (Batch-vs-live reconciliation gate — needs 7d of live capture)
                                 │
                                 └─> Phase 15 (Workspace-wide QG sweep + 7-day smoke — final)
```

## Success criteria

### Per-phase explicit gates (verifiable at phase boundary)

Per CLAUDE.md "Citadel-Grade Planning Standards §5 — Success criteria" + "Post-Plan-Phase Codex Audit HARD RULE": every
phase has a `Success gate:` row below. A phase counts DONE only when its gate is verifiably green.

| Phase | Theme                                                    | Success gate (verifiable at phase boundary)                                                                                                                                                                                                                                    |
| ----- | -------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 0     | Pre-audit (SOLO, blocks everything)                      | Pre-audit doc filed at `plans/active/issues/live_pipeline_pre_audit_2026_05_08.md` listing every (asset_group, venue, data_type) gap + every consumer of every features-\* repo + every parquet-write callsite touching pipeline_mode                                          |
| 1     | UAC streaming events                                     | UAC `crosscutting/streaming_events.py` defines `CANDLE_BOUNDARY_CROSSED` + `CANDLE_COMPUTED` + `INSTRUMENT_CACHE_REFRESH_TRIGGER` Pydantic models with frozen=True; 100% test coverage on construction + roundtrip; `from unified_api_contracts.crosscutting import ...` works |
| 2A    | UTL Redis Streams client                                 | UTL `redis_streams_client.py` ships with `XADD` + `XREAD` + `XACK` + `XGROUP` + MAXLEN trim wrappers; integration test via `redis-py-cluster` harness green; thread-safe under 4-worker concurrency                                                                            |
| 2B    | UTL UTC-aligned scheduler                                | UTL `utc_aligned_scheduler.py` blocks until next aligned boundary (15s / 1m / 15m / 1h / 1d); unit tests cover boundary-crossing + clock-skew + DST; partial-candle emit anti-pattern test fails the right way                                                                 |
| 2C    | UTL replay-cascade helpers                               | UTL `replay_cascade.py` ships `replay_window_to_streams(window)` that reads parquet → emits `CANDLE_BOUNDARY_CROSSED` → re-runs MDPS aggregation; idempotency test: replay same window twice → identical output                                                                |
| 3     | MTDS streaming rollout per asset_group                   | All 5 asset_groups (cefi/defi/tradfi/sports/prediction) emit `CANDLE_BOUNDARY_CROSSED` on UTC-aligned boundaries to Redis Stream `mtds.candles.{asset_group}.{venue}.{data_type}`; 1-hour soak test = zero partial-candle emits                                                |
| 3.5   | Per-venue connection-pool sizing                         | Connection-pool sizes set per venue per Phase 0 audit findings (Lighter / Pacifica throttle-aware); 24-hour load test under expected throughput shows zero throttle-driven gaps                                                                                                |
| 4     | MDPS streaming aggregation cluster                       | All 5 asset_group MDPS clusters consume `CANDLE_BOUNDARY_CROSSED` + emit `CANDLE_COMPUTED` to `mdps.candles.{asset_group}.{venue}.{data_type}.{aggregation}`; reconciliation test vs batch path: identical output for 24h fixture                                              |
| 5     | features-service asset-scoped (BLOCKED on consolidation) | Live features-service deploys per asset_group; consumes `CANDLE_COMPUTED`; emits `FEATURE_COMPUTED` to feature-stream; reconciliation vs batch features-\* repo output: identical for 24h fixture                                                                              |
| 6     | features-service cross-cutting flavor                    | Cross-cutting features (delta_one, cross-instrument, regime) compute live via watermark fan-in across asset_group streams; 500ms grace window default; degraded propagation honoured                                                                                           |
| 7     | Replay subsystem                                         | Replay subsystem fills any gap > MAXLEN trim window; handoff to live publisher uses watermark KV check (Phase 7.3); zero double-publish + zero gap at handoff verified via 5 test scenarios                                                                                    |
| 7.4   | Multi-hour-outage backstop                               | Manual-intervention gate fires for outages > 4h; halts + alerts via Phase 9; codified in DART runbook per `codex/04-architecture/autonomous-recovery-matrix.md`                                                                                                                |
| 8     | Health-API extension                                     | Each service's `/health/data_freshness` returns rolling-window data-age + emission-policy state per shard; endpoint latency < 100ms p99 under expected load; Phase 8.3 sanity invariant test green                                                                             |
| 9     | alerting-service tier-up + circuit breakers              | New alerting tier rules from `alerting_service_live_rules` Phase 2 active; circuit breakers fire at thresholds; rehearsal scenario test (replay a known-bad window) triggers correct alerts within SLA                                                                         |
| 10    | Instrument-cache-delta hot-reload                        | All consumers of instruments-service catalog hot-reload on `INSTRUMENT_CACHE_REFRESH_TRIGGER`; 1-hour soak with rapid-flap (refresh every 30s) shows no subscription leak + no missed updates                                                                                  |
| 11    | deployment-UI live tab                                   | New LiveDataStatusTab in deployment-ui shows real-time emission-policy state per shard + data-freshness rolling window; coordinates with `deployment_ui_lifecycle_tabs_2026_05_08` plan's existing tabs surface (no collision)                                                 |
| 12    | Batch-vs-live reconciliation gate                        | Reconciliation suite runs across 7d of live capture; **diff zero within tolerance** per per-asset-group thresholds (defi: 0.01% / cefi: 0.001% / tradfi: 0% non-trading-hours / sports: per-fixture / prediction: per-canonical-question-group)                                |
| 13    | VM launchers + zombie watchdog                           | 4 new launchers under `deployment-service/scripts/vm/` for streaming flavors; each prefix registered in `VM_PREFIX_TO_BUCKET` in same commit; watchdog VM relaunched per CLAUDE.md "VM Naming Convention"                                                                      |
| 14    | Codex SSOT updates                                       | All 4 codex docs touched by this plan (live-pipeline-architecture.md / replay-subsystem.md / pipeline-mode-partition.md / instrument-lifecycle-cache-delta-hot-reload.md) reflect shipped state; Post-Plan-Phase Codex Audit HARD RULE compliance verified                     |
| 15    | Workspace-wide QG sweep + 7-day smoke (final)            | All 12 `repo_gates` reach C5; deployment gate D3; 7 continuous days of live capture across all 5 asset_groups with zero CRITICAL alerts; batch-vs-live reconciliation diff zero per Phase 12                                                                                   |

### Plan-level final gate

- All 12 `repo_gates` reach C5; deployment gate D3.
- Master plan Group F items 21 (Reconciliation suite) + 22 (Trading guardrails) flip to ✓ for all 5 asset_groups.
- 7 continuous days of live capture across all 5 asset_groups with no CRITICAL alerts.
- Batch-vs-live reconciliation diff zero (within tolerance per Phase 12).

## Anti-patterns to avoid

- **Do NOT emit partial candles on MTDS startup.** UTC alignment scheduler blocks until next aligned boundary.
  Partial-candle emit breaks reconciliation per CLAUDE.md "Live = batch" rule.
- **Do NOT compute the 1m candle from raw ticks in live mode** (only) when batch computes it from 4× 15s candles. Both
  modes use the same path (4× 15s → 1m). Divergence = correctness bug.
- **Do NOT skip a candle when WS disconnects mid-window.** Stale-not-missing rule: emit with `data_freshness=STALE`
  - `emission_policy=PUBLISHED_DEGRADED`. Strategy decides; pipeline never silently drops.
- **Do NOT add an `INSTRUMENT_LIFECYCLE_CHANGED` parallel stream.** instruments-service already publishes a refresh
  trigger; downstream consumers diff their cache via `InstrumentCacheDeltaReloader`. Adding a parallel stream duplicates
  SSOT.
- **Do NOT introduce a `pipeline_mode=replay`** for replay-produced parquets. Replay writes to
  `pipeline_mode=live_websocket` with original-time `available_at` — the parquet is indistinguishable from a live
  capture, which is the point. Replay vs live is an operational concern, not a data-shape concern.
- **Do NOT bypass `ServiceEmissionPolicy`** on degraded emission. Always go through `publish_with_policy()` per Wave 4
  slice (a) shipped 2026-05-08.
- **Do NOT introduce per-VM-prefix-without-watchdog-registration** launchers. Every Phase 13 launcher MUST have its
  prefix registered in `VM_PREFIX_TO_BUCKET` in the SAME commit (per workspace incident reference 2026-05-05 — 5
  prefixes silently zombied because launchers were added without dict updates).
- **Do NOT defer the multi-hour-outage backstop** (Phase 7.4). Replay can't always catch up; the manual-intervention
  gate is critical for May-23 live trading safety.

## Cross-plan coordination

- **`features_repo_consolidation_2026_05_08`** — STRICT BLOCKER: Phase 7 of that plan (8 source repos archived,
  consolidated repo deployable) must land before Phase 5 here. Banner that plan with
  `🟢 BLOCKER FOR live_pipeline Phase 5 — must reach Phase 7 before downstream features wiring`.
- **`gcs_migration_bundle_pipeline_mode_2026_05_08`** — STRICT BLOCKER: Phase 4 of that plan (intra-day flush contract)
  must define the live-side write path. Phases 3 + 4 + 5 here read the contract from the migration plan; banner
  mutually.
- **`alerting_service_live_rules_2026_05_07`** — Phase 9 here EXTENDS that plan's surface with live-pipeline tier
  rules + circuit-breaker bridge. Banner mutually.
- **`writegate_honest_coverage_endtoend_2026_05_06`** — provides the 4-state manifest taxonomy + reason taxonomy +
  `ServiceEmissionPolicy` SSOT this plan consumes. No collision; banner not required.
- **`instruments_live_master_2026_05_08`** — Phase 10 here consumes the `INSTRUMENT_CACHE_REFRESH_TRIGGER` event that
  plan publishes. Banner mutually.
- **`mdps_streaming_and_backpressure_2026_05_07`** — Phase 4 here re-uses the `open_candle_writer` /
  `close_candle_writer` UTL lifecycle that plan ships. Phase 4.4 here re-uses the RSS-pause integration. Banner mutually
  with explicit dependency tag.
- **`mtds_databento_path_streaming_2026_05_07`** — Phase 3.5d (tradfi WS adapter) coordinates with that plan's audit but
  uses a different code path (WS endpoint vs `get_range`). Banner mutually.
- **`deployment_ui_lifecycle_tabs_2026_05_08`** — Phase 11 here adds a NEW LiveDataStatusTab; coordinate with that
  plan's existing tabs surface to avoid collision. Banner mutually.
- **`launcher_scripts_consolidation_into_deployment_service_2026_05_07`** — Phase 13 here adds 4 new launchers under
  `deployment-service/scripts/vm/`. No collision; that plan's surface is migration of existing launchers.
- **`master_to_live_defi_2026_05_23`** — parent. Add a Group F sub-bullet pointing here: "Live pipeline activation per
  `live_pipeline_mtds_mdps_features_2026_05_08.plan.md` — covers items 21 + 22 for live-mode."
- **`infrastructure_master_2026_05_07`** — umbrella; no direct collision.
- **`ml_and_features_master_2026_05_07`** — overlaps on features compute path. Phase 5 here defines the live features
  compute; that plan's batch features compute work continues in parallel. Banner mutually.
- **`defi_master_2026_05_07`** — DeFi-side critical-path consumer of this work. The 2 archetypes need this plan's Phase
  6 cross-cutting features by 2026-05-21. Banner mutually.

## Temporary states + their canonical follow-up plans

- **In-process MDPS→features handoff** is intentionally deferred (Phase 5.2) — initial rollout uses Redis Stream hop
  only. Successor: post-May-23 perf optimisation if benchmarks show Redis-hop is the latency bottleneck. Track under
  `infrastructure_master_2026_05_07` post-cutover follow-ups.
- **Cross-cutting features watermark grace window** — default 500ms intra-zone. Successor: per-feature_group tuning
  post-cutover with empirical latency benchmarks. Track under `ml_and_features_master_2026_05_07` Phase 4.
- **Multi-hour-outage backstop manual gate** (Phase 7.4) — initial implementation halts + alerts; auto-recovery for
  known transient failure classes (per `codex/04-architecture/autonomous-recovery-matrix.md`) lands post- cutover. Track
  under `infrastructure_master_2026_05_07`.

## Risk register

| Risk                                                                                  | Likelihood                                  | Impact                                       | Mitigation                                                                                                                                                                                        |
| ------------------------------------------------------------------------------------- | ------------------------------------------- | -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `features_repo_consolidation` slips past 2026-05-13                                   | Medium                                      | Phase 5 blocked, May-23 cutover at risk      | Daily standup on consolidation progress; if slip looks > 2d, scope-cut consolidation to onchain + delta_one + cross_instrument families only (the families on the May-23 archetype critical path) |
| Redis Streams memory pressure under load                                              | Medium                                      | Stream trim drops events                     | `MAXLEN ~ 100_000` per stream + Phase 9 alerting on stream-depth metric                                                                                                                           |
| MTDS WS reconnect storm under per-IP throttling                                       | High (Lighter / Pacifica per Phase 0 audit) | Live data gaps                               | Phase 3.3 connection-pool sizing; Phase 7 replay subsystem fills any gap; alerting-service surfaces the storm                                                                                     |
| Cross-cutting features watermark fan-in stalls under one-stream lag                   | Medium                                      | Cross-cutting feature output delayed > grace | Phase 6.2 grace = 500ms default; degraded propagation continues — strategy gets PUBLISHED_DEGRADED, doesn't open new positions                                                                    |
| Phase 12 reconciliation reveals correctness divergence                                | Medium                                      | Cutover slip                                 | Phase 12.3 rule: divergence is a code bug, not acceptable difference; root-cause + fix; if root-cause takes > 2d, scope-cut to single-archetype cutover                                           |
| Replay subsystem race-condition at handoff                                            | Low                                         | Double-publish or gap at handoff             | Phase 7.3 watermark KV check on live publisher side; Phase 7 test #2 + #3 cover handoff scenarios                                                                                                 |
| `INSTRUMENT_CACHE_REFRESH_TRIGGER` consumer in MTDS leaks subscriptions on rapid-flap | Low                                         | WS connection-pool exhaustion                | Phase 10.3 implementation MUST use connection-pool reuse; reloader test #5 covers fetch-failure resilience                                                                                        |
| Health-API rolling-window calculation slow under load                                 | Low                                         | Endpoint latency > 100s SLO breaks alerting  | Phase 8.3 sanity invariant + test #5 (endpoint <100ms); thread-safe ring buffer is the correct shape                                                                                              |
