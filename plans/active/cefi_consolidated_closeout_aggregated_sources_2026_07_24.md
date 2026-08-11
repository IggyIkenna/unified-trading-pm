---
doc_type: plan
title: CeFi consolidated close-out — aggregated source docs (discoverability index)
summary: >-
  The "Aggregated source docs" discoverability index extracted verbatim from cefi_consolidated_closeout_2026_07_18.md's
  2026-07-24 line-cap trim (2nd pass -- the umbrella:true exemption was removed same-day, flat 1000L hard cap now
  applies with no exceptions). Lists every other cefi-relevant plan/issue with a repo-root-relative path and a condensed
  digest of its currently-open todos (bold, non-checkbox markers so this stays structurally un-ingestable by AO's
  regen_backlog parser even though this doc itself is LOCAL/not dispatched). Read this alongside the parent for full
  context on what's open across the cefi asset group; the parent's own native Tracks 1-7 + Progress Log + Deferred-work
  sections are NOT duplicated here.
status: active
nature: process
asset_group: [cefi]
stage: [data]
repos:
  [
    instruments-service,
    market-tick-data-service,
    market-data-processing-service,
    features-service,
    unified-api-contracts,
    deployment-service,
    unified-trading-pm,
  ]
scope: [engineer]
tags: [cefi, discoverability, index, aggregated-source-docs, plan-hygiene]
related:
  [
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/archive/issues/plan_line_cap_remediation_2026_07_23.md,
  ]
created: "2026-07-24"
parent_epic: cefi_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
last_updated: "2026-08-02" # 2026-08-02: added 3 self-dispatched-but-unlinked citations (ag-closeout-audit linkage-gap fix); was 2026-07-25 (appended the parent's "Pass-through from the 2026-07-18 consolidated canonicalisation audit" section verbatim, 4-child split pass, cefi.4)
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Plan line-cap hygiene remediation, 2nd pass, /plans/archive/issues/plan_line_cap_remediation_2026_07_23.md -- operator
  ruling 2026-07-24 removed the umbrella:true exemption entirely (flat 1000L hard cap, no exceptions).
assigned_role: data_engineering
drift_direction: advance-code
context_scope:
  [
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/archive/issues/plan_line_cap_remediation_2026_07_23.md,
  ]
---

# CeFi consolidated close-out — aggregated source docs (discoverability index)

> Extracted verbatim from `/plans/active/cefi_consolidated_closeout_2026_07_18.md`'s 2026-07-24 line-cap trim (2nd
> pass). Nothing summarized or dropped.

## Aggregated source docs (referenced, not duplicated — every other active cefi + cefi-touching plan/issue)

> Every doc below is enriched with its path (repo-root-relative, leading-slash) + a condensed digest of its currently
> OPEN todos, so an AO worker can act from this doc alone without opening a dozen others. Only unchecked `- [ ]`
> top-level items are listed; `- [x]` items are omitted. Docs with 0 open todos get a one-line disposition instead of
> sub-bullets. Docs with >8 open todos list every P0/P1 in full and cap P2/P3 with a `+N more` marker — never a silent
> drop.

> Full 4-surface migration Progress Log detail (KRAKEN-SPOT dry-runs, fleet-monitoring lessons, etc.) lives in
> [`plans/active/cefi_4surface_migration_execution_log_2026_07_24.md`](/plans/active/cefi_4surface_migration_execution_log_2026_07_24.md)
> (filename carries `_2026_07_24`, not the `_07_18` the pointer text below once implied), extracted 2026-07-24 per the
> plan line-cap remediation. **NOT fully closed** — `status: active`, 7 open todos (verified 2026-07-24, not the "almost
> certainly 0" assumed at extraction time):
>
> - **[SCRIPT] P0.** Script 2 `_PATH_RE` must tolerate an embedded-slash wire stem (KRAKEN-SPOT 25,131) — FENCED to the
>   live rename fleet.
> - **[DATA] P0.** De-duplicate the 658 ambiguous catalogue wire keys (off-by-one expiry duplicates) in
>   `build_instrument_catalogue.py`.
> - **[DATA] P0.** Enumerate the MISSING catalogue rows behind the ≈5,413 healthy-venue residue in
>   `build_instrument_catalogue.py`.
> - **[DATA] P1.** Add a LIGHTER-ZKSYNC market-index → symbol map so the ~11,283 numeric-stem objects resolve.
> - **[DATA] P1.** DERIBIT combo mispartition — two distinct actions: (a) fix the still-open write-path leak (safe, ship
>   alone); (b) the partition-MOVE for 15,119 rows (needs fresh explicit operator sign-off).
> - **[DATA] P2.** Design the COMBO-in-perp-partition move for DERIBIT.
> - **[DATA] P2.** Register PACIFICA-SOLANA (265) in the fail-hard quarantine set.

- **Venue-specific canonicalisation residuals**:
  - [`plans/active/issues/bybit_futures_chain_write_shape_2026_07_13.md`](/plans/active/issues/bybit_futures_chain_write_shape_2026_07_13.md)
    — 0 open todos (status: open, narrative finding doc — no checkbox-tracked items, see file for recommended fix).
  - [`plans/archive/2026_07/cefi_deribit_combo_and_okx_bare_venue_gaps_2026_07_12.md`](/plans/archive/2026_07/cefi_deribit_combo_and_okx_bare_venue_gaps_2026_07_12.md)
    — 0 open todos (archived 2026-07-26, record-only).
  - [`plans/active/issues/cefi_chain_tail_v6_canonicalisation_2026_07_21.md`](/plans/archive/issues/cefi_chain_tail_v6_canonicalisation_2026_07_21.md)
    - 5. **[DATA] P1.** PROVE the fixed W1 emits v6 for a cefi chain on one real day (write + reader round-trip).
    - 6. **[DATA] P1.** Migrate existing v5 cefi chain objects → v6 (copy → content-verify → human-only purge of v5).
    - 7. **[DATA] P1.** Re-sync the manifest / data-status render for the migrated cefi chain cells so all four
         canonical surfaces agree.
    - 8. **[REVIEW] P1.** On W1 ship, record the cefi chain-tail v6 cutover date in the canonical-cutover-register.
  - [`plans/archive/issues/deribit_live_options_chain_path_noncanonical_2026_07_21.md`](/plans/archive/issues/deribit_live_options_chain_path_noncanonical_2026_07_21.md)
    — 0 open todos (resolved/archived 2026-07-26, `market-tick-data-service@ec0df878`).
  - [`plans/archive/issues/instruments_service_deribit_combo_purge_test_drift_2026_07_21.md`](/plans/archive/issues/instruments_service_deribit_combo_purge_test_drift_2026_07_21.md)
    — 0 open todos (closed/archived/record-only).
  - [`plans/archive/issues/cefi_okx_margin_type_wire_key_ambiguity_reclassification_2026_07_22.md`](/plans/archive/issues/cefi_okx_margin_type_wire_key_ambiguity_reclassification_2026_07_22.md)
    — 0 open todos (status: open, narrative finding doc — no checkbox-tracked items, see file for recommended fix).
  - [`plans/active/issues/bug_c_normalize_id_collision_options_futures_2026_07_22.md`](/plans/archive/issues/bug_c_normalize_id_collision_options_futures_2026_07_22.md)
    - **[BACKEND] P1.** Fix `_normalize_instrument_id_for_match` so OPTION/dated-FUTURE instrument_ids don't collide.
    - **[BACKEND] P2.** Add unit test coverage for `_normalize_instrument_id_for_match` using real OPTION/dated-FUTURE
      instrument_id shapes.
    - **[REVIEW] P2.** Audit other `_normalize_instrument_id_for_match` call sites for the same collision.
  - [`plans/active/issues/mtds_uac_embedded_colon_symbol_validation_regression_2026_07_21.md`](/plans/archive/issues/mtds_uac_embedded_colon_symbol_validation_regression_2026_07_21.md)
    — 0 open todos (status: open, narrative finding doc — no checkbox-tracked items, see file for recommended fix).
  - [`plans/active/issues/uac_build_instrument_id_colon_strictness_mtds_ripple_2026_07_21.md`](/plans/archive/issues/uac_build_instrument_id_colon_strictness_mtds_ripple_2026_07_21.md)
    - 1. **[REVIEW] P1.** Confirm whether MTDS call-site updates for the UAC colon-strictness change were intended in
         the SAME wave.
    - 2. **[DATA] P1.** Fix `canonical_write.py::write_defi_rows` (WETH:USDC POOL case) — resolve via the DeFi pool
         catalogue/wire-map before `build_instrument_id`.
    - 3. **[DATA] P1.** Fix `tardis_shared.py::derive_row_instrument_id`'s disabled-by-default fallback (ADAF0:USTF0
         case) the same way.
    - 4. **[REVIEW] P2.** Re-check `test_slash_id_never_forges_a_path_segment` failure — same fix as todo 2 or a
         separate gap.
    - 5. **[REVIEW] P2.** Once 2-4 ship, re-run MTDS's full `quality-gates.sh` to confirm this ripple is the only
         blocker.
  - [`plans/archive/2026_07/coinbase_bare_name_migration_execution_service_2026_07_10.md`](/plans/archive/2026_07/coinbase_bare_name_migration_execution_service_2026_07_10.md)
    — 0 open todos (complete/archived 2026-07-26, `execution-service@1267290`).
    - **[BACKEND] P2.** Re-key bare "COINBASE" → "COINBASE-SPOT" in
      `execution_cost_estimator.py`/`sor.py`/`venue_mapping.py`/`expected_start_dates.yaml`.
    - **[BACKEND] P3.** Grep `trade_handler.py`/`serializer.py` for bare COINBASE usage; re-key if lookup, leave if
      label/comment.
  - [`plans/archive/issues/cefi_future_instrument_type_no_candle_schema_contract_2026_07_21.md`](/plans/archive/issues/cefi_future_instrument_type_no_candle_schema_contract_2026_07_21.md)
    (archived — path updated 2026-07-29, was pointing at the pre-archival `active/issues/` location)
    - 1. **[DATA] P1.** Decide the CEFI `future` candle policy — standalone contract vs chain-bundle-only routing.
    - 2. **[DATA] P2.** Corpus-wide scan: which CEFI venues/instrument_types besides DERIBIT hit this.
    - 3. **[SCRIPT] P2.** Once ruled, register the contract (or fix routing) + add a regression test.
  - [`/plans/archive/issues/mdps_derivative_ticker_candle_schema_violation_2026_07_20.md`](/plans/archive/issues/mdps_derivative_ticker_candle_schema_violation_2026_07_20.md)
    - 2. **[DATA] P0.** Make a run whose every write failed EXIT NON-ZERO (fix the "N success/0 failed" summary to count
      written, not processed).
    - 3. **[DATA] P1.** Sweep the OTHER candle data_types for the same class of contract drift before the backfill.
  - [`plans/active/candle_canonical_path_migration_execution_2026_07_24.md`](/plans/archive/2026_07/candle_canonical_path_migration_execution_2026_07_24.md)
    (status: active — all 16 open todos are P0/P1, none to cap)
    - 1. **[DATA] P0.** Rebuild code tarballs for the 4 already-shipped repos (canonical-shape writer/reader changes
         live on VM images).
    - 2. **[DATA] P0.** VERIFY on `-test-` via `/data-pipeline-check-mdps` that the writer emits the canonical shape —
         gate before any prod-data executor.
    - 3. **[DATA] P0.** VERIFY readers dual-read correctly against both canonical and legacy-flat prefixes via
         `candle_read_prefixes`.
    - 4. **[SCRIPT] P0.** Run the sanctioned Tier-2 spot-VM single-walk census for a precise per-AG object count +
         dup-shape + empty-stem inventory.
    - 5. **[SCRIPT] P0.** Build the migration executor (P5) — idempotent, sharded, enumeration-file-driven,
         `--apply`-gated, checkpointed.
    - 6. **[SCRIPT] P0.** Implement the path transform in the executor (backward-add `instrument_type=`, keep SOURCE
         `data_type`, tf-normalise).
    - 7. **[SCRIPT] P0.** Implement DEDUP in the executor for the split-brain candle layout (~2x inflation on
         cefi/tradfi/prediction).
    - 8. **[SCRIPT] P0.** Implement PURGE of empty-stem objects (rewrite to `ticks.parquet` or delete if unrecoverable).
    - 9. **[SCRIPT] P0.** Implement QUARANTINE for unresolvable legacy TradFi `E1AF0_*_migrated_*` leaf ids (never
         guess).
    - 10. **[SCRIPT] P0.** Wire manifest re-record to the SOURCE-keyed row into the executor pass so skip-if-fresh is
          correct post-migration.
    - 11. **[SCRIPT] P0.** Upgrade the executor's pre-delete verification from SIZE-only to crc32c checksum.
    - 12. **[DATA] P0.** Extend `launch-canonical-migration-vm.sh` for this migration's per-AG SPOT fleet launch (≤2-3h
          target).
    - 13. **[DATA] P1.** P6 drain+snapshot: coordinate with the running `canonical-migration-cefi-wp*` raw_tick VMs
          before candle migration writes.
    - 14. **[DATA] P0.** P7 per-AG SPOT migration apply, in order defi→prediction→cefi→tradfi.
    - 15. **[DATA] P0.** P8 verify/reconcile: 4-surface reconciliation + extend the UAC canonical-path-violations oracle
          to `processed_candles/`.
    - 16. **[DATA] P1.** Root-cause + close the candle object↔manifest disconnect so skip-if-fresh can be trusted
          post-migration.
  - [`plans/active/issues/mdps_candle_path_instrument_type_segment_nondeterministic_2026_07_27.md`](/plans/archive/issues/mdps_candle_path_instrument_type_segment_nondeterministic_2026_07_27.md)
    — filed as a tracked follow-up to root-cause during the candle_canonical_path_migration_execution_2026_07_24.md work
    above (two consecutive `--force` writes for the identical CEFI:BINANCE-FUTURES shard landed at two different object
    paths — with vs. without the `instrument_type=` segment — despite byte-identical content).
    - 1. **[DATA] P3.** Root-cause why the `instrument_type=` segment's presence is non-deterministic for the identical
         shard (invocation-path-dependent vs. a resolution race).
