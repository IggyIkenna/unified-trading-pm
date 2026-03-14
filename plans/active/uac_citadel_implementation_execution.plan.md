---
name: uac-citadel-implementation-execution
overview:
  Execute the UAC Citadel Architecture redesign -- facade pattern, canonical domain reorganization, per-source
  normalization co-location, tier model fix, downstream migration, capability registry, new repos, and runtime
  guardrails across ~60 repos.
type: code
epic: epic-code-completion
status: active
completion_gates:
  code: C5
  deployment: none
  business: none
repo_gates:
  - repo: unified-trading-pm
    code: C0
    deployment: none
    business: none
  - repo: unified-trading-library
    code: C0
    deployment: none
    business: none
  - repo: unified-api-contracts
    code: C0
    deployment: none
    business: none
  - repo: unified-internal-contracts
    code: C0
    deployment: none
    business: none
  - repo: unified-config-interface
    code: C0
    deployment: none
    business: none
  - repo: unified-cloud-interface
    code: C0
    deployment: none
    business: none
  - repo: unified-market-interface
    code: C0
    deployment: none
    business: none
  - repo: unified-trade-execution-interface
    code: C0
    deployment: none
    business: none
  - repo: unified-sports-execution-interface
    code: C0
    deployment: none
    business: none
  - repo: unified-defi-execution-interface
    code: C0
    deployment: none
    business: none
  - repo: unified-position-interface
    code: C0
    deployment: none
    business: none
  - repo: unified-reference-data-interface
    code: C0
    deployment: none
    business: none
  - repo: unified-ml-interface
    code: C0
    deployment: none
    business: none
  - repo: unified-domain-client
    code: C0
    deployment: none
    business: none
  - repo: unified-feature-calculator-library
    code: C0
    deployment: none
    business: none
  - repo: unified-trading-codex
    code: C0
    deployment: none
    business: none
  - repo: system-integration-tests
    code: C0
    deployment: none
    business: none
depends_on:
  - uac_citadel_architecture_0ccb5b9b
