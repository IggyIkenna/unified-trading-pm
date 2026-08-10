---
doc_type: issue
title:
  Prod terraform state drift — 36 add / 18 change / 3 destroy pending in deployment-service/terraform/gcp (as of
  2026-08-07)
summary:
  While syncing the lst-rates scheduler description (slot-11, 2026-08-06) a targeted tofu apply was used to avoid
  inadvertently applying unrelated pending drift. That residual drift was filed as a P2 tracking todo in the OOM issue
  doc. This issue documents the full plan (re-run 2026-08-07 by slot-3) and gates the full prod apply on operator
  review. The 3 destroys include removal of 2 batch-sa Secret IAM members (not in current config) and destruction of the
  `client-reporting-batch` Cloud Run job — the latter requires explicit operator decision.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [terraform, opentofu, prod, drift, cloud-run, iam, operator-review]
related: [/plans/archive/2026_08/issues/defi_mtds_lst_rates_cloud_run_job_oom_2026_08_04.md]
created: 2026-08-07
author: slot-3
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: NA
drift_direction: correct-infra
resolved_by:
locked_by:
source:
  [
    "2026-08-07 (slot-3) — re-ran ENV=prod bash tofu.sh plan from deployment-service/terraform/gcp to verify and
    document the prod terraform drift first observed by slot-11 on 2026-08-06; read-only plan run, no apply.",
  ]
depends_on: []
context_scope:
  [
    deployment-service/terraform/gcp,
    deployment-service/terraform/gcp/client_reporting_scheduler.tf,
    deployment-service/terraform/gcp/t1_batch_scheduler.tf,
    /plans/archive/2026_08/issues/defi_mtds_lst_rates_cloud_run_job_oom_2026_08_04.md,
  ]
---

# Prod terraform drift — 36 add / 18 change / 3 destroy pending apply

## Background

Slot-11 (2026-08-06) ran a TARGETED `tofu apply` against the `lst-rates` scheduler description only to avoid
inadvertently applying the large unrelated pending drift in the prod terraform state
(`deployment-service/terraform/gcp`, backend `terraform/state/prod`). That drift was filed as a P2 tracking todo in
`/plans/archive/2026_08/issues/defi_mtds_lst_rates_cloud_run_job_oom_2026_08_04.md`. This issue doc files the full plan
for operator review and gates the full apply on human sign-off.

**Current state (re-run 2026-08-07, `ENV=prod bash tofu.sh plan`):** `Plan: 36 to add, 18 to change, 3 to destroy.`
(Grew from the 26/17/2 slot-11 observed — additional IaC merges landed on LDR since then without prod apply.)

## Destroys — require explicit human review before applying

These 3 resources would be removed by a full `tofu apply`. The first two are IAM members that are no longer declared in
the IaC config; the third is a Cloud Run job module removal.

### 1. `google_secret_manager_secret_iam_member.t1_batch_gh_pat_accessor` — DESTROY

- Removes: `serviceAccount:uts-prod-batch-sa@central-element-323112.iam.gserviceaccount.com` from
  `roles/secretmanager.secretAccessor` on secret `GH_PAT`
- Reason: `t1_batch_gh_pat_accessor` resource not in current IaC config
- Risk: if anything currently runs as `uts-prod-batch-sa` and needs `GH_PAT` access, it will break

### 2. `google_secret_manager_secret_iam_member.t1_batch_slack_webhook_accessor` — DESTROY

- Removes: `serviceAccount:uts-prod-batch-sa@central-element-323112.iam.gserviceaccount.com` from
  `roles/secretmanager.secretAccessor` on secret `AGENT_ORCHESTRATOR_SLACK_WEBHOOK`
- Reason: `t1_batch_slack_webhook_accessor` resource not in current IaC config
- Risk: if batch-sa needs Slack webhook access, removes it

### 3. `module.client_reporting_batch_job.google_cloud_run_v2_job.job` — DESTROY

- Destroys: `client-reporting-batch` Cloud Run job (`uts-prod-client-reporting-batch`, 2890 prior executions)
- Reason: module not in current `client_reporting_scheduler.tf` config
- Risk: **HIGH** — deletes a live Cloud Run job that has run 2890 times; must confirm the job is truly deprecated

## Key creates (36 total)

| Resource                                        | Purpose                                                                      |
| ----------------------------------------------- | ---------------------------------------------------------------------------- |
| `defi_collect_job["liquidation-events"]` + cron | Aave V3 + Morpho LiquidationCall events — wired by b370df8, never applied    |
| `defi_collect_job["risk-params"]` + cron        | Aave/Spark/Compound V3 reserve config — wired by b370df8, never applied      |
| `defi_removal_probe` SA + job + cron + IAM      | DeFi contract-removal truth-gate                                             |
| 4 GCS buckets                                   | alerting-service, datapoint-validation, kill-switch-audit-log, cicd-events   |
| 9 `google_project_iam_member.*`                 | default compute SA roles, github-actions objectviewer, tier-sa run-developer |
| 3 monitoring alert policies                     | crash-loop + instance-zero + memory-high for new Cloud Run services          |
| 1 storage IAM member                            | uts-test-deployment-scripts-object-admin                                     |

