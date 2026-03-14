# ═══════════════════════════════════════════════════════════════════════

# UAC CITADEL ARCHITECTURE — FULL REFACTOR SPECIFICATION v2

# Plan: uac_citadel_architecture_0ccb5b9b

# Date: 2026-03-14

# Key change from v1: Facade pattern for shallow, stable public API

# ═══════════════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────────────

# 1. IMPORT SURFACE DESIGN (THE FACADE ARCHITECTURE)

# ─────────────────────────────────────────────────────────────────────

import_surface: principle: | UAC internal structure can be arbitrarily deep for maintainability. All external consumers
access types through shallow root-level facades. Internal reorganisation never requires downstream import changes.

allowed_patterns: level_1_top_level: pattern: "from unified_api_contracts import X" consumers: [services, libraries,
UIC, SIT, all] note: "Primary path. ~50 most-used canonical types re-exported from **init**.py"

    level_2_domain_facade:
      pattern: "from unified_api_contracts.{domain} import X"
      domains: [market, execution, reference, sports, sports_reference,
                position, features, derivatives, infrastructure, errors,
                rate_limits, connectivity, latency, odds, options]
      consumers: [interfaces, services, libraries]
      note: "Domain-specific facade modules at UAC root. Each re-exports
             from canonical/domain/{domain}/ and canonical/crosscutting/"

    level_3_external:
      pattern: "from unified_api_contracts.external.{source} import X"
      consumers: [interface adapters only]
      note: "Each external/{source}/__init__.py re-exports from schemas.py
             so consumers never go to .schemas directly"

    level_3_registry:
      pattern: "from unified_api_contracts.registry import X"
      consumers: [interfaces, UTL, services]

    level_3_testing:
      pattern: "from unified_api_contracts.testing import X"
      consumers: [test files only]

blocked_patterns: - pattern: "from unified_api_contracts.canonical._ import X" exception: "UIC production code
(canonical neighbor), SIT tests" - pattern: "from unified_api_contracts.normalize_utils._ import X" exception: none -
pattern: "from unified_api_contracts.config._ import X" reason: "config/ deleted; types moved to UTL/UCI" - pattern:
"from unified_api_contracts.shared._ import X" reason: "shared/ deleted" - pattern: "from
unified_api_contracts.schemas.\* import X" reason: "schemas/ deleted (was facade-only)" - pattern: "from
unified_api_contracts.external.{source}.schemas import X" reason: "use external.{source} import X instead (**init**
re-exports)"

