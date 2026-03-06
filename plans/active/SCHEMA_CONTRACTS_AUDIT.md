# Schema Contracts Full Audit

**Status:** Audit complete. Remediation in progress.
**Date:** 2026-03-05 | **Last verified:** 2026-03-06
**Plan:** [schema_contracts_full_audit.plan.md](schema_contracts_full_audit.plan.md)
**Scope:** All 60+ repos scanned across 10 parallel agents
**Audit result:** Violations catalogued. Codex/cursor rules updated. Quality gates blocking.
**Remediation blockers remaining:**
- `unified-internal-contracts/unified_internal_contracts/domain/` scaffolded 2026-03-06 (was missing); service schema migration can now begin per Section 6 priority order.
- `InstrumentRecord` CONFLICT (UAC vs UIC) must be resolved before migration of instrument schemas.

---

## Executive Summary

| Category                                                 | Count                 | Repos Affected                                                         |
| -------------------------------------------------------- | --------------------- | ---------------------------------------------------------------------- |
| **MISPLACE-UAC** (adapter models not in UAC)             | **90**                | unified-market-interface (52), unified-sports-execution-interface (38) |
| **MISPLACE-UIC** (domain/cross-repo schemas outside UIC) | **44**                | 8 repos                                                                |
| **DUPLICATE** (same concept in 2+ places)                | **16**                | UAC+UIC (4), interfaces (2), adapter overlap (~10)                     |
| **CONFLICT** (same name, incompatible definitions)       | **1**                 | InstrumentRecord (UAC vs UIC)                                          |
| **CONFLICT-RISK** (local models diverging from UIC)      | **2**                 | features-volatility-service                                            |
| **CIRCULAR** (import direction violates tier DAG)        | **1 file**            | test_ac_uic_alignment.py in UAC                                        |
| **ORPHAN** (schema_registry.json stale entries)          | **4**                 | unified-internal-contracts                                             |
| **Repos with zero violations**                           | **~38 / ~54 audited** | See Section 2                                                          |

**Critical pre-conditions for remediation:**

1. `InstrumentRecord` CONFLICT must be resolved first (UAC and UIC define incompatible versions)
2. `unified-internal-contracts/unified_internal_contracts/domain/` directory must be created before service schemas can migrate
3. `schema-service-owned.mdc` and `schema-governance.md` actively enforce the OLD (wrong) pattern — retire/replace before any migration

---

## Master Schema Placement Rules (Authoritative)

| Category                                                       | Where It Lives                                          | Rationale                                                       |
| -------------------------------------------------------------- | ------------------------------------------------------- | --------------------------------------------------------------- |
| Raw venue API request/response models                          | UAC `unified_api_contracts_external/<venue>/schemas.py` | External API shapes; UAC is normalization SSOT                  |
| Adapter-private Pydantic models (`_<venue>_models.py`)         | UAC `unified_api_contracts_external/<venue>/schemas.py` | They parse external API responses — same rule, no exceptions    |
| Normalization schemas (map raw → canonical)                    | UAC `unified_api_contracts/schemas/`                    | Normalization layer                                             |
| Canonical types output by normalization                        | UAC `unified_normalised_contracts/`                     | Normalization output = external-derived canonical               |
| Canonical types used in internal messaging/pub-sub             | UIC (relevant domain subdirectory)                      | Messaging contracts                                             |
| Event envelopes (lifecycle, domain publish events)             | UIC `events.py` / `pubsub.py`                           | Internal messaging                                              |
| Shared identifiers cross-imported by 2+ repos                  | UIC `reference/`                                        | Cross-repo contract                                             |
| Error records for cross-repo error handling                    | UIC `schemas/errors.py`                                 | Internal contract                                               |
| Service domain data schemas (primary output data shape)        | UIC `domain/<service-name>/`                            | All schemas in UIC; accessed via UTL/UDC                        |
| Service-to-library protocol routing                            | Library tier (UTL, UCI, etc.)                           | Library owns protocol; schema lives in UIC                      |
| Interface-public types cross-imported elsewhere                | UIC                                                     | Determined by actual import graph                               |
| Interface-internal types not cross-imported                    | Interface (stays)                                       | Not a cross-repo contract                                       |
| `SchemaDefinition` / `ColumnSchema` (parquet shape descriptor) | Service `schemas/output_schemas.py`                     | Infrastructure concern — NOT a data contract. Stays in service. |

> **SchemaDefinition distinction:** `SchemaDefinition` and `ColumnSchema` objects (from `unified-trading-library`) are parquet schema enforcement descriptors — they tell the library HOW to validate a write. They are NOT Pydantic data contracts. They stay in the service. The corresponding Pydantic/TypedDict/dataclass model that describes the data SHAPE belongs in UIC.

---

## Section 1 — UAC/UIC Internal Audit

### 1a. UAC Schema Inventory (Summary)

| Category                   | File(s)                                                                                                                                                                                                                          | Count            | Status                                         |
| -------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------- | ---------------------------------------------- |
| Venue-specific raw schemas | `unified_api_contracts_external/<venue>/schemas.py` (75+ venues)                                                                                                                                                                 | 200+ classes     | CORRECT-UAC                                    |
| Normalization schemas      | `schemas/defi.py`, `derivatives.py`, `websocket.py`, `errors.py`, `rate_limits.py`, `prediction_market_arb.py`, `accounts.py`, `analytics.py`, `risk.py`, `protocol_sdks.py`, `cex_withdrawals.py`, `transfers.py`, `latency.py` | ~70 classes      | CORRECT-UAC                                    |
| Canonical domain types     | `unified_normalised_contracts/domain.py`                                                                                                                                                                                         | 29 classes       | CORRECT-UAC (some DUPLICATE with UIC — see 1c) |
| Error canonicals           | `unified_normalised_contracts/errors.py`                                                                                                                                                                                         | 23 error classes | CORRECT-UAC                                    |
| **Total audited**          |                                                                                                                                                                                                                                  | **~322 classes** |                                                |

