---
doc_type: issue
title: CeFi Track-2 coverage backfill VM preempted 2026-07-28, never recovered — finalize chain blocked
summary: >-
  Investigating the finalize-001 task (Reconcile CeFi Track-2 checkboxes) found the gating plan's own gate is NOT
  actually satisfied — only 3 of 5 todos in cefi_track2_coverage_backfill_checkpoints_2026_07_25.md are done. Root
  cause: the SPOT coverage-backfill VM (cefi-queue-heavy-binancefutu-x17-20260727-210013) was PREEMPTED 2026-07-28T10:51
  UTC after processing only ~55 of the ~2372 target days (~2.3%), wrote no PROGRESS.json checkpoint, and has sat dead
  for ~2 days with no auto-recovery or relaunch. This blocks the POST-BACKFILL gate todos (-004/-005) and, transitively,
  the entire finalize/archive chain.
status: open
nature: process
asset_group: [cefi]
stage: [data]
repos: [deployment-service, market-tick-data-service, unified-trading-pm]
scope: [engineer, admin]
tags: [cefi, backfill, vm-preemption, billing-waste, track-2, coverage, big-finding]
related:
  [
    /plans/active/cefi_track2_coverage_backfill_checkpoints_2026_07_25.md,
    /plans/active/cefi_track2_coverage_backfill_checkpoints_finalize_2026_07_25.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
  ]
created: 2026-07-30
parent_epic: cefi_master
priority: P1
source: ["finalize-001 (slot 10, review craft) reconciliation task, 2026-07-30"]
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-30
locked_since:
---

# CeFi Track-2 coverage backfill VM preempted, never recovered

## What I found

Dispatched `cefi_track2_coverage_backfill_checkpoints_finalize_2026_07_25.md`'s todo 1 ("Reconcile
`cefi_consolidated_closeout_2026_07_18.md`'s Track-2 checkboxes"), which is machine-gated
(`depends_on: [cefi_track2_coverage_backfill_checkpoints_2026_07_25]`, `gate_on_depends: true`) on ALL 5 todos of that
plan being `done`. Reading the gating plan's current state on disk: only 3 of 5 are `[x]` done (the resume-backfill
launch, the IS MID-BACKFILL checkpoint, the MTDS MID-BACKFILL checkpoint); the 2 POST-BACKFILL FINAL GATE todos (`-004`
`/data-pipeline-check-is`, `-005` `/data-pipeline-check-mtds`) are still `queued` in the live backlog (`-004` parked
`priority: 999` behind prerequisite `cefi-track2-backfill-vm-terminated=false`; `-005` `queued` at `priority: 20`). The
finalize task should not have been dispatchable under its own stated gate — filing this as a dispatch-gate discrepancy
for main/operator visibility, separate from the substantive finding below.

Investigated why POST-BACKFILL never ran — traced the backfill VM's actual state:

- `gcloud compute instances describe cefi-queue-heavy-binancefutu-x17-20260727-210013 --zone=asia-northeast1-c` → **not
  found** (no longer running).
- `gcloud compute operations list --filter="targetLink:cefi-queue-heavy-binancefutu-x17-20260727-210013"` shows:
  - `insert` DONE at `2026-07-27T14:30:12-07:00` (launch).
  - **`compute.instances.preempted` DONE at `2026-07-28T03:51:02-07:00`** (= `2026-07-28T10:51:02 UTC`).
