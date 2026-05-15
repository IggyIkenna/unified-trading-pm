---
title:
  "MDPS Phase 1.2B as-spec'd creates dual-SSOT lifecycle collision — Phase 1.2A unified the manifest verb but lifecycle
  unification needs a different shape"
created: 2026-05-10
author: chain-agent-2026-05-10-pm
source:
  - plans/active/mdps_streaming_and_backpressure_2026_05_07.md (Phase 1.2B + Phase 2)
  - plans/active/issues/mdps_phase_1_2_phase_2_deferral_2026_05_10.md (the prior deferral whose architectural concern
    re-surfaced under the spec'd Phase 1.2B shape)
  - market-data-processing-service/market_data_processing_service/app/core/canonical_writer.py:363 (write_candle_parquet
    post-Phase 1.2A — manifest verb is record_captured, lifecycle is one-shot StreamingParquetWriter)
  - market-data-processing-service/market_data_processing_service/app/core/candle_write_mixin.py:93 (_write_candles —
    per-instrument path the chain-bundle migration would NOT reach)
  - market-data-processing-service/market_data_processing_service/app/core/live_workers.py:1142-1188
    (_streaming_write_per_tf, the spec'd Phase 1.2B target)
  - unified-trading-library/unified_trading_library/streaming/candle_writer.py (UTL@ac6e3244 streaming lifecycle)
locked_by: live-defi-rollout
locked_since: 2026-05-10
execution:
  owner: operator triage → MDPS-dedicated tab in next work-split (decision: ship spec'd 1.2B with risk acceptance, OR
    lift to write_candle_parquet-internal migration shape)
  cadence: one-shot — resume Phase 1.2B once architectural shape is decided
  verifier: 4-pillar manifest write-gate validation green on a real CeFi backfill VM (writegate Phase 5 baseline + plan
    Phase 4 end-to-end)
  last_executed: "NEVER"
---

# MDPS Phase 1.2B dual-SSOT lifecycle collision — second-pass discovery 2026-05-10 PM

> **Severity**: P1 — blocks live-pipeline Phase 4 + the May-23 cutover (Group F items 21+22 prereq) IFF Phase 1.2B is
> shipped as-spec'd without architectural-shape resolution. Not a data-correctness bug today (production candle writes
> on Phase 1.2A + 1.2A.1 are honest); the risk is silent dual-SSOT drift if Phase 1.2B lands on the chain-bundle path
> while the per-instrument path keeps a different lifecycle.
>
> **Blast radius**: market-data-processing-service production candle write path; UTL streaming-candle-writer consumers;
> downstream live-pipeline; honest-coverage manifest semantics.
>
> **Suggested owner**: MDPS-dedicated tab in next work-split, with a 30-minute architectural decision as the first step
> (operator triage between three options below).

## What I found

### State of Phase 1.2A + 1.2A.1 (recap)

- Phase 1.2A (MDPS@`afdb754`) migrated `write_candle_parquet`'s manifest verb from legacy v4 `manifest.add(...)` to v5
  `record_captured(row_key, df=..., ...)`. **Both** the chain-bundle path
  (`_streaming_write_per_tf → _write_candles → write_candle_parquet`) and the per-instrument path
  (`_process_instrument_file → _write_candles → write_candle_parquet`) NOW emit the same v5 manifest shape — Phase 1.2A
  successfully eliminated the manifest verb dual-SSOT.
- Phase 1.2A.1 (MDPS@`1cdcda7`) added `_stamp_candle_available_at` at the head of `write_candle_parquet` so every candle
  DataFrame carries `available_at` before reaching `record_captured`'s `assert_available_at_present` guard. Production
  candle writes can resume.

### Phase 1.2B as-spec'd in the plan body (lines 217-253) creates a NEW dual-SSOT

The plan body's Phase 1.2B shape:

> "1. At shard start (per `(asset_group, venue, data_type, root, day)`), call `open_candle_writer(...)` for each
> timeframe → dict[timeframe, CandleWriterHandle].  
> 2. Per source-batch, build a chunk DataFrame and call `handle.writer.write_chunk(chunk_df)`.  
> 3. At shard end, iterate handles and call `close_candle_writer(handle, manifest_writer=..., attempted_at=...)` for
> each."

If shipped as-written, the chain-bundle path uses the **UTL streaming lifecycle**
(`open_candle_writer / write_chunk / close_candle_writer`) directly — bypassing `_write_candles` entirely.
`close_candle_writer` calls `manifest_writer.record_captured(row_key=..., df=..., **manifest_kwargs)` (UTL
candle_writer.py:356). The per-instrument path keeps calling `_write_candles → write_candle_parquet` which calls
`StreamingParquetWriter` ONE-SHOT (full df in one call) then constructs its OWN `ManifestWriter` and emits
`record_captured` from `canonical_writer.py:546`.

**Result**: the chain-bundle path emits manifest rows via UTL's `close_candle_writer`; the per-instrument path emits
manifest rows via `canonical_writer.write_candle_parquet`'s inline `ManifestWriter.record_captured`. The manifest **verb
is identical** (Phase 1.2A success) but the **emission code path is divergent**:

| Path              | StreamingParquetWriter usage               | record_captured callsite         | Schema-drift detection               | Cluster validation kwargs                               |
| ----------------- | ------------------------------------------ | -------------------------------- | ------------------------------------ | ------------------------------------------------------- |
| Chain-bundle 1.2B | UTL streaming lifecycle (open/write/close) | UTL `close_candle_writer:356`    | Yes (UTL `_fingerprint` per-chunk)   | Yes (UTL handle.expected_root_clusters)                 |
| Per-instrument    | One-shot (write_chunk(df), close)          | `canonical_writer.py:546` inline | No (single chunk; no drift possible) | No (write_candle_parquet doesn't accept cluster kwargs) |

This is the **"No double SSOT in data-saving methodology"** rule violation flagged in CLAUDE.md — "Where two paths
produce the same outcome, one is deleted." Two emission code paths mean future bugs (e.g. a future change to the
manifest contract) need to be applied in both places, with high risk of drift.

### The right migration shape (matches Phase 1.1's plan-body intent)

The plan-of-record Phase 1.1 lines 49-61 already imply the correct shape:

> "the existing `write_candle_parquet` is a one-shot convenience wrapper that does `open → write_chunk(df) → close` for
> callers that already have a fully-materialised DataFrame."

The right Phase 1.2B is therefore **migrate `write_candle_parquet` itself to use UTL
`open_candle_writer / write_chunk / close_candle_writer` internally**. Then BOTH paths (chain-bundle calling either
`_write_candles → write_candle_parquet` OR the streaming variant directly) flow through the SAME UTL lifecycle. Only ONE
emission code path; no dual-SSOT.

The chain-bundle streaming benefit (peak memory ≈ one slice in flight) requires the open/write/close lifecycle to be
externally driven from `_streaming_write_per_tf`. To preserve that benefit AND eliminate the dual-SSOT, the migration
needs THREE coordinated changes:

1. **Refactor `write_candle_parquet`** to call UTL `open_candle_writer + write_chunk(df) + close_candle_writer`
   internally. Same external signature; internal lifecycle harmonised. (~300 lines touched in canonical_writer.py.)
2. **Add a streaming-mode counterpart** (`open_candle_streaming_writer` / `close_candle_streaming_writer` in
   `canonical_writer.py`) that exposes the lifecycle externally for chain-bundle callers — wraps UTL helpers with the
   same `_infer_*` / `_stamp_candle_available_at` / `lookup_mdps_contract` plumbing `write_candle_parquet` does.
3. **Refactor `_streaming_write_per_tf`** to call the new streaming helpers from canonical_writer (NOT UTL helpers
   directly). This keeps the chain-bundle path inside MDPS's canonical_writer SSOT.

This is the "migrate `write_candle_parquet`'s manifest contract from `add()` → `record_captured()`" architectural change
flagged in `mdps_phase_1_2_phase_2_deferral_2026_05_10.md` lines 110-113 — but the change is now narrower (lifecycle
harmonisation, not verb migration; the verb migration already shipped in Phase 1.2A).

## Why I did NOT ship Phase 1.2B today

1. **Architectural scope creep without operator approval.** The plan-of-record describes Phase 1.2B at the callsite (~5
   functions in `live_workers.py`). The right migration shape (per the dual-SSOT rule) needs ~3 coordinated changes
   spanning `canonical_writer.py` (~300 lines refactor) + `live_workers.py` (~80 lines) + new tests. That's a 4-6 hour
   sub-plan, not an in-scope flip. Per CLAUDE.md "Findings Triage Discipline" — this is a Case 5 BIG finding (changes
   the work-split, contradicts the SSOT). Operator decision needed.
2. **Per-instrument path benefit is real but bounded.** The per-instrument path doesn't have an accumulator (one-shot
   per `(instrument, tf)`). Migrating it to streaming lifecycle is architecturally clean but provides zero peak-memory
   benefit. The streaming benefit accrues only to the chain-bundle path.
