---
title: "Macro + micro economic data capture — coverage audit across all 5 asset groups (capacity vs backfill)"
created: 2026-06-05
author: Harsh (audit run via Claude Code)
source:
  - Codebase audit 2026-06-05 — 6-domain parallel sweep (macro / CeFi / DeFi / TradFi / Sports+Prediction /
    codex-registry) walking the adapter→pipeline→manifest→codex chain with file:line evidence
  - unified-api-contracts/unified_api_contracts/registry/capability_declarations/{_altdata,_tradfi,_cefi,_defi*,_sports}.py
  - unified-api-contracts/unified_api_contracts/registry/{expected_coverage,data_source_continuity,data_availability}.py
  - unified-trading-pm/codex/02-data/{mtds-data-source-coverage-matrix,tradfi-data-types-catalog,defi-data-types-catalog,sports-data-source-coverage-matrix,prediction-data-types-catalog,honest_coverage_baseline_2026_05}.md
  - News-data-vendor research 2026-06-05 (prior; ETF-flow + macro vendor landscape)
parent_epic: mtds_mdps_master
priority: P1
status: active
estimate_class: infra
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 5
---

# Macro + micro economic data capture — coverage audit (2026-06-05)

> **Framing (operator, 2026-06-05):** "It's possible we haven't done the backfill on this, but that doesn't mean we
> don't have the capacity." This audit therefore separates **capability** (does an adapter/pipeline exist that _can_
> capture the source?) from **backfill/population** (have we actually _run_ it and do rows exist in the manifest?). A
> source we can capture but haven't backfilled is a **run task**, not a build task — and must not be mislabelled as a
> coverage gap.

## What I found

**Headline:** Microeconomic / market-structure data is captured **well** across almost every asset group (L3/L4).
Macroeconomic data is **essentially TradFi-only and thin**, and a whole tier of _free, public-domain_ macro/alt-data
sources is **declared in the UAC contracts but has no fetch adapter at all** (L0). So "the public data is available and
we're probably capturing it" is true for **micro**, not for **macro**.

### Capture-evidence ladder (how each source was classified)

| Level  | Meaning                                                                                                |
| ------ | ------------------------------------------------------------------------------------------------------ |
| **L0** | DECLARED only — a UAC contract dir / `SourceCapability` / registry entry exists, **no fetch adapter**  |
| **L1** | ADAPTER exists — code that can fetch the source, but not wired into a running pipeline                 |
| **L2** | PIPELINE-WIRED — adapter wired into an MTDS handler / features calculator / CLI operation              |
| **L3** | CAPTURES + EMITS — writes a `data_type` to GCS/manifest (`record_captured`/`record_empty`) **in code** |
| **L4** | DOCUMENTED — codex catalog/matrix lists it as captured with a coverage status                          |

**Important honesty caveat:** L3/L4 confirm the code _emits_ and the docs _claim_ capture. They do **NOT** confirm rows
are actually present in GCS/manifest for a given date range. **Actual population is unverified** — that is Phase 0
below, and it is exactly where the capacity-vs-backfill distinction gets settled per source.

### Coverage matrix (today)

| Asset group    | Micro / market-structure                                                                                                                                    | Macro / economic                                                                                                                                 |
| -------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| **CeFi**       | ✅ Strong (L3/L4) — funding, open interest, mark/index, liquidations, L2 book depth-5, trades, Deribit options IV/greeks/skew (dual live-WS + Tardis-batch) | ❌ None of its own (leans on shared TradFi macro)                                                                                                |
| **DeFi**       | ✅ Strong (L3/L4) — LST APRs, lending rates+utilization, DEX TVL/liquidity/volume/fees, oracle (Chainlink/Pyth), gas, MEV, perp-DEX funding, restaking      | ⚠️ On-chain "fundamentals" only (TVL via DeFiLlama). Crypto sentiment (Glassnode/fear_greed) declared-not-wired                                  |
| **TradFi**     | ⚠️ Equity/futures/VIX OHLCV captured (Databento); **fundamentals + ETF flows MISSING**                                                                      | ✅ Real — FRED rates/curve/inflation/credit/VIX + econ-calendar dates + corp-actions + earnings. **But outside the honest-coverage gate + thin** |
| **Sports**     | ✅ Strong (L4) — fixtures/stats/xG/injuries/lineups/weather + intraday odds (the-odds-api + Betfair exchange)                                               | ➖ N/A (direct-bookmaker odds incl. Pinnacle = operator-deferred, not a bug)                                                                     |
| **Prediction** | ✅ Polymarket + Kalshi (trades/book/lifecycle/question-groups)                                                                                              | ➖ Macro only as market _labels_; Manifold (3rd venue) is an empty dir                                                                           |

