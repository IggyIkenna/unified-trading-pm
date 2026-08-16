---
doc_type: issue
title: "Sports instruments-store manifest under-reports odds_api coverage vs the tick bucket (547 vs 247 missing days over the same window)"
summary: >-
  While investigating the `[DIAG] P3` "23 sentinel-free missing odds_api days" todo
  (`sports_satellite_ao_dispatch_batch12_2026_08_09.md:153`), a fresh census over the exact
  2020-06-06..2026-04-15 window used by the original root-cause investigation found the two sports manifest
  surfaces materially disagree on odds_api coverage: `instruments-store-sports-prd-central-element-323112` (the
  Axis-10b SSOT routing manifest) shows 547 missing calendar days for `source=odds_api`, while
  `market-data-tick-sports-prd-central-element-323112` (the bytes-physically-live-here tick bucket, and the bucket
  `check_shard_freshness`/the live backfill fleet actually read+write) shows only 247 missing days for the SAME
  window. This is the same cross-bucket-mirror-sync-gap class already tracked for `trades`/`TRADES` labeling in
  `sports_p2_trades_mirror_unstamped_instruments_store_2026_08_15.md`, here manifesting as coverage under-count
  rather than a stale label.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [instruments-service, market-tick-data-service, unified-trading-library]
scope: [engineer, admin]
tags: [sports, odds-api, manifest, cross-bucket, mirror-sync, data-correctness, honest-coverage]
related:
  [
    /plans/active/issues/sports_manifest_consolidator_zero_growth_stall_2026_07_29.md,
    /plans/active/issues/sports_p2_trades_mirror_unstamped_instruments_store_2026_08_15.md,
    /plans/active/issues/sports_odds_api_scattered_multiyear_gaps_2026_07_27.md,
    /codex/02-data/four-surface-reconciliation-procedure.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-16"
author: slot-32 (data_engineering)
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
source: ["sports_satellite_ao_dispatch_batch12_2026_08_09-153 (23 sentinel-free days investigation)"]
resolved_by:
locked_by:
locked_since:
drift_direction: advance-code
depends_on: []
---

# Sports IS-bucket odds_api coverage lags the tick bucket

## What I found

Reproduced the 2x2 `(has odds_api row) x (has ODDS_API sentinel row)` classification from
`sports_manifest_consolidator_zero_growth_stall_2026_07_29.md`'s root-cause section, over the exact same
`2020-06-06..2026-04-15` window, against BOTH candidate sports manifest surfaces (single read each, column-pruned +
date-filtered, no whole-corpus walk;
`market-tick-data-service/scripts/sports/investigate_23_sentinel_free_odds_gaps_2026_08_16.py --bucket-kind
{instruments-store,market-data}`):

| bucket                                     | days missing `source=odds_api` (of 2140 calendar days) | days with `venue=ODDS_API` sentinel |
| ------------------------------------------- | -------------------------------------------------------- | ------------------------------------ |
| `instruments-store-sports-prd` (SSOT routing manifest, Axis-10b) | **547** | 2140/2140 (100%) |
| `market-data-tick-sports-prd` (bytes physically live here; `get_tick_data_bucket()`/`check_shard_freshness` target) | **247** | 2139/2140 (99.95%) |

Both surfaces now show **0** sentinel-free residual for this window (the original "23 sentinel-free" finding is fully
resolved — see the companion Progress Log entry in the source doc) — but the two surfaces disagree by 300 days on
plain odds_api presence for the identical window. `instruments-store-sports-prd` is the more pessimistic/stale of the
two.

This is architecturally expected to some degree — sports routes every `data_type` through the IS-bucket manifest as
its documented SSOT/routing surface even though the actual bytes live in the tick bucket (Axis-10b pattern,
`instruments-service/scripts/reconcile_phantom_manifest_rows_all.py::_SPORTS_CROSS_BUCKET_DATA_TYPES`) — but the
mirror is evidently NOT staying in sync: a 300-day gap over a 2140-day window (14%) is too large to be simple
propagation lag. The sibling doc `sports_p2_trades_mirror_unstamped_instruments_store_2026_08_15.md` found the exact
same shape of gap (a live producer still writing rows the IS-bucket mirror never receives) for the `trades`/`TRADES`
data_type — this finding is very likely the SAME underlying sync gap, just observed via `source=odds_api` coverage
instead of a data_type label.

## Why it matters

Any future census/audit/investigation that reads `instruments-store-sports-prd` as "the" sports odds_api coverage
source (as the original 2026-07-29/30 root-cause investigation did, and as `four-surface-reconciliation-procedure.md`
would default to for a "check the SSOT manifest" instruction) will systematically OVER-report the true gap — this is
exactly what already happened once: the original investigation's 595/572/23 numbers were all measured against the
IS-bucket, which turns out to be the less-complete of the two surfaces for this source. A P3 diagnostic task
re-running the same query today would have reproduced a smaller-but-still-nonzero apparent gap purely from mirror
lag, not from a real missing-data problem, had it not also cross-checked the tick bucket directly.

## What I did NOT do

Did not investigate the mirror-sync mechanism itself (whether it's driven by the manifest consolidator's cross-bucket
sync, a writer double-stamp, or a one-time migration that was never made durable) — that diagnostic work belongs to
whoever picks up the todo below, and likely overlaps significantly with the sibling `trades`/`TRADES` doc's own
Progress Log findings (which already identified "the sports odds_api writer is still actively stamping
`data_type=trades`/`TRADES`... into this [IS-bucket] surface" as of 2026-08-15 — the write side for odds_api coverage
specifically was not separately confirmed live vs stale here).

## Recommended decision

- [ ] [DATA] P3. Determine whether `instruments-store-sports-prd`'s odds_api coverage gap vs
      `market-data-tick-sports-prd` is (a) the same cross-bucket-mirror-sync gap already being fixed for
      `trades`/`TRADES` in `sports_p2_trades_mirror_unstamped_instruments_store_2026_08_15.md` (in which case that
      fix, once it lands+executes, should be re-verified to also close this 300-day gap — no separate fix needed), or
      (b) a distinct gap needing its own remediation. Re-run
      `market-tick-data-service/scripts/sports/investigate_23_sentinel_free_odds_gaps_2026_08_16.py
      --bucket-kind instruments-store` after that sibling doc's `[OPERATOR]` relabel-VM todo executes; if the
      547-vs-247 gap has closed, flip this checkbox citing the shared fix; if not, scope a dedicated sync/backfill
      fix. Repos: instruments-service, market-tick-data-service.

## Progress Log

- **2026-08-16 (slot-32, data_engineering)**: filed while investigating the "23 sentinel-free missing odds_api days"
  `[DIAG] P3` todo — see the companion addendum in
  `/plans/active/issues/sports_manifest_consolidator_zero_growth_stall_2026_07_29.md`'s Progress Log for that task's
  own resolution (the 23-day residual is fully closed; this doc tracks the separate bucket-divergence finding
  surfaced along the way).