### 1b. UIC Schema Inventory (Summary)

| Category               | File(s)                                 | Count                           | Status                                        |
| ---------------------- | --------------------------------------- | ------------------------------- | --------------------------------------------- |
| Market data canonicals | `market_data/` (8 files)                | 11 native + 5 imported from UAC | CORRECT-UIC                                   |
| Position schemas       | `positions/` (4 files)                  | 5 classes                       | CORRECT-UIC                                   |
| Reference schemas      | `reference/` (2 files)                  | 6 classes                       | CORRECT-UIC (InstrumentRecord = CONFLICT)     |
| Event envelopes        | `events.py`                             | 25+ classes                     | CORRECT-UIC                                   |
| Pub/Sub messages       | `pubsub.py`                             | 16 classes                      | CORRECT-UIC                                   |
| Risk management        | `risk.py`                               | 12 classes                      | CORRECT-UIC                                   |
| ML pipeline            | `ml.py`                                 | 9 classes                       | CORRECT-UIC (2 = DUPLICATE with ml-interface) |
| Feature engineering    | `features.py`                           | 6 classes                       | CORRECT-UIC                                   |
| WebSocket lifecycle    | `connectivity/websocket_lifecycle.py`   | 7 classes                       | CORRECT-UIC                                   |
| Error/audit            | `schemas/errors.py`, `schemas/audit.py` | 8 classes                       | CORRECT-UIC                                   |
| Messaging              | `messaging.py`                          | 2 enums                         | CORRECT-UIC                                   |
| DeFi gas               | `defi.py`                               | 2 classes                       | CORRECT-UIC                                   |
| Alerting               | `alerting/__init__.py`                  | 1 class                         | CORRECT-UIC                                   |
| Reporting              | `reporting/fee_structure.py`            | 1 class                         | CORRECT-UIC                                   |
| **domain/ directory**  |                                         | **MISSING**                     | Must be created                               |
| **Total audited**      |                                         | **~110 classes**                |                                               |

### 1c. Duplicate/Conflict Between UAC and UIC

| Class Name                     | UAC Location                                                                                                            | UIC Location                                                                                                                           | Field Diff                                                                                                                                                                    | Verdict                           |
| ------------------------------ | ----------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------- |
| **InstrumentRecord**           | `unified_normalised_contracts/domain.py:47` (76 fields, `float`, raw symbols, GCS parquet schema)                       | `reference/instrument.py:49` (31 fields, `Decimal`, normalized, URDI adapter contract)                                                 | MAJOR: different field count, different numeric types (float vs Decimal), different InstrumentType enum values (SPOT_PAIR/PERPETUAL vs spot/perp), non-overlapping field sets | **CONFLICT — must rename one**    |
| **CanonicalOraclePrice**       | `domain.py:340` (5 fields: oracle, pair, price, timestamp, confidence)                                                  | `market_data/defi.py:78` (7 fields: feed_id, protocol, asset, price, confidence, publish_time)                                         | Different fields, different semantics                                                                                                                                         | **DUPLICATE — resolve ownership** |
| **CanonicalStakingRate**       | `domain.py:350` (4 fields: protocol, asset, apy, timestamp, chain="")                                                   | `market_data/defi.py:67` (5 fields: protocol, chain, asset, apy, total_staked, rewards_per_second)                                     | Different field counts                                                                                                                                                        | **DUPLICATE — resolve ownership** |
| **CanonicalOptionsChainEntry** | `domain.py:303` (15 fields: timestamp, venue, symbol, underlying, strike, option_type, expiration, bid/ask, iv, greeks) | `market_data/options_chain.py:12` (10 fields: underlying, expiry, strike, put_call, bid, ask, last, iv, greeks, open_interest, volume) | Different field counts                                                                                                                                                        | **DUPLICATE — resolve ownership** |

**Resolution rule:** UAC owns canonicals that are the OUTPUT of normalizers (they normalize external venue data to canonical form). UIC owns canonicals used for MESSAGING (cross-service pub-sub). For the three DeFi/options duplicates: determine which one the normalizers produce and which one the services subscribe to.

### 1d. Orphaned Schemas in UAC

No orphaned Pydantic classes found. All UAC classes are exported in `__all__` or imported by UIC or interfaces.

### 1e. Stale schema_registry.json Entries (UIC)

| Registered Schema         | Registry Module Path                                       | Actual State                                                                                                  |
| ------------------------- | ---------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| CanonicalOrderBook        | `unified_internal_contracts.market_data.orderbook`         | File does not exist in source — schema lives in UAC `domain.py`, re-imported by UIC `market_data/__init__.py` |
| CanonicalTrade            | `unified_internal_contracts.market_data.trade`             | Same — no `trade.py` source file                                                                              |
| CanonicalDerivativeTicker | `unified_internal_contracts.market_data.derivative_ticker` | Same — no `derivative_ticker.py` source file                                                                  |
| CanonicalLiquidation      | `unified_internal_contracts.market_data.liquidation`       | Same — no `liquidation.py` source file                                                                        |

**Action:** Update registry entries to reflect actual locations in UAC + the re-import path via UIC `market_data/__init__.py`.

### 1f. Tier Boundary: UIC→UAC Import (Existing)

**File:** `unified-internal-contracts/unified_internal_contracts/market_data/__init__.py` lines 3–9

```python
from unified_api_contracts.unified_normalised_contracts import (
    CanonicalDerivativeTicker,
    CanonicalLiquidation,
    CanonicalOrderBook,
    CanonicalTicker,
    CanonicalTrade,
)
```

**Status:** PERMITTED — UIC importing UAC is the correct direction.
**Formalization needed:** workspace-manifest.json L2 must be split: UAC (L2a) before UIC (L2b).

### 1g. CIRCULAR Violation in UAC

