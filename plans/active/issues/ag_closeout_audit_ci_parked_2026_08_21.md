---
doc_type: issue
title: ag-closeout-audit ci 2026-08-21 — orphan projection + parked findings
summary: >-
  2026-08-21 /ag-closeout-audit ci tranche Phase 1 audit (2 batches, 45 candidate docs). Compact orphan table.
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ag-closeout-audit, ci, orphan-projection]
related: [/plans/active/issues/ag_closeout_audit_cross_tranche_big_findings_2026_08_21.md, /plans/active/ci_consolidated_closeout_2026_07_25.md]
created: 2026-08-21
author: claude-session-2026-08-21
parent_epic: infrastructure_master
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
source: ["2026-08-21 — /ag-closeout-audit ci, 2 Phase-1 batches, 45 candidates"]
depends_on: []
context_scope: [/plans/active/issues/ag_closeout_audit_cross_tranche_big_findings_2026_08_21.md]
---

# ag-closeout-audit ci 2026-08-21

45 candidates, 2 batches. Counts: archivable_now 2 · archivable_after_planned_work 4 · orphaned_partial_coverage 9 ·
orphaned_never_touched 28 · exclude_cross_cutting 2.

## Orphaned — compact table

| Doc | Taxonomy |
|---|---|
| `ci_vm_exposure_remediation_2026_08_06.md` | fleet-wide CI concurrency cap, design question |
| `fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md` | visibility-change alert design |
| `capability_wizard_client_lite_and_ci_regen_followup_2026_07_24.md` | unscoped design call |
| `issues/agent_orchestrator_qg_cancel_notifier_same_sha_rerun_gap_2026_08_20.md` | 3 investigation todos |
| `issues/build_deploy_pipeline_provenance_and_aws_deferred_gaps_2026_07_21.md` | build_id ledger design |
| `issues/ci_alert_failure_resolution_linkage_2026_08_16.md` | ldr-ci-monitor linkage, operator-gated |
| `issues/ci_vm_io_starvation_audit_findings_and_optimization_2026_08_05.md` | fleet-wide CI concurrency cap (dup of ci_vm_exposure above) |
| `issues/cloud_build_router_failure_escalation_undercoverage_2026_08_16.md` | root-cause AO escalation-classifier gap |
| `issues/cloud_build_uac_publish_ordering_race_recurrence_2026_08_20.md` | fleet-level policy judgment |
| `issues/cloud_build_uac_publish_ordering_race_recurrence_strategy_service_2026_08_20.md` | BLOCKED-OPERATOR review |
| `issues/deployment_api_events_global_state_leak_flaky_metadata_probe_2026_08_06.md` | investigation |
| `issues/deployment_api_mtds_meta_missing_blocks_workspace_qg_step_5_83_2026_08_03.md` | architecture-tradeoff |
| `issues/deployment_service_basedpyright_ratchet_broken_by_dep_backmerge_2026_08_15.md` | BLOCKED-DECISION |
| `issues/ff_pull_fleet_drift_rca_2026_08_11.md` | real owner is `infra` tranche (per-tab-worktrees mechanics) |
| `issues/fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md` | RETRY_PER_TICK scaling design |
| `issues/fleet_wide_qg_cascade_pm_manifest_race_recurrence_2026_08_19.md` | secondary-priority confirmation |
| `issues/glue_runner_units_stopped_fleet_ci_outage_2026_08_04.md` | ✅ **EXTRACTED 2026-08-21 (Phase 3)** → `ci_satellite_ao_dispatch_batch17_2026_08_21.md` — the MISCLASSIFIED_LIKELY_AO_ELIGIBLE flag is now actioned (a starting threshold-N was supplied rather than treated as a permanent blocker) |
| `issues/image_build_validate_stranded_on_deregistered_glue_runners_2026_08_07.md` | design question |
| `issues/ldr_to_main_promote_fleet_queued_run_cancelled_livelock_2026_08_07.md` | time-gated GitHub retention retry |
| `issues/mdps_qg_tests_slice_oserror_cannot_send_recurrence2_2026_08_19.md` | conditional (3rd occurrence trigger) |
| `issues/mtds_is_historical_quickmerge_bypass_backlog_2026_08_16.md` | 2 OPERATOR decisions + gated script |
| `issues/na_corpus_ratchet_diff_base_vs_lagging_main_deadlocks_promotion_2026_08_10.md` | re-gate-design + kill-switch-journey |
| `issues/plan_reconciler_findings_ci_2026_08_19.md` | archivable_now — completed run-journal |
| `issues/post_cutover_silent_assumption_sweep_2026_07_23.md` | dead trading kill-switch (P0, correctly time-gated), tag-reconciliation stall |
| `issues/pytest_timeout_60s_flaky_under_contention_2026_07_29.md` + continued/continued2/continued3 | chain founding doc's 14-day monitoring window closed 2026-08-20 — archival action itself untracked; **fresh recurrences found 2026-08-19/20 outside the chain**, "self-resolves" claim NOT supported |
| `issues/quickmerge_environment_autodetect_forces_dev_off_main_2026_07_25.md` | design call |
| `issues/quickmerge_sentinel_race_retry_storm_under_pm_doc_push_contention_2026_07_21.md` | "do NOT dispatch blind" banner |
| `issues/todo_cancelled_disposition_format_breaks_todo_regression_check_2026_08_09.md` | real owner audit trail logged under `ao` |
| `issues/unified_trading_ci_ff_pull_cron_branch_override_gap_2026_08_17.md` | real owner audit trail logged under `ao` |
| `qg_host_adaptive_resource_governor_2026_07_14.md` | 3 open findings: pytest-xdist worker-death, MAX_DURATION/PYRIGHT_TIMEOUT scaling, AO/glue-runner ledger unification |
| `test_impact_fleet_wide_measurement_and_rollout_2026_08_03.md` | fleet-wide evidence-sufficiency, likely permanent human judgment |
| `workflow_template_drift_repeated_during_phase7_rollout_2026_07_27.md` | 8 consecutive KEEP-NA, escalated via ag_closeout_audit_ci_parked's own todos |

