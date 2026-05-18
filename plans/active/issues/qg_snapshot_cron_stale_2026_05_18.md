---
title: QG daily snapshot cron VM stale — last run 2026-05-14 (4 days)
created: 2026-05-18
author: harsh-slot-7
source:
  - work_split_2026_05_18_harsh.md § Slot 7 item 3
  - plans/active/deploy_missing_auto_launch_2026_05_07.md Phase 4.A (B-018)
locked_by: live-defi-rollout
---

## What I found

B-018 (Phase 4.A daily QG snapshot writer cron VM) was verified shipped 2026-05-14 per
`deploy_missing_auto_launch_2026_05_07.md`. Spot-check of
`gs://central-element-323112-deployment-events/quality_gates_snapshot/` on 2026-05-18 shows the most
recent snapshot subfolder is dated `2026-05-14` — 4 days stale. The VM was last launched on 2026-05-14
when the slot confirmed the cron was wired.

**Evidence**:
- GCS path: `gs://central-element-323112-deployment-events/quality_gates_snapshot/`
- Latest dated prefix seen: `2026-05-14/` (4 days before this finding)
- B-018 launcher: `deployment-service/scripts/vm/launch-qg-snapshot-vm.sh` (or equivalent)
- Watchdog prefix registered: confirmed in `vm_zombie_watchdog.py`

## Why it matters

The QG snapshot cron VM is the continuous-verification mechanism for Phase 4 (master plan Group G). A
4-day staleness gap means the workspace has had no automated daily quality-gate regression check since
2026-05-14. This is a live-defi-rollout readiness blocker if the cron VM has silently stopped.

## Recommended decision

**Operator action required** — verify Cloud Scheduler job `qg-snapshot-daily-launcher` (or equivalent)
status:

```bash
gcloud scheduler jobs list --project central-element-323112 | grep snapshot
gcloud scheduler jobs describe <job-name> --location <region> --project central-element-323112
```

If scheduler shows `DISABLED` or `FAILED`: re-enable + trigger a manual run:
```bash
gcloud scheduler jobs run <job-name> --project central-element-323112 --location <region>
```

If no scheduler job exists: the cron was never activated (same pattern as `honest-coverage` scheduler —
requires owner/cloudscheduler.jobs.create permissions). Operator (Ikenna) must activate.

**Slot 7 cannot activate** — `harsh` account lacks `cloudscheduler.jobs.create`/`update` permission.

## Status

`BLOCKED-OPERATOR-DECISION` — Cloud Scheduler activation requires Ikenna/owner account.