**File:** `unified-api-contracts/tests/test_ac_uic_alignment.py`
Imports from `unified_internal_contracts` inside an `unified-api-contracts` test file. UAC is a T0 leaf and must not import UIC even in tests.
**Action:** Move `test_ac_uic_alignment.py` to `unified-internal-contracts/tests/` (higher tier; UIC may import UAC).

---

## Section 2 — Violations by Repo

### T0 Libraries: unified-events-interface, unified-cloud-interface, execution-algo-library, matching-engine-library

**Result: ALL CLEAN** — 23 schemas, all `CORRECT-LOCAL`. No forbidden imports. No cross-repo violations.

### T1 Libraries: unified-reference-data-interface, unified-config-interface, unified-trading-library

**Result: ALL CLEAN** — 43 schemas.

- UCI enums (Venue, InstrumentType, InstructionType) are cross-imported and correctly placed in UCI.
- URDI schemas (CanonicalOptionsChain, CanonicalExpiryCalendar, FundingRateRef, OHLCVRef) are NOT cross-imported. Currently `CORRECT-LOCAL` per audit.
- UTL provides no schema access pattern for services yet (gap for remediation).

### unified-market-interface (T2)

| Class Name                                                                                                                                      | File                                                     | Verdict                                                              | Target                                                        |
| ----------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------- | -------------------------------------------------------------------- | ------------------------------------------------------------- |
| DeribitError, DeribitJsonRpcResponse, DeribitTrade, DeribitPosition, DeribitInstrument, DeribitTickerResult, DeribitAccountSummary (+ wrappers) | `adapters/_deribit_models.py` (30+ models)               | MISPLACE-UAC (some DUPLICATE with existing UAC deribit schemas)      | `unified_api_contracts_external/deribit/schemas.py`           |
| GraphToken, GraphUniswapPool, GraphUniswapSwap, GraphBalancerPool, GraphCurveSwap (+15 more)                                                    | `adapters/defi/_defi_graph_models.py` (21+ models)       | MISPLACE-UAC (NEW — no UAC equivalent for The Graph subgraph models) | `unified_api_contracts_external/thegraph/schemas.py` (create) |
| RateLimitConfig                                                                                                                                 | `base.py`                                                | CORRECT-LOCAL                                                        | —                                                             |
| VenueMapping                                                                                                                                    | `models/venue_config.py`                                 | CORRECT-LOCAL                                                        | —                                                             |
| **schemas.py re-exports**                                                                                                                       | Re-exports CanonicalTicker, CanonicalTrade etc. from UAC | CORRECT                                                              | —                                                             |

**Totals: MISPLACE-UAC: 51 | CORRECT-LOCAL: 2**

### unified-trade-execution-interface (T2)

**Result: ALL CLEAN** — OrderType, TimeInForce, StopLimitOrder, StopMarketOrder, ExitAlgoType, ExitInstruction, ExecutionStatus, ExecutionResult, SignalExecutionResult, MarginState, AccountState, CanonicalPartialFill, CanonicalOrderRejection, CanonicalOrderAmendment = all CORRECT-LOCAL. schemas.py correctly re-exports from UAC.

### unified-ml-interface (T2)

| Class Name                                                                                                   | File        | Verdict       | Notes                                                 |
| ------------------------------------------------------------------------------------------------------------ | ----------- | ------------- | ----------------------------------------------------- |
| ModelVariantConfig                                                                                           | `models.py` | DUPLICATE     | Also in UIC `ml.py` — UIC version should be canonical |
| ModelMetadata                                                                                                | `models.py` | DUPLICATE     | Also in UIC `ml.py` — UIC version should be canonical |
| HyperparameterConfig, FeatureConfig, TrainingData, PredictionSnapshot, CascadeConfig, CascadePredictionEvent | `models.py` | CORRECT-LOCAL | Not cross-imported elsewhere                          |

**Totals: DUPLICATE: 2 | CORRECT-LOCAL: 6**

### unified-feature-calculator-library (T2), unified-position-interface (T2), unified-defi-execution-interface (T2)

**Result: ALL CLEAN.**

### unified-sports-execution-interface (T2)

| Venue     | File                            | Models Count | UAC Status    | Verdict                  |
| --------- | ------------------------------- | ------------ | ------------- | ------------------------ |
| Matchbook | `adapters/_matchbook_models.py` | 12 models    | EXISTS in UAC | MISPLACE-UAC + DUPLICATE |
| Smarkets  | `adapters/_smarkets_models.py`  | 9 models     | EXISTS in UAC | MISPLACE-UAC + DUPLICATE |
| Betdaq    | `adapters/_betdaq_models.py`    | 6 models     | EXISTS in UAC | MISPLACE-UAC + DUPLICATE |
| Pinnacle  | `adapters/_pinnacle_models.py`  | 9 models     | EXISTS in UAC | MISPLACE-UAC + DUPLICATE |
| OddsAPI   | `adapters/_odds_api_models.py`  | 6 models     | EXISTS in UAC | MISPLACE-UAC + DUPLICATE |
| OneXBet   | `adapters/_onexbet_models.py`   | 4 models     | NOT in UAC    | MISPLACE-UAC (new)       |

**Totals: MISPLACE-UAC: 38 (34 duplicate with UAC, 4 new)**

### unified-domain-client (T3)

| Class Name                                 | File                        | Verdict       | Notes                                                                                                    |
| ------------------------------------------ | --------------------------- | ------------- | -------------------------------------------------------------------------------------------------------- |
| InstrumentKey                              | `schemas/instrument_key.py` | MISPLACE-UIC  | Cross-imported by instruments-service, market-tick-data-service + others. Should be in UIC `reference/`. |
| Other validators/utilities (5 dataclasses) | Various                     | CORRECT-LOCAL | Not cross-imported                                                                                       |

**Totals: MISPLACE-UIC: 1 | CORRECT-LOCAL: 5**

### execution-service

