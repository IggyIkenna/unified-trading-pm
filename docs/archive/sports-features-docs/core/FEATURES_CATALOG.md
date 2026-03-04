## Features Catalog (Authoritative List)

### Purpose

This file enumerates **every feature header** and defines its **type**, **horizon**, and **math/definition** at a minimum level required for unambiguous implementation.

Cross references:

- Processing + provider + CLI contract: `sports-betting-service/docs/PROCESSING_PROVIDERS_AND_CLI.md`
- Implementation nuances (rolling windows, priors, HT sequencing): `sports-betting-service/docs/FEATURES_IMPLEMENTATION_GUIDE.md`
- Domain guides: `sports-betting-service/docs/FEATURES_DOMAIN_GUIDES.md`

### Naming conventions (critical for `models.py`)

- Canonical feature names are **lowercase snake_case**.
- Line-based families are expanded into explicit column-safe names:
  - Asian handicap line `-0.5` becomes `_m0_5` and `+0.5` becomes `_p0_5`.
  - Totals line `2.5` becomes `_2_5` (no sign prefix).
- Example: `odds_ah_m0_5_home`, `odds_total_2_5_over`.

### Generated on

- 2025-12-13T09:20:26.834869+00:00

### MARKET features (108)

- Rationale + nuances: see `FEATURES_DOMAIN_GUIDES.md` and `FEATURES_IMPLEMENTATION_GUIDE.md`.

| Feature                       | Type  | Horizon | Definition/Math (minimum)                                            |
| ----------------------------- | ----- | ------- | -------------------------------------------------------------------- |
| `accel_home_1h_to_0`          | float | Pregame | accel = velocity_late - velocity_early                               |
| `accel_home_6h_to_1h`         | float | Pregame | accel = velocity_late - velocity_early                               |
| `book_fragmentation_away`     | float | Pregame | See domain guide + implementation guide for definition               |
| `book_fragmentation_home`     | float | Pregame | See domain guide + implementation guide for definition               |
| `gap_max_vs_pinnacle_away`    | float | Pregame | See domain guide + implementation guide for definition               |
| `gap_max_vs_pinnacle_draw`    | float | Pregame | See domain guide + implementation guide for definition               |
| `gap_max_vs_pinnacle_home`    | float | Pregame | See domain guide + implementation guide for definition               |
| `market_confidence`           | float | Pregame | See domain guide + implementation guide for definition               |
| `market_confidence_score`     | float | Pregame | See domain guide + implementation guide for definition               |
| `market_entropy`              | float | Pregame | See domain guide + implementation guide for definition               |
| `market_maturity_score`       | float | Pregame | See domain guide + implementation guide for definition               |
| `market_xg_disagreement_away` | float | Pregame | See domain guide + implementation guide for definition               |
| `market_xg_disagreement_home` | float | Pregame | See domain guide + implementation guide for definition               |
| `max_odds_away`               | float | Pregame | See domain guide + implementation guide for definition               |
| `max_odds_book_home`          | str   | Pregame | See domain guide + implementation guide for definition               |
| `max_odds_draw`               | float | Pregame | See domain guide + implementation guide for definition               |
| `max_odds_home`               | float | Pregame | See domain guide + implementation guide for definition               |
| `min_odds_home`               | float | Pregame | See domain guide + implementation guide for definition               |
| `odds_ah_0_away`              | float | Pregame | Observed odds at horizon (provider/bookmaker dependent)              |
| `odds_ah_0_home`              | float | Pregame | Observed odds at horizon (provider/bookmaker dependent)              |
| `odds_ah_m0_5_away`           | float | Pregame | Observed odds at horizon (provider/bookmaker dependent)              |
| `odds_ah_m0_5_home`           | float | Pregame | Observed odds at horizon (provider/bookmaker dependent)              |
| `odds_ah_m1_5_away`           | float | Pregame | Observed odds at horizon (provider/bookmaker dependent)              |
| `odds_ah_m1_5_home`           | float | Pregame | Observed odds at horizon (provider/bookmaker dependent)              |
| `odds_ah_m1_away`             | float | Pregame | Observed odds at horizon (provider/bookmaker dependent)              |
| `odds_ah_m1_home`             | float | Pregame | Observed odds at horizon (provider/bookmaker dependent)              |
| `odds_ah_m2_away`             | float | Pregame | Observed odds at horizon (provider/bookmaker dependent)              |
| `odds_ah_m2_home`             | float | Pregame | Observed odds at horizon (provider/bookmaker dependent)              |
| `odds_ah_p0_5_away`           | float | Pregame | Observed odds at horizon (provider/bookmaker dependent)              |
| `odds_ah_p0_5_home`           | float | Pregame | Observed odds at horizon (provider/bookmaker dependent)              |
| `odds_ah_p1_5_away`           | float | Pregame | Observed odds at horizon (provider/bookmaker dependent)              |
| `odds_ah_p1_5_home`           | float | Pregame | Observed odds at horizon (provider/bookmaker dependent)              |
| `odds_ah_p1_away`             | float | Pregame | Observed odds at horizon (provider/bookmaker dependent)              |
| `odds_ah_p1_home`             | float | Pregame | Observed odds at horizon (provider/bookmaker dependent)              |
| `odds_ah_p2_away`             | float | Pregame | Observed odds at horizon (provider/bookmaker dependent)              |
| `odds_ah_p2_home`             | float | Pregame | Observed odds at horizon (provider/bookmaker dependent)              |
| `odds_ft_1`                   | float | Pregame | Observed odds at horizon (provider/bookmaker dependent)              |
| `odds_ft_1_prob`              | float | Pregame | Implied probability derived from odds (vig-adjusted where specified) |
| `odds_ft_2`                   | float | Pregame | Observed odds at horizon (provider/bookmaker dependent)              |
| `odds_ft_2_prob`              | float | Pregame | Implied probability derived from odds (vig-adjusted where specified) |
| `odds_ft_over25`              | float | Pregame | Observed odds at horizon (provider/bookmaker dependent)              |
| `odds_ft_under25`             | float | Pregame | Observed odds at horizon (provider/bookmaker dependent)              |
| `odds_ft_x`                   | float | Pregame | Observed odds at horizon (provider/bookmaker dependent)              |
| `odds_h2h_away`               | float | Pregame | Observed odds at horizon (provider/bookmaker dependent)              |
| `odds_h2h_away_pinnacle`      | float | Pregame | Observed odds at horizon (provider/bookmaker dependent)              |
| `odds_h2h_away_prob`          | float | Pregame | Implied probability derived from odds (vig-adjusted where specified) |
| `odds_h2h_draw`               | float | Pregame | Observed odds at horizon (provider/bookmaker dependent)              |
| `odds_h2h_draw_pinnacle`      | float | Pregame | Observed odds at horizon (provider/bookmaker dependent)              |
| `odds_h2h_draw_prob`          | float | Pregame | Implied probability derived from odds (vig-adjusted where specified) |
| `odds_h2h_home`               | float | Pregame | Observed odds at horizon (provider/bookmaker dependent)              |
| `odds_h2h_home_pinnacle`      | float | Pregame | Observed odds at horizon (provider/bookmaker dependent)              |
| `odds_h2h_home_prob`          | float | Pregame | Implied probability derived from odds (vig-adjusted where specified) |
| `odds_h2h_max_vig`            | float | Pregame | vig = sum(implied_probs) - 1 (or per-market variant)                 |
| `odds_h2h_min_vig`            | float | Pregame | vig = sum(implied_probs) - 1 (or per-market variant)                 |
| `odds_h2h_vig`                | float | Pregame | vig = sum(implied_probs) - 1 (or per-market variant)                 |
| `odds_range_away`             | float | Pregame | Observed odds at horizon (provider/bookmaker dependent)              |
| `odds_range_draw`             | float | Pregame | Observed odds at horizon (provider/bookmaker dependent)              |
| `odds_range_home`             | float | Pregame | Observed odds at horizon (provider/bookmaker dependent)              |
| `odds_stability_score`        | float | Pregame | Observed odds at horizon (provider/bookmaker dependent)              |
| `odds_total_0_5_over`         | float | Pregame | Observed odds at horizon (provider/bookmaker dependent)              |
| `odds_total_0_5_under`        | float | Pregame | Observed odds at horizon (provider/bookmaker dependent)              |
| `odds_total_1_5_over`         | float | Pregame | Observed odds at horizon (provider/bookmaker dependent)              |
| `odds_total_1_5_under`        | float | Pregame | Observed odds at horizon (provider/bookmaker dependent)              |
| `odds_total_2_5_over`         | float | Pregame | Observed odds at horizon (provider/bookmaker dependent)              |
| `odds_total_2_5_under`        | float | Pregame | Observed odds at horizon (provider/bookmaker dependent)              |
| `odds_total_3_5_over`         | float | Pregame | Observed odds at horizon (provider/bookmaker dependent)              |
| `odds_total_3_5_under`        | float | Pregame | Observed odds at horizon (provider/bookmaker dependent)              |
| `odds_total_4_5_over`         | float | Pregame | Observed odds at horizon (provider/bookmaker dependent)              |
| `odds_total_4_5_under`        | float | Pregame | Observed odds at horizon (provider/bookmaker dependent)              |
| `odds_total_5_5_over`         | float | Pregame | Observed odds at horizon (provider/bookmaker dependent)              |
| `odds_total_5_5_under`        | float | Pregame | Observed odds at horizon (provider/bookmaker dependent)              |
| `pinnacle_away`               | float | Pregame | See domain guide + implementation guide for definition               |
| `pinnacle_draw`               | float | Pregame | See domain guide + implementation guide for definition               |
| `pinnacle_home`               | float | Pregame | See domain guide + implementation guide for definition               |
| `pinnacle_lead_time_away`     | float | Pregame | See domain guide + implementation guide for definition               |
| `pinnacle_lead_time_home`     | float | Pregame | See domain guide + implementation guide for definition               |
| `pinnacle_vs_market_away`     | float | Pregame | See domain guide + implementation guide for definition               |
| `pinnacle_vs_market_home`     | float | Pregame | See domain guide + implementation guide for definition               |
| `pinnacle_weight`             | float | Pregame | See domain guide + implementation guide for definition               |
| `sharp_book_available`        | str   | Pregame | See domain guide + implementation guide for definition               |
| `sharp_book_count`            | str   | Pregame | See domain guide + implementation guide for definition               |
| `sharp_consensus_away`        | float | Pregame | See domain guide + implementation guide for definition               |
| `sharp_consensus_home`        | float | Pregame | See domain guide + implementation guide for definition               |
| `sharp_soft_delta_away`       | float | Pregame | See domain guide + implementation guide for definition               |
| `sharp_soft_delta_home`       | float | Pregame | See domain guide + implementation guide for definition               |
| `sharp_soft_spread`           | float | Pregame | See domain guide + implementation guide for definition               |
| `sharp_vs_all_weight`         | float | Pregame | See domain guide + implementation guide for definition               |
| `soft_book_count`             | str   | Pregame | See domain guide + implementation guide for definition               |
| `soft_book_value_home`        | str   | Pregame | See domain guide + implementation guide for definition               |
| `soft_consensus_away`         | float | Pregame | See domain guide + implementation guide for definition               |
| `soft_consensus_home`         | float | Pregame | See domain guide + implementation guide for definition               |
| `steam_detected_away`         | float | Pregame | See domain guide + implementation guide for definition               |
| `steam_detected_home`         | float | Pregame | See domain guide + implementation guide for definition               |
| `steam_magnitude_away`        | float | Pregame | See domain guide + implementation guide for definition               |
| `steam_magnitude_home`        | float | Pregame | See domain guide + implementation guide for definition               |
| `steam_timing_away`           | float | Pregame | See domain guide + implementation guide for definition               |
| `steam_timing_home`           | float | Pregame | See domain guide + implementation guide for definition               |
| `velocity_home_10m_to_0`      | float | Pregame | velocity = Δprob / Δtime between snapshot windows                    |
| `velocity_home_24h_to_6h`     | float | Pregame | velocity = Δprob / Δtime between snapshot windows                    |
| `velocity_home_30m_to_10m`    | float | Pregame | velocity = Δprob / Δtime between snapshot windows                    |
| `velocity_home_6h_to_90m`     | float | Pregame | velocity = Δprob / Δtime between snapshot windows                    |
| `velocity_home_72h_to_24h`    | float | Pregame | velocity = Δprob / Δtime between snapshot windows                    |
| `velocity_home_90m_to_30m`    | float | Pregame | velocity = Δprob / Δtime between snapshot windows                    |
| `volatility_adjusted_edge`    | float | Pregame | Std dev of probability deltas over a window                          |
| `volatility_away_24h`         | float | Pregame | Std dev of probability deltas over a window                          |
| `volatility_draw_24h`         | float | Pregame | Std dev of probability deltas over a window                          |
| `volatility_home_24h`         | float | Pregame | Std dev of probability deltas over a window                          |
| `volatility_ratio_home_away`  | float | Pregame | Std dev of probability deltas over a window                          |

