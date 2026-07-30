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

## PARTIAL RECONCILIATION (2026-07-27, slot-8) — the 6 already-unambiguous venues ONLY, NOT closing this doc

Before executing `sports_closeout_exchange_fixed_odds_fork_2026_07_25.md` todo 5 ("Move the `instrument_type=odds/` GCS
objects for the 5 already-unambiguous venues ONLY" — the plan's title says "5", its own venue list names 6:
`BETFAIR_EX_UK`, `BETFAIR_EX_EU`, `SMARKETS`, `MATCHBOOK`, `BETFAIR_SB_UK`, `BETMGM`), re-measured live against the
manifest specifically for these 6 venues:

- None of these 6 venues are among the ~19 unmapped venues this doc lists (`BETONLINEAG`, `UNIBET`, `BETRIVERS`,
  `WILLIAMHILL`, `CASUMO`, `SPORT888`, `CORAL`, `PADDYPOWER`, `DRAFTKINGS`, `UNIBET_UK`, `SKYBET`, `BETSSON`, `FANDUEL`,
  `VIRGINBET`, `LIVESCOREBET`, `BETVICTOR`, `LADBROKES_UK`, `BOVADA`, `BETWAY`, `UNIBET_EU`) — confirmed by
  set-difference against the per-venue list above. So this doc's core concern (venues with no EXCHANGE_ODDS/FIXED_ODDS
  destination getting silently orphaned by a later legacy-contract retirement) does not apply to these 6: they already
  had a resolved class before this doc was filed, and moving them does not touch, retire, or otherwise affect the ~19
  unmapped venues' data or the legacy `odds` contract (retirement is a separate, later, explicitly-gated todo).
