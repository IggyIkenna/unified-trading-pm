"""
Database Models for Sports Betting Service

=============================================================================
TABLE CATEGORIES (56 tables total)
=============================================================================

CORE DATA (API-Football) - 12 tables:
- Country, Venue, League, Team, Player, Fixture
- FixtureStats, FixtureEvent, FixtureLineup, FixturePlayerStats
- Injury, Standing

EXTERNAL DATA SOURCES - 14 tables:
- Soccerfootball: SoccerfootballMatchStats, SoccerfootballProgressiveStats
- FootyStats: FootystatsMatchStats, FootystatsRefereeStats, FootystatsTeamSeasonStats
- Transfermarkt: TransfermarktPlayer, TransfermarktInjury, TransfermarktTransfer, TransfermarktManager, TransfermarktSquad
- Understat: UnderstatShot, UnderstatTeamStats, UnderstatMatchStats
- Weather: WeatherForecast

ODDS DATA - 6 tables:
- OddsSnapshot, OddsHTSnapshot, OddsHistory
- OddsMicrostructure, BookmakerMeta, SharpSoftSnapshot
- LeagueEfficiency

FEATURE STORE - 8 tables:
- FeatureVector, TeamRating, MultiSourceXG
- TeamStyleEmbedding, ManagerProfile, RefereeTeamHistory
- H2HRecord, TravelDistance

ML MODEL REGISTRY - 4 tables:
- MLModelRegistry, WalkForwardFold, FeatureImportance, PredictionLog

TRADING INTELLIGENCE - 10 tables:
- Signal, BetRecommendation, BetExecution
- DriftAlert, BankrollSnapshot, DailyPnL
- ModelPerformance, MarketSimulation, EnsemblePrediction

ARBITRAGE - 2 tables:
- ArbOpportunity, ArbBucketStats

=============================================================================

Version: 3.0
Last Updated: December 2025
"""

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase

# Note: Import engine from your database module
# from database import engine


class Base(DeclarativeBase):
    pass


# =============================================================================
# CORE TABLES (API-Football)
# =============================================================================


class Country(Base):
    """Countries table - stores country information"""

    __tablename__ = "countries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    code = Column(String, nullable=False)
    flag = Column(String)

    # Data Fetched Flags
    leagues_fetched = Column(Boolean, default=False)
    venues_fetched = Column(Boolean, default=False)


class Venue(Base):
    """Venues/Stadiums table"""

    __tablename__ = "venues"

    id = Column(Integer, primary_key=True, autoincrement=True)
    venue_id = Column(Integer, nullable=False, unique=True, index=True)
    name = Column(String, nullable=False)
    address = Column(String)
    city = Column(String)
    country = Column(String)
    capacity = Column(Integer)
    surface = Column(String)
    image = Column(String)

    # Geo data (for weather API)
    latitude = Column(Float)
    longitude = Column(Float)
    altitude = Column(Float)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class League(Base):
    """Leagues/Competitions table"""

    __tablename__ = "leagues"

    id = Column(Integer, primary_key=True, autoincrement=True)
    league_id = Column(Integer, nullable=False, index=True)
    league_name = Column(String, nullable=False)
    country = Column(String, nullable=False)
    country_code = Column(String, nullable=False)
    season = Column(Integer, nullable=False)
    start = Column(DateTime, nullable=False)
    end = Column(DateTime, nullable=False)
    current = Column(Boolean)

    # API-Football feature flags
    events = Column(Boolean)
    lineups = Column(Boolean)
    statistics_fixtures = Column(Boolean)
    statistics_players = Column(Boolean)
    standings = Column(Boolean)
    players = Column(Boolean)
    top_scorers = Column(Boolean)
    top_assists = Column(Boolean)
    top_cards = Column(Boolean)
    injuries = Column(Boolean)
    predictions = Column(Boolean)
    odds = Column(Boolean)

    # Data Fetched Flags
    teams_fetched = Column(Boolean, default=False)
    fixtures_fetched = Column(Boolean, default=False)
    injuries_fetched = Column(Boolean, default=False)
    predictions_fetched = Column(Boolean, default=False)
    odds_fetched = Column(Boolean, default=False)

    __table_args__ = (
        UniqueConstraint("league_id", "season", name="uix_league_season"),
    )


class Team(Base):
    """Teams table with cross-provider IDs"""

    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, autoincrement=True)
    team_id = Column(Integer, nullable=False, index=True)
    team_name = Column(String, nullable=False)
    team_code = Column(String)
    team_country = Column(String)
    team_founded = Column(Integer)
    team_national = Column(Boolean)
    team_logo = Column(String)

    # Venue info
    venue_id = Column(Integer)
    venue_name = Column(String)
    venue_address = Column(String)
    venue_city = Column(String)
    venue_capacity = Column(Integer)
    venue_surface = Column(String)
    venue_image = Column(String)

    # Season/League context
    season = Column(Integer)
    league_id = Column(Integer)

    # Cross-provider IDs for matching
    understat_team_id = Column(Integer)
    understat_team_name = Column(String)
    understat_league = Column(String)
    understat_match_score = Column(Float)
    understat_match_type = Column(String)
    footystats_team_id = Column(Integer)
    soccerfootball_team_id = Column(Integer)
    transfermarkt_team_id = Column(Integer)
    transfermarkt_slug = Column(String)

    # Geo data
    home_city = Column(String)
    home_lat = Column(Float)
    home_lon = Column(Float)

    __table_args__ = (UniqueConstraint("team_id", "season", name="uix_team_season"),)


