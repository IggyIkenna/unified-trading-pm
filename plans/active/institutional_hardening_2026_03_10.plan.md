---
id: institutional_hardening_2026_03_10
title: Institutional Hardening — Stress Market Resilience, Research Integrity, Maintainability
status: active
priority: P0
created: 2026-03-10
owner: agent
---

## Overview

Citadel-standard audit of the unified trading system identified 3 P0 systemic failures and 8 high-priority WARNs that
cause real P&L damage in stress markets. This plan covers all findings end-to-end: implementation, tests, and
validation.

**Not in scope:** HFT-specific concerns (co-location, tick-to-trade latency, FPGA execution).

**Repos affected:** `execution-service`, `risk-and-exposure-service`, `unified-internal-contracts`,
`unified-trading-library`, `ml-training-api`, `ml-inference-api`, `strategy-service`, `features-delta-one-service`,
`features-multi-timeframe-service`, `features-sports-service`, `market-data-processing-service`

---

## Stream A — Float → Decimal Migration (P0)

**Root cause:** `quantity: float` and `price: float` throughout the OMS, pre-trade risk engine, and position tracker.
IEEE 754 floating-point accumulation errors drift position state over many partial fills. Pre-trade risk checks enforce
a limit of `100.0` units but the float-accumulated position reads `99.9999999998` — the limit is silently breached.

### A1 — OMS Order Creation Fields

**File:** `execution-service/execution_service/orders/oms.py:44–49`

Current:

```python
quantity: float,
price: float,
```

Required change:

```python
from decimal import Decimal
quantity: Decimal,
price: Decimal,
```

- Update `create_order()` signature to accept `Decimal` for `quantity` and `price`
- Update `order_data` dict construction — both fields must remain `Decimal` when persisted
- Update all callers in `execution_service/api/` and `execution_service/engine/` that construct order dicts
- Update `OrderPersistenceAdapter` protocol to accept `Decimal` (serialise to string in DB layer, not float)
- Add `@validator` (Pydantic v2: `model_validator(mode='before')`) that rejects raw `float` input with a clear error

**Tests required:**

- `test_oms_rejects_float_price` — assert `TypeError` or `ValidationError` when `price=1.23` (float) passed
- `test_oms_accepts_decimal_price` — golden path with `price=Decimal("1.23")`
- `test_oms_position_accumulation_exact` — simulate 100 partial fills of `Decimal("0.1")` each, assert total =
  `Decimal("10.0")` exactly (would fail with float)

### A2 — Pre-Trade Risk Engine Position Arithmetic

**File:** `execution-service/execution_service/engine/live/risk.py:35–36, 54–64`

Current:

```python
quantity: float,
price: float,
...
current = (pos or {}).get("aggregated_quantity", 0.0)
add = quantity if side.upper() == "BUY" else -quantity
new_pos = current + add
```

Required change:

```python
from decimal import Decimal
quantity: Decimal,
price: Decimal,
...
current = Decimal((pos or {}).get("aggregated_quantity", "0"))
add = quantity if side.upper() == "BUY" else -quantity
new_pos = current + add
```

- `aggregated_quantity` stored in position tracker must be `Decimal`-serialised (string in Redis/Firestore, not float)
- `max_pos` loaded from config must be coerced to `Decimal` via `Decimal(str(raw_limit))` — never `Decimal(float)`
- `abs(new_pos) > max_pos` comparison: both sides `Decimal`

**Tests required:**

- `test_risk_position_limit_exact_decimal` — 50 BUY fills of `Decimal("2.0")` → position = `Decimal("100.0")`, next BUY
  of `Decimal("0.001")` → rejected at limit `Decimal("100.0")`
- `test_risk_float_coercion_rejected` — passing `quantity=2.0` (float) raises `TypeError`
- `test_risk_sell_position_crosses_short_limit` — short-side limit enforcement mirrors long-side

### A3 — Order Recovery Engine ExchangeOrder / InternalOrder Fields

**File:** `execution-service/execution_service/engine/startup/order_recovery.py:62–78`

Current:

```python
quantity: float
filled_quantity: float
```

Required change: `Decimal` for both fields. Update `apply_fill()` arithmetic accordingly.

**Tests required:**

- `test_recovery_fill_arithmetic_decimal` — fill of `Decimal("0.333333333333333333")` applied exactly, no rounding drift

### A4 — Unified Internal Contracts: Feature Price Fields

**File:** `unified-internal-contracts/unified_internal_contracts/features.py:116–135`

Current state: `spot_price: Decimal`, `front_month_price: Decimal | None` (correct), but derived fields `basis: float`,
`basis_pct: float`, `annualized_basis: float`, `price_ratio: float` (wrong).

Required change:

```python
basis: Decimal | None
basis_pct: Decimal | None
annualized_basis: Decimal | None
price_ratio: Decimal | None
```

Rationale: `basis = spot_price - front_month_price` — both inputs are `Decimal`, the output must be too. Casting to
float at the derivation step loses precision that was paid for in the source fields. ML features downstream receive a
float approximation of a Decimal basis — corrupting the signal.

Also update lines 122–240: all `float` fields that represent prices or price-derived ratios must become `Decimal`.
Fields that are dimensionless statistical measures (RSI, z-scores, normalised returns) may remain `float`.

