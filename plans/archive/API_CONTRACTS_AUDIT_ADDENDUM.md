# api-contracts Audit Addendum: Clarifications and Answers

This addendum addresses follow-up questions from the independent audit. It should be read alongside the main audit plan.

**Task list (DOs):** See `unified-trading-pm/plans/ai/tasks/API_CONTRACTS_TASK_LIST.md` for the full list of actionable tasks derived from this addendum, including sub-agent research areas.

---

## Venue Universe (Scope)

**Venues in scope:**
- **Upbit** — Korean market; add explicitly
- **Coinbase** — Spot, futures (when available); add explicitly
- **Binance** — Three separate endpoints; futures and perps share USD-M:
  - **Spot:** `api.binance.com` — spot pairs only
  - **USD-M (futures + perps):** `fapi.binance.com` — USDT-margined futures and perpetuals (same endpoint)
  - **Coin-M:** `dapi.binance.com` — coin-margined futures
  - api-contracts: `BinanceTicker` supports all three (optional prevClosePrice/bid/ask for spot; optional lastFundingRate for USD-M). Use distinct keys in venue_manifest: `binance-spot`, `binance-usdm`, `binance-coinm`.
- **Bybit** — Unified v5 API (all instrument types in one API). **Validate:** Confirm we always use v5 unified; no legacy split.
- **OKX** — Unified v5 API (`instType` distinguishes SPOT, MARGIN, SWAP, FUTURES, OPTION). **Validate:** Confirm we always use v5 unified; no legacy spot-only or futures-only endpoints.

**Kraken: REMOVED** — Not in our universe. Remove from all codex, api-contracts, UMI, UTEI, URDI, services, UIs, and PM plans.

---

## 1. TradFi: Databento + IBKR Only (No Direct)

**Clarification:** We do not go direct to TradFi venues (CME, NASDAQ, NYSE, etc.). We use:
- **Databento** – market data (trades, OHLCV, MBP-1, definitions)
- **IBKR** – execution (orders, positions, account)

**Schema approach:**
- If Databento normalizes fully across venues → **same schema** (DatabentoOhlcvBar, DatabentoTrade, DatabentoMbp1, etc.) for all TradFi datasets.
- **Venue nuances** (per Context7): CME (GLBX.MDP3) has pre-2017 quirks; NYSE symbology can be incomplete on some dates. Capture these as:
  - Optional fields or `venue_metadata` in schema
  - Or a `DatabentoVenueNotes` / validation rules doc in api-contracts

**Action:** Ensure api-contracts has Databento schemas for all data types (OHLCV-1m, OHLCV-1s, trades, **TBBO**, MBP-1, definition). Add `dataset_id` or `publisher_id` mapping to venue if needed for validation. IBKR schemas already exist (IBKROrder, IBKRPosition, IBKRError).

**TBBO vs MBP-1:** TBBO (Top of Book Bid/Offer) is a distinct Databento schema – trade events plus BBO snapshot before each trade. MBP-1 covers best bid/ask only. execution-service L2_MBP mode expects `tbbo` data. Add `DatabentoTbbo` schema to api-contracts; market-tick-data-handler uses `tbbo` but has no dedicated schema (only MBP-1).

---

## 1a. VIX: Historical vs Live, and Migration from Barchart

**Current state (batch):**
- **Barchart:** Manual CSV dumps from subscription. Schema: `BARCHART_OHLCV_15M_SCHEMA` (Time, Open, High, Low, Last, Volume). Example path: `market-tick-data-handler/data/vix/vix_intraday-15min_historical-data-*.csv`. Works for historical; no API, no live.
- **market-tick-data-handler:** External orchestrator processes Barchart CSVs, converts to parquet, uploads to GCS. Instrument: `CBOE:INDEX:VIX-USD`.

**Gap (live):** We need something to **stream VIX live** – index or futures. Research required as part of api-contracts / data-source shopping list.

**Research targets:**
- **Databento:** VIX options (OPRA) available; VIX index real-time/historical listed "in development" on roadmap. Check when index data ships.
- **IBKR:** TWS API can stream VIX index/futures; requires market data subscription. Add IBKR VIX streaming schemas when we integrate.
- **Others:** CBOE direct, other vendors – document as we find them.

**Action:** (1) Add VIX live-streaming research to api-contracts shopping list; (2) Document Barchart batch schema in api-contracts (migrate from market-tick-data-handler defi_schema.py); (3) When Databento index data or IBKR VIX streaming is chosen, add schemas and migrate away from Barchart manual CSV.

---

## 2. DeFi: Alchemy vs The Graph vs Protocol SDK

| Data Type | Source | Use Case |
|-----------|--------|----------|
| **Subgraph data** (swaps, pools, liquidity) | The Graph | Uniswap, Curve, Balancer – historical/indexed data |
| **RPC / on-chain** (balances, transfers, logs) | Alchemy | Real-time state, contract calls |
| **Protocol rates, oracle prices** | Protocol SDK (direct contract) | AAVE, Compound, Morpho, Lido, EtherFi, Ethena, **Curve, Fluid, Euler** |

**Protocol coverage (shopping list):** Capture the full universe of options – don't limit to what we use today. Fluid and Euler are on different chains (e.g. Fluid Plasma, Euler Plasma) but we can have the functionality. Curve and Compound: use **Context7** to get appropriate SDK options. It's fine to have more routing options (batch or live) than we need in practice; we pick those with the most extensive availability. Cost considerations apply, but this is the playground to see what's there. Document everything as a **shopping list** for what we end up using with the interfaces.

