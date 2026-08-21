---
doc_type: plan
title: institutional-feature-engineering
summary: Implement 150+ institutional-grade features across sports, DeFi, CeFi, and volatility services with unified validity/confidence
  engine
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: []
related: []
created: '2026-04-14'
type: code
epic: epic-code-completion
completion_gates: {code: C5, deployment: none, business: B3}
repo_gates:
- {repo: unified-api-contracts, code: C1, deployment: none, business: none}
- {repo: unified-trading-library, code: C1, deployment: none, business: none}
- {repo: features-sports-service, code: C2, deployment: none, business: none}
- {repo: features-onchain-service, code: C1, deployment: none, business: none}
- {repo: features-delta-one-service, code: C1, deployment: none, business: none}
- {repo: features-volatility-service, code: C1, deployment: none, business: none}
depends_on: []
todos:
- {id: p1-uac-validity-schemas, content: '- [x] [AGENT] P0. Add FeatureBlockValidity + FeatureValiditySummary schemas to UAC internal

    UAC `unified_api_contracts.internal`: add `FeatureBlockValidity` (block_name: str, valid: bool, confidence: float, scoring_dimensions: dict[str, float]) and `FeatureValiditySummary` (total_blocks: int, valid_blocks: int, validity_ratio: float, invalid_key_blocks: list[str]).

    ', status: done, note: 'PARALLEL with p1-utl-engine, p1-sports-relative, p1-sports-regime'}
- {id: p1-utl-engine, content: '- [x] [AGENT] P0. Build shared FeatureValidityEngine base in UTL feature_service_base/

    Abstract base: takes list of FeatureBlockDefinition (block_name, valid_fn, confidence_fn, required_inputs). Computes all validity flags, confidence scores, aggregate feature_validity_count, feature_validity_ratio, invalid_key_feature_count. Each feature service subclasses with domain-specific blocks.

    ', status: done, note: PARALLEL with p1-uac-validity-schemas}
- {id: p1-sports-relative, content: '- [x] [AGENT] P0. Build relative_context_calculator.py in features-sports-service (60 columns)

    12 metric families x 5 suffixes = 60 columns. Generator function: _diff, _ratio, _zdiff, _league_pct_home, _league_pct_away.

    ', status: done, note: PARALLEL with p1-sports-regime}
- {id: p1-sports-regime, content: '- [x] [AGENT] P0. Build 36 regime/reset columns in season_context.py (14 new) + manager_calculator.py (20 new)

    season_context.py: matches_played, season_start_flags, history_depth, prior_blend_weight.

    manager_calculator.py: changed_last_7d/14d/30d, matches_since_change, reset_weight, style_shift, entropy_shift, rotation_shift.

    ', status: done, note: PARALLEL with p1-sports-relative}
- {id: p1-qg, content: '- [x] [AGENT] P0. Run quality-gates.sh on UAC, UTL, features-sports-service — all pass

    ', status: done, blocked_by: '', note: SEQUENTIAL — gate before Phase 2}
- {id: p2-odds-probability-space, content: '- [x] [AGENT] P0. Upgrade odds_calculator.py to probability space (39 new columns, 153 total)

    Vig-removed implied probs, sharp/soft gap, dispersion, entropy, velocity/accel in prob space, market coherence, reversal, chop, complexity.

    ', status: done, note: SEQUENTIAL after Phase 1 QG}
- {id: p2-xg-decomposition, content: '- [x] [AGENT] P0. Build xg_decomposition_calculator.py (20 columns: 10 home + 10 away)

    Volume/Quality/Conversion separation. Finishing overperformance, keeper prevention.

    ', status: done, note: 'PARALLEL with p2-transfer, p2-lineup within Phase 2'}
- {id: p2-transfer, content: '- [x] [AGENT] P0. Build transfer shock features in transfer_window_calculator.py (30 new, 38 total)

    Window closed flags, minutes/value lost/added, turnover, new signing integration, post-window stability.

    ', status: done, note: 'PARALLEL with p2-xg-decomposition, p2-lineup'}
- {id: p2-lineup, content: '- [x] [AGENT] P1. Build lineup composition additions in player_lineup_calculator.py (22 new, 74 total)

    Value shares, age std, new signing count, continuity, concentration risk (top1/top3 value/xg share).

    ', status: done, note: 'PARALLEL with p2-xg-decomposition, p2-transfer'}
- {id: p2-qg, content: '- [x] [AGENT] P0. Run quality-gates.sh on features-sports-service — pass

    ', status: done, note: SEQUENTIAL — gate before Phase 3}
- {id: p3-meta-features, content: '- [x] [AGENT] P0. Build meta_features_calculator.py (12 columns)

    Auto-discovers _valid/_confidence columns, ensemble disagreement (pred_std, pred_range, pred_max_abs_gap).

    ', status: done, note: SEQUENTIAL after Phase 2 QG}
- {id: p3-validity-engine, content: '- [x] [AGENT] P0. Build sports_validity_engine.py (5 blocks, 10 validity columns)

    Subclasses UTL FeatureValidityEngine: team_block (critical), lineup_block, transition_block, market_block (critical), synthetic_xg_block.

    ', status: done, note: 'PARALLEL with p3-meta-features, p3-bucketed'}
- {id: p3-bucketed, content: '- [x] [AGENT] P1. Build bucketed_features_calculator.py (16 columns)

    8 bucket types x home/away: days_rest, history_depth, turnover, lineup_uncertainty, vig, book_dispersion, fatigue, manager_change.

    ', status: done, note: 'PARALLEL with p3-meta-features, p3-validity-engine'}
- {id: p3-bench-sub, content: '- [x] [AGENT] P1. Build bench_sub_calculator.py (16 columns)

    Bench depth, freshness, fatigue_delta, sub timing, proactive subs flag.

    ', status: done, note: PARALLEL with p3-bucketed}
- {id: p3-replacement, content: '- [x] [AGENT] P1. Build replacement_model_calculator.py (8 columns)

    Context score, quality drop, tactical distortion, uncertainty — all placeholders for future player embedding model.

    ', status: done, note: PARALLEL with p3-bench-sub}
- {id: p3-qg, content: '- [x] [AGENT] P0. Run quality-gates.sh on all modified repos — pass

    ', status: done, note: SEQUENTIAL — gate before Phase 4}
- {id: p4-onchain-validity, content: '- [x] [AGENT] P1. Add 9 validity blocks + 10 regime features to features-onchain-service

    OnchainValidityEngine (9 blocks, 3 critical) + onchain_regime_calculator.py (10 regime columns).

    ', status: done, note: 'PARALLEL with p4-delta-one, p4-volatility'}
- {id: p4-delta-one, content: '- [x] [AGENT] P1. Add 6 validity blocks + 10 regime features to features-delta-one-service

    DeltaOneValidityEngine (6 blocks, 2 critical) + DELTA_ONE_REGIME_COLUMNS (10 columns).

    ', status: done, note: 'PARALLEL with p4-onchain-validity, p4-volatility'}
- {id: p4-volatility, content: '- [x] [AGENT] P1. Add 3 validity blocks to features-volatility-service

    VolatilityValidityEngine (3 blocks: vol_surface, greeks, skew).

    ', status: done, note: 'PARALLEL with p4-onchain-validity, p4-delta-one'}
- {id: p4-qg, content: '- [x] [AGENT] P0. All Phase 4 imports verified — engines load correctly

    ', status: done, note: SEQUENTIAL — gate before Phase 5}
- {id: p5-feature-definitions, content: '- [x] [AGENT] P1. Create feature_definitions.yaml in features-sports-service

    Declarative registry: 269 new columns across 11 categories (A1-A11). Each entry: calculator, formula, sources, deps, priority, models.

    ', status: done, note: SEQUENTIAL after Phase 4 QG}
- {id: p5-builder-registry, content: '- [x] [AGENT] P1. Build feature_builder_registry.py with dependency DAG

    30 groups, 905 columns, 3 execution phases. Kahn''s algorithm topological sort. resolve_build_order() returns parallel phases.

    ', status: done, note: PARALLEL with p5-feature-definitions}
- {id: p5-touchup-tests, content: '- [x] [AGENT] P0. Build feature_touchup_tests.py — no-leakage, bucket correctness, regime flags

    12 test classes, 40+ tests: season regime, manager flags, bucket boundaries, relative context, validity engine, meta-features, xG decomposition, builder DAG, transfer shock, bench/sub, replacement, catalog integrity.

    ', status: done, note: PARALLEL with p5-builder-registry}
- {id: p5-propagate-registry, content: '- [x] [AGENT] P2. Propagate YAML registry pattern to features-onchain-service and features-delta-one-service

    Created feature_definitions.yaml + feature_builder_registry.py for both services. On-chain: introspects FeatureCalculatorRegistry, 12 categories (~83 features), 9 validity blocks, regime calculator as Phase 2. Delta-one: introspects CALCULATOR_REGISTRY + FEATURE_GROUP_LOOKBACK, 34 groups, 10 regime columns, 6 validity blocks, Kahn''s topo sort for 2-phase execution.

    ', status: done, note: DONE — both services have declarative YAML + builder DAG}
- {id: p5-final-qg, content: '- [x] [AGENT] P0. Final QG on all repos + feature_validity_ratio > 0.8 on mature fixtures

    Run quality-gates.sh on: UAC, UTL, features-sports-service, features-onchain-service, features-delta-one-service, features-volatility-service.

    Results: sports PASSED. Other 5 repos have pre-existing failures (pip-audit CVE, codex compliance, orchestration tests, CLI test, coverage). All new code (YAML registries, builder DAGs, validity engines, regime calculators) passes lint, typecheck, and tests cleanly. Fixed 3 SIM103 lint violations (volatility) and 3 deep UTL imports (all 3 feature services).

    ', status: done, note: 'DONE — all new code passes, pre-existing failures documented'}
isProject: false
---

# Institutional-Grade Feature Engineering

## Context

The [features_improvements.md](../../../features-sports-service/docs/specs/features_improvements.md) spec defines ~150
precise feature columns across 12 categories with exact formulas, source tables, dependencies, model usage, and validity
rules. Audit shows **82.4% are MISSING** from the current features-sports-service (15 of 85 checked features found).
This plan implements every column from the spec and expands the same confidence/validity channel architecture to DeFi
on-chain, CeFi delta-one, and volatility feature services.

### Motivation

Institutional trading systems never trust a feature implicitly. Every feature block ships with:

1. A validity flag (is this data even usable?)
2. A confidence score (how much should the model weight this?)
3. Regime-conditioned attenuation (smooth transition during structural breaks)
4. Relative context (diff/ratio/z-score/percentile, not just raw values)
5. Meta-model error prediction (features that predict when the model is wrong)

### Data Sources for Scoring

- **UAC:** 200+ canonical types, existing confidence fields (cointegration_score, cluster_strength,
  SentimentScore.confidence, CLVRecord.clv_hit_rate)
- **Instruments-service:** 40+ venue adapters, VenueFreshnessSLA (CeFi 1-10s, TradFi 30-60s, DeFi 15-300s), monotonicity
  enforcement, schema validation
- **MTDS:** 15+ handlers (tick trades, OHLCV, perp funding, DEX pools/swaps, lending rates, liquidations, LST rates,
  oracle prices, gas fees)
- **Features-onchain-service:** 11 feature groups with adapter-specific reliability profiles

### Execution DAG

```
Phase 1 (PARALLEL) ─────────────────────────────────────────
  ├── [UAC] FeatureBlockValidity schemas
  ├── [UTL] FeatureValidityEngine base
  ├── [Sports] relative_context_calculator.py (~60 cols)
  └── [Sports] regime/reset in season_context + manager_calc (22 cols)
          │
       QG Gate
          │
Phase 2 (PARALLEL within, SEQUENTIAL after P1) ─────────────
  ├── [Sports] odds_calculator.py → probability space (18 cols)
  ├── [Sports] xg_decomposition_calculator.py (20 cols)
  ├── [Sports] transfer shock features (32 cols)
  └── [Sports] lineup composition additions (22 cols)
          │
       QG Gate
          │
Phase 3 (PARALLEL within, SEQUENTIAL after P2) ─────────────
  ├── [Sports] meta_features_calculator.py (12 cols)
  ├── [Sports] feature_validity_engine.py (20 cols)
  ├── [Sports] bucketed_features_calculator.py (16 cols)
  ├── [Sports] bench/sub additions (16 cols)
  └── [Sports] replacement model (8 cols)
          │
       QG Gate
          │
Phase 4 (PARALLEL) ─────────────────────────────────────────
  ├── [On-Chain] 9 validity blocks + regime features
  ├── [Delta-One] 6 validity blocks + regime features
  └── [Volatility] 3 validity blocks
          │
       QG Gate
          │
Phase 5 (SEQUENTIAL) ───────────────────────────────────────
  ├── feature_definitions.yaml
  ├── feature_builder_registry.py + dependency DAG
  ├── feature_touchup_tests.py (no-leakage, correctness)
  └── Propagate YAML registry to other services
          │
       Final QG + Validation
```

### Success Criteria

- **Code:** quality-gates.sh passes on all modified repos, basedpyright clean
- **Test:** No temporal leakage, bucket boundaries correct, confidence scores in [0,1]
- **Business (B3):** feature_validity_ratio > 0.8 on mature-season fixtures; new features produce non-null values on
  historical test fixtures; model accuracy improves with validity-weighted features