facade_modules: # These .py files live at unified_api_contracts/ root # Each re-exports from deep internal paths
**init**.py: re_exports_from: - canonical/domain/\* (top ~50 most-used types) - canonical/crosscutting/errors
(CanonicalError and friends) - canonical/execution.py legacy symbols - registry/ (SPORTS_VENUES, VENUE_CATEGORY_MAP,
etc.) note: "This is what exists today, just reorganized internally"

    market.py:
      re_exports: [CanonicalTicker, CanonicalTrade, CanonicalOrderBook,
                    CanonicalOHLCV, CanonicalLiquidation,
                    CanonicalLiquidationCluster, CanonicalMarketState]

    execution.py:
      re_exports: [CanonicalOrder, CanonicalFill, OrderSide, OrderType,
                    OrderStatus, CanonicalBetOrder, BetOrder, BetExecution,
                    BetStatus, SignalSource]
      note: "Already exists as canonical/execution.py; becomes root facade"

    reference.py:
      re_exports: [CanonicalInstrument, ContractSpec, InstrumentType,
                    AccessMode, ExpiryType]

    sports.py:
      re_exports: [CanonicalOdds, OddsType, OutcomeType, CanonicalFixture,
                    TeamMapping, CanonicalLineup, CanonicalInjury,
                    CanonicalFixtureStats, CanonicalPlayerStats]
      note: "Types currently scattered in external/sports/canonical/"

    sports_reference.py:
      re_exports: [CanonicalFixture, TeamMapping, CanonicalLeague,
                    BookmakerInfo]
      note: "Subset of sports types relevant to USRI"

    position.py:
      re_exports: [CanonicalPosition, CanonicalBalance]

    features.py:
      re_exports: [CanonicalFeatureRecord, FeatureMetadata]
      note: "New types for UFI"

    derivatives.py:
      re_exports: [CanonicalOptionsChainEntry, OptionChainSnapshot,
                    NormalizedStrikeCoordinate, ComboLeg, ComboStrategyType,
                    CanonicalGreeks]

    infrastructure.py:
      re_exports: [CloudStorageQuota, CloudQuotaResponse]

    errors.py:
      re_exports_from: canonical/crosscutting/errors/*
      re_exports: [CanonicalError, CanonicalRateLimitError,
                    CanonicalUnknownVenueError, BetRejectedError,
                    VenueErrorCategory, all domain-specific errors]

    rate_limits.py:
      re_exports: [VenueRateLimitSpec, HttpRateLimitHeaders]

    connectivity.py:
      re_exports: [WebSocketState, ConnectionEvent]

    latency.py:
      re_exports: [LatencySnapshot, LatencyBucket]

    odds.py:
      re_exports: [CanonicalOdds, OddsType, OutcomeType, OddsFormat]
      note: "Already exists as canonical/odds.py; becomes root facade"

    options.py:
      re_exports: [NormalizedStrikeCoordinate, OptionChainSnapshot,
                    CanonicalOptionsChainEntry, CanonicalGreeks]
      note: "Already exists as canonical/options.py; becomes root facade"

# ─────────────────────────────────────────────────────────────────────

# 2. UAC INTERNAL RESTRUCTURE

# ─────────────────────────────────────────────────────────────────────

unified_api_contracts:

# ── 2a. Directory moves/creations ──────────────────────────────────

create_directories: - canonical/domain/market/ - canonical/domain/execution/ - canonical/domain/reference/ -
canonical/domain/sports/ - canonical/domain/sports_reference/ - canonical/domain/position/ -
canonical/domain/features/ - canonical/domain/derivatives/ - canonical/domain/infrastructure/ -
canonical/crosscutting/ - canonical/crosscutting/errors/ - normalize_utils/ - registry/

move_within_uac: # -- Canonical domain splits (flat .py → domain sub-packages) ----- - from: canonical/domain/market.py
to: canonical/domain/market/**init**.py note: "Split into tickers.py, trades.py, orderbooks.py, ohlcv.py if file > 400
lines; else keep as single module"

    - from: canonical/domain/sports.py
      to: canonical/domain/sports/__init__.py

    - from: canonical/domain/derivatives.py
      to: canonical/domain/derivatives/__init__.py

    - from: canonical/domain/instruments.py
      to: canonical/domain/reference/__init__.py

    - from: canonical/domain/account.py
      to: canonical/domain/position/__init__.py

    - from: canonical/domain/infrastructure.py
      to: canonical/domain/infrastructure/__init__.py

    # -- Sports canonical (WRONG location → RIGHT location) -----------
    - from: external/sports/canonical/betting.py
      to: canonical/domain/sports/betting.py
    - from: external/sports/canonical/odds.py
      to: canonical/domain/sports/odds.py
    - from: external/sports/canonical/fixture.py
      to: canonical/domain/sports/fixture.py
    - from: external/sports/canonical/mappings.py
      to: canonical/domain/sports/mappings.py
    - from: external/sports/canonical/bookmaker.py
      to: canonical/domain/sports/bookmaker.py
    - from: external/sports/canonical/live.py
      to: canonical/domain/sports/live.py
    - from: external/sports/canonical/lineup.py
      to: canonical/domain/sports/lineup.py
    - from: external/sports/canonical/injury.py
      to: canonical/domain/sports/injury.py
    - from: external/sports/canonical/fixture_stats.py
      to: canonical/domain/sports/fixture_stats.py
    - from: external/sports/canonical/features.py
      to: canonical/domain/sports/features.py
    - from: external/sports/canonical/events.py
      to: canonical/domain/sports/events.py
    - from: external/sports/canonical/arbitrage.py
      to: canonical/domain/sports/arbitrage.py
    - from: external/sports/canonical/player_stats.py
      to: canonical/domain/sports/player_stats.py
    - from: external/sports/canonical/progressive.py
      to: canonical/domain/sports/progressive.py
    - from: external/sports/canonical/processed_odds.py
      to: canonical/domain/sports/processed_odds.py
    - from: "external/sports/canonical/_features_*.py (all 5)"
      to: "canonical/domain/sports/_features_*.py"

    # -- Cross-cutting (domain files → crosscutting) ------------------
    - from: canonical/domain/rate_limits.py
      to: canonical/crosscutting/rate_limits.py
    - from: canonical/domain/latency.py
      to: canonical/crosscutting/latency.py
    - from: canonical/domain/connectivity.py
      to: canonical/crosscutting/connectivity.py
    - from: canonical/domain/analytics.py
      to: canonical/crosscutting/analytics.py
    - from: canonical/domain/risk.py
      to: canonical/crosscutting/risk.py

    # -- Errors (already in canonical/errors/ — move to crosscutting) -
    - from: canonical/errors/
      to: canonical/crosscutting/errors/
      note: "All 7 files: __init__.py, _canonical.py, _types.py,
             altdata.py, sports.py, defi.py, cefi.py"

    # -- Sports errors ------------------------------------------------
    - from: external/sports/errors.py
      to: canonical/crosscutting/errors/sports_execution.py
      note: "Merge with existing canonical/errors/sports.py if overlap"

    # -- Normalizers → normalize_utils/ (UAC-internal) ----------------
    - from: canonical/normalize/
      to: normalize_utils/
      note: "All 23 .py files move. Plus errors/ subdirectory.
             These are UAC-internal only — never imported outside UAC"

    # -- Canonical mappings → per-source or normalize_utils -----------
    - from: canonical/canonical_mappings.py
      to: normalize_utils/common_mappings.py
      note: "Source-specific mappings extract to external/{source}/mappings.py"

    # -- Registry (venue_manifest → registry/) ------------------------
    - from: external/venue_manifest/
      to: registry/venue_manifest/
      note: "All 7 files. venue_manifest is metadata, not an external API"

    - from: config/venue_rate_limits.py
      to: registry/venue_rate_limits.py

    - from: config/provider_modes.py
      to: registry/provider_modes.py

    # -- Existing canonical modules → become facades ------------------
    - from: canonical/execution.py
      to: canonical/domain/execution/__init__.py
      note: "Root execution.py becomes a facade that re-exports from here"

    - from: canonical/options.py
      to: canonical/domain/derivatives/options.py
      note: "Root options.py becomes a facade"

    - from: canonical/odds.py
      to: canonical/domain/sports/odds_canonical.py
      note: "Root odds.py becomes a facade. Rename to avoid collision
             with external/sports/canonical/odds.py moving here"

    - from: canonical/spread.py
      to: canonical/domain/market/spread.py

# ── 2b. External flattening ────────────────────────────────────────

flatten_external: # -- sports/sources/{provider} → external/{provider} -------------- - from:
external/sports/sources/oddsjam/ to: external/oddsjam/ - from: external/sports/sources/opticodds/ to:
external/opticodds/ - from: external/sports/sources/footystats/ to: external/footystats/ note: "Already exists at
external/footystats/ — merge or dedupe" - from: external/sports/sources/odds_api/ to: external/odds_api/ note: "Already
exists at external/odds_api/ — merge or dedupe" - from: external/sports/sources/understat/ to: external/understat/ note:
"Already exists at external/understat/ — merge or dedupe" - from: external/sports/sources/soccer_football_info/ to:
external/soccer_football_info/ note: "Already exists at external/soccer_football_info/ — merge" - from:
external/sports/sources/api_football/ to: external/api_football/ note: "Already exists at external/api_football/ —
merge" - from: external/sports/sources/betfair/ to: external/betfair/ note: "Already exists at external/betfair/ —
merge" - from: external/sports/sources/open_meteo/ to: external/open_meteo/ note: "Already exists at
external/open_meteo/ — merge" - from: external/sports/sources/pinnacle/ to: external/pinnacle/ note: "Already exists at
external/pinnacle/ — merge"

    # -- onchain/ → cryptoquant/ (single source inside) ---------------
    - from: external/onchain/cryptoquant.py
      to: external/cryptoquant/schemas.py

    # -- macro/ → yahoo_finance/ (single source inside) ---------------
    - from: external/macro/yahoo_finance.py
      to: external/yahoo_finance/schemas.py
      note: "Already exists at external/yahoo_finance/ — merge"

    # -- defi/ → KEEP or split by actual source -----------------------
    - from: external/defi/schemas.py
      to: external/defi/schemas.py
      note: "Keep if defi is one logical source; else split.
             Currently imports from protocol_sdks — review overlap"

    # -- prime_broker/ → KEEP (is a logical source) -------------------
    - action: keep
      path: external/prime_broker/
      note: "Prime broker IS a source (specific custodian API)"

    # -- mev/ → rename to flashbots/ or keep -------------------------
    - from: external/mev/
      to: external/mev/
      note: "DECISION NEEDED: rename to flashbots/ if that's the actual
             source, or keep mev/ if it's the source name. MEV is a
             concept; Flashbots is the API provider."

# ── 2c. External **init**.py re-export pattern ─────────────────────

external_init_pattern: description: | Every external/{source}/**init**.py MUST re-export all public symbols from
schemas.py (and normalize.py if present). This ensures consumers use 3-level imports max. example: | #
external/binance/**init**.py from unified_api_contracts.external.binance.market_schemas import _ from
unified_api_contracts.external.binance.order_schemas import _ from
unified_api_contracts.external.binance.account_schemas import _ from unified_api_contracts.external.binance.ws_schemas
import _

    binance_special_case: |
      Binance has 4 sub-modules (market_schemas.py, order_schemas.py,
      account_schemas.py, ws_schemas.py). Keep them for UAC-internal
      organization but __init__.py re-exports everything.
      Consumer: from unified_api_contracts.external.binance import X

    standard_source: |
      # external/{source}/__init__.py
      from unified_api_contracts.external.{source}.schemas import *

# ── 2d. Deletions ──────────────────────────────────────────────────

delete: - path: config/domain_config.py reason: "Orphan; service config belongs in service config.py" - path:
config/log_level.py reason: "LogLevel moves to unified-trading-library" - path: config/trading_validation.py reason:
"Validation framework → unified-config-interface" - path: config/quota_types.py reason: "Split: cloud quotas → UCI
abstractions, venue quotas → registry/venue_rate_limits.py" - path: config/**init**.py reason: "Empty after moves" -
path: config/ reason: "Entire directory deleted" - path: shared/ reason: "Already being deleted per git status (contents
moved)" - path: schemas/ reason: "Already being deleted per git status (was facade-only)" - path:
external/sports/canonical/ reason: "Moved to canonical/domain/sports/" - path: external/sports/sources/ reason:
"Flattened to external/{provider}/" - path: external/sports/errors.py reason: "Moved to
canonical/crosscutting/errors/" - path: external/sports/ reason: "Empty after moves (delete entire directory)" - path:
external/onchain/ reason: "Flattened to external/cryptoquant/" - path: external/macro/ reason: "Flattened to
external/yahoo_finance/" - path: external/venue_manifest/ reason: "Moved to registry/venue_manifest/" - path:
canonical/normalize/ reason: "Moved to normalize_utils/" - path: canonical/canonical_mappings.py reason: "Moved to
normalize_utils/common_mappings.py"

# ── 2e. New files ──────────────────────────────────────────────────

create_facade_files: # Root-level facades (the key innovation) - path: market.py type: facade - path: execution.py type:
facade note: "Replaces canonical/execution.py as public entry point" - path: reference.py type: facade - path: sports.py
type: facade note: "Re-exports from canonical/domain/sports/" - path: sports_reference.py type: facade - path:
position.py type: facade - path: features.py type: facade - path: derivatives.py type: facade - path: infrastructure.py
type: facade - path: errors.py type: facade - path: rate_limits.py type: facade - path: connectivity.py type: facade -
path: latency.py type: facade

create_internal_files: - path: normalize_utils/**init**.py - path: normalize_utils/common_mappings.py - path:
registry/**init**.py note: "Re-exports capability, endpoints, venue_manifest, etc." - path: registry/capability.py note:
"New: per-source capability declarations" - path: canonical/domain/sports/**init**.py note: "Re-exports all sports
canonical types" - path: canonical/domain/execution/**init**.py - path: canonical/domain/market/**init**.py - path:
canonical/domain/reference/**init**.py - path: canonical/domain/position/**init**.py - path:
canonical/domain/derivatives/**init**.py - path: canonical/domain/features/**init**.py - path:
canonical/domain/infrastructure/**init**.py - path: canonical/crosscutting/**init**.py - path:
canonical/crosscutting/errors/**init**.py

# ─────────────────────────────────────────────────────────────────────

# 3. INTERFACE REPOS — IMPORT CHANGES

# ─────────────────────────────────────────────────────────────────────

unified_market_interface: canonical_imports: # These all use `from unified_api_contracts import X` already # NO CHANGES
NEEDED for: # - **init**.py (from unified_api_contracts import CanonicalError, ...) # - schemas.py (from
unified_api_contracts import CanonicalTicker, ...) # - All adapters importing CanonicalError from top-level changes: []
note: "All canonical imports already at level 1. Zero changes."

external_imports: changes: # -- Already correct (3-level or will be after **init** re-export) -- # Most adapters: from
unified_api_contracts.external.{source}.schemas import X # After **init** re-export: from
unified_api_contracts.external.{source} import X # Both work; prefer dropping .schemas but not blocking

      # -- Flattening required (currently 5 levels) -------------------
      - file: adapters/sports/oddsjam_adapter.py
        old: "from unified_api_contracts.external.sports.sources.oddsjam.schemas import ..."
        new: "from unified_api_contracts.external.oddsjam import ..."

      - file: adapters/sports/opticodds_adapter.py
        old: "from unified_api_contracts.external.sports.sources.opticodds.schemas import ..."
        new: "from unified_api_contracts.external.opticodds import ..."

      # -- sports canonical import (moved location) -------------------
      - file: sports/protocol.py
        old: "from unified_api_contracts.external.sports import CanonicalOdds, OddsType"
        new: "from unified_api_contracts import CanonicalOdds, OddsType"
        note: "These are canonical types, not external. Already in __init__"

      # -- binance (optional: drop .market_schemas) -------------------
      - file: adapters/binance.py
        old: "from unified_api_contracts.external.binance import (BinanceLiquidationOrder, ...)"
        new: "from unified_api_contracts.external.binance import (...)"
        note: "Already correct — imports from __init__. No change needed."

      # -- Optional: drop .schemas suffix across all adapters ---------
      # e.g. from unified_api_contracts.external.bybit.schemas import X
      #   →  from unified_api_contracts.external.bybit import X
      # This is OPTIONAL and can be done incrementally. Both work after
      # __init__ re-exports are added.

dependency_changes: - remove: [unified-config-interface, unified-cloud-interface, unified-events-interface] note: "UMI
should depend on UAC only (T0 contracts). Config/cloud/events accessed via UTL at service level." verify: "grep
pyproject.toml for these deps"

unified_trade_execution_interface: canonical_imports: changes: [] note: "All use `from unified_api_contracts import X`.
No changes."

external_imports: changes: [] note: "All use unified_api_contracts.external.ccxt.schemas — already 4 levels but all
ccxt. After **init** re-export: from unified_api_contracts.external.ccxt import X (3 levels). Optional cleanup, not
blocking."

dependency_changes: []

unified_sports_execution_interface: canonical_imports: changes: - file: adapters/exchanges/polymarket_clob.py old: "from
unified_api_contracts.canonical.execution import (...)" new: "from unified_api_contracts.execution import (...)" note:
"Or from unified_api_contracts import X (top-level)"

      - file: adapters/bookmaker_api/pinnacle.py
        old: "from unified_api_contracts.canonical.execution import (...)"
        new: "from unified_api_contracts.execution import (...)"

external_imports: changes: [] note: "All already at from unified_api_contracts.external.{source}.schemas → drop .schemas
after **init** re-export. Optional."

dependency_changes: []

unified_reference_data_interface: canonical_imports: changes: [] note: "All use `from unified_api_contracts import X`.
No changes."

external_imports: changes: [] note: "All use unified_api_contracts.external.{source}.schemas — 4 levels. After **init**
re-export, drop .schemas. Optional cleanup."

dependency_changes: []

unified_position_interface: canonical_imports: changes: [] note: "All use `from unified_api_contracts import X`. No
changes."

external_imports: changes: # binance sub-module consolidation (after **init** re-export) - file:
tests/integration/test_vcr_position_schemas.py old: "from unified_api_contracts.external.binance.account_schemas import
..." new: "from unified_api_contracts.external.binance import ..." note: "After **init** re-exports all sub-modules"

      - file: tests/integration/test_vcr_position_schemas.py
        old: "from unified_api_contracts.external.binance.market_schemas import ..."
        new: "from unified_api_contracts.external.binance import ..."

dependency_changes: []

unified_defi_execution_interface: canonical_imports: changes: [] note: "Uses `from unified_api_contracts import X`. No
changes."

external_imports: changes: []

dependency_changes: []

unified_ml_interface: changes: [] note: "No UAC imports found. No changes."

# ─────────────────────────────────────────────────────────────────────

# 4. SERVICE REPOS — IMPORT CHANGES

# ─────────────────────────────────────────────────────────────────────

# The ONLY universal change across services is LogLevel migration.

# Everything else stays as `from unified_api_contracts import X`.

services_loglevel_migration: description: "LogLevel moves from UAC config/ to unified-trading-library" old_import: "from
unified_api_contracts import LogLevel" new_import: "from unified_trading_library import LogLevel" affected_repos: -
repo: alerting-service file: alerting_service/main.py - repo: batch-live-reconciliation-service file:
batch_live_reconciliation_service/cli/main.py - repo: execution-service file: execution_service/cli/main.py - repo:
features-calendar-service file: features_calendar_service/cli/handlers/batch_handler.py - repo:
features-commodity-service file: features_commodity_service/cli/main.py - repo: features-cross-instrument-service file:
features_cross_instrument_service/cli/main.py - repo: features-delta-one-service file:
features_delta_one_service/cli/main.py - repo: features-multi-timeframe-service file:
features_multi_timeframe_service/cli/main.py - repo: features-onchain-service file:
features_onchain_service/cli/main.py - repo: features-sports-service file: features_sports_service/cli/main.py - repo:
features-volatility-service file: features_volatility_service/cli/main.py - repo: instruments-service file:
instruments_service/cli/main.py - repo: market-data-processing-service file:
market_data_processing_service/cli/main.py - repo: market-tick-data-service file: market_tick_data_service/cli/main.py -
repo: ml-inference-service file: ml_inference_service/cli/main.py - repo: ml-training-service file:
ml_training_service/cli/main.py - repo: pnl-attribution-service file: pnl_attribution_service/cli/main.py - repo:
position-balance-monitor-service file: position_balance_monitor_service/cli/main.py - repo: risk-and-exposure-service
file: risk_and_exposure_service/cli/main.py - repo: strategy-service file: strategy_service/cli/main.py - repo:
trading-agent-service file: trading_agent_service/**main**.py

# Per-service non-LogLevel changes (most have ZERO additional changes)

service_specific_changes: execution_service: changes: - file: tests/unit/test_boost_exec_venues_4.py old: "from
unified_api_contracts.external.sports.canonical.betting import BetStatus" new: "from unified_api_contracts import
BetStatus" note: "BetStatus already in top-level **init**"

instruments_service: changes: - file: tests/unit/test_team_aliases.py old: "from
unified_api_contracts.external.sports.canonical.mappings import TeamMapping" new: "from unified_api_contracts import
TeamMapping" note: "TeamMapping already in top-level **init**"

      - file: tests/unit/test_api_contracts.py
        old: "from unified_api_contracts.external.ccxt.schemas import CcxtOrder"
        new: "from unified_api_contracts.external.ccxt import CcxtOrder"

      - file: tests/unit/test_api_contracts.py
        old: "from unified_api_contracts.external.thegraph.schemas import ..."
        new: "from unified_api_contracts.external.thegraph import ..."

strategy_service: changes: - file: tests/unit/test_vol_surface_strategy.py old: "from
unified_api_contracts.canonical.options import NormalizedStrikeCoordinate" new: "from unified_api_contracts.options
import NormalizedStrikeCoordinate" note: "Or from unified_api_contracts import NormalizedStrikeCoordinate"

trading_agent_service: changes: - file: tests/unit/test_coverage_boost_trading_agent.py old: "from
unified_api_contracts.canonical.domain.derivatives import ComboLeg" new: "from unified_api_contracts.derivatives import
ComboLeg" note: "Or from unified_api_contracts import ComboLeg"

      - file: tests/unit/test_strategy_ranker.py
        old: "from unified_api_contracts.canonical.domain.derivatives import ComboStrategyType"
        new: "from unified_api_contracts.derivatives import ComboStrategyType"

features_sports_service: changes: [] note: "Uses `from unified_api_contracts import (OddsType, ...)` — already correct"

features_commodity_service: changes: [] note: "Doc comments reference unified_api_contracts.external.macro.yahoo_finance
and unified_api_contracts.external.open_meteo — update comments only"

# All other services: LogLevel migration ONLY (listed above)

# No other import changes needed:

# alerting-service, batch-live-reconciliation-service,

# client-reporting-api, deployment-api, deployment-service,

# elysium-defi-system, features-calendar-service,

# features-cross-instrument-service, features-delta-one-service,

# features-multi-timeframe-service, features-onchain-service,

# features-volatility-service, market-data-processing-service,

# ml-inference-service, ml-training-service,

# pnl-attribution-service, position-balance-monitor-service,

# risk-and-exposure-service

# ─────────────────────────────────────────────────────────────────────

# 5. LIBRARIES AND CONTRACTS

# ─────────────────────────────────────────────────────────────────────

unified_internal_contracts: production_code: changes: - file: unified_internal_contracts/market_data/**init**.py old:
"from unified_api_contracts.canonical import (...)" new: "from unified_api_contracts.canonical import (...)" note: "UIC
is EXEMPTED from canonical.\* block. No change needed. UIC is UAC's closest neighbor and may import canonical."

      - file: unified_internal_contracts/domain/sports/execution.py
        old: "from unified_api_contracts import CanonicalFill, CanonicalOrder"
        new: "from unified_api_contracts import CanonicalFill, CanonicalOrder"
        note: "Already level 1. No change."

      - file: unified_internal_contracts/domain/market_tick_data/sports.py
        old: "from unified_api_contracts import (...)"
        new: "from unified_api_contracts import (...)"
        note: "Already level 1. No change."

      - file: unified_internal_contracts/domain/execution_service/sports.py
        old: "from unified_api_contracts import BetStatus"
        new: "from unified_api_contracts import BetStatus"
        note: "Already level 1. No change."

test_code: changes: - file: tests/integration/test_uac_integration.py old: | from unified_api_contracts.canonical.domain
import (...) from unified_api_contracts.canonical.execution import CanonicalFill from
unified_api_contracts.canonical.normalize.orderbooks import (...) from
unified_api_contracts.canonical.normalize.orders_fills import (...) from
unified_api_contracts.canonical.normalize.trades import (...) from unified_api_contracts.external.binance.market_schemas
import (...) from unified_api_contracts.external.binance.order_schemas import (...) new: | from unified_api_contracts
import (CanonicalFill, CanonicalInstrument, ...) from unified_api_contracts.execution import (CanonicalFill, ...) #
normalize imports: UIC test exempted OR use testing helpers from unified_api_contracts.testing import
normalize_orderbook, normalize_fill, ... from unified_api_contracts.external.binance import (...) note: "UIC integration
tests exempted from deep-import block. However, prefer facade paths where possible."

scripts: changes: - file: scripts/check_schema_organization.py old: "Check that UIC only imports from
unified_api_contracts.canonical" new: "Update rule to allow UIC from canonical OR from facades"

new_domain_modules: note: "Many new domain modules already added per git status. Verify they import from
unified_api_contracts at level 1 only."

unified_trading_library: receives: - symbol: LogLevel from: unified_api_contracts/config/log_level.py to:
unified_trading_library/core/log_level.py export_via: unified_trading_library/**init**.py note: "Add LogLevel to UTL
**init**.py exports. All 20+ services update their import to from unified_trading_library import LogLevel"

dependency_changes: remove: note: "UTL currently depends on some T2 interfaces (violation). Remove these once
adapter_facade pattern is finalized." add: - unified-features-interface # when created

existing_changes: note: "UTL already has domain_client/, feature_service_base/, mock_state_store, adapter_facade per git
status. These align with the plan. Verify no UAC deep imports."

unified_config_interface: receives: - symbol: REQUIRED_CONFIG_FIELDS (and trading_validation framework) from:
unified_api_contracts/config/trading_validation.py to: unified_config_interface/validation.py note: "Config validation
is UCI's domain"

    - symbol: "Cloud quota type definitions"
      from: unified_api_contracts/config/quota_types.py (cloud subset)
      to: unified_cloud_interface/abstractions.py
      note: "Cloud quota types belong in UCI (cloud abstraction)"

dependency_changes: []

unified_cloud_interface: receives: - symbol: "Cloud quota types" from: unified_api_contracts/config/quota_types.py
(cloud subset) note: "Only the cloud-specific quota types, not venue quotas"

test_dependency: add: unified-api-contracts note: "UCI tests may validate against UAC cloud SDK schemas. Production code
does NOT depend on UAC."

unified_domain_client: changes: - file: unified_domain_client/schemas/config_schema.py old: "from unified_api_contracts
import (...)" new: "from unified_api_contracts import (...)" note: "Already level 1. No change."

    - file: tests/integration/test_library_deps_integration.py
      old: "from unified_api_contracts import CanonicalOrder"
      new: "from unified_api_contracts import CanonicalOrder"
      note: "Already level 1. No change."

# ─────────────────────────────────────────────────────────────────────

# 6. SYSTEM INTEGRATION TESTS

# ─────────────────────────────────────────────────────────────────────

system_integration_tests: changes: - file: tests/abbreviated/test_contract_normalization.py old: | from
unified_api_contracts import CanonicalFill, CanonicalOrder from unified_api_contracts.canonical.execution import
OrderSide, OrderType new: | from unified_api_contracts import CanonicalFill, CanonicalOrder from
unified_api_contracts.execution import OrderSide, OrderType

    - file: tests/integration/test_interface_mock_chains.py
      old: |
        from unified_api_contracts.canonical.domain import CanonicalTicker
        from unified_api_contracts.testing.fault_injection import FaultConfig
        from unified_api_contracts.canonical.execution import CanonicalOrder
      new: |
        from unified_api_contracts.market import CanonicalTicker
        from unified_api_contracts.testing import FaultConfig
        from unified_api_contracts.execution import CanonicalOrder

    - file: tests/integration/test_uac_uic_compat.py
      old: "from unified_api_contracts.canonical import domain"
      new: "from unified_api_contracts import market, execution, reference"
      note: "SIT is exempted from deep-import block but prefer facades"

    - file: tests/integration/test_uac_uic_schema_compat.py
      old: "from unified_api_contracts.canonical.domain import CanonicalBetOrder"
      new: "from unified_api_contracts.sports import CanonicalBetOrder"
      note: "Or from unified_api_contracts import CanonicalBetOrder"

    - file: tests/integration/test_uac_deep_import_health.py
      note: "This test validates deep imports work. Update paths to
             validate FACADE imports work instead. Rename to
             test_uac_facade_import_health.py"

    - file: tests/smoke/test_layer0_contracts.py
      old: "from unified_api_contracts import schemas"
      new: "from unified_api_contracts import market, execution, errors"
      note: "schemas module being deleted; test facade modules instead"

# ─────────────────────────────────────────────────────────────────────

# 7. NEW REPOS

# ─────────────────────────────────────────────────────────────────────

new_repos: unified_features_interface: name: unified-features-interface type: interface arch_tier: 2 role: interface
description: "External feature/derived data IO. Analogous to UMI but for computed features (economic, on-chain,
sports)." dependencies: - unified-api-contracts - unified-trading-library imports_from_uac: - "from
unified_api_contracts.features import CanonicalFeatureRecord" - "from unified_api_contracts.external.{source} import
..."

unified_feature_orchestration_library: name: unified-feature-orchestration-library type: library arch_tier: 2 role:
library description: "Feature pipeline routing, handler framework, scheduling. Sits between UFCL (calculators) and
services." dependencies: - unified-trading-library - unified-feature-calculator-library - unified-features-interface

unified_sports_reference_interface: name: unified-sports-reference-interface type: interface arch_tier: 2 role:
interface description: "Sports reference data (fixtures, teams, leagues). Distinct from URDI due to different update
triggers and data lifecycle." dependencies: - unified-api-contracts - unified-trading-library imports_from_uac: - "from
unified_api_contracts.sports_reference import CanonicalFixture, TeamMapping" - "from
unified_api_contracts.external.{source} import ..."

# ─────────────────────────────────────────────────────────────────────

# 8. WORKSPACE MANIFEST SCHEMA EVOLUTION

# ─────────────────────────────────────────────────────────────────────

workspace_manifest: schema_changes: - field: arch_tier action: split new_fields: tier: "integer (0-11), strict
topological build order level" role: "string enum: contracts | primitive | library | interface | service | api | ui |
infrastructure" reason: "arch_tier conflated conceptual role with build order"

    - field: workspace_infrastructure
      action: add
      description: "Array of repos that are tooling/meta (PM, Codex).
                    Not in topologicalOrder. Not code dependencies."
      value: [unified-trading-pm, unified-trading-codex]

    - field: runtime_clients
      action: add
      description: "Array of repos that provide runtime infrastructure.
                    Not code deps but runtime interaction."
      value: [ibkr-gateway-infra]

dependency_fixes: - repo: unified-trading-library remove_deps: [unified-market-interface,
unified-trade-execution-interface, unified-position-interface, unified-reference-data-interface] reason: "T1 library
cannot depend on T2 interfaces (tier violation)"

    - repo: unified-domain-client
      verify_tier: 3
      note: "UDC depends on interfaces (T2) so it is T3"

    - repo: all-services
      remove_explicit_deps: [unified-config-interface, unified-cloud-interface,
                              unified-events-interface]
      keep_transitive_via: unified-trading-library
      note: "Services get T0 primitives transitively through UTL.
             Explicit deps create maintenance overhead with no benefit."

new_repo_entries: - name: unified-features-interface tier: 5 role: interface dependencies: [unified-api-contracts,
unified-trading-library]

    - name: unified-feature-orchestration-library
      tier: 6
      role: library
      dependencies: [unified-trading-library,
                      unified-feature-calculator-library,
                      unified-features-interface]

    - name: unified-sports-reference-interface
      tier: 5
      role: interface
      dependencies: [unified-api-contracts, unified-trading-library]

topological_regeneration: command: "python3 scripts/manifest/generate_workspace_dag.py" note: "Must regenerate after all
dependency changes"

# ─────────────────────────────────────────────────────────────────────

# 9. PM SCRIPTS AND RULES

# ─────────────────────────────────────────────────────────────────────

unified_trading_pm: scripts: - file: scripts/tier-gate-check.sh change: "Read 'tier' (integer) instead of 'arch_tier'
(string). Add validation: tier N cannot import from tier > N. Add schema validation for new manifest fields."

    - file: scripts/manifest/generate_workspace_dag.py
      change: "Use 'tier' and 'role' fields. Render workspace_infrastructure
               repos as dashed boxes outside the main DAG. Render
               runtime_clients with dotted edges."

    - file: scripts/validation/check-integration-dep-coverage.py
      change: "Update to use 'tier' field. Verify T0→T1→T2→T3 invariant."

    - file: scripts/validators/validate_workspace_manifest.py
      change: "Add schema validation for 'tier', 'role',
               'workspace_infrastructure', 'runtime_clients'.
               Reject 'arch_tier' (deprecated)."

    - file: scripts/validation/pre-flight-audit.sh
      change: "Update tier references from arch_tier to tier."

cursor_rules: new_rules: - name: uac-import-surface-enforcement.mdc location: .cursor/rules/imports/ content: | ALLOWED
imports from unified_api_contracts: from unified_api_contracts import X # level 1 from unified_api_contracts.{domain}
import X # level 2 facade from unified_api_contracts.external.{source} import X # level 3 from
unified_api_contracts.registry import X # level 3 from unified_api_contracts.testing import X # level 3

          BLOCKED (outside UAC):
            from unified_api_contracts.canonical.* import X
            from unified_api_contracts.normalize_utils.* import X
            from unified_api_contracts.config.* import X
            from unified_api_contracts.shared.* import X
            from unified_api_contracts.schemas.* import X
            from unified_api_contracts.external.{source}.schemas import X

          EXCEPTIONS:
            unified-internal-contracts: may import canonical.*
            system-integration-tests: may import any path

    update_rules:
      - file: .cursor/rules/imports/contracts-integration.mdc
        change: "Add facade import patterns. Remove references to
                 schemas/, shared/, config/ modules."

      - file: .cursor/rules/core/schema-governance-index.mdc
        change: "Update canonical domain structure to reflect
                 domain sub-packages. Add crosscutting section."

      - file: .cursor/rules/architecture/library-tier-architecture.mdc
        change: "Update tier diagram to use integer tiers.
                 Add workspace_infrastructure and runtime_clients."

      - file: .cursor/rules/core/search-before-implementing.mdc
        change: "Add unified-features-interface (UFI),
                 unified-feature-orchestration-library (UFOL),
                 unified-sports-reference-interface (USRI) to search list."

      - file: .cursor/rules/imports/library-init-exports.mdc
        change: "Add rule: UAC facade modules must re-export via __all__."

      - file: .cursor/rules/core/anti-patterns-quick-reference.mdc
        change: "Add row: 'Import from unified_api_contracts.canonical.*'
                 → 'Use facade: unified_api_contracts.{domain}'"

quality*gate_linter: description: "Add import-depth check to base-service.sh and base-library.sh" implementation: | # In
quality-gates base scripts, add step: # STEP N: UAC import surface enforcement rg 'from
unified_api_contracts\.canonical\.' "$SOURCE_DIR/" \
 --glob '!\*\*/test*_' --glob '!\*\*/conftest_' \
 && echo "FAIL: Deep canonical import found" && exit 1 || true rg 'from unified_api_contracts\.normalize_utils\.'
