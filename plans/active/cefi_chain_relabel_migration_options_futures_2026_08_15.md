---
doc_type: plan
title: CeFi options_chain/futures_chain path-position entity-rename migration
summary: >-
  Sequenced migration plan for "chain relabel migration part 2 of 2" — options_chain/futures_chain are UAC DataType
  members but are currently written into the instrument_type= GCS path segment (data_type= carries the literal "trades")
  across market-tick-data-service, unified-api-contracts (incl. the canonical-path oracle itself),
  market-data-processing-service, deployment-api, and deployment-ui. Drafted per operator ruling on BLK-f5cd6b22
  (2026-08-15) — a genuine cross-repo entity-rename plus a live production GCS data move with unmeasured blast radius,
  not a mechanical 1-hour fix, so it was scoped as a phased plan rather than a single AO-dispatched todo. Re-verified
  current and flipped to AO-dispatched (`assigned_vm: planning`) 2026-08-17 per operator ruling; phase gating enforced
  via `sequential: true` plus an explicit dispatchable Phase-3→4 gate todo (see Progress Log).
status: active
nature: design
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts, market-data-processing-service, deployment-api, deployment-ui]
scope: [engineer]
tags: [cefi, entity-rename, chain-relabel, options-chain, futures-chain, migration, canonical-path, delete-safety]
related:
  [
    /plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md,
    /plans/active/data_pipeline_alert_storm_ops_ao_dispatch_2026_08_15.md,
    /plans/active/cefi_chain_relabel_migration_options_futures_2026_08_15_finalize.md,
    /plans/archive/2026_08/cefi_satellite_ao_dispatch_batch19_2026_08_13.md,
    /codex/02-data/entity-rename-and-split-consumer-migration-rule.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
created: "2026-08-15"
last_updated: "2026-08-20"
# was: cefi_master (epic-assignment audit 2026-08-19) -- root cause + fix are a shared UAC canonical-path-oracle + MTDS-writer/MDPS-reader partition-path bug (options_chain/futures_chain landing in the wrong path segment), proven in this doc's own Phase 1/2 commits to hit CeFi and TradFi identically (build_cefi_partition_path AND build_tradfi_partition_path, CEFI_CHAIN_INSTRUMENT_TYPES AND TRADFI_CHAIN_INSTRUMENT_TYPES both widened in the same commits) -- would look identical for any asset group sharing this bundle-shard shape
parent_epic: mtds_mdps_master
assigned_vm: planning
execution_scope: orchestrator-agent
sequential: true
priority: P1
estimate_class: design
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 3.6
locked_by:
locked_since:
context_scope:
  [
    /codex/02-data/entity-rename-and-split-consumer-migration-rule.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    unified-api-contracts/unified_api_contracts/canonical/_partition_path_canonicality.py,
    unified-api-contracts/unified_api_contracts/canonical/partition_paths.py,
    market-tick-data-service/market_tick_data_service/engine/orchestrator/partitioned_writer.py,
    /plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md,
  ]
supersedes:
superseded_by:
depends_on: []
source: >-
  Escalated via BLK-f5cd6b22 (2026-08-15, slot-28·backend_engineer) out of
  cefi_satellite_ao_dispatch_batch19_2026_08_13.md's "Chain relabel migration part 2 of 2" todo, itself sourced from
  data_pipeline_alert_storm_root_cause_batch_2026_08_10.md:332-338 (todo #9). Operator ruling on the blocked question
  (2026-08-15): scope down to a phased plan, default assigned_vm: NA given the cross-repo blast radius and
  canonical-oracle change, do not resolve the move-vs-copy tactical question outside the plan's own drafting.
  SUPERSEDED 2026-08-17: na-eligibility-audit follow-up Q&A round 2 (2026-08-16, recorded in
  data_pipeline_alert_storm_ops_ao_dispatch_2026_08_15.md) ruled "re-verify plan is current, then dispatch
  execution" — re-verification found every Phase 1/2 file:line citation still accurate against live state despite
  4 intervening MTDS commits + 1 UAC-adjacent commit (none touched the cited chain-relabel code paths); assigned_vm
  flipped to planning accordingly (see Progress Log for full evidence).
assigned_role: backend_engineer
effort: high
drift_direction: advance-code
---

# CeFi options_chain/futures_chain path-position entity-rename migration

> **Why this WAS a separate LOCAL plan (2026-08-15), and why it is now AO-dispatched (2026-08-17)**: the source todo
> bundled a genuine 5-repo entity-rename (writer, the canonical-path oracle itself, adapters, the whole
> data-status/catalogue stack, UI) with a live production GCS data move over "6+ years" of vintage data and no measured
> blast radius — too much for a 1-hour, single-worker, unattended task, so it was drafted as a phased LOCAL plan.
> `entity-rename-and-split-consumer-migration-rule.md` requires every consumer to migrate in the SAME change. See
> `cefi_satellite_ao_dispatch_batch19_2026_08_13.md`'s todo item for the full investigation this plan was drafted from
> (file:line citations for every consumer below). **2026-08-17 update**: the operator's na-eligibility-audit follow-up
> Q&A round 2 (2026-08-16) explicitly ruled to dispatch this plan's execution once re-verified current — see the
> Progress Log. Per-phase gating stays enforced via `sequential: true` plus the explicit Phase-3→4 dispatchable gate
> todo below: `task_template.md` documents that a bare `sequential: true` chain SKIPS a non-ingested `[OPERATOR]` todo
> when computing "immediate predecessor," so Phase 3's `[OPERATOR]` backfill todo alone cannot be trusted to block
> Phase 4 — the gate todo closes that specific hole. Phase 3's live GCS move/delete still requires the operator per its
> own `[OPERATOR]` tag and the delete-safety protocol; only the plan's DISPATCH READINESS changed, not who may execute
> a destructive step.

## Consumer inventory (entity-rename rule step 1 — already compiled, 2026-08-15 investigation)

The bug, confirmed: `options_chain`/`futures_chain` (UAC `DataType` members,
`unified-api-contracts/unified_api_contracts/internal/domain/market_data_processing/candle_schema.py:92-93`) are written
into the `instrument_type=` GCS path segment; `data_type=` carries the literal `"trades"`.

1. **market-tick-data-service** (writer + manifest) — `engine/orchestrator/partitioned_writer.py:179-225` (`_get_writer`
   passes the raw itype string as `instrument_type=`; `data_type` column defaults to `"trades"` at lines 338-340);
   `engine/orchestrator/symbol_rules.py:160-162,218-220,288,385-395,481-539` (classification + dispatch to UAC builders,
   `_MERGED_DATA_TYPE_MAP` never remaps to `data_type=`); manifest mirrors the same drift at
   `engine/orchestrator/manifest_finalize.py::_write_bundle_shard_row` (lines 164-313, `base_row_key` at 255-265,
   comment at 360-379 explaining the CeFi/Tardis normalization to `"trades"`).
2. **unified-api-contracts** — path builders `canonical/partition_paths.py::build_cefi_partition_path` (219-302) /
   `build_tradfi_partition_path` (320-) construct the wrong shape. **Critically, the canonical-path ORACLE currently
   VALIDATES the wrong shape as correct**: `canonical/_partition_path_canonicality.py:61`
   (`CEFI_CHAIN_INSTRUMENT_ TYPES`) and `:70` (`TRADFI_CHAIN_INSTRUMENT_TYPES`) both list
   `{"options_chain","futures_chain","combo_chain"}` as valid `instrument_type` values, consumed by
   `canonical_path_violations()` (`:503`). A writer-only fix trips this gate the OTHER way — the oracle must migrate as
   part of this plan, not as an afterthought.
3. **market-data-processing-service** — chain adapters `app/adapters/cefi/options_chain_adapter.py` /
   `futures_chain_adapter.py` (routing already fixed part-1, `market-data-processing-service@93d783df`, keys off the
   `instrument_type=` segment authoritatively); `schemas/output_schemas.py:307,314,321` hardcoded
   `applies_to={"options_chain","futures_chain"}`; `app/core/output_path_helpers.py:31` `is_chain_bundle_data_type`.
4. **deployment-api** — `services/data_status_hierarchical.py`, `services/data_status_drilldown/*`,
   `routes/data_status/{_distinct_values,_axis_census,_downloads,_query_meta,_live_coverage}.py`,
   `services/shard_detail/_shard_core.py`, `utils/path_combinatorics.py`, `services/deploy_missing.py`.
5. **deployment-ui** — `src/components/DataStatusTab.tsx`, `DataStatusDrilldown.tsx`, `ShardDetailModal.tsx`,
   `src/lib/mock-api.ts`.

**Blast radius: NOT YET MEASURED anywhere in the corpus.** The only existing figure is qualitative ("affecting every
vintage", "6+ years of good data", `data_pipeline_alert_storm_root_cause_batch_2026_08_10.md` ~line 21). Phase 4's first
todo below measures this before any destructive action.

**What was NOT checked (entity-rename rule step 4, stated explicitly)**: whether `deployment-ui`'s components actually
branch on path-position client-side, vs. purely rendering whatever the backend returns (would need zero UI change) —
flagged as a to-verify in Phase 3's UI todo below, not assumed either way.

## Todos

### Phase 0 — resolve the move-vs-copy tactical question (must close before Phase 4 is scheduled, not before drafting)

- [x] ✅ [DATA] P0. **RESOLVED 2026-08-17 (slot 20, data_engineering) — reconciling reading (a), no fresh operator
      ruling needed.** Determined the operator's actual reasoning behind "move, don't copy-then-delete-separately"
      (`data_pipeline_alert_storm_root_cause_batch_2026_08_10.md:335`, dated 2026-08-10). See Progress Log for the full
      search trail and resolved backfill strategy.

### Phase 1 — UAC canonical layer (must land before Phase 2; the oracle is the SSOT every other repo trusts)

- [x] ✅ [BACKEND] P1. Extend `unified-api-contracts/unified_api_contracts/canonical/partition_paths.py`'s
      `build_cefi_partition_path`/`build_tradfi_partition_path` (or add sibling builders) so `options_chain`/
      `futures_chain` can be emitted at the `data_type=` segment while `instrument_type=` carries the real underlying
      instrument type instead of the literal `"trades"` placeholder. — unified-api-contracts@1a6fc193d9. Both builders'
      chain-bundle (v6 tail) detection now triggers off EITHER `instrument_type` OR `data_type` being in
      `CEFI_CHAIN_INSTRUMENT_TYPES`/`TRADFI_CHAIN_INSTRUMENT_TYPES`, so a caller can pass the corrected shape
      (`data_type="options_chain"`/`"futures_chain"`, `instrument_type="option"`/`"future"`) and still get the
      `underlying=/quote=/margin=/ticks.parquet` tail — legacy-shape callers (`instrument_type=options_chain`,
      `data_type="trades"`) are byte-identical to before (no regression). Added 3 new unit tests
      (`test_cefi_v6_chain_bundle_corrected_shape`, `test_cefi_v6_chain_corrected_shape_without_all_axes_falls_back_to_flat`,
      `test_tradfi_partition_path_chain_v6_corrected_shape`) pinning the corrected-shape output; all 46+89 existing
      `test_partition_paths.py`/`test_partition_path_is_canonical.py` tests still pass unmodified.
      `quality-gates.sh` green. Scope note: this todo is the BUILDER change only — `_partition_path_canonicality.py`'s
      oracle widening (dual-acceptance) and the regression tests pinning that dual-acceptance are the next two
      Phase-1 todos below, left untouched here per task scope.
- [x] ✅ [BACKEND] P1. Widen `_partition_path_canonicality.py`'s oracle (`CEFI_CHAIN_INSTRUMENT_TYPES` /
      `TRADFI_CHAIN_INSTRUMENT_TYPES` + `canonical_path_violations()`) to accept BOTH the legacy shape
      (`instrument_type=options_chain`) and the corrected shape (`data_type=options_chain`) as canonical for a
      transitional dual-acceptance window — do NOT reject the legacy shape yet; Phase 4's backfill hasn't run. —
      unified-api-contracts@b96b28927f. `_cefi_chain_tail_violations` and `_tradfi_path_violations` now detect
      chain-ness off EITHER `instrument_type` (legacy) OR `data_type` (corrected), both routing to the v6
      `underlying=/quote=/margin=/ticks.parquet` tail check. Also fixed a real tradfi misclassification bug this
      widening exposed: the corrected shape's `instrument_type` (`"future"`/`"option"`) is ALSO a
      `TRADFI_SINGLE_INSTRUMENT_TYPES` member, so routing on chain-ness FIRST (before falling through to the
      single-instrument-id check) is what stops a corrected-shape chain shard's symbol-less `ticks.parquet` fan-in
      from getting a false single-instrument-id violation. `_stem_id_form_violations` widened the same way (checks
      `data_type` too) for symmetry on the degenerate non-`ticks.parquet` v5-fallback edge case. Added 6 new unit
      tests (`test_cefi_chain_v6_tail_corrected_shape_is_never_flagged`,
      `test_cefi_chain_bare_v5_tail_corrected_shape_is_flagged`, `test_tradfi_chain_corrected_shape_is_canonical`,
      `test_tradfi_chain_corrected_shape_bare_tail_is_flagged` + 2 parametrized cases); all 135 pre-existing
      `test_partition_paths.py`/`test_partition_path_is_canonical.py` tests still pass unmodified (141 total).
      `quality-gates.sh` green. Scope note: the dedicated dual-acceptance + negative-control regression-test todo
      below is separate — my tests here cover this todo's own change, not that todo's full negative-control
      requirement.
- [x] ✅ [BACKEND] P1. Add regression tests pinning dual-acceptance (both shapes pass `canonical_path_violations()` during
      the window) plus a negative control (a third, made-up shape still fails). `quality-gates.sh` green. —
      unified-api-contracts@4e4a772bfd. Added `test_cefi_chain_dual_acceptance_pins_both_shapes_canonical` +
      `test_tradfi_chain_dual_acceptance_pins_both_shapes_canonical` (pin the EXACT empty-list
      `canonical_path_violations() == []` return for BOTH the legacy shape, `instrument_type=<chain-token>`, and the
      corrected shape, `data_type=<chain-token>`, cefi + tradfi, `options_chain`/`futures_chain`) plus
      `test_cefi_chain_third_made_up_shape_still_fails` (negative control: an invented `options_bundle` token — neither
      blessed shape — is not chain-detected, routes to the ordinary single-instrument id-form check, and is correctly
      rejected for a non-canonical-id filename). All 3 new tests pass; existing 141 `test_partition_paths.py`/
      `test_partition_path_is_canonical.py` tests unmodified. `quality-gates.sh` green
      (`.qg_last_passed_sha=4e4a772bfdf55336dbf38aeb0cbb62e75a044362`).

### Phase 2 — writer + adjacent consumers migrate together (gated on Phase 1 landing)

- [x] ✅ [BACKEND] P1. market-tick-data-service: switch `PartitionedTickWriter`/`symbol_rules.py`/`manifest_finalize.py` to
      emit the corrected shape for all NEW writes going forward (existing GCS objects/manifest rows at the old shape are
      untouched by this todo — Phase 4 handles them). Regression test asserting a fresh options_chain/ futures_chain
      write lands at the corrected path + manifest coordinates. — market-tick-data-service@5389036c31 (+ follow-up
      market-tick-data-service@5c98f404c8 fixing a line-cap regression from the first commit). CeFi's raw
      `instrument_type` (still the chain token, upstream Tardis adapters unchanged) is swapped with `data_type` (real
      schema value) at write time via `_corrected_chain_write_shape`/`_resolve_chain_write_context`
      (`chain_partition_dims.py`); TradFi's parallel bug fixed too (`_DATA_TYPE_TO_INSTRUMENT_TYPE` previously
      duplicated the chain token into `instrument_type` instead of resolving the real type). Chain-shard detection
      made symmetric (`_is_chain_shard`, either axis) across `_get_writer`/`_write_group`/`venue_fetch.py`/
      `manifest_finalize.py`/`_cluster_bookkeeping.py` so both legacy and corrected shapes are recognized during the
      dual-acceptance window; `_resolve_partition_data_type` no longer merges a genuine chain-bundle
      `options_chain`/`futures_chain` `data_type` value into a shared partition (previously collapsed the two
      distinct corrected-shape data_types together, defeating the migration). `combo_chain` explicitly out of scope
      (never mislabeled the same way). New regression tests:
      `tests/unit/test_partitioned_writer_cefi_chain_relabel_corrected_shape.py` (fresh options_chain/futures_chain
      writes land at the corrected path + shard-atom; combo_chain unaffected); updated 2 pre-existing
      `test_partitioned_writer_cluster_counts.py` assertions to the corrected atom. Full `quality-gates.sh` green
      (11025 passed, `.qg_last_passed_sha=5c98f404c83f8035b100b88dee9b5682ec65ddcd`).
- [x] ✅ [BACKEND] P1. market-data-processing-service: update `options_chain_adapter.py`/`futures_chain_adapter.py` +
      `output_schemas.py`'s hardcoded `applies_to` sets + `output_path_helpers.py::is_chain_bundle_data_type` to
      recognize the corrected shape IN ADDITION to the legacy shape (historical data still needs to resolve until Phase
      4 completes). — market-data-processing-service@bef6495bed. **Investigation found the real functional gap was
      NOT in the 3 named files** — all three already recognize both shapes by construction (see Progress Log for the
      full evidence trail): they operate exclusively on the canonical LOGICAL `data_type` (the value
      `CandleAdapterRegistry` keys on and `CandleOutput.data_type` carries, always `"options_chain"`/`"futures_chain"`
      regardless of which raw on-disk shape a shard was read from), never on the raw source
      `instrument_type=`/`data_type=` path segments. The actual gap was one level upstream:
      `orchestration_scanner.py::_blob_matches_data_type_partition` — MDPS's raw-tick file-DISCOVERY matcher — only
      matched the legacy shape (`instrument_type={data_type}/`), so a freshly-written corrected-shape shard
      (`data_type=options_chain/`, real type at `instrument_type=option/`) would never enter the candidate set at
      all, and the 3 named files (already shape-agnostic) would simply never be reached for that shard. Fixed to
      match EITHER segment. 2 new regression tests
      (`test_chain_type_matches_corrected_data_type_segment`,
      `test_futures_chain_type_matches_corrected_data_type_segment`) in `test_orchestration_scanner_coverage.py`.
      Full `quality-gates.sh` green (2462 passed, 2 skipped, `.qg_last_passed_sha=bef6495bed60e95462ede20b5dec463971ce13aa`).
- [x] ✅ [BACKEND] P1. deployment-api: update the data-status/catalogue stack (files listed in the consumer inventory
      above) to read/aggregate both shapes as the same logical entity during the migration window — a shard must not
      appear to double-count or vanish depending on which shape it's currently in. — deployment-api@2a1e504afc. New
      shared `deployment_api.utils.chain_bundle_shapes` module (dual-shape detection + alternate-axes resolution,
      `combo_chain` explicitly out of scope). Fixed: `data_status_hierarchical.py` normalizes legacy `data_type`
      ("trades") to the chain token so the drilldown TREE merges both shapes into one `data_type` node (the exact
      double-count/vanish failure mode); `shard_detail/_shard_core.py::_mtds_shard_path` now probes the alternate
      shape on a miss (also fixed a pre-existing `is_derivative_bundle` AND-vs-OR bug that meant neither pure shape's
      v6 bundle tail was ever correctly detected — found investigating this todo, fixed same file/commit);
      `data_status_drilldown/_instruments.py::_list_instruments_full` gets a dual-shape prefix fallback so a shard
      doesn't "vanish" from the per-instrument listing, and `_bundling_mode` now takes `data_type` so a
      corrected-shape bundle classifies `per_underlying` (not `per_symbol`); `path_combinatorics.py`'s
      `CombinatoricEntry.to_gcs_prefixes` emits the alternate-shape prefix for options_chain/futures_chain combos
      only (no widening of the rest of the combinatorics matrix — efficiency north-star). 26 new unit tests across
      5 test files; full `quality-gates.sh` green (`.qg_last_passed_sha=2a1e504afcf74a632790d424524539ff7158d35e`).
      **Explicitly NOT fixed (documented, not silently left)**: `get_shard_info`/`_collect_instrument_types`
      (`_instruments.py`) enumerates raw `instrument_type=` path segments without filtering by `data_type` — a
      pre-existing gap (its own docstring's claim of per-`data_type` scoping doesn't match its actual GCS-prefix
      scan) that predates this migration; during the dual-shape window it will list a corrected-shape bundle's real
      type (`option`/`future`) as a distinct entry alongside any genuine single-instrument TradFi `option`/`future`
      data for the same venue/day, which this todo's scope didn't extend to disambiguating. `routes/data_status/*.py`
      (`_distinct_values.py`/`_axis_census.py`/`_downloads.py`/`_query_meta.py`/`_live_coverage.py`) were checked and
      confirmed to be thin passthroughs with no independent chain-bundle prefix-building/aggregation logic of their
      own — no code change needed there; they inherit the fix via the services they call.
- [x] ✅ [UI] P2. **VERIFIED pure passthrough — no client-side chain path-position assumption found, no code
      change needed.** Read/grepped all 4 named deployment-ui files in full: `DataStatusTab.tsx` (7019 lines),
      `DataStatusDrilldown.tsx` (1355 lines), `ShardDetailModal.tsx` (554 lines), `mock-api.ts` (7062 lines).
      `DataStatusTab.tsx` carries exactly ONE `options_chain`/`futures_chain` literal in the whole file (a comment
      at line 5629) and ZERO `instrument_type ===`/`data_type ===` value comparisons anywhere; every
      `instrument_type:` value it forwards to `openShardDetail`/`InstrumentsModal`/`SchemaModal` is either the
      sentinel `"AUTO"`/`""` (defers resolution to the backend or a user picker) or `itName`/`match.instrument_type`
      sourced directly from a backend-supplied per-venue `instrument_types` array or search-match record — never
      derived by testing `data_type` against a chain token. The "Per-underlying breakdown (options_chain /
      futures_chain)" UI section renders `it.underlyings`, a dict the backend already computed and shaped.
      `DataStatusDrilldown.tsx`'s `isBundled = listing?.bundling === "per_underlying"` is driven by a
      backend-returned `bundling` field, not client-side instrument_type/data_type inspection; its own comment
      documents that CeFi instrument_type disambiguation (perpetual vs. options_chain) goes through a `/shard-info`
      backend call + a user picker, never a client guess. `ShardDetailModal.tsx`'s header comment states the branch
      is "driven by `shard_class` in the response; the UI does not infer" — confirmed: zero chain-token literals
      anywhere in the file. `mock-api.ts`'s only `options_chain`/`futures_chain`/`combo_chain` references live
      inside `_mkCefiMtdsHonest()`'s MOCK FIXTURE data arrays (seeding a realistic shape for local dev/Playwright),
      not route-handler logic. No deployment-ui commit — nothing to ship; this plan-doc flip is the complete
      evidence trail. See Progress Log for the full method.
