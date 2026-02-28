# HFT Features Implementation Status

**Date:** 2026-02-28
**Plan:** [HFT Feature Pipeline Integration](../.cursor/plans/hft_feature_pipeline_integration_70995051.plan.md)

## Summary

Adding 27 new HFT/microstructure features across 5 tiers to the feature engineering pipeline.

---

## Phase 1: SSOT Updates ✅ COMPLETE

### Completed
- ✅ **workspace-manifest.json**: Added `features-cross-instrument-service` at merge_level 7 (tier restructure 2026-02-28: old L6 services shifted to L7; deployment-api/engine inserted at new L6)
- ✅ **runtime-topology.yaml**: Added service flows, sharding dimensions, persistence flows, batch/live services list
- ✅ **TOPOLOGY-DAG.md**: Updated mermaid diagram with new service node and dependency edges

### Deferred (Manual)
- ⏸️ **SVG Diagrams**: RUNTIME_DEPLOYMENT_TOPOLOGY_DAG.svg and WORKSPACE_MANIFEST_DAG.svg require manual SVG editing or regeneration from YAML

---

## Phase 2: Repository Scaffolding (IN PROGRESS)

### features-cross-instrument-service Structure

```
features-cross-instrument-service/
├── features_cross_instrument_service/
│   ├── app/
│   │   ├── calculators/
│   │   │   ├── regime_calculator.py          # HMM, correlation regimes
│   │   │   ├── cross_venue_calculator.py     # Cross-venue spreads (Binance baseline)
│   │   │   ├── realized_implied_vol.py       # Realized vs implied vol ratio
│   │   │   └── cross_asset_correlation.py    # Cross-asset correlation
│   │   ├── core/
│   │   │   ├── orchestration_service.py
│   │   │   ├── data_loader.py
│   │   │   └── feature_writer.py
│   │   └── utils/
│   ├── engine/
│   │   └── cross_instrument_engine.py
│   ├── cli/
│   │   └── main.py
│   ├── schemas/
│   │   └── output_schemas.py
│   ├── config.py
│   └── models.py
├── tests/
│   ├── unit/
│   │   ├── test_regime_calculator.py
│   │   ├── test_cross_venue_calculator.py
│   │   ├── test_realized_implied_vol.py
│   │   └── test_time_leakage_guards.py      # Critical: prevent forward-looking bias
│   └── conftest.py
├── docs/
│   ├── ARCHITECTURE.md
│   ├── FEATURE_SPECIFICATION.md
│   ├── DEPENDENCIES.md
│   ├── GCS_PATHS.md
│   └── CONFIGURATION.md
├── scripts/
│   └── quality-gates.sh
├── pyproject.toml
└── README.md
```

**Key Dependencies (pyproject.toml):**
- `hmmlearn>=0.3.0` - HMM regime detection
- `ruptures>=1.1.0` - Changepoint detection for correlation regimes
- `scipy>=1.11.0` - Statistical functions
- Standard: `numpy`, `pandas`, `polars`, `pyarrow`
- Unified libs: `unified-trading-services`, `unified-domain-client`, `unified-feature-calculator-library`, `unified-config-interface`, `unified-events-interface`

---

## Phase 3: Schema Additions

### api-contracts (External Data Schemas)

**New files to create:**

1. **`api_contracts_external/databento/options.py`**
   - `DatabentoOptionQuote` - OPRA equity options
   - `DatabentoCMEOption` - CME gold/NG options

2. **`api_contracts_external/sentiment/cryptopanic.py`**
   - `CryptoPanicSentiment` - Crypto news sentiment

3. **`api_contracts_external/sentiment/lunarcrush.py`**
   - `LunarCrushSentiment` - Social sentiment

4. **`api_contracts_external/onchain/cryptoquant.py`**
   - `CryptoQuantExchangeFlow` - Exchange inflow/outflow

5. **`api_contracts_external/macro/fred.py`** (extend existing)
   - Treasury yield curve data

6. **`api_contracts_external/macro/yahoo_finance.py`**
   - DXY dollar index data

### unified-internal-contracts (Canonical Schemas)

**New files to create:**

1. **`unified_internal_contracts/market_data/option_quote.py`**
   ```python
   class CanonicalOptionQuote(BaseModel):
       instrument_key: str
       venue: str
       timestamp: datetime
       underlying: str
       strike: Decimal
       expiration: date
       option_type: Literal["call", "put"]
       bid_price: Decimal
       ask_price: Decimal
       bid_size: Decimal
       ask_size: Decimal
       bid_iv: Decimal | None
       ask_iv: Decimal | None
       mid_iv: Decimal | None
   ```

