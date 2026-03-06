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
- Transfermarkt: TransfermarktPlayer, TransfermarktInjury,
  TransfermarktTransfer, TransfermarktManager, TransfermarktSquad
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

from sqlalchemy.orm import DeclarativeBase

# Note: Import engine from your database module
# from database import engine


class Base(DeclarativeBase):
    pass


# =============================================================================
# CORE TABLES (API-Football)
# =============================================================================
