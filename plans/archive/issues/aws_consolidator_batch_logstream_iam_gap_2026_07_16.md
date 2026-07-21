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
status: resolved
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
last_updated:
  2026-07-16 (FIXED — added uts-manifest-consolidator-logs-prod IAM policy via terraform, applied live, all 26
  EventBridge rules re-enabled and verified past the container-init IAM gate; status -> resolved)
parent_epic: infrastructure_master
priority: P1
source:
  "Live evidence surfaced while executing tradfi_v9_stage1_finish_2026_07_06.md task -003 (RESUME runbook), 2026-07-16 —
  operator-authorized 're-stamp then resume' dispatch"
assigned_vm: NA
resolved_by: |
  deployment-service@55b4c00 (terraform/aws/manifest_consolidator_scheduler.tf — new
  uts-manifest-consolidator-logs-prod IAM policy: logs:CreateLogStream + logs:PutLogEvents scoped to
  arn:aws:logs:ap-northeast-1:427895769566:log-group:/aws/batch/uts-prod-manifest-consolidator-*:*, attached to
  unified-trading-role-prod). Applied live via `terraform apply` (targeted plan: 2 to add, 0 to change, 0 to destroy —
  no drift). All 26 uts-prod-consolidator-* EventBridge rules re-enabled and confirmed ENABLED. Verified: across 192
  FAILED jobs sampled post-fix (85 created after the fix), ZERO carry AccessDeniedException/logs:CreateLogStream —
  every one of the old AccessDenied failures predates the 08:58:31 UTC policy attach. 77+ jobs reached SUCCEEDED
  (instruments-*/market-data-* core group) with real CloudWatch log content confirming genuine consolidator/service
  code execution (not just past container-init). See "Resolution (2026-07-16)" section for full evidence + residual
  observations.
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

**RESOLVED (2026-07-16, later same-day session) — IAM gap fixed, all 26 rules re-enabled, verified past the
container-init gate.** See "Resolution (2026-07-16)" below for the exact policy change, verification evidence, and
residual (non-blocking) observations.

<details>
<summary>Original status at filing time (superseded)</summary>

**OPEN — re-disabled, not fixed.** All 26 AWS consolidator rules are back to `DISABLED` (matching their pre-resume
state, this time due to a confirmed reason rather than the original drain). This blocks the AWS half of
`tradfi_v9_stage1_finish_2026_07_06.md` task -003's literal gate ("all 26 AWS EventBridge rules re-enabled") — see that
plan's Progress Log for the full resume-session accounting. An IAM policy owner needs to make the fix in (1) above
before these rules can be safely re-enabled.

</details>

## Resolution (2026-07-16)

### 1. Role confirmed terraform-managed — fix made in IaC, not CLI

`unified-trading-role-prod` is tagged `ManagedBy=terraform`, defined at `deployment-service/terraform/aws/main.tf:419`
(`aws_iam_role.unified_trading`). Its attached managed policies before the fix: `AmazonEC2ContainerRegistryReadOnly`
(AWS-managed, ECR pull only), `unified-trading-policy-prod` (S3 / Athena / Glue / SQS / Secrets Manager — no `logs:*`),
`uts-manifest-consolidator-s3-prod` (S3 only, added for the consolidator buckets). **No CloudWatch Logs permission
existed anywhere on this role** — confirmed by reading every attached policy's default version via
`aws iam get-policy-version`.

The consolidator's Batch job definitions (`deployment-service/terraform/modules/container-job/aws/main.tf`) already
provision the log group per job via `aws_cloudwatch_log_group.job_logs` (`create_log_group = true` default, name =
`/aws/batch/${var.name}` = `/aws/batch/uts-prod-manifest-consolidator-<name>`) — confirmed all 26 log groups already
exist in AWS. The `logConfiguration` block does not set `awslogs-create-group`, so the running container only ever calls
`logs:CreateLogStream` + `logs:PutLogEvents`, never `logs:CreateLogGroup` — hence the fix is scoped to exactly those two
actions (least-privilege; no over-grant).

### 2. Exact IAM change (terraform)

