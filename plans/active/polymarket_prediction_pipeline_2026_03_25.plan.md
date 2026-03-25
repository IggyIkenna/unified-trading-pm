---
name: polymarket-prediction-pipeline
locked_by: live-defi-rollout
locked_since: 2026-03-25
overview: |
  Wire Polymarket CLOB + Gamma data into the unified trading system as the PREDICTION category.
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
  - unified-internal-contracts (UIC) — prediction domain TypedDicts (if needed)
  - unified-market-interface (UMI) — PolymarketGammaAdapter for tick data
  - unified-reference-data-interface (URDI) — PolymarketReferenceAdapter for market discovery
  - instruments-service — PREDICTION category hook
  - market-tick-data-service — PREDICTION category hook with POLYMARKET venue
  - unified-config-interface (UCI) — prediction domain config
  - unified-trading-pm — plan + scripts
  - unified-trading-codex — prediction-schema-paths.md
  - polymarket-correlation-research — borrow patterns (read-only, no modifications)

type: code
epic: epic-code-completion
status: active

completion_gates:
  code: C5
  deployment: D1
  business: B4

repo_gates:
  - repo: unified-api-contracts
    code: C0
    notes: "VENUE_CATEGORY_MAP, Polymarket canonical mappings, soccer team/fixture cross-reference"
  - repo: unified-internal-contracts
    code: C0
    notes: "Prediction domain TypedDicts if needed"
  - repo: unified-market-interface
    code: C0
    notes: "PolymarketGammaAdapter for CLOB trade data + Gamma market metadata"
  - repo: unified-reference-data-interface
    code: C0
    notes: "PolymarketReferenceAdapter for market discovery + instrument registration"
  - repo: instruments-service
    code: C0
    notes: "Wire PREDICTION category → POLYMARKET venue"
  - repo: market-tick-data-service
    code: C0
    notes: "Wire PREDICTION category → POLYMARKET venue for tick data"
  - repo: unified-config-interface
    code: C0
    notes: "Prediction domain config (if needed)"
  - repo: unified-trading-pm
    code: C0
    notes: "Plan file"
  - repo: unified-trading-codex
    code: C0
    notes: "prediction-schema-paths.md"

isProject: false