"$SOURCE_DIR/" \
        && echo "FAIL: Internal normalize_utils import found" && exit 1 || true
      rg 'from unified_api_contracts\.config\.' "$SOURCE_DIR/"
\
 && echo "FAIL: Deleted config module import found" && exit 1 || true rg 'from unified_api_contracts\.shared\.'
"$SOURCE_DIR/" \
        && echo "FAIL: Deleted shared module import found" && exit 1 || true
      rg 'from unified_api_contracts\.schemas\.' "$SOURCE_DIR/"
\
 && echo "FAIL: Deleted schemas module import found" && exit 1 || true exceptions: - repo: unified-api-contracts #
self-references allowed - repo: unified-internal-contracts # canonical neighbor - repo: system-integration-tests #
testing repo

# ─────────────────────────────────────────────────────────────────────

# 10. CODEX UPDATES

# ─────────────────────────────────────────────────────────────────────

unified_trading_codex: docs: - file: 02-data/contracts-scope-and-layout.md change: "Rewrite to document new UAC
structure: - Facade pattern explanation - canonical/domain/ sub-packages - canonical/crosscutting/ - normalize_utils/
(internal only) - registry/ (capability + venue_manifest) - external/ flat structure - Import surface rules with
examples"

    - file: 04-architecture/TIER-ARCHITECTURE.md
      change: "Update tier diagram to integer tiers.
               Add workspace_infrastructure and runtime_clients.
               Show facade import flow."

    - file: 04-architecture/data-flow-map.md
      change: "Add features stack data flow.
               Add sports reference data flow.
               Show facade boundaries."

    - file: 10-audit/ssot-reference-mapping.md
      change: "Update UAC section references.
               Add facade module → canonical internal mapping.
               Add new repos (UFI, UFOL, USRI)."

    - file: 00-SSOT-INDEX.md
      change: "Add entries for new facade modules, registry/capability,
               new repos."

