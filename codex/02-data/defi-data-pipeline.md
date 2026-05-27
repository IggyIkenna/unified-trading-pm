# DeFi Data Pipeline — collection → processing → features (end-to-end)

> **Purpose.** A single reference for the DeFi data path: what raw data we pull from each venue, how it's processed,
> what features we compute, and **why each venue is in the universe** (liquidity vs unique data). Grounded in code as of
> 2026-05-27. Companion to [`defi-execution-overview`](../04-architecture/defi-execution-overview.md) (execution side)
> and [`availability-manifest-and-data-status`](availability-manifest-and-data-status.md).
>
> **Audience.** Data-pipeline owner + anyone reasoning about DeFi coverage / features.

---

## 0. The four stages (one diagram)

```
instruments-service        MTDS                       MDPS                         features-service
(reference data)    →     (raw capture)        →     (processing)          →      (feature calc)
                                                                                    ├─ onchain family
 pool/token/market         dex_swaps, lending_         processed_candles            └─ delta_one (DEFI route)
 metadata, decimals,       indices, lst_rates,         (OHLCV bars from
 fee tiers, venue×chain     oracle_prices, dex_pool_    swaps/rates/liquidity)      → strategy-service
 universe, available_from   state, vault_share_price,                                  (archetype signals)
                            perp_funding, ...           + BYPASS types passed
                                                        straight to features
```

**Directional contract (enforced at manifest/preflight):**

- MTDS reads instruments-service `InstrumentRecord` parquets to know **what** to fetch and **which endpoint URL**
  (`source_archive_url_template`) — no hardcoded venue URLs in MTDS (QG-enforced).
- MDPS reads MTDS raw parquets. Some data_types have **no MDPS adapter** and are consumed directly by features (the
  "bypass" set, §4.3).
- features-onchain reads MDPS `processed_candles/` **and** the MTDS raw bucket directly (for bypass types).
- instruments-service depends on nothing downstream.

**Repos / CLIs:**

| Stage       | Repo                                    | CLI                                                                              |
| ----------- | --------------------------------------- | -------------------------------------------------------------------------------- |
| Reference   | `instruments-service`                   | `instruments process --DEFI --mode batch`                                        |
| Raw capture | `market-tick-data-service` (MTDS)       | `market_tick_data_service --operation collect-* --asset-group DEFI --mode batch` |
| Processing  | `market-data-processing-service` (MDPS) | `market-data-processing process --DEFI --mode batch --operation timer-candles`   |
| Features    | `features-service`                      | `features_service.onchain` / `features_service.delta_one --asset-group DEFI`     |

---

## 1. GCS bucket layout (verified 2026-05-27)

Canonical DeFi bucket: `market-data-tick-defi-prd-central-element-323112` (flat predecessor
`market-data-tick-defi-central-element-323112` is being consolidated into `-prd`; see
[`features_backfill_phase3`](../../plans/active/features_backfill_phase3_2026_05_22.md) for the candle-split state).

```
market-data-tick-defi-prd-.../
├── raw_tick_data/by_date/day=YYYY-MM-DD/asset_group=defi/venue=<V>/chain=<C>/instrument_type=<T>/data_type=<D>/*.parquet
│        data_type ∈ { dex_swaps, dex_pool_state, dex_pool_swaps, oracle_prices, rate_indices,
│                       rewards, risk_params, utilization, vault_share_price, eigenlayer_rewards, ... }
├── lst_rates/              ← LST exchange-rate snapshots (own top-level prefix)
├── lending_indices/        ← Aave/Compound/Morpho rate snapshots (own top-level prefix)
├── dex_pools/              ← pool reference/metadata snapshots
├── processed_candles/by_date/day=YYYY-MM-DD/   ← MDPS output (the candle path)
├── _index/  _manifests/  _vm_staging/  backfill-logs/  configs/
```

