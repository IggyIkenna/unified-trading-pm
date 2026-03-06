from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    UniqueConstraint,
)

from .base import Base


class FeatureVectorRefereeExplicit(Base):
    """Explicit feature vector table: feature_vector_referee_explicit"""

    __tablename__ = "feature_vector_referee_explicit"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fixture_id = Column(Integer, nullable=False, index=True)
    feature_horizon = Column(String, nullable=False)  # T-24h, T-1h, HT-2min, etc.
    timestamp_utc = Column(DateTime, nullable=False, index=True)  # as_of_utc

    ref_away_result_with_away_team = Column(Float)
    ref_bias_differential = Column(Float)
    ref_bias_toward_home = Column(Float)
    ref_historical_favor_away = Column(Float)
    ref_historical_favor_home = Column(Float)
    ref_home_result_with_home_team = Column(Float)
    ref_pen_propensity = Column(Float)
    ref_team_card_chemistry = Column(Float)
    ref_team_card_chemistry_away = Column(Float)
    ref_team_card_chemistry_home = Column(Float)
    ref_tolerance_x_away_fouls = Column(Float)
    ref_tolerance_x_home_fouls = Column(Float)
    ref_tolerance_x_team_fouls = Column(Float)
    referee_avg_cards = Column(Float)
    referee_avg_fouls = Column(Float)
    referee_avg_penalties = Column(Float)
    referee_card_rate_band = Column(String)
    referee_home_bias = Column(Float)
    referee_id = Column(Float)
    referee_x_discipline = Column(Float)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint(
            "fixture_id",
            "feature_horizon",
            "timestamp_utc",
            name="uq_feature_vector_referee_explicit_fixture_horizon_ts",
        ),
        Index(
            "ix_feature_vector_referee_explicit_fixture_horizon_ts",
            "fixture_id",
            "feature_horizon",
            "timestamp_utc",
        ),
    )


class FeatureVectorWeatherExplicit(Base):
    """Explicit feature vector table: feature_vector_weather_explicit"""

    __tablename__ = "feature_vector_weather_explicit"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fixture_id = Column(Integer, nullable=False, index=True)
    feature_horizon = Column(String, nullable=False)  # T-24h, T-1h, HT-2min, etc.
    timestamp_utc = Column(DateTime, nullable=False, index=True)  # as_of_utc

    bad_weather_flag = Column(Integer)
    cloud_cover_pct = Column(Float)
    humidity_pct = Column(Float)
    precipitation_mm = Column(Float)
    precipitation_prob = Column(Float)
    rain_flag = Column(Integer)
    temp_band = Column(String)
    temperature_c = Column(Float)
    wind_band = Column(String)
    wind_speed_kmh = Column(Float)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint(
            "fixture_id",
            "feature_horizon",
            "timestamp_utc",
            name="uq_feature_vector_weather_explicit_fixture_horizon_ts",
        ),
        Index(
            "ix_feature_vector_weather_explicit_fixture_horizon_ts",
            "fixture_id",
            "feature_horizon",
            "timestamp_utc",
        ),
    )


class FeatureVectorHtExplicit(Base):
    """Explicit feature vector table: feature_vector_ht_explicit"""

    __tablename__ = "feature_vector_ht_explicit"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fixture_id = Column(Integer, nullable=False, index=True)
    feature_horizon = Column(String, nullable=False)  # T-24h, T-1h, HT-2min, etc.
    timestamp_utc = Column(DateTime, nullable=False, index=True)  # as_of_utc

    comeback_attempted_away = Column(Float)
    comeback_attempted_home = Column(Float)
    dangerous_attacks_last_10_away = Column(Float)
    dangerous_attacks_last_10_home = Column(Float)
    event_rate_decline_away = Column(Float)
    event_rate_decline_home = Column(Float)
    game_state_at_ht = Column(Float)
    ht_xg_soccerfootball_away = Column(Float)
    ht_xg_soccerfootball_home = Column(Float)
    ht_xg_understat_away = Column(Float)
    ht_xg_understat_home = Column(Float)
    lead_changes = Column(Float)
    momentum_at_35_away = Column(Float)
    momentum_at_35_home = Column(Float)
    momentum_score_ht_away = Column(Float)
    momentum_score_ht_home = Column(Float)
    momentum_trend_away = Column(Float)
    momentum_trend_home = Column(Float)
    shots_last_10min_away = Column(Float)
    shots_last_10min_home = Column(Float)
    shots_last_5min_away = Column(Float)
    shots_last_5min_home = Column(Float)
    time_in_lead_away = Column(Float)
    time_in_lead_home = Column(Float)
    velocity_ht_home = Column(Float)
    xg_first_15min_away = Column(Float)
    xg_first_15min_home = Column(Float)
    xg_last_15min_away = Column(Float)
    xg_last_15min_home = Column(Float)
    xg_middle_15min_away = Column(Float)
    xg_middle_15min_home = Column(Float)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint(
            "fixture_id",
            "feature_horizon",
            "timestamp_utc",
            name="uq_feature_vector_ht_explicit_fixture_horizon_ts",
        ),
        Index(
            "ix_feature_vector_ht_explicit_fixture_horizon_ts",
            "fixture_id",
            "feature_horizon",
            "timestamp_utc",
        ),
    )