- **Coverage / backfill / VM ops**:
  - [`plans/archive/issues/aster_capture_broken_coverage_and_completeness_2026_07_20.md`](/plans/archive/issues/aster_capture_broken_coverage_and_completeness_2026_07_20.md)
    — 0 open todos (status: open, narrative finding doc — no checkbox-tracked items, see file for recommended fix).
  - [`plans/active/aster_and_cefi_rolling_adv_feature_2026_07_21.md`](/plans/active/aster_and_cefi_rolling_adv_feature_2026_07_21.md)
    (status: active)
    - **[DATA] P2.** Extend MDPS's candle-building orchestration to cover
      `batch_aster`/`batch_hyperliquid`/`batch_lighter_api`/`batch_extended` raw trades.
    - **[DATA] P2.** Backfill historical candles for these 4 venues' existing raw trade history.
    - **[BACKEND] P2.** Design + implement strategy-side consumption of the ADV signal (position-size cap, min-history
      gate).
    - **[DATA] P3.** (stretch) Consider wiring `book_depth.py`'s `adv_30d_usd` input to the same Phase-1 utility with
      `window_days=30`.
  - [`plans/active/issues/tardis_concurrent_ip_lockout_2026_07_12.md`](/plans/archive/issues/tardis_concurrent_ip_lockout_2026_07_12.md)
    — 0 open todos (status: resolved, archived). **2026-07-28 stale-citation drop**: the prior BLOCKED-OPERATOR-DECISION
    "RE-RUN G4 from a clean slate" bullet is stale — the archived doc's own copy of this todo is checked `[x]` and its
    `resolved_by` field reads "GCS-lease mutex shipped + hardened to atomic CAS; production multi-VM wave confirmed zero
    code=274 rows; superseded by CLAUDE.md/vm-launcher-runbook.md Tardis 1-VM-cap HARD RULE"
    (`/codex/05-infrastructure/vm-launcher-runbook.md` § Tardis cap). G4 re-verification itself is tracked under
    `cefi_e6_cf7_relabel_and_attempted_failed_remeasure_2026_07_26.md` per the archived doc's own todo #2 note.
  - [`plans/active/issues/mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md`](/plans/active/issues/mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md)
    — 0 open todos (status: open, narrative finding doc — no checkbox-tracked items, see file for recommended fix).
  - [`plans/archive/issues/mtds_backfill_vm_startup_oom_rc137_2026_07_14.md`](/plans/archive/issues/mtds_backfill_vm_startup_oom_rc137_2026_07_14.md)
    — 0 open todos (closed/archived/record-only).
  - [`plans/active/issues/cefi_backfill_per_day_catalogue_reload_2026_07_20.md`](/plans/active/issues/cefi_backfill_per_day_catalogue_reload_2026_07_20.md)
    — 0 open todos (status: open, narrative finding doc — no checkbox-tracked items, see file for recommended fix).
  - [`plans/active/issues/cefi_content_migration_vm_wedged_worker_2026_07_23.md`](/plans/archive/issues/cefi_content_migration_vm_wedged_worker_2026_07_23.md)
    — 0 open todos (status: open, narrative finding doc — no checkbox-tracked items, see file for recommended fix).
  - [`plans/active/issues/cefi_high_attempted_failed_batch_cluster_2026_07_23.md`](/plans/archive/issues/cefi_high_attempted_failed_batch_cluster_2026_07_23.md)
    - **[OPS] P0.** Confirm status of this plan's Track-2 DERIBIT Wave-3 backfill; launch if not running (cap-1
      `tardis-concurrency-guard.sh`-gated).
    - **[REVIEW] P1.** Close `tardis_concurrent_ip_lockout_2026_07_12.md`'s open post-fix G4 re-measurement todo once
      fresh cefi history accumulates.
    - **[DATA] P1.** Trace the fresh (2026-07-21) "FUTURE/OPTION row requires 'expiry_date'" recurrence to specific
      symbols.
    - **[REVIEW] P2.** Decide whether `DP_RUN_MOSTLY_EMPTY` should distinguish static backlog from fresh failure.
    - **[DATA] P3.** If pursued, a targeted historical run.log pull to attribute the `VENUE_FETCH_FAILED` bucket's
      sub-causes.
  - [`plans/active/issues/onchain_venues_mislabeled_batch_tardis_lane_2026_07_20.md`](/plans/active/issues/onchain_venues_mislabeled_batch_tardis_lane_2026_07_20.md)
    - **[DATA] P1.** Re-partition EXTENDED-STARKNET `batch_tardis` → `batch_extended` (MERGE, de-dup against existing
      `batch_extended` objects).
    - **[DATA] P1.** Re-partition LIGHTER-ZKSYNC `ohlcv_1m` under `batch_tardis` on days <2026-04-17 →
      `batch_lighter_api`.
    - **[DATA] P2.** Quarantine PACIFICA-SOLANA (no valid lane, no catalogue rows, venue culled).
    - **[DATA] P1.** Find the WRITER that stamped `batch_tardis` on a non-Tardis venue and fix the derivation at source.
  - [`plans/active/issues/cefi_onchain_venues_mislabeled_batch_tardis_2026_07_20.md`](/plans/archive/issues/cefi_onchain_venues_mislabeled_batch_tardis_2026_07_20.md)
    — 0 open todos (status: open, narrative finding doc — no checkbox-tracked items, see file for recommended fix).
  - [`plans/active/issues/batch_live_filename_divergence_sanitize_symbol_2026_07_20.md`](/plans/archive/issues/batch_live_filename_divergence_sanitize_symbol_2026_07_20.md)
    - **[SERVICE] P1.** Add a write-time canonical-path guard to the Tardis cefi lane (currently has none).
    - **[SERVICE] P1.** Fix `tardis_shared.py:671` to escape `/` in the stem (`sanitize_file_stem`); migrate 48+
      KRAKEN-SPOT corrupt objects.
    - **[SERVICE] P1.** Turn `validate=True` on the two `tardis_cefi_shards.py` write sites; make violations FATAL not
      advisory.
    - **[DATA] P1.** Migrate/restate the historical non-canonical live objects (1,697 colon_wire cefi) as part of the
      surface-A re-run.
  - [`plans/archive/2026_08/issues/manifest_v6_batch3_residual_orphaned_work_2026_07_21.md`](/plans/archive/2026_08/issues/manifest_v6_batch3_residual_orphaned_work_2026_07_21.md)
    — **ARCHIVED 2026-08-10** (plan_reconciler, cross-cutting tranche): both items resolved, see the archived doc's own
    banner for evidence.
    - **[CODE] P3.** Add `quote_asset`/`margin_type` to the deployment-api data-status API response for cefi chain
      shards (gated on v6 canonicalisation landing).
    - **[UI] P3.** Make the deployment-ui coverage heatmap filterable by `quote_asset`/`margin_type` once the API
      exposes them.
  - [`plans/archive/issues/mtds_rule11_shard_count_stale_baseline_2026_07_21.md`](/plans/archive/issues/mtds_rule11_shard_count_stale_baseline_2026_07_21.md)
    — 0 open todos (status: open, narrative finding doc — no checkbox-tracked items, see file for recommended fix).
  - [`plans/active/instruments_cefi_g1_g5_gate_execution_2026_07_24.md`](/plans/active/instruments_cefi_g1_g5_gate_execution_2026_07_24.md)
    (status: active)
    - **[INFRA] P1.** Disable/update the dead-CLI legacy daily Workflow (`instruments-service-daily` uses the dead
      `--operation instrument` CLI).
    - **[INFRA] P1.** NEW: the all-AG no-`--asset-group` producer path crashes (exit 1, no traceback) — fix so one 00:00
      job covers all AGs.
    - **[INFRA] P1.** NEW: the t1-recon Cloud Run JOB specs have no IaC source — codify job specs so they can't silently
      rot.
    - **[SCRIPT] P2.** Registry gap: `lifecycle-catalogue-regen-prediction` is in the TF `for_each` but missing from
      `_LIFECYCLE_CATALOGUE_JOBS`.
    - **[SCRIPT] P0.** G1 — instruments-service correct per-day: code right + deterministic + on LDR + QG-green; sample
      day audited cell-correct.
  - [`plans/active/issues/cefi_content_migration_fleet_half_incomplete_2026_07_26.md`](/plans/active/issues/cefi_content_migration_fleet_half_incomplete_2026_07_26.md)
    (status: open) — the 44-way sharded cefi content-canonicalisation `--apply` fleet did NOT complete corpus-wide (21
    of 44 shards died partway through).
    - **[SCRIPT] P1.** Relaunch the 21 dead/incomplete shards. **2026-07-28 retag**: no `[OPERATOR]` gate needed — the
      source doc itself already reclassified this to `[SCRIPT]` P1 (VM launches are AO-dispatchable by default per
      `/codex/05-infrastructure/vm-launcher-runbook.md`; this is a bounded relaunch of 21 NAMED shards via an existing
      idempotent script, not a new design/scope decision). Ordinary AO-dispatchable todo, no operator sign-off needed.
    - **[SCRIPT] P2.** Re-run the corpus-wide `run.log` grep to confirm all 44/44 complete once relaunched.
    - **[BACKEND] P2.** Cross-reference with `cefi_content_migration_vm_wedged_worker_2026_07_23.md`'s Recommendation
      item 1.