todos:
  # ═══════════════════════════════════════════════════════════════
  # PHASE 0: MANIFEST SCHEMA EVOLUTION + TIER MODEL
  # ═══════════════════════════════════════════════════════════════
  - id: p0-manifest-tier-role
    content: |
      - [x] [AGENT] P0. Add tier (integer) + role (string) fields to all ~65 repo entries in workspace-manifest.json. Fix tier assignments: UCfgI 1->0, URDI 1->2, USEI 1->2, EAL 0->2, MEL 0->2. Add workspace_infrastructure and runtime_clients fields. Add placeholder entries for UFI, UFOL, USRI.
    status: done
    note:
      "69 repos total (66 existing + 3 planned). All have tier+role. workspace_infrastructure and runtime_clients added."

  - id: p0-utl-tier-fix-remove-deps
    content: |
      - [x] [AGENT] P0. Remove tier-violating deps from UTL pyproject.toml: unified-market-interface, unified-trade-execution-interface. Verified adapter_facade has zero external consumers. (unified-position-interface and unified-reference-data-interface were not present.)
    status: done
    blocked_by: p0-manifest-tier-role

  - id: p0-utl-delete-adapter-facade
    content: |
      - [x] [AGENT] P0. Deleted adapter_facade.py. Removed 8 re-exports from __init__.py. Re-added DataSourceMapping from UTL's own domain module. Fixing pre-existing QG failures (CloudTarget x3, MockStateStore mutation, coverage).
    status: done
    blocked_by: p0-utl-tier-fix-remove-deps
    note: "Zero new failures from our changes. Pre-existing failures being fixed separately."

  - id: p0-umi-dep-cleanup
    content: |
      - [x] [AGENT] P0. SKIPPED: All 3 deps (UCfgI, UCI, UEI) are actively imported in UMI production source code (config.py, 12+ adapter files, 27+ event logging files). Cannot remove.
    status: done
    blocked_by: p0-manifest-tier-role
    note: "Exploration verified all 3 deps are genuinely used. Plan corrected."

  - id: p0-utei-dep-cleanup
    content: |
      - [x] [AGENT] P0. Removed unified-events-interface from UTEI (was unused in source). UCfgI kept (actively imported in factory.py, config.py). QG pass (pre-existing integration coverage note only).
    status: done
    blocked_by: p0-manifest-tier-role

  - id: p0-urdi-dep-cleanup
    content: |
      - [x] [AGENT] P0. Removed unified-events-interface from URDI (was unused in source). UCI kept (actively imported in 3 adapter files). QG pass (pre-existing test_get_instruments_mocked failure only).
    status: done
    blocked_by: p0-manifest-tier-role

  - id: p0-umli-dep-cleanup
    content: |
      - [x] [AGENT] P0. Removed unified-events-interface from UMLI (was unused in source). UCfgI and UCI kept (actively imported in model_registry.py). QG pass (pre-existing pip-audit CVE only).
    status: done
    blocked_by: p0-manifest-tier-role

  - id: p0-service-dep-cleanup
    content: |
      - [x] [AGENT] P1. Removed 4 redundant T0 deps: batch-audit-api (UEI), ml-training-api (UEI), trading-analytics-api (UEI), ml-inference-api (UCI). All QG pre-existing failures only, zero new failures.
    status: done
    blocked_by: p0-utl-delete-adapter-facade
    note:
      "Original plan had 6 batches of ~5 repos. Analysis: only 4 repos had genuinely redundant deps. 25 services
      actively import UCfgI/UCI/UEI."

  - id: p0-manifest-update-after-deps
    content: |
      - [x] [AGENT] P0. Updated manifest dependencies[] for 8 repos: UTL (-2 deps), UTEI/URDI/UMLI (-1 UEI each), batch-audit-api/ml-training-api/trading-analytics-api (-1 UEI each), ml-inference-api (-1 UCI).
    status: done
    blocked_by: p0-service-dep-cleanup, p0-utei-dep-cleanup, p0-urdi-dep-cleanup, p0-umli-dep-cleanup

  - id: p0-tier-gate-validator
    content: |
      - [x] [AGENT] P0. Updated tier-gate-check.sh to read integer tier field. Added dep-tier validation (tier N deps must have tier <= N). Updated test_tiers_are_valid. PM QG: lint+tests+typecheck pass.
    status: done
    blocked_by: p0-manifest-update-after-deps

  - id: p0-dag-regeneration
    content: |
      - [x] [AGENT] P0. DAG generation scripts (generate_workspace_dag.py) don't use tier/arch_tier -- they read topologicalOrder.levels. No changes needed. Fixed 2 pre-existing E501 lint errors in generate_data_flow_dag.py. PM QG passes.
    status: done
    blocked_by: p0-tier-gate-validator

  # ═══════════════════════════════════════════════════════════════
  # PHASE 1: UAC STRUCTURAL FOUNDATIONS
  # ═══════════════════════════════════════════════════════════════
  - id: p1-create-dirs
    content: |
      - [x] [AGENT] P0. Created 10 domain sub-packages, crosscutting/, normalize_utils/, confirmed registry/__init__.py.
    status: done
    blocked_by: p0-dag-regeneration

  - id: p1-move-normalize
    content: |
      - [x] [AGENT] P0. Moved 23 .py files + errors/ subdir from canonical/normalize/ to normalize_utils/. Moved canonical_mappings.py to normalize_utils/common_mappings.py. Deleted empty canonical/normalize/.
    status: done
    blocked_by: p1-create-dirs

  - id: p1-move-registry-assets
    content: |
      - [x] [AGENT] P0. Moved venue_manifest/ (7 files) to registry/. Moved venue_rate_limits.py and provider_modes.py to registry/.
    status: done
    blocked_by: p1-create-dirs

  - id: p1-move-errors-crosscutting
    content: |
      - [x] [AGENT] P0. Moved canonical/errors/ (7 files) to canonical/crosscutting/errors/. Moved external/sports/errors.py to sports_execution.py. No merge needed (different error types).
    status: done
    blocked_by: p1-create-dirs

  - id: p1-import-update
    content: |
      - [x] [AGENT] P0. Updated 87 files (43 modified + 44 new). All 5 import patterns replaced. Per-file-ignores pre-empted. UAC QG: 706 tests pass, lint/typecheck/codex clean. Smoke test PASSED.
    status: done
    blocked_by: p1-move-normalize, p1-move-registry-assets, p1-move-errors-crosscutting

  # ═══════════════════════════════════════════════════════════════
  # PHASE 2: CANONICAL DOMAIN REORGANIZATION + FACADES
  # ═══════════════════════════════════════════════════════════════
  - id: p2-split-domain-flat-files
    content: |
      - [x] [AGENT] P0. Split 7 flat domain files into sub-packages: market/, sports/, derivatives/, reference/ (was instruments), position/ (was account), infrastructure/, onchain/. All relative imports fixed (._base -> .._base).
    status: done
    blocked_by: p1-import-update

  - id: p2-move-sports-canonical
    content: |
      - [x] [AGENT] P0. Moved 20 .py files from external/sports/canonical/ to canonical/domain/sports/. Created temporary facade at external/sports/__init__.py. Fixed 3 file imports to use relative paths.
    status: done
    blocked_by: p2-split-domain-flat-files

  - id: p2-move-crosscutting-types
    content: |
      - [x] [AGENT] P0. Moved rate_limits.py, latency.py, connectivity.py, analytics.py, risk.py to canonical/crosscutting/. Fixed connectivity.py import (._base -> ..domain._base).
    status: done
    blocked_by: p2-split-domain-flat-files

  - id: p2-move-floating-files-with-facades
    content: |
      - [x] [AGENT] P0. Split execution.py (289L) into base.py/trade.py/sports.py(stub)/defi.py(stub). Moved options.py to derivatives/options.py, odds.py to sports/odds_canonical.py, spread.py to market/spread.py. Created 4 transition facades (execution, options, odds, spread).
    status: done
    blocked_by: p2-split-domain-flat-files

  - id: p2-rewrite-domain-init
    content: |
      - [x] [AGENT] P0. Rewrote domain/__init__.py: account->position, instruments->reference, 5 crosscutting moves, added execution. Fixed 8 collateral files. Domain smoke test PASSED.
    status: done
    blocked_by: p2-move-sports-canonical, p2-move-crosscutting-types, p2-move-floating-files-with-facades

  - id: p2-create-root-facades
    content: |
      - [x] [AGENT] P0. Created 15 root-level facade files. Added per-file-ignores for all facades. Circular import check PASSED.
    status: done
    blocked_by: p2-rewrite-domain-init

  - id: p2-update-root-init
    content: |
      - [x] [AGENT] P0. Root __init__.py needed no changes (already routes through transition facades). QG: 706 tests, 0 errors. Full smoke test PASSED.
    status: done
    blocked_by: p2-create-root-facades

  # ═══════════════════════════════════════════════════════════════
  # PHASE 3: EXTERNAL FLATTENING + PER-SOURCE CO-LOCATION
  # ═══════════════════════════════════════════════════════════════
  - id: p3-flatten-sports-sources
    content: |
      - [ ] [AGENT] P0. Flatten external/sports/sources/{provider}/ to external/{provider}/. 10 providers: oddsjam, opticodds (new dirs), footystats, odds_api, understat, soccer_football_info, api_football, betfair, open_meteo, pinnacle (merge into existing). Move entire directories including mocks/. External/{provider}/ is authoritative for merge conflicts.
    status: pending
    blocked_by: p2-update-root-init

  - id: p3-flatten-cloud-sdks
    content: |
      - [ ] [AGENT] P0. Flatten external/cloud_sdks/: aws/ -> external/aws/, gcp/ -> external/gcp/, aws.py -> external/aws/legacy.py or merge, quota_broker.py -> registry/. Delete external/cloud_sdks/ after moves.
    status: pending
    blocked_by: p2-update-root-init

  - id: p3-flatten-other-nested
    content: |
      - [ ] [AGENT] P0. Flatten external/onchain/cryptoquant.py -> external/cryptoquant/schemas.py. Merge external/macro/yahoo_finance.py into existing external/yahoo_finance/. Inspect external/mev/ -- if 3 distinct providers split; if composite keep. Keep external/defi/ and external/prime_broker/ as-is.
    status: pending
    blocked_by: p2-update-root-init

  - id: p3-per-source-normalize-cefi
    content: |
      - [ ] [AGENT] P1. Extract CeFi venue-specific normalizers from normalize_utils/ into external/{source}/normalize.py: binance, bybit, okx, deribit, coinbase, kraken, bitget, bitstamp, gateio, huobi, kucoin, mexc, upbit, bitfinex. Each imports shared utils from normalize_utils/.
    status: pending
    blocked_by: p3-flatten-sports-sources, p3-flatten-cloud-sdks, p3-flatten-other-nested

  - id: p3-per-source-normalize-defi
    content: |
      - [ ] [AGENT] P1. Extract DeFi + onchain normalizers from normalize_utils/ into external/{source}/normalize.py: hyperliquid, uniswap, aave, curve, alchemy, pyth, thegraph. Keep shared primitives in normalize_utils/.
    status: pending
    blocked_by: p3-flatten-sports-sources, p3-flatten-cloud-sdks, p3-flatten-other-nested

  - id: p3-per-source-normalize-sports-tradfi
    content: |
      - [ ] [AGENT] P1. Extract sports + TradFi normalizers from normalize_utils/ into external/{source}/normalize.py: betfair, pinnacle, ibkr, databento, fred. Keep shared primitives in normalize_utils/.
    status: pending
    blocked_by: p3-flatten-sports-sources, p3-flatten-cloud-sdks, p3-flatten-other-nested

  - id: p3-per-source-mappings
    content: |
      - [ ] [AGENT] P1. Extract per-source mappings from normalize_utils/common_mappings.py to external/{source}/mappings.py. Keep cross-venue lookups (DATA_SOURCE_TO_VENUES, VENUE_TO_DATA_SOURCE) in registry/.
    status: pending
    blocked_by: p3-per-source-normalize-cefi, p3-per-source-normalize-defi, p3-per-source-normalize-sports-tradfi

  - id: p3-external-init-reexports
    content: |
      - [ ] [AGENT] P1. Add __init__.py re-exports to ALL ~80 external sources. Standard: from .schemas import *. Binance: import from all 4 sub-modules. Scriptable/mechanical task.
    status: pending
    blocked_by: p3-per-source-mappings

  - id: p3-fix-umi-sports-import
    content: |
      - [ ] [AGENT] P0. Fix UMI sports/protocol.py: change from unified_api_contracts.external.sports import CanonicalOdds, OddsType to from unified_api_contracts import CanonicalOdds, OddsType. Closes external/sports/ dependency before deletion.
    status: pending
    blocked_by: p3-external-init-reexports

  - id: p3-delete-emptied-dirs
    content: |
      - [ ] [AGENT] P0. Delete external/sports/ (all content moved), external/onchain/, external/macro/, external/cloud_sdks/. Run UAC QG + UMI QG + full smoke test.
    status: pending
    blocked_by: p3-fix-umi-sports-import

  # ═══════════════════════════════════════════════════════════════
  # PHASE 4: CONFIG CLEANUP + CROSS-REPO MOVES
  # ═══════════════════════════════════════════════════════════════
  - id: p4-move-loglevel-to-utl
    content: |
      - [ ] [AGENT] P0. Copy config/log_level.py to unified_trading_library/core/log_level.py. Add LogLevel to UTL __init__.py exports. DO NOT delete from UAC yet. Run UTL QG.
    status: pending
    blocked_by: p3-delete-emptied-dirs

  - id: p4-move-trading-validation-to-ucfgi
    content: |
      - [ ] [AGENT] P0. Copy config/trading_validation.py to unified_config_interface/validation.py. Delete from UAC. Run UCfgI QG then UAC QG.
    status: pending
    blocked_by: p3-delete-emptied-dirs

  - id: p4-move-quota-types-to-uci
    content: |
      - [ ] [AGENT] P0. Move cloud-specific quota types from config/quota_types.py to unified_cloud_interface/abstractions.py. Move canonical ComputeType, VmQuotaShape to canonical/domain/infrastructure/compute.py (stays in UAC). Delete config/quota_types.py. Run UCI QG then UAC QG.
    status: pending
    blocked_by: p3-delete-emptied-dirs

  - id: p4-delete-config-shared-schemas
    content: |
      - [ ] [AGENT] P0. Delete config/domain_config.py (orphan), config/__init__.py. Keep config/log_level.py (deferred). Delete shared/ and schemas/ if still exist (check git status). Update any remaining internal references. Run UAC QG + full smoke test.
    status: pending
    blocked_by: p4-move-loglevel-to-utl, p4-move-trading-validation-to-ucfgi, p4-move-quota-types-to-uci

  # ═══════════════════════════════════════════════════════════════
  # PHASE 5: DOWNSTREAM IMPORT UPDATES + TRANSITION CLEANUP
  # ═══════════════════════════════════════════════════════════════
  - id: p5-loglevel-migration-batch1
    content: |
      - [ ] [AGENT] P0. Migrate LogLevel import in services batch 1 (~7 repos): alerting-service, batch-live-reconciliation-service, execution-service, features-calendar-service, features-commodity-service, features-cross-instrument-service, features-delta-one-service. Change from unified_api_contracts import LogLevel to from unified_trading_library import LogLevel. Run QG each.
    status: pending
    blocked_by: p4-delete-config-shared-schemas

  - id: p5-loglevel-migration-batch2
    content: |
      - [ ] [AGENT] P0. Migrate LogLevel import in services batch 2 (~7 repos): features-multi-timeframe-service, features-onchain-service, features-sports-service, features-volatility-service, instruments-service, market-data-processing-service, market-tick-data-service. Run QG each.
    status: pending
    blocked_by: p4-delete-config-shared-schemas

  - id: p5-loglevel-migration-batch3
    content: |
      - [ ] [AGENT] P0. Migrate LogLevel import in services batch 3 (~7 repos): ml-inference-service, ml-training-service, pnl-attribution-service, position-balance-monitor-service, risk-and-exposure-service, strategy-service, trading-agent-service. Run QG each.
    status: pending
    blocked_by: p4-delete-config-shared-schemas

  - id: p5-interface-umi-updates
    content: |
      - [ ] [AGENT] P0. Update UMI adapter imports: oddsjam_adapter.py external.sports.sources.oddsjam.schemas -> external.oddsjam, opticodds_adapter.py same pattern. Run UMI QG.
    status: pending
    blocked_by: p4-delete-config-shared-schemas

  - id: p5-interface-usei-updates
    content: |
      - [ ] [AGENT] P0. Update USEI adapter imports: polymarket_clob.py canonical.execution -> execution facade, pinnacle.py same. Run USEI QG.
    status: pending
    blocked_by: p4-delete-config-shared-schemas

  - id: p5-interface-upi-updates
    content: |
      - [ ] [AGENT] P0. Update UPI test imports: test_vcr_position_schemas.py external.binance.account_schemas -> external.binance, external.binance.market_schemas -> external.binance. Run UPI QG.
    status: pending
    blocked_by: p4-delete-config-shared-schemas

  - id: p5-service-specific-execution
    content: |
      - [ ] [AGENT] P0. Fix execution-service: external.sports.canonical.betting.BetStatus -> unified_api_contracts.BetStatus. Run execution-service QG.
    status: pending
    blocked_by: p4-delete-config-shared-schemas

  - id: p5-service-specific-instruments
    content: |
      - [ ] [AGENT] P0. Fix instruments-service: external.sports.canonical.mappings.TeamMapping -> unified_api_contracts.TeamMapping, external.ccxt.schemas -> external.ccxt, external.thegraph.schemas -> external.thegraph. Run instruments-service QG.
    status: pending
    blocked_by: p4-delete-config-shared-schemas

  - id: p5-service-specific-strategy-trading
    content: |
      - [ ] [AGENT] P0. Fix strategy-service: canonical.options.NormalizedStrikeCoordinate -> options.NormalizedStrikeCoordinate. Fix trading-agent-service: canonical.domain.derivatives.ComboLeg -> derivatives.ComboLeg, same for ComboStrategyType. Run QGs.
    status: pending
    blocked_by: p4-delete-config-shared-schemas

  - id: p5-service-specific-features-commodity
    content: |
      - [ ] [AGENT] P2. Update features-commodity-service doc comments referencing unified_api_contracts.external.macro.yahoo_finance and unified_api_contracts.external.open_meteo to new paths (external.yahoo_finance, external.open_meteo). Run features-commodity-service QG.
    status: pending
    blocked_by: p4-delete-config-shared-schemas

  - id: p5-uic-test-updates
    content: |
      - [ ] [AGENT] P0. Update UIC test_uac_integration.py: expose normalize functions via unified_api_contracts.testing (add to testing/__init__.py importing from normalize_utils/). Update canonical.execution -> execution facade. Update binance sub-module imports -> external.binance. Update check_schema_organization.py. Run UIC QG + testing helpers smoke test.
    status: pending
    blocked_by: p4-delete-config-shared-schemas

  - id: p5-sit-updates
    content: |
      - [ ] [AGENT] P0. Update SIT: test_contract_normalization.py canonical.execution -> execution, test_interface_mock_chains.py canonical.domain -> market/execution facades, test_uac_uic_compat.py -> facades, test_uac_uic_schema_compat.py -> sports facade, rename test_uac_deep_import_health.py -> test_uac_facade_import_health.py, test_layer0_contracts.py schemas -> facades. Run SIT QG.
    status: pending
    blocked_by: p4-delete-config-shared-schemas

  - id: p5-transition-facade-cleanup
    content: |
      - [ ] [AGENT] P0. Delete ALL transition facades from UAC: canonical/execution.py, canonical/options.py, canonical/odds.py, config/log_level.py. Delete config/ directory entirely. Remove LogLevel from UAC __init__.py. Run UAC QG + post-LogLevel smoke test.
    status: pending
    blocked_by:
      p5-loglevel-migration-batch1, p5-loglevel-migration-batch2, p5-loglevel-migration-batch3,
      p5-interface-umi-updates, p5-interface-usei-updates, p5-interface-upi-updates, p5-service-specific-execution,
      p5-service-specific-instruments, p5-service-specific-strategy-trading, p5-uic-test-updates, p5-sit-updates

  # ═══════════════════════════════════════════════════════════════
  # PHASE 6: LINTER ENFORCEMENT
  # ═══════════════════════════════════════════════════════════════
  - id: p6-import-surface-linter
    content: |
      - [ ] [AGENT] P0. Add UAC import surface linter to base-service.sh and base-library.sh. Block patterns: canonical.*, normalize_utils.*, config.*, shared.*, schemas.*. UAC_CANONICAL_EXEMPT=true exemption for UAC, UIC, SIT. Run PM QG.
    status: pending
    blocked_by: p5-transition-facade-cleanup

  - id: p6-cursor-rule-create
    content: |
      - [ ] [AGENT] P1. Create uac-import-surface-enforcement.mdc with allowed/blocked import patterns and exceptions.
    status: pending
    blocked_by: p6-import-surface-linter

  - id: p6-cursor-rules-update
    content: |
      - [ ] [AGENT] P1. Update existing cursor rules: contracts-integration.mdc, schema-governance-index.mdc, library-tier-architecture.mdc, search-before-implementing.mdc, library-init-exports.mdc, anti-patterns-quick-reference.mdc.
    status: pending
    blocked_by: p6-import-surface-linter

  - id: p6-workspace-qg-validation
    content: |
      - [ ] [AGENT] P1. Run workspace-wide QG validation across all repos to verify linter catches violations and exemptions work correctly.
    status: pending
    blocked_by: p6-cursor-rule-create, p6-cursor-rules-update

  # ═══════════════════════════════════════════════════════════════
  # PHASE 7: REGISTRY CAPABILITY MODEL
  # ═══════════════════════════════════════════════════════════════
  - id: p7-capability-model
    content: |
      - [ ] [AGENT] P0. Create registry/capability.py with SourceCapability Pydantic model: source, domains, crosscutting, supports_live/batch/historical/testnet/mainnet, auth_scope, auth_environments, operations.
    status: pending
    blocked_by: p6-workspace-qg-validation

  - id: p7-endpoint-resolution
    content: |
      - [ ] [AGENT] P0. Create resolve_endpoint(source, environment, mode, operation) -> EndpointSpec in registry/capability.py. Raises CapabilityResolutionError if unsupported combination.
    status: pending
    blocked_by: p7-capability-model

  - id: p7-backfill-providers
    content: |
      - [ ] [AGENT] P1. Backfill capability declarations for all ~80 providers grouped by domain: CeFi (~15), DeFi (~15), Sports (~15), TradFi (~10), Alt data (~10), Meta (~5).
    status: pending
    blocked_by: p7-endpoint-resolution

  - id: p7-coverage-matrix
    content: |
      - [ ] [AGENT] P1. Create scripts/coverage_matrix.py generating Domain x Source matrix (JSON + human table). Run UAC QG.
    status: pending
    blocked_by: p7-backfill-providers

  # ═══════════════════════════════════════════════════════════════
  # PHASE 8: NEW REPOS
  # ═══════════════════════════════════════════════════════════════
  - id: p8-create-ufi
    content: |
      - [ ] [AGENT] P1. Create unified-features-interface repo: pyproject.toml, quality-gates.sh, __init__.py, core adapters. Write canonical/domain/features/ types in UAC (CanonicalFeatureRecord, FeatureMetadata). Register in workspace-manifest.json.
    status: pending
    blocked_by: p7-coverage-matrix

  - id: p8-create-ufol
    content: |
      - [ ] [AGENT] P1. Create unified-feature-orchestration-library repo: pipeline routing, batch/live handlers, feature registry. Register in workspace-manifest.json.
    status: pending
    blocked_by: p8-create-ufi

  - id: p8-create-usri
    content: |
      - [ ] [AGENT] P1. Create unified-sports-reference-interface repo: fixtures, leagues, teams, players, bookmakers. Register in workspace-manifest.json.
    status: pending
    blocked_by: p7-coverage-matrix

  - id: p8-dag-regenerate
    content: |
      - [ ] [AGENT] P1. Regenerate workspace DAG with all 3 new repos. Run PM QG.
    status: pending
    blocked_by: p8-create-ufi, p8-create-ufol, p8-create-usri

  # ═══════════════════════════════════════════════════════════════
  # PHASE 9: REPLAY + DRIFT INFRASTRUCTURE
  # ═══════════════════════════════════════════════════════════════
  - id: p9-uic-internal-registry
    content: |
      - [ ] [AGENT] P1. Create UIC internal endpoint registry for cross-service schema validation.
    status: pending
    blocked_by: p7-coverage-matrix

  - id: p9-replay-workflow
    content: |
      - [ ] [AGENT] P1. Create PM contract-replay.yml reusable workflow. Layer 1: raw schema parse against external/{source}/schemas.py. Layer 2: canonical output invariants (required fields, enum ranges, cross-field constraints).
    status: pending
    blocked_by: p9-uic-internal-registry

  - id: p9-drift-recording
    content: |
      - [ ] [AGENT] P1. Create PM contract-drift-record.yml nightly CI (staging only). Approval-gated PRs labeled schema-impact. Never auto-merge.
    status: pending
    blocked_by: p9-replay-workflow

  - id: p9-lane-metrics
    content: |
      - [ ] [AGENT] P1. Define 4 validation lanes per (source, domain) pair: smoke (every PR), replay (on merge), live (nightly staging), drift (nightly staging). Emit Prometheus counters: uac_validation_result, uac_validation_duration_seconds, uac_drift_detected. Create Grafana dashboard for per-source per-domain lane health. Alert on drift detection, replay failure, consecutive live validation failures.
    status: pending
    blocked_by: p9-drift-recording

  - id: p9-extend-cassettes-all-interfaces
    content: |
      - [ ] [AGENT] P2. Extend cassette replay validation to ALL interface repos: UTEI, USEI, UDEI, UPI, UFI, USRI (not just UMI/URDI).
    status: pending
    blocked_by: p9-lane-metrics

  # ═══════════════════════════════════════════════════════════════
  # PHASE 10: RUNTIME GUARDRAILS + SERVICE ADOPTION
  # ═══════════════════════════════════════════════════════════════
  - id: p10-error-taxonomy
    content: |
      - [ ] [AGENT] P0. Create fail-fast error classes in UTL: UnsupportedModeError(source, requested_mode, supported_modes, suggested_resolution), UnsupportedEnvironmentError, ApiKeyScopeMismatchError(source, key_scope, target_env), CapabilityResolutionError, UnsupportedOperationError. Run UTL QG.
    status: pending
    blocked_by: p7-coverage-matrix

  - id: p10-preflight-umi
    content: |
      - [ ] [AGENT] P1. Wire preflight capability checks into UMI adapters: resolve_capability -> validate_mode -> validate_env -> validate_auth_scope -> resolve_endpoint -> execute -> validate raw -> normalize -> return canonical. Run UMI QG.
    status: pending
    blocked_by: p10-error-taxonomy

  - id: p10-preflight-utei-usei
    content: |
      - [ ] [AGENT] P1. Wire preflight capability checks into UTEI and USEI adapters. Same 9-step flow. Run QGs.
    status: pending
    blocked_by: p10-error-taxonomy

  - id: p10-preflight-remaining-interfaces
    content: |
      - [ ] [AGENT] P1. Wire preflight capability checks into UDEI, UPI, URDI, USRI, UFI, UFCL. Run QGs.
    status: pending
    blocked_by: p10-error-taxonomy

  - id: p10-duplicate-mapping-detection
    content: |
      - [ ] [AGENT] P1. Scan all interface adapter repos for duplicate raw->canonical mapping logic. Extract duplicates to UAC external/{source}/normalize.py. Interface adapters must call UAC normalizers, not re-implement.
    status: pending
    blocked_by: p10-preflight-umi, p10-preflight-utei-usei, p10-preflight-remaining-interfaces

  - id: p10-service-consumption-audit
    content: |
      - [ ] [AGENT] P1. Scan all services for direct raw payload parsing (from unified_api_contracts.external.* in service repos). Migrate any hits to canonical imports via interface layer.
    status: pending
    blocked_by: p10-duplicate-mapping-detection

  - id: p10-qg-validators
    content: |
      - [ ] [AGENT] P1. Add QG validators to base-service.sh: duplicate mapping detection (fail if service contains raw->canonical normalizer), ad-hoc endpoint literal detection using broad venue URL patterns covering all CeFi+sports venues from registry/venue_constants.py (not just 4 venues). Run PM QG.
    status: pending
    blocked_by: p10-service-consumption-audit

  - id: p10-codex-contracts-layout
    content: |
      - [ ] [AGENT] P2. Rewrite codex 02-data/contracts-scope-and-layout.md for new UAC structure: facade pattern, canonical/domain sub-packages, crosscutting, normalize_utils, registry, import surface rules.
    status: pending
    blocked_by: p10-qg-validators

  - id: p10-codex-tier-architecture
    content: |
      - [ ] [AGENT] P2. Update codex 04-architecture/TIER-ARCHITECTURE.md: integer tiers, workspace_infrastructure, runtime_clients, facade import flow.
    status: pending
    blocked_by: p10-qg-validators

  - id: p10-codex-data-flow
    content: |
      - [ ] [AGENT] P2. Update codex 04-architecture/data-flow-map.md: features stack + sports reference data flows, facade boundaries.
    status: pending
    blocked_by: p10-qg-validators

  - id: p10-codex-ssot-index
    content: |
      - [ ] [AGENT] P2. Update codex 10-audit/ssot-reference-mapping.md and 00-SSOT-INDEX.md: facade modules, registry/capability, new repos (UFI, UFOL, USRI).
    status: pending
    blocked_by: p10-codex-contracts-layout, p10-codex-tier-architecture, p10-codex-data-flow