### LEAGUE features (27)

| Feature                                   | Type  | Horizon | Definition/Math (minimum)                              |
| ----------------------------------------- | ----- | ------- | ------------------------------------------------------ |
| `league_avg_away_goals`                   | float | Pregame | See domain guide + implementation guide for definition |
| `league_avg_goals`                        | float | Pregame | See domain guide + implementation guide for definition |
| `league_avg_home_goals`                   | float | Pregame | See domain guide + implementation guide for definition |
| `league_avg_margin`                       | float | Pregame | See domain guide + implementation guide for definition |
| `league_betfair_liquidity`                | float | Pregame | See domain guide + implementation guide for definition |
| `league_bookmaker_count`                  | int   | Pregame | See domain guide + implementation guide for definition |
| `league_closing_line_accuracy`            | float | Pregame | See domain guide + implementation guide for definition |
| `league_defense_index`                    | float | Pregame | See domain guide + implementation guide for definition |
| `league_efficiency_score`                 | float | Pregame | See domain guide + implementation guide for definition |
| `league_goal_variance`                    | float | Pregame | See domain guide + implementation guide for definition |
| `league_id`                               | float | Pregame | See domain guide + implementation guide for definition |
| `league_liquidity_tier`                   | int   | Pregame | See domain guide + implementation guide for definition |
| `league_model_r2`                         | float | Pregame | See domain guide + implementation guide for definition |
| `league_normalized_attack_strength_away`  | float | Pregame | See domain guide + implementation guide for definition |
| `league_normalized_attack_strength_home`  | float | Pregame | See domain guide + implementation guide for definition |
| `league_normalized_defense_strength_away` | float | Pregame | See domain guide + implementation guide for definition |
| `league_normalized_defense_strength_home` | float | Pregame | See domain guide + implementation guide for definition |
| `league_odds_variance_away`               | float | Pregame | See domain guide + implementation guide for definition |
| `league_odds_variance_home`               | float | Pregame | See domain guide + implementation guide for definition |
| `league_offense_index`                    | float | Pregame | See domain guide + implementation guide for definition |
| `league_pace`                             | float | Pregame | See domain guide + implementation guide for definition |
| `league_physicality`                      | float | Pregame | See domain guide + implementation guide for definition |
| `league_pinnacle_available`               | int   | Pregame | See domain guide + implementation guide for definition |
| `league_ref_bias`                         | float | Pregame | See domain guide + implementation guide for definition |
| `league_sharp_book_coverage`              | str   | Pregame | See domain guide + implementation guide for definition |
| `league_steam_frequency`                  | float | Pregame | See domain guide + implementation guide for definition |
| `league_tier`                             | int   | Pregame | See domain guide + implementation guide for definition |

### TEAM features (262)

- Rationale + nuances: see `FEATURES_DOMAIN_GUIDES.md` and `FEATURES_IMPLEMENTATION_GUIDE.md`.

