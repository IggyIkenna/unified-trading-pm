---
doc_type: codex-ssot
title: Transfer Architecture
summary: >-
  Five transfer types (ON_CHAIN / CEX_WITHDRAWAL / CEX_INTERNAL / CUSTODY_TRANSFER / BRIDGE) each with a distinct
  execution path, confirmation mechanism, and events — plus per-venue wallet capabilities (which venues need a
  funding-to-trading internal move after deposit) and the DeFi treasury reserve-ratio (20/10/30) capital flow. Also
  carries the 2026-08-12 operator rulings on mirrored custody: strategy-layer PnL/balance tracking is identical whether
  collateral is mirrored or held, WalletMappingConfig is the per-client custody binding layer (VENUE_WALLET_CAPABILITIES
  stays pure venue physics), a cross-custodian move is a PERSISTED multi-hop route with per-hop status, and manual
  acknowledged transfers are part of the model rather than an exception.
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
authoritative_for:
  [
    five-transfer-type taxonomy + per-venue wallet capabilities,
    mirrored-custody routing model (per-client binding + multi-hop route + manual acknowledgement),
  ]
referenced_by:
  [
    /codex/04-architecture/transfer-coordinator.md,
    /codex/04-architecture/treasury-custody-flow.md,
    /codex/04-architecture/wallet-hierarchy-and-capital-flow.md,
    /codex/09-strategy/architecture-v2/cross-cutting/transfer-rebalance.md,
  ]
owner:
last_reviewed: 2026-09-13
code_refs:
---

# Transfer Architecture

## Overview

The system discriminates five transfer types, each with a different execution path, latency profile, and fee structure.
Transfer type determines which adapter handles execution, how confirmation works, and what events are emitted. The SSOT
for per-venue routing is `VenueWalletCapabilities` in UAC —
`unified_api_contracts/internal/domain/execution_service/transfer_types.py` (re-verified 2026-07-31; this doc previously
gave the path as `execution_service/transfer_types.py`, which does not exist — the module lives in UAC, not in the
execution-service package, even though its UAC sub-path is named after the consumer).

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

## Mirrored custody, multi-hop routes, and per-client binding (operator rulings 2026-08-12)

**The governing principle, verbatim from the operator:** _"we track our wallets as separate from a trading perspective
to monitor balances and keep things agnostic, but the adaptor we are using to handle the money determines how we
actually execute the instructions."_ Two consequences that must not be conflated:

- **Position / PnL / balance tracking is IDENTICAL whether collateral is mirrored or directly held.** The mirrored
  balance is what is tracked, exactly as an unmirrored balance would be. The strategy layer neither knows nor cares
  which custodian holds the asset — a strategy emits ONE transfer instruction and never names a rail.
- **Transfer ROUTING is where the custodian topology matters**, and it is resolved below the strategy layer from
  per-client configuration.

### The worked example this model must satisfy

Bybit + OKX under Copper custody; Binance under CEFFU. Client deposits to treasury, moves to the trading wallet (held at
Copper) — that is the collateral to mirror.

| Strategy instruction        | Underlying route                                                                                |
| --------------------------- | ----------------------------------------------------------------------------------------------- |
| Move 1 BTC to Bybit and OKX | Instruct **Copper** to mirror against each venue. No coin moves.                                |
| Move between Bybit and OKX  | Instruct **Copper** only — both venues sit under the same custodian's mirror.                   |
| Move OKX → Binance          | **Unmirror at Copper → physically move Copper→CEFFU on-chain → mirror at Binance.** Three hops. |

The third row is the shape everything else must accommodate: **one strategy instruction, N underlying hops, crossing a
custodian boundary.**

### RULING 1 — `WalletMappingConfig` is the per-client binding layer

Custody binding is **NOT** a global venue property. The same venue is direct for one client and custodied for another,
so:

- **`VENUE_WALLET_CAPABILITIES` stays pure venue PHYSICS** — what is _possible_ at a venue: where deposits land, whether
  a funding→trading move is required, whether withdrawal needs a whitelist, the CCXT params. Immutable venue facts,
  global.
- **`WalletMappingConfig` carries the per-client CHOICE** — which custodian, which venues are mirrored, treasury and
  trading wallet identities. Already per-share-class and GCS-loaded (`wallet-config/{chain_env}/wallet_mapping.json`),
  so this extends an existing surface rather than adding a third.
- **The router intersects the two.** Physics says what can be done; client config says what this client does.

Rejected alternatives, recorded so they are not re-proposed: keying `VENUE_WALLET_CAPABILITIES` by `(venue, client_id)`
mixes immutable venue facts with per-client policy and grows combinatorially; a third dedicated routing config adds
another overlapping SSOT surface. **The constraint set is (client_id, strategy_id) — never a hardcoded venue→custodian
map, of which there must be exactly one.**

### RULING 2 — a multi-hop transfer is a PERSISTED route plan with per-hop status

The coordinator expands one instruction into an explicit ordered route, persisted, with independent per-hop state:

```
TransferRoute(instruction_id, client_id)
  hop 1  UNMIRROR   OKX      @copper        status=DONE
  hop 2  ON_CHAIN   copper -> ceffu         status=PENDING   <-- resumable
  hop 3  MIRROR     BINANCE  @ceffu         status=NOT_STARTED
```

**Why persisted rather than an opaque adapter sequence:** a failure between hops leaves real collateral stranded
_between custodians_. Hop 2 must be retryable without replaying hop 1 — an unmirror is not idempotent with a re-mirror.
It also supplies the audit record the ledger's `CUSTODY_MOVE` event already expects. The strategy layer still observes
one instruction and one terminal status.

`AtomicInstruction` / `AtomicLeg` / `CompensationPolicy` were considered and NOT chosen: they exist for trade legs, and
compensation semantics for a half-moved custody balance differ from unwinding a trade.

### RULING 4 — share class is NOT a venue margin currency; funding routes are computed, not hardcoded

**The defect this replaces.** `_CARRY_BASIS_PERP_VENUE_BUNDLES` and `_FUNDING_DISPERSION_VENUES` in `catalog_carry.py`
attach a `ShareClass` to each venue — `("hyperliquid", "HYPERLIQUID", ShareClass.USDC)`, with comments like _"KRAKEN
takes USDC + USDT, USDC wins"_. **`ShareClass` is being used to encode the venue's margin currency.** Those are
different concepts:

- **Share class** = what the client subscribed in and is redeemed in. A property of the fund.
- **Venue margin currency** = what collateral the venue accepts. A property of the venue.

Conflating them means an ETH share class cannot trade a USDC-margined venue **by construction of the slot list**, and
`"USDC wins"` is a static pick where the right answer depends on what the client holds and which routes their config
permits. **Operator ruling: any share class can work on any venue in theory** — what varies is the route required to get
from share-class capital to acceptable collateral, and whether that route is permitted.

**The model: a funding-route feasibility graph per `(client_id, strategy_id)`.** The system must know what it has access
to — trading venues, custodians, **borrow/lend venues**, bank brokers — and from that derive which routes exist:

| Route              | Mechanism                                            | Risk the system must carry                                                                                            |
| ------------------ | ---------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| **Direct**         | Share-class asset IS accepted collateral             | none                                                                                                                  |
| **Convert**        | Swap share-class asset → required collateral         | depeg, and a residual short exposure to the sold asset — optionally perp-hedged (USD/USDT perps exist on some venues) |
| **Borrow against** | Post share-class asset, borrow the collateral        | borrow cost + liquidation; **gated by client restriction config, not universal**                                      |
| **Lend to offset** | Lend the share-class asset while borrowing the other | nets out roughly for USDC/USDT; leaves the depeg asymmetry                                                            |