The current backfill (`mtds-dex-swaps-backfill`, `collect-dex-swaps`, 2023-01-01→2026-05-25) writes `dex_swaps` +
`vault_share_price` into `raw_tick_data/by_date/...` in `-prd`.

---

## 2. Stage 1 — instruments-service (reference data, NOT market data)

IS produces `InstrumentRecord` parquets — the **universe** and **per-instrument metadata** MTDS needs. The "stamped
instruments" line in MTDS logs (`loaded N stamped instruments for venue=BALANCER-ETHEREUM`) is IS output being read.

**`InstrumentRecord` fields:** `instrument_type`, `instrument_key`, `source_archive_url_template` (the IS→MTDS fetch-URL
contract), `available_from_datetime` / `available_to_datetime`, token decimals, fee tier, TVL snapshots.

**Universe enumeration** (`instruments_service/engine/orchestrator.py`):

- Static: `_STATIC_DEFI_VENUES` (LIDO/ETHERFI/ETHENA/EIGENLAYER-ETHEREUM), `_SOLANA_DEFI_VENUES`
  (DRIFT/KAMINO/RAYDIUM/ORCA/MARINADE/JITO/PACIFICA-SOLANA), `_L2_DEX_PERP_VENUES` (LIGHTER-ZKSYNC, EXTENDED-STARKNET).
- Dynamic: `_build_defi_venues()` = `protocol × get_supported_chains_for_protocol()` (Uniswap V2/V3/V4, Aave V3, Morpho,
  Balancer, PancakeSwap V3, Sushiswap V3, Aerodrome, Camelot, Velodrome, Trader Joe, GMX).
- **Relevance filter** (`filter_defi_instruments_by_relevance()`): DEX pools need **both** tokens in `MAJOR_ASSETS`;
  lending markets need only the base token in `MAJOR_ASSETS`.
- **Monotonicity** (`_enforce_defi_monotonicity()`): per-venue high-water mark — a run returning fewer instruments than
  the HWM is blocked (prevents silent universe shrink).

**IS does NOT produce** `lst_rates` or `lending_indices` time-series — those are raw captures MTDS fetches using the IS
`source_archive_url_template` (e.g. Lido APR endpoint). IS is reference data only.

---

## 3. Stage 2 — MTDS raw capture: what we pull, from where

### 3.1 CLI operations → data_types

| `--operation`                                                                                                                     | data_type(s)                                                | Source                                                                             |
| --------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| `collect-dex-swaps`                                                                                                               | `dex_swaps`                                                 | The Graph subgraphs (UniV3 / Balancer / Messari schemas)                           |
| `collect-dex-pools`                                                                                                               | `dex_pool_state`                                            | The Graph subgraphs                                                                |
| `collect-lending-indices` / `collect-evm-defi`                                                                                    | `lending_indices` (+ `utilization`, `risk_params` derived)  | The Graph (Aave native / Messari / Compound custom); DeFiLlama (Solana)            |
| `collect-lst-rates`                                                                                                               | `lst_rates`                                                 | EVM: direct `eth_call` at historical block via Alchemy. Solana: Marinade/Jito REST |
| `collect-oracle-prices`                                                                                                           | `oracle_prices`                                             | Chainlink `latestRoundData()` (EVM) + Pyth Hermes REST (Solana)                    |
| `collect-solana-defi`                                                                                                             | `dex_pools`, `lending_indices`, `lst_rates`, `perp_funding` | Orca/Raydium/Phoenix/Kamino REST, DeFiLlama, Drift S3+API                          |
| `collect-eigenlayer-rewards`                                                                                                      | `eigenlayer_rewards`                                        | EigenLayer                                                                         |
| `collect-vault-share-price`                                                                                                       | `vault_share_price`                                         | ERC-4626 `convertToAssets`                                                         |
| `collect-perp-funding`                                                                                                            | `perp_funding`                                              | Drift / GMX / Hyperliquid                                                          |
| `collect-liquidations` / `-events`, `-flash-loan-events`, `-bridge-events`, `-mev-events`, `-gas-fees`, `-aggregator-routes`, ... | as named                                                    | per-protocol                                                                       |

