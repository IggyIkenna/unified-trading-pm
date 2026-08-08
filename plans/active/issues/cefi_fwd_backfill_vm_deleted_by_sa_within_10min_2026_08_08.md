---
doc_type: issue
title: >-
  cefi-fwd-20260808-110409 (STANDARD VM, 62-day backfill) deleted by unified-trading-sa within 10-13 minutes of launch —
  same double-insert pattern as cefi-fwd-20260806-064507; GCS probe confirms 0 data written
summary: >-
  `cefi-fwd-20260808-110409` was launched by slot-14 (task defi_cefi_venue_chain_axis_contamination-011) at
  2026-08-08T11:04Z for a 62-day `derivative_ticker` backfill (2026-06-05→08-05, 6 venues). Audit logs show TWO
  `v1.compute.instances.insert` ops 8 seconds apart (11:04:15Z + 11:04:23Z) — same double-launch pattern as the prior
  `cefi-fwd-20260806-064507` incident (13s apart). Both were then DELETED (not stop'd) by
  `unified-trading-sa@central-element-323112.iam.gserviceaccount.com` at 11:14:58Z and 11:17:12Z — within 10-13 minutes
  of launch, before any meaningful data could be written. GCS probe (slot-17, 2026-08-08, `probe_cefi_perp_funding_raw_
  coverage.py`) confirms 0 objects across 2026-06-05→08-05 for BINANCE-FUTURES/BYBIT/OKX-SWAP/KRAKEN-FUTURES/BITGET-
  FUTURES; tiny pre-existing DERIBIT remnants (20-21/day from earlier DERIBIT-only backfill) and BITFINEX-FUTURES
  remnants (07-22/07-24) — none written by this VM. **Consequence**: -011 corpus recompute gate NOT met; -014 (GCS
  cleanup) correctly remains blocked; the backfill window 2026-06-05→08-05 is still absent for 5 of 6 CARRY_BASIS_PERP
  venues. This is the second consecutive cefi-fwd VM terminated before completing its window (prior:
  `cefi-fwd-20260806-065837`, terminated at 12/75 days). Root cause unknown — likely the Tardis concurrency guard or
  zombie watchdog reacting to the double-insert (two concurrent VMs). Operator + slot-14 action required.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [deployment-service]
scope: [engineer, admin]
tags: [cefi, vm, backfill, premature-deletion, tardis, concurrency-guard, data-pipeline, data-correctness]
related:
  [
    /plans/active/issues/cefi_fwd_vm_preempted_false_positive_standard_provisioning_2026_08_06.md,
    /plans/active/issues/defi_cefi_venue_chain_axis_contamination_2026_07_28.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
  ]
created: "2026-08-08"
author: slot-17
priority: P1
parent_epic: infrastructure_master
source: >-
  Operator flagged early STOPPING state. slot-17 confirmed via gcloud compute instances describe + gcloud logging read
  audit trail + GCS probe (probe_cefi_perp_funding_raw_coverage.py 2026-06-05→08-05).
assigned_vm: NA
execution_scope: local-only
drift_direction: fix
estimate_class: bug
estimate_baseline: 0.5
calibrated_ai_days: 0.4
assigned_role: infra
resolved_by:
locked_by:
---

# cefi-fwd-20260808-110409 deleted within 10-13 min — 0 data written

## Evidence

**Audit log** (`gcloud logging read protoPayload.resourceName:"cefi-fwd-20260808-110409"`, 2026-08-08):

| Timestamp                | Method                        | Actor                                                               |
| ------------------------ | ----------------------------- | ------------------------------------------------------------------- |
| 2026-08-08T11:04:15.980Z | `v1.compute.instances.insert` | `unified-trading-sa@central-element-323112.iam.gserviceaccount.com` |
| 2026-08-08T11:04:23.563Z | `v1.compute.instances.insert` | `unified-trading-sa@...`                                            |
| 2026-08-08T11:14:58.310Z | `v1.compute.instances.delete` | `unified-trading-sa@...`                                            |
| 2026-08-08T11:17:12.082Z | `v1.compute.instances.delete` | `unified-trading-sa@...`                                            |

**GCS probe** (`probe_cefi_perp_funding_raw_coverage.py --start 2026-06-05 --end 2026-08-05`, slot-17 2026-08-08):

- BINANCE-FUTURES: **0 objects** across entire window
- BYBIT: 18 total (06-22→06-27 remnants only, pre-existing)
- OKX-SWAP: 18 total (06-22→06-27 remnants only, pre-existing)
- KRAKEN-FUTURES: 12 total (06-22→06-27 remnants only, pre-existing)
- BITGET-FUTURES: **0 objects** across entire window
- DERIBIT: 20-21/day (from prior DERIBIT-only backfill, NOT from this VM)
- BITFINEX-FUTURES: 101 total (07-22=60, 07-24=41, remnants, NOT from this VM)

## Pattern analysis

This is the **third consecutive cefi-fwd VM terminated before completing its intended window**:

1. `cefi-fwd-20260806-065837`: terminated at 12/75 days (documented in cefi_tardis archive, operator flagged premature)
2. `cefi-fwd-20260808-110409`: terminated within 10-13 minutes, 0 data written

Both show a **double-insert** pattern (8s apart here; 13s apart for `cefi-fwd-20260806-064507`). The prior similar issue
(`cefi_fwd_vm_preempted_false_positive_standard_provisioning_2026_08_06.md`) was about `instances.stop` — here it's
`instances.delete`. Deletion is more aggressive and writes 0 data.

**Likely trigger**: Tardis concurrency guard or zombie watchdog detecting two concurrent `cefi-fwd-` VMs and deleting
both.

## Impact

- Task `-011` (corpus recompute prerequisite for `-014`) is blocked — raw input ABSENT for 5/6 venues
- Task `-014` (GCS contamination cleanup) correctly remains gated
- The P2 forward-cron venue gap fix (new todo in contamination plan) is also blocked on raw data
- The daily cefi corpus recompute cron fires at 07:00 UTC but will honest-skip the gap window

## Action items

- [ ] [OPERATOR] P0. **Diagnose root cause of double-insert + deletion pattern.** Check if the Tardis concurrency guard
      (`tardis-concurrency-guard.sh`) is triggering on double-launch and killing both instances. Check if the zombie
      watchdog (`exit_code_fleet_monitor`) has a `vm.delete` path that fires on concurrency violations. Confirm whether
      `cefi-fwd-20260806-065837`'s early termination at 12/75 days was also a deletion (check its audit log the same
      way).
- [ ] [INFRA] P1. **Re-launch the backfill** once root cause is understood. Pre-check: run
      `tardis-concurrency-guard.sh cefi-fwd` before launching to ensure no concurrent instances. Use a single-launch
      only (prevent double-insert). Expected runtime: ~18-24h for 62 days × 6 venues.
- [ ] [DATA] P1. **Re-run GCS probe to confirm coverage** after backfill VM terminates normally. Only then re-dispatch
      task `-011` (corpus recompute). Do NOT flip `-011` done on VM-STOPPED alone — measure GCS coverage.
