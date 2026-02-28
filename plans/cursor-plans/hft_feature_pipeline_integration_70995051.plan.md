---
name: HFT Feature Pipeline Integration
overview: "Integrate 27 new HFT/microstructure features across the feature engineering pipeline, including: Tier 1 (10 features from existing data in MDPS/features-delta-one), Tier 2 (4 regime features requiring new calculator), Tier 3 (4 TradFi vol surfaces via Databento), Tier 4 (6 cheap/free external data sources), Tier 5 (3 incremental book features). Create new features-cross-instrument-service for cross-asset calculations. Update all SSOTs, DAGs, manifests, and deployment topology."
todos:
  - id: update_workspace_manifest
    content: Add features-cross-instrument-service to workspace-manifest.json with correct dependencies and merge_level
    status: completed
  - id: update_runtime_topology
    content: Add service flows, sharding dimensions, and persistence flows to runtime-topology.yaml
    status: completed
  - id: update_topology_dag
    content: Update TOPOLOGY-DAG.md mermaid diagram with new service and edges
    status: completed
  - id: update_svg_diagrams
    content: Update RUNTIME_DEPLOYMENT_TOPOLOGY_DAG.svg and WORKSPACE_MANIFEST_DAG.svg
    status: completed
  - id: create_feature_specs
    content: Create feature specification documents for all 5 tiers
    status: completed
  - id: scaffold_cross_instrument_service
    content: Scaffold features-cross-instrument-service directory structure and pyproject.toml
    status: completed
  - id: add_databento_schemas
    content: Add Databento OPRA and CME options schemas to api-contracts
    status: completed
  - id: add_external_data_schemas
    content: Add external data source schemas (CryptoPanic, LunarCrush, etc.) to api-contracts
    status: completed
  - id: add_internal_schemas
    content: Add CanonicalOptionQuote, CanonicalBookUpdate, CrossInstrumentFeatures to unified-internal-contracts
    status: completed
  - id: implement_tier1_mdps
    content: Implement 10 Tier 1 HFT features in MDPS (trade size percentiles, spread volatility, book pressure, etc.)
    status: completed
  - id: implement_tier1_delta_one
    content: Implement Amihud illiquidity, VPIN, Kyle's lambda in features-delta-one-service
    status: completed
  - id: implement_regime_calculator
    content: Implement HMM and correlation regime calculators in features-cross-instrument-service
    status: completed
  - id: implement_tradfi_vol
    content: Implement TradFi vol surface calculator in features-volatility-service
    status: completed
  - id: implement_external_adapters
    content: Implement 6 external data source adapters (CryptoPanic, LunarCrush, CryptoQuant, DefiLlama, FRED, Yahoo)
    status: completed
  - id: implement_incremental_book
    content: Implement Tardis incremental_book_L2 adapter in market-tick-data-handler
    status: completed
  - id: write_unit_tests
    content: Write unit tests for all new feature calculators
    status: completed
  - id: write_integration_tests
    content: Write integration tests for data flows (MDPS → features-delta-one → features-cross-instrument → ML)
    status: cancelled
  - id: run_schema_validation
    content: Run schema validation for all new outputs
    status: cancelled
  - id: run_quality_gates
    content: Run quality gates for all modified repos and fix errors
    status: cancelled
  - id: update_deployment_configs
    content: Add sharding config for features-cross-instrument-service
    status: completed
  - id: add_cloud_build_trigger
    content: Add Cloud Build trigger for features-cross-instrument-service
    status: completed
  - id: provision_databento_creds
    content: Provision Databento API key in Secret Manager
    status: cancelled
  - id: provision_external_api_keys
    content: Provision external API keys (CryptoPanic, LunarCrush, etc.) in Secret Manager
    status: cancelled
  - id: deploy_services
    content: Deploy features-cross-instrument-service and updated services to Cloud Run
    status: cancelled
  - id: backfill_historical_data
    content: Run batch mode backfill for 2024 data
    status: cancelled
  - id: verify_event_logging
    content: Verify lifecycle events for new service
    status: cancelled
  - id: run_data_completeness_checks
    content: Run DataCompletionChecker for all new datasets
    status: cancelled
  - id: calculate_feature_quality_metrics
    content: Calculate feature statistics (NaN/inf counts, distributions)
    status: cancelled
  - id: live_mode_smoke_test
    content: Start services in live mode and verify PubSub/GCS
    status: cancelled
  - id: update_codex
    content: Update unified-trading-codex with new architecture decisions and patterns
    status: completed
  - id: update_service_readmes
    content: Update README.md for all modified services
    status: completed
  - id: create_migration_guide
    content: Create HFT_FEATURES_MIGRATION_GUIDE.md in unified-trading-pm
    status: completed
isProject: false
---

# HFT Feature Pipeline Integration Plan

## Overview

Add 27 new features/feature groups to the pipeline:

- **Tier 1 (10):** Compute from existing data (MDPS/features-delta-one)
- **Tier 2 (4):** Regime features (new service/calculator)
- **Tier 3 (4):** TradFi vol surfaces (Databento integration)
- **Tier 4 (6):** Cheap/free external data
- **Tier 5 (3):** Incremental book data (Tardis L2)

**Key architectural decisions:**

- All Tier 1 HFT features stay in MDPS (single source of truth for microstructure)
- New `features-cross-instrument-service` for cross-asset calculations (realized vs implied vol, cross-venue spreads)
- Regime features implemented now (HMM, correlation regimes) as part of cross-instrument service
- Full TradFi vol surface implementation (Databento OPRA + CME options)

---

## Phase 1: Documentation & Manifest Updates (Foundation)

### 1.1 Update Workspace Manifest

**File:** `unified-trading-pm/workspace-manifest.json`

**Changes:**