- Real live scope for these 6 (via `read_availability_index`, manifest-derived, no GCS walk): **44,525 manifest shards /
  12,778,825 summed `row_count`** across `instrument_type=ODDS, data_type=TRADES` (both fields uppercase-cased on
  disk/manifest for these 6 venues — 0 lowercase-cased manifest rows found for them). This does not match either this
  doc's cited 54.8M-corpus-wide figure (expected — that's the full ~27-venue corpus) or the plan's own cited
  561,260/32,616-etc. figures (neither reconciled here — still an open question for the OTHER venues/this doc's todo 1).
  Todo 5 was executed against this FRESH live count, not either stale figure.
- Result: todo 5 executed 2026-07-27 — 44,525/44,525 shards copied to `instrument_type=exchange_odds`/`fixed_odds`
  (lowercase, per the final sports casing doctrine), independently re-verified (crc32c+size match, 0 missing, 0
  mismatch), and the old `instrument_type=ODDS/data_type=TRADES` source objects deleted (0 remaining). See
  `sports_closeout_exchange_fixed_odds_fork_2026_07_25.md` todo 5 for the evidence citation.
- **This doc STAYS OPEN** — the ~19-unmapped-venue question (this doc's actual main subject) is untouched by the above
  and still needs the operator/data_engineering follow-up steps below before the legacy `odds` contract can be safely
  retired.

## PARTIAL RECONCILIATION (2026-07-27, slot-14) — the 3 previously-ambiguous venues ONLY, NOT closing this doc

Before executing `sports_closeout_exchange_fixed_odds_fork_2026_07_25.md`'s "move those 3 venues' GCS objects" todo
(bare `BETFAIR`, `ODDS_API`, `PINNACLE` — the 3 venues the mapping todo ruled 2026-07-26), re-measured live against the
manifest specifically for these 3 venues, per this same doc's precedent for the prior 6-venue move:

- None of these 3 venues are among the ~19 unmapped venues this doc lists (`BETONLINEAG`, `UNIBET`, `BETRIVERS`,
  `WILLIAMHILL`, `CASUMO`, `SPORT888`, `CORAL`, `PADDYPOWER`, `DRAFTKINGS`, `UNIBET_UK`, `SKYBET`, `BETSSON`, `FANDUEL`,
  `VIRGINBET`, `LIVESCOREBET`, `BETVICTOR`, `LADBROKES_UK`, `BOVADA`, `BETWAY`, `UNIBET_EU`) — confirmed by
  set-difference against the per-venue list above. So this doc's core concern (venues with no EXCHANGE_ODDS/FIXED_ODDS
  destination getting silently orphaned by a later legacy-contract retirement) does not apply to these 3.
- Real live scope for these 3 (via `read_availability_index`, manifest-derived, no GCS walk), measured 2026-07-27: bare
  `BETFAIR` = **0 shards / 0 rows** under `instrument_type=ODDS` — the venue key does not appear at all among the
  manifest's 31 distinct venues (any instrument_type), consistent with the mapping todo's own text that the plan's cited
  33 rows were dead legacy writes from a since-fixed structural bug (`mtds@accd8aa4`, 2026-07-20). `ODDS_API` = **0
  shards / 0 rows** under `instrument_type=ODDS` — the venue key DOES exist in the manifest, but only under other
  instrument_types (markets/outcomes/settlements per the mapping ruling), none of which are `odds`. `PINNACLE` =
  **15,570 shards / 4,887,512 summed row_count** under `instrument_type=ODDS, data_type=TRADES` (uppercase on disk) —
  matches this doc's own earlier corpus-wide PINNACLE figure (4,887,512) above, not the plan's stale "32,616 rows"
  citation.
- Result: the plan's move-todo executed 2026-07-27 against these fresh live counts — 15,570/15,570 PINNACLE shards
  copied to `instrument_type=fixed_odds` (lowercase), independently re-verified (crc32c+size match, 0 missing, 0
  mismatch), old `instrument_type=ODDS/data_type=TRADES` PINNACLE source objects deleted (0 remaining). BETFAIR/
  ODDS_API had nothing to move (0 shards each) — not a data-loss concern, just confirmation their plan-cited row counts
  no longer (or never did) exist under the `odds` instrument_type. See
  `sports_closeout_exchange_fixed_odds_fork_2026_07_25.md`'s move-todo for the full evidence citation
  (`market-tick-data-service@2d0a7dc6`).
- **This doc STAYS OPEN** — the ~19-unmapped-venue question (this doc's actual main subject) is untouched by the above
  and still needs the operator/data_engineering follow-up steps below before the legacy `odds` contract can be safely
  retired.

## Suggested next step (not performed here — scope belongs to the plan's own mapping-ruling pattern, i.e. an `[OPERATOR]` decision, per `sports_closeout_exchange_fixed_odds_fork_2026_07_25.md` todo 1's precedent)

1. Reconcile where the plan's 561,260 / per-venue figures came from (grep `sports_consolidated_closeout_2026_07_19.md`
   for the derivation, if recorded).
2. If the ~19 extra venues are genuinely in-scope sportsbook data with no other home, extend the plan's venue→class
   mapping before the Move todos dispatch.
3. If they're out of scope (different asset_group / already migrated / legitimately excluded), record why in this doc's
   `resolved_by` and close.

## Investigation (2026-07-28, corpus-only — no live GCS/manifest access from this session)

Ran the doc's own suggested next-steps 1-2 as a corpus grep/read, not a live query:

1. **Where the plan's 561,260/32,616 figures came from**: NOT in `sports_consolidated_closeout_2026_07_19.md` (grepped,
   0 hits for either figure). Traced instead to
   `/plans/archive/2026_07/data_status_page_ux_and_canonicalisation_history_2026_07_24.md` (line 993, dated
   **2026-07-17**): a live snapshot of the sports `availability_index.parquet` taken 10 days before this doc's own
   2026-07-27 measurement, itemizing only the "evidenced" venues (the ones the 2026-07-18 operator ruling needed) — its
   own text says "the middle will not be guessed", i.e. it was never a claim of a complete venue enumeration. This
   confirms the 561,260/32,616 figures are a stale point-in-time snapshot, not a narrower legitimate slice (date-range
   or data_type-scoped) as this doc's "What this doc is NOT claiming" section speculated might be the case — but see
   finding 2 below for a real, distinct data_type-scope difference.