- `gsutil cat gs://deployment-scripts-central-element-323112/vm-logs/cefi-queue-heavy-binancefutu-x17-20260727-210013/run.log`
  tail confirms the last lines are timestamped `2026-07-28 10:49:xx` (matches the preemption instant), mid-write on
  `date=2020-03-27` — i.e. only ~55 of the ~2372 days in the `2020-02-01..2026-07-28` target span (~2.3%) had been
  processed before the VM died. This matches the previously-measured throughput
  (`cefi_track2_coverage_backfill_checkpoints_2026_07_25.md`'s 2026-07-28 Progress Log: ≈3.25 days/hr).
- `gsutil cat .../PROGRESS.json` → **not found** (`No URLs matched`) — this launcher does not write the
  PROGRESS-checkpoint contract file (`/codex/05-infrastructure/vm-launcher-runbook.md`'s HARD RULE that preemption
  recovery must resume from measured progress, never replay `START_DATE`), so even a manual relaunch has no
  machine-readable resume point beyond the run.log's last `Processed date=` line.
- No replacement VM exists: `gcloud compute instances list --filter="name~cefi-queue"` returns empty. No auto-recovery
  has fired in the ~2 days since preemption (today is 2026-07-30).

Net effect: the backfill is genuinely ~2.3% complete, not "done", and has been silently dead for 2 days. The
`cefi-track2-backfill-vm-terminated` prerequisite (used to park `-004`) is still correctly `false` in spirit (the VM
never _completed_), but nothing is driving toward completion either.

## Why it matters

This blocks the entire gated close-out chain for CeFi Track 2: `-004`/`-005` (POST-BACKFILL final gate) →
`cefi_track2_coverage_backfill_checkpoints_finalize_2026_07_25.md` (checkbox reconciliation + archival) →
`cefi_consolidated_closeout_2026_07_18.md`'s Track 2 closure. Per the data-pipeline-correctness HARD RULE ("plans run to
actual completion, not smoke-test green") and the SPOT/backfill governance rule (idempotent shards must actually resume,
not silently stall), a 2-day-dead SPOT VM at 2.3% progress is exactly the preemption-without-auto-recovery class
`/vm-preemption-billing-waste-audit` exists to catch — this one evaded it because it's a one-off backfill launcher not
wired into the standing fleet monitor (per the VM-launcher-runbook's own "one-off VMs aren't wired into the fleet
monitor, check it yourself" caveat).

I did NOT flip any of the 5 Track-2 checkboxes in `cefi_consolidated_closeout_2026_07_18.md` for the 2 POST-BACKFILL
items — doing so would misrepresent a 2.3%-complete, dead backfill as finished. I DID flip the 3 that have genuine,
verifiable evidence (resume-backfill launch confirmed running at the time; both MID-BACKFILL checkpoints ran and
produced reports) — see the plan diff in the same commit as this issue doc.

## Recommended decision

- **A [RECOMMENDED]**: Relaunch the coverage backfill (SPOT, idempotent skip-if-fresh, N=1 Tardis cap via
  `tardis-concurrency-guard.sh`) to resume from where it died (`~date=2020-03-27` onward through the target span). Also
  fix the launcher to emit `PROGRESS.json` per the PROGRESS-checkpoint contract so a future preemption is resumable and
  visible without a manual run.log tail. Once it genuinely completes, re-run `-004`/`-005` and finish the finalize
  chain.
- **B**: Given the measured throughput (~3.25 days/hr against a ~2372-day span → ~30-day wall-clock ETA even
  uninterrupted), re-open the original "is a fresh accepted coverage % more valuable than a ~30-day, preemption-prone
  backfill" question to the operator before relaunching — the original 50.79%-acceptance archival's premise (a supposed
  350x throughput ceiling) was reversed autonomously on 2026-07-18 on the strength of a "~1-2 days of work at June
  rates" estimate that this preemption (and the prior park note) shows was significantly optimistic in practice.

## Todos

- [ ] [INFRA] P1. Relaunch the cefi coverage backfill VM (SPOT, idempotent skip-if-fresh, N=1 Tardis cap) to resume from
      the 2026-07-28 preemption point (~`date=2020-03-27`) through the `2020-02-01..2026-07-28` target span; confirm
      progress climbing on 2+ successive checks per the async-wait discipline. Repo: deployment-service.
- [ ] [INFRA] P2. Add `PROGRESS.json` checkpoint emission to the cefi coverage-backfill launcher
      (`scripts/vm/launch-cefi-sharded-backfill.sh` or its underlying pipeline script) per the PROGRESS-checkpoint
      contract, so a future preemption can auto-resume/be diagnosed without a manual run.log tail. Repo:
      deployment-service.
- [ ] [REVIEW] P1. Once the relaunched VM genuinely completes (measured exit, not a wall-clock guess), re-run
      `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md`'s `-004`/`-005` POST-BACKFILL gate todos, then resume
      `cefi_track2_coverage_backfill_checkpoints_finalize_2026_07_25.md`'s remaining 2 Track-2 checkboxes + coverage %.
      Repo: unified-trading-pm.

## Progress log

- 2026-07-30 (slot-10, review craft): Filed while working `finalize-001`. Confirmed via `gcloud compute operations list`
  that the backfill VM was preempted 2026-07-28T10:51 UTC at ~2.3% progress, with no PROGRESS.json and no relaunch
  since. Flipped the 3 substantiated Track-2 checkboxes in `cefi_consolidated_closeout_2026_07_18.md` (launch, IS-MID,
  MTDS-MID); left the 2 POST-BACKFILL checkboxes unflipped pending genuine completion. Posted `/blocked` from slot 10
  recommending the finalize task stay open until the relaunch + POST-BACKFILL gates genuinely pass.
