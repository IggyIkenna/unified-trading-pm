---
doc_type: codex-ssot
title: "Archetype: `YIELD_STAKING_SIMPLE`"
summary:
  "YIELD_STAKING_SIMPLE archetype (family CARRY_AND_YIELD): pure liquid staking — deposit a native PoS asset (ETH/SOL)
  into an LST protocol (Lido/Rocket Pool/Jito/Marinade) to earn validator yield, no basis leg / leverage / directional
  view. HOLD_UNTIL_FLIP; realises restaking layers (CARRY_BASE/AVS_CONTINUOUS/ISSUER_SEASONAL) via dust conversion; 100
  bps LST-depeg auto-unwind kill-switch. Code backport DEFERRED."
implementation_status: design
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: [defi, strategy, staking, lst, yield, carry-yield]
related:
  [
    ../families/carry-and-yield.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-staked-basis.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-recursive-staked.md,
    ../cross-cutting/restaking-reward-economics.md,
  ]
created: 2026-04-17
authoritative_for: ["YIELD_STAKING_SIMPLE archetype spec"]
referenced_by:
  [
    /codex/09-strategy/architecture-v2/archetypes/carry-recursive-borrow-lending-only.md,
    /codex/09-strategy/architecture-v2/archetypes/defi-lp-vault.md,
    /codex/09-strategy/architecture-v2/archetypes/yield-rotation-lending.md,
    /codex/09-strategy/architecture-v2/cross-cutting/dart-manual-trade-spec.md,
    /codex/09-strategy/architecture-v2/families/carry-and-yield.md,
  ]
owner:
last_reviewed:
code_refs:
archetype: YIELD_STAKING_SIMPLE
family: CARRY_AND_YIELD
venue_universe: [LIDO, ROCKET_POOL, ETHERFI, JITO, MARINADE]
topology_requirements:
  isolation: { execution-service: isolated }
  co_location: []
  latency_budget_ms: 500
  min_sla_tier: basic
---

# Archetype: `YIELD_STAKING_SIMPLE`

> **Family:** [Carry & Yield](../families/carry-and-yield.md) **Settlement model:** Continuous — stake assets, earn
> validator reward, passively held. **Code module (target):**
> `strategy-service/engine/strategies/yield_staking_simple_engine.py`

## What it does

Pure staking: deposit native PoS asset (ETH, SOL, etc.) into liquid staking protocol to earn validator rewards. No basis
leg, no leverage, no directional view. Just held-to-earn-yield.

## Token / position flow

```
1. DEPOSIT: stake share_class capital into selected LST protocol
   - ETH → Lido → receive stETH (rebasing or wrapped wstETH)
   - ETH → Rocket Pool → receive rETH
   - SOL → Jito → receive JitoSOL
   - SOL → Marinade → receive mSOL

2. HOLD: LST balance grows via rebase (stETH) or exchange rate increase (rETH, JitoSOL, mSOL)

   For restaking-eligible LSTs (weETH, pufETH, ankrETH, ETHx; jitoSOL, mSOL when held in Jito Restaking/etc.) the realised
   yield comes from THREE on-chain-discoverable layers (see
   [restaking-reward-economics.md](../cross-cutting/restaking-reward-economics.md)):
     - CARRY_BASE              — exchange_rate appreciation (continuous, in target denomination)
     - CARRY_AVS_CONTINUOUS    — EigenLayer/Karak per-token rewards (claimed periodically; EIGEN, KARAK, AVS-specific)
     - CARRY_ISSUER_SEASONAL   — issuer-side episodic distributions (Ether.fi quarterly Seasons via Merkle distributor;
                                 Puffer / Ankr / Stader / Karak; for SOL: Jito JTO drops, Marinade MNDE)

   Layers 2 + 3 produce non-target-denomination tokens which the strategy realises via `ConvertDustInstruction` through
   the dust-conversion router — actual swap simulation through the matching engine on Binance / Uniswap / Jupiter tick
   data. Pre-TGE points (KING, MILES, KARAK pre-launch, CARROT) are tracked but unrealisable until TGE — pnl-attribution
   emits CARRY_ISSUER_SEASONAL rows with `value_eth=0` and `points_pending=true` until pricing materialises.

3. EXIT: unstake
   - Lido: swap stETH → ETH on DEX OR use Lido withdrawal queue (slow)
   - Rocket Pool: swap rETH → ETH on DEX OR use Rocket withdrawal
   - Jito: instant unstake via Kamino or slow validator unbonding
   - Marinade: instant unstake (with ~0.3% fee) or delayed (free)
```

