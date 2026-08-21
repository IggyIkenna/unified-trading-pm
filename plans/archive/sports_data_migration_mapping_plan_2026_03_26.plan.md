---
doc_type: plan
title: sports-data-migration-mapping-plan
summary: 'Layered data migration plan for sports pipeline. Maps every data source,

  endpoint, and field to its UTS classification. Migration starts with

  mappings only, then reference data, then odds, then derived features.

  Each layer tested live before proceeding to the next.'
status: superseded
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [instruments-service]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-27'
type: code
epic: epic-code-completion
depends_on: [sports-integration-01-reference-data-pipeline, sports-integration-02-odds-market-data-pipeline, sports-batch-pipeline-end-to-end]
isProject: false
superseded_by: [consolidated_sports_prediction_pipeline_2026_04_15.plan.md]
reconciliation_status: superseded
reconciliation_date: 2026-04-25
---

> **SUPERSEDED 2026-04-25 by
> [consolidated_sports_prediction_pipeline_2026_04_15.plan.md](./consolidated_sports_prediction_pipeline_2026_04_15.plan.md).**
> Deps (sports_integration_01/02 + sports_batch_pipeline) all consolidated; not in §12.0 register Original scope
> retained for history. See `_reconciliation_evidence_map_2026_04_25.md` for evidence.

# Sports Data Migration & Mapping Plan

> **Conflict resolution**: Pass 2-6 (reference data backfill) depend on sports_batch_pipeline Phase 2
> (instruments-service SPORTS hook) being complete. GCS paths must use `source=ODDS_API` format (not `venue=ODDS_API`)
> per sports_e2e_validation adapter rewrite.

## Guiding Principles

