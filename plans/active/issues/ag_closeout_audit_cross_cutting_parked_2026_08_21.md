---
doc_type: issue
title: ag-closeout-audit cross-cutting 2026-08-21 — orphan projection + parked findings
summary: >-
  2026-08-21 /ag-closeout-audit cross-cutting tranche Phase 1 audit (6 batches, 166 candidate docs — the largest
  tranche). Compact orphan table; the tranche's own P0 live-capital-safety findings live in the cross-tranche
  big-findings doc (items 1-5, 8, 12).
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ag-closeout-audit, cross-cutting, orphan-projection]
related: [/plans/active/issues/ag_closeout_audit_cross_tranche_big_findings_2026_08_21.md, /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md]
created: 2026-08-21
last_updated: 2026-08-21
author: claude-session-2026-08-21
parent_epic: security_and_cross_cutting_master
assigned_vm: NA
execution_scope: human
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0
estimate_calibrated_ai_days: 0
assigned_role: NA
drift_direction: NA
resolved_by:
locked_by:
source: ["2026-08-21 — /ag-closeout-audit cross-cutting, 6 Phase-1 batches, 166 candidates"]
depends_on: []
context_scope: [/plans/active/issues/ag_closeout_audit_cross_tranche_big_findings_2026_08_21.md]
---

# ag-closeout-audit cross-cutting 2026-08-21

166 candidates, 6 batches — the largest tranche. Both master closeout docs
(`cross_cutting_consolidated_closeout_2026_07_25.md`, `cross_cutting_closeout_observability_and_monitoring_2026_08_09.md`)
are `assigned_vm: NA` (methodology caveat). Orphan rate ran 50-66% in several batches — the highest of any tranche.

**P0 findings already in the cross-tranche big-findings doc**: items 1-5 (execution-service safety gaps), 8 (BLRS
recon), 12 (git-stash/autostash hazard).

## Orphaned — compact table (by batch)

