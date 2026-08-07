---
doc_type: issue
title:
  "plan_reconciler run findings — 2026-08-07 cefi tranche shard (agt-8ce897): flips verified, contradictions/doc-drift
  routed, hygiene fixes applied"
summary: >-
  Daily deep plan-reconciliation, cefi tranche only (94 cefi-tagged docs in plans/active+issues + cefi_master epic +
  normative refs + codex). Fan-out DETECT via read-only hunter sub-agents, adversarial VERIFY (refuter + confirmer),
  then apply only confirmed fixes on review branch plan_reconciler/agt-8ce897. 4 hygiene-sweep hard failures
  (reference-path ratchet 83/81, AG-closeout linkage 77/69, terminal-status-archived 4/0, archive-candidates) are the
  Phase-0 mechanical feeds; 8 inventory orphans + INDEX drift 21 noted. Grace set (38 cefi docs, <12h) read-only. Final
  counts and the Phase-5.9 ledger live in the sections below.
status: open
nature: issue
asset_group: [cefi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan_reconciler, reconciliation, plan-hygiene, run-findings, cefi, sharded]
related: [plan_reconcile_autonomous_sweep_2026_07_30, zero_checkbox_sweep_all_tranches_2026_07_31]
created: 2026-08-07
author: plan_reconciler
parent_epic: plan_hygiene_master
priority: P2
assigned_vm: NA
execution_scope: local-only
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
assigned_role: NA
drift_direction: none
source: agt-8ce897
depends_on: []
resolved_by:
locked_by: plan_reconciler
---

# plan_reconciler findings — 2026-08-07 (cefi tranche, dispatch agt-8ce897)

Run journal + presentation doc. Sections appended as the run progresses.

## Run metadata

- Dispatch: `agt-8ce897`, slot 12, branch `plan_reconciler/agt-8ce897`
- Tranche: `cefi` (asset_group: cefi → 94 docs in plans/active + issues/; epic `plans/epics/cefi_master.md`; normative
  refs + codex stay in scope per SKILL.md)
- Grace set (read-only, newest change <12h): 38 cefi docs — listed in Coverage section
- Hygiene sweep: 4 hard failures (reference-path 83/81; existence 92/86; AG-closeout linkage 77/69;
  terminal-status-archived 4/0; archive-candidates 0), 8 inventory orphans, INDEX drift 21

## Phase-0 mechanical feed (itemized, adjudicated subset)

Adjudicated inline from the sweep report (2026-08-07 00:14 run) — cefi-tagged subset only:

- **Terminal-status-archived (4, baseline 0): ALL NON-cefi** — sit_stamp_skipped_on_detached_head_pinned_sha_2026_08_06
  (resolved), sports_mtds_backfill_vm_unscoped_fetch_oom_2026_08_06 (resolved),
  omniroute_multi_provider_routing_evaluation_2026_08_03 (superseded),
  tradfi_satellite_ao_dispatch_batch2_finalize_2026_07_25 (complete). Owned by sibling tranches; not touched here.
- **AG-closeout linkage (77 vs baseline 69): cefi orphans = 7** — 4 in grace set (cefi_book_snapshot5…,
  cefi_derivative_ticker_tardis_resolver…, cefi_liquidations_attempted_failed…, plan_reconciler_findings_2026_08_07
  [this doc, expected]) + **3 writable**:
  features_universe_filter_settlement_suffix_and_vm_tarball_staleness_2026_07_27,
  mtds_cefi_docker_image_stale_5mo_2026_07_30,
  mtds_live_mode_never_touches_authenticated_tardis_datasets_endpoint_2026_08_02. Corpus-wide regression already tracked
  in ag_closeout_linkage_baseline_regression_87_vs_69_2026_08_06 (grace).
- **Reference-path ratchet (format 83/81, existence 92/86): ZERO violations in cefi-tagged plans/active docs** — the 39
  plans/active hits are scratch_scenarios_day1 (defi) + sports/infra/ao/cross-cutting docs. Standing issue:
  reference_path_convention_2026_07_23.
- **Inventory orphans (8): cefi-tagged count TBD** — H5 mechanical adjudicator verifying.
- **Archive candidates: 0** (0 locked / 0 archivable) — nothing to do this run.

## Flips verified

<!-- appended as STEP 4/5 confirms -->

## Zero-checkbox sweep (cefi, H6 result — pending STEP-4 verify)

Zero-checkbox docs in writable cefi set: **2** (both prose-work; register already lists both as NEW/unclassified in its
2026-08-06 measurement):

1. `plans/active/issues/mtds_pipeline_check_enumerate_shards_masks_cefi_sports_mvp_2026_08_06.md` (assigned_vm:
   planning, AO-eligible) — proposed conversion: 2× `[SCRIPT] P1` (CEFI/SPORTS override in `_venue_data_type_is_mvp()`
   mirroring `_TRADFI_MVP_SHARDS`; per-asset_group fallback in the last-resort enumerate) + 1× `[REVIEW] P2` re-run of
   the full-matrix invocation as done-when.
