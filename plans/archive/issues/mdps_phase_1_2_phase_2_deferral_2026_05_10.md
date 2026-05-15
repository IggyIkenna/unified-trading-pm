---
title:
  "MDPS Phase 1.2 + Phase 2 deferral 2026-05-10 — semantic dual-SSOT collision blocks safe migration; needs plan refresh"
created: 2026-05-10
author: chain-agent-2026-05-10
source:
  - plans/active/mdps_streaming_and_backpressure_2026_05_07.md (Phase 1.2 + Phase 2)
  - plans/active/issues/audit_2026_05_08_substantial_unfixed_items.md Item #3 § "Still open"
  - plans/archive/issues/mdps_streaming_primitives_prompt_vs_plan_conflict_2026_05_09.plan.md (resolution archived)
  - market-data-processing-service/market_data_processing_service/app/core/live_workers.py:1142-1188
  - market-data-processing-service/market_data_processing_service/app/core/canonical_writer.py:168-347
  - unified-trading-library/unified_trading_library/streaming/candle_writer.py (UTL@ac6e3244)
locked_by: live-defi-rollout
locked_since: 2026-05-10
execution:
  owner: operator triage → MDPS-dedicated tab in next work-split
  cadence: one-shot — resume Phase 1.2 + Phase 2 once preconditions met
  verifier: Phase 4 end-to-end VM run (mdps_streaming_and_backpressure plan §Phase 4)
  last_executed: "NEVER"
---

# MDPS Phase 1.2 + Phase 2 deferral — second-pass attempt 2026-05-10

> **2026-05-10 PM-second SUPERSEDED-BY**: this issue's "remaining scope is the per-batch chunking refactor… not blocked
> by SSOT" framing was wrong. The PM-second chain-agent re-attempted Phase 1.2B and discovered that the spec'd shape
> creates a NEW dual-SSOT lifecycle collision — the chain-bundle path migrating to UTL `open/write/close` lifecycle
> while the per-instrument path keeps `write_candle_parquet`'s one-shot lifecycle WOULD undo Phase 1.2A's
> verb-unification spirit at the lifecycle layer. Pre-requisite UTL fix shipped: UTL@`6ce59900` (streaming facade
> re-exports). Architectural concern + 3 resolution options now tracked in
> [`mdps_phase_1_2b_dual_ssot_lifecycle_collision_2026_05_10.md`](mdps_phase_1_2b_dual_ssot_lifecycle_collision_2026_05_10.md)
> — that issue doc is the active SSOT for Phase 1.2B + Phase 2 next steps. This issue stays open as the prior session's
> deferral record (Phase 1.2A + 1.2A.1 RESOLVED here per below; Phase 1.2B + 2 redirected to the new issue doc).

> **2026-05-10 PM RESOLVED-PARTIAL**: Phase 1.2A SHIPPED MDPS@`afdb754` (v5 manifest verb migration eliminated the
> dual-SSOT collision). Phase 1.2A.1 SHIPPED MDPS@`1cdcda7` (write-time `available_at` stamping closes the
> production-write blocker). Phase 1.2B (`_streaming_write_per_tf` structural migration to UTL
> `open_candle_writer`/`write_chunk`/`close_candle_writer` lifecycle) AND Phase 2 (`ResourceProfiler.on_memory_warning`
> wiring) remain DEFERRED to the next MDPS-focused tab — not blocked by SSOT or correctness; remaining scope is the
> per-batch chunking refactor for the memory-budget improvement Phase 1.2B promises (peak memory ≈ one timeframe-batch
> in flight, NOT all-day-all-timeframes accumulated). Phase 1.2A.1 means production candle writes can resume on the
> band-aid memory-tier launcher (`deployment-service@02ee6d6`) without raising `LookaheadBiasError` — the band-aid
> retirement waits on Phase 1.2B + Phase 4.

> **Severity**: P0 — blocks live-pipeline Phase 4 + the May-23 cutover (Group F items 21+22 prereq).
>
> **Blast radius**: market-data-processing-service production candle write path; downstream live-pipeline; unified
> manifest semantics.
>
> **Suggested owner**: MDPS-dedicated tab in next work-split, with a 30-minute plan-of-record refresh as the first step.

## Why this issue exists