### Batch 1-2 (docs #1-64)
| Doc | Taxonomy |
|---|---|
| `asset_class_to_asset_group_rename_2026_07_21.md` | operator ruling BLK-87fc93e4, human-only (9-repo breaking rename) |
| `bigquery_feature_ml_compute_engine_option_2026_06_08.md` | 3 unresolved operator design Qs |
| `bucket_estate_consolidation_closeout_2026_07_24.md` | producer-chain feature work, out of scope for its own plan |
| `bucket_fold_execution_strategy_2026_07_17.md` / `_features` / `_ml` / `_portfolio_state` | all human plans per 2026-07-17 ruling |
| `carry_staked_basis_funding_scan_experiment_2026_06_16.md` | ~24 research todos gated on v9-migration sequencing |
| `citadel_paper_batch_live_reconciliation_2026_06_19.md` | wallet hard-stop + real ML-feature work |
| `code_readiness_five_agent_coordinator_2026_08_19.md` + `t1-t5` (~78 items) | uses a different, legitimate dispatch mechanism (operator-launched interactive slots), not neglect |
| `colocated_feature_pipeline_in_memory_handoff_2026_06_21.md` | dependency-blocked — **re-verified 2026-08-21**: sole open item (1.5b column pruning) gated on `features_service_e2e_pipeline_test_2026_05_26.md`, which is still `status: active` with real open Track-1 remainder as of its own 2026-08-09 entry — gate NOT lifted, still genuinely dependency-blocked |
| `cross_ag_live_capture_parity_2026_08_14.md` | claimed only by draft batch19 — **re-verified 2026-08-21**: read all 7 open items directly. The one apparent bounded candidate ("file the IS BYBIT daily-catalog publish-timing gap as its own instruments-service issue") is **already a todo inside `cross_cutting_satellite_ao_dispatch_batch19_2026_08_19.md`** (line ~100) — not missing coverage, just sitting in an unpromoted `status: draft` batch. The other 6 items are genuinely OPERATOR-paired ("do both together or neither"), a still-diagnosing-chain wait-then-check, or open-ended engineering design ("give consumers a projected/filtered read path") per na-eligibility-audit's own 2026-08-21 re-assessment. Zero new extractable items found. |
| `cross_venue_funding_reversion_research_2026_07_24.md` | 13 research todos |
| `daily_trading_analyst_llm_job_design_2026_07_29.md` | build-phase todos |
| `data_completion_to_100_all_ag_2026_06_21.md` | ~5-6 substantively resolved (checkboxes unflipped), ~3 uncovered — **light-checked 2026-08-21**: 9 open items grepped (cefi backfill, IS-store backfill, cross-data_type completeness, DeFi catalogue MVP filter, DeFi honest-absence, CF-11 swallow-fixes, QG 5.70 regression restore, features-service category=defi ban) — each reads as substantial per-AG data/build work, not a mechanical checkbox-flip; not deep-read line-by-line, left for a future pass with more budget |
| `data_pipeline_ag_residual_backfill_decisions_2026_07_24.md` | operator HARD RULE items |
| `data_pipeline_alerts_batch_remediation_2026_07_15.md` | claimed only by draft batch19 — **re-verified 2026-08-21**: sole open item is the 24h-observation-window todo; na-eligibility-audit reaffirmed it blocked the SAME day (2026-08-21) — the real gate is "underlying sports/tradfi/cefi conditions actually clear", not pure elapsed time, still unmet. No new extractable item. |
| `data_pipeline_completion_2026_08_21.md` (7 items) | fresh, no batch has picked up the new set — **re-verified 2026-08-21**: all 7 open items grepped directly — 2 explicit `[OPERATOR]` sign-off items, 5 `[BACKEND]`/`[DATA]` items each phrased as a root-cause investigation or a cross-archetype design/build ("resolve the transitive closure per archetype", "root-cause the stray-tuple count growth") — genuinely too-large/design-needed, not mechanical |
| `instruments_completion_tracker_2026_07_06.md` | investigation + NA-gate pointers |
| `instruments_foundation_completeness_2026_06_24.md` / `_phase0_cross_cutting` | GATE 0 not signed off |
| `instruments_store_cf_canonicalization_single_walk_2026_07_24.md` | irreversible single-walk, KEEP-NA 7+ rounds |
| `is_catalogue_g1_root_audit_log_2026_07_24.md` | gated on IS backfill/UAC/v9 |
| `ao_scheduled_skills_benchmark_and_ruled_decisions_session_2026_07_30.md` | recursive benchmark re-runs |
| `blocking_gcs_writes_on_event_loop_cross_asset_group_2026_07_18.md` | 5 per-handler async-ification items — **re-verified 2026-08-21**: now 4 open (1 more, lst_rates, shipped 2026-08-21 since Phase-1). Read the doc's own repeated na-eligibility-audit history (6 passes through 2026-08-21, same day): every pass independently concludes the remaining items need real per-handler correctness judgment (an async-ification design call, a stage-module extraction refactor, a call-chain signature change) — not a mass mechanical edit. Confirmed, not extracted. |
| `capability_wizard_analysis_findings_2026_06_11.md` | F1-F3/F7/F10-F13/F16-F19/F46 still open — **light-checked 2026-08-21**: sole open checkbox is `[BLOCKED-CREDENTIALS]` (F46, perp `place_order` scaffolds) — genuinely operator/credential-gated, matches taxonomy |
| `ci_reconcile_overnight_batch_2026_08_11.md` | BLOCKED-PERMISSIONS, no self-service IAM |
| `defi_cefi_venue_chain_axis_contamination_2026_07_28.md` | partially worked, sequenced infra items remain — **re-verified 2026-08-21**: sole open item still GATED on `defi_pool_uppercase_recurrence_after_fold_2026_08_11.md`'s own `[SCRIPT]` re-retirement todo — read that doc's latest entries, "GATE STILL NOT MET" as of its most recent 2026-08-17 sessions, still `status: open`. Blocker has NOT shipped/resolved. Note: this doc's own `assigned_vm: planning` (already AO-dispatch-eligible directly, no satellite batch needed) makes "orphaned" a loose fit here regardless of the gate. |

