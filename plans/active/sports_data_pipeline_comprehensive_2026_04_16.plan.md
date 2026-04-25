---
title: "Sports Data Pipeline — Comprehensive Enrichment, Mapping, Scheduling & Validation"
created: 2026-04-16
status: active
locked_by: live-defi-rollout
locked_since: 2026-04-16
priority: P0
repos:
  - unified-api-contracts
  - instruments-service
  - features-sports-service
  - market-tick-data-service
  - market-data-processing-service
  - unified-trading-library
  - deployment-service
  - deployment-api
  - unified-trading-pm
code_readiness: C4
deployment_readiness: D0
business_readiness: B1
superseded_by: [sports_roadmap_master_execution_2026_04_21.plan.md]
reconciliation_status: superseded
reconciliation_date: 2026-04-25
---

> **SUPERSEDED 2026-04-25 by
> [sports_roadmap_master_execution_2026_04_21.plan.md](./sports_roadmap_master_execution_2026_04_21.plan.md).** Newer
> master execution wrapper at §12.0 register is live SSOT; this umbrella has 0/67 vs roadmap's 18/3 Original scope
> retained for history. See `_reconciliation_evidence_map_2026_04_25.md` for evidence.

# Sports Data Pipeline — Comprehensive Plan

## Context

Sports pipeline spans 7 data providers, 33 prediction leagues, 5 pipeline layers (instruments → MTDS → MDPS → features →
ML), plus scheduling, data status, and live adapters. This plan consolidates ALL outstanding sports work from prior
sessions and plans into a single actionable reference.

### Providers & Data

| Provider                   | Data Types                                                         | Coverage                                             | Auth              |
| -------------------------- | ------------------------------------------------------------------ | ---------------------------------------------------- | ----------------- |
| API Football               | Fixtures, stats, lineups, events, injuries                         | 800+ leagues                                         | RapidAPI          |
| FootyStats                 | Match stats, 24 potentials, 68 odds markets                        | 33 prediction leagues                                | API key           |
| SFI (Soccer Football Info) | Progressive (30s: stats+xG+dominance+in-play odds), pre-match odds | ~2000 matches/day                                    | RapidAPI Ultra    |
| Understat                  | Shot-level xG                                                      | 6 leagues (EPL, La Liga, BL, Serie A, Ligue 1, RFPL) | Scraping (no key) |
| Transfermarkt              | Team/player values, transfers                                      | 33 leagues                                           | RapidAPI          |
| Open-Meteo                 | Weather (3-hour match window, 3 lead times)                        | Global (by venue coords)                             | Free              |
| Odds API                   | Bookmaker-level odds (23 bookmakers)                               | 33 prediction leagues                                | API key           |

### Running VMs (as of 2026-04-16)

**Sports enrichment (4):** footystats-backfill (COMPLETED), transfermarkt-backfill, understat-backfill,
weather-backfill-openmeteo **CeFi (15):** Binance Futures 2022-2025, Binance Spot 2020-2025, Bybit 2021-2025
**DeFi/TradFi (4):** mtds-backfill-defi-1, mtds-migrate-tradfi, mtds-gas-fees-arbitrum/solana **Not launched:** SFI
progressive backfill

### Dependency DAG

```
Phase 1 (QG + Deploy) ──→ Phase 2 (SFI Schema) ──→ Phase 3 (Mappings)
                      ──→ Phase 4 (Manifest)    ──→ Phase 5 (PIT Safety)
                                                 ──→ Phase 6 (Sharding)
                                                 ──→ Phase 7 (Live)
Phase 1 ──→ Phase 8 (Cross-Category Monitoring)
Phase 3 + Phase 4 + Phase 5 ──→ Phase 9 (Validation)
```

---

## Phase 1: QG + Deploy Code Changes [PARALLEL]

- [ ] [AGENT] P0. Run QG on unified-api-contracts (FTMatchRaw 68 odds + 24 potentials,
      normalize_footystats_odds_snapshot, resolve_sfi_team 543 teams)
- [ ] [AGENT] P0. Run QG on instruments-service (\_fetch_footystats_odds, get_fixture_odds_snapshot adapter method, odds
      wiring in short-circuit + full flow)
- [ ] [SCRIPT] P0. Create code tarballs:
      `bash deployment-service/scripts/vm/create-code-tarballs.sh --asset-group SPORTS --include deployment-service`
- [ ] [SCRIPT] P0. Upload tarballs to GCS:
      `gsutil -m cp /tmp/*.tar.gz gs://deployment-scripts-central-element-323112/code/`
