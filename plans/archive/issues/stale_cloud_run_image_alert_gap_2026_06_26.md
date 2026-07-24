---
doc_type: issue
title: "STALE-IMAGE / not-latest-code: no alert when Cloud Run jobs run an outdated image"
summary:
  "There is **no alert** when a Cloud Run job (or long-lived service) is running an image that is older than the latest
  build on `live-defi-rollout` / `main`. The failure class is:"
status: resolved
nature: process
asset_group: cross-asset
stage: [meta]
repos: [deployment-service, alerting-service, unified-api-contracts]
scope: [engineer, admin]
tags: []
related: []
created: 2026-06-26
severity: P1
priority: P1
resolved_by:
  {
    utl: unified-trading-library@d9d344a9,
    uac: unified-api-contracts@c6a2fede,
    deployment_service: deployment-service@fc3c4a7,
  }
resolved_date: 2026-06-26
class: STALE-IMAGE
assigned_vm: NA
parent_epic: observability_master
locked_by: live-defi-rollout
locked_since: 2026-05-21
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

> **RESOLVED 2026-06-30 (verified, archived)** — DP_CLOUD_RUN_STALE_IMAGE alert shipped + verified present in UTL
> events/event_types.py, UAC alerting/rules.py, and deployment-service/data_pipeline_monitors/stale_image_watcher.py
> (+cli +unit test). The alert GAP is closed; the operator image-rebuild is a separate follow-up.

> **RESOLVED 2026-06-26** — DP-VM-007 alert implemented and shipped to `live-defi-rollout` across all 3 repos. See
> shipped SHAs in `resolved_by` above. Operator action still required for the image rebuild (IAM-blocked).

# Issue: STALE-IMAGE alert class is unmonitored

## What is missing

There is **no alert** when a Cloud Run job (or long-lived service) is running an image that is older than the latest
build on `live-defi-rollout` / `main`. The failure class is:

> A production Cloud Run job executing the 2026-06-23 image (`a41ad9f7` / `d279615`) while the repository has shipped
> commits `f739a41` and `d279615` — the running image is missing those fixes and the operator has no Slack signal.

This is distinct from the exit-code / heartbeat / deadman coverage (all of which monitor RUNTIME behaviour of a running
image). STALE-IMAGE is a **static-property gap**: a job can heartbeat healthily forever on old code and never fire any
existing alert.

## Why it matters

The data-pipeline alerts codex SSOT (`/codex/05-infrastructure/data-pipeline-alerts.md`) requires:

> "every deployment must be (a) ALERT-FREE and (b) running LATEST CODE to count as done"

And:

> "any failure class that does NOT currently produce a Slack alert must get an alert ADDED"

The Cloud Run jobs are currently confirmed stale (2026-06-23 image, missing f739a41/d279615). The rebuild is IAM-blocked
for agent identities — operator must trigger Cloud Build manually. But the **absence of an alert** is the architectural
gap to close.

## Scope of the gap

Affects ALL 61 classified Cloud Run jobs in `deployment-service/deployment_service/cloud_run_job_registry.py`
(`CLOUD_RUN_JOBS`). The deployment-api already surfaces per-job execution status at `GET /api/deployments/inventory`
(including the image digest via the GCP `run_v2` client in `routes/_cloud_run_executions.py`) — the raw material for a
staleness check exists. What is missing is:

1. A **comparison step**: resolve the latest image digest built from the current HEAD (the Cloud Build trigger writes
   this to Artifact Registry) and compare it to each job's running image digest.
2. An **alert rule**: a new `DP_CLOUD_RUN_STALE_IMAGE` event (UTL + UAC DataPipelineAlertRule) emitted by the meta sweep
   (`dp-meta-watchers`) when the running digest != latest.
3. Routing: WARN to `#data-pipeline-alerts` (or CRITICAL for jobs in a LIVE umbrella).

## Why the fix is deferred to a plan (not done inline)

The stale-image check requires cross-service coordination:

- The latest-image digest must be resolved from **Artifact Registry** (a new GCP API seam in
  `deployment_service/backends/_gcp_sdk.py` — the approved SDK boundary).
- The Cloud Run job's running image digest is surfaced via `run_v2` (already available) — but comparing two digests from
  two APIs is a new codepath needing its own guard test.
- A new UTL event constant + UAC `DataPipelineAlertRule` entry is a cross-repo change (unified-trading-library +
  unified-api-contracts) which triggers full-QG on both repos.
- The "latest build" concept for `deployment-api:latest` needs a clear definition: is it the most recent Cloud Build
  SUCCESS on `main`? On `live-defi-rollout`? This is a design decision.

This is a real P1 gap (silent stale code in prod), not a cosmetic one. The operator note about the 2026-06-23 image is
the concrete instance.

## Immediate operator action required

The Cloud Run jobs are confirmed running the 2026-06-23 image (missing f739a41/d279615). Image rebuild requires Cloud
Build trigger with operator credentials (IAM-blocked for agent identity):

```
gcloud builds submit --config=cloudbuild.yaml --project=central-element-323112
```

Run for: `deployment-service` and any other repos whose Cloud Run jobs are stale.

## Implementation sketch (for the fix agent)

1. **UTL** (`unified_trading_library/events/event_types.py`): add `DP_CLOUD_RUN_STALE_IMAGE`.
2. **UAC** (`unified_api_contracts/canonical/crosscutting/alerting/rules.py`): add to `DATA_PIPELINE_ALERT_RULES` as
   WARN/SLACK-only (one rule per-job or one aggregated alert).
3. **deployment-service** (`deployment_service/backends/_gcp_sdk.py`): add
   `latest_image_digest_for_service(service_name)` that queries Artifact Registry `artifactregistry.v1` for the
   `:latest` tag's digest.
4. **deployment-service meta sweep** (`deployment_service/data_pipeline_monitors/meta_watchers.py`): add
   `check_cloud_run_image_freshness(...)` that for each Cloud Run job reads its running image digest (via `run_v2` —
   already used in `routes/_cloud_run_executions.py`) and compares to the latest Artifact Registry digest; emits
   `DP_CLOUD_RUN_STALE_IMAGE` WARN when stale.
5. **Unit tests**: synthetic digest mismatch → WARN emitted; matching digest → no emit.
6. **QG-green on all 3 repos** before quickmerge.

## References

- `/codex/05-infrastructure/data-pipeline-alerts.md` § DP-VM class (the stale-image class is a gap)
- `/codex/05-infrastructure/deployment-observability.md` § Cloud Run jobs registry
- `deployment-service/deployment_service/cloud_run_job_registry.py` — 61 classified jobs
- `deployment-service/deployment_service/backends/_gcp_sdk.py` — the approved GCP SDK seam
- `deployment-service/deployment_service/data_pipeline_monitors/meta_watchers.py` — extension point
- Operator note 2026-06-26: jobs confirmed on 2026-06-23 image, missing f739a41/d279615