### Batch 3-4 (docs #65-128)
| Doc | Taxonomy |
|---|---|
| `dp_cron_did_not_fire_still_storming_after_gcs_persistence_fix_2026_08_20.md` | reconcile 3 stale predecessor docs |
| `dp_revocation_release_never_resolves_identity_2026_08_15.md` | OPERATOR clear-stuck-holds |
| `e2e_wiring_reachability_audit_2026_08_15.md` | multiple P0 audit-trail/reconciliation-safety gaps, see big findings item 5-adjacent |
| `epsilon_zero_determinism_proof_never_runs_2026_08_20.md` | gated behind state-fabric build |
| `execution_delta_proxy_repricer_generalization_2026_08_18.md` | large hub, only 2 zero-risk items extracted |
| `external_instruction_bridge_atomic_not_wired_2026_08_20.md` | 2 execution-engine design efforts |
| `external_instruction_defi_handlers_simulation_only_2026_08_20.md` | BORROW/REPAY wiring + coverage extension |
| `fill_completed_event_schema_break_live_defi_2026_08_08.md` | OPERATOR P1 real-money correctness |
| `ibkr_gateway_infra_release_tag_stall_2026_08_11.md` | 2 items, reconfirmed 4x zero resolution |
| `live_path_has_no_stale_producer_revocation_2026_08_14.md` | P0 kill-switch-adjacent, claimed only by draft batch20 |
| `main_backmerge_backmerge_cycle_reverts_caller_stub_comment_fix_2026_08_20.md` | reproduce+root-cause the revert mechanism |
| `main_backmerge_to_ldr_no_retry_safety_net_for_non_pm_repos_2026_08_18.md` | open-ended investigation |
| `manifest_schema_drift_dup_residual_diagnosis_2026_08_15.md` | OPERATOR, worker-non-determinable |
| `manifest_writer_per_vm_shard_flush_scales_with_shard_size_2026_07_28.md` | claimed only by draft batch20 |
| `market_data_timestamp_semantics_collapsed_to_one_field_2026_08_20.md` | see cross-tranche big findings item 5 |
| `mdps_adapter_protocol_polars_seam_mis_scoped_ao_dispatch_2026_08_15.md` | redirected to parent doc |
| `mdps_backfill_vm_fleet_wedged_mid_shutdown_and_monitor_blind_2026_08_11.md` | P0 unpause cron blocked-on-deploy |
| `mdps_fleet_duplicate_relaunch_explosion_2026_08_15.md` | P0 cron re-enable, **triple-tracked** across 3 docs, claimed only by draft batch20 |
| `mdps_ws_venue_fallback_removal_polymarket_decision_2026_08_17.md` | OPERATOR |
| `mtds_backfill_vm_fleet_wedged...` see mdps entry above | |
| `mtds_ldr_cloud_build_docker_step6_failure_2026_08_10.md` | OPERATOR/dependency-blocked |
| `na_audit_progress_log_extracted_checkbox_never_flipped_pattern_2026_08_16.md` | routing-to-sports-tranche todo |
| `per_client_config_surface_keying_and_missing_axes_2026_08_12.md` | 8 design/build checkboxes + 2 OPERATOR |
| `plan_reconciler_findings_cross_cutting_2026_08_18.md` / `_2026_08_19.md` / `_security_and_cross_cutting_master_2026_08_19.md` | run-log punch-lists, ~4-5 + ~22 + ~35 residual items — mostly intentional future-pass input, not process failures |
| `plan_reconciler_full_corpus_sweep_2026_08_20.md` | 5/6 class-level todos NA (locked_by boilerplate, context-scout append-corruption, 104-doc auto-fold, 16 archive candidates, 153 P3s) |
| `pm_bats_tmux_fixture_leak_wedges_shared_host_2026_08_10.md` | 2 design questions |
| `quickmerge_exit_zero_on_failed_regate_and_silent_directory_files_2026_08_20.md` | P0, human-supervised by design |
| `recon_bucket_missing_nightly_recon_failing_2026_07_13.md` | see cross-tranche big findings item 8 |