3. **Phase 1.2A + 1.2A.1 already retire the production blocker.** Honest manifest writes resume on the band-aid
   memory-tier launcher today. Phase 1.2B's value is the durable streaming flush + retire-the-band-aid path; not
   correctness. Shipping a correct-but-architecturally-divergent Phase 1.2B is worse than waiting for the right shape.
4. **Phase 2 (ResourceProfiler) depends on Phase 1.2B per plan execution DAG line 298** ("Phase 2 has dep only on Phase
   1.2 callsite"). With Phase 1.2B deferred for architectural decision, Phase 2 cannot ship cleanly either — the
   "in-flight workers continue running" semantic relies on the streaming flush state Phase 1.2B introduces.

## What I shipped

1. **UTL@`6ce59900`** — exported
   `open_candle_writer / write_chunk / close_candle_writer / SchemaDriftError / CandleWriterHandle` from
   `unified_trading_library/streaming/__init__.py`. Pre-requisite for any MDPS consumer wire-in; the deep path was the
   only public surface before this commit. Discovery captured + fixed (Case 1 finding per Findings Triage). No behaviour
   change.
2. **This issue doc** — Case 5 architectural concern surfaced for operator triage.

## Why it matters

- **Live-pipeline Phase 4 stays blocked.** The umbrella plan (`live_pipeline_mtds_mdps_features_2026_05_08.md` Phase 4)
  re-uses the UTL lifecycle this plan ships in Phase 1.2B for live-mode candle aggregation. If Phase 1.2B lands as a
  dual-SSOT shape, live-pipeline Phase 4 inherits the divergence — every future MDPS write-path change has to be applied
  twice. Resolving the architectural shape NOW (before Phase 1.2B ships) is cheaper than refactoring after.
- **May-23 cutover deadline.** Group F items 21+22 are MDPS streaming + memory-backpressure prereqs. 13 days remain. The
  right shape ship is a 4-6 hour decision; the wrong shape ship is a multi-day refactor under deadline pressure.
- **`write_candle_parquet`-internal migration is also the live-pipeline-aggregator integration point.** The future live
  streaming aggregator (live*pipeline plan Phase 4) feeds candles into this same write path. If we migrate
  `write_candle_parquet` to UTL lifecycle internally NOW, the live aggregator's integration is "call
  `open_candle_writer` directly + use the existing canonical_writer plumbing" — clean. If we don't, the live aggregator
  has to re-derive `\_infer*\*`/`\_stamp_candle_available_at`/`lookup_mdps_contract` plumbing.

## Recommended decision

Three options, mutually exclusive:

### Option A — Migrate `write_candle_parquet` internally (recommended)

Spawn a new MDPS-dedicated sub-plan `plans/active/mdps_canonical_writer_lifecycle_unification_2026_05_10.md` with these
phases:

1. **Phase 1A — Refactor `write_candle_parquet` to use UTL lifecycle internally** (~3 hours):
   - Replace `StreamingParquetWriter` direct usage at `canonical_writer.py:476-485` with
     `open_candle_writer + write_chunk(df) + close_candle_writer` — convert the one-shot path to a 1-chunk lifecycle
     call.
   - Eliminate the inline `manifest_writer.record_captured(...)` block (lines 540-569) — `close_candle_writer` does this
     now.
   - Preserve all `_infer_*` / `_stamp_candle_available_at` / `lookup_mdps_contract` / `partition_path` plumbing.
   - Preserve cluster-validation kwargs (chain-bundle types) — pass them through to `close_candle_writer`.
   - Tests: every existing `test_canonical_writer_record_helpers.py` test still passes; add 2 new tests for the
     `open + 1×write_chunk + close` lifecycle path matching the existing one-shot semantics.

2. **Phase 1B — Add streaming-mode counterpart in `canonical_writer.py`** (~1 hour):
   - `open_candle_streaming_writer(*, asset_group, source_data_type, timeframe, instrument_id, venue, date_str, underlying, ..., manifest_service_name) -> CandleWriterHandle`
     — opens with all manifest_kwargs pre-filled.
   - `close_candle_streaming_writer(handle, *, manifest_writer)` — thin wrapper around UTL `close_candle_writer` that
     routes the manifest_writer (constructed once at the bundle level, not per-tf).
   - The user-facing `write_candle_parquet` becomes a 3-line wrapper:
     `handle = open_candle_streaming_writer(...); write_chunk(handle, candles_df); close_candle_streaming_writer(...)`.

3. **Phase 1C — Refactor `_streaming_write_per_tf` to use streaming helpers** (~1 hour):
   - At `_process_chain_bundle_streaming` start: per-tf `open_candle_streaming_writer(...)` → handles dict.
   - In `_streaming_process_slice_timeframes`: `write_chunk(handle, candles_df)` instead of accumulator append.
   - At bundle end (rename `_streaming_write_per_tf` → `_streaming_close_per_tf`): per-tf
     `close_candle_streaming_writer(handle, manifest_writer=...)`.
   - Tests in `tests/unit/test_streaming_write_per_tf.py`: 4-test matrix per the plan's existing spec (success / empty /
     failed / schema-drift) PLUS a memory-ceiling regression test via `tracemalloc`.

