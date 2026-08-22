---
doc_type: plan
title: Issues corpus completion dispatch — 572 active issue docs to DONE
summary:
  "Autonomous dispatch (operator 2026-08-21, /autonomous): drive every plans/active/issues doc to a terminal state —
  archived, covered-elsewhere, executed, or operator-ruled. Classification by a 30-agent workflow, 141 merged decisions
  (23 operator-ruled in two question rounds, 9 attempt-then-ask, 109 adopted recommendations), execution in waves."
status: active
nature: process
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [issues-corpus, autonomous-dispatch, triage, archival, operator-rulings]
related:
  [
    /plans/active/issues_corpus_executable_queue_2026_08_21.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/12-agent-workflow/commit-push-flip-rule.md,
  ]
created: "2026-08-21"
last_updated: 2026-08-21
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 20
estimate_calibrated_ai_days: 16
locked_by:
locked_since:
context_scope:
  [
    /plans/active/issues_corpus_executable_queue_2026_08_21.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
    cursor-configs/AUTONOMOUS_AGENT_RULES.md,
    scripts/plan-hygiene/count_open_tasks.py,
  ]
supersedes:
superseded_by:
depends_on:
source:
assigned_role: infra
effort: xhigh
drift_direction: advance-code
---

# Issues corpus completion dispatch — 572 active issue docs to DONE

> **Operator dispatch (2026-08-21)**: _"complete the 1,137 open issues — too many issues docs — /autonomous. Use
> workflows. Figure out all the operator-blocking questions up front so you can just go for it. I don't care if they are
> AO or NA."_ This plan is the dispatch's plan-of-record and Progress Log (AUTONOMOUS_AGENT_RULES rules 6/13d).

## Baseline (count_open_tasks.py, 2026-08-21)

