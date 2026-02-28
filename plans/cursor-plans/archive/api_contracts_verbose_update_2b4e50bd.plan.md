---
name: API Contracts Verbose Update
overview: Incorporate all 10 sub-agent investigative findings into the API Contracts addendum and task list; remove Kraken entirely; add Upbit/Coinbase; distinguish Binance-spot vs Binance-futures; validate Bybit/OKX unified APIs; achieve full typability (external APIs, internal system, pandas, dependencies) with no surprises.
todos:
  - id: addendum-section-15
    content: Add Section 15 (Sub-Agent Findings) to API_CONTRACTS_AUDIT_ADDENDUM.md
    status: completed
  - id: addendum-venue-fixes
    content: Update addendum with venue universe (Upbit, Coinbase; Binance-spot/futures; Bybit/OKX unified; remove Kraken)
    status: completed
  - id: task-list-updates
    content: Update API_CONTRACTS_TASK_LIST.md with priorities, schema names, venue fixes
    status: completed
  - id: kraken-removal
    content: Remove Kraken from entire codebase (130+ files across codex, docs, rules, api-contracts, UMI, UTEI, URDI, services)
    status: completed
  - id: addendum-to-plan
    content: Consolidate addendum Sections 1-14 content into this plan
    status: completed
  - id: task-list-to-plan
    content: Consolidate task list DOs into this plan
    status: completed
isProject: false
---

# API Contracts Verbose Update — Master Plan

## Primary Goal: Everything Typable, No Surprises

**Objective:** Dramatically improve typing for everything external to our system (APIs, cloud SDKs, market data, orders, positions) and everything internal (pandas DataFrames, config, schemas). Dependencies like pandas should be fully typable. No surprises at runtime — validation and type checking catch drift before execution.

---

## Venue Universe (CRITICAL — Codex Rules)

### Venues in Scope


| Venue               | Endpoint Model        | Notes                                                                              |
| ------------------- | --------------------- | ---------------------------------------------------------------------------------- |
| **BINANCE-SPOT**    | Separate from futures | `api.binance.com` — spot only                                                      |
| **BINANCE-FUTURES** | Separate from spot    | `fapi.binance.com` — USDT-M, coin-M, options                                       |
| **OKX**             | Unified v5 API        | All instrument types (SPOT, MARGIN, SWAP, FUTURES, OPTION) in one API              |
| **BYBIT**           | Unified v5 API        | All instrument types (spot, perpetual, futures, options) in one API — **validate** |
| **UPBIT**           | Single API            | Korean market; add explicitly                                                      |
| **COINBASE**        | Single API            | Spot, futures (when available); add explicitly                                     |
| **DERIBIT**         | Single API            | Options, futures, spot                                                             |
| **HYPERLIQUID**     | Single API            | On-chain perps                                                                     |
| **ASTER**           | Single API            | On-chain perps                                                                     |
| **IBKR**            | TWS/ib_insync         | TradFi execution                                                                   |
| **Databento**       | REST                  | TradFi market data                                                                 |
| **Tardis**          | REST                  | CeFi market data                                                                   |
| **Yahoo Finance**   | REST                  | Equity/ETF data                                                                    |
| **Barchart**        | CSV (no API)          | VIX 15m historical                                                                 |


### Kraken: REMOVE ENTIRELY

**Kraken is NOT in our universe** — not MVP, not expanded. Remove from:

- **unified-trading-codex:** All docs, rules, subscription-model, batch/live per-service docs, epics, validators, architecture
- **api-contracts:** `api_contracts/kraken/`, venue_manifest, collect_responses, validate_schemas, tests, collected_responses/kraken/
- **unified-market-interface:** adapters/kraken.py, factory, ws_handlers, data_source_mapping, schemas
- **unified-reference-data-interface:** adapters/kraken.py, factory, tests
- **unified-trade-execution-interface:** factory, schemas, base_adapter
- **position-balance-monitor-service:** account_query_client
- **risk-and-exposure-service:** models, tests
- **execution-service:** manual_schemas, manual_instruction_api, specs, nautilus_compatibility
- **settlement-ui, live-health-monitor-ui:** ManualTradingPanel, ManualTradingControls, App
- **execution-algo-library:** SOR tests
- **instruments-service:** DEPENDENCIES.md
- **market-tick-data-handler:** nautilus_schema
- **unified-trading-pm:** All plans, task lists, library docs

**Grep scope:** ~130 files. Delete Kraken adapter code, remove from venue lists, remove from config generators, instruction generators, routing matrices.

### Binance: Spot, USD-M, Coin-M (Three Endpoints)

**Different endpoints; futures and perps share USD-M:**

- **BINANCE-SPOT:** `api.binance.com` — spot pairs only; 24hr ticker has prevClosePrice, bid/ask
- **BINANCE-USDM:** `fapi.binance.com` — USDT-margined futures + perpetuals (same endpoint); 24hr ticker has lastFundingRate, no bid/ask
- **BINANCE-COINM:** `dapi.binance.com` — coin-margined futures; 24hr ticker has pair, no bid/ask

`BinanceTicker` schema supports all three (optional fields per endpoint). `venue_manifest` and `ENDPOINT_SCHEMA_MAP` should use `binance-spot`, `binance-usdm`, `binance-coinm` as distinct keys.

### Bybit and OKX: Unified APIs (Validate)

- **OKX v5:** Single base URL; `instType` distinguishes SPOT, MARGIN, SWAP, FUTURES, OPTION. One API for all instrument types. **Validate:** Confirm we always use v5 unified; no legacy spot-only or futures-only endpoints.
- **Bybit v5:** Single base URL; `category` distinguishes spot, linear, inverse, option. One API for all. **Validate:** Confirm we always use v5 unified; no legacy split.

**Action:** Audit UMI, UTEI, URDI, execution-service for any Bybit/OKX usage. Ensure all use unified v5. Document in api-contracts that we contract the unified API only.

---

## Consolidated Content from Addendum (Sections 1–14)

### 1. TradFi: Databento + IBKR Only

- Databento: market data (trades, OHLCV, MBP-1, TBBO, definitions)
- IBKR: execution (orders, positions, account)
- Add `DatabentoTbbo` (distinct from MBP-1); L2_MBP mode expects tbbo

### 2. VIX: Barchart Batch, Live Research

- Barchart: BARCHART_OHLCV_15M_SCHEMA for historical
- Research: Databento index (in dev), IBKR TWS, others
- Migrate Barchart schema to api-contracts

### 3. DeFi: Alchemy, The Graph, Protocol SDKs

- Subgraph: swaps, pools, liquidity
- Alchemy: RPC, transfers, logs
- Protocol SDKs: AAVE, Compound, Morpho, Lido, Curve, Fluid, Euler
- Atomic: Instadapp, Morpho flash loans
- MEV: Flashbots, MEV-Share

