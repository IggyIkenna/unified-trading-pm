---
doc_type: issue
title:
  sports odds_horizon_bucket's pivot treats h2h as a mandatory anchor — real 3-layer trace, 1 of 3 layers fixed, 1 layer
  deliberately deferred as a genuine schema-design decision
summary: >-
  Deep-traced `mdps_t1_recon_job_oom_failing_7_days_2026_07_26.md`'s open "Path A½ silently suppresses ALL
  non-MATCH_ODDS candle output" todo (that doc is at its 999/1000-line hard cap, zero headroom — this doc carries the
  full investigation + fix instead of editing it in place). The bug is actually THREE independent h2h-anchoring points,
  not the one the source doc named: (1) `process_to_candles`'s Path A½ short-circuit (the one already named), (2)
  `pivot_mtds_to_wide`'s own hardcoded `if h2h_wide.empty: return pd.DataFrame()` — a SEPARATE, deeper anchor that would
  have defeated a Path A½ fix on its own, and (3) `CandleOutput`'s open/high/low/close fields being hardcoded to
  home/away/draw_odds (the h2h-only repurposing of a generic OHLCV container) — which has no defined mapping for
  spreads/totals/btts values at all. Fixed (2) — a clean, judgment-free correctness fix with 4 new/updated regression
  tests. Deliberately did NOT touch (1) or attempt (3): generalizing (1) alone, now that (2) is fixed, would make
  `process_to_candles` silently emit non-empty-looking CandleOutputs with ALL-NaN prices for non-h2h instruments — WORSE
  than today's honest `empty_confirmed`, because (3) has no real value to put in those 4 slots yet. (3) is a genuine
  schema-design decision (extend CandleOutput with market-specific fields vs. branch the OHLCV mapping by instrument
  type), not something to guess at, mirroring this same doc-family's own KALSHI-adapter precedent.
status: open
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
---

# sports odds_horizon_bucket — real 3-layer h2h-anchoring bug, layer 2 of 3 fixed

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
- [ ] [SCRIPT] P2. Now unblocked: generalize `process_to_candles`'s Path A½ check (the same
      `_RECOGNIZED_MARKET_KEYS`-style generalization drafted and reverted this session) + implement the Option-B
      candle-value mapping (explicit market-type → slot table per the required mitigation above), with a live production
      repro proving real non-NaN prices for a spreads/totals/btts instrument. STOP + re-block if any market needs >2
      meaningful odds legs. (repo: market-data-processing-service)

## Codex SSOTs

- `/codex/02-data/honest-absence-downstream-handling.md` — the empty_confirmed vs. malformed-field distinction this
  bug's Layer 1/2 both implement correctly (Layer 2 now fixed; Layer 1 deliberately unchanged pending Layer 3).
