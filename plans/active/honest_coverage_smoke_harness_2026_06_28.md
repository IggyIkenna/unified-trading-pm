---
doc_type: plan
title: Honest-coverage smoke-test harness — RUNNABLE / INSUFFICIENT-HISTORY / HONEST-EMPTY per AG×venue×data_type
summary:
  "Build a harness that walks the availability manifest to classify every AG×venue×data_type×instrument shard as
  RUNNABLE (continuous window) / INSUFFICIENT-HISTORY (partial → must FAIL) / HONEST-EMPTY (no data → handled), with
  product-shaped required windows, so we can smoke-test MDPS+features over the span each path actually needs."
status: active
nature: process
asset_group: [cross-cutting]
stage: [data, backtest]
repos: [e2e-testing, unified-api-contracts]
scope: [engineer, admin]
tags:
  [
    smoke-test,
    honest-coverage,
    manifest,
    capture-status,
    insufficient-history,
    honest-empty,
    coverage-matrix,
    sports-seasonal,
  ]
related:
  [
    ./mdps_features_reduced_artifact_tracker_2026_06_28.md,
    ./mvp_for_mdps_and_features_universe_uac_2026_06_28.md,
    ../epics/batch_live_symmetry_master.md,
  ]
created: 2026-06-28
parent_epic: batch_live_symmetry_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: brand-new
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 5
assigned_role: data_engineering
model_tier: opus-required
thinking_tier: high
drift_direction: advance-code
last_updated: 2026-06-28
locked_by: NA
locked_since:
supersedes:
superseded_by:
depends_on: [mvp_for_mdps_and_features_universe_uac_2026_06_28]
gate_on_depends: true
source: [operator request 2026-06-28]
---

# Honest-coverage smoke-test harness

The goal you set: find where we have **honest, good coverage** for tick data, candle data, and every data_type×venue
combo across all asset groups, so we can smoke-test that the MDPS+features code path actually works over the time span
it needs — and **fail loudly** where coverage is only partial, rather than silently testing half a window.

**Execution model:** Opus / thinking high for the DESIGN (cross-AG synthesis over the manifest semantics +
product-shaped windows). Sonnet for the implementation once the classification contract is fixed.

**Prereq:** Plan 3 (MVP universe) — the harness iterates the MVP-for-MDPS universe and knows which combos carry features
vs candles-only.

## Classification contract (rides the existing 4-state capture_status — no new bookkeeping)

| State                    | Meaning                                                         | Smoke-test behaviour                                  |
| ------------------------ | --------------------------------------------------------------- | ----------------------------------------------------- |
| **RUNNABLE**             | continuous coverage over the required window                    | run the path; it MUST succeed                         |
| **INSUFFICIENT-HISTORY** | only a partial window present                                   | **FAIL** — never run partial                          |
| **HONEST-EMPTY**         | genuinely no data (e.g. no trades that day / `empty_confirmed`) | handled, not a failure — assert the path tolerates it |

## Required-window is product-shaped

- **Sports / seasonal** — a long _continuous_ instrument-and-market pipeline across seasons (markets open/settle; need
  cross-season continuity, not a single day).
- **Max-daily-aggregation data types** — a single day is enough (the path only ever aggregates within a day).
- Everything else — a declared lookback window per (AG, data_type).

## Todos

- [ ] [DESIGN] P1. (opus) Define the classification function over the availability manifest: given (AG, venue,
      data_type, instrument, required_window), return RUNNABLE / INSUFFICIENT-HISTORY / HONEST-EMPTY using
      `capture_status` + the 4-state completeness math. Distinguish HONEST-EMPTY
      (`empty_confirmed`/`expected_unattempted`) from INSUFFICIENT-HISTORY (window only partially captured) — this is
      the crux and must not collapse. — Gate: a reviewed spec + a `classify_shard_coverage(...)` signature; honest-empty
      vs insufficient-history decision table.
- [ ] [DESIGN] P1. (opus) Build the **required-window registry** per (AG, data_type): seasonal-continuous for sports
      markets, daily for max-daily-aggregation types, lookback-N otherwise. Source the seasonal boundaries from the
      sports league registry, not magic numbers. — Gate: registry covers all 5 AGs' MVP data_types; sports entries
      reference real season windows.
- [ ] [IMPLEMENT] P1. Implement the harness: iterate the Plan-3 MVP universe, classify every shard, and emit a
      **coverage matrix** artifact (AG × venue × data_type × instrument → state + window covered). Select one
      representative RUNNABLE shard per (AG × venue × data_type) for the smoke set. — Gate: running the harness produces
      the matrix + a smoke-set manifest; no combo silently skipped (un-classified = hard error).
