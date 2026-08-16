---
doc_type: plan
title: CeFi options_chain/futures_chain path-position entity-rename migration
summary: >-
  Sequenced migration plan for "chain relabel migration part 2 of 2" — options_chain/futures_chain are UAC DataType
  members but are currently written into the instrument_type= GCS path segment (data_type= carries the literal "trades")
  across market-tick-data-service, unified-api-contracts (incl. the canonical-path oracle itself),
  market-data-processing-service, deployment-api, and deployment-ui. Drafted per operator ruling on BLK-f5cd6b22
  (2026-08-15) — this is a genuine cross-repo entity-rename plus a live production GCS data move with unmeasured blast
  radius, not a mechanical 1-hour fix, so it is scoped here as a phased LOCAL plan (assigned_vm: NA) rather than a
  single AO-dispatched todo.
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
    /plans/active/cefi_satellite_ao_dispatch_batch19_2026_08_13.md,
    /codex/02-data/entity-rename-and-split-consumer-migration-rule.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
created: "2026-08-15"
last_updated: "2026-08-15"
parent_epic: cefi_master
assigned_vm: NA
execution_scope: local-only
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
    /plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md,
    unified-api-contracts/unified_api_contracts/canonical/_partition_path_canonicality.py,
    unified-api-contracts/unified_api_contracts/canonical/partition_paths.py,
    market-tick-data-service/market_tick_data_service/engine/orchestrator/partitioned_writer.py,
    market-tick-data-service/market_tick_data_service/engine/orchestrator/manifest_finalize.py,
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
assigned_role: backend_engineer
effort: high
drift_direction: advance-code
---

# CeFi options_chain/futures_chain path-position entity-rename migration

> **Why this is a separate LOCAL plan, not an AO todo**: the source todo bundled a genuine 5-repo entity-rename (writer,
> the canonical-path oracle itself, adapters, the whole data-status/catalogue stack, UI) with a live production GCS data
> move over "6+ years" of vintage data and no measured blast radius.
> `entity-rename-and-split- consumer-migration-rule.md` requires every consumer to migrate in the SAME change; that is
> not a 1-hour, single- worker, unattended task. See `cefi_satellite_ao_dispatch_batch19_2026_08_13.md`'s todo item for
> the full investigation this plan was drafted from (file:line citations for every consumer below).

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

- [ ] [DATA] P0. Determine the operator's actual reasoning behind "move, don't copy-then-delete-separately"
      (`data_pipeline_alert_storm_root_cause_batch_2026_08_10.md:335`, dated 2026-08-10) for THIS migration
      specifically, vs. the general copy-then-verify-then-delete precedent in
      `market-data-processing-service/scripts/backfill_defi_dex_pool_swaps_source_correction.py` (copy-only, delete as a
      separate later delete-safety-gated step, because GCS has no atomic move and a bare move risks data loss on partial
      failure). Grep `unified-trading-pm/plans/active/issues/autonomous_session_operator_decisions_*.md` and any
      Slack/blocked-question history around 2026-08-10 for the stated rationale. Produce one of: (a) a reconciling
      reading (e.g. "copy + crc32c-verify + delete inside the SAME script run IS what 'move' meant colloquially here —
      satisfies both"), or (b) an explicit unresolved-conflict flag requesting a fresh operator ruling before Phase 4 is
      scheduled. Done when: this plan's Progress Log records the resolved backfill strategy with its source citation (or
      the explicit "no record found, re-asked, operator said X" trail).

### Phase 1 — UAC canonical layer (must land before Phase 2; the oracle is the SSOT every other repo trusts)

- [ ] [BACKEND] P1. Extend `unified-api-contracts/unified_api_contracts/canonical/partition_paths.py`'s
      `build_cefi_partition_path`/`build_tradfi_partition_path` (or add sibling builders) so `options_chain`/
      `futures_chain` can be emitted at the `data_type=` segment while `instrument_type=` carries the real underlying
      instrument type instead of the literal `"trades"` placeholder.
