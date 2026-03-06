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

# =============================================================================
# EXPLICIT FEATURE VECTORS (AUTO-GENERATED FROM FEATURES_CATALOG.md)
# =============================================================================
# NOTE: These tables intentionally use explicit columns per feature, as requested.
# Column names correspond to canonical lowercase feature names in FEATURES_CATALOG.md.


class FeatureVectorMarketExplicit(Base):
    """Explicit feature vector table: feature_vector_market_explicit"""

    __tablename__ = "feature_vector_market_explicit"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fixture_id = Column(Integer, nullable=False, index=True)
    feature_horizon = Column(String, nullable=False)  # T-24h, T-1h, HT-2min, etc.
    timestamp_utc = Column(DateTime, nullable=False, index=True)  # as_of_utc

    accel_home_1h_to_0 = Column(Float)
    accel_home_6h_to_1h = Column(Float)
    avg_goals_market = Column(Float)
    book_fragmentation_away = Column(Float)
    book_fragmentation_home = Column(Float)
    ctmcl = Column(Float)
    gap_max_vs_pinnacle_away = Column(Float)
    gap_max_vs_pinnacle_draw = Column(Float)
    gap_max_vs_pinnacle_home = Column(Float)
    market_confidence = Column(Float)
    market_confidence_score = Column(Float)
    market_entropy = Column(Float)
    market_maturity_score = Column(Float)
    market_xg_disagreement_away = Column(Float)
    market_xg_disagreement_home = Column(Float)
    max_odds_away = Column(Float)
    max_odds_book_home = Column(String)
    max_odds_draw = Column(Float)
    max_odds_home = Column(Float)
    min_odds_home = Column(Float)
    odds_ah_0_away = Column(Float)
    odds_ah_0_home = Column(Float)
    odds_ah_m0_5_away = Column(Float)
    odds_ah_m0_5_home = Column(Float)
    odds_ah_m1_5_away = Column(Float)
    odds_ah_m1_5_home = Column(Float)
    odds_ah_m1_away = Column(Float)
    odds_ah_m1_home = Column(Float)
    odds_ah_m2_away = Column(Float)
    odds_ah_m2_home = Column(Float)
    odds_ah_p0_5_away = Column(Float)
    odds_ah_p0_5_home = Column(Float)
    odds_ah_p1_5_away = Column(Float)
    odds_ah_p1_5_home = Column(Float)
    odds_ah_p1_away = Column(Float)
    odds_ah_p1_home = Column(Float)
    odds_ah_p2_away = Column(Float)
    odds_ah_p2_home = Column(Float)
    odds_ft_1 = Column(Float)
    odds_ft_1_prob = Column(Float)
    odds_ft_2 = Column(Float)
    odds_ft_2_prob = Column(Float)
    odds_ft_over25 = Column(Float)
    odds_ft_under25 = Column(Float)
    odds_ft_x = Column(Float)
    odds_h2h_away = Column(Float)
    odds_h2h_away_pinnacle = Column(Float)
    odds_h2h_away_prob = Column(Float)
    odds_h2h_draw = Column(Float)
    odds_h2h_draw_pinnacle = Column(Float)
    odds_h2h_draw_prob = Column(Float)
    odds_h2h_home = Column(Float)
    odds_h2h_home_pinnacle = Column(Float)
    odds_h2h_home_prob = Column(Float)
    odds_h2h_max_vig = Column(Float)
    odds_h2h_min_vig = Column(Float)
    odds_h2h_vig = Column(Float)
    odds_range_away = Column(Float)
    odds_range_draw = Column(Float)
    odds_range_home = Column(Float)
    odds_stability_score = Column(Float)
    odds_total_0_5_over = Column(Float)
    odds_total_0_5_under = Column(Float)
    odds_total_1_5_over = Column(Float)
    odds_total_1_5_under = Column(Float)
    odds_total_2_5_over = Column(Float)
    odds_total_2_5_under = Column(Float)
    odds_total_3_5_over = Column(Float)
    odds_total_3_5_under = Column(Float)
    odds_total_4_5_over = Column(Float)
    odds_total_4_5_under = Column(Float)
    odds_total_5_5_over = Column(Float)
    odds_total_5_5_under = Column(Float)
    pinnacle_away = Column(Float)
    pinnacle_draw = Column(Float)
    pinnacle_home = Column(Float)
    pinnacle_lead_time_away = Column(Float)
    pinnacle_lead_time_home = Column(Float)
    pinnacle_vs_market_away = Column(Float)
    pinnacle_vs_market_home = Column(Float)
    pinnacle_weight = Column(Float)
    sharp_book_available = Column(String)
    sharp_book_count = Column(String)
    sharp_consensus_away = Column(Float)
    sharp_consensus_home = Column(Float)
    sharp_soft_delta_away = Column(Float)
    sharp_soft_delta_home = Column(Float)
    sharp_soft_spread = Column(Float)
    sharp_vs_all_weight = Column(Float)
    soft_book_count = Column(String)
    soft_book_value_home = Column(String)
    soft_consensus_away = Column(Float)
    soft_consensus_home = Column(Float)
    steam_detected_away = Column(Float)
    steam_detected_home = Column(Float)
    steam_magnitude_away = Column(Float)
    steam_magnitude_home = Column(Float)
    steam_timing_away = Column(Float)
    steam_timing_home = Column(Float)
    velocity_home_10m_to_0 = Column(Float)
    velocity_home_24h_to_6h = Column(Float)
    velocity_home_30m_to_10m = Column(Float)
    velocity_home_6h_to_90m = Column(Float)
    velocity_home_72h_to_24h = Column(Float)
    velocity_home_90m_to_30m = Column(Float)
    volatility_adjusted_edge = Column(Float)
    volatility_away_24h = Column(Float)
    volatility_draw_24h = Column(Float)
    volatility_home_24h = Column(Float)
    volatility_ratio_home_away = Column(Float)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint(
            "fixture_id",
            "feature_horizon",
            "timestamp_utc",
            name="uq_feature_vector_market_explicit_fixture_horizon_ts",
        ),
        Index(
            "ix_feature_vector_market_explicit_fixture_horizon_ts",
            "fixture_id",
            "feature_horizon",
            "timestamp_utc",
        ),
    )


