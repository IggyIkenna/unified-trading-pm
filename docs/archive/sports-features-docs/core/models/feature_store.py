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
# FEATURE STORE TABLES
# =============================================================================


class TeamStyleEmbedding(Base):
    """Team style embeddings (PCA-derived latent factors)"""

    __tablename__ = "team_style_embeddings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    team_id = Column(Integer, nullable=False, index=True)

    # Period
    as_of_date = Column(DateTime, nullable=False)
    games_window = Column(Integer, default=30)  # Last N games used

    # PCA components (style factors)
    style_pc1 = Column(Float)  # Tempo/pace
    style_pc2 = Column(Float)  # Defensive structure
    style_pc3 = Column(Float)  # Pressing intensity
    style_pc4 = Column(Float)  # Verticality
    style_pc5 = Column(Float)  # Width
    style_pc6 = Column(Float)  # Set-piece reliance

    # Raw style metrics
    avg_possession = Column(Float)
    avg_shots = Column(Float)
    avg_shots_conceded = Column(Float)
    avg_dangerous_attacks = Column(Float)
    avg_ppda = Column(Float)
    avg_oppda = Column(Float)
    avg_pass_accuracy = Column(Float)
    avg_deep_completions = Column(Float)

    # Attacking style
    xg_per_shot = Column(Float)
    counter_attack_ratio = Column(Float)
    set_piece_reliance = Column(Float)
    attack_width = Column(Float)
    attack_directness = Column(Float)

    # Defensive style
    defensive_block_height = Column(Float)
    tackle_aggression = Column(Float)
    aerial_dominance = Column(Float)

    # Metadata
    league_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("ix_style_team_date", "team_id", "as_of_date"),)


class ManagerProfile(Base):
    """Manager tactical profile and form tracking"""

    __tablename__ = "manager_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    manager_id = Column(Integer, nullable=False, index=True)
    manager_name = Column(String)

    # Current assignment
    team_id = Column(Integer, index=True)
    team_name = Column(String)
    appointed_date = Column(DateTime)

    # Career stats
    career_games = Column(Integer)
    career_wins = Column(Integer)
    career_ppg = Column(Float)

    # Tactical fingerprint (career averages)
    avg_possession_career = Column(Float)
    avg_ppda_career = Column(Float)
    avg_goals_for_career = Column(Float)
    avg_goals_against_career = Column(Float)
    attacking_style_score = Column(Float)  # 0-1
    defensive_style_score = Column(Float)  # 0-1

    # Recent form (under this manager at current team)
    games_at_current_team = Column(Integer)
    ppg_at_current_team = Column(Float)
    xg_diff_at_current_team = Column(Float)
    win_rate_at_current_team = Column(Float)

    # Manager tier (1=Elite, 2=Good, 3=Average, 4=Weak)
    manager_tier = Column(Integer)

    # Metadata
    as_of_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class RefereeTeamHistory(Base):
    """Referee-team historical interactions"""

    __tablename__ = "referee_team_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    referee_id = Column(Integer, nullable=False, index=True)
    team_id = Column(Integer, nullable=False, index=True)

    # Sample
    matches_count = Column(Integer)
    as_home = Column(Integer)
    as_away = Column(Integer)

    # Results
    wins = Column(Integer)
    draws = Column(Integer)
    losses = Column(Integer)
    ref_favor_score = Column(Float)  # +ve = favors team, -ve = against

    # Cards
    total_yellows = Column(Integer)
    total_reds = Column(Integer)
    avg_yellows_per_game = Column(Float)
    avg_reds_per_game = Column(Float)
    cards_vs_league_avg = Column(Float)  # Higher = more cards under this ref

    # Penalties
    penalties_for = Column(Integer)
    penalties_against = Column(Integer)
    pen_per_game_vs_avg = Column(Float)

    # Derived
    card_chemistry = Column(Float)  # How ref treats this team
    ref_home_bias = Column(Float)  # Does ref favor home teams?

    # Metadata
    as_of_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("ix_ref_team", "referee_id", "team_id"),)


class H2HRecord(Base):
    """Head-to-head historical record between teams"""

    __tablename__ = "feature_h2h_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    home_team_id = Column(Integer, nullable=False, index=True)
    away_team_id = Column(Integer, nullable=False, index=True)

    # Overall record
    total_matches = Column(Integer)
    home_wins = Column(Integer)
    draws = Column(Integer)
    away_wins = Column(Integer)

    # Goals
    home_goals_total = Column(Integer)
    away_goals_total = Column(Integer)
    avg_home_goals = Column(Float)
    avg_away_goals = Column(Float)
    avg_total_goals = Column(Float)

    # Recent form (last 5 H2H)
    home_wins_last5 = Column(Integer)
    draws_last5 = Column(Integer)
    away_wins_last5 = Column(Integer)

    # xG (if available)
    avg_home_xg = Column(Float)
    avg_away_xg = Column(Float)

    # Patterns
    btts_rate = Column(Float)  # Both teams to score rate
    over_2_5_rate = Column(Float)
    clean_sheet_home_rate = Column(Float)
    clean_sheet_away_rate = Column(Float)

    # Venue-adjusted
    home_advantage_factor = Column(Float)  # How much home helps in this fixture

    # Last match info
    last_match_date = Column(DateTime)
    last_match_score = Column(String)  # e.g., "2-1"

    # Metadata
    as_of_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("ix_h2h_teams", "home_team_id", "away_team_id"),)


class TravelDistance(Base):
    """Pre-computed travel distances for fixtures"""

    __tablename__ = "travel_distances"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Teams
    from_team_id = Column(Integer, nullable=False, index=True)
    to_team_id = Column(Integer, nullable=False, index=True)

    # Venues
    from_venue_id = Column(Integer)
    to_venue_id = Column(Integer)
    from_city = Column(String)
    to_city = Column(String)

    # Coordinates
    from_lat = Column(Float)
    from_lon = Column(Float)
    to_lat = Column(Float)
    to_lon = Column(Float)

    # Distances
    distance_km = Column(Float)
    distance_band = Column(String)  # local (<100km), regional, national, international

    # Travel type estimation
    requires_flight = Column(Boolean)
    estimated_travel_hours = Column(Float)
    timezone_change = Column(Integer)  # Hours of timezone difference

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("ix_travel_teams", "from_team_id", "to_team_id"),)


class FeatureVector(Base):
    """Pre-computed feature vectors for ML"""

    __tablename__ = "feature_vectors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fixture_id = Column(Integer, nullable=False, index=True)

    # Feature context
    feature_horizon = Column(String, nullable=False)  # T-24h, T-1h, HT-2min
    timestamp_utc = Column(DateTime, nullable=False)

    # Feature data (stored as JSON or separate columns)
    feature_group = Column(String)  # market, team, lineup, context, etc.
    feature_name = Column(String)
    feature_value = Column(Float)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("ix_features_fixture_horizon", "fixture_id", "feature_horizon"),)


class TeamRating(Base):
    """Elo and derived team ratings"""

    __tablename__ = "feature_team_ratings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    team_id = Column(Integer, nullable=False, index=True)

    # Rating date
    as_of_date = Column(DateTime, nullable=False, index=True)

    # Ratings
    elo = Column(Float)
    attack_strength = Column(Float)
    defence_strength = Column(Float)

    # Context
    league_id = Column(Integer)
    season = Column(Integer)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)


# =============================================================================
# TRADING INTELLIGENCE TABLES 🔥
