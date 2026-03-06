from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
    UniqueConstraint,
)

from .base import Base

# =============================================================================
# SOCCERFOOTBALL.INFO TABLES
# =============================================================================


class SoccerfootballMatchStats(Base):
    """Soccerfootball.info match statistics - HT/FT stats"""

    __tablename__ = "soccerfootball_match_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fixture_id = Column(Integer, nullable=False, index=True)
    match_id = Column(Integer)  # Soccerfootball.info match ID

    # Full-time stats
    ft_goals_home = Column(Integer)
    ft_goals_away = Column(Integer)
    ft_shots_home = Column(Integer)
    ft_shots_away = Column(Integer)
    ft_shots_on_target_home = Column(Integer)
    ft_shots_on_target_away = Column(Integer)
    ft_corners_home = Column(Integer)
    ft_corners_away = Column(Integer)
    ft_fouls_home = Column(Integer)
    ft_fouls_away = Column(Integer)
    ft_yellow_cards_home = Column(Integer)
    ft_yellow_cards_away = Column(Integer)
    ft_red_cards_home = Column(Integer)
    ft_red_cards_away = Column(Integer)
    ft_possession_home = Column(Float)
    ft_possession_away = Column(Float)
    ft_xg_home = Column(Float)
    ft_xg_away = Column(Float)

    # Half-time stats (CRITICAL FOR HT MODELS)
    ht_goals_home = Column(Integer)
    ht_goals_away = Column(Integer)
    ht_shots_home = Column(Integer)
    ht_shots_away = Column(Integer)
    ht_shots_on_target_home = Column(Integer)
    ht_shots_on_target_away = Column(Integer)
    ht_corners_home = Column(Integer)
    ht_corners_away = Column(Integer)
    ht_fouls_home = Column(Integer)
    ht_fouls_away = Column(Integer)
    ht_yellow_cards_home = Column(Integer)
    ht_yellow_cards_away = Column(Integer)
    ht_red_cards_home = Column(Integer)
    ht_red_cards_away = Column(Integer)
    ht_possession_home = Column(Float)
    ht_possession_away = Column(Float)
    ht_xg_home = Column(Float)
    ht_xg_away = Column(Float)

    # Metadata
    match_kickoff_utc = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class SoccerfootballProgressiveStats(Base):
    """Soccerfootball.info progressive stats - minute-by-minute"""

    __tablename__ = "soccerfootball_progressive_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fixture_id = Column(Integer, nullable=False, index=True)
    minute = Column(Integer, nullable=False)

    # Cumulative stats at this minute
    cumulative_shots_home = Column(Integer)
    cumulative_shots_away = Column(Integer)
    cumulative_xg_home = Column(Float)
    cumulative_xg_away = Column(Float)
    cumulative_corners_home = Column(Integer)
    cumulative_corners_away = Column(Integer)
    cumulative_fouls_home = Column(Integer)
    cumulative_fouls_away = Column(Integer)
    possession_home = Column(Float)
    possession_away = Column(Float)

    __table_args__ = (UniqueConstraint("fixture_id", "minute", name="uix_fixture_minute"),)


# =============================================================================
# FOOTYSTATS TABLES
# =============================================================================


class FootystatsMatchStats(Base):
    """FootyStats match statistics - dangerous attacks, potentials"""

    __tablename__ = "footystats_match_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fixture_id = Column(Integer, nullable=False, index=True)
    footystats_match_id = Column(Integer)

    # Goals
    home_goals = Column(Integer)
    away_goals = Column(Integer)
    total_goals = Column(Integer)

    # Dangerous attacks (UNIQUE FEATURE)
    dangerous_attacks_home = Column(Integer)
    dangerous_attacks_away = Column(Integer)
    attacks_home = Column(Integer)
    attacks_away = Column(Integer)

    # PPG
    home_ppg = Column(Float)
    away_ppg = Column(Float)

    # xG
    home_xg = Column(Float)
    away_xg = Column(Float)

    # Potentials (pre-match probabilities 0-100)
    o05_potential = Column(Integer)
    o15_potential = Column(Integer)
    o25_potential = Column(Integer)
    o35_potential = Column(Integer)
    o45_potential = Column(Integer)
    btts_potential = Column(Integer)
    home_win_potential = Column(Integer)
    draw_potential = Column(Integer)
    away_win_potential = Column(Integer)

    # Metadata
    match_kickoff_utc = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class FootystatsRefereeStats(Base):
    """FootyStats referee statistics - UNIQUE FEATURE"""

    __tablename__ = "footystats_referee_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    referee_id = Column(Integer, index=True)
    referee_name = Column(String, nullable=False)

    # Match stats
    matches_officiated = Column(Integer)
    avg_yellow_cards = Column(Float)
    avg_red_cards = Column(Float)
    avg_fouls = Column(Float)
    avg_penalties = Column(Float)

    # Outcome stats
    home_win_rate = Column(Float)
    away_win_rate = Column(Float)
    draw_rate = Column(Float)
    avg_goals = Column(Float)

    # Derived
    cards_per_foul = Column(Float)
    card_rate_band = Column(String)  # low/medium/high

    # Timestamp
    as_of_date = Column(DateTime)
    season = Column(Integer)

    __table_args__ = (UniqueConstraint("referee_name", "season", name="uix_referee_season"),)


