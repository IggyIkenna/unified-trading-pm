---
doc_type: codex-ssot
title: "Archetype: `CARRY_BASIS_DATED_INV`"
summary: >-
  Archetype CARRY_BASIS_DATED_INV: inverse of CARRY_BASIS_DATED — short dated future + long cash to capture
  backwardation (spot > future) convergence at expiry. Entry when (spot - future)/spot > min_entry_threshold;
  delta-neutral; shares CarryBasisDatedEngine via ALLOWED_ARCHETYPES with direction selected by archetype_id. TradFi
  energy spot crunches + crypto bear-market dated.
implementation_status: design
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: [strategy, carry, tradfi, defi, archetype, deribit]
related:
  [
    /codex/09-strategy/architecture-v2/archetypes/carry-basis-dated.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-basis-perp.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-basis-perp-inv.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-staked-basis-dated.md,
    ../families/carry-and-yield.md,
  ]
created: "2026-05-18"
authoritative_for: [CARRY_BASIS_DATED_INV archetype specification]
referenced_by:
  [
    /codex/09-strategy/architecture-v2/archetypes/carry-basis-dated.md,
    /codex/09-strategy/architecture-v2/families/carry-and-yield.md,
    /codex/09-strategy/strategy-summary.md,
  ]
owner:
last_reviewed:
code_refs:
archetype: CARRY_BASIS_DATED_INV
family: CARRY_AND_YIELD
venue_universe: [CME, DERIBIT, OKX, BYBIT]
topology_requirements:
  isolation: { execution-service: isolated, strategy-service: isolated }
  co_location: [execution-service, strategy-service]
  latency_budget_ms: 150
  min_sla_tier: premium
---

# Archetype: `CARRY_BASIS_DATED_INV`

> **Family:** [Carry & Yield](../families/carry-and-yield.md) **Settlement model:** Position held until future expiry
> (or closed earlier if spread converges). **Code module (target):**
> `strategy-service/strategy_service/engine/strategies/v2/carry_and_yield/basis_dated.py` (`ALLOWED_ARCHETYPES` =
> `CARRY_BASIS_DATED_INV`)

## What it does

Inverse of `CARRY_BASIS_DATED`: short dated future + long cash (or equivalent). Captures the futures-spot discount
(backwardation) as the spread converges to zero at expiry. The position profits when futures trade below spot — typical
in commodity supply-crunch regimes (oil/gas front-month premium) and crypto bear markets.

**Backwardation**: spot > future. Entry when
`basis_spread = (spot_price − future_price) / spot_price > min_entry_threshold`. P&L locked at entry; realised at
convergence (expiry or early exit).

## Token / position flow

```
1. ENTRY TRIGGER: basis_spread = (spot_price - future_price) / spot_price
   Enter when basis_spread > min_entry_threshold (after costs).
   Regime: spot premium (backwardation), NOT contango.

2. PAIRED ENTRY:
   - TRADE: SELL dated future (short the depressed contract)
   - HOLD: cash or cash-equivalent (long the higher-priced spot equivalent)
   Execute as near-atomic pair — ATOMIC if same venue; LEADER_HEDGE if cross-venue.

3. HOLD: delta-neutral basis position. Monitor spread convergence.

4. EXIT (either):
   a. Spread converges to near-zero before expiry → close short future + release cash
   b. Future expiry → settled automatically; cash position released
   c. Risk trigger (basis widens further — spot premium grows unexpectedly) → close both legs
```

## Relationship to CARRY_BASIS_DATED

| Dimension       | `CARRY_BASIS_DATED` (long)                 | `CARRY_BASIS_DATED_INV` (short)                |
| --------------- | ------------------------------------------ | ---------------------------------------------- |
| Regime          | Contango (futures > spot)                  | Backwardation (futures < spot)                 |
| Long leg        | Spot asset                                 | Cash / cash-equivalent                         |
| Short leg       | Dated future                               | Dated future                                   |
| Spread at entry | `(future − spot) / spot > threshold`       | `(spot − future) / spot > threshold`           |
| P&L at expiry   | Captures convergence of contango premium   | Captures convergence of backwardation discount |
| Typical regimes | TradFi financials, normal commodity curves | Energy spot crunches, crypto bear market dated |

Both archetypes use the same `CarryBasisDatedEngine` (via `ALLOWED_ARCHETYPES`); the engine reads `basis_spread_bps`
from features and selects direction based on `archetype_id`.

## Supported venues / instruments

- **TradFi (commodity)**: CME crude oil (CL) seasonal backwardation; Henry Hub natural gas; agricultural calendar rolls
- **Crypto**: Deribit BTC/ETH quarterly futures in backwardation (typically bear markets or post-halving periods)
- **Equity index**: rare; seasonal program-trading backwardation on S&P futures around rebalances

