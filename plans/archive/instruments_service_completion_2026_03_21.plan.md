---
title: "Instruments Service Completion — Post-Batch-Validation Residuals"
created: 2026-03-21
status: active
priority: P0
owner: agent
locked_by: null
locked_since: null
---

# Instruments Service Completion

Residual items from the instruments-service batch validation session (2026-03-18 to 2026-03-21). All 4 asset classes
flowing (1.35M+ instruments, 35 venues). These items clean up remaining gaps.

## Context

Session produced: CeFi 387k (18 venues), TradFi 959k (5 venues), DeFi 110 (12 venues), Sports 336 (1 venue). 49 venues
with 380 error codes classified. URDI architecture clean for DeFi (zero UMI imports). 8 USRI sports adapters built, 7/8
tested working. Data ownership docs in codex.

## Phase 1: Service Topology Rollout (DONE)

- [x] [AGENT] P0. Wire market-tick-data-service to UTL topology resolver — also fixed hardcoded GCSEventSink in live
      mode
- [x] [AGENT] P0. Wire market-data-processing-service to UTL topology resolver
- [x] [AGENT] P0. Wire execution-service to UTL topology resolver — replaced hardcoded GCSEventSink with topology-driven
      selection
- [x] [AGENT] P0. Wire strategy-service to UTL topology resolver
- [x] [AGENT] P0. Wire risk-and-exposure-service to UTL topology resolver — already had get_messaging_protocol, added
      get_storage_protocol
- [x] [AGENT] P0. Wire alerting-service to UTL topology resolver
- [x] [AGENT] P0. Wire features-delta-one-service to UTL topology resolver — already fully wired
- [x] [AGENT] P0. Wire features-onchain-service to UTL topology resolver — already fully wired
- [x] [AGENT] P0. Wire pnl-attribution-service to UTL topology resolver — added get_storage_protocol

**Gate**: PASSED — All 9 services import `get_messaging_protocol` from UTL.

## Phase 2: DeFi Venue Fixes (DONE)

- [x] [AGENT] P1. Fix Aave V3 — hardcoded wrong subgraph ID, now uses `get_subgraph_id("aave_v3", chain)` from UAC SSOT
- [x] [AGENT] P1. Fix Balancer — GraphQL `minTvl` was unquoted (BigDecimal needs string), lowered threshold 500k→100k
- [x] [AGENT] P1. Verify Hyperliquid — confirmed correct, no changes needed
- [x] [AGENT] P2. Databento .env cleanup — removed stale placeholder bucket, kept only API key

**Gate**: DeFi batch produces 110 instruments across 12 venues (was 98/11). Target 150+ needs Aave V3 + Balancer to
produce via Graph — may need live API key test.

## Phase 3: Features-Sports-Service Data Wiring (SEQUENTIAL)

Calculators are ALREADY migrated (20 calculators in features-sports-service). What's missing is data source wiring.

### Data classification (per data-ownership-principles.md):

- **Reference data (USRI)**: fixtures (API Football), leagues/teams/standings (SoccerFootball), weather (Open Meteo),
  player values (Transfermarkt)
- **Derived/features data (UFI)**: xG stats (Understat), match statistics/predictions (FootyStats) — these are
  pre-computed, not raw ticks
- **Market data (UMI)**: odds ticks (OddsAPI, OpticOdds, Pinnacle) — raw price feeds

### Todos:

- [ ] [AGENT] P1. Audit calculator field parity: compare features-sports-service calculator input columns vs
      new-sports-batting-services calculator input columns — document any gaps
- [ ] [AGENT] P1. Wire features-sports-service data/loader.py to USRI: add `load_fixtures_from_usri(date, leagues)`,
      `load_teams_from_usri(league_id)`, `load_weather_from_usri(venue_lat, venue_lon, date)` methods
- [ ] [AGENT] P1. Wire features-sports-service data/loader.py to UFI: add `load_xg_from_ufi(match_ids)` for Understat,
      `load_match_stats_from_ufi(date)` for FootyStats — these are derived features, not raw data
- [ ] [AGENT] P1. Wire features-sports-service batch_handler.py: on invocation, call loader → calculators → writer
      (DataSink)
- [ ] [AGENT] P2. Understat match-level scraping: map API Football fixture IDs → Understat match IDs for bulk xG fetch
- [ ] [AGENT] P2. Test: run features-sports-service batch for Jan 3 2026, verify feature vectors produced
- [ ] [AGENT] P2. Backfill script: generate features for historical dates using USRI + UFI data

**Gate**: features-sports-service produces feature vectors for EPL Jan 3 2026 fixtures via
`--run-mode batch --start-date 2026-01-03`.

## Phase 4: Live Mode Design + Implementation (SEQUENTIAL)

- [ ] [HUMAN] P0. Design decision: instruments-service live mode architecture
  - CeFi live source: CCXT (TARDIS is T+1 only) — configurable via InstrumentProcessingConfig
  - DeFi live source: same URDI adapters, different polling interval
  - Sports live source: API Football fixtures (pre-match), OddsAPI/OpticOdds (live odds via UMI)
  - Config: `cefi_live_source: "ccxt"`, `polling_interval_minutes: 15`
- [ ] [AGENT] P0. Implement instruments-service live mode handler (replace stub in live_mode_handler.py)
- [ ] [AGENT] P0. Wire ConfigReloader for hot-reload of InstrumentProcessingConfig in live mode
- [ ] [AGENT] P1. Wire PubSub for instrument change notifications to downstream services
- [ ] [AGENT] P1. Wire features-sports-service live mode: PubSub subscriber triggers feature recomputation on new
      fixture/odds data

**Gate**: instruments-service --run-mode live produces instruments continuously with configurable polling.

## Phase 5: Final QG + Documentation (PARALLEL)

- [ ] [AGENT] P1. Run quality gates on all modified repos (instruments-service, UAC, UCI, UMI, URDI, USRI, UTL,
      features-sports-service + 9 topology-wired services)
- [ ] [AGENT] P2. Update asset-class-ownership.md: DeFi section from "MOSTLY CLEAN" → "CLEAN" (fully on URDI), Sports
      section from "NEEDS WORK" → "PARTIALLY COMPLETE" (USRI built, calculators migrated, data wiring pending)
- [ ] [AGENT] P2. Update instruments_service_batch_validation_2026_03_17.plan.md — mark completed items from this
      session

## Phase 6: Sports API Key Rotation + Testing (PARALLEL — user action items)

- [ ] [HUMAN] P2. Rotate OddsAPI key if current one stays deactivated (new key: d90728dfda10f7499074bf047a996ec8 —
      updated in Secret Manager, test showed 82 sports but adapter got 401)
- [ ] [HUMAN] P3. Pinnacle API credentials — needed for sharp odds, low priority
- [ ] [AGENT] P2. Test all 7 working sports sources end-to-end: api_football (56 fixtures), odds_api (2521 odds),
      footystats (50 stats), open_meteo (weather), understat (xG), soccerfootball (50 leagues), transfermarkt (Apify)
