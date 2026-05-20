---
title:
  "DeFi 46-day upstream backfill launch — PAUSED at preflight (launcher-script blocker; operator decision required)"
created: 2026-05-20
author: ikenna-slot-1 (operator authorization 2026-05-20 "we should do this now, defi needs working")
source:
  - "plans/active/issues/defi_upstream_46day_full_backfill_2026_05_16.md (parent — operator approval granted 2026-05-20)"
  - "deployment-service/scripts/vm/launch-defi-backfill-vm.sh (instruments DeFi launcher — hardcoded END=2026-04-04)"
  - "deployment-service/scripts/vm/launch-instruments-backfill-vm.sh (multi-asset launcher — hardcoded DeFi END=2026-02-28)"
locked_by: live-defi-rollout
locked_since: 2026-05-20
severity:
  P1 — paused preflight; no VMs launched. Resumes once operator picks instruments-launcher path (A/B/C below).
launched_at: 2026-05-20  # task initiated; VMs NOT actually created — see PAUSE below
---

## What I found

Preflight inspection of the launcher scripts revealed that the instruments-service DeFi half of the 46-day backfill
**cannot be launched without modifying launcher code**. The MTDS DeFi half is launchable as-is via `--start/--end`
flags, but launching MTDS without instruments-service first will produce shards with `EXPECTED_DEPENDENCY_NOT_AVAILABLE`
emissions (instruments-service is the upstream universe enumerator). Per writegate dependency-chain semantics the
MTDS half is wasted compute without the instruments half landing first.

Per CLAUDE.md HARD RULE "Blockers to flag (pause if hit) — Launcher script doesn't accept the date range cleanly" I
have stopped at preflight and not launched any VMs.

### Launcher state matrix (DeFi-relevant only)

| Launcher                                      | Accepts `--start/--end`? | Hardcoded END         | Action needed                        |
| --------------------------------------------- | ------------------------ | --------------------- | ------------------------------------ |
| `launch-instruments-backfill-vm.sh`           | NO                       | 2026-02-28 (DeFi VM)  | **EDIT or workaround required**       |
| `launch-defi-backfill-vm.sh` (instr-targeted) | NO                       | 2026-04-04            | **EDIT or workaround required**       |
| `launch-mtds-dex-pools-backfill-vm.sh`        | YES (`--start/--end`)    | n/a (default = today) | OK — launches with override          |
| `launch-mtds-eigenlayer-rewards-backfill-vm.sh` | YES                    | n/a                   | OK                                   |
| `launch-mtds-liquidations-backfill-vm.sh`     | YES                      | n/a                   | OK                                   |
| `launch-mtds-perp-funding-backfill-vm.sh`     | YES                      | n/a                   | OK                                   |
| `launch-mtds-solana-drift-backfill-vm.sh`     | YES                      | n/a                   | OK                                   |
| `launch-mtds-gas-fees-backfill-vm.sh`         | YES (positional)         | n/a                   | OK                                   |
| `launch-mtds-lending-indices-backfill-vm.sh`  | YES (positional)         | n/a                   | OK                                   |
| `launch-mtds-lst-rates-backfill-vm.sh`        | YES (positional)         | n/a                   | OK                                   |
| `launch-mtds-pyth-archive-backfill-vm.sh`     | YES (positional)         | n/a (2022-11..2023-09 default) | OK with override            |
| `launch-mtds-pyth-lst-backfill-vm.sh`         | YES (positional)         | n/a                   | OK                                   |
| `launch-mtds-vault-share-price-backfill-vm.sh` | YES (positional)        | n/a                   | OK                                   |
| `launch-mtds-solana-gas-backfill-vm.sh`       | YES                      | n/a                   | **SKIP — VM `mtds-gas-fees-solana` already RUNNING since 2026-05-19 covering 2021-01-01..2026-05-19** |

### Currently-running DeFi backfill VMs (preflight inventory 2026-05-20 07:55Z)

```
mtds-gas-fees-solana             RUNNING   created 2026-05-19T11:41:56-07:00  range 2021-01-01..2026-05-19 (covers window)
mtds-backfill-odds-1             RUNNING   created 2026-05-19T11:42:10-07:00  (prediction/sports — not DeFi)
mtds-dex-pools-backfill          TERMINATED created 2026-05-19T11:41:49-07:00 (safe to relaunch)
mtds-eigenlayer-rewards-backfill TERMINATED ... (safe to relaunch)
mtds-liquidations-backfill       TERMINATED ... (safe to relaunch)
mtds-perp-funding-backfill       TERMINATED 2026-05-16T04:52:27-07:00 (safe to relaunch)
mtds-solana-drift-backfill       TERMINATED 2026-05-19T12:35:53-07:00 (safe to relaunch)
```

No VM-name collisions for the proposed MTDS relaunches (each launcher uses a fixed name and the prior VM is TERMINATED).

## Why it matters

Operator said "we should do this now, defi needs working" at 2026-05-20 expecting the backfill to launch. Surfacing
the launcher-edit blocker explicitly so the operator picks a path rather than slot-1 silently editing launcher scripts
and triggering downstream prek-hook / commit-flip discipline overhead during an active dispatch.

## Operator decision required

**Pick ONE**:

### (A) Edit both instruments-service launchers to accept `--start/--end` (RECOMMENDED)

- Edit `launch-defi-backfill-vm.sh` to accept `--start <YYYY-MM-DD>` and `--end <YYYY-MM-DD>` (matching MTDS launcher
  convention).