2. **Whether the ~19 unmapped venues have another canonical destination**: strong corpus evidence they do.
   `/plans/archive/issues/mdps_t1_recon_job_oom_failing_7_days_2026_07_26.md` (Updates 4-12) documents an
   actively-worked, already-shipped fix chain for MDPS-derived sports odds products (`odds_movement_15m`,
   `odds_snapshot_15m`, `odds_horizon_bucket`/`_15m`, `arbitrage_opportunity_15m`) whose exact venue list — 23 venues
   incl. WILLIAMHILL, BETFAIR_EX_EU, BETFAIR_EX_UK, BETONLINEAG, BETRIVERS, BETSSON, BETVICTOR, CASUMO, CORAL,
   DRAFTKINGS, FANDUEL, LADBROKES_UK, LIVESCOREBET, PADDYPOWER, PINNACLE, SKYBET, SMARKETS, SPORT888, UNIBET, UNIBET_UK,
   VIRGINBET, BETFAIR_SB_UK, MATCHBOOK — is a near-exact match for this doc's ~19-venue unmapped list. Per that doc's
   Update 5: `unified_api_contracts.internal.schemas._candle_contracts.py` registers all 4 of these MDPS-derived
   products under a single **generic `instrument_type="odds"`** (the same instrument_type key this doc's undercount
   query summed, and the same one `sports_closeout_exchange_fixed_odds_fork_2026_07_25.md` is forking) — while this
   doc's own undercount query (see "What was measured" above) had `filters=None`, i.e. it summed `row_count` across
   **every `data_type`** under `instrument_type=odds/ODDS`, not just `data_type=trades`. The fork plan's
   Move-GCS-objects todos are explicitly scoped to `data_type=trades` only (confirmed: both already-executed Move todos
   measured their live scope as "`instrument_type=ODDS/data_type=TRADES`" specifically). This is consistent with the ~19
   venues' bulk of row_count being
   `odds_movement_15m`/`odds_snapshot_15m`/`odds_horizon_bucket`/`arbitrage_opportunity_15m` rows (a DIFFERENT data_type
   family from `trades`), which would mean they are not orphaned raw sportsbook trades data at all — they are a separate
   MDPS-derived product line, already tracked and being actively fixed in a different, already-active plan.

**This is a strong, corpus-grounded finding, not a live-manifest-verified one** — it does not itself prove zero
`data_type=trades` rows exist for these 19 venues (only that a large, separate, already-explained `data_type` family
does exist for them under the same instrument_type). The one remaining check needed to fully close this doc is narrow
and mechanical, not open-ended, so this is being left as a normal dispatchable audit todo rather than an operator
escalation — the ambiguity the original todo worried about ("are the ~19 venues in-scope, or legitimately out of scope")
now has a concrete, checkable hypothesis to confirm rather than an open judgment call.

## Todos

