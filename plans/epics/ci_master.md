---
doc_type: epic
title: CI Master — GitHub Actions delivery pipeline, quickmerge/ship scripts, LDR→main promotion gate set
summary:
  L4 cross-cutting epic owning the fleet's GitHub Actions CI/CD delivery pipeline — quickmerge/safe-doc-push ship
  scripts, the LDR→main promotion gate set (sit-gate/fleet-green, quality-gates-v2, quickmerge-provenance),
  workflow-template rollout + self-hosted-runner capacity, semver-agent release tagging, and Cloud Build/Cloud Run
  deploy verification. Carved out of infrastructure_master 2026-08-18 (see Codex SSOTs).
status: active
nature: process
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator, unified-trading-ci, unified-api-contracts]
scope: [engineer, admin]
tags: [ci, cicd, quickmerge, github-actions, promotion, sit-gate, quality-gates-v2, self-hosted-runner]
related:
  [
    /codex/08-workflows/ci-cd-flow.md,
    /codex/12-agent-workflow/host-concurrency-and-commit-provenance.md,
    /codex/04-architecture/ci-alerting.md,
    /codex/11-project-management/epic-taxonomy-2026-08-18.md,
    /plans/active/epic_taxonomy_restructure_and_html_reconcile_2026_08_18.md,
  ]
created: 2026-08-18
name: ci_master
tier: L4
priority: P0
assigned_vm: NA
parent: master_to_live_defi_2026_05_23
co_operators:
codex_ssots:
  - /codex/08-workflows/ci-cd-flow.md
  - /codex/12-agent-workflow/host-concurrency-and-commit-provenance.md
  - /codex/04-architecture/ci-alerting.md
  - /codex/05-infrastructure/per-tab-worktrees.md