- Issues scanned 573 · open todos 1,176 raw / 1,146 deduped · `na` 888 · `planning` 281.
- Plans corpus (NOT this dispatch's target): 1,258 deduped open across 435 plans — separate follow-up.
- Classification workflow `wf_c3224ebe-34e` (30 agents, 8.9M tokens, 59 min): 571/572 docs classified —
  ARCHIVE_RESOLVED 56 · COVERED_ELSEWHERE 49 · EXECUTABLE 286 (S120/M110/L42/XL14) · OPERATOR_GATED 114 · MIXED 66.
  One doc missed (`dp_cron_did_not_fire_dedup_volatile_field_2026_08_17.md`) — classified in wave 1.
- Durable per-doc verdicts + queues: `${WORKSPACE_ROOT}/.ao_checkpoints/issues_corpus_completion_2026_08_21/`
  (`triage_docs.json`, `triage_decisions.json`, `queue_<verdict>.json`) — shared-host convention (task_template §3
  finding X). Not git-tracked; regenerate from this plan's ledger if lost.

## Operator rulings 2026-08-21 (citable record — D23 convention)

| Question | Answer |
| --- | --- |
| One-off spends | APPROVED Databento CME invoice + the-odds-api top-up. DECLINED Claude top-ups ("we have loads"). IPRoyal $7 not selected. |
| Recurring subscriptions (Glassnode / Sportradar / Databento OPRA / ICE) | "None of these yet." |
| Credentials (CEX exec keys / Tenderly / Bybit scoped) | "Check Secret Manager, we have these" — verified present (see D12/D16/D19). |
| Delete batches (D2 manifest+GCS / D3 stash / D10 VMs) | ALL APPROVED under their stated gates. |
| Your-hands items | GitHub outside-collaborator click: WILL DO. Betfair: CANNOT change password. Mac check-in + MacOS-session claim: not selected. |
| Elysium | v5 reissue draft (30-day) + build lite carve-out now. |
| Pause reversals | BOTH reversed: reactivate l2_book plan; reopen IDE heartbeat design. |
| Confirmations | Round-5 rulings accurate; AAVE-PLASMA is a priority; 'Chunks 1/2' not located. |

## Decision ledger (141 merged decisions)

Disposition key: OPERATOR-RULED (answered above) · ATTEMPT-THEN-ASK (try with existing access; escalate only on a
genuine wall) · ADOPTED-REC (decided under rule 2 using the documented record; reversible by operator veto).

- **D1** [descope-approval] Stale meta-doc disposition — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Approve all — repeated audits agree these are churn, not live tasks; the two keep-open items and the one split are the only exceptions. _Affects: ao_round5_apply_session_operator_qa_index_2026_08_08.md, ao_scheduled_skills_benchmark_and_ruled_decisions_session_2026_07_30.md, ag_closeout_audit_cross_tranche_big_findings_2026_08_21.md, pytest_timeout_60s_flaky_under_contention_continued2_2026_08_03.md, pytest_timeout_60s_flaky_under_contention_continued3_2026_08_03.md, claude_anthropic_flat_rate_billing_calibration_2026_08_12.md, defi_upstream_instruments_catalog_stale_2026_07_15.md, ao_tranche_full_content_audit_findings_2026_07_31.md, instruments_docs_audit_outstanding_items_2026_07_08.md, instruments_remaining_work_audit_2026_07_10.md_
- **D2** [delete-approval] Manifest/GCS correction batch — OPERATOR-RULED 2026-08-21 — APPROVED ALL under each item's stated precondition (retention check / fresh dry-run / snapshot-first). Execute serially, one item per verified step, citing the gate result inline. _Affects: prediction_batch4_deferred_residuals_2026_08_16.md, sports_mdt_odds_captured_cells_not_found_rate_2026_08_16.md, retirement_completeness_pollutant_reverify_ice_still_live_2026_08_15.md, tradfi_cme_future_typed_blank_instrument_id_2026_08_09.md, tradfi_underlying_rename_apply_size_only_verification_gap_2026_08_12.md, sports_halftime_odds_sfi_vs_inplay_2026_07_16.md, sports_cf8_out_of_window_mechanism_reconciliation_2026_08_16.md_
- **D3** [delete-approval] Stash-pile and stale-WIP cleanup — OPERATOR-RULED 2026-08-21 — APPROVED the full stash/WIP cleanup (fresh blob re-verify before each drop; .tabs/3 re-audit first; recover sandbox fix; per-file review of slot-0 dirty files). _Affects: operator_action_items_consolidated_2026_08_08.md, unified_trading_pm_stash_pile_accumulation_2026_07_26.md, features_service_clean_check_dangling_fleet_ci_dedup_revert_2026_08_07.md, mtds_duplicate_file_split_refactor_two_sessions_2026_08_12.md, tradfi_instrument_type_lowercase_residual_381k_2026_08_15.md, mac_slot0_base_checkout_stuck_dirty_files_2026_08_11.md_
- **D4** [external-account] AWS access for worker identities — ATTEMPT-THEN-ASK — apply the already-ruled codebuild grant + scoped SSM grant from this slot's AWS identity (IAM self-service rule); fix the credential-resolution path. Only if AWS admin is genuinely absent here, escalate. _Affects: check_agent_orchestrator_ssm_send_command_access_denied_2026_08_09.md, ci_reconciler_ikenna_worker_ssm_permission_gap_2026_08_16.md, codex_drift_followups_dual_cloud_image_builds_2026_08_08.md, ci_reconcile_overnight_batch_2026_08_11.md_
- **D5** [budget-spend] Databento CME billing + relaunch fleet — OPERATOR-RULED 2026-08-21 — APPROVED: operator pays the Databento CME invoice; agent pauses the tradfi-bf-cme-ohlcv-1m fleet wave mechanism NOW (autonomous, zero-cost), relaunch only after billing clears. _Affects: tradfi_databento_account_billing_suspended_2026_08_09.md, ag_closeout_audit_cross_tranche_big_findings_2026_08_21.md, dp_vm_001_tradfi_bf_cme_ohlcv_1m_btc_2020_exit137_stall_relaunch_bound_page_2026_08_16.md, tradfi_bf_cme_ohlcv_1m_relaunch_dispatch_budget_hit_2026_08_16.md_
- **D6** [business-priority] Docs-reconcile findings sign-off — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Approve all — each item carries a per-doc recommendation; the two BIG findings need named owners now, the rest is bounded cleanup. _Affects: docs_reconcile_bigger_scope_findings_2026_08_19.md, docs_reconcile_operator_decisions_2026_08_02.md, docs_reconcile_remaining_broken_links_2026_08_02.md, docs_reconcile_findings_2026_08_17.md_
- **D7** [credentials-purchase] the-odds-api key exhaustion — OPERATOR-RULED 2026-08-21 — APPROVED: operator tops up/rotates the the-odds-api key; agent bounds the batch backfill consumer so it cannot starve live, then relaunches the live odds VM on current LDR once the key works. _Affects: dp_live_004_sports_odds_live_shard_never_captured_shared_key_quota_2026_08_20.md, live_sports_odds_upstream_failure_masked_as_honest_absence_2026_08_20.md, sports_mdt_odds_captured_cells_not_found_rate_2026_08_16.md_
- **D8** [descope-approval] Draft satellite batches activation — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Promote all — each is already conflict-checked, vetted work idle only for lack of sign-off; the defi batch also stops recurring false DP-FETCH-009 pages. _Affects: ag_closeout_audit_cefi_parked_2026_08_21.md, ag_closeout_audit_cross_cutting_parked_2026_08_21.md, dp_fetch_009_defi_dex_pool_swaps_uniswap_v3_ethereum_stale_schema_validation_failed_2026_08_16.md_
- **D9** [design-ruling] Over-cap plan handling policy — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Split both docs now; also approve the narrow carve-out — it closes a recurring false-positive class without letting content growth past the cap. _Affects: plan_reconciler_findings_cefi_2026_08_16.md, plan_reconciler_findings_defi_master_epic_2026_08_18.md, tradfi_consolidated_closeout_over_line_cap_blocks_routine_edits_2026_08_09.md_
- **D10** [delete-approval] Stale/wedged VM remediation — OPERATOR-RULED 2026-08-21 — APPROVED all three VM remediations (cycle BYBIT-FUTURES live VM via its registered launcher; inspect the deribit-sweep VM then delete only if confirmed hung; kill/relaunch the 2 stale mdps-features-live VMs, bounded backfill VMs finish with a corrective re-pass). _Affects: dp_live_004_stale_mtds_vm_pre_fix_image_2026_08_20.md, dp_vm_003_canonical_migration_cefi_deribit_sweep_wedged_relaunched_fresh_name_2026_08_16.md, defi_pool_uppercase_recurrence_after_fold_2026_08_11.md_
- **D11** [design-ruling] Tarball pipeline hardening — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Approve refresh + narrow auto-dirty, defer the gate — the first two close measured recurring page classes cheaply; the gate is a riskier shared-pipeline change deserving its own design pass. _Affects: dp_vm_001_mdps_tradfi_2021_exit_nonzero_stale_tarball_rootcause_2026_08_16.md, lc_verify_tarball_freshness_auto_mode_silent_dirty_skip_2026_08_06.md, dp_vm_001_mdps_backfill_cefi_tarball_race_relaunched_2026_08_15.md_
- **D12** [credentials-purchase] CEX execution credentials — OPERATOR-RULED 2026-08-21 — 'check Secret Manager, we have these': VERIFIED in GSM (central-element-323112): binance-trade-api-key/-secret, bybit-trade-api-key (+bybit-api-secret; bybit-trade-api-secret ABSENT), exec-<client>-okx-api-key/-secret/-passphrase x9, deribit-testnet-write-*, bybit-testnet-trade-*. Now EXECUTABLE: wire place_order() + verify the withdraw path on testnet. _Affects: capability_wizard_analysis_findings_2026_06_11.md, cefi_ccxt_withdraw_stub_returns_false_confirmed_2026_08_16.md_
- **D13** [design-ruling] Basedpyright ratchet 1259 vs 1261 — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Deeper bisection first — ratchets-only-go-down is a HARD RULE and a cross-slot measurement shows 1259 is reachable on a current tree; raise only as last resort. _Affects: deployment_service_basedpyright_ratchet_broken_by_dep_backmerge_2026_08_15.md, dp_watcher_stale_003_identity_after_registry_id_bump_to_004_2026_07_31.md_
- **D14** [business-priority] Historical quickmerge-bypass commits — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Bulk-bless after review — the 3 already-reviewed commits were clean and all repos' gates are green; this removes latent promotion risk at lowest cost. _Affects: deployment_service_historical_quickmerge_bypass_backlog_2026_08_21.md, mtds_is_historical_quickmerge_bypass_backlog_2026_08_16.md_
- **D15** [design-ruling] OKX-FUTURES xperp disambiguation — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): instFamily lookup — deterministic and consistent with the already-ruled mechanism for the original xperp ambiguity. _Affects: ag_closeout_audit_cefi_parked_2026_08_21.md, okx_futures_instid_marker_convention_mismatch_2026_07_30.md_
- **D16** [external-account] Tenderly fork credential — OPERATOR-RULED 2026-08-21 — VERIFIED in GSM: tenderly-api-key + tenderly-fork-rpc-url exist. EXECUTABLE: un-skip test_tenderly_fork_full_cycle + close the e2e wizard D4 item (verify secret versions are non-empty first). _Affects: exec_tenderly_2026_08_15.md, e2e_defi_config_taxonomy_wizard_roundtrip_2026_06_17.md_
- **D17** [credentials-purchase] Glassnode API key — OPERATOR-RULED 2026-08-21 — DECLINED for now ('none of these yet'): no Glassnode purchase; adapter stays dormant, todo stays BLOCKED-CREDENTIALS with this dated ruling (re-ask only on a named product need). _Affects: glassnode_kaiko_credential_ask_2026_08_09.md, operator_action_items_consolidated_2026_08_08.md_
- **D18** [credentials-purchase] Sportradar scope and purchase — OPERATOR-RULED 2026-08-21 — DECLINED for now: no Sportradar purchase; SportradarAdapter stays dormant (BLOCKED-CREDENTIALS, dated). _Affects: sportradar_credential_ask_2026_08_09.md, operator_action_items_consolidated_2026_08_08.md_
- **D19** [credentials-purchase] Bybit trade-scoped key — OPERATOR-RULED 2026-08-21 — partially present: bybit-trade-api-key exists, bybit-trade-api-secret does NOT. EXECUTABLE half: confirm the code's scoped-name fallback works with bybit-api-secret; the missing secret stays a credential-ask (operator's Bybit login). _Affects: per_venue_scope_key_provisioning_incomplete_2026_07_23.md, operator_action_items_consolidated_2026_08_08.md_
- **D20** [external-account] GitHub outside-collaborator approval — OPERATOR-RULED 2026-08-21 — operator will click 'Require approval for all outside collaborators' in the GitHub UI. Pending-operator; verify via the repo settings once done. _Affects: governance_sweep_deferred_followups_2026_08_06.md, operator_action_items_consolidated_2026_08_08.md_
- **D21** [business-priority] Live-trading hard-stop timing — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): When ready — every prior pass re-confirmed these as not-time-sensitive reserved sign-offs with no new readiness evidence. _Affects: operator_action_items_consolidated_2026_08_08.md, governance_sweep_deferred_followups_2026_08_06.md_
- **D22** [design-ruling] Backlog park-drift alert — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Build in AO's regen path — cheap, catches the drift closest to its source, and closes a silent-thrash class already documented twice. _Affects: backlog_park_lost_across_sibling_todo_insertion_2026_07_30.md, backlog_regen_reverted_p1_2_park_2026_08_01.md_
- **D23** [design-ruling] Ruling-record convention — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Dedicated ruling-record doc per session — simplest, with 2 working precedents already in the corpus. _Affects: operator_ruling_record_ao_round5_apply_session_2026_08_08.md, operator_action_items_consolidated_2026_08_08.md_
- **D24** [other] Round-5 ruling transcription check — OPERATOR-RULED 2026-08-21 — CONFIRMED: all 6 round-5 rulings accurate as transcribed. Close the doc. _Affects: operator_ruling_record_ao_round5_apply_session_2026_08_08.md, operator_action_items_consolidated_2026_08_08.md_
- **D25** [budget-spend] Databento ICE/OPRA subscriptions — OPERATOR-RULED 2026-08-21 — DECLINED for now: no Databento ICE/OPRA add-ons; both stay deliberately fail-closed (dated ruling recorded on the docs). _Affects: databento_ice_opra_subscription_ask_2026_08_09.md, operator_action_items_consolidated_2026_08_08.md_
- **D26** [business-priority] Elysium SLA v5 reissue — OPERATOR-RULED 2026-08-21 — APPROVED: draft SLA v5 (30-day support period, corrected dates) for operator review BEFORE anything goes to the client. _Affects: elysium_sla_v4_support_period_and_stale_dates_2026_08_08.md, plan_reconciler_findings_all_2026_08_12.md_
- **D27** [business-priority] Elysium disclosure and carve-out scope — OPERATOR-RULED 2026-08-21 — APPROVED: build the 'lite' carve-out repo now, withhold the venue-integration reference, ship the inert betfair/ibkr/polymarket adapters as-is. _Affects: elysium_sla_v4_support_period_and_stale_dates_2026_08_08.md, venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md_
- **D28** [design-ruling] na-eligibility skill follow-ups — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Approve both — the doc edit is cheap defense against the stale-Read class; the re-audit cost is bounded and already accepted. _Affects: na_eligibility_audit_same_tranche_duplicate_concurrent_dispatch_2026_08_18.md, na_eligibility_body_hash_unstable_across_marker_appends_2026_08_17.md_
- **D29** [budget-spend] Overage-rejected account top-up — OPERATOR-RULED 2026-08-21 — DECLINED ('not topping up claude, we have loads'): overage-rejected accounts stay unusable until the 2026-08-23 weekly reset; failover routes around them. Close the remediation todo as DEFERRED-BY-DESIGN citing this ruling. _Affects: account_failover_ignores_overage_rejected_2026_08_18.md_
- **D30** [external-account] Gemini proj4 accounts — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Re-disable — explicitly cancelled as unneeded; a one-line reversible disable beats provisioning an idle spare. _Affects: ao_dispatch_skew_root_cause_and_session_cleanup_2026_08_21.md_
- **D31** [business-priority] Smoke-test findings reconcile depth — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Spot-check — 2 of 3 spot-checked failures were structural manifest non-instrumentation a trace can't fix. _Affects: adapter_findings_gcs_manifest_deployment_api_reconciliation_gap_2026_07_08.md_
- **D32** [design-ruling] Workflow-drift design items — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Provide the ruling — 6 audit passes with no forward decision is pure churn either way. _Affects: ag_closeout_audit_ci_parked_2026_08_16.md_
- **D33** [design-ruling] Fork batch-draft collision prevention — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Tighten fork-prompt language — cheapest reduction; a full lock's maintenance cost isn't justified by one zero-loss incident. _Affects: ag_closeout_audit_fork_scope_creep_duplicate_batch_draft_2026_08_19.md_
- **D34** [business-priority] l2_book plan reactivation — OPERATOR-RULED 2026-08-21 — APPROVED: reactivate l2_book_microstructure_capture (assigned_vm: planning) so the reopen-drop dispatch-defect re-test can run. _Affects: ao_residuals_after_dispatch_hardening_2026_07_17.md_
- **D35** [design-ruling] IDE heartbeat mechanism — OPERATOR-RULED 2026-08-21 — APPROVED: reopen the IDE-compatible human-fleet heartbeat design as a FRESH ruling/mechanism revisit (the UserPromptSubmit rejection stands; propose a different carrier). _Affects: ao_review_slot_hard_rule_and_diagnostics_2026_08_17.md_
- **D36** [design-ruling] tmpfs sizing vs PrivateTmp — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Keep the reaper — shipped and verified; revisit only on recurrence. _Affects: ao_tmp_tmpfs_full_sqlite_disk_full_errors_2026_08_21.md_
- **D37** [design-ruling] Turn-count circuit breaker — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Monitoring-only first — cheapest, reversible, sizes the threshold with real data. _Affects: ao_worker_unbatched_tool_calls_inflate_turn_count_2026_08_05.md_
- **D38** [business-priority] Superseded-epic artefact ownership — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Check for successors first, fall back to shared-mechanism epic assignment. _Affects: artefact_sections_with_superseded_owning_epics_2026_08_20.md_
- **D39** [business-priority] t1-recon zombie schedulers — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Investigate first — if no real consumer depends on t1-recon/ml/, retiring is cheaper and matches precedent. _Affects: asia_northeast1_zombie_schedulers_dead_targets_2026_08_07.md_
- **D40** [business-priority] AutoSpawn refill SLA — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Correct the SLA — impact is bounded to idle capacity; raising the cap risks host degradation without an audit. _Affects: autospawn_fleet_cap_headroom_throttling_routine_sla_miss_2026_08_09.md_
- **D41** [design-ruling] Per-todo prerequisites mechanism — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Build the per-todo mechanism — fixes the root and composes with existing depends_on machinery. _Affects: blocked_prerequisites_marker_not_in_non_dispatchable_regex_2026_07_28.md_
- **D42** [design-ruling] BLRS determinism ledger roots — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): External wrapper — keeps a resolver bug from turning the honest no-op into a fabricated ε=0 verdict (prior review endorsed). _Affects: blrs_daily_determinism_ledger_root_wiring_scope_2026_08_20.md_
- **D43** [other] CI-events ledger build_id — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Leave as-is — low-signal nicety, nothing currently blocked. _Affects: build_deploy_pipeline_provenance_and_aws_deferred_gaps_2026_07_21.md_
- **D44** [design-ruling] book_snapshot5 contract fixes — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Change the calculators and reformat the message — no writer produces the expected shape, and the reformat needs no schema change. _Affects: cefi_book_snapshot5_schema_contract_ts_event_levels_mismatch_2026_07_28.md_
- **D45** [budget-spend] Tardis tier upgrade — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Keep free tier — the registry is a complete, correct, cited fix for the current instrument set; not urgent. _Affects: cefi_inverse_contract_size_wrong_and_missing_2026_08_12.md_
- **D46** [design-ruling] 586 marker-less CeFi rows — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Rewrite now — pattern already proven multiple times; marginal cost is low. _Affects: cefi_residual_followups_after_honest_done_2026_07_17.md_
- **D47** [design-ruling] Fenced-code path exemption — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Add the exemption — removes a recurring false-positive class without weakening enforcement. _Affects: check_reference_paths_silent_skip_and_quiet_hides_violation_2026_08_12.md_
- **D48** [design-ruling] LDR monitor streak linkage — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Defer — the higher-value per-run linkage is already fixed. _Affects: ci_alert_failure_resolution_linkage_2026_08_16.md_
- **D49** [other] Unpark citadel batch1-004 — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Unpark now — strongest evidence of any parked sibling. _Affects: citadel_satellite_ao_dispatch_batch1_004_repeat_wedge_parked_2026_08_08.md_
- **D50** [design-ruling] Claude CLI autoupdater pin — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Remove unless a specific compatibility issue is guarded — the generation gap risks its own bugs. _Affects: claude_settings_symlink_writeback_drops_hooks_2026_08_11.md_
- **D51** [budget-spend] Cloud Build 'fallback' naming — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Rename — no observed failure needed cross-region redundancy; the fix is cheap and prevents documented false-alarm triage. _Affects: cloud_build_router_fallback_region_same_as_primary_2026_08_14.md_
- **D52** [design-ruling] UAC publish-ordering race fix — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Approve with the self-hosted move dropped — repeated recurrence justifies shipping now; reintroducing public-repo fork-PR exposure isn't worth the minutes saved. _Affects: cloud_build_uac_publish_ordering_race_recurrence_strategy_service_2026_08_20.md_
- **D53** [external-account] Traffic-pin alert webhook — ATTEMPT — populate the GSM webhook secret via a one-off GH workflow dispatch (the GH secret cannot be read back, a workflow can write it to GSM); verify with a UAT canary rollback. _Affects: cloud_run_traffic_pin_silent_freeze_alert_wiring_2026_08_05.md_
- **D54** [other] Locked-doc context_scope backfill — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Wait — the docs are already resolved and will most likely archive on their own. _Affects: context_scope_backfill_locked_docs_residual_2026_08_20.md_
- **D55** [business-priority] Partial VM cost labeling — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Ship partial — ~30% visibility beats 0.16%; remaining tiers are independent work. _Affects: cost_observability_deferred_followups_2026_07_10.md_
- **D56** [design-ruling] Dashboard Playwright gating — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Gate it — this exact ungated gap already produced 2 silent regressions. _Affects: dashboard_deepseek_e2e_specs_red_stale_fixture_expectations_2026_08_08.md_
- **D57** [design-ruling] PROTOCOL_LAUNCH_DATES aliases — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Centralize — eliminates the bug class at the source. _Affects: defi_aavev3_bare_alias_enumerator_bug_2026_08_08.md_
- **D58** [business-priority] Balancer historical backfill — ATTEMPT — verify whether Balancer dex_pool_state backtests feed live decisions; backfill iff yes, else go-forward-only (document either way). _Affects: defi_balancer_dex_pool_state_writer_schema_mismatch_2026_08_04.md_
- **D59** [design-ruling] Per-candidate liquidation features — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Check the sibling work first — it may make this design question moot. _Affects: defi_catalog_engine_config_key_contract_drift_2026_07_23.md_
- **D60** [design-ruling] CONSOLIDATOR_DOWN Slack routing — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Add now — cheap, closes a real zero-delivery gap on a CRITICAL alert. _Affects: defi_consolidator_paused_by_inflight_rebuild_vm_2026_08_07.md_
- **D61** [descope-approval] Unused LST adapter family — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Delete — ABI-direct already gives equivalent-or-better coverage; reconsider only on a named product need. _Affects: defi_lst_adapter_factory_family_unused_by_production_path_2026_08_09.md_
- **D62** [design-ruling] Stale-fallback completeness check — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Row-count mismatch — a concrete self-diagnosing signal that caught the real 2026-08-07 incident (260 vs ~27,549). _Affects: defi_manifest_allow_stale_fallback_incomplete_for_long_pause_2026_08_07.md_
- **D63** [design-ruling] Oracle empty-path classification — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Classify+thread — mirrors the shipped Pyth http_status pattern and reuses existing machinery. _Affects: defi_oracle_family_empty_path_exception_classification_2026_08_09.md_
- **D64** [descope-approval] Uppercase-corpus migration plan type — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Human-driven — needs a precise per-AG count first and spans 4 prod buckets; matches the human-default rule for judgment-adjacent scale. _Affects: defi_pool_uppercase_recurrence_after_fold_2026_08_11.md_
- **D65** [design-ruling] Pyth instrument_id canonicalization — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): PYTH-SOLANA form with migration, gated on a regression test against the known false-77-gap-days failure mode. _Affects: defi_pyth_oracle_prices_seeded_feeds_unfetchable_2026_08_03.md_
- **D66** [business-priority] AAVE-PLASMA archetype coverage — OPERATOR-RULED 2026-08-21 — AAVE-PLASMA IS a priority: file the strategy-service archetype/slot catalogue implementation todo now. _Affects: defi_venue_e2e_batch1_deferred_followups_2026_08_17.md_
- **D67** [design-ruling] Health-alert gate cron shape — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Lean narrower — documented OOM-regression risk from census fan-out; no committed ruling in the record. _Affects: deployment_api_inventory_alert_gate_ondemand_only_2026_07_27.md_
- **D68** [design-ruling] QG 5.83 sibling-repo source — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Mildly favor origin — this fragility has recurred twice. _Affects: deployment_api_mtds_meta_missing_blocks_workspace_qg_step_5_83_2026_08_03.md_
- **D69** [design-ruling] t1-recon Terraform ownership — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): for_each as sole owner after the external-consumer check; for imports, verify whether dev/staging state already aliases any address first, then pick an isolation scheme. _Affects: deployment_service_t1_recon_duplicate_module_definitions_2026_08_09.md_
- **D70** [external-account] AWS creds for dp-meta-watchers — ATTEMPT-THEN-ASK — create one least-privilege IAM key in GSM (matches *-worker-aws-creds pattern) if AWS IAM access exists from this slot; else escalate. _Affects: dp_live_003_agent_orch_aws_credentials_gap_2026_08_10.md_
- **D71** [business-priority] Revocation-hold audit — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Audit once — cheap, and a stuck hold silently blocks deploys with no page. _Affects: dp_revocation_release_never_resolves_identity_2026_08_15.md_
- **D72** [design-ruling] page_operator carve-out generalization — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Wait — 2 data points is thin for the right abstraction; each carve-out has been cheap. _Affects: dp_vm_001_expected_universe_halt_safety_false_page_2026_08_07.md_
- **D73** [design-ruling] manifest-recon auto-relaunch — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Keep None — the root cause was memory sizing (already fixed via column-slimming); auto-relaunch would mask future OOMs. _Affects: dp_vm_003_manifest_recon_cefi_silent_death_unsliced_manifest_read_2026_08_15.md_
- **D74** [other] DeFi consolidator pause ownership — OPERATOR-RULED 2026-08-21 — operator did NOT claim the MacOS session. ADOPT REC: leave the defi consolidator paused, keep identifying the session owner (never resume blind). _Affects: dp_watcher_004_defi_market_data_consolidator_scheduler_flapping_pause_2026_08_21.md_
- **D75** [design-ruling] MTDS collision-guard exemption — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Hold off — one ~60-min window doesn't establish MTDS traffic as invariant-like; widening a dispatch-safety guard needs more evidence. _Affects: escalation_collision_guard_starvation_market_tick_data_service_2026_08_21.md_
- **D76** [design-ruling] e2e wiring rulings — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Close the ruling, require manual OTC review (typo-compounding risk), and scope the wiring as a LOCAL design plan — it's a live-capital design call, not a patch. _Affects: e2e_wiring_reachability_audit_2026_08_15.md_
- **D77** [design-ruling] Execution sensitivity layer rulings — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Allow triggered MARKET (backtest-realism concern no longer applies post-trigger) and route explicitly — a fourth router is premature. _Affects: execution_delta_proxy_repricer_generalization_2026_08_18.md_
- **D78** [business-priority] On-chain collectors for 5 feature groups — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Per-protocol collectors — matches existing patterns, avoids a vendor; operator must name the protocol/field mapping before scoping. _Affects: features_onchain_featureless_shards_and_vocabulary_split_2026_07_20.md_
- **D79** [business-priority] Corporate-actions re-sourcing — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): yfinance first; escalate to paid only if coverage proves inadequate. _Affects: features_service_corporate_actions_polygon_io_banned_vendor_2026_08_18.md_
- **D80** [design-ruling] ff-pull drift cleanups — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Keep auto-clean narrow (widening risks discarding real dependency edits) and bulk-clean the archives (one-time, low-risk, fixes the dirty-count noise). _Affects: ff_pull_fleet_drift_rca_2026_08_11.md_
- **D81** [business-priority] FILL_COMPLETED gap-window audit — ATTEMPT (read-only) — check strategy-service deployment timestamps vs the FILL_COMPLETED fix + FillDB counts for the gap window; reconcile ONLY if a live instance ran (escalate that specific finding). _Affects: fill_completed_event_schema_break_live_defi_2026_08_08.md_
- **D82** [external-account] glue-1 checkout-reuse check — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Skip — low-value confirmation the doc itself treats as optional. _Affects: fleet_wide_qg_cascade_pm_manifest_race_recurrence_2026_08_19.md_
- **D83** [external-account] gemma-4-31b investigation — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Stop — blind-retrying guidance applies; the remaining lead has no guaranteed resolution. _Affects: gemma_4_31b_it_persistent_timeout_2026_08_19.md_
- **D84** [design-ruling] Retire grind-style bulk scripts — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Retire — safe-doc-push already solves the exact concurrency-safety problem this investigation rediscovered piecemeal. _Affects: git_stash_push_pop_silently_drops_content_under_high_branch_velocity_2026_08_17.md_
- **D85** [design-ruling] Honest-coverage model rulings — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Keep resharding gated (its own text requires mockup sign-off), approve the OPTION removal (same evidence class as the shipped fix), route market_metadata through reference_scope (consistent with the model). _Affects: honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md_
- **D86** [business-priority] TradFi paper-engine wiring — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Keep deferred — no evidence the cycle-scope ruling changed. _Affects: ibkr_place_order_guard_determinism_proof_infeasible_2026_08_21.md_
- **D87** [design-ruling] Visibility/runner-drift re-audit check — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Don't build — 5+ audit passes found no recurrence and there's no existing tracker to diff against. _Affects: image_build_validate_stranded_on_deregistered_glue_runners_2026_08_07.md_
- **D88** [design-ruling] Registry/wiring audit rulings — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): All three recs — correct asset_group avoids downstream drift, narrowing would silently reduce coverage, and the wiring blocker is resolved. _Affects: issue_docs_remediation_sweep_2026_06_02.md_
- **D89** [business-priority] CEFI liquidation-capture variant — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Downgrade — cheap, stops the capability manifest overclaiming. _Affects: liquidation_capture_cefi_bid_ladder_variant_unbuilt_2026_08_17.md_
- **D90** [design-ruling] Lightweight-launcher admission gating — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Migrate the single candidate (launch-prediction-pipeline-vm.sh) — the census already found it's a small job. _Affects: live_path_has_no_stale_producer_revocation_2026_08_14.md_
- **D91** [budget-spend] Mac host QG concurrency — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Document the ceiling first; consider RAM only if queueing fixes don't reduce contention. _Affects: local_host_concurrent_qg_serial_rule_violated_2026_08_15.md_
- **D92** [business-priority] Runner action warm-cache — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Accept — the retry net already closes the incident class; caching adds maintenance for a rare mode. _Affects: main_backmerge_to_ldr_no_retry_safety_net_for_non_pm_repos_2026_08_18.md_
- **D93** [design-ruling] author: required on generated docs — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Make required — provenance should never be silently droppable; the guard alone doesn't stop deliberate drops. _Affects: main_ldr_backmerge_silently_reapplies_collateral_frontmatter_deletion_2026_08_17.md_
- **D94** [business-priority] Byte-identical manifest duplicates — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): No action — touching the incident-scarred 3625-line consolidator carries more risk than the duplication's cost. _Affects: manifest_schema_drift_dup_residual_diagnosis_2026_08_15.md_
- **D95** [design-ruling] Flush durability tradeoff — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Reject — redundant once delta-shards ship; preserving durability is the workspace default. _Affects: manifest_writer_per_vm_shard_flush_scales_with_shard_size_2026_07_28.md_
- **D96** [design-ruling] Timestamp split declaration policy — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Explicit declaration — P0 replay-integrity issue; a silent default repeats the invisible-ambiguity failure this doc exists to close. _Affects: market_data_timestamp_semantics_collapsed_to_one_field_2026_08_20.md_
- **D97** [design-ruling] Sports feature entrypoint — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Fold — consistency with every other family; the current state actively misleads live-launcher work. _Affects: mdps_features_deadcode_consolidation_2026_07_20.md_
- **D98** [business-priority] MEV bundle boundary timing — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Continue deferring — the operator made this exact call 2 days prior; no new information. _Affects: mev_engines_no_tenderly_simulate_bundle_call_site_2026_08_19.md_
- **D99** [design-ruling] Bash shared-index hard-block — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Keep warn-only — the warn guard covers the measured incident class; fleet-wide behavior change needs more signal. _Affects: model_capability_aware_dispatch_audit_2026_08_21.md_
- **D100** [budget-spend] Per-worker memory ceiling — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Arm conservatively — two runaway scripts starved the whole fleet within ~36h under the shared cap alone. _Affects: mtds_gas_fees_migration_script_unbounded_memory_2026_07_30.md_
- **D101** [business-priority] MTDS missing -prod trigger — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Confirm intentional, pending input from whoever owns MTDS cutover phasing — the register has no entry either way. _Affects: mtds_ldr_cloud_build_docker_step6_failure_2026_08_10.md_
- **D102** [external-account] Near-instant QG kill root-cause — ATTEMPT-THEN-ASK — run dmesg/journalctl via SSM on the shared host; if no root path exists, record and move on. _Affects: mtds_qg_background_task_near_instant_kill_2026_08_15.md_
- **D103** [design-ruling] Venue-key case fallback removal — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Remove — every venue's dual-registration makes it redundant; both polymarket connectors already resolve under canonical keys. _Affects: mtds_ws_venue_fallback_removal_polymarket_decision_2026_08_17.md_
- **D104** [design-ruling] NA-ratchet gate scoping — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Entry only — re-gating aggregate PRs is what converts ordinary growth into the documented promotion deadlock, with no demonstrated safety benefit. _Affects: na_corpus_ratchet_diff_base_vs_lagging_main_deadlocks_promotion_2026_08_10.md_
- **D105** [design-ruling] staking_apy_bps methodology — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Widen lookback or smooth — either addresses the root statistical cause; clamping only masks it. Quant-methodology call. _Affects: onchain_staking_apy_bps_single_day_annualization_noise_2026_08_09.md_
- **D106** [design-ruling] Operational-modes migration rulings — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Assign owner+date (unblocks the codex-doc todo) and fold the flag for convention consistency — no protocol-level reason for an exception was found. _Affects: operational_modes_antipatterns_not_actually_deleted_2026_08_09.md_
- **D107** [other] Consolidated action-items residual — OPERATOR-RULED 2026-08-21 — IPRoyal ~$7 proxy NOT approved (unselected): forexfactory stays BLOCKED-CREDENTIALS. Every other (non-spend) disposition in this batch ADOPTED as recommended. _Affects: operator_action_items_consolidated_2026_08_08.md_
- **D108** [business-priority] Pendle priority — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Keep P3 — no archetype declares Pendle; the parent doc has live tracking. _Affects: pendle_venue_onboarding_2026_08_16.md_
- **D109** [design-ruling] Per-client config axes — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): All three axes (the original operator ask established demand) with asymmetric reload — matches the recovery-matrix philosophy and errs safe. _Affects: per_client_config_surface_keying_and_missing_axes_2026_08_12.md_
- **D110** [credentials-purchase] Dormant CEX venue credentials — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Decline — no demand signal; provisioning ahead of need has ongoing credential-hygiene cost. _Affects: per_venue_scope_key_provisioning_incomplete_2026_07_23.md_
- **D111** [design-ruling] Plan-quality defense rulings — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Prek-sufficient (the full-sweep target has moved for sessions) and the parser fix (fixes the actual root cause, not prettier). _Affects: plan_quality_four_line_defense_architecture_2026_07_23.md_
- **D112** [business-priority] sports Track-H denominator — ATTEMPT — open sports_track_h's source doc; rule directly if the record resolves it, else escalate the concrete options. _Affects: plan_reconciler_findings_all_2026_08_12.md_
- **D113** [delete-approval] batch1b delete-risk retag — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Retag — costs nothing and matches the delete-safety HARD RULE. _Affects: plan_reconciler_findings_security_and_cross_cutting_master_2026_08_19.md_
- **D114** [business-priority] Firestore-migration successors — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Author the 3 plans (bounded, prevents drift); set the duration if the GO/NO-GO precondition is near, else it can wait. _Affects: plan_reconciler_findings_ui_2026_08_10.md_
- **D115** [other] 'Chunks 1/2' review artifact — OPERATOR-RULED 2026-08-21 — operator did not locate the artifact either. Close as chat-only/unresolvable (the search was exhaustive; no pointer exists). _Affects: pm_archive_false_done_and_review_backlog_2026_08_15.md_
- **D116** [design-ruling] Post-cutover residuals — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Split now and wire the digest — it's a real fail-open point in cross-repo breaking-change protection. _Affects: post_cutover_silent_assumption_sweep_2026_07_23.md_
- **D117** [design-ruling] proseWrap non-idempotency — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Accept the ratchet — it holds the corpus at 0; fleet-wide prettier blast radius is disproportionate to a cosmetic bug. _Affects: prosewrap_padding_corpus_wide_1290_space_2026_08_03.md_
- **D118** [external-account] Betfair password rotation — OPERATOR-RULED 2026-08-21 — operator CANNOT change the Betfair password. Root cause is Betfair's own ACCOUNT_PENDING_PASSWORD_CHANGE flag (not a workspace defect): the account holder must change it on betfair.com. Stays BLOCKED-OPERATOR naming the account holder; no agent action possible. _Affects: prediction_betfair_lay_price_adapter_scaffold_deleted_2026_08_09.md_
- **D119** [design-ruling] quickmerge ENVIRONMENT autodetect — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Broaden — the specific risk the trial exposed is fixed and confirmed fleet-clean. _Affects: quickmerge_environment_autodetect_forces_dev_off_main_2026_07_25.md_
- **D120** [design-ruling] QG green-tree fast-path — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Re-measure first; if still material, the fast-path with operator-reviewed design. _Affects: quickmerge_sentinel_race_retry_storm_under_pm_doc_push_contention_2026_07_21.md_
- **D121** [business-priority] Batch-live-recon gap promotion — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Promote — well-scoped deterministic multi-repo work; 6+ audits over 5+ weeks reached the same conclusion. _Affects: recon_bucket_missing_nightly_recon_failing_2026_07_13.md_
- **D122** [design-ruling] Preemption signal source — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): API fallback — the marker failed 2/2 even after hardening; the API signal has no race. _Affects: session_bound_vm_monitoring_reliability_gap_2026_07_26.md_
- **D123** [design-ruling] Per-slot gcloud configs — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): No — pinning stops scripts trusting the ambient account; named configs add bootstrap complexity for a closed case. _Affects: shared_host_gcloud_active_account_cross_slot_clobber_2026_08_04.md_
- **D124** [design-ruling] Glue-runner idiom + TS differ — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Build the protocol and retry (root cause fully understood; removes a live-runner risk); leave the TS differ as a backlog candidate unless promote latency becomes measured pain. _Affects: silent_failures_surfacing_as_generic_promotion_lag_2026_07_17.md_
- **D125** [design-ruling] seed_validator contract scope — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Author — a load-bearing MTDS gate depends on these; leaving 2 of 4 families vacuous defeats the audit's purpose. _Affects: silent_wrong_answer_audit_untracked_followups_2026_07_28.md_
- **D126** [design-ruling] Repeat-skip auto-park — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Build — real wasted spawn overhead; a conservative threshold closes the gap without human vigilance. _Affects: solana_dex_pool_swaps_indexer_002_repeat_wedge_parked_2026_08_08.md_
- **D127** [design-ruling] odds data_type casing — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Harden consumers — the ecosystem already treats dual casing as solved; rewriting betfair_adapter is unreviewed scope expansion. _Affects: sports_odds_data_type_casing_wider_than_odds_api_2026_08_15.md_
- **D128** [business-priority] Conflict-marker slot cleanup — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Dispatch now — escalations at 53/27/14 attempts are starved purely for these slots. _Affects: stale_slot_conflict_markers_block_escalation_dispatch_2026_08_21.md_
- **D129** [design-ruling] Sub-agent write-scope guard — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Build — the failure is invisible-by-default and could silently corrupt a peer's work. _Affects: subagent_wrote_to_foreign_checkout_bare_repo_path_2026_08_18.md_
- **D130** [design-ruling] ONCHAIN pseudo-chain — ATTEMPT — verify live consumers of the ONCHAIN label; keep if any reader exists, else remove. _Affects: three_chain_registries_disagree_none_authoritative_2026_08_19.md_
- **D131** [other] Legacy-twin dry-run coverage — ATTEMPT — read the 2026-08-15 legacy-twin dry-run's actual scope; close if it covers the vanished-before-tracked-delete pattern, else commission the targeted check. _Affects: tradfi_legacy_twin_candidates_already_absent_unexplained_2026_08_14.md_
- **D132** [design-ruling] Share-class symbol convention — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Dot-join — matches standard ticker convention; zero corpus precedent exists, so this is the operator's naming call. _Affects: tradfi_reconciliation_2026_08_17_findings_2026_08_17.md_
- **D133** [descope-approval] Equity tbbo scope — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Gate out — matches the decided scope with the smaller single-repo change; the alternative requires affirmatively reversing a ruling. _Affects: tradfi_tbbo_unclassified_adapter_error_dp_fetch_009_2026_08_15.md_
- **D134** [design-ruling] Kamino historical oracle path — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Accept — a bespoke reader for one venue's one data_type is disproportionate unless a specific backtest needs it. _Affects: uac_data_type_validity_combinator_fragmentation_2026_07_07.md_
- **D135** [credentials-purchase] Firebase admin E2E strategy — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Emulator-backed — avoids provisioning/rotating a live admin credential in CI. _Affects: ui_admin_v1_routes_need_firebase_admin_creds_and_e2e_dev_server_instability_2026_08_09.md_
- **D136** [design-ruling] Branch-registry consolidation + Mac check-in — OPERATOR-RULED 2026-08-21 — Mac laptop check-in NOT scheduled by operator; stays [OPERATOR] with this date. Registry consolidation: keep separate registries + parity test (REC adopted). _Affects: unified_trading_ci_ff_pull_cron_branch_override_gap_2026_08_17.md_
- **D137** [other] Ahead-of-origin slot sweep — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Add it — cheap insurance against silently orphaned commits. _Affects: unified_trading_ci_slot3_checkout_has_3_stale_unpushed_commits_2026_08_20.md_
- **D138** [other] Category-1 GCS-call fixes routing — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): AO batch — the same mechanical-fix-plus-live-verify pattern already worked across 6 repos with zero data loss found. _Affects: utl_gcs_client_upload_from_string_silent_write_failure_2026_08_18.md_
- **D139** [design-ruling] Disk-guard liveness signal — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Drop tmux — the shipped signal covers both worker types; fabricated sessions risk confusing send-keys nudges and TmuxPruner. _Affects: vm_disk_guard_wipes_active_slot_venvs_2026_08_20.md_
- **D140** [design-ruling] Class-B stall-watch coverage — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Allowlist — gets protection without re-opening the heuristic to every fleet VM name. _Affects: vm_launcher_class_b_no_stall_kill_gap_2026_07_27.md_
- **D141** [business-priority] pipeline_e2e --resume gate — ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Dispatch now — gating a small resilience feature behind an open-ended unfixed root cause has cost more re-diagnosis time than the feature would take to ship. _Affects: worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md_

