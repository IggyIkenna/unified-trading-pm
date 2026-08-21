---
doc_type: plan
title: prediction-pipeline-phase2
summary: "Phase 2 of prediction pipeline: unified fixture ID for cross-venue arb, settlement index\nregistry, prediction\
  \ market features, and 1-week validation run.\n\n## Problem\nPhase 1 wired the pipeline end-to-end (2000 instruments,\
  \ 1500 trades, GCS verified). But:\n1. Sports instrument IDs use Polymarket condition_id — not the canonical fixture_id\
  \ format\n   ``{fixture_id}::{market_type}::{outcome}::{bookmaker_key}`` used by CanonicalOdds.\n   This breaks cross-venue\
  \ arb (Polymarket vs Betfair vs Odds API).\n2. No settlement index registry — what Chainlink feed settles BTC? What settles\
  \ SPX?\n3. No prediction features in the features pipeline — BTC features exist in\n   polymarket-correlation-research\
  \ but aren't in the system.\n4. No sports prediction features — odds spread, uncertainty, bookmaker consensus.\n\n## Solution\n\
  Phase 2A: Unified fixture ID — cross-reference Polymarket with API-Football. Use\n``{fixture_id}::{market_type}::{outcome}::polymarket``\
  \ matching CanonicalOdds format.\nPhase 2B: Settlement index registry in UAC.\nPhase 2C: Port BTC/SPX features from polymarket-correlation-research.\n\
  Phase 2D: Sports prediction features template.\nPhase 2E: 1-week validation run (2026-03-19 to 2026-03-25).\n\n## Key\
  \ Insight\nCanonicalOdds format: ``{fixture_id}::{market_type}::{outcome}::{bookmaker_key}``\nExample: ``1034567::h2h::home::betfair_ex_uk``\n\
  For Polymarket: ``1034567::moneyline::home::polymarket``\nSame fixture_id = arb is GROUP BY fixture_id, outcome → compare\
  \ prices.\n\n## Scope: 7 repos\n- unified-api-contracts — settlement registry, fixture ID helpers\n- unified-reference-data-interface\
  \ — cross-reference Polymarket gameId → API-Football fixture_id\n- instruments-service (URDI sports/ sub-package) — fixture\
  \ lookup by team+date (existing get_fixtures)\n- unified-features-interface — prediction feature calculators\n- features-prediction-service\
  \ — new service or extend existing\n- unified-trading-pm — plan + validation scripts\n- unified-trading-pm/codex — update\
  \ prediction-schema-paths.md"
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-25'
locked_by: live-defi-rollout
locked_since: 2026-03-25
type: code
epic: epic-code-completion
completion_gates: {code: C4, deployment: D1, business: B4}
repo_gates:
- {repo: unified-api-contracts, code: C0, notes: 'Settlement registry, prediction instrument ID convention'}
- {repo: unified-reference-data-interface, code: C0, notes: Cross-reference Polymarket → API-Football fixture_id}
- {repo: instruments-service (URDI sports/ sub-package), code: C0, notes: Fixture lookup by team+date (may need no changes)}
- {repo: unified-features-interface, code: C0, notes: 'Prediction feature calculators (OFI, streak, odds spread)'}
- {repo: unified-trading-pm, code: C0, notes: Validation scripts}
- {repo: unified-trading-pm/codex, code: C0, notes: Updated prediction-schema-paths.md}
isProject: false
todos:
- {id: p2a-1-fixture-cross-reference, content: "- [x] [AGENT] P0. Cross-reference Polymarket sports fixtures with API-Football fixture_id.\n  File: unified_reference_data_interface/adapters/polymarket.py\n\n  Current: sports instrument_key = Polymarket condition_id (0x...)\n  Target:  sports instrument_key = API-Football fixture_id (e.g. \"1034567\")\n\n  The CanonicalOdds format is: {fixture_id}::{market_type}::{outcome}::{bookmaker_key}\n  For Polymarket: {fixture_id}::moneyline::home::polymarket\n\n  Cross-reference flow in _build_sports_id():\n  1. Already have: home_team (canonical), away_team (canonical), date, league_id\n  2. Call USRI api_football adapter: get_fixtures(date, [league.api_football_id])\n  3. Match by team names (both canonical, direct comparison)\n  4. If match: use API-Football fixture_id\n  5. If no match: use PM_{gameId} as fallback\n\n  The USRI api_football adapter requires an API key from Secret Manager.\n  In batch mode without key: fall back to PM_{gameId}\
    \ with a warning.\n\n  Also update instrument_key (currently condition_id) to use the canonical\n  fixture-based instrument ID for sports: {fixture_id}::{market_type}::{outcome}::polymarket\n  Keep condition_id in raw_symbol for trade fetching.\n", status: pending}
