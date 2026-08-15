---
doc_type: issue
title:
  "A VM relaunched under a NEW name cannot resume from a prior VM's PROGRESS.json checkpoint — re-walks from START_DATE"
summary: >-
  Distinct from cefi_track2_backfill_vm_preempted_no_recovery_2026_07_30.md (which covers PROGRESS.json not being
  WRITTEN at all for a launcher family, now fixed via deployment-service@28b7dce) — this is about a launcher that DOES
  write PROGRESS.json correctly, but a manual relaunch after the original VM dies (**CORRECTED 2026-08-14: confirmed
  ordinary SPOT preemption, not an OOM-class kill — see below**) creates a NEW VM with a new name/log path, which has no
  mechanism to read the DEAD VM's checkpoint file. Net effect: the relaunch silently re-walks from the original
  START_DATE instead of resuming from the last completed date, wasting real API calls/wall-clock (idempotent re-fetch,
  not data-corrupting, but a real cost this workspace's own resume-checkpoint contract is supposed to prevent).
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
  (no exit_code/traceback/preemption marker in the log; confirmed 2026-08-14 as ordinary SPOT preemption via full
  resource-sample history, not OOM), manual relaunch under a new VM name confirmed re-walking already-captured dates"
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

## CORRECTED 2026-08-14 — death cause resolved: ordinary SPOT preemption, not OOM

> **CORRECTION.** The original finding below characterized the RSS trajectory right before death (17.7GB→51GB in <4min)
> as an unexplained runaway. That read only looked at the LAST few `RESOURCE_SAMPLE` lines before the log went silent.
> Pulling the FULL resource-sample history for both OKX-SWAP VMs (449 + 1,436 samples) and, separately, both
> BINANCE-FUTURES cohortA-heavy VMs from the very next backfill run (149 + 804 samples — ~2,838 samples total across 4
> independent VM deaths) shows this is a clean, repeating, BOUNDED sawtooth: climbs from ~2-6GB to ~55-68GB over 5-7
> minutes (one calendar day's fan-out for this shard's instrument set), then drops back to ~2-7GB once that day writes
> and releases — never a monotonic runaway. Every one of the 4 deaths happened at essentially random points in that
> cycle, including one at only 28.7% of the machine's 128GB ceiling — nowhere near a peak, let alone the ceiling. The
> launcher's own wrapper (`setup-data-pipeline-vm.sh`'s `CEFI_CHUNK_SCRIPT`) explicitly detects a child OOM-kill (exit
> 137 → logs `CHUNK_FAILED: ... reason=OOM_KILLED`) and that line appears **zero times** across all 4 run.logs. The logs
> just stop instantly with no wrapper-level message either — consistent with the WHOLE VM (wrapper included)
> disappearing at once, i.e. genuine SPOT reclaim, not the Python process being individually OOM-killed while the
> wrapper survives to log it. **Verdict: this launcher's "heavy" tier has no memory leak and no OOM risk at its current
> scope** — the silent deaths are ordinary, expected SPOT preemption. Answers the P3 todo below.

## What was found (2026-08-12)

`cefi-okx-swap-2026-heavy-20260812-225944` (a `launch-cefi-sharded-backfill.sh` VM) correctly processed 2026-02-25
through 2026-04-14 (`PROGRESS.json: last_completed_date=2026-04-14, monotonic=true`), each day logging real captured
trades+book_snapshot_5 rows. It then died silently while processing 2026-04-19 — the log stops entirely: no
`exit_code=`, no traceback, no SIGTERM/SIGKILL marker, no preemption event anywhere in the log. `gcloud describe` 404s
on the instance — genuinely gone, not just stopped. **Cause now confirmed** (see correction above): ordinary SPOT
preemption, not an OOM-class kill.

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
- [x] ✅ [INFRA] P3. **ANSWERED 2026-08-14 — confirmed SPOT preemption, not OOM; rightsizing checked, no action
      needed.** See correction above for the full evidence (4 VM deaths, ~2,838 combined RESOURCE_SAMPLE lines, 0
      OOM_KILLED lines). Separately ran `/vm-resource-rightsizing-check` on the current `e2-highmem-16` default: CPU is
      genuinely underutilized (~100% of 16 vCPU ≈ 6-7%, matching the 2026-08-10 tradfi audit's signature) but this is
      NOT a fixable over-provisioning case — GCP hard-caps every custom machine family (e2, n2) at 64GB for an 8-vCPU
      shape (`gcloud compute machine-types describe` confirms this directly), and this shard's peak (~55-68GB) already
      exceeds that, so 16 vCPU is the actual GCP-enforced MINIMUM to hold the current working set — there is no smaller
      shape that keeps the same RAM. The real idle-capacity lever is `--batch-date-concurrency` (parallelizing dates
      within a chunk, default OFF) — NOT recommended yet: it would run multiple currently-uncapped ~60GB per-date peaks
      concurrently, and the shared `ParallelPerSymbolRunner` path this launcher uses has a confirmed, still-open gap
      (`mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md`'s P2: `max_in_flight_bytes` is permanently `None`, a
      no-op) — enabling concurrency before that lands would knowingly reproduce the OOM history already documented there
      for the sibling sports/odds_api launcher. Fix that P2 first, then revisit concurrency as a throughput win.

## Progress Log

- 2026-08-12 — Filed. RSS-trajectory tail-read led to an OOM-vs-preemption open question (P3).
- 2026-08-14 — Investigating a live BINANCE-FUTURES cohortA-heavy stall (separate `/vm-preemption-billing-waste-audit`
  - `/vm-resource-rightsizing-check` pass, prompted by an operator ask to check VM memory/CPU usage properly rather than
    "just advocate more resources") pulled the FULL resource-sample history for that run too, which contradicted my own
    live read moments earlier in the same session (I'd initially, wrongly, pattern-matched a tail-only snapshot to this
    doc's OKX-SWAP finding). Re-checked THIS doc's original OKX-SWAP evidence the same way and found the identical
    tail-only mistake here. Corrected both P3 and the summary/body above; no code or data was affected by the wrong
    framing (it never drove any action beyond this doc's own open todo). Also closed the rightsizing half of the P3 todo
    the same session — see correction above for the full reasoning on why the CPU idleness isn't independently fixable.
