---
title: "Trigger-Based Sports Reference Data Refresh"
status: active
priority: P1
created: 2026-04-13
locked_by: live-defi-rollout
locked_since: 2026-04-13
---

# Trigger-Based Sports Reference Data Refresh

## Problem

Three conflated concerns need separating:

1. **Mappings** (teams, leagues, canonical IDs): Accumulating reference files that grow at predictable trigger points (season start, transfer window close, promotion/relegation). Currently re-fetched identically every day — 180+ hours/year wasted on Transfermarkt alone.

2. **Daily source data** (FootyStats predictions, Understat xG, injuries, fixture stats): Date-specific data that SHOULD run daily on fixture dates. Already mostly correct, but FootyStats predictions are rejected wholesale when a few rows have nulls — should write what we have and let downstream handle nulls.

3. **Data status denominator** ("when SHOULD data exist?"): The availability manifest needs to understand trigger calendars to avoid false positives. Transfer data shouldn't show as "missing" outside windows. Fixture-dependent data shouldn't show as "missing" on non-fixture days.

## Current Anti-Patterns

### Mappings: Daily re-fetch of static data
```
# 365 identical copies per year:
sports_reference/by_date/day=2026-04-01/entity=teams/teams.parquet
sports_reference/by_date/day=2026-04-02/entity=teams/teams.parquet  # same
```

### Predictions: Whole-shard rejection for partial nulls
```
# 15 fixtures, 5 missing o25_potential → ALL 15 predictions rejected
ERROR FootyStats predictions shard 2026-04-01 REJECTED — null-rate violations
```

### Data status: False "missing" on non-trigger dates
```
# Transfermarkt shows 2% availability because denominator = every calendar day
# Reality: data only changes 5x/year per league
```

---

## Workstream A: Mapping Reference Files (Trigger-Based)

### A1. Trigger Calendar

Triggers are **per-league** because seasons differ:

| League type | Season span | Triggers |
|-------------|------------|----------|
| European (EPL, La Liga, etc.) | Aug-May | Season start (Aug), winter window close (Feb), summer window open (Jun), summer window close (Sep) |
| MLS | Feb-Oct | Season start (Feb), primary close (May), secondary close (Aug) |
| J-League | Jan-Dec | Season start (Feb), primary close (Apr), secondary close (Aug) |
| Allsvenskan/Eliteserien | Mar-Nov | Season start (Mar), mid-season close (Aug), off-season close (Mar+1) |
| Brasileirao | Apr-Dec | Season start (Apr), primary close (May), secondary close (Aug) |

Transfer window dates: **already in UAC** (`transfer_windows.py`).
Season start dates: **need to add to UAC**.

### A2. Entity Classification

| Entity | Provider(s) | Type | Trigger |
|--------|------------|------|---------|
| Leagues | UAC SSOT (hardcoded) | Static | Never refresh — fixed universe choice |
| Teams per league | API Football, Transfermarkt | Trigger | Season start + promotion/relegation |
| Player values (squad market values) | Transfermarkt | Trigger | Window open + window close |
| Team canonical mappings (API Football ID ↔ canonical ↔ Transfermarkt ID ↔ FootyStats ID) | All providers | Trigger | Same as teams (new teams need mapping) |
| SFI leagues | SoccerFootball.info | Trigger | Season start only (slow-moving) |
| SFI standings | SoccerFootball.info | Weekly | After each match round (not trigger-based, but NOT daily) |

### A3. GCS Target Shape

```
# Accumulating master file (current state, grows with new teams)
sports_reference/master/entity=teams/teams.parquet
sports_reference/master/entity=team_mapping/team_mapping.parquet
sports_reference/master/entity=player_values/player_values.parquet

# Historical snapshots at trigger points (for ML training point-in-time)
sports_reference/snapshots/entity=player_values/season=2025/trigger=winter_close/player_values.parquet
sports_reference/snapshots/entity=teams/season=2025/trigger=season_start/teams.parquet
```

### A4. Historical Backfill Math

- 7 seasons (2019-2026) x ~5 triggers/season x 30 leagues = ~1,050 API calls
- At 1 call/min (Transfermarkt RapidAPI rate limit) = ~17.5 hours one-time
- vs current: 2,000+ days x 30 leagues = 60,000+ calls

---

## Workstream B: Daily Source Data (Already Correct, Minor Fixes)

These entities are date-specific and SHOULD run daily on fixture dates. No refactor needed except:

### B1. Stop rejecting prediction shards for partial nulls

FootyStats predictions currently reject entire shards when some fixtures have null potentials. Lower-league matches legitimately lack some fields. Fix: warn, don't reject. Downstream feature calculators already handle nulls via defaults.

- [x] [CODE] P0. Change `_validate_predictions_null_rates` from reject to warn-and-write (instruments-service)