class FeatureVectorContextExplicit(Base):
    """Explicit feature vector table: feature_vector_context_explicit"""

    __tablename__ = "feature_vector_context_explicit"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fixture_id = Column(Integer, nullable=False, index=True)
    feature_horizon = Column(String, nullable=False)  # T-24h, T-1h, HT-2min, etc.
    timestamp_utc = Column(DateTime, nullable=False, index=True)  # as_of_utc

    aerial_dominance = Column(Float)
    ah_primary_line = Column(Float)
    ah_vig = Column(Float)
    asian_leads_european = Column(Float)
    attack_directness = Column(Float)
    attack_dominance_late_away = Column(Float)
    attack_dominance_late_home = Column(Float)
    attacks = Column(Float)
    bet365_lag_away = Column(Float)
    bet365_lag_home = Column(Float)
    bet_size_multiplier = Column(Float)
    betfair_volume_estimate = Column(Float)
    betfair_weight = Column(Float)
    big_chance_conversion_away = Column(Float)
    big_chance_conversion_home = Column(Float)
    big_chance_pct = Column(Float)
    big_chances_created = Column(Float)
    bookmaker_agreement = Column(Float)
    bookmaker_count = Column(Integer)
    books_in_sync = Column(Float)
    both_short_rest = Column(Float)
    btts_potential = Column(Float)
    cards_under_referee = Column(Float)
    cards_vs_ref_avg = Column(Float)
    closing_line_predictability = Column(Float)
    competition_stage = Column(Float)
    competition_type = Column(Float)
    continental_hangover = Column(Float)
    continental_hangover_away = Column(Float)
    continental_hangover_home = Column(Float)
    corners = Column(Float)
    corrupted_data_flag = Column(Integer)
    counter_attack_opportunity = Column(Float)
    country_id = Column(Float)
    crosses = Column(Float)
    dangerous_attacks = Column(Float)
    data_completeness_score = Column(Float)
    decay_weighted_goals_against = Column(Float)
    decay_weighted_goals_for = Column(Float)
    decay_weighted_xg_against = Column(Float)
    decay_weighted_xg_for = Column(Float)
    def_avg_height_cm = Column(Float)
    def_line_count = Column(Integer)
    def_line_rating = Column(Float)
    def_line_value = Column(Float)
    defensive_block_height = Column(Float)
    delta_p_away_poisson_vs_market = Column(Float)
    delta_p_draw_poisson_vs_market = Column(Float)
    delta_p_home_poisson_vs_market = Column(Float)
    direct_vs_patient = Column(Float)
    elo_diff = Column(Float)
    elo_vs_league_avg = Column(Float)
    exchange_price_home = Column(Float)
    exchange_vs_sharp_delta = Column(Float)
    expected_clv = Column(Float)
    feature_reliability_score = Column(Float)
    fixture_pile_up = Column(Float)
    form_x_xi_strength_away = Column(Float)
    form_x_xi_strength_home = Column(Float)
    fwd_line_goals_season = Column(Float)
    fwd_line_rating = Column(Float)
    fwd_line_value = Column(Float)
    fwd_line_xg_per90 = Column(Float)
    game_control = Column(Float)
    gk_rating = Column(Float)
    gk_saves_pct = Column(Float)
    goals_vs_league_avg_away = Column(Float)
    goals_vs_league_avg_home = Column(Float)
    high_intensity_match = Column(Float)
    historical_clv_accuracy = Column(Float)
    history_depth_last1 = Column(Float)
    history_depth_last10 = Column(Float)
    history_depth_last3 = Column(Float)
    history_depth_last5 = Column(Float)
    history_depth_season = Column(Float)
    history_depth_season_away = Column(Float)
    history_depth_season_home = Column(Float)
    insufficient_data_last10 = Column(Float)
    insufficient_data_last3 = Column(Float)
    insufficient_data_last5 = Column(Float)
    insufficient_data_season = Column(Float)
    intensity_score_away = Column(Float)
    intensity_score_home = Column(Float)
    is_derby = Column(Integer)
    is_promoted_team_away = Column(Integer)
    is_promoted_team_home = Column(Integer)
    is_relegation_battle = Column(Integer)
    key_absentees_count = Column(Integer)
    key_passes = Column(Float)
    kickoff_hour = Column(Float)
    late_surge_away = Column(Float)
    late_surge_home = Column(Float)
    learnability_score = Column(Float)
    liquidity_score = Column(Float)
    match_card_risk_score = Column(Float)
    match_tempo = Column(Float)
    max_min_spread = Column(Float)
    max_momentum_away = Column(Float)
    max_momentum_home = Column(Float)
    max_single_move_away = Column(Float)
    max_single_move_home = Column(Float)
    max_stake_estimate = Column(Float)
    mid_line_rating = Column(Float)
    mid_line_value = Column(Float)
    mid_line_xg_per90 = Column(Float)
    midweek_european = Column(Float)
    npxg_understat_away = Column(Float)
    npxg_understat_home = Column(Float)
    o05_potential = Column(Float)
    o15_potential = Column(Float)
    o25_potential = Column(Float)
    o35_potential = Column(Float)
    o45_potential = Column(Float)
    pass_tempo = Column(Float)
    passes_final_third = Column(Float)
    path_smoothness_away = Column(Float)
    path_smoothness_home = Column(Float)
    pen_differential_expected = Column(Float)
    pen_opportunity_away = Column(Float)
    pen_opportunity_home = Column(Float)
    physical_mismatch = Column(Float)
    played_continental_last_week = Column(Float)
    possession = Column(Float)
    possession_battle = Column(Float)
    possession_consistency = Column(Float)
    possession_style = Column(Float)
    possession_vs_league_avg_away = Column(Float)
    possession_vs_league_avg_home = Column(Float)
    possession_x_xg_home = Column(Float)
    ppda = Column(Float)
    ppda_style = Column(Float)
    ppg = Column(Float)
    pre_match_away_ppg = Column(Float)
    pre_match_home_ppg = Column(Float)
    preseaon_available = Column(Integer)
    preseaon_form_score = Column(Float)
    preseaon_goals_against = Column(Float)
    preseaon_goals_for = Column(Float)
    preseaon_wins = Column(Integer)
    preseaon_xg_against = Column(Float)
    preseaon_xg_for = Column(Float)
    press_vs_build = Column(Float)
    price_discovery_score = Column(Float)
    raw_edge = Column(Float)
    red_card_diff = Column(Float)
    red_risk_with_ref = Column(Float)
    region = Column(Float)
    rest_diff = Column(Float)
    risk_adjusted_ev = Column(Float)
    rlm_detected_away = Column(Float)
    rlm_detected_home = Column(Float)
    rlm_magnitude_away = Column(Float)
    rlm_magnitude_home = Column(Float)
    sbo_pinnacle_delta_away = Column(Float)
    sbo_pinnacle_delta_home = Column(Float)
    set_piece_reliance = Column(Float)
    shot_coordinates = Column(Float)
    shot_pressure_ratio_away = Column(Float)
    shot_pressure_ratio_home = Column(Float)
    shot_volume_style = Column(Float)
    shots = Column(Float)
    shots_blocked = Column(Float)
    shots_blocked_pct = Column(Float)
    shots_off_target = Column(Float)
    shots_on_target = Column(Float)
    shots_vs_league_avg_away = Column(Float)
    shots_vs_league_avg_home = Column(Float)
    shrinkage_factor_away = Column(Float)
    shrinkage_factor_home = Column(Float)
    shrinkage_strength_league = Column(Float)
    skip_fixture_flag = Column(Integer)
    tackle_aggression = Column(Float)
    tempo_differential = Column(Float)
    total_history_depth = Column(Float)
    total_primary_line = Column(Float)
    total_vig = Column(Float)
    use_market_prior_flag = Column(Integer)
    use_player_aggregation = Column(Integer)
    value_lost_to_injury = Column(Float)
    venue_altitude_m = Column(Float)
    venue_capacity = Column(Float)
    venue_home_advantage_score = Column(Float)
    venue_id = Column(Float)
    venue_surface = Column(Float)
    weather_x_style = Column(Float)
    weighted_consensus_away = Column(Float)
    weighted_consensus_home = Column(Float)
    xg_acceleration_away = Column(Float)
    xg_acceleration_home = Column(Float)
    xg_confidence = Column(Float)
    xg_consensus_away = Column(Float)
    xg_consensus_home = Column(Float)
    xg_disagreement_away = Column(Float)
    xg_disagreement_home = Column(Float)
    xg_footystats_away = Column(Float)
    xg_footystats_home = Column(Float)
    xg_is_understat_league = Column(Float)
    xg_max_source_away = Column(Float)
    xg_max_source_home = Column(Float)
    xg_min_source_away = Column(Float)
    xg_min_source_home = Column(Float)
    xg_model_residual_away = Column(Float)
    xg_model_residual_home = Column(Float)
    xg_per_shot = Column(Float)
    xg_per_shot_synthetic = Column(Float)
    xg_per_shot_synthetic_away = Column(Float)
    xg_per_shot_synthetic_home = Column(Float)
    xg_per_shot_understat_away = Column(Float)
    xg_per_shot_understat_home = Column(Float)
    xg_range_away = Column(Float)
    xg_range_home = Column(Float)
    xg_soccerfootball_away = Column(Float)
    xg_soccerfootball_home = Column(Float)
    xg_soccerfootball_vs_footystats_away = Column(Float)
    xg_soccerfootball_vs_footystats_home = Column(Float)
    xg_source = Column(String)
    xg_source_count = Column(Integer)
    xg_source_primary = Column(String)
    xg_synthetic_away = Column(Float)
    xg_synthetic_diff = Column(Float)
    xg_synthetic_home = Column(Float)
    xg_synthetic_last5 = Column(Float)
    xg_synthetic_last5_away = Column(Float)
    xg_synthetic_last5_home = Column(Float)
    xg_synthetic_season = Column(Float)
    xg_synthetic_season_away = Column(Float)
    xg_synthetic_season_home = Column(Float)
    xg_synthetic_total = Column(Float)
    xg_synthetic_vs_goals = Column(Float)
    xg_synthetic_vs_goals_away = Column(Float)
    xg_synthetic_vs_goals_home = Column(Float)
    xg_trend_away = Column(Float)
    xg_trend_home = Column(Float)
    xg_understat_away = Column(Float)
    xg_understat_home = Column(Float)
    xg_understat_vs_footystats_away = Column(Float)
    xg_understat_vs_footystats_home = Column(Float)
    xg_understat_vs_soccerfootball_away = Column(Float)
    xg_understat_vs_soccerfootball_home = Column(Float)
    xg_used_away = Column(Float)
    xg_used_home = Column(Float)
    xg_vs_league_avg_away = Column(Float)
    xg_vs_league_avg_home = Column(Float)
    xg_x_elo_away = Column(Float)
    xg_x_elo_home = Column(Float)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint(
            "fixture_id",
            "feature_horizon",
            "timestamp_utc",
            name="uq_feature_vector_context_explicit_fixture_horizon_ts",
        ),
        Index(
            "ix_feature_vector_context_explicit_fixture_horizon_ts",
            "fixture_id",
            "feature_horizon",
            "timestamp_utc",
        ),
    )


# =============================================================================