## Waves

### Wave 1 — no-input work (workflow `wf_b38a4988-fc3` complete 2026-08-21; archival pass 2 pending)

- [ ] [SCRIPT] P0. Archive the 56 ARCHIVE_RESOLVED docs via the 6-step ritual (serial lane, safe-doc-push). Done-when:
      `queue_archive_resolved.json` docs all under `plans/archive/` with referrers fixed; skips listed in Progress Log.
      Pass 1 (2026-08-21): 18 archived (`unified-trading-pm@4edaa505b1`, `@f7b7ee1aa5`, `@b97de2cbf9`, `@6c274b982d`,
      `@dc08518953`, `@c66f71e3d5`, `@4c8de37473`), 38 skipped — see Progress Log for the skip taxonomy.
- [ ] [SCRIPT] P1. Archival pass 2 over the 38 pass-1 skips + the 9 covered-lane `flag-for-archive` docs: (a) docs whose
      `archive_exempt: true` carries an explicit BRIDGE note ("drop this line + git mv in the follow-on pass") — this
      dispatch IS that pass, drop the bridge and archive; (b) `locked_by: live-defi-rollout` placeholder docs — run
      `scripts/plans/clear_locked_by_placeholder_2026_08_12.py --dry-run` then `--apply` (the sanctioned fix for the
      documented branch-name-as-lock bug; a real actor id such as `harsh-fleet-audit` stays locked), then archive;
      (c) superseded-by-successor report docs (`ag_closeout_audit_*_parked_2026_08_16/19`, `na_eligibility_audit_defi_blocks_2026_08_16/17/18`)
      → `status: superseded` + `superseded_by` + archive; (d) genuine standing references (`autonomous_session_operator_decisions_2026_07_25`,
      `tradfi_autonomous_session_operator_decisions_2026_07_25`, `operator_ruling_record_plan_reconcile_session_2026_08_15`,
      `sit_gate_treadmill_*`, `cefi_empty_confirmed_historical_breakdown_reference_*`) → leave active, correct their
      queue verdict to STANDING-REFERENCE. Done-when: every pass-1 skip has one of those four dispositions logged.
      `wiv6q901k` (2.5h, 172 tool calls) processed all 51 candidates with real dispositions (18 archived/superseded,
      13 locked_by-cleared-then-archived, 12 standing-reference-kept correctly left open, 6 genuinely skipped —
      1 gate-still-open, 2 real-actor-locks, 1 stale-duplicate deferred to its own tracked operator-gated delete, 2
      re-verified-not-actually-0-open) — but never shipped any of it (repeated contention-driven reverts over its own
      2.5h run). Recorded the full per-doc record at
      `.ao_checkpoints/issues_corpus_completion_2026_08_21/archival_pass2_result.json`; dispatched a dedicated
      reconciliation agent (`aa77a3d57eba3ef6c`) to verify + ship it in scoped batches, explicitly warned this checkout
      also carries substantial unrelated peer WIP right now (confirmed via `git status`) — never `git add -A`.