**Execution model (live and batch):**
- **CLOB** (CeFi): Binance, OKX, Deribit, etc. → UTEI
- **DEX** (DeFi): Uniswap, Curve, etc. → UDEI
- **Lending/Staking** (Zero-Alpha): AAVE, Lido, EtherFi, Ethena, etc. → **We still execute live**; no execution algo (no TWAP/VWAP), fills at benchmark
- **Atomic flash loans:** Instadapp, Morpho – we want to execute atomic transactions (borrow → use → repay in one tx)
- **MEV protection:** Basic protection (live and batch) via Flashbots/MEV-Share
- **Batch:** Fill at alpha zero – our simulated matching engine has no mechanism to match the impact of MEV dynamics
- **Live:** We get filled wherever we get filled (no simulated impact; real fills)

**Action:** api-contracts should have schemas for:
- The Graph, Alchemy, Protocol SDK responses (as before)
- **Protocol SDKs:** AAVE, Compound, Morpho, Lido, EtherFi, Ethena, **Curve, Fluid, Euler** – use Context7 for Curve/Compound SDK options; Fluid/Euler are on different chains but we support the functionality
- **Atomic execution:** Instadapp `executeOperation` / `flashLoan` payloads; Morpho `onMorphoFlashLoan` callback payloads
- **MEV:** Flashbots bundle request/response schemas

---

## 3. Flash Loans, Atomic Transactions, and Strategy–Execution Synergy

**Flash loans and atomic transactions are inherently tied.** Flash loans can be used for arbitrage, but for our strategies we use them for **atomic multi-leg transactions** – everything must land in one tx or the whole thing reverts.

**Example flow (leveraged LST staking):**
1. Flash loan borrow
2. Stake → get LST (liquid staking token)
3. Deposit LST on Aave as collateral
4. Borrow against collateral
5. Repay flash loan
6. **Leverage** = 1 / (1 − target_ltv); **capital × leverage** = amount staked; capital locked as collateral (removing it breaches LTV)

**Strategy-service ↔ Execution-service synergy:**
- **Strategy-service** sends the bundled instruction (strategy instruction) – the full multi-leg plan
- **Execution-service** understands the ordering and executes leg by leg, but **atomically** (batch or live)
- **Live:** Uses the right interfaces/SDKs (Instadapp, Morpho, Aave, Lido, etc.) to execute
- **Batch vs Live:** The more similar they look, the better – same code paths, different external interface, different fill (benchmark vs actual trade). One fill is simulated (benchmark); one is real.

---

## 4. MEV Protection: General, Options, and Early Schema Capture

**MEV protection is general** – we always try to avoid MEV extraction (frontrunning, sandwiching). Different options have different cost vs protection tradeoffs.

**MEV protection options (cheaper → more expensive):**

| Option | Cost | Protection | SDK / Endpoint |
|--------|------|------------|----------------|
| **Public mempool** | Free | None | Default RPC |
| **Flashbots Protect** | No upfront fee; gas refunds possible | High | `https://rpc.flashbots.net`, `eth_sendPrivateTransaction` |
| **MEV Blocker** (CoW DAO) | ~0.1 ETH/block + 90% of tx value | High | `https://rpc.mevblocker.io/fast` |
| **Private relay** | Varies | High | Provider-specific |
| **Builder inclusion** (direct) | Bid-based | Highest | `eth_sendBundle`, MEV-Share |

**SDKs and schema sources (get schemas early):**

| Provider | Package | Schema Source | Format |
|----------|---------|---------------|--------|
| **Flashbots** | `flashbots` (Python), `@flashbots/ethers-provider-bundle` (JS) | https://flashbots.github.io/api-specs/latest/openrpc.json | OpenRPC (JSON) |
| **MEV-Share** | `@flashbots/mev-share-client` | https://github.com/flashbots/mev-share/blob/main/specs/bundles/v0.1.md | TypeScript types + Markdown |
| **Flashbots Protect** | - | https://docs.flashbots.net/flashbots-protect/ | `eth_sendPrivateTransaction` JSON-RPC |
| **MEV Blocker** | - | https://docs.cow.fi/mevblocker | RPC docs |
| **Instadapp** | `dsa-connect`, `dsa-sdk` | https://docs.instadapp.io, https://github.com/Instadapp/flashloan-aggregator | Spell/cast patterns, `getBestRoutes` |
| **Morpho** | - | https://docs.morpho.org/morpho/concepts/advanced-concepts/flashloans | Solidity + docs |

**Action:** Reverse-engineer specs for **as many MEV protection options as possible** into api-contracts (and optionally an SDK). Execution config drives which option we use – optionality via config.

**Schema sources to reverse-engineer:**
1. **Flashbots** – OpenRPC `openrpc.json` → `eth_sendBundle`, `eth_callBundle`, `eth_sendPrivateTransaction`
2. **MEV-Share** – v0.1.md → bundle request/response
3. **MEV Blocker** (CoW DAO) – RPC docs
4. **bloXroute** – Protect API
5. **Titan Builder** – `eth_sendPrivateTransaction`, `eth_sendBundle`
6. **Generic private relay** – `eth_sendPrivateTransaction` (common pattern)

**Execution config:** `mev_protection_provider` (or similar) in config selects which provider/endpoint to use. Same execution code path; different RPC endpoint and request shape per provider. Schemas in api-contracts support all options.

**Priority:** Capture all provider schemas early so we have optionality. MEV protection applies to all DeFi execution; we need it before we go live.

---

## 4a. Chain Scope: Ethereum (ERC20) + BTC Only

**For now:** Everything is on **Ethereum (ERC20)** OR **BTC network** – no bridging.

