---
title:
  "MDPS streaming primitives — spawn prompt's open/close_candle_writer contract conflicts with plan-of-record (audit
  issue #3 P0)"
created: 2026-05-09
author: agent-mdps-streaming-spawn
status: resolved-partial-2026-05-09
source:
  - plans/active/issues/audit_2026_05_08_substantial_unfixed_items.md § Item 3
  - plans/active/mdps_streaming_and_backpressure_2026_05_07.md Phase 1.1
  - plans/active/live_pipeline_mtds_mdps_features_2026_05_08.md Phase 4 + § "Coordination" (lines 425-449, 1107-1108)
  - spawn prompt 2026-05-09 (this session)
locked_by: live-defi-rollout
locked_since: 2026-05-09
---

> **RESOLUTION 2026-05-09**: Operator approved option (a) — ship per plan-of-record. Follow-up agent shipped the
> **UAC SSOT half** as a clean independent unit (UAC@`4bd84e7c` — 3 typed `LifecycleEventType` members +
> 3 Pydantic detail models + 3 typed event wrappers + 12 unit tests in
> `tests/internal/unit/test_connectivity_gap_event_taxonomy.py`). The remaining 4 deliverables (UTL `open_candle_writer`
> / `close_candle_writer`, MDPS Phase 1.2 callsite migration, MTDS `LiveConnectivityWatchdog`, MDPS Phase 2
> ResourceProfiler wiring) are still open per audit-issue-3 § "Update 2026-05-09 — UAC SSOT shipped, code wiring still
> open" — they are full-QG-cycle items in 3 different repos with foreign-WIP-in-shared-tree complications, and the
> MDPS Phase 1.2 callsite migration alone is a substantial 1100+ line file refactor that's not safe to bundle with the
> SSOT commit. The plan-of-record contract on `open_candle_writer` / `close_candle_writer` (parquet-write-lifecycle
> wrappers, NOT trade aggregator) stands as the canonical shape for the next agent to implement against; this issue
> resolved the contract-shape ambiguity but did not ship all the code.

# MDPS streaming primitives — spawn-prompt vs plan-of-record contract conflict

> **Severity**: P0 — blocks audit issue #3 (live_pipeline Phase 4 unblock). **Blast radius**: UTL +
> market-data-processing-service + market-tick-data-service + unified-api-contracts; affects 2 active plans
> (`mdps_streaming_and_backpressure_2026_05_07.md`,
> `live_pipeline_mtds_mdps_features_2026_05_08.md`). **Suggested owner**: operator triage — direction needed before any
> code lands.

## What I found

A spawn prompt for "MDPS streaming primitives — P0 blocker for live_pipeline Phase 4 per audit issue #3" specifies a
`open_candle_writer` / `close_candle_writer` contract that **does not match** the contract the active plans-of-record
specify under the SAME symbol names. Shipping the prompt's design would land 4 repos of code with the wrong shape and
collide with the next agent who picks up either of the two plans-of-record.

### Spawn-prompt-specified contract (Step 1 of the prompt)

`unified-trading-library/unified_trading_library/streaming/candle_writer.py`:

```python
class OpenCandleWriter:
    """Streaming candle accumulator — opens new candle at boundary, accumulates trades.

    Lifecycle: open() at boundary → on_trade(price, volume) called per tick →
    close() at next boundary returns finalized OHLCV bar."""
    def on_trade(self, price: Decimal, volume: Decimal, ts: datetime) -> None: ...
    def close(self) -> CandleBar: ...

class CloseCandleWriter:
    """Companion writer that finalizes + emits CANDLE_BOUNDARY_CROSSED event +
    triggers downstream CANDLE_COMPUTED cascade per live-pipeline architecture."""
    async def close_and_emit(self, candle: CandleBar) -> None: ...
```

This is a **trade-by-trade OHLCV aggregator** — incrementally builds bar state from individual trades, emits a finalized
`CandleBar` at boundary close, and publishes Redis Stream events.

### Plan-of-record contract (`mdps_streaming_and_backpressure_2026_05_07` Phase 1.1)