### 4. MEV Protection

- Flashbots, MEV Blocker, bloXroute, Titan
- Reverse-engineer specs into api_contracts/mev/

### 5. Chain Scope: Ethereum + BTC Only

- No bridging
- BTC: vanilla basis only

### 6. Chain × Instruction Validation

- Strategy-service + execution-service: reject STAKE/UNSTAKE/FLASH_*/ATOMIC for BTC

### 7. On-Chain Transfers

- CEX withdrawal schemas (Binance, OKX, Bybit, Upbit, Coinbase — NOT Kraken)
- eth_sendRawTransaction, eth_sendTransaction, ERC20 calldata
- Instadapp/Morpho transfer payloads

### 8. Instrument Types

- INSTRUMENT_TYPES_BY_VENUE matrix
- Per-venue nuances (OKX instType, Binance contractType, etc.)

### 9. Validation Pipeline

- (venue, instrument_type, operation) plausibility before external SDKs

### 10. collected_responses / generated_schemas / api_contracts

- Document flow in README

### 11. SCHEMA_VERSIONS.md + Pinned Validation

- Pinned package versions; CI validates against exact versions

### 12. Endpoints vs Credentials

- api-contracts owns endpoints; interfaces own credentials
- ENDPOINT_SCHEMA_MAP: (venue, endpoint) → schema_class

### 13. Error Schemas

- Per-venue response models; central VENUE_ERROR_MAP
- Rate limit (429), WebSocket errors, FIX session

### 14. Exchange State, Data Source State

- Health, ping, WebSocket lifecycle, FIX, REST errors
- Tie each schema to (venue, endpoint) or (venue, channel)

### 15. Cloud SDKs (GCP, AWS)

- Compute, Cloud Run, GCS, BigQuery, EC2, ECS, S3, Glue, quotas
- Sync/async per endpoint

### 16. Quota Handling (UTD v3)

- QuotaBrokerClient, QuotaExceededMessage, VmQuotaShape

---

## Consolidated Task List (DOs) — With Venue Fixes

### 1. Market Data / Feed


| DO  | Description                                                                      | Venues             | Priority |
| --- | -------------------------------------------------------------------------------- | ------------------ | -------- |
| 1.1 | Databento: OHLCV-1m, OHLCV-1s, trades, TBBO, MBP-1, MBP-10, definition           | Databento          | P0       |
| 1.2 | DatabentoTbbo schema                                                             | Databento          | P0       |
| 1.3 | Tardis: BookSnapshot5, Liquidations, DerivativeTicker, OptionsChain, raw schemas | Tardis             | P0       |
| 1.4 | Barchart BARCHART_OHLCV_15M_SCHEMA                                               | Barchart           | P1       |
| 1.5 | Yahoo: Ohlcv24h, Splits, Dividends                                               | Yahoo              | P1       |
| 1.6 | Per-venue data types                                                             | All (excl. Kraken) | P2       |


### 2. Orders / Positions


| DO  | Description                                  | Venues                                                     | Priority |
| --- | -------------------------------------------- | ---------------------------------------------------------- | -------- |
| 2.1 | CEX order schemas: submit, ack, fill, cancel | Binance-spot, Binance-futures, OKX, Bybit, Upbit, Coinbase | P0       |
| 2.2 | CEX position schemas                         | Same                                                       | P0       |
| 2.3 | IBKR order/position                          | IBKR                                                       | P0       |
| 2.4 | DeFi order/position                          | Uniswap, AAVE, Morpho                                      | P1       |
| 2.5 | CEX withdrawal                               | Binance, OKX, Bybit, Upbit, Coinbase                       | P1       |


### 3. Reference Data


| DO  | Description                              | Priority |
| --- | ---------------------------------------- | -------- |
| 3.1 | INSTRUMENT_TYPES_BY_VENUE (excl. Kraken) | P0       |
| 3.2 | Symbology per venue                      | P1       |
| 3.3 | Contract specs (tick, lot, expiry)       | P2       |


### 4. Exchange Status / Market Feed Status


| DO  | Description         | Venues                                                              | Priority |
| --- | ------------------- | ------------------------------------------------------------------- | -------- |
| 4.1 | Health/ping schemas | All (excl. Kraken)                                                  | P1       |
| 4.2 | WebSocket lifecycle | Binance-spot, Binance-futures, OKX, Bybit, Deribit, Upbit, Coinbase | P1       |
| 4.3 | ENDPOINT_SCHEMA_MAP | All                                                                 | P0       |


### 5. Error Handling


| DO  | Description                              | Priority |
| --- | ---------------------------------------- | -------- |
| 5.1 | VENUE_ERROR_MAP expansion (excl. Kraken) | P0       |
| 5.2 | Rate limit (429) schemas                 | P1       |
| 5.3 | error_example.json per venue             | P2       |


### 6–8. Cloud SDKs, Quota

Same as task list; add GCP/AWS Pydantic schemas, QuotaBroker schemas.

### 9. DeFi / MEV / Transfers

Same as task list; CEX withdrawal excludes Kraken.

### 10. Kraken Removal (New)


| DO   | Description                                                                 | Scope                             |
| ---- | --------------------------------------------------------------------------- | --------------------------------- |
| 10.1 | Delete api-contracts kraken/ dir, venue_manifest entry, collected_responses | api-contracts                     |
| 10.2 | Delete UMI kraken adapter, factory refs                                     | unified-market-interface          |
| 10.3 | Delete URDI kraken adapter, factory refs                                    | unified-reference-data-interface  |
| 10.4 | Remove Kraken from UTEI factory, schemas                                    | unified-trade-execution-interface |
| 10.5 | Remove from position-balance-monitor, risk-and-exposure, execution-service | Services                          |
| 10.6 | Remove from codex docs, rules, epics, validators                            | unified-trading-codex             |
| 10.7 | Remove from UI (settlement-ui, live-health-monitor-ui)                      | UIs                               |
| 10.8 | Remove from unified-trading-pm plans, task lists                            | PM                                |


---

## Sub-Agent Findings (Section 15 Content for Addendum)

### 15.1 Market Data / Feed

- Databento: Tbbo, Mbp10, raw schemas, helpers
- Tardis: BookSnapshot5, Liquidations, DerivativeTicker, OptionsChain, raw schemas
- Barchart: BarchartOhlcv15m
- Yahoo: Ohlcv24h, Splits, Dividends

### 15.2 Orders / Positions

- CEX: Order submit/ack/cancel, position query, margin balance, realized PnL
- Venues: Binance-spot, Binance-futures, OKX, Bybit, Upbit, Coinbase (no Kraken)
- DeFi: Swap/lend/borrow request/response, flash loans, atomic bundles

### 15.3 Reference Data