- [x] ✅ [BACKEND] P2. market-data-processing-service: `app/utils/path_parsing.py::blob_matches_canonical_instrument_id_stems`
      fixed. — market-data-processing-service@88db2842f9. Two changes were needed, not one: (1)
      `blob_matches_canonical_instrument_id_stems`'s direct `instrument_type=` branch now falls through to
      `_tradfi_chain_bundle_match` whenever the blob filename is a chain-bundle (`_is_chain_bundle_filename`),
      regardless of whether the direct segment half-matched — closes the originally-described gap. (2) **Investigation
      found `_tradfi_chain_bundle_match` itself was NOT actually bundle-shape-complete as the todo's own text assumed**:
      it only ever checked the LEGACY `instrument_type={chain_token}/` segment (e.g. `instrument_type=options_chain/`)
      — for the corrected shape the chain token lives at `data_type=`, not `instrument_type=` (confirmed against
      `unified-api-contracts`'s `build_tradfi_partition_path` docstring: corrected-shape order is
      `instrument_type={real_type}/data_type={chain_token}/underlying=.../ticks.parquet`), so even after fix (1) a
      corrected-shape bundle still failed to match. Widened `_tradfi_chain_bundle_match` to check EITHER
      `instrument_type={itype}/` OR `data_type={itype}/`, mirroring the "either axis" dual-shape-acceptance pattern
      used throughout this migration (UAC's `is_chain` detection, MDPS's own `orchestration_scanner.py` whole-day
      fix). 4 new regression tests in `tests/unit/test_path_parsing_chain_bundle_match.py` (corrected-shape OPTION/
      FUTURE bundle match via fallthrough, non-bundle direct-hit unaffected — no regression, a genuinely-wrong
      underlying still correctly misses). Full `quality-gates.sh` green (2128 passed,
      `.qg_last_passed_sha=88db2842f99a454b727b5deee6b87cb088637c22`).

