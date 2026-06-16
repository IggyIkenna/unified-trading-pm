---
scope: [engineer, admin]
---

# DeFi Reward Lifecycle

## What It Is

DeFi staking strategies generate multiple reward streams beyond base staking yield. This doc covers:

- **Staking yield**: Continuous (weETH/ETH rate appreciation, stETH rebasing)
- **Restaking rewards**: EIGEN token distributed weekly via EigenLayer RewardsCoordinator
- **Seasonal airdrops**: ETHFI distributed quarterly to weETH holders/operators

## Reward Schedules (UAC Registry SSOT)

Defined in `unified_api_contracts/registry/reward_schedules.py`:

| Protocol   | Token | Frequency              | Settlement Type        |
| ---------- | ----- | ---------------------- | ---------------------- |
| EIGENLAYER | EIGEN | Weekly (Mon 00:00 UTC) | `SEASONAL_WEEKLY`      |
| ETHERFI    | ETHFI | Quarterly (~90 days)   | `SEASONAL_QUARTERLY`   |
| LIDO       | None  | N/A                    | No EIGEN/ETHFI rewards |

## Instrument Requirements

For reward lifecycle to work end-to-end, each layer must be present:

| Layer            | EIGEN                                        | ETHFI                                         |
| ---------------- | -------------------------------------------- | --------------------------------------------- |
| Instruments      | `EIGENLAYER-ETHEREUM:GOVERNANCE_TOKEN:EIGEN` | `ETHERFI-GOV-ETHEREUM:GOVERNANCE_TOKEN:ETHFI` |
| Binance spot     | `BINANCE-SPOT:SPOT_PAIR:EIGEN~USDT`          | `BINANCE-SPOT:SPOT_PAIR:ETHFI~USDT`           |
| MTDS data        | `eigen_price_usdt` candles                   | `ethfi_price_usdt` candles                    |
| Features-onchain | `eigen_claimable_amount`                     | `ethfi_claimable_amount`                      |

## Instruction Flow

```
strategy-service (RewardClaimMixin._check_reward_claims())
    │
    │  features: eigen_claimable_amount > min_claim_value_usd?
    ▼
CLAIM_REWARD instruction → execution-service (claim_reward_handler.py)
    │
    │  calls EigenLayerConnector.claim_rewards(token="EIGEN")
    │  → EigenLayer RewardsCoordinator.processClaim() on-chain
    ▼
SELL_REWARD instruction → execution-service (sell_reward_handler.py)
    │
    │  calls UniswapConnector.swap_exact_input(EIGEN → USDC)
    │  or routes to Binance spot EIGENUSDT market
    ▼
position-balance-monitor-service
    │  tracks: pending → claimed → sold lifecycle
    │  via aggregate_with_rewards() in defi_staking_aggregator.py
    ▼
pnl-attribution-service
    attribution factors:
    - PNL_FACTOR_STAKING_YIELD (continuous, from exchange rate delta)
    - PNL_FACTOR_RESTAKING_REWARD (at claim time = realised)
    - PNL_FACTOR_SEASONAL_REWARD (at airdrop announcement)
    - PNL_FACTOR_REWARD_UNREALISED (M2M of unclaimed tokens)
```

## Key Types and Functions

| Symbol                                    | Location                                                              |
| ----------------------------------------- | --------------------------------------------------------------------- |
| `CLAIM_REWARD`, `SELL_REWARD`             | `unified_api_contracts.canonical.domain.execution.base.OperationType` |
| `RewardScheduleEntry`, `REWARD_SCHEDULES` | `unified_api_contracts.registry.reward_schedules`                     |
| `RewardPosition`                          | `unified_api_contracts.internal.positions.reward_position`            |
| `RewardClaimMixin._check_reward_claims()` | `strategy_service.engine.strategies.defi_enhancements`                |
| `claim_reward_handler.py`                 | `execution_service.engine.handlers.claim_reward_handler`              |
| `sell_reward_handler.py`                  | `execution_service.engine.handlers.sell_reward_handler`               |
| `EigenLayerConnector.claim_rewards()`     | `execution_service.defi_execution.protocols.eigenlayer`               |
| `aggregate_with_rewards()`                | `position_balance_monitor_service.core.defi_staking_aggregator`       |
| `PNL_FACTOR_RESTAKING_REWARD`             | `pnl_attribution_service.engine.breakdown`                            |

## Strategy Config

`RewardClaimMixin` config fields (all strategies inheriting `DeFiBaseStrategy`):

```yaml
auto_claim: true # Enable automatic CLAIM_REWARD
auto_sell: true # Enable automatic SELL_REWARD after claim
min_claim_value_usd: 50.0 # Min USD value before claiming
min_sell_value_usd: 50.0 # Min USD value before selling
claim_frequency_hours: 168 # Check every 168h (weekly for EIGEN)
```

## Protocol Differences

**EtherFi + EigenLayer**: Restaking strategy. Earns EIGEN (weekly) + ETHFI (quarterly). Both reward instructions are
emitted when threshold exceeded.

**Lido**: Pure staking. No EIGEN/ETHFI restaking rewards. `reward_tokens: []` must be set in config; strategy skips
`_check_reward_claims()` for EIGEN/ETHFI.

## M2M Valuation

Unrealised rewards (claimed but not sold) are marked-to-market using:

- `eigen_price_usdt` feature from MTDS/MDPS
- `ethfi_price_usdt` feature from MTDS/MDPS
- `unrealised_reward_pnl = accrued_amount × current_token_price`

## E2E Testing

```bash
# Test ETHERFI reward lifecycle (default)
python e2e-testing/scripts/defi/test_reward_lifecycle.py

# Test Lido (expect no EIGEN/ETHFI reward instructions)
python e2e-testing/scripts/defi/test_reward_lifecycle.py --protocol LIDO

# Run with more candles to trigger quarterly ETHFI
python e2e-testing/scripts/defi/test_reward_lifecycle.py --candles 30
```
