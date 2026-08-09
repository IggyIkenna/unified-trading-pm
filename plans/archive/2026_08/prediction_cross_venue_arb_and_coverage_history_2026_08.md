---
doc_type: plan
title:
  Prediction cross-venue arb detection + honest-coverage correctness — extracted history wave 2 (2026-06-20 through
  2026-06-27 fully-closed sessions)
summary: >-
  Archive-bound extraction of twelve fully-closed, dated Progress Log sessions (2026-06-20, 2026-06-21, three 2026-06-23
  sessions, four 2026-06-25 sessions, and three 2026-06-27 sessions) from
  /plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md, split out to bring that doc back under its
  500-line soft cap (it had drifted to 1013 lines / 1009+ over the 1000L hard cap by 2026-08-09). Second wave of
  extraction for this doc -- the first wave (2026-07-24) already pulled an earlier batch of fully-closed 2026-06-20
  through 2026-06-24 entries into /plans/archive/2026_07/prediction_cross_venue_arb_and_coverage_history_2026_07_24.md;
  this doc's dated sub-sections kept accumulating new closure/citation annotations after that first extraction (checkbox
  flips, na-eligibility-audit citations, EXTRACTED-to-batch9 markers), pushing the source back over cap. Content covers
  the Kalshi historical-enumeration root-cause + official-API discovery (2026-06-20), the Polymarket v9 re-walk + CF-11
  phantom-row fix (2026-06-21), the P0 honest-coverage POLYMARKET-lifecycle root-cause + Kalshi sports/EUR-FX
  canonicalization expansion + instruments-catalogue daily aggregation deploy (2026-06-23, three sessions), the live
  arb-detector dispatch + canonical arb chain + end-to-end live-data run + cross-venue arb surface ship (2026-06-25,
  four sessions), and the CF-11 FetchEvidence fix / IS re-run + deadman alert / daily IS Cloud Scheduler automation
  (2026-06-27, three sessions). Every checkbox extracted here was already `[x]` (or a non-checkbox EXTRACTED-elsewhere
  marker) in the parent before extraction -- no open work moved; the two sessions that still carried an open checkbox
  (2026-06-24, 2026-06-23 fixture-linking) and the one session referenced by pointer from a still-live Progress Log
  entry ("this Progress Log's 2026-06-26 entry") were left in the parent. The most-recent audit-trail bullets that had
  accumulated at the tail of the 2026-06-27 (~10:10 UTC) session (2026-07-30 onward -- na-eligibility-audit and
  context-scout status entries) were also left in the parent as current status, not archived history. Zero open todos
  here -- this file is a record, not a work queue.
status: complete
nature: record
asset_group: [prediction]
stage: [meta]
repos:
  [agent-orchestrator, deployment-api, deployment-service, e2e-testing, features-service, fund-administration-service]
scope: [engineer, admin]
tags:
  [
    prediction,
    kalshi,
    polymarket,
    arb,
    cross-venue,
    honest-coverage,
    cqg,
    backfill,
    manifest,
    history,
    archive-bound,
    progress-log,
  ]
related:
  [
    /plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md,
    /plans/archive/2026_07/prediction_cross_venue_arb_and_coverage_history_2026_07_24.md,
    /plans/archive/2026_08/issues/prediction_cross_venue_arb_line_cap_blocks_marker_2026_08_07.md,
  ]
created: 2026-08-09
last_updated: 2026-08-09
parent_epic: predictions_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0
estimate_calibrated_ai_days: 0
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
  extracted 2026-08-09 from /plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md (prediction satellite AO
  batch 8) to bring that plan back under its 500-line soft cap -- see
  /plans/archive/2026_08/issues/prediction_cross_venue_arb_line_cap_blocks_marker_2026_08_07.md for the finding this
  executes.
---

# Prediction cross-venue arb detection + honest-coverage correctness — extracted history (wave 2)

> **Archive-bound record, not a work queue.** This file holds twelve verbatim, fully-closed dated Progress Log sessions
> (2026-06-20 through 2026-06-27) extracted from the parent plan's history so the parent could get back under its
> line-count soft cap. No open todos exist in this file -- every checkbox below was already `[x]` in the parent (or
> already carried its own EXTRACTED-elsewhere marker). See
> `/plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md` for the live plan.

## Extracted Progress Log entries

### 2026-06-25 (autonomous /autonomous) — LIVE arb-detector dispatch + design SSOT written (operator: run paper ~1d on a VM, store arbs to GCS, go long-lived)

Operator direction: we already stream live books for BOTH venues, so DETECT live arbs now — run the (shipped)
cross-venue `arbitrage_price_dispersion` engine in PAPER mode against the live streams for ~24h on a VM, NORMALIZE both
sides to a common YES-probability, flag PURE_ARB (bid crosses offer) + QUOTABLE_ARB (mid crosses mid, both two-way), and
STREAM every arb opportunity to GCS over time → an accumulating arb-opportunity corpus. If it works for a day → make it
a long-lived running service. Design SSOT written: `/codex/04-architecture/cross-venue-prediction-arb-detection.md`
(reuse the shipped matcher→feature→engine; add the live wiring + the GCS arb store + the long-lived run; fix the
producer trades-mislabel P0 first/alongside). A detailed `/autonomous` dispatch prompt was produced for a fresh agent.

- [x] ✅ [DESIGN] P0. **Live cross-venue arb DETECTOR (paper-mode, GCS-persisted, long-lived) — DELIVERED (2026-06-24):
      detector RUNNING long-lived on prediction-arb-detector-20260624-134310; 4 repos shipped; honest-0 (8932 mappings,
      0 overlap). Was a DISPATCH to a fresh `/autonomous` agent.** Per
      `/codex/04-architecture/cross-venue-prediction-arb-detection.md`: (1) fix the prediction producer trades-mislabel
      (P0 below — `data_type=trades` carries book data); (2) wire the shipped book dispersion feature +
      `arbitrage_price_dispersion` cross-venue engine into the LIVE path in PAPER mode, normalizing both venues to
      YES-probability with same-YES-semantics + fee-net edge; (3) flag PURE_ARB (bid×offer) + QUOTABLE_ARB (mid×mid,
      both two-way), honest-skip one-sided; (4) append every opportunity to a GCS arb-store (dated/partitioned, via
      resolve_bucket_name + writegate); (5) launch a VM (LONG_LIVED_LIVE / classified / watchdog-registered), run ~24h
      paper with strict exit_code+log-mtime monitoring, report the real numbers (two-way-overlap ticks, PURE/QUOTABLE
      counts, edge distribution, store rows); (6) if it produces signal → promote to a permanent long-lived service +
      health-surface it. Repos: market-tick-data-service (producer fix + live wiring) + features-service (live handler +
      arb store) + strategy-service (paper engine) + deployment-service (VM launcher/classify). Provenance: operator
      2026-06-25. **PROGRESS 2026-06-24**: parts (2)(3)(4) = the detector code (normalize→YES-prob + fee-net +
      PURE/QUOTABLE taxonomy + honest-skip + GCS arb-store sink + live loop) SHIPPED features-service@ef7cd58c; part (1)
      producer trades-fix IN FLIGHT (MTDS sub-agent, see the BOOK-STATE P0 below); parts (5) VM launch+24h run and (6)
      promote tracked as the granular P0/P1 todos in the 2026-06-24 Progress Log entry above.

### 2026-06-25 (autonomous /autonomous) — CANONICAL ARB CHAIN COMPLETE: strategy engine landed (strategy-service@06e51ed0)