# ─────────────────────────────────────────────────────────────────────

# 11. REGISTRY AND CAPABILITY MODEL

# ─────────────────────────────────────────────────────────────────────

registry_capability: new_file: unified_api_contracts/registry/capability.py description: "Per-source capability
declarations" schema: | class SourceCapability(BaseModel): source: str domains: list[str] # e.g. ["market", "execution"]
crosscutting: list[str] # e.g. ["rate_limits", "errors"] modes: list[str] # ["live", "batch", "paper"] environments:
list[str] # ["mainnet", "testnet"] auth_scope: list[str] # ["api_key", "oauth", "cert"] data_domains: list[str] #
["cefi", "defi", "sports", ...]

initial_sources: - binance, bybit, okx, deribit, coinbase, kraken # cefi - uniswap, aave, curve, balancer # defi -
betfair, betdaq, smarkets, pinnacle # sports - fred, ecb, barchart, ibkr # tradfi - alchemy, pyth, thegraph # defi-live

coverage_matrix: file: registry/coverage_matrix.py description: "Auto-generated: which sources provide which canonical
types. Domain × Source matrix."

# ─────────────────────────────────────────────────────────────────────

# 12. VCR / CASSETTE STORY

# ─────────────────────────────────────────────────────────────────────

vcr_cassettes: location: "external/{source}/mocks/\*.yaml stays co-located with source" drift_detection: description:
"Nightly CI job replays cassettes, compares to schemas" workflow: ".github/workflows/cassette-drift.yml (already exists
in UMI/URDI)" extension: "Add to all interface repos" replay_workflow: location: unified-trading-pm/scripts/replay/
description: "Record → validate → diff → alert pipeline"

