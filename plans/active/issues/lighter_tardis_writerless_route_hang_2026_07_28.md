---
doc_type: issue
title: "LIGHTER-ZKSYNC (and likely any Tardis venue) _route_lighter hangs indefinitely when called with writer=None"
summary:
  "While re-verifying the LIGHTER-ZKSYNC Tardis exchange-slug/market_id fix with a diagnostic script calling
  _route_lighter directly with writer=None, the call reliably hung indefinitely (no further log output, no exception, no
  completion) immediately after a successful Tardis download + one 'Event logging not initialized' warning from the
  in-flight registry. Reproduced 3/3 times across trades/book_snapshot_5/derivative_ticker. Not a defect in the
  Tardis-slug/market_id fix itself (real rows download correctly in every case) — this is a separate robustness gap in
  the post-download validation/in-flight-registry path when no real ChunkWriter or setup_events() call is present."
status: open
nature: notes
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, unified-trading-library]
scope: [engineer]
tags: [tardis, lighter-zksync, hang, event-logging, diagnostics]
related:
  [
    /plans/archive/2026_07/defi_satellite_ao_dispatch_batch1_2026_07_25.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
  ]
created: 2026-07-28
author: unknown
parent_epic: infrastructure_master
priority: P3
source:
  "Discovered while executing defi_satellite_ao_dispatch_batch1-045 (re-verify LIGHTER-ZKSYNC Tardis fix), slot-12,
  2026-07-28."
assigned_vm: planning
resolved_by:
locked_by:
context_scope:
  [
    market-tick-data-service/market_tick_data_service/market_interface/adapters/tradfi/tardis_batch_download.py,
    unified-trading-library/unified_trading_library/io/streaming_writer.py,
    unified-trading-library/unified_trading_library/io/streaming_shard_finalizer.py,
    unified-trading-library/unified_trading_library/events_interface/__init__.py,
    unified-trading-library/unified_trading_library/lifecycle/in_flight_registry.py,
    /plans/archive/2026_07/defi_satellite_ao_dispatch_batch1_2026_07_25.md,
  ]
execution_scope: orchestrator-agent
model_tier: sonnet-doable
thinking_tier: medium
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.5
last_updated: 2026-07-28
supersedes:
superseded_by:
depends_on:
assigned_role: data_engineering
drift_direction: advance-code
locked_since:
# archive_exempt: true (temporary bridge, flip-then-mv pattern) — this doc's last open
# todo is its own archival trigger; exemption set in the SAME commit as the flip so the
# cross-repo /done M3 flip check passes at the active path, then dropped when git mv'd
# to plans/archive/issues/ in the IMMEDIATELY FOLLOWING commit (check_archive_candidates.sh
# --only flip-then-mv exemption, 2026-08-09). See Progress Log 2026-08-12.
archive_exempt: true
---

## What I found

Re-verifying the LIGHTER-ZKSYNC Tardis exchange-slug + numeric market_id fix (`market-tick-data-service@0c4000a02`)
required calling `market_tick_data_service.adapters.umi_tick_provider._route_lighter` directly from a standalone
diagnostic script (no real `ChunkWriter`, `writer=None`, `setup_events()` never called — this is not a real service
entrypoint, just a probe). For each of the 3 data_types (`trades`, `book_snapshot_5`, `derivative_ticker`), the sequence
was identical:

1. `Tardis streaming request: exchange=lighter, symbol=<id>, data_type=<dt>, date=2026-07-01` — correct.
2. `Free data date detected, skipping auth` — correct (first-of-month free tier).
3. `Tardis streaming success: <N> rows, ...` — real data, confirms the fix works.
4. `DomainValidationService initialized` + a `Stage-0 OBSERVE: non-canonical instrument-id form` notice (expected — cefi
   single-instrument shard filenames are not full canonical instrument_ids, a separate known/tracked pre-existing gap,
   not this finding).