todos:
  # ============================================================================
  # PHASE 1 — UAC: PREDICTION Category + Venue Registry  [PARALLEL]
  # ============================================================================
  - id: p1a-prediction-venue-category-map
    content: |
      - [ ] [AGENT] P0. Add PREDICTION to VENUE_CATEGORY_MAP in UAC market_data_categories.py.
        File: unified_api_contracts/registry/market_data_categories.py
        Currently PREDICTION is missing entirely. Add:
          "prediction": {
              "venues": ["POLYMARKET", "KALSHI"],
              "data_types": ["prediction_trades", "prediction_book_snapshot", "prediction_market_metadata"],
          }
        Also add POLYMARKET and KALSHI to the VENUE_CATEGORY_MAP reverse lookup.
        QG: cd unified-api-contracts && bash scripts/quality-gates.sh
    status: pending

  - id: p1b-expand-polymarket-series-mappings
    content: |
      - [ ] [AGENT] P0. Expand Polymarket series-to-league mappings in UAC sports_mappings.py.
        File: unified_api_contracts/external/polymarket/sports_mappings.py
        Currently only maps 10 leagues. Add all Polymarket soccer series discovered:
          Polymarket series slug          → canonical league_id
          ─────────────────────────────────────────────────────
          "premier-league-2025"           → "EPL"
          "efl-championship"              → "ENG_CHAMPIONSHIP"
          "efa-2025"                      → "FA_CUP"
          "la-liga-2025"                  → "LAL"
          "la-liga-2"                     → "SPA_SEGUNDA"
          "copa-del-rey"                  → "COPA_DEL_REY"
          "bundesliga-2025"              → "BUN"
          "bundesliga-2"                 → "GER_2BUNDESLIGA"
          "serie-a-2025"                 → "SEA"
          "ligue-1-2025"                 → "FL1"
          "ligue-2"                      → "FR_LIGUE_2"
          "scottish-premiership"         → "SCO_PREM"
          "primeira-liga"                → "POR_PRIMEIRA"
          "denmark-superliga"            → "DEN_SUPERLIGA"
          "norway-eliteserien"           → "NOR_ELITESERIEN"
          "tur-2025"                     → "TUR_SUPER_LIG"
          "a-league-soccer"              → "AUS_ALEAGUE"
          "mls-2025"                     → "MLS"
          "primera-a"                    → "COL_PRIMERA_A"
          "primera-divisin-argentina"    → "ARG_PRIMERA"
          "k-league"                     → "KOR_KLEAGUE"
          "japan-j2-league"              → "JPN_J2"
          "saudi-professional-league"    → "SAU_PRO_LEAGUE"
          "rus-2025"                     → "RUS_PREMIER"
          "ucl-2025" / "ucl"             → "UCL"
          "uel-2025"                     → "UEL"
          "europa-conference-league"     → "UECL"
          "womens-champions-league"      → "UWCL"
          "concacaf"                     → "CONCACAF"
          "sud-2025"                     → "COPA_SUDAMERICANA"
          "fifa-friendly"                → "FIFA_FRIENDLY"
          "uef-qualifiers"               → "UEF_QUALIFIERS"
          "ofc"                          → "OFC"
          "liga-1"                       → "IDN_LIGA_1"
        Ensure any NEW league_ids that don't exist in LEAGUE_REGISTRY are also added
        to league_data_prediction.py or league_data_other.py as appropriate.
        Include reverse mapping function: get_canonical_league_for_polymarket_series(series_slug).
    status: pending

  - id: p1c-expand-crypto-macro-mappings
    content: |
      - [ ] [AGENT] P0. Expand crypto/macro mappings in UAC crypto_macro_mappings.py.
        File: unified_api_contracts/external/polymarket/crypto_macro_mappings.py
        Current: BTC timeframes (5m,15m,1h,4h,1d), SPX timeframes (1d only).
        Expand to match actual Polymarket series discovered:

        POLYMARKET_BTC_TIMEFRAMES = ("5m", "15m", "1h", "4h", "1d", "1w", "1M")
        POLYMARKET_ETH_TIMEFRAMES = ("5m", "15m", "1h", "4h", "1d", "1w", "1M")
        POLYMARKET_SOL_TIMEFRAMES = ("5m", "15m", "1h", "4h", "1d")
        POLYMARKET_XRP_TIMEFRAMES = ("5m", "15m", "1h", "4h", "1w")
        POLYMARKET_DOGE_TIMEFRAMES = ("5m", "15m", "1d", "1M")
        POLYMARKET_BNB_TIMEFRAMES = ("5m", "15m", "4h", "1d")
        POLYMARKET_HYPE_TIMEFRAMES = ("5m", "15m", "1h", "4h", "1d")

        POLYMARKET_SPX_TIMEFRAMES = ("1d", "1M")  # daily + monthly hit
        POLYMARKET_NDX_TIMEFRAMES = ("1d", "1M")
        POLYMARKET_DJIA_TIMEFRAMES = ("1d",)
        POLYMARKET_DAX_TIMEFRAMES = ("1d",)
        POLYMARKET_HANG_SENG_TIMEFRAMES = ("1d",)
        POLYMARKET_RUSSELL_TIMEFRAMES = ("1d",)

        Add commodity series:
        POLYMARKET_CRUDE_OIL_TIMEFRAMES = ("1d",)
        POLYMARKET_GOLD_TIMEFRAMES = ("1d",)
        POLYMARKET_SILVER_TIMEFRAMES = ("1d",)

        Add forex series:
        POLYMARKET_GBPUSD_TIMEFRAMES = ("1d",)
        POLYMARKET_EURUSD_TIMEFRAMES = ("1d",)
        POLYMARKET_USDJPY_TIMEFRAMES = ("1d",)

        Add slug pattern constants for runtime market discovery:
        SLUG_PATTERNS = {
            "BTC_5M": "btc-updown-5m-{ts}",
            "BTC_HOURLY": "bitcoin-up-or-down-{month}-{day}-{time}-et",
            "SPX_DAILY": "spx-daily-up-or-down",
            ...
        }

        Expand get_polymarket_tags_for_underlying() with all new underlyings.
    status: pending

  - id: p1d-canonical-instrument-id-format
    content: |
      - [ ] [AGENT] P0. Define canonical instrument ID format for PREDICTION category.
        File: unified_api_contracts/external/polymarket/schemas.py (add docstring)
        AND create: unified_api_contracts/canonical/domain/prediction/__init__.py

        Canonical instrument ID format for PREDICTION:
        ┌────────────────────────────────────────────────────────────────┐
        │ Crypto up/down:                                                │
        │   POLYMARKET::UP_DOWN::{ASSET}::{TIMEFRAME}::{WINDOW_END_TS}  │
        │   e.g. "POLYMARKET::UP_DOWN::BTC::5M::1774230900"             │
        │                                                                │
        │ Macro/equity up/down:                                          │
        │   POLYMARKET::UP_DOWN::{INDEX}::{TIMEFRAME}::{DATE}           │
        │   e.g. "POLYMARKET::UP_DOWN::SPX::1D::2026-03-25"             │
        │                                                                │
        │ Soccer/football fixture:                                       │
        │   POLYMARKET::{MARKET_TYPE}::{FIXTURE_ID}::{OUTCOME}          │
        │   e.g. "POLYMARKET::MONEYLINE::1034567::HOME"                  │
        │   e.g. "POLYMARKET::SPREADS::1034567::AWAY_-1.5"              │
        │   e.g. "POLYMARKET::TOTALS::1034567::OVER_2.5"                │
        │   e.g. "POLYMARKET::BTTS::1034567::YES"                       │
        └────────────────────────────────────────────────────────────────┘

        Category ID format (human-readable groupings):
          PREDICTION                       — top-level MarketCategory
          PREDICTION::CRYPTO               — BTC/ETH/SOL/XRP/DOGE/BNB/HYPE up/down
          PREDICTION::MACRO                — SPX/NDX/DJIA/crude/gold/forex up/down
          PREDICTION::FOOTBALL             — soccer fixture markets
          PREDICTION::SPORTS_OTHER         — NBA/NFL/MLB/MMA/esports

        Create helper: build_prediction_instrument_id(venue, market_type, asset_or_fixture, timeframe_or_outcome, window_id)
        Create helper: parse_prediction_instrument_id(instrument_id) -> PredictionInstrumentParts
    status: pending

  # ============================================================================
  # PHASE 1 gate: cd unified-api-contracts && bash scripts/quality-gates.sh
  # ============================================================================

  # ============================================================================
  # PHASE 2 — UAC: Polymarket-to-Canonical Soccer Mapping Tables  [SEQUENTIAL after P1]
  # ============================================================================
  - id: p2a-polymarket-team-name-mapping
    content: |
      - [ ] [AGENT] P0. Build Polymarket team name → canonical team name mapping.
        File: unified_api_contracts/external/polymarket/sports_mappings.py

        Polymarket uses full team names in market questions and outcomes:
          "Club Atlético de Madrid" → "ATLETICO_MADRID"
          "Real Sociedad de Fútbol" → "REAL_SOCIEDAD"
          "Sydney FC" → "SYDNEY_FC"
          "Perth Glory FC" → "PERTH_GLORY"

        Build POLYMARKET_TEAM_TO_CANONICAL dict by:
        1. Reading existing canonical team mappings from UAC team_mappings.py
        2. Fetching sample Polymarket soccer markets to get team name patterns
        3. Creating fuzzy match function for runtime resolution of unmapped teams
        4. Static mapping for all teams in current 25+ Polymarket soccer leagues

        Include helper: get_canonical_team_for_polymarket(polymarket_team_name: str) -> str | None
        Include helper: match_polymarket_fixture_to_canonical(
            home_team: str, away_team: str, game_start: datetime
        ) -> str | None  # returns canonical fixture_id

        The fixture cross-reference uses: league + home/away team + date → API-Football fixture_id.
        This requires URDI/USRI api_football adapter at runtime (not static).
        The static part is team name normalization only.
    status: pending
    blocked_by: p1b-expand-polymarket-series-mappings

  - id: p2b-polymarket-market-type-mapping
    content: |
      - [ ] [AGENT] P1. Map Polymarket sportsMarketType to canonical market types.
        File: unified_api_contracts/external/polymarket/sports_mappings.py

        Polymarket sportsMarketType values observed:
          "moneyline"  → MONEYLINE (match winner)
          "spreads"    → SPREADS (handicap, has "line" field e.g. -1.5)
          "totals"     → TOTALS (over/under goals, has threshold)
          "btts"       → BTTS (both teams to score)
          "draw"       → DRAW (via moneyline neg-risk group)

        Map to canonical: CanonicalBetMarket.market_name or new PredictionMarketType enum.
        Include the "line" value in canonical ID for spreads/totals:
          SPREADS with line=-1.5 → "SPREADS::fixture_id::HOME_-1.5"
          TOTALS with line=2.5 → "TOTALS::fixture_id::OVER_2.5"
    status: pending

  - id: p2c-polymarket-gamma-market-schema-update
    content: |
      - [ ] [AGENT] P1. Update PolymarketGammaMarket schema with sports-specific fields.
        File: unified_api_contracts/external/polymarket/schemas.py

        Add missing fields observed in Gamma API responses:
          sports_market_type: str | None  (moneyline, spreads, totals, btts)
          line: float | None              (spread/total value e.g. -1.5, 2.5)
          game_start_time: str | None     (ISO datetime of fixture kickoff)
          game_id: int | None             (Polymarket internal game ID)
          group_item_title: str | None    (outcome label e.g. "Sydney FC (-1.5)")
          series_slug: str | None         (league series e.g. "premier-league-2025")
          event_slug: str | None          (event grouping slug)
          neg_risk: bool = False          (neg-risk multi-outcome group)
          neg_risk_market_id: str | None  (group ID for arb detection)
          resolution_source: str | None   (official resolution URL)

        Update PolymarketGammaMarket OR create PolymarketSportsGammaMarket subclass.
    status: pending

  # ============================================================================
  # PHASE 2 gate: cd unified-api-contracts && bash scripts/quality-gates.sh
  # ============================================================================

  # ============================================================================
  # PHASE 3 — URDI + UMI: Polymarket Adapters  [PARALLEL, after P1]
  # ============================================================================
  - id: p3a-urdi-polymarket-reference-adapter
    content: |
      - [ ] [AGENT] P0. Create PolymarketReferenceAdapter in URDI.
        File: unified_reference_data_interface/adapters/polymarket.py

        Purpose: Discover Polymarket markets and register them as InstrumentRecord[].
        Pattern: Follow api_football.py adapter pattern in URDI.

        For CRYPTO up/down:
          1. Fetch active markets via Gamma API: offset pagination, filter by slug patterns
             (btc-updown-5m-*, bitcoin-up-or-down-*, etc.)
          2. For each market: build canonical instrument_id (POLYMARKET::UP_DOWN::BTC::5M::ts)
          3. Return InstrumentRecord with condition_id, clob_token_ids, resolution_source

        For SOCCER:
          1. Fetch active markets via Gamma API: filter by series_slug matching soccer leagues
          2. For each match event: cross-reference with API-Football fixtures using
             team names + game_start_time + league
          3. Build canonical instrument_id (POLYMARKET::MONEYLINE::fixture_id::outcome)
          4. Return InstrumentRecord with both Polymarket and canonical IDs

        For MACRO:
          1. Fetch SPX/NDX/DJIA/crude/gold daily up/down via slug patterns
          2. Build canonical instrument_id (POLYMARKET::UP_DOWN::SPX::1D::date)

        API: https://gamma-api.polymarket.com/markets (no auth, paginated oldest-first)
        Borrow patterns from: polymarket-correlation-research/polymarket_correlation/fetchers/polymarket.py
          - offset-based pagination (not text search — text search unreliable)
          - concurrent fetching with ThreadPoolExecutor
          - rate limiting (0.02s between requests)

        Register in URDI factory.py: "POLYMARKET" → PolymarketReferenceAdapter
    status: pending
    blocked_by: p1d-canonical-instrument-id-format

  - id: p3b-umi-polymarket-adapter
    content: |
      - [ ] [AGENT] P0. Create PolymarketTickAdapter in UMI.
        File: unified_market_interface/adapters/polymarket.py

        Purpose: Fetch historical trades and price data for registered Polymarket markets.
        Pattern: Follow OddsApiAdapter pattern for SPORTS tick data in UMI.

        Two data sources per market:
        1. CLOB API: https://clob.polymarket.com
           - GET /trades?market={conditionId} — historical trade fills
           - GET /book?token_id={clobTokenId} — current order book snapshot
           No auth required for read-only.

        2. Data API: https://data-api.polymarket.com
           - GET /trades?market={conditionId}&after={ts} — paginated trade history
           Pattern from polymarket-correlation-research: cursor-based pagination,
           handle 429 with 2s backoff, 500 trades per page, max 30 pages per market.

        Output: DataFrame with columns:
          instrument_id (canonical), timestamp, price, size, side, condition_id,
          outcome (Up/Down or team name), notional

        For crypto up/down: aggregate trades into 5m/15m/1h bars with OFI features
        (borrow from polymarket_correlation/features.py PolyFeatureBuilder)

        Register in UMI: "POLYMARKET" → PolymarketTickAdapter in PREDICTION registry.
    status: pending
    blocked_by: p1d-canonical-instrument-id-format

  # ============================================================================
  # PHASE 3 gate: cd unified-reference-data-interface && bash scripts/quality-gates.sh
  #               cd unified-market-interface && bash scripts/quality-gates.sh
  # ============================================================================

  # ============================================================================
  # PHASE 4 — Services: Wire PREDICTION Category  [SEQUENTIAL after P3]
  # ============================================================================
  - id: p4a-instruments-prediction-hook
    content: |
      - [ ] [AGENT] P0. Wire PREDICTION category in instruments-service orchestrator.
        File: instruments_service/engine/orchestrator.py

        Add to get_venues_for_categories():
          "PREDICTION" → ["POLYMARKET"]

        This routes instruments-service --category PREDICTION to call
        URDI PolymarketReferenceAdapter → InstrumentRecord[] → hive Parquet.

        GCS output path:
          instruments-store-prediction-{project}/instrument_availability/
            by_date/day={date}/venue=POLYMARKET/instruments.parquet

        Test: cd instruments-service && python -m instruments_service.service \
          --operation fetch --category PREDICTION --date 2026-03-25
    status: pending
    blocked_by: p3a-urdi-polymarket-reference-adapter

  - id: p4b-mtds-prediction-hook
    content: |
      - [ ] [AGENT] P0. Wire PREDICTION category in MTDS orchestrator.
        File: market_tick_data_service/engine/orchestrator.py

        Add to get_venues_for_categories():
          "PREDICTION" → ["POLYMARKET"]

        This routes market-tick-data-service --category PREDICTION to call
        UMI PolymarketTickAdapter → DataFrame → hive Parquet.

        GCS output path:
          market-data-tick-prediction-{project}/raw_tick_data/
            by_date/day={date}/data_type=trades/venue=POLYMARKET/
              sub_category=crypto/trades.parquet
              sub_category=macro/trades.parquet
              sub_category=football/trades.parquet

        Test: cd market-tick-data-service && python -m market_tick_data_service.service \
          --operation download --category PREDICTION --date 2026-03-25
    status: pending
    blocked_by: p3b-umi-polymarket-adapter

  # ============================================================================
  # PHASE 4 gate: cd instruments-service && bash scripts/quality-gates.sh
  #               cd market-tick-data-service && bash scripts/quality-gates.sh
  # ============================================================================

  # ============================================================================
  # PHASE 5 — GCS Buckets + Codex  [PARALLEL, can start immediately]
  # ============================================================================
  - id: p5a-gcs-bucket-creation
    content: |
      - [ ] [HUMAN] P1. Create GCS buckets for prediction category data.
        Buckets needed (following existing naming convention):
          instruments-store-prediction-{project}
          market-data-tick-prediction-{project}
          features-prediction-{project}   (for future features service)

        Hive-partitioned paths:
          instruments-store-prediction-{project}/
            instrument_availability/by_date/day={date}/venue=POLYMARKET/instruments.parquet

          market-data-tick-prediction-{project}/
            raw_tick_data/by_date/day={date}/data_type=trades/venue=POLYMARKET/
              sub_category=crypto/{asset}_{timeframe}.parquet
              sub_category=macro/{index}_{timeframe}.parquet
              sub_category=football/{fixture_id}.parquet

        Region: asia-northeast1 (same as other buckets)
        Storage class: STANDARD
    status: pending

  - id: p5b-codex-prediction-schema-paths
    content: |
      - [ ] [AGENT] P2. Create prediction-schema-paths.md in codex.
        File: unified-trading-codex/02-data/prediction-schema-paths.md

        Document:
        1. Canonical instrument ID format for all PREDICTION sub-categories
        2. GCS hive path templates
        3. Polymarket API endpoints and rate limits
        4. Series-to-league mapping table
        5. Team name normalization rules
        6. Data freshness expectations (crypto: every 5m, soccer: per matchday)
    status: pending

  # ============================================================================
  # PHASE 6 — Validation  [SEQUENTIAL after P4]
  # ============================================================================
  - id: p6a-crypto-validation
    content: |
      - [ ] [HUMAN+AGENT] P0. Validate crypto up/down pipeline end-to-end.
        1. instruments-service --category PREDICTION --date 2026-03-25
           → Verify: BTC/ETH/SOL 5m+15m+1h markets discovered for today
        2. market-tick-data-service --category PREDICTION --date 2026-03-25
           → Verify: Trade data fetched for discovered markets
        3. Check canonical instrument IDs match format spec
        4. Check GCS output in hive paths
    status: pending
    blocked_by: p4a-instruments-prediction-hook, p4b-mtds-prediction-hook

  - id: p6b-soccer-validation
    content: |
      - [ ] [HUMAN+AGENT] P0. Validate soccer fixture pipeline end-to-end.
        1. instruments-service --category PREDICTION --date 2026-03-25
           → Verify: Soccer fixtures from Premier League, La Liga, etc. discovered
           → Verify: Polymarket team names resolved to canonical team IDs
           → Verify: Cross-reference with API-Football fixture_ids where possible
        2. market-tick-data-service --category PREDICTION --date 2026-03-25
           → Verify: Trade data for soccer markets fetched
        3. Check canonical instrument IDs include fixture_id from API-Football
    status: pending
    blocked_by: p4a-instruments-prediction-hook, p4b-mtds-prediction-hook

  # ============================================================================
  # PHASE 7 — QG Sweep  [PARALLEL after P6]
  # ============================================================================
  - id: p7a-qg-sweep
    content: |
      - [ ] [AGENT] P0. Run quality gates across all touched repos.
        cd unified-api-contracts && bash scripts/quality-gates.sh
        cd unified-internal-contracts && bash scripts/quality-gates.sh
        cd unified-reference-data-interface && bash scripts/quality-gates.sh
        cd unified-market-interface && bash scripts/quality-gates.sh
        cd instruments-service && bash scripts/quality-gates.sh
        cd market-tick-data-service && bash scripts/quality-gates.sh
        All must pass.
    status: pending
    blocked_by: p6a-crypto-validation
---

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

- `instruments-service --category PREDICTION` produces InstrumentRecord[]
- `market-tick-data-service --category PREDICTION` writes tick data to GCS
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
| `unified-trading-codex/02-data/prediction-schema-paths.md`           | New: PREDICTION paths doc          | Create |

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
python -m instruments_service.service --operation fetch --category PREDICTION --date 2026-03-25
python -m market_tick_data_service.service --operation download --category PREDICTION --date 2026-03-25
gsutil ls gs://instruments-store-prediction-*/instrument_availability/by_date/day=2026-03-25/
gsutil ls gs://market-data-tick-prediction-*/raw_tick_data/by_date/day=2026-03-25/
```
