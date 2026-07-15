---
doc_type: issue
title: cefi-binance-futures-2021-heavy SPOT VM RUNNING 9 days with zero output — no fire-and-forget violation
summary:
  VM `cefi-binance-futures-2021-heavy-20260703-105623` (created 2026-07-03T10:56Z, SPOT, asia-northeast1-c) has been
  RUNNING continuously for 9 days as of 2026-07-12. Serial console output stops dead at 2026-07-05T00:00:18Z (7+ days of
  silence) and no per_vm shard has ever been written to
  gs://market-data-tick-cefi-prd-central-element-323112/_index/per_vm/ for this VM. This is a stalled/zombie backfill VM
  blocking the BINANCE-FUTURES 2021 shard from ever completing, which keeps BINANCE-FUTURES af>0 in the cefi G4 gate
  (mvp_backfill_cefi_tick_v10_2026_06_27.md).
status: resolved
nature: record
asset_group: [cefi]
stage: [data]
repos: [deployment-service]
scope: [engineer, admin]
tags: [infra, spot-vm, zombie-vm, no-fire-and-forget, g4-gate, cefi]
related: [plans/archive/2026_07/mvp_backfill_cefi_tick_v10_2026_06_27.md]
created: 2026-07-12
parent_epic: cefi_master
priority: P1
source: [plans/archive/2026_07/mvp_backfill_cefi_tick_v10_2026_06_27.md G4 verification, slot-2 2026-07-12]
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: infra
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-12 (P1 + P2 items closed)
locked_by:
resolved_by: deployment-service@14a0787
---

# cefi-binance-futures-2021-heavy SPOT VM stalled 9 days — infra triage

## What I found

`gcloud compute instances describe cefi-binance-futures-2021-heavy-20260703-105623 --zone=asia-northeast1-c --project=central-element-323112`
reports STATUS=RUNNING, created 2026-07-03T03:57:28-07:00 (2026-07-03T10:57:28Z) — **9 days uptime** as of this check
(2026-07-12T03:30Z).

`gcloud compute instances get-serial-port-output` for this VM shows its LAST log line at **2026-07-05T00:00:18Z**
(systemd rsyslog SIGHUP) — **7+ days with zero serial output**. The buffer was not truncated (gcloud did not report a
`--start` offset needed to see "new" output beyond the full buffer, meaning this genuinely is the full history — nothing
has been logged since).

`gsutil ls gs://market-data-tick-cefi-prd-central-element-323112/_index/per_vm/*binance-futures-2021*` returns **zero
matches** — no per-VM manifest shard has EVER been written for this VM in its 9-day life. It has not merged into the
consolidated manifest either (this exact VM was flagged identically in the 2026-07-06T22:32Z G4 verification run in
`mvp_backfill_cefi_tick_v10_2026_06_27.md`, at which point it had already been running 3 days with no shard — it is now
6 days further along with the same zero-output symptom).

## Why it matters

