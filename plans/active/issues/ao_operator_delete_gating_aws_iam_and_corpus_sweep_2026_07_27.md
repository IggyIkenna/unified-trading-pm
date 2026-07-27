---
doc_type: issue
title:
  "AO's AWS identity (uts-orchestrator-epic-role) cannot self-grant IAM permissions and has zero S3/RDS/DynamoDB/ECS
  access — blocks closing the operator-delete-gating problem on the AWS side; plus tracked follow-up for the corpus-wide
  [OPERATOR]-tag reduction sweep"
summary: >-
  Found 2026-07-26/27 while shipping the reversibility-qualified prod-delete carve-out (delete-safety-protocol §3a,
  task_template.md finding T — see /codex/02-data/gcs-and-manifest-delete-safety-protocol.md, already shipped at
  unified-trading-pm@7687c6a79). The operator separately asked to give the AO orchestrator's cloud identity whatever
  permissions it's missing across both clouds (monitor/create/modify/delete on Cloud Run, buckets, databases, VMs) so
  agents stop hitting permission walls. GCP side is DONE: unified-trading-sa@central-element-323112 (the orchestrator's
  actual GCP identity, distinct from the human ADC used interactively) was granted roles/storage.admin,
  roles/compute.admin, roles/bigquery.admin, roles/datastore.owner, roles/cloudsql.admin (additive, verified via `gcloud
  projects get-iam-policy central-element-323112 --filter="bindings.members:unified-trading-sa@..."`). AWS side is
  BLOCKED: both the orchestrator VM (i-0c9b283b31d6b5ca7) and the human-planning VM (i-0dd9812a96cdda5dc) assume the
  SAME IAM role, uts-orchestrator-epic-role. Empirically probed (read calls, since the role can't even list its own
  policies): EC2 describe + SSM work; S3 ListAllMyBuckets, RDS DescribeDBInstances, DynamoDB ListTables, and ECS
  ListClusters are ALL AccessDenied. The role also lacks iam:ListAttachedRolePolicies/iam:ListRolePolicies on ITSELF, so
  no agent running as this role — including this one — can read or modify its own AWS permissions. This is a genuine
  hard blocker, not a judgment call: it needs a human with a DIFFERENT AWS identity (root, or a separate IAM-admin user)
  to attach broader access (e.g. AmazonS3FullAccess, AmazonRDSFullAccess, AmazonDynamoDBFullAccess,
  AmazonECS_FullAccess, or an equivalent scoped custom policy) to uts-orchestrator-epic-role, plus optionally a
  narrowly-scoped iam:{Get,List,Put,Attach,Detach}RolePolicy grant limited to that one role's ARN if self-service IAM
  management is wanted going forward.

  Separately, the operator asked (2026-07-27) to grep ALL remaining [OPERATOR]-tagged todos workspace-wide and move as
  many as possible to a script-driven/no-operator-needed pattern — "unless it's a genuinely unclear investigation for
  new features, even audits can be agent-driven across all plans and issues." A sizing pass found only ~15 of the 669
  active docs have an open [OPERATOR]-tagged todo actually citing delete-safety-protocol (most of the corpus never
  touches this topic) — 1 (defi_consolidated_closeout_2026_07_18.md) was fixed same-session as a worked example; a
  background agent (session-internal id a387f323a591e01ff, not a durable identifier — check /workflows or task
  notifications, not this doc, for its live status) was dispatched to work through the remaining 14 one at a time,
  applying the SAME reversibility-verified-vs-approve-executes-vs-leave-gated judgment per file (several of the 14 cite
  hard-stops #2-#5, which are correctness invariants unrelated to reversibility and must stay untouched). That agent's
  actual completion state was NOT verified before this doc was written — this session hit context limits mid-sweep and
  had to checkpoint. The broader "[OPERATOR] tags outside the delete-safety topic" scope (VM-launch authority
  reservations, credential asks, genuine design-judgment todos) was explicitly NOT sized or touched — the operator's own
  caveat ("unless it's genuinely unclear investigation for new features") means this needs a real per-tag classification
  pass, not a blind removal, and that classification work has not started yet.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator, unified-trading-library]
scope: [engineer, admin]
tags: [aws, iam, permissions, agent-orchestrator, delete-safety, operator-gating, hard-rule, infra]
related:
  [
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    plans/active/task_template.md,
  ]
created: 2026-07-27
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
drift_direction: unknown
depends_on: []
locked_by:
resolved_by:
source:
  [
    "Operator ask 2026-07-26/27: give AO the cloud permissions it needs; separately, reduce corpus-wide [OPERATOR] tags
    wherever a script-driven path suffices. Both surfaced mid-session while shipping the reversibility carve-out; this
    doc exists because the session hit a context checkpoint before either could be fully closed out.",
  ]
assigned_role: infra
---

# AO cross-cloud IAM gap + corpus-wide `[OPERATOR]`-tag reduction

## Todos

- [ ] [OPERATOR] P0. **Attach broader AWS permissions to `uts-orchestrator-epic-role`** (account `427895769566`).
      Requires a human with a DIFFERENT AWS identity than this role itself (root, or a separate IAM-admin user) — no
      agent running AS this role can grant it more, verified empirically (see summary). Minimum: S3, RDS, DynamoDB, ECS
      access matching what the GCP side already has (storage/database/compute admin). Optionally also grant
      `iam:{Get,List,Put,Attach,Detach}RolePolicy` scoped to this ONE role's ARN so future gaps are self-serviceable
      without a human round-trip. **Done when**: `aws s3api list-buckets`, `aws rds     describe-db-instances`,
      `aws dynamodb list-tables`, `aws ecs list-clusters` all succeed when run as this role.
