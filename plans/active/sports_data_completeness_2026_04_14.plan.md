---
title: "Sports Data Completeness — Backfill, Denominators, League Breakdowns, Weather, HT Pipeline"
status: active
priority: P0
created: 2026-04-14
locked_by: live-defi-rollout
locked_since: 2026-04-14
---

# Sports Data Completeness

## Context

A massive session (2026-04-13/14) overhauled the sports data pipeline: URDI skip for enrichment entities, canonical
fixture keys with league prefix, rate-limit-aware retries, trigger-based Transfermarkt refresh, per-season GCS paths,
model_dump fixes, v4 manifest writes. 17 backfill processes were launched and may still be running. 5 repos have
uncommitted changes.

**Memory references:**

- `memory/project_sports_backfill_and_trigger_refactor_2026_04_13.md` — full session details
- `memory/project_sports_data_completeness_rules_2026_04_14.md` — per-entity denominator rules, venue coords, injuries
  zero-file, shard dimensions
- `memory/project_sports_remaining_todos_2026_04_14.md` — GCS layout, bucket paths
- `memory/project_manifest_v4_sports_fix_needed.md` — venue vs data_type naming
- `memory/feedback_ht_odds_temporal_filter.md` — HT odds bm_time ±2min buffer rule
- `memory/project_manifest_v4_session2_2026_04_14.md` — other agent's v4 changes (may conflict)

**Plan references:**

- `plans/active/trigger_based_reference_data_2026_04_13.plan.md` — trigger-based refresh architecture

---

## Phase 0 — Stabilize (Reconcile + Commit)

- [x] [CODE] P0. Check if backfill processes completed — all 9 API Football backfills SIGTERM'd at 00:36:38 (killed
      while hitting 429s). Data partial but in GCS.
- [x] [CODE] P0. Reconcile orchestrator.py — both sessions' changes applied sequentially (no conflict). Other agent's
      \_write_venue + \_write_catalogue_record + POLYMARKET shard split all intact.
- [x] [CODE] P0. Strip source prefix from data_type names: all 20+ manifest writes + freshness check expected lists +
      \_ENRICHMENT_ONLY_ENTITIES + \_PER_FIXTURE_ENTITIES + CLI help updated. Also fixed UTL check_shard_freshness to
      check data_type column (was only checking venue — broken for v4 sports).
- [ ] [CODE] P0. Run `rescan_sports_manifest.py --workers 16` with corrected data_type names
- [ ] [QG] P0. Run QG on all 6 repos: UAC, instruments-service, features-sports-service, deployment-api,
      unified-trading-pm, unified-trading-library
- [ ] [CODE] P0. Commit all repos via quickmerge

## Phase 1 — League Breakdowns (PARALLEL)

- [ ] [CODE] P0. Add `league_id=` to manifest writes for: FIXTURE_EVENTS (join fixture→league via fixture_id),
      FIXTURE_STATS, FIXTURE_LINEUPS, PLAYER_STATS, INJURIES (from API Football response), UNDERSTAT_XG (from match
      league field), FOOTYSTATS_PREDICTIONS/MATCHES (from FOOTYSTATS_HISTORICAL_SEASON_IDS reverse map)
- [ ] [CODE] P0. Understat league scoping: data status denominator must only expect data for 6 leagues (EPL, La Liga,
      Bundesliga, Serie A, Ligue 1, RFPL). Use `UNDERSTAT_NAMES` from UAC `provider_league_ids.py`
- [ ] [CODE] P1. Deployment-api: per-data_type denominator rules (fixture calendar for match entities, every day for
      injuries, trigger dates for Transfermarkt, 6-league subset for Understat)

## Phase 2 — Venue Coordinates + Weather (SEQUENTIAL)

- [ ] [CODE] P0. Check archive `new-sports-batting-services` for existing venue/stadium data with coordinates
- [ ] [CODE] P0. Check UAC for venue schemas (search for `venue_latitude`, `stadium`, `CanonicalVenue`)
- [ ] [CODE] P0. Build venue master table: fetch unique venue_id → (lat, lon, name, city, capacity) from API Football
      `/venues` endpoint. ~2,000 unique venues. Write to `sports_reference/master/entity=venues/venues.parquet`
- [ ] [CODE] P0. Update `_fetch_weather_data()` to read venue coords from master table (not from fixtures parquet)
- [ ] [SCRIPT] P1. Weather backfill: run for all fixture dates with known venue coordinates
- [ ] [QG] P0. Run QG on instruments-service

## Phase 3 — Injuries Zero-File + Data Integrity (PARALLEL)

- [ ] [CODE] P0. Injuries: write empty parquet (correct schema, 0 rows) when API Football returns 0 injuries for a date.
      Current behavior: no file written → manifest has no entry → data status flags as missing. Fix: always write, even
      if empty.
- [ ] [CODE] P1. Shard-level failure dimensions: per-date for date entities, per-date×per-league for league-scoped
      entities (Understat — if EPL fails but Bundesliga succeeds, write Bundesliga, fail EPL shard only)

## Phase 4 — SFI Progressive Pipeline (SEQUENTIAL)

- [ ] [CODE] P0. SFI adapter: add `get_progressive_stats(fixture_id)` method. UAC schemas exist:
      `SFMatchProgressiveStatsRaw`, `CanonicalProgressiveStats`. Normalizer exists: `normalize_sfi_progressive_stats()`
- [ ] [CODE] P0. Orchestrator: add `_fetch_sfi_progressive()` function, wire into enrichment flow. Write to
      `entity=ht_stats` or `entity=sf_progressive`
- [ ] [CODE] P0. FSS `halftime_calculator.py` already reads `sf_progressive_df` — verify entity name matches GCS path in
      `gcs_reader.py`
- [ ] [CODE] P1. MTDS/MDPS: HT odds temporal filter using `detect_ht_break_minute()` output. Rule:
      `bm_time > ht_start + 2min AND bm_time < ht_end - 2min`. See `memory/feedback_ht_odds_temporal_filter.md`
- [ ] [SCRIPT] P1. SFI progressive backfill for historical dates

## Phase 5 — FSS League Position + Remaining Backfills (PARALLEL)

- [ ] [CODE] P1. FSS: reconstruct league position at fixture time from standings snapshots. Logic: 3pts/win, 1pt/draw,
      0pts/loss. Only count league matches (not cup/European). Each team plays each other twice per season. Validate: if
      team has more games than (num_teams-1)\*2, wrong matches included. Handle: playoff/split leagues (Belgian,
      Scottish)
- [ ] [SCRIPT] P1. SFI standings backfill (0 dates currently in GCS)
- [ ] [CODE] P2. transfer_records entity: check if Transfermarkt RapidAPI has individual transfer endpoint. If yes, add
      adapter method + orchestrator fetch
- [ ] [QG] P0. Final QG on all affected repos

---

## Success Criteria

- Data status page shows ALL entities (FIXTURES, EVENTS, LINEUPS, STATS, PLAYER_STATS, INJURIES, STANDINGS, LEAGUES,
  TEAMS, XG, PREDICTIONS, MATCHES, PLAYER_VALUES, WEATHER) with correct completion %
- Per-league breakdown visible for every entity that has league context
- No false "missing" flags (injuries on zero-injury days, Understat for non-covered leagues, Transfermarkt on
  non-trigger dates)
- Weather data flowing for fixture dates with known venue coordinates
- SFI progressive data flowing, halftime calculator producing 137 features
- HT odds correctly filtered by actual halftime timing ±2min
- All repos QG pass