The purpose is **route feasibility, not policy**: knowing Aave lets you borrow USDT against your holdings says the route
_exists_, not that the strategy _should_ take it. That keeps it opt-in. An ETH share class trading basis (borrow a
stable, buy spot, sell perps, pay borrow) must therefore be **expressible and then opted into**, never excluded by a
hardcoded catalogue row.

**What this must produce:** a slot whose funding route is infeasible under the client's constraints **fails loudly at
resolution time**, in the same way `_staked_basis_eligible()` already refuses to emit an infeasible (LST × perp_venue)
pair. Same pattern, one layer up.

**Boundary worth stating:** `ShareClassFxMatrix` keeps its role for **NAV conversion in the allocator** — that is an
accounting projection. It does NOT perform capital movement. A real conversion is a trade with slippage, fees and a
residual exposure someone owns, so it belongs in the route graph above, not in an FX matrix.

Tracked in
[the Elysium readiness plan](/plans/active/elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md) § H.15.

### Manual / acknowledged transfers are part of the model, not an exception

Some moves the system **cannot** execute: separately-managed accounts where the client must move funds to a main
account, prime-broker instructions, or simply missing credentials. The system must still **record** the transfer so the
strategy layer sees the balance move. This is an acknowledgement path — an externally-executed transfer booked in
canonical form — and it is what makes the model work across asset groups (a bookmaker deposit is the same shape as an
SMA sweep). It is NOT a rail: the rail axis describes _how money moves_, and "a human did it" is a statement about _who
executed_, so the two must stay separate fields.

### Known gaps as of 2026-08-12 (audited, tracked, NOT yet built)

| Gap                                                                                                                                                                                                      | Where it bites                                                                                                          |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| **CEFFU absent from every routing surface** — `custody_provider` is `copper`/`fireblocks`/`''`; zero venues bound to ceffu; `WalletMappingConfig.custodian` is `copper`/`fireblocks`/`mock`              | Binance cannot be routed via CEFFU at all                                                                               |
| **No mirroring in `CustodyProvider`** — Ceffu's `oes_*` methods sit OUTSIDE the protocol; Copper has no ClearLoop path (`clearloop` = zero source hits)                                                  | Callers using mirroring are coupled to Ceffu concretely, defeating agnosticism                                          |
| **No mirrored-vs-held distinction in `WalletType`** (`FUNDING`/`TRADING`/`SPOT`/`UNIFIED`/`ON_CHAIN`)                                                                                                    | A balance mirrored onto Binance is custodied at CEFFU — double-counting it misstates available margin and client assets |
| **No custody↔custody route**; no multi-hop representation                                                                                                                                                | The OKX→Binance row above is unexecutable                                                                               |
| **No manual/acknowledged transfer path** — `UNITY_WALLET_OP` and `IBKR_FUND_MOVE` are declared with ZERO consumers fleet-wide                                                                            | SMA and bookmaker moves are unrepresentable                                                                             |
| **FOUR overlapping transfer-type enums** — `transfer_types.TransferType` (5, this doc's SSOT), `architecture_v2.enums.TransferType` (7), `domain.defi.transfers.TransferType` (6), `BusTransferType` (5) | Any reader can cite a different "the" taxonomy; `architecture_v2`'s has no member docstrings at all                     |

Tracked in
[the Elysium readiness plan](/plans/active/elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md) § H.11.

## Related Docs

- [Kill Switch & Circuit Breaker](kill-switch-circuit-breaker.md) -- halt conditions that freeze transfers
- [Autonomous Recovery Matrix](autonomous-recovery-matrix.md) -- how transfers fit into recovery decisions
- [Execution Policy](/codex/04-architecture/execution-policy.md) -- bridge and withdrawal fee estimation
- [Custody Providers](custody-providers.md) -- Copper / CEFFU / LocalKey / Mock providers (single SSOT)
- [Wallet Hierarchy & Capital Flow](wallet-hierarchy-and-capital-flow.md) -- two-tier wallet model and share classes
