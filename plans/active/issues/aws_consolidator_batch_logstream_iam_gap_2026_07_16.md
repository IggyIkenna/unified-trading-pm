---
doc_type: issue
title:
  "BIG FINDING (cross-cutting infra): all 26 AWS Batch manifest-consolidator job definitions fail 100% of the time at
  container-init with a CloudWatch Logs IAM AccessDeniedException — discovered live when the pre-migration-drain RESUME
  runbook re-enabled the 26 EventBridge rules for the first time since 2026-06-08. Re-disabled immediately; NOT
  DeFi-specific, NOT caused by this resume — a pre-existing IAM policy gap that was silently masked for ~38 days by the
  rules being disabled."
summary:
  "While executing tradfi_v9_stage1_finish_2026_07_06.md task -003 (the coordinated 48-GCP-scheduler/26-AWS-rule RESUME
  runbook), re-enabling all 26 `uts-prod-consolidator-*` AWS EventBridge rules (`rate(1 minute)`, AWS Batch targets)
  caused every triggered job across every asset_group/domain (execution, features-*, instruments, market-data,
  ml-training-artifacts, strategy — cefi/defi/tradfi/prediction/sports) to fail within seconds at container
  initialization with an identical `ResourceInitializationError: ... AccessDeniedException: ... is not authorized to
  perform: logs:CreateLogStream ...` — the ECS task execution role `unified-trading-role-prod` lacks
  `logs:CreateLogStream` (and likely `logs:CreateLogGroup`/`logs:PutLogEvents`) on the per-job-definition CloudWatch log
  groups (`/aws/batch/uts-prod-manifest-consolidator-<name>`). Confirmed via live re-enable + `aws batch describe-jobs`
  on 3 independent job names (execution-cefi, features-delta-one-tradfi, features-onchain-cefi) — byte-identical error
  shape each time, before any application code runs. All 26 rules were disabled again within ~2 minutes of enabling (36
  already-queued jobs left to drain to FAILED naturally — bounded, not a repeat-fire risk since the rules are off). This
  is NOT a DeFi-specific issue and NOT introduced by this resume session — it is a genuine, pre-existing IAM policy gap
  on the shared execution role that has been silently invisible for the entire ~38-day drain because nothing was
  triggering these rules to surface it."
