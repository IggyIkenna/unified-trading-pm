---
doc_type: codex-ssot
title: "Archetype: `CARRY_BASIS_PERP_INV`"
summary: >-
  Archetype CARRY_BASIS_PERP_INV (renamed 2026-05-18 from CARRY_RECURSIVE_BORROW_PERP_HEDGED): recursive ETH-LST
  supply-borrow loop on Aave/Morpho + a USDC-margined CeFi perp short sized to E_actual for delta neutrality. Yield =
  R_lend + R_fund + R_usdc - gas - slippage; perp venue Hyperliquid PRIMARY / Bybit <=50% SECONDARY; recursion amplifies
  the spread, not the delta.
implementation_status: code-shipped
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: [strategy, carry, defi, cefi, execution, archetype, bybit]
related:
  [
    /codex/09-strategy/architecture-v2/archetypes/carry-recursive-borrow-perp-hedged.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-recursive-staked.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-recursive-borrow-lending-only.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-basis-perp.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-staked-basis-dated.md,
    ../families/carry-and-yield.md,
  ]
created: 2026-05-18
authoritative_for: [CARRY_BASIS_PERP_INV archetype specification (recursive borrow + perp-hedged carry)]
referenced_by:
  [
    /codex/09-strategy/architecture-v2/archetypes/carry-basis-dated-inv.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-recursive-borrow-lending-only.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-recursive-borrow-perp-hedged.md,
    /codex/09-strategy/architecture-v2/families/carry-and-yield.md,
    /codex/09-strategy/strategy-summary.md,
  ]
owner:
last_reviewed:
code_refs:
archetype: CARRY_BASIS_PERP_INV
family: CARRY_AND_YIELD
venue_universe: [AAVE, MORPHO, HYPERLIQUID, BYBIT]
topology_requirements:
  isolation: { execution-service: isolated, strategy-service: isolated }
  co_location: [execution-service, strategy-service]
  latency_budget_ms: 300
  min_sla_tier: premium
---

# Archetype: `CARRY_BASIS_PERP_INV`

> **Family:** [Carry & Yield](../families/carry-and-yield.md) **Settlement model:** Continuous; market-neutral recursive
> on-chain loop + CeFi perp hedge. **Code module:**
> `strategy-service/strategy_service/engine/strategies/v2/carry_and_yield/recursive_staked.py` (`ALLOWED_ARCHETYPES` =
> `CARRY_BASIS_PERP_INV`)

> **Renamed 2026-05-18**: was `CARRY_RECURSIVE_BORROW_PERP_HEDGED` — see
> [carry-recursive-borrow-perp-hedged.md](carry-recursive-borrow-perp-hedged.md) for the historical doc.

## What it does

Family 2 recursive supply-borrow loop: supply ETH LST as collateral on a lending protocol (Aave V3 / Morpho), borrow
ETH, swap to LST, re-supply — amplifying the staking spread (`R_lend`). A USDC-margined ETH perp short is placed on a
CeFi venue sized to neutralise the residual spot-ETH delta the recursion carries.

**Yield = `R_lend + R_fund + R_usdc − gas − slippage`** where:

- `R_lend` = amplified staking spread (supply LST yield minus borrow ETH rate), levered by recursion depth
- `R_fund` = perp funding capture (positive when longs pay shorts)
- `R_usdc` = USDC margin yield at perp venue (near-zero for Hyperliquid May-23 baseline)

The "INV" suffix denotes that the on-chain long-equivalent is realised via recursive borrow leverage — the inverse of
`CARRY_BASIS_PERP`'s direct spot purchase. Both achieve a delta-neutral long-spot + short-perp structure; this archetype
amplifies `R_lend` via recursion while `CARRY_BASIS_PERP` leaves the spot unlevered.

## Token / position flow

```
PHASE 1 — Recursive on-chain loop (identical to CARRY_RECURSIVE_BORROW_LENDING_ONLY):
  1. SUPPLY: ETH LST collateral → lending protocol (Aave V3 / Morpho)
  2. BORROW: ETH → swap back to LST → re-supply (× N iterations)
     Depth d, LTV per loop ≤ liquidation_threshold - 0.05
     Cumulative collateral = base × (1 − ltv^(d+1)) / (1 − ltv)
     Cumulative debt        = base × ltv × (1 − ltv^d) / (1 − ltv)
     Net ETH-equiv delta    = base (invariant for all d, ltv)

PHASE 2 — CeFi perp hedge:
  3. TRADE: SHORT ETH perp = max(0, E_actual − target_net_delta) on CeFi venue
     E_actual read live from Aave getUserAccountData (not closed-form; accounts for peg drift)
     Venue PRIMARY: Hyperliquid (USDC-margin); SECONDARY: Bybit (USDC-margin, ≤50% HL notional cap)

Net carry (USDC, annualised):
    R_net = R_lend + R_fund + R_usdc − gas − slippage
```

