---
doc_type: plan
title: CeFi satellite AO batch 1 — conflict-cleared extraction from the 2026-07-25 orphan audit
summary: >-
  First AO-dispatch batch for cefi. Extracted from a 29-doc AO-eligibility triage over every cefi satellite doc not
  covered by cefi_consolidated_closeout_2026_07_18.md / cefi_consolidated_closeout_aggregated_sources_2026_07_24.md. The
  triage found 40 candidate AO-eligible todos across the 29 docs, each cross-checked against every one of that doc's own
  flagged conflicts (40 total) per the operator's 2026-07-25 conflict-check discipline. 38 of the 40 survived review —
  zero-conflict, explicitly declared non-blocking in the triage's own text (code-orthogonal / low-collision-risk /
  not-a-data-safety-risk), already handled inline in the todo's own coordination note, or resolvable by clear logic
  (both sides read-only with no mutation). 3 of the 29 docs were flagged doc_too_large_or_risky_for_batch and excluded
  entirely (1 of their AO-eligible candidates deferred); 1 further candidate (a live GCS rename migration) was excluded
  on cross-doc evidence it is already actively executing via a separate live session. 3 same-doc groups (8 sub-items)
  were combined into 3 todos to avoid an in-batch same-file collision, so the 38 surviving candidates ship here as 33
  todo bullets.
status: active
nature: process
asset_group: [cefi]
stage: [data]
repos:
  [
    market-tick-data-service,
    market-data-processing-service,
    instruments-service,
    deployment-api,
    deployment-service,
    alerting-service,
    unified-trading-library,
    unified-api-contracts,
    unified-trading-pm,
  ]
scope: [engineer]
tags: [cefi, ao-dispatch, close-out, batch-1, satellite-docs, conflict-checked]
related:
  [
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/cefi_consolidated_closeout_aggregated_sources_2026_07_24.md,
    /plans/active/ag_closeout_audit_rollout_2026_07_25.md,
    /plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch1_2026_07_25.md,
    /plans/active/prediction_satellite_ao_dispatch_batch1_2026_07_25.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 2.8
estimate_calibrated_ai_days: 2.2
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  /autonomous session 2026-07-25, driven by the /ag-closeout-audit skill Phase 3 (conflict-checked next-batch drafting)
  after a 29-doc cefi satellite AO-eligibility triage (per-doc ao_eligible_todos / human_only_todos / conflicts_found /
  doc_too_large_or_risky_for_batch captured this session). This doc is the conflict-cleared subset only (33 of 40
  candidates).
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
---

# CeFi satellite AO batch 1 — conflict-cleared extraction

> **Status: draft.** Per CLAUDE.md's plan-destination rule and the ag-closeout-audit skill's autonomous-mode guidance, a
> skill-drafted AO batch is never auto-shipped to `active` — flip this frontmatter's `status` to `active` only after
> operator review. All 33 todos below are same-priority-within-doc and touch distinct files (verified doc-by-doc below;
> 3 same-doc groups were combined specifically to avoid a same-file collision) so they are safe to dispatch concurrently
> once activated. Unlike the tradfi/prediction batch1 precedents (5/43 and 7/9 pass rates), cefi's conflict picture was
> mostly informational/awareness-only rather than literal duplicate-claims against
> cefi_consolidated_closeout_2026_07_18.md's own open todos — every included item's reasoning is spelled out inline
> below as a **Conflict-check note** where a conflict existed at all.

## Todos

- [ ] [DATA] P1. **Extend MDPS candle-building to the 4 on-chain-perp CeFi venues + backfill.** Point MDPS's candle
      scanner/writer (`market-data-processing-service/market_data_processing_service/`) at
      ASTER/HYPERLIQUID/LIGHTER-ZKSYNC/EXTENDED-STARKNET
      (`pipeline_mode=batch_aster`/`batch_hyperliquid`/`batch_lighter_api`/`batch_extended`) so it produces
      `processed_candles/` for them — MTDS already captures their raw trades broadly, MDPS just isn't pointed at them.
      Then backfill `timeframe=24h` candles over each venue's already-captured raw-trade range per the manifest (ASTER
      is 2024-01-01 onward per `plans/archive/issues/aster_capture_broken_coverage_and_completeness_2026_07_20.md`, not
      the UAC-native 2023-07-22 start, until that doc's GAP-4 is separately resolved). SPOT VM backfill per the
      heavy-I/O + SPOT-default infra rules. **Coordination note**: MDPS's `processed_candles/` namespace has other
      independent in-flight work (cefi_consolidated_closeout's Track 1 raw-tick canonical-ID migration and Track 7
      candle bundle-collision residual, both for the EXISTING tardis-sourced venues, not these 4) — confirm neither is
      mid-write on the same code paths/objects before shipping. Repo: market-data-processing-service. **Done when**:
      `processed_candles/` objects with real non-zero `quote_volume` exist for a recent day for each of the 4 venues;
      features-service's `RollingAdvReader.compute_rolling_adv()` returns a non-`NO_DATA` `AdvStatus` for at least one
      probed instrument on one venue; a manifest-verified backfill covers each venue's full already-captured raw-trade
      range. Source: `aster_and_cefi_rolling_adv_feature_2026_07_21.md`.
- [ ] [REVIEW] P1. **Audit cefi MDPS state adapters for leading-NaN routing.** Confirm every cefi state adapter
      (`trades_adapter.py`, `book_snapshot_adapter.py`, `derivative_adapter.py`, `futures_chain_adapter.py`,
      `options_chain_adapter.py`) in market-data-processing-service routes through `_finalize_session_grid`
      (`base_adapter.py:36-624`) so no adapter emits leading-NaN before its first real observation, and confirm
      `liquidations_adapter.py`'s no-grid event-count design is the sole intentional exception (per
      `issues/mdps_state_adapter_leading_nan_audit_2026_05_29.md`). Repo: market-data-processing-service. **Done when**:
      a written per-adapter verdict (routes-through-finalize / intentionally-exempt) is recorded in this plan's Progress
      Log or a new issue doc; any non-routing, non-exempt adapter is filed as a follow-up finding, not silently fixed.
      Source: `data_completion_cefi_2026_07_15.md`.
- [ ] [REVIEW] P1. **Verify MDPS cefi candle-manifest faithfulness.** On a sample day (e.g. 2026-05-03), compare
      `ohlcv_*` manifest-row coverage against actual `processed_candles/` candle-file coverage, and reconcile the
      cross-writes noted in the source doc (782 MTDS-written `ohlcv` rows; 616 MDPS-written `trades` rows) to determine
      which service legitimately emits `ohlcv` per venue (MTDS REST-poll venues like LIGHTER/PACIFICA vs MDPS-processed
      venues). Repos: market-data-processing-service, market-tick-data-service. **Conflict-check note**: this reads the
      same `processed_candles/` corpus as the master closeout's Track 7 149-object bundle-collision residual, but the
      triage's own text calls it "low collision risk (different defect axis)" — a faithfulness/coverage check, not the
      bundle-collision defect Track 7 already quarantined. **Done when**: a written comparison report
      (ohlcv-row-coverage vs candle-file-coverage + cross-write reconciliation) with a PASS/FAIL faithfulness verdict is
      recorded in this plan's Progress Log or a new issue doc; on PASS, the absorbed
      `cefi_processed_candles_manifest_file_disconnect` issue doc is archived per its own closing instruction. Source:
      `data_completion_cefi_2026_07_15.md`.
