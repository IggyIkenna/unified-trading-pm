---
title: Monitor-job auto-re-pin gap + alerting-CLI wiring finalization (2026-06-24)
created: 2026-06-24
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

- [x] ✅ [INFRA] P2. Add a `redeploy-monitor-jobs` step to the `deployment-api:latest` build that re-pins the 4 monitor
      jobs to the freshly-pushed digest. **DONE** — `deployment-service/cloudbuild.yaml` carries the `redeploy-monitor-jobs`
      step (guarded `if [ "${_SERVICE_NAME}" != "deployment-api" ]; then exit 0; fi` so it fires ONLY for the deployment-api
      build), confirmed on BOTH `origin/main` and `origin/live-defi-rollout`. So once the auto-kill fix (`cli.py`) lands on
      main, the next main-built `:latest` carries it AND this step auto-re-pins the 4 jobs to it — self-healing, no manual
      tofu. Verified 2026-06-24.
- [ ] [INFRA] P2. **Finalize the alerting-CLI durable command**: the `__main__` guard IS in `alerting-service:latest`
      (verified 2026-06-24) but NOT yet confirmed on alerting-service's *main* — so switching the job to
      `python -m alerting_service.cli.main` (which re-pins `:latest`) risks the same caveat-#2 regression on the next
      main build. HELD until `alerting-service@e111843` is verified on main; the `-c` bridge is live + draining the backlog
      in the meantime (safe, image-agnostic). Then `gcloud run jobs update` / `tofu apply` `alerting_paging_job` + drop the
      bridge.
- [x] ✅ [INFRA] P3. **dp-meta 16Gi + wave-launcher path/memory durable**. Runtime already correct (gcloud). tf made
      durable: `data_pipeline_fleet_monitor_scheduler.tf` carries dp-meta 16Gi/cpu4; `wave_launcher_scheduler.tf` memory
      `4Gi->8Gi` shipped — deployment-service@`fd083ba` (dirty-deps carve-out; UAC had foreign mvp_scope WIP). **No blanket
      tofu apply run** — it would have switched the monitor images digest→`:latest` while main still lacked the auto-kill
      fix (caveat #2), AND the runtime is already correct; the cloudbuild auto-repin (item 1) makes `:latest` durable once
      the fix is on main. Verified 2026-06-24.