class FeatureVectorLeagueExplicit(Base):
    """Explicit feature vector table: feature_vector_league_explicit"""

    __tablename__ = "feature_vector_league_explicit"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fixture_id = Column(Integer, nullable=False, index=True)
    feature_horizon = Column(String, nullable=False)  # T-24h, T-1h, HT-2min, etc.
    timestamp_utc = Column(DateTime, nullable=False, index=True)  # as_of_utc

    league_avg_away_goals = Column(Float)
    league_avg_goals = Column(Float)
    league_avg_home_goals = Column(Float)
    league_avg_margin = Column(Float)
    league_betfair_liquidity = Column(Float)
    league_bookmaker_count = Column(Integer)
    league_closing_line_accuracy = Column(Float)
    league_defense_index = Column(Float)
    league_efficiency_score = Column(Float)
    league_goal_variance = Column(Float)
    league_id = Column(Float)
    league_liquidity_tier = Column(Integer)
    league_model_r2 = Column(Float)
    league_normalized_attack_strength_away = Column(Float)
    league_normalized_attack_strength_home = Column(Float)
    league_normalized_defense_strength_away = Column(Float)
    league_normalized_defense_strength_home = Column(Float)
    league_odds_variance_away = Column(Float)
    league_odds_variance_home = Column(Float)
    league_offense_index = Column(Float)
    league_pace = Column(Float)
    league_physicality = Column(Float)
    league_pinnacle_available = Column(Integer)
    league_ref_bias = Column(Float)
    league_sharp_book_coverage = Column(String)
    league_steam_frequency = Column(Float)
    league_tier = Column(Integer)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint(
            "fixture_id",
            "feature_horizon",
            "timestamp_utc",
            name="uq_feature_vector_league_explicit_fixture_horizon_ts",
        ),
        Index(
            "ix_feature_vector_league_explicit_fixture_horizon_ts",
            "fixture_id",
            "feature_horizon",
            "timestamp_utc",
        ),
    )