### Batch 5-6 (docs #129-166)
| Doc | Taxonomy |
|---|---|
| `lazy_scoped_loading_refactor_2026_08_16.md` | known unresolved silent-data-corruption bug (caught pre-ship, no live risk) |
| `legacy_bucket_dual_write_decommission_2026_07_24.md` (8 items) | prod-bucket deletes = human-only hard stop |
| `manifest_v9_residual_2026_08_15.md` | 4 of 5 items uncovered, citation mismatch w/ batch14 |
| `master_data_canonicalisation_migration_catalogue_2026_06_07.md` | G4 --apply per-AG + WAVE 5 live-side |
| `mtds_venue_backfill_and_ops_hardening_residuals_2026_07_24.md` (7 items) | Kalshi/Extended/v9-column/ohlcv-1s gaps |
| `nick_ai_platform_disclosure_artifact_2026_08_16.md` (4 P0 items) | client-disclosure content, OPERATOR review gate |
| `per_client_config_surface_keying_and_missing_axes_2026_08_12.md` | (also listed above) |
| `pipeline_mode_partition_migration_2026_06_01.md` | prediction instruments-bucket gap |
| `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md` (6 items) | M6-M8 cadence/replay design |
| `producer_silence_flatten_protocol_2026_08_14.md` | see cross-tranche big findings item 4 |
| `service_config_ownership_and_instruction_contract_2026_08_12.md` (13 items, draft) | apparently never promoted past draft, worth an operator check |
| `state_fabric_artefacts_2026_08_20.md` (27 items) | client-artefact build-out |
| `state_fabric_uac_foundation_2026_08_20.md` (16 items) | UAC registry/StateEnvelope design-and-build |
| `v2_engine_venue_buildout_2026_06_15.md` (23 items) | "engine SHIPPED, BLOCKED on X" residuals |
| `venue_capability_route_axis_and_cross_ag_declarations_2026_08_14.md` | citation drift vs batch14 (3 items don't match extraction text) |
| `venue_readiness_and_registry_hardening_2026_08_16.md` (5 items) | consolidate venue_universe into UAC SSOT |
| `w14_execution_service_exchange_version_pinning_and_cassette_drift_2026_08_20.md` (10 items) | drift-detection design/build/CI |
| `w15_execution_service_venue_adaptor_security_audit_2026_08_20.md` | see cross-tranche big findings item 1 |
| `w22_strategy_execution_messaging_external_api_2026_08_20.md` | KILL_SWITCH/FLATTEN_POSITION vocabulary (P0 safety), BORROW/REPAY, BRIDGE wiring |
| `w_execution_orchestrator_oms_persistence_impl_2026_08_21.md` | see cross-tranche big findings item 2 |
| `walkthrough_feedback_remediation_2026_08_21.md` | NA-by-design, same code_readiness dispatch mechanism |

## Mechanical hygiene flags

- ✅ `instruments_mtds_consistency_remediation_residuals_2026_07_24.md`: 0 open checkboxes is a false-completion — real
  work lives in `defi_manifest_venue_itype_canon_swap_execution_2026_08_10.md` (outside covering set). **FIXED
  2026-08-21**: re-verified the delegated todo (e) is still genuinely open, added a real tracked `- [ ]` checkbox
  pointing to it (was prose-only in the summary before).
- ✅ `w15_execution_service_venue_adaptor_security_audit_2026_08_20.md`: duplicate `## Progress Log` H2 header from
  concurrent-editing. **FIXED 2026-08-21**: removed the duplicate header, merged into one Progress Log section.
- ✅ `walkthrough_feedback_remediation_2026_08_21.md`: unfilled `<shipping-sha>` placeholder in checkbox citations
  (parked doc said 4; a direct `grep -c` found 5). **FIXED 2026-08-21**: `git blame`d each placeholder line to its
  real landing commit and filled in the actual short shas (`b8f4fea784` ×4, `62828f01cb` ×1); re-verified
  `grep -c shipping-sha` now returns 0.
- ⬜ `context_scout_stale_citations_and_doc_drift_2026_08_20.md`'s real coverage came from the **ao** tranche's batch,
  not any cross-cutting batch — cross-tranche attribution nuance, not a gap. **Re-verified 2026-08-21**: confirmed
  its own Disposition section already correctly points every extracted finding at
  `/plans/active/ao_satellite_ao_dispatch_batch2_2026_08_21.md` — no fix needed in the target doc, this flag was
  purely informational.
- ✅ `cross_cutting_satellite_ao_dispatch_batch19_2026_08_19.md` / `batch20_2026_08_19.md` — both `status: draft`,
  never promoted; their `_finalize` companions are `status: active` and structurally can never complete. **FIXED
  2026-08-21**: flipped both `_finalize` docs' `status: active` → `blocked` (their sole `gate_on_depends: true`
  target stays draft, so they cannot complete — `blocked` states the real reason instead of the misleading
  `active`). Re-flip to `active` once an operator promotes batch19/batch20. **Not fixed** (out of mechanical-fix
  scope, needs an operator call): whether to actually promote batch19/batch20 themselves — both contain real,
  already-vetted, conflict-checked bounded work from 2026-08-19 that has sat undispatched for 2+ days.

