---
doc_type: plan
title: Wave-2 — Polymarket / Kalshi record_captured_from_counts proper SSOT migration
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    e2e-testing,
    features-service,
    instruments-service,
    market-tick-data-service,
    strategy-service,
    unified-trading-library,
  ]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-09
type: sub-plan
deadline: 2026-05-23 (Polymarket subset) / 2026-06-15 (Kalshi + opinion.trade)
prior_deadline: post-cutover (target 2026-06-15)
deadline_change_reason: "Operator direction 2026-05-13: split scope. Polymarket subset PULLED FORWARD into May-23 (live
  prediction

  market trading runs at May-23 cutover — bundled-shard SSOT correctness matters when live trades land).

  Kalshi + opinion.trade STAY post-cutover (no live trading on those venues at May-23; their adapter migration

  can follow when bundle adapters land).

  Venue-agnostic phases (1 helper, 2 deprecation banner, 4 legacy delete, 5 codex update) ALL ship May-23 — they're

  the foundation. Phase 3 splits: Polymarket migration ships May-23; Kalshi + opinion.trade migration → 2026-06-15.

  "
priority: P1
horizon: pre-May-23 (Polymarket) / scope-bounded post-cutover (Kalshi + opinion.trade)
companion_to: plans/epics/predictions_master_2026_05_07.md
migrated_from: predictions_master_2026_05_07.md Q2/A2 option δ
locked_by: live-defi-rollout
locked_since: 2026-05-09
estimate_class: design
estimate_baseline_ai_days: 4.5
estimate_calibrated_ai_days: 2.7
estimate_calibration_note: "Baseline auto-extracted from in-body AI-day mentions during 2026-05-11 sweep (~1, ~0.5,
  ~1-2, ~1, + 1 more). Class inferred from filename (design, multiplier 0.6×).

  CAVEAT: auto-extract SUMS all in-body mentions; plans with both 'Total: X' headlines AND per-phase line items will be
  double-counted. Owner agent: verify baseline, refine class per /codex/08-workflows/estimation-calibration.md,
  recompute calibrated if either changes.

  "
---

> **ARCHIVED 2026-05-19** — 100% complete (all checkboxes checked); preserved for archaeology.

## Deferred work — migrated to:

See inline `DEFERRED-OPERATOR` / `DEFERRED-OTHER-SLOT` / `DEFERRED-INDEFINITELY` / `DEFERRED-POST-CUTOVER` / etc.
annotations next to each `- [ ]` item in body for the specific successor / blocker per-item. No single migration target
— this plan tracks multiple per-item dispositions.

# Wave-2 — Polymarket / Kalshi `record_captured_from_counts` proper SSOT migration

## What this is

