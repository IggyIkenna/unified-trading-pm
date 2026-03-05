# API Contracts Comprehensive Task List (DOs)

**Source:** `API_CONTRACTS_AUDIT_ADDENDUM.md`
**Goal:** Fill out api-contracts to a verbose understanding of what's available and all possible interactions with external APIs.
**Scope:** Market data, feed, orders, positions, reference data, exchange status, market feed status, error handling, cloud SDKs (GCP, AWS), quotas.

---

## 1. Market Data / Feed

| DO  | Priority | Description                                                                                                  | Venues / Sources |
| --- | -------- | ------------------------------------------------------------------------------------------------------------ | ---------------- |
| 1.1 | P1       | Add Databento schemas: OHLCV-1m, OHLCV-1s, trades, TBBO, MBP-1, MBP-5, MBP-10, definition                    | Databento        |
| 1.2 | P1       | Add DatabentoTbbo schema (distinct from MBP-1)                                                               | Databento        |
| 1.3 | P1       | Migrate Tardis full schemas: BookSnapshot5, Liquidations, DerivativeTicker, OptionsChain, raw column schemas | Tardis           |
| 1.4 | P1       | Migrate Barchart BARCHART_OHLCV_15M_SCHEMA to api-contracts                                                  | Barchart         |
| 1.5 | P2       | Add Yahoo Finance schemas (OHLCV, ticker, splits, dividends)                                                 | Yahoo Finance    |
| 1.6 | P1       | Document per-venue data types: trades, OHLCV, orderbook, ticker, funding, liquidations                       | All venues       |

---

## 2. Orders / Positions

| DO  | Priority | Description                                                                                                                                  | Venues / Sources                                                                       |
| --- | -------- | -------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| 2.1 | P0       | Add CEX order schemas: submit, ack, fill, cancel, status (e.g. BinanceOrderSubmitRequest, BinanceOrderSubmitResponse, OKXOrderSubmitRequest) | Binance-spot, Binance-usdm (futures+perps), Binance-coinm, OKX, Bybit, Upbit, Coinbase |
| 2.2 | P1       | Add CEX position schemas: open position, PnL, margin (e.g. BinancePosition, OKXPosition)                                                     | Binance-spot, Binance-usdm, Binance-coinm, OKX, Bybit                                  |
| 2.3 | P1       | Add IBKR order/position schemas (TWS/ib_insync)                                                                                              | IBKR                                                                                   |
| 2.4 | P2       | Add DeFi order/position schemas (DEX, lending)                                                                                               | Uniswap, AAVE, Morpho                                                                  |
| 2.5 | P2       | Add CEX withdrawal schemas (Binance-spot, Binance-usdm, Binance-coinm, OKX, Bybit, Upbit, Coinbase)                                          | CeFi                                                                                   |

---

## 3. Reference Data

| DO  | Priority | Description                                                                                    | Venues / Sources              |
| --- | -------- | ---------------------------------------------------------------------------------------------- | ----------------------------- |
| 3.1 | P0       | Add instrument definition schemas per venue                                                    | Databento, Tardis, CCXT, IBKR |
| 3.2 | P1       | Add INSTRUMENT_TYPES_BY_VENUE matrix (ETFs, equity, options, futures, perpetuals, spot, index) | All                           |
| 3.3 | P2       | Add symbology/metadata schemas                                                                 | Databento, Tardis             |
| 3.4 | P2       | Add venue-specific contract specs (tick size, lot size, expiry)                                | Per venue                     |

---

## 4. Exchange Status / Market Feed Status

