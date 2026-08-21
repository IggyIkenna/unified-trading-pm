---
doc_type: issue
title: ag-closeout-audit defi 2026-08-21 — orphan projection + parked findings
summary: >-
  2026-08-21 /ag-closeout-audit defi tranche Phase 1 audit (4 batches, 105 candidate docs). Compact orphan table —
  full escalation-worthy findings live in the cross-tranche big-findings doc.
status: open
nature: issue
asset_group: [defi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ag-closeout-audit, defi, orphan-projection]
related: [/plans/active/issues/ag_closeout_audit_cross_tranche_big_findings_2026_08_21.md, /plans/active/defi_consolidated_closeout_2026_07_18.md]
created: 2026-08-21
author: claude-session-2026-08-21
parent_epic: defi_master
assigned_vm: NA
execution_scope: human
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0
estimate_calibrated_ai_days: 0
assigned_role: NA
drift_direction: NA
resolved_by:
locked_by:
source: ["2026-08-21 — /ag-closeout-audit defi, 4 Phase-1 batches, 105 candidates"]
depends_on: []
context_scope: [/plans/active/issues/ag_closeout_audit_cross_tranche_big_findings_2026_08_21.md]
---

# ag-closeout-audit defi 2026-08-21

105 candidates, 4 batches. Counts: archivable_now 9 · archivable_after_planned_work ~11 · orphaned_partial_coverage
~5 · orphaned_never_touched ~46 · exclude_cross_cutting ~34 (very high mistag rate — defi's own master closeout
`defi_consolidated_closeout_2026_07_18.md` is `assigned_vm: NA`, so most gated work reads structurally orphaned
under the strict coverage bar even when a real gate chain exists — methodology caveat, not a real gap).

**Escalation-worthy defi findings already captured in the cross-tranche big-findings doc** (items 1-6): W15
security audit, OMS persistence, execution_state_does_not_survive_restart, producer_silence_flatten_protocol,
market_data_timestamp_semantics, health_factor_monitor liquidation-protection gap.

## Orphaned (never_touched / partial_coverage) — compact table

