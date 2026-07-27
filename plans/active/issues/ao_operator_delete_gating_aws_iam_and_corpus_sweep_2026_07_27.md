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
- [ ] [DIAG] P1. **Verify the background sweep agent's actual completion state** (14 files:
      `sports_consolidated_closeout_2026_07_19.md`, `defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md`,
      `tradfi_satellite_ao_dispatch_batch2_2026_07_25.md`, `cefi_track7_candle_namespace_residual_2026_07_25.md`,
      `sports_consolidated_native_ao_extract_2026_07_25.md`, `prediction_satellite_ao_dispatch_batch2_2026_07_25.md`,
      `issues/sports_legacy_duplicate_triage_2026_07_22.md`,
      `issues/sports_day_all_teams_venues_fold_key_scheme_mismatch_2026_07_25.md`,
      `cefi_satellite_ao_dispatch_batch1_2026_07_25.md`,
      `issues/prediction_phantom_reconciler_wipes_bundle_atom_2026_07_10.md`,
      `docker_artifact_registry_cleanup_policy_2026_07_24.md`,
      `issues/gate_on_depends_wiring_gap_defi_dex_pool_finalize_2026_07_25.md`,
      `issues/defi_lst_rates_migrated_marker_unfiltered_live_reader_2026_07_25.md`,
      `issues/mtds_instruments_metadata_hive_canonicalisation_reader_gap_2026_07_26.md`). Grep each for
      `reversibility-verified`/`approve-executes` framing (the pattern already applied to
      `defi_consolidated_closeout_2026_07_18.md` and `sports_legacy_fixtures_path_migration_2026_07_24.md`) and confirm
      the relevant commits actually landed on `origin/live-defi-rollout` (`git log --oneline -- <path>`) — do NOT assume
      the agent finished cleanly just because it was dispatched. Any file not yet done: finish it per the same criteria
      (§3a of the delete-safety protocol), respecting the hard-stop #2-#5 scope boundary (only hard-stop #1, plain
      prod-bucket delete, is affected by the carve-out).
- [ ] [DIAG] P1. **Classify every remaining `[OPERATOR]` tag workspace-wide by REASON, not just presence** — the
      operator's ask was to move as many as possible off a human-blocking path, "unless it's a genuinely unclear
      investigation for new features." This needs a real per-tag read (grep finds ~182 docs mentioning
      `[OPERATOR]`/`human-only`/`delete-safety-protocol`/`prod-bucket delete` — most are NOT delete-safety related at
      all: VM-launch-authority reservations tied to a standing operator ruling for one workstream, credential asks,
      genuine design-judgment calls that are correctly gated per the dispatch-scope-eligibility rule). Produce a
      classification (delete-safety-reducible / VM-launch-authority / credential-ask / genuine-judgment-call / other)
      before touching anything outside the delete-safety subset already covered by the todo above — a blind strip of
      `[OPERATOR]` tags outside their actual reason would violate dispatch-scope-eligibility
      (`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility") for the
      genuine-judgment-call cases.
