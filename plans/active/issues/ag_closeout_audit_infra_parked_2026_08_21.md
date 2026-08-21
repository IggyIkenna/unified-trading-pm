---
doc_type: issue
title: ag-closeout-audit infra 2026-08-21 — orphan projection + parked findings
summary: >-
  2026-08-21 /ag-closeout-audit infra tranche Phase 1 audit (3 batches, 69 candidate docs). Compact orphan table.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ag-closeout-audit, infra, orphan-projection]
related: [/plans/active/issues/ag_closeout_audit_cross_tranche_big_findings_2026_08_21.md, /plans/active/infra_consolidated_closeout_2026_07_25.md]
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
source: ["2026-08-21 — /ag-closeout-audit infra, 3 Phase-1 batches, 69 candidates"]
depends_on: []
context_scope: [/plans/active/issues/ag_closeout_audit_cross_tranche_big_findings_2026_08_21.md]
---

# ag-closeout-audit infra 2026-08-21

69 candidates, 3 batches. Counts: archivable_now 5 · archivable_after_planned_work 20 · orphaned_partial_coverage 5
· orphaned_never_touched 36 · exclude_cross_cutting 5.

**Escalation-worthy infra findings already in the cross-tranche big-findings doc**: item 11 (safe-doc-push.sh,
8+ incidents), item 12 (git-stash-race, 6+ repros).

## Orphaned — compact table

