---
doc_type: issue
title:
  "sports_closeout_exchange_fixed_odds_fork's EXCHANGE_ODDS/FIXED_ODDS venue list (8 venues, 561,260 rows) covers a
  small fraction of the live instrument_type=odds manifest (~27 venues, 54.8M rows) — the later GCS-move todos are
  likely under-scoped"
summary: >-
  Pre-drain todo 2 of sports_closeout_exchange_fixed_odds_fork_2026_07_25.md required a manifest snapshot before any GCS
  move. Reading the live sports availability_index for instrument_type=odds (both `ODDS`/`odds` casings, no date/venue
  restriction) returned 295,921 manifest entries across ~27 venues summing to 54,835,957 total row_count — not the 8
  venues / 561,260 rows the plan's mapping-ruling todo (todo 1) and its two Move-the-GCS-objects todos enumerate
  (BETFAIR_EX_UK, BETFAIR_EX_EU, SMARKETS, MATCHBOOK, BETFAIR_SB_UK, BETMGM, bare BETFAIR, ODDS_API, PINNACLE).
  Per-venue figures also diverge sharply from the plan's own cited numbers for the same venues it DID enumerate — e.g.
  PINNACLE: plan says "32,616 rows", live manifest shows 4,887,512 for PINNACLE alone. At least ~19 additional bookmaker
  venues (BETONLINEAG, UNIBET, BETRIVERS, WILLIAMHILL, CASUMO, SPORT888, CORAL, PADDYPOWER, DRAFTKINGS, UNIBET_UK,
  SKYBET, BETSSON, FANDUEL, VIRGINBET, LIVESCOREBET, BETVICTOR, LADBROKES_UK, BOVADA, BETWAY, UNIBET_EU) carry
  substantial instrument_type=odds row_count and are absent from the plan's venue→class mapping entirely. If the plan's
  two Move todos execute as scoped (5 then 3 venues, 8 total) and a later todo retires the legacy `odds` contract entry,
  these ~19 unmapped venues' data has no EXCHANGE_ODDS/FIXED_ODDS destination and would be silently orphaned by the
  cutover. NOT YET DETERMINED (needs operator/data_engineering follow-up, not resolved by this doc): whether the plan's
  cited 561,260 / 32,616-etc. figures came from a narrower slice (e.g. a specific date range, a `data_type=trades`-only
  cut, or a distinct-shard count rather than a row_count sum) that legitimately excludes the other venues and the
  cumulative history — or whether the plan's venue enumeration is genuinely incomplete. This doc does not attempt that
  reconciliation; it exists so the discrepancy is on record before the Move todos are dispatched against a possibly
  incomplete list.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts, unified-trading-pm]
scope: [engineer]
tags: [data-correctness, sports, odds, venue-mapping, manifest, operator-notify, pre-drain]
related:
  [
    /plans/active/sports_closeout_exchange_fixed_odds_fork_2026_07_25.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
  ]
created: 2026-07-27
priority: P0
parent_epic: sports_master
source: >-
  Measured directly against the live
  gs://market-data-tick-sports-prd-central-element-323112/_index/availability_index.parquet during
  sports_closeout_exchange_fixed_odds_fork_2026_07_25.md todo 2 (pre-drain snapshot), 2026-07-27T00:47:17Z — snapshot
  gs://market-data-tick-sports-prd-central-element-323112/_index/snapshots/pre_odds_predrain_exchange_fixed_fork_2026_07_27_20260727T004717Z.parquet
  (10,367,527 bytes, byte-verified). Read via unified_trading_library.read_availability_index, columns=[date, venue,
  instrument_type, row_count, capture_status], no filter (client-side pandas filter on instrument_type to rule out a
  pyarrow-pushdown-filter artifact — the pushdown-filtered read had returned an implausible KALSHI/0-row-only result,
  which this client-side re-check contradicted with real bookmaker-venue data, so the pushdown path is suspect
  separately from this finding but not yet root-caused).
execution_scope: local-only
drift_direction: advance-docs
depends_on: []
locked_by:
locked_since:
assigned_vm: NA
resolved_by:
---

# sports odds venue-enumeration undercount, discovered at pre-drain

> **🔴 OPERATOR-NOTIFY — data-correctness class, scoped to `sports_closeout_exchange_fixed_odds_fork_2026_07_25.md`.**
> Do not dispatch that plan's two "Move the `instrument_type=odds/` GCS objects" todos (P1) against their current
> 8-venue list until this is reconciled — either the 561,260/32,616-etc. figures are confirmed to be a legitimate
> narrower slice (in which case this doc closes as a false alarm with the slice definition recorded), or the venue list
> needs to grow to cover the ~19 additional venues found live before any legacy-contract retirement proceeds.