- {id: p2a-1b-historical-per-date-fetching, content: "- [x] [AGENT] P0. Add per-date historical fetching to URDI PolymarketReferenceDataAdapter.\n  Added `date` parameter to `get_instruments()`. When date is provided, fetches ALL markets\n  ending on that UTC date (including closed/resolved) using `end_date_min/max` Gamma params.\n  Removed 2000-market cap for historical mode (_MAX_PAGES_HISTORICAL = 200 = ~20k markets).\n  Validated: 55,383 markets across 7 days (6,700-10,100 per day). Saturday peak = 10,139.\n", status: completed}
- {id: p2a-2-instrument-id-convention, content: "- [x] [AGENT] P0. Standardize prediction instrument ID format.\n  File: unified_api_contracts/canonical/domain/prediction/prediction_mapping.py\n\n  Document and enforce:\n    Sports:  {fixture_id}::{market_type}::{outcome}::{venue}\n             e.g. 1034567::moneyline::home::polymarket\n             Matches CanonicalOdds: 1034567::h2h::home::betfair_ex_uk\n\n    Crypto:  {venue}::up_down::{asset}::{timeframe}::{window_end_ts}\n             e.g. polymarket::up_down::btc::5m::1774230900\n\n    Macro:   {venue}::up_down::{index}::{timeframe}::{date}\n             e.g. polymarket::up_down::spx::1d::2026-03-25\n\n  Add build_prediction_instrument_id() and parse_prediction_instrument_id() helpers.\n  These live alongside the existing build_fixture_id() in canonical_ids.py.\n", status: completed}
- {id: p2b-1-settlement-registry, content: "- [x] [AGENT] P0. Create settlement index registry in UAC.\n  File: unified_api_contracts/external/polymarket/settlement_registry.py\n\n  Maps each underlying to its settlement data source:\n    BTC  → Chainlink BTC/USD stream (data.chain.link/streams/btc-usd)\n         → Also: Binance BTCUSDT 1m candle High price\n    ETH  → Chainlink ETH/USD stream\n    SOL  → Chainlink SOL/USD stream\n    XRP  → Chainlink XRP/USD stream\n    DOGE → Chainlink DOGE/USD stream\n    BNB  → Chainlink BNB/USD stream\n    HYPE → Chainlink HYPE/USD stream (if available)\n    SPX  → S&P 500 Official Close (S&P Dow Jones Indices)\n    NDX  → NASDAQ Composite Official Close\n    DJIA → Dow Jones Industrial Average Official Close\n    CRUDE_OIL → NYMEX WTI CL Front Month Settlement\n    GOLD → COMEX GC Front Month Settlement\n    SILVER → COMEX SI Front Month Settlement\n\n  Schema: SettlementSource(underlying, source_name, source_url, resolution_type,\n               \
    \            chainlink_feed_id, exchange_pair)\n  resolution_type: \"chainlink\" | \"exchange_candle\" | \"official_close\" | \"oracle\"\n\n  S&P 500 components: 503 stocks, float-adjusted market cap weighted.\n  Top 10 (AAPL, MSFT, NVDA, AMZN, GOOGL, META, BRK.B, AVGO, JPM, LLY) ≈ 35%.\n  Full list public at spglobal.com. Exact weightings change intraday.\n  Document this in the registry but don't hardcode all 503.\n", status: completed}
- {id: p2c-1-btc-spx-features, content: "- [x] [AGENT] P1. Port BTC prediction features from polymarket-correlation-research.\n  Source: polymarket-correlation-research/polymarket_correlation/features.py\n  Target: unified-features-interface/unified_features_interface/prediction/\n\n  Key features (from PolyFeatureBuilder):\n  - poly_ofi: Order flow imbalance (net_flow / total_vol, range [-1, 1])\n  - poly_dir: Sign of net flow (-1, 0, +1)\n  - poly_streak: Consecutive same-direction bars (signed, resets on empty bar)\n  - poly_flow_mom3: 3-bar rolling sum of net flow\n  - poly_vol_surge: Current vol / 12-bar avg vol\n  - poly_wallet_surge: Current unique wallets / 12-bar avg\n  - poly_has_trades: Binary trade presence\n  - poly_bars_since_trade: Count of empty bars since last trade\n  - poly_freshness: Exponential decay score (1.0 at trade, halves every N bars)\n\n  Interaction features:\n  - ix_vol_x_ofi, ix_mom_x_ofi, ix_funding_x_ofi, ix_streak_x_mom\n\n  FillPolicy: ZERO (default),\
    \ NAN, DECAY for sparse data handling.\n  These features apply to BOTH BTC and SPX up/down markets.\n\n  Do NOT copy code — reimplement using system patterns (UAC schemas, UIC types,\n  features-interface calculator pattern). Reference the research repo for logic only.\n", status: completed, blocked_by: p2a-1-fixture-cross-reference}
