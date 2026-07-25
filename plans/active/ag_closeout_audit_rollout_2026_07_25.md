---
doc_type: plan
title: AG closeout-audit rollout — cefi/defi/tradfi/prediction (sports treatment, generalized)
summary: >-
  Autonomous session (/autonomous, operator away, 2026-07-25) driving the /ag-closeout-audit skill across the 4 asset
  groups that haven't had it yet — cefi, defi, tradfi, prediction — each of which already carries its own
  <ag>_consolidated_closeout_2026_07_18.md sitting in the same pre-treatment state sports was in before this session's
  earlier work (satellite triage -> sports_satellite_ao_dispatch_batch2 -> gated batch2_finalize -> orphan-projection
  audit). For each AG: discover its covering-plan set, run a per-doc Workflow classification audit (archivable now /
  archivable once currently-dispatched work lands / orphaned with no coverage / cross-cutting exclude), then — with a
  hard conflict-check against the consolidated plan's own todos first — draft (status: draft, never auto-shipped to
  active) the next AO-dispatch-batch + gated finalize plan pair for genuinely AO-eligible orphaned work. This is the
  plan-of-record / Progress Log for the whole rollout per cursor-configs/AUTONOMOUS_AGENT_RULES.md rule 6 — a compressed
  future-session must be able to resume losslessly from this doc alone.
status: complete
nature: process
asset_group: [cefi, defi, tradfi, prediction, sports, cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ag-closeout-audit, autonomous, plan-hygiene, ao-dispatch, orphan-audit]
related:
  - /cursor-configs/skills/ag-closeout-audit/SKILL.md
  - /plans/active/sports_consolidated_closeout_2026_07_19.md
  - /plans/active/sports_satellite_ao_dispatch_batch2_2026_07_24.md
  - /plans/active/sports_satellite_ao_dispatch_batch2_finalize_2026_07_24.md
  - /plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: research
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 4.8
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Operator instruction 2026-07-25: "keep going for the next 8 hours or until you are done with everything /autonomous
  ... anything remaining you need to queue because you have to ask me operator questions for decisions make clear for me
  so that i can answer when im back" — issued immediately after confirming the /ag-closeout-audit skill's scope (audit +
  report + draft next batch) via AskUserQuestion. Genuine operator-decision-caliber questions are QUEUED in the linked
  issue doc per that instruction, NOT silently auto-decided (this overrides AUTONOMOUS_AGENT_RULES.md rule 2's default
  "decide yourself, don't ask" for THIS session only — the operator explicitly asked for queued questions instead).
---

# AG closeout-audit rollout — cefi/defi/tradfi/prediction

## Todos

- [x] [DOC] P1. **Sports**: got the 53-doc orphan-audit workflow's results (`wf_8cdc5fb5-b1f`, 53/53 agents, 0 errors),
      synthesized + journaled below, reported to operator. Also archived the 2 `archivable_now` docs the audit found
      (`sports_closeout_batch1_finalize_2026_07_24.md`, `data_completion_sports_history_2026_07_24.md`) —
      unified-trading-pm (see Progress Log; this specific ship hit a real bug, see the 2026-07-25 "shipping bug" entry
      below).
- [x] [DOC] P1. **Sports**: drafted + shipped `sports_satellite_ao_dispatch_batch3_2026_07_25.md` + finalize (12
      conflict-cleared todos of 25 candidates; triage `wf_74a99101-69b`, 26 agents, 0 errors). See Progress Log.
- [x] [DOC] P1. **cefi**: audit done (`wf_90271270-b12`, 49/49 agents, 0 errors), 5 of 7 `archivable_now` docs resolved
      (2 deferred — see Progress Log), triage workflow (`wf_b4e843d4-5bc`, 29 docs) in flight.
- [x] [DOC] P1. **defi**: audit done (`wf_d2678add-324`, 56/56 agents, 0 errors), all 8 `archivable_now` docs resolved,
      triage workflow (`wf_bbe74687-4e1`, 39 docs) in flight.
- [x] [DOC] P1. **tradfi**: audit done (`wf_daa543c3-c36`, 23/23 agents, 0 errors); drafted + shipped tradfi's
      FIRST-EVER AO-dispatch batch, `tradfi_satellite_ao_dispatch_batch1_2026_07_25.md` + finalize (5 conflict-cleared
      todos of 43 candidates; triage `wf_92bc129c-2a8`, 21 agents, 0 errors). See Progress Log.
- [x] [DOC] P1. **prediction**: audit done (`wf_a5170a34-d47`, 20/20 agents, 0 errors); drafted + shipped prediction's
      FIRST-EVER AO-dispatch batch, `prediction_satellite_ao_dispatch_batch1_2026_07_25.md` + finalize (7
      conflict-cleared todos, all from `prediction_phase_ab_residuals_2026_07_24.md`; triage `wf_b8829ea8-6cd`, 13
      agents, 0 errors). See Progress Log.