## Key changes (18 total)

| Resource                                     | Change                                                                               |
| -------------------------------------------- | ------------------------------------------------------------------------------------ |
| `defi_collect_cron["lst-rates"]`             | description + CPU 1→2 / memory 4Gi→8Gi (backfill IaC sync, live already at 8Gi/2CPU) |
| `defi_collect_cron["perp-funding"]`          | description update                                                                   |
| `vm_log_archival` + `vm_serial_capture` jobs | in-place update                                                                      |
| `consolidator_liveness_job["fast"/"slow"]`   | in-place update                                                                      |
| `data_pipeline_meta_watchers_job`            | in-place update                                                                      |
| 5 `expected_universe_v2_job[*]`              | in-place update                                                                      |
| 3 `manifest_consolidator_job[*]`             | add `CONSOLIDATOR_STALL_ALERT_CYCLES` env var; some memory changes                   |
| 2 `instruments_*_t1_recon_job`               | in-place update                                                                      |
| `is_daily_enum_job["prediction"]`            | in-place update                                                                      |

## Recommended approach for operator

1. **Confirm `client-reporting-batch` is deprecated** before approving the full apply (check
   `client_reporting_scheduler.tf` — if the module block was intentionally removed, the destroy is correct; if it was
   accidentally dropped, restore it before applying).
2. **Confirm the 2 batch-sa Secret IAM member removals are intentional** (check `t1_batch_scheduler.tf` — if these were
   deliberately removed from config, the destroy is correct).
3. Run `ENV=prod bash tofu.sh plan -no-color` from `deployment-service/terraform/gcp` to review the current full plan
   before applying.
4. Run `ENV=prod bash tofu.sh apply` when satisfied.

## Todos

- [ ] [OPERATOR] P1. **RE-SCOPED 2026-08-09 — the plan has grown far beyond "3 destroys" since this todo was written.**
      A fresh `ENV=prod bash tofu.sh plan` now shows **36 to add, 17 to change, 4 to destroy** (real drift accumulated
      from active development since 2026-08-07, not a sign of anything wrong). Full analysis in the Progress Log entry
      below. A full raw-plan read (not just the categorized summary) found one specific in-place update that should be
      excluded or confirmed before apply: `module.data_pipeline_meta_watchers_job` would be shrunk from its currently
      LIVE `cpu=8/memory=32Gi` down to the committed IaC's `cpu=4/memory=16Gi` — see the second Progress Log entry below
      for why this looks like an un-backported live capacity fix, not safe routine drift. Awaiting explicit operator
      go-ahead given the scale change from what was originally reviewed — do NOT delegate to AO, still a prod infra
      apply with destructive changes.

## Progress Log

- **na-eligibility-audit 2026-08-08 (cross-cutting tranche)**: KEEP-NA, valid — sole open todo is explicitly
  `[OPERATOR]`-tagged with the doc's own text stating "Do NOT delegate to AO — this is a prod infra apply with
  destructive changes" (3 terraform destroys against live prod state, including a live Cloud Run job with 2890 prior
  executions).