- **Manifest / data-status / honest-coverage**:
  - [`plans/archive/issues/manifest_completeness_full_corpus_map_build_2026_07_20.md`](/plans/archive/issues/manifest_completeness_full_corpus_map_build_2026_07_20.md)
    - 1. **[DATA] P0.** VERIFY the prod projection before sizing the win — is `_publish_emission_check` actually firing
         on prod MDPS backfills.
    - 5. **[DATA] P0.** The 1.58 GB defi-prd index is its own P0 — audit every `read_availability_index` caller on defi
         for OOM risk.
    - 6. **[DOC] P2.** Record in codex that the per-VM manifest flush is already debounced (50 entries/5.0s).
  - [`plans/active/issues/honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md`](/plans/active/issues/honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md)
    (14 open — every P0/P1 listed, P2/P3 capped)
    - **[DESIGN] P1.** Fix the mockup's leaf model everywhere it still needs it (Finding 1) — re-verify
      SPORTS/PREDICTION don't have an analogous mistake.
    - **[DESIGN] P1.** Design the CEFI instrument-definition parquet resharding (Finding 2, decided) — reshard to (date,
      venue, instrument_type); design only, gated on operator sign-off.
    - **[CODE] P1.** Widen the writer-fix scope to Solana DeFi + CURVE-OPTIMISM (blank `instrument_type` bug hits 7 more
      venues).
    - **[CODE] P1.** Pull the real per-instrument_type breakdown for DERIBIT live and confirm whether OPTION coverage is
      actually healthy.
    - **[CODE] P1.** Add `missing_dates`/`dates_found_list` to the per-instrument_type and per-underlying breakdown
      entries (deployment-api + deployment-ui).
    - **[CODE] P1.** Move `market_metadata` off the MTDS `per_venue_per_data_type_daily` axis onto the
      `reference_scope`-based model.
    - **[VERIFY] P1.** Raw-parquet spot-check the 5 additional CeFi venues flagged as likely hitting the same multi-type
      blank-collapse.
    - **[CODE] P1.** Backfill historical CeFi/TradFi manifest rows with the corrected per-instrument_type split.
    - +6 more P2/P3 — see file for the rest.
  - [`plans/active/issues/coverage_floor_registries_no_cross_propagation_2026_07_17.md`](/plans/active/issues/coverage_floor_registries_no_cross_propagation_2026_07_17.md)
    - **[CODE] P1.** Add a falsifier test that fails CI when `coverage_starts.py` and `venue_mapping.py` disagree on a
      venue's start date.
    - **[DATA] P1.** Resolve the 8 confirmed multi-year/multi-month CeFi mismatches
      (BITFINEX/KRAKEN/COINBASE-SPOT/DERIBIT/OKX/BINANCE/BYBIT/HYPERLIQUID).
    - **[DATA] P2.** Resolve the CME mismatch (`coverage_starts.py` 2010-01-01 `# TODO verify` vs `venue_mapping.py`
      2020-01-01).
    - **[DATA] P2.** Resolve the POLYMARKET mismatch (CLOB-launch vs first-actual-instrument, ~2.3-year gap).
    - **[DATA] P3.** Resolve the small 1-21 day DeFi protocol drifts + decide the AAVE_V3 chain-axis question.
    - **[DATA] P3.** Publish an explicit key-mapping table between `coverage_starts.py` and `venue_mapping.py` keys.
  - [`plans/archive/issues/instrument_availability_hive_canonicalisation_2026_07_21.md`](/plans/archive/issues/instrument_availability_hive_canonicalisation_2026_07_21.md)
    - 7. **[DATA] P1.** PROVE the fixed writers green on one real day, then migrate historical flat
      `instrument_availability`/`market_lifecycle`/`futures_contracts` objects into full hive.
    - 8. **[REVIEW] P1.** On writer ship, record the `instrument_availability` full-hive cutover date in the
         canonical-cutover-register.
  - [`plans/active/issues/canonical_path_oracle_blind_to_filename_stem_2026_07_20.md`](/plans/active/issues/canonical_path_oracle_blind_to_filename_stem_2026_07_20.md)
    - **[DATA] P1.** Re-run CeFi surface-A reconciliation with the fixed oracle and restate the verdict.
    - **[DATA] P2.** The legitimately-unresolvable objects need a quarantine/honest-absence disposition (separate
      design).
  - [`plans/archive/issues/canonical_closeout_open_questions_2026_07_18.md`](/plans/archive/issues/canonical_closeout_open_questions_2026_07_18.md)
    — 0 open todos (status: open, narrative finding doc — no checkbox-tracked items, see file for recommended fix).
  - [`plans/active/issues/estate_orphan_assessment_2026_07_21.md`](/plans/active/issues/estate_orphan_assessment_2026_07_21.md)
    - 3. **[INFRA] P1.** Run the orphan sweep for defi/cefi/tradfi/prediction on a VM — only tradfi completed;
      defi/prediction hit a throughput cliff; cefi failed twice (blocked on `migration_orphan_sweep_performance_decay`
      fix).
    - 4. **[CODE] P2.** Make the manifest load resumable/streamed in `migration_orphan_sweep.py` (folded into the
         performance-decay doc).
    - 5. **[CODE] P3.** `GcsEventSink` never `.shutdown()`s its background `ThreadPoolExecutor` — costs real SPOT-VM
         minutes.
    - 6. **[CODE] P2.** Give `backfill_orphan_class_e.py --apply` a batched-incremental `record_cells()` call
         (checkpoint/resume).
  - [`plans/active/issues/phantom_audit_estate_coverage_gap_2026_07_10.md`](/plans/active/issues/phantom_audit_estate_coverage_gap_2026_07_10.md)
    — 0 open todos (status: open, narrative finding doc — no checkbox-tracked items, see file for recommended fix).
  - [`/plans/archive/issues/features_by_date_root_canonicalisation_2026_07_21.md`](/plans/archive/issues/features_by_date_root_canonicalisation_2026_07_21.md)
    - 6. **[DATA] P1.** PROVE the fixed delta_one + volatility writers green on one real day, then migrate historical
      objects UP into the `by_date/day=` tree.
    - 7. **[DATA] P1.** Re-sync the availability manifest + data-status render for the migrated features cells.
    - 8. **[REVIEW] P1.** On writer ship, record the features `by_date/day=` cutover date in the
         canonical-cutover-register.
  - [`plans/active/issues/mdps_features_deadcode_consolidation_2026_07_20.md`](/plans/active/issues/mdps_features_deadcode_consolidation_2026_07_20.md)
    (exactly 8 open — all listed)
    - 1. **[SCRIPT] P2.** S1-a — `launch-prediction-features-vm.sh` BROKEN; superseded by
         `launch-features-vm.sh --feature-family cross_instrument`; DELETE + repoint registry.
    - 2. **[SCRIPT] P2.** S1-b — `launch-mdps-features-live.sh` non-runnable but still registered (5 rows); DELETE
         launcher + rows OR finish the dispatcher branch.
    - 3. **[SCRIPT] P1.** S1-c — `mdps-sports-<year>-<ts>` emitted but registered in NEITHER registry — sports MDPS
         shard invisible to zombie watchdog.
    - 4. **[SCRIPT] P3.** S2-a — trim `launch-features-backfill-vm.sh` to the redirect stub (dead body, duplicate
         helper).
    - 5. **[SCRIPT] P3.** S2-b — delete the 8 stale `features_*_service` keys in `setup-data-pipeline-vm.sh`
         SERVICE_TARBALLS.
    - 6. **[SCRIPT] P3.** S3-a — delete MDPS one-offs past `Delete-when` after verifying each condition.
    - 7. **[SCRIPT] P3.** S3-c — repoint `smoke_matrix.py` SSOT citations to `launch-features-vm.sh` + the codex
         smoke-matrix doc.
    - 8. **[SCRIPT] P3.** S3-b — sports dual entrypoint needs operator/design adjudication (fold behind family flag OR
         bless submodule).
  - [`/plans/archive/issues/mdps_prior_seed_context_thread_unsafe_2026_07_20.md`](/plans/archive/issues/mdps_prior_seed_context_thread_unsafe_2026_07_20.md)
    - 3. **[DATA] P1.** Assess blast radius on EXISTING candle data — any past MDPS run with `max_workers>1` over a
      heterogeneous file list.
  - [`plans/archive/issues/migration_orphan_sweep_performance_decay_2026_07_22.md`](/plans/archive/issues/migration_orphan_sweep_performance_decay_2026_07_22.md)
    - 7. **[CODE] P3.** Genuinely stream `_load_manifested_cells()`'s parquet read instead of relying on a bigger
      machine type.
  - [`plans/archive/2026_07/mdps_features_reduced_artifact_tracker_2026_06_28.md`](/plans/archive/2026_07/mdps_features_reduced_artifact_tracker_2026_06_28.md)
    — ARCHIVED 2026-07-27, 0 open todos (all 9 mini-plans confirmed archived/complete).
  - [`plans/active/data_pipeline_check_mdps_features_2026_07_20.md`](/plans/active/data_pipeline_check_mdps_features_2026_07_20.md)
    (status: active — 28 open; 22 P0/P1 listed, 6 P2 capped)
    - 8. **[DATA] P0.** RUN + VALIDATE `/data-pipeline-check-mdps` e2e across all MVP candle shards.
    - 9. **[DATA] P0.** RUN + VALIDATE `/data-pipeline-check-features` e2e across all MVP feature shards.
    - 10. **[DATA] P1.** Steady-state benchmark VMs per representative shard-type; project full-history time + cost.
    - 11. **[DATA] P0.** Cross-repo orphan/lineage audit (MTDS→MDPS→features→ml/strategy) + MIGRATE to zero orphans.
    - 12. **[SCRIPT] P1.** Backfill-processing path code-ready + OPTIMIZED (within-VM multiproc, faster-libs).
    - 13. **[DATA] P0.** Produce concrete ETA to backfill all remaining DeFi MVP.
    - 15. **[DATA] P1.** Full DeFi-MVP candle backfill on real infra — GATED on the canonical-path migration's P8.
    - NEW todo. **[SCRIPT] P1.** Add the all-NaN-parquet-vs-`captured` assertion to `/data-pipeline-check-mdps`.
    - NEW todo. **[DATA] P0.** Verify whether MDPS `max_workers` actually OVERLAPS the GCS writes (up to ~8x speedup if
      fixed).
    - NEW todo. **[DATA] P0.** Enumerate the candle-coverage GAP per (asset_group, venue, data_type, timeframe).
    - NEW todo. **[DATA] P0.** Run `/data-pipeline-check-mdps` across all relevant AGs NOT already in candles.
    - NEW todo. **[DATA] P0.** Run `/data-pipeline-check-features` across ALL shards (8 families x valid AGs).
    - NEW todo. **[DOC] P1.** Correct `/codex/05-infrastructure/spot-vms-for-backfill.md`'s preemption-signal claim.
    - NEW todo. **[SCRIPT] P1.** Close residual risk 1: make arg-required launchers relaunchable.
    - NEW todo. **[DATA] P0.** VERIFY the prod projection on a real prod-bucket MDPS run before sizing the win.
    - NEW todo. **[SCRIPT] P0.** Implement F1+F2 (UTL `manifest_completeness.py`) + F3 (MDPS `_publish_emission_check`).
    - NEW todo. **[DATA] P0.** Audit every `read_availability_index` caller on defi for OOM risk.
    - NEW todo. **[SCRIPT] P0.** Fix the shared seed context + regression test (PREREQUISITE for raising concurrency).
    - NEW todo. **[DATA] P1.** Blast radius: did any PAST prod MDPS run use max_workers>1 over a heterogeneous list.
    - NEW todo. **[SCRIPT] P0.** Implement R1 (concurrent date-subprocesses), the months→weeks throughput lever.
    - NEW todo. **[SCRIPT] P1.** Implement R1 bounded-concurrent `_run_date_as_subprocess` dispatch.
    - NEW todo. **[DATA] P0.** Real-VM re-measure of end-to-end per-instrument-day rate after the read-path fix.
    - +6 more P2 — see file for the rest.
  - [`plans/active/issues/backfill_smoke_write_path_canonical_audit_2026_07_20.md`](/plans/archive/2026_08/issues/backfill_smoke_write_path_canonical_audit_2026_07_20.md)
    - 1. **[DATA] P1.** instruments-service: canonicalise the `instrument_availability` write using the sink PREFIX
         mechanism, NOT the partition dict.
    - 2. **[DATA] P1.** market-tick-data-service: rule on and fix the cefi chain tail — `partitioned_writer.py:291-293`
         populates `quote_asset`/`margin_type` for tradfi only.
    - 3. **[DOCS] P2.** instruments-service + market-tick-data-service: correct the three in-repo comments that assert
         the IS live writer emits the hive layout.
    - 4. **[SCRIPT] P2.** unified-trading-pm: add a Phase-0 `-test-` assertion on the resolved WRITE bucket to
         `data-pipeline-check-mdps`/`data-pipeline-check-features`.
    - 5. **[DOCS] P2.** unified-trading-pm: add an explicit "never pass `--allow-live-prod-writes`" prohibition to
         `data-pipeline-check-mtds/SKILL.md`.
    - 6. **[DATA] P3.** instruments-service: decide whether `market_lifecycle`/`futures_contracts` are in the canonical
         shard grammar's scope.
  - [`plans/active/issues/pipeline_e2e_check_vm_name_collision_2026_07_12.md`](/plans/archive/issues/pipeline_e2e_check_vm_name_collision_2026_07_12.md)
    — 0 open todos (status: open, narrative finding doc — no checkbox-tracked items, see file for recommended fix).
  - [`plans/active/issues/fail_hard_canonical_enforcement_design_2026_07_20.md`](/plans/active/issues/fail_hard_canonical_enforcement_design_2026_07_20.md)
    - **[WRITER] P1.** A-iso — rebuild the `tardis_cefi_shards.py:144` groupby loop as per-shard isolated. Ships alone.
    - **[DESIGN] P1.** Close the three §5 gaps (derivative-bundle column gate; live-lane dual-resolver reconciliation;
      read marker disposition) before write-enforce.
    - **[WRITER] P2.** Pass `violation_classes={STRUCTURAL}` explicitly at the 3 `canonical_path_violations` write
      callsites.
    - **[DATA] P2.** Stage 0 — classify-and-log at every write/manifest/read site, zero behaviour change.
    - **[UAC] P2.** `is_quarantined_instrument_id` + `ResolutionEvidence` + the registry (composes, no fenced-file
      edit).
    - **[DATA] P3.** Schema v10 `instrument_id_form` + backfill classification (Stage 2), after the v2 dedup `--apply`.
