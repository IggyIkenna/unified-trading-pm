---
doc_type: issue
title: >-
  SPORTS odds expectation gap — the manifest asserts confirmed-absence for (venue, league) pairs that have NEVER
  captured anything (296/1,626 = 18.2%, incl. 8 venues 100% dead across 33 leagues each), inflating the sports coverage
  denominator (+ case-duplicate odds data_types)
summary: >-
  Sports odds are recorded at (venue, league_id, date) grain under data_type=trades with instrument_type=odds, sourced
  from api_football (1,396,916) / odds_api (388,852) / polymarket_clob (20,785). Measured in prod 2026-07-20: of 1,626
  (venue, league) pairs, 296 (18.2%) have NEVER had a single `captured` row, yet are enumerated and marked
  empty_confirmed — i.e. the manifest asserts "we looked and confirmed there is nothing" for bookmaker/competition
  combinations that appear to produce no data at all. EIGHT venues are 100% dead across 33 leagues each (BETFAIR,
  PROPHETX, KALSHI, ODDS_API, ONEXBET, POLYMARKET, NOVIG, BETOPENLY — note KALSHI/POLYMARKET are PREDICTION venues and
  ODDS_API is an aggregator SOURCE, not a bookmaker); MATCHBOOK is 20.3% dead and PINNACLE 17.2% dead (plausibly
  competitions they do not price); SPORT888 and SMARKETS are 0% dead. Overall capture_status across the 1,806,553
  odds-carrying rows: empty_confirmed 1,267,113 / captured 427,163 / attempted_failed 112,277. There is no per-(venue,
  league) coverage declaration gating the expected universe. Separately the data_type vocabulary carries case-duplicates
  splitting one logical stream across two keys — ODDS (22,145) vs odds (20,331), ODDS_SNAPSHOT vs odds_snapshot,
  ODDS_MOVEMENT vs odds_movement — plus odds_horizon_bucket (124,294) coexisting with odds_horizon_bucket_15m/1h/4h/1d.
  NOTE an earlier version of this issue mis-diagnosed these rows as impossible order-book trades via
  AUDITED_BOOKMAKERS.is_exchange; that framing is WRONG (instrument_type=odds) and is corrected in the body banner.
status: open
nature: issue
asset_group: [sports]
stage: [meta]
repos: [unified-api-contracts, market-tick-data-service]
scope: [engineer, admin]
tags: [sports, shard-enumeration, expected-universe, honest-coverage, data-completeness, manifest, cartesian-blowup]
related: [aster_capture_broken_coverage_and_completeness_2026_07_20.md]
created: 2026-07-20
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: design
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 0.9
assigned_role: data-pipeline
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
source:
  [
    "operator question 2026-07-20: 'shard counts for sports 308 why — do we expect shards for each bookmaker? only makes
    sense for odds. are we manifest recording odds per bookmaker where not all bookmakers even exist for all odds?'",
  ]
---

# SPORTS shard enumeration: cartesian blowup + false honest-absence

