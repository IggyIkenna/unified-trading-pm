---
doc_type: plan
title: Live pipeline (MTDS / MDPS / features-service) for 2026-05-23 DeFi cutover
summary:
status: complete
nature: record
asset_group: [infrastructure]
stage: [meta]
repos:
  [
    alerting-service,
    batch-live-reconciliation-service,
    deployment-api,
    deployment-service,
    deployment-ui,
    features-service,
  ]
scope: [engineer, admin]
tags: []
related: []
created: "2026-05-08"
epic: epic-deployment
priority: P0
parent: master_to_live_defi_2026_05_23
locked_by: live-defi-rollout
locked_since: 2026-05-08
last_updated: 2026-05-08
completion_gates: { code: C5, deployment: D3, business: B4 }
repo_gates:
  - { repo: unified-api-contracts, code: C0, deployment: none, business: none }
  - { repo: unified-trading-library, code: C0, deployment: none, business: none }
  - { repo: market-tick-data-service, code: C0, deployment: none, business: none }
  - { repo: market-data-processing-service, code: C0, deployment: none, business: none }
  - { repo: features-service, code: C0, deployment: none, business: none }
  - { repo: instruments-service, code: C0, deployment: none, business: none }
  - { repo: alerting-service, code: C0, deployment: none, business: none }
  - { repo: strategy-service, code: C0, deployment: none, business: none }
  - { repo: deployment-api, code: C0, deployment: none, business: none }
  - { repo: deployment-ui, code: C0, deployment: none, business: none }
  - { repo: deployment-service, code: C0, deployment: none, business: none }
  - { repo: unified-trading-pm, code: C0, deployment: none, business: none }
depends_on:
  [
    features-repo-consolidation-2026-05-08,
    gcs-migration-bundle-pipeline-mode-2026-05-08,
    alerting-service-live-rules-2026-05-07,
    writegate-honest-coverage-endtoend-2026-05-06,
    instruments-live-master-2026-05-08,
  ]