- Add `features-cross-instrument-service` to repositories section:
  - type: "service"
  - arch_tier: "service"
  - merge_level: 6 (same as other features services)
  - dependencies: features-delta-one-service, features-volatility-service, market-data-processing-service, unified-domain-client, unified-trading-services, unified-config-interface, unified-events-interface, unified-feature-calculator-library
  - status: "active"
  - completion_path: "cefi"
- Update `features-volatility-service` dependencies to include Databento data sources (via market-tick-data-handler)
- Update topological order level 6 to include `features-cross-instrument-service`

**Validation:**

- Run `python scripts/validate-manifest.py` (if exists) or manually verify JSON schema
- Ensure no circular dependencies introduced

### 1.2 Update Runtime Topology YAML

**File:** `unified-trading-deployment-v3/configs/runtime-topology.yaml`

**Add service flows:**

```yaml
# Layer 3 → Cross-Instrument: Features → Cross-Instrument Aggregation
- producer: features-delta-one-service
  consumer: features-cross-instrument-service
  data: delta_one_features_for_cross_instrument
  modes:
    batch: { transport: gcs }
    live: { transport: pubsub }

- producer: features-volatility-service
  consumer: features-cross-instrument-service
  data: volatility_features_for_cross_instrument
  modes:
    batch: { transport: gcs }
    live: { transport: pubsub }

- producer: market-data-processing-service
  consumer: features-cross-instrument-service
  data: processed_market_data_multi_venue
  modes:
    batch: { transport: gcs }
    live: { transport: pubsub }

# Cross-Instrument → ML Training
- producer: features-cross-instrument-service
  consumer: ml-training-service
  data: cross_instrument_features
  modes:
    batch: { transport: gcs }

- producer: features-cross-instrument-service
  consumer: ml-inference-service
  data: live_cross_instrument_features
  modes:
    batch: { transport: gcs }
    live: { transport: pubsub }
```

**Add sharding dimensions:**

```yaml
features-cross-instrument-service:
  batch: [category, feature_category, date]
  live: [feature_category]
  topic_template: "features-cross-instrument-{feature_category}"
  notes: >
    Aggregates across venues/instruments. Feature categories: regime (HMM, correlation),
    cross_venue_spread, realized_vs_implied_vol, cross_asset_correlation.
```

**Add to clusters:**

```yaml
clusters:
  features:
    services:
      - features-calendar-service
      - features-delta-one-service
      - features-volatility-service
      - features-onchain-service
      - features-cross-instrument-service  # NEW
```

**Add persistence flow:**

```yaml
persistence_flows:
  - actor: features-cross-instrument-service
    sink: gcs
    dataset: cross_instrument_features
```

**Add to batch_and_live_services:**

```yaml
batch_and_live_services:
  - features-cross-instrument-service
```

### 1.3 Update TOPOLOGY-DAG.md

**File:** `unified-trading-codex/04-architecture/TOPOLOGY-DAG.md`

**Changes:**

1. Add to Layer 3 services in mermaid diagram:

```mermaid
subgraph L3["Layer 3 · Features"]
    FCS["features-calendar-service\nUFC"]
    FDS["features-delta-one-service\nUMI + UDC + UFC"]
    FVS["features-volatility-service\nUMI + UDC + UFC"]
    FOS["features-onchain-service\nUDEI + UDC + UFC"]
    FCIS["features-cross-instrument-service\nUFC + UDC\nAggregates: FDS + FVS + MDPS"]  # NEW
end
```



1. Add dependency edges:

```mermaid
FDS & FVS & MDPS --> FCIS
FCIS --> MLTR & MLIN
UFC --> FCIS
```



1. Update version label: `features-cross-instrument-service v1.0`

### 1.4 Update RUNTIME_DEPLOYMENT_TOPOLOGY_DAG.svg

**File:** `unified-trading-codex/04-architecture/RUNTIME_DEPLOYMENT_TOPOLOGY_DAG.svg`

**Manual SVG edit required** (or regenerate from updated YAML):

- Add `features-cross-instrument-service` node in Layer 3 cluster
- Add edges from FDS, FVS, MDPS → FCIS
- Add edges from FCIS → ML services
- Update legend/key if needed

### 1.5 Update WORKSPACE_MANIFEST_DAG.svg

**File:** `unified-trading-codex/04-architecture/WORKSPACE_MANIFEST_DAG.svg`

**Manual SVG edit required:**

- Add `features-cross-instrument-service` at merge_level 6
- Draw dependency arrows from T0/T1/T2 libraries
- Ensure visual consistency with other features services

### 1.6 Create Feature Specification Documents

**New files to create:**

1. `**market-data-processing-service/docs/HFT_FEATURES_TIER1_ADDITIONS.md`**
  - Document 10 new Tier 1 features (trade size percentiles, spread volatility, book pressure gradient, etc.)
  - Schema definitions for new columns
  - Calculation formulas
  - Data sources (which adapters provide inputs)
2. `**features-cross-instrument-service/docs/FEATURE_SPECIFICATION.md`**
  - Tier 2 regime features (HMM, correlation regimes)
  - Cross-venue spread calculations
  - Realized vs implied vol
  - Cross-asset correlation features
  - Schema definitions
3. `**features-volatility-service/docs/TRADFI_VOL_SURFACES.md`**
  - CBOE equity options (SPY, QQQ, single stocks)
  - CME gold/NG options
  - Vol surface interpolation methods
  - Schema additions
4. `**features-delta-one-service/docs/EXTERNAL_DATA_SOURCES.md`**
  - Tier 4 external data integrations (CryptoPanic, LunarCrush, CryptoQuant, DefiLlama, FRED, Yahoo Finance)
  - API endpoints, rate limits, schemas
  - Feature calculations from external data
5. `**market-tick-data-handler/docs/INCREMENTAL_BOOK_L2.md**`
  - Tardis incremental_book_L2 ingestion
  - Order cancellation rate calculation
  - Iceberg order detection
  - Queue dynamics tracking

### 1.7 Update Cursor Rules (if conflicts exist)

