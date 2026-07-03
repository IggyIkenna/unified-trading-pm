---
doc_type: plan
title: cross-domain-alpha-execution-intelligence
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [execution-service]
scope: [engineer, admin]
tags: []
related: []
created: '2026-04-14'
remaining_todos_consolidated_into: consolidated_strategy_and_ui_2026_04_15
superseded_by: [consolidated_strategy_and_ui_2026_04_15.md]
reconciliation_status: superseded_by_consolidator
reconciliation_date: 2026-04-25
overview: Cross-domain feature blending, microstructure features, DeFi alpha, execution cost prediction, unified SOR, feature freshness SLA, data quality scoring
type: code
epic: epic-code-completion
locked_by: live-defi-rollout
locked_since: 2026-04-11
completion_gates: {code: C5, deployment: none, business: B3}
repo_gates:
- {repo: unified-api-contracts, code: C0, deployment: none, business: none}
- {repo: unified-trading-library, code: C0, deployment: none, business: none}
- {repo: features-delta-one-service, code: C0, deployment: none, business: none}
- {repo: features-onchain-service, code: C0, deployment: none, business: none}
- {repo: features-cross-instrument-service, code: C0, deployment: none, business: none}
- {repo: execution-service, code: C0, deployment: none, business: none}
- {repo: market-tick-data-service, code: C0, deployment: none, business: none}
depends_on: []
todos:
- {id: p1-uac-crossdomain-schemas, content: '- [ ] [AGENT] P0. Add cross-domain feature, SLA, and DQS schemas to UAC internal

    Add to `unified_api_contracts/internal/`:

    - `CrossDomainFeatureSpec`: source_domain, target_domain, lag_hours, correlation_method, granger_pvalue

    - `FeatureFreshnessSLA`: domain (cefi/defi/tradfi/sports), max_staleness_seconds (live), max_staleness_seconds_batch, attenuation_formula

    - `DataQualityScore`: instrument_id, date, completeness (0-1), consistency (0-1), timeliness (0-1), aggregate_dqs (0-1)

    - `ExecutionCostPrediction`: instrument_id, venue, order_size, predicted_slippage_bps, predicted_fill_rate, optimal_algorithm, confidence

    - `MicrostructureFeatures`: instrument_id, timestamp, ofi (order flow imbalance), vpin, kyle_lambda, depth_imbalance_5/10/20, trade_size_clustering_score

    ', status: todo, note: 'PARALLEL with p1-utl-sla-engine, p1-utl-crossdomain-calc'}
- {id: p1-utl-sla-engine, content: '- [ ] [AGENT] P0. Build FeatureFreshnessSLAEngine in UTL feature_service_base/sla_engine.py

    `FeatureFreshnessSLAEngine`:

    - `check_freshness(feature_timestamp: datetime, domain: str, mode: str) -> tuple[bool, float]` — returns (within_sla, attenuation_factor)

    - Attenuation: `max(0, 1 - (staleness / max_staleness))` — smooth confidence decay, not binary

    - Default SLAs: CeFi live=60s/batch=3600s, DeFi live=12s/batch=300s, TradFi live=60s/batch=86400s, Sports live=300s/batch=3600s

    - SLA overrides via config (hot-reloadable)

    - Integrates with existing FeatureValidityEngine: SLA breach sets block confidence to attenuation factor

    ', status: todo, note: PARALLEL with p1-uac-crossdomain-schemas}
- {id: p1-utl-crossdomain-calc, content: '- [ ] [AGENT] P0. Build cross-domain feature calculators in UTL feature_calculator/crossdomain.py

    Calculator functions (domain-agnostic, used by any feature service):

    - `lag_adjusted_correlation(series_a: Series, series_b: Series, max_lag_hours: int = 48) -> DataFrame` — correlation at each lag

    - `granger_causality_score(x: Series, y: Series, max_lag: int = 24) -> float` — p-value of Granger test

    - `cross_domain_lead_lag(domain_a_features: DataFrame, domain_b_features: DataFrame) -> DataFrame` — pairwise lead-lag matrix

    - `merge_cross_domain_features(primary: DataFrame, secondary: DataFrame, lag_hours: int, prefix: str) -> DataFrame` — time-shifted join

    Key cross-domain signals:

    - DeFi DEX volume → CeFi crypto volatility (lag 1-4 hours)

    - DeFi gas prices → CeFi transaction costs (lag 0-1 hours)

    - Sports sharp money (Pinnacle) → prediction market prices (lag 10-45 min)

    - Macro rates → squad values/TV money (lag days-weeks, sports)

    ', status: todo, note: PARALLEL with p1-utl-sla-engine}
- {id: p1-utl-dqs, content: '- [ ] [AGENT] P1. Build DataQualityScorer in UTL feature_service_base/data_quality.py

    `DataQualityScorer`:

    - `score_completeness(df: DataFrame, expected_columns: list, expected_rows: int) -> float` — % present / expected

    - `score_consistency(df: DataFrame, cross_source_df: DataFrame, key_columns: list) -> float` — % matching across sources

    - `score_timeliness(timestamps: Series, expected_interval: timedelta) -> float` — 1 - (mean_delay / max_acceptable)

    - `aggregate(completeness, consistency, timeliness, weights=(0.4, 0.3, 0.3)) -> float` — weighted DQS

    - Output: DataQualityScore per instrument per day, stored in manifest

    - DQS flows to meta-model as feature (models learn to distrust low-quality data)

    ', status: todo, note: PARALLEL with p1-utl-crossdomain-calc}
- {id: p1-qg, content: '- [ ] [AGENT] P0. Run quality-gates.sh on UAC, UTL — all pass

    ', status: todo, note: SEQUENTIAL — gate before Phase 2}
- {id: p2-microstructure-delta-one, content: '- [ ] [AGENT] P0. Add microstructure feature calculators to features-delta-one-service

    Since features-microstructure-service doesn''t exist as a separate repo, add to features-delta-one-service:

    New calculator `microstructure_calculator.py`:

    - `order_flow_imbalance(trades: DataFrame, window: int) -> Series` — net aggressive buying pressure

    - `vpin_estimate(trades: DataFrame, volume_bucket_size: int) -> Series` — Volume-synced PIN

    - `depth_imbalance(orderbook_snapshots: DataFrame, levels: list[int]) -> DataFrame` — bid/ask imbalance at 5/10/20 levels

    - `trade_size_clustering(trades: DataFrame) -> Series` — detect institutional block orders via size distribution

    - `inter_exchange_lead_lag(venue_a_trades: DataFrame, venue_b_trades: DataFrame) -> float` — cross-venue latency signal

    Register in CALCULATOR_REGISTRY, add to feature_definitions.yaml

    ', status: todo, note: 'PARALLEL with p2-crossdomain-features, p2-defi-alpha'}
- {id: p2-crossdomain-features, content: '- [ ] [AGENT] P0. Wire cross-domain features into features-cross-instrument-service

    Add `crossdomain_feature_handler.py`:

    - Load DeFi on-chain features (TVL, gas, DEX volume) from GCS

    - Load CeFi delta-one features (volatility, funding rate) from GCS

    - Compute lag-adjusted cross-correlations using UTL crossdomain.py

    - Output cross-domain features: `defi_dex_volume_24h_lag_vs_btc_vol`, `defi_gas_vs_cefi_spread`, `sharp_money_lead_prediction_mkt`

    - Store to GCS: `gs://features/cross_domain/{category}/{date}/features.parquet`

    - Add to feature_definitions.yaml with dependency DAG

    ', status: todo, note: PARALLEL with p2-microstructure-delta-one}
- {id: p2-defi-alpha, content: '- [ ] [AGENT] P1. Add DeFi-specific alpha features to features-onchain-service

    New calculators:

    - `mev_features_calculator.py`: sandwich_attack_frequency (per pool, from mempool data), frontrunning_probability

    - `liquidity_concentration_calculator.py`: tick_liquidity_distribution (Uniswap V3), concentrated_position_ratio, liquidity_migration_score

    - `whale_activity_calculator.py`: large_transfer_count (from Alchemy Transfers), whale_accumulation_score, smart_money_flow_direction

    - `bridge_flow_calculator.py`: bridge_volume_net (from Socket/cross-chain data), bridge_direction_signal, chain_flow_momentum

    Register all in FeatureCalculatorRegistry, add to feature_definitions.yaml

    ', status: todo, note: PARALLEL with p2-crossdomain-features}
- {id: p2-sla-integration, content: '- [ ] [AGENT] P1. Integrate SLA engine into all feature services

    For each: features-delta-one-service, features-onchain-service, features-cross-instrument-service:

    - Import FeatureFreshnessSLAEngine from UTL

    - In feature computation handler: check freshness before using upstream data

    - If SLA breached: attenuate confidence of dependent features, emit FEATURE_SLA_BREACH event

    - Add SLA metrics to health API data_freshness callback

    ', status: todo, note: PARALLEL with p2-defi-alpha}
- {id: p2-dqs-mtds, content: '- [ ] [AGENT] P1. Integrate DataQualityScorer into market-tick-data-service

    In data_manifest_handler.py:

    - After writing tick data to GCS, compute DQS per instrument per day

    - Store DQS in manifest: `data_manifest.json` gains `quality_scores` dict per operation

    - DQS flows downstream: feature services read DQS from manifest, include as meta-feature

    - Add DQS to health API response

    ', status: todo, note: PARALLEL with p2-sla-integration}
- {id: p2-qg, content: '- [ ] [AGENT] P0. Run quality-gates.sh on all Phase 2 repos — pass

    ', status: todo, note: SEQUENTIAL — gate before Phase 3}
- {id: p3-cost-model, content: "- [ ] [AGENT] P0. Build execution cost prediction model in execution-service\nNew module `algo_library/cost_model.py`:\n- `ExecutionCostPredictor`:\n  - `predict(instrument_id, venue, order_size, spread, depth, volatility, time_of_day) -> ExecutionCostPrediction`\n  - Model: LightGBM trained on historical fill data (predicted slippage, fill rate)\n  - Feature engineering: rolling spread (5m/15m/1h), depth at best 5 levels, realized vol (1h), hour_of_day, day_of_week\n  - Training data source: execution-service fill logs in GCS\n  - Inference: <10ms per prediction (cached model)\n- `CostModelTrainer`: periodic retraining from fill history\n- Integration: InstructionRouter queries cost model before routing, adds predicted_cost to instruction context\n- Strategy-service can query via health API endpoint\n", status: todo, note: PARALLEL with p3-unified-sor}
- {id: p3-unified-sor, content: "- [ ] [AGENT] P1. Build unified CeFi+DeFi SOR in execution-service\nNew module `algo_library/unified_sor.py`:\n- `UnifiedSmartOrderRouter`:\n  - `route(instruction, venues: list[VenueConfig]) -> list[VenueSplit]` — optimal split across CeFi + DeFi venues\n  - Cost comparison: CeFi (maker/taker fees + spread) vs DeFi (gas + swap fee + slippage)\n  - Uses ExecutionCostPredictor for each venue to estimate total cost\n  - Optimization: minimize total execution cost subject to fill constraints\n  - Venue types: CLOB (Binance, Coinbase), AMM (Uniswap, Curve), Hybrid (Hyperliquid)\n- Wire into InstructionRouter: if instruction_type == TRADE and multiple venues available, use UnifiedSOR\n- Fallback: single-venue execution if SOR overhead > benefit threshold\n", status: todo, note: PARALLEL with p3-cost-model}
- {id: p3-qg, content: '- [ ] [AGENT] P0. Run quality-gates.sh on execution-service — pass

    ', status: todo, note: SEQUENTIAL — gate before Phase 4}
- {id: p4-final-qg, content: '- [ ] [AGENT] P0. Final QG on all repos: UAC, UTL, features-delta-one-service, features-onchain-service, features-cross-instrument-service, execution-service, market-tick-data-service

    ', status: todo, note: SEQUENTIAL — final validation}
isProject: false
---

> **SUPERSEDED 2026-04-25 by
> [consolidated_strategy_and_ui_2026_04_15.md](./consolidated_strategy_and_ui_2026_04_15.md).** Original scope retained
> for history. Frontmatter `remaining_todos_consolidated_into:` was already present; this commit formalises it as
> canonical `superseded_by:` and adds this banner. See `_reconciliation_evidence_map_2026_04_25.md` for evidence.

# Cross-Domain Alpha & Execution Intelligence

## Context

The current system computes features per domain independently. Cross-domain signals (DeFi → CeFi, sharp money →
prediction markets) are real alpha sources being left on the table. Execution lacks a unified cost model and cross-venue
SOR. This plan addresses 7 deltas from the 2026-04-11 analysis.

### Execution DAG

```
Phase 1 (PARALLEL) ─────────────────────────────────────────
  ├── [UAC] Cross-domain, SLA, DQS, cost prediction schemas
  ├── [UTL] FeatureFreshnessSLAEngine
  ├── [UTL] Cross-domain feature calculators
  └── [UTL] DataQualityScorer
          │
       QG Gate (UAC + UTL)
          │
Phase 2 (PARALLEL within, SEQUENTIAL after P1) ─────────────
  ├── [features-delta-one] Microstructure calculators (OFI, VPIN, depth)
  ├── [features-cross-instrument] Cross-domain feature wiring
  ├── [features-onchain] DeFi alpha features (MEV, liquidity, whale, bridge)
  ├── [all feature services] SLA engine integration
  └── [MTDS] Data quality scoring integration
          │
       QG Gate (all feature repos + MTDS)
          │
Phase 3 (PARALLEL within, SEQUENTIAL after P2) ─────────────
  ├── [execution] ExecutionCostPredictor
  └── [execution] UnifiedSmartOrderRouter (CeFi + DeFi)
          │
       QG Gate (execution-service)
          │
Phase 4 (SEQUENTIAL) ───────────────────────────────────────
  └── Final QG on all 7 repos
```

### Success Criteria

- **Code:** quality-gates.sh passes on all 7 repos
- **Test:** Cross-domain features produce non-null values for historical data; SLA engine correctly attenuates stale
  features; DQS scores correlate with model performance
- **Business (B3):** Cross-domain features improve model AUC by >2%; execution cost model predicts slippage within 20%
  of actual; unified SOR reduces average execution cost by >5bps vs single-venue
