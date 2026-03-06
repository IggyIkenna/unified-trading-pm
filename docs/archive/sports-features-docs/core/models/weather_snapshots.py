from datetime import datetime

from sqlalchemy import (
    Boolean,
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
# WEATHER TABLES
# =============================================================================


class WeatherForecast(Base):
    """Open-Meteo weather forecasts"""

    __tablename__ = "weather_forecasts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fixture_id = Column(Integer, nullable=False, index=True)
    venue_id = Column(Integer)

    # Location
    latitude = Column(Float)
    longitude = Column(Float)

    # Timestamp
    forecast_for_utc = Column(DateTime, nullable=False)  # When forecast is FOR (kickoff)
    fetched_at_utc = Column(DateTime, nullable=False)  # When we fetched it
    forecast_horizon_hours = Column(Integer)  # How far in advance (24h, 1h, etc.)

    # Weather data
    temperature_c = Column(Float)
    wind_speed_kmh = Column(Float)
    wind_gusts_kmh = Column(Float)
    wind_direction = Column(Float)
    humidity_pct = Column(Float)
    precipitation_mm = Column(Float)
    precipitation_prob = Column(Float)
    rain_mm = Column(Float)
    snowfall_cm = Column(Float)
    cloud_cover_pct = Column(Float)
    visibility_m = Column(Float)
    surface_pressure_hpa = Column(Float)

    # Derived bands
    temp_band = Column(String)  # cold/cool/mild/warm
    wind_band = Column(String)  # calm/medium/windy
    rain_flag = Column(Boolean)
    bad_weather_flag = Column(Boolean)
    weather_severity_index = Column(Float)  # 0-1 composite

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("fixture_id", "forecast_horizon_hours", name="uix_fixture_horizon"),)


# =============================================================================
# EXECUTION / ORCHESTRATION TABLES (NON-FEATURE CONTRACTS)
# =============================================================================


class PlayerSnapshot(Base):
    """
    Player state snapshot as-of a timestamp (for deterministic backtests).

    This is NOT a feature table. It is an execution-layer contract used to:
    - reconstruct what was known at a horizon
    - build XI expectation distributions
    - support transfer/injury/value-aware aggregations
    """

    __tablename__ = "player_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(Integer, nullable=False, index=True)
    team_id = Column(Integer, index=True)  # current club as-of snapshot
    season = Column(Integer, index=True)
    as_of_utc = Column(DateTime, nullable=False, index=True)

    # Availability
    injury_status = Column(Boolean)
    injury_severity = Column(Integer)  # 1-3
    expected_return_days = Column(Integer)
    suspension_flag = Column(Boolean)

    # Form / workload (as-of safe aggregates)
    minutes_last_3 = Column(Float)
    minutes_last_5 = Column(Float)
    minutes_last_10 = Column(Float)

    # Transfermarkt value
    market_value_eur = Column(Integer)
    market_value_date = Column(DateTime)

    # Metadata
    source = Column(String)  # apifootball / transfermarkt / derived
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("player_id", "as_of_utc", name="uq_player_snapshot_player_asof"),
        Index("ix_player_snapshot_player_asof", "player_id", "as_of_utc"),
    )


class XIExpectation(Base):
    """
    Probabilistic lineup table for expected XI aggregation.

    Grain: one row per (fixture, team, player, horizon, as_of).
    """

    __tablename__ = "xi_expectations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fixture_id = Column(Integer, nullable=False, index=True)
    team_id = Column(Integer, nullable=False, index=True)
    player_id = Column(Integer, nullable=False, index=True)

    feature_horizon = Column(String, nullable=False)  # T-24h, T-1h, HT-2min
    as_of_utc = Column(DateTime, nullable=False, index=True)

    p_start = Column(Float)  # probability player starts
    p_90 = Column(Float)  # probability plays 90 (optional)
    p_sub_on = Column(Float)  # probability subbed on (optional)

    source = Column(String)  # confirmed / predicted / prior
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint(
            "fixture_id",
            "team_id",
            "player_id",
            "feature_horizon",
            "as_of_utc",
            name="uq_xi_expectation_fixture_team_player_horizon_asof",
        ),
        Index(
            "ix_xi_expectation_fixture_horizon_asof",
            "fixture_id",
            "feature_horizon",
            "as_of_utc",
        ),
    )


class HTState(Base):
    """
    Canonical half-time state snapshot used by HT feature pipeline and delta models.

    Grain: one row per fixture at an as-of timestamp near half-time (e.g., HT-2min).
    """

    __tablename__ = "ht_states"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fixture_id = Column(Integer, nullable=False, unique=True, index=True)
    timestamp_utc = Column(DateTime, nullable=False, index=True)  # as_of (HT-2min)

    # Score state
    ht_score_home = Column(Integer)
    ht_score_away = Column(Integer)

    # First-half aggregates (best available source + fallback)
    ht_xg_home = Column(Float)
    ht_xg_away = Column(Float)
    ht_shots_home = Column(Integer)
    ht_shots_away = Column(Integer)
    ht_cards_home = Column(Integer)
    ht_cards_away = Column(Integer)
    ht_dangerous_attacks_home = Column(Integer)
    ht_dangerous_attacks_away = Column(Integer)
    ht_possession_home = Column(Float)
    ht_possession_away = Column(Float)

    source_primary = Column(String)  # soccerfootball / understat / apifootball / derived
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("ix_ht_state_fixture_ts", "fixture_id", "timestamp_utc"),)


# =============================================================================
# FEATURE STORE TABLES