- [ ] [DATA] P1. **Re-run `cf_manifest_audit.py` against the live cefi manifest, no `--apply`.** Re-run against live
      `instruments-store-cefi-prd-central-element-323112` and report current CF-1/CF-3/CF-4/CF-8 status, null
      `capture_status` %, and blank `data_type` % — the successor doc claims cefi's instruments-store v9 migration is
      "fully migrated" fleet-wide without directly re-confirming these named residuals; this todo produces that direct
      re-confirmation. Repo: unified-trading-library (script) / instruments-service (target data). Do NOT run any
      `--apply`. **Done when**: a fresh CF-1/CF-3/CF-4/CF-8 GREEN/RED verdict with counts, measured against live data,
      is recorded in this plan's Progress Log. Source: `data_completion_cefi_2026_07_15.md`.
- [x] ✅ [BACKEND] P1. **Add a cefi parity regression test for deployment-api's pipeline_mode dedup.** Mirror the
      existing `test_pipeline_mode_rows_do_not_double_count_shards`
      (`deployment-api/tests/unit/test_chain_breakdown_shards_vs_dates.py`, which today only guards the DeFi
      chain-breakdown builder) — assert multiple `pipeline_mode=` rows for one cefi
      `(venue, data_type,     instrument_type, instrument_id, day)` shard atom collapse to ONE counted shard via
      `_shard_atom_cols` derived from the UAC `SHARD_AXIS_MATRIX`. Repo: deployment-api. This is the regression-guard
      half only — the separate `pipeline_mode` drilldown-filter UI feature-add is out of scope. **Done when**: a new
      passing test asserting cefi venue-breakdown pipeline_mode dedup exists in
      `deployment-api/tests/unit/test_venue_breakdown_shards_cefi_dedup.py` (new file); `quality-gates.sh` green.
      Source: `data_completion_cefi_2026_07_15.md`. — deployment-api@51890b3. The cefi shard atom
      `(venue, data_type, instrument_type, instrument_id, day)` is counted in
      `deployment_api/services/data_status/instrument_coverage.py::per_instrument_coverage` via a Python
      `set[tuple[instrument_id, date]]` (`found_pairs`), which already collapses duplicate `pipeline_mode` rows for free
      — unlike the DeFi chain-breakdown builder this needed no `_shard_atom_cols`/`drop_duplicates` fix, only the
      missing regression test. New test
      `TestPerInstrumentCoverageDoesNotDoubleCountPipelineModeRows::test_pipeline_mode_rows_do_not_double_count_shards`
      asserts 2 instruments x 5 dates x 2 pipeline_modes (`batch_binance`/`live_binance`) = 20 raw rows collapse to
      `found_shards == 10` distinct shard atoms. `quality-gates.sh` green (sentinel `cc1403d`), shipped via quickmerge.
- [ ] [DATA] P1. **Re-run the IS cefi reference-data backfill to close the KRAKEN-SPOT/KRAKEN-FUTURES/BITFINEX-SPOT
      gap.** Now that `_DEFAULT_EXCHANGES` derives from the canonical `VenueMapping.all_tardis_exchanges` SSOT (shipped
      `is@a6bc4d48`), re-run `instrument_availability/by_date/` so the IS catalogue's captured-venue set becomes ⊇ the
      MTDS captured present-set. Memory-heavy multi-year sweep — launch on a SPOT VM per the heavy-I/O +
      VM-launcher-runbook rules, sized to avoid the OOM that previously killed `cefi-instr-deribit` (2026-05-04). Repo:
      instruments-service. **Coordination requirement (inline, non-blocking)**: this backfill queries Tardis's
      reference/catalog endpoints — run `tardis-concurrency-guard.sh` to check the live Tardis-VM fleet count FIRST,
      since master closeout's Track-2 raw-tick coverage backfill also claims the hard N=1-concurrent-Tardis-VM cap; do
      not launch both simultaneously. **Done when**: `instrument_availability/by_date/` for a sampled recent day shows
      the previously-missing venues present in the IS reference catalogue, with a measured before/after venue-count and
      row-count delta recorded in this plan's Progress Log. Source: `data_completion_cefi_2026_07_15.md`.
- [x] ✅ [DIAG] P1. **Root-cause the ASTER MTDS `attempted_failed` regression (3,491 → 17,675), evidence-gathering
      only.** (a) Re-run
      `GET /api/data-status/turbo?service=market-tick-data-service&start_date=2018-01-01&end_date=<today>&asset_group=CEFI&include_sub_dimensions=true`
      and record `asset_groups.CEFI.venues.ASTER.failure_pillars.failed_other` + `capture_status_counts` to confirm
      reproducibility; (b) pull the raw manifest rows behind that count from the
      `market-data-tick-cefi-prd-central-element-323112` manifest and record each row's `error_reason`/timestamp to
      determine if they're the SAME rows carried over from the 2026-05-13 incident or genuinely new; (c) check whether
      any manifest index rebuild/consolidation/rollup ran against the bucket between 2026-06-22 and 2026-07-07 that
      could explain a stale read. Read-only, no fix attempt. Repo: market-tick-data-service / deployment-api.
      **Conflict-check note**: cefi_consolidated_closeout_2026_07_18.md's Track-2 checkpoint cadence will ALSO
      re-measure ASTER's attempted_failed as a side effect of its own POST-BACKFILL `/data-pipeline-check-mtds` gate —
      but that gate is itself gated behind the still-unlaunched Track-1/Track-2 backfill (confirmed unlaunched elsewhere
      in this same triage), so there is no live process this read-only investigation could collide with; it only reads
      data and appends findings to this issue doc. Safe to run now, independent of when the master's later checkpoint
      eventually fires. **Done when**: all three sub-checks have a recorded, evidenced result appended to this issue
      doc's Progress Log; root cause need not be conclusively identified — the deliverable is the evidence. Source:
      `issues/aster_mtds_failure_count_regression_2026_07_07.md`. — **DONE (slot-11, 2026-07-26, done incidentally while
      executing the downstream `cefi_satellite_ao_dispatch_batch2_2026_07_26.md` todo that consumes this evidence — this
      todo was still unchecked when that dispatch landed, and its 3 sub-checks are identical to what the downstream todo
      needed anyway, so ran them once rather than duplicate the read across two dispatches).** All three sub-checks
      recorded with evidence in `issues/aster_mtds_failure_count_regression_2026_07_07.md`'s 2026-07-26 Progress Log
      entry: (a) not reproducible at 17,675 — live manifest read shows 150; (b) NOT the same May-13 rows (different
      error class `UpstreamTimestampBiasError`, same-day 2026-07-25 timestamps); (c) multiple manifest rebuild/snapshot
      events found in the 06-22→07-07-adjacent window (plausible mechanism, not conclusively pinned — noted as moot
      since the count already recovered). Doc's `status:` flipped to `resolved` in that same session.