- **Adapters / QG / process**:
  - [`plans/active/issues/breaking_change_differ_blind_to_registry_data_dicts_2026_07_09.md`](/plans/active/issues/breaking_change_differ_blind_to_registry_data_dicts_2026_07_09.md)
    - **[DESIGN] P1.** Specify the contract-surface extension to `detect_breaking_change.py` (allowlist mechanism, which
      mutations are breaking).
    - **[FIX] P1.** Implement the extension in `scripts/cicd/detect_breaking_change.py` + tag the three registry
      constants as contract surface in UAC.
    - **[TEST] P1.** Add cases to `test_detect_breaking_change.py` including the exact `23fa3a99` regression shape.
    - **[FIX] P1.** Close the SIT coverage gap: add the `build_expected('cefi')` + capability/fold cross-repo invariant
      to `system-integration-tests`.
    - **[DESIGN] P2.** Decide whether provider (UAC) registry-change promotes should fan out consumer QG (≥ IS) as a
      gate.
    - **[DOCS] P2.** Once landed, update the breaking-differ section of `/codex/08-workflows/ci-cd-flow.md`.
    - **[VERIFY] P1.** Reproduce end-to-end: differ on `23fa3a99` returns `is_breaking: true` post-fix; the new SIT
      invariant goes RED.
  - [`plans/archive/issues/instruments_service_cefi_qg_red_on_ldr_head_2026_07_08.md`](/plans/archive/issues/instruments_service_cefi_qg_red_on_ldr_head_2026_07_08.md)
    — 0 open todos (Option A shipped `unified-api-contracts@0ab1074a` + `instruments-service@c0f5529c`, per
    `instruments_remaining_work_audit_2026_07_10.md`'s 2026-07-10 decision-ledger entry #1; resolved + archived
    2026-07-30).
  - [`plans/archive/issues/deployment_api_cefi_venue_canonical_compare_test_regression_2026_07_21.md`](/plans/archive/issues/deployment_api_cefi_venue_canonical_compare_test_regression_2026_07_21.md)
    — 0 open todos (closed/archived/record-only).
  - [`plans/active/issues/two_agents_slot3_collision_and_yahoo_finance_red_tree_2026_07_15.md`](/plans/archive/2026_08/issues/two_agents_slot3_collision_and_yahoo_finance_red_tree_2026_07_15.md)
    — 0 open todos (status: open, narrative finding doc — no checkbox-tracked items, see file for recommended fix).
  - [`plans/archive/issues/mtds_mdps_order_book_imbalance_duplicated_2026_07_07.md`](/plans/archive/issues/mtds_mdps_order_book_imbalance_duplicated_2026_07_07.md)
    — 0 open todos (status: resolved, archived 2026-07-27 — UAC-side retirement shipped
    `unified-api-contracts@49314f51`; numeric-agreement check closed MOOT per the doc's own zero-production-rows
    finding).
  - [`plans/active/issues/per_venue_scope_key_provisioning_incomplete_2026_07_23.md`](/plans/active/issues/per_venue_scope_key_provisioning_incomplete_2026_07_23.md)
    - **[HUMAN] P1.** Create `bybit-trade-api-key`/`bybit-trade-api-key-secret` in GCP — the one remaining step to
      complete Bybit's scope split.
    - **[HUMAN] P2.** Decide on OKX/Hyperliquid's scope-separation design, if wanted at all.
    - **[HUMAN] P3.** Decide whether to build the Aster execution adapter and/or provision Upbit/Kraken/Bitfinex/Bitget
      credentials.
  - [`/plans/archive/issues/rotate_exchange_keys_stale_venue_registry_2026_07_23.md`](/plans/archive/issues/rotate_exchange_keys_stale_venue_registry_2026_07_23.md)
    - **[SCRIPT] P1.** Verify every venue in `rotate-exchange-keys/main.py`'s key-pattern list against live GCP Secret
      Manager.
    - **[SCRIPT] P1.** Confirm whether `rotate-exchange-keys` is actually invoked on a schedule/trigger.
    - **[SCRIPT] P2.** Fix the corrected venue list in `rotate-exchange-keys/main.py` once verified.
  - [`plans/archive/issues/tarball_rotation_breaks_vm_recovery_2026_07_20.md`](/plans/archive/issues/tarball_rotation_breaks_vm_recovery_2026_07_20.md)
    — 0 open todos (status: open, narrative finding doc — no checkbox-tracked items, see file for recommended fix).
  - [`plans/archive/issues/ui_coverage_ts_venue_category_v2_rename_gap_2026_07_10.md`](/plans/archive/issues/ui_coverage_ts_venue_category_v2_rename_gap_2026_07_10.md)
    — 0 open todos (status: open, narrative finding doc — no checkbox-tracked items, see file for recommended fix).
  - [`plans/archive/issues/vm_backfill_data_correctness_findings_2026_06_29.md`](/plans/archive/issues/vm_backfill_data_correctness_findings_2026_06_29.md)
    — 0 open todos (status: open, narrative finding doc — no checkbox-tracked items, see file for recommended fix).
  - [`plans/archive/issues/group_c_cloud_run_job_failures_triage_2026_07_16.md`](/plans/archive/issues/group_c_cloud_run_job_failures_triage_2026_07_16.md)
    - **[INFRA] P1.** Decide + implement a default-to-yesterday date bridge for MTDS's batch CLI (needs an owner
      decision on which repo).
  - [`plans/archive/2026_07/is_daily_enum_capture_heal_2026_07_07.md`](/plans/archive/2026_07/is_daily_enum_capture_heal_2026_07_07.md)
    (status: draft)
    - **[CODE] P0.** Add `exc_info=True` to the UTL shard-isolation catch so the swallowed exception surfaces in logs.
    - **[CODE] P0.** With the real traceback now visible, re-run `is-daily-enum-{prediction,sports}` and fix the real
      root cause.
    - **[VERIFY] P1.** Backfill the missed windows: prediction 07-01→07-06, sports 06-28→07-06.