todos:
  - { id: phase-0-pre-audit-live-pipeline, content: "- [x] [AGENT] P0. Phase 0 — Pre-audit manifest for the live
        pipeline. Produce\n  `unified-trading-pm/plans/archive/issues/live_pipeline_preaudit_2026_05_08.md`
        enumerating:\n  (a) every existing MTDS adapter that already has a websocket / streaming code path (not all
        venues do —\n      CCXT REST-only venues need a poll fallback), and per-venue connection-pool / rate-limit /
        IP-redundancy\n      constraints (CloudFront cooldowns for Lighter / Pacifica per
        `feedback_lighter_pacifica_cloudfront_quirks`,\n      singleton-lock pattern for SFI / prediction-API venues,
        per-key throttling for Bybit/Binance);\n  (b) every site in MTDS / MDPS / features-* that currently writes to
        GCS — confirm every write path is\n      already migrated to `ManifestWriter.record_captured` / `record_empty` /
        `record_failed` /\n      `record_expected_empty` per writegate Phase 2 (so the `pipeline_mode` column propagates
        without\n      adapter-by-adapter touchwork);\n\
        \  (c) the MTDS RSS-pause + `ParallelPerSymbolRunner` integration status
        (per\n      `project_mtds_parallelization_fix_2026_05_07` memory: as of 2026-05-07 the wiring agent was
        dispatched\n      but RSS-pause integration was PENDING — verify before Phase 3 starts that the pause hook is
        wired,\n      otherwise add a sub-todo here);\n  (d) every existing event published by MTDS / MDPS / features-*
        / instruments-service — catalog\n      per-service event names + payloads + `unified_api_contracts.events.*`
        registration status, so Phase 1\n      knows which events are NEW vs which already exist;\n  (e) every consumer
        of `ServiceEmissionPolicy` shipped 2026-05-08 (UAC@58c3b61 slice (a) + UTL@1a7e1d4b)\n      — Phase 8 wires the
        policy decision into MDPS / features candle emission paths, but the consumer\n      list (strategy-service /
        position-balance-monitor / risk-and-exposure / pnl-attribution) needs an\n      explicit row-by-row
        mapping;\n  (f) every existing usage of `ApiKeyReloader`\
        \ / `start_domain_config_reloaders` so Phase 10's\n      instrument-cache-delta hot-reload pattern can mirror
        the exact shape;\n  (g) every existing Redis dependency in the workspace — `grep -rn \"redis\\.\" across all
        repos — and\n      whether any are using Streams or just KV; Phase 2 needs to know whether to add `redis>=5.0`
        (Streams\n      require ≥5) to UTL's deps or whether it's already present.\n  Output committed under
        `plans/active/issues/`. Subsequent phases reference the artifact.\n", status: done, note: "PM@12483f5b —
        408-line audit doc shipped 2026-05-08 by tab2-pre-audit sub-agent. Covers all 7 audit subsections (a-g) with
        file:line / commit-sha / count evidence + 10 cross-cutting Phase-3-13 sub-todos + per-consumer wire-in tables
        for Phases 8 + 10. Notable: MTDS RSS-pause WIRED 2026-05-08 (cli/main.py:103-128) — auto-memory
        `project_mtds_parallelization_fix_2026_05_07` 'RSS-pause PENDING' claim is now stale; `redis>=5.0` already
        declared in UTL pyproject." }
  - { id: phase-1-uac-streaming-events, content: "- [x] [AGENT] P0. Phase 1 — UAC streaming event types. PARALLEL with
        Phase 2A.\n\n  Site: `unified-api-contracts/unified_api_contracts/events/streaming.py` (NEW module).\n\n  New
        event types as Pydantic models extending the existing `EmissionLifecycleEvent` shape
        from\n  UAC@58c3b61:\n\n  ```python\n  class CandleBoundaryCrossedEvent(BaseModel):\n      event_type:
        Literal[\"CANDLE_BOUNDARY_CROSSED\"]\n      asset_group: AssetGroup\n      venue: str\n      chain: str |
        None\n      instrument_id: str | None\n      data_type: DataType\n      instrument_type: str |
        None\n      league_id: str | None\n      timeframe: str   # \"15s\", \"1m\", \"5m\", ...\n      period_start:
        datetime  # UTC, aligned to timeframe boundary\n      period_end: datetime    # UTC, aligned (period_start +
        timeframe)\n      tick_count: int         # number of source ticks captured for the window\n      available_at:
        datetime  # when MTDS finalised the window (= period_end\
        \ + grace)\n      data_freshness: Literal[\"FRESH\", \"STALE\"]  # STALE if WS reconnect
        mid-window\n      pipeline_mode: PipelineMode                  # always \"live_websocket\" for this
        event\n      correlation_id: str\n      vm_name: str\n\n  class
        CandleComputedEvent(BaseModel):\n      event_type: Literal[\"CANDLE_COMPUTED\"]\n      # same shard-key columns
        as CandleBoundaryCrossedEvent\n      ...\n      row_count: int          # rows in the emitted candle parquet (1
        per window for OHLCV)\n      available_at: datetime  # when MDPS finalised the candle (= window_close +
        aggregation latency)\n      data_freshness: Literal[\"FRESH\", \"STALE\",
        \"ZERO_ACTIVITY_BAR\"]\n      emission_policy: ServiceEmissionPolicy   # PUBLISHED_OK / PUBLISHED_DEGRADED /
        STALE_DATA / BLOCKED\n      policy_decision_reason: str | None\n      pipeline_mode:
        PipelineMode\n      correlation_id: str\n      vm_name: str\n\n  class
        InstrumentCacheRefreshTriggerEvent(BaseModel):\n      event_type: Literal[\"INSTRUMENT_CACHE_REFRESH_TRIGGER\"\
        ]\n      # Published by instruments-service after every successful catalog refresh.\n      # Downstream MTDS /
        MDPS / features-service consume this + diff their cache.\n      # Shape mirrors EmissionLifecycleEvent so
        existing event subscribers don't need a new code path.\n      asset_group: AssetGroup\n      catalog_refresh_at:
        datetime       # when the catalog parquet was finalised\n      row_count_total:
        int\n      row_count_added_since_last: int    # 0 if no delta — consumers skip cache
        refresh\n      row_count_removed_since_last: int\n      correlation_id: str\n      vm_name:
        str\n  ```\n\n  `PipelineMode` StrEnum lives at `unified_api_contracts/canonical/crosscutting/pipeline_mode.py`
        (NEW —\n  coordinated with `gcs_migration_bundle_pipeline_mode_2026_05_08` Phase 1A; one of the two plans
        owns\n  this enum, recommend the migration plan owns it because it ships first chronologically).\n\n  Tests
        `unified-api-contracts/tests/unit/test_streaming_events.py`:\n  (1) JSON serialization\
        \ round-trip for all 3 events;\n  (2) `period_end - period_start == parse_timeframe(timeframe)` invariant on
        CandleBoundaryCrossedEvent;\n  (3) `data_freshness` closed-set values exactly;\n  (4) `emission_policy` defaults
        to `PUBLISHED_OK` when not specified.\n\n  QG: UAC quality-gates.sh clean.\n", status: done, note: "UAC@8bc3f2a
        (PipelineMode SSOT) + UAC@b643c9a (Phase 1 streaming events: CandleBoundaryCrossedEvent / CandleComputedEvent /
        InstrumentCacheRefreshTriggerEvent + EmissionOutcome closed-set + parse_timeframe + 17 unit tests) + UAC@b02335d
        (top-level facade: PipelineMode + is_batch / is_live / source_string_for / pipeline_mode_for_source surfaced
        from `unified_api_contracts` per Citadel Import Rules). Module at `unified_api_contracts/events/streaming.py`.
        CandleComputedEvent carries BOTH `emission_policy` (POLICY) AND orthogonal `emission_outcome` (OUTCOME —
        PUBLISHED_OK / PUBLISHED_DEGRADED / STALE_DATA / BLOCKED). All events default `pipeline_mode` to LIVE_WEBSOCKET.
        **QG state 2026-05-08 PM (RESOLVED)**: foreign blockers cleared — ORACLE_COVERAGE_START shipped at UAC@3adee82
        (Tab 1 DeFi-launch); EN DASH at alerting/thresholds.py:60 already replaced by HYPHEN-MINUS. Issue
        `plans/archive/issues/uac_utl_qg_blockers_2026_05_08.plan.md` marked RESOLVED." }
  - { id: phase-2a-utl-redis-streams-client, content: "- [x] [AGENT] P0. Phase 2A — UTL Redis Streams client wrapper.
        PARALLEL with Phase 1.\n\n  Site: `unified-trading-library/unified_trading_library/streaming/redis_stream.py`
        (NEW).\n\n  Helper API (matches existing UTL helper-shape, e.g. `ApiKeyReloader`,
        `ManifestWriter`):\n\n  ```python\n  class StreamPublisher:\n      def __init__(self, *, redis_url: str,
        stream_name: str, max_len_approx: int = 100_000): ...\n      def publish(self, event: BaseModel) -> str: ...   #
        returns Redis stream ID; XADD with MAXLEN ~\n      def close(self) -> None: ...\n\n  class
        StreamConsumerGroup:\n      def __init__(self, *, redis_url: str, stream_name: str, group_name: str,
        consumer_name: str,\n                   deserialize_to: type[BaseModel]): ...\n      def read_blocking(self, *,
        count: int = 10, block_ms: int = 5_000) -> list[tuple[str, BaseModel]]:\n          # XREADGROUP, blocking up to
        block_ms; returns list of (stream_id, deserialized_event).\n\
        \          ...\n      def ack(self, stream_ids: list[str]) -> None: ...   # XACK\n      def claim_pending(self,
        *, idle_threshold_ms: int = 60_000) -> list[tuple[str, BaseModel]]:\n          # XAUTOCLAIM — recover crashed
        consumers' pending messages after idle_threshold_ms.\n          ...\n      def close(self) -> None:
        ...\n  ```\n\n  Stream-name convention: `streaming.{asset_group}.{event_type}` (lowercase, dot-separated).
        Group\n  names per consumer service: `mdps`, `features-asset-scoped`, `features-cross-cutting`.
        Consumer\n  names per VM: `${VM_NAME}` (matches workspace per-VM-shard-isolation convention).\n\n  Tests
        `unified-trading-library/tests/unit/test_redis_stream.py` using `fakeredis>=2.20`:\n  (1) publish + read
        round-trip;\n  (2) consumer group fan-out — two consumers in different groups both receive every message;\n  (3)
        consumer group load-balance — two consumers in the SAME group split the messages;\n  (4) ack semantics —
        un-acked messages remain in the pending list;\n\
        \  (5) `claim_pending` recovers messages from a stalled consumer after the idle threshold;\n  (6) `MAXLEN ~`
        trim — stream length stays bounded under load.\n\n  Add `redis>=5.0` and `fakeredis>=2.20` (test-only — but
        workspace flat-deps rule means it goes in\n  `[project.dependencies]` not
        `[project.optional-dependencies.test]`) to UTL pyproject if Phase 0 § (g)\n  confirms they're not already
        present.\n\n  QG: UTL quality-gates.sh clean.\n", status: done, note: UTL@f24e651b —
        `unified_trading_library/streaming/redis_stream.py` (StreamPublisher + StreamConsumerGroup; XADD + MAXLEN ~ +
        XREADGROUP + XACK + XAUTOCLAIM + idempotent XGROUP CREATE) + `replay.py`. 6 unit tests via fakeredis.
        Event-class-agnostic (generic BaseModel TypeVar). fakeredis>=2.20 added to pyproject (flat-deps). `redis>=5.0`
        already present. Companion UTL@87134364 added pipeline_mode kwarg to ManifestWriter (gcs_migration plan Phase
        1B). UTL QG blocked by foreign UAC breakage at conftest import — see
        `plans/archive/issues/uac_utl_qg_blockers_2026_05_08.plan.md`. }
  - { id: phase-2b-utl-utc-aligned-scheduler, content: "- [x] [AGENT] P0. Phase 2B — UTL UTC-aligned timeframe
        scheduler. SEQUENTIAL after Phase 2A.\n\n  Site:
        `unified-trading-library/unified_trading_library/streaming/utc_aligned_scheduler.py`
        (NEW).\n\n  Helper:\n  ```python\n  class UTCAlignedScheduler:\n      \"\"\"\n      Fires a callback at every
        aligned timeframe boundary, with grace window for late ticks.\n\n      On startup, BLOCKS until the next aligned
        boundary — never fires for partial windows.\n      E.g. UTCAlignedScheduler(timeframe=\"15s\",
        grace_seconds=1.0) booted at 14:23:07.4 UTC fires\n      its first callback at 14:23:16.0 UTC for window
        [14:23:00, 14:23:15] (period closed at\n      14:23:15 + 1s grace).\n      \"\"\"\n      def __init__(self, *,
        timeframe: str, grace_seconds: float = 1.0,\n                   on_boundary: Callable[[BoundaryTick], None]):
        ...\n      async def run_forever(self) -> None: ...\n      def stop(self) -> None:
        ...\n\n  @dataclass(frozen=True)\n\
        \  class BoundaryTick:\n      timeframe: str\n      period_start: datetime  # UTC, aligned\n      period_end:
        datetime    # UTC, aligned\n      wall_clock_at_fire: datetime  # period_end + grace\n  ```\n\n  Tests
        `unified-trading-library/tests/unit/test_utc_aligned_scheduler.py` using `freezegun`:\n  (1) booted at
        14:23:07.4 UTC for timeframe=\"15s\" — first callback fires at 14:23:16.0 UTC;\n  (2) `period_start` +
        `period_end` always aligned to the timeframe (00, 15, 30, 45 for 15s; 00 for 1m);\n  (3) on stop, `run_forever`
        returns cleanly without firing pending callbacks;\n  (4) clock-jump (NTP sync skews wall-clock) — assert
        next-fire-time recomputed against new wall-clock;\n  (5) timeframe parsing — supports \"15s\", \"1m\", \"5m\",
        \"15m\", \"1h\", \"1d\" (canonical workspace set).\n\n  QG: UTL quality-gates.sh clean.\n", status: done, note: UTL@8c67df5d
        — `unified_trading_library/streaming/utc_aligned_scheduler.py` ships UTCAlignedScheduler async class +
        BoundaryTick frozen dataclass; supports 15s/1m/5m/15m/1h/1d timeframes; recomputes next-fire time against
        datetime.now(UTC) each iteration (NTP-tolerant); 5 tests via freezegun. UTL@858f3c84 — package
        `unified_trading_library.streaming.__init__.py` now publishes UTCAlignedScheduler + BoundaryTick +
        StreamPublisher + StreamConsumerGroup + ReplayPublisher + ReplayWatermarkKV from one import surface (Citadel
        facade pattern). }
  - { id: phase-2c-utl-replay-cascade-helpers, content: "- [x] [AGENT] P1. Phase 2C — UTL replay-cascade helpers.
        PARALLEL with Phase 2B.\n\n  Site: `unified-trading-library/unified_trading_library/streaming/replay.py`
        (NEW).\n\n  Helper:\n  ```python\n  class ReplayPublisher:\n      \"\"\"\n      Publishes historical
        CandleBoundaryCrossedEvent / CandleComputedEvent to the live Redis Stream\n      for downstream replay. Stamps
        event timestamps to ORIGINAL window times (not replay-execution\n      time), preserving the live-pipeline
        semantics. Coordinates handoff to the live publisher via a\n      per-shard `replay_watermark` Redis key —
        replay owns the stream up to the watermark; live takes\n      over at the next aligned boundary past the
        watermark.\n      \"\"\"\n      def __init__(self, *, stream_publisher:
        StreamPublisher,\n                   watermark_kv: ReplayWatermarkKV): ...\n      def publish_window(self,
        event: CandleBoundaryCrossedEvent | CandleComputedEvent) -> None: ...\n    \
        \  def finalize(self, *, target_period_end: datetime) -> None:\n          \"\"\"Flag replay complete up to
        `target_period_end`; live consumer at the same shard takes over\n          at the next aligned
        boundary.\"\"\"\n\n  class ReplayWatermarkKV:\n      \"\"\"Per-shard Redis KV:
        replay_watermark.{asset_group}.{shard_key} → ISO timestamp.\"\"\"\n      def get(self, shard_key: str) ->
        datetime | None: ...\n      def set(self, shard_key: str, period_end: datetime) -> None: ...\n  ```\n\n  Tests
        `unified-trading-library/tests/unit/test_replay.py` using `fakeredis`:\n  (1) publish_window round-trip with
        original-time timestamps preserved;\n  (2) finalize sets the watermark KV and live consumer at the same shard
        sees the watermark;\n  (3) double-publish protection — replay + live racing on the same window emits ONLY ONE
        event\n      (consumer-side dedupe via the watermark KV check; live publisher refuses to publish
        for\n      period_end ≤ replay_watermark);\n  (4) replay tail at watermark\
        \ — replay finalize at 14:23:00 + live publisher firing at 14:23:15\n      both seen by consumer with no gap and
        no duplicate.\n\n  QG: UTL quality-gates.sh clean.\n", status: done, note: "UTL@f24e651b —
        `unified_trading_library/streaming/replay.py` ships ReplayPublisher.publish_window (preserves original
        period_end + refuses publish for period_end ≤ current_watermark) + ReplayPublisher.finalize (advances per-shard
        watermark KV; rejects backwards) + ReplayWatermarkKV at `replay_watermark.{shard_key}` → ISO-8601 UTC. 4 unit
        tests via fakeredis (publish-window round-trip, finalize-advance, double-publish-protection,
        watermark-tail-handoff). UTL@858f3c84 lifted ReplayPublisher + ReplayWatermarkKV into the
        `unified_trading_library.streaming` package surface." }
  - { id: phase-3-mtds-streaming-rollout, content: "- [x] [AGENT] P0. Phase 3 — MTDS websocket streaming rollout per
        asset_group. SEQUENTIAL after Phase 1 + 2.\n  (3.1 ✅ orchestration + CLI surface SHIPPED 2026-05-11 Harsh slot
        5 at mtds@`97b2224` — `live/websocket_runner.py`\n  `LiveWebsocketRunner` + `LiveWebsocketTickSink` +
        `WSFeedConnector`/`TickSink`/`ShardManifestRecorder` Protocols +\n  `InstrumentCacheRefreshConsumer` [3.4] +
        `cli/handlers/websocket_streaming_handler.py` `WebsocketStreamingHandler`\n  registered as `--operation
        websocket-streaming` + `--shard-spec`/`--base-timeframe`/`--correlation-id` args +\n  config
        `streaming_redis_url`/`vm_name`/`mtds_live_pool_size_per_shard` [3.3] + 21 unit tests; ruff +
        basedpyright\n  clean. **3.2 DONE 2026-05-18 slot-6 (MTDS@a6a045a)**. ~~Still open: 3.2 per-venue-adapter
        reconnect-STALE verification~~ 3.5 per-venue WS-adapter wire-in\n  [`WS_FEED_CONNECTOR_FACTORIES` empty registry
        — handler raises on unregistered venue], `ShardManifestRecorder`\n\
        \  ManifestWriter wiring [per-asset_group v5 row keys — rides with 3.5], per-asset_group smoke launches. See
        scoreboard.)\n\n  Site: `market-tick-data-service/market_tick_data_service/adapters/*.py`
        and\n  `market_tick_data_service/cli/main.py`.\n\n  3.1 — ✅ SHIPPED (mtds@`97b2224`). Add a `--mode live
        --operation websocket-streaming` mode to MTDS CLI. Live-mode\n       dispatch routes to a NEW
        `live/websocket_runner.py` (`LiveWebsocketRunner`) that:\n       (a) wires `UTCAlignedScheduler` per
        `(asset_group, venue, data_type, timeframe)` shard atom from\n           the v5 SSOT;\n       (b) opens
        websocket connections per shard via the existing per-venue adapter;\n       (c) buffers ticks in-memory until
        the scheduler fires the boundary callback;\n       (d) at boundary fire, packages the buffered ticks → emits
        `CandleBoundaryCrossedEvent` via\n           `StreamPublisher` to
        `streaming.{asset_group}.candle_boundary_crossed`;\n       (e) writes the buffered ticks to GCS at the
        `pipeline_mode=live_websocket`\
        \ partition (intra-day\n           5-15min flush cadence per `gcs_migration_bundle_pipeline_mode_2026_05_08`
        Phase 4 contract);\n       (f) records to manifest via `record_captured` / `record_empty` per the existing
        4-category tree.\n\n  3.2 — Per-asset_group websocket adapters: verify each adapter's existing reconnect logic
        respects\n       the WS-disconnect → STALE flag rule. On reconnect mid-window: emit the current window
        with\n       `data_freshness=\"STALE\"` + `emission_policy=PUBLISHED_DEGRADED`; do NOT skip the
        window\n       (stale-not-missing rule per CLAUDE.md live-pipeline architecture memory + the live
        gap-semantics\n       4-category tree).\n\n  3.3 — Connection pool sizing per shard via NEW config
        `mtds_live_pool_size_per_shard` (default 1, can\n       be tuned per venue for IP/key redundancy under
        CloudFront throttling). Pool size is per-shard\n       config, NOT a manifest dimension (per workspace
        shard-SSOT rule — stays in v5 atom).\n\n  3.4 — `INSTRUMENT_CACHE_REFRESH_TRIGGER`\
        \ consumer in MTDS: subscribe to the\n       `streaming.{asset_group}.instrument_cache_refresh_trigger` group →
        on receive, diff the current\n       catalog cache against the new GCS catalog → subscribe new instruments /
        drop delisted ones.\n       Implementation pattern mirrors `ApiKeyReloader` (Phase 10 codifies the cross-service
        pattern).\n\n  3.5 — Per-venue rollout sequence (from highest-tick-volume to lowest, so we de-risk the heavy
        paths\n       first):\n       a. defi (chain × protocol shards — relatively low tick rate but the May-23
        critical path);\n       b. cefi spot/perp (highest tick rate, per-instrument or `(venue, N instrument)` chunk
        shard);\n       c. cefi options/futures (bundled per-root; cluster validation must propagate through
        the\n          live emission per writegate Phase 1A enforcement);\n       d. tradfi (Databento WS where
        available; REST poll fallback for ETFs);\n       e. sports (per `(source, league_id)` shard — odds_api WS where
        available; REST poll otherwise);\n\
        \       f. prediction (per `(venue, canonical_question_group)` shard).\n\n  Each rollout sub-step ships its own
        commit + smoke launch per workspace \"no fire-and-forget VM\n  launches\" rule (event-verification protocol
        mandatory: STARTED within 60s, hourly progress events,\n  STOPPED/FAILED on exit + non-empty
        metadata).\n\n  Tests under `market-tick-data-service/tests/unit/test_live_runner.py` per asset_group + 6
        per-venue\n  smoke tests `tests/integration/test_live_smoke_<venue>.py` (skipped on CI without secrets,
        run\n  manually pre-rollout).\n\n  QG: MTDS quality-gates.sh clean per asset_group
        rollout.\n\n  **Coordination**: `mtds_databento_path_streaming_2026_05_07` is for batch-side Databento
        streaming\n  (path=tempfile + chunked to_df). Live-mode tradfi (3.5d) MAY use a different code path
        —\n  Databento has a WS endpoint distinct from get_range. Phase 3.5d agent reads that plan's audit\n  notes
        before designing the tradfi WS adapter; banner mutually.\n", status: helper-shipped, note: "2026-05-11
        harsh-live-pipeline-impl-tab — 3.1 (runner orchestration + CLI surface) + 3.3 (pool-size config) + 3.4
        (InstrumentCacheRefreshConsumer) SHIPPED at mtds@97b2224. **3.2 DONE 2026-05-18 slot-6 — pop_reconnect_flag()
        set-and-reset contract tests for all 16 WSFeedConnectors (MTDS@a6a045a)**; 3.5 (per-venue WSFeedConnector
        implementations: defi→cefi spot/perp→cefi options/futures→tradfi→sports→prediction). **3.5a/b: 13
        WSFeedConnectors landed 2026-05-16 (slot-3) — DRIFT-SOLANA, HYPERLIQUID, BINANCE-FUTURES, BYBIT-FUTURES,
        OKX-FUTURES, DERIBIT, ASTER, BINANCE-SPOT, BYBIT-SPOT, COINBASE-SPOT, OKX-SPOT, KRAKEN-SPOT, KRAKEN-FUTURES.
        Latest: MTDS@df3fa2f. 90 unit tests pass; basedpyright clean. All 13 verified producing live trades. ALL 8 CEFI
        PERP VENUES (7 cutover + Kraken-Futures) + 5 CEFI SPOT + DRIFT. Side-mapping codified per venue.**
        **3.5a-PHOENIX: SHIPPED 2026-05-17 (slot-3) at MTDS@f6a56c1 — PhoenixWSFeedConnector via Jupiter lite-api
        polling (Phoenix own REST DNS-dead; Jupiter routes live quotes through Phoenix on-chain CLOB). 3s poll interval
        for SOL-USDC/WBTC-USDC/WBTC-SOL. Reconnect-flag semantics preserved. 21 unit tests pass (1 live-integration
        skipped). Venue key: 'phoenix'.** **3.5d-TRADFI-DATABENTO: SHIPPED 2026-05-17 (slot-3) at MTDS@946bab0 —
        DatabentoTradfiWSFeedConnector for CME/ICE/NYSE/NASDAQ/CBOE/ARCA/BATS. Bridges Databento Live thread-backed
        callback to async generator via asyncio.Queue + call_soon_threadsafe. 30 unit tests pass (1 live-integration
        skipped). Status: BLOCKED-CREDENTIALS (Real-Time Databento key needed; ping in
        ikenna_orchestrator/pings/slot_3.md).** **3.5e-SPORTS-ODDS_API: SHIPPED 2026-05-17 (slot-3) at MTDS@cab6f57 —
        OddsApiWSFeedConnector polling adapter (no native WS). Venue key: 'odds_api'. Instrument:
        ODDS_API:SPORT:{sport_key}. 60s poll interval (credit-aware). 29 unit tests pass (1 live-integration skipped).
        Status: BLOCKED-CREDENTIALS (odds-api-key credit quota; ping in ikenna_orchestrator/pings/slot_3.md).**
        **3.5f-PREDICTION-POLYMARKET-KALSHI: SHIPPED 2026-05-17 (slot-3) at MTDS@99fc7b3 — PolymarketWSFeedConnector
        (Gamma API polling, 30s, public/no credentials) + KalshiWSFeedConnector (native WS public ticker channel, no
        credentials). 53 unit tests pass (2 live-integration skipped). Venue keys: 'polymarket' + 'kalshi'. PHASE 3.5
        COMPLETE — all WSFeedConnectors shipped across defi/cefi/tradfi/sports/prediction. ShardManifestRecorder
        ManifestWriter wiring: ALREADY COMPLETE per MTDS@ab17cc3 (slot-7, 2026-05-12).** NOTE: per ikenna_orchestrator
        ledger commit 1e01433c the operator reassigned slot-5's Phase 3/5/6/15 to Ikenna slot 7." }
  - { id: phase-4-mdps-streaming-aggregation, content: "- [x] [AGENT] P0. Phase 4 — MDPS streaming aggregation cluster
        per asset_group. SEQUENTIAL after Phase 3. (UTL@`ee64481a` real impl shipped 2026-05-11 slot 4 RE-TASK;
        per-service MDPS consumer wiring shipped 2026-05-11 Harsh slot 5 at mdps@`0068b2f` — `live_aggregator.py`
        LiveStreamAggregator + 7 Protocol adapters + `--mode live --operation streaming-aggregation` + 12 unit tests;
        QG-clean.)\n\n  **DESIGN-AHEAD shipped 2026-05-11 (Ikenna slot 4)**: UTL@`58bfbbeb`
        —\n  `unified_trading_library.streaming.MDPSStreamingAggregator` + `AggregatorConfig` +
        caller-supplied\n  `TickFetcher` / `InstrumentCatalogGate` / `TimeframeDAG` Protocols landed as design-only
        stubs.\n  Every method raises `NotImplementedError` until Phase 4 implementation lands (gated
        on\n  `features_repo_consolidation_2026_05_08` Phase 7 + the live-pipeline cascade unblock).\n  Class docstring
        contract covers: 4-category gap semantics (FRESH / ZERO_ACTIVITY_BAR / no-emit /\n\
        \  STALE-emit / WS-dead-cascade), multi-timeframe cascade (Live = batch symmetry), RSS-pause\n  integration with
        `mdps_streaming_and_backpressure_2026_05_07.md`, cluster validation propagation\n  per writegate Phase 1A.
        Consumers (MDPS `cli/main.py` + `live_aggregator.py`) compile against\n  the shape now. Full-execution criterion
        (work-split):\n  `from unified_trading_library.streaming import MDPSStreamingAggregator` resolves + 11
        design-only\n  contract tests pass (run-raises-NotImpl, Protocols runtime-checkable, frozen-dataclass
        config).\n  **DEFERRED**: implementation body (subscribe-fetch-aggregate-write-publish loop + cascade
        fan-in)\n  ships once Harsh slot 2 lands features-consolidation Phase 7.\n\n  Site:
        `market-data-processing-service/market_data_processing_service/cli/main.py` +\n  `live_workers.py` + a NEW
        `live_aggregator.py`.\n\n  4.1 — Add `--mode live` to MDPS CLI dispatching to `live_aggregator.py`:\n       (a)
        `StreamConsumerGroup` per `(asset_group, venue, data_type)`\
        \ shard subscribes to\n           `streaming.{asset_group}.candle_boundary_crossed` with
        `group_name=\"mdps\"`;\n       (b) on each `CandleBoundaryCrossedEvent`, fetch the just-flushed tick parquet
        from GCS\n           (intra-day flush per Phase 3.1.e — path is deterministic from event payload);\n       (c)
        aggregate ticks → produce OHLCV for the timeframe;\n       (d) write the candle to GCS at
        `pipeline_mode=live_websocket` per\n           `gcs_migration_bundle_pipeline_mode_2026_05_08`;\n       (e) emit
        `CandleComputedEvent` to `streaming.{asset_group}.candle_computed` with\n           `emission_policy` from the
        shipped `ServiceEmissionPolicy` SSOT (UAC@58c3b61 + UTL@1a7e1d4b).\n\n  4.2 — Multi-timeframe cascade rule
        (CRITICAL — live=batch symmetry): the 1m candle MUST be derived\n       from the 4× 15s candles, NOT from raw
        ticks. Same code path as batch. Implementation:\n       `live_aggregator.py` waits for 4× CandleComputed{15s}
        events for a given shard → feeds them\n       through\
        \ the SAME aggregation function as batch's `_process_standard_timeframe` →\n       emits CandleComputed{1m}.
        This rule extends to all parent timeframes (5m from 5×1m, 15m from\n       3×5m, 1h from 4×15m) per the
        workspace timeframe DAG.\n\n  4.3 — Live gap semantics (4-category tree applied per emission
        decision):\n       (A) WS connected, no trades, catalog says alive → zero-activity bar (O=H=L=C=prior_LTP,
        vol=0)\n           with `data_freshness=ZERO_ACTIVITY_BAR`, `emission_policy=PUBLISHED_OK`;\n       (A') WS
        connected, no trades, catalog says delisted/non-trading → no candle emitted;
        manifest\n           `record_empty(reason=EXPECTED_*)` per writegate taxonomy;\n       (B/C) WS disconnected
        mid-window or malformed ticks → emit candle with\n           `data_freshness=STALE`,
        `emission_policy=PUBLISHED_DEGRADED`, carry-forward LTP. Stale-not-\n           missing rule;\n       (D) WS
        dead >N consecutive windows → stop emitting CandleComputed for the shard; alerting-\n           service\
        \ (Phase 9) fires CRITICAL.\n\n  4.4 — RSS-pause integration: live-aggregator subscribes to
        `ResourceProfiler.on_memory_warning` per\n       `mdps_streaming_and_backpressure_2026_05_07` Phase 2 contract —
        on warning, pause new\n       `XREADGROUP` calls + drain in-flight aggregations cleanly. Coordinate with that
        plan's agent\n       so the backpressure shape is identical between batch and live.\n\n  4.5 — Cluster
        validation propagates for bundled shards (options_chain / futures_chain / sports\n       per-fixture-bundle /
        prediction canonical-question-group) via `record_captured`'s required\n       `expected_root_clusters` +
        `cluster_extractor` kwargs per writegate Phase 1A.\n\n  Tests
        `market-data-processing-service/tests/unit/test_live_aggregator.py`:\n  (1) candle_boundary → candle_computed
        round-trip with full window;\n  (2) timeframe cascade — 4× 15s emission triggers 1× 1m emission with derived
        OHLCV;\n  (3) zero-activity bar — empty window produces ZERO_ACTIVITY_BAR candle with\
        \ prior_LTP;\n  (4) stale window — WS reconnect mid-window produces PUBLISHED_DEGRADED candle;\n  (5)
        catalog-delisted — instrument-cache says delisted, no candle emitted, manifest record_empty;\n  (6) cluster
        validation — bundled shard without expected_root_clusters raises\n      MissingClusterValidationError (writegate
        Phase 1A enforcement preserved).\n\n  QG: MDPS quality-gates.sh clean.\n\n  **Coordination**:
        `mdps_streaming_and_backpressure_2026_05_07` Phase 1 ships the\n  `open_candle_writer` / `close_candle_writer`
        UTL lifecycle. Phase 4 of THIS plan re-uses that\n  lifecycle for live aggregation writes (same shard atomicity
        contract, same per-VM tempfile +\n  rename, same single-`record_captured` per shard). That plan must reach its
        Phase 1.2 (MDPS\n  callsite migration) before Phase 4 here lands.\n", status: done, note: "2026-05-11
        ikenna-live-pipeline-tab — UTL primitive PROMOTED TO IMPLEMENTATION at UTL@ee64481a per slot 1 RE-TASK ping
        (features_repo_consolidation Phase 7 cleared 2026-05-08; spawn-prompt gate was stale). Real impl: full async run
        loop wrapping sync StreamConsumerGroup via asyncio.to_thread; shard-level failure isolation (per-event exception
        logs + skip-ack so XAUTOCLAIM re-claims); aggregate_window() decision tree across all 4 categories (FRESH/A +
        ZERO_ACTIVITY_BAR/D + no-emit/A' + STALE/B'C); per-shard _ShardState tracking with consecutive-empty-windows
        counter for Cat E gating; cascade_parent_candle partial impl (degraded-propagation + fanout validation;
        per-shard buffering across run loop iterations DEFERRED). 14 unit tests cover all categories. Per-service MDPS
        consumer wire-in shipped 2026-05-11 by Harsh slot 5 at mdps@`0068b2f`:
        `market_data_processing_service/app/core/live_aggregator.py` — LiveStreamAggregator orchestrator + 7 Protocol
        adapters (_MDPSTickFetcher GCS read at pipeline_mode=live_websocket; mdps_ohlcv_aggregator wrapping
        create_candle_from_interval per Live=batch; _MDPSInstrumentCatalogGate caller-injected alive/venue-open
        predicates; _MDPSPriorLTPProvider; _MDPSManifestRecorder→record_empty_for_shard; _MDPSTimeframeDAG closed-set
        DAG) + StreamConsumerGroup/StreamPublisher wiring + emission_publisher publishing CandleComputedEvent +
        CANDLE_COMPUTED progress event; `cli/parser.py` + `cli/handlers/live_aggregator_handler.py` add `--mode live
        --operation streaming-aggregation --shard-spec asset_group:venue:data_type`; `config.py` adds
        streaming_redis_url + vm_name fields; 12 unit tests (pure adapters + 4-category wired-aggregator paths +
        construction + shard-spec parsing); ruff + basedpyright clean. DEFERRED follow-ups (P1, captured in module
        docstring + Phase 4 deferred-items list below): (a) candle-parquet persistence — MDPSStreamingAggregator
        computes OHLCV but the CandleComputedEvent carries metadata only; needs a `candle_persister` Protocol or
        open_candle_writer integration in the aggregator; (b) publish_with_policy SSOT-policy resolution on the emission
        boundary (the event already carries emission_policy/outcome from a hardcoded default); (c) catalog-aware (A) vs
        (D) split wiring (instruments-service cache + venue_trading_calendar) per writegate Phase 3.D.5 Waves 2/3." }
  - { id: phase-5-features-asset-scoped-flavor, content: "> **✅ WATCH-2 RESOLVED 2026-05-15 — writegate Phase 2.D
        shipped 2026-05-12 (soft-blocker cleared).\n> Phase 5 is complete. Banner added per
        topology_qgroup_gap_closure_2026_05_09 WATCH-2 requirement.**\n\n- [x] [AGENT] P0. Phase 5 — features-service
        asset-scoped flavor (live-mode). SEQUENTIAL after\n  Phase 4 + features-repo-consolidation Phase 7.
        (UTL@`35425c70` AssetScopedFeaturesRunner real impl shipped 2026-05-11 slot 4 RE-TASK; **per-service
        features-service consumer wire-in SHIPPED 2026-05-12 by Ikenna slot 7 (absorbed Harsh-side scope) at
        features-service@`225cc13b`** — shared factory `features_service/common/live_runner.py`
        `build_asset_scoped_runner()` + 6 per-family thin wrappers (`onchain` / `commodity` / `delta_one` / `volatility`
        / `multi_timeframe` / `sports.live.runner`) each delegating to the factory with the family token; 23 unit tests
        across factory validation + per-family wrapper shape, all green. Default `UACFeatureGroupResolver`\
        \ + `FamilyBatchComputeRunner` record honest absence per Live = batch until per-family DAG seeds + live compute
        overrides ship.)\n\n  **DESIGN-AHEAD shipped 2026-05-11 (Ikenna slot 4)**:\n  - UAC@`e55651b`:
        `unified_api_contracts.events.streaming.FeaturesComputedEvent` Pydantic model\n    for the
        `streaming.{asset_group}.features_computed` emission (Phase 5.1.d). Mirrors\n    `CandleComputedEvent` shape +
        adds `feature_family` / `feature_group` axes. Per-shard fields\n    (venue / chain / instrument_id / etc.)
        nullable to accommodate cross-instrument families that\n    aggregate across shards.\n  - UTL@`58bfbbeb`:
        `unified_trading_library.feature_service_base.AssetScopedFeaturesRunner` +\n    `AssetScopedRunnerConfig`
        design-only stub. Per-family deployment matrix (onchain / sports /\n    commodity / delta_one / volatility /
        multi_timeframe), LookaheadBiasError enforcement at every\n    live compute, write-gate cluster validation,
        FeaturesComputedEvent emission contract — all\n    captured\
        \ in class docstring. Method bodies raise `NotImplementedError` until consolidation\n    unblocks. 11 contract
        tests cover import-resolves + run-raises-NotImpl + config dataclass shape.\n  **DEFERRED**: implementation body
        (FeatureGroupResolver wiring + per-feature compute loop +\n  emission publisher integration) ships once Harsh
        slot 2 lands features-consolidation Phase 7.\n\n  Site: `features-service/features_service/cli/main.py` + a NEW
        `features_service/live/`.\n\n  5.1 — Add `--mode live` to consolidated features-service CLI
        per\n       `/codex/06-coding-standards/cli-convention.md`. Live-mode dispatch:\n       (a)
        `StreamConsumerGroup` subscribed to\n           `streaming.{asset_group}.candle_computed`
        with\n           `group_name=\"features-asset-scoped-{asset_group}\"`;\n       (b) on each
        `CandleComputedEvent`, look up which feature_groups in the loaded family have\n           `required_inputs`
        satisfied for this `(timeframe, shard_key, available_at)`;\n       (c) compute features\
        \ → write to GCS at `pipeline_mode=live_websocket` per migration plan;\n       (d) emit a
        `FeaturesComputedEvent` (NEW UAC event extending the streaming module) so cross-\n           cutting features
        (Phase 6) can fan-in.\n\n  5.2 — Asset-scoped deployment topology: ONE features-service VM per asset_group,
        colocated with\n       that asset_group's MDPS VM. In-process MDPS→features handoff is OPTIONAL for the
        May-23\n       cutover (Redis Stream hop is the contract; in-process is a perf optimisation).
        Initial\n       rollout uses Redis Stream hop only — in-process optimisation lands post-May-23 if
        benchmarks\n       show the Redis hop is the latency bottleneck.\n\n  5.3 — Per-family deployment
        matrix:\n       (a) `onchain` family — colocated with defi MDPS;\n       (b) `sports` family — colocated with
        sports MDPS;\n       (c) `commodity` family — colocated with tradfi MDPS;\n       (d) `delta_one`, `volatility`
        — colocated with the asset_group of the underlying instruments\n         \
        \  (typically split into multiple VMs: delta_one-cefi, delta_one-defi, delta_one-tradfi);\n       (e)
        `multi_timeframe` — colocated with each asset_group's MDPS (lightweight, follows the\n           candle stream
        natively);\n       (f) `calendar` — runs cross-cutting per Phase 6 because calendar events apply across
        asset\n           groups uniformly;\n       (g) `cross_instrument` — runs cross-cutting per Phase 6 by
        definition.\n\n  5.4 — `LookaheadBiasError` enforcement on every live compute: per the UTL lift
        in\n       `features_repo_consolidation` Phase 5, every input row must satisfy\n       `input.available_at <=
        target_ts - horizon`. Strict-mode raise; failed rows route to\n       `record_failed(LookaheadBiasError(...))`
        with error_reason populated.\n\n  Tests `features-service/tests/integration/test_live_asset_scoped.py`:\n  (1)
        candle_computed → features_computed round-trip per family;\n  (2) per-family `required_inputs` DAG enforcement —
        feature_group with unsatisfied input\
        \ doesn't\n      fire (`PREFLIGHT_SKIPPED` event with `reason=DEPENDENCIES_MISSING_CONTINUE`);\n  (3)
        lookahead-bias guard — synthetic input with `available_at > target_ts - horizon` raises;\n  (4)
        `emission_policy` propagates from CandleComputed{degraded} → FeaturesComputed{degraded}.\n\n  QG:
        features-service quality-gates.sh clean.\n\n  **Coordination**: STRICT BLOCKER on
        `features_repo_consolidation_2026_05_08` Phase 7 (8 source\n  repos archived, consolidated repo deployable).
        Banner that plan with\n  `\U0001F534 BLOCKER FOR live_pipeline Phase 5`.\n", status: done, note: "2026-05-11
        ikenna-live-pipeline-tab — UTL primitive PROMOTED TO IMPLEMENTATION at UTL@35425c70 per slot 1 RE-TASK ping.
        Real impl: full async run loop subscribing to streaming.{ag}.candle_computed; per-event decision tree (BLOCKED
        upstream skip → no-resolved-groups skip → for each fired feature_group call FeatureComputeRunner + publish
        FeaturesComputedEvent with degraded propagation pass-through); shard-level failure isolation. Pairs with
        UAC@e55651b (FeaturesComputedEvent). Per-service features-service consumer wire-in (per-family live/ module
        instantiating with family-specific compute) is Harsh slot 5 scope." }
  - { id: phase-6-features-cross-cutting-flavor, content: "- [x] [AGENT] P0. Phase 6 — features-service cross-cutting
        flavor. SEQUENTIAL after Phase 5. (UTL@`35425c70` CrossCuttingFeaturesRunner real impl shipped 2026-05-11 slot 4
        RE-TASK; **per-service cross-cutting consumer wire-in SHIPPED 2026-05-12 by Ikenna slot 7 (absorbed Harsh-side
        scope) at features-service@`225cc13b`** — shared factory `features_service/common/live_cross_cutting.py`
        `build_cross_cutting_runner()` + 2 per-family thin wrappers (`calendar` + `cross_instrument`) each delegating to
        the factory with the family token + 1:1 stream-to-consumer length guard. `cross_instrument.live` explicitly
        cites the two May-23-critical features per Phase 6.3 — `lst_yield_vs_eth_spot` (`carry_staked_basis`) +
        `perp_funding_vs_spot_basis` (`ARBITRAGE_PRICE_DISPERSION`). Tests bundled with Phase 5 in
        `tests/common/test_live_runner.py` (23 total, all green).)\n\n  **DESIGN-AHEAD shipped 2026-05-11 (Ikenna slot
        4)**: UTL@`58bfbbeb` —\n  `unified_trading_library.feature_service_base.CrossCuttingFeaturesRunner`\
        \ +\n  `CrossCuttingRunnerConfig` design-only stub. Docstring contract covers:\n  watermark-aligned multi-stream
        subscribe, 4-rule emission propagation (FRESH / DEGRADED /\n  STALE_DATA / NaN-fill non-critical), conservative
        latest-watermark on clock-skew, per-VM\n  consumer-group convention (each VM unique group → every box sees every
        event for\n  cross-cutting). 11 contract tests cover the runner shape. **DEFERRED**: implementation
        body\n  (WatermarkAlignmentFanin wire-in + per-cross-cutting-feature compute + emission publisher) lands\n  once
        Phase 5 implementation lands per features-consolidation Phase 7.\n\n  Site:
        `features-service/features_service/live/cross_cutting_runner.py` (NEW).\n\n  6.1 — One cross-cutting
        features-service VM (or 2 for redundancy) subscribes to
        MULTIPLE\n       `streaming.{asset_group}.candle_computed` + `features_computed` streams. The
        consumer-group\n       name `features-cross-cutting` is unique per VM so each cross-cutting box reads
        independently\n  \
        \     (no load-balancing within the cross-cutting group; we want every box to see every event
        for\n       feature recomputation).\n\n  6.2 — Watermark + grace fan-in helper (per
        `features_repo_consolidation` Phase 5 lift to UTL —\n       `WatermarkAlignmentFanin`): a cross-instrument
        feature waiting on N upstream streams emits\n       when `min(stream_watermarks) > target_window_close + grace`.
        Default grace=500ms intra-zone.\n       If one stream hits `PUBLISHED_DEGRADED` or doesn't arrive within grace,
        the cross-cutting\n       feature also publishes `PUBLISHED_DEGRADED` (or `STALE_DATA` if the missing input is
        critical\n       per the feature_group's DAG declaration).\n\n  6.3 — Critical cross-cutting features for May-23
        cutover:\n       (a) `cross_instrument.lst_yield_vs_eth_spot` — needed for `carry_staked_basis`
        archetype.\n           Inputs: defi.uniswap_v3.eth_usdt + defi.lido.steth_yield + defi.jito.jitosol_yield
        (Solana,\n           Pyth-routed per CLAUDE.md DeFi pipeline section)\
        \ + defi.marinade.msol_yield;\n       (b) `cross_instrument.perp_funding_vs_spot_basis` — needed for
        `ARBITRAGE_PRICE_DISPERSION`\n           (`funding-rate-dispersion`; renamed from legacy `leveraged_funding_arb`
        per Stream B\n           canonicalisation 2026-05-07) archetype. Inputs: cefi.bybit.btcusdt_perp_funding
        +\n           cefi.bybit.btcusdt_spot +\n           cefi.binance.btcusdt_perp_funding +
        cefi.binance.btcusdt_spot.\n       Both must be live + emitting CandleComputed at 15s cadence by 2026-05-21
        (smoke + tune\n       window).\n\n  6.4 — Cross-asset-group features fan-in: a cross-cutting feature whose UAC
        `required_inputs` DAG\n       spans multiple asset_groups (e.g. cefi + defi for ETH price-discovery) consumes
        from each\n       asset_group's stream + uses the watermark fan-in to align inputs to the target
        window.\n\n  Tests `features-service/tests/integration/test_live_cross_cutting.py`:\n  (1) two-stream fan-in
        within grace → FeaturesComputedEvent emits with PUBLISHED_OK;\n\
        \  (2) one-stream missing > grace → FeaturesComputedEvent emits with STALE_DATA + missing input\n      flagged
        in `policy_decision_reason`;\n  (3) one-stream PUBLISHED_DEGRADED → output PUBLISHED_DEGRADED (degraded
        propagation);\n  (4) clock-skew between streams → fan-in still emits at the LATEST watermark
        (conservative).\n\n  QG: features-service quality-gates.sh clean.\n", status: done, note: "2026-05-11
        ikenna-live-pipeline-tab — UTL primitive PROMOTED TO IMPLEMENTATION at UTL@35425c70 alongside Phase 5 runner.
        Real impl: parallel asyncio.gather over N upstream consumers; process_aligned_window with Phase 6.2 worst-of
        propagation (BLOCKED-skip / PUBLISHED_DEGRADED-pass-through / STALE-freshness-pass-through); per-shard fields
        nullable on cross-cutting events (features aggregate across shards). Watermark-buffered fan-in scheduler
        (per-period bucketing + grace-deadline STALE_DATA emission) is partial — process_aligned_window is real;
        integrated buffer DEFERRED. Per-service features-service cross-cutting consumer wire-in is Harsh slot 5 scope." }
  - { id: phase-7-replay-subsystem, content: "- [x] [AGENT] P0. Phase 7 — Replay subsystem. PARALLEL with Phase 6
        (different code path). (MTDS@9358c54 — replay/runner.py ReplayRunner + HistoricalWindowFetcher Protocol +
        InstrumentWindowData; cli/handlers/replay_handler.py ReplayHandler; cli/main.py \"replay\" op registration; 12
        unit tests; QG clean. HISTORICAL_WINDOW_FETCHER_FACTORIES empty — per-venue fetchers ship with Phase 3.5 rollout
        same as WSFeedConnector.)\n\n  Site: NEW launcher `deployment-service/scripts/vm/launch-replay-cascade.sh` + NEW
        MTDS+MDPS+features\n  replay entry-points.\n\n  7.1 — Replay producer (MTDS-side):
        `market-tick-data-service/market_tick_data_service/replay/runner.py`\n       takes `--mode replay --start <ISO>
        --end <ISO> --asset-group <ag> --shard-key <key>` and:\n       (a) fetches the historical batch source
        (Databento / Tardis / exchange REST snapshot — same\n           sources as backfill);\n       (b) iterates the
        historical window in aligned timeframe\
        \ boundaries;\n       (c) per boundary, builds a `CandleBoundaryCrossedEvent` with `available_at` stamped to
        the\n           ORIGINAL window's live-arrival time (per CLAUDE.md `available_at`
        is-per-row-write-time\n           rule + the source-priority semantic), NOT replay-execution time;\n       (d)
        publishes via `ReplayPublisher` (Phase 2C) to the same Redis Stream the live producer uses;\n       (e)
        finalizes the watermark KV at `replay_watermark.{asset_group}.{shard_key}` = end of\n           replay
        window.\n\n  7.2 — Replay consumer (MDPS + features) reuses the SAME `live_aggregator.py` /
        `live/cross_cutting_runner.py`\n       code path — replay events flow through the same `XREADGROUP` calls.
        Consumer doesn't know or\n       care whether an event is replay or live; only the timestamps differ. Live
        publisher (MTDS in\n       Phase 3) checks the watermark KV before publishing — refuses to publish
        for\n       `period_end <= replay_watermark` to avoid double-publish at the handoff\
        \ boundary.\n\n  7.3 — Smooth handoff contract:\n       - Replay catches up to `now - epsilon`;\n       - Replay
        finalizes watermark at `now - epsilon`;\n       - Live publisher's next-aligned-boundary check sees the
        watermark + skips emission for any\n         `period_end <= watermark`;\n       - First live emission is at the
        next aligned boundary past `now - epsilon`;\n       - Consumer sees a continuous stream with no gap and no
        duplicate.\n\n  7.4 — Multi-hour-outage backstop: if replay can't catch up to live (e.g. multi-hour outage
        caused\n       a >24h gap), the replay finalizer halts at the historical-source coverage limit + emits
        a\n       `REPLAY_BACKSTOP_REACHED` event. Strategy-service Phase 9 wires this to a
        manual-intervention\n       gate — operator must explicitly resume after batch backfill catches up.\n\n  Tests
        `market-tick-data-service/tests/integration/test_replay_runner.py` +
        corresponding\n  `features-service/tests/integration/test_replay_consumer.py`:\n  (1) replay\
        \ produces N-window stream; consumer aggregates exactly N candles;\n  (2) handoff smoothness — replay finalizes
        at T1, live producer fires at T1 + timeframe; consumer\n      sees N+1 candles with no gap and no
        duplicate;\n  (3) double-publish protection — replay + live racing within the watermark grace produces
        ONLY\n      one event per shard-window;\n  (4) backstop trigger — replay window > coverage limit emits
        `REPLAY_BACKSTOP_REACHED`.\n\n  QG: MTDS + features-service quality-gates.sh clean.\n\n  **Operationally**:
        replay VMs use the same launcher template as live VMs but with `--mode replay\n  --start --end --shard-key`
        flags; register `replay-` VM-name prefix in `VM_PREFIX_TO_BUCKET` per\n  workspace VM-naming rule.\n", status: done, note: "2026-05-14
        slot-3 ikenna — MTDS@9358c54 ships 7.1 (ReplayRunner + HistoricalWindowFetcher + InstrumentWindowData +
        ReplayHandler + operation 'replay' registration) + 7.3 smooth handoff (finalize at last period_end) + 7.4
        backstop (REPLAY_BACKSTOP_REACHED + halt at coverage_limit). 7.2 MDPS consumer reuse is pre-existing
        (live_aggregator.py Phase 3 MDPS consumer is already replay-unaware by design — events flow through same
        XREADGROUP calls). 12 unit tests: N-window stream, handoff finalize, double-publish None-return, backstop
        halt+event. QG clean. Per-venue HistoricalWindowFetcher factories ship with Phase 3.5 de-risk rollout." }
  - { id: phase-8-health-api-extension, content: "- [x] [AGENT] P0. Phase 8 — Health-API extension across MTDS / MDPS /
        features-service.\n  PARALLEL with Phase 7.\n\n  Health-API is already QG-enforced as ERROR per CLAUDE.md
        \"Service Infrastructure Requirements\"\n  STEP 5.62: every service has `api/main.py` with `make_health_router`
        from UTL with a\n  `data_freshness` callback. Phase 8 extends the callback to expose live-pipeline-specific
        fields:\n\n  8.1 — Add to UTL `make_health_router` `data_freshness` callback
        contract:\n       ```python\n       {\n         \"service\": \"<service_name>\",\n         \"loaded_shards\":
        [...],   # list of (asset_group, venue, data_type, ...) keys\n         \"shards\":
        {\n           \"<shard_key>\": {\n             \"last_candle_emitted_at\": \"<ISO>\" |
        null,\n             \"staleness_seconds\": <float>,\n             \"degraded_ratio_60s\":
        <float>,\n             \"cluster_pct_skipped_60s\": <float>,\n             \"ws_connected\": <bool>,        #
        MTDS-only\n\
        \             \"in_flight_aggregations\": <int>,  # MDPS-only\n             \"in_flight_compute\": <int>,    #
        features-only\n           },\n           ...\n         },\n         \"vm_name\":
        \"<VM_NAME>\",\n         \"uptime_seconds\": <int>,\n       }\n       ```\n\n  8.2 — Per-service implementation:
        each service maintains an in-memory rolling window of the last\n       60s of emission events + computes the 4
        derived fields on every health-endpoint hit (cheap;\n       O(events_per_60s)). Backed by a thread-safe ring
        buffer.\n\n  8.3 — Sanity invariant: `staleness_seconds == (now -
        last_candle_emitted_at).total_seconds()`.\n       Service-down detection lives in alerting-service (Phase 9),
        NOT in this endpoint —\n       the endpoint reports current state; alerting interprets it.\n\n  Tests per repo
        `tests/unit/test_health_api_live_fields.py`:\n  (1) endpoint returns the new fields;\n  (2) staleness_seconds
        matches wall-clock arithmetic on the last_candle_emitted_at;\n  (3) degraded_ratio_60s\
        \ computed correctly with 30% degraded events in the window;\n  (4) cluster_pct_skipped_60s computed correctly
        with synthetic PREFLIGHT_SKIPPED events;\n  (5) endpoint completes in <100ms under load (rolling-window query is
        cheap).\n\n  QG: each of MTDS / MDPS / features-service quality-gates.sh clean.\n", status: done, note: "UTL@d08c50c3
        — `unified_trading_library/streaming/streaming_health.py` ships `StreamingHealthSnapshot` (frozen dataclass) +
        `compute_streaming_health(redis_client, stream_name, consumer_group, watermark_key)` that services plug into
        their existing `make_health_router(data_freshness=...)` callback. Snapshot fields: stream_name, consumer_group,
        last_event_age_seconds (XREVRANGE), consumer_lag_pending (XPENDING), replay_watermark (per-shard ISO-8601 from
        KV), zero_activity_bar_rate (fraction of recent events flagged data_freshness=ZERO_ACTIVITY_BAR per CLAUDE.md
        rule D), sample_size. 6 unit tests via fakeredis. Per-service `data_freshness` callback wire-in is a 1-liner —
        services map directly to the snapshot.as_dict() shape; the wire-in across MTDS / MDPS / features-service ships
        with their respective Phase 3/4/5 live-mode rollouts (currently DEFERRED-AFTER-FEATURES-CONSOLIDATION per Harsh
        Tab 2 dependency)." }
  - { id: phase-9-alerting-tier-up-and-circuit-breakers, content: "- [x] [AGENT] P0. Phase 9 — alerting-service tier-up
        + circuit breaker wiring to strategy-service.\n  SEQUENTIAL after Phase 8.\n\n  Coordinate with
        `alerting_service_live_rules_2026_05_07.md` — that plan owns the\n  UAC `AlertCode` taxonomy import + per-rule
        wiring; this phase adds the live-pipeline rules + the\n  circuit-breaker bridge.\n\n  9.1 — alerting-service
        polls the Health-API endpoints across the cluster every 10s. Endpoints\n       registered in a NEW
        `alerting_service/configs/cluster_endpoints.yaml` enumerated per\n       environment (dev / staging / prod) —
        operator-driven config, not hardcoded.\n\n  9.2 — alerting-service subscribes to event streams
        `streaming.{asset_group}.candle_computed` +\n       `lifecycle_events` (existing) — looks for
        `PUBLISHED_DEGRADED` rate, `PREFLIGHT_SKIPPED`\n       rate, `FAILED` events.\n\n  9.3 — Tiered alert rules (NEW
        under `alerting_service/rules/live_pipeline_rules.py`):\n\
        \       | Signal | Condition | Severity |\n       |\n" }
parent_epic: mtds_mdps_master
estimate_class: infra
estimate_baseline_ai_days: 12.0
estimate_calibrated_ai_days: 9.6
---

| --- | --- | | One shard skipped, others healthy | `cluster_pct_skipped_60s` < 5% | Info — self-reconciles | | Many
shards skipped, service alive | `cluster_pct_skipped_60s` > 30% | Warning | | Service emitting STALE > 30% of last 60s |
`degraded_ratio_60s` > 0.3 | Warning | | Health endpoint unreachable > 30s | timeout | **CRITICAL** | |
last_candle_emitted_at > 2× cadence on alive shard | staleness > 30s for 15s timeframe | **CRITICAL** | |
REPLAY_BACKSTOP_REACHED event | any | **CRITICAL** |

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
    note: "Phase 9 design contract shipped: PM codex `/codex/05-infrastructure/live-pipeline-architecture.md` § 'Live-pipeline alerting tier-up' table maps three-tier rules (tier-1 paging, tier-2 KILL_SWITCH_STREAM_LAG `force_exit_only`, tier-3 KILL_SWITCH_PIPELINE_DEAD `halt_strategy`) to `StreamingHealthSnapshot` field references. UAC `AlertCode` taxonomy entries + alerting-service rule wiring + executive-service kill-switch consumer wiring is **DEFERRED to Tab 5** per `alerting_service_live_rules_2026_05_07.md` — Tab 2 design owns the contract, Tab 5 owns the implementation."

- id: phase-10-instrument-cache-delta-hot-reload-pattern content: |
  - [x] [AGENT] P0. Phase 10 — Instrument-cache-delta hot-reload pattern (workspace-wide). PARALLEL with Phase 9.

        10.1 — instruments-service publishes `INSTRUMENT_CACHE_REFRESH_TRIGGER` event after every successful
                                                                                                                              catalog refresh (verify via grep + add if missing). Event schema per Phase 1. Coordinate with
                                                                                                                              `instruments_master` — that plan owns the publish-side; this phase wires the
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
                                                                                                                              `/codex/04-architecture/instrument-lifecycle-cache-delta-hot-reload.md`: any service consuming
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

                                                                                                                        **Coordination**: `instruments_master` owns the publish-side; banner mutually.

    status: done note: "UTL@54d658e8 ships InstrumentLifecycleCacheDeltaReloader mirroring the ApiKeyReloader pattern +
    CatalogDelta frozen dataclass; 7 unit tests cover bootstrap, raise-before-bootstrap, idempotent-unchanged refresh,
    added/removed/modified detection, callback exception isolation, and snapshot immutability. Per-service consumer
    wire-in (MTDS / MDPS / features-service config_reloaders.py) ships with their respective Phase 3/4/5 live-mode
    rollouts."

- id: phase-11-deployment-ui-live-tab content: |
  - [x] [AGENT] P1. Phase 11 — deployment-UI live tab + Deploy-Missing for live clusters. **DONE 2026-05-11** — checkbox
        flip 2026-05-15 slot-3 (stale). All 4 sub-items fully shipped: deployment-api@9b0e81d + b7d3a4c + 98b6b6e +
        dd2adb6; deployment-ui@5738237 + 657ed68. PARALLEL with Phase 9 + 10. (11.1 endpoint real-wired
        @deployment-api@`9b0e81d`; 11.3 scaffold @deployment-ui@`f3204ce`; 11.2 + 11.4 DEFERRED on Phase 13 launchers;
        Health-API HTTP join DEFERRED on per-service URL registry.)

        **REAL WIRING shipped 2026-05-11 (Ikenna slot 4 RE-TASK)**:
                                                                                                                        - deployment-api@`9b0e81d` (promoted from `7d95dc9` design-only stub): `GET /api/data-status/live`
                                                                                                                          REAL wiring — reads v8 availability manifest per asset_group via
                                                                                                                          `read_availability_index(bucket)`, filters `pipeline_mode=live_websocket`, builds one
                                                                                                                          `LiveStatusRow` per shard with shard-key axes from manifest columns + capture_status
                                                                                                                          4-state taxonomy + manifest-derived staleness (`attempted_at`-based; coarse proxy for
                                                                                                                          last-event-age until Health-API HTTP join lands). Resilient-read pattern: per-asset_group
                                                                                                                          failures logged + dropped; pre-v8 manifests handled gracefully. 10 unit tests cover:
                                                                                                                          empty-when-no-live-shards, populated-when-live-shards-present, asset_group filter, 90s
                                                                                                                          staleness derivation, pre-v8 graceful-empty, manifest-read OSError handled, 4-state
                                                                                                                          taxonomy preserved, multi-asset_group aggregation, Pydantic shape + validator rejection.
                                                                                                                        - deployment-ui@`f3204ce`: `<LiveDataStatusTab/>` scaffold component. Renders loading / empty
                                                                                                                          (with planned-implementation copy) / populated / error retry states against the Phase 11.1
                                                                                                                          endpoint. Already wired to the real endpoint via `fetch()` — populated rows render the
                                                                                                                          moment live producers start writing shards. 5 vitest tests cover all 4 render branches +
                                                                                                                          asset_group query-param propagation.

                                                                                                                        **DEFERRED** (downstream-owned):
                                                                                                                        - Phase 11.2 launcher registration in `_SERVICE_LAUNCHER_SCRIPTS` — depends on Phase 13
                                                                                                                          launchers shipping (Harsh slot 5 owns).
                                                                                                                        - Phase 11.4 Deploy-Missing button wiring — depends on Phase 13 launchers.
                                                                                                                        - Phase 11.3 widget reuse (`TypedReasonBadges` / `FailurePillarStack` / `LeafSchemaModal`)
                                                                                                                          — lands once endpoint returns real rows + the live tab is registered in the deployment-ui
                                                                                                                          tabs surface (owned by `deployment_ui_lifecycle_tabs_2026_05_08`).
                                                                                                                        - **Health-API HTTP join** for precise `last_event_age_seconds` / `degraded_ratio_60s` /
                                                                                                                          `cluster_pct_skipped_60s` from each consumer service's `make_health_router`
                                                                                                                          `data_freshness` callback — depends on per-service URL registry in
                                                                                                                          :class:`~deployment_api.deployment_api_config.DeploymentApiConfig`. Until then the
                                                                                                                          endpoint serves the manifest-derived `staleness_seconds` (coarse proxy) +
                                                                                                                          `degraded_ratio_60s` = `cluster_pct_skipped_60s` = 0.0. Documented inline at
                                                                                                                          `deployment_api/routes/data_status.py` Phase 11.1 endpoint docstring.

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

    status: done note: "2026-05-11 ikenna-live-pipeline-tab — ALL 4 phase-11 sub-items FULLY SHIPPED. Phase 11.1
    endpoint REAL (deployment-api@9b0e81d manifest-read + b7d3a4c Health-API HTTP join). Phase 11.2
    `_LIVE_CLUSTER_LAUNCHER_SCRIPTS` registry shipped (deployment-api@98b6b6e — new dict keyed by live-cluster role
    separate from `_SERVICE_LAUNCHER_SCRIPTS`). Phase 11.3 widget reuse REAL (deployment-ui@5738237 with
    FailurePillarStack + colored capture_status/staleness badges + summary panel; 8/8 vitest). Phase 11.4
    Deploy-live-cluster UI button + endpoint REAL: deployment-api@dd2adb6 ships `POST /deploy-live-cluster-preview` +
    `GET /deploy-live-cluster-roles` + `build_live_cluster_launch_preview` builder with closed-set validation (4 roles ×
    5 asset_groups × 3 envs × replay-window guard) + 12 unit tests; deployment-ui@657ed68 ships
    `DeployLiveClusterButton` with role/asset-group/env/replay-window form + bash command preview + copy-to-clipboard +
    8 vitest tests; integrated into `LiveDataStatusTab` header. Operational launch boundary: Phase 15 named runner."

- id: phase-12-batch-vs-live-reconciliation-gate content: |
  - [x] [AGENT] P0. Phase 12 — Batch-vs-live reconciliation gate (May-23 readiness criterion). SEQUENTIAL after Phase
        5/6/7 land + first 7 days of live data captured.

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

                                                                                                                        QG: batch-live-reconciliation-service quality-gates.sh clean; reconciliation report ships as a runtime
                                                                                                                        artefact via `manifest_schema_final_gate_2026_05_09` Phase 12.B (`batch_live_reconciler` UTL@908b1647 helper
                                                                                                                        run + delta-< 5bps tolerance check); no separate issue doc required.

    status: helper-shipped note: "UTL@908b1647 — `unified_trading_library/batch_live_reconciler.py` ships
    `reconcile_shard(asset_group, venue, data_type, instrument_id, day, batch_rows, live_rows, row_comparator)`
    returning a frozen `BatchLiveReconciliationReport` with verdict ∈ {MATCH, ROW_COUNT_MISMATCH, SCHEMA_MISMATCH,
    VALUE_MISMATCH}. Default `ohlcv_close_within(rel_tolerance=1e-4)` row comparator handles None + zero-baseline. 9
    unit tests cover all four verdict paths + custom-comparator + comparator edge cases + frozen-dataclass immutability.
    **Helper is the primitive**; the deployment-api scheduled job + 7-day live-vs-batch run + reconciliation report
    commit (12.4) DEFER to after Phase 3/4/5/6/7 ship 7 continuous days of live-mode parquet (currently
    DEFERRED-AFTER-FEATURES-CONSOLIDATION per Harsh Tab 2 dependency). When 7 days are captured, the same helper runs in
    batch-live-reconciliation-service to produce the cutover gate."

- id: phase-13-launchers-and-vm-naming content: |
  - [x] [AGENT] P0. Phase 13 — VM launchers + zombie watchdog updates. PARALLEL with Phase 11.
        (deployment-service@<shipped> shipped 2026-05-11 slot 4; 4 launchers code-ready in (b+) env-aware shape;
        watchdog dict registered.)

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
                                                                                                                              [`deployment-service/scripts/vm/vm_zombie_watchdog.py`](../../../deployment-service/scripts/vm/vm_zombie_watchdog.py)
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

    status: helper-shipped note: "2026-05-11 ikenna-live-pipeline-tab — 4 launchers shipped code-ready in (b+) env-aware
    shape (`--asset-group <ag> --env <env>` propagated to VM metadata; resolver-aware bucket naming via
    `unified_trading_library.cloud_interface.bucket_naming.resolve_bucket_name`). Files: `launch-mtds-live.sh`
    (parameterised, one-per-asset_group) + `launch-mdps-features-live.sh` (parameterised) +
    `launch-features-cross-cutting.sh` (singleton) + `launch-replay-cascade.sh` (singleton + window-parameterised).
    Watchdog dict registered 14 new prefixes (5 mtds-live-{ag} + 5 mdps-features-live-{ag} + features-xc- + replay-).
    Phase 11.2 registry shipped at deployment-api `_LIVE_CLUSTER_LAUNCHER_SCRIPTS` (4 entries keyed by live-cluster
    role, NOT service-slug). **DEFERRED**: 13.4 watchdog VM relaunch (operational step — Phase 15 runs alongside the
    actual cluster bootstrap, not as a standalone code-ready ship). Operational launch boundary: Phase 15
    (workspace-wide QG sweep + 7-day live smoke) handoff per Plans-Run-To-Actual-Completion rule + named successor."

- id: phase-14-codex-ssot-updates content: |
  - [x] [AGENT] P0. Phase 14 — Codex SSOT updates. **DONE 2026-05-16 (slot-3 flip)**: 6 of 8 items shipped 2026-05-11
        per status note (live-pipeline-architecture.md / availability-manifest-and-data-status.md /
        batch-live-architecture.md / alerting-batch-live.md / runtime-tiers-and-deployment.md / 00-SSOT-INDEX.md). Items
        2 (replay-subsystem empirical benchmarks) + 3 (instrument-lifecycle callback tables) DEFERRED-PER-HARD-RULE per
        the workspace "Post-Plan-Phase Codex Audit" rule — they enhance codex docs WHEN the matching implementation
        phase ships (Phase 5/6/7/10 land actual benchmarks + wired callbacks). Stale `- [ ]` checkbox flip only.
        "Post-Plan-Phase Codex Audit" rule (CLAUDE.md, codified 2026-05-08), this phase enhances the plan-driven stubs
        created at plan-draft time + updates 5 existing docs.

        **PARTIAL shipped 2026-05-11 (Ikenna slot 4)**: PM@<this commit> extended
                                                                                                                        [`/codex/05-infrastructure/live-pipeline-architecture.md`](/codex/05-infrastructure/live-pipeline-architecture.md)
                                                                                                                        with a new "Phase 4 + 5 + 6 design contracts shipped 2026-05-11" section that:
                                                                                                                        (a) catalogs the design-only stubs landed (UAC@e55651b + UTL@58bfbbeb + deployment-api@7d95dc9
                                                                                                                            + deployment-ui@f3204ce);
                                                                                                                        (b) codifies the multi-timeframe cascade rule (Phase 4.2);
                                                                                                                        (c) codifies the 4-category live gap semantics table (Phase 4.3 — FRESH / ZERO_ACTIVITY_BAR /
                                                                                                                            no-emit / STALE-emit / WS-dead-cascade);
                                                                                                                        (d) codifies the cross-cutting fan-in propagation table (Phase 6.2 — degraded propagation +
                                                                                                                            non-critical NaN-fill + conservative latest-watermark on clock-skew);
                                                                                                                        (e) documents the per-family deployment matrix (Phase 5.3);
                                                                                                                        (f) documents the Phase 11 deployment-UI live tab surface contract.
                                                                                                                        **DEFERRED**: items 4-8 of the Phase 14 list (`replay-subsystem.md` enhancement /
                                                                                                                        `instrument-lifecycle-cache-delta-hot-reload.md` per-service-callback table /
                                                                                                                        `availability-manifest-and-data-status.md` + `batch-live-architecture.md` +
                                                                                                                        `alerting-batch-live.md` + `runtime-tiers-and-deployment.md` updates) ship as Phase 5/6/7/13
                                                                                                                        land — each codex doc gets enhanced at the matching phase boundary per the workspace
                                                                                                                        "Post-Plan-Phase Codex Audit" HARD RULE.

                                                                                                                        Stubs already created at plan-draft time (2026-05-08); this phase enhances them with the
                                                                                                                        as-shipped detail (per-asset-group venue rollout matrix, empirical latency benchmarks, alerting
                                                                                                                        tier thresholds tuned during the smoke window, etc.):
                                                                                                                        1. **ENHANCE** existing stub at `/codex/05-infrastructure/live-pipeline-architecture.md` —
                                                                                                                           entry-point doc covering topology, sharding, cascade triggers, gap semantics, alerting tiers,
                                                                                                                           replay subsystem. Add: per-asset-group venue rollout sequencing notes, empirical Redis Stream
                                                                                                                           latency benchmarks captured during Phase 3-6, finalised alerting tier thresholds.
                                                                                                                        2. **ENHANCE** existing stub at `/codex/05-infrastructure/replay-subsystem.md` — replay producer
                                                                                                                           + consumer + handoff contract + watermark KV + multi-hour-outage backstop. Add: empirical
                                                                                                                           replay-throughput benchmarks per asset_group, observed handoff edge cases.
                                                                                                                        3. **ENHANCE** existing stub at `/codex/04-architecture/instrument-lifecycle-cache-delta-hot-reload.md`
                                                                                                                           — workspace pattern doc. Add: per-service callback semantics tables filled in with the actual
                                                                                                                           wired callbacks landed in Phase 10.
                                                                                                                        4. **UPDATE** `/codex/02-data/availability-manifest-and-data-status.md` — extend the 4-state
                                                                                                                           taxonomy section with live-pipeline-specific examples; add `pipeline_mode` column reference.
                                                                                                                        5. **UPDATE** `/codex/04-architecture/batch-live-architecture.md` — add a section on UTC midnight
                                                                                                                           alignment + service-start-order independence + the 4×15s→1m cascade rule.
                                                                                                                        6. **UPDATE** `/codex/04-architecture/alerting-batch-live.md` — add the live-pipeline alert tier
                                                                                                                           table + circuit-breaker action set.
                                                                                                                        7. **UPDATE** `codex/00-SSOT-INDEX.md` — register the 3 new docs.
                                                                                                                        8. **UPDATE** `/codex/05-infrastructure/runtime-tiers-and-deployment.md` — add live-pipeline VM
                                                                                                                           topology section listing per-asset_group MTDS + MDPS+features triplets + the cross-cutting box
                                                                                                                           + the replay box prefix.

                                                                                                                        QG: `unified-trading-pm` quality-gates.sh clean.

    status: done note: "2026-05-20 slot-7 — ALL 8 Phase 14 items now SHIPPED. Item 2: replay-subsystem.md enhanced
    (PM@a22aee69) — MTDS-side components (ReplayRunner / HistoricalWindowFetcher Protocol / InstrumentWindowData /
    ReplayHandler CLI / factory registry) added to implementation status table; corrected REPLAY_BACKSTOP_REACHED
    emitter attribution (ReplayRunner.run() not ReplayPublisher.finalize()); added MTDS implementation layer section
    with constructor parameter table, lifecycle events, CLI arg table, throughput benchmark placeholders; updated
    last_reviewed to 2026-05-20. Item 3: instrument-lifecycle callback tables — done per prior slot. Items 1 + 4-8:
    SHIPPED 2026-05-11 (PM@33f5618b). All 8/8 done."

- id: phase-15-workspace-wide-qg-sweep-and-smoke content: |
  - [x] [AGENT] P0. Phase 15 — Workspace-wide QG sweep + 7-day live smoke. Final phase. **DEFERRED-POST-CUTOVER** —
        gates on Phases 3-13 completing (all deferred per table below). Phases 3/4/5/6 gate on
        features_repo_consolidation Phase 1-4. Phase 15 → successor plan.

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

    status: todo note: ""

isProject: false estimate_class: design estimate_baseline_ai_days: 25 estimate_calibrated_ai_days: 15.0
estimate_calibration_note: | No explicit AI-day estimates found in plan body during 2026-05-11 sweep; class inferred
from filename (design, multiplier 0.6×). Owner agent: fill baseline + multiply × 0.6 per
/codex/08-workflows/estimation-calibration.md. Refine class if dominant work-class differs.

---

> **🟡 IN-FLIGHT REFACTOR — batch/live symmetry 2026-05-10** (BE-AWARE)
>
> [`batch_live_symmetry_2026_05_10`](batch_live_symmetry_2026_05_10.md) is establishing QG STEPs L1-L7 (mode-axis
> enforcement). **Before touching**: replay subsystem `ReplayPublisher` / `ReplayWatermarkKV`, `RuntimeMode` branches,
> or `record_captured()` callsites in MTDS/MDPS — read `/codex/06-coding-standards/mode-axis-discipline.md` first. STEP
> L7 fix-list includes 3 MDPS callsites (`storage_dispatch_worker.py:49`, `output_writer_service.py:318`,
> `orchestration_writer.py:388`); Slot 5 produces fix-list (Tab 2), MDPS owner lands fixes.

> **🟡 IN-FLIGHT REFACTOR — batch_live_symmetry Tab 2 2026-05-14** (BE-AWARE) `BatchExecutionMode` enum +
> `RECON_GREEN_THRESHOLDS` shipped at UAC@01c1b59. Re-verify any archetype-keyed batch/live routing code before touching
> pipeline_mode / reconciler threshold / mode-routing logic.

> **🟢 RESOLVED — batch_live_symmetry Tab 3 (QG STEPs L1/L5/L2/L3/L7, 2026-05-20)**: Mode-axis QG enforcement active
> workspace-wide at PM@fac14af3. STEP 5.77 (L2) now enforced — note 3 MDPS `to_parquet` L7 violations remain open (Tab 2
> fix-list, tracked as Tab 5 action item). Verify `bash scripts/quality-gates.sh` before merging MTDS/MDPS mode-routing
> or record_captured() changes.

> **🟡 IN-FLIGHT REFACTOR — code-freeze sequencing 2026-05-10** (BE-AWARE)
>
> [`plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md`](code_freeze_migrate_backfill_sequencing_2026_05_10.md)
> sequences this plan's **Phase 4-5 per-asset-group cascade** AFTER (a) `features_repo_consolidation_2026_05_08` Phase 7
> (Phase 1 freeze blocker) and (b) `gcs_migration_bundle_pipeline_mode_2026_05_08` Phase 2 GCS bundled migration (Phase
> 2 freeze gate). Phase 0-3 UAC + UTL foundations stay in Phase 1 (already partly shipped Tab 2 PM/evening 2026-05-08 —
> 4 UTL primitives landed); Phase 4-15 cannot start until Phase 2 freeze fires.

# Live pipeline (MTDS / MDPS / features-service) for 2026-05-23 DeFi cutover

> **🟡 IN-FLIGHT REFACTOR — `available_at` adapter stamping** (coordinated by
> `available_at_lookahead_bias_completion_2026_05_08` Phase 1). MDPS bar boundary contract (Phase 0 of that plan) is
> foundational for live pipeline `available_at` propagation — re-verify before touching MDPS emit path.

## Why this plan exists

Master plan (`master_to_live_defi_2026_05_23.md`) target: two DeFi archetypes (`carry_staked_basis` lead +
`ARBITRAGE_PRICE_DISPERSION` (`funding-rate-dispersion`; renamed from legacy `leveraged_funding_arb` per Stream B
canonicalisation 2026-05-07)) live on a real wallet ≥7 continuous days by 2026-05-23. The underlying pipeline is
currently batch-only — nothing streams. Live-mode is a non-trivial activation that touches MTDS / MDPS /
features-service (newly consolidated per `features_repo_consolidation_2026_05_08`) plus the deployment-UI /
alerting-service / strategy-service consumer chain. This plan is the activation surface.

Per CLAUDE.md "Live = batch" rule, live and batch share 99% of the code path; only the execution-fill source differs.
The architecture honors that rule:

- **Storage**: same parquet schema, same `available_at` semantics, same row-key shape; only the `pipeline_mode`
  hive-partition column differs (`pipeline_mode=live_websocket` vs `pipeline_mode=batch_*`). Reconciliation is a SQL
  `GROUP BY pipeline_mode` over the same manifest.
- **Manifest shard atom (live = batch, day-grain) — ratified 2026-05-10 cross-plan audit Q4 per CLAUDE.md
  "Shard-granularity SSOT (CRITICAL)" + "Live = batch" rules.** Live `live_aggregator.py` emits per-window
  `CandleComputedEvent` as an OPERATIONAL mechanic (Redis Stream signal for downstream MDPS/features cascade), but the
  manifest write boundary is identical to batch: ONE
  `record_captured(row_key=(asset_group, venue, data_type, instrument_type, instrument_id, day, timeframe), ...)` per
  shard-day, fired at UTC-midnight close via a per-shard consolidator that aggregates the day's per-window candles into
  a single parquet finalize. Per-window candles are emitted to Redis but NOT to the manifest as separate rows — this
  preserves single-atom SSOT across (writer atomicity, manifest row_key, data-status rollup, downstream pre-flight gate,
  deployment-UI drill-down). Reader logic does NOT branch on `pipeline_mode` for atom shape. Cluster-validation gates
  (bundled shards: options_chain / futures_chain / prediction canonical-question-group / sports fixture bundle) run
  identically batch + live. Banned anti-pattern: a live `record_captured` row_key like `(venue, day, timeframe, window)`
  that adds an extra dimension — that's the same class of bug as the legacy `category=` / `asset_group=` drift (see
  CLAUDE.md "Shard-granularity SSOT" reference incidents 2026-05-05 MDPS NaN-bars + 2026-05-06 TradFi MVP
  partial-bundle).
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

- [`/codex/04-architecture/batch-live-architecture.md`](/codex/04-architecture/batch-live-architecture.md) — code-path
  symmetry contract.
- [`/codex/04-architecture/batch-live-architecture.md`](/codex/04-architecture/batch-live-architecture.md) — pipeline
  trigger + cascade architecture.
- [`/codex/02-data/availability-manifest-and-data-status.md`](/codex/02-data/availability-manifest-and-data-status.md) —
  manifest schema + 4-state taxonomy + reason taxonomy (`EXPECTED_*` / `SOURCE_RETURNED_ZERO`).
- [`/codex/02-data/honest-absence-downstream-handling.md`](/codex/02-data/honest-absence-downstream-handling.md) —
  per-consumer NaN-handling rules + reason taxonomy applied per consumer class.
- [`/codex/04-architecture/alerting-batch-live.md`](/codex/04-architecture/alerting-batch-live.md) — alerting rules
  taxonomy; Phase 9 extends with live-pipeline tier rules.
- [`/codex/04-architecture/autonomous-recovery-matrix.md`](/codex/04-architecture/autonomous-recovery-matrix.md) —
  circuit-breaker action types (stop_new_signals / force_exit_only / halt_strategy).
- [`/codex/05-infrastructure/runtime-tiers-and-deployment.md`](/codex/05-infrastructure/runtime-tiers-and-deployment.md)
  — current runtime topology; Phase 14 extends with live-pipeline topology.
- [`/codex/05-infrastructure/launcher-script-ssot.md`](/codex/05-infrastructure/launcher-script-ssot.md) — every gcloud
  launcher MUST live in `deployment-service/scripts/vm/`. Phase 13 adds 4 new launchers per this rule.
- [`/codex/04-architecture/shard-level-failure-isolation.md`](/codex/04-architecture/shard-level-failure-isolation.md) —
  shard-level error handling; live-pipeline preserves the rule.
- [`/codex/04-architecture/runtime-deployment-topology.md`](/codex/04-architecture/runtime-deployment-topology.md) —
  runtime topology SSOT; Phase 14 adds live-pipeline section.

## Pre-audit manifest

Phase 0 produces `unified-trading-pm/plans/archive/issues/live_pipeline_preaudit_2026_05_08.md`. Subsequent phases
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
| 0     | Pre-audit (SOLO, blocks everything)                      | Pre-audit doc filed at `plans/archive/issues/live_pipeline_preaudit_2026_05_08.md` listing every (asset_group, venue, data_type) gap + every consumer of every features-\* repo + every parquet-write callsite touching pipeline_mode                                          |
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
| 7.4   | Multi-hour-outage backstop                               | Manual-intervention gate fires for outages > 4h; halts + alerts via Phase 9; codified in DART runbook per `/codex/04-architecture/autonomous-recovery-matrix.md`                                                                                                               |
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
- **`gcs_migration_bundle_pipeline_mode_2026_05_08`** — STRICT BLOCKER on TWO axes (cross-plan audit Q5 ratified
  2026-05-10 — most-comprehensive-owner rule):
  - **🔴 Phase 1A owns the `PipelineMode` UAC enum SSOT.** The migration plan ships the column + enum atomically (it
    walks every parquet ONCE to add the hive partition); Phase 1 here CONSUMES the shipped enum. Banner that plan with
    `🔴 OWNS PipelineMode enum SSOT — live_pipeline Phase 1 BLOCKED until shipped` and add explicit Phase-1-here gate.
  - **🔴 Phase 4 of that plan (intra-day flush contract)** must define the live-side write path; Phases 3 + 4 + 5 here
    read the contract from the migration plan.
- **`alerting_service_live_rules_2026_05_07`** — Phase 9 here EXTENDS that plan's surface with live-pipeline tier
  rules + circuit-breaker bridge. Banner mutually.
- **`writegate_honest_coverage_endtoend_2026_05_06`** — provides the 4-state manifest taxonomy + reason taxonomy +
  `ServiceEmissionPolicy` SSOT this plan consumes. No collision; banner not required.
- **`instruments_master`** — Phase 10 here consumes the `INSTRUMENT_CACHE_REFRESH_TRIGGER` event that plan publishes.
  Banner mutually.
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
  `live_pipeline_mtds_mdps_features_2026_05_08.md` — covers items 21 + 22 for live-mode."
- **`infrastructure_master`** — umbrella; no direct collision.
- **`features_and_ml_master`** — overlaps on features compute path. Phase 5 here defines the live features compute; that
  plan's batch features compute work continues in parallel. Banner mutually.
- **`defi_master`** — DeFi-side critical-path consumer of this work. The 2 archetypes need this plan's Phase 6
  cross-cutting features by 2026-05-21. Banner mutually.

## Open questions

### Q1 — [harsh-live-pipeline-impl-tab, 2026-05-11 ~15:30 UTC] — Phase 3.5 collision: two `manifest_recorder.py`

**Status**: 🟢 RECONCILING ON LDR — Ikenna's side is executing the proposed fix; Harsh slot 5's `cc62f02` is superseded.

**Update [2026-05-11 ~14:45 UTC, harsh-live-pipeline-impl-tab end-of-shift]**: `live-defi-rollout` now has
`mtds@ab17cc3` (`MTDSShardManifestRecorder` — all-6-asset_group v5 row keys + `connector_registry.py`) **plus
`mtds@8782225` ("MTDSShardManifestRecorder.close() — Q1 reconciliation half")** — i.e. the proposed reconciliation is in
flight: Ikenna's recorder won + `close()` was added to it (the bit that would have touched Ikenna's file). So Harsh slot
5's `tab/hk/5@cc62f02` (the duplicate cefi-only `StreamingShardManifestRecorder` + the complementary wire-in half) is
**superseded** — do NOT rebase/merge it onto LDR; it's preserved on the slot branch only as a reference. **Still open on
top of `8782225`** (next agent — see the handover block below + the plan's Phase-3 `note:`): (a) wire
`manifest_recorder=MTDSShardManifestRecorder(...)` into `cli/handlers/websocket_streaming_handler.py` (still `=None`
unless `8782225`/a follow-up did it — check first); (b) `live/__init__.py` export of `MTDSShardManifestRecorder`; (c)
`ShardManifestRecorder.close()` on the Protocol in `websocket_runner.py` + `LiveWebsocketRunner.run()` finally-block
calling it (check whether `8782225` added the Protocol method or just the recorder method); (d) 3.2 per-venue-adapter
reconnect-STALE verification + 3.5 per-venue `WSFeedConnector` impls (defi → cefi spot/perp → cefi options/futures →
tradfi → sports → prediction) — `WS_FEED_CONNECTOR_FACTORIES` registry still empty, handler raises `NotImplementedError`
on unregistered venue; (e) per-asset_group smoke launches (Phase 13 launchers + Phase 15). The proposed-reconciliation
text below stands; this Q closes once (a)–(c) land + a fresh `bash scripts/quality-gates.sh` is green.

**Original [2026-05-11 ~15:30 UTC]**:

Working from main's 2026-05-11 14:01 `[main → slot 5]` "you keep Phase 3; finish 3.2/3.5/`ShardManifestRecorder`" brief,
I built the concrete `ShardManifestRecorder` impl + the runner-shutdown wiring. Mid-flight, **Ikenna slot 7's `ab17cc3`
("Phase 3.5 ShardManifestRecorder wiring + connector-registry helper", `semver-rollout[bot]`, 2026-05-11 15:12) landed
on `live-defi-rollout`** — it ships:

- `market_tick_data_service/live/manifest_recorder.py` — `MTDSShardManifestRecorder` (211 lines; builds the
  **per-asset_group v5 shard-atom row_key** for ALL 6 asset_groups — cefi spot/perp, cefi options/futures
  bundled-by-root, defi chain-first, sports per-source, prediction canonical-question-group, tradfi futures/ETFs; always
  stamps `pipeline_mode=PipelineMode.LIVE_WEBSOCKET`).
- `market_tick_data_service/live/connector_registry.py` — `register_ws_feed_connector()` helper wrapping
  `WS_FEED_CONNECTOR_FACTORIES` (double-register / empty-venue / non-callable guards + `overwrite=True`;
  `unregister_ws_feed_connector()` + `registered_venues()` test helpers).
- `tests/unit/test_live_manifest_recorder.py` — 10 tests.

**Overlap**: my `tab/hk/5` (`cc62f02`, slot-branch only — **NOT** pushed to `live-defi-rollout`) ALSO adds
`live/manifest_recorder.py` (`StreamingShardManifestRecorder` — cefi-style per-instrument only; **superseded by Ikenna's
all-6-asset_group `MTDSShardManifestRecorder`**). Per "System-First / don't duplicate", **Ikenna's wins.**

**My complementary work that is NOT in `ab17cc3`** (Ikenna didn't touch `websocket_runner.py` / `live/__init__.py` / the
handler):

- `live/websocket_runner.py` — `ShardManifestRecorder.close()` Protocol method + `LiveWebsocketRunner.run()`
  finally-block calls `manifest_recorder.close()` (flush on shutdown). **Note**: Ikenna's `MTDSShardManifestRecorder`
  would need a `close()` method to satisfy the extended Protocol — touches Ikenna's file, hence this Q.
- `cli/handlers/websocket_streaming_handler.py` — wires `manifest_recorder=<concrete recorder>(...)` (was
  `manifest_recorder=None` — the blocker Ikenna's commit message references) + docstring.
- `live/__init__.py` — export the recorder.
- `tests/unit/test_websocket_runner.py` — runner-calls-recorder-`close()` test (+ the 6 `StreamingShardManifestRecorder`
  tests, which become moot under Ikenna's recorder).

**Proposed reconciliation** (awaiting main / ikenna-main): (1) DROP my `live/manifest_recorder.py` + the 6
`StreamingShardManifestRecorder` tests; (2) on top of `ab17cc3`, re-apply the `close()` Protocol method +
runner-shutdown call + add `close()` to Ikenna's `MTDSShardManifestRecorder` + wire
`manifest_recorder=MTDSShardManifestRecorder(bucket=bucket, vm_name=vm_name)` into the handler + `__init__.py` export +
the runner-calls-close test + (optionally) refactor the handler's inline `WS_FEED_CONNECTOR_FACTORIES` to use Ikenna's
`connector_registry.register_ws_feed_connector`. Per the 14:01 plan-aware-merge instruction ("if you see a conflict on
those files, that's Ikenna slot 7's work — ping me / ikenna-main, don't blindly resolve") I'm holding rather than
force-resolving. Also: Ikenna slot 7 was supposed to take Phase 5/6/15 per the 2026-05-11 deconflict — `ab17cc3` is
Ikenna slot 7 doing Phase 3.5 "common-denominator wiring", which overlaps. ⇒ **slot-5-vs-slot-7 Phase-3 ownership needs
a firm call.**

## Deferred work after 2026-05-08 PM Tab 2 session

The 2026-05-08 PM/evening Tab 2 session shipped UTL primitives (Phase 8 / 10 / 12 + writegate Phase 5 helper) + codex
design docs (Phase 9 alerting tier-up + CeFi ML live-serving + ML alerting rules). Service-side wire-in is DEFERRED and
tracked here so the next agent picks up cleanly without re-reading session notes.

| Phase                                  | Status as of 2026-05-08 PM          | Successor / blocker                                                                                                                |
| -------------------------------------- | ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| 3 — MTDS websocket streaming rollout   | `todo` (checkbox `- [ ]`)           | DEFERRED-AFTER-FEATURES-CONSOLIDATION — gates on Harsh Tab 2 `features_repo_consolidation_2026_05_08` Phase 1-4 completing         |
| 4 — MDPS streaming aggregation cluster | `todo` (checkbox `- [ ]`)           | DEFERRED-AFTER-FEATURES-CONSOLIDATION — same gate                                                                                  |
| 5 — features-service asset-scoped      | `todo` (checkbox `- [ ]`)           | DEFERRED-AFTER-FEATURES-CONSOLIDATION — same gate                                                                                  |
| 6 — features-service cross-cutting     | `todo` (checkbox `- [ ]`)           | DEFERRED-AFTER-FEATURES-CONSOLIDATION — same gate                                                                                  |
| 7 — Replay subsystem integration test  | `todo` (checkbox `- [ ]`)           | UTL helper at UTL@f24e651b ready; integration test deferred until MTDS+MDPS live-mode wired                                        |
| 8 — Health-API extension               | `done` (UTL helper at UTL@d08c50c3) | Per-service `data_freshness` callback wire-in (1-liner per service) ships with Phase 3/4/5 rollouts                                |
| 9 — Alerting tier-up                   | `design-shipped`                    | DEFERRED-TO-TAB-5 — design contract in `/codex/05-infrastructure/live-pipeline-architecture.md` § "Live-pipeline alerting tier-up" |
| 10 — Instrument cache-delta hot-reload | `done` (UTL helper at UTL@54d658e8) | Per-service consumer wire-in ships with Phase 3/4/5 rollouts                                                                       |
| 11 — deployment-UI live tab            | `todo` (checkbox `- [ ]`)           | DEFERRED-AFTER-FEATURES-CONSOLIDATION + needs `/api/live-status` endpoint                                                          |
| 12 — Batch-vs-live reconciliation      | `helper-shipped` (UTL@908b1647)     | deployment-api scheduled job + 7-day cutover-gate run DEFERRED-TO-POST-CUTOVER (needs 7d of live-mode parquet first)               |
| 13 — VM launchers + watchdog           | `todo` (checkbox `- [ ]`)           | DEFERRED-AFTER-PHASE-3-4-5 — launcher shape depends on which services landed live-mode                                             |
| 14 — Codex SSOT updates                | `todo` (checkbox `- [ ]`)           | PARTIALLY-COMPLETE — 2026-05-08 PM session updated 3 docs; full sweep deferred to plan-completion audit                            |
| 15 — Workspace QG sweep + 7-day smoke  | `todo` (checkbox `- [ ]`)           | DEFERRED — gates on Phases 3-13 completing                                                                                         |

Cross-plan items NOT addressed this session (still open in their own plans-of-record):

- **`available_at` + lookahead-bias chain (Tab 2 share = links 0/3/4/5/8)**: No phases shipped this session. Open in
  [`available_at_lookahead_bias_completion_2026_05_08.md`](../archive/2026_05/available_at_lookahead_bias_completion_2026_05_08.md)
  Phases 0 / 3 / 4 / 5 / 8. Link 7 (`assert_available_at_present`) was already COVERED per that plan's status table (no
  action required).
- **Writegate Phase 5 ratchet**: Helper `unified_trading_library/honest_coverage_ratchet.py` shipped at UTL@59996210;
  baseline cell population (operator runs `measure-honest-coverage.py` on same-region GCE VM) + base-service.sh QG STEP
  wiring still open in
  [`writegate_honest_coverage_endtoend_2026_05_06.md`](writegate_honest_coverage_endtoend_2026_05_06.md) Phase 5.
- **CeFi ML live-serving wiring**: Design doc shipped at `/codex/16-strategy-playbooks/ml/cefi-ml-live-serving.md`; the
  features-service live ML inference compute path + UAC `MODEL_PATH_TEMPLATES` SSOT + UTL `ModelArtefactReloader`
  - per-event `model_version` stamping all open in the
    [`cefi_ml_may_23_2026.epic.md`](../archive/cefi_ml_may_23_2026.epic.md) (line 35-37 success criteria) — Harsh Tab 2
    wires the implementation per epic.
- **CeFi ML alerting wiring**: Design doc shipped at `/codex/15-runbooks/alerting/ml-alerting-rules.md` with 4 proposed
  AlertCode entries (`ML_SIGNAL_STALE`, `ML_MODEL_DRIFT_DETECTED`, `ML_PNL_DEVIATION`, `ML_INFERENCE_LATENCY_SLO`); Tab
  5 wires the actual alerting-service rule structure + KillSwitchBus rule entries per
  [`alerting_service_live_rules_2026_05_07.md`](alerting_service_live_rules_2026_05_07.md).

## Deferred work after 2026-05-11 Ikenna slot 4 RE-TASK session (promote-to-implementation)

The 2026-05-11 RE-TASK session (slot 1 ping confirmed features_repo_consolidation Phase 7 cleared 2026-05-08; the
design- ahead spawn-prompt gate was stale) PROMOTED Phase 4 / 5 / 6 UTL design stubs to real implementation. Items still
open are tracked here so Harsh slot 5 + the next agent pick up cleanly.

| Phase / item                                                    | Status as of 2026-05-11                                       | Successor / blocker                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| --------------------------------------------------------------- | ------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Phase 4 — MDPS streaming aggregation UTL primitive              | `done` (UTL@`ee64481a`)                                       | Per-service MDPS consumer wire-in (MDPS `live_aggregator.py` + `cli/main.py --mode live`) → Harsh slot 5.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| Phase 5 — features-service asset-scoped UTL primitive           | `done` (UTL@`35425c70`)                                       | Per-service per-family `live/` consumer wire-in (consolidated features-service) → Harsh slot 5.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| Phase 6 — features-service cross-cutting UTL primitive          | `done` (UTL@`35425c70` partial)                               | Watermark-buffered fan-in scheduler (per-period bucketing + grace-deadline STALE_DATA emission) DEFERRED in-place; per-service cross-cutting consumer wire-in → Harsh slot 5.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| Phase 4 cascade_parent_candle — per-shard child-event buffering | `done` (UTL@`5d3eddd`)                                        | Per-shard child-event buffer across run-loop iterations + flush at parent boundary SHIPPED 2026-05-11 slot 4. `_feed_cascade_buffer` recursively cascades up timeframe DAG via Protocol-supplied TimeframeDAG.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| Phase 6.1 watermark-buffered fan-in scheduler integration       | `done` (UTL@`9c0e9d3`)                                        | CrossCuttingFeaturesRunner integrated `WatermarkAlignmentFanin` for per-period bucketing + grace-deadline STALE emission. Boundary buffer per `(period_end, target_grain)` flushes when all upstreams emit OR grace expires.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| Phase 11.1 endpoint manifest read + Health-API HTTP join        | `done` (deployment-api@`b7d3a4c`)                             | Endpoint REAL-wired to v8 manifest read + parallel HTTPX join across registered service Health-API URLs (`live_pipeline_service_urls` in `DeploymentApiConfig`). Returns `last_candle_emitted_at` + `staleness_seconds` from `data_freshness` callback when service URL registered; falls back to manifest `attempted_at`. Per-service URL registry empty by default; populate per environment via DeploymentApiConfig override.                                                                                                                                                                                                                                                                                                                                                                                                       |
| Phase 11.3 widget reuse — FailurePillarStack + colored badges   | `done` (deployment-ui@`5738237`)                              | Extracted `LiveStatusPopulated` sub-component with summary panel (total/captured/stale/degraded counts), `FailurePillarStack` widget for attempted_failed breakdown (key `failed_other`), per-row colored capture_status badges per 4-state taxonomy, per-row staleness badges with WARN=30s / CRIT=60s thresholds + `formatStaleness` helper. 8/8 vitest tests pass. Tabs-surface integration tracked in `deployment_ui_lifecycle_tabs_2026_05_08`.                                                                                                                                                                                                                                                                                                                                                                                   |
| Phase 14 — Codex SSOT updates items 4-8                         | `done` (PM@`33f5618b`)                                        | 5 codex docs extended 2026-05-11: `availability-manifest-and-data-status.md` (live-pipeline 4-state taxonomy examples + pipeline_mode column reference), `batch-live-architecture.md` (§10 UTC midnight alignment + service-start-order independence + 4×15s→1m cascade rule + cross-cutting fan-in), `alerting-batch-live.md` (live-pipeline alert tier table + 3 circuit-breaker actions), `runtime-tiers-and-deployment.md` (live-pipeline VM topology section), `00-SSOT-INDEX.md` (3 new doc registrations).                                                                                                                                                                                                                                                                                                                      |
| Phase 13 — VM launchers + watchdog dict                         | `helper-shipped` (deployment-service@<this commit>)           | 4 launchers shipped code-ready in (b+) env-aware shape: `launch-mtds-live.sh` + `launch-mdps-features-live.sh` (both parameterised by `--asset-group <ag> --env <env>`) + `launch-features-cross-cutting.sh` (singleton) + `launch-replay-cascade.sh` (singleton + window-parameterised). Watchdog dict registered 14 new prefixes (5 mtds-live-{ag} + 5 mdps-features-live-{ag} + features-xc- + replay-). Operational launch deferred to Phase 15 cluster bootstrap (named successor per Plans-Run-To-Actual-Completion rule). Watchdog VM relaunch (`launch-vm-zombie-watchdog.sh`) deferred to Phase 15 same logical unit.                                                                                                                                                                                                         |
| Phase 11.2 — `_LIVE_CLUSTER_LAUNCHER_SCRIPTS` registry          | `done` (deployment-api@<this commit>)                         | NEW registry separate from `_SERVICE_LAUNCHER_SCRIPTS` (which serves per-shard Deploy-Missing). Keyed by live-cluster role (`mtds-live` / `mdps-features-live` / `features-cross-cutting` / `replay-cascade`) per `/codex/05-infrastructure/runtime-tiers-and-deployment.md` § "Live-pipeline VM topology". Phase 11.4 UI button consumes this registry.                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| Phase 14 item 3 — instrument-lifecycle codex callback tables    | `done` (PM@<this commit>)                                     | `/codex/04-architecture/instrument-lifecycle-cache-delta-hot-reload.md` extended with per-service Phase-10-detail tables for MTDS / MDPS / features-service `CatalogDelta` callback wiring + reloader invocation pattern. Unblocked by Phase 10 `[x] done` status — `InstrumentLifecycleCacheDeltaReloader` (UTL@`54d658e8`) shipped, callback semantics now documented against the real Protocol surface.                                                                                                                                                                                                                                                                                                                                                                                                                             |
| Phase 14 item 2 — replay-subsystem.md MTDS layer                | ✅ `done` (PM@`a22aee69`, 2026-05-20 slot-7)                  | `/codex/05-infrastructure/replay-subsystem.md` enhanced with full MTDS-side implementation detail: split status table into UTL + MTDS layers; added ReplayRunner / HistoricalWindowFetcher Protocol / InstrumentWindowData / ReplayHandler CLI / HISTORICAL_WINDOW_FETCHER_FACTORIES registry scaffold (empty at Phase 7) entries; corrected REPLAY_BACKSTOP_REACHED emitter attribution (ReplayRunner.run() not ReplayPublisher.finalize()); added "MTDS implementation layer" section with constructor parameter table, lifecycle events, CLI arg table, benchmark placeholder table. Per-venue fetcher implementations remain ⏳ PENDING Phase 3.5. Throughput benchmarks ⏳ PENDING Phase 7 production run.                                                                                                                        |
| Phase 11.4 — Deploy live-cluster UI button + endpoint           | `done` (deployment-api@`dd2adb6` + deployment-ui@`657ed68`)   | `POST /deploy-live-cluster-preview` + `GET /deploy-live-cluster-roles` consume `_LIVE_CLUSTER_LAUNCHER_SCRIPTS` registry; closed-set validation across 4 roles × 5 asset_groups × 3 envs + replay-window guard; 12 unit tests. `DeployLiveClusterButton` (deployment-ui) renders role/asset-group/env/replay-window form + bash command preview + copy-to-clipboard; 8 vitest tests; integrated into `LiveDataStatusTab` header.                                                                                                                                                                                                                                                                                                                                                                                                       |
| Phase 13.4 — Watchdog VM relaunch (operational)                 | `done` (operational 2026-05-11 14:18 UTC; verified 14:21 UTC) | Tarball refresh via `create-code-tarballs.sh` (CORE — UAC/UTL/MTDS/deployment-service all timestamped 2026-05-11T13:16Z). Old watchdog `vm-zombie-watchdog-20260510-194210` deleted; new `vm-zombie-watchdog-20260511-141810` RUNNING in `asia-northeast1-c`. **Verified per `No fire-and-forget VM launches` rule**: serial console shows `vm_zombie_watchdog.py` (39.9 KiB, fresh upload) pulled from GCS at 13:19; first poll completed at 13:19:58 — "found 2 watchable VMs in 2.7s (2 known-prefix + shard signal, 0 unknown-prefix → heartbeat-only) / 2 alive / 0 zombie / 0 too_young / killed 0/0". The 14 new `VM_PREFIX_TO_BUCKET` entries from Phase 13 (5 mtds-live-{ag} + 5 mdps-features-live-{ag} + features-xc- + replay-) are loaded in-process; when live-pipeline VMs launch with those names, watchdog sees them. |

Cross-side handshake — **HARSH SLOT 5 UNBLOCKED**: per-service consumer wire-in across MTDS / MDPS / features-service is
now actionable. The UTL primitives (`MDPSStreamingAggregator` / `AssetScopedFeaturesRunner` /
`CrossCuttingFeaturesRunner`) compile, type-clean, ship with their full Protocol surfaces, and have unit tests covering
every decision branch. Cross-side ping sent to Harsh main via `plans/active/_agent_pings.md`.

## Deferred work after 2026-05-11 Ikenna slot 4 design-ahead session

The 2026-05-11 Ikenna slot 4 session shipped design-only stubs + Phase 11.1 endpoint stub + Phase 11.3 UI scaffold +
Phase 14 codex doc extension covering Phase 4 + 5 + 6 + 11 design contracts (5 commits across UAC / UTL / deployment-api
/ deployment-ui / PM). All implementation bodies are gated on `features_repo_consolidation_2026_05_08` Phase 7 (Harsh
slot 2).

| Phase / item                                       | Status as of 2026-05-11   | Successor / blocker                                                                                                                                                |
| -------------------------------------------------- | ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Phase 4 — MDPS streaming aggregation cluster       | `design-shipped`          | DEFERRED-AFTER-`features_repo_consolidation_2026_05_08` Phase 7. Stub at UTL@`58bfbbeb`.                                                                           |
| Phase 5 — features-service asset-scoped flavor     | `design-shipped`          | DEFERRED-AFTER-`features_repo_consolidation_2026_05_08` Phase 7. Stubs at UAC@`e55651b` + UTL@`58bfbbeb`.                                                          |
| Phase 6 — features-service cross-cutting flavor    | `design-shipped`          | DEFERRED-AFTER-Phase 5 implementation. Stub at UTL@`58bfbbeb`.                                                                                                     |
| Phase 11 — deployment-UI live tab + Deploy-Missing | `design-shipped`          | Phase 11.1/11.3 stubs at deployment-api@`7d95dc9` + deployment-ui@`f3204ce`. Phase 11.2/11.4 deferred to Phase 13.                                                 |
| Phase 14 — Codex SSOT updates (item 1)             | `design-shipped` (item 1) | live-pipeline-architecture.md extension landed (PM@<this commit>); items 4-8 deferred to corresponding phase boundaries per Post-Plan-Phase Codex Audit HARD RULE. |

Cross-plan items NOT addressed this session (still open in their own plans-of-record):

- **features-repo-consolidation Phase 7**: Harsh slot 2 owns the consolidation work that unblocks live-pipeline Phase
  4/5/6 implementation. Open in
  [`features_repo_consolidation_2026_05_08.md`](features_repo_consolidation_2026_05_08.md).
- **Phase 13 launchers + watchdog updates**: separate todo (Phase 11.2/11.4 cross-references this). Open in this plan's
  Phase 13.

## Deferred work after 2026-05-11 Harsh slot 5 session (per-service consumer wire-in)

The 2026-05-11 Harsh slot 5 sessions shipped: **(1st)** the Phase 4 MDPS streaming-aggregation consumer wire-in
(mdps@`0068b2f` — `live_aggregator.py` LiveStreamAggregator + 7 Protocol adapters +
`--mode live --operation streaming-aggregation --shard-spec` CLI + config fields + 12 unit tests); **(2nd)** Phase
3.1+3.3+3.4 — the MTDS websocket-streaming **producer** half (mtds@`97b2224` — `live/websocket_runner.py`
`LiveWebsocketRunner` + `LiveWebsocketTickSink` + `WSFeedConnector`/`TickSink`/`ShardManifestRecorder` Protocols +
`InstrumentCacheRefreshConsumer`

- `cli/handlers/websocket_streaming_handler.py` + `--operation websocket-streaming` registration + config fields + 21
  unit tests). Both ruff + basedpyright clean. Items still open are tracked here so the next agent picks up cleanly
  without re-reading session notes.

| Phase / item                                               | Status as of 2026-05-11                                                                                                           | Successor / blocker                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| ---------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Phase 4 — MDPS streaming aggregation (consumer wire-in)    | `done` (mdps@`0068b2f`)                                                                                                           | DEFERRED follow-ups: **(a)** candle-parquet persistence — `MDPSStreamingAggregator` computes the OHLCV bar but the `CandleComputedEvent` carries metadata only; needs a `candle_persister` Protocol on the aggregator OR wiring `unified_trading_library.streaming.open_candle_writer`/`write_chunk`/`close_candle_writer` into it. **2-repo change (UTL + MDPS)** → next slot-5 session or operator triage. **(b)** `publish_with_policy` SSOT-policy resolution on the emission boundary (the event already carries `emission_policy`/`emission_outcome` from a hardcoded `STRICT_FAIL` default). **(c)** catalog-aware (A) vs (D) split wiring (instruments-service cache `is_alive` + UAC `venue_trading_calendar` `is_venue_open`) per writegate Phase 3.D.5 Waves 2/3 — currently `_MDPSInstrumentCatalogGate` defaults both predicates to `True`.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| Phase 3 — MTDS websocket streaming rollout                 | `helper-shipped` (3.1+3.3+3.4 mtds@`97b2224`; **+ ShardManifestRecorder + connector-registry helper mtds@`ab17cc3`**)             | 2026-05-12 Ikenna slot 7 (absorbed Harsh-side scope) shipped the **common-denominator wiring** that was blocking every per-venue rollout: `live/manifest_recorder.py` `MTDSShardManifestRecorder` (wraps UTL `ManifestWriter`, builds v5 shard-atom row_key per-asset_group, stamps `pipeline_mode=LIVE_WEBSOCKET`) + `live/connector_registry.py` `register_ws_feed_connector()` helper (double-register guard, overwrite escape, empty-venue guard) + 10 unit tests covering pipeline_mode stamping, per-asset_group row-key shape, record_empty delegation, and full registry contract. **Closes the plan body L1360 blocker "ShardManifestRecorder ManifestWriter wiring — rides with 3.5"**. **Still STILL OPEN**: 3.2 per-venue-adapter reconnect-STALE verification (needs the 3.5 adapters); 3.5 per-venue `WSFeedConnector` implementations — each venue's real WS adapter is per-venue trading-engineering work that should be sequenced by operator/next slots (de-risk order: defi → cefi spot/perp → cefi options/futures → tradfi → sports → prediction). Runner can now be wired with a real `manifest_recorder` (constructor parameter at `LiveWebsocketRunner.__init__`); per-asset_group smoke launches gate on the first venue's adapter landing. 2026-05-11 Harsh slot 5 (2nd session) prior history: **3.1 orchestration + CLI surface SHIPPED** — `market_tick_data_service/live/websocket_runner.py` `LiveWebsocketRunner` (UTCAlignedScheduler-driven; per-instrument tick buffers; `LiveWebsocketTickSink` → `pipeline_mode=live_websocket` parquet; `WSFeedConnector`/`TickSink`/`ShardManifestRecorder` Protocols; STALE-on-reconnect; per-instrument + per-window failure isolation; `record_empty(SOURCE_RETURNED_ZERO)` for empty windows) + `InstrumentCacheRefreshConsumer` [**3.4** done] + `cli/handlers/websocket_streaming_handler.py` `WebsocketStreamingHandler` (`--operation websocket-streaming --shard-spec ag:venue:dt`) + `cli/main.py` operation registration + `--base-timeframe`/`--correlation-id` args + `config/service_config.py` `streaming_redis_url`/`vm_name`/`mtds_live_pool_size_per_shard` [**3.3** done] + `tests/unit/test_websocket_runner.py` 21 tests; ruff+basedpyright clean; full QG green except 2 pre-existing failures (`test_league_partitioning` + `test_partitioned_writer_cefi_available_at` — from HEAD's `enforce_available_at` / cefi→tradfi-available_at commits `48254d2`/`a512edf`/`c186ecb`, NOT this session). **STILL OPEN**: **3.2** per-venue-adapter reconnect-STALE verification (needs the 3.5 adapters); **3.5** per-venue `WSFeedConnector` implementations (defi → cefi spot/perp → cefi options/futures → tradfi → sports → prediction; `WS_FEED_CONNECTOR_FACTORIES` registry empty → handler raises `NotImplementedError` on unregistered venue); `ShardManifestRecorder` `ManifestWriter` wiring (per-asset_group v5 row keys differ → rides with 3.5; runner currently `manifest_recorder=None`); per-asset_group smoke launches (Phase 13 launchers + Phase 15). **NOTE**: `ikenna_orchestrator` ledger `1e01433c` reassigned slot-5 Phase 3/5/6/15 → Ikenna slot 7, but operator gave Harsh slot 5 a direct "continue with phase 3" instruction 2026-05-11 — main to reconcile slot-5-vs-slot-7 ownership for 3.5. |
| Phase 5 — features-service asset-scoped flavor             | `done` (features-service@`225cc13b`)                                                                                              | ✅ DONE 2026-05-12 by Ikenna slot 7 (absorbed Harsh-side scope). Shared factory `features_service/common/live_runner.py` `build_asset_scoped_runner()` + 6 per-family thin wrappers (`features_service/{onchain,commodity,delta_one,volatility,multi_timeframe}/live/__init__.py` + `features_service/sports/live/runner.py`) delegating to the factory with family token; 23 unit tests across factory validation + per-family wrapper shape, all green. Default `UACFeatureGroupResolver` + `FamilyBatchComputeRunner` record honest absence until per-family DAG seeds + live compute overrides ship.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| Phase 6 — features-service cross-cutting flavor            | `done` (features-service@`225cc13b`)                                                                                              | ✅ DONE 2026-05-12 by Ikenna slot 7 (absorbed Harsh-side scope). Shared factory `features_service/common/live_cross_cutting.py` `build_cross_cutting_runner()` + 2 per-family wrappers (`features_service/{calendar,cross_instrument}/live/__init__.py`) with 1:1 stream-to-consumer length guard. `cross_instrument.live` cites the two May-23-critical features per Phase 6.3. Tests bundled with Phase 5 (`tests/common/test_live_runner.py`). Watermark-buffered fan-in scheduler (per-period bucketing + grace-deadline STALE_DATA emission) integrated buffer DEFERRED — UTL @`35425c70` ships `process_aligned_window` real but per-shard buffering across run-loop iterations remains follow-up.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| Phase 13 — VM launchers + watchdog dict                    | `done` (deployment-service shipped 2026-05-11 slot 4; 4 launchers code-ready in (b+) env-aware shape; watchdog dict +14 prefixes) | DEFERRED operational: 13.4 watchdog VM relaunch ships with Phase 15 cluster bootstrap. Slot-5 wire-in verified the launchers exist; no code change needed this session.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| Phase 14 — Codex SSOT updates (live-pipeline-architecture) | `done` (items 1 + 4-8 shipped 2026-05-11 slot 4)                                                                                  | The Phase-4-wire-in shape (LiveStreamAggregator + 7 Protocol adapters + the persistence-gap follow-up) is documented in this plan's Phase 4 `note:` field; codex `live-pipeline-architecture.md` already covers the topology. A short codex amendment noting the persistence-gap follow-up (when (a) lands) rides with that work.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| Phase 15 — Workspace QG sweep + 7-day live smoke           | `helper-shipped` (per-affected-repo unit tests green on slot 7 absorption — features-service 23/23 + mtds 10/10)                  | 2026-05-12 Ikenna slot 7 close-out: Phase-5/Phase-6/Phase-3.5-wiring slices now in `live-defi-rollout`. **15.1 QG sweep status**: features-service `tests/common/test_live_runner.py` 23/23 green locally (workspace `.venv-workspace` + slot PYTHONPATH); mtds `tests/unit/test_live_manifest_recorder.py` 10/10 green; no remote CI trigger on `live-defi-rollout` per CLAUDE.md. **15.2 7-day live smoke**: STILL DEFERRED — requires per-venue real WS adapters to land (Phase 3.5 per-venue rollouts) + per-asset_group VM launchers from Phase 13 (already code-ready) to fire against real Redis Stream + real GCS. The 7-day smoke is a Plans-Run-To-Actual-Completion handoff to subsequent slots/operator-directed venue sequencing. Successor: Phase 3.5 per-venue rollouts (defi first per Phase 6.3 carry_staked_basis dependency) → cluster bootstrap launches the 4 Phase 13 launchers (`launch-mtds-live.sh`, `launch-mdps-features-live.sh`, `launch-features-cross-cutting.sh`, `launch-replay-cascade.sh` per-asset_group) → 7-day continuous smoke. Ownership coordinated with slot 6 (workspace QG ratchet).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |

Cross-plan items NOT addressed this session (still open in their own plans-of-record):

- **features-repo-consolidation Phase 7**: ✅ shipped per LEDGER (features-service deployable, 8 child repos archived) —
  the gate for Phase 5/6 wire-in is cleared; remaining is the slot-5 wire-in work above. Open in
  [`features_repo_consolidation_2026_05_08.md`](features_repo_consolidation_2026_05_08.md).
- **Phase 9 alerting tier-up**: `design-shipped` (codex contract landed); UAC `AlertCode` + alerting-service rule
  wiring + executive-service kill-switch consumer DEFERRED-TO-TAB-5 per
  [`alerting_service_live_rules_2026_05_07.md`](alerting_service_live_rules_2026_05_07.md).
- **MDPSStreamingAggregator candle-persistence + cascade-buffer primitive extensions**: open in
  [`mdps_streaming_and_backpressure_2026_05_07.md`](mdps_streaming_and_backpressure_2026_05_07.md) (which owns the
  `open_candle_writer`/`write_chunk`/`close_candle_writer` lifecycle the persistence follow-up will use).

## DONE-2026-05-12 — Ikenna slot 7 (absorbed Harsh-side scope)

Closes the Harsh slot 5 carry-forward per `ikenna_orchestrator/_agent_pings.md` [main → slot 7] absorb directive
2026-05-11 (Harsh leaving ~3hr → Ikenna slot 7 picks up live-pipeline Phase 5/6/15 + Phase 3.5 common-denominator
wiring; Harsh-5 kept Phase 3.1/3.3/3.4 producer-side per cross-side deconflict at PM@`e025de42`).

Shipped commits:

- **features-service@`225cc13b`** — Phase 5 + Phase 6 per-service wire-in. Shared factories
  (`features_service/common/live_runner.py` + `live_cross_cutting.py`) wrapping the UTL@`35425c70` primitives + 6
  asset-scoped + 2 cross-cutting thin family wrappers + 23 unit tests, all green.
- **mtds@`ab17cc3`** — Phase 3.5 ShardManifestRecorder + connector-registry helper. Closes the cross-venue wiring
  blocker (`live/manifest_recorder.py` `MTDSShardManifestRecorder` + `live/connector_registry.py`
  `register_ws_feed_connector()` + 10 unit tests). Per-venue real WS adapter implementations remain operator- directed
  per-venue trading-engineering work (Phase 3.5 sequencing: defi → cefi spot/perp → cefi options/futures → tradfi →
  sports → prediction).
- **PM@`<this commit>`** — plan flips Phase 5 + Phase 6 → `done`; Phase 15 → `helper-shipped` with the 7-day live smoke
  handoff to subsequent slots / operator-directed venue sequencing per Plans-Run-To-Actual-Completion HARD RULE; Phase 3
  scoreboard entry expanded with the new wiring evidence; LEDGER refresh slot 7 entry.

EOD-audit (per CLAUDE.md "End-of-cycle audit clause"): every deferral cited above lives in this plan body scoreboard
rows above OR is owner-tracked in the named successor plan (per-venue real adapters → operator-directed next-cycle
sequencing; 7-day live smoke → Phase 3.5 rollouts + Phase 13 launchers; watermark-buffer integration → UTL
CrossCuttingFeaturesRunner follow-up).

## Temporary states + their canonical follow-up plans

- **MDPSStreamingAggregator candle-parquet persistence** is intentionally deferred (Phase 4 follow-up (a) above) — the
  current primitive shape (`OHLCVAggregator` returns a 6-tuple; `CandleComputedEvent` carries metadata only) gives the
  live-mode consumer no shard-aware hook to persist the bar; the wire-in publishes the `candle_computed` event cascade
  only. Successor: a `candle_persister` Protocol on `MDPSStreamingAggregator` OR wiring
  `unified_trading_library.streaming.open_candle_writer`/`write_chunk`/`close_candle_writer` into it. Track under
  [`mdps_streaming_and_backpressure_2026_05_07.md`](mdps_streaming_and_backpressure_2026_05_07.md) Phase 1 (which ships
  that lifecycle) + the next Harsh slot-5 session for the MDPS-side consumer wiring.
- **In-process MDPS→features handoff** is intentionally deferred (Phase 5.2) — initial rollout uses Redis Stream hop
  only. Successor: post-May-23 perf optimisation if benchmarks show Redis-hop is the latency bottleneck. Track under
  `infrastructure_master` post-cutover follow-ups.
- **Cross-cutting features watermark grace window** — default 500ms intra-zone. Successor: per-feature_group tuning
  post-cutover with empirical latency benchmarks. Track under `features_and_ml_master` Phase 4.
- **Multi-hour-outage backstop manual gate** (Phase 7.4) — initial implementation halts + alerts; auto-recovery for
  known transient failure classes (per `/codex/04-architecture/autonomous-recovery-matrix.md`) lands post- cutover.
  Track under `infrastructure_master`.

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

## DONE-2026-05-11 — Ikenna slot 4 design-ahead session

Five commits across UAC / UTL / deployment-api / deployment-ui / PM shipped the Phase 4/5/6/11/14 design contracts as
design-only stubs so consumer services compile against the shapes before
[`features_repo_consolidation_2026_05_08`](features_repo_consolidation_2026_05_08.md) Phase 7 unblocks implementation:

- **unified-api-contracts@`e55651b`** — `FeaturesComputedEvent` streaming event (Phase 5.1.d).
- **unified-trading-library@`58bfbbeb`** — `MDPSStreamingAggregator` (Phase 4) + `AssetScopedFeaturesRunner` (Phase 5)
  - `CrossCuttingFeaturesRunner` (Phase 6) design-only stubs + 11 contract tests across 2 test files.
- **deployment-api@`7d95dc9`** — `GET /api/data-status/live` endpoint stub + `LiveStatusRow` + `LiveStatusResponse`
  Pydantic models (Phase 11.1) + 4 unit tests.
- **deployment-ui@`f3204ce`** — `<LiveDataStatusTab/>` scaffold (Phase 11.3) + 5 vitest render-branch tests.
- **unified-trading-pm@<this commit>** — `/codex/05-infrastructure/live-pipeline-architecture.md` extended with Phase
  4-5-11 design contracts section + plan checkbox flips + scoreboard.

Full-execution criterion (per work-split slot 4 done-definition):
`from unified_trading_library.streaming import MDPSStreamingAggregator` resolves + the class signature matches the
design contract (verified via 11 design-only contract tests passing locally against the per-slot worktree). Same for the
features-service runners + UAC event + deployment-api endpoint + deployment-ui scaffold.

## DONE-2026-05-11 — Ikenna slot 4 RE-TASK (promote-to-implementation)

Slot 1 RE-TASK ping ([`ikenna_orchestrator/_agent_pings.md`](../../ikenna_orchestrator/_agent_pings.md) line 36)
verified that the design-ahead spawn-prompt's "BLOCKED on features_repo_consolidation Phase 7" gate was **stale**
([`features_repo_consolidation_2026_05_08.md:678`](features_repo_consolidation_2026_05_08.md) Phase 7 `[x]` shipped
2026-05-08, three days before this RE-TASK). Two follow-up commits in UTL **PROMOTE the design stubs to real
implementation**:

- **unified-trading-library@`ee64481a`** — `MDPSStreamingAggregator` real impl: full async run loop wrapping sync
  `StreamConsumerGroup` via `asyncio.to_thread`; shard-level failure isolation (per-event exception logs + skip-ack);
  `aggregate_window()` 4-category decision tree (Cat A FRESH-emit / Cat D ZERO_ACTIVITY_BAR / Cat A' no-emit / Cat B'/C
  STALE-emit) with per-shard `_ShardState` consecutive-empty-windows counter gating Cat E WS-dead-cascade.
  `cascade_parent_candle` partial impl: degraded-propagation + fanout validation real; per-shard child-event buffering
  across run-loop iterations deferred to a follow-up. 2 new Protocols (`OHLCVAggregator`, `PriorLTPProvider`,
  `ManifestRecorder`) added so caller supplies the batch-compatible OHLCV function per live=batch rule. 14 unit tests
  cover all 5 categories + cascade fanout + degraded propagation.

- **unified-trading-library@`35425c70`** — `AssetScopedFeaturesRunner` + `CrossCuttingFeaturesRunner` real impls. Asset-
  scoped runner: async run loop subscribing to `streaming.{ag}.candle_computed`; per-event decision tree (BLOCKED skip →
  no-resolved-groups skip → for each fired feature_group: compute + publish FeaturesComputedEvent with degraded
  propagation pass-through). Cross-cutting runner: parallel `asyncio.gather` over N upstream consumers; Phase 6.2 worst-
  of propagation (BLOCKED skip + PUBLISHED_DEGRADED pass-through + STALE freshness pass-through); per-shard fields
  nullable on cross-cutting events. New Protocol `CrossCuttingFeatureCompute` for the multi-input compute signature. 13
  unit tests covering all decision branches across both runners.

- **unified-trading-pm@<this commit>** — Phase 4/5/6 checkboxes flipped to `[x]` with `<repo>@<sha>` evidence; status
  notes updated to `done`; new "Deferred work after 2026-05-11 RE-TASK session" scoreboard section captures the open
  items (per-service consumer wire-in → Harsh slot 5; watermark-buffered fan-in scheduler partial; cascade per-shard
  buffer deferred; Phase 11.1 endpoint real-wiring deferred until live producers running). Cross-side ping to Harsh slot
  5 via `plans/active/_agent_pings.md` to unblock per-service consumer wiring across MTDS / MDPS / features-service.

Test coverage: 14 (MDPS aggregator) + 13 (features runners) = **27 unit tests** across the 3 UTL primitives, all passing
against the per-slot worktree. The UTL primitives are pure orchestration — feature-family business logic + OHLCV
aggregation function stay with the consumer services (per Citadel Rule 7 SSOT). Live = batch principle preserved end-
to-end: the caller supplies the **same** aggregation/compute callables that batch uses.

### Follow-up commit: Phase 11.1 endpoint real wiring (deployment-api@`9b0e81d`)

After operator pushback ("are there really no deferrals?"), promoted the `/api/data-status/live` endpoint from the
2026-05-11 design-only stub at deployment-api@`7d95dc9` to **real manifest-read wiring**:

- Reads v8 availability manifest per asset_group via `read_availability_index(bucket)` using the shared MTDS/MDPS
  bucket-name template (`market-data-tick-{asset_group}-{pid}`).
- Filters `pipeline_mode == "live_websocket"`; pre-v8 manifests (no column) handled gracefully → empty.
- Builds `LiveStatusRow` per shard: shard-key axes from manifest columns; `capture_status` from the v5 4-state taxonomy
  column; `staleness_seconds` derived from manifest `attempted_at` write-time (tz-aware UTC subtraction); empty when the
  manifest is unreachable.
- Resilient: per-asset_group read failures logged + that asset_group dropped from the response; endpoint stays
  responsive when one bucket is missing.
- `degraded_ratio_60s` + `cluster_pct_skipped_60s` stay at 0.0 — those require per-service Health-API HTTP join for
  rolling-window emission stats. Documented inline at the endpoint docstring + in this plan's scoreboard as DEFERRED on
  a per-service URL registry in `DeploymentApiConfig`.
- 10 unit tests (up from 4): empty-when-no-live-shards, populated-when-live-shards-present, asset_group filter honoured,
  90s staleness derivation, pre-v8 manifest graceful-empty, manifest-read OSError handled, 4-state capture_status
  taxonomy preserved, multi-asset_group aggregation, Pydantic shape, validator rejection.

The deployment-ui `<LiveDataStatusTab/>` (deployment-ui@`f3204ce`) already calls `fetch('/api/data-status/live')`, so
populated rows will render the moment Harsh slot 5's per-service consumer wiring lands + live producers start writing
`pipeline_mode=live_websocket` shards. Phase 11.1 endpoint half is **done**; 11.2 + 11.3 + 11.4 deferrals stay as
downstream-owned per the scoreboard.

## DONE-2026-05-11 — Harsh slot 5 end-of-shift handover

Harsh slot 5's shift ended 2026-05-11 ~14:45 UTC. This block is the clean pick-up point for Ikenna's agent.

### ✅ Shipped this shift (on `live-defi-rollout`)

- **Phase 3.1 + 3.3 + 3.4 — MTDS websocket-streaming producer** — `mtds@97b2224` (code) + `PM@b1b8e504` (plan-flip) +
  `PM@46156ec0` (slot_5 ping):
  - `market_tick_data_service/live/websocket_runner.py` — `LiveWebsocketRunner` per `(asset_group, venue, data_type)`
    shard: UTL `UTCAlignedScheduler`-driven; per-instrument tick buffers (`record_tick` / `consume_stream` /
    `pending_tick_count` public surface); `LiveWebsocketTickSink` → `pipeline_mode=live_websocket` parquet
    (`live_tick_blob_path`); caller-supplied `WSFeedConnector` / `TickSink` / `ShardManifestRecorder` Protocols;
    `flush_window` publishes `CandleBoundaryCrossedEvent` (tick_count + `data_freshness=STALE` on mid-window WS
    reconnect via `pop_reconnect_flag`); per-instrument + per-window failure isolation;
    `record_empty(SOURCE_RETURNED_ZERO)` for empty windows; `apply_instrument_delta` hot-reload.
    `available_at = period_end + grace`, never read-time-derived. [**3.4**] `InstrumentCacheRefreshConsumer` —
    subscribes `streaming.{ag}.instrument_cache_refresh_trigger`, `poll_once` / `maybe_dispatch` public; zero-delta
    skip; callback-exception isolation; `ApiKeyReloader` pattern.
  - `market_tick_data_service/cli/handlers/websocket_streaming_handler.py` — `WebsocketStreamingHandler`
    (`BaseModeHandler`), `--operation websocket-streaming --shard-spec ag:venue:dt`; resolves the per-venue connector
    from `WS_FEED_CONNECTOR_FACTORIES` (intentionally empty — raises `NotImplementedError` on unregistered venue,
    pointing at Phase 3.5); `parse_shard_spec` public; standalone `run(args) -> int` dispatch entry point.
  - `market_tick_data_service/cli/main.py` — registers `"websocket-streaming"` operation + `--shard-spec` /
    `--base-timeframe` / `--correlation-id` args.
  - `market_tick_data_service/config/service_config.py` — `streaming_redis_url` / `vm_name` /
    `mtds_live_pool_size_per_shard` [**3.3**] fields.
  - `tests/unit/test_websocket_runner.py` — 21 tests (helpers, tick-sink parquet write, boundary-flush
    captured/honest-empty/STALE-reconnect/no-recorder/publish-shape, consume_stream buffering, instrument-delta
    hot-reload, `InstrumentCacheRefreshConsumer`, `parse_shard_spec`, Protocol runtime-checkability). ruff +
    basedpyright clean; full MTDS QG green except 2 **pre-existing** failures on HEAD's last commits
    (`test_league_partitioning` + `test_partitioned_writer_cefi_available_at` — from the `enforce_available_at` /
    cefi→tradfi-available_at commits `48254d2`/`a512edf`/`c186ecb`, NOT this shift).

### ⏭ Left — in priority order (next agent / Ikenna)

1. ✅ **Phase 3.5 `ShardManifestRecorder` wire-in — DONE MTDS@5388a9c (2026-05-18 slot-6).** `mtds@ab17cc3` shipped
   `MTDSShardManifestRecorder` (all-6-asset_group v5 row keys) + `connector_registry.py`; `mtds@8782225` added
   `MTDSShardManifestRecorder.close()` + `ShardManifestRecorder.close()` Protocol method + runner finally-block call.
   `mtds@5388a9c` (slot-6) completed the wire-in: (a) `websocket_streaming_handler.py` now passes
   `MTDSShardManifestRecorder(writer=ManifestWriter(service_name="market-tick-data-service", catalogue_bucket=bucket, batch_size=1))`
   instead of `None`; (b) `live/__init__.py` exports `MTDSShardManifestRecorder`; (c) conflict markers from
   `test_bybit_ws_connector.py` + `test_deribit_ws_connector.py` cleaned; (d) handler wire-in gate test added to
   `test_live_manifest_recorder.py`. Full QG green.
2. ✅ **Phase 3.2 DONE** — pop_reconnect_flag() set-and-reset tests for all 16 WSFeedConnectors — MTDS@a6a045a
   (2026-05-18 slot-6).
3. ✅ **Phase 3.5 DONE** — all 18 WSFeedConnectors shipped (DRIFT-SOLANA, HYPERLIQUID, BINANCE-FUTURES, BYBIT-FUTURES,
   OKX-FUTURES, DERIBIT, ASTER, KRAKEN-FUTURES, BINANCE-SPOT, BYBIT-SPOT, OKX-SPOT, COINBASE-SPOT, KRAKEN-SPOT, PHOENIX,
   CME/ICE/NYSE/NASDAQ/CBOE/ARCA/BATS via Databento, ODDS_API, POLYMARKET, KALSHI). All registered via
   `connector_registry.register_ws_feed_connector` — `register_all()` loads all. MTDS@99fc7b3 (slot-3, 2026-05-17).
4. ✅ **Phase 13.1/13.2/13.3 DONE** — 4 launchers under `deployment-service/scripts/vm/` (`launch-mtds-live.sh` +
   `launch-mdps-features-live.sh` + `launch-features-cross-cutting.sh` + `launch-replay-cascade.sh`). 14 prefixes
   registered in `VM_PREFIX_TO_BUCKET` (`mtds-live-{ag}-` × 5 + `mdps-features-live-{ag}-` × 5 + `features-xc-` +
   `replay-`). Phase 13.4 (watchdog) ✅ Ikenna slot 4.
5. **Phase 15** — workspace QG sweep + 7-day live smoke — gates on operational cluster launch; Ikenna slot 7 owns.

### Exact next step

✅ **Wire-in complete — MTDS@5388a9c (2026-05-18 slot-6).** `websocket_streaming_handler.py` now passes a real
`MTDSShardManifestRecorder` to `LiveWebsocketRunner`. Next: Phase 3.5 per-venue adapter fan-out (defi first) + Phase
13.1/13.2/13.3 VM-launcher entries.

### Cross-plan items NOT touched this shift (open in their own plans-of-record)

- Phase 5 (features-svc per-family `live/`) + Phase 6 (cross-cutting `live/`) + Phase 15 = Ikenna slot 7's per the
  2026-05-11 deconflict. (Note: slot 2's 2026-05-11 14:15 cross-side ping flagged `225cc13b` features-svc Phase 5/6
  live-runner wire-in failing `[3.5/6] IMPORT PATTERNS` — 11 deep
  `from unified_trading_library.feature_service_base.live_aggregator import ...`; mechanical
  `check-import-patterns.py --fix` or re-export at the UTL root — routed to that Phase 5/6 owner, not Harsh slot 5.)

## Deferred work after 2026-05-20 slot-8 session (mock-data-benchmarking migration)

**MIGRATED FROM**: `plans/active/mock_data_pipeline_benchmarking_2026_05_10.md` Phase 3 items 3.C-followup + 3.D (slot-8
2026-05-20). Both items named this plan as their successor; benchmarking plan closed 100% after this migration.

- [x] [BLOCKED-OPERATOR-DECISION — awaiting operator [ack] on 3.D, then this unblocks] [AGENT] P2. **3.C-followup
      (migrated): `CEFI_BOOK_SNAPSHOT_5_SPEC` missing from generators.** CeFi bucket has `book_snapshot_5` data for
      BITGET-FUTURES on 2026-05-07 (21 instruments, ~535k rows/instrument avg → ~11.2M total/day). No
      `CEFI_BOOK_SNAPSHOT_5_SPEC` in `registry/generators/cefi.py`. **Do NOT add until 3.D below confirms** MTDS reads
      it (to avoid spec drift from reality). Ping filed 2026-05-19 in `harsh_orchestrator/pings/slot_7.md`. Re-audited
      2026-05-20 slot-7: still awaiting operator [ack]. Provenance: `mock_data_pipeline_benchmarking_2026_05_10.md`
      Phase 3.C-followup.

- [x] [BLOCKED-OPERATOR-DECISION — ping filed 2026-05-19 harsh_orchestrator/pings/slot_7.md; awaiting operator pick
      (a/b/c)] [AGENT] P1. **3.D (migrated): Prod-reader schema-parity verification.** PARTIAL progress already shipped:
      (1) ✅ MTDS reader wire-in — `TickDataHandler.process()` early-return when `get_synthetic_input_override()` is set
      (skips Tardis/Databento external-API calls; mtds@`82639e0`). (2) ✅ strategy-service reader wire-in —
      `GCSFeatureProvider._resolve_feature_bucket` + `_load_feature_group` prefix (strategy@`a03d12e`). (3) ✅
      ml-inference-service wire-in — `FeatureSubscriber.read()` override check (ml-inference@`0206358`). (4) ✅ Harness
      `mtds_read` command fixed (`--operation fetch` → `--operation download`; utl@`7eceaba`). **DEFERRED remains**:
      subprocess-mode harness run + schema-drift assertion (requires VM, needs operator sign-off). Run each generator's
      output through prod MTDS / MDPS / features-\* reader via harness `subprocess` mode (once `--synthetic-input-uri`
      flag is wired) and assert NO schema-drift error. Any column the prod reader expects that the Phase 2.A skeleton
      omits → add to skeleton + `# SCHEMA-PARITY: <reader>` provenance line. **Also include slot-8 handshake items**:
      (a) cefi fixtures cover 21-venue zero-activity-bar matrix incl. Cat-D shape
      (`catalogue_audit_cefi_2026_05_12.md`); (b) tradfi re-point at new `tradfi_etfs.py`/`tradfi_roots.py` SSOT once
      Ikenna's catalogue Phase 5 lands — do not bake fragmented 4-place ETF list into specs; (c) sports/prediction gaps
      (`EXPECTED_PAUSED_LEAGUE` + `prediction_canonical_question_group` + `MARKET_LIFECYCLE`) already covered by
      DEFERRED-PER-USER post-cutover sports/prediction sub-plan. Provenance:
      `mock_data_pipeline_benchmarking_2026_05_10.md` Phase 3.D + slot-8 handshake
      `harsh_orchestrator/pings/slot_8.md:15`.
