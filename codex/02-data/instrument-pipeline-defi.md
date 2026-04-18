# DeFi Instrument Pipeline

## Overview

Every DeFi strategy depends on a chain of upstream services providing instrument definitions, market data, and features.
This doc covers the full pipeline from instrument definition to strategy signal generation, including which instruments
are required by which strategy type.

## Pipeline Stages

```
instruments-service
    │  Provides: InstrumentRecord objects with canonical instrument_key
    │  Adapters: eigenlayer.py, ethfi.py, lido.py, etherfi.py, binance.py, hyperliquid.py
    ▼
market-tick-data-service (MTDS)
    │  Consumes: instrument_key list per venue
    │  Produces: raw_tick_data/by_date/day={date}/data_type={dt}/instrument_type={it}/venue={v}/{key}.parquet
    │  PATH_REGISTRY template: "raw_tick_data" — partition_keys = [date, data_type, instrument_type, venue]
    ▼
market-data-processing-service (MDPS)
    │  Consumes: raw_tick_data parquets (per instrument_key)
    │  Produces: processed_candles/by_date/day={date}/timeframe={tf}/data_type={dt}/instrument_type={it}/venue={v}/{id}.parquet
    │  PATH_REGISTRY template: "processed_candles" — partition_keys = [date, timeframe, data_type, instrument_type, venue]
    ▼
features-onchain-service
    │  Consumes: processed_candles + on-chain RPC data (Aave, EigenLayer, EtherFi)
    │  Produces: feature vectors (eigen_claimable_amount, lido_staking_apy, health_factor, ...)
    │  GCS bucket: features/
    ▼
strategy-service
    │  Consumes: feature vectors
    │  Produces: DEPLOY/EXIT/CLAIM_REWARD/SELL_REWARD/STAKE/UNSTAKE instructions
    ▼
execution-service
    │  Consumes: instructions
    │  Executes: on-chain transactions (Aave, Uniswap, EigenLayer, Lido)
```

## Per-Strategy Instrument Requirements

| Strategy                      | Staking Instrument                    | Perp Instrument                                  | Reward Token(s)                   | Price Feeds Needed                                                              |
| ----------------------------- | ------------------------------------- | ------------------------------------------------ | --------------------------------- | ------------------------------------------------------------------------------- |
| `DEFI_STAKED_BASIS` (EtherFi) | `ETHERFI-ETHEREUM:LST:WEETH@ETHEREUM` | `HYPERLIQUID:PERPETUAL:ETH-USDC@LIN@HYPERLIQUID` | EIGEN (weekly), ETHFI (quarterly) | `eigen_price_usdt`, `ethfi_price_usdt`, `weeth_eth_rate`                        |
| `DEFI_STAKED_BASIS_LIDO`      | `LIDO-ETHEREUM:LST:WSTETH@ETHEREUM`   | `HYPERLIQUID:PERPETUAL:ETH-USDC@LIN@HYPERLIQUID` | None                              | `wsteth_eth_rate`                                                               |
| `DEFI_RECURSIVE_BASIS`        | `ETHERFI-ETHEREUM:LST:WEETH@ETHEREUM` | `HYPERLIQUID:PERPETUAL:ETH-USDC@LIN@HYPERLIQUID` | EIGEN (weekly), ETHFI (quarterly) | `eigen_price_usdt`, `ethfi_price_usdt`, `weeth_eth_rate`, `aave_supply_apy_eth` |
| `DEFI_AAVE_LENDING`           | None (borrows ETH)                    | None                                             | None                              | `aave_supply_apy_usdc`, `aave_borrow_apy_eth`, `health_factor`                  |

## Canonical Instrument Keys (instruments-service SSOT)

### Staking / LST Instruments

| Key                                   | Venue              | Type            | Deploy Date |
| ------------------------------------- | ------------------ | --------------- | ----------- |
| `ETHERFI-ETHEREUM:LST:WEETH@ETHEREUM` | `ETHERFI-ETHEREUM` | `YIELD_BEARING` | 2023-11-01  |
| `LIDO-ETHEREUM:LST:STETH@ETHEREUM`    | `LIDO-ETHEREUM`    | `YIELD_BEARING` | 2020-12-18  |
| `LIDO-ETHEREUM:LST:WSTETH@ETHEREUM`   | `LIDO-ETHEREUM`    | `YIELD_BEARING` | 2020-12-18  |

### Governance / Reward Tokens

| Key                                           | Venue                  | Type               | Contract                                     | Deploy Date |
| --------------------------------------------- | ---------------------- | ------------------ | -------------------------------------------- | ----------- |
| `EIGENLAYER-ETHEREUM:GOVERNANCE_TOKEN:EIGEN`  | `EIGENLAYER-ETHEREUM`  | `GOVERNANCE_TOKEN` | `0xec53bF9167f50cDEB3Ae105f56099aaaB9061F83` | 2024-09-17  |
| `ETHERFI-GOV-ETHEREUM:GOVERNANCE_TOKEN:ETHFI` | `ETHERFI-GOV-ETHEREUM` | `GOVERNANCE_TOKEN` | `0xFe0c30065B384F05761f15d0CC899D4F9F9Cc0eB` | 2024-03-18  |

### Perp Instruments (Hedge Leg)

| Key                                              | Venue             |
| ------------------------------------------------ | ----------------- |
| `HYPERLIQUID:PERPETUAL:ETH-USDC@LIN@HYPERLIQUID` | `HYPERLIQUID`     |
| `BINANCE-FUTURES:PERPETUAL:ETHUSDT`              | `BINANCE-FUTURES` |

### Binance Spot (Reward Sale Venue)