### 3.2 Per-data_type content + source (the important ones)

| data_type               | What it is                                                                                                                                                                         | Key columns                                                                                                                                                                                                    | Source                                                                                |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| **`dex_swaps`**         | individual swap events on a DEX pool                                                                                                                                               | `swap_id, timestamp, pool_id, token_a/b (or token_in/out), amount0/1 (or amount_in/out), amount_usd, fee_rate_bps, tick, sender`                                                                               | The Graph (schema fallback: univ3 → pancake → univ3_minimal → messari → sushi_custom) |
| **`dex_pool_state`**    | daily/hourly pool snapshot                                                                                                                                                         | `pool_id, token_a/b, fee_rate_bps, tvl_usd, volume_usd, fees_usd, tx_count, price_a/b, liquidity, sqrt_price, tick`                                                                                            | The Graph                                                                             |
| **`lending_indices`**   | per-asset lending market rate snapshot                                                                                                                                             | `protocol, chain, symbol, liquidity_index, variable_borrow_index, supply_rate, borrow_rate, utilization_rate, total_supply, total_debt, reserve_factor, IRM slopes (slope1/2, optimal_utilization, base_rate)` | The Graph (Aave native / Messari / Compound custom); DeFiLlama for Solana             |
| **`lst_rates`**         | LST/LRT exchange rate (share→underlying)                                                                                                                                           | `timestamp, token, exchange_rate, apy, quote_asset, protocol, chain, block_number, method, contract, is_rebasing, rebase_rate`                                                                                 | EVM `eth_call` at noon-UTC historical block; Solana REST                              |
| **`oracle_prices`**     | reference price feed                                                                                                                                                               | `feed, base/quote_asset, price, confidence, publish_time, updated_at, round_id, block_number, source, chain`                                                                                                   | Chainlink (EVM, on-chain `latestRoundData`) + Pyth Hermes (Solana)                    |
| **`perp_funding`**      | DeFi-perp funding/mark                                                                                                                                                             | `protocol, symbol, funding_rate (24h/7d/30d), oracle_px, mark_px, open_interest, oi_long/short`                                                                                                                | Drift S3+API (Solana), GMX (Arb/Avax), Hyperliquid                                    |
| **`vault_share_price`** | ERC-4626 vault price-per-share                                                                                                                                                     | `vault_address, share_price, timestamp`                                                                                                                                                                        | ERC-4626 `convertToAssets`                                                            |
| `rate_indices`          | feature-facing projection of lending state (Aave `getReserveData` / `getUserAccountData`); carries `utilization_rate`, `ltv`, `liquidation_threshold`, `health_factor`, IRM params | —                                                                                                                                                                                                              | derived from lending capture                                                          |
| `liquidations`          | liquidation events                                                                                                                                                                 | `collateral/principal_symbol+amount, liquidator, user`                                                                                                                                                         | The Graph                                                                             |
| `eigenlayer_rewards`    | restaking rewards                                                                                                                                                                  | —                                                                                                                                                                                                              | EigenLayer                                                                            |

**Schema fallback pattern** (all subgraph handlers): on `SubgraphSchemaError` ("Type X has no field …" — the
`messari schema failed, trying next fallback` log line) the handler advances through an ordered list of schema variants;
all exhausted → `record_failed`. This is why one venue (e.g. Curve) tries multiple subgraph schemas.

### 3.3 EVM vs Solana

- **EVM** — all via The Graph (GraphQL) or Alchemy `eth_call` at a historical block (block resolved from timestamp).
  Subgraph IDs centralised in UAC `SUBGRAPH_IDS`. Chains: Ethereum, Arbitrum, Base, Optimism, Polygon, Avalanche, BSC,
  Linea. (ankrETH rate is inverted: `1e18 / raw`.)
