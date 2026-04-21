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
    deployment: D0
depends_on:
  - sports_scheduler_periodic_tier_dispatch_2026_04_21
isProject: false
---

## Context

Plan `sports_scheduler_periodic_tier_dispatch_2026_04_21` ships the
scheduler code that knows how to fire Tier-1 discovery + Tier-2
reference at their declared cadences. Code lands at
`deployment-service d9652cd` (2026-04-21).

But code isn't enough — the scheduler is a polling loop. Someone has
to actually RUN it on a cron / Cloud Scheduler / as a long-lived
process. Today the scheduler is only invoked locally during dev.

This plan takes Plan 1's code to **D3** — staging integration with the
real Cloud Run job actually firing on schedule.

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
    - Firing gcloud dispatch of child VMs (already per-fixture in
      existing scheduler — should work)

## Pre-audit manifest

| File / resource                                                         | Status                              | Action                                                                     |
| ----------------------------------------------------------------------- | ----------------------------------- | -------------------------------------------------------------------------- |
| `deployment-service/deployment_service/cli/commands/sports_trigger.py`  | Entry point for scheduler main loop | Confirm how it's meant to be invoked (foreground / daemon).                |
| `deployment-service/Dockerfile` or per-command Dockerfile               | ?                                   | Determine if scheduler has its own image or shares the service image.       |
| `deployment-service/cloud_run/` or similar                              | ?                                   | Existing Cloud Run configs — extend or add new.                             |
| Cloud Scheduler                                                         | Live GCP resource                   | Create cron entry hitting the scheduler's HTTP endpoint OR spawning job.    |
| `sports_trigger_state` GCS key                                          | Not yet created                     | First scheduler run auto-creates; IAM must allow write.                     |

Phase 0 (below) requires empirically confirming each row.

## Operational shape — two options

### Option A: Long-lived Cloud Run service, self-polling

- Scheduler runs 24/7 with a 5-minute poll loop (existing
  `poll_interval_seconds=300`).
- Cheapest in dev, wasteful at scale (idle CPU between polls).
- Simpler deployment.

### Option B: Cloud Scheduler → short-lived Cloud Run job per poll

- Cloud Scheduler cron every 5 min triggers a Cloud Run job.
- Job runs ONE iteration of `_check_periodic_tiers` + `get_upcoming_fixtures`
  + `_dispatch_trigger` loop, exits.
- State persisted to GCS between runs (Plan 1 already persists
  `last_run[tier_name]` there).
- Right shape per codex §8 (Cloud Run warm-start ~1s, cheap per-invocation).

**Decision: Option B** unless Phase 0 finds a blocking reason. Matches
codex economics contract.

## Success criteria

- Cloud Scheduler cron entry present and ENABLED.
- Cloud Run job exists with the scheduler image + correct service account
  (read/write `gs://deployment-scripts-.../sports_scheduler_state/`).
- First automated fire succeeds: Tier-1 discovery dispatches a
  `launch-api-football-backfill-vm.sh --entity FIXTURES --lookback 1
  --lookahead 7 --force-window` (or equivalent CLI) within 6h of
  activation.
- Tier-2 reference fires within 24h.
- Every fired CLI appears in `/api/vm-deployments` with its own VM
  lifecycle + self-delete.
- State persistence verified across reruns: `last_run` file has the
  correct timestamps after two scheduler cycles.
- Deployment gates D1-D3 closed.

## Phases

### Phase 0: Pre-audit + Option A/B decision [SEQUENTIAL]

- [ ] [AGENT] P0. Read
      `deployment-service/deployment_service/cli/commands/sports_trigger.py`
      end-to-end. Document the current invocation shape (daemon? one-
      shot?). Update this plan with PRE-AUDIT-FINDINGS.

- [ ] [AGENT] P0. Grep deployment-service for existing Cloud Run configs
      (`cloud_run/`, Dockerfile, `cloudbuild.yaml`). Identify whether an
      image for the scheduler exists.

- [ ] [AGENT] P0. Confirm Option B feasibility: does the CLI accept a
      `--one-shot` / `--single-iteration` flag? If not, add one in a
      preparatory commit (tiny — wraps existing main-loop code in an
      `if args.one_shot: iterate_once()` branch).

### Phase 1: Image + IAM (D1) [SEQUENTIAL]

- [ ] [AGENT] P0. Ensure deployment-service image builds with the
      scheduler entrypoint. If missing, add `CMD ["python", "-m",
      "deployment_service", "sports-trigger", "--one-shot"]` for Option
      B (or no CMD override for Option A — container runs main loop).

- [ ] [AGENT] P0. Service-account permissions: reader/writer on the
      deployment-scripts bucket, `compute.instanceAdmin.v1` on the
      project (to create child VMs), `run.developer` if Cloud Run jobs
      are used.

### Phase 2: Cloud Scheduler cron [SEQUENTIAL, depends on Phase 1]

- [ ] [AGENT] P0. Create Cloud Scheduler cron hitting the Cloud Run job.
      Cadence: every 5 min (matches scheduler's existing poll interval).
      Timezone: UTC.

- [ ] [AGENT] P0. Smoke test: force-trigger the cron once. Confirm logs
      show the job ran + state file exists in GCS.

### Phase 3: First automated Tier-1 / Tier-2 fire (D2 → D3) [SEQUENTIAL]

- [ ] [AGENT] P0. Wait 6h. Check that Tier-1 discovery dispatched at
      least one `launch-api-football-backfill-vm.sh` run.

- [ ] [AGENT] P0. Wait 24h. Check that Tier-2 reference (INJURIES) fired.

- [ ] [AGENT] P1. Monitor for a week. Spot-check state file shows
      `last_run[discovery]` and `last_run[reference]` updating on cadence.

### Phase 4: Observability hooks [PARALLEL with Phase 3]

- [ ] [AGENT] P1. Grafana / datadog / wherever fleet telemetry lives:
      add an alert on "sports scheduler last successful Tier-1 fire >
      12h ago".

## Dependency graph

```
Phase 0 (audit + choose A/B) ─► Phase 1 (image + IAM) ─► Phase 2 (cron) ─► Phase 3 (live fire)
                                                                               │
                                                                               └─► Phase 4 (telemetry)
```

## Hard dependency

Plan `sports_scheduler_periodic_tier_dispatch_2026_04_21` must reach C5
before this plan starts. Confirmed: committed as `deployment-service
d9652cd` on 2026-04-21.

## Out of scope

- Changes to the scheduler logic itself — belongs in Plan 1.
- Per-fixture Tier-3/4 dispatch — already operational on the existing
  scheduler.
- Cloud Run vs VM economics writeup — covered in
  `codex/02-data/sports-scheduling-and-sharding.md` §8.
