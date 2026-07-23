---
doc_type: codex-ssot
title: Transfer Architecture
summary:
  Five transfer types (ON_CHAIN / CEX_WITHDRAWAL / CEX_INTERNAL / CUSTODY_TRANSFER / BRIDGE) each with a distinct
  execution path, confirmation mechanism, and events — plus per-venue wallet capabilities (which venues need a
  funding-to-trading internal move after deposit) and the DeFi treasury reserve-ratio (20/10/30) capital flow.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service, unified-trading-library]
scope: [engineer, admin]
tags: [transfers, execution, defi, cefi, treasury, custody, bridge]
related:
  [
    /codex/04-architecture/transfer-coordinator.md,
    /codex/04-architecture/treasury-custody-flow.md,
    /codex/04-architecture/wallet-hierarchy-and-capital-flow.md,
    /codex/04-architecture/custody-providers.md,
    /codex/04-architecture/kill-switch-circuit-breaker.md,
  ]
created: 2026-04-16
authoritative_for: [five-transfer-type taxonomy + per-venue wallet capabilities]
referenced_by:
  [
    /codex/04-architecture/transfer-coordinator.md,
    /codex/04-architecture/treasury-custody-flow.md,
    /codex/04-architecture/wallet-hierarchy-and-capital-flow.md,
    /codex/09-strategy/architecture-v2/cross-cutting/transfer-rebalance.md,
  ]
owner:
last_reviewed: 2026-05-17
code_refs:
---

# Transfer Architecture

## Overview

The system discriminates five transfer types, each with a different execution path, latency profile, and fee structure.
Transfer type determines which adapter handles execution, how confirmation works, and what events are emitted. The SSOT
for per-venue routing is `VenueWalletCapabilities` in UAC (`execution_service/transfer_types.py`).

## Transfer Types

| Type               | Mechanism                                                        | Latency                          | Fees              | Use Case                                         |
| ------------------ | ---------------------------------------------------------------- | -------------------------------- | ----------------- | ------------------------------------------------ |
| `ON_CHAIN`         | Direct blockchain transfer, signed via Copper (MPC) or local key | Minutes (confirmation-dependent) | Gas               | DeFi<>DeFi same-chain, DeFi<>CeFi                |
| `CEX_WITHDRAWAL`   | Exchange withdrawal to external address via CCXT `withdraw()`    | Minutes to hours                 | Withdrawal fee    | CeFi->CeFi cross-exchange, CeFi->DeFi            |
| `CEX_INTERNAL`     | Exchange internal transfer between wallet types via exchange API | Instant                          | None              | Funding->trading, spot->futures on same exchange |
| `CUSTODY_TRANSFER` | Transfer via custody provider (Copper MPC signing)               | 1-5s signing + blockchain time   | Gas               | Treasury->trading wallet, custodied moves        |
| `BRIDGE`           | Cross-chain bridge (Across protocol)                             | Minutes                          | Bridge + gas fees | Cross-chain capital movement                     |

## CEX Internal Transfer Endpoints

Each exchange exposes its own internal transfer API:

- **Binance**: `POST /sapi/v1/asset/transfer` -- universal transfer between wallet types (e.g. `MAIN_UMFUTURE`)
- **OKX**: `POST /api/v5/asset/transfer` -- asset transfer between account types (type `0` funding -> `18` trading)
- **Bybit**: `POST /v5/asset/transfer/inter-transfer` -- inter-account transfer

These are wrapped by CCXT `transfer()` with venue-specific params.

## Venue Wallet Capabilities

Each venue has a different wallet structure that determines whether an internal transfer is needed after deposit:

### CeFi

| Venue   | Deposit Target  | Requires Internal Transfer | Notes                                                |
| ------- | --------------- | -------------------------- | ---------------------------------------------------- |
| Binance | Funding wallet  | Yes (`MAIN_UMFUTURE`)      | Deposits land in funding, trading is on futures      |
| OKX     | Funding account | Yes (type `0` -> `18`)     | Deposits land in funding, trading on trading account |
| Bybit   | Unified account | No                         | Unified account -- deposits go directly to trading   |
| Deribit | Trading account | No                         | Direct to trading                                    |

### DeFi

| Venue                          | Wallet Type | Custody    | Internal Transfer |
| ------------------------------ | ----------- | ---------- | ----------------- |
| Aave, Uniswap, EtherFi, Morpho | On-chain    | Copper MPC | No                |
| Hyperliquid                    | On-chain    | Copper MPC | No (L1 deposit)   |
| Polymarket                     | On-chain    | Copper MPC | No                |