**Coverage matrix:** See
[`../category-instrument-coverage.md § 6. CARRY_BASIS_DATED_INV`](../category-instrument-coverage.md#6-carry_basis_dated_inv)
for the authoritative cash × dated-future pairings.

## Config schema

```yaml
spot_venue: CME # cash/spot leg venue
spot_instrument: "CME:SPOT:CL"
future_venue: CME
future_instrument: "CME:FUTURE:CL:20260920"
share_class: USD
min_entry_basis_bps: 50 # minimum spot premium (backwardation) after costs
exit_basis_bps: 10 # close when spread < 10 bps (near convergence)
max_allocated_equity_pct: 0.20 # 20% of equity per opportunity
rollover_days_before_expiry: 5
execution_policy_ref: tradfi-paired-basis-v2

# Leverage + net-delta controls (universal per StrategyInstanceDefinition):
target_leverage: 1.0 # [1, 10]; hard-clamped by per-instrument vol cap at entry
target_net_delta: 0.0 # net directional delta (0 = basis-neutral)
max_underlying_move_pct: 3.0 # vol-cap clamp: skip entry if realized move > X% in 1h
instrument_volatility_registry_lookup: true
```

## Execution semantics

- Both legs entered via ATOMIC (same venue) or LEADER_HEDGE (cross-venue)
- Exit symmetrically — buy back short future + release cash
- No roll needed if held to expiry (futures settle; cash released)
- If closed early: both legs closed simultaneously

### LegController integration

Same as `CARRY_BASIS_DATED` with direction inverted. `LegController.update(slot, tick)` reads `archetype_id` and sets
short leg = future, long leg = cash. ATOMIC on single-venue instruments; LEADER_HEDGE otherwise.

**Code-backport status:** DEFERRED — `carry_and_yield/basis_dated.py` still wires legs hand-built. Backport tracked in
`defi_recursive_borrow_archetypes_2026_05_10.md` factory-wiring phase.

## P&L attribution

- **Basis convergence P&L**: locked-in spread × notional (captured at exit/expiry)
- **Carry cost of short future**: daily settlement P&L on the short position (mark-to-market roll)
- **Cash yield**: interest on the long cash leg (T-bill / money-market yield on un-deployed capital)
- **Commissions + execution alpha**: per-fill

## Risk profile

- Drawdowns: low (delta-neutral); main risk is backwardation widening further before convergence
- Basis widening risk is asymmetric — commodity supply crunches can persist weeks before front-month premium collapses
- Typical Sharpe: 1.2–2.5 for well-run commodity backwardation basis (lower than contango due to spike risk)
- Kill switches: basis widens beyond `max_basis_bps`, venue outage, one-leg liquidity collapse

## Reaction to equity change

```python
def react_to_equity_change(new_equity):
    self.equity = new_equity
    target_notional = new_equity * self.config.max_allocated_equity_pct
    emit ATOMIC([
        TRADE(future, target_notional=-target_notional, direction=SHORT),
        # cash leg is implicitly the non-deployed portion — no active instruction needed
    ])
```

## Example instances

```
CARRY_BASIS_DATED_INV@cme-cl-front-second-inv-usd-prod    (crude backwardation front vs second month)
CARRY_BASIS_DATED_INV@cme-ng-seasonal-inv-usd-prod        (natgas seasonal backwardation)
CARRY_BASIS_DATED_INV@deribit-btc-quarterly-inv-usdt-prod (BTC bear-market quarterly discount)
```

## See also

- Contango variant (long spot + short future): [carry-basis-dated.md](carry-basis-dated.md)
- Perp variant (long spot + short perp): [carry-basis-perp.md](carry-basis-perp.md)
- Inverse perp (recursive borrow + perp hedge): [carry-basis-perp-inv.md](carry-basis-perp-inv.md)
- Staked basis dated (staking yield + dated future): [carry-staked-basis-dated.md](carry-staked-basis-dated.md)
- Family: [carry-and-yield.md](../families/carry-and-yield.md)

## Not in this archetype

- **Contango basis** (futures > spot, long spot + short future) → `CARRY_BASIS_DATED`
- **Perp funding capture** (not expiry-convergence; perpetual contract) → `CARRY_BASIS_PERP`
- **LST staked basis** (yield-bearing collateral + perp hedge) → `CARRY_STAKED_BASIS`
- **Directional short futures** (naked short without cash long hedge) → `ML_DIRECTIONAL_CONTINUOUS` (rules-based)