- **Ethereum:** All DeFi (AAVE, Compound, Curve, Fluid, Euler, Lido, Morpho, Instadapp, Uniswap, etc.), flash loans, MEV protection, LST staking
- **BTC:** **Vanilla basis strategy only** for now – no other BTC strategies

**Rationale:** Avoid bridging complexity. Keep scope to two chains with clear separation of use cases.

---

## 4b. Chain-Specific Instruction Types: Strategy-Service ↔ Execution-Service Alignment

**Current gap:** Strategy-service and execution-service are **not** aligned on chain-specific instruction validity. Neither service enforces chain validation – both accept all instruction types regardless of chain. Strategy-service generates instructions; execution-service routes them. If strategy-service emits STAKE for a BTC instrument, execution-service would attempt to route it (and fail at runtime).

**Requirement:** Both services must enforce the same chain × instruction matrix. Strategy-service should not generate invalid combinations; execution-service should reject them at validation.

**Instruction types by chain:**

| Instruction Type | ETH (Ethereum) | BTC |
|------------------|---------------|-----|
| **TRADE** | ✓ (CEX perps, CLOB) | ✓ (vanilla basis: spot + perp) |
| **SWAP** | ✓ (DEX, Uniswap, Curve) | ✓ (possible but low liquidity) |
| **LEND** | ✓ (AAVE, Morpho) | ✓ (possible; yields low – fairly pointless) |
| **BORROW** | ✓ (AAVE, Morpho) | ✓ (possible; yields low) |
| **REPAY** | ✓ | ✓ |
| **STAKE** | ✓ (Lido, EtherFi, LST) | ❌ **Not on BTC** |
| **UNSTAKE** | ✓ | ❌ **Not on BTC** |
| **FLASH_BORROW** | ✓ (Morpho, Instadapp) | ❌ **Not on BTC** |
| **FLASH_REPAY** | ✓ | ❌ **Not on BTC** |
| **ATOMIC** (bundle) | ✓ (Instadapp, Morpho) | ❌ **Not on BTC** |
| **TRANSFER** | ✓ (ERC20, CEX withdrawal) | ✓ (CEX withdrawal only; no bridge) |

**Summary:**
- **ETH:** Full instruction set – staking, atomic, flash loans, LST, swaps, lend, borrow
- **BTC:** TRADE, SWAP, LEND, BORROW, REPAY, TRANSFER only. **No STAKE, UNSTAKE, FLASH_BORROW, FLASH_REPAY, ATOMIC.** Lend/borrow on BTC possible but yields are low.

**Action:** Add chain-aware validation in both strategy-service (instruction generation) and execution-service (instruction validator). Reject STAKE/UNSTAKE/FLASH_*/ATOMIC for BTC-chain instruments. Document in unified-domain-client instruction schema and both service specs.

---

## 4c. On-Chain Transfers: API Contracts Gap

**Current state:** On-chain transfer execution is **not** fully contracted in api-contracts.

| Use Case | What Exists | Missing |
|----------|-------------|---------|
| **Read transfers** | `AlchemyAssetTransfer` (getAssetTransfers) | — |
| **CEX withdrawal** (Binance, OKX, Bybit) | — | Withdrawal request/response schemas |
| **On-chain ERC20 transfer** | — | `eth_sendRawTransaction` / `eth_sendTransaction` request/response |
| **ERC20 `transfer()`** | — | Calldata / ABI schema for `transfer(address,uint256)` |
| **Protocol SDK transfers** (Instadapp, Morpho) | — | `executeOperation` / spell payload schemas for transfer legs |

`COVERAGE_AUDIT.md` notes: **Deposit/Withdrawal – Not covered.**

**Action:** Add to api-contracts: (1) CEX withdrawal schemas (Binance `POST /sapi/v1/capital/withdraw/apply`, OKX, Bybit); (2) JSON-RPC `eth_sendRawTransaction` / `eth_sendTransaction` request/response; (3) ERC20 transfer calldata schema; (4) Instadapp/Morpho transfer-related payload schemas as we integrate.

---

## 4d. Instrument Types: Universe and Venue Nuances

**Instrument types covered:** ETFs, equity, options, futures, perpetuals, spot, index.

**Requirement:** api-contracts must capture the **full universe** of what each venue/data source supports. Nuances across CeFi, TradFi, and DeFi affect request/response shapes, available endpoints, and data types.

| Instrument Type | CeFi | TradFi (Databento/IBKR) | DeFi |
|-----------------|------|-------------------------|------|
| **Spot** | Binance, OKX, Bybit, etc. – ticker, orderbook, trades | Databento: trades, OHLCV, MBP-1, TBBO | Uniswap, Curve – pool, swap, token |
| **Perpetuals** | Binance Futures, OKX SWAP, Bybit, Deribit, Hyperliquid | — | Aster (on-chain perps) |
| **Futures** | Quarterly/dated futures | CME, CBOE via Databento | — |
| **Options** | Deribit, OKX options | CBOE via Databento; IBKR | — |
| **Equity** | — | Databento (XNAS, XNYS); Yahoo; IBKR | — |
| **ETF** | Some CeFi (e.g. Coinbase INDEX) | Databento, IBKR | — |
| **Index** | Some venues (e.g. INDEX-USD) | — | — |

**Venue-specific nuances to incorporate:**
- **OKX:** `instType` = SPOT, MARGIN, SWAP, FUTURES, OPTION – different response shapes per type
- **Binance:** `contractType` = PERPETUAL, CURRENT_QUARTER, NEXT_QUARTER for futures
- **Databento:** `instrument_class` = F (future), O (option), S (stock), etc.; dataset_id varies by publisher
- **IBKR:** Equity vs futures vs options – different contract specs and order types
- **DeFi:** Pool vs A_TOKEN vs DEBT_TOKEN vs LST – protocol-specific schemas

