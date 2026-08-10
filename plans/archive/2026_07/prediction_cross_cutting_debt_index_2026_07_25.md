---
doc_type: plan
title:
  Prediction closeout — cross-cutting / issue-doc coverage index (forked from
  prediction_consolidated_closeout_2026_07_18)
summary: >-
  Pure discoverability digest — forked verbatim out of prediction_consolidated_closeout_2026_07_18.md's "Aggregated
  source docs → Additional cross-cutting / issue-doc coverage" subsection (2026-07-25 consolidated-closeout split pass,
  line-cap remediation) to keep that parent within its line-cap target. Catalogs ~20 docs whose open work is genuinely
  cross-AG (defi/cefi/tradfi/sports-scoped debt, or shared infra/tooling debt) rather than prediction-owned dispatch
  surface — every bullet uses the bold non-checkbox digest convention (never real `- [ ]` checkboxes), same as it did in
  the parent, since this doc does not own the actual work for any of them.
status:
  complete # (was: active) 2026-07-28 archival sweep: this doc's own single [DOC] P3 todo (verify the digest is
  # accurate) is done; verified zero open todos of its own
nature: process
asset_group: [prediction]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [prediction, cross-cutting, close-out, debt-index, aggregated-sources, discoverability]
related:
  [
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
    /plans/active/prediction_phase_ab_residuals_2026_07_24.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-26" # was 2026-07-25 — /plan-reconcile prediction shard re-measured every digest open-count; 3 provably-stale entries corrected (bleed doc, pipeline_e2e_check_vm_name_collision, group_c triage)
parent_epic: predictions_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: data_engineering
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source: >-
  2026-07-25 consolidated-closeout split pass on prediction_consolidated_closeout_2026_07_18.md (design: fork the
  "Additional cross-cutting / issue-doc coverage" subsection out verbatim — the single biggest lever to bring that
  parent back under its line-cap target, since none of its content is prediction-owned work).
---

## Deferred work — migrated to:

**N/A — this doc is a pure discoverability index, not a work-owning plan.** Its own single todo (verify the digest stays
accurate) is done. The real open work it catalogs lives in the ~20 cited cross-AG sibling docs (including
`BLOCKED-OPERATOR-DECISION` P1 items, and a documented history of 3 stale digest counts corrected 2026-07-26) —
archiving this index does not close any of that work; see `/plans/active/prediction_consolidated_closeout_2026_07_18.md`
for the live picture.

> **🗄️ ARCHIVED 2026-07-28 (plan-hygiene sweep)** — this doc's own scope (a verified-accurate discoverability digest) is
> complete; it does not represent the prediction cross-cutting debt being cleared. Per
> `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`.

# Prediction closeout — cross-cutting / issue-doc coverage index

> **Forked from `prediction_consolidated_closeout_2026_07_18.md` (2026-07-25, consolidated-closeout split pass).** This
> is exactly the "Additional cross-cutting / issue-doc coverage" subsection of that doc's "Aggregated source docs"
> index, moved verbatim — nothing summarized, rewritten, or dropped, except one internal cross-reference (see the note
> below the table) that only made sense in-place. **This is a discoverability index only** — "referenced, not
> duplicated," same as it was in the parent. Every bullet below is the bold non-checkbox digest convention
> (`- **[TAG] P<n>.**`, never a real `- [ ] ` checkbox) per `task_template.md` finding H, since this doc does not own
> the dispatch surface for any of the ~20 docs it catalogs — each one's own file is still the one place its todos
> actually ship from.
>
> **Why these specific docs are here and not in the parent's own "Aggregated source docs" index**: every doc below is
> genuinely cross-AG (its open work spans defi/cefi/tradfi/sports, not prediction specifically) or shared infra/tooling
> debt — prediction is a bystander/co-affected party, not the primary owner. The parent's own index keeps the docs where
> prediction genuinely IS the primary or a co-equal owner (Capture/correctness, Manifest/CQG, Canonicalisation,
> Venue-perps, UI/bucket, ML/arb, Cross-cutting-w/-sports, Cross-asset-arb, Skills/engine, Parent epic).

**Additional cross-cutting / issue-doc coverage** (originally indexed 2026-07-24; forked verbatim 2026-07-25):

- [`plans/active/canonical_id_builder_retrofit_checklist_2026_07_08.md`](/plans/active/canonical_id_builder_retrofit_checklist_2026_07_08.md)
  (9 open total)
  - **[DATA] P1.** Retrofit the ~48 DeFi adapters that build `instrument_key` as an ad hoc f-string
  - **[DATA] P1.** Resolve the non-canonical TYPE-token question before retrofitting todo 1
  - **[DATA] P1.** Fix the real "no VENUE:TYPE: wrap at all" gap in both Prediction adapters — Kalshi
  - +6 more (3×P2, 3×P3) — see file for the rest
- [`plans/active/candle_canonical_path_migration_execution_2026_07_24.md`](/plans/archive/2026_07/candle_canonical_path_migration_execution_2026_07_24.md)
  (16 open total — all P0/P1, listed in full)
  - **[DATA] P0.** Rebuild code tarballs (`refresh_code_tarballs.sh`) for the 4 already-shipped repos
  - **[DATA] P0.** VERIFY on `-test-` via `/data-pipeline-check-mdps` (force+skip+canonical legs)
  - **[DATA] P0.** VERIFY readers dual-read correctly (features-service delta_one + volatility, unified-trading-api)
  - **[SCRIPT] P0.** Run the sanctioned Tier-2 spot-VM single-walk census (bounded in-session sampling already)
  - **[SCRIPT] P0.** Build the migration executor (P5): clone
  - **[SCRIPT] P0.** Implement the path transform in the executor: backward-add `instrument_type=` via
  - **[SCRIPT] P0.** Implement DEDUP in the executor for the split-brain candle layout (same object present under both)
  - **[SCRIPT] P0.** Implement PURGE of empty-stem objects (`venue={V}/.parquet` with no leaf id, ~0.6-0.8% defect)
  - **[SCRIPT] P0.** Implement QUARANTINE (never guess) for unresolvable legacy TradFi `E1AF0_*_migrated_*` leaf ids
  - **[SCRIPT] P0.** Wire manifest re-record to the SOURCE-keyed row (via `record_captured`, path-independent) into
  - **[SCRIPT] P0.** Upgrade the executor's pre-delete verification from SIZE-only to crc32c checksum before any prod
  - **[DATA] P0.** Extend `launch-canonical-migration-vm.sh` for this migration's per-AG SPOT fleet launch (target)
  - **[DATA] P0.** P7 per-AG SPOT migration apply, in order defi→prediction→cefi→tradfi (tradfi last)
  - **[DATA] P0.** P8 verify/reconcile: 4-surface reconciliation + extend the UAC canonical-path-violations oracle
  - **[DATA] P1.** P6 drain+snapshot: coordinate with the running `canonical-migration-cefi-wp*` raw_tick VMs
  - **[DATA] P1.** Root-cause + close the candle object↔manifest disconnect (6 degenerate MDPS manifest rows vs 20k+)
- [`plans/active/data_pipeline_check_mdps_features_2026_07_20.md`](/plans/active/data_pipeline_check_mdps_features_2026_07_20.md)
  (28 open total)
  - 8. **[DATA] P0.** RUN + VALIDATE `/data-pipeline-check-mdps` e2e: auto-select high-coverage day per AG
  - 9. **[DATA] P0.** RUN + VALIDATE `/data-pipeline-check-features` e2e: multi-day input window per family
  - 11. **[DATA] P0.** Cross-repo orphan/lineage audit (MTDS→MDPS→features→ml/strategy) + MIGRATE existing
        candle/feature
  - 13. **[DATA] P0.** Produce concrete ETA to backfill all remaining DeFi MVP (from benchmark + remaining-shard count)
  - NEW todo. **[DATA] P0.** Verify whether MDPS `max_workers` (8 on e2-standard-8) actually OVERLAPS the GCS writes
  - NEW todo. **[DATA] P0.** Enumerate the candle-coverage GAP per (asset_group, venue, data_type, timeframe)
  - NEW todo. **[DATA] P0.** Run `/data-pipeline-check-mdps` across all relevant AGs NOT already in candles
  - NEW todo. **[DATA] P0.** Run `/data-pipeline-check-features` across ALL shards (8 families x valid AGs)
  - NEW todo. **[DATA] P0.** VERIFY the prod projection on a real prod-bucket MDPS run before sizing the win
  - NEW todo. **[SCRIPT] P0.** Implement F1+F2 (UTL `manifest_completeness.py`) + F3 (MDPS `_publish_emission_check`)
  - NEW todo. **[DATA] P0.** Audit every `read_availability_index` caller on defi for a missing column/filter projection
  - NEW todo. **[SCRIPT] P0.** Fix the shared seed context (per-call immutable value object + collision-proof
    frame-cache)
  - NEW todo. **[SCRIPT] P0.** Implement R1 (concurrent date-subprocesses) — the months->weeks lever that is SAFE today
  - NEW todo. **[DATA] P0.** Real-VM re-measure of end-to-end per-instrument-day rate against a PROD-sized index
  - 10. **[DATA] P1.** Steady-state benchmark VMs (250GB disk) per representative shard-type
  - 12. **[SCRIPT] P1.** Backfill-processing path (download→process→upload) code-ready + OPTIMIZED learning from cefi
  - 15. **[DATA] P1.** Full DeFi-MVP candle backfill on real infra — GATED
  - NEW todo. **[DOC] P1.** Correct `/codex/05-infrastructure/spot-vms-for-backfill.md`: the preemption signal was NOT
  - NEW todo. **[SCRIPT] P1.** Close residual risk 1 — make arg-required launchers relaunchable (features especially)
  - NEW todo. **[DATA] P1.** Blast radius: did any PAST prod MDPS run use max_workers>1 over a heterogeneous list
  - NEW todo. **[SCRIPT] P1.** Implement R1: bounded-concurrent `_run_date_as_subprocess` dispatch (the 2-week
    throughput)
  - +6 more (P2) — see file for the rest
- [`plans/archive/2026_07/is_daily_enum_capture_heal_2026_07_07.md`](/plans/archive/2026_07/is_daily_enum_capture_heal_2026_07_07.md)
  (`status: draft`)
  - **[CODE] P0.** Add `exc_info=True` to the UTL shard-isolation catch (`service_framework/_adapter.py`)
  - **[CODE] P0.** With the real traceback now visible, re-run `is-daily-enum-{prediction,sports}` and read the ACTUAL
  - **[VERIFY] P1.** Backfill the missed windows: prediction 07-01→07-06, sports 06-28→07-06
- [`plans/archive/2026_07/mdps_features_reduced_artifact_tracker_2026_06_28.md`](/plans/archive/2026_07/mdps_features_reduced_artifact_tracker_2026_06_28.md)
  — ARCHIVED 2026-07-27, 0 open todos, all 9 mini-plans confirmed archived/complete
- [`plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md`](/plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md)
  (9 open total)
  - **[OPERATOR] P0.** BLOCKED-OPERATOR-DECISION — coordinate a maintenance window with the operator for the prediction
  - **[DATA] P1.** BLOCKED-OPERATOR-DECISION — Snapshot the prediction canonical manifest index
  - **[DATA] P1.** BLOCKED-OPERATOR-DECISION — Apply `rebuild_prediction_manifest.py` (full date range)
  - **[DATA] P1.** BLOCKED-OPERATOR-DECISION — Resume the prediction consolidator cron; record the before/after
    fill-rate
  - **[DATA] P1.** BLOCKED-OPERATOR-DECISION — Snapshot the tradfi canonical manifest index and pause its consolidator
  - **[DATA] P1.** BLOCKED-OPERATOR-DECISION — Apply `rebuild_tradfi_manifest.py` (full date range)
  - **[DATA] P1.** BLOCKED-OPERATOR-DECISION — Resume the tradfi consolidator cron; record evidence in the Progress Log
  - +2 more (P2/P3) — see file for the rest
- [`plans/active/issues/adapter_findings_gcs_manifest_deployment_api_reconciliation_gap_2026_07_08.md`](/plans/active/issues/adapter_findings_gcs_manifest_deployment_api_reconciliation_gap_2026_07_08.md)
  - **[VERIFY] P1.** Check whether manifest regeneration is automatic or requires an explicit re-enumeration trigger
  - **[VERIFY] P2.** Spot-check 2-3 more findings from the smoke-test doc across all 3 layers
  - **[DECISION] P2.** Once the pilot trace (AAVE_V3) lands, decide the reconciliation cadence for the remaining 58
- [`plans/active/issues/backfill_smoke_write_path_canonical_audit_2026_07_20.md`](/plans/active/issues/backfill_smoke_write_path_canonical_audit_2026_07_20.md)
  - 1. **[DATA] P1.** instruments-service: canonicalise the `instrument_availability` write to
  - 2. **[DATA] P1.** market-tick-data-service: rule on and fix the cefi chain tail — `partitioned_writer.py:291-293`
  - 3. **[DOCS] P2.** instruments-service + market-tick-data-service: correct the three in-repo comments that assert
  - 4. **[SCRIPT] P2.** unified-trading-pm: add a Phase-0 `-test-` assertion on the resolved WRITE bucket
  - 5. **[DOCS] P2.** unified-trading-pm: add an explicit "never pass `--allow-live-prod-writes`" prohibition
  - 6. **[DATA] P3.** instruments-service: decide whether `market_lifecycle` (`writers.py:495-501`) should
- [`plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md`](/plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md)
  (8 open total — listed in full, not over the >8 cap threshold)
  - 7. **[DATA] P0.** Root-cause the object↔manifest disconnect (20,734 cefi candle objects on 2026-04-14 vs 6 MDPS)
  - 2. **[DATA] P1.** Corpus-wide count of zero-length-stem candle objects (`…/venue=*/.parquet`); purge or repair
  - 3. **[DATA] P1.** Canonicalise TradFi candle leaf ids (`E1AF0_C3200_migrated_*` → `VENUE:TYPE:SYMBOL`)
  - 9. **[DATA] P1.** Split-brain candle layout (addendum iii-a): the same cefi day (2026-05-23) holds BOTH
  - 19. **[SCRIPT] P2.** Fix `_copy_verify_delete()`'s retry-idempotency gap
  - 13. **[DATA] P3.** `ProvisionalTargetIndex` keys lack a bucket component, so the split-brain COUNT is off
  - 15. **[DOC] P3.** `unified-trading-library`'s `build_canonical_candle_path()` docstring example still shows
  - 16. **[SCRIPT] P3.** Investigate why `CEFI:DERIBIT:trades:24h`'s force-leg MEASURED classification shows
- [`plans/active/issues/coverage_floor_registries_no_cross_propagation_2026_07_17.md`](/plans/active/issues/coverage_floor_registries_no_cross_propagation_2026_07_17.md)
  - **[CODE] P1.** Add a falsifier test (mirroring `scripts/check_coverage_exclusions.py`'s pattern)
  - **[DATA] P1.** Resolve the 8 confirmed multi-year/multi-month CeFi mismatches (BITFINEX, KRAKEN, COINBASE-SPOT)
  - **[DATA] P2.** Resolve the CME mismatch — `coverage_starts.py`'s 2010-01-01 carries `# TODO verify`
  - **[DATA] P2.** Resolve the POLYMARKET mismatch (2022-11-21 CLOB-launch vs 2025-03-14 first-actual-instrument)
  - **[DATA] P3.** Resolve the small 1-21 day DeFi protocol drifts (CURVE, UNISWAP_V2, UNISWAP_V4, BALANCER, LIDO)
  - **[DATA] P3.** Publish an explicit key-mapping table between `coverage_starts.py`'s bare venue/protocol keys
- [`plans/archive/issues/cross_ag_prediction_rows_bleed_into_sports_instruments_index_2026_07_20.md`](/plans/archive/issues/cross_ag_prediction_rows_bleed_into_sports_instruments_index_2026_07_20.md)
  (8 open total — listed in full, not over the >8 cap threshold; **re-measured 2026-07-26, `/plan-reconcile` prediction
  shard** — the previous list was a stale ROUND-3 snapshot: it named todos 5/6/7 (answered 2026-07-24) and a todo 8 that
  does not exist in the target doc, while silently omitting ROUND-4/5/6's todos 12/13/14/15 — three of them P0)
  - 12. **[BACKEND] P0.** Fix `_write_consolidated`'s CAS precondition to be correlated with the content read, not a
    late `blob.reload()` — makes a genuine conflict actually raise `PreconditionFailed`
  - 13. **[BACKEND] P0.** Once todo 12 ships, confirm a new consolidator Cloud Run image build+deploys via the normal
        CI/CD pipeline rather than needing a manual trigger
  - 14. **[DATA] P0.** Only after todo 13's image is confirmed serving: re-run
        `remediate_cross_ag_prediction_bleed_round3_2026_07_24.py` and verify it holds across a real consolidation cycle
  - 1. **[DATA] P1.** Pin the true full count and composition — read the `instruments-store-sports` index
  - 2. **[BACKEND] P1.** Locate the writer — trace which job/uploader writes `asset_group=prediction` rows
  - 3. **[BACKEND] P1.** Fix the misattribution at the writer so a prediction shard's manifest row lands only
  - 4. **[DATA] P2.** Remediate the already-written bleed rows — decide whether to relocate them
  - 15. **[DATA] P2.** Determine whether `market-data-tick-sports-prd`'s 20,785 `venue=KALSHI`/`empty_confirmed` rows
        are the same bleed class or a separate population
- [`plans/active/issues/estate_orphan_assessment_2026_07_21.md`](/plans/active/issues/estate_orphan_assessment_2026_07_21.md)
  - 3. **[INFRA] P1.** Run the orphan sweep for defi / cefi / tradfi / prediction on a VM — deployment-service@f8e885f
  - 4. **[CODE] P2.** Make the manifest load resumable / streamed in `migration_orphan_sweep.py`
  - 5. **[CODE] P3.** `GcsEventSink` never `.shutdown()`s its background `ThreadPoolExecutor` (4 workers)
  - 6. **[CODE] P2.** Give `backfill_orphan_class_e.py --apply` a batched-incremental `record_cells()` call
  - 8. **[DATA] P2.** Measure prediction's `B_legacy_duplicate` population — never reported anywhere in this doc's
       already-durable sweep report (prediction-specific; other-AG-only todos 7/3c not listed here)
- [`plans/archive/issues/group_c_cloud_run_job_failures_triage_2026_07_16.md`](/plans/archive/issues/group_c_cloud_run_job_failures_triage_2026_07_16.md)
  — 0 open todos (all 6 `[x]`; **corrected 2026-07-26, `/plan-reconcile` prediction shard** — the previously-listed
  `[INFRA] P1` default-to-yesterday date bridge is `[x]` in the target doc, and the artifact is live:
  `unified_trading_library/service_framework/_adapter.py::_default_batch_dates_to_yesterday()` (line 26) is called by
  `_build_io()`'s BATCH branch at lines 209-210, per `unified-trading-library@3485c4d0`)
- [`plans/active/issues/honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md`](/plans/active/issues/honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md)
  (14 open total)
  - **[DESIGN] P1.** Fix the mockup's leaf model everywhere it still needs it (Finding 1) — CEFI/TRADFI/DEFI's
  - **[DESIGN] P1.** Design the CEFI instrument-definition parquet resharding (Finding 2, decided)
  - **[CODE] P1.** Widen the writer-fix scope to Solana DeFi + CURVE-OPTIMISM (same CEFI instrument-definition parquet
    resharding design as the item above)
  - **[CODE] P1.** Pull the real per-instrument_type breakdown for DERIBIT live (the comparison built for this doc)
  - **[CODE] P1.** Add `missing_dates`/`dates_found_list` to the per-instrument_type and per-underlying breakdown
  - **[CODE] P1.** Move `market_metadata` off the MTDS `per_venue_per_data_type_daily` axis
  - **[VERIFY] P1.** Raw-parquet spot-check the 5 additional CeFi venues flagged by the pre-audit's registry read
  - **[CODE] P1.** Backfill historical CeFi/TradFi manifest rows with the corrected per-instrument_type split
  - +6 more (4×P2, 2×P3) — see file for the rest
- [`plans/active/issues/instrument_availability_hive_canonicalisation_2026_07_21.md`](/plans/active/issues/instrument_availability_hive_canonicalisation_2026_07_21.md)
  - 7. **[DATA] P1.** PROVE the fixed writers green on one real day (write + skip-if-fresh + manifest row)
  - 8. **[REVIEW] P1.** On writer ship, record the `instrument_availability` full-hive cutover date
- [`plans/active/issues/instrument_id_format_canonicalization_2026_07_08.md`](/plans/archive/issues/instrument_id_format_canonicalization_2026_07_08.md)
  - **[SCRIPT] P2.** DEX-pool catalog regeneration (finding 2, all 13 protocols) — real code is already correct
  - **[DECISION] P2.** Confirm exact target quote-currency per on-chain-perp venue (finding 4) — ASTER/PACIFICA
- [`plans/active/issues/instruments_docs_audit_outstanding_items_2026_07_08.md`](/plans/active/issues/instruments_docs_audit_outstanding_items_2026_07_08.md)
  — 0 open todos (closed/archived/record-only)
- [`plans/active/issues/instruments_remaining_work_audit_2026_07_10.md`](/plans/active/issues/instruments_remaining_work_audit_2026_07_10.md)
  — 0 open todos (closed/archived/record-only)
- [`plans/active/issues/manifest_completeness_full_corpus_map_build_2026_07_20.md`](/plans/archive/issues/manifest_completeness_full_corpus_map_build_2026_07_20.md)
  - 1. **[DATA] P0.** VERIFY the prod projection before sizing the win — is `_publish_emission_check` actually firing
  - 5. **[DATA] P0.** The 1.58 GB defi-prd index is its own P0 — audit every `read_availability_index` caller on defi
  - 6. **[DOC] P2.** Record in codex that the per-VM manifest flush is ALREADY debounced (50 entries/5.0s,
       `utl@6b6d53bd`)
- [`plans/active/issues/mdps_features_deadcode_consolidation_2026_07_20.md`](/plans/active/issues/mdps_features_deadcode_consolidation_2026_07_20.md)
  (8 open total — listed in full, not over the >8 cap threshold)
  - 3. **[SCRIPT] P1.** S1-c — `mdps-sports-<year>-<ts>` emitted by `launch-mdps-sharded-backfill.sh:206` but registered
  - 1. **[SCRIPT] P2.** S1-a — `launch-prediction-features-vm.sh` BROKEN (packages removed)
  - 2. **[SCRIPT] P2.** S1-b — `launch-mdps-features-live.sh` non-runnable (no dispatcher branch)
  - 4. **[SCRIPT] P3.** S2-a — trim `launch-features-backfill-vm.sh` to the redirect stub (lines 170-309 unreachable)
  - 5. **[SCRIPT] P3.** S2-b — delete the 8 stale `features_*_service` keys in `setup-data-pipeline-vm.sh`
  - 6. **[SCRIPT] P3.** S3-a — delete MDPS one-offs past `Delete-when` after verifying each condition
  - 7. **[SCRIPT] P3.** S3-c — repoint `features-service/scripts/sports/smoke_matrix.py` SSOT citations
  - 8. **[SCRIPT] P3.** S3-b — sports dual entrypoint (`python -m features_service.sports`)
- [`/plans/archive/issues/mdps_prior_seed_context_thread_unsafe_2026_07_20.md`](/plans/archive/issues/mdps_prior_seed_context_thread_unsafe_2026_07_20.md)
  - 3. **[DATA] P1.** Assess blast radius on EXISTING candle data: any past MDPS run with `max_workers>1`
- [`plans/archive/issues/migration_orphan_sweep_performance_decay_2026_07_22.md`](/plans/archive/issues/migration_orphan_sweep_performance_decay_2026_07_22.md)
  - 7. **[CODE] P3.** Genuinely stream `_load_manifested_cells()`'s parquet read (row-group batches)
- [`plans/active/issues/mtds_is_full_adapter_smoketest_findings_2026_07_07.md`](/plans/active/issues/mtds_is_full_adapter_smoketest_findings_2026_07_07.md)
  - **[VERIFY] P1.** NEW (2026-07-14) — FLUID lending_indices silently returns 0 rows for ~18 months of its own declared
  - **[VERIFY] P1.** Root-cause the 273 mistagged DERIBIT/COMBO rows (open question #1) — not attempted this session
  - **[CODE] P2.** Update both drilldown mockups — not attempted this session (out of dispatched scope)
- [`plans/active/issues/pipeline_e2e_check_vm_name_collision_2026_07_12.md`](/plans/archive/issues/pipeline_e2e_check_vm_name_collision_2026_07_12.md)
  (1 open — **corrected 2026-07-26, `/plan-reconcile` prediction shard**; was wrongly digested as "0 open todos
  (closed/archived/record-only)")
  - **[CODE] P2.** Add a collision-resistant component (e.g. an 8-hex slug of `hash(venue, data_type)`) to the
    pipeline-e2e-check VM name
- [`/plans/archive/issues/prediction_lifecycle_prefetch_gate_and_resolution_day_catalogue_2026_07_14.md`](/plans/archive/issues/prediction_lifecycle_prefetch_gate_and_resolution_day_catalogue_2026_07_14.md)
  (dup ref — see `prediction_consolidated_closeout_2026_07_18.md`'s "Aggregated source docs → Capture / correctness"
  subsection for its 2 open todos — corrected 2026-07-25, was "see Capture / correctness above," which only resolved
  while this content lived in the same file as that subsection)
- [`plans/archive/issues/prediction_universe_capture_dead_since_07_01_2026_07_06.md`](/plans/archive/issues/prediction_universe_capture_dead_since_07_01_2026_07_06.md)
  — 0 open todos (closed/archived/record-only; archived 2026-07-26)
- [`plans/archive/issues/ui_coverage_ts_venue_category_v2_rename_gap_2026_07_10.md`](/plans/archive/issues/ui_coverage_ts_venue_category_v2_rename_gap_2026_07_10.md)
  — 0 open todos (closed/archived/record-only)

## Progress Log

- **2026-07-25** — Forked verbatim from `prediction_consolidated_closeout_2026_07_18.md`'s "Aggregated source docs"
  index (consolidated-closeout split pass, line-cap remediation) — the single biggest lever to bring that parent back
  under its line-cap target, since none of this content was prediction-owned dispatch surface. One internal
  cross-reference corrected in the move (the `prediction_lifecycle_prefetch_gate_and_resolution_day_catalogue` dup-ref,
  which said "see Capture / correctness above" — no longer true once relocated to a different file). No other content
  changed; every doc's own open-todo count and item list is exactly as it was in the parent.
- **2026-07-26** — `/plan-reconcile` prediction shard (autonomous). Re-measured every `N open` digest claim in this file
  against real `- [ ]` counts and fixed the 3 that were provably stale — this file inherited them verbatim from the
  parent, so they were stale before the fork, not introduced by it: (1)
  `cross_ag_prediction_rows_bleed_into_sports_instruments_index_2026_07_20.md` listed a ROUND-3 snapshot (todos 5/6/7,
  answered 2026-07-24, plus a todo 8 that does not exist in the target doc) while omitting ROUND-4/5/6's todos
  12/13/14/15 — three of them P0, i.e. genuinely open P0 work invisible in the index that promises "nothing is silently
  dropped"; (2) `pipeline_e2e_check_vm_name_collision_2026_07_12.md` was digested as "0 open" but has 1 open `[CODE] P2`
  at line 118; (3) `group_c_cloud_run_job_failures_triage_2026_07_16.md` was digested with an open `[INFRA] P1` that is
  `[x]` in the target doc and whose artifact is live in UTL. The remaining 20-odd digest claims in this file re-measured
  clean.

## Todos

- [x] ✅ [DOC] P3. **This index's digest claims have been found stale before (3 of ~20 on the 2026-07-26 re-measure) —
      it is not "0 open work"** — it catalogs real open todos across ~20 sibling docs (including
      `BLOCKED-OPERATOR-DECISION` P1 items), so its own checkbox-free format must not be read as evidence the prediction
      cross-cutting debt is cleared; re-verify each digest count before relying on it. **Verified accurate 2026-07-28**
      — re-read the doc in full: the caveat correctly describes both the doc's own non-checkbox digest format and its
      documented history of stale counts (the 2026-07-26 `/plan-reconcile` correction of 3 entries, recorded in the
      Progress Log above). No further correction needed; checkbox flipped to record the verification.