- **Solana** — no subgraphs; per-protocol REST/SDK. Pyth via Hermes REST (archive from 2023-10-01). Drift historical via
  S3 (to 2025-01-08) then live API. DeFiLlama is the unified fallback for Solana lending (Kamino/Solend/Marginfi;
  marginfi is TVL-only, `supply_apy=0`).

---

## 4. The venue universe — same-kind data vs unique data (the "why each venue" question)

This is the core distinction. Venues fall into **two buckets**: those that give the **same kind of data** (DEX
swaps/pools — chosen for liquidity / cross-venue dispersion), and those included specifically for **unique data** a
strategy needs (lending rates, LST APRs, oracle prices, vault shares, perp funding, restaking rewards).

SSOT: `unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi*.py` +
`registry/defi_venues.py`.

### 4.1 Same-kind data (DEX swaps + pools) — chosen for liquidity & price dispersion

These feed the **`arbitrage_price_dispersion`** archetype. They all provide `dex_swaps` + `dex_pool_state` — the value
is **breadth of liquidity across venues/chains**, not unique fields.

| Venue                                        | Chains                                    | Notes                                                     |
| -------------------------------------------- | ----------------------------------------- | --------------------------------------------------------- |
| Uniswap V2 / V3 / V4                         | V3: ETH, ARB, BASE, OPT, POLY (V2/V4 ETH) | deepest liquidity; V3 adds tick/sqrt_price/liquidity      |
| Balancer                                     | ETH, ARB, POLY, OPT, AVAX, BASE           | multi-token weighted pools                                |
| Curve                                        | ETH, OPT, AVAX                            | stableswap (ARB/POLY subgraphs deprecated → api.curve.fi) |
| PancakeSwap V3                               | BSC, ETH, BASE                            | UniV3 fork                                                |
| SushiSwap V3 / (V2 legacy)                   | ETH/BASE/AVAX; V2 on ARB                  | mixed schemas                                             |
| Aerodrome V3                                 | BASE                                      | UniV3-style                                               |
| Camelot V3                                   | ARB                                       | Algebra fork (feeZtO/feeOtZ)                              |
| Velodrome V2                                 | OPT                                       | Messari schema                                            |
| Trader Joe V2                                | AVAX                                      | currently empty                                           |
| Solana DEXes: Raydium, Orca, Phoenix, Kamino | SOLANA                                    | REST APIs; Drift is CLOB-style                            |

### 4.2 Unique data — venue included because it's the only source of that signal

| Role                    | Venues                                                                                                                                           | Unique data they provide                                                                                                                    | Used by                                         |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- |
| **Lending**             | Aave V3, Compound V3, Spark, Morpho, Fluid (+Euler/Radiant/Venus/Benqi declared)                                                                 | `lending_indices` (supply/borrow rate, utilization, IRM slopes), `liquidations`, `risk_params` (LTV, liquidation_threshold, reserve_factor) | `carry_staked_basis` borrow leg + HF            |
| **LST / staking (ETH)** | Lido (stETH/wstETH), RocketPool (rETH), Coinbase (cbETH), EtherFi (weETH), Ethena (sUSDe), Mantle (mETH), Swell, Stader, StakeWise, Puffer, Ankr | `lst_rates` (exchange_rate, is_rebasing, apy)                                                                                               | `carry_staked_basis` staking yield              |
| **LST / staking (SOL)** | Marinade (mSOL), Jito (jitoSOL), SolBlaze (bSOL), Sanctum                                                                                        | `lst_rates` for SOL-family                                                                                                                  | `carry_staked_basis` (Solana side)              |
| **Oracles**             | **Pyth (Solana only)**, **Chainlink (all EVM)**                                                                                                  | `oracle_prices` (price + confidence + publish_time)                                                                                         | price feed; oracle-deviation / staleness gating |
| **DeFi perps**          | GMX (Arb/Avax), Drift (Solana), Hyperliquid (own L1), Aster                                                                                      | `perp_funding` (+ liquidations)                                                                                                             | `carry_staked_basis` hedge leg                  |
| **Restaking / vaults**  | EigenLayer, Solayer, Picasso, Cambrian; ERC-4626 vaults (EtherFi, Yearn V3, Morpho Vaults, Pendle)                                               | `rewards` / `restaking_rewards`, `vault_share_price`                                                                                        | second-layer AVS yield, vault APY               |
| **Cost / infra**        | Alchemy (synthetic), Flashbots, Across/Stargate                                                                                                  | `gas_fees`, `mev_events`, `bridge_events`                                                                                                   | execution cost / MEV / cross-chain              |

