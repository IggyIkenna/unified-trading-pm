---
title: "Sports Feature Completion — 857-Feature ML Target"
status: active
priority: P0
created: 2026-04-10
locked_by: live-defi-rollout
locked_since: 2026-04-10
superseded_by: [sports_data_pipeline_comprehensive_2026_04_16.plan.md]
reconciliation_status: superseded
reconciliation_date: 2026-04-25
---

> **SUPERSEDED 2026-04-25 by
> [sports_data_pipeline_comprehensive_2026_04_16.plan.md](./sports_data_pipeline_comprehensive_2026_04_16.plan.md).**
> Some scope shipped via §12.0 Plan 6 + denormalisation §12.1; comprehensive plan + integration_04 own remainder
> Original scope retained for history. See `_reconciliation_evidence_map_2026_04_25.md` for evidence.

# Sports Feature Completion Plan

## Context

The sports ML pipeline targets 857 features across 10 categories (per archive FEATURES_CATALOG.md). Current batch
pipeline produces 586 columns from 16 active calculators. 165 odds features are in a separate exporter (working).
Several calculators exist but are not wired (ht_features, ml_predictions, steam_detector). Multiple data sources
(FootyStats, Understat, fixture_player_stats, injuries, coaches) are NOT being consumed despite adapters existing.

### Current vs Target

| Category    | Target | Implemented | Gap  | Notes                                                                                 |
| ----------- | ------ | ----------- | ---- | ------------------------------------------------------------------------------------- |
| MARKET/Odds | 108    | 165         | +57  | Exceeds target                                                                        |
| TEAM        | 262    | 219         | -43  | team_form(74)+team_goals(63)+team_xg(8)+team_derived(20)+advanced_stats(54)           |
| H2H         | 22     | 53          | +31  | Exceeds target                                                                        |
| LEAGUE      | 27     | 27          | 0    | Complete                                                                              |
| PLAYER      | 4      | 0\*         | -4   | \*player_lineup has 72 cols but PLAYER category is separate                           |
| LINEUP      | 40     | 72          | +32  | Exceeds target                                                                        |
| REFEREE     | 20     | 5           | -15  | Only avg_cards/fouls/penalties/card_rate_band/home_bias                               |
| WEATHER     | 10     | 9           | -1   | Missing precipitation_mm                                                              |
| HT          | 8      | 13          | +5   | But SKIPPED in batch (live-only) — must enable                                        |
| OTHER       | 356    | ~224        | -132 | halftime(116)+multisource_xg(28)+poisson(15)+venue(26)+season(6)+goal_timing(10)+misc |

### Data Source Issues

| Source               | Status                                | Impact                                     |
| -------------------- | ------------------------------------- | ------------------------------------------ |
| fixture_player_stats | In GCS but NOT READ by any calculator | Player features = 0                        |
| injuries             | In GCS but NOT READ                   | Injury impact features = 0                 |
| coaches              | In GCS but NOT READ                   | Manager features = 0                       |
| FootyStats           | Adapter exists, NOT CALLED in batch   | dangerous_attacks, first-half data missing |
| Understat            | Adapter exists, NOT CALLED in batch   | Per-shot xG missing for top 5 leagues      |
| TransferMarkt        | No credentials                        | Squad value features blocked               |
| SoccerInfo           | No credentials                        | Historical player data blocked             |

### Dependency DAG

```
Phase 1 (Data Wiring) ──→ Phase 2 (Team +43) ──→ Phase 4 (Exporter Integration)
                      ├──→ Phase 3 (Referee +15)──→ Phase 4
                      ├──→ Phase 3 (Weather +1) ──→ Phase 4
                      ├──→ Phase 3 (HT batch)   ──→ Phase 4
                      └──→ Phase 3 (Steam wire) ──→ Phase 4
Phase 5 (New calculators) ──→ Phase 4
Phase 6 (FootyStats/Understat) ──→ Phase 4
Phase 4 ──→ Phase 7 (QG) ──→ Phase 8 (Backfill VMs)
```

## Phase 1: Wire Existing GCS Data Into Pipeline [PARALLEL]

Read fixture_player_stats, injuries, and coaches from GCS in derived_features_exporter.py. These tables already exist in
GCS from instruments-service backfill.