- [x] ✅ [DATA] P0. **DONE 2026-07-29 (batch closeout pass) — DISPOSITION B: nonzero, real orphan risk confirmed for ALL
      19 venues, NOT a false alarm.** Ran the exact per-venue check this todo specifies (`read_availability_index`,
      `market-data-tick-sports-prd-central-element-323112`, columns=[date,venue,instrument_type,data_type,row_count,
      capture_status], no new whole-corpus walk — the same single-object manifest read this doc's own investigation
      already used), filtered to the 19 named venues + `instrument_type.str.lower()=="odds"` +
      `data_type.str.lower()=="trades"`:

      ```
                              rows matching (19 venues, instrument_type in {odds,ODDS}, data_type=trades): 292,117
                              summed row_count: 51,291,778
                              capture_status: 100% captured (0 empty_confirmed)
                              data_type on-disk casing: 100% lowercase "trades" (0 "TRADES")
                              per-venue breakdown (rows): PADDYPOWER 21879, UNIBET 21722, DRAFTKINGS 20286, SKYBET 19917, SPORT888 18882,
                                FANDUEL 18025, BETONLINEAG 17806, BETRIVERS 17477, CORAL 17134, WILLIAMHILL 16962, BETVICTOR 16937,
                                VIRGINBET 15358, LIVESCOREBET 14607, CASUMO 14222, BETSSON 14160, UNIBET_UK 12685, LADBROKES_UK 12164,
                                BOVADA 1006, BETWAY 864, UNIBET_EU 24
                              ```

                              This directly contradicts the 2026-07-28 corpus-only investigation's hypothesis (that the 19 venues' `odds`
                              footprint is exclusively the MDPS-derived 15m-product family) — every one of the 19 venues has real, substantial,
                              100%-captured raw sportsbook `data_type=trades` rows under `instrument_type=odds` TODAY, not zero. **Per this
                              todo's own disposition-B branch: escalating, not closing.** All 19 venues (not a subset) genuinely need a
                              venue→class mapping added to `sports_closeout_exchange_fixed_odds_fork_2026_07_25.md` before that plan's legacy
                              `odds` UAC contract retirement can safely proceed — retiring the contract with these 51.3M rows still unmapped
                              would silently orphan them. **BIG FINDING — operator-notify per the data-correctness hard rule** (this reverses a
                              prior investigation's conclusion and blocks a legacy-contract retirement in an active plan); flagged in this
                              session's final report. Follow-up tracked as a fresh todo below (never left as prose per the
                              todos-not-prose rule). Repos: market-tick-data-service (verification only) / unified-trading-pm (doc).

- [ ] [DATA] P0. **Extend `sports_closeout_exchange_fixed_odds_fork_2026_07_25.md`'s venue→class mapping to cover all 19
      previously-"unmapped" venues** (BETONLINEAG, UNIBET, BETRIVERS, WILLIAMHILL, CASUMO, SPORT888, CORAL, PADDYPOWER,
      DRAFTKINGS, UNIBET_UK, SKYBET, BETSSON, FANDUEL, VIRGINBET, LIVESCOREBET, BETVICTOR, LADBROKES_UK, BOVADA, BETWAY,
      UNIBET_EU — 292,117 real `data_type=trades` shards / 51,291,778 rows, measured 2026-07-29, see the todo above) —
      classify each as EXCHANGE_ODDS or FIXED_ODDS (mirroring the already-executed 9-venue precedent), move the GCS
      objects, and only then let the fork plan's legacy-contract-retirement todo proceed. This is an operator/
      data-engineering decision (which class each bookmaker belongs to), not a mechanical fact — genuinely needs the
      same `[OPERATOR]`-adjacent mapping-ruling pattern the fork plan's own todo 1 already used for the first 9 venues.
      Repos: market-tick-data-service, unified-api-contracts, unified-trading-pm.

## Secondary, smaller finding (not this doc's main subject)

The `read_availability_index(..., filters=[("instrument_type","=","odds")])` pushdown-filtered read returned an
implausible 20,785-entry, all-`KALSHI`, all-`0`-row_count result — inconsistent with the client-side-filtered result
above (which shows real bookmaker data). This looks like a pyarrow row-group pushdown-filter bug or a schema/dtype
mismatch on the `instrument_type` column for filtered reads specifically, not a data problem. Not root-caused here;
worth a follow-up if anyone else hits a suspiciously narrow/empty result from a filtered `read_availability_index` call
on this bucket.

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid (sports tranche) — the sole open `[DATA] P0` self-identifies as an
  operator call — 'classify each as EXCHANGE_ODDS or FIXED_ODDS ... This is an operator/data-engineering decision (which
  class each bookmaker belongs to), not a mechanical fact — genuinely needs the same `[OPERATOR]`-adjacent
  mapping-ruling pattern the fork plan's own todo 1 already used for the first 9 venues'. BIG FINDING re-surfaced in
  this run's report: 19 venues / 292,117 shards / 51,291,778 rows would be silently orphaned if
  `sports_closeout_exchange_fixed_odds_fork_2026_07_25.md`'s legacy-contract retirement proceeds before this mapping
  lands