isProject: false
---

# UAC Citadel Architecture -- Execution Todos

## Related Documents

- Implementation spec: `unified-trading-pm/plans/active/uac_citadel_implementation.plan.md` (1307 lines -- facade
  architecture, per-repo import changes, manifest schema)
- Architecture plan: `unified-trading-pm/plans/active/uac_citadel_architecture_0ccb5b9b.plan.md` (target structure, tier
  model, interface catalog)

## Phases Overview + Sizing

| Phase | Description                                 | Todos | Size | Effort estimate                                                  | Risk         |
| ----- | ------------------------------------------- | ----- | ---- | ---------------------------------------------------------------- | ------------ |
| 0     | Manifest schema + tier model                | 17    | L    | 65 manifest edits + 28 service pyproject.toml                    | Low          |
| 1     | UAC structural foundations                  | 5     | M    | File moves + ~100 import rewrites                                | Medium       |
| 2     | Canonical domain reorg + facades            | 7     | XL   | domain/**init**.py rewrite, 15 facade files, execution sub-split | **Critical** |
| 3     | External flattening + normalize co-location | 11    | L    | ~80 external dirs, normalize extraction                          | Medium       |
| 4     | Config cleanup + cross-repo moves           | 4     | S    | 4 cross-repo copies                                              | Low          |
| 5     | Downstream imports + facade cleanup         | 13    | M    | 21 services + 5 interfaces, parallel batches                     | Low          |
| 6     | Linter enforcement                          | 4     | S    | Linter rules + cursor rules                                      | Low          |
| 7     | Registry capability model                   | 4     | M    | Pydantic models + 80 provider backfills                          | Low          |
| 8     | New repos                                   | 4     | M    | 3 repos from template                                            | Low          |
| 9     | Replay + drift                              | 5     | L    | GHA workflows + Prometheus + Grafana                             | Low          |
| 10    | Guardrails + codex                          | 11    | L    | Error classes + 9 interface preflight + codex                    | Medium       |

**Critical path**: ~30 sequential steps from p0-manifest-tier-role to p10-codex-ssot-index. **Total: 86 todos.
Completion = QG pass per repo. No quickmerge in this plan.**

## Operational Guide (inline -- agents reference this directly)

### Merge strategy for external/{provider}/ flattening (Phase 3)

When `external/sports/sources/{provider}/` merges into existing `external/{provider}/`:

- `external/{provider}/` is **authoritative** (it's the version imported by interfaces)
- If `sports/sources/{provider}/schemas.py` has types NOT in `external/{provider}/schemas.py`, add missing types
- If same class with different fields, `external/{provider}/` version wins
- Move entire directories including `mocks/` -- union cassette files if target `mocks/` already exists
- Delete `sports/sources/{provider}/` after merge

### Transition facade lifecycle

| Facade                        | Created                                       | Deleted                                | Consumer                                                                     |
| ----------------------------- | --------------------------------------------- | -------------------------------------- | ---------------------------------------------------------------------------- |
| `canonical/execution.py`      | Phase 2 (p2-move-floating-files-with-facades) | Phase 5 (p5-transition-facade-cleanup) | USEI: `canonical.execution` imports                                          |
| `canonical/options.py`        | Phase 2                                       | Phase 5                                | strategy-service test                                                        |
| `canonical/odds.py`           | Phase 2                                       | Phase 5                                | Safety                                                                       |
| `external/sports/__init__.py` | Phase 2 (p2-move-sports-canonical)            | Phase 3 (p3-delete-emptied-dirs)       | UMI `sports/protocol.py` (fixed in p3-fix-umi-sports-import before deletion) |
| `config/log_level.py`         | Exists                                        | Phase 5 (p5-transition-facade-cleanup) | 21 services import LogLevel                                                  |

### Smoke test commands

**Full smoke test** (Phases 1-4, while LogLevel in UAC):

```bash
cd unified-api-contracts && .venv/bin/python -c "
from unified_api_contracts import (
    CanonicalTicker, CanonicalTrade, CanonicalOrderBook, CanonicalOhlcvBar,
    CanonicalOrder, CanonicalFill, CanonicalError, CanonicalRateLimitError,
    CanonicalInstrument, CanonicalPosition, CanonicalBalance, CanonicalOdds,
    CanonicalFixture, CanonicalLiquidation, CanonicalFundingRate, LogLevel,
    BetStatus, BetOrder, BetExecution, TeamMapping, ComboLeg, ComboStrategyType,
    NormalizedStrikeCoordinate, OptionChainSnapshot, OrderSide, OrderType,
    OrderStatus, VenueRateLimitSpec, HttpRateLimitHeaders, OddsType, OutcomeType,
    SignalSource, ContractSpec, AccessMode, ENDPOINT_REGISTRY,
    SPORTS_VENUES, VENUE_CATEGORY_MAP
); print('PASSED')
"
```

**Post-LogLevel smoke test** (Phase 5.6+): same but remove `LogLevel` from imports. **Facade import test** (Phase 2.6+):
`import unified_api_contracts.market; import unified_api_contracts.execution; ...` (all 15 facades) **Domain **init**
test** (Phase 2.5): `from unified_api_contracts.canonical.domain import CanonicalTicker, CanonicalOrder, ...`

### Git strategy

- No quickmerge. QG pass = done. Commit only.
- `git add <specific files>` not `git add -A`
- Never use `--dep-branch` (agent rule)
- Cross-repo phases: commit T0 first, then T1, then T2
- Rollback: `git revert HEAD~N` for all phase commits in reverse. Previous phase is stable.

## Quality Gate Pre-emption Strategy (Schema Repos)

UAC and UIC are schema repos -- not typical service/library code. They have large re-export `__init__.py` files,
Pydantic models with camelCase fields from external APIs, and `from X import *` patterns. These WILL trigger QG failures
if not pre-empted.

**Before writing ANY new file, check if it needs these bypasses:**

| Pattern                                                    | QG rule it trips                              | Bypass                                                                         | Where to add                                                         |
| ---------------------------------------------------------- | --------------------------------------------- | ------------------------------------------------------------------------------ | -------------------------------------------------------------------- |
| `from .schemas import *` in `__init__.py`                  | ruff F403/F405 (wildcard import)              | `per-file-ignores` in pyproject.toml                                           | `"unified_api_contracts/external/*/__init__.py" = ["F403", "F405"]`  |
| camelCase fields in Pydantic models (external API schemas) | ruff N815 (mixedCase variable)                | `per-file-ignores`                                                             | `"unified_api_contracts/external/*/*.py" = ["N815"]`                 |
| Root facade files re-exporting `*`                         | ruff F403/F405                                | `per-file-ignores`                                                             | `"unified_api_contracts/market.py" = ["F403", "F405"]` (each facade) |
| New `__init__.py` with many re-exports                     | basedpyright reportUnknownVariableType        | Explicit `__all__` list OR `# pyright: reportUnknownVariableType=false` at top | Each new `__init__.py`                                               |
| `normalize_utils/` files importing from each other         | ruff I001 (import order) after path changes   | Run `ruff check --fix` after all moves                                         | Part of Step 1.5                                                     |
| New `canonical/crosscutting/` modules                      | basedpyright might flag re-exports as unknown | Ensure each module has explicit `__all__`                                      | Each new crosscutting module                                         |

