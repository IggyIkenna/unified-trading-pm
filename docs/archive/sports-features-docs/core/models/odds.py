from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    String,
)

from .base import Base

# =============================================================================
# ODDS API TABLES
# =============================================================================


class OddsSnapshot(Base):
    """Odds API pre-match odds snapshots"""

    __tablename__ = "odds_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fixture_id = Column(Integer, nullable=False, index=True)

    # Bookmaker
    bookmaker_key = Column(String, nullable=False)
    bookmaker_name = Column(String)

    # Timestamp
    timestamp_utc = Column(DateTime, nullable=False, index=True)
    snapshot_type = Column(
        String
    )  # T-72h, T-24h, T-6h, T-90m, T-80m, T-70m, T-60m, T-50m, T-40m, T-30m, T-20m, T-10m, T-0, HT-2min

    # H2H (1X2) odds
    odds_home = Column(Float)
    odds_draw = Column(Float)
    odds_away = Column(Float)

    # Over/Under odds (2.5 as primary)
    ou_line = Column(Float)
    ou_over = Column(Float)
    ou_under = Column(Float)

    # Asian Handicap odds
    ah_line = Column(Float)
    ah_home = Column(Float)
    ah_away = Column(Float)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index(
            "ix_odds_fixture_bookmaker_timestamp",
            "fixture_id",
            "bookmaker_key",
            "timestamp_utc",
        ),
    )


class OddsHTSnapshot(Base):
    """Odds API half-time odds snapshots - CRITICAL FOR HT MODELS"""

    __tablename__ = "odds_ht_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fixture_id = Column(Integer, nullable=False, index=True)

    # Bookmaker
    bookmaker_key = Column(String, nullable=False)
    bookmaker_name = Column(String)

    # Timestamp (HT-2min = half_time_start - 2 minutes)
    timestamp_utc = Column(DateTime, nullable=False, index=True)
    half_time_start_utc = Column(DateTime)

    # H2H (1X2) odds at half-time
    ht_odds_home = Column(Float)
    ht_odds_draw = Column(Float)
    ht_odds_away = Column(Float)

    # Over/Under at half-time
    ht_ou_line = Column(Float)
    ht_ou_over = Column(Float)
    ht_ou_under = Column(Float)

    # Asian Handicap at half-time
    ht_ah_line = Column(Float)
    ht_ah_home = Column(Float)
    ht_ah_away = Column(Float)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("ix_ht_odds_fixture_bookmaker", "fixture_id", "bookmaker_key"),)


class OddsHistory(Base):
    """
    High-frequency odds history for price dynamics/microstructure features.

    CRITICAL: This table stores bookmaker-level snapshots at high frequency
    to enable velocity, acceleration, steam detection, and lead/lag analysis.

    Target: 50-100 snapshots per fixture across all bookmakers.
    """

    __tablename__ = "odds_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fixture_id = Column(Integer, nullable=False, index=True)
    bookmaker_key = Column(String, nullable=False, index=True)

    # Timestamp (CRITICAL for velocity calculations)
    timestamp_utc = Column(DateTime, nullable=False, index=True)
    api_last_update = Column(DateTime)  # When bookmaker last updated their odds

    # ===== H2H (1X2) MARKET =====
    odds_home = Column(Float)
    odds_draw = Column(Float)
    odds_away = Column(Float)

    # Implied probabilities (pre-computed for efficiency)
    prob_home = Column(Float)  # 1 / odds_home (vig-included)
    prob_draw = Column(Float)
    prob_away = Column(Float)

    # ===== ASIAN HANDICAP =====
    ah_line = Column(Float)  # e.g., -0.5, -1.0, -1.5
    odds_ah_home = Column(Float)
    odds_ah_away = Column(Float)

    # ===== TOTALS (O/U) =====
    ou_line = Column(Float)  # e.g., 2.5, 3.0
    odds_over = Column(Float)
    odds_under = Column(Float)

    # ===== BOOKMAKER METADATA =====
    bookmaker_type = Column(String)  # 'sharp' or 'soft'
    bookmaker_region = Column(String)  # 'asian', 'european', 'us'

    # ===== COMPUTED DELTA (vs previous snapshot) =====
    # These can be computed on insert or via query
    delta_prob_home = Column(Float)  # Change from previous snapshot
    delta_prob_away = Column(Float)
    delta_prob_draw = Column(Float)
    time_since_prev_seconds = Column(Integer)  # Time since previous snapshot

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index(
            "ix_odds_history_fixture_book_time",
            "fixture_id",
            "bookmaker_key",
            "timestamp_utc",
        ),
        Index("ix_odds_history_bookmaker_time", "bookmaker_key", "timestamp_utc"),
    )