## Mechanical hygiene flags

- `github_actions_operator_gated_followups_2026_07_17.md` STEP 2d: gated on "digest-drift-sweep's dormant primary
  cascade" being open, but `plan_reconciler_findings_ci_2026_08_19.md` already found this premise empirically
  false (cascade resumed firing) and closed the real target doc — citation never back-propagated.
- Two stuck cross-tranche retags sat 5+ days: `ff_pull_fleet_drift_rca_2026_08_11.md` (drop `ci` tag),
  `todo_cancelled_disposition_format_breaks_todo_regression_check_2026_08_09.md` (resolve `[ci, ao]` dual-tag) —
  each candidate tranche correctly declines to write a tag it isn't sure is theirs; nobody owns the fix.
- Duplicate dispatch risk: "add `detect_template_drift.py --workflows --repo <self>`" for `unified-api-contracts`
  tracked in BOTH `unified_api_contracts_image_build_gate_template_lag_blocks_all_pm_commits_2026_08_14.md` (self-
  dispatched) AND `ci_satellite_ao_dispatch_batch15_2026_08_16.md` line ~267 — check before either ships.
- `sit_gate_treadmill_recurs_under_high_ldr_velocity_2026_08_08.md` confirmed extracted verbatim into
  `ci_satellite_ao_dispatch_batch16_2026_08_21.md` todo 2 — correctly covered, not orphaned.

## Progress Log

- **2026-08-21**: Doc created directly from the 2026-08-21 /ag-closeout-audit ci Phase-1 sweep (2 batches). No
  mechanical fixes applied yet.
- **2026-08-21 (Phase 3, AO-dispatch batch drafting)**: re-verified this doc's own mechanical-hygiene flags —
  the STEP 2d/D3 stale-citation issue was already corrected (confirmed live in
  `github_actions_operator_gated_followups_2026_07_17.md`'s D3 table, dated 2026-08-21); the `ff_pull_fleet_drift_
  rca_2026_08_11.md` and `todo_cancelled_disposition_format_breaks_todo_regression_check_2026_08_09.md` stale
  cross-tranche `ci` tags were also already dropped (both docs' live `asset_group`/tags confirmed clean of `ci`).
  Read 3 of the ~28 `orphaned_never_touched` rows in full: 1 genuinely bounded item found and extracted
  (`glue_runner_units_stopped_fleet_ci_outage_2026_08_04.md`'s sole remaining monitoring-gap todo, previously
  self-flagged `MISCLASSIFIED_LIKELY_AO_ELIGIBLE` 2x without ever being extracted) →
  `ci_satellite_ao_dispatch_batch17_2026_08_21.md`. `mdps_qg_tests_slice_oserror_cannot_send_recurrence2_2026_08_19.md`
  re-confirmed still conditional (3rd-occurrence trigger not yet met); `pytest_timeout_60s_flaky_under_contention_
  2026_07_29.md` re-confirmed already `assigned_vm: planning` (not a true NA orphan — it's live-dispatchable
  through the normal backlog already, no extraction needed). Did NOT reach the remaining ~25 orphan rows —
  explicitly not exhaustively re-verified this pass.