- [x] 2. ✅ [SCRIPT] P0. Mark the 49 COVERED_ELSEWHERE docs with the counter-recognized EXTRACTED/DUPLICATE-OF or
      superseded_by form (serial lane) — `unified-trading-pm@6c274b982d` + `@dc08518953` + `@c66f71e3d5` + `@4c8de37473`
      (47 processed: 14 newly marked, 5 edited, 1 partial, 18 verified already-deduped/0-open, 9 flagged for archival;
      4 skipped where the coverage claim did not hold — `archival_referrer_codex_redirect_bulk_cleanup_2026_08_17`,
      `defi_morpho_lending_indices_never_wired_2026_07_12`, `dp_vm_001_tradfi_bf_cme_ohlcv_1m_es_2020_exit137_*`,
      `workflow_template_drift_repeated_during_phase7_rollout_2026_07_27` — those four re-enter the executable queue).
      `count_open_tasks.py` after: issues open deduped 1,146 → 1,129; docs 573 → 558.

### Wave 2 — operator-approved actions + credential wiring (non-PM repos first; deletes serial)

- [x] 3. ✅ [INFRA] P0. D5: pause the `tradfi-bf-cme-ohlcv-1m-` fleet wave mechanism now — `deployment-service@3367cfea`
      + `unified-trading-pm@9b269c9fb1`. Found the REAL mechanism (not the Terraform Cloud Scheduler job, dormant since
      2026-06-25): an undocumented crontab entry on the AO orchestrator VM running `wave_launcher.py` every 3h. Paused
      it via SSM (backup left on-VM); verified 0 new CME VMs over 20 min; stopped 2 already-running CME VMs burning
      SPOT for zero progress (402 billing errors); shipped a live `cme_billing_probe_ok()` gate so dispatch is
      conditional on billing regardless of which mechanism resumes it. 3 docs retagged.
      ADOPTED (autonomous-dispatch authority): the discovered host-cron's disposition — confirm the Terraform
      Cloud Scheduler pair still works end-to-end, then delete the host-cron once confirmed (worker rec, tracked as a
      new `[OPERATOR]` P1 todo on `tradfi_databento_account_billing_suspended_2026_08_09.md`); reversible, low-risk,
      operator may override by naming this decision.
