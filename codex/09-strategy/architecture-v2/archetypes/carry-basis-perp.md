---
topology_requirements:
  isolation:
    execution-service: isolated
  co_location: []
  latency_budget_ms: 150
  min_sla_tier: standard
---

# Archetype: `CARRY_BASIS_PERP`

> **Family:** [Carry & Yield](../families/carry-and-yield.md) **Settlement model:** Continuous; positions maintained as
> long as funding rate is favorable. **Code module (target):**
> `strategy-service/engine/strategies/carry_basis_perp_engine.py`

## What it does

Long spot + short perpetual future. Captures funding rate (paid by perp longs to perp shorts when perp > spot) while
staying delta-neutral. Position rebalanced when funding rate drops below threshold or moves to another venue.

## Token / position flow

```
1. FUNDING RATE SCAN: monitor funding rates across eligible perp venues for the target asset.
   Enter when annualized_funding > min_funding_threshold (after all costs).

2. PAIRED ENTRY:
   - TRADE: BUY spot (target_notional = allocated_equity)
   - TRADE: SELL perp at venue with highest funding (target_notional = allocated_equity)
   ATOMIC if same venue (e.g., Binance cross-margin netting — enormous capital efficiency).
   LEADER_HEDGE if cross-venue.

3. HOLD: collect funding every funding tick (4h / 8h typical).

4. REBALANCE TRIGGERS:
   - Funding drops below exit_threshold → close position
   - Better funding at another venue → migrate (close old, open new — sequential, not atomic)
   - Delta drift > rebalance_band → rebalance leg sizes
   - Equity change → scale both legs

5. EXIT: close both legs symmetrically (ATOMIC or LEADER_HEDGE).
```

## Supported venues / instruments

Any (spot, perp) pair:

- **Single-venue netted (best capital efficiency)**: Binance spot + Binance perp, OKX spot + OKX perp, Bybit spot +
  Bybit perp
- **Cross-venue**: Uniswap/Coinbase spot + Hyperliquid/Deribit/Binance perp; L2 spot (Uniswap Arbitrum) + CEX perp
- **Crypto primary**: BTC, ETH, SOL; occasionally top-10 alts
- **Multi-coin rotation**: config to rotate across eligible assets based on funding-rate ranking

## Expression options

- Spot: actual asset holding
- Perp: perpetual future

## Hold policies

- CONTINUOUS — hold while funding favorable
- Rebalance cadence config (e.g., re-evaluate venue/coin selection every 4h/8h)

## Config schema

```yaml
spot_venue: UNISWAP_V3_ETHEREUM # or BINANCE for netted
spot_instrument: "UNISWAP_V3:ETH-USDC"
perp_venue: HYPERLIQUID
perp_instrument: "HYPERLIQUID:PERPETUAL:ETH-USD"
target_funding_rate_bps: 80 # 80 bps (8%) annualized minimum
exit_funding_rate_bps: 20 # exit when funding drops below 20 bps
delta_hedge_rebalance_pct: 2 # rebalance if delta > 2%
staking_method: fractional_kelly
max_allocated_equity_pct: 0.30
share_class: USDT
execution_policy_ref: cefi-defi-combined-v7
exploit_venue_netting: true # when spot + perp on same venue
```

## Execution semantics

- Entry: ATOMIC if spot+perp on same venue (Binance batch API); LEADER_HEDGE otherwise
- Exit: same
- Funding collection: passive; PBMS tracks funding accrual per position

## P&L attribution

- **Funding P&L**: funding_rate × notional × holding_period (earned)
- **Basis change P&L**: entry_basis - exit_basis (minor, tends to zero for perps)
- **Fees / slippage**: per-fill
- **Execution alpha**: vs benchmark

## Risk profile

- Drawdowns: very low (delta-neutral); tail risks are funding reversal, spot/perp spread widening during stress
- Typical Sharpe: 1.5-3.5 for well-run basis (high thanks to low vol + consistent funding)
- Kill switches: funding flips negative beyond hold threshold, LST/spot depeg (if variant with LST), venue outage

## Reaction to equity change

Both legs scale proportionally → ATOMIC reconciliation to avoid delta breach.

## Example instances

```
Single-venue netted:
  CARRY_BASIS_PERP@binance-btc-usdt-prod
  CARRY_BASIS_PERP@okx-eth-usdt-prod
  CARRY_BASIS_PERP@bybit-sol-usdt-prod

Cross-venue:
  CARRY_BASIS_PERP@uniswap-hyperliquid-eth-usdt-prod
  CARRY_BASIS_PERP@coinbase-deribit-btc-usd-prod
  CARRY_BASIS_PERP@uniswap-arbitrum-hyperliquid-eth-usdt-prod

Multi-coin rotation:
  CARRY_BASIS_PERP@binance-multicoin-usdt-prod                 (auto-rotate across BTC/ETH/SOL)
```

## Migration from legacy

| Legacy                                                                         | Notes                                                                     |
| ------------------------------------------------------------------------------ | ------------------------------------------------------------------------- |
| `defi/basis-trade.md`                                                          | Generic perp basis                                                        |
| `defi/btc-basis-trade.md`, `defi/l2-basis-trade.md`, `defi/sol-basis-trade.md` | All same archetype, different instance configs                            |
| `defi/ethena-benchmark.md`                                                     | Ethena's USDe is conceptually a staked-basis product; reference benchmark |
| Code: `basis_trade.py`, `btc_basis.py`, `sol_basis.py`, `l2_basis.py`          | All → `CarryBasisPerpEngine`                                              |

## Not in this archetype

- **Dated-contract basis** (expiry-based arbitrage) — `CARRY_BASIS_DATED`
- **LST collateral on the spot leg** (yield-bearing token + perp hedge) — `CARRY_STAKED_BASIS`
- **Flash-loan leveraged loops on top of staked basis** — `CARRY_RECURSIVE_STAKED`
- **Directional futures / perp trades** (no paired spot) — `ML_DIRECTIONAL_CONTINUOUS` or `RULES_DIRECTIONAL_CONTINUOUS`
- **Cross-venue perp spread arbitrage** (funding-rate differential between two perp venues for the same asset) —
  `ARBITRAGE_PRICE_DISPERSION`

## See also

- Family: [carry-and-yield.md](../families/carry-and-yield.md)
- Staked variant: [carry-staked-basis.md](carry-staked-basis.md)
- Recursive variant: [carry-recursive-staked.md](carry-recursive-staked.md)
- Capital efficiency on same-venue netted basis:
  [../../../04-architecture/capital-efficiency-patterns.md](../../../04-architecture/capital-efficiency-patterns.md)