**Action:** Document per-venue instrument-type matrix in api-contracts (e.g. `INSTRUMENT_TYPES_BY_VENUE` or venue_manifest extension). Ensure schemas and examples cover each (venue × instrument_type) combination we use. Use Context7 when adding/updating schemas to match current provider APIs.

**Shopping list philosophy:** Don't limit api-contracts to what we use today. Capture the full universe of venues, data sources, and protocols as a **shopping list**. This extends to **all SDKs** – it's the research pace. We're investigating all possible sets for all possible things. More options for routing data (batch or live) than we need is fine – we pick those with the most extensive availability. Cost and operational considerations apply when we wire interfaces, but api-contracts is the playground: document everything we know is possible. When we integrate, we choose from the list.

---

## 4e. Validation Pipeline: Block Ourselves Before External SDKs Block Us

**Principle:** Strategy-service and execution-service must validate against api-contracts **before** external SDKs fail. If we ask for data, positions, or balances that don't exist for a venue, we should fail at our validation layer – not when the external API returns an error.

**Flow:**
1. **api-contracts** = source of truth for what each venue/data source supports (endpoints, request/response shapes, instrument types, data types)
2. **Strategy-service** generates instructions – validated against: (venue, instrument_type, operation) plausibility from api-contracts
3. **Execution-service** routes and executes – validated against: (venue, instrument_type, operation) plausibility from api-contracts
4. **Interfaces** (UMI, UTEI, UDEI, URDI, UPI) – use api-contracts to parse responses; if schema doesn't match, we catch drift early

**What we block:**
- Asking for **market data** that doesn't exist (e.g. options chain from a venue that only has spot)
- Asking for **positions** that don't exist (e.g. perp positions from a spot-only venue)
- Asking for **account balances** that don't exist (e.g. margin balance from a cash-only account)
- Emitting **instructions** for operations a venue doesn't support

**Action:** Add validation step in strategy-service and execution-service that checks (venue, instrument_type, operation) against api-contracts universe before processing. Same for data requests – validate (venue, data_type) against api-contracts before querying.

---

## 4f. Live Testing Against Actual Returns: Where Do Credentials Live?

**Question:** Integration tests against real API returns need credentials. Should these live in **api-contracts** (with test credentials) or in the **interfaces** (UMI, UTEI, etc.) that use api-contracts?

**Answer: Integration tests in the interfaces.**

| Concern | api-contracts | Interfaces (UMI, UTEI, UDEI, URDI, UPI) |
|---------|---------------|----------------------------------------|
| **Owns** | Schemas only; no HTTP calls | Adapters, HTTP clients, credentials |
| **Credentials** | None – doesn't call APIs | Yes – `get_secret_client()`, env |
| **Unit tests** | Validate against `collected_responses/`, `examples/`, VCR cassettes | Mock responses; validate parsing with api-contracts |
| **Integration tests** | Not applicable – no API calls | Call real API → validate response with api-contracts schema |

**Rationale:**
- api-contracts is a **pure schema library**. It doesn't make HTTP calls. Adding credentials to api-contracts would violate separation of concerns and duplicate credential management.
- The **interfaces** already have the adapter pattern, credentials, and the actual HTTP calls. They are the natural place for "call real API, validate response against schema" tests.
- **api-contracts** validates itself with: (1) `collected_responses/` – JSON saved by `collect_responses.py` (run with credentials in a separate job or manually); (2) `examples/` – hand-curated; (3) VCR cassettes – recorded once, replayed without credentials. No live credentials in api-contracts CI.
- **Interfaces** integration tests: Call real API (with CI secrets) → parse with api-contracts schema → assert validation passes. If it fails, either schema is stale or API changed. Use **Context7** when implementing live request paths to ensure correct client/SDK usage and response handling.

**Recommended flow:**
1. **api-contracts CI:** Unit tests only (examples, collected_responses, VCR). No credentials.
2. **Optional:** Scheduled job (e.g. weekly) runs `collect_responses.py` with credentials → refreshes `collected_responses/` → api-contracts validates. Credentials in that job only.
3. **Interfaces CI:** Integration tests (marked `@pytest.mark.integration`) that call real APIs when credentials available; skip gracefully otherwise. Validate every response with api-contracts.

---

## 5. collected_responses vs generated_schemas vs api_contracts