5. `WARNING in-flight key=<key> failed: Event logging not initialized. Call setup_events() first.`
6. **Then: nothing. No further log lines, no exception, no return from the awaited coroutine.** CPU/RSS on the process
   stayed elevated (in one 3-symbol/3-data_type combined run, RSS grew past 13GB before eventually being killed by an
   outer `timeout`) but no forward progress was observed. Each single-symbol, single-data_type repro also hung the same
   way after step 5, requiring the exact PID to be killed manually.

## Why it matters

- This is NOT the fix being re-verified — the Tardis slug (`lighter`, not `lighter-zksync`) and numeric market_id
  resolution both work correctly on current code; real rows returned every time (trades: 88,494/218,300/591,860 rows
  across market_ids 0/1/2; book_snapshot_5: 1,459,257 rows; derivative_ticker: 238,121 rows — all for BTC market_id=1 on
  2026-07-01).
- But it's a real robustness gap: any code path that reaches `_route_lighter` (or, likely, the shared
  `TardisAdapter.download_batch`/in-flight-registry plumbing more generally, not LIGHTER-specific) without a live
  event-logging system initialized appears to hang forever rather than failing fast or degrading gracefully. That's a
  foot-gun for future diagnostic tooling, one-off scripts, or tests that call these adapters directly (a genuine, if
  rare, production-adjacent risk — a mis-wired one-off backfill/diagnostic script could hang a process indefinitely
  instead of erroring).
- Root cause NOT yet isolated (not confirmed): the in-flight registry's failed-item path awaiting a flush/ack that
  nothing ever provides when there's no real writer consuming it; or a retry loop with no backoff cap tied to the "Event
  logging not initialized" condition.

**RULED 2026-08-12 (/plan-reconcile, operator interactive)**: implement the configurable-timeout fix in the SHARED
`_upload_gcs_with_retry()` helper (broadest fix — covers every caller of that helper, not just `_route_lighter`), not a
narrow call-site-only `asyncio.wait_for()` wrap and not graceful-degradation-only. Not implemented in this docs-only
pass — tracked as a new `[CODE]` todo below.

- [x] ✅ [CODE] P2. Add a configurable timeout to `_upload_gcs_with_retry()` (or the shared in-flight-registry flush/ack
      await path it wraps, wherever the actual hang occurs) so a caller with no live writer/event-logging fails fast
      instead of hanging indefinitely, per the 2026-08-12 operator ruling (`plan_reconciler_findings_all_2026_08_12.md`,
      RULED block above). Repo: market-tick-data-service / unified-trading-library. — implemented via a configurable
      `timeout_seconds` on the shared helper (option 2) wired through
      `StreamingParquetWriter(upload_timeout_seconds=...)` (default 600s = `_GCS_UPLOAD_TIMEOUT_SECONDS`); daemon-thread
      wall-clock bound raises `TimeoutError` instead of an indefinite hang; + 2 unit tests.
      **unified-trading-library@b3afeb8c4** (QG green, quickmerge-verified on origin/live-defi-rollout).

## Recommended decision

Investigate whether `TardisAdapter.download_batch` / `_ChainAnnotatingWriter` / the in-flight-registry consumer path has
an unbounded await when `writer is None` and/or `setup_events()` was never called, and either (a) fail fast with a clear
error in that case, or (b) add a bounded timeout so a misconfigured caller degrades instead of hanging.

## Todos

- [x] [DIAG] P3. Root-cause the indefinite hang in the Tardis download post-processing path (in-flight registry /
      `DomainValidationService` / event-logging consumer) when a caller invokes an adapter's `download_batch`/
      `_route_*` with `writer=None` and no prior `setup_events()` call. — market-tick-data-service +
      unified-trading-library root cause documented below; fix is a human design decision (see Progress Log §
      2026-08-05).

## Progress Log

- **na-eligibility-audit 2026-07-30**: RECLASSIFY -> assigned_vm: planning (conflict-check CLEAR against 231 active
  planning docs; no open todo elsewhere duplicates this claim) - scoped root-cause diagnostic with an explicit stated
  done-when (identify the blocking await) — AO-eligible per dispatch-scope eligibility