- [ ] [IMPLEMENT] P1. Wire a smoke-runner that, for each smoke-set shard, runs MDPS→features over the required window
      and asserts: RUNNABLE → succeeds with right-edge + no-look-ahead (calls Plan 4's guard); INSUFFICIENT-HISTORY →
      **refuses to run** (explicit fail, not a partial pass); HONEST-EMPTY → path tolerates absence without crashing or
      writing silent placeholders. — Gate: the runner exits non-zero on a planted INSUFFICIENT-HISTORY shard and green
      on a real RUNNABLE shard for each AG.
- [ ] [VERIFY] P1. Run the harness against live manifests for all 5 AGs; publish the coverage matrix (which combos are
      RUNNABLE today vs gaps). Big gaps → file issue docs per findings-triage, do not silently descope. — Gate: matrix
      published in this plan's Progress Log; any RED combo has an issue doc or is a known HONEST-EMPTY.
- [ ] [AGENT] P1. e2e-testing (+ any UAC helper) QG green; quickmerge `--agent --files`. — Gate: QG green; CI
      `quality-gates-v2` green.

## Representative smoke matrix (audit-derived 2026-06-28)

**Min-window driver (correction):** the minimum continuous window is
`max over feature families of (lookback_periods × coarsest_timeframe)` for what consumes that shard — NOT the base
granularity. A 200-period feature at 24h needs ~200 trading days even on a 15s base. The required-window registry
computes this from the real feature config, not a guess.

Per-AG representative shard + min-window + today's blocker (full per-AG matrices in the Progress Log):

| AG             | Representative shard(s)                                                                                                               | Min continuous window (driver)                                                                             | Today's coverage verdict / blocker                                                                                                        |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| **CeFi**       | BINANCE-FUTURES BTC perp — trades + book_snapshot_5 + derivative_ticker; DERIBIT BTC options_chain/futures_chain (bundle)             | ~200 trading days if any 24h-TF feature uses a 200-period lookback; days for 1m-only families              | RUNNABLE on Binance; **372 HYPERLIQUID phantoms** to reconcile; HL liquidations + DEX book = honest-absent                                |
| **DeFi**       | UNISWAP_V3-ETH dex_pool_swaps (tick) + dex_pool_state; AAVE_V3 lending_indices; LIDO lst_rates; oracle_prices; DRIFT-SOL perp_funding | snapshots → short (1–2d); dex_pool_swaps → intraday; coarse-TF feature lookback otherwise                  | **~219k phantom rows** (swaps_ohlcv batch-writer failure) gate RUNNABLE; UNISWAP_V4/vault = non-MVP, skip                                 |
| **TradFi**     | CME ES + NQ + VX(XCBF) futures (ohlcv_1m); a commodity (GC/CL); equity/ETF basis leg (SPY/AAPL)                                       | ~290 calendar days for a 200-period 24h feature (1m base)                                                  | **BLOCKED-until-Plan-5** (no MDPS passthrough layer; dependency-checker `instrument_id=''` bug); 15s/options/VIX-cash/ICE = honest-absent |
| **Sports**     | EPL × {api_football FIXTURES, understat XG, odds_api ODDS(tick), footystats}; EREDIVISIE (understat HONEST-EMPTY)                     | **season-continuous — golden window `2025-09-01 .. 2025-11-30` (91d)** satisfies all rolling/CLV lookbacks | RUNNABLE in golden window; structural gaps: understat=big-5-only (89 absent), A_LEAGUE×footystats, GREEK×transfermarkt                    |
| **Prediction** | A crypto market live on BOTH Polymarket+Kalshi (arb-overlap), + politics + sports; trades + book_snapshot_5 + CQG/market_lifecycle    | **one full market lifecycle** (created→resolved→settled): ~1.5h hourly, ~24h daily, long for elections     | **~19.5k phantoms** (52% of captured) flip + MTDS writer fix prerequisite; single-venue + financial = honest-absent                       |

**Cross-AG blocker the harness must encode:** four AGs carry phantom-capture pollution (the just-pulled
`phantom_captures_*_2026_06_28.md` issues) and TradFi is MDPS-gap-blocked — so "RUNNABLE today" ≠ "RUNNABLE after
reconciliation." The classifier reads the post-reconciliation manifest, and the smoke set names the
reconciliation/Plan-5 prerequisite per shard rather than silently passing on a phantom `captured`.

## Notes

- "Fail on partial" is the hard rule here: a half-window must NOT produce a green smoke test. The classifier's
  insufficient-history branch is the safety property — test it adversarially.
- Honest-empty handling is already partly covered by the data-pipeline-correctness contingencies
  (`data_pipeline_hardening_self_monitoring_2026_06_22`); this harness _consumes_ those signals, it doesn't re-implement
  honest-absence detection.
- Output feeds Plan 7: the benchmark picks its full-month shard from the RUNNABLE set (Binance first).