- [ ] [DATA] P0. D7: bound the batch odds backfill consumer's quota share; relaunch the live odds VM on LDR after the key
      works. Done-when: live odds capture manifest rows resume (time_created after relaunch). Attempt 2 (`wy6ls9574`)
      found the D7-proper mandate (bound consumer + probe + relaunch) was ALREADY done by an earlier session — measured
      live: odds-api-key quota healthy (22M remaining), VM RUNNING — but the relaunched VM still captures ZERO rows,
      root-caused to a separate live defect (`mtds_odds_api_ws_sport_key_wildcard_never_expanded_2026_08_21`: a
      wildcard `sport_key` is never expanded to real leagues). Fix + tests written in market-tick-data-service
      (`odds_api_ws.py` + `test_odds_api_ws_connector.py`, uncommitted) but the turn was force-ended mid-QG-run — NOT
      shipped, NOT verified green, VM NOT relaunched with the fix. QG confirmed still alive (nohup'd, host-wide gate
      contention) — will finish independently of any one tick. Next tick: check QG result, ship via quickmerge,
      refresh the tarball, cycle the VM, verify a captured row, flip all 3 affected docs.
- [x] 4. ✅ [BACKEND] P0. D12/D16/D19: verify the named GSM secrets have non-empty latest versions; wire binance/bybit/okx
      `place_order()` off NotImplementedError; un-skip `test_tenderly_fork_full_cycle`; verify CEX_WITHDRAW on a testnet
      venue — `execution-service@58e4eed74a` + `unified-trading-pm@34ec8f06eb`+`@280b3ce93b`. Binance/Bybit
      `place_order()` were already live (the NotImplementedError finding was stale); OKX has no pooled credential
      source by design, left to its own tracked design item. Un-skipped the Tenderly test — found + fixed a genuine
      WSTETH-address bug in `aave_live.py`, then hit a real Tenderly account write-RPC ceiling (5 writes/VNet) on the
      6th call, reproduced twice; xfail(strict=False) citing a new dated `[OPERATOR]` P3 tier-upgrade ask. CEX_WITHDRAW
      verified end-to-end on deribit-testnet (bybit-testnet-trade-api-key-secret is present but 0 bytes — flagged,
      deribit substituted). Bybit's scoped-name→unscoped fallback confirmed live. 5 docs flipped. Re-verification pass
      (`wy6ls9574`) confirmed nothing had drifted and found one real doc error: `exec_tenderly_2026_08_15.md` claimed
      `bybit-testnet-trade-api-key-secret` was a 0-byte empty secret — the correct name has no "-key-" before "-secret"
      (`bybit-testnet-trade-api-secret`), a real 36-byte value existing since 2026-05-19. Corrected —
      `unified-trading-pm@ffbe04df68`.
