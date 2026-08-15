---
doc_type: issue
title: Sports Track O attempted_at repair — pre-clobber snapshot's target keys are extinct (venue renamed)
summary: >-
  The Track O "repair attempted_at on the 112,277 rows from the named pre-clobber snapshot" todo
  (`sports_consolidated_closeout_2026_07_19.md`) is unexecutable as literally specified: a dry-run join of the
  pre-clobber snapshot against the live canonical (production dedup key) found 0 matches for venue IN (BETFAIR,
  MATCHBOOK, PINNACLE), data_type='trades' — BETFAIR was split into BETFAIR_SB_UK/_EX_EU/_EX_UK by a later
  venue-taxonomy migration, and live data_type='trades' rows now belong only to venue=ODDS_API. The consolidator-pause
  safety question is separately resolved (not needed — incremental cycles anti-join unchanged canonical rows through
  untouched, confirmed via manifest_consolidator._duckdb_merge_payload).
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service, unified-trading-library, unified-trading-pm]
scope: [engineer]
tags: [sports, manifest, attempted_at, venue-rename, track-o]
related: [/plans/active/sports_consolidated_closeout_2026_07_19.md]
created: 2026-08-14
author: claude-code (slot-12, backend_engineer, AO-dispatched)
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P2
source: >-
  Investigated while executing /plans/archive/2026_08/sports_satellite_ao_dispatch_batch13_2026_08_13.md's Track O
  attempted_at-repair todo.
resolved_by:
locked_by:
locked_since:
context_scope: [/plans/active/sports_consolidated_closeout_2026_07_19.md]
drift_direction: advance-code
depends_on: []
---

# Sports Track O attempted_at repair — target keys extinct

## What I found

The Track O todo assumed the pre-clobber snapshot's `(venue, data_type)` keys (`BETFAIR`/`MATCHBOOK`/`PINNACLE`,
`data_type='trades'`) still exist in the live canonical `availability_index.parquet`. They don't: `venue=BETFAIR` has 0
rows (split into `BETFAIR_SB_UK`, `BETFAIR_EX_EU`, `BETFAIR_EX_UK` by a later venue-taxonomy migration — plausibly Track
C's venue-vocabulary cleanup or `sports_taxonomy_p2_migration_2026_08_08.md`), and the only live `data_type='trades'`
rows belong to `venue=ODDS_API`, an unrelated cell. A dry-run key-join (both the base
`(date, venue, data_type, service_name)` key and the full production dedup key, `_dedup_key_sql`-normalized identically
to `manifest_consolidator.py`) confirmed 0 matches either way.

## Why it matters

The underlying data-correctness concern (rows carrying a clobbered `attempted_at` from the 2026-07-12/13 v9-migration
consolidator bug) may still be real — just under different venue names now. Nobody has checked whether the rows that now
live under `BETFAIR_SB_UK`/`BETFAIR_EX_EU`/`BETFAIR_EX_UK` (and wherever MATCHBOOK/PINNACLE's `trades` rows landed)
carry the same wrong stamp.

## Recommended decision

1. Trace the venue-rename mapping (which new venue(s) absorbed old BETFAIR's rows — 1:1 or 1:N split by market/region)
   via the migration that performed the split (check `sports_taxonomy_p2_migration_2026_08_08.md` and Track C's
   footystats/casing work for the mechanism).
2. Re-run the pre-clobber-snapshot join against the renamed keys to determine whether the clobber defect persists.
3. If it does, re-target the repair (CAS write, no consolidator pause needed per the resolved pause question above).
4. If the 2026-06-21 true-value window no longer has any live counterpart at all (rows since deleted/purged by other
   Track C/V work), close this as moot.

## Todos

- [ ] [DIAG] P2. Trace which renamed venue(s) (`BETFAIR_SB_UK`/`BETFAIR_EX_EU`/`BETFAIR_EX_UK`, and MATCHBOOK/
      PINNACLE's current `trades`-equivalent) absorbed the pre-clobber snapshot's rows, then re-run the attempted_at
      dry-run join against the correct current keys. (repos: market-tick-data-service)