| Directory | Purpose | Owner |
|-----------|---------|-------|
| **collected_responses/** | Real API responses saved by `scripts/collect_responses.py` | Ephemeral / CI artifact |
| **generated_schemas/** | Auto-generated Pydantic from `scripts/validate_schemas.py --generate-schemas` | Output of validation tool |
| **api_contracts/** | Hand-maintained canonical schemas (SSOT) | Primary source |

**Validation flow:**
1. `collect_responses.py` → fetches live API responses → writes to `collected_responses/{venue}/*.json`
2. `validate_schemas.py` → loads responses → validates against `api_contracts/{venue}/schemas.py` Pydantic models
3. `validate_schemas.py --generate-schemas` → if schema missing, can generate a draft → `generated_schemas/`
4. Human reviews generated schema → promotes to `api_contracts/`

**Viability validation:**
- **Unit tests:** `test_schema_validation.py` – validates `collected_responses` and `examples/*.json` against schemas
- **VCR replay:** `test_vcr_replay.py` – replays HTTP cassettes, validates response body against schema
- **Live (optional):** `LIVE_API_VERIFICATION=1` runs `verify_contracts_vs_reality_live.py`

**Recommendation:** Document this flow in `api-contracts/README.md` and add a `SCHEMA_VALIDATION.md` that explains collected_responses (ephemeral), generated_schemas (draft), api_contracts (canonical).

---

## 6. SCHEMA_VERSIONS.md and Pinned-Version Validation Tests

**Current:** api-contracts has `pydantic>=2.0,<3.0` only. No pins for databento, tardis, ccxt, etc. (api-contracts does not import them).

**Requirement:** Add `SCHEMA_VERSIONS.md` that records which external package versions the schemas were validated against. **We must also test those exact pinned versions against the same schemas** – CI should install the pinned versions and run schema validation to ensure no drift.

**SCHEMA_VERSIONS.md format:**
```markdown
| Venue/Provider | Schema Module | Package / API | Pinned Version | Last Validated |
|----------------|---------------|---------------|---------------|----------------|
| Databento | api_contracts.databento | databento-python | 0.32.x | 2026-02 |
| Tardis | api_contracts.tardis | Tardis HTTP API | v1 | 2026-02 |
| Binance | api_contracts.binance | Binance Futures API | 2024 | 2026-02 |
| CCXT | api_contracts.ccxt | ccxt | 4.x | 2026-02 |
| The Graph | api_contracts.thegraph | GraphQL | - | 2026-02 |
| Flashbots | api_contracts.mev | mev-share / relay | v0.1 | 2026-02 |
```

**Testing requirement:**
- Add optional dev dependency group `[schema-validation]` in api-contracts pyproject.toml with pinned versions (databento==0.32.x, ccxt==4.x, etc.)
- CI job (or quality-gates step): `uv pip install -e ".[schema-validation]"` then run `validate_schemas.py` and/or `test_schema_validation.py` against collected_responses and examples
- If a pinned package changes its response shape, tests fail → we update schemas or bump the pin with explicit review

**Action:** Add `SCHEMA_VERSIONS.md`, optional `[project.optional-dependencies] schema-validation` with pinned versions, and a CI step that validates schemas against those exact versions.

---

## 7. Ownership: Endpoints vs Credentials

| Concern | Owner | Rationale |
|---------|-------|-----------|
| **Endpoint names / base URLs** | api-contracts | Canonical list in `vcr_endpoints.py` or new `endpoints.py`; interfaces import from api-contracts |
| **Credentials (API keys, secrets)** | Interfaces (UMI, UTEI, UDEI, URDI, UPI) | They call `get_secret_client()`; config owns secret names |
| **Secret names** (e.g. `tardis_secret_name`) | unified-config-interface (UnifiedCloudConfig) | Config defines which secret to use; api-contracts `venue_manifest` has `config_secret_field` as documentation only |

**Flow:**
- api-contracts: `VENUE_BASE_URLS = {"binance": "https://fapi.binance.com", ...}` – **owned**
- UMI adapter: `url = api_contracts.endpoints.VENUE_BASE_URLS["binance"] + "/fapi/v1/ticker/24hr"` – uses api-contracts
- UMI adapter: `api_key = get_secret_client(secret_name=config.tardis_secret_name)` – credentials from config/UCS

**Action:** Add `api_contracts/endpoints.py` with base URLs; interfaces refactor to import from there. Credentials stay in interfaces + config. Extend with `ENDPOINT_SCHEMA_MAP` (see Section 8a) so each endpoint/channel maps to its response schema(s).

---

## 8. Error Schemas: Organisation by Venue

**Current state:**
- **Per-venue:** Each venue has `{Venue}Error` in `api_contracts/{venue}/schemas.py` (e.g. BinanceError, OKXError, DeribitError)
- **Central:** `api_contracts/schemas/errors.py` has `VENUE_ERROR_MAP` (code → classification) and `DATABENTO_ERROR_MAP`
- **Shared:** `ErrorAction` enum in `api_contracts/shared/error_action.py`

**Issue:** Errors are split – some logic in central `errors.py`, some in each venue. No single "error response directory" per venue.

**Proposed structure:**
```
api_contracts/
  schemas/
    errors.py           # ErrorAction, VenueErrorClassification, VENUE_ERROR_MAP (aggregate)
  binance/
    schemas.py          # BinanceError (response model) + BinanceError.classify()
    examples/
      error_example.json
  databento/
    schemas.py          # DatabentoError + DATABENTO_ERROR_MAP (or keep in errors.py)
  ...
```

**Recommendation:**
- Keep **response models** (BinanceError, OKXError, etc.) in each venue's `schemas.py` – they mirror API shape
- Keep **classification maps** (VENUE_ERROR_MAP, DATABENTO_ERROR_MAP) in `schemas/errors.py` – single place for retry/reconnect logic
- Add `api_contracts/schemas/errors/` only if we have many cross-cutting error types; otherwise current structure is acceptable
- Ensure every venue in `venue_manifest` has `error_schema_classes` populated and `error_example.json` present

**Messaging/response schemas:** WebSocket message schemas (e.g. OKXOrderUpdateWS, BybitOrderUpdateWS) are in venue schemas. Add a `api_contracts/schemas/websocket.py` section or doc that lists all WS message types by venue for discoverability.

---

## 8a. Exchange State, Data Source State, and Connectivity: Full Surface in api-contracts

**Requirement:** Everything the exchange or data source can respond with that affects our error handling, validation, request/response, connectivity, or WebSocket/FIX behaviour must be known, documented, and schematised in api-contracts. We block surprises by contracting the full surface up front; when surprises occur, we add them.

**Scope:**
- **Health / readiness** – ping, health check, status endpoint responses
- **WebSocket lifecycle** – connect success, disconnect, reconnect, connection error, session expiry
- **WebSocket control** – ping/pong, heartbeat, subscribe ack, unsubscribe ack, error
- **FIX connectivity** – session state, logon/logout, heartbeat, reject, sequence reset
- **REST connectivity** – timeout, connection refused, rate limit, maintenance
- **Error responses** – per-endpoint error shapes (HTTP status, body, codes)

**Endpoint association:** Every schema must be tied to the **endpoint** (or **channel** for WebSocket) that produces it. Example: `GET /fapi/v1/ping` → `BinancePingResponse`; `wss://stream.binance.com/ws` channel `@markPrice` → `BinanceMarkPriceStream`.

**What we need per venue:**

| Category | Examples | Schemas | Endpoint/Channel |
|----------|----------|---------|------------------|
| **Health** | `/ping`, `/time`, `/health` | `{Venue}PingResponse`, `{Venue}TimeResponse` | REST path |
| **WebSocket connect** | `{"op":"subscribe","args":[...]}` ack | `{Venue}WsSubscribeAck`, `{Venue}WsSubscribeError` | WS channel |
| **WebSocket disconnect** | `{"code":1006,"reason":"..."}` | `{Venue}WsCloseEvent` | WS close frame |
| **WebSocket error** | `{"event":"error","message":"..."}` | `{Venue}WsError` | WS message |
| **WebSocket heartbeat** | `ping`/`pong`, `{"event":"heartbeat"}` | `{Venue}WsPing`, `{Venue}WsPong` | WS message |
| **WebSocket reconnect** | `{"code":1000,"reason":"..."}` | `{Venue}WsReconnectHint` | WS close frame |
| **REST error** | `{"code":-1021,"msg":"Timestamp expired"}` | `{Venue}Error` | REST path |
| **Rate limit** | `429`, `Retry-After` | `{Venue}RateLimitError` | REST path |
| **FIX session** | `35=0` (heartbeat), `35=3` (reject) | `{Venue}FixHeartbeat`, `{Venue}FixReject` | FIX msg type |

**Action:**
1. **Audit** each venue’s REST, WebSocket, and FIX docs for: health, ping, error, WebSocket lifecycle, FIX session state.
2. **Add schemas** for every known response shape. Tie each to `(venue, endpoint)` or `(venue, channel)`.
3. **Document** in `api_contracts/venue_manifest.py` or a new `ENDPOINT_SCHEMA_MAP`: `{ (venue, endpoint) → schema_class }`.
4. **Over time:** When new surprises occur (e.g. new error code, new WS close reason), add schema and endpoint mapping; update error classification if needed.

---

## 9. Downstream Usage: Yes, Use api-contracts

**Current consumers:**
- `unified-trade-execution-interface` – CCXT, Deribit, Bybit, OKX schemas
- `instruments-service` – DomainConfigProtocol, CCXT, The Graph
- `market-tick-data-handler` – Databento schemas (but also has duplicate local schemas)
- `strategy-service`, `unified-domain-client` – DomainConfigProtocol, CLOB_VENUES, etc.

**Plan:** Move market-tick-data-handler's `tardis_schema.py`, `databento_schema.py`, `defi_schema.py` into api-contracts. market-tick-data-handler then imports from api-contracts.

**Validation:** After migration, run:
```bash
rg "TARDIS_TRADES_SCHEMA|DATABENTO_OHLCV|AAVE_RATES_SCHEMA" --type py
# Should return 0 outside api-contracts
```

---

## 10. Tardis Schema Migration (P0 – Triple Duplication)

**Current state – three copies of Tardis schemas:**

| Location | Content | Lines |
|----------|---------|-------|
| **api-contracts** `tardis/schemas.py` | TardisExchange, TardisInstrument, TardisTrade, TardisOrderBook, TardisOrderBookLevel, TardisError | 60 |
| **market-tick-data-handler** `schemas/data_providers/tardis_schema.py` | TARDIS_TRADES_SCHEMA, TARDIS_BOOK_SNAPSHOT_5_SCHEMA, TARDIS_LIQUIDATIONS_SCHEMA, TARDIS_DERIVATIVE_TICKER_SCHEMA, TARDIS_OPTIONS_CHAIN_SCHEMA, TARDIS_SCHEMA_MAP, get_tardis_schema(), get_tardis_required_columns() | 415 |
| **unified-trading-services** `models/schemas.py` | ValidationConfig.required_columns_by_data_type (trades, book_snapshot_5, liquidations, derivative_ticker, options_chain + _validated + _nautilus variants) | ~180 |

**Missing in api-contracts:**
- TardisBookSnapshot5 (5-level order book)
- TardisLiquidations
- TardisDerivativeTicker (funding_rate, open_interest, mark_price, etc.)
- TardisOptionsChain (greeks, strike, expiration, etc.)
- Raw column schemas (list[dict]) for DataFrame validation
- get_tardis_schema() / get_tardis_required_columns() helpers

**Config duplication:**
- `market-tick-data-handler` config_dataclasses.MarketDataTypeConfig.tardis_data_types
- Should come from api-contracts (e.g. TARDIS_DATA_TYPES constant)

**Migration steps:**
1. Add to api-contracts: `api_contracts/tardis/raw_schemas.py` – TARDIS_*_SCHEMA, TARDIS_SCHEMA_MAP, get_tardis_schema(), get_tardis_required_columns()
2. Add Pydantic models: TardisBookSnapshot5, TardisLiquidations, TardisDerivativeTicker, TardisOptionsChain (align with raw column names)
3. Add TARDIS_DATA_TYPES constant to api-contracts
4. unified-trading-services: Import required_columns_by_data_type from api-contracts (or build from get_tardis_required_columns)
5. market-tick-data-handler: Delete tardis_schema.py; import from api_contracts.tardis
6. Update venue_manifest for tardis with new response_schema_classes

---

## 11. Summary of Actions

| # | Action |
|---|--------|
| 1 | **Tardis migration (P0):** Add full Tardis schemas to api-contracts; remove from market-tick-data-handler and unified-trading-services |
| 2 | TradFi: Rely on Databento + IBKR; add venue nuance notes (CME, NYSE) to Databento schemas if needed |
| 3 | DeFi: Add protocol SDK schemas (AAVE, Compound, Curve, Fluid, Euler, Lido, Morpho, etc.) from defi_schema.py; use Context7 for Curve/Compound; Fluid/Euler on different chains |
| 4 | **MEV (early):** Reverse-engineer specs for all options (Flashbots, MEV Blocker, bloXroute, Titan, etc.) into api_contracts/mev/; execution config drives which provider to use |
| 5 | **Atomic execution:** Add Morpho/Instadapp payload schemas; strategy-service bundled instruction ↔ execution-service leg-by-leg atomic execution |
| 6 | Document collected_responses / generated_schemas / api_contracts flow in README |
| 7 | Add SCHEMA_VERSIONS.md + pinned [schema-validation] deps + CI tests that validate schemas against exact pinned versions |
| 8 | api-contracts owns endpoints; interfaces own credentials |
| 9 | Reorganise error docs: per-venue response models stay; central classification in errors.py |
| 10 | Migrate Databento + DeFi + Barchart schemas from market-tick-data-handler to api-contracts (BARCHART_OHLCV_15M_SCHEMA for VIX) |
| 11 | **Chain scope:** Ethereum (ERC20) + BTC only; BTC = vanilla basis strategy only; no bridging |
| 12 | **Databento TBBO:** Add `DatabentoTbbo` schema (distinct from MBP-1); L2_MBP mode expects tbbo |
| 13 | **On-chain transfers:** Add CEX withdrawal schemas, eth_sendRawTransaction/eth_sendTransaction, ERC20 transfer calldata, protocol SDK transfer payloads |
| 14 | **Chain-instruction alignment:** Add chain-aware validation in strategy-service + execution-service; reject STAKE/UNSTAKE/FLASH_*/ATOMIC for BTC |
| 15 | **Instrument types:** Document per-venue matrix (ETFs, equity, options, futures, perpetuals, spot, index); incorporate CeFi/TradFi/DeFi nuances into schemas |
| 16 | **Validation pipeline:** Add (venue, instrument_type, operation) plausibility checks in strategy-service and execution-service using api-contracts universe |
| 17 | **Live testing:** Integration tests in interfaces (UMI, UTEI, etc.) with credentials; api-contracts uses collected_responses/examples/VCR only; use Context7 for live paths |
| 18 | **Exchange/data-source state:** Add schemas for health, ping, WebSocket lifecycle (connect/disconnect/error/heartbeat), FIX session state, REST errors; tie each schema to (venue, endpoint) or (venue, channel); add ENDPOINT_SCHEMA_MAP |
| 19 | **Shopping list:** Document full universe of venues/protocols/data sources in api-contracts; don't limit to current usage; pick best options when wiring interfaces |
| 20 | **VIX live streaming research:** Identify where we can stream VIX live (index or futures); research Databento (index in dev?), IBKR (TWS), others; migrate from Barchart manual CSV when better option available |
| 21 | **Cloud SDKs (GCP):** Add schemas for VM creation, Cloud Run, GCS, BigQuery (external tables), quotas; sync and async pass per endpoint |
| 22 | **Cloud SDKs (AWS):** Add schemas for EC2, ECS/Lambda, S3, Glue, Hive, external tables, quotas; sync and async pass per endpoint |
| 23 | **Quota handling:** Add QuotaBrokerClient and quota-exceeded message schemas from UTD v3; incorporate into api-contracts |

