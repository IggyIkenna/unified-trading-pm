---
doc_type: issue
title:
  cloud_run_service_crash_loop alert-policy creates 404 permanently — metric type
  `run.googleapis.com/container/restart_count` does not exist for Cloud Run
summary: >-
  The 3 crash-loop alert-policy creates retried per infra_satellite_ao_dispatch_batch18 item 2 still 404 with "Cannot
  find metric(s) that match type = run.googleapis.com/container/restart_count" (2026-08-20, slot-12). Root cause:
  that metric type is not a real Cloud Monitoring descriptor — the project's full descriptor list for
  run.googleapis.com/container/* has 26 entries, none named restart_count (verified via the Monitoring REST API). The
  memory-HIGH and instance-zero policies for the same 3 services created fine because their metric types exist. The
  crash-loop filter must be reworked onto a real signal (recommended: a logs-based metric) or removed.
status: open
nature: issue
asset_group:
  [infrastructure]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [terraform, monitoring, alert-policy, cloud-run, crash-loop, root-cause]
related:
  [
    /plans/active/infra_satellite_ao_dispatch_batch18_2026_08_17.md,
    /plans/active/issues/deployment_service_prod_terraform_drift_2026_08_07.md,
  ]
created: 2026-08-20
author: slot-12
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: infra
drift_direction: correct-infra
resolved_by:
locked_by:
source:
  [
    "2026-08-20 (slot-12, dispatched task infra_satellite_ao_dispatch_batch18-bdde083837b7) — retried the 3 crash-loop alert-policy creates per batch18 item 2; still 404; verified root cause via Monitoring REST API (26 run.googleapis.com/container/* descriptors, none restart_count).",
  ]
depends_on: []
context_scope:
  [
    deployment-service/terraform/gcp/cloud_run_service_liveness.tf,
    /plans/active/infra_satellite_ao_dispatch_batch18_2026_08_17.md,
    /plans/active/issues/deployment_service_prod_terraform_drift_2026_08_07.md,
  ]
---

# Cloud Run crash-loop alert-policy creates 404 permanently — metric type does not exist

## What I found

Retried the 3 `google_monitoring_alert_policy.cloud_run_service_crash_loop` creates (`market-data-query-service`,
`central-market-data-tardis-loader`, `uts-prod-data-status-rollup-svc`) declared in
`deployment-service/terraform/gcp/cloud_run_service_liveness.tf:135` with a targeted prod apply
(`ENV=prod ./tofu.sh apply -target='google_monitoring_alert_policy.cloud_run_service_crash_loop'`). **All 3 still
404**, four days after the original 2026-08-16 failure, with the identical error:

```
Error: Error creating AlertPolicy: googleapi: Error 404: Cannot find metric(s) that match type =
"run.googleapis.com/container/restart_count". If a metric was created recently, it could take up to 10 minutes to
become available.
```

**Root cause: `run.googleapis.com/container/restart_count` is not a real Cloud Run / Cloud Monitoring metric type.**
Verified directly against the Monitoring REST API (`projects/central-element-323112/metricDescriptors`, filter
`metric.type = starts_with("run.googleapis.com/container/")`):

- The full descriptor list for `run.googleapis.com/container/*` in this project has **26 metric types** — including
  `instance_count`, `instance_count_with_readiness`, `memory/utilizations`, `cpu/utilizations`,
  `completed_probe_count`, `probe_latencies`, `startup_latencies`, etc. — **none of them named `restart_count`**.
- A `timeSeries` query for `run.googleapis.com/container/restart_count` over the last day returns **0 series**.
- A GET on the exact descriptor `metricDescriptors/run.googleapis.com/container/restart_count` returns
  `Invalid metric name` (descriptor absent).

The memory-HIGH (`run.googleapis.com/container/memory/utilizations`) and instance-zero
(`run.googleapis.com/container/instance_count`) policies for the **same 3 services created successfully** — confirmed
live via `gcloud monitoring policies list`: 3 `memory HIGH (OOM risk)` + 1 `OFFLINE (0 active instances)` policies
present, 0 `crash-looping`. This isolates the failure precisely to the nonexistent metric type in the crash-loop
filter. `restart_count` is a GKE (`k8s_container/restart_count`) concept, not a Cloud Run metric.

**This 404 is permanent** — the filter references a metric the Monitoring API cannot resolve, so no amount of retrying
will create these policies. Prod terraform drift (3 to add on every `ENV=prod tofu plan`) will persist until the
configuration is changed.

## Why it matters

- **Perpetual prod drift**: every `ENV=prod tofu plan` shows `3 to add` for resources that can never be applied,
  polluting every future drift review (incl. the remaining batch18 items and the prod-terraform-drift doc).
- **Crash-loop coverage gap**: these 3 services currently have only memory-high + instance-zero alerting. A container
  that restart-churns *without* OOM or *without* dropping below its min-instance floor would page nobody.
- The `.tf` declares an impossible resource; the config must be corrected, not the apply retried.

## Recommended decision

Rework the crash-loop alert filter onto a **real, resolvable signal**. The preferred shape (matches the file's own
detection-layer intent of "2+ restarts / 15m"):

- **Option A (recommended)** — add a `google_logging_metric` (e.g. `cloud_run_crash_loop`) counting Cloud Run
  instance-restart/ERROR log entries per `resource.labels.service_name`, then point the crash-loop alert policy's
  `condition_threshold.filter` at `metric.type = "logging.googleapis.com/user/cloud_run_crash_loop"` with a
  service_name filter. This keeps the crash-loop layer for all 3 services and is idempotent/re-runnable.
- **Option B (minimal)** — if the logs-based-metric design is declined, remove the crash-loop resource entirely
  (and the `restart_alert = true` entries in `cloud_run_service_liveness_targets`), accepting that these 3 services
  keep memory-high + instance-zero coverage only. Optionally revisit restart detection later.

The metric-selection is a small design call; Option A is the recommendation. Either way the config change must ship
with a verified `ENV=prod tofu plan` showing zero diff for the affected resource(s).

## Addendum 2026-08-21 — 2 of the 3 target services do not exist under these names at all

Independently re-confirmed the invalid-metric root cause this session (same finding, different investigation: real
`metricDescriptors` API query, 25-26 `run.googleapis.com/container/*` types, no `restart_count`) — consolidating here
rather than duplicating. **New finding neither this doc nor the original `prod_terraform_drift_backlog_reconcile_2026_07_24.md`
todo had**: before any metric fix matters, `gcloud run services list --project=central-element-323112` (default
region, no filter) shows **`market-data-query-service` and `central-market-data-tardis-loader` are not currently
deployed Cloud Run services** — only `uts-prod-data-status-rollup-svc` is real. A separate service,
`run-jobs-tardis-data-loader`, IS live and sounds like a plausible successor to the tardis-loader target, but grepping
the entire `deployment-service/terraform/gcp/*.tf` tree for either name (`central-market-data-tardis-loader` or
`run-jobs-tardis-data-loader`) finds it referenced NOWHERE outside `cloud_run_service_liveness.tf` itself — so there is
no in-repo evidence of a rename, and `run-jobs-tardis-data-loader` isn't terraform-managed at all (deployed
out-of-band, same pattern as the DP audit jobs' runtime deploys).

**Why this matters for the recommended fix**: Option A's `google_logging_metric` would filter on
`resource.labels.service_name` — building one for a service name that doesn't exist produces a metric that creates
successfully and simply never has data, which is the EXACT silent-failure mode this doc's own Option A is trying to
avoid for the crash-loop signal itself. The memory-high and instance-zero policies for these same 2 services are
ALREADY live in prod (confirmed via `gcloud monitoring policies list` per this doc's own Progress Log) and have
presumably been silently monitoring nothing since they were created — a materially bigger, already-existing gap than
the crash-loop 404 alone.

**Before implementing Option A, resolve**: (1) was `market-data-query-service` decommissioned/renamed/merged into
another live service (`features-service`/`client-reporting-api` are plausible candidates by function, not confirmed),
and (2) is `run-jobs-tardis-data-loader` genuinely the successor to `central-market-data-tardis-loader`, or an
unrelated service that happens to share "tardis" in its name. This is a real judgment call needing either operator
input or a deeper fleet-deploy-mechanism audit — not resolved here, and NOT mechanically AO-dispatchable as-is until
the target identity question is answered (the existing todo below still stands for `uts-prod-data-status-rollup-svc`,
the one confirmed-real target).

## Todos

- [ ] [OPERATOR] P1. **Resolve target-service identity for 2 of the 3 monitored names before any metric fix ships**:
      confirm whether `market-data-query-service` was decommissioned/renamed/merged (candidates: `features-service`,
      `client-reporting-api` — not verified) and whether `run-jobs-tardis-data-loader` (the one live service with a
      similar name/purpose) is genuinely `central-market-data-tardis-loader`'s successor. The memory-high +
      instance-zero policies for both are ALREADY live in prod monitoring nothing under these names — this is a
      standing, silent gap independent of the crash-loop metric bug below. Source: this doc's 2026-08-21 addendum.
- [ ] [INFRA] P2. Rework `google_monitoring_alert_policy.cloud_run_service_crash_loop`
      (`deployment-service/terraform/gcp/cloud_run_service_liveness.tf:135`) onto a real metric — recommended: add a
      `google_logging_metric` (`logging.googleapis.com/user/cloud_run_crash_loop`) counting Cloud Run
      restart/ERROR log entries per `resource.labels.service_name` and point the crash-loop filter at it; verify with
      `ENV=prod tofu plan` zero-diff + a successful apply of the 3 policies. Repo: deployment-service. Source: this
      doc.
- [ ] [INFRA] P3. If Option A is declined, remove the crash-loop resource + `restart_alert=true` entries from
      `cloud_run_service_liveness.tf` so prod drift clears, and annotate in the file that crash-loop coverage for
      these 3 services is intentionally dropped (memory-high + instance-zero remain). Repo: deployment-service.
      Source: this doc.

## Progress Log

- **2026-08-20 (slot-12, task infra_satellite_ao_dispatch_batch18-bdde083837b7)**: retried the 3 crash-loop
  alert-policy creates (targeted prod apply); all 3 still 404. Verified root cause via Monitoring REST API: 26
  `run.googleapis.com/container/*` metric descriptors, none `restart_count`; 0 time series; exact-descriptor GET
  fails. Memory-HIGH + instance-zero policies for the same services confirmed live. This is a permanent 404, not a
  transient. Filed this doc with the recommended fix (logs-based metric). No code change to deployment-service
  performed (config fix tracked in the todos above).