### Phase 3 — backfill existing GCS objects + manifest rows (gated on Phase 0's decision AND Phase 2 landing; delete-safety-gated)

- [ ] [OPERATOR] P1. Measure the actual blast radius first (a dry-run/count-only mode over the manifest and a GCS
      listing) — no existing count exists anywhere in the corpus. Then write + dry-run a backfill script implementing
      Phase 0's resolved strategy: per legacy-shape object, compute the corrected-shape target, copy (or the resolved
      move-semantics) + verify (checksum) + update the manifest row at the corrected coordinates, and only delete the
      legacy-shape object under `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`. Tagged `[OPERATOR]`: this
      deletes production data across 6+ years of vintage shards with no established reversibility check yet (finding
      T/U's carve-outs don't apply until a fresh soft-delete-retention check is run and cited). Cite the measured
      count + the dry-run result before requesting `--apply` approval.

### Phase 4 — close out (gated on Phase 3 completing + verifying zero remaining legacy-shape rows)

- [ ] [DATA] P1. **Dispatch gate — do not skip.** `sequential: true` alone does NOT hold this boundary: Phase 3's
      `[OPERATOR]` todo is excluded from AO ingestion, so the sequential chain's "immediate predecessor" computation
      SKIPS it and would otherwise make this Phase 4 dispatchable the moment Phase 2 lands
      (`plans/active/task_template.md` § 4, "`sequential: true` only orders ... ingested/dispatchable todos"). This
      todo is the real, dispatchable gate: query the manifest (+ a scoped GCS listing) for any remaining legacy-shape
      (`instrument_type=options_chain`/`futures_chain`/`combo_chain`) rows or objects. If ANY remain, Phase 3's
      backfill has not finished — `skip-current-task` with `reason_code: GATED` (per `worker.md` § 4c) rather than
      proceeding; do NOT narrow the oracle while legacy-shape data still exists in production, or every untouched
      legacy-shape shard starts failing `canonical_path_violations()`. If zero remain, record the verifying query +
      zero-count here and this todo is done — Phase 4 may proceed.