**Check for conflicts:**

- Search `.cursor/rules/` for any rules that might contradict new service architecture
- Verify no rules block cross-service data flows
- Ensure sharding dimension rules accommodate new service

**No conflicts expected** based on current rule set, but validate during implementation.

---

## Phase 2: Infrastructure & Scaffolding (Parallel to Phase 1)

### 2.1 Scaffold features-cross-instrument-service

**Use service setup template:**

```bash
cd /Users/ikennaigboaka/Documents/repos/unified-trading-system-repos
# Copy template from existing features service
cp -r features-delta-one-service features-cross-instrument-service
cd features-cross-instrument-service
```

**Update pyproject.toml:**

- name = "features-cross-instrument-service"
- dependencies: features-delta-one-service, features-volatility-service, market-data-processing-service (via GCS reads, not Python imports)
- Add hmmlearn, ruptures for regime detection

**Create directory structure:**

```
features-cross-instrument-service/
├── features_cross_instrument_service/
│   ├── app/
│   │   ├── calculators/
│   │   │   ├── regime_calculator.py       # HMM, correlation regimes
│   │   │   ├── cross_venue_calculator.py  # Cross-venue spreads
│   │   │   ├── realized_implied_vol.py    # Realized vs implied vol
│   │   │   └── cross_asset_correlation.py # Cross-asset correlation
│   │   ├── engine/
│   │   │   └── cross_instrument_engine.py
│   │   └── cli.py
│   ├── schemas/
│   │   └── output_schemas.py
│   └── tests/
├── docs/
│   ├── ARCHITECTURE.md
│   ├── FEATURE_SPECIFICATION.md
│   ├── DEPENDENCIES.md
│   ├── GCS_PATHS.md
│   ├── CONFIGURATION.md
│   ├── SCHEMA_VALIDATION.md
│   └── TESTING.md
├── scripts/
│   └── quality-gates.sh
└── README.md
```

**Key architectural decisions:**

- Reads from GCS outputs of FDS, FVS, MDPS (no direct Python imports of those services)
- Uses unified-feature-calculator-library for base patterns
- Publishes to PubSub in live mode, writes to GCS in both modes

### 2.2 Add Databento Schemas to api-contracts

**File:** `api-contracts/api_contracts_external/databento/schemas.py`

**Add schemas for:**

- OPRA options data (CBOE equity options)
- CME options data (gold GC, natural gas NG)
- Vol surface interpolation helpers

**Example:**

```python
class DatabentoOptionQuote(BaseModel):
    """OPRA options quote schema."""
    ts_event: int  # nanoseconds
    ts_recv: int
    instrument_id: int
    symbol: str
    underlying: str
    strike: Decimal
    expiration: date
    option_type: Literal["C", "P"]
    bid_price: Decimal
    ask_price: Decimal
    bid_size: int
    ask_size: int
    bid_iv: Decimal | None
    ask_iv: Decimal | None
```

### 2.3 Add External Data Source Schemas to api-contracts

**File:** `api-contracts/api_contracts_external/sentiment/`

**New files:**

- `cryptopanic.py` (CryptoPanic API)
- `lunarcrush.py` (LunarCrush API)
- `cryptoquant.py` (CryptoQuant API)
- `defi_llama.py` (DefiLlama API - may already exist, extend if needed)
- `fred.py` (FRED API - may already exist, extend if needed)
- `yahoo_finance.py` (Yahoo Finance API)

**Each schema includes:**

- Request/response models
- Rate limit constants
- API key configuration (via Secret Manager)

### 2.4 Update market-tick-data-handler for New Data Types

**Add adapters for:**

1. **Databento OPRA adapter** (`market_tick_data_handler/app/adapters/tradfi/databento_opra_adapter.py`)
  - Ingest CBOE equity options quotes
  - Normalize to CanonicalOptionQuote (new schema in unified-internal-contracts)
2. **Databento CME adapter** (`market_tick_data_handler/app/adapters/tradfi/databento_cme_adapter.py`)
  - Ingest CME gold/NG options
  - Normalize to CanonicalOptionQuote
3. **Tardis incremental_book_L2 adapter** (`market_tick_data_handler/app/adapters/cefi/tardis_incremental_book_adapter.py`)
  - Ingest order-level book updates
  - Track order additions, cancellations, modifications
  - Normalize to CanonicalBookUpdate (new schema)

**Add to CLI:**

- New data_type flags: `--data-type opra_options`, `--data-type cme_options`, `--data-type incremental_book_l2`

### 2.5 Add New Schemas to unified-internal-contracts

**File:** `unified-internal-contracts/unified_internal_contracts/market_data/`

**New schemas:**

1. `**option_quote.py`:**

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

1. `**book_update.py`:**

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

1. `**cross_instrument_features.py`:**

```python
   class CrossInstrumentFeatures(BaseModel):
       timestamp: datetime
       feature_category: Literal["regime", "cross_venue_spread", "realized_vs_implied", "cross_asset_correlation"]
       features: dict[str, float]
       metadata: dict[str, Any]


```

---

## Phase 3: Feature Implementation (Parallel Workstreams)

### Workstream A: Tier 1 HFT Features in MDPS

**Files to modify:**

1. `**market-data-processing-service/market_data_processing_service/app/adapters/cefi/trades_adapter.py`**
  **Add trade size percentile calculations:**

```python
   def calculate_trade_size_percentiles(sizes: np.ndarray) -> dict[str, float]:
       """Calculate p10, p50, p90, p99 of trade sizes."""
       return {
           "trade_size_p10": np.percentile(sizes, 10),
           "trade_size_p50": np.percentile(sizes, 50),
           "trade_size_p90": np.percentile(sizes, 90),
           "trade_size_p99": np.percentile(sizes, 99),
       }


```

   **Add whale trade detection:**

