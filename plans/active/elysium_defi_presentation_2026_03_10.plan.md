# Plan: Elysium DeFi Presentation

status: active priority: P2 owner: product target: 2026-03-25 (deliver with or before fork)

## Context

Elysium Capital needs a standalone presentation demonstrating: what DeFi strategies we've built, the 14 protocols
supported, backtest results, and what the elysium-defi-lite-fork delivers to them. The presentation must stand alone —
Elysium may share it internally. Style matches the existing 10 HTML presentations in
`unified-trading-pm/presentations/`.

---

## Content Outline (9 slides)

### Slide 1 — Title

"DeFi Strategy System — Built for Elysium" Subtitle: Systematic DeFi yield capture across 14 protocols | March 2026

### Slide 2 — The DeFi Opportunity

- Onchain yield is persistent and systematic (funding rates, basis gaps, lending spreads)
- Measured difference: DeFi basis often 3–8% annualised vs CeFi
- Most institutions lack infrastructure to capture these systematically
- We built it — and you're getting it

### Slide 3 — Our DeFi Infrastructure

Table of 14 supported protocols:

| Protocol   | Category         | Chain                    | What We Do                     |
| ---------- | ---------------- | ------------------------ | ------------------------------ |
| Aave V3    | Lending          | Ethereum, Arbitrum, Base | Lend/borrow, yield monitoring  |
| Balancer   | DEX              | Ethereum, Arbitrum       | LP positions, pool yields      |
| Curve      | Stablecoin DEX   | Ethereum                 | LP, yield, pool APY monitoring |
| Ethena     | Yield stablecoin | Ethereum                 | USDe yield, basis strategy     |
| Euler      | Lending          | Ethereum                 | Supply/borrow rates            |
| Fluid      | Lending          | Ethereum                 | Yield optimization             |
| EtherFi    | Liquid staking   | Ethereum                 | eETH restaking yield           |
| Lido       | Liquid staking   | Ethereum                 | stETH staking APY              |
| Morpho     | Lending          | Ethereum, Base           | Optimized lending rates        |
| Uniswap V2 | DEX              | Ethereum                 | Liquidity + price data         |
| Uniswap V3 | Concentrated DEX | Ethereum, Arbitrum       | LP positions, fee APY          |
| Uniswap V4 | DEX              | Ethereum                 | Hook-based strategies          |
| Instadapp  | Yield aggregator | Ethereum                 | Cross-protocol optimization    |
| DefiLlama  | Analytics        | All chains               | TVL, yields, protocol data     |

### Slide 4 — Four DeFi Strategies

Explain each with diagram:

**1. Basis Strategy** — Collect funding rates

- When perp funding > threshold: short perp, long spot → capture funding rate
- Annual yield: 5–15% when funding positive (market in contango)

**2. Lending Yield** — Sustainable stablecoin yield

- Deposit USDT/USDC to Aave V3 → earn supply APY (3–6% stable)
- Supplement with Morpho/Euler for rate optimization

**3. Staked Basis** — Yield on liquid staking tokens

- Hold stETH (Lido) vs ETH basis → earn staking yield + basis
- Low risk, ~4–6% annualised

**4. Recursive Basis** — Enhanced yield via recursive positioning

- Deposit stETH as collateral → borrow ETH → re-stake → repeat
- Higher yield but higher gas cost; careful position monitoring required

### Slide 5 — Backtest Results

Reference numbers from `e2e_smoke_and_portable_backtests` plan:

- DeFi strategy suite: 20 trades, cumulative PnL = +39.2 (backtest period)
- Win rate: X% (calculate from backtest output)
- Chart: cumulative PnL over backtest period (Chart.js line chart)
- Table: per-strategy trade count, avg hold time, PnL contribution

Note: backtests are deterministic (<2s), no live API calls, reproducible.

### Slide 6 — Risk Management

- Per-protocol circuit breakers (configurable failure thresholds)
- Gas cost gating: skip any transaction if gas > $50
- Max position size per protocol (configurable)
- Slippage tolerance: 0.5% default, configurable per strategy
- Emergency stop: single env var `paper_trading=true` prevents all on-chain execution
- Yield monitoring: rebalance only when differential > 1% APY (avoids churn)

### Slide 7 — What Elysium Gets

- Complete fork of the DeFi system: `elysium-defi-system` private GitHub repo
- Full source code, documented, tested (integration tests with VCR cassettes)
- Single command: `docker-compose up` → running in paper trading mode
- Web dashboard: positions, signals, yields, PnL chart (http://localhost:8080)
- 14 DeFi protocol adapters (read data + execute transactions)
- All 4 DeFi strategies ready to run

**You own it completely.** Modify strategies, add protocols, adjust parameters.

### Slide 8 — Path to Live Trading

- Month 1: Paper trading — observe signals, review system behavior
- Month 2: Live with small capital ($10k) — validate execution, measure slippage
- Month 3+: Scale with full capital + monitoring via Grafana dashboards
- Optional: We support/maintain the system under a retainer

Setup time: <1 hour after receiving credentials. Prerequisites: Alchemy RPC URL + Ethereum wallet.

### Slide 9 — Next Steps

- [ ] Receive fork access (GitHub invite + Docker image)
- [ ] Setup session (30 min): we walk through installation + first paper trade
- [ ] Configure wallet address + RPC URL
- [ ] Run paper trading for 2 weeks
- [ ] Decision: scale to live or ask for adjustments

---

## Implementation

### P1 — Create HTML presentation

File: `unified-trading-pm/presentations/10-defi-elysium.html` Follow exact same HTML/CSS structure as existing
presentations (01–09). Use Chart.js for backtest PnL line chart (Slide 5). Use HTML table for protocol support grid
(Slide 3).

### P2 — Architecture SVG

File: `unified-trading-pm/presentations/assets/defi-architecture.svg` Data flow diagram:

```
Blockchain RPC (Alchemy) → UMI DeFi Adapters → Strategy Engine
                                                      ↓
                                             Signal Generator
                                                      ↓
                                         Execution Handlers → On-Chain Transaction
                                                      ↓
                                               Web Dashboard
```

### P3 — Backtest results data

File: `unified-trading-pm/presentations/assets/defi-backtest-data.json` Calculated from portable backtest output.
Contains: trade list, PnL series, summary stats. Used by Chart.js in Slide 5.

### P4 — Update master.html

File: `unified-trading-pm/presentations/00-master.html` Add Slide 10 to the navigation index.

### P5 — Playwright test

Add to `unified-trading-pm/presentations/tests/`:

- Verify Slide 10 loads without JS errors
- Verify PnL chart renders (Chart.js canvas visible)
- Verify protocol table has 14 rows

---

## Verification Gates

- [ ] Slide 10 renders correctly in Chrome, Firefox
- [ ] PnL chart loads with backtest data (not empty)
- [ ] Protocol table shows all 14 protocols with correct categories
- [ ] Playwright tests green
- [ ] PDF export works (for printed backup)

## Files Created / Modified

- `unified-trading-pm/presentations/10-defi-elysium.html` (new)
- `unified-trading-pm/presentations/assets/defi-architecture.svg` (new)
- `unified-trading-pm/presentations/assets/defi-backtest-data.json` (new)
- `unified-trading-pm/presentations/00-master.html` (update — add slide 10)
- `unified-trading-pm/presentations/tests/test_elysium_presentation.spec.ts` (new)

## Dependencies

- `elysium_defi_lite_fork_2026_03_10.plan.md` (content accuracy — fork details)
- `e2e_smoke_and_portable_backtests.plan.md` (backtest result numbers)
