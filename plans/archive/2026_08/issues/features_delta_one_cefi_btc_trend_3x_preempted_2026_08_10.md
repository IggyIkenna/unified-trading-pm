---
doc_type: issue
title: features-service delta_one cefi BTC-trend backfill — 3× boot-stage SPOT preemption, P2.11.16 blocked
summary: >-
  The citadel P2.11.16 delta_one `returns` backfill for cefi/BTC (4 dates: 2026-04-22, 2026-05-01..03) was relaunched 3
  times on 2026-08-10 and ALL THREE VMs were preempted at boot (~3-5 min in, zero parquet/run.log/EXIT_STATUS written
  each time) on the same heavily-contended `asia-northeast1-c` zone (822 VMs running). Genuine
  `compute.instances.preempted` events confirmed each time via operations list. Root cause is zone/host SPOT capacity,
  not a code defect (bounded local preflight already passed 1/1 with the id-form fix chain live). Per
  spot-vms-for-backfill.md on-demand for backfill is "a bug, not a default" UNLESS the run genuinely cannot absorb
  preemption — this 4-date run cannot (nothing to resume, every relaunch pays full boot for zero work). Requesting
  operator ruling: approve `--on-demand` for this tiny bounded window, or park P2.11.16 for a less-contended launch
  window.
status: resolved
nature: process
asset_group: [cefi]
stage: [data]
repos: [deployment-service, features-service, unified-trading-pm]
scope: [engineer, admin]
tags: [cefi, features-service, backfill, vm-preemption, spot, operator-decision, delta-one, btctrend, big-finding]
related:
  [
    /plans/active/citadel_satellite_ao_dispatch_batch1_2026_08_08.md,
    /plans/archive/2026_08/issues/delta_one_cefi_lookback_instrument_id_form_mismatch_2026_08_09.md,
    /codex/05-infrastructure/spot-vms-for-backfill.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
  ]
created: 2026-08-10
parent_epic: batch_live_symmetry_master
priority: P1
source: ["citadel_satellite_ao_dispatch_batch1-004 (slot 30, data_engineering), P2.11.16, 2026-08-10"]
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-08-11
locked_by:
locked_since:
resolved_by: >-
  citadel_satellite_ao_dispatch_batch1-004 (slot 9, data_engineering, 2026-08-11) — the P2.11.16 corpus recompute was
  already EXECUTED by slot-20 on 2026-08-10 via the sibling blocker's P2 re-run todo
  (delta_one_cefi_lookback_instrument_id_form_mismatch_2026_08_09.md), on the host (run-bounded-analysis.sh, not a VM) —
  the `[OPERATOR]` on-demand ruling is MOOT. Verified live from GCS: btc_trailing_return_{1m,3m,6m,12m} +
  btc_realized_vol non-null in the returns corpus for 2026-05-01/02/03 (100% on 05-02/03), availability-index
  capture_status=captured on all 3 dates. No on-demand VM relaunch performed. This issue is an archive candidate (0 open
  todos).
context_scope:
  [
    /plans/active/citadel_satellite_ao_dispatch_batch1_2026_08_08.md,
    /plans/archive/2026_08/issues/delta_one_cefi_lookback_instrument_id_form_mismatch_2026_08_09.md,
    /codex/05-infrastructure/spot-vms-for-backfill.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    deployment-service/scripts/vm/launch-features-vm.sh,
  ]
---

> **🟢 ARCHIVED 2026-08-11 — RESOLVED** (status: resolved, 0 open todos, unlocked). The blocking condition cleared
> without an operator ruling: slot-20 executed the P2.11.16 recompute on 2026-08-10 via the sibling blocker's P2 re-run
> todo, on the host (run-bounded-analysis.sh) — no backfill VM and no `--on-demand` decision were ever needed. Live-GCS
> verification (slot 9, 2026-08-11) confirmed `btc_trailing_return_{1m,3m,6m,12m}` + `btc_realized_vol` non-null in the
> returns corpus for 2026-05-01/02/03 with availability-index `capture_status=captured`; P2.11.16 flipped in
> `citadel_satellite_ao_dispatch_batch1_2026_08_08.md`. Archived by task `citadel_satellite_ao_dispatch_batch1-004`.

# features-service delta_one cefi BTC-trend backfill — 3× boot-stage SPOT preemption

## What I found

