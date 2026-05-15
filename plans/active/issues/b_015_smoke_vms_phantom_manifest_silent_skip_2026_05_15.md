---
title: "B-015 smoke VMs silent-skipped due to phantom manifest — features-onchain + MTDS lst_rates produced ZERO data"
created: 2026-05-15
author: ikenna-main (slot 1)
source:
  - "ikenna-main → harsh-slot-9 ping 2026-05-14 14:38 UTC (B-015 VMs LAUNCHED)"
  - "GCS event stream: gs://central-element-323112-events/events/market-tick-data-service/2026-05-14/mtds-lst-rates-20260514-143803/"
  - "GCS output bucket: gs://market-data-tick-defi-central-element-323112/lst_rates/ (last partition = 2026-04-14)"
severity: P0 (blocks B-015 paper-trade gate + Group B data-correctness)
locked_by: live-defi-rollout
locked_since: 2026-05-15
---

## What I found

Both B-015 smoke VMs launched 2026-05-14 14:38 UTC (operator-approved) **completed in seconds without
writing any data**. Root cause: phantom manifest rows reporting "already captured" for dates that have
zero output parquets on disk.

### MTDS lst_rates smoke (`mtds-lst-rates-20260514-143803`)

- **STARTED**: 2026-05-14 13:40:51 UTC
- **STOPPED**: 2026-05-14 13:40:54 UTC (3 seconds total)
- **Backfill window**: 2026-04-15 → 2026-04-19 (4 days, smoke pre-authorized <1 week)
- **Outcome**: 5× `MANIFEST_FRESHNESS_SKIP` events (one per day), reason
  `"already_captured_by_concurrent_worker"`. No `record_captured()` calls, no parquet writes.
- **Output bucket state**: `gs://market-data-tick-defi-central-element-323112/lst_rates/` last
  partition = `date=2026-04-14/`. **Dates 2026-04-15 → present do NOT exist on disk.**
- **Phantom**: manifest believes 2026-04-15..19 captured; bucket has nothing. Either (a) stale
  in-flight lock from an aborted prior worker (`already_captured_by_concurrent_worker` reason matches),
  or (b) manifest row written speculatively before parquet flush.

### features-onchain smoke (`features-onchain-defi-backfill-20260514-143829`)

- **No event stream**: `gs://central-element-323112-events/events/features-onchain/2026-05-14/` is
  empty (404 on ls).
- **Output bucket state**: `gs://features-onchain-central-element-323112/` empty (0 bytes).
- **Outcome**: VM either never STARTED, never emitted events, or crashed silently before STARTED.
- No way to tell from current artifacts whether VM ran and silently failed, or never ran.

## Why it matters

- **B-015 paper-trade gate is BLOCKED**: Harsh slot 9 standing by since 2026-05-14 13:10 UTC (per
  `_agent_pings.md` ping ledger) waiting on smoke verification before Phase 2 launch.
- **`carry_staked_basis` archetype eligibility (May-23 cutover) at risk**: lst_rates is the primary
  staking-yield signal; without recent data the strategy can't compute APRs.
- **Manifest phantom is a systemic risk**: if `MANIFEST_FRESHNESS_SKIP` is firing on absent data,
  ALL DeFi backfills going forward will skip silently. Need phantom audit run before next
  backfill attempt.

## Recommended decision

**Three actions in order**:

1. **Phantom audit on lst_rates rows for 2026-04-15..present**: Run
   `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py --asset-group DEFI --dry-run`
   filtered to `data_type=lst_rates` on same-region GCE VM. Identify the count of phantom rows.
2. **Apply phantom flips** (with `--apply-flips`) to mark phantom rows as `attempted_failed` so the
   freshness check stops skipping them.
3. **Re-launch both smoke VMs** with:
   - MTDS: `bash deployment-service/scripts/vm/launch-mtds-defi-vm.sh ...` with `--force-resync`
     flag (if exists) OR a unique `VM_NAME` that bypasses cache.
   - features-onchain: investigate why first launch produced no event stream; relaunch with
     event-stream verification per the no-fire-and-forget HARD RULE.

**Assignment**: Ikenna slot 8 (audit theme owner) takes phantom audit + apply-flips (~1.6 cal AI-days).
Harsh slot 9 holds B-015 Phase 2 until smoke is genuinely green (manifest-verified row count > 0 AND
sample parquet inspection passes the 4-pillar validation per CLAUDE.md).

## Cross-references

- Predecessor ping ledger entries: `plans/active/_agent_pings.md` § "2026-05-14 13:10..14:38" (B-015
  Phase 1 BLOCKED → P1 ACK → VMs LAUNCHED chain).
- Related plan: `plans/active/defi_master_2026_05_07.md` § paper-trade gate (carry_staked_basis path).
- Phantom audit pattern: `codex/02-data/availability-manifest-and-data-status.md` § "Phantom audit".
- No fire-and-forget VM rule: CLAUDE.md § "No fire-and-forget VM launches (CRITICAL)" — features-onchain
  VM appears to violate this (no STARTED event in 60s window observed).

execution:
  owner: ikenna slot 8 (phantom audit + apply-flips) + harsh slot 9 (B-015 hold + re-verification)
  cadence: one-shot
  verifier: bucket count > 0 + sample parquet inspection + manifest captured_status matches on-disk
  last_executed: NEVER