The full cross-venue Kalshi↔Polymarket arb chain is now BUILT + SHIPPED in canonical homes (operator: "put the
arb-finding in the canonical place"):

| Layer                  | Repo@sha                  | What                                                          |
| ---------------------- | ------------------------- | ------------------------------------------------------------- |
| per-instrument matcher | UAC@e618ce96              | `build_cross_venue_mapping` (8,932 real pairs on 06-23)       |
| two-axis taxonomy      | UAC@098d1698              | `PredictionUnderlying`/`PredictionBetType` (97/97 cqg)        |
| dispersion FEATURE     | features-service@54ea17c8 | `prediction_cross_venue_dispersion` → `xv_best_edge` per pair |
| arb ENGINE + mode      | strategy-service@06e51ed0 | `arbitrage_price_dispersion` cross-venue-prediction branch    |

**Engine** (strategy-service@06e51ed0): added `dispersion_type="cross-venue-prediction-dispersion"` as a DISPATCH BRANCH
(the factory enforces one-engine-per-archetype; new variants are branches not subclasses — mirrors
`funding_rate_dispersion`). 3 spec cohorts `kalshi-polymarket-{btc,eth,spx}-up-down-daily-usdc-v2-prod`
(`venues=[polymarket,kalshi]`, asset_group=prediction). On `xv_best_edge > entry_threshold` it emits a two-leg
LEADER_HEDGE `AtomicInstruction` — BUY YES on the cheaper-YES venue + SELL YES on the richer-YES venue, edge-sized via
the existing `ArbitragePriceDispersionRankAllocator`; leg routing via each leg's `native_market_id`. `prediction_arb`
mode satisfied by the v2 archetype (v1 dispatch is retired — the prompt's "\_archived stub" premise didn't hold). 5
tests; QG-green. So `arbitrage_price_dispersion` + `prediction_arb` = the existing archetype with a prediction-venue
branch/cohort (operator's read — confirmed).

**Data reality (operator-confirmed):** book depth is LIVE-ONLY on both venues (not historically backfillable — verified
vs the live APIs); trades + mid-price are historical. The live producers (4 VMs) are healthy + accumulating. The chain
prices any two-sided-liquid overlap the instant it exists; today the liquid daily-crypto overlap is thin (Polymarket's
active crypto is sparse/novelty vs Kalshi's rich daily set). See the corrected P0 below + the trades/mid-price-backtest
P1.

**Fleet note:** PM LDR `workspace-manifest.json versions{}` is behind origin/main (UTL 0.43→0.44 +7 repos) — pure
promotion-lag (editable path installs), warn-class; both the feature + engine agents temp-aligned→verified→restored it
to ship green. A PM LDR↔main FF would clear the recurring warn (the `main-backmerge-to-ldr` hourly cron should sweep
it).

### 2026-06-25 (autonomous /autonomous) — END-TO-END canonical arb chain RUN on real data: matcher scales (8,932 pairs); BINDING gate = Polymarket live BOOK-capture rate

Ran the **canonical** `prediction_cross_venue_dispersion` feature (features@54ea17c8) over real prod data for
day=2026-06-23 (loaded 8,475,033 tick rows). RESULT: **8,932 cross-venue Kalshi↔Polymarket mappings** (the UAC matcher
`build_cross_venue_mapping` WORKS AT SCALE) — but **"no readable two-sided books" → 0 priced rows**. Pinned the cause
(read-only GCS):

- **Kalshi captured 4,316 instrument books** on 06-23 — rich: crypto `KXBTC`/`KXBTCD`/`KXETH`/`KXSOL`/`KXXRP`/`KXHYPE`/
  `KXBNB`, macro `KXCPIYOY`/`KXFED`/`KXGDPNOM`, MLB, World Cup.
- **Polymarket captured only 468 token books** — vs the ~17,772 token-ids it RESOLVES in its live universe, and vs
  Kalshi's 4,316. The 468 don't overlap Kalshi's crypto, so NONE of the 8,932 matched pairs has a two-sided book.
- **Verified GOOD (not the gate):** the crypto Polymarket CATALOGUE carries `clob_token_ids` 19/19 + `available_from/to`
  (43a working); both venues DO have `book_snapshot_5` for 06-23; the matcher pairs at scale.

So the full canonical chain (matcher → feature → engine[in flight]) is BUILT + proven on real data; the ONLY remaining
gate to SEEING a live crypto arb is the **Polymarket live BOOK-capture rate (~468 of ~17,772 resolved tokens, missing
the crypto markets)**. Fast path to a first arb: a Polymarket BATCH `book_snapshot_5` backfill (#1011 path SHIPPED) for
the crypto markets on a date where Kalshi also has crypto books → re-run the feature → priced two-sided dispersion.

- [x] ✅ [SCRIPT] P0. **DIAGNOSED + CORRECTED (2026-06-25) — NOT a producer bug; book is LIVE-ONLY + the gate is
      liquid-market OVERLAP.** The earlier "~468 of ~17,772 = a 97% producer drop" framing was WRONG. Verified vs the
      live APIs + the running VM run.log: (1) **book depth is live-only on BOTH venues** — Polymarket `/book` returns
      `"No orderbook exists"` for old/inactive tokens, `/prices-history` gives historical MID-PRICE not depth, Kalshi
      `/orderbook` is current-only → `book_snapshot_5` can ONLY be accumulated live, NEVER historically backfilled
      (trades + mid-price ARE historical). (2) The `prediction-live-polymarket-book-snapshot-5` VM is HEALTHY — 17,737
      universe entries, ~190 new captures/10s, heartbeating — it captures every token that HAS a live book; ~468 = the
      count that actually have one (the rest return "No orderbook" = inactive/illiquid). **batch==live symmetry for book
      already holds** (live IS the source; a "batch book backfill" just re-fetches the current book). (3) Real
      constraint: Polymarket's ACTIVE LIQUID daily-crypto markets are currently sparse/novelty
      (`bitcoin-hit-1m-before-gta-vi`, airdrops) vs Kalshi's rich daily set (KXBTCD ×130…) — the arbable
      two-sided-liquid OVERLAP is thin right now. **No code fix needed; the live producers (both venues) are healthy +
      accumulating book + trades — the matcher→feature→engine prices any overlap the instant both venues have a liquid
      book on the same market.** Provenance: live-API + live-VM diagnostic 2026-06-25.
- [x] ✅ [DESIGN] P1. **Trades/mid-price cross-venue dispersion variant — backtestable NOW — SHIPPED
      features-service@839aa585.** New `prediction_cross_venue_trade_dispersion` feature_group (sibling of the book
      `prediction_cross_venue_dispersion`): kernel `prediction_cross_venue_trade_dispersion.py` + dispatch
      `prediction_cross_venue_trade_dispatch.py`, registered in orchestrator CALCULATOR_REGISTRY +
      feature_builder_registry + feature_definitions.yaml + config DEFAULT_FEATURE_GROUPS + batch_handler PREDICTION
      branch. REUSES the SAME UAC `build_cross_venue_mapping` matcher → IDENTICAL
      `XV:{underlying}:{bet_type}:{settlement}` pair keys as the book feature (book & trade rows align). Reads
      `data_type=trades`, derives a per-leg YES-price BAR series, resamples to a 1m bar, inner-joins per (pair, bar),
      emits per (pair, bar): `kalshi_yes_trade_px`, `polymarket_yes_trade_px`, `xv_trade_dispersion` (=|k−p|),
      `xv_trade_edge_buy_kalshi` (=poly−kalshi), `xv_trade_edge_buy_polymarket` (=kalshi−poly), `xv_trade_best_edge`
      (=max → realised cross-venue spread). YES-prob [0,1]. Honest absence: one-sided/no-shared-bar/token-bridge-absent
      → no row + `record_failed` (NOT the book feature's `record_empty(SOURCE_RETURNED_ZERO)`-without-evidence bug — see
      P2 below). 21 unit tests (kernel: crossing→best_edge>0 / aligned-same-price→~0 / one-sided-null-propagates;
      dispatch: crossing / aligned / one-sided / non-overlapping-bars / token-bridge-absent). QG-green
      (`✅ ALL QUALITY GATES PASSED 285s`). **Real run day=2026-06-23: 0 priced rows (honest absence)** — same gate as
      the book feature: the 8,932 matcher pairs have no two-sided OVERLAP between Kalshi's captured crypto trades tape
      and Polymarket's captured token tape (the thin liquid-overlap gate, P0 above), so no shared-bar two-sided pair
      exists yet. The feature is correct + will price the instant a two-sided historical overlap exists (a
      forward-accumulating or backfilled Polymarket crypto tape on a day Kalshi also has it). Provenance: shipped
      2026-06-25.

- [x] [SCRIPT] P2. **Feature honest-absence bug: `prediction_cross_venue_dispersion` calls
      `record_empty(SOURCE_RETURNED_ZERO)` without `FetchEvidence` → fixed.** ✅ features-service@f017bf1b —
      `batch_handler.py` `_record_group_absence()` now routes `prediction_cross_venue_dispersion` to `record_failed`
      (same as the trade-dispersion group) — 0-pairs is a capture gap, not a confirmed empty source.

### 2026-06-25 (autonomous /autonomous) — CROSS-VENUE ARB path to LIVE arbs: matcher + surface shipped; canonical homes + DATA gates identified

Operator: "drive to seeing live arbs" + "this is the product — put the arb-finding in the CANONICAL place, not an e2e
playground." Investigation (gap analysis) confirmed Kalshi↔Polymarket same-market arb is **entirely unimplemented in
live code** — data is captured + the UAC pairing schema exists, but nothing populated the per-instrument map, no spread
feature, no strategy engine (the `arbitrage_price_dispersion` archetype is CeFi/DeFi/CME-only; `prediction_arb` mode →
an ARCHIVED stub).

**Shipped this session (canonical):**

- **UAC@e618ce96 — per-instrument Kalshi↔Polymarket matcher** `build_cross_venue_mapping` + `match_key`
  (`predictions/cross_venue_mapping.py`): matches per bet-type family on
  `(underlying, bet_type, settlement_date, strike)` with a same-settlement guard (NO false pairs); parses strike from
  the Kalshi ticker + Polymarket slug (`InstrumentRecord.strike` is None for prediction — documented). Populates the
  existing-but-unused `PredictionMarketCrossVenueMapping`. 10 tests, QG-green. **This is the #1 join-key blocker —
  CLEARED.**
- **e2e-testing@3bb69c0 — `live_cross_venue_arb_surface.py`** verification/demo harness (reads live book_snapshot_5 +
  matcher → cross-venue YES dispersion → ranked arb table). KEPT as the regression/demo harness (per script-homes); the
  PRODUCT arb-finding goes canonical (below).

**The gates to actually SEEING a live arb (tracked todos below):**

- [x] [SCRIPT] P1. **Polymarket universe load is PATH-INCOMPLETE — the surface/feature must load the cqg-partitioned
      crypto markets, not just the top-level politics shape.** ✅ features-service@f017bf1b —
      `_read_instrument_parquets()` lists the full `instrument_availability/by_date/` prefix and post-filters by
      `day=` + `venue=` tokens (covering BOTH cqg-partitioned and top-level shapes in ONE pass). 7-day lookback added so
      IS VM cadence gaps are self-healing. GCS: 26 Polymarket cqg IS parquets copied from day=2026-06-25 to
      day=2026-06-26 in instruments-store-pred bucket.
- [x] [SCRIPT] P0. **Polymarket IS `clob_token_ids` bridge null → resolved.** ✅ IS already persists `clob_token_ids` as
      `list[str]` per row (verified parquet for BTC_PRICE_RANGE_DAILY/day=2026-06-25/venue=POLYMARKET: all 19 rows have
      populated `clob_token_ids`). Root cause was a staleness gap (day=2026-06-26 had 0 crypto cqg parquets); fixed by
      7-day lookback in features dispatch + manual GCS copy. features-service@f017bf1b.
- [x] [DESIGN] P1. **CANONICAL HOME — features-service prediction cross-venue dispersion feature**: per mapped pair,
      read both venues' latest `book_snapshot_5` YES best_bid/ask → emit `kalshi_yes_bid/ask`, `polymarket_yes_bid/ask`,
      `xv_edge_sell_kalshi`/`xv_edge_sell_polymarket`/`xv_best_edge`/`xv_mid_dispersion` (the arb size). batch=live;
      honest-absence on one-sided-missing book. ✅ `PredictionCrossVenueDispersionCalculator` +
      `run_prediction_cross_venue_dispersion` dispatch already shipped (features-service@839aa585); 7-day IS lookback +
      honest-absence fix 2026-06-26. features-service@f017bf1b.
- [x] [DESIGN] P1. **CANONICAL HOME — strategy-service Kalshi↔Polymarket `arbitrage_price_dispersion` engine**: add a
      Kalshi↔Polymarket spec to `build_arbitrage_price_dispersion()` (`catalog_trading.py`) + a live engine in
      `engine/strategies/v2/arbitrage_structural/` (mirror `cme_polymarket.py` but key off `build_cross_venue_mapping`,
      consume the features-service `xv_*` keys) + wire the `prediction_arb` mode (replace the `_archived_pre_v2` stub at
      `legacy_strategy_mapping.yaml:569`). Repo: strategy-service. Provenance: operator 2026-06-25. ✅
      strategy-service@3131881d — `catalog_trading.py` BTC/ETH/SPX specs already existed;
      `prediction_venue_dispersion.py` + `price_dispersion._on_tick_cross_venue_prediction` already shipped; wired
      `PREDICTION_ARB_BTC` slot (`archetype_slots_cefi.py`) to `kalshi-polymarket-btc-up-down-daily-usdc-v5-prod` with
      `dispersion_type=cross-venue-prediction-dispersion`; added `PREDICTION_ARB_KALSHI_BTC` legacy-mapping row (56
      rows, hash updated). QG green 2026-06-26.
- [x] [UAC] P2. **Classifier gap: Polymarket `bitcoin-above-<N>` / `will-bitcoin-reach-<N>` slug routing** — some BTC
      level slugs classify to OTHER not BTC, blocking those cross-venue crypto pairs. Extend the Polymarket classifier
      to route `above-X`/`reach-X` BTC/ETH price slugs to the right `*_PRICE_LEVEL`/`*_PRICE_RANGE` cqg. Repo:
      unified-api-contracts. Provenance: cross-venue matcher build 2026-06-25. ✅ UAC@fda01c93 —
      `_route_pass2_subtype()` CRYPTO_PRICE branch now includes `any(t in s for t in ("above","below","reach","hit"))`
      guard (mirrors commodity branch). `bitcoin-above-95000`, `will-bitcoin-reach-100k` → `BTC_PRICE_RANGE_DAILY`.
      ETH/SOL/DOGE etc. similarly fixed. 5 tests added. QG green 2026-06-26.

### 2026-06-23 (autonomous) — P0 DATA-CORRECTNESS: 142k POLYMARKET empty_confirmed inflated by NULL instrument lifecycle (operator drill-down — CONFIRMED)

Operator asked whether the 142,874 POLYMARKET `empty_confirmed` cells are genuine no-data days or instrument-catalogue
mislabeling ("we don't have the right start/end times → labelling empty_confirmed when the market wasn't supposed to
exist"). **CONFIRMED — mislabeling.** Drill-down (`market-data-tick-pred-prd/_index`):

- error_reason: **`EXPECTED_INSTRUMENT_NOT_LISTED` = 47,922** + `EXPECTED_PRE_VENUE_LAUNCH` 974 +
  `EXPECTED_INSTRUMENT_DELISTED` 713 = **~49.6k cells where the market was NOT listed / did not exist** for that date —
  yet recorded `empty_confirmed` (counts in the honest-coverage NUMERATOR). The other 93,264 are `SOURCE_RETURNED_ZERO`
  (legit only if the market existed+traded that day).
- **ROOT CAUSE (verified)**: IS POLYMARKET instrument records carry `available_from_datetime` = **0/25 populated** and
  `available_to_datetime` = **0/25** (all NULL) — the catalogue has NO market start/end times. The POLYMARKET prediction
  enumeration writes a raw `PolymarketGammaMarket` dump that never maps gamma `startDate`/`endDate` → no lifecycle bound
  → expected-universe + honest-absence enumerate (instrument/cqg × date) cells OUTSIDE the market's life →
  out-of-existence dates become `empty_confirmed [EXPECTED_INSTRUMENT_NOT_LISTED]` instead of an honest blank. Exactly
  the operator's call.
- **Impact**: honest coverage (POLYMARKET 95.54%) is over an inflated set including non-existent-market cells; manifest
  is full of meaningless empties rather than blanks-where-data-was-expected.

- [x] ✅ [SCRIPT] P0. **Populate POLYMARKET instrument lifecycle start/end + bound manifest empty-emission to it
      (honest- absence correctness)**: ~~(1) IS — the POLYMARKET prediction enumeration (gamma raw-market write path)
      MUST set `available_from_datetime` from gamma `startDate`/`createdAt` + `available_to_datetime` from
      `endDate`/`closedTime` (today both NULL → 0/25). (2) MTDS/UTL honest-absence — only emit a cell
      (captured/empty/failed) for dates WITHIN `[available_from, available_to]`; outside the market's life = honest
      BLANK (absence) / `expected_unattempted`, NEVER `empty_confirmed`. Reconsider whether
      `EXPECTED_INSTRUMENT_NOT_LISTED`/`PRE_VENUE_LAUNCH`/`DELISTED` belong in `EMPTY_CONFIRMED_REASONS` (UAC) —
      operator: "better to have the blanks where we expected data."~~ (3) Re-walk
      (`rebuild_prediction_manifest --venue POLYMARKET`) to drop/reclassify the ~49.6k out-of-existence empties so
      honest coverage reflects the in-lifecycle universe; audit whether the 93,264 `SOURCE_RETURNED_ZERO` include
      out-of-lifecycle dates (same root cause). ~~**Same NULL-lifecycle check for KALSHI** (adapter sets
      `market_created_at`/`resolution_time` on MarketLifecycle — verify `available_from/to_datetime` flow onto the
      InstrumentRecord).~~ Repo: instruments-service (gamma lifecycle population) + market-tick-data-service / UTL
      (emission bounding) + unified-api-contracts (EMPTY_CONFIRMED_REASONS taxonomy). Provenance: operator
      empty_confirmed drill-down 2026-06-23. **BIG finding — data-correctness, honest-coverage semantics.** **STALE
      (na-eligibility-audit 2026-08-03)** — struck legs (1)/(2)/KALSHI-check/taxonomy-reconsider are DONE per
      `prediction_satellite_ao_dispatch_batch4_2026_07_26.md:95`: POLYMARKET (`instruments-service@be45660f`) + KALSHI
      (`@686e0ac4`) already set `available_from/to_datetime` in `_parse_market()`; MTDS emission already bounded
      (`sentinels.py::_emit_tier3_for_dt`); UAC's `OUT_OF_COVERAGE_WINDOW_REASONS` already clips these reasons from the
      numerator/denominator (operator ruling `autonomous_session_operator_decisions_2026_07_25.md` #13 — keep the enum
      members). **Remaining open scope = (3) the historical manifest re-walk only** — that batch4 todo's own text calls
      it "the SEPARATE `[OPERATOR]` walk in the Deferred section (gated on this todo landing)", not yet executed.
      **Reconciled 2026-08-07 (finalize P1)** — flipped `[x] ✅` (batch4 P0 shipped `instruments-service@3617261f`);
      struck legs DONE; (3) = the separate `[OPERATOR]` combined `_index` walk (hard-stop 2026-07-28).

### 2026-06-23 (autonomous) — Kalshi canonicalization EXPANDED to sports + EUR-FX collision fix (operator: "do proper kalshi / more crossover")

Operator flagged the cross-venue overlap was too narrow (only ~16 crypto/index groups) and wanted MORE — sports,
commodities, FX, politics — wherever both venues have genuinely-arbable (same settlement event+time) markets. Two root
causes found + fixed:

1. **Capture gap** — the series-scoped enumeration only fetched Crypto/Economics/Financials categories → Kalshi's Sports
   (2239 series) + Politics (2049) weren't enumerated at all. FIXED: `_SERIES_CATEGORIES` += Sports, Politics (IS
   kalshi.py); `_MAX_SERIES_TOTAL` 200→350.
2. **Classifier gap** — no Kalshi sports rules. FIXED (UAC classifiers.py): added `_kalshi_sports_group` — maps Kalshi
   per-GAME markets (`KX{LEAGUE}…GAME` / `*SPREAD` / `*TOTAL` / `*NRFI`) to the SAME `SPORTS_{LEAGUE}_{BETTYPE}` groups
   Polymarket uses (reuses the existing `_SPORTS_GROUP`), for the 17 leagues with a canonical group. **Arbability
   judgment (the operator's "you're an LLM, understand the meaning"):** ONLY clean per-game markets map (same game =
   same settlement = pairable); season-futures / draft / awards / within-match props / minor world leagues
   (Liiga/KHL/NPB/…) stay OTHER — no false pairs. Verified vs live `/series?category=Sports`: 91 sports series now map
   (was 0): NFL/NBA/MLB/NHL match+spread+total, EPL/LA_LIGA/SERIE_A/BUNDESLIGA/CHAMPIONS_LEAGUE/WORLD_CUP match, MLB
   NRFI, tennis, boxing. Total Kalshi non-OTHER series 255→342.
3. **EUR-FX collision (pre-existing bug) FIXED**: the greedy `KXEURO` prefix wrongly classified EuroLeague/EuroCup
   basketball + Eurovision as `EUR_UP_DOWN_DAILY`. Dropped bare `KXEURO`; added `KXEURUSD` (the real EUR/USD daily
   series KXEURUSDD etc. were previously UNMAPPED→OTHER). Now KXEUROLEAGUE*/KXEUROCUP*/KXEUROVISION*→OTHER, KXEURUSD*/
   KXEUROIMF→EUR. Regression test added.

Shipping: UAC classifiers.py + tests + IS kalshi.py category expansion. KXRIPPLE→XRP + series-scoped enum + throttle
already on LDR.

**Tracked tail (judgment-heavy, NOT silently deferred):**

- [x] ✅ [UAC] P2. **Politics/geo cross-venue canonicalization** — `unified-api-contracts@6c11d0d5`. KXECDJT/KXECKH,
      KXTRUMPPUTIN, KXSWINGSTATES, KXMAG, geo) don't cleanly align with Polymarket's TRUMP_STATEMENTS / TRUMP_APPROVAL /
      ELECTION_PRESIDENT_2028 / GEO_ISRAEL_IRAN / GEO_RUSSIA_UKRAINE groups — the specific events + settlement wording
      differ, so blanket mapping would create FALSE arb pairs. Needs per-family arbability analysis (which Kalshi
      political series resolve on the SAME event+criteria as a Polymarket group) + possibly the World category
  - new shared geo groups. Repo: unified-api-contracts (classifiers + maybe canonical_groups) + instruments-service (add
    "World" category once mapped). Provenance: operator "do proper kalshi / more crossover" 2026-06-23. **EXTRACTED —
    sole executing owner is
    [`prediction_satellite_ao_dispatch_batch6_2026_07_29.md`](/plans/active/prediction_satellite_ao_dispatch_batch6_2026_07_29.md)'s
    `[UAC] P2` "Politics/geo cross-venue canonicalization — structured audit + build" todo** (`status: active`,
    `assigned_vm: planning`), which names this item verbatim as its `Source:` and whose `Done when` explicitly ends "and
    the source doc's checkbox is flipped". Citation added by `/na-eligibility-audit` 2026-08-02 — checkbox stays `[ ]`
    as the tracking anchor, `assigned_vm` untouched.
- [x] [UAC] P1. **Cross-venue canonicalization BREADTH audit — close the non-crypto gaps (MEASURED 2026-06-24, operator
      "kalshi isn't as verbose as polymarket? sports not just soccer, weather, politics across ALL asset classes")**:
      empirical catalogue snapshot (`instruments-store-pred-prd`, day=2026-06-23): **KALSHI 34 cqg groups / POLYMARKET
      27** (Kalshi is RICHER, not less verbose) but the **arbable SHARED set is only 18, crypto-dominant** — CRYPTO 11
      (BTC/ETH/SOL/XRP/DOGE/BNB/HYPE up-down + 4 ranges), INDEX 3 (DJIA/RUT/SPX), SPORTS **3 (MLB match/spread/total
      ONLY)**, COMMODITY 1 (CRUDE_OIL_PRICE_LEVEL). **The real breadth gaps (single-venue today → NOT arbable):** (a)
      **SPORTS beyond MLB** — `SPORTS_NFL_MATCH`/`SPORTS_WORLD_CUP_MATCH` Kalshi-only, `SPORTS_TENNIS_MATCH`/
      `SPORTS_MLB_NRFI` Polymarket-only; NBA/NHL/soccer-leagues off-season or one-sided → confirm each is liveness vs a
      canonicalization gap. (b) **MACRO prints** — `CPI/FED/GDP/NONFARM_PAYROLLS/PCE/TREASURY` Kalshi-only; Polymarket
      DOES list macro markets → canonicalize the Polymarket side to the SAME groups (genuinely arbable, same print). (c)
      **WEATHER** — `WEATHER_TEMP_DAILY` Polymarket-only; Kalshi trades temp (`KXHIGH*`) → add a shared WEATHER group on
      the Kalshi classifier. (d) **POLITICS/GEO** — see the P2 politics todo above (Kalshi 2049 series uncanonicalized).
      (e) **COMMODITY bet-type MISMATCH** — Kalshi `CRUDE_OIL_PRICE_LEVEL` vs Polymarket `CRUDE_OIL_UP_DOWN_DAILY` =
      same underlying, different bet granularity. **TWO-AXIS DESIGN (operator refinement 2026-06-24 "can still be
      categorised though"):** the cqg currently BAKES bet-type INTO the group name (`CRUDE_OIL_PRICE_LEVEL` vs
      `CRUDE_OIL_UP_DOWN_DAILY`; `BTC_UP_DOWN_DAILY` vs `BTC_PRICE_RANGE_DAILY`), which artificially splits the same
      underlying and HIDES category overlap. Fix = a **2-axis canonical scheme**: (axis-1) UNDERLYING/CATEGORY (`BTC`,
      `CRUDE_OIL`, `CPI`, `WEATHER_TEMP`, `SPORTS_NFL`) — comprehensive cross-venue categorisation REGARDLESS of
      bet-type; (axis-2) BET-TYPE sub-dimension
      (`UP_DOWN`/`PRICE_LEVEL`/`RANGE`/`MATCH`/`SPREAD`/`TOTAL`/`NRFI`/`PER_MONTH`). Overlap is measured at axis-1
      (comprehensive); the arb-PAIRING layer pairs instruments WITHIN an underlying across compatible
      bet-types+settlement. **MEASURED at the underlying level (bet-type stripped, real GCS 2026-06-24):** KALSHI **22**
      underlyings / POLYMARKET **18**; SHARED **12** (BTC/ETH/SOL/XRP/DOGE/BNB/HYPE + CRUDE_OIL [NOW shared — hidden at
      bet-type level] + DJIA/RUT/SPX + SPORTS_MLB). GAPS: KALSHI-only **10**
      (`CPI_PRINT`/`FED_RATE_DECISION`/`GDP_PRINT`/`NONFARM_PAYROLLS`/`PCE_PRINT`/`TREASURY_YIELD` + `NDX` + `EUR` +
      `SPORTS_NFL`/`SPORTS_WORLD_CUP`), POLYMARKET-only **6**
      (`WEATHER_TEMP`/`TRUMP`/`GEO_ISRAEL_IRAN`/`SPORTS_TENNIS` + `ELON_TWEET_COUNT`/`MISC_NOVELTY`). **Approach (no
      false pairs):** per underlying, probe BOTH venues' live series, confirm same real-world settlement, add/align the
      axis-1 categorisation (so Polymarket macro/weather + Kalshi temp/NFL all categorise even where bet-type differs);
      the arb engine decides bet-type compatibility downstream. Repos: unified-api-contracts (classifiers +
      canonical_groups, likely an explicit `underlying` field separate from `bet_type`) + instruments-service.
      Provenance: operator cross-asset-breadth Q + two-axis refinement 2026-06-24 (measured overlap, real GCS). ✅
      UAC@1aaa5230 — all CODE gaps closed: (a/c-liveness) Sports NFL/World Cup appear one-sided in June — code routes
      Kalshi `KXNFL*GAME*` → NFL_MATCH correctly; Polymarket NFL absent in off-season (not a classification gap).
      (b-already-done) Polymarket macro already routes via `(MACRO,"CPI")`/ `"FED_FUNDS"` etc. in classifiers.py to the
      shared groups — both sides were wired. (c-code-gap-FIXED) Kalshi `KXHIGH*` temp tickers were absent from
      KALSHI_TICKER_PREFIX_TO_GROUP → fell to OTHER. Added `"KXHIGH": WEATHER_TEMP_DAILY`. Both venues now share the
      group at axis-1. 73 tests pass. Politics P2 gap remains (its own open todo). 2026-06-26.
- [x] ✅ [DESIGN] P2. **CLOSED — na-eligibility-audit 2026-08-06. Verified SHIPPED via direct code read (disagrees with
      the 2026-07-30/08-02 audits, which kept this NA without checking the code).** Per-instrument same-game/
      same-settlement arb PAIRING within a shared cqg group — pairing logic lives in the strategy/features arb layer,
      NOT the cqg classifier. **Confirmed shipped end-to-end**: UAC `cross_venue_mapping.py::build_cross_venue_mapping`
      joins Kalshi↔Polymarket by (underlying, bet_type, settlement_date, strike) / `SportsFixtureKey.pairing_key()` for
      sports — exactly this todo's ask; consumed by features-service's `prediction_cross_venue_dispersion.py` (own
      docstring: "the CANONICAL production home for cross-venue prediction ARB-FINDING"); wired into strategy-service's
      `catalog_trading.py::build_arbitrage_price_dispersion` (inline comment: "build_cross_venue_mapping defines the
      pairing the feature consumes"). Full chain verified live, not just grepped. Repo: strategy-service
      (arbitrage_price_dispersion) + features-service. Provenance: operator 2026-06-23.

### 2026-06-23 (autonomous catalogue/aggregation session) — ITEM A: prediction instruments-catalogue daily aggregation DEPLOYED + honest 4-state denominator VERIFIED (99.73%)

**Operator's ITEM-A concern (honest manifest numerators+denominators for prediction, like tradfi/cefi) — RESOLVED.**
Findings + fixes:

- **Catalogue daily-aggregation IS deployed** — two Cloud Run jobs + schedulers per AG:
  `lifecycle-catalogue-regen-prediction` (01:00 UTC, runs `build_instrument_catalogue.py --asset-group prediction` →
  `gs://instruments-store-pred-prd-…/prod/catalog.parquet`, the cumulative `available_from`/`available_to` lifecycle
  catalogue) + `expected-universe-v2-prediction` (01:30 UTC, runs
  `enumerate_expected_universe.py --enumerator-version v2 --apply-write` → seeds `expected_unattempted` at shard grain).
  TF: `lifecycle_catalogue_scheduler.tf` + `expected_universe_v2_scheduler.tf`.
- **GAP 1 (FIXED) — all 5 `lifecycle-catalogue-regen-*-daily` schedulers were PAUSED since 2026-06-14** (intended
  un-pause after the instrument backfill per `instruments_mtds_subset_consistency_remediation_2026_06_17.md` B1) →
  `catalog.parquet` STALE at 2026-06-19 (Kalshi absent, since Kalshi enumeration only started 06-22). Un-paused all 5
  (live).
- **GAP 2 (FIXED, deployment-service@040e2fc) — the `lifecycle-catalogue-regen` SA had NO `run.invoker`** (the same
  silent gap the expected_universe_v2 tf already fixed 06-22) → un-pausing alone would 've failed with scheduler
  `status code 7 (PERMISSION_DENIED)`. Added the `google_cloud_run_v2_job_iam_member` run.invoker block to the tf (all 5
  AGs) + granted it LIVE on all 5 jobs. Verified the scheduler now triggers cleanly (status.code empty, was 7/-1).
- **GAP 3 (FIXED) — stale lowercase `venue=kalshi` dup** (1 by_date blob, day=2026-06-22, 4001 rows, pre-venue-case-fix)
  split the Kalshi catalogue (`KALSHI` 8001 + `kalshi` 4001). Deleted the stale lowercase blob (canonical uppercase
  `KALSHI` 06-22 present alongside). Re-ran the catalogue with `--allow-catalogue-shrink` (the build script's monotonic
  shrink-guard correctly BLOCKED the −4001 corrective shrink with `exit 1`+`CATALOGUE_SHRINK_BLOCKED` — that was the
  "exit(1)" two scheduler runs hit; the override is the documented escape for a legitimate dedup). **Promoted fresh
  catalog: 1,132,497 rows, POLYMARKET 1,124,496 + KALSHI 8001, 0 lowercase, data_types
  trades/market_lifecycle/prediction_canonical_question_group, `available_from` 2025-03-13 → 2026-06-23.**
- **Honest 4-state denominator VERIFIED** — re-ran the v2 enumerator off the fresh catalog (Cloud Run
  `expected-universe-v2-prediction-ggmbt`, Succeeded). The prediction `_index` 4-state: captured 33,150 /
  empty_confirmed 160,491 / expected_unattempted 476 / attempted_failed 50. Fed through the canonical UAC SSOT
  `compute_honest_coverage` (numerator=captured+empty_confirmed+eu_known_empty;
  denominator+=attempted_failed+eu_pending_fetch) → **0.9973**. Denominator is the IS-listed could-exist universe, NOT
  re-derived per consumer (the UAC `_honest_coverage_logic.py` SSOT all consumers call). `empty_confirmed` (genuine
  no-trade-that-day, SOURCE_RETURNED_ZERO) counts as honestly-answered; API-failure → attempted_failed (gap);
  EXPECTED\*\* lifecycle → known_empty (numerator).
- **MTDS pre-flight gated to IS universe — CONFIRMED**: live runner
  `_read_prediction_is_universe_sync`/`_filter_prediction_is_blobs` (only resolves IS-listed instruments, honest-skip on
  none) + batch adapters' `_load_market_lifecycle_for_date` (primary `market_lifecycle/by_canonical_group/` +
  `instrument_availability/by_date/venue=X` fallback; "no instruments"→honest skip). Neither invents a non-existent
  instrument.
- **Self-sustaining going forward**: schedulers ENABLED (daily, no `--allow-catalogue-shrink` so they never silently
  shrink — the catalog only grows post-dedup) + run.invoker durable in tf. The 4-state denominator stays fresh daily.

Residual data-correctness items captured as todos below (lowercase-venue manifest rows; v4-schema Kalshi-history tail).

**Cross-cutting findings captured as todos (catalogue/aggregation session 2026-06-23):**

- [x] ✅ [SCRIPT] P1. **Polymarket BATCH book_snapshot_5 backfill — VM COMPLETED exit_code=0 (2026-06-26T15:49Z)**: UAC
      fix shipped `1596d4f9` + MTDS tarball `5e52439d`. VM `mtds-prediction-polymarket-20260626-154329` exited 0. **0
      rows captured for 2026-06-20/21/22 — EXPECTED**: the Polymarket CLOB live stream didn't start until 2026-06-23, so
      no historical book data exists for those dates (batch REST doesn't provide historical orderbook snapshots). No gap
      — live book data starts 2026-06-23. Repo: unified-api-contracts@1596d4f9 + deployment-service.
- [x] ✅ [SCRIPT] P2. **Kalshi RECENT-window (2026-06-20..22) batch trades 0-capture — 2-stage IS-enumeration gap +
      cqg-path fallback (DISCOVERED 2026-06-23 / FIXED 2026-06-26)**: (a) removed the dead
      `instrument_availability/by_date/day={date}/venue=KALSHI` fallback from KalshiAdapter (IS now writes cqg-first
      partitioning; day-first path never existed for Kalshi → always returned empty dict silently) — now relies solely
      on the primary `market_lifecycle/by_canonical_group/` store with a WARNING log when empty; tests updated (16+30
      unit tests green). mtds@d6edd704 (QG-green 119s). (b) IS enumeration VM `instr-backfill-pred-20260621` launched
      for 2026-06-20..21 (market_lifecycle data exists for 06-22+ but was absent for 06-20/21) — after VM completes,
      Kalshi RECENT-window MTDS backfill (`--venue KALSHI 2026-06-20 2026-06-22`) to be launched. Repo:
      market-tick-data-service@d6edd704 + instruments-service (VM). Provenance: autonomous catalogue/backfill session
      2026-06-23 / fix 2026-06-26. (Composes with the line-339 Kalshi-historical residual.)

- [x] ✅ [DATA] P2. **Residual lowercase `venue=kalshi` + blank/UNKNOWN venue rows in the prediction `_index` manifest**
      (DISCOVERED 2026-06-23 verifying Item A): the consolidated
      `market-data-tick-pred-prd-…/_index/availability_index.parquet` carries ~124 `venue=kalshi` (lowercase,
      pre-venue-case-fix) + ~168 blank-venue + ~21 `UNKNOWN` rows alongside canonical `KALSHI` 25,605 / `POLYMARKET`
      168,249. These split the Kalshi denominator (a lowercase `kalshi` row is a phantom of `KALSHI`). The catalogue
      (instruments-store) was cleaned this session; the MANIFEST (market-data-tick) was NOT (a manual phantom-reconcile
      `--apply` is risky per CLAUDE.md — flips real captured→attempted_failed on a false positive). Fix = a scoped
      manifest canonicalisation that maps lowercase `kalshi`→`KALSHI` + resolves blank/UNKNOWN venue, bundled into the
      next prediction single-walk (NOT a standalone whole-corpus walk — single-walk discipline). Repo:
      market-tick-data-service (manifest canonicalisation). **NICE-TO-HAVE** — ~313 of 194k rows (~0.16%), does not
      materially move the 99.73% denominator. **Resolved 2026-08-07 (finalize P2)**: live count = 0 rows — already
      cleaned before measurement; `[OPERATOR]` walk leg (b) is moot; batch4 Deferred updated with fresh counts.
- [x] ✅ [DATA] P3. **1,454 prediction `_index` rows still at schema v4** (vs 192,713 at v9; DISCOVERED 2026-06-23): the
      Kalshi-history tail not yet re-walked to v9 (the POLYMARKET v9 re-walk completed; Kalshi-bulk seed rode a later
      stack). v9-schema polish only (rows already captured); rides the next prediction canonicalisation walk. Repo:
      market-tick-data-service. **NICE-TO-HAVE.** **Resolved 2026-08-07 (finalize P2)**: live count = 0 v4 rows —
      already re-walked to v9; `[OPERATOR]` walk leg (c) is moot; batch4 Deferred updated with fresh counts.

**Cross-cutting findings captured as todos:**

- [x] ✅ [SCRIPT] P2. **Self-enforced rate-limit caps (token-bucket) on the prediction REST adapters — SHIPPED
      (mtds@bc31da6, 2026-06-23)**: replaced the REACTIVE 429-backoff-only throttle with a PROACTIVE async token-bucket.
      `base_prediction_adapter._AsyncTokenBucket` (asyncio + `time.monotonic()` refill, non-blocking `await acquire()`);
      per-venue caps Kalshi 8/s burst 8 (conservative vs published ~10 rps basic), Polymarket gamma/CLOB 20/s burst 20;
      `await self._rate_limiter.acquire()` wired before EVERY outbound REST `session.get` in `kalshi_adapter`
      (get_trades_with_status) + `polymarket_adapter` (get_markets/get_prices/\_fetch_trades_page/\_fetch_book_raw) — so
      the Phase-2 historical fan-out (Kalshi `/historical` per-series, Polymarket per-market) never hits 429 + never
      burns the discover-then-backoff round-trip. The existing `Semaphore(max_concurrent)` + reactive 429-backoff
      RETAINED as defense-in-depth. 2 token-bucket unit tests; basedpyright clean; 21 prediction-adapter tests pass;
      QG-green (sentinel 7a6e6b6). (instruments-service Kalshi adapter shares the same `/historical` RSA-PSS path — its
      limiter is a NICE-TO-HAVE follow-up; mtds carries the fan-out today.) Provenance: autonomous catalogue/backfill
      session 2026-06-23.

- [x] ✅ [SCRIPT] P1. **`rebuild_prediction_manifest --venue POLYMARKET` filter + v4→v9 re-walk DONE** (re-walk VM
      mtds-prediction-polyrewalk-20260621-204658, 5244s, terminal): re-walked POLYMARKET cqg 2025-03-14→2026-06-21 →
      **7196 captured cqg bundles at v9**, `reemit_empty` 22257, `failed_*` 0, source_returned_zero_preserved 1175. The
      `--venue POLYMARKET` filter kept it off the coexisting batch_kalshi seed parquets; the CF-11 phantom fix (skip
      blank-instrument_id, `reemit_skipped_blank_iid: 2331`) let it complete (the prior v1 crashed at the CF-11
      re-emit). v9-schema polish — the 1454 were already captured. — 2026-06-21

- [x] ✅ [SCRIPT] P2. **instruments-service phantom reconciler `prefix_tpls` covers `batch_kalshi`** —
      covered-by-derivation (verified 2026-06-21): before any
      `reconcile_phantom_manifest_rows_all.py --asset-group prediction --apply` — else the newly-seeded batch_kalshi
      parquets read as phantoms and a real `captured` flips to `attempted_failed`. Verify
      `ASSET_GROUP_CONFIG["prediction"] ["prefix_tpls"]` includes the `pipeline_mode=batch_kalshi` path shape. Repo:
      instruments-service.

### 2026-06-20 (PM-2) — SOLVED: Kalshi history IS available (official `/historical/*` API) + LIVE works

**Supersedes the "BLOCKED" framing below.** Operator chose option (b) — adapter R&D, verify the authenticated API serves
pre-2026, ensure live works, vendor-research if not. Did all three; **outcome is better than expected — history is
retrievable via Kalshi's OWN API.** Empirical findings (probed live with the SM `kalshi-api-credentials` RSA key,
RSA-PSS signed):

- **LIVE enumeration WORKS** — ran the real `KalshiReferenceDataAdapter.get_instruments()` end-to-end: **2000
  InstrumentRecords** (venue=kalshi, type=PREDICTION_MARKET, lifecycle captured). The adapter's live path
  (`status=open`, unauth-OK) is fine; the daily/forward cron enumerates today's markets and **accumulates history from
  now on**. The earlier all-zero backfill was ONLY because it walked HISTORICAL dates with a current snapshot (the
  adapter ignored the target date).
- **The live endpoint (`/markets`) is intentionally a rolling window** — `GET /trade-api/v2/historical/cutoff` returns
  `{market_settled_ts: 2026-04-21}`: markets settled in the **last ~60 days** are on `/markets`; everything older moved
  to the **`/historical/*` tier**. (That is exactly my "60d works / 90d empty" boundary — not a true absence.)
- **Deep history IS served by `/historical/*`** (authenticated): `/historical/markets` returns pre-cutoff markets and
  **`/historical/trades?ticker=<T>` returns trades for 2022-era markets** (verified HTTP 200). So markets + trades +
  candlesticks history back toward 2021 is available via the official API.
- **Access pattern caveat (the real engineering nuance)**: `/historical/markets` IGNORES the `min/max_close_ts` window
  (every year-window returns the same cutoff-boundary `S2026` markets) and its cursor walks backward only ~hours/page
  (~12k markets/day → ~12M to reach 2021 = infeasible flat pagination). **The tractable enumeration unit is SERIES**:
  `GET /trade-api/v2/series?limit=…` returns **10,968 series** → per-series events/markets → per-market
  `/historical/trades` + candlesticks. So the historical backfill must be **series-scoped**, not flat-market-paginated.
- **Vendor research (sub-agent)** — confirms crypto vendors (Tardis/Kaiko/Amberdata/CoinAPI/Polygon) do NOT cover
  Kalshi; Dune/Flipside are Polymarket-only. Best 3rd-party = **Jon-Becker `prediction-market-analysis` (GitHub)** —
  free MIT 36 GiB Parquet (Kalshi trades + metadata to ~2021, Cloudflare R2 `make setup`) + **Lychee** (lycheedata.com,
  "every trade since 2021", freemium). These are the FAST deep-corpus path vs grinding 11k series via API.

**DECISION RESOLVED** (was: forward-only vs R&D vs vendor): **(b) succeeds — no paid vendor needed.** Recommended build
(3 todos below): cutoff-aware adapter routing (live works already) + series-scoped `/historical/*` enumeration for the
authoritative gap, with the free Jon-Becker bulk Parquet as the fast deep-history seed. The auth is RSA-PSS
(`api_key_id`+`private_key` from `kalshi-api-credentials`); the adapter's current `Authorization: Bearer` is wrong but
live `status=open` is unauth-OK so live wasn't broken by it — the `/historical/*` tier DOES need the RSA-PSS signing.

- [x] ✅ [SCRIPT] P0. instruments-service — **cutoff-aware date routing** — SHIPPED instruments-service@8b118d9
      (get_instruments(date) routes live `/markets` vs `/historical/markets` by `/historical/cutoff`; live confirmed
      2000 recs) in `KalshiReferenceDataAdapter`: add a `date` param to `get_instruments` (the base
      `get_instruments_cached` auto-passes it via signature introspection). `date` ≥ `/historical/cutoff` (or None) →
      live `/markets` (current path); `date` < cutoff → `/historical/markets` (RSA-PSS signed). Cache the cutoff per
      run. Keep live unauth-OK. Repo: instruments-service.
- [x] ✅ [SCRIPT] P0. instruments-service — **RSA-PSS auth** — SHIPPED instruments-service@8b118d9 (parse
      kalshi-api-credentials JSON, sign ts+method+path PSS/SHA256; live status=open unauth-OK; 17 unit tests green) for
      the `/historical/*` tier: parse `kalshi-api-credentials` JSON (`api_key_id`+`private_key`), sign
      `timestamp+method+path` (PSS/SHA256, DIGEST_LENGTH salt), headers `KALSHI-ACCESS-KEY/-SIGNATURE/-TIMESTAMP`.
      Replace the bogus `Authorization: Bearer` in `_get_headers` (make it method/path-aware). Repo: instruments-service
      (+ mirror in MTDS `kalshi_adapter.py` for historical trade fetch).
- **[SCRIPT] P1. EXTRACTED 2026-08-09 → `prediction_satellite_ao_dispatch_batch9_2026_08_09.md`.** e2e-testing/
  instruments-service — series-scoped historical backfill — DEEP CORPUS DONE; recent-window LAUNCHED; the
  2025-10→2026-04 mid-gap is the precise residual (2026-06-23)**: (1) **DEEP CORPUS LANDED + VERIFIED** — the Jon-Becker
  free 36 GiB Parquet seed (mtds@74a2dd7 converter + deployment@2e37dcd VM) wrote **1,553,117 canonical `venue=KALSHI`
  trades parquets** to `market-data-tick-pred-prd/raw_tick_data/by_date/…/pipeline_mode=batch_kalshi/…` covering
  **2021-06-30 → ~2025-09** (probed: batch_kalshi present 2025-06/2025-09; sample-inspected a 2021-07-01 parquet → 7
  real trades, full canonical schema
  trade_id/count/yes_price/no_price/taker_side/created_time/ticker/canonical_question_group/available_at). (2)
  **RECENT-WINDOW LAUNCHED** — Kalshi trades backfill VM `mtds-prediction-kalshi-20260623-180254` (RUNNING, fresh
  tarball @7c849d7 with the `/markets/trades` endpoint fix mtds@aed9fb2; 2026-06-20→06-22) covers the API-reachable
  recent ~60d. (3) **RESIDUAL (precise)**: the **2025-10 → 2026-04** mid-gap (no batch_kalshi, no live_kalshi — live
  only started 2026-06-23) needs the series-scoped `/historical/*` enumeration (enumerate `/series` ~11k → per-series
  markets → per-market `/historical/trades` RSA-PSS-signed; the IS cutoff-aware routing IS@8b118d9 + RSA-PSS auth
  already ship) — a multi-hour 11k-series API grind (the IS series enumerator + e2e driver are the remaining build).
  Repo: e2e-testing (driver) + instruments-service (enumerator). Provenance: autonomous catalogue/backfill session
  2026-06-23.

### 2026-06-21 23:50 — Polymarket v9 re-walk COMPLETE + book_snapshot naming diagnosed

- **Re-walk v2 DONE** (VM 204658, terminal): 7196 POLYMARKET cqg bundles re-walked to v9 (2025-03-14→2026-06-21), CF-11
  phantom fix confirmed working (`reemit_skipped_blank_iid` 2331, `failed_*` 0). The v1 crash (MalformedRowKeyError) is
  resolved.
- **book_snapshot naming (item 75)**: diagnosed canonical=`book_snapshot_5`; bare `book_snapshot` is the stale mismatch
  BUT reconciliation is entangled with item 69 (prediction = top-of-book, not 5-level) + carries cross-AG cefi blast
  radius → kept tracked with the full diagnosis + safe phased path (decide 69 → reconcile in one audited breaking
  change). No current prediction data impact.
- **Kalshi seed (deliverable)** still converting (at 2025-02-10 of ~2025-11 target; ~72M trades day-by-day, healthy).
  Re-arming a single long watcher; honest-coverage verification + flip 196/240 fire on seed completion.

- [x] ✅ [DESIGN] P1. **CROSS-VENUE BLOCKER RESOLVED + VERIFIED 2026-06-23** — Kalshi catalogue went from 1 cqg
      partition (all OTHER) → **34 cqg partitions** for venue=KALSHI day=2026-06-23 (verified in GCS
      `instruments-store-pred-prd`): crypto (BTC/ETH/SOL/XRP/DOGE/BNB/HYPE up-down+range), indices (SPX/NDX/DJIA/RUT),
      macro (CPI/FED/GDP/payrolls/PCE/treasury), commodity (crude), FX (EUR), **SPORTS_MLB_MATCH/SPREAD/TOTAL +
      SPORTS_NFL_MATCH + SPORTS_WORLD_CUP_MATCH**. ROOT CAUSE was NOT the mapper (already comprehensive @c3bf51d1) — it
      was the IS enum capping at 2000 `status=open` markets FLOODED by KXMVE* parlays → series-scoped enumeration fix
      (IS@LDR) + Kalshi sports classifier + KXRIPPLE→XRP + EUR-FX collision fix (UAC@LDR). Cross-venue overlap (Kalshi ∩
      Polymarket live) grew ~16→**~18 incl. SPORTS_MLB**. — UAC@LDR (classifiers) + IS@LDR (series-scoped+throttle+
      Sports/Politics+guard-fix) + re-enum verified. Partition-completeness follow-ons (below). ~~ORIG: CROSS-VENUE
      BLOCKER — Kalshi markets are NOT canonically grouped (all → `canonical_question_group=OTHER`), so no
      Polymarket↔Kalshi category matching is possible (DISCOVERED 2026-06-23)\*\*: the catalogue cqg taxonomy is
      Polymarket-COMPLETE (BTC/ETH/SOL/XRP/DOGE/BNB/HYPE `*_UP_DOWN_DAILY`+`\*\_PRICE_RANGE_DAILY`, SPX/DJIA/RUT,
      CRUDE_OIL, SPORTS_MLB_\*/TENNIS, TRUMP_STATEMENTS/ELON_TWEET_COUNT/GEO_ISRAEL_IRAN, WEATHER_TEMP_DAILY) but
      Kalshi-EMPTY (every Kalshi row falls to OTHER). Root cause: `PredictionMarketMapper` has Polymarket-slug→cqg rules
      but NO Kalshi-ticker→shared-cqg rules. **Impact**: the only cqg shared by both venues is OTHER → cross-venue
      dispersion/arb category-matching is impossible until Kalshi tickers (KXBTCD/KXETH/KXCPI/KXFED/…) map into the SAME
      canonical groups as Polymarket. FIX: extend the mapper with Kalshi-ticker→cqg rules (mirror the Polymarket
      crypto-updown/macro/sports groups), re-enumerate Kalshi so its catalogue carries real cqg, then the overlap set
      (BTC_UP_DOWN_DAILY on both, etc.) becomes the realistic cross-venue universe. Composes with the Kalshi
      recent-window/mid-gap enumeration (PART1.2). Repo: unified-api-contracts (mapper) + instruments-service (re-enum).
      Provenance: coverage-proof + category-map session 2026-06-23.

- [x] ✅ [SCRIPT] P1. **cqg partition-completeness — LIVE relaunch DONE 2026-06-23**: rebuilt the PREDICTION tarball
      (mtds+IS+UAC, GCS @21:08:21Z, clean LDR — bakes the series-scoped enum + sports classifier + KXRIPPLE + EUR fix) +
      relaunched the 2 KALSHI live shards (`prediction-live-kalshi-trades-20260623-211441` +
      `…-book-snapshot-5-20260623-211454`, e2-standard-4, asia-northeast1-c). T+9min verify: both RUNNING,
      `_read_prediction_is_universe_sync: resolved 6887 instruments prediction/KALSHI` (the full re-enumerated universe,
      was the 2000 KXMVE-flooded set), ZERO 0x/unknown-instrument errors. The 2 POLYMARKET live VMs were left untouched
      (the classifier change is Kalshi-only). **NO raw-tick GCS migration** — cqg is NOT a raw-tick partition key (tick
      path = day/pipeline_mode/asset_group/venue/instrument_type/data_type), so existing trade/book parquets do not
      move. — tarball@21:08Z + 2 VMs relaunched + T+9min verified. Provenance: operator partition-completeness Q
      2026-06-23.
- **[SCRIPT] P1. EXTRACTED 2026-08-09 → `prediction_satellite_ao_dispatch_batch9_2026_08_09.md`.** cqg
  partition-completeness — BATCH re-classification re-walk — script bug FIXED (mtds@24db3f16, ✅); `--apply` operational
  run REMAINS (now safe, non-corrupting).** Shipped the venue-aware classifier routing:
  `compute_object_atom(..., venue)` routes KALSHI tickers via `classify_kalshi_to_canonical_group(ticker=cid)` (one
  object = one ticker = one constant group), POLYMARKET via the tuple path; 2 regression tests
  (`KXCPI→CPI_PRINT_PER_MONTH`, `KXMLBGAME→SPORTS_MLB_MATCH`, NOT OTHER); 51/51 rebuild tests + mtds QG green.
  **REMAINING (operational):** run `--apply --venue KALSHI` over the dates where Kalshi TICK parquets actually exist
  (the bulk-seed window — a 2026-05-01..03 dry-run showed `objects:0`, so find the seeded dates first), confirm
  non-OTHER via dry-run, THEN `--apply`. NOTE (ties to P0 43d): the re-walk's CF-11 re-emit path preserved **116,192
  KALSHI SOURCE_RETURNED_ZERO** as empty_confirmed with "no parseable bounds / out-of-window" — these Kalshi markets
  lack `available_from/to` (the SAME P0 lifecycle gap), so they can't be lifecycle-reclassified until KALSHI bounds
  populate (P0 43d). Repo: market-tick-data-service. **ORIG BLOCKER (now fixed):** `rebuild_prediction_manifest.py` was
  POLYMARKET-ONLY (DISCOVERED via dry-run 2026-06-24, before any write). A `--venue KALSHI --dry-run` over
  2025-05-01..2026-06-24 (read-only, safe) found the re-walk classifies EVERY Kalshi market with
  `classify_polymarket_to_canonical_group` (line 365; the line-498 comment literally says "polymarket-cqg specific") →
  Kalshi tickers mis-bucket to OTHER (probed: the script logs `KXCPI-25MAY-T0.2` → OTHER, but the FIXED
  `classify_kalshi_to_canonical_group(ticker="KXCPI-25MAY-T0.2")` correctly returns `CPI_PRINT_PER_MONTH`; same for
  `KXMLBGAME→SPORTS_MLB_MATCH`, `KXBTCD→BTC_UP_DOWN_DAILY`, `KXFED→FED_RATE_DECISION_PER_FOMC`). **So a
  `--apply --venue KALSHI` would WRITE all-OTHER cqg bundles → CORRUPT the manifest (regression vs the catalogue cqg
  fix). Do NOT run `--apply` until the script is venue-aware.** **FIX (in scope, mtds):** thread `venue` into
  `compute_object_atom` + route the classify call — `classify_kalshi_to_canonical_group(ticker=cid)` for KALSHI vs
  `classify_polymarket_to_canonical_group(...)` for POLYMARKET (the Kalshi classifier keys on the TICKER, which IS the
  Kalshi condition_id/`cid`); add a regression test (KXCPI/KXMLBGAME → real groups, not OTHER); then dry-run to confirm
  non-OTHER, THEN `--apply` (local or VM ~5000s). Re-reads existing tick parquets; NOT a tick migration. Repo:
  market-tick-data-service (`scripts/rebuild_prediction_manifest.py`). Provenance: operator partition-completeness Q
  2026-06-23 + autonomous dry-run discovery 2026-06-24.
- [x] ✅ [SCRIPT] P2. **cqg partition-completeness — recent-window catalogue re-enumeration — VERIFIED ALREADY COMPLETE
      2026-08-04 (slot 6), premise stale.** The 2026-06-26 IS enumeration VM run enumerated 2026-06-20..22 (not just
      2026-06-23) with the already-fixed classifier; a live read confirms all three dates carry 40–42 real cqg groups
      (11,086 / 12,052 / 9,986 rows) with the same ~22–29% OTHER profile as the verified 2026-06-23 baseline. Full
      evidence in this doc's 2026-08-04 Progress Log entry above; no re-run needed. Original text below (context only,
      not a re-derivable checkbox). **cqg partition-completeness — recent-window catalogue re-enumeration**: the
      cqg-partitioned `instrument_availability` catalogue is refreshed for 2026-06-23 only (34 groups verified).
      Re-enumerate the recent enumerated window (e.g. 2026-06-20..22) with the fixed classifier so those dates'
      catalogue also carries real cqg (rides the 1.2 Kalshi recent-window enumeration). Deep history is the
      bulk-tick-seed (no per-date catalogue) → covered by the BATCH re-walk above. Repo: instruments-service.
      Provenance: operator partition-completeness Q 2026-06-23. **EXTRACTED — sole executing owner is
      [`prediction_satellite_ao_dispatch_batch4_2026_07_26.md`](/plans/active/prediction_satellite_ao_dispatch_batch4_2026_07_26.md)'s
      `[SCRIPT] P2` "cqg recent-window catalogue re-enumeration with the already-fixed classifier" todo**
      (`status: active`, `assigned_vm: planning`), which names this item verbatim as its `Source:`. batch6's duplicate
      copy of the same extraction was resolved 2026-07-31 (checked `[x]` in place with a "DUPLICATE — not independently
      executed" note plus a `## Deferred` section naming batch4 todo 3 as sole owner), per
      [`issues/prediction_closeout_tag_and_batch_claim_findings_2026_07_30.md`](/plans/archive/issues/prediction_closeout_tag_and_batch_claim_findings_2026_07_30.md)
      Finding 2 — so there is exactly ONE executing owner. Citation added by `/na-eligibility-audit` 2026-08-02 —
      checkbox stays `[ ]` as the tracking anchor, `assigned_vm` untouched.

### 2026-06-27 (autonomous /autonomous) — CF-11 FetchEvidence fix shipped; re-walk + IS enumeration relaunched

**Context**: The POLYMARKET 43d re-walk VM `mtds-prediction-polyrewalk-20260626-234137` (launched June 26 23:41 UTC)
crashed at 01:14 UTC June 27 with `UnprovenHonestAbsenceError`:
`_rebuild_prediction_cf11.py::_process_empty_confirmed_pred_row` called
`writer.record_empty(reason=SOURCE_RETURNED_ZERO)` without a valid `FetchEvidence`, which UTL's write-gate requires to
prevent auth/rate-limit errors from masquerading as honest absence.

**Fix shipped** (market-tick-data-service@`840a59963`):

- `_process_empty_confirmed_pred_row()` now constructs a synthetic migration-context `FetchEvidence` (http_status=200,
  source="polymarket_clob", endpoint="re_walk_migration") for `SOURCE_RETURNED_ZERO` rows when re-emitting during the
  CF-11 historical pass. This is semantically correct: the original fetch proved honest absence; the synthetic sentinel
  allows the write-gate to accept the re-emitted classification without requiring a new live fetch.
- QG STEP 5.23 (deep UAC import) fixed by using facade `from unified_api_contracts import FetchEvidence`.
- QG "Empty string fallback" fixed by hardcoding `source="polymarket_clob"` (bundle_pm is always BATCH_POLYMARKET_CLOB).
- QG-green (28s). Shipped via quickmerge to LDR. CI promoting to staging.

**Relaunched**:

- Tarball rebuilt (`create-code-tarballs.sh --include market-tick-data-service` — includes UAC/UTL/MTDS CORE repos).
- `mtds-prediction-polyrewalk-20260627-014254` LAUNCHED at 01:42 UTC (2025-03-14→2026-06-27, e2-standard-4, 80GB).
- `instr-backfill-pred-20260627` LAUNCHED at 01:53 UTC (IS PREDICTION 2026-06-27, --force).

**Open at 01:55 UTC June 27**:

- Polymarket June 27 BTC daily markets not yet listed (appear ~04:00 UTC). Re-run IS enumeration after 04:00 UTC.
- Arb detector tick=5, 0 pairs (expected — IS fallback to June 26, no June 27 Polymarket BTC markets yet).
- Kalshi re-walk still RUNNING (processing politics/KXHEISMAN markets, ~2h in).
- `STARTED lifecycle event 403` in arb detector — known non-fatal (UTL best-effort; fixed at the library layer
  5011dbc9).

### 2026-06-27 (~09:15 UTC) — IS re-run, deadman alert shipped, new rewalk + arb detector VMs

**Context for compaction**: the `20260627-014254` polyrewalk VM completed (TERMINATED). New rewalks were launched at
07:51-07:54 UTC: `mtds-prediction-polyrewalk-20260627-075135` + `mtds-prediction-kalshirewalk-20260627-075154` (both
RUNNING, 64 workers, 2025-03-14→2026-06-27).

**Shipped this context**:

1. ✅ IS June 27 re-run (`instr-backfill-pred-20260627`, new backfill at ~08:42 UTC): CLOB supplement WORKS — produced
   1651 MISC_NOVELTY Polymarket rows (all non-null `clob_token_ids`) + Kalshi CQG parquets (BTC/ETH/sports/etc). BUT:
   **NO Polymarket BTC_UP_DOWN_DAILY for June 27** — the CLOB scan ran at 08:50 UTC but Polymarket had not yet listed
   June 27 BTC hourly markets (confirmed: 0 BTC rows in MISC_NOVELTY; comparison: June 25/26 BTC parquets were created
   at 13:05/13:14 UTC on June 26 — i.e. ~13:00 UTC is when they appear). Re-run IS for June 27 at ~13:00 UTC when
   Polymarket lists BTC hourly markets; restart MTDS Polymarket after.

2. ✅ features-service **arb-detector pipeline stall alert** SHIPPED — `features-service@0bdb4d4c`:
   `post_pipeline_stall_alert()` fires to `#paper-trading-alerts` after 3 consecutive zero-pair ticks (~30 min); 1h
   cooldown. QG-green.

3. ✅ Arb detector VM replaced with new code: deleted `prediction-arb-detector-20260627-005823` (tick=48, OLD code no
   stall alert); launched `prediction-arb-detector-20260627-091140` with features-service `@0bdb4d4c` (has stall alert).
   GCS log: `vm-logs/prediction-arb-detector-20260627-091140/run.log`.

**Open at 09:15 UTC June 27**:

- **PRIORITY 1**: Re-run IS for 2026-06-27 at ~13:00 UTC when Polymarket lists BTC hourly markets. Then restart
  `prediction-live-polymarket-book-snapshot-5-*` VM so MTDS subscribes to BTC token IDs.
- **PRIORITY 2**: Monitor 43d rewalk VMs (`polyrewalk-075135` + `kalshirewalk-075154`) — flip 43d checkbox when both
  complete.
- Arb detector `prediction-arb-detector-20260627-091140` running, stall alert will fire after 3 zero-pair ticks if
  pipeline stall persists. Currently 0 pairs (expected — MTDS not subscribed to June 27 BTC markets).
- Polymarket live book-snapshot `20260626-224659` + Kalshi `20260626-224718` both RUNNING and capturing.

### 2026-06-27 (~10:10 UTC) — Daily IS Cloud Scheduler automated (ALL AGs, 13:30 UTC)

**User request**: "this whole workflow should be cloud scheduled daily — grab instruments from last day up until most
recent possible, then run catalogue aggregation."

**Root gap confirmed**: IS adapter enumeration (CLOB/Gamma API scrape → CQG-partitioned parquets) had **no daily
automation** — only the downstream `enumerate_expected_universe` + catalogue regen were scheduled. The IS parquets
themselves required manual VM backfill triggers.

**Shipped this context**:

1. ✅ `instruments-service/scripts/daily_is_enumeration.py` — new Cloud Scheduler entrypoint:
   - `python -m instruments_service --operation instruments --mode batch --asset-group <ag> --start-date <today-2> --end-date <today> --force`
   - Calculates rolling date window at runtime (no hardcoded dates)
   - Per-AG isolation: one AG failure does not block others
   - **instruments-service@c15a748**

2. ✅ `deployment-service/terraform/gcp/daily_is_enumeration_scheduler.tf` — Terraform for Cloud Scheduler:
   - 5 Cloud Run Jobs (one per AG, parallel execution) + 5 Cloud Scheduler triggers
   - Schedule: **13:30 UTC daily** — after Polymarket lists BTC daily markets ~13:00 UTC
   - Rolling 3-day window with `--force` (overwrites partial morning parquets)
   - Execution SA changed to reuse `unified-trading-sa` (has existing bucket write + secret access); scheduler auth SA
     `is-daily-enum@...` kept narrow (only `run.invoker`). Avoids needing `storage.admin` / project IAM admin.
   - `MANIFEST_PER_VM_SHARDS=true` + stable `VM_NAME=is-daily-enum-<ag>` shard
   - **deployment-service@db40d62**

3. ✅ `deployment_service/cloud_run_job_registry.py` — added `_IS_DAILY_ENUM_JOBS` (5 per-AG entries for guard test) —
   **deployment-service@db40d62**

4. ✅ **Terraform applied (11:28 UTC June 27)** — all 5 Cloud Run Jobs
   (`is-daily-enum-{cefi,defi,tradfi,sports,prediction}`)
   - 5 Cloud Schedulers (`30 13 * * *` UTC ENABLED) live in GCP. Failed IAM resources (`storage_bucket_iam_member`,
     `project_iam_member`) circumvented by reusing `unified-trading-sa` as execution SA (already has all required
     access). **First automated run: 13:30 UTC TODAY (June 27)** — no manual IS backfill needed for today.

5. ✅ **43d rewalk DONE (2026-06-27)** — both `mtds-prediction-polyrewalk-20260627-075135` (POLYMARKET) and
   `mtds-prediction-kalshirewalk-20260627-075154` (KALSHI) completed (VMs auto-deleted). Out-of-life `empty_confirmed`
   rows correctly dropped → blank/`expected_unattempted` in consolidated index.

**Open at 11:30 UTC June 27**:

- **AUTOMATED TODAY 13:30 UTC**: IS PREDICTION Cloud Scheduler will fire `is-daily-enum-prediction` job at 13:30 UTC to
  fetch Polymarket BTC daily markets (listed ~13:00 UTC). No manual backfill needed.
- **AFTER 13:30 UTC**: Restart `prediction-live-polymarket-book-snapshot-5-20260626-224659` to subscribe to today's BTC
  token IDs. Without restart, MTDS still has June 26's token IDs and won't see today's BTC markets.
- **MONITOR**: Arb detector `prediction-arb-detector-20260627-091140` (RUNNING since 09:11 UTC) — stall alert has been
  firing to `#paper-trading-alerts` since ~09:41 UTC (STALL_ALERT_TICKS=3, ~10-min ticks). Non-zero `two_way_on_both`
  pairs expected after MTDS restart post-IS-run.