class OddsMicrostructure(Base):
    """
    Pre-computed price dynamics features per fixture.

    Computed from OddsHistory after odds collection is complete.
    One row per fixture with all microstructure features.
    """

    __tablename__ = "odds_microstructure"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fixture_id = Column(Integer, nullable=False, unique=True, index=True)
    computed_at = Column(DateTime, default=datetime.utcnow)

    # ===== VELOCITY FEATURES (12) =====
    velocity_home_24h_to_6h = Column(Float)
    velocity_home_6h_to_1h = Column(Float)
    velocity_home_1h_to_10m = Column(Float)
    velocity_home_10m_to_0 = Column(Float)
    velocity_away_24h_to_6h = Column(Float)
    velocity_away_6h_to_1h = Column(Float)
    velocity_away_1h_to_10m = Column(Float)
    velocity_away_10m_to_0 = Column(Float)
    velocity_draw_24h_to_6h = Column(Float)
    velocity_draw_6h_to_1h = Column(Float)
    velocity_draw_1h_to_10m = Column(Float)
    velocity_draw_10m_to_0 = Column(Float)

    # ===== ACCELERATION FEATURES (6) =====
    accel_home_early = Column(Float)  # velocity_6h_to_1h - velocity_24h_to_6h
    accel_home_late = Column(Float)  # velocity_1h_to_0 - velocity_6h_to_1h
    accel_away_early = Column(Float)
    accel_away_late = Column(Float)
    accel_draw_early = Column(Float)
    accel_draw_late = Column(Float)

    # ===== VOLATILITY FEATURES (8) =====
    volatility_home_24h = Column(Float)  # Std dev of prob changes
    volatility_away_24h = Column(Float)
    volatility_draw_24h = Column(Float)
    path_smoothness_home = Column(Float)  # 1 = smooth, 0 = jumpy
    path_smoothness_away = Column(Float)
    max_single_move_home = Column(Float)  # Largest single delta
    max_single_move_away = Column(Float)
    volatility_ratio = Column(Float)  # vol_home / vol_away

    # ===== STEAM DETECTION (6) =====
    steam_detected_home = Column(Boolean, default=False)
    steam_detected_away = Column(Boolean, default=False)
    steam_magnitude_home = Column(Float)
    steam_magnitude_away = Column(Float)
    steam_timing_home = Column(Float)  # Hours before kickoff
    steam_timing_away = Column(Float)

    # ===== BOOKMAKER MICROSTRUCTURE (13) =====
    pinnacle_lead_time_home = Column(Float)  # Minutes before others
    pinnacle_lead_time_away = Column(Float)
    bet365_lag_home = Column(Float)  # Minutes after Pinnacle
    bet365_lag_away = Column(Float)
    asian_leads_european = Column(Boolean)
    sbo_pinnacle_delta_home = Column(Float)  # Sharp disagreement
    sbo_pinnacle_delta_away = Column(Float)
    book_fragmentation_home = Column(Float)  # Std dev across books
    book_fragmentation_away = Column(Float)
    books_in_sync = Column(Boolean)
    pinnacle_vs_market_home = Column(Float)
    pinnacle_vs_market_away = Column(Float)
    sharp_soft_spread = Column(Float)  # Sharp avg - Soft avg

    # ===== REVERSE LINE MOVEMENT (4) =====
    rlm_detected_home = Column(Boolean, default=False)
    rlm_detected_away = Column(Boolean, default=False)
    rlm_magnitude_home = Column(Float)
    rlm_magnitude_away = Column(Float)

    # ===== FIRST/LAST MOVER (4) =====
    first_mover_bookmaker = Column(String)
    first_mover_time_before_ko = Column(Float)  # Hours
    last_significant_move_time = Column(Float)  # Hours before KO
    total_snapshots_collected = Column(Integer)