- [ ] [AGENT] P0. Add GCS reader for fixture_player_stats in derived_features_exporter.py — read from
      instruments-service GCS path `sports_reference/by_date/day={date}/entity=player_stats/`
- [ ] [AGENT] P0. Add GCS reader for injuries in derived_features_exporter.py — read from
      `sports_reference/by_date/day={date}/entity=injuries/`
- [ ] [AGENT] P0. Add GCS reader for coaches in derived_features_exporter.py — read from
      `sports_reference/by_date/day={date}/entity=coaches/` (may not exist yet — handle gracefully)

## Phase 2: Complete Team Features (219 → 262 = +43 columns) [SEQUENTIAL after Phase 1]

Expand team calculators with missing sub-categories. All use existing fixture_stats/events data.

- [ ] [AGENT] P0. Add pressing metrics to advanced_stats_calculator.py: press_success_rate, high_press_frequency,
      press_recovery_time (home/away = +6 columns)
- [ ] [AGENT] P0. Add counter-attack metrics to team_form.py or new counter_attack_calculator.py:
      counter_attack_frequency, counter_attack_conversion_rate, transition_speed (home/away = +6 columns)
- [ ] [AGENT] P0. Add set-piece features to team_goals.py: corner_conversion_rate, free_kick_conversion_rate,
      set_piece_goals_pct, set_piece_conceded_pct (home/away = +8 columns)
- [ ] [AGENT] P0. Add shot quality features to advanced_stats_calculator.py: shot_quality_avg (xG/shot),
      shot_placement_inside_box_pct, headed_goal_pct (home/away = +6 columns)
- [ ] [AGENT] P0. Add temporal performance to team_form.py: first_15_min_goals_rate, last_15_min_goals_rate,
      second_half_improvement (home/away = +6 columns)
- [ ] [AGENT] P0. Add efficiency metrics to team_derived.py: ppg_vs_xg_expected, xg_overperformance_rolling,
      shot_efficiency_trend (home/away = +6 columns)
- [ ] [AGENT] P1. Add remaining team features to reach 262: possession_efficiency, territory_control_pct,
      progressive_pass_rate (home/away = +5 columns)

## Phase 3: Complete Referee, Weather, HT, Steam [PARALLEL]

- [ ] [AGENT] P0. Expand referee_features.py from 5 → 20 columns: add home_card_rate, away_card_rate,
      penalty_award_rate, yellow_to_red_ratio, second_yellow_rate, card_timing_early/late, foul_to_card_ratio,
      league_specific_card_avg, var_penalty_rate, home_penalty_rate, away_penalty_rate, referee_strictness_score,
      red_card_rate, avg_match_fouls (= +15 columns)
- [ ] [AGENT] P0. Add precipitation_mm to weather_calculator.py WEATHER_COLUMNS — already fetched from Open-Meteo, just
      not in output list (= +1 column)
- [ ] [AGENT] P0. Enable ht_features in batch mode — halftime_calculator already produces HT scores from completed
      fixtures; wire HT_BATCH_COLUMNS into derived_features_exporter (remove the skip, use halftime_calculator output as
      input)
- [ ] [AGENT] P0. Wire steam_detector into odds_features_exporter — SteamMoveSignal fields (steam_detected,
      steam_magnitude, steam_direction, stale_venue_count) should be columns in ODDS_COLUMNS output

## Phase 4: New Feature Calculators [PARALLEL, depends on Phase 1]

- [ ] [AGENT] P0. Create player_stats_calculator.py — reads fixture_player_stats from GCS, computes:
      top_scorer_goals_avg, top_assist_avg, player_rating_variance, key_player_contribution_pct (= 4 PLAYER category
      features)
- [ ] [AGENT] P0. Create manager_calculator.py — reads coaches from GCS, computes: manager_tenure_days,
      manager_win_rate, manager_ppg, manager_is_new (< 90 days), manager_honeymoon_effect, manager_home_bias,
      manager_tactical_flexibility (formation changes), manager_derby_record (home/away = ~20 columns)
- [ ] [AGENT] P0. Create injury_impact_calculator.py — reads injuries from GCS + fixture_player_stats, computes:
      injured_player_value_lost, total_injury_count, key_player_injured, injury_crisis_score, days_avg_injury_duration
      (home/away = ~10 columns)
