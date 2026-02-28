---
name: Schema Contract Validation Coverage
overview: "Close the gap between defined contracts and validated usage: add VCR cassettes for all public/no-auth venues, mark auth-required endpoints BLACKLISTED_UNVALIDATED, wire 22 missing adapters, fix bare excepts with EnhancedError, and complete execution-results-api contract adoption."
todos:
  - id: v2-vcr-public-venues
    content: "Batch 1A: VCR cassettes + replay tests for 8 public/no-auth venues: kalshi, polymarket, thegraph, defillama, barchart, open_meteo, upbit, fear_greed"
    status: pending
  - id: v2-endpoint-registry-unvalidated
    content: "Batch 1B: Add BLACKLISTED_UNVALIDATED status to endpoint_registry.py; mark all 22 auth-required venues with reason=auth_required_no_cassette"
    status: pending
  - id: v2-urdi-parse-raw-and-umi-stubs
    content: "Batch 1C: Add abstract _parse_raw to URDI base_adapter; implement 12 NotImplementedError stubs in UMI (coinbase, databento, tardis, aster normalizers)"
    status: pending
  - id: v2-execution-results-api
    content: "Batch 1D: Full UIC adoption for execution-results-api — EnhancedError on all exception handlers, lifecycle log_events, typed Pydantic response models"
    status: pending
  - id: v2-new-adapters-public
    content: "Batch 2E: New UMI adapters group 1 — kalshi, polymarket, defillama, fear_greed (public/no-auth, VCR testable)"
    status: pending
  - id: v2-new-adapters-cefi-sports
    content: "Batch 2F: New UMI adapters group 2 — aster, upbit, odds_api, pinnacle, glassnode, arkham (auth-required, BLACKLISTED_UNVALIDATED)"
    status: pending
  - id: v2-new-adapters-tradfi-altdata
    content: "Batch 2G: New UMI adapters group 3 — ibkr, fred, ecb, ofr, openbb, yahoo_finance, api_football, footystats, soccer_football, mev; delete empty defi/schemas.py; blacklist github"
    status: pending
  - id: v2-enhanced-error-high-priority
    content: "Batch 2H: Replace 311 bare excepts with EnhancedError in execution-service (201), instruments-service (62), market-tick-data-handler (48)"
    status: pending
  - id: v2-enhanced-error-remaining
    content: "Batch 3I: EnhancedError rollout for features-delta-one (20), features-onchain (13), features-volatility (12); remove unified-position-interface from .cursorignore"
    status: pending
  - id: v2-quality-gates
    content: "Batch 3J: Run quality gates on api-contracts, unified-market-interface, unified-reference-data-interface to verify all new VCR tests and adapters pass"
    status: pending
isProject: false
---

# Schema Contract Validation Coverage

## Current State (from audit)

- VCR coverage: 23% (11/48 venues) — 37 venues have schemas, zero cassettes
- 23 venue schemas have no UMI adapter consuming them
- `execution-results-api`: zero UIC imports, zero log_events, zero EnhancedError
- `execution-service`: 201 bare excepts, 108 `dict[str,Any]`, 0 EnhancedError
- `market-tick-data-handler`: 48 bare excepts, 0 EnhancedError
- 12 `NotImplementedError` stubs in UMI adapters
- URDI has no abstract `_parse_raw()` — all 10 adapters bypass contract validation at ingest
- `unified-position-interface` is in `.cursorignore` — invisible to quality gates

## Architecture

```mermaid
flowchart LR
    subgraph external [External API Contracts]
        VCR["VCR cassettes\n11/48 venues"]
        UNVALIDATED["BLACKLISTED_UNVALIDATED\nauth-required, no cassette"]
    end
    subgraph interfaces [Interface Layer]
        UMI["unified-market-interface\n22 adapters missing"]
        URDI["unified-reference-data-interface\nno _parse_raw base"]
        UPI["unified-position-interface\nin .cursorignore"]
    end
    subgraph services [Services]
        ERA["execution-results-api\n0 contracts"]
        SVCN["7 services\n400+ bare excepts"]
    end
    external --> interfaces --> services
```



## Batch 1 — Independent, highest value (4 parallel agents)

**A: VCR cassettes for 8 public/no-auth venues**

- Venues: `kalshi`, `polymarket`, `thegraph`, `defillama`, `barchart`, `open_meteo`, `upbit`, `fear_greed`
- Each: mock YAML cassette + `tests/vcr/test_{venue}_vcr.py` replay test
- File: `api-contracts/api_contracts/api_contracts_external/{venue}/mocks/*.yaml`
- File: `api-contracts/tests/vcr/test_{venue}_vcr.py`
- Raises coverage from 23% → ~39%

**B: `endpoint_registry.py` — add `BLACKLISTED_UNVALIDATED` status**

- File: `api-contracts/api_contracts/api_contracts_external/endpoint_registry.py`
- Add `BLACKLISTED_UNVALIDATED = "BLACKLISTED_UNVALIDATED"` to `EndpointStatus` enum
- Mark all 22 auth-required venues with `status=BLACKLISTED_UNVALIDATED, reason="auth_required_no_cassette"`
- Venues: binance WS private, okx private, bybit private, hyperliquid private, tardis (all), databento (all), deribit private, coinbase private, ibkr (all), ccxt (venue-dependent), api_football, arkham, aster, glassnode, footystats, soccer_football_info, odds_api, pinnacle, mev, ofr, openbb + github (BLACKLISTED_NOT_MARKET_DATA)

