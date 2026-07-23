---
doc_type: codex-ssot
title: Treasury × Trading Wallet Invariant
summary:
  "HARD invariant: treasury/reserve-custody wallets never source or destination a `StrategyInstruction` nor enter the
  allocator pool; trading wallets never serve as long-term custody reserve or operator-withdrawal destination. Enforced
  via `isolation_policy.py`; violation raises `TreasuryWalletMisuseError`. Cross-purpose peer to client-funds isolation."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service, strategy-service]
scope: [engineer, admin]
tags: [defi, strategy, execution, risk, self-healing]
related:
  [
    ../../../04-architecture/client-funds-isolation.md,
    ../../../04-architecture/custody-providers.md,
    /codex/09-strategy/architecture-v2/cross-cutting/universe-enumeration-contract.md,
    /codex/09-strategy/architecture-v2/cross-cutting/capital-client-isolation.md,
  ]
created: 2026-05-22
authoritative_for: [treasury-vs-trading wallet purpose-separation invariant]
referenced_by: [/codex/09-strategy/architecture-v2/cross-cutting/strategy-execution-runtime.md]
owner:
last_reviewed: 2026-05-22
code_refs:
---

# Treasury × Trading Wallet Invariant

> **[DELTA 2026-05-22]** **Current state:** Invariant enforced in code but undocumented at codex level. Discovery via
> `strategy_archetype_logic_audit_2026_05_20.md`. **Planned delta:** Full invariant spec per `strategy_master.md`.
> **Target architecture:** Canonical rule: treasury wallets never used for active trading; trading wallets never used
> for custody reserve.

## Context

Hard separation between treasury/reserve custody and active trading wallet pools. This invariant prevents operational
risk scenarios where reserve capital is inadvertently deployed as trading collateral or vice versa.

## Current State

The invariant is enforced via `isolation_policy.py` in strategy-service and at the execution-service transfer layer via
`CrossClientTransferForbiddenError`. Wallet classification (treasury vs trading) lives in `WalletProvisioningConfig` in
UTL.

## The Invariant

```
treasury_wallet.purpose == "reserve_custody"
    → NEVER appears as source or destination in StrategyInstruction
    → NEVER appears in allocator pool
    → MAY appear in TreasuryLedger for operator-directed movements only

trading_wallet.purpose == "active_trading"
    → NEVER appears as operator withdrawal destination
    → NEVER appears as long-term custody reserve
    → IS the only valid source/destination for StrategyInstruction execution legs
```

Violation raises `TreasuryWalletMisuseError` (UTL, to be added per `strategy_master.md` Phase N).

## Composes with

This invariant is the per-wallet expression of the client funds isolation HARD RULE:
`/codex/04-architecture/client-funds-isolation.md`. Client isolation governs cross-client movement; this invariant
governs cross-purpose movement within a single client's wallet set.

## See also

- `plans/epics/strategy_master.md`
- `plans/active/issues/strategy_archetype_logic_audit_2026_05_20.md`
- `/codex/04-architecture/client-funds-isolation.md`
- `/codex/04-architecture/custody-providers.md`
- `/codex/09-strategy/architecture-v2/cross-cutting/universe-enumeration-contract.md`