2. **`unified_internal_contracts/market_data/book_update.py`**
   ```python
   class CanonicalBookUpdate(BaseModel):
       instrument_key: str
       venue: str
       timestamp: datetime
       sequence_number: int
       update_type: Literal["add", "modify", "cancel"]
       side: Literal["bid", "ask"]
       price: Decimal
       size: Decimal
       order_id: str | None
   ```

3. **`unified_internal_contracts/features/cross_instrument.py`**
   ```python
   class CrossInstrumentFeatures(BaseModel):
       timestamp: datetime
       feature_category: Literal["regime", "cross_venue_spread", "realized_vs_implied", "cross_asset_correlation"]
       base_asset: str  # e.g., "BTC"
       representative_venue: str  # "BINANCE-FUTURES"
       features: dict[str, float]
       metadata: dict[str, Any]
   ```

---

## Phase 4: Feature Implementations

### Tier 1: Compute from Existing Data (10 features)

#### MDPS Additions (`market-data-processing-service`)

**Files to modify:**

1. **`app/adapters/cefi/trades_adapter.py`**
   - ✅ Add `calculate_trade_size_percentiles()` - p10, p50, p90, p99
   - ✅ Add `detect_whale_trades()` - trades > p99 rolling distribution
   - ✅ Add `calculate_volume_clock_features()` - time to fill N contracts

2. **`app/adapters/cefi/book_snapshot_adapter.py`**
   - ✅ Add `calculate_spread_volatility()` - std of 15 intra-candle spread samples
   - ✅ Add `calculate_book_pressure_gradient()` - volume slope across 5 levels
   - ✅ Add `calculate_effective_to_quoted_ratio()` - effective/quoted spread ratio

3. **`app/adapters/cefi/liquidations_adapter.py`**
   - ✅ Add `calculate_liquidation_cascade_metrics()` - inter-time, acceleration, clustering

4. **`schemas/output_schemas.py`**
   - ✅ Add new columns to `PROCESSED_CANDLE_SCHEMA`

#### features-delta-one-service Additions

**Files to modify:**

1. **`app/calculators/microstructure.py`**
   - ✅ Add `calculate_amihud_illiquidity()` - |return| / dollar volume
   - ✅ Add `calculate_vpin()` - volume-sync'd probability of informed trading
   - ✅ Add `calculate_kyles_lambda()` - rolling regression ΔP on signed volume
   - ✅ Add `calculate_funding_rate_cross_venue_spread()` - funding arb signal

2. **`schemas/output_schemas.py`**
   - ✅ Add new feature columns

### Tier 2: Regime Features (4 features)

#### features-cross-instrument-service (NEW)

**Files to create:**

1. **`app/calculators/regime_calculator.py`**
   - ✅ `RegimeCalculator.fit_hmm_volatility_regime()` - 2-3 state Gaussian HMM on returns
   - ✅ `RegimeCalculator.calculate_regime_persistence()` - time-in-current-regime
   - ✅ `CorrelationRegimeCalculator.detect_correlation_regime_changes()` - changepoint detection
   - ✅ `CorrelationRegimeCalculator.calculate_regime_transition_probability()` - HMM transition matrix

**Key Implementation Notes:**
- Use `hmmlearn.hmm.GaussianHMM` for volatility regimes
- Use `ruptures.Pelt` for correlation changepoint detection
- **Time-leakage guard**: HMM fitted on historical data only, never future data
- **Test requirement**: `test_time_leakage_guards.py` must verify no forward-looking bias

### Tier 3: TradFi Vol Surfaces (4 features)

#### features-volatility-service Additions

**Files to create:**

1. **`app/calculators/tradfi_vol_surface.py`**
   - ✅ `TradFiVolSurfaceCalculator.calculate_vol_surface_features()` - ATM IV, skew, term structure
   - ✅ `_interpolate_iv()` - cubic interpolation across moneyness/expiry grid
   - ✅ `_calculate_skew()` - 25-delta put-call skew
   - ✅ `_calculate_convexity()` - butterfly spread (vol surface curvature)

