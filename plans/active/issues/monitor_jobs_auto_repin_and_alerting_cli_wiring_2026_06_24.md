---
doc_type: issue
title: Monitor-job auto-re-pin gap + alerting-CLI wiring finalization (2026-06-24)
summary:
  Resolving the residual deadman alerts surfaced two infra-hygiene gaps. The CODE/TF durable fixes are **shipped**; this
  doc tracks the remaining finalization + the one real standing gap.
status: open
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [alerting-service, deployment-api, deployment-service]
scope: [engineer, admin]
tags: [monitoring, alerting, infrastructure, self-healing, observability, escalation, runbook]
related: []
created: 2026-06-24
parent_epic: mtds_mdps_master
priority: P2
source:
  - dp_alert_flood_triage_and_monitor_fixes_2026_06_23.md (the two "honest caveats")
  - { live incident: alerting-paging SPOF down (exec-fail) + deadman digest-pin coordination }
assigned_vm: planning
resolved_by:
locked_by: live-defi-rollout
locked_since: 2026-06-24
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-27
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
- **LIVE NOW**: the job runs on a temporary
  `-c "from alerting_service.cli.main import main_service_cli; main_service_cli()"` bridge (works on any image — calls
  the function directly; verified running + draining the backlog).
- **FINALIZE**: once `e111843` promotes to main + the `alerting-service:latest` image rebuilds (carrying the guard), a
  `tofu apply` of `alerting_paging_job` switches it to the durable `python -m alerting_service.cli.main`. Then re-pin /
  re-verify and drop the `-c` bridge.

### 2. dp-* monitor jobs don't auto-re-pin on a deployment-api build (PRE-EXISTING gap)

The `uts-prod-monitoring-deadman` + `uts-prod-dp-{exit-code,heartbeat,meta}-*` jobs run `deployment-api:latest` but
**pin the digest at job-update time** — a new `deployment-api:latest` build does NOT reach them until a manual
`gcloud run jobs update` or `tofu apply`. During this incident that meant fixes on LDR-but-not-main had to be
hand-pinned (digest `34b1bbc0`) to avoid a main-built `:latest` regressing them. **Now that the fixes are on main,
re-pinning to `:latest` is safe** — but the auto-update gap remains.

## Why it matters

A monitor fix (or any deployment-api code fix) silently fails to reach the running dp-* jobs until someone remembers to
re-pin — the exact manual toil that made this incident's coordination fragile. The
`cloud-build/deployment-service-jobs-image.cloudbuild.yaml` ALREADY has the pattern (a `redeploy-jobs` step that re-pins
`uts-prod-tarball-cleanup` + `vm-log-archival-prd` to the freshly-pushed `:latest`) — but it covers the
`deployment-service:latest` maintenance jobs, NOT the `deployment-api:latest` monitor jobs.

## Recommended decision

- [x] ✅ [INFRA] P2. Add a `redeploy-monitor-jobs` step to the `deployment-api:latest` build that re-pins the 4 monitor
      jobs to the freshly-pushed digest. **CONFIG DONE** — `deployment-service/cloudbuild.yaml` carries the
      `redeploy-monitor-jobs` step (guarded `if [ "${_SERVICE_NAME}" != "deployment-api" ]; then exit 0; fi`; loops the
      4 jobs `gcloud run jobs update --image=…:latest` after `push`), confirmed on `origin/main` (line ~217) and LDR.
      **⚠️ EXECUTE-VERIFICATION STILL PENDING (2026-06-24) — see the new todo below.** Two deployment-api builds after
      the auto-kill fix (`566642f1`→`1f66fd70`, `7e1ee9e5`→`db336b9`) did NOT run the step + produced BAD images,
      because both built from the **orphaned pre-force-sync commit `4d054df`** (Cloud Build's repo mirror went stale
      after the deployment-service `main` force-sync and still resolves `main`→`4d054df`, which lacks the step AND has
      inconsistent monitor code). So the step is config-correct but unproven; it will self-verify on the next REAL
      (non-`[skip ci]`) `main` promotion (which refreshes the CB mirror).