Working `citadel_satellite_ao_dispatch_batch1_2026_08_08.md`'s P2.11.16 todo ("features-service: recompute the BTC trend
feature corpus so `btc_trailing_return_{1m,3m,6m,12m}` + `btc_realized_vol` actually exist in GCS"). Established the
recompute is genuinely needed (`returns` feature_group absent from the delta_one corpus for all paper-window dates; the
existing `volatility_realized` parquet lacks `btc_realized_vol`), the id-form fix chain
(`delta_one_cefi_lookback_instrument_id_form_mismatch_2026_08_09.md` →
`features-service@d2e32548/1cd9f819/0c70a43f/2ea0c8cb`) is LIVE (bounded preflight passed 1/1 with canonical
`BITGET-FUTURES:PERPETUAL:BTCUSDT`), and launched the backfill via
`launch-features-vm.sh --feature-family delta_one --asset-group CEFI --start-date 2026-04-22 --end-date 2026-05-03 --launch-mode full --env prod`
with `FEATURE_GROUP=returns`.

**THREE launches, THREE preemptions, all at boot, all on the same `asia-northeast1-c` zone:**

| Attempt | VM                                        | Insert (UTC) | `compute.instances.preempted` (PT) | Progress                                        |
| ------- | ----------------------------------------- | ------------ | ---------------------------------- | ----------------------------------------------- |
| 1       | `features-delta-one-cefi-20260810-140712` | 14:09Z       | 07:10:22                           | **ZERO** (no run.log/EXIT_STATUS/parquet)       |
| 2       | `features-delta-one-cefi-20260810-141704` | 14:17Z       | 07:21:28                           | **ZERO** (no run.log/EXIT_STATUS/parquet)       |
| 3       | `features-delta-one-cefi-20260810-142400` | 14:25Z       | 07:28:03                           | **ZERO** (only `TARBALL_PINS.json`; boot-stage) |

- All 3 confirmed GENUINE preemption via
  `gcloud compute operations list --filter="targetLink~features-delta-one-cefi-20260810"` → three separate
  `compute.instances.preempted` system events, statusMessage "Instance was preempted." Root cause closed per
  spot-vms-for-backfill.md §"Manual check-in on a SPOT VM" — no bug-hunting needed.
- Attempt 2 also hit an initial `asia-northeast1-c` `e2-standard-8` resource_availability STOCKOUT (retried 15s later →
  created), reinforcing that the zone is capacity-contended (measured: 822 VMs running on the host pool).
- Launcher `ZONE` is a HARD literal (`launch-features-vm.sh:233` `ZONE="asia-northeast1-c"`), no env override — a
  sibling-zone relaunch would require editing shared infra code, not a clean autonomous option.
- **None of the 3 VMs wrote `run.log`/`EXIT_STATUS`/any parquet** — there is NO measured progress to resume; each
  relaunch re-pays full boot + tarball pull + preemption odds for ZERO new work. This is the exact case where the SPOT
  cheap-resume assumption (60-91% cheaper because idempotent resume is cheap) **never engages**.

## Why it matters

P2.11.16's done-when ("delta_one feature corpus carries non-null `btc_trailing_return_{1m,3m,6m,12m}` +
`btc_realized_vol` for the paper-trading window, manifest-row check") is blocked on infra, not code. The zone is
capacity-saturated right now (3× boot preemption in 18 min). This also transitively holds the companion P2.11.20
(TSMOM_BTC_CTA capability wiring, shares the VM run per the plan) and the downstream
`citadel_paper_batch_live_reconciliation` paper-run signal check. Per the data-pipeline-correctness HARD RULE I did NOT
flip any checkbox — the corpus is genuinely absent.

The 4-date window (2026-04-22, 2026-05-01..03) is tiny; on-demand `e2-standard-8` for this bounded run is a small,
one-time, bounded cost (a few dollars for a sub-hour run) vs. the SSOT's blanket "on-demand is a bug" which assumes a
backfill that CAN cheaply absorb preemption. This run cannot.

## Recommended decision