related_plans:
  - ../active/ci_consolidated_closeout_2026_07_25.md
  - ../active/ci_pipeline_speed_and_cost_redesign_2026_08_05.md
  - ../active/ci_satellite_ao_dispatch_batch13_2026_08_13.md
  - ../active/ci_satellite_ao_dispatch_batch13_2026_08_13_finalize.md
  - ../active/ci_satellite_ao_dispatch_batch15_2026_08_16.md
  - ../active/ci_satellite_ao_dispatch_batch15_2026_08_16_finalize.md
  - ../active/ci_tranche_zero_checkbox_archive_sweep_2026_08_18.md
  - ../active/ci_tranche_zero_checkbox_archive_sweep_2026_08_18_finalize.md
  - ../active/ci_vm_exposure_remediation_2026_08_06.md
  - ../active/fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md
  - ../active/issues/ag_closeout_audit_ci_parked_2026_08_16.md
  - ../active/issues/autostash_pop_can_silently_discard_uncommitted_foreign_edits_2026_08_07.md
  - ../active/issues/breaking_change_differ_blind_to_registry_data_dicts_2026_07_09.md
  - ../active/issues/build_deploy_pipeline_provenance_and_aws_deferred_gaps_2026_07_21.md
  - ../active/issues/ci_alert_failure_resolution_linkage_2026_08_16.md
  - ../active/issues/ci_reconcile_overnight_batch_2026_08_11.md
  - ../active/issues/ci_reconciler_ikenna_worker_ssm_permission_gap_2026_08_16.md
  - ../active/issues/ci_registry_drift_uac_utl_stale_tag_version_conflict_2026_07_26.md
  - ../active/issues/ci_vm_io_starvation_audit_findings_and_optimization_2026_08_05.md
  - ../active/issues/cloud_build_router_failure_escalation_undercoverage_2026_08_16.md
  - ../active/issues/cloud_build_router_fallback_region_same_as_primary_2026_08_14.md
  - ../active/issues/cloud_run_traffic_pin_silent_freeze_alert_wiring_2026_08_05.md
  - ../active/issues/deployment_api_events_global_state_leak_flaky_metadata_probe_2026_08_06.md
  - ../active/issues/digest_drift_sweep_silent_noop_github_token_scope_2026_07_16.md
  - ../active/issues/features_service_clean_check_dangling_fleet_ci_dedup_revert_2026_08_07.md
  - ../active/issues/ff_pull_fleet_drift_rca_2026_08_11.md
  - ../active/issues/fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md
  - ../active/issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md
  - ../active/issues/ibkr_gateway_infra_release_tag_stall_2026_08_11.md
  - ../active/issues/image_build_validate_stranded_on_deregistered_glue_runners_2026_08_07.md
  - ../active/issues/instruments_service_defi_golden_red_capability_drift_2026_08_14.md
  - ../active/issues/ldr_docs_gate_red_but_silent_inherited_e_aborts_verdict_2026_08_10.md
  - ../active/issues/ldr_docs_gate_red_but_silent_inherited_e_aborts_verdict_2026_08_10_finalize_2026_08_17.md
  - ../active/issues/ldr_to_main_promote_fleet_queued_run_cancelled_livelock_2026_08_07.md
  - ../active/issues/main_backmerge_to_ldr_no_retry_safety_net_for_non_pm_repos_2026_08_18.md
  - ../active/issues/main_ldr_backmerge_silently_reapplies_collateral_frontmatter_deletion_2026_08_17.md
  - ../active/issues/mtds_is_historical_quickmerge_bypass_backlog_2026_08_16.md
  - ../active/issues/mtds_ldr_cloud_build_docker_step6_failure_2026_08_10.md
  - ../active/issues/plan_reconciler_findings_ci_2026_08_10.md
  - ../active/issues/plan_reconciler_findings_ci_2026_08_16.md
  - ../active/issues/pm_version_split_blocks_all_quickmerge_code_commits_2026_08_10.md
  - ../active/issues/promote_pr_non_supersession_after_greeks_service_fix_2026_08_18.md
  - ../active/issues/qg_sentinel_environment_blind_2026_07_23.md
  - ../active/issues/quickmerge_isolated_worktree_missing_sibling_pm_checkout_2026_08_10.md
  - ../active/issues/quickmerge_setup_bootstrap_loop_blocks_commit_2026_08_09.md
  - ../active/issues/safe_doc_push_unrecognized_flag_silently_becomes_branch_name_2026_08_18.md
  - ../active/issues/semver_agent_squash_promote_blind_to_patch_fixes_2026_08_07.md
  - ../active/issues/silent_failures_surfacing_as_generic_promotion_lag_2026_07_17.md
  - ../active/issues/sit_gate_treadmill_recurs_under_high_ldr_velocity_2026_08_08.md
  - ../archive/2026_08/issues/sit_stamp_dispatch_503_false_positive_2026_08_17.md
  - ../active/issues/strategy_service_ldr_qg_infra_flake_and_promotion_deadlock_2026_08_06.md
  - ../active/issues/uac_value_only_config_change_breaks_utl_untested_2026_07_20.md
  - ../active/issues/unified_api_contracts_image_build_gate_template_lag_blocks_all_pm_commits_2026_08_14.md
  - ../active/issues/unified_api_contracts_image_build_gate_template_lag_blocks_all_pm_commits_2026_08_14_finalize_2026_08_18.md
  - ../active/issues/unified_trading_ci_ff_pull_cron_branch_override_gap_2026_08_17.md
  - ../active/issues/uv_version_pin_live_ci_reusable_workflow_still_hardcoded_2026_08_09.md
  - ../active/issues/workflow_template_drift_repeated_during_phase7_rollout_2026_07_27.md
  - ../active/issues/workflow_template_runs_on_placeholder_prettier_mangled_fleetwide_2026_08_07.md
last_updated: 2026-08-20
locked_by:
locked_since:
execution_scope: local-only
drift_direction: advance-code
depends_on: []
---

# CI Master — GitHub Actions delivery pipeline, quickmerge/ship scripts, LDR→main promotion gate set

## Report

Live HTML ledger: https://claude.ai/code/artifact/b5491741-4a60-494b-be4d-0e44b5d01830 (generated 2026-08-18,
`/plan-reconcile ci_master`) — link recovered 2026-08-19 during the Phase 6 link-collection sweep; this epic's own
`## Report` section was missing despite the report having been published and the HTML file shipped (`580a772372`).

## Why this epic exists

Created 2026-08-18 as part of the epic-taxonomy restructure (`/codex/11-project-management/epic-taxonomy-2026-08-18.md`)
— `infrastructure_master` had absorbed 296/833 (35.5%) of all corpus `parent_epic` references despite its own summary
framing it narrowly, and no epic owned the CI/CD delivery pipeline directly even though it was one of the two largest
distinguishable content clusters inside that catch-all. This epic is that carve-out: everything about the mechanism
that gets a commit from a developer's tree onto `main` and keeps that pipeline healthy — quickmerge/safe-doc-push, the
LDR→main gate set, GitHub Actions workflow templates, self-hosted runners, release tagging, and Cloud Build/Cloud Run
deploy verification (explicitly filed under "CI verification after every push" in CLAUDE.md, not treated as a separate
deployment-infra concern).