| Class Name                             | File                    | Type        | Verdict       | UIC Target                           |
| -------------------------------------- | ----------------------- | ----------- | ------------- | ------------------------------------ |
| SportsBetResult                        | `sports/models.py`      | Domain data | MISPLACE-UIC  | `domain/execution-service/sports.py` |
| SportsVenueScore                       | `sports/models.py`      | Domain data | MISPLACE-UIC  | `domain/execution-service/sports.py` |
| SportsVenueSelection                   | `sports/models.py`      | Domain data | MISPLACE-UIC  | `domain/execution-service/sports.py` |
| ManualInstructionRequest/Response etc. | `api/manual_schemas.py` | HTTP DTO    | CORRECT-LOCAL | —                                    |

**Totals: MISPLACE-UIC: 3 | CORRECT-LOCAL: 5**

### strategy-service

| Class Name                                                                     | File                      | Type          | Verdict              | UIC Target                              |
| ------------------------------------------------------------------------------ | ------------------------- | ------------- | -------------------- | --------------------------------------- |
| PositionData, ExposureData, RiskData, PnLData, OrderData, StrategyDecisionData | `models/domain_data.py`   | Domain data   | MISPLACE-UIC         | `domain/strategy-service/monitoring.py` |
| Order                                                                          | `models/order.py`         | Domain data   | MISPLACE-UIC         | `domain/strategy-service/order.py`      |
| Event wrappers (PositionSnapshot, RiskAssessment etc.)                         | `models/domain_events.py` | CORRECT-LOCAL | Internal event state | —                                       |

**Totals: MISPLACE-UIC: 7 | CORRECT-LOCAL: 7**

### strategy-validation-service, risk-and-exposure-service, alerting-service

**Result: ALL CLEAN.** Risk-and-exposure correctly imports from UIC (RiskPosition, RiskMetrics etc.). Alerting correctly uses UIC AlertEvent.

### market-data-processing-service

| Class Name                                             | File                           | Type                              | Verdict         | UIC Target                                        |
| ------------------------------------------------------ | ------------------------------ | --------------------------------- | --------------- | ------------------------------------------------- |
| UnifiedCandleSchema, MarketState, DataType, CandleData | `models.py`                    | Domain data                       | MISPLACE-UIC    | `domain/market-data-processing/candle_schema.py`  |
| InstrumentInfo, InstrumentMetadata, CandleOutput       | `app/adapters/base_adapter.py` | Cross-service adapter contract    | MISPLACE-UIC    | `domain/market-data-processing/adapter_models.py` |
| PROCESSED_CANDLE_SCHEMA, RATE_INDEX_SCHEMA             | `schemas/output_schemas.py`    | SchemaDefinition (infrastructure) | CORRECT (stays) | —                                                 |
| ProcessingConfig, ProcessingResult etc.                | `models.py`                    | Internal helper                   | CORRECT-LOCAL   | —                                                 |

**Totals: MISPLACE-UIC: 7 | CORRECT (SchemaDefinition): 2 | CORRECT-LOCAL: 8**

### market-tick-data-service

| Class Name                                                                                                                                       | File                           | Type                              | Verdict             | Notes                                                                                               |
| ------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------ | --------------------------------- | ------------------- | --------------------------------------------------------------------------------------------------- |
| TRADES_SCHEMA, BOOK_SNAPSHOT_5_SCHEMA, DERIVATIVE_TICKER_SCHEMA, LIQUIDATIONS_SCHEMA, OHLCV_1M_SCHEMA, QUOTES_SCHEMA, LIQUIDITY_SNAPSHOTS_SCHEMA | `schemas/output_schemas.py`    | SchemaDefinition (infrastructure) | **CORRECT (stays)** | SchemaDefinition objects are operational parquet descriptors, not data contracts. Stays in service. |
| ValidationResult                                                                                                                                 | `models/validation_schemas.py` | Internal                          | CORRECT-LOCAL       | —                                                                                                   |

**Totals: CORRECT (SchemaDefinition): 7 | CORRECT-LOCAL: 1**

> **Note:** Agent 7 initially flagged these as MISPLACE-UIC. Corrected after Agent 8 clarification: `SchemaDefinition` objects are infrastructure concerns, not data contracts. The canonical data shapes for tick data already live in UIC `market_data/` (CanonicalTrade, CanonicalOrderBook, etc.). No violation.

### market-data-api

| Class Name        | File                           | Type                              | Verdict      | UIC Target                                   |
| ----------------- | ------------------------------ | --------------------------------- | ------------ | -------------------------------------------- |
| OrderBookSnapshot | `core/orderbook_subscriber.py` | Domain data (API response format) | MISPLACE-UIC | `domain/market-data-api/orderbook_schema.py` |

**Totals: MISPLACE-UIC: 1**

### instruments-service

| Class Name         | File                        | Type                              | Verdict             | Notes                                                                                          |
| ------------------ | --------------------------- | --------------------------------- | ------------------- | ---------------------------------------------------------------------------------------------- |
| INSTRUMENTS_SCHEMA | `schemas/output_schemas.py` | SchemaDefinition (infrastructure) | **CORRECT (stays)** | Operational parquet descriptor. Actual instrument data shape in UIC `reference/instrument.py`. |

**Totals: CORRECT (SchemaDefinition): 1**

### features-calendar-service

| Class Name                                   | File                        | Type                              | Verdict             | Notes                    |
| -------------------------------------------- | --------------------------- | --------------------------------- | ------------------- | ------------------------ |
| TIME_FEATURES_SCHEMA, ECONOMIC_EVENTS_SCHEMA | `schemas/output_schemas.py` | SchemaDefinition (infrastructure) | **CORRECT (stays)** | Operational descriptors. |

**Totals: CORRECT (SchemaDefinition): 2**

### features-delta-one-service, features-cross-instrument-service, features-multi-timeframe-service