> Decision (default — option (a) per prior agent's audit): extend `canonical_writer.py` with two new public symbols
> co-located with `write_candle_parquet`:
>
> - `open_candle_writer(*, asset_group, venue, data_type, timeframe, root, day, available_at, schema, ...) -> CandleWriterHandle`
>   — opens a `StreamingParquetWriter`, returns an opaque handle (NamedTuple or small dataclass) holding the writer
>   instance + the shard row_key + a `total_rows: int` accumulator.
> - `close_candle_writer(handle: CandleWriterHandle, *, manifest_writer: ManifestWriter, attempted_at: datetime)` —
>   flushes + closes the parquet, then performs the SINGLE `record_captured` (or `record_empty` if `total_rows == 0`,
>   or `record_failed(...)` if the close raised). Idempotent on second call (no-op).
> - The existing `write_candle_parquet` is a one-shot convenience wrapper that does
>   `open → write_chunk(df) → close` for callers that already have a fully-materialised DataFrame.

This is a **parquet write-lifecycle wrapper** around the existing `StreamingParquetWriter`. Each `write_chunk(df)` takes
already-aggregated DataFrame chunks (the per-tf OHLCV bars MDPS already aggregates from upstream MTDS ticks). It owns
parquet atomicity, schema-drift detection across chunks, single `record_captured` per shard, idempotent close, cluster-
validation kwargs for bundled shards.

### Why the plan-of-record contract is the right one

1. **`live_pipeline_mtds_mdps_features_2026_05_08` Phase 4 explicitly cross-references the plan-of-record's contract:**

   > **Coordination**: `mdps_streaming_and_backpressure_2026_05_07` Phase 1 ships the
   > `open_candle_writer` / `close_candle_writer` UTL lifecycle. Phase 4 of THIS plan re-uses that lifecycle for live
   > aggregation writes (same shard atomicity contract, same per-VM tempfile + rename, same single-`record_captured`
   > per shard).

   The "shard atomicity contract / per-VM tempfile + rename / single-`record_captured` per shard" language describes
   the **parquet-write-lifecycle wrapper**, NOT a trade aggregator. A trade aggregator does not own a tempfile + rename;
   `StreamingParquetWriter` does.

2. **Phase 4 of the live-pipeline plan describes the trade aggregator separately** as a `live_aggregator.py` module
   inside MDPS — distinct file, distinct layer:

   > 4.2 — On each CandleBoundaryCrossedEvent, MDPS reads the closed window's tick range from MTDS via the in-process
   > buffer (or replay from GCS for batch parity) and runs through the SAME aggregation function as batch's
   > `_process_standard_timeframe` → emits CandleComputed{1m}.

   Trade-by-trade OHLCV building is the live-aggregator's job, NOT the parquet-write helper's job. The live-aggregator
   is OUT OF SCOPE for `mdps_streaming_and_backpressure` (which is purely about parquet-write streaming + memory
   backpressure).

3. **The plan-of-record's tests enumerate the parquet-lifecycle behaviour explicitly** (Phase 1.1 tests #1-6):

   - "open → write_chunk × N → close yields one parquet with N×rows; manifest has exactly ONE captured row"
   - "schema drift across chunks — second `write_chunk` with a different column set raises `SchemaDriftError`"
   - "bundled-shard cluster validation — `close_candle_writer` without `expected_root_clusters` for an `options_chain`
     data_type raises `MissingClusterValidationError`"

   These tests assume **DataFrame chunks**, not trades. The contract is unambiguous in the plan body.

4. **The audit issue's exit criterion** (`audit_2026_05_08_substantial_unfixed_items.md` Item 3) lists ONLY locations,
   not contracts:

   > - `open_candle_writer` + `close_candle_writer` exist in
   >   `unified-trading-library/unified_trading_library/streaming/`
   > - MDPS `app/core/live_workers.py` consumes them

   This was written assuming the consumer is the **MDPS write-side** (`_streaming_write_per_tf` in `live_workers.py`).
   That's the parquet-write-lifecycle consumer, NOT a trade aggregator consumer. The consumer site confirms the
   plan-of-record's contract.

### Other prompt-vs-plan deltas (smaller but compounding)

- **Prompt Step 2 (UAC `CONNECTIVITY_GAP_DETECTED`)**: prompt says "extend
  `unified-api-contracts/unified_api_contracts/events/streaming.py`". Plan-of-record (in
  `mdps_streaming_and_backpressure` § "Migrated issue 2026-05-08 — Live data recovery self-detect") says: "added to UAC
  `LifecycleEventType` ... each carries `{venue, gap_window_start, gap_window_end_or_null, last_received_at, message_count_during_gap}`".
  These are different UAC modules — `events/streaming.py` is the new Phase-4 streaming event package
  (CandleBoundaryCrossedEvent / CandleComputedEvent), `LifecycleEventType` is the workspace-wide lifecycle StrEnum.
  Plan adds a 3-event family (`CONNECTIVITY_GAP_DETECTED` / `CONNECTIVITY_RECOVERED` / `CONNECTIVITY_GAP_BACKFILLED`),
  prompt says only one event. Plan adds a `classification` Literal field that the prompt design also has — partial
  alignment. **This delta is reconcilable** (probably plan is right + add to LifecycleEventType so existing event-stream
  subscribers don't need a new code path), but worth confirming.
- **Prompt Step 3 (MTDS `LiveConnectivityWatchdog`)**: aligns with plan-of-record's `[SCRIPT] P1` todo. Module location
  (`market_tick_data_service/market_interface/connectivity_watchdog.py`) is reasonable; plan doesn't pin it.
- **Prompt Step 4 (MDPS `ResourceProfiler.on_memory_warning` wiring)**: matches plan-of-record Phase 2. **But Phase 2
  depends on Phase 1.2 landing first per the plan's execution DAG** (`Phase 1.2 → Phase 2`), and Phase 1.2 depends on
  Phase 1.1. So ResourceProfiler wiring cannot ship in isolation — it needs the streaming flush callsite in
  `_streaming_write_per_tf` first.

## Why it matters

- **Citadel-grade plan→code discipline**: per CLAUDE.md "Master Plan — Live DeFi Trading", _docs are the intent. Order
  of operations: doc → plan → code. Drift between any pair (doc/plan/code) is a review-blocking failure._ Shipping the
  prompt's contract under the plan's symbol names creates immediate plan-vs-code drift across 2 active plans + 4 repos.

- **4-repo blast radius**: shipping the prompt's design would commit to UTL + UAC + MTDS + MDPS shapes that the next
  agent on either plan-of-record will then have to refactor when they discover the conflict. The "Two teammates ×
  multiple parallel agents — don't edit unfamiliar files" rule applies — once the wrong contract lands across 4 repos,
  the next agent inherits architectural debt that's costlier to undo than to discuss now.

- **Phase 1.1's contract is load-bearing for live_pipeline Phase 4**: live_pipeline Phase 4.4 says "Phase 4 here re-uses
  the RSS-pause integration this plan ships in Phase 2" + "Phase 4 of THIS plan re-uses that lifecycle for live
  aggregation writes". If Phase 1.1 ships the wrong contract (trade aggregator instead of parquet-lifecycle wrapper),
  Phase 4 can't actually re-use it because the live-aggregator already produces DataFrame bars from trades — the right
  consumer of `open_candle_writer` is the **finalize-aggregated-bars-to-parquet** step, NOT the trade-by-trade
  aggregation itself.

- **"audit issue #3 RESOLVED" would not be honest**: per CLAUDE.md "Plans Run To Actual Completion", marking the audit
  issue resolved requires the work to actually unblock live_pipeline Phase 4. Shipping a divergent contract under the
  same symbol names blocks Phase 4 differently — it doesn't unblock anything; it creates a 4-repo refactor before Phase
  4 can land.

## Recommended decision

The operator picks ONE of these directions; agent ships per the chosen path. **Pending direction, no code is committed
to any of UTL / UAC / MTDS / MDPS.**

### (a) Ship per plan-of-record (recommended)

**Step 1 → parquet-write-lifecycle wrapper** in
`unified-trading-library/unified_trading_library/streaming/candle_writer.py` (or co-located in canonical_writer.py per
the plan body's wording — operator picks):

- `open_candle_writer(*, asset_group, venue, data_type, timeframe, root, day, available_at, schema, ...) -> CandleWriterHandle`
- `close_candle_writer(handle, *, manifest_writer, attempted_at, expected_root_clusters=None, cluster_extractor=None)`
- `write_candle_parquet(...)` becomes the one-shot wrapper.
- Tests per Phase 1.1's 6-test matrix.

**Step 2 → UAC**: extend `LifecycleEventType` (not `events/streaming.py`) with `CONNECTIVITY_GAP_DETECTED` /
`CONNECTIVITY_RECOVERED` / `CONNECTIVITY_GAP_BACKFILLED` per plan-of-record § "Migrated issue 2026-05-08".

**Step 3 → MTDS**: `LiveConnectivityWatchdog` per plan + per-venue `VENUE_HEARTBEAT_INTERVAL` (the calibration is a
separate `[SCRIPT] P1` todo — bootstrap with conservative defaults documented in the watchdog).

**Step 4 → MDPS**: split into TWO commits per the plan's execution DAG:

- 4.a — Phase 1.2: migrate `_streaming_write_per_tf` to consume `open_candle_writer` / `close_candle_writer` lifecycle.
- 4.b — Phase 2: wire `ResourceProfiler.on_memory_warning` callback to the BatchWorkers admission gate.

This is the path that aligns 4 repos + 2 plans + the audit issue with no architectural drift.

### (b) Ship per spawn-prompt (NOT recommended without re-spec)

If the prompt's trade-aggregator design IS what the operator wants, then both plans-of-record need to be re-spec'd
first because their cross-references will break:

- `mdps_streaming_and_backpressure_2026_05_07` Phase 1.1 + 1.2 + Phase 4 cross-references rewritten;
- `live_pipeline_mtds_mdps_features_2026_05_08` Phase 4 § "Coordination" rewritten + lines 425-449 + 1107-1108;
- The "shard atomicity contract / per-VM tempfile + rename / single-`record_captured` per shard" language in the live-
  pipeline plan needs to point at NEW symbols (the parquet-write-lifecycle wrapper that the trade-aggregator design
  doesn't include).

This is feasible but expensive (3+ plan rewrites + new symbols invented for the parquet-lifecycle helpers); the audit
issue's exit criterion would also need rewording.

### (c) Hybrid: rename to disambiguate

Rename the prompt's trade-aggregator design to `LiveCandleAggregator` / `live_aggregator.py` (matching the live-pipeline
Phase 4 module name); rename the plan's parquet-lifecycle helpers as planned (`open_candle_writer` /
`close_candle_writer`); ship both. Both plans-of-record stay intact; the only edit needed is to document that the
prompt's design is the live-aggregator (Phase 4 of live-pipeline), not the parquet-lifecycle wrapper (Phase 1.1 of
mdps-streaming).