class Player(Base):
    """Players table with cross-provider IDs"""

    __tablename__ = "players"

    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(Integer, nullable=False, unique=True, index=True)

    # Basic info
    name = Column(String)
    firstname = Column(String)
    lastname = Column(String)
    age = Column(Integer)
    nationality = Column(String)

    # Physical attributes
    height = Column(String)
    weight = Column(String)

    # Playing info
    number = Column(Integer)
    position = Column(String)
    photo = Column(String)

    # Birth information
    birth_date = Column(String)
    birth_place = Column(String)
    birth_country = Column(String)

    # Cross-provider IDs
    understat_player_id = Column(Integer)
    transfermarkt_player_id = Column(Integer)
    footystats_player_id = Column(Integer)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Fixture(Base):
    """Fixtures/Matches table"""

    __tablename__ = "fixtures"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fixture_id = Column(Integer, nullable=False, unique=True, index=True)
    referee = Column(String)
    date = Column(DateTime)
    timestamp = Column(DateTime)
    kickoff_utc = Column(DateTime, index=True)  # Canonical kickoff time
    periods_first = Column(DateTime)
    periods_second = Column(DateTime)

    # Venue
    venue_id = Column(Integer)
    venue_name = Column(String)
    venue_city = Column(String)

    # Status
    status_long = Column(String)
    status_short = Column(String)
    status_elapsed_time = Column(Float)

    # League
    league_id = Column(Integer, index=True)
    league_name = Column(String)
    season = Column(Integer, index=True)
    round = Column(String)

    # Teams
    home_team_id = Column(Integer, index=True)
    home_team_name = Column(String)
    away_team_id = Column(Integer, index=True)
    away_team_name = Column(String)
    winner_team_id = Column(Integer)
    winner_team_name = Column(String)

    # Scores
    home_score = Column(Float)
    away_score = Column(Float)
    home_score_halftime = Column(Float)
    away_score_halftime = Column(Float)
    home_score_fulltime = Column(Float)
    away_score_fulltime = Column(Float)
    home_score_extratime = Column(Float)
    away_score_extratime = Column(Float)
    home_score_penalty = Column(Float)
    away_score_penalty = Column(Float)

    # Data Fetched Flags
    fixture_stats_fetched = Column(Boolean, default=False)
    fixture_events_fetched = Column(Boolean, default=False)
    fixture_lineups_fetched = Column(Boolean, default=False)
    fixture_player_stats_fetched = Column(Boolean, default=False)
    fixture_injuries_fetched = Column(Boolean, default=False)
    soccerfootball_stats_fetched = Column(Boolean, default=False)
    footystats_fetched = Column(Boolean, default=False)
    understat_fetched = Column(Boolean, default=False)
    odds_fetched = Column(Boolean, default=False)
    weather_fetched = Column(Boolean, default=False)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FixtureStats(Base):
    """Fixture Statistics table - team-level statistics per fixture (API-Football)"""

    __tablename__ = "fixture_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fixture_id = Column(Integer, nullable=False, index=True)
    team_id = Column(Integer, nullable=False)
    team_name = Column(String)

    # Shooting
    shots_on_goal = Column(Integer)
    shots_off_goal = Column(Integer)
    total_shots = Column(Integer)
    blocked_shots = Column(Integer)
    shots_insidebox = Column(Integer)
    shots_outsidebox = Column(Integer)

    # Other stats
    fouls = Column(Integer)
    corner_kicks = Column(Integer)
    offsides = Column(Float)
    ball_possession = Column(String)
    yellow_cards = Column(Float)
    red_cards = Column(Float)
    goalkeeper_saves = Column(Float)
    total_passes = Column(Integer)
    passes_accurate = Column(Integer)
    passes_percentage = Column(String)
    expected_goals = Column(Float)
    goals_prevented = Column(Float)

    __table_args__ = (
        UniqueConstraint("fixture_id", "team_id", name="uix_fixture_team_stats"),
    )


class FixtureEvent(Base):
    """Fixture Events table - in-game events (goals, cards, substitutions)"""

    __tablename__ = "fixture_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fixture_id = Column(Integer, nullable=False, index=True)
    team_id = Column(Integer)
    team_name = Column(String)
    player_id = Column(Float)
    player_name = Column(String)
    time = Column(Float)  # Match minute
    extra = Column(Float)  # Stoppage time
    assist_id = Column(Float)
    assist_name = Column(String)
    type = Column(String)  # Goal, Card, subst, Var
    detail = Column(String)  # Normal Goal, Yellow Card, etc.
    comments = Column(Text)


class FixtureLineup(Base):
    """Fixture Lineups table - starting lineups and formations"""

    __tablename__ = "fixture_lineups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fixture_id = Column(Integer, nullable=False, index=True)
    team_id = Column(Integer, nullable=False)
    team_name = Column(String)
    coach_id = Column(Float)
    coach_name = Column(String)
    formation = Column(String)
    player_id = Column(Integer)
    player_name = Column(String)
    player_number = Column(Integer)
    player_pos = Column(String)
    player_grid = Column(String)
    is_substitute = Column(Boolean, default=False)

    # Lineup type and timestamp tracking (CRITICAL for anti-leakage)
    lineup_type = Column(String)  # 'expected' or 'confirmed'
    announced_at_utc = Column(DateTime, index=True)  # When lineup was first received
    source = Column(String)  # 'api_football', 'predicted', 'news_scrape'

    # For fallback tracking
    prediction_confidence = Column(Float)  # 0-1, how confident we are in predicted XI


class FixturePlayerStats(Base):
    """Fixture Player Statistics table - detailed player statistics per fixture"""

    __tablename__ = "fixture_player_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fixture_id = Column(Integer, nullable=False, index=True)
    team_id = Column(Integer, nullable=False)
    team_name = Column(String)
    player_id = Column(Integer)
    player_name = Column(String)
    minutes = Column(Float)
    number = Column(Integer)
    position = Column(String)
    rating = Column(Float)
    captain = Column(Boolean)
    substitute = Column(Boolean)
    offsides = Column(Float)
    shots_total = Column(Float)
    shots_on = Column(Float)
    goals_total = Column(Float)
    goals_conceded = Column(Float)
    goals_assists = Column(Float)
    goals_saves = Column(Float)
    passes_total = Column(Float)
    passes_key = Column(Float)
    passes_accuracy = Column(String)
    tackles_total = Column(Float)
    tackles_blocks = Column(Float)
    tackles_interceptions = Column(Float)
    duels_total = Column(Float)
    duels_won = Column(Float)
    dribbles_attempts = Column(Float)
    dribbles_success = Column(Float)
    dribbles_past = Column(Float)
    fouls_drawn = Column(Float)
    fouls_committed = Column(Float)
    cards_yellow = Column(Integer)
    cards_red = Column(Integer)
    penalty_won = Column(Float)
    penalty_commited = Column(Float)
    penalty_scored = Column(Integer)
    penalty_missed = Column(Integer)
    penalty_saved = Column(Float)


