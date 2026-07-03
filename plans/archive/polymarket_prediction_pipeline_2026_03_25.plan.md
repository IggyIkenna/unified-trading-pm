---
doc_type:
title: polymarket-prediction-pipeline
summary:
status: active
nature:
asset_group: [cross-cutting]
stage: [meta]
repos: [instruments-service, market-tick-data-service, unified-api-contracts, unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-25'
remaining_todos_consolidated_into: consolidated_sports_prediction_pipeline_2026_04_15
superseded_by: [consolidated_sports_prediction_pipeline_2026_04_15.md]
reconciliation_status: superseded_by_consolidator
reconciliation_date: 2026-04-25
locked_by: live-defi-rollout
locked_since: 2026-03-25
overview: 'Wire Polymarket CLOB + Gamma data into the unified trading system as the PREDICTION category.

  Three sub-domains: crypto up/down (BTC, ETH, SOL, XRP, DOGE, BNB, HYPE — all timeframes),

  macro up/down (SPX, NDX, DJIA, DAX, crude oil, gold — daily+), and football/soccer fixture

  markets (25+ leagues on Polymarket mapped to canonical league/team/fixture IDs from UAC).


  ## Problem

  The PREDICTION category exists in UIC MarketCategory and UAC has Polymarket schemas

  (external/polymarket/ with schemas.py, normalize.py, sports_mappings.py, crypto_macro_mappings.py)

  but NO pipeline wiring exists:

  1. PREDICTION not in UAC market_data_categories.py (no VENUE_CATEGORY_MAP entry)

  2. No POLYMARKET venue in instruments-service or MTDS orchestrators

  3. No UMI adapter for Polymarket Gamma/CLOB/Data APIs

  4. No URDI adapter for Polymarket reference data (market discovery)

  5. Polymarket soccer team/fixture names NOT mapped to canonical IDs

  6. No GCS buckets for prediction category data

  7. polymarket-correlation-research is standalone — fetchers need to move into UMI/URDI


  ## Solution

  Phase 1: UAC — add PREDICTION to VENUE_CATEGORY_MAP, expand Polymarket mappings

  Phase 2: UAC — build Polymarket-to-canonical mapping tables for soccer leagues/teams/fixtures

  Phase 3: URDI + UMI — create Polymarket adapters for reference data + tick data

  Phase 4: instruments-service + MTDS — wire PREDICTION category with POLYMARKET venue

  Phase 5: GCS buckets + hive paths for prediction data

  Phase 6: Validation — fetch 1-day crypto + soccer data end-to-end


  ## Scope: 10 repos touched

  - unified-api-contracts (UAC) — VENUE_CATEGORY_MAP, Polymarket mappings, canonical ID format

  - unified-api-contracts (internal) (UIC) — prediction domain TypedDicts (if needed)

  - unified-market-interface (UMI) — PolymarketGammaAdapter for tick data

  - unified-reference-data-interface (URDI) — PolymarketReferenceAdapter for market discovery

  - instruments-service — PREDICTION category hook

  - market-tick-data-service — PREDICTION category hook with POLYMARKET venue

  - unified-config-interface (UCI) — prediction domain config

  - unified-trading-pm — plan + scripts

  - unified-trading-pm/codex — prediction-schema-paths.md

  - polymarket-correlation-research — borrow patterns (read-only, no modifications)

  '
type: code
epic: epic-code-completion
completion_gates: {code: C5, deployment: D1, business: B4}
repo_gates:
- {repo: unified-api-contracts, code: C0, notes: 'VENUE_CATEGORY_MAP, Polymarket canonical mappings, soccer team/fixture cross-reference'}
- {repo: unified-api-contracts (internal), code: C0, notes: Prediction domain TypedDicts if needed}
- {repo: unified-market-interface, code: C0, notes: PolymarketGammaAdapter for CLOB trade data + Gamma market metadata}
- {repo: unified-reference-data-interface, code: C0, notes: PolymarketReferenceAdapter for market discovery + instrument registration}
- {repo: instruments-service, code: C0, notes: Wire PREDICTION category → POLYMARKET venue}
- {repo: market-tick-data-service, code: C0, notes: Wire PREDICTION category → POLYMARKET venue for tick data}
- {repo: unified-config-interface, code: C0, notes: Prediction domain config (if needed)}
- {repo: unified-trading-pm, code: C0, notes: Plan file}
- {repo: unified-trading-pm/codex, code: C0, notes: prediction-schema-paths.md}
isProject: false
todos:
- {id: p1a-prediction-venue-category-map, content: "- [ ] [AGENT] P0. Add PREDICTION to VENUE_CATEGORY_MAP in UAC market_data_categories.py.\n  File: unified_api_contracts/registry/market_data_categories.py\n  Currently PREDICTION is missing entirely. Add:\n    \"prediction\": {\n        \"venues\": [\"POLYMARKET\", \"KALSHI\"],\n        \"data_types\": [\"prediction_trades\", \"prediction_book_snapshot\", \"prediction_market_metadata\"],\n    }\n  Also add POLYMARKET and KALSHI to the VENUE_CATEGORY_MAP reverse lookup.\n  QG: cd unified-api-contracts && bash scripts/quality-gates.sh\n", status: done, note: 'VENUES_BY_CATEGORY[''prediction''] + DATA_TYPES_BY_CATEGORY already present in market_data_categories.py'}
- {id: p1b-expand-polymarket-series-mappings, content: "- [ ] [AGENT] P0. Expand Polymarket series-to-league mappings in UAC sports_mappings.py.\n  File: unified_api_contracts/external/polymarket/sports_mappings.py\n  Currently only maps 10 leagues. Add all Polymarket soccer series discovered:\n    Polymarket series slug          → canonical league_id\n    ─────────────────────────────────────────────────────\n    \"premier-league-2025\"           → \"EPL\"\n    \"efl-championship\"              → \"ENG_CHAMPIONSHIP\"\n    \"efa-2025\"                      → \"FA_CUP\"\n    \"la-liga-2025\"                  → \"LAL\"\n    \"la-liga-2\"                     → \"SPA_SEGUNDA\"\n    \"copa-del-rey\"                  → \"COPA_DEL_REY\"\n    \"bundesliga-2025\"              → \"BUN\"\n    \"bundesliga-2\"                 → \"GER_2BUNDESLIGA\"\n    \"serie-a-2025\"                 → \"SEA\"\n    \"ligue-1-2025\"                 → \"FL1\"\n    \"ligue-2\"                      → \"FR_LIGUE_2\"\n \
    \   \"scottish-premiership\"         → \"SCO_PREM\"\n    \"primeira-liga\"                → \"POR_PRIMEIRA\"\n    \"denmark-superliga\"            → \"DEN_SUPERLIGA\"\n    \"norway-eliteserien\"           → \"NOR_ELITESERIEN\"\n    \"tur-2025\"                     → \"TUR_SUPER_LIG\"\n    \"a-league-soccer\"              → \"AUS_ALEAGUE\"\n    \"mls-2025\"                     → \"MLS\"\n    \"primera-a\"                    → \"COL_PRIMERA_A\"\n    \"primera-divisin-argentina\"    → \"ARG_PRIMERA\"\n    \"k-league\"                     → \"KOR_KLEAGUE\"\n    \"japan-j2-league\"              → \"JPN_J2\"\n    \"saudi-professional-league\"    → \"SAU_PRO_LEAGUE\"\n    \"rus-2025\"                     → \"RUS_PREMIER\"\n    \"ucl-2025\" / \"ucl\"             → \"UCL\"\n    \"uel-2025\"                     → \"UEL\"\n    \"europa-conference-league\"     → \"UECL\"\n    \"womens-champions-league\"      → \"UWCL\"\n    \"concacaf\"                     → \"CONCACAF\"\n    \"sud-2025\"      \
    \               → \"COPA_SUDAMERICANA\"\n    \"fifa-friendly\"                → \"FIFA_FRIENDLY\"\n    \"uef-qualifiers\"               → \"UEF_QUALIFIERS\"\n    \"ofc\"                          → \"OFC\"\n    \"liga-1\"                       → \"IDN_LIGA_1\"\n  Ensure any NEW league_ids that don't exist in LEAGUE_REGISTRY are also added\n  to league_data_prediction.py or league_data_other.py as appropriate.\n  Include reverse mapping function: get_canonical_league_for_polymarket_series(series_slug).\n", status: pending}
- {id: p1c-expand-crypto-macro-mappings, content: '- [x] [AGENT] P0. Expand crypto/macro mappings in UAC crypto_macro_mappings.py — POLYMARKET_TIMEFRAMES + slug patterns + get_polymarket_tags_for_underlying() expanded with all underlyings

    ', status: done, note: crypto_macro_mappings.py has POLYMARKET_TIMEFRAMES + slug patterns}
- {id: p1d-canonical-instrument-id-format, content: "- [ ] [AGENT] P0. Define canonical instrument ID format for PREDICTION category.\n  File: unified_api_contracts/external/polymarket/schemas.py (add docstring)\n  AND create: unified_api_contracts/canonical/domain/prediction/__init__.py\n\n  Canonical instrument ID format for PREDICTION:\n  ┌────────────────────────────────────────────────────────────────┐\n  │ Crypto up/down:                                                │\n  │   POLYMARKET::UP_DOWN::{ASSET}::{TIMEFRAME}::{WINDOW_END_TS}  │\n  │   e.g. \"POLYMARKET::UP_DOWN::BTC::5M::1774230900\"             │\n  │                                                                │\n  │ Macro/equity up/down:                                          │\n  │   POLYMARKET::UP_DOWN::{INDEX}::{TIMEFRAME}::{DATE}           │\n  │   e.g. \"POLYMARKET::UP_DOWN::SPX::1D::2026-03-25\"             │\n  │                                                                │\n  │ Soccer/football fixture: \
    \                                      │\n  │   POLYMARKET::{MARKET_TYPE}::{FIXTURE_ID}::{OUTCOME}          │\n  │   e.g. \"POLYMARKET::MONEYLINE::1034567::HOME\"                  │\n  │   e.g. \"POLYMARKET::SPREADS::1034567::AWAY_-1.5\"              │\n  │   e.g. \"POLYMARKET::TOTALS::1034567::OVER_2.5\"                │\n  │   e.g. \"POLYMARKET::BTTS::1034567::YES\"                       │\n  └────────────────────────────────────────────────────────────────┘\n\n  Category ID format (human-readable groupings):\n    PREDICTION                       — top-level MarketCategory\n    PREDICTION::CRYPTO               — BTC/ETH/SOL/XRP/DOGE/BNB/HYPE up/down\n    PREDICTION::MACRO                — SPX/NDX/DJIA/crude/gold/forex up/down\n    PREDICTION::FOOTBALL             — soccer fixture markets\n    PREDICTION::SPORTS_OTHER         — NBA/NFL/MLB/MMA/esports\n\n  Create helper: build_prediction_instrument_id(venue, market_type, asset_or_fixture, timeframe_or_outcome, window_id)\n  Create helper:\
    \ parse_prediction_instrument_id(instrument_id) -> PredictionInstrumentParts\n", status: pending}
- {id: p2a-polymarket-team-name-mapping, content: "- [ ] [AGENT] P0. Build Polymarket team name → canonical team name mapping.\n  File: unified_api_contracts/external/polymarket/sports_mappings.py\n\n  Polymarket uses full team names in market questions and outcomes:\n    \"Club Atlético de Madrid\" → \"ATLETICO_MADRID\"\n    \"Real Sociedad de Fútbol\" → \"REAL_SOCIEDAD\"\n    \"Sydney FC\" → \"SYDNEY_FC\"\n    \"Perth Glory FC\" → \"PERTH_GLORY\"\n\n  Build POLYMARKET_TEAM_TO_CANONICAL dict by:\n  1. Reading existing canonical team mappings from UAC team_mappings.py\n  2. Fetching sample Polymarket soccer markets to get team name patterns\n  3. Creating fuzzy match function for runtime resolution of unmapped teams\n  4. Static mapping for all teams in current 25+ Polymarket soccer leagues\n\n  Include helper: get_canonical_team_for_polymarket(polymarket_team_name: str) -> str | None\n  Include helper: match_polymarket_fixture_to_canonical(\n      home_team: str, away_team: str, game_start:\
    \ datetime\n  ) -> str | None  # returns canonical fixture_id\n\n  The fixture cross-reference uses: league + home/away team + date → API-Football fixture_id.\n  This requires URDI/USRI api_football adapter at runtime (not static).\n  The static part is team name normalization only.\n", status: done, note: POLYMARKET_TEAM_TO_CANONICAL + get_canonical_team_for_polymarket in sports_mappings.py}
- {id: p2b-polymarket-market-type-mapping, content: '- [x] [AGENT] P1. POLYMARKET_MARKET_TYPE_MAP + POLYMARKET_MARKET_TO_CANONICAL implemented in sports_mappings.py / canonical_ids.py

    ', status: done, note: Market type mapping complete}
- {id: p2c-polymarket-gamma-market-schema-update, content: '- [x] [AGENT] P1. PolymarketGammaMarket updated with sports_market_type, line, game_start_time, game_id, group_item_title, series_slug, event_slug, neg_risk, neg_risk_market_id, resolution_source fields

    ', status: done, note: schemas.py lines ~339-349}
- {id: p3a-urdi-polymarket-reference-adapter, content: "- [ ] [AGENT] P0. Create PolymarketReferenceAdapter in URDI.\n  File: unified_reference_data_interface/adapters/polymarket.py\n\n  Purpose: Discover Polymarket markets and register them as InstrumentRecord[].\n  Pattern: Follow api_football.py adapter pattern in URDI.\n\n  For CRYPTO up/down:\n    1. Fetch active markets via Gamma API: offset pagination, filter by slug patterns\n       (btc-updown-5m-*, bitcoin-up-or-down-*, etc.)\n    2. For each market: build canonical instrument_id (POLYMARKET::UP_DOWN::BTC::5M::ts)\n    3. Return InstrumentRecord with condition_id, clob_token_ids, resolution_source\n\n  For SOCCER:\n    1. Fetch active markets via Gamma API: filter by series_slug matching soccer leagues\n    2. For each match event: cross-reference with API-Football fixtures using\n       team names + game_start_time + league\n    3. Build canonical instrument_id (POLYMARKET::MONEYLINE::fixture_id::outcome)\n    4. Return InstrumentRecord\
    \ with both Polymarket and canonical IDs\n\n  For MACRO:\n    1. Fetch SPX/NDX/DJIA/crude/gold daily up/down via slug patterns\n    2. Build canonical instrument_id (POLYMARKET::UP_DOWN::SPX::1D::date)\n\n  API: https://gamma-api.polymarket.com/markets (no auth, paginated oldest-first)\n  Borrow patterns from: polymarket-correlation-research/polymarket_correlation/fetchers/polymarket.py\n    - offset-based pagination (not text search — text search unreliable)\n    - concurrent fetching with ThreadPoolExecutor\n    - rate limiting (0.02s between requests)\n\n  Register in URDI factory.py: \"POLYMARKET\" → PolymarketReferenceAdapter\n", status: done, note: SUPERSEDED — implemented as instruments_service/reference_data/adapters/prediction/polymarket.py (PolymarketReferenceDataAdapter)}
- {id: p3b-umi-polymarket-adapter, content: "- [ ] [AGENT] P0. Create PolymarketTickAdapter in UMI.\n  File: unified_market_interface/adapters/polymarket.py\n\n  Purpose: Fetch historical trades and price data for registered Polymarket markets.\n  Pattern: Follow OddsApiAdapter pattern for SPORTS tick data in UMI.\n\n  Two data sources per market:\n  1. CLOB API: https://clob.polymarket.com\n     - GET /trades?market={conditionId} — historical trade fills\n     - GET /book?token_id={clobTokenId} — current order book snapshot\n     No auth required for read-only.\n\n  2. Data API: https://data-api.polymarket.com\n     - GET /trades?market={conditionId}&after={ts} — paginated trade history\n     Pattern from polymarket-correlation-research: cursor-based pagination,\n     handle 429 with 2s backoff, 500 trades per page, max 30 pages per market.\n\n  Output: DataFrame with columns:\n    instrument_id (canonical), timestamp, price, size, side, condition_id,\n    outcome (Up/Down or team name),\
    \ notional\n\n  For crypto up/down: aggregate trades into 5m/15m/1h bars with OFI features\n  (borrow from polymarket_correlation/features.py PolyFeatureBuilder)\n\n  Register in UMI: \"POLYMARKET\" → PolymarketTickAdapter in PREDICTION registry.\n", status: done, note: SUPERSEDED — PolymarketAdapter in MTDS market_interface/adapters/prediction/}
- {id: p4a-instruments-prediction-hook, content: "- [ ] [AGENT] P0. Wire PREDICTION category in instruments-service orchestrator.\n  File: instruments_service/engine/orchestrator.py\n\n  Add to get_venues_for_categories():\n    \"PREDICTION\" → [\"POLYMARKET\"]\n\n  This routes instruments-service --asset-group PREDICTION to call\n  URDI PolymarketReferenceAdapter → InstrumentRecord[] → hive Parquet.\n\n  GCS output path:\n    instruments-store-prediction-{project}/instrument_availability/\n      by_date/day={date}/venue=POLYMARKET/instruments.parquet\n\n  Test: cd instruments-service && python -m instruments_service.service \\\n    --operation fetch --asset-group PREDICTION --date 2026-03-25\n", status: done, note: 'get_venues_for_categories PREDICTION → POLYMARKET, KALSHI in orchestrator.py'}
- {id: p4b-mtds-prediction-hook, content: "- [ ] [AGENT] P0. Wire PREDICTION category in MTDS orchestrator.\n  File: market_tick_data_service/engine/orchestrator.py\n\n  Add to get_venues_for_categories():\n    \"PREDICTION\" → [\"POLYMARKET\"]\n\n  This routes market-tick-data-service --asset-group PREDICTION to call\n  UMI PolymarketTickAdapter → DataFrame → hive Parquet.\n\n  GCS output path:\n    market-data-tick-prediction-{project}/raw_tick_data/\n      by_date/day={date}/data_type=trades/venue=POLYMARKET/\n        sub_category=crypto/trades.parquet\n        sub_category=macro/trades.parquet\n        sub_category=football/trades.parquet\n\n  Test: cd market-tick-data-service && python -m market_tick_data_service.service \\\n    --operation download --asset-group PREDICTION --date 2026-03-25\n", status: done, note: get_venues_for_categories PREDICTION → POLYMARKET in mtds/orchestrator.py}
- {id: p5a-gcs-bucket-creation, content: "- [ ] [HUMAN] P1. Create GCS buckets for prediction category data.\n  Buckets needed (following existing naming convention):\n    instruments-store-prediction-{project}\n    market-data-tick-prediction-{project}\n    features-prediction-{project}   (for future features service)\n\n  Hive-partitioned paths:\n    instruments-store-prediction-{project}/\n      instrument_availability/by_date/day={date}/venue=POLYMARKET/instruments.parquet\n\n    market-data-tick-prediction-{project}/\n      raw_tick_data/by_date/day={date}/data_type=trades/venue=POLYMARKET/\n        sub_category=crypto/{asset}_{timeframe}.parquet\n        sub_category=macro/{index}_{timeframe}.parquet\n        sub_category=football/{fixture_id}.parquet\n\n  Region: asia-northeast1 (same as other buckets)\n  Storage class: STANDARD\n", status: pending}
- {id: p5b-codex-prediction-schema-paths, content: "- [ ] [AGENT] P2. Create prediction-schema-paths.md in codex.\n  File: unified-trading-pm/codex/02-data/prediction-schema-paths.md\n\n  Document:\n  1. Canonical instrument ID format for all PREDICTION sub-categories\n  2. GCS hive path templates\n  3. Polymarket API endpoints and rate limits\n  4. Series-to-league mapping table\n  5. Team name normalization rules\n  6. Data freshness expectations (crypto: every 5m, soccer: per matchday)\n", status: done, note: prediction-schema-paths.md exists in codex/02-data/}
- {id: p6a-crypto-validation, content: "- [ ] [HUMAN+AGENT] P0. Validate crypto up/down pipeline end-to-end.\n  1. instruments-service --asset-group PREDICTION --date 2026-03-25\n     → Verify: BTC/ETH/SOL 5m+15m+1h markets discovered for today\n  2. market-tick-data-service --asset-group PREDICTION --date 2026-03-25\n     → Verify: Trade data fetched for discovered markets\n  3. Check canonical instrument IDs match format spec\n  4. Check GCS output in hive paths\n", status: pending, blocked_by: 'p4a-instruments-prediction-hook, p4b-mtds-prediction-hook'}
- {id: p6b-soccer-validation, content: "- [ ] [HUMAN+AGENT] P0. Validate soccer fixture pipeline end-to-end.\n  1. instruments-service --asset-group PREDICTION --date 2026-03-25\n     → Verify: Soccer fixtures from Premier League, La Liga, etc. discovered\n     → Verify: Polymarket team names resolved to canonical team IDs\n     → Verify: Cross-reference with API-Football fixture_ids where possible\n  2. market-tick-data-service --asset-group PREDICTION --date 2026-03-25\n     → Verify: Trade data for soccer markets fetched\n  3. Check canonical instrument IDs include fixture_id from API-Football\n", status: pending, blocked_by: 'p4a-instruments-prediction-hook, p4b-mtds-prediction-hook'}
- {id: p7a-qg-sweep, content: "- [ ] [AGENT] P0. Run quality gates across all touched repos.\n  cd unified-api-contracts && bash scripts/quality-gates.sh\n  cd unified-api-contracts && bash scripts/quality-gates.sh  # includes internal contracts\n  cd unified-reference-data-interface && bash scripts/quality-gates.sh\n  cd unified-market-interface && bash scripts/quality-gates.sh\n  cd instruments-service && bash scripts/quality-gates.sh\n  cd market-tick-data-service && bash scripts/quality-gates.sh\n  All must pass.\n", status: pending, blocked_by: p6a-crypto-validation}
---

> **SUPERSEDED 2026-04-25 by
> [consolidated_sports_prediction_pipeline_2026_04_15.md](./consolidated_sports_prediction_pipeline_2026_04_15.md).**
> Original scope retained for history. Frontmatter `remaining_todos_consolidated_into:` was already present; this commit
> formalises it as canonical `superseded_by:` and adds this banner. See `_reconciliation_evidence_map_2026_04_25.md` for
> evidence.

# Polymarket Prediction Pipeline

## Problem Statement

The PREDICTION category exists in UIC MarketCategory but has zero pipeline wiring. Polymarket (the largest prediction
market by volume) provides public APIs for crypto up/down markets (BTC/ETH/SOL all timeframes), equity index markets
(SPX/NDX daily), and 25+ soccer/football leagues with moneyline/spreads/totals/btts markets. This data needs to flow
through the standard instruments-service → market-tick-data-service pipeline with canonical instrument IDs that map
Polymarket's team names, fixtures, and market types to our existing canonical formats.

## What Already Exists

| Component                   | Location                                           | Status                         |
| --------------------------- | -------------------------------------------------- | ------------------------------ |
| `MarketCategory.PREDICTION` | UIC `market_category.py:16`                        | Exists, unused                 |
| Polymarket schemas          | UAC `external/polymarket/schemas.py`               | Complete (14 models)           |
| Polymarket normalizers      | UAC `external/polymarket/normalize.py`             | Complete (6 functions)         |
| Sports tag mappings         | UAC `external/polymarket/sports_mappings.py`       | 10 leagues mapped              |
| Crypto/macro tag mappings   | UAC `external/polymarket/crypto_macro_mappings.py` | BTC+SPX only                   |
| Research fetchers           | `polymarket-correlation-research/`                 | Standalone, patterns to borrow |
| `CanonicalBetMarket`        | UAC `canonical/domain/`                            | Exists, used by normalize      |

## What's Missing

| Gap                                        | Where to fix                                 |
| ------------------------------------------ | -------------------------------------------- |
| PREDICTION not in `VENUE_CATEGORY_MAP`     | UAC `registry/market_data_categories.py`     |
| No POLYMARKET venue in instruments-service | `orchestrator.py`                            |
| No POLYMARKET venue in MTDS                | `orchestrator.py`                            |
| No UMI adapter for Polymarket              | `unified_market_interface/adapters/`         |
| No URDI adapter for Polymarket             | `unified_reference_data_interface/adapters/` |
| Only 10/25+ soccer leagues mapped          | UAC `sports_mappings.py`                     |
| No team name normalization                 | UAC `sports_mappings.py`                     |
| No fixture cross-reference                 | Needs URDI adapter at runtime                |
| No GCS buckets                             | Infrastructure                               |
| SPX only has "1d" timeframe                | UAC `crypto_macro_mappings.py`               |

## Polymarket API Architecture (Reference)

| API   | Endpoint                   | Auth                         | Use Case                                 |
| ----- | -------------------------- | ---------------------------- | ---------------------------------------- |
| Gamma | `gamma-api.polymarket.com` | None                         | Market discovery, metadata, tags, series |
| CLOB  | `clob.polymarket.com`      | L2 HMAC (optional for reads) | Order book, trades                       |
| Data  | `data-api.polymarket.com`  | None                         | Historical trade fills (paginated)       |

**Key Gamma fields for sports markets:**

- `series[].slug` → league (e.g., "premier-league-2025")
- `sportsMarketType` → market type (moneyline, spreads, totals, btts)
- `line` → spread/total value (e.g., -1.5)
- `gameStartTime` → fixture kickoff ISO datetime
- `gameId` → Polymarket internal game ID
- `outcomes` → team names or Up/Down
- `conditionId` → unique market ID (for CLOB/Data API joins)
- `clobTokenIds` → [YES_token, NO_token]

**Key Gamma fields for crypto/macro:**

- `slug` → e.g., "btc-updown-5m-1774230900" or "spx-daily-up-or-down"
- `outcomes` → ["Up", "Down"]
- `resolutionSource` → Chainlink stream URL or Binance
- `endDate` → window end time

## Polymarket Soccer Leagues Available (25+)

| Polymarket Series Slug      | Canonical league_id | Country | Competition            |
| --------------------------- | ------------------- | ------- | ---------------------- |
| `premier-league-2025`       | EPL                 | GB      | English Premier League |
| `efl-championship`          | ENG_CHAMPIONSHIP    | GB      | English Championship   |
| `efa-2025`                  | FA_CUP              | GB      | FA Cup                 |
| `la-liga-2025`              | LAL                 | ES      | La Liga                |
| `la-liga-2`                 | SPA_SEGUNDA         | ES      | Segunda División       |
| `copa-del-rey`              | COPA_DEL_REY        | ES      | Copa del Rey           |
| `bundesliga-2025`           | BUN                 | DE      | Bundesliga             |
| `bundesliga-2`              | GER_2BUNDESLIGA     | DE      | 2. Bundesliga          |
| `serie-a-2025`              | SEA                 | IT      | Serie A                |
| `ligue-1-2025`              | FL1                 | FR      | Ligue 1                |
| `ligue-2`                   | FR_LIGUE_2          | FR      | Ligue 2                |
| `scottish-premiership`      | SCO_PREM            | GB      | Scottish Premiership   |
| `primeira-liga`             | POR_PRIMEIRA        | PT      | Primeira Liga          |
| `denmark-superliga`         | DEN_SUPERLIGA       | DK      | Superliga              |
| `norway-eliteserien`        | NOR_ELITESERIEN     | NO      | Eliteserien            |
| `tur-2025`                  | TUR_SUPER_LIG       | TR      | Süper Lig              |
| `a-league-soccer`           | AUS_ALEAGUE         | AU      | A-League               |
| `mls-2025`                  | MLS                 | US      | Major League Soccer    |
| `primera-a`                 | COL_PRIMERA_A       | CO      | Primera A              |
| `primera-divisin-argentina` | ARG_PRIMERA         | AR      | Primera División       |
| `k-league`                  | KOR_KLEAGUE         | KR      | K League               |
| `japan-j2-league`           | JPN_J2              | JP      | J2 League              |
| `saudi-professional-league` | SAU_PRO_LEAGUE      | SA      | SPL                    |
| `rus-2025`                  | RUS_PREMIER         | RU      | Premier League         |
| `ucl-2025`                  | UCL                 | INTL    | Champions League       |
| `uel-2025`                  | UEL                 | INTL    | Europa League          |
| `europa-conference-league`  | UECL                | INTL    | Conference League      |
| `concacaf`                  | CONCACAF            | INTL    | CONCACAF               |
| `sud-2025`                  | COPA_SUDAMERICANA   | INTL    | Copa Sudamericana      |

## Polymarket Crypto/Macro Markets Available

| Asset     | Series Slug Pattern                             | Timeframes                  | Resolution         |
| --------- | ----------------------------------------------- | --------------------------- | ------------------ |
| BTC       | `btc-updown-{tf}-{ts}`, `bitcoin-up-or-down-*`  | 5m, 15m, 1h, 4h, 1d, 1w, 1M | Chainlink BTC/USD  |
| ETH       | `eth-updown-{tf}-{ts}`, `ethereum-up-or-down-*` | 5m, 15m, 1h, 4h, 1d, 1w, 1M | Chainlink ETH/USD  |
| SOL       | `sol-updown-{tf}-{ts}`, `solana-up-or-down-*`   | 5m, 15m, 1h, 4h, 1d         | Chainlink SOL/USD  |
| XRP       | `xrp-updown-{tf}-{ts}`, `xrp-up-or-down-*`      | 5m, 15m, 1h, 4h, 1w         | Chainlink XRP/USD  |
| DOGE      | `doge-updown-{tf}-{ts}`                         | 5m, 15m, 1d, 1M             | Chainlink DOGE/USD |
| BNB       | `bnb-updown-{tf}-{ts}`                          | 5m, 15m, 4h, 1d             | Chainlink BNB/USD  |
| HYPE      | `hype-updown-{tf}-{ts}`                         | 5m, 15m, 1h, 4h, 1d         | Chainlink          |
| SPX       | `spx-daily-up-or-down`, `spx-hit-price-monthly` | 1d, 1M                      | Official close     |
| NDX       | `ndx-daily-up-or-down`, `ndx-hit-price-monthly` | 1d, 1M                      | Official close     |
| DJIA      | `dow-jones-daily-up-or-down`                    | 1d                          | Official close     |
| DAX       | `dax-daily-up-or-down`                          | 1d                          | Official close     |
| Crude Oil | `crude-oil-cl-up-or-down`, `oil-daily-*`        | 1d                          | NYMEX settlement   |
| Gold      | `gold-daily-up-or-down`                         | 1d                          | COMEX settlement   |
| Silver    | `silver-daily-up-or-down`                       | 1d                          | COMEX settlement   |
| EUR/USD   | `eurusd-daily-up-or-down`                       | 1d                          | Forex close        |
| GBP/USD   | `gbpusd-daily-up-or-down`                       | 1d                          | Forex close        |
| USD/JPY   | `usdjpy-daily-up-or-down`                       | 1d                          | Forex close        |

## Canonical Instrument ID Format (SSOT)

| Sub-category     | Format                                                  | Example                                    |
| ---------------- | ------------------------------------------------------- | ------------------------------------------ |
| Crypto up/down   | `POLYMARKET::UP_DOWN::{ASSET}::{TF}::{WINDOW_END_TS}`   | `POLYMARKET::UP_DOWN::BTC::5M::1774230900` |
| Macro up/down    | `POLYMARKET::UP_DOWN::{INDEX}::{TF}::{DATE}`            | `POLYMARKET::UP_DOWN::SPX::1D::2026-03-25` |
| Soccer moneyline | `POLYMARKET::MONEYLINE::{FIXTURE_ID}::{OUTCOME}`        | `POLYMARKET::MONEYLINE::1034567::HOME`     |
| Soccer spreads   | `POLYMARKET::SPREADS::{FIXTURE_ID}::{OUTCOME}_{LINE}`   | `POLYMARKET::SPREADS::1034567::AWAY_-1.5`  |
| Soccer totals    | `POLYMARKET::TOTALS::{FIXTURE_ID}::{OVER_UNDER}_{LINE}` | `POLYMARKET::TOTALS::1034567::OVER_2.5`    |
| Soccer BTTS      | `POLYMARKET::BTTS::{FIXTURE_ID}::{YES_NO}`              | `POLYMARKET::BTTS::1034567::YES`           |

## Category ID Format (Human-Readable Groupings)

```
PREDICTION                     ← MarketCategory enum value
├── PREDICTION::CRYPTO         ← BTC, ETH, SOL, XRP, DOGE, BNB, HYPE up/down
├── PREDICTION::MACRO          ← SPX, NDX, DJIA, DAX, crude, gold, forex up/down
├── PREDICTION::FOOTBALL       ← 25+ soccer leagues (moneyline, spreads, totals, btts)
└── PREDICTION::SPORTS_OTHER   ← NBA, NFL, MLB, MMA, esports (future)
```

## Fixture Cross-Reference Strategy

Polymarket soccer markets identify fixtures by team names + game start time + series slug. Our canonical system uses
API-Football fixture_ids.

**Runtime cross-reference flow:**

1. URDI PolymarketReferenceAdapter discovers soccer markets via Gamma API
2. Extract: home_team, away_team, gameStartTime, series_slug
3. Map series_slug → canonical league_id (static table in sports_mappings.py)
4. Normalize team names → canonical team names (static table + fuzzy match)
5. Query API-Football (via USRI) for fixtures matching: league + teams + date
6. If match found: use API-Football fixture_id as canonical fixture_id
7. If no match: use `PM_{gameId}` as fallback fixture_id

**Team name normalization examples:**

```
"Club Atlético de Madrid"    → "ATLETICO_MADRID"
"Real Sociedad de Fútbol"    → "REAL_SOCIEDAD"
"FC Bayern München"          → "BAYERN_MUNICH"
"Paris Saint-Germain"        → "PSG"
"Sydney FC"                  → "SYDNEY_FC"
"Boyacá Chicó FC"           → "BOYACA_CHICO"
```

## Dependency DAG

```
P1 (UAC registry + mappings) ──┬── P1a: VENUE_CATEGORY_MAP
  [PARALLEL]                    ├── P1b: Soccer league mappings
                                ├── P1c: Crypto/macro mappings
                                └── P1d: Canonical ID format
                                          │
                                 UAC QG gate
                                          │
P2 (UAC soccer mapping) ──────── P2a: Team name mapping
  [SEQUENTIAL after P1]          P2b: Market type mapping
                                  P2c: Gamma schema update
                                          │
                                 UAC QG gate
                                          │
P3 (URDI + UMI adapters) ────── P3a: URDI PolymarketReferenceAdapter
  [PARALLEL, after P1]           P3b: UMI PolymarketTickAdapter
                                          │
                              URDI + UMI QG gate
                                          │
P4 (Services) ────────────────── P4a: instruments-service PREDICTION hook
  [SEQUENTIAL after P3]          P4b: MTDS PREDICTION hook
                                          │
                           instruments + MTDS QG gate
                                          │
P5 (GCS + Codex) ─────────────── P5a: GCS bucket creation    ← CAN START IMMEDIATELY
  [PARALLEL with all]             P5b: Codex docs
                                          │
P6 (Validation) ──────────────── P6a: Crypto end-to-end
  [SEQUENTIAL]                    P6b: Soccer end-to-end
                                          │
P7 (QG sweep) ────────────────── P7a: All repos green
```

## Success Criteria

### Phase 1

- PREDICTION in VENUE_CATEGORY_MAP with POLYMARKET venue
- 25+ soccer leagues mapped to canonical league_ids
- All crypto/macro underlyings and timeframes registered
- `cd unified-api-contracts && bash scripts/quality-gates.sh` green

### Phase 2

- Team name normalization covers all teams in 25+ leagues
- sportsMarketType mapped to canonical types
- PolymarketGammaMarket schema has all sports-specific fields

### Phase 3

- URDI adapter discovers markets from all 3 sub-categories
- UMI adapter fetches trades with canonical instrument IDs
- Both adapters handle rate limiting and pagination correctly

### Phase 4

- `instruments-service --asset-group PREDICTION` produces InstrumentRecord[]
- `market-tick-data-service --asset-group PREDICTION` writes tick data to GCS
- Canonical instrument IDs consistent across both services

### Phase 6

- B4: 1-day pipeline end-to-end with zero errors for both crypto and soccer
- Soccer fixture_ids cross-referenced with API-Football where possible
- Trade data includes volume, price, side, timestamp for all markets

## Pre-Audit Manifest

### Symbols being ADDED (no existing consumers to break)

| Symbol                           | Where                           | Consumers                 |
| -------------------------------- | ------------------------------- | ------------------------- |
| PREDICTION in VENUE_CATEGORY_MAP | UAC registry                    | instruments-service, MTDS |
| PolymarketReferenceAdapter       | URDI adapters/                  | instruments-service       |
| PolymarketTickAdapter            | UMI adapters/                   | MTDS                      |
| POLYMARKET_TEAM_TO_CANONICAL     | UAC external/polymarket         | URDI adapter              |
| build_prediction_instrument_id() | UAC canonical/domain/prediction | URDI, UMI adapters        |
| parse_prediction_instrument_id() | UAC canonical/domain/prediction | downstream consumers      |

### Files that need changes

| File                                                                 | Change                             | Action |
| -------------------------------------------------------------------- | ---------------------------------- | ------ |
| `unified_api_contracts/registry/market_data_categories.py`           | Add PREDICTION category            | Edit   |
| `unified_api_contracts/external/polymarket/sports_mappings.py`       | Expand to 25+ leagues + team names | Edit   |
| `unified_api_contracts/external/polymarket/crypto_macro_mappings.py` | Add all assets + timeframes        | Edit   |
| `unified_api_contracts/external/polymarket/schemas.py`               | Add sports-specific Gamma fields   | Edit   |
| `unified_api_contracts/canonical/domain/prediction/__init__.py`      | New: canonical ID helpers          | Create |
| `unified_reference_data_interface/adapters/polymarket.py`            | New: reference adapter             | Create |
| `unified_reference_data_interface/factory.py`                        | Register POLYMARKET adapter        | Edit   |
| `unified_market_interface/adapters/polymarket.py`                    | New: tick adapter                  | Create |
| `instruments_service/engine/orchestrator.py`                         | Add PREDICTION → POLYMARKET        | Edit   |
| `market_tick_data_service/engine/orchestrator.py`                    | Add PREDICTION → POLYMARKET        | Edit   |
| `unified-trading-pm/codex/02-data/prediction-schema-paths.md`        | New: PREDICTION paths doc          | Create |

## Verification

```bash
# Phase 1
cd unified-api-contracts && bash scripts/quality-gates.sh

# Phase 3
cd unified-reference-data-interface && bash scripts/quality-gates.sh
cd unified-market-interface && bash scripts/quality-gates.sh

# Phase 4
cd instruments-service && bash scripts/quality-gates.sh
cd market-tick-data-service && bash scripts/quality-gates.sh

# Phase 6: end-to-end
# Crypto
python -m instruments_service.service --operation fetch --asset-group PREDICTION --date 2026-03-25
python -m market_tick_data_service.service --operation download --asset-group PREDICTION --date 2026-03-25
gsutil ls gs://instruments-store-prediction-*/instrument_availability/by_date/day=2026-03-25/
gsutil ls gs://market-data-tick-prediction-*/raw_tick_data/by_date/day=2026-03-25/
```
