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
    decided BRIDGE execution architecture (BridgeRouter + SocketBridgeConnector for EVM + new WormholeBridgeConnector for Solana),
  ]
referenced_by:
  [
    /codex/04-architecture/transfer-coordinator.md,
    /codex/04-architecture/treasury-custody-flow.md,
    /codex/04-architecture/wallet-hierarchy-and-capital-flow.md,
    /codex/09-strategy/architecture-v2/cross-cutting/transfer-rebalance.md,
  ]
owner:
last_reviewed: 2026-08-19
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

> **⚠️ Re-verified 2026-08-19: this local 5-member taxonomy no longer exists in code.** The `execution_service
.transfer_types.TransferType` enum this table mirrored was **deleted 2026-08-14** — resolved as a strict subset of
> `BusTransferType` (the transfer-type SSOT, `unified_api_contracts.canonical.crosscutting.transfer_events`, 13
> members) per the workspace's shadow-SSOT-type rule, with the source-value mapping preserved verbatim in that
> module's header comment. The table below is kept as a simplified execution-path summary for the five mechanisms
> still meaningfully distinct at this doc's level of detail, but for the authoritative type list use
> `/codex/09-strategy/architecture-v2/cross-cutting/transfer-rebalance.md` § "Transfer types — `BusTransferType`, 13
> members" — do not cite this table as "the" enum.

| Type               | Mechanism                                                                                                                                                                                                                                                                                       | Latency                          | Fees              | Use Case                                         |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------- | ----------------- | ------------------------------------------------ |
| `ON_CHAIN`         | Direct blockchain transfer, signed via Copper (MPC) or local key                                                                                                                                                                                                                                | Minutes (confirmation-dependent) | Gas               | DeFi<>DeFi same-chain, DeFi<>CeFi                |
| `CEX_WITHDRAWAL`   | Exchange withdrawal to external address via CCXT `withdraw()`                                                                                                                                                                                                                                   | Minutes to hours                 | Withdrawal fee    | CeFi->CeFi cross-exchange, CeFi->DeFi            |
| `CEX_INTERNAL`     | Exchange internal transfer between wallet types via exchange API                                                                                                                                                                                                                                | Instant                          | None              | Funding->trading, spot->futures on same exchange |
| `CUSTODY_TRANSFER` | Transfer via custody provider (Copper MPC signing)                                                                                                                                                                                                                                              | 1-5s signing + blockchain time   | Gas               | Treasury->trading wallet, custodied moves        |
| `BRIDGE`           | **corrected 2026-08-19** — `SocketBridgeConnector`, a Socket v2 aggregator selecting the best route across Across / Stargate / Hop / CCTP / LayerZero / LiFi (previously mis-stated as "Across protocol" directly — Across is one of the six protocols Socket routes across, not the mechanism) | Minutes                          | Bridge + gas fees | Cross-chain capital movement                     |

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
| Kalshi    | Direct to trading     | No                |

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
6. Cross-chain moves: BRIDGE via SocketBridgeConnector (Socket v2 aggregator across Across/Stargate/Hop/CCTP/LayerZero/LiFi;
   corrected 2026-08-19 -- previously named "Across protocol" directly, see § "Transfer Types" above)
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

| Gap                                                                                                                                                                                                                                                                                                                                              | Where it bites                                                                                                          |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------- |
| **CEFFU absent from every routing surface** — `custody_provider` is `copper`/`fireblocks`/`''`; zero venues bound to ceffu; `WalletMappingConfig.custodian` is `copper`/`fireblocks`/`mock`                                                                                                                                                      | Binance cannot be routed via CEFFU at all                                                                               |
| **No mirroring in `CustodyProvider`** — Ceffu's `oes_*` methods sit OUTSIDE the protocol; Copper has no ClearLoop path (`clearloop` = zero source hits)                                                                                                                                                                                          | Callers using mirroring are coupled to Ceffu concretely, defeating agnosticism                                          |
| **No mirrored-vs-held distinction in `WalletType`** (`FUNDING`/`TRADING`/`SPOT`/`UNIFIED`/`ON_CHAIN`)                                                                                                                                                                                                                                            | A balance mirrored onto Binance is custodied at CEFFU — double-counting it misstates available margin and client assets |
| **No custody↔custody route**; no multi-hop representation                                                                                                                                                                                                                                                                                        | The OKX→Binance row above is unexecutable                                                                               |
| **No manual/acknowledged transfer path** — `UNITY_WALLET_OP` and `IBKR_FUND_MOVE` are declared with ZERO consumers fleet-wide                                                                                                                                                                                                                    | SMA and bookmaker moves are unrepresentable                                                                             |
| ~~**FOUR overlapping transfer-type enums**~~ — **RESOLVED 2026-08-12/14.** Unioned onto `BusTransferType` (13 members, `unified-api-contracts@4663daf908`); `transfer_types.TransferType` (the local 5-member enum this row used to call "this doc's SSOT") was then deleted 2026-08-14 as a strict subset. See § "Transfer Types" banner above. | n/a — closed                                                                                                            |

