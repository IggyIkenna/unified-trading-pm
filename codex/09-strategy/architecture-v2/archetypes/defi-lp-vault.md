---
doc_type: codex-ssot
title: "Archetype: `DEFI_LP_VAULT`"
summary: >-
  `DEFI_LP_VAULT` archetype — deposit into an ERC-4626 vault (Yearn V3 / Morpho / Aave Vaults / Sommelier) and hold
  while `vault_share_price_apy_bps` >= `min_apy_bps` (default 100 = 1%); exit on APY-below-floor or `max_drawdown_bps`
  (default 500 = 5%) breach; single-leg ATOMIC deposit/redeem resolved via LegController.
implementation_status: code-shipped
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: [defi, market-making, erc-4626, vault, yield, strategy]
related:
  [
    ../families/market-making.md,
    /codex/09-strategy/architecture-v2/archetypes/defi-lp-concentrated.md,
    /codex/09-strategy/architecture-v2/archetypes/defi-lp-pool.md,
    /codex/09-strategy/architecture-v2/archetypes/yield-rotation-lending.md,
    /codex/09-strategy/architecture-v2/archetypes/yield-staking-simple.md,
  ]
created: 2026-05-01
authoritative_for: [DEFI_LP_VAULT archetype specification]
referenced_by:
  [
    /codex/09-strategy/architecture-v2/archetypes/defi-lp-concentrated.md,
    /codex/09-strategy/architecture-v2/archetypes/defi-lp-pool.md,
    /codex/09-strategy/architecture-v2/families/market-making.md,
  ]
owner:
last_reviewed:
code_refs: [strategy-service/strategy_service/engine/strategies/v2/defi_lp/vault.py]
archetype: DEFI_LP_VAULT
family: MARKET_MAKING
venue_universe: [YEARN_V3, MORPHO, AAVE_VAULT, SOMMELIER]
topology_requirements:
  isolation: { execution-service: isolated, strategy-service: isolated }
  co_location: [execution-service, strategy-service]
  latency_budget_ms: 1000
  min_sla_tier: premium
---

# Archetype: `DEFI_LP_VAULT`

> **Family:** [Market Making](../families/market-making.md) (`MARKET_MAKING`). **Settlement model:** ERC-4626 deposit /
> redeem. **Code module (SHIPPED):** `strategy-service/strategy_service/engine/strategies/v2/defi_lp/vault.py`.

## What it does

Deposits into an ERC-4626 vault (Yearn V3, Morpho MetaMorpho, Aave Vaults, Sommelier, etc.) and holds while realised APY
stays above `min_apy_bps`. Exits on APY-below-floor OR drawdown breach.

Share price `pps = totalAssets / totalSupply` accretes over time net of the vault's perf + management fees. The
features-onchain `vault_share_price_apy` calculator emits annualised share-price drift as
`vault_share_price_apy_bps_<vault>`, which is the engine's primary input.

## State machine

```
NEUTRAL --apy >= min_apy--> DEPOSITED --apy < min_apy OR drawdown >= max-->  WITHDRAWN
```

## Required params

- `vault_address` — ERC-4626 contract
- `venue` — `YEARN_V3` | `MORPHO` | `AAVE_VAULT` | `SOMMELIER` | ...
- `stake_fraction` — equity fraction (default `1.0`)
- `min_apy_bps` — exit floor (default `100` = 1%)
- `max_drawdown_bps` — exit ceiling on drawdown (default `500` = 5%)

## Required feature keys

- `vault_share_price_<vault_address>`
- `vault_share_price_apy_bps_<vault_address>`
- `vault_drawdown_bps_<vault_address>`

### LegController integration

`LegController.update(slot, tick, execution_mode=ATOMIC)` resolves vault deposit/redeem as a 1-leg ATOMIC instruction
(single ERC-4626 `deposit` or `redeem` call). No multi-leg sequencing required — the vault contract handles the
underlying token swap internally.

**Code-backport status:** DEFERRED — `defi_lp/vault.py` currently emits `AtomicInstruction` hand-built without
`LegController`. Backport tracked in `defi_recursive_borrow_archetypes_2026_05_10.md` factory-wiring phase. Docs ship
now per operator decision 2026-05-07.

## Risks

- **Strategy concentration** — many ERC-4626 vaults are thin wrappers over a single underlying yield strategy.
  Diversification from the vault itself is illusory; treat each vault as a single-strategy bet.
- **Withdraw queues** — some vaults gate withdrawals behind an epoch queue; emergency exit may take days. Verify via the
  vault's `previewRedeem` ABI before deploying real capital.
- **Perf fee step-changes** — operators of the underlying vault can raise the perf fee mid-deposit. APY drops without an
  underlying yield change; engine exits on the new realised APY.

## Example instances

```
DEFI_LP_VAULT@yearn-v3-usdc-ethereum-prod
DEFI_LP_VAULT@morpho-metamorpho-usdc-ethereum-prod
DEFI_LP_VAULT@aave-vault-usdc-arbitrum-prod
```

## Not in this archetype

- Direct concentrated / full-range pool LP (no ERC-4626 wrapper) → [`DEFI_LP_CONCENTRATED`](defi-lp-concentrated.md) /
  [`DEFI_LP_POOL`](defi-lp-pool.md)
- Lending-supply APY rotation across protocols → [`YIELD_ROTATION_LENDING`](yield-rotation-lending.md) (Carry & Yield)
- Staking-derivative (LST) yield without a vault wrapper → [`YIELD_STAKING_SIMPLE`](yield-staking-simple.md) (Carry &
  Yield)

## Plan

`plans/archive/defi_pipeline_extension_2026_05_01.plan.md` Phase 4.3.
