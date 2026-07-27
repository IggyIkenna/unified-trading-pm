---
doc_type: issue
title: >-
  heartbeat_stall_watcher's auto-kill has NEVER worked in production — vm_zombie_watchdog is structurally absent from
  the deployment-api production image, not just stale; the fast-spawn dispatch fallback is ALSO broken (HTTP 422)
summary: >-
  Discovered while investigating why a 6h-frozen migration VM (cs9-1d) wasn't auto-recovered. The DETECTION half of
  heartbeat_stall_watcher works correctly and IS scheduled (Cloud Scheduler `uts-prod-dp-heartbeat-watcher-cron`, */5 *
  * * *, Cloud Run Job `uts-prod-dp-heartbeat-watcher` on `deployment-api:latest`) — its logs show it correctly
  classified cs9-1d as `verdict=stall hb_age=361.8` (~6h), matching the independently-confirmed freeze. But the
  auto-kill ACTION fails every single time: `auto-kill: vm_zombie_watchdog unavailable in runtime — cannot kill`.
  Root-caused to `deployment-api/Dockerfile`: `COPY scripts/ ./scripts/` (the only line that would put
  `scripts/vm/vm_zombie_watchdog.py` into the image) is under the `api-dev` (test-only) build stage, NOT the production
  `api` stage that `deployment-api:latest` actually is. Production installs `deployment-service` via `uv pip install
  --no-deps /tmp/deployment-service` then `rm -rf`s the source — a wheel install never carries the top-level `scripts/`
  directory. This is a STRUCTURAL packaging gap, not staleness — no image rebuild would fix it without a Dockerfile
  change. Found this is NOT limited to the migration campaign: a completely unrelated
  `mdps-backfill-cefi-20260726-165959` VM had been frozen for 17+ hours (1033 min) with the identical failure on every
  5-min check the whole time. The fast-spawn dispatch fallback (`repository_dispatch` → AutoSpawn a worker when
  auto-kill can't run) is ALSO failing independently every time: `HTTP 422 Unprocessable Entity`. Both frozen VMs were
  manually killed this session (cs9-1d relaunched as cs9-1d-r2; mdps-backfill-cefi-20260726-165959 killed, not yet
  relaunched — outside this session's scope, needs a human/different agent to pick up that shard).
status: open
nature: issue
asset_group: [infrastructure, cefi]
stage: [meta]
repos: [deployment-api, deployment-service]
scope: [engineer, admin]
tags:
  [
    vm-monitoring,
    hung-vm,
    stall-detection,
    zombie-watchdog,
    docker-packaging,
    deployment-observability,
    production-incident,
  ]
related:
  [
    /plans/active/issues/migration_vm_hung_detection_monitoring_gap_2026_07_27.md,
    /plans/active/issues/relaunch_stalled_vm_no_checkpoint_resume_gap_2026_07_27.md,
    /plans/active/cefi_migration_cutover_and_track8_completion_2026_07_25.md,
  ]
created: 2026-07-27
parent_epic: infrastructure_master
priority: P0
estimate_class: infra
assigned_role: infrastructure
source: >-
  Surfaced while answering the operator's direct question "why didn't this come into deployment ui monitor and data
  pipeline alerts and event logs" about a 6h-frozen cefi-migration VM, 2026-07-27. Verified via `gcloud logging read`
  against the actual Cloud Run Job execution logs (not inferred from code alone) — the exact WARNING lines are quoted
  above. Root cause confirmed by reading `deployment-api/Dockerfile` directly and cross-checking which build stage the
  `deployment-api:latest` deployed image actually corresponds to.
assigned_vm: NA
execution_scope: local-only
drift_direction: none
depends_on: []
locked_by:
locked_since:
resolved_by:
---

# heartbeat_stall_watcher auto-kill is structurally broken in production (Docker packaging gap)

> Investigation-only record (this doc). Two frozen VMs were killed manually this session (see below) — everything else
> here is `assigned_vm: NA`, a human decides when to pick up the actual fix.

## What I found

`deployment_service/data_pipeline_monitors/cli.py::_zombie_watchdog()` (lines 357-389) tries to import
`scripts.vm.vm_zombie_watchdog` (the "image path", per its own docstring: "the monitor jobs run in the deployment-api
image where WORKDIR=/app + `scripts/` is a package") then falls back to bare `vm_zombie_watchdog`. Both fail in
production, every single sweep, for every stalled VM:

```
2026-07-27 16:21:17,890 WARNING auto-kill: vm_zombie_watchdog unavailable in runtime — cannot kill mdps-backfill-cefi-20260726-165959
2026-07-27 16:21:17,891 WARNING heartbeat_stall_watcher: mdps-backfill-cefi-20260726-165959 verdict=stall hb_age=1033.4795923333334
```

**The detection is correct** — `classify_vm_liveness()` fires `verdict=STALL` unconditional on `is_backfill` from a
stale heartbeat sidecar alone, so the WARN-level `DP_VM_STALL` `log_event()` call fires regardless of what happens next.
**The kill is not** — `_kill_stalled_vm()` (cli.py lines 418-436) needs the `vm_zombie_watchdog` module for its
`compute_v1.InstancesClient()` + `_kill_vm()` helper, and that module is never present.

### Root cause: `deployment-api/Dockerfile` only copies `scripts/` in the TEST stage

```dockerfile
# production stage "api" (lines ~50-158) — this is what deployment-api:latest IS
COPY deployment_api/ ./deployment_api/
...
CMD ["gunicorn", "deployment_api.main:app", ...]

# Stage for quality gates (test-in-image)
FROM api AS api-dev
USER root
COPY scripts/ ./scripts/        # <-- ONLY here, never in the "api" stage above
COPY tests/ ./tests/
```

`deployment-service` itself is installed into the production stage via
`uv pip install --system --no-deps /tmp/deployment-service && rm -rf /tmp/deployment-service` (lines 115-117) — a
`--no-deps` wheel install only installs the `deployment_service/` PACKAGE, never the sibling top-level `scripts/`
directory sitting next to it in that repo. So `scripts/vm/vm_zombie_watchdog.py` is **structurally absent** from
`deployment-api:latest` — this is not "the image needs a rebuild", a rebuild changes nothing without a Dockerfile edit.

### Confirmed via the Cloud Scheduler + Cloud Run Job execution history (not inferred)

- `uts-prod-dp-heartbeat-watcher-cron` (Cloud Scheduler, `*/5 * * * *`, `ENABLED`) fires the Cloud Run Job
  `uts-prod-dp-heartbeat-watcher` reliably — checked 10+ consecutive executions, all `SUCCEEDED_COUNT=1` (the process
  itself never crashes; this is a silent logic failure, not a crash).
- The deployed image is
  `asia-northeast1-docker.pkg.dev/central-element-323112/unified-trading-system/deployment-api:latest` (a floating tag).

### This is NOT limited to the cefi-migration campaign

While investigating the migration VM (`canonical-migration-cefi-content-apply-055803-cs9-1d`, frozen since 09:33 UTC,
~6h), the SAME logs showed a completely unrelated VM — `mdps-backfill-cefi-20260726-165959` — had been frozen for **17+
hours (1033 minutes)** with the identical `auto-kill: vm_zombie_watchdog unavailable` failure on EVERY 5-minute check
across that entire window. Nobody had noticed. This is a fleet-wide gap, not a migration-specific one.

### A second, independent broken safety net

Every single one of these sweeps ALSO logged:

```
2026-07-27 16:21:17,824 WARNING dispatch: repository_dispatch HTTP 422 (best-effort): HTTP Error 422: Unprocessable Entity
```

The fast-spawn dispatch (meant to hand a stuck-VM finding off to an autonomous worker when the in-band actuator can't
run) is failing on every attempt too — **not investigated further this session** (out of scope for the immediate
incident response), but it means the fallback path that's supposed to catch exactly this "actuator degraded" case is
ALSO not functioning. Whether `RelaunchStalledVm`'s relaunch actuator itself fired for either VM (independent of the raw
`vm_killer` delete) was not confirmed either — no `relaunch_stalled_vm` log lines were found in the checked windows,
which could mean its per-(vm-prefix,day) budget was already exhausted, or something else — undetermined.

## Immediate action taken this session (not a fix — a stopgap)

- Manually deleted `canonical-migration-cefi-content-apply-055803-cs9-1d` (relaunched as `cs9-1d-r2`, part of this
  session's own migration campaign — see `cefi_migration_cutover_and_track8_completion_2026_07_25.md`).
- Manually deleted `mdps-backfill-cefi-20260726-165959` (NOT relaunched — outside this session's scope; a human or a
  different agent with MDPS backfill context needs to pick up whatever shard this VM was covering).

## Todos

- [ ] [CODE] P0. Fix `deployment-api/Dockerfile` so the PRODUCTION `api` stage (not just `api-dev`) carries whatever
      `vm_zombie_watchdog.py` needs — either `COPY` the file explicitly into the production stage before the `--no-deps`
      deployment-service install discards `/tmp/deployment-service`, or restructure so the kill helper doesn't depend on
      an unpackaged sibling script. Requires an actual image rebuild + Cloud Run redeploy + verification (this is a
      **production infrastructure change**, bigger blast radius than a pure-python fix — cite
      `Evidence: cloudbuild=<id>` resolving SUCCESS per the workspace's runtime-verification HARD RULE before marking
      done).
- [ ] [CODE] P1. Investigate the `repository_dispatch HTTP 422` fast-spawn dispatch failure — a second, independent
      broken safety net that should have caught the auto-kill degradation.
- [ ] [CODE] P2. Confirm whether `RelaunchStalledVm`'s relaunch actuator (separate from the raw kill) actually fired for
      either VM, and if not, why (budget exhaustion vs a separate bug) — no `relaunch_stalled_vm` log line was found for
      either VM in the checked windows.
- [ ] [OPERATOR] P1. Someone with MDPS backfill context needs to determine what shard
      `mdps-backfill-cefi-20260726-165959` was covering and whether it needs relaunching — this session killed it as a
      stopgap but has no context on its scope/importance.
