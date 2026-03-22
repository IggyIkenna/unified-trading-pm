# Session 6: Instrument Registry & Representative Sample

## Services & Repos Affected
> **DO NOT work on these repos in other sessions — they are owned by this session.**

| Repo | What Changes | Risk |
|------|-------------|------|
| unified-api-contracts | Add REPRESENTATIVE_INSTRUMENT_SAMPLE registry, enhance generate_ui_reference_data.py with 9 missing registries | MED |
| unified-internal-contracts | Update InstrumentGenerator to read from UAC registry instead of hardcoded lists | MED |
| instruments-service | Update mock_data_provider to use new registry-driven generator | LOW |
| system-integration-tests | Update alignment tests for new registry structure | LOW |

## Plans Covered
| Plan | Phases | Todos | Reference |
|------|--------|-------|-----------|
| Plan A | Phase 1 (registry generation script) | ~4 todos | plans/active/plan_a_registry_schema_sync_2026_03_21.plan.md |
| Plan A | Phase 2 (OpenAPI spec fixes) | ~4 todos | plans/active/plan_a_registry_schema_sync_2026_03_21.plan.md |
| Plan A | Phase 3 (CI triggers) | ~4 todos | plans/active/plan_a_registry_schema_sync_2026_03_21.plan.md |
| Plan D | Scenario instrument injection | related | plans/active/plan_d_testnet_stress_testing_2026_03_21.plan.md |

## What's Already Done (Don't Redo)
- Plan A Phase 0 DONE: aave_plasma bug fixed, 18 venue maps added, classify_venue_error wired into execution-service
- InstrumentGenerator exists in UIC with real venue rules (Deribit expiry, CME codes, Aave wrapped tokens)
- InstrumentDefinition schema in UIC is the SSOT
- CanonicalInstrument in UAC is the external-facing schema
- Conversion (CanonicalInstrument → InstrumentDefinition) works with sanitization (None→"", datetime→ISO, float→str)
- 70 SIT tests including 43 alignment tests between generator/URDI/instruments-service
- instruments-service mock mode verified: 52 instruments, 14 types, 20+ venues

## The Architecture (3 Layers)

```
Layer 1: Representative default sample
  └── REPRESENTATIVE_INSTRUMENT_SAMPLE in UAC registry
  └── Deterministic, always the same, covers all venues/types
  └── "The instruments that have been around forever and will continue to be"

Layer 2: Scenario overrides (ScenarioConfig)
  └── BAD_SCHEMA → inject malformed instruments
  └── FLASH_CRASH → expire options mid-session
  └── DELISTED → instruments with available_to in the past
  └── NEW_LISTING → instruments with available_from = now

Layer 3: User ad-hoc (runtime via API)
  └── Create fake symbol with custom expiry, strike, venue
  └── Delete/delist instrument mid-session
  └── Test how system handles unknown venues, bad schemas
```

## Part 1: Move Representative Sample to UAC

### Step 1: Create REPRESENTATIVE_INSTRUMENT_SAMPLE in UAC

File: `unified-api-contracts/unified_api_contracts/registry/representative_sample.py`