# ─────────────────────────────────────────────────────────────────────

# 13. EXECUTION PHASES (ORDERED)

# ─────────────────────────────────────────────────────────────────────

execution_order: phase_0_manifest: repos: [unified-trading-pm] tasks: - "Split arch_tier → tier + role in
workspace-manifest.json" - "Add workspace_infrastructure, runtime_clients fields" - "Fix UTL dependency violations
(remove T2 interface deps)" - "Remove explicit T0 deps from services (transitive via UTL)" - "Add new repo entries (UFI,
UFOL, USRI)" - "Regenerate topological order and DAG SVG" - "Update tier-gate-check.sh" blocks: [phase_1]

phase_1_uac_foundations: repos: [unified-api-contracts] tasks: - "Create directory structure: canonical/domain/_,
crosscutting/_, normalize_utils/, registry/" - "Move venue_manifest → registry/" - "Move venue_rate_limits,
provider_modes → registry/" - "Move canonical/errors/ → canonical/crosscutting/errors/" - "Move canonical/normalize/ →
normalize_utils/" - "Move canonical_mappings.py → normalize_utils/common_mappings.py" - "Update all UAC-internal
imports" blocks: [phase_2, phase_3]

phase_2_canonical_reorg: repos: [unified-api-contracts] tasks: - "Split canonical/domain/\*.py → domain sub-packages" -
"Move external/sports/canonical/ → canonical/domain/sports/" - "Create canonical/crosscutting/ modules (rate_limits,
latency, etc.)" - "Create root-level facade files (market.py, execution.py, etc.)" - "Update **init**.py to re-export
via facades" - "Verify all existing top-level imports still work" blocks: [phase_3]

