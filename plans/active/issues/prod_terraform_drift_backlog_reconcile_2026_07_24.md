---
doc_type: issue
title: Prod terraform drift backlog needs a deliberate operator-gated reconcile-apply (21 add / 18 change)
summary: |
  A full `tofu plan` against `terraform/state/prod` (`deployment-service/terraform/gcp`) shows 21-add/18-change/0-destroy
  of committed-but-un-applied resources (BigQuery `feature_external` tables, `paper_stream` job/cron,
  `batch_live_smoke_matrix`, the recovered `expected_universe_v2` run.invoker IAM, `odum_portal` domain mapping,
  defi_forward_poll updates). Surfaced 2026-06-23 during an unrelated watch-the-watchers dead-man's-switch `tofu apply`
  (targeted to that apply's own resources only, to avoid blindly sweeping this backlog in). Excised
  2026-07-24 from `data_pipeline_hardening_self_monitoring_2026_06_22.md` (plan line-cap remediation split, row 9) —
  this is a general prod-infra terraform-drift item, not a data-pipeline-hardening concern.
status: open
nature: process
asset_group: [cross-cutting, infrastructure]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [infra, terraform, drift, prod, reconcile-apply]
created: "2026-07-24"
last_updated: "2026-07-24"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.8
assigned_role: infra
drift_direction: advance-code
resolved_by:
locked_by:
locked_since:
source:
  [
    "Excised 2026-07-24 from data_pipeline_hardening_self_monitoring_2026_06_22.md per the plan line-cap remediation
    triage (plans/active/issues/plan_line_cap_remediation_2026_07_23.md, row 9) — the original author's own note already
    said 'filing as a P1 issue todo', this doc completes that filing.",
    "Originally surfaced 2026-06-23 during the watch-the-watchers dead-man's-switch tofu apply.",
  ]
related: [/plans/active/data_pipeline_hardening_self_monitoring_2026_06_22.md]
depends_on: []
---

# Prod terraform drift backlog needs a deliberate operator-gated reconcile-apply

## What I found

- **FINDING (separate, flagged not swept):** prod `terraform/state/prod` has a DRIFT BACKLOG of committed-but-un-applied
  changes (BigQuery `feature_external` tables, `paper_stream` job/cron, `batch_live_smoke_matrix`, the recovered
  `expected_universe_v2` run.invoker IAM, `odum_portal` domain mapping, defi_forward_poll updates — 21 add / 18 change
  in the full plan). NOT mine to sweep in a deadman apply. Needs a deliberate operator-gated reconcile-apply. → filing
  as a P1 issue todo.

## Why it matters

Committed-but-unapplied terraform means the working tree and the deployed prod state have drifted apart in ways nobody
has explicitly reviewed — some of these resources (e.g. `paper_stream` job/cron, `batch_live_smoke_matrix`) may be
load-bearing for in-flight work and their absence in prod could be masking a gap, while others (e.g. `odum_portal`
domain mapping) may be intentionally staged ahead of a cutover. Applying blind risks reverting or half-shipping
unrelated resources; not applying at all risks the drift silently growing. This is a general prod-infra concern
(`deployment-service/terraform/gcp`), not scoped to any one asset-group's data pipeline — it does not belong inside a
data-pipeline-hardening plan.

## Recommended decision

Someone with prod-infra + terraform context should walk the current `tofu plan` diff resource-by-resource, confirm each
is intended (not stale/abandoned), and apply in a deliberate operator-gated pass — mirroring how the watch-the-watchers
dead-man's-switch apply was scoped to `-target=...` its own resources rather than a blanket apply. Re-run `tofu plan`
fresh before acting (the 21/18 counts are as of 2026-06-23 and may have shifted).

## 2026-07-26 fresh `tofu plan` + resource-by-resource classification (slot-11, read-only)

Re-ran `ENV=prod ./tofu.sh init && ENV=prod ./tofu.sh plan` fresh against `terraform/state/prod` (read-only — no
`apply`). Result: **10 to add, 67 to change, 0 to destroy** — a COMPLETELY DIFFERENT composition from the 2026-06-23
finding (21 add / 18 change: BigQuery `feature_external` tables, `paper_stream`, `batch_live_smoke_matrix`,
`expected_universe_v2` run.invoker IAM, `odum_portal` domain mapping, `defi_forward_poll` updates). **None of the
June-23 items appear in today's diff** — that backlog was evidently cleared by an apply sometime since; what's below is
an entirely fresh drift set, exactly why the original todo said to re-run `tofu plan` fresh first.

**BLOCKING CAVEAT — this plan is provably incomplete.** The active ADC identity
(`unified-trading-sa@central- element-323112.iam.gserviceaccount.com`) lacks read permissions on 112 OTHER resources
tofu couldn't even refresh: 58 storage buckets (`storage.buckets.get`/`getIamPolicy` denied — most of the canonical
for_each bucket estate), 22 Secret Manager secrets, 26 project-level IAM-member reads, 4 pubsub topics + 2 pubsub
subscriptions (`getIamPolicy` denied). The true drift for these is UNKNOWN. Before any full-backlog apply decision, an
operator needs to either (a) grant `unified-trading-sa` the missing viewer-tier roles, or (b) re-run this plan under a
more-privileged credential — see follow-up todo below.

