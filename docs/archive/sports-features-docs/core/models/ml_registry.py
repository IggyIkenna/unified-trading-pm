from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)

from .base import Base

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