| Feature                             | Type  | Horizon | Definition/Math (minimum)                                      |
| ----------------------------------- | ----- | ------- | -------------------------------------------------------------- |
| `away_aerial_dominance`             | float | Pregame | See domain guide + implementation guide for definition         |
| `away_attack_directness`            | float | Pregame | See domain guide + implementation guide for definition         |
| `away_attack_value_missing`         | float | Pregame | See domain guide + implementation guide for definition         |
| `away_attack_variance`              | float | Pregame | See domain guide + implementation guide for definition         |
| `away_attack_width`                 | float | Pregame | See domain guide + implementation guide for definition         |
| `away_big_chance_pct`               | float | Pregame | See domain guide + implementation guide for definition         |
| `away_cards_under_referee`          | float | Pregame | See domain guide + implementation guide for definition         |
| `away_cards_vs_ref_avg`             | float | Pregame | See domain guide + implementation guide for definition         |
| `away_congestion_score`             | float | Pregame | See domain guide + implementation guide for definition         |
| `away_counter_attack_ratio`         | float | Pregame | Ratio of corresponding values (epsilon guard)                  |
| `away_cross_reliance`               | float | Pregame | See domain guide + implementation guide for definition         |
| `away_dangerous_attacks_avg`        | float | Pregame | See domain guide + implementation guide for definition         |
| `away_days_rest`                    | float | Pregame | See domain guide + implementation guide for definition         |
| `away_days_since_manager_change`    | float | Pregame | See domain guide + implementation guide for definition         |
| `away_def_avg_height_cm`            | float | Pregame | See domain guide + implementation guide for definition         |
| `away_def_line_rating`              | float | Pregame | See domain guide + implementation guide for definition         |
| `away_def_line_value`               | float | Pregame | See domain guide + implementation guide for definition         |
| `away_def_quality_drop`             | float | Pregame | See domain guide + implementation guide for definition         |
| `away_defense_variance`             | float | Pregame | See domain guide + implementation guide for definition         |
| `away_defensive_block_height`       | float | Pregame | See domain guide + implementation guide for definition         |
| `away_elo`                          | float | Pregame | See domain guide + implementation guide for definition         |
| `away_form_points`                  | float | Pregame | See domain guide + implementation guide for definition         |
| `away_form_string`                  | str   | Pregame | See domain guide + implementation guide for definition         |
| `away_form_trend`                   | float | Pregame | See domain guide + implementation guide for definition         |
| `away_formation`                    | float | Pregame | See domain guide + implementation guide for definition         |
| `away_foul_propensity`              | float | Pregame | See domain guide + implementation guide for definition         |
| `away_fwd_line_rating`              | float | Pregame | See domain guide + implementation guide for definition         |
| `away_fwd_line_value`               | float | Pregame | See domain guide + implementation guide for definition         |
| `away_fwd_quality_drop`             | float | Pregame | See domain guide + implementation guide for definition         |
| `away_fwd_xg_per90`                 | float | Pregame | See domain guide + implementation guide for definition         |
| `away_game_control`                 | float | Pregame | See domain guide + implementation guide for definition         |
| `away_games_last_14d`               | float | Pregame | See domain guide + implementation guide for definition         |
| `away_games_last_21d`               | float | Pregame | See domain guide + implementation guide for definition         |
| `away_games_under_manager`          | float | Pregame | See domain guide + implementation guide for definition         |
| `away_gk_rating`                    | float | Pregame | See domain guide + implementation guide for definition         |
| `away_goals_conceded_avg`           | float | Pregame | See domain guide + implementation guide for definition         |
| `away_goals_conceded_last1`         | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `away_goals_conceded_last3`         | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `away_goals_conceded_last5`         | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `away_goals_conceded_season`        | float | Pregame | Mean over season-to-date matches (as-of cutoff applied)        |
| `away_goals_ewma_30d`               | float | Pregame | EWMA with previous-season prior (half-life per suffix)         |
| `away_goals_last1`                  | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `away_goals_last3`                  | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `away_goals_last5`                  | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `away_goals_momentum`               | float | Pregame | See domain guide + implementation guide for definition         |
| `away_goals_season`                 | float | Pregame | Mean over season-to-date matches (as-of cutoff applied)        |
| `away_goals_std_last10`             | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `away_goals_vs_league`              | float | Pregame | See domain guide + implementation guide for definition         |
| `away_interception_rate`            | float | Pregame | See domain guide + implementation guide for definition         |
| `away_key_absentees_count`          | int   | Pregame | See domain guide + implementation guide for definition         |
| `away_key_players_missing`          | float | Pregame | See domain guide + implementation guide for definition         |
| `away_last_travel_km`               | float | Pregame | See domain guide + implementation guide for definition         |
| `away_manager_attack_style`         | float | Pregame | See domain guide + implementation guide for definition         |
| `away_manager_avg_possession`       | float | Pregame | See domain guide + implementation guide for definition         |
| `away_manager_avg_ppda`             | float | Pregame | See domain guide + implementation guide for definition         |
| `away_manager_clean_sheet_rate`     | float | Pregame | See domain guide + implementation guide for definition         |
| `away_manager_defensive_style`      | float | Pregame | See domain guide + implementation guide for definition         |
| `away_manager_goals_per_game`       | float | Pregame | See domain guide + implementation guide for definition         |
| `away_manager_honeymoon`            | float | Pregame | See domain guide + implementation guide for definition         |
| `away_manager_ppg_last5`            | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `away_manager_set_piece_focus`      | float | Pregame | See domain guide + implementation guide for definition         |
| `away_manager_tier`                 | int   | Pregame | See domain guide + implementation guide for definition         |
| `away_manager_win_rate`             | float | Pregame | See domain guide + implementation guide for definition         |
| `away_manager_xg_diff_last5`        | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `away_match_tempo`                  | float | Pregame | See domain guide + implementation guide for definition         |
| `away_mid_line_rating`              | float | Pregame | See domain guide + implementation guide for definition         |
| `away_mid_line_value`               | float | Pregame | See domain guide + implementation guide for definition         |
| `away_midweek_european`             | float | Pregame | See domain guide + implementation guide for definition         |
| `away_new_manager_flag`             | int   | Pregame | See domain guide + implementation guide for definition         |
| `away_pass_tempo`                   | float | Pregame | See domain guide + implementation guide for definition         |
| `away_pen_box_entries`              | float | Pregame | See domain guide + implementation guide for definition         |
| `away_pen_won_rate`                 | float | Pregame | See domain guide + implementation guide for definition         |
| `away_played_continental_last_week` | float | Pregame | See domain guide + implementation guide for definition         |
| `away_possession_ewma_30d`          | float | Pregame | EWMA with previous-season prior (half-life per suffix)         |
| `away_possession_last1`             | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `away_possession_last3`             | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `away_possession_last5`             | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `away_possession_season`            | float | Pregame | Mean over season-to-date matches (as-of cutoff applied)        |
| `away_possession_style`             | float | Pregame | See domain guide + implementation guide for definition         |
| `away_possession_trend`             | float | Pregame | See domain guide + implementation guide for definition         |
| `away_ppda_style`                   | float | Pregame | See domain guide + implementation guide for definition         |
| `away_ppg_last3`                    | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `away_ppg_last5`                    | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `away_ppg_season`                   | float | Pregame | Mean over season-to-date matches (as-of cutoff applied)        |
| `away_predictability`               | float | Pregame | See domain guide + implementation guide for definition         |
| `away_prev_goals_conceded`          | float | Pregame | See domain guide + implementation guide for definition         |
| `away_prev_goals_scored`            | float | Pregame | See domain guide + implementation guide for definition         |
| `away_prev_opponent_strength`       | float | Pregame | See domain guide + implementation guide for definition         |
| `away_prev_result`                  | float | Pregame | See domain guide + implementation guide for definition         |
| `away_prev_was_home`                | float | Pregame | See domain guide + implementation guide for definition         |
| `away_prev_xg`                      | float | Pregame | See domain guide + implementation guide for definition         |
| `away_red_risk_with_ref`            | float | Pregame | See domain guide + implementation guide for definition         |
| `away_response_when_ahead`          | float | Pregame | See domain guide + implementation guide for definition         |
| `away_response_when_behind`         | float | Pregame | See domain guide + implementation guide for definition         |
| `away_set_piece_reliance`           | float | Pregame | See domain guide + implementation guide for definition         |
| `away_short_rest`                   | float | Pregame | See domain guide + implementation guide for definition         |
| `away_shot_volume_style`            | float | Pregame | See domain guide + implementation guide for definition         |
| `away_shots_accuracy_avg`           | float | Pregame | See domain guide + implementation guide for definition         |
| `away_shots_blocked_pct`            | float | Pregame | See domain guide + implementation guide for definition         |
| `away_shots_conceded_last5`         | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `away_shots_conceded_season`        | float | Pregame | Mean over season-to-date matches (as-of cutoff applied)        |
| `away_shots_last1`                  | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `away_shots_last3`                  | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `away_shots_last5`                  | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `away_shots_season`                 | float | Pregame | Mean over season-to-date matches (as-of cutoff applied)        |
| `away_sot_pct_last5`                | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `away_sot_pct_season`               | float | Pregame | Mean over season-to-date matches (as-of cutoff applied)        |
| `away_squad_avg_value`              | float | Pregame | See domain guide + implementation guide for definition         |
| `away_squad_total_value`            | float | Pregame | See domain guide + implementation guide for definition         |
| `away_tackle_aggression`            | float | Pregame | See domain guide + implementation guide for definition         |
| `away_team_id`                      | float | Pregame | See domain guide + implementation guide for definition         |
| `away_top_assister_in_xi`           | float | Pregame | See domain guide + implementation guide for definition         |
| `away_top_scorer_in_xi`             | float | Pregame | See domain guide + implementation guide for definition         |
| `away_top_xg_player_in_xi`          | float | Pregame | See domain guide + implementation guide for definition         |
| `away_total_travel_14d`             | float | Pregame | See domain guide + implementation guide for definition         |
| `away_transition_speed`             | float | Pregame | See domain guide + implementation guide for definition         |
| `away_travel_band`                  | str   | Pregame | See domain guide + implementation guide for definition         |
| `away_travel_km`                    | float | Pregame | See domain guide + implementation guide for definition         |
| `away_value_lost_to_injury`         | float | Pregame | See domain guide + implementation guide for definition         |
| `away_xg_avg`                       | float | Pregame | See domain guide + implementation guide for definition         |
| `away_xg_ewma_30d`                  | float | Pregame | EWMA with previous-season prior (half-life per suffix)         |
| `away_xg_ewma_90d`                  | float | Pregame | EWMA with previous-season prior (half-life per suffix)         |
| `away_xg_last1`                     | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `away_xg_last3`                     | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `away_xg_last5`                     | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `away_xg_momentum`                  | float | Pregame | See domain guide + implementation guide for definition         |
| `away_xg_per_shot`                  | float | Pregame | See domain guide + implementation guide for definition         |
| `away_xg_season`                    | float | Pregame | Mean over season-to-date matches (as-of cutoff applied)        |
| `away_xga_last1`                    | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `away_xga_last3`                    | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `away_xga_last5`                    | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `away_xga_season`                   | float | Pregame | Mean over season-to-date matches (as-of cutoff applied)        |
| `home_aerial_dominance`             | float | Pregame | See domain guide + implementation guide for definition         |
| `home_attack_directness`            | float | Pregame | See domain guide + implementation guide for definition         |
| `home_attack_value_missing`         | float | Pregame | See domain guide + implementation guide for definition         |
| `home_attack_variance`              | float | Pregame | See domain guide + implementation guide for definition         |
| `home_attack_width`                 | float | Pregame | See domain guide + implementation guide for definition         |
| `home_big_chance_pct`               | float | Pregame | See domain guide + implementation guide for definition         |
| `home_cards_under_referee`          | float | Pregame | See domain guide + implementation guide for definition         |
| `home_cards_vs_ref_avg`             | float | Pregame | See domain guide + implementation guide for definition         |
| `home_congestion_score`             | float | Pregame | See domain guide + implementation guide for definition         |
| `home_counter_attack_ratio`         | float | Pregame | Ratio of corresponding values (epsilon guard)                  |
| `home_cross_reliance`               | float | Pregame | See domain guide + implementation guide for definition         |
| `home_dangerous_attacks_avg`        | float | Pregame | See domain guide + implementation guide for definition         |
| `home_days_rest`                    | float | Pregame | See domain guide + implementation guide for definition         |
| `home_days_since_manager_change`    | float | Pregame | See domain guide + implementation guide for definition         |
| `home_def_avg_height_cm`            | float | Pregame | See domain guide + implementation guide for definition         |
| `home_def_line_rating`              | float | Pregame | See domain guide + implementation guide for definition         |
| `home_def_line_value`               | float | Pregame | See domain guide + implementation guide for definition         |
| `home_def_quality_drop`             | float | Pregame | See domain guide + implementation guide for definition         |
| `home_defense_variance`             | float | Pregame | See domain guide + implementation guide for definition         |
| `home_defensive_block_height`       | float | Pregame | See domain guide + implementation guide for definition         |
| `home_elo`                          | float | Pregame | See domain guide + implementation guide for definition         |
| `home_form_points`                  | float | Pregame | See domain guide + implementation guide for definition         |
| `home_form_string`                  | str   | Pregame | See domain guide + implementation guide for definition         |
| `home_form_trend`                   | float | Pregame | See domain guide + implementation guide for definition         |
| `home_formation`                    | float | Pregame | See domain guide + implementation guide for definition         |
| `home_foul_propensity`              | float | Pregame | See domain guide + implementation guide for definition         |
| `home_fwd_line_rating`              | float | Pregame | See domain guide + implementation guide for definition         |
| `home_fwd_line_value`               | float | Pregame | See domain guide + implementation guide for definition         |
| `home_fwd_quality_drop`             | float | Pregame | See domain guide + implementation guide for definition         |
| `home_fwd_xg_per90`                 | float | Pregame | See domain guide + implementation guide for definition         |
| `home_game_control`                 | float | Pregame | See domain guide + implementation guide for definition         |
| `home_games_last_14d`               | float | Pregame | See domain guide + implementation guide for definition         |
| `home_games_last_21d`               | float | Pregame | See domain guide + implementation guide for definition         |
| `home_games_under_manager`          | float | Pregame | See domain guide + implementation guide for definition         |
| `home_gk_rating`                    | float | Pregame | See domain guide + implementation guide for definition         |
| `home_goals_conceded_avg`           | float | Pregame | See domain guide + implementation guide for definition         |
| `home_goals_conceded_last1`         | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `home_goals_conceded_last3`         | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `home_goals_conceded_last5`         | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `home_goals_conceded_season`        | float | Pregame | Mean over season-to-date matches (as-of cutoff applied)        |
| `home_goals_ewma_30d`               | float | Pregame | EWMA with previous-season prior (half-life per suffix)         |
| `home_goals_last1`                  | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `home_goals_last3`                  | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `home_goals_last5`                  | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `home_goals_momentum`               | float | Pregame | See domain guide + implementation guide for definition         |
| `home_goals_season`                 | float | Pregame | Mean over season-to-date matches (as-of cutoff applied)        |
| `home_goals_std_last10`             | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `home_goals_vs_league`              | float | Pregame | See domain guide + implementation guide for definition         |
| `home_interception_rate`            | float | Pregame | See domain guide + implementation guide for definition         |
| `home_key_absentees_count`          | int   | Pregame | See domain guide + implementation guide for definition         |
| `home_key_players_missing`          | float | Pregame | See domain guide + implementation guide for definition         |
| `home_last_travel_km`               | float | Pregame | See domain guide + implementation guide for definition         |
| `home_manager_attack_style`         | float | Pregame | See domain guide + implementation guide for definition         |
| `home_manager_avg_possession`       | float | Pregame | See domain guide + implementation guide for definition         |
| `home_manager_avg_ppda`             | float | Pregame | See domain guide + implementation guide for definition         |
| `home_manager_clean_sheet_rate`     | float | Pregame | See domain guide + implementation guide for definition         |
| `home_manager_defensive_style`      | float | Pregame | See domain guide + implementation guide for definition         |
| `home_manager_goals_per_game`       | float | Pregame | See domain guide + implementation guide for definition         |
| `home_manager_honeymoon`            | float | Pregame | See domain guide + implementation guide for definition         |
| `home_manager_ppg_last5`            | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `home_manager_set_piece_focus`      | float | Pregame | See domain guide + implementation guide for definition         |
| `home_manager_tier`                 | int   | Pregame | See domain guide + implementation guide for definition         |
| `home_manager_win_rate`             | float | Pregame | See domain guide + implementation guide for definition         |
| `home_manager_xg_diff_last5`        | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `home_match_tempo`                  | float | Pregame | See domain guide + implementation guide for definition         |
| `home_mid_line_rating`              | float | Pregame | See domain guide + implementation guide for definition         |
| `home_mid_line_value`               | float | Pregame | See domain guide + implementation guide for definition         |
| `home_midweek_european`             | float | Pregame | See domain guide + implementation guide for definition         |
| `home_new_manager_flag`             | int   | Pregame | See domain guide + implementation guide for definition         |
| `home_pass_tempo`                   | float | Pregame | See domain guide + implementation guide for definition         |
| `home_pen_box_entries`              | float | Pregame | See domain guide + implementation guide for definition         |
| `home_pen_won_rate`                 | float | Pregame | See domain guide + implementation guide for definition         |
| `home_played_continental_last_week` | float | Pregame | See domain guide + implementation guide for definition         |
| `home_possession_ewma_30d`          | float | Pregame | EWMA with previous-season prior (half-life per suffix)         |
| `home_possession_last1`             | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `home_possession_last3`             | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `home_possession_last5`             | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `home_possession_season`            | float | Pregame | Mean over season-to-date matches (as-of cutoff applied)        |
| `home_possession_style`             | float | Pregame | See domain guide + implementation guide for definition         |
| `home_possession_trend`             | float | Pregame | See domain guide + implementation guide for definition         |
| `home_ppda_style`                   | float | Pregame | See domain guide + implementation guide for definition         |
| `home_ppg_last3`                    | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `home_ppg_last5`                    | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `home_ppg_season`                   | float | Pregame | Mean over season-to-date matches (as-of cutoff applied)        |
| `home_predictability`               | float | Pregame | See domain guide + implementation guide for definition         |
| `home_prev_goals_conceded`          | float | Pregame | See domain guide + implementation guide for definition         |
| `home_prev_goals_scored`            | float | Pregame | See domain guide + implementation guide for definition         |
| `home_prev_opponent_strength`       | float | Pregame | See domain guide + implementation guide for definition         |
| `home_prev_result`                  | float | Pregame | See domain guide + implementation guide for definition         |
| `home_prev_was_home`                | float | Pregame | See domain guide + implementation guide for definition         |
| `home_prev_xg`                      | float | Pregame | See domain guide + implementation guide for definition         |
| `home_red_risk_with_ref`            | float | Pregame | See domain guide + implementation guide for definition         |
| `home_response_when_ahead`          | float | Pregame | See domain guide + implementation guide for definition         |
| `home_response_when_behind`         | float | Pregame | See domain guide + implementation guide for definition         |
| `home_set_piece_reliance`           | float | Pregame | See domain guide + implementation guide for definition         |
| `home_short_rest`                   | float | Pregame | See domain guide + implementation guide for definition         |
| `home_shot_volume_style`            | float | Pregame | See domain guide + implementation guide for definition         |
| `home_shots_accuracy_avg`           | float | Pregame | See domain guide + implementation guide for definition         |
| `home_shots_blocked_pct`            | float | Pregame | See domain guide + implementation guide for definition         |
| `home_shots_conceded_last5`         | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `home_shots_conceded_season`        | float | Pregame | Mean over season-to-date matches (as-of cutoff applied)        |
| `home_shots_last1`                  | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `home_shots_last3`                  | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `home_shots_last5`                  | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `home_shots_season`                 | float | Pregame | Mean over season-to-date matches (as-of cutoff applied)        |
| `home_sot_pct_last5`                | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `home_sot_pct_season`               | float | Pregame | Mean over season-to-date matches (as-of cutoff applied)        |
| `home_squad_avg_value`              | float | Pregame | See domain guide + implementation guide for definition         |
| `home_squad_total_value`            | float | Pregame | See domain guide + implementation guide for definition         |
| `home_tackle_aggression`            | float | Pregame | See domain guide + implementation guide for definition         |
| `home_team_id`                      | float | Pregame | See domain guide + implementation guide for definition         |
| `home_top_assister_in_xi`           | float | Pregame | See domain guide + implementation guide for definition         |
| `home_top_scorer_in_xi`             | float | Pregame | See domain guide + implementation guide for definition         |
| `home_top_xg_player_in_xi`          | float | Pregame | See domain guide + implementation guide for definition         |
| `home_total_travel_14d`             | float | Pregame | See domain guide + implementation guide for definition         |
| `home_transition_speed`             | float | Pregame | See domain guide + implementation guide for definition         |
| `home_value_lost_to_injury`         | float | Pregame | See domain guide + implementation guide for definition         |
| `home_xg_avg`                       | float | Pregame | See domain guide + implementation guide for definition         |
| `home_xg_ewma_30d`                  | float | Pregame | EWMA with previous-season prior (half-life per suffix)         |
| `home_xg_ewma_90d`                  | float | Pregame | EWMA with previous-season prior (half-life per suffix)         |
| `home_xg_last1`                     | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `home_xg_last3`                     | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `home_xg_last5`                     | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `home_xg_momentum`                  | float | Pregame | See domain guide + implementation guide for definition         |
| `home_xg_per_shot`                  | float | Pregame | See domain guide + implementation guide for definition         |
| `home_xg_season`                    | float | Pregame | Mean over season-to-date matches (as-of cutoff applied)        |
| `home_xga_last1`                    | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `home_xga_last3`                    | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `home_xga_last5`                    | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `home_xga_season`                   | float | Pregame | Mean over season-to-date matches (as-of cutoff applied)        |

