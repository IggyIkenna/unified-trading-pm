---
doc_type: plan
title: domain-agnostic-ml-framework
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-api-contracts, unified-trading-library]
scope: [engineer, admin]
tags: []
related: []
created: '2026-04-14'
remaining_todos_consolidated_into: consolidated_ml_advanced_pipeline_2026_04_15
superseded_by: [consolidated_ml_advanced_pipeline_2026_04_15.md]
reconciliation_status: superseded_by_consolidator
reconciliation_date: 2026-04-25
overview: Extract domain-agnostic ML framework (targets, splits, signals, decisions) into UAC+UTL, with sports as category plugin
type: code
epic: epic-code-completion
completion_gates: {code: C4, deployment: none, business: none}
repo_gates:
- {repo: unified-api-contracts, code: C0, deployment: none, business: none}
- {repo: unified-trading-library, code: C0, deployment: none, business: none}
- {repo: ml-training-service, code: C0, deployment: none, business: none}
depends_on: []
context: "## Problem\nThe sports ML specs (target_spec.md, model_family_config.md, decision_policy.md, yamls.md)\ndefine sports-only bolt-ons. UTS principle: infrastructure is shared, domains plug in via config.\n\n## Architecture\n3 layers:\n- Layer 1 (UAC): Domain-agnostic schemas (TargetSpec, ModelFamilyConfig, SignalPackage, etc.)\n- Layer 2 (UTL): Domain-agnostic engines (target_registry, split_builder, signal_builder, etc.)\n- Layer 3 (UTL config_interface): Domain presets (SportsMLPresets extensions)\n- Layer 4 (ML-svc): Service wiring (--asset-group sports --family X)\n\n## Dependency DAG\n```\nPhase 1 (UAC schemas) ──> Phase 2 (UTL engines) ──> Phase 3 (Sports presets)\n                                                          │\n                                                          v\n                                                 Phase 4 (ML-svc wiring)\n```\nAll phases are SEQUENTIAL (each depends on the prior).\n\n## Pre-Audit Manifest\n| Repo | File | Action |\n|"
---

---|------|--------|
  | UAC | internal/domain/ml/schemas.py | ADD new schemas alongside existing |
  | UAC | internal/domain/ml/__init__.py | ADD exports for new schemas |
  | UTL | ml/__init__.py | ADD exports for new engines |
  | UTL | ml/target_registry.py | CREATE |
  | UTL | ml/split_builder.py | CREATE |
  | UTL | ml/signal_builder.py | CREATE |
  | UTL | ml/decision_policy_engine.py | CREATE |
  | UTL | ml/promotion_gate_evaluator.py | CREATE |
  | UTL | config_interface/sports_ml_config.py | EXTEND with target_specs, model_families, etc. |
  | ML-svc | app/core/sports_target_generator.py | EXTEND with full target builders |
  | ML-svc | adapters/feature_data_adapter.py | EXTEND with sports GCS paths |
  | ML-svc | cli/parser.py | EXTEND with sports category + family args |

