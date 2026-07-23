---
doc_type: codex-ssot
title: Client Configuration and Risk Dimensions
summary:
  Client config schema (ClientConfig/DefiClientConfig in UAC internal.client_config) plus the five per-client risk
  dimensions (market/liquidity/counterparty/funding/reward) and how strategy/risk/PBM/execution services consume them.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [features-service, unified-trading-api, unified-trading-pm, unified-trading-system-ui]
scope: [engineer, admin]
tags: [client-config, risk, defi, cefi, health-factor, entitlements, features]
related:
  [
    /codex/04-architecture/share-class-architecture.md,
    /codex/04-architecture/defi-risk-monitoring.md,
    /codex/09-strategy/architecture-v2/cross-cutting/reward-lifecycle.md,
  ]
created: 2026-04-03
authoritative_for: [per-client configuration schema and the five risk dimensions]
referenced_by:
owner:
last_reviewed: 2026-05-17
code_refs:
---

# Client Configuration and Risk Dimensions

## Overview

The system is multi-client: each client (fund/operator) has independent capital allocation, risk limits, and
entitlements. This doc covers the client config schema, how risk dimensions are computed per client, and how downstream
services consume client config.

## Client Config Schema (UAC SSOT)

Client configuration lives in `unified_api_contracts.internal.client_config`. Key fields:

```python
@dataclass
class ClientConfig:
    client_id: str                          # e.g. "bankelysium-001"
    org_id: str                             # e.g. "bankelysium"
    share_class: str                        # "ETH", "BTC", "USD", "USDC"
    categories_enabled: list[str]           # ["DEFI", "CEFI", "SPORTS"]
    max_total_notional_usd: Decimal         # Hard cap across all strategies
    max_drawdown_pct: Decimal               # Portfolio-level max drawdown (e.g. 0.10 = 10%)
    defi_config: DefiClientConfig | None    # DeFi-specific limits
    cefi_config: CeFiClientConfig | None    # CeFi-specific limits
    sports_config: SportsClientConfig | None
```

```python
@dataclass
class DefiClientConfig:
    max_leverage: Decimal                   # Max leverage across DeFi strategies (e.g. 3.0)
    min_health_factor: Decimal              # Min Aave HF before alert (e.g. 1.5)
    allowed_protocols: list[str]            # ["ETHERFI", "LIDO", "AAVE", "UNISWAP"]
    allowed_chains: list[str]              # ["ETHEREUM", "ARBITRUM", "BASE"]
    reward_auto_claim: bool                # Whether to auto-claim EIGEN/ETHFI rewards
    reward_auto_sell: bool                 # Whether to auto-sell claimed rewards
```

## Risk Dimensions

Risk and exposure service (`risk-and-exposure-service`) computes risk per client across five dimensions:

### 1. Market Risk (Delta)

Net directional exposure in base currency units. For DeFi:

- Staking position delta = +1 (long spot via staked ETH)
- Perp hedge delta = -1 per unit notional
- Net delta = staking notional - perp notional

Target: delta-neutral (net delta ≈ 0). Alert threshold: `max_hedge_deviation_pct` (default 2%).

### 2. Liquidity Risk (Health Factor)

For Aave-leveraged strategies, the Aave Health Factor (HF) measures liquidation risk:

```
HF = Σ(collateral_i × liquidation_threshold_i) / total_debt
```

HF < 1.0 triggers on-chain liquidation. System alerts at HF < `min_health_factor` (default 1.5). Emergency exit triggers
at HF < `emergency_exit_hf` (default 1.2).

Monitored in: `features-service (onchain family)` → `health_factor` feature → `risk-and-exposure-service` alert handler.

### 3. Counterparty Risk (Venue Concentration)

Maximum exposure per venue/protocol as a percentage of total portfolio:

```yaml
# risk-and-exposure-service config
max_venue_concentration_pct: 0.40 # Max 40% in any single venue
```

Tracked across: staking protocol (EtherFi/Lido), perp venue (Hyperliquid/Binance/OKX), lending protocol (Aave/Compound),
bridge protocol (Socket/LayerZero).

### 4. Funding Rate Risk (Carry Risk)

For basis trade strategies, the P&L depends on positive carry (funding rate > borrowing cost). If funding turns
negative:

- P&L = staking_apy + funding_rate - borrow_apy
- Risk threshold: `exit_funding_rate_annualised` (default 0.5% annualised)

Below threshold, strategy emits EXIT instruction. Risk service flags positions with funding rate < 0 as
`CARRY_RISK_ELEVATED`.

### 5. Reward Token Risk (M2M Exposure)

Unclaimed EIGEN/ETHFI represent unrealised token exposure. If token price drops before sell:

- `unrealised_reward_pnl = accrued_amount × current_token_price`
- Alert if unrealised reward exposure > `max_reward_exposure_usd` (default $5,000)

Monitored via `eigen_claimable_usd` and `ethfi_claimable_usd` features.

## How Services Consume Client Config

### Strategy-Service

Reads client config at startup via `UnifiedCloudConfig`. Config controls:

- Which strategy categories are enabled
- `DeFiStrategyConfig.auto_claim`, `auto_sell`, `min_claim_value_usd`
- `DeFiStrategyConfig.max_leverage`, `target_notional_usd`

### Risk-and-Exposure-Service

Reads `ClientConfig.max_drawdown_pct` and `DefiClientConfig.min_health_factor` to set alert thresholds. Emits
`RISK_LIMIT_BREACH` events when limits exceeded.

### Position-Balance-Monitor-Service

Aggregates positions per `(client_id, strategy_id)`. Portfolio-level risk computed by joining all strategy positions for
the client.

### Execution-Service

Validates instructions against `allowed_protocols` and `allowed_chains` before submitting on-chain. Rejects instructions
for protocols not in the client's allowlist.

## UI Entitlements (Tab Gating)

UI entitlements are stored per `(user_id, org_id)` in Firestore. DeFi tabs are gated by `DEFI` category being in
`categories_enabled`. See:

- `unified-trading-system-ui/src/contexts/AuthContext.tsx` — entitlement loading
- `unified-trading-api-gateway/api_gateway/auth/entitlements.py` — server-side validation

## Demo Client: Patrick @ Bankelysium

For demo mode, the pre-seeded client is:

- `client_id`: `bankelysium-001`
- `org_id`: `bankelysium`
- Login: `patrick@bankelysium.com`
- Categories: `["DEFI"]` (Strategies/Sports/Predictions tabs locked)
- `share_class`: `ETH`
- `max_leverage`: `3.0`
- `min_health_factor`: `1.5`

## Key Files

| File                                                                   | Purpose                         |
| ---------------------------------------------------------------------- | ------------------------------- |
| `unified_api_contracts/internal/client_config.py`                      | `ClientConfig` schema (SSOT)    |
| `risk_and_exposure_service/engine/orchestrator.py`                     | Risk dimension computation      |
| `strategy_service/engine/strategies/defi_base_strategy.py`             | Reads client config limits      |
| `position_balance_monitor_service/core/portfolio_aggregator.py`        | Per-client position aggregation |
| `unified-trading-pm/codex/04-architecture/share-class-architecture.md` | Share class P&L isolation       |

## Related Docs

- `/codex/04-architecture/share-class-architecture.md` — Share class P&L isolation
- `/codex/04-architecture/defi-risk-monitoring.md` — DeFi-specific risk monitoring
- `/codex/09-strategy/architecture-v2/cross-cutting/reward-lifecycle.md` — Reward token risk (EIGEN/ETHFI M2M)
