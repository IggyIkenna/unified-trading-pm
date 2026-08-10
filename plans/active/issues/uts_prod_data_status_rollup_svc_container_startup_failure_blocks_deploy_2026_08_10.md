---
doc_type: issue
title:
  "uts-prod-data-status-rollup-svc fails to start on every image redeploy since ~2026-08-10T14:58Z — total stdout/stderr
  silence, container exits within ~30s, blocking the instruments-service rollup timeout fix from reaching prod"
summary: >-
  While shipping a fix for instruments-service's data-status rollup timing out (sports asset-group grew to 16.4M rows,
  blowing the 420s per-service ceiling — deployment-api@f1b80de071, deployment-service@34d65fad34), found the code fix
  cannot actually reach the LIVE `uts-prod-data-status-rollup-svc` Cloud Run service: every attempted redeploy since at
  least 2026-08-10T14:58:00Z (7 consecutive Cloud Build attempts, spanning multiple UNRELATED commits before mine too)
  fails with `HealthCheckContainerError` — "container failed to start and listen on the port... within the allocated
  timeout" — and ZERO application-level log lines (not even a raw sys.stderr.write() diagnostic bypass) ever appear for
  the failed revision. The SAME image deploys and runs FINE as `uts-shared-deployment-api` in the same build — only this
  specific secondary service, which sets `DEPLOYMENT_API_MINIMAL_STARTUP=true` (a 2026-08-09 addition to lifespan.py),
  fails. Cloud Run correctly refuses to cut traffic to the broken revision, so the service is still SERVING (on an old
  image, imperatively updated with the new --timeout=1700s config but NOT the new code) — not a live outage, but a
  standing deploy blocker.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api]
scope: [engineer, admin]
tags: [deployment, cloud-run, startup, logging, gunicorn, data-status, rollup, ci-cd]
related:
  [
    /plans/archive/issues/deployment_registry_reaper_not_draining_stale_entries_2026_07_24.md,
    /plans/active/issues/data_status_rollup_ml_service_full_blob_missing_2026_07_26.md,
  ]
created: 2026-08-10
author: claude-agent
priority: P1
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by:
source:
  Discovered while re-verifying deployment-api@f1b80de071 (the instruments-service rollup timeout fix) actually reached
  the live uts-prod-data-status-rollup-svc — it hadn't, 3 build attempts in, all with the same
  HealthCheckContainerError.
context_scope:
  [
    deployment-api/deployment_api/lifespan.py,
    deployment-api/deployment_api/settings.py,
    deployment-api/deployment_api/deployment_api_config.py,
    deployment-api/cloudbuild.yaml,
    /plans/archive/issues/deployment_registry_reaper_not_draining_stale_entries_2026_07_24.md,
  ]
---

## What was found

Shipping `deployment-api@f1b80de071` (instruments-service rollup-timeout fix) triggered the standard LDR→main promote →
Cloud Build → `gcloud run services update "${_ROLLUP_SVC}" --image ...` deploy step (`deployment-api/cloudbuild.yaml`).
That step has been failing on **every** attempt since well before this fix existed:

```
$ gcloud builds list --filter="substitutions.REPO_NAME=deployment-api" --limit=10
ab54dfc5  FAILURE  2026-08-10T18:31:44+00:00   <- after my merge
c3350231  FAILURE  2026-08-10T18:05:05+00:00   <- after my merge
6a133745  FAILURE  2026-08-10T17:50:18+00:00   <- my merge, first attempt
f35dc043  FAILURE  2026-08-10T16:33:40+00:00   <- unrelated commit
2be367f4  FAILURE  2026-08-10T15:30:20+00:00   <- unrelated commit
d0399b92  FAILURE  2026-08-10T15:20:28+00:00   <- unrelated commit
400cd03a  FAILURE  2026-08-10T14:58:00+00:00   <- unrelated commit, first observed failure
eb7a47f3  SUCCESS  2026-08-10T13:13:16+00:00   <- last known-good
```

**7 consecutive failures across at least 4 different commits** (mine and at least 3 unrelated ones) — this is a standing
blocker for the WHOLE repo's deploy pipeline for this ONE service, not something my change introduced.

Each failing build's `deploy` step log shows the SAME shape: the FIRST `gcloud run deploy` in the step
(`uts-shared-deployment-api`, the main app) succeeds cleanly and gets a new revision serving 100% traffic. The SECOND
`gcloud run services update "${_ROLLUP_SVC}" --image "$$IMG"` — the exact same image — fails:

```
ERROR: (gcloud.run.services.update) The user-provided container failed to start and listen on the port defined
provided by the PORT=8080 environment variable within the allocated timeout.
```

`gcloud run revisions describe` on the failed revision confirms `reason: HealthCheckContainerError`. Cloud Logging for
that exact revision (`resource.labels.revision_name=...`, no severity filter, 200-entry unfiltered pull) shows **zero**
application-level log lines of any kind — not `logger.info()`, not `print()`, not even the raw
`sys.stderr.write("[STARTUP-DIAGNOSTIC] lifespan entered\n")` bypass diagnostic already present in
`deployment_api/lifespan.py:205-206` (left there specifically for this class of symptom, per the archived
`deployment_registry_reaper_not_draining_stale_entries_2026_07_24.md` investigation below). Only system-level
`run.googleapis.com/varlog/system` lines exist: `Starting new instance` → `Container called exit(1)` →
`STARTUP TCP probe failed` → repeat, roughly every 17s, for the ~4min health-check window before Cloud Run gives up.

