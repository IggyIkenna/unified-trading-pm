---
doc_type: issue
title: Plan reconciler findings — sports tranche (agt-132fc8)
summary:
  Run-findings doc for the sports-tranche sharded daily reconciliation (dispatch agt-132fc8, 2026-08-06). Hunter fan-out
  DETECT → adversarial VERIFY → apply confirmed → route hard items. Live journal for the run.
status: open
resolved_by:
nature: issue
asset_group: [sports]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan_reconciler, findings, sports, reconciliation]
related: [/plans/epics/sports_master.md]
parent_epic: sports_master
priority: P2
assigned_vm: NA
created: 2026-08-06
author: plan_reconciler
source: agt-132fc8
locked_by: plan_reconciler
---

# Plan reconciler run-findings — sports tranche (agt-132fc8)

> Live journal for the 2026-08-06 sports-tranche reconciliation shard. Sections are appended as the run progresses.
> Normative refs (PLAN_FORMAT.md / task_template.md / INDEX.md / ACTIVE_INDEX.md) + codex stay in scope per the
> sharded-run contract; audit corpus = `asset_group: sports` docs in `plans/active/` + `plans/active/issues/` +
> `plans/epics/sports_master.md`.

## Coverage (hunters / batches / docs)

**Corpus** (2026-08-06, from `rg -l '^asset_group:.*sports'` over `plans/active/` + `plans/active/issues/` +
`plans/epics/`): 82 docs = 1 epic (`sports_master.md`, 168.5 KB) + 28 active plans + 53 issues. **Non-grace working set
= 53 docs (1.96 MB)**, grace set (newest git change <12h, context-only) = 29 docs + this findings doc.

**Hunter fan-out plan (10 hunters, all read-only, sonnet, SUB_AGENT_MANDATORY_RULES injected):**

| Hunter            | Batch                         | Docs                                                                                                                                                                                                                                                                                                                                                                                                           | Size       |
| ----------------- | ----------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| A (epic-cluster)  | closeout core                 | sports_consolidated_native_ao_extract (main GRACE + finalize), sports_closeout_track_s2_foldin (+finalize), sports_closeout_track_x_hygiene (+finalize), sports_closeout_exchange_fixed_odds_fork (+finalize), sports_track_h_denominator_gated, sports_track_h_denominator_prereqs                                                                                                                            | 10         |
| B (epic-cluster)  | data completion               | data_completion_sports, predictions_ml_walk_forward_and_arb, sports_arb_decay_window_and_alpha_gate_design, sports_odds_feature_naming_canonicalization, sports_canonical_universe_and_apifootball_reference_expansion, sports_catalog_league_grain_only_scope, sports_group_c_execution_backtest_harness                                                                                                      | 7          |
| C (epic-cluster)  | satellite AO + features sweep | sports_satellite_ao_dispatch_batch5, batch9_finalize, data_pipeline_check_mdps_features_finalize, sports_features_layer_findings_sweep (+part2, part3)                                                                                                                                                                                                                                                         | 6          |
| D (epic-cluster)  | odds API cluster              | sports_odds_api_scattered_multiyear_gaps, sports_batch_odds_api_capture_outage_recurrence_check, sports_odds_venue_enumeration_undercount_predrain, sports_odds_stale_fixture_reinjection, mtds_sports_odds_api_force_fetch_no_parquet, sports_odds_markets_outcomes_settlements_arbitrage_expected_since_2024_zero_captured, sports_odds_feature_naming_four_way_mismatch, sports_halftime_odds_sfi_vs_inplay | 8          |
| E (epic-cluster)  | estate/instruments            | estate_orphan_assessment, instruments_remaining_work_audit, mtds_is_full_adapter_smoketest_findings, instruments_service_sports_footystats_uac_overlap_qg_red                                                                                                                                                                                                                                                  | 4          |
| F (epic-cluster)  | recon/stats/fixtures          | sports_cf8_available_at_backfill_regression, sports_stats_delayed_live_capture_still_dead_post_fix, sports_fixtures_schedule_wrong_schema_day, candle_feature_canonical_path_divergence, sports_peripheral_bucket_league_vocabulary_contamination                                                                                                                                                              | 5          |
| G1 (epic-cluster) | ops/mdps                      | autonomous_session_operator_decisions, mdps_sports_honest_absence_writes_fail_fetchevidence_gate, mtds_pipeline_check_process_killed_during_skip_leg_poll, mtds_pipeline_check_enumerate_shards_masks_cefi_sports_mvp, ml_training_and_prediction_pipeline_launchers_stale_post_consolidation, mdps_features_deadcode_consolidation, sports_catalog_dp_catalog_001_junk_name_crash                             | 7          |
| G2 (epic-cluster) | fetch/manifest/coverage       | footystats_matches_predictions_fetch_gaps, sports_dependency_check_manifest_vs_gcs_path, backfill_smoke_write_path_canonical_audit, adapter_findings_gcs_manifest_deployment_api_reconciliation_gap, sports_index_recency_masked_captured_atoms, phantom_audit_estate_coverage_gap                                                                                                                             | 6          |
| EPIC              | epic hub                      | sports_master.md in full + closeout cross-check                                                                                                                                                                                                                                                                                                                                                                | 1 (168 KB) |
| CODEX             | codex-alignment               | Codex SSOTs sections of 12 sports plans + 2 known-broken refs (sports-canonical-league-cup-registry, plan-completion-and-archival-discipline)                                                                                                                                                                                                                                                                  | 12 plans   |

**STEP-1 hygiene inputs** (sweep 2026-08-06 21:51 UTC): 4 hard failures — reference-path format 83 (baseline 81),
existence 88 (86), AG-closeout linkage 75 orphans (69), terminal-status-archived 3 (0); archive-candidates ratchet RED.
All corpus-wide ratchets — flagged, not sports-fixable in this shard. Sports-relevant flags: 2 BROKEN codex refs (see
CODEX hunter), 2 estimate DRIFTs (`sports_satellite_ao_dispatch_batch9/10_finalize`, 50% infra), 1 priority-tier WARN
(sports_odds_stale_fixture_reinjection P1), INDEX.md drift 19 (corpus-wide, not sports-owned).

**Cross-slot observation (noted, not touched)**: the ROOT PM clone (`unified-trading-pm`, not this slot) is checked out
on the ci-tranche reconciler's review branch `plan_reconciler/agt-a304c9` (PR #2400 open, committed work pushed) with
leftover staged WIP (`plan_reconciler_ci_late_findings_2026_08_06.md` staged-mod + untracked
`ag_closeout_audit_ci_parked_2026_08_06.md`). Not this run's work — left untouched, reported for awareness only.

## Flips verified

## Contradictions

## Doc-drift

## Hygiene fixes

## Filed

## Archive candidates (operator review)

## Refuted (dropped by verify)

## Plans not reached