### H2H features (20)

| Feature                       | Type  | Horizon | Definition/Math (minimum)                              |
| ----------------------------- | ----- | ------- | ------------------------------------------------------ |
| `h2h_matches_total`           | float | Pregame | See domain guide + implementation guide for definition |
| `h2h_away_wins`               | int   | Pregame | See domain guide + implementation guide for definition |
| `h2h_home_wins`               | int   | Pregame | See domain guide + implementation guide for definition |
| `h2h_draws`                   | int   | Pregame | See domain guide + implementation guide for definition |
| `h2h_home_win_pct`            | float | Pregame | See domain guide + implementation guide for definition |
| `h2h_away_win_pct`            | float | Pregame | See domain guide + implementation guide for definition |
| `h2h_goals_away_avg`          | float | Pregame | See domain guide + implementation guide for definition |
| `h2h_goals_home_avg`          | float | Pregame | See domain guide + implementation guide for definition |
| `h2h_total_goals_avg`         | float | Pregame | See domain guide + implementation guide for definition |
| `h2h_last_result`             | float | Pregame | See domain guide + implementation guide for definition |
| `h2h_last_score_away`         | float | Pregame | See domain guide + implementation guide for definition |
| `h2h_last_score_home`         | float | Pregame | See domain guide + implementation guide for definition |
| `h2h_matches_last5y`          | float | Pregame | See domain guide + implementation guide for definition |
| `h2h_btts_pct`                | float | Pregame | See domain guide + implementation guide for definition |
| `h2h_over25_pct`              | float | Pregame | See domain guide + implementation guide for definition |
| `h2h_days_since_last`         | float | Pregame | See domain guide + implementation guide for definition |
| `h2h_home_at_home_venue_wins` | int   | Pregame | See domain guide + implementation guide for definition |
| `h2h_away_at_home_venue_wins` | int   | Pregame | See domain guide + implementation guide for definition |
| `h2h_possession_away_avg`     | float | Pregame | See domain guide + implementation guide for definition |
| `h2h_possession_home_avg`     | float | Pregame | See domain guide + implementation guide for definition |
| `h2h_xg_away_avg`             | float | Pregame | See domain guide + implementation guide for definition |
| `h2h_xg_home_avg`             | float | Pregame | See domain guide + implementation guide for definition |

### PLAYER features (4)

| Feature                         | Type  | Horizon | Definition/Math (minimum)                              |
| ------------------------------- | ----- | ------- | ------------------------------------------------------ |
| `player_advantage`              | float | Pregame | See domain guide + implementation guide for definition |
| `player_aggregated_defense`     | float | Pregame | See domain guide + implementation guide for definition |
| `player_aggregated_value_ratio` | float | Pregame | Ratio of corresponding values (epsilon guard)          |
| `player_aggregated_xg_for`      | float | Pregame | See domain guide + implementation guide for definition |

### LINEUP features (40)

- Rationale + nuances: see `FEATURES_DOMAIN_GUIDES.md` and `FEATURES_IMPLEMENTATION_GUIDE.md`.

