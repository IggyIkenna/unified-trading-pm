---
doc_type: issue
title:
  The CeFi funding-timestamp-fix VM launcher (and its migration-VM template ancestor) has no date-range sharding
  support, so a large single-venue backfill runs single-threaded for tens of hours on one VM — and asia-northeast1-c
  SPOT capacity churned hard during this session's run (5 of 11 launched VMs preempted within ~2 hours), which one-off
  migration VMs have no automatic recovery from
summary: >-
  While scaling the bulk-Tardis `derivative_ticker.funding_timestamp` reprocessing fix
  (`perp_funding_data_semantics_and_cadence_2026_06_16.md`) to its full historical corpus, two related operational gaps
  surfaced. (1) The launcher takes one `<VENUE> <START_DATE> <END_DATE>` triple per invocation and the underlying script
  is explicitly single-threaded (GCS-I/O-bound, not CPU-bound, per its own docstring) — for BINANCE-FUTURES's ~1706-day
  remaining range at the measured single-VM rate (~1.2 days/minute), that is ~24 hours on one VM with no built-in way to
  split the date range across concurrent VMs; the operator only got parallelism this session by manually computing
  per-venue midpoint dates and launching a second `<VENUE> <midpoint> <end>` VM by hand. (2) Manually launching those
  shards, plus a follow-up EXTENDED-STARKNET launch, surfaced that `asia-northeast1-c` SPOT capacity churned hard in a
  short window: 5 of the 11 VMs launched in this session's ~2-hour window were preempted (`compute.instances.preempted`
  + auto-delete via `--instance-termination-action=DELETE`), and CLAUDE.md's own documented position is that "one-off
  migration VMs aren't wired into the fleet monitor" — so nothing auto-relaunches them; the operator had to notice the
  gap in `gcloud compute instances list`, check each preempted VM's last `PROGRESS.json` checkpoint, and manually
  relaunch each one resuming from measured progress (never replaying the original `START_DATE`, per the existing HARD
  RULE).
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-service, market-tick-data-service]
scope: [engineer]
tags: [vm-launcher, sharding, spot-preemption, backfill, cefi, parallelization]
related:
  [
    /plans/active/issues/perp_funding_data_semantics_and_cadence_2026_06_16.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /codex/05-infrastructure/spot-vms-for-backfill.md,
  ]
created: 2026-07-28
parent_epic: infrastructure_master
priority: P2
source:
  [
    "autonomous session, CeFi perp-funding-timestamp VM scale-out, 2026-07-28",
    "gcloud compute operations list — 5 confirmed compute.instances.preempted events within ~2h",
  ]
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: local-only
drift_direction: advance-code
depends_on: []
---

# CeFi migration VM launcher: no date-range sharding + no auto-recovery for preempted one-off VMs

## What I found

### 1. No sharding — single-VM backfills scale to "tens of hours" with no built-in parallelism

`deployment-service/scripts/vm/launch-cefi-funding-timestamp-fix-vm.sh <VENUE> <START_DATE> <END_DATE>` (and its
template ancestor `launch-cefi-migration-vm.sh`) launches exactly ONE VM per invocation, and the underlying
`market-tick-data-service/scripts/one_offs/reprocess_bulk_tardis_derivative_ticker_funding_timestamp_2026_07_28.py` is
deliberately single-threaded (its own docstring: "this workload is GCS-I/O-bound, not CPU-bound"). Measured real
throughput on a live VM: ~1.2 days of historical data processed per minute. For the largest remaining venue
(BINANCE-FUTURES, ~1706 days remaining at the time of measurement), that projects to **~24 hours on one VM** — well past
a single operator session, let alone the `vm-launcher-runbook.md` "few-hour parallelization threshold" this class of job
is supposed to stay under.

**What exists today that COULD support sharding, but isn't wired up**: the launcher already accepts an arbitrary
`START_DATE`/`END_DATE` pair, and the reprocessing script's own design doc confirms independent GCS prefixes per venue
are "safe to launch concurrently" — so date-range sharding of ONE venue across MULTIPLE VMs is mechanically safe (the
script's own idempotency guard, `skipped_next_funding_timestamp_already_present`, makes any accidental date overlap
between shards a fast no-op, not a correctness risk). Nothing in the launcher computes or exposes this split, though —
the operator did it by hand this session (fetch each running VM's `PROGRESS.json`, compute a midpoint date between
current progress and the venue's end date, launch a second VM covering `<midpoint> <end>`).

### 2. One-off migration VMs have zero automatic preemption recovery

Confirmed via `gcloud compute operations list --filter="operationType=compute.instances.preempted"`: of the 11 VMs
launched in this session's ~2-hour window (6 original single-shard + a manually-added shard per venue + one
Extended-Starknet VM), **5 were preempted and auto-deleted** (`--instance-termination-action=DELETE` means a preempted
SPOT VM vanishes, it doesn't sit `TERMINATED` for inspection). This matches the documented, accepted tradeoff of
defaulting backfill VMs to SPOT (60-91% cheaper) — the gap is CLAUDE.md's own stated position that "one-off migration
VMs aren't wired into the fleet monitor" (unlike the always-on fleet, which presumably has some relaunch-on-preemption
automation). The PROGRESS-checkpoint contract (`vm-logs/{vm}/PROGRESS.json`, monotonic-gated) correctly SURVIVES the
VM's deletion (it's a GCS object, not VM-local state) — so recovery from measured progress IS possible, it's just
entirely manual today: notice the VM is gone (nothing pages for it), fetch its last `PROGRESS.json`, and relaunch with
that date as the new `START_DATE`.

## Why it matters

Every large one-off CeFi/DeFi/TradFi migration or backfill VM launched via this launcher family inherits both gaps —
this is not specific to the funding_timestamp fix. As the workspace's VM-launched migration volume grows, manual
midpoint-splitting and manual preempt-and-relaunch babysitting doesn't scale to an unattended/autonomous operator
session the way the rest of this workspace's automation does.

## Recommended fix (not built here — real scope, not a drive-by)

1. **Sharding**: add a `SHARD_COUNT` (or explicit `--shards N`) option to the launcher family that computes N
   evenly-spaced date sub-ranges from a single `<VENUE> <START> <END>` invocation and launches N VMs, one per shard,
   each with its own `VM_NAME` suffix — mirroring what was done by hand this session. Bound it (e.g. don't silently
   launch 50 VMs from a fat-fingered `--shards 50`).
2. **Preemption recovery for one-off migration VMs**: either (a) extend the existing fleet-monitor relaunch mechanism
   (`RelaunchPreemptedVm`) to cover the `-fts-`/`-fts-ext-` (and sibling one-off migration) VM prefixes now that they're
   correctly registered in `vm_prefix_registry.py`/`launcher_registry.py`, so a preempted one-off VM auto-relaunches
   from its last `PROGRESS.json` the same way a fleet VM would; or (b) a lightweight standalone sweep script (cron or
   manual) that lists `RUNNING`-expected-but-missing one-off migration VMs by name pattern, reads their last checkpoint,
   and relaunches — cheaper to build than (a) if fleet-monitor integration is a bigger lift than it looks.

## Progress Log

- 2026-07-28 (autonomous session): found while scaling the CeFi funding_timestamp fix to its full corpus. Worked around
  both gaps manually this session (computed 6 per-venue midpoint shards; independently discovered and manually
  relaunched 5 preempted VMs from their measured `PROGRESS.json` checkpoints, never replaying original `START_DATE`).
  Filing as a real, scoped follow-up rather than building the general fix under this session's time budget — the
  workaround is proven safe (idempotency-guard-backed), just not automated.