## Supported venues / instruments

**Coverage matrix:** See
[`../category-instrument-coverage.md § 10. YIELD_STAKING_SIMPLE`](../category-instrument-coverage.md#10-yield_staking_simple)
for the authoritative protocol × chain × LST table with APY anchors and unbonding times.

## Config schema

```yaml
staking_protocol: LIDO # or ROCKET_POOL, JITO, MARINADE
asset: ETH # or SOL
share_class: ETH # typically same as underlying
exit_preference: DEX_SWAP # or PROTOCOL_WITHDRAWAL
max_allocated_pct: 1.0 # can hold 100% staked for pure yield strategies
execution_policy_ref: defi-direct-v2
rebalance_cadence_days: 30 # e.g., claim rewards + restake monthly

# Leverage + net-delta controls (universal per StrategyInstanceDefinition; Stream D 2026-05-07):
target_leverage: 1.0 # [1, 10]; always 1.0 for pure staking (no borrowed capital)
target_net_delta: 0.0 # net directional delta (0 = delta-neutral vs staking underlying)
max_underlying_move_pct: 3.0 # vol-cap clamp: skip entry if realized move > X% in 1h window
instrument_volatility_registry_lookup: true # use realized_vol_20 (1h candles) from FSS
```

## Execution semantics

- `STAKE` action type for deposits
- `UNSTAKE` action type for withdrawals (or SWAP via DEX if exit_preference = DEX_SWAP)
- Passive between events

### LegController integration

`LegController.update(slot, tick, execution_mode=ATOMIC)` resolves a 1-leg STAKE or UNSTAKE action per equity-change
event. Exit via DEX_SWAP becomes a 2-leg SWAP→TRANSFER bundle (ATOMIC if same-DEX, LEADER_HEDGE otherwise).

**Code-backport status:** DEFERRED — `carry_and_yield/yield_staking_simple.py` still wires legs hand-built. Backport
tracked in `defi_recursive_borrow_archetypes_2026_05_10.md` factory-wiring phase. Docs ship now per operator decision
2026-05-07.

## P&L attribution

- **Staking yield**: LST_balance_change × ETH_price (rebase model) OR LST_price × ETH_price (exchange rate model)
- **No execution alpha** (mostly passive deposit/withdrawal)

## Risk profile

- Drawdowns: LST depeg (stETH depegged to ~0.94 in 2022; rare but real)
- Typical Sharpe: very high in nominal terms (low vol); tail risk is depeg
- Kill switches: depeg > threshold (e.g., 1%), slashing events on validators, protocol incident
- Depeg kill-switch default: **100 bps (1%)** absolute deviation between LST oracle price and redemption NAV;
  auto-unwind on breach. Tightened per-LST when volatility warrants (e.g. 50 bps on stETH post-2022).

## Reaction to equity change

```python
def react_to_equity_change(new_equity):
    self.equity = new_equity
    target_staked = new_equity * self.config.max_allocated_pct
    return [STAKE(protocol=self.proto, target_staked_amount=target_staked)]
```

## Example instances

```
YIELD_STAKING_SIMPLE@lido-eth-prod
YIELD_STAKING_SIMPLE@rocketpool-eth-prod
YIELD_STAKING_SIMPLE@jito-sol-prod
YIELD_STAKING_SIMPLE@marinade-sol-prod
```

## Migration from legacy

No dedicated legacy doc. Simple staking was implicit in staked-basis strategies (stake + use LST as collateral). v2
extracts pure staking as a first-class archetype for clients who want just the yield without the basis complexity.

## Not in this archetype

- **Recursive leverage loops** (flash-loan amplified) — `CARRY_RECURSIVE_STAKED`
- **Staking paired with perp hedge** — `CARRY_STAKED_BASIS`
- **Protocol rotation across lending venues** — `YIELD_ROTATION_LENDING`
- **LP market making / active range management** — `MARKET_MAKING_CONTINUOUS` (AMM LP variant)

## See also

- Family: [carry-and-yield.md](../families/carry-and-yield.md)
- Staked basis (stake + short perp): [carry-staked-basis.md](carry-staked-basis.md)
- Recursive (leveraged) variant: [carry-recursive-staked.md](carry-recursive-staked.md)