| DO  | Priority | Description                                                                            | Venues / Sources                                                                |
| --- | -------- | -------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| 4.1 | P1       | Add health/ping schemas per venue                                                      | All REST venues                                                                 |
| 4.2 | P1       | Add WebSocket lifecycle schemas: connect, disconnect, reconnect, error, session expiry | All WS venues                                                                   |
| 4.3 | P1       | Add WebSocket control schemas: ping/pong, heartbeat, subscribe ack, unsubscribe ack    | Binance-spot, Binance-usdm, Binance-coinm, OKX, Bybit, Deribit, Upbit, Coinbase |
| 4.4 | P2       | Add FIX session schemas: logon, logout, heartbeat, reject, sequence reset              | OKX, Bybit, Upbit                                                               |
| 4.5 | P1       | Add ENDPOINT_SCHEMA_MAP: (venue, endpoint) → schema_class                              | All                                                                             |
| 4.6 | P2       | Add exchange data status / market feed status schemas                                  | Per venue                                                                       |

---

## 5. Error Handling

| DO  | Priority | Description                                                           | Venues / Sources  |
| --- | -------- | --------------------------------------------------------------------- | ----------------- |
| 5.1 | P1       | Add per-endpoint error response schemas (e.g. BinanceError, OKXError) | All venues        |
| 5.2 | P1       | Add rate limit schemas (429, Retry-After)                             | All REST venues   |
| 5.3 | P1       | Add WebSocket error/close schemas                                     | All WS venues     |
| 5.4 | P1       | Consolidate VENUE_ERROR_MAP with ErrorAction classification           | Central errors.py |
| 5.5 | P2       | Add error_example.json per venue                                      | All               |

---

## 6. Cloud SDKs – GCP

| DO  | Priority | Description                                                              | API / Service         |
| --- | -------- | ------------------------------------------------------------------------ | --------------------- |
| 6.1 | P2       | Add GCP Compute Engine schemas: VM create, list, delete, instance config | google-cloud-compute  |
| 6.2 | P2       | Add Cloud Run schemas: deploy, revision, service status                  | google-cloud-run      |
| 6.3 | P2       | Add GCS schemas: upload, download, list, delete, blob metadata           | google-cloud-storage  |
| 6.4 | P2       | Add BigQuery schemas: query, load, external tables                       | google-cloud-bigquery |
| 6.5 | P2       | Add GCP quota/usage schemas (compute.instances, etc.)                    | Cloud Quotas API      |
| 6.6 | P2       | Document sync vs async pass for each GCP client                          | Per client            |

---

## 7. Cloud SDKs – AWS

| DO  | Priority | Description                                                          | API / Service        |
| --- | -------- | -------------------------------------------------------------------- | -------------------- |
| 7.1 | P2       | Add EC2 schemas: RunInstances, DescribeInstances, TerminateInstances | boto3 ec2            |
| 7.2 | P2       | Add ECS/Lambda schemas (Cloud Run equivalent)                        | boto3 ecs, lambda    |
| 7.3 | P2       | Add S3 schemas: put_object, get_object, list_objects, delete         | boto3 s3             |
| 7.4 | P2       | Add Glue/Athena schemas (Hive, external tables)                      | boto3 glue, athena   |
| 7.5 | P2       | Add AWS quota/usage schemas (Service Quotas API)                     | boto3 service-quotas |
| 7.6 | P2       | Document sync vs async pass for each AWS client                      | Per client           |

---

## 8. Quota Handling (UTD v3)

| DO  | Priority | Description                                                             | Source                        |
| --- | -------- | ----------------------------------------------------------------------- | ----------------------------- |
| 8.1 | P1       | Add QuotaBrokerClient request/response schemas (acquire, release)       | unified-trading-deployment-v3 |
| 8.2 | P1       | Add quota-exceeded message schemas (reason, retry_after_seconds)        | UTD v3 worker_manager         |
| 8.3 | P1       | Add vm_quota_shape_from_compute_config output schema                    | UTD v3 quota_requirements     |
| 8.4 | P1       | Add GCP write quota (WRITE_QUOTA_PER_MINUTE, WRITE_QUOTA_BUFFER) schema | UTD v3 config                 |
| 8.5 | P2       | Document quota broker API contract for api-contracts                    | quota_broker_client           |

