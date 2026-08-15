---
doc_type: issue
title: Sports IS-bucket cross-bucket `trades` mirror rows never re-stamped to `odds`
summary: >-
  Live census 2026-08-15 (sports_taxonomy_p2_migration_2026_08_08.md's "assert the vocabulary has collapsed to TWO
  types" REVIEW todo): the `trades`→`odds` re-stamp shipped earlier in that plan only touched the
  `market-data-tick-sports-prd` manifest. The SSOT reference manifest (`instruments-store-sports-prd`) still carries
  `data_type=trades`/`TRADES` cross-bucket-mirror rows (Axis-10b pattern,
  `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py::_SPORTS_CROSS_BUCKET_DATA_TYPES`) that were never
  relabeled, so a live query against that surface still shows a third odds-family type.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [instruments-service, market-tick-data-service]
scope: [engineer]
tags: [sports, migration, canonicalisation, manifest, cross-bucket, trades, odds]
related:
  [/plans/active/sports_taxonomy_p2_migration_2026_08_08.md, /codex/02-data/four-surface-reconciliation-procedure.md]
created: "2026-08-15"
last_updated: 2026-08-15
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
source: ["sports_taxonomy_p2_migration_2026_08_08.md REVIEW todo, live census 2026-08-15 (slot-20)"]
resolved_by:
locked_by:
locked_since:
---

# Sports IS-bucket `trades` mirror rows never re-stamped

## What I found

Live census (2026-08-15, `unified_trading_library.read_availability_index`) against the two sports manifest buckets,
restricted to odds-family `data_type` values:

- `market-data-tick-sports-prd-central-element-323112` (raw+derived, batch+live — the P0 re-stamp's actual target):
  captured rows are `odds_horizon_bucket`=5,419,978, `odds`=542,879, `arbitrage_opportunity`=17,851 (untouched, as
  required), plus the already-tracked `odds_snapshot`/`odds_movement` phantoms (separate BLOCKED-OPERATOR-DECISION todo)
  and a small `trades`=1,600 residue. This surface is effectively collapsed to the intended two types modulo the
  already-tracked items.
- `instruments-store-sports-prd-central-element-323112` (the SSOT reference/routing manifest — sports routes every
  data_type through this one manifest per Axis-10b, even though `trades`/`odds_horizon_bucket` bytes physically live in
  the tick bucket): still carries `trades`=43,726 captured (122,286 all-status) + `TRADES`=32 captured (2,216
  all-status) rows. None of this plan's re-stamp todos (the P0 `trades`→`odds` todo, the 19-token lowercase todo —
  `TRADES`/`trades` was never one of the 19 tokens) actually touched this manifest's cross-bucket mirror rows.

## Why it matters

The plan's own REVIEW todo ("assert the vocabulary has collapsed to TWO types … anything outside these is incomplete")
fails on this surface: a consumer reading the IS-bucket manifest directly (the documented SSOT for sports data-type
membership) still sees a live third type, `trades`, at non-trivial volume.

## Recommended decision

Extend the existing `trades`→`odds` re-stamp tooling
(`market-tick-data-service/scripts/sports/restamp_sports_trades_to_odds_2026_08_12.py` /
`manifest_swap_trades_to_odds_2026_08_12.py`) to also relabel the IS-bucket's cross-bucket mirror rows (or confirm via a
fresh live probe whether the manifest consolidator's cross-bucket sync already carries these on its next cycle, before
assuming a code fix is needed).

- [ ] [DATA] P2. Census the `instruments-store-sports-prd` manifest's `trades`/`TRADES` rows' `capture_status`/
      `venue`/`date` distribution, confirm whether they are stale historical mirrors of already-migrated tick-bucket
      shards (safe metadata-only relabel) or reflect a live producer still writing the old label into this surface, then
      re-stamp or fix the writer accordingly. §3a does not apply (no object delete, manifest-only). Re-run this doc's
      census after the fix; 0 remaining `trades`/`TRADES` rows on this surface closes the parent plan's "assert the
      vocabulary has collapsed to TWO types" REVIEW todo. (repo: instruments-service or market-tick-data-service,
      whichever owns the write path found)