## Todos

- [ ] [INFRA] P2. Per D8 ruling (ADOPTED-REC 2026-08-21: "Promote all — already conflict-checked, vetted work idle
      only for lack of sign-off"): promote `cross_cutting_satellite_ao_dispatch_batch19_2026_08_19.md` and
      `cross_cutting_satellite_ao_dispatch_batch20_2026_08_19.md` from `status: draft` to `status: active`, and
      flip their gated `_finalize` companions' `status` back from `blocked` to `active` (they were set to `blocked`
      this same run precisely because their drafts were undispatched — see Mechanical hygiene flags above). Done-when:
      both batch frontmatter read `status: active`, both finalize plans read `status: active`, and
      `regen_backlog_from_plan.py` ingests both batches' todos (confirmed via a live backlog listing).

## Progress Log

- **2026-08-21**: Doc created directly from the 2026-08-21 /ag-closeout-audit cross-cutting Phase-1 sweep (6
  batches, the largest tranche). No mechanical fixes applied yet.
- **2026-08-21 — ruling D8 (Draft satellite batches activation)**: ADOPTED-REC 2026-08-21 (autonomous-dispatch
  authority, AUTONOMOUS_AGENT_RULES rule 2): Promote all — each is already conflict-checked, vetted work idle only
  for lack of sign-off; the defi batch also stops recurring false DP-FETCH-009 pages. Source:
  /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger.
- **ag-closeout-audit 2026-08-21 (cross-cutting tranche, Phase 2+3 sweep)**: Phase 2 — applied all 5 mechanical
  hygiene fixes (4 real edits + 1 confirmed-no-op), see updated flags above with per-item evidence. Phase 3 — did a
  full re-verification pass over every row in the Batch 1-2 orphan table (24 rows): deep-read 6 candidate docs in
  full (`cross_ag_live_capture_parity`, `data_pipeline_alerts_batch_remediation`,
  `blocking_gcs_writes_on_event_loop_cross_asset_group`, `colocated_feature_pipeline_in_memory_handoff`,
  `defi_cefi_venue_chain_axis_contamination` + its gating sibling doc, `data_pipeline_completion_2026_08_21`),
  light-checked 2 more via grep (`data_completion_to_100_all_ag`, `capability_wizard_analysis_findings`), and
  trusted the remaining ~16 rows' already-precise one-line gates (operator ruling / research-class / irreversible
  single-walk — unambiguous gate types that don't need a re-verify-shipped check). **Result: zero new
  genuinely-bounded AO-dispatch candidates found** — the one apparent candidate (file the IS BYBIT daily-catalog
  publish-timing gap as its own issue) turned out to already be a todo inside the still-`draft`
  `cross_cutting_satellite_ao_dispatch_batch19_2026_08_19.md`, not missing coverage. See the updated table rows
  above for full per-doc evidence. **No new batch23 doc created** — there was nothing genuinely bounded and
  uncovered to put in one. **NOT REACHED this session**: Batch 3-4 (docs #65-128, ~24 rows) and Batch 5-6 (docs
  #129-166, ~38 rows) of the orphan table were not re-verified at all — a future session should pick up there.
  **Big finding surfaced**: batch19 and batch20 (both real, conflict-checked, already-vetted work from
  2026-08-19) have sat `status: draft`/undispatched for 2+ days with their gated `_finalize` companions
  incorrectly reading `status: active` (now corrected to `blocked`, see above) — worth an operator look at
  promoting them rather than continuing to mine for new extractions when known-good work already sits unshipped.
