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
related: [/plans/active/issues/aster_capture_broken_coverage_and_completeness_2026_07_20.md]
created: 2026-07-20
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
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

## What adversarial verification REFUTED — EXTRACTED to archive (2026-07-26)

Full REFUTED-claims writeup (why empty_confirmed is NOT fabricated across the board, the ONEXBET/BETFAIR false-absence
proof, the case-duplicate frozen-legacy evidence) moved to
`/plans/archive/2026_07/sports_shard_enumeration_cartesian_blowup_deferred_history_2026_07_22.md` to bring this doc back
under the 1000-line hard cap. Root cause + fix plan (still current) continues below.

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

> **✅ STEP 1.1 + 1.2 + 1.4 SHIPPED — mtds@accd8aa4 (2026-07-20).** `REQUESTED_ODDS_API_BOOKMAKERS` exported +
> `expected_odds_api_venue_keys()`; `_expected_sports_bookmakers()` now derives purely from the request list (bare
> BETFAIR/ODDS_API/ONEXBET removed from scope, 21 real books now expectable); the v1 `SOURCE_RETURNED_ZERO` branch
> replaced its fabricated `record_empty(fetch_evidence=...)` with `record_zero_rows(was_expected=True)` (mirrors v2).
> Regression lock: `tests/unit/test_sports_sentinel_scope.py` (7 tests) + updated
> `tests/unit/engine/test_sentinels_coverage.py` + `tests/unit/test_orchestrator_per_data_type_sentinel.py`. Verified:
> wire string byte-identical, all 3 phantom venues excluded, all 21 real books included, 71+ tests green, gate green.
> **NOT done: 1.3** (grain-normalization / `is_bookmaker_league_covered_exact`) — largely moot now that bare BETFAIR
> can't be emitted, so deferred; **1.5** (fan-out invariant guard) — the derivation is now single-sourced so the
> tautological runtime assert was skipped in favor of the regression-locking tests; **1.6** (the 4
> captured-but-never-requested venues: BETMGM/BETWAY/BOVADA/UNIBET_EU) — not yet investigated. Part 2 (vocabulary) and
> Part 3 (manifest remediation, incl. the operator-facing UAC reason reclassification) remain OPEN, gated per their own
> sections below.

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

### 1.3 Normalize the capture-dedup key so captures actually suppress sentinels — ✅ SHIPPED 2026-07-22

**✅ SHIPPED — `unified-api-contracts@719e8ea3` + `market-tick-data-service@f37b140f`.** Added
`is_bookmaker_league_covered_exact(bookmaker, league_id)` to `sports_bookmaker_league_coverage.py` (no base-key suffix
folding, unlike `is_bookmaker_league_covered`) + export; MTDS's `_emit_sports_v2_sentinels` now uses it instead of the
folding version. New test `unified-api-contracts/tests/unit/test_sports_bookmaker_league_coverage_exact.py` (6 tests)
proves the two functions genuinely diverge on real fixture data. No MTDS dependency-version bump needed (editable local
path pin). Original spec below, retained for context.

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

### 1.5 Add a fan-out invariant guard in the writer — ✅ SHIPPED 2026-07-22

**✅ SHIPPED — `market-tick-data-service@f37b140f`** (same commit as 1.3). Added the assert in
`_emit_sports_tier2_sentinels` before the v1/v2 dispatch:
`set(bookmakers_scope) == set(expected_odds_api_venue_keys())`, raises `ValueError` on drift. Tests:
`test_emit_sports_tier2_sentinels_raises_on_scope_drift` (monkeypatched stray key),
`test_emit_sports_tier2_sentinels_no_raise_when_scope_matches_by_construction`. Original spec below, retained for
context.

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

