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
)

from .base import Base

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
    alert_type = Column(String, nullable=False)  # feature_drift, prediction_drift, calibration_drift, clv_profit_drift
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
    recommended_action = Column(String)  # investigate, retrain, recalibrate, halt_betting
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
