---
scope: [engineer, admin]
topology_requirements:
  isolation:
    execution-service: isolated
  co_location: []
  latency_budget_ms: 150
  min_sla_tier: standard
---

# CARRY_RECURSIVE_BORROW_LENDING_ONLY -- Family 1 archetype

> **Sibling archetypes:** [carry-recursive-staked.md](./carry-recursive-staked.md) (Family 0) -
> [carry-recursive-borrow-perp-hedged.md](./carry-recursive-borrow-perp-hedged.md) (Family 2)

> **Status:** Design-shipped 2026-05-12 (UAC enum + ARCHETYPE_CONFIG_SEED + per-chain ReserveParams). Implementation
> gated on Phase 4 Solidity + Phase 5 Python orchestrator + Phase 12 backtest harness per
> [`plans/active/defi_recursive_borrow_archetypes_2026_05_10.md`](../../../../plans/active/defi_recursive_borrow_archetypes_2026_05_10.md).

## What it does

Pure-lending recursive supply-borrow loop on Aave V3 (with Spark / Morpho Blue / Compound V3 as future expansion).
Holds an LST collateral (e.g. wstETH), borrows ETH against it at the chain's highest available E-Mode LTV (0.93 on
Aave ETH_CORRELATED), swaps borrowed ETH -> wstETH on Uniswap V3, redeposits, and repeats up to `n_loops` times.
Net yield = stake yield x leverage_factor - ETH borrow rate x debt_factor. NO perp leg: closed-form math shows
directional ETH exposure is exactly `base` capital for any `(ltv, d)`, so the recursion amplifies the SPREAD, not
the delta. Family 2 wraps the same legs with a USDC-margined perp short for delta neutrality; Family 1 accepts the
directional exposure.

## Token flow (recursion math)

```
Cumulative LST collateral (ETH-eq) = base x (1 - ltv^(d+1)) / (1 - ltv)
Cumulative ETH debt                = base x ltv x (1 - ltv^d) / (1 - ltv)
Net ETH-equivalent spot exposure E = base    (exactly, for all finite (ltv, d))
```

Yield formula:

```
R_lend = S x (1 - ltv^(d+1)) / (1 - ltv) - B x ltv x (1 - ltv^d) / (1 - ltv)
```

Worked example -- wstETH/WETH E-Mode at `ltv=0.93, d=8, S=3.2%, B=2.4%`:
`R_lend ~ 5.27 x 3.2% - 4.56 x 2.4% ~ 6.0% net APR` (HIGH confidence on lending math; MED on S+B which vary by
regime). Gas drag ~0.6% on Ethereum mainnet, ~0.1% on Arbitrum/Base.

## Per-chain x per-lender cells (Top-7 May-23 shortlist)

Cell ID convention: `<lender>_<chain>_<collateral>_<debt>_<mode>`. Ranked by `expected_apr x confidence`.

| Cell | LTV (mode) | Expected APR | Confidence | Notes |
| ---- | ---------- | ------------ | ---------- | ----- |
| `aave_v3_ethereum_wsteth_weth_emode` | 0.93 ETH_CORRELATED | 6-10% net | HIGH | Flagship; deepest liquidity; ~14x leverage at d=8 |
| `morpho_ethereum_wsteth_weth_market_0945` | 0.945 (per-market LLTV) | 8-12% net | MED-HIGH | Highest-LTV Family 1 cell; tighter HF buffer |
| `aave_v3_arbitrum_wsteth_weth_emode` | 0.93 | 6-18% net | HIGH (cell), LOW (exact params) | Cheap L2 gas -> `recursion_depth_max=10` |
| `aave_v3_base_cbeth_weth_emode` | 0.93 (low-conf) | ~3-3.5% leveraged spread | MED | Base-native LST; no bridge risk; Coinbase counterparty |
| `morpho_ethereum_susde_usdc_market_086` | 0.86 (per-market) | 15-25% net | MED | Stable-stable loop; sUSDe yield-decay + cooldown unwind latency |
| `aave_v3_ethereum_weeth_weth_emode` | 0.93 | 5-15% cash + EIGEN/ETHFI points | MED | Points discounted in APR; PendleOracle dep |
| `aave_v3_base_wsteth_weth_emode` | 0.93 (low-conf) | ~3.2-3.8% leveraged spread | MED-HIGH | Cheapest gas; Lido canonical bridge risk |

Per-chain ReserveParams + E-Mode definitions live in
`unified-api-contracts/unified_api_contracts/registry/defi_reserve_params.py` (Ethereum shipped; Arbitrum + Base
P0 unblockers per plan body Findings Triage).

## Per-cell config schema

