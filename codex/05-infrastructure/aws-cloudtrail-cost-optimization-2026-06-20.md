---
scope: [admin, engineer]
last_reviewed: 2026-06-20
---

# AWS CloudTrail cost optimization — duplicate-trail removal (2026-06-20)

> Account `427895769566`. Trails home `eu-west-2`, multi-region (the live fleet runs in `ap-northeast-1` / Tokyo, where
> the duplicate cost surfaced as the `APN1-*` usage types).

## Canonical setup (the rule)

There must be **exactly ONE** account-wide CloudTrail trail: the multi-region **organization trail `logs`**. AWS gives
you the **first** copy of management events for free and bills **every additional copy at $2.00 / 100,000 events**. A
second account/region-wide management-events trail just duplicates the (otherwise-free) first copy → pure waste. **Never
create a second account-wide management-events trail** — the org trail already covers every account/region.

Canonical trail `logs`:

- multi-region, **organization trail**, `ReadWriteType=All`, `IncludeManagementEvents=true`, S3 data events on
  `arn:aws:s3` (all buckets).
- delivers to bucket `aws-cloudtrail-logs-427895769566-02e8f7c1` (eu-west-2).

## The incident

A second redundant trail `management-events` ran alongside `logs`:

- multi-region, **not** an org trail, management-events-only (no data events), **same delivery bucket** as `logs`.
- Because `logs` already recorded the first (free) copy of every management event, `management-events` produced the
  billable **second** copy.
- **June 1–20 2026**: usage type `APN1-PaidEventsRecorded` = **16,117,332 events × $2/100k = $322.35** — **96% of the
  entire CloudTrail bill**, tracking ~**$500/mo**. Dead giveaway: `APN1-FreeEventsRecorded` and
  `APN1-PaidEventsRecorded` showed **identical 16.1M counts** (the same events recorded twice).
- Context: ~16M management events / 20 days is normal API churn from the multi-VM agent fleet (EKS/ECS control plane,
  Secrets Manager fetches, autoscaling). The first copy is free; **only the duplication cost money** — so the fix is
  removing the duplicate trail, not reducing API activity.

## Fix (executed 2026-06-20)

```bash
aws cloudtrail stop-logging --name management-events --region eu-west-2   # immediate, reversible cost stop
aws cloudtrail delete-trail --name management-events --region eu-west-2   # clean removal
```

- **Not IaC-managed** — no `aws_cloudtrail` resource anywhere in the workspace IaC (`deployment-service/terraform/aws/`
  has none) and no code/bucket references → the CLI delete sticks; nothing recreates it on the next `terraform apply`.
- **Audit coverage unaffected** — the org trail `logs` still records all management events (incl. KMS/CMK actions, which
  satisfies `custody-onboarding-checklist.md` B.2.4) + all S3 data events. Verified `logs` `IsLogging=true` with a fresh
  delivery immediately after the delete.
- **Saving: ~$322 over the partial month → ~$500/mo of credit burn eliminated, zero coverage loss.**

### Deleted trail config (for recreatability, if ever needed)

`management-events`: `HomeRegion=eu-west-2`, `IsMultiRegionTrail=true`, `IncludeGlobalServiceEvents=true`,
`IsOrganizationTrail=false`, `LogFileValidationEnabled=false`; event selector `ReadWriteType=All`,
`IncludeManagementEvents=true`, no `DataResources`; S3 bucket `aws-cloudtrail-logs-427895769566-02e8f7c1`, no
prefix/SNS/CloudWatch/KMS.

## Watch-item (not actioned)

`logs` logs S3 **data events on `arn:aws:s3` = every object in every bucket** ($0.10/100k). Currently ~$2/mo, but with
millions of parquet objects in the data/mirror buckets this can grow fast. If account-wide S3 object auditing isn't
required, scope the data-event selector to specific buckets.

## Context — credits

AWS spend is ~100% covered by promotional credits (net out-of-pocket ~$0 since May 2026). Credit burn started Feb 2026
and is accelerating (~$2.6k May, ~$2.25k in the first 20 days of June ≈ $3.4k/mo run-rate). This $500/mo CloudTrail
saving directly extends the credit runway. Remaining credit balance is **not** queryable via API — only Billing Console
→ Credits.

## References

- Cost data: AWS Cost Explorer (`aws ce get-cost-and-usage`, grouped by `RECORD_TYPE` / `USAGE_TYPE` / `SERVICE`),
  2026-06-20.
- Custody KMS-audit requirement satisfied by the surviving `logs` trail: `custody-onboarding-checklist.md` B.2.4.
