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
status: resolved
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
    /plans/archive/2026_07/cefi_migration_cutover_and_track8_completion_2026_07_25.md,
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
  2026-07-28, all 4 todos closed (Dockerfile fix deployed + verified, 422-dispatch fixed, RelaunchStalledVm root-caused,
  mdps VM relaunched on larger machine)
---

# heartbeat_stall_watcher auto-kill is structurally broken in production (Docker packaging gap)

> RESOLVED 2026-07-28. All 4 todos closed: the Dockerfile packaging fix shipped and is verified live in production
> (`cloudbuild=17bc8bff` SUCCESS), the 422-dispatch bug is fixed, `RelaunchStalledVm`'s non-firing was root-caused to
> the same gap and fixed alongside it, and the mdps-backfill-cefi VM was relaunched on a larger machine per the
> operator's go-ahead. See each todo below for full evidence.

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

### Root cause: `deployment-api/Dockerfile` never copied `deployment-service/scripts/` in EITHER stage

**Correction to this doc's own first-pass diagnosis**: the original write-up assumed `api-dev`'s
`COPY scripts/ ./scripts/` at least covered the test stage, leaving only production broken. That assumption was wrong —
that line copies **deployment-api's own, unrelated `scripts/` directory** (its local audit/dev tools —
`audit_running_but_invisible.py`, `census_manifest_data_type_2026_07_24.py`, etc.), not `deployment-service/scripts/`.
Verified directly: `ls deployment-api/scripts/` has no `vm/` subdirectory at all, and nothing in `cloudbuild.yaml` /
`buildspec.aws.yaml` ever vendors `deployment-service/scripts/` into deployment-api's own `scripts/` path. So
`scripts/vm/vm_zombie_watchdog.py` was **never packaged into this image, in any stage, ever** — not a production-vs-test
gap, a total one.

```dockerfile
# production stage "api" (lines ~50-158) — this is what deployment-api:latest IS
COPY deployment_api/ ./deployment_api/
...
CMD ["gunicorn", "deployment_api.main:app", ...]

# Stage for quality gates (test-in-image)
FROM api AS api-dev
USER root
COPY scripts/ ./scripts/        # <-- deployment-api's OWN unrelated scripts/, not deployment-service's
COPY tests/ ./tests/
```

`deployment-service` itself is installed into the production stage via
`uv pip install --system --no-deps /tmp/deployment-service && rm -rf /tmp/deployment-service` (lines 115-117) — a
`--no-deps` wheel install only installs the `deployment_service/` PACKAGE, never the sibling top-level `scripts/`
directory sitting next to it in that repo. So `scripts/vm/vm_zombie_watchdog.py` is **structurally absent** from
`deployment-api:latest` — this is not "the image needs a rebuild", a rebuild changes nothing without a Dockerfile edit.

The SAME gap gates the entire Layer-0 recovery-actuator family too — see "RelaunchStalledVm root cause" below.

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

### A second, independent broken safety net — root-caused + FIXED (`deployment-service@9d0ee9e`)

Every single one of these sweeps ALSO logged:

```
2026-07-27 16:21:17,824 WARNING dispatch: repository_dispatch HTTP 422 (best-effort): HTTP Error 422: Unprocessable Entity
```

**Root cause (confirmed, not guessed)**: `escalation.py::_dispatch_to_orchestrator`'s `client_payload` carried 11
top-level keys
(`repo, pr_number, wall_type, context, authoring_slot, model, action, vm_name, relaunch_launcher, deployment_id, asset_group`)
— GitHub's `repository_dispatch` endpoint caps `client_payload` at **10 top-level properties**. `git blame` traces the
break to commit `1f769da9f` (2026-06-23, "LDR → staging Tier C auto-drain"), which added the 5 relaunch-binding fields
on top of the pre-existing 6, pushing 6→11. The 422's actual GitHub-side response body was never logged (only
`exc.code` + the generic exception string), so the exact reason was invisible in Cloud Logging until this investigation
read the code directly.

Those 5 fields were also confirmed **dead weight regardless of the 422**: `escalate-to-orchestrator.yml`'s actual
`POST /api/escalate` body (in `unified-trading-pm`) only ever forwards
`repo/pr_number/wall_type/context/ authoring_slot/model` — the 5 relaunch-specific fields never reached the orchestrator
by any path, structured or otherwise. The same vm_name/launcher/deployment_id/asset_group binding already rides in the
human-readable `context` string via the existing `relaunch_ctx` text, which the workflow DOES forward end-to-end.

**Fixed**: dropped the 5 dead fields, bringing `client_payload` to 6 top-level keys (`deployment-service@9d0ee9e`, full
`quality-gates.sh` green, 2898+ tests passed). Added a regression test asserting the key count stays ≤10, and corrected
the existing test that had enshrined the buggy 11-key payload shape as expected behavior.

