---
doc_type: codex-runbook
title: "CLOUD_AUTH_FAILED Runbook"
summary: >-
  On-call runbook for CLOUD_AUTH_FAILED alerts — cross-cloud IAM/STS authentication failures (AWS
  AssumeRole/AssumeRoleWithWebIdentity denied, GCP service-account impersonation refused). Emitted by
  cost-snapshot-worker; severity HIGH, pages PagerDuty + Telegram.
status: current
nature: process
asset_group: [meta]
stage: [meta]
repos: [deployment-api, unified-api-contracts]
scope: [engineer, admin]
tags: [runbook, alerting, aws, iam, cross-cloud, monitoring]
related:
  [
    /codex/15-runbooks/alerting/operator-playbook.md,
    /codex/05-infrastructure/orchestrator-cloud-identity-self-service.md,
    /plans/archive/issues/infra_health_audit_alert_coverage_gaps_2026_08_07.md,
  ]
created: 2026-08-07
owner: ikenna
cadence: on-demand
verifier: operator
last_executed:
code_refs: []
---

# `CLOUD_AUTH_FAILED` Runbook

> **What this is:** the on-call operator's first stop when a cross-cloud IAM/STS authentication failure is detected. The
> most common case is AWS `AssumeRoleWithWebIdentity` `AccessDenied` from the cost-snapshot worker — the Cloud Run Job
> still exits 0 (per-cloud isolation) so there is no other visible signal. Severity HIGH (PagerDuty P2).

## TL;DR

An IAM/STS authentication error fired from a cross-cloud worker (currently: `cost-snapshot-worker` attempting AWS Athena
via `AssumeRoleWithWebIdentity`). The affected cloud's scheduled work is silently failing every cycle. Fix the IAM
policy gap using the self-service grant procedure in `orchestrator-cloud-identity-self-service.md`; no other automated
recovery exists.

## Trigger condition

- **Code:** `CLOUD_AUTH_FAILED` (UAC closed-set).
- **Pattern (fnmatch):** `CLOUD_AUTH_FAILED` (exact match).
- **Threshold key:** N/A — qualitative condition (permission denied = immediate alert).
- **Emitter(s):** `cost-snapshot-worker` (deployment-api); future cross-cloud callers.
- **Upstream signal:** Per-cloud exception containing known IAM/STS error indicators (`AccessDenied`, `AssumeRole`,
  `PERMISSION_DENIED`, `403 Forbidden`, etc.).
- **De-dup window:** Per `alerting-service` default.

## Severity + paging

- **Severity:** HIGH (PagerDuty P2).
- **Paging channels:** PagerDuty + Telegram.
- **Triggers kill-switch:** false.
- **PagerDuty service:** `uts-prod-live-trading` (1st-tier Ikenna → 2nd-tier Harsh, 30-min auto-escalate).

## Diagnosis (first 5 minutes)

1. **Identify the cloud** from the alert payload field `cloud` (e.g. `aws`, `gcp`, `github`).
2. **Identify the exact error** from payload field `error` — copy the full exception string.
3. **For AWS `AssumeRoleWithWebIdentity`:** confirm the role ARN from `DeploymentApiConfig.aws_athena_reader_role_arn`;
   check the AWS IAM trust policy allows the GCP workload-identity federation audience.
4. **For GCP `PERMISSION_DENIED`:** confirm `unified-trading-sa@<project>.iam.gserviceaccount.com` has the required role
   on the target resource.
5. **Pull recent Cloud Run Job logs** to see the raw exception:
   ```bash
   gcloud logging read \
     'resource.type="cloud_run_job" resource.labels.job_name="cost-snapshot-worker"
      severity>=ERROR' \
     --limit=20 --format='value(textPayload)' --project=<project-id>
   ```

## Resolution paths

### Path 1 — Self-service IAM grant (preferred)

Per `/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md`:

```bash
# AWS: grant AssumeRoleWithWebIdentity on the reader role to the GCP SA's OIDC identity
# (exact command depends on the specific missing grant — see the SSOT above)

# GCP: grant the missing role
gcloud projects add-iam-policy-binding <project-id> \
  --member="serviceAccount:unified-trading-sa@<project-id>.iam.gserviceaccount.com" \
  --role="roles/<missing-role>"
```

Then verify by re-running one cycle:

```bash
gcloud run jobs execute cost-snapshot-worker --region=<region> --project=<project-id>
```

**Success:** Job execution completes for the previously-failing cloud; no `CLOUD_AUTH_FAILED` on the next scheduled
cycle.

### Path 2 — Escalate to operator (if identity doesn't match self-service scope)

If the missing grant is on a role or identity outside the self-service matrix, post in `#agent-orchestrator-alerts` with
the exact error + the required IAM change. Do NOT leave the alert open indefinitely — file an issue doc if resolution is
deferred.

### Path 3 — Kill-switch / halt

N/A — `CLOUD_AUTH_FAILED` does not trigger a kill-switch. The deployment-api still serves other clouds' cached snapshots
during outage.

## Rollback

- **Undoing an IAM grant:** `gcloud projects remove-iam-policy-binding` (reverse of Path 1).
- The underlying data snapshots for the failing cloud will be stale until the next successful run.

## Common false-positives

- **Transient STS endpoint outage:** If the error message includes `ServiceUnavailable` or `RequestExpired` alongside an
  auth indicator, retry once; a persistent `CLOUD_AUTH_FAILED` on consecutive cycles indicates a real IAM gap, not a
  transient error.

## Escalation criteria + targets

Escalate immediately when ANY of:

- `CLOUD_AUTH_FAILED` has fired on 3+ consecutive cycles for the same cloud.
- The IAM gap is on an identity outside the self-service matrix (requires operator).
- The failing cloud is `gcp` (core billing data unavailable to the deployment UI).

Targets:

- **Tier 1 (primary):** Ikenna (Telegram + PagerDuty).
- **Tier 2 (secondary):** Harsh (Telegram + PagerDuty 30-min auto-escalate).
- **Tier 3:** N/A.

## Success criteria

- Trigger condition no longer satisfied (next cost-snapshot-worker cycle emits `SERVICE_PROCESSED` for the
  previously-failing cloud).
- DART Active Alerts shows alert `resolved`.
- No re-fire within 24 h.

## Post-incident

File write-up within 24h for any HIGH true-positive:
`unified-trading-pm/plans/active/issues/incident_<YYYY_MM_DD>_cloud_auth_failed.md`.

## Cross-references

- **AlertCode taxonomy:** [`alert-code-taxonomy.md`](./alert-code-taxonomy.md).
- **Self-service IAM grants:** `/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md`.
- **Operator playbook:** [`operator-playbook.md`](./operator-playbook.md).
- **Implementing plan:** `/plans/archive/issues/infra_health_audit_alert_coverage_gaps_2026_08_07.md`.
- **UAC SSOT:** `unified-api-contracts/unified_api_contracts/canonical/crosscutting/alerting/`.
