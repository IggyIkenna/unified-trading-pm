from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    UniqueConstraint,
)

from .base import Base

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

    __table_args__ = (UniqueConstraint("league_id", "season", name="uix_league_season"),)


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

    __table_args__ = (UniqueConstraint("fixture_id", "team_id", name="uix_fixture_team_stats"),)


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
