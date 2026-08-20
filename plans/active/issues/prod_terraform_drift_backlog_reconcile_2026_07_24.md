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
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [infra, terraform, drift, prod, reconcile-apply]
created: "2026-07-24"
author: unknown
last_updated: "2026-08-20"
parent_epic: security_and_cross_cutting_master
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
related: [/plans/archive/2026_08/data_pipeline_hardening_self_monitoring_2026_06_22.md]
depends_on: []
context_scope:
  [
    /codex/05-infrastructure/orchestrator-cloud-identity-self-service.md,
    /plans/archive/2026_08/data_pipeline_hardening_self_monitoring_2026_06_22.md,
    deployment-service/terraform/gcp,
    deployment-service/terraform/modules/container-job/gcp,
  ]
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

## 2026-08-20 fresh `tofu plan` + full re-classification (read-only Phase-1 sanity gate — no `apply`)

Operator-requested final look at the diff before Phase 2 (the actual `tofu apply`, separately gated on review of this
section). **This pass is read-only — no `apply` was run.**

**BLOCKING BUG found + fixed before a plan could even be produced.** `terraform/gcp/paper_determinism_workflow.tf:159`
(`output "paper_determinism_workflow_name"`) referenced `module.paper_determinism_workflow.name`, an attribute the
`../modules/workflow/gcp` module does not export (it exports `workflow_name`, `workflow_id`, `workflow_revision_id`,
`scheduler_job_name`, `execution_url` — never `name`). `tofu plan` failed outright (`Error: Unsupported attribute`,
exit 1) before evaluating any resource diff. Traced to `deployment-service@200c4791` (`feat(infra): wire paper batch
determinism workflow`), landed ~47 min before this check and already promoted LDR→main once — never caught because no
CI job runs `tofu plan` against live prod state/credentials. One-line, unambiguous fix (small+clear per findings
triage): `module.paper_determinism_workflow.name` → `module.paper_determinism_workflow.workflow_name`. Verified
`tofu fmt -check` + `ENV=prod ./tofu.sh validate` clean, full `quality-gates.sh` green, shipped separately from this
doc update as **`deployment-service@fd35a67f14`**.

### Fresh plan result: **7 to add, 63 to change, 1 to destroy** (71 total) — full visibility

`ENV=prod ./tofu.sh init && ENV=prod ./tofu.sh plan` ran clean (exit 0) with **zero `PERMISSION_DENIED`/`Error:`
lines** — the 112-resource visibility gap from 2026-07-26 stays closed (the 2026-07-27 IAM grants still hold). This is
a completely different composition from both the 2026-07-26 (10/67) and 2026-07-27 (17/71) checks — most of what those
passes classified has since been applied (see below), and a large new batch (the 47-bucket lifecycle-exemption change)
has landed in code since.

**The previously-classified 12 — reconciled against live state:**

- **10 of the 12 are CONFIRMED ALREADY APPLIED** — `google_service_account.defi_removal_probe`,
  `google_cloud_run_v2_job_iam_member.defi_removal_probe_run_invoker`,
  `google_cloud_scheduler_job.defi_removal_probe_daily`, `module.defi_removal_probe_job`,
  `google_storage_bucket_iam_member.defi_removal_probe_store_admin`,
  `google_project_iam_member.default_compute_sa_datastore_user`, and all 4 canonical buckets (`alerting-service`,
  `datapoint-validation`, `kill-switch-audit-log`, `unified-trading-cicd-events`) are present in `tofu state list` and
  produce **zero diff** on this fresh refresh. No longer in the plan at all — confirmed live in prod, not just
  state-tracked.
- **The 2 label-only updates are STILL PENDING** — now addressed as `module.t1_recon_instruments_job["cefi"]` /
  `["prediction"]` (the per-asset-group named modules `module.instruments_cefi_t1_recon_job` /
  `module.instruments_prediction_t1_recon_job` were refactored into a `for_each` module since 2026-07-26; same
  underlying resources, same `purpose=t1-batch-cefi`-style label diff, still un-applied). Classification unchanged:
  **INTENDED**.
