---
doc_type: issue
title: Macro + micro economic data capture — coverage audit across all 5 asset groups (capacity vs backfill)
summary: >-
  Headline: Microeconomic / market-structure data is captured well across almost every asset group (L3/L4).
  Macroeconomic data is essentially TradFi-only and thin, and a free-tier vendor category is coded but not backfilled
  (capacity ≠ backfill) — includes a vendor cost/coverage refresh and an architecture-direction decision log.
status: resolved
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [features-service, market-tick-data-service]
scope: [engineer, admin]
tags: [audit, data-correctness, tradfi, defi, cefi, honest-coverage, backfill, features]
related: [macro_econ_adapter_scaffolds_2026_06_09]
created: 2026-06-05
author: unknown
parent_epic: mtds_mdps_master
priority: P1
source:
  [
    "Codebase audit 2026-06-05 — 6-domain parallel sweep (macro / CeFi / DeFi / TradFi / Sports+Prediction /
    codex-registry) walking the adapter→pipeline→manifest→codex chain with file:line evidence",
    "unified-api-contracts/unified_api_contracts/registry/capability_declarations/_altdata.py",
    "unified-api-contracts/unified_api_contracts/registry/capability_declarations/_tradfi.py",
    "unified-api-contracts/unified_api_contracts/registry/capability_declarations/_cefi.py",
    "unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi.py",
    "unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi_chain_data.py",
    "unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi_coverage.py",
    "unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi_lst.py",
    "unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi_oracle_coverage.py",
    "unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi_source_capabilities.py",
    "unified-api-contracts/unified_api_contracts/registry/capability_declarations/_sports.py",
    "unified-api-contracts/unified_api_contracts/registry/expected_coverage.py",
    "unified-api-contracts/unified_api_contracts/registry/data_source_continuity.py",
    "unified-api-contracts/unified_api_contracts/registry/data_availability.py",
    "/codex/02-data/mtds-data-source-coverage-matrix.md",
    "/codex/02-data/tradfi-data-types-catalog.md",
    "/codex/02-data/defi-data-types-catalog.md",
    "/codex/02-data/sports-data-source-coverage-matrix.md",
    "/codex/02-data/prediction-data-types-catalog.md",
    "/codex/02-data/honest_coverage_baseline_2026_05.md",
    News-data-vendor research 2026-06-05 (prior; ETF-flow + macro vendor landscape),
  ]
assigned_vm: planning
resolved_by: main-agent (blocked-question BLK-00e5bdf7, 2026-08-13) -- all todos [x], no open work
locked_by:
context_scope:
  [
    /plans/active/data_completion_to_100_all_ag_2026_06_21.md,
    market-tick-data-service/market_tick_data_service/engine/orchestrator/manifest_finalize.py,
    instruments-service/instruments_service/reference_data/adapters/tradfi/fx.py,
    market-tick-data-service/market_tick_data_service/adapters/_umi_fred.py,
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
    /plans/archive/issues/fred_backfill_early_date_indefinite_stall_2026_07_30.md,
  ]
estimate_class: infra
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 5
locked_since:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-29
---

> **ARCHIVED 2026-08-13** — all todos [x], no open work. Archived via
> `plans/active/issues/locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10.md`'s follow-on pass (operator
> ruling option B, BLK-00e5bdf7).

# Macro + micro economic data capture — coverage audit (2026-06-05)