| Doc | Taxonomy |
|---|---|
| `data_completion_defi_2026_07_15.md` (17 items) | operator/VM-gated, KEEP-NA reaffirmed 5+ passes |
| `defi_cf2_cf3_legacy_canonical_backfill_2026_08_08.md` | scoping-only, declined coverage twice |
| `defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md` | design/build, uncovered |
| `defi_live_poller_phased_build_2026_08_15.md` (draft) | 37 venue live-connector builds undispatched, prior audit already recommends a dedicated batch2 |
| `defi_migration_audit_log_2026_07_24.md` | gated (GATE C v9, Era-B retirement, destructive-delete sign-off) |
| `defi_track5_coverage_mvp_backfill_2026_07_24.md` | gated on NA closeout doc |
| `elysium_carveout_stubbed_strategy_service_2026_08_12.md` (draft) | client-artefact judgment, correctly NA |
| `elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md` (88 items) | client-artefact HARD RULE, standing debt across 5+ rounds |
| `issues/defi_aavev3_bare_alias_enumerator_bug_2026_08_08.md` | 11 VM-launch attempts failed, infra-blocked |
| `issues/defi_adapter_dead_code_audit_2026_07_24.md` | governance-params-poller cross-repo gap, OPERATOR-NOTIFY tagged |
| `issues/defi_balancer_dex_pool_state_writer_schema_mismatch_2026_08_04.md` | human historical-backfill decision |
| `issues/defi_catalog_engine_config_key_contract_drift_2026_07_23.md` | design sub-decision |
| `issues/defi_collect_schedulers_paused_since_2026_07_18_2026_08_16.md` | gated on defi_track01 (itself NA) |
| `issues/defi_consolidator_paused_by_inflight_rebuild_vm_2026_08_07.md` | alert-routing design question |
| `issues/defi_gas_net_cost_partial_wiring_gap_2026_08_17.md` | self-dispatched, near-complete |
| `issues/defi_legacy_data_type_names_manifest_migration_scope_2026_08_04.md` | 5-part delete-safety proof needed |
| `issues/defi_legacy_fold_relaunch_vm_infra_flakiness_and_oom_2026_08_15.md` | claimed only by draft batch14 (false-orphan, promote batch14) |
| `issues/defi_lst_adapter_factory_family_unused_by_production_path_2026_08_09.md` | OPERATOR delete-vs-wire call |
| `issues/defi_lst_yields_backfill_blocked_manifest_consolidator_and_hyperliquid_perp_funding_gap_2026_08_08.md` | claimed only by draft batch14 |
| `issues/defi_manifest_allow_stale_fallback_incomplete_for_long_pause_2026_08_07.md` | design + relaunch, draft-batch-limbo |
| `issues/defi_manifest_venue_itype_canon_swap_execution_2026_08_10.md` | self-dispatched, live drain-condition-gated |
| `issues/defi_morpho_lending_indices_never_wired_2026_07_12.md` | gate_on_depends on data_completion_defi (unmet) |
| `issues/defi_onchain_dep_check_blazestake_lstrates_stalls_2026_08_06.md` | claimed only by draft batch18, held by batch9 park |
| `issues/defi_oracle_family_empty_path_exception_classification_2026_08_09.md` | BLOCKED-OPERATOR-DECISION |
| `issues/defi_oracle_prices_onchain_branch_retry_starvation_2026_08_16.md` | verify/retry, uncovered |
| `issues/defi_orphan_bucket_delete_list_includes_canonical_bucket_2026_08_15.md` | delete-safety re-proof |
| `issues/defi_pool_uppercase_recurrence_after_fold_2026_08_11.md` | **big finding**: ~17.4M defi-scope non-canonical objects (~30.7M fleet-wide), fix shipped, migration-plan-destination decision open |
| `issues/defi_pyth_oracle_prices_seeded_feeds_unfetchable_2026_08_03.md` | instrument_id naming design, correctly declined by batch11 |
| `issues/defi_strategy_ids_carry_banned_sce_suffix_identity_migration_2026_08_19.md` | duplicate-tracking overlap w/ execution_delta_proxy_repricer_generalization, unreconciled |
| `issues/defi_turbo_api_hides_real_captured_data_2026_07_07.md` | mechanical UAC registration, only cited in Deferred prose |
| `issues/defi_upstream_instruments_catalog_stale_2026_07_15.md` | design, no concrete done-when |
| `issues/defi_venue_e2e_batch1_deferred_followups_2026_08_17.md` | both items OPERATOR-tagged |
| `issues/dex_pool_fees_phantom_premise_false_real_mid_may_objects_2026_08_12.md` | correct a disproven premise in an archived plan |
| `issues/dp_fetch_009_defi_dex_pool_swaps_uniswap_v3_ethereum_stale_schema_validation_failed_2026_08_16.md` | `--apply` the reclass script |
| `issues/dp_vm_001_mdps_defi_2022_exit_nonzero_singledate_hang_2026_08_15.md` | relaunch-vs-wait + internal-timeout add |
| `issues/dp_vm_001_mdps_defi_2026_lock_ttl_staleness_budget_mismatch_2026_08_15.md` | budget-align + cross-check |
| `issues/dp_vm_002_mdps_defi_2022_dex_pool_swaps_pregenesis_no_manifest_trace_2026_08_15.md` | confirm-if-recurs |
| `issues/e2e_defi_config_taxonomy_wizard_roundtrip_2026_06_17.md` | DEFERRED-BY-DESIGN + BLOCKED-CREDENTIALS |
| `issues/exec_tenderly_2026_08_15.md` | OPERATOR credential provision |
| `issues/glassnode_kaiko_credential_ask_2026_08_09.md` | BLOCKED-CREDENTIALS |
| `issues/health_factor_monitor_no_production_entrypoint_liquidation_unprotected_2026_08_19.md` | see cross-tranche big findings item 6 |
| `issues/karak_decommission_2026_08_16.md` (27 items) | ruled Human/non-AO plan by design, mistagged parent_epic (should be defi_master not security_and_cross_cutting_master) |
| `issues/mdps_defi_pipeline_e2e_check_zero_captured_days_after_oom_fix_2026_08_17.md` | re-run for a real verdict |
| `issues/mev_engines_no_tenderly_simulate_bundle_call_site_2026_08_19.md` | deferred post-cutover |
| `issues/mev_engines_opportunity_detection_signals_unproduced_2026_08_18.md` | 4 build/design todos, 2 already extracted via batch17 |
| `issues/onchain_staking_apy_bps_single_day_annualization_noise_2026_08_09.md` | quant-math design call |
| `issues/pendle_venue_onboarding_2026_08_16.md` | conflict w/ venue_readiness_and_registry_hardening (NA) — do not double-dispatch |
| `issues/pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21.md` + `pnl_true_native_staking_return_spec_2026_08_20.md` | Option B build, operator-ruled 2026-07-29, unbuilt |
| `issues/solana_dex_pool_swaps_indexer_002_repeat_wedge_parked_2026_08_08.md` | mistagged — real owner is `ao` tranche (dispatch/crash-loop bug) |
| `issues/three_chain_registries_disagree_none_authoritative_2026_08_19.md` | BLOCKED-OPERATOR-DECISION, one-line, cheap to close |
| `lst_rate_honest_coverage_2026_07_21.md` | 2 items explicit operator-owned boundaries |

## Mechanical hygiene flags

- `uac_data_type_validity_combinator_fragmentation_2026_07_07.md` (self-dispatched): `mtds-oracle-prices-backfill`
  VM shows **zero running instances** 5 days after last checkpoint — no verify/relaunch/terminal decision made.
  Risk: incomplete oracle_prices honest-coverage for 5 DeFi lending protocols.
- `strategy_service_expansion_overlays_config_and_wizard_2026_08_12.md` (draft/NA): doc's own text says it "must
  land BEFORE the strategy-service repository is sent" — sits undispatched despite explicit deadline language.
- `defi_consolidated_closeout_2026_07_18.md` and `defi_track01_per_instrument_and_canon_id_2026_07_24.md` are both
  `assigned_vm: NA` — the tranche's de-facto master/gate docs cannot count as coverage, inflating the orphan count
  structurally (not a real gap for anything gated correctly on them).
- 2 batch plans stuck `status: draft` for days: `defi_satellite_ao_dispatch_batch14_2026_08_16.md`,
  `defi_satellite_ao_dispatch_batch18_2026_08_19.md`.

## Progress Log

- **2026-08-21**: Doc created directly from the 2026-08-21 /ag-closeout-audit defi Phase-1 sweep (4 batches). No
  mechanical fixes applied yet.