class Injury(Base):
    """Injuries table - player injuries per fixture (API-Football)"""

    __tablename__ = "injuries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fixture_id = Column(Integer, nullable=False, index=True)
    player_id = Column(Integer)
    player_name = Column(String)
    reason = Column(String)
    team_id = Column(Integer)
    team_name = Column(String)


class Standing(Base):
    """League Standings table"""

    __tablename__ = "standings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    league_id = Column(Integer, nullable=False, index=True)
    season = Column(Integer, nullable=False)
    team_id = Column(Integer, nullable=False, index=True)
    team_name = Column(String)

    # Position
    rank = Column(Integer)
    points = Column(Integer)
    goal_diff = Column(Integer)
    group_name = Column(String)
    form = Column(String)  # Last 5 results (e.g., "WWDLW")
    status = Column(String)  # Promotion/relegation
    description = Column(String)

    # All matches
    all_played = Column(Integer)
    all_win = Column(Integer)
    all_draw = Column(Integer)
    all_lose = Column(Integer)
    all_goals_for = Column(Integer)
    all_goals_against = Column(Integer)

    # Home matches
    home_played = Column(Integer)
    home_win = Column(Integer)
    home_draw = Column(Integer)
    home_lose = Column(Integer)
    home_goals_for = Column(Integer)
    home_goals_against = Column(Integer)

    # Away matches
    away_played = Column(Integer)
    away_win = Column(Integer)
    away_draw = Column(Integer)
    away_lose = Column(Integer)
    away_goals_for = Column(Integer)
    away_goals_against = Column(Integer)

    # Timestamp
    as_of_date = Column(DateTime, index=True)  # Snapshot date


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

    __table_args__ = (
        UniqueConstraint("fixture_id", "minute", name="uix_fixture_minute"),
    )


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

    __table_args__ = (
        UniqueConstraint("referee_name", "season", name="uix_referee_season"),
    )


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

    __table_args__ = (
        UniqueConstraint("team_id", "season", name="uix_team_season_footystats"),
    )


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

    __table_args__ = (
        UniqueConstraint("club_id", "season", name="uix_club_season_squad"),
    )


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
    result = Column(
        String
    )  # Goal, SavedShot, MissedShots, BlockedShot, ShotOnPost, OwnGoal

    # Context
    situation = Column(
        String
    )  # OpenPlay, FromCorner, SetPiece, DirectFreekick, Penalty
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

    __table_args__ = (
        UniqueConstraint(
            "understat_team_id", "season", name="uix_understat_team_season"
        ),
    )


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

    __table_args__ = (
        Index("ix_ht_odds_fixture_bookmaker", "fixture_id", "bookmaker_key"),
    )


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

    __table_args__ = (
        Index("ix_sharp_soft_fixture_time", "fixture_id", "timestamp_utc"),
    )


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
    forecast_for_utc = Column(
        DateTime, nullable=False
    )  # When forecast is FOR (kickoff)
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

    __table_args__ = (
        UniqueConstraint(
            "fixture_id", "forecast_horizon_hours", name="uix_fixture_horizon"
        ),
    )


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
        UniqueConstraint(
            "player_id", "as_of_utc", name="uq_player_snapshot_player_asof"
        ),
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

    source_primary = Column(
        String
    )  # soccerfootball / understat / apifootball / derived
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("ix_ht_state_fixture_ts", "fixture_id", "timestamp_utc"),)


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

    __table_args__ = (
        Index("ix_features_fixture_horizon", "fixture_id", "feature_horizon"),
    )


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
# =============================================================================


class BetRecommendation(Base):
    """Bet recommendations from the model pipeline"""

    __tablename__ = "bet_recommendations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fixture_id = Column(Integer, nullable=False, index=True)

    # Timing
    prediction_horizon = Column(String)  # T-24h, T-1h, HT-2min
    created_at = Column(DateTime, default=datetime.utcnow)
    execute_at = Column(DateTime)  # When to place bet

    # Market
    market = Column(String, nullable=False)  # home, draw, away, over_2.5, ah_-0.5, etc.
    bookmaker = Column(String)

    # Predictions
    predicted_prob = Column(Float)
    market_prob = Column(Float)
    edge = Column(Float)
    confidence = Column(Float)

    # Stake
    recommended_stake = Column(Float)
    stake_pct = Column(Float)
    kelly_raw = Column(Float)

    # Status
    status = Column(String, default="pending")  # pending, executed, skipped, expired
    skip_reason = Column(String)  # edge_too_small, variance_too_high, etc.

    # Model info
    model_version = Column(String)
    ensemble_weights = Column(JSON)

    __table_args__ = (Index("ix_bet_rec_fixture_market", "fixture_id", "market"),)


class BetExecution(Base):
    """Actual bet executions and results"""

    __tablename__ = "bet_executions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    recommendation_id = Column(Integer, ForeignKey("bet_recommendations.id"))
    fixture_id = Column(Integer, nullable=False, index=True)

    # Execution details
    executed_at = Column(DateTime, default=datetime.utcnow)
    bookmaker = Column(String)
    market = Column(String)

    # Odds & stake
    entry_odds = Column(Float)
    stake = Column(Float)
    potential_return = Column(Float)

    # Results (filled after match)
    closing_odds = Column(Float)
    result = Column(String)  # win, loss, push, void
    pnl = Column(Float)

    # CLV tracking
    clv = Column(Float)  # closing_prob - entry_prob
    clv_percentage = Column(Float)  # clv / entry_prob * 100

    # Metadata
    match_result = Column(String)  # 1, X, 2
    final_score_home = Column(Integer)
    final_score_away = Column(Integer)


