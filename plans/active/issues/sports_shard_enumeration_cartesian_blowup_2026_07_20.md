---
doc_type: issue
title: >-
  SPORTS odds sentinel expectation axis is disconnected from the Odds-API request list — 5 category-derived keys vs a
  hardcoded 23-key bookmakers= list sharing only PINNACLE/MATCHBOOK, so 3 keys can never capture (418,860
  structurally-false rows) and 21 requested books can never be recorded missing
summary: >-
  VERIFIED by a 7-agent audit with an adversarial refutation pass (2026-07-20, confidence high). Sports odds are written
  by engine/orchestrator/sentinels.py (_emit_sports_v2_sentinels :283 / v1 :367), NOT by pipeline_e2e_check.py. ROOT
  CAUSE — the sentinel expectation axis and the actual request list are two different sets that nobody reconciles.
  venue_fetch.py:132 `_expected_sports_bookmakers()` derives scope from UAC venue CATEGORIES and returns exactly 5 keys
  (BETFAIR, MATCHBOOK, ODDS_API, ONEXBET, PINNACLE), while odds_api_adapter.py:114-149 sends a hardcoded 23-key
  `bookmakers=` list. They intersect on only PINNACLE and MATCHBOOK. Consequences, both measured — (a) BETFAIR(bare),
  ODDS_API and ONEXBET are never requested so they can never capture, yet are fanned out into the expectation universe:
  418,860 structurally-false rows (ONEXBET alone 139,620, 100% empty_confirmed, never retried); (b) 21 books that ARE
  requested on every call can never be recorded as missing, so their gaps are invisible — this is why venues like
  SPORT888/SMARKETS look "0% dead": they are UNMEASURED, not healthy. Also confirmed: a bare-vs-suffixed BETFAIR grain
  mismatch (sentinel writes BETFAIR, capture writes BETFAIR_EX_UK/EX_EU/SB_UK) whose dedup does not normalize, yielding
  ~15,570 provably-false attempted_failed rows; and a fabricated fetch-evidence helper (sentinels.py:97-104) that
  synthesizes http_status=200/rows_in_response=0 for a book never individually requested, defeating
  UnprovenHonestAbsenceError on the v1 path. REFUTED during verification (do not act on): that no per-bookmaker fetch
  occurs (one provider call returns a bookmaker_key column and IS grouped per book, so PINNACLE/MATCHBOOK zero-rows are
  DEFENSIBLE honest absence); that the coverage oracle's circularity is the root cause; and that the ODDS/odds case
  duplicates are a live bug (they are frozen legacy, both cohorts stop 2026-04-14, and GCS holds only lowercase `odds`
  directories — the uppercase rows are manifest-only phantoms). PREFERRED REMEDIATION is NOT a purge: adding
  EXPECTED_BOOKMAKER_NO_LEAGUE_COVERAGE + EXPECTED_PAUSED_LEAGUE to UAC OUT_OF_COVERAGE_WINDOW_REASONS (their siblings
  are already there — the omission IS the classification defect) reclassifies 1,066,231 rows out of both numerator and
  denominator, reversibly, with zero GCS writes; sports honest coverage moves 94.31% -> 87.64%, which is operator-facing
  and therefore gated on an operator decision.
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

---

# VERIFIED DIAGNOSIS + FIX PLAN (7-agent audit with adversarial verification, 2026-07-20)

> Confidence: **high**. This supersedes ALL analysis above the line. The audit refuted several of its own headline
> claims during verification — the surviving root cause is stated first.

## ROOT CAUSE (single sentence)

The sentinel expectation axis is derived from UAC venue _categories_ (`_expected_sports_bookmakers()` -> 5 keys) while
the actual Odds-API request carries a hardcoded 23-key `bookmakers=` list. The two sets share only `PINNACLE` and
`MATCHBOOK`, so 3 keys can NEVER capture (418,860 structurally-false rows) and 21 requested books can NEVER be recorded
as missing (invisible gaps).

## What adversarial verification REFUTED (do NOT act on these)