---

## 9. DeFi / MEV / Transfers

| DO  | Priority | Description                                                                                           | Sources            |
| --- | -------- | ----------------------------------------------------------------------------------------------------- | ------------------ |
| 9.1 | P2       | Add MEV schemas: Flashbots, MEV Blocker, bloXroute, Titan, eth_sendBundle, eth_sendPrivateTransaction | api_contracts/mev/ |
| 9.2 | P2       | Add protocol SDK schemas: AAVE, Compound, Curve, Fluid, Euler, Morpho, Lido                           | Protocol SDKs      |
| 9.3 | P2       | Add Instadapp/Morpho atomic execution payload schemas                                                 | Instadapp, Morpho  |
| 9.4 | P2       | Add eth_sendRawTransaction, eth_sendTransaction, ERC20 transfer calldata                              | Alchemy/RPC        |
| 9.5 | P2       | Add AlchemyAssetTransfer (read) – already exists; add execution schemas                               | Alchemy            |

---

## 10. TradFi / VIX

| DO   | Priority | Description                                                                | Sources   |
| ---- | -------- | -------------------------------------------------------------------------- | --------- |
| 11.1 | P2       | Research VIX live streaming: Databento (index in dev?), IBKR (TWS), others | Research  |
| 11.2 | P2       | Add Barchart batch schema to api-contracts                                 | Barchart  |
| 11.3 | P2       | Add IBKR VIX streaming schemas when chosen                                 | IBKR      |
| 11.4 | P2       | Add Databento VIX index schemas when available                             | Databento |

---

## 11. Cross-Cutting

| DO   | Priority | Description                                                                           |
| ---- | -------- | ------------------------------------------------------------------------------------- |
| 12.1 | P1       | Add SCHEMA_VERSIONS.md + pinned [schema-validation] deps                              |
| 12.2 | P1       | Add api_contracts/endpoints.py with base URLs + ENDPOINT_SCHEMA_MAP                   |
| 12.3 | P1       | Add chain-instruction validation (BTC vs ETH) to strategy-service + execution-service |
| 12.4 | P1       | Add (venue, instrument_type, operation) plausibility checks                           |
| 12.5 | P2       | Document collected_responses / generated_schemas / api_contracts flow                 |
| 12.6 | P1       | Migrate all schemas from market-tick-data-handler to api-contracts                    |

---

## Sub-Agent Research Areas (10 agents)

| Agent | Focus                                                                                                          | Repos / Paths                                     |
| ----- | -------------------------------------------------------------------------------------------------------------- | ------------------------------------------------- |
| 1     | Market data / feed – Databento, Tardis, Yahoo, Barchart                                                        | api-contracts, market-tick-data-handler           |
| 2     | Orders / positions – CeFi (Binance-spot, Binance-usdm, Binance-coinm, OKX, Bybit, Upbit, Coinbase), IBKR, DeFi | api-contracts, unified-trade-execution-interface  |
| 3     | Reference data – instrument types, venue matrix                                                                | api-contracts, instruments-service                |
| 4     | Exchange status / WebSocket / FIX lifecycle                                                                    | api-contracts, per-venue schemas                  |
| 5     | Error handling – per-venue errors, rate limits                                                                 | api-contracts/schemas/errors.py                   |
| 6     | Cloud SDKs – GCP (Compute, Cloud Run, GCS, BigQuery)                                                           | api-contracts/cloud_sdks, unified-trading-library |
| 7     | Cloud SDKs – AWS (EC2, ECS, S3, Glue, quotas)                                                                  | api-contracts/cloud_sdks                          |
| 8     | Quota handling – UTD v3 quota broker, message schemas                                                          | unified-trading-deployment-v3, api-contracts      |
| 9     | DeFi / MEV / transfers                                                                                         | api-contracts, execution-service                  |
| 10    | TradFi / VIX / Barchart                                                                                        | api-contracts, market-tick-data-handler           |