**Scope-guard note**: the two resources the dispatching plan named as cross-cutting-batch-owned (do not edit, but
classify) — the wave-launcher job image pin (`google_project_iam_member.wave_launcher_compute_admin` /
`wave_launcher_sa_user`, `wave_launcher_scheduler.tf`) and `lifecycle_catalogue_scheduler.tf`'s bucket-name fix
(`google_storage_bucket_iam_member.lifecycle_catalogue_instruments_admin["cefi"|"defi"|"prediction"|"sports"|"tradfi"]`)
— both fall inside the unreadable set above (project-IAM and bucket-IAM reads respectively), so they could NOT be
classified today. They're not silently skipped; they're blocked on the same IAM-grant follow-up below.

### Three-way classification — the 12 real (non-cosmetic) resources

| Resource                                                                          | Action | Classification                | Why                                                                                                                                                                                                                                                       |
| --------------------------------------------------------------------------------- | ------ | ----------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `google_service_account.defi_removal_probe`                                       | create | **INTENDED**                  | DeFi on-chain removal probe (Option B truth-gate), plan-tracked (`defi_catalogue_available_to_false_delisting_2026_07_20` / `defi_consolidated_closeout_2026_07_18` Track 3), code shipped `deployment-service@9a36478`                                   |
| `google_cloud_run_v2_job_iam_member.defi_removal_probe_run_invoker`               | create | **INTENDED**                  | Same bundle                                                                                                                                                                                                                                               |
| `google_cloud_scheduler_job.defi_removal_probe_daily`                             | create | **INTENDED**                  | Same bundle — 00:30 UTC daily trigger, ahead of the 01:00 lifecycle-catalogue-regen-defi run                                                                                                                                                              |
| `module.defi_removal_probe_job` (Cloud Run Job)                                   | create | **INTENDED**                  | Same bundle — the job itself                                                                                                                                                                                                                              |
| `google_storage_bucket_iam_member.defi_removal_probe_store_admin`                 | create | **INTENDED**                  | Same bundle — probe's write access to its DeFi bucket                                                                                                                                                                                                     |
| `google_project_iam_member.default_compute_sa_datastore_user`                     | create | **INTENDED**                  | Explicit documented prerequisite for the deployment-registry Firestore dual-write migration (`deployment_registry_firestore_p0_unblock_2026_07_14.md`), see `main.tf:661-669`                                                                             |
| `google_storage_bucket.canonical["alerting-service-central-element-323112"]`      | create | **INTENDED**                  | Genuinely-missing canonical bucket per `cloud-providers.yaml` SSOT (added `deployment-service@5f6d4e1`, 2026-07-21)                                                                                                                                       |
| `google_storage_bucket.canonical["central-element-323112-datapoint-validation"]`  | create | **INTENDED**                  | Same — added 2026-07-21 (todo 31, VM-prefix registration)                                                                                                                                                                                                 |
| `google_storage_bucket.canonical["central-element-323112-kill-switch-audit-log"]` | create | **INTENDED**                  | Same — added `deployment-service@f372f85`, 2026-07-21                                                                                                                                                                                                     |
| `google_storage_bucket.canonical["unified-trading-cicd-events"]`                  | create | **INTENDED (higher urgency)** | Same — added `deployment-service@9343a2f`, 2026-07-21; `main.tf:746` confirms every live CI/CD event writer/reader already resolves to this EXACT literal bucket name — it doesn't exist in prod yet, so those writes/reads may be failing silently today |
| `module.instruments_cefi_t1_recon_job` (labels only)                              | update | **INTENDED**                  | Committed labels (`purpose=t1-batch-cefi`) postdate the live resource's stale labels (`deployment-service@4dd8d53`); correctness-only, no functional change                                                                                               |
| `module.instruments_prediction_t1_recon_job` (labels only)                        | update | **INTENDED**                  | Same pattern, same commit                                                                                                                                                                                                                                 |

None of the 12 fall into STALE/ABANDONED or DELIBERATELY-STAGED-AHEAD-OF-A-CUTOVER — every one traces to a real,
already-shipped code commit whose terraform-side counterpart just hasn't been applied to prod yet.