**What stayed with `security_and_cross_cutting_master` (the renamed `infrastructure_master` remainder) instead**:
quality-gates.sh's own STATIC-CHECK/ratchet content (basedpyright ratchet, codex-freshness ratchet, the "no broad
except" gate blind spot, NA-corpus ratchet) — these are coding-standards-debt / QG-execution-environment concerns
(the same script also runs in CI, but the doc's own subject is the debt ceiling or the local check, not the delivery
pipeline mechanism). Also VM/backfill/data-pipeline incident docs that merely mention CI/quickmerge in passing while
being fundamentally about asset-group data content stayed put — this restructure does not reassign asset-group-primary
docs to their natural asset-group epic, only carves CI and UAC content out of `infrastructure_master`.

## Scope

- **Ship scripts** — `quickmerge.sh` (the two-pass gate-then-land mechanism, `--isolated` worktree mode, the
  bootstrap/setup.sh re-entry path, the autostash/rebase-reconcile recipe) and `safe-doc-push.sh` (the doc-only ship
  path). Both are the ONLY sanctioned way code/docs reach LDR — a raw `git push` is banned.
- **The LDR→main promotion gate set** — `sit-gate/fleet-green` (fleet-shared SIT signal), `quality-gates-v2` (the
  promote-PR GitHub Actions check), and `quickmerge-provenance` (commit-trailer verification). Includes the
  `ldr-to-main-promote-fleet` / PM `ldr-to-main-promote` scheduled-promotion workflows, `main-backmerge-to-ldr`, and
  the `sit-stamp` dispatch mechanism.
- **GitHub Actions workflow infrastructure** — the `unified-trading-ci` reusable-workflow repo, per-repo workflow
  template rollout (`rollout-workflow-templates.sh`) and its drift/parity gate, self-hosted-runner provisioning +
  capacity (the CI VM, `image-build-validate.yml` runner registration), and the dedicated CI-escalation runner.
- **Release tagging** — `semver-agent` (tag minting on `push:[main]`), `reconcile_release_tags.py` (stall detector),
  and the wheel-publish pipeline.
- **Cross-repo breaking-change detection** — `detect_breaking_change.py` (the AST differ) and its known blind spots
  (registry-VALUE edits, not just symbol/signature changes) — the class of bug where a UAC content change reaches
  `main` with no cross-repo gate examining it.
- **Cloud Build / Cloud Run deploy verification** — the `cloud-build-router` (regional fallback, per-repo triggers),
  image-build-gate template parity, and the "green deploy ≠ live traffic" Cloud Run revision-pin class of failure.

## Current state (as of the 2026-08-18 carve-out)

The 58 docs assigned to this epic skew heavily toward **live incident/postmortem docs** (issue-type, `status: open`)
rather than long-running build-out plans — this domain is mostly firefighting an already-shipped pipeline, not
building a new one. Recurring failure classes visible across the corpus at carve-out time:

- **Self-hosted-runner capacity** — `fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27` +
  `_continues_day2_2026_07_29` + `ci_vm_io_starvation_audit_findings_and_optimization_2026_08_05` +
  `ci_vm_exposure_remediation_2026_08_06` are one connected incident: the fleet-wide `quality-gates-v2`
  self-hosted-runner flip outran the documented operator-paced capacity plan, causing I/O starvation on the dedicated
  CI VM; the audit + remediation plans are the fix-forward.
- **Promotion-pipeline livelock/flake** — `ldr_to_main_promote_fleet_queued_run_cancelled_livelock_2026_08_07`,
  `strategy_service_ldr_qg_infra_flake_and_promotion_deadlock_2026_08_06`,
  `sit_gate_treadmill_recurs_under_high_ldr_velocity_2026_08_08`, and
  `silent_failures_surfacing_as_generic_promotion_lag_2026_07_17` all describe the same shape: the promotion pipeline's
  single-concurrency-group / gate-treadmill design starves or misreports under real multi-agent fleet load.
- **Workflow-template drift** — `workflow_template_drift_repeated_during_phase7_rollout_2026_07_27`,
  `workflow_template_runs_on_placeholder_prettier_mangled_fleetwide_2026_08_07`, and
  `fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06` track the ongoing per-repo→reusable-workflow
  consolidation and its recurring parity-drift failure mode (prettier mangling template placeholders fleet-wide).
- **Release tagging stalls** — `ibkr_gateway_infra_release_tag_stall_2026_08_11` and
  `semver_agent_squash_promote_blind_to_patch_fixes_2026_08_07` both root-cause to semver-agent silently minting zero
  tags under specific commit-shape conditions.
