---
doc_type: issue
title: "plan_reconciler full-corpus deep reconciliation run — all tranches, 2026-08-12"
summary: >-
  Run-findings doc for an interactive, operator-directed /plan-reconcile "all" (unsharded) run, 2026-08-12. Corpus: 774
  docs (278 active plans + 468 issue docs + 28 epics). Fanned out 46 size-balanced read-only hunter batches (~700KB
  each, partitioned by parent_epic) covering every doc in full, surfaced 121 contradictions (6 P0 / 37 P1 / 52 P2 / 26
  P3), 18 done-but-unchecked candidates, 25 zero-checkbox docs, 56 AO-dispatch-readiness findings, and 16 codex-drift
  findings. All 6 P0s + 37 P1s were individually adversarially verified (several turned out to be false alarms from
  races with concurrent sessions on the shared corpus, or correctly-tracked deferrals — noted where relevant) and either
  auto-fixed directly in the source docs or routed to the operator for a ruling (4 genuine judgment calls, resolved
  interactively). This doc tracks what that pass did NOT individually resolve: lower-confidence done-but-unchecked
  candidates needing a fresh re-check, zero-checkbox docs needing conversion/archival, and the full P2/P3 contradiction
  + AO-readiness + codex-drift backlog, so nothing found by the 46 hunters is silently dropped.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan_reconciler, reconciliation, plan-hygiene, findings, all-tranches]
related:
  [
    /plans/archive/2026_08/issues/plan_reconciler_findings_defi_2026_08_09.md,
    /plans/archive/2026_08/issues/plan_reconciler_findings_ci_2026_08_09.md,
    /plans/archive/2026_08/issues/plan_reconciler_findings_cefi_2026_08_09.md,
    /plans/archive/2026_08/issues/plan_reconciler_findings_cross_cutting_2026_08_09.md,
  ]
created: "2026-08-12"
parent_epic: plan_hygiene_master
priority: P2
estimate_class: research
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.8
assigned_role: review
assigned_vm: NA
execution_scope: local-only
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: "Interactive session, operator-directed full-corpus /plan-reconcile run, 2026-08-12."
context_scope:
  [
    unified-trading-pm/scripts/plan-hygiene/run_hygiene_sweep.sh,
    unified-trading-pm/cursor-configs/skills/plan-reconcile/SKILL.md,
  ]
drift_direction: advance-code
depends_on: []
---

# plan_reconciler run — 2026-08-12 (interactive, full corpus)

## What was already fixed directly in this pass (not tracked here again)

All 6 P0 and 37 P1 contradictions were individually verified and resolved in-place in their source docs (dated
`CORRECTED 2026-08-12 (/plan-reconcile)` banners/annotations), plus 4 operator-ruled judgment calls (2 confirmed "RULED"
statuses, 1 account-identity correction, 1 VM-dispatch `depends_on` gate) and ~10 clean HARD-evidence done-but-unchecked
flips. Two archival-eligible docs were unblocked and archived (`infra_satellite_ao_dispatch_batch13` pair,
`glue_pool_starvation_monitor_stale_jobs_after_runner_revert_2026_08_07.md` — the last one after disproving a false
line-cap-deadlock premise blocking it). See `git log` on this date for the individual commits. Two flagged
mechanism-level bugs are worth operator attention beyond doc fixes: the AO orchestrator's `auto_park.manual_park`
idempotency guard silently no-ops re-park attempts (observed 4x/26x redundant re-dispatch on two sports docs), and
`SUB_AGENT_MANDATORY_RULES.md` is at 10228/10240 bytes — 12 bytes from its hard QG cap.

## Section 1 — done-but-unchecked candidates needing a fresh re-check (not flipped — evidence was ambiguous/partial)

- [ ] [REVIEW] P2. `plans/active/issues/ao_non_dispatchable_regex_swallows_resolved_retags_2026_07_29.md` todo 1 — the
      doc's own Progress Log shows a real commit (`unified-trading-pm@6edd4486a`) rephrased 24 mentions across 15 files,
      but the todo's stated scope is "the full 27/21-file list" — re-run the corpus-wide script the todo cites to
      confirm the remaining 3 files, then flip with the precise citation.
- [ ] [REVIEW] P2. `plans/active/issues/tradfi_live_shard_atom_unknown_writer_2026_08_09.md` todo — equivalent evidence
      exists in `tradfi_satellite_ao_dispatch_batch11_2026_08_10.md` (still `status: draft`, not yet ingested) — do NOT
      flip until batch11 is dispatched/verified; re-check batch11's status first. Also note: batch11's own evidence
      citations for 2-3 adjacent todos use the literal unresolved placeholder `unified-trading-pm@<sha>` instead of a
      real commit sha — needs a real citation before anything downstream trusts it.
- [ ] [REVIEW] P1. `plans/active/issues/sports_af_full_entity_completion_2026_08_03.md` — HARD evidence (VM run.log,
      exit_code=0, repeat-stable census) exists for 6 of 8 named entities; run the final unified re-census + notify +
      close per `sports_all_vendor_honest_coverage_convergence_2026_08_07.md`'s convergence evidence.