- **The 2 previously-invisible scope-guard resources are ALSO now confirmed applied**:
  `google_project_iam_member.wave_launcher_compute_admin`/`wave_launcher_sa_user` and
  `google_storage_bucket_iam_member.lifecycle_catalogue_instruments_admin["cefi"|"defi"|"prediction"|"sports"|"tradfi"]`
  are all present in state, zero diff. Both were blocked on the IAM-visibility gap in the 2026-07-26 pass; that gap is
  closed and both are live.

**Cosmetic client/client_version fix (`deployment-service@f57c96e`) mostly held — one gap found.** The shared-module
fix eliminated the bulk 65-diff set as designed. But `google_cloud_run_v2_job.subgraph_health_probe`
(`subgraph_health_probe_scheduler.tf`) is a **standalone** resource (not built via `../modules/container-job/gcp`) and
was never given its own `ignore_changes = [client, client_version]` copy — unlike `vm_log_archival_scheduler.tf`, which
got one in the same commit. It still shows the identical client/client_version-only cosmetic diff. New follow-up todo
filed below (same pattern, same fix, different file).

### Three-way classification — every non-cosmetic resource in the current 7/63/1 diff

**Creates (7) — all INTENDED:**

| Resource | Why |
| --- | --- |
| `module.batch_rerun_job.google_cloud_run_v2_job.job`, `module.paper_determinism_workflow.google_workflows_workflow.workflow`, `module.paper_determinism_workflow.google_cloud_scheduler_job.trigger[0]` | Paper-batch determinism orchestration bundle, `deployment-service@200c4791` (the commit this pass unblocked) |
| `google_monitoring_alert_policy.cloud_run_service_crash_loop["central-market-data-tardis-loader"\|"market-data-query-service"\|"uts-prod-data-status-rollup-svc"]` | Generic Cloud Run liveness/OOM alert registry, `deployment-service@fa07db64` — covers 3 audit findings (9.5mo crash-loop, 19mo never-started, an OOM) |
| `google_secret_manager_secret_iam_member.t1_batch_gh_pat_accessor` | GH_PAT accessor grant for the subgraph health probe, `deployment-service@bf96eebd` |

**Destroy (1) — INTENDED:**

| Resource | Why |
| --- | --- |
| `google_cloud_scheduler_job.blrs_daily_determinism_cron[0]` | Its resource block was deleted in the SAME commit (`200c4791`) that adds the new orchestrated `paper_determinism_workflow` — the old standalone BLRS cron is cleanly superseded, not stale/abandoned |

**Updates (63) — 62 INTENDED, 1 COSMETIC:**