- **Cross-repo gate blind spots** — `breaking_change_differ_blind_to_registry_data_dicts_2026_07_09` and
  `uac_value_only_config_change_breaks_utl_untested_2026_07_20` are the same underlying class: `detect_breaking_change.py`
  and SIT are both name/signature-only, so a UAC registry VALUE edit (not a symbol removal) reaches `main` with zero
  cross-repo gate examining it — a real, still-open coverage gap.
- **Ship-script mechanism bugs** — `quickmerge_isolated_worktree_missing_sibling_pm_checkout_2026_08_10`,
  `quickmerge_setup_bootstrap_loop_blocks_commit_2026_08_09`, `qg_sentinel_environment_blind_2026_07_23`,
  `pm_version_split_blocks_all_quickmerge_code_commits_2026_08_10`,
  `safe_doc_push_unrecognized_flag_silently_becomes_branch_name_2026_08_18`, and
  `autostash_pop_can_silently_discard_uncommitted_foreign_edits_2026_08_07` are direct bugs in the quickmerge /
  safe-doc-push mechanism itself.
- **The two active build-out plans** — `ci_consolidated_closeout_2026_07_25` (quickmerge / Cloud Build / GitHub
  Actions / SIT-promotion consolidated close-out, REVIVED 2026-08-10) and
  `ci_pipeline_speed_and_cost_redesign_2026_08_05` (fast LDR→main target + needs-driven cross-repo triggering + cost
  right-sizing) are the two largest non-incident plans, each already `active` with a real estimate.
- **Recurring housekeeping** — the `ci_satellite_ao_dispatch_batch*` / `ci_tranche_zero_checkbox_archive_sweep` /
  `plan_reconciler_findings_ci_*` / `ag_closeout_audit_ci_parked_*` family are the standing AO-dispatch-batch and
  `/plan-reconcile ci` / `/ag-closeout-audit ci` tranche outputs — this epic inherits the "ci" tranche's existing
  audit cadence unchanged, it just now has a real epic home instead of `infrastructure_master`.

## Assigned active plans

_58 active plans/issues declare `parent_epic: ci_master` in their frontmatter (carved from `infrastructure_master`
2026-08-18). Workers pick up in priority order (P0 first)._

<!-- prettier-ignore-start -->

## P0 — must complete before next foundation gate

### [`ci_vm_io_starvation_audit_findings_and_optimization_2026_08_05`](../active/issues/ci_vm_io_starvation_audit_findings_and_optimization_2026_08_05.md)
**status**: open
**title**: CI VM cost + I/O audit — verified findings, corrected root cause, and the path to downsizing the dedicated CI VM

### [`fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27`](../active/issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md)
**status**: open
**title**: Fleet-wide quality-gates-v2 self-hosted-runner flip already landed on 19/24 repos, ahead of the documented operator-paced capacity plan

### [`image_build_validate_stranded_on_deregistered_glue_runners_2026_08_07`](../active/issues/image_build_validate_stranded_on_deregistered_glue_runners_2026_08_07.md)
**status**: open · **estimate**: 0.1 cal AI-days (class: infra)
**title**: image-build-validate.yml (unified-trading-ci) hardcoded self-hosted [self-hosted, glue] runners that were deregistered

### [`strategy_service_ldr_qg_infra_flake_and_promotion_deadlock_2026_08_06`](../active/issues/strategy_service_ldr_qg_infra_flake_and_promotion_deadlock_2026_08_06.md)
**status**: open · **estimate**: 0.2 cal AI-days (class: refactor)
**title**: strategy-service LDR→main promotion: quality-gates-v2 "red" on promote PR #490 was a CI infra flake

## P1 — important; post-current-gate

### [`autostash_pop_can_silently_discard_uncommitted_foreign_edits_2026_08_07`](../active/issues/autostash_pop_can_silently_discard_uncommitted_foreign_edits_2026_08_07.md)
**status**: open
**title**: A concurrent `git pull --rebase --autostash` can silently discard another session's uncommitted foreign WIP

### [`breaking_change_differ_blind_to_registry_data_dicts_2026_07_09`](../active/issues/breaking_change_differ_blind_to_registry_data_dicts_2026_07_09.md)
**status**: open
**title**: Breaking-change differ is blind to UAC registry data-dicts — a consumer-breaking value edit promotes LDR→main with no cross-repo gate

### [`ci_consolidated_closeout_2026_07_25`](../active/ci_consolidated_closeout_2026_07_25.md)
**status**: active · **estimate**: 4.0 cal AI-days (class: infra)
**title**: CI/CD consolidated close-out — quickmerge, Cloud Build, GitHub Actions, SIT/promotion pipeline