- [ ] [BACKEND] P1. Widen `_partition_path_canonicality.py`'s oracle (`CEFI_CHAIN_INSTRUMENT_TYPES` /
      `TRADFI_CHAIN_INSTRUMENT_TYPES` + `canonical_path_violations()`) to accept BOTH the legacy shape
      (`instrument_type=options_chain`) and the corrected shape (`data_type=options_chain`) as canonical for a
      transitional dual-acceptance window — do NOT reject the legacy shape yet; Phase 4's backfill hasn't run.
- [ ] [BACKEND] P1. Add regression tests pinning dual-acceptance (both shapes pass `canonical_path_violations()` during
      the window) plus a negative control (a third, made-up shape still fails). `quality-gates.sh` green.

### Phase 2 — writer + adjacent consumers migrate together (gated on Phase 1 landing)

- [ ] [BACKEND] P1. market-tick-data-service: switch `PartitionedTickWriter`/`symbol_rules.py`/`manifest_finalize.py` to
      emit the corrected shape for all NEW writes going forward (existing GCS objects/manifest rows at the old shape are
      untouched by this todo — Phase 4 handles them). Regression test asserting a fresh options_chain/ futures_chain
      write lands at the corrected path + manifest coordinates.
- [ ] [BACKEND] P1. market-data-processing-service: update `options_chain_adapter.py`/`futures_chain_adapter.py` +
      `output_schemas.py`'s hardcoded `applies_to` sets + `output_path_helpers.py::is_chain_bundle_data_type` to
      recognize the corrected shape IN ADDITION to the legacy shape (historical data still needs to resolve until Phase
      4 completes).
- [ ] [BACKEND] P1. deployment-api: update the data-status/catalogue stack (files listed in the consumer inventory
      above) to read/aggregate both shapes as the same logical entity during the migration window — a shard must not
      appear to double-count or vanish depending on which shape it's currently in.
- [ ] [UI] P2. deployment-ui: verify whether `DataStatusTab.tsx`/`DataStatusDrilldown.tsx`/`ShardDetailModal.tsx`/
      `mock-api.ts` branch on path-position client-side. If they're a pure passthrough of backend-shaped data (likely,
      per deployment-api already normalizing above), state that explicitly and skip; only change code if a real
      client-side assumption is found.

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

- [ ] [BACKEND] P2. Narrow `_partition_path_canonicality.py`'s oracle back to ONLY the corrected shape (remove
      legacy-shape acceptance), completing the entity-rename per the "shard atom identical across writer/manifest/
      status/gate/UI" discipline.
- [ ] [DOC] P2. Add/update a codex SSOT documenting the corrected options_chain/futures_chain path shape (candidate: a
      new subsection in the cefi canonical-naming doc, or a new standalone doc if none exists yet).
- [ ] [DOC] P2. Flip the citing todo in `data_pipeline_alert_storm_root_cause_batch_2026_08_10.md` (todo #9) and
      `cefi_satellite_ao_dispatch_batch19_2026_08_13.md`'s redirected todo, citing this plan + final evidence. Run the
      standard 6-step archival ritual on this plan once all phases are done.

## Progress Log

- **2026-08-15 (slot-28·backend_engineer)**: drafted this plan per operator ruling on `BLK-f5cd6b22` (scope the
  chain-relabel migration down from a single AO todo into a phased LOCAL plan; default `assigned_vm: NA`; do not resolve
  the move-vs-copy question outside the plan's own drafting). Consumer inventory + file:line citations carried over from
  this session's 2-pass Explore-agent investigation (see the source todo's own Progress Log entry in
  `cefi_satellite_ao_dispatch_batch19_2026_08_13.md` for the raw investigation transcript). No code changed.
- **na-eligibility-audit 2026-08-16** [body-hash:d9dd38ca14bec7be]: KEEP-NA, valid — Read the full 183-line doc end-to-end (single Read, no truncation) plus cross-checked the redirect chain.
