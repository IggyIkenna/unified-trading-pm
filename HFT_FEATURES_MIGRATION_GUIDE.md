# HFT Features Migration Guide

**Date:** 2026-02-28  
**Version:** 1.0  
**Status:** Implementation Complete (Local, Not Deployed)

## Summary

Added 27 new HFT/microstructure features across 5 tiers to the feature engineering pipeline.

---

## What Changed

### New Service
- **features-cross-instrument-service** - Aggregates cross-venue, cross-instrument features (regime detection, realized vs implied vol, cross-venue spreads)

### Modified Services
- **market-data-processing-service** - 10 new Tier 1 HFT features
- **features-delta-one-service** - 4 advanced microstructure features (VPIN, Kyle's lambda, Amihud, funding spreads)
- **features-volatility-service** - TradFi vol surface calculator (CBOE/CME options)
- **market-tick-data-handler** - Databento options ingestion, Tardis incremental book L2
- **features-calendar-service** - 4 external data adapters (CryptoPanic, LunarCrush, FRED, Yahoo)
- **features-onchain-service** - 2 external data adapters (CryptoQuant, DefiLlama)

### New Schemas
- **api-contracts**: Databento options, external data sources (sentiment, macro, onchain)
- **unified-internal-contracts**: CanonicalOptionQuote, CanonicalBookUpdate, CrossInstrumentFeatures

---

## Feature Breakdown

### Tier 1: Compute from Existing Data (10 features)

**market-data-processing-service:**
1. Trade size distribution (p10/p50/p90/p99 per candle)
2. Spread volatility (std of 15 intra-candle spread samples)
3. Book pressure gradient (volume slope across 5 levels)
4. Whale trade detection (trades > p99 rolling size)
5. Effective-to-quoted spread ratio
6. Volume clock features (time to fill N contracts)
7. Liquidation cascade intensity (inter-time, acceleration, clustering)

**features-delta-one-service:**
8. Amihud illiquidity (|return| / dollar volume)
9. VPIN (volume-sync'd probability of informed trading)
10. Kyle's lambda (rolling regression ΔP on signed volume)
11. Funding rate cross-venue spread (Binance vs OKX/Bybit/Hyperliquid)

### Tier 2: Regime Features (4 features)

**features-cross-instrument-service:**
12. HMM volatility regime (2-3 state Gaussian HMM on returns)
13. Correlation regime (rolling cross-asset correlation + changepoint detection)
14. Regime transition probability (current state → next state likelihood)
15. Regime persistence (time-in-current-regime, avg regime duration)

### Tier 3: TradFi Vol Surfaces (4 features)

**features-volatility-service:**
16. CBOE equity vol surfaces (SPY, QQQ, single stocks: ATM IV, skew, term structure)
17. CME gold options vol surface (GC)
18. CME natural gas options vol surface (NG)
19. Cross-asset vol correlation (crypto IV vs VIX, gold IV vs equity IV)

### Tier 4: External Data Sources (6 features)

**features-calendar-service:**
20. Crypto sentiment score (CryptoPanic API)
21. Social sentiment (LunarCrush API)
22. Treasury yield curve slope (FRED API: 10Y-2Y, 10Y-3M)
23. DXY momentum (Yahoo Finance)

**features-onchain-service:**
24. Exchange inflow/outflow (CryptoQuant API)
25. Stablecoin dominance rate-of-change (DefiLlama API)

### Tier 5: Incremental Book Data (3 features)

**market-tick-data-handler:**
26. Order cancellation rate (Tardis incremental_book_L2)
27. Iceberg order detection (hidden liquidity)
28. Order arrival rate by level (queue dynamics)

---

## Schema Changes

### market-data-processing-service Output Schema

**New columns:**
- `trade_size_p10`, `trade_size_p50`, `trade_size_p90`, `trade_size_p99`
- `whale_trade_count`, `whale_trade_volume`
- `volume_clock_mean_seconds`, `volume_clock_std_seconds`
- `spread_volatility`
- `book_pressure_gradient`
- `effective_to_quoted_spread_ratio`
- `liquidation_cascade_event_count`, `liquidation_cascade_total_volume`, `liquidation_cascade_max_cluster_size`

### features-delta-one-service Output Schema

**New columns:**
- `amihud_illiquidity`, `amihud_illiquidity_ma_{20,50,100}`, `amihud_illiquidity_std_{20,50,100}`
- `vpin`, `vpin_ma_{20,50}`
- `kyles_lambda_{50,100,200}`
- `funding_spread_binance_{venue}`, `funding_spread_binance_{venue}_ma_{8,24,48}`, `funding_spread_binance_{venue}_std_{8,24,48}`

### features-cross-instrument-service Output Schema

**New dataset:** `cross_instrument_features`

**Columns:**
- `timestamp`, `timestamp_out`
- `feature_category` (regime | cross_venue_spread | realized_vs_implied | cross_asset_correlation)
- `base_asset` (e.g., BTC, ETH)
- `representative_venue` (BINANCE-FUTURES)
- Feature columns (dynamic based on category)

---

## Configuration Changes

### New Dependencies

**features-cross-instrument-service:**
- `hmmlearn>=0.3.0` - HMM regime detection
- `ruptures>=1.1.0` - Changepoint detection
- `scipy>=1.11.0` - Statistical functions

**features-volatility-service:**
- `scipy>=1.11.0` - Vol surface interpolation

### API Keys Required (Secret Manager)

**Databento:**
- `databento-api-key` - OPRA + CME options data (~$100-500/mo)

**External APIs:**
- `cryptopanic-api-key` - Crypto sentiment (free tier: 5 req/min)
- `lunarcrush-api-key` - Social sentiment (free tier: 50 req/day)
- `cryptoquant-api-key` - Exchange flow (free tier or $29/mo)
- `fred-api-key` - Treasury yields (free)
- No key required: DefiLlama, Yahoo Finance

---

## Deployment Changes

### New PubSub Topics

```bash
# features-cross-instrument-service
gcloud pubsub topics create features-cross-instrument-regime
gcloud pubsub topics create features-cross-instrument-cross_venue_spread
gcloud pubsub topics create features-cross-instrument-realized_vs_implied
gcloud pubsub topics create features-cross-instrument-cross_asset_correlation
```

### New GCS Paths

```
gs://{bucket}/cross_instrument_features/
  feature_category=regime/
    date=YYYY-MM-DD/
      *.parquet
  feature_category=cross_venue_spread/
    date=YYYY-MM-DD/
      *.parquet
  feature_category=realized_vs_implied/
    date=YYYY-MM-DD/
      *.parquet
  feature_category=cross_asset_correlation/
    date=YYYY-MM-DD/
      *.parquet
```

### Sharding Config

**Added to `unified-trading-deployment-v3/configs/sharding_config.yaml`:**

```yaml
features-cross-instrument-service:
  batch:
    dimensions: [category, feature_category, date]
    category_values: [cefi, defi, tradfi]
    feature_category_values: [regime, cross_venue_spread, realized_vs_implied, cross_asset_correlation]
  live:
    dimensions: [feature_category]
```

---

## Testing

### Unit Tests Added

**Coverage achieved:**
- features-cross-instrument-service: 70%+
- market-data-processing-service: 79-93% (adapters)
- features-delta-one-service: 75%+
- features-volatility-service: 70%+
- market-tick-data-handler: 98% (incremental book adapter)

**Time-leakage guards:**
- All calculators verified NO forward-looking bias
- `.shift(-N)` only in targets.py (ML labels)
- Comprehensive test suite in `test_time_leakage_guards.py`

### Integration Tests (DEFERRED)

**Reason:** Requires testing infrastructure from consolidated plan

**Future tests:**
- End-to-end: MDPS → features-delta-one → features-cross-instrument → ML
- Schema validation on real GCS data
- Live mode PubSub flow

---

## Breaking Changes

**None.** All changes are additive:
- New columns added to existing schemas (backward compatible)
- New service (no impact on existing services)
- Existing features unchanged

---

## Rollout Plan

### Phase 1: Validation (Current Status)

✅ All SSOTs updated (workspace-manifest.json, runtime-topology.yaml, TOPOLOGY-DAG.md, SVGs)
✅ All schemas added (api-contracts, unified-internal-contracts)
✅ All implementations complete with unit tests
✅ All documentation created

### Phase 2: Deployment (Blocked - Needs Testing Infrastructure)

**Prerequisites:**
- Testing infrastructure from consolidated plan
- Integration tests passing
- Quality gates passing on all repos

**Steps:**
1. Provision API keys in Secret Manager
2. Create PubSub topics
3. Deploy features-cross-instrument-service to Cloud Run
4. Deploy updated services (MDPS, features-delta-one, features-volatility, market-tick-data-handler)
5. Run schema validation on sandbox data

### Phase 3: Backfill (Blocked - Needs Deployment)

**Steps:**
1. Run batch mode for historical dates (2024-01-01 to 2024-12-31)
2. Verify data completeness via DataCompletionChecker
3. Calculate feature quality metrics (NaN/inf counts, distributions)

### Phase 4: Live Mode (Blocked - Needs Backfill)

**Steps:**
1. Start services in live mode
2. Verify PubSub message flow
3. Verify GCS persistence
4. Monitor Cloud Logging for errors

---

## Representative Underlying (Binance Baseline)

**Key architectural decision:**

All cross-venue spreads calculated vs **Binance as representative baseline**.

**Rationale:**
- Binance has highest liquidity for most crypto pairs
- Defined in `unified-trading-deployment-v3/configs/representative_instruments.yaml`
- Example: `BINANCE-FUTURES:PERPETUAL:BTC-USDT@LIN` is representative for BTC

**Cross-venue spreads:**
- OKX spread = (OKX_price - Binance_price) / Binance_price * 10000 bps
- Bybit spread = (Bybit_price - Binance_price) / Binance_price * 10000 bps
- Hyperliquid spread = (Hyperliquid_price - Binance_price) / Binance_price * 10000 bps

**Spread to moving averages:**
- Spread to MA20, MA50, MA200 calculated for each venue
- Identifies overbought/oversold vs historical average

---

## Time-Leakage Prevention

**Critical guardrail:** All features are backward-looking only.

**Enforcement:**
- `.shift(-N)` forbidden in all calculators (except targets.py for ML labels)
- Realized volatility uses past data only (no future returns)
- Implied volatility is forward-looking by nature (market expectation) - acceptable
- HMM regimes fitted on historical data only
- Comprehensive test suite verifies no forward-looking bias

**Test pattern:**
```python
def test_no_forward_looking_in_realized_vol():
    """Ensure realized vol never uses future data."""
    df = create_synthetic_data_with_future_spike(spike_at_idx=100)
    features = calculator.calculate(df.iloc[:50])
    assert features at idx=50 does NOT reflect spike at idx=100
```

---

## Performance Considerations

### Memory Usage

**features-cross-instrument-service:**
- Aggregates across multiple venues/instruments
- Memory scales with: num_venues × num_instruments × lookback_window
- Recommended: 4-8GB RAM per shard

**market-data-processing-service:**
- New features add ~10% memory overhead
- Trade size percentiles require buffering raw trades
- Recommended: maintain 8GB RAM allocation

### Compute Requirements

**Regime detection (HMM):**
- CPU-intensive (EM algorithm)
- Scales with: num_states × num_observations
- Batch mode: ~5-10s per instrument per day
- Live mode: ~1-2s per update (incremental)

**Vol surface interpolation:**
- Scipy griddata cubic interpolation
- Scales with: num_strikes × num_expiries
- ~100ms per surface per update

---

## Monitoring

### Event Logging

**New lifecycle events:**
- features-cross-instrument-service: STARTED, VALIDATION_STARTED, PROCESSING_STARTED, PERSISTENCE_STARTED, STOPPED

**Check events:**
```bash
gsutil ls gs://central-element-323112-events/features-cross-instrument-service/
```

### Data Completeness

**Use DataCompletionChecker:**
```python
from unified_domain_client import DataCompletionChecker

checker = DataCompletionChecker()
result = checker.check_dataset_completeness(
    dataset="cross_instrument_features",
    start_date=date(2024, 1, 1),
    end_date=date(2024, 12, 31),
    expected_frequency="daily",
)
```

### Feature Quality Metrics

**Check for NaN/inf:**
```python
import pandas as pd

df = pd.read_parquet("gs://bucket/cross_instrument_features/date=2024-12-01/*.parquet")
print(f"NaN count: {df.isna().sum().sum()}")
print(f"Inf count: {np.isinf(df.select_dtypes(include=[np.number])).sum().sum()}")
```

---

## Rollback Plan

**If issues arise:**

1. **Disable features-cross-instrument-service:**
   ```bash
   gcloud run services update features-cross-instrument-service --no-traffic
   ```

2. **Revert service updates:**
   ```bash
   cd market-data-processing-service
   git revert <commit-hash>
   bash scripts/quickmerge.sh "revert: HFT features Tier 1"
   ```

3. **GCS data is immutable** - no rollback needed for persistence layer

---

## Next Steps

### Immediate (Blocked by Testing Infrastructure)
1. Run integration tests (needs testing infrastructure from consolidated plan)
2. Run quality gates on all modified repos
3. Deploy to sandbox environment
4. Validate schemas on real data

### Short-term (Post-Deployment)
1. Provision API keys in Secret Manager
2. Backfill historical data (2024-01-01 to 2024-12-31)
3. Start live mode for all services
4. Monitor for 48 hours

### Medium-term (Post-Validation)
1. Train ML models on new features
2. Validate alpha contribution via backtest
3. Optimize feature calculation performance (if needed)
4. Add more external data sources (Tier 4 extensible)

---

## Documentation

### Specifications Created
- market-data-processing-service/docs/HFT_FEATURES_TIER1_ADDITIONS.md
- features-delta-one-service/docs/MICROSTRUCTURE_FEATURES_ADVANCED.md
- features-volatility-service/docs/TRADFI_VOL_SURFACES.md
- features-calendar-service/docs/EXTERNAL_DATA_SOURCES.md
- market-tick-data-handler/docs/INCREMENTAL_BOOK_L2.md
- features-cross-instrument-service/docs/FEATURE_SPECIFICATION.md

### Codex Updates
- unified-trading-codex/02-data/cross-instrument-features-architecture.md
- unified-trading-codex/04-architecture/RUNTIME_TOPOLOGY_DECISIONS.md
- unified-trading-codex/06-coding-standards/time-leakage-prevention.md

### SSOTs Updated
- unified-trading-pm/workspace-manifest.json
- unified-trading-deployment-v3/configs/runtime-topology.yaml
- unified-trading-deployment-v3/configs/sharding_config.yaml
- unified-trading-codex/04-architecture/TOPOLOGY-DAG.md
- unified-trading-codex/04-architecture/WORKSPACE_MANIFEST_DAG.svg
- unified-trading-codex/04-architecture/RUNTIME_DEPLOYMENT_TOPOLOGY_DAG.svg

---

## Cost Estimates

### Data Ingestion
- **Databento OPRA + CME:** ~$100-500/mo (depends on symbols/exchanges)
- **CryptoQuant:** $0-29/mo (free tier or starter)
- **Others:** Free (CryptoPanic, LunarCrush, DefiLlama, FRED, Yahoo)

### Compute
- **features-cross-instrument-service:** ~$50-100/mo (Cloud Run, 4GB RAM, event-driven)
- **Incremental compute for existing services:** ~$20-30/mo (10% overhead)

**Total estimated increase:** ~$170-660/mo

---

## Support

**Questions/Issues:**
- Check unified-trading-pm/HFT_FEATURES_IMPLEMENTATION_STATUS.md for detailed status
- See service-specific docs in each repo's docs/ directory
- Codex: unified-trading-codex/02-data/, 04-architecture/, 06-coding-standards/

**Rollout tracking:**
- Status: Implementation complete, deployment pending
- Blocked by: Testing infrastructure from consolidated plan
- Next milestone: Integration tests passing