### [`ci_pipeline_speed_and_cost_redesign_2026_08_05`](../active/ci_pipeline_speed_and_cost_redesign_2026_08_05.md)
**status**: active · **estimate**: 3.2 cal AI-days (class: infra)
**title**: CI pipeline redesign — fast LDR→main (3-5min target), needs-driven cross-repo triggering, cost right-sizing

### [`ci_reconcile_overnight_batch_2026_08_11`](../active/issues/ci_reconcile_overnight_batch_2026_08_11.md)
**status**: open
**title**: /ci-reconcile overnight batch — 17-item CI/CD alert reconciliation

### [`ci_vm_exposure_remediation_2026_08_06`](../active/ci_vm_exposure_remediation_2026_08_06.md)
**status**: active · **estimate**: 0.8 cal AI-days (class: infra)
**title**: Close the 3 remaining exposure items from the CI VM I/O-starvation audit

### [`cloud_build_router_failure_escalation_undercoverage_2026_08_16`](../active/issues/cloud_build_router_failure_escalation_undercoverage_2026_08_16.md)
**status**: open
**title**: `cloud_build_router_failure` AO wall_type fired for only 1 of 5 repos hit by the identical UAC cascade

### [`digest_drift_sweep_silent_noop_github_token_scope_2026_07_16`](../active/issues/digest_drift_sweep_silent_noop_github_token_scope_2026_07_16.md)
**status**: open
**title**: digest-drift-sweep has been a silent no-op since birth — `secrets.GITHUB_TOKEN` cannot read another repo's contents

### [`ff_pull_fleet_drift_rca_2026_08_11`](../active/issues/ff_pull_fleet_drift_rca_2026_08_11.md)
**status**: open · **estimate**: 0.4 cal AI-days (class: infra)
**title**: FF-pull fleet drift RCA — actor/detector collision divergence + a false "cron is broken" diagnosis

### [`fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29`](../active/issues/fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md)
**status**: open
**title**: Fleet-wide QG self-hosted-runner capacity crisis, day 2

### [`instruments_service_defi_golden_red_capability_drift_2026_08_14`](../active/issues/instruments_service_defi_golden_red_capability_drift_2026_08_14.md)
**status**: open
**title**: instruments-service defi expected-universe GOLDEN test red again — blocks fleet-wide instruments-service quickmerge

### [`ldr_docs_gate_red_but_silent_inherited_e_aborts_verdict_2026_08_10`](../active/issues/ldr_docs_gate_red_but_silent_inherited_e_aborts_verdict_2026_08_10.md)
**status**: open
**title**: ldr-docs-gate red for 10+ hours with zero Slack pages — inherited `-e` aborts the gate step before it writes verdict

### [`ldr_to_main_promote_fleet_queued_run_cancelled_livelock_2026_08_07`](../active/issues/ldr_to_main_promote_fleet_queued_run_cancelled_livelock_2026_08_07.md)
**status**: open · **estimate**: 0.3 cal AI-days (class: infra)
**title**: ldr-to-main-promote-fleet's single concurrency group starves under heavy multi-agent trigger volume

### [`main_backmerge_to_ldr_no_retry_safety_net_for_non_pm_repos_2026_08_18`](../active/issues/main_backmerge_to_ldr_no_retry_safety_net_for_non_pm_repos_2026_08_18.md)
**status**: open · **estimate**: 0.4 cal AI-days (class: infra)
**title**: A failed main-backmerge-to-ldr run strands LDR indefinitely on every non-PM repo

### [`pm_version_split_blocks_all_quickmerge_code_commits_2026_08_10`](../active/issues/pm_version_split_blocks_all_quickmerge_code_commits_2026_08_10.md)
**status**: open · **estimate**: 0.25 cal AI-days (class: infra)
**title**: PM VERSION_SPLIT blocks every quickmerge CODE commit to unified-trading-pm

### [`qg_sentinel_environment_blind_2026_07_23`](../active/issues/qg_sentinel_environment_blind_2026_07_23.md)
**status**: open · **estimate**: 0.4 cal AI-days (class: refactor)
**title**: QG sentinel is ENVIRONMENT-blind — quickmerge runs gates as development, standalone runs default to prod

### [`quickmerge_isolated_worktree_missing_sibling_pm_checkout_2026_08_10`](../active/issues/quickmerge_isolated_worktree_missing_sibling_pm_checkout_2026_08_10.md)
**status**: open
**title**: quickmerge.sh isolated-worktree mode fails every non-PM repo ship — missing sibling unified-trading-pm checkout

### [`quickmerge_setup_bootstrap_loop_blocks_commit_2026_08_09`](../active/issues/quickmerge_setup_bootstrap_loop_blocks_commit_2026_08_09.md)
**status**: open
**title**: quickmerge re-enters setup.sh after the quality audit and exits without committing