**Result: ALL CLEAN.** SchemaDefinition output_schemas.py files are infrastructure. UIC `features.py` has DeltaOneFeatureRecord, CrossInstrumentFeatures, CrossTimeframeFeatures as the canonical contracts.

### features-volatility-service

| Class Name                          | File                | Type            | Verdict         | UIC Equivalent                                    |
| ----------------------------------- | ------------------- | --------------- | --------------- | ------------------------------------------------- |
| VolatilityFeatures                  | `models.py`         | Local dataclass | CONFLICT-RISK   | `OptionsIvRecord` in UIC `features.py`            |
| FuturesTermStructureFeatures        | `models.py`         | Local dataclass | CONFLICT-RISK   | `FuturesTermStructureRecord` in UIC `features.py` |
| OptionQuote, VolatilitySurfacePoint | `models.py`         | Internal helper | CORRECT-LOCAL   | —                                                 |
| SchemaDefinition objects            | `output_schemas.py` | Infrastructure  | CORRECT (stays) | —                                                 |

> **CONFLICT-RISK:** Service maintains local dataclasses that mirror UIC contracts. Not a hard violation but risks field-level divergence. Recommendation: service imports from UIC instead of maintaining local copies.

### features-onchain-service

| Class Name              | File                        | Type                                  | Verdict         | UIC Target                                         |
| ----------------------- | --------------------------- | ------------------------------------- | --------------- | -------------------------------------------------- |
| OnchainFeature          | `models.py` (lines 10–46)   | Domain data (on-chain feature output) | MISPLACE-UIC    | Add as `OnchainFeatureRecord` to UIC `features.py` |
| ONCHAIN_FEATURES_SCHEMA | `schemas/output_schemas.py` | SchemaDefinition                      | CORRECT (stays) | —                                                  |

**Totals: MISPLACE-UIC: 1**

### features-sports-service

| Schema                                                                                                                                                                                                                                                                          | File                        | Type                                        | Verdict      | UIC Target                                                                                             |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------- | ------------------------------------------- | ------------ | ------------------------------------------------------------------------------------------------------ |
| FIXTURE_STATS_COLUMNS, FIXTURE_EVENTS_COLUMNS, FIXTURE_LINEUPS_COLUMNS, FIXTURE_PLAYER_STATS_COLUMNS, INJURIES_COLUMNS, PLAYERS_COLUMNS, VENUES_COLUMNS, FIXTURES_COLUMNS, LEAGUES_COLUMNS, TEAMS_COLUMNS, REFEREES_COLUMNS, COACHES_COLUMNS, STANDINGS_COLUMNS, ROUNDS_COLUMNS | `schemas/output_schemas.py` | Column lists (not SchemaDefinition objects) | MISPLACE-UIC | Add as TypedDict/dataclass in new UIC `sports.py` module: FixtureStatsRecord, FixtureEventsRecord etc. |

> **Note:** Unlike other features services, these are raw Python lists of column names — NOT `SchemaDefinition` objects. They are effectively data contracts that consumers need to understand sports data shape. They must be formalized as UIC TypedDicts.

**Totals: MISPLACE-UIC: 14**

### Services Group D (ml-inference, ml-training, pnl-attribution, position-balance-monitor) + APIs

**Result: ALL CLEAN** — 88 schemas audited, all CORRECT-LOCAL.