- **Cross-AG-touching (cefi + defi/prediction, referenced here for the cefi slice)** — primary tracking:
  [`/plans/active/defi_consolidated_closeout_2026_07_18.md`](/plans/active/defi_consolidated_closeout_2026_07_18.md) /
  [`/plans/active/prediction_consolidated_closeout_2026_07_18.md`](/plans/active/prediction_consolidated_closeout_2026_07_18.md):
  - [`defi_onchain_derivable_values_and_date_drift_2026_06_20.md`](/plans/archive/2026_07/defi_onchain_derivable_values_and_date_drift_2026_06_20.md)
    — ✅ ARCHIVED 2026-07-27, all 14 todos done: Pyth Hermes/jitoSOL resolved as **clip**
    (`unified-api-contracts@4a29261e`), Latent Bug-class-3 local-fallback sweep shipped (`instruments-service@8b02b647`;
    broader sweep beyond that concrete precedent filed separately at
    `/plans/archive/issues/defi_broader_local_fallback_vs_uac_sweep_2026_07_27.md`).
  - [`plans/active/defi_pipeline_e2e_and_coverage_validation_2026_06_20.md`](/plans/active/defi_pipeline_e2e_and_coverage_validation_2026_06_20.md)
    (status: active)
    - **[VERIFY] P0.** Phase-D gate — full Stage-4 historical carry tracer over 2022-01-01..today across all 7
      archetypes (REOPENED 2026-07-12, prior ✅ was logic-only).
    - **[SCRIPT] P1.** Re-run `scripts/phase_d_gate.py` against real 2022→today data once the DeFi backfill reaches full
      coverage.
    - **[AGENT] P2.** `SolidlyCLForkPool` historical golden-swap validation (≥20-Velodrome + ≥20-Aerodrome real on-chain
      fixtures).
  - [`plans/active/cefi_deribit_binance_futures_bundle_verification_2026_06_20.md`](/plans/active/cefi_deribit_binance_futures_bundle_verification_2026_06_20.md)
    (status: active)
    - **[SCRIPT] P2.** Spot-check: download 3 random days of DERIBIT options; verify `options_chain` greeks / IVs
      populated.
    - **[SCRIPT] P2.** Spot-check: download 1 day of BINANCE-FUTURES perps; verify funding + open_interest populated.
  - [`plans/active/cefi_ml_directional_continuous_live_2026_06_20.md`](/plans/active/cefi_ml_directional_continuous_live_2026_06_20.md)
    (status: active)
    - **[AGENT] P0.** Continuous ML prediction signal live on real capital across OKX + Binance + Bybit for ≥7
      continuous days — GATED on wallet-key/kill-switch operator action.
    - **[VERIFY] P0.** Backtest fidelity via the 2-year batch backtest config grid — architecture verified, the actual
      grid run is still pending operator scheduling.
    - **[RESEARCH] P2.** Not currently scheduled (2026-07-24: reworded off the bare DEFERRED-then-dash marker, which is
      reserved for whole-plan migrations per the plan-discipline gate — this is a single low-priority research idea, not
      a plan-level deferral, and has no successor plan to banner): volume as a first-class feature for the cs/ext ML
      models.
  - [`plans/archive/issues/dp_catalog_not_running_sports_prediction_2026_07_15.md`](/plans/archive/issues/dp_catalog_not_running_sports_prediction_2026_07_15.md)
    (status: resolved, 2 open)
    - **[OPS] P2.** Verify the next scheduled `lifecycle-catalogue-regen-sports` run promotes successfully +
      `prod/catalog.parquet` row count is `>= 27,216`.
    - **[INFRA] P3.** Grant `lifecycle-catalogue-regen@...` `storage.objects.create` so structured events stop silently
      403ing.
  - [`plans/active/prediction_capture_incident_remediation_2026_07_06.md`](/plans/active/prediction_capture_incident_remediation_2026_07_06.md)
    (status: active, 9 open — top 3 shown, full list on the prediction closeout)
    - **[VERIFY] P0.** Demo dry-run: returned tickers are genuine perps, 0 event contracts (capture into a NON-PROD
      sink).
    - **[CODE] P1.** Make the perp base URL config-driven (`KALSHI_PERP_ENV=demo|prod`), delete the hardcoded
      events-host const.
    - **[VERIFY] P1.** Pin the prediction-store event-capture gap — are Kalshi/Polymarket EVENT markets captured
      correctly in the PREDICTION store.
  - [`plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md`](/plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md)
    (status: active, 8 open — top 3 shown, full list on the prediction closeout)
    - **[SCRIPT] P0.** Populate POLYMARKET instrument lifecycle start/end + bound manifest empty-emission to it — BIG
      finding, data-correctness/honest-coverage semantics.
    - **[SCRIPT] P1.** e2e-testing/instruments-service — series-scoped historical backfill: 2025-10→2026-04 mid-gap is
      the precise residual.
    - **[OPS] P2.** Tarball-overwrite race — a concurrent fleet `create-code-tarballs` clobbers a freshly-rebuilt
      tarball before a new VM's boot-fetch.
  - [`plans/active/prediction_live_clob_depth_capture_2026_07_24.md`](/plans/active/prediction_live_clob_depth_capture_2026_07_24.md)
    (status: active, 1 open)
    - **[DATA] P2.** Verify END-TO-END depth-history retention — the RAW live book store is rolling-latest-window per
      instrument, not a multi-hour archive.
  - [`plans/archive/2026_07/prediction_perps_kalshi_polymarket_parked_2026_07_24.md`](/plans/archive/2026_07/prediction_perps_kalshi_polymarket_parked_2026_07_24.md)
    (status: active, 1 open)
    - **[SCRIPT] P1.** Polymarket-perp enumerator — BLOCKED-UPSTREAM (no public perps API exists yet, confirmed
      2026-06-22); scaffold shipped, auto-flows on endpoint availability.