- **context-scout 2026-08-09**: populated context_scope (4 entries).
- **2026-08-09 (interactive session)**: operator authorized proceeding on this todo; ran `ENV=prod bash tofu.sh init`
  (was needed — 3 modules not yet installed on this checkout) then a fresh `plan`. The live plan is dramatically bigger
  than this doc's original "3 destroys" framing: **36 to add, 17 to change, 4 to destroy**. Full breakdown:
  - **The originally-reviewed `client-reporting-batch` Cloud Run job destroy is now MOOT** — live-checked via
    `gcloud run jobs describe uts-prod-client-reporting-batch`: it no longer exists. Someone already applied that part
    of the drift since this doc was written.
  - **The 2 Secret IAM member destroys still match** (`t1_batch_gh_pat_accessor`, `t1_batch_slack_webhook_accessor`) —
    unreviewed by this pass beyond confirming they're still present in the plan.
  - **2 new, never-reviewed destroys**: `google_cloud_scheduler_job.defi_collect_cron["token-transfers"]` and
    `module.defi_collect_job["token-transfers"]` — NOT a loss, a deliberate replacement: the plan simultaneously
    _creates_ `liquidation-events` and `risk-params` scheduler+job pairs (visible in the `defi_collect_cron_names`/
    `defi_collect_job_names` output diff), consistent with this session's broader DeFi collector restructuring work.
  - **36 creates are almost entirely additive**: 4 new GCS buckets (`alerting-service-*`, `*-datapoint-validation`,
    `*-kill-switch-audit-log`, `unified-trading-cicd-events`); 13 new IAM grants (mostly
    `google_project_iam_member.default_compute_sa_*` — reads as "adopt already-live permissions into Terraform," the
    same safe pattern used in this session's AWS CodeBuild ruling, not a new grant of access); 6 new monitoring alert
    policies (crash-loop/memory-high/instance-zero on `central-market-data-tardis-loader`, `market-data-query-service`,
    `uts-prod-data-status-rollup-svc`); a wholly new `defi_removal_probe` service (SA + Cloud Run job + IAM + scheduler)
    being stood up.
  - **17 in-place updates are routine**: label/tag drift, a memory-limit reduction (16Gi→8Gi on
    `is_daily_enum_job["prediction"]`), new `CONSOLIDATOR_STALL_ALERT_CYCLES` env vars on 3 manifest-consolidator jobs.
  - **Assessment: this reads as healthy drift from active, unrelated development landing on this repo since 2026-08-07,
    not a dangerous or suspicious plan.** Full raw plan output not attached here (2394 lines) — re-run
    `ENV=prod bash tofu.sh plan -no-color` from `deployment-service/terraform/gcp` for the live version before applying;
    this analysis is a point-in-time read given how fast this repo is moving today. Did NOT run `apply` — left for
    explicit final operator go-ahead given the scope grew well past what was originally authorized.
- **2026-08-09 (interactive session, full raw-plan review)**: operator asked to actually read the full 2394-line raw
  `plan -no-color` output rather than trust the categorized summary above. Grepped every
  `will be destroyed`/`will be created`/`will be updated in-place` block and read each in full.
  - **The 4 destroys match the summary exactly, no surprises**: `defi_collect_cron["token-transfers"]` +
    `defi_collect_job["token-transfers"]` (confirmed deliberate replacement — the job's own `create_time` in the plan is
    TODAY, 2026-08-09, meaning it was stood up live very recently and is already being superseded), plus the 2
    `t1_batch_*_accessor` Secret IAM member removals. No `force new resource` / replacement anywhere in the plan.
  - **All 36 creates individually enumerated and match the summary** — no hidden deletions disguised as creates. Three
    IAM-condition members (`uts_prd_objectadmin_group_a`, `uts_test_objectadmin_group_a`,
    `github_actions_deploy_objectviewer_group_a`) show as creates despite an identically-titled/conditioned binding
    already appearing in the refresh log — most likely the provider's `Read()` no longer matches the state's literal
    condition-text-embedded ID (a byte-level formatting difference), so `apply` would re-assert an already-live binding.
    GCP conditional IAM bindings are idempotent on (role, member, condition), so worst case this is a no-op, not a
    duplicate grant — noted for completeness, not blocking.
  - **NEW FINDING — one of the 17 in-place updates is NOT routine and should be excluded or confirmed before apply**:
    `module.data_pipeline_meta_watchers_job.google_cloud_run_v2_job.job` would change `cpu 8->4` and
    `memory 32Gi->16Gi`. The committed `.tf` (`data_pipeline_fleet_monitor_scheduler.tf:181-186`) declares 16Gi/cpu4
    with a comment dated 2026-06-24: _"the meta sweep OOM'd at 2/4/8Gi (signal 9)... 16Gi is green"_ — but the plan's
    refreshed LIVE state shows this job is currently running at double that, 32Gi/cpu8, and `gcloud run jobs describe`
    shows the live job's `lastModifier` annotation as `creator=ikenna@odum-research.com` via the `gcloud` CLI client —
    i.e. the operator manually bumped this job's resources live, outside Terraform/CI, and the `.tf` file (and its
    now-stale comment) was never updated to match. Given this job's own comment history is a repeated pattern of "corpus
    grew -> prior memory ceiling became insufficient -> OOM -> bump" (2Gi->4Gi->8Gi->16Gi documented, now apparently
    ->32Gi live), applying this plan as-is would silently undo that live fix and likely reintroduce the exact
    OOM/stale-sentinel/deadman-page failure mode the `.tf` comment itself describes. Contrast with the OTHER memory
    reduction in this plan, `is_daily_enum_job["prediction"]` 16Gi->8Gi (line 2285 of the raw plan): that one's `.tf`
    comment cites a measured RSS figure ("prediction enumerates 50k+ Polymarket markets, 5+ GB RSS observed; 8Gi
    prevents OOM") with ~3GB of headroom above measured peak — that reduction reads as safe. The meta-watchers one has
    no comparable fresh evidence backing 16Gi as sufficient at current corpus size.
  - **Recommendation**: apply everything except `data_pipeline_meta_watchers_job`, either via `-target` exclusion or by
    bumping the `.tf` config to `cpu=8/memory=32Gi` first (to match and codify the live fix) before a full apply. Do not
    apply the plan as-is without addressing this one resource.
  - **All other 16 in-place updates reviewed and confirmed routine**: label/purpose-tag renames on the
    `instruments_*_t1_recon_job`s (`t1-recon`->`t1-batch-{cefi,prediction}`, service name sync), scheduler description
    text updates on `lst-rates`/`perp-funding` (both purely descriptive, documenting already-applied historical live
    memory bumps), and the `liquidation-events`/`risk-params` output-map additions. No other memory/cpu/env changes
    found beyond the two already discussed.