class DriftAlert(Base):
    """Model and data drift alerts"""

    __tablename__ = "drift_alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Alert details
    alert_type = Column(
        String, nullable=False
    )  # feature_drift, prediction_drift, calibration_drift, clv_profit_drift
    severity = Column(String)  # low, medium, high, critical

    # Metrics
    metric_name = Column(String)  # ks_statistic, calibration_error, clv_correlation
    metric_value = Column(Float)
    threshold = Column(Float)

    # Context
    feature_name = Column(String)  # If feature drift
    model_name = Column(String)
    league_id = Column(Integer)

    # Timestamps
    detected_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)

    # Action
    recommended_action = Column(
        String
    )  # investigate, retrain, recalibrate, halt_betting
    action_taken = Column(String)


class BankrollSnapshot(Base):
    """Daily bankroll tracking for risk management"""

    __tablename__ = "bankroll_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Date
    snapshot_date = Column(DateTime, nullable=False, index=True)

    # Bankroll
    bankroll = Column(Float)
    daily_pnl = Column(Float)

    # Exposure
    daily_staked = Column(Float)
    daily_bets = Column(Integer)

    # Performance
    win_rate = Column(Float)
    avg_clv = Column(Float)
    roi = Column(Float)

    # Risk metrics
    current_drawdown = Column(Float)
    max_drawdown = Column(Float)
    sharpe_ratio = Column(Float)

    # Staking adjustments
    kelly_fraction_used = Column(Float)
    drawdown_modifier = Column(Float)


class ModelPerformance(Base):
    """Track model performance over time"""

    __tablename__ = "model_performance"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Model
    model_name = Column(String, nullable=False, index=True)
    model_version = Column(String)

    # Time period
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)

    # Performance metrics
    n_predictions = Column(Integer)
    n_bets_placed = Column(Integer)

    # Accuracy
    mae = Column(Float)  # Mean absolute error
    rmse = Column(Float)
    r2_score = Column(Float)

    # Calibration
    brier_score = Column(Float)
    log_loss = Column(Float)
    calibration_error = Column(Float)

    # CLV
    avg_clv = Column(Float)
    clv_positive_rate = Column(Float)

    # PnL
    total_pnl = Column(Float)
    roi = Column(Float)
    win_rate = Column(Float)

    # By league
    league_id = Column(Integer)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)


class MarketSimulation(Base):
    """Results from synthetic market simulations"""

    __tablename__ = "market_simulations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fixture_id = Column(Integer, nullable=False, index=True)

    # Simulation params
    simulated_at = Column(DateTime, default=datetime.utcnow)
    current_odds_home = Column(Float)
    current_odds_draw = Column(Float)
    current_odds_away = Column(Float)
    hours_to_kickoff = Column(Float)

    # Simulation results (for home market)
    expected_closing_odds_home = Column(Float)
    expected_ev_now = Column(Float)
    expected_ev_wait = Column(Float)
    ev_95th_percentile = Column(Float)
    ev_5th_percentile = Column(Float)

    # Recommendation
    optimal_action = Column(String)  # bet_now, wait
    optimal_entry_time = Column(String)  # T-30m, T-10m, etc.
    expected_slippage = Column(Float)


class ArbOpportunity(Base):
    """Track arbitrage opportunities by bucket"""

    __tablename__ = "arb_opportunities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fixture_id = Column(Integer, nullable=False, index=True)

    # Timing
    detected_at = Column(DateTime, default=datetime.utcnow)
    market = Column(String)  # home, draw, away, over_2.5, etc.

    # Back side
    back_book = Column(String, nullable=False)
    back_book_type = Column(String)  # sharp, soft, exchange, semi_sharp
    back_odds = Column(Float)
    back_stake = Column(Float)

    # Lay side
    lay_book = Column(String, nullable=False)
    lay_book_type = Column(String)
    lay_odds = Column(Float)
    lay_stake = Column(Float)

    # Classification
    bucket = Column(String, nullable=False)  # soft_sharp, soft_soft, soft_exchange
    edge_pct = Column(Float)
    expected_edge_min = Column(Float)
    expected_edge_max = Column(Float)
    risk_score = Column(Float)

    # Validation
    edge_valid = Column(Boolean)
    suspicious = Column(Boolean)
    suspicious_reason = Column(String)

    # Execution
    executed = Column(Boolean, default=False)
    execution_status = Column(String)  # success, partial, failed, skipped
    actual_back_odds = Column(Float)  # May differ from detected
    actual_lay_odds = Column(Float)

    # Results
    profitable = Column(Boolean)
    realized_edge = Column(Float)
    pnl = Column(Float)

    __table_args__ = (Index("ix_arb_fixture_bucket", "fixture_id", "bucket"),)


class ArbBucketStats(Base):
    """Aggregate stats by arb bucket for analysis"""

    __tablename__ = "arb_bucket_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Period
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    bucket = Column(String, nullable=False)  # soft_sharp, soft_soft, soft_exchange

    # Volume
    n_opportunities = Column(Integer)
    n_executed = Column(Integer)
    n_profitable = Column(Integer)

    # Edge stats
    avg_edge = Column(Float)
    median_edge = Column(Float)
    std_edge = Column(Float)
    min_edge = Column(Float)
    max_edge = Column(Float)

    # Performance
    hit_rate = Column(Float)  # % profitable
    avg_roi = Column(Float)
    total_pnl = Column(Float)

    # Risk
    avg_risk_score = Column(Float)
    max_loss = Column(Float)

    __table_args__ = (Index("ix_arb_stats_period_bucket", "period_start", "bucket"),)


class MultiSourceXG(Base):
    """Store xG from multiple sources for comparison"""

    __tablename__ = "multi_source_xg"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fixture_id = Column(Integer, nullable=False, index=True)
    team = Column(String, nullable=False)  # home, away

    # xG from each source
    xg_understat = Column(Float)  # 5 leagues, shot-level
    xg_soccerfootball = Column(Float)  # 35 leagues, match-level
    xg_footystats = Column(Float)  # 33 of 35 leagues, team-level
    xg_apifootball = Column(Float)  # 35 leagues, basic
    xg_synthetic = Column(Float)  # Our trained model

    # Half-time xG (where available)
    ht_xg_understat = Column(Float)
    ht_xg_soccerfootball = Column(Float)

    # Non-penalty xG (Understat only)
    npxg_understat = Column(Float)

    # Derived features
    xg_consensus = Column(Float)  # Mean of available sources
    xg_disagreement = Column(Float)  # Std of available sources
    xg_range = Column(Float)  # Max - min
    xg_source_count = Column(Integer)  # How many sources available

    # Best source used
    xg_used = Column(Float)  # Final xG value
    xg_source_primary = Column(String)  # understat, soccerfootball, etc.
    xg_confidence = Column(Float)  # 1.0 for understat, 0.7 for synthetic

    # Metadata
    league_id = Column(Integer)
    is_understat_league = Column(Boolean)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("ix_xg_fixture_team", "fixture_id", "team"),)