2. **`app/adapters/databento_opra_adapter.py`** (market-tick-data-handler)
   - ✅ Ingest CBOE equity options (SPY, QQQ, single stocks)

3. **`app/adapters/databento_cme_adapter.py`** (market-tick-data-handler)
   - ✅ Ingest CME gold/NG options

**Data Source:** Databento OPRA + CME GLBX.MDP3 (subscription required)

### Tier 4: External Data Sources (6 features)

**Adapters to create:**

1. **`features-calendar-service/app/adapters/cryptopanic_adapter.py`**
   - Crypto sentiment score (CryptoPanic API, free tier: 5 req/min)

2. **`features-calendar-service/app/adapters/lunarcrush_adapter.py`**
   - Social sentiment (LunarCrush free tier)

3. **`features-onchain-service/app/adapters/cryptoquant_adapter.py`**
   - Exchange inflow/outflow (CryptoQuant free tier or $29/mo)

4. **`features-onchain-service/app/adapters/defillama_adapter.py`** (extend existing)
   - Stablecoin dominance rate-of-change

5. **`features-calendar-service/app/adapters/fred_adapter.py`** (extend existing)
   - Treasury yield curve slope (10Y-2Y, 10Y-3M)

6. **`features-calendar-service/app/adapters/yahoo_finance_adapter.py`**
   - DXY momentum (Yahoo Finance free)

### Tier 5: Incremental Book Features (3 features)

#### market-tick-data-handler Additions

**Files to create:**

1. **`app/adapters/cefi/tardis_incremental_book_adapter.py`**
   - ✅ `IncrementalBookAdapter.calculate_order_cancellation_rate()` - cancel rate per minute
   - ✅ `IncrementalBookAdapter.detect_iceberg_orders()` - repeated adds at same price
   - ✅ `IncrementalBookAdapter.calculate_order_arrival_rate_by_level()` - queue dynamics

**Data Source:** Tardis incremental_book_L2 feed (already subscribed)

---

## Phase 5: Cross-Venue Features (Representative Underlying)

### Implementation Strategy

**Representative Underlying: Binance**
- All cross-venue spreads calculated vs Binance as baseline
- Defined in: `unified-trading-deployment-v3/configs/representative_instruments.yaml`
- Example: `BTC-USDT@LIN` on `BINANCE-FUTURES` is representative for BTC

**Cross-Venue Calculator** (`features-cross-instrument-service/app/calculators/cross_venue_calculator.py`):

```python
class CrossVenueCalculator:
    """Calculate cross-venue spreads using Binance as representative baseline."""

    def calculate_venue_spreads(self, data: dict[str, pd.DataFrame], base_asset: str) -> pd.DataFrame:
        """
        Calculate spreads of all venues vs Binance (representative).

        Args:
            data: {venue: DataFrame} with columns [timestamp, close, ...]
            base_asset: e.g., "BTC"

        Returns:
            DataFrame with columns:
            - timestamp
            - binance_close (representative)
            - okx_spread_bps (OKX - Binance) / Binance * 10000
            - bybit_spread_bps
            - hyperliquid_spread_bps
            - ...
        """
        representative_venue = "BINANCE-FUTURES"
        binance_data = data[representative_venue]

        features = {"timestamp": binance_data["timestamp"], "binance_close": binance_data["close"]}

        for venue, venue_data in data.items():
            if venue == representative_venue:
                continue

            # Merge on timestamp
            merged = pd.merge(binance_data[["timestamp", "close"]],
                             venue_data[["timestamp", "close"]],
                             on="timestamp",
                             suffixes=("_binance", f"_{venue}"))

            # Calculate spread in bps
            spread_bps = ((merged[f"close_{venue}"] - merged["close_binance"]) /
                         merged["close_binance"]) * 10000

            features[f"{venue.lower()}_spread_bps"] = spread_bps

        return pd.DataFrame(features)

    def calculate_spread_to_moving_average(self, df: pd.DataFrame, windows: list[int] = [20, 50, 200]) -> pd.DataFrame:
        """Calculate spread of price to its moving averages."""
        for window in windows:
            ma = df["close"].rolling(window).mean()
            df[f"spread_to_ma{window}_bps"] = ((df["close"] - ma) / ma) * 10000
        return df

    def calculate_cross_venue_correlation(self, data: dict[str, pd.DataFrame], window: int = 50) -> pd.DataFrame:
        """Calculate rolling correlation between venues."""
        # Pivot to wide format
        all_closes = {}
        for venue, venue_data in data.items():
            all_closes[venue] = venue_data.set_index("timestamp")["close"]

        wide_df = pd.DataFrame(all_closes)

        # Rolling correlation matrix
        rolling_corr = wide_df.rolling(window).corr()

        # Extract pairwise correlations
        # ... implementation
        return rolling_corr
```

