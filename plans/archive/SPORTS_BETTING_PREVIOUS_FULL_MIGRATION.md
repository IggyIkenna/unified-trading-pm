---
doc_type: plan
title: Sports-Betting-Services-Previous — Full Migration Plan
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [instruments-service, market-tick-data-service, unified-api-contracts]
scope: [engineer, admin]
tags: []
related: []
created: "2026-03-02"
---

# Sports-Betting-Services-Previous — Full Migration Plan

> Supersedes: SPORTS_INTEGRATION_PHASE1.md (done), SPORTS_MIGRATION_PHASE2_FULL.md (partially done) Date: 2026-03-02
> Status: COMPLETE (2026-03-02)

## Objective

Migrate **100% of functionality** from `sports-betting-services-previous` into the unified trading system. Migrate **0%
of methodology** — no SQLAlchemy, no PostgreSQL, no `os.getenv()`, no custom logging. Everything follows unified
standards: GCS Parquet, Pydantic schemas in AC, UnifiedCloudConfig, unified-events-interface.

## Source Inventory (46 SQLAlchemy Models → Pydantic Schemas)

### Already Migrated (confirmed working)

| Component               | Old Location                               | New Location                                             | Status  |
| ----------------------- | ------------------------------------------ | -------------------------------------------------------- | ------- |
| 18 feature calculators  | `footballbets/features/`                   | `features-sports-service/calculators/`                   | DONE    |
| 5 data clients          | `footballbets/cli/` + `footballbets/core/` | `features-sports-service/clients/`                       | DONE    |
| Engine + pipeline       | `footballbets/features/pipeline_test.py`   | `features-sports-service/engine.py`                      | DONE    |
| Data loader (SQL→GCS)   | `footballbets/features/data_loader.py`     | `features-sports-service/data/loader.py`                 | DONE    |
| ETL tracking (4 tables) | `CountryETL/LeagueETL/FixtureETL/TeamETL`  | `features-sports-service/etl/state.py` (GCS JSON)        | DONE    |
| Arb vig + detection     | `footballbets/arbitrage/`                  | `features-sports-service/arb/` + AC                      | DONE    |
| 20 bookmaker adapters   | N/A (new)                                  | `unified-sports-execution-interface/`                    | DONE    |
| Core canonical schemas  | N/A (new)                                  | `unified-api-contracts/sports/canonical/`                | DONE    |
| 8 source schema sets    | N/A (new)                                  | `unified-api-contracts/sports/sources/`                  | PARTIAL |
| Config (os.getenv→UCI)  | `footballbets/core/config.py`              | `features-sports-service/config.py` (UnifiedCloudConfig) | DONE    |
| Logging                 | `footballbets/core/logging_service.py`     | `unified-events-interface` (setup_events/log_event)      | DONE    |

### Gap 1: Missing Canonical Schemas in unified-api-contracts

New Pydantic schemas needed in `unified-api-contracts/sports/canonical/`:

| Schema                        | Source Model(s)                  | Key Fields                                                                                                                                                  | File               |
| ----------------------------- | -------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------ |
| `CanonicalFixtureEvent`       | `FixtureEvent`                   | fixture_id, team_id, player_id, minute, extra_time, event_type (goal/card/sub), detail, comments                                                            | `events.py`        |
| `CanonicalLineup`             | `FixtureLineup` + `FixtureCoach` | fixture_id, team_id, formation, coach_name, players (list with position, grid, number, is_substitute)                                                       | `lineup.py`        |
| `CanonicalPlayerMatchStats`   | `FixturePlayerStats` (33 cols)   | fixture_id, player_id, team_id, minutes, rating, captain + shots/goals/assists/passes/tackles/duels/dribbles/fouls/cards/penalty stats                      | `player_stats.py`  |
| `CanonicalInjury`             | `Injury`                         | fixture_id, team_id, player_id, player_name, reason                                                                                                         | `injury.py`        |
| `CanonicalFixtureStatsDetail` | `FixtureStats` (19 cols)         | fixture_id, team_id, shots_on/off/total/blocked/inside/outside, fouls, corners, offsides, possession, passes_total/accurate/pct, cards, xG, goals_prevented | `fixture_stats.py` |
| `CanonicalProgressiveStats`   | `SFMatchProgressiveStats`        | fixture_id, timer_seconds, team, goals/possession/attacks/shots/corners/fouls/cards/subs/dominance at 30s intervals                                         | `progressive.py`   |
| `CanonicalProgressiveOdds`    | `SFMatchProgressiveOdds`         | fixture_id, timer_seconds, 1X2/AH/OU/AC odds + 1H variants at 30s intervals                                                                                 | `progressive.py`   |

