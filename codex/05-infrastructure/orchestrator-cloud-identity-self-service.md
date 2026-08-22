---
doc_type: codex-ssot
title: Orchestrator cloud identities are self-service — a permission gap on them is not an operator escalation
summary: >-
  The AO orchestrator's two cloud identities (GCP `unified-trading-sa`, AWS `uts-orchestrator-epic-role`) both hold
  IAM-self-management permission as of 2026-07-27. A worker hitting a permission/IAM gap on either identity should grant
  the missing role directly (least-privilege, verified live) and continue — this is NOT a `[OPERATOR]` or
  `BLOCKED-CREDENTIALS` escalation. Documents the two identities' current grants, WHY the ambient credentials are
  already available to every AO worker (tmux-spawned shells inherit `.profile`/`.bashrc`'s
  `GOOGLE_APPLICATION_CREDENTIALS`; AWS instance-role access is automatic via the EC2 metadata service, not
  env-dependent), and the exact grant mechanics per cloud (materially different: AWS is resource-scoped to the role's
  own ARN; GCP has no such primitive, so `unified-trading-sa` holds full project-level
  `resourcemanager.projectIamAdmin`).
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer, admin]
tags: [iam, gcp, aws, agent-orchestrator, self-service, credential-ask, permissions, orchestrator-identity]
related:
  [
    /codex/05-infrastructure/credentials-matrix.md,
    /codex/05-infrastructure/agent-orchestrator-api-host.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    plans/active/task_template.md,
    /plans/archive/issues/ao_operator_delete_gating_aws_iam_and_corpus_sweep_2026_07_27.md,
  ]
created: 2026-07-27
authoritative_for:
  [
    the orchestrator's two cloud identities and their current IAM grants,
    when a permission gap is self-fixable vs a genuine credential-ask,
    the exact self-grant commands per cloud,
  ]
referenced_by: []
owner:
last_reviewed: 2026-07-31
code_refs:
  [
    agent-orchestrator/server/tmux_spawn.py,
    unified-trading-library/unified_trading_library/cloud_interface/providers/gcp.py,
  ]
---

# Orchestrator cloud identities are self-service

## The two identities