- [ ] [SCRIPT] P0. Re-run FootyStats VM with updated code (adds odds extraction — same /todays-matches endpoint, no
      extra API calls)
- [ ] [SCRIPT] P0. Launch SFI progressive backfill VM (2024-03-15 to 2026-04-16, ~1756 matches/day × ~700 days)

**Success criteria:** UAC + instruments-service QG pass. FootyStats VM writing `entity=footystats_odds/` with 68
columns. SFI VM writing progressive data.

---

## Phase 2: SFI Progressive Schema Enhancement [SEQUENTIAL after Phase 1]

- [ ] [AGENT] P0. Enhance CanonicalProgressiveStats in UAC to capture nested SFI structure: xG per team, dominance
      (index + avg_2_5), in-play odds (1X2, AH, O/U, Asian Corner), attacks (normal + dangerous split), shoots
      (total/on/off/goal_area)
- [ ] [AGENT] P0. Update SFI adapter `_normalize_sfi_progressive_stat()` to map nested dict structure to enhanced
      canonical model
- [ ] [AGENT] P0. Add `ht_start_timer` + `ht_end_timer` extraction in instruments-service SFI progressive writer —
      detect stats freeze (5+ consecutive entries where goals+shots+corners+attacks all unchanged, after minute 43)
- [ ] [AGENT] P1. Enhance `detect_ht_break_minute()` in FSS halftime_calculator.py — add stats-freeze fallback when no
      timer gap > 300s exists (SFI continues timer through HT, stats freeze instead)
- [ ] [AGENT] P1. Write `ht_start_timer`/`ht_end_timer` as columns in SFI progressive GCS entity so FSS reads them
      directly

**Success criteria:** SFI progressive parquets contain xG, dominance, in-play odds, ht_start/ht_end. FSS
detect_ht_break_minute works on SFI data.

---

## Phase 3: Cross-Provider Entity Mappings [PARALLEL with Phase 2]

### 3A: Team Mappings

- [ ] [AGENT] P0. Expand GCS `sports_reference/mappings/team_mapping.parquet` — add columns: `sfi_name`,
      `footystats_name`, `api_football_name`, `transfermarkt_name`, `understat_name`. Source from UAC resolve
      functions + SFI_TEAM_NAME_TO_CANONICAL (543 teams)
- [ ] [AGENT] P0. Extend SFI team mapping across years (sample ~1 week per year 2019-2025 via SFI /matches/day/full/) to
      capture promoted/relegated teams. Append to SFI_TEAM_NAME_TO_CANONICAL in UAC
- [ ] [AGENT] P1. Build `resolve_transfermarkt_team()` in UAC (Transfermarkt uses full names, mostly trivial but some
      differ: "1. FC Köln" vs "FC_KOLN")

### 3B: Player Mappings

- [ ] [AGENT] P1. Extract player names from SFI events (goal scorers, cards), Understat (shot-level xG), Transfermarkt
      (player values). Build `sports_reference/mappings/player_mapping.parquet` in GCS
- [ ] [AGENT] P2. Cross-match player names across providers using fuzzy matching + team+league context

### 3C: Season Triggers & Refresh

- [ ] [AGENT] P0. Implement `season_dates.py` in UAC: `get_season_start()`, `get_season_end()`,
      `get_reference_refresh_dates()` for all 33 prediction leagues, 2019-2027
- [ ] [AGENT] P0. Per-league Transfermarkt trigger (currently fetches ALL 33 leagues on ANY trigger date — need
      per-league filtering using UAC transfer windows + season dates)
- [ ] [AGENT] P1. Wire season-start trigger → instruments-service fetches teams from all providers → writes to GCS
      team_mapping.parquet (append + deduplicate)
- [ ] [AGENT] P1. FootyStats season ID auto-refresh: new season IDs change annually, need automatic discovery

**Success criteria:** GCS team_mapping.parquet has all provider columns. Player mapping exists. Season triggers fire
per-league, not all-league.

---

## Phase 4: Data Manifest, Status & Denominators [PARALLEL with Phase 2]

### 4A: Manifest Fixes

- [ ] [SCRIPT] P0. Manifest rescan instruments-service — fixes 496 empty data_type entries, discovers XG/weather/odds
      days
- [ ] [SCRIPT] P0. Manifest rescan MTDS sports — fixes 15,488 empty odds data_type entries
- [ ] [AGENT] P0. Standings migration: add league_id + season columns to pre-2024 standings parquets (no API calls,
      local migration)