- Edit `launch-instruments-backfill-vm.sh` to (a) accept `--asset-group defi` filter, OR (b) accept `--start/--end`
  override for the DeFi VM only.
- Launch `instr-backfill-defi-targeted-46d` with `--start 2026-04-01 --end 2026-05-16`.
- Time: ~30 min launcher edit + 10 min VM bootstrap + ~2-4h backfill wallclock.
- Commit + flip discipline applies (deployment-service@<sha> + plan-flip in same agent turn).

### (B) One-shot inline override (bypass launcher edit)

- Slot 1 writes a one-off `launch-defi-46day-backfill.sh` (copy of `launch-defi-backfill-vm.sh` with `START_DATE=2026-04-01`
  + `END_DATE=2026-05-16` hardcoded + unique VM name `instr-backfill-defi-46d-20260520`).
- Lives at `deployment-service/scripts/vm/launch-defi-46day-backfill.sh` (one-off, kept until backfill validated).
- Time: ~10 min script copy + launch.
- Risk: workspace drift — launcher SSOT now has 3 DeFi-instrument launchers.

### (C) Defer instruments-service half; launch MTDS-only half NOW

- Skip instruments-service backfill (accept that DeFi raw_tick_data shards will mostly `record_empty(EXPECTED_DEPENDENCY_NOT_AVAILABLE)`).
- Launch 12 MTDS DeFi backfill VMs with `--start 2026-04-01 --end 2026-05-16`.
- Useful **only if** the MTDS handlers can synthesize a universe from on-chain enumeration without consulting
  instruments-service availability — VERIFY before launching.
- NOT RECOMMENDED — wasted compute risk is high without confirming MTDS handler universe-resolution path.

### (D) Different window

- E.g. 14-day backfill (2026-05-02..2026-05-16) per parent-issue option (C). Smaller scope, faster turnaround.
- Still requires instruments-service launcher fix per (A) or (B).

## Recommended decision

**(A) — edit both launchers properly + relaunch full 46-day instruments + MTDS DeFi fleet.** Single clean
modification, durable for future backfill operations, aligns with launcher SSOT convention.

## VM plan (for execution once operator picks path)

If (A) or (B) approved, slot 1 will launch in this order:

1. **Stage 1 — instruments-service DeFi** (must land first):
   - VM `instr-backfill-defi-46d-20260520` (asia-northeast1-c, e2-standard-4)
   - Range 2026-04-01..2026-05-16, all 7 DeFi venues (CURVE-AVALANCHE, CURVE-OPTIMISM, BALANCER-ETHEREUM,
     UNISWAPV3-ETHEREUM, UNISWAPV3-POLYGON, RAYDIUM-SOLANA, UNISWAPV4-ETHEREUM).
   - Expected duration: 2-4h wallclock.
   - Output: `gs://instruments-store-defi-central-element-323112/instrument_availability/by_date/day=2026-04-01..day=2026-05-16/`.
   - T+10min verification: `gcloud compute instances describe instr-backfill-defi-46d-20260520 --zone=asia-northeast1-c --format='value(status)'` = RUNNING + log file present in GCS staging.

2. **Stage 2 — MTDS DeFi raw_tick_data fleet** (depends on Stage 1 mostly-complete; can start ~1h into Stage 1):
   - 11 VMs in parallel (skip solana-gas — already running):
     - `mtds-dex-pools-backfill` (--start 2026-04-01 --end 2026-05-16)
     - `mtds-eigenlayer-rewards-backfill` (same)
     - `mtds-liquidations-backfill` (same)
     - `mtds-perp-funding-backfill` (same — covers DeFi perps via Hyperliquid)
     - `mtds-solana-drift-backfill` (same)
     - `mtds-gas-fees-<ts>` via positional `2026-04-01 2026-05-16`
     - `mtds-lending-indices-<ts>` (positional 2026-04-01 2026-05-16)
     - `mtds-lst-rates-<ts>` (positional 2026-04-01 2026-05-16)
     - `mtds-pyth-archive-<ts>` (positional 2026-04-01 2026-05-16)
     - `mtds-pyth-lst-<ts>` (positional 2026-04-01 2026-05-16)
     - `mtds-vault-share-price-<ts>` (positional 2026-04-01 2026-05-16)
   - Expected duration per VM: 1-3h wallclock; total fleet wallclock ~3h (parallel).
   - Output: `gs://market-data-tick-defi-central-element-323112/raw_tick_data/by_date/day=2026-04-01..day=2026-05-16/`.
   - T+10min verification per VM (ScheduleWakeup).

3. **Stage 3 — manifest divergence A3**: post-backfill, run manifest divergence audit for asset_group=defi /
   date window 2026-04-01..2026-05-16 → expect 0 MISSING_EXPECTED. Closes parent issue.

Total estimated VM compute: 12 VMs × ~2h avg = 24 VM-hours. e2-standard-4 ~$0.13/h ⇒ ~$3 GCP cost.

## Cross-references

- Parent: `plans/active/issues/defi_upstream_46day_full_backfill_2026_05_16.md`
- Launcher SSOT: `codex/05-infrastructure/vm-tarball-deployment.md`
- VM verification SSOT: same § "Post-launch verification — T+10min check"
- VM prefix mapping: `deployment-service/scripts/vm/vm_zombie_watchdog.py` (all proposed prefixes already registered)

---

## Status

**PAUSED — awaiting operator decision (A/B/C/D above).** No VMs launched 2026-05-20. ScheduleWakeup NOT armed. Banner
NOT yet added to parent issue (will add on launch).

When operator picks path, slot 1 resumes within same dispatch cycle.