```python
"""Representative instrument sample — SSOT for mock/test instrument selection.

This registry defines WHICH specific instruments are generated in mock mode.
The InstrumentGenerator reads this instead of hardcoding its own lists.
Updating the sample is a registry change, not a generator code change.

The sample is designed to be:
- Strategic: covers every venue × instrument_type combination in VENUE_CATEGORY_MAP
- Representative: uses instruments that exist in production and are unlikely to be delisted
- Minimal: one instrument per venue×type where possible, full options chain for BTC on Deribit
- Extensible: scenarios can ADD instruments on top (Layer 2), users can create ad-hoc (Layer 3)
"""

# CeFi base assets — the coins that exist on every CeFi venue
CEFI_BASE_ASSETS: list[str] = ["BTC", "ETH", "SOL"]

# TradFi equity symbols per venue
# Format: (symbol, asset_class) — asset_class is one of: equity, etf, index
TRADFI_EQUITIES: dict[str, list[tuple[str, str]]] = {
    "NASDAQ": [("AAPL", "equity"), ("QQQ", "etf")],
    "NYSE": [("GLD", "etf"), ("IBIT", "etf")],
    "CBOE": [("VIX", "index")],
}

# TradFi futures specs per venue
# Format: (root_symbol, base_asset, contract_size, tick_size)
TRADFI_FUTURES: dict[str, list[tuple[str, str, float, float]]] = {
    "CME": [("ES", "USD", 50.0, 0.25), ("NQ", "USD", 20.0, 0.25)],
    "ICE": [("ZB", "USD", 1000.0, 1/32), ("ZN", "USD", 1000.0, 1/64)],
}

# DeFi tokens per venue
# Format: (symbol, underlying, instrument_type, extra_params)
DEFI_INSTRUMENTS: dict[str, list[dict[str, object]]] = {
    "AAVE_V3_ETH": [
        {"symbol": "aUSDC", "underlying": "USDC", "type": "A_TOKEN", "ltv": 0.825},
        {"symbol": "aUSDT", "underlying": "USDT", "type": "A_TOKEN", "ltv": 0.75},
        {"symbol": "aWETH", "underlying": "WETH", "type": "A_TOKEN", "ltv": 0.825},
        {"symbol": "variableDebtUSDC", "underlying": "USDC", "type": "DEBT_TOKEN"},
        {"symbol": "variableDebtUSDT", "underlying": "USDT", "type": "DEBT_TOKEN"},
        {"symbol": "variableDebtWETH", "underlying": "WETH", "type": "DEBT_TOKEN"},
    ],
    "COMPOUND_V3_ETH": [
        {"symbol": "cUSDCv3", "underlying": "USDC", "type": "POOL"},
    ],
    "UNISWAPV3-ETH": [
        {"symbol": "USDT-ETH-0.3%", "underlying": "ETH", "type": "POOL", "fee_tier": 3000},
        {"symbol": "USDC-ETH-0.05%", "underlying": "ETH", "type": "POOL", "fee_tier": 500},
    ],
    # ... etc for all DeFi venues
    "LIDO": [
        {"symbol": "stETH", "underlying": "ETH", "type": "LST"},
        {"symbol": "wstETH", "underlying": "ETH", "type": "LST"},
    ],
    "ETHERFI": [
        {"symbol": "eETH", "underlying": "ETH", "type": "LST"},
        {"symbol": "weETH", "underlying": "ETH", "type": "LST"},
    ],
}

# Sports leagues for mock generation
SPORTS_LEAGUES: list[str] = ["premier_league", "nba", "la_liga", "nfl"]

# Options chain config
OPTIONS_CHAIN_CONFIG = {
    "underlying": "BTC",
    "venue": "DERIBIT",
    "strike_interval_usd": 500,
    "atm_price_usd": 60000,
    "strike_range_pct": 0.30,  # ±30% from ATM
    "weekly_expiries": 4,
    "monthly_expiries": 3,
    "quarterly_expiries": 3,
}
```

Export from UAC `__init__.py` and `registry/__init__.py`.

### Step 2: Update InstrumentGenerator to read from registry

In `unified-internal-contracts/unified_internal_contracts/testing/instrument_generator.py`:

Replace:
```python
_CEFI_BASE_ASSETS: list[str] = ["BTC", "ETH", "SOL"]
```

With:
```python
from unified_api_contracts.registry.representative_sample import (
    CEFI_BASE_ASSETS,
    TRADFI_EQUITIES,
    TRADFI_FUTURES,
    DEFI_INSTRUMENTS,
    SPORTS_LEAGUES,
    OPTIONS_CHAIN_CONFIG,
)
```

Remove all hardcoded `_CEFI_BASE_ASSETS`, `_TRADFI_EQUITY_SYMBOLS`, `_TRADFI_FUTURES_SPECS` from the generator. Replace with reads from the imported registry.

### Step 3: Add scenario instrument injection (Layer 2)

In `ScenarioConfig` (UIC testing/scenarios/seed_spec.yaml), add instrument override sections:

```yaml
scenarios:
  normal:
    instrument_overrides: []  # use default sample
  bad_schema:
    instrument_overrides:
      - action: inject
        instrument_key: "UNKNOWN:SPOT:FAKE-USD"
        missing_fields: [base_asset, quote_asset]  # deliberately malformed
  flash_crash:
    instrument_overrides:
      - action: expire
        pattern: "DERIBIT:OPTION:BTC-*"  # expire all BTC options mid-session
        available_to: "now"
  delisted:
    instrument_overrides:
      - action: inject
        instrument_key: "BINANCE-SPOT:SPOT_PAIR:LUNA-USDT"
        available_to: "2022-05-09T00:00:00Z"  # Terra collapse
  new_listing:
    instrument_overrides:
      - action: inject
        instrument_key: "BINANCE-SPOT:SPOT_PAIR:NEWCOIN-USDT"
        available_from: "now"
```