2. `plans/active/issues/mtds_pipeline_check_process_killed_during_skip_leg_poll_2026_08_06.md` (assigned_vm: NA,
   local-only) — proposed conversion: `[DATA] P1` reproduce with strace/py-spy to capture the signal, `[REVIEW] P1`
   check systemd/loginctl idle-session-reaper policy (needs VM-level access), `[OPERATOR] P2` host-wide
   install-pkill-guard-shell-env.sh if cross-slot pkill confirmed.

Grace-set zero-checkbox docs: 0. finished-record / informational / ambiguous: 0 each. Verification + conversion
application in STEP 4/5; the standing register (`zero_checkbox_sweep_all_tranches_2026_07_31.md`) gets its two
NEW/unclassified rows classified at apply time.

## Contradictions

<!-- routed + filed -->

## Doc-drift

<!-- flagged, routed to operator -->

## Hygiene fixes

<!-- applied -->

## Filed

<!-- durable todos/issue refs -->

## Archive candidates (operator review)

<!-- none / listed -->

## Refuted (dropped by verify)

<!-- appended -->

## Coverage (hunters / batches / docs)

- Total cefi-tagged docs: 94 (+ epic cefi_master + normative refs + codex)
- Grace-set docs (read-only): 38 — cefi_satellite_ao_dispatch_batch4_2026_07_31,
  issues/cefi_consolidated_vm_aster_data_landing_recheck_2026_07_30,
  issues/cefi_live_event_cold_compactor_oom_and_legacy_path_check_2026_08_07,
  cefi_satellite_ao_dispatch_batch6_2026_08_02,
  issues/deribit_dated_option_trades_perpetual_misclassification_2026_07_27,
  issues/mtds_qg_red_combined_coverage_shortfall_2026_08_05,
  issues/cefi_content_migration_corpus_still_incomplete_relaunch_round3_needed_2026_07_31,
  data_pipeline_check_mdps_features_2026_07_20, issues/cefi_tardis_derivative_ticker_historical_gap_2026_08_04,
  issues/mtds_backfill_launcher_guard_overapplies_to_nontardis_venues_2026_07_28,
  cefi_consolidated_closeout_aggregated_sources_2026_07_24, cefi_satellite_ao_dispatch_batch8_2026_08_06,
  issues/cefi_book_snapshot5_schema_contract_ts_event_levels_mismatch_2026_07_28,
  issues/cefi_derivative_ticker_tardis_resolver_aiodns_hardfail_2026_07_28,
  issues/cefi_track7_candle_bundle_regeneration_vm_2026_08_04, issues/coverage_floor_new_backfill_gaps_found_2026_07_27,
  issues/coverage_floor_registries_no_cross_propagation_2026_07_17,
  issues/deribit_options_chain_af_g4_blocker_2026_07_03, issues/strategy_ml_orphan_coverage_design_gaps_2026_08_03,
  issues/tarball_stale_window_cefi_live_capture_correctness_risk_2026_08_01,
  issues/uac_data_type_validity_combinator_fragmentation_2026_07_07,
  issues/cefi_liquidations_attempted_failed_lifetime_count_stale_2026_07_30,
  cefi_track7_candle_namespace_residual_finalize_2026_07_25,
  issues/cefi_content_apply_memory_freeze_recurs_post_fix_and_registry_false_reap_2026_07_31,
  cefi_track7_candle_namespace_residual_2026_07_25, issues/cefi_content_migration_fleet_half_incomplete_2026_07_26,
  issues/deribit_combo_perpetual_partition_move_2026_07_21,
  issues/instrument_availability_hive_migration_unrecognized_shapes_and_content_mismatch_2026_08_03,
  hyperliquid_aster_defi_to_cefi_asset_group_migration_2026_08_02_finalize,
  issues/bybit_futures_chain_write_shape_2026_07_13, issues/cefi_track2_backfill_vm_preempted_no_recovery_2026_07_30,
  hyperliquid_aster_defi_to_cefi_asset_group_migration_2026_08_02, issues/ag_closeout_audit_cefi_parked_2026_08_06,
  issues/okx_futures_instid_marker_convention_mismatch_2026_07_30, cefi_satellite_ao_dispatch_batch7_2026_08_03,
  issues/upbit_cefi_data_gap_may_2026_2026_08_04, issues/defi_cefi_venue_chain_axis_contamination_2026_07_28,
  ag_closeout_audit_rollout_2026_07_25
- Writable cefi docs: 56 (94 − 38)

## Plans not reached

<!-- appended if any -->

## Phase-5.9 ledger

- routed_to_operator == parked_in_issue_doc: TBD
- agent_skips == enumerated: TBD (no apply-agents expected — single-writer orchestrator)