**One-line mental model:** _DEX venues are interchangeable liquidity sources (more = better price dispersion); lending /
LST / oracle / perp / restaking venues are each in the universe because they're the canonical source of one specific
signal the archetype math needs._

### 4.3 RPC tiers & chains

`CHAIN_RPC_TEMPLATES` (`_defi_chain_data.py`) tiers chains: Tier-1 strategy-critical (Ethereum, Arbitrum, Base, Optimism
— Alchemy, low reorg depth), Tier-2 (BSC, Polygon, Avalanche, Gnosis), Tier-3 zkEVMs/OP-stack, Tier-4 alt-L1s (public
RPC). Plus `SOLANA_RPC_TEMPLATES` (Alchemy/Helius), `HYPERLIQUID_RPC_TEMPLATES`, and MEV-resistant submission URLs
(`PROTECTED_RPC_URLS`: Flashbots Protect, MEV Blocker).

---

## 5. Stage 3 — MDPS processing: raw → processed_candles

MDPS turns a subset of raw types into OHLCV `processed_candles`. Six DeFi adapters
(`market-data-processing-service/.../app/adapters/defi/`):

| Adapter                     | Input raw type                    | How OHLCV is built                                                                                                                                                                                                                                                                                     |
| --------------------------- | --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `DefiSwapAdapter`           | `dex_swaps`, `dex_pool_swaps`     | **real OHLCV** — per-swap price derived (cascade: `amount_usd/amount_in` → `amount1/amount0` → `(sqrtPriceX96/2^96)^2`), grouped by interval → first/max/min/last + summed volume. **Sparse: no swap in window = no row** (not forward-filled). Extra cols: `chain`, `swap_count`, `volume_quote_usd`. |
| `DefiLendingIndicesAdapter` | `lending_indices`, `rate_indices` | rate is a **state**, so O=H=L=C=rate, LOCF-filled across the day; volume proxy = `total_atoken_supply`. Base granularity **15m** (no sub-15m). Extra: `borrow_rate`, `utilization_ratio`, `liquidity_index`.                                                                                           |
| `DefiLiquidityAdapter`      | `dex_pool_state` (V2/V3/V4)       | `mid_price = (token0_price + 1/token1_price)/2` LOCF; volume = `tvl_usd`; `depth_bid/ask = reserve0/1`.                                                                                                                                                                                                |
| `DefiMarketStateAdapter`    | `market_state`                    | O=H=L=C=`liquidity`; `spread_bps = utilization×10000`.                                                                                                                                                                                                                                                 |
| `DefiFxRateAdapter`         | CeFi spot candle closes           | derives `fx_rate_eth_usd / btc_usd / sol_usd` (USD conversion helper).                                                                                                                                                                                                                                 |
| `DefiBookSnapshotAdapter`   | on-chain CLOB L2 (Hyperliquid)    | delegates to CeFi book adapter.                                                                                                                                                                                                                                                                        |