class LeagueEfficiency(Base):
    """
    Market efficiency scores by league.

    Pre-computed based on historical market analysis.
    Used for weighting predictions and setting priors.
    """

    __tablename__ = "league_efficiency"

    id = Column(Integer, primary_key=True, autoincrement=True)
    league_id = Column(Integer, nullable=False, unique=True, index=True)
    league_name = Column(String)

    # Efficiency metrics
    efficiency_score = Column(Float)  # 0-1, higher = more efficient
    efficiency_tier = Column(Integer)  # 1-5 (1 = hyper-efficient)
    typical_edge_pct = Column(Float)  # Expected edge % (e.g., 0.02 = 2%)

    # Market characteristics
    sharp_book_coverage = Column(Integer)  # # of sharp books covering
    pinnacle_available = Column(Boolean, default=False)
    betfair_liquidity = Column(Float)  # Avg exchange volume
    avg_bookmaker_count = Column(Integer)
    avg_margin = Column(Float)  # Avg vig across books

    # Historical stats
    avg_odds_variance = Column(Float)  # Variance across bookmakers
    steam_frequency = Column(Float)  # How often steam moves occur
    closing_line_accuracy = Column(Float)  # How often CL beats open

    # Metadata
    last_updated = Column(DateTime, default=datetime.utcnow)


class BookmakerMeta(Base):
    """
    Bookmaker classification and characteristics.

    Used for sharp/soft separation, weighting, and microstructure.
    """

    __tablename__ = "bookmaker_meta"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bookmaker_key = Column(String, nullable=False, unique=True, index=True)
    bookmaker_name = Column(String)

    # Classification
    bookmaker_type = Column(String)  # 'sharp', 'exchange', 'semi_sharp', 'recreational'
    region = Column(String)  # 'asian', 'european', 'uk', 'us', 'global'

    # Weighting (0-1, higher = more trust)
    weight = Column(Float, default=0.5)

    # Characteristics
    accepts_sharp_money = Column(Boolean, default=False)
    limits_winners = Column(Boolean, default=True)
    avg_margin = Column(Float)  # Typical overround
    max_stake_eur = Column(Float)  # Max bet allowed

    # Lead/lag characteristics
    typical_lead_time_mins = Column(Float)  # How early they move vs average
    follows_pinnacle = Column(Boolean, default=True)

    # Coverage
    leagues_covered = Column(Integer)  # # of leagues with odds

    # Metadata
    last_updated = Column(DateTime, default=datetime.utcnow)


class SharpSoftSnapshot(Base):
    """
    Pre-computed sharp vs soft consensus per fixture.

    Computed at each prediction timepoint (T-24h, T-1h, etc.)
    """

    __tablename__ = "sharp_soft_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fixture_id = Column(Integer, nullable=False, index=True)
    timestamp_utc = Column(DateTime, nullable=False)

    # Sharp consensus
    sharp_prob_home = Column(Float)
    sharp_prob_draw = Column(Float)
    sharp_prob_away = Column(Float)
    sharp_book_count = Column(Integer)

    # Soft consensus
    soft_prob_home = Column(Float)
    soft_prob_draw = Column(Float)
    soft_prob_away = Column(Float)
    soft_book_count = Column(Integer)

    # KEY: Sharp-Soft Delta (leading indicator)
    sharp_soft_delta_home = Column(Float)
    sharp_soft_delta_draw = Column(Float)
    sharp_soft_delta_away = Column(Float)

    # Weighted consensus (sharps count more)
    weighted_prob_home = Column(Float)
    weighted_prob_away = Column(Float)

    # Market quality at this time
    book_fragmentation = Column(Float)  # Std dev across all books
    max_min_spread = Column(Float)

    __table_args__ = (Index("ix_sharp_soft_fixture_time", "fixture_id", "timestamp_utc"),)


# =============================================================================
# WEATHER TABLES
