---
doc_type: codex-ssot
title: Wallet Hierarchy & Capital Flow Architecture
summary:
  Two-tier wallet hierarchy (per-share-class treasury wallet to per-strategy hot wallets, custodian-managed) and the
  automated capital-flow model — reserve-ratio rebalancing, deposit/withdrawal instruction flows, strategy-initiated
  cross-chain bridging, and the WalletMappingConfig UAC schema keyed by share class (not chain).
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [alerting-service, execution-service, strategy-service]
scope: [engineer, admin]
tags: [wallet, treasury, capital-flow, defi, cefi, custody, uac, strategy]
related:
  [
    /codex/04-architecture/transfer-architecture.md,
    /codex/04-architecture/treasury-custody-flow.md,
    /codex/04-architecture/custody-providers.md,
    /codex/04-architecture/per-client-isolation-architecture.md,
  ]
created: 2026-03-30
authoritative_for: [two-tier wallet hierarchy + share-class treasury capital-flow model + WalletMappingConfig]
referenced_by:
  [
    /codex/04-architecture/chain-environment-resolution.md,
    /codex/04-architecture/custody-providers.md,
    /codex/04-architecture/defi-phase3-infrastructure.md,
    /codex/04-architecture/execution-modes-and-chain-resolution.md,
    /codex/04-architecture/transfer-architecture.md,
    /codex/04-architecture/treasury-custody-flow.md,
    /codex/15-runbooks/custody-onboarding-checklist.md,
    /codex/05-infrastructure/per-archetype-wallet-isolation.md,
  ]
owner:
last_reviewed: 2026-05-17
code_refs:
---

# Wallet Hierarchy & Capital Flow Architecture

## Overview

The system manages client capital through a two-tier wallet hierarchy with automated capital flow between tiers. Each
strategy operates on an isolated hot wallet (potentially on different chains). A treasury wallet per **share class**
serves as the client-facing deposit/withdrawal point.

## Wallet Hierarchy

Both wallet tiers are managed by the configured **custodian** (currently Copper.co, switchable). Clients
deposit/withdraw into the custodian's treasury wallet based on their fund's **share class** (base currency). The system
moves funds to the custodian's trading wallet(s) for strategy execution. The custodian name is a config parameter —
switching providers requires only a new `CustodyProvider` implementation, no strategy changes.

```
CLIENT                CUSTODIAN TREASURY WALLET       CUSTODIAN TRADING WALLETS (per strategy, any chain)
                      (per share class)
                                                      ┌─ AAVE_LENDING (ETH chain)
USDC ──────────>  Treasury-USDC  ──── fund ────>      ├─ BASIS_TRADE (ETH chain)
(on ETH/ARB)      (share class: USDC, lives on ETH)   └─ L2_BASIS (Arbitrum — strategy bridges internally)
                                    <── rebalance ──

ETH ───────────>  Treasury-ETH  ──── fund ────>       ├─ RECURSIVE_STAKED (ETH chain)
(on ETH)          (share class: ETH, lives on ETH)    └─ STAKED_BASIS (ETH chain)

SOL/USDC ──────>  Treasury-SOL  ──── fund ────>       ├─ SOL_BASIS (Solana)
(on Solana)       (share class: SOL, lives on SOL)    └─ SOL_LENDING (Solana)

BTC ───────────>  Treasury-BTC  ──── fund ────>       └─ BTC_LENDING (Bitcoin/wrapped)
(on Bitcoin)      (share class: BTC, lives on BTC)

CeFi:             Funding Account ── transfer ──>     ├─ BASIS_TRADE (Hyperliquid sub-account)
(exchange-managed) (Binance/HL/OKX)                   ├─ BTC_BASIS (Binance sub-account)
                                                      └─ FUNDING_ARB (Bybit sub-account)
```

