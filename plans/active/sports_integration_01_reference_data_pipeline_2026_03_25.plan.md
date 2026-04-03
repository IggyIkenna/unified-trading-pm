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
    code: C0
    notes: "Extend _fetch_sports_reference_data() for all entity types + mappings"
  - repo: instruments-service (reference_data/ sub-package)
    code: C0
    notes: "Add standings, injuries, fixture details methods to API-Football adapter"
  - repo: instruments-service (reference_data/ sub-package)
    code: C0
    notes: "Fix get_teams() season logic for European leagues"
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
      - [ ] [AGENT] P0. Fix instruments-service reference_data api_football get_teams(league_id, season) season calculation.
        File: instruments_service/reference_data/adapters/api_football.py
        Current: effective_season = season if season is not None else datetime.now().year
        Fix: For Aug-start leagues (European), season = current_year if month >= 8 else current_year - 1.
        For Jan-start leagues (South America, Asia), season = current_year.
        Use LEAGUE_REGISTRY.season_months to determine start month per league.
        Test: adapter.get_teams(39, season=None) should return 20 EPL teams (not 0).
        REMAINING: Season logic fix still needed.
    status: pending

  # ============================================================================
  # PHASE 2 — Add missing instruments-service reference_data fetch methods  [PARALLEL within phase]
  # ============================================================================
  - id: p2a-standings
    content: |
      - [ ] [AGENT] P1. Add fetch_standings(league_id, season) to instruments-service reference_data api_football adapter.
        File: instruments_service/reference_data/adapters/api_football.py
        API endpoint: GET /standings?league={id}&season={year}
        Returns: league table (position, team, points, GD, form)
        Write to GCS: sports_reference/by_date/day={date}/entity=standings/standings.parquet
        REMAINING: Method not yet implemented in instruments-service sports adapters.
    status: pending
  - id: p2b-injuries
    content: |
      - [ ] [AGENT] P1. Add fetch_injuries(date) to instruments-service reference_data api_football adapter.
        API endpoint: GET /injuries?date={YYYY-MM-DD}
        Returns: player injuries with reason, status, return date
        Write to GCS: sports_reference/by_date/day={date}/entity=injuries/injuries.parquet
        REMAINING: Method not yet implemented in instruments-service sports adapters.
    status: pending
  - id: p2c-fixture-stats
    content: |
      - [ ] [AGENT] P1. Add fetch_fixture_stats(fixture_id) to instruments-service reference_data api_football adapter.
        API endpoint: GET /fixtures/statistics?fixture={id}
        Returns: shots, possession, corners, fouls, cards per team
        Write to GCS: sports_reference/by_date/day={date}/entity=fixture_stats/fixture_stats.parquet
    status: pending
  - id: p2d-fixture-events
    content: |
      - [ ] [AGENT] P1. Add fetch_fixture_events(fixture_id) to instruments-service reference_data api_football adapter.
        API endpoint: GET /fixtures/events?fixture={id}
        Returns: goals, cards, substitutions timeline
        Write to GCS: sports_reference/by_date/day={date}/entity=fixture_events/fixture_events.parquet
    status: pending
  - id: p2e-fixture-lineups
    content: |
      - [ ] [AGENT] P1. Add fetch_fixture_lineups(fixture_id) to instruments-service reference_data api_football adapter.
        API endpoint: GET /fixtures/lineups?fixture={id}
        Returns: starting XI, formation, coach
        Write to GCS: sports_reference/by_date/day={date}/entity=fixture_lineups/fixture_lineups.parquet
    status: pending
  - id: p2f-player-stats
    content: |
      - [ ] [AGENT] P1. Add fetch_fixture_player_stats(fixture_id) to instruments-service reference_data api_football adapter.
        API endpoint: GET /fixtures/players?fixture={id}
        Returns: per-player per-match stats (33 fields)
        Write to GCS: sports_reference/by_date/day={date}/entity=player_stats/player_stats.parquet
    status: pending

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
      - [ ] [AGENT] P1. Extend _fetch_sports_reference_data() in instruments-service orchestrator.
        File: instruments_service/engine/orchestrator.py:386
        Currently fetches: leagues, teams
        Add: standings, injuries, fixture_stats, fixture_events, fixture_lineups,
          fixture_player_stats, team_mapping, fixture_mapping
        Each entity writes to hive partition.
        Rate limit: 1 req/sec between API-Football calls.
    status: pending
    blocked_by: p3a-team-mapping, p3b-fixture-mapping

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