- **Newly discovered (completeness check, 2026-07-24)** — cefi-tagged docs (`asset_group: [..., cefi, ...]`) not
  previously named in this section; several are already discussed in Track 1-7 above with full detail, but are listed
  here too so this section alone stays a complete open-todo index:
  - [`plans/active/canonical_id_builder_retrofit_checklist_2026_07_08.md`](/plans/archive/2026_08/canonical_id_builder_retrofit_checklist_2026_07_08.md)
    (status: active, 9 open — 3 P1 shown, 6 P2/P3 capped)
    - **[DATA] P1.** Retrofit the ~48 DeFi adapters that build `instrument_key` as an ad hoc f-string to
      `build_canonical_instrument_id`.
    - **[DATA] P1.** Resolve the non-canonical TYPE-token question before retrofitting the above
      (VAULT/SUPPLY/BORROW/etc. aren't real InstrumentType values).
    - **[DATA] P1.** Fix the "no VENUE:TYPE: wrap at all" gap in both Prediction adapters (Kalshi/Polymarket store bare
      raw provider ids).
    - +6 more P2/P3 — see file for the rest.
  - [`plans/active/cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md`](/plans/active/cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md)
    (status: active, 22 open — 14 P0/P1 shown, 8 P2 capped)
    - **[UAC] P0.** Map the index perps (SPXUSDT/NAS100/SPYUSDT/XAUUSDT) to the CME index-future canonical, carrying the
      scale/multiplier.
    - **[DESIGN] P0.** execution-service — IBKR equities execution adapter is the GATING unlock for the single-stock
      basis winners.
    - **[DESIGN] P0.** strategy-service + UAC — replace the fixed net-profitable-12 with a broad universe + dynamic
      live-net-carry ranking.
    - **[SCRIPT] P0.** Propagation ops (B1/B3/B4) — run the IS→catalogue→enumerator→MTDS chain on real infra to
      completion.
    - **[SCRIPT] P1.** instruments-service — pass the equity-perp filter + stamp EQUITY_PERP/TOKENIZED_EQUITY via the
      shared canonical builder.
    - **[SCRIPT] P1.** Backfill the 3 KRX stocks via guardrailed Yahoo (operator ladder).
    - **[UAC] P1.** Databento L-floor boundary PRECISION — measure the exact earliest-accessible date per level for our
      subscription.
    - **[SCRIPT] P1.** market-tick-data-service — capture indexPrice/markPrice/fundingRate for the equity-perps as a
      first-class data_type.
    - **[DESIGN] P1.** strategy-service — INDEX-perp cash-and-carry as the FIRST equity-perp archetype.
    - **[DESIGN] P1.** strategy-service — the basis archetype's edge = NET basis; restrict entry to US market hours.
    - **[RESEARCH] P1.** instruments-service — check OKX/Bybit/Hyperliquid for a WTI/Brent OIL perp.
    - **[DESIGN] P1.** strategy-service — single-stock basis archetype on the 12 net-profitable names.
    - **[SCRIPT] P1.** e2e-testing — re-run the NET-basis backtest with DIVIDENDS priced into the long cash-stock leg.
    - **[RESEARCH] P1.** instruments-service — KEEP crude/gold/natgas/SPX/NDX perps despite net≤0 NOW (carry flips with
      the futures curve).
    - +8 more P2 — see file for the rest.
  - [`plans/active/data_completion_cefi_2026_07_15.md`](/plans/active/data_completion_cefi_2026_07_15.md) (status:
    active, 26 open — 20 P0/P1 (18 shown, 2 folded into the row above), 6 P2/P3 capped; mostly MIGRATED FROM
    `cefi_manifest_canonicalisation_2026_06_01.md`)
    - **[DATA] P0.** ⑧ IS cefi reference-universe gap — root-cause code fix shipped; operational backfill re-run + CLOB
      sub-part remain.
    - **[CODE] P1.** execution-service — DeFi raw-tick loaders (`data/loaders/defi.py`) still legacy, need a `chain`
      kwarg + defi instrument-id→chain mapping.
    - **[CODE] P1.** deployment-api FLAG-3 — decide the UAT health-summary bucket model (keep aggregate form or migrate
      to per-AG buckets).
    - **[CODE] P1.** deployment-api CeFi pipeline_mode dedup + drilldown filter — add a cefi parity regression test +
      the filter param.
    - **[DATA] P1.** Before the REAL `_index` rebuild — multi-year dry-run phantom spot-check.
    - **[DATA] P0.** NEXT SESSION — execute the migration: gap-fill, irreversible orphan-sweep, E5 rebuild, E7 verify,
      E8 legacy-bucket delete.
    - **[DATA] P0.** C-pipeline_mode RIDER — the `pipeline_mode=` partition lands in this walk.
    - **[DATA] P1.** C-source RIDER — the `source` column lands in this walk.
    - **[DATA] P0.** Post-walk: re-read the canonical `_index` data-state and confirm 100% v9 / legacy-only cells = 0.
    - **[DATA] P0.** Orphan sweep + bucket-state evidence — `-prd` is intermediate form; E5/E7 must delete the
      legacy-FORM `-prd` objects too.
    - **[DATA] P0.** RETRACTION of the earlier "E4-BUG" P0 finding — it was wrong; no migrator fix needed.
    - **[DATA] P0.** E4 remaining work = ORPHAN SWEEP + gap-fill (irreversible delete of ~1.2M legacy orphan objects).
    - **[DATA] P1.** E6 CF-7 relabel — COINBASE↔COINBASE-SPOT, blank venue/data_type → canonical; investigate the 50%
      attempted_failed rows.
    - **[DATA] P0.** E7 Verify — `cf_manifest_audit_2026_06_01.py` → CF-1…CF-12 GREEN on data-state.
    - **[DATA] P0.** E8 IRREVERSIBLE — after E7 GREEN, delete legacy `market-data-tick-cefi` permanently.
    - **[DATA] P0.** Absorbed from `cefi_processed_candles_manifest_file_disconnect` — root cause corrected; 3 real
      sub-findings to action.
    - **[CODE] P1.** ⑦ cefi could-exist denominator seed — build the `--catalog-path` parquet + run the v2 enumerator
      against the canonical `_index`.
    - **[DATA] P1.** cefi `instruments-store` `_index` v8→v9 single-walk — real audit found 18,076 L6-legacy-only cells;
      re-audit against the successor doc before flipping.
    - +6 more P2/P3 — see file for the rest.
  - [`plans/active/issues/adapter_findings_gcs_manifest_deployment_api_reconciliation_gap_2026_07_08.md`](/plans/active/issues/adapter_findings_gcs_manifest_deployment_api_reconciliation_gap_2026_07_08.md)
    - **[VERIFY] P1.** Check whether manifest regeneration is automatic or requires an explicit re-enumeration trigger
      when an adapter's stamped `instrument_type` changes.
    - **[VERIFY] P2.** Spot-check 2-3 more findings from the smoke-test doc across all 3 layers.
    - **[DECISION] P2.** Once the AAVE_V3 pilot trace lands, decide the reconciliation cadence for the remaining 58
      findings.
  - [`plans/archive/issues/aster_mtds_failure_count_regression_2026_07_07.md`](/plans/archive/issues/aster_mtds_failure_count_regression_2026_07_07.md)
    — 0 open todos (resolved/archived 2026-07-26: count self-recovered to 150, well below the 06-22 baseline; see doc's
    Progress Log for the full evidence trail).
    - **[SCRIPT] P2.** Once root-caused: re-run recovery or diagnose a new adapter break.
  - [`plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md`](/plans/archive/issues/candle_feature_canonical_path_divergence_2026_07_20.md)
    (exactly 8 open — all listed)
    - 2. **[DATA] P1.** Corpus-wide count of zero-length-stem candle objects; purge or repair.
    - 3. **[DATA] P1.** Canonicalise TradFi candle leaf ids (`E1AF0_*_migrated_*` → `VENUE:TYPE:SYMBOL`) — 93% of the
         tradfi corpus now sitting in `_quarantine/` unresolved.
    - 7. **[DATA] P0.** Root-cause the candle object↔manifest disconnect — cross-AG confirmed, skip-if-fresh moot
         fleet-wide until fixed.
    - 9. **[DATA] P1.** Split-brain candle layout — quantify the corpus-wide split; fold into the A/B/C migration.
    - 13. **[DATA] P3.** `ProvisionalTargetIndex` keys lack a bucket component — fix before trusting the split-brain
          count precisely.
    - 15. **[DOC] P3.** UTL's `build_canonical_candle_path()` docstring example still shows superseded semantics.
    - 16. **[SCRIPT] P3.** Investigate `CEFI:DERIBIT:trades:24h`'s force-leg `off_template=29` classification mismatch.
    - 19. **[SCRIPT] P2.** Fix `_copy_verify_delete()`'s retry-idempotency gap — a verification-FAILED destination is
          never re-copied on a subsequent run.
  - [`plans/active/issues/cefi_batch_manifest_blank_instrument_type_on_failure_2026_07_12.md`](/plans/active/issues/cefi_batch_manifest_blank_instrument_type_on_failure_2026_07_12.md)
    - **[DATA] P3.** GATED on the P1-corrected cefi backfill re-capture sweep — run a Layer-1 completeness audit; only
      reconcile genuinely-permanent blank-instrument_type gaps.
  - [`plans/archive/issues/cefi_layer1_denominator_gaps_2026_07_03.md`](/plans/archive/issues/cefi_layer1_denominator_gaps_2026_07_03.md)
    — 0 open todos (closed/archived/record-only).
  - [`plans/archive/issues/cefi_mtds_writer_raw_symbol_vs_canonical_eu_namespace_mismatch_2026_07_15.md`](/plans/archive/issues/cefi_mtds_writer_raw_symbol_vs_canonical_eu_namespace_mismatch_2026_07_15.md)
    — all todos checked, but `status: open` — 2 operator-gated `--apply` production data-mutation sign-offs still
    pending (relabel ~2.59M/3.13M raw-symbol Tardis manifest rows to canonical ids; purge ~49,720 stale-shape
    `expected_unattempted` rows), deliberately never captured as separate checkboxes. NOT closed/archived/record-only.
  - [`plans/active/issues/cefi_onchain_perp_batch_venue_allowlist_gap_2026_07_12.md`](/plans/active/issues/cefi_onchain_perp_batch_venue_allowlist_gap_2026_07_12.md)
    - **[BLOCKED-CREDENTIALS] P1.** Tardis prod API key only has free-tier/preview entitlement for `lighter` exchange
      historical CSVs — needs operator subscription upgrade or an accepted-limitation ruling.
  - [`plans/active/issues/cefi_residual_followups_after_honest_done_2026_07_17.md`](/plans/active/issues/cefi_residual_followups_after_honest_done_2026_07_17.md)
    (status: open, 14 open — this is Track 1's own source doc, see Track 1 above for context; 11 P0/P1 shown, 3 P2
    capped)
    - **[DOCS] P0.** Lock the two contracts: single-instrument cefi filename stem = FULL instrument_id; shard atom WITH
      pipeline_mode.
    - **[BACKEND] P0.** DEPLOY the reader bridge to all 4 in-scope consumers before the D4 GCS cutover can run.
    - **[SCRIPT] P0.** Parquet CONTENT backfill (corpus-wide) — script written + dry-run-validated, `--apply` is
      operator-gated Phase-E.
    - **[SCRIPT] P0.** Filename rename (Tardis lane) — rename single-instrument cefi objects wire→canonical.
    - **[SCRIPT] P0.** Manifest completion — resolve the ~490k raw captured rows and de-duplicate coexisting id forms.
    - **[INFRA] P0.** Pre-migration drain + snapshot (GATES all Phase-1 `--apply`) — stop ALL live cefi writers both
      clouds before cutover.
    - **[BACKEND] P1.** features raw feature groups cannot consume the REAL raw_tick schema — needs a shaping decision,
      not a loader tweak.
    - **[INFRA] P1.** Fix the features-service image build — stale base-image UAC causes an ImportError.
    - **[SCRIPT] P1.** Close residual #3 — drop the 10,368 non-Tardis eu-twin canonical collisions.
    - **[DOCS] P1.** Resolve the codex↔plan SSOT contradictions the audit surfaced.
    - **[DOCS] P1.** Progress Log at every gate — each `--apply` records measured before/after row counts + coverage
      delta.
    - +3 more P2 — see file for the rest.
  - [`plans/active/issues/cefi_shard_enumeration_blindspots_and_canonical_fetch_dependency_2026_07_18.md`](/plans/archive/issues/cefi_shard_enumeration_blindspots_and_canonical_fetch_dependency_2026_07_18.md)
    — 0 open todos (status: open, narrative finding doc — no checkbox-tracked items, see file for recommended fix).
  - [`plans/active/issues/deribit_combo_perpetual_partition_move_2026_07_21.md`](/plans/active/issues/deribit_combo_perpetual_partition_move_2026_07_21.md)
    - **[DESIGN] P1.** Cross-check this doc's root-cause fix against the concurrent DERIBIT-COMBO venue-registry purge
      before either lands.
    - **[WRITER] P1.** Widen the combo-shape guard and port the split fix into `tardis_cefi_shards.py`.
    - **[DATA] P2.** Implement + dry-run the partition-move script against the 15,119-row scope; canary two named
      objects first.
    - **[DATA] P2.** Operator review of the widened scope + live-fleet sequencing before any `--apply` is scheduled.
  - [`plans/active/issues/deribit_options_chain_af_g4_blocker_2026_07_03.md`](/plans/active/issues/deribit_options_chain_af_g4_blocker_2026_07_03.md)
    - **[VERIFY] P0.** Verify DERIBIT options_chain af after wave-1 reprobe VMs complete.
    - **[MONITOR] P1.** If af > 0 after reprobe: check DERIBIT light VM logs for OOM/preemption evidence.
    - **[OPS] P1.** Close issue when DERIBIT options_chain af=0 in prd manifest.
    - **[DATA] P0.** `futures_chain` retry path must STOP attempting a structurally-absent channel — gate at the WRITER
      (SUPERSEDED note: it's our bundle, not a source absence).
  - [`plans/active/issues/instrument_id_format_canonicalization_2026_07_08.md`](/plans/archive/issues/instrument_id_format_canonicalization_2026_07_08.md)
    - **[SCRIPT] P2.** DEX-pool catalog regeneration (finding 2, all 13 protocols) — re-run instrument discovery and
      rewrite the 6,180 stale catalog rows.
    - **[DECISION] P2.** Confirm exact target quote-currency per on-chain-perp venue (ASTER/PACIFICA/LIGHTER-ZKSYNC).
  - [`plans/active/issues/instruments_docs_audit_outstanding_items_2026_07_08.md`](/plans/active/issues/instruments_docs_audit_outstanding_items_2026_07_08.md)
    — 0 open todos (status: open, narrative finding doc — no checkbox-tracked items, see file for recommended fix).
  - [`plans/active/issues/instruments_remaining_work_audit_2026_07_10.md`](/plans/active/issues/instruments_remaining_work_audit_2026_07_10.md)
    — 0 open todos (status: open, narrative finding doc — no checkbox-tracked items, see file for recommended fix).
  - [`plans/active/issues/mtds_is_full_adapter_smoketest_findings_2026_07_07.md`](/plans/active/issues/mtds_is_full_adapter_smoketest_findings_2026_07_07.md)
    - **[VERIFY] P1.** FLUID lending_indices silently returns 0 rows for ~18 months of its own declared availability
      window — needs an alternate historical read path.
    - **[VERIFY] P1.** Root-cause the 273 mistagged DERIBIT/COMBO rows (open question #1) — not attempted, out of
      dispatched scope.
    - **[CODE] P2.** Update both drilldown mockups — not attempted, out of dispatched scope.
  - [`plans/archive/issues/mtds_ungated_test_families_2026_07_17.md`](/plans/archive/issues/mtds_ungated_test_families_2026_07_17.md)
    (archived 2026-07-31, all 5 todos done)
    - **[BACKEND] P1.** Fix the 8 non-integration `tests/market_interface/unit/` failures (defi handlers/adapters,
      barchart/yahoo).
    - **[BACKEND] P1.** Fix the remaining 14 `tests/market_interface/adapters/**` canonical-output/write failures.
    - **[BACKEND] P1.** Widen `PYTEST_UNIT_DIR` to cover the market_interface
      unit/adapters/clients/schema_validation/cli dirs.
    - **[BACKEND] P2.** Decide the `tests/integration/**` story — 12 modules never run anywhere under
      `RUN_INTEGRATION=false`.
    - **[QG] P2.** Fleet sweep — a PM quality-gate check comparing each repo's `tests/*/unit/` dirs against its
      `PYTEST_UNIT_DIR`.
  - [`plans/archive/issues/solana_perp_dex_cull_drift_pacifica_2026_07_16.md`](/plans/archive/issues/solana_perp_dex_cull_drift_pacifica_2026_07_16.md)
    — ✅ CLOSED 2026-08-03, all todos done, archived.
  - [`plans/active/issues/tardis_impossible_combinations_recorded_as_attempted_failed_2026_07_17.md`](/plans/active/issues/tardis_impossible_combinations_recorded_as_attempted_failed_2026_07_17.md)
    - **[CODE] P0.** Gate the Tardis request universe on the vendor catalog (symbol x data_type x date-range); cache +
      refresh daily.
    - **[CODE] P0.** Stop recording impossible combos as `attempted_failed` — distinguish by Tardis JSON code.
    - **[CODE] P1.** Log the Tardis error code — `code=300` and `code=140` are currently indistinguishable in logs.
    - **[DATA] P1.** Size the damage — count existing `attempted_failed` rows attributable to 400s and purge/reclassify.
    - **[CONTRACT] P2.** Register Tardis error codes in UAC (`classify_venue_error`).
  - [`plans/active/issues/uac_data_type_validity_combinator_fragmentation_2026_07_07.md`](/plans/active/issues/uac_data_type_validity_combinator_fragmentation_2026_07_07.md)
    - **[CODE] P2.** `_L5_VENUES` part resolved-by-deletion; STILL OPEN — audit
      `_SOURCE_COVERAGE_START`/`_PROTOCOL_TO_DATA_TYPE` (onchain, not cefi) for the same read-from-UAC fix.
    - **[CODE] P2.** Add missing `book_snapshot`/`market_metadata`/`fills` declarations to
      `VENUE_DATA_TYPE_CAPABILITIES["POLYMARKET"/"KALSHI"]`.
    - **[SCRIPT] P3.** Delete confirmed-dead code — not touched this pass (concurrent edits).
    - **[DESIGN] P2.** 31 DeFi (venue, data_type) pairs declare a genesis start-date with zero real captured rows —
      needs an operator/data-owner decision per pair.

## Pass-through from the 2026-07-18 consolidated canonicalisation audit (slot-4) — decisions + measured worklist

> Authored by the DeFi close-out audit (`defi_consolidated_closeout_2026_07_18.md`) and handed here per the operator's
> ownership split (cefi findings land in THIS plan). Operator rulings 2026-07-18. **Moved verbatim from
> `cefi_consolidated_closeout_2026_07_18.md` (2026-07-25 line-cap trim, 4-child split pass) — nothing summarized or
> dropped.** ⚠️ **Possible overlap flagged, not resolved**: this section may duplicate content in the parent's own "CEFI
> CANONICAL SPEC" section (operator-authoritative target spec) — both were authored the same day (2026-07-18) from
> related but distinct audits and were never diffed against each other. Per `task_template.md` §3 finding M ("don't
> guess-delete, preserve both copies"), this is flagged here for a LATER dedicated pass, not resolved now.

**Operator decisions confirmed (cefi):**

- **Venue token = HYPHENATED** (`BINANCE-FUTURES:PERPETUAL:BTC-USDT@LIN`), NOT underscore — the builder only `.upper()`s
  the venue and it must equal the GCS `venue=` axis (always hyphen); underscore would FAIL the verify-gate `[A-Z0-9-]+`.
  So the live manifest's ~9.5M "hyphen" rows are ALREADY canonical → **no `-`→`_` rename** (the underscore illustrative
  form in earlier docs is wrong).
- **ASTER quote = PER-SYMBOL REAL quote** (operator ruling 2026-07-18): use each symbol's actual on-chain `quoteAsset`
  (predominantly USDT — 504/509 — but the tail carries its real USD1/USDC/`U`; `aster.py` already embeds the per-symbol
  quote). ASTER data is REAL (its own Binance-compatible endpoints `fapi.asterdex.com`, not a Binance proxy).
  Representative id = `ASTER:PERPETUAL:BTC-USDT@LIN`; **NOT hardcoded USDT** — the earlier `ASTER=USDT` note was the
  majority, not the rule. Fix the stale docs (`shard-granularity-cefi.md:106` = USDC, `DEFI_DOWNLOAD_STRATEGY.md:164`).
- **DERIBIT always-quote** — confirmed the gating P0 (already Track-1 / the DERIBIT quote-fix item, see
  `/plans/archive/2026_07/cefi_migration_cutover_and_track8_completion_2026_07_25.md`).
- **Venue purge (operator ruling, refined 2026-07-18)** — remove the CULLED/defunct venues ENTIRELY from UAC + manifest
  - GCS data + MVP catalogue + docs, **snapshot-first** (irreversible): BITSTAMP-SPOT / HUOBI-SPOT/-FUTURES /
    GEMINI-SPOT / PHEMEX-SPOT (defunct), and the Solana-perp cull
    (DRIFT/PACIFICA/MANGO/ZETA/FLASH/SOLAYER/PICASSO/CAMBRIAN). **KEEP registered (NOT purged)**: **BINANCE-DELIVERY**
    (live COIN-M product — descope from MVP backfill, keep the UAC registration/scaffold; the audit found it still fully
    registered across UAC, which is fine — just mark non-MVP), KALSHI-PERP + POLYMARKET-PERP (roadmap — will be added),
    LIGHTER-ZKSYNC (blocked-credentials MVP scaffold — external-data-always-available rule), EXTENDED-STARKNET (live
    MVP). Clean the STALE `/codex/02-data/mvp-scope-canonical.md` PACIFICA-as-MVP bolding.
- **DERIBIT-COMBO leg-aware combos (cross-AG)** — adopt the operator's 2026-07-09 leg-aware signed-weight spec (per-leg
  human-readable `instrument_key` + weight + direction-as-sign, 1–4-leg hard cap) for DERIBIT-COMBO by extending the
  shared `build_leg()` path to `cefi/deribit_combo_adapter.py` + `cefi/tardis/combos.py` — the open cross-AG P2 in
  `canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md`.

**Live manifest worklist (`market-data-tick-cefi-prd`, 11.19M rows; ~44.3% of ids non-canonical)** — the migration must
map these (measured via the distinct-values audit; counts approximate):

> **⛔ CASE DIRECTION CORRECTED 2026-07-20, operator ruling D1** — recorded in
> [`data_pipeline_reconciliation_skill_2026_07_20.md`](/plans/active/data_pipeline_reconciliation_skill_2026_07_20.md) §
> "OPERATOR DECISIONS — ALL THREE RULED 2026-07-20". **This table previously ordered the `instrument_type` case-fold
> DOWN to lowercase** (row 1: `PERPETUAL`/`SPOT_PAIR`/`FUTURE`/`OPTION` → "lowercase", 7.58M rows) — **directly
> contradicting the parent doc's own "✅ CASING FREEZE LIFTED 2026-07-20 (operator ruling D1 — UPPERCASE column
> ratified)" note** (`instruments-service@555ddf1c`), which already shipped these 7.58M rows UPPERCASE and ratified that
> as the target. The row count is unchanged and preserved below; **the direction is corrected — these rows are already
> canonical, no further fold needed.** This applies to the manifest `instrument_type` **COLUMN only**: the id
> **segment** stays UPPER, unaffected either way.

| dimension       | non-canonical                                     | canonical target                                   |     ~rows | action                        |
| --------------- | ------------------------------------------------- | -------------------------------------------------- | --------: | ----------------------------- |
| instrument_type | `PERPETUAL`/`SPOT_PAIR`/`FUTURE`/`OPTION`         | UPPERCASE ~~lowercase~~ (D1, already shipped)      |     7.58M | already-canonical — no action |
| instrument_type | `''`/`NULL`/`spot`/`index`                        | resolve from id / remap                            |     3.23M | resolve                       |
| instrument_id   | perp missing `@LIN`/`@INV`                        | append margin marker                               | 2,402,330 | reconstruct                   |
| instrument_id   | raw no-colon (`SPELLUSDT`)                        | `VENUE:TYPE:BASE-QUOTE@MARGIN`                     | 1,362,316 | reconstruct                   |
| instrument_id   | DERIBIT option (0% canonical)                     | `DERIBIT:OPTION:BASE-USD@INV-YYYYMMDD-STRIKE-C\|P` |  ~428,600 | add quote + YYYYMMDD          |
| instrument_id   | `VENUE:PERP:RAW` (HL/LIGHTER/ASTER)               | `VENUE:PERPETUAL:BASE-QUOTE@LIN\|INV`              |   374,272 | reconstruct                   |
| instrument_id   | DERIBIT future `BASE-DDMMMYY`                     | `DERIBIT:FUTURE:BASE-USD@INV-YYYYMMDD`             |  ~250,600 | add quote                     |
| instrument_id   | KRAKEN raw `FI_/FF_`                              | `KRAKEN-FUTURES:FUTURE:BASE-USD@…-YYYYMMDD`        |    68,469 | reconstruct                   |
| source          | `''`/`NULL`                                       | vendor token (`tardis`/native)                     | 3,441,207 | backfill vendor               |
| pipeline_mode   | `NULL`                                            | `{mode}_{source}`                                  |   345,492 | backfill                      |
| venue           | `OKX` bare (64) · `DERIBIT-COMBO`→`DERIBIT` (226) | resolve family / encode combo in id                |      ~290 | resolve/collapse              |

**Enumeration-restore (cross-AG, owned by the DeFi plan Track 6)**: a raw un-canonicalised distinct-values audit panel
per asset_group (the view removed on `deployment-api@512180be`) is being restored so this worklist stays live-visible.

## Retagged into cefi scope 2026-07-25

Orthogonality mistags found scoping the new cross-cutting AG layer — see
`cursor-configs/skills/ag-closeout-audit/SKILL.md`'s Orthogonality HARD CHECK:

- [`crypto_alpha_research_2026_07_24.md`](/plans/active/crypto_alpha_research_2026_07_24.md) — book construction /
  signal research / paper-trading POC, overwhelmingly Binance-perp/CeFi content.
- [`vol_dvol_backtestable_engines_2026_07_13.md`](/plans/archive/2026_08/vol_dvol_backtestable_engines_2026_07_13.md) (+
  its gated
  [`_finalize_2026_07_30.md`](/plans/archive/2026_08/vol_dvol_backtestable_engines_2026_07_13_finalize_2026_07_30.md)) —
  DVOL-backtestable VOL_CARRY + VOL_ARB_RV_IV engines, exclusively Deribit DVOL-index CeFi vol trading. **ARCHIVED
  2026-08-03 to `plans/archive/2026_08/`** — both engines' backtests came back non-passing (BLOCKED-INSUFFICIENT-EDGE),
  stay `not_available`.

## Self-dispatched docs with no digest linkage (added 2026-08-02, ag-closeout-audit linkage-gap fix)

`check_ag_closeout_linkage.py` flagged these as having zero real graph/mention path to the cefi closeout family — each
is genuinely `assigned_vm: planning` + `status: open`/`active` (its own dispatch vehicle, so nothing is actually stuck),
but none was ever named in this digest, making them invisible to a human reader tracing cefi's open work from here.
Listed for discoverability only — being listed here is NOT dispatch, per this doc's own standing convention.

- [`cefi_content_migration_corpus_still_incomplete_relaunch_round3_needed_2026_07_31.md`](/plans/active/issues/cefi_content_migration_corpus_still_incomplete_relaunch_round3_needed_2026_07_31.md)
  — split-out child of `cefi_content_migration_fleet_half_incomplete_2026_07_26.md`; one open `[OPERATOR] P1` todo
  (relaunch-strategy ruling for 10 repeat-failing shards).
- [`tarball_stale_window_cefi_live_capture_correctness_risk_2026_08_01.md`](/plans/active/issues/tarball_stale_window_cefi_live_capture_correctness_risk_2026_08_01.md)
  — 8 of 9 todos done as of 2026-08-02 (ASTER book_snapshot_5/liquidations fixes shipped); one open `[DATA] P3` to file
  a follow-up issue for 2 incidentally-found unrelated chronic findings (OKX-FUTURES trades gaps, POLYMARKET-PERP
  perp_funding).

## Digest additions for cefi-tagged linkage orphans (added 2026-08-07, ag-closeout-audit cefi run)

`check_ag_closeout_linkage.py` flagged these 6 cefi-tagged docs as having no graph/mention path to the cefi closeout
family (all classified by the 2026-08-06 and 2026-08-07 ag-closeout-audit cefi runs; none were AO-eligible as-of-their
classification except items extracted into batch9 — see the batch docs). Listed for discoverability only — being listed
here is NOT dispatch, per this doc's own standing convention.

- [`cefi_book_snapshot5_schema_contract_ts_event_levels_mismatch_2026_07_28.md`](/plans/active/issues/cefi_book_snapshot5_schema_contract_ts_event_levels_mismatch_2026_07_28.md)
  — 2 open items, both explicit design/redesign decisions for features-service's loader (classified 2026-08-06,
  orphaned_never_touched, not AO-eligible).