### The three categories (capacity vs backfill — the spine of this audit)

**Category A — capacity BUILT + WIRED; backfill/population TO BE VERIFIED (L2–L4 in code).** These are _not_ build
tasks. If a manifest check shows them empty for a window, the fix is **run the backfill**, not write code.

- TradFi macro: `macro_result` (FRED ~25 series — UST curve, TIPS, FedFunds/SOFR, T10Y2Y, HY-OAS, CPI, breakevens, GDP,
  UNRATE, VIXCLS) — `market-tick-data-service/.../adapters/tradfi/fred_adapter.py`
- TradFi: equity/futures OHLCV (Databento), VIX 24h/15m (Barchart+Yahoo+honest gap), corporate actions (Polygon),
  earnings (yfinance) — features-service `calendar/`
- CeFi: `derivative_ticker` (funding/OI/mark/index), `trades`, `book_snapshot_5`, `liquidations`, `options_chain` — MTDS
  live-WS connectors + Tardis batch
- DeFi: `lst_rates`, `lending_indices`, `dex_pool_state`, `dex_pool_swaps`, `oracle_prices`, `gas_fees`, `mev_events`,
  `perp_funding`, `native_staking`, `eigenlayer_rewards`, `liquidation_events` — MTDS DeFi handlers
- Sports: api_football / footystats / understat / transfermarkt / open_meteo + odds_api + Betfair
- Prediction: Polymarket + Kalshi

**Category B — capacity BUILT but ORPHANED / UNWIRED (L1).** Adapter exists; not reachable by the running pipeline. Fix
= wire + run (small).

- features-service `calendar/.../yield_curve_calculator.py` + `economic_results_calculator.py` — **registered in the
  calculator registry but NOT in `CALENDAR_FEATURE_GROUPS` (`calendar/cli/handlers/batch_handler.py`)** → never
  dispatched. Also the `economic_results` handler `app()` is not registered in the calendar CLI `ServiceBootstrap`
  operations → built but no scheduler/script invokes it. (Duplicates the MTDS FRED path.)
- TradFi `massive_tradfi_rest_connector.py` (6 data_types incl. options_chain/futures_chain) — scaffold, zero
  orchestrator refs
- TradFi `ecb_adapter.py` / `ofr_adapter.py` / `openbb_adapter.py` / `ibkr_adapter.py` — adapters exist + L0 capability
  decls, no orchestrator wiring / manifest emission found
- DeFi `onchain/adapters/cryptoquant_adapter.py` — exists (L1), no wired MTDS operation/emission

**Category C — GENUINE capability gap (L0, no adapter — or empty stub).** These need an adapter built. Most have the UAC
`SourceCapability` already declared, so they are _scaffolded_, not zero.

