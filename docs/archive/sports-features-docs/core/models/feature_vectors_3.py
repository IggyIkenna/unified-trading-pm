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


class FeatureVectorH2hExplicit(Base):
    """Explicit feature vector table: feature_vector_h2h_explicit"""

    __tablename__ = "feature_vector_h2h_explicit"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fixture_id = Column(Integer, nullable=False, index=True)
    feature_horizon = Column(String, nullable=False)  # T-24h, T-1h, HT-2min, etc.
    timestamp_utc = Column(DateTime, nullable=False, index=True)  # as_of_utc

    h2h_away_wins = Column(Integer)
    h2h_btts_pct = Column(Float)
    h2h_days_since_last = Column(Float)
    h2h_draws = Column(Integer)
    h2h_goals_away_avg = Column(Float)
    h2h_goals_home_avg = Column(Float)
    h2h_home_at_venue_wins = Column(Integer)
    h2h_home_win_pct = Column(Float)
    h2h_home_wins = Column(Integer)
    h2h_last_result = Column(Float)
    h2h_last_score_away = Column(Float)
    h2h_last_score_home = Column(Float)
    h2h_matches_last5y = Column(Float)
    h2h_matches_total = Column(Float)
    h2h_over25_pct = Column(Float)
    h2h_possession_away_avg = Column(Float)
    h2h_possession_home_avg = Column(Float)
    h2h_total_goals_avg = Column(Float)
    h2h_xg_away_avg = Column(Float)
    h2h_xg_home_avg = Column(Float)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint(
            "fixture_id",
            "feature_horizon",
            "timestamp_utc",
            name="uq_feature_vector_h2h_explicit_fixture_horizon_ts",
        ),
        Index(
            "ix_feature_vector_h2h_explicit_fixture_horizon_ts",
            "fixture_id",
            "feature_horizon",
            "timestamp_utc",
        ),
    )


class FeatureVectorPlayerExplicit(Base):
    """Explicit feature vector table: feature_vector_player_explicit"""

    __tablename__ = "feature_vector_player_explicit"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fixture_id = Column(Integer, nullable=False, index=True)
    feature_horizon = Column(String, nullable=False)  # T-24h, T-1h, HT-2min, etc.
    timestamp_utc = Column(DateTime, nullable=False, index=True)  # as_of_utc

    player_advantage = Column(Float)
    player_aggregated_defense = Column(Float)
    player_aggregated_value_ratio = Column(Float)
    player_aggregated_xg_for = Column(Float)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint(
            "fixture_id",
            "feature_horizon",
            "timestamp_utc",
            name="uq_feature_vector_player_explicit_fixture_horizon_ts",
        ),
        Index(
            "ix_feature_vector_player_explicit_fixture_horizon_ts",
            "fixture_id",
            "feature_horizon",
            "timestamp_utc",
        ),
    )


class FeatureVectorLineupExplicit(Base):
    """Explicit feature vector table: feature_vector_lineup_explicit"""

    __tablename__ = "feature_vector_lineup_explicit"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fixture_id = Column(Integer, nullable=False, index=True)
    feature_horizon = Column(String, nullable=False)  # T-24h, T-1h, HT-2min, etc.
    timestamp_utc = Column(DateTime, nullable=False, index=True)  # as_of_utc

    away_xi_aerial_won_pct = Column(Float)
    away_xi_assists_season = Column(Float)
    away_xi_avg_rating = Column(Float)
    away_xi_avg_value = Column(Float)
    away_xi_blocks_per90_avg = Column(Float)
    away_xi_clearances_per90_avg = Column(Float)
    away_xi_goals_season = Column(Float)
    away_xi_interceptions_per90_avg = Column(Float)
    away_xi_stability = Column(Float)
    away_xi_tackles_per90_avg = Column(Float)
    away_xi_total_value = Column(Float)
    away_xi_xg_per90_avg = Column(Float)
    formation_attacking_ratio = Column(Float)
    formation_away = Column(Float)
    formation_differs_from_usual = Column(Float)
    formation_home = Column(Float)
    home_xi_aerial_won_pct = Column(Float)
    home_xi_assists_season = Column(Float)
    home_xi_attack_xg_avg = Column(Float)
    home_xi_avg_age = Column(Float)
    home_xi_avg_rating = Column(Float)
    home_xi_avg_value = Column(Float)
    home_xi_blocks_per90_avg = Column(Float)
    home_xi_clearances_per90_avg = Column(Float)
    home_xi_goals_season = Column(Float)
    home_xi_interceptions_per90_avg = Column(Float)
    home_xi_stability = Column(Float)
    home_xi_tackles_per90_avg = Column(Float)
    home_xi_total_value = Column(Float)
    home_xi_xg_per90_avg = Column(Float)
    lineup_available = Column(Integer)
    lineup_source = Column(Float)
    xi_aerial_won_pct = Column(Float)
    xi_blocks_per90_avg = Column(Float)
    xi_clearances_per90_avg = Column(Float)
    xi_interceptions_per90_avg = Column(Float)
    xi_rating_diff = Column(Float)
    xi_tackles_per90_avg = Column(Float)
    xi_value_ratio = Column(Float)
    xi_value_vs_league_avg = Column(Float)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint(
            "fixture_id",
            "feature_horizon",
            "timestamp_utc",
            name="uq_feature_vector_lineup_explicit_fixture_horizon_ts",
        ),
        Index(
            "ix_feature_vector_lineup_explicit_fixture_horizon_ts",
            "fixture_id",
            "feature_horizon",
            "timestamp_utc",
        ),
    )