- [`cefi_derivative_ticker_tardis_resolver_aiodns_hardfail_2026_07_28.md`](/plans/archive/2026_08/issues/cefi_derivative_ticker_tardis_resolver_aiodns_hardfail_2026_07_28.md)
  — 9 of 10 todos done+verified; sole open `[DATA] P3` Follow-ups item (fetch_l2_book / book_snapshot_5 case-sensitivity
  audit) extracted into [`cefi_satellite_ao_dispatch_batch9_2026_08_07.md`](/plans/archive/2026_08/cefi_satellite_ao_dispatch_batch9_2026_08_07.md) todo 1 (classified 2026-08-07).
- [`cefi_liquidations_attempted_failed_lifetime_count_stale_2026_07_30.md`](/plans/active/issues/cefi_liquidations_attempted_failed_lifetime_count_stale_2026_07_30.md)
  — 2 open items, both blocked on an `[OPERATOR]` decision among 3 named options (classified 2026-08-06,
  orphaned_never_touched, not AO-eligible).
- [`features_universe_filter_settlement_suffix_and_vm_tarball_staleness_2026_07_27.md`](/plans/active/issues/features_universe_filter_settlement_suffix_and_vm_tarball_staleness_2026_07_27.md)
  — `[SCRIPT] P2` done-when half-2 (real-VM-launch observation of `LC_TARBALL_FRESHNESS` auto-republish) extracted into
  [`cefi_satellite_ao_dispatch_batch9_2026_08_07.md`](/plans/archive/2026_08/cefi_satellite_ao_dispatch_batch9_2026_08_07.md) todo 3 (classified 2026-08-07).