**Test required:**

- `test_futures_basis_decimal_precision` — compute `basis` from two large Decimal prices, assert no precision loss vs
  manual Decimal arithmetic

### A5 — Parquet Schema: Price Columns to Fixed-Point int64

**File:** `unified-trading-library` — Parquet schema definitions

Current: `ColumnSchema(name="price", dtype="float64")` throughout.

Institutional standard: prices stored as `int64` with a fixed-point exponent (e.g., `price_raw: int64`,
`price_exponent: int8 = -8` meaning multiply by `10^-8` to get real price). This is how Bloomberg, Refinitiv, and all
exchange binary protocols encode prices.

Required:

- Add `PriceColumn` schema type: `raw: int64`, `exponent: int8`
- Or: store as `string` (`Decimal.__str__()`) in parquet if downstream consumers are Python-only
- Add migration utility: `float64_price_to_decimal_string(col: pa.Array) -> pa.Array`
- Document the encoding decision in `unified-trading-codex/06-coding-standards/`

**Test required:**

- Round-trip test: `Decimal("12345.678901234567")` → parquet → back → exactly equal (fails with float64)

---

## Stream B — VaR Model Hardening (P0)

**Root cause:** `parametric_var()` in
`risk-and-exposure-service/risk_and_exposure_service/core/var_calculator.py:80–100` uses `statistics.mean()` +
`statistics.stdev()` and assumes normally distributed returns. This systematically understates VaR in every fat-tail
market regime — exactly the markets where you need accurate VaR most.

### B1 — Add Cornish-Fisher Adjusted Parametric VaR

**File:** `risk-and-exposure-service/risk_and_exposure_service/core/var_calculator.py`

Add new function `parametric_var_cornish_fisher()`:

```python
import math
import statistics

def parametric_var_cornish_fisher(
    returns: list[float],
    confidence: float = 0.99,
    horizon_days: int = 1,
) -> float:
    """
    Cornish-Fisher adjusted parametric VaR.

    Accounts for observed skewness and excess kurtosis in the return
    distribution. More accurate than plain parametric VaR for fat-tailed
    assets (crypto, small-cap equity, illiquid fixed income).

    Reference: Cornish & Fisher (1937). Used by JP Morgan RiskMetrics,
    Basel III internal model guidance.
    """
    _validate_inputs(returns, confidence, horizon_days)
    if len(returns) < 30:
        raise InsufficientDataError(
            f"Cornish-Fisher requires >= 30 observations; got {len(returns)}. "
            "Use historical_var() for short return series."
        )
    mu = statistics.mean(returns)
    sigma = statistics.stdev(returns)
    n = len(returns)
    skew = _sample_skewness(returns, mu, sigma)
    kurt = _sample_excess_kurtosis(returns, mu, sigma)

    # Standard normal quantile for tail_prob
    tail_prob = max(1e-15, min(1.0 - confidence, 1.0 - 1e-15))
    z = math.sqrt(2.0) * _erfinv(2.0 * tail_prob - 1.0)

    # Cornish-Fisher expansion
    z_cf = (
        z
        + (z**2 - 1.0) * skew / 6.0
        + (z**3 - 3.0 * z) * kurt / 24.0
        - (2.0 * z**3 - 5.0 * z) * skew**2 / 36.0
    )

    var_1d = mu + z_cf * sigma
    var_1d = min(var_1d, 0.0)
    return _horizon_scale(var_1d, horizon_days)
```

Add private helpers `_sample_skewness()` and `_sample_excess_kurtosis()` using stdlib only (no scipy dependency). Both
use the unbiased n-1 denominator.

### B2 — Minimum Observation Guard

**File:** `risk_and_exposure_service/core/var_calculator.py:_validate_inputs()`

Current minimum: 2 observations. This is mathematically sufficient for `statistics.stdev()` but statistically
meaningless and operationally dangerous.

Required:

```python
MIN_OBSERVATIONS_PARAMETRIC = 30
MIN_OBSERVATIONS_HISTORICAL = 10
MIN_OBSERVATIONS_CORNISH_FISHER = 30

class InsufficientDataError(ValueError):
    """Raised when return series has too few observations for the requested VaR method."""
```

- `parametric_var()` → raises `InsufficientDataError` if `len(returns) < MIN_OBSERVATIONS_PARAMETRIC`
- `historical_var()` → raises `InsufficientDataError` if `len(returns) < MIN_OBSERVATIONS_HISTORICAL`
- Caller in the risk engine must handle `InsufficientDataError` by publishing `RISK_INSUFFICIENT_DATA` event and using
  the last known VaR or a conservative fallback, not by silently crashing

### B3 — Regime-Adaptive Stress Multipliers

**File:** `risk_and_exposure_service/core/var_calculator.py:_STRESS_MULTIPLIERS`

Current: hardcoded dict of 3 historical scenarios. This does not adapt to new regime types.

Required:

- Move `_STRESS_MULTIPLIERS` to `UnifiedCloudConfig` (configurable at runtime without deploy)
- Add `current_regime_multiplier()` function: reads a `CURRENT_REGIME_STRESS_FACTOR` config key (default `1.0`) that
  risk managers can set via the admin API to amplify all VaR figures during known stress periods
