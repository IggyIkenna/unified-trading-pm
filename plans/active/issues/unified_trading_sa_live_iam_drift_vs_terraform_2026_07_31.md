---
doc_type: issue
title:
  "unified-trading-sa holds 34 live project-level IAM roles but only ~10 are declared anywhere in
  deployment-service/terraform/gcp — including undeclared roles/resourcemanager.projectIamAdmin and
  roles/iam.serviceAccountAdmin (self-escalation-capable) on the exact god-SA bucket_iam_write_protection_per_tier is
  trying to de-privilege"
summary: >-
  While executing bucket_iam_write_protection_per_tier_2026_06_09.md P2.2b (grant uts-prd-sa/uts-test-sa/
  uts-migration-sa the non-storage roles real runtimes need), this session needed a credential with
  resourcemanager.projects.setIamPolicy to apply the terraform change (github-actions-deploy lacked it; the operator's
  ADC token had expired non-interactively). Falling back to unified-trading-sa's own credential (per RULES.md's
  ambient-identity guidance) worked — and a `gcloud projects get-iam-policy --filter` on that identity surfaced 34
  distinct project-level roles live on unified-trading-sa, vs. the ~10 declared across every .tf file in
  deployment-service/terraform/gcp (9 in main.tf's unified_trading_* google_project_iam_member resources +
  monitoring.viewer in monitoring_deadman_scheduler.tf). 24+ roles are live with NO terraform declaration anywhere in
  this repo, including roles/resourcemanager.projectIamAdmin and roles/iam.serviceAccountAdmin — both of which let this
  SA grant/modify IAM policy and manage other service accounts, i.e. self-escalate or escalate any other SA in the
  project. This is a live security exposure on the exact identity bucket_iam_write_protection_per_tier_2026_06_09.md
  exists to de-privilege, and it is bigger in kind (privilege-escalation-capable, not just storage-write-capable) than
  either god-SA finding already tracked in that plan's Phase 2 issue docs (P2.1's "removing objectAdmin before rewire"
  and P2.2's "tier SAs are storage-only" / "default compute SA has 28 roles"). No terraform state was mutated to produce
  this finding — pure read-only `gcloud` queries + a repo-wide grep for iam_member resources referencing
  unified_trading. This is a NEW, independent finding — not a duplicate of
  issues/bucket_iam_p2_tier_sa_scope_gap_and_default_compute_sa_overprivilege_2026_07_30.md (that doc's Finding 2 is
  about the GCP *default compute* SA, a different identity).
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: [iam, terraform, gcp, security, ssot-contradiction, drift, privilege-escalation]
related:
  [
    /plans/active/bucket_iam_write_protection_per_tier_2026_06_09.md,
    /plans/active/issues/bucket_iam_p2_tier_sa_scope_gap_and_default_compute_sa_overprivilege_2026_07_30.md,
    /plans/active/issues/bucket_iam_p2_god_sa_removal_before_runtime_rewire_2026_07_30.md,
    /codex/05-infrastructure/bucket-isolation-model.md,
    /codex/05-infrastructure/orchestrator-cloud-identity-self-service.md,
  ]
created: "2026-07-31"
last_updated: "2026-07-31"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: infra
sequential: false
drift_direction: correct-code
source: >-
  Surfaced 2026-07-31 (slot-14, infra) while executing bucket_iam_write_protection_per_tier_2026_06_09.md P2.2b
  (bucket_iam_write_protection_per_tier-010) — a credential-availability side-investigation, not the task's own scope.
resolved_by:
locked_by:
locked_since:
depends_on: []
---

# unified-trading-sa's live IAM policy has 24+ undeclared project-level roles, including two self-escalation-capable ones

## What I found

Live query (identity: `unified-trading-sa` itself, which does hold `resourcemanager.projects.getIamPolicy` — itself
notable, see below):

```
gcloud projects get-iam-policy central-element-323112 --format=json \
  --flatten="bindings[].members" \
  --filter="bindings.members:unified-trading-sa@central-element-323112.iam.gserviceaccount.com"
```

returned 34 distinct roles:

```
roles/artifactregistry.admin          roles/logging.configWriter
roles/artifactregistry.reader         roles/logging.logWriter
roles/bigquery.admin                  roles/logging.viewer
roles/bigquery.dataEditor             roles/monitoring.alertPolicyEditor
roles/bigquery.jobUser                roles/monitoring.viewer
roles/cloudbuild.builds.editor        roles/pubsub.admin
roles/cloudbuild.builds.viewer        roles/pubsub.editor
roles/cloudfunctions.viewer           roles/pubsub.publisher
roles/cloudkms.viewer                 roles/pubsub.viewer
roles/cloudscheduler.admin            roles/resourcemanager.projectIamAdmin   <- SELF-ESCALATION
roles/cloudscheduler.viewer           roles/run.admin
roles/cloudsql.admin                  roles/run.developer
roles/compute.admin                   roles/run.invoker
roles/compute.instanceAdmin.v1        roles/secretmanager.admin
roles/datastore.owner                 roles/secretmanager.secretAccessor
roles/datastore.user                  roles/secretmanager.viewer
roles/iam.serviceAccountAdmin         <- SELF-ESCALATION   roles/storage.admin
roles/iam.serviceAccountUser          roles/storage.objectAdmin
roles/iap.tunnelResourceAccessor
```