Also extend `CanonicalFixture` with: `home_shots_blocked`, `away_shots_blocked`, `home_offsides`, `away_offsides`,
`home_passes_total`, `away_passes_total`, `home_passes_accuracy`, `away_passes_accuracy`.

### Gap 2: Extend Source-Specific Schemas

Each provider's raw API response needs full Pydantic coverage in `unified-api-contracts/sports/sources/`:

**FootyStats** (`sources/footystats/schemas.py`):

- `FTMatchRaw` — ~250 fields: goals, corners, cards, shots, fouls, possession, xG, BTTS, 60+ odds cols, goal timings,
  potentials
- `FTRefereeRaw` — ~75 fields: per-match cards/goals/penalties/BTTS stats
- `FTLeagueStatsRaw` — ~170 fields: league-level aggregates (goals, BTTS, corners, cards, shots, fouls, over/under %)
- `FTWeatherRaw` — wind, temp, pressure, clouds, humidity, lat/lon
- `FTOddsRaw` — market_type, market_option, bookmaker, odds_value
- `FTTeamRaw` — performance_rank, table_position, season stats
- `FTPlayerRaw` — ~55 fields: per-game goal/assist/card/minute stats (home/away/overall)
- `FTLineupRaw`, `FTLineupEventRaw`

**Soccer-Football-Info** (`sources/soccer_football_info/schemas.py`):

- `SFMatchRaw` — ~75 fields: scores (1H/2H/OT/pen), stats, odds (start+kickoff for 1X2/OU/AH)
- `SFMatchEventRaw` — event_type, timer, team
- `SFMatchDominanceRaw` — timer, team_a/b_dominance (30s snapshots)
- `SFMatchProgressiveStatsRaw` — 30s interval stats (~22 fields)
- `SFMatchProgressiveOddsRaw` — 30s interval odds (~27 fields)
- `SFLeagueRaw`, `SFTeamRaw`

**Understat** (`sources/understat/schemas.py`):

- `USTeamHistoryRaw` — per-match xG/xGA/PPDA/deep stats
- `USMatchRaw` — goals, xG, forecast probabilities
- `USPlayerRaw` — games/minutes/goals/assists/shots/xG/xA/xG_chain/xG_buildup
- `USMatchShotRaw` — x/y coordinates, xG per shot, situation, shot_type
- `USMatchRosterRaw` — per-match player xG breakdown
- `USPlayerShotRaw` — per-player shot detail
- `USPlayerMatchRaw` — per-match player stats
- `USPlayerSeasonRaw` — season aggregates

**Odds API** (`sources/odds_api/schemas.py`):

- `ODOddsRaw` — fixture_id, bookmaker_key, market, outcome_name/price/point, measurement_time
- `ODTeamsRaw` — league mapping for team discovery

### Gap 3: League Classification Config → instruments-service

**Source**: `extra/league_classification_config.py` — ~50+ leagues with tier, classification, data source flags
**Target**: `instruments-service/instruments_service/sports/league_registry.py`

Transform Python dict to Pydantic-validated YAML config stored in GCS ConfigStore. Fields: league_id, name, country,
tier (1-3), classification (Prediction/Reference/Features), data_sources (dict of provider→bool).

### Gap 4: Team Aliases & Cross-Provider Mappings → instruments-service

**Source**: `team_name_changes.py`, `footystats_team_mapping.py`, `mapping.py` **Target**:
`instruments-service/instruments_service/sports/team_aliases.py`

Load from GCS Parquet, validate against `TeamMapping` schema from AC.

