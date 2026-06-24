---
title: Monitor-job auto-re-pin gap + alerting-CLI wiring finalization (2026-06-24)
created: 2026-06-24
author: monitor/infra agent
source:
  - dp_alert_flood_triage_and_monitor_fixes_2026_06_23.md (the two "honest caveats")
  - live incident: alerting-paging SPOF down (exec-fail) + deadman digest-pin coordination
parent_epic: mtds_mdps_master
priority: P2
status: active
locked_by: live-defi-rollout
locked_since: 2026-06-24
---

## What I found

Resolving the residual deadman alerts surfaced two infra-hygiene gaps. The CODE/TF durable fixes are **shipped**; this
doc tracks the remaining finalization + the one real standing gap.

### 1. alerting-CLI wiring (DURABLE FIX SHIPPED — finalization pending a tofu apply)

The `alerting-service:latest` image is **dual-use**: its `CMD` is `uvicorn …` (the API SERVICE), but the
`uts-prod-alerting-paging` Cloud Run JOB needs the **CLI subscriber** (`--operation alerts --mode live`). The job
provided `args` but **no `command`** + the image `ENTRYPOINT []`, so it exec'd `--operation` as a binary → "exec failed"
on every run → the alerting SPOF went down → the deadman correctly paged `alerting-subscriber down`.

- **SHIPPED**: `alerting-service@e111843` adds `if __name__ == "__main__": main_service_cli()` to
  `alerting_service/cli/main.py` (the CLI had NO console-script / `__main__` guard). And the deployment-service tf
  (`audit03_cron_provisioning.tf`) now sets `command = ["python", "-m", "alerting_service.cli.main"]`.
- **LIVE NOW**: the job runs on a temporary `-c "from alerting_service.cli.main import main_service_cli; main_service_cli()"`
  bridge (works on any image — calls the function directly; verified running + draining the backlog).
- **FINALIZE**: once `e111843` promotes to main + the `alerting-service:latest` image rebuilds (carrying the guard), a
  `tofu apply` of `alerting_paging_job` switches it to the durable `python -m alerting_service.cli.main`. Then re-pin /
  re-verify and drop the `-c` bridge.

### 2. dp-* monitor jobs don't auto-re-pin on a deployment-api build (PRE-EXISTING gap)

The `uts-prod-monitoring-deadman` + `uts-prod-dp-{exit-code,heartbeat,meta}-*` jobs run `deployment-api:latest` but
**pin the digest at job-update time** — a new `deployment-api:latest` build does NOT reach them until a manual
`gcloud run jobs update` or `tofu apply`. During this incident that meant fixes on LDR-but-not-main had to be hand-pinned
(digest `34b1bbc0`) to avoid a main-built `:latest` regressing them. **Now that the fixes are on main, re-pinning to
`:latest` is safe** — but the auto-update gap remains.

## Why it matters

A monitor fix (or any deployment-api code fix) silently fails to reach the running dp-* jobs until someone remembers to
re-pin — the exact manual toil that made this incident's coordination fragile. The
`cloud-build/deployment-service-jobs-image.cloudbuild.yaml` ALREADY has the pattern (a `redeploy-jobs` step that re-pins
`uts-prod-tarball-cleanup` + `vm-log-archival-prd` to the freshly-pushed `:latest`) — but it covers the
`deployment-service:latest` maintenance jobs, NOT the `deployment-api:latest` monitor jobs.

## Recommended decision

- [ ] [INFRA] P2. Add a `redeploy-jobs` step to whatever builds + pushes `deployment-api:latest` (the
      `deployment-api-main-deploy` / `deployment-api-build` trigger path — confirm the exact config; `cloudbuild.yaml` is
      parameterized per `_SERVICE_NAME`, so the step must fire ONLY for the deployment-api build, not the
      deployment-dashboard build) that re-pins the 4 monitor jobs to the freshly-pushed digest. Mirror the existing
      `deployment-service-jobs-image.cloudbuild.yaml` `redeploy-jobs` step. Failure-tolerant (a job absent in an env
      WARNs, never fails the build).
- [ ] [INFRA] P2. **Finalize the alerting-CLI durable command**: after `alerting-service@e111843` is on main + the image
      rebuilds, `tofu apply` `alerting_paging_job` (or `gcloud run jobs update uts-prod-alerting-paging --command=python
      --args="-m,alerting_service.cli.main,--operation,alerts,--mode,live"`) → verify it starts + drains → drop the `-c`
      bridge.
- [ ] [INFRA] P3. **Finalize the dp-meta 16Gi + wave-launcher path/memory** via a targeted `tofu apply` (the runtime
      already has them via `gcloud run jobs update`; the tf — `data_pipeline_fleet_monitor_scheduler.tf` +
      `wave_launcher_scheduler.tf` — makes them durable so the next blanket apply doesn't revert).