**Realized vs Implied Vol Ratio** (`features-cross-instrument-service/app/calculators/realized_implied_vol.py`):

```python
class RealizedImpliedVolCalculator:
    """Calculate realized vs implied volatility ratios."""

    def calculate_vol_ratio(self, realized_vol_df: pd.DataFrame, implied_vol_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate realized / implied vol ratio.

        IMPORTANT: Realized vol looks backward, implied vol looks forward.
        This is acceptable for feature engineering as they measure different things:
        - Realized vol: historical volatility (backward-looking)
        - Implied vol: market's expectation of future volatility (forward-looking)

        Time-leakage guard: Ensure realized vol uses only past data (no .shift(-horizon)).
        """
        # Merge on timestamp
        merged = pd.merge(realized_vol_df, implied_vol_df, on=["timestamp", "instrument_key"])

        # Calculate ratio
        merged["realized_implied_vol_ratio"] = merged["realized_vol_20"] / (merged["atm_iv"] + 1e-10)

        # Ratio regime
        merged["vol_ratio_zscore"] = (
            (merged["realized_implied_vol_ratio"] - merged["realized_implied_vol_ratio"].rolling(100).mean()) /
            (merged["realized_implied_vol_ratio"].rolling(100).std() + 1e-10)
        )

        return merged
```

---

## Phase 6: Time-Leakage Prevention

### Critical Guards

**Test File:** `tests/unit/test_time_leakage_guards.py`

```python
def test_no_forward_looking_in_realized_vol():
    """Ensure realized vol never uses future data."""
    calculator = RegimeCalculator()

    # Create synthetic data with known future spike
    df = create_synthetic_data_with_future_spike(spike_at_idx=100)

    # Calculate features up to idx=50
    features = calculator.fit_hmm_volatility_regime(df.iloc[:50]["returns"])

    # Verify: features at idx=50 should NOT reflect spike at idx=100
    assert features["current_regime"] != detect_spike_regime(df.iloc[100])

def test_no_shift_negative_in_features():
    """Scan all feature calculators for .shift(-N) usage."""
    # Allowed: targets.py (explicitly forward-looking labels)
    # Forbidden: All other calculators

    for calculator_file in glob("app/calculators/*.py"):
        if "targets.py" in calculator_file:
            continue

        with open(calculator_file) as f:
            content = f.read()
            # Check for .shift(-N) pattern
            assert not re.search(r"\.shift\(-\d+\)", content), \
                f"Forward-looking .shift() found in {calculator_file}"
```

**Enforcement:**
- All calculators use `.rolling(window)` with positive lookback only
- `.shift(-horizon)` ONLY allowed in `targets.py` (ML labels)
- Unit tests verify no future data leakage
- Code review checklist includes time-leakage check

---

## Phase 7: Testing Strategy

### Unit Tests (Required)

**Coverage target:** Maintain existing coverage (no drops)

**Test files to create:**

1. **`tests/unit/test_regime_calculator.py`**
   - Test HMM with synthetic 3-regime data
   - Test regime persistence calculation
   - Test correlation changepoint detection

2. **`tests/unit/test_cross_venue_calculator.py`**
   - Test spread calculation vs Binance baseline
   - Test handling of missing venues
   - Test spread to MA calculation

3. **`tests/unit/test_realized_implied_vol.py`**
   - Test vol ratio calculation
   - Test handling of zero/NaN implied vol
   - Test regime classification

4. **`tests/unit/test_time_leakage_guards.py`** (CRITICAL)
   - Test no forward-looking data in all calculators
   - Test `.shift(-N)` only in targets.py
   - Test rolling windows use past data only

5. **`tests/unit/test_trade_size_percentiles.py`** (MDPS)
   - Test percentile calculations
   - Test whale trade detection
   - Test volume clock features

### Integration Tests (DEFERRED)

**Reason:** Requires testing infrastructure from consolidated plan

**Future tests:**
- End-to-end: MDPS → features-delta-one → features-cross-instrument → ML
- Schema validation on real GCS data
- Live mode PubSub flow

