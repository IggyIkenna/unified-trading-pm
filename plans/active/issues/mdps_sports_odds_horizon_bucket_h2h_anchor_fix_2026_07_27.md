---
doc_type: issue
title:
  sports odds_horizon_bucket's pivot treats h2h as a mandatory anchor — real 3-layer trace, ALL 3 layers fixed +
  verified against real production data
summary: >-
  Deep-traced `mdps_t1_recon_job_oom_failing_7_days_2026_07_26.md`'s open "Path A½ silently suppresses ALL
  non-MATCH_ODDS candle output" todo (that doc is at its 999/1000-line hard cap, zero headroom — this doc carries the
  full investigation + fix instead of editing it in place). The bug was actually THREE independent h2h-anchoring points,
  not the one the source doc named: (1) `process_to_candles`'s Path A½ short-circuit (the one already named), (2)
  `pivot_mtds_to_wide`'s own hardcoded `if h2h_wide.empty: return pd.DataFrame()` — a SEPARATE, deeper anchor that would
  have defeated a Path A½ fix on its own, and (3) `CandleOutput`'s open/high/low/close fields being hardcoded to
  home/away/draw_odds (the h2h-only repurposing of a generic OHLCV container) — which had no defined mapping for
  spreads/totals/btts values at all. Layer 2 fixed first session (4 regression tests). Layers 1+3 fixed together in a
  follow-up session per operator ruling BLK-4f4309e2 (Option B: market-aware OHLCV branching, no new UAC fields) —
  implemented as a coalesce-broadcast (open=high=low=close = the one real price available per call, since production is
  provably single-market-AND-single-outcome per call) rather than a fixed per-market slot table, which ALSO fixed a
  newly-discovered 4th sub-bug: h2h's own AWAY/DRAW-selection candles had `close=NaN` always, pre-existing and
  independent of this generalization. Verified end-to-end against real production data: a live `t1-recon` re-trigger
  reached `Completed=True` with `odds_horizon_bucket` 100%/0-errors on both dates (first time ever), and real
  `ASIAN_HANDICAP_*`/`OVER_UNDER_*` `odds_horizon_bucket` output now exists in GCS for the first time, with bounded
  plausible O=H=L=C prices. Residual, deliberately-not-fixed gap: `h2h_lay` (MATCH_ODDS_LAY) has no pivot logic in
  `pivot_mtds_to_wide` at all — flagged, not fixed, correctly still returns `empty_confirmed` rather than a false
  positive or a false failure.
status: resolved
nature: issue
asset_group: [sports]
stage: [meta]
repos: [market-data-processing-service]
scope: [engineer, admin]
tags: [sports, odds, mdps, honest-absence, data-correctness, pivot, schema-design]
related:
  [
    /plans/active/issues/mdps_t1_recon_job_oom_failing_7_days_2026_07_26.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
  ]
created: 2026-07-27
priority: P1
parent_epic: mtds_mdps_master
source: "slot-11, infra, dispatched off mdps_t1_recon_job_oom_failing_7_days_2026_07_26.md's Path A½ todo, 2026-07-27"
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by:
  "market-data-processing-service@d6f99b8 (main@9cc084e), verified via
  uts-prod-market-data-processing-service-t1-recon-jsghk, 2026-07-27"
---

# sports odds_horizon_bucket — real 3-layer h2h-anchoring bug, ALL 3 layers fixed + verified against real production data

## What I found

Traced the full call chain from GCS to output, not just the one function the source doc named:

1. **`_iter_chain_symbol_dfs`** (`live_workers_streaming.py`) and every `process_to_candles` call site in
   `live_workers_chain.py` (`_process_chain_bundle_streaming`, `_process_chain_by_symbol`,
   `_process_standard_timeframe`) all pre-slice `tick_data` to ONE `instrument_id` before calling the adapter —
   confirmed via code read (all 4-5 call sites group/filter by instrument before the call) and via the existing test
   `test_real_combined_shape_af_fixture_id_nan_end_to_end`'s own docstring ("the shape `_iter_chain_symbol_dfs` actually
   hands `process_to_candles` in production (grouped by `instrument_id`, so a single market/outcome per call)"). So a
   non-h2h instrument slice containing real rows is the NORMAL production shape, not an edge case.