- [ ] [REVIEW] P1. **Audit every remaining `_normalize_instrument_id_for_match` call site for the same collision.** In
      `deployment_api/services/data_status/instrument_coverage.py` — the `missing_instruments` computation,
      `normalized_iid_counts`, and the `per_instrument` breakdown block — for the same `@`-suffix normalization
      collision on DERIBIT OPTION, DERIBIT dated-FUTURE, and OKX-FUTURES dated-FUTURE instrument_ids already proven to
      corrupt `per_instrument_coverage`. Reuse the issue's own measured methodology (query
      `instruments-store-cefi-prd-central-element-323112/prod/catalog.parquet`, compare raw-unique vs
      normalized-unique-key counts per venue/instrument_type). Read-only — no code change. Repo: deployment-api.
      **Conflict-check note**: the one flagged conflict (master closeout's OPEN DERIBIT quote-before-`@` P0 item) is
      explicitly code-orthogonal per the triage's own text — different repo (instruments-service) and different
      function, fixing content BEFORE `@` while this bug is driven by everything AFTER `@` being stripped — "do not race
      on the same file." Sequencing awareness only: the master's rebuild will change the raw DERIBIT instrument_id
      strings this audit measures against, so re-run this audit if the master's rebuild lands first. **Done when**: each
      of the 3 named call sites has a recorded PASS/FAIL collision-ratio verdict for at least DERIBIT OPTION and DERIBIT
      dated-FUTURE, citing measured counts, written into this issue doc or a new dated issue doc. Source:
      `issues/bug_c_normalize_id_collision_options_futures_2026_07_22.md`.
- [ ] [DATA] P1. **Purge orphaned CeFi on-chain-perp reference-data blobs left under the DEFI bucket.** For
      EXTENDED-STARKNET/PACIFICA-SOLANA/LIGHTER-ZKSYNC, written before the 2026-06-25 defi→cefi venue reclassification
      (~3 objects/day across history, un-enumerated since Phase 1 of that reclassification) — via a snapshot-first purge
      script analogous to `scripts/purge_cefi_perp_defi_contamination_2026_06_25.py` (which purged the manifest `_index`
      rows for this contamination but never touched the underlying `by_date` blob files). Confirm the expected-universe
      seeder still emits zero defi `expected_unattempted` rows for these 3 venues on a fresh dry-run
      (`engine/orchestrator/defi.py` already excludes them since the reclassification). Repo: instruments-service.
      **Done when**: a manifest-driven listing of the DEFI instruments bucket's
      `instrument_availability/by_date/**/venue={EXTENDED-STARKNET|PACIFICA-SOLANA|LIGHTER-ZKSYNC}/` prefixes returns 0
      objects (snapshot-backed before any delete), and a fresh `enumerate_expected_universe` dry-run for
      asset_group=DEFI shows 0 rows for these 3 venues. Source: `instruments_cefi_g1_g5_gate_execution_2026_07_24.md`.
- [ ] [BACKEND] P1. **Fix `deribit_volatility_index_handler.py`'s `available_at` wall-clock bug.**
      `_candles_to_dataframe` (market-tick-data-service) currently sets `available_at` from the BATCH-run wall-clock
      `attempted_at` instead of each row's own deterministic OHLC timestamp — change `"available_at": attempted_at`
      (line ~170) to reuse the already-computed per-row conversion
      (`"available_at": datetime.fromtimestamp(ts_ms /     1000.0, tz=UTC)`, mirroring the existing `"timestamp"` field
      on line ~162). Repo: market-tick-data-service. **Done when**: `_candles_to_dataframe` derives `available_at` from
      the row's own `ts_ms`; a regression test in `tests/unit/test_deribit_volatility_index_handler.py` proves a
      same-day re-run yields byte-identical `available_at` for every row; `quality-gates.sh` green. Source:
      `issues/cefi_available_at_wallclock_despite_deterministic_row_timestamp_2026_07_24.md`.
- [ ] [BACKEND] P1. **Fix `book_microstructure_handler.py`'s `available_at` wall-clock bug.** `_rows_to_dataframe`
      (market-tick-data-service) should use the already-computed deterministic day-representative `as_of` timestamp
      instead of the BATCH-run wall-clock `attempted_at` — thread `as_of` (already computed at line ~227, passed into
      `derive_microstructure_rows`) into `_rows_to_dataframe` and change
      `df.assign(available_at=attempted_at.isoformat(),     source=_SOURCE)` (line ~175) to use `as_of`. Repo:
      market-tick-data-service. **Done when**: `_rows_to_dataframe` stamps `available_at` from `as_of`; a regression
      test in `tests/unit/test_book_microstructure_handler.py` proves a same-day re-run yields byte-identical
      `available_at`, consistent with the handler's documented ε=0 BATCH==LIVE goal; `quality-gates.sh` green. Source:
      `issues/cefi_available_at_wallclock_despite_deterministic_row_timestamp_2026_07_24.md`.
- [ ] [DATA] P1. **Extend BYBIT futures_chain shape-2 duplicate verification to the full audited scope.** Extend the
      archived migration plan's 5-day sample to every day the existing Phase-1 scope-audit output
      (`_index/audit/bybit_futures_chain_shape_scope_2026_07_13.parquet`, `market-tick-data-service@5e367479`)
      classified `bare_flat_only`/`bundled_flat_only`/`mixed` — row-level diff each bare_flat/bundled_flat object
      against its hive/canonical counterpart using the same columns Phase 1 Todo 2 used, and write a per-day
      duplicate-verdict audit parquet. Read-only verification only — does NOT delete anything (the actual cleanup stays
      BLOCKED-OPERATOR-DECISION). Repo: market-tick-data-service. **Conflict-check note**: the one flagged conflict is
      master closeout's Track 7 verification of 6 of 8 specific (day, venue) cells for raw-tick PRESENCE ahead of a
      candle backfill — a different specific days/purpose (presence-confirmation for 8 named days vs duplicate-status
      for ~500+ days ahead of a Phase-4 delete decision), and both sides are read-only audits with no mutation, so there
      is no regression risk from running both. **Done when**: a new audit parquet gives a per-day
      duplicate/not-duplicate verdict for every day the Phase-1 scope audit classified
      bare_flat_only/bundled_flat_only/mixed, closing the "sample-based, not exhaustive" caveat. Source:
      `issues/bybit_futures_chain_write_shape_2026_07_13.md`.
- [ ] [DIAG] P1. **Combined investigation for `cefi_batch_download_oom_crashloop_capture_halt_2026_07_24.md` (3
      sub-items merged into one todo since all 3 append findings to that same doc):** (a) Pull the FULL unfiltered Cloud
      Logging output for the 2026-07-21 and 2026-07-22 executions of `uts-prod-market-tick-data-service-cefi-t1-recon`
      and determine whether those two days show the same signal-9/OOM crash-loop pattern confirmed for 2026-07-23/24, or
      a distinct earlier-stage failure. (b) Confirm whether the PAUSED `market-tick-cefi-daily-download` Cloud Scheduler
      job (paused since 2026-07-16) is dead/superseded — `gcloud scheduler jobs describe`, cross-reference against the
      two confirmed-live cefi triggers, grep market-tick-data-service + deployment-service for any live reference; if
      dead, delete it, if live, record why. (c) Check whether the recon job's download path (`hyperliquid_s3.py`'s
      `HyperliquidS3Downloader`) and the Surface-C cefi manifest-dedup scripts share a common heavy-import code path
      that could connect this OOM to the separately-documented dedup-script OOMs — static code-read comparison only, no
      execution. Repos: market-tick-data-service, instruments-service. **Done when**: all three sub-verdicts
      (same-pattern-vs-different for the two days; dead-vs-live for the scheduler job, with delete or kept-reason
      recorded; shared-import verdict named or ruled out) are recorded in the issue doc's Progress Log. Source:
      `issues/cefi_batch_download_oom_crashloop_capture_halt_2026_07_24.md`.