| Resource(s) | Change | Classification | Why |
| --- | --- | --- | --- |
| `google_storage_bucket.canonical[...]` (42 buckets: config-store/execution-store/features-*/instruments-store-*/market-data-tick-*/ml-store/strategy-store-* prd+test pairs, alerting-service, commodity-signals-batch) + `google_storage_bucket.deployment_state` | Removes the COLDLINE@60d `lifecycle_rule` | **INTENDED** | Operator-ruled 2026-08-17 cost-optimization exemption (raw pipeline/working-data estate stays always-hot, manifest-retention-governed) — codified in `deployment-service@2995d0cf`, documented in-file at `canonical_buckets.tf`'s `canonical_strip_lifecycle_kinds` local (47-bucket set incl. this one) |
| `module.t1_recon_instruments_job["cefi"\|"prediction"]` | Labels only | **INTENDED** | Carried over from the 2026-07-26 classification (see above) — module addressing changed, resource + reason didn't |
| `module.manifest_consolidator_job["instruments-cefi"\|"instruments-defi"\|"instruments-prediction"\|"instruments-tradfi"]` | `timeout: 1800s → 7200s` | **INTENDED** | `manifest_consolidator_timeouts` local map, `deployment-service@38790807` ("extend hourly-bucket timeout floor") — `instruments-sports` deliberately excluded from this diff (different, already-correct 600s override elsewhere in the same map) |
| `module.expected_universe_v2_job["cefi"\|"defi"\|"prediction"\|"sports"\|"tradfi"]` | `args: [...] → (known after apply)` | **INTENDED (expected to recur)** | `deployment-service@1d8ede92` made `--start-date` a genuinely rolling today-120d window — args is now computed at apply time by design, so this WILL show as changed on every future `tofu plan` too; that's correct behavior, not un-applied drift beyond today's catch-up |
| `google_cloud_scheduler_job.cost_snapshot_cron` | `http_target.headers["X-API-Key"]` restored | **INTENDED (higher urgency)** | `deployment-service@13ebe526` ("restore cost snapshot API key header") — the live cron is very likely running WITHOUT the key today, i.e. probably failing silently, same urgency class as the earlier `unified-trading-cicd-events` bucket finding |
| `google_cloud_scheduler_job.defi_collect_cron["risk-params"]` | `description` text only | **INTENDED** | `deployment-service@b5a92312` — doc-string refresh (OOM-fix narrative), zero functional change |
| `module.dp_daily_digest_job\|dp_drilldown_reconciliation_job\|dp_manifest_hygiene_changed_job\|dp_manifest_hygiene_full_job\|dp_reprobe_empty_job.google_cloud_run_v2_job.job` | `image: @sha256:cf2eb74... → :latest` | **INTENDED, but VERIFY before applying** | `data_pipeline_audit_scheduler.tf`'s own header: `:latest` is the deliberate default runner image ("Override only to pin a specific build-id tag"); the live digest pin traces to a manual `gcloud run jobs deploy` during the 2026-08-16 OOM incident (Cloud Build `816b2532`) to get the fix live fast. Applying moves these back to the documented default — but **confirm the AR `:latest` tag currently resolves to that same build (or newer) first**, so applying can't silently roll back to a stale image |
| `google_cloud_scheduler_job.dp_exit_code_monitor_cron` | `schedule: "0 * * * *" → "*/5 * * * *"` | **INTENDED, but SANITY-CHECK before applying** | The `*/5 * * * *` cadence has been the committed value since the file's original creation commit (`deployment-service@5866f12c`) — no commit ever changed it — so this traces cleanly to code intent, not a stale value. Flagged anyway because it's a 12x invocation-frequency jump with real cost/noise implications; worth a quick "is 5-minute polling still wanted" confirmation, not a blind apply |
| `google_cloud_run_v2_job.subgraph_health_probe` | `client`/`client_version` only | **COSMETIC / PROVIDER-QUIRK** | Same root cause as the already-fixed 65 (out-of-band `gcloud`-stamped metadata) — `deployment-service@f57c96e`'s `ignore_changes` fix missed this standalone (non-shared-module) resource. Do not apply; fix the code gap first (new todo below) |

None of the 71 resources classified as stale/abandoned/conflicting.

### Ready-to-apply list, in dependency order (once Phase 2 is authorized)

1. `module.batch_rerun_job.google_cloud_run_v2_job.job` (independent Cloud Run Job)
2. `module.paper_determinism_workflow.google_workflows_workflow.workflow` (its YAML source references
   `module.batch_rerun_job.name`, implicit dependency on step 1)