- [ ] [BACKEND] P2. Narrow `_partition_path_canonicality.py`'s oracle back to ONLY the corrected shape (remove
      legacy-shape acceptance), completing the entity-rename per the "shard atom identical across writer/manifest/
      status/gate/UI" discipline.
- [ ] [DOC] P2. Add/update a codex SSOT documenting the corrected options_chain/futures_chain path shape (candidate: a
      new subsection in the cefi canonical-naming doc, or a new standalone doc if none exists yet).
- [ ] [DOC] P2. Flip the citing todo in `data_pipeline_alert_storm_root_cause_batch_2026_08_10.md` (todo #9) and
      `cefi_satellite_ao_dispatch_batch19_2026_08_13.md`'s redirected todo, citing this plan + final evidence. Run the
      standard 6-step archival ritual on this plan once all phases are done.

## Progress Log

- **context-scout 2026-08-17**: populated/refreshed context_scope (6 entries)
- **2026-08-15 (slot-28·backend_engineer)**: drafted this plan per operator ruling on `BLK-f5cd6b22` (scope the
  chain-relabel migration down from a single AO todo into a phased LOCAL plan; default `assigned_vm: NA`; do not resolve
  the move-vs-copy question outside the plan's own drafting). Consumer inventory + file:line citations carried over from
  this session's 2-pass Explore-agent investigation (see the source todo's own Progress Log entry in
  `cefi_satellite_ao_dispatch_batch19_2026_08_13.md` for the raw investigation transcript). No code changed.
- **na-eligibility-audit 2026-08-16** [body-hash:d9dd38ca14bec7be]: KEEP-NA, valid — Read the full 183-line doc end-to-end (single Read, no truncation) plus cross-checked the redirect chain.
- **2026-08-17 (slot 1, data_engineering, AO-dispatched via `data_pipeline_alert_storm_ops_ao_dispatch_2026_08_15.md`)**:
  Re-verified this plan against live state per the operator's na-eligibility-audit follow-up Q&A round 2 ruling
  ("re-verify plan is current, then dispatch execution"). **Result: still current.** Checked every cited file for
  post-draft (>2026-08-15) commits: UAC's `partition_paths.py`/`_partition_path_canonicality.py` had ZERO commits
  since the draft — `build_cefi_partition_path`/`build_tradfi_partition_path` still at lines 219/320,
  `CEFI_CHAIN_INSTRUMENT_TYPES`/`TRADFI_CHAIN_INSTRUMENT_TYPES` still at lines 61/70, `canonical_path_violations`
  still at line 503, all exactly as cited. MTDS had 4 intervening commits touching the 3 cited orchestrator files
  (`bd07cfc3`, `ecedb15f`, `83948068`, `28e2eb36`) but none touched the chain-relabel code paths this plan cites —
  `_write_bundle_shard_row` still at line 164, `_MERGED_DATA_TYPE_MAP` still at line 160 — confirmed by reading each
  commit's diff (sports `data_type` sanitization, `quarantined_legs` threading, a new Stage-3 read-gate function, and
  a per-date concurrency fix — all additive/orthogonal, none touched the `instrument_type=`/`data_type=` chain-relabel
  logic). MDPS's chain adapters + deployment-api's data-status stack: zero commits since draft. deployment-ui: one
  commit (`080ceb8`) touched only `DataStatusTab.tsx` (coverage-breakdown + asset-group toggle UI, unrelated to
  path-position rendering) — Phase 2's UI todo is unaffected. **Dispatch-readiness change**: flipped
  `assigned_vm: NA` → `planning`, `execution_scope: local-only` → `orchestrator-agent`, added `sequential: true`.
  Before doing so, read `task_template.md` § 4 in full and found a real hazard: a bare `sequential: true` chain skips
  non-ingested todos (incl. `[OPERATOR]`-tagged ones) when computing the predecessor, so Phase 3's `[OPERATOR]`
  backfill todo would NOT actually have blocked Phase 4 from dispatching right after Phase 2 landed — closed by
  inserting an explicit dispatchable `[DATA] P1` gate todo at the top of Phase 4 that checks for zero remaining
  legacy-shape rows and self-defers via `skip-current-task reason_code=GATED` otherwise (see Phase 4). Authored the
  required companion finalize plan per the "every AO-dispatched plan needs a gated finalize plan" hard rule:
  `cefi_chain_relabel_migration_options_futures_2026_08_15_finalize.md`. **Also found**: the citing todo in
  `data_pipeline_alert_storm_ops_ao_dispatch_2026_08_15.md` tagged this work `(repo: instruments-service)` — wrong;
  this plan touches none of instruments-service, and its real repos are the 5 in this doc's own `repos:` frontmatter.
  Flipped that checkbox with the corrected repo list as part of this same session.