- [ ] [DATA] P1. **Conflict-check (2026-07-25 plan-reconcile): shares `partitioned_writer.py`'s `write_chunk`→
      `_update_cluster_and_chain_counts` call chain with the P2 cluster-counts-widen todo below. Do NOT dispatch
      concurrently — run the P2 widen FIRST so this proof validates the final, post-widen code, not a
      soon-to-be-superseded intermediate state.** **Prove + execute the cefi chain-tail v6 canonicalisation cutover (3
      sub-items merged into one todo — the cutover-register update needs the proof + migration's actual results, and
      both write findings to the same issue doc):** (a) Prove the shipped W1 v6 fix end-to-end against real GCS data
      (`-test-` bucket) — feed one real day of already-captured cefi `options_chain`/`futures_chain` tick data through
      `PartitionedTickWriter.write_chunk`, confirm the written path is v6-canonical
      (`underlying={U}/quote={Q}/margin={M}/ticks.parquet`), confirm `reader.py`'s v6-first probe reads it back, and
      confirm `_assert_canonical_chain_path` raises on a hand-constructed synthetic v5-shaped path. (b) Enumerate real
      v5 cefi chain objects in GCS and migrate each to v6 shape via copy + content-verify, recording any collision as an
      explicit unrecoverable-loss entry rather than silently merging; re-sync the manifest/data-status render for
      migrated cells. Do NOT delete/purge old v5 objects — human-only. (c) Record the cutover in
      `/codex/02-data/canonical-cutover-register.md` §7 — cite `market-tick-data-service@04222eb0` (W1) and
      `unified-api-contracts@9a92cf4f` (structural guard), and update cefi's "chain tail" cell to an accurate two-part
      status (code EXECUTED with both shas / data-migration status matching (b)'s actual outcome at time of edit, not
      overstated). Repo: market-tick-data-service (+ codex). **Done when**: (a)'s three checks each have a recorded
      PASS/FAIL with the exact object path(s)/day cited; (b)'s enumeration count and per-object migration report are
      recorded (old v5 objects left in place); (c)'s register entry cites both shas with an accurate, (b)-consistent
      two-part status — all in the issue doc's Progress Log / the register, committed via quickmerge. Source:
      `issues/cefi_chain_tail_v6_canonicalisation_2026_07_21.md`.
- [ ] [DATA] P1. **Conflict-check (2026-07-25 plan-reconcile): shares the same `partitioned_writer.py` call chain as the
      P1 v6-canonicalisation-proof todo above — run this one FIRST, then the P1 proof, never concurrently.** **Widen the
      cefi chain-tail cluster-counts bookkeeping key to include quote/margin.** `_update_cluster_and_chain_counts`
      (`market-tick-data-service/.../engine/orchestrator/partitioned_writer.py`) keys
      `_cluster_counts`/`_chain_available_at_max` on the 3-tuple `(itype, dt, underlying)` — widen to the 5-tuple
      `(itype, dt, underlying, quote, margin)`, mirroring the fix already applied to `_row_counts`/the writer-object
      cache key, so two cefi chains sharing an underlying but different quote/margin settlement no longer merge their
      coverage/available_at bookkeeping. Repo: market-tick-data-service. **Done when**: a new unit test proves two
      same-underlying, different-margin cefi chains produce separate `_cluster_counts`/`_chain_available_at_max` entries
      (analogous to the existing `test_cefi_chain_same_underlying_different_margin_never_collides`); all existing tests
      green; `quality-gates.sh` green; shipped via quickmerge. Source:
      `issues/cefi_chain_tail_v6_canonicalisation_2026_07_21.md`.
