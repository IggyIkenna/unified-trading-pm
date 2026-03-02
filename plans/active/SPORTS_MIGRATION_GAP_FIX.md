# Sports Migration Gap Fix Plan

> Follows: SPORTS_BETTING_PREVIOUS_FULL_MIGRATION.md (COMPLETE)
> Date: 2026-03-02
> Status: ACTIVE

## Objective

Fix all remaining gaps identified during the full audit of `sports-betting-services-previous` migration so that the old repo is fully superseded and can be permanently archived.

## Gaps Identified

### P0 — Must Fix
1. **8 canonical tables missing data exporters** — fixture_stats, fixture_events, fixture_lineups, fixture_player_stats, injuries, players, venues (fixture_coaches merged into lineups export)
2. **74 leagues missing from classification registry** — only 20 of 94 leagues migrated

### P1 — Should Fix
3. **Batch fetch shell scripts not migrated** — 4 scripts (~1,439L) for rate-limited bulk data collection
4. **Team/stadium mapping data incomplete** — ~200+ aliases and 50 stadiums not loaded

### P2 — Nice to Have
5. **Feature tracking incomplete** — 533 of 606 features untracked (11 modules missing)
6. **Geocoding CLI not migrated** — venue lat/lon via Google Maps API

### P3 — Low Priority
7. **Round names data** — 210 tournament round names for season context

## Execution Streams (6 parallel + 1 integration)

| Stream | Agent | Priority | Target | Description |
|--------|-------|----------|--------|-------------|
| 1 | A | P0 | features-sports-service | 4 fixture-level data exporters |
| 2 | B | P0 | features-sports-service | 3 standalone data exporters + registry/validation |
| 3 | C | P0 | instruments-service | Expand league classification 20→94 |
| 4 | D | P1 | instruments-service | Team/stadium mapping data |
| 5 | E | P2 | features-sports-service | 11 feature tracking modules |
| 6 | F | P1 | features-sports-service | Batch fetch CLI scripts |
| 7 | G | P2-P3 | both | Geocoding, round names, final verification |

## Done Criteria

- [ ] `get_available_tables()` returns 14 tables (7 existing + 7 new)
- [ ] `_TABLE_CONFIGS` in validation.py has 14 entries
- [ ] `DEFAULT_CLASSIFICATION_REGISTRY.league_count == 94`
- [ ] Team alias resolver loads 56+ teams with cross-provider mappings
- [ ] Feature tracking covers 400+ features across 14 modules
- [ ] Batch fetch CLI accepts all 4 providers with rate limiting
- [ ] All tests pass in features-sports-service and instruments-service
- [ ] basedpyright clean on both repos
