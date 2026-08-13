---
doc_type: codex-ssot
title: "Archetype: `CARRY_RECURSIVE_STAKED`"
summary: >-
  Archetype CARRY_RECURSIVE_STAKED (Family 0): recursive leverage of a liquid-staking position (stake -> pledge ->
  borrow -> restake, ~2.5-4x effective) capturing leveraged LST yield including the three restaking layers (CARRY_BASE +
  AVS-continuous + issuer-seasonal, dust-converted). Cascading liquidation/depeg risk amplified by leverage; tight
  max_stETH_depeg_bps + HF kill-switches.
implementation_status: design
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [features-service, strategy-service]
scope: [engineer, admin]
tags: [strategy, carry, defi, execution, archetype, features]
related:
  [
    ../families/carry-and-yield.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-staked-basis.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-recursive-borrow-lending-only.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-recursive-borrow-perp-hedged.md,
    ../cross-cutting/restaking-reward-economics.md,
  ]
created: 2026-04-17
authoritative_for: [CARRY_RECURSIVE_STAKED archetype specification (Family 0 recursive staked carry)]
referenced_by:
  [
    /codex/04-architecture/capital-efficiency-patterns.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-basis-perp-inv.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-basis-perp.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-recursive-borrow-lending-only.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-recursive-borrow-perp-hedged.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-recursive-staked-config-variants.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-staked-basis.md,
    /codex/09-strategy/architecture-v2/archetypes/yield-staking-simple.md,
  ]
owner:
last_reviewed:
code_refs:
archetype: CARRY_RECURSIVE_STAKED
family: CARRY_AND_YIELD
venue_universe: [LIDO, AAVE, KAMINO, JITO, MARINADE]
topology_requirements:
  isolation: { execution-service: isolated, strategy-service: isolated }
  co_location: [execution-service, strategy-service]
  latency_budget_ms: 150
  min_sla_tier: premium
---

# Archetype: `CARRY_RECURSIVE_STAKED`

> **Family:** [Carry & Yield](../families/carry-and-yield.md) **Settlement model:** Continuous; multi-cycle leveraged
> loop. **Code module (target):** `strategy-service/engine/strategies/carry_recursive_staked_engine.py`

## What it does

Recursive leveraging of a liquid staking position: stake ETH → receive stETH → pledge on Aave → borrow ETH → stake again
→ receive more stETH → pledge → borrow → repeat. Each loop multiplies effective staking exposure by (1 / (1 − LTV ×
safety)). Typical effective leverage 3-4x on ETH. Captures leveraged staking yield, but with cascading liquidation risk.

## Token / position flow

```
Initial capital: 1 ETH

Loop 0 (initial stake):
  STAKE 1 ETH on Lido → 1 stETH
  PLEDGE 1 stETH on Aave (LTV 75%, safety buffer → effective LTV 0.60)
  BORROW 0.60 ETH

Loop 1:
  STAKE 0.60 ETH on Lido → 0.60 stETH (more)
  PLEDGE 0.60 stETH → BORROW 0.36 ETH

Loop 2:
  STAKE 0.36 → BORROW 0.216
  ...

After N loops, total stETH ≈ 1 / (1 − 0.60) = 2.5 (at effective LTV 0.6)
Total staking yield earned on 2.5 ETH vs 1 ETH of capital = 2.5x nominal
Net yield = 2.5 × total_lst_yield − 1.5 × borrow_rate − fees − depeg_risk_provision

For restaking-eligible LSTs (weETH, pufETH, ankrETH, ETHx) `total_lst_yield` is itself the SUM of THREE
on-chain-discoverable layers (see [restaking-reward-economics.md](../cross-cutting/restaking-reward-economics.md)):

  total_lst_yield = CARRY_BASE                       (exchange_rate appreciation)
                  + CARRY_AVS_CONTINUOUS_realised    (EigenLayer/Karak/Symbiotic per-token, dust-converted to ETH)
                  + CARRY_ISSUER_SEASONAL_realised   (Ether.fi/Puffer/Ankr/Stader episodic, dust-converted to ETH)

The realisation step uses `ConvertDustInstruction` through the dust-conversion router — actual swap simulation through
matching engine on stored Binance/Uniswap/Jupiter tick data, not a hardcoded haircut. realised - mark = the
`REWARD_REALISATION_SLIPPAGE` PnL factor.

Leverage amplifies all three layers: at LTV 0.85 (effective leverage 6.67x) the EigenLayer aggregate APY of 0.65%
becomes ~4.3pp net-APR uplift on the restaking-eligible cohort, which can flip pufETH from base-loss to net-profit
(verified empirically 2025-06-15..21).

Unwinding:
  Reverse loops. Each loop: REPAY → UNPLEDGE → UNSTAKE (respecting unbonding period on Lido).
```

## Supported venues / instruments