| Feature                           | Type  | Horizon | Definition/Math (minimum)                               |
| --------------------------------- | ----- | ------- | ------------------------------------------------------- |
| `away_xi_aerial_won_pct`          | float | Pregame | See domain guide + implementation guide for definition  |
| `away_xi_assists_season`          | float | Pregame | Mean over season-to-date matches (as-of cutoff applied) |
| `away_xi_avg_rating`              | float | Pregame | See domain guide + implementation guide for definition  |
| `away_xi_avg_value`               | float | Pregame | See domain guide + implementation guide for definition  |
| `away_xi_blocks_per90_avg`        | float | Pregame | See domain guide + implementation guide for definition  |
| `away_xi_clearances_per90_avg`    | float | Pregame | See domain guide + implementation guide for definition  |
| `away_xi_goals_season`            | float | Pregame | Mean over season-to-date matches (as-of cutoff applied) |
| `away_xi_interceptions_per90_avg` | float | Pregame | See domain guide + implementation guide for definition  |
| `away_xi_stability`               | float | Pregame | See domain guide + implementation guide for definition  |
| `away_xi_tackles_per90_avg`       | float | Pregame | See domain guide + implementation guide for definition  |
| `away_xi_total_value`             | float | Pregame | See domain guide + implementation guide for definition  |
| `away_xi_xg_per90_avg`            | float | Pregame | See domain guide + implementation guide for definition  |
| `formation_attacking_ratio`       | float | Pregame | Ratio of corresponding values (epsilon guard)           |
| `formation_away`                  | float | Pregame | See domain guide + implementation guide for definition  |
| `formation_differs_from_usual`    | float | Pregame | See domain guide + implementation guide for definition  |
| `formation_home`                  | float | Pregame | See domain guide + implementation guide for definition  |
| `home_xi_aerial_won_pct`          | float | Pregame | See domain guide + implementation guide for definition  |
| `home_xi_assists_season`          | float | Pregame | Mean over season-to-date matches (as-of cutoff applied) |
| `home_xi_attack_xg_avg`           | float | Pregame | See domain guide + implementation guide for definition  |
| `home_xi_avg_age`                 | float | Pregame | See domain guide + implementation guide for definition  |
| `home_xi_avg_rating`              | float | Pregame | See domain guide + implementation guide for definition  |
| `home_xi_avg_value`               | float | Pregame | See domain guide + implementation guide for definition  |
| `home_xi_blocks_per90_avg`        | float | Pregame | See domain guide + implementation guide for definition  |
| `home_xi_clearances_per90_avg`    | float | Pregame | See domain guide + implementation guide for definition  |
| `home_xi_goals_season`            | float | Pregame | Mean over season-to-date matches (as-of cutoff applied) |
| `home_xi_interceptions_per90_avg` | float | Pregame | See domain guide + implementation guide for definition  |
| `home_xi_stability`               | float | Pregame | See domain guide + implementation guide for definition  |
| `home_xi_tackles_per90_avg`       | float | Pregame | See domain guide + implementation guide for definition  |
| `home_xi_total_value`             | float | Pregame | See domain guide + implementation guide for definition  |
| `home_xi_xg_per90_avg`            | float | Pregame | See domain guide + implementation guide for definition  |
| `lineup_available`                | int   | Pregame | See domain guide + implementation guide for definition  |
| `lineup_source`                   | float | Pregame | See domain guide + implementation guide for definition  |
| `xi_aerial_won_pct`               | float | Pregame | See domain guide + implementation guide for definition  |
| `xi_blocks_per90_avg`             | float | Pregame | See domain guide + implementation guide for definition  |
| `xi_clearances_per90_avg`         | float | Pregame | See domain guide + implementation guide for definition  |
| `xi_interceptions_per90_avg`      | float | Pregame | See domain guide + implementation guide for definition  |
| `xi_rating_diff`                  | float | Pregame | Difference between corresponding values                 |
| `xi_tackles_per90_avg`            | float | Pregame | See domain guide + implementation guide for definition  |
| `xi_value_ratio`                  | float | Pregame | Ratio of corresponding values (epsilon guard)           |
| `xi_value_vs_league_avg`          | float | Pregame | See domain guide + implementation guide for definition  |

### REFEREE features (20)

- Rationale + nuances: see `FEATURES_DOMAIN_GUIDES.md` and `FEATURES_IMPLEMENTATION_GUIDE.md`.

| Feature                          | Type  | Horizon | Definition/Math (minimum)                              |
| -------------------------------- | ----- | ------- | ------------------------------------------------------ |
| `ref_away_result_with_away_team` | float | Pregame | See domain guide + implementation guide for definition |
| `ref_bias_differential`          | float | Pregame | See domain guide + implementation guide for definition |
| `ref_bias_toward_home`           | float | Pregame | See domain guide + implementation guide for definition |
| `ref_historical_favor_away`      | float | Pregame | See domain guide + implementation guide for definition |
| `ref_historical_favor_home`      | float | Pregame | See domain guide + implementation guide for definition |
| `ref_home_result_with_home_team` | float | Pregame | See domain guide + implementation guide for definition |
| `ref_pen_propensity`             | float | Pregame | See domain guide + implementation guide for definition |
| `ref_team_card_chemistry`        | float | Pregame | See domain guide + implementation guide for definition |
| `ref_team_card_chemistry_away`   | float | Pregame | See domain guide + implementation guide for definition |
| `ref_team_card_chemistry_home`   | float | Pregame | See domain guide + implementation guide for definition |
| `ref_tolerance_x_away_fouls`     | float | Pregame | See domain guide + implementation guide for definition |
| `ref_tolerance_x_home_fouls`     | float | Pregame | See domain guide + implementation guide for definition |
| `ref_tolerance_x_team_fouls`     | float | Pregame | See domain guide + implementation guide for definition |
| `referee_avg_cards`              | float | Pregame | See domain guide + implementation guide for definition |
| `referee_avg_fouls`              | float | Pregame | See domain guide + implementation guide for definition |
| `referee_avg_penalties`          | float | Pregame | See domain guide + implementation guide for definition |
| `referee_card_rate_band`         | str   | Pregame | See domain guide + implementation guide for definition |
| `referee_home_bias`              | float | Pregame | See domain guide + implementation guide for definition |
| `referee_id`                     | float | Pregame | See domain guide + implementation guide for definition |
| `referee_x_discipline`           | float | Pregame | See domain guide + implementation guide for definition |

### WEATHER features (10)

- Rationale + nuances: see `FEATURES_DOMAIN_GUIDES.md` and `FEATURES_IMPLEMENTATION_GUIDE.md`.

| Feature              | Type  | Horizon | Definition/Math (minimum)                                            |
| -------------------- | ----- | ------- | -------------------------------------------------------------------- |
| `bad_weather_flag`   | int   | Pregame | See domain guide + implementation guide for definition               |
| `cloud_cover_pct`    | float | Pregame | See domain guide + implementation guide for definition               |
| `humidity_pct`       | float | Pregame | See domain guide + implementation guide for definition               |
| `precipitation_mm`   | float | Pregame | See domain guide + implementation guide for definition               |
| `precipitation_prob` | float | Pregame | Implied probability derived from odds (vig-adjusted where specified) |
| `rain_flag`          | int   | Pregame | See domain guide + implementation guide for definition               |
| `temp_band`          | str   | Pregame | See domain guide + implementation guide for definition               |
| `temperature_c`      | float | Pregame | See domain guide + implementation guide for definition               |
| `wind_band`          | str   | Pregame | See domain guide + implementation guide for definition               |
| `wind_speed_kmh`     | float | Pregame | See domain guide + implementation guide for definition               |

### HT features (8)

- Rationale + nuances: see `FEATURES_DOMAIN_GUIDES.md` and `FEATURES_IMPLEMENTATION_GUIDE.md`.

| Feature                     | Type  | Horizon | Definition/Math (minimum)                              |
| --------------------------- | ----- | ------- | ------------------------------------------------------ |
| `game_state_at_ht`          | float | HT      | See domain guide + implementation guide for definition |
| `ht_xg_soccerfootball_away` | float | HT      | See domain guide + implementation guide for definition |
| `ht_xg_soccerfootball_home` | float | HT      | See domain guide + implementation guide for definition |
| `ht_xg_understat_away`      | float | HT      | See domain guide + implementation guide for definition |
| `ht_xg_understat_home`      | float | HT      | See domain guide + implementation guide for definition |
| `momentum_score_ht_away`    | float | HT      | See domain guide + implementation guide for definition |
| `momentum_score_ht_home`    | float | HT      | See domain guide + implementation guide for definition |
| `velocity_ht_home`          | float | HT      | velocity = Δprob / Δtime between snapshot windows      |

### OTHER features (356)