**✅ INVESTIGATED (2026-07-22) — legacy data, no active bypass, no quarantine needed.** GCS-verified
(`market-data-tick-sports-prd-central-element-323112/_index/availability_index.parquet`, read-only): all 3,667 rows for
these 4 venues are `capture_status=captured`, `source` ∈ {`odds_api` (~83%), `api_football` (~17%)}, `service_name` ∈
{`migrate-sports-canonical`, `market-tick-data-service`}, `written_at` clustering at 2026-05-05 (bulk v9 migration) and
2026-07-13/16 (the same manifest-rebuild restamp already documented for the ODDS/odds case-duplicates) — **not** any
recent/live timestamp. Git-history search (`git log --all -S`) in both `market-tick-data-service` and
`execution-service` found zero trace of BETMGM anywhere, and confirmed BETWAY + a bare "unibet" scraper existed as one
of **14 real Playwright HTML odds-scrapers** in `execution-service/sports_execution/adapters/scrapers/` (dynamically
dispatched from MTDS's `market_interface/sports/registry.py::adapter_for_bookmaker()` — a genuine, legitimate second
ingest path, entirely independent of `odds_api_adapter.py`'s `bookmakers=` list), removed from `_ADAPTER_PATHS`
2026-05-12 and source-deleted 2026-07-08 (`execution-service@29a888a8d`). The `betway` exclusion in
`odds_api_adapter.py:103-107` (dated 2026-03-28) governs only the Odds-API aggregator's own request and post-dates these
rows' original ingestion. **Conclusion: the rows are legacy, honestly captured under an earlier/different bookmaker
universe (the retired scraper path + `api_football`'s independent vocabulary), carried forward by the v9 canonical
migration — not a currently-active bypass.** No quarantine needed; no code fix required.

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

### 2.2 Add a write-time closed-set guard on `data_type` (do this regardless of 2.1's outcome) — ✅ SHIPPED 2026-07-22

> **⚠️ CORRECTION 2026-07-27** — 07-26 allowlisted `TRADES`/`trades` as "deliberate", missing the closeout doc's
> SAME-DAY (07-23) reversal (lower-case, no exception). Corrected (`uac@bddd063e`+`mtds@7ffabf77`).

**✅ SHIPPED — `unified-api-contracts@50301e5f`.** New `tests/unit/test_sports_data_type_vocabulary.py`, skip-gated with
a `TODO(K0-b)` reason (hoisted to a module-level `_SKIP_REASON_K0B` constant to satisfy the QG rule that
`pytest.mark.skip` needs its `reason=` on the same physical line as the decorator). Now that 2.1/4.3 has decided
lowercase is canonical, unskipping this + fixing the actual case-variant members is the next step (folds into 3.4).
Original spec below, retained for context.

**File:** `unified-api-contracts/unified_api_contracts/registry/market_data_categories.py`,
`DATA_TYPES_BY_ASSET_GROUP["sports"]` (~`:211-245`) — currently registers **both** `"odds"` and `"ODDS"`. **Change:** do
not edit the members yet (blocked on 2.1), but add a QG check that the sports data_type set contains no case-variant
pairs, gated behind a `# TODO(K0-b)` skip until the decision lands. Then flip it live in the same commit as 2.1's
resolution. **Test:** `unified-api-contracts/tests/unit/test_sports_data_type_vocabulary.py` —
`assert len({d.lower() for d in DATA_TYPES_BY_ASSET_GROUP["sports"]}) == len(DATA_TYPES_BY_ASSET_GROUP["sports"])`.

### 2.3 Close the `(sports, odds)` hole in the instrument_type→data_type matrix — ✅ SHIPPED 2026-07-22

**✅ SHIPPED — `unified-api-contracts@9b50a667`.** Added `("sports", "odds"): frozenset({"trades"})` to
`VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE` (landed at line 855; the matrix's sports block had shifted a few lines
since the doc was written, same content/order). Verified
`CONTRACT_REGISTRY[("sports","odds","trades")] = SPORTS_ODDS_TRADES` unchanged. 2 tests added to
`tests/internal/unit/test_sports_prediction_contracts.py`, scoped to the sports odds-family instrument types this matrix
actually declares (the doc's literal "every CONTRACT_REGISTRY key" test spec was measured to produce 424+207 false
positives across unrelated ml_training/reference/derived contracts this matrix was never meant to cover — narrowed
deliberately, see the shipped commit for detail). Did **not** touch the sibling `UNCERTAIN`
`("sports","fixture"/"exchange_odds"/"fixed_odds"/"prop")` entries (no new evidence) or the other 3 `CONTRACT_REGISTRY`
`("sports","odds",...)` entries (naming mismatch with `DATA_TYPES_BY_ASSET_GROUP`, separate issue). Original spec below,
retained for context.

**File:** `market_data_categories.py:832-843` — the matrix has **no** `("sports","odds")` entry, yet prod writes
1,806,527 rows under exactly that pair. The neighbours (`fixture`, `exchange_odds`, `fixed_odds`, `prop`) are
self-labelled `# UNCERTAIN — sports-owner verify`. **Change:** add `("sports","odds"): {"trades", ...}` matching the
registered contract `CONTRACT_REGISTRY[("sports","odds","trades")]` at
`unified_api_contracts/internal/schemas/_sports_prediction_contracts.py:553`. Strip the `UNCERTAIN` labels on the
entries you can now confirm. **Test:** assert every `(asset_group, instrument_type)` key present in `CONTRACT_REGISTRY`
has a matrix entry containing that contract's `data_type`. **Verification:** UAC QG green; re-run
`unified-api-contracts/tests/unit/test_coverage_exclusions.py`.

### 2.4 Fix the codex↔UAC↔prod contradiction on `instrument_type` — ✅ SHIPPED 2026-07-22

**✅ SHIPPED — `unified-trading-pm@2dbb62019`** (same commit as the K0-DECISION(b) reversal). Overview and every worked
example's `instrument_type` changed from `sports_market` (confirmed zero rows in prod, not in `CONTRACT_REGISTRY`) to
`odds` (confirmed canonical: `taxonomy.py:44` + `CONTRACT_REGISTRY[("sports","odds","trades")]` = `SPORTS_ODDS_TRADES`),
and the previously-undocumented, production-dominant `trades` data type added to the Overview and Instrument Type
Mapping table. Original spec below, retained for context.

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

### 3.2 ⛔ NOT-TO-DO (as proposed) — bulk purge of the dead-pair rows (923,952 by this section's own narrower predicate;

operative scope per the operator's 2026-07-22 ruling is 1,066,231, see Phase 5 decisions below — 1,136,624, the other
figure this heading used to cite, turned out to be Option C's population in §4.2, not this one's; see that decision's
full writeup)

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
4. **Prod-bucket deletes are a human-only hard stop** (`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`).

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
  probe under the PROOF-OF-HONEST-ABSENCE hard rule (`/codex/02-data/availability-manifest-and-data-status.md:564-581`).
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

### 3.3 Relabel pass for the 37,426 never-captured `attempted_failed` rows — predicate CONFIRMED 2026-07-23

These sit on pairs that never captured anything (dominated by bare-BETFAIR's 37,426 and the legacy prediction-venue
rows) and are provably false failure claims. A one-off relabel to honest absence is the right instrument — **not** a
gate, since Part 1 stops the source. **Precedent script to model on:**
`market-tick-data-service/scripts/relabel_sports_odds_no_coverage_2026_06_21.py`. **Constraint:** same
consolidator-pause + per-VM-union + `_index/purge_backups/` rules as 3.2. Relabel is reversible from the snapshot; it
does not delete rows, so it does **not** hit the human-only delete hard stop — but it **does** move the coverage number,
so it is still gated on Part 4.

**✅ Predicate confirmed against real prod data (2 independent agents, blind to each other, both exact-match on first
try, no tuning):** `never_captured = capture_status=='attempted_failed' AND (venue,league_id) NOT IN LIVE_PAIRS`
(`LIVE_PAIRS` = distinct `(venue,league_id)` with `capture_status=='captured'`) → **37,426, exact match**, reading the
sports manifest via `instruments-service/scripts/measure_honest_coverage.py`'s `_read_manifest("sports", merge=True)`
with its `_READ_COLUMNS*` lists monkeypatched in-process to add `league_id` (a real manifest column, not derived from
`instrument_id`). **Venue breakdown of the 37,426 is 100% `venue=='BETFAIR'`** (not a mix with prediction-venue rows as
the section title's "dominated by" implied) with real, non-blank `league_id` values (MLS, SEGUNDA_DIVISION, SERIE_B,
SERIE_A, LA_LIGA, etc.) — "bare-BETFAIR" refers to the unqualified venue string, not an empty league_id.

**Test in the original spec above (67,206 on-or-after-first-capture) no longer reproduces — explained, not a predicate
bug.** Both agents got the same complement instead: 20,590 (`attempted_failed AND (venue,league_id) IN LIVE_PAIRS`), and
37,426 + 20,590 = 58,016 = today's entire `attempted_failed` population — a clean, internally-consistent partition.
Today's total `attempted_failed` (58,016) is itself far below the doc's 2026-07-20 measurement (112,277) — consistent
with an actively-churning live backfill/retry pipeline closing out failures over the 3 days since this doc was written
(also: `captured` rose 427,163→548,715, `empty_confirmed` fell 1,267,113→1,223,527 in the same window). No partition of
today's data can reproduce 67,206; it is definitionally impossible today, not a derivation error — re-run this section's
predicate immediately before writing relabel code, exactly as this doc's own Part 4.1 caveat already prescribes for
stale numbers. A finer date-based split of the 20,590 IN-`LIVE_PAIRS` side (row date **on-or-after** vs. **before** that
pair's own first-captured date — the doc's literal "on-or-after their pair's first capture" wording) gives 12,945
on-or-after (genuine current failure) + 7,645 before-first-capture. **7,645 is an exact match to a separately-cited
figure elsewhere in this doc** (line ~878, the deprioritized `first_capture_date` third-gate-axis measurement) — a
disjoint population from the 37,426 (that one's entirely on never-captured pairs; this one's on pairs that DID
eventually capture, pre-first-capture) and not double-counted with it. Full three-way split today: **37,426 (dead pair,
unchanged) + 7,645 (live pair, pre-first-capture, unchanged) + 12,945 (live pair, genuine current failure, down from
67,206) = 58,016** — two of three components are stable/frozen, only the actively-retried component shrank. **Test
(updated):** dry-run diff report asserting the on-or-after-first-capture rows (currently 12,945, not 67,206 — re-measure
at execution time) are **untouched** (genuine fetch failures — no gate should suppress them).

### 3.4 Drop the phantom uppercase `ODDS` manifest rows — BLOCKED on 2.1

22,145 uppercase `ODDS` rows have **no backing GCS objects** (verified on three sample days). They double-count any
`data_type`-grouped denominator. The 20,331 lowercase twins match disk. But dropping them contradicts codex
K0-DECISION(b), so this is blocked on the operator ruling in 4.3.

### 3.5 The 1,337 suffixed `odds_horizon_bucket_{15m,1h,4h,1d}` rows

Confirmed DEAD cohort (0 captured, ever) per `/codex/02-data/sports-data-types-catalog.md:39-40`, and carrying a genuine
**axis shift**: `instrument_type` holds bookmaker names (`paddypower` 346, `pinnacle` 278, …) while `venue` holds
`FOOTBALL` — a sport, violating `_sports_prediction_contracts.py:15-16` which requires `venue` = the bookmaker. 0/1337
rows have `venue == instrument_type`, proving a shift not a duplication. **Action:** low priority, tiny blast radius.
Fold into 3.3's relabel pass or leave with a documented exclusion. Do **not** spin a separate migration for 1,337 rows.

---

## Part 4 — Operator scope decisions (blocking Part 3)

Present these together; they are coupled.

### 4.1 🔴 BIG FINDING — two contradictory honest-coverage formulas are live over the same rows — ✅ DECIDED 2026-07-22

- `unified-api-contracts/.../_honest_coverage_logic.py:88-96` (what `deployment-api` runs, what the operator sees):
  numerator = `captured + (empty_confirmed − out_of_window) + expected_unattempted_known_empty` → **credits**
  `empty_confirmed`.
- `instruments-service/scripts/measure_honest_coverage.py:600-602` (what `coverage.json` → `HonestCoverageCard.tsx`
  shows): `reachable = captured + attempted_failed + expected_unattempted`, `coverage = captured/reachable` →
  **excludes** `empty_confirmed` entirely.
- `/codex/02-data/honest-coverage-model.md:219-226` sides with the second.

They disagree by ~10pp on sports today and move in opposite directions under every remediation option. **This is a
cross-repo SSOT contradiction and a data-correctness finding independent of everything else in this plan.** Per the
CLAUDE.md triage rule it needs `plans/active/issues/` + operator notification **now**, and it must be settled before any
row is touched.

**✅ DECIDED (2026-07-22, interactive session)**: adopt the **EXCLUDE-`empty_confirmed`** formula — the
`instruments-service/scripts/measure_honest_coverage.py` logic, which already matches
`/codex/02-data/honest-coverage-model.md:219-226` — as the **ONE global formula** for `compute_honest_coverage()`. This
is **NOT sports-scoped**: it changes UAC's `compute_honest_coverage()` for **every asset group**, not just sports, and
it moves every asset group's dashboard coverage percentage. **This is a SEPARATE, bigger piece of work** — it needs its
own careful cross-asset-group impact-measurement pass before it ships. Do **not** touch `_honest_coverage_logic.py`
until that measurement (below) has been reviewed and the ship is explicitly re-authorized; that file is unchanged by
this run's shipped items. Track the global rollout as its own follow-up plan before implementation starts.

**📊 MEASURED (2026-07-22, real prod `central-element-323112`)** — every asset group's coverage moves **DOWN** under the
proposed formula, some substantially. Measured via
`unified-api-contracts/scripts/measure_honest_coverage_formula_delta.py` (drives the REAL production
`compute_honest_coverage()` and `measure_honest_coverage.py::_count_statuses()` against the same merged + MVP-gated
dataframe — the formulas are never reimplemented, only the row→`CaptureStatusCounts` folding is, verified against
`read_capture_status_counts`'s classification rules):

| Asset group | Total rows | Current % (credits `empty_confirmed`) | Proposed % (excludes it) | Δ pp       | `empty_confirmed` % of total |
| ----------- | ---------- | ------------------------------------- | ------------------------ | ---------- | ---------------------------- |
| CEFI        | 8,980,261  | 60.88%                                | 49.38%                   | **-11.50** | 28.2%                        |
| DEFI        | 52,293,294 | 68.49%                                | 68.44%                   | -0.05      | 28.1%                        |
| TRADFI      | 6,262,988  | 80.75%                                | 71.79%                   | **-8.96**  | 60.7%                        |
| SPORTS      | 1,977,165  | 94.32%                                | 84.13%                   | **-10.19** | 64.2%                        |
| PREDICTION  | 745,358    | 99.55%                                | 94.36%                   | **-5.19**  | 92.6%                        |

DEFI barely moves because its `out_of_window` reclassification already absorbs almost all of its `empty_confirmed` rows
(14.65M of 14.72M) — the other four asset groups have far smaller `out_of_window` carve-outs relative to their
`empty_confirmed` count, so fully excluding `empty_confirmed` hits them much harder. **This means shipping 4.1 as a
single global cutover would make EVERY asset-group dashboard number drop simultaneously** (CEFI and TRADFI by
double-digit points), which will read as a coverage regression fleet-wide unless it is clearly communicated (and
probably dashboarded) as a formula change, not a data-quality change, at ship time. Re-run the script above for a fresh
number immediately before actually shipping — prod manifests move daily and this table has a date on it.

**✅ SHIPPED 2026-07-22 — `unified-api-contracts@7338fa65`.** Operator gave an explicit, fresh go-ahead with this exact
measured table in hand (not a rubber-stamp of the earlier abstract "yes, global" answer). Re-measured immediately before
shipping, same day, same script:

| Asset group | Total rows (re-measure) | Current % | Proposed % | Δ pp       | Note                                                                        |
| ----------- | ----------------------- | --------- | ---------- | ---------- | --------------------------------------------------------------------------- |
| CEFI        | 8,980,229               | 60.88%    | 49.38%     | **-11.50** | matches the original run almost exactly                                     |
| DEFI        | 9,133                   | 99.48%    | 99.47%     | -0.01      | ⚠️ see anomaly note below — not a real signal                               |
| TRADFI      | 6,262,988               | 80.75%    | 71.79%     | **-8.96**  | EXACT row-count match to the original run                                   |
| SPORTS      | 1,783,541               | 96.73%    | 88.69%     | **-8.04**  | ~10% fewer rows than original (normal day-to-day churn); still a large drop |
| PREDICTION  | 745,358                 | 99.55%    | 94.36%     | **-5.19**  | EXACT row-count match to the original run                                   |

**DEFI anomaly (investigated, does not change the ship decision)**: this re-measurement's DEFI read found only 9,133
rows via the pinned-primary bucket (`market-data-tick-defi-prd-central-element-323112`), vs ~52.29M in the original
same-day measurement. That bucket's `blob.updated` timestamp landed literally seconds before this run's read — strong
evidence an unrelated concurrent process was actively rewriting/consolidating the DEFI manifest index at that exact
moment, not a real 99.98% data loss. The "legacy" fallback bucket this script also checks
(`market-data-tick-defi-central-element-323112`) is a confirmed-404, already-migrated-away bucket per
`/codex/05-infrastructure/bucket-isolation-model.md` §11.3 — unrelated, pre-existing, and expected. Both readings give
the SAME ship conclusion (DEFI's delta is negligible either way), so this doesn't change the decision; the true current
DEFI row count should be re-checked independently of this ship if anyone needs a live number.

**Formula implementation note**: the shipped formula also REVERSES `expected_unattempted_known_empty`'s prior numerator
credit (it now lands in the denominator only, alongside `pending_fetch`) — matching
`instruments-service::_count_statuses` exactly, which never split `expected_unattempted` by reason at all. This is a
slightly bigger behavioral change than the original "just stop crediting `empty_confirmed`" framing implied; it was
caught by UAC's own test suite (a test asserting the old known-empty-credit behavior failed against the new formula) and
fixed in the same commit, not shipped as a partial formula.

**Cross-repo fallout audited**: `deployment-api` (3 test files: `test_data_status_capture_status.py`,
`test_data_status_union.py`, `data_status/test_oow_denominator.py`) and `unified-trading-library`
(`test_manifest_writer_coverage_counts.py`) were checked line-by-line against the new formula. Only
`test_oow_denominator.py` had tests whose PREMISE (not just asserted values) no longer held — rewritten separately
(deployment-api ship tracked next); every other file needs zero test-expectation changes, either because they test
count-bucketing rather than the ratio, or because their fixture shapes happen to give the same output under both
formulas (all-empty-is-out-of-window shapes, or zero-empty shapes).

### 4.2 Which coverage semantics does sports want? — ✅ DECIDED 2026-07-22

Three measured options, pick one:

| Option                                                              | Sports coverage | Rows written | Reversible         |
| ------------------------------------------------------------------- | --------------- | ------------ | ------------------ |
| **A** — add the 2 reasons to `OUT_OF_COVERAGE_WINDOW_REASONS` (3.1) | 94.31% → 87.64% | 0            | Yes, one line      |
| **B** — purge dead-pair rows (3.2)                                  | 94.31% → 91.07% | 923,952 del  | No                 |
| **C** — reclassify to `expected_unattempted`                        | 94.31% → 85.44% | ~1.1M mod    | Yes, from snapshot |

**✅ DECIDED (2026-07-22, interactive session)**: **BOTH A and B, combined — not either/or.** Apply A's mechanism
(reclassify the dead-pair rows with the new `EXPECTED_BOOKMAKER_NO_LEAGUE_COVERAGE` / `EXPECTED_PAUSED_LEAGUE`
`OUT_OF_COVERAGE_WINDOW_REASONS` codes) to the specific dead-pair row set that 3.2 targets, **and then also physically
purge that same reclassified set** (3.2's mechanism) — reason-code first, then delete, rather than picking one mechanism
over the other. This purge execution is gated on **4.4 (Phase 6d)** landing first — see 4.4 below.

### 4.3 Sports `data_type` case direction — codex vs the physical estate — ✅ DECIDED 2026-07-22, REVERSES K0-DECISION(b)

K0-DECISION(b) (2026-07-18) says UPPER is canonical; GCS holds only lowercase directories with zero uppercase ones on
every sampled day. **Re-confirm or reverse K0(b) before any normalizer is re-pointed.** Both shipped normalizers
(`migrate_sports_canonical_v9.py:122-133`, `normalize_sports_mtds_data_type_case_2026_06_25.py:44-51`) point UPPER→lower
and neither ever completed.

**✅ DECIDED (2026-07-22, interactive session)**: **REVERSE K0-DECISION(b).** Lowercase `odds` is canonical, not
uppercase `ODDS` — GCS physically holds only lowercase `odds` directories on every sampled day (2020-07-21, 2023-05-10,
2026-04-14; zero uppercase `ODDS` objects on any of them), so the uppercase manifest rows are a phantom, not the
lowercase ones. `/codex/02-data/sports-data-types-catalog.md` is updated accordingly (2026-07-22): the canonical forms
are now `odds`, `odds_snapshot`, `odds_movement`, `arbitrage_opportunity`, `odds_horizon_bucket`, `markets`, `outcomes`,
`settlements` (lower-case), reversing the 2026-07-19 K0-DECISION(b) banner. The two shipped normalizers now point in the
CORRECT direction (UPPER→lower) — re-point/complete them rather than reversing them. 3.4's phantom-uppercase-`ODDS`
purge remains gated on **4.4 (Phase 6d)**.

### 4.4 Phase 6d — the sports venue-injection gap must land BEFORE any purge — code complete, NOT deployed (2026-07-22)

`deployment-api/deployment_api/services/data_status/mtds.py::is_mtds_honest_coverage_target` **used to explicitly
exclude SPORTS** ("bookmaker axis is Phase 6d"). CeFi/TradFi/DeFi/PREDICTION get UAC-declared venues injected with zero
manifest rows so a fully-absent venue still renders at 0%. Sports did not — its denominator was manifest-derived from
observed venues only. **Purging the zero-capture venues would have made them vanish from the data-status UI instead of
rendering an honest 0%**, reintroducing exactly the invisibility bug `manifest.py:856-861` documents having fixed
elsewhere. Phase 6d was a hard prerequisite for 3.2, and desirable before 3.3.

**✅ IMPLEMENTED 2026-07-22 (code complete, QG-green locally; ship queued — see below)**:
`is_mtds_honest_coverage_target` now includes SPORTS. A new sibling function, `mtds_honest_coverage_for_bookmaker`
(mtds.py), handles the axis the generic per-(venue, data_type, calendar-date) path can't: for each league UAC's
`BOOKMAKER_LEAGUE_COVERAGE` says a bookmaker has ever priced, it pulls real fixture dates via
`sports_expected_dates_for_league` (floor-clipped to the `odds_api` UAC coverage start — the 2020-06 sports data floor,
not a raw calendar range) and counts captured/ empty_confirmed manifest rows per `(bookmaker, league_id, date)` —
columns the writer already emits (`venue_fetch.py::_build_sports_shard_path`). `mtds_expected_venues` resolves the full
23-bookmaker request scope via UAC's new `expected_odds_api_bookmaker_keys()` (shipped `unified-api-contracts@7338fa65`
alongside the Part 4.1 formula change — a `"bookmaker"` `venue_accessor` sentinel, since bookmakers aren't a
`VenueMapping` property). 11 new unit tests (`tests/unit/data_status/test_mtds_honest_coverage_for_bookmaker.py`) pin
the found-vs-expected arithmetic, multi-league aggregation, case-insensitive bookmaker matching, the capture_status
OK-mask, and the gate/expected-venues wiring; full `quality-gates.sh` green locally (4921 tests).

**Ship/deploy status — SHIPPED 2026-07-22 (after a session-boundary/compaction gap; the blocker below cleared on its
own).** `deployment-api@6d20724` ("feat(data-status): SPORTS bookmaker x league x fixture-date honest-coverage axis
(Phase 6d)"), landed on `live-defi-rollout`, pushed, content-verified `ahead=0` against `origin/live-defi-rollout`. The
previously-cited blocker (`unified-api-contracts` foreign-live `DEFI_VENUE_PHASE` work) was the SAME session's own
parallel DeFi-five-venues investigation, not truly foreign — it finished and committed
(`unified-api-contracts@91b6f094`/`@0b0442a6`) sometime between the original NOT-deployed note and this pass, clearing
`unified-api-contracts` to a clean tree. Full `quality-gates.sh` ran green locally before shipping (155s, sentinel
matched HEAD).

**✅ CONFIRMED LIVE IN PRODUCTION (2026-07-22, read-only verified)**: promote PR `promote/deployment-api/6d2072483b62`
(`quality-gates-v2` + `image-build-gate` both green, 17:37:19Z) squash-merged to `origin/main` as `f8abbae`
(18:42:38+01:00 / 17:42:38Z) — content-verified, not SHA-trusted (squash merges mint a new commit hash):
`git show origin/main:deployment_api/services/data_status/mtds.py | grep -c mtds_honest_coverage_for_bookmaker`
returns 3. `uts-shared-deployment-api`'s deployed image is `deployment-api:f8abbae` (exact squash SHA), redeployed
2026-07-22T17:51:37Z — read-only verified via
`gcloud run services describe uts-shared-deployment-api --region asia-northeast1 --project central-element-323112 --format='value(spec.template.spec.containers[0].image)'`.
Phase 6d is genuinely running in the one shared Cloud Run instance that serves the real data-status UI/decisions.

**Scope investigation (2026-07-22)** — Phase 6d is **not a boolean flip**; the injection mechanism the other 4
categories share cannot be reused as-is for SPORTS without a real design change:

- `mtds.py:344-359` (`mtds_expected_venues`) resolves each category's expected-venue list off `VenueMapping` via
  `MTDS_CATEGORY_META[cat]["venue_accessor"]` (a flat venue-name list) — SPORTS's entry (`mtds.py:96-104`) has
  `venue_accessor: ""` with the comment "Phase 6d adds `get_expected_bookmakers` to UAC"; that UAC accessor **does not
  exist yet**. The 23-key real bookmaker list lives today as `REQUESTED_ODDS_API_BOOKMAKERS` in
  `market-tick-data-service/market_tick_data_service/market_interface/adapters/sports/odds_api_adapter.py` — MTDS, not
  UAC. Per the tier/import rules (no service→service deps; UAC is the only SSOT deployment-api may import), it must be
  **added to UAC first** (e.g. alongside `unified_api_contracts/registry/sports_bookmaker_league_coverage.py`) and MTDS
  re-pointed to import it from there rather than deployment-api importing from MTDS.
- The bigger blocker: `MTDS_CATEGORY_META["SPORTS"]["axis"]` is `"per_league_per_bookmaker_per_fixture_date"` — a 3-D
  shape — but `axis` is **purely a descriptive label** today (only read at `breakdowns_domain.py:759`,
  `manifest.py:1131`, `venue_resolution.py:330` to stamp an `honest_axis` string on the API response). The actual
  injection loop, `_apply_mtds_honest_coverage` in `breakdowns_core.py`, has **no axis-dispatch** — it unconditionally
  treats the top-level dimension as a flat "venue" and computes denominators via `mtds_expected_dates_for_venue_dt`'s
  trading/calendar-day model. Naively pointing SPORTS at this path (accessor returning bookmaker names as "venues")
  would inject a **calendar-day** denominator for what is really a **per-(bookmaker, league, fixture-date)** shard space
  — wrong on two axes at once (missing the league dimension entirely, and fixture-dates ≠ calendar trading-days). That
  would silently manufacture a new coverage-percentage defect of the same shape this plan exists to fix.
- Net: Phase 6d needs **(a)** a new UAC bookmaker-list export, **(b)** either a genuine axis-aware branch inside
  `_apply_mtds_honest_coverage` for the 3-D shape, or a SPORTS-specific sibling function that folds
  bookmaker×league×fixture-date up to the same `venues_dict` output shape the caller expects — not a small patch. Treat
  it as its own scoped implementation pass (candidate follow-up plan, not a same-session tack-on), reusing the
  already-shipped `is_bookmaker_league_covered_exact` / `REQUESTED_ODDS_API_BOOKMAKERS` machinery from Part 1 as the
  data source rather than re-deriving expected bookmakers from scratch.

### 4.5 Issue-doc corrections to file

`unified-trading-pm/plans/active/issues/sports_shard_enumeration_cartesian_blowup_2026_07_20.md` needs a correction
banner:

- Its summary states _"There is no per-(venue, league) coverage declaration gating the expected universe."_ **FALSE** —
  `unified-api-contracts/unified_api_contracts/registry/sports_bookmaker_league_coverage.py` exists, is wired at
  `sentinels.py:321`, and is materialised on 606,772 prod rows. Strike the line.
- The reason-split figures `538,098 / 369,272` are wrong; the measured values are
  `EXPECTED_BOOKMAKER_NO_LEAGUE_COVERAGE 606,772 / EXPECTED_PAUSED_LEAGUE 459,459 / SOURCE_RETURNED_ZERO 200,864 / VENUE_FETCH_FAILED 94,127 / blank 385,402`.

---

## ⛔ NOT-TO-DO — EXTRACTED to archive (2026-07-26)

Full numbered REFUTED-premises checklist moved to
`/plans/archive/2026_07/sports_shard_enumeration_cartesian_blowup_deferred_history_2026_07_22.md` (same content as the
earlier REFUTED section above, restated as a checklist) — to bring this doc back under the 1000-line hard cap. Do not
act on any of the 10 refuted premises there.

## Suggested shipping order

1. **4.1 + 4.5** — file the issue doc and the corrections; notify the operator. (Unblocks nothing but must not wait.)
2. **1.1 → 1.2 → 1.5** — one commit each, QG-green per commit. Stops all new false rows.
3. **1.3 → 1.4** — grain + evidence fixes.
4. **2.3 → 2.2** — UAC contract hole and the case-pair guard (skipped until 2.1).
5. **1.6** — the four unrequested-but-capturing venues.
6. **[operator gate 4.2 / 4.3 / 4.4]**
7. **3.1** (if option A) → **3.3** → **2.4** → **3.4 / 3.5**.

`Codex SSOTs` this plan is written against: `/codex/02-data/availability-manifest-and-data-status.md`,
`…/honest-coverage-model.md`, `…/gcs-and-manifest-delete-safety-protocol.md`, `…/sports-data-types-catalog.md`,
`…/sports-gcs-path-ssot.md`, `/codex/04-architecture/shard-level-failure-isolation.md`.

---

## Deferred work after 2026-07-22 — EXTRACTED to archive (2026-07-26)

Full historical derivation (why 1,066,231 not 1,136,624, the independently-verified 3.3 predicate writeup, the
soft-delete-vs-backup investigation) moved to
`/plans/archive/2026_07/sports_shard_enumeration_cartesian_blowup_deferred_history_2026_07_22.md` to bring this doc back
under the 1000-line hard cap (task_template.md finding J) — every item there was already `- [x]` (done, not open work).
Current authoritative state: see this doc's own RE-TRIAGE (2026-07-23) section + the 2026-07-26 Part 2/Part 3 progress
entries below.

---

## Progress Log

**2026-07-22** — Operator made 3 scope decisions on Part 4 in a live interactive chat session (recorded here, not
previously written to any doc): **4.1** — adopt the EXCLUDE-`empty_confirmed` formula (instruments-service's
`measure_honest_coverage.py`, matching `/codex/02-data/honest-coverage-model.md`) as the ONE global
`compute_honest_coverage()` formula for **every** asset group; this is a SEPARATE, larger piece of work **out of scope
for this workflow phase**, needing its own cross-asset-group impact-measurement pass before it ships —
` _honest_coverage_logic.py` is untouched by this run. **4.2** — BOTH option A (reclassification via the new
`OUT_OF_COVERAGE_WINDOW_REASONS` codes) AND option B (physical purge) combined: reclassify the dead-pair rows with the
new reason codes, then also physically purge that same set, rather than either/or. **4.3** — REVERSE K0-DECISION(b):
lowercase `odds` is canonical, not uppercase `ODDS`, per the physical-estate evidence (zero uppercase `ODDS` objects on
any of the 3 sampled days). `/codex/02-data/sports-data-types-catalog.md` updated same-day to record the reversal
(banner + Instrument Type Mapping + all 8 worked examples' `instrument_type` corrected from the non-existent-in-prod
`sports_market` to `odds`, + the `trades` data_type documented for the first time). **4.4** remains OPEN and unstarted —
re-verified 2026-07-22 by direct code read that Phase 6d has NOT landed
(`deployment-api/deployment_api/services/data_status/mtds.py:230-236` `is_mtds_honest_coverage_target` still explicitly
excludes SPORTS); it remains a hard prerequisite for 3.2/4.2's purge and must be sequenced before that purge executes.
Parallel note: Part 1 items 1.3/1.5/1.6 and Part 2 items 2.2/2.3 are being implemented **in the same run** by sibling
workflow agents — this entry does not claim that work; see their own commits/banners in Part 1/Part 2 above for status.

**2026-07-22 (later same day)** — Operator gave explicit fresh authorization to continue Phase 3 → 4 → 5 with the
measured magnitude in hand. **Phase 3 shipped**: `compute_honest_coverage()` rewritten to match
`instruments-service::_count_statuses` exactly (`unified-api-contracts@7338fa65`) — caught and fixed a real bug in the
first draft (`expected_unattempted_known_empty` had incorrectly kept its pre-4.1 numerator credit; UAC's own test suite
caught it before ship). Cross-repo fallout audited empirically (not just by inspection) via each dependent repo's own
`quality-gates.sh` against the new formula through its editable local UAC install: `deployment-api` needed 2 real test
rewrites (`test_oow_denominator.py`, premise no longer held) + doc fixes; `unified-trading-library` needed zero changes.
**Phase 4 implemented**: `mtds_honest_coverage_for_bookmaker()` (new sibling to `mtds_honest_coverage_for_venue`, since
SPORTS' bookmaker×league×fixture-date axis has no calendar-date/league dimension the generic path handles) + UAC's
`expected_odds_api_bookmaker_keys()` accessor + `is_mtds_honest_coverage_target` now includes SPORTS. 11 new tests,
`quality-gates.sh` green locally. **Not yet deployed** — confirmed factually (not speculatively) via a dedicated 4-agent
scoping workflow: the code is uncommitted working-tree diff, 12 commits behind trunk, blocked from even committing by
`unified-api-contracts`'s foreign LIVE dependency (another concurrent session's DEFI_VENUE_PHASE work, reconfirmed LIVE
via <120s mtime checks repeated over several hours — correctly left untouched). **Phase 5: NO-GO.** The same scoping
workflow read Part 3/Part 4 in full and confirmed 3.0's prerequisite is unsatisfiable today, and surfaced 3 genuine
operator-owned decisions (the human-only prod-bucket-delete hard stop 4.2 never reconciled; 3 unreconciled row-count
figures for 3.1/3.2's scope; 3.3's unspecified destination value) plus several real implementation gaps (no atomic
cross-object "same transaction" primitive on GCS; no safety tooling built yet) that block drafting any write script,
independent of the Phase 6d deploy timeline. Converted to `- [ ]` todos in the Deferred-work table above rather than
left as prose. **Lesson (data-loss near-miss, caught by /pre-compact)**: this exact write-up was LOST twice during
shipping — the repeated quickmerge retry cycles against this same file (racing an extremely active sibling session
landing dozens of commits/hour to adjacent plan docs) silently dropped the uncommitted edit at least once via an
autostash-pop that produced no conflict markers and no error, just silent reversion to the prior commit. Caught only
because `/pre-compact`'s Step 1 (`git status`, re-grep the doc for expected content) is mandatory-first, not because
anything alerted on the loss. **Also discovered mid-audit**: a pre-existing, unrelated `instruments-service` commit
(CeFi off-by-one-day expiry dedup, `.qg_last_passed_sha`-verified passing) sitting committed-but-unpushed from earlier
in this session, blocked by the same foreign UAC dependency — queued for push alongside Phase 4's deployment-api ship,
not newly discovered work. A fleet-wide `staging-backmerge-to-ldr.yml` template-drift (sibling bug to the
`main-backmerge-to-ldr.yml` fix shipped earlier this session) was also found and fixed across 4 repos while chasing an
unrelated PM post-gate failure.

**2026-07-22 (continuation, post-compaction)** — Retried the queued ships now that the shared-workspace contention
cleared: `deployment-api@6d20724` (Phase 6d) landed on `origin/live-defi-rollout` via quickmerge's documented
clean-tree/unpushed-commit fallthrough (the commit already existed locally from a pre-compaction attempt);
`instruments-service`'s CeFi-dedup commit was found already landed (`ahead=0`) and `system-integration-tests`'
workflow-template fix was found already landed too — both must have gone through in an earlier retry this session that
predates this compaction. **Verified Phase 6d is genuinely live in prod** — not just promoted — via
`gcloud run services describe uts-shared-deployment-api`: deployed image `deployment-api:7ab62ec` (revision
`uts-shared-deployment-api-00251-f45`, ready `2026-07-22T18:48:32Z`) contains `mtds_honest_coverage_for_bookmaker`
(grepped the actual deployed commit's tree, not just git ancestry — a first ancestry-only check falsely suggested it
wasn't deployed, because squash-merge-to-main promotes never preserve the feature commit as a git ancestor; content-grep
is the correct check for this trunk model, git ancestry is not). **Operator RULED all 3 Phase 5 decisions** (via
`AskUserQuestion`, this session): human-only triggers the prod-bucket write; row-count scope = 1,136,624; 3.3's
destination = `empty_confirmed` + one of 3.1's two new codes. Recorded as `[x]` in the todos above. **New open gap
surfaced applying the ruling**: 1,136,624 matches neither already-computed figure in this doc (923,952 for 3.2's coded
SQL predicate, 1,066,231 for 3.1's already-shipped/measured effect) — no query producing it exists anywhere here;
flagged as a P0 follow-up rather than silently picking one of the existing numbers to stand in for it. **Also fixed,
opportunistically**: `distinct_values_noncanonical_audit_2026_07_20.md` was the sole remaining `plan-discipline` QG
violation (a different file than the `lst_rate_honest_coverage_2026_07_21.md` one baselined earlier this session — that
one had since been fixed by its owning session) — added the missing `## Deferred work — migrated to:` banner and
re-baselined `plan_discipline_baseline.yaml` back down to 0 (rather than ship the earlier temporary tolerate-1 baseline,
which was no longer accurate).

**2026-07-22 (second continuation, same day)** — Rather than treat the 1,136,624 gap as a script-writing exercise,
traced its provenance first: `git log -S` on the doc showed it entered in the doc's very first commit (`435356187f3`),
in the same breath as §4.2's Option C ("reclassify to `expected_unattempted`", cited only as "~1.1M mod", never given an
exact figure) — not as a second measurement of §3.2's dead-pair population. No script or doc anywhere computes 1,136,624
for 3.1/3.2, and it exceeds both 923,952 and 1,066,231. Since §4.2 already decided **combined A+B**, not C, scoping
3.1/3.2 to 1,136,624 would have silently substituted a rejected option's population into the chosen mechanism — surfaced
to the operator as a likely SSOT contradiction via `AskUserQuestion` rather than resolved unilaterally. Operator
confirmed the re-pick and chose **1,066,231** (3.1's own already-shipped, already-measured scope). **This closes the
reconciliation with zero new derivation work**: 3.1's shipped predicate already produces exactly the ruled population,
so 3.2/3.3 (if and when the human-only trigger fires) target that same 1,066,231-row set, not 3.2's originally-drafted
narrower LIVE_PAIRS/`row_count`-filtered subset (923,952). Updated the Phase 5 DECISION todo, closed the now-superseded
"derive the predicate" `[SCRIPT]` todo as resolved, and corrected §3.2's heading to stop pairing 923,952 with 1,136,624
as if they scoped the same population. Also re-ran into the sibling-contention pattern 4 more times shipping the
cosmetic 1,136,624→P0-todo edit from the prior entry above — each retry got a fresh green `quality-gates.sh` invalidated
by a sibling commit before `quickmerge.sh` could land it; stopped retrying per policy (content verified intact,
uncommitted, low-value) and folded that edit into this same round of changes instead.

## RE-TRIAGE (2026-07-23)

**Verdict: STILL OPEN, ACCURATE.** This doc is already exhaustively self-tracked (7-agent audit + adversarial
verification + a full Progress Log through the 2026-07-22 second continuation) — re-triage here is a check for movement
since that last entry, not a re-derivation of the whole finding.

Spot-checked the pieces most likely to have moved:

- **Part 1 code fixes (1.1/1.2/1.4/1.3/1.5)** — all still show `✅ SHIPPED` banners in the doc and the cited commits
  (`mtds@accd8aa4`, `uac@719e8ea3` + `mtds@f37b140f`) are present in `git log` for both repos. Confirmed
  `_expected_sports_bookmakers()`-class fixes are durable (not reverted).
- **Part 4.1/4.2/4.3/4.4 operator decisions** — all four show
  `✅ DECIDED`/`✅ SHIPPED`/`✅ CONFIRMED LIVE IN PRODUCTION` banners with cited SHAs (`uac@7338fa65`,
  `deployment-api@6d20724` → prod image `deployment-api:f8abbae`). No reason to doubt these given the doc's own
  read-only production verification steps.
- **Part 3 (manifest remediation: 3.1 reclassify / 3.2 purge / 3.3 relabel / 3.4 drop phantoms)** — per the task
  background for this re-triage round and confirmed independently: searched `market-tick-data-service` git history since
  2026-07-22 12:00 for any write matching this doc's own scoped population (1,066,231 dead-pair rows). Found none — the
  only sports-manifest writes in that window are `mtds@e9d9dec0` (a different, already-tracked wrong-source wipe,
  1,266,874 rows) and `mtds@f9f012cb` (a different, already-tracked phantom `soccer_*` league_id prune). Part 3 remains
  genuinely un-executed, matching the doc's own "Not done (scoping closed, executable pending the human trigger)" state
  — the human-only prod-bucket-write gate (`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`) has not been
  exercised for this population.
- **The open `- [ ]` todos** (restate 3.3's SQL predicate, confirm execution order, confirm 3.4's procedure weight, the
  cross-object-CAS mechanism question, the missing safety tooling) — no evidence any of these were picked up since the
  last Progress Log entry.

No conflicts with any other doc in this batch. `sports_live_writer_instrument_type_casing_never_fixed_2026_07_22.md`
(K1/K2, resolved this session) and this doc's own Part 4.3 (`ODDS`/`odds` **data_type-value** case direction) are easily
confused but are genuinely different axes — K1/K2 is about `instrument_type`/`data_type` on the raw sports odds writer,
4.3 is about the `data_type` string's own casing vocabulary (`odds` vs `ODDS`) for a frozen-legacy dataset — this doc's
own §4.3 already documents that distinction correctly, no correction needed here.

**2026-07-23 — §3.3 P1 predicate resolved via 2-agent independent derivation (workflow `wf_701f070c-2a0`).** Both
agents, blind to each other's implementation, derived the same predicate from the doc's own §3.2/§3.3 text and got an
**exact match on 37,426** on the first run, no tuning. Real schema discovery in the process: `league_id` is a genuine
manifest column (`unified-trading-library/manifest_writer/_rows.py:64` et al.), just absent from
`measure_honest_coverage.py`'s own narrower default read-columns — must be monkeypatched in-process (same pattern
`measure_honest_coverage_formula_delta.py` already uses for `error_reason`), not re-derived from `instrument_id`
parsing. The doc's other §3.3 test figure (67,206) did **not** reproduce, but both agents independently landed on the
same complement (20,590) and traced why: today's total `attempted_failed` (58,016) is itself far below the doc's
2026-07-20 snapshot (112,277) — an actively-churning retry pipeline, not a predicate error. A finer date-split recovered
a three-way partition (37,426 dead-pair + 7,645 live-pair-pre-first-capture + 12,945 live-pair-genuine- failure =
58,016) where the 7,645 figure is an exact, independent match to a wholly separate citation elsewhere in this same doc
(the deprioritized `first_capture_date` axis measurement, line ~878) — strong corroboration the methodology is right
even though the headline 67,206 figure is simply stale. Full write-up in §3.3 above; both the P1 SCRIPT todo and the
§3.3 section itself updated with the confirmed predicate, the schema note, and the explained discrepancy. Phase 5
execution itself was NOT touched — this was read-only investigation against real prod data (verified `git status` clean
on `instruments-service`/`unified-api-contracts` after the run), no manifest writes, no GCS mutation.

**Lesson — this exact edit was lost once in transit, recovered from a pre-commit patch backup, not re-derived.** A
quickmerge attempt's stash-aside-foreign-files mechanism swept this file's diff away along with unrelated foreign WIP;
neither `git stash list` nor its top 3 entries contained it, but `~/.cache/prek/patches/*.patch` (pre-commit's own
patch-backup directory, a separate mechanism from `git stash`) did —
`grep -l "RESOLVED 2026-07-23" ~/.cache/prek/patches/*.patch` found it in 5 dated patches. `git apply`/`patch --fuzz`
both failed to cleanly reapply the bundled multi-file patch against the since-moved HEAD, so the edits were
reconstructed directly (same content, verified against the recovered patch) rather than risk a partial/fuzzy apply
corrupting the file.

**2026-07-23 (continuation) — remaining Part 3 DECISION/SCRIPT todos ruled via operator chat + one dedicated
investigation.** Operator answered interactively (3 questions, all "Recommended" option chosen): execution order is
strict sequential 3.1→3.2→3.3 (3.4 stays separately blocked on 2.1); 3.4 gets a lighter procedure than 3.2/3.3 since its
rows are confirmed-phantom with no backing GCS object; the cross-object write mechanism is sequential per-object CAS
with a partial-apply alarm, matching the existing `purge_pre_launch_manifest_rows.py` precedent — no new design pass
needed. Separately, the operator asked directly why a hand-rolled `_index/purge_backups/` backup step is needed given
GCS's 7-day soft-delete policy — a live investigation (real `gcloud storage buckets describe` / `gsutil versioning get`
against `market-data-tick-sports-prd-central-element-323112`, cross-checked against Google's current first-party docs)
confirmed soft-delete IS enabled (7-day retention) and DOES cover overwrites, not just explicit deletes — so the
backup-copy requirement is dropped as redundant. But the same investigation found soft-delete would NOT have helped the
actual precedent incident this section cites (`reconcile_phantom_manifest_rows_stale_read_ overwrite_2026_07_12.md`, now
in `plans/archive/issues/` — its citation path here was stale, corrected in the same edit): that was a stale-read blind
overwrite with no write-time guard, and soft-delete is purely retroactive, not a write-time gate — the real fix there
was a staleness/merge check, which is exactly what the ruled CAS+partial-apply mechanism (above) provides. All 5
previously-open `- [ ]` todos in the checklist are now `- [x]`; the only work left in Part 3 is genuine unbuilt safety
tooling (CAS+alarm implementation, row-identity assertions, consolidator-paused pre-flight, `coverage_drift.py`
pre-notify mechanism, dry-run mode) plus the standing human-only execution trigger — neither of which is a decision left
to make.

**2026-07-26 (slot-2) — Part 2 §2.2 + 3 of 5 Part 3 safety-tooling items shipped (build-only, no manifest/GCS write).**

- **Part 2 §2.2**: dropped uppercase `"ODDS"` from `DATA_TYPES_BY_ASSET_GROUP["sports"]`, unskipped
  `test_sports_data_type_set_has_no_case_variant_pairs` (allowlisted the separately-decided `TRADES`/`trades` exception,
  K1) — `unified-api-contracts@a32ad5fb`. Caught + fixed a resulting cross-repo regression: mtds's
  `test_rule11_per_ag_shard_counts_byte_unchanged` re-pinned SPORTS 96→88 — `market-tick-data-service@f7504a10`.
- **Part 3 safety tooling** (CAS+alarm itself out of scope, tracked in `sports_consolidated_closeout_2026_07_19.md`):
  `assert_consolidator_paused` + `assert_row_identity` (`mtds@f7504a10`,
  `scripts/sports_manifest_remediation_safety.py`, composes existing `consolidator_liveness.py` primitives);
  `coverage_drift.py` pre-notify (`deployment-api@1f0d3a0`, additive-only); a dry-run-ONLY 3.3 demo script (no `--apply`
  flag at all) — live-tested, re-measured **0** dead-pair `attempted_failed` rows today (down from 37,426 on
  2026-07-23), row-identity guard correctly flagged the drift.
- **3.4 deliberately deferred** — needs a live per-row GCS-existence check, more scope than this pass; genuinely open,
  not blocked on a decision.
- **Follow-up finding (different repo, not fixed here)**: `consolidator_liveness.py`'s `_scheduler_job_name_for_bucket`
  resolves the env short-form to `"prd"`, but the real deployed Cloud Scheduler jobs use literal `"prod"`
  (`uts-prod-manifest-consolidator-{key}-cron`, confirmed live) — every scheduler-state lookup for these buckets 404s.
  My check fails closed (treats unknown as not-paused), so no unsafe write resulted, but the monitor's own
  `REASON_SCHEDULER_PAUSED` classification can never fire. Follow-up todo below.

- [ ] [INFRA] P2. Fix `consolidator_liveness._scheduler_job_name_for_bucket`'s env-short-form resolution — real deployed
      jobs use `"prod"`, not the `"prd"` bucket-naming short form `_resolve_deployment_env_short()` produces (confirmed
      live 2026-07-26 via `gcloud scheduler jobs list`, both sports buckets 404). (repo: unified-trading-library)