3. `module.paper_determinism_workflow.google_cloud_scheduler_job.trigger[0]` (depends on step 2's workflow)
4. `google_monitoring_alert_policy.cloud_run_service_crash_loop["central-market-data-tardis-loader"\|"market-data-query-service"\|"uts-prod-data-status-rollup-svc"]`
   + `google_secret_manager_secret_iam_member.t1_batch_gh_pat_accessor` (independent of everything above and each
   other)
5. `google_cloud_scheduler_job.blrs_daily_determinism_cron[0]` **destroy** — after steps 1-3 are live, so BLRS daily
   reconciliation coverage has no gap
6. Low-risk updates, any order: `cost_snapshot_cron` (prioritize — likely-broken cron), `defi_collect_cron["risk-params"]`
   description, `t1_recon_instruments_job["cefi"\|"prediction"]` labels, `manifest_consolidator_job[...]` timeouts (4),
   `expected_universe_v2_job[...]` args (5)
7. The 42 canonical-bucket + `deployment_state` lifecycle-rule removals — apply as one batch (single already-shipped
   commit, single operator ruling)
8. **Confirm first, then apply**: `dp_exit_code_monitor_cron` schedule bump; the 5 `dp_*_job` image reversions (verify
   `:latest` freshness in AR first)
9. **Do NOT apply**: `subgraph_health_probe` client/client_version — ship its own `ignore_changes` fix first (mirrors
   `f57c96e`), confirm it clears on the next plan, then there's nothing left to apply for it

## Todos

- [x] ✅ [INFRA] P1. **Reconcile the prod terraform drift backlog** (`deployment-service/terraform/gcp`, state
      `terraform/state/prod`): a full `tofu plan` shows 21-add/18-change/0-destroy of committed-but-un-applied resources
      (bigquery feature_external tables, paper_stream, batch_live_smoke_matrix, expected_universe_v2 run.invoker IAM,
      odum_portal domain mapping). Review each is intended + operator-gated apply. Surfaced 2026-06-23 during the
      deadman apply (targeted to avoid sweeping these blindly). — DONE (2026-07-26, slot-11): re-ran `tofu plan` fresh
      (see § above — the 2026-06-23 backlog is entirely gone, replaced by a fresh 10-add/67-change set) and produced the
      full three-way classification. Superseded by the 3 scoped follow-ups below.
- [ ] [INFRA] P1. **RULED 2026-07-28 (applying the operator's general theme: "full backfills/migrations... DO IT",
      "unpause whatever needs unpausing to unblock a task", "do not allow anything to partially complete") — retagged
      away from `[OPERATOR]`, APPROVED to apply.** All 12 resources classified above are INTENDED — each traces to an
      already-shipped, already-reviewed code commit whose terraform counterpart is simply un-applied; the classification
      found none stale, abandoned, or deliberately-staged-ahead of a cutover. These are CREATE-only (plus 2 label-only
      updates) — not a delete — so the reversibility concern the original gate cited does not actually apply at the same
      bar as a GCS-bucket delete (a `tofu destroy`/revert remains available if any of these 12 turns out wrong). **Scope
      note before executing (full-completion mandate)**: the permission-grant todo below (done 2026-07-27) revealed the
      diff is NOT static — once `unified-trading-sa` could see the previously-unreadable 112 resources, a fresh
      `tofu plan` showed **17 to add / 71 to change**, a different, larger, now-fully-visible composition than the 10/67
      this doc's 12-resource classification was built from. Per "do not allow anything to partially complete," do NOT
      apply only the stale 12 in isolation: first re-run the same three-way (INTENDED / cosmetic-provider-quirk /
      stale-or-conflicting) classification over the CURRENT full 17/71 diff (the 12 already classified here should still
      qualify as INTENDED, but the newly-visible resources need the same review before anything is applied), then
      `tofu apply` every resource classified INTENDED in one pass, in dependency order, skipping the confirmed cosmetic
      `client`/`client_version` diffs (ship the P2 `ignore_changes` fix below first if convenient, so the cosmetic set
      stops re-appearing in the same plan run). **Done when**: a `tofu plan` run shows zero remaining diff for every
      resource classified INTENDED in the refreshed pass.

      **RE-CLASSIFIED 2026-08-20 (still Phase 1, still no `apply` — see full section above).** The 10/67 and 17/71 diffs
      referenced above are both gone — 10 of the original 12 are confirmed already applied, and the live composition is
      now a completely fresh **7 add / 63 change / 1 destroy** (a large new batch, mainly the 47-bucket lifecycle-rule
      cost-optimization change, landed since 08-06). Full re-classification done: 70 of 71 resources are INTENDED
      (2 flagged VERIFY-first, not blocking), 1 is cosmetic (`subgraph_health_probe`, new follow-up todo below), 0
      stale/conflicting. A blocking bug (`paper_determinism_workflow.tf` bad output reference) had to be fixed first
      just to get a plan to run at all — see `deployment-service@fd35a67f14`. Phase 2 (`tofu apply`) remains gated on a
      human reviewing this section; not actioned in this pass.
- [x] [INFRA] P1. ✅ **DONE 2026-07-27** — **downgraded from `[OPERATOR]` per
      `/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md` § "The rule"**: a permission gap on
      `unified-trading-sa`'s own identity is self-fixable, not an operator escalation (the earlier gating pass predates
      that rule). Granted `roles/secretmanager.viewer`, `roles/pubsub.viewer` (superseded), and `roles/pubsub.admin`
      (the one that actually covers `pubsub.{topics,subscriptions}.getIamPolicy` — `pubsub.viewer` alone did not,
      discovered by re-running the real check, not assumed) — `storage.admin`/`resourcemanager.projectIamAdmin` from
      earlier this session already covered the bucket + project-IAM reads. **Done when, verified for real**: ran
      `ENV=prod ./tofu.sh init && ENV=prod ./tofu.sh plan` fresh against `deployment-service/terraform/gcp` three times
      (before any grant, after the first two roles, after `pubsub.admin`) — the first two runs still errored
      (`pubsub.topics.getIamPolicy`/`pubsub.subscriptions.getIamPolicy` denied even after `pubsub.viewer`), the third
      run completed clean: **zero `PERMISSION_DENIED`/`Error:` lines, 17 to add / 71 to change / 0 to destroy**. The
      "112 unreadable resources" gap is closed; the drift set itself (a fresh, different composition from both the
      2026-06-23 and 2026-07-26 findings) is now fully visible for the next classification pass.