---

## 12. Full Surface Scope: Feed, Orders, Positions, Reference, Status, Errors

**Requirement:** api-contracts must cover **all** types of possible interactions with external APIs, not just market data. Document every category below with schemas for request/response, sync/async, and endpoint association.

| Category | Description | Examples |
|----------|-------------|----------|
| **Feed** | Market data streams (trades, OHLCV, orderbook, ticker) | Databento, Tardis, exchange WebSocket streams |
| **Orders** | Order submission, ack, fill, cancel, status | Binance, OKX, IBKR, Deribit, DeFi protocols |
| **Positions** | Open positions, PnL, margin | CeFi, IBKR, DeFi lending |
| **Reference data** | Instrument definitions, symbology, metadata | Databento, Tardis, CCXT, IBKR |
| **Exchange data status** | Health, ping, availability | REST `/ping`, `/time`, `/health` |
| **Market feed status** | WebSocket lifecycle, FIX session state | Connect, disconnect, heartbeat, reconnect |
| **Error handling** | Per-endpoint errors, rate limits, classification | ErrorAction, VENUE_ERROR_MAP |

**Action:** Audit each venue in api-contracts for coverage of all seven categories. Add missing schemas. Tie each to (venue, endpoint).

---

## 13. Cloud SDKs: GCP and AWS