### Other

| Venue     | Wallet Type           | Internal Transfer |
| --------- | --------------------- | ----------------- |
| CME, CBOE | Traditional brokerage | N/A (no crypto)   |
| Betfair   | Direct to trading     | No                |

## External Transfer: Two Flavours

### 1. Direct Address-to-Address

Whitelisted addresses stored in system config. Used when we hold keys locally or via Copper. Full control over
transaction construction and signing.

### 2. Via Custodian (Copper)

MPC-signed transactions through the Copper API. The `CopperCustodyProvider` in `execution-service/custody/copper.py`
handles signing and submission. Supports all EVM chains.

**Toggle logic:** Use Copper when configured for the venue/chain, fall back to local key when Copper is not configured.
This is a per-venue config decision, not a global switch.

## CeFi Funding-to-Trading Flow

When a client deposits to a CeFi venue:

```
1. Deposit lands in funding wallet (Binance, OKX) or unified account (Bybit)
2. PBMS treasury_monitor detects balance increase
   -> emits DEPOSIT_DETECTED event
3. If venue requires_internal_transfer == True:
   a. Auto-initiate CEX_INTERNAL transfer (funding -> trading)
   b. Use CCXT transfer() with venue-specific params
   c. Emit CEX_INTERNAL_TRANSFER_COMPLETED
4. Funds available for trading
```

For Bybit and Deribit, step 3 is skipped -- deposits land directly in the trading account.

## DeFi Treasury Flow

Operates on the share class architecture (one treasury wallet per share class: USDC, ETH, BTC, SOL):

```
1. Client deposits -> treasury wallet (custodied by Copper)
2. Treasury monitor maintains reserve ratio:
   - Target: 20%
   - Low threshold: 10%  (TREASURY_LOW)
   - High threshold: 30% (TREASURY_HIGH)
3. When TREASURY_LOW (<10%):
   - Strategies must reduce positions
   - System emits TREASURY_LOW event
4. When TREASURY_HIGH (>30%):
   - Excess capital deployed to strategies
   - Strategy emits TransferInstruction
5. Treasury -> trading wallet: CUSTODY_TRANSFER via Copper create_transfer()
6. Cross-chain moves: BRIDGE via Across protocol
   - Cost estimated via bridge_cost_model.py
```

## Transfer Confirmation

Each transfer type has a different confirmation mechanism:

| Type               | Confirmation Method                                              | Polling |
| ------------------ | ---------------------------------------------------------------- | ------- |
| `ON_CHAIN`         | Wait for N blockchain confirmations (12 ETH, 1 for L2s)          | Yes     |
| `CEX_WITHDRAWAL`   | Poll exchange withdrawal status API                              | Yes     |
| `CEX_INTERNAL`     | Instant -- no confirmation needed                                | No      |
| `CUSTODY_TRANSFER` | Copper `poll_transaction_status()` then blockchain confirmations | Yes     |
| `BRIDGE`           | Bridge protocol status + destination chain confirmation          | Yes     |

On success: emit `TRANSFER_CONFIRMED`. On failure after retry exhaustion: emit `TRANSFER_FAILED`.

## Events

All transfers emit lifecycle events via unified-trading-library. Failures trigger Telegram + PagerDuty alerts.

| Event                             | When                                |
| --------------------------------- | ----------------------------------- |
| `TRANSFER_INITIATED`              | Transfer started                    |
| `TRANSFER_CONFIRMED`              | Transfer completed successfully     |
| `TRANSFER_FAILED`                 | Transfer failed after retries       |
| `CEX_INTERNAL_TRANSFER_COMPLETED` | Funding->trading internal move done |
| `DEPOSIT_DETECTED`                | PBMS detects inbound deposit        |
| `TREASURY_LOW`                    | Reserve ratio below 10%             |
| `TREASURY_HIGH`                   | Reserve ratio above 30%             |

## Related Docs

- [Kill Switch & Circuit Breaker](kill-switch-circuit-breaker.md) -- halt conditions that freeze transfers
- [Autonomous Recovery Matrix](autonomous-recovery-matrix.md) -- how transfers fit into recovery decisions
- [Execution Policy](../execution-policy.md) -- bridge and withdrawal fee estimation
- [Custody Providers](custody-providers.md) -- Copper / CEFFU / LocalKey / Mock providers (single SSOT)
- [Wallet Hierarchy & Capital Flow](wallet-hierarchy-and-capital-flow.md) -- two-tier wallet model and share classes