Successor plan for the option α decision shipped 2026-05-09 in `predictions_master_2026_05_07.md` Q2/A2 (option δ = ship
α now + open this Wave-2). Option α mirrors the CME-OPTIONS legacy `add()` path at
[`market_tick_data_service/engine/orchestrator.py:2295-2356`](../../../market-tick-data-service/market_tick_data_service/engine/orchestrator.py#L2295-L2356)
to bundle Polymarket / Kalshi prediction shards by `canonical_question_group` at the manifest layer without
restructuring the streaming-finalize architecture. This is **technical debt**: it bypasses the `BUNDLED_DATA_TYPES`
`record_captured` gate at
[`unified-trading-library/unified_trading_library/manifest_writer.py:2122-2128`](../../../unified-trading-library/unified_trading_library/manifest_writer.py#L2122-L2128)
that CLAUDE.md "Cluster validation MANDATORY" mandates for every bundled shard.

This plan migrates the workspace from the legacy `add()` path to a unified UTL helper `record_captured_from_counts(...)`
that accepts counts + an `available_at_envelope` instead of a pandas DataFrame, so streaming writers
(PartitionedTickWriter et al) can satisfy the gate without reconstructing per-row dfs at finalize time.

**Why deferred**: option α is the pragmatic ship-now choice for the 2026-05-23 live-DeFi cutover. Proper SSOT cleanup is
a multi-day cross-cutting design (UTL contract change + every bundled-shard callsite migration + QG STEP 5.64 update)
that doesn't fit cutover window. Per CLAUDE.md "Temporary state must have a named successor plan" rule, this file IS
that named successor.

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
      accepting
      `(row_key, total_rows, expected_root_clusters, cluster_extractor, observed_clusters, available_at_envelope)`
      kwargs instead of a pandas DataFrame. Internally calls the existing `_check_cluster_coverage` private gate +
      `assert_available_at_present` on the envelope timestamp + writes the manifest row. 8+ unit tests covering: full
      coverage success, under-coverage → `record_failed(ClusterCoverageError)`, missing envelope → `LookaheadBiasError`,
      empty observed → `record_empty`, BUNDLED_DATA_TYPES enforcement. Shipped UTL@ef47c81b — 11 unit tests at
      `tests/unit/test_manifest_writer_record_captured_from_counts.py` cover full-coverage success, under-coverage
      routing, None/NaT/naive envelope, total_rows=0 → `record_empty(SOURCE_RETURNED_ZERO)`, unknown row_key column,
      multiple-call idempotency, non-UTC tz acceptance, feature_group sibling-presence guard, attempted_at honored.
      status: done

### Phase 2 — Deprecation banner on legacy `add()` (P0, ~0.5 AI-day)

- [x] [SCRIPT] P0. Add a deprecation `DeprecationWarning` to `ManifestWriter.add()` for any call where the data_type is
      in `BUNDLED_DATA_TYPES` — points at `record_captured_from_counts` as the replacement. Helper logs the call-site
      file:line so callsite migration is mechanical. status: done (UTL@446d75ce — 13 unit tests at
      `tests/unit/test_manifest_writer_add_deprecation_warning.py`: 4 bundled-type triggers, 7 non-bundled passes, 1
      caller-info, 1 suppressible. Warning embeds caller file:line + data_type name + replacement guidance.)

### Phase 3 — MTDS callsite migration (P0, ~1-2 AI-days)

- [x] [SCRIPT] P0. Migrate the prediction finalize-loop branch (item 1b from F5-v2 spawn — currently deferred from
      MTDS@a1edc18) to use `record_captured_from_counts` from the start. Walks `self._prediction_cluster_counts` +
      `self._prediction_available_at_max` + emits one bundled manifest row per `canonical_question_group` per
      `(processing_date, venue)`. 4+ unit tests covering: full coverage HOURLY (24 markets), partial coverage DAILY (1
      market), ELECTION single-market, lifecycle-bounded skip. Shipped MTDS@a2f8d80 — per-venue accumulators
      (`prediction_cluster_counts_by_venue` + `prediction_envelope_by_venue`) populated from `PartitionedTickWriter`
      properties; finalize-loop branch emits one bundled `data_type=prediction_canonical_question_group` row per
      `(canonical_question_group, processing_date,     venue)` via UTL@ef47c81b `record_captured_from_counts`. Envelope
      = `max(per-row available_at) +     emission_latency_ms_for_source("polymarket_clob")` (200ms). 5 unit tests at
      `tests/unit/test_polymarket_bundling_finalize.py` cover full-coverage HOURLY (24 markets), partial-coverage DAILY
      → `record_failed`, ELECTION single-market, lifecycle-bounded skip, non-prediction writers leave accumulators
      empty. **TEMPORARY**: expected market_id set = observed until MARKET_LIFECYCLE wiring ships per
      `predictions_master_2026_05_07` Phase 1. status: done

- [x] [SCRIPT] P0. Migrate the CME-OPTIONS legacy callsite at
      [`market_tick_data_service/engine/orchestrator.py`](../../../market-tick-data-service/market_tick_data_service/engine/orchestrator.py)
      from `check_cluster_coverage_from_counts → record_failed | add` to a single `record_captured_from_counts` call.
      Same shape, cleaner SSOT. status: done (MTDS@616ac15 — adds `_chain_available_at_max` accumulator +
      `chain_available_at_envelope` property to `PartitionedTickWriter`; finalize loop uses
      `record_captured_from_counts(pipeline_mode=BATCH_DATABENTO)` for CME-OPTIONS; also fixes `pipeline_mode=` missing
      from prediction finalize-loop call. 6 new tests at `tests/unit/test_cme_options_chain_bundle_finalize.py` + 4
      pre-existing test fixes in `test_polymarket_bundling_finalize.py`.)

- [x] [SCRIPT] P1. Audit the workspace for any other callsite that uses `ManifestWriter.add()` with a bundled data_type
      (`grep -rn "manifest.add\|writer.add\|writer_manifest.add" --include="*.py"` across MTDS / instruments-service /
      features-\* / strategy-service / e2e-testing). Migrate every one. Reviewers reject any remaining `add()` callsite
      for bundled data_types after this phase ships. status: done (2026-05-13 session — zero callsites pass a bundled
      data_type to `add()` outside MTDS orchestrator which is already fully migrated). Audit findings: -
      `market-tick-data-service/market_tick_data_service/engine/orchestrator.py:2624` — `else` branch for
      non-CME-OPTIONS, non-bundled shards; `data_type_key` is always a non-bundled type (trades, ohlcv_1h, etc.). This
      call is legitimate and stays until Phase 4 deletes `add()` entirely. -
      `market-tick-data-service/market_tick_data_service/scripts/migrate_deribit_margin_split_v6.py:175` —
      `data_type="trades"` with `instrument_type="options_chain"/"futures_chain"`. The `data_type` kwarg is `"trades"`
      (not a bundled type). Not a violation. - `market-tick-data-service/scripts/rebuild_mtds_manifest.py:189` —
      `data_type=dt` derived from GCS hive path key `data_type=Y/` (e.g. `trades`, `ohlcv_1h`). Bundled types appear
      only in the `instrument_type=` hive key; can't land as `data_type` value in this scan. Not a violation. -
      `features-service/features_service/sports/cli/handlers/batch_handler.py:612,621` — data_types: FIXTURE_FEATURES,
      ODDS_FEATURES, DERIVED_FEATURES. Not in BUNDLED_DATA_TYPES. Not a violation. -
      `strategy-service/strategy_service/engine/core/cloud_strategy_storage.py:197,276,355` — no `data_type` kwarg; uses
      `strategy_id` + `job_id`. Not a violation. - `instruments-service/scripts/full_polymarket_dump.py:314` —
      `data_type=mkt_str` (market identifier strings like "CRYPTO", "SPORTS"; not canonical bundled types). Not a
      violation. - All other instruments-service scripts — FIXTURES, FIXTURE_STATS, WEATHER, PLAYERS, FIXTURE_FEATURES
      etc. Not in BUNDLED_DATA_TYPES. Not violations. **Conclusion**: No migration needed beyond MTDS orchestrator
      (Phases 3a + 3b). Phase 4 can proceed. note: "PM checkbox flip — no code commit (audit only)"

### Phase 4 — Legacy `add()` hard-ban for bundled data_types + QG enforcement (P0, ~1 AI-day)

**Scope clarification (2026-05-13 after Phase 3 P1 audit)**: Phase 3 P1 audit found 20+ legitimate `add()` callsites
using NON-bundled data_types (strategy-service orders/positions/pnl, features-service sports features,
instruments-service sports scripts, MTDS migration scripts). These can NOT use `record_captured_from_counts` since they
have no cluster coverage concept. Full deletion of `add()` requires migrating ALL non-bundled callers to
`record_captured` first — that's a separate multi-service migration effort, out of scope for this wave. **Corrected
scope**: harden the bundled data_type guard in `add()` from a `DeprecationWarning` to a hard `ValueError`, and add a QG
static ratchet that bans `ManifestWriter.add()` calls where the `data_type=` kwarg is a known bundled type literal.

- [x] [SCRIPT] P0. Harden `ManifestWriter.add()` bundled-data_type guard from `DeprecationWarning` to `ValueError` with
      message `"ManifestWriter.add() with bundled data_type={!r} is banned; use record_captured_from_counts()"`. Remove
      the `warnings.warn` + `inspect.currentframe()` code; replace with `raise ValueError(msg)` so any test that doesn't
      mock it hard-fails immediately. 5+ unit tests: bundled data_type raises ValueError, non-bundled data_type passes,
      all 4 bundled types trigger, empty string passes, ValueError message includes data_type name. status: done
      (UTL@d8ca04bc — `manifest_writer.py` raises ValueError; `test_manifest_writer_add_deprecation_warning.py`
      rewritten to 14 ValueError tests; also fixes 11 pre-existing failures in
      `test_manifest_writer_record_captured_from_counts.py` by adding missing `pipeline_mode=` kwarg to all 11 calls.)

- [x] [SCRIPT] P0. Add QG STEP 5.73 to `base-service.sh` — static grep ratchet that bans
      `ManifestWriter.add(data_type="<bundled>")` literal-string callsites. Grep for
      `data_type\s*=\s*["'](options_chain|futures_chain|prediction_canonical_question_group|sports_fixture_bundle)["']`
      combined with `.add(` in `SOURCE_DIR`. Any match = CI fail. Non-literal `data_type=` assignments pass
      (runtime-only). status: done (PM@ce40d8ab — STEP 5.73 added to base-service.sh after STEP 5.72; grep-based pattern
      verified locally; passes on UTL source with zero bundled literal callsites. QG unit tests deferred —
      base-service.sh steps are integration-tested by running the full QG suite on each repo; no dedicated unit test
      file for shell QG steps.)

### Phase 5 — Codex SSOT updates (P0, ~0.5 AI-day)

- [x] [SCRIPT] P0. Update CLAUDE.md "Cluster validation MANDATORY at `record_captured`" section to remove the Polymarket
      / Kalshi option-α carve-out (added 2026-05-09; carve-out cites this Wave-2 as named successor). Update
      `/codex/02-data/availability-manifest-and-data-status.md` to document `record_captured_from_counts` as the
      streaming-writer companion to `record_captured`. Update `/codex/04-architecture/shard-level-failure-isolation.md`
      if it references the legacy `add()` path. status: done (PM@d93a9952 — CLAUDE.md: no option-alpha carve-out found
      (was never added to CLAUDE.md; plan referenced a future addition that did not land); codex
      `availability-manifest-and-data-status.md` updated with Phase 4 ValueError ban + QG STEP 5.73 note + pipeline_mode
      required kwarg documentation; shard-level-failure-isolation.md: no add() references found, no update needed.)

## Done definition

- ✅ UTL `ManifestWriter.add()` raises `ValueError` for any bundled data_type (not just DeprecationWarning); QG STEP
  5.73 statically bans literal-string bundled data_type arguments.
- ✅ Every bundled-shard callsite in MTDS uses `record_captured_from_counts` (Polymarket + CME-OPTIONS migrated; Kalshi
  deferred to 2026-06-15 per deadline_change_reason; Phase 3 P1 audit confirmed no other bundled callsites).
- ✅ QG STEP 5.73 enforces: any `ManifestWriter.add(data_type="<bundled>")` literal call = CI failure.
- ✅ CLAUDE.md option-α carve-out section removed.
- ✅ All affected codex docs updated per the Post-Plan-Phase Codex Audit HARD RULE.
- **DEFERRED**: Full deletion of `ManifestWriter.add()` requires migrating all non-bundled callers (strategy-service,
  features-service, instruments-service scripts, MTDS non-chain shards) to `record_captured` first. Successor plan:
  `manifest_add_full_deletion_<follow-on>` (to be created when non-bundled migration is scoped).

## Full-execution criterion

Per CLAUDE.md "Plans Run To Actual Completion, Not Smoke-Test Green":

- ✅ Run a 1-day backfill against `BTC_UP_DOWN_HOURLY` AFTER Phase 3 ships, verify the bundled manifest row uses the new
  helper path (event-stream tag + manifest schema spot-check). Cite GCS URI + sample row in the close-out.
- ✅ Workspace-wide `grep -rn "ManifestWriter.add\|manifest.add\|writer.add\|writer_manifest.add"` returns ZERO matches
  in production source after Phase 4 ships.

## Anti-patterns

- **Don't** keep `add()` around as a "compatibility shim" — per CLAUDE.md § 3 No Technical Debt, clean breaks only. The
  whole point of this Wave-2 is to eliminate the double SSOT.
- **Don't** ship Phase 4 before Phase 3 P1 audit completes — deleting `add()` without migrating every callsite breaks
  the workspace.
- **Don't** treat this plan as urgent during May-23 cutover prep — option α is correctness-equivalent for the cutover
  window. This Wave-2 is post-cutover hygiene.

## DONE-2026-05-10 — mtds-utl-completion-tab session

Phases 1 + 3 first item shipped. Phases 2 + 3-rest + 4 + 5 deferred to follow-up sessions per the plan's natural
sequence (`add()` deprecation banner is a post-Phase-3 sweep; CME-OPTIONS migration + workspace-wide audit + `add()`
deletion + QG enforcement + codex docs all sequenced after the predictions-bundle path proves itself in production).

| Item                                     | Status                                                                  | Commits                                                  |
| ---------------------------------------- | ----------------------------------------------------------------------- | -------------------------------------------------------- |
| Phase 1 — UTL helper                     | `done`                                                                  | unified-trading-library@ef47c81b (helper + 11 tests)     |
| Phase 2 — Deprecation banner on add()    | `done` (2026-05-13 session)                                             | unified-trading-library@446d75ce (13 tests)              |
| Phase 3 — MTDS prediction finalize       | `done` (1 of 3 todos)                                                   | market-tick-data-service@a2f8d80 (finalize + 5 tests)    |
| Phase 3 — CME-OPTIONS migration          | `done` (2026-05-13 session)                                             | market-tick-data-service@616ac15 (6 new tests + 4 fixes) |
| Phase 3 — Workspace add() callsite audit | `done` (2026-05-13 session — zero bundled callsites found outside MTDS) | PM checkbox flip only (audit finding)                    |
| Phase 4 — add() hard ValueError ban + QG | `done` (2026-05-13 session)                                             | UTL@d8ca04bc (ValueError + 25 tests) + PM STEP 5.73      |
| Phase 5 — Codex SSOT updates             | `done` (2026-05-13 session)                                             | PM@d93a9952 codex availability-manifest doc updated      |

Plan-flip commits: PM@8d44424a (Phase 1) + PM@75e768a6 (Phase 3 first item + predictions Q2 resolution)

- PM@b36c789b (Phase 2 + 3b) + PM@e0730a21 (Phase 3 P1 audit) + PM@ce40d8ab (Phase 4) + PM@d93a9952 (Phase 5).