- [ ] [AGENT] P1. Per-league partitioning for flat entities still writing without league_id: fixtures, injuries,
      understat_xg, transfermarkt_leagues

### 4B: Data Status Page

- [ ] [AGENT] P0. Validate deployment-UI data status page reads sports availability indexes correctly — check accordion
      hierarchy, league drill-down, provider breakdown
- [ ] [AGENT] P0. Per-field availability dates in UAC: SFI xG available from 2024-03-15 only. Prevents false "missing
      data" alerts for pre-2024 dates
- [ ] [AGENT] P1. Correct denominators per data_type: fixture calendar for match entities, trigger dates for
      Transfermarkt teams, daily for injuries/odds, 6-league subset for Understat
- [ ] [AGENT] P1. League tagging in data status: if a league has no SFI coverage, don't show it as "missing" for SFI
      data types — show "N/A"

**Success criteria:** Data status page shows accurate sports coverage. No false missing-data alerts. Denominators match
actual data availability.

### 4C: Data Status Page Fixes (from Phase 4B audit)

- [ ] [AGENT] P1. Add provider-specific start dates to data status denominator — SFI xG only from 2024-03-15, don't show
      pre-2024 dates as "missing". Use `get_venue_data_type_start_date()` pattern from CeFi for sports entities in
      `deployment-api/deployment_api/services/data_status_service.py`
- [ ] [AGENT] P2. Fix UI label: show "fixtures" not "dates" for sports entity counts. Add `unit` field to
      `TurboLeagueStatus` type in `deployment-ui/src/api/client.ts`
- [ ] [AGENT] P2. Add N/A indicator for uncovered leagues — when a league has FIXTURES but no coverage for a given
      entity (e.g., J-League has no Understat xG), show "N/A" instead of omitting entirely

---

## Phase 5: System-Wide Feature Timestamp PIT Validation [ALL CATEGORIES]

This is NOT sports-specific — applies to CeFi, DeFi, TradFi, and Sports equally. Every feature must carry a source data
timestamp. The feature pipeline must validate that no feature uses data that didn't exist at the feature's evaluation
time.

- [ ] [AGENT] P0. Audit: verify all data sources carry `available_from` or equivalent timestamp in their parquets. For
      sports: FootyStats has `kickoff_utc` (data published ~2-4h pre-match), SFI progressive has `timer` (30s
      resolution), Odds API has per-snapshot timestamps. For CeFi/DeFi: candle close times. For TradFi: market close
      times.
- [ ] [AGENT] P0. UTL/FSS: implement system-wide PIT validation that rejects any feature row where
      source_data_timestamp > feature_evaluation_timestamp. This should be a validation step in the feature pipeline
      base class (UTL `feature_service_base/`), not per-provider logic.
- [ ] [AGENT] P1. Add `data_available_at` column to FootyStats odds/predictions parquets — derived from `kickoff_utc`
      minus publication lead time (~4h for major leagues, ~2h for minor)
- [ ] [AGENT] P1. Add `data_available_at` to SFI progressive — each row already has timer-derived wall clock time
- [ ] [AGENT] P1. Validate across all feature horizons for sports:
  - T-24h: historical form, league position, H2H, Odds API T-24h snapshots
  - T-6h/T-4h/T-2h: above + FootyStats potentials (if published)
  - T-0 (pre-match): above + FootyStats odds + Odds API closing
  - HT: above + SFI progressive at halftime
  - Post-match: all providers
- [ ] [AGENT] P2. Equivalent validation for CeFi features (candle features can't use future candles), DeFi (block
      timestamps), TradFi (market hours)

**Success criteria:** System-wide PIT validation in feature pipeline base. No lookahead bias possible in any category.

---

## Phase 6: Data-Type Sharding & CLI [PARALLEL with Phase 4]

- [ ] [AGENT] P0. Validate `--sports-provider` + `--sports-entity` CLI dimensions work for all 7 providers
- [ ] [AGENT] P0. Data-type level sharding within providers that have multiple types: SFI (PROGRESSIVE + MATCHES +
      STANDINGS), FootyStats (PREDICTIONS + MATCHES + ODDS), API Football (FIXTURES + STATS + LINEUPS + EVENTS +
      INJURIES)
- [ ] [AGENT] P1. Ensure each data_type gets its own manifest entry with correct league_id, venue, data_type columns
- [ ] [AGENT] P1. Validate manifest data_type names are human-readable and consistent across providers (PREDICTIONS not
      FOOTYSTATS_PREDICTIONS — source is the venue column)