class FootystatsTeamSeasonStats(Base):
    """FootyStats team season statistics"""

    __tablename__ = "footystats_team_season_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    team_id = Column(Integer, nullable=False, index=True)
    season = Column(Integer, nullable=False)

    # Goals
    season_goals = Column(Integer)
    season_conceded = Column(Integer)

    # xG
    season_xg = Column(Float)
    season_xga = Column(Float)

    # Dangerous attacks
    season_dangerous_attacks = Column(Integer)
    season_dangerous_attacks_against = Column(Integer)

    # Other stats
    season_corners = Column(Integer)
    season_corners_against = Column(Integer)
    season_shots = Column(Integer)
    season_shots_against = Column(Integer)
    season_shots_on_target = Column(Integer)
    season_shots_on_target_against = Column(Integer)
    avg_possession = Column(Float)
    clean_sheets = Column(Integer)
    failed_to_score = Column(Integer)
    btts_count = Column(Integer)
    over25_count = Column(Integer)

    # Per game averages
    corners_per_game = Column(Float)
    shots_per_game = Column(Float)
    dangerous_attacks_per_game = Column(Float)

    __table_args__ = (UniqueConstraint("team_id", "season", name="uix_team_season_footystats"),)


# =============================================================================
# TRANSFERMARKT (APIFY) TABLES
# =============================================================================


class TransfermarktPlayer(Base):
    """Transfermarkt player data"""

    __tablename__ = "transfermarkt_players"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transfermarkt_player_id = Column(Integer, nullable=False, unique=True, index=True)
    player_id = Column(Integer, index=True)  # API-Football player_id for matching

    # Basic info
    name = Column(String)
    position = Column(String)
    date_of_birth = Column(DateTime)
    age = Column(Integer)
    nationality = Column(String)

    # Physical
    height_cm = Column(Integer)
    foot = Column(String)  # right/left/both

    # Value
    market_value_eur = Column(Integer)
    market_value_date = Column(DateTime)

    # Contract
    current_club_id = Column(Integer)
    current_club_name = Column(String)
    contract_expiry = Column(DateTime)
    shirt_number = Column(Integer)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TransfermarktInjury(Base):
    """Transfermarkt injury history"""

    __tablename__ = "transfermarkt_injuries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transfermarkt_player_id = Column(Integer, nullable=False, index=True)
    player_id = Column(Integer, index=True)  # API-Football player_id

    # Injury details
    injury_type = Column(String)
    injury_start_date = Column(DateTime, index=True)
    injury_end_date = Column(DateTime)
    days_out = Column(Integer)
    games_missed = Column(Integer)

    # Metadata
    reported_at_utc = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class TransfermarktTransfer(Base):
    """Transfermarkt transfer history"""

    __tablename__ = "transfermarkt_transfers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transfermarkt_player_id = Column(Integer, nullable=False, index=True)
    player_id = Column(Integer, index=True)

    # Transfer details
    from_club_id = Column(Integer)
    from_club_name = Column(String)
    to_club_id = Column(Integer)
    to_club_name = Column(String)
    transfer_date = Column(DateTime, index=True)
    transfer_fee_eur = Column(Integer)
    transfer_type = Column(String)  # permanent, loan, loan_return, free
    market_value_at_transfer = Column(Integer)

    # Season context
    season = Column(String)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)


