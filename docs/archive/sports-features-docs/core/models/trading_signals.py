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