### Gap 5: Feature Tracking Registry → features-sports-service — COMPLETE

**Source**: `footballbets/features/tracking/` — 14 modules, ~500+ features with status tracking **Target**:
`features-sports-service/features_sports_service/tracking/`

Recreated as Pydantic-based feature registry. Status enum: COMPLETE, DATA_NEEDED, TESTED, BLOCKED, NOT_STARTED. CI
integration: validate declared features match computed output.

**Completed (2026-03-02):** Expanded from 14 → 24 tracking modules, 420 → 998 features. 10 new calculators added
(team_style, manager, referee_interaction, ht_sequencing, schedule_fatigue, promoted_team, market_efficiency,
market_structure, price_dynamics, synthetic_xg). SportsFeatureVector in unified-api-contracts expanded to 1077 fields.
773 tests pass. Status: 614 TESTED, 249 COMPLETE, 77 DATA_NEEDED, 52 NOT_STARTED, 6 BLOCKED.

### Gap 6: Provider CLI Handlers → features-sports-service

**Source**: 8 CLI modules in `footballbets/cli/` **Target**:
`features-sports-service/features_sports_service/cli/handlers/`

| Old CLI                       | New Handler                  | Notes                                            |
| ----------------------------- | ---------------------------- | ------------------------------------------------ |
| `api_football_cli.py`         | `api_football_handler.py`    | Delegates to `clients/api_football/`             |
| `footystats_cli.py`           | `footystats_handler.py`      | Delegates to `clients/footystats/`               |
| `understat_cli.py`            | `understat_handler.py`       | Delegates to `clients/understat/`                |
| `odds_api_cli.py` (579L)      | `odds_handler.py`            | Multi-market, rate-limited, backfill+incremental |
| `soccer_football_info_cli.py` | `soccer_football_handler.py` | Delegates to `clients/soccer_football.py`        |
| `market_tick_data_cli.py`     | SKIP                         | Already in `market-tick-data-service`            |

### Gap 7: Utility Functions → features-sports-service

**Source**: Various utility files in `footballbets/` **Target**:
`features-sports-service/features_sports_service/utils/` or integrated into clients

| Old File                    | Functionality        | Target                                                       |
| --------------------------- | -------------------- | ------------------------------------------------------------ |
| `footystats_analyzers.py`   | Statistical analysis | `features-sports-service/utils/stats.py`                     |
| `footystats_parsers.py`     | Data parsing         | `features-sports-service/clients/footystats/_parsers.py`     |
| `footystats_normalizers.py` | Data normalization   | `features-sports-service/clients/footystats/_normalizers.py` |

### Gap 8: Remaining Feature Calculators (from SPORTS_MIGRATION_PHASE2_FULL.md TODOs)

Items 5-10 from the existing plan are still TODO:

- season_context, goal_timing, venue_context, referee calculators
- Team features (split: team_form, team_goals, team_xg, team_derived)
- h2h, league, odds, halftime, player_lineup, poisson_xg, multisource_xg, advanced_stats

---

## Execution Streams (Parallelizable)

### Stream A — Canonical Schemas (unified-api-contracts, 5 agents parallel)

All independent — no cross-dependencies between schema files.

| Agent | Task                                                  | Files                                                       |
| ----- | ----------------------------------------------------- | ----------------------------------------------------------- |
| A1    | CanonicalFixtureEvent + CanonicalInjury               | `canonical/events.py`, `canonical/injury.py`                |
| A2    | CanonicalLineup (with nested player list)             | `canonical/lineup.py`                                       |
| A3    | CanonicalPlayerMatchStats (33-field Pydantic model)   | `canonical/player_stats.py`                                 |
| A4    | CanonicalFixtureStatsDetail + extend CanonicalFixture | `canonical/fixture_stats.py`, extend `canonical/fixture.py` |
| A5    | CanonicalProgressiveStats + CanonicalProgressiveOdds  | `canonical/progressive.py`                                  |

### Stream B — Source Schemas (unified-api-contracts, 4 agents parallel)

All independent — each provider is a separate directory.