Added to `deployment-service/terraform/aws/manifest_consolidator_scheduler.tf` (same pattern as the existing
`uts-manifest-consolidator-s3-prod` policy — a dedicated, narrowly-scoped managed policy attached to the shared
`unified_trading` role, not a broadened blanket grant):

```hcl
data "aws_iam_policy_document" "manifest_consolidator_logs" {
  statement {
    sid    = "ManifestConsolidatorCloudWatchLogs"
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = [
      "arn:aws:logs:${var.aws_region}:${var.aws_account_id}:log-group:/aws/batch/uts-prod-manifest-consolidator-*:*",
    ]
  }
}

resource "aws_iam_policy" "manifest_consolidator_logs" {
  name   = "uts-manifest-consolidator-logs-${var.environment}"
  policy = data.aws_iam_policy_document.manifest_consolidator_logs.json
}

resource "aws_iam_role_policy_attachment" "manifest_consolidator_logs" {
  role       = aws_iam_role.unified_trading.name
  policy_arn = aws_iam_policy.manifest_consolidator_logs.arn
}
```

Applied via `terraform init` (real S3 backend:
`bucket=uts-terraform-state-427895769566 key=terraform/state/prod region=ap-northeast-1`) + a **targeted**
`terraform plan`/`apply` (`-target` on the 3 new resources only) — plan showed exactly
`2 to add, 0 to change, 0 to destroy` (the data source doesn't count as a resource action), so no drift from other
in-flight terraform work was touched or applied. Verified live:
`aws iam list-attached-role-policies --role-name unified-trading-role-prod` shows `uts-manifest-consolidator-logs-prod`
attached; `aws iam get-policy-version` shows the exact statement above (`CreateDate: 2026-07-16T08:58:31Z`). Shipped to
git via `deployment-service@55b4c00` (quickmerge, `--files` scoped to the 2 touched files only; `deployment-service`
quality-gates.sh green, 61s).

### 3. Re-enabled all 26 rules + verification

`aws events enable-rule` on all 26 `uts-prod-consolidator-*` rules at `2026-07-16T08:59:41Z`; read-back confirmed all 26
`ENABLED`. Polled `aws batch list-jobs --job-queue uts-prod-manifest-consolidator` across every status for ~15 minutes
post-enable:

- **Zero new `AccessDeniedException`/`logs:CreateLogStream` failures.** Of 192 total FAILED jobs visible at the final
  check, 85 were created after the 08:58:31Z policy attach — **all 85 have a different `statusReason`**
  (`Job attempt duration exceeded timeout` or `Essential container in task exited`, see § 4); **none** carry the old
  `AccessDeniedException`/`logs:CreateLogStream` signature. The remaining ~107 FAILED entries all pre-date the fix
  (07:53–07:58Z, from the original resume-session test documented above).
- **SUCCEEDED jobs climbing continuously** (0 → 9 → 41 → 59 → 77+ over the poll window), all in the
  `instruments-*`/`market-data-*` (Phase-A "core") bucket group.
- **Directly verified 3 sampled job IDs** (`execution-cefi`, `features-delta-one-defi`, `features-onchain-cefi` — the
  same 3 names the original AccessDenied confirmation used) via `aws batch describe-jobs`: each has a real
  `container.logStreamName` assigned, and `aws logs get-log-events` on that stream shows **actual application log
  content** (`ServiceRuntime: op=__bootstrap__ mode=batch provider=aws ...`, `Event logging initialized`,
  `DomainValidationService initialized`, etc.) — i.e. `logs:CreateLogStream` + `logs:PutLogEvents` are genuinely
  working, and the container runs its real consolidator/service code well past container-init.

### 4. Residual (non-blocking) observation — NOT the IAM issue, left rules ENABLED

Past the IAM gate, two distinct failure reasons appear in the post-fix window, spread across both core and Phase-D
"extended" (derived-data) buckets roughly proportionally (not isolated to one group):

- `Job attempt duration exceeded timeout` (27+ instances) — consolidator runs taking longer than the job's configured
  1800s attempt timeout.
- `Essential container in task exited` (21+ instances, non-zero exit) — one directly-inspected case (`execution-cefi`)
  showed a transient argparse error on attempt 1
  (`market-tick-data-service: error: the following arguments are required: --operation, --mode`) that **self-healed on
  the job's automatic retry** (attempt 2 ran the normal consolidator bootstrap cleanly, confirmed via live logs) —
  consistent with a first-invocation-after-38-days cold-start race, not a permanent per-bucket code bug.

Both patterns are consistent with a **38-day-idle backlog catch-up** (first real runs since the 2026-06-08 drain have
much more to consolidate than steady-state incremental runs) and are **already a known, separately-tracked class** of
consolidator behavior (see `market-tick-data-service/Dockerfile` rebuild-trigger history —
`manifest_consolidator_instruments_sports_intermittent_slow_run_2026_07_14.md`,
`instruments_sports_manifest_consolidator_lock_livelock_2026_07_15.md` — plus existing lock-aware liveness alerting).
Per this doc's own remediation criterion ("leave enabled if they now run"): jobs **are** running, real work is
happening, and the retry/next-minute-cycle mechanism is self-healing observed failures — so **all 26 rules were left
ENABLED**, not re-disabled. If this residual pattern does not taper off as backlogs clear, it is a separate,
already-tracked consolidator-performance concern (not an IAM/access issue) for the existing liveness-watchdog owner to
pick up — out of scope for this IAM-gap fix.

## Progress Log

- 2026-07-16 (this session): Read the role (`aws iam get-role`/`list-attached-role-policies`/`get-policy-version`),
  confirmed terraform-managed, confirmed the 26 log groups already exist (created by the container-job module), added
  the least-privilege `uts-manifest-consolidator-logs-prod` policy in
  `deployment-service/terraform/aws/manifest_consolidator_scheduler.tf`, applied live via targeted `terraform apply` (2
  add / 0 change / 0 destroy), shipped via quickmerge (`deployment-service@55b4c00`, QG green 61s), re-enabled all 26
  EventBridge rules, and verified via `aws batch describe-jobs` + `aws logs get-log-events` that the IAM gap is fully
  closed (zero new AccessDenied among 85 post-fix failures; 77+ genuine SUCCEEDED runs with real log content). Status →
  resolved.

## Correction 2026-07-16 — rules RE-DISABLED (AWS is not a live target)

Operator challenge ("what are the AWS consolidators doing — we don't even have AWS bucket data yet") prompted a
data-presence check that reversed the re-enable decision:

- **AWS is not a live write target.** Live collection (incl. the DeFi collectors restored this session) writes ONLY to
  GCS — collector logs show `gs://…` sinks, no `s3://`. On AWS S3 (account 427895769566): most asset groups' buckets are
  EMPTY (instruments-store-{cefi,tradfi,sports,pred}, features-*); the DeFi buckets that DO hold data (`dex-pools-prd`
  ~39k, `evm-defi-prd` ~30k, `instruments-store-defi-prd` ~54k, `market-data-tick-defi-prd`) are **frozen at ~2024-08**
  (`by_date/day=` partitions stop there) — a stale historical mirror, not live dual-write.
- **Therefore the 26 `uts-prod-consolidator-*` EventBridge rules consolidate stale-or-empty buckets** — running 26 AWS
  Batch jobs per cron cycle for zero live value. Re-enabling them (as part of the blanket 48-GCP/26-AWS drain-resume
  runbook) was over-eager: the runbook assumed the resumed fleet had live data to process, which is true for GCP but not
  AWS.
- **Action:** re-DISABLED all 26 rules (verified 0 ENABLED). **The IAM fix is KEPT** (the role genuinely lacked
  `logs:CreateLogStream`/`PutLogEvents`; it's correct and needed if/when AWS ever becomes a live target). Re-enabling is
  one command (`aws events enable-rule`) whenever a real dual-cloud AWS write path is stood up.
- `status` reverts to a documented DEFERRED-until-AWS-is-live posture (IAM gap closed; scheduling intentionally off).