- Add `REGIME_STRESS_FACTOR_CHANGED` event when the multiplier changes

**Tests required (B1–B3):**

- `test_cornish_fisher_fat_tails` — return series with known skew=-1.5, kurt=3.0; assert CF-VaR > parametric-VaR
- `test_cornish_fisher_symmetric` — with skew=0, kurt=0; assert CF-VaR ≈ parametric-VaR (within 0.001)
- `test_insufficient_data_parametric` — 5 observations → `InsufficientDataError`
- `test_insufficient_data_historical` — 3 observations → `InsufficientDataError`
- `test_stress_multiplier_from_config` — mock `UnifiedCloudConfig` returning `2.5`, assert VaR × 2.5
- `test_regime_factor_event_emitted` — assert `REGIME_STRESS_FACTOR_CHANGED` event logged on update

---

## Stream C — Point-in-Time Enforcement & Lookahead Bias Prevention (P0)

**Root cause:** No systematic enforcement that features only use data available at the time of prediction. Silent
lookahead bias inflates research alpha. Three categories:

1. Feature computation uses future reference data
2. ML train/test split happens after normalization
3. No enforced `as_of_date` parameter on feature queries

### C1 — PointInTimeEnforcer Class

**New file:** `unified-trading-library/src/unified_trading_library/point_in_time.py`

```python
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal


class PointInTimeViolation(ValueError):
    """Raised when a feature record contains data from after the prediction timestamp."""


@dataclass(frozen=True)
class FeatureTimestamps:
    data_timestamp: datetime    # When the bar/tick data was observed
    timestamp_out: datetime     # When the feature becomes available for prediction


def enforce_point_in_time(
    data_timestamp: datetime,
    timestamp_out: datetime,
    label_timestamp: datetime | None = None,
) -> None:
    """
    Enforce that:
    1. timestamp_out > data_timestamp (feature is not available before data exists)
    2. label_timestamp > timestamp_out (label uses data strictly after feature was available)

    Raises PointInTimeViolation with full context if any constraint is violated.
    """
    if timestamp_out <= data_timestamp:
        raise PointInTimeViolation(
            f"timestamp_out={timestamp_out} must be strictly after "
            f"data_timestamp={data_timestamp}. Lookahead bias detected."
        )
    if label_timestamp is not None and label_timestamp <= timestamp_out:
        raise PointInTimeViolation(
            f"label_timestamp={label_timestamp} must be strictly after "
            f"timestamp_out={timestamp_out}. Label leaks into feature window."
        )


def validate_feature_dataframe(df: "pl.DataFrame | pd.DataFrame") -> None:
    """
    Validate all rows of a feature DataFrame for point-in-time correctness.
    Expects columns: 'timestamp', 'timestamp_out'.
    Optionally: 'label_timestamp' for training datasets.
    Raises PointInTimeViolation on first violation found.
    """
```

Export from `unified_trading_library/__init__.py`.

**Tests required:**

- `test_pit_valid_timestamps` — `timestamp_out` = `data_timestamp` + 500ms → no exception
- `test_pit_violation_same_timestamp` — `timestamp_out` == `data_timestamp` → `PointInTimeViolation`
- `test_pit_violation_future_data` — `timestamp_out` < `data_timestamp` → `PointInTimeViolation`
- `test_pit_label_violation` — label at T+1h, feature available at T+2h → `PointInTimeViolation`
- `test_pit_dataframe_validation` — 1000-row polars DataFrame, inject 1 violation at row 500, assert caught

### C2 — Feature Services: Enforce PIT at Output

**Files:** All 8 features repos — each `orchestration_service.py` or equivalent output path.

In `features-delta-one-service` this is already partially present (synthetic delay of 500ms in
`test_lookahead_bias.py`). Make it a **hard enforcement** not just a test:

In `features_delta_one_service/app/core/orchestration_service.py` (and equivalents):

```python
from unified_trading_library.point_in_time import enforce_point_in_time, PointInTimeViolation

# After computing each feature batch, before writing to storage:
for row in feature_batch:
    try:
        enforce_point_in_time(
            data_timestamp=row.timestamp,
            timestamp_out=row.timestamp_out,
        )
    except PointInTimeViolation as e:
        log_event(LOOKAHEAD_BIAS_VIOLATION, severity="CRITICAL", details={"error": str(e), "row": row})
        raise  # Never silently emit biased features
```

Apply to:

- `features-delta-one-service`
- `features-multi-timeframe-service`
- `features-sports-service`
- `features-options-service` (if present)
- `market-data-processing-service` candle output path

### C3 — ML Training Pipeline: Train/Test Split Before Normalization

**File:** `ml-training-api/` — locate the training pipeline entry point and any normalization/scaling steps.

Required pattern (enforce in code review checklist and add validation):

```python
# CORRECT: split first, normalize after
split_date = config.train_cutoff_date  # from UnifiedCloudConfig — NOT hardcoded
train_df = features[features["date"] < split_date].copy()
test_df  = features[features["date"] >= split_date].copy()

scaler = StandardScaler()
train_df[feature_cols] = scaler.fit_transform(train_df[feature_cols])
test_df[feature_cols]  = scaler.transform(test_df[feature_cols])   # transform only, never fit_transform
```

