---
title: "Macro + micro economic data capture — coverage audit across all 5 asset groups (capacity vs backfill)"
created: 2026-06-05
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
locked_by: live-defi-rollout
locked_since: 2026-05-21
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
4. **The immediate trading use case (refined w/ Ikenna 2026-06-05).** MicroStrategy/Saylor sells **actual BTC, not ETF
   shares** — so the "who's selling" signal is **on-chain whale-wallet / entity flows** (Glassnode-class labeling),
   _not_ ETF flows. ETF flows remain useful for the BTC-ETF-demand / S&P-decorrelation axis but are a _different_
   signal. Both the on-chain whale-flow source and macro sit in the thin/missing column. (Corrects the earlier ETF-flow
   conflation.)
5. **Batch == live.** Macro/alt-data must capture once and replay the same rows; a capture-at-publish discipline
   (immutable `available_at` = capture time) fits the existing manifest/parquet model and avoids the point-in-time
   pitfalls flagged in the news-vendor research.

## Phase 0 — live capture verification (EXECUTED 2026-06-05)

Verified against the live `data-status-rollup` (Cloud Run job, every 5 min →
`gs://central-element-323112-data-status-rollups/<service>/{coverage,full}.json.gz`; snapshot 2026-06-03) — the same
coverage surface the deployment-UI data-status drilldown reads. **This settles capacity vs backfill with hard numbers.**

### Micro / market-structure — CAPTURED + POPULATED ✅

| Asset group    | Bucket                          | Days found/expected (2018–2026) | Head date      | Venues                                                                                                         | Notes                                                                                                                    |
| -------------- | ------------------------------- | ------------------------------- | -------------- | -------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| **CeFi**       | `market-data-tick-cefi-…`       | 29.4% (2577/3076)               | 2026-04-18     | 20 (Binance/Bybit/OKX/Deribit/Hyperliquid/Kraken/Bitget/Bitfinex/Aster/Upbit + DEX-perps)                      | 121B obs; per-venue high (Binance-fut 87%); per-data_type uneven (trades/derivative_ticker rich, book_snapshot_5 sparse) |
| **TradFi**     | `market-data-tick-tradfi-…`     | 79.1% (2297/3076)               | 2026-04-15     | 6 exchanges: CBOE, CME, FX, ICE, NASDAQ, NYSE                                                                  | equity/futures OHLCV (Databento)                                                                                         |
| **DeFi**       | `market-data-tick-defi-…`       | 46.8% (2340/3076)               | **2026-05-28** | **70** (all LST, lending ×8 chains, DEX, + explicit `LST_RATES`/`ORACLE_PRICES`/`GAS_FEES`/`CHAINLINK`/`PYTH`) | most comprehensive + current                                                                                             |
| **Sports**     | `market-data-tick-sports-…`     | 100% (2128 days)                | —              | (league/match axis)                                                                                            | populated                                                                                                                |
| **Prediction** | `market-data-tick-prediction-…` | 78% but only 398 days           | 2026           | Polymarket, Kalshi                                                                                             | captured but sparse/recent                                                                                               |

### Macro / economic — CODED, NOT POPULATED ❌ (capacity ≠ backfill, confirmed)

- **MTDS manifest keyword scan: `fred`=0, `yield_curve`=0, `economic`=0, `vix`=0** across the ENTIRE production
  manifest. The FRED rates/curve/CPI capture (`fred_adapter`) has **never run in production — 0 rows.** (By contrast
  `derivative_ticker`=48, `lst_rates`=24, `oracle_prices`=46, `gas_fees`=12 confirm micro is real.)
- **`features-calendar-service` rollup: `bucket=""`, 0 shards, 0% completion** for every asset group — the macro
  calendar features (economic_events dates, NFP/CPI/GDP actuals, time_features, yield_curve features) are **not
  populated and not even monitored**.