- ml-inference correctly migrated to UIC (InferenceRequest/InferenceResult from Plan #11 Phase 1).
- API services (execution-results-api, client-reporting-api, deployment-api) correctly use HTTP-only FastAPI models as CORRECT-LOCAL.

---

## Section 3 — Aggregate Violation Catalogue

### 3a. MISPLACE-UAC (90 total — adapter models that must move to UAC)

| File                                                               | Models                                                                                                                                                                                     | Count | UAC Target                                                                           | Priority |
| ------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----- | ------------------------------------------------------------------------------------ | -------- |
| `unified-market-interface/adapters/_deribit_models.py`             | DeribitError, DeribitJsonRpcResponse, DeribitTrade, DeribitOrderInfo, DeribitOrderResult, DeribitPosition, DeribitInstrument, DeribitTickerResult, DeribitAccountSummary + wrapper classes | 30+   | `unified_api_contracts_external/deribit/schemas.py` (expand)                         | HIGH     |
| `unified-market-interface/adapters/defi/_defi_graph_models.py`     | GraphToken, GraphUniswapPool, GraphUniswapSwap, GraphUniswapV2Pair, GraphBalancerPool, GraphCurveSwap + 15 more                                                                            | 21+   | `unified_api_contracts_external/thegraph/schemas.py` (create)                        | HIGH     |
| `unified-sports-execution-interface/adapters/_matchbook_models.py` | MatchbookAuthResponse + 11 more                                                                                                                                                            | 12    | `unified_api_contracts_external/matchbook/schemas.py` (already exists — deduplicate) | MEDIUM   |
| `unified-sports-execution-interface/adapters/_smarkets_models.py`  | SmarketsErrorResponse + 8 more                                                                                                                                                             | 9     | `unified_api_contracts_external/smarkets/schemas.py` (exists — deduplicate)          | MEDIUM   |
| `unified-sports-execution-interface/adapters/_betdaq_models.py`    | BetdaqErrorResponse + 5 more                                                                                                                                                               | 6     | `unified_api_contracts_external/betdaq/schemas.py` (exists — deduplicate)            | MEDIUM   |
| `unified-sports-execution-interface/adapters/_pinnacle_models.py`  | PinnacleMoneyline + 8 more                                                                                                                                                                 | 9     | `unified_api_contracts_external/pinnacle/schemas.py` (exists — deduplicate)          | MEDIUM   |
| `unified-sports-execution-interface/adapters/_odds_api_models.py`  | OddsApiOutcome + 5 more                                                                                                                                                                    | 6     | `unified_api_contracts_external/odds_api/schemas.py` (exists — deduplicate)          | MEDIUM   |
| `unified-sports-execution-interface/adapters/_onexbet_models.py`   | OneXBetOutcome, OneXBetMarket, OneXBetOddsResponse, OneXBetEvent                                                                                                                           | 4     | `unified_api_contracts_external/onexbet/schemas.py` (create)                         | LOW      |

### 3b. MISPLACE-UIC (44 total — cross-repo/domain schemas outside UIC)

| Schema(s)                                                                                                                                                                                                                                                                                      | Current Location                                                          | UIC Target                                                                   | Priority |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | -------- |
| InstrumentKey                                                                                                                                                                                                                                                                                  | `unified-domain-client/unified_domain_client/schemas/instrument_key.py`   | `unified_internal_contracts/reference/instrument_key.py`                     | HIGH     |
| SportsBetResult, SportsVenueScore, SportsVenueSelection                                                                                                                                                                                                                                        | `execution-service/execution_service/sports/models.py`                    | `unified_internal_contracts/domain/execution-service/sports.py`              | MEDIUM   |
| PositionData, ExposureData, RiskData, PnLData, OrderData, StrategyDecisionData                                                                                                                                                                                                                 | `strategy-service/strategy_service/models/domain_data.py`                 | `unified_internal_contracts/domain/strategy-service/monitoring.py`           | MEDIUM   |
| Order                                                                                                                                                                                                                                                                                          | `strategy-service/strategy_service/models/order.py`                       | `unified_internal_contracts/domain/strategy-service/order.py`                | MEDIUM   |
| UnifiedCandleSchema, MarketState, DataType, CandleData                                                                                                                                                                                                                                         | `market-data-processing-service/market_data_processing_service/models.py` | `unified_internal_contracts/domain/market-data-processing/candle_schema.py`  | MEDIUM   |
| InstrumentInfo, InstrumentMetadata, CandleOutput                                                                                                                                                                                                                                               | `market-data-processing-service/.../base_adapter.py`                      | `unified_internal_contracts/domain/market-data-processing/adapter_models.py` | MEDIUM   |
| OrderBookSnapshot                                                                                                                                                                                                                                                                              | `market-data-api/market_data_api/core/orderbook_subscriber.py`            | `unified_internal_contracts/domain/market-data-api/orderbook_schema.py`      | LOW      |
| OnchainFeature                                                                                                                                                                                                                                                                                 | `features-onchain-service/features_onchain_service/models.py`             | Add as `OnchainFeatureRecord` to `unified_internal_contracts/features.py`    | MEDIUM   |
| FIXTURE_STATS_COLUMNS, FIXTURE_EVENTS_COLUMNS, FIXTURE_LINEUPS_COLUMNS, FIXTURE_PLAYER_STATS_COLUMNS, INJURIES_COLUMNS, PLAYERS_COLUMNS, VENUES_COLUMNS, FIXTURES_COLUMNS, LEAGUES_COLUMNS, TEAMS_COLUMNS, REFEREES_COLUMNS, COACHES_COLUMNS, STANDINGS_COLUMNS, ROUNDS_COLUMNS (column lists) | `features-sports-service/schemas/output_schemas.py`                       | Formalize as 14 TypedDicts in new `unified_internal_contracts/sports.py`     | LOW      |

### 3c. DUPLICATE — Same Concept in Multiple Places

| Concept                                                                      | Location 1                                                                              | Location 2                                                                      | Resolution                                                                                                                                                   |
| ---------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| InstrumentRecord                                                             | `unified-api-contracts: unified_normalised_contracts/domain.py` (76 fields, GCS schema) | `unified-internal-contracts: reference/instrument.py` (31 fields, URDI adapter) | **CONFLICT** — rename one. UAC version → `InstrumentRecordRaw` or `InstrumentWarehouseRow`. UIC version keeps `InstrumentRecord`.                            |
| CanonicalOraclePrice                                                         | `unified-api-contracts: domain.py:340` (5 fields)                                       | `unified-internal-contracts: market_data/defi.py:78` (7 fields)                 | Determine which is the normalizer output (UAC) and which is the messaging canonical (UIC). If fields differ, reconcile or keep both with distinct semantics. |
| CanonicalStakingRate                                                         | `unified-api-contracts: domain.py:350` (4 fields)                                       | `unified-internal-contracts: market_data/defi.py:67` (5 fields)                 | Same resolution as CanonicalOraclePrice                                                                                                                      |
| CanonicalOptionsChainEntry                                                   | `unified-api-contracts: domain.py:303` (15 fields)                                      | `unified-internal-contracts: market_data/options_chain.py:12` (10 fields)       | Same                                                                                                                                                         |
| ModelVariantConfig                                                           | `unified-ml-interface: models.py`                                                       | `unified-internal-contracts: ml.py`                                             | UIC version is canonical; ml-interface should import from UIC                                                                                                |
| ModelMetadata                                                                | `unified-ml-interface: models.py`                                                       | `unified-internal-contracts: ml.py`                                             | UIC version is canonical; ml-interface should import from UIC                                                                                                |
| Sports venue adapter models (Matchbook, Smarkets, Betdaq, Pinnacle, OddsAPI) | `unified-sports-execution-interface: adapters/_*_models.py`                             | `unified-api-contracts: unified_api_contracts_external/<venue>/schemas.py`      | Remove from sports interface; import from UAC                                                                                                                |

### 3d. CONFLICT — Incompatible Definitions

| Class                                                                 | Conflict                                                                                                                                                                        | Resolution                                                                                                                                   |
| --------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| **InstrumentRecord**                                                  | UAC (76 fields, `float`, SPOT_PAIR/PERPETUAL enum values, raw symbol mappings for GCS warehouse) vs UIC (31 fields, `Decimal`, spot/perp enum values, normalized exchange data) | Rename: UAC version → `InstrumentWarehouseRow`; UIC keeps `InstrumentRecord`. Update all UAC normalizers and GCS write code to use new name. |
| **VolatilityFeatures vs OptionsIvRecord** (RISK)                      | features-volatility-service defines local `VolatilityFeatures` dataclass; UIC has `OptionsIvRecord`. If fields diverge = conflict.                                              | Volatility service imports `OptionsIvRecord` from UIC instead of maintaining local copy. Remove local.                                       |
| **FuturesTermStructureFeatures vs FuturesTermStructureRecord** (RISK) | Same pattern                                                                                                                                                                    | Same resolution                                                                                                                              |

### 3e. ORPHAN — Defined but Never Imported

No true orphans found in UAC or UIC class definitions. However:

| Issue                                                                                                  | Location                   | Status                                                                                         |
| ------------------------------------------------------------------------------------------------------ | -------------------------- | ---------------------------------------------------------------------------------------------- |
| schema_registry.json points to `market_data.orderbook`, `.trade`, `.derivative_ticker`, `.liquidation` | UIC `schema_registry.json` | Stale entries — source files don't exist (classes live in UAC + re-imported). Update registry. |
| `test_ac_uic_alignment.py`                                                                             | UAC `tests/`               | CIRCULAR — must move to UIC tests.                                                             |

---

## Section 4 — Codex & Cursor Rules Gaps

| Rule                                                                    | Exists in Codex?                    | Exists in .mdc?                       | Gap                                                                        | Priority | Action                                                                                             |
| ----------------------------------------------------------------------- | ----------------------------------- | ------------------------------------- | -------------------------------------------------------------------------- | -------- | -------------------------------------------------------------------------------------------------- |
| Adapter-private `_<venue>_models.py` → UAC (no exceptions)              | Partial (usage patterns documented) | YES (unified-api-contracts-usage.mdc) | Migration governance not documented                                        | HIGH     | Update `contracts-integration.mdc` to state adapter-private models are not exempt                  |
| Service domain schemas → UIC `domain/<service>/` (not service-owned)    | NO — codex says OPPOSITE            | NO                                    | `schema-governance.md` and `schema-service-owned.mdc` CONTRADICT this rule | HIGH     | Retire `schema-service-owned.mdc`; update `schema-governance.md` §TL;DR and §Service-owned section |
| No schema outside UAC/UIC (except CORRECT-LOCAL + SchemaDefinition)     | NO                                  | NO                                    | No quality gate enforcement                                                | HIGH     | Add schema placement check to `quality-gates-service-template.sh`                                  |
| UIC may import from UAC; UAC must NOT import from UIC (even in tests)   | YES (TIER-ARCHITECTURE.md)          | NO .mdc                               | No rule enforcement for tests                                              | MEDIUM   | Add `imports/uic-may-import-uac.mdc` rule                                                          |
| UAC = T0 leaf; UIC = T0-with-UAC-dependency; build order UAC before UIC | YES (TIER-ARCHITECTURE.md)          | NO                                    | Build order not in manifest                                                | MEDIUM   | Update workspace-manifest.json L2 → L2a (UAC) + L2b (UIC)                                          |
| Normalization canonicals → UAC; messaging canonicals → UIC              | Implicit in chain.md                | NO                                    | No explicit rule distinguishing the two canonical categories               | MEDIUM   | Add to `contracts-scope-and-layout.md`                                                             |
| SchemaDefinition objects (infrastructure) stay in service               | YES (schema-governance.md)          | YES (schema-service-owned.mdc)        | Correct but mixes with data contract rules — needs clarification           | LOW      | Add explicit distinction in new schema-placement-master.mdc                                        |
| schema_registry.json must be kept current                               | NO                                  | NO                                    | No validation script                                                       | LOW      | Add registry validation to quality gate                                                            |
| Service domain schema access via UTL/UDC (not direct UIC import)        | NO                                  | NO                                    | UTL lacks schema access API                                                | LOW      | Document after UTL schema bridge is built                                                          |

---

## Section 5 — Tier Structure Assessment

### Current State (workspace-manifest.json L2)

```
L2: [unified-api-contracts, unified-internal-contracts, unified-cloud-interface,
     unified-events-interface, execution-algo-library, matching-engine-library,
     unified-reference-data-interface]  ← ALL grouped as T0 "pure leaves"
```

### Actual Dependency (confirmed)

```
unified-internal-contracts/unified_internal_contracts/market_data/__init__.py:3–9
imports from unified-api-contracts  ← UIC depends on UAC
```

### Required Change

```
L2a: [unified-api-contracts, unified-cloud-interface, unified-events-interface,
      execution-algo-library, matching-engine-library]   ← true T0 leaves
L2b: [unified-internal-contracts, unified-reference-data-interface]   ← T0-with-T0-dep
```

**Risk assessment:** Low — UIC already imports UAC in production. Formalizing the split makes the implicit explicit. No downstream repos need to change their tier classification. CI/CD build order is the only system that needs to be updated.

---

## Section 6 — Remediation Priority Order

### P0 — Blockers (must do before Phase 2 library tier hardening)

1. **Rename InstrumentRecord in UAC** → `InstrumentWarehouseRow` (or similar). Fix all UAC normalizers and GCS write callers. This removes the CONFLICT that blocks all other migrations.
2. **Retire `schema-service-owned.mdc`** → Create `imports/service-domain-schema-in-uic.mdc` with new rule.
3. **Update `schema-governance.md`** TL;DR and service-owned section.
4. **Create `unified_internal_contracts/domain/`** directory structure in UIC.
5. **Move test_ac_uic_alignment.py** from UAC to UIC tests (removes CIRCULAR violation).

### P1 — High Value Migrations

6. **Move InstrumentKey** from unified-domain-client → UIC `reference/instrument_key.py`. Update all importers.
7. **Move `_deribit_models.py`** (30+ models) from unified-market-interface → UAC `deribit/schemas.py`.
8. **Move `_defi_graph_models.py`** (21+ models) from unified-market-interface → new UAC `thegraph/schemas.py`.
9. **Resolve UAC/UIC DeFi/options canonicals** — decide ownership of CanonicalOraclePrice, CanonicalStakingRate, CanonicalOptionsChainEntry.
10. **Deduplicate ModelVariantConfig/ModelMetadata** — ml-interface imports from UIC instead of own copies.

### P2 — Service Domain Schema Migrations

11. **strategy-service**: Move 7 domain data schemas to `UIC/domain/strategy-service/`.
12. **execution-service**: Move 3 sports schemas to `UIC/domain/execution-service/`.
13. **market-data-processing-service**: Move 7 domain models to `UIC/domain/market-data-processing/`.
14. **market-data-api**: Move 1 schema to `UIC/domain/market-data-api/`.
15. **features-onchain-service**: Move 1 schema to UIC `features.py`.

### P0–P3 Status (2026-03-05)

All P0–P3 items **COMPLETED**. Backward-compat re-export stubs eliminated. Quality gates blocking. Schema SoC enforcement in place.

### P3 — Completed

16. ~~**features-sports-service**: Formalize 14 column lists as TypedDicts in UIC `sports.py`.~~ ✅ Done
17. ~~**Eliminate backward-compat re-export stubs**~~ ✅ Done:
    - **UAC**: `binance/schemas.py` stub — eliminated; consumers import from sub-modules (`account_schemas`, `market_schemas`, `order_schemas`, `ws_schemas`) directly.
    - **UAC**: `cloud_sdks/aws_schemas.py` — no stub found; already structured as individual sub-modules (`aws/s3.py`, `aws/sqs.py`, etc.).
    - **Migration stubs (interfaces)**: `unified-market-interface/adapters/_deribit_models.py`, `defi/_defi_graph_models.py` — deleted.
    - **Migration stubs (UDC)**: `unified-domain-client/schemas/instrument_key.py` — deleted.
    - **Service re-export stubs** (strategy-service, execution-service, market-data-processing, market-data-api, features-onchain) — stubs removed; consumers import from UIC `domain/` directly.
    - **Sports adapter stubs** (Matchbook, Smarkets, Betdaq, Pinnacle, OddsAPI, OneXBet in USEI) — deleted; consumers import from UAC.
    - **features-sports-service**: `schemas/output_schemas.py` TypedDict re-export section removed; only column lists remain.
    - **features-volatility-service**: `models.py` backward-compat aliases (`VolatilityFeatures`, `FuturesTermStructureFeatures`) removed; all consumers now import from UIC directly.
    - **Rule**: `cursor-rules/core/no-backward-compat-shims.mdc`. Quality gate STEP 5.8 is BLOCKING.
18. ~~**features-volatility-service**: Replace local VolatilityFeatures/FuturesTermStructureFeatures with UIC imports.~~ ✅ Done — aliases removed; calculators and tests import `OptionsIvRecord`/`FuturesTermStructureRecord` from UIC directly.
19. ~~**Update schema_registry.json** stale entries.~~ ✅ Done
20. ~~**Add schema placement quality gate checks** to all service/library templates.~~ ✅ Done (STEP 5.9)
21. ~~**Update workspace-manifest.json L2 → L2a/L2b** split.~~ ✅ Done
22. ~~**Sports adapter execution schemas**: Extend UAC sports venue schemas with execution-specific shapes.~~ ✅ Done (USEI adapter stubs deleted; UAC is already the canonical home for execution-specific shapes per adapter-models-belong-in-uac.mdc)
23. ~~**features-volatility-service reconciliation**: Resolve timestamp type and missing FuturesTermStructure fields.~~ ✅ Done — UIC `FuturesTermStructureRecord` already uses `datetime`; service calculators use `datetime` consistently. Timestamp conversion note captured in models.py docstring.

---

## Appendix: Repository Clean/Violated Summary

### Clean Repos (zero violations)

- unified-events-interface, unified-cloud-interface, execution-algo-library, matching-engine-library (T0 libs)
- unified-reference-data-interface, unified-config-interface, unified-trading-library (T1 libs)
- unified-trade-execution-interface, unified-feature-calculator-library, unified-position-interface, unified-defi-execution-interface (T2 libs)
- strategy-validation-service, risk-and-exposure-service, alerting-service
- features-delta-one-service, features-cross-instrument-service, features-multi-timeframe-service
- ml-inference-service, ml-training-service, pnl-attribution-service, position-balance-monitor-service
- execution-results-api, client-reporting-api, deployment-api, deployment-service
- market-tick-data-service, instruments-service, features-calendar-service _(SchemaDefinition only — infrastructure, not violations)_

### Previously Violated Repos — All Remediated ✅

- unified-api-contracts: InstrumentRecord renamed `InstrumentWarehouseRow`; CIRCULAR test moved to UIC tests ✅
- unified-internal-contracts: domain/ dir created; stale registry updated; DeFi/options duplicates resolved ✅
- unified-market-interface: \_deribit_models.py + \_defi_graph_models.py stubs deleted ✅
- unified-sports-execution-interface: all 6 adapter stubs deleted; consumers import from UAC ✅
- unified-ml-interface: ModelVariantConfig/ModelMetadata import from UIC ✅
- unified-domain-client: InstrumentKey moved to UIC; stub deleted ✅
- execution-service: sports models moved to UIC domain/execution_service/sports.py ✅
- strategy-service: domain_data.py + order.py moved to UIC domain/strategy_service/ ✅
- market-data-processing-service: domain models moved to UIC domain/market_data_processing/ ✅
- market-data-api: OrderBookSnapshot moved to UIC domain/market_data_api/ ✅
- features-onchain-service: OnchainFeature moved to UIC as OnchainFeatureRecord ✅
- features-sports-service: 14 column lists formalized as TypedDicts in UIC sports.py ✅
- features-volatility-service: backward-compat aliases removed; imports from UIC directly ✅