---

## Phase 8: Deployment Configuration

### Sharding Config

**File:** `unified-trading-deployment-v3/configs/sharding_config.yaml`

```yaml
features-cross-instrument-service:
  batch:
    dimensions: [category, feature_category, date]
    category_values: [cefi, defi, tradfi]
    feature_category_values:
      - regime
      - cross_venue_spread
      - realized_vs_implied
      - cross_asset_correlation
  live:
    dimensions: [feature_category]
    feature_category_values:
      - regime
      - cross_venue_spread
      - realized_vs_implied
      - cross_asset_correlation
```

### Cloud Build Trigger

**File:** `.github/workflows/features-cross-instrument-service-build.yml`

```yaml
name: features-cross-instrument-service-build
on:
  push:
    branches: [main]
    paths:
      - 'features-cross-instrument-service/**'
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build and push
        run: |
          gcloud builds submit features-cross-instrument-service/ \
            --config features-cross-instrument-service/cloudbuild.yaml
```

### PubSub Topics

**Topics to create:**

```bash
# Regime features
gcloud pubsub topics create features-cross-instrument-regime

# Cross-venue spreads
gcloud pubsub topics create features-cross-instrument-cross_venue_spread

# Realized vs implied vol
gcloud pubsub topics create features-cross-instrument-realized_vs_implied

# Cross-asset correlation
gcloud pubsub topics create features-cross-instrument-cross_asset_correlation
```

---

## Deferred Tasks (Require Deployment)

### Cannot Complete Without Infrastructure

- ❌ Integration testing (needs testing infrastructure)
- ❌ Schema validation on real data (needs deployment)
- ❌ Live mode smoke testing (needs deployment)
- ❌ Data backfilling (needs deployment)
- ❌ Databento API key provisioning (deployment task)
- ❌ External API keys provisioning (deployment task)
- ❌ Event logging verification (needs deployment)
- ❌ Data completeness checks (needs deployment)

**Next Steps:**
1. Complete all code implementations locally
2. Run unit tests to maintain coverage
3. Run quality gates on all modified repos
4. Leave changes uncommitted until testing infrastructure is ready
5. Add deferred tasks to consolidated plan for later execution

---

## Documentation Updates

### Codex Updates Required

**Files to update:**

1. **`unified-trading-codex/02-data/feature-pipeline-architecture.md`**
   - Add section on cross-instrument features
   - Document representative underlying (Binance baseline)
   - Add data flow diagrams

2. **`unified-trading-codex/04-architecture/RUNTIME_TOPOLOGY_DECISIONS.md`**
   - Document decision to create features-cross-instrument-service
   - Rationale for keeping Tier 1 features in MDPS
   - Regime feature implementation approach

3. **`unified-trading-codex/06-coding-standards/time-leakage-prevention.md`** (NEW)
   - Guidelines for preventing forward-looking bias
   - Test patterns for time-leakage guards
   - Allowed vs forbidden patterns

### Service Documentation

**Files to create:**

1. **`market-data-processing-service/docs/HFT_FEATURES_TIER1_ADDITIONS.md`**
2. **`features-cross-instrument-service/docs/FEATURE_SPECIFICATION.md`**
3. **`features-volatility-service/docs/TRADFI_VOL_SURFACES.md`**
4. **`features-delta-one-service/docs/EXTERNAL_DATA_SOURCES.md`**
5. **`market-tick-data-handler/docs/INCREMENTAL_BOOK_L2.md`**

---

## Summary Statistics

**Total Features:** 27 feature groups
- Tier 1 (existing data): 10 features
- Tier 2 (regime): 4 features
- Tier 3 (TradFi vol): 4 features
- Tier 4 (external data): 6 features
- Tier 5 (incremental book): 3 features

**Repos Modified:** 7
- market-data-processing-service
- features-delta-one-service
- features-volatility-service
- features-cross-instrument-service (NEW)
- market-tick-data-handler
- api-contracts
- unified-internal-contracts

**Repos Updated (SSOTs):** 3
- unified-trading-pm (workspace-manifest.json)
- unified-trading-deployment-v3 (runtime-topology.yaml)
- unified-trading-codex (TOPOLOGY-DAG.md)

**Estimated Effort:** 20-28 days (4-6 weeks with parallel execution)

**Current Status:** Phase 1 complete (SSOTs), Phase 2-4 in progress (implementations)