2. **Layer 1 — `process_to_candles`'s Path
   A½`** (`bucket_assignment_adapter.py`~line 718): checks`(tick_data["market_key"] == "h2h").sum() ==
   0`and short-circuits to`empty_confirmed` — unconditionally true for any non-h2h instrument regardless of whether ITS
   OWN market data is genuinely present. This is the mechanism the source doc named.
3. **Layer 2 — `pivot_mtds_to_wide`'s own anchor** (same file, ~line 502, pre-fix): even if Layer 1 didn't exist,
   `h2h_wide = _pivot_market(df, "h2h", ...)` then `if h2h_wide.empty: return pd.DataFrame()` — UNCONDITIONALLY, before
   even attempting to compute spreads/totals/btts wide data. A spreads-only slice never had h2h rows to begin with, so
   this ALSO forces empty regardless of real spreads/totals/btts data being present. This is a genuinely separate bug
   from Layer 1 — fixing only Layer 1 would still hit this and produce empty output.
4. **Layer 3 — `CandleOutput`'s OHLCV repurposing** (same file, `process_to_candles`'s return statement): `open`/`high`/
   `low`/`close` are hardcoded to `home_by_bucket`/`away_by_bucket`/`draw_by_bucket`/`home_by_bucket` — a 3-value
   H2H-SPECIFIC repurposing of the generic 4-slot OHLCV container ("repurpose: away_odds in high slot" per the existing
   comment). There is no defined mapping for `asian_handicap_home_odds`/`asian_handicap_away_odds` (2 values + a line),
   `over_odds`/`under_odds` (2 values + a line), or `btts_yes_odds`/`btts_no_odds` (2 values) into these 4 slots.

## Why it matters

Confirmed via real production output (source doc's own Update 9 investigation, cross-checked against
`processed_candles/.../data_type=odds_horizon_bucket/`): this product has **never produced real candle output for any
market other than plain h2h, for its entire history** — despite `pivot_mtds_to_wide()`/`_pivot_market()` explicitly
implementing spreads/totals/btts pivoting and the UAC SchemaContract deliberately supporting all these
`instrument_type`s uniformly. Layer 2 is the deepest, most consequential gap: it silently drops real, already-fetched
spreads/totals/btts data at the DataFrame level, before any output-schema question even arises — this affects
`process_to_bucketed_df` too (the "primary output method for features-service consumption" per its own docstring),
independent of whatever CandleOutput/manifest question Layer 3 resolves to.

## What was fixed this session (Layer 2 only)

`market-data-processing-service` — `pivot_mtds_to_wide()`: removed the `if h2h_wide.empty: return pd.DataFrame()`
mandatory-anchor check. Now picks whichever of h2h/spreads/totals/btts wide-pivots is non-empty as the merge base grain,
defaulting the other 3 markets' columns to NaN (mirroring the existing spreads/totals/btts-absent-from-h2h-bundle
default pattern, just no longer privileging h2h as the one exempt case). Only genuinely empty (none of the 4 markets
present at all) still returns `pd.DataFrame()`.

4 new/updated tests in `tests/unit/test_bucket_assignment_adapter.py`:

- `test_pivot_spreads_only_no_h2h_returns_real_data` / `test_pivot_totals_only_no_h2h_returns_real_data` (new) — prove a
  spreads/totals-only slice now returns its own real data, with h2h columns present-but-NaN.
- `test_pivot_no_recognized_market_still_empty` (new) — proves genuine absence (no h2h/spreads/totals/btts at all) still
  correctly returns empty — only the false-negative case was the bug.
- `test_no_h2h_returns_empty_not_malformed` / `test_no_h2h_multiple_bookmakers` (updated) — these pre-existing
  `process_to_bucketed_df` tests asserted `result.empty` for spreads-only bookmakers; that assertion WAS the Layer-2
  bug's own test coverage (locking in the bug as "expected"). Updated to assert the corrected behavior: real spreads
  data returned, still no `MalformedTickFieldError`.

**NOT touched**: `process_to_candles`'s Path A½ (Layer 1) stays exactly as-is — see "What's genuinely left" below for
why generalizing it now would be a regression, not a fix.

## What's genuinely left — Layer 1 and Layer 3, a real design decision

Layer 1 (Path A½) and Layer 3 (CandleOutput OHLCV mapping) are coupled: Layer 1 can only be safely generalized once
Layer 3 has a real answer, because generalizing Path A½ in isolation would make `process_to_candles` fall through into
the now-fixed pivot, get real spreads/totals/btts rows, but then populate `open`/`high`/`low`/`close` from
`home_odds`/`away_odds`/`draw_odds` — which are NaN for a non-h2h instrument — silently turning today's honest
`empty_confirmed` into a fake-non-empty, all-NaN-priced "captured" candle. That is a worse failure mode (harder for a
downstream consumer to detect than an honest absence label), so it was not attempted.

The next implementer needs to decide, before touching Path A½ (mirroring this doc-family's own KALSHI-adapter precedent,
`mdps_t1_recon_job_oom_failing_7_days_2026_07_26.md`'s open KALSHI todo, for the same "needs real judgment, not a guess"
reason):

1. **Does `CandleOutput` get new market-specific fields** (e.g. `asian_handicap_home_odds`/`over_odds`/`btts_yes_odds`
   as first-class output columns, alongside or instead of the generic OHLCV names), requiring a UAC SchemaContract
   change for `odds_horizon_bucket`? Or **does the OHLCV mapping branch by the instrument's own market type** (an
   ASIAN_HANDICAP instrument writes its home/away odds into open/close, a BTTS instrument writes yes/no into open/high,
   etc.) — keeping the existing generic schema but making the 4-slot repurposing market-aware?
2. Once (1) is decided, Path A½ can be generalized to "no recognized market present" (the fix drafted and then reverted
   in this session is a ready-made diff for that half) and the new candle-value-mapping logic added alongside it.
3. Re-run this doc's own new pivot tests plus a fresh end-to-end production repro (mirroring
   `test_real_combined_shape_af_fixture_id_nan_end_to_end`'s pattern) against a real non-h2h instrument slice to confirm
   real, non-NaN prices reach the output.

## Decision (operator, 2026-07-27, BLK-4f4309e2)

**Option B — branch the OHLCV mapping by instrument market type; NO new UAC fields.** `CandleOutput`'s generic
open/high/low/close schema stays unchanged; the sports bucket-assignment adapter maps each instrument's own market type
onto the 4 existing slots (mirroring the already-accepted h2h repurposing: `open=home_odds`, `high=away_odds`,
`low=draw_odds`, `close=home_odds`).

Reasoning (operator, verbatim rationale): (1) **UAC minimalism** — `CandleOutput` is a shared cross-asset contract
(CEFI/DEFI/TRADFI/OPTIONS/QUANT/SPORTS); adding sports-specific named fields (`over_odds`/`btts_yes_odds`/
`asian_handicap_*`) pushes asset-specific bloat onto every consumer, the exact canonical-bloat direction UAC
consolidation fights. (2) **Intra-sports consistency** — h2h already repurposes OHLCV slots; adding named fields for the
other 3 market types would leave two different representations for sports odds inside the same `odds_horizon_bucket`
output (h2h repurposed vs. spreads/totals/btts named), which is incoherent. Branching keeps all sports odds markets on
one mechanism. (3) **Blast radius + reversibility** — branching touches no cross-cutting SSOT and is reversible (named
fields can still be added later if this proves painful); adding fields commits a shared contract that is hard to walk
back.

**Required mitigation (non-negotiable per the ruling)**: the market-type → OHLCV-slot mapping MUST be explicit and
documented (a mapping table/comment on the branch, matching the existing h2h repurposing convention) — never a silent
overload, so a downstream reader of e.g. a BTTS instrument is not misled into thinking `open`/`high` are literal
first/highest trade prices.

**Re-block trigger for the next implementer**: if any market type turns out to need >2 meaningful odds legs that do not
fit the 4 OHLCV slots (e.g. a 3-way spread or a multi-line totals market), STOP and re-open a `/blocked` — that specific
market would justify revisiting Option A (named fields) for that market only, not a wholesale reversal.

Known market shapes to map (from `_pivot_market`'s existing spreads/totals/btts pivoting, now correctly reaching this
adapter per the Layer-2 fix above):

- `asian_handicap` (spreads): 2 legs (`asian_handicap_home_odds`, `asian_handicap_away_odds`) → fits 2 of 4 slots.
- `totals`: 2 legs (`over_odds`, `under_odds`) → fits 2 of 4 slots.
- `btts`: 2 legs (`btts_yes_odds`, `btts_no_odds`) → fits 2 of 4 slots.

All three are ≤2 legs, so none currently trip the re-block trigger.

## Recommended decision

- [x] [DESIGN] P1. Decide the `CandleOutput` schema question above (new market-specific fields vs. market-aware OHLCV
      branching) for sports `odds_horizon_bucket`'s spreads/totals/btts output — a genuine product/schema decision, not
      a worker-determinable fact. ✅ — DECIDED: Option B (market-aware OHLCV branching, no UAC schema change), operator
      ruling via BLK-4f4309e2, 2026-07-27. See "Decision" section above for full rationale + required mitigation +
      re-block trigger. No code shipped for this todo — it is pure decision-of-record (task `repos: []`); todo 2 below
      implements it.
- [x] [SCRIPT] P2. Now unblocked: generalize `process_to_candles`'s Path A½ check + implement the Option-B candle-value
      mapping. **DONE, verified end-to-end against real production data** — `market-data-processing-service@d6f99b8`
      (`main@9cc084e`). See Update 2 for full evidence: real WILLIAMHILL/production-shaped regression tests, and a live
      `t1-recon` re-trigger (`uts-prod-market-data-processing-service-t1-recon-jsghk`, sports-scoped, `--force`,
      2026-07-25..26) that reached `Completed=True` in 16m23.8s with `odds_horizon_bucket: 505/505` and `837/837`
      succeeded (0 errors, both dates) — the first time this data_type has EVER hit 100% in this doc-family's history.
      Real GCS output confirmed: `instrument_type=MATCH_ODDS` (already-working) PLUS 14-18 distinct `ASIAN_HANDICAP_*`
      variants and 9 `OVER_UNDER_*` variants now exist for the first time ever on both dates (461+ non-MATCH_ODDS
      objects on day 1 alone; zero existed pre-fix), with real bounded O=H=L=C prices (e.g. `ASIAN_HANDICAP_0_5::HOME`
      close=2.1; `OVER_UNDER_2_5::OVER` close=2.27/2.35; `::UNDER` close=1.68/1.65). (repo:
      market-data-processing-service)

## Update 2 (2026-07-27, attended session) — Path A½ generalized + a THIRD, previously-unknown sub-bug found and fixed in the same change: h2h's own AWAY/DRAW-selection candles had `close=NaN` always

Picked up todo 2 above. Per the operator's explicit standard for this doc-family ("investigate for real, don't guess"),
traced both open safety questions from scratch before implementing, then found and fixed one more thing along the way.

### (a) Could `btts` ever legitimately co-occur with another `market_key` in the same slice?

**No — proven at the code level, not just observed.** `build_instrument_id()`
(`unified_api_contracts/canonical/domain/sports/canonical_ids.py`) embeds the market type as a segment derived 1:1 from
`ODDS_API_MARKET_TO_CANONICAL` (`h2h`→`MATCH_ODDS`, `h2h_lay`→`MATCH_ODDS_LAY`, `spreads`→`ASIAN_HANDICAP`,
`totals`→`OVER_UNDER`, `btts`→`BOTH_TEAMS_TO_SCORE`, ... — 11 raw keys, 11 distinct canonical values, confirmed
injective) — two different `market_key` raw values can never collide into the same `instrument_id` MARKET segment.
Stronger than what was asked: `build_instrument_id` ALSO embeds the **selection/outcome**
(`{SPORT}:{VENUE}:{MARKET}: {LEAGUE}:{SEASON}:{HOME}-{AWAY}::{SELECTION}`), so a slice grouped by one `instrument_id`
value (`_iter_chain_symbol_dfs`, confirmed the sole production dispatch path for sports — see (b)) is not just
single-market but single-OUTCOME (e.g. `MATCH_ODDS::HOME`, `MATCH_ODDS::AWAY`, `MATCH_ODDS::DRAW` are 3 separate
instrument_ids, never merged in one raw-file group). This closed-set, injective mapping is what makes the Path A½
generalization and the OHLCV coalesce below both safe.

### (b) Is there a call path where `tick_data` reaches `process_to_candles` genuinely NOT yet market-filtered?

**No, for `process_to_candles` specifically — confirmed by reading every call site, not just the ones already traced.**
All 4 real call sites (`live_workers_streaming.py::_process_chain_bundle_streaming` →
`_streaming_process_slice_timeframes`; `live_workers_chain.py::_process_chain_timeframe` [groups by `instrument_key`],
`_process_chain_timeframe_by_symbol` [groups by `symbol`], `_process_standard_timeframe` [file itself is
single-instrument]) slice/filter to ONE instrument before calling `process_to_candles`. For sports specifically:
`_is_chain_data()` (`live_workers_chain.py`) always returns `True` for any `.../ticks.parquet` path when the file has no
`symbol` column (true for every sports odds raw file, confirmed via `market_tick_data_service`'s `odds_api_adapter.py`
row schema), so sports odds ALWAYS routes through the streaming path, which groups by `instrument_id` (the only
chain-group candidate sports files carry) — never falls through to a path that could hand `process_to_candles` an
unsliced bundle.

**`process_to_bucketed_df` is the genuine multi-market-bundle path — but it doesn't have Path A½ at all.**
`scripts/reprocess_sports_odds.py::reprocess_date()` reads a WHOLE DAY's raw odds (`_read_raw_odds`, no per-instrument
slicing) and calls `adapter.process_to_bucketed_df(raw_df)` directly — a real, genuinely-unsliced multi-market,
multi-fixture, multi-selection bundle. Confirmed this method has **no Path A½ short-circuit anywhere** (it goes straight
to `_prepare_tick_data`/`pivot_mtds_to_wide`, unaffected by anything in this fix) and doesn't do OHLCV assembly either
(returns the wide dataframe with `home_odds`/`away_odds`/... columns intact, no repurposing) — so neither part of
today's fix touches its behavior. This is the "genuinely NOT yet market-filtered" path the original todo asked about; it
exists, but for a different method than the one being generalized.

### A third sub-bug found while implementing: h2h's OWN AWAY/DRAW-selection candles were already broken the same way

Given (a)/(b) confirm every `process_to_candles` call is single-market AND single-outcome, the OLD hardcoded OHLCV
mapping (`open=close=home_odds`, `high=away_odds`, `low=draw_odds`) could only ever populate 1-2 of its 4 slots per call
— home/away/draw are never simultaneously present in one real call, so the "combine 3 selections into one row" premise
`pivot_mtds_to_wide`'s docstring describes was never actually exercised in production. **Verified directly against real
written output** (day=2026-07-25,
`processed_candles/.../data_type=odds_horizon_bucket/ instrument_type=MATCH_ODDS/venue=BETFAIR_EX_EU/...KALMAR-MJALLBY::{HOME,AWAY,DRAW}.parquet`,
pulled + inspected with pandas): HOME-selection rows had real `open`/`close` but `high`/`low` NaN; **AWAY-selection rows
had real `high` (away odds correctly placed there) but `open`/`low`/`close` NaN**; **DRAW-selection rows had real `low`
(draw odds) but `open`/`high`/`close` NaN**. `close` — the field a downstream reader looks at first — was silently NaN
for 2 of every 3 MATCH_ODDS candles in production, for the product's entire history, independent of and prior to the
generalization being implemented here.

### Fix implemented (`market-data-processing-service@d6f99b8`, `bucket_assignment_adapter.py`)

1. **Path A½ generalized**: `_RECOGNIZED_MARKET_KEYS = frozenset({"h2h", "spreads", "totals", "btts"})` — exactly the 4
   markets `pivot_mtds_to_wide()`'s `_pivot_market()` calls actually implement. Deliberately excludes `"h2h_lay"`:
   grepped `pivot_mtds_to_wide()` and confirmed there is no `_pivot_market(df, "h2h_lay", ...)` call at all —
   MATCH_ODDS_LAY has a real UAC SchemaContract but no pivot logic here, a genuinely separate, not-yet-investigated gap
   (flagged, not fixed — an h2h_lay-only slice still correctly short-circuits to empty_confirmed, never a false
   MalformedTickFieldError).
2. **Option-B OHLCV mapping, implemented as a coalesce-broadcast** (not a fixed per-market slot table, once (a)/(b)
   proved at-most-one-column-populated is a hard invariant, not a heuristic): `_PRICE_COLS_BY_PRIORITY` coalesces
   `home_odds → away_odds → draw_odds → asian_handicap_home/away_odds → over/under_odds → btts_yes/no_odds` (priority
   order preserves the pre-existing "home is primary" convention for the defensive/synthetic multi-outcome case) into
   ONE real price per bucket, broadcast to all 4 slots (`open=high=low=close`). This is explicit/documented (module +
   method docstrings updated) per the ruling's required mitigation, fixes the newly-found h2h AWAY/DRAW `close=NaN` bug
   as a side effect, and never trips the ">2 legs" re-block trigger (coalescing doesn't care how many conceptual legs a
   market has, only that at most one is ever populated per call).
3. Module + method docstrings updated to document the O=H=L=C convention explicitly.

**Tests** (`tests/unit/test_bucket_assignment_adapter.py`, 3 new classes, all using real market_key shapes):
`TestGeneralizedPathAHalfRecognizedMarkets` — a byte-accurate real WILLIAMHILL `market_key="totals"` 12-row slice
(pulled directly from the exact GCS object Update 9 cited, `fixture_id=1494218`, sliced to the real `::OVER`
instrument_id) that pre-fix force-emptied and post-fix produces real bounded candles; btts-only and spreads-only
single-outcome slices; an `h2h_lay`-only slice confirming it correctly STAYS empty_confirmed (documents the known gap,
doesn't silently regress it); a genuinely-unrecognized-market-key slice confirming true absence still empty_confirmed.
`TestH2hSingleSelectionOhlcNoLongerNan` — HOME/AWAY/DRAW single-selection slices proving `close` is no longer
permanently NaN for AWAY/DRAW. Full suite: 2315 passed, 87.12% coverage. `quality-gates.sh --no-fix` → ALL QUALITY GATES
PASSED. Shipped via `quickmerge.sh --agent`.

### Production verification — real, watched-to-terminal-state, both absence-of-errors AND positive-output proof

LDR→main promotion (PR #515) merged, fresh Cloud Build (`a7edb06f`, confirmed building `main@9cc084e`) published digest
`sha256:e65835ea...`; confirmed the triggered execution's container actually resolved to this exact digest before
trusting the result. Triggered `uts-prod-market-data-processing-service-t1-recon-jsghk`
(`MDPS_ASSET_GROUP=SPORTS --start-date 2026-07-25 --end-date 2026-07-26 --force`), polled
`status.conditions[type=Completed]` directly via the JSON condition object (not a naive string match — checked for
`status ∈ {"True","False"}` specifically, not merely non-empty, after an initial polling-script bug treated the
in-flight `status="Unknown"` condition as a false-positive terminal state and was caught before being reported). Reached
a genuine terminal state: **`Completed=True`, "Execution completed successfully in 16m23.8s."**

**Absence-of-errors**: `🏁 sports processing complete: 2020/2020 succeeded, 0 errors` (day 1) and
`3348/3348 succeeded, 0 errors` (day 2), `SUB-DIMENSION STATUS: All (data_type x instrument_type) combinations passed`
for both. `odds_horizon_bucket` specifically: `505/505 succeeded` (39,000 candles) and `837/837 succeeded` (58,845
candles) — **100%, zero errors, the first time this data_type has ever reached full success in this doc-family's
history** (every prior run — Updates 4/5/7/8/9/10 of the parent OOM doc — hit SOME failure class here).

**Positive output, pulled directly from GCS and inspected (not inferred from log absence)**: before this run,
`processed_candles/.../data_type=odds_horizon_bucket/` for both dates contained ONLY `instrument_type=MATCH_ODDS/`
(confirmed via a pre-run baseline listing). After: `MATCH_ODDS` PLUS 14 (day 1) / 18 (day 2) distinct `ASIAN_HANDICAP_*`
point-parameterised variants PLUS 9 `OVER_UNDER_*` variants on EACH date — real non-MATCH_ODDS `odds_horizon_bucket`
output for the first time ever (461+ objects on day 1 alone by partial count, timed out counting day 2 exhaustively but
the per-instrument_type listing above already proves the shape). Downloaded 2 real files and inspected with pandas:

- `FOOTBALL:BETONLINEAG:ASIAN_HANDICAP_0_5:ALLSVENSKAN:2026-27:DEGERFORS-DJURGARDEN::HOME` — bucket 0:
  `open=high=low=close=2.10` (real, bounded, O=H=L=C broadcast confirmed working exactly as designed); other 7 buckets
  correctly NaN (no bookmaker quote in that horizon window — genuine sparse coverage, not a bug).
- `FOOTBALL:BETONLINEAG:OVER_UNDER_2_5:ARGENTINA_PRIMERA:2026-27:RIVER_PLATE-BARRACAS_CENTRAL::OVER` — 2 populated
  buckets, `close=2.27`/`2.35`; the sibling `::UNDER` instrument — `close=1.68`/`1.65` — both real, plausible decimal
  soccer odds, O=H=L=C matching in every populated bucket.

`MATCH_ODDS_LAY` correctly absent (as expected — `h2h_lay` is deliberately not in `_RECOGNIZED_MARKET_KEYS`, the
documented, not-yet-fixed gap). No `BOTH_TEAMS_TO_SCORE` objects observed on these 2 particular dates — consistent with
btts being a genuinely sparser market (not every bookmaker/fixture offers it; not investigated further as a possible
issue since the mechanism (Path A½ + coalesce) is proven correct on the 2 markets that DID have real data this run, and
`TestGeneralizedPathAHalfRecognizedMarkets::test_btts_only_slice_produces_real_output` already proves the code path in
isolation).

This is the direct, real-production evidence the task mandate asked for on both counts: absence of errors AND positive,
bounded, plausible output for the newly-unblocked markets.

## Codex SSOTs

- `/codex/02-data/honest-absence-downstream-handling.md` — the empty_confirmed vs. malformed-field distinction this
  bug's Layer 1/2 both implement correctly (Layer 2 now fixed; Layer 1 deliberately unchanged pending Layer 3).