Add `TrainTestSplitValidator` class:

```python
class TrainTestSplitValidator:
    """Validates that no information from the test set leaked into scaler fitting."""

    def validate(
        self,
        scaler: StandardScaler,
        train_df: pd.DataFrame,
        test_df: pd.DataFrame,
        feature_cols: list[str],
    ) -> None:
        """Assert that scaler mean/var matches train-only statistics."""
        for i, col in enumerate(feature_cols):
            expected_mean = train_df[col].mean()
            if abs(scaler.mean_[i] - expected_mean) > 1e-6:
                raise TrainTestContaminationError(
                    f"Scaler mean for '{col}' ({scaler.mean_[i]:.6f}) does not match "
                    f"train-only mean ({expected_mean:.6f}). Scaler was fit on full dataset."
                )
```

**Tests required:**

- `test_split_before_normalize_correct` — split → fit train only → transform test → assert test scaler params not seen
  in fit
- `test_contamination_detected` — deliberately fit on full dataset, `TrainTestSplitValidator.validate()` →
  `TrainTestContaminationError`
- `test_train_cutoff_from_config` — assert `split_date` reads from `UnifiedCloudConfig`, not hardcoded

### C4 — Walk-Forward Validation Infrastructure

**New file:** `unified-trading-library/src/unified_trading_library/walk_forward.py`

```python
from dataclasses import dataclass
from datetime import date, timedelta


@dataclass
class WalkForwardFold:
    fold_id: int
    train_start: date
    train_end: date
    test_start: date
    test_end: date


def generate_walk_forward_folds(
    data_start: date,
    data_end: date,
    train_window_days: int,
    test_window_days: int,
    step_days: int | None = None,
) -> list[WalkForwardFold]:
    """
    Generate rolling walk-forward folds. No overlap between test windows.

    Args:
        data_start: First available data date
        data_end: Last available data date (exclusive)
        train_window_days: Training window length in calendar days
        test_window_days: Test window length in calendar days
        step_days: How far to advance each fold. Defaults to test_window_days (non-overlapping)

    Returns:
        List of WalkForwardFold with strict temporal ordering.
    """
```

Add `WalkForwardEvaluator` that:

- Takes a model factory, feature source, and label source
- Iterates folds, fitting on train, predicting on test
- Returns per-fold metrics (Sharpe, hit rate, avg return, max drawdown)
- Asserts no future data contamination by calling `PointInTimeEnforcer` on each fold

**Tests required:**

- `test_walk_forward_no_overlap` — assert no test date appears in any train window
- `test_walk_forward_ordering` — assert `fold_n.test_end < fold_n+1.train_start` for all n
- `test_walk_forward_minimum_train_size` — assert each fold has at least 252 trading days of training data

### C5 — Strategy Service: Backtest Point-in-Time Guard

**File:** `strategy-service/` — locate backtest configuration and signal generation.

Add validation hook: before any signal or label is generated in backtest mode, assert:

```python
if mode == ExecutionMode.BACKTEST:
    PointInTimeEnforcer.assert_no_future_reference_data(
        as_of_date=current_bar_date,
        reference_data_snapshot_date=instrument.metadata_as_of_date,
    )
```

This prevents reference data (instrument classification, sector, market cap tier) from using the current database state
rather than the state at `as_of_date`.

### C6 — Transaction Cost Sensitivity Analysis

**New file:** `unified-trading-library/src/unified_trading_library/tc_sensitivity.py`

Institutional standard: every strategy must show how alpha decays as assumed fill costs increase from 0 → 1x → 2x → 5x
estimated.

```python
def compute_tc_sensitivity(
    gross_returns: list[float],
    estimated_tc_bps: float,
    multipliers: list[float] | None = None,
) -> dict[float, float]:
    """
    Returns {multiplier: net_sharpe} for each tc multiplier.
    If net_sharpe goes negative at 2x estimated TC, the alpha is illusory.
    """
```

**Tests required:**

- `test_tc_sensitivity_zero_alpha` — strategy with all alpha from TC artefact → Sharpe < 0 at 2x
- `test_tc_sensitivity_robust` — genuine alpha strategy → Sharpe positive at 5x TC

---

## Stream D — Kill Switch Durability (P1)

**Root cause:** `execution-service/execution_service/engine/kill_switch.py` — `threading.Event` lives in RAM. Process
restart (crash, OOM, container eviction) silently resets the kill switch to inactive. The trading halt is lost.

### D1 — Durable Kill Switch backed by Config Store

**File:** `execution-service/execution_service/engine/kill_switch.py` — full replacement

