---
doc_type: issue
title:
  tradfi ohlcv_1h was added to SOURCE_PRIORITY without an availability semantic — FIXED as tick_timestamp; only a P3
  latency re-check remains
summary: >-
  A half-finished change added ("tradfi","ohlcv_1h"):["yahoo"] to SOURCE_PRIORITY without the matching
  AVAILABILITY_AT_SEMANTICS entry, failing 6 UAC tests tree-wide and blocking every unrelated UAC ship. FIXED 2026-08-13
  as tick_timestamp (unified-api-contracts@8f0903bb85), matching every other tradfi MARKET BAR; the same change added
  the missing per-instrument_type validity-matrix entry, which the parked work had put in the wrong structure. This
  doc's FIRST framing was wrong and is kept visible as a correction rather than edited away: it called the choice an
  operator decision and recommended fetch_completed_at as "conservative", when fetch_completed_at stamps available_at at
  BACKFILL wall-clock — on a 5-year-old candle that erases the series from every point-in-time backtest. The two tradfi
  fetch_completed_at pairs are FRED macro series, not bars, so they were never a precedent. Yahoo's 15-min delay is
  already modelled by emission_latency_ms_for_source. Remaining: P3 re-check that the 900_000ms latency, documented
  against ^VIX-style indices, also holds for 1h equity bars.
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [unified-api-contracts, market-tick-data-service]
scope: [engineer]
tags: [data-correctness, availability-semantics, source-priority, point-in-time, blocked-operator-decision]
related:
  [
    /plans/active/issues/tradfi_databento_account_billing_suspended_2026_08_09.md,
    /codex/02-data/honest-absence-downstream-handling.md,
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
    /plans/archive/2026_08/alert_driven_dependency_revocation_2026_08_12.md,
  ]
created: 2026-08-13
last_updated: "2026-08-20"
parent_epic: uac_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: design
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.2
assigned_role: data_engineering
effort: max
drift_direction: advance-code
sequential: true
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Found 2026-08-13 inheriting ~5h-idle WIP in slot 4 while shipping UAC Phases 2-3. The Yahoo half was the sole cause of
  all 6 gate failures; the revocation half was clean and shipped separately.
depends_on: []
context_scope:
  [
    market-tick-data-service/scripts/measure_yahoo_1h_equity_emission_latency_2026_08_14.py,
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
    unified-api-contracts/unified_api_contracts/canonical/crosscutting/availability_semantics.py,
    /plans/active/issues/tradfi_databento_account_billing_suspended_2026_08_09.md,
  ]
---

# tradfi ohlcv_1h availability semantic — FIXED (was: missing)

## Nothing is parked any more — all of it shipped

**Everything described below is HISTORY.** An earlier revision of this doc said two files were "parked" in a named git
stash in slot 4 with a copy in that session's scratchpad. Both of those locations are session/slot-local and are gone
now; **do not go looking for them**. The work was unstashed, completed and landed in `unified-api-contracts@8f0903bb85`,
so the content lives in git history where anyone can reach it:

| file                                               | change                                                 | state                |
| -------------------------------------------------- | ------------------------------------------------------ | -------------------- |
| `canonical/crosscutting/_source_priority_data.py`  | adds `("tradfi","ohlcv_1h"): ["yahoo"]`                | ✅ shipped           |
| `registry/market_data_categories.py`               | adds `"ohlcv_1h"` to the tradfi equity validity matrix | ✅ shipped           |
| `canonical/crosscutting/availability_semantics.py` | adds `("tradfi","ohlcv_1h"): "tick_timestamp"`         | ✅ shipped (the fix) |

## Why it blocked everything while it sat (resolved)

The pair was registered as a source with no availability semantic, so two symmetry invariants failed and took four more
tests with them:

```
SOURCE_PRIORITY pairs unreachable from the validity matrix: [('tradfi', 'ohlcv_1h')]
Era-B purge would break SOURCE_PRIORITY <-> AVAILABILITY_AT_SEMANTICS symmetry.
  SOURCE_PRIORITY-only: [('tradfi', 'ohlcv_1h')]; AVAILABILITY-only: []
```

Six failures, one root. Because they were tree-wide, ANY unrelated `unified-api-contracts` ship was blocked while it sat
— which is how it was found. All six are green as of `8f0903bb85`; this is recorded so the next person who sees that
error text recognises the shape, not because it is still happening.