| Feature                                | Type  | Horizon | Definition/Math (minimum)                                      |
| -------------------------------------- | ----- | ------- | -------------------------------------------------------------- |
| `aerial_dominance`                     | float | Pregame | See domain guide + implementation guide for definition         |
| `ah_primary_line`                      | float | Pregame | See domain guide + implementation guide for definition         |
| `ah_vig`                               | float | Pregame | vig = sum(implied_probs) - 1 (or per-market variant)           |
| `asian_leads_european`                 | float | Pregame | See domain guide + implementation guide for definition         |
| `attack_directness`                    | float | Pregame | See domain guide + implementation guide for definition         |
| `attack_dominance_late_away`           | float | Pregame | See domain guide + implementation guide for definition         |
| `attack_dominance_late_home`           | float | Pregame | See domain guide + implementation guide for definition         |
| `attacks`                              | float | Pregame | See domain guide + implementation guide for definition         |
| `avg_goals_market`                     | float | Pregame | Market-implied total goals / line-derived expectation          |
| `bet365_lag_away`                      | float | Pregame | See domain guide + implementation guide for definition         |
| `bet365_lag_home`                      | float | Pregame | See domain guide + implementation guide for definition         |
| `bet_size_multiplier`                  | float | Pregame | See domain guide + implementation guide for definition         |
| `betfair_volume_estimate`              | float | Pregame | See domain guide + implementation guide for definition         |
| `betfair_weight`                       | float | Pregame | See domain guide + implementation guide for definition         |
| `big_chance_conversion_away`           | float | Pregame | See domain guide + implementation guide for definition         |
| `big_chance_conversion_home`           | float | Pregame | See domain guide + implementation guide for definition         |
| `big_chance_pct`                       | float | Pregame | See domain guide + implementation guide for definition         |
| `big_chances_created`                  | float | Pregame | See domain guide + implementation guide for definition         |
| `bookmaker_agreement`                  | float | Pregame | See domain guide + implementation guide for definition         |
| `bookmaker_count`                      | int   | Pregame | See domain guide + implementation guide for definition         |
| `books_in_sync`                        | float | Pregame | See domain guide + implementation guide for definition         |
| `both_short_rest`                      | float | Pregame | See domain guide + implementation guide for definition         |
| `btts_potential`                       | float | Pregame | See domain guide + implementation guide for definition         |
| `cards_under_referee`                  | float | Pregame | See domain guide + implementation guide for definition         |
| `cards_vs_ref_avg`                     | float | Pregame | See domain guide + implementation guide for definition         |
| `closing_line_predictability`          | float | Pregame | See domain guide + implementation guide for definition         |
| `comeback_attempted_away`              | float | HT      | See domain guide + implementation guide for definition         |
| `comeback_attempted_home`              | float | HT      | See domain guide + implementation guide for definition         |
| `competition_stage`                    | float | Pregame | See domain guide + implementation guide for definition         |
| `competition_type`                     | float | Pregame | See domain guide + implementation guide for definition         |
| `congestion_diff`                      | float | Pregame | Difference between corresponding values                        |
| `congestion_score`                     | float | Pregame | See domain guide + implementation guide for definition         |
| `continental_hangover`                 | float | Pregame | See domain guide + implementation guide for definition         |
| `continental_hangover_away`            | float | Pregame | See domain guide + implementation guide for definition         |
| `continental_hangover_home`            | float | Pregame | See domain guide + implementation guide for definition         |
| `corners`                              | float | Pregame | See domain guide + implementation guide for definition         |
| `corrupted_data_flag`                  | int   | Pregame | See domain guide + implementation guide for definition         |
| `counter_attack_opportunity`           | float | Pregame | See domain guide + implementation guide for definition         |
| `country_id`                           | float | Pregame | See domain guide + implementation guide for definition         |
| `crosses`                              | float | Pregame | See domain guide + implementation guide for definition         |
| `ctmcl`                                | float | Pregame | Market-implied total goals / line-derived expectation          |
| `dangerous_attacks`                    | float | Pregame | See domain guide + implementation guide for definition         |
| `dangerous_attacks_last_10_away`       | float | HT      | See domain guide + implementation guide for definition         |
| `dangerous_attacks_last_10_home`       | float | HT      | See domain guide + implementation guide for definition         |
| `data_completeness_score`              | float | Pregame | See domain guide + implementation guide for definition         |
| `days_since_manager_change`            | float | Pregame | See domain guide + implementation guide for definition         |
| `days_since_season_start`              | float | Pregame | See domain guide + implementation guide for definition         |
| `decay_weighted_goals_against`         | float | Pregame | See domain guide + implementation guide for definition         |
| `decay_weighted_goals_for`             | float | Pregame | See domain guide + implementation guide for definition         |
| `decay_weighted_xg_against`            | float | Pregame | See domain guide + implementation guide for definition         |
| `decay_weighted_xg_for`                | float | Pregame | See domain guide + implementation guide for definition         |
| `def_avg_height_cm`                    | float | Pregame | See domain guide + implementation guide for definition         |
| `def_line_count`                       | int   | Pregame | See domain guide + implementation guide for definition         |
| `def_line_rating`                      | float | Pregame | See domain guide + implementation guide for definition         |
| `def_line_value`                       | float | Pregame | See domain guide + implementation guide for definition         |
| `defensive_block_height`               | float | Pregame | See domain guide + implementation guide for definition         |
| `delta_p_away_poisson_vs_market`       | float | Pregame | See domain guide + implementation guide for definition         |
| `delta_p_draw_poisson_vs_market`       | float | Pregame | See domain guide + implementation guide for definition         |
| `delta_p_home_poisson_vs_market`       | float | Pregame | See domain guide + implementation guide for definition         |
| `direct_vs_patient`                    | float | Pregame | See domain guide + implementation guide for definition         |
| `division_tier`                        | int   | Pregame | See domain guide + implementation guide for definition         |
| `elo_diff`                             | float | Pregame | Difference between corresponding values                        |
| `elo_vs_league_avg`                    | float | Pregame | See domain guide + implementation guide for definition         |
| `event_rate_decline_away`              | float | HT      | See domain guide + implementation guide for definition         |
| `event_rate_decline_home`              | float | HT      | See domain guide + implementation guide for definition         |
| `exchange_price_home`                  | float | Pregame | See domain guide + implementation guide for definition         |
| `exchange_vs_sharp_delta`              | float | Pregame | See domain guide + implementation guide for definition         |
| `expected_clv`                         | float | Pregame | See domain guide + implementation guide for definition         |
| `feature_reliability_score`            | float | Pregame | See domain guide + implementation guide for definition         |
| `fixture_pile_up`                      | float | Pregame | See domain guide + implementation guide for definition         |
| `form_x_xi_strength_away`              | float | Pregame | See domain guide + implementation guide for definition         |
| `form_x_xi_strength_home`              | float | Pregame | See domain guide + implementation guide for definition         |
| `fwd_line_goals_season`                | float | Pregame | Mean over season-to-date matches (as-of cutoff applied)        |
| `fwd_line_rating`                      | float | Pregame | See domain guide + implementation guide for definition         |
| `fwd_line_value`                       | float | Pregame | See domain guide + implementation guide for definition         |
| `fwd_line_xg_per90`                    | float | Pregame | See domain guide + implementation guide for definition         |
| `game_control`                         | float | Pregame | See domain guide + implementation guide for definition         |
| `games_last_14d`                       | float | Pregame | See domain guide + implementation guide for definition         |
| `games_last_21d`                       | float | Pregame | See domain guide + implementation guide for definition         |
| `games_played_season`                  | float | Pregame | Mean over season-to-date matches (as-of cutoff applied)        |
| `games_played_season_away`             | float | Pregame | See domain guide + implementation guide for definition         |
| `games_played_season_home`             | float | Pregame | See domain guide + implementation guide for definition         |
| `games_since_season_start`             | float | Pregame | See domain guide + implementation guide for definition         |
| `games_under_manager`                  | float | Pregame | See domain guide + implementation guide for definition         |
| `gk_rating`                            | float | Pregame | See domain guide + implementation guide for definition         |
| `gk_saves_pct`                         | float | Pregame | See domain guide + implementation guide for definition         |
| `goals_vs_league_avg_away`             | float | Pregame | See domain guide + implementation guide for definition         |
| `goals_vs_league_avg_home`             | float | Pregame | See domain guide + implementation guide for definition         |
| `high_intensity_match`                 | float | Pregame | See domain guide + implementation guide for definition         |
| `historical_clv_accuracy`              | float | Pregame | See domain guide + implementation guide for definition         |
| `history_depth_last1`                  | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `history_depth_last10`                 | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `history_depth_last3`                  | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `history_depth_last5`                  | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `history_depth_season`                 | float | Pregame | Mean over season-to-date matches (as-of cutoff applied)        |
| `history_depth_season_away`            | float | Pregame | See domain guide + implementation guide for definition         |
| `history_depth_season_home`            | float | Pregame | See domain guide + implementation guide for definition         |
| `insufficient_data_last10`             | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `insufficient_data_last3`              | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `insufficient_data_last5`              | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `insufficient_data_season`             | float | Pregame | Mean over season-to-date matches (as-of cutoff applied)        |
| `intensity_score_away`                 | float | Pregame | See domain guide + implementation guide for definition         |
| `intensity_score_home`                 | float | Pregame | See domain guide + implementation guide for definition         |
| `is_derby`                             | int   | Pregame | See domain guide + implementation guide for definition         |
| `is_early_season`                      | int   | Pregame | Mean over season-to-date matches (as-of cutoff applied)        |
| `is_first_3_games`                     | int   | Pregame | See domain guide + implementation guide for definition         |
| `is_promoted_team_away`                | int   | Pregame | See domain guide + implementation guide for definition         |
| `is_promoted_team_home`                | int   | Pregame | See domain guide + implementation guide for definition         |
| `is_relegation_battle`                 | int   | Pregame | See domain guide + implementation guide for definition         |
| `key_absentees_count`                  | int   | Pregame | See domain guide + implementation guide for definition         |
| `key_passes`                           | float | Pregame | See domain guide + implementation guide for definition         |
| `kickoff_hour`                         | float | Pregame | See domain guide + implementation guide for definition         |
| `lambda_away_bayesian`                 | float | Pregame | See domain guide + implementation guide for definition         |
| `lambda_away_lower_95`                 | float | Pregame | See domain guide + implementation guide for definition         |
| `lambda_away_market_implied`           | float | Pregame | See domain guide + implementation guide for definition         |
| `lambda_away_poisson`                  | float | Pregame | See domain guide + implementation guide for definition         |
| `lambda_away_upper_95`                 | float | Pregame | See domain guide + implementation guide for definition         |
| `lambda_blend_away`                    | float | Pregame | See domain guide + implementation guide for definition         |
| `lambda_blend_home`                    | float | Pregame | See domain guide + implementation guide for definition         |
| `lambda_diff_poisson`                  | float | Pregame | See domain guide + implementation guide for definition         |
| `lambda_home_bayesian`                 | float | Pregame | See domain guide + implementation guide for definition         |
| `lambda_home_lower_95`                 | float | Pregame | See domain guide + implementation guide for definition         |
| `lambda_home_market_implied`           | float | Pregame | See domain guide + implementation guide for definition         |
| `lambda_home_poisson`                  | float | Pregame | See domain guide + implementation guide for definition         |
| `lambda_home_upper_95`                 | float | Pregame | See domain guide + implementation guide for definition         |
| `lambda_total_poisson`                 | float | Pregame | See domain guide + implementation guide for definition         |
| `lambda_uncertainty_away`              | float | Pregame | See domain guide + implementation guide for definition         |
| `lambda_uncertainty_home`              | float | Pregame | See domain guide + implementation guide for definition         |
| `late_surge_away`                      | float | Pregame | See domain guide + implementation guide for definition         |
| `late_surge_home`                      | float | Pregame | See domain guide + implementation guide for definition         |
| `lead_changes`                         | float | HT      | See domain guide + implementation guide for definition         |
| `learnability_score`                   | float | Pregame | See domain guide + implementation guide for definition         |
| `liquidity_score`                      | float | Pregame | See domain guide + implementation guide for definition         |
| `manager_attack_style`                 | float | Pregame | See domain guide + implementation guide for definition         |
| `manager_avg_possession`               | float | Pregame | See domain guide + implementation guide for definition         |
| `manager_avg_ppda`                     | float | Pregame | See domain guide + implementation guide for definition         |
| `manager_away_id`                      | float | Pregame | See domain guide + implementation guide for definition         |
| `manager_clean_sheet_rate`             | float | Pregame | See domain guide + implementation guide for definition         |
| `manager_defensive_style`              | float | Pregame | See domain guide + implementation guide for definition         |
| `manager_experience_diff`              | float | Pregame | Difference between corresponding values                        |
| `manager_goals_per_game`               | float | Pregame | See domain guide + implementation guide for definition         |
| `manager_h2h_home_wins`                | int   | Pregame | See domain guide + implementation guide for definition         |
| `manager_h2h_matches`                  | float | Pregame | See domain guide + implementation guide for definition         |
| `manager_home_id`                      | float | Pregame | See domain guide + implementation guide for definition         |
| `manager_honeymoon`                    | float | Pregame | See domain guide + implementation guide for definition         |
| `manager_ppg_last5`                    | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `manager_set_piece_focus`              | float | Pregame | See domain guide + implementation guide for definition         |
| `manager_trophy_diff`                  | float | Pregame | Difference between corresponding values                        |
| `manager_win_rate`                     | float | Pregame | See domain guide + implementation guide for definition         |
| `manager_xg_diff_last5`                | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `match_card_risk_score`                | float | Pregame | See domain guide + implementation guide for definition         |
| `match_tempo`                          | float | Pregame | See domain guide + implementation guide for definition         |
| `max_min_spread`                       | float | Pregame | See domain guide + implementation guide for definition         |
| `max_momentum_away`                    | float | Pregame | See domain guide + implementation guide for definition         |
| `max_momentum_home`                    | float | Pregame | See domain guide + implementation guide for definition         |
| `max_single_move_away`                 | float | Pregame | See domain guide + implementation guide for definition         |
| `max_single_move_home`                 | float | Pregame | See domain guide + implementation guide for definition         |
| `max_stake_estimate`                   | float | Pregame | See domain guide + implementation guide for definition         |
| `mid_line_rating`                      | float | Pregame | See domain guide + implementation guide for definition         |
| `mid_line_value`                       | float | Pregame | See domain guide + implementation guide for definition         |
| `mid_line_xg_per90`                    | float | Pregame | See domain guide + implementation guide for definition         |
| `midweek_european`                     | float | Pregame | See domain guide + implementation guide for definition         |
| `momentum_at_35_away`                  | float | HT      | See domain guide + implementation guide for definition         |
| `momentum_at_35_home`                  | float | HT      | See domain guide + implementation guide for definition         |
| `momentum_trend_away`                  | float | HT      | See domain guide + implementation guide for definition         |
| `momentum_trend_home`                  | float | HT      | See domain guide + implementation guide for definition         |
| `new_manager_flag`                     | int   | Pregame | See domain guide + implementation guide for definition         |
| `new_manager_flag_away`                | float | Pregame | See domain guide + implementation guide for definition         |
| `new_manager_flag_home`                | float | Pregame | See domain guide + implementation guide for definition         |
| `npxg_understat_away`                  | float | Pregame | See domain guide + implementation guide for definition         |
| `npxg_understat_home`                  | float | Pregame | See domain guide + implementation guide for definition         |
| `o05_potential`                        | float | Pregame | See domain guide + implementation guide for definition         |
| `o15_potential`                        | float | Pregame | See domain guide + implementation guide for definition         |
| `o25_potential`                        | float | Pregame | See domain guide + implementation guide for definition         |
| `o35_potential`                        | float | Pregame | See domain guide + implementation guide for definition         |
| `o45_potential`                        | float | Pregame | See domain guide + implementation guide for definition         |
| `p_poisson_away`                       | float | Pregame | See domain guide + implementation guide for definition         |
| `p_poisson_draw`                       | float | Pregame | See domain guide + implementation guide for definition         |
| `p_poisson_home`                       | float | Pregame | See domain guide + implementation guide for definition         |
| `pass_tempo`                           | float | Pregame | See domain guide + implementation guide for definition         |
| `passes_final_third`                   | float | Pregame | See domain guide + implementation guide for definition         |
| `path_smoothness_away`                 | float | Pregame | See domain guide + implementation guide for definition         |
| `path_smoothness_home`                 | float | Pregame | See domain guide + implementation guide for definition         |
| `pen_differential_expected`            | float | Pregame | See domain guide + implementation guide for definition         |
| `pen_opportunity_away`                 | float | Pregame | See domain guide + implementation guide for definition         |
| `pen_opportunity_home`                 | float | Pregame | See domain guide + implementation guide for definition         |
| `physical_mismatch`                    | float | Pregame | See domain guide + implementation guide for definition         |
| `played_continental_last_week`         | float | Pregame | See domain guide + implementation guide for definition         |
| `possession`                           | float | Pregame | See domain guide + implementation guide for definition         |
| `possession_battle`                    | float | Pregame | See domain guide + implementation guide for definition         |
| `possession_consistency`               | float | Pregame | See domain guide + implementation guide for definition         |
| `possession_style`                     | float | Pregame | See domain guide + implementation guide for definition         |
| `possession_vs_league_avg_away`        | float | Pregame | See domain guide + implementation guide for definition         |
| `possession_vs_league_avg_home`        | float | Pregame | See domain guide + implementation guide for definition         |
| `possession_x_xg_home`                 | float | Pregame | See domain guide + implementation guide for definition         |
| `ppda`                                 | float | Pregame | See domain guide + implementation guide for definition         |
| `ppda_style`                           | float | Pregame | See domain guide + implementation guide for definition         |
| `ppg`                                  | float | Pregame | See domain guide + implementation guide for definition         |
| `pre_match_away_ppg`                   | float | Pregame | See domain guide + implementation guide for definition         |
| `pre_match_home_ppg`                   | float | Pregame | See domain guide + implementation guide for definition         |
| `preseaon_available`                   | int   | Pregame | See domain guide + implementation guide for definition         |
| `preseaon_form_score`                  | float | Pregame | See domain guide + implementation guide for definition         |
| `preseaon_goals_against`               | float | Pregame | See domain guide + implementation guide for definition         |
| `preseaon_goals_for`                   | float | Pregame | See domain guide + implementation guide for definition         |
| `preseaon_wins`                        | int   | Pregame | See domain guide + implementation guide for definition         |
| `preseaon_xg_against`                  | float | Pregame | See domain guide + implementation guide for definition         |
| `preseaon_xg_for`                      | float | Pregame | See domain guide + implementation guide for definition         |
| `press_vs_build`                       | float | Pregame | See domain guide + implementation guide for definition         |
| `price_discovery_score`                | float | Pregame | See domain guide + implementation guide for definition         |
| `prior_attack_adjustment`              | float | Pregame | See domain guide + implementation guide for definition         |
| `prior_decay_factor`                   | float | Pregame | See domain guide + implementation guide for definition         |
| `prior_defense_adjustment`             | float | Pregame | See domain guide + implementation guide for definition         |
| `prior_goals_against`                  | float | Pregame | See domain guide + implementation guide for definition         |
| `prior_goals_for`                      | float | Pregame | See domain guide + implementation guide for definition         |
| `prior_manager_attack_style`           | float | Pregame | See domain guide + implementation guide for definition         |
| `prior_manager_defense_style`          | float | Pregame | See domain guide + implementation guide for definition         |
| `prior_manager_possession`             | float | Pregame | See domain guide + implementation guide for definition         |
| `prior_possession`                     | float | Pregame | See domain guide + implementation guide for definition         |
| `prior_preseaon_form`                  | float | Pregame | See domain guide + implementation guide for definition         |
| `prior_preseaon_xg_against`            | float | Pregame | See domain guide + implementation guide for definition         |
| `prior_preseaon_xg_for`                | float | Pregame | See domain guide + implementation guide for definition         |
| `prior_reliability`                    | float | Pregame | See domain guide + implementation guide for definition         |
| `prior_shots_against`                  | float | Pregame | See domain guide + implementation guide for definition         |
| `prior_shots_for`                      | float | Pregame | See domain guide + implementation guide for definition         |
| `prior_squad_stability`                | float | Pregame | See domain guide + implementation guide for definition         |
| `prior_squad_value_ratio`              | float | Pregame | Ratio of corresponding values (epsilon guard)                  |
| `prior_weight_away`                    | float | Pregame | See domain guide + implementation guide for definition         |
| `prior_weight_home`                    | float | Pregame | See domain guide + implementation guide for definition         |
| `prior_xg_attack`                      | float | Pregame | See domain guide + implementation guide for definition         |
| `prior_xg_defense`                     | float | Pregame | See domain guide + implementation guide for definition         |
| `raw_edge`                             | float | Pregame | See domain guide + implementation guide for definition         |
| `red_card_diff`                        | float | Pregame | Difference between corresponding values                        |
| `red_risk_with_ref`                    | float | Pregame | See domain guide + implementation guide for definition         |
| `region`                               | float | Pregame | See domain guide + implementation guide for definition         |
| `rest_diff`                            | float | Pregame | Difference between corresponding values                        |
| `risk_adjusted_ev`                     | float | Pregame | See domain guide + implementation guide for definition         |
| `rlm_detected_away`                    | float | Pregame | See domain guide + implementation guide for definition         |
| `rlm_detected_home`                    | float | Pregame | See domain guide + implementation guide for definition         |
| `rlm_magnitude_away`                   | float | Pregame | See domain guide + implementation guide for definition         |
| `rlm_magnitude_home`                   | float | Pregame | See domain guide + implementation guide for definition         |
| `sbo_pinnacle_delta_away`              | float | Pregame | See domain guide + implementation guide for definition         |
| `sbo_pinnacle_delta_home`              | float | Pregame | See domain guide + implementation guide for definition         |
| `season_progress_pct`                  | float | Pregame | See domain guide + implementation guide for definition         |
| `set_piece_reliance`                   | float | Pregame | See domain guide + implementation guide for definition         |
| `shot_coordinates`                     | float | Pregame | See domain guide + implementation guide for definition         |
| `shot_pressure_ratio_away`             | float | Pregame | See domain guide + implementation guide for definition         |
| `shot_pressure_ratio_home`             | float | Pregame | See domain guide + implementation guide for definition         |
| `shot_volume_style`                    | float | Pregame | See domain guide + implementation guide for definition         |
| `shots`                                | float | Pregame | See domain guide + implementation guide for definition         |
| `shots_blocked`                        | float | Pregame | See domain guide + implementation guide for definition         |
| `shots_blocked_pct`                    | float | Pregame | See domain guide + implementation guide for definition         |
| `shots_last_10min_away`                | float | HT      | See domain guide + implementation guide for definition         |
| `shots_last_10min_home`                | float | HT      | See domain guide + implementation guide for definition         |
| `shots_last_5min_away`                 | float | HT      | See domain guide + implementation guide for definition         |
| `shots_last_5min_home`                 | float | HT      | See domain guide + implementation guide for definition         |
| `shots_off_target`                     | float | Pregame | See domain guide + implementation guide for definition         |
| `shots_on_target`                      | float | Pregame | See domain guide + implementation guide for definition         |
| `shots_vs_league_avg_away`             | float | Pregame | See domain guide + implementation guide for definition         |
| `shots_vs_league_avg_home`             | float | Pregame | See domain guide + implementation guide for definition         |
| `shrinkage_factor_away`                | float | Pregame | See domain guide + implementation guide for definition         |
| `shrinkage_factor_home`                | float | Pregame | See domain guide + implementation guide for definition         |
| `shrinkage_strength_league`            | float | Pregame | See domain guide + implementation guide for definition         |
| `skip_fixture_flag`                    | int   | Pregame | See domain guide + implementation guide for definition         |
| `squad_turnover_rate`                  | float | Pregame | See domain guide + implementation guide for definition         |
| `style_clash_score`                    | float | Pregame | See domain guide + implementation guide for definition         |
| `style_embedding_available`            | int   | Pregame | See domain guide + implementation guide for definition         |
| `style_pc1`                            | float | Pregame | See domain guide + implementation guide for definition         |
| `style_pc2`                            | float | Pregame | See domain guide + implementation guide for definition         |
| `style_pc3`                            | float | Pregame | See domain guide + implementation guide for definition         |
| `style_similarity`                     | float | Pregame | See domain guide + implementation guide for definition         |
| `tackle_aggression`                    | float | Pregame | See domain guide + implementation guide for definition         |
| `team_a_xg_prematch`                   | float | Pregame | See domain guide + implementation guide for definition         |
| `team_b_xg_prematch`                   | float | Pregame | See domain guide + implementation guide for definition         |
| `tempo_differential`                   | float | Pregame | See domain guide + implementation guide for definition         |
| `time_in_lead_away`                    | float | HT      | See domain guide + implementation guide for definition         |
| `time_in_lead_home`                    | float | HT      | See domain guide + implementation guide for definition         |
| `total_history_depth`                  | float | Pregame | See domain guide + implementation guide for definition         |
| `total_primary_line`                   | float | Pregame | See domain guide + implementation guide for definition         |
| `total_vig`                            | float | Pregame | vig = sum(implied_probs) - 1 (or per-market variant)           |
| `travel_fatigue_away`                  | float | Pregame | See domain guide + implementation guide for definition         |
| `travel_fatigue_home`                  | float | Pregame | See domain guide + implementation guide for definition         |
| `use_market_prior_flag`                | int   | Pregame | See domain guide + implementation guide for definition         |
| `use_player_aggregation`               | int   | Pregame | See domain guide + implementation guide for definition         |
| `value_lost_to_injury`                 | float | Pregame | See domain guide + implementation guide for definition         |
| `venue_altitude_m`                     | float | Pregame | See domain guide + implementation guide for definition         |
| `venue_capacity`                       | float | Pregame | See domain guide + implementation guide for definition         |
| `venue_home_advantage_score`           | float | Pregame | See domain guide + implementation guide for definition         |
| `venue_id`                             | float | Pregame | See domain guide + implementation guide for definition         |
| `venue_surface`                        | float | Pregame | See domain guide + implementation guide for definition         |
| `weather_x_style`                      | float | Pregame | See domain guide + implementation guide for definition         |
| `weighted_consensus_away`              | float | Pregame | See domain guide + implementation guide for definition         |
| `weighted_consensus_home`              | float | Pregame | See domain guide + implementation guide for definition         |
| `xg_acceleration_away`                 | float | Pregame | See domain guide + implementation guide for definition         |
| `xg_acceleration_home`                 | float | Pregame | See domain guide + implementation guide for definition         |
| `xg_confidence`                        | float | Pregame | See domain guide + implementation guide for definition         |
| `xg_consensus_away`                    | float | Pregame | See domain guide + implementation guide for definition         |
| `xg_consensus_home`                    | float | Pregame | See domain guide + implementation guide for definition         |
| `xg_disagreement_away`                 | float | Pregame | See domain guide + implementation guide for definition         |
| `xg_disagreement_home`                 | float | Pregame | See domain guide + implementation guide for definition         |
| `xg_first_15min_away`                  | float | HT      | See domain guide + implementation guide for definition         |
| `xg_first_15min_home`                  | float | HT      | See domain guide + implementation guide for definition         |
| `xg_footystats_away`                   | float | Pregame | See domain guide + implementation guide for definition         |
| `xg_footystats_home`                   | float | Pregame | See domain guide + implementation guide for definition         |
| `xg_is_understat_league`               | float | Pregame | See domain guide + implementation guide for definition         |
| `xg_last_15min_away`                   | float | HT      | See domain guide + implementation guide for definition         |
| `xg_last_15min_home`                   | float | HT      | See domain guide + implementation guide for definition         |
| `xg_max_source_away`                   | float | Pregame | See domain guide + implementation guide for definition         |
| `xg_max_source_home`                   | float | Pregame | See domain guide + implementation guide for definition         |
| `xg_middle_15min_away`                 | float | HT      | See domain guide + implementation guide for definition         |
| `xg_middle_15min_home`                 | float | HT      | See domain guide + implementation guide for definition         |
| `xg_min_source_away`                   | float | Pregame | See domain guide + implementation guide for definition         |
| `xg_min_source_home`                   | float | Pregame | See domain guide + implementation guide for definition         |
| `xg_model_residual_away`               | float | Pregame | See domain guide + implementation guide for definition         |
| `xg_model_residual_home`               | float | Pregame | See domain guide + implementation guide for definition         |
| `xg_per_shot`                          | float | Pregame | See domain guide + implementation guide for definition         |
| `xg_per_shot_synthetic`                | float | Pregame | See domain guide + implementation guide for definition         |
| `xg_per_shot_synthetic_away`           | float | Pregame | See domain guide + implementation guide for definition         |
| `xg_per_shot_synthetic_home`           | float | Pregame | See domain guide + implementation guide for definition         |
| `xg_per_shot_understat_away`           | float | Pregame | See domain guide + implementation guide for definition         |
| `xg_per_shot_understat_home`           | float | Pregame | See domain guide + implementation guide for definition         |
| `xg_range_away`                        | float | Pregame | See domain guide + implementation guide for definition         |
| `xg_range_home`                        | float | Pregame | See domain guide + implementation guide for definition         |
| `xg_soccerfootball_away`               | float | Pregame | See domain guide + implementation guide for definition         |
| `xg_soccerfootball_home`               | float | Pregame | See domain guide + implementation guide for definition         |
| `xg_soccerfootball_vs_footystats_away` | float | Pregame | See domain guide + implementation guide for definition         |
| `xg_soccerfootball_vs_footystats_home` | float | Pregame | See domain guide + implementation guide for definition         |
| `xg_source`                            | str   | Pregame | See domain guide + implementation guide for definition         |
| `xg_source_count`                      | int   | Pregame | See domain guide + implementation guide for definition         |
| `xg_source_primary`                    | str   | Pregame | See domain guide + implementation guide for definition         |
| `xg_synthetic_away`                    | float | Pregame | See domain guide + implementation guide for definition         |
| `xg_synthetic_diff`                    | float | Pregame | Difference between corresponding values                        |
| `xg_synthetic_home`                    | float | Pregame | See domain guide + implementation guide for definition         |
| `xg_synthetic_last5`                   | float | Pregame | Mean over last-N matches (no padding beyond available matches) |
| `xg_synthetic_last5_away`              | float | Pregame | See domain guide + implementation guide for definition         |
| `xg_synthetic_last5_home`              | float | Pregame | See domain guide + implementation guide for definition         |
| `xg_synthetic_season`                  | float | Pregame | Mean over season-to-date matches (as-of cutoff applied)        |
| `xg_synthetic_season_away`             | float | Pregame | See domain guide + implementation guide for definition         |
| `xg_synthetic_season_home`             | float | Pregame | See domain guide + implementation guide for definition         |
| `xg_synthetic_total`                   | float | Pregame | See domain guide + implementation guide for definition         |
| `xg_synthetic_vs_goals`                | float | Pregame | See domain guide + implementation guide for definition         |
| `xg_synthetic_vs_goals_away`           | float | Pregame | See domain guide + implementation guide for definition         |
| `xg_synthetic_vs_goals_home`           | float | Pregame | See domain guide + implementation guide for definition         |
| `xg_trend_away`                        | float | Pregame | See domain guide + implementation guide for definition         |
| `xg_trend_home`                        | float | Pregame | See domain guide + implementation guide for definition         |
| `xg_understat_away`                    | float | Pregame | See domain guide + implementation guide for definition         |
| `xg_understat_home`                    | float | Pregame | See domain guide + implementation guide for definition         |
| `xg_understat_vs_footystats_away`      | float | Pregame | See domain guide + implementation guide for definition         |
| `xg_understat_vs_footystats_home`      | float | Pregame | See domain guide + implementation guide for definition         |
| `xg_understat_vs_soccerfootball_away`  | float | Pregame | See domain guide + implementation guide for definition         |
| `xg_understat_vs_soccerfootball_home`  | float | Pregame | See domain guide + implementation guide for definition         |
| `xg_used_away`                         | float | Pregame | See domain guide + implementation guide for definition         |
| `xg_used_home`                         | float | Pregame | See domain guide + implementation guide for definition         |
| `xg_vs_league_avg_away`                | float | Pregame | See domain guide + implementation guide for definition         |
| `xg_vs_league_avg_home`                | float | Pregame | See domain guide + implementation guide for definition         |
| `xg_x_elo_away`                        | float | Pregame | See domain guide + implementation guide for definition         |
| `xg_x_elo_home`                        | float | Pregame | See domain guide + implementation guide for definition         |