# =============================================================================
# ML MODEL REGISTRY
# =============================================================================


class MLModelRegistry(Base):
    """Track trained ML models and versions"""

    __tablename__ = "ml_model_registry"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Model identification
    model_name = Column(String, nullable=False, index=True)  # model_2a, model_3b, etc.
    model_type = Column(String)  # catboost, xgboost, lightgbm, huber, ridge
    version = Column(String, nullable=False)  # v1.0.0

    # Training info
    trained_at = Column(DateTime)
    training_start_date = Column(DateTime)
    training_end_date = Column(DateTime)
    fold = Column(Integer)  # Walk-forward fold number

    # Hyperparameters (JSON string)
    hyperparameters = Column(Text)

    # Performance metrics
    train_mae = Column(Float)
    val_mae = Column(Float)
    test_mae = Column(Float)
    train_rmse = Column(Float)
    val_rmse = Column(Float)
    test_rmse = Column(Float)
    r2_score = Column(Float)

    # For probabilistic models
    brier_score = Column(Float)
    log_loss = Column(Float)
    calibration_error = Column(Float)

    # Storage
    model_path = Column(String)  # Path to saved model file
    scaler_path = Column(String)  # Path to scaler if used

    # Status
    is_production = Column(Boolean, default=False)
    deprecated = Column(Boolean, default=False)
    deprecated_reason = Column(String)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("ix_model_name_version", "model_name", "version"),)


class WalkForwardFold(Base):
    """Track walk-forward validation folds"""

    __tablename__ = "walk_forward_folds"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Fold identification
    fold_number = Column(Integer, nullable=False)
    test_year = Column(Integer, nullable=False)

    # Date ranges
    train_start = Column(DateTime)
    train_end = Column(DateTime)
    test_start = Column(DateTime)
    test_end = Column(DateTime)

    # Sample sizes
    train_samples = Column(Integer)
    test_samples = Column(Integer)

    # Models trained in this fold
    models_trained = Column(Text)  # JSON list of model_ids

    # Aggregate performance
    avg_mae = Column(Float)
    avg_rmse = Column(Float)
    avg_clv = Column(Float)
    test_roi = Column(Float)

    # Status
    completed_at = Column(DateTime)
    status = Column(String)  # pending, training, complete, failed

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)


class FeatureImportance(Base):
    """Store feature importance from tree models"""

    __tablename__ = "feature_importance"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Model reference
    model_id = Column(Integer, ForeignKey("ml_model_registry.id"))
    model_name = Column(String)

    # Feature
    feature_name = Column(String, nullable=False)
    feature_group = Column(String)  # market, team, lineup, context, etc.

    # Importance scores
    importance_score = Column(Float)  # Gain-based
    importance_rank = Column(Integer)
    importance_pct = Column(Float)  # Percentage of total

    # SHAP values (if computed)
    shap_mean_abs = Column(Float)
    shap_std = Column(Float)

    # Metadata
    computed_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("ix_importance_model", "model_id", "importance_rank"),)


class PredictionLog(Base):
    """Log all predictions for analysis and audit"""

    __tablename__ = "prediction_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fixture_id = Column(Integer, nullable=False, index=True)

    # Timing
    prediction_time = Column(DateTime, nullable=False)
    prediction_horizon = Column(String)  # T-24h, T-1h, HT-2min
    kickoff_time = Column(DateTime)

    # Model info
    model_name = Column(String)
    model_version = Column(String)

    # Predictions
    pred_home = Column(Float)
    pred_draw = Column(Float)
    pred_away = Column(Float)
    pred_xg_home = Column(Float)
    pred_xg_away = Column(Float)

    # Market at prediction time
    market_odds_home = Column(Float)
    market_odds_draw = Column(Float)
    market_odds_away = Column(Float)

    # Computed edge
    edge_home = Column(Float)
    edge_draw = Column(Float)
    edge_away = Column(Float)

    # Confidence
    model_confidence = Column(Float)
    learnability_score = Column(Float)

    # Actuals (filled post-match)
    actual_result = Column(String)  # home, draw, away
    actual_goals_home = Column(Integer)
    actual_goals_away = Column(Integer)
    closing_odds_home = Column(Float)
    closing_odds_draw = Column(Float)
    closing_odds_away = Column(Float)

    # CLV tracking
    clv_home = Column(Float)
    clv_draw = Column(Float)
    clv_away = Column(Float)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("ix_pred_fixture_time", "fixture_id", "prediction_time"),)


class Signal(Base):
    """Generated trading signals"""

    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fixture_id = Column(Integer, nullable=False, index=True)

    # Signal timing
    generated_at = Column(DateTime, default=datetime.utcnow)
    valid_until = Column(DateTime)  # Signal expires at kickoff
    signal_horizon = Column(String)  # T-24h, T-1h, HT-2min

    # Match info
    home_team = Column(String)
    away_team = Column(String)
    league_id = Column(Integer)
    kickoff_time = Column(DateTime)

    # Signal details
    market = Column(String, nullable=False)  # home, draw, away, over_2.5, ah_-0.5
    direction = Column(String)  # back, lay

    # Predictions
    model_prob = Column(Float)
    market_prob = Column(Float)
    edge = Column(Float)

    # Recommendations
    recommended_odds = Column(Float)
    recommended_stake = Column(Float)
    stake_pct = Column(Float)
    kelly_fraction = Column(Float)

    # Confidence
    confidence = Column(Float)
    learnability_score = Column(Float)

    # Best execution
    best_bookmaker = Column(String)
    best_odds = Column(Float)

    # Status
    status = Column(String, default="pending")  # pending, executed, expired, cancelled
    executed_at = Column(DateTime)
    execution_odds = Column(Float)

    # Metadata
    model_version = Column(String)

    __table_args__ = (Index("ix_signal_fixture_market", "fixture_id", "market"),)