| Agent | Task                                                                                                                                 | Files                                     |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------- |
| B1    | FootyStats full schemas (FTMatch ~250 fields, FTReferee, FTLeagueStats, FTWeather, FTOdds, FTTeam, FTPlayer, FTLineup)               | `sources/footystats/schemas.py`           |
| B2    | Soccer-Football-Info full schemas (SFMatch, SFMatchEvent, SFMatchDominance, SFProgressiveStats, SFProgressiveOdds, SFLeague, SFTeam) | `sources/soccer_football_info/schemas.py` |
| B3    | Understat full schemas (USTeamHistory, USMatch, USPlayer, USMatchShot, USMatchRoster, USPlayerShot, USPlayerMatch, USPlayerSeason)   | `sources/understat/schemas.py`            |
| B4    | Odds API full schemas (ODOdds, ODTeams) + extend existing                                                                            | `sources/odds_api/schemas.py`             |

### Stream C — instruments-service (2 agents parallel)

| Agent | Task                                                              | Files                                           |
| ----- | ----------------------------------------------------------------- | ----------------------------------------------- |
| C1    | League classification registry (Pydantic config, GCS ConfigStore) | `instruments_service/sports/league_registry.py` |
| C2    | Team aliases + cross-provider mapping loader                      | `instruments_service/sports/team_aliases.py`    |

### Stream D — features-sports-service Infrastructure (3 agents parallel)

| Agent | Task                                                    | Files                                                    |
| ----- | ------------------------------------------------------- | -------------------------------------------------------- |
| D1    | Feature tracking registry (14 modules → Pydantic-based) | `features_sports_service/tracking/`                      |
| D2    | CLI handlers (5 provider handlers)                      | `features_sports_service/cli/handlers/`                  |
| D3    | Utility migrations (parsers, normalizers, stats)        | `features_sports_service/utils/` + `clients/footystats/` |

### Stream E — Remaining Feature Calculators (4 agents parallel, after Stream A)

Depends on Stream A for any new canonical schemas, but calculators are independent of each other.

| Agent | Task                                                                     |
| ----- | ------------------------------------------------------------------------ |
| E1    | season_context + goal_timing + venue_context + referee calculators       |
| E2    | Team features split (team_form, team_goals, team_xg, team_derived)       |
| E3    | h2h + league + odds + halftime calculators                               |
| E4    | player_lineup + poisson_xg + multisource_xg + advanced_stats calculators |

### Stream F — Tests (parallel with each stream)

Each agent above writes unit tests alongside implementation. No separate test stream needed.

---

## Data Migration (Post-Code, Separate Execution)

After all code is migrated, a data migration script will:

1. Export existing PostgreSQL data to Parquet (or use existing GCS data)
2. Transform through new Pydantic schemas for validation
3. Write to new GCS path structure
4. Verify round-trip integrity

---

## Done Criteria

- [x] All 46 old SQLAlchemy models have Pydantic equivalents (canonical or source-specific)
- [x] `unified-api-contracts/sports/canonical/` has: fixture, events, lineup, player_stats, injury, fixture_stats,
      progressive, odds, features, betting, arbitrage, bookmaker, mappings, processed_odds
- [x] `unified-api-contracts/sports/sources/` has full schemas for: api_football, footystats, soccer_football_info,
      understat, odds_api, open_meteo, betfair, pinnacle
- [x] All 18 feature calculators pass unit tests in features-sports-service
- [x] Feature tracking registry validates all declared features are computed
- [x] 5 CLI handlers operational in features-sports-service
- [x] League registry in instruments-service with 20 leagues
- [x] Team aliases in instruments-service
- [x] Zero imports from sports-betting-services-previous anywhere in workspace
- [x] sports-betting-services-previous moved to archive/

## Key Files

- `archive/sports-betting-services-previous/footballbets/core/models.py` — source of truth for old data model (2309
  lines, 46 models) [ARCHIVED]
- `unified-api-contracts/unified_api_contracts/sports/` — target for all schemas
- `features-sports-service/` — target for feature logic, clients, CLI, tracking
- `instruments-service/instruments_service/sports/` — target for league registry, team aliases
- `unified-trading-/codex/04-architecture/sports-integration-plan.md` — architectural decisions