**C: URDI `_parse_raw` + 12 UMI `NotImplementedError` stubs**

- File: `unified-reference-data-interface/unified_reference_data_interface/base_adapter.py` — add abstract `_parse_raw(raw, schema_class) -> BaseModel`; failure raises `EnhancedError` + `log_event("INSTRUMENT_SCHEMA_VIOLATION")`
- UMI stubs to implement: `coinbase` (normalize_ohlcv, normalize_liquidation), `databento_adapter` (normalize_derivative_ticker, normalize_liquidation), `tardis_adapter` (normalize_ohlcv), `aster_adapter` (full suite from 27 schema models)

**D: `execution-results-api` — full contract adoption**

- Add `unified-internal-contracts>=1.0.0` to `execution-results-api/pyproject.toml`
- All exception handlers → `EnhancedError(category=..., correlation_id=str(uuid4()))`
- Add `log_event("STARTED")` / `log_event("STOPPED")` / `log_event("FAILED")` lifecycle events
- Replace any `dict[str, object]` response shapes with typed Pydantic models from UIC

## Batch 2 — New adapters in 3 groups (4 parallel agents)

**E: New UMI adapters group 1** (public/no-auth → VCR testable immediately)

- `adapters/prediction/kalshi_adapter.py` — REST, normalize to `CanonicalOdds`
- `adapters/prediction/polymarket_adapter.py` — REST, normalize to `CanonicalOdds`
- `adapters/defi/defillama_adapter.py` — REST, normalize to `CanonicalLiquidityPool`
- `adapters/alt_data/fear_greed_adapter.py` — REST, normalize to alt data schema

**F: New UMI adapters group 2** (auth-required, mark BLACKLISTED_UNVALIDATED)

- `adapters/cefi/aster_adapter.py` — 27 models in schema, needs full normalizer suite
- `adapters/cefi/upbit_adapter.py` — normalize_trade, normalize_orderbook
- `adapters/sports/odds_api_adapter.py` — normalize to `CanonicalOdds`
- `adapters/sports/pinnacle_adapter.py` — normalize to `CanonicalOdds`
- `adapters/onchain/glassnode_adapter.py` — normalize to onchain metrics schema
- `adapters/onchain/arkham_adapter.py` — normalize to onchain flow schema

**G: New UMI adapters group 3** (TradFi + Alt Data)

- `adapters/tradfi/ibkr_adapter.py` — reuse URDI ibkr adapter pattern, normalize_trade + normalize_ohlcv
- `adapters/tradfi/fred_adapter.py` — normalize to `CanonicalYieldCurve`
- `adapters/tradfi/ecb_adapter.py` — normalize to `CanonicalYieldCurve`
- `adapters/tradfi/ofr_adapter.py` — normalize to risk-free rate schema
- `adapters/tradfi/openbb_adapter.py` — normalize to `CanonicalBondData`
- `adapters/tradfi/yahoo_finance_adapter.py` — normalize_trade + normalize_ohlcv
- `adapters/alt_data/api_football_adapter.py` — normalize to football match schema
- `adapters/alt_data/footystats_adapter.py` — normalize to football stats schema
- `adapters/alt_data/soccer_football_adapter.py` — normalize to football match schema
- `adapters/onchain/mev_adapter.py` — normalize to MEV event schema
- Delete empty `api-contracts/api_contracts/api_contracts_external/defi/schemas.py`
- BLACKLIST `github` as `BLACKLISTED_NOT_MARKET_DATA`

**H: EnhancedError rollout — highest bare-except services**

- `execution-service` (201 bare excepts): wrap with `EnhancedError(category=SERVER_ERROR, correlation_id=uuid4())`
- `instruments-service` (62): same pattern
- `market-tick-data-handler` (48): same + add `log_event` on failures

## Batch 3 — Cleanup (2 parallel agents)

**I: Remaining EnhancedError rollout + position interface**

- `features-delta-one-service` (20), `features-onchain-service` (13), `features-volatility-service` (12)
- Remove `unified-position-interface` from `.cursorignore`
- Verify quality gates pass for UPI after making it visible

**J: Quality gates + VCR test runner verification**

- Run `cd api-contracts && bash scripts/quality-gates.sh --no-fix` to confirm all new VCR tests pass
- Run `cd unified-market-interface && bash scripts/quality-gates.sh --no-fix` to confirm new adapters pass
- Run `cd unified-reference-data-interface && bash scripts/quality-gates.sh --no-fix`

## Files Summary

- CREATE: ~30 new adapter files in `unified-market-interface/unified_market_interface/adapters/`
- CREATE: ~16 VCR cassette YAMLs + 8 test files in `api-contracts/tests/vcr/`
- MODIFY: `api-contracts/.../endpoint_registry.py` — new status enum + 22 endpoint entries
- MODIFY: `unified-reference-data-interface/.../base_adapter.py` — abstract `_parse_raw`
- MODIFY: `execution-results-api/` — UIC adoption
- MODIFY: 7 service repos — replace bare excepts with `EnhancedError`
- MODIFY: `.cursorignore` — remove unified-position-interface
- DELETE: `api-contracts/api_contracts/api_contracts_external/defi/schemas.py` (empty)