Picking up from [`audit_2026_05_08_substantial_unfixed_items.md`](audit_2026_05_08_substantial_unfixed_items.md) Item #3
§ "Still open" (deferred 2026-05-09 with rationale "MDPS working tree has 9+ foreign-modified test files from parallel
agents' sessions"). Today's chain agent re-attempted Phase 1.2 + Phase 2 and surfaced a **semantic dual-SSOT collision**
that the original plan-of-record `mdps_streaming_and_backpressure_2026_05_07.md` did not anticipate. The deferral
pattern banned by CLAUDE.md "Plans Run To Actual Completion, Not Smoke-Test Green" is exactly what this is — but the
right next move is not to ship a broken half-migration; it is to refresh the plan-of-record so the next agent has a
clean target.

## What I found (today, 2026-05-10)

### State of the working tree (workspace-wide)

Workspace is in heavy in-flight state from Friday-Saturday's parallel-agent activity:

- **PM**: ~250 modified files including `audit_2026_05_08_substantial_unfixed_items.md` (76 lines diff, foreign).
  Plan-of-record `mdps_streaming_and_backpressure_2026_05_07.md` itself is CLEAN.
- **MDPS**: `canonical_writer.py` has a 1-line dirty diff (a docstring rename
  `data_pipeline_completion_2026_04_18.plan.md` → `…_18.md` — automated parallel-agent plan-rename sweep, not
  substantive WIP). `live_workers.py` is CLEAN. The `_streaming_write_per_tf` function at line 1142-1188 is intact and
  matches the plan-of-record's described shape.
- **UTL**: `streaming/candle_writer.py` has a 1-line dirty diff (foreign). Tests directory has 8 foreign-modified test
  files. The shipped UTL primitives at `ac6e3244` are stable on origin.
- **UAC**: 2 foreign-modified test files + `__init__.py`.

The dirty PM + dirty MDPS canonical_writer.py + dirty UTL state means foot-gun #1 (bundling foreign work into my commit
via shared-tree git-add races) and foot-gun #4 (auto-revert prek hooks) are HIGH-probability incidents. Per CLAUDE.md
"Two teammates × multiple parallel agents — don't edit unfamiliar files" I MUST stay surgical with pathspec form on
every commit + skip files I don't own.

### State of the architecture (semantic dual-SSOT)

**This is the substantive blocker, NOT the foreign WIP.** Reading plan-of-record line 50-61 + UTL@`ac6e3244`'s shipped
shape together, the current state is:

1. UTL ships `open_candle_writer` / `write_chunk` / `close_candle_writer` in
   `unified_trading_library/streaming/candle_writer.py`. `close_candle_writer` calls
   `manifest_writer.record_captured( row_key=..., df=..., attempted_at=..., **manifest_kwargs)` — the v5 honest-coverage
   manifest verb.
2. MDPS already has `canonical_writer.write_candle_parquet(...)` (canonical_writer.py:168-347) which calls
   `manifest_writer.add(processing_date=..., venue=..., chain=..., instrument_type=..., data_type=..., timeframe=..., league_id=..., underlying=..., instrument_id=..., row_count=..., expected=True, available=True)`
   — the LEGACY v4 `add()` shape, NOT `record_captured`.
3. Plan-of-record line 56-61 says "the existing `write_candle_parquet` is a one-shot convenience wrapper that does
   `open → write_chunk(df) → close` for callers that already have a fully-materialised DataFrame (preserves backward
   compat for non-MDPS callers — the workspace 'no shims' rule allows this when a single repo is being migrated)."

**The collision.** If Phase 1.2 migrates `_streaming_write_per_tf` (live_workers.py:1142-1188) to call
`open_candle_writer → write_chunk × N → close_candle_writer` directly from UTL, the manifest writes for the
`_streaming_write_per_tf` path use `record_captured(...)` (v5 shape) while EVERY OTHER MDPS write path
(`_process_instrument_file → _write_candles → write_candle_parquet`) keeps using `manifest_writer.add(...)` (v4 shape).
This is a textbook **double SSOT in data-saving methodology** — banned by CLAUDE.md "No double SSOT". Production
manifest rows would have inconsistent shape depending on which orchestration path produced them, breaking honest-
coverage rollups + data-status drilldown.

**The right migration shape** is the one plan-of-record line 50-61 implies but doesn't make explicit: also migrate
`canonical_writer.write_candle_parquet` to internally use the UTL lifecycle (i.e. `write_candle_parquet` becomes the
one-shot convenience wrapper that calls `open_candle_writer → write_chunk(df) → close_candle_writer` under the hood,
losing the inline `manifest_writer.add(...)` call). That keeps every MDPS callsite on the same v5 manifest path.

**Why I did NOT ship that today**:

1. `canonical_writer.py` is foreign-modified (the 1-line docstring sweep). Editing it now would require resolving the
   dirty hunk into my commit — bundling foreign WIP via foot-gun #1.
2. The migration of `write_candle_parquet`'s manifest contract from `add()` → `record_captured()` is an architectural
   change with workspace-wide consumer impact (e.g. `_process_instrument_file` flows + every other MDPS write path). The
   plan-of-record does NOT describe this migration as a Phase 1.x todo. Doing it as part of Phase 1.2 would silently
   expand the work-split scope.
3. Per CLAUDE.md "Findings Triage Discipline" — this is an "in-flight VM bug / contradicts an in-flight refactor" case-5
   BIG finding. The right action is operator-notify + issue doc, not silently expand scope.