- INSTRUMENT_TYPES_BY_VENUE
- Symbology, ETF, Index, Options chain, Greeks
- Cross-venue type mapping (OKX SWAP = Binance PERPETUAL)

### 15.4 Exchange Status

- REST health, WebSocket lifecycle, FIX, ENDPOINT_SCHEMA_MAP
- ~50+ missing schemas

### 15.5 Error Handling

- VENUE_ERROR_MAP (13 venues missing; Kraken removed)
- Rate limit (429), classify(), endpoint mapping

### 15.6–15.10

Cloud SDKs, Quota, DeFi/MEV, TradFi/VIX — as in original plan.

---

## Implementation Phases

**Phase 1 (P0):**

- Kraken removal (entire codebase)
- Addendum Section 15 + venue universe updates
- Task list updates (remove Kraken, add Upbit/Coinbase, Binance-spot/futures)
- DatabentoTbbo, full Tardis migration
- Coinbase, Upbit order/position schemas
- QuotaBroker schemas, INSTRUMENT_TYPES_BY_VENUE, ENDPOINT_SCHEMA_MAP
- VENUE_ERROR_MAP expansion (excl. Kraken)

**Phase 2 (P1):**

- BarchartOhlcv15m, YahooOhlcv24h
- CEX order submit/ack/cancel, margin, withdrawal (Binance, OKX, Bybit, Upbit, Coinbase)
- Rate limit schemas
- GCP/AWS Cloud SDK Pydantic schemas
- MEV, flash loan schemas

**Phase 3 (P2):**

- WebSocket lifecycle, FIX
- Reference data: symbology, ETF, Index, Options chain
- Error examples
- Sync/async docs

---

## Files to Modify


| File                                                                            | Change                                                                                                            |
| ------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| API_CONTRACTS_AUDIT_ADDENDUM.md                                                 | Add Section 15; add venue universe (Upbit, Coinbase; Binance-spot/futures; Bybit/OKX unified); remove Kraken refs |
| API_CONTRACTS_TASK_LIST.md                                                      | Priorities; schema names; remove Kraken; add Upbit, Coinbase; Binance-spot/futures; add Kraken removal DOs        |
| api-contracts/                                                                  | Delete kraken/; update venue_manifest; remove from collect_responses, validate_schemas, tests                     |
| unified-market-interface/                                                       | Delete adapters/kraken.py; remove from factory, ws_handlers, data_source_mapping                                  |
| unified-reference-data-interface/                                               | Delete adapters/kraken.py; remove from factory                                                                    |
| unified-trade-execution-interface/                                              | Remove Kraken from factory, schemas                                                                               |
| unified-trading-codex/                                                          | Remove Kraken from all docs, rules, epics, validators                                                             |
| position-balance-monitor-service, risk-and-exposure-service, execution-service | Remove Kraken refs                                                                                                |
| settlement-ui, live-health-monitor-ui                                           | Remove Kraken from venue dropdowns                                                                                |
| unified-trading-pm/                                                             | Remove Kraken from plans, task lists                                                                              |


---

## Sub-Agent Execution Strategy (Up to 10 Agents)

**Principle:** Different repos = zero conflict risk. Launch parallel agents per repo/scope.


| Agent  | Scope             | Task                                                                                                                                       | Repo(s)                                                               |
| ------ | ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------- |
| **1**  | Kraken removal    | Delete api_contracts/kraken/, venue_manifest entry, collected_responses/kraken/, update collect_responses.py, validate_schemas.py, tests   | api-contracts                                                         |
| **2**  | Kraken removal    | Delete adapters/kraken.py; remove from factory, ws_handlers, data_source_mapping, schemas                                                  | unified-market-interface                                              |
| **3**  | Kraken removal    | Delete adapters/kraken.py; remove from factory, tests                                                                                      | unified-reference-data-interface                                      |
| **4**  | Kraken removal    | Remove Kraken from factory, schemas, base_adapter                                                                                          | unified-trade-execution-interface                                     |
| **5**  | Kraken removal    | Remove from account_query_client, models, manual_schemas, manual_instruction_api, specs, nautilus_compatibility                            | position-balance-monitor, risk-and-exposure, execution-service       |
| **6**  | Kraken removal    | Remove from all docs, rules, epics, validators, subscription-model, architecture                                                           | unified-trading-codex                                                 |
| **7**  | Kraken removal    | Remove from ManualTradingPanel, ManualTradingControls, App; remove from PM plans, task lists                                               | settlement-ui, live-health-monitor-ui, unified-trading-pm             |
| **8**  | Kraken removal    | Remove from execution-algo-library SOR, instruments-service DEPENDENCIES, market-tick-data-handler nautilus_schema                         | execution-algo-library, instruments-service, market-tick-data-handler |
| **9**  | Addendum updates  | Add Section 15 (Sub-Agent Findings); add venue universe (Upbit, Coinbase; Binance-spot/futures; Bybit/OKX unified); remove all Kraken refs | API_CONTRACTS_AUDIT_ADDENDUM.md                                       |
| **10** | Task list updates | Add priorities, schema names; remove Kraken; add Upbit, Coinbase; Binance-spot/futures; add Kraken removal DOs (10.1–10.8)                 | API_CONTRACTS_TASK_LIST.md                                            |


**Agent prompts:** Each agent receives: (1) "Follow all workspace cursor rules in .cursorrules"; (2) "uv not pip, quickmerge not git push"; (3) Specific task from table above; (4) "Delete deprecated code — do not archive in place"; (5) "Report back: files changed, any blockers".

**Execution order:** Agents 1–8 can run in parallel (different repos). Agents 9–10 (addendum, task list) can run in parallel with each other and with 1–8.

---

## Sub-Agent Execution Results (2026-02-26)


| Agent | Scope                 | Status | Notes                                                                                                            |
| ----- | --------------------- | ------ | ---------------------------------------------------------------------------------------------------------------- |
| 1     | api-contracts         | Done   | Deleted kraken/, collected_responses/kraken/; updated venue_manifest, collect_responses, validate_schemas, tests |
| 2     | UMI                   | Done   | Deleted adapters/kraken.py; updated factory, ws_handlers, data_source_mapping, schemas; 57 tests pass            |
| 3     | URDI                  | Done   | Deleted adapters/kraken.py; updated factory, tests                                                               |
| 4     | UTEI                  | Done   | Removed from factory, base_adapter; 39 tests pass                                                                |
| 5     | Services              | Done   | PBM, risk-and-exposure, execution-service updated                                                               |
| 6     | Codex                 | Done   | 40+ files; validate-alignment.py keeps forbidden_venues={"KRAKEN"} as guard                                      |
| 7     | UIs + PM              | Done   | settlement-ui, live-health-monitor-ui, unified-trading-pm plans                                                  |
| 8     | Algo/instruments/tick | Done   | execution-algo-library, instruments-service, market-tick-data-handler, unified-trading-services                  |
| 9     | Addendum              | Done   | Section 15 added; Venue Universe section; Kraken REMOVED documented                                              |
| 10    | Task list             | Done   | Priorities, Binance-spot/futures, Upbit/Coinbase, Kraken removal DOs 10.1–10.8                                   |