- [x] [DIAG] P1. ✅ **Verified 2026-07-27** — all 14 files done, commits confirmed on `origin/live-defi-rollout` via
      `git merge-base --is-ancestor` (`cc438a02c`, `1be59b97b`, `1e7f5389a`, `c6ef8cb1f`, `f5232f3e5`) + spot-checked
      actual file content (not just trusting the agent's self-report). 6 files downgraded to reversibility-verified (all
      against buckets fresh-checked at 604800s), 2 re-cited as approve-executes (whole-bucket/non-GCS, correctly stays
      `[OPERATOR]`), 6 correctly left untouched (hard-stop #2, manifest-row mutations that aren't `gcs_delete_object`
      calls, or policy/scope decisions rather than delete execution — §3a doesn't apply to any of these). No bucket
      found below the 604800s threshold. See Progress Log below for detail.
- [ ] [DIAG] P1. **Classify the remaining `[OPERATOR]` tags workspace-wide by REASON** — precise count as of 2026-07-27:
      **44 active/issue docs carry 95 open `[OPERATOR]`-tagged todos total**
      (`grep -rlE '^\s*-\s*\[ \].*\[OPERATOR\]' plans/active plans/active/issues --include="*.md"`); 15 of those 44 are
      the delete-safety set already resolved by the todo above. **29 files remain unclassified** — read each, classify
      by reason (delete-safety-reducible-but-missed / VM-launch-authority-reservation / credential-ask /
      genuine-judgment-call needing a real human decision / other), and only downgrade the
      delete-safety-reducible-but-missed cases using the exact same fresh-check discipline as the todo above. Do NOT
      touch VM-launch-authority or genuine-judgment-call cases — removing `[OPERATOR]` from those violates
      dispatch-scope-eligibility (`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` §
      "Dispatch-scope eligibility"). The 29 files (relative to `plans/active/`):
      `defi_expected_unattempted_seeder_design_2026_07_26.md`, `deployment_ui_observability_ux_tracker_2026_07_17.md`,
      `infra_satellite_ao_dispatch_batch1_2026_07_26.md`,
      `issues/ag_closeout_auditor_one_shot_complete_no_agentrow_2026_07_26.md`,
      `issues/ao_backlog_done_row_disappearance_2026_07_25.md`,
      `issues/central_vm_relaunch_does_not_reregister_glue_runners_2026_07_24.md`,
      `issues/defi_legacy_precanonical_composite_venue_objects_2026_07_24.md`,
      `issues/defi_write_defi_rows_leaf_symbol_not_canonical_id_capture_not_stopped_2026_07_24.md`,
      `issues/deployment_ui_nav_consolidation_2026_07_17.md`,
      `issues/fleet_audit_triad_deferred_followups_2026_06_01.md`,
      `issues/github_actions_deploy_sa_overbroad_secret_access_2026_07_24.md`,
      `issues/idle_slot_dirty_wip_never_auto_resolves_2026_07_20.md`,
      `issues/instruments_store_prediction_path_scheme_not_asset_group_pipeline_mode_2026_07_26.md`,
      `issues/kalshi_execution_credential_secret_name_mismatch_2026_07_26.md`,
      `issues/mdps_features_live_launcher_exec_dispatch_never_wired_2026_07_27.md`,
      `issues/odds_api_raw_ingestion_gap_2026_06_21_24_2026_07_26.md`,
      `issues/orchestrator_jwt_secret_not_pinned_causes_fleet_git_status_outage_2026_07_24.md`,
      `issues/plan_health_tests_leak_real_slack_alerts_2026_07_24.md`,
      `issues/post_cutover_silent_assumption_sweep_2026_07_23.md`,
      `issues/prod_terraform_drift_backlog_reconcile_2026_07_24.md`,
      `issues/qg_sentinel_environment_blind_2026_07_23.md`, `issues/shared_host_home_filesystem_full_2026_07_26.md`,
      `issues/sports_odds_api_key_deactivated_2026_07_26.md`,
      `issues/sports_player_stats_empty_write_followups_2026_07_26.md`,
      `issues/sports_pre_floor_fixtures_orphan_misclassification_2026_07_22.md`,
      `issues/vm_startup_scripts_no_auto_rollout_to_gcs_2026_07_19.md`,
      `market_tick_data_service_lending_instrument_type_historical_restamp_2026_07_24.md`,
      `mtds_available_at_cross_asset_backfill_2026_07_13.md`,
      `prediction_satellite_ao_dispatch_batch4_2026_07_26_finalize.md`, `repo_scripts_governance_audit_2026_06_18.md`,
      `sports_predictions_live_mode_activation_readiness_2026_07_21.md`, `vol_dvol_backtestable_engines_2026_07_13.md`.
      **Done when**: every one of these 29 files has a stated classification (either fixed inline in the file itself, or
      logged in this issue doc's Progress Log if left as-is) — no file silently skipped.

## Progress Log

- **2026-07-27**: Background agent (dispatched pre-compact) completed all 14 delete-safety-set files. Verified via
  ancestor-check + content spot-check, not just trusting its self-report (per this workspace's own "grep-then-READ"
  discipline). Todo above flipped. Continuing autonomously (`/autonomous`, operator away ~6h) to the broader 29-file
  classification pass next.