**Key principle:** Treasury is keyed by **share class** (the fund's base currency), not chain. Clients deposit into the
treasury for their share class. The chain is just where that treasury wallet lives. Once funds move to trading wallets,
the strategy decides which chains and venues to use. There is no bridging at deposit time.

**Bridging only happens within strategy execution** — e.g., a CROSS_CHAIN_YIELD_ARB strategy might bridge USDC from
Ethereum to Arbitrum to chase better yields. That's a strategy-level BRIDGE instruction, not a deposit flow.

## Capital Allocation Model

### DeFi (On-Chain)

| Wallet      | % of AUM           | Purpose                     | Speed   |
| ----------- | ------------------ | --------------------------- | ------- |
| Treasury    | 20% (configurable) | Client deposits/withdrawals | Instant |
| Hot wallets | 80% (configurable) | Strategy execution          | Instant |

**Rebalancing rules:**

- Treasury < min_threshold (e.g. 10%) → strategies reduce positions → funds flow hot → treasury
- Treasury > max_threshold (e.g. 30%) → excess flows treasury → hot wallets → strategies increase
- Rebalancing is a **strategy instruction** — the strategy emits WITHDRAW + TRANSFER instructions
- Position-balance-monitor detects the threshold breach and triggers via event

### CeFi (Exchange)

| Wallet               | % of AUM          | Purpose                   | Speed   |
| -------------------- | ----------------- | ------------------------- | ------- |
| Funding/Spot account | 0% (pass-through) | Client deposits land here | Instant |
| Trading sub-account  | 100%              | Strategy execution        | Instant |

No buffer needed — exchanges handle deposits/withdrawals internally. Client deposits into funding account, system
transfers to trading sub-account immediately.

### Sports

No treasury/hot wallet split. Single wallet per venue. Simpler capital structure.

## Capital Flow — Instruction Types

### Client Deposit (DeFi)

```
1. Client deposits USDC to Treasury-ETH wallet (detected by position-balance-monitor)
2. Event: DEPOSIT_DETECTED {wallet: treasury-eth, amount: 100000, token: USDC}
3. Strategy evaluates: treasury at 35% > max_threshold 30%
4. Strategy emits: TRANSFER treasury-eth → hot-wallet-aave-eth (USDC, $15000)
5. Strategy emits: TRANSFER treasury-eth → hot-wallet-basis-eth (USDC, $10000)
6. Strategies increase positions proportionally
```

### Client Withdrawal (DeFi)

```
1. Client requests withdrawal of $50000
2. If treasury has sufficient funds: instant withdrawal from treasury
3. If treasury < withdrawal amount:
   a. Event: TREASURY_LOW {wallet: treasury-eth, balance: 30000, requested: 50000}
   b. Strategies receive REDUCE_POSITION signal
   c. Strategies emit WITHDRAW + TRANSFER instructions (hot → treasury)
   d. Once treasury funded: withdrawal completes
```

### Cross-Chain Rebalancing (Strategy-Initiated Only)

Bridging is a **strategy execution decision**, not a deposit flow. It only happens when a strategy needs to move capital
between chains for yield optimization.

```
1. CROSS_CHAIN_YIELD_ARB strategy detects better APY on Optimism vs Arbitrum
2. Instructions:
   a. WITHDRAW hot-wallet-arb (Aave Arbitrum) → free capital
   b. BRIDGE hot-wallet-arb → hot-wallet-opt (via Socket/Across)
   c. LEND hot-wallet-opt → Aave Optimism pool
3. Position-balance-monitor tracks in-flight bridge capital as PENDING_BRIDGE
```

**Not used for:** Client deposits (deposit natively on target chain) or initial strategy funding (treasury funds trading
wallet on the same chain).

### CeFi Venue Funding

```
1. Client deposits USDT to Binance funding account (detected via exchange API)
2. System transfers: funding → trading sub-account (exchange internal, instant, no gas)
3. Strategy deploys: TRANSFER margin to perp sub-account + TRADE
4. On withdrawal: reverse flow
```

## Custody — Copper Integration

All wallet private keys managed by **Copper.co** (MPC custody):

- Key never assembled in one place (split across Copper + client + backup)
- Signing latency: ~1-2 seconds (acceptable for DeFi, fine for batch)
- API integration: `POST /sign-transaction` with raw tx bytes
- Supports EVM chains natively, Solana support in progress
- Insurance coverage on custodied assets

**Integration point:** execution-service signs transactions via Copper API instead of raw private key from Secret
Manager. The interface is the same — execution-service calls `sign_and_submit(tx)`, implementation routes to Copper.

```python
# Current (Secret Manager key):
pk = secret_client.get_secret("eth-trading-wallet-pk")
signed = web3.eth.account.sign_transaction(tx, pk)

# With Copper:
signed = copper_client.sign_transaction(tx, wallet_id="hot-wallet-aave-eth")
# Copper handles MPC signing internally
```

## Configuration Schema

### WalletMappingConfig (System-Level — UAC)

Defined in `unified_api_contracts.internal.domain.defi.wallet_config`. This is the SSOT for all wallet mappings per
chain environment. Loaded from GCS at: `wallet-config/{chain_env}/wallet_mapping.json`.

**Dataclass hierarchy:**

| Class                     | Purpose                                                                         |
| ------------------------- | ------------------------------------------------------------------------------- |
| `WalletMappingConfig`     | Top-level: custodian, chain_env, share_classes map, reserve thresholds          |
| `ShareClassWalletMapping` | Per-share-class: treasury wallet + list of trading wallets                      |
| `TradingWalletConfig`     | Per-strategy wallet: wallet_id, address, strategy_id, chain, max_allocation_usd |
| `WalletConfig`            | Single wallet: wallet_id, address, chain, label                                 |

**Top-level fields:**

| Field               | Type                                 | Default | Description                          |
| ------------------- | ------------------------------------ | ------- | ------------------------------------ |
| `custodian`         | `str`                                | —       | `"copper"`, `"fireblocks"`, `"mock"` |
| `chain_env`         | `str`                                | —       | `"mainnet"`, `"testnet"`, `"fork"`   |
| `share_classes`     | `dict[str, ShareClassWalletMapping]` | `{}`    | Per-share-class wallet mappings      |
| `reserve_pct`       | `Decimal`                            | `20`    | Target treasury reserve % of AUM     |
| `min_threshold_pct` | `Decimal`                            | `10`    | Below this: TREASURY_LOW event       |
| `max_threshold_pct` | `Decimal`                            | `30`    | Above this: TREASURY_HIGH event      |

**Helper methods:**

- `get_treasury_address(share_class)` — returns treasury wallet address for a share class
- `get_treasury_chain(share_class)` — returns the chain where the treasury wallet lives
- `get_trading_address(share_class, strategy_id)` — returns trading wallet address for a strategy
- `get_all_strategy_ids()` — returns all strategy IDs with trading wallets across all share classes

**GCS path helper:** `wallet_config_gcs_path(chain_env)` returns `"wallet-config/{chain_env}/wallet_mapping.json"`.

**Example config (testnet):**

```json
{
  "custodian": "copper",
  "chain_env": "testnet",
  "reserve_pct": "20",
  "min_threshold_pct": "10",
  "max_threshold_pct": "30",
  "share_classes": {
    "USDC": {
      "share_class": "USDC",
      "treasury_wallet": {
        "wallet_id": "vault-usdc-sep",
        "address": "0x...",
        "chain": "ETHEREUM"
      },
      "trading_wallets": [
        {
          "wallet_id": "trading-aave-sep",
          "address": "0x...",
          "strategy_id": "AAVE_LENDING",
          "chain": "ETHEREUM"
        },
        {
          "wallet_id": "trading-l2-basis-sep",
          "address": "0x...",
          "strategy_id": "L2_BASIS",
          "chain": "ARBITRUM"
        }
      ]
    },
    "SOL": {
      "share_class": "SOL",
      "treasury_wallet": {
        "wallet_id": "vault-sol-devnet",
        "address": "7Ec...",
        "chain": "SOLANA"
      },
      "trading_wallets": [
        {
          "wallet_id": "trading-sol-basis-devnet",
          "address": "Fg6...",
          "strategy_id": "SOL_BASIS",
          "chain": "SOLANA"
        }
      ]
    }
  }
}
```

A `testnet_wallet_mapping.json` fixture exists for development and integration testing.

### Per-Strategy Wallet Config (strategy config JSON)

```json
{
  "strategy_id": "DEFI_ETH_YLD_AAVE_USDC_HUF_1H",
  "wallet_config": {
    "custodian": "copper",
    "chain": "ETHEREUM",
    "trading_wallet_id": "trading-aave-eth",
    "trading_wallet_address": "0x1234...abcd",
    "treasury_wallet_id": "vault-eth-main",
    "treasury_wallet_address": "0x5678...efgh",
    "treasury_reserve_pct": 20,
    "treasury_min_threshold_pct": 10,
    "treasury_max_threshold_pct": 30,
    "max_deploy_pct": 95
  }
}
```

### CeFi Wallet Config

```json
{
  "strategy_id": "DEFI_ETH_BASIS_MULTI_HUF_1H_V1",
  "cefi_wallet_config": {
    "venue": "HYPERLIQUID",
    "funding_account_id": "main",
    "trading_sub_account_id": "basis-eth-1",
    "auto_transfer_on_deposit": true,
    "treasury_reserve_pct": 0
  }
}
```

### Custodian Config (system-level, not per-strategy)

```json
{
  "custody": {
    "provider": "copper",
    "api_url": "https://api.copper.co/platform",
    "credentials_secret": "copper-api-key",
    "sandbox_api_url": "https://api.sandbox.copper.co/platform",
    "sandbox_credentials_secret": "copper-sandbox-api-key"
  }
}
```

The `custodian` field in wallet_config references this system-level config. To switch providers (e.g. Fireblocks),
change the system-level `custody.provider` and add the new `CustodyProvider` implementation. Per-strategy wallet IDs
remain the same.

## System Integration Points

| Service                       | Responsibility                                                                                                                     |
| ----------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| **position-balance-monitor**  | Read balances per wallet per chain. Detect deposits. Track treasury vs hot wallet split. Emit TREASURY_LOW / TREASURY_HIGH events. |
| **strategy-service**          | Capital allocation decisions. Emit TRANSFER instructions for treasury↔hot wallet. Reduce positions when treasury needs funding.    |
| **execution-service**         | Execute transfers via Copper signing. Handle bridge instructions for cross-chain. CeFi sub-account transfers via exchange API.     |
| **risk-and-exposure-service** | Aggregate exposure across all wallets (treasury + hot + in-flight). Per-strategy risk includes wallet isolation.                   |
| **pnl-attribution-service**   | Track P&L per hot wallet. Transfer costs (gas, bridge fees) as realized costs.                                                     |
| **alerting-service**          | Treasury threshold alerts. Large deposit/withdrawal notifications. Bridge completion tracking.                                     |
| **UAC**                       | Wallet config schemas. Chain↔wallet mappings. Copper integration types.                                                            |

## What Exists vs What Needs Building

| Component                         | Status             | Where                                                   |
| --------------------------------- | ------------------ | ------------------------------------------------------- |
| TRANSFER instruction type         | **Working**        | strategy-service, execution-service                     |
| BRIDGE instruction type           | **Working**        | execution-service (Socket connector)                    |
| Per-venue balance reading         | **Working**        | position-balance-monitor (venue_balance_tracker)        |
| On-chain balance reading          | **Working**        | position-balance-monitor (Alchemy API)                  |
| CeFi sub-account transfers        | **Working**        | execution-service (exchange adapters)                   |
| WalletMappingConfig schema        | **Working**        | UAC `internal/domain/defi/wallet_config.py`             |
| GCS wallet config path            | **Working**        | `wallet-config/{chain_env}/wallet_mapping.json`         |
| Testnet wallet mapping fixture    | **Working**        | `testnet_wallet_mapping.json`                           |
| CopperCustodyProvider             | **Working**        | execution-service `custody/copper.py` (HMAC-SHA256 MPC) |
| LocalKeyCustodyProvider           | **Working**        | execution-service `custody/local_key.py` (dev only)     |
| MockCustodyProvider               | **Working**        | execution-service `custody/mock.py`                     |
| Custody factory                   | **Working**        | execution-service `custody/factory.py`                  |
| Treasury threshold monitoring     | **Needs building** | position-balance-monitor or alerting                    |
| Auto-rebalance treasury↔hot       | **Needs building** | strategy-service (meta-strategy or hook)                |
| Per-client AUM tracking           | **Needs building** | position-balance-monitor / IBOR                         |
| Deposit detection events          | **Partially**      | position-balance-monitor                                |
| Cross-wallet exposure aggregation | **Needs building** | risk-and-exposure-service                               |

## Security Model

- **Copper MPC**: No single party holds full key. Signing requires coordination.
- **Wallet isolation**: Strategy A can't access Strategy B's wallet.
- **Treasury access**: Only system can transfer treasury → hot wallet (no manual access).
- **Rate limiting**: Max transfer per hour configurable per wallet.
- **Alerting**: Any transfer > threshold triggers Telegram notification.
- **Audit trail**: All transfers logged via log_event() → GCS events bucket.
