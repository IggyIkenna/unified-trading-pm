---
name: UAC Residual Refactors and Provider Manifest
overview: |
  Residual UAC work: (1) Raw→normalized mapping — all domains (CeFi, DeFi, TradFi, Sports) with market/reference/derived split; TradFi by asset class (commodities, bonds, fx, equity, etf, equity index). (2) Nesting sports/DeFi/TradFi into canonical/market/, canonical/reference/, canonical/derived/. (3) Provider manifest expansion: testnet, data_type, API keys. Single SSOT for provider metadata. Supersedes uac_nested_domain_deviations and uac_package_reorganization.
todos:
  - id: nesting-sports-market
    content: Move sports market data (odds, live, bookmaker, betting, arbitrage) to canonical/market/sports/
    status: pending
  - id: nesting-sports-reference
    content:
      Move sports reference data (mappings, fixture, events, injury, lineup, player_stats) to
      canonical/reference/sports/
    status: pending
  - id: nesting-sports-execution
    content: Move BetOrder, BetExecution to canonical/execution/sports/
    status: pending
  - id: nesting-sports-errors
    content: Move sports errors to canonical/errors/sports/
    status: pending
  - id: nesting-defi-errors
    content: Move _venue_errors_defi to canonical/errors/defi/
    status: pending
  - id: nesting-defi-market-ref
    content: Create canonical/market/defi/ and canonical/reference/defi/; move Pyth, DeFiLlama, etc. per mapping
    status: pending
  - id: nesting-tradfi-market-ref
    content: Create canonical/market/{bonds,fx,commodities,equity,etf,equity_index}/ and reference/ equivalents
    status: pending
  - id: nesting-downstream
    content: Update downstream imports for new canonical paths
    status: pending
  - id: ref-canonical-reference
    content: Create canonical/reference/ with instruments.py (InstrumentType, ContractSpec)
    status: pending
  - id: ref-canonical-common
    content: Create canonical/common/ for cross-domain types (ohlcv, instruments, rate_limits)
    status: pending
  - id: ref-derived-alt
    content: Add canonical/derived/ or extend data_type for processed data (footy stats features, understats)
    status: pending
  - id: credentials-remove-coinglass-hyblock
    content: Remove coinglass-api-key and hyblock-api-key from credentials-registry and cursor rules
    status: completed
  - id: manifest-schema
    content: Extend provider_api_versions with has_testnet, testnet_keys_we_have, data_type, keys checklist
    status: completed
  - id: manifest-secrets-alignment
    content: Align with DATA_SOURCE_TO_SECRET and defi_keys plan; single SSOT
    status: pending
  - id: manifest-generate-script
    content: Extend generate_data_source_modes.py for testnet, data_type, keys checklist
    status: completed
  - id: manifest-codex-ssot
    content: Update Codex secrets-management.md, ssot-reference-mapping.md
    status: completed
  - id: manifest-cursor-rules
    content: Add provider-manifest-ssot.mdc cursor rule (provider manifest = SSOT for keys, testnet, data_type)
    status: completed
  - id: manifest-api-contracts-docs
    content: Update UAC CONTRIBUTING.md and PACKAGE_LAYOUT_AND_SCOPE.md to reference provider manifest
    status: completed
  - id: manifest-secret-check-script
    content: Add --check-secrets flag stub to generate_data_source_modes.py (optional)
    status: completed
  - id: manifest-audit-inventories
    content: Audit and consolidate all API key inventories into provider manifest
    status: completed
  - id: manifest-ui-docs-url
    content: Add ui_docs_url field to provider manifest schema (dashboard/user docs, distinct from spec_url)
    status: completed
isProject: false
---

# UAC Residual Refactors and Provider Manifest

## Superseded Plans (archived to plans/archive/)

- uac_nested_domain_deviations_9a5e89ee
- uac_package_reorganization_c1c0734e

**Symlink note:** Plans archived to `plans/archive/` may be symlinked from `.cursor/plans/` for agent context. The
canonical location is `unified-trading-pm/plans/archive/`.

## Completed (2026-03-14)

Provider manifest Phase 3: schema (has_testnet, ui_docs_url, data_type, keys checklist), generation script (ui_docs
column, --check-secrets stub), cursor rule (provider-manifest-ssot.mdc), UAC docs, Codex SSOT, audit. Alchemy and
Binance have full manifest entries.

## Phase 1: Sports/DeFi Nesting

Sports has both **market data** (live odds, trades, bookmaker) and **reference data** (fixtures, mappings, lineups,
player/team/league registry). Split by data type:

| From                                                                                                                  | To                                            | Data type |
| --------------------------------------------------------------------------------------------------------------------- | --------------------------------------------- | --------- |
| external/sports/canonical/odds.py, live.py, bookmaker.py, arbitrage.py, processed_odds.py, progressive.py             | canonical/market/sports/                      | market    |
| external/sports/canonical/mappings.py, fixture.py, events.py, injury.py, lineup.py, player_stats.py, fixture_stats.py | canonical/reference/sports/                   | reference |
| external/sports/canonical/\*features\*\*.py, features.py                                                              | canonical/derived/sports/ (or keep in market) | derived   |
| external/sports/canonical/betting.py                                                                                  | canonical/execution/sports/                   | execution |
| external/sports/errors.py                                                                                             | canonical/errors/sports/                      | errors    |
| schemas/\_venue_errors_defi.py                                                                                        | canonical/errors/defi/                        | errors    |

## Phase 1b: Derived / Alternative Data (catch-all for processed)

Data that is already processed (not raw): OHLCV bars, footy stats features (Understat, Footystats), xG/advanced metrics.
Use `canonical/derived/` or extend `data_type` in provider manifest with `derived` / `alternative` to distinguish from
raw market/reference.

| Data type   | Examples                                                                   |
| ----------- | -------------------------------------------------------------------------- |
| derived     | OHLCV (aggregated from ticks), ProcessedCandle                             |
| alternative | Footystats team stats (feature-like), Understat xG, \*features\*\* schemas |

## Raw → Normalized Mapping (all domains)

Goal: **All raw data easily mappable to normalised groupings.** Primary axis = data type (market | reference | derived).
Secondary axis = asset class / domain.

### Common (cross-domain — transcends CeFi, DeFi, TradFi, Sports)

Data types that share the same schema across domains. Do not duplicate under cefi/defi/bonds/etc.

| Data type | Normalized path               | Raw sources                                                                                | Notes                                                                                  |
| --------- | ----------------------------- | ------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------- |
| derived   | canonical/common/ohlcv/       | Aster, Barchart, Binance, Bybit, Databento, Yahoo, Polygon, Hyperliquid, Kalshi, OKX, etc. | CanonicalOhlcvBar, ProcessedCandle — same shape for crypto, equity, bonds, commodities |
| reference | canonical/common/instruments/ | All venues — instrument metadata, symbol registry                                          | InstrumentType, ContractSpec, instrument_key — cross-domain                            |
| market    | canonical/common/rate_limits/ | All venues — rate limit headers, specs                                                     | VenueRateLimitSpec, HttpRateLimitHeaders — cross-cutting                               |

**Rationale:** OHLCV from Binance (CeFi), Yahoo (TradFi), and Aster (onchain perps) normalizes to the same
`CanonicalOhlcvBar`. Placing it under `derived/cefi/` or `derived/equity/` would duplicate the type. Use
`canonical/common/` for types that transcend domain boundaries.

### CeFi (crypto)

| Data type | Normalized path           | Raw sources                                                            | Normalize module                      |
| --------- | ------------------------- | ---------------------------------------------------------------------- | ------------------------------------- |
| market    | canonical/market/cefi/    | Binance, Bybit, OKX, Deribit, CCXT, etc. — trades, orderbooks, tickers | cefi_trades, cefi_orderbooks, tickers |
| reference | canonical/reference/cefi/ | Binance, Bybit, Deribit, Dydx, etc. — instrument info, symbol metadata | reference_data, instruments           |
| derived   | canonical/common/ohlcv/   | (OHLCV lives in common — see above)                                    | ohlcv                                 |

### DeFi / Onchain

| Data type | Normalized path           | Raw sources                                                     | Normalize module            |
| --------- | ------------------------- | --------------------------------------------------------------- | --------------------------- |
| market    | canonical/market/defi/    | Pyth (oracle prices), TheGraph (swaps, pools — live)            | alt_data (Pyth), defi swaps |
| reference | canonical/reference/defi/ | Protocol specs, pool addresses, token addresses, chain registry | (to consolidate)            |
| derived   | canonical/derived/defi/   | Glassnode, Arkham, DeFiLlama (TVL, MVRV, flows)                 | alt_data                    |

### TradFi (commodities, bonds, fx, equity, etf, equity index)

| Asset class  | Data type | Normalized path                  | Raw sources                     | Normalize module                  |
| ------------ | --------- | -------------------------------- | ------------------------------- | --------------------------------- |
| bonds        | market    | canonical/market/bonds/          | FRED, ECB, OFR, OpenBB          | bonds_fx                          |
| bonds        | reference | canonical/reference/bonds/       | (tenor registry, series IDs)    | (to add)                          |
| fx           | market    | canonical/market/fx/             | ECB, Fix, IBKR                  | bonds_fx, fix                     |
| commodities  | market    | canonical/market/commodities/    | Baker Hughes, EIA, CFTC         | (to add — external schemas exist) |
| commodities  | reference | canonical/reference/commodities/ | Contract specs, series IDs      | (to add)                          |
| equity       | market    | canonical/market/equity/         | Yahoo, Polygon, IBKR, Databento | common/ohlcv, reference_data      |
| etf          | market    | canonical/market/etf/            | Same as equity                  | common/ohlcv                      |
| equity_index | market    | canonical/market/equity_index/   | Yahoo, Polygon, Databento       | common/ohlcv                      |

