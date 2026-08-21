---
doc_type: plan
title: ml-pipeline-complete
summary: Complete ML training pipeline for all categories — Sports (family-based), TradFi (market-hours-aware), CEFI stubs
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-library]
scope: [engineer, admin]
tags: []
related: []
created: '2026-04-14'
type: code
epic: epic-code-completion
completion_gates: {code: C4, deployment: none, business: none}
repo_gates:
- {repo: ml-training-service, code: C0, deployment: none, business: none}
- {repo: unified-trading-library, code: C0, deployment: none, business: none}
depends_on: [domain-agnostic-ml-framework]
context: "## Problem\nML training service has full CEFI pipeline but Sports and TradFi are incomplete:\n- Sports: framework layer done (UAC schemas, UTL engines, SportsMLPresets, FamilyRouter) but\n  target builders are minimal, no feature adapter, no --family CLI, no grid configs\n- TradFi: same targets as CEFI (swing_high/swing_low) but market hours filtering not wired\n  automatically, no TradFi grid configs\n- CEFI: mostly complete but cross_venue_spread stub needs verification\n\n## Architecture\n```\nPhase 1 (Sports targets)  ──┐\nPhase 2 (TradFi wiring)  ───┼──> Phase 4 (CLI + grid configs) ──> Phase 5 (E2E tests)\nPhase 3 (Feature adapter) ──┘\n```\nPhases 1-3 are PARALLEL. Phase 4 depends on all three. Phase 5 is final validation.\n\n## Existing Infrastructure\n- target_generator_factory.py: routes swing_high/low, clv, xg, ht_delta, cross_venue_spread\n- sports_target_generator.py: CLVTargetGenerator, XGTargetGenerator, HTDeltaTargetGenerator (minimal)\n- cloud_feature_provider.py:\
  \ _get_category() handles CEFI/TRADFI/DEFI but NOT SPORTS\n- data_filters.py: filter_market_hours() exists but not auto-invoked for TRADFI\n- config.py: TrainingConfig has CEFI/TRADFI instruments, no sports section\n- config_loader.py: TEST/DEVELOPMENT/PRODUCTION grids for CEFI only\n- family_router.py: routes SPORTS only, returns None for others\n- session_times.py (UAC): is_trading_hours(exchange, dt) for all exchanges\n- InstrumentRecord: regular_open_utc, regular_close_utc, is_trading_day fields\n\n## Pre-Audit Manifest\n| Repo | File | Action |\n|"
---

---|------|--------|
  | ML-svc | app/core/sports_target_generator.py | EXTEND — complete all builders |
  | ML-svc | app/core/target_generator_factory.py | EXTEND — add sports family routing |
  | ML-svc | app/core/cloud_feature_provider.py | EXTEND — add SPORTS category, feature groups |
  | ML-svc | app/core/family_router.py | EXTEND — add TRADFI support |
  | ML-svc | app/core/data_filters.py | VERIFY — market hours filter |
  | ML-svc | app/core/config_loader.py | EXTEND — add sports/tradfi grid presets |
  | ML-svc | config.py | EXTEND — add sports config section |
  | ML-svc | cli/parser.py | EXTEND — add --family arg |
  | ML-svc | cli/handlers/__init__.py | EXTEND — wire family-based dispatch |
  | ML-svc | tests/unit/ | CREATE — tests for all new code |
  | UTL | config_interface/sports_ml_config.py | VERIFY — presets complete |