- **GCP**: `unified-trading-sa@central-element-323112.iam.gserviceaccount.com` — the orchestrator's real GCP identity
  (distinct from a human's interactive `gcloud auth login`). Ambient on every AO worker:
  `GOOGLE_APPLICATION_CREDENTIALS` is exported in both `~/.profile` and `~/.bashrc` on the orchestrator VM, so any
  tmux-spawned worker shell already authenticates as this SA — no separate credential setup needed.
- **AWS**: `uts-orchestrator-epic-role` (account `427895769566`) — assumed via the EC2 instance profile by the
  orchestrator VM (`i-0c9b283b31d6b5ca7`). Automatic for every process on that VM via the metadata service; no env var
  or key file involved at all.

**The separate `human-planning` VM (`i-0dd9812a96cdda5dc`) previously shared this same identity setup — it was
terminated 2026-08-03** (`ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md`); do not carry forward any "either VM"
/ "both VMs" framing for it.

## The rule

**A worker that hits a GCP/AWS permission error while acting AS one of these two identities should grant the missing
role directly, verify live, and continue — this is not `[OPERATOR]`/`BLOCKED-CREDENTIALS`.** Reserve those tags for a
gap on a genuinely DIFFERENT identity this worker cannot assume (e.g. `github-actions-deploy`, a human's personal
account, a brand-new credential that doesn't exist yet). Grant least-privilege — the specific role that closes the
specific gap, never blanket `Owner`/`AdministratorAccess` — and always re-verify the actual capability live (call the
real API, don't just read the IAM policy back) before marking a todo done, per this workspace's
evidence-backed-completion standard.

## GCP — project-level, not resource-scoped (know this before granting)

`unified-trading-sa` holds `roles/resourcemanager.projectIamAdmin` on `central-element-323112`. GCP has **no**
equivalent to AWS's `Resource: <own-role-arn>` scoping — `projectIamAdmin` can add/remove ANY binding on the WHOLE
project, including granting itself or anyone else `Owner`. There is no "manage only my own bindings" GCP primitive, so
this is a broader grant than the AWS side by necessity, not by choice — granted deliberately (2026-07-27, operator
ruling) to close this exact gap.

```bash
gcloud projects add-iam-policy-binding central-element-323112 \
  --member="serviceAccount:unified-trading-sa@central-element-323112.iam.gserviceaccount.com" \
  --role="roles/<MISSING_ROLE>" \
  --condition=None   # required — the project has pre-existing conditional bindings
```

Current grants (2026-07-27, additive only, never reduced): `storage.admin`, `storage.objectAdmin`, `compute.admin`,
`compute.instanceAdmin.v1`, `bigquery.admin`, `bigquery.dataEditor`, `bigquery.jobUser`, `datastore.owner`,
`datastore.user`, `cloudsql.admin`, `cloudscheduler.admin`, `cloudscheduler.viewer`, `run.admin`, `run.developer`,
`run.invoker`, `iam.serviceAccountAdmin`, `iam.serviceAccountUser`, `resourcemanager.projectIamAdmin`,
`secretmanager.secretAccessor`, `secretmanager.viewer`, `secretmanager.admin` (added 2026-07-31 — `secretAccessor`/
`.viewer` are read-only, `secrets.create` needed none of them; closed while provisioning `kalshi-api-key-id`/
`kalshi-private-key-pem` from the existing `kalshi-api-credentials` bundle), `pubsub.admin` (supersedes
`.editor`/`.viewer` — plain `.viewer` does not cover `topics/subscriptions.getIamPolicy`, discovered by testing, not
assumed), `cloudfunctions.viewer`, `cloudbuild.builds.editor/.viewer`, `artifactregistry.reader`, `logging.viewer`,
`monitoring.viewer`. Re-verify live via
`gcloud projects get-iam-policy central-element-323112 --flatten="bindings[].members" --filter="bindings.members:unified-trading-sa@..."`
before assuming a role is present — this list drifts as gaps get closed.

## AWS — resource-scoped to the role's own ARN

`uts-orchestrator-epic-role` holds an inline `self-manage-own-policies` policy scoped ONLY to itself
(`Resource: arn:aws:iam::427895769566:role/uts-orchestrator-epic-role`), granting
`iam:{Get,List}RolePolicy`/`{Get,List}AttachedRolePolicies`/`{Put,Attach,Detach}RolePolicy` — narrower and safer than
the GCP side, since it structurally cannot touch any OTHER identity's permissions.

```bash
aws iam attach-role-policy --role-name uts-orchestrator-epic-role --policy-arn <MANAGED_POLICY_ARN>
# or, for a custom scoped permission:
aws iam put-role-policy --role-name uts-orchestrator-epic-role --policy-name <name> --policy-document '<json>'
```

Current managed-policy grants: `AmazonS3FullAccess`, `AmazonRDSFullAccess`, `AmazonDynamoDBFullAccess`,
`AmazonECS_FullAccess`, `AmazonEC2ContainerRegistryPowerUser`, `uts-orchestrator-epic-policy` (custom). Inline:
`allow-codebuild-readonly`, `ci-cost-explorer-readonly`, `ci-escalation-runner-ssm-param-access`,
`deployment-registry-ssm-config`, `disk-recovery-ssm-temp`, `orchestrator-state-s3-rw`, `self-manage-own-policies`,
`self-ec2-createtags-instance` (`ec2:CreateTags` scoped to `instance/*` — the role's own EC2 grants didn't cover
tagging a newly-launched instance; added 2026-08-22 to launch a throwaway CI-bootstrap-verify EC2 host), `self-passrole-to-ec2`
(`iam:PassRole` scoped to the role's own ARN, condition `iam:PassedToService=ec2.amazonaws.com` — needed to attach the
role's own instance profile to a NEW instance via `run-instances`; added 2026-08-22), `self-ec2-lifecycle-throwaway-verify`
(`ec2:{Reboot,Stop,Terminate}Instances` scoped to `instance/*` with condition `ec2:ResourceTag/Lifecycle=throwaway-verify`
— deliberately narrowed to only instances carrying that exact tag, so it can never touch the real fleet; added
2026-08-22), `temp-manifest-consolidator-aws-decommission`. Re-verify via
`aws iam list-attached-role-policies --role-name uts-orchestrator-epic-role` / `list-role-policies` before assuming a
policy is present — note IAM inline-policy grants can take up to ~15-30s to propagate before a dependent API call
succeeds (confirmed 2026-08-22: an immediate retry after `put-role-policy` still 403'd; a second retry ~15s later
passed).

## Provenance

Both self-service grants landed 2026-07-27 while closing out the reversibility-carve-out work
(`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a) — the same underlying complaint (agents blocked on an
operator for something they could safely do themselves) showed up at the IAM layer, not just the delete-gating layer.
Full history + exact commands run:
`plans/active/issues/ao_operator_delete_gating_aws_iam_and_corpus_sweep_2026_07_27.md` (will archive; this doc is the
durable SSOT going forward).
