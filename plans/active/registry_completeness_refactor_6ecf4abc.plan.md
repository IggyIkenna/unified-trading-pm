---
name: Registry Completeness Refactor
overview:
  Two-stage plan to complete the UAC venue/instrument registry, eliminate DRY violations between UAC/UCI/UIC, add
  missing instrument types and sports market granularity, adopt the registry across all consumers, and add integration
  tests. Stage 1 is purely additive (non-breaking). Stage 2 tears down duplicates and redirects consumers.
todos:
  - id: s1-tradfi-types
    content:
      "Stage 1.1+1.2: Add BOND, EQUITY, ETF, COMMODITY, CURRENCY to UAC InstrumentType; fix Databento and IBKR
      normalizer mappings"
    status: pending
  - id: s1-sports-markets
    content:
      "Stage 1.3+1.5: Add missing OddsType values (HALF_TIME_RESULT, CORNERS, CARDS, PLAYER_PROPS, etc.); add BetSide
      enum and CommissionModel enum"
    status: pending
  - id: s1-venue-coverage
    content:
      "Stage 1.4+1.6+1.7: Add sports venues to INSTRUMENT_TYPES_BY_VENUE; add supported_market_types per venue; add
      betdaq/smarkets/matchbook/manifold/onexbet to venue_manifest"
    status: pending
  - id: s1-vcr-cassettes
    content: "Stage 1.8: Record 4 pending VCR cassettes (polymarket x3, coinbase x1)"
    status: pending
  - id: s1-integration-tests
    content: "Stage 1.10: Add integration tests validating registry covers all consumer expectations"
    status: pending
  - id: s2-enum-consolidation
    content:
      "Stage 2.6+2.7: Consolidate Venue/InstrumentType enums (UAC owns, UCI re-exports); remove _VENUE_TO_TARDIS from
      UIC"
    status: pending
  - id: s2-exec-service-adopt
    content: "Stage 2.1: execution-service replaces local CLOB_VENUES/DEX_VENUES/ZERO_ALPHA_VENUES with UAC imports"
    status: pending
  - id: s2-consumer-adoption
    content: "Stage 2.2-2.5: instruments-service, market-data-api, UMI, UTEI adopt UAC registry"
    status: pending
  - id: s2-sports-normalize-fix
    content: "Stage 2.8: Fix normalize_sports_order hardcoded back; use BetSide enum and venue category"
    status: pending
  - id: s2-provider-cleanup
    content: "Stage 2.10: Audit 53 yellow providers; verify/mark green or remove dormant ones"
    status: pending
isProject: false
---

# UAC Registry Completeness and Consumer Adoption Refactor

## Current State Summary

The registry in `unified-api-contracts` is comprehensive (79 provider dirs, 240+ endpoint mappings, 72 providers in
YAML, 81 VCR cassettes) but has three systemic problems:

- **Zero consumer repos import from `unified_api_contracts.registry`** -- every consumer (execution-service,
  instruments-service, market-data-api, UMI, UTEI, MEL) bypasses the registry and either hardcodes venue data or uses
  UCI's overlapping definitions
- **DRY violations** -- venue sets (`CLOB_VENUES`, `DEX_VENUES`, `ZERO_ALPHA_VENUES`) duplicated in execution-service;
  `Venue` enum and `VenueMapping` in UCI overlaps with UAC `venue_constants.py` and `venue_manifest/`;
  `_VENUE_TO_TARDIS` in UIC duplicates UCI's `tardis_to_venue`
- **Incomplete coverage** -- missing TradFi instrument types (bonds, FX, equity, ETF, commodity), sports market types
  (half_time, corners, cards, player_props), no sports broker/aggregator pattern, 53 yellow providers

## Separation of Concerns (Decision Framework)

Per codex `02-data/contracts-scope-and-layout.md`:

- **UAC** owns: external API schemas, canonical normalized types, venue manifest, venue constants for normalization,
  endpoint-to-schema mapping, VCR cassettes, capability declarations