```python
   def detect_whale_trades(sizes: np.ndarray, window: int = 100) -> dict[str, float]:
       """Detect trades > p99 of rolling size distribution."""
       rolling_p99 = pd.Series(sizes).rolling(window).quantile(0.99)
       whale_trades = sizes > rolling_p99
       return {
           "whale_trade_count": whale_trades.sum(),
           "whale_trade_volume": sizes[whale_trades].sum(),
       }


```

1. `**market-data-processing-service/market_data_processing_service/app/adapters/cefi/book_snapshot_adapter.py**`
  **Add spread volatility (std of 15 intra-candle spread samples):**

```python
   def calculate_spread_volatility(spreads: np.ndarray) -> float:
       """Calculate std of spread samples within candle."""
       return np.std(spreads)


```

   **Add book pressure gradient (volume slope across 5 levels):**

```python
   def calculate_book_pressure_gradient(bid_volumes: np.ndarray, ask_volumes: np.ndarray) -> dict[str, float]:
       """Calculate volume slope across 5 levels."""
       bid_slope = np.polyfit(range(5), bid_volumes, 1)[0]
       ask_slope = np.polyfit(range(5), ask_volumes, 1)[0]
       return {
           "bid_pressure_gradient": bid_slope,
           "ask_pressure_gradient": ask_slope,
           "net_pressure_gradient": bid_slope - ask_slope,
       }


```

   **Add effective-to-quoted spread ratio:**

```python
   def calculate_effective_to_quoted_ratio(effective_spread: float, quoted_spread: float) -> float:
       """Ratio of effective spread to quoted spread."""
       return effective_spread / quoted_spread if quoted_spread > 0 else 0.0


```

1. `**market-data-processing-service/market_data_processing_service/app/adapters/cefi/liquidations_adapter.py**`
  **Add liquidation cascade intensity:**

```python
   def calculate_liquidation_cascade_metrics(liquidations: list[CanonicalLiquidation]) -> dict[str, float]:
       """Calculate inter-liquidation time, acceleration, clustering."""
       timestamps = [liq.timestamp for liq in liquidations]
       inter_times = np.diff([t.timestamp() for t in timestamps])

       return {
           "liquidation_inter_time_mean": np.mean(inter_times) if len(inter_times) > 0 else 0.0,
           "liquidation_inter_time_std": np.std(inter_times) if len(inter_times) > 0 else 0.0,
           "liquidation_acceleration": np.diff(inter_times).mean() if len(inter_times) > 1 else 0.0,
           "liquidation_clustering_score": 1.0 / np.mean(inter_times) if len(inter_times) > 0 and np.mean(inter_times) > 0 else 0.0,
       }


```

1. **Add new adapter: `volume_clock_adapter.py`**
  **Volume clock features (time to fill N contracts):**

```python
   class VolumeClock:
       """Track time to fill volume thresholds."""

       def calculate_volume_clock_features(self, trades: list[CanonicalTrade], thresholds: list[float]) -> dict[str, float]:
           """Calculate time to fill N contracts."""
           cumulative_volume = np.cumsum([t.size for t in trades])
           timestamps = [t.timestamp for t in trades]

           features = {}
           for threshold in thresholds:
               idx = np.searchsorted(cumulative_volume, threshold)
               if idx < len(timestamps):
                   time_to_fill = (timestamps[idx] - timestamps[0]).total_seconds()
                   features[f"volume_clock_{int(threshold)}"] = time_to_fill
               else:
                   features[f"volume_clock_{int(threshold)}"] = None

           return features


```

1. **Update output schema:**
  **File:** `market-data-processing-service/schemas/output_schemas.py`
   Add new columns:
  - `trade_size_p10`, `trade_size_p50`, `trade_size_p90`, `trade_size_p99`
  - `spread_volatility_15s`
  - `bid_pressure_gradient`, `ask_pressure_gradient`, `net_pressure_gradient`
  - `whale_trade_count`, `whale_trade_volume`
  - `effective_to_quoted_spread_ratio`
  - `liquidation_inter_time_mean`, `liquidation_inter_time_std`, `liquidation_acceleration`, `liquidation_clustering_score`
  - `volume_clock_1000`, `volume_clock_5000`, `volume_clock_10000` (configurable thresholds)

### Workstream B: Tier 1 Features in features-delta-one-service

**Files to modify:**

1. `**features-delta-one-service/features_delta_one_service/app/calculators/microstructure.py`**
  **Add Amihud illiquidity:**

