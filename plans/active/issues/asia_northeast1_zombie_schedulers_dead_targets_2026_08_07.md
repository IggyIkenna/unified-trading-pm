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
related:
  [
    /plans/archive/2026_08/infra_health_audit_findings_fix_2026_08_07.md,
    /plans/archive/issues/infra_health_audit_alert_coverage_gaps_2026_08_07.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-07
last_updated: 2026-08-09
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
    /plans/archive/issues/infra_health_audit_alert_coverage_gaps_2026_08_07.md,
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

- [x] ✅ [DOC] P2. **Repoint candidate (2) RULED + EXECUTED 2026-08-09**: `uts-prod-client-reporting-daily-snapshot`
      (asia-northeast1) vs. the europe-west1 `client-reporting-daily-snapshot` twin — RE-ENABLE asia-northeast1, PAUSE
      europe-west1. **Already executed live this session** via `gcloud scheduler jobs resume/pause`; re-verified fresh
      just now:
      `gcloud scheduler jobs describe uts-prod-client-reporting-daily-snapshot --location=asia-northeast1     --project=central-element-323112 --format='value(state)'`
      → `ENABLED`;
      `gcloud scheduler jobs describe client-reporting-daily-snapshot --location=europe-west1     --project=central-element-323112 --format='value(state)'`
      → `PAUSED`. Both confirmed live-verified, DONE.
- [ ] [OPERATOR] P2. **STANDING-ACTION — repoint candidate (1) RULED, Terraform retirement not yet executed.**
      `uts-prod-client-reporting-hourly-update` (asia-northeast1): RETIRE it — `client-reporting-hourly` (via Cloud Run
      Job `client-reporting-batch`, identical `5 * * * *` schedule, confirmed succeeding hourly) already covers the
      function. This scheduler is currently `PAUSED` (from the bulk-pause below) but pausing alone is NOT full
      retirement — the actual Terraform/infra resource still needs to be decommissioned. Track and execute that
      decommission as its own step.
- [ ] [OPERATOR] P2. **STANDING-ACTION — repoint candidate (3) RULED, Terraform retirement not yet executed.**
      `catalogue-regen-nightly` vs. `instrument-catalogue-regen-nightly`: RETIRE BOTH — a newer per-asset-group
      `lifecycle-catalogue-regen-{ag}-daily` system (prediction/sports/cefi/defi `ENABLED`, tradfi paused as of
      2026-08-09 — see `plans/active/issues/lifecycle_catalogue_regen_tradfi_daily_unexplained_pause_2026_08_09.md` for
      the tradfi leg's own separate investigation) already replaced them functionally. Both are already `PAUSED` live
      (re-verified fresh this session: both `gcloud scheduler jobs describe ... --location=asia-northeast1` calls return
      `PAUSED`). Pausing is not full retirement — decommission both scheduler resources (and confirm neither Cloud Run
      Job `catalogue-regen`/`instrument-catalogue-regen` is still referenced elsewhere) as their own step.
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
- [ ] [OPERATOR] P2. **STANDING-ACTION — repoint candidate (4) RULED, Terraform retirement not yet executed.**
      `uts-prod-features-sports-t1-schedule` (asia-northeast1): RETIRE it -- its target
      (`uts-prod-features-sports-service-t1-recon`) never existed as a real function (dead-from-birth per the 2026-07-14
      ruling cited above), and the live sports feature-generation path
      (`features-service-sports-daily`/`-daily-trigger`) is a fully separate, later-generation stack that doesn't need
      this scheduler at all. This scheduler is currently `PAUSED` (from the bulk-pause below) but pausing alone is NOT
      full retirement -- the actual Terraform/infra resource still needs to be decommissioned. Track and execute that
      decommission as its own step.
- [ ] [DIAG] P3. For the 34 non-repoint dead-target schedulers (dev/staging-tier `*-t1-schedule`s +
      `central-market-data-service-scheduler-trigger`): confirm with each owning service team/repo whether the
      dev/staging-tier T1-recon Cloud Run Job was deliberately decommissioned (in which case these schedulers should
      eventually be DELETED, not just left paused forever) or should be redeployed. Not resolved here — this pass's
      scope was pause + triage only.

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