class DailyPnL(Base):
    """Daily P&L tracking"""

    __tablename__ = "daily_pnl"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Date
    date = Column(DateTime, nullable=False, unique=True, index=True)

    # Volume
    total_bets = Column(Integer)
    total_staked = Column(Float)

    # Results
    wins = Column(Integer)
    losses = Column(Integer)
    pushes = Column(Integer)
    win_rate = Column(Float)

    # P&L
    gross_pnl = Column(Float)
    commission = Column(Float)
    net_pnl = Column(Float)
    roi = Column(Float)

    # CLV
    avg_clv = Column(Float)
    clv_positive_rate = Column(Float)

    # By market
    pnl_1x2 = Column(Float)
    pnl_ou = Column(Float)
    pnl_ah = Column(Float)
    pnl_ht = Column(Float)

    # By model
    pnl_pregame = Column(Float)
    pnl_halftime = Column(Float)

    # Bankroll
    starting_bankroll = Column(Float)
    ending_bankroll = Column(Float)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)


class EnsemblePrediction(Base):
    """Store ensemble predictions with component weights"""

    __tablename__ = "ensemble_predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fixture_id = Column(Integer, nullable=False, index=True)
    prediction_horizon = Column(String)  # T-24h, T-1h, HT-2min

    # Component predictions
    pred_clv_model = Column(Float)
    pred_xg_model = Column(Float)
    pred_poisson_model = Column(Float)
    pred_market_model = Column(Float)

    # Weights used
    weight_clv = Column(Float)
    weight_xg = Column(Float)
    weight_poisson = Column(Float)
    weight_market = Column(Float)

    # Ensemble output
    ensemble_prediction = Column(Float)

    # Disagreement
    disagreement_std = Column(Float)
    max_difference = Column(Float)
    high_disagreement = Column(Boolean)
    confidence_modifier = Column(Float)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)


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