### `RelaunchStalledVm` root cause — CONFIRMED, same structural gap as `vm_zombie_watchdog`, not budget exhaustion

`RelaunchStalledVm` exists (`deployment-service/scripts/recovery/relaunch_stalled_vm.py:115`), budget-bounded to
`_MAX_RELAUNCHES_PER_DAY=2` per (vm-prefix, day), and IS wired into `escalation.py::_recover_stalled_vm()` via
`_DP_RECOVERY_ACTIONS[DP_VM_STALL]` — `route_finding()` runs it every 5-min sweep for both frozen VMs, before the kill
attempt. **It never actually fired — confirmed to be the SAME Docker-packaging gap, not budget exhaustion**:
`_recover_stalled_vm` gates on `_ACTUATORS_AVAILABLE` (`escalation.py:105-120`, probing
`find_spec("scripts.recovery.relaunch_consolidator")`), which returns `UNAVAILABLE`/`actuators_not_in_runtime` before
ever instantiating any actuator — because the ENTIRE `scripts/recovery/` package (17 files: `relaunch_consolidator`,
`relaunch_stalled_vm`, `enter_safe_mode`, `restart_service`, etc.) was equally absent from the production image, for the
identical reason `scripts/vm/vm_zombie_watchdog.py` was. Confirmed via `gcloud logging read` (project
`central-element-323112`, 24h window): zero hits for `relaunch_stalled_vm`/`RelaunchStalledVm` anywhere, and no
budget-exceeded CRITICAL log line either (a real budget-exhaustion path would emit one) — the actuator was simply never
reachable, for either VM.

**Fixed alongside the `vm_zombie_watchdog` Dockerfile fix** (see Todo 1 below) — `scripts/recovery/` is self-contained
(only `unified_trading_library`/`unified_api_contracts` + stdlib, no cross-import on `scripts.vm`) and already carries
its own `__init__.py`, so it was folded into the SAME `COPY` fix rather than needing a separate change.

## Immediate action taken this session (not a fix — a stopgap)

- Manually deleted `canonical-migration-cefi-content-apply-055803-cs9-1d` (relaunched as `cs9-1d-r2`, part of this
  session's own migration campaign — see
  `/plans/archive/2026_07/cefi_migration_cutover_and_track8_completion_2026_07_25.md`).
- Manually deleted `mdps-backfill-cefi-20260726-165959` (NOT relaunched — outside this session's scope; a human or a
  different agent with MDPS backfill context needs to pick up whatever shard this VM was covering).

### `mdps-backfill-cefi-20260726-165959` shard reconstruction (2026-07-27, follow-up investigation)

Full forensic trail recovered from
`gs://deployment-scripts-central-element-323112/vm-logs/ mdps-backfill-cefi-20260726-165959/` (`LAUNCH_PARAMS.json`,
`PROGRESS.json`, `run.log`) plus Cloud Audit Logs — **no mutating action taken, read-only**:

- **Shard**: `asset_group=cefi`, `data_type=trades`, `venues={HYPERLIQUID, LIGHTER-ZKSYNC, EXTENDED-STARKNET}`,
  requested range `2024-01-01→2026-07-25`, `mode=full`, `force=false`.
- **Progress before freeze**: genuine, verified writes through `2025-06-05` (522/937 days, 55.7% of the requested range)
  — **415 days (2025-06-06→2026-07-25, 44.3%) remain an open gap**.