- **`features-onchain-service` rollup: 0 shards** — the DeFi on-chain FEATURE layer is unpopulated too (raw on-chain
  data IS in MTDS DeFi; the downstream feature computation hasn't run).

**Conclusion — answers the operator's exact question:** for **macro**, the hypothesis is confirmed — _we have the
capacity (adapters/calculators) but never ran the backfill_; the FRED rates/curve/inflation slice is a **run task, not a
build task**. For **micro**, we both built and populated it. The free Category-C macro sources
(CFTC/EIA/Baker-Hughes/fear_greed) remain genuine build tasks.

### Secondary findings from the live data

- **Head-of-feed staleness:** CeFi head = 2026-04-18, TradFi = 2026-04-15 (~7 weeks stale vs 2026-06-05); DeFi current
  (2026-05-28). CeFi/TradFi capture appears stalled/paused at the head — worth a separate operational check.
- **Feature layers (calendar + onchain) empty** even where raw is captured → the feature-computation cadence is not
  running (the Category-B orphan finding, confirmed live).

## Vendor cost/coverage refresh (Ikenna's questions, 2026-06-05)

Web-verified; refines the news-vendor research 2026-06-05. Lens = "cheap + useful enough to _preliminary-add to the
chain to assess viability_" (Ikenna's bar), not a full build.

| Vendor                                           | What it gives us                                                                                                                                                                                                               | Real cost                                                                                                  | Verdict                                                                                                                                                                                                                                                                                                                                                                           |
| ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Glassnode (Studio Professional)**              | **on-chain whale/entity flows** — Whale Exchange Flows (1k+ BTC entity deposits = large-holder selling pressure), entity-adjusted flows, whale cohorts, supply distribution. The actual "Saylor-type" signal. API is Pro-only. | **$999/yr** (NOT the ~$10k recalled — that's bespoke Enterprise). $29-49/mo retail has no entity data/API. | **strong + cheap** — best single add for the on-chain "who's selling" signal                                                                                                                                                                                                                                                                                                      |
| **CryptoQuant**                                  | exchange/whale/miner flow intelligence + API (Glassnode alternative)                                                                                                                                                           | ~hundreds–low-thousands $/yr                                                                               | **we already have an L1 `cryptoquant_adapter.py`** (Category B) — wiring it may beat buying Glassnode; evaluate both                                                                                                                                                                                                                                                              |
| **CoinGlass API**                                | spot BTC/ETH/SOL ETF flow-history **+** cross-venue funding/OI/liquidations/long-short (the CeFi-aggregator gap in this audit)                                                                                                 | $29 Hobbyist / $79 Startup / **$299 Standard (commercial+history)** / $699 Pro per mo                      | **good dual-purpose** — one sub covers ETF flows AND the missing CeFi aggregator tier                                                                                                                                                                                                                                                                                             |
| **CryptoPanic**                                  | crypto news aggregation + crowd-vote PanicScore sentiment                                                                                                                                                                      | free Developer tier ends 2026-04-01; paid Growth/Enterprise ~$30/mo (unverified, bot-gated)                | **cheap but get a quote**; sentiment is crowd-vote (noisy), not NLP                                                                                                                                                                                                                                                                                                               |
| **RavenPack / Bigdata.com**                      | news NLP / sentiment / event _detection_ (Edge). **NOT** the "HFT NFP/GDP actuals" the LinkedIn pitch implied — "squawk" is a third-party term (Newsquawk/LiveSquawk).                                                         | enterprise contact-sales; small-fund ~$50-150k/yr; macro slice = same Edge license                         | **expensive + mis-pitched** — for fast economic ACTUALS the real vendors are **AlphaFlash (CME, sub-second NFP/CPI/FOMC), Newsquawk, haawks**                                                                                                                                                                                                                                     |
| **Massive = Polygon.io rebrand / Benzinga news** | US-equity news (published_utc PIT, Benzinga archive to 2001) + ticker sentiment                                                                                                                                                | $29-79/mo                                                                                                  | ✅ **Already an adopted vendor** — Massive _is_ Polygon.io rebranded (2025-10-30) and is Databento's secondary TradFi source in `SOURCE_PRIORITY` (plan `tradfi_massive_dual_source_2026_05_28.md`); we already hold the adapter + key, so its Benzinga **news** endpoint is a natural same-vendor add. (The CLAUDE.md "removed Polygon.io" line is **stale** — see sub-finding.) |
| **LunarCrush**                                   | crypto (now equities) social metrics (Galaxy Score, AltRank, social volume)                                                                                                                                                    | ~$24/mo                                                                                                    | cheap social-sentiment feed; metrics not raw news                                                                                                                                                                                                                                                                                                                                 |

**Net:** cheapest high-value adds = **Glassnode Pro (~$999/yr)** for the on-chain whale-flow / Saylor signal, and
**CoinGlass (~$299/mo)** if we want ETF flows + the CeFi-aggregator gap in one sub. Both are operator
credential/subscription asks. **CryptoQuant is already half-wired** (Category B) — evaluate wiring it before buying
Glassnode.

## Architecture direction (Ikenna + Harsh, 2026-06-05)

Agreed end-state for news/alt-text: **cheap LLM (Haiku) + our own embeddings/entity-graphs extract news into
_deterministic_ features** (`entity_sold_btc=1`, amount, long/short + sector/entity-impact "weightage knobs") feeding
the existing ~20k-feature gradient-boosted-tree stack — i.e. LLM-as-feature-extractor, not LLM-as-trader. Polymarket is
**both a venue and a (free, already-captured) deterministic political/event data source**. This is a large, _later_
effort (post the current data-pipeline push); the near-term move is only to **preliminary-add a cheap+useful source to
assess viability** — pointing back to Glassnode Pro / CoinGlass / fear_greed, not the full news-NLP build.

## Recommended decision

Phased, foundation-first; parallel-up _within_ a layer, not across:

- **Phase 0 — Verify population — DONE 2026-06-05** (above): micro populated; **macro = 0 rows (capacity exists,
  backfill never ran)**; feature layers (calendar/onchain) empty; CeFi/TradFi heads ~7wk stale.
- **Phase 1 — RUN WHAT WE ALREADY HAVE (≈0 build — the capacity-vs-backfill wins):**
  1. **Run the FRED macro backfill** (rates/curve/CPI/VIX-daily) — the adapter exists and emits, it has simply never
     run. Pick MTDS-FRED **or** features-FRED as the single source of truth (do not run both) and backfill from 2018.
  2. **Wire the Category-B orphans** so the feature layer populates: `yield_curve` / `economic_results` into
     `CALENDAR_FEATURE_GROUPS`; trigger the calendar + on-chain feature computation (both currently 0 shards).
  3. **Investigate the CeFi/TradFi head-staleness** (~7wk) — capture paused, or a lagging batch cadence?
- **Phase 2 — Free quick-win adapters (small builds, capabilities already declared):** **fear_greed** (free, no-auth,
  ~100 lines), then **CFTC COT** + **EIA** + **Baker Hughes** (free macro).
- **Phase 3 — On-chain whale-flow signal (the Saylor signal):** wire the existing L1 `cryptoquant_adapter.py`, and/or
  operator approves **Glassnode Pro (~$999/yr)** credential ask.
- **Phase 4 — ETF flows:** build the flow data_type — **CoinGlass (~$299/mo commercial, also fills the CeFi-aggregator
  gap)** vs free-unlicensed Farside vs SEC N-PORT — operator's call.
- **Phase 5 — Bring macro/alt-data into the honest-coverage gate:** add an `altdata` (or fold into a SHARED axis) key in
  `expected_coverage`, set `coverage_start` dates, register in the data-status matrix so macro can no longer be silently
  empty.
- **Phase 6 — Remaining Category C breadth:** Glassnode sentiment metrics, CeFi aggregators (Coinglass/Hyblock), live
  stablecoin peg, dYdX funding, Manifold, equity fundamentals — likely an epic-scoped follow-on.

## Open questions for operator (Harsh + Ikenna)

1. **`altdata` home:** revive `altdata` as a real asset_group, or model macro as a SHARED cross-asset axis? (Decides
   where data_types + buckets live.)
2. **Build-vs-buy for paid sources:** approve **Glassnode Pro (~$999/yr, whale/entity flows)** and/or **CoinGlass
   (~$299/mo, ETF flows + CeFi aggregator)** — or evaluate the already-half-wired **CryptoQuant** adapter first? All are
   credential/subscription asks per the External-Data rule.
3. **Single FRED source of truth:** MTDS `fred_adapter` vs features-service `calendar/fred_adapter` — both exist; one
   should be deleted (no parallel paths).
4. **Scope of first tranche:** all 5 asset groups' macro at once, or crypto (CeFi+DeFi) macro/sentiment + ETF flows
   first to serve the current decorrelation thesis?

## Correctness sub-findings (surfaced per Findings-Triage, NOT fixed here)

- **`codex/02-data/tradfi-data-types-catalog.md` is stale:** claims earnings via Polygon (actually **yfinance**);
  references handler names that don't exist in code (`tradfi_ohlcv_handler`, `corporate_action_handler`). →
  codex-alignment fix.
- **Stale SSOT + naming inconsistency (NOT a ban — corrected 2026-06-05):** the workspace CLAUDE.md "Removed providers:
  Polygon.io (TradFi data)" line is **stale**. Polygon.io **rebranded to Massive** (2025-10-30) and was deliberately
  **re-adopted** as Databento's secondary TradFi source — `massive_tradfi_rest_connector.py` (base URL
  `https://api.polygon.io`), `SOURCE_PRIORITY[("tradfi", …)] = ["databento", "massive"]`, plan
  `tradfi_massive_dual_source_2026_05_28.md`. The corporate-actions adapter hits the same `api.polygon.io` but is named
  `polygon_corporate_actions_adapter.py` → **one vendor, two names**. Action: (a) update the CLAUDE.md "removed" line to
  record the rebrand + re-adoption; (b) align the `polygon`↔`massive` naming. **Not a ban.**
- **Live Binance-futures OI** hardcoded `None` on the WS path (`binance_futures_book_ticker_ws.py`) — OI only via Tardis
  batch on the largest venue.

## Audit method + provenance

6 parallel general-purpose audit agents (2026-06-05), one per domain (macro / CeFi / DeFi / TradFi / Sports+Prediction /
codex-registry), each grep-then-**read** (0 hits ≠ absent — escalated to reading candidate handler/connector/registry
files), classifying every source on the capture ladder with file:line evidence. The macro and codex-registry audits
independently corroborated the L0 declared-not-wired set. Where a finding is code-only (not population-verified), it is
marked so above.