**Fixed:** Binance ticker schema — `BinanceTicker` now supports Spot (prevClosePrice, bid/ask), USD-M (lastFundingRate), Coin-M; `ticker_example.json` updated to full response; `test_all_examples_validate_against_contracts` passes.

**Pre-existing (unchanged):** URDI merge conflict in unified-trading-services; risk-and-exposure config validation; coverage thresholds in UTEI, execution-algo-library.

---

## Phase 2: Full API Contracts Scope Expansion (10 Agents) — EXECUTED 2026-02-26

**What was done:** Phase 1 = Kraken removal + doc updates. Phase 2 = Full scope implementation across 10 agents.

**Phase 2 agents** — split task list DOs across 10 agents to implement schemas, migrations, and infrastructure. Use **Context7** for external API/SDK docs.


| Agent  | Scope                           | DOs to Implement                                                                                               | Repos                                               |
| ------ | ------------------------------- | -------------------------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| **1**  | Market data – Databento, Tardis | 1.1–1.3: DatabentoTbbo, Mbp10, Tardis BookSnapshot5, Liquidations, DerivativeTicker, OptionsChain, raw schemas | api-contracts, market-tick-data-handler             |
| **2**  | Market data – Barchart, Yahoo   | 1.4–1.6: BarchartOhlcv15m, YahooOhlcv24h, per-venue data types                                                 | api-contracts                                       |
| **3**  | Orders / Positions              | 2.1–2.5: CEX order/position/withdrawal schemas (Binance-spot, Binance-usdm, OKX, Bybit, Upbit, Coinbase)       | api-contracts                                       |
| **4**  | Reference data, Exchange status | 3.1–3.4, 4.1–4.6: INSTRUMENT_TYPES_BY_VENUE, symbology, health/ping, WebSocket lifecycle, ENDPOINT_SCHEMA_MAP  | api-contracts                                       |
| **5**  | Error handling                  | 5.1–5.5: VENUE_ERROR_MAP expansion, rate limit schemas, error_example.json                                     | api-contracts                                       |
| **6**  | Cloud SDKs GCP                  | 6.1–6.6: Compute, Cloud Run, GCS, BigQuery, quota Pydantic schemas                                             | api-contracts/cloud_sdks                            |
| **7**  | Cloud SDKs AWS                  | 7.1–7.6: EC2, ECS, S3, Glue, Service Quotas schemas                                                            | api-contracts/cloud_sdks                            |
| **8**  | Quota handling                  | 8.1–8.5: QuotaBrokerClient, QuotaExceededMessage, VmQuotaShape                                                 | api-contracts, unified-trading-deployment-v3        |
| **9**  | DeFi / MEV / Transfers          | 9.1–9.5: MEV schemas, protocol SDKs, eth_sendRawTransaction, CEX withdrawal                                    | api-contracts                                       |
| **10** | Cross-cutting, TradFi           | 11.1–12.6, 10.1–10.4: SCHEMA_VERSIONS.md, endpoints.py, chain validation, Barchart, VIX                        | api-contracts, strategy-service, execution-service |


**Execution:** 10 agents launched in parallel; all completed.

### Phase 2 Execution Results


| Agent | Scope              | Status | Deliverables                                                                                                                                                                                             |
| ----- | ------------------ | ------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1     | Databento + Tardis | Done   | DatabentoTbbo, DatabentoMbp10; TardisBookSnapshot5, Liquidations, DerivativeTicker, OptionsChain; raw schemas; dataset→venue mappings; market-tick-data-handler migration                                |
| 2     | Barchart + Yahoo   | Done   | BarchartOhlcv15m, YahooOhlcv24h/Splits/Dividends; VENUE_DATA_TYPES.md                                                                                                                                    |
| 3     | CEX order/position | Done   | 67 schemas across Binance-spot/usdm/coinm, OKX, Bybit, Upbit, Coinbase                                                                                                                                   |
| 4     | Canonical mappings | Done   | canonical_mappings.py (DATA_SOURCE_TO_VENUES, VENUE_TO_DATA_SOURCE, DATASET_TO_CANONICAL_VENUE, SYMBOL_MAPPINGS); INSTRUMENT_TYPES_BY_VENUE; ENDPOINT_SCHEMA_MAP; migrated from unified-trading-services |
| 5     | Error handling     | Done   | VENUE_ERROR_MAP 3→15 venues; classify() for 7 venues; RateLimitResponse; WebSocketClose; error_example.json                                                                                              |
| 6     | GCP Cloud SDKs     | Done   | 32 schemas (Compute, Cloud Run, GCS, BigQuery, quotas); SYNC_ASYNC.md                                                                                                                                    |
| 7     | AWS Cloud SDKs     | Done   | 42 schemas (EC2, ECS, Lambda, S3, Glue, Service Quotas)                                                                                                                                                  |
| 8     | Quota handling     | Done   | 14 schemas (QuotaBroker, VmQuotaShape, GcpQuotaExceeded, AwsQuotaExceeded)                                                                                                                               |
| 9     | DeFi/MEV/transfers | Done   | 44 schemas (MEV, protocol SDKs, eth_sendRawTransaction, ERC20 calldata, CEX withdrawal); DEFI_DATASET_TO_CANONICAL_VENUE                                                                                 |
| 10    | Cross-cutting      | Done   | endpoints.py, SCHEMA_VERSIONS.md, TRADFI_VENUE_NUANCES.md, VIX_LIVE_RESEARCH.md; README version note                                                                                                     |


---

## Canonical Mappings (SSOT in api-contracts)

**Principle:** All canonical naming and mappings live in api-contracts. Interfaces and services **reference** api-contracts; they do not own or duplicate mapping logic. api-contracts version = version of our mappings, schemas, and endpoints.

**Mappings to implement:**


| Mapping                       | Location              | Purpose                                                                                                       |
| ----------------------------- | --------------------- | ------------------------------------------------------------------------------------------------------------- |
| **Canonical venue names**     | venue_constants.py    | BINANCE-SPOT, BINANCE-USDM, OKX, BYBIT, etc.                                                                  |
| **Data source → venues**      | canonical_mappings.py | tardis → [BINANCE-SPOT, BINANCE-FUTURES, ...]; databento → [XNAS, XNYS, CME, ...]; ccxt → [...]; ibkr → [...] |
| **Dataset → canonical venue** | canonical_mappings.py | Databento dataset_id (e.g. GLBX.MDP3) → CME; Tardis exchange (binance-futures) → BINANCE-USDM                 |
| **Symbol mappings**           | canonical_mappings.py | BTCUSDT ↔ BTC-USDT ↔ XBTUSD; cross-venue, cross-data-source                                                   |
| **Instrument type canonical** | venue_constants.py    | INSTRUMENT_TYPES_BY_VENUE; PERPETUAL vs SWAP vs FUTURE normalization                                          |


