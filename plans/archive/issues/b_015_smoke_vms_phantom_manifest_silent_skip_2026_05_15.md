---
doc_type: issue
title: B-015 smoke VMs silent-skipped due to phantom manifest — features-onchain + MTDS lst_rates produced ZERO data
summary:
status: resolved
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, instruments-service]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-15
author: ikenna-main (slot 1)
resolved: 2026-05-17
resolution:
  SUPERSEDED — B-015 chain advanced past this. Original "phantom manifest" hypothesis incorrect (manifest was clean;
  root cause was stale lock markers). Chain progressed through 8 VM attempts + 3 infra fixes (ml-training@876f0e5,
  deployment-service@a6f746f, features-service@d687df7d) + lending-indices phantom flip. VM 8
  (features-onchain-defi-20260517-025847) wrote 5 lst_yields parquets — B-015 gate UNBLOCKED 2026-05-17 02:08 UTC.
source:
  [
    "ikenna-main → harsh-slot-9 ping 2026-05-14 14:38 UTC (B-015 VMs LAUNCHED)",
    "GCS event stream:
    gs://central-element-323112-events/events/market-tick-data-service/2026-05-14/mtds-lst-rates-20260514-143803/",
    "GCS output bucket: gs://market-data-tick-defi-central-element-323112/lst_rates/ (last partition = 2026-04-14)",
  ]
severity: P0 (blocks B-015 paper-trade gate + Group B data-correctness)
locked_by: live-defi-rollout
locked_since: 2026-05-15
---

## What I found

Both B-015 smoke VMs launched 2026-05-14 14:38 UTC (operator-approved) **completed in seconds without writing any
data**. Root cause: phantom manifest rows reporting "already captured" for dates that have zero output parquets on disk.

### MTDS lst_rates smoke (`mtds-lst-rates-20260514-143803`)

- **STARTED**: 2026-05-14 13:40:51 UTC
- **STOPPED**: 2026-05-14 13:40:54 UTC (3 seconds total)
- **Backfill window**: 2026-04-15 → 2026-04-19 (4 days, smoke pre-authorized <1 week)
- **Outcome**: 5× `MANIFEST_FRESHNESS_SKIP` events (one per day), reason `"already_captured_by_concurrent_worker"`. No
  `record_captured()` calls, no parquet writes.
- **Output bucket state**: `gs://market-data-tick-defi-central-element-323112/lst_rates/` last partition =
  `date=2026-04-14/`. **Dates 2026-04-15 → present do NOT exist on disk.**
- **Phantom**: manifest believes 2026-04-15..19 captured; bucket has nothing. Either (a) stale in-flight lock from an
  aborted prior worker (`already_captured_by_concurrent_worker` reason matches), or (b) manifest row written
  speculatively before parquet flush.

### features-onchain smoke (`features-onchain-defi-backfill-20260514-143829`)

- **No event stream**: `gs://central-element-323112-events/events/features-onchain/2026-05-14/` is empty (404 on ls).
- **Output bucket state**: `gs://features-onchain-central-element-323112/` empty (0 bytes).
- **Outcome**: VM either never STARTED, never emitted events, or crashed silently before STARTED.
- No way to tell from current artifacts whether VM ran and silently failed, or never ran.

## Why it matters

- **B-015 paper-trade gate is BLOCKED**: Harsh slot 9 standing by since 2026-05-14 13:10 UTC (per `_agent_pings.md` ping
  ledger) waiting on smoke verification before Phase 2 launch.
- **`carry_staked_basis` archetype eligibility (May-23 cutover) at risk**: lst_rates is the primary staking-yield
  signal; without recent data the strategy can't compute APRs.
- **Manifest phantom is a systemic risk**: if `MANIFEST_FRESHNESS_SKIP` is firing on absent data, ALL DeFi backfills
  going forward will skip silently. Need phantom audit run before next backfill attempt.

## Phantom audit results — 2026-05-15 (slot 8)

**Ran**:
`instruments-service/scripts/reconcile_phantom_manifest_rows_all.py --asset-group defi --dry-run --data-types lst_rates`

**Result**: `Real captures: 30, Phantom captures: 0` — **manifest is CLEAN**. No phantom rows found. No flips applied.

This disproves the original hypothesis. The `MANIFEST_FRESHNESS_SKIP / already_captured_by_concurrent_worker` reason is
**NOT caused by phantom manifest rows**. The 30 `lst_rates` captured manifest rows all have corresponding parquet files
on disk.

### Revised root cause hypothesis

The `already_captured_by_concurrent_worker` skip is from a **stale in-flight lock marker** — an MTDS per-VM shard
isolation mechanism (`MANIFEST_PER_VM_SHARDS=true`) where a prior VM wrote a lock record but then aborted/crashed before
completing. The freshness check sees the lock and skips rather than overwriting. Since the lock is stale, the data for
`2026-04-15..19` appears "in progress" to the next VM, which exits immediately.

### Revised recommended decision

1. **Apply-flips not needed** — manifest is clean, nothing to flip.
2. **Re-launch MTDS lst_rates smoke** with a unique `VM_NAME` (e.g., `mtds-lst-rates-smoke-v2-20260515`) so that the
   per-VM shard isolation sees a fresh VM and does not match the stale lock. Command pattern:
   ```bash
   VM_NAME=mtds-lst-rates-smoke-v2-20260515 MANIFEST_PER_VM_SHARDS=true \
   bash deployment-service/scripts/vm/launch-mtds-defi-vm.sh \
     --data-type lst_rates --asset-group defi \
     --start-date 2026-04-15 --end-date 2026-04-19
   ```
3. **features-onchain smoke investigation** — no event stream suggests VM crash before STARTED event. Re-launch with
   event-stream monitoring per no-fire-and-forget rule; add `--log-level DEBUG` to capture boot failure.
4. **GCS network instability note**: phantom audit encountered `ConnectionResetError` + `NameResolutionError` for
   `storage.googleapis.com` during the listing phase (2026-05-15 11:22–11:23 UTC). Retry logic handled it; audit
   completed successfully. Not related to B-015 root cause.

**Assignment**: Harsh slot 9 re-launches smoke VMs with unique `VM_NAME` + monitors event stream. Ikenna slot 8 phantom
audit is COMPLETE (clean result, no action needed).

## Cross-references

- Predecessor ping ledger entries: `plans/active/_agent_pings.md` § "2026-05-14 13:10..14:38" (B-015 Phase 1 BLOCKED →
  P1 ACK → VMs LAUNCHED chain).
- Related plan: `plans/active/defi_master_2026_05_07.md` § paper-trade gate (carry_staked_basis path).
- Phantom audit pattern: `/codex/02-data/availability-manifest-and-data-status.md` § "Phantom audit".
- No fire-and-forget VM rule: CLAUDE.md § "No fire-and-forget VM launches (CRITICAL)" — features-onchain VM appears to
  violate this (no STARTED event in 60s window observed).

execution: owner: ikenna slot 8 (phantom audit + apply-flips) + harsh slot 9 (B-015 hold + re-verification) cadence:
one-shot verifier: bucket count > 0 + sample parquet inspection + manifest captured_status matches on-disk
last_executed: NEVER

---

## Triage — 2026-05-18

**Status**: CLOSED — SHIPPED **Triaged by**: slot-8 triage sweep **Reason**: Resolved 2026-05-17; VM 8 wrote 5 parquets,
gate unblocked