> **🟢 2026-06-09 — Phase 2 (free Category-C adapter scaffolds) BEING ADDRESSED via wrapper plan
> `plans/active/macro_econ_adapter_scaffolds_2026_06_09.md`** (parent_epic: mtds_mdps_master). Built: fear_greed UAC
> contract (was an empty stub) + `FearGreedAdapter`/`CFTCCOTAdapter`/`BakerHughesAdapter`/`EIAAdapter` in MTDS
> `adapters/tradfi/` (fetch → parse-via-UAC → `CanonicalOnChainMetric` + `classify_venue_error()` +
> `ADAPTER_FETCH_FAILED` + mock unit tests). EIA live fetch is `BLOCKED-CREDENTIALS` (free key ask in
> `ikenna_orchestrator/pings/slot_3.md`). **This audit STAYS ACTIVE** — the backfill RUN, paid sources (Glassnode/
> CoinGlass/CryptoQuant), and the `altdata` asset-group / honest-coverage-gate / GCS-shard-write wiring (Open Questions
> #1–#4, Phases 3–6) remain operator-blocked and are tracked on the wrapper plan + here.
>
> **[2026-07-14 correction, verify-rerun-2 finding 229]**: the wrapper plan `macro_econ_adapter_scaffolds_2026_06_09.md`
> was SUPERSEDED/FOLDED 2026-07-13 (now `plans/archive/2026_07/macro_econ_adapter_scaffolds_2026_06_09.md`, banner: "do
> NOT dispatch further work here; the live todos are in M-1") as part of the MTDS/MDPS 2-survivor consolidation — every
> open todo was migrated verbatim into
> [`data_completion_to_100_all_ag_2026_06_21.md`](../data_completion_to_100_all_ag_2026_06_21.md) §"Folded-in scope
> 2026-07-13" (status: active). The remaining Phases 3-6 / backfill-RUN / paid-source work described above is now
> tracked on **that** live plan, not the archived wrapper. This audit doc (status: open) itself stays active as the
> canonical record of the coverage findings.

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

**Net:** cheapest high-value adds = **Glassnode Pro
(~$999/yr)** for the on-chain whale-flow / Saylor signal, and
**CoinGlass (~$299/mo)** if we want ETF flows + the
CeFi-aggregator gap in one sub. Both are operator credential/subscription asks. **CryptoQuant is already half-wired**
(Category B) — evaluate wiring it before buying Glassnode.

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
2. **Build-vs-buy for paid sources:** approve **Glassnode Pro
   (~$999/yr, whale/entity flows)** and/or **CoinGlass
   (~$299/mo, ETF flows + CeFi aggregator)** — or evaluate the
   already-half-wired **CryptoQuant** adapter first? All are credential/subscription asks per the External-Data rule.
3. **Single FRED source of truth:** MTDS `fred_adapter` vs features-service `calendar/fred_adapter` — both exist; one
   should be deleted (no parallel paths).
4. **Scope of first tranche:** all 5 asset groups' macro at once, or crypto (CeFi+DeFi) macro/sentiment + ETF flows
   first to serve the current decorrelation thesis?

## Correctness sub-findings (surfaced per Findings-Triage, NOT fixed here)

- **`/codex/02-data/tradfi-data-types-catalog.md` is stale:** claims earnings via Polygon (actually **yfinance**);
  references handler names that don't exist in code (`tradfi_ohlcv_handler`, `corporate_action_handler`). →
  codex-alignment fix.
- **SUPERSEDED 2026-08-12 (/plan-reconcile) — this finding is now itself the stale one.** ~~Stale SSOT + naming
  inconsistency (NOT a ban — corrected 2026-06-05): the workspace CLAUDE.md "Removed providers: Polygon.io (TradFi
  data)" line is stale. Polygon.io rebranded to Massive (2025-10-30) and was deliberately re-adopted as Databento's
  secondary TradFi source — `massive_tradfi_rest_connector.py` (base URL `https://api.polygon.io`),
  `SOURCE_PRIORITY[("tradfi", …)] = ["databento", "massive"]`, plan `tradfi_massive_dual_source_2026_05_28.md`. The
  corporate-actions adapter hits the same `api.polygon.io` but is named `polygon_corporate_actions_adapter.py` → one
  vendor, two names. Action: (a) update the CLAUDE.md "removed" line to record the rebrand + re-adoption; (b) align the
  `polygon`↔`massive` naming. Not a ban.~~ Massive/Polygon.io was subsequently fleet-wide BANNED for real (ruling
  2026-07-19, removal complete 2026-08-03 per current CLAUDE.md — "Removed vendors ... Massive-fka-Polygon.io (`polygon`
  = the CHAIN)"). `massive_tradfi_rest_connector.py` no longer exists in the repo (zero grep hits, confirmed by
  `data_completion_to_100_all_ag_2026_06_21.md`'s 2026-08-03 na-eligibility-audit), and
  `tradfi_massive_dual_source_2026_05_28.md` is itself archived. Do not re-adopt Polygon.io/Massive per this paragraph —
  it describes a policy that was reversed after this doc was last touched.
- **Live Binance-futures OI** hardcoded `None` on the WS path (`binance_futures_book_ticker_ws.py`) — OI only via Tardis
  batch on the largest venue.

## Todos

- [x] ✅ [OPERATOR] P1. **Operator-ruled 2026-07-29 (interactive decision session): FRED only — run the backfill.
      Explicitly declined Glassnode Pro and CoinGlass (not paying for either); operator already holds FRED API
      credentials.** Resolve the 4 open operator questions and action the Recommended-decision phases — e.g. Phase 1's
      FRED macro backfill (adapter exists, has never run in production) and Phase 5 (bring macro/alt-data into the
      honest-coverage gate); Phases 1-6 remain largely unactioned as of this doc's last update. Questions 1 (altdata
      home) and 4 (tranche scope) stay open — narrowed to FRED-only, no immediate call needed since FRED already has a
      home (`asset_group=tradfi`, venue=`FRED`, per the existing adapter). Question 2 (paid vendors) is now CLOSED — no
      Glassnode/CoinGlass. Question 3 (duplicate FRED adapter) was independently already resolved 2026-07-27 (see
      `june_2026_vintage_audit_findings_2026_07_27.md` item 41c) — features-service's adapter was deleted in favor of a
      pure MTDS-reader; only
      `market-tick-data-service/market_tick_data_service/market_interface/adapters/tradfi/ fred_adapter.py`'s
      `FredAdapter` remains, nothing left to delete.

