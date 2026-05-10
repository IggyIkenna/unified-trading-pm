---
title: Wave-2 — Polymarket / Kalshi record_captured_from_counts proper SSOT migration
type: sub-plan
status: planned
created: 2026-05-09
deadline: post-cutover (target 2026-06-15)
horizon: scope-bounded
companion_to: plans/epics/predictions_master_2026_05_07.md
migrated_from: predictions_master_2026_05_07.md Q2/A2 option δ
locked_by: live-defi-rollout
locked_since: 2026-05-09
---

# Wave-2 — Polymarket / Kalshi `record_captured_from_counts` proper SSOT migration

## What this is

Successor plan for the option α decision shipped 2026-05-09 in
`predictions_master_2026_05_07.md` Q2/A2 (option δ = ship α now + open
this Wave-2). Option α mirrors the CME-OPTIONS legacy `add()` path at
[`market_tick_data_service/engine/orchestrator.py:2295-2356`](../../../market-tick-data-service/market_tick_data_service/engine/orchestrator.py#L2295-L2356)
to bundle Polymarket / Kalshi prediction shards by
`canonical_question_group` at the manifest layer without restructuring
the streaming-finalize architecture. This is **technical debt**: it
bypasses the `BUNDLED_DATA_TYPES` `record_captured` gate at
[`unified-trading-library/unified_trading_library/manifest_writer.py:2122-2128`](../../../unified-trading-library/unified_trading_library/manifest_writer.py#L2122-L2128)
that CLAUDE.md "Cluster validation MANDATORY" mandates for every bundled
shard.

This plan migrates the workspace from the legacy `add()` path to a
unified UTL helper `record_captured_from_counts(...)` that accepts
counts + an `available_at_envelope` instead of a pandas DataFrame, so
streaming writers (PartitionedTickWriter et al) can satisfy the gate
without reconstructing per-row dfs at finalize time.

**Why deferred**: option α is the pragmatic ship-now choice for the
2026-05-23 live-DeFi cutover. Proper SSOT cleanup is a multi-day
cross-cutting design (UTL contract change + every bundled-shard
callsite migration + QG STEP 5.64 update) that doesn't fit cutover
window. Per CLAUDE.md "Temporary state must have a named successor
plan" rule, this file IS that named successor.

## Composes with

- [`predictions_master_2026_05_07.md`](../epics/predictions_master_2026_05_07.md) Q2/A2 — option α writer-side
  collection half (MTDS@a1edc18) + finalize-loop branch (item 1b deferred to this Wave-2).
- [`writegate_honest_coverage_endtoend_2026_05_06.md`](writegate_honest_coverage_endtoend_2026_05_06.md) — Phase 1A
  cluster validation gate (the gate this Wave-2 makes streaming-writer-friendly).
- CLAUDE.md "Cluster validation MANDATORY at `record_captured` for bundled shards" (the workspace SSOT).
- CLAUDE.md "No double SSOT in data-saving methodology" (the rule that bans the legacy `add()` path long-term).

## Phases

### Phase 1 — UTL helper authoring (P0, ~1 AI-day)

- [x] [SCRIPT] P0. Author `unified_trading_library.manifest_writer.ManifestWriter.record_captured_from_counts(...)`
      accepting `(row_key, total_rows, expected_root_clusters, cluster_extractor, observed_clusters, available_at_envelope)`
      kwargs instead of a pandas DataFrame. Internally calls the existing `_check_cluster_coverage` private gate +
      `assert_available_at_present` on the envelope timestamp + writes the manifest row. 8+ unit tests covering: full
      coverage success, under-coverage → `record_failed(ClusterCoverageError)`, missing envelope → `LookaheadBiasError`,
      empty observed → `record_empty`, BUNDLED_DATA_TYPES enforcement.
      Shipped UTL@ef47c81b — 11 unit tests at `tests/unit/test_manifest_writer_record_captured_from_counts.py` cover
      full-coverage success, under-coverage routing, None/NaT/naive envelope, total_rows=0 → `record_empty(SOURCE_RETURNED_ZERO)`,
      unknown row_key column, multiple-call idempotency, non-UTC tz acceptance, feature_group sibling-presence guard,
      attempted_at honored.
      status: done

### Phase 2 — Deprecation banner on legacy `add()` (P0, ~0.5 AI-day)

- [ ] [SCRIPT] P0. Add a deprecation `DeprecationWarning` to `ManifestWriter.add()` for any call where the data_type is
      in `BUNDLED_DATA_TYPES` — points at `record_captured_from_counts` as the replacement. Helper logs the call-site
      file:line so callsite migration is mechanical.
      status: todo
      note: ""

### Phase 3 — MTDS callsite migration (P0, ~1-2 AI-days)

- [x] [SCRIPT] P0. Migrate the prediction finalize-loop branch (item 1b from F5-v2 spawn — currently deferred from
      MTDS@a1edc18) to use `record_captured_from_counts` from the start. Walks `self._prediction_cluster_counts` +
      `self._prediction_available_at_max` + emits one bundled manifest row per `canonical_question_group` per
      `(processing_date, venue)`. 4+ unit tests covering: full coverage HOURLY (24 markets), partial coverage DAILY (1
      market), ELECTION single-market, lifecycle-bounded skip.
      Shipped MTDS@a2f8d80 — per-venue accumulators (`prediction_cluster_counts_by_venue` +
      `prediction_envelope_by_venue`) populated from `PartitionedTickWriter` properties; finalize-loop branch emits
      one bundled `data_type=prediction_canonical_question_group` row per `(canonical_question_group, processing_date,
      venue)` via UTL@ef47c81b `record_captured_from_counts`. Envelope = `max(per-row available_at) +
      emission_latency_ms_for_source("polymarket_clob")` (200ms). 5 unit tests at
      `tests/unit/test_polymarket_bundling_finalize.py` cover full-coverage HOURLY (24 markets), partial-coverage
      DAILY → `record_failed`, ELECTION single-market, lifecycle-bounded skip, non-prediction writers leave
      accumulators empty. **TEMPORARY**: expected market_id set = observed until MARKET_LIFECYCLE wiring ships per
      `predictions_master_2026_05_07` Phase 1.
      status: done

- [ ] [SCRIPT] P0. Migrate the CME-OPTIONS legacy callsite at
      [`market_tick_data_service/engine/orchestrator.py:2295-2356`](../../../market-tick-data-service/market_tick_data_service/engine/orchestrator.py#L2295-L2356)
      from `check_cluster_coverage_from_counts → record_failed | add` to a single
      `record_captured_from_counts` call. Same shape, cleaner SSOT. Tests already exist for the CME-OPTIONS
      branch; verify they still pass post-migration.
      status: todo
      note: ""

- [ ] [SCRIPT] P1. Audit the workspace for any other callsite that uses `ManifestWriter.add()` with a bundled data_type
      (`grep -rn "manifest.add\|writer.add\|writer_manifest.add" --include="*.py"` across MTDS / instruments-service /
      features-* / strategy-service / e2e-testing). Migrate every one. Reviewers reject any remaining `add()` callsite
      for bundled data_types after this phase ships.
      status: todo
      note: ""

### Phase 4 — Legacy `add()` deletion + QG enforcement (P0, ~1 AI-day)

- [ ] [SCRIPT] P0. Delete the legacy `ManifestWriter.add()` method entirely. Per CLAUDE.md "No double SSOT" rule — once
      every callsite uses `record_captured_from_counts`, the parallel path goes. Update UTL `__all__` exports.
      status: todo
      note: ""

- [ ] [SCRIPT] P0. Update QG STEP 5.64 (the AST-walk that asserts `record_captured(` callsites pass `expected_root_clusters`
      + `cluster_extractor` for bundled data_types) to additionally assert NO callsite uses `ManifestWriter.add()` for
      any data_type — `add()` is gone, so any remaining import = error. CI fails on any leftover.
      status: todo
      note: ""

### Phase 5 — Codex SSOT updates (P0, ~0.5 AI-day)

- [ ] [SCRIPT] P0. Update CLAUDE.md "Cluster validation MANDATORY at `record_captured`" section to remove the
      Polymarket / Kalshi option-α carve-out (added 2026-05-09; carve-out cites this Wave-2 as named successor). Update
      `codex/02-data/availability-manifest-and-data-status.md` to document `record_captured_from_counts` as the
      streaming-writer companion to `record_captured`. Update
      `codex/04-architecture/shard-level-failure-isolation.md` if it references the legacy `add()` path.
      status: todo
      note: ""

## Done definition

- ✅ UTL `ManifestWriter.add()` method deleted; `record_captured_from_counts` is the only path for bundled-shard
  manifest emission from streaming writers.
- ✅ Every bundled-shard callsite in MTDS uses `record_captured_from_counts` (Polymarket + Kalshi + CME-OPTIONS minimum;
  Phase 3 P1 audit catches any others).
- ✅ QG STEP 5.64 enforces: any `ManifestWriter.add()` callsite = CI failure.
- ✅ CLAUDE.md option-α carve-out section removed.
- ✅ All affected codex docs updated per the Post-Plan-Phase Codex Audit HARD RULE.

## Full-execution criterion

Per CLAUDE.md "Plans Run To Actual Completion, Not Smoke-Test Green":

- ✅ Run a 1-day backfill against `BTC_UP_DOWN_HOURLY` AFTER Phase 3 ships, verify the bundled manifest row uses the
  new helper path (event-stream tag + manifest schema spot-check). Cite GCS URI + sample row in the close-out.
- ✅ Workspace-wide `grep -rn "ManifestWriter.add\|manifest.add\|writer.add\|writer_manifest.add"` returns ZERO matches
  in production source after Phase 4 ships.

## Anti-patterns

- **Don't** keep `add()` around as a "compatibility shim" — per CLAUDE.md § 3 No Technical Debt, clean breaks only.
  The whole point of this Wave-2 is to eliminate the double SSOT.
- **Don't** ship Phase 4 before Phase 3 P1 audit completes — deleting `add()` without migrating every callsite breaks
  the workspace.
- **Don't** treat this plan as urgent during May-23 cutover prep — option α is correctness-equivalent for the cutover
  window. This Wave-2 is post-cutover hygiene.