**Requirement:** Add api-contracts for Google Cloud SDK and AWS SDK operations – as much as humanly possible. Include sync and async pass for different endpoints.

**GCP (Google Cloud):**

| Service | Operations | Schemas | Sync/Async |
|---------|-------------|---------|------------|
| **Compute Engine** | VM create, list, delete, instance config | GcpComputeInstanceCreate, GcpComputeInstanceList, etc. | Both |
| **Cloud Run** | Deploy, revision, service status | GcpCloudRunService, GcpCloudRunRevision | Both |
| **Cloud Storage (GCS)** | Upload, download, list, delete, blob metadata | GcsBlob, GcsBucket, GcsUploadResponse | Both |
| **BigQuery** | Query, load, external tables | BqQueryResult, BqExternalTableConfig | Both |
| **Quotas** | Quota get, usage | GcpQuotaUsage, GcpQuotaExceeded | Both |

**AWS:**

| Service | Operations | Schemas | Sync/Async |
|---------|-------------|---------|------------|
| **EC2** | RunInstances, DescribeInstances, TerminateInstances | AwsEc2Instance, AwsEc2RunInstancesResponse | Both |
| **ECS / Lambda** | Cloud Run equivalent | AwsEcsTask, AwsLambdaInvocation | Both |
| **S3** | put_object, get_object, list_objects, delete | AwsS3Object, AwsS3ListResponse | Both |
| **Glue / Athena** | Hive, external tables | AwsGlueTable, AwsAthenaQueryResult | Both |
| **Service Quotas** | Quota get, request increase | AwsServiceQuota, AwsQuotaExceeded | Both |