## Supported venues / instruments

| Layer        | Venue                                 | Role                               |
| ------------ | ------------------------------------- | ---------------------------------- |
| On-chain     | Aave V3 (ETH mainnet, Arbitrum, Base) | Supply/borrow loop                 |
| On-chain     | Morpho (ETH mainnet)                  | Alternative lending market         |
| CeFi PRIMARY | Hyperliquid L1                        | USDC-margined ETH-PERP short hedge |
| CeFi BACKUP  | Bybit (UTA)                           | ≤50% of HL notional cap (May-23)   |

**May-23 allowed cells**: `aave_v3_ethereum_wsteth_weth_emode`, `morpho_ethereum_wsteth_weth_market_0945`,
`aave_v3_ethereum_wsteth_weth_emode` (Bybit backup). Full catalog in
`strategy-service/.../target_universe/catalog.py:_build_carry_basis_perp_inv`.

## Net APR formula

```
R_lend = S × (1 − ltv^(d+1)) / (1 − ltv) − B × ltv × (1 − ltv^d) / (1 − ltv)
R_fund = +f × (perp_short_size / base)                    (delta=0 ⟹ +f)
R_usdc = u × (usdc_margin_buffer / base)                  (HL pays ~0; Bybit flex-savings ~0 May-23)
R_net  = R_lend + R_fund + R_usdc − gas − slippage

Worked example (wstETH/WETH E-Mode, ltv=0.93, d=8, S=3.2%, B=2.4%, f=+12% APR):
  R_lend ≈ 7.88%   R_fund ≈ +12.0%   R_usdc ≈ 0   drag ≈ 0.6%
  R_net  ≈ 19.28%   [HIGH confidence on R_lend; MED on R_fund — regime-variable]
```

## Config schema

```yaml
# Required on-chain params:
lending_protocol: AAVE_V3 # AAVE_V3 | MORPHO
lending_chain: ethereum # ethereum | arbitrum | base
lst_asset: wstETH # LST collateral token
borrow_asset: WETH # borrowed token

# Recursion params:
target_ltv: 0.90 # per-loop LTV (must be ≤ liquidation_threshold - 0.05)
max_recursion_depth: 8 # max supply-borrow iterations
flash_loan_enabled: true # use flash loan for atomic recursion (Phase 4 Solidity)

# CeFi perp hedge params:
perp_venue: hyperliquid # hyperliquid | bybit
perp_instrument: ETH-PERP
target_net_delta: 0.0 # 0 = fully delta-neutral
usdc_margin_buffer_min_pct: "0.30" # 3× initial-margin buffer

# Kill-switch thresholds:
kill_switch_drawdown_pct: "0.045"
kill_switch_position_breach_pct: "0.03"

# Leverage + net-delta (universal per StrategyInstanceDefinition):
target_leverage: "0.93" # per-loop LTV ≈ effective leverage on lending leg
target_net_delta: "0.0" # delta-neutral: on-chain equiv long = perp short
max_underlying_move_pct: "5.0"

# Chain constraint:
allowed_chains: [ethereum, arbitrum, base]
```

## Kill-switch surface (additive to base)

Extends `CARRY_RECURSIVE_BORROW_LENDING_ONLY` kill-switch codes with perp-leg codes:

- `DEFI_FUNDING_RATE_FLIP` — 30d-avg funding crosses negative threshold → position-pause / partial reduction
- `DEFI_CROSS_VENUE_DELTA_DRIFT` — `|perp_short_size − E_actual| > 5% × E_actual` → PerpHedgeSizer auto-rebalance
- `DEFI_PERP_VENUE_OUTAGE` — HL bridge halt / Bybit rate-limit → route to backup or flash-close on-chain
- `DEFI_PERP_MARGIN_CALL` — `available_margin < MM × 1.2` → top-up from treasury or partial unwind

## Bybit counterparty cap policy

Cap Bybit notional at ≤50% of Hyperliquid leg notional for first 30 days post-cutover. Rationale: Feb-2025 hack
counterparty-trust discount. Codified in `ARCHETYPE_CONCENTRATION_MULTIPLIER` (UAC risk_rules/archetype.py).

## Execution semantics

Two-phase opening per `LegController.update(slot, tick, execution_mode=LEADER_HEDGE)`:

1. Recursive on-chain bundle (leader): STAKE → TRANSFER → LEND → BORROW × N (flash mode or sequential multicall)
2. CeFi perp short (hedge): fires after on-chain finalization within `hedge_deadline_ms`

