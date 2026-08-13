---
doc_type: codex-ssot
title: "Archetype: `DEFI_LP_POOL`"
summary: >-
  Archetype DEFI_LP_POOL: full-range pool LP (Curve stableswap / Balancer weighted) held until invariant-drift signals
  depeg — DEPOSIT while lp_pool_invariant_drift_bps < depeg_exit_bps, WITHDRAW at/above threshold (or on kill switch).
  No in-range rebalance math (the pool invariant absorbs spot moves); single-pool ATOMIC, cross-pool rotation
  LEADER_HEDGE.
implementation_status: code-shipped
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: [strategy, defi, execution, archetype, features]
related:
  [
    ../families/market-making.md,
    /codex/09-strategy/architecture-v2/archetypes/defi-lp-concentrated.md,
    /codex/09-strategy/architecture-v2/archetypes/yield-rotation-lending.md,
    /codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md,
  ]
created: 2026-05-01
authoritative_for: [DEFI_LP_POOL archetype specification]
referenced_by:
  [
    /codex/09-strategy/architecture-v2/archetypes/defi-lp-concentrated.md,
    /codex/09-strategy/architecture-v2/archetypes/defi-lp-vault.md,
    /codex/09-strategy/architecture-v2/families/market-making.md,
  ]
owner:
last_reviewed:
code_refs:
archetype: DEFI_LP_POOL
family: MARKET_MAKING
venue_universe: [CURVE, BALANCER_V2, BALANCER_V3]
topology_requirements:
  isolation: { execution-service: isolated, strategy-service: isolated }
  co_location: [execution-service, strategy-service]
  latency_budget_ms: 1000
  min_sla_tier: premium
---

# Archetype: `DEFI_LP_POOL`

> **Family:** [Market Making](../families/market-making.md) (`MARKET_MAKING`). **Settlement model:** atomic deposit /
> withdraw through pool contract. **Code module:**
> `strategy-service/strategy_service/engine/strategies/v2/defi_lp/pool.py`.

## What it does

Deposits into a full-range pool (Curve stableswap, Balancer weighted) and holds until invariant drift signals depeg
risk. No within-range rebalance math — the pool's invariant absorbs spot moves automatically; the only external decision
is "stay in or get out."

## State machine

```
NEUTRAL  --healthy invariant-->  DEPOSITED  --invariant drift > exit-->  WITHDRAWN
```

`drift` is read from features-onchain feature `lp_pool_invariant_drift_bps_<pool_address>` — Curve uses the D-invariant,
Balancer uses the V-invariant. The features-onchain `pool_invariant_drift` calculator computes both. **Drift > 0 means
bleed; drift > `depeg_exit_bps` means exit immediately.**

## Required params

- `pool_address` — pool contract
- `venue` — `CURVE` | `BALANCER_V2` | `BALANCER_V3`
- `stake_fraction` — fraction of equity (default `1.0`)
- `depeg_exit_bps` — exit threshold (default `50`)

## Trigger conditions

| Trigger  | Condition                                                   |
| -------- | ----------------------------------------------------------- |
| DEPOSIT  | `_PoolState == NEUTRAL` and `drift_bps < depeg_exit_bps`    |
| WITHDRAW | `_PoolState == DEPOSITED` and `drift_bps >= depeg_exit_bps` |
| WITHDRAW | kill switch (`flatten_on_kill`)                             |

## Execution semantics

- `InstructionActionV2.SWAP` with `params["lp_operation"] = "deposit"` (multi-token add-liquidity) for entry
- `InstructionActionV2.SWAP` with `params["lp_operation"] = "withdraw"` (proportional or imbalanced) for exit
- Single-pool: ATOMIC bundle (add-liquidity + receive LP token, or burn LP + receive underlying)
- Cross-pool rotation: LEADER_HEDGE (withdraw → bridge → deposit)

> The dedicated `LP_MINT` / `LP_BURN` enum values exist (actions 13/14 in the instruction catalog), but the `defi_lp`
> engines route every LP op through `SWAP` + `lp_operation` today (`pool.py` emits `lp_operation="deposit"|"withdraw"`);
> migrating to the dedicated actions is a non-blocking follow-up. Earlier drafts of this doc named `LP_DEPOSIT` /
> `LP_WITHDRAW` actions — those enum values do not exist; corrected 2026-05-20.

### LegController integration

`LegController.update(slot, tick, execution_mode=ATOMIC)` resolves single-pool deposit/withdraw as 1-leg bundles.
Cross-pool rotation expands to 3 legs (WITHDRAW → BRIDGE → DEPOSIT) with LEADER_HEDGE deadlines per bridge SLA.

**Code-backport status:** DEFERRED — `defi/lp_pool.py` (when added) wires legs hand-built. Backport tracked in
`defi_recursive_borrow_archetypes_2026_05_10.md` factory-wiring phase. Docs ship now per operator decision 2026-05-07.

## Risks

- **Depeg detection lag** — the invariant drift is computed from on-chain pool reserves; if the chain itself stalls, the
  feature staleness allows the position to bleed. Risk-and-exposure-service emits `MARKET_TICK_FRESHNESS` warnings on
  stale onchain features.
- **Withdraw friction** — Curve and Balancer charge an exit fee on imbalanced withdrawals; if the pool is already
  depegging, the exit itself prints worse than the on-paper invariant.
- **Yield vs IL** — pools with high CRV / BAL incentives earn enough to tolerate small drift; high-volatility pools may
  have negative carry even at zero drift. The seed-the-strategy decision is operator-driven.

## Example instances

```
DEFI_LP_POOL@curve-3pool-usdc-usdt-dai-ethereum-prod
DEFI_LP_POOL@curve-steth-eth-ethereum-prod
DEFI_LP_POOL@balancer-v2-wsteth-eth-arbitrum-prod
```

## Not in this archetype

- Concentrated-range (Uniswap V3-style) LP → [`DEFI_LP_CONCENTRATED`](defi-lp-concentrated.md)
- ERC-4626 yield-vault deposit → [`DEFI_LP_VAULT`](defi-lp-vault.md)
- Lending-supply APY rotation (Aave/Compound supply side) → [`YIELD_ROTATION_LENDING`](yield-rotation-lending.md) (Carry
  & Yield)
- Stablecoin price-dispersion arb across pools → [`ARBITRAGE_PRICE_DISPERSION`](arbitrage-price-dispersion.md)

## Plan

`plans/archive/defi_pipeline_extension_2026_05_01.plan.md` Phase 4.2.