### Phase 2 cannot ship without Phase 1.2

Plan-of-record line 298 (execution DAG) says Phase 2 has "dep only on Phase 1.2 callsite". Phase 2 wires
`ResourceProfiler.on_memory_warning` to gate `BatchWorkers._submit_instrument_file_tasks` (batch_workers.py:288). The
gate's "in-flight workers continue running" semantic relies on Phase 1.2's streaming flush state surviving — without
Phase 1.2 the in-flight workers still hold full-DF state in memory, which means Phase 2's "pause new submits but let
in-flight finish" gives weaker memory relief than the plan promises. Shipping Phase 2 alone is technically feasible (it
would reduce peak memory by gating new submits) but the plan-of-record explicitly orders Phase 2 BEHIND Phase 1.2. Per
CLAUDE.md "Plans must capture full codebase impact upfront" + "Citadel-Grade Planning § 2 Phased Execution DAG", I will
NOT silently shuffle the order.

## Why it matters

- **Live-pipeline Phase 4 stays blocked.** The umbrella plan (`live_pipeline_mtds_mdps_features_2026_05_08.md` Phase 4)
  re-uses the UTL lifecycle this plan ships. Unblocking that requires Phase 1.2 wiring landed in MDPS.
- **May-23 cutover deadline.** Group F items 21+22 are MDPS streaming + memory-backpressure prereqs. 13 days remain.
- **Manifest correctness drift risk.** If a future agent ships Phase 1.2 without ALSO migrating `write_candle_parquet`,
  MDPS production starts emitting two manifest shapes and downstream rollups silently corrupt. This needs to be in the
  plan body, not in agent memory.

## Recommended decision

**Refresh `mdps_streaming_and_backpressure_2026_05_07.md` plan body** before the next agent picks up Phase 1.2:

1. **Add Phase 1.2.A — UNIFY canonical_writer.py manifest semantics**: migrate `write_candle_parquet` to use
   `open_candle_writer → write_chunk → close_candle_writer` internally (so the manifest verb is `record_captured`). This
   becomes the one-shot wrapper line 50-61 already references, but with the manifest verb correction. Body includes the
   workspace-grep audit table per CLAUDE.md "Citadel-Grade Planning § 6 Downstream Consumer Updates" (extended) listing
   every caller of `write_candle_parquet` + every caller of `manifest_writer.add(...)` in MDPS that needs to flip.
2. **Sequence Phase 1.2.A before Phase 1.2.B (the original `_streaming_write_per_tf` migration)** — Phase 1.2.A is
   strictly preparatory (single-call manifest verb migration); Phase 1.2.B is the streaming flush migration.
3. **Add an explicit "what NOT to do" callout**: do NOT ship Phase 1.2.B alone. The dual-SSOT collision is the
   substantive blocker the previous deferral did not name. Phase 2 stays gated on Phase 1.2.B.
4. **Keep the existing 4-test matrix in Phase 1.2.B**, but add 2 tests in Phase 1.2.A:
   `test_write_candle_parquet_emits_record_captured_not_add` + `test_manifest_row_shape_v5_post_migration`.
5. **Operator coordination**: confirm no concurrent agent is currently mid-edit on `canonical_writer.py` before spawning
   the MDPS-dedicated tab. Today's 1-line dirty diff is the docstring sweep — if that has landed by the time the new tab
   spawns, the tree is clean enough to safely ship Phase 1.2.A.

## Exit criteria (closing this issue)

- Plan-of-record `mdps_streaming_and_backpressure_2026_05_07.md` body includes the new Phase 1.2.A todo with full
  audit-table + manifest-verb migration design. — `[ ]` open
- MDPS-dedicated tab assigned in next work-split. — `[ ]` open
- canonical_writer.py is clean OR foreign 1-line diff has been pushed by its owner. — `[ ]` open
- Phase 1.2.A + 1.2.B + Phase 2 ship in the same coordinated tab session per the refreshed execution DAG. — `[ ]` open
- Live-pipeline Phase 4 banner removable. — `[ ]` open

## Cross-references

- [`audit_2026_05_08_substantial_unfixed_items.md`](audit_2026_05_08_substantial_unfixed_items.md) Item #3 — the prior
  deferral this issue continues.
- [`mdps_streaming_and_backpressure_2026_05_07.md`](../mdps_streaming_and_backpressure_2026_05_07.md) — plan-of-record
  needing the body refresh.
- [`live_pipeline_mtds_mdps_features_2026_05_08.md`](../live_pipeline_mtds_mdps_features_2026_05_08.md) Phase 4 — the
  downstream consumer of this work.
- UTL@`ac6e3244` — the UTL primitives shipped 2026-05-09; this issue is the consumer-wire-in side that did NOT ship.