- [ ] [DATA] P1. **Corpus-wide scan for the missing-candle-SchemaContract failure class.** Enumerate every CEFI (and,
      per the doc's own scope, the DeFi/Prediction equivalent) venue x instrument_type combination that emits a
      non-chain-bundled `instrument_type=future` (or structurally-equivalent standalone dated-instrument) raw tick and
      hits "No SchemaContract registered" on an MDPS candle write. Read
      `unified_api_contracts/internal/schemas/_candle_contracts.py`'s `CONTRACT_REGISTRY` against CEFI's MVP venue list,
      cross-checked against `output_path_helpers.py`'s `CEFI_CHAIN_INSTRUMENT_TYPES` chain-bundle detection to determine
      which venues route a standalone FUTURE-typed shard into the per-instrument candle writer vs the chain-bundle path.
      Repos: unified-api-contracts, market-data-processing-service. **Done when**: a written list of every affected
      (asset_group, venue, instrument_type) combination beyond DERIBIT that hits this gap is produced (or an explicit
      confirmed-empty finding), giving the pending human policy decision the systemic-vs-DERIBIT-specific fact it needs.
      Source: `issues/cefi_future_instrument_type_no_candle_schema_contract_2026_07_21.md`.
- [ ] [DATA] P1. **Trace the fresh 2026-07-21 DERIBIT/COINBASE-FUTURES/BITFINEX-FUTURES/OKX-FUTURES `expiry_date`
      recurrence to specific symbols.** Pull the real run.log for the 2026-07-21 book_snapshot_5/trades writes (the
      ~4,655-row recurrence hitting `market_interface/adapters/cefi/tardis_shared.py`'s expiry-parsing fallback at lines
      516-518/544, distinct from the already-fixed BITGET-FUTURES shape from `market-tick-data-service@55ec86ac`),
      identify the exact symbols that failed to parse, and confirm or rule out the DERIBIT-combo-symbol hypothesis by
      cross-checking against `deribit_combo_perpetual_partition_move_2026_07_21.md`'s documented combo-symbol shapes.
      Repo: market-tick-data-service. **Done when**: a written per-symbol trace of the recurrence exists (from the real
      run.log, not re-derived from the normalized manifest), the combo-symbol hypothesis is explicitly confirmed or
      ruled out with cited evidence, and a new/extended issue doc records the finding. Source:
      `issues/cefi_high_attempted_failed_batch_cluster_2026_07_23.md`.
- [ ] [BACKEND] P1. **Add a PROGRESS-equivalent classification for content-canonicalisation dry-run/audit scripts.**
      `classify_no_capture_reason()` (`deployment-service/deployment_service/data_pipeline_monitors/_gcs.py`)
      false-pages `DP_VM_GONE_NO_CAPTURE` for a task type that structurally never writes the availability manifest —
      extend `_PROGRESS_RE` to also match `migrate_cefi_content_instrument_id_catalogue_2026_07_17.py`'s own summary
      vocabulary (`would_patch`, `already_canonical_skipped` in a `stats=` dict, or the literal
      `SCRIPT 1 CONTENT     MIGRATION SUMMARY` banner), mirroring how it already recognizes
      `record_captured`/`CATALOGUE_PROMOTED`. Repo: deployment-service. **Done when**: `classify_no_capture_reason()`
      returns `NoCaptureReason.PROGRESS` (not `SILENT`) for a run.log fixture matching this script's vocabulary, backed
      by a passing unit test in `test_data_pipeline_monitors.py`; `quality-gates.sh` green. Source:
      `issues/cefi_content_migration_vm_wedged_worker_2026_07_23.md`.
- [ ] [INFRA] P1. **Wire the already-built `DeploymentsRegistry.reap_stale()` into the exit-code fleet-monitor cron.**
      `reap_stale()` (`unified-trading-library/.../deployment_registry.py`) is already implemented + unit-tested but has
      ZERO callers anywhere outside its own tests — wire it into deployment-service's `*/5 * * *     *` exit-code sweep
      (`cli.py`'s `mode == "exit-code"` branch), passing the running-VM-name set the sweep already computes via
      `_list_running_vms()`, so a `deployments/active/*.json` registration whose GCE instance is confirmed gone gets
      archived automatically (verified live: this VM's record stayed `status: running` 4 days after its GCE instance was
      deleted). Pure wiring — no new archival logic needed. Repo: deployment-service. **Done when**: `cli.py`'s
      exit-code mode calls `DeploymentsRegistry(bucket=...).reap_stale(running_vm_names=...)` once per sweep; a passing
      test in `test_data_pipeline_monitors_cli.py` proves a gone-VM `active/` entry gets archived after one
      `--mode exit-code` run; `quality-gates.sh` green. Source:
      `issues/cefi_content_migration_vm_wedged_worker_2026_07_23.md`.
- [ ] [BACKEND] P1. **Add `DP_VM_GONE_NO_CAPTURE` to alerting-service's recurring-alert cooldown map.**
      `_RECURRING_ALERT_COOLDOWNS` (`alerting-service/alerting_service/notifiers/router.py`) is missing this event,
      mirroring the exact pattern already shipped for `DP_RUN_MOSTLY_EMPTY` (`alerting-service@fe76ded3`) — use a
      cooldown ≥ the detector's measured 300s sweep cadence, the same 1800.0s (30 min) value already adopted for the
      other DP_* entries; correct the stale comment (lines ~74-75) naming this event as "intentionally NOT here." Repo:
      alerting-service. **Done when**: `_RECURRING_ALERT_COOLDOWNS["DP_VM_GONE_NO_CAPTURE"]` is set (≥300s), the comment
      is corrected, and 2 new/extended regression tests (collapse-within-window + re-nag-past-boundary, plus a
      `_dedup_window_for` assertion) pass; `quality-gates.sh` green. Source:
      `issues/cefi_content_migration_vm_wedged_worker_2026_07_23.md`.
- [ ] [DATA] P1. **Probe Tardis exchange-info coverage for PACIFICA-SOLANA, investigation only.** Query
      `GET     https://api.tardis.dev/v1/exchanges/pacifica` (mirroring the same probe method the doc already used for
      `lighter`) to determine whether Tardis provides ANY historical coverage for PACIFICA-SOLANA
      trades/derivative_ticker, and if so its data_types + per-symbol `availableSince`. Do NOT implement any of the 3
      design options in the doc's "Follow-up" section, do NOT launch any backfill VM — fact-finding only, to give the
      pending human design decision real evidence. Repo: market-tick-data-service (read-only external API probe). **Done
      when**: a written finding is appended to the source doc's "Follow-up: PACIFICA-SOLANA historical depth" section
      (or a new linked issue doc), stating definitively YES/NO whether Tardis covers PACIFICA-SOLANA, citing the exact
      probe evidence. Source: `issues/cefi_onchain_perp_batch_venue_allowlist_gap_2026_07_12.md`.
- [ ] [DATA] P1. **Fill the HYPERLIQUID recent-tail manifest gap via the HL batch lane.** From ~2026-06-24 through now-2
      days — HYPERLIQUID is a non-Tardis DEX venue, exempt from the N=1 Tardis cap — launch the existing cefi HL batch
      launcher for the missing date range per `issues/cefi_hl_aster_batch_data_gaps_2026_06_22.md`. Repos:
      deployment-service, market-tick-data-service. **Done when**: manifest rows for venue=HYPERLIQUID show `captured`
      status across the 2026-06-24→now-2 range in the cefi `_index`, with no new `attempted_failed` regressions
      (before/after row counts reported). Source: `issues/cefi_residual_followups_after_honest_done_2026_07_17.md`.
- [ ] [SCRIPT] P1. **Re-run the HYPERLIQUID phantom-manifest re-census on a bigger VM.**
      `reconcile_phantom_manifest_rows_all.py --asset-group cefi` OOMs on the existing 15GB box — re-run on a 32-64GB VM
      to relabel the 1,277 HL phantom rows to their `@LIN` canonical path. Repo: instruments-service. **Done when**:
      phantom row count for HYPERLIQUID, measured by the script's own post-run count, is 0, verified against the live
      cefi manifest (not just exit code). Source: `issues/cefi_residual_followups_after_honest_done_2026_07_17.md`.
- [ ] [BACKEND] P1. **Close the residual `cefi → BATCH_TARDIS` fabrication path.** In
      `unified_trading_library/pipeline_mode_resolver.py`'s `derive_pipeline_mode_for_row`, before the generic
      `_ASSET_GROUP_FALLBACKS['cefi']` branch returns `PipelineMode.BATCH_TARDIS` (reached only when the (asset_group,
      data_type) has no `SOURCE_PRIORITY` entry and the venue has no `_VENUE_OVERRIDES` entry), check
      `VenueMapping().get_tardis_exchange_for_venue(venue)` (original hyphenated form); if `None`, return `None` instead
      of `BATCH_TARDIS` — mirrors the already-shipped LIGHTER-ZKSYNC/ohlcv_1m honest-absence guard. Leave every existing
      `_VENUE_OVERRIDES` entry and the SOURCE_PRIORITY-lookup path untouched. Repo: unified-trading-library.
      **Conflict-check note**: this is a pure future-write routing fix touching no existing data — orthogonal to the
      separate, still-open PACIFICA-SOLANA existing-object disposition question (purge vs quarantine) flagged elsewhere
      in this doc's conflicts. **Done when**: `quality-gates.sh` green; new unit tests prove (a) a synthetic cefi venue
      absent from both `_VENUE_OVERRIDES` and `VenueMapping.all_tardis_exchanges` now resolves to `None` for an unmapped
      data_type, and (b) a genuine Tardis-exchange cefi venue still resolves to `BATCH_TARDIS`. Source:
      `issues/cefi_onchain_venues_mislabeled_batch_tardis_2026_07_20.md`.
- [ ] [DATA] P1. **Re-partition the pre-~2026-02 LIGHTER-ZKSYNC `ohlcv_1m` tail out of `batch_tardis`.** ~1,050 objects
      (2025-07-15→~2026-02-01) still mislabeled `pipeline_mode=batch_tardis` — Tardis never emits LIGHTER ohlcv_1m at
      all, so ALL of it under `batch_tardis` is native `lighter_api` data mislabeled. Use the existing idempotent
      `restamp_lighter_ohlcv_batch_tardis_to_lighter_api_2026_07_18.py`: dry-run with
      `--start-date     2025-07-01 --end-date 2026-02-05` first (sanity-check count ≈1,050, investigate if wildly
      different), then `--apply` (copy → crc32c-verify → delete + one captured manifest row per object), then run the
      cefi manifest consolidator `--force`, then re-verify zero `captured` rows remain for this venue/data_type/window
      under `batch_tardis`. Do NOT touch LIGHTER `derivative_ticker`/`trades`/`book_snapshot_5` under `batch_tardis` —
      correctly Tardis-archived, out of scope. Repo: market-tick-data-service. **Conflict-check note**: the one flagged
      conflict (a sibling doc scoping this wider, to "<2026-04-17") is explicitly non-blocking per the triage's own text
      — "not a data-safety risk, the existing restamp tool is idempotent and would no-op on already-corrected days."
      **Cross-plan coordination note (2026-07-25 plan-reconcile)**: `cefi_consolidated_closeout_2026_07_18.md`'s
      Deferred-work table item 6 (Track 1, still not-started as of this note) separately plans a LIGHTER-ZKSYNC
      numeric-stem→canonical-symbol filename rename over the same venue's raw objects — a different mutation axis
      (filename stem, not `pipeline_mode=` partition path) but potentially overlapping GCS objects. Before running this
      todo's `--apply` step, confirm Track 1's rename has NOT started against the same window; if it has, re-derive
      which order is safe by reading `restamp_lighter_ohlcv_batch_tardis_to_lighter_api_2026_07_18.py`'s
      path-enumeration logic against Track 1's Script 2 resolver rather than assuming either order is safe. **Done
      when**: the `--apply` run completes with `moved`/`already-done`/`resumed-delete` for every enumerated object and
      zero `CONFLICT`/`MISSING`/`COPY-VERIFY-FAILED` statuses; consolidator run completes; a fresh availability_index
      query shows zero `captured` LIGHTER-ZKSYNC `ohlcv_1m` rows under `batch_tardis` for the window and the
      corresponding `batch_lighter_api` rows exist. Source:
      `issues/cefi_onchain_venues_mislabeled_batch_tardis_2026_07_20.md`.
- [ ] [DATA] P1. **Characterize the EXTENDED-STARKNET `batch_tardis` vs `batch_extended` content divergence,
      read-only.** For the 2026-01-01→~2026-06-04 overlap window, read a stratified sample (≥3 days × ≥10 overlapping
      instruments, `derivative_ticker` + `ohlcv_1m`) from BOTH lanes and produce a written report measuring per sampled
      shard: row-count deltas, column-set diffs, per-lane time-range coverage, and value agreement on shared timestamps
      (the doc's own spot-check already found one shard differs in md5/size/crc32c). Cross-check availability-manifest
      `captured` rows for the sampled keys to record which pipeline_mode each carries. Do NOT move, delete, or write any
      GCS object or manifest row, and do NOT pick or recommend a winning copy — reserved for the operator. Repo:
      market-tick-data-service (new dated one-off script, lifecycle-marked). **Done when**: a written report gives, for
      every sampled shard, row-count delta / column-set diff / per-lane coverage / overlapping-timestamp agreement
      percentage, plus the captured-row pipeline_mode cross-check; zero GCS/manifest writes occurred; the report
      explicitly declines to name an authoritative copy. Source:
      `issues/cefi_onchain_venues_mislabeled_batch_tardis_2026_07_20.md`.
- [ ] [BACKEND] P1. **Register `volatility_index` in cefi's data-type enumeration.** Add `"volatility_index"` to
      `DATA_TYPES_BY_ASSET_GROUP["cefi"]` in `unified_api_contracts/registry/market_data_categories.py`, mirroring the
      existing 2026-07-21 OKX-FUTURES/OKX-SWAP addition precedent in the same file. DERIBIT captures real PROD
      volatility_index data and it's already registered as a live `DataTypeCapability`, but the asset-group enumeration
      itself omits it — any consumer enumerating from `DATA_TYPES_BY_ASSET_GROUP` directly stays blind to this live
      cell. Repo: unified-api-contracts. **Done when**: `"volatility_index"` is present in the dict; `quality-gates.sh`
      green; grep confirms no parallel hardcoded cefi data-type list needs a matching edit. Source:
      `issues/cefi_shard_enumeration_blindspots_and_canonical_fetch_dependency_2026_07_18.md`.
- [x] ✅ [DATA] P1. **DONE 2026-07-26 (slot-8, `review`/`data_engineering`) — count is ZERO, plan checkbox was stale vs
      actual state.** Targeted (non-recursive) delimiter listing of
      `gs://market-data-tick-cefi-prd-central-element-323112/pipeline_mode=live_deribit/` returned "matched no objects";
      the bucket's top-level listing (`_index/`, `_migration_backup/`, `_migration_backups/`, `_quarantine/`,
      `_remediation_backups/`, `backfill-logs/`, `processed_candles/`, `raw_tick_data/`, `_vm_staging/`) confirms no
      `pipeline_mode=live_deribit/` prefix exists at all. `DeribitOptionsChainHandler` never wrote (or wrote nothing)
      under the legacy shape — zero blast radius. Full detail:
      `issues/deribit_live_options_chain_path_noncanonical_2026_07_21.md` todo 1.
- [x] ✅ [DATA] P1. **DONE — shipped `market-tick-data-service@ec0df878`; plan checkbox was stale vs actual code state
      (this rewrite already landed before this checkbox was flipped).** `_write_shard` builds its path exclusively via
      UAC `build_cefi_partition_path` (`instrument_type="options_chain"`, `quote_asset`/`margin_type` via
      `derive_settlement_dimensions`), mirroring `partitioned_writer.py::_cefi_chain_partition_dims`; the adjacent
      `record_captured(...)` call in `_collect_expiry_shard` passes `instrument_type="options_chain"` (not the legacy
      singular `"option"`); `test_write_shard_produces_v6_canonical_chain_path` +
      `test_write_shard_fans_in_across_calls_same_day_underlying` +
      `test_collect_expiry_shard_records_options_chain_instrument_type` assert the v6 shape + fan-in + manifest match;
      `quality-gates.sh` green. Source: `issues/deribit_live_options_chain_path_noncanonical_2026_07_21.md`.
- [ ] [DATA] P1. **Audit recent CEFI Tardis backfill VM launches for actual vs claimed completion.** Enumerate recent
      `mtds-backfill-cefi-*` launches via `gcloud compute operations list` / the `vm-logs/{vm}/` GCS prefix, and
      cross-check each run's claimed-complete signal (VM self-delete + the "mtds-backfill loop complete" log line)
      against actual manifest coverage (`capture_status` by date/venue/symbol) for that VM's declared scope, flagging
      any run whose coverage stops short of its declared end-date with no matching error/OOM signal. Repos:
      market-tick-data-service, deployment-service (read-only). **Done when**: a findings table, appended to this issue
      doc, lists each recently-completed-looking CEFI backfill VM run with its claimed-vs-actual completion status,
      explicitly flagging any silent short-fall. Source:
      `issues/mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md`.
- [ ] [PM] P1. **Verify + archive `mtds_mdps_order_book_imbalance_duplicated_2026_07_07.md`.** Both its remaining open
      checkboxes are already shipped — grep unified-api-contracts (`registry/data_type_capability.py`,
      `canonical/crosscutting/_source_priority_data.py`, `canonical/crosscutting/pipeline_mode.py`,
      `canonical/crosscutting/availability_semantics.py`, plus the named test files) for `order_flow_imbalance` and
      confirm zero live capability/logic entries remain (only retirement comments); cite
      `unified-api-contracts@49314f51` as the shipping commit closing the P1 UAC-side-retirement checkbox; close the P2
      numeric-agreement checkbox as MOOT (the doc's own todo-3 finding: zero production rows were ever captured, nothing
      to compare). Flip both to `[x]`, set `status: resolved`, then run the standard 6-step archival ritual (move to
      `plans/archive/issues/`, fix every corpus referrer's path). Repo: unified-trading-pm. **Done when**: both
      checkboxes show `[x]` with cited evidence; `status: resolved`; file moved to `plans/archive/issues/`; all corpus
      referrers updated; plan-hygiene/prek checks stay green. Source:
      `issues/mtds_mdps_order_book_imbalance_duplicated_2026_07_07.md`.
- [ ] [SCRIPT] P1. **Verify rotate-exchange-keys' venue registry + invocation path (2 sub-items merged — both append to
      the same issue doc's evidence trail):** (a) Verify every venue secret name referenced in
      `deployment-service/functions/rotate-exchange-keys/main.py`'s venue list against live GCP Secret Manager
      (`central-element-323112`) — for all ~29 listed entries (including the 5 never-verified: coinbase, kraken,
      bitfinex, bitget, upbit), classify match / renamed-target / no-secret-exists. Read-only — does not edit `main.py`.
      (b) Confirm whether `rotate-exchange-keys` is actually invoked on a live schedule/trigger in
      `central-element-323112` — determine live/wired vs dead/unwired and record the specific Scheduler job name /
      trigger config found (or its absence). Read-only infra query — no severity classification change, no rotation
      triggered. Repo: deployment-service. **Done when**: (a) a per-venue match/renamed-target/no-secret-exists table
      covering all ~29 entries (0 unverified) is appended to the issue doc's evidence trail; (b) a definitive live/dead
      verdict for the invocation path, with the specific gcloud evidence, is appended to the same evidence trail.
      Source: `issues/rotate_exchange_keys_stale_venue_registry_2026_07_23.md`.
- [ ] [SCRIPT] P1. **Build a dry-run-only reclass script for cefi Tardis-400 impossible-combination `attempted_failed`
      rows.** Mirror the repo's established `reclass_*.py` pattern (dry-run by default, `--apply` flag present but NOT
      invoked in this todo's scope, snapshot-before-write, before/after row counts) — identify cefi manifest rows
      attributable to Tardis HTTP-400 `code=300` (invalid-symbol) / `code=140` (date-not-available), the
      structural-absence codes already gated going-forward in `tardis_csv_transport.py`'s `is_structural_absence`
      (shipped `market-tick-data-service@a7569298`), and produce a dry-run proposal to reclassify them to
      `empty_confirmed`. Reproduce/refresh the already-measured dry-run count (24,410 rows, 2026-07-18) as the script's
      validation output. Do NOT pass `--apply`. Repo: market-tick-data-service. **Done when**: script committed at
      `market-tick-data-service/scripts/reclass_cefi_tardis_impossible_combinations_400_<date>.py` with a unit test, QG
      green; a dry-run execution against a current prod manifest snapshot completed with its row-count/breakdown
      recorded in the target issue doc's Progress Log; `--apply` never invoked. Source:
      `issues/tardis_impossible_combinations_recorded_as_attempted_failed_2026_07_17.md`.

## Progress Log

- **2026-07-26 (slot 6) — todo -001 scoping.** Dispatched the "Extend MDPS candle-building to the 4 on-chain-perp CeFi
  venues + backfill" todo. Scoping investigation (before any code/infra change) found the todo's own premise partially
  stale:
  - **No MDPS code change is needed.** An Explore-agent pass over `market-data-processing-service` confirmed: the CeFi
    venue list is UAC-owned (`VENUES_BY_ASSET_GROUP["cefi"]`,
    `unified-api-contracts/unified_api_contracts/registry/market_data_categories.py:272-361`) and ASTER/HYPERLIQUID/
    LIGHTER-ZKSYNC/EXTENDED-STARKNET are ALREADY present in it; MDPS's timeframe list (`config.py:419-421`,
    `["15s","1m","5m","15m","1h","4h","24h"]`) is one flat default with no per-venue gating;
    `resolve_pipeline_mode_from_source` (`app/core/canonical_writer_shaping.py:99-138`) generically resolves any
    closed-set UAC `PipelineMode` member, and `BATCH_ASTER`/`BATCH_HYPERLIQUID`/`BATCH_LIGHTER_API`/`BATCH_EXTENDED`
    already exist there. No hardcoded allowlist blocks these venues; there is no closed-list test to extend either
    (grepped `tests/` for all 4 venue tokens — zero hits beyond HYPERLIQUID, which is already treated as supported). The
    gap is purely OPERATIONAL: the backfill has never been run for these venues.
  - **Manifest-verified healthy captured raw-trade ranges** (`read_availability_index` over
    `market-data-tick-cefi-prd-central-element-323112`, filtered `service_name=='market-tick-data-service'`,
    `capture_status=='captured'`): **HYPERLIQUID** 95,678 rows, 2024-01-01 → 2026-07-20. **LIGHTER-ZKSYNC** 475 rows,
    2026-02-01 → 2026-05-06. **EXTENDED-STARKNET** 1,305 rows, 2024-10-19 → 2026-07-25. These 3 venues' raw-capture
    foundation is solid — safe to backfill candles against.
  - **ASTER carved OUT of this pass** — its manifest shows 486,890 `expected_unattempted` / 300 `attempted_failed` /
    only 1 `captured` row despite real many-instrument raw-trade files physically present on GCS for a recent day
    (2026-07-20/21) — a manifest-registration gap, not (necessarily) a real capture failure. This directly contradicts
    the archived `aster_capture_broken_coverage_and_completeness_2026_07_20.md`'s "RESOLVED — verified with real data"
    banner. Filed as a P0 big-finding issue doc: `issues/aster_raw_capture_manifest_registration_gap_2026_07_26.md`
    (`unified-trading-pm@580d1cdf7`). A manifest-scoped backfill range for ASTER would be wrong right now (it would
    think almost nothing exists), so ASTER is deferred to that issue doc's own remediation, not re-attempted here blind.
  - **CLI entrypoint confirmed** for the actual backfill:
    `market-data-processing process --start-date <D> --end-date <D> --CEFI --venues ASTER HYPERLIQUID LIGHTER-ZKSYNC EXTENDED-STARKNET [--data-types trades ...] [--timeframes ...]`
    (`market_data_processing_service.cli.main:run_cli`, flags in `cli/parser.py:114-155`). Also confirmed already-
    unregistered `processed_candles/` output for ASTER on disk (`timeframe=15s`/`1m` only, day=2026-07-20, no MDPS
    manifest rows) — no currently-running GCE VM is producing it (`gcloud compute instances list` at discovery time
    showed only unrelated `mdps-backfill-tradfi-*` VMs), so it's stray/orphaned, not a live collision risk.
  - **Dry-run validation (2026-07-26)**:
    `bash deployment-service/scripts/vm/launch-mdps-backfill-vm.sh --venues "HYPERLIQUID LIGHTER-ZKSYNC EXTENDED-STARKNET" cefi 2024-01-01 2026-07-25 dry`
    (VM `mdps-backfill-cefi-20260726-164248`, deleted after validation — no GCS writes in dry mode). Confirmed the happy
    path: `trades`-data_type candle aggregation (15s→1m→5m→15m→1h→4h→24h chain, real `quote_volume`-bearing output) —
    43/50 files succeeded on day 1 alone. **Found a real, separate gap**: `derivative_ticker` candle-building for
    HYPERLIQUID hard-fails for every instrument sampled (8/8 — ADA/AVAX/BNB/DOGE/FIL/LTC/MATIC/SOL-PERP) with
    `No SchemaContract registered for asset_group='cefi' instrument_type='UNKNOWN' data_type='deriv_ohlcv_1m' venue='HYPERLIQUID'`
    plus a companion `SCHEMA_VALIDATION_FAILED` (NOT-NULLABLE OHLC columns getting NaN) at the 15s tier. This is
    `derivative_ticker`-specific (funding-rate/mark-price candles) — it does NOT block the `trades`/`quote_volume` path
    this todo's "Done when" bar needs (ADV reader only reads `trades`-derived 24h candles), so it's tracked as a
    follow-up, not fixed inline here: **[DATA] P2 follow-up** — root-cause the `instrument_type='UNKNOWN'` resolution
    (should resolve `perpetual`) for HYPERLIQUID `derivative_ticker` → `deriv_ohlcv_1m` candle-building, then either fix
    the resolution or register the missing `unified_api_contracts.internal.schemas.contracts.CONTRACT_REGISTRY` entry —
    repo: market-data-processing-service (+ unified-api-contracts if a new contract is needed).
  - **Real backfill, live observation (2026-07-26 16:53 UTC, day 1 of 937)**: `trades` (the ADV-relevant data_type)
    completed cleanly for day 2024-01-01 with real candles generated; the pipeline then hit a THIRD non-blocking,
    orthogonal gap while processing `book_snapshot_5`:
    `MDPS canonical_writer: empty_confirmed manifest write failed for HYPERLIQUID:PERPETUAL:AAVE-USD@LIN day=2024-01-01 tf=15s`
    — the UTL Phase-1-KEYSTONE honest-absence gate (`record_empty(reason=SOURCE_RETURNED_ZERO)` requires
    `FetchEvidence`) correctly REFUSED an unproven empty write. Root cause visible in the preceding
    `WARNING Missing bid_price_0 or ask_price_0 columns` — HYPERLIQUID's raw book_snapshot_5 columns are named
    `bid_px_00`/`ask_px_00` (not `bid_price_0`/`ask_price_0`), so MDPS's book-candle aggregator reads it as "no valid
    rows" and (incorrectly) tries to record it as honest-absence rather than as a column-mapping bug. **[DATA] P2
    follow-up** — fix the book_snapshot_5 column-name mapping for HYPERLIQUID (and check
    LIGHTER-ZKSYNC/EXTENDED-STARKNET for the same `bid_px_NN`/`ask_px_NN` naming) in the MDPS book-candle aggregator,
    repo: market-data-processing-service. Non-blocking for this todo's `trades`/24h bar — the gate correctly prevented a
    silent bad write; this is a data-quality/schema-mapping fix, not urgent.
  - **Real backfill LAUNCHED (2026-07-26, in progress)**:
    `bash deployment-service/scripts/vm/ launch-mdps-backfill-vm.sh --venues "HYPERLIQUID LIGHTER-ZKSYNC EXTENDED-STARKNET" cefi 2024-01-01 2026-07-25 full`
    → VM `mdps-backfill-cefi-20260726-164955` (SPOT, e2-standard-8, asia-northeast1-c), confirmed STARTED (RUNNING at
    launch +<60s). Code tarballs for market-data-processing-service + market-tick-data-service were fresh at launch;
    unified-api-contracts/unified-trading-library/deployment-service tarballs were WARN-stale (unrelated peer-repo churn
    from sibling slots during launch prep) — advisory only (`LC_TARBALL_FRESHNESS` not set to enforce), not expected to
    affect candle-building correctness since MDPS/MTDS (the repos that actually matter for this job) were fresh.
    Monitoring for completion; post-completion steps: (1) run the launcher's own reminder —
    `rebuild_manifest_from_canonical_paths('market-data-tick-cefi-central-element- 323112', service_name='market-data-processing-service', prefix='processed_candles/by_date')`
    — to consolidate the per-VM shard into the canonical index, (2) verify `processed_candles/` objects with non-zero
    `quote_volume` exist for a recent day for each of the 3 venues, (3) verify `features-service`'s
    `RollingAdvReader. compute_rolling_adv()` returns non-`NO_DATA` for at least one probed instrument. **Minor
    housekeeping note**: the deleted dry-run VM's per-VM manifest shard
    (`_index/per_vm/mdps-backfill-cefi-20260726-164248.parquet`, 50 entries, `process_final=False`) was written to the
    prod cefi bucket before the VM was killed — a harmless orphaned per-VM shard (never consolidated, no candle data
    actually landed since dry-run skips uploads); will be superseded/ignored by the next consolidation pass, not cleaned
    up separately.

## Deferred

### Excluded — doc flagged `doc_too_large_or_risky_for_batch: true` (3 of 29 docs)

Per the batch-authoring rule, a doc flagged too-large/risky is excluded ENTIRELY — none of its AO-eligible candidates
are dispatched here, regardless of how clean their own conflict picture looks:

- `cefi_4surface_migration_execution_log_2026_07_24.md` — 1 AO-eligible candidate excluded (re-run the CeFi instrument
  catalogue rollup to resolve the 33 BITGET-FUTURES CME-letter-month gap rows). The doc's own 4 conflicts show it is
  live-tracking a fast-moving, actively-drained migration (Track 1 dedup, LATE renames, Surface C v2 apply) with
  multiple DELTA-dated sections superseding each other within the same file — genuinely needs its own dedicated
  triage/design pass, not folding into this batch.
- `issues/cefi_backfill_per_day_catalogue_reload_2026_07_20.md` — 0 AO-eligible candidates (both remaining fixes are
  undecided two-option design forks, one of which also conflicts with the live cefi OOM-outage investigation).
- `issues/onchain_venues_mislabeled_batch_tardis_lane_2026_07_20.md` — 0 AO-eligible candidates (a sibling issue doc on
  the SAME day/venues, `cefi_onchain_venues_mislabeled_batch_tardis_2026_07_20.md`, actively cross-corrects this doc's
  own closure-action recommendations — the two docs disagree on PACIFICA-SOLANA disposition and on whether
  EXTENDED-STARKNET is a simple de-dup or a content-divergent reconciliation; not safe to execute either doc's closure
  list without reading the other first).

### Excluded — cross-doc live-conflict evidence (1 item)

`issues/cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md`'s "Execute the LATE colliding-venue renames
migration to completion" (Range A/B/C `--apply` + final verification dry-run) is EXCLUDED even though its own
`conflicts_found` list (2 entries, both about unrelated stale-checkbox reconciliation) doesn't flag this directly.
`cefi_4surface_migration_execution_log_2026_07_24.md`'s own human-only rationale for the identical item states this
exact work — the SAME 3 excluding-date-range Range A/B/C `--apply` passes, ~507,851 objects — is "ACTIVELY IN PROGRESS
via a live human-directed /autonomous session," already queued/running, with a genuine 1114-object residual explicitly
BLOCKED-OPERATOR-DECISION. Dispatching a fresh AO todo for this would race/duplicate live production GCS mutations.
Resolved by clear logic (already running elsewhere), no operator question needed — re-check status in the finalize plan
before considering a fresh dispatch.

### Human-only remainder

The 29-doc triage additionally found ~97 human-only items across all docs (unmade operator/design decisions, credential
asks, time-gated accrual windows, prod-bucket-delete hard-stops, or items already superseded/shipped elsewhere) — none
of these are AO-eligible by construction; see each source doc's own `why_not_ao` rationale.

### No new operator-decision-queue entry from this batch

Every one of the 40 candidates' conflict pictures resolved cleanly on inspection — either the flagged conflict targeted
a DIFFERENT (often already-human-only) item, was explicitly declared non-blocking in the triage's own text
(code-orthogonal / low-collision-risk / not-a-data-safety-risk), was already handled inline in the todo's own
coordination note, or was resolvable by clear logic (both sides read-only with no mutation; or definitively already
running elsewhere, per the cross-doc exclusion above). No item required an operator ruling to include or exclude, so
`issues/autonomous_session_operator_decisions_2026_07_25.md` gets no new entry from this batch.

## Reconciliation

Once a todo here ships, flip the corresponding checkbox/section in its named source doc, citing this plan's commit as
evidence. This plan's own reconciliation-then-archive step is machine-gated via a companion
`cefi_satellite_ao_dispatch_batch1_finalize_2026_07_25.md` (`depends_on: [cefi_satellite_ao_dispatch_batch1_2026_07_25]`
— `gate_on_depends: true`), mirroring the tradfi/prediction batch1 finalize-plan pattern.

## Codex SSOTs

No new durable contract is created by this plan — every todo executes an already-decided spec from its source doc.