| Source                                                   | Provides                                                      | Public?                                                                        | UAC state                                                                            |
| -------------------------------------------------------- | ------------------------------------------------------------- | ------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------ |
| **CFTC (COT)**                                           | speculative positioning (macro sentiment)                     | free                                                                           | declared `_altdata.py`, no adapter                                                   |
| **EIA**                                                  | oil/gas inventories (energy macro)                            | free w/ key                                                                    | declared `_altdata.py`, no adapter                                                   |
| **Baker Hughes**                                         | rig counts (energy supply)                                    | free                                                                           | declared `_altdata.py`, no adapter                                                   |
| **fear_greed**                                           | crypto risk sentiment                                         | free, **no auth**                                                              | UAC dir is an **empty stub**                                                         |
| **open_meteo (as macro)**                                | weather → commodity/energy macro                              | free, no auth                                                                  | adapter exists for **Sports** but never exposed as a macro feed                      |
| **PMI / ISM, regulatory**                                | activity surveys / policy                                     | free/public                                                                    | declared, nothing                                                                    |
| **ETF FLOWS**                                            | net creation/redemption (BTC/S&P decorrelation signal)        | public (Farside free-unlicensed) / **CoinGlass ~$29/mo licensed** / SEC N-PORT | **not even properly declared** — `rg etf_flow\|fund_flow\|net_creation` = **0 hits** |
| **Equity fundamentals / earnings financials**            | balance-sheet / income / cashflow                             | public (SEC EDGAR / yfinance)                                                  | declared-only `_tradfi.py`                                                           |
| **CeFi aggregators (Coinglass / Hyblock / CryptoQuant)** | cross-venue aggregated OI, long/short, top-trader positioning | freemium                                                                       | UAC dirs **empty stubs**                                                             |
| **Glassnode on-chain sentiment**                         | MVRV / SOPR / NVT / NUPL / exchange-balance                   | $29/mo                                                                         | declared batch-only `_altdata.py`, unwired                                           |
| **Live stablecoin peg time-series**                      | USDC/USDT/DAI live depeg                                      | public on-chain                                                                | only **static** history registries exist                                             |
| **dYdX perp funding**                                    | perp-DEX funding (arb leg)                                    | free                                                                           | only in `internal/architecture_v2/venue_tokens.py` (L0)                              |
| **Manifold**                                             | 3rd prediction venue (cross-venue dispersion)                 | free                                                                           | UAC dir **empty**                                                                    |

> **Out of scope here (operator-decided, not a gap):** direct-bookmaker sports odds (bet365 / Pinnacle / 14 others) were
> **DEFERRED-INDEFINITELY 2026-05-12**; scrapers deleted from MTDS `_ADAPTER_PATHS`. Sports line-movement currently
> rests on the-odds-api + Betfair. Listed only so it isn't re-flagged.

## Why it matters

1. **No asset-group-agnostic macro pipeline + no owning plan.** Macro is bolted onto TradFi. The `altdata` asset_group
   was **deprecated** (audit IN-5, 2026-05-12) and orphaned, so these sources have no clean home. Filename + content
   grep across `plans/active/`, `active/issues/`, `epics/` for `macro|economic|altdata|fundamental|etf|sentiment` →
   **zero owning plan/epic.** This is unowned work.
2. **Macro is outside the honest-coverage gate.** `registry/expected_coverage.py` has **no `altdata` key**, and TradFi
   scope lists only OHLCV venues — _not_ FRED / `macro_result`. No macro source has a `coverage_start`. So even captured
   macro can be **silently empty without failing any quality gate** — directly contradicting the "trust the actual
   distribution, not the constant" and "honest-absence" rules. (`honest_coverage_baseline_2026_05.md` is still DRAFT/TBD
   — no macro baseline measured.)
3. **"External data is always available — never silently defer adapters" (HARD RULE).** The Category C sources are
   free/public; per the rule, the unblock for the paid ones (ETF flows, Glassnode) is a credential/subscription **ask**,
   not a descope.
4. **The immediate trading use case.** The BTC/S&P decorrelation + MicroStrategy-driven move that started this thread
   needs **ETF flows + macro** — both in the thin/missing column.
5. **Batch == live.** Macro/alt-data must capture once and replay the same rows; a capture-at-publish discipline
   (immutable `available_at` = capture time) fits the existing manifest/parquet model and avoids the point-in-time
   pitfalls flagged in the news-vendor research.

## What is NOT yet verified — Phase 0 (the capacity-vs-backfill resolver)

This audit verified **code capacity** (file:line on the ladder). It did **NOT** verify actual GCS/manifest **row
population**. Before any build, run Phase 0 to classify each Category-A/B data_type as _populated_ vs
_empty-needs-backfill_:

- For each macro/micro `data_type`: resolve bucket via `resolve_bucket_name(...)`, read the manifest `_index`, and
  report captured/empty/expected_unattempted counts over a known window (e.g. last 90d). Use the actual
  `schema_version` + `capture_status` distribution, never the constant.
- Spot-inspect a sample parquet per data_type (row count > 0, schema matches contract, no silent placeholders).
- Output: a per-data_type table — **populated** (done) / **coded-but-empty** (Category A → run backfill) / **orphaned**
  (Category B → wire+run) / **absent** (Category C → build).

## Recommended decision

Phased, foundation-first; parallel-up _within_ a layer, not across:

- **Phase 0 — Verify population** (above). ~0.5d. Settles which Category-A items are merely un-backfilled.
- **Phase 1 — Free quick wins (highest value × ease):**
  1. **fear_greed** adapter — free, no-auth, UAC scaffold + capability already exist → ~100 lines. Crypto risk sentiment
     for CeFi+DeFi.
  2. **CFTC COT** + **EIA** + **Baker Hughes** — free macro, capabilities declared, adapters small.
  3. Wire the **Category B orphans** (yield_curve / economic_results into `CALENDAR_FEATURE_GROUPS`; decide MTDS-FRED vs
     features-FRED as the single source of truth — do not run both).
- **Phase 2 — ETF flows** (explicitly wanted): build the flow data_type; source decision is operator's (free-unlicensed
  Farside vs **CoinGlass ~$29/mo licensed** vs SEC N-PORT) — see news-vendor research 2026-06-05.
- **Phase 3 — Bring macro/alt-data into the honest-coverage gate:** add an `altdata` (or fold into a SHARED axis) key in
  `expected_coverage`, set `coverage_start` dates, register in the data-status matrix so macro can no longer be silently
  empty.
- **Phase 4 — Remaining Category C breadth:** Glassnode on-chain sentiment, CeFi aggregators (Coinglass/Hyblock), live
  stablecoin peg, dYdX funding, Manifold, equity fundamentals — likely an epic-scoped follow-on (estimate above covers
  Phases 0–2 + B-wiring; full C breadth is larger).

## Open questions for operator (Harsh + Ikenna)

1. **`altdata` home:** revive `altdata` as a real asset_group, or model macro as a SHARED cross-asset axis? (Decides
   where data_types + buckets live.)
2. **Build-vs-buy for paid sources:** approve CoinGlass (~$29/mo, ETF flows) and Glassnode (~$29/mo, on-chain
   sentiment)? Both are credential/subscription asks per the External-Data rule.
3. **Single FRED source of truth:** MTDS `fred_adapter` vs features-service `calendar/fred_adapter` — both exist; one
   should be deleted (no parallel paths).
4. **Scope of first tranche:** all 5 asset groups' macro at once, or crypto (CeFi+DeFi) macro/sentiment + ETF flows
   first to serve the current decorrelation thesis?

## Correctness sub-findings (surfaced per Findings-Triage, NOT fixed here)

- **`codex/02-data/tradfi-data-types-catalog.md` is stale:** claims earnings via Polygon (actually **yfinance**);
  references handler names that don't exist in code (`tradfi_ohlcv_handler`, `corporate_action_handler`). →
  codex-alignment fix.
- **Banned-provider drift:** **Polygon.io is the live corporate-actions source**
  (`features-service/.../calendar/adapters/polygon_corporate_actions_adapter.py`) despite Polygon being a banned TradFi
  data provider per workspace CLAUDE.md. → operator decision (replace vs un-ban for corporate actions specifically).
- **Live Binance-futures OI** hardcoded `None` on the WS path (`binance_futures_book_ticker_ws.py`) — OI only via Tardis
  batch on the largest venue.

## Audit method + provenance

6 parallel general-purpose audit agents (2026-06-05), one per domain (macro / CeFi / DeFi / TradFi / Sports+Prediction /
codex-registry), each grep-then-**read** (0 hits ≠ absent — escalated to reading candidate handler/connector/registry
files), classifying every source on the capture ladder with file:line evidence. The macro and codex-registry audits
independently corroborated the L0 declared-not-wired set. Where a finding is code-only (not population-verified), it is
marked so above.