- [x] ✅ [INFRA] P1. **Verify the `redeploy-monitor-jobs` auto-repin EXECUTES end-to-end + codify the force-push
      CB-mirror hazard.** VERIFIED BROKEN, then FIXED (2026-07-27): (a) The step shipped by item 1 above was **never
      reachable**. It lived in `deployment-service/cloudbuild.yaml` guarded on `_SERVICE_NAME==deployment-api`, but no
      LIVE Cloud Build trigger ever builds that file with that substitution — `deployment-service-build` (the only
      trigger that builds that file on `main`) never overrides `_SERVICE_NAME`, so it always builds the file's own
      default (`deployment-dashboard`); the trigger that actually builds+deploys deployment-api,
      `deployment-api-main-deploy`, reads a **completely different file** — deployment-api's own root `cloudbuild.yaml`
      — which never contained the step at all. Confirmed two ways: (i)
      `gcloud builds log <deployment-api-main-deploy build d8ac905b, 2026-07-27T06:25:23Z, SUCCESS>` has no
      `redeploy-monitor-jobs` step; (ii) all 4 monitor jobs' `run.googleapis.com/lastUpdatedTime` sat stale (e.g.
      `uts-prod-monitoring-deadman` last touched 2026-07-12 by a human `gcloud run jobs update`, not the Cloud Build SA)
      across dozens of real deployment-api main builds since 2026-06-24. **FIXED**: moved the step into
      `deployment-api/cloudbuild.yaml` (the file the live trigger actually reads), gated on `_DEPLOY=true` like the
      `deploy` step so a feature-branch/build-only `:latest` can never repin production jobs — deployment-api@21d6858
      (amended from b1028e6 by quickmerge). Removed the now-fully-dead step from `deployment-service/cloudbuild.yaml` —
      deployment-service@02d3292 (amended from dd8c6d6). (b) Codified BOTH the force-push CB-mirror hazard AND the
      general "a shared cloudbuild.yaml guard only protects code actually built with the guarded substitution" lesson in
      `/codex/08-workflows/ci-cd-flow.md` (new subsections after "Workflow-template rollout") —
      unified-trading-pm@6ef1b4fb0. **RESIDUAL** (tracked as the new todo below): the fix has not yet been proven
      executing on a REAL `deployment-api-main-deploy` build — that requires the next LDR→main promotion to actually
      reach `main` and fire the deploy trigger, which is beyond this todo's own turn to synchronously wait out.
- [x] ✅ [INFRA] P1. **Confirm the moved `redeploy-monitor-jobs` step (deployment-api@21d6858) actually executes
      end-to-end.** CONFIRMED (2026-07-27), all three acceptance criteria met with real evidence: manually fired the
      LIVE `deployment-api-main-deploy` trigger
      (`gcloud builds triggers run deployment-api-main-deploy     --branch=live-defi-rollout`, same
      trigger/cloudbuild.yaml/substitutions the real `main` push path uses — `_DEPLOY=true`
      `_SERVICE_NAME=deployment-api` — against the LDR tip carrying the fix, rather than waiting out the natural
      LDR→main promotion cadence, which was running ~1.5-2h between cycles) — build `2ea305e9`, SUCCESS, commit
      `21d6858`. (i) The build log shows `Step #12 - "redeploy-monitor-jobs"` running
      `Re-resolving <job> ->     …deployment-api:latest` + `has successfully been updated` for all 4 jobs
      (`uts-prod-monitoring-deadman`, `uts-prod-dp-exit-code-monitor`, `uts-prod-dp-heartbeat-watcher`,
      `uts-prod-dp-meta-watchers`). (ii) `gcloud run jobs describe <job> --format=export` on all 4 confirms
      `run.googleapis.com/lastUpdatedTime` advanced to `2026-07-27T08:50:23Z`-`08:50:37Z` (the build's timestamp) with
      `lastModifier` = `1060025368044@cloudbuild.gserviceaccount.com` (the Cloud Build SA, not a human). (iii)
      `gcloud run jobs execute     uts-prod-monitoring-deadman --wait` on the freshly-repinned image completed cleanly:
      `Execution completed successfully in 44.81s`. The redeploy-monitor-jobs auto-repin is now proven live end-to-end;
      item 1's original "CONFIG DONE" claim is retroactively corrected — it was NOT actually working until this fix.
- [ ] [INFRA] P2. **Finalize the alerting-CLI durable command**: the `__main__` guard IS in `alerting-service:latest`
      (verified 2026-06-24) but NOT yet confirmed on alerting-service's _main_ — so switching the job to
      `python -m alerting_service.cli.main` (which re-pins `:latest`) risks the same caveat-#2 regression on the next
      main build. HELD until `alerting-service@e111843` is verified on main; the `-c` bridge is live + draining the
      backlog in the meantime (safe, image-agnostic). Then `gcloud run jobs update` / `tofu apply`
      `alerting_paging_job` + drop the bridge.
- [x] ✅ [INFRA] P3. **dp-meta 16Gi + wave-launcher path/memory durable**. Runtime already correct (gcloud). tf made
      durable: `data_pipeline_fleet_monitor_scheduler.tf` carries dp-meta 16Gi/cpu4; `wave_launcher_scheduler.tf` memory
      `4Gi->8Gi` shipped — deployment-service@`fd083ba` (dirty-deps carve-out; UAC had foreign mvp_scope WIP). **No
      blanket tofu apply run** — it would have switched the monitor images digest→`:latest` while main still lacked the
      auto-kill fix (caveat #2), AND the runtime is already correct; the cloudbuild auto-repin (item 1) makes `:latest`
      durable once the fix is on main. Verified 2026-06-24.