**Scope constraints:**

- **CeFi:** No new venues beyond scoped (Binance-spot/usdm/coinm, OKX, Bybit, Upbit, Coinbase, Deribit, Hyperliquid, Aster)
- **DeFi:** Euler, Fluid (Plasma), ERC20, BTC-related chains only; nothing outside
- **TradFi:** IBKR + Databento (~506 venues); no direct CME
- **Same venue, multiple data sources:** Yes — e.g. Binance via Tardis, Binance via CCXT; document which datasets map to which canonical venue

**Nuances:** Even in unified schemas (CCXT, IBKR, Databento), capture venue-specific differences (field names, symbol formats, instrument type naming). Document in schema docstrings or companion mapping files.

---

## Schema Version Alignment and Verification

**Principle:** Schemas are pinned to SDK/API versions. CI fails if versions don't align. Two-level testing.

### api-contracts (Unit Test)

- **Context7 check:** What's available in the external API docs vs what we have in schemas. Smoke test: do we have schemas for all endpoints we claim to support?
- **Version pinning:** SCHEMA_VERSIONS.md + pyproject.toml `[schema-validation]` pin SDK versions (databento, tardis, binance API version, etc.)
- **CI gate:** If schema-validation deps are installed and any pinned version doesn't match → FAIL
- **Unit test:** `test_schemas_align_with_context7` (or similar) — use Context7 to fetch API spec, compare available endpoints/response shapes vs our schemas; report gaps

### Interfaces (Integration Test)

- **UMI, UPI, URDI, UTEI, UDEI:** Each interface pins SDK/API version (e.g. Binance API v2)
- **Version alignment check:** If interface depends on SDK version X, api-contracts must have schemas for version X. If not → FAIL
- **Integration test:** Call real API with credentials; validate response against api-contracts schema. Smoke test: does what we get back match what we expect?
- **Schema loading:** Interfaces load schemas pinned to the version they use. If on Binance v2, must have expansive schemas for v2.

### Dependency Checking (Like Internal Deps)

- **api-contracts CI:** Install pinned [schema-validation] deps; run schema validation; fail if versions don't align
- **Interface CI:** If interface has SDK dep (e.g. databento-python 0.32.x) and api-contracts doesn't have schemas for that version → FAIL
- **Out-of-version:** Same pattern as internal dependency checking — if interface uses SDK v2 but api-contracts only has v1 schemas → FAIL

---

## Phase 3: Schema Verification (10 Agents) — Context7 + Version Alignment — DONE

Phase 3 agents completed 2026-02-26. See agent reports for Binance, OKX/Bybit, Databento/Tardis, CCXT/IBKR, DeFi, Cloud SDKs, SCHEMA_VERSIONS, CI gate, UMI, UTEI/URDI/UDEI/UPI.

---

## Phase 4: Remaining Items + Institutional Gaps (10 Agents) — DONE 2026-02-27

**Source:** [api_contracts_institutional_gaps_518ca0e3.plan.md](/.cursor/plans/api_contracts_institutional_gaps_518ca0e3.plan.md) + Phase 3 remaining items.

### Concrete Next Steps (File Edits)


| Step | File(s)                                                                                          | Edit                                                                                                                                                                                                                                                                                                            |
| ---- | ------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | `api-contracts/scripts/check_sdk_version_alignment.py`                                           | **Create** script: parse SCHEMA_VERSIONS.md + pyproject [schema-validation]; for each interface (UMI, UTEI, URDI) read SDK deps; FAIL if interface SDK version not covered by api-contracts schemas                                                                                                             |
| 2    | `api-contracts/scripts/quality-gates.sh`                                                         | Add step: run `check_sdk_version_alignment.py` when schema-validation deps installed                                                                                                                                                                                                                            |
| 3    | `unified-trade-execution-interface/tests/integration/test_api_contracts_integration.py`          | **Create** integration test: call real Binance/CCXT API; validate response with CcxtOrder, CcxtTrade, CcxtPosition; skip if no credentials                                                                                                                                                                      |
| 4    | `unified-reference-data-interface/tests/integration/test_api_contracts_integration.py`           | **Create** integration test: call CCXT fetch_markets/fetch_ticker; validate with CcxtMarket, CcxtTicker                                                                                                                                                                                                         |
| 5    | `api-contracts/api_contracts/ccxt/schemas.py`                                                    | Expand: add CcxtFundingRate, CcxtOpenInterest, CcxtOhlcv, CcxtAggTrade; expand CcxtPosition (18 fields), CcxtOrder (reduceOnly, stopPrice, trades), CcxtMarket (20 fields), CcxtBalance (debt, timestamp), CcxtTrade (takerOrMaker, fees array)                                                                 |
| 6    | `api-contracts/api_contracts/schemas/derivatives.py`                                             | Add: PositionRisk, InsuranceFundState, LongShortRatio, OpenInterestHistory, FundingRateHistory, SettlementEvent, VolSurface, VolSurfaceSlice, VolSmilePoint, VolTermStructure                                                                                                                                   |
| 7    | `api-contracts/api_contracts/schemas/accounts.py`                                                | **Create** shared: DepositAddress, DepositRecord, WithdrawalRecord, InternalTransfer, SubAccount, ExchangeFeeSchedule, PortfolioMarginAccount                                                                                                                                                                   |
| 8    | `api-contracts/api_contracts/binance/schemas.py`                                                 | Add: BinanceAggTrade, BinanceFundingRateHistory, BinancePremiumIndex, BinanceDepositAddress, BinanceDepositHistory, BinanceWithdrawalHistory, BinanceFeeRate, BinanceInternalTransfer, BinanceSubAccount, BinanceAdlQuantile, BinanceInsuranceFund, BinancePositionRisk, BinancePapiAccount, BinancePapiBalance |
| 9    | `api-contracts/api_contracts/okx/schemas.py`, `bybit/schemas.py`                                 | Add fee, deposit, withdrawal, funding history, risk limit, long/short ratio, portfolio margin schemas per institutional gaps                                                                                                                                                                                    |
| 10   | `api-contracts/api_contracts/betfair/`, `pinnacle/`, `polymarket/`, `odds_api/`, `api_football/` | **Create** 5 sports betting modules: schemas.py, examples/, mocks/, venue_manifest entries                                                                                                                                                                                                                      |


### Phase 4 Agent Assignments