- **context-scout 2026-08-03**: refreshed context_scope (4 entries) — reviewed against current doc content, list still
  accurate (unchanged).
- **ROOT CAUSE ANALYSIS — slot-5, 2026-08-05**: two-phase failure identified via static trace of the `_route_lighter` →
  `download_batch` → `_download_one_perp_symbol_streaming` → `_ensure_cols_and_finalise` (ThreadPoolExecutor) →
  `finalise_and_write_cefi_shards_streaming` → `StreamingShardFinalizer.finalize()` → `_tardis_cefi_shard_router` →
  `finalise_rows_and_path` call chain.

  **Phase 1 — trigger**: `finalise_rows_and_path()` at `tardis_cefi_shards.py:818` calls
  `log_event("SCHEMA_CONTRACT_VIOLATION", ...)` inside a schema-validation block. When `setup_events()` hasn't been
  called and `_mode` is not `"local"/"test"` (default: `"batch"`), the `log_event()` in
  `unified_trading_library/events_interface/__init__.py:274` raises
  `RuntimeError("Event logging not initialized. Call setup_events() first.")`. Additional `log_event` sites in the
  manifest-writer path (`_writer_validation.py:221,238`, `_rows.py:696`, `_queries.py:369`, `_state.py:554,577`) can
  trigger the same failure.

  **Phase 2 — the hang**: `StreamingShardFinalizer._route_row_groups()` at `streaming_shard_finalizer.py:220` catches
  the router's exception and calls `_close_writers_on_exception()` (line 221) to close any `StreamingParquetWriter`
  instances already created for prior row-groups. Each `writer.close()` → `_upload_to_gcs()` (via
  `streaming_writer.py:417`) performs a **synchronous, unbounded** GCS upload on the executor thread. In a standalone
  diagnostic script without proper cloud-credential/channel initialization, this GCS upload blocks indefinitely — the
  executor thread is stuck, the `loop.run_in_executor` future at `tardis_batch_download.py:709-711` never resolves, and
  the coroutine hangs forever on `await`. Same hazard exists in `_emit_per_symbol_manifest` → `ManifestWriter.flush()` →
  `_write_to_gcs()` which also performs synchronous GCS operations.

  **Exact blocking await**: `await loop.run_in_executor(finalise_executor, _ctx.run, _ensure_cols_and_finalise)` at
  `tardis_batch_download.py:709-711` — the future never resolves because the executor thread is blocked inside
  `StreamingParquetWriter.close()` → `_upload_to_gcs()` → `_upload_gcs_with_retry()` (unbounded synchronous GCS upload).

  **Recommended fix (human design decision — 3 options)**:
  1. **(Minimal/fail-fast)** Add `asyncio.wait_for(..., timeout=N)` around the `run_in_executor` call at line 709.
  2. **(Robustness)** Add a configurable upload timeout to `_upload_gcs_with_retry()` in `streaming_writer.py`.
  3. **(Graceful degradation)** Wrap `log_event()` calls in the Tardis processing path with the same
     `try/except RuntimeError` pattern used by `_default_event_emitter` in `instruments_write_gate.py:147-153`. This
     addresses the trigger (Phase 1) rather than the hang mechanism (Phase 2), but is the most targeted fix for the
     specific "standalone diagnostic script without setup_events()" use case.

  **Full call chain traced**: `_route_lighter(venue_upper="LIGHTER-ZKSYNC", writer=None, ...)` →
  `tardis.download_batch(writer=_w=None, ...)` → `_run_per_symbol_batch(partition_writer=None, ...)` →
  `_runner.run(tasks)` → `_safe_run_one` → `task.fn()` → `_download_one_perp_symbol` →
  `_download_one_perp_symbol_streaming` → `await self.download_csv_streaming(...)` [SUCCEEDS] →
  `await loop.run_in_executor(finalise_executor, _ctx.run, _ensure_cols_and_finalise)` **[HANGS]** where
  `_ensure_cols_and_finalise` calls `finalise_and_write_cefi_shards_streaming` → `StreamingShardFinalizer.finalize()` →
  `_route_row_groups` → `shard_router(rg_df)` → `_tardis_cefi_shard_router` → `finalise_rows_and_path` →
  `log_event("SCHEMA_CONTRACT_VIOLATION", ...)` → `RuntimeError("Event logging not initialized...")` → caught →
  `_close_writers_on_exception` → `StreamingParquetWriter.close()` → `_upload_to_gcs()` [BLOCKS INDEFINITELY].

  **Evidence**: The observed WARNING
  `"in-flight key=<key> failed: Event logging not initialized. Call setup_events() first."` at step 5 of the issue
  report is `in_flight_registry.py:143` logging the `str(exc)` from the RuntimeError caught at
  `tardis_batch_download.py:724` (`except Exception as _exc: registry.failed(in_flight_key, error=str(_exc))`). The
  "DomainValidationService initialized" message (step 4) is the module-level
  `_DOMAIN_VALIDATOR = DomainValidationService("market_data")` in `engine/orchestrator/__init__.py:133` executing at
  first import of the orchestrator module (triggered by `finalise_rows_and_path` →
  `_validate_canonical_path_at_write_time` in `symbol_rules.py`). The "Stage-0 OBSERVE" notice (step 4) is
  `symbol_rules.py:420` logging non-canonical instrument-id forms.