- **UIC** owns: internal service-to-service contracts, `InstrumentDefinition` (GCS/parquet record), `InstrumentKey`
  (canonical ID format)
- **UCI** owns: config loading (`BaseConfig`, `ConfigStore`), runtime config schemas -- but currently also holds `Venue`
  enum, `InstrumentType` enum, and `VenueMapping` which codex says belong in UAC for normalization

**Decision**: Venue definitions, instrument type definitions, and venue-to-provider mappings are normalization concerns
and belong in UAC. UCI should re-export from UAC for config consumers. UIC's `InstrumentKey._VENUE_TO_TARDIS` should
delegate to UAC/UCI's mapping.

---

## Stage 1: Non-Breaking Additions (Add New Paths, No Removals)

### 1.1 Add Missing TradFi Instrument Types to UAC

**Files:**

- [unified-api-contracts/unified_api_contracts/canonical/domain/reference/**init**.py](unified-api-contracts/unified_api_contracts/canonical/domain/reference/__init__.py)
- [unified-api-contracts/unified_api_contracts/registry/venue_constants.py](unified-api-contracts/unified_api_contracts/registry/venue_constants.py)

Add to UAC's canonical `InstrumentType`:

- `BOND` -- IBKR (`BOND` secType), Databento (`B` instrument_class)
- `EQUITY` -- IBKR (`STK`), Databento (`E`); already in UCI but not UAC
- `ETF` -- IBKR (`FUND`), Databento (`N`); already in UCI but not UAC
- `COMMODITY` -- IBKR (`CMDTY`); already in UCI but not UAC
- `CURRENCY` / `FX_SPOT` -- IBKR (`CASH`), Databento (`S`); UCI has `CURRENCY` and `Venue.FX`
- `CDS` -- OFR data exists as `CanonicalCdsSpread`; add as instrument type for pricing (not trading)
- `WARRANT` -- IBKR (`WAR`); optional, can keep mapping to OPTION

Add to `INSTRUMENT_TYPES_BY_VENUE` for TradFi venues (NASDAQ, NYSE, CME, IBKR, etc.).

### 1.2 Fix Databento and IBKR Normalizer Mappings

**Files:**

- [unified-api-contracts/unified_api_contracts/external/databento/normalize.py](unified-api-contracts/unified_api_contracts/external/databento/normalize.py)
  -- extend `_instrument_class_to_type`: B->BOND, E->EQUITY, N->ETF, X->INDEX, C->SPOT_PAIR (currently all fall through
  to SPOT_PAIR default)
- [unified-api-contracts/unified_api_contracts/external/ibkr/normalize.py](unified-api-contracts/unified_api_contracts/external/ibkr/normalize.py)
  -- fix: BOND->BOND (not SPOT), IND->INDEX (not SPOT), CMDTY->COMMODITY (not SPOT), add FOP->OPTION

### 1.3 Add Missing Sports Market Types to OddsType

**File:**
[unified-api-contracts/unified_api_contracts/canonical/domain/sports/odds.py](unified-api-contracts/unified_api_contracts/canonical/domain/sports/odds.py)

Current OddsType has 6 values: `H2H`, `OVER_UNDER`, `ASIAN_HANDICAP`, `BOTH_TEAMS_SCORE`, `CORRECT_SCORE`, `OUTRIGHT`.

Add:

- `HALF_TIME_RESULT` -- half-time winner
- `FIRST_HALF_OVER_UNDER` -- first half totals
- `CORNERS` -- corner count markets
- `CARDS` -- booking markets
- `PLAYER_PROPS` -- anytime scorer, shots on target, etc.
- `DRAW_NO_BET` -- common line
- `DOUBLE_CHANCE` -- common line
- `GOAL_SCORER` -- first/last/anytime scorer markets

### 1.4 Add Sports Market Coverage Per Venue

**File:**
[unified-api-contracts/unified_api_contracts/canonical/domain/sports/venue_execution_registry.py](unified-api-contracts/unified_api_contracts/canonical/domain/sports/venue_execution_registry.py)

Add `supported_market_types: list[OddsType]` to `VenueExecutionProfile` (or a new mapping). Document per venue:

| Venue       | Back | Lay | H2H | Over/Under | Asian Handicap | Correct Score | Player Props | Corners/Cards |
| ----------- | ---- | --- | --- | ---------- | -------------- | ------------- | ------------ | ------------- |
| Betfair     | Y    | Y   | Y   | Y          | Y              | Y             | Y (limited)  | Y             |
| Smarkets    | Y    | Y   | Y   | Y          | Y              | Y             | N            | N             |
| Matchbook   | Y    | Y   | Y   | Y          | Y              | N             | N            | N             |
| Betdaq      | Y    | Y   | Y   | Y          | Y              | Y             | N            | N             |
| Pinnacle    | Y    | N   | Y   | Y          | Y              | Y             | Y            | Y             |
| Paddy Power | Y    | N   | Y   | Y          | Y              | Y             | Y            | Y             |
| Bet365      | Y    | N   | Y   | Y          | Y              | Y             | Y            | Y             |

(scraped venues -- market type support depends on scraper implementation)

### 1.5 Add BetSide Enum and Commission Schema

**File:**
[unified-api-contracts/unified_api_contracts/canonical/domain/sports/**init**.py](unified-api-contracts/unified_api_contracts/canonical/domain/sports/__init__.py)

- Add `BetSide` enum: `BACK`, `LAY` (replace `is_back: bool` on `CanonicalOdds` and `side: str` on `CanonicalBetOrder`)
- Add `CommissionModel` enum: `NET_WINNINGS_PCT`, `BUILT_INTO_ODDS`, `NOTIONAL_PCT`, `FLAT_FEE` (formalize what
  `venue_execution_registry.py` already uses as strings)
- Fix `normalize_sports_order` in
  [unified-api-contracts/unified_api_contracts/normalize_utils/sports.py](unified-api-contracts/unified_api_contracts/normalize_utils/sports.py)
  which hardcodes `side="back"` -- should derive from venue category (EXCHANGE -> configurable, BOOKMAKER -> always
  BACK)

### 1.6 Add Sports Venues to INSTRUMENT_TYPES_BY_VENUE

**File:**
[unified-api-contracts/unified_api_contracts/registry/venue_constants.py](unified-api-contracts/unified_api_contracts/registry/venue_constants.py)

Sports venues (BETFAIR, KALSHI, POLYMARKET, PINNACLE, SMARKETS, MATCHBOOK, BETDAQ) are currently missing from
`INSTRUMENT_TYPES_BY_VENUE`. Add them with their supported instrument types (FIXED_ODDS, EXCHANGE_ODDS, etc.).

### 1.7 Add Missing Venues to venue_manifest

**File:**
[unified-api-contracts/unified_api_contracts/registry/venue_manifest/betting_sports.py](unified-api-contracts/unified_api_contracts/registry/venue_manifest/betting_sports.py)

Green providers not in manifest: betdaq, smarkets, matchbook, manifold, onexbet. Add `VenueContract` entries for each.

### 1.8 Record Pending VCR Cassettes

4 endpoints are PENDING (public, no auth needed):

- polymarket gamma events, gamma tags, prices-history
- coinbase products

Record cassettes and update `_endpoint_registry_data.py` status to RECORDED.

### 1.9 Sports Broker/Aggregator Assessment

**Finding:** No cross-bookmaker position aggregation or sports prime broker exists in the system. Versifi is
crypto-only.

**Potential aggregators to evaluate (external services):**

- **BetConnect** -- allows backing bookmaker prices via an exchange model; acts as aggregator
- **OddsMatrix** -- multi-bookmaker API aggregation platform
- **Betfair Exchange** -- de facto aggregation point (can lay bookmaker positions)
- **Pinnacle** -- sharp bookmaker, no aggregation but best available odds for hedging

**Recommendation:** Add a `SportsAggregatorType` concept to UAC registry, classifying venues as:

- `DIRECT_EXECUTION` -- direct bookmaker/exchange API
- `ODDS_AGGREGATOR` -- read-only odds (Odds API, OpticOdds, OddsJam)
- `EXECUTION_AGGREGATOR` -- routes orders across venues (none currently, BetConnect potential)
- `POSITION_AGGREGATOR` -- cross-venue position view (none currently)

For the existing system, position aggregation should be built into `position-balance-monitor-service` using per-venue
balance/position endpoints (Betfair AccountFunds, Smarkets balance, Matchbook balance, Betdaq balance -- schemas exist
in UAC for all four).

### 1.10 Add Integration Tests for Registry Usage

For each consumer that will adopt UAC registry in Stage 2, add integration tests now that validate:

- `INSTRUMENT_TYPES_BY_VENUE` covers all venues the consumer uses
- `CLOB_VENUES`/`DEX_VENUES`/`ZERO_ALPHA_VENUES` in UAC match current consumer expectations
- `VENUE_MANIFEST` has entries for all venues the consumer calls
- `ENDPOINT_SCHEMA_MAP` covers all endpoints the consumer uses

**Test locations:**

- `unified-api-contracts/tests/integration/test_registry_consumer_contracts.py` (new)
- `execution-service/tests/integration/test_uac_registry_alignment.py` (new)
- `instruments-service/tests/integration/test_uac_registry_alignment.py` (new)

---

## Stage 2: Breaking Teardown (Remove Duplicates, Redirect Consumers)

### 2.1 execution-service: Replace Local Venue Sets with UAC Imports

**File:**
[execution-service/execution_service/utils/instruction_type.py](execution-service/execution_service/utils/instruction_type.py)
(lines 47-111)

- Delete local `CLOB_VENUES`, `DEX_VENUES`, `ZERO_ALPHA_VENUES` definitions
- Import from `unified_api_contracts.registry.venue_constants`
- Update all internal references in `instruction_type.py`, `domain.py`, `_venue_book_types.py`

**File:**
[execution-service/execution_service/instruments/registry.py](execution-service/execution_service/instruments/registry.py)

- Evaluate `VENUES_CONFIG` (GCS codes, nautilus codes) -- if these are execution-service-specific config (deployment
  paths), keep them local. If they describe venue attributes, move to UAC.

### 2.2 instruments-service: Adopt INSTRUMENT_TYPES_BY_VENUE

**Files in instruments-service:**

- Use `INSTRUMENT_TYPES_BY_VENUE` from UAC to determine what instrument types to query per venue
- Use UAC `VENUE_MANIFEST` for venue connectivity info (REST/WS/FIX)
- Replace implicit venue-to-instrument-type logic in adapters with explicit UAC lookups

### 2.3 market-data-api: Add Venue Validation

- Add `unified-api-contracts` as dependency
- Validate venue names in API routes against UAC venue constants
- Use `ENDPOINT_SCHEMA_MAP` for endpoint validation

### 2.4 UMI: Adopt VENUE_MANIFEST

**File:**
[unified-market-interface/unified_market_interface/sports/registry.py](unified-market-interface/unified_market_interface/sports/registry.py)

- Replace hardcoded `_ADAPTER_PATHS` with registry-driven lookup using UAC `VENUE_MANIFEST` or `BOOKMAKER_REGISTRY`

### 2.5 UTEI: Add Venue Validation

- Use UAC venue constants for venue name validation in WebSocket feeds and adapter factories

### 2.6 Consolidate Venue/InstrumentType Enums (UCI -> UAC)

This is the most significant architectural change. Per codex, venue enums for normalization belong in UAC.

**Option A (recommended): UAC owns, UCI re-exports**

- Move `Venue` enum and `InstrumentType` enum canonical definitions to UAC
- UCI imports and re-exports from UAC (no consumer code changes needed except import path)
- `VenueMapping` stays in UCI as it's config/orchestration, but delegates venue validation to UAC

**Option B: Keep split, add alignment test**

- Keep UCI enums as-is, add a CI test that asserts UCI.Venue values == UAC venue_constants values
- Less disruptive but maintains two sources of truth

Decision point: Option A is cleaner long-term but requires UAC to not depend on UCI (which it currently doesn't --
safe). Option B is faster.

### 2.7 Consolidate VENUE_TO_TARDIS

**File:**
[unified-internal-contracts/unified_internal_contracts/reference/instrument_key.py](unified-internal-contracts/unified_internal_contracts/reference/instrument_key.py)

- Remove `_VENUE_TO_TARDIS` dict from UIC
- Import from UCI's `VenueMapping.venue_to_tardis` (reverse of `tardis_to_venue`)
- Or: delegate to UAC if venue mappings move there in 2.6

### 2.8 Fix normalize_sports_order Hardcoded Back

**File:**
[unified-api-contracts/unified_api_contracts/normalize_utils/sports.py](unified-api-contracts/unified_api_contracts/normalize_utils/sports.py)

- Use new `BetSide` enum instead of hardcoded `side="back"`
- Derive side from venue category: `SportsVenueType.EXCHANGE_API` -> side from order, `BOOKMAKER_API` -> always BACK

### 2.9 Populate URDI / Sports Reference Interface

`unified-sports-reference-interface` declares "canonical sports reference data types" but has zero schemas -- everything
lives in UAC `canonical/domain/sports/`. Either:

- Re-export UAC sports canonical types from USRI (if separation is desired for downstream consumers)
- Or acknowledge USRI is an adapter layer only (like URDI) and the schemas correctly live in UAC

### 2.10 Provider API Versions Cleanup

53 of 72 providers are yellow in `provider_api_versions.yaml`. For each:

- If schemas exist and cassettes exist -> verify and mark green
- If schemas exist but no cassette -> mark as pending cassette
- If no schemas -> evaluate whether provider is actually used; if not, remove or mark dormant

---

## Rollout Order (Dependency-Safe)

```
Stage 1 (all non-breaking, can be parallelized):
  1.1 + 1.2  TradFi instrument types + normalizer fixes (UAC only)
  1.3 + 1.5  Sports market types + BetSide enum (UAC only)
  1.4 + 1.6  Sports venue coverage in registry (UAC only)
  1.7        Missing venues in manifest (UAC only)
  1.8        VCR cassette recording (UAC only)
  1.9        Sports aggregator assessment (design doc only)
  1.10       Integration tests (UAC + consumers)

Stage 2 (sequential, each step verified before next):
  2.6        Consolidate enums (UAC + UCI) -- foundational
  2.7        Consolidate _VENUE_TO_TARDIS (UIC) -- depends on 2.6
  2.1        execution-service adopts UAC registry -- depends on 2.6
  2.2        instruments-service adopts UAC registry
  2.3        market-data-api adds validation
  2.4        UMI adopts VENUE_MANIFEST
  2.5        UTEI adds validation
  2.8        Fix normalize_sports_order
  2.9        USRI scope clarification
  2.10       Provider cleanup
```

## Repos Touched

| Repo                              | Stage | Changes                                                                      |
| --------------------------------- | ----- | ---------------------------------------------------------------------------- |
| unified-api-contracts             | 1 + 2 | Instrument types, market types, venue manifest, normalizers, registry, enums |
| unified-config-interface          | 2     | Re-export from UAC (or alignment test)                                       |
| unified-internal-contracts        | 2     | Remove VENUE_TO_TARDIS, delegate to UCI/UAC                                  |
| execution-service                 | 2     | Delete local venue sets, import from UAC                                     |
| instruments-service               | 2     | Adopt INSTRUMENT_TYPES_BY_VENUE                                              |
| market-data-api                   | 2     | Add UAC dependency, venue validation                                         |
| unified-market-interface          | 2     | Replace hardcoded ADAPTER_PATHS                                              |
| unified-trade-execution-interface | 2     | Add venue validation                                                         |
| position-balance-monitor-service  | 1     | Sports aggregator pattern (if pursued)                                       |
