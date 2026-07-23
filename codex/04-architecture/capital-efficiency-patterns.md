---
doc_type: codex-ssot
title: Capital Efficiency Patterns
summary:
  12 capital-efficiency patterns (cross-margin basis, Deribit portfolio-margin greek netting, Reg-T, Aave LTV recursive
  loop, Unity pooled book, flash-loan atomic composites, …) — each names required venue features + the CaR / gross / net
  risk-rule ceilings that bound joint exposure; per-client allocation summed ≤100%.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-service, execution-service]
scope: [engineer, admin]
tags: [capital, execution, defi, cefi, strategy, risk]
related:
  [
    /codex/04-architecture/capital-flow-model.md,
    /codex/04-architecture/capital-structure-and-regulatory.md,
    /codex/09-strategy/architecture-v2/cross-cutting/venue-account-coordination.md,
  ]
created: 2026-04-17
authoritative_for: [capital-efficiency patterns and joint-exposure risk ceilings]
referenced_by:
  [
    /codex/02-venues/venue-registry-reference.md,
    /codex/03-services/venue-capability-registry.md,
    /codex/04-architecture/capital-flow-model.md,
    /codex/04-architecture/capital-structure-and-regulatory.md,
    /codex/04-architecture/risk-preflight-flow.md,
    /codex/04-architecture/risk-rule-taxonomy.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-basis-perp.md,
    /codex/09-strategy/architecture-v2/archetypes/market-making-continuous.md,
  ]
owner:
last_reviewed: 2026-05-17
code_refs:
---

# Capital Efficiency Patterns

> **What it is:** The recurring patterns that unlock capital efficiency when multiple strategies share a venue account
> or when a single strategy uses structural venue features (cross-margin, portfolio margin, LTV-based lending, greek
> netting, atomic composites). Each pattern names the venue features it requires and the coordination primitives it
> depends on.

## Why this matters

Running each strategy with dedicated capital on a dedicated account wastes:

- Margin (each strategy posts full margin independently)
- Bandwidth (redundant positions that could offset)
- Fees (VIP tiers require aggregate volume)
- Capital at rest (idle collateral)

Capital efficiency patterns reclaim that waste — sometimes 2–5× effective leverage on the same underlying equity.

## Pattern 1: Cross-margin basis + directional (CEX)

**Setup:**

- Strategy A: directional long BTC (perp)
- Strategy B: basis trade BTC (spot + perp)
- Same client, same Binance account, cross-margin enabled

**Benefit:** Strategy B's short perp leg contributes margin relief to Strategy A's long perp (opposite sign on perp
side). Effective margin use lower than sum-of-parts.

**Requirements:**

- Venue supports cross-margin
- Venue-account coordination primitives active (aggregation + pre-flight)
- Attribution rules defined for shared positions

**Trap:** Liquidation cascade — if cross-margin breaches, BOTH strategies' positions liquidate together. Risk gates must
model joint risk, not per-strategy.

## Pattern 2: Portfolio margin — greek netting (Deribit)

**Setup:**

- Multiple vol strategies on Deribit with different option positions
- Same client, same Deribit account, portfolio margin enabled

**Benefit:** Portfolio margin nets greeks across the book — long calls + short puts at same strike offset. Margin
requirement scales with net greek exposure, not sum of individual option positions.

**Requirements:**

- Deribit portfolio margin access (qualification-based)
- Execution-service computes joint greek state for pre-flight
- Risk-and-exposure-service sees joint greeks

**Trap:** Synthetic perp via long-call + short-put can become a perp-equivalent without "showing" as a perp position —
risk models must account for equivalent delta.

## Pattern 3: Reg-T netting (IBKR equities)

**Setup:**

- Long equity basket via IBKR
- Short-ETF hedge via IBKR
- Same IBKR account

**Benefit:** Reg-T margin rules net long and short positions in overlapping names. Effective margin lower.

**Requirements:**

- IBKR account with margin (not cash-only)
- Execution-service respects IBKR's position-level netting

## Pattern 4: LTV-based DeFi lending loop

**Setup:**

- Supply stETH as collateral on Aave (75% LTV for stETH)
- Borrow ETH against it
- Stake borrowed ETH via Lido → wstETH
- Supply wstETH back as collateral
- Borrow again
- Recursive loop

**Benefit:** Leverage ETH staking yield by ~3× (depending on LTV decay per recursion). See
[/codex/09-strategy/architecture-v2/archetypes/carry-recursive-staked.md](/codex/09-strategy/architecture-v2/archetypes/carry-recursive-staked.md).

**Requirements:**

- Protocol supports wstETH collateral (Aave V3 ETH)
- LST haircut model in execution-service pre-flight
- ATOMIC_ON_CHAIN for single-tx loop (else per-step rollback risk)
- Health factor monitor in live ops

