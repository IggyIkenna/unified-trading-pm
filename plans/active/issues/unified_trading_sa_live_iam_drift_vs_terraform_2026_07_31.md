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
sequential: true
drift_direction: correct-code
source: >-
  Surfaced 2026-07-31 (slot-14, infra) while executing bucket_iam_write_protection_per_tier_2026_06_09.md P2.2b
  (bucket_iam_write_protection_per_tier-010) — a credential-availability side-investigation, not the task's own scope.
resolved_by:
locked_by:
locked_since:
depends_on: []
context_scope:
  [
    /plans/active/bucket_iam_write_protection_per_tier_2026_06_09.md,
    /codex/05-infrastructure/bucket-isolation-model.md,
    /codex/05-infrastructure/orchestrator-cloud-identity-self-service.md,
  ]
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

## Audit findings (2026-07-31, slot 7, infra) — P0 todo

**Method**: `gcloud logging read` against
`protoPayload.methodName="SetIamPolicy" AND protoPayload.serviceName="cloudresourcemanager.googleapis.com"`, filtered
precisely on the structured field
`protoPayload.serviceData.policyDelta.bindingDeltas.member="serviceAccount:unified-trading-sa@central-element-323112.iam.gserviceaccount.com"`
(a bare full-text substring filter was tried first and returned an identical result set, confirming the field-level
filter isn't under-matching). Read as the `unified-trading-sa` identity itself (has `logging.viewer`); ran via
`--account=` per-invocation rather than `gcloud config set account`, since `/home/ubuntu/.config/gcloud` is a
**host-shared config dir** across all slots (confirmed via `gcloud config configurations list` — named configs
`slot11-work`/`slot14-work`/`slot15-work`/`slot16-work` coexist) — mutating the shared `default` config's active account
would have raced other slots' concurrent `gcloud` calls; the one accidental `gcloud config set account` mutation made
mid-investigation was immediately reverted back to `github-deploy` (its original value) before the flag-based approach
was adopted.

**Retention-window ceiling (hard constraint, verified)**: `gcloud logging buckets list --project=central-element-323112`
shows the `_Required` bucket at `global` location, `retentionDays=400`, `locked=True` (Google's immutable Admin-Activity
floor — SetIamPolicy is always logged here, cannot be shortened or disabled).
`gcloud projects describe central-element-323112` shows `createTime=2021-08-16T12:52:47Z` — the project is ~4.4 years
old, so **any IAM grant made before ~2025-06-27 (400 days before this audit) has no retrievable Cloud Audit Log entry,
full stop** — not a misconfiguration, a hard Google-side retention floor.

**Result — only 3 of the 24 undeclared roles have ANY audit-log trail in the retrievable window**, and all three are
recent, self-granted, non-terraform events:

| timestamp (UTC)          | action | role                        | actor (= granter)             |
| ------------------------ | ------ | --------------------------- | ----------------------------- |
| 2026-07-31T01:00:41.332Z | ADD    | `roles/secretmanager.admin` | `unified-trading-sa` (itself) |
| 2026-07-31T13:07:44.180Z | ADD    | `roles/pubsub.publisher`    | `unified-trading-sa` (itself) |
| 2026-07-31T19:32:14.596Z | ADD    | `roles/logging.logWriter`   | `unified-trading-sa` (itself) |

All three: (a) are in the undeclared-24 set (none of `secretmanager.admin`/`pubsub.publisher`/`logging.logWriter` match
the 9 terraform-declared roles — the closest declared cousins are `secretmanager.secretAccessor` and `pubsub.editor`,
which are DIFFERENT roles), (b) happened TODAY, all within the ~19 hours immediately preceding this audit, (c) were
granted by `unified-trading-sa` acting AS ITSELF (not by a human, not by `github-actions-deploy`, not via `tofu apply`)
— i.e., some agent session today used the SA's own ambient credential (per RULES.md's ambient-identity guidance) to
self-grant itself three NEW project-level roles outside terraform entirely, live evidence of exactly the
self-escalation-adjacent pattern this doc's "Why it matters" section warns about (though these three specific roles are
not the two flagged self-escalation-capable ones — `projectIamAdmin`/`serviceAccountAdmin` — those two show ZERO
bindingDelta ADD events for `unified-trading-sa` anywhere in the 400-day window, meaning they predate 2025-06-27 too).