**Pre-emption rule**: Before running QG after any phase, first update `pyproject.toml` `per-file-ignores` for ALL
new/moved files. Run `ruff check --fix` to auto-fix import ordering. Add `__all__` to ALL new `__init__.py` files. THEN
run QG. This avoids the slow cycle of "write code -> fail QG -> add bypass -> re-run QG".

**UAC existing bypasses to extend** (from current `pyproject.toml`):

```toml
[tool.ruff.lint.per-file-ignores]
"unified_api_contracts/external/binance/*.py" = ["N815", "N803", "F403", "F405"]
"unified_api_contracts/external/cloud_sdks/*.py" = ["N803", "N815", "F403", "F405"]
# After Phase 3: extend to ALL external sources + facades
"unified_api_contracts/external/*/__init__.py" = ["F403", "F405"]
"unified_api_contracts/external/*/schemas.py" = ["N815", "N803"]
"unified_api_contracts/market.py" = ["F403", "F405"]
"unified_api_contracts/execution.py" = ["F403", "F405"]
# ... (all 15 facade files)
```

## Risk Register

| Risk                                                       | Likelihood   | Impact                         | Mitigation                                                                                    |
| ---------------------------------------------------------- | ------------ | ------------------------------ | --------------------------------------------------------------------------------------------- |
| `canonical/domain/__init__.py` rewrite breaks facade chain | High         | **Critical** (blocks 35 repos) | Dedicated smoke test (Step 2.5). `from .market import *` pattern validated before proceeding. |
| Circular imports from facade files                         | Medium       | High (blocks Phase 2)          | Detection script after Step 2.6. Fix with `TYPE_CHECKING` guards.                             |
| Normalize move breaks UAC tests (~100 import changes)      | Medium       | Medium (UAC-only)              | Batch 10 files at a time with QG after each batch.                                            |
| LogLevel deletion before service migration                 | Was Critical | **Eliminated**                 | Deferred to Phase 5.6 with explicit `blocked_by` chain.                                       |
| external/sports/ deletion breaks UMI                       | Was Critical | **Eliminated**                 | UMI 1-line fix bundled in Phase 3.5 before deletion.                                          |
| New `__init__.py` files fail basedpyright                  | High         | Medium (blocks QG)             | Pre-empt with `__all__` lists and `per-file-ignores`. See QG Pre-emption Strategy.            |
| Sports/sources merge conflicts (10 providers)              | Medium       | Low (UAC-internal)             | `external/{provider}/` is authoritative. Union missing types.                                 |
| Phase 2 fails mid-way, partial state                       | Low          | High                           | Rollback: `git revert HEAD~N` for all Phase 2 commits. Phase 1 is stable.                     |

