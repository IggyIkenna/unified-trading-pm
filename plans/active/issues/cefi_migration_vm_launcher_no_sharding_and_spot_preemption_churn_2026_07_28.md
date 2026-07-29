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
status: blocked
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
resolved_by: "deployment-service@bf51669 (sharding), deployment-service@3da9ffa (preemption-recovery root-cause fix)"
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

- [x] ✅ [SCRIPT] P2. Sharding: `--shards N` / `SHARD_COUNT` added to `launch-cefi-funding-timestamp-fix-vm.sh` (new
      shared lib `scripts/vm/_cefi-fts-launcher-lib.sh`, `cefi_fts_split_date_shards`) — N evenly-spaced contiguous date
      sub-ranges, last shard absorbs the remainder, bounded at `MAX_SHARDS=8` (GCE 63-char instance-name limit + a
      fat-finger guard), N=1 default path byte-identical to pre-fix behavior (regression-verified), per-shard
      `lc_write_launch_params` records THAT shard's own start/end (not the original full range) so a preemption-relaunch
      resumes the correct sub-range. Verified via dry-run smoke test (10-day window into 3 shards: 3/3/4 days,
      exhaustive, no gap/overlap) + the repo's `test_vm_launcher_scripts.py` suite. **DONE 2026-07-29 —
      `deployment-service@bf51669`.**
- [x] ✅ [SCRIPT] P2. Preemption recovery: root-caused via real investigation, NOT the general sweep-script fallback
      this doc's own text proposed. The existing fleet-monitor mechanism (`exit_code_fleet_monitor.py` →
      `DP_VM_PREEMPTED` → `RelaunchPreemptedVm`) DOES already cover the `-fts-` prefix (registered in
      `vm_prefix_registry.py`, contradicting this doc's original "not wired into the fleet monitor" framing) and IS on a
      real `*/5` Cloud Scheduler cadence (`uts-prod-dp-exit-code-monitor-cron`) — but real Cloud Run execution logs
      (`gcloud logging read`) show it has been hitting its 300s Cloud Run task timeout on EVERY SINGLE execution for at
      least 2 days (`2026-07-27T05:00` onward — the fleet outgrew the timeout that was last tuned for memory, not
      wall-clock, on 2026-06-23), so `DP_VM_PREEMPTED` has never fired even once in that window (0 matching log lines in
      3 days) — a genuinely BROKEN safety net, not merely a scope gap. Fix: `timeout_seconds` 300→900 in
      `terraform/gcp/data_pipeline_fleet_monitor_scheduler.tf`. **Code shipped 2026-07-29 —
      `deployment-service@3da9ffa`; the actual `terraform apply` to production could NOT be completed in-session** —
      this repo's terraform has no CI-driven apply pipeline and requires `-var project_id/environment/bucket_prefix`
      values not present anywhere in the checkout (no `.tfvars`, no discoverable apply workflow) — guessing them against
      live alerting infra with no plan-review safety net was judged the wrong risk to take blind. **Needs a human (or
      whoever owns the sanctioned apply process) to run `terraform apply` for this one resource** — until then the code
      fix is correct but inert; preempted one-off VMs still need manual relaunch (done throughout this session from
      measured `PROGRESS.json`, never replaying `START_DATE`).

## Progress Log

- 2026-07-28 (autonomous session): found while scaling the CeFi funding_timestamp fix to its full corpus. Worked around
  both gaps manually this session (computed 6 per-venue midpoint shards; independently discovered and manually
  relaunched 5 preempted VMs from their measured `PROGRESS.json` checkpoints, never replaying original `START_DATE`).
  Filing as a real, scoped follow-up rather than building the general fix under this session's time budget — the
  workaround is proven safe (idempotency-guard-backed), just not automated.
- 2026-07-29 (autonomous session, resumed after a session-limit crash mid-workflow): built and shipped both fixes.
  Sharding matched the doc's own recommendation exactly. Preemption recovery required real investigation rather than the
  assumed sweep-script build — the doc's premise ("not wired into the fleet monitor") turned out to be incomplete: the
  mechanism exists and is correctly registered, it is just chronically timing out. Fixing the ACTUAL root cause (a
  3x-too-small Cloud Run timeout) is a smaller, more correct fix than building a parallel sweep script would have been,
  and it fixes recovery for the WHOLE one-off-migration-VM population once deployed, not just this venue family. Status
  `resolved` reflects the CODE being complete and correct; the doc stays discoverable via this Progress Log entry until
  the terraform apply is confirmed live (verify via: no more `"Terminating task"` timeout log lines for
  `uts-prod-dp-exit-code-monitor`, and a real `DP_VM_PREEMPTED` log line appearing within 15 min of a genuine
  preemption).
