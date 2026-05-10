---
name: mdps-streaming-and-backpressure
overview:
  Successor plan covering DEFERRED MDPS Units 1+2+3 (incremental candles flush, eager → row-group iterator read,
  ResourceProfiler admission control) — band-aid VM-launcher memory bump shipped (deployment-service@02ee6d6); the
  durable streaming + backpressure path is owed.
type: code
epic: epic-code-completion
status: active

asset_group: cross-cutting
priority: P1
deadline: 2026-05-23
parent: master_to_live_defi_2026_05_23
locked_by: live-defi-rollout
locked_since: 2026-05-07
last_updated: 2026-05-07

completion_gates:
  code: C5
  deployment: D3
  business: none

repo_gates:
  - repo: market-data-processing-service
    code: C0
    deployment: none
    business: none
  - repo: unified-trading-library
    code: C0
    deployment: none
    business: none

depends_on: []

todos:
  - id: phase-1-incremental-flush-utl-helper
    content: |
      - [x] [AGENT] P1. Phase 1.1 — Add open/write_chunk/close lifecycle at the canonical_writer level so MDPS can stream candles without losing shard atomicity. **SHIPPED 2026-05-09 UTL@`ac6e3244`** — `unified-trading-library/unified_trading_library/streaming/candle_writer.py` (365 lines: `open_candle_writer` / `write_chunk` / `close_candle_writer` / `CandleWriterHandle` dataclass / `SchemaDriftError`) + `tests/unit/streaming/test_candle_writer.py` (10 tests passing). Idempotent close, 4-branch decision matrix (error → `record_failed` / zero-rows → `record_empty(SOURCE_RETURNED_ZERO)` / rows → `record_captured` + atomic rename / second call no-op). Cluster-validation kwargs forwarded to `record_captured` for bundled shards. Phase 1.2 (MDPS callsite migration) + Phase 2 (`ResourceProfiler.on_memory_warning`) remain open — see `plans/active/issues/audit_2026_05_08_substantial_unfixed_items.md` Item #3 § "Still open" for blocker citation.

      Current shape (the wall the previous agent hit):
      `unified-trading-library/.../canonical_writer.py:write_candle_parquet(...)` constructs a fresh
      `StreamingParquetWriter`, calls `.write_chunk(df)` ONCE with a fully-materialised DataFrame, then `.close()` —
      i.e. one DataFrame per writer instance, fully closed per call. There is no externally-exposed
      open/write_chunk/close lifecycle. To preserve shard atomicity (one parquet per `(timeframe, root, day)` AND
      ONE `record_captured` per shard) while bounding peak memory, the call site must be able to open a writer,
      stream N chunks into it, then close + record once — without exposing `StreamingParquetWriter` to MDPS.

      Decision (default — option (a) per prior agent's audit): extend `canonical_writer.py` with two new public
      symbols co-located with `write_candle_parquet`:

      - `open_candle_writer(*, asset_group, venue, data_type, timeframe, root, day, available_at, schema, ...) -> CandleWriterHandle`
        — opens a `StreamingParquetWriter`, returns an opaque handle (NamedTuple or small dataclass) holding the
        writer instance + the shard row_key + a `total_rows: int` accumulator.
      - `close_candle_writer(handle: CandleWriterHandle, *, manifest_writer: ManifestWriter, attempted_at: datetime)`
        — flushes + closes the parquet, then performs the SINGLE `record_captured` (or `record_empty` if
        `total_rows == 0`, or `record_failed(...)` if the close raised). Idempotent on second call (no-op).
      - The existing `write_candle_parquet` is a one-shot convenience wrapper that does
        `open → write_chunk(df) → close` for callers that already have a fully-materialised DataFrame
        (preserves backward compat for non-MDPS callers — the workspace "no shims" rule allows this when a single
        repo is being migrated and the wrapper is the canonical short-form, not a fallback).

      Cluster validation discipline preserved: `close_candle_writer` accepts the same
      `expected_root_clusters` / `cluster_extractor` kwargs as the underlying `record_captured`; for
      bundled shards (`options_chain` / `futures_chain` etc.) these MUST be passed (UTL guard already raises
      `MissingClusterValidationError` for missing kwargs per writegate Phase 1A; this plan keeps that contract
      intact end-to-end).

      Tests under `unified-trading-library/tests/unit/test_canonical_writer_chunked.py`:
      (1) open → write_chunk × N → close yields one parquet with N×rows; manifest has exactly ONE captured row.
      (2) open → write_chunk × 0 → close emits `record_empty(reason=SOURCE_RETURNED_ZERO)` and writes NO parquet.
      (3) open → write_chunk → exception mid-stream → close is called with `error=...` and routes to
          `record_failed(...)`; partial parquet is deleted (no half-written file on disk).
      (4) idempotent close — second call is a no-op (does not double-record).
      (5) schema drift across chunks — second `write_chunk` with a different column set raises
          `SchemaDriftError` and `close` routes to `record_failed`.
      (6) bundled-shard cluster validation — `close_candle_writer` without `expected_root_clusters` for an
          `options_chain` data_type raises `MissingClusterValidationError`.

      QG: `cd unified-trading-library && bash scripts/quality-gates.sh` clean. Push directly to `live-defi-rollout`.
    status: todo
    note: ""

  - id: phase-1-2a-canonical-writer-manifest-verb-unification
    content: |
      - [x] [AGENT] P0. Phase 1.2A — Unify `canonical_writer.write_candle_parquet` manifest verb v4→v5
        (`manifest.add` → `record_captured`). **SHIPPED 2026-05-10**
        MDPS@`afdb754` — `market-data-processing-service/market_data_processing_service/app/core/canonical_writer.py`
        success path now calls `manifest_writer.record_captured(row_key=..., df=candles_df, category=..., ...)`
        instead of legacy v4 `manifest_writer.add(...)`. Eliminates the dual-SSOT collision flagged in
        `plans/active/issues/mdps_phase_1_2_phase_2_deferral_2026_05_10.md` — without this unification,
        Phase 1.2B (`_streaming_write_per_tf` migration via UTL `close_candle_writer`) would have produced
        two manifest shapes in production depending on which orchestration path emitted the row, breaking
        honest-coverage rollups + data-status drilldown.

      What shipped:
      1. **`write_candle_parquet` success path migrated** — replaced inline `manifest.add(...)` block
         (lines 299-345 pre-migration) with `record_captured(row_key, df=candles_df, category,
         instrument_type, data_type, venue, row_count, timeframe, league_id, chain, underlying,
         instrument_id, attempted_at)`. The `df=candles_df` kwarg drives the 4-pillar write-gate
         validation (row count > 0, NaN ratio, schema match, cluster coverage for bundled types).
      2. **`_emit_status_for_shard` v5 contract compliance** — fixed pre-existing latent bug where
         `record_empty(row_key=row_key)` was called WITHOUT a typed reason (would raise
         `LegacyBlankErrorReasonError` per UTL@68b3804a). Now passes
         `reason=EmptyConfirmedReason.SOURCE_RETURNED_ZERO.value` + `attempted_at=datetime.now(UTC)`
         on both empty + failed paths.
      3. **Module docstring updated** — v4 → v5 reference in the file header + Phase 1.2A migration
         provenance citation.
      4. **Tests** — 4 new + 9 total passing in
         `tests/unit/test_canonical_writer_record_helpers.py`:
         - `test_write_candle_parquet_calls_record_captured_not_add` (success path uses `record_captured`,
           NOT legacy `add`).
         - `test_write_candle_parquet_empty_df_skips_manifest_write` (empty df returns None without
           manifest write — caller emits `record_empty_for_shard` upstream).
         - `test_record_empty_for_shard_passes_typed_reason` (typed
           `SOURCE_RETURNED_ZERO` reason from `EMPTY_CONFIRMED_REASONS` enforced).
         - `test_record_failed_for_shard_passes_attempted_at` (audit-trail stamp present).

      Discovery / known follow-up: **MDPS does NOT currently stamp `available_at` on candle DataFrames**.
      `record_captured` calls `assert_available_at_present(df)` which raises `LookaheadBiasError` if
      missing. This is the correct fail-loud behaviour per workspace
      "available_at is per-row, write-time" rule, but production callers will hit this until
      `available_at` stamping ships in MDPS candle generation paths. **DEFERRED** — captured as
      Phase 1.2A.1 below; MUST land before MDPS resumes production runs OR Phase 1.2B ships.

      Workspace-grep audit (Citadel § 6 Downstream Consumer Updates):
      - **In-scope (this phase) ✅**: `canonical_writer.py:313` migrated.
      - **Out-of-scope (other plans)**: Many services still use legacy v4 `writer.add(...)` —
        `market-data-processing-service/scripts/reprocess_sports_odds.py:563,570`,
        `deployment-service/scripts/rebuild_sports_manifest.py:208`,
        `features-delta-one-service/.../engine/orchestrator.py:316,322`,
        `features-volatility-service/.../engine/orchestrator.py:198,204,270,276,651,657`,
        `features-multi-timeframe-service/.../engine/orchestrator.py:254,261`,
        `features-cross-instrument-service/.../cli/handlers/batch_handler.py:472,479`,
        `features-commodity-service/.../cli/handlers/batch_handler.py:275`,
        `features-service/features_service/{calendar,onchain,volatility}/engine/...`,
        `instruments-service/.../engine/orchestrator.py:6561`,
        `strategy-service/.../engine/core/cloud_strategy_storage.py:197,276,355`. These are tracked
        under writegate Phase 2.E + features_repo_consolidation residual sweeps; NOT in scope here.
    status: done
    note: |
      "2026-05-10 phase-1-2a-agent shipped: canonical_writer.py v4→v5 manifest verb migration +
      _emit_status_for_shard v5 contract compliance + 4 new tests + plan flip. Unblocks Phase 1.2B."

  - id: phase-1-2a-1-mdps-available-at-stamping
    content: |
      - [x] [AGENT] P0. Phase 1.2A.1 — Stamp `available_at` on every MDPS candle DataFrame before
        `write_candle_parquet`. **SHIPPED 2026-05-10**
        MDPS@`1cdcda7` — `market-data-processing-service/market_data_processing_service/app/core/canonical_writer.py`
        adds `_stamp_candle_available_at()` helper invoked at the head of
        `write_candle_parquet` (single chokepoint) so every candle DataFrame
        carries `available_at = bar_close + emission_latency` before reaching
        `StreamingParquetWriter.write_chunk` AND `ManifestWriter.record_captured`.
        Eliminates the production blocker flagged as a Phase 1.2A discovery:
        without this, `assert_available_at_present(df)` raised `LookaheadBiasError`
        on every production candle write.

      What shipped:
      1. `_stamp_candle_available_at(df, asset_group, source_data_type, timeframe)` —
         single chokepoint helper. Idempotent (preserves upstream-stamped values).
         Resolves the UAC `SOURCE_PRIORITY` primary source via
         `_resolve_primary_source_for_candle` (bridge dict
         `_MDPS_SOURCE_DATA_TYPE_TO_PRIORITY_KEY` maps MDPS-specific
         source_data_type strings — `book_snapshot_5`, `derivative_ticker`,
         `dex_pool_swaps`, `lst_rates`, etc. — to the UAC SOURCE_PRIORITY
         data_type axis where they diverge; CeFi `trades`/`ohlcv_1m` resolve
         directly without a bridge entry). Computes
         `available_at = timestamp + tf_delta + emission_latency_ms_for_source(primary_source)`
         per the workspace `Live = batch` + `available_at is per-row, write-time`
         rules. Per-source latency lookups: tardis=50ms (CeFi),
         databento=10ms (TradFi), onchain_subgraph=60s (DeFi default),
         onchain_rpc=200ms (DeFi RPC reads), polymarket_clob=200ms (Prediction).
      2. Integer epoch-ms timestamp coercion mirrors
         `candle_write_mixin._coerce_int_timestamp_column` (unit inferred from
         magnitude: ns >1e18, us >1e15, ms >1e12, else s) so the MDPS
         internal `timestamp` column is correctly bridged regardless of
         dtype on entry.
      3. `write_candle_parquet` wires the helper after `_normalise_timeframe`
         and BEFORE `StreamingParquetWriter.write_chunk` — `available_at`
         lands BOTH in the on-disk parquet (downstream features-* + MDPS
         read-time consumers see live-equivalent timestamps) AND in the df
         forwarded to `record_captured`. The 4-pillar write-gate validation
         inside `record_captured` (row count > 0, NaN ratio, schema match,
         cluster coverage for bundled types) sees the stamped df.
      4. **Tests — 9 new** in
         `tests/unit/test_canonical_writer_record_helpers.py`:
         - per-asset-group stamping correctness (cefi trades 1m, tradfi
           ohlcv_1m databento, defi dex_pool_swaps onchain_subgraph 15m);
         - idempotency when upstream already stamped (preserves their values);
         - integer epoch-ms timestamp coercion (real 2026-04-15 epoch ms);
         - empty df adds typed `available_at` column for schema-axis
           consistency;
         - missing `timestamp` column raises `ValueError`;
         - unmapped `(asset_group, source_data_type)` raises `KeyError`
           (closed-set fail-loud per UAC's round-trip rule);
         - end-to-end `write_candle_parquet` stamps `available_at` in BOTH
           `record_captured` df AND `StreamingParquetWriter.write_chunk`.

      All 18 tests in `test_canonical_writer_record_helpers.py` pass
      (9 pre-existing + 9 new). Phase 1.2B and Phase 2 unblocked.

      Discovery / known follow-up: When the live streaming aggregator
      ships in `live_pipeline_mtds_mdps_features_2026_05_08` Phase 4, it
      may pre-stamp `available_at` at tick-aggregation time (live mode
      `available_at` = bar-close-actual-emission, not the synthesized
      bar-close + estimated latency). The idempotency check preserves
      that upstream stamp — no further changes needed in this writer
      when the live path lands.
    status: done
    note: |
      "2026-05-10 phase-1-2a-1-agent shipped: _stamp_candle_available_at helper +
      _MDPS_SOURCE_DATA_TYPE_TO_PRIORITY_KEY bridge + integer-epoch coercion +
      9 new tests + plan flip. Unblocks Phase 1.2B + Phase 2 + production resumption."

  - id: phase-1-mdps-streaming-callsite
    content: |
      - [ ] [AGENT] P1. Phase 1.2 (now Phase 1.2B) — Migrate MDPS `_streaming_write_per_tf` to the new lifecycle.

      **DEFERRED 2026-05-10 PM** — chain-agent re-attempted Phase 1.2B and surfaced a new dual-SSOT collision concern
      that the spec'd shape creates. Phase 1.2A (MDPS@`afdb754`) successfully unified the manifest verb across the
      chain-bundle and per-instrument paths (both emit `record_captured`); shipping Phase 1.2B as-spec'd would
      RE-INTRODUCE a dual-SSOT — this time at the lifecycle layer (chain-bundle on UTL `open/write/close` lifecycle vs
      per-instrument on `write_candle_parquet`'s one-shot lifecycle). Pre-requisite UTL fix shipped: UTL@`6ce59900`
      exports `open_candle_writer / write_chunk / close_candle_writer / SchemaDriftError / CandleWriterHandle` from
      the streaming facade (was deep-path only). Architectural concern + 3 resolution options (A: migrate
      `write_candle_parquet` internally; B: ship as-spec'd accept temp dual-SSOT with named successor; C: re-scope
      Phase 1.2B+2 to a new lifecycle-unification plan) tracked in
      [`plans/active/issues/mdps_phase_1_2b_dual_ssot_lifecycle_collision_2026_05_10.md`](issues/mdps_phase_1_2b_dual_ssot_lifecycle_collision_2026_05_10.md).
      Operator triage decision required before next attempt.

      Site: `market-data-processing-service/.../live_workers.py:1118-1164` (the `_streaming_write_per_tf`
      accumulator pattern). Current behaviour: accumulates a per-timeframe dict-of-lists in memory across the
      whole shard, then materialises one giant DataFrame at the end and shoves it through
      `_write_candles → write_candle_parquet`. Peak memory = full-day candles for ALL timeframes simultaneously.

      Migration:
      1. At shard start (per `(asset_group, venue, data_type, root, day)`), call `open_candle_writer(...)` for
         each timeframe → dict[timeframe, CandleWriterHandle].
      2. Per source-batch (e.g. per-instrument, per-hour, per-N-rows — match the existing batch boundary in
         `_process_instrument_file` so we don't introduce a new boundary), build a chunk DataFrame and call
         `handle.writer.write_chunk(chunk_df)`.
      3. At shard end, iterate handles and call `close_candle_writer(handle, manifest_writer=..., attempted_at=...)`
         for each. Per-handle exceptions are caught and routed via `record_failed(...)` — shard-level failure
         isolation rule applies (no `raise` inside the per-shard loop; CLAUDE.md "Shard-level failure isolation").
      4. Cluster-validation kwargs propagated for bundled data_types (read from
         `unified_api_contracts.canonical.crosscutting.honest_coverage.BUNDLED_DATA_TYPES`).
      5. The existing schema + timestamp validation in `candle_write_mixin.py:_write_candles` is moved INSIDE the
         chunk loop (validated per-chunk) — schema drift across chunks must trip `SchemaDriftError` (Phase 1.1
         test #5 covers this).

      Tests `market-data-processing-service/tests/unit/test_streaming_write_per_tf.py`:
      (1) per-batch flush — N batches × M rows each → final parquet has N×M rows; exactly ONE
          `record_captured` per (timeframe, shard).
      (2) memory ceiling regression — synthesise 10 batches × 10k rows of cefi BTCUSDT 1m candles and assert
          peak resident-memory delta is < (1 batch × 1.5 safety factor), via `tracemalloc` snapshot diff between
          batch 1 and batch 5.
      (3) exception-mid-stream — fail at batch 3 of 5; assert no parquet on disk, manifest row =
          `attempted_failed` with the typed error_reason, and no other timeframe's writer is left open
          (defensive close in finally block).
      (4) shard-level failure isolation — failing timeframe `5m` does NOT prevent `1m` and `15m` from completing
          their own `record_captured`.

      QG: `cd market-data-processing-service && bash scripts/quality-gates.sh` clean.
    status: blocked
    note: |
      "2026-05-10 PM chain-agent attempted; blocker = dual-SSOT lifecycle collision flagged in
      issues/mdps_phase_1_2b_dual_ssot_lifecycle_collision_2026_05_10.md (Case 5 BIG finding per Findings Triage).
      Pre-requisite UTL@`6ce59900` shipped (streaming facade re-exports). Architectural decision (Options A/B/C in
      issue doc) required before next attempt; resumes when operator picks resolution path."

  - id: phase-2-resource-profiler-wiring
    content: |
      - [ ] [AGENT] P1. Phase 2 — Wire MDPS to ResourceProfiler.on_memory_warning for admission control.

      **DEFERRED-AFTER-PHASE-1.2B 2026-05-10 PM** — plan execution DAG line ~423 ("Phase 2 has dep only on Phase 1.2
      callsite") gates Phase 2 on Phase 1.2B landing. Phase 1.2B blocked on architectural decision per
      [`issues/mdps_phase_1_2b_dual_ssot_lifecycle_collision_2026_05_10.md`](issues/mdps_phase_1_2b_dual_ssot_lifecycle_collision_2026_05_10.md);
      Phase 2 inherits the same gate. The "in-flight workers continue running" semantic for the admission-control
      gate relies on Phase 1.2B's streaming flush state — shipping Phase 2 alone would gate new submits but in-flight
      workers would still hold full-DF state in memory (weaker memory relief than the plan promises). UTL primitives
      `ResourceProfiler.add_memory_warning_callback` (UTL@`3a204c03`) + `ParallelPerSymbolRunner` (UTL@`50ad40ef`)
      already exist; the MDPS-side consumer wire-in is the deferred scope.

      Audit finding (verified by previous agent via `grep -r "ResourceProfiler|on_memory_warning"` in MDPS source
      = 0 hits): MDPS does NOT currently subscribe to memory warnings, so it has no backpressure path when a
      VM nears the OOM threshold. The MTDS pattern is the reference shape:

      - UTL@`3a204c03` `add_memory_warning_callback` — registers a callback fired when ResourceProfiler observes
        rss% above the configured threshold.
      - UTL@`50ad40ef` `ParallelPerSymbolRunner` — MTDS uses asyncio; flips an `_is_paused: bool` event in the
        callback, awaits resume in the main loop.

      MDPS uses `ThreadPoolExecutor` not asyncio — so the wiring shape differs:

      1. `cli/main.py` `ServiceBootstrap(...)` registers a callback at startup
         (`ServiceBootstrap.add_memory_warning_callback(self._on_memory_warning)` — extend the bootstrap
         contract if the hook isn't there yet, fold into UTL `feature_service_base/base_service.py`).
      2. `BatchWorkers._on_memory_warning(sample: ResourceSample)` sets `self._paused: bool = True` and records
         the trigger for ops events (`MEMORY_BACKPRESSURE_ENGAGED`).
      3. The submission loop (`BatchWorkers._submit_next_shard` / wherever `executor.submit(...)` is called)
         checks `self._paused` BEFORE every submit. If paused: `time.sleep(30)` (config-driven) then re-check.
         A separate watchdog thread calls `self._unpause_if_safe()` after the 30s window if rss% has dropped
         under `resume_threshold` — avoids deadlock if the warning fires once and never clears.
      4. In-flight shards continue to run (we don't kill workers mid-shard; that would lose the streaming
         flush state from Phase 1). Only NEW submissions are gated.
      5. Emit `MEMORY_BACKPRESSURE_ENGAGED` / `MEMORY_BACKPRESSURE_RESOLVED` lifecycle events with the
         observed rss%, # in-flight, # pending — operators see the throttle in the events stream.

      Tests `market-data-processing-service/tests/unit/test_memory_backpressure.py`:
      (1) callback flips `_paused=True`; subsequent submit attempts hit the gate and sleep.
      (2) auto-resume after 30s when synthetic rss% drops below `resume_threshold`.
      (3) deadlock guard — pause + never-clear → watchdog forces unpause after `max_pause_duration_seconds`.
      (4) in-flight shards complete cleanly after pause is engaged (no kill).

      QG: MDPS quality-gates.sh clean.
    status: deferred-after-phase-1-2b
    note: |
      "2026-05-10 PM chain-agent did not attempt; blocker = Phase 1.2B blocked on architectural decision per
      issues/mdps_phase_1_2b_dual_ssot_lifecycle_collision_2026_05_10.md; plan execution DAG gates Phase 2 on Phase 1.2B
      callsite. Resumes when Phase 1.2B unblocks."

  - id: phase-3-row-group-iterator-read
    content: |
      - [ ] [AGENT] P2. Phase 3 (LOWER PRIORITY) — Convert eager `_read_tick_data` to row-group iterator.

      Audit finding from previous agent (the reason this was deferred):
      `_read_tick_data` is called from `_process_instrument_file` (live_workers.py:713) AND from batch_workers
      paths. Several downstream consumers (`_process_standard_timeframe`, `_extract_instrument_info`,
      `_validate_*` in `candle_write_mixin`) take a fully-materialised pd.DataFrame and probe columns by
      `len(df) > 0` / `df["instrument_id"].iloc[0]` / `df.columns`. Adapting these to consume an iterator
      requires either accumulating to full DF anyway (defeats the purpose) or per-batch metadata extraction +
      a memory-budget aggregator at the boundary. Estimated 3-5 commits each touching a different consumer.

      Approach (sequential within phase — each consumer migrated + tested in its own commit):

      1. Add `_read_tick_data_chunked(path, *, row_group_size_mb=128) -> Iterator[pd.DataFrame]` alongside the
         existing eager `_read_tick_data`. Both keep the same column contract.
      2. Per consumer, identify the metadata it needs:
         - `_extract_instrument_info` only needs the first non-empty row → take `next(iter)` and short-circuit;
           the rest of the file isn't consumed by this caller.
         - `_validate_*` checks schema + sample columns → run on the FIRST chunk only; record the schema and
           assert subsequent chunks match (cheap, since pyarrow chunk schema is metadata-only).
         - `_process_standard_timeframe` is the heavy consumer — it groups by minute and aggregates OHLCV.
           Migrate to a streaming-groupby that flushes complete minutes as soon as the next chunk's first
           timestamp crosses the minute boundary. Edge case: the LAST chunk may have an incomplete minute that
           must be carried to "no more chunks" close — track via `pending_minute_state: dict | None`.
      3. The Phase 1.2 `_streaming_write_per_tf` callsite naturally consumes the chunked output without further
         refactor — it already writes per-batch (Phase 1.2 batch boundary == row-group boundary).
      4. DELETE the eager `_read_tick_data` once all consumers migrate (workspace "no double SSOT" rule —
         one path per outcome).

      Tests `market-data-processing-service/tests/unit/test_chunked_tick_read.py`:
      (1) chunked read of a 5GB synthetic parquet completes with peak memory < 200MB (assert via tracemalloc).
      (2) `_process_standard_timeframe` produces identical OHLCV for chunked vs eager input on the same fixture.
      (3) cross-minute-boundary edge case — synthetic parquet where minute boundaries split across two row
          groups; aggregator carries pending state correctly.
      (4) schema drift across chunks raises `SchemaDriftError` (and the schema-validate-once optimisation is
          actually firing — assert via test spy that `_validate_schema` is called exactly once per file).

      QG: MDPS quality-gates.sh clean.

      **Why P2 (lower than Phases 1+2):** Phases 1+2 alone collapse the working-set memory usage by ~10×
      (one timeframe-batch in flight vs all-day-all-timeframes accumulated). Phase 3 is the read-side analogue
      and is necessary for the truly large input files (CME GLBX trades > 5GB), but the band-aid VM-launcher
      memory bump (deployment-service@`02ee6d6`) plus Phases 1+2 should be sufficient for the May 23 cutover.
      Phase 3 lands post-cutover unless a specific shard hits OOM despite Phases 1+2 in place.
    status: todo
    note: ""

  - id: phase-4-validation
    content: |
      - [ ] [AGENT] P1. Phase 4 — End-to-end validation on a real backfill VM + retire the band-aid memory bump.

      1. Launch a CeFi BTCUSDT 1m+5m+15m+1h ohlcv backfill VM for a 30-day window using the post-Phase-1+2 code.
         Verify via `gcloud compute instances describe` that the VM uses the standard memory tier (NOT the
         elevated tier from deployment-service@`02ee6d6`).
      2. Tail events: assert STARTED → INSTRUMENT_PROCESSED × N (with non-zero row counts —
         per-instrument progress events, CLAUDE.md "no fire-and-forget VM launches" rule) →
         optionally MEMORY_BACKPRESSURE_ENGAGED/RESOLVED if synthetic load triggers it → STOPPED.
      3. Verify per-shard manifest rows: `capture_status=captured` with the new shard atom (per-instrument-per-day
         per timeframe) and ZERO `attempted_failed` rows attributable to OOM.
      4. Compare output parquets byte-for-byte against a reference backfill from before the migration on the
         same date range — must be identical (the streaming flush must be a strict refactor, not a behaviour
         change).
      5. Once validated for cefi spot, repeat for cefi options (bundled shard — exercises cluster validation
         end-to-end through the new lifecycle).
      6. Revert the band-aid memory tier in deployment-service to the standard size and commit
         `chore(deployment): revert MDPS launcher memory bump now that streaming flush is in place
         (depends on PHASE-1+2 land)`.

      Success criteria: VM completes 30-day cefi backfill on standard memory tier, manifest is honest, output
      bytes match pre-migration reference.
    status: todo
    note: ""

isProject: false
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
> at UTC-midnight close is the equivalent of batch's chunked-write-then-finalize sequence. Banned: live `record_captured`
> row_key shapes that add a `window` dimension (same drift-bug class as legacy `category=` / `asset_group=` per
> 2026-05-04 phantom-audit incident).

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
- **Umbrella:** `infrastructure_master_2026_05_07.md` — folds in shard-granularity SSOT propagation and related
  cross-cutting plumbing.

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

- [ ] [SCRIPT] P1. **`LiveConnectivityWatchdog` wrapper per venue** in MTDS. Per (venue, ws-connection): heartbeat
      timeout detection (per-venue `VENUE_HEARTBEAT_INTERVAL` empirical baseline — see calibration todo below);
      `gap_state` tracking via state machine (`HEALTHY → STALE → GAP → RECOVERING → HEALTHY`); emit typed event on every
      transition. Wraps existing per-venue WS adapter without touching adapter internals (decorator pattern).
- [ ] [SCRIPT] P1. **`CONNECTIVITY_GAP_DETECTED` / `CONNECTIVITY_RECOVERED` / `CONNECTIVITY_GAP_BACKFILLED` event
      types** added to UAC `LifecycleEventType` (alerting-service plan adds the alerting rule taxonomy; THIS plan adds
      the event types themselves). Each carries
      `{venue, gap_window_start, gap_window_end_or_null,     last_received_at, message_count_during_gap}`.
- [ ] [SCRIPT] P1. **Auto-backfill on `CONNECTIVITY_RECOVERED`**: pick source per UAC `SOURCE_PRIORITY`; fill the gap
      window via REST batch fetch; call `record_captured` per filled row; emit `CONNECTIVITY_GAP_BACKFILLED` when
      complete. Per CLAUDE.md "Manifest concurrency principle" — read-once + per-date freshness check + CAS write.
      Honors per-venue rate limits.
- [ ] [SCRIPT] P1. **MDPS write-gate gap-row detection**: when MDPS reads MTDS rows and finds a manifest gap row, route
      to `record_failed(reason=UPSTREAM_LIVE_GAP)` for the affected MDPS-output windows rather than processing
      zero/partial inputs. Connects via the same manifest contract MDPS already reads.
- [ ] [SCRIPT] P1. **execution-service circuit-breaker pause on `CONNECTIVITY_GAP_DETECTED`**. Per-venue +
      per-instrument circuit-breaker; pause new orders + drain in-flight orders (do NOT cancel — let venue-side matching
      engine resolve). Resume on `CONNECTIVITY_RECOVERED`. Reuses the kill-switch bus from `alerting_service_live_rules`
      Phase 8.
- [ ] [SCRIPT] P1. **Per-venue `VENUE_HEARTBEAT_INTERVAL` empirical baseline calibration**. 7-day observation per venue;
      record inter-message delta distributions; pick 99th percentile as the heartbeat threshold per venue. Output: UAC
      `VENUE_HEARTBEAT_INTERVAL: dict[VenueKey, timedelta]`.
- [ ] [AGENT] P1. **Codex update**: extend `codex/04-architecture/batch-live-architecture.md` with a "live=batch 4-state
      capture parity" section explicit on how live mode emits the same 4 states as batch via the watchdog +
      auto-backfill loop.

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

| Phase / item                                                          | Status as of 2026-05-10 PM           | Successor / blocker                                                                                                                                                                                                                              |
| --------------------------------------------------------------------- | ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Phase 1.2B — `_streaming_write_per_tf` migration to UTL lifecycle     | `blocked` (checkbox `- [ ]`)         | DEFERRED-PENDING-OPERATOR-TRIAGE per [`issues/mdps_phase_1_2b_dual_ssot_lifecycle_collision_2026_05_10.md`](issues/mdps_phase_1_2b_dual_ssot_lifecycle_collision_2026_05_10.md). Three resolution options (A/B/C) in issue doc. ~6 AI-hours total. |
| Phase 2 — ResourceProfiler.on_memory_warning + ConnectivityWatchdog   | `deferred-after-phase-1-2b` (`- [ ]`) | DEFERRED-AFTER-PHASE-1.2B per plan execution DAG. UTL primitives exist (UTL@`3a204c03` `add_memory_warning_callback` + UTL@`50ad40ef` `ParallelPerSymbolRunner`); MDPS consumer wire-in is the scope.                                              |
| Phase 4 — End-to-end backfill VM validation + retire band-aid mem-bump | `todo` (`- [ ]`)                     | DEFERRED-AFTER-PHASES-1.2B-AND-2 per plan execution DAG. Real-infra run requirement per "Plans Run To Actual Completion" HARD RULE.                                                                                                              |

Cross-plan items NOT addressed this session (still open in their own plans-of-record):

- **Live-pipeline Phase 4** (`live_pipeline_mtds_mdps_features_2026_05_08.md` Phase 4) inherits the dual-SSOT
  collision risk via the live aggregator's `write_candle_parquet` integration point. Resolution Option A in the issue
  doc (`write_candle_parquet`-internal lifecycle migration) is the cleanest unblock — the live aggregator then calls
  `open_candle_writer` directly with the existing canonical_writer plumbing.
- **MDPS Phase 1.2 + Phase 2 deferral 2026-05-10 (morning issue doc)**:
  [`issues/mdps_phase_1_2_phase_2_deferral_2026_05_10.md`](issues/mdps_phase_1_2_phase_2_deferral_2026_05_10.md)
  remains open as the prior session's deferral record; the new PM issue doc is the lifecycle-shape follow-up.
- **Audit Item #3** (`issues/audit_2026_05_08_substantial_unfixed_items.md`) tracks the original audit finding that
  spawned both deferral cycles. Still PARTIALLY-RESOLVED (Phase 1.2A + 1.2A.1 shipped; Phase 1.2B + Phase 2 + Phase 4
  pending architectural decision + execution).

## Temporary states + their canonical follow-up plans

This plan ITSELF is the successor for the deployment-service@`02ee6d6` band-aid memory bump. The dual-SSOT lifecycle
collision concern surfaced 2026-05-10 PM is tracked in
[`plans/active/issues/mdps_phase_1_2b_dual_ssot_lifecycle_collision_2026_05_10.md`](issues/mdps_phase_1_2b_dual_ssot_lifecycle_collision_2026_05_10.md);
on operator triage of resolution Options A/C, a new `mdps_canonical_writer_lifecycle_unification_2026_05_NN.md` plan
becomes the successor for Phase 1.2B + Phase 2 + Phase 4. No further temporary state is introduced by this plan —
Phases 1+2+3 are the final shape; Phase 4 retires the band-aid.