phase_3_external_flatten: repos: [unified-api-contracts] tasks: - "Flatten sports/sources/{provider} →
external/{provider}/" - "Flatten onchain/cryptoquant → external/cryptoquant/" - "Flatten macro/yahoo_finance →
external/yahoo_finance/" - "Add **init**.py re-exports to binance (sub-module consolidation)" - "Add **init**.py
re-exports to all other sources" - "Delete emptied directories (sports/, onchain/, macro/)" blocks: [phase_4]

phase_4_config_cleanup: repos: [unified-api-contracts, unified-trading-library, unified-config-interface,
unified-cloud-interface] tasks: - "Move LogLevel to UTL" - "Move trading_validation to UCI" - "Move cloud quota types to
UCI (cloud interface)" - "Delete UAC config/ directory entirely" - "Delete UAC shared/ and schemas/ directories" blocks:
[phase_5]

phase_5_downstream_imports: repos: [all interfaces, all services, UIC, SIT] tasks: - "Update LogLevel imports across 20+
services" - "Update 2 USEI canonical.execution imports → execution facade" - "Update UMI oddsjam/opticodds imports
(flatten)" - "Update UMI sports/protocol.py import" - "Update instruments-service sports canonical imports" - "Update
execution-service sports canonical imports" - "Update strategy-service canonical.options import" - "Update
trading-agent-service canonical.domain.derivatives imports" - "Update SIT deep imports to facades" - "Update binance
sub-module imports where needed" - "Remove noqa: qg-deep-import comments (no longer needed)" note: "This is the bulk of
downstream changes — but most repos need ONLY the LogLevel change. ~5 repos need additional fixes."