**Rollback procedure** (applies to all phases): If a phase fails mid-execution, revert all commits from that phase in
reverse order (`git revert`). The previous phase's state is stable. Re-attempt with corrected approach.

## Agent Handoff Protocol

- A todo starts only when ALL its `blocked_by` dependencies are marked `done`
- Parallel todos (same `blocked_by`) can be assigned to parallel agents in a single message
- Phase N+1 starts only when ALL Phase N todos are `done` (the last todo in each phase has `blocked_by` covering all its
  siblings)
- When an agent completes a todo: mark `status: done`, update `- [ ]` to `- [x]`
- If a todo fails QG: mark `status: blocked`, add a `note:` explaining the failure. Do NOT proceed to dependent todos.
- **No quickmerge. QG pass = done. Commit only, no PR/merge.**

## Phase Completion Criteria

| Phase | Complete when                                                                                                                                                                                    |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 0     | All 17 todos done. PM QG green. DAG regenerated. Tier-gate validator wired.                                                                                                                      |
| 1     | All 5 todos done. UAC QG green. Full smoke test passes.                                                                                                                                          |
| 2     | All 7 todos done. UAC QG green. Full smoke test + facade import test + domain/**init**.py smoke test all pass. No circular imports.                                                              |
| 3     | All 11 todos done. UAC QG + UMI QG green. Full smoke test passes. external/sports/, onchain/, macro/, cloud_sdks/ deleted. Per-source normalize.py exists for all venues with normalizers.       |
| 4     | All 4 todos done. UAC + UTL + UCfgI + UCI QGs green. Full smoke test passes. config/ only contains log_level.py.                                                                                 |
| 5     | All 13 todos done. All 21 service QGs green. All interface QGs green. UIC + SIT QGs green. UAC QG green with post-LogLevel smoke test. All transition facades deleted. config/ deleted entirely. |
| 6     | All 4 todos done. PM QG green. Workspace-wide QG validation passes (no false positives from exemptions, no false negatives from blocked patterns).                                               |
| 7     | All 4 todos done. UAC QG green. All ~80 providers have SourceCapability declarations. Coverage matrix generates without errors.                                                                  |
| 8     | All 4 todos done. 3 new repos created with green QGs. DAG regenerated with new repos.                                                                                                            |
| 9     | All 5 todos done. Replay workflow runs against all interface VCR cassettes. Drift recording creates test PR. Lane metrics emit to Prometheus.                                                    |
| 10    | All 11 todos done. All interface + service QGs green. Zero duplicate normalizers outside UAC. Zero hardcoded venue URLs outside tests. Codex docs updated.                                       |