1. **Mappings first** — get canonical↔provider ID resolution working before touching any data
2. **Fresh vs backfill** — grab fresh for ~1 month, then compare against backfilled historical
3. **Live-capable** — every endpoint we use for backfill must also work live (flag where it won't)
4. **Documented per provider** — which endpoint, what it returns, where it sits in the classification
5. **Season scope** — most recent complete season (2024-25 for European, 2025 for calendar-year leagues)

---

## Data Classification Hierarchy

```
Layer 0: MAPPINGS (canonical ↔ provider-specific IDs)
         → Must exist before any other layer
         → Rarely changes (per season / per team transfer)
         → Lives in: instruments-store-sports-*/sports_reference/mappings/

Layer 1: REFERENCE DATA (facts that describe the world)
         → Fixtures, leagues, teams, venues, countries
         → Changes: fixtures daily, teams per window, leagues per season
         → Lives in: instruments-store-sports-*/sports_reference/by_date/day={date}/entity={type}/

Layer 2: MARKET TICK DATA (odds = tradeable instruments)
         → Odds snapshots at multiple time horizons, bookmaker prices
         → Needs instrument IDs generated (FOOTBALL:BETFAIR:MATCH_ODDS:...)
         → Changes: continuously (live) or per-snapshot (batch)
         → Lives in: market-data-tick-sports-*/raw_tick_data/by_date/day={date}/venue=ODDS_API/

Layer 3: DERIVED STAGE 1 (stable, factual derivations)
         → League standings, team form (last N results), goal difference
         → Won't change once the match is played
         → Lives in: features-sports-*/by_date/day={date}/

Layer 4: DERIVED STAGE 2 (complex, subjective derivations)
         → xG models, lineup predictions, pressing intensity, weather impact
         → May change with model updates or new data
         → Lives in: features-sports-*/by_date/day={date}/
```

---

## Provider Inventory

### Provider 1: API-Football (api-football.com)

- **Secret**: `api-football-api-key`
- **Adapter**: `instruments_service/reference_data/adapters/api_football.py`
- **Role**: PRIMARY reference data source + fixture details
- **Live feasible**: Yes (1 req/sec free tier, faster on paid)
- **Coverage**: 100% of fixtures (143K), 100% of teams (30K)

| Endpoint                                 | Classification      | Live?               | UTS Destination                     |
| ---------------------------------------- | ------------------- | ------------------- | ----------------------------------- |
| `GET /fixtures?date={YYYY-MM-DD}`        | Layer 1: Reference  | Yes                 | instruments-service → GCS fixtures  |
| `GET /leagues`                           | Layer 1: Reference  | Yes                 | instruments-service → GCS leagues   |
| `GET /teams?league={id}&season={yr}`     | Layer 1: Reference  | Yes                 | instruments-service → GCS teams     |
| `GET /venues`                            | Layer 1: Reference  | Yes                 | instruments-service → GCS venues    |
| `GET /standings?league={id}&season={yr}` | Layer 3: Derived S1 | Yes                 | instruments-service → GCS standings |
| `GET /injuries?date={YYYY-MM-DD}`        | Layer 3: Derived S1 | Yes                 | instruments-service → GCS injuries  |
| `GET /fixtures/statistics?fixture={id}`  | Layer 3: Derived S1 | Yes (post-match)    | FSS → fixture_stats                 |
| `GET /fixtures/events?fixture={id}`      | Layer 3: Derived S1 | Yes (post-match)    | FSS → fixture_events                |
| `GET /fixtures/lineups?fixture={id}`     | Layer 4: Derived S2 | Yes (~1h pre-match) | FSS → lineups                       |
| `GET /fixtures/players?fixture={id}`     | Layer 3: Derived S1 | Yes (post-match)    | FSS → player_stats                  |

**Live notes**: Lineups only available ~60min before kickoff. Post-match stats available ~2h after FT.

### Provider 2: FootyStats (footystats.org)

- **Secret**: `footystats-api-key`
- **Adapter**: `instruments_service/reference_data/adapters/footystats.py`
- **Role**: Enrichment — 215 columns per match (corners, dangerous attacks, xG, cards, first-half splits)
- **Live feasible**: Yes (API updates after each match within hours)
- **Coverage**: 72.8% of fixtures mapped (102K/140K), 21.2% of teams mapped

| Endpoint                    | Classification                       | Live? | UTS Destination        |
| --------------------------- | ------------------------------------ | ----- | ---------------------- |
| `GET /matches?date={date}`  | Layer 3: Derived S1                  | Yes   | FSS → enrichment       |
| `GET /teams?league={id}`    | Layer 0: Mapping (ft_team_id needed) | Yes   | mappings               |
| `GET /players?league={id}`  | Layer 4: Derived S2                  | Yes   | FSS → player features  |
| `GET /referees?league={id}` | Layer 3: Derived S1                  | Yes   | FSS → referee features |

**Key columns (215 total)**:
`team_a_corners, team_b_corners, team_a_shots_on_target, team_a_possession, team_a_xg, team_a_fh_corners` (first-half
specific), `dangerous_attacks_home`, etc. **Mapping dependency**: Needs `ft_team_id` and `ft_match_id` from mapping
table to join with API-Football fixtures.

### Provider 3: Understat (understat.com)

- **Secret**: None (public scraping)
- **Adapter**: `instruments_service/reference_data/adapters/understat.py`
- **Role**: Shot-level xG data (x,y coordinates, situation, shot type)
- **Live feasible**: Partially — data appears ~30min after match, but scraping has no SLA
- **Coverage**: 8.1% of fixtures mapped (11.3K — only 5 leagues: EPL, La Liga, Bundesliga, Serie A, Ligue 1)

| Endpoint                             | Classification      | Live?        | UTS Destination           |
| ------------------------------------ | ------------------- | ------------ | ------------------------- |
| Match xG (`/match/{id}`)             | Layer 4: Derived S2 | ~30min delay | FSS → xG features         |
| Shot data (`/match/{id}`)            | Layer 4: Derived S2 | ~30min delay | FSS → shot model features |
| Team history (`/team/{id}/{season}`) | Layer 3: Derived S1 | Yes          | FSS → team xG history     |
| Player seasons                       | Layer 4: Derived S2 | Yes          | FSS → player xG features  |

**Live notes**: Scraping-based, no official API. Can break if site changes. No guaranteed freshness SLA. **Mapping
dependency**: Needs `us_team_id` and `us_fixture_id` from mapping table.

### Provider 4: Soccer-Football-Info (soccerfootball.info)

- **Secret**: `soccer-football-info-api-key`
- **Adapter**: `instruments_service/reference_data/adapters/soccerfootball_info.py`
- **Role**: Progressive time-series stats (how stats evolve during match), HT data, dominance metrics
- **Live feasible**: Yes (API with key)
- **Coverage**: 38.1% of fixtures mapped (53.6K)

| Endpoint                       | Classification             | Live?            | UTS Destination             |
| ------------------------------ | -------------------------- | ---------------- | --------------------------- |
| `GET /matches?date={date}`     | Layer 1: Reference (basic) | Yes              | FSS → match data            |
| Progressive stats (per-minute) | Layer 4: Derived S2        | Yes (post-match) | FSS → progressive features  |
| Team standings                 | Layer 3: Derived S1        | Yes              | FSS → standings cross-check |
| Manager data                   | Layer 4: Derived S2        | Yes              | FSS → manager features      |

**Key data**: Progressive stats show stat values at different time points during the match — critical for HT feature
calculation. **Mapping dependency**: Needs `sf_team_id` and `sf_fixture_id` from mapping table.

### Provider 5: Transfermarkt (transfermarkt.com)

- **Secret**: `transfermarkt-api-key`
- **Adapter**: `instruments_service/reference_data/adapters/transfermarkt.py`
- **Role**: Player market values, squad composition, transfer history
- **Live feasible**: Partially — valuations update monthly, not real-time
- **Coverage**: 40.8% of teams mapped (12.2K)

| Endpoint         | Classification      | Live?             | UTS Destination                 |
| ---------------- | ------------------- | ----------------- | ------------------------------- |
| Teams by league  | Layer 1: Reference  | Yes (slow-moving) | instruments-service             |
| Players by team  | Layer 4: Derived S2 | Yes (slow-moving) | FSS → player valuation features |
| Transfer history | Layer 4: Derived S2 | Weekly updates    | FSS → squad stability features  |

**Live notes**: Data is slow-moving (monthly valuations). Pre-match use only — not suitable for in-play.

### Provider 6: Open-Meteo (open-meteo.com)

- **Secret**: None (public API)
- **Adapter**: `instruments_service/reference_data/adapters/open_meteo.py`
- **Role**: Weather at stadium location on match day
- **Live feasible**: Yes (free, fast, forecast + historical)
- **Coverage**: Any venue with lat/lon (from venues.csv: 3,445 venues)

| Endpoint           | Classification                 | Live?           | UTS Destination                   |
| ------------------ | ------------------------------ | --------------- | --------------------------------- |
| Historical weather | Layer 3: Derived S1            | Yes             | FSS → weather features            |
| Weather forecast   | Layer 4: Derived S2 (forecast) | Yes (pre-match) | FSS → weather prediction features |

**Mapping dependency**: Needs venue lat/lon from API-Football venues table.

### Provider 7: The Odds API (the-odds-api.com)

- **Secret**: `odds-api-api-key`
- **UMI adapter**: `unified_market_interface/adapters/sports/odds_api_adapter.py`
- **Role**: Bookmaker odds (64 bookmakers, h2h/spreads/totals markets)
- **Live feasible**: Yes (live odds endpoint available, costs credits)
- **Coverage**: Old mapping shows 0% fixture mapping (od_fixture_id was never populated — odds matched by team name +
  date)

| Endpoint                                       | Classification            | Live?      | UTS Destination     |
| ---------------------------------------------- | ------------------------- | ---------- | ------------------- |
| `GET /historical/sports/{key}/odds?date={iso}` | Layer 2: Market tick data | Batch only | MTDS → odds parquet |
| `GET /sports/{key}/odds`                       | Layer 2: Market tick data | Yes (live) | MTDS → live odds    |

**Key**: Odds API uses its own event IDs. Matching to API-Football fixtures is by team name + commence_time, NOT by a
direct ID mapping. This is why `od_fixture_id` was 0% populated — the old system matched by heuristic.

---

## Current Mapping Coverage (from old system)

| Mapping      | Total   | AF   | FT    | US   | SF    | OD    | TM    |
| ------------ | ------- | ---- | ----- | ---- | ----- | ----- | ----- |
| **Teams**    | 29,821  | 100% | 21.2% | 8.5% | 36.9% | 0%    | 40.8% |
| **Fixtures** | 140,483 | 100% | 72.8% | 8.1% | 38.1% | 0%    | -     |
| **Leagues**  | 605     | 100% | 60.5% | 5.8% | 42.5% | 40.5% | 59.0% |

**Key gaps**:

- Odds API (OD): 0% — always matched by name heuristic, never by ID
- Understat: 8.1% — only covers 5 leagues
- FootyStats teams: 21.2% — only prediction-tier leagues

---

## Migration Execution Order

### Pass 1: MAPPINGS ONLY (no data yet)

**Goal**: Get the canonical↔provider mapping tables into GCS so every downstream service can resolve IDs.

- [x] Backfill `team_mapping.parquet` (29.8K rows) → DONE
- [x] Backfill `fixture_mapping.parquet` (140K rows) → DONE
- [x] Backfill `league_mapping.parquet` (605 rows) → DONE
- [x] Backfill `odds_api_team_mapping.parquet` (658 rows) → DONE
- [x] UAC `mapping_resolver.py` reads from GCS at runtime → DONE
- [ ] Verify FSS can read mappings and resolve provider IDs
- [ ] Test live mapping generation: run instruments-service for today, verify new fixtures get mapped
- [ ] Compare fresh mapping vs backfilled mapping for same date

### Pass 2: REFERENCE DATA (fixtures, teams, leagues for season 2024-25)

**Goal**: Backfill the last complete season into instruments-service production paths.

- [ ] Filter fixtures.csv to season=2024 (European) / season=2025 (calendar-year)
- [ ] Partition by date, convert to parquet, write to `sports_reference/by_date/day={date}/entity=fixtures/`
- [ ] Write teams for the season to `sports_reference/by_date/day=all/entity=teams/`
- [ ] Write venues to `sports_reference/by_date/day=all/entity=venues/`
- [ ] Run instruments-service for 1 fresh day, compare output format matches backfill format

### Pass 3: MARKET TICK DATA (odds for season 2024-25)

**Goal**: Backfill odds into MTDS production paths with human-readable instrument IDs.

- [ ] Read odds from v3 bucket for 2024-25 season dates
- [ ] Generate canonical instrument IDs: `FOOTBALL:{bookmaker}:{market}:{league}:{season}:{home}-{away}::{selection}`
- [ ] Add `time_bucket` column (infer from fetch timestamp)
- [ ] Write to `raw_tick_data/by_date/day={date}/venue=ODDS_API/ticks.parquet`
- [ ] Run MTDS for 1 fresh day, compare output format matches backfill format

### Pass 4: DERIVED STAGE 1 (stable derivations for season 2024-25)

**Goal**: Backfill or re-derive standings, fixture_stats, fixture_events from historical data.

- [ ] Standings from API-Football (already in fixture_stats.csv)
- [ ] Fixture stats partitioned by date
- [ ] Fixture events partitioned by date
- [ ] Weather from Open-Meteo (re-fetch for venues with lat/lon)
- [ ] Run FSS for 1 fresh day, compare

### Pass 5: DERIVED STAGE 2 (complex derivations)

**Goal**: Either backfill from old feature parquets OR re-derive using FSS calculators.

- [ ] Decision: use old `football-ml-features-*/version=1/` parquets as-is, or re-derive?
- [ ] If re-derive: run FSS batch for each date in 2024-25 season
- [ ] If backfill: copy old feature parquets into new bucket paths
- [ ] Compare old features vs freshly computed features for same fixtures

### Pass 6: LIVE PIPELINE VALIDATION

**Goal**: Run the full pipeline live for ~1 month, compare with historical.

- [ ] instruments-service: daily run, check fixtures/teams/standings match expected
- [ ] MTDS: daily odds at 4 time buckets, verify instrument IDs
- [ ] FSS: daily feature computation, verify all 6 providers contribute
- [ ] ML inference: generate predictions, compare with historical model output
- [ ] Strategy: paper trade for 1 month

---

## Live Feasibility Summary

| Provider           | Pre-match (T-24h)          | Pre-match (T-1h)     | In-play (HT)        | Post-match                  |
| ------------------ | -------------------------- | -------------------- | ------------------- | --------------------------- |
| **API-Football**   | Fixtures, teams, standings | Lineups (~60min pre) | Live score (paid)   | Stats, events, player stats |
| **FootyStats**     | Historical matches         | -                    | -                   | Match data (~hours)         |
| **Understat**      | Team history               | -                    | -                   | Shot xG (~30min)            |
| **SoccerFootball** | Standings, teams           | -                    | -                   | Progressive stats           |
| **Transfermarkt**  | Squad, valuations          | -                    | -                   | -                           |
| **Open-Meteo**     | Forecast                   | Forecast             | -                   | Historical                  |
| **Odds API**       | Historical odds            | Live odds (credits)  | Live odds (credits) | -                           |

**Flags for live limitations**:

- Understat: scraping-based, no SLA, can break
- FootyStats: post-match only (hours delay), not useful for in-play
- Transfermarkt: monthly updates, pre-match only
- Lineups: only available ~60min before kickoff from API-Football

---

## Season Scope for Migration

**Last complete season**: 2024 (for Aug-start European leagues: 2024-25 season, which ended May 2025) **Current
in-progress season**: 2025 (2025-26, started Aug 2025) **Calendar-year leagues**: 2025 for Brazil/Argentina (Jan-Dec),
last complete = 2024

From fixture distribution:

- Season 2024: 21,242 fixtures
- Season 2025: 20,040 fixtures (in progress)

Migration targets season 2024 first, then backfills 2025 up to today.