status: open
nature: issue
asset_group: [cefi, defi, tradfi, prediction, sports, meta]
stage: [data]
repos: [deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags:
  [
    aws,
    eventbridge,
    batch,
    iam,
    cloudwatch-logs,
    access-denied,
    manifest-consolidator,
    pre-migration-drain,
    resume-runbook,
    infra-drift,
  ]
related:
  [
    ../master_data_canonicalisation_migration_catalogue_2026_06_07.md,
    ../tradfi_v9_stage1_finish_2026_07_06.md,
    ./defi_scheduled_collection_outage_paused_crons_2026_07_16.md,
    ./group_c_cloud_run_job_failures_triage_2026_07_16.md,
  ]
created: 2026-07-16
last_updated: 2026-07-16
parent_epic: infrastructure_master
priority: P1
source:
  "Live evidence surfaced while executing tradfi_v9_stage1_finish_2026_07_06.md task -003 (RESUME runbook), 2026-07-16 —
  operator-authorized 're-stamp then resume' dispatch"
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: local-only
model_tier: opus-required
thinking_tier: max
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
supersedes:
superseded_by:
depends_on: []
assigned_role: infra
drift_direction: advance-code
locked_since:
---

> **NOTIFY-OPERATOR class BIG FINDING (cross-cutting infra, AWS side).** All 26 AWS Batch manifest-consolidator
> EventBridge rules — the AWS half of the pre-migration-drain RESUME runbook, covering execution/features/instruments/
> market-data/ml-training-artifacts/strategy consolidation across every asset_group — fail 100% of the time at container
> startup, before any consolidator code runs, due to a missing IAM permission on the shared task execution role. Found
> live, by actually re-enabling them for the first time since the 2026-06-08 drain; re-disabled within minutes. This is
> a genuine gap independent of the DeFi collector bugs found in the same session (see the related docs) — a THIRD,
> distinct broken-job class discovered by this resume.

## What happened

Executing the RESUME runbook (`master_data_canonicalisation_migration_catalogue_2026_06_07.md:138-146`), all 26
`uts-prod-consolidator-*` AWS EventBridge rules were re-enabled (`aws events enable-rule`), each a `rate(1 minute)`
schedule targeting an AWS Batch job (queue `uts-prod-manifest-consolidator`, one job definition per rule,
`uts-prod-manifest-consolidator-<domain>-<asset_group>`). Verified via `aws batch describe-job-queues` +
`describe-job-definitions` beforehand that the queue (`ENABLED`/`VALID`) and every sampled job definition (`ACTIVE`)
genuinely exist — this is not a missing-target problem like the GCP side hit.

Within ~90 seconds of enabling, jobs began firing on the 1-minute cadence (confirmed via
`aws batch list-jobs --job-status STARTING/RUNNABLE` showing 30+ in-flight jobs across every rule name). Polling for
terminal state: **0 SUCCEEDED, 17 FAILED at the first check, climbing to 36+ in-flight/failed within ~90 more seconds**
— every rule, every domain, immediate and total failure.

## Root cause (confirmed via `aws batch describe-jobs`)

```
ResourceInitializationError: failed to validate logger args: create stream has been retried 1 times: failed to create
Cloudwatch log stream: operation error CloudWatch Logs: CreateLogStream, https response error StatusCode: 400,
api error AccessDeniedException: User: arn:aws:sts::427895769566:assumed-role/unified-trading-role-prod/<session-id>
is not authorized to perform: logs:CreateLogStream on resource:
arn:aws:logs:ap-northeast-1:427895769566:log-group:/aws/batch/uts-prod-manifest-consolidator-<name>:log-stream:...
because no identity-based policy allows the logs:CreateLogStream action : exit status 1
```

Confirmed byte-identical (same error shape, different log-group/role-session per job) on 3 independently sampled job
names spanning different domains: `uts-prod-manifest-consolidator-execution-cefi-scheduled`,
`-features-delta-one-tradfi-scheduled`, `-features-onchain-cefi-scheduled`. The failure happens in the ECS/Fargate
agent's own log-driver setup, **before the container's application code starts** — so this is not a consolidator
code/logic bug at all, it is purely an IAM policy gap on the `unified-trading-role-prod` role: it is missing
`logs:CreateLogStream` (and very likely `logs:CreateLogGroup` / `logs:PutLogEvents`, not yet individually confirmed
since the failure occurs at the first permission check) scoped to the `/aws/batch/uts-prod-manifest-consolidator-*` log
group family.

## Why this was invisible for ~38 days

The 26 rules were DISABLED as part of the 2026-06-08 pre-migration drain (see
`master_data_canonicalisation_migration_catalogue_2026_06_07.md` § "Pre-migration drain"). Nothing has invoked these job
definitions since — so a pre-existing (or since-drifted) IAM gap on the execution role never had a chance to surface.
This is analogous in shape to the DeFi collector findings in
`defi_scheduled_collection_outage_paused_crons_2026_07_16.md` and `group_c_cloud_run_job_failures_triage_2026_07_16.md`
Cluster 5 (a real bug hidden behind a paused scheduler), but a DIFFERENT root cause (IAM, not application code) and a
DIFFERENT blast radius (every AWS-side consolidator, not just DeFi).

## Action taken this session

1. **Confirmed targets exist** before enabling (job queue ENABLED/VALID; 8 sampled job definitions ACTIVE) — ruled out
   the "orphaned target" class that hit 2 of the GCP-side jobs in the same resume.
2. **Enabled all 26 rules**, confirmed jobs fired on cadence (STARTING/RUNNABLE observed).
3. **Polled to terminal state** — 0 succeeded, 17→36 failed within ~2 minutes, all with the identical IAM error.
4. **Disabled all 26 rules again** (`aws events disable-rule`) — confirmed all 26 read back `DISABLED`. This stops NEW
   job submissions; ~36 already-queued jobs (SUBMITTED/RUNNABLE/STARTING at the moment of disable) will drain to FAILED
   on their own over the next few minutes (bounded — not a repeat-fire risk since the triggering rules are off).
5. **Did NOT touch IAM policy** — an IAM change to a shared production execution role is exactly the kind of
   cross-cutting, blast-radius-uncertain change that needs a deliberate, reviewed fix (confirm the MINIMAL missing
   actions, scope the resource ARN correctly, verify no other role/job depends on the current restrictive state for a
   reason) rather than a same-session patch bolted onto an unrelated scheduler-resume task.

## Remediation (recommended — NOT executed; needs an owner)

1. Add `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents` to the `unified-trading-role-prod` IAM policy,
   scoped to `arn:aws:logs:ap-northeast-1:427895769566:log-group:/aws/batch/uts-prod-manifest-consolidator-*` (or
   broader if other AWS Batch job families under the same role need it too — worth checking whether non-consolidator AWS
   Batch jobs on this same role are equally affected, since this role is shared).
2. Once the policy is fixed, re-run the RESUME steps for the 26 EventBridge rules from this doc
   (`aws events enable-rule` for each), and re-verify with the same `aws batch list-jobs --job-status SUCCEEDED/FAILED`
   pattern this doc used before considering it genuinely resumed.
3. Consider whether this same execution role's CloudWatch permissions gap affects any OTHER already-enabled AWS Batch
   workload sharing `unified-trading-role-prod` — not checked this session (scoped strictly to the 26 rules this resume
   touched).

## Status

**OPEN — re-disabled, not fixed.** All 26 AWS consolidator rules are back to `DISABLED` (matching their pre-resume
state, this time due to a confirmed reason rather than the original drain). This blocks the AWS half of
`tradfi_v9_stage1_finish_2026_07_06.md` task -003's literal gate ("all 26 AWS EventBridge rules re-enabled") — see that
plan's Progress Log for the full resume-session accounting. An IAM policy owner needs to make the fix in (1) above
before these rules can be safely re-enabled.