**Action:** Add `api_contracts/cloud_sdks/gcp.py` and `api_contracts/cloud_sdks/aws.py` (or extend existing) with Pydantic schemas for each operation. Document sync vs async client usage per endpoint. Use Context7 for current SDK versions.

---

## 14. Quota Handling (Unified Trading Deployment v3)

**Current state:** UTD v3 uses a quota broker for VM creation, Cloud Run, and orchestration. Messages are passed around when quotas are exceeded.

**Quota broker flow:**
- `QuotaBrokerClient.acquire(quota_shape, batch_size)` → `QuotaBrokerAcquireResult` (granted, lease_id, reason, retry_after_seconds)
- `QuotaBrokerClient.release(lease_id)` → release lease
- `vm_quota_shape_from_compute_config(config)` → quota shape dict
- Worker shards: `quota_denied_reason`, `quota_retry_after_seconds`, `quota_lease_id`

**GCP quotas:** `WRITE_QUOTA_PER_MINUTE`, `WRITE_QUOTA_BUFFER` for Compute Engine write operations.

**Action:** Add to api-contracts:
1. `QuotaBrokerAcquireRequest` / `QuotaBrokerAcquireResult` (or equivalent)
2. `QuotaBrokerReleaseRequest`
3. `QuotaExceededMessage` (reason, retry_after_seconds, lease_id)
4. `VmQuotaShape` (from vm_quota_shape_from_compute_config)
5. GCP/AWS quota API response schemas (Cloud Quotas API, Service Quotas API)

**Reference:** `unified-trading-deployment-v3/deployment/quota_broker_client.py`, `api/utils/quota_requirements.py`, `deployment/worker_manager.py`

---

## 15. Sub-Agent Investigation Findings (2026-02-26)

### 15.1 Market Data / Feed

- **Databento:** Tbbo, Mbp10, raw schemas, helpers
- **Tardis:** BookSnapshot5, Liquidations, DerivativeTicker, OptionsChain, raw schemas
- **Barchart:** BarchartOhlcv15m
- **Yahoo:** Ohlcv24h, Splits, Dividends

### 15.2 Orders / Positions

- **CEX:** Order submit/ack/cancel, position query, margin balance, realized PnL
- **Venues:** Binance-spot, Binance-futures, OKX, Bybit, Upbit, Coinbase
- **DeFi:** Swap/lend/borrow request/response, flash loans, atomic bundles

### 15.3 Reference Data

- INSTRUMENT_TYPES_BY_VENUE
- Symbology, ETF, Index, Options chain, Greeks
- Cross-venue type mapping (OKX SWAP = Binance PERPETUAL)

### 15.4 Exchange Status

- REST health, WebSocket lifecycle, FIX, ENDPOINT_SCHEMA_MAP
- ~50+ missing schemas across venues

### 15.5 Error Handling

- VENUE_ERROR_MAP expansion (13 venues missing)
- Rate limit (429), classify(), endpoint mapping

### 15.6 Cloud SDKs (GCP)

- Compute Engine: VM create, list, delete, instance config
- Cloud Run: Deploy, revision, service status
- GCS: Upload, download, list, delete, blob metadata
- BigQuery: Query, load, external tables
- Quotas: Quota get, usage
- Sync and async pass per endpoint

### 15.7 Cloud SDKs (AWS)

- EC2: RunInstances, DescribeInstances, TerminateInstances
- ECS / Lambda: Cloud Run equivalent
- S3: put_object, get_object, list_objects, delete
- Glue / Athena: Hive, external tables
- Service Quotas: Quota get, request increase
- Sync and async pass per endpoint

### 15.8 Quota Handling

- QuotaBrokerClient.acquire/release
- QuotaExceededMessage (reason, retry_after_seconds, lease_id)
- VmQuotaShape from vm_quota_shape_from_compute_config
- GCP/AWS quota API response schemas

### 15.9 DeFi / MEV

- Protocol SDKs: AAVE, Compound, Morpho, Lido, Curve, Fluid, Euler
- Atomic execution: Instadapp, Morpho flash loans
- MEV protection: Flashbots, MEV Blocker, bloXroute, Titan — reverse-engineer specs into api_contracts/mev/
- CEX withdrawal schemas (Binance, OKX, Bybit, Upbit, Coinbase)

### 15.10 TradFi / VIX

- Databento: OHLCV, trades, TBBO, MBP-1, definitions
- IBKR: Orders, positions, account
- VIX: Barchart batch schema; research live streaming (Databento index in dev, IBKR TWS)