**Common bar mechanics** (`base_adapter.py`): 200µs synthetic delay (anti-lookahead), end-of-period candle convention,
timeframes `15s/1m/5m/15m/1h/4h/24h`, DeFi treated as 24/7. Empty paths: zero rows → `empty_confirmed`;
ticks-outside-day → `UpstreamTimestampBiasError`. Output schema = `PROCESSED_CANDLE_SCHEMA`
(`timestamp, venue, symbol, instrument_id, open/high/low/close, volume` + nullable extras). Output:
`processed_candles/by_date/day={date}/`.

**Bypass types (no MDPS adapter — features read them straight from MTDS):** `liquidations`, `oracle_prices`,
`dex_pools`, `lst_rates`, `vault_share_price`, `perp_funding`, `gas_fees`, `rewards`, `risk_params`,
`liquidation_events`, `flash_loan_events`, `eigenlayer_rewards`, `utilization`, `staking_yields`, etc.

---

## 6. Stage 4 — feature calculation

Two feature paths run on DeFi data.

### 6.1 `onchain` family (DeFi-specific) — `features_service/onchain/`

Driven by `OnChainOrchestrationService`; definitions in `onchain/schemas/feature_definitions.yaml` (~74 declared
columns). Key groups:

| Group                                                 | Inputs                            | What it computes                                                                                                                                       |
| ----------------------------------------------------- | --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `lending_rates`                                       | `rate_indices` (+ DeFiLlama live) | normalises supply/borrow/util across protocols; **synthesises supply APY** (`borrow_apy × util × (1−reserve_factor)`); `rate_spread = borrow − supply` |
| `lst_yields`                                          | `lst_rates`                       | **`staking_apy_bps = ((rate[t]/rate[t-1])^365 − 1)×1e4`** (day-over-day annualised). `staking_apy_total_bps = base + eigen + seasonal − dust`          |
| `lst_native_rates`                                    | `lst_rates`                       | raw same-day exchange rate (no prior-day join) — `carry_staked_basis` Phase 6B                                                                         |
| `perp_funding_rates`                                  | `perp_funding`                    | `funding_rate_apy_bps = annualise_funding_rate_bps(raw, venue)` (MVP: Hyperliquid ETH-PERP)                                                            |
| `utilization`                                         | `rate_indices`                    | `aave_utilization` (passthrough; fallback `liquidity_rate/variable_borrow_rate`)                                                                       |
| `risk_params`                                         | `rate_indices`                    | `aave_ltv`, `aave_liquidation_threshold`                                                                                                               |
| `health_factor`                                       | `rate_indices`                    | `aave_health_factor`, collateral/debt ETH                                                                                                              |
| `rate_impact` (live)                                  | DeFiLlama                         | projected APY after injecting a $500k position (two-slope IRM); `rate_impact_*_bps`                                                                    |
| `rewards`                                             | `rate_indices`                    | `weekly_rewards = reward_rate×7`                                                                                                                       |
| `flash_loan_availability`                             | `rate_indices` (Morpho)           | `morpho_flash_loan_liquidity`                                                                                                                          |
| `macro_tvl` / `macro_sentiment` / `fear_greed` (live) | DeFiLlama, Alternative.me         | TVL, stablecoin dominance, F&G index                                                                                                                   |
| `regime`                                              | mixed                             | `oracle_deviation_flag` (\|oracle−dex\|/dex > 1%), `tvl_regime_bucket`, util/gas/HF buckets                                                            |

App-layer calculators (live/current-day): `ChainlinkPegDeviationCalculator` (`peg_deviation_bps` rolling 1h on
wstETH/cbETH/weETH; `oracle_staleness_seconds`), `ConcentratedLiquidityIlRealisedCalculator` (V3 IL vs fees),
`VaultSharePriceApyCalculator` (`vault_share_price_apy_bps` annualised), `PoolInvariantDriftCalculator` (Curve
StableSwap Newton-D drift / Balancer weighted-geomean drift).