**Trap:** stETH depeg (2022-06 / 2024-stress) liquidates the loop cascading. HF alerts + auto-deleveraging required.

## Pattern 5: Delta-hedged vol on same account

**Setup:**

- Long straddle on Deribit
- Delta hedge via Deribit perp

**Benefit:** Portfolio margin recognizes the delta-hedge offsets the option delta; margin scales with vega + gamma +
second-order, not notional.

**Requirements:**

- Deribit portfolio margin
- Delta-hedge executed on same account (not cross-venue)

## Pattern 6: LP + borrow on same chain

**Setup:**

- Supply USDC/WETH LP position on Uniswap V3
- Use LP NFT as collateral on some protocols (e.g., Gamma, Panoptic)
- Borrow against it
- Deploy borrowed into farming / yield

**Benefit:** LP earns fees; collateral serves dual purpose.

**Requirements:**

- Protocol accepts LP NFTs as collateral (limited set)
- Rebalancing LP range triggers reconciliation of LTV

**Trap:** Concentrated LP exit price differs from entry; collateral value shifts with price; LTV can blow up.

## Pattern 7: Unity pooled book with child arb

**Setup:**

- Single Unity wallet serves multiple sports strategies
- Strategy A: arb on 1X2
- Strategy B: ML directional on over/unders
- Strategy C: market making on totals

**Benefit:** One deposit serves all three strategies; Unity's internal SOR picks best child book per leg;
subscription-waiver turnover thresholds crossed faster via aggregate volume.

**Requirements:**

- Unity meta-broker adapter
- PBMS attribution per strategy (parsed from Unity fill reports with child-book tag)
- Per-strategy position accounting despite shared wallet

## Pattern 8: IBKR basket netting

**Setup:**

- Stat arb cross-sectional: 100 longs, 100 shorts
- Portfolio margin IBKR

**Benefit:** IBKR portfolio margin recognizes factor-neutral basket as lower-risk; margin requirement scales with
residual beta/vol, not gross.

**Requirements:**

- IBKR portfolio margin eligibility (qualification)
- Basket-level margin model in pre-flight

## Pattern 9: Binance cross-margin netting with ~5% headroom

**Setup:**

- Hedged basis: long spot + short perp at Binance
- Same Binance account, cross-margin

**Benefit:** Binance cross-margin recognizes the hedge; practical requirement ~5% of total notional (vs ~20% on isolated
margin per leg).

**Requirements:**

- Cross-margin enabled at Binance
- Pre-flight recognizes hedge; doesn't double-count margin

**Trap:** Funding-rate fluctuations still require margin buffer for variation; 5% is minimum-at-rest, not total need.

## Pattern 10: Same-chain atomic composites

**Setup:**

- Flash loan → liquidate underwater position → sell collateral → repay flash loan → keep spread
- Single Ethereum tx

**Benefit:** Zero capital required for the flash-loan loop; only gas.

**Requirements:**

- Flash loan receiver contract deployed (per CLAUDE.md, `FlashLoanReceiver.sol`)
- Error classification for flash-loan reverts (per `DefiErrorCode`)
- Gas budget + MEV-aware submission

## Pattern 11: Unity deposit leverage (commercial)

**Setup:**

- Deposit $10.8k (refundable at $5.3M volume)
- Trade via Unity
- Deposit acts as bond, not margin — doesn't consume buying power

**Benefit:** Unity extends credit-against-deposit; capital-efficient relative to per-book deposits.

**Requirements:**

- Unity relationship established
- Subscription: $2.6k/mo (waived at $260k/mo turnover)

## Pattern 12: Options spread vs outright

**Setup:**

- Instead of outright long call, deploy call spread (long K1 + short K2)

**Benefit:** Portfolio margin requirement scales with max loss = K2 - K1 - premium, not notional.

**Requirements:**

- Portfolio margin account

**Tradeoff:** Capped upside; pick when upside capping is acceptable.

## Cross-pattern interactions

Multiple patterns compose:

- Pattern 2 (portfolio margin) + Pattern 5 (delta-hedge) on Deribit
- Pattern 4 (LTV loop) + Pattern 10 (atomic composite) on Aave
- Pattern 1 (cross-margin) + Pattern 9 (basis) on Binance
- Pattern 7 (Unity pool) + Pattern 11 (deposit leverage) on Unity

Venue-account coordination primitives
([/codex/09-strategy/architecture-v2/cross-cutting/venue-account-coordination.md](/codex/09-strategy/architecture-v2/cross-cutting/venue-account-coordination.md))
make composition safe.

## Risk scaling

Capital efficiency is NOT free — risk concentration grows with efficiency:

- Higher leverage → tighter liquidation triggers
- Shared account → joint liquidation
- Greek netting → correlated blow-ups in regime shifts
- LP-as-collateral → dual price dependency

Risk-and-exposure-service must model joint risk, not per-strategy. Family-level limits + correlation caps handle this.

## Per-archetype Capital-at-Risk ceiling cross-link

Each capital-efficiency pattern above unlocks leverage but also concentrates tail risk into specific stress scenarios
(stETH depeg, exchange outage, oracle desync, liquidation cascade). The **`CapitalAtRiskCeiling` RiskRuleTrigger** is
the gate that bounds the joint exposure introduced by combining these patterns. The trigger declares:

```python
CapitalAtRiskCeiling(
    trigger_type="capital_at_risk_ceiling",
    max_var_usd=Decimal("25000"),
    confidence=Decimal("0.95"),
    scenario_id="pyth_solana_depeg",
)
```

A rule with this trigger is scoped per archetype (`RiskRuleScope.PER_ARCHETYPE`); its evaluator queries the family
aggregator for the archetype's 95% VaR under the named scenario and compares to `max_var_usd`. Breach → `BLOCK` — the
archetype cannot open new positions until the VaR drops below the ceiling.

The same scope axis carries **per-account** `MaxGrossExposure` + `MaxNetExposure` triggers (closed-union members in
[risk-rule-taxonomy.md](risk-rule-taxonomy.md#riskruletrigger-uac-canonicalcrosscuttingrisk_rulepy)) that bound the
account-wide gross/net regardless of how cleverly the capital-efficiency patterns net out. The two layers compose:

1. **Account-level guards** (`MAX_GROSS_EXPOSURE`, `MAX_NET_EXPOSURE`, `MAX_DAILY_LOSS`) — the floor that ANY pattern
   combination must respect; independent of per-archetype tuning.
2. **Per-archetype CaR ceiling** (`CAPITAL_AT_RISK_CEILING`) — bounds the tail exposure of each archetype's chosen
   pattern stack (e.g. Pattern 4 LTV loop + Pattern 10 atomic composite for `carry_recursive_staked`).
3. **Family aggregate** (`FAMILY_GROSS_EXPOSURE_CAP`, `FAMILY_CAPITAL_AT_RISK_CEILING`,
   `FAMILY_CORRELATION_WITH_OTHER_FAMILY`) — the **family aggregator** in UTL rolls up per-archetype state into
   per-family state (sum-of-positions + max drawdown + cross-family correlation matrix from rolling returns) and feeds
   rule_evaluator at family scope. This is the layer that catches "all LST-family + funding-arb-family share oracle-risk
   exposure on Pyth Solana" — per-archetype rules would miss the cross-family correlation; the aggregator surfaces it.

Capital-allocation gates compose with these risk-rule pre-flight checks: every order goes through
[`risk_preflight(order, context)`](risk-preflight-flow.md) BEFORE reaching execution-service. If any of the three layers
above fires `BLOCK`, the order is rejected at Layer 2; if `SCALE_DOWN` fires (e.g. correlation creeping toward the
family-level ceiling), the order proceeds at the min-aggregated scale_factor. The capital-efficiency patterns are NOT
preflight-aware — they're pure structural setups; the rule registry is the gate that bounds their joint exposure.

See
[risk-rule-taxonomy.md § `RiskRuleTrigger`](risk-rule-taxonomy.md#riskruletrigger-uac-canonicalcrosscuttingrisk_rulepy)
for the full closed-union of trigger types + [risk-preflight-flow.md](risk-preflight-flow.md) for the every-order
integration path.

## Venue-feature requirements summary

| Pattern               | Venue feature required         |
| --------------------- | ------------------------------ |
| Cross-margin basis    | Binance/OKX/Bybit cross-margin |
| Portfolio margin vol  | Deribit portfolio margin       |
| Reg-T netting         | IBKR margin                    |
| LTV loop              | Aave V3 (wstETH 75%)           |
| Delta-hedged same acc | Deribit portfolio margin       |
| LP + borrow           | Gamma / Panoptic / etc.        |
| Unity pool            | Unity agreement                |
| IBKR basket           | IBKR portfolio margin          |
| Binance basis ~5%     | Binance cross-margin           |
| Atomic composites     | EVM chain                      |
| Unity deposit         | Unity commercial terms         |
| Spread vs outright    | Portfolio margin account       |

## Cross-references

- Venue-account coordination:
  [/codex/09-strategy/architecture-v2/cross-cutting/venue-account-coordination.md](/codex/09-strategy/architecture-v2/cross-cutting/venue-account-coordination.md)
- Venue registry: [/codex/02-venues/venue-registry-reference.md](/codex/02-venues/venue-registry-reference.md)
- Unity: [/codex/02-venues/unity-integration.md](/codex/02-venues/unity-integration.md)
- Recursive staked:
  [/codex/09-strategy/architecture-v2/archetypes/carry-recursive-staked.md](/codex/09-strategy/architecture-v2/archetypes/carry-recursive-staked.md)
- Liquidation archetype:
  [/codex/09-strategy/architecture-v2/archetypes/liquidation-capture.md](/codex/09-strategy/architecture-v2/archetypes/liquidation-capture.md)
- Risk gates:
  [/codex/09-strategy/architecture-v2/cross-cutting/risk-gates.md](/codex/09-strategy/architecture-v2/cross-cutting/risk-gates.md)
- Risk rule taxonomy (closed-set RiskRuleId / RiskRuleScope / RiskRuleTrigger):
  [risk-rule-taxonomy.md](risk-rule-taxonomy.md)
- Risk pre-flight aggregation (every-order path): [risk-preflight-flow.md](risk-preflight-flow.md)
- Risk-breaker escalation seam (cross-pattern joint risk): [risk-breaker-seam.md](risk-breaker-seam.md)

## Per-Client Capital Allocation

Capital is allocated to archetypes **per client** via `ClientShareClassSubscription`. Each subscription declares a
percentage allocation for a specific archetype; the `AllocationEngine` in UTL routes capital accordingly.

### Allocation rules

- `AllocationEngine` resolves per-archetype capital by multiplying the archetype's total available capital by
  `allocation_pct` from each active `ClientShareClassSubscription`.
- When **multiple clients** subscribe to the same archetype, their `allocation_pct` values are summed across all active
  subscriptions. The sum MUST be ≤ 100% across all clients for a given archetype — the engine enforces this invariant at
  subscription write time and at every allocation decision.
- The engine emits an `AllocationDecisionEvent` for each `AllocationDecision` produced; downstream consumers
  (position-balance-monitor, risk-and-exposure-service) react to these events.

### Suspension on drawdown

When a client's drawdown for a given (client, archetype) pair exceeds `ClientRiskPreferences.max_drawdown_pct`, the
corresponding `ClientShareClassSubscription` transitions to `SUSPENDED_DRAWDOWN`. The `AllocationEngine` treats any
subscription with `status == SUSPENDED_DRAWDOWN` as having `allocation_pct = 0` — **no capital is allocated to that
(client, archetype) pair** until the subscription is manually re-activated by an operator.

This ensures a single client hitting their drawdown limit does not disrupt other clients' allocations on the same
archetype — the suspended subscription's share is simply unallocated (not redistributed).

### Example

| Client      | Archetype                    | `allocation_pct` | Status               | Capital allocated      |
| ----------- | ---------------------------- | ---------------- | -------------------- | ---------------------- |
| demo-client | `carry_staked_basis`         | 60%              | `ACTIVE`             | 60% of archetype total |
| client-B    | `carry_staked_basis`         | 30%              | `ACTIVE`             | 30% of archetype total |
| client-C    | `carry_staked_basis`         | 10%              | `SUSPENDED_DRAWDOWN` | 0% (suspended)         |
| demo-client | `arbitrage_price_dispersion` | 80%              | `ACTIVE`             | 80% of archetype total |

In this example, `carry_staked_basis` has 90% allocated (60 + 30; client-C's 10% is suspended). The remaining 10% is
unallocated.

### Cross-references

- UAC `ClientShareClassSubscription` — subscription type; fields: `client_id`, `share_class_id`, `archetype`,
  `allocation_pct`, `status` (`ACTIVE` / `SUSPENDED_DRAWDOWN` / `TERMINATED`)
- UAC `AllocationDecision` — per-(client, archetype) capital allocation output; fields: `client_id`, `archetype`,
  `allocated_usd`, `allocation_pct`, `reason`
- UAC `AllocationDecisionEvent` — event emitted on each decision; consumed by PBMS + risk service
- UTL `AllocationEngine` — resolves allocations per archetype; enforces sum ≤ 100%; emits `AllocationDecisionEvent`
- Client lifecycle prerequisite: subscriptions require `ClientOnboardingState == SUBSCRIBED` (or later) —
  [`client-lifecycle-state-machine.md`](client-lifecycle-state-machine.md)
- Plan: `wallet_treasury_client_flow_2026_05_10.md` Phase 2.C (UAC subscription types) + Phase 3.C (AllocationEngine
  UTL)

## Not in this doc

- **Per-venue margin formula implementations** — venue registry + execution-service pre-flight
- **LTV haircut tables** — venue capability registry
- **Greek calculator** — pricing engine / options service
- **Liquidation thresholds** — per-venue capability registry
- **Flash-loan receiver internals** — `deployment-service/contracts/FlashLoanReceiver.sol`
