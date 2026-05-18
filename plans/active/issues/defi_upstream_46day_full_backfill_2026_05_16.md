---
title: "DeFi upstream 46-day full backfill — operator approval required (instruments-service DeFi + MTDS DeFi raw_tick_data)"
created: 2026-05-16
author: ikenna-main (continuous orchestrator loop)
source:
  - "ikenna-slot-3 finding at plans/active/issues/defi_features_pipeline_not_run_2026_05_14.md (LST ✅, MDPS ❌)"
  - "MDPS DeFi backfill VM (mdps-backfill-defi-20260516-205843 FAILED rc=1, self-deleted) surfaced upstream gap"
locked_by: live-defi-rollout
locked_since: 2026-05-16
severity: P1 — non-blocking for B-015 paper-trade (5-day window pre-authorized in parallel ping); blocking for live DeFi data correctness across full historical window
---

## What I found

Slot-3's deeper investigation into B-015 features-onchain Smoke B failure surfaced a systemic gap that goes beyond
the original 5-day smoke target:

The MDPS DeFi pipeline requires 2 upstream dependencies that are **missing for the entire 2026-04-01 → 2026-05-16
window** (46 days):

1. **`gs://instruments-store-defi-central-element-323112/instrument_availability/by_date/day=*/`** — DeFi instruments
   index (per-protocol enumerator writes; needs instruments-service DeFi backfill).
2. **`gs://market-data-tick-defi-central-element-323112/raw_tick_data/by_date/day=*/`** — DeFi raw tick data (needs
   coordinated multi-handler MTDS DeFi batch: solana_defi_handler + evm_defi_handler + lst_rates_handler +
   gas_fee_handler).

The 5-day smoke window (2026-04-15..19 — slot 9's original B-015 target) is being addressed in parallel by slot-3
since <1 week is pre-authorized per CLAUDE.md HARD RULE. See cross-side ping
`plans/active/_agent_pings.md` § "2026-05-16 [time] ikenna-main → ikenna-slot-3 / harsh-slot-9".

## Why it matters

- **NOT a B-015 paper-trade blocker** — the 5-day smoke window is sufficient for the carry_staked_basis Phase 2
  launch; that work is sequencing through slot-3 in parallel.
- **IS a data-correctness blocker for full live-DeFi** — without the 46-day backfill, any feature/strategy that
  reads >5 days of historical DeFi data hits silent gaps.
- May-23 cutover live-DeFi gate is the trigger date for the data-correctness ask.

## Operator approval request (per CLAUDE.md HARD RULE — ≥1 week)

```
BACKFILL APPROVAL REQUEST — DeFi upstream 46-day full backfill

Window: 2026-04-01 → 2026-05-16 (46 days)
Asset group: defi
Buckets affected:
  - gs://instruments-store-defi-central-element-323112/instrument_availability/
  - gs://market-data-tick-defi-central-element-323112/raw_tick_data/
Est rows: ~46 days × ~5 protocols × multiple data_types per protocol = ~5,000-10,000 manifest rows
Est VM compute: 4-8 hours wall-clock if coordinated multi-handler batch
Singleton-locked launchers required per CLAUDE.md (no fire-and-forget)
```

Unblocks: full live-DeFi data correctness across historical window. Without it, any feature/strategy reading >5 days
of DeFi history silently hits gaps.

## Recommended decision

Operator picks one:
- **(A) Run the full backfill** — slot-3 owns; coordinated multi-handler batch on same-region GCE VMs; ~4-8 hours.
- **(B) Defer to post-cutover** — file successor plan `defi_upstream_full_backfill_post_cutover_2026_06_01.md`;
  May-23 live-DeFi cuts over with only the 5-day smoke + forward-rolling new data.
- **(C) Tighter window** (e.g. 14 days) — covers carry_staked_basis recent-history needs without full 46-day
  scope. ~1-2 hours VM compute.

**My recommendation**: **(C) 14-day backfill** as the pragmatic middle. carry_staked_basis only needs recent-history
for parameter estimation + smoke validation; doesn't need full 46-day archive. Post-cutover can absorb the
remainder if needed.

## Cross-references

- Companion: `plans/active/issues/defi_features_pipeline_not_run_2026_05_14.md` (slot-3's finding)
- Cross-side ping: `plans/active/_agent_pings.md` § "2026-05-16 ikenna-main → ikenna-slot-3 / harsh-slot-9"
- CLAUDE.md § "GCS backfill approval gate (codified here)" — ≥1 week → operator approval required

---

## Triage — 2026-05-18

**Status**: OPEN  
**Triaged by**: slot-8 triage sweep  
**Reason**: Operator approval pending for 46-day backfill execution