| Agent  | Scope                                    | Concrete Tasks                                                                                                                                                                                                                                                                                                                                                                                  |
| ------ | ---------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1**  | Version alignment + CI                   | Create `check_sdk_version_alignment.py`; wire into quality-gates.sh; add ib_insync to [schema-validation] if UTEI uses it                                                                                                                                                                                                                                                                       |
| **2**  | Interface integration tests              | Create UTEI `test_api_contracts_integration.py`; create URDI `test_api_contracts_integration.py`; follow UTEI_URDI_UDEI_UPI_VERSION_ALIGNMENT_REPORT.md pattern                                                                                                                                                                                                                                 |
| **3**  | CCXT completeness                        | Expand ccxt/schemas.py: CcxtFundingRate, CcxtOpenInterest, CcxtOhlcv, CcxtAggTrade; expand CcxtPosition, CcxtOrder, CcxtMarket, CcxtBalance, CcxtTrade per institutional gaps                                                                                                                                                                                                                   |
| **4**  | Shared schemas                           | Create schemas/accounts.py; extend schemas/derivatives.py with PositionRisk, InsuranceFundState, LongShortRatio, OpenInterestHistory, FundingRateHistory, SettlementEvent, VolSurface, VolSurfaceSlice, VolSmilePoint, VolTermStructure                                                                                                                                                         |
| **5**  | Binance institutional                    | Add BinanceAggTrade, BinanceFundingRateHistory, BinancePremiumIndex, BinanceDepositAddress, BinanceDepositHistory, BinanceWithdrawalHistory, BinanceFeeRate, BinanceInternalTransfer, BinanceSubAccount, BinanceAdlQuantile, BinanceInsuranceFund, BinancePositionRisk, BinancePapiAccount, BinancePapiBalance                                                                                  |
| **6**  | OKX + Bybit institutional                | Add fee, deposit, withdrawal, funding history, risk limit, long/short ratio, portfolio margin, settlement schemas to OKX and Bybit                                                                                                                                                                                                                                                              |
| **7**  | Databento + Hyperliquid + Aster          | Databento: Mbo, Bbo1s, Bbo1m, Cmbp1, Status, Imbalance, Statistics, SystemMsg, ErrorMsg; Hyperliquid: UserState, L2Book, FundingHistoryEntry, Fill, OpenOrder, Candle, VaultDetails, Liquidation, SpotMeta, UserFees, SubAccount; Aster: full Binance Futures-compatible schemas                                                                                                                |
| **8**  | IBKR + DeFi advanced                     | IBKR: ScannerSubscription, Execution, CommissionReport, PnLSingle, PnLHistory, MarketDepth, HistoricalTick, SecDefOptParams, OptionGreeks; Alchemy: Block, Transaction, Log, DecodedLog, GasOracle, NFTMetadata, SimulationResult; The Graph: AaveUserPosition, UniV3Position, CurveGauge, MorphoPosition; DeFi protocol lending: AaveV3ReserveData, CompoundV3UserPosition, MorphoUserPosition |
| **9**  | Sports betting (5 modules)               | Create betfair/, pinnacle/, polymarket/, odds_api/, api_football/ — each with schemas.py, examples/, mocks/, venue_manifest entries per institutional gaps                                                                                                                                                                                                                                      |
| **10** | Deribit + Coinbase + Upbit institutional | Deribit: AccountSummary, PortfolioMarginSummary, VolatilityIndex, FundingRateHistory, SettlementCashFlows, RiskLimit; Coinbase: FeeSchedule, Order, Fill; Upbit: FeeRate; extend remaining CEX venues with deposit/withdrawal/transfer lifecycle                                                                                                                                                |


### Phase 4 Execution Results


| Agent | Scope                           | Status | Deliverables                                                                                          |
| ----- | ------------------------------- | ------ | ----------------------------------------------------------------------------------------------------- |
| 1     | Version alignment + CI          | Done   | check_sdk_version_alignment.py; quality-gates.sh step; ib_insync in schema-validation                 |
| 2     | Interface integration tests     | Done   | UTEI test_api_contracts_integration.py (3 tests); URDI test_api_contracts_integration.py (2 tests)    |
| 3     | CCXT completeness               | Done   | 15 new schemas; CcxtPosition/Order/Market/Balance/Trade expanded; ENDPOINT_SCHEMA_MAP                 |
| 4     | Shared schemas                  | Done   | schemas/accounts.py; derivatives.py extended (PositionRisk, InsuranceFundState, LongShortRatio, etc.) |
| 5     | Binance institutional           | Done   | 14 schemas (AggTrade, FundingRateHistory, DepositAddress, FeeRate, PapiAccount, etc.)                 |
| 6     | OKX + Bybit institutional       | Done   | OKX 12 schemas; Bybit 10 schemas; fee, deposit, funding, risk limit, portfolio margin                 |
| 7     | Databento + Hyperliquid + Aster | Done   | Databento 9; Hyperliquid 12; Aster 17 schemas                                                         |
| 8     | IBKR + DeFi advanced            | Done   | IBKR 14; Alchemy 11; The Graph 10; DeFi lending 9 schemas                                             |
| 9     | Sports betting                  | Done   | betfair, pinnacle, polymarket, odds_api, api_football (5 modules, venue_manifest)                     |
| 10    | Deribit + Coinbase + Upbit      | Done   | Deribit 7; Coinbase 3; Upbit 3 schemas                                                                |


---

## Phase 5: VCR, CI Wiring, Docs Consolidation (10 Agents)

**Scope:** VCR endpoints, ENDPOINT_SCHEMA_MAP, SCHEMA_VERSIONS.md, interface CI wiring (all interfaces), documentation consolidation, codex/cursor rules updates.

### Phase 5 Agent Assignments


| Agent  | Scope                                 | Tasks                                                                                                                                                                 |
| ------ | ------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1**  | VCR endpoints                         | Add betfair, pinnacle, polymarket, odds_api, api_football to vcr_endpoints.py; create cassette placeholders; update record_vcr_cassettes.py if needed                 |
| **2**  | ENDPOINT_SCHEMA_MAP + SCHEMA_VERSIONS | Audit Phase 4 schemas; add any missing ENDPOINT_SCHEMA_MAP entries; add sports venues + new CEX/DeFi venues to SCHEMA_VERSIONS.md                                     |
| **3**  | check_sdk_version_alignment.py        | Extend script to accept --interface-path for self-check; add all api-contracts consumers (20+ repos) to INTERFACES list                                               |
| **4**  | Interface quality gates (batch 1)     | Add SDK alignment step to UMI, UTEI, URDI, unified-cloud-interface, unified-trading-services quality-gates.sh                                                         |
| **5**  | Interface quality gates (batch 2)     | Add SDK alignment step to market-tick-data-handler, instruments-service, execution-service, strategy-service, pnl-attribution-service                                |
| **6**  | Interface quality gates (batch 3)     | Add SDK alignment step to ml-inference-service, ml-training-service, features-*, position-balance-monitor, risk-and-exposure, market-data-processing, alerting-service |
| **7**  | api-contracts docs consolidation      | Create API_CONTRACTS_CHAIN_OF_EVENTS.md; consolidate SCHEMA_VALIDATION_SUMMARY, README, collected_responses flow; remove/archive obsolete docs                        |
| **8**  | Interface docs consolidation          | Create INTERFACE_API_CONTRACTS_FLOW.md in UMI, UTEI, URDI; document chain: config → SDK → api-contracts validation → adapter; remove obsolete methods/docs            |
| **9**  | Codex docs updates                    | Update 02-data, 05-infrastructure/unified-libraries, 06-coding-standards for api-contracts chain, schema-validation, version alignment; add API contracts section     |
| **10** | Cursor rules updates                  | Add api-contracts-version-alignment.mdc; update search-before-implementing, external-import-standards; sync to unified-trading-pm/cursor-rules/                       |