**Success criteria:** Can run `--sports-provider SOCCER_FOOTBALL_INFO --sports-entity SFI_PROGRESSIVE` to fetch only
progressive data. Each entity has clean manifest entries.

---

## Phase 7: Live Adapters [AFTER Phase 2]

- [ ] [AGENT] P1. SFI WebSocket integration (Ultra plan includes real-time progressive feed) — wire into
      instruments-service live mode
- [ ] [AGENT] P1. FootyStats live endpoint — same /todays-matches but called at higher frequency (every 5 min pre-match
      window)
- [ ] [AGENT] P2. Validate API Football live fixtures endpoint (already implemented: `GET /fixtures?live=all`, 65 Tier
      0+1 leagues) works end-to-end through features
- [ ] [AGENT] P2. Odds API live — already getting bookmaker-level snapshots, validate they flow into features correctly

**Success criteria:** All 4 live-capable providers have working live adapters. SFI WebSocket streams progressive data in
real-time.

---

## Phase 8: Cross-Category Pipeline Monitoring [PARALLEL, ongoing]

### 8A: CeFi (15 VMs)

- [ ] [SCRIPT] P0. Monitor CeFi VM completion: check logs for each year-shard (Binance Futures/Spot 2020-2025, Bybit
      2021-2025)
- [ ] [SCRIPT] P0. After MTDS completes per year: trigger MDPS candle computation for those dates
- [ ] [SCRIPT] P1. After MDPS completes: trigger features-delta-one-service for CeFi features
- [ ] [SCRIPT] P2. After features: trigger ML training + inference

### 8B: DeFi/TradFi (4 VMs)

- [ ] [SCRIPT] P0. Monitor DeFi backfill VM: validate data quality (block timestamps, gas fees, lending rates)
- [ ] [SCRIPT] P0. Monitor TradFi VM: check CME/Databento completion (T+1 = 2-phase, Databento is T+1 not T+2)
- [ ] [SCRIPT] P1. After MTDS completes: trigger MDPS for DeFi/TradFi candles

### 8C: Sports (4 VMs + SFI pending)

- [ ] [SCRIPT] P0. Monitor understat-backfill: currently at 2022-01-21, ETA ~6 hours to present
- [ ] [SCRIPT] P0. Monitor transfermarkt-backfill: teams per league, ~90s rate limit per league
- [ ] [SCRIPT] P0. Monitor weather-backfill-openmeteo: rate-limited (429s), check progress
- [ ] [SCRIPT] P1. After all enrichment VMs complete: final manifest rescan (instruments + MTDS sports)

### 8D: E2E Validation (all 5 categories)

- [ ] [SCRIPT] P1. CEFI cluster E2E: T+1 single day + live 1h + reconciliation
- [ ] [SCRIPT] P1. SPORTS cluster E2E: T+1 single day + trigger scheduler + feature validation (600+ columns)
- [ ] [SCRIPT] P2. DEFI cluster E2E: T+1 single day
- [ ] [SCRIPT] P2. TRADFI cluster E2E: T+1 single day on weekday (needs DATABENTO_API_KEY)
- [ ] [SCRIPT] P2. PREDICTION cluster E2E: T+1 single day

**Success criteria:** All VMs complete successfully. MDPS triggered for completed MTDS shards. E2E tests pass for all 5
categories.

---

## Phase 9: Schema Validation & Cross-Provider Audit [AFTER Phases 3-5]

- [ ] [AGENT] P1. Validate every parquet column matches UAC schema definition (no orphan columns, no missing required
      columns)
- [ ] [AGENT] P1. Cross-validate FootyStats odds vs Odds API odds for same fixtures (different bookmaker granularity —
      FT has aggregated, OA has per-bookmaker)
- [ ] [AGENT] P1. Cross-validate SFI xG vs Understat xG for same fixtures (SFI from 2024-03-15, Understat from 2019)
- [ ] [AGENT] P2. Cross-validate SFI match stats vs API Football stats vs FootyStats stats (goals, shots, corners should
      match)
- [ ] [AGENT] P2. Null-rate validation per provider per data_type per league — identify leagues with sparse data
- [ ] [AGENT] P2. Audit: ensure we capture EVERY field each provider offers (no dropped columns in normalization)

**Success criteria:** Cross-provider data joins work via canonical_fixture_id. Stats match across providers where
overlapping. No silent data loss.