- [x] ✅ [DESIGN] P1. **Scope + build the actual FRED backfill invocation — no runnable entry point exists today,
      confirmed 2026-07-29.** DONE — `unified-api-contracts@0c0f6953` + `market-tick-data-service@407f69f1`.
      `venue_mapping.all_databento_venues` + `VENUES_BY_ASSET_GROUP["tradfi"]` now include `"FRED"`; new
      `market_tick_data_service/adapters/_umi_fred.py::route_fred_tradfi` (mirrors `_umi_yahoo.py`'s shape, no Databento
      fallthrough — FRED has none) is wired into `fetch_tick_data_for_venue`'s dispatch chain ahead of the
      Yahoo/Databento branches; `tick_data_handler.py`'s `_VENUE_FIXED_SOURCE_VENUES` gained `"FRED"` (else the
      `--source databento` required-gate would raise on the first FRED-targeted run — same 2026-06-23 FX incident class,
      pre-empted this time). (a) instrument_id: `derive_tradfi_row_instrument_id(venue="FRED", instrument_type)` →
      `build_instrument_id("FRED", BOND|INDEX, series_id)` — already correctly implemented by
      `FredAdapter.write_canonical_shard`, just never invoked; reused as-is. (b) data_type mismatch: NOT a bug in the
      adapter — `market_data_categories.py`'s `"macro_result"` declaration for FRED was simply wrong/stale;
      `yield_curve`/`ohlcv_1d` is the real, already-correct wire contract (confirmed: features-service's
      `mtds_fred_reader.py`, shipped 2026-07-27, already reads exactly this shape). Corrected
      `VENUE_DATA_TYPE_CAPABILITIES["FRED"]` to declare it (this is the dict `get_expected_data_types_for_venue` reads
      to build the live pre-flight `data_types` filter in `venue_fetch.py` — without the fix a real capture run would
      only ever request `"macro_result"`, which the adapter never emits, and honest-empty every day). Added
      `"yield_curve"`/`"ohlcv_1d"` to `DATA_TYPES_BY_ASSET_GROUP["tradfi"]` (both were missing entirely, despite being
      legal in MTDS's own local `tradfi_shared.TRADFI_DATA_TYPES` — `validate_data_type_for_venue(strict=True)` gates on
      the UAC list, not the MTDS-local one). (c) expected_coverage: added `"FRED": ["yield_curve", "ohlcv_1d"]` to
      `_TRADFI` in `expected_coverage.py`. Discovered + fixed 2 more registry gaps the full QG surfaced (not in the
      original scoping): `venue_to_data_provider["FRED"]="fred"` and `VENUE_TO_ADAPTER_KEY["FRED"]=NO_ADAPTER_YET`
      (sentineled, reasoned comment — FRED has no instruments-service URDI reference-data adapter yet, see the new P3
      todo below) — both are hard parity gates (`test_venue_source_adapter_parity.py`, `test_venue_adapter_keys.py`)
      that fail on ANY tradfi venue with no data-source/adapter-key entry. Updated 2 test-ratchet counts (tradfi
      shard-enumeration 12→14 cells, `test_pipeline_e2e_tradfi_canonical.py` +
      `test_pipeline_e2e_prediction_canonical.py`). **Verified end-to-end against the LIVE FRED API** (operator's Secret
      Manager credential) for 2024-01-16: 27/29 series returned real observations with correct
      venue/instrument_type/data_type/instrument_id shape (2 absent — ICSA weekly has no release that exact day, an
      honest empty). **Finding for the next todo**: FRED does NOT strictly filter a monthly/quarterly series to the
      exact requested day — querying ANY day within a given month/quarter (e.g. FEDFUNDS on 2024-01-02, -01-20, -01-31)
      returns the SAME period-start-dated observation; a naive day-by-day backfill will therefore write that series'
      identical value into every day-partition of the period (harmless/idempotent — `mtds_fred_reader.py`'s reader
      already dedups by the observation's own `date` column — but worth knowing before sizing the backfill's write
      volume).