This is the cleanest path if the operator wants both layers shipped this session. But Phase 4 of live-pipeline depends
on a lot of upstream Phase-1/2/3 work (Redis Stream + UTC-aligned scheduler + MTDS WS streaming + replay-subsystem) —
shipping the live-aggregator without those dependencies in place is premature.

## Other follow-ups captured for the same session

These are smaller per-shippable-unit items the operator should know about regardless of (a)/(b)/(c):

- **MDPS Phase 1.2 + Phase 2 are bound by the execution DAG**: Phase 2 (ResourceProfiler) depends on Phase 1.2 (callsite
  migration), which depends on Phase 1.1 (UTL primitive). Cannot ship Phase 2 in isolation; need the chain.

- **Step 4's prompt mentions a `ServiceBootstrap` callback**: per workspace QG STEP 5.61, MDPS already has a
  `ServiceBootstrap`. Adding `add_memory_warning_callback` to the bootstrap contract per plan Phase 2 is a UTL change
  (`feature_service_base/base_service.py`) — that's an extra UTL commit beyond what the prompt covers.

- **Audit issue #3's "Item 1 — Aster execution connector" already RESOLVED 2026-05-09 (`execution-service@25a1d561`).**
  Item #3 stays open pending direction here.

## Composes with

- `Findings Triage Discipline` HARD RULE — case-5 BIG finding (≥2 repos, contradicts SSOT, May-23 critical path) →
  notify operator + file issue doc, don't ship.
- `Plans Run To Actual Completion, Not Smoke-Test Green` — shipping divergent code under the same symbol names is the
  exact "looks done in isolation, system as a whole is RED" failure mode.
- `Two teammates × multiple parallel agents — don't edit unfamiliar files` — this composes; the next agent on either
  plan-of-record needs the contract correct or they re-do work.
- `Master Plan principle (docs are the intent)` — drift between plan and code at the contract level is review-blocking.