`CARRY_RECURSIVE_BORROW_LENDING_ONLY` ARCHETYPE_CONFIG_SEED row
(`internal/architecture_v2/archetype_config.py:182`):

- `collateral_currency: "USDC"`
- `hedge_ratio: None` (no perp leg)
- `position_cap_usd: 15_000.0` (smaller than CARRY_RECURSIVE_STAKED; Family 1 not yet live-tested)
- `kill_switch_drawdown_pct: 0.04` (tighter than Family 0; no perp dampener; LST/ETH peg is dominant tail)
- `kill_switch_position_breach_pct: 0.025` (tighter; HF buffer is the load-bearing safety)

Per-cell overrides via catalog builder `_build_carry_recursive_borrow_lending_only()` in `strategy-service`
`engine/strategies/v2/target_universe/catalog.py` (Phase 3 spec). Chain-overridable defaults:
`ltv_target = liquidation_threshold - 0.05`, `rebalance_threshold_lower_hf=1.10`, `oracle_staleness_max_seconds=86400`.
`gas_budget_usd_per_loop_iter`: 25 (eth), 0.50 (arb), 0.20 (base). `recursion_depth_max`: 8 (eth), 10 (arb), 12 (base).

## Kill-switch surface

Alert codes added 2026-05-12 to `unified_api_contracts.canonical.crosscutting.alerting.codes.AlertCode` that fire
for Family 1 cells:

- `DEFI_HEALTH_FACTOR_CRITICAL` -- HF < 1.10 -> partial unwind.
- `DEFI_LIQUIDATION_IMMINENT` -- HF < `health_factor_kill` (default 1.05) -> flash-unwind.
- `DEFI_ORACLE_STALE_PAUSE` -- Chainlink ER feed > `oracle_staleness_max_seconds` -> pause new loops.
- `DEFI_RECURSIVE_LOOP_GAS_BUDGET_EXCEEDED` -- per-loop gas > budget -> stop recursion at current depth.

Family 1 cells do NOT fire `DEFI_FUNDING_RATE_FLIP` / `DEFI_CROSS_VENUE_DELTA_DRIFT` / `DEFI_PERP_VENUE_OUTAGE` --
those are Family 2 only (perp-leg surface).

## Backtest scenarios

See
[recursive-borrow-backtest-scenarios-2026-05.md](../../../16-strategy-playbooks/defi/recursive-borrow-backtest-scenarios-2026-05.md).
Family 1 applies Cat B (liquidation stress -- LST/ETH depeg cascades, HF threshold crossing, oracle staleness) and
the venue+bridge subset of Cat C (Aave pause, Morpho per-market pause, wstETH/weETH canonical bridge halt). Family 1
SKIPS Cat A (funding regime) -- no perp leg, no funding exposure.

## Batch=live status

Single-engine-class config-driven dispatch per Phase 3 design: Family 1 reuses `CarryRecursiveStakedEngine` with
`perp_leg_enabled=False` + `staking_yield_enabled=True` (LST exchange-rate appreciation feeds R_lend directly).
`strategy-service/strategy_service/engine/strategies/v2/factory.py:63` `_ARCHETYPE_ENGINE_MAP` will register the
same engine class for Family 0, 1, and 2 archetype keys. Same code path batch and live -- only the execution fill
source differs (matching engine vs live venue), per workspace `Batch = Live` invariant.

## See also

- [carry-recursive-staked.md](./carry-recursive-staked.md) -- Family 0 (staked basis carry, includes perp hedge)
- [carry-recursive-borrow-perp-hedged.md](./carry-recursive-borrow-perp-hedged.md) -- Family 2 (delta-hedged sibling)
- [../../../04-architecture/flash-loan-receiver.md](../../../04-architecture/flash-loan-receiver.md) -- flash-loan-receiver pattern for `OpeningMode.FLASH` (depth >= 5 or size >= $50k on Ethereum)
- [../../../16-strategy-playbooks/defi/venue-collateral-2026-05-07.md](../../../16-strategy-playbooks/defi/venue-collateral-2026-05-07.md) -- per-chain venue+collateral admission

## Not in this archetype

- Perp hedge leg -> [carry-recursive-borrow-perp-hedged.md](./carry-recursive-borrow-perp-hedged.md) (Family 2)
- LST staking yield as the primary alpha source (Family 0) -> [carry-recursive-staked.md](./carry-recursive-staked.md)
- Non-recursive single-stake-plus-perp -> [carry-staked-basis.md](./carry-staked-basis.md)
- Pure lending rotation without recursion -> [yield-rotation-lending.md](./yield-rotation-lending.md)
- Simple LST hold without leverage -> [yield-staking-simple.md](./yield-staking-simple.md)
