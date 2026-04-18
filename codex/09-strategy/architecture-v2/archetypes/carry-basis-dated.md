---
topology_requirements:
  isolation:
    execution-service: isolated
  co_location: []
  latency_budget_ms: 150
  min_sla_tier: standard
---

# Archetype: `CARRY_BASIS_DATED`

> **Family:** [Carry & Yield](../families/carry-and-yield.md) **Settlement model:** Position held until future expiry
> (or closed earlier if spread converges). **Code module (target):**
> `strategy-service/engine/strategies/carry_basis_dated_engine.py`

## What it does

Long spot + short dated future. Captures the futures-spot premium (contango) or discount (backwardation) as the spread
converges to zero at expiry.

## Token / position flow

```
1. ENTRY TRIGGER: basis_spread = (future_price - spot_price) / spot_price
   Enter when |basis_spread| > min_entry_threshold (after costs).

2. PAIRED ENTRY:
   - TRADE: BUY spot instrument (target_notional = allocated_equity)
   - TRADE: SELL dated future (target_notional = allocated_equity)
   Execute as near-atomic pair (ATOMIC if both legs on same venue; leader-hedge otherwise).

3. HOLD: delta-neutral basis position. Monitor spread convergence.

4. EXIT (either):
   a. Spread converges to near-zero before expiry → close both legs for realized basis
   b. Future expiry → settled automatically; spot position closed on expiry
   c. Risk trigger (stop-loss on basis widening unexpectedly) → close both legs
```

## Supported venues / instruments

- **TradFi commodities**: CL (crude) spot + CL future on CME; GC (gold) spot + GC future
- **TradFi equity index**: SPX cash vs ES future
- **Crypto dated**: Deribit BTC dated + Binance/Coinbase BTC spot; Deribit ETH dated + spot

## Expression options

- Spot: actual asset via spot venue
- Future: dated contract (expires; requires roll if held to expiry)

## Hold policies

- HOLD_UNTIL_FLIP (hold until spread reverts) or time-box to expiry

## Config schema

```yaml
spot_venue: CME # for commodities
spot_instrument: "CME:SPOT:CL"
future_venue: CME
future_instrument: "CME:FUTURE:CL:20260920"
share_class: USD
min_entry_basis_bps: 50 # 0.5% min basis after costs
exit_basis_bps: 10 # close when spread < 10 bps
max_allocated_equity_pct: 0.20 # 20% of equity per basis opp
rollover_days_before_expiry: 5
execution_policy_ref: tradfi-paired-basis-v2
```

## Execution semantics

- Both legs entered via ATOMIC (if supported) or LEADER_HEDGE (if cross-venue)
- Exit same way — atomic unwinding preferred
- Roll: close expiring future, open next-month future; rebalance spot if notional drift

## P&L attribution

- **Basis convergence P&L**: locked-in spread × notional (captured at exit/expiry)
- **Funding / carrying cost**: borrow cost of spot, storage cost (commodities)
- **Commissions + execution alpha**: per-fill

## Risk profile

- Drawdowns: very low (delta-neutral); main risk is basis widening before convergence
- Typical Sharpe: 1.5-3.0 for well-run TradFi basis
- Kill switches: basis widens beyond configured max, venue outage, one-leg liquidity collapse

## Reaction to equity change

```python
def react_to_equity_change(new_equity):
    self.equity = new_equity
    # Scale both legs to maintain delta-neutral
    target_notional = new_equity * self.config.max_allocated_equity_pct
    emit ATOMIC([
        TRADE(spot, target_notional=target_notional, direction=LONG),
        TRADE(future, target_notional=-target_notional, direction=SHORT),
    ])
```

## Example instances

```
CARRY_BASIS_DATED@cme-cl-front-second-usd-prod     (crude front vs second month)
CARRY_BASIS_DATED@cme-gc-monthly-roll-usd-prod      (gold monthly basis)
CARRY_BASIS_DATED@cme-spx-es-usd-prod               (S&P cash vs ES futures)
CARRY_BASIS_DATED@deribit-btc-quarterly-usdt-prod   (BTC spot vs Deribit quarterly)
```

## Migration from legacy

No dedicated legacy doc. Crypto dated basis is rare (perp variant more common — see `CARRY_BASIS_PERP`). TradFi dated
basis is a new codified archetype under v2.

## Not in this archetype

- **Perpetual funding carry** (funding-rate capture on perps) — `CARRY_BASIS_PERP`
- **LST staked basis** (yield-bearing staking token vs perp hedge) — `CARRY_STAKED_BASIS`
- **Calendar vol trades** (front vs back month expiry on options) — `VOL_TRADING_OPTIONS` (calendar expression)
- **Directional futures bets** (long front-month without cash leg) — `ML_DIRECTIONAL_CONTINUOUS` or
  `RULES_DIRECTIONAL_CONTINUOUS`

## See also

- Family: [carry-and-yield.md](../families/carry-and-yield.md)
- Perp variant: [carry-basis-perp.md](carry-basis-perp.md)