- [x] [DOC] P1. **cefi + defi**: triage workflows (`wf_b4e843d4-5bc`, `wf_bbe74687-4e1`) completed; applied the same
      conflict-cleared-subset drafting discipline used for sports/tradfi/prediction to author
      `cefi_satellite_ao_dispatch_batch1_2026_07_25.md` (33 todos) and `defi_satellite_ao_dispatch_batch1_2026_07_25.md`
      (53 todos, defi's FIRST-EVER AO-dispatch batch) + finalize plans. See Progress Log.
- [x] [DOC] P2. **Final report** (AUTONOMOUS_AGENT_RULES.md rule 9): all 5 AGs audited, all 5 have a drafted batch. See
      the closing Progress Log entry below. Loop ends with this ship.
- [x] [DOCS] P3. **Clarify the `--files` delimiter — space-separated, not comma** — root-caused this session (see the
      "combined-ship recovery saga" Progress Log entry, corrected). **DONE 2026-07-25**: added a clarifying block to
      `/codex/08-workflows/ci-cd-flow.md`'s Pass-2-quickmerge section (CLAUDE.md itself already points there as the
      quickmerge SSOT and has essentially zero byte headroom left under its hard cap, 39,925/40,960 B — not touched).
      `check_frontmatter_schema.py --files` has the identical trap; left as a smaller note for a future pass since its
      own doc surface is thinner.

## Progress Log