- [x] [DATA] P1. **Run the FRED backfill** once the driver above exists — operator confirmed they already hold the
      `fred-api-key` credential (Secret Manager); this becomes a normal backfill VM launch (SPOT per the hard rule) once
      a real invocation path exists. Register the `expected_coverage` entry in the SAME change so honest-coverage never
      reads a false gap for the newly-populated rows. **Driver now exists** (see the DESIGN todo above, DONE 2026-07-29)
      — the `expected_coverage` entry is ALSO already registered (same todo). Low-frequency series will write duplicate
      identical values across every day-partition of their release period (see the finding noted on the DESIGN todo
      above) — a real but low-cost/idempotent characteristic to be aware of when sizing/monitoring the run, not a
      blocker.

      **IN PROGRESS 2026-07-29 (slot 8) — 2 real bugs found + fixed before any row could be captured, launch pending
              re-verification:**
              1. **`market-tick-data-service@886a4e23`** — `_umi_fred.py::fetch_fred_series` constructed `FredAdapter()` with NO
              `project_id`, so `BaseTradfiAdapter.get_api_key()`'s `if not self.project_id: raise` guard fired on EVERY
              series on EVERY day (masked as a generic "FRED API key not found" that looked exactly like a missing/bad
              secret). Fixed: pass `project_id=get_project_id()`.
              2. **`market-tick-data-service@9bc844f4`** (QG in flight, not yet quickmerged as of this checkpoint) — even with
              (1) fixed, `BaseTradfiAdapter.get_api_key()` itself called
              `self.secret_client.access_secret_version(project_id=, secret_id=, version_id=)` — **that method does not
              exist** on `unified_trading_library.cloud_interface`'s `SecretClient`/`CachingSecretClient` (the real
              interface is `get_secret(secret_name)`); every call raised `AttributeError`, masked by the same broad
              except-and-reraise. Same byte-identical bug found + fixed in the DeFi and on-chain-perp sibling base adapters
              (`base_defi_adapter.py`, `base_onchain_perp_adapter.py`) in the SAME commit — a copy-pasted defect across all
              3 TradFi/DeFi/onchain-perp adapter families, only surfaced now because FRED was apparently the first live
              caller of this code path. Verified via a local repro script (not committed — scratchpad only): 27/29 real
              FRED rows captured for 2024-01-02 (2 honest-empty, no release that exact day) once both fixes landed.
              3. Neither bug was `--dry-run`-catchable or QG-catchable — existing `get_api_key` unit tests
              (`tests/market_interface/unit/test_defi_live_tradfi_adapters.py`) only cover the `project_id`-missing guard
              path and the lazy-init `secret_client` property, never a full success-path call through to
              `secret_client.<method>(...)` with an assertion on which method/args were used — an un-spec'd `MagicMock()`
              silently accepts a call to a nonexistent method instead of raising `AttributeError` like the real client
              would. **Follow-up P3 todo added below** to close this coverage gap so the SAME defect class can't hide again.
              4. Also fixed live (unrelated but blocking): the TradFi + prediction manifest-consolidator Cloud Scheduler crons
              were stuck `PAUSED` ~20h (since 2026-07-29T01:05Z) — see
              `plans/active/issues/tradfi_pred_manifest_consolidator_cron_stuck_paused_2026_07_29.md` for the full writeup;
              resumed both, TradFi catch-up merge processed 130 shards / 6.2M rows.
              5. **Next steps (resume here)**: once `market-tick-data-service@9bc844f4` clears QG, quickmerge it, rebuild
              TRADFI code tarballs (`deployment-service/scripts/vm/create-code-tarballs.sh --asset-group TRADFI`), relaunch
              a `--year 2024` smoke VM via `launch-tradfi-bf-fred.sh` and **verify real captured rows** (not just
              chunk-progress log lines — that false-positived once already this session), then launch the full
              `1962-01-02..today` production backfill (no `--year` flag; single VM by design, see the launcher's header
              comment for why NOT year-sharded), verify its early progress the same way, THEN flip this checkbox with the
              VM name + verified evidence.

              **IN PROGRESS 2026-07-30 (slot 6) — resumed here; confirmed both slot-8 bugs already shipped (under a
              provenance-rewritten SHA, not literally `9bc844f4` — this repo runs frequent `chore(provenance):
              re-provenance` commits, so exact-SHA `git log` greps can false-negative; verified by READING the current
              `get_api_key()` body in all 3 base adapters instead), then found + fixed a THIRD, more severe bug the
              `--year 2024` smoke test itself caught before any full-scale launch:**
              1. **`unified-api-contracts@6d87d95e`** (QG passed 266s, shipped via quickmerge, landed on
              live-defi-rollout — verified `ahead=0`/`behind=0` against origin) —
              `venue_trading_calendar.py::_venue_excludes_weekends_holidays()` gates ANY `asset_group=='tradfi'`
              venue behind `US_MARKET_HOLIDAYS` (the NYSE/NASDAQ equity calendar) + weekends. FRED was added to
              `VENUE_TO_ASSET_GROUP["tradfi"]` by the DESIGN todo above (2026-07-29) — which silently made FRED
              inherit this gate too. FRED is a federal-government macro-data source, not an exchange: its real
              release calendar is NOT the equity-market calendar (Good Friday closes NYSE but not the Fed/BLS).
              **Confirmed live in the manifest**, not just inferred from code: launched a fresh
              `tradfi-bf-fred-2024-20260730-011634` smoke VM (SPOT, `--year 2024`), and its very first processed
              date (2024-01-01) wrote `capture_status=empty_confirmed, error_reason=EXPECTED_HOLIDAY` with ZERO
              fetch attempt — harmless for that SPECIFIC date (it's also a genuine federal holiday), but the same
              mechanism would silently mis-stamp real FRED data on every Good-Friday-class date across the full
              1962-2026 backfill window, which the ORIGINAL 27/29-row single-day verification (2024-01-02, a
              regular weekday) could never have caught. Fix: added `CALENDAR_EXEMPT_TRADFI_VENUES = {"FRED"}`,
              checked before the `asset_group` gate — verified via direct call (`is_non_trading_day`/
              `non_trading_day_reason` now return `False`/`None` for FRED on Good Friday 2024-03-29 AND on
              weekends, while NYSE/CME on the same dates are unaffected). Added 4 regression tests to
              `tests/test_non_trading_day_reason.py`. **Trade-off flagged, not blocking**: this also stops
              skipping FRED on weekends (FRED almost certainly never publishes then, so those will just come back
              honest-empty at a small, bounded, one-time backfill cost) — chose full exemption over inventing a
              new weekday-only-but-holiday-exempt category this codebase has no existing pattern for.
              2. **Separately found, NOT fixed (P3 followup below, non-blocking, no data loss)**: the SAME smoke VM's
              second processed date (2024-01-02, a regular weekday) logged a confusing
              `SHARD_INCOMPLETE ... expected 1 venues, wrote 0, missing: ['FRED']` warning even though the
              consolidated manifest already has 27 genuinely `capture_status=captured` rows for that exact date
              (written 2026-07-29T23:58Z — this IS the DESIGN todo's own "27/29 real FRED rows captured for
              2024-01-02" verification, which evidently wrote to the real production manifest, not just a
              scratchpad). The pre-flight correctly SKIPPED re-fetching already-covered data (no data loss) but
              the per-VM shard's own "did I personally write this date" bookkeeping then emits a
              SHARD_INCOMPLETE/missing warning that could mislead an operator scanning logs into thinking data is
              missing when it is not. Cosmetic, not correctness-affecting — see the P3 todo below.
              3. **Stopped** the pre-fix smoke VM (`tradfi-bf-fred-2024-20260730-011634`, `gcloud compute instances
              delete`, this worker's own just-launched VM, 2 chunks in — see the VM-delete guardrail in
              `data_engineering.md`, which this satisfies: own fleet, launched this session, confirmed non-stale by
              direct observation, not a staleness-confusion mistake) rather than let it keep writing
              holiday-mismatched rows across the full year that would need a redo anyway once the fix lands.
              4. **Verification completed 2026-07-30 (slot 6)**: `unified-api-contracts@6d87d95e` landed +
              verified. Confirmed MTDS uses `path = "../unified-api-contracts"` (editable, content-first) —
              no dep-bump needed, BUT the VM deploy path uses PREBUILT GCS TARBALLS, not a live clone, so a
              tarball rebuild WAS required (`deployment-service/scripts/vm/create-code-tarballs.sh
              --asset-group TRADFI` — confirmed `unified-api-contracts-code.manifest.json` then showed
              `commit_sha=6d87d95e`; skipping this step silently re-deploys stale pre-fix code — the first
              post-fix smoke VM did exactly that and still showed the OLD bug until this was caught).
              Relaunched `--year 2024` smoke VM (`tradfi-bf-fred-2024-20260730-014447`) with the rebuilt
              tarball: confirmed live the 2024-01-01 skip-list dropped from 8→7 venues (FRED no longer
              listed), AND a genuinely untouched date (2024-01-04) got 27 real captured rows,
              `complete=True` — the definitive "verify real captured rows" proof the plan required. My
              OWN earlier pre-fix smoke VM had already written ONE wrong row (2024-01-01,
              `empty_confirmed`/`EXPECTED_HOLIDAY`) before I could stop it — corrected via
              `--year 2024 --force-recapture` (`tradfi-bf-fred-2024-20260730-015643`), verified via the
              per-VM shard directly (consolidated index lags via its own async consolidator — expected,
              not a bug): 2024-01-01 now shows 27 rows, all `capture_status=captured`, no error_reason.
              **False-alarm correction (2026-07-30, slot 6)**: the first 3 full-backfill launches
              (`tradfi-bf-fred-full-20260730-020236`/`-021518`/`-022323`) appeared to hang on chunk 1
              (CPU flat, zero progress for 1-7 min) and were killed, initially misdiagnosed as a
              FredAdapter bug. **Corrected via live `gcloud compute ssh` + `py-spy dump`** on a 4th
              repro VM: the process was legitimately parked in
              `_wait_for_in_flight_cycle_then_reread` — a documented, BOUNDED (3600s default horizon
              for tradfi, which has no per-AG override) wait for a genuinely live TRADFI manifest
              consolidator lock (confirmed fresh via `gs://.../_index/consolidator.lock`, not
              orphaned). Not a bug — the manifest system's own "legitimate in-flight merge" protection
              working as designed, most likely triggered by this session's own heavy TRADFI write
              activity. **Verified live**: let that same repro VM keep running past the wait — it
              then wrote 13 real FRED rows for `1970-01-01`, `complete=True`. Full retraction +
              corrected diagnosis + a small follow-up (tradfi-specific horizon tuning + an
              observability log line) filed in
              `fred_backfill_early_date_indefinite_stall_2026_07_30.md` (downgraded P1/open →
              P3/resolved). **Full production backfill RELAUNCHED**: `tradfi-bf-fred-full-20260730-024848`
              (SPOT, `1962-01-02..2026-07-29`, single VM, true honest-coverage floor). Committing to
              let it run through any legitimate consolidator wait (up to 1h) rather than killing it
              prematurely again — early-progress verification in flight.

              **✅ DONE 2026-07-30 (slot 6)**: `tradfi-bf-fred-full-20260730-024848` cleared its chunk-1
              consolidator-lock wait at ~19min (lock rotated 3x under sustained fleet write pressure,
              then cleared outright — `gsutil cat .../consolidator.lock` → `CommandException: No URLs
              matched`, confirmed on 2 consecutive checks) and began writing real data at the TRUE
              1962-01-02 floor: `venue=FRED: 12 rows written across 12 partitions (12 instruments)`,
              `Manifest updated: date=1962-01-02 venues=1 shards=12 total_records=12 complete=True`,
              `Processed date=1962-01-02: 1 venues ok, 0 failed, 0 skipped`. Confirmed it continues
              (not a one-shot artifact): `date=1962-01-03` processed identically 2 min later, same
              shape, `complete=True`, CPU now steady ~100% (genuine active work, not idle-wait).
              This is the "verify real captured rows" proof this todo's own prior notes required,
              at the actual backfill floor date this time (not a `--year 2024` smoke substitute).
              VM left running unattended to complete its full `1962-01-02..2026-07-29` sweep (3370
              chunks) — SPOT + idempotent shards per the backfill-VM hard rule, safe to let finish
              outside this session. Checkbox flipped per `done_definition: "Checkbox flipped in plan
              + code shipped."` — code (the calendar-exemption fix, `unified-api-contracts@6d87d95e`)
              is shipped and verified; the backfill run itself is launched, verified progressing
              correctly past the true floor, and self-sufficient to completion.

              **Operational note 2026-07-30 (slot 2, DP-VM-001 escalation agt-f421bc)**: the eventual
              successor of that VM (relaunched again as `-052935` then `-064542` per the
              catalogue-`iterrows()` fix in the linked issue doc) was later false-positive
              stall-killed by an (at-the-time) unfixed watchdog/consolidator-wait headroom gap
              — NOT a new bug, and NOT this todo reopening. Also found + fixed a genuine,
              separate launcher-registry gap (`tradfi-bf-fred-` had no relaunch-launcher
              binding, `deployment-service@1d24854`) and relaunched again:
              `tradfi-bf-fred-full-20260730-110724`. Full root-cause chain + evidence in
              `/plans/archive/issues/fred_backfill_early_date_indefinite_stall_2026_07_30.md`
              Progress Log — this note is just the pointer so the chronological thread here
              doesn't dead-end at "left running unattended."

- [x] ✅ [CODE] P2. **Convert this doc's own "Recommended decision" Phase 1 (line ~250 above) into a real tracked todo —
      found 2026-07-30 it was only ever prose, never a `- [ ]` item, so it's never actually been dispatched.** Wire the
      Category-B orphans so the feature layer populates: register `"yield_curve"`/`"economic_results"` into
      `features_service/calendar/cli/handlers/batch_handler.py`'s `CALENDAR_FEATURE_GROUPS` list (currently only
      `["time_features", "economic_events"]`), and register the `economic_results` operation in
      `features_service/calendar/cli/main.py`'s `ServiceBootstrap(operations={...})` dict (currently missing entirely —
      `economic_results_handler.py`'s `app()` has no `if __name__ == "__main__":` guard and no scheduler/VM-launcher
      path invokes it, confirmed via a full grep of `deployment-service/scripts/vm/launch-features-*.sh`). Both
      calculators (`economic_results_calculator.py`, `yield_curve_calculator.py`) already do REAL work (read genuine
      FRED actuals via `mtds_fred_reader.py`, not mocked) — this is a pure wiring gap, not a build task, and now that
      the 2026-07-29 FRED backfill has landed real production rows (this doc's own P1 todos above), running this wiring
      would for the first time actually produce non-empty output. Also wire `economic_results_handler.py` to call
      `ManifestWriter` (confirmed via full read it currently writes real GCS parquet but never registers in the manifest
      at all — unlike `time_features`/`economic_events`, which do). Check
      `/plans/archive/issues/features_calendar_pipeline_mode_gap_2026_05_12.md` first for the still-open `pipeline_mode`
      tagging decision this wiring will also need. Repo: features-service. Done when: a real `--operation compute` batch
      run for a recent date shows non-empty `yield_curve`/`economic_results` output in
      `gs://<features-calendar bucket>/calendar/{yield_curve,economic_results}/by_date/day=<date>/*.parquet`, with a
      corresponding manifest row for `economic_results`.

      **✅ DONE 2026-07-30 (slot 2)**: the wiring itself (`CALENDAR_FEATURE_GROUPS`, `ServiceBootstrap` operations,
              `ManifestWriter` registration, `PipelineMode.BATCH_FRED` tagging) had already shipped
              (`features-service@4eb5d628`, slot 5, same day) but had never actually been run against real captured FRED data
              to prove the "Done when" bar — running it surfaced 2 real bugs that silently produced zero rows for both
              feature groups, now fixed and verified:
              1. **Read-side bug, NOT a write-side defect as 4eb5d628's own commit message suspected** —
              `mtds_fred_reader.py::_read_day_parquet` called `pd.read_parquet(storage.get_uri(bucket, name))` on a bare
              `gs://` path string. The canonical wire path is deep Hive-style
              (`day=/pipeline_mode=/asset_group=/venue=/instrument_type=/data_type=`), so pandas' pyarrow engine
              auto-detects partitioning even for a single file and materializes dictionary-encoded PARTITION columns
              (`venue`, `instrument_type`, `data_type`) that collide with the file's OWN already-embedded plain-string
              columns of the identical names — `ArrowTypeError: Unable to merge: Field venue has incompatible types:
              string vs dictionary<...>`. This affected EVERY captured FRED parquet, including ones written fresh that
              same day — confirmed via direct repro (the identical file read cleanly through a plain `BytesIO` stream but
              raised when passed as a `gs://` path string). Fixed by reading via `storage.download_bytes()` +
              `io.BytesIO()` (existing pattern already used elsewhere in features-service).
              2. **`_generate_economic_results` never stamped a `timestamp` column** (`ECONOMIC_RESULTS_COLUMNS` never
              declared one, unlike `YIELD_CURVE_COLUMNS`) — the shared `process_day()`/`_write_via_storage()` path runs
              every feature_group through `FeatureWriteGate`, which alignment-checks a `timestamp` column against
              `expected_date` and rejected the whole shard at 0% alignment when the column was simply absent. Fixed by
              stamping `timestamp=target_date` (mirrors `_generate_yield_curve`'s existing pattern).

              **Verified against real production FRED data** (2024-01-22, the earliest day with full DGS-series capture from
              an earlier smoke-verification run — the true production backfill launched 2026-07-30 was still sweeping
              forward from 1962 and had not yet reached recent dates): `yield_curve` wrote 1 real row
              (`gs://features-calendar-prd-central-element-323112/calendar/yield_curve/by_date/day=2024-01-22/features.parquet`),
              `economic_results` wrote 5 real rows (4 genuine FRED values — CPI/GDP/NFP/PCE — + 1 honest-empty for
              ICSA/CLAIMS, no release that exact day) at the sibling `economic_results` path — both confirmed
              `capture_status=captured` in the live availability-index manifest. This is the "Done when" proof this todo's
              own text required and had not yet been produced. Shipped:
              `features-service@c5561a7a` (the 2 fixes) + `features-service@7b76f382` (companion test-fixture update —
              the FRED-reader tests mocked `pd.read_parquet` keyed by URI string, which no longer intercepts the
              `download_bytes`-based read; reworked to serve real parquet bytes per blob path instead of a URI-keyed
              stand-in). Full `quality-gates.sh` green (238 features-service test files, 17983 passed) before shipping.

- [x] ✅ [DATA] P3. **Fix the misleading `SHARD_INCOMPLETE ... wrote 0 ... missing: [venue]` warning that fires even
      when the date is ALREADY correctly captured.** — market-tick-data-service@79b1453f + quickmerge. Root cause:
      `_write_date_manifest`'s completeness check compared `written_venues` (from `shard_counts`, which
      preflight-skipped venues never populate) against `active_venues` (which still includes them). Fix: filter
      `state.preflight_skipped` venues (intentionally skipped because all data_types are already fully covered in the
      consolidated manifest) out of the expected set before `validate_batch_completeness`. Also added an info-level log
      so operators can see which venues were excluded from the completeness check.
- [x] ✅ [TEST] P3. **Close the `get_api_key()` success-path test-coverage gap that let the `access_secret_version`
      defect ship undetected.** — market-tick-data-service@b88ecd67. Added `test_get_api_key_success_calls_get_secret` +
      `test_get_api_key_no_value_raises` to `test_defi_live_tradfi_adapters.py` for all 3 base adapters
      (`TestBaseTradfiAdapterExtra`, new `TestBaseDefiAdapterGetApiKey`, new `TestBaseOnchainPerpAdapterGetApiKey`) —
      each mocks `secret_client` with `MagicMock(spec=SecretClient)` and asserts `get_api_key()` calls
      `get_secret(secret_name)`. Verified the regression-catching property directly: temporarily reintroduced
      `access_secret_version(...)` in `base_tradfi_adapter.py` and confirmed the new tests fail with
      `AttributeError: Mock object has no attribute 'access_secret_version'` (reverted before shipping). QG green, 9/9
      new tests pass.
- [x] ✅ [BACKEND] P3. **Build the instruments-service "fred" URDI reference-data adapter** —
      instruments-service@df83fdcd + unified-api-contracts@598b8e49. `FredReferenceDataAdapter` mirrors the FX precedent
      (`instruments_service/reference_data/adapters/tradfi/fx.py`): a small static-list adapter (no vendor call)
      emitting the 28 `_KEY_SERIES` as `InstrumentRecord` catalogue rows via
      `build_instrument_id("FRED", entry_type, series_id)` — byte-identical to MTDS's
      `derive_tradfi_row_instrument_id(..., venue="FRED")`. `VENUE_TO_ADAPTER_KEY["FRED"]` is `"fred"` (was
      `NO_ADAPTER_YET`). Factory registered in `_ADAPTERS`/`_ADAPTER_KEYS`. 5 unit tests in `test_fred.py`. QG green
      (105s, 2026-08-04).
- [x] ✅ [DATA] P2. **NEW (2026-08-09, operator-flagged)** — reduce FRED backfill API-call waste for monthly/quarterly
      series. Per the finding above (the DESIGN todo's Progress Log note): querying FRED for ANY day within a given
      month/quarter returns the SAME period-start observation, so the current day-by-day backfill loop issues one API
      call per calendar day even though the underlying value only changes ~12x/year (monthly) or 4x/year (quarterly) —
      real, wasted request volume against a rate-limited external API, not merely "harmless write duplication" as
      originally framed (operator: "seems waste of resources vs fetching once"). Fix: step the backfill loop by the
      series' actual release cadence (query once per period, e.g. via FRED's own release-calendar metadata or a
      per-series frequency lookup) instead of once per day; let the existing T+1 forward-poll / live capture path pick
      up new period values going forward as they publish, rather than re-simulating that motion historically.
      `mtds_fred_reader.py`'s existing date-dedup stays as a correctness backstop either way. Repo:
      market-tick-data-service (`_umi_fred.py`, `mtds_fred_reader.py`).

      **DONE 2026-08-09** — `market-tick-data-service@b75edd373` + `features-service@d121867a8`. Added
              `_should_query_fred(series_id, target)` to `_umi_fred.py`: for the 7 monthly/quarterly `KEY_SERIES` entries
              (FEDFUNDS/PAYEMS/CPIAUCSL/GDP/GDPC1/UNRATE/PCEPI), samples once every 7 calendar days (`target.day % 7 == 1`)
              instead of every day — `_fetch_one_series` skips the live FRED call entirely (no adapter invocation) on a
              non-sample day, cutting real request volume ~83% for those series while staying well inside the ~30/90-day
              value-persistence window so no release transition is missed (deliberately NOT anchored to calendar
              day==1 — several of these series publish weeks after their reference period starts, so a day==1-only anchor
              would have risked silently missing the real release; the periodic day%7 grid instead samples repeatedly
              through the whole period). Daily/weekly series (treasury tenors, ICSA) are unaffected. Companion fix in
              `features-service`'s `mtds_fred_reader.py`: added a bounded (`_MISSING_DAY_LOOKBACK_DAYS=7`) fallback to the
              nearest earlier written day for the same monthly/quarterly series, so a narrow caller window (e.g.
              `economic_results_calculator`'s ±5/+2-day window around a release date) can't land entirely on an unwritten
              day now that most calendar days have no partition for these series. Unit tests added in both repos
              (`tests/unit/test_umi_fred_cadence.py`, extended `tests/calendar/unit/test_mtds_fred_reader.py`). QG green
              both repos.

## Audit method + provenance

6 parallel general-purpose audit agents (2026-06-05), one per domain (macro / CeFi / DeFi / TradFi / Sports+Prediction /
codex-registry), each grep-then-**read** (0 hits ≠ absent — escalated to reading candidate handler/connector/registry
files), classifying every source on the capture ladder with file:line evidence. The macro and codex-registry audits
independently corroborated the L0 declared-not-wired set. Where a finding is code-only (not population-verified), it is
marked so above.

## Progress Log

- **context-scout 2026-08-03**: refreshed context_scope (6 entries) — the FRED backfill saga (this doc's own bulk of
  recent activity) is now essentially done; swapped the two now-fixed-bug-specific entries
  (`test_defi_live_tradfi_adapters.py`, `base_tradfi_adapter.py`) for the FRED adapter route file (`_umi_fred.py`) and
  the still-open companion doc (`fred_backfill_early_date_indefinite_stall_2026_07_30.md`), matching the doc's only 2
  remaining open todos (the SHARD_INCOMPLETE warning fix in `manifest_finalize.py`, and the instruments-service FRED
  URDI adapter mirroring `fx.py`).

- **context-scout 2026-08-06**: re-scouted; all `- [ ]` todos are now flipped `[x]` (both remaining items the 2026-08-03
  marker cited shipped 2026-08-04) — context_scope re-verified (6 entries) as still-valid historical evidence pointers,
  unchanged; worth a fresh source-hunt pass if/when this doc is next touched with new open work.