### [`safe_doc_push_unrecognized_flag_silently_becomes_branch_name_2026_08_18`](../active/issues/safe_doc_push_unrecognized_flag_silently_becomes_branch_name_2026_08_18.md)
**status**: open · **estimate**: 0.08 cal AI-days (class: infra)
**title**: safe-doc-push.sh has no --agent flag — an unrecognized flag silently becomes the target BRANCH

### [`semver_agent_squash_promote_blind_to_patch_fixes_2026_08_07`](../active/issues/semver_agent_squash_promote_blind_to_patch_fixes_2026_08_07.md)
**status**: open · **estimate**: 0.5 cal AI-days (class: infra)
**title**: semver-agent silently mints ZERO tags fleet-wide when a promote cycle has no exported-API-changing commit

### [`silent_failures_surfacing_as_generic_promotion_lag_2026_07_17`](../active/issues/silent_failures_surfacing_as_generic_promotion_lag_2026_07_17.md)
**status**: open · **estimate**: 0.8 cal AI-days (class: refactor)
**title**: Three unrelated hard failures all surfaced as the same vague "PROMOTION LAG > 60m" warning

### [`uac_value_only_config_change_breaks_utl_untested_2026_07_20`](../active/issues/uac_value_only_config_change_breaks_utl_untested_2026_07_20.md)
**status**: open · **estimate**: 0.8 cal AI-days (class: infra)
**title**: UAC value-only registry/config edits break UTL's own tests with no gate able to see it

### [`unified_trading_ci_ff_pull_cron_branch_override_gap_2026_08_17`](../active/issues/unified_trading_ci_ff_pull_cron_branch_override_gap_2026_08_17.md)
**status**: open
**title**: slot-cron-ff-pull.sh's own branch-override registry never got a unified-trading-ci row

### [`workflow_template_runs_on_placeholder_prettier_mangled_fleetwide_2026_08_07`](../active/issues/workflow_template_runs_on_placeholder_prettier_mangled_fleetwide_2026_08_07.md)
**status**: open · **estimate**: 0.4 cal AI-days (class: infra)
**title**: Fleet-wide broken `runs-on:` in 7 workflow templates — prettier deterministically mangles the `{{RUNS_ON}}` placeholder

## P2 — useful; opportunistic

### [`build_deploy_pipeline_provenance_and_aws_deferred_gaps_2026_07_21`](../active/issues/build_deploy_pipeline_provenance_and_aws_deferred_gaps_2026_07_21.md)
**status**: open · **estimate**: 1.2 cal AI-days (class: infra)
**title**: Build/deploy pipeline gaps surfaced by the artifact-pipeline audit — 2 confirmed AWS-lane bugs + 2 GCP observability gaps

### [`ci_alert_failure_resolution_linkage_2026_08_16`](../active/issues/ci_alert_failure_resolution_linkage_2026_08_16.md)
**status**: open · **estimate**: 0.36 cal AI-days (class: design)
**title**: CI-failures Slack alerts carry no shared identity between a CRITICAL and its eventual resolution

### [`ci_reconciler_ikenna_worker_ssm_permission_gap_2026_08_16`](../active/issues/ci_reconciler_ikenna_worker_ssm_permission_gap_2026_08_16.md)
**status**: open
**title**: ci_reconciler's ambient AWS identity is a static IAM user, not `uts-orchestrator-epic-role`

### [`ci_registry_drift_uac_utl_stale_tag_version_conflict_2026_07_26`](../active/issues/ci_registry_drift_uac_utl_stale_tag_version_conflict_2026_07_26.md)
**status**: open
**title**: unified-trading-system-ui's registry-drift CI job has been silently broken since 2026-07-21 (UAC/UTL stale-tag pip conflict)

### [`ci_satellite_ao_dispatch_batch13_2026_08_13`](../active/ci_satellite_ao_dispatch_batch13_2026_08_13.md)
**status**: active · **estimate**: 2.9 cal AI-days (class: refactor)

### [`ci_satellite_ao_dispatch_batch13_2026_08_13_finalize`](../active/ci_satellite_ao_dispatch_batch13_2026_08_13_finalize.md)
**status**: active · **estimate**: 0.4 cal AI-days (class: infra)

### [`ci_satellite_ao_dispatch_batch15_2026_08_16`](../active/ci_satellite_ao_dispatch_batch15_2026_08_16.md)
**status**: active · **estimate**: 3.6 cal AI-days (class: refactor)

