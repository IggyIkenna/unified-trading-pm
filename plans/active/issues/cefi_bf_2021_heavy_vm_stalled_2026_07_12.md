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
status: open
nature: record
asset_group: [cefi]
stage: [data]
repos: [deployment-service]
scope: [engineer, admin]
tags: [infra, spot-vm, zombie-vm, no-fire-and-forget, g4-gate, cefi]
related: [plans/active/mvp_backfill_cefi_tick_v10_2026_06_27.md]
created: 2026-07-12
parent_epic: cefi_master
priority: P1
source: [plans/active/mvp_backfill_cefi_tick_v10_2026_06_27.md G4 verification, slot-2 2026-07-12]
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: infra
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-12 (P1 item closed)
locked_by:
resolved_by:
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

## Open actions

- [x] ✅ [INFRA] P1. Terminate + relaunch the BINANCE-FUTURES 2021 heavy shard (see recommendation 1). —
      deployment-service (VM ops, no code diff): terminated `cefi-binance-futures-2021-heavy-20260703-105623`
      (re-verified stalled at termination time — serial output still dead since 2026-07-05T00:00:18Z, still zero per_vm
      manifest shards); relaunched via
      `ONLY="BINANCE-FUTURES:2021:heavy" FORCE=1 MACHINE_TYPE_HEAVY=e2-highmem-16     bash scripts/vm/launch-cefi-sharded-backfill.sh`
      (exit 0, "All 1 VMs launched") → `cefi-binance-futures-2021-heavy-20260712-041346`, SPOT, e2-highmem-16, RUNNING,
      active serial output (gsutil scopes firing every ~60s) confirmed at T+~13min — 2026-07-12T04:27Z.
- [ ] [INFRA] P2. Root-cause the zero-serial-output stall before/while terminating (see recommendation 2).