### Concrete File Edits (Phase 5)


| File                                                | Edit                                                                                      |
| --------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| api_contracts/vcr_endpoints.py                      | Add betfair, pinnacle, polymarket, odds_api, api_football to VCR_ENDPOINTS                |
| api_contracts/endpoints.py                          | Audit ENDPOINT_SCHEMA_MAP for Phase 4 schemas; add any missing                            |
| SCHEMA_VERSIONS.md                                  | Add sports venues, Deribit, Hyperliquid, Aster, DeFi protocol lending                     |
| scripts/check_sdk_version_alignment.py              | Add --interface-path; extend INTERFACES to all 20+ api-contracts consumers                |
| **/quality-gates.sh (all interfaces)                | Add step: run check_sdk_version_alignment.py --interface-path . when api-contracts is dep |
| api-contracts/docs/API_CONTRACTS_CHAIN_OF_EVENTS.md | Create: chain from config → SDK → schema validation → adapter                             |
| unified-trading-codex/                              | Add API contracts section; update dependency-matrix, schema governance                    |
| .cursor/rules/api-contracts-version-alignment.mdc   | Create; sync to unified-trading-pm/cursor-rules/                                          |


### Phase 5 Execution Results


| Agent | Scope                                 | Status | Deliverables                                                                                                                                   |
| ----- | ------------------------------------- | ------ | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| 1     | VCR endpoints                         | Done   | betfair [], pinnacle, polymarket, odds_api, api_football; auth_query_param; record_vcr_cassettes + test_vcr_replay updates                     |
| 2     | ENDPOINT_SCHEMA_MAP + SCHEMA_VERSIONS | Done   | Sports, Deribit, Hyperliquid, Aster, DeFi sections; BASE_URLS; ENDPOINT_SCHEMA_MAP entries                                                     |
| 3     | check_sdk_version_alignment           | Done   | --interface-path; INTERFACES extended to 20 repos; api-contracts version check for all consumers                                               |
| 4     | Quality gates batch 1                 | Done   | UMI, UTEI, URDI, unified-cloud-interface, unified-trading-services                                                                             |
| 5     | Quality gates batch 2                 | Done   | market-tick-data-handler, instruments-service, execution-service, strategy-service, pnl-attribution-service                                   |
| 6     | Quality gates batch 3                 | Done   | ml-inference, ml-training, features-*, position-balance-monitor, risk-and-exposure, market-data-processing, alerting-service                    |
| 7     | api-contracts docs                    | Done   | docs/API_CONTRACTS_CHAIN_OF_EVENTS.md; README consolidated; SCHEMA_VALIDATION_SUMMARY.md removed                                               |
| 8     | Interface docs                        | Done   | UMI, UTEI, URDI docs/INTERFACE_API_CONTRACTS_FLOW.md; CONSOLIDATION_COMPLETE.md, TRADFI_ADAPTERS_CONSOLIDATED.md removed                       |
| 9     | Codex docs                            | Done   | 02-data/api-contracts-chain.md; schema-governance, dependency-matrix, 06-coding-standards updates                                              |
| 10    | Cursor rules                          | Done   | api-contracts-version-alignment.mdc; search-before-implementing, external-import-standards updates; synced to unified-trading-pm/cursor-rules/ |


---

## Phase 6: Discovery, Inventory, Full Integration (10 Agents)

**Sources:** [api_contracts_—_full_cross-venue_institutional_expansion_569b9380.plan.md](/.cursor/plans/api_contracts_—_full_cross-venue_institutional_expansion_569b9380.plan.md), [api_contracts_institutional_gaps_518ca0e3.plan.md](/.cursor/plans/api_contracts_institutional_gaps_518ca0e3.plan.md). **Goal:** Full understanding of what's available; integrate into structure. Use Context7 for verification.

### Remaining Gaps (from Full Expansion Plan)


| Category           | Status  | Remaining                                                                                                                                                                                                                                      |
| ------------------ | ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CCXT               | ~70%    | CcxtBorrowRate, CcxtBorrowInterest, CcxtMarginAdjustment, CcxtInsuranceFund, CcxtLiquidation, CcxtSettlementHistory, CcxtSubaccount, CcxtCurrency, CcxtOption, CcxtFees, CcxtVolatilityHistory, CcxtLeverage, CcxtMarginMode, CcxtPositionMode |
| Binance            | Done    | BinanceIsolatedMarginBorrowRate, BinanceCrossMarginData, BinanceIncome, BinanceMarkPriceKline, BinanceIndexPriceKline, BinanceMyTrades, BinanceDeliveryHistory                                                                                 |
| Bybit              | Done    | BybitUnifiedAccount (REST equivalent of WalletWS)                                                                                                                                                                                              |
| OKX                | Done    | OKXOptionSummary (vol surface), OKXOptionTicker                                                                                                                                                                                                |
| IBKR               | Partial | IBKRFAProfile, IBKRFAAccountGroup, IBKRFAAllocationProfile, IBKRAccountUpdateMulti, IBKRNewsProvider/Article/HistoricalNews, IBKRFlexQuery, IBKRPortfolioAnalytics                                                                             |
| Cross-venue matrix | Missing | Document CCXT vs direct; what normalizes downstream; venue-unique exposure                                                                                                                                                                     |


### Phase 6 Agent Assignments