todos:
  # ─────────────────────────────────────────────────────────────
  # Phase 1: Sports Target Builders (PARALLEL with Phase 2, 3)
  # ─────────────────────────────────────────────────────────────

  - id: p1-sports-targets
    content: |
      - [x] [AGENT] P0. Complete sports target builders in sports_target_generator.py

      Current state: CLVTargetGenerator, XGTargetGenerator, HTDeltaTargetGenerator exist
      with minimal logic (column subtraction, zeros for missing).

      Enhance:
        - CLVTargetGenerator: validate input shape, compute edge_bps not just raw drift,
          support multiple bookmaker columns, return named target columns matching TargetSpec
        - XGTargetGenerator: compute all pregame_xg targets (home_xg, away_xg, total_goals,
          goal_diff, win_flag, draw_flag, loss_flag) from match result columns
        - HTDeltaTargetGenerator: compute all HT targets (ht_goal_diff, ht_total_goals,
          next_goal_team, ht_momentum_shift) from HT + FT data
        - Add MetaTargetBuilder: computes residual and quality targets from OOF predictions
          (bet_quality_score, residual_alpha, model_disagreement)
        - Add SportsTargetOrchestrator: given a family config from SportsMLPresets,
          dispatches to correct builder(s) and returns combined target DataFrame

      All builders must:
        - Accept DataFrame + family_config (or target_names list)
        - Return DataFrame with columns matching TargetSpec.target_name
        - Handle missing columns gracefully (log warning, return NaN column)
        - Be domain-agnostic in interface (family config drives what to build)
    status: done

  - id: p1-sports-targets-tests
    content: |
      - [x] [AGENT] P0. Write tests for sports target builders

      Test file: tests/unit/test_sports_target_builders.py

      Tests with synthetic match data (100-row DataFrames):
        - CLV: drift computation, edge_bps, multiple bookmakers, missing columns
        - XG: all 7 pregame targets from goals, missing columns graceful
        - HTDelta: all 4 HT targets from HT+FT data
        - Meta: residual computation from dummy OOF predictions
        - Orchestrator: routes family config to correct builders, combined output shape

      Must maintain >= 80% coverage.
    status: done

  # ─────────────────────────────────────────────────────────────
  # Phase 2: TradFi Market Hours Integration (PARALLEL)
  # ─────────────────────────────────────────────────────────────

  - id: p2-tradfi-hours
    content: |
      - [x] [AGENT] P0. Wire market hours filtering for TRADFI category

      In training_orchestrator.py or the handler layer:
        - When category=TRADFI, automatically apply filter_market_hours() to features
        - Use is_trading_hours() from UAC session_times for per-row filtering
        - Instrument metadata provides regular_open_utc/regular_close_utc
        - Fallback: use session_times.get_session_times(exchange, date) if no metadata

      In family_router.py:
        - Add TRADFI support: returns FamilyRouter with CEFI-equivalent families
          but with market_hours_filter=True flag
        - TradFi uses same target types (swing_high/swing_low) as CEFI

      In config.py:
        - Add tradfi_market_hours_filter: bool = True (auto-filter for TRADFI)
        - Ensure TRADFI instruments resolve correctly (SPY already in INSTRUMENT_ID_MAP)
    status: done

  - id: p2-tradfi-tests
    content: |
      - [x] [AGENT] P0. Write tests for TradFi market hours integration

      Test file: tests/unit/test_tradfi_market_hours.py

      Tests:
        - filter_market_hours correctly removes non-trading rows for SPY
        - TRADFI category auto-applies market hours filter
        - Weekend/holiday rows filtered
        - Pre-market/post-market handling
        - FamilyRouter returns valid config for TRADFI
    status: done

  # ─────────────────────────────────────────────────────────────
  # Phase 3: Sports Feature Adapter (PARALLEL)
  # ─────────────────────────────────────────────────────────────

  - id: p3-sports-features
    content: |
      - [x] [AGENT] P0. Add sports feature loading to CloudFeatureProvider

      In cloud_feature_provider.py:
        - Add "SPORTS" to _get_category(): detect from instrument_id format
          (sports instruments use ODDS_API:FOOTBALL:*, BETFAIR:*, etc.)
        - Add SPORTS_FEATURE_GROUPS constant (from FSS output):
          team_state, player_state, lineup_state, manager_state, transition_state,
          validity_state, odds_features, derived_features
        - Add _load_sports_features() method: loads from features-sports-{project}/
          by fixture_id and date, not by instrument_id and timeframe
        - Sports data is fixture-based (one row per fixture), not time-series

      In config.py Settings:
        - Add features_sports_bucket_template: str (features-sports-{project_id})
        - Add get_sports_bucket() method
    status: done

  - id: p3-sports-features-tests
    content: |
      - [x] [AGENT] P0. Write tests for sports feature loading

      Test file: tests/unit/test_sports_feature_provider.py

      Tests:
        - _get_category() returns "SPORTS" for sports instrument IDs
        - SPORTS_FEATURE_GROUPS matches SportsMLPresets.feature_groups
        - Sports bucket template resolves correctly
        - Mock GCS loading returns expected DataFrame shape
    status: done

  # ─────────────────────────────────────────────────────────────
  # Phase 4: CLI + Grid Configs + Handler Wiring (SEQUENTIAL after 1-3)
  # ─────────────────────────────────────────────────────────────

  - id: p4-cli-family
    content: |
      - [x] [AGENT] P0. Add --family CLI arg and wire through handlers

      In cli/parser.py:
        - Add --family arg (optional, choices from SportsMLPresets family names)
        - When --asset-group SPORTS: --family is required
        - When --asset-group CEFI/TRADFI: --family is ignored (uses target_types)

      In cli/handlers/__init__.py:
        - _MLTrainingModeHandler.run(): if category=SPORTS, use FamilyRouter
          to get family config, then dispatch to pipeline with family targets
        - Wire FamilyRouter output into TrainingPipelineConfig construction
    status: done

  - id: p4-grid-configs
    content: |
      - [x] [AGENT] P0. Add sports and TradFi grid config presets

      In config_loader.py:
        - SPORTS_TEST_GRID: 1 family (pregame_xg), 2 targets, 10 optuna trials
        - SPORTS_DEVELOPMENT_GRID: 3 families, all targets, 30 trials
        - SPORTS_PRODUCTION_GRID: 5 families, all targets, 50 trials
        - TRADFI_TEST_GRID: SPY only, 1h, swing_high, 2 folds, 10 trials
        - TRADFI_PRODUCTION_GRID: SPY, 1h+4h, both targets, 5 folds, 50 trials

      Sports grids use family dimension instead of instrument dimension.
      TrainingGridConfig may need sports_families field alongside instruments.
    status: done

  - id: p4-tests
    content: |
      - [x] [AGENT] P0. Write tests for CLI + grid configs

      Tests:
        - --family arg parsing and validation
        - Sports grid config total_variants computation
        - TradFi grid config creation
        - Handler dispatch with --asset-group SPORTS --family pregame_xg_family
        - Grid config serialization round-trip
    status: done

  # ─────────────────────────────────────────────────────────────
  # Phase 5: E2E Integration Tests + QG (SEQUENTIAL after Phase 4)
  # ─────────────────────────────────────────────────────────────

  - id: p5-e2e
    content: |
      - [x] [AGENT] P0. Full E2E tests with dummy data for all categories

      Test file: tests/unit/test_pipeline_e2e.py

      Sports E2E:
        - Generate synthetic fixture DataFrame (100 rows, correct feature groups)
        - Generate synthetic odds snapshots for CLV
        - Generate synthetic match results for XG
        - Run SportsTargetOrchestrator for pregame_xg_family
        - Verify target DataFrame has all expected columns
        - Verify FamilyRouter → target builder → feature adapter chain works

      TradFi E2E:
        - Generate synthetic SPY candle data with timestamps
        - Include market hours / non-market hours rows
        - Verify market hours filter removes correct rows
        - Run through target generator (swing_high) with filtered data
        - Verify same pipeline as CEFI but with fewer rows

      CEFI verification:
        - Ensure existing CEFI pipeline still works after all changes
        - No regressions

      Run: cd ml-training-service && bash scripts/quality-gates.sh
      Must maintain >= 80% coverage.
    status: done

  - id: p5-qg
    content: |
      - [x] [AGENT] P0. All quality gates pass

      Repos to verify:
        - ml-training-service: bash scripts/quality-gates.sh (>= 80% coverage)
        - unified-trading-library: bash scripts/quality-gates.sh (>= 65% coverage)

      No regressions in existing tests.
    status: done

isProject: false
---