4. **Phase 2 — ResourceProfiler.on_memory_warning wiring** (~1 hour) — unchanged from the plan's spec, just sequenced
   AFTER Phase 1A+B+C land.

5. **Phase 4 — End-to-end validation** — unchanged from the plan's spec.

Total: ~6 hours, single coordinated tab, eliminates dual-SSOT, unblocks live-pipeline Phase 4 cleanly.

### Option B — Ship Phase 1.2B as-spec'd, accept dual-SSOT short-term

Ship the plan body's Phase 1.2B exactly. `_streaming_write_per_tf` calls UTL
`open_candle_writer / write_chunk / close_candle_writer` directly. `write_candle_parquet` keeps its current shape.
**Workspace rule violation accepted as temporary state** with a named successor plan filename — the same rule that
requires "Temporary state must have a named successor plan." Successor plan:
`mdps_canonical_writer_lifecycle_unification_2026_05_NN.md` (filed at archival of the streaming-and-backpressure plan).

**Risk**: future MDPS write-path bugs need to be fixed in two places. Live-pipeline Phase 4 inherits the divergence.

### Option C — Withdraw Phase 1.2B + Phase 2 from streaming-and-backpressure plan

Plan-of-record gets a re-scope: Phase 1.2B and Phase 2 move to the new lifecycle-unification plan (Option A's shape).
The streaming-and-backpressure plan archives with Phase 1.1 + 1.2A + 1.2A.1 shipped + Phase 1.2B + Phase 2 + Phase 4
explicitly migrated to the successor. Phase 4's end-to-end validation gates on Option A's lifecycle-unification plan
landing.

## Exit criteria (closing this issue)

- Operator triage decision logged (A / B / C). — `[ ]` open
- If A or C: new sub-plan `mdps_canonical_writer_lifecycle_unification_2026_05_NN.md` filed in `plans/active/` with the
  Phase 1A/1B/1C structure described above. — `[ ]` open
- If B: streaming-and-backpressure plan body acknowledges the dual-SSOT temporary state + names the successor plan
  filename per the "Temporary state must have a named successor plan" rule. — `[ ]` open
- Phase 1.2B + Phase 2 + Phase 4 ship under whichever plan owns them post-decision. — `[ ]` open
- Live-pipeline Phase 4 banner removable. — `[ ]` open

## Extension issue (2026-05-10 evening)

> **EXTENSION**: A subsequent agent attempted Option A and discovered a GCS-upload semantics gap — UTL
> `close_candle_writer` finalizes locally + `shutil.move`s, but `write_candle_parquet` consumers all upload to GCS. See
> [`mdps_option_a_gcs_upload_semantics_gap_2026_05_10.md`](mdps_option_a_gcs_upload_semantics_gap_2026_05_10.md) for the
> audit + R1 (MDPS-level wrapper) vs R2 (extend UTL `close_candle_writer` with GCS upload) decision matrix. Phase 1.2B +
> Phase 2 remain DEFERRED pending operator triage of Option A's R1 vs R2 sub-decision.

## Cross-references

- [`mdps_option_a_gcs_upload_semantics_gap_2026_05_10.md`](mdps_option_a_gcs_upload_semantics_gap_2026_05_10.md) — the
  extension issue capturing Option A's internal architectural sub-decision (R1 MDPS-local vs R2 UTL-extension).
- [`mdps_phase_1_2_phase_2_deferral_2026_05_10.md`](mdps_phase_1_2_phase_2_deferral_2026_05_10.md) — the prior deferral
  this issue continues (Phase 1.2A unified the manifest verb; this issue is the lifecycle-shape follow-up).
- [`mdps_streaming_and_backpressure_2026_05_07.md`](../mdps_streaming_and_backpressure_2026_05_07.md) — plan-of-record;
  Phase 1.2B + Phase 2 annotation update tracking the deferral lives in the plan body.
- [`live_pipeline_mtds_mdps_features_2026_05_08.md`](../live_pipeline_mtds_mdps_features_2026_05_08.md) Phase 4 — the
  downstream consumer of this work; banner removal gated on resolution.
- UTL@`ac6e3244` — UTL streaming-candle-writer primitives (lifecycle the migration consumes).
- UTL@`6ce59900` — UTL streaming facade re-exports (this session's pre-requisite ship).
- MDPS@`afdb754` — Phase 1.2A manifest verb migration (foundation that makes this issue tractable).
- MDPS@`1cdcda7` — Phase 1.2A.1 `available_at` stamping (production blocker retired).