- **2026-08-17 (slot 20, data_engineering) — Phase 0 move-vs-copy tactical question RESOLVED, reading (a).** Searched
  the corpus for the operator's stated rationale behind "move, don't copy-then-delete-separately"
  (`data_pipeline_alert_storm_root_cause_batch_2026_08_10.md:335`): grepped every
  `unified-trading-pm/plans/active/issues/autonomous_session_operator_decisions_*.md` file, every `BLK-*` id logged
  against 2026-08-10 across `plans/active/issues/` and `plans/archive/` (~80 hits), and every doc created 2026-08-10 —
  none reference this specific decision. The source doc's own frontmatter explains why: its `source:` line records
  "Interactive session 2026-08-10 ... Operator decisions recorded inline" — this was a live chat instruction during an
  ad-hoc session, not a structured `/blocked` ruling (no `BLK-*` id) or a Slack post, so no deeper transcript exists
  anywhere in the corpus to recover — the cited line IS the complete primary source. This confirms option (b)'s
  "no record found" branch for the SEARCH half, but a fresh operator ruling is not actually needed here because the
  task's own reconciling-reading example — already drafted into this exact todo by the 2026-08-16
  na-eligibility-audit/dispatch session — resolves the apparent conflict without contradicting either side: **"copy +
  content-verify (checksum) + delete inside the SAME script run" satisfies both the operator's framing (the end state
  is a MOVE — no legacy-shape duplicate survives the run) and the `backfill_defi_dex_pool_swaps_source_correction.py`
  precedent's safety rationale (GCS has no atomic move primitive; a bare move risks data loss on partial failure, so
  the underlying mechanics are always copy-then-verify-then-delete regardless of what the combined operation is
  called).** Read that precedent script in full
  (`market-data-processing-service/scripts/backfill_defi_dex_pool_swaps_source_correction.py:1-73`): it also
  deliberately does NOT delete the source at all (`ALREADY_COVERED`/gap-fill only, ADDITIVE not a migration) — a
  genuinely different shape from this migration's requirement (Phase 3 must actually retire the legacy-shape object
  once its corrected-shape twin is copy+verified), so its "copy-not-move" framing was never in tension with "move" as
  a description of Phase 3's overall operation; it was only ever in tension with a naive interpretation of "move" as a
  single atomic GCS call, which GCS does not offer and which
  `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`'s Part 5 (the legacy-COPIED-not-MOVED invariant) already
  forbids skipping regardless of this todo. **Resolved backfill strategy for Phase 3**: per legacy-shape object, copy
  to the corrected-shape target (`gcs_copy_object`), content-verify (checksum per Part 2 of the delete-safety
  protocol — not existence-only), update the manifest row at the corrected coordinates, THEN delete the legacy-shape
  object via `gcs_conditional_delete` scoped to the verified generation (per the five-part proof + §3a reversibility
  check) — all within the same script/session, so the net observable effect is a move (nothing legacy-shaped survives
  once the run completes) while the mechanics stay the always-required copy-verify-delete sequence. This does not
  change Phase 3's `[OPERATOR]` tag, its delete-safety gating, or its blast-radius-measurement requirement — only
  confirms the backfill script's shape before it is written. No code changed by this todo.