Tracked in
[the Elysium readiness plan](/plans/active/elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md) § H.11.

## Bridging execution reality (verified 2026-08-19) — the DECIDED architecture

### Current state: three dispatch surfaces, zero live production bridge execution

A workspace-wide re-verification found `BRIDGE` genuinely modeled end-to-end on the **emit** side —
`strategy-service/strategy_service/transfer_coordinator.py`'s netting logic carries `BusTransferType.BRIDGE` generically
(rail=`on_chain`, `chain_id`/`dest_chain_id` fields), real and tested. On the **consume** side (execution-service), there
are three separate surfaces that could plausibly dispatch a bridge, and as of this pass none of them do, for three
different reasons:

1. **`TransferCoordinator`** (`execution_service/transfer_coordinator.py`) — the intended single entry point, but it has
   **zero production construction sites workspace-wide** (grep-confirmed: not imported, not built, not referenced in
   `app.py` or any wiring module — only its own unit tests construct it). Its `BRIDGE` routing-table row also named a
   fabricated target; see `/codex/04-architecture/transfer-coordinator.md`'s routing table for that fix.
2. **`TransferWiring` / `CompositeTransferAdapter`** (`execution_service/engine/transfers/{wiring,factory}.py`) — real
   production wiring, genuinely called at startup (`api/app.py` calls `build_transfer_wiring(config)`). But
   `CompositeTransferAdapter` only implements `execute_internal_transfer` / `execute_withdrawal` /
   `execute_onchain_transfer` / `get_transfer_status` / `get_balance` — **no bridge method exists on it at all.**
3. **`SocketBridgeConnector` / `CCTPBridgeConnector`** (`defi_execution/protocols/bridge.py`, `cctp.py`) — real and
   live-capable: `SocketBridgeConnector.bridge()` was fixed 2026-08-14 (per its own docstring) to call Socket's
   `/build-tx` endpoint, approve the input token, and sign+broadcast a real transaction — no longer the quote-only
   silent-success stub it used to be. Both connectors implement the `BaseBridgeConnector` ABC
   (`bridge()`/`get_bridge_status()`/`get_bridge_quotes()`/`get_supported_chains()`). But **zero production call sites**
   dispatch into either connector — the only references outside `bridge.py`/`cctp.py` themselves are comments in
   `kamino.py` and `bridge_cost_model.py` pointing at them as a future integration.

**Net effect:** the bridge is built and adapter-injectable, but nothing in the live dispatch path calls it. This is the
same shape as `/codex/09-strategy/architecture-v2/cross-cutting/transfer-rebalance.md`'s IMPLEMENTATION STATUS box
("the whole rail below it is built and adapter-injected; the near end is disconnected") — that box tracks the
producer-side gap (nothing emits `TransferIntent`), this section tracks the matching consumer-side gap (nothing routes
`BRIDGE` once emitted).

### The decision (operator ruling 2026-08-19) — this replaces the prior pass's "genuine open questions" 1 and 2

The operator has now decided the two open bridge-provider questions the prior pass flagged. This is buildable spec, not
an open question anymore:

1. **EVM↔EVM bridging: wire up the EXISTING `SocketBridgeConnector`.** It is already correctly built — a Socket v2
   aggregator picking the best route across Across / Stargate / Hop / CCTP / LayerZero / LiFi — the gap is purely that
   nothing calls it in production (§ above). **No new bridge connector is needed for EVM↔EVM.**
2. **EVM↔Solana bridging: build a NEW `WormholeBridgeConnector`.** Verified zero hits for this name or for "Wormhole" as
   an implemented connector anywhere in the workspace today (the only prior mention is a docstring example on an
   unrelated ledger-event enum). Wormhole was chosen because it is the most liquid, most battle-tested EVM↔Solana
   bridge with general token support — unlike CCTP, which is USDC-only and already has its own connector
   (`CCTPBridgeConnector`) reserved for that narrower EVM↔EVM/USDC-native use.