- [ ] [REVIEW] P2. `plans/active/sports_track_h_denominator_prereqs_2026_07_28.md` todo 2 (batch_footystats copy+swap) —
      the PROD data-correctness work is done+verified (fresh live manifest census cited), but the code commit is blocked
      on an unrelated repo QG gate. Re-check market-tick-data-service QG state; if green, commit + flip.
- [ ] [REVIEW] P2. `plans/active/issues/tradfi_mvp_of_mvp_instrument_scope_ruling_2026_08_09.md` todo — part 1 of its
      2-part done-when (confirm `wave_launcher.py`'s actual mechanism) is answered by
      `tradfi_scope_ruling_possible_violation_legacy_fleet_relaunched_2026_08_09.md` (GCP Cloud Scheduler → Cloud Run
      Job, not a host cron, per Terraform + live verification) — NOTE this directly contradicts the P0 finding already
      fixed in `tradfi_backfill_oom_remediation_2026_06_24.md` this same run, which found the opposite (an undocumented
      host cron). Both cite live evidence from different dates — reconcile which is current before relying on either.
      Part 2 (whether `deployment-service@bcf55c781`'s fix was actually redeployed to the Cloud Run Job image) is
      unaddressed by either doc — track separately.
- [ ] [REVIEW] P2. `plans/active/issues/cefi_onchain_perp_batch_venue_allowlist_gap_2026_07_12.md` — a doc's 2026-08-08
      Progress Log promises imminent archival of an all-`[x]`, unlocked doc still sitting in `plans/active/issues/` as
      of this run — check current state and archive if still eligible.

## Section 2 — zero-checkbox docs (need conversion to tracked todos, or archival)

- [ ] [DOC] P2. `plans/active/issues/dp_exit_code_monitor_sweep_overlap_storm_2026_08_10.md` — genuine unresolved
      structural bug (exit-code-monitor `sweep()` takes >30min sequentially while cron fires every 5min, causing 4-6
      overlapping runs). Add: parallelize per-VM GCS reads in `exit_code_fleet_monitor.py` +
      `heartbeat_stall_watcher.py`'s `sweep()` via `ThreadPoolExecutor` (precedent in `cli.py`).
- [ ] [DOC] P3. `plans/active/issues/plan_reconciler_findings_ui_2026_08_11.md` — add: expand the ui-tranche doc
      inventory to include multiline-frontmatter `asset_group:\n  [ui]` docs missed by same-line grep.
- [ ] [OPERATOR] P2. `plans/active/issues/ci_escalation_no_coverage_for_local_ratchet_gate_breaches_2026_08_10.md` —
      decide the resolution path for the local-quality-gate-breach escalation coverage gap (fleet-wide detector +
      escalation wall type, vs accept as a known gap).
- [ ] [DATA] P2. `plans/active/issues/dp_vm_002_mdps_cefi_2021_silent_zero_false_positive_2026_08_11.md` — re-launch the
      `mdps-cefi-2021-*` sharded backfill (resume from checkpoint, prior run killed mid-2021-01-04).
- [ ] [OPERATOR] P3. `plans/active/issues/tradfi_smoke_290d_window_data_gap_2026_08_11.md` — decide tradfi 290-day
      honest-coverage strategy (3 options stated in doc, recommendation: accept INSUFFICIENT until tracked backfill
      lands).
- [ ] [OPERATOR] P2. `plans/active/issues/execution_service_ldr_provenance_bypass_backlog_2026_08_10.md` — choose
      resolution path for execution-service's 7 LDR quickmerge-provenance bypasses before the next promote PR.
- [ ] [CODE] P1. `plans/active/issues/mtds_pipeline_check_enumerate_shards_masks_cefi_sports_mvp_2026_08_06.md` — add
      `_CEFI_MVP_SHARDS`/SPORTS-equivalent override to `pipeline_e2e_check.py`'s `_venue_data_type_is_mvp()` (this doc
      is `assigned_vm: planning` with nothing dispatchable as authored — AO-readiness gap too).
- [ ] [DATA] P2. `plans/active/issues/features_sports_compute_features_hard_fail_missing_upstream_today_2026_08_10.md` —
      once instruments-service writes real 2026-08-10 sports_reference data, `--force` recompute the sports features
      backfill for day=2026-08-10 to replace false `empty_confirmed` rows.
- [ ] [CONFIG] P2. `plans/active/issues/sports_features_2026_backfill_launch_window_was_today_2026_08_10.md` — clamp the
      per-year sports features backfill launcher's `end_date = min(today-1, {year}-12-31)` for the current year.
- [ ] [OPERATOR] P2. `plans/active/issues/ag_closeout_audit_tradfi_parked_2026_08_10.md` — flip
      `tradfi_satellite_ao_dispatch_batch11_2026_08_10.md` and `...batch12_2026_08_10.md` from `draft`→`active`
      (unblocks 4 docs + 8 open todos) — cross-check against Section 1's wave_launcher-mechanism reconciliation first.
- [ ] [REVIEW] P2. `plans/active/issues/plan_reconciler_findings_defi_2026_08_09.md`,
      `.../plan_reconciler_findings_cefi_2026_08_09.md`, `.../plan_reconciler_findings_ci_2026_08_09.md`,
      `.../plan_reconciler_findings_cross_cutting_2026_08_09.md` — 4 stalled/incomplete plan_reconciler run journals,
      `locked_by: plan_reconciler` since 2026-08-09 (~3 days old at time of this run). Confirm each dispatch is
      genuinely dead (not a live session), then release the lock and either re-dispatch a fresh tranche run or archive
      as an aborted attempt.
- [ ] [DOC] P1. `plans/active/issues/deployment_service_qg_red_11_actuator_tests_suite_order_regression_2026_08_10.md` —
      already given a real tracked todo directly in this pass (was P1 FLEET-BLOCKING with zero todos); listed here only
      as a pointer since it's the highest-severity zero-checkbox finding from this run.
- [ ] [REVIEW] P3. `plans/active/issues/_agent_pings.md` — explicit tombstone (RETIRED 2026-07-04), archive candidate.
- [ ] [REVIEW] P3. `plans/active/issues/ag_closeout_audit_prediction_parked_2026_08_10.md` — completed audit-run record,
      archive candidate.
- [ ] [REVIEW] P3.
      `plans/active/issues/sports_api_football_live_odds_second_source_conflicts_with_wipe_ruling_2026_08_02.md` — doc's
      own resolution section says both open questions already resolved; flip `status: resolved` + archive.
- [ ] [REVIEW] P3. `plans/active/issues/instruments_service_sports_footystats_uac_overlap_qg_red_2026_07_30.md` —
      tension noted: superseded + zero real work but deliberately kept unarchived "for the corpus trail" — confirm
      that's still the intended disposition or archive.

## Section 3 — full P2/P3 backlog from this run (compact log, one line each)

Format: `- [ ] [REVIEW] P3. (severity/class) doc — one-line gist`. These were surfaced by the 46 hunter batches but not
individually resolved in this pass (lower severity, high volume — ~150 items). A future `/plan-reconcile` pass (sharded
or full) should triage these; most are cosmetic/stale-ref/index-drift class, not live-work-misrouting risks.

- [ ] [REVIEW] P3. (P2) plans/active/ag_closeout_audit_rollout_2026_07_25.md:114-118 — sole open todo framed as "finish
      the mass-flip" but 2 audit markers call that framing stale
- [ ] [REVIEW] P3. (P2)
      plans/active/issues/escalation_queue_reconciler_false_resolution_via_unrelated_qg_green_2026_08_09.md:136 — a
      Todos bullet has no checkbox marker at all, unlike its 3 siblings
- [ ] [REVIEW] P3. (P3) agent_operating_framework_master_batch2 manifest entries 14/18 — 404, archived before manifest
      generated (index drift)
- [ ] [REVIEW] P3. (P2) plans/active/ao_satellite_ao_dispatch_batch11_2026_08_09.md:16 — frontmatter says
      active/planning, todo already [x] — cosmetic
- [ ] [REVIEW] P3. (P2) plans/active/citadel_paper_batch_live_reconciliation_2026_06_19.md:145-146 — register claims 3
      open checkboxes but body describes a 4th unmigrated item with no checkbox syntax
- [ ] [REVIEW] P3. (P3) plans/active/issues/batch_live_reconciliation_service_audit_2026_05_27.md:386-600 — G3 status
      predates a later operator ruling, no cross-ref
- [ ] [REVIEW] P3. (P3) plans/active/issues/live_pipeline_persistence_hot_path_decoupling_2026_06_24.md:13-16 — fragile
      YAML status split across scalar+comment lines
- [ ] [REVIEW] P3. (P2) plans/active/issues/cefi_onchain_perp_batch_venue_allowlist_gap_2026_07_12.md:526-531 — see
      Section 1 item on this doc
- [ ] [REVIEW] P3. (P3)
      plans/active/issues/cefi_content_migration_corpus_still_incomplete_relaunch_round3_needed_2026_07_31.md:3-5 —
      title staleness
- [ ] [REVIEW] P3. (P3) plans/active/cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md:30 — stale cross-ref
- [ ] [REVIEW] P3. (P2)
      plans/active/issues/cefi_enumeration_audit_instrument_type_leakage_and_catalogue_orphans_2026_07_27.md —
      round5/round7/batch10 disagree on operator-gated status
- [ ] [REVIEW] P3. (P2) plans/active/cefi_consolidated_closeout_aggregated_sources_2026_07_24.md — stale
      aggregated-sources digest entry
- [ ] [REVIEW] P3. (P2) plans/active/issues/cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md — stale
      `depends_on` gate pointing at a now-completed blocker
- [ ] [REVIEW] P3. (P2) plans/active/issues/mdps_multi_instrument_bundle_write_race_hypothesis_2026_08_09.md:4-5 — title
      still frames a hypothesis the doc's own body refuted
- [ ] [REVIEW] P3. (P2) plans/active/issues/okx_futures_instid_marker_convention_mismatch_2026_07_30.md:166 — tag/prose
      mismatch ([DATA] P1 vs "tagging [OPERATOR] until decided")
- [ ] [REVIEW] P3. (P3) plans/active/issues/upbit_cefi_data_gap_may_2026_2026_08_04.md:1-34 — missing required `status:`
      frontmatter key
- [ ] [REVIEW] P3. (P2) plans/active/issues/elysium_sla_v4_support_period_and_stale_dates_2026_08_08.md — duplicate
      SLA-reissue decision tracked in two docs with different owners/priorities
- [ ] [REVIEW] P3. (P3) plans/active/issues/elysium_sla_v4_support_period_and_stale_dates_2026_08_08.md — frontmatter
      last_updated stale
- [ ] [REVIEW] P3. (P3) plans/active/elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md — frontmatter
      last_updated stale
- [ ] [REVIEW] P3. (P2) plans/active/issues/defi_mdps_candle_backfill_fleet_outcome_2026_08_06.md — MDPS timeout todo
      duplicate-tracked in 2 docs
- [ ] [REVIEW] P3. (P2) plans/active/defi_satellite_ao_dispatch_batch3_2026_07_26_finalize.md — frontmatter/body status
      self-contradiction
- [ ] [REVIEW] P3. (P2) plans/active/defi_satellite_ao_dispatch_batch6_2026_07_30_finalize.md — frontmatter/body status
      self-contradiction
- [ ] [REVIEW] P3. (P2) plans/active/defi_pipeline_e2e_and_coverage_validation_2026_06_20_finalize_2026_07_27.md —
      frontmatter/body status self-contradiction
- [ ] [REVIEW] P3. (P2) plans/active/issues/plan_reconciler_findings_2026_08_07.md:73-75 — falsely attributes a
      shipped-commit citation to a different, unshipped todo
- [ ] [REVIEW] P3. (P3) plans/active/github_actions_operator_gated_followups_2026_07_17.md:244 — "still unfixed"
      present-tense claim contradicted by its own SSOT doc (3-of-4 fixes shipped)
- [ ] [REVIEW] P3. (P2) plans/active/blocked_question_payload_quality_and_condition_retirement_2026_08_10.md:16 —
      frontmatter status:active vs all-todos-done body
- [ ] [REVIEW] P3. (P3) plans/active/blocked_question_card_context_rendering_2026_08_10.md:29 — frontmatter last_updated
      stale by 1 day
- [ ] [REVIEW] P3. (P2) plans/active/features_service_e2e_pipeline_test_2026_05_26.md — frontmatter last_updated stale;
      "2 genuinely open items" claim off by 1
- [ ] [REVIEW] P3. (P2) plans/active/colocated_feature_pipeline_in_memory_handoff_2026_06_21.md — cites 2 items as
      "still open" that the referenced gate doc shows resolved; also a rotted "574 errors" basedpyright target
- [ ] [REVIEW] P3. (P2) plans/active/infra_satellite_ao_dispatch_batch12_finalize_2026_08_09.md — real archival +
      literal `unified-trading-pm@SHA_PLACEHOLDER` evidence citation (fix the citation, not the archival)
- [ ] [REVIEW] P3. (P2) plans/active/lst_rate_honest_coverage_2026_07_21.md — Phase-1 todo checked done, body says the
      infra regen run is still open
- [ ] [REVIEW] P3. (P2) plans/active/issues/orchestrator_vm_disk_io_contention_runner_burst_2026_07_28.md — proposes a
      fix already investigated + differently resolved by the pytest-timeout doc-chain
- [ ] [REVIEW] P3. (P3) plans/active/issues/cve_affected_pinned_deps_remediation_2026_06_18.md — frontmatter `repos:`
      list stale against body (~22 repos actually touched)
- [ ] [REVIEW] P3. (P2) plans/active/issues/pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md:634-638 —
      Deferred-work table lists 2 items as unresolved that later Todos/Progress-Log entries close
- [ ] [REVIEW] P3. (P3) plans/active/codex_violations_ratchet_to_five_2026_06_10.md:26 — stale
      `locked_by: live-defi-rollout` despite a documented operator unlock over a month prior
- [ ] [REVIEW] P3. (P3) plans/active/issues/cefi_fwd_backfill_vm_deleted_by_sa_within_10min_2026_08_08.md:17 — "2nd" vs
      "3rd" consecutive-VM count mismatch within the same doc
- [ ] [REVIEW] P3. (P2) plans/active/issues/uac_value_only_config_change_breaks_utl_untested_2026_07_20.md:444 —
      disagrees with a sibling doc on whether the corpus-wide `locked_by: live-defi-rollout` placeholder is benign or a
      bug
- [ ] [REVIEW] P3. (P3) plans/active/fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md:422 — stale
      "needs todo 9's update" Codex-SSOTs line, todo 9 already done
- [ ] [REVIEW] P3. (P2) plans/active/issues/features_service_coverage_and_script_canon_2026_06_10.md —
      `locked_by: live-defi-rollout` placeholder-lock corpus-wide bug instance
- [ ] [REVIEW] P3. (P3) plans/active/repo_scripts_governance_audit_2026_06_18.md — same placeholder-lock bug instance
- [ ] [REVIEW] P3. (P2) plans/active/ci_pipeline_speed_and_cost_redesign_2026_08_05.md — headline "beaten by 10-50x"
      contradicted by its own admitted ~7.5min pre-PR latency
- [ ] [REVIEW] P3. (P2) plans/active/issues/tier_a_ci_status_gate_unrecoverable_deadlock_2026_08_09.md — audit entry
      says "both open todos" but only 1 is actually unchecked
- [ ] [REVIEW] P3. (P2)
      plans/active/issues/gcp_service_accounts_registry_diverged_from_live_provisioning_2026_07_31.md:116-118 —
      "DEFAULT-RULED" label presents an undecided design call as settled
- [ ] [REVIEW] P3. (P3) plans/active/issues/defi_bridge_events_historical_backfill_gap_2026_07_28.md:134 — checkbox [x]
      vs body text "Still open"/"Left `- [ ]`" (later Progress Log resolved for real)
- [ ] [REVIEW] P3. (P3) plans/active/issues/solana_dex_pool_swaps_indexer_002_repeat_wedge_parked_2026_08_08.md:96-100 —
      self-defeating "unpark is moot" vs "once unparked, verify" todo pairing
- [ ] [REVIEW] P3. (P2)
      plans/active/issues/cloud_build_failure_watcher_limit_30_coverage_gap_silently_drops_failures_under_load_2026_08_10.md:43
      — checked-done todo, `resolved_by` is an unfilled template placeholder
- [ ] [REVIEW] P3. (P3) plans/active/defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md — frontmatter
      last_updated stale
- [ ] [REVIEW] P3. (P2) plans/active/issues/cross_cutting_manifest_canonicalisation_findings_2026_07_11.md —
      "RESUME-runbook readiness" section stale since 2026-07-14, runbook was actually executed 2026-07-16
- [ ] [REVIEW] P3. (P2) plans/active/issues/cefi_hl_aster_batch_data_gaps_2026_06_22.md:384-391 — 2 docs describe what
      looks like the same EXTENDED-STARKNET backfill without cross-referencing
- [ ] [REVIEW] P3. (P3) plans/active/data_completion_to_100_all_ag_2026_06_21.md:61-66 — self-removal-instruction banner
      still present after its own stated removal condition
- [ ] [REVIEW] P3. (P3) plans/active/pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md:27-28 —
      inconsistent execution_scope pairing with assigned_vm:NA vs corpus convention
- [ ] [REVIEW] P3. (P2) plans/active/issues/solana_dex_pool_swaps_indexer_scope_2026_07_12.md — presents
      `build_drift_v2_sig_index.py` as a live precedent script; it was deleted 2026-07-16 (fixed content-wise by another
      doc, cross-ref not added here)
- [ ] [REVIEW] P3. (P2) plans/active/deployment_registry_firestore_p3_cutover_2026_07_14.md — model_tier corrected to
      sonnet 2026-08-10, overview doc's phase-index table not updated
- [ ] [REVIEW] P3. (P2) plans/active/deployment_registry_firestore_migration_2026_07_14.md — overview table still lists
      P3 as "Opus/high", propagating the same stale claim
- [ ] [REVIEW] P3. (P3) plans/active/deepseek_claude_blended_provider_routing_2026_07_28.md — bogus lock predates doc
      creation
- [ ] [REVIEW] P3. (P2) plans/active/ao_satellite_ao_dispatch_batch6_2026_08_04.md — Deferred section claims a doc is
      still operator-gated; its own finalize twin shows it was reclassified NA→planning the same day, self-flagged but
      never corrected
- [ ] [REVIEW] P3. (P3) plans/archive/2026_08/issues/ao_park_disposition_blocked_answer_no_follow_through_2026_07_31.md
      — `locked_since` predates `created` by 2 months (impossible); `locked_by` is a branch name, not an owner
- [ ] [REVIEW] P3. (P2) plans/active/codex_vs_repo_docs_ssot_audit_2026_06_01.md:87,96 — Phase-3 checkbox still asserts
      an opus-gating requirement the doc's own later section already retired
- [ ] [REVIEW] P3. (P2) plans/active/issues/over_cap_live_plan_is_permanently_unverdictable_2026_08_02.md:131-138 — todo
      2 checked "Implemented" citing a literal unresolved `<sha>` placeholder
- [ ] [REVIEW] P3. (P2) plans/active/prediction_consolidated_closeout_2026_07_18.md:183,186 — closeout ground-truth
      stale vs phase children
- [ ] [REVIEW] P3. (P3) plans/active/issues/ag_closeout_audit_prediction_parked_2026_08_10.md:66 — self-contradiction re
      batch10
- [ ] [REVIEW] P3. (P2) plans/active/sports_consolidated_native_ao_extract_2026_07_25.md:15,49 — frontmatter
      status:active vs body draft banner
- [ ] [REVIEW] P3. (P2) plans/active/sports_satellite_ao_dispatch_batch5_2026_07_26.md:84 — banner says 2 open todos,
      both now [x]
- [ ] [REVIEW] P3. (P2) plans/active/issues/sports_manifest_consolidator_zero_growth_stall_2026_07_29.md:478-482 —
      orphaned prose Follow-up now correctly tracked elsewhere, source doc not updated
- [ ] [REVIEW] P3. (P2) plans/active/issues/sports_index_recency_masked_captured_atoms_2026_07_13.md — all checkboxes
      [x], frontmatter status stale (self-flagged 2026-08-06, never fixed)
- [ ] [REVIEW] P3. (P3) plans/active/issues/mdps_odds_horizon_bucket_shard4_residual_failures_2026_07_25.md — stale
      annotation claims a followup "is not tracked as a todo" directly beneath the todo tracking it
- [ ] [REVIEW] P3. (P2) plans/archive/2026_08/issues/sfi_progressive_stats_json_truncation_2026_08_09.md — frontmatter
      status:open vs body all-[x]-done + resolved_by empty
- [ ] [REVIEW] P3. (P2) plans/active/sports_satellite_ao_dispatch_batch10_2026_08_06_finalize.md — Progress Log claims a
      codex path "does not resolve" for a path confirmed to exist
- [ ] [REVIEW] P3. (P3) plans/active/crypto_alpha_research_2026_07_24.md:103-107 — §C claims a permanent
      BLOCKED-OPERATOR-DECISION tag not actually present on the checkboxes (assigned_vm: NA, low impact)
- [ ] [REVIEW] P3. (P2) plans/active/strategy_archetype_latency_deployment_profile_audit_2026_08_10.md — cites
      "execution plan todo 6" for a gap now covered by the new todo added this run (renumber if needed)
- [ ] [REVIEW] P3. (P2) plans/active/tradfi_registry_coverage_and_ao_readiness_2026_07_25.md — 3 stale-verify
      sub-findings (CME billing, KRX, adapter smoke) — re-verify against current state
- [ ] [REVIEW] P3. (P2) plans/active/tradfi_manifest_content_recovery_completion_2026_07_24_finalize_2026_07_27.md:12 —
      minor drift, unspecified
- [ ] [REVIEW] P3. (ao-readiness, several) — see raw hunter output for: autonomous_session_operator_decisions,
      ao_satellite batch13/17 finalize twins, meta_plan_corpus_hygiene batch1 finalize, reference_path_convention
      finalize, doc_body_link_checker finalize, one_shot_complete_session finalize,
      sub_agent_mandatory_rules_size_warn_headroom, ao_satellite batch11/17 — mostly "nothing dispatchable as authored"
      or missing definition-of-done on already-narrow todos, low severity
- [ ] [REVIEW] P3. (ao-readiness) plans/active/issues/mdps_force_flag_dropped_subprocess_per_date_2026_08_08.md:116-120
      — VM-launch todo untagged `[OPERATOR]`, no inline safe-idempotent justification
- [ ] [REVIEW] P3. (ao-readiness) plans/active/defi_satellite_ao_dispatch_batch6_2026_07_30.md:453 — manifest-row
      DELETE + index rebuild todo, cites an operator ruling but not inline
- [ ] [DOC] P3. (codex-drift) plans/active/defi_consolidated_closeout_2026_07_18.md:260 — flags 2 codex docs as stale on
      venue-vs-chain segment order, unresolved 3+ weeks, no tracked follow-up
- [ ] [REVIEW] P3. (ao-readiness) plans/active/issues/defi_mdps_candle_backfill_fleet_outcome_2026_08_06.md — missing
      definition-of-done
- [ ] [REVIEW] P3. (ao-readiness) plans/active/issues/deployment_ui_capability_bundle_stale_drift_pacifica_2026_07_16.md
      — instruction not on todo's first physical line
- [ ] [DOC] P3. (codex-drift)
      plans/active/blocked_question_payload_quality_and_condition_retirement_2026_08_10.md:186-188 — self-imposed
      follow-up written as prose in "Codex SSOTs" section, not a tracked todo
- [ ] [DOC] P3. (codex-drift) plans/active/issues/dependency_health_alerting_never_wired_2026_08_12.md —
      `/codex/04-architecture/dependency-health-policy.md` reads as though DEPENDENCY_DEGRADED alerting is live; no
      producer/consumer exists anywhere in the fleet (self-tracked already in that doc)
- [ ] [REVIEW] P3. (ao-readiness) plans/active/issues/cve_affected_pinned_deps_remediation_2026_06_18.md — missing
      definition-of-done, inherently unbounded scope for an AO-dispatched todo
- [ ] [REVIEW] P3. (ao-readiness) plans/active/data_pipeline_check_mdps_features_2026_07_20.md — P0 todo has only a
      prose gate condition, no depends_on/gate_on_depends enforcement — risk of dispatch into a known-blocked wall
- [ ] [DOC] P3. (codex-drift) plans/active/bucket_iam_write_protection_per_tier_2026_06_09.md — uncertain whether codex
      §4 correction (vs the shipped §8 fix) landed
- [ ] [REVIEW] P3. (ao-readiness) plans/active/defi_compute_gcp_migration_2026_08_08.md — destructive AWS ECS-cluster
      delete todo, no `[OPERATOR]` tag
- [ ] [REVIEW] P3. (ao-readiness) plans/active/issues/cefi_fwd_backfill_vm_deleted_by_sa_within_10min_2026_08_08.md —
      VM-launch todo tagged `[INFRA]` not `[OPERATOR]`
- [ ] [REVIEW] P3. (ao-readiness) plans/active/issues/cf_manifest_audit_first_full_rollup_findings_2026_07_26.md — live
      production manifest rewrite on a twice-regressed sports surface, no `[OPERATOR]` tag
- [ ] [REVIEW] P3. (ao-readiness)
      plans/active/issues/defi_oracle_family_empty_path_exception_classification_2026_08_09.md — `assigned_vm: planning`
      doc's only open todo tagged `[LOCAL]`
- [ ] [REVIEW] P3. (ao-readiness) plans/active/issues/vm_launcher_setup_script_freshness_gap_2026_07_31.md — asks worker
      to "author a dedicated migration plan" (judgment call, not bounded AO work)
- [ ] [DOC] P3. (codex-drift) plans/active/issues/recon_bucket_missing_nightly_recon_failing_2026_07_13.md — codex SSOT
      lists `features-onchain` as a DAG producer, live Terraform service map lacks that key
- [ ] [REVIEW] P3. (ao-readiness) plans/active/issues/lighter_tardis_writerless_route_hang_2026_07_28.md — AO-dispatched
      but explicitly needs a human design decision among 3 options
- [ ] [DOC] P3. (codex-drift) plans/active/issues/claude_settings_symlink_writeback_drops_hooks_2026_08_11.md — already
      self-tracked
- [ ] [REVIEW] P3. (ao-readiness)
      plans/active/issues/mtds_pipeline_check_enumerate_shards_masks_cefi_sports_mvp_2026_08_06.md — see Section 2
- [ ] [REVIEW] P3. (ao-readiness)
      plans/active/issues/dp_vm_002_detector_generic_alert_text_and_bucket_kind_blindness_2026_08_09.md — low severity
- [ ] [DOC] P3. (codex-drift)
      plans/active/issues/strategy_service_ldr_tip_fails_own_quality_gate_blocks_all_commits_2026_08_10.md — unspecified
      drift
- [ ] [DOC] P3. (codex-drift) plans/active/issues/order_state_machine_ssot_vs_uac_orderstatus_2026_07_31.md —
      9-state-vs-7-state enum mismatch, unresolved (related to the P1 fixed this run)
- [ ] [REVIEW] P3. (ao-readiness) plans/active/issues/defi_manifest_venue_itype_canon_swap_execution_2026_08_10.md —
      133M-row manifest prod-write todo tagged `[SCRIPT]` not `[OPERATOR]` (has substantial safety machinery, likely low
      risk)
- [ ] [REVIEW] P3. (ao-readiness) plans/active/issues/defi_pool_uppercase_recurrence_after_fold_2026_08_11.md — see
      Section 2 (zero-checkbox)
- [ ] [REVIEW] P3. (ao-readiness) plans/active/issues/cefi_hl_aster_batch_data_gaps_2026_06_22.md — VM-launch todo, no
      `[OPERATOR]` tag, no inline idempotency statement
- [ ] [REVIEW] P3. (ao-readiness) plans/active/solana_dex_pool_swaps_indexer_2026_08_08.md — low severity
- [ ] [DOC] P3. (codex-drift) plans/active/issues/_cefi_canonical_blueprint_2026_07_17.md — no evidence the Phase-2
      codex correction on filename-stem contract ever shipped
- [ ] [REVIEW] P3. (ao-readiness) plans/active/issues/tradfi_live_shard_atom_unknown_writer_2026_08_09.md — see Section
      1
- [ ] [OPERATOR] P2. plans/active/issues/ao_scheduled_job_reserve_and_staggering_2026_08_04.md — a sibling `sudo`
      instruction issue already fixed this run; the doc's claim that the codex SSOT was updated to remove the sudo HARD
      RULE should be re-verified against live CLAUDE.md
- [ ] [REVIEW] P3. (ao-readiness) plans/active/ao_satellite_ao_dispatch_batch14_finalize_2026_08_09.md — low severity
- [ ] [DOC] P3. (codex-drift) plans/active/ao_satellite_ao_dispatch_batch7_finalize_2026_08_06.md — codex-alignment fix
      claimed complete, partially true per a sibling doc — low severity, historical
- [ ] [REVIEW] P3. (ao-readiness) plans/active/issues/duplicate_finalize_plans_created_for_one_parent_2026_08_06.md — 3
      open todos lack an explicit "Done when" clause
- [ ] [REVIEW] P3. (ao-readiness) plans/active/codex_vs_repo_docs_ssot_audit_2026_06_01.md:790-808 — per-repo rollout
      item, ibkr-gateway-infra, low severity
- [ ] [REVIEW] P3. (ao-readiness) plans/active/prediction_satellite_ao_dispatch_batch6_2026_07_29.md:544-558 — low
      severity
- [ ] [DOC] P3. (codex-drift) plans/active/predictions_ml_walk_forward_and_arb_2026_06_20.md:150 — low severity
- [ ] [REVIEW] P3. (ao-readiness) plans/active/issues/sports_af_full_entity_completion_2026_08_03.md — see Section 1
- [ ] [REVIEW] P3. (ao-readiness) plans/active/sports_taxonomy_p3_consumers_2026_08_08.md — auto_park idempotency
      mechanism finding, see "already fixed" section above for the fleet-wide flag
- [ ] [REVIEW] P3. (ao-readiness)
      plans/active/issues/sports_stats_delayed_live_capture_still_dead_post_fix_2026_07_29.md — low severity
- [ ] [REVIEW] P3. (ao-readiness) plans/active/sports_closeout_track_s2_foldin_2026_07_25.md — multiple
      BLOCKED-PREREQUISITES todos, low severity
- [ ] [REVIEW] P3. (ao-readiness)
      plans/active/issues/sports_manifest_consolidator_static_rows_out_injuries_2026_08_10.md — ambiguous verb "consider
      whether" with a conditional premise
- [ ] [REVIEW] P3. (ao-readiness) plans/active/sports_track_h_denominator_prereqs_2026_07_28.md — blocked status buried
      at end of a long paragraph
- [ ] [REVIEW] P3. (ao-readiness) plans/archive/2026_08/issues/sfi_progressive_stats_json_truncation_2026_08_09.md —
      duplicate YAML frontmatter key `archive_exempt`
- [ ] [REVIEW] P3. (ao-readiness)
      plans/active/issues/instruments_service_sports_footystats_uac_overlap_qg_red_2026_07_30.md — `locked_by` is a
      branch-name-shaped value, not an owner
- [ ] [DOC] P3. (codex-drift) plans/active/issues/defi_catalog_engine_config_key_contract_drift_2026_07_23.md:855-871 —
      low severity
- [ ] [REVIEW] P3. (ao-readiness) plans/active/strategy_archetype_latency_deployment_profile_execution_2026_08_10.md —
      written conditionally ("may have flagged") — see the new todo added this run
- [ ] [DOC] P3. (codex-drift) plans/active/strategy_archetype_latency_deployment_profile_audit_2026_08_10.md — this
      codex SSOT staleness already has a tracked fix (added this run)
- [ ] [REVIEW] P3. (ao-readiness) plans/active/issues/mdps_tradfi_ohlcv_15m_24h_conversion_still_zero_2026_07_27.md —
      bundled ready-and-blocked halves in one todo
- [ ] [REVIEW] P3. (ao-readiness)
      plans/active/issues/tradfi_year_shard_backfill_launcher_missing_source_self_deletes_2026_08_09.md —
      non-dispatchable marker may not match the AO regex
- [ ] [REVIEW] P3. (ao-readiness)
      plans/active/issues/tradfi_scope_ruling_possible_violation_legacy_fleet_relaunched_2026_08_09.md — VM-delete/kill
      decision tagged `[INFRA]` not `[OPERATOR]`
- [ ] [REVIEW] P3. (ao-readiness)
      plans/active/issues/tradfi_consolidated_closeout_over_line_cap_blocks_routine_edits_2026_08_09.md — "Consider
      whether X should Y" hides an open-ended design call
- [ ] [REVIEW] P3. (ao-readiness) plans/active/issues/tradfi_cme_future_typed_blank_instrument_id_2026_08_09.md —
      already fixed this run (checked-done todo reopened, tracked separately)

## Progress Log

- **2026-08-12 (interactive session)**: full-corpus /plan-reconcile run. Phase 0 deterministic inventory +
  `run_hygiene_sweep.sh --ci --no-regen` entry gate (3 hard failures found, 2 confirmed transient/races with concurrent
  sessions on the shared checkout — re-ran green; 1 genuine, the NA-corpus ratchet at 410 vs baseline 389+20, routed to
  `/na-eligibility-audit`, not this skill's remit). Phase 1: 46 epic-cluster hunter batches (~700KB each, partitioned by
  `parent_epic`) dispatched in 10 waves of 5 (max-parallel per CLAUDE.md), every doc read in full by exactly one hunter.
  Phase 3: all 6 P0 + 37 P1 contradictions individually verified (several via dedicated live-check agents — Databento
  billing status, tradfi wave-launcher mechanism, ES_OPT/VIX code-path coverage, ag-closeout-linkage gate, line counts,
  git-push status, archival status) before any fix applied. Phase 4: 4 genuine judgment calls routed to the operator in
  one batched Q&A round, all answered and applied. Phase 5: fixes committed with `docs(plans):` prefix; this doc created
  to track the remaining lower-severity backlog per the "no silent caps" rule — the raw 46-batch hunter output (~236
  total findings across categories) existed only in an ephemeral session scratchpad and would have been lost without
  this doc.