```python
"""Durable kill switch — persisted via UnifiedCloudConfig config store.

State survives process restarts. Must be explicitly deactivated by a human,
not by a restart event.
"""
from unified_cloud_interface import get_config_store
from unified_events_interface import KILL_SWITCH_ACTIVATED, KILL_SWITCH_DEACTIVATED, log_event

_KEY_ACTIVE = "kill_switch.active"
_KEY_REASON = "kill_switch.reason"
_KEY_ACTIVATED_AT = "kill_switch.activated_at"


def is_active() -> bool:
    """Return True if kill switch is active. Reads from config store on every call."""
    return bool(get_config_store().get(_KEY_ACTIVE, default=False))


def activate(reason: str) -> None:
    store = get_config_store()
    store.set(_KEY_ACTIVE, True)
    store.set(_KEY_REASON, reason)
    store.set(_KEY_ACTIVATED_AT, datetime.now(UTC).isoformat())
    log_event(KILL_SWITCH_ACTIVATED, details={"reason": reason})


def deactivate(deactivated_by: str) -> None:
    store = get_config_store()
    store.set(_KEY_ACTIVE, False)
    log_event(KILL_SWITCH_DEACTIVATED, details={"deactivated_by": deactivated_by})
```

Add `KILL_SWITCH_ACTIVATED` and `KILL_SWITCH_DEACTIVATED` to `unified-events-interface` if not present.

**Startup guard:** At `execution-service` startup, before any venue connection, check `is_active()`. If `True`, log
`KILL_SWITCH_BLOCKED_STARTUP` and refuse to start order submission. Log the stored reason so the operator knows why.

**Tests required:**

- `test_kill_switch_survives_restart` — activate → re-instantiate config store mock → `is_active()` still True
- `test_kill_switch_blocked_at_startup` — mock config store returning active=True → assert venue adapters not
  initialised
- `test_deactivation_requires_actor` — `deactivate()` without `deactivated_by` raises `TypeError`
- `test_kill_switch_event_emitted` — activate → assert `KILL_SWITCH_ACTIVATED` event logged with reason

---

## Stream E — Order Recovery Hardening (P1)

### E1 — Configurable Orphan Age Threshold per Venue

**File:** `execution-service/execution_service/engine/startup/order_recovery.py:48`

Current: `MAX_ORPHAN_AGE_MINUTES: int = 5` — module-level constant, not configurable.

Required:

- Move to `UnifiedCloudConfig`: `order_recovery.orphan_age_minutes_default = 5`
- Add per-venue override: `order_recovery.orphan_age_minutes.{venue} = 15` (e.g. IBKR has slower REST API)
- `OrderRecoveryEngine.__init__()` reads from config, not from the constant
- Add per-order-type override: maker limit orders get `30` minutes, IOC/FOK get `2` minutes

### E2 — Cancel Confirmation Loop

**File:** `execution-service/execution_service/engine/startup/order_recovery.py` — `recover_venue()` method

Current:

```python
cancelled = await self._venue_adapter.cancel_order(venue, ex_order.order_id)
if cancelled:
    result.cancelled_orphans += 1
```

Problem: `cancel_order()` returns `True` when the cancel _request_ was sent, not when the cancel was _confirmed_ by the
venue. If the order fills between the cancel request and confirmation, you have an unrecorded position.

Required:

```python
cancel_sent = await self._venue_adapter.cancel_order(venue, ex_order.order_id)
if cancel_sent:
    # Poll for confirmation with timeout
    confirmed = await self._venue_adapter.confirm_cancel(
        venue, ex_order.order_id, timeout_seconds=10
    )
    if confirmed:
        result.cancelled_orphans += 1
    else:
        # Cancel did not confirm — may have filled
        log_event(
            ORDER_CANCEL_UNCONFIRMED,
            severity="CRITICAL",
            details={"venue": venue, "order_id": ex_order.order_id},
        )
        result.cancel_unconfirmed += 1
        # Do NOT mark as cancelled internally — treat as PENDING until fill confirmed
```

Add `ORDER_CANCEL_UNCONFIRMED` to `unified-events-interface`.

**Tests required:**

- `test_orphan_age_from_config` — mock config returning `20` for IBKR → assert 20-minute threshold used
- `test_cancel_confirmation_required` — cancel sent, confirmation timeout → `ORDER_CANCEL_UNCONFIRMED` emitted
- `test_cancel_confirmed_marked_cancelled` — cancel + confirm success → order removed from internal state
- `test_cancel_unconfirmed_not_removed` — cancel unconfirmed → order stays in `PENDING` state

---

## Stream F — Stale Price Guard in Pre-Trade Risk (P1)

**Root cause:** `execution-service/execution_service/engine/live/risk.py` calls
`position_tracker.get_position(canonical_id)` with no check on data freshness. During a market data feed disruption,
pre-trade risk checks pass using stale position prices.

### F1 — Position Tracker: Return Timestamp with Position

**File:** `execution-service/execution_service/engine/live/positions.py` (or equivalent)

Change `get_position()` return type:

```python
# Before
async def get_position(canonical_id: str) -> dict | None: ...

# After
from datetime import datetime
async def get_position(canonical_id: str) -> tuple[dict | None, datetime | None]:
    """Returns (position_data, last_updated_at). last_updated_at is None if no position."""
```

### F2 — Pre-Trade Risk: Reject Stale Positions

**File:** `execution-service/execution_service/engine/live/risk.py`