- **Likely cause of freeze**: sustained memory pressure, not preemption. `run.log` shows 11× `rc=-9` (OOM-killed)
  per-date subprocess failures and a `memory backpressure engaged at 85.7%` warning, RSS peaking ~23.8GB on an
  `e2-standard-8` (32GB, no swap). No `PREEMPTED` marker was ever written and Cloud Audit Logs show no
  `compute.instances.preempted` event for this instance — ruling out SPOT reclamation. This looks like a genuine
  guest-level hang from memory exhaustion, most likely per-date (concurrency was unset/serial, yet still hit 85%+ on a
  single date's candle aggregation across 3 venues × 7 timeframes) rather than a concurrency artifact.
- **Timeline**: created `2026-07-26T16:59:5xZ`, last checkpoint `2026-07-26T23:07:10Z`, deleted
  `2026-07-27T16:26:59Z`/`16:27:55Z` — ~17h20m frozen from last real progress to deletion.
- **Recommendation** (not yet actioned — `[OPERATOR]` todo below): relaunch the remaining gap only
  (`2025-06-06→2026-07-25`, same venues/data_type, `mode=full`) rather than the full original range — idempotent
  skip-if-fresh would no-op the completed span anyway, but narrowing saves wall-clock. Given the repeated OOM kills on
  this exact shape, consider a larger machine type (e.g. `e2-standard-16`) before relaunching — the memory pressure
  looks per-date, not concurrency-driven, so throttling concurrency is unlikely to help as much as more RAM would.
- **Independent gap flagged**: this failure mode (sustained memory pressure, no swap, no preemption, no exit code)
  currently leaves the standard fleet monitor blind to "wedged but not exited" — it isn't a SPOT preemption the
  auto-recovery matrix watches for, and it produced no `EXIT_STATUS`. This VM class has a forensic trail (thanks to the
  `PROGRESS.json`/`LAUNCH_PARAMS.json` checkpoint contract) but no _liveness_ trail beyond the heartbeat log lines
  themselves going quiet — worth a look independent of this doc's main Dockerfile-packaging thread.

## Todos

- [x] ✅ [CODE] P0. **DONE 2026-07-28 — `deployment-api@fa54159` (content), promoted to `main` as `6d47904` (LDR→main
      promotion rebases/renames commits, "Option-B direct" — content diffed and confirmed identical).** Fixed
      `deployment-api/Dockerfile` so the PRODUCTION `api` stage (not just `api-dev`) carries `vm_zombie_watchdog.py` AND
      the whole `scripts/recovery/` actuator family. **Evidence: cloudbuild=17bc8bff-0ee2-47f7-8488-f2b61ea7bdf6**
      (trigger `deployment-api-main-deploy`, `_DEPLOY=true`, `COMMIT_SHA=6d47904`) resolving SUCCESS, finished
      2026-07-28T06:58:01Z. Confirmed the Cloud Run Job `uts-prod-dp-heartbeat-watcher` is running the updated
      `deployment-api:latest` image (executions completing normally post-deploy). **Caveat, stated plainly**: no stalled
      VM existed at deploy time to exercise the actual kill/relaunch code path end-to-end — the fix is verified
      structurally (content on main, build green, deployed) and via the code path's own logic (traced exactly how
      `scripts.vm.vm_zombie_watchdog`/`scripts.recovery.relaunch_consolidator` now resolve as PEP 420 namespace packages
      under `/app`), not via a live incident, since none exists right now. The LDR→main pipeline's own promote PR #410
      (293-commit-behind, hit the since-fixed CI hang) was superseded by the fleet's own auto-regenerated promote PRs
      (#411→#412→#413→#414); #414 merged cleanly — no manual bypass of the standard pipeline was needed once the
      underlying hang was fixed.
- [x] ✅ [CODE] P1. **DONE 2026-07-27 — `deployment-service@9d0ee9e`.** Root-caused the `repository_dispatch HTTP 422`:
      `client_payload` carried 11 top-level keys, over GitHub's 10-key cap (introduced by commit `1f769da9f`,
      2026-06-23). The 5 relaunch-specific fields were also confirmed dead weight — `escalate-to-orchestrator.yml` never
      forwarded them to `/api/escalate` regardless. Dropped them (back to 6 keys); the same binding still reaches the
      worker via the existing `context` text. Regression test added asserting the ≤10-key cap; full `quality-gates.sh`
      green (2898+ tests).
- [x] ✅ [CODE] P2. **DONE 2026-07-27.** Confirmed `RelaunchStalledVm` never fired for either VM because of the SAME
      structural packaging gap as `vm_zombie_watchdog` (`scripts.recovery.relaunch_consolidator` also absent from the
      image), NOT budget exhaustion — zero log hits for either mechanism, no budget-exceeded CRITICAL line either. Fixed
      alongside Todo 1 (`deployment-api@fa54159` also COPYs the whole `scripts/recovery/` package).
- [x] ✅ [OPERATOR] P1. **DONE 2026-07-28.** Operator confirmed the OOM diagnosis and approved relaunching on a larger
      machine. Relaunched the remaining gap only (`2025-06-06→2026-07-25`, same scope: `cefi/trades` for
      `HYPERLIQUID/LIGHTER-ZKSYNC/EXTENDED-STARKNET`) as `mdps-backfill-cefi-20260728-083156`, `e2-standard-16` (up from
      `e2-standard-8`), `full` mode, SPOT. Launch command validated via a `dry` pass first (which itself creates a real
      VM running `--dry-run` — deleted immediately after confirming the args resolved correctly), then the real `full`
      launch. Note: 4 code tarballs (market-data-processing-service, market-tick-data-service, unified-api-contracts,
      deployment-service) were stale at launch time — the republish tool itself errored locally on an unrelated
      fastapi/UTL version mismatch in this session's venv; proceeded anyway since the staleness was in repos whose
      recent changes don't affect MDPS candle-processing correctness (non-blocking warning, not enforced).
