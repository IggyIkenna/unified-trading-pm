---
doc_type: issue
title:
  "38 Cloud Scheduler jobs (37 asia-northeast1 + 1 europe-west1) target Cloud Run Jobs that no longer exist —
  bulk-paused, 4 with an obvious live successor flagged for operator repoint review"
summary: >-
  Follow-up bulk triage on `infra_health_audit_findings_fix_2026_08_07.md` todo 1 ("Dedicated zombie sweep"). Re-derived
  the scheduler↔Cloud-Run-Job cross-reference from scratch (not trusting the originating audit's headline counts):
  listed every `asia-northeast1` Cloud Scheduler job (158 total) plus the one in-scope `europe-west1` job
  (`central-market-data-service-scheduler-trigger` — the workspace's OTHER 3 europe-west1 zombies,
  `gen-inst-defs-scheduler`/`check-missing-cloud-storage-scheduler`/`tardis-data-loader-scheduler`, were already fixed
  by a concurrent agent directly in the parent plan's todo, not duplicated here), extracted each `httpTarget.uri`'s
  target Cloud Run Job name, and cross-checked against `gcloud run jobs list` for both regions. **38 schedulers target a
  Cloud Run Job that does not exist** (confirmed via the live jobs list, not just the audit's claim): 32 were `ENABLED`
  (including the 1 europe-west1 job — the audit's own headline said "31 asia-northeast1"; the 1-count delta is the
  europe-west1 job, correctly in scope here per the task split), 6 were already `PAUSED`. All 32 `ENABLED` ones were
  bulk-paused via `gcloud scheduler jobs pause` and verified `state: PAUSED` post-pause. Cloud Logging
  (`resource.type="cloud_scheduler_job"`, 2-day window) confirms all 32 fired at least once today (2026-08-07) before
  being paused; the 6 already-`PAUSED` ones show zero attempts in the same 2-day window (already dormant coming in). 4
  of the 38 have an obvious live successor by name-similarity + matching/near-matching schedule — flagged separately
  below as REPOINT CANDIDATES, not auto-repointed (a bigger decision per task scope). The remaining 34 (mostly
  `uts-{dev,staging}-*-t1-schedule` targeting `*-t1-recon`/`*-service` Cloud Run Jobs across
  features-{delta-one,cross-instrument,multi-timeframe,volatility,calendar,commodity}, ml-inference, ml, strategy,
  execution-config-snapshot, batch-live-reconciliation, market-data-processing, market-tick-data, instruments) have NO
  same-tier Cloud Run Job at all in either region — for most families only the `uts-prod-*` variant exists (already
  alive, already has its own working `ENABLED` scheduler) — dev/staging-tier T1-recon jobs appear to have been
  decommissioned or never deployed as separate Cloud Run Jobs, with their schedulers left un-pruned. Repointing a
  dev/staging scheduler to the prod-tier job would change environment semantics — correctly out of scope for
  auto-repoint, not flagged as a repoint candidate, just paused.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [cloud-scheduler, cloud-run, zombie, dead-target, infra-health-audit, gcp, bulk-triage]
related: [/plans/active/infra_consolidated_closeout_2026_07_25.md]
created: 2026-08-07
last_updated: 2026-08-21
parent_epic: observability_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: infra
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
source:
  "infra_health_audit_findings_fix_2026_08_07.md todo 1 (Dedicated zombie sweep) — Cloud-Scheduler-dead-target class"
context_scope:
  [
    /plans/archive/2026_08/infra_health_audit_findings_fix_2026_08_07.md,
    deployment-service/terraform/gcp/t1_batch_scheduler.tf,
    /plans/active/issues/deployment_service_t1_recon_duplicate_module_definitions_2026_08_09.md,
  ]
---

# 38 asia-northeast1 (+1 europe-west1) Cloud Scheduler jobs with dead Cloud Run Job targets

## Method

1. `gcloud scheduler jobs list --project=central-element-323112 --location=asia-northeast1 --format="table(name,schedule,state,httpTarget.uri)"`
   — 158 rows. Plus the single in-scope `europe-west1` job `central-market-data-service-scheduler-trigger` (the other 3
   europe-west1 zombies from the same original audit were already resolved by a concurrent agent inside the parent
   plan's own todo — not re-touched here).
2. `gcloud run jobs list --project=central-element-323112 --region={asia-northeast1,europe-west1}` — live job inventory
   for both regions (114 asia-northeast1 jobs, 7 europe-west1 jobs).
3. Regex-extracted each scheduler's target job name from `.../namespaces/central-element-323112/jobs/{name}:run` (145 of
   the 158 rows target a Cloud Run Job this way; the other 13 target Cloud Workflows, GCE VM `instances.start`, or a
   Cloud Run **Service** HTTP endpoint — out of scope, a Cloud Run Job "doesn't exist" check doesn't apply to those
   target types).
4. Cross-checked each target name against the live jobs list for its region. **38 of the 145 targets do not exist.**
5. For each dead target, ran `difflib.get_close_matches` against the full live-job list (both regions) plus a
   live-successor-scheduler check (does a _different_, currently-succeeding scheduler already point at the closest-match
   job on a similar cadence) — this is the "obvious live successor" quick check from the task, not a deep investigation
   per item.
6. Pulled `gcloud logging read 'resource.type="cloud_scheduler_job" AND (job_id="..." OR ...)' --freshness=2d` once for
   all 38 names together (avoids 38 separate `describe` calls) to get last-fired evidence — **note**:
   `gcloud scheduler jobs describe` clears `status`/`lastAttemptTime` once a job is `PAUSED`, so Cloud Logging is the
   only source for this once a job is paused (a wrinkle worth knowing for future scheduler-pause hygiene — grab
   `lastAttemptTime` via `describe` BEFORE pausing if you need it recorded from that source).
7. Bulk-paused all 32 `ENABLED` dead-target schedulers via `gcloud scheduler jobs pause <name> --location=<region>`,
   verified 38/38 (32 just-paused + 6 already-paused) show `state: PAUSED` in a fresh `jobs list` post-action.

## Repoint candidates (flagged only — NOT auto-repointed; needs an operator/follow-up pass)

| #   | Dead scheduler                                                  | Dead target                                                                                                 | Live successor found                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | Evidence |
| --- | --------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| 1   | `uts-prod-client-reporting-hourly-update` (asia, `5 * * * *`)   | `uts-prod-client-reporting-update`                                                                          | Cloud Run Job **`client-reporting-batch`** (asia-northeast1, exists) via the already-`ENABLED` scheduler **`client-reporting-hourly`** — **identical schedule** `5 * * * *`, confirmed succeeding hourly. This is the task's own confirmed example.                                                                                                                                                                                                                                                                                                 |
| 2   | `uts-prod-client-reporting-daily-snapshot` (asia, `15 0 * * *`) | `uts-prod-client-reporting-daily-snapshot` (same name, but the asia-northeast1 Cloud Run Job doesn't exist) | Cloud Run Job **`client-reporting-daily-snapshot`** exists in **europe-west1** and is already served by an already-`ENABLED` europe-west1 scheduler of the exact same name (`client-reporting-daily-snapshot`) — **identical schedule** `15 0 * * *`. The dead asia scheduler looks like a stale leftover of a cross-region migration; the function is already covered.                                                                                                                                                                             |
| 3   | `catalogue-regen-nightly` (asia, `30 4 * * *`)                  | `catalogue-regen`                                                                                           | Cloud Run Job **`instrument-catalogue-regen`** exists (asia-northeast1) — close-name match, plausible rename target. **Caveat**: its own dedicated scheduler `instrument-catalogue-regen-nightly` (schedule `0 2 * * *`) exists but is itself currently `PAUSED` — so neither path is currently exercising that job on a schedule. Operator should decide: repoint `catalogue-regen-nightly`→`instrument-catalogue-regen` and re-enable, or just re-enable `instrument-catalogue-regen-nightly` and leave `catalogue-regen-nightly` paused/retired. |
| 4   | `uts-prod-features-sports-t1-schedule` (asia, `30 2 * * *`)     | `uts-prod-features-sports-service-t1-recon`                                                                 | Soft note, not a strict rename: sports feature generation already appears to run via a **different mechanism** — the `ENABLED` Cloud Workflow trigger `features-service-sports-daily-trigger` (`0 7 * * *`) → Cloud Run Job `features-service-sports-job`. Not the same schedule/mechanism, so not a confident 1:1 repoint — flagged for awareness only.                                                                                                                                                                                            |

`central-market-data-service-scheduler-trigger` (europe-west1, dead target `central-market-data-service`) was checked
too: zero name-similarity matches (cutoff 0.6) against either region's job list, and zero references to
`central-market-data-service` anywhere in the workspace (`grep -rl` across all ~30 repos, excluding stash-archives) — no
successor identified. Paused only.

## Full list — all 38 paused/confirmed-paused (name, region, schedule, prior state, dead target, last-fired)

| Scheduler                                           | Region          | Schedule     | Was            | Dead target (Cloud Run Job)                              | Last fired (UTC, Cloud Logging, 2d window) |
| --------------------------------------------------- | --------------- | ------------ | -------------- | -------------------------------------------------------- | ------------------------------------------ |
| `catalogue-regen-nightly`                           | asia-northeast1 | `30 4 * * *` | ENABLED→PAUSED | `catalogue-regen`                                        | 2026-08-07T04:31:24Z                       |
| `central-market-data-service-scheduler-trigger`     | europe-west1    | `5 6 * * *`  | ENABLED→PAUSED | `central-market-data-service`                            | 2026-08-07T06:05:09Z                       |
| `uts-dev-batch-live-reconciliation-t1-schedule`     | asia-northeast1 | `0 6 * * *`  | ENABLED→PAUSED | `uts-dev-batch-live-reconciliation-service`              | 2026-08-07T06:00:23Z                       |
| `uts-dev-execution-config-snapshot-t1-schedule`     | asia-northeast1 | `30 0 * * *` | ENABLED→PAUSED | `uts-dev-execution-service-config-snapshot`              | 2026-08-07T00:30:20Z                       |
| `uts-dev-features-calendar-t1-schedule`             | asia-northeast1 | `30 1 * * *` | ENABLED→PAUSED | `uts-dev-features-calendar-service-t1-recon`             | 2026-08-07T01:30:24Z                       |
| `uts-dev-features-commodity-t1-schedule`            | asia-northeast1 | `30 2 * * *` | ENABLED→PAUSED | `uts-dev-features-commodity-service-t1-recon`            | 2026-08-07T02:30:30Z                       |
| `uts-dev-features-cross-instrument-t1-schedule`     | asia-northeast1 | `30 2 * * *` | ENABLED→PAUSED | `uts-dev-features-cross-instrument-service-t1-recon`     | 2026-08-07T02:30:20Z                       |
| `uts-dev-features-delta-one-t1-schedule`            | asia-northeast1 | `0 2 * * *`  | ENABLED→PAUSED | `uts-dev-features-delta-one-service-t1-recon`            | 2026-08-07T02:00:29Z                       |
| `uts-dev-features-multi-timeframe-t1-schedule`      | asia-northeast1 | `30 2 * * *` | ENABLED→PAUSED | `uts-dev-features-multi-timeframe-service-t1-recon`      | 2026-08-07T02:30:22Z                       |
| `uts-dev-features-volatility-t1-schedule`           | asia-northeast1 | `0 2 * * *`  | ENABLED→PAUSED | `uts-dev-features-volatility-service-t1-recon`           | 2026-08-07T02:00:24Z                       |
| `uts-dev-instruments-cefi-t1-schedule`              | asia-northeast1 | `0 6 * * *`  | ENABLED→PAUSED | `uts-dev-instruments-service-cefi-t1-recon`              | 2026-08-07T06:00:24Z                       |
| `uts-dev-market-data-processing-t1-schedule`        | asia-northeast1 | `0 1 * * *`  | ENABLED→PAUSED | `uts-dev-market-data-processing-service-t1-recon`        | 2026-08-07T01:00:31Z                       |
| `uts-dev-market-tick-data-cefi-t1-schedule`         | asia-northeast1 | `0 6 * * *`  | ENABLED→PAUSED | `uts-dev-market-tick-data-service-cefi-t1-recon`         | 2026-08-07T06:00:24Z                       |
| `uts-dev-market-tick-data-fast-t1-schedule`         | asia-northeast1 | `30 0 * * *` | ENABLED→PAUSED | `uts-dev-market-tick-data-service-fast-t1-recon`         | 2026-08-07T00:30:28Z                       |
| `uts-dev-ml-inference-t1-schedule`                  | asia-northeast1 | `0 3 * * *`  | ENABLED→PAUSED | `uts-dev-ml-inference-service-t1-recon`                  | 2026-08-07T03:00:24Z                       |
| `uts-dev-strategy-t1-schedule`                      | asia-northeast1 | `0 4 * * *`  | ENABLED→PAUSED | `uts-dev-strategy-service-t1-recon`                      | 2026-08-07T04:00:21Z                       |
| `uts-prod-client-reporting-daily-snapshot`          | asia-northeast1 | `15 0 * * *` | ENABLED→PAUSED | `uts-prod-client-reporting-daily-snapshot`               | 2026-08-07T00:16:20Z                       |
| `uts-prod-client-reporting-hourly-update`           | asia-northeast1 | `5 * * * *`  | ENABLED→PAUSED | `uts-prod-client-reporting-update`                       | 2026-08-07T17:07:05Z                       |
| `uts-prod-execution-config-snapshot-t1-schedule`    | asia-northeast1 | `30 0 * * *` | ENABLED→PAUSED | `uts-prod-execution-service-config-snapshot`             | 2026-08-07T00:30:20Z                       |
| `uts-prod-features-calendar-t1-schedule`            | asia-northeast1 | `30 1 * * *` | already PAUSED | `uts-prod-features-calendar-service-t1-recon`            | no attempt in 2d (already dormant)         |
| `uts-prod-features-commodity-t1-schedule`           | asia-northeast1 | `30 2 * * *` | already PAUSED | `uts-prod-features-commodity-service-t1-recon`           | no attempt in 2d (already dormant)         |
| `uts-prod-features-cross-instrument-t1-schedule`    | asia-northeast1 | `30 2 * * *` | already PAUSED | `uts-prod-features-cross-instrument-service-t1-recon`    | no attempt in 2d (already dormant)         |
| `uts-prod-features-delta-one-t1-schedule`           | asia-northeast1 | `0 2 * * *`  | already PAUSED | `uts-prod-features-delta-one-service-t1-recon`           | no attempt in 2d (already dormant)         |
| `uts-prod-features-multi-timeframe-t1-schedule`     | asia-northeast1 | `30 2 * * *` | already PAUSED | `uts-prod-features-multi-timeframe-service-t1-recon`     | no attempt in 2d (already dormant)         |
| `uts-prod-features-sports-t1-schedule`              | asia-northeast1 | `30 2 * * *` | ENABLED→PAUSED | `uts-prod-features-sports-service-t1-recon`              | 2026-08-07T02:30:20Z                       |
| `uts-prod-features-volatility-t1-schedule`          | asia-northeast1 | `0 2 * * *`  | already PAUSED | `uts-prod-features-volatility-service-t1-recon`          | no attempt in 2d (already dormant)         |
| `uts-prod-ml-inference-t1-schedule`                 | asia-northeast1 | `0 3 * * *`  | ENABLED→PAUSED | `uts-prod-ml-inference-service-t1-recon`                 | 2026-08-07T03:00:22Z                       |
| `uts-prod-ml-t1-schedule`                           | asia-northeast1 | `0 3 * * *`  | ENABLED→PAUSED | `uts-prod-ml-service-t1-recon`                           | 2026-08-07T03:00:20Z                       |
| `uts-staging-batch-live-reconciliation-t1-schedule` | asia-northeast1 | `0 6 * * *`  | ENABLED→PAUSED | `uts-staging-batch-live-reconciliation-service`          | 2026-08-07T06:00:25Z                       |
| `uts-staging-execution-config-snapshot-t1-schedule` | asia-northeast1 | `30 0 * * *` | ENABLED→PAUSED | `uts-staging-execution-service-config-snapshot`          | 2026-08-07T00:30:30Z                       |
| `uts-staging-features-calendar-t1-schedule`         | asia-northeast1 | `30 1 * * *` | ENABLED→PAUSED | `uts-staging-features-calendar-service-t1-recon`         | 2026-08-07T01:30:29Z                       |
| `uts-staging-features-commodity-t1-schedule`        | asia-northeast1 | `30 2 * * *` | ENABLED→PAUSED | `uts-staging-features-commodity-service-t1-recon`        | 2026-08-07T02:30:22Z                       |
| `uts-staging-features-cross-instrument-t1-schedule` | asia-northeast1 | `30 2 * * *` | ENABLED→PAUSED | `uts-staging-features-cross-instrument-service-t1-recon` | 2026-08-07T02:30:24Z                       |
| `uts-staging-features-delta-one-t1-schedule`        | asia-northeast1 | `0 2 * * *`  | ENABLED→PAUSED | `uts-staging-features-delta-one-service-t1-recon`        | 2026-08-07T02:00:24Z                       |
| `uts-staging-features-multi-timeframe-t1-schedule`  | asia-northeast1 | `30 2 * * *` | ENABLED→PAUSED | `uts-staging-features-multi-timeframe-service-t1-recon`  | 2026-08-07T02:30:24Z                       |
| `uts-staging-features-volatility-t1-schedule`       | asia-northeast1 | `0 2 * * *`  | ENABLED→PAUSED | `uts-staging-features-volatility-service-t1-recon`       | 2026-08-07T02:00:22Z                       |
| `uts-staging-ml-inference-t1-schedule`              | asia-northeast1 | `0 3 * * *`  | ENABLED→PAUSED | `uts-staging-ml-inference-service-t1-recon`              | 2026-08-07T03:00:24Z                       |
| `uts-staging-strategy-t1-schedule`                  | asia-northeast1 | `0 4 * * *`  | ENABLED→PAUSED | `uts-staging-strategy-service-t1-recon`                  | 2026-08-07T04:00:24Z                       |

**Verification**: post-pause `gcloud scheduler jobs list --location={asia-northeast1,europe-west1}` cross-checked
programmatically against this same 38-row list — all 38 show `state: PAUSED`.

## Why pause (not delete) and why this is safe

A scheduler firing into a nonexistent Cloud Run Job does zero useful work today — it just wastes an invocation +
produces a gRPC `NOT_FOUND` log line every fire. Pausing is reversible (unlike delete) and cannot break anything that
currently works, since the target was already gone. Not deleting because 4 of the 38 (see Repoint candidates above) may
want to be repointed rather than retired outright, and the remaining 34's "correct" disposition (retire vs. rebuild the
dev/staging-tier job) is a product decision, not this triage pass's call.

## Todos

- [x] ✅ [DOC] P2. **Repoint candidate (2) corrected + re-verified 2026-08-20**: verified
      `client-reporting-daily-snapshot` exists in europe-west1 while the asia-northeast1 target is nonexistent. The
      previously recorded 2026-08-09 state was inverted/stale (asia ENABLED, europe PAUSED). Paused
      `uts-prod-client-reporting-daily-snapshot` in asia-northeast1 and resumed `client-reporting-daily-snapshot` in
      europe-west1; live verification: asia `PAUSED`, europe `ENABLED`, both schedule `15 0 * * *`. Reversible; no
      job deletion.
- [x] ✅ [INFRA] P2. **STANDING-ACTION — repoint candidate (1) RULED, Terraform retirement EXECUTED 2026-08-15.**
      `uts-prod-client-reporting-hourly-update` (asia-northeast1): RETIRED — `client-reporting-hourly` (via Cloud Run
      Job `client-reporting-batch`, identical `5 * * * *` schedule, confirmed succeeding hourly) already covers the
      function. `google_cloud_scheduler_job.client_reporting_hourly_update` removed from
      `deployment-service/terraform/gcp/client_reporting_scheduler.tf`; `ENV=prod ./tofu.sh apply -target=...` (targeted
      plan showed exactly `0 to add, 0 to change, 4 to destroy` for all 4 candidates together, no unrelated drift
      touched); post-apply `gcloud scheduler jobs describe` confirms `NOT_FOUND`. Shipped
      deployment-service@7b418aabe784234e8a3dfd0e6266aac83c45b5c6 (this same commit fixed a pre-existing registry-guard
      test false-positive the removal exposed — see commit for detail).
- [x] ✅ [INFRA] P2. **STANDING-ACTION — repoint candidate (3) RULED, Terraform retirement EXECUTED 2026-08-15.**
      `catalogue-regen-nightly` vs. `instrument-catalogue-regen-nightly`: RETIRED BOTH — a newer per-asset-group
      `lifecycle-catalogue-regen-{ag}-daily` system (prediction/sports/cefi/defi `ENABLED`, tradfi paused as of
      2026-08-09 — see `plans/active/issues/lifecycle_catalogue_regen_tradfi_daily_unexplained_pause_2026_08_09.md` for
      the tradfi leg's own separate investigation) already replaced them functionally. Confirmed neither
      `catalogue-regen:run` nor `instrument-catalogue-regen:run` job URI is referenced by any other `.tf` trigger before
      removing both `google_cloud_scheduler_job` resources (SA/IAM/job module left in place, out of scope). Post-apply
      `gcloud scheduler jobs describe` confirms both `NOT_FOUND`. Shipped
      deployment-service@7b418aabe784234e8a3dfd0e6266aac83c45b5c6.
- [x] ✅ [DOC] P2. **CONFIRMED 2026-08-09 — repoint candidate (4): superseded, RULED retire.** Read
      `deployment-service/terraform/gcp/t1_batch_scheduler.tf` lines 66-75: the
      `uts-prod-features-sports-service-t1-recon` target (this scheduler's dead target) is explicitly documented as
      never having existed as a real function in ANY tier -- "the sports-features t1-recon target job doesn't exist in
      ANY tier (dev or prod) -- that scheduler entry was already dead," per an explicit operator ruling dated 2026-07-14
      (`bucket_estate_consolidation_to_sub100_2026_07_13.md`). Separately read
      `deployment-service/terraform/services/features-service-sports/gcp/main.tf` lines 1-15, 296-312: the CURRENT live
      sports feature-generation path is a distinct, later-generation stack (`features-service-sports-job` +
      `features-service-sports-daily` Workflow + `features-service-sports-daily-trigger` scheduler, consolidated
      2026-07-15, confirmed healthy via a real scheduled fire that SUCCEEDED, kept ENABLED) that itself superseded an
      intermediate LEGACY `features-sports-service-job` + its own daily-trigger scheduler -- fully retired/deleted via
      `tofu state rm` + `gcloud delete` on 2026-07-15, all 404-confirmed. So there are three generations here
      (dead-from-birth t1-recon -> retired-and-deleted legacy daily -> current live daily), not two coexisting functions
      that both need to exist -- t1-recon and the current `features-service-sports-daily` path are NOT functionally
      distinct; t1-recon was never a real function for sports feature generation at all. Retagged `[OPERATOR]` ->
      `[DOC]` and flipped done; added to the same Terraform-retirement-pending bucket as repoint candidates (1) and (3)
      below (RULED-retire, decommission not yet executed) for consistency.
- [x] ✅ [INFRA] P2. **STANDING-ACTION — repoint candidate (4) RULED, Terraform retirement EXECUTED 2026-08-15.**
      `uts-prod-features-sports-t1-schedule` (asia-northeast1): RETIRED -- its target
      (`uts-prod-features-sports-service-t1-recon`) never existed as a real function (dead-from-birth per the 2026-07-14
      ruling cited above), and the live sports feature-generation path
      (`features-service-sports-daily`/`-daily-trigger`) is a fully separate, later-generation stack that doesn't need
      this scheduler at all. Removed the `"features-sports"` key from `t1_batch_scheduler.tf`'s `t1_batch_services_all`
      map; targeted `tofu apply` confirms destroyed; post-apply
      `gcloud scheduler jobs describe uts-prod-features-sports-t1-schedule` → `NOT_FOUND`. Shipped
      deployment-service@7b418aabe784234e8a3dfd0e6266aac83c45b5c6.
- [x] ✅ [DIAG] P3. **CONFIRMED 2026-08-15 — dev/staging tier is abandoned, not actively maintained; recommend
      RETIRE (delete), not redeploy.** For the 34 non-repoint dead-target schedulers (dev/staging-tier
      `*-t1-schedule`s + `central-market-data-service-scheduler-trigger`): no owning "service team" exists to consult
      (single-operator workspace) — resolved via direct code + live-infra evidence instead. Three independent signals
      all point the same direction:
      1. **Terraform defines the schedulers per-environment but the Cloud Run Job targets were added LATER and never
         backfilled to dev/staging.** `t1_batch_scheduler.tf`'s `google_cloud_scheduler_job.t1_batch_schedule`
         resource is `for_each`'d over `local.t1_batch_services` for EVERY environment (dev/staging/prod alike, minus
         the sports-only dev exclusion) — so a scheduler exists per tier once that tier's state was ever applied. But
         the actual `google_cloud_run_v2_job` resources for most of these targets (strategy, market-data-processing,
         batch-live-reconciliation, instruments-cefi/prediction, mtds-fast/cefi/tradfi) live in
         `audit03_cron_provisioning.tf` and `t1_recon_instruments_jobs.tf` — both added 2026-05-22 through 2026-07-14,
         well after dev/staging's schedulers were first created — and neither file scopes its modules away from
         dev/staging (no `count`/`for_each` on `var.environment`), so a real `ENV=dev ./tofu.sh apply` WOULD create
         them if run.
      2. **That apply has never happened.** `grep -rn "ENV=dev\|ENV=staging" deployment-service/.github/workflows/`
         returns zero hits — the only CI-driven deploy path is the GCP Cloud Build pipeline on `branch=main`, which is
         `ENV=prod` only (confirmed at `deployment-service/.github/workflows/quality-gates-v2.yml:142`). There is no
         scheduled or triggered job anywhere in this repo's CI that runs `ENV=dev`/`ENV=staging` `tofu apply` for this
         directory — dev/staging applies, if they ever happened, were one-off manual actions, not a maintained path.
      3. **Live GCP confirms it**: `gcloud run jobs list --region=asia-northeast1` shows exactly ONE
         `uts-dev-*`/`uts-staging-*` job in the entire fleet (~114 jobs) — `uts-dev-instruments-service-t1-recon`,
         which is itself the OLD all-AG job name t1_batch_scheduler.tf's own header comment says was "RETIRED and
         replaced by per-AG jobs" (i.e., a stray leftover from BEFORE the per-AG split, not evidence of active
         dev-tier maintenance). Zero `uts-dev-`/`uts-staging-` jobs at all in europe-west1 (checked for
         `central-market-data-service` specifically too — none).
      **Conclusion**: dev/staging is not a live, actively-deployed tier for this T1 batch pipeline — it was
      provisioned once (schedulers only) and never kept in sync as the job-provisioning side of the stack grew.
      Redeploying would mean running a one-off manual `ENV=dev/staging ./tofu.sh apply` against a stack with no CI
      path keeping it current, for an environment with no operator-stated need (same shape as the sports dev-tier
      precedent already ruled on 2026-07-14 in this same file: dev held no unique data/value vs. prod). Recommend
      RETIRE, matching the pattern already executed for repoint candidates (1)/(3)/(4) in this doc. Filed the actual
      Terraform decommission as a new STANDING-ACTION todo below rather than executing it in this diagnostic pass
      (34+1 schedulers across the shared `t1_batch_services` map is a bigger, more error-prone change than this DIAG
      todo's scope — needs its own careful `for_each` exclusion work, not folded in here).
- [x] ✅ [INFRA] P3. **STANDING-ACTION — Terraform-retire the dev/staging-tier `*-t1-schedule` schedulers +
      `central-market-data-service-scheduler-trigger` — DONE 2026-08-15 (slot-7).** The doc's own stated "34" count
      didn't reconcile against its own Full-list table above (24 dev/staging rows) — re-derived live instead of
      trusting either number: `gcloud scheduler jobs list --filter="name~'uts-(dev|staging)-.*-t1-schedule'"` →
      **24** (14 dev + 10 staging, matching the table exactly) + 1 (`central-market-data-service-scheduler-trigger`)
      = **25 total**, not 34 (see Progress Log for the discrepancy note; `uts-dev-instruments-t1-schedule`, the one
      OTHER live `uts-dev-*` match, is a different legacy scheduler not in this doc's dead-target list at all —
      excluded, its target is the one stray live job the sibling alert-coverage doc already flagged). Shipped
      `deployment-service@074bae2a` (verified landed, `ahead=0` vs `origin/live-defi-rollout`; see Progress Log for why
      this differs from the pre-ship SHA): `t1_batch_scheduler.tf` adds `t1_batch_services_dev_staging_excluded_keys =
      keys(local.t1_batch_services_all)` (derived from the map's own keys, not hand-listed — can't go stale the way
      the schedulers themselves did) and changes the `t1_batch_services` conditional to
      `contains(["dev","staging"], var.environment)`. **Neither the dev-tier schedulers nor the trigger were ever
      Terraform-tracked** (confirmed via `state list` — dev's state has zero `t1_batch_schedule` instances; the
      trigger doesn't appear anywhere in the repo) — only staging's 10 were real tracked resources, destroyed via
      `tofu apply -target='google_cloud_scheduler_job.t1_batch_schedule'` (`0 to add, 0 to change, 10 destroyed`).
      Dev's 14 + the europe-west1 trigger deleted directly via `gcloud scheduler jobs delete` (mirroring this doc's
      own original pause action, which was also direct-gcloud, never Terraform). **All 25 verified `NOT_FOUND`.**
- [x] ✅ [DIAG] P3. **RESOLVED 2026-08-15 (slot-22)** — Root-caused the 3 PROD dead-target schedulers; two distinct
      root causes, NOT one shared cause.
      1. **`uts-prod-ml-inference-t1-schedule` — pure orphan, RETIRED (deleted).** NOT in the `t1_batch_services_all`
         Terraform map at all (confirmed via grep — no `"ml-inference"` key exists), so it was never Terraform-tracked;
         some manually-created leftover from before `ml-training-service` + `ml-inference-service` were consolidated
         into `ml-service` (2026-05-21, `ml_repo_consolidation_2026_05_19.md` — confirmed via 3 independent code
         comments citing that consolidation in `shared/gcp/main.tf`, `modules/shared-infrastructure/gcp/variables.tf`,
         `cloud-build/gcp/main.tf`). The file header's own schedule-design comment (`t1_batch_scheduler.tf` lines
         36-37) still names a separate "08:00 — ml-inference CEFI" phase, but no live successor exists for it — the
         unified `ml` job (see finding 2) was presumably meant to absorb this CeFi-specific inference pass, but that
         job itself was never deployed either. Deleted directly via
         `gcloud scheduler jobs delete uts-prod-ml-inference-t1-schedule --location=asia-northeast1` (not
         Terraform-tracked, so no `.tf`/state change needed — mirrors this doc's own precedent for the dev-tier
         schedulers, which were also confirmed non-Terraform-tracked before direct deletion). Verified `NOT_FOUND`
         post-delete.
      2. **`uts-prod-execution-config-snapshot-t1-schedule` + `uts-prod-ml-t1-schedule` — NOT dead-from-birth, NOT
         retirement candidates: a genuine half-finished deployment.** Both scheduler resources ARE Terraform-tracked
         (`"execution-config-snapshot"` and `"ml"` keys in `t1_batch_services_all`, `t1_batch_scheduler.tf` lines
         157-161 and 202-206) with `job_name`s `uts-prod-execution-service-config-snapshot` and
         `uts-prod-ml-service-t1-recon` respectively — but **no `google_cloud_run_v2_job` resource with either name
         exists anywhere in the Terraform tree** (grepped every `.tf` file; `ml-service` has no
         `terraform/services/` directory at all, unlike every sibling T1-batch family — features-\*, instruments,
         market-tick-data, market-data-processing, strategy, batch-live-reconciliation all have theirs). Confirmed
         **not** a code gap: `execution-service/execution_service/cli/batch_backtest.py` and
         `ml-service/ml_service/inference/cli/main.py` both already support a `--tag t1-recon` GCS-output-prefix mode
         (line 370 and 135 respectively) — the application-level T1-recon logic was BUILT, but the Cloud Run Job
         deployment (Docker image build, IAM, `google_cloud_run_v2_job` Terraform resource) to actually run it was
         never provisioned. Every sibling family in the same `for_each` map has both halves (scheduler + job); these
         two only ever got the scheduler half — the schedulers have been firing into `NOT_FOUND` since inception,
         never a regression. **Not auto-fixed here**: unlike a pure retire (sports-t1-recon, dev/staging), deciding
         whether to (a) finish the deployment (these ARE load-bearing per the schedule-design comments — execution
         config-snapshot is described as "prerequisite for Stage 3 recon", and strategy-service-t1-recon's own
         description says it "reads t1-recon/ml/" as input, meaning ml-service's T1-recon output has apparently never
         been produced) or (b) retire the schedulers because the function is genuinely obsolete now, is a product
         decision this DIAG-scoped todo can't make alone — filed as a new `[OPERATOR]` todo below. Left both
         schedulers `PAUSED` (as they already were since the 2026-08-07 bulk-pause) — no infra state changed by this
         todo beyond the ml-inference deletion.
      Repos touched: unified-trading-pm (this doc, diag-only); no deployment-service change this pass (see follow-up
      todo below for the judgment call finding 2 needs).
- [ ] [INFRA] P2. Per D39 ruling (2026-08-21, autonomous-dispatch authority): investigate first whether any live
      consumer depends on `strategy-service-t1-recon`'s `t1-recon/ml/` input or Stage-3 recon's
      `execution-config-snapshot` prerequisite (trace real callers in strategy-service / batch-live-reconciliation-service,
      not just the schedule-design comments). If NO real consumer is found, retire both
      `uts-prod-execution-config-snapshot-t1-schedule` and `uts-prod-ml-t1-schedule` via Terraform (mirroring the
      sports-t1-recon precedent already executed in this doc), and re-confirm the already-executed
      `uts-prod-ml-inference-t1-schedule` retirement above is consistent with the finding. If a real consumer IS
      found, finish the deployment instead — add `google_cloud_run_v2_job` Terraform resources for
      `uts-prod-execution-service-config-snapshot` and `uts-prod-ml-service-t1-recon` (mirroring the sibling
      per-family modules in `audit03_cron_provisioning.tf` / `t1_recon_instruments_jobs.tf`). Repo: deployment-service.
      Done when: the investigation's finding (consumer found / not found) is cited here, and the resulting action
      (retire or finish-deploy) is shipped with evidence.
- [ ] [INFRA] P3. **NEW 2026-08-15 (slot-7)** — Clean up 2 orphaned staging Terraform-state entries:
      `google_cloud_scheduler_job.t1_batch_schedule["features-onchain"]` and `["features-sports"]`, tracked in
      staging's state but absent from the current `t1_batch_services_all` map keys entirely. Low-risk/self-resolving
      (any future untargeted `ENV=staging tofu apply` would destroy them anyway) — a small `tofu apply
      -target='google_cloud_scheduler_job.t1_batch_schedule["features-onchain"]'
      -target='google_cloud_scheduler_job.t1_batch_schedule["features-sports"]'` clears them explicitly. Repo:
      deployment-service.
- [x] ✅ [DIAG] P2. **RESOLVED 2026-08-15 (slot-7)** — Investigated + fixed dev Terraform state's
      `google_service_account.t1_batch` entry. **Confirmed the danger the todo flagged was real**: dev's entry was
      byte-identical to prod's real SA (`unique_id=106252291607337267760`, same `email`/`id` — verified via a direct
      `ENV=prod state show` comparison), and that SA is actively referenced by 9+ prod-tier scheduler `.tf` files
      (`t1_batch_scheduler.tf`, `qg_snapshot_scheduler.tf`, `defi_forward_poll_scheduler.tf`, etc.) — the proposed
      REPLACE would have issued a live GCP DELETE against prod's real, in-use SA. **Safe fix applied instead**: (1)
      `ENV=dev tofu state rm 'google_service_account.t1_batch'` — dev-state-only bookkeeping change, zero GCP API
      calls, prod's own state never touched (only 2 read-only `state show` calls made against it, for comparison).
      (2) A subsequent create attempt hit a 409 — `uts-dev-batch-sa` already exists live but was never imported. (3)
      `ENV=dev tofu import 'google_service_account.t1_batch' 'projects/central-element-323112/serviceAccounts/uts-dev-batch-sa@central-element-323112.iam.gserviceaccount.com'`
      — attached the REAL, distinct dev SA (`unique_id=105668859597877647299`, confirmed different from prod's).
      **Verified**: post-import targeted plan = "No changes. Your infrastructure matches the configuration." No code
      change (pure live Terraform state operation — matches this task's own empty `repos: []`). **Adjacent finding**
      (out of this todo's scope, filed separately): a full untargeted `ENV=dev tofu plan` surfaced 2 more
      `_imports_reconcile.tf` defects (a dead import block + a broader prod-only-hardcoding risk affecting ~20 more
      resources) — filed as 2 new todos in
      `/plans/active/issues/deployment_service_t1_recon_duplicate_module_definitions_2026_08_09.md` (same file already
      tracks related `_imports_reconcile.tf` bugs). Repo: deployment-service (no diff — state-only).

## Progress Log

- **2026-08-07**: Filed following `infra_health_audit_findings_fix_2026_08_07.md` todo 1 (Dedicated zombie sweep).
  Re-derived the scheduler↔Cloud-Run-Job cross-reference from scratch (158 asia-northeast1 + 1 in-scope europe-west1
  scheduler vs. 114+7 live Cloud Run Jobs); confirmed 38 dead targets (32 `ENABLED` + 6 already `PAUSED`); bulk-paused
  all 32 via `gcloud scheduler jobs pause`, verified 38/38 now `PAUSED`; flagged 4 repoint candidates (not
  auto-repointed) + 1 informational note; captured last-fired evidence via a single batched Cloud Logging query
  (discovered `gcloud scheduler jobs describe` clears `status`/`lastAttemptTime` once a job is `PAUSED` — noted in
  Method for future reference). No code changes — infra-only (no repo owns these scheduler resources).
- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (2 entries), still accurate.
- **RULED 2026-08-09 (operator)**: "Confirmed — retire it." Per the ruling's own flagged spot-check, read
  `deployment-service/terraform/gcp/t1_batch_scheduler.tf` (lines 66-75) and
  `deployment-service/terraform/services/features-service-sports/gcp/main.tf` (lines 1-15, 296-312) to confirm whether
  t1-recon and the live `features-service-sports-daily` Workflow are the same function or two genuinely distinct ones.
  Confirmed same function across three successive generations: (1) `uts-prod-features-sports-service-t1-recon` --
  dead-from-birth, never materialized in any tier, per an explicit 2026-07-14 operator ruling
  (`bucket_estate_consolidation_to_sub100_2026_07_13.md`); (2) a LEGACY `features-sports-service-job` + daily-trigger --
  fully retired/deleted via `tofu state rm` + `gcloud delete` on 2026-07-15, all 404-confirmed; (3) the CURRENT
  `features-service-sports-job` + `features-service-sports-daily` Workflow + `-daily-trigger` scheduler -- live,
  ENABLED, confirmed via a real scheduled fire that SUCCEEDED. Retagged the todo `[OPERATOR]` -> `[DOC]`, flipped done,
  and filed a new `[OPERATOR]` STANDING-ACTION todo for the actual Terraform decommission (pause is not full
  retirement), matching repoint candidates (1) and (3)'s existing pattern for consistency.
- **2026-08-15 (DIAG P3 todo resolved)**: Confirmed the remaining 34 non-repoint dead-target schedulers via code +
  live-infra evidence (no "owning service team" exists to ask in this single-operator workspace): dev/staging is not
  an actively-deployed tier for this T1 batch pipeline — the Cloud Run Job resources for most targets were added to
  Terraform (`audit03_cron_provisioning.tf`, `t1_recon_instruments_jobs.tf`) well after dev/staging's schedulers were
  first created, no CI path anywhere runs `ENV=dev`/`ENV=staging` `tofu apply` for this directory (Cloud Build is
  `ENV=prod`-only), and live GCP shows exactly one stray `uts-dev-*` job fleet-wide (`uts-dev-instruments-service-t1-recon`,
  itself a pre-per-AG-split leftover, not evidence of maintenance) and zero in europe-west1. Recommend RETIRE, not
  redeploy — same shape as the sports dev-tier precedent above. Filed the actual Terraform decommission as a new
  `[INFRA]` STANDING-ACTION todo rather than executing it in this diagnostic pass (needs its own careful
  `for_each`-exclusion change against the shared `t1_batch_services` map, not folded into a DIAG todo).

- **2026-08-15 (slot-7, infra) — STANDING-ACTION todo executed; 3 adjacent findings flagged, not fixed (all out of
  this todo's dev/staging-only scope).** Full evidence in the flipped todo above. Adjacent findings for whoever picks
  these up next:
  1. **3 unexplained PROD dead-target schedulers**, present in this doc's own original 38-row Full-list table but
     never covered by any of the 4 repoint candidates or the 6 already-paused-prod-features rows:
     `uts-prod-execution-config-snapshot-t1-schedule`, `uts-prod-ml-inference-t1-schedule`,
     `uts-prod-ml-t1-schedule` (all `ENABLED→PAUSED` in the original 2026-08-07 action, root cause never
     investigated — prod SHOULD have real Cloud Run Jobs for these families, unlike dev/staging). This is very
     likely where the doc's "34" count actually came from (34 ≈ 24 dev/staging + these 3 + rounding/miscount, not
     independently confirmed). Not touched here (prod explicitly out of scope for this todo) — worth a fresh
     root-cause pass.
  2. **2 orphaned staging Terraform-state entries**: `google_cloud_scheduler_job.t1_batch_schedule["features-onchain"]`
     and `["features-sports"]` are tracked in staging's state but absent from the CURRENT `t1_batch_services_all` map
     keys entirely (not merely excluded) — a `-target`'d apply doesn't reach genuinely-orphaned instances the way an
     untargeted `tofu plan` would (confirmed: my targeted apply's summary was `10 destroyed`, not 12, even though
     `state list` showed 12 `t1_batch_schedule` entries pre-apply). Low-risk — self-resolving on any future
     untargeted staging apply — not chased further this pass.
  3. **Dev's Terraform state carries `google_service_account.t1_batch` recorded with PROD's real values**
     (`account_id=uts-prod-batch-sa`, matching prod's live SA email/unique_id exactly) instead of a genuine dev SA —
     a targeted plan against it proposes a REPLACE (`uts-prod-batch-sa`→`uts-dev-batch-sa`). NOT touched by this
     todo (unrelated to the scheduler retirement; replacing/deleting a service-account resource that may be
     cross-referenced elsewhere warrants its own careful investigation, not an incidental side-effect here). staging's
     own SA entry was independently confirmed correct (`0 to change` in the same targeted plan) — this drift is
     dev-specific, likely a stray `terraform import` of prod's real SA into dev's state slot at some point.
- **2026-08-15 (slot-7) — post-ship SHA correction**: the STANDING-ACTION todo above originally cited
  `deployment-service@074bae2a` (the Pass-1/pre-ship commit). Quickmerge's Pass-2 reconciliation
  (`git pull --rebase --autostash`) rewrote it to **`074bae2a63ebe00a0a5259b0fa8fe83b2bdcbea3`** because origin had
  advanced with an unrelated promote-pipeline merge (`96917145`/`b330fc4a`) between the Pass-1 commit and the Pass-2
  ship. Corrected the citation above to the verified post-quickmerge SHA (`ahead=0` vs `origin/live-defi-rollout`,
  `git status --porcelain` clean). **Lesson**: a quickmerge-shipped commit's SHA is not stable until AFTER the ship
  completes — always re-derive via `git rev-parse HEAD` post-quickmerge before citing it as evidence; never trust a
  pre-ship commit SHA recorded earlier in the session.
- **2026-08-15 (slot-22) — DIAG todo resolved: 2 distinct root causes for the 3 PROD dead-target schedulers, not
  one.** `uts-prod-ml-inference-t1-schedule` was a pure orphan (not Terraform-tracked at all, a leftover from the
  2026-05-21 ml-inference-service→ml-service consolidation) — deleted directly via `gcloud scheduler jobs delete`,
  verified `NOT_FOUND`. `uts-prod-execution-config-snapshot-t1-schedule` and `uts-prod-ml-t1-schedule` are a
  different, more serious shape: both ARE Terraform-tracked (real `for_each` map keys) and their application-level
  CLI code already supports the T1-recon mode, but the `google_cloud_run_v2_job` resource to actually run them was
  never provisioned in any `.tf` file — the schedulers have fired into `NOT_FOUND` since inception. Whether to finish
  the deployment (closing a possible silent data-pipeline gap — `strategy-service-t1-recon` says it reads
  `t1-recon/ml/`) or retire the function is a product call, not resolvable by this DIAG-scoped todo alone — filed as
  a new `[OPERATOR]` todo. No deployment-service change shipped this pass; the ml-inference deletion is the only
  live-infra change.
- **context-scout 2026-08-17**: populated/refreshed context_scope (2 entries)

- **2026-08-20 (slot 27, dispatch agt-21dce5)**: Corrected the stale candidate-(2) execution record above after
  direct GCP verification. The dead asia target is now `PAUSED`; the real europe-west1 twin is `ENABLED` on the same
  `15 0 * * *` schedule. This was a reversible scheduler-state correction; no Cloud Run Job was deleted.
- **context-scout 2026-08-20**: refreshed context_scope (3 entries).

**2026-08-21 — ruling D39 (t1-recon zombie schedulers)**: ADOPTED-REC 2026-08-21 (autonomous-dispatch authority,
AUTONOMOUS_AGENT_RULES rule 2): Investigate first — if no real consumer depends on t1-recon/ml/, retiring is cheaper
and matches precedent. Source: /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger.