The InstrumentGenerator reads `ScenarioConfig.instrument_overrides` and applies them after generating the default sample.

### Step 4: Add ad-hoc instrument API endpoint (Layer 3)

In unified-trading-api, add:
```
POST /api/instruments/mock/create — create a test instrument at runtime
DELETE /api/instruments/mock/{key} — remove/delist a test instrument
POST /api/instruments/mock/expire/{key} — set available_to=now
```

These mutate MockStateStore and are only available when `is_mock_mode()`. In real mode, they return 403.

## Part 2: Enhance Registry Generation Script (9 Missing Registries)

File: `unified-trading-pm/scripts/openapi/generate_ui_reference_data.py`

### What to add (0/9 currently extracted):

1. **venue_error_classifications** — serialize `VENUE_ERROR_MAP` from `canonical/crosscutting/errors/__init__.py`
2. **instruction_constraints** — serialize `INSTRUCTION_CONSTRAINTS` from `registry/instruction_constraints.py`
3. **defi_protocol_registry** — serialize `DEFI_VENUE_TO_PROTOCOL` and `DEFI_PROTOCOLS` from `registry/defi_protocol_registry.py`
4. **venue_rate_limits** — serialize `VENUE_RATE_LIMITS` from `registry/venue_rate_limits.py`
5. **risk_type_categories** — serialize `RISK_TYPE_CATEGORIES` from `canonical/crosscutting/risk_taxonomy.py`
6. **market_data_categories** — serialize `DATA_TYPES_BY_CATEGORY`, `VENUES_BY_CATEGORY`, `TIMEFRAMES` from `registry/market_data_categories.py`
7. **chain_rpc_templates** — serialize `CHAIN_RPC_TEMPLATES` from `registry/capability_declarations/_defi.py`
8. **subgraph_ids** — serialize `SUBGRAPH_IDS` from `registry/capability_declarations/_defi.py`
9. **representative_instrument_sample** — serialize the new `REPRESENTATIVE_INSTRUMENT_SAMPLE` registry

For each: import the Python symbol, serialize to JSON-safe dict (convert frozensets→lists, enums→str, Decimal→str, dataclasses→dict). Add to the output JSON under a new top-level key.

Test: verify the output JSON has all 9 new sections with >0 entries each.

### Step: Fix OpenAPI spec gaps

1. Add execution-results-api (50 endpoints) to the spec generation script
2. Fix 66 empty schemas — introspect FastAPI apps to get actual response models
3. Add unified-trading-api and auth-api to the spec

## Part 3: CI Triggers

Add GitHub Actions workflow triggers:
- When UAC is committed → run generate_ui_reference_data.py → commit updated JSON → PR on unified-trading-system-ui
- When UIC is committed → same flow for UIC enum changes
- This keeps the UI's registry copy always in sync with the Python source

## Key Rules
- uv pip install not pip install
- Never run pytest directly — use bash scripts/quality-gates.sh
- Do NOT run quickmerge — only git add + git commit
- basedpyright not pyright (with run_timeout 120)
- UAC import rules: consumers import from domain facades only, not canonical.* or normalize_utils.*
- REPRESENTATIVE_INSTRUMENT_SAMPLE is registry data — lives in UAC registry/, not in the generator

## Success Criteria
- [ ] REPRESENTATIVE_INSTRUMENT_SAMPLE lives in UAC registry (not hardcoded in generator)
- [ ] InstrumentGenerator reads from UAC registry, has ZERO hardcoded instrument lists
- [ ] ScenarioConfig supports instrument_overrides (inject, expire, delist)
- [ ] Ad-hoc instrument API works in mock mode
- [ ] generate_ui_reference_data.py extracts all 9 missing registries
- [ ] execution-results-api in OpenAPI spec
- [ ] 66 empty schemas filled
- [ ] CI triggers: UAC commit → UI registry update PR
- [ ] All affected repos pass quality-gates.sh
- [ ] Alignment tests updated and passing