3. **Routing: a new `BridgeRouter`** at the execution-service dispatch layer selects the adapter by destination chain
   family — EVM destination → `SocketBridgeConnector`, Solana destination → `WormholeBridgeConnector` — both behind one
   common interface so the provider choice stays swappable later (operator's explicit requirement: "it can change
   because it's an adapter"). `BaseBridgeConnector` already exists as that common interface for the EVM case; extending
   it (or its replacement) to also cover a Solana destination is the prerequisite below, not a separate design.
   `BridgeRouter` is what `TransferCoordinator`'s `BRIDGE` row should ultimately target once `TransferCoordinator`
   itself gets a production construction site (a distinct, still-open gap — see
   `/codex/04-architecture/transfer-coordinator.md`).

### Prerequisite: the chain-identifier type is EIP-155-only and cannot represent Solana

This is the structural blocker item 2 depends on, verified at every layer that would need to carry a Solana
destination:

- **`TransferIntent.chain_id` / `dest_chain_id`** (UAC `canonical/crosscutting/transfer_events.py`) — both typed plain
  `int`, docstring says "EIP-155". Same shape independently in strategy-service's own `TransferRequest`
  (`strategy_service/transfer_coordinator.py`).
- **`BaseBridgeConnector.bridge()` / `get_bridge_quotes()`** (`defi_execution/protocols/bridge.py`) — `source_chain_id:
int`, `dest_chain_id: int` baked into the ABC's method signatures. Every chain reference throughout `bridge.py` is
  `int`-typed — the connector's chain tables are EVM-only by construction, not by omission.
- **`BridgeProtocol`** (UAC `internal/domain/defi/transfers.py`) — 8 members (`NATIVE`, `STARGATE`, `ACROSS`, `HOP`,
  `LAYERZERO`, `SOCKET`, `LIFI`, `CCTP`). No `WORMHOLE` member.
- **`CHAIN_BRIDGE_GRAPH`** (UAC `canonical/crosscutting/defi.py`) — has **zero edges touching `ChainKind.SOLANA`**,
  even though `ChainKind.SOLANA` already exists as an enum member one layer up (used by strategy archetype configs'
  `allowed_chains` and MTDS adapter dispatch — the enum's own docstring already describes Solana as a "non-EVM chain...
  with separate RPC template dicts"). The chain-family split this project needs already exists at the archetype/adapter
  layer; it simply never propagated down into the transfer/bridge layer's `int`-typed fields.

**What needs building, concretely:** a broader chain-identifier type replacing the bare `int` on `TransferIntent
.chain_id`/`dest_chain_id` and on `BaseBridgeConnector`'s bridge-facing method signatures — e.g. a discriminated union
or a `(chain_family, chain_specific_address)` pair (EVM branch carries the existing EIP-155 `int`; Solana branch carries
a base58 program/wallet address) — plus a `WORMHOLE` member on `BridgeProtocol` and the corresponding
`CHAIN_BRIDGE_GRAPH` edges. The exact shape is an implementation call for whoever builds it, but it must land in BOTH
the UAC contract layer (`TransferIntent`, `BridgeProtocol`, `CHAIN_BRIDGE_GRAPH`) and the execution-service connector
layer (`BaseBridgeConnector`, the new `WormholeBridgeConnector`) — extending only one side leaves the other unable to
express a Solana-destined intent end-to-end.

### Still genuinely open (operator has NOT decided these — do not treat as resolved)

- Whether fixing `RecursiveLoopOrchestrator._submit_flash_loan()`'s live-mode stub (see
  `/codex/04-architecture/flash-loan-receiver.md` § "Live-mode flash-loan submission is stubbed") is in scope now. This
  is atomic on-chain flash-loan execution, a structurally different mechanism from the venue-to-venue `BRIDGE` transfers
  this section covers — not the same gap, and not decided.
- Whether a dedicated atomic-execution SSOT doc (covering `AtomicBundleExecutor` + the `RecursiveLeverageReceiver` flash
  flows together) should be created. Not decided.

## Custodian-mediated collateral delegation (`CUSTODIAN_COLLATERAL_DELEGATION`, 2026-08-22)

> **Status: design ruled, build tracked in
> [`/plans/active/w23_pod_collateral_delegation_transfer_rail_2026_08_22.md`](/plans/active/w23_pod_collateral_delegation_transfer_rail_2026_08_22.md)
> (+ finalize). Not yet built as of this writing.**

POD (first DeFi allocator client) is building an API where we instruct "move X asset from venue A to venue B for
fund Y" and POD internally resolves custodian address + exchange account and executes it — we never see a wallet
address and never sign anything (WhatsApp thread with POD's Timo, 2026-08-21/22). This is mechanically distinct from
every existing `BusTransferType` member: not CCXT (`CEX_WITHDRAW`/`SUBACCOUNT_MOVE`), not on-chain
(`ON_CHAIN`/`BRIDGE`/`CUSTODY_TRANSFER`), and not signing-based like Copper/CEFFU's `CustodyProvider`.

**Operator architecture ruling, 2026-08-22**: do not force this into `CustodyProvider` — treat it as one more
instruction on the same unified `TransferIntent` path every other rail already uses. Strategy states `(from_venue,
to_venue, asset, amount)`; execution-service's adapter absorbs the venue/custodian-specific mechanics. This composes
directly with this doc's existing "manual acknowledged transfers are part of the model rather than an exception"
principle above — POD is one more mechanism reaching the same single source of truth for balances (a "wallet"
abstraction regardless of whether it's an on-chain address, a CEX sub-account, or opaque custodian-internal state we
can't read directly and must poll/wait on), not a special case.

- **New rail**: `BusTransferType.CUSTODIAN_COLLATERAL_DELEGATION`, `TransferRail.OTHER` (same family as
  `UNITY_WALLET_OP`/`IBKR_FUND_MOVE` — neither CCXT nor on-chain). Generic, not POD-specific — any future custodian
  offering the same instruct-and-confirm model reuses it.
- **Adapter wiring**: follows the `BRIDGE` precedent exactly — a duck-typed `execute_collateral_delegation` method on
  `TransferAdapter` implementations (not a required `Protocol` member, so it can't break existing fake adapter test
  doubles), dispatched via `TransferHandler._execute_custodian_delegation_transfer`. Confirmation reuses the existing
  rail-agnostic `TransferConfirmationPoller`/`get_transfer_status()` unchanged.
- **Restrictions registry**: which venue-pairs a custodian can move between lives in the UAC capability registry
  (`unified_api_contracts.registry.capability`'s `SourceCapability`/`register_capability`), not hardcoded in
  execution-service — this is the "restrictions" mechanism the operator's ruling calls for.
- **Balance pre-check**: POD exposes no balance-query endpoint (confirmed absent from the WhatsApp thread), so the
  pre-flight check reads PBMS's balances projection (epic `system_readiness_master.md` W9 "Account balances: the
  single strategy I/O"), not POD directly.

### Proposed external API — pending POD's confirmation

Draft sent to POD 2026-08-22, field names chosen to map near-1:1 onto `TransferIntent`/`TransferResult` (below) so the
real `LivePodCollateralAdapter` needs minimal translation once POD builds to it.

**Submit** — `POST /v1/collateral-transfers`

| Field            | Type               | Maps to (our side)                  | Notes                                                                     |
| ---------------- | ------------------ | ----------------------------------- | ------------------------------------------------------------------------- |
| `instruction_id` | `string` (uuid)    | `TransferIntent.idempotency_key`    | resubmitting the same id returns the cached result, never double-executes |
| `fund_id`        | `string`           | POD-side mapping of our `client_id` | static 1x mapping, not renegotiated per call                              |
| `from_venue`     | `string`           | `TransferIntent.source_venue`       | canonical venue code                                                      |
| `to_venue`       | `string`           | `TransferIntent.dest_venue`         |                                                                           |
| `asset`          | `string`           | `TransferIntent.asset`              |                                                                           |
| `amount`         | `string` (decimal) | `TransferIntent.amount`             | decimal string, never float                                               |
| `requested_at`   | `string` (ISO8601) | `TransferIntent.timestamp`          | UTC                                                                       |

Sync ack: `instruction_id` (echoed), `pod_reference_id` (POD's own tracking id, stored alongside ours),
`status` (`ACCEPTED`/`REJECTED`), `reject_reason` (closed-set code, populated only if `REJECTED`), `accepted_at`.

**Status** — `GET /v1/collateral-transfers/{instruction_id}`, plus a webhook push if POD can offer one (saves both
sides a poll loop): `pod_reference_id`, `status` (`ACCEPTED`/`PROCESSING`/`COMPLETED`/`FAILED`/`REJECTED` — maps onto
our `TransferStatus.PENDING`/`CONFIRMED`/`FAILED`, `PROCESSING`/`ACCEPTED` both collapse to `PENDING` on our side),
`requested_amount`, `settled_amount` (only if it can legitimately differ), `completed_at`, `error_code` + `error_message`
(closed set, `FAILED` only).

**Open questions for POD** (mirrors the same class of gap CEFFU's stub left open — worth asking upfront): decimal
precision per asset; sync-only vs webhook vs poll; rate limits / minimum transfer amount; sandbox base URL + test
credentials; whether POD's venue codes match ours or need a translation table; auth (HMAC-SHA256 matching our Copper
convention, or a different scheme).

## Related Docs

- [Kill Switch & Circuit Breaker](kill-switch-circuit-breaker.md) -- halt conditions that freeze transfers
- [Autonomous Recovery Matrix](autonomous-recovery-matrix.md) -- how transfers fit into recovery decisions
- [Execution Policy](/codex/04-architecture/execution-policy.md) -- bridge and withdrawal fee estimation
- [Custody Providers](custody-providers.md) -- Copper / CEFFU / LocalKey / Mock providers (single SSOT)
- [Wallet Hierarchy & Capital Flow](wallet-hierarchy-and-capital-flow.md) -- two-tier wallet model and share classes