- REFUTED -- THE HEADLINE CLAIM THAT empty_confirmed IS FABRICATED ACROSS THE BOARD ('no per-bookmaker fetch is ever
  performed', 'roughly 1.06M rows assert honest absence for cells never fetched'). This is materially wrong about how
  the Odds API works. venue_fetch.py:695 issues ONE provider call whose response carries a bookmaker_key column, and
  captures are produced by records_df.groupby(['bookmaker_key','league_id','fixture_id']). The aggregator returns ALL
  requested bookmakers in that single response. So for any bookmaker actually in the request, its absence from the
  response IS a genuine observation of absence -- exactly the operator's alternative hypothesis ('we asked the
  aggregator for this league-date and it returned nothing'). The per-bookmaker fan-out is a legitimate pattern, not a
  fabrication. What matters is not whether each book was individually requested (none are, by design) but whether it was
  in the request list at all.
- REFUTED -- 'FABRICATED HONEST-ABSENCE PROOF affects all 200,864 SOURCE_RETURNED_ZERO rows'. Scope is overstated and
  the wrong path is cited. In the v2 fixture-level path (the dominant one), SOURCE_RETURNED_ZERO is emitted via
  `writer_manifest.record_zero_rows(..., was_expected=True)` at sentinels.py:325 with NO fetch_evidence at all -- the
  code comment at :321-324 explicitly notes this routes to attempted_failed and requires no proving evidence. The
  `_reached_empty_fetch_evidence` synthesis (sentinels.py:97-104) appears only on the v1 season-calendar fallback path
  at :443. The claim conflated two different branches.
- REFUTED -- 'ONEXBET is an INTENTIONAL mechanism, honestly reason-coded, so this is not a false-absence bug; it is only
  a denominator-inflation question.' This is wrong, and the adapter proves it. `onexbet` is NOT in
  `_HISTORICAL_BOOKMAKERS` (odds_api_adapter.py:114-147), the explicit 23-key `bookmakers=` list actually sent to the
  API. 1xBet is never requested, so it can never appear in a response. Its 139,620 empty_confirmed rows assert the
  aggregator returned nothing for a bookmaker that was never asked for. That is a FALSE honest-absence claim, identical
  in kind to bare BETFAIR -- not a defensible reason-coded absence.
- REFUTED (NEW ROOT CAUSE, sharper than either sub-report reached) -- the defect is NOT 'the coverage oracle is
  circular' nor 'league-alias vocabulary mismatch'. It is that the expectation axis is disconnected from the
  `bookmakers=` request list, and it is wrong in BOTH directions. Measured set comparison of the 23 requested keys
  against the 5-key sentinel scope and against the manifest: (a) IN SCOPE BUT NEVER REQUESTED =
  ['BETFAIR','ODDS_API','ONEXBET'] -> 418,860 structurally-impossible rows, 0 captured, ever; (b) REQUESTED BUT NEVER
  EXPECTATION-TRACKED = 21 books
  ['BETFAIR_EX_EU','BETFAIR_EX_UK','BETFAIR_SB_UK','BETONLINEAG','BETRIVERS','BETSSON','BETVICTOR','CASUMO','CORAL','DRAFTKINGS','FANDUEL','LADBROKES_UK','LIVESCOREBET','PADDYPOWER','SKYBET','SMARKETS','SPORT888','UNIBET','UNIBET_UK','VIRGINBET','WILLIAMHILL']
  -> these are fetched on every single call yet can never be recorded as missing. Only PINNACLE and MATCHBOOK are both
  requested AND enumerated. Decisively: REQUESTED venues with ZERO captures = NONE (empty set). Every book that is
  actually asked for does capture. So the entire 'dead venue' phenomenon is explained by non-requested keys, NOT by
  bookmakers declining to price leagues.
- REFUTED -- 'PINNACLE 16/93 and MATCHBOOK 16/79 dead leagues are false honest-absence claims from alias misses.' Partly
  right about the alias mismatch, but the conclusion does not follow: pinnacle and matchbook ARE in the `bookmakers=`
  request list, so their zero-row cells reflect a real probe of a real book. Their 188,041 empty_confirmed rows are
  DEFENSIBLE honest absence -- the operator's alternative hypothesis (a) holds for exactly these two venues. Any
  remediation must not sweep them in with the 1.1M structurally-false rows.
- REFUTED -- 'the case duplicates are a LIVE bug.' They are FROZEN legacy. Measured per-data_type date ranges: ODDS and
  odds both span 2020-06-01..2026-04-14 and STOP there, while `trades` runs to 2026-06-27. written_at for both cohorts
  occurs on only three dates (2026-04-08: 23 rows, 2026-04-13: 526, 2026-07-13: 21,596/19,782 = the manifest rebuild
  restamp). Every live-code reference to an uppercase 'ODDS' data_type is in a migration/rebuild script
  (migrate_sports_canonical_v9.py, rebuild_sports_manifest_v9.py, normalize_sports_mtds_data_type_case_2026_06_25.py,
  migrate_sports_instruments_legacy_gap_2026_07_13.py) -- none in the live writer. This is a live DATA defect in the
  served index (the duplicate rows still double-count any data_type-grouped denominator), but NOT an actively-writing
  bug. The distinction changes the fix from 'stop the writer' to 'one-off dedupe'.
- REFUTED (NEW) -- the prior report treated the ODDS/odds split as duplicated physical shards and left canonical
  direction contested. Measured against GCS: on day=2020-07-21, day=2023-05-10 and day=2026-04-14 the bucket contains
  ONLY `data_type=odds` (5, 5 and 2 objects respectively) and ZERO `data_type=ODDS` directories, while the manifest
  carries BOTH spellings for those same days (2020-07-21: 6 uppercase + 5 lowercase). So uppercase ODDS is a
  MANIFEST-ONLY PHANTOM with no backing objects; lowercase matches disk. This inverts the practical conclusion:
  codex/02-data/sports-data-types-catalog.md:32-41 K0-DECISION(b) 2026-07-18 declares UPPER canonical for sports, which
  contradicts the physical estate. The phantom rows should be dropped, not the lowercase ones -- and the K0 decision
  needs operator re-confirmation before any normalizer is re-pointed.
- REFUTED -- 'written_at differs by ~41 microseconds (ODDS 2026-04-13T02:10:21.383459 vs odds ...383500), proving the
  twins were emitted microseconds apart in the same pass and are therefore not benign legacy.' The maximum written_at
  for both cohorts is 2026-07-13T23:56:41 (the rebuild), not 2026-04-13. The microsecond-adjacency describes rows
  written by a bulk rebuild pass iterating a data_type list, which is evidence FOR the rebuild-artifact explanation, not
  against the legacy explanation.
- REFUTED -- internal numerical contradiction between the sub-reports, resolved by my measurement. The 'dead' section
  reported EXPECTED_BOOKMAKER_NO_LEAGUE_COVERAGE 538,098 / EXPECTED_PAUSED_LEAGUE 369,272; the 'writer' and 'applic'
  sections reported 606,772 / 459,459. My groupby over the odds slice gives 606,772 / 459,459 (plus SOURCE_RETURNED_ZERO
  200,864, VENUE_FETCH_FAILED 94,127, and 385,402 blank). The 'dead' figures are wrong and should not be carried
  forward.
- WEAKENED -- 'prediction-venue rows are provably stale because their date range stops at 2026-06-20 while in-scope
  venues run to 2026-06-27.' The cited evidence does not prove it: PADDYPOWER, UNIBET, DRAFTKINGS, SKYBET, FANDUEL,
  CORAL and most other captured-only venues ALSO stop at 2026-06-20. The 2026-06-27 tail is unique to the five
  enumerated scope keys precisely because sentinels keep emitting past the last capture. The conclusion (stale residue
  predating the 2026-06-21 exclusion) is still probably correct -- the venues are verifiably out of the live scope today
  -- but it rests on the code filter, not on the date gap.
- NEW FINDING NEITHER REPORT FLAGGED -- FREE-TEXT REASON TAXONOMY VIOLATIONS in the odds slice. The error_reason column
  contains full English sentences as values, e.g. "record_empty(reason=SOURCE_RETURNED_ZERO) rejected:
  instruments-service catalog says 'trades' was ALIVE on MATCHBOOK/2024-02-08. Use
  record_failed(EmptyFromLiveInstrumentError(...)) instead -- this is a real fetch failure, not honest absence." A
  rejection diagnostic has been persisted as the reason code itself. This is the class tracked by
  plans/active/issues/sports_rebuild_v9_free_text_reason_taxonomy_rejection_2026_07_13.md, still present in the live
  index and breaking any closed-set reason consumer.
- NEW FINDING NEITHER REPORT FLAGGED -- FOUR VENUES CAPTURE DESPITE NOT BEING REQUESTED: BETMGM (988), BETWAY (1,226),
  BOVADA (1,419), UNIBET_EU (34), all dated 2025-07-31..2025-12-31. None is in the `bookmakers=` list. `betway` is
  EXPLICITLY EXCLUDED at odds_api_adapter.py:105 for corrupt data ('4-6% price diff vs OddsPapi', validated 2026-03-28),
  yet 1,226 captured rows exist. Either a second ingest path bypasses the audited bookmaker list or the exclusion
  post-dates the data. Worth its own check before these rows feed features.
- ANSWER TO THE OPERATOR'S QUESTION, corrected: YES we record shards per bookmaker, and yes a per-(bookmaker,league)
  applicability gate already exists and is consulted -- so the premise 'not all bookmakers exist for all odds' is
  already handled and is NOT the failure. NO it does not work, but for a different reason than either sub-report gave:
  the expectation universe is a 5-key static list that shares only 2 keys with the 23-key list actually sent to the API.
  Three enumerated keys can never be captured (418,860 false rows) and twenty-one requested books are never
  expectation-tracked (their gaps are invisible). Fix = derive the sentinel scope FROM the adapter's `bookmakers=` list
  (odds_api_adapter.py:114) rather than from UAC venue categories, so the expected universe equals the requested
  universe by construction. That single change removes the phantom axes and makes the 21 unmeasured books measurable,
  without touching the league gate that already works.

# Sports odds manifest — ordered fix plan

**Repos:** `market-tick-data-service` (MTDS), `unified-api-contracts` (UAC), `unified-trading-pm` (codex/issues),
`instruments-service` (coverage formula), `deployment-api` (denominator). **Root cause (single sentence):** the sentinel
expectation axis is derived from UAC venue _categories_ (`_expected_sports_bookmakers()` → 5 keys) while the actual
Odds-API request carries a hardcoded 23-key `bookmakers=` list — the two sets share only `PINNACLE` and `MATCHBOOK`, so
3 keys can never capture (418,860 structurally-false rows) and 21 requested books can never be recorded as missing.

Verified anchors used below (re-read at execution time):

- `market-tick-data-service/market_tick_data_service/market_interface/adapters/sports/odds_api_adapter.py:114-149` —
  `_HISTORICAL_BOOKMAKERS`, 23 keys; `:150` `_LIVE_BOOKMAKERS = _HISTORICAL_BOOKMAKERS`; sent at `:296`, `:337`, `:549`,
  `:791`. Exclusion rationale (betway/boylesports/leovegas) at `:103-107`.
- `market-tick-data-service/market_tick_data_service/engine/orchestrator/venue_fetch.py:129`
  `_SPORTS_TIER2_BOOKMAKER_CATEGORIES`, `:132-146` `_expected_sports_bookmakers()`, `:101` `_LEAGUE_PARTITIONED_VENUES`,
  `:695` `_process_sports_venue_with_leagues`.
- `market-tick-data-service/market_tick_data_service/engine/orchestrator/sentinels.py:200`
  `_emit_sports_tier2_sentinels`, `:281` `_emit_sports_v2_sentinels`, `:301-304` dedup, `:319-337` coverage branch,
  `:340-362` `EXPECTED_PAUSED_LEAGUE`, `:365` `_emit_sports_v1_sentinels`, `:97-104` `_reached_empty_fetch_evidence`.
- `unified-api-contracts/unified_api_contracts/canonical/crosscutting/_honest_coverage_empty_reasons.py:514`
  `OUT_OF_COVERAGE_WINDOW_REASONS`, `:556` `WITHIN_WINDOW_EXPECTED_ABSENCE_REASONS`, `:185`
  `EXPECTED_BOOKMAKER_NO_LEAGUE_COVERAGE`.
- `unified-api-contracts/unified_api_contracts/registry/sports_bookmaker_league_coverage.py:82-95`
  `_normalize_bookmaker`, `:123-145` `is_bookmaker_league_covered`.

---

## Part 1 — Code fixes that stop NEW false rows

Do these first and in order. Steps 1.1–1.2 alone eliminate every structurally-impossible row going forward.

### 1.1 Make the requested-bookmaker list a first-class exported contract (MTDS)

**File:** `market_tick_data_service/market_interface/adapters/sports/odds_api_adapter.py:114-150` **Change:** keep the
curated list, but stop storing it only as a pre-joined comma string. Introduce a module-level `Final[tuple[str, ...]]`
of the 23 lowercase keys and derive the wire strings from it:

```python
REQUESTED_ODDS_API_BOOKMAKERS: Final[tuple[str, ...]] = ("pinnacle", "betfair_ex_uk", ...)  # 23 keys, order preserved
_HISTORICAL_BOOKMAKERS = ",".join(REQUESTED_ODDS_API_BOOKMAKERS)
_LIVE_BOOKMAKERS = _HISTORICAL_BOOKMAKERS
```

Add a public accessor `expected_odds_api_venue_keys() -> list[str]` returning
`sorted(k.upper() for k in REQUESTED_ODDS_API_BOOKMAKERS)` — the uppercase form matches the venue column written by
`venue_fetch.py:695`'s `groupby(["bookmaker_key", ...])`. **Test:**
`tests/market_interface/unit/sports/test_odds_api_bookmaker_scope.py` — assert
`len(REQUESTED_ODDS_API_BOOKMAKERS) == 23`, no duplicates, all lowercase, the excluded set
`{"betway","boylesports","leovegas","leovegas_se"}` is disjoint from it, and
`_HISTORICAL_BOOKMAKERS.split(",") == list(REQUESTED_ODDS_API_BOOKMAKERS)`. **Verification:**
`cd market-tick-data-service && bash scripts/quality-gates.sh --no-fix`; the wire string is byte-identical to today
(`python -c` diff against the current literal before/after).

### 1.2 Derive the sentinel scope FROM the request list, not from UAC categories

**File:** `market_tick_data_service/engine/orchestrator/venue_fetch.py:113-146` **Change:** replace the body of
`_expected_sports_bookmakers()` with `return expected_odds_api_venue_keys()` (import from the adapter, or better: move
`REQUESTED_ODDS_API_BOOKMAKERS` into UAC as `ODDS_API_REQUESTED_BOOKMAKERS` and have both the adapter and this function
read it, so the tier/import rules aren't bent — MTDS orchestrator importing MTDS market_interface is fine, but UAC is
the cleaner SSOT home). Delete `_SPORTS_TIER2_BOOKMAKER_CATEGORIES` (`:129`) and the now-dead
`get_expected_bookmakers`/`_is_prediction_market_venue` filter — the prediction-venue exclusion becomes structural (they
were never in `bookmakers=`). Rewrite the stale comment block at `:110-128`: the "12 × 33 = 396" figure is wrong twice
over (real scope was 5, new scope is 23; `23 × 33 = 759` pairs/date before season filtering).

**Net effect, measured:** removes `BETFAIR` (bare), `ODDS_API`, `ONEXBET` from the expectation universe → stops ~418,860
rows/rebuild that are 0-captured by construction. Adds expectation tracking for 21 books that are fetched on every call
and currently invisible when they gap.

**Test:** `tests/unit/test_sports_sentinel_scope.py`:

1. `set(_expected_sports_bookmakers()) == {k.upper() for k in REQUESTED_ODDS_API_BOOKMAKERS}` — the two sets are equal
   **by construction**, and this is the regression lock.
2. Assert `"BETFAIR" not in scope` and `{"BETFAIR_EX_UK","BETFAIR_EX_EU","BETFAIR_SB_UK"} <= scope` (bare-key phantom
   cannot return).
3. Assert `"ODDS_API" not in scope` (aggregator stays on the provider axis only) while
   `_LEAGUE_PARTITIONED_VENUES == frozenset({"ODDS_API"})` is untouched.
4. Assert `"ONEXBET" not in scope`.
5. Assert no member of UAC `PREDICTION_MARKET_VENUES` (uppercased) is in scope.

**Verification:** run the sentinel emitter against a fixture day with a canned Odds-API response and assert the emitted
`venue` set ⊆ scope; then a dry-run over one real prod day and confirm zero rows are emitted for
`BETFAIR`/`ODDS_API`/`ONEXBET`.

### 1.3 Normalize the capture-dedup key so captures actually suppress sentinels

**File:** `sentinels.py:301-304` (`if (bm, _canon_lid, _fid_str) in captured_sports_shards: continue`) and the parallel
league-pair check at `:344-347`. **Change:** after 1.2 the bare/suffixed grain mismatch is mostly gone, but the dedup
still compares raw strings while `is_bookmaker_league_covered` normalizes (`sports_bookmaker_league_coverage.py:82-95`).
Make **one** grain canonical: compare on the exact captured venue key on both sides, and **remove the base-key union
from the coverage lookup** in the sentinel path (call a new `is_bookmaker_league_covered_exact()` that does not fold
suffixes). Rationale: the fold is what let bare `BETFAIR` resolve "covered" on 50 leagues and manufacture 15,570 false
`attempted_failed` rows. **Test:** unit test asserting
`is_bookmaker_league_covered_exact("BETFAIR", "K_LEAGUE_1") is False` while
`is_bookmaker_league_covered_exact("BETFAIR_EX_UK", <a league in its map>) is True`; plus an emitter test where a
capture under `BETFAIR_EX_UK` suppresses the sentinel for that exact key. **Verification:** re-emit one prod day; assert
`attempted_failed` count for any venue with ≥1 capture on that (league, date) is 0.

### 1.4 Delete the fabricated fetch-evidence helper on the v1 path

**File:** `sentinels.py:97-104` (`_reached_empty_fetch_evidence`) and its call site at `:443`. **Change:** the helper
synthesizes `http_status=200, response_received=True, rows_in_response=0, endpoint=f"{venue}:{data_type}"` for a
bookmaker that was never individually requested, defeating `UnprovenHonestAbsenceError`. **Scope correction:** this
affects only the **v1 season-calendar fallback** path — the v2 path (dominant) uses
`record_zero_rows(was_expected=True)` at `:325` with no evidence and is fine. Replace the v1 call with the same
`record_zero_rows(..., was_expected=True)` branch, and delete the helper. **Test:**
`rg -n '_reached_empty_fetch_evidence'` returns 0 hits; a unit test asserting the v1 path emits `attempted_failed` (not
`empty_confirmed` with synthetic 200) for an uncovered book. **Verification:** on a fixture day forced down the v1 path,
assert every `empty_confirmed` row either carries real `FetchEvidence` or a structural reason (`EXPECTED_PAUSED_LEAGUE`
/ `EXPECTED_BOOKMAKER_NO_LEAGUE_COVERAGE`).

### 1.5 Add a fan-out invariant guard in the writer

**File:** `sentinels.py:200-230` (`_emit_sports_tier2_sentinels`, before the v1/v2 dispatch). **Change:** assert
`set(bookmakers_scope) == set(expected_odds_api_venue_keys())` and raise a loud `ValueError` on drift. This is the
machine guard that prevents the expectation universe from silently diverging from the request list again. **Test:**
monkeypatch the scope to inject a stray key; assert raise. **Verification:** QG green; one prod dry-run day completes
without the guard firing.

### 1.6 Investigate the 4 venues capturing without being requested

`BETMGM` (988), `BETWAY` (1,226), `BOVADA` (1,419), `UNIBET_EU` (34) have captured rows dated 2025-07-31..2025-12-31 yet
appear in no `bookmakers=` list — and `betway` is **explicitly excluded for corrupt data** at
`odds_api_adapter.py:103-107`. Either a second ingest path bypasses the audited list, or the exclusion post-dates the
data. **Action:** trace with `rg -n 'bookmaker_key' market_tick_data_service/` and a GCS `written_at`/`service_name`
check on those rows. If a second path exists, route it through `REQUESTED_ODDS_API_BOOKMAKERS`. If the data predates the
exclusion, quarantine the 1,226 BETWAY rows before they reach features. **Verification:** either a code fix + test, or a
dated finding appended to the issue doc in step 4.4.

---

## Part 2 — Vocabulary canonicalisation

### 2.1 ⚠️ BLOCKED-OPERATOR-DECISION — do not run any case normalizer yet

The `ODDS`/`odds` (and `ODDS_SNAPSHOT`/`odds_snapshot`, `ODDS_MOVEMENT`/`odds_movement`) split is **frozen legacy, not
an actively-writing bug** — both cohorts stop at 2026-04-14 while `trades` runs to 2026-06-27, and every live reference
to uppercase `ODDS` is in a migration/rebuild script, none in the live writer.

**The direction is contested and the codex is on the wrong side of the physical estate:**

- `unified-trading-pm/codex/02-data/sports-data-types-catalog.md:32-41` K0-DECISION(b), 2026-07-18, declares **UPPER**
  canonical for sports.
- But GCS holds **only** `data_type=odds` directories on day=2020-07-21, day=2023-05-10 and day=2026-04-14 (5, 5, 2
  objects; **zero** `data_type=ODDS`), while the manifest carries both spellings for those same days. **Uppercase `ODDS`
  is a manifest-only phantom with no backing objects.**

**Action:** put this to the operator (see 4.3). Do **not** touch `migrate_sports_canonical_v9.py:122-133` or
`scripts/normalize_sports_mtds_data_type_case_2026_06_25.py:44-51` until the direction is re-confirmed — both currently
point UPPER→lower, which K0 says is superseded, which GCS says is right.

### 2.2 Add a write-time closed-set guard on `data_type` (do this regardless of 2.1's outcome)

**File:** `unified-api-contracts/unified_api_contracts/registry/market_data_categories.py`,
`DATA_TYPES_BY_ASSET_GROUP["sports"]` (~`:211-245`) — currently registers **both** `"odds"` and `"ODDS"`. **Change:** do
not edit the members yet (blocked on 2.1), but add a QG check that the sports data_type set contains no case-variant
pairs, gated behind a `# TODO(K0-b)` skip until the decision lands. Then flip it live in the same commit as 2.1's
resolution. **Test:** `unified-api-contracts/tests/unit/test_sports_data_type_vocabulary.py` —
`assert len({d.lower() for d in DATA_TYPES_BY_ASSET_GROUP["sports"]}) == len(DATA_TYPES_BY_ASSET_GROUP["sports"])`.

### 2.3 Close the `(sports, odds)` hole in the instrument_type→data_type matrix

**File:** `market_data_categories.py:832-843` — the matrix has **no** `("sports","odds")` entry, yet prod writes
1,806,527 rows under exactly that pair. The neighbours (`fixture`, `exchange_odds`, `fixed_odds`, `prop`) are
self-labelled `# UNCERTAIN — sports-owner verify`. **Change:** add `("sports","odds"): {"trades", ...}` matching the
registered contract `CONTRACT_REGISTRY[("sports","odds","trades")]` at
`unified_api_contracts/internal/schemas/_sports_prediction_contracts.py:553`. Strip the `UNCERTAIN` labels on the
entries you can now confirm. **Test:** assert every `(asset_group, instrument_type)` key present in `CONTRACT_REGISTRY`
has a matrix entry containing that contract's `data_type`. **Verification:** UAC QG green; re-run
`unified-api-contracts/tests/unit/test_coverage_exclusions.py`.

### 2.4 Fix the codex↔UAC↔prod contradiction on `instrument_type`

**File:** `unified-trading-pm/codex/02-data/sports-data-types-catalog.md:5-6, 48-54, 99-101`. **Change:** the doc omits
`trades` from its 8 data types and prescribes `instrument_type=sports_market` — a value with **zero rows** in prod,
against `instrument_type=odds` on 91.5% of the manifest. Update the doc to match UAC + prod (`instrument_type=odds`,
`data_type=trades` is canonical and registered), or add a SUPERSEDED banner if the sports owner intends `sports_market`
as a target state — but then it needs a migration plan, not a silent doc claim. **Verification:** doc
`authoritative_for:` frontmatter still resolves; `rg 'sports_market' --glob '!.venv*'` shows only `taxonomy.py:44` and
the doc.

### 2.5 Free-text reason values in `error_reason` (existing issue, still live)

The odds slice contains full English sentences as reason values, e.g.
`"record_empty(reason=SOURCE_RETURNED_ZERO) rejected: instruments-service catalog says 'trades' was ALIVE on MATCHBOOK/2024-02-08. ..."`
— a rejection diagnostic persisted as the code itself. Tracked by
`unified-trading-pm/plans/active/issues/sports_rebuild_v9_free_text_reason_taxonomy_rejection_2026_07_13.md`.
**Change:** add a writer-side assertion that `error_reason ∈ EMPTY_CONFIRMED_REASONS ∪ <classified error codes>` and
raise on anything else; the diagnostic belongs in a log line, not the column. Fold the existing rows into the Part-3
remediation as a **relabel**, not a delete.

---

## Part 3 — Manifest remediation for existing rows

### 3.0 ⛔ PREREQUISITE — nothing in Part 3 executes until Part 4 closes

Every remediation option moves the sports coverage number, and the two live formulas move in **opposite directions**.
Sequencing Part 3 before Part 4 ships a coverage regression to the operator's dashboard labelled as a cleanup.

### 3.1 PREFERRED INSTRUMENT — reason reclassification, not deletion (one-line, reversible, zero GCS writes)

**File:** `unified-api-contracts/unified_api_contracts/canonical/crosscutting/_honest_coverage_empty_reasons.py:514`
(`OUT_OF_COVERAGE_WINDOW_REASONS`). **Change:** add `EXPECTED_BOOKMAKER_NO_LEAGUE_COVERAGE` and `EXPECTED_PAUSED_LEAGUE`
to the frozenset. Both are permanent/structural absences and their siblings `EXPECTED_INSTRUMENT_NOT_LISTED`,
`EXPECTED_PRE_SEASON`, `EXPECTED_POST_SEASON` are **already** in it — their omission is the actual classification
defect. `WITHIN_WINDOW_EXPECTED_ABSENCE_REASONS` (`:556`) is derived, so it updates automatically. **Measured effect:**
clips 1,066,231 rows from **both** numerator and denominator; sports honest coverage 94.31% → 87.64%. No prod-bucket
write, no row destroyed, fully revertible by removing two set members. **Test:** extend
`unified-api-contracts/tests/unit/test_honest_coverage.py:340-341` (the partition invariant already asserted there) plus
an explicit membership test for the two new reasons and a golden-number test on a synthetic sports row set.
**Verification:** `bash scripts/quality-gates.sh` in UAC; then recompute `compute_honest_coverage` over a local copy of
the prod index and assert 87.64% ±0.01pp.

### 3.2 ⛔ NOT-TO-DO (as proposed) — bulk purge of the 923,952 / 1,136,624 dead-pair rows

**Marked NOT-TO-DO. Four independent grounds, all verified:**

1. **It inverts the operator-facing number.** `empty_confirmed` is numerator-credited by
   `_honest_coverage_logic.py:88-96` (via
   `deployment-api/deployment_api/services/data_status/coverage_metrics.py:404,412`, sports
   `coverage_semantics='event_driven'` at `:42`). A purge drops the dashboard 94.31% → 91.07% while
   instruments-service's `coverage.json` **rises** 84.08% → 88.79%.
2. **Resurrection is a physical fact, not a hazard.**
   `gs://market-data-tick-sports-prd-central-element-323112/_index/per_vm/_legacy_seed.parquet` exists (362,753 rows,
   22,675 of them dead-pair) and the consolidator re-merges it every cycle. A canonical-index-only purge self-reverts —
   the exact failure mode `features-service/scripts/sports/purge_stale_daylevel_failed_rows_2026_07_14.py` hit on its
   first `--apply`.
3. **Deletion is the wrong instrument for a classification bug** that a two-entry frozenset (3.1) fixes reversibly.
4. **Prod-bucket deletes are a human-only hard stop** (`codex/02-data/gcs-and-manifest-delete-safety-protocol.md`).

Plus: the root cause survives any purge — before Part 1 ships, the enumerator regenerates the rows on the next run.

**If and only if the operator later authorises deletion**, the candidate predicate is below. It is recorded for scoping,
not as authorisation:

```sql
LIVE_PAIRS := SELECT DISTINCT (venue, league_id)
              FROM UNION(_index/availability_index.parquet,
                         _index/per_vm/*.parquet)      -- UNION IS MANDATORY
              WHERE capture_status = 'captured'

PURGE_CANDIDATE(row) :=
      row.asset_group   = 'sports'
  AND row.capture_status = 'empty_confirmed'
  AND (row.venue, row.league_id) NOT IN LIVE_PAIRS
  AND row.error_reason IN ('EXPECTED_BOOKMAKER_NO_LEAGUE_COVERAGE',
                           'EXPECTED_PAUSED_LEAGUE')   -- withholds SOURCE_RETURNED_ZERO
  AND row.row_count IN (0, NULL)
```

Both clauses are load-bearing and empirically verified:

- **The UNION** — computing `LIVE_PAIRS` from the consolidated index alone misclassifies `('ODDS_API','')` as dead and
  would wrongly purge 340 rows that have captured data in `_index/per_vm/_legacy_seed.parquet`.
- **The `error_reason` filter** — it withholds the 175,246 dead-pair `SOURCE_RETURNED_ZERO` rows, which assert a proven
  probe under the PROOF-OF-HONEST-ABSENCE hard rule (`codex/02-data/availability-manifest-and-data-status.md:564-581`).
  If that proof is bogus the correct action is `reprobe_new_empty_confirmed.py` → `attempted_failed`, **never** erasing
  the evidence.

**Procedure if authorised (all steps mandatory, in order):**

1. Confirm the consolidator is **PAUSED** for the whole window — verify by state file, not by observing idleness.
2. Snapshot the canonical index **and every `_index/per_vm/*.parquet`** to `_index/purge_backups/<date>/`. **Never**
   write a `.bak.parquet` inside `_index/per_vm/` — `_read_and_merge_per_vm_shards` filters on `.endswith('.parquet')`
   with no `.bak` exclusion and will merge your backup back in.
3. Apply the predicate to **both** the canonical index and every per-VM shard in the same transaction; the manifest
   write is CAS — re-read and retry on conflict, never force.
4. Pre-notify on `coverage_drift.py` — a change of this magnitude fires per-`(calc, league_id)` drift alerts and will
   page as an incident otherwise.
5. Resume the consolidator and verify the post-purge row count **survives one full cycle** before declaring done. Re-run
   the count at T+1 cycle and T+24h.

### 3.3 Relabel pass for the 37,426 never-captured `attempted_failed` rows

These sit on pairs that never captured anything (dominated by bare-BETFAIR's 37,426 and the legacy prediction-venue
rows) and are provably false failure claims. A one-off relabel to honest absence is the right instrument — **not** a
gate, since Part 1 stops the source. **Precedent script to model on:**
`market-tick-data-service/scripts/relabel_sports_odds_no_coverage_2026_06_21.py`. **Constraint:** same
consolidator-pause + per-VM-union + `_index/purge_backups/` rules as 3.2. Relabel is reversible from the snapshot; it
does not delete rows, so it does **not** hit the human-only delete hard stop — but it **does** move the coverage number,
so it is still gated on Part 4. **Test:** dry-run diff report asserting the 67,206 `attempted_failed` rows that are
on-or-after their pair's first capture are **untouched** (genuine fetch failures — no gate should suppress them).

### 3.4 Drop the phantom uppercase `ODDS` manifest rows — BLOCKED on 2.1

22,145 uppercase `ODDS` rows have **no backing GCS objects** (verified on three sample days). They double-count any
`data_type`-grouped denominator. The 20,331 lowercase twins match disk. But dropping them contradicts codex
K0-DECISION(b), so this is blocked on the operator ruling in 4.3.

### 3.5 The 1,337 suffixed `odds_horizon_bucket_{15m,1h,4h,1d}` rows

Confirmed DEAD cohort (0 captured, ever) per `codex/02-data/sports-data-types-catalog.md:39-40`, and carrying a genuine
**axis shift**: `instrument_type` holds bookmaker names (`paddypower` 346, `pinnacle` 278, …) while `venue` holds
`FOOTBALL` — a sport, violating `_sports_prediction_contracts.py:15-16` which requires `venue` = the bookmaker. 0/1337
rows have `venue == instrument_type`, proving a shift not a duplication. **Action:** low priority, tiny blast radius.
Fold into 3.3's relabel pass or leave with a documented exclusion. Do **not** spin a separate migration for 1,337 rows.

---

## Part 4 — Operator scope decisions (blocking Part 3)

Present these together; they are coupled.

### 4.1 🔴 BIG FINDING — two contradictory honest-coverage formulas are live over the same rows

- `unified-api-contracts/.../_honest_coverage_logic.py:88-96` (what `deployment-api` runs, what the operator sees):
  numerator = `captured + (empty_confirmed − out_of_window) + expected_unattempted_known_empty` → **credits**
  `empty_confirmed`.
- `instruments-service/scripts/measure_honest_coverage.py:600-602` (what `coverage.json` → `HonestCoverageCard.tsx`
  shows): `reachable = captured + attempted_failed + expected_unattempted`, `coverage = captured/reachable` →
  **excludes** `empty_confirmed` entirely.
- `codex/02-data/honest-coverage-model.md:219-226` sides with the second.

They disagree by ~10pp on sports today and move in opposite directions under every remediation option. **This is a
cross-repo SSOT contradiction and a data-correctness finding independent of everything else in this plan.** Per the
CLAUDE.md triage rule it needs `plans/active/issues/` + operator notification **now**, and it must be settled before any
row is touched.

### 4.2 Which coverage semantics does sports want?

Three measured options, pick one:

| Option                                                              | Sports coverage | Rows written | Reversible         |
| ------------------------------------------------------------------- | --------------- | ------------ | ------------------ |
| **A** — add the 2 reasons to `OUT_OF_COVERAGE_WINDOW_REASONS` (3.1) | 94.31% → 87.64% | 0            | Yes, one line      |
| **B** — purge dead-pair rows (3.2)                                  | 94.31% → 91.07% | 923,952 del  | No                 |
| **C** — reclassify to `expected_unattempted`                        | 94.31% → 85.44% | ~1.1M mod    | Yes, from snapshot |

**Recommendation: A.** It is semantically defensible ("this bookmaker never lists this league" is exactly an out-of-life
cell, same class as the already-clipped `EXPECTED_INSTRUMENT_NOT_LISTED`), costs zero prod writes, and preserves every
row for audit. Note on C: sports currently has **zero** `expected_unattempted` rows (`capture_status.unique()` = 3
states only), so C activates downstream branches never exercised on this asset group.

### 4.3 Sports `data_type` case direction — codex vs the physical estate

K0-DECISION(b) (2026-07-18) says UPPER is canonical; GCS holds only lowercase directories with zero uppercase ones on
every sampled day. **Re-confirm or reverse K0(b) before any normalizer is re-pointed.** Both shipped normalizers
(`migrate_sports_canonical_v9.py:122-133`, `normalize_sports_mtds_data_type_case_2026_06_25.py:44-51`) point UPPER→lower
and neither ever completed.

### 4.4 Phase 6d — the sports venue-injection gap must land BEFORE any purge

`deployment-api/deployment_api/services/data_status/mtds.py::is_mtds_honest_coverage_target` **explicitly excludes
SPORTS** ("bookmaker axis is Phase 6d"). CeFi/TradFi/DeFi/PREDICTION get UAC-declared venues injected with zero manifest
rows so a fully-absent venue still renders at 0%. Sports does not — its denominator is manifest-derived from observed
venues only. **Purge the zero-capture venues and they vanish from the data-status UI instead of rendering an honest
0%**, reintroducing exactly the invisibility bug `manifest.py:856-861` documents having fixed elsewhere. Phase 6d is a
hard prerequisite for 3.2, and desirable before 3.3.

### 4.5 Issue-doc corrections to file

`unified-trading-pm/plans/active/issues/sports_shard_enumeration_cartesian_blowup_2026_07_20.md` needs a correction
banner:

- Its summary states _"There is no per-(venue, league) coverage declaration gating the expected universe."_ **FALSE** —
  `unified-api-contracts/unified_api_contracts/registry/sports_bookmaker_league_coverage.py` exists, is wired at
  `sentinels.py:321`, and is materialised on 606,772 prod rows. Strike the line.
- The reason-split figures `538,098 / 369,272` are wrong; the measured values are
  `EXPECTED_BOOKMAKER_NO_LEAGUE_COVERAGE 606,772 / EXPECTED_PAUSED_LEAGUE 459,459 / SOURCE_RETURNED_ZERO 200,864 / VENUE_FETCH_FAILED 94,127 / blank 385,402`.

---

## ⛔ NOT-TO-DO — premises that did not survive verification

Do not spend engineering time on any of these.

1. **"`empty_confirmed` is fabricated across the board — no per-bookmaker fetch is ever performed."** — **REFUTED.**
   `venue_fetch.py:695` issues one provider call whose response carries a `bookmaker_key` column; captures come from
   `records_df.groupby(["bookmaker_key","league_id","fixture_id"])`. The aggregator returns **all requested bookmakers**
   in that single response, so for a book that **is** in the request list, its absence from the response _is_ a genuine
   observation of absence. The per-bookmaker fan-out is a legitimate pattern. The defect is not "was each book
   individually requested" (none are, by design) — it is "was it in the request list at all."
2. **"Fabricated honest-absence proof affects all 200,864 `SOURCE_RETURNED_ZERO` rows."** — **REFUTED, scope overstated
   and wrong path cited.** The dominant v2 path emits via `record_zero_rows(..., was_expected=True)` at
   `sentinels.py:325` with **no** `fetch_evidence` — the comment at `:321-324` explicitly notes no proving evidence is
   required. `_reached_empty_fetch_evidence` appears **only** on the v1 fallback at `:443`. Fix is step 1.4, narrowly
   scoped.
3. **"The root cause is the circular coverage oracle."** — **REFUTED as the root cause.** The oracle _is_
   self-referential (`sports_bookmaker_league_coverage.py:3-7`: covered iff ≥1 captured row exists) and that is a real
   known floor worth documenting — but it is not what produces the dead venues. **Every book actually in the
   `bookmakers=` list captures; the set of requested-venues-with-zero-captures is EMPTY.** Do not rebuild the league
   gate; it works.
4. **"The league-alias vocabulary mismatch (16/33 leagues) is the root cause of MATCHBOOK 16 / PINNACLE 16 dead."** —
   **REFUTED as a defect.** `pinnacle` and `matchbook` ARE in the request list (`odds_api_adapter.py:132,133`), so their
   zero-row cells reflect a real probe of a real book. Their 188,041 `empty_confirmed` rows are **defensible honest
   absence**. The alias mismatch is real but cosmetic here; **do not sweep these two venues into any remediation** aimed
   at the structurally-false rows.
5. **"ONEXBET is intentional and honestly reason-coded — only a denominator-inflation question."** — **REFUTED, and
   inverted.** `onexbet` is **not** in `_HISTORICAL_BOOKMAKERS` (`odds_api_adapter.py:114-149`). It is never requested,
   so it can never appear in a response. Its 139,620 `empty_confirmed` rows assert the aggregator returned nothing for a
   book that was never asked for — a **false** honest-absence claim, identical in kind to bare BETFAIR. Step 1.2 removes
   it; it is not a "leave it, just note the denominator" case.
6. **"The case-duplicate rows are a LIVE writer bug — fix the writer."** — **REFUTED.** Frozen legacy: both cohorts stop
   at 2026-04-14 while `trades` runs to 2026-06-27; every uppercase-`ODDS` reference in live code is in a
   migration/rebuild script. **Do not go hunting for a writer to stop.** It is a one-off data dedupe (3.4), gated on
   4.3.
7. **"The 41-microsecond `written_at` gap proves the twins were emitted in the same live pass and are not legacy."** —
   **REFUTED.** Max `written_at` for both cohorts is `2026-07-13T23:56:41` (the rebuild), not 2026-04-13. Microsecond
   adjacency is evidence **for** the bulk-rebuild-artifact explanation, iterating a data_type list — not against it.
8. **"ODDS_API is a 100%-dead venue."** — **REFUTED.** It has **165,677 captured rows across 94 leagues** (306,416
   total). It is dead only on the bookmaker axis. It must be **excluded from every purge scope** — this is the same
   class of error as the original "impossible order-book trades" conclusion: a subset read as a total. Its legitimate
   provider axis (`_LEAGUE_PARTITIONED_VENUES`, `venue_fetch.py:101`) must not be touched by step 1.2.
9. **"Prediction-venue rows are provably stale because their dates stop at 2026-06-20 while in-scope venues run to
   2026-06-27."** — **WEAKENED, do not cite this evidence.** PADDYPOWER, UNIBET, DRAFTKINGS, SKYBET, FANDUEL and CORAL
   **also** stop at 2026-06-20; the 2026-06-27 tail is unique to the enumerated scope keys precisely because sentinels
   keep emitting past the last capture. The conclusion (stale residue predating the 2026-06-21 exclusion) is still
   probably right, but it rests on the code filter at `venue_fetch.py:144`, not on the date gap.
10. **Adding a `first_capture_date` third gate axis (`EXPECTED_BOOKMAKER_NOT_YET_ONBOARDED`).** — **DEPRIORITIZED, do
    not build yet.** The payoff was measured at 7,645 `attempted_failed` rows (6.8%), and it was scoped against the
    wrong root cause. After steps 1.2 + 3.3 remove the phantom axes, re-measure — most of that 7,645 lives on bare
    BETFAIR, which will no longer exist. Revisit only if the residual is still material. If it is, the derivation is
    cheap: `refresh_sports_bookmaker_league_coverage_2026_06_21.py:54-63` already groups by `(venue, league)` over
    captured rows and only needs `.min()` on date — no new corpus walk.

---

## Suggested shipping order

1. **4.1 + 4.5** — file the issue doc and the corrections; notify the operator. (Unblocks nothing but must not wait.)
2. **1.1 → 1.2 → 1.5** — one commit each, QG-green per commit. Stops all new false rows.
3. **1.3 → 1.4** — grain + evidence fixes.
4. **2.3 → 2.2** — UAC contract hole and the case-pair guard (skipped until 2.1).
5. **1.6** — the four unrequested-but-capturing venues.
6. **[operator gate 4.2 / 4.3 / 4.4]**
7. **3.1** (if option A) → **3.3** → **2.4** → **3.4 / 3.5**.

`Codex SSOTs` this plan is written against: `codex/02-data/availability-manifest-and-data-status.md`,
`…/honest-coverage-model.md`, `…/gcs-and-manifest-delete-safety-protocol.md`, `…/sports-data-types-catalog.md`,
`…/sports-gcs-path-ssot.md`, `codex/04-architecture/shard-level-failure-isolation.md`.
