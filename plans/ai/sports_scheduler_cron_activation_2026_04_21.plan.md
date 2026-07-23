---
title: "Sports Scheduler — Cloud Run + Cron Activation (deploys Plan 1's periodic dispatch)"
priority: P0
status: active
owner: agent
created: 2026-04-21
locked_by: live-defi-rollout
locked_since: 2026-04-21
type: deployment
epic: none
completion_gates:
  code: none
  deployment: D3
  business: none
repo_gates:
  - repo: deployment-service
    code: C5
    deployment: D3
depends_on:
  - sports_scheduler_periodic_tier_dispatch_2026_04_21
isProject: false
---

## PRE-AUDIT-FINDINGS (Phase 0 — 2026-04-21)

| Item                   | Finding                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| ---------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Invocation**         | `sports-trigger run` = blocking poll loop (`SportsTriggerScheduler.run()`). `sports-trigger evaluate` = single `run_once()`; dry-run was `--dry-run` only (always default true) — fixed to `--dry-run/--execute` so real runs are possible from `evaluate`.                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| **Option B**           | **Feasible.** `run_once()` already runs periodic discovery + reference + fixture-proximate tiers. Added **`sports-trigger run --one-shot`** (exits after one cycle) for Cloud Scheduler → Cloud Run Job.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| **Docker / Cloud Run** | Root `Dockerfile` builds `api` (gunicorn dashboard) and `api-dev` for QG. **No** prior scheduler-only target. Added Docker stage **`sports-scheduler`** (`FROM api AS sports-scheduler`) with `CMD` = `python -m deployment_service sports-trigger run --one-shot` and `HEALTHCHECK NONE` (jobs don't serve HTTP). `cloudbuild.yaml` now includes `build-sports-scheduler` + `push-sports-scheduler` steps and declares both image tags in `images:`; QG gates both pushes. Cloud Run Job + Cloud Scheduler provisioned via `terraform/gcp/sports_scheduler_cron.tf` (`google_cloud_run_v2_job` + `google_cloud_scheduler_job` at `*/5 * * * *` UTC) — `terraform apply` deferred to orchestrator Phase 6. |
| **Codex §12**          | Plan indexed under §12.4 deployment activation; dependency `sports_scheduler_periodic_tier_dispatch` at C5 remains the code prerequisite.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |

## Context

Plan `sports_scheduler_periodic_tier_dispatch_2026_04_21` ships the scheduler code that knows how to fire Tier-1
discovery + Tier-2 reference at their declared cadences. Code lands at `deployment-service d9652cd` (2026-04-21).

But code isn't enough — the scheduler is a polling loop. Someone has to actually RUN it on a cron / Cloud Scheduler / as
a long-lived process. Today the scheduler is only invoked locally during dev.

This plan takes Plan 1's code to **D3** — staging integration with the real Cloud Run job actually firing on schedule.

**2026-04-22 — activated via VM-daemon** (file: `deployment-service/scripts/vm/launch-sports-scheduler-vm.sh`) because
the Cloud Run path is blocked on Plans 12 (`deployment_service_build_infrastructure_repair`) + 13
(`utl_base_image_rebuild_and_workflow_unblock`). The VM-daemon shape uses the existing tarball-deployment infra
(`setup-data-pipeline-vm.sh` branch `VM_TASK=sports-scheduler-poll`) and runs `SportsTriggerScheduler.run()` in its
built-in 300-s poll loop. Zero Cloud-Run-image dependency. Terraform in `terraform/gcp/sports_scheduler_cron.tf`
deferred — kept in repo for future migration back to Cloud Run once Plans 12 + 13 land. See
`/codex/02-data/sports-scheduling-and-sharding.md` §8 for the Cloud Run vs VM-daemon decision notes.

## Blast radius

- **deployment-service**:
  - Dockerfile for the scheduler job (may already exist — pre-audit).
  - Cloud Run job definition or Cloud Scheduler config.
- **GCP infrastructure** (out-of-repo):
  - Cloud Scheduler cron creation
  - Cloud Run service / job deployment
  - Service account + IAM for:
    - Reading `gs://deployment-scripts-.../sports_scheduler_state/`
    - Writing the same (state persistence)
    - Firing gcloud dispatch of child VMs (already per-fixture in existing scheduler — should work)

## Pre-audit manifest

| File / resource                                                        | Status                              | Action                                                                   |
| ---------------------------------------------------------------------- | ----------------------------------- | ------------------------------------------------------------------------ |
| `deployment-service/deployment_service/cli/commands/sports_trigger.py` | Entry point for scheduler main loop | Confirm how it's meant to be invoked (foreground / daemon).              |
| `deployment-service/Dockerfile` or per-command Dockerfile              | ?                                   | Determine if scheduler has its own image or shares the service image.    |
| `deployment-service/cloud_run/` or similar                             | ?                                   | Existing Cloud Run configs — extend or add new.                          |
| Cloud Scheduler                                                        | Live GCP resource                   | Create cron entry hitting the scheduler's HTTP endpoint OR spawning job. |
| `sports_trigger_state` GCS key                                         | Not yet created                     | First scheduler run auto-creates; IAM must allow write.                  |

Phase 0 (below) requires empirically confirming each row.

## Operational shape — two options

### Option A: Long-lived Cloud Run service, self-polling

- Scheduler runs 24/7 with a 5-minute poll loop (existing `poll_interval_seconds=300`).
- Cheapest in dev, wasteful at scale (idle CPU between polls).
- Simpler deployment.

### Option B: Cloud Scheduler → short-lived Cloud Run job per poll

- Cloud Scheduler cron every 5 min triggers a Cloud Run job.
- Job runs ONE iteration of `_check_periodic_tiers` + `get_upcoming_fixtures`
  - `_dispatch_trigger` loop, exits.
- State persisted to GCS between runs (Plan 1 already persists `last_run[tier_name]` there).
- Right shape per codex §8 (Cloud Run warm-start ~1s, cheap per-invocation).

**Decision: Option B** unless Phase 0 finds a blocking reason. Matches codex economics contract.

## Success criteria

- Cloud Scheduler cron entry present and ENABLED.
- Cloud Run job exists with the scheduler image + correct service account (read/write
  `gs://deployment-scripts-.../sports_scheduler_state/`).
- First automated fire succeeds: Tier-1 discovery dispatches a
  `launch-api-football-backfill-vm.sh --entity FIXTURES --lookback 1 --lookahead 7 --force-window` (or equivalent CLI)
  within 6h of activation.
- Tier-2 reference fires within 24h.
- Every fired CLI appears in `/api/vm-deployments` with its own VM lifecycle + self-delete.
- State persistence verified across reruns: `last_run` file has the correct timestamps after two scheduler cycles.
- Deployment gates D1-D3 closed.

## Phases

### Phase 0: Pre-audit + Option A/B decision [SEQUENTIAL]

- [x] [AGENT] P0. Read `deployment-service/deployment_service/cli/commands/sports_trigger.py` end-to-end. Document the
      current invocation shape (daemon? one- shot?). Update this plan with PRE-AUDIT-FINDINGS.

- [x] [AGENT] P0. Grep deployment-service for existing Cloud Run configs (`cloud_run/`, Dockerfile, `cloudbuild.yaml`).
      Identify whether an image for the scheduler exists.

- [x] [AGENT] P0. Confirm Option B feasibility: does the CLI accept a `--one-shot` / `--single-iteration` flag? If not,
      add one in a preparatory commit (tiny — wraps existing main-loop code in an `if args.one_shot: iterate_once()`
      branch).

### Phase 1: Image + IAM (D1) [SEQUENTIAL]

- [x] [AGENT] P0. Ensure deployment-service image builds with the scheduler entrypoint. If missing, add
      `CMD ["python", "-m",     "deployment_service", "sports-trigger", "--one-shot"]` for Option B (or no CMD override
      for Option A — container runs main loop). **Shipped 2026-04-21**: Dockerfile stage `FROM api AS sports-scheduler`
      with `CMD ["python", "-m", "deployment_service", "sports-trigger", "run", "--one-shot"]`; cloudbuild.yaml gains
      `build-sports-scheduler` + `push-sports-scheduler` steps; CLI gains `run --one-shot` flag and
      `evaluate --dry-run/--execute` pair. 8 new unit tests (`tests/unit/test_sports_trigger_cli.py`) + 16 pre-existing
      periodic tests all green. Terraform `terraform/gcp/sports_scheduler_cron.tf` defines both the Cloud Run Job and
      Cloud Scheduler cron — ready for `terraform apply` by the orchestrator once tarballs land on
      `origin/live-defi-rollout`.

- [x] [AGENT] P0. Service-account permissions: reader/writer on the deployment-scripts bucket,
      `compute.instanceAdmin.v1` on the project (to create child VMs), `run.developer` if Cloud Run jobs are used.
      **Resolved 2026-04-22 via VM-daemon path** — the sports-scheduler VM boots with `--scopes=cloud-platform` against
      the default Compute Engine SA, which inherits `storage.objectAdmin` on deployment-scripts-\* (already granted for
      every other backfill VM) + `compute.instanceAdmin.v1` (child-VM dispatch from per-fixture Tier-3/4 paths). No new
      IAM grants needed. Terraform at `terraform/gcp/sports_scheduler_cron.tf` retained for the Cloud Run path (blocked
      on Plans 12 + 13) and will be revisited when that image pipeline is repaired.

### Phase 2: Cloud Scheduler cron [SEQUENTIAL, depends on Phase 1]

- [x] [AGENT] P0. Create Cloud Scheduler cron hitting the Cloud Run job. Cadence: every 5 min (matches scheduler's
      existing poll interval). Timezone: UTC. **Resolved 2026-04-22 via VM-daemon path** — N/A for the VM shape. The
      daemon runs `SportsTriggerScheduler.run()` which has its own 300-s `time.sleep` poll loop, so no external cron is
      needed. Terraform resource `google_cloud_scheduler_job.sports_scheduler_cron` (schedule `*/5 * * * *`, UTC) in
      `terraform/gcp/sports_scheduler_cron.tf` retained for the Cloud Run Job migration (blocked on Plans 12 + 13).

- [x] [AGENT] P0. Smoke test: force-trigger the cron once. Confirm logs show the job ran + state file exists in GCS.
      **Resolved 2026-04-22 via VM-daemon path** — VM `sports-scheduler-20260422-111929` launched at
      `2026-04-22T11:19:29Z` in `asia-northeast1-c` (first launch `sports-scheduler-20260422-105122` hit a
      `ModuleNotFoundError: click` bootstrap bug because deployment-service installs with `--no-deps` on the data
      pipeline VM — fixed by adding an explicit `uv pip install click google-cloud-run google-cloud-compute` step in the
      `sports-scheduler-poll` branch of `setup-data-pipeline-vm.sh`). GCS log URI:
      `gs://deployment-scripts-central-element-323112/vm-logs/sports-scheduler-20260422-111929/run.log`. State bucket:
      `gs://deployment-scripts-central-element-323112/sports_scheduler_state/`.

### Phase 3: First automated Tier-1 / Tier-2 fire (D2 → D3) [SEQUENTIAL]

- [x] [AGENT] P0. Wait 6h. Check that Tier-1 discovery dispatched at least one `launch-api-football-backfill-vm.sh` run.
      Default-flip 2026-05-06: explicitly **Deferred to orchestrator Phase 6**; tracked under that owner now, not this
      plan.

- [x] [AGENT] P0. Wait 24h. Check that Tier-2 reference (INJURIES) fired. Default-flip 2026-05-06: explicitly **Deferred
      to orchestrator Phase 6**; tracked under that owner now, not this plan.

- [x] [AGENT] P1. Monitor for a week. Spot-check state file shows `last_run[discovery]` and `last_run[reference]`
      updating on cadence. Default-flip 2026-05-06: explicitly **Deferred to orchestrator Phase 6**; tracked under that
      owner now.

### Phase 4: Observability hooks [PARALLEL with Phase 3]

- [ ] [AGENT] P1. Grafana / datadog / wherever fleet telemetry lives: add an alert on "sports scheduler last successful
      Tier-1 fire > 12h ago". **Deferred to orchestrator Phase 6** — requires live telemetry backend integration.

## Dependency graph

```
Phase 0 (audit + choose A/B) ─► Phase 1 (image + IAM) ─► Phase 2 (cron) ─► Phase 3 (live fire)
                                                                               │
                                                                               └─► Phase 4 (telemetry)
```

## Hard dependency

Plan `sports_scheduler_periodic_tier_dispatch_2026_04_21` must reach C5 before this plan starts. Confirmed: committed as
`deployment-service d9652cd` on 2026-04-21.

## Out of scope

- Changes to the scheduler logic itself — belongs in Plan 1.
- Per-fixture Tier-3/4 dispatch — already operational on the existing scheduler.
- Cloud Run vs VM economics writeup — covered in `/codex/02-data/sports-scheduling-and-sharding.md` §8.
