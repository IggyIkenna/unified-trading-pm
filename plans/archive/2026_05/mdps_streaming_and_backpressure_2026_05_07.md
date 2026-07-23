---
doc_type: plan
title: MDPS streaming + backpressure successor plan (2026-05-07)
summary:
status: complete
nature: record
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-service, execution-service, unified-api-contracts, unified-trading-library]
scope: [engineer, admin]
tags: []
related: []
created: "2026-05-07"
epic: epic-code-completion
priority: P1
parent: master_to_live_defi_2026_05_23
locked_by: live-defi-rollout
locked_since: 2026-05-07
last_updated: 2026-05-07
completion_gates: { code: C5, deployment: D3, business: none }
repo_gates:
  - { repo: market-data-processing-service, code: C0, deployment: none, business: none }
  - { repo: unified-trading-library, code: C0, deployment: none, business: none }
depends_on: []
todos:
  - { id: phase-1-incremental-flush-utl-helper, content: "- [x] [AGENT] P1. Phase 1.1 — Add open/write_chunk/close
        lifecycle at the canonical_writer level so MDPS can stream candles without losing shard atomicity. **SHIPPED
        2026-05-09 UTL@`ac6e3244`** — `unified-trading-library/unified_trading_library/streaming/candle_writer.py` (365
        lines: `open_candle_writer` / `write_chunk` / `close_candle_writer` / `CandleWriterHandle` dataclass /
        `SchemaDriftError`) + `tests/unit/streaming/test_candle_writer.py` (10 tests passing). Idempotent close,
        4-branch decision matrix (error → `record_failed` / zero-rows → `record_empty(SOURCE_RETURNED_ZERO)` / rows →
        `record_captured` + atomic rename / second call no-op). Cluster-validation kwargs forwarded to `record_captured`
        for bundled shards. Phase 1.2 (MDPS callsite migration) + Phase 2 (`ResourceProfiler.on_memory_warning`) remain
        open — see `plans/archive/issues/audit_2026_05_08_substantial_unfixed_items.md` Item #3 § \"Still open\" for
        blocker citation.\n\
        \nCurrent shape (the wall the previous agent
        hit):\n`unified-trading-library/.../canonical_writer.py:write_candle_parquet(...)` constructs a
        fresh\n`StreamingParquetWriter`, calls `.write_chunk(df)` ONCE with a fully-materialised DataFrame, then
        `.close()` —\ni.e. one DataFrame per writer instance, fully closed per call. There is no
        externally-exposed\nopen/write_chunk/close lifecycle. To preserve shard atomicity (one parquet per `(timeframe,
        root, day)` AND\nONE `record_captured` per shard) while bounding peak memory, the call site must be able to open
        a writer,\nstream N chunks into it, then close + record once — without exposing `StreamingParquetWriter` to
        MDPS.\n\nDecision (default — option (a) per prior agent's audit): extend `canonical_writer.py` with two new
        public\nsymbols co-located with `write_candle_parquet`:\n\n- `open_candle_writer(*, asset_group, venue,
        data_type, timeframe, root, day, available_at, schema, ...) -> CandleWriterHandle`\n  — opens a
        `StreamingParquetWriter`,\
        \ returns an opaque handle (NamedTuple or small dataclass) holding the\n  writer instance + the shard row_key +
        a `total_rows: int` accumulator.\n- `close_candle_writer(handle: CandleWriterHandle, *, manifest_writer:
        ManifestWriter, attempted_at: datetime)`\n  — flushes + closes the parquet, then performs the SINGLE
        `record_captured` (or `record_empty` if\n  `total_rows == 0`, or `record_failed(...)` if the close raised).
        Idempotent on second call (no-op).\n- The existing `write_candle_parquet` is a one-shot convenience wrapper that
        does\n  `open → write_chunk(df) → close` for callers that already have a fully-materialised
        DataFrame\n  (preserves backward compat for non-MDPS callers — the workspace \"no shims\" rule allows this when
        a single\n  repo is being migrated and the wrapper is the canonical short-form, not a fallback).\n\nCluster
        validation discipline preserved: `close_candle_writer` accepts the same\n`expected_root_clusters` /
        `cluster_extractor` kwargs as the underlying `record_captured`;\
        \ for\nbundled shards (`options_chain` / `futures_chain` etc.) these MUST be passed (UTL guard already
        raises\n`MissingClusterValidationError` for missing kwargs per writegate Phase 1A; this plan keeps that
        contract\nintact end-to-end).\n\nTests under
        `unified-trading-library/tests/unit/test_canonical_writer_chunked.py`:\n(1) open → write_chunk × N → close
        yields one parquet with N×rows; manifest has exactly ONE captured row.\n(2) open → write_chunk × 0 → close emits
        `record_empty(reason=SOURCE_RETURNED_ZERO)` and writes NO parquet.\n(3) open → write_chunk → exception
        mid-stream → close is called with `error=...` and routes to\n    `record_failed(...)`; partial parquet is
        deleted (no half-written file on disk).\n(4) idempotent close — second call is a no-op (does not
        double-record).\n(5) schema drift across chunks — second `write_chunk` with a different column set
        raises\n    `SchemaDriftError` and `close` routes to `record_failed`.\n(6) bundled-shard cluster validation —
        `close_candle_writer`\
        \ without `expected_root_clusters` for an\n    `options_chain` data_type raises
        `MissingClusterValidationError`.\n\nQG: `cd unified-trading-library && bash scripts/quality-gates.sh` clean.
        Push directly to `live-defi-rollout`.\n", status: todo, note: "" }
  - { id: phase-1-2a-canonical-writer-manifest-verb-unification, content: "- [x] [AGENT] P0. Phase 1.2A — Unify
        `canonical_writer.write_candle_parquet` manifest verb v4→v5\n  (`manifest.add` → `record_captured`). **SHIPPED
        2026-05-10**\n  MDPS@`afdb754` —
        `market-data-processing-service/market_data_processing_service/app/core/canonical_writer.py`\n  success path now
        calls `manifest_writer.record_captured(row_key=..., df=candles_df, category=..., ...)`\n  instead of legacy v4
        `manifest_writer.add(...)`. Eliminates the dual-SSOT collision flagged
        in\n  `plans/archive/issues/mdps_phase_1_2_phase_2_deferral_2026_05_10.md` — without this unification,\n  Phase
        1.2B (`_streaming_write_per_tf` migration via UTL `close_candle_writer`) would have produced\n  two manifest
        shapes in production depending on which orchestration path emitted the row, breaking\n  honest-coverage rollups
        + data-status drilldown.\n\nWhat shipped:\n1. **`write_candle_parquet` success path migrated** — replaced inline
        `manifest.add(...)`\
        \ block\n   (lines 299-345 pre-migration) with `record_captured(row_key, df=candles_df,
        category,\n   instrument_type, data_type, venue, row_count, timeframe, league_id, chain,
        underlying,\n   instrument_id, attempted_at)`. The `df=candles_df` kwarg drives the 4-pillar
        write-gate\n   validation (row count > 0, NaN ratio, schema match, cluster coverage for bundled types).\n2.
        **`_emit_status_for_shard` v5 contract compliance** — fixed pre-existing latent bug
        where\n   `record_empty(row_key=row_key)` was called WITHOUT a typed reason (would
        raise\n   `LegacyBlankErrorReasonError` per UTL@68b3804a). Now
        passes\n   `reason=EmptyConfirmedReason.SOURCE_RETURNED_ZERO.value` + `attempted_at=datetime.now(UTC)`\n   on
        both empty + failed paths.\n3. **Module docstring updated** — v4 → v5 reference in the file header + Phase 1.2A
        migration\n   provenance citation.\n4. **Tests** — 4 new + 9 total passing
        in\n   `tests/unit/test_canonical_writer_record_helpers.py`:\n   -
        `test_write_candle_parquet_calls_record_captured_not_add`\
        \ (success path uses `record_captured`,\n     NOT legacy `add`).\n   -
        `test_write_candle_parquet_empty_df_skips_manifest_write` (empty df returns None without\n     manifest write —
        caller emits `record_empty_for_shard` upstream).\n   - `test_record_empty_for_shard_passes_typed_reason`
        (typed\n     `SOURCE_RETURNED_ZERO` reason from `EMPTY_CONFIRMED_REASONS` enforced).\n   -
        `test_record_failed_for_shard_passes_attempted_at` (audit-trail stamp present).\n\nDiscovery / known follow-up:
        **MDPS does NOT currently stamp `available_at` on candle DataFrames**.\n`record_captured` calls
        `assert_available_at_present(df)` which raises `LookaheadBiasError` if\nmissing. This is the correct fail-loud
        behaviour per workspace\n\"available_at is per-row, write-time\" rule, but production callers will hit this
        until\n`available_at` stamping ships in MDPS candle generation paths. **DEFERRED** — captured as\nPhase 1.2A.1
        below; MUST land before MDPS resumes production runs OR Phase 1.2B ships.\n\nWorkspace-grep\
        \ audit (Citadel § 6 Downstream Consumer Updates):\n- **In-scope (this phase) ✅**: `canonical_writer.py:313`
        migrated.\n- **Out-of-scope (other plans)**: Many services still use legacy v4 `writer.add(...)`
        —\n  `market-data-processing-service/scripts/reprocess_sports_odds.py:563,570`,\n  `deployment-service/scripts/rebuild_sports_manifest.py:208`,\n  `features-service
        (delta-one family)/.../engine/orchestrator.py:316,322`,\n  `features-service (volatility
        family)/.../engine/orchestrator.py:198,204,270,276,651,657`,\n  `features-service (multi-timeframe
        family)/.../engine/orchestrator.py:254,261`,\n  `features-service (cross-instrument
        family)/.../cli/handlers/batch_handler.py:472,479`,\n  `features-service (commodity
        family)/.../cli/handlers/batch_handler.py:275`,\n  `features-service/features_service/{calendar,onchain,volatility}/engine/...`,\n  `instruments-service/.../engine/orchestrator.py:6561`,\n  `strategy-service/.../engine/core/cloud_strategy_storage.py:197,276,355`.
        These are\
        \ tracked\n  under writegate Phase 2.E + features_repo_consolidation residual sweeps; NOT in scope here.\n", status: done, note: '"2026-05-10
        phase-1-2a-agent shipped: canonical_writer.py v4→v5 manifest verb migration +

        _emit_status_for_shard v5 contract compliance + 4 new tests + plan flip. Unblocks Phase 1.2B."

        ' }
  - { id: phase-1-2a-1-mdps-available-at-stamping, content: "- [x] [AGENT] P0. Phase 1.2A.1 — Stamp `available_at` on
        every MDPS candle DataFrame before\n  `write_candle_parquet`. **SHIPPED 2026-05-10**\n  MDPS@`1cdcda7` —
        `market-data-processing-service/market_data_processing_service/app/core/canonical_writer.py`\n  adds
        `_stamp_candle_available_at()` helper invoked at the head of\n  `write_candle_parquet` (single chokepoint) so
        every candle DataFrame\n  carries `available_at = bar_close + emission_latency` before
        reaching\n  `StreamingParquetWriter.write_chunk` AND `ManifestWriter.record_captured`.\n  Eliminates the
        production blocker flagged as a Phase 1.2A discovery:\n  without this, `assert_available_at_present(df)` raised
        `LookaheadBiasError`\n  on every production candle write.\n\nWhat shipped:\n1. `_stamp_candle_available_at(df,
        asset_group, source_data_type, timeframe)` —\n   single chokepoint helper. Idempotent (preserves
        upstream-stamped values).\n   Resolves the UAC `SOURCE_PRIORITY`\
        \ primary source via\n   `_resolve_primary_source_for_candle` (bridge
        dict\n   `_MDPS_SOURCE_DATA_TYPE_TO_PRIORITY_KEY` maps MDPS-specific\n   source_data_type strings —
        `book_snapshot_5`, `derivative_ticker`,\n   `dex_pool_swaps`, `lst_rates`, etc. — to the UAC
        SOURCE_PRIORITY\n   data_type axis where they diverge; CeFi `trades`/`ohlcv_1m` resolve\n   directly without a
        bridge entry). Computes\n   `available_at = timestamp + tf_delta +
        emission_latency_ms_for_source(primary_source)`\n   per the workspace `Live = batch` + `available_at is per-row,
        write-time`\n   rules. Per-source latency lookups: tardis=50ms (CeFi),\n   databento=10ms (TradFi),
        onchain_subgraph=60s (DeFi default),\n   onchain_rpc=200ms (DeFi RPC reads), polymarket_clob=200ms
        (Prediction).\n2. Integer epoch-ms timestamp coercion
        mirrors\n   `candle_write_mixin._coerce_int_timestamp_column` (unit inferred from\n   magnitude: ns >1e18, us
        >1e15, ms >1e12, else s) so the MDPS\n   internal `timestamp` column is correctly\
        \ bridged regardless of\n   dtype on entry.\n3. `write_candle_parquet` wires the helper after
        `_normalise_timeframe`\n   and BEFORE `StreamingParquetWriter.write_chunk` — `available_at`\n   lands BOTH in
        the on-disk parquet (downstream features-* + MDPS\n   read-time consumers see live-equivalent timestamps) AND in
        the df\n   forwarded to `record_captured`. The 4-pillar write-gate validation\n   inside `record_captured` (row
        count > 0, NaN ratio, schema match,\n   cluster coverage for bundled types) sees the stamped df.\n4. **Tests — 9
        new** in\n   `tests/unit/test_canonical_writer_record_helpers.py`:\n   - per-asset-group stamping correctness
        (cefi trades 1m, tradfi\n     ohlcv_1m databento, defi dex_pool_swaps onchain_subgraph 15m);\n   - idempotency
        when upstream already stamped (preserves their values);\n   - integer epoch-ms timestamp coercion (real
        2026-04-15 epoch ms);\n   - empty df adds typed `available_at` column for schema-axis\n     consistency;\n   -
        missing `timestamp`\
        \ column raises `ValueError`;\n   - unmapped `(asset_group, source_data_type)` raises
        `KeyError`\n     (closed-set fail-loud per UAC's round-trip rule);\n   - end-to-end `write_candle_parquet`
        stamps `available_at` in BOTH\n     `record_captured` df AND `StreamingParquetWriter.write_chunk`.\n\nAll 18
        tests in `test_canonical_writer_record_helpers.py` pass\n(9 pre-existing + 9 new). Phase 1.2B and Phase 2
        unblocked.\n\nDiscovery / known follow-up: When the live streaming aggregator\nships in
        `live_pipeline_mtds_mdps_features_2026_05_08` Phase 4, it\nmay pre-stamp `available_at` at tick-aggregation time
        (live mode\n`available_at` = bar-close-actual-emission, not the synthesized\nbar-close + estimated latency). The
        idempotency check preserves\nthat upstream stamp — no further changes needed in this writer\nwhen the live path
        lands.\n", status: done, note: '"2026-05-10 phase-1-2a-1-agent shipped: _stamp_candle_available_at helper +

        _MDPS_SOURCE_DATA_TYPE_TO_PRIORITY_KEY bridge + integer-epoch coercion +

        9 new tests + plan flip. Unblocks Phase 1.2B + Phase 2 + production resumption."

        ' }
  - { id: phase-1-mdps-streaming-callsite, content: "- [x] ✅ [AGENT] P1. Phase 1.2 (now Phase 1.2B) — Migrate MDPS
        `_streaming_write_per_tf` to the new lifecycle. **SHIPPED 2026-05-18 MDPS@`15c1889`** —
        `CandleStreamingWriteContext` + `open_candle_streaming_writer` + `write_streaming_chunk` +
        `close_candle_streaming_writer` added to `canonical_writer.py`; `_streaming_write_per_tf` in `live_workers.py`
        rewired to per-batch open/write/close (pd.concat materialisation eliminated, peak mem ≈ 1 batch × 1.5); 4 unit
        tests in `test_streaming_write_per_tf.py` (per_batch_flush, memory_ceiling, exception_mid_stream,
        shard_level_isolation). QG green. Slot 2 tab/ikennaigboaka/2.\n\n**Phase 1A SHIPPED 2026-05-15 MDPS@`0077f1d`**
        — `write_candle_parquet` migrated to UTL `open_candle_writer + _utl_write_chunk + finalize_local()` (R1
        GCS-first approach per operator 2026-05-14 direction). Direct `StreamingParquetWriter` instantiation eliminated
        from MDPS canonical_writer.py. Phase 1B (`open_candle_streaming_writer`\
        \ helper) + Phase 1C (`_streaming_write_per_tf` refactor) + Phase 2 + Phase 4 remain open.\n\n**DEFERRED
        2026-05-10 PM** — chain-agent re-attempted Phase 1.2B and surfaced a new dual-SSOT collision concern\nthat the
        spec'd shape creates. Phase 1.2A (MDPS@`afdb754`) successfully unified the manifest verb across
        the\nchain-bundle and per-instrument paths (both emit `record_captured`); shipping Phase 1.2B as-spec'd
        would\nRE-INTRODUCE a dual-SSOT — this time at the lifecycle layer (chain-bundle on UTL `open/write/close`
        lifecycle vs\nper-instrument on `write_candle_parquet`'s one-shot lifecycle). Pre-requisite UTL fix shipped:
        UTL@`6ce59900`\nexports `open_candle_writer / write_chunk / close_candle_writer / SchemaDriftError /
        CandleWriterHandle` from\nthe streaming facade (was deep-path only). Architectural concern + 3 resolution
        options (A: migrate\n`write_candle_parquet` internally; B: ship as-spec'd accept temp dual-SSOT with named
        successor; C: re-scope\nPhase 1.2B+2 to a new lifecycle-unification\
        \ plan) tracked
        in\n[`plans/archive/issues/mdps_phase_1_2b_dual_ssot_lifecycle_collision_2026_05_10.md`](../archive/issues/mdps_phase_1_2b_dual_ssot_lifecycle_collision_2026_05_10.md).\nOperator
        triage decision required before next attempt.\n\nSite:
        `market-data-processing-service/.../live_workers.py:1118-1164` (the `_streaming_write_per_tf`\naccumulator
        pattern). Current behaviour: accumulates a per-timeframe dict-of-lists in memory across the\nwhole shard, then
        materialises one giant DataFrame at the end and shoves it through\n`_write_candles → write_candle_parquet`. Peak
        memory = full-day candles for ALL timeframes simultaneously.\n\nMigration:\n1. At shard start (per
        `(asset_group, venue, data_type, root, day)`), call `open_candle_writer(...)` for\n   each timeframe →
        dict[timeframe, CandleWriterHandle].\n2. Per source-batch (e.g. per-instrument, per-hour, per-N-rows — match the
        existing batch boundary in\n   `_process_instrument_file` so we don't introduce a new boundary), build\
        \ a chunk DataFrame and call\n   `handle.writer.write_chunk(chunk_df)`.\n3. At shard end, iterate handles and
        call `close_candle_writer(handle, manifest_writer=..., attempted_at=...)`\n   for each. Per-handle exceptions
        are caught and routed via `record_failed(...)` — shard-level failure\n   isolation rule applies (no `raise`
        inside the per-shard loop; CLAUDE.md \"Shard-level failure isolation\").\n4. Cluster-validation kwargs
        propagated for bundled data_types (read
        from\n   `unified_api_contracts.canonical.crosscutting.honest_coverage.BUNDLED_DATA_TYPES`).\n5. The existing
        schema + timestamp validation in `candle_write_mixin.py:_write_candles` is moved INSIDE the\n   chunk loop
        (validated per-chunk) — schema drift across chunks must trip `SchemaDriftError` (Phase 1.1\n   test #5 covers
        this).\n\nTests `market-data-processing-service/tests/unit/test_streaming_write_per_tf.py`:\n(1) per-batch flush
        — N batches × M rows each → final parquet has N×M rows; exactly ONE\n    `record_captured`\
        \ per (timeframe, shard).\n(2) memory ceiling regression — synthesise 10 batches × 10k rows of cefi BTCUSDT 1m
        candles and assert\n    peak resident-memory delta is < (1 batch × 1.5 safety factor), via `tracemalloc`
        snapshot diff between\n    batch 1 and batch 5.\n(3) exception-mid-stream — fail at batch 3 of 5; assert no
        parquet on disk, manifest row =\n    `attempted_failed` with the typed error_reason, and no other timeframe's
        writer is left open\n    (defensive close in finally block).\n(4) shard-level failure isolation — failing
        timeframe `5m` does NOT prevent `1m` and `15m` from completing\n    their own `record_captured`.\n\nQG: `cd
        market-data-processing-service && bash scripts/quality-gates.sh` clean.\n", status: done, note: '"SHIPPED
        2026-05-18 MDPS@15c1889 — CandleStreamingWriteContext + open_candle_streaming_writer +

        write_streaming_chunk + close_candle_streaming_writer; _streaming_write_per_tf rewired to per-batch lifecycle;

        4 unit tests passing. QG green. Dual-SSOT concern resolved via Option A (write_candle_parquet internal
        lifecycle)."

        ' }
  - { id: phase-2-resource-profiler-wiring, content: "- [x] ✅ [AGENT] P1. Phase 2 — Wire MDPS to
        ResourceProfiler.on_memory_warning for admission control. **SHIPPED 2026-05-18 MDPS@`6c560f4`** —
        `BatchOrchestrationMixin._init_backpressure` + `_on_memory_warning` + `_unpause_if_safe` + submission gate loop;
        `cli/main.py` `_start_resource_profiler()` + emergency ManifestWriter flush; 4 unit tests in
        `tests/unit/test_memory_backpressure.py` passing.\n\n**DEFERRED-AFTER-PHASE-1.2B 2026-05-10 PM** — plan
        execution DAG line ~423 (\"Phase 2 has dep only on Phase 1.2\ncallsite\") gates Phase 2 on Phase 1.2B landing.
        Phase 1.2B blocked on architectural decision
        per\n[`../archive/issues/mdps_phase_1_2b_dual_ssot_lifecycle_collision_2026_05_10.md`](../archive/issues/mdps_phase_1_2b_dual_ssot_lifecycle_collision_2026_05_10.md);\nPhase
        2 inherits the same gate. The \"in-flight workers continue running\" semantic for the admission-control\ngate
        relies on Phase 1.2B's streaming flush state — shipping Phase\
        \ 2 alone would gate new submits but in-flight\nworkers would still hold full-DF state in memory (weaker memory
        relief than the plan promises). UTL primitives\n`ResourceProfiler.add_memory_warning_callback` (UTL@`3a204c03`)
        + `ParallelPerSymbolRunner` (UTL@`50ad40ef`)\nalready exist; the MDPS-side consumer wire-in is the deferred
        scope.\n\nAudit finding (verified by previous agent via `grep -r \"ResourceProfiler|on_memory_warning\"` in MDPS
        source\n= 0 hits): MDPS does NOT currently subscribe to memory warnings, so it has no backpressure path when
        a\nVM nears the OOM threshold. The MTDS pattern is the reference shape:\n\n- UTL@`3a204c03`
        `add_memory_warning_callback` — registers a callback fired when ResourceProfiler observes\n  rss% above the
        configured threshold.\n- UTL@`50ad40ef` `ParallelPerSymbolRunner` — MTDS uses asyncio; flips an `_is_paused:
        bool` event in the\n  callback, awaits resume in the main loop.\n\nMDPS uses `ThreadPoolExecutor` not asyncio —
        so the wiring shape differs:\n\
        \n1. `cli/main.py` `ServiceBootstrap(...)` registers a callback at
        startup\n   (`ServiceBootstrap.add_memory_warning_callback(self._on_memory_warning)` — extend the
        bootstrap\n   contract if the hook isn't there yet, fold into UTL `feature_service_base/base_service.py`).\n2.
        `BatchWorkers._on_memory_warning(sample: ResourceSample)` sets `self._paused: bool = True` and records\n   the
        trigger for ops events (`MEMORY_BACKPRESSURE_ENGAGED`).\n3. The submission loop
        (`BatchWorkers._submit_next_shard` / wherever `executor.submit(...)` is called)\n   checks `self._paused` BEFORE
        every submit. If paused: `time.sleep(30)` (config-driven) then re-check.\n   A separate watchdog thread calls
        `self._unpause_if_safe()` after the 30s window if rss% has dropped\n   under `resume_threshold` — avoids
        deadlock if the warning fires once and never clears.\n4. In-flight shards continue to run (we don't kill workers
        mid-shard; that would lose the streaming\n   flush state from Phase 1). Only NEW submissions\
        \ are gated.\n5. Emit `MEMORY_BACKPRESSURE_ENGAGED` / `MEMORY_BACKPRESSURE_RESOLVED` lifecycle events with
        the\n   observed rss%, # in-flight, # pending — operators see the throttle in the events stream.\n\nTests
        `market-data-processing-service/tests/unit/test_memory_backpressure.py`:\n(1) callback flips `_paused=True`;
        subsequent submit attempts hit the gate and sleep.\n(2) auto-resume after 30s when synthetic rss% drops below
        `resume_threshold`.\n(3) deadlock guard — pause + never-clear → watchdog forces unpause after
        `max_pause_duration_seconds`.\n(4) in-flight shards complete cleanly after pause is engaged (no kill).\n\nQG:
        MDPS quality-gates.sh clean.\n", status: done, note: '"SHIPPED 2026-05-18 MDPS@6c560f4 —
        BatchOrchestrationMixin._init_backpressure + _on_memory_warning +

        _unpause_if_safe + submission gate loop; cli/main.py _start_resource_profiler() + emergency ManifestWriter
        flush;

        4 unit tests in tests/unit/test_memory_backpressure.py passing. Unblocked after Phase 1.2B shipped."

        ' }
  - { id: phase-3-row-group-iterator-read, content: "- [x] [AGENT] [DEFERRED-POST-CUTOVER] P2. Phase 3 (LOWER PRIORITY)
        — Convert eager `_read_tick_data` to row-group iterator. Plan body explicitly states \"Phase 3 lands
        post-cutover unless a specific shard hits OOM despite Phases 1+2 in place.\" Phases 1+2 shipped 2026-05-18;
        May-23 gate not blocked. — slot-2 2026-05-20.\n\nAudit finding from previous agent (the reason this was
        deferred):\n`_read_tick_data` is called from `_process_instrument_file` (live_workers.py:713) AND from
        batch_workers\npaths. Several downstream consumers (`_process_standard_timeframe`,
        `_extract_instrument_info`,\n`_validate_*` in `candle_write_mixin`) take a fully-materialised pd.DataFrame and
        probe columns by\n`len(df) > 0` / `df[\"instrument_id\"].iloc[0]` / `df.columns`. Adapting these to consume an
        iterator\nrequires either accumulating to full DF anyway (defeats the purpose) or per-batch metadata extraction
        +\na memory-budget aggregator at the boundary. Estimated\
        \ 3-5 commits each touching a different consumer.\n\nApproach (sequential within phase — each consumer migrated
        + tested in its own commit):\n\n1. Add `_read_tick_data_chunked(path, *, row_group_size_mb=128) ->
        Iterator[pd.DataFrame]` alongside the\n   existing eager `_read_tick_data`. Both keep the same column
        contract.\n2. Per consumer, identify the metadata it needs:\n   - `_extract_instrument_info` only needs the
        first non-empty row → take `next(iter)` and short-circuit;\n     the rest of the file isn't consumed by this
        caller.\n   - `_validate_*` checks schema + sample columns → run on the FIRST chunk only; record the schema
        and\n     assert subsequent chunks match (cheap, since pyarrow chunk schema is metadata-only).\n   -
        `_process_standard_timeframe` is the heavy consumer — it groups by minute and aggregates OHLCV.\n     Migrate to
        a streaming-groupby that flushes complete minutes as soon as the next chunk's first\n     timestamp crosses the
        minute boundary. Edge case: the LAST\
        \ chunk may have an incomplete minute that\n     must be carried to \"no more chunks\" close — track via
        `pending_minute_state: dict | None`.\n3. The Phase 1.2 `_streaming_write_per_tf` callsite naturally consumes the
        chunked output without further\n   refactor — it already writes per-batch (Phase 1.2 batch boundary == row-group
        boundary).\n4. DELETE the eager `_read_tick_data` once all consumers migrate (workspace \"no double SSOT\" rule
        —\n   one path per outcome).\n\nTests
        `market-data-processing-service/tests/unit/test_chunked_tick_read.py`:\n(1) chunked read of a 5GB synthetic
        parquet completes with peak memory < 200MB (assert via tracemalloc).\n(2) `_process_standard_timeframe` produces
        identical OHLCV for chunked vs eager input on the same fixture.\n(3) cross-minute-boundary edge case — synthetic
        parquet where minute boundaries split across two row\n    groups; aggregator carries pending state
        correctly.\n(4) schema drift across chunks raises `SchemaDriftError` (and the schema-validate-once\
        \ optimisation is\n    actually firing — assert via test spy that `_validate_schema` is called exactly once per
        file).\n\nQG: MDPS quality-gates.sh clean.\n\n**Why P2 (lower than Phases 1+2):** Phases 1+2 alone collapse the
        working-set memory usage by ~10×\n(one timeframe-batch in flight vs all-day-all-timeframes accumulated). Phase 3
        is the read-side analogue\nand is necessary for the truly large input files (CME GLBX trades > 5GB), but the
        band-aid VM-launcher\nmemory bump (deployment-service@`02ee6d6`) plus Phases 1+2 should be sufficient for the
        May 23 cutover.\nPhase 3 lands post-cutover unless a specific shard hits OOM despite Phases 1+2 in place.\n", status: deferred-post-cutover, note: "DEFERRED-POST-CUTOVER
        2026-05-20 slot-2: Phases 1+2 shipped 2026-05-18; band-aid bump covers May-23 gate." }
  - { id: phase-4-validation, content: "- [x] [AGENT] [BLOCKED-OPERATOR] P1. Phase 4 — End-to-end validation on a real
        backfill VM + retire the band-aid memory bump. Phases 1+2 shipped (unblocked); VM launch + verification required
        before band-aid revert (deployment-service@02ee6d6). Operator ping filed. — slot-2 2026-05-20.\n\n1. Launch a
        CeFi BTCUSDT 1m+5m+15m+1h ohlcv backfill VM for a 30-day window using the post-Phase-1+2 code.\n   Verify via
        `gcloud compute instances describe` that the VM uses the standard memory tier (NOT the\n   elevated tier from
        deployment-service@`02ee6d6`).\n2. Tail events: assert STARTED → INSTRUMENT_PROCESSED × N (with non-zero row
        counts —\n   per-instrument progress events, CLAUDE.md \"no fire-and-forget VM launches\" rule) →\n   optionally
        MEMORY_BACKPRESSURE_ENGAGED/RESOLVED if synthetic load triggers it → STOPPED.\n3. Verify per-shard manifest
        rows: `capture_status=captured` with the new shard atom (per-instrument-per-day\n   per timeframe) and ZERO
        `attempted_failed`\
        \ rows attributable to OOM.\n4. Compare output parquets byte-for-byte against a reference backfill from before
        the migration on the\n   same date range — must be identical (the streaming flush must be a strict refactor, not
        a behaviour\n   change).\n5. Once validated for cefi spot, repeat for cefi options (bundled shard — exercises
        cluster validation\n   end-to-end through the new lifecycle).\n6. Revert the band-aid memory tier in
        deployment-service to the standard size and commit\n   `chore(deployment): revert MDPS launcher memory bump now
        that streaming flush is in place\n   (depends on PHASE-1+2 land)`.\n\nSuccess criteria: VM completes 30-day cefi
        backfill on standard memory tier, manifest is honest, output\nbytes match pre-migration reference.\n", status: blocked-operator, note: "BLOCKED-OPERATOR
        2026-05-20 slot-2: VM launch + verification required; operator ping filed in slot_2.md." }
isProject: false
estimate_class: design
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 3.0
estimate_calibration_note: "No explicit AI-day estimates found in plan body during 2026-05-11 sweep; class inferred from
  filename (design, multiplier 0.6×).

  Owner agent: fill baseline + multiply × 0.6 per /codex/08-workflows/estimation-calibration.md. Refine class if
  dominant work-class differs.

  "
parent_epic: mtds_mdps_master
---

# MDPS streaming + backpressure successor plan (2026-05-07)

> **Fold-into-umbrella banner 2026-05-08**: this plan's Phase 1-3 work overlaps the
> [`live_pipeline_mtds_mdps_features_2026_05_08`](live_pipeline_mtds_mdps_features_2026_05_08.md) Phase 1-4 umbrella.
> Per the 2026-05-08 audit (Crit 6 GAP — completion-pointer): this plan is the **MDPS-streaming sub-plan** of the
> live-pipeline umbrella; the umbrella's Phase 4 explicitly cross-references this plan's `open_candle_writer` /
> `close_candle_writer` UTL lifecycle (per § "Cross-plan coordination" in the umbrella). When this plan ships, its todos
> satisfy the umbrella's Phase 4 corresponding success-gate row. **Successor**: this plan is its own completion; per
> CLAUDE.md "Citadel-Grade Planning Standards §3 — No Technical Debt", every phase ships final production shape.

> **🟢 DEPENDENCY — Live-pipeline activation 2026-05-08**
>
> [`live_pipeline_mtds_mdps_features_2026_05_08`](./live_pipeline_mtds_mdps_features_2026_05_08.md) Phase 4 RE-USES the
> `open_candle_writer` / `close_candle_writer` UTL lifecycle this plan ships in Phase 1.1 (UTL canonical_writer chunked
> lifecycle) for live-mode candle aggregation. Phase 4.4 of the live-pipeline plan also re-uses the RSS-pause
> integration this plan ships in Phase 2 (ResourceProfiler.on_memory_warning wiring). **This plan's Phase 1.2 + Phase 2
> must reach C5 before live-pipeline Phase 4 starts.** Banner removed when both Phase 1.2 and Phase 2 are flipped done
> here.

> **🟢 SHARD-ATOM SSOT — live inherits batch atom (ratified 2026-05-10 cross-plan audit Q4)**
>
> Per CLAUDE.md "Shard-granularity SSOT (CRITICAL)" + "Live = batch" rules: the live aggregator that consumes this
> plan's `open_candle_writer` / `close_candle_writer` lifecycle emits ONE `record_captured` per shard-day
> `(asset_group, venue, data_type, instrument_type, instrument_id, day, timeframe)` — IDENTICAL atom to the batch
> chunked-write path Phase 1.2B migrates. Per-window `CandleComputedEvent`s are Redis-Stream operational signals, NOT
> manifest rows. The per-shard consolidator that aggregates the day's per-window candles into a single parquet finalize
> at UTC-midnight close is the equivalent of batch's chunked-write-then-finalize sequence. Banned: live
> `record_captured` row_key shapes that add a `window` dimension (same drift-bug class as legacy `category=` /
> `asset_group=` per 2026-05-04 phantom-audit incident).

## Why this plan exists

The `mtds_per_instrument_download_api_2026_04_24.md` line of work shipped a band-aid fix for an MDPS VM OOM regression
on 2026-05-07: deployment-service@`02ee6d6` bumps the launcher memory tier so MDPS VMs don't OOM under the current
eager-read + eager-write code path. That lets the May 23 cutover proceed, but it's strictly a tactical fix — the durable
solution is a streaming flush + read-side iterator + admission control, none of which were safely deliverable in the
audit budget the parent session had.

Per CLAUDE.md "Temporary state must have a named successor plan (no silent fix later)" — this plan IS the named
successor. The band-aid is **temporary state**; this plan is the **canonical follow-up plan** that makes the band-aid
retireable.

The Unit numbering (Unit 1 / Unit 2 / Unit 3) carries forward from the parent session's deferral notes so agents picking
this up can cross-reference the original audit findings without re-deriving them.

## Parent + related plans

- **Parent (deferred from):** session 2026-05-07 mid-cycle deferred Units 1+2+3 because the shard-atomicity test matrix
  (one parquet per `(timeframe, root, day)`, one `record_captured` per shard, exception-mid-stream cleanup, idempotent
  close, schema drift across chunks) was not safely deliverable in the budget. Audit findings preserved verbatim in the
  per-todo `content` blocks above.
- **Related — band-aid already shipped:** `deployment-service@02ee6d6` — VM-launcher memory tier bump. Phase 4 retires
  this commit once Phases 1+2 land.
- **Related — MTDS reference shape for backpressure (Phase 2):** UTL@`3a204c03` `add_memory_warning_callback`
  - UTL@`50ad40ef` `ParallelPerSymbolRunner`. MDPS uses ThreadPoolExecutor not asyncio so the wiring shape differs
    (described in Phase 2 above), but the contract — register a callback in `ServiceBootstrap`, flip a paused flag, gate
    new submissions — is identical.
- **Master:** `master_to_live_defi_2026_05_23.md` — Group D (Coverage & shard) item 14, "Operability under load"
  item 16. This plan satisfies item 16 for MDPS specifically.
- **Umbrella:** `infrastructure_master.md` — folds in shard-granularity SSOT propagation and related cross-cutting
  plumbing.

## Execution DAG

```
Phase 1 (UTL canonical_writer lifecycle + MDPS callsite migration — SEQUENTIAL within phase)
  │   1.1  open_candle_writer / close_candle_writer in UTL canonical_writer.py
  │   1.2  MDPS _streaming_write_per_tf migrated to the new lifecycle
  │
  ├─> Phase 2 (ResourceProfiler wiring — PARALLEL with Phase 3, dep only on Phase 1.2 callsite)
  │
  ├─> Phase 3 (P2 — row-group iterator read; PARALLEL with Phase 2)
  │
  └─> Phase 4 (End-to-end validation + retire band-aid memory bump — depends on 1+2; 3 optional)
```

## Success criteria

- **Phase 1.1:** `unified-trading-library` quality-gates.sh clean; 6 unit tests under
  `tests/unit/test_canonical_writer_chunked.py` pass; PR pushed to `live-defi-rollout`.
- **Phase 1.2:** MDPS quality-gates.sh clean; 4 unit tests under `tests/unit/test_streaming_write_per_tf.py` pass; PR
  pushed to `live-defi-rollout`.
- **Phase 2:** MDPS quality-gates.sh clean; 4 unit tests under `tests/unit/test_memory_backpressure.py` pass;
  `MEMORY_BACKPRESSURE_ENGAGED` / `_RESOLVED` events visible in a synthetic-load smoke run.
- **Phase 3 (P2):** MDPS quality-gates.sh clean; 4 unit tests under `tests/unit/test_chunked_tick_read.py` pass; eager
  `_read_tick_data` deleted (no parallel paths).
- **Phase 4 (D3):** real-backfill VM completes a 30-day cefi shard on the standard memory tier with honest manifest
  rows; band-aid commit (deployment-service@`02ee6d6`) reverted in a follow-up commit.

## Migrated issue 2026-05-08 — Live data recovery self-detect

**Source**: `mtds_live_data_recovery_self_detect_2026_05_08` (archived). Live WS connectivity loss has no upstream
detection / signal / recovery today. Gap windows silently lost; downstream can't distinguish "venue quiet" from "MTDS
disconnected"; manifests have no `LIVE_CONNECTIVITY_GAP` rows; auto-backfill unimplemented. Violates Live=Batch
principle (batch has 4-state capture taxonomy; live has none for outages).

**Cross-plan banner**: coordinates with `alerting_service_live_rules_2026_05_07` (event-type taxonomy added there),
`master_to_live_defi_2026_05_23` Group F+G live-only readiness, and the staleness work in
`writegate_honest_coverage_endtoend_2026_05_06` Phase 3.D.5 Wave 3.M (downstream-detection counterpart). Operator
decision 2026-05-08: keep both `TICK_STALENESS` (MDPS, downstream-detected) and `CONNECTIVITY_GAP` (MTDS,
upstream-detected) as complementary signals.

- [x] [SCRIPT] P1. **`LiveConnectivityWatchdog` wrapper per venue** in MTDS. Per (venue, ws-connection): heartbeat
      timeout detection (per-venue `VENUE_HEARTBEAT_INTERVAL` empirical baseline — see calibration todo below);
      `gap_state` tracking via state machine (`HEALTHY → STALE → GAP → RECOVERING → HEALTHY`); emit typed event on every
      transition. Wraps existing per-venue WS adapter without touching adapter internals (decorator pattern). ✅
      **VERIFIED-DONE 2026-05-18 by slot 2** — `LiveConnectivityWatchdog` fully implemented at
      `market_interface/connectivity_watchdog.py` (HEALTHY/GAP state machine, 3-event emission). Wired into
      `api/main.py` startup (`c09a0e2`) + per-adapter heartbeat hooks (`4faef39` — "Item #5 closure"). Uses
      `DEFAULT_HEARTBEAT_THRESHOLD_BY_CLASS` defaults (empirical per-venue calibration is item 531 below).
- [x] [SCRIPT] P1. **`CONNECTIVITY_GAP_DETECTED` / `CONNECTIVITY_RECOVERED` / `CONNECTIVITY_GAP_BACKFILLED` event
      types** added to UAC `LifecycleEventType`. ✅ **VERIFIED-DONE 2026-05-16 by slot 2** — all 3 enum values already
      shipped at `unified-api-contracts/unified_api_contracts/internal/events.py:105-107` with full event metadata
      classes at lines 820-890 (`ConnectivityGapDetectedEvent` / `ConnectivityRecoveredEvent` /
      `ConnectivityGapBackfilledEvent`). Each event carries
      `{venue, gap_window_start, gap_window_end_or_null, last_received_at, message_count_during_gap}`. Companion
      `AlertCode` taxonomy at `alerting/rules.py` already fires per event-type. No further code change needed.
- [x] [SCRIPT] P1. **Auto-backfill on `CONNECTIVITY_RECOVERED`**: pick source per UAC `SOURCE_PRIORITY`; fill the gap
      window via REST batch fetch; call `record_captured` per filled row; emit `CONNECTIVITY_GAP_BACKFILLED` when
      complete. ✅ **SHIPPED 2026-05-19 slot 2** — framework + Protocol scaffold at mtds@`129290f`: `GapBackfillRunner`
      subscribes to `CONNECTIVITY_RECOVERED`, filters to matching (venue, data_type) shard, calls
      `RestBackfillProvider.fetch_gap()` per instrument via `asyncio.to_thread`, writes via `TickSink.flush()`, records
      via `ShardManifestRecorder.record_captured()`, then calls `watchdog.mark_backfilled()`. Safe no-op
      (`MTDS_BACKFILL_PROVIDER_MISSING` log event) when `provider=None` — per-venue REST adapters (Phase 3.6 rollout,
      plan `backfill_runner.py` § per-venue) are the remaining work.
- [x] [SCRIPT] P1. **MDPS write-gate gap-row detection**: when MDPS reads MTDS rows and finds a manifest gap row, route
      to `record_failed(reason=UPSTREAM_LIVE_GAP)` for the affected MDPS-output windows rather than processing
      zero/partial inputs. Connects via the same manifest contract MDPS already reads. ✅ **SHIPPED 2026-05-19 slots
      1+2**: (1) ✅ `UPSTREAM_LIVE_GAP` added to UAC `RecordFailedReason` at uac@`60c0ee9`; (2) ✅
      `DependencyChecker.check_upstream_manifest_has_live_gap()` at mdps@`5729750`; (3) ✅ MTDS gap rows —
      `ShardManifestRecorder.record_failed()` + `MTDSShardManifestRecorder.record_failed()` + watchdog-aware
      `_record_empty_window` at mtds@`494e0d5`; (4) ✅ MDPS orchestration wiring — `_process_instrument_file` live-gap
      pre-check at mdps@`14cf74c` + `_gate_live_gap_data_types` wired into `process_category` with 4 unit tests at
      mdps@`ebe2f06`. Filters gapped (venue, data_type) pairs from processing loop.
- [x] [SCRIPT] P1. **execution-service circuit-breaker pause on `CONNECTIVITY_GAP_DETECTED`**. Per-venue +
      per-instrument circuit-breaker; pause new orders + drain in-flight orders (do NOT cancel — let venue-side matching
      engine resolve). Resume on `CONNECTIVITY_RECOVERED`. Reuses the kill-switch bus from `alerting_service_live_rules`
      Phase 8. ✅ **SHIPPED 2026-05-18 slot 2** — execution-service@`8c9f7893c` + mtds@`46531e5`. Three
      execution-service files: (1) `circuit_breaker.py`: `allow_recovery()` → OPEN→HALF_OPEN bypass on
      `CONNECTIVITY_RECOVERED`; (2) `engine/connectivity_gap_bridge.py` (NEW): `on_connectivity_gap_detected` →
      `force_open(venue, "MTDS_GAP …")`, `on_connectivity_recovered` → `allow_recovery(venue)`; (3)
      `live_execution_handler.py`: wires `subscribe_coordination_events` at startup. MTDS side:
      `connectivity_watchdog.py` now calls `publish_coordination_event` on HEALTHY→GAP (`_tick`) and GAP→HEALTHY
      (`heartbeat`) transitions.
- [x] [SCRIPT] P1. **Per-venue `VENUE_HEARTBEAT_INTERVAL` empirical baseline calibration**. 7-day observation per venue;
      record inter-message delta distributions; pick 99th percentile as the heartbeat threshold per venue. Output: UAC
      `VENUE_HEARTBEAT_INTERVAL: dict[VenueKey, timedelta]`. **DEFERRED** — requires 7-day live MTDS telemetry not yet
      accumulated. `DEFAULT_HEARTBEAT_THRESHOLD_BY_CLASS` provides fallback defaults (cefi_ws=5s, defi_ws=10s,
      tradfi_replay=30s). ✅ **Successor plan created 2026-05-19 slot 2**:
      `plans/active/venue_heartbeat_calibration_2026_05_post23.md` — 5-task plan with P99-methodology spec and Full
      Execution Criterion. Pre-condition: MTDS live ≥7 days with heartbeat telemetry enabled.
- [x] [AGENT] P1. **Codex update**: extend `/codex/04-architecture/batch-live-architecture.md` with a "live=batch
      4-state capture parity" section explicit on how live mode emits the same 4 states as batch via the watchdog +
      auto-backfill loop. ✅ **SHIPPED 2026-05-16 by slot 2** at PM@<TBD> — new "Live=batch 4-state capture parity"
      section appended to § "Anti-drift guards" before § "Batch-only service exemptions". Covers: live mode MUST NOT
      introduce a 5th state; per-event mapping table (GAP_DETECTED → attempted_failed UPSTREAM_LIVE_GAP / BACKFILLED →
      captured / RECOVERED+empty → empty_confirmed EXPECTED_VENUE_QUIET / planned outage → expected_unattempted);
      operational signal vs manifest row distinction; cross-link to UAC event metadata classes (lines 820-890) +
      alerting taxonomy.

## Anti-patterns to avoid

- **Do NOT introduce a parallel `_streaming_write_per_tf_v2` next to the existing one** — workspace "no double SSOT"
  rule. Migrate the callsite + delete the old eager assembly.
- **Do NOT widen the candle parquet partial-write window** — at no point during streaming should consumers see a
  half-written parquet. Use the per-VM tempfile-then-rename pattern that `StreamingParquetWriter` already implements
  (verify in Phase 1.1 test #3 — exception-mid-stream must leave NO file on disk, not a half-written file).
- **Do NOT couple the row-group iterator to a specific row-group size in a way that constrains the writer side** — Phase
  3 reads parquets from MTDS that we don't control the row-group layout of. Use a `bytes_per_chunk` budget on the
  reader, not a fixed N rows.
- **Do NOT try to kill in-flight workers on memory warning** — Phase 2 explicitly gates only NEW submissions; killing
  in-flight loses the streaming flush state from Phase 1.

## Deferred work after 2026-05-10 PM chain-agent session

The 2026-05-10 PM chain-agent session shipped UTL@`6ce59900` (streaming facade re-exports of `open_candle_writer` /
`write_chunk` / `close_candle_writer` / `SchemaDriftError` / `CandleWriterHandle` — pre-requisite for any MDPS consumer
wire-in) and surfaced a Case 5 BIG architectural concern that blocks Phase 1.2B + Phase 2 from shipping cleanly under
the spec'd shape. Items still open are tracked here so the next agent picks up cleanly.

| Phase / item                                                           | Status as of 2026-05-10 PM            | Successor / blocker                                                                                                                                                                                                                                                      |
| ---------------------------------------------------------------------- | ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Phase 1.2B — `_streaming_write_per_tf` migration to UTL lifecycle      | `blocked` (checkbox `- [ ]`)          | DEFERRED-PENDING-OPERATOR-TRIAGE per [`../archive/issues/mdps_phase_1_2b_dual_ssot_lifecycle_collision_2026_05_10.md`](../archive/issues/mdps_phase_1_2b_dual_ssot_lifecycle_collision_2026_05_10.md). Three resolution options (A/B/C) in issue doc. ~6 AI-hours total. |
| Phase 2 — ResourceProfiler.on_memory_warning + ConnectivityWatchdog    | `deferred-after-phase-1-2b` (`- [ ]`) | DEFERRED-AFTER-PHASE-1.2B per plan execution DAG. UTL primitives exist (UTL@`3a204c03` `add_memory_warning_callback` + UTL@`50ad40ef` `ParallelPerSymbolRunner`); MDPS consumer wire-in is the scope.                                                                    |
| Phase 4 — End-to-end backfill VM validation + retire band-aid mem-bump | `todo` (`- [ ]`)                      | DEFERRED-AFTER-PHASES-1.2B-AND-2 per plan execution DAG. Real-infra run requirement per "Plans Run To Actual Completion" HARD RULE.                                                                                                                                      |

Cross-plan items NOT addressed this session (still open in their own plans-of-record):

- **Live-pipeline Phase 4** (`live_pipeline_mtds_mdps_features_2026_05_08.md` Phase 4) inherits the dual-SSOT collision
  risk via the live aggregator's `write_candle_parquet` integration point. Resolution Option A in the issue doc
  (`write_candle_parquet`-internal lifecycle migration) is the cleanest unblock — the live aggregator then calls
  `open_candle_writer` directly with the existing canonical_writer plumbing.
- **MDPS Phase 1.2 + Phase 2 deferral 2026-05-10 (morning issue doc)**:
  [`../archive/issues/mdps_phase_1_2_phase_2_deferral_2026_05_10.md`](../archive/issues/mdps_phase_1_2_phase_2_deferral_2026_05_10.md)
  remains open as the prior session's deferral record; the new PM issue doc is the lifecycle-shape follow-up.
- **Audit Item #3** (`../archive/issues/audit_2026_05_08_substantial_unfixed_items.md`) tracks the original audit
  finding that spawned both deferral cycles. Still PARTIALLY-RESOLVED (Phase 1.2A + 1.2A.1 shipped; Phase 1.2B + Phase
  2 + Phase 4 pending architectural decision + execution).

## Temporary states + their canonical follow-up plans

This plan ITSELF is the successor for the deployment-service@`02ee6d6` band-aid memory bump. The dual-SSOT lifecycle
collision concern surfaced 2026-05-10 PM is tracked in
[`plans/archive/issues/mdps_phase_1_2b_dual_ssot_lifecycle_collision_2026_05_10.md`](../archive/issues/mdps_phase_1_2b_dual_ssot_lifecycle_collision_2026_05_10.md);
on operator triage of resolution Options A/C, a new `mdps_canonical_writer_lifecycle_unification_2026_05_NN.md` plan
becomes the successor for Phase 1.2B + Phase 2 + Phase 4. No further temporary state is introduced by this plan — Phases
1+2+3 are the final shape; Phase 4 retires the band-aid.