```python
from unified_cloud_interface import UnifiedCloudConfig

_MAX_STALE_SECONDS_DEFAULT = 5  # configurable

async def check_order(self, ...) -> tuple[bool, str]:
    pos, last_updated = await self.position_tracker.get_position(canonical_id)
    if last_updated is not None:
        staleness = (datetime.now(UTC) - last_updated).total_seconds()
        max_stale = UnifiedCloudConfig().get(
            "risk.max_stale_position_seconds", default=_MAX_STALE_SECONDS_DEFAULT
        )
        if staleness > max_stale:
            log_event(
                STALE_POSITION_DATA,
                severity="WARNING",
                details={"canonical_id": canonical_id, "staleness_s": staleness},
            )
            return False, f"Position data stale by {staleness:.1f}s (max {max_stale}s)"
```

Add `STALE_POSITION_DATA` to `unified-events-interface`.

**Tests required:**

- `test_stale_position_rejected` — position last updated 10s ago, max_stale=5 → rejected with reason
- `test_fresh_position_accepted` — position last updated 1s ago, max_stale=5 → proceeds to limit check
- `test_stale_check_bypassed_in_batch_mode` — batch/backtest mode has no staleness constraint
- `test_stale_event_emitted` — staleness exceeded → `STALE_POSITION_DATA` event logged

---

## Stream G — Circuit Breaker Exponential Backoff (P2)

**Root cause:** `execution-service/execution_service/engine/circuit_breaker.py:38–39` — fixed 300s cooldown.
Intermittent venue failures cycle OPEN→HALF_OPEN→OPEN every 5 minutes, locking you out of the venue for hours while
hedges remain unplaced.

### G1 — Exponential Backoff on Consecutive OPEN Cycles

**File:** `execution-service/execution_service/engine/circuit_breaker.py`

Add to `VenueCircuitBreaker`:

```python
_consecutive_open_cycles: int = 0
_BASE_COOLDOWN: float  # from config, default 300.0
_MAX_COOLDOWN: float = 3600.0  # cap at 1 hour

def _compute_cooldown(self) -> float:
    """Exponential backoff: 300 → 600 → 1200 → 2400 → 3600s (capped)."""
    return min(self._BASE_COOLDOWN * (2 ** self._consecutive_open_cycles), self._MAX_COOLDOWN)

def _transition_to_open(self) -> None:
    self._state = _STATE_OPEN
    self._open_at = time.monotonic()
    self._consecutive_open_cycles += 1
    self._cooldown = self._compute_cooldown()  # use per-cycle cooldown

def _transition_to_closed(self) -> None:
    self._state = _STATE_CLOSED
    self._consecutive_open_cycles = 0  # reset on successful recovery
    self._failure_count = 0
```

### G2 — DEGRADED Intermediate State

Add `_STATE_DEGRADED` between CLOSED and OPEN. Enters DEGRADED when failure rate is 20–60% over a 60-second window (not
consecutive failures, but rate-based). In DEGRADED state: orders allowed at reduced rate (50% of normal submit rate),
`CIRCUIT_BREAKER_DEGRADED` event emitted.

```python
_STATE_DEGRADED: str = "DEGRADED"

# Rolling window failure rate
_recent_results: deque[bool]  # True=success, False=failure; maxlen=20
_degraded_threshold: float = 0.3  # 30% failure rate → DEGRADED
_open_threshold: float = 0.6     # 60% failure rate → OPEN
```

**Tests required:**

- `test_exponential_backoff_three_cycles` — 3 OPEN cycles → cooldowns are 300, 600, 1200
- `test_backoff_resets_on_close` — OPEN×3 → successful CLOSED → next OPEN starts back at 300s
- `test_degraded_state_at_30pct` — 6/20 recent failures → DEGRADED state, orders not blocked
- `test_open_state_at_60pct` — 12/20 recent failures → OPEN state, orders blocked
- `test_max_cooldown_cap` — 10 OPEN cycles → cooldown does not exceed 3600s

---

## Stream H — Multi-Leg Cancel Race Condition (P2)

**Root cause:** `execution-service/execution_service/engine/concurrent.py` — after leg imbalance, cancel is sent to the
successful leg but cancel success is not verified before clearing imbalance state.

### H1 — Cancel Confirmation + Strategy Halt on Unconfirmed Cancel

**File:** `execution-service/execution_service/engine/concurrent.py`

After detecting imbalance:

```python
if imbalance:
    # Attempt to cancel the successful leg
    cancel_result = await _attempt_cancel_with_confirmation(
        successful_leg_instruction,
        handler_registry,
        timeout_ms=200,
    )
    if not cancel_result.confirmed:
        # Cancel did not confirm — may have filled
        log_event(
            "CONCURRENT_LEG_CANCEL_UNCONFIRMED",
            severity="CRITICAL",
            details={
                "execution_id": execution_id,
                "unhedged_leg": successful_leg,
                "spread_id": spread_id,
            },
        )
        # Halt further submissions for this spread_id
        await _halt_spread(spread_id, reason="cancel_unconfirmed")
```

`_halt_spread()` writes to the config store under key `spread_halts.{spread_id}` so it survives restarts.

**Tests required:**

- `test_imbalance_cancel_confirmed` — leg A fails, cancel leg B sent, confirmed → `both_succeeded=False`, no halt
- `test_imbalance_cancel_unconfirmed` — leg A fails, cancel B unconfirmed → `CONCURRENT_LEG_CANCEL_UNCONFIRMED`
  emitted + spread halted
