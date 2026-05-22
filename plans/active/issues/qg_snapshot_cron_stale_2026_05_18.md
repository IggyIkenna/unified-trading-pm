---
title: QG daily snapshot cron VM stale — last run 2026-05-14 (4 days)
created: 2026-05-18
source:
  - work_split_2026_05_18_harsh.md § Slot 7 item 3
  - plans/active/deploy_missing_auto_launch_2026_05_07.md Phase 4.A (B-018)
locked_by: live-defi-rollout
priority: P2
status: active
---

## What I found

B-018 (Phase 4.A daily QG snapshot writer cron VM) was verified shipped 2026-05-14 per
`deploy_missing_auto_launch_2026_05_07.md`. Spot-check of
`gs://central-element-323112-deployment-events/quality_gates_snapshot/` on 2026-05-18 shows the most recent snapshot
subfolder is dated `2026-05-14` — 4 days stale. The VM was last launched on 2026-05-14 when the slot confirmed the cron
was wired.

**Evidence**:

- GCS path: `gs://central-element-323112-deployment-events/quality_gates_snapshot/`
- Latest dated prefix seen: `2026-05-14/` (4 days before this finding)
- B-018 launcher: `deployment-service/scripts/vm/launch-qg-snapshot-vm.sh` (or equivalent)
- Watchdog prefix registered: confirmed in `vm_zombie_watchdog.py`

## Why it matters

The QG snapshot cron VM is the continuous-verification mechanism for Phase 4 (master plan Group G). A 4-day staleness
gap means the workspace has had no automated daily quality-gate regression check since 2026-05-14. This is a
live-defi-rollout readiness blocker if the cron VM has silently stopped.

## Recommended decision

**Operator action required** — verify Cloud Scheduler job `qg-snapshot-daily-launcher` (or equivalent) status:

```bash
gcloud scheduler jobs list --project central-element-323112 | grep snapshot
gcloud scheduler jobs describe <job-name> --location <region> --project central-element-323112
```

If scheduler shows `DISABLED` or `FAILED`: re-enable + trigger a manual run:

```bash
gcloud scheduler jobs run <job-name> --project central-element-323112 --location <region>
```

If no scheduler job exists: the cron was never activated (same pattern as `honest-coverage` scheduler — requires
owner/cloudscheduler.jobs.create permissions). Operator (Ikenna) must activate.

**Slot 7 cannot activate** — `harsh` account lacks `cloudscheduler.jobs.create`/`update` permission.

## Status

`BLOCKED-OPERATOR-DECISION` — Cloud Scheduler activation requires Ikenna/owner account.

## Status update — 2026-05-22

**Investigated 2026-05-22**: confirmed no `qg-snapshot-daily` Cloud Scheduler job exists in `asia-northeast1`. The
launcher script (`launch-qg-snapshot-vm.sh`) does NOT implement `--dry-run-scheduler-body`, so the scheduler job
creation recipe in the script comments is incomplete — the Compute Engine REST API JSON body for
`gcloud scheduler jobs create http` must be constructed manually.

**Immediate fix applied**: manually launched VM `qg-snapshot-20260522-054719` (asia-northeast1-c, e2-small, RUNNING).
This will produce a fresh GCS snapshot at: `gs://central-element-323112-deployment-events/quality_gates_snapshot/`
Verify after ~30 min:

```bash
gsutil ls gs://central-element-323112-deployment-events/quality_gates_snapshot/
```

Logs: `gsutil cat gs://deployment-scripts-central-element-323112/vm-logs/qg-snapshot-20260522-054719/run.log`

**Remaining work (still needs operator/slot action)**:

- [ ] [AGENT] P1. Implement `--dry-run-scheduler-body` flag in `launch-qg-snapshot-vm.sh` to output the Compute Engine
      REST API JSON body for the Cloud Scheduler job creation.
- [ ] [AGENT] P1. Create Cloud Scheduler job `qg-snapshot-daily` at `0 6 * * *` UTC using service account
      `uts-prod-batch-sa@central-element-323112.iam.gserviceaccount.com` + location `asia-northeast1`.

Until the Cloud Scheduler job exists, the daily snapshot must be launched manually. This issue stays active until the
Cloud Scheduler job is confirmed healthy (not just the launcher script landing once).