class FeatureVectorTeamExplicit(Base):
    """Explicit feature vector table: feature_vector_team_explicit"""

    __tablename__ = "feature_vector_team_explicit"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fixture_id = Column(Integer, nullable=False, index=True)
    feature_horizon = Column(String, nullable=False)  # T-24h, T-1h, HT-2min, etc.
    timestamp_utc = Column(DateTime, nullable=False, index=True)  # as_of_utc

    away_aerial_dominance = Column(Float)
    away_attack_directness = Column(Float)
    away_attack_value_missing = Column(Float)
    away_attack_variance = Column(Float)
    away_attack_width = Column(Float)
    away_big_chance_pct = Column(Float)
    away_cards_under_referee = Column(Float)
    away_cards_vs_ref_avg = Column(Float)
    away_congestion_score = Column(Float)
    away_counter_attack_ratio = Column(Float)
    away_cross_reliance = Column(Float)
    away_dangerous_attacks_avg = Column(Float)
    away_days_rest = Column(Float)
    away_days_since_manager_change = Column(Float)
    away_def_avg_height_cm = Column(Float)
    away_def_line_rating = Column(Float)
    away_def_line_value = Column(Float)
    away_def_quality_drop = Column(Float)
    away_defense_variance = Column(Float)
    away_defensive_block_height = Column(Float)
    away_elo = Column(Float)
    away_form_points = Column(Float)
    away_form_string = Column(String)
    away_form_trend = Column(Float)
    away_formation = Column(Float)
    away_foul_propensity = Column(Float)
    away_fwd_line_rating = Column(Float)
    away_fwd_line_value = Column(Float)
    away_fwd_quality_drop = Column(Float)
    away_fwd_xg_per90 = Column(Float)
    away_game_control = Column(Float)
    away_games_last_14d = Column(Float)
    away_games_last_21d = Column(Float)
    away_games_under_manager = Column(Float)
    away_gk_rating = Column(Float)
    away_goals_conceded_avg = Column(Float)
    away_goals_conceded_last1 = Column(Float)
    away_goals_conceded_last3 = Column(Float)
    away_goals_conceded_last5 = Column(Float)
    away_goals_conceded_season = Column(Float)
    away_goals_ewma_30d = Column(Float)
    away_goals_last1 = Column(Float)
    away_goals_last3 = Column(Float)
    away_goals_last5 = Column(Float)
    away_goals_momentum = Column(Float)
    away_goals_season = Column(Float)
    away_goals_std_last10 = Column(Float)
    away_goals_vs_league = Column(Float)
    away_interception_rate = Column(Float)
    away_key_absentees_count = Column(Integer)
    away_key_players_missing = Column(Float)
    away_last_travel_km = Column(Float)
    away_manager_attack_style = Column(Float)
    away_manager_avg_possession = Column(Float)
    away_manager_avg_ppda = Column(Float)
    away_manager_clean_sheet_rate = Column(Float)
    away_manager_defensive_style = Column(Float)
    away_manager_goals_per_game = Column(Float)
    away_manager_honeymoon = Column(Float)
    away_manager_ppg_last5 = Column(Float)
    away_manager_set_piece_focus = Column(Float)
    away_manager_tier = Column(Integer)
    away_manager_win_rate = Column(Float)
    away_manager_xg_diff_last5 = Column(Float)
    away_match_tempo = Column(Float)
    away_mid_line_rating = Column(Float)
    away_mid_line_value = Column(Float)
    away_midweek_european = Column(Float)
    away_new_manager_flag = Column(Integer)
    away_pass_tempo = Column(Float)
    away_pen_box_entries = Column(Float)
    away_pen_won_rate = Column(Float)
    away_played_continental_last_week = Column(Float)
    away_possession_ewma_30d = Column(Float)
    away_possession_last1 = Column(Float)
    away_possession_last3 = Column(Float)
    away_possession_last5 = Column(Float)
    away_possession_season = Column(Float)
    away_possession_style = Column(Float)
    away_possession_trend = Column(Float)
    away_ppda_style = Column(Float)
    away_ppg_last3 = Column(Float)
    away_ppg_last5 = Column(Float)
    away_ppg_season = Column(Float)
    away_predictability = Column(Float)
    away_prev_goals_conceded = Column(Float)
    away_prev_goals_scored = Column(Float)
    away_prev_opponent_strength = Column(Float)
    away_prev_result = Column(Float)
    away_prev_was_home = Column(Float)
    away_prev_xg = Column(Float)
    away_red_risk_with_ref = Column(Float)
    away_response_when_ahead = Column(Float)
    away_response_when_behind = Column(Float)
    away_set_piece_reliance = Column(Float)
    away_short_rest = Column(Float)
    away_shot_volume_style = Column(Float)
    away_shots_accuracy_avg = Column(Float)
    away_shots_blocked_pct = Column(Float)
    away_shots_conceded_last5 = Column(Float)
    away_shots_conceded_season = Column(Float)
    away_shots_last1 = Column(Float)
    away_shots_last3 = Column(Float)
    away_shots_last5 = Column(Float)
    away_shots_season = Column(Float)
    away_sot_pct_last5 = Column(Float)
    away_sot_pct_season = Column(Float)
    away_squad_avg_value = Column(Float)
    away_squad_total_value = Column(Float)
    away_tackle_aggression = Column(Float)
    away_team_id = Column(Float)
    away_top_assister_in_xi = Column(Float)
    away_top_scorer_in_xi = Column(Float)
    away_top_xg_player_in_xi = Column(Float)
    away_total_travel_14d = Column(Float)
    away_transition_speed = Column(Float)
    away_travel_band = Column(String)
    away_travel_km = Column(Float)
    away_value_lost_to_injury = Column(Float)
    away_xg_avg = Column(Float)
    away_xg_ewma_30d = Column(Float)
    away_xg_ewma_90d = Column(Float)
    away_xg_last1 = Column(Float)
    away_xg_last3 = Column(Float)
    away_xg_last5 = Column(Float)
    away_xg_momentum = Column(Float)
    away_xg_per_shot = Column(Float)
    away_xg_season = Column(Float)
    away_xga_last1 = Column(Float)
    away_xga_last3 = Column(Float)
    away_xga_last5 = Column(Float)
    away_xga_season = Column(Float)
    congestion_diff = Column(Float)
    congestion_score = Column(Float)
    days_since_manager_change = Column(Float)
    days_since_season_start = Column(Float)
    division_tier = Column(Integer)
    games_last_14d = Column(Float)
    games_last_21d = Column(Float)
    games_played_season = Column(Float)
    games_played_season_away = Column(Float)
    games_played_season_home = Column(Float)
    games_since_season_start = Column(Float)
    games_under_manager = Column(Float)
    home_aerial_dominance = Column(Float)
    home_attack_directness = Column(Float)
    home_attack_value_missing = Column(Float)
    home_attack_variance = Column(Float)
    home_attack_width = Column(Float)
    home_big_chance_pct = Column(Float)
    home_cards_under_referee = Column(Float)
    home_cards_vs_ref_avg = Column(Float)
    home_congestion_score = Column(Float)
    home_counter_attack_ratio = Column(Float)
    home_cross_reliance = Column(Float)
    home_dangerous_attacks_avg = Column(Float)
    home_days_rest = Column(Float)
    home_days_since_manager_change = Column(Float)
    home_def_avg_height_cm = Column(Float)
    home_def_line_rating = Column(Float)
    home_def_line_value = Column(Float)
    home_def_quality_drop = Column(Float)
    home_defense_variance = Column(Float)
    home_defensive_block_height = Column(Float)
    home_elo = Column(Float)
    home_form_points = Column(Float)
    home_form_string = Column(String)
    home_form_trend = Column(Float)
    home_formation = Column(Float)
    home_foul_propensity = Column(Float)
    home_fwd_line_rating = Column(Float)
    home_fwd_line_value = Column(Float)
    home_fwd_quality_drop = Column(Float)
    home_fwd_xg_per90 = Column(Float)
    home_game_control = Column(Float)
    home_games_last_14d = Column(Float)
    home_games_last_21d = Column(Float)
    home_games_under_manager = Column(Float)
    home_gk_rating = Column(Float)
    home_goals_conceded_avg = Column(Float)
    home_goals_conceded_last1 = Column(Float)
    home_goals_conceded_last3 = Column(Float)
    home_goals_conceded_last5 = Column(Float)
    home_goals_conceded_season = Column(Float)
    home_goals_ewma_30d = Column(Float)
    home_goals_last1 = Column(Float)
    home_goals_last3 = Column(Float)
    home_goals_last5 = Column(Float)
    home_goals_momentum = Column(Float)
    home_goals_season = Column(Float)
    home_goals_std_last10 = Column(Float)
    home_goals_vs_league = Column(Float)
    home_interception_rate = Column(Float)
    home_key_absentees_count = Column(Integer)
    home_key_players_missing = Column(Float)
    home_last_travel_km = Column(Float)
    home_manager_attack_style = Column(Float)
    home_manager_avg_possession = Column(Float)
    home_manager_avg_ppda = Column(Float)
    home_manager_clean_sheet_rate = Column(Float)
    home_manager_defensive_style = Column(Float)
    home_manager_goals_per_game = Column(Float)
    home_manager_honeymoon = Column(Float)
    home_manager_ppg_last5 = Column(Float)
    home_manager_set_piece_focus = Column(Float)
    home_manager_tier = Column(Integer)
    home_manager_win_rate = Column(Float)
    home_manager_xg_diff_last5 = Column(Float)
    home_match_tempo = Column(Float)
    home_mid_line_rating = Column(Float)
    home_mid_line_value = Column(Float)
    home_midweek_european = Column(Float)
    home_new_manager_flag = Column(Integer)
    home_pass_tempo = Column(Float)
    home_pen_box_entries = Column(Float)
    home_pen_won_rate = Column(Float)
    home_played_continental_last_week = Column(Float)
    home_possession_ewma_30d = Column(Float)
    home_possession_last1 = Column(Float)
    home_possession_last3 = Column(Float)
    home_possession_last5 = Column(Float)
    home_possession_season = Column(Float)
    home_possession_style = Column(Float)
    home_possession_trend = Column(Float)
    home_ppda_style = Column(Float)
    home_ppg_last3 = Column(Float)
    home_ppg_last5 = Column(Float)
    home_ppg_season = Column(Float)
    home_predictability = Column(Float)
    home_prev_goals_conceded = Column(Float)
    home_prev_goals_scored = Column(Float)
    home_prev_opponent_strength = Column(Float)
    home_prev_result = Column(Float)
    home_prev_was_home = Column(Float)
    home_prev_xg = Column(Float)
    home_red_risk_with_ref = Column(Float)
    home_response_when_ahead = Column(Float)
    home_response_when_behind = Column(Float)
    home_set_piece_reliance = Column(Float)
    home_short_rest = Column(Float)
    home_shot_volume_style = Column(Float)
    home_shots_accuracy_avg = Column(Float)
    home_shots_blocked_pct = Column(Float)
    home_shots_conceded_last5 = Column(Float)
    home_shots_conceded_season = Column(Float)
    home_shots_last1 = Column(Float)
    home_shots_last3 = Column(Float)
    home_shots_last5 = Column(Float)
    home_shots_season = Column(Float)
    home_sot_pct_last5 = Column(Float)
    home_sot_pct_season = Column(Float)
    home_squad_avg_value = Column(Float)
    home_squad_total_value = Column(Float)
    home_tackle_aggression = Column(Float)
    home_team_id = Column(Float)
    home_top_assister_in_xi = Column(Float)
    home_top_scorer_in_xi = Column(Float)
    home_top_xg_player_in_xi = Column(Float)
    home_total_travel_14d = Column(Float)
    home_transition_speed = Column(Float)
    home_value_lost_to_injury = Column(Float)
    home_xg_avg = Column(Float)
    home_xg_ewma_30d = Column(Float)
    home_xg_ewma_90d = Column(Float)
    home_xg_last1 = Column(Float)
    home_xg_last3 = Column(Float)
    home_xg_last5 = Column(Float)
    home_xg_momentum = Column(Float)
    home_xg_per_shot = Column(Float)
    home_xg_season = Column(Float)
    home_xga_last1 = Column(Float)
    home_xga_last3 = Column(Float)
    home_xga_last5 = Column(Float)
    home_xga_season = Column(Float)
    is_early_season = Column(Integer)
    is_first_3_games = Column(Integer)
    lambda_away_bayesian = Column(Float)
    lambda_away_lower_95 = Column(Float)
    lambda_away_market_implied = Column(Float)
    lambda_away_poisson = Column(Float)
    lambda_away_upper_95 = Column(Float)
    lambda_blend_away = Column(Float)
    lambda_blend_home = Column(Float)
    lambda_diff_poisson = Column(Float)
    lambda_home_bayesian = Column(Float)
    lambda_home_lower_95 = Column(Float)
    lambda_home_market_implied = Column(Float)
    lambda_home_poisson = Column(Float)
    lambda_home_upper_95 = Column(Float)
    lambda_total_poisson = Column(Float)
    lambda_uncertainty_away = Column(Float)
    lambda_uncertainty_home = Column(Float)
    manager_attack_style = Column(Float)
    manager_avg_possession = Column(Float)
    manager_avg_ppda = Column(Float)
    manager_away_id = Column(Float)
    manager_clean_sheet_rate = Column(Float)
    manager_defensive_style = Column(Float)
    manager_experience_diff = Column(Float)
    manager_goals_per_game = Column(Float)
    manager_h2h_home_wins = Column(Integer)
    manager_h2h_matches = Column(Float)
    manager_home_id = Column(Float)
    manager_honeymoon = Column(Float)
    manager_ppg_last5 = Column(Float)
    manager_set_piece_focus = Column(Float)
    manager_trophy_diff = Column(Float)
    manager_win_rate = Column(Float)
    manager_xg_diff_last5 = Column(Float)
    new_manager_flag = Column(Integer)
    new_manager_flag_away = Column(Float)
    new_manager_flag_home = Column(Float)
    p_poisson_away = Column(Float)
    p_poisson_draw = Column(Float)
    p_poisson_home = Column(Float)
    prior_attack_adjustment = Column(Float)
    prior_decay_factor = Column(Float)
    prior_defense_adjustment = Column(Float)
    prior_goals_against = Column(Float)
    prior_goals_for = Column(Float)
    prior_manager_attack_style = Column(Float)
    prior_manager_defense_style = Column(Float)
    prior_manager_possession = Column(Float)
    prior_possession = Column(Float)
    prior_preseaon_form = Column(Float)
    prior_preseaon_xg_against = Column(Float)
    prior_preseaon_xg_for = Column(Float)
    prior_reliability = Column(Float)
    prior_shots_against = Column(Float)
    prior_shots_for = Column(Float)
    prior_squad_stability = Column(Float)
    prior_squad_value_ratio = Column(Float)
    prior_weight_away = Column(Float)
    prior_weight_home = Column(Float)
    prior_xg_attack = Column(Float)
    prior_xg_defense = Column(Float)
    season_progress_pct = Column(Float)
    squad_turnover_rate = Column(Float)
    style_clash_score = Column(Float)
    style_embedding_available = Column(Integer)
    style_pc1 = Column(Float)
    style_pc2 = Column(Float)
    style_pc3 = Column(Float)
    style_similarity = Column(Float)
    team_a_xg_prematch = Column(Float)
    team_b_xg_prematch = Column(Float)
    travel_fatigue_away = Column(Float)
    travel_fatigue_home = Column(Float)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint(
            "fixture_id",
            "feature_horizon",
            "timestamp_utc",
            name="uq_feature_vector_team_explicit_fixture_horizon_ts",
        ),
        Index(
            "ix_feature_vector_team_explicit_fixture_horizon_ts",
            "fixture_id",
            "feature_horizon",
            "timestamp_utc",
        ),
    )


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
# HELPER FUNCTIONS
# =============================================================================


def create_all_tables(engine):
    """Create all database tables"""
    Base.metadata.create_all(engine)


def drop_all_tables(engine):
    """Drop all database tables"""
    Base.metadata.drop_all(engine)


# Uncomment to create tables on module load
# from database import engine
# create_all_tables(engine)