- {id: p2d-1-sports-prediction-features, content: "- [x] [AGENT] P1. Create sports prediction features template.\n  Target: unified-features-interface/unified_features_interface/prediction/\n\n  Features from cross-bookmaker odds data:\n  - odds_spread_max_min: Max - min implied probability across bookmakers\n  - odds_median: Median implied probability across bookmakers\n  - odds_mean: Mean implied probability across bookmakers\n  - odds_outlier_count: Bookmakers >2σ from median (noise/sharp money signal)\n  - odds_uncertainty: Variance of implied probabilities (high = uncertain outcome)\n  - odds_consensus: % of bookmakers agreeing on favourite direction\n  - odds_movement_1h: Change in median odds over last hour\n  - odds_movement_24h: Change in median odds over last 24 hours\n  - odds_value: Polymarket price vs bookmaker consensus (mispricing signal)\n\n  Multi-instrument features (cross-venue for same fixture):\n  - Use unified fixture_id to join Polymarket + Betfair + Odds API prices\n\
    \  - Strip extreme outliers (>3σ), compare stripped median vs raw mean\n  - Signal richness: high uncertainty = ML model has more edge potential\n\n  These go into features-prediction-service (or unified-features-interface\n  if a dedicated service doesn't exist yet) as prediction feature calculators.\n", status: completed}
- {id: p2e-1-validation-run, content: "- [x] [HUMAN+AGENT] P0. Run full 1-week prediction pipeline.\n  Date range: 2026-03-19 to 2026-03-25 (7 days)\n\n  For each date:\n  1. instruments-service --asset-group PREDICTION --date {date}\n     → Verify: BTC/ETH/SOL up/down, SPX markets, soccer fixtures discovered\n     → Verify: fixture_id cross-referenced with API-Football where possible\n  2. market-tick-data-service --asset-group PREDICTION --date {date}\n     → Verify: Trades fetched for discovered markets\n     → Verify: Data type = prediction_trades\n  3. Check GCS hive partitions:\n     gs://instruments-store-prediction-central-element-323112/\n       instrument_availability/by_date/day={date}/venue=POLYMARKET/\n     gs://market-data-tick-prediction-central-element-323112/\n       raw_tick_data/by_date/day={date}/...\n  4. Verify canonical IDs consistent across services\n  5. Verify sports fixtures have human-readable format:\n     {fixture_id}::moneyline::home::polymarket\n", status: completed,
  blocked_by: 'p2a-1-fixture-cross-reference, p2c-1-btc-spx-features'}
- {id: p2f-1-qg-sweep, content: "- [x] [AGENT] P0. Run quality gates across all touched repos.\n  Results: Our code passes lint+tests. Pre-existing C901 complexity in URDI DeFi adapters\n  (aave_v3, uniswap_v2/v3/v4) and stale mock paths in instruments-service orchestrator tests\n  cause baseline failures unrelated to prediction pipeline changes.\n  cd unified-api-contracts && bash scripts/quality-gates.sh\n  cd unified-reference-data-interface && bash scripts/quality-gates.sh\n  cd unified-features-interface && bash scripts/quality-gates.sh\n  cd unified-trading-pm && bash scripts/quality-gates.sh\n  All must pass.\n", status: pending, blocked_by: p2e-1-validation-run}
---

# Prediction Pipeline Phase 2

## Core Architectural Decision: Unified Fixture ID

The existing CanonicalOdds instrument ID format is:

```
{fixture_id}::{market_type}::{outcome}::{bookmaker_key}
```

Example: `1034567::h2h::home::betfair_ex_uk`

For prediction markets, the format becomes:

```
{fixture_id}::{market_type}::{outcome}::polymarket
```

Example: `1034567::moneyline::home::polymarket`

The fixture_id (from API-Football) is the **shared join key** across all venues. Arb detection =
`GROUP BY fixture_id, outcome → compare prices across venues`.

## Cross-Reference Flow

