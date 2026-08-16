---
doc_type: codex-ssot
title: "Cross-Cutting: Capital / Client Isolation"
summary:
  Strategy-v2 client-isolation guarantees — every event/fill/P&L/instruction carries client_id, and capital, credentials
  (Secret Manager trading/{client_id}/{venue}/{type}), configs, risk, kill-switches, audit, allocator, and UI scope are
  all isolated per client. We face ONE client per strategy instance (a fund is a single client); the only cross-client
  operation is human-approved platform-level allocation (out of v1 scope). Covers the client-type + custody-model
  tables.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service]
scope: [engineer, admin]
tags: [strategy, execution, client-isolation, reconciliation, cefi, defi]
related:
  [
    ../axes/share-class.md,
    /codex/09-strategy/architecture-v2/cross-cutting/portfolio-allocator.md,
    /codex/09-strategy/architecture-v2/cross-cutting/venue-account-coordination.md,
    ../../../04-architecture/capital-structure-and-regulatory.md,
  ]
created: 2026-04-17
authoritative_for: [strategy-v2 cross-cutting client-isolation dimensions (per-instance client_id tagging)]
referenced_by:
  [
    /codex/04-architecture/account-instructions.md,
    /codex/09-strategy/_archived_pre_v2/cross-cutting/share-classes.md,
    /codex/09-strategy/architecture-v2/README.md,
    /codex/09-strategy/architecture-v2/axes/share-class.md,
    /codex/09-strategy/architecture-v2/cross-cutting/strategy-availability-and-locking.md,
    /codex/09-strategy/architecture-v2/cross-cutting/treasury-trading-wallet-invariant.md,
    /codex/09-strategy/architecture-v2/cross-cutting/venue-account-coordination.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Cross-Cutting: Capital / Client Isolation

> **What it is:** The guarantees that one client's capital, credentials, risk, and audit state are fully isolated from
> another client's. Every event, fill, P&L entry, and instruction carries `client_id`; no code path reads across clients
> without an explicit cross-client scope (which only exists at platform-level allocation).
>
> **Why it matters:** We face ONE client per strategy instance. The client may be an individual, a firm's principal
> capital, or a fund. Regardless, the _client layer_ of the 5-layer identity model is the isolation boundary. Leaks here
> are the highest-severity compliance failure.

## Isolation dimensions

1. **Capital** — venue accounts, wallets, subaccounts are client-tagged; no pooling across clients
2. **Credentials** — API keys, wallet private keys per (client, venue) pair in Secret Manager
3. **Configs** — strategy configs tagged with `client_id`
4. **Instructions** — every `StrategyInstruction` / `AccountInstruction` carries `client_id`
5. **Fills + P&L** — every fill tagged with `client_id`; P&L aggregation per client
6. **Risk** — risk-and-exposure-service aggregates limits per client, enforces per-client
7. **Kill switches** — per strategy instance, which is scoped to one client
8. **Audit** — audit log filtered by `client_id`; reporting per client
9. **Allocator** — Portfolio Allocator has one instance per client
10. **UI scope** — UI auth enforces client_id filter on every data request

## Client types

| Client type     | Nature                    | Notes                                                                                  |
| --------------- | ------------------------- | -------------------------------------------------------------------------------------- |
| Individual      | Single person's capital   | Standard SMA or direct-wallet                                                          |
| Firm principal  | Firm's own capital        | "House book"                                                                           |
| Fund            | Investment fund           | Fund is ONE client from our perspective; investor-level accounting stays at fund layer |
| Managed account | Individual/fund-style SMA | Hybrid; we manage, they own                                                            |

**Rule:** We face ONE client per strategy instance. The fund case is a single client relationship at our layer.
Investor-in-fund accounting is the fund's responsibility. See
[../../../04-architecture/capital-structure-and-regulatory.md](../../../04-architecture/capital-structure-and-regulatory.md).

## Credential isolation

Credentials are stored in Secret Manager, keyed as:

```
secret: trading/{client_id}/{venue}/{credential_type}
  values: api_key, api_secret, wallet_private_key, rpc_url, ...
```

- Fetched at runtime by services that need them (execution-service, PBMS-read, reference-data adapters)
- Injected via factory/constructor params (see CLAUDE.md interface credential convention)
- Reloaded via `ApiKeyReloader` on rotation
- Never logged, never emitted in events

## Venue-account isolation

Every venue account is a (client_id, venue, account_id) tuple:

```
(client_A, BINANCE, "binance-subaccount-1")
(client_A, BINANCE, "binance-subaccount-2")
(client_B, BINANCE, "binance-subaccount-99")
(client_A, UNISWAP_V3_ETHEREUM, "0xclientA_wallet")
(client_B, UNISWAP_V3_ETHEREUM, "0xclientB_wallet")
```

PBMS projects positions per (client, venue-account). No aggregation across client_id (only within).

## Fund-client framing in code

```python
# Strategy emission
instruction = StrategyInstruction(
    strategy_instance_id=...,
    client_id="fund_XYZ",          # fund is the client
    ...
)

# Execution
venue_account = venue_account_registry.get(
    client_id="fund_XYZ",          # isolation enforced
    venue=instruction.target_venue,
)

# Risk
limits = risk_limits.for_client("fund_XYZ")
```

Investor-level accounting (who in fund_XYZ owns what) is NOT our concern. Fund_XYZ treats us as a single external
manager.

## Share-class × client

Share class is per-instance. A single client can have multiple instances in different share classes:

```
client_A_fund
 ├── ML_DIRECTIONAL_CONTINUOUS@binance-btc-5m-USDT-prod    (USDT share class)
 ├── ML_DIRECTIONAL_CONTINUOUS@ibkr-spy-1h-USD-prod         (USD share class)
 └── CARRY_STAKED_BASIS@lido-binance-eth-ETH-prod           (ETH share class)
```

Portfolio Allocator converts each instance's NAV to client-reporting currency for allocation decisions.

## Cross-client operations

The only valid cross-client operation is **platform-level allocation** (client-to-client capital reallocation). This:

- Requires human approval + compliance review
- Moves between entirely separate legal entities / agreements
- Is not implemented in the current v1 scope
- Out of scope for all services below platform-allocation level

All other services reject cross-client reads/writes.

## Compliance boundaries

Per
[../../../04-architecture/capital-structure-and-regulatory.md](../../../04-architecture/capital-structure-and-regulatory.md):

| Custody model       | Who holds capital                  | Movement restrictions                                                 |
| ------------------- | ---------------------------------- | --------------------------------------------------------------------- |
| CeFi SMA            | Client's own CEX account           | Client-authorized API moves only; withdrawals may be client-co-signed |
| CeFi fund (future)  | Firm-owned, multiple CEXes         | Firm authority                                                        |
| DeFi client wallet  | Copper / Fireblocks                | Client-co-signed per policy                                           |
| DeFi firm           | Firm wallet                        | Firm authority                                                        |
| Sports Unity pool   | Firm-managed Unity wallet          | Firm authority; Unity T&C                                             |
| Sports direct books | Per-book accounts (firm or client) | Per book                                                              |
| TradFi IBKR SMA     | Client's IBKR account              | Managed under IA agreement                                            |
| TradFi counterparty | Depends                            | Per ISDA/relationship                                                 |

## Audit isolation

Every event in the system carries:

- `client_id`
- `strategy_instance_id`
- `(family, archetype_id, archetype_build_version, slot_version, config_hash, config_version)`
- `instruction_id`
- `source_service`
- `timestamp`

Audit queries filter by `client_id` at the boundary. UI enforces via auth.

## Client onboarding flow

Per
[../../../04-architecture/capital-structure-and-regulatory.md](../../../04-architecture/capital-structure-and-regulatory.md):

1. Legal agreement signed (per custody model)
2. Credentials provisioned in Secret Manager under client_id
3. Venue accounts registered with PBMS
4. Strategy instances created + linked to client_id
5. Portfolio Allocator instance configured for client
6. Initial capital top-up via transfer/rebalance service
7. Kill switches set; first tick enabled

## Client offboarding flow

1. Kill switches armed (`DISABLED`)
2. Positions unwound (CLOSE_ALL)
3. Capital transferred back per custody-model mechanics
4. Credentials revoked / rotated
5. Strategy instances retired
6. Allocator instance retired
7. Audit exported; retained per compliance policy

## Not in this doc

- **Per-custody details** —
  [../../../04-architecture/capital-structure-and-regulatory.md](../../../04-architecture/capital-structure-and-regulatory.md)
- **Credential rotation internals** — ops + Secret Manager
- **Secret Manager schema** — infrastructure docs
- **Regulatory filings** — compliance docs
- **Audit log storage** — event-store architecture

## Cross-references

- Capital structure + regulatory:
  [../../../04-architecture/capital-structure-and-regulatory.md](../../../04-architecture/capital-structure-and-regulatory.md)
- Share class: [../axes/share-class.md](../axes/share-class.md)
- Portfolio allocator: [portfolio-allocator.md](portfolio-allocator.md)
- Venue-account coordination: [venue-account-coordination.md](venue-account-coordination.md)