> **Batch gap (track):** `utilization`, `rate_impact`, `macro_*`, `onchain_perps` are **batch-skipped for historical
> dates** (live-only sources — DeFiLlama Yields API has no historical archive; plus an MTDS backfill schema gap). They
> run normally in live mode. Verify before relying on these columns in a batch feature run.

### 6.2 `delta_one` family applied to DeFi (asset_group=DEFI)

`delta_one` runs on DeFi via `DEFI_DATA_TYPE_OVERRIDES` (`delta_one/engine/orchestrator.py`): price-series indicators
remap their input from CeFi `trades` to DeFi sources —

- **`oracle_prices`** → `technical_indicators` (RSI/MACD/ADX/Bollinger/ATR/Stoch/Ichimoku), `moving_averages`,
  `oscillators`, `volatility_realized` (Parkinson/Garman-Klass/Yang-Zhang), `momentum`, `returns`, `market_structure`,
  `candlestick_patterns`, `targets`.
- **`dex_swaps`** → `volume_analysis`, `vwap`, `microstructure` (per-swap volume as order flow).
- **`derivative_ticker`** (Hyperliquid) → `funding_oi`, `liquidations`.

So DeFi price features are computed off the **Chainlink/Pyth oracle series**, and DeFi flow features off **swap
events**.

### 6.3 Output schema

UIC contract: `OnchainFeatureRecord` (`unified-api-contracts/.../internal/domain/features_onchain/onchain_feature.py`) —
`timestamp, instrument_key ("DEFI:PROTOCOL:TOKEN:CHAIN"), lending_rate, borrowing_rate, utilization_ratio, staking_yield, reward_apy, tvl, available_liquidity, ltv, liquidation_threshold, market_state, is_halted, is_auction`.
Per-group wide rows differ (e.g. `lst_yields`: `token, exchange_rate, prev_rate, staking_apy_bps, …`).

---

## 7. Archetype data lineage (how it all composes)

**`carry_staked_basis`** (recursive LST stake + perp short hedge):

```
lst_rates ──► onchain.lst_yields ──► staking_apy_total_bps ┐
                                                            ├─► strategy: net basis = staking − funding
perp_funding ──► onchain.perp_funding_rates ──► funding_apy ┘
lending_indices/rate_indices ──► onchain.{lending_rates,utilization,risk_params,health_factor}  (cost-of-capital + HF gate)
```

**`arbitrage_price_dispersion`** (cross-venue price spread):

```
dex_swaps (many venues) ──► MDPS DefiSwapAdapter ──► dex_ohlcv ──► delta_one (vwap/volume/microstructure)
oracle_prices ──► delta_one price indicators + onchain.regime.oracle_deviation_flag (risk gate)
dex_pool_state ──► onchain pool-invariant-drift / concentrated-liquidity-IL  (LP health)
```

---

## 8. Pointers

- Venue/capability SSOT: `unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi*.py`,
  `registry/defi_venues.py`, `registry/defi_venue_capabilities.py` (per-venue per-data_type coverage start dates).
- Canonical schemas: `unified_api_contracts/internal/domain/defi/parquet_records.py`,
  `internal/schemas/_defi_v2_contracts.py`, `internal/market_data/defi.py`.
- Error taxonomy (35 `DefiErrorCode`): `canonical/crosscutting/errors/defi.py`.
- MTDS handlers: `market-tick-data-service/market_tick_data_service/cli/handlers/*defi*.py`,
  `.../adapters/defi/base_defi_adapter.py`, `configs/venue_data_types.yaml`.
- MDPS adapters: `market-data-processing-service/.../app/adapters/defi/`.
- Features: `features-service/features_service/onchain/` (engine + app/calculators + schemas/feature_definitions.yaml),
  `features_service/delta_one/engine/orchestrator.py`.
- Execution side: [`defi-execution-overview`](../04-architecture/defi-execution-overview.md).