> **⚠️ CORRECTION 2026-07-20 — the original framing of this issue was WRONG. Read this first.**
>
> The first version of this doc claimed the 1,806,553 `data_type=trades` rows were impossible ORDER-BOOK trades for
> fixed-odds sportsbooks (reasoning from UAC `AUDITED_BOOKMAKERS.is_exchange`). **That is incorrect.** Those rows carry
> `instrument_type=odds` (1,806,527 of 1,806,553) and come from `source=api_football` (1,396,916) / `odds_api` (388,852)
> / `polymarket_clob` (20,785) — i.e. the `trades` data_type is carrying **ODDS**, not an exchange trade tape. The
> `is_exchange` lens does not apply, and no claim in this doc should be built on it.
>
> **What IS measured and does hold** (prod, 2026-07-20), and what the operator's question was really about — whether we
> record odds per bookmaker where a bookmaker does not cover that competition at all:
>
> - Grain is (venue, league_id, date). 35 venues x 93 leagues appear.
> - **296 of 1,626 (venue, league) pairs — 18.2% — have NEVER had a single `captured` row.**
> - **EIGHT venues are 100% dead** (33 leagues each, zero captures ever): BETFAIR, PROPHETX, KALSHI, ODDS_API, ONEXBET,
>   POLYMARKET, NOVIG, BETOPENLY. (KALSHI/POLYMARKET are PREDICTION venues; ODDS_API is an aggregator SOURCE, not a
>   bookmaker — both smell like enumeration errors, pending verification.)
> - MATCHBOOK 16/79 leagues dead (20.3%), PINNACLE 16/93 dead (17.2%) — plausibly competitions they do not price.
> - SPORT888 and SMARKETS are 0% dead.
> - Overall `capture_status`: empty_confirmed 1,267,113 / captured 427,163 / attempted_failed 112,277.
>
> So the concern stands — we appear to assert confirmed-absence daily for (venue, league) combinations that have never
> produced data — but the mechanism is a **(venue x league) expectation gap**, NOT an is_exchange/order-book mismatch.
>
> A second correction: `scripts/pipeline_e2e_check.py::enumerate_mtds_shards` (the source of the 308) is a **smoke-sweep
> scope** whose own comment says the cross-product is DELIBERATE for non-PREDICTION/TRADFI groups ("probing beyond the
> expected set is part of the sweep's over/under-declaration coverage"). It is therefore probably NOT the writer of
> these manifest rows. The real writer is under investigation; do not "fix" the smoke script assuming it is the cause.
>
> Sections below this banner predate the correction and are retained only for the measured numbers they cite; their
> is_exchange-based reasoning is superseded.

The operator asked why SPORTS enumerates 308 shards and whether per-bookmaker recording is meaningful given not every
bookmaker offers every market. The concern is valid; the original explanation below is not.

## What the enumeration produces

`enumerate_mtds_shards("SPORTS", …)` → **28 venues x 11 data_types = 308**, an unfiltered cartesian product.

- **Venues (28):** BETFAIR, BETFAIR_EX_EU, BETFAIR_EX_UK, BETFAIR_SB_UK, BETMGM, BETONLINEAG, BETOPENLY, BETRIVERS,
  BETSSON, BETVICTOR, BETWAY, BOVADA, CASUMO, CORAL, DRAFTKINGS, FANDUEL, LIVESCOREBET, MATCHBOOK, NOVIG, ODDS_API,
  ONEXBET, PADDYPOWER, PINNACLE, PROPHETX, SKYBET, UNIBET, VIRGINBET, WILLIAMHILL.
- **Data types (11):** ODDS, odds, odds_snapshot, odds_movement, odds_horizon_bucket, arbitrage_opportunity, markets,
  outcomes, settlements, trades, trades_inplay.

## Why it is wrong

1. **`trades` / `trades_inplay` for fixed-odds sportsbooks is structurally impossible.** UAC's `AUDITED_BOOKMAKERS`
   (registry/_odds_api_maps.py) carries an `is_exchange` flag and marks only **2 of 21** audited venues as exchanges
   (`BETFAIR_EX`, `MATCHBOOK`). A sportsbook quotes prices; it has no order book and no trade tape. The enumerator emits
   trades cells for all 28 anyway.
2. **`SPORTS_CAPABILITIES` declares 15 SOURCES, not 28 venues** — the source-level capability declaration is not
   consulted when expanding the venue axis.
3. **Cross-bookmaker derived types are emitted per-bookmaker.** `arbitrage_opportunity` is by definition a cross-venue
   construct; per-venue cells are not meaningful.
4. **Case-duplicate data_type vocabulary** splits one logical stream in two: `ODDS`/`odds`,
   `ODDS_SNAPSHOT`/`odds_snapshot`, `ODDS_MOVEMENT`/`odds_movement`; plus `odds_horizon_bucket` coexisting with
   `odds_horizon_bucket_{15m,1h,4h,1d}`.
5. **Coverage is not universal even where it IS meaningful** — no bookmaker prices every fixture or market, so a
   bookmaker x odds cell is only expected where that book actually covers the event. There is no per-(venue,
   fixture/market) expectation gate.

## Prod impact (measured 2026-07-20)

`market-data-tick-sports-prd-central-element-323112/_index/availability_index.parquet`:

- **1,974,679** total rows; **1,806,553** are `data_type=trades`.
- Of those trades rows: **1,267,113 `empty_confirmed`**, 427,163 `captured`, 112,277 `attempted_failed`.
- Per-venue trades rows include **PINNACLE 155,797** (is_exchange=False — impossible), BETFAIR 139,620, ONEXBET 139,620,
  BETOPENLY 139,524, NOVIG 139,524, PROPHETX 139,524.
- Case-duplicates present as real rows: `ODDS` 22,145 vs `odds` 20,331.

`empty_confirmed` means "we looked and confirmed there is no data". Asserting that for a cell that cannot physically
exist is false honest-absence: it inflates the coverage denominator, makes sports coverage look worse than reality, and
hides genuine gaps in the cells that DO matter.

## Fix direction (needs operator scope call — changes the coverage denominator)

1. **Gate the venue x data_type expansion on an applicability matrix**: `trades`/`trades_inplay` only where
   `is_exchange`; `arbitrage_opportunity` (and other cross-venue derivations) at asset-group/derived grain, not per
   bookmaker; odds-family types only for venues that actually publish odds via a declared source.
2. **Canonicalise the data_type vocabulary** (kill the ODDS/odds case-duplicates and reconcile `odds_horizon_bucket` vs
   its `_15m/_1h/_4h/_1d` variants) — one logical stream, one key.
3. **Add a per-(venue, market) expectation gate** so a bookmaker is only expected where it covers the event, instead of
   assuming universal coverage.
4. **Purge the false rows** once (1) lands, mirroring the ASTER CAS cleanup: remove `empty_confirmed` rows for
   impossible cells (consolidator paused, generation-matched write), leaving `captured` rows untouched.

## Guard note

`tests/unit/test_pipeline_e2e_prediction_canonical.py::test_rule11_per_ag_shard_counts_byte_unchanged` pins SPORTS
at 308. That pin tracks current enumeration output — it is NOT an endorsement. When the enumeration is corrected the pin
must come DOWN. Do not blindly re-raise it (this issue exists because a re-pin was about to do exactly that).