```python
   def calculate_amihud_illiquidity(returns: np.ndarray, dollar_volume: np.ndarray, window: int = 20) -> np.ndarray:
       """|return| / dollar volume (rolling)."""
       abs_returns = np.abs(returns)
       illiquidity = abs_returns / dollar_volume
       return pd.Series(illiquidity).rolling(window).mean().values


```

   **Add VPIN (volume-sync'd probability of informed trading):**

```python
   def calculate_vpin(trades: pd.DataFrame, volume_bucket_size: float, n_buckets: int = 50) -> float:
       """VPIN calculation using volume buckets."""
       # Classify trades by side (buy/sell)
       trades["bucket"] = (trades["cumulative_volume"] // volume_bucket_size).astype(int)

       # Aggregate by bucket
       bucket_agg = trades.groupby("bucket").agg({
           "buy_volume": "sum",
           "sell_volume": "sum",
       })

       # VPIN = average absolute order imbalance over n_buckets
       bucket_agg["imbalance"] = (bucket_agg["buy_volume"] - bucket_agg["sell_volume"]).abs()
       bucket_agg["total_volume"] = bucket_agg["buy_volume"] + bucket_agg["sell_volume"]
       bucket_agg["vpin_component"] = bucket_agg["imbalance"] / bucket_agg["total_volume"]

       return bucket_agg["vpin_component"].tail(n_buckets).mean()


```

   **Add Kyle's lambda (rolling regression ΔP on signed volume):**

```python
   def calculate_kyles_lambda(price_changes: np.ndarray, signed_volumes: np.ndarray, window: int = 100) -> np.ndarray:
       """Rolling regression of price change on signed volume."""
       from scipy import stats

       lambdas = []
       for i in range(window, len(price_changes)):
           window_prices = price_changes[i-window:i]
           window_volumes = signed_volumes[i-window:i]
           slope, _, _, _, _ = stats.linregress(window_volumes, window_prices)
           lambdas.append(slope)

       return np.array([np.nan] * window + lambdas)


```

1. **Update output schema:**
  **File:** `features-delta-one-service/schemas/output_schemas.py`
   Add new columns:
  - `amihud_illiquidity_{window}` (multiple windows: 20, 50, 100)
  - `vpin_{bucket_size}` (multiple bucket sizes)
  - `kyles_lambda_{window}` (multiple windows: 50, 100, 200)

### Workstream C: Tier 2 Regime Features (features-cross-instrument-service)

**File:** `features-cross-instrument-service/features_cross_instrument_service/app/calculators/regime_calculator.py`

**Implement HMM volatility regime:**

```python
from hmmlearn import hmm
import numpy as np

class RegimeCalculator:
    def __init__(self, n_states: int = 3):
        self.n_states = n_states
        self.model = hmm.GaussianHMM(n_components=n_states, covariance_type="full")

    def fit_hmm_volatility_regime(self, returns: np.ndarray) -> dict[str, Any]:
        """Fit HMM on returns to detect volatility regimes."""
        returns_reshaped = returns.reshape(-1, 1)
        self.model.fit(returns_reshaped)

        states = self.model.predict(returns_reshaped)
        transition_matrix = self.model.transitionmat_

        return {
            "current_regime": int(states[-1]),
            "regime_persistence": self._calculate_persistence(states),
            "transition_probabilities": transition_matrix[states[-1]].tolist(),
            "regime_means": self.model.means_.flatten().tolist(),
            "regime_variances": np.diag(self.model.covars_[0]).tolist(),
        }

    def _calculate_persistence(self, states: np.ndarray, window: int = 100) -> float:
        """Average time in current regime."""
        recent_states = states[-window:]
        current_state = states[-1]
        regime_durations = []

        current_duration = 0
        for state in reversed(recent_states):
            if state == current_state:
                current_duration += 1
            else:
                if current_duration > 0:
                    regime_durations.append(current_duration)
                current_duration = 0

        return np.mean(regime_durations) if regime_durations else 0.0
```

**Implement correlation regime:**

```python
from ruptures import Pelt

class CorrelationRegimeCalculator:
    def detect_correlation_regime_changes(self, returns_matrix: np.ndarray, penalty: float = 10.0) -> dict[str, Any]:
        """Detect correlation regime changes using changepoint detection."""
        # Calculate rolling correlation
        rolling_corr = self._calculate_rolling_correlation(returns_matrix)

        # Detect changepoints
        algo = Pelt(model="rbf").fit(rolling_corr)
        changepoints = algo.predict(pen=penalty)

        # Current regime
        current_regime_start = changepoints[-2] if len(changepoints) > 1 else 0
        current_regime_corr = rolling_corr[current_regime_start:].mean()

        return {
            "current_correlation": float(current_regime_corr),
            "changepoints": changepoints,
            "regime_duration": len(rolling_corr) - current_regime_start,
            "regime_stability": self._calculate_stability(rolling_corr[current_regime_start:]),
        }

    def _calculate_rolling_correlation(self, returns_matrix: np.ndarray, window: int = 50) -> np.ndarray:
        """Calculate rolling pairwise correlation."""
        correlations = []
        for i in range(window, len(returns_matrix)):
            window_data = returns_matrix[i-window:i]
            corr_matrix = np.corrcoef(window_data.T)
            # Average off-diagonal correlations
            mask = ~np.eye(corr_matrix.shape[0], dtype=bool)
            avg_corr = corr_matrix[mask].mean()
            correlations.append(avg_corr)

        return np.array(correlations)

    def _calculate_stability(self, correlations: np.ndarray) -> float:
        """Stability = inverse of correlation volatility."""
        return 1.0 / (np.std(correlations) + 1e-8)
```

### Workstream D: Tier 3 TradFi Vol Surfaces

**File:** `features-volatility-service/features_volatility_service/app/calculators/tradfi_vol_surface.py`

**Implement vol surface interpolation:**

```python
from scipy.interpolate import griddata
import numpy as np

class TradFiVolSurfaceCalculator:
    def calculate_vol_surface_features(self, option_quotes: list[CanonicalOptionQuote], underlying_price: float) -> dict[str, float]:
        """Calculate vol surface features from CBOE/CME options."""
        # Extract strikes, expiries, IVs
        strikes = np.array([q.strike for q in option_quotes])
        expiries = np.array([(q.expiration - date.today()).days / 365.0 for q in option_quotes])
        ivs = np.array([q.mid_iv for q in option_quotes if q.mid_iv is not None])

        # Moneyness
        moneyness = strikes / underlying_price

        # ATM IV (interpolate at moneyness=1.0, expiry=30d)
        atm_iv = self._interpolate_iv(moneyness, expiries, ivs, target_moneyness=1.0, target_expiry=30/365)

        # 25-delta skew (call - put IV at 25-delta)
        skew_25d = self._calculate_skew(option_quotes, delta=0.25)

        # Term structure slope (30d vs 90d ATM IV)
        atm_30d = self._interpolate_iv(moneyness, expiries, ivs, target_moneyness=1.0, target_expiry=30/365)
        atm_90d = self._interpolate_iv(moneyness, expiries, ivs, target_moneyness=1.0, target_expiry=90/365)
        term_structure_slope = (atm_90d - atm_30d) / (60/365)

        return {
            "atm_iv_30d": atm_iv,
            "skew_25d": skew_25d,
            "term_structure_slope": term_structure_slope,
            "vol_surface_convexity": self._calculate_convexity(moneyness, ivs),
        }

    def _interpolate_iv(self, moneyness: np.ndarray, expiries: np.ndarray, ivs: np.ndarray, target_moneyness: float, target_expiry: float) -> float:
        """Interpolate IV at target moneyness and expiry."""
        points = np.column_stack([moneyness, expiries])
        target = np.array([[target_moneyness, target_expiry]])
        interpolated = griddata(points, ivs, target, method="cubic")
        return float(interpolated[0])

    def _calculate_skew(self, option_quotes: list[CanonicalOptionQuote], delta: float) -> float:
        """Calculate put-call skew at given delta."""
        # Filter to ~25-delta options (approximate by moneyness)
        # This is simplified; production would use actual delta calculation
        calls = [q for q in option_quotes if q.option_type == "call" and 0.9 < q.strike / q.underlying_price < 1.1]
        puts = [q for q in option_quotes if q.option_type == "put" and 0.9 < q.strike / q.underlying_price < 1.1]

        if calls and puts:
            call_iv = np.mean([q.mid_iv for q in calls if q.mid_iv])
            put_iv = np.mean([q.mid_iv for q in puts if q.mid_iv])
            return call_iv - put_iv

        return 0.0

    def _calculate_convexity(self, moneyness: np.ndarray, ivs: np.ndarray) -> float:
        """Calculate vol surface convexity (butterfly spread)."""
        # Fit quadratic to moneyness-IV relationship
        coeffs = np.polyfit(moneyness, ivs, 2)
        convexity = coeffs[0]  # Second-order coefficient
        return float(convexity)
```

**Update market-tick-data-handler to ingest Databento options:**

**File:** `market-tick-data-handler/market_tick_data_handler/app/adapters/tradfi/databento_opra_adapter.py`

```python
class DatabentoOPRAAdapter:
    """Ingest CBOE equity options via Databento OPRA feed."""

    async def fetch_options_quotes(self, symbols: list[str], start_date: date, end_date: date) -> list[CanonicalOptionQuote]:
        """Fetch options quotes from Databento."""
        # Use Databento client (already in api-contracts)
        # Normalize to CanonicalOptionQuote
        pass
```

### Workstream E: Tier 4 External Data Sources

**Add adapters to features-delta-one-service or features-calendar-service:**

1. **CryptoPanic sentiment** (`features-calendar-service/app/adapters/cryptopanic_adapter.py`)
2. **LunarCrush sentiment** (`features-calendar-service/app/adapters/lunarcrush_adapter.py`)
3. **CryptoQuant on-chain** (`features-onchain-service/app/adapters/cryptoquant_adapter.py`)
4. **DefiLlama stablecoin dominance** (`features-onchain-service/app/adapters/defillama_adapter.py`)
5. **FRED treasury yields** (`features-calendar-service/app/adapters/fred_adapter.py`)
6. **Yahoo Finance DXY** (`features-calendar-service/app/adapters/yahoo_finance_adapter.py`)

**Each adapter:**

- Implements rate limiting (use `@with_retry` from UTS)
- Stores API key in Secret Manager
- Normalizes to internal schema
- Writes to GCS

**Add funding rate cross-venue spread to features-delta-one-service:**

**File:** `features-delta-one-service/features_delta_one_service/app/calculators/funding_rate.py`

```python
def calculate_cross_venue_funding_spread(funding_rates: dict[str, float]) -> dict[str, float]:
    """Calculate funding rate spread across venues."""
    venues = list(funding_rates.keys())
    spreads = {}

    for i, venue1 in enumerate(venues):
        for venue2 in venues[i+1:]:
            spread_key = f"funding_spread_{venue1}_{venue2}"
            spreads[spread_key] = funding_rates[venue1] - funding_rates[venue2]

    return spreads
```

### Workstream F: Tier 5 Incremental Book Features

**File:** `market-data-processing-service/market_data_processing_service/app/adapters/cefi/incremental_book_adapter.py`

**New adapter for Tardis incremental_book_L2:**

```python
class IncrementalBookAdapter:
    """Process incremental book updates to calculate order-level features."""

    def calculate_order_cancellation_rate(self, updates: list[CanonicalBookUpdate], window_seconds: int = 60) -> float:
        """Calculate order cancellation rate."""
        recent_updates = [u for u in updates if (datetime.now(timezone.utc) - u.timestamp).total_seconds() <= window_seconds]

        total_orders = len([u for u in recent_updates if u.update_type in ["add", "modify"]])
        cancelled_orders = len([u for u in recent_updates if u.update_type == "cancel"])

        return cancelled_orders / total_orders if total_orders > 0 else 0.0

    def detect_iceberg_orders(self, updates: list[CanonicalBookUpdate]) -> dict[str, int]:
        """Detect iceberg orders (repeated adds at same price)."""
        # Group by price level
        price_groups = {}
        for update in updates:
            if update.update_type == "add":
                key = (update.side, update.price)
                price_groups.setdefault(key, []).append(update)

        # Detect icebergs (>5 adds at same price within 1 minute)
        iceberg_count = 0
        for (side, price), adds in price_groups.items():
            if len(adds) > 5:
                time_span = (adds[-1].timestamp - adds[0].timestamp).total_seconds()
                if time_span < 60:
                    iceberg_count += 1

        return {"iceberg_order_count": iceberg_count}

    def calculate_order_arrival_rate_by_level(self, updates: list[CanonicalBookUpdate], n_levels: int = 5) -> dict[str, float]:
        """Calculate order arrival rate by book level."""
        # Approximate level by price distance from mid
        # Production would track actual level positions
        arrival_rates = {}

        for level in range(n_levels):
            level_updates = [u for u in updates if self._get_level(u) == level]
            arrival_rate = len(level_updates) / 60.0  # per minute
            arrival_rates[f"arrival_rate_level_{level}"] = arrival_rate

        return arrival_rates

    def _get_level(self, update: CanonicalBookUpdate) -> int:
        """Approximate book level (0=top of book)."""
        # Simplified; production would track actual book state
        return 0  # Placeholder
```

**Update output schema to include incremental book features.**

---

## Phase 4: Testing & Validation

### 4.1 Unit Tests

**For each new feature calculator:**

- Test with synthetic data
- Test edge cases (empty data, NaN handling, division by zero)
- Test output schema compliance

**Example test structure:**

```python
# features-cross-instrument-service/tests/unit/test_regime_calculator.py
def test_hmm_volatility_regime():
    calculator = RegimeCalculator(n_states=3)
    returns = np.random.randn(1000) * 0.02  # Synthetic returns
    result = calculator.fit_hmm_volatility_regime(returns)

    assert "current_regime" in result
    assert 0 <= result["current_regime"] < 3
    assert "regime_persistence" in result
    assert result["regime_persistence"] >= 0
```

### 4.2 Integration Tests

**Test data flows:**

- MDPS → features-delta-one → features-cross-instrument → ML services
- MDPS → features-volatility → features-cross-instrument
- market-tick-data-handler → MDPS (new data types: OPRA, CME options, incremental_book_L2)

**Use GCS sandbox:**

- Write test data to `gs://test-project/test-data/`
- Run services in batch mode with `--date 2024-01-01`
- Verify output schemas and data completeness

### 4.3 Schema Validation

**Run schema validation for all new outputs:**

```bash
cd market-data-processing-service
python -m market_data_processing_service.app.validators.schema_validator --date 2024-01-01

cd features-cross-instrument-service
python -m features_cross_instrument_service.app.validators.schema_validator --date 2024-01-01
```

**Verify:**

- All new columns present
- No NaN/null where not expected
- Data types correct (Decimal for prices, float for features)

### 4.4 Quality Gates

**Run quality gates for all modified repos:**

```bash
cd /Users/ikennaigboaka/Documents/repos/unified-trading-system-repos
source .venv-workspace/bin/activate

# Modified services
for repo in market-data-processing-service features-delta-one-service features-volatility-service features-cross-instrument-service market-tick-data-handler; do
    cd $repo
    bash scripts/quality-gates.sh --no-fix
    cd ..
done

# Modified libraries
for repo in api-contracts unified-internal-contracts; do
    cd $repo
    bash scripts/quality-gates.sh --no-fix
    cd ..
done
```

**Fix any linter/type errors before proceeding.**

---

## Phase 5: Deployment & Rollout

### 5.1 Update Deployment Configs

**File:** `unified-trading-deployment-v3/configs/sharding_config.yaml`

**Add sharding config for features-cross-instrument-service:**

```yaml
features-cross-instrument-service:
  batch:
    dimensions: [category, feature_category, date]
    category_values: [cefi, defi]
    feature_category_values: [regime, cross_venue_spread, realized_vs_implied, cross_asset_correlation]
  live:
    dimensions: [feature_category]
    feature_category_values: [regime, cross_venue_spread, realized_vs_implied, cross_asset_correlation]
```

### 5.2 Update Cloud Build Triggers

**Add Cloud Build trigger for features-cross-instrument-service:**

```yaml
# .github/workflows/features-cross-instrument-service-build.yml
name: features-cross-instrument-service-build
on:
  push:
    branches: [main]
    paths:
      - 'features-cross-instrument-service/**'
```

### 5.3 Provision Databento Credentials

**Add to Secret Manager:**

```bash
gcloud secrets create databento-api-key --data-file=- <<EOF
YOUR_DATABENTO_API_KEY
EOF
```

**Update credentials-registry.yaml:**

```yaml
databento:
  api_key:
    secret_name: databento-api-key
    project_id: central-element-323112
```

### 5.4 Provision External Data API Keys

**Add to Secret Manager:**

```bash
gcloud secrets create cryptopanic-api-key --data-file=- <<EOF
YOUR_CRYPTOPANIC_API_KEY
EOF

gcloud secrets create lunarcrush-api-key --data-file=- <<EOF
YOUR_LUNARCRUSH_API_KEY
EOF

# Repeat for CryptoQuant, etc.
```

### 5.5 Deploy Services

**Use deployment-api or manual Cloud Run deployment:**

```bash
# Deploy features-cross-instrument-service
cd features-cross-instrument-service
gcloud run deploy features-cross-instrument-service \
  --source . \
  --region us-central1 \
  --memory 4Gi \
  --cpu 2 \
  --timeout 3600 \
  --set-env-vars GCP_PROJECT_ID=central-element-323112

# Update market-tick-data-handler
cd ../market-tick-data-handler
gcloud run deploy market-tick-data-handler \
  --source . \
  --region us-central1 \
  --memory 8Gi \
  --cpu 4 \
  --timeout 3600
```

### 5.6 Backfill Historical Data

**Run batch mode for historical dates:**

```bash
# Backfill MDPS with new Tier 1 features
cd market-data-processing-service
python -m market_data_processing_service.cli batch \
  --start-date 2024-01-01 \
  --end-date 2024-12-31 \
  --venue binance \
  --category cefi

# Backfill features-cross-instrument
cd ../features-cross-instrument-service
python -m features_cross_instrument_service.cli batch \
  --start-date 2024-01-01 \
  --end-date 2024-12-31 \
  --category cefi
```

---

## Phase 6: Monitoring & Validation

### 6.1 Event Logging

**Verify lifecycle events for new service:**

```bash
gsutil ls gs://central-element-323112-events/features-cross-instrument-service/
```

**Check for:**

- STARTED, VALIDATION_STARTED, VALIDATION_COMPLETED
- PROCESSING_STARTED, PROCESSING_COMPLETED
- PERSISTENCE_STARTED, PERSISTENCE_COMPLETED
- STOPPED

### 6.2 Data Completeness Checks

**Use DataCompletionChecker from UDC:**

```python
from unified_domain_client import DataCompletionChecker

checker = DataCompletionChecker()
result = checker.check_dataset_completeness(
    dataset="cross_instrument_features",
    start_date=date(2024, 1, 1),
    end_date=date(2024, 12, 31),
    expected_frequency="daily",
)

print(f"Completeness: {result.completeness_pct}%")
print(f"Missing dates: {result.missing_dates}")
```

### 6.3 Feature Quality Metrics

**Calculate feature statistics:**

```python
import pandas as pd

# Load features
df = pd.read_parquet("gs://central-element-323112-features/cross_instrument_features/date=2024-12-01/*.parquet")

# Check for NaN/inf
print(f"NaN count: {df.isna().sum().sum()}")
print(f"Inf count: {np.isinf(df.select_dtypes(include=[np.number])).sum().sum()}")

# Feature distributions
print(df.describe())
```

### 6.4 Live Mode Smoke Test

**Start services in live mode:**

```bash
# Start features-cross-instrument-service in live mode
cd features-cross-instrument-service
python -m features_cross_instrument_service.cli live \
  --category cefi \
  --feature-category regime
```

**Monitor PubSub topics:**

```bash
gcloud pubsub subscriptions pull features-cross-instrument-regime-cefi-sub --limit=10
```

**Verify:**

- Messages published to PubSub
- GCS persistence happening in parallel
- No errors in Cloud Logging

---

## Phase 7: Documentation Finalization

### 7.1 Update Codex

**Files to update:**

1. `**unified-trading-codex/02-data/feature-pipeline-architecture.md`**
  - Add section on cross-instrument features
  - Document new sharding dimensions
  - Add data flow diagrams
2. `**unified-trading-codex/04-architecture/RUNTIME_TOPOLOGY_DECISIONS.md`**
  - Document decision to create features-cross-instrument-service
  - Rationale for keeping Tier 1 features in MDPS
  - Regime feature implementation approach
3. `**unified-trading-codex/06-coding-standards/feature-calculator-standards.md`**
  - Add examples from new calculators
  - Document external data source integration patterns

### 7.2 Update Service READMEs

**For each modified service:**

- Update README.md with new features
- Add examples of new CLI flags
- Document new configuration options

### 7.3 Create Migration Guide

**File:** `unified-trading-pm/plans/ai/HFT_FEATURES_MIGRATION_GUIDE.md`

**Contents:**

- Summary of 27 new features
- Breaking changes (if any)
- Schema changes
- Backfill instructions
- Monitoring checklist

---

## Success Criteria

### Phase 1-2 (Documentation & Scaffolding)

- Workspace manifest updated and validated
- Runtime topology YAML updated
- All DAG diagrams updated (TOPOLOGY-DAG.md, SVGs)
- features-cross-instrument-service scaffolded
- All new schemas added to api-contracts and unified-internal-contracts

### Phase 3 (Implementation)

- All 10 Tier 1 features implemented in MDPS
- VPIN, Kyle's lambda, Amihud illiquidity implemented in features-delta-one
- Regime calculator (HMM, correlation) implemented in features-cross-instrument
- TradFi vol surface calculator implemented in features-volatility
- 6 external data source adapters implemented
- Incremental book adapter implemented in MDPS

### Phase 4 (Testing)

- All unit tests passing
- Integration tests passing (GCS sandbox)
- Schema validation passing
- Quality gates passing for all modified repos

### Phase 5 (Deployment)

- features-cross-instrument-service deployed to Cloud Run
- Databento credentials provisioned
- External API keys provisioned
- Historical data backfilled

### Phase 6 (Monitoring)

- Lifecycle events logging correctly
- Data completeness checks passing
- Feature quality metrics within expected ranges
- Live mode smoke test successful

### Phase 7 (Documentation)

- Codex updated
- Service READMEs updated
- Migration guide created

---

## Estimated Effort

- **Phase 1-2 (Documentation & Scaffolding):** 2-3 days
- **Phase 3 (Implementation):** 10-14 days (parallel workstreams)
- **Phase 4 (Testing):** 3-4 days
- **Phase 5 (Deployment):** 2-3 days
- **Phase 6 (Monitoring):** 1-2 days
- **Phase 7 (Documentation):** 1-2 days

**Total:** ~20-28 days (4-6 weeks with parallel execution)

---

## Dependencies & Blockers

**External dependencies:**

- Databento subscription approval (~$100-500/mo)
- External API keys (CryptoPanic, LunarCrush, CryptoQuant)

**Internal dependencies:**

- features-delta-one-service must be stable before features-cross-instrument can consume its outputs
- market-tick-data-handler must support new data types before downstream services can process them

**No circular dependencies** introduced by this plan.

---

## Rollback Plan

**If issues arise:**

1. **Revert manifest changes:**

```bash
   cd unified-trading-pm
   git revert <commit-hash>


```

1. **Disable features-cross-instrument-service:**

```bash
   gcloud run services update features-cross-instrument-service --no-traffic


```

1. **Revert MDPS schema changes:**
  - Deploy previous version of MDPS
  - Downstream services continue using old schema
2. **GCS data is immutable** — no rollback needed for persistence layer

---

## Post-Implementation Tasks

1. **Train ML models on new features** (separate epic)
2. **Validate alpha contribution** via backtest (separate epic)
3. **Optimize feature calculation performance** (if needed)
4. **Add more external data sources** (Tier 4 can be extended incrementally)
5. **Implement cross-venue arbitrage signals** (uses cross-venue spread features)

---

## Notes

- This plan integrates seamlessly with existing consolidated_remaining_work.plan.md
- Placement: Insert after "Phase 2: CI/CD & Quality Gates" and before "Phase 4: Testing Infrastructure"
- No conflicts with existing DAG/manifest work
- Parallelizable with other feature work (e.g., sports betting features are separate vertical)
