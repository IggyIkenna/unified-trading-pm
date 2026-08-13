---
doc_type: codex-ssot
title: "Cross-Cutting: Transfer / Rebalance"
summary:
  "Venue-scope capital-movement primitive: moves capital between venues within one strategy via 7 transfer types
  (INTERNAL_SUBACCOUNT / CEX_WITHDRAWAL_DEPOSIT / ON_CHAIN_TRANSFER / BRIDGE / WRAP_UNWRAP / UNITY_WALLET_OP /
  IBKR_FUND_MOVE); target-state, idempotent by `instruction_id`, cost-budgeted; bridge paths from `CHAIN_BRIDGE_GRAPH`."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: [defi, cefi, execution, strategy, reconciliation, uac]
related:
  [
    /codex/09-strategy/architecture-v2/cross-cutting/portfolio-allocator.md,
    /codex/09-strategy/architecture-v2/cross-cutting/venue-account-coordination.md,
    ../../../04-architecture/capital-flow-model.md,
    ../../../04-architecture/transfer-architecture.md,
  ]
created: 2026-04-17
authoritative_for:
  [venue-scope capital-movement primitive (target-state TRANSFER/BRIDGE reconciliation + bridge-selection graph)]
referenced_by:
  [
    /codex/02-venues/venue-registry-reference.md,
    /codex/04-architecture/capital-flow-model.md,
    /codex/04-architecture/capital-structure-and-regulatory.md,
    /codex/09-strategy/_archived_pre_v2/defi/cross-chain-sor-rebalancing.md,
    /codex/09-strategy/architecture-v2/README.md,
    /codex/09-strategy/architecture-v2/axes/share-class.md,
    /codex/09-strategy/architecture-v2/axes/venue-eligibility.md,
    /codex/09-strategy/architecture-v2/cross-cutting/futures-roll-and-combos.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Cross-Cutting: Transfer / Rebalance

> **What it is:** The venue-level capital movement primitive. When a strategy's eligible-venue allocations drift from
> target, the transfer/rebalance service moves capital between venues (same chain via `TRANSFER`, cross-chain via
> `BRIDGE`, CEX-to-CEX via internal transfer or withdrawal+deposit). Event-driven, target-state-based, idempotent.

> ## ⚠️ IMPLEMENTATION STATUS (verified 2026-08-12) — this doc describes the DESIGN; most of it does not run yet
>
> **Nothing emits `TransferIntent` in production.** A workspace-wide search finds zero production construction sites
> outside the UAC class definition. execution-service's `TransferCoordinator.execute(intent)` is a real consume-time
> entry point **with no live producer**. The whole rail below it is built and adapter-injected; the near end is
> disconnected. Read this doc as the target, not the current behaviour.
>
> | Break                                                                                                | Status                                      |
> | ---------------------------------------------------------------------------------------------------- | ------------------------------------------- |
> | `enable_transfer_rebalancing` never forwarded — `make_worker_target`'s `False` default always won    | ✅ FIXED `strategy-service@db6e38ae3a`      |
> | Four competing transfer-type enums, no shared vocabulary                                             | ✅ FIXED `unified-api-contracts@4663daf908` |
> | Nothing sends `REBALANCE_PERIOD_TICK`, so `_handle_rebalance_period_tick` never fires                | ❌ OPEN                                     |
> | `compute_rebalance_transfers()` does not exist — zero non-test `TransferRequest(` construction sites | ❌ OPEN                                     |
>
> Live plan:
> [service-config-ownership-and-instruction-contract](/plans/active/service_config_ownership_and_instruction_contract_2026_08_12.md)
> § H.

## Scope

Transfer/rebalance is the _venue scope_ of capital movement. It moves capital between venues **within one strategy** (or
between subaccounts on one venue). It does NOT reallocate between strategies (that's
[portfolio-allocator.md](portfolio-allocator.md)) or between clients (platform allocator).

All three capital-flow scopes share the same event-driven "target X at Y = Z" primitive. See
[../../../04-architecture/capital-flow-model.md](../../../04-architecture/capital-flow-model.md).

## Triggers

A rebalance cycle fires when:

1. **Drift from allocation policy** — one venue's balance falls below its min threshold or rises above its max
2. **Scheduled cadence** — daily / weekly / per rebalance_cadence in config
3. **Explicit operator command** — emergency rebalance
4. **Allocator directive** — Portfolio Allocator has increased a strategy's equity; extra capital must be spread across
   venues
5. **Post-fill imbalance** — after a large one-sided fill, pre-funding on another venue is depleted

## Transfer types — `BusTransferType`, 13 members (UNIONED 2026-08-12)

> **This table previously listed the 7 members of `architecture_v2.enums.TransferType`.** That enum was one of FOUR
> competing transfer-type enums (20 distinct values, 18 of them in exactly one enum); they were unioned onto
> `BusTransferType` — the SSOT, `unified_api_contracts.canonical.crosscutting.transfer_events` — in
> `unified-api-contracts@4663daf908`. **Use these names; the old ones no longer exist as a shared vocabulary.**
> `CEX_WITHDRAWAL_DEPOSIT` in particular was SPLIT, because it conflated direction into one value.

| Member             | Rail       | When                                  | Mechanism                           |
| ------------------ | ---------- | ------------------------------------- | ----------------------------------- |
| `CEX_WITHDRAW`     | `cefi`     | leaving a CeFi venue                  | exchange withdrawal API (CCXT)      |
| `CEX_DEPOSIT`      | `on_chain` | funding a CeFi venue                  | send to the venue's deposit address |
| `SUBACCOUNT_MOVE`  | `cefi`     | Binance master → subaccount           | venue internal API                  |
| `ON_CHAIN`         | `on_chain` | wallet → wallet, same chain           | EVM/Solana transaction              |
| `BRIDGE`           | `on_chain` | ETH on Arbitrum → ETH on Optimism     | Across/Stargate/LayerZero/etc.      |
| `WRAP_UNWRAP`      | `on_chain` | ETH ↔ wstETH, USDC ↔ aUSDC            | token wrapping                      |
| `DEFI_DEPOSIT`     | `on_chain` | into a DeFi protocol                  | protocol deposit                    |
| `DEFI_WITHDRAW`    | `on_chain` | out of a DeFi protocol                | protocol withdrawal                 |
| `CUSTODY_TRANSFER` | `on_chain` | custody-held wallet movement          | custody provider (Copper / CEFFU)   |
| `SWEEP`            | `on_chain` | dust consolidation to the main wallet | see § "Sweep and gas reserve"       |
| `REBALANCE`        | `on_chain` | venue-balance correction              | as routed                           |
| `UNITY_WALLET_OP`  | `other`    | Unity deposit / withdrawal            | Unity API                           |
| `IBKR_FUND_MOVE`   | `other`    | IBKR cash allocation                  | IBKR internal                       |

**The `rail` column is not decoration — it is in the type.** `BUS_TRANSFER_TYPE_RAIL` and `bus_transfer_type_rail()`
classify every member, because execution-service's live `CompositeTransferAdapter` routes on **CeFi-vs-on-chain**, not
on the transfer type. Emitting a type whose rail cannot service it is the failure this mapping exists to prevent. Note
the deliberate asymmetry: `CEX_WITHDRAW` is `cefi` (an API call) while `CEX_DEPOSIT` is `on_chain` (a chain transaction
to the venue's address). `UNITY_WALLET_OP` and `IBKR_FUND_MOVE` fit neither rail — hence the third `other` value,
matching [transfer-architecture](/codex/04-architecture/transfer-architecture.md)'s standing "no manual/acknowledged
transfer path" finding for exactly those two.

## Transfer type router

Each request is classified into one of the 13 members above from source/destination venue + asset + chain, then routed
by its rail. See [autonomous-recovery-matrix](/codex/04-architecture/autonomous-recovery-matrix.md).

_(A pointer here to an agent `memory/` file was removed 2026-08-12: agent memory is BANNED workspace-wide, is per-cwd,
and was never readable by anyone else — so that reference had never resolved for any reader.)_

## Sweep and gas reserve — the concrete model behind `SWEEP`

Two config fields define this, and their own descriptions are the spec (`strategy-service/strategy_service/config.py`):

- **`sweep_threshold_usd`** (default `10.0`) — _"USD threshold below which wallet balances are swept to the main
  wallet"_. Dust consolidation, not portfolio rebalancing.
- **`min_eth_reserve`** (default `0.05`) — _"Minimum ETH balance to maintain in DeFi wallets for gas (in ETH)"_. A floor
  to top UP to, not a target to trade around.

This is **threshold logic, not a judgment call**, which is why it is buildable without a further design decision.
Balance source is `strategy_service/position/core/venue_balance_tracker.py::get_all_balances()`. A sweep must never take
a wallet below `min_eth_reserve` — gas is what makes the next transfer possible, so sweeping it is self-defeating.

## Target-state protocol

Strategies emit `TRANSFER` or `BRIDGE` instructions with target balances:

```yaml
action: TRANSFER
venue_from: BINANCE
venue_to: OKX
asset: USDT
target_balance_at_destination: 500_000
deadline_seconds: 3600
```

Transfer/rebalance service:

1. Checks current balance at destination
2. Computes required move = target - current
3. Computes source requirements (fee buffer, withdrawal minimum)
4. Issues chain-level transaction(s) or CEX API call
5. Monitors confirmation
6. Emits `TRANSFER_COMPLETE` or `TRANSFER_FAILED`

## Idempotency

Instructions are idempotent by `instruction_id`. Re-issuing the same target (same id) is a no-op if already reconciled.
Re-issuing with different id but same target-state is also effectively a no-op (balance already at target).

## Cost awareness

Every transfer has:

- **Explicit cost**: network gas, CEX withdrawal fee, bridge fee, wrap cost
- **Implicit cost**: time-out-of-market (asset not working during bridge; bridge latency 1-30 min)

Strategies declare cost tolerance:

```yaml
rebalance_policy:
  max_cost_bps_per_move: 5 # skip move if >5 bps
  max_total_cost_bps_per_day: 20 # don't exceed daily cost budget
  min_move_amount_usd: 10_000 # don't move tiny amounts
  prefer_method: # tie-breaker when multiple work
    - INTERNAL_SUBACCOUNT
    - CEX_WITHDRAWAL_DEPOSIT
    - BRIDGE
```

## Bridge selection (DeFi)

Cross-chain moves have multiple bridge options. The canonical 1-hop bridge graph is
`unified_api_contracts.canonical.crosscutting.defi.CHAIN_BRIDGE_GRAPH` — use it to enumerate valid rebalance paths
rather than hardcoding chain pairs here. Multi-hop paths (e.g. Starknet → Ethereum → Arbitrum) are not in
`CHAIN_BRIDGE_GRAPH` and must be decomposed by the rebalancer into sequential 1-hop legs.

| Bridge             | Chains                   | Speed               | Cost            |
| ------------------ | ------------------------ | ------------------- | --------------- |
| Across             | ETH↔ARB/OP/BASE          | Fast (sec–min)      | Low             |
| Stargate           | Most EVM                 | Medium              | Medium          |
| LayerZero native   | Most EVM                 | Medium              | Medium          |
| Wormhole           | EVM↔Solana               | Medium              | Medium          |
| CCTP (USDC native) | ETH↔ARB/OP/BASE/AVAX     | Fast                | Low (mint/burn) |
| Native bridges     | Optimism/Arbitrum native | Slow (hours–7d)     | Lowest          |
| Hyperliquid native | HYPERLIQUID_L1↔ARBITRUM  | Fast (~minutes)     | Low (USDC-only) |
| StarkGate          | STARKNET↔ETHEREUM        | Very slow (~8h out) | Low             |

Bridge selection policy is an artifact-versioned rule table similar to execution policies.

## Pre-funding allocation strategies

For `SOR_AT_EXECUTION` venue routing mode:

| Allocation        | Logic                                        |
| ----------------- | -------------------------------------------- |
| `EQUAL_WEIGHT`    | N venues → 1/N each                          |
| `PRO_RATA_VOLUME` | weight ∝ historical fill share               |
| `PRO_RATA_EDGE`   | weight ∝ observed per-venue edge capture     |
| `MANUAL`          | operator-set weights                         |
| `DYNAMIC`         | allocator algorithm re-balances periodically |

## Wallet movement patterns per category

| Category           | Typical patterns                                                                              |
| ------------------ | --------------------------------------------------------------------------------------------- |
| CeFi SMA           | INTERNAL_SUBACCOUNT intra-venue; CEX_WITHDRAWAL_DEPOSIT inter-venue (with client approval)    |
| DeFi firm          | ON_CHAIN_TRANSFER intra-chain; BRIDGE inter-chain                                             |
| DeFi client wallet | ON_CHAIN_TRANSFER + BRIDGE only with client-co-signed instructions (Copper/Fireblocks policy) |
| Sports Unity pool  | UNITY_WALLET_OP (deposit/withdraw from firm treasury)                                         |
| Sports direct      | per-book deposit/withdraw APIs                                                                |
| TradFi IBKR        | IBKR_FUND_MOVE (internal allocation)                                                          |

## Reconciliation with PBMS

After every transfer:

- PBMS reads destination venue balance
- Compares vs target
- Emits `TRANSFER_RECONCILED` when match
- If drift persists > N minutes → emit `TRANSFER_DRIFT_ALERT`

## Failure modes

| Failure                                | Mitigation                                                      |
| -------------------------------------- | --------------------------------------------------------------- |
| Bridge hung (tx submitted, no confirm) | Monitor → manual intervention if > N min                        |
| CEX withdrawal paused                  | Fail fast; emit alert; strategy falls back to no-rebalance mode |
| Insufficient gas at source             | Pre-flight gas top-up; if fail, alert                           |
| Wrong destination address              | Refuse to submit without whitelist match                        |
| Partial fill on bridge                 | Resubmit remainder                                              |

See [../../../04-architecture/autonomous-recovery-matrix.md](../../../04-architecture/autonomous-recovery-matrix.md) for
full recovery flows.

## Not in this doc

- **Strategy-to-strategy capital reallocation** — [portfolio-allocator.md](portfolio-allocator.md)
- **Client-to-client capital movement** — platform allocator (not covered here)
- **Which asset to send** — strategy decides based on position + eligibility
- **Emergency full close** — `AccountInstruction.CLOSE_ALL` + transfer after close
- **Manual booking** — manual-trade-booking service

## Cross-references

- Capital flow model: [../../../04-architecture/capital-flow-model.md](../../../04-architecture/capital-flow-model.md)
- Autonomous recovery:
  [../../../04-architecture/autonomous-recovery-matrix.md](../../../04-architecture/autonomous-recovery-matrix.md)
- Portfolio allocator: [portfolio-allocator.md](portfolio-allocator.md)
- Venue-account coordination: [venue-account-coordination.md](venue-account-coordination.md)
- Capital structure per category:
  [../../../04-architecture/capital-structure-and-regulatory.md](../../../04-architecture/capital-structure-and-regulatory.md)