class TransfermarktManager(Base):
    """Transfermarkt manager/coach data"""

    __tablename__ = "transfermarkt_managers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    manager_id = Column(Integer, index=True)
    manager_name = Column(String, nullable=False)

    # Manager details
    nationality = Column(String)
    date_of_birth = Column(DateTime)

    # Current/historical position
    club_id = Column(Integer, index=True)
    club_name = Column(String)
    appointment_date = Column(DateTime)
    departure_date = Column(DateTime)  # Null if current
    tenure_days = Column(Integer)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TransfermarktSquad(Base):
    """Transfermarkt squad composition"""

    __tablename__ = "transfermarkt_squads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    club_id = Column(Integer, nullable=False, index=True)
    team_id = Column(Integer, index=True)  # API-Football team_id
    season = Column(String, nullable=False)

    # Squad composition
    total_players = Column(Integer)
    avg_age = Column(Float)
    total_market_value = Column(Integer)
    foreigners_count = Column(Integer)
    avg_player_value = Column(Integer)

    # Position breakdown
    goalkeepers_count = Column(Integer)
    defenders_count = Column(Integer)
    midfielders_count = Column(Integer)
    forwards_count = Column(Integer)

    # Timestamp
    as_of_date = Column(DateTime)

    __table_args__ = (UniqueConstraint("club_id", "season", name="uix_club_season_squad"),)


# =============================================================================
# UNDERSTAT TABLES (5 leagues only)
# =============================================================================


class UnderstatShot(Base):
    """Understat shot-level xG data - UNIQUE FEATURE (5 leagues only)"""

    __tablename__ = "understat_shots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    shot_id = Column(Integer, unique=True, index=True)
    fixture_id = Column(Integer, index=True)  # API-Football fixture_id
    understat_match_id = Column(Integer, index=True)

    # Shot details
    minute = Column(Integer)
    player_id = Column(Integer)
    player_name = Column(String)
    team_id = Column(Integer)
    home_away = Column(String)  # 'h' or 'a'

    # Location (0-1 scale)
    x = Column(Float)
    y = Column(Float)

    # xG
    xg = Column(Float)

    # Result
    result = Column(String)  # Goal, SavedShot, MissedShots, BlockedShot, ShotOnPost, OwnGoal

    # Context
    situation = Column(String)  # OpenPlay, FromCorner, SetPiece, DirectFreekick, Penalty
    shot_type = Column(String)  # RightFoot, LeftFoot, Head, OtherBodyPart
    last_action = Column(String)  # Preceding action

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)


class UnderstatTeamStats(Base):
    """Understat team statistics - PPDA, xG (5 leagues only)"""

    __tablename__ = "understat_team_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    understat_team_id = Column(Integer, nullable=False, index=True)
    team_id = Column(Integer, index=True)  # API-Football team_id
    team_name = Column(String)
    season = Column(String, nullable=False)
    league = Column(String)  # EPL, La_liga, Serie_A, Bundesliga, Ligue_1

    # Season stats
    matches = Column(Integer)
    wins = Column(Integer)
    draws = Column(Integer)
    losses = Column(Integer)
    goals = Column(Integer)
    goals_against = Column(Integer)
    xg = Column(Float)
    xga = Column(Float)
    npxg = Column(Float)  # Non-penalty xG
    npxga = Column(Float)
    deep = Column(Integer)  # Deep completions
    deep_allowed = Column(Integer)
    ppda = Column(Float)  # PPDA (pressures per dangerous attack)
    oppda = Column(Float)  # Opponent PPDA

    # Timestamp
    as_of_date = Column(DateTime)

    __table_args__ = (UniqueConstraint("understat_team_id", "season", name="uix_understat_team_season"),)


class UnderstatMatchStats(Base):
    """Understat match-level statistics"""

    __tablename__ = "understat_match_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    understat_match_id = Column(Integer, unique=True, index=True)
    fixture_id = Column(Integer, index=True)  # API-Football fixture_id

    # Teams
    home_team = Column(String)
    away_team = Column(String)

    # Match date
    datetime_utc = Column(DateTime)

    # Goals
    home_goals = Column(Integer)
    away_goals = Column(Integer)

    # xG
    home_xg = Column(Float)
    away_xg = Column(Float)

    # Deep completions
    home_deep = Column(Integer)
    away_deep = Column(Integer)

    # PPDA
    home_ppda = Column(Float)
    away_ppda = Column(Float)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)


# =============================================================================
# ODDS API TABLES