- [ ] [AGENT] P1. Create travel_calculator.py — uses venue_context coordinates, computes: travel_distance_km (already in
      venue_context), cumulative_travel_last_30d, jet_lag_factor, travel_vs_opponent_ratio, is_european_away_return
      (home/away = ~10 columns)
- [ ] [AGENT] P1. Create elo_calculator.py — implements Elo rating model from historical results, computes: elo_rating,
      elo_diff, elo_expected_score, elo_form_trend, elo_league_adjusted (home/away = ~10 columns)
- [ ] [AGENT] P1. Create formation_calculator.py — reads formation from fixture_lineups, computes:
      formation_attacking_score (exists in player_lineup), formation_change_from_last, formation_h2h_mismatch,
      formation_vs_league_avg (home/away = ~8 columns)
- [ ] [AGENT] P1. Create european_fatigue_calculator.py — detects midweek European matches, computes:
      played_european_midweek, european_travel_distance, days_since_european_match, european_rotation_pct (home/away =
      ~8 columns)

## Phase 5: Wire FootyStats + Understat Into Batch [SEQUENTIAL]

FootyStats needs API key (footystats-api-key in Secret Manager). Understat is public (no auth). Both adapters exist in
instruments-service. Both have fetch handlers in \_fetch_runner.py. Issue: batch pipeline with --skip-fetch reads from
GCS, not live API. Need to ensure reference data from these sources is IN GCS first.

- [ ] [AGENT] P0. Verify FootyStats API key exists in Secret Manager — if not, document as blocker
- [ ] [AGENT] P0. Verify Understat data exists in GCS for backfill dates — Understat is public, instruments-service
      should write it
- [ ] [AGENT] P0. Add FootyStats-specific features to calculators: dangerous_attacks_home/away, dangerous_attacks_diff,
      first_half_pressure_score, footystats_btts_potential, footystats_over25_potential (= ~6 columns from FootyStats
      match data)
- [ ] [AGENT] P0. Ensure multisource_xg_calculator reads Understat xG columns from enriched fixtures — columns
      home_xg_understat/away_xg_understat already defined, verify they get populated

## Phase 6: Integrate All Into Exporter + Output Schema [SEQUENTIAL after Phases 2-5]

- [ ] [AGENT] P0. Wire all new calculators into derived_features_exporter.py — add Groups for: player_stats, manager,
      injury_impact, travel, elo, formation, european_fatigue
- [ ] [AGENT] P0. Update TABLE_SCHEMAS in output_schemas.py — add new columns to derived_features schema
- [ ] [AGENT] P0. Wire promoted_team_handler into team_form calculator — blend features for newly promoted teams with no
      historical data
- [ ] [AGENT] P1. Update ml_predictions.py — either remove stub or implement basic prediction passthrough

## Phase 7: Quality Gates [SEQUENTIAL after Phase 6]

- [ ] [AGENT] P0. Run features-sports-service quality gates:
      `cd features-sports-service && bash scripts/quality-gates.sh`
- [ ] [AGENT] P0. Verify derived_features column count matches target (857 total across both exporters)
- [ ] [AGENT] P0. Run single-date local test:
      `features-sports-service --operation compute --mode batch --date 2025-03-01 --skip-fetch --tables derived_features`

## Phase 8: Backfill VMs [SEQUENTIAL after Phase 7]

- [ ] [SCRIPT] P0. Re-run derived_features backfill with complete feature set:
      `bash launch_fss_phase3_backfill.sh --derived-only` (--skip-existing will only reprocess dates where schema
      changed)
- [ ] [SCRIPT] P0. Verify feature completeness:
      `python scripts/check_pipeline_completeness.py --start-date 2020-06-01 --end-date 2025-07-23`

## Blocked Items (No Credentials)

- [ ] [HUMAN] P2. TransferMarkt API credentials — needed for squad_value features
- [ ] [HUMAN] P2. SoccerInfo API credentials — needed for historical player data
- [ ] [HUMAN] P1. FootyStats API key verification in Secret Manager

## Success Criteria

- [ ] All 857 target features producing non-null values for dates with sufficient data
- [ ] features-sports-service quality gates pass
- [ ] derived_features + odds_features backfill complete for 2020-06-01 → 2025-07-23
- [ ] ML training can begin on full feature set