This VM occupies a SPOT slot and (per the plan's "no fire-and-forget" HARD RULE) should have either completed, been
preempted, or been visibly failing loudly within hours — not silently running for 9 days producing nothing. It is the
last blocker keeping BINANCE-FUTURES/2021/heavy shard unresolved, which keeps `BINANCE-FUTURES` in the cefi Layer-2 af
set in the `mvp_backfill_cefi_tick_v10_2026_06_27.md` G4 gate. VM lifecycle triage (delete zombie / inspect via
`gcloud compute ssh` / check startup-script exit) is outside `data_engineering` craft scope per that plan's precedent
(2026-07-06 entry: "Infra-triage handoff — SPOT VM life-cycle is outside data_engineering craft scope").

## Recommended decision

1. `[INFRA]` P1. Terminate `cefi-binance-futures-2021-heavy-20260703-105623` (it is not making progress and SPOT
   preemption-safety means a clean relaunch is idempotent/safe) and relaunch the BINANCE-FUTURES 2021 heavy shard via
   `ONLY="BINANCE-FUTURES:2021:heavy" FORCE=1 MACHINE_TYPE_HEAVY=e2-highmem-16 bash scripts/vm/launch-cefi-sharded-backfill.sh`
   (per the plan's G3 relaunch recipe for OOM-killed/stalled heavy shards).
2. `[INFRA]` P2. Root-cause why this VM produced zero serial output for 7+ days without either completing or being
   SPOT-preempted (startup-script hang? network stall on Tardis fetch? OOM without kernel OOM-killer log?) — the VM's
   disk/logs should be inspected via serial console dump or `gcloud compute ssh` before termination if diagnosis is
   wanted, since termination destroys the evidence.

## Root cause (P2)

By the time this task picked up, item 1 had already terminated + deleted the old VM (`--delete-disks=all`), so live
serial-console / SSH forensics were no longer possible. The evidence trail survived anyway: the heartbeat daemon's
GCS-tee'd `run.log` uploads independently of the VM/disk, at
`gs://deployment-scripts-central-element-323112/vm-logs/cefi-binance-futures-2021-heavy-20260703-105623/run.log` (12.77
MiB, last-modified 2026-07-12T04:12:33Z — survived termination).

That log shows the REAL Tardis worker producing normal per-symbol `StreamingParquetWriter: uploaded ...` progress lines
every 10-30s (peak_rss ~22GB) for BINANCE-FUTURES/2021-07-01/book_snapshot_5, right up to **2026-07-04T15:14:33Z**
(`canonical shard binance-futures/zilusdt — 610286 rows`). After that timestamp there is **no further worker output at
all** — no next-symbol request line, no traceback, no OOM signal — for the remaining 7+ days until termination. Every
line after 15:14:33Z is a `PIPELINE_HEARTBEAT ... source=vm-life-emitter` marker, printed exactly once every 60s,
unbroken, all the way to 2026-07-12T04:12:21Z.

**Why the stall watchdog never fired**: `vm-exec-with-gcs-tee.sh`'s per-VM stall watchdog (`STALL_TIMEOUT_SEC=1800`)
kills the workload if `LOCAL_LOG` hasn't grown in 30 min — UNLESS the launcher sets `STALL_PROGRESS_REGEX`, in which
case the timer only resets on a genuine progress-marker line (see the wrapper's own 2026-06-19 SFI/gas-fees incident
comments — this is a previously-diagnosed failure class). `launch-cefi-sharded-backfill.sh` never set
`STALL_PROGRESS_REGEX` (unlike `launch-mdps-sharded-backfill.sh` / `launch-sfi-backfill-vm.sh` /
`launch-mtds-gas-fees-backfill-vm.sh`, which all do). Meanwhile `setup-data-pipeline-vm.sh` (BUG1b, 2026-06-22) wires a
`vm-life-emitter` loop (`while true; echo PIPELINE_HEARTBEAT; sleep 60`) into the **same** tee'd command whose output
feeds the **same** `LOCAL_LOG` the watchdog measures. Result: the heartbeat's own bytes reset the stall timer every
single poll, forever — the watchdog literally could not distinguish "worker alive and progressing" from "worker frozen,
only the liveness heartbeat is still ticking." The VM sat `RUNNING` for 9 days because nothing ever told it to stop.

The underlying freeze itself (why the Tardis worker produced zero further output — no request line even logged before it
— after finishing `zilusdt`) could not be further diagnosed: no traceback/exception/OOM message exists anywhere in the
surviving log, and the VM + boot disk (the only place a `py-spy`/proc-stack dump could have come from) were already
deleted by item 1 before this task could inspect them live — termination destroys the evidence, exactly as
recommendation 2 warned. Plausible mechanisms consistent with a silent, exception-free freeze immediately after a shard
finalize (blocking connection-pool checkout, hung auth-token refresh, deadlocked thread-pool join) are listed for
reference but unconfirmed.

**Fix shipped**: `launch-cefi-sharded-backfill.sh` now sets `STALL_PROGRESS_REGEX=uploaded` — the
`StreamingParquetWriter`/`StreamingShardFinalizer` "uploaded" marker fires on every per-shard GCS finalize across both
the heavy per-symbol-streaming path (`tardis_cefi_shards.py`) and the light/DERIBIT bulk chain-glob path
(`tardis_bulk_download.py`), verified present in both, so it's a safe universal per-shard progress marker for every
venue/group this launcher spawns. Confirmed via `DRY_RUN=1` smoke (heavy + light metadata both carry
`STALL_PROGRESS_REGEX=uploaded`). A future genuine hang on any CeFi sharded-backfill VM now trips the existing 30-min
watchdog (kill + `py-spy`/proc-stack dump + `DEPLOYMENT_FAILED` + self-delete) instead of running silently for days.

## Open actions

- [x] ✅ [INFRA] P1. Terminate + relaunch the BINANCE-FUTURES 2021 heavy shard (see recommendation 1). —
      deployment-service (VM ops, no code diff): terminated `cefi-binance-futures-2021-heavy-20260703-105623`
      (re-verified stalled at termination time — serial output still dead since 2026-07-05T00:00:18Z, still zero per_vm
      manifest shards); relaunched via
      `ONLY="BINANCE-FUTURES:2021:heavy" FORCE=1 MACHINE_TYPE_HEAVY=e2-highmem-16     bash scripts/vm/launch-cefi-sharded-backfill.sh`
      (exit 0, "All 1 VMs launched") → `cefi-binance-futures-2021-heavy-20260712-041346`, SPOT, e2-highmem-16, RUNNING,
      active serial output (gsutil scopes firing every ~60s) confirmed at T+~13min — 2026-07-12T04:27Z.
- [x] ✅ [INFRA] P2. Root-cause the zero-serial-output stall before/while terminating (see recommendation 2). —
      deployment-service@14a0787: root-caused via the surviving GCS run.log (see "Root cause (P2)" above) —
      `vm-life-emitter`'s 60s heartbeat defeated the size-based stall watchdog because the launcher never set
      `STALL_PROGRESS_REGEX`. Shipped `STALL_PROGRESS_REGEX=uploaded` in `launch-cefi-sharded-backfill.sh` so future
      hangs on any CeFi sharded-backfill venue/group trip the existing 30-min watchdog instead of running silently.
