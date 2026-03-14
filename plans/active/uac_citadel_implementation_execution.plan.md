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
      - [ ] [AGENT] P0. Add tier (integer) + role (string) fields to all ~65 repo entries in workspace-manifest.json. Fix tier assignments: UCfgI 1->0, URDI 1->2, USEI 1->2, EAL 0->2, MEL 0->2. Add workspace_infrastructure and runtime_clients fields. Add placeholder entries for UFI, UFOL, USRI.
    status: pending

  - id: p0-utl-tier-fix-remove-deps
    content: |
      - [ ] [AGENT] P0. Remove tier-violating deps from UTL pyproject.toml: unified-market-interface, unified-trade-execution-interface, unified-position-interface, unified-reference-data-interface. Verify with rg that adapter_facade has zero external consumers.
    status: pending
    blocked_by: p0-manifest-tier-role

  - id: p0-utl-delete-adapter-facade
    content: |
      - [ ] [AGENT] P0. Delete unified_trading_library/core/adapter_facade.py (30 lines). Remove adapter_facade re-exports from UTL __init__.py. Run UTL quality gates.
    status: pending
    blocked_by: p0-utl-tier-fix-remove-deps

  - id: p0-umi-dep-cleanup
    content: |
      - [ ] [AGENT] P0. Remove unified-config-interface, unified-cloud-interface, unified-events-interface from UMI pyproject.toml. UEI removal is dep graph simplification (not tier fix). Run UMI quality gates -- if fails, keep failing dep.
    status: pending
    blocked_by: p0-manifest-tier-role

  - id: p0-utei-dep-cleanup
    content: |
      - [ ] [AGENT] P0. Remove unified-config-interface from UTEI pyproject.toml. Run UTEI quality gates.
    status: pending
    blocked_by: p0-manifest-tier-role

  - id: p0-urdi-dep-cleanup
    content: |
      - [ ] [AGENT] P0. Remove unified-cloud-interface from URDI pyproject.toml. Run URDI quality gates.
    status: pending
    blocked_by: p0-manifest-tier-role

  - id: p0-umli-dep-cleanup
    content: |
      - [ ] [AGENT] P0. Verify unified-config-interface, unified-cloud-interface exist in UMLI pyproject.toml deps before removing. Remove if present. Run UMLI quality gates.
    status: pending
    blocked_by: p0-manifest-tier-role

  - id: p0-service-dep-cleanup-batch1
    content: |
      - [ ] [AGENT] P1. Remove explicit UCfgI/UCI/UEI deps from services batch 1 (~5 repos): alerting-service, batch-audit-api, client-reporting-api, deployment-api, execution-results-api. Per service: edit pyproject.toml -> run QG -> if fails keep dep.
    status: pending
    blocked_by: p0-utl-delete-adapter-facade

  - id: p0-service-dep-cleanup-batch2
    content: |
      - [ ] [AGENT] P1. Remove explicit UCfgI/UCI/UEI deps from services batch 2 (~5 repos): execution-service, features-calendar-service, features-commodity-service, features-cross-instrument-service, features-delta-one-service.
    status: pending
    blocked_by: p0-utl-delete-adapter-facade

  - id: p0-service-dep-cleanup-batch3
    content: |
      - [ ] [AGENT] P1. Remove explicit UCfgI/UCI/UEI deps from services batch 3 (~5 repos): features-multi-timeframe-service, features-onchain-service, features-sports-service, features-volatility-service, instruments-service.
    status: pending
    blocked_by: p0-utl-delete-adapter-facade

  - id: p0-service-dep-cleanup-batch4
    content: |
      - [ ] [AGENT] P1. Remove explicit UCfgI/UCI/UEI deps from services batch 4 (~5 repos): market-data-api, market-data-processing-service, market-tick-data-service, ml-inference-api, ml-inference-service.
    status: pending
    blocked_by: p0-utl-delete-adapter-facade

  - id: p0-service-dep-cleanup-batch5
    content: |
      - [ ] [AGENT] P1. Remove explicit UCfgI/UCI/UEI deps from services batch 5 (~5 repos): ml-training-api, ml-training-service, pnl-attribution-service, position-balance-monitor-service, risk-and-exposure-service.
    status: pending
    blocked_by: p0-utl-delete-adapter-facade

  - id: p0-service-dep-cleanup-batch6
    content: |
      - [ ] [AGENT] P1. Remove explicit UCfgI/UCI/UEI deps from services batch 6 (~4 repos): strategy-service, trading-agent-service, trading-analytics-api, batch-live-reconciliation-service.
    status: pending
    blocked_by: p0-utl-delete-adapter-facade

  - id: p0-manifest-update-after-deps
    content: |
      - [ ] [AGENT] P0. Update workspace-manifest.json dependencies[] arrays for all repos changed in Phase 0. Sequential (after all dep cleanup agents complete).
    status: pending
    blocked_by:
      p0-service-dep-cleanup-batch1, p0-service-dep-cleanup-batch2, p0-service-dep-cleanup-batch3,
      p0-service-dep-cleanup-batch4, p0-service-dep-cleanup-batch5, p0-service-dep-cleanup-batch6, p0-umi-dep-cleanup,
      p0-utei-dep-cleanup, p0-urdi-dep-cleanup, p0-umli-dep-cleanup

  - id: p0-tier-gate-validator
    content: |
      - [ ] [AGENT] P0. Update scripts/tier-gate-check.sh to read integer tier field. Add validation: tier N cannot depend on tier > N. Add schema validation for workspace_infrastructure, runtime_clients.
    status: pending
    blocked_by: p0-manifest-update-after-deps

  - id: p0-dag-regeneration
    content: |
      - [ ] [AGENT] P0. Update scripts/manifest/generate_workspace_dag.py for new tier+role schema. Regenerate WORKSPACE_MANIFEST_DAG.svg and DATA_FLOW_DAG.svg. Wire tier-gate into QG base scripts. Run PM quality gates.
    status: pending
    blocked_by: p0-tier-gate-validator

  # ═══════════════════════════════════════════════════════════════
  # PHASE 1: UAC STRUCTURAL FOUNDATIONS
  # ═══════════════════════════════════════════════════════════════
  - id: p1-create-dirs
    content: |
      - [ ] [AGENT] P0. Create UAC directory structure: canonical/domain/{market,execution,reference,sports,sports_reference,position,features,derivatives,infrastructure,onchain}/, canonical/crosscutting/{errors}/, normalize_utils/, ensure registry/__init__.py exists.
    status: pending
    blocked_by: p0-dag-regeneration

  - id: p1-move-normalize
    content: |
      - [ ] [AGENT] P0. Move canonical/normalize/ (23 .py files + errors/ subdir) to normalize_utils/. Move canonical/canonical_mappings.py to normalize_utils/common_mappings.py. FILE MOVES ONLY -- imports updated in p1-import-update.
    status: pending
    blocked_by: p1-create-dirs

  - id: p1-move-registry-assets
    content: |
      - [ ] [AGENT] P0. Move external/venue_manifest/ (7 files) to registry/venue_manifest/. Move config/venue_rate_limits.py to registry/. Move config/provider_modes.py to registry/. FILE MOVES ONLY.
    status: pending
    blocked_by: p1-create-dirs

  - id: p1-move-errors-crosscutting
    content: |
      - [ ] [AGENT] P0. Move canonical/errors/ (7 files) to canonical/crosscutting/errors/. Move external/sports/errors.py to canonical/crosscutting/errors/sports_execution.py (merge if overlap). FILE MOVES ONLY.
    status: pending
    blocked_by: p1-create-dirs

  - id: p1-import-update
    content: |
      - [ ] [AGENT] P0. Update ALL UAC-internal imports (~100+ changes across ~30 files). Patterns: canonical.normalize -> normalize_utils, canonical.errors -> canonical.crosscutting.errors, external.venue_manifest -> registry.venue_manifest, config.venue_rate_limits -> registry.venue_rate_limits, config.provider_modes -> registry.provider_modes. Run QG after each batch of ~10 files. Run full smoke test at end.
    status: pending
    blocked_by: p1-move-normalize, p1-move-registry-assets, p1-move-errors-crosscutting

  # ═══════════════════════════════════════════════════════════════
  # PHASE 2: CANONICAL DOMAIN REORGANIZATION + FACADES
  # ═══════════════════════════════════════════════════════════════
  - id: p2-split-domain-flat-files
    content: |
      - [ ] [AGENT] P0. Split canonical/domain flat .py files into sub-packages: market.py -> market/__init__.py, sports.py -> sports/__init__.py, derivatives.py -> derivatives/__init__.py, instruments.py -> reference/__init__.py, account.py -> position/__init__.py, infrastructure.py -> infrastructure/__init__.py, onchain.py -> onchain/__init__.py. Split files >400 lines into sub-modules.
    status: pending
    blocked_by: p1-import-update

  - id: p2-move-sports-canonical
    content: |
      - [ ] [AGENT] P0. Move external/sports/canonical/*.py (15+ files) to canonical/domain/sports/. Update external/sports/__init__.py as temporary facade re-importing from canonical/domain/sports/. Existing sports/__init__.py re-exports from both original types AND newly moved files.
    status: pending
    blocked_by: p2-split-domain-flat-files

  - id: p2-move-crosscutting-types
    content: |
      - [ ] [AGENT] P0. Move canonical/domain/{rate_limits,latency,connectivity,analytics,risk}.py to canonical/crosscutting/.
    status: pending
    blocked_by: p2-split-domain-flat-files

  - id: p2-move-floating-files-with-facades
    content: |
      - [ ] [AGENT] P0. Move canonical/execution.py to canonical/domain/execution/__init__.py, split into base.py (shared: CanonicalOrder, CanonicalFill, OrderStatus), trade.py (CeFi/TradFi), sports.py (BetOrder, BetExecution), defi.py. Leave transition facade at canonical/execution.py. Move canonical/options.py to canonical/domain/derivatives/options.py (leave facade). Move canonical/odds.py to canonical/domain/sports/odds_canonical.py (leave facade). Move canonical/spread.py to canonical/domain/market/spread.py.
    status: pending
    blocked_by: p2-split-domain-flat-files

  - id: p2-rewrite-domain-init
    content: |
      - [ ] [AGENT] P0. Rewrite canonical/domain/__init__.py for sub-package imports (from .market import * pattern continues). Run dedicated canonical/domain smoke test to verify all symbols resolve. This single file determines Phase 2 success.
    status: pending
    blocked_by: p2-move-sports-canonical, p2-move-crosscutting-types, p2-move-floating-files-with-facades

  - id: p2-create-root-facades
    content: |
      - [ ] [AGENT] P0. Create 15 root-level facade files at unified_api_contracts/: market.py, execution.py, reference.py, sports.py, sports_reference.py, position.py, features.py, derivatives.py, infrastructure.py, errors.py, rate_limits.py, connectivity.py, latency.py, odds.py, options.py. Each re-exports from deep internal paths. Run circular import detection.
    status: pending
    blocked_by: p2-rewrite-domain-init

  - id: p2-update-root-init
    content: |
      - [ ] [AGENT] P0. Update UAC root __init__.py to re-export from new internal paths. Verify all existing from unified_api_contracts import X imports still work. Run UAC QG + full smoke test + facade import test.
    status: pending
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

  - id: p6-cursor-rule-create
    content: |
      - [ ] [AGENT] P1. Create uac-import-surface-enforcement.mdc with allowed/blocked import patterns and exceptions.
    status: pending

  - id: p6-cursor-rules-update
    content: |
      - [ ] [AGENT] P1. Update existing cursor rules: contracts-integration.mdc, schema-governance-index.mdc, library-tier-architecture.mdc, search-before-implementing.mdc, library-init-exports.mdc, anti-patterns-quick-reference.mdc.
    status: pending

  - id: p6-workspace-qg-validation
    content: |
      - [ ] [AGENT] P1. Run workspace-wide QG validation across all repos to verify linter catches violations and exemptions work correctly.
    status: pending

  # ═══════════════════════════════════════════════════════════════
  # PHASE 7: REGISTRY CAPABILITY MODEL
  # ═══════════════════════════════════════════════════════════════
  - id: p7-capability-model
    content: |
      - [ ] [AGENT] P0. Create registry/capability.py with SourceCapability Pydantic model: source, domains, crosscutting, supports_live/batch/historical/testnet/mainnet, auth_scope, auth_environments, operations.
    status: pending

  - id: p7-endpoint-resolution
    content: |
      - [ ] [AGENT] P0. Create resolve_endpoint(source, environment, mode, operation) -> EndpointSpec in registry/capability.py. Raises CapabilityResolutionError if unsupported combination.
    status: pending

  - id: p7-backfill-providers
    content: |
      - [ ] [AGENT] P1. Backfill capability declarations for all ~80 providers grouped by domain: CeFi (~15), DeFi (~15), Sports (~15), TradFi (~10), Alt data (~10), Meta (~5).
    status: pending

  - id: p7-coverage-matrix
    content: |
      - [ ] [AGENT] P1. Create scripts/coverage_matrix.py generating Domain x Source matrix (JSON + human table). Run UAC QG.
    status: pending

  # ═══════════════════════════════════════════════════════════════
  # PHASE 8: NEW REPOS
  # ═══════════════════════════════════════════════════════════════
  - id: p8-create-ufi
    content: |
      - [ ] [AGENT] P1. Create unified-features-interface repo: pyproject.toml, quality-gates.sh, __init__.py, core adapters. Write canonical/domain/features/ types in UAC (CanonicalFeatureRecord, FeatureMetadata). Register in workspace-manifest.json.
    status: pending

  - id: p8-create-ufol
    content: |
      - [ ] [AGENT] P1. Create unified-feature-orchestration-library repo: pipeline routing, batch/live handlers, feature registry. Register in workspace-manifest.json.
    status: pending

  - id: p8-create-usri
    content: |
      - [ ] [AGENT] P1. Create unified-sports-reference-interface repo: fixtures, leagues, teams, players, bookmakers. Register in workspace-manifest.json.
    status: pending

  - id: p8-dag-regenerate
    content: |
      - [ ] [AGENT] P1. Regenerate workspace DAG with all 3 new repos. Run PM QG.
    status: pending

  # ═══════════════════════════════════════════════════════════════
  # PHASE 9: REPLAY + DRIFT INFRASTRUCTURE
  # ═══════════════════════════════════════════════════════════════
  - id: p9-uic-internal-registry
    content: |
      - [ ] [AGENT] P1. Create UIC internal endpoint registry for cross-service schema validation.
    status: pending

  - id: p9-replay-workflow
    content: |
      - [ ] [AGENT] P1. Create PM contract-replay.yml reusable workflow. Layer 1: raw schema parse against external/{source}/schemas.py. Layer 2: canonical output invariants (required fields, enum ranges, cross-field constraints).
    status: pending

  - id: p9-drift-recording
    content: |
      - [ ] [AGENT] P1. Create PM contract-drift-record.yml nightly CI (staging only). Approval-gated PRs labeled schema-impact. Never auto-merge.
    status: pending

  - id: p9-lane-metrics
    content: |
      - [ ] [AGENT] P1. Define 4 validation lanes per (source, domain) pair: smoke (every PR), replay (on merge), live (nightly staging), drift (nightly staging). Emit Prometheus counters: uac_validation_result, uac_validation_duration_seconds, uac_drift_detected. Create Grafana dashboard for per-source per-domain lane health. Alert on drift detection, replay failure, consecutive live validation failures.
    status: pending

  - id: p9-extend-cassettes-all-interfaces
    content: |
      - [ ] [AGENT] P2. Extend cassette replay validation to ALL interface repos: UTEI, USEI, UDEI, UPI, UFI, USRI (not just UMI/URDI).
    status: pending

  # ═══════════════════════════════════════════════════════════════
  # PHASE 10: RUNTIME GUARDRAILS + SERVICE ADOPTION
  # ═══════════════════════════════════════════════════════════════
  - id: p10-error-taxonomy
    content: |
      - [ ] [AGENT] P0. Create fail-fast error classes in UTL: UnsupportedModeError(source, requested_mode, supported_modes, suggested_resolution), UnsupportedEnvironmentError, ApiKeyScopeMismatchError(source, key_scope, target_env), CapabilityResolutionError, UnsupportedOperationError. Run UTL QG.
    status: pending

  - id: p10-preflight-umi
    content: |
      - [ ] [AGENT] P1. Wire preflight capability checks into UMI adapters: resolve_capability -> validate_mode -> validate_env -> validate_auth_scope -> resolve_endpoint -> execute -> validate raw -> normalize -> return canonical. Run UMI QG.
    status: pending

  - id: p10-preflight-utei-usei
    content: |
      - [ ] [AGENT] P1. Wire preflight capability checks into UTEI and USEI adapters. Same 9-step flow. Run QGs.
    status: pending

  - id: p10-preflight-remaining-interfaces
    content: |
      - [ ] [AGENT] P1. Wire preflight capability checks into UDEI, UPI, URDI, USRI, UFI, UFCL. Run QGs.
    status: pending

  - id: p10-duplicate-mapping-detection
    content: |
      - [ ] [AGENT] P1. Scan all interface adapter repos for duplicate raw->canonical mapping logic. Extract duplicates to UAC external/{source}/normalize.py. Interface adapters must call UAC normalizers, not re-implement.
    status: pending

  - id: p10-service-consumption-audit
    content: |
      - [ ] [AGENT] P1. Scan all services for direct raw payload parsing (from unified_api_contracts.external.* in service repos). Migrate any hits to canonical imports via interface layer.
    status: pending

  - id: p10-qg-validators
    content: |
      - [ ] [AGENT] P1. Add QG validators to base-service.sh: duplicate mapping detection (fail if service contains raw->canonical normalizer), ad-hoc endpoint literal detection using broad venue URL patterns covering all CeFi+sports venues from registry/venue_constants.py (not just 4 venues). Run PM QG.
    status: pending

  - id: p10-codex-contracts-layout
    content: |
      - [ ] [AGENT] P2. Rewrite codex 02-data/contracts-scope-and-layout.md for new UAC structure: facade pattern, canonical/domain sub-packages, crosscutting, normalize_utils, registry, import surface rules.
    status: pending

  - id: p10-codex-tier-architecture
    content: |
      - [ ] [AGENT] P2. Update codex 04-architecture/TIER-ARCHITECTURE.md: integer tiers, workspace_infrastructure, runtime_clients, facade import flow.
    status: pending

  - id: p10-codex-data-flow
    content: |
      - [ ] [AGENT] P2. Update codex 04-architecture/data-flow-map.md: features stack + sports reference data flows, facade boundaries.
    status: pending

  - id: p10-codex-ssot-index
    content: |
      - [ ] [AGENT] P2. Update codex 10-audit/ssot-reference-mapping.md and 00-SSOT-INDEX.md: facade modules, registry/capability, new repos (UFI, UFOL, USRI).
    status: pending

isProject: false
---

# UAC Citadel Architecture -- Execution Todos

Detailed execution plan: `unified-trading-pm/plans/active/uac_citadel_implementation.plan.md` (implementation spec)
Architecture plan: `unified-trading-pm/plans/active/uac_citadel_architecture_0ccb5b9b.plan.md`

## Phases Overview

- **Phase 0**: Manifest schema evolution + tier model fix (17 todos)
- **Phase 1**: UAC structural foundations -- directory moves + import updates (5 todos)
- **Phase 2**: Canonical domain reorganization + root-level facades (7 todos)
- **Phase 3**: External flattening + per-source normalization co-location (11 todos)
- **Phase 4**: Config cleanup + cross-repo moves (4 todos)
- **Phase 5**: Downstream import updates + transition facade cleanup (13 todos)
- **Phase 6**: Linter enforcement (4 todos)
- **Phase 7**: Registry capability model (4 todos)
- **Phase 8**: New repos (4 todos)
- **Phase 9**: Replay + drift infrastructure (5 todos)
- **Phase 10**: Runtime guardrails + service adoption + codex (11 todos)

**Total: 86 todos**