- **A [RECOMMENDED]**: Operator approves a single `--on-demand` relaunch for this 4-date window (features launcher's
  `--on-demand` flag verified working — `launch-features-vm.sh:188` sets `ON_DEMAND=true` after init, NOT the cefi
  launcher's pre-2026-08-06 env-var bug). `e2-standard-8` on-demand for a sub-hour bounded run ≈ a few dollars. This
  matches the `cefi_track2_backfill_vm_preempted_no_recovery_2026_07_30.md` precedent where the operator ruled ON_DEMAND
  (option b) after repeated preemption. After completion: manifest-row check + flip P2.11.16/P2.11.20 + /done.
- **B**: Park P2.11.16/P2.11.20 for a less-contended launch window (zone contention is transient — it cleared on attempt
  2's 15s-retry stockout earlier today). No cost, but the paper-run signal check stays held indefinitely until a SPOT VM
  gets past boot.
- **C**: Retry SPOT a 4th time — rejected as a recommendation: 3 identical boot-stage failures = stable-condition
  signal, not flapping (per async-wait/poll discipline), and each relaunch is a fresh full-boot cost with zero-work
  odds.

## Todos

- [x] ✅ [OPERATOR] P1. **Ruling: approve `--on-demand` (option A) for the 4-date delta_one cefi `returns` backfill, or
      park P2.11.16/P2.11.20 (option B)** — 3× boot-stage SPOT preemption evidence above; launcher `--on-demand`
      verified functional. On approve: relaunch
      `FEATURE_GROUP=returns bash launch-features-vm.sh --feature-family delta_one --asset-group CEFI --start-date 2026-04-22 --end-date 2026-05-03 --launch-mode full --env prod --on-demand`,
      verify terminal state, manifest-row check, flip P2.11.16/P2.11.20, /done. Repo: deployment-service (launch) +
      unified-trading-pm (plan flip). ✅ CLOSED AS MOOT 2026-08-11 (slot 9, citadel_satellite_ao_dispatch_batch1-004):
      no operator ruling was needed — the P2.11.16 recompute was already EXECUTED by slot-20 on 2026-08-10 via the
      sibling blocker `delta_one_cefi_lookback_instrument_id_form_mismatch_2026_08_09.md`'s P2 re-run todo, on the host
      via `run-bounded-analysis.sh` (not a VM). Live-GCS verification this session: `returns` parquets for
      2026-05-01/02/03 carry `btc_trailing_return_{1m,3m,6m,12m}` + `btc_realized_vol` non-null (05-02/03 100% @15s),
      and the availability index shows `capture_status=captured` for `returns` + `volatility_realized` on all 3 dates
      (written 2026-08-10T23:14Z). 2026-04-22 honestly emission-suppressed (data sparsity: 229 candles < 12m's 252-bar
      lookback). P2.11.16 checkbox flipped in `citadel_satellite_ao_dispatch_batch1_2026_08_08.md`. No `--on-demand` VM
      was launched — the blocker this ruling was for is gone.

## Progress Log

- 2026-08-11 (slot 9, data_engineering, dispatched `citadel_satellite_ao_dispatch_batch1-004`): **RESOLVED — the blocker
  cleared without an operator ruling.** Re-investigating P2.11.16 found the corpus recompute was already EXECUTED by
  slot-20 on 2026-08-10 via the sibling blocker `delta_one_cefi_lookback_instrument_id_form_mismatch_2026_08_09.md`'s
  own P2 re-run todo (that doc now archived RESOLVED) — slot-20 ran `returns` + `volatility_realized` for cefi/BTC on
  the HOST (`run-bounded-analysis.sh`), so no backfill VM and no `--on-demand` ruling were ever needed (the slot-30
  escalation's 3× SPOT preemption was moot from the start). Independently verified live from GCS this session
  (features-service venv; `list_blobs` + pyarrow schema/null count + availability-index read):
  `btc_trailing_return_{1m,3m,6m,12m}` + `btc_realized_vol` are present + non-null in the `returns` corpus for
  2026-05-01/02/03 (05-02/03 100% @15s; 05-01 95.6–99.6% warmup), availability index `capture_status=captured` for
  `returns` + `volatility_realized` on all 3 dates (written 2026-08-10T23:14Z); 2026-04-22 honestly emission-suppressed
  (229 candles < 12m's 252-bar lookback — data sparsity, consistent with slot-7/slot-20). P2.11.16 flipped in the batch
  plan; this `[OPERATOR]` todo closed as moot; doc set `status: resolved` — archive candidate (0 open todos).

- 2026-08-10 (slot 30, data_engineering, dispatched `citadel_satellite_ao_dispatch_batch1-004`): Established P2.11.16
  need (returns corpus absent; volatility_realized lacks btc_realized_vol), confirmed fix chain live (preflight 1/1),
  launched the backfill. Attempts 1+2 preempted at boot. Attempt 3 (`features-delta-one-cefi-20260810-142400`) launched
  14:25Z, confirmed RUNNING, watcher armed; on watcher fire confirmed `compute.instances.preempted` DONE 07:28:03 PT —
  **3rd consecutive boot-stage preemption, zero progress**. All 3 preemptions verified genuine via operations list. Per
  the plan's committed note ("If attempt 3 also preempts at boot, escalate: document the 3×-preemption in an issue doc +
  request operator ruling on --on-demand"), filed this issue doc with the `[OPERATOR]` decision todo. P2.11.16 +
  P2.11.20 checkboxes left `- [ ]` (corpus genuinely absent — no false progress). Full per-attempt evidence in the
  plan's own Progress Log (committed `ca962b7e17`).