A repo-wide grep for every `google_project_iam_member`/`google_service_account_iam_member` resource referencing
`google_service_account.unified_trading` across ALL of `deployment-service/terraform/gcp/*.tf` (not just `main.tf`)
finds only:

```
main.tf: storage.objectAdmin, bigquery.dataEditor, secretmanager.secretAccessor, run.invoker, pubsub.editor,
         compute.instanceAdmin.v1, iam.serviceAccountUser, artifactregistry.reader, redis.viewer (conditional),
         + a bucket-level storage.objectAdmin on trading-audit-records (google_storage_bucket_iam_member)
monitoring_deadman_scheduler.tf: monitoring.viewer
```

= 9 project-level roles declared. **24 of the 34 live roles have zero terraform declaration anywhere in this repo** —
either granted via `gcloud`/console directly, imported from a different (undiscovered) terraform root/workspace, or
applied by a process outside this checkout entirely. I did not investigate which; that's this doc's own P1 todo.

`roles/resourcemanager.projectIamAdmin` + `roles/iam.serviceAccountAdmin` are the two that matter most:
`projectIamAdmin` lets `unified-trading-sa` grant/revoke IAM bindings on the project (including granting itself more
roles, or granting other SAs — e.g. one of the tier SAs — arbitrary roles without going through terraform at all);
`serviceAccountAdmin` lets it create/delete/modify service accounts and their keys. Combined, a compromised
`unified-trading-sa` credential (or a bug in any script running as it) could self-escalate to effectively full project
control — a materially different (and worse) class of exposure than "can write every GCS bucket," which is the narrower
problem `bucket_iam_write_protection_per_tier_2026_06_09.md` was scoped to fix.

## Why it matters

Per `findings-triage`'s "SSOT contradiction → NOTIFY OPERATOR" + this being a live security exposure on the
`unified-trading-sa` identity that `bucket_iam_write_protection_per_tier_2026_06_09.md`'s entire Phase 2 already treats
as the primary de-privilege target (P2.1b: remove its `storage.objectAdmin`) — that plan's current scope (storage roles
only) will leave `unified-trading-sa` with `resourcemanager.projectIamAdmin` even after P2.1b fully lands, i.e. even a
"successful" god-SA storage de-privilege leaves a self-escalation vector open. This also means the live IAM policy is
not fully terraform-managed for this SA — any `tofu plan`/`tofu apply` against `main.tf` today would NOT show these 24
roles as drift-to-be-removed (terraform only manages resources it declares), so they are invisible to the normal
`tofu plan` review path relied on elsewhere in this same plan's P1.1-P2.2b work.

## Recommended decision

1. Enumerate where the 24 undeclared roles actually came from (console grant history / a different terraform workspace /
   `gcloud` audit logs for `SetIamPolicy` calls naming `unified-trading-sa`) before deciding whether to import them into
   terraform (if genuinely needed) or revoke them (if drift/leftover).
2. `roles/resourcemanager.projectIamAdmin` and `roles/iam.serviceAccountAdmin` specifically need an operator ruling:
   does any real workflow need `unified-trading-sa` to self-manage IAM/service-accounts, or is this drift/over-grant
   that should be revoked outright regardless of the broader per-tier/per-service SA reconciliation in
   `bucket_iam_p2_tier_sa_scope_gap_and_default_compute_sa_overprivilege_2026_07_30.md`?
3. Once (1)/(2) are answered, either `terraform import` the genuinely-needed roles (so future `tofu plan` reviews catch
   drift) or revoke the rest via a scoped `google_project_iam_member` removal (never a blanket policy overwrite —
   `gcloud projects set-iam-policy` on the whole policy risks dropping unrelated bindings; use per-role
   `gcloud projects remove-iam-policy-binding` or the terraform-managed equivalent instead).

## Todos

- [ ] [INFRA] P0. Audit `unified-trading-sa`'s IAM policy history (Cloud Audit Logs `SetIamPolicy` for this member, or
      `gcloud logging read` on `protoPayload.serviceName="cloudresourcemanager.googleapis.com"`) to identify how each of
      the 24 undeclared roles was granted and by what identity/process. (repo: deployment-service)
- [ ] [OPERATOR] P1. Rule on `roles/resourcemanager.projectIamAdmin` + `roles/iam.serviceAccountAdmin` specifically:
      genuinely needed (name the workflow) vs. revoke. These two are self-escalation-capable and should not sit
      undecided long. (repo: unified-trading-pm)
- [ ] [TERRAFORM] P2. Once P0/P1 resolve, either `terraform import` the genuinely-needed undeclared roles into `main.tf`
      (so `tofu plan` catches future drift) or remove the rest via scoped `google_project_iam_member` deletions — never
      a blanket `set-iam-policy` policy overwrite. (repo: deployment-service)
- [ ] [DOCS] P3. Cross-reference this doc from `bucket_iam_write_protection_per_tier_2026_06_09.md`'s Phase 2 (P2.1b
      already scopes "remove the god-SA objectAdmin" — note there that even a completed P2.1b leaves
      `projectIamAdmin`/`serviceAccountAdmin` live unless this doc's P1/P2 also land). (repo: unified-trading-pm)