`CLOSE_LEADER_IF_HEDGE_FAILS` triggers flash-unwind of the on-chain loop if the perp fails.

**Translation-layer status (2026-08-09):** SHIPPED — `CarryRecursiveStakedEngine.on_tick()` in
`strategy-service/strategy_service/engine/strategies/v2/carry_and_yield/recursive_staked.py` now builds a real
`AtomicInstruction` for this archetype (previously an unconditional `return []` stub): the Family-1 lending-loop legs
plus one CeFi perp-hedge `AtomicLeg` sized via `unified_trading_library.risk.net_delta.residual_hedge_size()`
(strategy-service@f2ac7fdf). Execution-service's `execution_service/algo_library/recursive_loop_runner.py` gives
`RecursiveLoopOrchestrator` its first real production caller, including `PerpLegConfig` reconstruction
(execution-service@2352a17e). **`PerpHedgeSizer.compute_rebalance()`/`.compute_margin_topup()` now has a live caller
(2026-08-12)**: `PerpHedgeMonitorLifecycle` (one `PerpHedgeMonitor` per open Family-2 position, `HealthFactorMonitor`-
pattern 300s poll loop) is wired at `execution-service/execution_service/api/app.py` startup/shutdown
(execution-service@afd0166b), dispatching rebalance/margin-topup intents through `PerpHedgeDispatchRouter` into the SAME
`RecursiveLoopOrchestrator` path `recursive_loop_runner.py` uses — no second instruction sink. The
`PerpHedgeFetchProvider` production-fetch seam and real on-chain execution wiring were tracked + completed via
`/plans/archive/2026_08/recursive_loop_orchestrator_wiring_finalize_2026_08_09.md`. Full build plan:
`/plans/archive/2026_08/recursive_loop_orchestrator_wiring_2026_08_09.md`.

## Funding-regime degradation policy

Phase 7.5 adaptive sizing (rolling 7d + 30d funding-APR mean):

- 30d-avg `< −5% APR`: reduce perp short by 50%
- 30d-avg `< −15% APR`: set perp short to 0 (revert to Family 1 mechanics)
- 30d-avg `> +30% APR`: maintain or increase perp short toward `target_net_delta − 0.5`

## P&L attribution

| Layer        | Income source            | Cost                     |
| ------------ | ------------------------ | ------------------------ |
| Lending loop | Amplified staking spread | Gas (4–12 rebalances/yr) |
| Perp short   | Funding APR (when +)     | Commission               |
| USDC margin  | Venue margin yield       | Near-zero May-23         |

## Risk profile

- **Delta**: 0 by construction (`E_actual` always hedged by perp short via PerpHedgeSizer)
- **Liquidation**: on-chain loop faces health-factor risk; kill-switch at `min_health_factor`
- **Funding flip**: perp funding going negative erodes net APR; degradation policy manages this
- **Bridge risk**: Hyperliquid 5-min withdrawal dispute window encoded in unwind timing budget
- **Smart contract**: Aave / Morpho exploit risk; mitigated by per-protocol position caps
- **Typical Sharpe**: 1.5–3.5 in +funding regime; degrades to 0.8–1.2 in neutral-funding regime

## Example instances

```
CARRY_BASIS_PERP_INV@aave-hyperliquid-eth-usdt-prod
CARRY_BASIS_PERP_INV@morpho-bybit-eth-usdt-prod
CARRY_BASIS_PERP_INV@aave-hyperliquid-btc-usdt-prod
```

## See also

- Historical doc (pre-rename): [carry-recursive-borrow-perp-hedged.md](carry-recursive-borrow-perp-hedged.md)
- Family 0 (staking yield + HL hedge hardcoded): [carry-recursive-staked.md](carry-recursive-staked.md)
- Family 1 (no perp leg): [carry-recursive-borrow-lending-only.md](carry-recursive-borrow-lending-only.md)
- Direct basis perp (unlevered spot): [carry-basis-perp.md](carry-basis-perp.md)
- Dated variant with staking: [carry-staked-basis-dated.md](carry-staked-basis-dated.md)
- Family: [carry-and-yield.md](../families/carry-and-yield.md)

## Not in this archetype

- **Direct spot + perp basis** (no recursion, no lending) → `CARRY_BASIS_PERP`
- **Staking without recursion** (LST as perp margin, no borrow loop) → `CARRY_STAKED_BASIS`
- **Lending-only recursion** (no CeFi perp hedge) → `CARRY_RECURSIVE_BORROW_LENDING_ONLY`
- **Stablecoin recursive loops** (USDC debt, no ETH delta, perp would introduce not hedge delta) — excluded