### [`ci_satellite_ao_dispatch_batch15_2026_08_16_finalize`](../active/ci_satellite_ao_dispatch_batch15_2026_08_16_finalize.md)
**status**: active · **estimate**: 0.5 cal AI-days (class: infra)

### [`cloud_run_traffic_pin_silent_freeze_alert_wiring_2026_08_05`](../active/issues/cloud_run_traffic_pin_silent_freeze_alert_wiring_2026_08_05.md)
**status**: open · **estimate**: 0.24 cal AI-days (class: infra)
**title**: deployment-api traffic silently pinned to a stale revision-name for ~24h despite 5 green CI deploys

### [`deployment_api_events_global_state_leak_flaky_metadata_probe_2026_08_06`](../active/issues/deployment_api_events_global_state_leak_flaky_metadata_probe_2026_08_06.md)
**status**: open · **estimate**: 0.6 cal AI-days (class: research)
**title**: deployment-api promote PR #501 test failure hits a real GCE metadata probe despite mocking — module-level global-state leak

### [`features_service_clean_check_dangling_fleet_ci_dedup_revert_2026_08_07`](../active/issues/features_service_clean_check_dangling_fleet_ci_dedup_revert_2026_08_07.md)
**status**: open · **estimate**: 0.12 cal AI-days (class: research)
**title**: Uncommitted, unexplained staged revert of fleet-workflow-dedup thin-caller-stubs found in features-service-clean-check

### [`fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06`](../active/fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md)
**status**: active · **estimate**: 4.8 cal AI-days (class: infra)
**title**: Convert the remaining fully-duplicated fleet workflow templates into unified-trading-ci reusable workflows

### [`ibkr_gateway_infra_release_tag_stall_2026_08_11`](../active/issues/ibkr_gateway_infra_release_tag_stall_2026_08_11.md)
**status**: open
**title**: ibkr-gateway-infra release-tag-stall — root-caused past the "false alarm" verdict

### [`ldr_docs_gate_red_but_silent_inherited_e_aborts_verdict_2026_08_10_finalize_2026_08_17`](../active/issues/ldr_docs_gate_red_but_silent_inherited_e_aborts_verdict_2026_08_10_finalize_2026_08_17.md)
**status**: open
**title**: Finalize — ldr-docs-gate silent -e trap

### [`main_ldr_backmerge_silently_reapplies_collateral_frontmatter_deletion_2026_08_17`](../active/issues/main_ldr_backmerge_silently_reapplies_collateral_frontmatter_deletion_2026_08_17.md)
**status**: open · **estimate**: 0.4 cal AI-days (class: infra)
**title**: main→LDR back-merge silently re-applies a frontmatter key an earlier promotion dropped as collateral

### [`mtds_is_historical_quickmerge_bypass_backlog_2026_08_16`](../active/issues/mtds_is_historical_quickmerge_bypass_backlog_2026_08_16.md)
**status**: open
**title**: MTDS + instruments-service carry an 8-commit-each, month-old, multi-author strict-quickmerge bypass backlog

### [`mtds_ldr_cloud_build_docker_step6_failure_2026_08_10`](../active/issues/mtds_ldr_cloud_build_docker_step6_failure_2026_08_10.md)
**status**: open
**title**: market-tick-data-service LDR Cloud Build fails at docker step 6 — genuine image-build break

### [`plan_reconciler_findings_ci_2026_08_10`](../active/issues/plan_reconciler_findings_ci_2026_08_10.md)
**status**: open
**title**: plan_reconciler findings — ci tranche — 2026-08-10

### [`plan_reconciler_findings_ci_2026_08_16`](../active/issues/plan_reconciler_findings_ci_2026_08_16.md)
**status**: open
**title**: plan_reconciler findings — ci tranche — 2026-08-16

### [`sit_gate_treadmill_recurs_under_high_ldr_velocity_2026_08_08`](../active/issues/sit_gate_treadmill_recurs_under_high_ldr_velocity_2026_08_08.md)
**status**: open · **estimate**: 0.4 cal AI-days (class: infra)
**title**: SIT-gate treadmill recurs under high LDR commit velocity — repos stuck 8/6 straight blocked ticks

### [`unified_api_contracts_image_build_gate_template_lag_blocks_all_pm_commits_2026_08_14`](../active/issues/unified_api_contracts_image_build_gate_template_lag_blocks_all_pm_commits_2026_08_14.md)
**status**: open · **estimate**: 0.12 cal AI-days (class: infra)
**title**: unified-api-contracts' new consumer-qg-gate job was never forward-ported into image-build-gate.yml's SSOT template