### Sports (already in Phase 1)

| Data type | Normalized path             | Raw sources                                     |
| --------- | --------------------------- | ----------------------------------------------- |
| market    | canonical/market/sports/    | Betfair, Pinnacle, Odds API, etc. — odds, live  |
| reference | canonical/reference/sports/ | Fixtures, mappings, lineups, player/team/league |
| derived   | canonical/derived/sports/   | Footystats, Understat, \*features\*\*           |

### Proposed canonical layout

```
canonical/
  common/           # cross-domain — transcends cefi, defi, tradfi, sports
    ohlcv/          # CanonicalOhlcvBar, ProcessedCandle (CeFi, TradFi, onchain)
    instruments/    # InstrumentType, ContractSpec, instrument_key
    rate_limits/    # VenueRateLimitSpec, HttpRateLimitHeaders
  market/
    cefi/          # trades, orderbooks, tickers
    defi/          # oracle prices, swaps (live)
    bonds/         # yield curves, CDS
    fx/            # FX rates
    commodities/   # rig count, EIA, CFTC
    equity/        # equity prices (uses common/ohlcv)
    etf/
    equity_index/
    sports/
  reference/
    cefi/          # venue-specific instrument metadata
    defi/          # protocol specs, pool addresses
    bonds/         # tenor registry
    commodities/   # contract specs
    equity/        # symbol registry
    sports/
  derived/
    cefi/          # domain-specific derived (excl. OHLCV)
    defi/          # Glassnode, Arkham, DeFiLlama
    sports/        # xG, features
```

## Coordination: ui-api-alerting-observability plan

The ui-api-alerting-observability-2026-03-14 plan adds a `LogLevel` enum to UAC (top-level export). When nesting/moving
modules in UAC, ensure this export path is preserved. That plan declares `depends_on` this plan to avoid conflicts.

---

## Phase 2: Reference Data

Create canonical/reference/ with:

- instruments.py (InstrumentType, ContractSpec) — CeFi/DeFi instruments
- sports/ — fixtures, mappings, lineups, player/team/league registry (from Phase 1)

Document reference = mappings + registry + reference/instruments + reference/sports.

## Phase 3: Provider Manifest Expansion

### 3.1 Schema Table

Extend provider_api_versions.yaml with these fields per provider:

| Field                | Type                                         | Description                                                               |
| -------------------- | -------------------------------------------- | ------------------------------------------------------------------------- |
| spec_url             | str                                          | API spec / endpoint docs (existing)                                       |
| ui_docs_url          | str                                          | Dashboard, user docs, or UI docs URL (distinct from spec_url)             |
| has_testnet          | bool                                         | Provider offers testnet/sandbox environment                               |
| testnet_keys_we_have | bool                                         | We have testnet API keys provisioned                                      |
| testnet_network      | str                                          | Testnet name (e.g. Sepolia, testnet)                                      |
| data_type            | central, private, both, derived, alternative | Raw vs processed; derived/alternative = OHLCV, footy features, understats |
| keys_public_we_have  | bool                                         | We have public/read-only API keys                                         |
| keys_private_we_have | bool                                         | We have private/write API keys                                            |
| secret_names         | { public: [], private: [] }                  | Secret Manager secret names for keys                                      |

**Data source vs endpoint:** One provider entry can map to multiple endpoints (e.g. REST + WebSocket, mainnet +
testnet). The manifest is provider-level; endpoints are listed via spec_url and ui_docs_url. For 1:1 endpoint registry,
consider an optional `endpoints: [{ url, type }]` array per provider.

### 3.2 DeFi Testnet

Align with defi_keys plan:

- **Sepolia** — Ethereum testnet (Alchemy, etc.)
- **Tenderly fork** — Local/fork testing
- **Hyperliquid testnet** — Hyperliquid testnet environment

### 3.3 Checklist Output

`generate_data_source_modes.py` outputs a markdown table:

| provider | modes | has_testnet | testnet_keys | data_type | keys_public | keys_private | ui_docs | gap |
| -------- | ----- | ----------- | ------------ | --------- | ----------- | ------------ | ------- | --- |

### 3.5 Parallel Execution

Use parallel agents for independent tasks (e.g. nesting-sports-domain + nesting-sports-execution +
nesting-sports-errors; manifest-schema + manifest-generate-script + manifest-cursor-rules). See
cursor-rules/core/parallel-agent-execution.mdc.

### 3.6 SSOT Alignment

Provider manifest (`provider_api_versions.yaml`) = single source. Align:

- `DATA_SOURCE_TO_SECRET` (unified-cloud-interface or config)
- defi_keys plan (Plan 3)
- Codex: secrets-management.md, ssot-reference-mapping.md