### B2. Daily entities (no change needed)

| Entity | Provider | Cadence | Status |
|--------|----------|---------|--------|
| Injuries | API Football | Daily | Correct |
| Fixture stats/events/lineups/player_stats | API Football | Per completed fixture | Correct |
| FootyStats predictions | FootyStats | Daily on fixture dates | Correct (after B1 fix) |
| FootyStats matches | FootyStats | Daily on fixture dates | Correct |
| Understat xG | Understat | Daily on fixture dates (6 leagues) | Correct |

---

## Workstream C: Data Status Denominator ("When SHOULD Data Exist?")

The availability manifest denominator must understand:
- **Fixture-dependent data** (predictions, match stats): Expected only on fixture dates → use fixture calendar
- **Transfer-window data** (player values, transfer records): Expected during/after windows → use window calendar
- **Mapping data** (teams, leagues): Expected at trigger dates only → use trigger calendar
- **Daily reference data** (injuries): Expected every day → use calendar days

### C1. Denominator by entity type

| Entity type | Denominator | Source |
|-------------|------------|--------|
| Match data (fixture stats, predictions, xG) | Fixture calendar dates | UAC `get_league_fixture_calendar()` |
| Transfer/squad data (player_values) | Window + 30d grace | UAC `is_transfer_data_expected()` |
| Mappings (teams, team_mapping) | Trigger dates only | UAC trigger calendar (Phase A) |
| Injuries | All calendar days in season | Season start/end from UAC |

- [x] [CODE] P0. Wire `is_transfer_data_expected()` into deployment-api for Transfermarkt entities
- [ ] [CODE] P1. Wire trigger-date denominator for mapping entities (after Phase A)

---

## Dependency DAG

```
Workstream B (daily fixes) ─── independent, do now
    [x] B1: Prediction null-rate warn-not-reject

Workstream C (denominator) ─── partially done
    [x] C1a: Transfer window denominator (deployment-api)
    [ ] C1b: Trigger-date denominator (needs A1)

Workstream A (mappings refactor) ─── main work
    Phase A1: UAC season start calendar
        ↓
    Phase A2: Orchestrator trigger-aware logic
        ↓
    Phase A3: Historical backfill at trigger dates
        ↓
    Phase A4: Wire trigger denominator into data status (C1b)
```

Workstreams B and C1a are done. Workstream A is the remaining substantial work.

---

## Phase A1 — UAC Season Start Calendar

- [ ] [CODE] P0. Add `season_dates.py` to `canonical/domain/sports/` with per-league season start/end dates (2019-2027)
- [ ] [CODE] P0. Public API: `get_season_start(league_id, season_year)`, `get_season_end(league_id, season_year)`
- [ ] [CODE] P0. Add `get_reference_refresh_dates(league_id, year)` — union of season start + all window open/close
- [ ] [CODE] P0. Re-export from `sports/__init__.py` and `sports.py` facade
- [ ] [QG] P0. `bash scripts/quality-gates.sh` on UAC

## Phase A2 — Trigger-Aware Orchestrator

- [ ] [CODE] P0. Add `_is_reference_refresh_date(league_id, date)` check using UAC triggers
- [ ] [CODE] P0. Skip team/player_values fetches when not a trigger date (log skip reason)
- [ ] [CODE] P0. Refactor `_fetch_transfermarkt_data` to accept `season` parameter
- [ ] [CODE] P1. Change GCS write path for mappings: `master/` (append-only) + `snapshots/` (trigger-dated)
- [ ] [CODE] P1. Make team_mapping append-only (read existing, merge new, write back)
- [ ] [QG] P0. `bash scripts/quality-gates.sh` on instruments-service

## Phase A3 — Historical Backfill

- [ ] [CODE] P0. Add `--season` CLI arg to instruments-service
- [ ] [SCRIPT] P0. Backfill script: for each league, for each trigger date 2019-2026, fetch `season=X`
- [ ] [SCRIPT] P1. Run on VM fleet (parallelize by league)
- [ ] [QG] P0. Validate GCS snapshots exist for all trigger dates

## Phase A4 — Trigger Denominator in Data Status

- [ ] [CODE] P1. Add trigger-date denominator for mapping entities in deployment-api
- [ ] [QG] P0. `bash scripts/quality-gates.sh` on deployment-api

---

## Success Criteria

- Transfermarkt API calls drop from ~365/year/league to ~5/year/league
- FootyStats predictions never rejected for partial nulls (warn only)
- ML training has point-in-time squad values at every trigger boundary since 2019
- Live mode: reference data refreshes within 24h of each trigger date
- Data status page: correct availability (expected only at trigger/fixture dates, no false "missing")
- All affected repos QG pass
