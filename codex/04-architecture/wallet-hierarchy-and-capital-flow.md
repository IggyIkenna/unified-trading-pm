# Wallet Hierarchy & Capital Flow Architecture

## Overview

The system manages client capital through a two-tier wallet hierarchy with automated capital flow between tiers. Each
strategy operates on an isolated hot wallet per chain. A treasury wallet per chain serves as the client-facing
deposit/withdrawal point.

## Wallet Hierarchy

Both wallet tiers are managed by the configured **custodian** (currently Copper.co, switchable). Clients
deposit/withdraw into the custodian's treasury wallet. The system moves funds to the custodian's trading wallet(s) for
strategy execution. The custodian name is a config parameter — switching providers requires only a new `CustodyProvider`
implementation, no strategy changes.

```
CLIENT                CUSTODIAN TREASURY WALLET     CUSTODIAN TRADING WALLETS (per strategy per chain)
                      (per chain)
                                                    ┌─ AAVE_LENDING (ETH chain)
Deposit ───────>  Treasury-ETH  ──── fund ────>     ├─ BASIS_TRADE (ETH chain)
Withdraw <──────  (client-facing)  <── rebalance ── ├─ RECURSIVE_STAKED (ETH chain)
                                                    └─ AMM_LP (ETH chain)

                  Treasury-ARB  ──── fund ────>     ├─ L2_BASIS (Arbitrum)
                  (bridged from ETH)                └─ MULTICHAIN_LENDING (Arbitrum)

                  Treasury-SOL  ──── fund ────>     ├─ SOL_BASIS (Solana)
                  (bridged from ETH)                └─ KAMINO_LENDING (Solana)

CeFi:             Funding Account ── transfer ──>   ├─ BASIS_TRADE (Hyperliquid sub-account)
(exchange-managed) (Binance/HL/OKX)                 ├─ BTC_BASIS (Binance sub-account)
                                                    └─ FUNDING_ARB (Bybit sub-account)
```

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

### Cross-Chain Deployment (Omnichain)

```
1. Strategy decides to deploy on Arbitrum
2. Instructions:
   a. TRANSFER hot-wallet-eth → treasury-eth (if needed)
   b. BRIDGE treasury-eth → treasury-arb (via Socket/Across)
   c. TRANSFER treasury-arb → hot-wallet-l2basis-arb
   d. Strategy deploys on Arbitrum
3. Position-balance-monitor tracks in-flight bridge capital as PENDING_BRIDGE
```

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
| **strategy-service**          | Capital allocation decisions. Emit TRANSFER instructions for treasury↔hot wallet. Reduce positions when treasury needs funding.   |
| **execution-service**         | Execute transfers via Copper signing. Handle bridge instructions for cross-chain. CeFi sub-account transfers via exchange API.     |
| **risk-and-exposure-service** | Aggregate exposure across all wallets (treasury + hot + in-flight). Per-strategy risk includes wallet isolation.                   |
| **pnl-attribution-service**   | Track P&L per hot wallet. Transfer costs (gas, bridge fees) as realized costs.                                                     |
| **alerting-service**          | Treasury threshold alerts. Large deposit/withdrawal notifications. Bridge completion tracking.                                     |
| **UAC**                       | Wallet config schemas. Chain↔wallet mappings. Copper integration types.                                                           |

## What Exists vs What Needs Building

| Component                         | Status               | Where                                            |
| --------------------------------- | -------------------- | ------------------------------------------------ |
| TRANSFER instruction type         | Exists               | strategy-service, execution-service              |
| BRIDGE instruction type           | Exists               | execution-service (Socket connector)             |
| Per-venue balance reading         | Exists               | position-balance-monitor (venue_balance_tracker) |
| On-chain balance reading          | Exists               | position-balance-monitor (Alchemy API)           |
| CeFi sub-account transfers        | Exists               | execution-service (exchange adapters)            |
| Treasury wallet config schema     | **Needs building**   | UAC                                              |
| Treasury threshold monitoring     | **Needs building**   | position-balance-monitor or alerting             |
| Auto-rebalance treasury↔hot      | **Needs building**   | strategy-service (meta-strategy or hook)         |
| Copper MPC signing integration    | **Needs building**   | execution-service                                |
| Per-client AUM tracking           | **Needs building**   | position-balance-monitor / IBOR                  |
| Deposit detection events          | **Partially exists** | position-balance-monitor                         |
| Cross-wallet exposure aggregation | **Needs building**   | risk-and-exposure-service                        |

## Security Model

- **Copper MPC**: No single party holds full key. Signing requires coordination.
- **Wallet isolation**: Strategy A can't access Strategy B's wallet.
- **Treasury access**: Only system can transfer treasury → hot wallet (no manual access).
- **Rate limiting**: Max transfer per hour configurable per wallet.
- **Alerting**: Any transfer > threshold triggers Telegram notification.
- **Audit trail**: All transfers logged via log_event() → GCS events bucket.