- `test_halted_spread_blocks_new_orders` — `_halt_spread()` written → subsequent submission to same spread rejected

---

## Stream I — Position Model Type Unification (P2)

**Root cause:** DeFi positions use `Decimal` (`execution_service/models/position.py:80`), CeFi/TradFi orders use `float`
(`orders/oms.py`). Cross-asset position aggregation silently casts Decimals to floats during portfolio-level risk
calculations.

### I1 — Unified Position Quantity/Price Protocol

**New file:** `unified-internal-contracts/unified_internal_contracts/position_types.py`

```python
from decimal import Decimal
from typing import Protocol

class PositionQuantityProtocol(Protocol):
    """All position models must expose quantity as Decimal."""
    @property
    def quantity(self) -> Decimal: ...
    @property
    def price(self) -> Decimal: ...
    @property
    def last_updated(self) -> datetime: ...
```

All position models (`DeFiPosition`, CeFi OMS positions, TradFi positions) must implement this protocol.

Add cross-asset portfolio aggregator that accepts `list[PositionQuantityProtocol]` and performs all arithmetic in
`Decimal`. Never casts to float internally.

**Tests required:**

- `test_defi_cefi_aggregation_decimal` — mix DeFi (Decimal) + CeFi position → portfolio total in Decimal, no float cast
- `test_protocol_compliance_defi` — `DeFiPosition` satisfies `PositionQuantityProtocol` (runtime check)
- `test_protocol_compliance_oms` — updated OMS position satisfies protocol

---

## Stream J — OrchestrationWorkersMixin Refactor (P3)

**Root cause:** `market-data-processing-service/market_data_processing_service/app/core/orchestration_workers.py` is 728
lines with `write_candles()` at 204 lines. Violates 900L class / 200L function limits. Untestable at responsibility
level — impossible to mock individual concerns.

### J1 — Split into Four Focused Classes

**New structure:**

```
app/core/
  candle_generator.py         # CandleGeneratorWorker — pure computation, no I/O
  parquet_schema_worker.py    # ParquetSchemaWorker — schema enforcement + validation
  storage_dispatch_worker.py  # StorageDispatchWorker — GCS write + event emission
  orchestration_coordinator.py # OrchestrationCoordinator — thin coordinator (< 100L)
  orchestration_workers.py    # KEEP for backward compat: re-exports coordinator
```

Each class:

- `< 200` lines
- Has its own unit test file
- Has no I/O dependency except `StorageDispatchWorker`
- Injected via constructor (no `self._storage_client = StorageClient()` inside `__init__`)

**Tests required per class:**

- `CandleGeneratorWorker` — feed raw tick list, assert OHLCV output (no I/O)
- `ParquetSchemaWorker` — feed valid + invalid DataFrames, assert schema enforcement
- `StorageDispatchWorker` — mock `StorageClient`, assert upload called with correct path + event emitted
- `OrchestrationCoordinator` — mock all three workers, assert delegation order

---

## Stream K — Research Quality Standards (P3)

### K1 — Regime Classification for Strategy Validation

**New file:** `unified-trading-library/src/unified_trading_library/regime_classifier.py`

```python
from enum import StrEnum

class MarketRegime(StrEnum):
    BULL_LOW_VOL = "bull_low_vol"
    BULL_HIGH_VOL = "bull_high_vol"
    BEAR_LOW_VOL = "bear_low_vol"
    BEAR_HIGH_VOL = "bear_high_vol"

def classify_regime(
    returns: list[float],
    volatility: list[float],
    return_threshold: float = 0.0,
    vol_threshold_percentile: float = 50.0,
) -> list[MarketRegime]:
    """Classify each period into one of four regimes."""
```

Strategies must show positive expectancy in at least 3 of 4 regimes. If performance concentrates in 1 regime, it is
curve-fitted to that regime.

### K2 — Capacity Analysis

**New file:** `unified-trading-library/src/unified_trading_library/capacity_analysis.py`

```python
def compute_capacity_curve(
    gross_returns: list[float],
    estimated_aum: float,
    market_impact_model: Callable[[float, float], float],
    aum_steps: list[float] | None = None,
) -> dict[float, float]:
    """
    Returns {aum: net_sharpe} showing alpha decay as AUM increases.
    Institutional requirement: strategy must be viable at target AUM.
    """
```

### K3 — Survivorship Bias Guard for Return Series

**New file:** `unified-trading-library/src/unified_trading_library/survivorship_guard.py`

```python
def validate_return_series_coverage(
    return_series: pd.Series,
    universe_start_date: date,
    as_of_date: date,
) -> SurvivorshipReport:
    """
    Checks whether the return series has gaps consistent with
    survivorship bias (instrument added mid-period or became liquid
    only during the lookback window).

    Flags: missing data at start of window, first observation date
    significantly after universe_start_date.
    """
```

---

## Acceptance Criteria

### Stream A (Float → Decimal)

- [ ] `oms.py` `quantity` and `price` fields are `Decimal`; float input raises `TypeError`
- [ ] `risk.py` position accumulation uses Decimal arithmetic; verified with 100-fill exact test
- [ ] `order_recovery.py` uses Decimal for all quantity/fill fields
- [ ] `features.py` derived price fields (`basis`, `price_ratio`, etc.) are `Decimal`
- [ ] Parquet encoding decision documented in codex; migration utility present
- [ ] All existing tests pass with no float-quantity regressions