- **2026-07-25 (session start)**: Plan created. Prior work this session (before /autonomous): shipped the
  finalize-plan-coverage QG rule (task_template.md + check_finalize_plan_coverage.py + baseline), landed the
  verify-slot-host-symmetry.sh RECOVERED-bookend fix, built + shipped the /ag-closeout-audit skill (6 branch-drift /
  shared-venv-corruption retries — all confirmed transient, none real defects), filed
  `issues/test_build_index_deterministic_races_on_concurrent_corpus_writes_2026_07_25.md` (found while shipping the
  skill — real flakiness in a pre-existing test, not caused by this session's changes). Launched a 53-agent Workflow
  classifying every sports-primary doc (`wf_8cdc5fb5-b1f`) — in flight when /autonomous was invoked.

- **2026-07-25, sports orphan-audit results** (`wf_8cdc5fb5-b1f`, 53/53 agents done, 0 errors, 3.46M subagent tokens,
  2453s): of 72 total sports-primary docs (asset_group ⊆ {sports, prediction, meta}, cross-cutting multi-AG docs
  pre-excluded), 19 were already `status: resolved`/`archived` before this audit (excluded from the deep pass) and 53
  were classified. Breakdown of those 53: **2 archivable_now** (zero real remaining open work today — see next entry,
  both archived), **22 archivable_after_planned_work** (open today, but ALL of it is dispatched via a real todo in
  `sports_consolidated_closeout_2026_07_19.md` or `sports_satellite_ao_dispatch_batch2_2026_07_24.md` +
  `batch2_finalize` — will reach 0 once those land), **27 orphaned** (13 `orphaned_partial_coverage` + 14
  `orphaned_never_touched` — one of the 14 is `sports_consolidated_closeout_2026_07_19.md` itself, a tautological
  self-reference since the doc's own todos completing is the audit's premise, so the real count is **26 satellite
  docs**), **2 exclude_cross_cutting** (the per-doc agent correctly caught 2 docs the deterministic asset_group
  pre-filter missed: `predictions_ml_walk_forward_and_arb_2026_06_20.md` and
  `issues/cross_ag_prediction_rows_bleed_into_sports_instruments_index_2026_07_20.md`). **Answer to the operator's
  question**: **26 sports-primary plan/issue docs would remain orphaned** even after
  `sports_consolidated_closeout_2026_07_19.md`'s own todos AND `sports_satellite_ao_dispatch_batch2_2026_07_24.md` + its
  finalize plan ALL run to completion. Full per-doc list + reasoning:
  `subagents/workflows/wf_8cdc5fb5-b1f/journal.jsonl` (also mirrored to `/tmp/.../scratchpad/sports_audit_results.json`
  this session, not committed — regenerate from the journal if needed). The 26: `data_completion_sports_2026_07_24.md`,
  `sports_arb_decay_window_and_alpha_gate_design_2026_07_21.md`, `sports_catalog_league_grain_only_scope_2026_07_08.md`,
  `sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md`,
  `sports_group_c_execution_backtest_harness_2026_07_21.md`,
  `sports_consolidated_closeout_aggregated_sources_2026_07_24.md`,
  `sports_legacy_fixtures_path_migration_2026_07_24.md`, `sports_live_availability_and_source_latency_2026_07_24.md`,
  `sports_odds_feature_naming_canonicalization_2026_07_21.md`,
  `sports_predictions_live_mode_activation_readiness_2026_07_21.md`,
  `issues/canonical_player_stats_fixture_events_quality_2026_07_16.md`,
  `issues/fixtures_manifest_duplicate_collision_residual_2026_07_24.md`,
  `issues/fixtures_manifest_legacy_backfill_2026_07_24.md`,
  `issues/footystats_matches_predictions_fetch_gaps_2026_07_08.md`,
  `issues/sports_dependency_check_manifest_vs_gcs_path_2026_07_08.md`,
  `issues/sports_day_all_teams_venues_fold_key_scheme_mismatch_2026_07_25.md`,
  `issues/sports_features_layer_findings_sweep_2026_07_18.md` (~35+ open checkboxes, the 73-todo sweep doc — too large
  for batch3, needs its own dedicated triage pass, see todo below),
  `issues/sports_fixtures_schedule_noncanonical_raw_league_id_folders_2026_07_24.md`,
  `issues/sports_fixtures_schedule_wrong_schema_day_2026_04_14.md`,
  `issues/sports_legacy_duplicate_triage_2026_07_22.md`,
  `issues/sports_odds_markets_outcomes_settlements_arbitrage_expected_since_2024_zero_captured_2026_07_24.md`,
  `issues/sports_odds_stale_fixture_reinjection_2026_07_14.md`,
  `issues/sports_odds_team_name_alias_gap_south_america_2026_07_09.md`,
  `issues/sports_odds_feature_naming_four_way_mismatch_2026_07_21.md`,
  `issues/sports_phantom_audits_reference_not_marketdata_2026_07_14.md`,
  `issues/sports_shard_enumeration_cartesian_blowup_2026_07_20.md`. Next: conflict-checked batch3 draft for the
  AO-eligible subset (triage workflow `wf_74a99101-69b` launched).

- **2026-07-25, archival + a real shipping bug found**: archived the 2 `archivable_now` docs
  (`sports_closeout_batch1_finalize_2026_07_24.md`, `data_completion_sports_history_2026_07_24.md` →
  `plans/archive/2026_07/`) with ARCHIVED banners and fixed the 3 real corpus referrers
  (`data_completion_sports_2026_07_24.md`, `sports_live_availability_and_source_latency_2026_07_24.md`,
  `sports_satellite_ao_dispatch_batch2_finalize_2026_07_24.md`). **First ship attempt landed a HALF-migration**: a
  concurrent, unrelated commit (`9aed72662`, "verify + flip 3 tradfi cheap-win checkpoints") picked up only the ADD half
  of the `git mv` rename (both archived docs' new-path content, correct) but NOT the DELETE half — leaving a stale
  duplicate at BOTH the old `plans/active/...` path AND the new `plans/archive/2026_07/...` path simultaneously — and
  separately dropped this doc's own todo-1-flip and this whole Progress Log entry back to the session-start version
  (confirmed via `git ls-files` showing both paths tracked at HEAD, and this file reverting to 83 lines). This is
  exactly the class of bug `/plan-reconcile`'s Phase 5.9(c) warns about ("VERIFY AT HEAD — never trust a commit
  summary... a hook conflicts, the restore fails, and your edits are silently rolled back while the working tree still
  LOOKS right"), now confirmed on THIS branch under heavy concurrent load, not just a hypothetical. `git rm` on the 2
  stale active-path duplicates is BLOCKED for autonomous workers by agent-orchestrator's `block_destructive_commands.py`
  guardrail — correctly not circumvented; instead converted both into explicit `STALE DUPLICATE` redirect stubs with a
  queued `[OPERATOR] git rm` todo each, and queued the actual delete in
  `issues/autonomous_session_operator_decisions_2026_07_25.md` entry 1. Redid all the lost edits + shipped the stubs in
  a second attempt, this time verifying content immediately before AND after staging — **landed clean and verified AT
  HEAD** (`unified-trading-pm@6b6e4ac14`, confirmed via `git show HEAD:<path>` on all 7 files, not just `git status`).

- **2026-07-25, tradfi + prediction orphan-audit results**: launched 4 more per-AG orphan-audit Workflows in parallel
  (cefi 49 docs, defi 56 docs, tradfi 23 docs, prediction 20 docs) to make full use of the /autonomous window. tradfi
  (`wf_daa543c3-c36`, 23/23 agents, 0 errors) and prediction (`wf_a5170a34-d47`, 20/20 agents, 0 errors) finished first.
  - **tradfi**: 21 of 23 orphaned (13 `orphaned_never_touched` + 8 `orphaned_partial_coverage`), 1
    `archivable_after_planned_work` (the master closeout itself — self-referential, same caveat as sports), 1
    `archivable_now` (`issues/tradfi_t1_no_working_mtds_job_2026_07_17.md` — its item independently verified `[x]` with
    live re-verification evidence in a forked sibling doc). **91% orphan rate** — much higher than sports' 36% (26/72).
    Root cause, confirmed per-doc: `tradfi_consolidated_closeout_2026_07_18.md`'s own dispatched checkboxes cover
    DIFFERENT scope (Phase A2/C adapter+data-status work) from what its satellite docs actually need; the satellite
    docs' specific items appear only in the closeout's "Aggregated source docs (referenced, not duplicated)" digest
    section — an explicit non-coverage index, same pattern as sports' `..._aggregated_sources_...md`. tradfi never got a
    batch1-style AO-dispatch extraction at all (unlike sports, which had batch1+batch2 before this session). The 21
    orphaned: `canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md`, `data_completion_tradfi_2026_07_15.md`,
    `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md`, `tradfi_backfill_throughput_followups_2026_07_24.md`,
    `tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md`,
    `tradfi_manifest_content_recovery_completion_2026_07_24.md`, `tradfi_multisource_backfill_2026_06_22.md`,
    `tradfi_phase_d_terminal_gate_2026_07_24.md`, `tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md`,
    `issues/cme_combo_underlying_extraction_garbage_2026_07_19.md`,
    `issues/databento_default_executor_dns_starvation_risk_2026_07_17.md`,
    `issues/tradfi_backfill_oom_remediation_2026_06_24.md`,
    `issues/tradfi_canonical_path_migration_design_2026_07_19.md`,
    `issues/tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md`,
    `issues/tradfi_eu_not_draining_source_axis_drift_2026_06_24.md`,
    `issues/tradfi_fx_provenance_and_manifest_id_defects_2026_07_24.md`,
    `issues/tradfi_mvp_mode_unreachable_dead_gate_2026_07_08.md`,
    `issues/tradfi_manifest_rebuild_deletion_resurrection_gap_2026_07_20.md`,
    `issues/tradfi_ohlcv_attempted_failed_cluster_2026_07_23.md`,
    `issues/tradfi_todo_cells_below_vendor_discovery_floor_2026_07_20.md`,
    `issues/tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md`.
  - **prediction**: 13 of 20 orphaned (9 `orphaned_never_touched` + 4 `orphaned_partial_coverage`), 6
    `exclude_cross_cutting` (correctly deferred — these are the sports+prediction dual-tagged docs already covered by
    the SPORTS audit; verified no double-counting), 1 `archivable_after_planned_work` (master closeout,
    self-referential). Same structural finding as tradfi: `prediction_consolidated_closeout_2026_07_18.md`'s own
    checkboxes are new audit/verification work, not dispatch of its phase-child docs' (phase_ab_residuals, phase_c,
    phase_d, phase_e) own specific open items — those only appear in prose digest form. No AO-dispatch-batch exists for
    prediction at all. The 13 orphaned: `data_completion_prediction_2026_07_15.md`,
    `prediction_phase_ab_residuals_2026_07_24.md`, `prediction_phase_c_data_status_ui_2026_07_24.md`,
    `prediction_phase_d_formal_smoke_and_backfill_2026_07_24.md`, `prediction_phase_e_football_arb_live_2026_07_24.md`,
    `predictions_ml_walk_forward_and_arb_2026_06_20.md`, `predictions_other_bucket_and_ui_drilldown_2026_06_20.md`,
    `issues/kalshi_live_capture_regression_and_drift_2026_07_13.md`,
    `issues/prediction_arb_live_execution_bridge_2026_07_20.md`,
    `issues/prediction_lifecycle_prefetch_gate_and_resolution_day_catalogue_2026_07_14.md`,
    `issues/prediction_phantom_reconciler_wipes_bundle_atom_2026_07_10.md`,
    `issues/prediction_polymarket_legacy_dual_write_trees_metadata_loss_2026_07_24.md`,
    `issues/prediction_universe_capture_dead_since_07_01_2026_07_06.md`. Next: AO-eligibility triage + conflict-check
    workflows for both AGs' orphaned docs (mirroring sports batch3), then draft `tradfi_satellite_ao_dispatch_batch1`
    and `prediction_satellite_ao_dispatch_batch1` (status: draft) for the AO-eligible subset of each. cefi (49 docs) and
    defi (56 docs) audits still in flight.

- **2026-07-25, cefi orphan-audit results** (`wf_90271270-b12`, 49/49 agents, 0 errors, 3.53M subagent tokens): 30
  orphaned (20 `orphaned_never_touched` + 10 `orphaned_partial_coverage`, one of the 10 is the master closeout itself —
  self-referential, its own Track 3/Track 4 have zero checkboxes at all, so it's genuinely NOT self-covering unlike
  sports'/tradfi's/prediction's master docs; real satellite orphan count is **29**), **7 `archivable_now`** (real,
  independently-verified-done docs sitting un-archived — `cefi_consolidated_closeout_aggregated_sources_2026_07_24.md`,
  `issues/aster_capture_broken_coverage_and_completeness_2026_07_20.md`,
  `issues/cefi_deribit_combo_and_okx_bare_venue_gaps_2026_07_12.md`,
  `issues/cefi_okx_margin_type_wire_key_ambiguity_reclassification_2026_07_22.md`,
  `issues/deployment_api_cefi_venue_canonical_compare_test_regression_2026_07_21.md`,
  `issues/instruments_service_deribit_combo_purge_test_drift_2026_07_21.md`,
  `issues/mtds_rule11_shard_count_stale_baseline_2026_07_21.md`), 9 `exclude_cross_cutting` (correctly caught — several
  prediction-primary docs mis-tagged with cefi, plus a few genuinely cross-cutting issue docs), 3
  `archivable_after_planned_work`. Same structural pattern as tradfi/prediction: satellite docs' items are only
  digest-referenced in the master's Track sections, not actually dispatched via a real checkbox. cefi has never had an
  AO-dispatch-batch extraction. The 29 orphaned satellite docs: `aster_and_cefi_rolling_adv_feature_2026_07_21.md`,
  `cefi_4surface_migration_execution_log_2026_07_24.md`, `data_completion_cefi_2026_07_15.md`,
  `instruments_cefi_g1_g5_gate_execution_2026_07_24.md`, `issues/aster_mtds_failure_count_regression_2026_07_07.md`,
  `issues/bug_c_normalize_id_collision_options_futures_2026_07_22.md`,
  `issues/cefi_available_at_wallclock_despite_deterministic_row_timestamp_2026_07_24.md`,
  `issues/bybit_futures_chain_write_shape_2026_07_13.md`, `issues/cefi_backfill_per_day_catalogue_reload_2026_07_20.md`,
  `issues/cefi_batch_download_oom_crashloop_capture_halt_2026_07_24.md`,
  `issues/cefi_batch_manifest_blank_instrument_type_on_failure_2026_07_12.md`,
  `issues/cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md`,
  `issues/cefi_chain_tail_v6_canonicalisation_2026_07_21.md`,
  `issues/cefi_content_migration_vm_wedged_worker_2026_07_23.md`,
  `issues/cefi_future_instrument_type_no_candle_schema_contract_2026_07_21.md`,
  `issues/cefi_high_attempted_failed_batch_cluster_2026_07_23.md`,
  `issues/cefi_onchain_perp_batch_venue_allowlist_gap_2026_07_12.md`,
  `issues/cefi_onchain_venues_mislabeled_batch_tardis_2026_07_20.md`,
  `issues/cefi_residual_followups_after_honest_done_2026_07_17.md`,
  `issues/cefi_shard_enumeration_blindspots_and_canonical_fetch_dependency_2026_07_18.md`,
  `issues/deribit_live_options_chain_path_noncanonical_2026_07_21.md`,
  `issues/instruments_service_cefi_qg_red_on_ldr_head_2026_07_08.md`,
  `issues/mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md`,
  `issues/mtds_mdps_order_book_imbalance_duplicated_2026_07_07.md`,
  `issues/per_venue_scope_key_provisioning_incomplete_2026_07_23.md`,
  `issues/onchain_venues_mislabeled_batch_tardis_lane_2026_07_20.md`,
  `issues/rotate_exchange_keys_stale_venue_registry_2026_07_23.md`, `issues/tardis_concurrent_ip_lockout_2026_07_12.md`,
  `issues/tardis_impossible_combinations_recorded_as_attempted_failed_2026_07_17.md`. Next: archive the 7
  `archivable_now` docs (careful ship this time — the earlier sports archival hit a half-landed-rename bug from
  concurrent branch activity, verify AT HEAD not just exit code) + launch the AO-eligibility triage for the 29 orphaned.
  defi (56 docs) audit still in flight.

- **2026-07-25, defi orphan-audit results** (`wf_d2678add-324`, 56/56 agents, 0 errors, 4.09M subagent tokens): 40
  orphaned (24 `orphaned_never_touched` + 16 `orphaned_partial_coverage`, one of the 16 is the master closeout itself —
  self-referential — real satellite orphan count is **39**), **8 `archivable_now`** (all 8 resolved: 6
  `mvp_backfill_defi_onchain_v10_operational_log_part<N>` history-fork docs flipped `status: complete` in place,
  `defi_pool_canonical_instrument_id_policy_contradiction_2026_07_17.md` shipped,
  `gas_fees_lst_rates_manifest_bucket_mismatch_2026_07_10.md` deliberately NOT flipped — carries
  `locked_by: live-defi-rollout`, queued for the operator, entry 2 in
  `autonomous_session_operator_decisions_2026_07_25.md`), **6 `archivable_after_planned_work`**, **2
  `exclude_cross_cutting`**. Same structural pattern as cefi/tradfi/prediction. Next: AO-eligibility triage
  (`wf_bbe74687-4e1`, 39 docs) launched.

- **2026-07-25, cefi/tradfi/prediction archival-now resolutions**: 5 of cefi's 6 non-index `archivable_now` issue docs
  resolved with `resolved_by` citations (`aster_capture_broken_coverage_and_completeness`,
  `cefi_okx_margin_type_wire_key_ambiguity_reclassification`,
  `deployment_api_cefi_venue_canonical_compare_test_regression`, `instruments_service_deribit_combo_purge_test_drift`,
  `mtds_rule11_shard_count_stale_baseline`). `cefi_deribit_combo_and_okx_bare_venue_gaps_2026_07_12.md` (the 6th)
  deliberately EXCLUDED from shipping — it's already 1497 lines, well over the 1000-line hard cap from 4+ prior
  sessions' appended content unrelated to my edit; the status-flip edit is preserved locally but needs a proper
  line-cap-remediation split (extract a `_history` fork doc, matching the `data_completion_sports_history` precedent)
  before it can ship — deferred to a follow-up pass, not rushed here. The 7th cefi `archivable_now` candidate
  (`cefi_consolidated_closeout_aggregated_sources_2026_07_24.md`) was deliberately NOT archived at all — its verdict
  conflicted with how the sibling sports audit treated the equivalent still-active discoverability index for a
  not-yet-done closeout; left active pending operator review.

- **2026-07-25, sports batch3 + tradfi batch1 + prediction batch1 drafted and shipped** (all `status: draft`, each
  paired with a gated finalize plan per `task_template.md` §4): `sports_satellite_ao_dispatch_batch3_2026_07_25.md` (12
  conflict-cleared todos of 25 AO-eligible candidates the sports triage found — 23 were conflict-gated and are preserved
  in its Deferred section); `tradfi_satellite_ao_dispatch_batch1_2026_07_25.md` (tradfi's FIRST-EVER AO-dispatch batch —
  5 conflict-cleared todos of 43 candidates, 38 deferred); `prediction_satellite_ao_dispatch_batch1_2026_07_25.md`
  (prediction's FIRST-EVER AO-dispatch batch — 7 conflict-cleared todos, all extracted from the single highest-yield
  source doc `prediction_phase_ab_residuals_2026_07_24.md`; the other 12 orphaned prediction docs deferred entirely).
  Every conflict-gated candidate across all three batches (60+ total) is preserved in its plan's own Deferred section
  and summarized for the operator, per the explicit 2026-07-25 instruction to never silently resolve a conflict rather
  than queue it. cefi + defi triage workflows (`wf_b4e843d4-5bc`, `wf_bbe74687-4e1`) still in flight — their batch1
  plans follow the same discipline once ready.

- **2026-07-25, shipping the combined batch — 2 real (non-transient) blockers hit and fixed, not just retried**: (1)
  `check_finalize_plan_coverage.py` flagged a genuine 2nd ratchet violation —
  `infra_capture_and_devops_leftovers_2026_07_06.md` (AO Plan 6 of the instruments-completion set, still
  `status: active` with 4 open `BLOCKED-*` items), an already-committed pre-existing AO plan that predates the
  2026-07-24 finalize-plan-coverage rule and never got a companion finalize doc — surfaced now because a concurrent
  frontmatter-hygiene commit touched it today. Not mine to ignore (it was blocking the shared gate for everyone), so
  authored `infra_capture_and_devops_leftovers_2026_07_06_finalize_2026_07_25.md` (3 todos: re-verify the ASTER
  connector prereqs, re-check the 4 credential/operator gates, conditionally archive) to backfill the gap — back to
  baseline=1. (2) `test_build_index_is_deterministic` flaked again (same pre-filed
  `issues/test_build_index_deterministic_races_on_concurrent_corpus_writes_2026_07_25.md` class — two `build_index()`
  calls inside one test observed different `status:` values for the same doc, i.e. genuine concurrent-write racing
  during the test, not caused by my changeset) — confirmed transient, retried clean.

- **2026-07-25, cefi AO-eligibility triage results** (`wf_b4e843d4-5bc`, 29/29 agents, 0 errors, 3.0M subagent tokens):
  40 total `ao_eligible_todos` found across the 29 orphaned cefi docs, 40 `conflicts_found` entries to check against
  them (3 docs flagged `doc_too_large_or_risky_for_batch`). Delegated the per-todo conflict-matching (conflicts are a
  flat per-doc list, not indexed to specific todos — each has to be read and judged against every eligible item) to a
  sub-agent under the same discipline used for sports/tradfi/prediction. Result:
  **`cefi_satellite_ao_dispatch_batch1_2026_07_25.md`** (cefi's FIRST-EVER AO-dispatch batch — 33 todos from 38
  conflict-cleared candidates, grouped to avoid in-batch same-file collisions) + its gated finalize companion. 2 of the
  40 candidates excluded: 1 from the `doc_too_large_or_risky_for_batch` doc
  (`cefi_4surface_migration_execution_log_2026_07_24.md`), 1 (the LATE colliding-venue-renames Range A/B/C `--apply`
  work) excluded on cross-doc evidence that it's already actively running under a separate live `/autonomous` session —
  dispatching it fresh would race a live prod GCS migration. No new operator-decision question needed; both exclusions
  resolved cleanly by the discipline itself. Validated (`check_frontmatter_schema.py`, `check_todo_format.sh`,
  `check_line_caps.sh` all clean) and folded into the same ship as the infra finalize backfill + cefi/defi resolutions +
  sports/tradfi/prediction batches. defi triage (`wf_bbe74687-4e1`) still the only one outstanding.

- **2026-07-25, defi AO-eligibility triage + batch1 drafted (last of 5 AGs)** (`wf_bbe74687-4e1`, 38/39 agents on the
  first pass — 1 (`issues/defi_perp_daily_ctx_manifest_gap_reader_risk_2026_07_22.md`) errored on a dropped connection
  mid-response, retried clean via a follow-up Workflow's own RetryMissing phase, 4.09M+ subagent tokens combined): 59
  total `ao_eligible_todos` found across the 38+1 orphaned defi docs (1 doc flagged `doc_too_large_or_risky_for_batch` —
  `issues/defi_dexpool_second_writer_path_and_zero_capture_2026_07_10.md`, excluded entirely). Used a
  Workflow-orchestrated pipeline this time (per-doc conflict-resolution agents in parallel, one per doc with ≥1 eligible
  candidate, each independently checking its own doc's `conflicts_found` against
  `defi_consolidated_closeout_2026_07_18.md`'s + `defi_consolidated_closeout_aggregated_sources_2026_07_24.md`'s own
  claimed scope) rather than a single monolithic drafting agent, given the larger scale (39 docs vs cefi's 29). Result:
  **`defi_satellite_ao_dispatch_batch1_2026_07_25.md`** (defi's FIRST-EVER AO-dispatch batch — 53 todos from 59
  candidates, several same-file collisions merged per the prediction-batch1 precedent) + gated finalize companion. Only
  2 of 59 excluded outright + 1 landed in `needs_operator_ruling` (queued as entry 3 in
  `autonomous_session_operator_decisions_2026_07_25.md` — Kamino/Solend `lending_indices` `instrument_type` shape:
  writer code vs a live GCS probe disagree, not resolvable by clear logic/superseding alone). Validated
  (`check_frontmatter_schema.py`, `check_todo_format.sh` both clean; `check_line_caps.sh` shows a SOFT warning at 607
  lines — well under the 1000-line hard cap, no action needed) and folded into the same combined ship as the other 4
  AGs' work. **All 5 asset groups now have a drafted (status: draft, never auto-shipped active) AO-dispatch batch +
  gated finalize plan pair** — sports batch3, tradfi/prediction/cefi/defi batch1 (tradfi/prediction/cefi/defi all
  first-ever for their AG). Next: land the combined 25-file ship (in a multi-retry recovery cycle — see the dedicated
  entry below), then write the rule-9 closing report.

- **2026-07-25, the combined-ship recovery saga (17+ retries) — the REAL root cause, corrected**: shipping the 25-file
  combined commit (cefi/defi archivable_now resolutions + infra finalize backfill + all 5 AGs' new batch/finalize pairs)
  hit a long chain of failures. Several were genuine transients on this heavily-loaded shared host (`uptime` showed load
  average 7–14.5 on a 4-core box, 23 concurrent users), each diagnosed before retrying: (1)
  `check_finalize_plan_coverage.py` caught a real pre-existing gap (`infra_capture_and_devops_leftovers_2026_07_06.md`,
  predates the 2026-07-24 rule) — fixed with a real finalize-plan backfill, not a retry; (2)
  `test_build_index_is_deterministic` flaked from genuine concurrent doc-status mutation mid-test (known class,
  pre-filed issue doc); (3) a subprocess-probe test hit a 60s `pytest-timeout` under host CPU contention; (4) shared
  `.venv` transiently broke twice (`pandas`/`numpy.rec` partially-initialized-module errors from another process's
  concurrent dependency install, confirmed transient via direct `python3 -c "import X"` both times); (5) a shared
  `/home/ubuntu/.cache/qg-tmp/` scratch file vanished mid-run (another concurrent QG's cleanup); (6) the whole-suite
  wall-clock guard (600s) tripped once under load; (7) a `.git/index.lock` collision from a genuinely concurrent git
  process (waited, it cleared itself).

  **But the dominant, 100%-reproducible failure across ~10 consecutive retries — "⚠️ Path not found (and not tracked)" /
  "❌ No valid paths from --files. Nothing to commit." — was NOT a host-load race or a quickmerge.sh defect. It was my
  own invocation mistake**: `scripts/quickmerge.sh`'s STAGE 5 file-staging loop is
  `for f in $FILES_ARG; do [ -e "$f" ] && git add "$f" ...`, an UNQUOTED bash expansion that word-splits only on IFS
  whitespace — the script's own code comment even says so ("FILES_ARG is a space-separated path list", line ~1524). I
  had been passing **comma-separated** paths (`--files 'a.md,b.md,c.md'`) all session, which bash treats as ONE single
  token (no whitespace to split on) — so the loop ran exactly once with `f="a.md,b.md,c.md"` (the whole comma-joined
  string), `[ -e "$f" ]` correctly failed (no file has that literal name), and the error message printed exactly what
  was observed: every filename comma-joined into one blob. I initially misdiagnosed this as a `git stash pop` positional
  race (STAGE 5 also does `stash push -u` → checkout → `stash pop --quiet` around the same block, which looked plausible
  given the observed content-survives-but-doesn't-land pattern) and even drafted a "root-caused bug" writeup
  - a P2 follow-up todo for it — **both wrong, corrected here before shipping**. Proof: manually reproducing STAGE 5's
    exact stash push → fetch → checkout → stash pop sequence by hand succeeded cleanly (exit 0 at every step, content
    restored correctly) — the stash mechanism itself was never broken. Switching to **space-separated** `--files`
    (`--files 'a.md b.md c.md'`) fixed it on the very next attempt (`unified-trading-pm@ec5448ad3`, verified pushed to
    origin via `git merge-base --is-ancestor`). **Lesson, corrected**: `--files` (and
    `check_frontmatter_schema.py --files`, which has the identical trap — confirmed separately) both require
    SPACE-separated paths, not comma — CLAUDE.md's own example (`--files '<paths>'`) doesn't specify the delimiter,
    which is exactly how this drifted wrong all session. Worth a CLAUDE.md/task_template.md clarification as a cheap,
    high-value fix (see Todos) — no script change needed, this was never a code defect.

- **2026-07-25, batches shipped, verified pushed to origin**: split into 2 commits once the space-separated fix was
  found (smaller batches were already mid-flight when the fix landed; no need to recombine). **Batch A**
  (`unified-trading-pm@ec5448ad3`) — cefi/defi archivable_now resolutions (13 files). **Batch B**
  (`unified-trading-pm@62129d24f`) — the rollout plan + all 5 AGs' new batch/finalize pairs + the infra finalize-plan
  backfill (12 files), after 6 more branch-drift races (this branch's push velocity is genuinely very high right now —
  many concurrent AO worker slots landing every 1-2 min; each drift was independently verified to not touch any of my 12
  files before `git merge --ff-only`). Both commits confirmed
  `git merge-base --is-ancestor <sha> origin/live-defi-rollout` = true, and spot-checked content at HEAD for
  `defi_satellite_ao_dispatch_batch1` (53 todos), `cefi_satellite_ao_dispatch_batch1` (33 todos),
  `sports_satellite_ao_dispatch_batch3`, and `infra_capture_and_devops_leftovers_2026_07_06_finalize` — all correct.
  Also shipped a small P3 doc fix (`unified-trading-pm@62129d24f` folded it in): added the space-vs-comma `--files`
  clarification to `/codex/08-workflows/ci-cd-flow.md`'s Pass-2-quickmerge section (CLAUDE.md itself has ~1KB of
  headroom left under its hard byte cap — not touched, it already points readers to that codex doc as the quickmerge
  SSOT).

## Closing report (AUTONOMOUS_AGENT_RULES.md rule 9)

**All 5 asset groups got the full `/ag-closeout-audit` treatment this session** (sports had batch1/batch2 from before
this session; this session added batch3 for sports and the FIRST-EVER AO-dispatch batch for the other 4 AGs).

| AG         | Satellite docs orphaned | `archivable_now` found | `archivable_now` resolved                                            | New/latest AO batch | Batch todos (of N candidates)  |
| ---------- | ----------------------- | ---------------------- | -------------------------------------------------------------------- | ------------------- | ------------------------------ |
| sports     | 26 (of 72 primary)      | 2                      | 2 (archived)                                                         | batch3              | 12 (of 25)                     |
| cefi       | 29                      | 7                      | 5 (2 deferred — line-cap split needed; conflicting verdict on 1)     | batch1 (first-ever) | 33 (of ~40)                    |
| defi       | 39                      | 8                      | 7 (6 status-flipped not yet archived; 1 locked, queued for operator) | batch1 (first-ever) | 53 (of 59)                     |
| tradfi     | 21 (91% orphan rate)    | 1                      | 0 (correctly left open — stale verdict vs a live SIGKILL follow-up)  | batch1 (first-ever) | 5 (of 43)                      |
| prediction | 13                      | 0                      | n/a                                                                  | batch1 (first-ever) | 7 (of 9 in its one source doc) |

**Every new batch is `status: draft`** — none auto-dispatched to the AO fleet, per the operator's original instruction.
Each has a gated `_finalize_*.md` companion (`depends_on` + `gate_on_depends: true`) that will reconcile source-doc
checkboxes and run the archival ritual once the batch's own todos land. Every conflict-gated candidate across all 5 AGs
(200+ total, tallied loosely across sports 23 + cefi ~2 + defi ~2+1-ruling + tradfi 38 + prediction 2) is preserved in
its plan's own Deferred section with a stated reason — none silently dropped.

**Operator-decisions queue** (`issues/autonomous_session_operator_decisions_2026_07_25.md`) — 3 entries, all still
`open`, per the operator's explicit instruction to queue rather than auto-decide:

1. `git rm` 2 stale-duplicate stub files (sports archival half-landed-rename cleanup).
2. `gas_fees_lst_rates_manifest_bucket_mismatch_2026_07_10.md` — locked doc (`locked_by: live-defi-rollout`), audit says
   resolved, needs an `[unlock-plan]` + flip decision.
3. Kamino/Solend `lending_indices` `instrument_type` shape — writer code vs a live GCS probe disagree (defi batch1's one
   genuinely-ambiguous conflict).

**Not this session's queue, but relayed directly since the operator asked mid-session**: the
`sports_day_all_teams_venues_fold_key_scheme_mismatch_2026_07_25.md` question (from
`sports_satellite_ao_dispatch_batch2`, a different, already-in-flight batch, not one this session drafted) — gave full
GCS-path context + verification commands in chat; still awaiting the operator's actual A/B/C choice.

**Real bugs/findings surfaced and handled**:

- A genuine data-integrity bug (half-landed archival rename from concurrent branch writes) — root-caused and fully
  remediated early in the session.
- `infra_capture_and_devops_leftovers_2026_07_06.md`'s missing finalize-plan-coverage gap — backfilled with a real
  finalize plan, not worked around.
- The `--files` comma-vs-space invocation trap — root-caused (after an initial wrong theory, corrected in-place before
  it shipped anywhere) and documented in the actual SSOT.
- `issues/test_build_index_deterministic_races_on_concurrent_corpus_writes_2026_07_25.md` — filed earlier this session,
  re-confirmed transient (not caused by this session's changes) every time it recurred.

**Verified end-state**: `git status --porcelain` clean, `git rev-list --count origin/live-defi-rollout..HEAD` = 0 (both
ship commits confirmed ancestors of origin). No uncommitted work. Loop ends here — success criteria (all 5 AGs audited,
every AO-eligible orphaned doc either dispatched via a new conflict-checked batch or explicitly deferred with a reason,
every genuine operator-decision-caliber question queued not silently decided) are met.