todos:
  # ─────────────────────────────────────────────────────────────
  # Phase 1: UAC Domain-Agnostic ML Schemas
  # ─────────────────────────────────────────────────────────────

  - id: p1-uac-schemas
    content: |
      - [x] [AGENT] P0. Add domain-agnostic ML schemas to UAC internal/domain/ml/schemas.py

      New schemas (all BaseModel, domain-agnostic):
        - TargetSpec: target_name, domain, phase, task_type, horizon,
          label_formula, required_inputs, validity_conditions, evaluation_metrics, target_group
        - EvaluationMetricsConfig: primary list[str], secondary list[str]
        - ModelFamilyConfig: family_name, phase, purpose, feature_groups_required,
          feature_groups_optional, target_names, algorithms (per task_type),
          calibration, promotion_gates dict[str,float]
        - SplitStrategy: strategy_type (rolling/expanding), n_periods, period_unit,
          validation_window_size, validation_window_unit, gap_days
        - SignalPackage: entity_id, domain, market_type, prediction_phase,
          fundamental_prob, market_implied_prob, edge_bps, expected_clv_bps,
          uncertainty_score, bet_quality_score, signal_rank, abstain_flag, reason_codes
        - RegimeOverride: name, applies_when str, threshold_adjustments dict
        - FilterConfig: min_edge_bps, max_uncertainty_score, min_feature_validity_ratio
        - DecisionPolicyConfig: mode, filters FilterConfig, regime_overrides list,
          abstain_rules list[str], ranking_weights dict[str,float]
        - PromotionGate: metric_name, threshold, comparison (min/max)
        - AlgorithmConfig: regression list[ModelType], classification list[ModelType]

      Update __init__.py to export all new schemas.
    status: done

  - id: p1-uac-tests
    content: |
      - [x] [AGENT] P0. Write tests for new UAC ML schemas

      Tests:
        - Instantiation with valid data
        - Serialization round-trip (model_dump / model_validate)
        - Validation (invalid task_type, empty target_names, etc.)
        - TargetSpec with sports and cefi examples
        - ModelFamilyConfig with different algorithm sets
        - SignalPackage with abstain_flag edge cases
        - DecisionPolicyConfig with regime overrides

      Run: cd unified-api-contracts && bash scripts/quality-gates.sh
      Must maintain >= 84% coverage.
    status: done

  # ─────────────────────────────────────────────────────────────
  # Phase 2: UTL Domain-Agnostic ML Engines
  # ─────────────────────────────────────────────────────────────

  - id: p2-target-registry
    content: |
      - [x] [AGENT] P0. Create unified_trading_library/ml/target_registry.py

      TargetRegistry class:
        - __init__(specs: list[TargetSpec])
        - get_specs_for_family(family_name: str) -> list[TargetSpec]
        - get_specs_for_domain(domain: str) -> list[TargetSpec]
        - get_specs_for_phase(phase: str) -> list[TargetSpec]
        - get_spec(target_name: str) -> TargetSpec
        - validate_targets(targets_df, spec) -> list[str] (validation errors)

      Domain-agnostic: no sports/cefi imports. Just a lookup + validation layer.
    status: done

  - id: p2-split-builder
    content: |
      - [x] [AGENT] P0. Create unified_trading_library/ml/split_builder.py

      SplitBuilder class:
        - __init__(config: SplitStrategy)
        - generate_splits(df, date_col="timestamp") -> list[SplitFold]
        - SplitFold: train_start, train_end, val_start, val_end, fold_number

      Strategies:
        - "rolling": rolling N-period window (N configurable, period_unit configurable)
        - "expanding": expanding window (existing behavior, for diagnostics)

      Period resolution via PeriodResolver protocol:
        - CalendarPeriodResolver: months/quarters/years
        - SeasonPeriodResolver: registered via domain presets (sports)

      Must NOT break existing WalkForwardValidator — this is additive.
    status: done

  - id: p2-signal-builder
    content: |
      - [x] [AGENT] P0. Create unified_trading_library/ml/signal_builder.py

      SignalBuilder class:
        - __init__(policy: DecisionPolicyConfig)
        - build_signals(predictions: dict[str, pd.DataFrame], entity_col: str) -> list[SignalPackage]
        - _compute_edge_bps(fundamental_prob, market_implied_prob) -> float
        - _compute_uncertainty_score(validity_ratio, ...) -> float
        - _rank_signals(signals: list[SignalPackage]) -> list[SignalPackage]

      Domain-agnostic: works with any prediction DataFrames keyed by model family.
    status: done

  - id: p2-decision-policy
    content: |
      - [x] [AGENT] P0. Create unified_trading_library/ml/decision_policy_engine.py

      DecisionPolicyEngine class:
        - __init__(config: DecisionPolicyConfig)
        - apply_filters(signals: list[SignalPackage]) -> list[SignalPackage]
        - apply_regime_overrides(signals, regime_flags: dict[str, bool]) -> list[SignalPackage]
        - apply_abstain_logic(signals) -> list[SignalPackage] (sets abstain_flag)
        - rank_and_select(signals, top_n: int) -> list[SignalPackage]
        - run(signals, regime_flags) -> list[SignalPackage] (full pipeline)
    status: todo

  - id: p2-promotion-gates
    content: |
      - [ ] [AGENT] P0. Create unified_trading_library/ml/promotion_gate_evaluator.py

      PromotionGateEvaluator class:
        - __init__(gates: list[PromotionGate])
        - evaluate(metrics: dict[str, float]) -> tuple[bool, list[str]]
          Returns (passed, list of failure reasons)
        - evaluate_family(family_config: ModelFamilyConfig, metrics) -> tuple[bool, list[str]]
    status: done

  - id: p2-utl-exports
    content: |
      - [x] [AGENT] P0. Update unified_trading_library/ml/__init__.py with new exports
    status: done

  - id: p2-utl-tests
    content: |
      - [x] [AGENT] P0. Write tests for all UTL engines

      Test files:
        - tests/unit/test_ml_target_registry.py
        - tests/unit/test_ml_split_builder.py
        - tests/unit/test_ml_signal_builder.py
        - tests/unit/test_ml_decision_policy_engine.py
        - tests/unit/test_ml_promotion_gate_evaluator.py

      Each with:
        - Happy path with dummy data
        - Edge cases (empty inputs, missing columns)
        - Domain-agnostic verification (works for sports AND cefi configs)

      Run: cd unified-trading-library && bash scripts/quality-gates.sh
      Must maintain >= 65% coverage.
    status: done

  # ─────────────────────────────────────────────────────────────
  # Phase 3: Sports Domain Presets
  # ─────────────────────────────────────────────────────────────

  - id: p3-sports-presets
    content: |
      - [x] [AGENT] P0. Extend SportsMLPresets in UTL config_interface/sports_ml_config.py

      New static methods:
        - target_specs() -> list[TargetSpec]: 32 sports targets from target_spec.md
        - model_families() -> list[ModelFamilyConfig]: 5 families
        - split_config() -> SplitStrategy: rolling 2-season, 8-week validation
        - decision_policy(mode: str) -> DecisionPolicyConfig: filters + regime overrides
        - promotion_gates() -> dict[str, list[PromotionGate]]: per-family thresholds

      These are pure config — no business logic. Just typed Python returning the
      domain knowledge from the spec docs.
    status: done

  - id: p3-sports-tests
    content: |
      - [x] [AGENT] P0. Write tests for sports presets

      Test file: tests/config_interface/unit/test_sports_ml_presets.py

      Tests:
        - target_specs returns 32 TargetSpecs, all domain="sports"
        - model_families returns 5 families covering all target groups
        - split_config returns rolling with period_unit="season", n_periods=2
        - decision_policy returns valid config for each mode
        - promotion_gates covers all 5 families
        - Round-trip: all presets serialize/deserialize correctly

      Run: cd unified-trading-library && bash scripts/quality-gates.sh
    status: done

  # ─────────────────────────────────────────────────────────────
  # Phase 4: ML Training Service Wiring
  # ─────────────────────────────────────────────────────────────

  - id: p4-family-router
    content: |
      - [x] [AGENT] P0. Create FamilyRouter bridge in ML training service

      Created app/core/family_router.py with:
        - get_family_router(category) factory — returns FamilyRouter for "SPORTS", None otherwise
        - FamilyRouter class: holds families, registry, decision_policies
        - Methods: get_family, validate_features, get_policy_for_phase
        - _build_sports_router() builds from SportsMLPresets

      Added "SPORTS" to CLI CATEGORIES in cli/parser.py.
      Added facade re-exports (SportsMLPresets, TargetRegistry) in UTL __init__.py.
      14 tests in tests/unit/test_family_router.py.
    status: done

  - id: p4-sports-targets
    content: |
      - [x] [AGENT] P0. Sports target generators implemented — sports_target_generator.py has XG/CLV/HT/Meta builders + test_sports_target_builders.py exists. target_generator_factory.py routes sports families.
    status: done

  - id: p4-feature-adapter
    content: |
      - [ ] [AGENT] P0. Add sports GCS feature loading to ML training service

      In adapters/feature_data_adapter.py, add sports feature path resolution:
        - Bucket: features-sports-{project}/by_date/day={date}/
        - Feature groups: derived features + odds features
        - Merge logic: join on fixture_id

      Wire into the pipeline so --asset-group sports loads from FSS output.
    status: todo

  - id: p4-cli-wiring
    content: |
      - [x] [AGENT] P0. Extend ML training service CLI for sports (partial)

      Done:
        - "SPORTS" added to CATEGORIES in cli/parser.py
        - FamilyRouter routes --asset-group sports to SportsMLPresets (app/core/family_router.py)

      Remaining (requires sports data pipeline):
        - Add --family arg (pregame_xg, pregame_clv, ht_xg, ht_clv, meta)
        - Wire handler to construct TrainingPipelineConfig from family config
    status: done

  - id: p4-ml-tests
    content: |
      - [x] [AGENT] P0. Write ML training service tests for FamilyRouter

      Done:
        - tests/unit/test_family_router.py: 14 tests covering router creation,
          family lookup, registry integration, decision policies, feature validation
        - ML-svc QG passes (80% coverage maintained)

      Remaining (requires target builder implementation):
        - tests/unit/test_sports_target_builders.py
        - tests/integration/test_sports_pipeline_e2e.py
    status: done

  # ─────────────────────────────────────────────────────────────
  # Phase 5: Cleanup
  # ─────────────────────────────────────────────────────────────

  - id: p5-archive
    content: |
      - [x] [AGENT] P1. Archive completed spec docs

      Superseded notes added:
        - features_improvements.md: superseded by SportsMLPresets + feature calculators
        - ml_refactor.md: superseded by domain-agnostic ML framework (this plan)

      Kept active (domain knowledge consumed by SportsMLPresets):
        - target_spec.md, model_family_config.md, decision_policy.md, yamls.md

      MEMORY.md updated.
    status: done

isProject: false
---

> **SUPERSEDED 2026-04-25 by
> [consolidated_ml_advanced_pipeline_2026_04_15.md](./consolidated_ml_advanced_pipeline_2026_04_15.md).** Original scope
> retained for history. Frontmatter `remaining_todos_consolidated_into:` was already present; this commit formalises it
> as canonical `superseded_by:` and adds this banner. See `_reconciliation_evidence_map_2026_04_25.md` for evidence.