- **context-scout 2026-08-06**: re-scouted; the 2026-08-05 root-cause analysis pinpointed exact call-chain files
  (`tardis_batch_download.py`, `streaming_writer.py`, `streaming_shard_finalizer.py`, `events_interface/__init__.py`)
  more precise than the prior generic entries — swapped `umi_tick_provider.py`/`event_facade.py` for those, kept
  `in_flight_registry.py` (still the evidence log source) and the source dispatch plan, now 6 entries.
- **slot-7 implementation — 2026-08-12**: Implemented the operator-ruled fix (option 2 — configurable upload timeout in
  the SHARED `_upload_gcs_with_retry()` helper, `unified_trading_library/io/streaming_writer.py`). The helper gains
  `timeout_seconds: float | None = None` (`None` = historical unbounded behavior); when set, the whole `with_retry`
  chain runs on a daemon `threading.Thread` and the caller is bounded by a wall-clock `join(timeout_seconds)`, raising
  `TimeoutError` on expiry so a wedged GCS upload (writer=None / no setup_events() diagnostic call) fails fast instead
  of blocking the executor thread forever (Phase 2 mechanism). `StreamingParquetWriter` gains `upload_timeout_seconds`
  (default `_GCS_UPLOAD_TIMEOUT_SECONDS = 600.0`, matching the GCS SDK's per-attempt/retry deadline so healthy uploads
  are unaffected; `None` opts out). Shipped **unified-trading-library@b3afeb8c4** (QG green 158s incl. 2 new unit tests;
  quickmerge-verified on origin/live-defi-rollout).

## Follow-ups

- [x] ✅ [CODE] P3. Implement one of the 3 recommended fixes for the Tardis writer=None/setup_events() hang
      (asyncio.wait_for timeout at tardis_batch_download.py:709, configurable upload timeout in _upload_gcs_with_retry,
      or graceful log_event RuntimeError degradation) — RESOLVED: the 2026-08-12 operator ruling
      (`plan_reconciler_findings_all_2026_08_12.md`) picked option 2 (configurable timeout in the shared
      `_upload_gcs_with_retry()`), implemented in the P2 todo above — **unified-trading-library@b3afeb8c4**. _(retagged
      2026-08-12 (/plan-reconcile): no longer applicable — the operator pick resolved the 3-option ambiguity; tag
      superseded by the implementation.)_

> **2026-08-06 archive-candidate audit**: DIAG todo is [x] (root cause traced to the blocking run_in_executor await),
> but the Progress Log's 'Recommended fix (human design decision - 3 options)' is never implemented - the hang is only
> diagnosed, not fixed, and no follow-up todo tracks the fix