### The other 65 "changes" — a 4th bucket the 3-way taxonomy doesn't fit: COSMETIC/PROVIDER-QUIRK, not real drift

All 65 remaining planned changes are `google_cloud_run_v2_job.job` resources (mtds-collect-\*, manifest-consolidator-\*,
is-daily-enum-\*, lifecycle-catalogue-\*, t1-recon-\*, sports-enrichment-\*, etc.) showing ONLY `client` and
`client_version` reverting from a gcloud-stamped value (e.g. `"gcloud"` / `"572.0.0"`) to `null` — verified via a
line-range extraction of every update block (none carry any other attribute change; the only 2 exceptions are the
label-only pair classified above). This is a known Cloud Run + Terraform-provider interaction: these jobs are deployed
at RUNTIME by `backends/cloud_run.py`, not by `tofu apply` (`main.tf`'s own header: "Cloud Run Job definitions are
intentionally absent here... deployed at runtime by backends/cloud_run.py"). Every out-of-band `gcloud run jobs deploy`
stamps `client`/`client_version` metadata the committed `.tf` config never sets, so `tofu plan` perpetually shows this
as drift. **Applying would not change how these jobs run** (provider-computed metadata, not a spec you control) and the
diff reimmediately reappears on the next real deploy. The correct fix is a code change
(`lifecycle { ignore_changes = [client, client_version] }` in `modules/container-job/gcp`), not an apply — see follow-up
todo below.

### Recommended apply order (once the `[OPERATOR]` gate below is exercised)

1. `google_service_account.defi_removal_probe` → `google_storage_bucket_iam_member.defi_removal_probe_store_admin` →
   `module.defi_removal_probe_job` → `google_cloud_run_v2_job_iam_member.defi_removal_probe_run_invoker` →
   `google_cloud_scheduler_job.defi_removal_probe_daily` (the resource graph resolves this automatically on a full
   `tofu apply`; stated here only in case of a `-target`-scoped piecemeal apply).
2. `google_project_iam_member.default_compute_sa_datastore_user` (independent).
3. The 4 canonical buckets (independent of each other and of everything above).
4. The 2 t1_recon_job label updates (independent, cosmetic-safe).
5. Do **NOT** apply the 65 client/client_version-only changes — ship the `ignore_changes` code fix first (they'll
   disappear from `tofu plan` entirely once that lands), then confirm zero drift remains.

## Todos

- [x] ✅ [INFRA] P1. **Reconcile the prod terraform drift backlog** (`deployment-service/terraform/gcp`, state
      `terraform/state/prod`): a full `tofu plan` shows 21-add/18-change/0-destroy of committed-but-un-applied resources
      (bigquery feature_external tables, paper_stream, batch_live_smoke_matrix, expected_universe_v2 run.invoker IAM,
      odum_portal domain mapping). Review each is intended + operator-gated apply. Surfaced 2026-06-23 during the
      deadman apply (targeted to avoid sweeping these blindly). — DONE (2026-07-26, slot-11): re-ran `tofu plan` fresh
      (see § above — the 2026-06-23 backlog is entirely gone, replaced by a fresh 10-add/67-change set) and produced the
      full three-way classification. Superseded by the 3 scoped follow-ups below.
- [ ] [OPERATOR] P1. **Gated apply of the 12 INTENDED resources** classified above (`deployment-service/terraform/gcp`,
      state `terraform/state/prod`) — `tofu apply` targeted to just these 12, in the recommended order above. Requires
      an operator with prod-apply authority; do NOT blanket-apply the whole 77-resource diff (65 of the 77 are cosmetic
      and will just re-drift on the next deploy). **Done when**: a `tofu plan` run under a permission set that can see
      them shows zero remaining diff for these 12.
- [ ] [OPERATOR] P1. **Grant `unified-trading-sa` the missing read-only IAM roles** (or designate a more-privileged
      credential for future `tofu plan` runs) so the next drift audit can see the 112 currently-unreadable resources (58
      buckets, 22 secrets, 26 project-IAM members, 6 pubsub). Needs an operator with IAM-admin authority on
      `central-element-323112`. **Done when**: a fresh `tofu plan` produces zero permission-denied read errors.
- [ ] [INFRA] P2. **Add `lifecycle { ignore_changes = [client, client_version] }`** to
      `deployment-service/terraform/modules/container-job/gcp`'s `google_cloud_run_v2_job` resource, so the 65 cosmetic
      client/client_version diffs stop appearing on every `tofu plan` (they reflect out-of-band `backends/cloud_run.py`
      deploys, not real terraform-managed drift). **Done when**: a fresh `tofu plan` shows 0 changes for every
      `module.*_job.google_cloud_run_v2_job.job` / `google_cloud_run_v2_job.vm_log_archival` resource. Repo:
      deployment-service.