**Same image, different outcome, by service.** `uts-shared-deployment-api` and `uts-prod-data-status-rollup-svc` both
deploy from the exact same build's `$$IMG`. Only the rollup service fails. The one confirmed configuration difference
(`gcloud run revisions describe` on the last successfully-imperatively-updated rollup-svc revision):
`DEPLOYMENT_API_MINIMAL_STARTUP=true` is set on the rollup service only — a 2026-08-09 addition to
`deployment_api/lifespan.py` (`MINIMAL_STARTUP` gates skipping 3 background tasks: auto-sync, SSE events drain,
catalogue-lifecycle cache warm). This is the leading, UNCONFIRMED hypothesis — not proven, since local Docker
reproduction (this laptop is arm64, the image is amd64-only, ran under slow QEMU emulation) didn't reliably reproduce
the fast prod crash in the time available for this investigation.

## Why this matters

- **Directly blocks verification of `deployment-api@f1b80de071` + `deployment-service@34d65fad34`** (instruments-
  service rollup timeout fix) — the code is correct (QG green, unit tests added), and BOTH platform-level settings it
  depends on are already live via direct imperative `gcloud` calls (Cloud Run service `--timeout=1700s`, Cloud Scheduler
  `--attempt-deadline=1700s`, both confirmed via `describe`) — but the actual NEW CODE
  (`_CHILD_JOIN_TIMEOUT_OVERRIDES_S`, the per-service override) cannot reach the live service until this deploy blocker
  clears. Re-triggering the rollup right now would still run the OLD worker code.
- **This is the SAME symptom class** (`deployment_registry_reaper_not_draining_stale_entries_2026_07_24.md`, now
  archived) already spent MANY sessions across 2026-07-24→25 chasing for `uts-shared-deployment-api` specifically —
  wrong gunicorn file, `CancelledError` interruption, stale base image digest, and finally "total stdout/stderr silence
  at the raw stream level, for the app AND gunicorn's own access log, cause never confirmed" as that investigation's
  last dead end before being archived (its final entries suggested a container/base-image-layer change as the next
  unexplored angle, and possibly a GCP support ticket). That investigation was for the MAIN service and (per its own
  history) that service DOES currently log fine — this is either a NEW instance of the same underlying platform-level
  cause resurfacing, or a genuinely distinct cause specific to `DEPLOYMENT_API_MINIMAL_STARTUP=true`.
- **Blocks every future deployment-api change from reaching this specific service**, not just mine — a standing, silent,
  cross-cutting regression.

## What's needed

1. Confirm or rule out the `DEPLOYMENT_API_MINIMAL_STARTUP=true` hypothesis directly — e.g. redeploy the rollup-svc with
   that env var temporarily UNSET (matching `uts-shared-deployment-api`'s config) and see if the SAME image then starts
   cleanly. If it does, the bug is somewhere in the `lifespan.py` `MINIMAL_STARTUP` branch itself (added 2026-08-09) —
   read it for a code path that can raise before `yield` (an unhandled exception in the `if MINIMAL_STARTUP:` branches
   would abort the whole lifespan context manager before Uvicorn/gunicorn ever binds the port, and per the archived
   doc's own finding, an exception this early may not reach Cloud Logging at all).
2. If MINIMAL_STARTUP isn't it: this needs the same platform-level investigation the archived doc's last entries
   recommended and never completed — diff the actual image LAYERS (not just Dockerfile source) between a known-working
   revision and the current one, or open a GCP support case given "total silence at the raw stdout/stderr stream level
   for both app code and gunicorn's own access log" was already ruled un-explainable by app-code changes alone in that
   investigation.
3. Once the container starts cleanly: re-verify `deployment-api@f1b80de071`'s actual effect — re-trigger
   `data_status_rollup_worker.py --services instruments-service` and confirm it now succeeds within the raised 1500s
   per-service ceiling (previously failed at 420s on every attempt, 3 consecutive live runs), and that the corrected
   sports coverage (from `unified-api-contracts@5d4a1e6fb` + `instruments-service@9f93da039`) becomes visible via the
   served `/api/data-status/manifest` response.

## Todos

- [ ] [BACKEND] P1. Test the `DEPLOYMENT_API_MINIMAL_STARTUP` hypothesis directly (redeploy rollup-svc with it
      temporarily unset; if the SAME image then starts, read `lifespan.py`'s `MINIMAL_STARTUP` branches for an unhandled
      early exception). Done-when: hypothesis confirmed or ruled out with direct evidence.
- [ ] [BACKEND] P1. If ruled out, escalate to image-layer diffing / GCP support per the archived sibling doc's own final
      recommendation (its last unexplored angle for the same "total silence" symptom class). Done-when: root cause
      identified.
- [ ] [DATA] P2. Once the container starts cleanly, re-trigger the instruments-service rollup and confirm success + the
      corrected sports coverage is visible via `/api/data-status/manifest`. Done-when: a fresh `full.json.gz` post-dates
      this fix and a spot-check of instruments-service's sports coverage no longer counts the deleted out-of-scope rows.

## Progress Log

- **2026-08-10 (interactive session)**: filed while verifying `deployment-api@f1b80de071` reached prod. Confirmed via
  `gcloud builds list`/`describe`/`logging read` that this is a standing, pre-existing (7 consecutive failures across 4+
  commits, starting well before my change), silent deploy blocker specific to `uts-prod-data-status-rollup-svc`. Did not
  root-cause it — out of scope for the rollup-timeout task this session was actually dispatched for; local Docker repro
  was inconclusive (arm64 laptop vs amd64 image, emulation too slow to reliably compare startup timing against prod's
  ~30s crash). Platform-level halves of the rollup-timeout fix (Cloud Run `--timeout=1700s`, Cloud Scheduler
  `--attempt-deadline=1700s`) are live regardless, applied directly via `gcloud` (not gated on this blocker) — only the
  CODE half is stuck behind it.