### Stream B (VaR)

- [ ] `parametric_var_cornish_fisher()` implemented and exported
- [ ] `InsufficientDataError` raised for n<30 (parametric), n<10 (historical)
- [ ] Stress multipliers read from `UnifiedCloudConfig`
- [ ] All 6 VaR tests pass

### Stream C (Lookahead Bias)

- [ ] `PointInTimeEnforcer` in UTL, exported from `__init__`
- [ ] All 8 feature services call `enforce_point_in_time()` before storage write
- [ ] ML training pipeline: split before normalize, `TrainTestSplitValidator` present
- [ ] `WalkForwardEvaluator` implemented with no-overlap guarantee
- [ ] Strategy backtest has PIT reference data guard
- [ ] `compute_tc_sensitivity()` implemented

### Stream D (Kill Switch)

- [ ] Kill switch backed by config store; survives process restart
- [ ] Startup guard blocks order submission if switch is active
- [ ] `KILL_SWITCH_ACTIVATED` / `KILL_SWITCH_DEACTIVATED` events in UEI

### Stream E (Order Recovery)

- [ ] Orphan age threshold from config, per-venue override supported
- [ ] Cancel confirmation loop: unconfirmed cancels emit `ORDER_CANCEL_UNCONFIRMED`
- [ ] Unconfirmed cancelled orders stay PENDING, not removed from internal state

### Stream F (Stale Price Guard)

- [ ] `get_position()` returns `(data, timestamp)` tuple
- [ ] Pre-trade risk rejects orders when position data older than config threshold
- [ ] `STALE_POSITION_DATA` event in UEI

### Stream G (Circuit Breaker)

- [ ] Exponential backoff implemented; 3-cycle progression verified by test
- [ ] `_STATE_DEGRADED` present; enters at 30% failure rate
- [ ] Max cooldown capped at 3600s

### Stream H (Multi-Leg Race)

- [ ] Cancel confirmation required before clearing imbalance state
- [ ] Unconfirmed cancel → spread halted in durable config store

### Stream I (Position Model)

- [ ] `PositionQuantityProtocol` in UIC
- [ ] Cross-asset aggregator uses Decimal arithmetic
- [ ] DeFi + CeFi positions satisfy protocol (runtime check)

### Stream J (Orchestration Refactor)

- [ ] `OrchestrationWorkersMixin` replaced by 4 focused classes
- [ ] Each class < 200L with its own test file
- [ ] All existing candle generation tests pass

### Stream K (Research Quality)

- [ ] `MarketRegime` classifier implemented
- [ ] `compute_capacity_curve()` implemented
- [ ] `SurvivorshipReport` validator implemented

---

## Implementation Order

| Order | Stream                                     | Reason                                      |
| ----- | ------------------------------------------ | ------------------------------------------- |
| 1     | C1 — PointInTimeEnforcer (UTL)             | Zero-dependency; unlocks all other C work   |
| 2     | B2 — InsufficientDataError + guard         | Tiny, high safety value                     |
| 3     | D1 — Durable kill switch                   | Safety-critical; standalone change          |
| 4     | F1+F2 — Stale price guard                  | Standalone; high stress-market value        |
| 5     | A1+A2 — Float→Decimal OMS+risk             | Highest P0 risk; start with core path       |
| 6     | E1+E2 — Order recovery hardening           | Builds on A3 Decimal change                 |
| 7     | A3+A4 — Recovery + contract Decimal        | Complete Decimal migration                  |
| 8     | C2 — PIT enforcement in feature services   | Depends on C1                               |
| 9     | C3+C4 — ML split validator + walk-forward  | Depends on C1                               |
| 10    | B1+B3 — Cornish-Fisher + regime multiplier | Depends on B2                               |
| 11    | G1+G2 — Circuit breaker backoff + degraded | Moderate complexity                         |
| 12    | H1 — Multi-leg cancel confirmation         | Moderate complexity                         |
| 13    | I1 — Position model unification            | Depends on A1 Decimal being done            |
| 14    | C5 — Strategy backtest PIT guard           | Depends on C1                               |
| 15    | C6+K1+K2+K3 — Research quality tooling     | Research infra; non-blocking                |
| 16    | J1 — Orchestration refactor                | Maintainability; non-blocking               |
| 17    | A5 — Parquet fixed-point                   | Longest; requires schema migration planning |

---

## Notes

- All new classes: no `os.getenv()` — use `UnifiedCloudConfig`
- All new events: register in `unified-events-interface` before use
- All Decimal coercions from external strings: use `Decimal(str(value))` never `Decimal(float_value)`
- Float → Decimal migration is a breaking change for any consumer that serialises positions to JSON with `json.dumps()`
  — switch to `str(decimal_value)` or use `decimal_encoder` in serialisation layer
- `PointInTimeEnforcer` is intentionally in UTL (not UIC) as it is a utility function, not a domain contract
- Walk-forward folds must use calendar dates, not trading day counts, to avoid look-ahead through holiday calendars