| Key                                 | Symbol    |
| ----------------------------------- | --------- |
| `BINANCE-SPOT:SPOT_PAIR:EIGEN~USDT` | EIGENUSDT |
| `BINANCE-SPOT:SPOT_PAIR:ETHFI~USDT` | ETHFIUSDT |

## GCS Path Templates (PATH_REGISTRY SSOT)

Both templates defined in `unified_trading_library.config_interface.paths.registry.PATH_REGISTRY`.

### Raw Tick Data (MTDS output)

```
raw_tick_data/by_date/day={date}/data_type={data_type}/instrument_type={instrument_type}/venue={venue}/{instrument_key}.parquet
```

Example:

```
raw_tick_data/by_date/day=2026-03-01/data_type=trades/instrument_type=PERPETUAL/venue=BINANCE-FUTURES/BINANCE-FUTURES:PERPETUAL:ETHUSDT.parquet
```

### Processed Candles (MDPS output)

```
processed_candles/by_date/day={date}/timeframe={timeframe}/data_type={data_type}/instrument_type={instrument_type}/venue={venue}/{instrument_id}.parquet
```

Example:

```
processed_candles/by_date/day=2026-03-01/timeframe=1H/data_type=ohlcv_1h/instrument_type=PERPETUAL/venue=BINANCE-FUTURES/BINANCE-FUTURES:PERPETUAL:ETHUSDT.parquet
```

### Usage in Services

```python
from unified_trading_library.config_interface.paths.registry import build_path

# MTDS: write path for a single instrument
path = build_path(
    "raw_tick_data",
    date="2026-03-01",
    data_type="trades",
    instrument_type="PERPETUAL",
    venue="BINANCE-FUTURES",
) + "/BINANCE-FUTURES:PERPETUAL:ETHUSDT.parquet"

# MDPS: write path for processed candles
path = build_path(
    "processed_candles",
    date="2026-03-01",
    timeframe="1H",
    data_type="ohlcv_1h",
    instrument_type="PERPETUAL",
    venue="BINANCE-FUTURES",
) + "/BINANCE-FUTURES:PERPETUAL:ETHUSDT.parquet"
```

## How to Add New Instruments to the Pipeline

### Step 1: Add the Instrument Adapter (instruments-service)

Create or update an adapter in `instruments_service/reference_data/adapters/`:

```python
class MyTokenReferenceDataAdapter(BaseReferenceDataAdapter):
    @property
    def venue(self) -> str:
        return "mytoken-ethereum"

    async def get_instruments(self, ...) -> list[InstrumentRecord]:
        return [InstrumentRecord(
            instrument_key="MYTOKEN-ETHEREUM:GOVERNANCE_TOKEN:MTK",
            venue="MYTOKEN-ETHEREUM",
            instrument_type=InstrumentType.GOVERNANCE_TOKEN,
            base_asset="MTK",
            ...
        )]
```

Register in `factory.py`:

- Add to `CANONICAL_VENUE_TO_ADAPTER`: `"MYTOKEN-ETHEREUM": "mytoken"`
- Add to `_ADAPTERS`: `"mytoken": MyTokenReferenceDataAdapter`

### Step 2: Add MTDS Coverage

If the new instrument requires a dedicated market data feed (e.g. Binance spot price), verify the venue adapter in MTDS
handles it. For on-chain tokens, ensure the venue adapter fetches from the correct API (Binance, Coingecko, etc.).

### Step 3: Add Features-Onchain Feature

If the instrument has on-chain state (claimable balance, APY), add a feature in `features-onchain-service`:

```python
# Example: my_token_claimable_amount
async def compute_my_token_claimable(wallet_address: str, rpc_url: str) -> float:
    contract = w3.eth.contract(address=MY_TOKEN_CONTRACT, abi=MY_TOKEN_ABI)
    return contract.functions.balanceOf(wallet_address).call()
```

### Step 4: Add to Strategy Config

Reference the new instrument in the strategy YAML config and feature list. Update the strategy's `_required_features`
list to include the new feature key.

### Step 5: Update Reward Schedule (if applicable)

If the token is distributed on a schedule, add it to `unified_api_contracts/registry/reward_schedules.py`:

```python
RewardScheduleEntry(
    protocol="MYPROTOCOL",
    token="MTK",
    settlement_type=RewardSettlementType.SEASONAL_WEEKLY,
    distribution_day=0,   # Monday
    distribution_hour=0,
)
```

## Key Files

| File                                                         | Purpose                                                      |
| ------------------------------------------------------------ | ------------------------------------------------------------ |
| `instruments_service/reference_data/adapters/eigenlayer.py`  | EIGEN governance token adapter                               |
| `instruments_service/reference_data/adapters/ethfi.py`       | ETHFI governance token adapter                               |
| `instruments_service/reference_data/adapters/lido.py`        | stETH/wstETH LST adapters                                    |
| `instruments_service/reference_data/factory.py`              | Adapter registry (`CANONICAL_VENUE_TO_ADAPTER`, `_ADAPTERS`) |
| `unified_api_contracts/registry/reward_schedules.py`         | EIGEN/ETHFI reward schedule SSOT                             |
| `unified_trading_library/config_interface/paths/registry.py` | GCS path templates SSOT                                      |
| `market_tick_data_service/engine/orchestrator.py`            | MTDS write path + per-instrument files                       |
| `market_data_processing_service/config.py`                   | MDPS `get_processed_path()`                                  |

## Related Docs

- `codex/09-strategy/cross-cutting/reward-lifecycle.md` — EIGEN/ETHFI reward claim/sell lifecycle
- `codex/02-data/partitioning.md` — Hive partition schema for GCS
- `codex/02-data/hive-schema-compatibility.md` — BigQuery external table compatibility