## What was measured (2026-07-27, pre-drain snapshot time)

Query:
`read_availability_index(bucket="market-data-tick-sports-prd-central-element-323112", columns=["date","venue","instrument_type","row_count","capture_status"], filters=None)`,
then client-side `instrument_type.str.lower() == "odds"`.

- Total manifest entries (all instrument_types): 465,223
- `instrument_type` value_counts: `ODDS`=275,136, `odds`=20,785, blank/other=~169,294, `SPORT`=8
- Matching `odds`/`ODDS` entries: 295,921
- Summed `row_count` across those entries: **54,835,957**
- capture_status breakdown: `captured`=54,835,957, `empty_confirmed`=0 (i.e. essentially all matched entries are real
  captured data, not honest-absence placeholders)
- By venue (row_count sum, descending): MATCHBOOK 5,786,903 · PINNACLE 4,887,512 · BETONLINEAG 3,884,011 · UNIBET
  3,643,081 · BETRIVERS 2,663,376 · WILLIAMHILL 2,603,619 · CASUMO 2,487,062 · BETFAIR_EX_UK 2,407,423 · BETFAIR_EX_EU
  2,386,948 · SPORT888 2,228,223 · CORAL 2,183,527 · PADDYPOWER 2,167,335 · DRAFTKINGS 1,956,118 · UNIBET_UK 1,935,637 ·
  SKYBET 1,912,231 · BETSSON 1,722,631 · FANDUEL 1,710,435 · VIRGINBET 1,675,565 · LIVESCOREBET 1,629,455 · BETVICTOR
  1,570,357 · LADBROKES_UK 1,149,365 · SMARKETS 1,113,644 · BETFAIR_SB_UK 1,073,017 · BOVADA 32,466 · BETWAY 15,102 ·
  BETMGM 10,890 · UNIBET_EU 24 · KALSHI 0

## The plan's enumeration (for comparison)

`sports_closeout_exchange_fixed_odds_fork_2026_07_25.md` scopes exactly 8 venues total:

- EXCHANGE_ODDS: `BETFAIR_EX_UK`, `BETFAIR_EX_EU`, `SMARKETS`, `MATCHBOOK`, bare `BETFAIR` (33 rows per the plan)
- FIXED_ODDS: `BETFAIR_SB_UK`, `BETMGM`, `ODDS_API` (33 rows), `PINNACLE` (32,616 rows)

Comparing the venues the plan DID enumerate against what's live: PINNACLE alone is 4,887,512 live vs. 32,616 cited
(≈150x); BETFAIR_SB_UK 1,073,017 vs. no figure cited; BETMGM 10,890 (closer in order of magnitude, but still not
reconciled). `bare BETFAIR` and `ODDS_API`'s tiny cited figures (33 each) don't appear as isolated venue keys in this
query's output — worth checking whether they're absorbed under a different key in the live data, another sign the
reconciliation hasn't been done.

## What this doc is NOT claiming

Not asserting the plan's numbers are simply wrong — they may reflect a legitimate narrower cut (single date,
`data_type=trades`-only from a recent fix, or a distinct-shard rather than row_count metric) that this doc's blunter
"everything tagged odds, all time" query doesn't reproduce. Also not asserting the ~19 extra venues are in-scope for
THIS fork (they may already have a home under a different asset_group/instrument_type this doc's author didn't check).
Flagging only that the discrepancy exists, is large, and touches the exact set of GCS-move todos that would otherwise
proceed against the narrower list.

## Suggested next step (not performed here — scope belongs to the plan's own mapping-ruling pattern, i.e. an `[OPERATOR]` decision, per `sports_closeout_exchange_fixed_odds_fork_2026_07_25.md` todo 1's precedent)

1. Reconcile where the plan's 561,260 / per-venue figures came from (grep `sports_consolidated_closeout_2026_07_19.md`
   for the derivation, if recorded).
2. If the ~19 extra venues are genuinely in-scope sportsbook data with no other home, extend the plan's venue→class
   mapping before the Move todos dispatch.
3. If they're out of scope (different asset_group / already migrated / legitimately excluded), record why in this doc's
   `resolved_by` and close.

## Secondary, smaller finding (not this doc's main subject)

The `read_availability_index(..., filters=[("instrument_type","=","odds")])` pushdown-filtered read returned an
implausible 20,785-entry, all-`KALSHI`, all-`0`-row_count result — inconsistent with the client-side-filtered result
above (which shows real bookmaker data). This looks like a pyarrow row-group pushdown-filter bug or a schema/dtype
mismatch on the `instrument_type` column for filtered reads specifically, not a data problem. Not root-caused here;
worth a follow-up if anyone else hits a suspiciously narrow/empty result from a filtered `read_availability_index` call
on this bucket.