| Agent  | Scope                                    | Tasks                                                                                                                                                                                                                          |
| ------ | ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **1**  | Context7 CCXT discovery                  | Use Context7 to fetch CCXT manual; list all fetch_* methods; compare vs our schemas; document missing (BorrowRate, InsuranceFund, Liquidation, Subaccount, Currency, Option, etc.); add any high-value missing schemas         |
| **2**  | Context7 Binance/Bybit/OKX discovery     | Use Context7 to fetch Binance, Bybit, OKX API docs; verify we have schemas for all endpoints we claim; add BinanceMarkPriceKline, BinanceIndexPriceKline, BinanceMyTrades, BinanceDeliveryHistory, BinanceIncome if missing    |
| **3**  | Context7 Databento/Tardis discovery      | Use Context7 to fetch Databento, Tardis API docs; verify schema coverage; add any missing (book_snapshot_25, incremental_book_L2, quotes for Tardis)                                                                           |
| **4**  | Context7 DeFi/MEV discovery              | Use Context7 to fetch Alchemy, The Graph, Flashbots, MEV Blocker, bloXroute docs; verify we have schemas for all endpoints; document gaps                                                                                      |
| **5**  | Context7 Sports + other venues discovery | Use Context7 to fetch Betfair, Pinnacle, Polymarket, Odds API, API-Football; check polymarket_and_kalishi.md for Kalishi; document any additional sports/prediction APIs                                                       |
| **6**  | API_CONTRACTS_AVAILABLE_INVENTORY.md     | Create comprehensive inventory: all external APIs (CeFi, TradFi, DeFi, Sports, Cloud); what we have schemas for; what we don't; what's planned; CCXT vs direct mapping                                                         |
| **7**  | Cross-venue matrix + CCXT vs direct      | Create docs/CROSS_VENUE_MATRIX.md: what comes via CCXT vs direct; what normalizes downstream; what each venue uniquely exposes                                                                                                 |
| **8**  | Remaining CCXT schemas                   | Add CcxtBorrowRate, CcxtBorrowInterest, CcxtMarginAdjustment, CcxtInsuranceFund, CcxtLiquidation, CcxtSettlementHistory, CcxtSubaccount, CcxtCurrency, CcxtOption, CcxtFees; expand CcxtPosition with marginMode, positionMode |
| **9**  | Remaining Binance/IBKR schemas           | Add BinanceMarkPriceKline, BinanceIndexPriceKline, BinanceMyTrades, BinanceDeliveryHistory, BinanceIncome; add IBKR FA/News/FlexQuery/PortfolioAnalytics if feasible                                                           |
| **10** | Structure integration                    | Update ENDPOINT_SCHEMA_MAP, SCHEMA_VERSIONS.md, venue_manifest, VCR_ENDPOINTS for all new schemas; ensure docs/INDEX.md reflects inventory                                                                                     |


### Deliverables

- **api-contracts/docs/API_CONTRACTS_AVAILABLE_INVENTORY.md** — Full inventory of available APIs, schema coverage, gaps
- **api-contracts/docs/CROSS_VENUE_MATRIX.md** — CCXT vs direct, normalization flow, venue-unique exposure
- **Remaining schemas** — CCXT (BorrowRate, InsuranceFund, etc.), Binance (MarkPriceKline, MyTrades, etc.), IBKR (FA, News, etc.)
- **Plan alignment** — Mark full expansion plan todos as completed or document remaining; sync institutional gaps plan

### Phase 6 Execution Results


| Agent | Scope                                | Status | Deliverables                                                                                                                                                                                                               |
| ----- | ------------------------------------ | ------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1     | Context7 CCXT                        | Done   | CcxtBorrowRate, CcxtInsuranceFund, CcxtLiquidation, CcxtSubaccount, CcxtCurrency, CcxtCurrencyNetwork; ENDPOINT_SCHEMA_MAP, venue_manifest                                                                                 |
| 2     | Context7 Binance/Bybit/OKX           | Done   | BinanceMarkPriceKline, BinanceIndexPriceKline, BinanceMyTrades, BinanceDeliveryHistory, BinanceIncome; BybitMarkPriceKline, BybitIndexPriceKline; OKXMarkPriceKline, OKXIndexPriceKline, OKXOptionSummary, OKXOptionTicker |
| 3     | Context7 Databento/Tardis            | Done   | TardisBookSnapshot25, TardisIncrementalBookL2, TardisQuotes; Databento system_msg, error_msg in ENDPOINT_SCHEMA_MAP                                                                                                        |
| 4     | Context7 DeFi/MEV                    | Done   | FlashbotsCancelPrivateTransactionParams; AlchemyWebhookSubscription, AlchemyWebhookCreateParams; SCHEMA_VERSIONS.md DeFi/MEV inventory                                                                                     |
| 5     | Context7 Sports                      | Done   | Sports API inventory; Kalshi, FootyStats, OpticOdds, Sportmonks, BetsAPI documented; Kalshi recommended P0                                                                                                                 |
| 6     | API_CONTRACTS_AVAILABLE_INVENTORY.md | Done   | CeFi, TradFi, DeFi, Sports, Cloud; CCXT vs direct; Planned/not contracted                                                                                                                                                  |
| 7     | CROSS_VENUE_MATRIX.md                | Done   | CCXT vs direct; normalization flow; venue-unique exposure; data source→venue; schema coverage matrix                                                                                                                       |
| 8     | Remaining CCXT schemas               | Done   | CcxtBorrowInterest, CcxtMarginAdjustment, CcxtSettlementHistory, CcxtOption, CcxtFees, CcxtVolatilityHistory, CcxtLeverage, CcxtMarginMode, CcxtPositionMode; CcxtPosition expanded                                        |
| 9     | Remaining Binance/IBKR               | Done   | Binance schemas verified; IBKRAccountUpdateMulti added; FA/News/Flex/PortfolioAnalytics deferred                                                                                                                           |
| 10    | Structure integration                | Done   | venue_manifest updated; INDEX.md links; full expansion plan todos marked; 295+ ENDPOINT_SCHEMA_MAP entries resolve                                                                                                         |


---

## What's Left Not Covered (Post-Phase 6)

- **Kalshi** — P0 recommended; add api_contracts/kalshi/ for cross-venue prediction-market arb
- **FootyStats, OpticOdds, Sportmonks, BetsAPI** — Sports data APIs; add if sports-betting-services needs shared schemas
- **Polymarket Gamma API** — Extend Polymarket schemas for Gamma metadata (event, neg-risk, tags)
- **Betfair REST** — listMarketCatalogue, placeOrders response schemas; current focus is streaming
- **API-Football odds** — ApiFootballOdds for /odds and /odds/live
- **bloXroute** — Ethereum BDN; no schemas
- **IBKR deferred** — FAProfile, News, FlexQuery, PortfolioAnalytics (documented in SCHEMA_VERSIONS.md)
- VCR cassette recording for sports venues (requires API keys)
- Full integration test coverage for new schemas

---

## Typability Goal

- **External:** Every API response/request has a Pydantic schema. No `dict[str, Any]` for external data.
- **Internal:** Config, DataFrames (pandas), domain models — all typed. Use `pandas-stubs`, `numpy.typing` where needed.
- **Dependencies:** Pin versions in SCHEMA_VERSIONS.md; validate schemas against pinned packages.
- **No surprises:** Validation fails at our layer before external SDKs; type checker catches mismatches at edit time.