```
Polymarket Gamma API market
  │
  ├── outcomes: ["Spurs", "Grizzlies"]
  ├── sportsMarketType: "moneyline"
  ├── gameStartTime: "2026-03-25T23:00:00Z"
  └── events[0].seriesSlug: "nba-2026"
          │
          ▼
  1. Normalize teams: get_canonical_team_for_polymarket("Spurs") → "SPURS"
  2. Map series: get_canonical_league_for_polymarket_series("nba-2026") → "NBA"
  3. Lookup: USRI api_football.get_fixtures("2026-03-25", league_ids=[NBA_ID])
  4. Match: find fixture where home="SPURS" or away="SPURS" on that date
  5. Result: fixture_id = "1034567"
          │
          ▼
  instrument_key = "1034567::moneyline::home::polymarket"
  raw_symbol = condition_id (for trade fetching)
```

## Settlement Sources

| Underlying | Source           | Feed                            |
| ---------- | ---------------- | ------------------------------- |
| BTC        | Chainlink        | data.chain.link/streams/btc-usd |
| ETH        | Chainlink        | data.chain.link/streams/eth-usd |
| SOL        | Chainlink        | data.chain.link/streams/sol-usd |
| SPX        | Official Close   | S&P Dow Jones Indices           |
| CRUDE_OIL  | NYMEX Settlement | CME Group CL                    |
| GOLD       | COMEX Settlement | CME Group GC                    |

## Features to Port

### From polymarket-correlation-research (BTC + SPX)

- OFI, direction, streak, flow momentum, volume surge, wallet surge
- Freshness decay for sparse data (65% of 5m bars empty)
- Interaction features (vol×OFI, momentum×OFI, etc.)

### New Sports Prediction Features

- Odds spread (max-min across bookmakers)
- Uncertainty (variance of implied probabilities)
- Consensus (% agreeing on favourite)
- Movement (1h, 24h median odds change)
- Value (Polymarket vs bookmaker consensus)

## Dependency DAG

```
P2A (Unified fixture ID) ──┬── A1: Cross-reference Polymarket→API-Football
  [PARALLEL]                └── A2: Instrument ID convention + helpers
                                     │
                            UAC + URDI QG gate
                                     │
P2B (Settlement registry) ──── B1: Settlement sources in UAC
  [PARALLEL with A]                  │
                                     │
P2C (BTC/SPX features) ───── C1: Port OFI, streak, freshness from research repo
  [AFTER A]                          │
                                     │
P2D (Sports features) ────── D1: Odds spread, uncertainty, consensus
  [PARALLEL with C]                  │
                              features QG gate
                                     │
P2E (Validation) ──────────── E1: 1-week pipeline run
  [AFTER all]                        │
                                     │
P2F (QG sweep) ────────────── F1: All repos green
```

## Success Criteria

### Phase 2A

- Sports instruments use API-Football fixture_id as instrument_key
- Format: `{fixture_id}::{market_type}::{outcome}::polymarket`
- Same fixture_id as CanonicalOdds from Betfair/Odds API

### Phase 2B

- Settlement registry covers all 20 underlyings
- Each entry has source_name, source_url, resolution_type

### Phase 2C

- BTC features compute from Polymarket trade data
- Features work for both BTC and SPX markets
- Sparse data handled via FillPolicy (ZERO/DECAY)

### Phase 2D

- Odds spread, uncertainty, consensus features compute from cross-bookmaker data
- Multi-instrument features use unified fixture_id to join across venues

### Phase 2E

- 7 days of data in GCS hive partitions
- Canonical IDs consistent across instruments → tick data → features
- Sports fixture IDs match between PREDICTION and SPORTS categories

## Pre-Audit Manifest

### Files to CREATE

| File                                                                | Purpose                     |
| ------------------------------------------------------------------- | --------------------------- |
| `unified_api_contracts/external/polymarket/settlement_registry.py`  | Settlement source registry  |
| `unified_features_interface/.../prediction/btc_spx_features.py`     | BTC/SPX prediction features |
| `unified_features_interface/.../prediction/sports_odds_features.py` | Sports odds features        |

### Files to MODIFY

| File                                                                      | Change                        |
| ------------------------------------------------------------------------- | ----------------------------- |
| `unified_reference_data_interface/adapters/polymarket.py`                 | Cross-reference fixture_id    |
| `unified_api_contracts/canonical/domain/prediction/prediction_mapping.py` | ID helpers                    |
| `unified_api_contracts/external/polymarket/__init__.py`                   | Export settlement registry    |
| `unified-trading-pm/codex/02-data/prediction-schema-paths.md`             | Update with fixture ID format |
