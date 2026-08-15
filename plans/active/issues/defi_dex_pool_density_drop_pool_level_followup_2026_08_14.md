---
doc_type: issue
title: DeFi dex_pool_state/dex_pool_swaps density drop — needs a pool-level (not venue-level) cross-check
summary: >-
  A venue-level cross-check (defi_rebuild_vm_oom_root_cause_and_relaunch_carveout_2026_08_10.md's Track todo) found
  DeFi's daily shard count fell >26x (33,091.8/day Dec2025-Feb2026 -> 1,254.5/day 2026-06-30..07-19) while distinct
  venue count fell only ~31% (54.54 -> 37.55/day) — venue retirement alone cannot explain the magnitude. The dominant
  contributors (dex_pool_state 657.35/day + dex_pool_swaps 173.75/day, 66% of the recent-window total) are POOL-grain,
  not venue-grain, so the real driver is likely a shrinking tracked-pool universe per surviving venue. This is
  directionally consistent with named in-flight dex_pools/dex_swaps retirement plans but not confirmed at the pool-count
  level.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, instruments-service, unified-trading-pm]
scope: [engineer]
tags: [defi, dex-pools, dex-swaps, shard-density, capture-gap, pool-catalogue]
related:
  [
    /plans/archive/2026_08/issues/defi_rebuild_vm_oom_root_cause_and_relaunch_carveout_2026_08_10.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
  ]
created: 2026-08-14
author: claude-code (slot-12, backend_engineer, AO-dispatched)
parent_epic: defi_master
assigned_vm: NA
execution_scope: local-only
priority: P2
source: >-
  Investigated while executing /plans/archive/2026_08/defi_satellite_ao_dispatch_batch13_2026_08_13.md's
  shard-density-trend-verification todo (itself sourced from
  defi_rebuild_vm_oom_root_cause_and_relaunch_carveout_2026_08_10.md).
resolved_by:
locked_by:
locked_since:
context_scope: [/plans/archive/2026_08/issues/defi_rebuild_vm_oom_root_cause_and_relaunch_carveout_2026_08_10.md]
drift_direction: advance-code
depends_on: []
---

# DeFi dex_pool density drop — pool-level follow-up

## What I found

Venue-level cross-check (bounded `read_availability_index_safe` queries, 3 windows, `capture_status=captured` only):

| window                       | avg shards/day | avg distinct venues/day |
| ---------------------------- | -------------: | ----------------------: |
| known-good (Dec2025-Feb2026) |       33,091.8 |                   54.54 |
| mid (Jun10-29)               |        6,188.7 |                   46.45 |
| recent (Jun30-Jul19)         |        1,254.5 |                   37.55 |

Shard count fell >26x; venue count fell only ~31%. `dex_pool_state` + `dex_pool_swaps` are the dominant data_types in
the recent window (66% of the total) and are POOL-grain (many pools per venue), not venue-grain — so a shrinking
per-venue pool count, not fewer venues, is the more likely primary driver.

## Why it matters

If the pool-count drop is a genuine, intended retirement/consolidation (the doc names `dex_pools`/`dex_swaps`/
`kamino_lending`/`blazestake`/`sushiswap` retirement plans as in flight), this is expected and fine. If it's an
unflagged capture regression (e.g. a pool-enumeration/catalogue-refresh job stalled or a filter narrowed
unintentionally), it's a real, currently-invisible DeFi data gap.

## Recommended decision

Run a pool-COUNT-level census (not venue-level): compare the distinct tracked-pool-id count per venue between the
known-good and recent windows (e.g. via the DEX pool catalogue / `instruments-store-defi` reference data, or the
manifest's own instrument-id-grained rows if `dex_pool_state`/`dex_pool_swaps` carry one). If the pool count dropped
proportionally to the shard count and matches a documented retirement's scope, close as genuine. If it dropped
disproportionately or doesn't match a named retirement's actual pool list, escalate as a capture-gap finding.

## Todos

- [ ] [DIAG] P2. Pool-count-level census: distinct tracked pool/instrument ids per venue for `dex_pool_state`/
      `dex_pool_swaps`, known-good (Dec2025-Feb2026) vs recent (2026-06-30..07-19) — confirm the drop matches a named
      retirement plan's actual pool-removal scope, or escalate as a capture gap. (repo: market-tick-data-service)