**The remaining 21 undeclared roles (including both `roles/resourcemanager.projectIamAdmin` and
`roles/iam.serviceAccountAdmin`) have NO retrievable grant event** — they were added before the 400-day audit-log floor
and cannot be traced to a specific actor/process via Cloud Audit Logs by any query. No REMOVE deltas for
`unified-trading-sa` appear in the window either (nothing was revoked and re-granted).

**Consequence for P1's operator ruling**: provenance for 21/24 roles (incl. both self-escalation-capable ones) is
unrecoverable — the ruling in P1 must be made on CURRENT NEED, not historical justification (no "who granted this and
why" answer exists to consult). The 3 traceable roles are a separate, actionable finding on their own: they show the
ambient-SA-credential pattern is ACTIVELY producing new undeclared project-level grants as of today, so P2's
terraform-import-or-revoke pass should treat this as a live, still-open leak, not a one-time historical drift snapshot —
whatever P1/P2 decide, a recheck of `unified-trading-sa`'s live policy vs. terraform after P2 lands is warranted to
confirm no further self-grants happened in the interim.

## Todos

- [x] [INFRA] P0. ✅ Audit `unified-trading-sa`'s IAM policy history (Cloud Audit Logs `SetIamPolicy` for this member,
      or `gcloud logging read` on `protoPayload.serviceName="cloudresourcemanager.googleapis.com"`) to identify how each
      of the 24 undeclared roles was granted and by what identity/process. (repo: deployment-service) —
      unified-trading-pm@7b2ea5656. See "Audit findings" section above: 3/24 traceable (all self-granted by the SA
      itself, today, outside terraform); 21/24 (incl. both self-escalation-capable roles) predate the 400-day Cloud
      Audit Log retention floor and are permanently untraceable via this mechanism. No further audit-log query will
      recover more — investigation exhausted the available evidence.
- [x] [INFRA] P1. ✅ RULED (2026-08-03, operator): **KEEP both** `roles/resourcemanager.projectIamAdmin` and
      `roles/iam.serviceAccountAdmin` for now — insufficient certainty to safely revoke either, given the audit-log
      evidence is exhausted (21/24 undeclared roles, incl. both self-escalation-capable ones, predate the 400-day
      retention floor per the Audit findings above). `projectIamAdmin` plausibly enables this workspace's own documented
      "both cloud identities are IAM-self-service — grant a missing role yourself" pattern
      (`/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md`), so revoking it carries real live-break
      risk. `iam.serviceAccountAdmin` has no found justification but is ALSO kept for now rather than revoked
      speculatively. Revisit revocation only with stronger evidence later — do not revoke speculatively. (repo:
      unified-trading-pm)
- [ ] [TERRAFORM] P2. **UNBLOCKED (2026-08-03)** — P1 ruled KEEP on both `projectIamAdmin` and `serviceAccountAdmin`
      (see P1 above): `terraform import` ALL 24 currently-live undeclared roles into `main.tf` as-is, matching the
      "keep, document, no removal" ruling, so `tofu plan` stops showing drift and future changes are caught — never a
      blanket `set-iam-policy` policy overwrite. (repo: deployment-service)
- [ ] [DOCS] P3. Cross-reference this doc from `bucket_iam_write_protection_per_tier_2026_06_09.md`'s Phase 2 (P2.1b
      already scopes "remove the god-SA objectAdmin" — note there that even a completed P2.1b leaves
      `projectIamAdmin`/`serviceAccountAdmin` live unless this doc's P1/P2 also land). (repo: unified-trading-pm)

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
- **slot-8 2026-08-03**: applied operator ruling on P1 (KEEP both `projectIamAdmin` and `serviceAccountAdmin` —
  insufficient certainty to safely revoke given exhausted audit-log evidence; revisit only with stronger evidence
  later). Flipped P1 done, retagged `[OPERATOR]`→`[INFRA]`, and unblocked P2's terraform-import scope accordingly.
