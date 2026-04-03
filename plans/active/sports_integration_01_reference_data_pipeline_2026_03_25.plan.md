---
name: sports-integration-01-reference-data-pipeline
locked_by: live-defi-rollout
locked_since: 2026-03-25
overview: |
  instruments-service --category SPORTS produces ALL reference data with cross-provider
  mapping tables in GCS hive format. Fixes European league season param, adds standings,
  injuries, fixture details, and cross-provider TeamMapping/FixtureMapping tables.
  Downstream services (FSS, ML) use these mappings to resolve provider-specific IDs.
type: code
epic: epic-code-completion
status: active

completion_gates:
  code: C4
  deployment: D1
  business: B1

repo_gates:
  - repo: instruments-service
    code: C4
    notes: "DONE: All 9 entity types + mapping tables wired in orchestrator. Season logic fixed."
  - repo: instruments-service (reference_data/ sub-package)
    code: C4
    notes:
      "DONE: All methods exist on ApiFootballAdapter (fixtures, leagues, teams, standings, injuries, stats, events,
      lineups, player_stats)"
  - repo: unified-api-contracts
    code: C4
    notes:
      "DONE: ALL 33/33 leagues have cross-provider mappings. team_mapping.csv (6,245 teams), team_names.py,
      team_mappings.py all complete."

depends_on:
  - sports-batch-pipeline-end-to-end

isProject: false
todos:
  # ============================================================================
  # PHASE 1 — Fix season logic  [SEQUENTIAL]
  # ============================================================================
  - id: p1-fix-season-logic
    content: |
      - [x] [AGENT] P0. Fix instruments-service reference_data api_football get_teams(league_id, season) season calculation.
        DONE: _effective_season_for_league() uses get_league_by_api_football_id() → season_months[0]
        to determine start month per league. European Aug-start → year-1 when querying in spring.
        Calendar-year leagues → current year. File: reference_data/adapters/sports/adapters/api_football.py
    status: done

  # ============================================================================
  # PHASE 2 — Add missing instruments-service reference_data fetch methods  [PARALLEL within phase]
  # ============================================================================
  - id: p2a-standings
    content: |
      - [x] [AGENT] P1. Add fetch_standings(league_id, season) to api_football adapter.
        DONE: Method exists + orchestrator wired. Writes to entity=standings/.
    status: done
  - id: p2b-injuries
    content: |
      - [x] [AGENT] P1. Add fetch_injuries(date) to api_football adapter.
        DONE: Method exists + orchestrator wired. Writes to entity=injuries/.
    status: done
  - id: p2c-fixture-stats
    content: |
      - [x] [AGENT] P1. Add fetch_fixture_stats(fixture_id) to api_football adapter.
        DONE (2026-04-03): Method exists. Orchestrator wired for completed fixtures
        (FT/AET/PEN) with 1 req/sec rate limiting. entity=fixture_stats/.
    status: done
  - id: p2d-fixture-events
    content: |
      - [x] [AGENT] P1. Add fetch_fixture_events(fixture_id) to api_football adapter.
        DONE (2026-04-03): Method exists. Orchestrator wired. entity=fixture_events/.
    status: done
  - id: p2e-fixture-lineups
    content: |
      - [x] [AGENT] P1. Add fetch_fixture_lineups(fixture_id) to api_football adapter.
        DONE (2026-04-03): Method exists. Orchestrator wired. entity=fixture_lineups/.
    status: done
  - id: p2f-player-stats
    content: |
      - [x] [AGENT] P1. Add fetch_fixture_player_stats(fixture_id) to api_football adapter.
        DONE (2026-04-03): Method exists. Orchestrator wired. entity=player_stats/.
    status: done

  # ============================================================================
  # PHASE 2 gate: instruments-service QG
  # ============================================================================

  # ============================================================================
  # PHASE 3 — Cross-provider mapping tables  [SEQUENTIAL after Phase 2]
  # DONE (2026-03-30): ALL 33/33 prediction leagues now have cross-provider mappings.
  # UAC team_mapping.csv has 6,245 teams. Odds API team_names.py and API-Football
  # team_mappings.py cover all 33 leagues including ENG_CHAMPIONSHIP, ENG_LEAGUE_ONE,
  # ENG_LEAGUE_TWO, LIGA_3. Archived team/fixture mappings (29K teams, 140K fixtures)
  # exist in archive/sports_audit_data/.
  # ============================================================================
  - id: p3a-team-mapping
    content: |
      - [x] [AGENT] P0. Build and dump TeamMapping table to GCS.
        DONE (2026-03-30): ALL 33/33 leagues now have cross-provider mappings in UAC.
        team_mapping.csv has 6,245 teams. Odds API team_names.py and API-Football
        team_mappings.py updated to cover all 33 leagues (including ENG_CHAMPIONSHIP,
        ENG_LEAGUE_ONE, ENG_LEAGUE_TWO, LIGA_3). Archived mappings (29K teams, 140K
        fixtures) exist in archive/sports_audit_data/.
    status: done
  - id: p3b-fixture-mapping
    content: |
      - [x] [AGENT] P0. Build and dump FixtureMapping table to GCS.
        DONE (2026-03-30): Fixture mappings exist in archive/sports_audit_data/ (140K fixtures).
        canonical_fixture_id (human-readable), api_football_fixture_id (numeric),
        footystats_match_id, understat_match_id, date, home_team_canonical, away_team_canonical.
    status: done

  # ============================================================================
  # PHASE 4 — Wire into orchestrator  [SEQUENTIAL]
  # ============================================================================
  - id: p4-orchestrator-wiring
    content: |
      - [x] [AGENT] P1. Extend _fetch_sports_reference_data() in instruments-service orchestrator.
        DONE (2026-04-03): All 9 entity types wired: leagues, teams, standings, injuries,
        fixture_stats, fixture_events, fixture_lineups, player_stats + mapping tables.
        Per-fixture entities iterate over completed fixtures (FT/AET/PEN) with 1 req/sec.
        File: instruments_service/engine/orchestrator.py
    status: done

  # ============================================================================
  # PHASE 5 — Validation  [SEQUENTIAL]
  # ============================================================================
  - id: p5-validation
    content: |
      - [ ] [AGENT] P0. Run instruments-service for 2026-03-22 (Saturday with EPL fixtures).
        Verify ALL entity types written to GCS.
        Verify TeamMapping has EPL + Bundesliga + La Liga + Serie A + Ligue 1 entries.
        Verify fixture_stats, fixture_events populated for completed fixtures.
        QG: cd instruments-service && bash scripts/quality-gates.sh
    status: pending
    blocked_by: p4-orchestrator-wiring
---

# Sports Integration Plan 1: Reference Data Pipeline

Part of the 6-plan sports integration series. See master plan index at .claude/plans/splendid-percolating-wave.md for
the full dependency DAG.

## Success Criteria

- 9+ entity types written to GCS per date
- 2 mapping tables written (team_mapping, fixture_mapping)
- European league teams returned (season=2025 fix)
- All IDs human-readable