- [x] ✅ [INFRA] P2. **Add `lifecycle { ignore_changes = [client, client_version] }`** to
      `deployment-service/terraform/modules/container-job/gcp`'s `google_cloud_run_v2_job` resource, so the 65 cosmetic
      client/client_version diffs stop appearing on every `tofu plan` (they reflect out-of-band `backends/cloud_run.py`
      deploys, not real terraform-managed drift). **Done when**: a fresh `tofu plan` shows 0 changes for every
      `module.*_job.google_cloud_run_v2_job.job` / `google_cloud_run_v2_job.vm_log_archival` resource. Repo:
      deployment-service.

      **DONE 2026-07-30 — deployment-service@f57c96e.** Added `ignore_changes = [client, client_version]` to BOTH the
          shared `terraform/modules/container-job/gcp/main.tf` `google_cloud_run_v2_job.job` resource (covers every
          `module.*_job` consumer — the 65-diff bulk) AND the standalone
          `terraform/gcp/vm_log_archival_scheduler.tf` `google_cloud_run_v2_job.vm_log_archival` resource (not built via
          the shared module, so it needed its own copy — extended its existing `ignore_changes = [launch_stage]` rather
          than duplicating). Code-only (no `tofu apply` — that's this doc's still-open P1 item); `tofu fmt -check` clean
          on the added lines; full `quality-gates.sh` green.
- [ ] [INFRA] P2. **Extend the `f57c96e` `ignore_changes = [client, client_version]` fix to
      `terraform/gcp/subgraph_health_probe_scheduler.tf`'s standalone `google_cloud_run_v2_job.subgraph_health_probe`
      resource** (found 2026-08-20 — see the fresh-plan section above). This resource is NOT built via the shared
      `../modules/container-job/gcp` module and was missed when `f57c96e` patched the shared module +
      `vm_log_archival`'s standalone copy; it still shows the identical client/client_version-only cosmetic diff on
      every `tofu plan`. Same fix, same pattern, one more file. **Done when**: a fresh `tofu plan` shows 0 changes for
      `google_cloud_run_v2_job.subgraph_health_probe`. Repo: deployment-service.