| Doc | Taxonomy |
|---|---|
| `ao_ci_aws_to_ionos_migration_2026_08_18.md` | ~15 items, human plan (migrates the AO host itself) |
| `codex_violations_ratchet_to_five_2026_06_10.md` | Phase 3 schema-provenance migration, needs dedicated design pass |
| `compute_flexible_cud_sizing_analysis_2026_08_16.md` | 2 date-gated re-checks (~1-2wk, ≥2026-09-15) |
| `deployment_network_egress_ingress_observability_2026_08_18.md` | gated on GCP support case (Flow Logs anomaly) |
| `issues/agent_orchestrator_pytest_cov_silent_death_under_host_load_2026_08_20.md` | wire workaround into QG permanently |
| `issues/agent_orchestrator_qg_baseline_stale_cgroup_kill_2026_08_20.md` | RSS-doubling investigation |
| `issues/agent_orchestrator_quickmerge_orphan_reap_kills_interactive_background_2026_08_20.md` | **live infra hazard**: any quickmerge/QG run near ~340s can silently die (tmux-session exemption doesn't fire for interactive sessions) |
| `issues/autostash_pop_can_silently_discard_uncommitted_foreign_edits_2026_08_07.md` | see cross-tranche big findings item 12 |
| `issues/check_line_caps_sh_whitespace_only_exemption_false_positive_2026_08_19.md` | frontmatter/claim mismatch (see hygiene flags) |
| `issues/claude_settings_symlink_writeback_drops_hooks_2026_08_11.md` | DISABLE_AUTOUPDATER policy tradeoff |
| `issues/deployment_service_client_broken_functions_2026_08_20.md` | 9 live-broken function fixes + 2 dead-code removals |
| `issues/deployment_service_preexisting_qg_failures_sync_configs_hardcoded_project_id_2026_08_19.md` | prose-only remaining work (never converted to `- [ ]`) |
| `issues/deployment_service_prod_terraform_drift_2026_08_07.md` | forward-pointer to t1_recon duplicate-module doc |
| `issues/deployment_service_t1_recon_duplicate_module_definitions_2026_08_09.md` | canonical-module choice + import env-gating risk |
| `issues/dp_live_003_agent_orch_aws_credentials_gap_2026_08_10.md` | credential-provisioning architecture call |
| `issues/ff_pull_fleet_drift_rca_2026_08_11.md` | uv.lock auto-clean scope + bulk-clean 43 archived repos |
| `issues/gcp_service_accounts_registry_diverged_from_live_provisioning_2026_07_31.md` | large-scope provisioning/redeploy remainder |
| `issues/gitignore_sync_script_destructive_due_to_stale_central_template_2026_07_27.md` | human diffing judgment |
| `issues/issue_docs_remediation_sweep_2026_06_02.md` | UAC axis classification, MTDS reconciliation, 2 operator tofu-apply items |
| `issues/lc_verify_tarball_freshness_auto_mode_silent_dirty_skip_2026_08_06.md` | design consideration |
| `issues/mac_slot0_base_checkout_stuck_dirty_files_2026_08_11.md` | commit-vs-discard OPERATOR call |
| `issues/manual_launcher_shard_dedup_gap_167_of_187_2026_08_15.md` | non-bounded, needs its own plan |
| `issues/mtds_live_vm_tarball_freshness_default_proposal_2026_08_16.md` | auto-vs-enforce policy |
| `issues/plan_quality_four_line_defense_architecture_2026_07_23.md` | 2 non-bounded design forks |
| `issues/prod_terraform_drift_backlog_reconcile_2026_07_24.md` | crash-loop alert policy residual moved to `cloud_run_crash_loop_alert_policy_invalid_metric_2026_08_20.md` (checkbox never split to reflect it) |
| `issues/safe_doc_push_extreme_stash_quarantine_drops_renamed_file_content_2026_08_15.md` + `_prek_patch_orphaned_recurrence` + `_stash_pileup_quarantine_drops_renamed_path` + `_unrecognized_flag_silently_becomes_branch_name` | see cross-tranche big findings item 11 |
| `issues/session_bound_vm_monitoring_reliability_gap_2026_07_26.md` | PREEMPTED marker grace-period design |
| `issues/shared_host_gcloud_active_account_cross_slot_clobber_2026_08_04.md` | per-slot named gcloud configs (fix-direction 1 already shipped via batch18) |
| `issues/slot7_unified_trading_ci_foreign_slot12_commit_wrong_branch_2026_08_14.md` | forensic investigation |
| `issues/utl_gcs_client_upload_from_string_silent_write_failure_2026_08_18.md` | 16 files/22 call sites still carry the bug pattern, AO-vs-human dispatch-scope decision blocking |
| `issues/vm_launcher_class_b_no_stall_kill_gap_2026_07_27.md` | whole-fleet blast-radius judgment, repeatedly rejected as out-of-scope |
| `manifest_consolidator_and_lifecycle_cost_optimization_2026_08_16.md` | cost-gain re-check (time-gated), cold-start investigation, periodic OOM re-check |
| `na_docs_validity_and_ao_eligibility_audit_2026_07_26.md` | see cross-tranche big findings item 13 |
| `repo_scripts_governance_audit_2026_06_18.md` | campaign-gated Delete-EXECUTION remainder + enforcement-wiring |
| `stash_pile_workspace_cleanup_2026_06_03.md` | destructive stash mutation + laptop-only sweeps, non-batchable by policy |

## Mechanical hygiene flags

- `check_line_caps_sh_whitespace_only_exemption_false_positive_2026_08_19.md`: `infra_satellite_ao_dispatch_batch1_2026_08_21.md`'s
  own conflict-check text claims this doc was "independently RECLASSIFIED to `assigned_vm: planning`" but its live
  frontmatter still reads `assigned_vm: NA` — reclassification never landed or reverted, needs a direct fix.
- `deployment_service_preexisting_qg_failures_sync_configs_hardcoded_project_id_2026_08_19.md`: zero checkbox syntax
  anywhere despite explicit "still open" prose — HARD RULE violation, convert to a real `- [ ]`.
- `agent_orchestrator_quickmerge_orphan_reap_kills_interactive_background_2026_08_20.md` cluster (with
  `agent_orchestrator_qg_baseline_stale_cgroup_kill_2026_08_20.md` and the pytest-cov doc): same 2026-08-20 evening,
  same shared host — a live "any full quickmerge/QG run near/above ~340s silently dies" condition, worth flagging
  fleet-wide (affects any agent's shipping attempt, not just AO's own).

## Progress Log

- **2026-08-21**: Doc created directly from the 2026-08-21 /ag-closeout-audit infra Phase-1 sweep (3 batches). No
  mechanical fixes applied yet.