## RESOLVED 2026-08-13 — `tick_timestamp`, shipped as `unified-api-contracts@8f0903bb85`. Never an open decision.

> **CORRECTION.** The original version of this section framed it as an operator decision between two semantics and
> recommended `fetch_completed_at` as "the conservative direction — it can only make a strategy look worse than reality,
> never better." **That was wrong, and following it would have caused real damage.** The correction was prompted by the
> operator asking a simple question — _if a candle is 5 years old, is `fetch_completed_at` at the candle close?_ — which
> the original analysis had never checked. It is not.

**What `fetch_completed_at` actually means.** `available_at` is stamped **per-row at write time**
(`availability_semantics.py` module docstring: "each row's value = when the live pipeline would have actually had that
row's information"). `fetch_completed_at` resolves to when the FETCH completed. For a 5-year-old candle backfilled today
that stamps `available_at` ≈ today, so the bar reads as "not available until 2026" and **disappears from every
point-in-time backtest before today**. That is not conservative — it silently deletes history.

**The siblings do not disagree; they are different KINDS of data.** Every tradfi MARKET BAR uses `tick_timestamp`:

| pair                                     | semantic             | what it is                                   |
| ---------------------------------------- | -------------------- | -------------------------------------------- |
| `trades`, `tbbo`, `ohlcv_1s`, `ohlcv_1m` | `tick_timestamp`     | real market bars                             |
| `yield_curve`, `ohlcv_1d`                | `fetch_completed_at` | FRED macro series (VIXCLS, CPI, GDP, UNRATE) |

`("tradfi","ohlcv_1d")` is a "degenerate 1-obs/day bar" of published economic series — it genuinely becomes known when
published/fetched. It is not a precedent for a bar series. Yahoo `ohlcv_1h` is a market bar, so it takes
`tick_timestamp` like every other one.

**The delay concern is already handled by that semantic, not by choosing a different one.** `tick_timestamp` is not
"available at the bar's own timestamp" — it stamps **tick-time + `emission_latency_ms_for_source(source)`**, explicitly
so "the historical archive replay matches the live emission latency". Yahoo is already registered:

```python
"yahoo": 900_000,  # 15 min: Yahoo Finance free-tier intraday delay
```

So the lookahead risk the original text worried about is modelled by an existing, already-populated mechanism — and the
"go measure Yahoo's serving delay" todo was asking for a number the registry already carries.

## Todos

- [x] ✅ [CODE] P1. **Semantic decided and applied: `("tradfi","ohlcv_1h"): "tick_timestamp"`** — matching every other
      tradfi market bar, per the correction above. NOT an operator decision: the two `fetch_completed_at` tradfi entries
      are FRED macro series, not bars, so there was no genuine precedent conflict. Yahoo's 15-min free-tier delay is
      carried by `emission_latency_ms_for_source("yahoo") == 900_000`, already registered.
- [x] ✅ [CODE] P1. **Validity-matrix reachability fixed** — the parked work had added `ohlcv_1h` to the flat
      `DATA_TYPES_BY_ASSET_GROUP["tradfi"]` enumeration, but the reachability invariant reads the per-instrument_type
      `VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE`, a different structure — which is why one of the six kept failing
      after the semantic was added. Added to `("tradfi","equity")` only, matching the source's documented NASDAQ/NYSE
      coverage; deliberately NOT widened to future/etf/index, which would over-fan cells the writer never captures.
- [x] ✅ [CODE] P1. Parked files unstashed and all six originally-failing tests verified green together
      (`test_source_priority`, `test_validity_matrix_completeness`, the four `test_era_b_purge` cases) — 32 passed.
- [ ] [DATA] P3. **Re-verify the 15-min Yahoo latency still holds for 1h equity bars specifically.** The registered
      900_000 ms is documented against "CBOE-sourced indices like ^VIX"; it is the right mechanism and a sane default,
      but it was measured for a different instrument class. **Script ready, not yet run**:
      `market-tick-data-service/scripts/measure_yahoo_1h_equity_emission_latency_2026_08_14.py` polls a live ticker
      across a real bar-close boundary and records wall-clock-vs-bar-close latency — this CANNOT be measured
      retrospectively (Yahoo exposes no server-side "first available at" field), only live during NASDAQ/NYSE market
      hours (09:30-16:00 America/New_York). Checked 2026-08-14T00:15Z: market closed (next open ~13:30 UTC same day) —
      run it during the next open window:
      `.venv/bin/python scripts/measure_yahoo_1h_equity_emission_latency_2026_08_14.py --ticker AAPL`. Repo:
      market-tick-data-service.
- [ ] [DOCS] P2. Record in `/codex/02-data/tradfi-databento-sourcing-ssot.md` that Yahoo is an interim `ohlcv_1h` source
      while Databento billing is suspended, with its measured delay — so the next person adding an interim vendor knows
      the availability semantic is part of the change, not a follow-up.

## Progress Log

- 2026-08-13 — **RESOLVED and shipped: `unified-api-contracts@8f0903bb85`.** Semantic = `tick_timestamp`; validity
  matrix entry added to `("tradfi","equity")`; parked files unstashed; all six originally-failing tests green (32
  passed), full UAC gate green. The lesson worth keeping is about how this was nearly got wrong: the original filing
  reasoned from the NAME `fetch_completed_at` and from a two-row table of "sibling" pairs, and produced a confident
  recommendation — "conservative; can only make a strategy look worse, never better" — that was the opposite of true.
  Reading the actual contract (`available_at` is per-row WRITE-TIME) takes one file open and shows immediately that on a
  backfilled bar it stamps today, erasing the series from point-in-time backtests. **A registry value's meaning is in
  its stamping implementation, never in its name or in what its neighbours happen to use.** The catch came from the
  operator asking the one concrete question the analysis had skipped — _if the candle is 5 years old, is
  `fetch_completed_at` at the candle close?_ — which is the shape of question worth asking of any semantic before
  recommending it.
- 2026-08-13 — Filed while inheriting ~5h-idle WIP in slot 4. The Yahoo half was the sole cause of all 6 UAC gate
  failures; the dependency-revocation half in the same dirty tree was independent and clean, so it was separated and
  shipped as `unified-api-contracts@c206f9100d` (Phases 2-3) rather than being held hostage to this decision. Parked
  rather than guessed because a wrong `tick_timestamp` here is invisible: it produces optimistic backtests, not an
  error. The failing test is the only thing standing between that guess and a shared contract.
- 2026-08-14 — **Downstream MTDS-side code shipped: `market-tick-data-service@9341a84344`.** This is separate, ~24h-idle
  WIP found in the same slot 4 (`_umi_yahoo.py`'s `fetch_yahoo_equities_intraday`, `umi_tick_provider.py` routing,
  `tick_data_handler.py`'s `--source` exemption) — it was blocked transitively by this doc's own UAC gate failure while
  unresolved, and became shippable once `unified-api-contracts@8f0903bb85` landed. Two real gaps found while finishing
  it, both fixed same-commit: (1) `test_tradfi_enumeration_is_narrowed_to_the_14_fetchable_cells` had a stale hardcoded
  14-cell expectation that didn't account for the two new `(NASDAQ|NYSE, ohlcv_1h)` cells — renamed to
  `..._16_fetchable_cells` and the set/count/docstring updated; (2) `TickDataHandler._resolve_source()` grew past the
  50-line method cap — extracted `_is_cboe_yahoo_only()` as its own static helper. QG green
  (`ALL QUALITY GATES PASSED`), all four files shipped together.
- **na-eligibility-audit 2026-08-16** (tradfi tranche, dispatch agt-45ad7b): **RECLASSIFY, whole-doc → planning.** Both
  remaining todos are small, bounded, no-judgment-call actions confined to market-tick-data-service + one codex doc: run
  the already-written `measure_yahoo_1h_equity_emission_latency_2026_08_14.py` during market hours, then record the
  measured delay in `/codex/02-data/tradfi-databento-sourcing-ssot.md`. Conflict-checked clean. `assigned_vm: NA →
  planning`, `execution_scope → orchestrator-agent`, `effort: max` added. **Also corrected `assigned_role: data_engineer
  → data_engineering`** — the prior value was a near-miss of no registered role (registry has `data_engineering.md`,
  not `data_engineer.md`) that would have silently mis-routed dispatch.
- **context-scout 2026-08-17**: refreshed context_scope (4 entries) — swapped the already-shipped UAC registry files
  for the remaining-work targets: the ready-to-run latency-measurement script (P3) and the codex doc to update (P2),
  plus the billing-suspension doc explaining why Yahoo is the interim source.
- **context-scout 2026-08-20**: refreshed context_scope (4 entries)