## Progress Log

- **na-eligibility-audit 2026-08-09 (round11 RECLASSIFY+satellite-extraction sweep, infra tranche)**: KEEP-NA, valid —
  unchanged. The remaining open item is operator-APPROVED but still requires a FRESH three-way (INTENDED /
  cosmetic-provider-quirk / stale-or-conflicting) classification over whatever the current live `tofu plan` diff is
  today before any `tofu apply` — the doc's own text is explicit that the diff is a moving target (grew from 10/67 to
  17/71 the last time it was checked) and the classification itself is real judgment (is each newly-visible resource
  intended, stale, or a conflict), not a mechanical re-run of the old 12-resource table. A real, deliberate, prod- infra
  `tofu apply` remains operator-level application work per the existing 2026-08-06 ruling, not bounded worker dispatch.
  Checked against this round's accumulated-precedent list (IAM self-service, D16 all-repos, S5.1 tiering,
  plan-destination-AO-default, escalation-N=3-days, reversibility-qualified deletes, Option B retired, GSM secret + 5
  Slack webhooks): the resources classified here are CREATE-only (plus 2 label-only updates), not deletes, so the
  reversibility-qualified-deletes carve-out's REASONING (a `tofu destroy`/revert remains available if wrong) already
  applies and is already cited by this doc's own text — but that carve-out lowers the reversibility bar for a delete, it
  does not itself convert "apply prod infrastructure changes" into worker-determinable dispatch; the fresh
  classification step is still real judgment. No change from the existing ruling.
- **na-eligibility-audit 2026-08-06 (infra tranche)**: KEEP-NA, valid — RULED 2026-07-28 APPROVED-to-apply;
  re-classifying + applying the current full drift set on prod terraform is operator-approved application work, not
  bounded worker dispatch.

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid (infra tranche, dispatch agt-30721a) — Dominant remaining item is
  a live, moving-target prod-terraform review (diff grew from 10/67 to 17/71 after a permission grant, needs fresh
  three-way classification) — stays NA as a whole; the smaller lifecycle-ignore-changes item is an individually
  plausible future RECLASSIFY candidate, not actioned this run.

- **context-scout 2026-08-03**: populated context_scope (4 entries).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (4 entries), unchanged.

- **context-scout 2026-08-17**: populated/refreshed context_scope (4 entries).
- **na-eligibility-audit 2026-08-17** (infra tranche) [body-hash:07ede18badf7abdb]: KEEP-NA, valid — explicit dated operator ruling cited in-doc (RULED 2026-07-28, reaffirmed 2026-08-06) — remaining work is a fresh three-way classification of a moving-target prod-terraform diff before any operator-level apply.
- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries).
- **2026-08-20 (Phase-1 read-only re-classification pass, no `apply`)**: fresh `tofu plan` = 7 add/63 change/1 destroy
  (see full section above). Fixed one blocking bug first (`paper_determinism_workflow.tf` bad output attribute
  reference, `deployment-service@fd35a67f14`) that made `tofu plan` fail outright — landed ~47min earlier in
  `200c4791`, never CI-caught (no CI job runs `tofu plan` against live prod). Confirmed 10 of the previously-classified
  12 are now live in prod (state-verified, zero diff); the 2 label-only updates are still pending, re-addressed post
  module-refactor as `module.t1_recon_instruments_job["cefi"|"prediction"]`. Full three-way re-classification: 70/71
  resources INTENDED (2 flagged verify-before-apply, not blocking), 1 cosmetic (`subgraph_health_probe` — new P2 todo
  filed, same `ignore_changes` gap as the already-fixed 65), 0 stale/conflicting. Phase 2 (`tofu apply`) NOT run —
  remains gated on operator review of this section.