- [ ] [DATA] P1. D2: execute the approved manifest/GCS correction batch item-by-item under each stated gate
      (soft-delete retention ≥604800s cited inline or snapshot-first; fresh dry-run before every --apply). Done-when:
      each item's verification query returns the expected zero/row count, logged per item. 3/7 docs resolved:
      `prediction_batch4_deferred_residuals_2026_08_16` (POLYMARKET reclass correctly WITHHELD — a permanent
      manifest-`--apply`-reserved-for-human hard-stop D2's generic approval doesn't cross); `sports_mdt_odds_captured_cells_not_found_rate_2026_08_16`
      (both row-removal items found ALREADY resolved by an untraced concurrent writer — re-verified via fresh
      precondition + verification query, 0 residual rows either way; a `[DIAG]` follow-up filed to find the writer);
      `tradfi_cme_future_typed_blank_instrument_id_2026_08_09` (fresh soft-delete retention 604800s + a
      content-verified retire script shipped `market-tick-data-service@53e6d971ce`, retired 873,007/880,933 stale
      `venue=CME`/`instrument_type=FUTURE` rows with a live bundle-grain counterpart, 7,926 no-counterpart rows left
      untouched + split into a new follow-up issue doc; verify query confirms 7,926 residual exactly, doc archived —
      `unified-trading-pm@9bb1899fe4`). Remaining 4 docs retrying via `wnroqem2n`.