- **2026-08-17 (slot 4, backend_engineer) — Phase 2 MDPS todo done, market-data-processing-service@bef6495bed.**
  Investigated the 4 named consumers (`options_chain_adapter.py`, `futures_chain_adapter.py`,
  `output_schemas.py`'s `applies_to` sets, `output_path_helpers.py::is_chain_bundle_data_type`) by tracing the actual
  variable threading, not just grepping for the token: `data_type` reaches all 4 as the canonical LOGICAL request name
  (`"options_chain"`/`"futures_chain"` — the same value `CandleAdapterRegistry.get_adapter(data_type=...)` keys on and
  `CandleOutput`'s own `data_type` field always carries), never the raw source `instrument_type=`/`data_type=` GCS path
  segments. Confirmed via `live_workers_chain.py::_resolve_chain_adapter_data_type`'s docstring + logic (the "already
  fixed part-1" routing cited in this plan's consumer inventory) — it normalizes BOTH shapes to the same logical
  `data_type` BEFORE any of the 4 named files ever see it. So none of the 4 needed a code change; verified with an
  explicit trace, not assumed.
  **Found the real gap one level upstream**: `orchestration_scanner.py::_blob_matches_data_type_partition` — the
  raw-tick file-DISCOVERY matcher that decides which blobs even become read/routing candidates — checked ONLY
  `instrument_type={data_type}/` (the legacy on-disk shape). Since MTDS's Phase 2 writer todo
  (`market-tick-data-service@5389036c31`) now emits the corrected shape (`data_type=options_chain/`, real type at
  `instrument_type=option/`) for fresh writes, this matcher would silently never discover any freshly-written
  corrected-shape shard — it never enters the candidate set, so the (already shape-agnostic) adapter/schema/path-helper
  logic never gets a chance to run on it. Fixed to accept EITHER `instrument_type={data_type}/` OR
  `data_type={data_type}/`. 2 new regression tests in `test_orchestration_scanner_coverage.py` pin both
  options_chain and futures_chain corrected-shape blobs as discoverable. Full `quality-gates.sh` green (2462 passed,
  2 skipped, `.qg_last_passed_sha=bef6495bed60e95462ede20b5dec463971ce13aa`).
  **What was NOT fixed (tracked as a new Phase 2 P2 todo above, not silently left)**: `path_parsing.py`'s
  `blob_matches_canonical_instrument_id_stems` (the TradFi instrument-id-filtered backfill matcher — a distinct code
  path from the whole-day scanner fixed here) has a related gap: its direct `instrument_type=` branch now half-matches
  the corrected shape's real-type segment but then fails the per-instrument-stem filename check (bundle files are
  `ticks.parquet`, not `{stem}.parquet`), short-circuiting before ever reaching the chain-bundle underlying-root
  matcher that would actually resolve it correctly. Left as a distinct, correctly-scoped follow-up rather than folded
  into this commit, since fixing it requires reordering the function's branches (a different, riskier change) and this
  plan's own todo scope named MDPS's chain-ADAPTER consumers, not the TradFi instrument-id-filter path.
  **Also fixed (this file, same commit)**: the prior Phase 2 MTDS todo's `<repo>@<sha>` citations swapped the two
  commits and cited an unresolvable SHA — `plan-hygiene`'s commit-SHA-evidence check caught this when I staged the
  file. Verified against `market-tick-data-service`'s real history: the FIRST commit ("emit corrected shape") is
  `5389036c31` (was mis-cited as `5c98f404c8`), and the follow-up line-cap fix is `5c98f404c8` (was mis-cited as the
  non-existent `6e06fe17`) — its message literally reads "shrink writer to 900-line cap", confirming the swap. Fixed
  both citations plus the QG sentinel SHA at the same todo, and my own new Progress Log entry above which had copied
  the same wrong SHA before I caught it.
- **2026-08-17 (slot 23, backend_engineer) — Phase 2 deployment-api todo done, deployment-api@2a1e504afc.** See the
  checkbox annotation above for the full change list + explicit not-fixed scope. Also fixed a QG false-positive this
  work exposed: the new `_probe_mtds_shard_axes` helper inserted above `_shard_core.py::_manifest_row_for_coord`
  shifted that pre-existing, already-baselined bare `read_availability_index` call from line 525 to 565 —
  re-pointed the line-keyed baseline entry (`unified-trading-pm@b7131a09a0`, direct-pushed per the GATE-INFRA
  `scripts/quality_gates/` carve-out) so the ratchet check keeps recognizing it instead of misreporting it as new.
- **2026-08-17 (slot 1, ui_developer craft) — Phase 2 UI todo done, verification-only.** Read every named
  deployment-ui file end-to-end (`DataStatusDrilldown.tsx` + `ShardDetailModal.tsx` in full via Read;
  `DataStatusTab.tsx` 7019L and `mock-api.ts` 7062L too large for one Read — swept with `rg` for
  `options_chain|futures_chain|combo_chain` literals and `instrument_type`/`data_type` `===`/`!==` comparisons
  across each whole file, then read every hit's surrounding code rather than grep-then-conclude). Found zero
  client-side path-position branching in any of the four: `DataStatusTab.tsx`'s two `itGuess` sites (lines
  5909/5949) turned out to be unrelated to CeFi chains — they resolve a PREDICTION/Polymarket "OTHER"-bucket
  sentinel (`name.toUpperCase() === "POLYMARKET" ? "OTHER" : "AUTO"`), not an instrument_type/data_type value
  check; every other `instrument_type:` assignment site (`match.instrument_type` from a backend search-match
  record at lines 1244/1255, `itName` from a backend-supplied per-venue `instrument_types` array at lines
  5594/5618/5693/5718) is backend-sourced, never computed by testing which axis carries the chain token.
  `DataStatusDrilldown.tsx`'s bundling decision (`isBundled`) and `ShardDetailModal.tsx`'s tab rendering
  (`shard_class`) are both explicitly backend-driven by design (the latter's own header comment says so).
  `mock-api.ts`'s chain-token references are confined to `_mkCefiMtdsHonest()`'s fixture-seed arrays. Matches
  the plan's own prediction ("likely... per deployment-api already normalizing"). No deployment-ui code changed;
  this plan-doc commit is the only artifact.
- **2026-08-17 (slot 15, backend_engineer) — Phase 2 MDPS follow-up todo done, market-data-processing-service@88db2842f9.**
  See the checkbox annotation above for the full change list. Key finding beyond the todo's own description: the
  todo's text assumed `_tradfi_chain_bundle_match` "DOES handle bundles correctly" once reached — investigation
  showed that was only true for the LEGACY shape; the corrected shape needed a second, distinct fix (checking
  `data_type=` in addition to `instrument_type=` for the chain token) before the fallthrough alone would actually
  resolve a corrected-shape bundle. Caught this by writing the regression tests FIRST against the real
  `build_tradfi_partition_path` segment order (confirmed via UAC docstring, not assumed) and watching them fail
  after only the branch-order fix — the fallthrough alone was insufficient. `quality-gates.sh` green.
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