**Coverage matrix:** See
[`../category-instrument-coverage.md § 8. CARRY_RECURSIVE_STAKED`](../category-instrument-coverage.md#8-carry_recursive_staked)
for the authoritative staking × lending × share-class combinations.

## Config schema

```yaml
staking_protocol: LIDO
lending_protocol: AAVE_V3_ETHEREUM
collateral_asset: stETH
borrow_asset: ETH
target_leverage: 2.5 # effective leverage after loops
max_leverage: 3.0 # max safety bound
safety_buffer_ltv: 0.15 # 75% - 15% = 60% effective LTV
max_stETH_depeg_bps: 50 # 0.5% — very tight; recursive amplifies depeg loss
health_factor_target: 1.6
health_factor_kill: 1.25
max_allocated_equity_pct: 0.25
rebalance_cadence: 1h
execution_policy_ref: defi-lending-default-v4

# Chain constraint (UAC canonical/crosscutting/defi.ChainKind; Phase 3 defi_master 2026-05-18):
# On-chain leg (staking + lending loop) is ethereum-only today; Arbitrum added when
# Arbitrum Aave V3 stETH E-Mode cells are validated (see cell table in carry-recursive-borrow-lending-only.md).
# CeFi venues are not chain-gated.
allowed_chains: [ethereum]
```

## Execution semantics

Entry: sequence of ATOMIC multicalls per loop. Each loop is one multicall (STAKE + TRANSFER + LEND + BORROW). Unwind is
the reverse.

### LegController integration

The recursive supply/borrow loop is generated by `LegController.update(slot, tick, execution_mode=ATOMIC)`:

1. `LegController` reads the `RecursiveLoopPlan` (n_loops, ltv_per_loop) from `RecursiveLoopOrchestrator`.
2. Per-loop: STAKE → TRANSFER → LEND → BORROW fires as a single bundled `AtomicInstruction` via flash loan or sequential
   multicall depending on `opening_mode` config.
3. Health-factor gate (`LOOP_ABORTED_HF_LOW`) is checked inside `LegController.on_pre_leg_check()` before each
   iteration.

**Code-backport status:** DEFERRED — `carry_and_yield/recursive_staked.py` still chains loops inline.
`RecursiveLoopOrchestrator` ships separately in `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 5. Docs ship now
per operator decision 2026-05-07.

## P&L attribution

- **Leveraged staking yield**: (1 / (1 − effective_LTV)) × staking_yield
- **Borrow cost**: leverage × borrow_rate (negative)
- **Execution alpha**: per-leg fills
- **Depeg loss (if realized)**: major tail loss if stETH depegs

## Risk profile

- Drawdowns: moderate in normal regimes; severe during stETH depeg (amplified by leverage)
- Typical Sharpe: 2.0-3.5 in normal; can be sharply negative during depeg
- Kill switches:
  - stETH depeg > max_bps
  - Aave health factor < kill threshold
  - Chain congestion preventing deleverage

## Reaction to equity change

Rescale initial stake; recursion depth preserved.

## Example instances

```
CARRY_RECURSIVE_STAKED@lido-aave-eth-prod              (ETH on Ethereum Aave)
CARRY_RECURSIVE_STAKED@lido-aave-arbitrum-eth-prod      (ETH on Arbitrum Aave)
CARRY_RECURSIVE_STAKED@jito-kamino-sol-prod            (SOL on Kamino)
```

## Migration from legacy

| Legacy                            | Notes                          |
| --------------------------------- | ------------------------------ |
| `defi/recursive-staked-basis.md`  | Direct match                   |
| Code: `recursive_staked_basis.py` | → `CarryRecursiveStakedEngine` |

> **Sibling archetypes (Family 1/2 — added 2026-05-12):** Family 1 + Family 2 are distinct enum members consuming the
> recursive-loop infrastructure with different leg composition. See
> [carry-recursive-borrow-lending-only.md](carry-recursive-borrow-lending-only.md) (Family 1; no perp leg) +
> [carry-recursive-borrow-perp-hedged.md](carry-recursive-borrow-perp-hedged.md) (Family 2; USDC-margined perp short for
> delta neutrality across HL + Bybit).

## Not in this archetype

- **Simple LST hold** (no leverage) — `YIELD_STAKING_SIMPLE`
- **Non-recursive staked basis** (one stake + one perp hedge, no loops) — `CARRY_STAKED_BASIS`
- **Pure lending rotation** (no staking leg) — `YIELD_ROTATION_LENDING`
- **Liquidation snipe during cascade** — `LIQUIDATION_CAPTURE`
- **Pure recursive lending arb** (no staking yield, no perp) →
  [carry-recursive-borrow-lending-only.md](carry-recursive-borrow-lending-only.md)
- **Delta-hedged recursive borrow** (Family 1 + USDC perp short) →
  [carry-recursive-borrow-perp-hedged.md](carry-recursive-borrow-perp-hedged.md)

## Backtest scenarios

14 scenarios gate every cell from `design-shipped` → `live-ready`. Full taxonomy in
[../../../16-strategy-playbooks/defi/recursive-borrow-backtest-scenarios-2026-05.md](../../../16-strategy-playbooks/defi/recursive-borrow-backtest-scenarios-2026-05.md).

Key Category B scenarios relevant to this archetype's LST peg-deviation risk:

- `SCN-B1-FLASH-CRASH-LST-DEPEG`: wstETH/ETH −3% in 1 block
- `SCN-B3-WSTETH-PEG-EXTREME`: wstETH/ETH −8% (slashing)
- `SCN-B4-CBETH-PEG-COINBASE`: cbETH/ETH −5%
- `SCN-B5-ORACLE-STALE-24H`: Chainlink 24h staleness

Oracle-deviation features: `ChainlinkPegDeviationCalculator` (`"chainlink_peg_deviation"`) in
`features-service/features_service/onchain/app/calculators/`.

## See also

- Family: [carry-and-yield.md](../families/carry-and-yield.md)
- Non-recursive variant: [carry-staked-basis.md](carry-staked-basis.md)
- Sibling recursive variants (added 2026-05-12):
  [carry-recursive-borrow-lending-only.md](carry-recursive-borrow-lending-only.md) +
  [carry-recursive-borrow-perp-hedged.md](carry-recursive-borrow-perp-hedged.md)
- Venue collateral rules (LTV, haircut):
  [../../../02-venues/venue-registry-reference.md](../../../02-venues/venue-registry-reference.md)
- Backtest scenarios (Phase 12):
  [../../../16-strategy-playbooks/defi/recursive-borrow-backtest-scenarios-2026-05.md](../../../16-strategy-playbooks/defi/recursive-borrow-backtest-scenarios-2026-05.md)