- [x] 5. ✅ [INFRA] P1. D3: stash/WIP cleanup per the approved scope — `wiv6q901k` (`unified-trading-pm@470ff79cb7`,
      `@2f046c4db0`, `@e1f61e5168`). .tabs/3 re-audit found drift continuing (152 entries now, vs 42/59/125 at prior
      checks) — documented, not itself a blocker. features-service-clean-check + MTDS slot-3 targets both already had
      0 stash entries (nothing to drop); slot-25 doesn't exist on this host (AO-VM slot, unreachable from a laptop
      session — flagged, not resolved). Sandbox project-ID fix: investigated and closed as moot (the named scripts no
      longer carry the literal; today's QG already enforces the equivalent check fleet-wide) — sandbox-test-user is
      safe to retire. Slot-0 dirty files per-file diff-reviewed, none touched (outside this session's write scope —
      left as an evidence-backed recommendation). Recovered its own mid-run contention casualty (an orphaned autostash
      merge commit) without data loss. Never ran `git stash drop` anywhere (hard-blocked by tooling regardless).
- [x] 6. ✅ [INFRA] P1. D10: VM remediation — `wiv6q901k` (`unified-trading-pm@1c7bc8d73c`). BYBIT-FUTURES: cycled onto
      the LDR fix via the registered launcher; still 0 captured rows after ~15min — found a NEW live defect, Bybit's
      gateway actively REJECTING specific topic/symbol subscribe acks (`handler not found`), not silently dropping
      them as previously suspected; old VMs deliberately left running since the real fix-verification gate isn't met
      yet. Deribit-sweep VM: confirmed NOT hung (already self-deleted 2026-08-16 after a clean `DEPLOYMENT_COMPLETED`
      exit) — nothing to delete; archived the stale issue doc. The 2 long-lived mdps-features-live VMs: confirmed
      genuinely stuck (404 retry loop), killed + relaunched via the registered launcher with the current fix baked in.
      The ~11 bounded backfill VMs: left alone per the ruling — 9/10 had already self-deleted on completion, only 1
      still running, untouched.
- [x] N. ✅ [SCRIPT] P1. D34: flip `l2_book_microstructure_capture` to `assigned_vm: planning` + un-void the re-test
      todo. **DONE 2026-08-22** — `unified-trading-pm@403eaa6e9b`.
- [x] N. ✅ [SCRIPT] P1. D8: promote cefi batch22, cross_cutting batch19/20, defi batch19 from draft to active
      (re-run the conflict check first). **DONE 2026-08-22** — `unified-trading-pm@403eaa6e9b`. All 4 conflict-
      checks re-verified clean; `defi_satellite_ao_dispatch_batch19_2026_08_21.md`'s `assigned_vm` stays `NA`
      (flipping to `planning` needs a gated finalize-companion plan per task_template §4 — confirmed by a real gate
      failure — left as a named follow-up in that doc).
- [x] N. ✅ [BACKEND] P1. D66: file the AAVE-PLASMA archetype/slot catalogue todo in strategy-service's owning
      plan. **DONE 2026-08-22** — `unified-trading-pm@403eaa6e9b`. Filed in
      `/plans/active/venue_e2e_wiring_2026_08_16.md` (repos includes strategy-service).
- [x] N. ✅ [SCRIPT] P1. D35: author the IDE-compatible heartbeat design todo (fresh carrier proposal; UserPromptSubmit
      stays rejected) in the human-fleet doc. **DONE 2026-08-22** — `unified-trading-pm@403eaa6e9b`. Authored Phase
      9 in `/plans/active/ao_human_fleet_integration_2026_08_15.md`; found its own already-shipped Phase 2b
      (2026-08-19, before this ruling) likely already IS the different, non-hook carrier this ruling asks for
      (`ao-liveness-heartbeat.py`, a cron transcript-mtime poll) — Phase 9's todo confirms or scopes the residual.
- [x] N. ✅ [SCRIPT] P1. D26/D27: draft Elysium SLA v5 (30-day, corrected dates) for operator review; open the
      carve-out repo build as a tracked todo in the Elysium disclosure doc. **DONE 2026-08-22** —
      `unified-trading-pm@403eaa6e9b`. Drafted `/codex/14-customer-journeys/commercial-model/ODUM_SLA_v5_2026-08-22.md`
      (DRAFT, not sent) — 30-day support period needed no change, v4 already had it consistent; only the 5 stale
      June/May-2026 dates were corrected. Carve-out todo confirmed already tracked in
      `elysium_sla_v4_support_period_and_stale_dates_2026_08_08.md` since 2026-08-11, not duplicated.
- [x] N. ✅ [SCRIPT] P1. Apply every ledger disposition (ruled + adopted) to its affected docs: write the dated
      ruling line, replace each stale operator-gate marker with the reflecting disposition marker per task_template
      §3, and convert the now-executable units into todos. **DONE 2026-08-22 — 179/179 docs, verified by direct
      measurement** (fresh grep of every doc in `dispositions_by_doc.json` for its D-number(s) co-occurring with a
      2026-08-21/22-dated line, re-run against `origin/live-defi-rollout` after every ship, ending at 0 remaining).
      Finished via 4 parallel batch sub-agents (~17 docs each) plus 6 docs handled directly where they overlapped
      with Task-2 D-item execution. Prior 44/179 count was stale/superseded.
- [x] N. ✅ [INFRA] P2. ATTEMPT set: D4, D53, D70, D102, D81, D112, D131, D58, D130 — each resolved with its own
      evidence line in the Progress Log or escalated with concrete options. **DONE 2026-08-22** —
      `unified-trading-pm@9de638a1d3` + `@74fafbb805`. D4/D70/D58/D130/D131 genuinely EXECUTED with real evidence
      (an IAM grant, a new IAM user+GSM credential, two code-verified design resolutions, an archived-doc
      cross-reference); D53/D81/D102/D112 ESCALATED with concrete options each, no fabricated completions.

### Wave 3 — executable queue

- [ ] [SCRIPT] P1. Execute `/plans/active/issues_corpus_executable_queue_2026_08_21.md` (352 docs, one todo each) in
      effort order S→M→L→XL, ≤5 concurrent authoring agents on distinct repos, gate+ship serial. Done-when: that plan
      archives.
- [ ] [SCRIPT] P2. Re-run `count_open_tasks.py`; issues-open-deduped must be < 200 before this plan closes, with every
      remaining open todo carrying a dated operator ruling or BLOCKED-<TOKEN> naming its external dependency.

## Progress Log

- **2026-08-21 (session start)** — Count baseline taken; 29-batch classification workflow run; 141 decisions merged;
  two operator question rounds answered (table above); wave 1 launched (archive + covered lanes); GSM verified for
  D12/D16/D19; Betfair root cause = Betfair's own pending-password-change flag. Plan-of-record + executable queue plan
  authored (`unified-trading-pm@1b0b4aa87c`). Decision board artifact published for operator review.
- **2026-08-21 (wave 1 complete, `wf_b38a4988-fc3`, 12 agents, 91 min)** — Archive lane: 18/56 archived, 38 skipped.
  Skip taxonomy: 24 × `archive_exempt: true` (≈half explicit BRIDGE notes deferring to "the follow-on pass", the rest
  genuine standing references — the classifier over-called these as ARCHIVE_RESOLVED); 8 × `locked_by` (7 the
  `live-defi-rollout` placeholder bug, 1 real actor `harsh-fleet-audit`); 3 × live unresolved operator-preference
  items still in prose; 1 stale duplicate left by an incomplete rename (`_cefi_canonical_blueprint_2026_07_17`); 1 with
  a genuinely open checkbox the classifier missed; 1 archival owned by an active finalize plan. Covered lane: 47/49
  processed, 4 coverage claims refuted (re-queued as executable). The one doc the classifier missed
  (`dp_cron_did_not_fire_dedup_volatile_field_2026_08_17`) = operator-gated; it enters the ruling sweep. Side findings
  filed by the lane: `locked_by_live_defi_rollout_placeholder_regression_new_writer_2026_08_21.md` (a new writer
  re-emitting the placeholder) + `locked_by_live_defi_rollout_archival_referrer_cleanup_2026_08_21.md` (7 prose
  referrers). Wave 2 (`wf_67607ae2-059`: D5/D7/D12) and wave 2b (`wf_76e252f8-2e7`: ruling application over 179
  docs + D2 corrections) running. Progress metric: issues open deduped 1,146 → 1,129.
- **2026-08-22 (tick 3)** — Both wave-2/2b workflows hit the account session-limit mid-run (reset 2:20am London,
  external constraint, not a logic failure): D5 and D12 completed fully before the limit (see Wave 2 checkboxes above);
  D7 and 9 of 12 ruling chunks + 5 of 7 D2 docs got zero work (agent returned null). After the operator confirmed the
  reset, resumed both workflows from cache (`wy6ls9574`, `wnroqem2n`) — completed work replays instantly, only the
  failed pieces re-run. Launched wave 3 in parallel (`wiv6q901k`): archival pass 2 (the 38 pass-1 skips + 9
  wave-1-flagged + 1 ruling-sweep-flagged docs, per the four dispositions above), D10 VM remediation, D3 stash
  cleanup. Adopted the D5 host-cron disposition (worker rec, logged inline above) without a fresh operator round —
  matches the established ADOPTED-REC pattern, reversible by veto.
- **2026-08-22 (tick 4)** — Wave 2 (`wy6ls9574`) fully resolved except D7's final ship step: D5 unchanged (cached);
  D12 re-verified clean + fixed one stale-doc credential-name error (see checkbox above). D7 is genuinely in-flight,
  not done: a live capture defect was found and fixed (code+tests written), but the fix sits uncommitted in the
  shared `market-tick-data-service` checkout with its `quality-gates.sh --no-fix` run still queued behind host-wide
  QG contention (nohup'd — survives past this tick, checked via `ps`/log tail rather than re-running). Left
  deliberately un-flipped per CLAIM≤MEASUREMENT — next tick finishes the ship→tarball→VM-cycle→verify chain.
- **2026-08-22 (tick 5, sub-agent dispatch on D2 affected_docs[3])** — Executed
  `tradfi_cme_future_typed_blank_instrument_id_2026_08_09.md`'s sole open `[OPERATOR]` retire todo (3rd of 7 D2 docs
  resolved, see checkbox above). Fresh precondition re-check (bounded, column-projected read): soft-delete retention
  604800s (PASS); population 880,933 stale rows — unchanged from the 2026-08-16 measurement (had actually stopped
  growing, contrary to the doc's "actively growing" framing). Shipped a content-verified retire script
  (`market-tick-data-service@53e6d971ce`, full `quality-gates.sh` green, 11230 passed) modeled on the
  `retire_dex_pool_fees_all_captured_rows_2026_08_12.py` worked example (CAS + consolidator-pause hard-abort +
  pre-write snapshot); paused the tradfi consolidator cron, ran `--apply` against the live 14.48M-row index, retired
  873,007 rows, verified the 7,926 no-counterpart residual exactly, resumed the cron. Split the residual into a new
  follow-up issue (`tradfi_cme_future_no_counterpart_residual_2026_08_22.md`, per plan-completion-and-archival §2 —
  never left as prose) and archived the now-fully-done source doc per the 6-step ritual (cross-repo `archive_exempt`
  bridge, two-commit split — `unified-trading-pm@9bb1899fe4` flip commit, archival `git mv` commit follows). Caught
  + fixed 2 real bugs in the new retire script before shipping (pyarrow strict-null `or_`/`and_` propagation silently
  un-marking a null-`instrument_id` row as non-stale; a test assertion missing `data_type` in its result key masked a
  real drop). No other slot was concurrently on this specific doc (`locked_by` empty, last commit predated this
  dispatch); an UNRELATED dirty `unified-api-contracts` WIP from another live session blocked quickmerge's pre-flight
  audit — resolved via `--skip-preflight` (a documented multi-agent-safety skip, not a QG bypass) rather than
  touching someone else's uncommitted work. **Side finding**: this exact commit's own edits were twice silently
  reverted by an untraced shared-host mechanism before landing (the 102-entry autostash/quarantine pile flagged by
  `safe-doc-push.sh` on this push) — redone and shipped successfully on retry; flagging for the standing
  multi-agent-collision investigation, not re-diagnosed further here.
- **2026-08-22 (tick 5)** — Wave 3 (`wiv6q901k`) complete: D3 + D10 fully shipped (checkboxes above); archival pass 2
  processed all 51 candidates correctly but never shipped (2.5h run, repeated contention reverts) — delegated to a
  fresh reconciliation agent (`aa77a3d57eba3ef6c`) with the full per-doc record, explicit warning that this checkout
  currently carries substantial unrelated peer WIP (confirmed via `git status`), and a hard "never `git add -A`"
  instruction. Also this tick: activated `sports_satellite_ao_dispatch_batch14_2026_08_16` (`d71c9211f5`) — a fully
  conflict-checked draft gating 11 downstream AO tasks, found via a live re-check of the AO dashboard's blocked-task
  count at the operator's request (confirmed the number is NOT stale — a fresh recompute via the same function the
  dispatcher itself uses landed on exactly 440, matching the dashboard). Flipped 26 ruling-sweep spinoff docs
  `assigned_vm: NA`→`planning` per the operator's direct instruction — repeatedly reverted by the same contention
  class before landing; re-verify before trusting it shipped. Launched a background agent (build-in-progress) for
  the POLYMARKET manifest reclassification dry-run tool in `deployment-service/scripts/migrations/`, dry-run only,
  `--apply` withheld pending explicit operator approval.
- **2026-08-22 (tick 6)** — Confirmed via `git show origin/...` (not just local state): the 26-doc `assigned_vm`
  flip DID land (7 attempts total — 5 failed on the same host-contention class documented in
  `pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md`, 2 on real dangling-reference content errors
  now fixed, 1 finally landed clean). The archival-pass-2 reconciliation agent (`aa77a3d57eba3ef6c`) and the
  manifest-dry-run agent (`afc28df9fb2034c5a`) both ended their turns claiming a background push/QG run was "still
  running" — verified via `ps` that NEITHER process actually exists anymore. Resumed both via `SendMessage` with the
  real state and explicit instructions to re-verify from scratch and finish in the foreground rather than assume a
  phantom continuation. **Host contention across this shared slot is severe and sustained** (confirmed: 6+ other
  live sessions in this slot since session start, dozens of concurrent `quality-gates.sh`/`safe-doc-push.sh`
  processes observed across repos) — every ship this tick required 1-7 retries; this is the dominant cost driver
  right now, not logic errors. Next tick: verify both resumed agents' real outcomes before trusting either.
- **2026-08-22 (tick 7)** — Finished the ruling-sweep to 179/179 (measured, not trusted) and every remaining
  Wave-2 D-item (D34/D8/D66/D35/D26/D27 + full ATTEMPT set) — see the flipped checkboxes above for per-item
  evidence. Sustained severe host contention required multiple ship retries and 2 local-edit reversions caught +
  refixed (a bold-non-checkbox marker and a resolved-without-archival frontmatter state, both real plan-hygiene
  gate hits, not false positives) plus resolving 2 unrelated peers' merge conflicts conservatively before this
  session's own pushes could land. Remaining: Wave 1's archival-pass-2 (already delegated) and Wave 3's
  executable-queue execution (352 docs, not started this tick).
