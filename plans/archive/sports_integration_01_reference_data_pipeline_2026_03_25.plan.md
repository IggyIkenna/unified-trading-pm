---
doc_type: plan
title: sports-integration-01-reference-data-pipeline
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-25'
remaining_todos_consolidated_into: consolidated_sports_prediction_pipeline_2026_04_15
superseded_by: [consolidated_sports_prediction_pipeline_2026_04_15.plan.md]
reconciliation_status: superseded_by_consolidator
reconciliation_date: 2026-04-25
overview: 'instruments-service --asset-group SPORTS produces ALL reference data with cross-provider

  mapping tables in GCS hive format. Fixes European league season param, adds standings,

  injuries, fixture details, and cross-provider TeamMapping/FixtureMapping tables.

  Downstream services (FSS, ML) use these mappings to resolve provider-specific IDs.

  '
type: code
epic: epic-code-completion
completion_gates: {code: C4, deployment: D1, business: B1}
repo_gates:
- {repo: instruments-service, code: C4, notes: 'DONE: All 9 entity types + mapping tables wired in orchestrator. Season logic fixed.'}
- {repo: instruments-service (reference_data/ sub-package), code: C4, notes: 'DONE: All methods exist on ApiFootballAdapter (fixtures, leagues, teams, standings, injuries, stats, events, lineups, player_stats)'}
- {repo: unified-api-contracts, code: C4, notes: 'DONE: ALL 33/33 leagues have cross-provider mappings. team_mapping.csv (6,245 teams), team_names.py, team_mappings.py all complete.'}
depends_on: [sports-batch-pipeline-end-to-end]
isProject: false
todos:
- {id: p1-fix-season-logic, content: "- [x] [AGENT] P0. Fix instruments-service reference_data api_football get_teams(league_id, season) season calculation.\n  DONE: _effective_season_for_league() uses get_league_by_api_football_id() → season_months[0]\n  to determine start month per league. European Aug-start → year-1 when querying in spring.\n  Calendar-year leagues → current year. File: reference_data/adapters/sports/adapters/api_football.py\n", status: done}
- {id: p2a-standings, content: "- [x] [AGENT] P1. Add fetch_standings(league_id, season) to api_football adapter.\n  DONE: Method exists + orchestrator wired. Writes to entity=standings/.\n", status: done}
- {id: p2b-injuries, content: "- [x] [AGENT] P1. Add fetch_injuries(date) to api_football adapter.\n  DONE: Method exists + orchestrator wired. Writes to entity=injuries/.\n", status: done}
- {id: p2c-fixture-stats, content: "- [x] [AGENT] P1. Add fetch_fixture_stats(fixture_id) to api_football adapter.\n  DONE (2026-04-03): Method exists. Orchestrator wired for completed fixtures\n  (FT/AET/PEN) with 1 req/sec rate limiting. entity=fixture_stats/.\n", status: done}
- {id: p2d-fixture-events, content: "- [x] [AGENT] P1. Add fetch_fixture_events(fixture_id) to api_football adapter.\n  DONE (2026-04-03): Method exists. Orchestrator wired. entity=fixture_events/.\n", status: done}
- {id: p2e-fixture-lineups, content: "- [x] [AGENT] P1. Add fetch_fixture_lineups(fixture_id) to api_football adapter.\n  DONE (2026-04-03): Method exists. Orchestrator wired. entity=fixture_lineups/.\n", status: done}
- {id: p2f-player-stats, content: "- [x] [AGENT] P1. Add fetch_fixture_player_stats(fixture_id) to api_football adapter.\n  DONE (2026-04-03): Method exists. Orchestrator wired. entity=player_stats/.\n", status: done}
- {id: p3a-team-mapping, content: "- [x] [AGENT] P0. Build and dump TeamMapping table to GCS.\n  DONE (2026-03-30): ALL 33/33 leagues now have cross-provider mappings in UAC.\n  team_mapping.csv has 6,245 teams. Odds API team_names.py and API-Football\n  team_mappings.py updated to cover all 33 leagues (including ENG_CHAMPIONSHIP,\n  ENG_LEAGUE_ONE, ENG_LEAGUE_TWO, LIGA_3). Archived mappings (29K teams, 140K\n  fixtures) exist in archive/sports_audit_data/.\n", status: done}
- {id: p3b-fixture-mapping, content: "- [x] [AGENT] P0. Build and dump FixtureMapping table to GCS.\n  DONE (2026-03-30): Fixture mappings exist in archive/sports_audit_data/ (140K fixtures).\n  canonical_fixture_id (human-readable), api_football_fixture_id (numeric),\n  footystats_match_id, understat_match_id, date, home_team_canonical, away_team_canonical.\n", status: done}
- {id: p4-orchestrator-wiring, content: "- [x] [AGENT] P1. Extend _fetch_sports_reference_data() in instruments-service orchestrator.\n  DONE (2026-04-03): All 9 entity types wired: leagues, teams, standings, injuries,\n  fixture_stats, fixture_events, fixture_lineups, player_stats + mapping tables.\n  Per-fixture entities iterate over completed fixtures (FT/AET/PEN) with 1 req/sec.\n  File: instruments_service/engine/orchestrator.py\n", status: done}
- {id: p5-validation, content: "- [ ] [AGENT] P0. Run instruments-service for 2026-03-22 (Saturday with EPL fixtures).\n  Verify ALL entity types written to GCS.\n  Verify TeamMapping has EPL + Bundesliga + La Liga + Serie A + Ligue 1 entries.\n  Verify fixture_stats, fixture_events populated for completed fixtures.\n  QG: cd instruments-service && bash scripts/quality-gates.sh\n", status: pending, blocked_by: p4-orchestrator-wiring}
- {id: p5b-manifest-tracking, content: "- [ ] [AGENT] P0. Verify instruments-service ManifestWriter tracks SPORTS reference data.\n  ManifestWriter already exists in instruments-service orchestrator.\n  Verify: availability_index written for each SPORTS date with entity counts.\n  Verify: --force=True overwrites, --force=False (default) skips existing dates.\n  Run completeness check: all dates 2020-06-01 to 2026-03-28 should have entries\n  after L0 backfill (71/71 chunks done per p8a-l0-reference-backfill in Plan 02).\n", status: pending, blocked_by: p5-validation}
- {id: p6a-one-month-ref-validation, content: "- [ ] [SCRIPT] P0. Validate reference data for 1 month (2025-03-01 to 2025-03-31).\n  Read availability_index from instruments-store-sports bucket.\n  Verify: all 31 dates have entries, all 9 entity types present per matchday.\n  Verify: teams, leagues, standings populated for all 33 prediction leagues.\n  Report gaps. Only proceed to full-period check after 1-month passes.\n", status: pending, blocked_by: p5b-manifest-tracking}
- {id: p6b-full-period-ref-validation, content: "- [ ] [SCRIPT] P0. Validate reference data for full period (2020-06-01 to 2026-03-28).\n  Completeness target: >= 99% of matchdays have reference data in GCS.\n  Report: per-league coverage, per-entity-type coverage, dates with gaps.\n  Flag dates needing --force re-run. Declare done when >= 99% complete.\n", status: pending, blocked_by: p6a-one-month-ref-validation}
---

> **SUPERSEDED 2026-04-25 by
> [consolidated_sports_prediction_pipeline_2026_04_15.plan.md](./consolidated_sports_prediction_pipeline_2026_04_15.plan.md).**
> Original scope retained for history. Frontmatter `remaining_todos_consolidated_into:` was already present; this commit
> formalises it as canonical `superseded_by:` and adds this banner. See `_reconciliation_evidence_map_2026_04_25.md` for
> evidence.

# Sports Integration Plan 1: Reference Data Pipeline

Part of the 6-plan sports integration series. See master plan index at .claude/plans/splendid-percolating-wave.md for
the full dependency DAG.

## Success Criteria

- 9+ entity types written to GCS per date
- 2 mapping tables written (team_mapping, fixture_mapping)
- European league teams returned (season=2025 fix)
- All IDs human-readable
- Manifest tracks 100% of dates with entity counts
- Full period (2020-06-01 to 2026-03-28) >= 99% coverage validated
- --force overwrites existing, default skips (idempotent re-runs)