phase_6_linter_enforcement: repos: [unified-trading-pm] tasks: - "Add UAC import surface linter to base-service.sh" -
"Add UAC import surface linter to base-library.sh" - "Create uac-import-surface-enforcement.mdc cursor rule" - "Update
existing cursor rules" - "Run full workspace quality gates to verify" blocks: [phase_7]

phase_7_registry_capability: repos: [unified-api-contracts] tasks: - "Build registry/capability.py with SourceCapability
model" - "Backfill capability data for all 80+ sources" - "Generate coverage matrix" - "Add capability assertions to VCR
tests"

phase_8_new_repos: repos: [unified-features-interface, unified-feature-orchestration-library,
unified-sports-reference-interface] tasks: - "Create repos from canonical template (scripts/setup.sh)" - "Register in
workspace-manifest.json" - "Implement core interfaces" - "Migrate consumption from existing services"

phase_9_replay_drift: repos: [unified-trading-pm, unified-api-contracts, all interfaces] tasks: - "Build PM replay
workflow scripts" - "Extend cassette-drift.yml to all interface repos" - "Add VCR capability assertions" - "Set up
nightly drift detection"

phase_10_guardrails: repos: [unified-trading-library, all services] tasks: - "Add fail-fast error classes to UTL" - "Add
preflight capability checks (mode/env validation)" - "Standardize raw→canonical pipeline in adapters" - "Remove
duplicate normalization logic from services"

# ─────────────────────────────────────────────────────────────────────

# IMPACT SUMMARY

# ─────────────────────────────────────────────────────────────────────

impact_summary: uac_internal: files_moved: "~100+ (canonical splits, normalize moves, external flattens)" files_created:
"~15 facades + ~10 **init**.py + capability.py" files_deleted: "config/ (7), shared/ (1), schemas/ (1), emptied dirs"

downstream_impact: zero_change_repos: 35 loglevel_only_repos: 15 loglevel_plus_minor_repos: 5 significant_change_repos:
3 # UMI, USEI, SIT note: "The facade pattern reduces downstream changes by ~80% compared to the v1 deep-import approach"

linter_rule: new_blocked_patterns: 5 repos_exempted: 3 # UAC, UIC, SIT existing_noqa_removed: "~50 noqa: qg-deep-import
comments"
