---
doc_type: issue
title:
  "A VM relaunched under a NEW name cannot resume from a prior VM's PROGRESS.json checkpoint — re-walks from START_DATE"
summary: >-
  Distinct from cefi_track2_backfill_vm_preempted_no_recovery_2026_07_30.md (which covers PROGRESS.json not being
  WRITTEN at all for a launcher family, now fixed via deployment-service@28b7dce) — this is about a launcher that DOES
  write PROGRESS.json correctly, but a manual relaunch after the original VM dies (whether preemption or an undetermined
  OOM-class kill) creates a NEW VM with a new name/log path, which has no mechanism to read the DEAD VM's checkpoint
  file. Net effect: the relaunch silently re-walks from the original START_DATE instead of resuming from the last
  completed date, wasting real API calls/wall-clock (idempotent re-fetch, not data-corrupting, but a real cost this
  workspace's own resume-checkpoint contract is supposed to prevent).
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [deployment-service, market-tick-data-service]
scope: [engineer, admin]
tags: [vm-launcher, spot-preemption, resume-checkpoint, billing-waste]
related:
  [
    /plans/active/issues/cefi_track2_backfill_vm_preempted_no_recovery_2026_07_30.md,
    /codex/05-infrastructure/spot-vms-for-backfill.md,
  ]
parent_epic: cefi_master
source:
  "CeFi equity-perp Tardis backfill, 2026-08-12 interactive session — cefi-okx-swap-2026-heavy VM died silently mid-run
  (RSS 17.7GB→51GB in <4min, no exit_code/traceback/preemption marker), manual relaunch under a new VM name confirmed
  re-walking already-captured dates"
assigned_vm: NA
created: 2026-08-12
resolved_by:
locked_by:
locked_since:
priority: P2
execution_scope: local-only
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /codex/05-infrastructure/spot-vms-for-backfill.md,
    /plans/active/issues/cefi_track2_backfill_vm_preempted_no_recovery_2026_07_30.md,
  ]
---

# VM relaunch under a new name cannot resume from a prior VM's checkpoint

## What was found (2026-08-12)

`cefi-okx-swap-2026-heavy-20260812-225944` (a `launch-cefi-sharded-backfill.sh` VM) correctly processed 2026-02-25
through 2026-04-14 (`PROGRESS.json: last_completed_date=2026-04-14, monotonic=true`), each day logging real captured
trades+book_snapshot_5 rows. It then died silently while processing 2026-04-19 — RSS climbed 17.7GB→51GB in under 4
minutes, then the log stops entirely: no `exit_code=`, no traceback, no SIGTERM/SIGKILL marker, no preemption event
anywhere in the log. `gcloud describe` 404s on the instance — genuinely gone, not just stopped. Cause (OOM-class kill
vs. SPOT preemption) undetermined without VM-level forensics not available after the fact.

A manual relaunch (`cefi-okx-swap-2026-heavy-20260813-120003`, same scope) was confirmed genuinely running, but
**re-processed 2026-02-25 from scratch** rather than resuming at 2026-04-15 — the new VM has its own name and GCS
log/checkpoint path, with no mechanism to discover or read the dead VM's `PROGRESS.json`. Separately,
`MANIFEST_CONSOLIDATED_STALENESS_SEC=86400` means the manifest reader tolerates a same-day-stale consolidated index, so
the relaunch also doesn't see the first VM's already-captured shards via that path either.

**Cost**: not data-corrupting (re-fetching real data is idempotent), but real, avoidable waste — ~49 already-captured
days re-walked (real Tardis API calls + wall-clock) before reaching new territory.

## Todos

- [ ] [INFRA] P2. Give `launch-cefi-sharded-backfill.sh` (and any sibling launcher using the same per-VM-named
      `PROGRESS.json` pattern) a way for a manual/auto relaunch to discover and resume from the PRIOR VM's checkpoint
      for the same logical job (same venue/scope/date-range) — e.g. a stable job-id-keyed checkpoint path independent of
      the VM's own instance name, or an explicit `--resume-from-vm=<prior-vm-name>` flag that reads that VM's
      `PROGRESS.json` before starting. Mirrors the intent already proven for SPOT-preemption auto-relaunch
      (`spot-vms-for-backfill.md`'s resume-checkpoint contract) — this closes the gap for a MANUAL relaunch under a
      genuinely new name, which the auto-relaunch path may not hit the same way.
- [ ] [INFRA] P3. Investigate the silent-death root cause (OOM vs. preemption) — if reproducible, consider whether this
      launcher family's machine-type default needs a rightsizing check (`/vm-resource-rightsizing-check`) given the RSS
      trajectory observed (17.7GB→51GB in <4 min is a fast climb worth a closer look).