### [`workflow_template_drift_repeated_during_phase7_rollout_2026_07_27`](../active/issues/workflow_template_drift_repeated_during_phase7_rollout_2026_07_27.md)
**status**: open
**title**: agent-orchestrator's workflow-template-parity gate drifted + blocked EVERY unified-trading-pm commit 3 times within ~1 hour

## P3 — backlog; revisit quarterly

### [`ag_closeout_audit_ci_parked_2026_08_16`](../active/issues/ag_closeout_audit_ci_parked_2026_08_16.md)
**status**: open
**title**: ag-closeout-audit ci delta report — 2026-08-16

### [`ci_tranche_zero_checkbox_archive_sweep_2026_08_18`](../active/ci_tranche_zero_checkbox_archive_sweep_2026_08_18.md)
**status**: active · **estimate**: 0.96 cal AI-days (class: infra)

### [`ci_tranche_zero_checkbox_archive_sweep_2026_08_18_finalize`](../active/ci_tranche_zero_checkbox_archive_sweep_2026_08_18_finalize.md)
**status**: active · **estimate**: 0.16 cal AI-days (class: infra)

### [`cloud_build_router_fallback_region_same_as_primary_2026_08_14`](../active/issues/cloud_build_router_fallback_region_same_as_primary_2026_08_14.md)
**status**: open
**title**: cloud-build-router's "regional fallback" has retried the SAME region as primary since 2026-04-15

### [`promote_pr_non_supersession_after_greeks_service_fix_2026_08_18`](../active/issues/promote_pr_non_supersession_after_greeks_service_fix_2026_08_18.md)
**status**: open
**title**: Promote-PR non-supersession after a gate-passing greeks-service re-run

### [`sit_stamp_dispatch_503_false_positive_2026_08_17`](../archive/2026_08/issues/sit_stamp_dispatch_503_false_positive_2026_08_17.md)
**status**: resolved (archived 2026-08-20)
**title**: full-workspace-sit "failures" were GitHub API 503s in the SIT_VALIDATED stamp-dispatch step, not broken cross-repo checks

### [`unified_api_contracts_image_build_gate_template_lag_blocks_all_pm_commits_2026_08_14_finalize_2026_08_18`](../active/issues/unified_api_contracts_image_build_gate_template_lag_blocks_all_pm_commits_2026_08_14_finalize_2026_08_18.md)
**status**: open · **estimate**: 0.1 cal AI-days (class: infra)
**title**: unified_api_contracts_image_build_gate_template_lag — finalize

### [`uv_version_pin_live_ci_reusable_workflow_still_hardcoded_2026_08_09`](../active/issues/uv_version_pin_live_ci_reusable_workflow_still_hardcoded_2026_08_09.md)
**status**: open
**title**: UV_VERSION centralization missed the truly-live CI reusable workflow copy in unified-trading-ci

<!-- prettier-ignore-end -->

## Cross-epic coordination

- **`security_and_cross_cutting_master`** (the renamed `infrastructure_master`) — shares the same `master_to_live_defi_2026_05_23`
  parent lineage; its own quality-gates.sh ratchet/debt docs are a DIFFERENT domain from this epic's delivery-pipeline
  mechanism docs, even though both run through the same `quality-gates.sh` script. Do not re-merge them.
- **`uac_master`** — several docs here (`breaking_change_differ_blind_to_registry_data_dicts`,
  `uac_value_only_config_change_breaks_utl_untested`) are about a CI GATE's blindness to UAC content changes, not about
  UAC's own schema/registry correctness — they stay here because the fix is a gate/pipeline change, not a UAC-content
  change. If the fix pattern reverses (UAC starts requiring a new governance discipline instead), re-evaluate.
- **`plan_hygiene_master`** — the `plan_reconciler_findings_ci_*` / `ag_closeout_audit_ci_parked_*` docs are outputs of
  plan-hygiene tooling (`/plan-reconcile`, `/ag-closeout-audit`) run against this epic's own "ci" tranche; the tooling
  itself is owned by `plan_hygiene_master`, only its per-tranche findings docs live here.

## Codex SSOTs

| Doc | Owns |
| --- | --- |
| `/codex/08-workflows/ci-cd-flow.md` | Gate set / quickmerge / strict-quickmerge / LDR-is-SSOT / branch-protection / semver + wheel release / deployment flow |
| `/codex/12-agent-workflow/host-concurrency-and-commit-provenance.md` | QG concurrency model / commit-provenance trailer / reconcile-retry mechanics |
| `/codex/04-architecture/ci-alerting.md` | `ci-failures` Slack channel routing, dedup, cooldown mechanics |
| `/codex/05-infrastructure/per-tab-worktrees.md` | Ship-script isolated-worktree mechanics, commit attribution |