- [`mtds_cefi_docker_image_stale_5mo_2026_07_30.md`](/plans/archive/issues/mtds_cefi_docker_image_stale_5mo_2026_07_30.md)
  — both todos fully claimed by `cefi_satellite_ao_dispatch_batch6_2026_08_02.md`'s open `[OPS] P2` todo
  (archivable_after_planned_work, classified 2026-08-07).
- [`mtds_live_mode_never_touches_authenticated_tardis_datasets_endpoint_2026_08_02.md`](/plans/active/issues/mtds_live_mode_never_touches_authenticated_tardis_datasets_endpoint_2026_08_02.md)
  — sole remaining item is a standing observability tripwire, not actionable now (classified 2026-08-06,
  orphaned_never_touched, not AO-eligible).

## Digest additions for cefi-tagged linkage orphans (added 2026-08-10, ag-closeout-audit cefi run)

`check_ag_closeout_linkage.py` flagged these cefi-tagged docs as having no graph/mention path to the cefi closeout
family (all classified by the 2026-08-10 `/ag-closeout-audit cefi` run, slot 27, dispatch agt-dab448).

- [`ag_closeout_audit_cefi_parked_2026_08_10_r2.md`](/plans/archive/2026_08/issues/ag_closeout_audit_cefi_parked_2026_08_10_r2.md)
  — parked findings from the 2026-08-10 audit run (Round 2, slot 27); 0 parked findings, 1 orphaned doc extracted into
  batch18. Resolved + archived. Round 1 at
  [`ag_closeout_audit_cefi_parked_2026_08_10.md`](/plans/archive/2026_08/issues/ag_closeout_audit_cefi_parked_2026_08_10.md).
- [`cefi_satellite_ao_dispatch_batch18_2026_08_10.md`](/plans/archive/2026_08/cefi_satellite_ao_dispatch_batch18_2026_08_10.md)
  — batch18 draft, completed + archived — root cause diagnosed (NOT inverted comparison; transient GCS/parse error), fix
  shipped at `unified-trading-library@26294ddf71`.
- [`cefi_satellite_ao_dispatch_batch18_finalize_2026_08_10.md`](/plans/archive/2026_08/cefi_satellite_ao_dispatch_batch18_finalize_2026_08_10.md)
  — paired finalize plan, completed + archived — closeout linkage verified (0 cefi orphans).

## Todos

- [ ] [DOC] P2. **Keep this discoverability index synced as sibling docs close out** — this doc's own "Aggregated source
      docs" section catalogs dozens of genuinely open cefi todos as bold non-checkbox markers by design (e.g. Script 2
      P0 embedded-slash wire-stem fix, catalogue-dedup P0, DERIBIT combo P1 partition-move); none of that open work is
      tracked as a checkbox in this index itself.

## Progress Log

- **na-eligibility-audit 2026-07-30** (tranche=cefi, autonomous): KEEP-NA, valid - the sole todo is a standing
  discoverability-index sync with no terminal done-state; by design a human-maintained digest, not a dispatchable unit.
- **na-eligibility-audit 2026-07-31** (tranche=cefi, autonomous): KEEP-NA, valid — re-verified after the file's last
  commit (5fb83f4ea) touched only a corpus-referrer link (archived-doc path fix from an unrelated ag-closeout-audit
  run), not this doc's own todo/scope. Verdict unchanged from 2026-07-30.
- **context-scout 2026-08-03**: re-confirmed context_scope (2 entries) unchanged — this doc is itself a pointer/index of
  dozens of other docs (its own body IS the reading list), so the parent plan + the line-cap-remediation source doc
  remain the right minimal set; no source-code paths added (genuinely code-free discoverability-index doc).
- **context-scout 2026-08-01**: populated/refreshed context_scope (2 entries).
- **na-eligibility-audit 2026-08-04** (tranche=cefi, autonomous): KEEP-NA, valid — reaffirms the 2026-07-31 verdict; the
  sole open checkbox is the standing "keep this index synced" maintenance task, by design never terminal.
- **context-scout 2026-08-05**: re-scouted; context_scope unchanged (2 entries), still accurate.
- **na-eligibility-audit 2026-08-06** (tranche=cefi, autonomous): KEEP-NA, valid — reaffirms the 2026-08-04 verdict;
  by-design non-checkbox discoverability index (bold-marker syntax throughout, deliberately un-ingestable), the sole
  real checkbox is a standing "keep synced" maintenance task, never terminal.
- **na-eligibility-audit 2026-08-07** (tranche=cefi, autonomous): KEEP-NA, valid — this doc is a
  structurally-un-ingestable discoverability index by design (frontmatter states so); its one real checkbox is a
  standing, non-terminal sync-maintenance duty, not bounded dispatchable work. Reaffirms 4 prior passes (2026-07-30,
  07-31, 08-04, 08-06).
- **context-scout 2026-08-07**: re-confirmed context_scope (2 entries) unchanged — the 2026-08-07 "Digest additions"
  section (6 new cefi-tagged linkage-orphan docs) doesn't change this: those docs are the index's OWN new content
  (already linked in the body), not reading-list prerequisites for touching this doc itself. Parent closeout plan + the
  line-cap-remediation source doc remain the right minimal set; still genuinely code-free (discoverability-index doc).
- **na-eligibility-audit 2026-08-09** (tranche=cefi, autonomous): KEEP-NA, valid — discoverability-index doc by design
  (non-checkbox markers for cited content, deliberately un-ingestable by AO's parser per its own frontmatter). Sole real
  checkbox is a standing sync-maintenance duty with no terminal done-state. Reaffirmed across 6+ prior passes.
