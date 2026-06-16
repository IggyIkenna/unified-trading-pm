---
scope: [engineer, admin]
last_reviewed: 2026-05-18
---

# P&L Attribution — Cross-Cutting Concern

## Hard Rules

### 1. P&L attribution uses canonical factors only

Every P&L component maps to one of the canonical attribution factors. No ad-hoc "other" or "unclassified" buckets. If a
P&L component does not fit an existing factor, a new factor must be formally added to the canonical list.

### 2. Attribution is identical in live and batch

The `PnLCalculator` in strategy-service runs the same code path for live and batch modes. Live mode processes real-time
fills; batch mode replays historical fills. The attribution logic, factor decomposition, and output schema are
identical.

```
Live:  CanonicalFill (from execution-service) → PnLCalculator → PnLAttribution
Batch: CanonicalFill (from CSV replay)        → PnLCalculator → PnLAttribution
```

### 3. T+1 reconciliation is mandatory

Every strategy instance runs a T+1 batch reconciliation that recomputes yesterday's P&L from settlement data. The batch
result is the official P&L. Live P&L is indicative only — it may differ due to delayed fills, funding settlements, or
price corrections.

```
Live P&L (indicative):
  Updated on every fill and funding event
  Used for: real-time dashboards, risk monitoring, position sizing

Batch P&L (official):
  Computed at T+1 from settled data
  Used for: reporting, performance measurement, fee calculation
  OVERRIDES live P&L where they differ
```

### 4. DeFi lending/borrowing yield is derived from on-chain INDEXES, never APY

**APY is a presentation view, NEVER a primary in P&L attribution.** Every lending/borrowing yield component is computed
from the protocol's on-chain index growth between the prev-block and now-block snapshots:

```
supply_yield(prev_block, now_block) = aToken_balance × (liquidity_index_now / liquidity_index_prev - 1)
borrow_cost(prev_block, now_block)  = debt_token_balance × (variable_borrow_index_now / variable_borrow_index_prev - 1)
```

The on-chain `liquidity_index` (Aave) / `supplyIndex` (Compound V3) IS the rate — it accrues continuously every block
per the protocol's interest-rate model. APY is just a 365-day annualization of the same accrual; using APY introduces a
discretization error AND loses the per-block fidelity needed for block-aligned P&L attribution.

**Treasury wiring**: positions are tracked as the actual aToken / debt-token balance (Aave aUSDC, vDebt-USDC; Compound
V3 base-token + collateral-token balances). position-balance-monitor-service reads on-chain
`balanceOf(aToken_addr, user)` per block → balance growth IS the yield. The CARRY_LENDING_SUPPLY / CARRY_LENDING_BORROW
factor rows below formalize the computation.

**Banned patterns** (review-blocking):

- `supply_pnl = supply_usd × apy × time_fraction` — uses APY proxy instead of index growth.
- `borrow_cost = borrow_usd × borrow_apy / 365 × days` — same issue, mirror side.
- Tracking position in USD rather than aToken units — discards the on-chain growth signal.
- Reading `currentLiquidityRate` / `currentVariableBorrowRate` (the APR view) instead of `liquidityIndex` /
  `variableBorrowIndex` (the cumulative-growth view).

**Backfill prerequisite**: MTDS `lending_indices` parquet must carry per-block `liquidity_index` +
`variable_borrow_index` columns for the historical window covered by backtest replay. Currently captured per
[`amm-slippage-simulation.md`](../../../04-architecture/amm-slippage-simulation.md) § "Per-protocol IRM parameter
capture" — see also `plans/active/issues/aave_irm_slope_capture_dropped_2026_05_12.md` for the slope-fields capture gap
fix.

### 5. Staking yield: wrapped (price-delta) vs rebasing (balance-delta) — distinct attribution paths

Both produce the same economic yield but the **data source differs**:

| Token shape                | Examples                                                                                        | Yield mechanism                                                                 | Attribution factor                                                      | Data source                                                                                                                                       |
| -------------------------- | ----------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- | ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Wrapped / non-rebasing** | wstETH, weETH, cbETH (ETH side); jitoSOL, mSOL, bSOL (Solana side)                              | On-chain exchange rate accretes; user balance stays fixed                       | `CARRY_BASE` = `holding × (exchange_rate_now / exchange_rate_prev - 1)` | `lst-rates` parquet — oracle price from issuer's stake pool contract (`rETH.getExchangeRate()`, `wstETH.stEthPerToken()`, Jito stake-pool getter) |
| **Rebasing**               | stETH (Lido native), ankrETH (rebasing variant), native unstaked SOL via validator-distribution | User balance grows mechanically each rebase epoch; price stays ~1:1 with native | `CARRY_BASE_REBASING` = `(balance_now - balance_prev) × token_price`    | position-balance-monitor `balanceOf(token, wallet)` per block + `lst-rates` for token price                                                       |

**Native chain-side direct** (preferred over oracle proxy where available): both shapes can sometimes be derived
directly from on-chain validator-distribution events (Ethereum beacon `Withdrawal` events + execution-layer rewards;
Solana `getInflationReward` per-epoch). The codex
[`amm-slippage-simulation.md`](../../../04-architecture/amm-slippage-simulation.md) § "Per-protocol capture detail"
table lists the canonical chain-native sources per protocol. The oracle / exchange-rate path is the proxy fallback when
direct chain-native capture is unavailable.

**Centralized-exchange collateral form** (per
[`codex/09-strategy/architecture-v2/archetypes/carry-staked-basis.md`](../archetypes/carry-staked-basis.md) § "Venue ×
LST collateral matrix"):

| CEX                             | Accepted LST collateral                                              | Form                                                               | Attribution factor when posted as cross-margin                                                  |
| ------------------------------- | -------------------------------------------------------------------- | ------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------- |
| **Bybit (UTA)**                 | stETH + METH + USDe                                                  | **Rebasing** (Bybit absorbs daily rebase server-side at UTA layer) | `CARRY_BASE_REBASING` — position-balance-monitor reads Bybit subaccount balance delta per day   |
| **OKX (multi-currency margin)** | wstETH + cbETH + weETH (haircut TBD per Stream A live probe)         | **Wrapped non-rebasing**                                           | `CARRY_BASE` — `holding × (exchange_rate_now / exchange_rate_prev - 1)` per the on-chain getter |
| **Deribit (X:PM/X:SM)**         | stETH (7.5% haircut, offsets ETH-perp directly — 2026-01-13 onwards) | **Rebasing**                                                       | `CARRY_BASE_REBASING`                                                                           |
| **Drift (Solana CL DEX)**       | jitoSOL + mSOL (native non-rebasing)                                 | **Wrapped non-rebasing**                                           | `CARRY_BASE`                                                                                    |

Implication for `carry_staked_basis` archetype `_build_legs` discipline: the on-chain `STAKE` leg shape MUST match the
perp venue's accepted collateral form. ETH-side: Bybit + Deribit consume the rebasing stETH directly
(`Lido.submit → stETH → TRANSFER`); OKX requires wrapping (`Lido.submit → stETH → wstETH wrap → TRANSFER`). Solana side:
jitoSOL / mSOL / bSOL are natively non-rebasing — no wrap step needed for Drift. **Banned**: posting wrapped wstETH to
Bybit (Bybit's UTA pricing is calibrated on stETH share-price; wstETH delta diverges) — and conversely posting rebasing
stETH to OKX (OKX has no daily-rebase reconciliation; the position would mark as undersized post- rebase).
Archetype-engine config (`default_basis_trade.yaml`) discriminates by `perp_venue` to select the right wrap-or-not step
at `_build_legs` time.

**Banned patterns**:

- Single `CARRY_BASE` factor with shape-agnostic computation — misses the rebasing case (balance grows but the
  exchange-rate-change formula returns 0).
- Treating stETH and wstETH as identical for attribution — they have DIFFERENT data sources.
- CEX collateral posted in the rebasing form — re-collateralization risk on every Lido rebase.

### 6. Gas fees: real per-block capture, treasury-provisioned, P&L-attributed

Gas is a P&L factor on every DeFi transaction. Three discipline rules:

1. **Real per-block capture, not modeled**: MTDS `gas_fee_handler` writes per-(chain, block) `gas_used`, `gas_price`,
   `native_token_usd_price_at_block` to the `gas_fees` data_type. Strategy decision + execution simulation read the
   actual per-block gas — no synthetic / averaged proxies in either batch replay or live preflight.
2. **Native-gas-token treasury check + auto-provision**: every DeFi strategy preflight (`StrategyEngineV2.on_tick()` +
   execution-service preflight gate) verifies the wallet's native-gas-token balance per chain (ETH on
   Ethereum/Arbitrum/Optimism/Base; SOL on Solana; BNB on BSC; MATIC on Polygon; AVAX on Avalanche; GNO on Gnosis)
   exceeds a configured threshold. When below threshold, the strategy auto-provisions by routing X% of starting capital
   into the native-gas token via the spot venue (default `native_gas_reservation_pct = 1.0%` per DeFi strategy config;
   tunable per chain via `default_basis_trade.yaml` `native_gas_reservation_pct_by_chain`). **Hard block** when balance
   < threshold AND auto-provision route unavailable — strategy emits `record_failed(GAS_INSUFFICIENT)` instead of
   attempting a tx that will revert at validator level.
3. **GAS as a P&L factor**: every fill on a DeFi venue contributes `-(gas_used × gas_price × native_usd_at_tx_block)` to
   the `GAS` factor (see Factor Definitions table). Strategy alpha vs execution alpha layer rule: gas is `EXECUTION`
   layer for production trades (counterparty-independent cost); `STRATEGY` layer only when the strategy over-trades
   (excessive rebalances eating gas — that's signal-quality, not fill-quality).

**Banned patterns**:

- Hardcoded gas-cost constants in archetype configs (`gas_cost_usd_per_tx = 5`) — must read per-block from `gas_fees`.
- Pre-trade simulations that ignore gas — over-estimates fill P&L for any DeFi leg.
- Treasury accounting that lumps native gas into "available capital" — gas reserves are non-deployable.

### 7. Factor × layer dual axis — closed sets stay decoupled

Every `PnLAttribution` row is tagged with TWO orthogonal axes:

- **`factor: PnLFactor`** — the **economic driver** (DELTA / FUNDING / BASIS / CARRY / FEES / SLIPPAGE / etc., closed
  set in [§ Canonical Attribution Factors](#canonical-attribution-factors) below). Answers "what moved the price."
- **`layer: PnLLayer`** — the **system layer** that contributed (`STRATEGY` | `EXECUTION`, closed set). Answers "which
  part of the stack is responsible — the signal or the fill."

The two axes do NOT live in the same enum. Mixing them (e.g. `STRATEGY_ALPHA` as a sibling of `DELTA` and `FEES` in one
flat enum) double-counts: `STRATEGY_ALPHA + EXECUTION_ALPHA` already sums to total P&L by construction, so adding
`SLIPPAGE`, `FEES`, etc. as siblings double-books them. Keep the two enums independent.

**Layer derivation** (per [`batch-live-architecture.md §5 + §6`](../../../04-architecture/batch-live-architecture.md)):

- `STRATEGY` rows = factor decomposition computed against `BatchExecutionMode.BENCHMARK` matching-engine fills (always
  fill at requested price; zero execution alpha by definition). Captures what the strategy's signal earned assuming
  perfect execution.
- `EXECUTION` rows = factor decomposition of `(live_or_SIMULATED_fill_pnl − BENCHMARK_fill_pnl)`. Captures what the
  execution layer added or lost relative to the idealised fill: realised vs modelled slippage, latency, queue position,
  adverse selection, size impact, partial fills, fee surprises.

**Invariant** (UTL helper enforces; see § Decomposition Invariants below):

```
sum(rows where layer=STRATEGY)             = strategy_alpha_total
sum(rows where layer=EXECUTION)            = execution_alpha_total
sum(rows over both layers, all factors)    = realised_total_pnl
```

`STRATEGY_ALPHA` and `EXECUTION_ALPHA` are **derived sum-by-layer views**, NOT enum members. Aggregators expose them as
computed fields on rollups; storage stays factor × layer.

**Per-factor layer profile** (which layer each factor typically populates):

| Factor                        | Layer profile        | Notes                                                                      |
| ----------------------------- | -------------------- | -------------------------------------------------------------------------- |
| `DELTA`                       | STRATEGY (mostly)    | Position-side; tiny EXECUTION residual when fill price ≠ requested price   |
| `FUNDING`                     | STRATEGY (entirely)  | Position-side; fill-price-independent                                      |
| `BASIS`                       | STRATEGY (entirely)  | Convergence/divergence of holdings; not execution-driven                   |
| `CARRY` + sub-factors         | STRATEGY (entirely)  | Yield/rate accrual on held collateral                                      |
| `GREEKS`                      | STRATEGY (mostly)    | Sensitivity-driven; small EXECUTION residual via fill-price delta on delta |
| `SETTLEMENT`                  | STRATEGY (entirely)  | Contract expiry / event resolution                                         |
| `SLIPPAGE`                    | EXECUTION (entirely) | Definition: fill_price − benchmark_price. Layer = EXECUTION                |
| `FEES`                        | Both                 | STRATEGY = modelled fee schedule; EXECUTION = surprise (rate change, etc.) |
| `REBATE`                      | Both                 | STRATEGY = modelled maker rebate; EXECUTION = surprise                     |
| `LIQUIDATION`                 | EXECUTION (entirely) | Liquidation penalty/bonus is execution outcome                             |
| `REWARD_REALISATION_SLIPPAGE` | EXECUTION (entirely) | Dust-conversion router slippage residual                                   |
| `FX`                          | STRATEGY (entirely)  | Currency conversion at settlement                                          |
| `RESIDUAL`                    | Either               | Unexplained; investigate when > 1%                                         |

## Canonical Attribution Factors

### Factor Hierarchy

```
Total P&L
├── DELTA                          — P&L from directional price movement
├── FUNDING                        — P&L from perpetual funding rate payments
├── BASIS                          — P&L from basis convergence/divergence
├── CARRY                          — P&L from yield / interest rate differential
│   ├── CARRY_BASE                 — exchange_rate appreciation of staked LST (lst-rates parquet)
│   ├── CARRY_AVS_CONTINUOUS       — EigenLayer/Karak/Symbiotic continuous rewards per token (eigenlayer_rewards parquet)
│   └── CARRY_ISSUER_SEASONAL      — LST-issuer episodic distributions (Ether.fi quarterly, Puffer / Ankr / Stader / Karak; lst_seasonal_rewards parquet)
├── REWARD_REALISATION_SLIPPAGE    — slippage from converting reward dust tokens to target denomination
├── GREEKS                         — P&L from options sensitivities (gamma, vega, theta)
├── FEES                           — P&L impact from transaction fees (exchange, gas, protocol)
├── SLIPPAGE                       — P&L impact from execution vs benchmark price
├── SETTLEMENT                     — P&L from contract expiry / sports event settlement
├── LIQUIDATION                    — P&L impact from liquidation events (penalty, bonus)
├── REBATE                         — P&L from maker rebates, referral bonuses
├── FX                             — P&L from currency conversion (non-USD denominated venues)
└── RESIDUAL                       — Unexplained P&L (must be < 1% of total, else investigate)
```

### CARRY decomposition for restaking-eligible LSTs

For restaking-eligible LSTs (weETH, pufETH, ankrETH, ETHx; jitoSOL, mSOL on Solana) the CARRY parent factor is
decomposed into three sub-factors, each tagged via `RewardPnLLayer` from
`unified_api_contracts.internal.architecture_v2.restaking_rewards`:

| Sub-factor                | Source data                    | Cadence    | Reward tokens (per LST)                                                                                                         |
| ------------------------- | ------------------------------ | ---------- | ------------------------------------------------------------------------------------------------------------------------------- |
| **CARRY_BASE**            | `lst-rates` parquet            | Continuous | LST's quote asset (ETH for ETH-side, SOL for Solana-side, USDe for sUSDe)                                                       |
| **CARRY_AVS_CONTINUOUS**  | `eigenlayer_rewards` parquet   | Continuous | EIGEN, KARAK, ARPA, AVS-specific tokens                                                                                         |
| **CARRY_ISSUER_SEASONAL** | `lst_seasonal_rewards` parquet | Episodic   | weETH: ETHFI quarterly seasons; pufETH: PUFFER/CARROT ad-hoc; ankrETH: ANKR monthly; ETHx: SD monthly; jitoSOL: JTO; mSOL: MNDE |

The `LST_REWARD_STREAMS` registry in UAC names every (LST, layer, reward token, distributor) tuple. features-onchain
indexes `Transfer(from=registered_distributor)` events to populate `lst_seasonal_rewards` parquets daily.

`REWARD_REALISATION_SLIPPAGE` is a separate top-level factor that captures the cost of converting reward dust into the
target denomination (ETH / SOL / USDC). Computed by the dust-conversion router (see
[restaking-reward-economics.md](./restaking-reward-economics.md)) by simulating each token's conversion route through
the matching engine on stored Binance / Uniswap / Jupiter tick data, NOT by applying a hardcoded haircut.
realised_amount

- mark_at_receipt_amount = REWARD_REALISATION_SLIPPAGE.

### Factor Definitions

> ⚠️ **Rows marked with bold** (`CARRY_LENDING_SUPPLY`, `CARRY_LENDING_BORROW`, `CARRY_BASE_REBASING`, `GAS`) are
> **proposed sub-factors not yet in the `PnLFactor` enum**. They are documented here to formalize the intent; adding
> them requires a UAC PR per the closed-set process described in the enum docstring. Until the PR lands, code MUST use
> `CARRY` for lending yield and `FEES` for gas (tagged at EXECUTION layer).

| Factor                      | Computation                                                                                                                                                                                                                                                                                                                                          | Sign Convention                                         |
| --------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- |
| DELTA                       | `sum(position_qty × (price_now - price_prev))` per instrument                                                                                                                                                                                                                                                                                        | Positive = profitable direction                         |
| FUNDING                     | `sum(position_qty × funding_rate × funding_interval)` per perp                                                                                                                                                                                                                                                                                       | Positive = received funding                             |
| BASIS                       | `spot_pnl + perp_pnl` for basis trades (captures convergence)                                                                                                                                                                                                                                                                                        | Positive = basis moved in favor                         |
| **CARRY_LENDING_SUPPLY**    | `aToken_balance × (liquidity_index_now / liquidity_index_prev - 1)` per (protocol, asset, block). **NEVER `supply × apy × time_fraction`** — APY is a derived view, not a primary; the on-chain index IS the rate.                                                                                                                                   | Positive = supply yield accreted                        |
| **CARRY_LENDING_BORROW**    | `debt_token_balance × (variable_borrow_index_now / variable_borrow_index_prev - 1)` per (protocol, asset, block). **NEVER `borrow × apy × time_fraction`**. The debt principal grows mechanically with `variable_borrow_index`; consumers track the debt-token balance separately.                                                                   | Negative = borrow cost accrued                          |
| CARRY_BASE                  | **Wrapped non-rebasing LST** (wstETH, weETH, cbETH, jitoSOL, mSOL, jitoSOL): `holding × (exchange_rate_now / exchange_rate_prev - 1)` (oracle price IS the yield — non-rebasing token, balance fixed, price accretes)                                                                                                                                | Positive = exchange-rate accreted                       |
| **CARRY_BASE_REBASING**     | **Rebasing LST** (stETH, ankrETH-rebasing variants, native mSOL distribution): `(balance_now - balance_prev) × token_price` (balance accretes; price stays ~1:1 with native). Distinct factor from `CARRY_BASE` because the data source is balance-delta, NOT price-delta — wiring shape differs at the position-balance-monitor + lst-rates reader. | Positive = balance accreted                             |
| CARRY_AVS_CONTINUOUS        | `sum_per_token(claimed_amount × token_eth_price)` from eigenlayer_rewards                                                                                                                                                                                                                                                                            | Positive = AVS rewards earned                           |
| CARRY_ISSUER_SEASONAL       | `sum_per_distributor(transfer_amount × token_eth_price_at_receipt)` from lst_seasonal_rewards                                                                                                                                                                                                                                                        | Positive = issuer epoch reward received                 |
| REWARD_REALISATION_SLIPPAGE | `realised_amount_target - mark_at_receipt_target` from dust-conversion router                                                                                                                                                                                                                                                                        | Negative when reward token sells below mid              |
| GREEKS                      | `delta_pnl + gamma_pnl + vega_pnl + theta_pnl` for options                                                                                                                                                                                                                                                                                           | Per-greek decomposition                                 |
| FEES                        | `-sum(fee_amount)` for all trades in period                                                                                                                                                                                                                                                                                                          | Always negative (cost)                                  |
| **GAS**                     | `-sum(gas_used × gas_price_per_block × native_token_usd_price_at_tx_block)` per defi chain                                                                                                                                                                                                                                                           | Always negative (cost — every defi tx burns native gas) |
| SLIPPAGE                    | `sum(fill_price - benchmark_price) × quantity × side_sign`                                                                                                                                                                                                                                                                                           | Negative = worse than benchmark                         |
| SETTLEMENT                  | `settlement_value - mark_value` at expiry/event resolution                                                                                                                                                                                                                                                                                           | Positive = favorable settlement                         |
| LIQUIDATION                 | `liquidation_penalty` or `liquidation_bonus`                                                                                                                                                                                                                                                                                                         | Negative for penalized party                            |
| REBATE                      | `sum(rebate_amount)` for maker fills and referral credits                                                                                                                                                                                                                                                                                            | Always positive (income)                                |
| FX                          | `pnl_local × (fx_rate_now - fx_rate_trade)` for non-USD venues                                                                                                                                                                                                                                                                                       | Positive = favorable FX move                            |
| RESIDUAL                    | `total_pnl - sum(all_attributed_factors)`                                                                                                                                                                                                                                                                                                            | Should be near zero                                     |

## Strategy-Specific Factor Profiles

### Per-Archetype Factor Relevance

| Archetype             | DELTA | FUNDING | BASIS | CARRY | GREEKS | FEES | SLIPPAGE | SETTLE | Notes                     |
| --------------------- | ----- | ------- | ----- | ----- | ------ | ---- | -------- | ------ | ------------------------- |
| Delta-One Basis       | Low   | High    | High  | Low   | --     | Med  | Med      | Low    | Funding is primary alpha  |
| DeFi Recursive Basis  | Low   | Med     | High  | High  | --     | High | Med      | --     | Gas fees dominate costs   |
| Statistical Arb       | High  | Low     | --    | --    | --     | High | High     | --     | Slippage is critical      |
| Market Making         | Low   | Low     | --    | --    | --     | Med  | High     | --     | Spread capture + rebates  |
| Momentum              | High  | Low     | --    | --    | --     | Med  | Med      | --     | Delta is the whole play   |
| Mean Reversion        | High  | Low     | --    | --    | --     | Med  | Med      | --     | Delta from mean return    |
| Sports Arbitrage      | --    | --      | --    | --    | --     | High | --       | High   | Settlement is binary      |
| Calendar Spread       | Low   | High    | High  | Low   | Low    | Med  | Med      | Med    | Basis term structure      |
| Volatility Arb        | Low   | --      | --    | --    | High   | Med  | Med      | Med    | Greeks are the whole play |
| Funding Rate Harvest  | Low   | High    | Low   | --    | --     | Low  | Low      | --     | Pure funding collection   |
| Liquidation Sniper    | High  | --      | --    | --    | --     | High | High     | --     | Gas-competitive entry     |
| Cross-Exchange Arb    | Low   | Low     | --    | --    | --     | Med  | High     | --     | Spread capture            |
| Prediction Contrarian | --    | --      | --    | --    | --     | Med  | Med      | High   | Binary settlement         |
| Yield Optimization    | Low   | --      | --    | High  | --     | Med  | Low      | --     | Carry is the whole play   |

`--` = not applicable for this archetype.

## Attribution Computation

### Per-Fill Attribution

Every `CanonicalFill` triggers an attribution update:

```python
# strategy_service/engine/core/pnl_calculator.py (simplified)
def attribute_fill(fill: CanonicalFill, position: Position, config: StrategyConfig) -> PnLAttribution:
    factors = {}

    # DELTA: price movement since last mark
    factors["DELTA"] = position.quantity * (fill.price - position.avg_entry_price)

    # FEES: exchange fee on this fill
    factors["FEES"] = -fill.fee_amount

    # SLIPPAGE: fill vs benchmark
    if fill.benchmark_price:
        side_sign = Decimal("1") if fill.side == "BUY" else Decimal("-1")
        factors["SLIPPAGE"] = (fill.price - fill.benchmark_price) * fill.quantity * side_sign

    # REBATE: if maker fill and venue offers rebate
    if fill.is_maker and fill.rebate_amount:
        factors["REBATE"] = fill.rebate_amount

    return PnLAttribution(
        strategy_id=config.strategy_id,
        client_id=config.client_id,
        instrument_id=fill.instrument_id,
        timestamp=fill.timestamp,
        factors=factors,
        total_pnl=sum(factors.values()),
    )
```

### Periodic Attribution (Funding, Carry)

Some factors accrue over time, not on fills:

```python
# Funding rate attribution (every funding interval, typically 8H)
def attribute_funding(position: Position, funding_rate: Decimal, interval_hours: int) -> PnLAttribution:
    funding_pnl = position.quantity * position.notional * funding_rate
    # Long pays positive funding, short receives
    if position.side == "LONG":
        funding_pnl = -funding_pnl

    return PnLAttribution(
        factors={"FUNDING": funding_pnl},
        total_pnl=funding_pnl,
    )

# Carry attribution — lending yield uses on-chain index growth per §4 Hard Rule.
# BANNED: carry_pnl = collateral * apy * days / 365  ← APY proxy, never use this.
# CORRECT for CARRY_LENDING_SUPPLY:
def attribute_carry_lending(atoken_balance: Decimal, liquidity_index_now: Decimal, liquidity_index_prev: Decimal) -> PnLAttribution:
    carry_pnl = atoken_balance * (liquidity_index_now / liquidity_index_prev - 1)
    return PnLAttribution(
        factors={"CARRY_LENDING_SUPPLY": carry_pnl},
        total_pnl=carry_pnl,
    )
```

### Options Greeks Attribution

For options strategies, P&L is decomposed into greek components:

```
Delta P&L    = delta × underlying_price_change
Gamma P&L    = 0.5 × gamma × underlying_price_change^2
Vega P&L     = vega × implied_vol_change
Theta P&L    = theta × time_decay_days
Rho P&L      = rho × interest_rate_change

Total Greeks P&L = sum(delta_pnl, gamma_pnl, vega_pnl, theta_pnl, rho_pnl)
```

### Settlement Attribution (Sports / Prediction)

Sports and prediction markets settle as binary outcomes:

```python
def attribute_settlement(position: Position, outcome: str, settlement_price: Decimal) -> PnLAttribution:
    # settlement_price: 1.0 if outcome matches bet, 0.0 if not
    settlement_pnl = position.quantity * (settlement_price - position.avg_entry_price)

    return PnLAttribution(
        factors={"SETTLEMENT": settlement_pnl},
        total_pnl=settlement_pnl,
    )
```

## T+1 Attribution Pipeline

### Batch Reconciliation Flow

```
T+1 Batch (runs daily at 02:00):
  1. LOAD: Read all fills for T from execution-service GCS archive
  2. LOAD: Read all funding payments for T from venue APIs (UTEI)
  3. LOAD: Read all settlements for T (expired contracts, sports results)
  4. LOAD: Read opening positions for T from PBMS snapshot
  5. LOAD: Read closing positions for T from PBMS snapshot
  6. COMPUTE: Per-fill attribution (DELTA, FEES, SLIPPAGE, REBATE)
  7. COMPUTE: Periodic attribution (FUNDING, CARRY)
  8. COMPUTE: Settlement attribution (SETTLEMENT, LIQUIDATION)
  9. COMPUTE: FX attribution (for non-USD denominated venues)
  10. COMPUTE: Residual = total_pnl - sum(all_factors)
  11. VALIDATE: |RESIDUAL| < 0.01 × |total_pnl| (1% tolerance)
  12. WRITE: Attribution breakdown to GCS
  13. WRITE: Summary to BigQuery for reporting
```

### Reconciliation Checks

| Check                         | Tolerance | Action if Failed                   |
| ----------------------------- | --------- | ---------------------------------- |
| Residual < 1% of total        | 1%        | WARN — investigate unexplained P&L |
| Residual < 5% of total        | 5%        | CRITICAL — manual reconciliation   |
| Position balance matches PBMS | Exact     | CRITICAL — position break          |
| Fill count matches venue      | Exact     | CRITICAL — missing fills           |
| Funding payments match venue  | 0.01%     | WARN — rounding differences        |

### GCS Attribution Output

```
# Illustrative path — actual bucket resolved via resolve_bucket_name("pnl") (bucket-name SSOT rule).
{resolve_bucket_name("pnl")}/{strategy_id}/{client_id}/{date}/
  ├── attribution_summary.json       # factor totals for the day
  ├── attribution_detail.parquet     # per-fill and per-event attribution
  ├── positions_opening.json         # SOD positions
  ├── positions_closing.json         # EOD positions
  └── reconciliation_report.json     # checks passed/failed
```

## Reporting Dimensions

### Attribution Rollups

P&L attribution can be sliced across multiple dimensions:

```
DIMENSION HIERARCHY:

By Organization:
  org_total
    └── client_1
          ├── strategy_A (instance 1)
          ├── strategy_A (instance 2, different config)
          └── strategy_B
    └── client_2
          └── strategy_A

By Strategy:
  strategy_A_total
    ├── client_1 (config v1)
    └── client_2 (config v2)

By Venue:
  binance_total
    ├── client_1 / strategy_A
    └── client_2 / strategy_A

By Asset Class:
  cefi_total
    ├── all CeFi strategies
  defi_total
    ├── all DeFi strategies
  tradfi_total / sports_total / prediction_total

By Factor:
  funding_total (across all strategies, clients, venues)
  delta_total
  fees_total
  ...
```

### Reporting Periods

| Period    | Computation                   | Storage                                |
| --------- | ----------------------------- | -------------------------------------- |
| Daily     | T+1 batch attribution         | `gs://pnl/{strategy}/{client}/{date}/` |
| Weekly    | Sum of daily attributions     | Computed on-demand from daily data     |
| Monthly   | Sum of daily attributions     | Computed on-demand from daily data     |
| YTD       | Sum of daily attributions     | Computed on-demand from daily data     |
| Inception | Sum of all daily attributions | Computed on-demand from daily data     |

### Key Performance Metrics (Derived from Attribution)

| Metric               | Computation                                            | Granularity           |
| -------------------- | ------------------------------------------------------ | --------------------- |
| Gross P&L            | `sum(all factors)`                                     | Daily, per strategy   |
| Net P&L              | `gross_pnl + FEES + SLIPPAGE`                          | Daily, per strategy   |
| Sharpe Ratio         | `mean(daily_returns) / std(daily_returns) × sqrt(365)` | Rolling 30/90/365 day |
| Max Drawdown         | `max peak-to-trough decline`                           | Since inception       |
| Win Rate             | `count(profitable_days) / count(all_days)`             | Rolling 30 day        |
| Avg Win / Avg Loss   | `mean(positive_days) / abs(mean(negative_days))`       | Rolling 30 day        |
| Cost Ratio           | `abs(FEES + SLIPPAGE) / abs(gross_pnl)`                | Daily, per strategy   |
| Funding Contribution | `FUNDING / gross_pnl`                                  | Per funding strategy  |
| Alpha vs Benchmark   | `strategy_return - benchmark_return`                   | Daily                 |

## Live vs Batch Reconciliation

### Discrepancy Sources

| Source                 | Live P&L Impact    | Batch P&L Impact    | Resolution                  |
| ---------------------- | ------------------ | ------------------- | --------------------------- |
| Delayed fill report    | Missing fill       | Included            | Batch is correct            |
| Venue price correction | Original price     | Corrected price     | Batch is correct            |
| Funding rate revision  | Estimated rate     | Actual settled rate | Batch is correct            |
| Gas price fluctuation  | Estimated gas      | Actual gas used     | Batch is correct            |
| FX rate timing         | Spot rate at fill  | Settlement rate     | Batch is correct            |
| Position break         | Incorrect position | Reconciled position | CRITICAL — investigate root |

### Reconciliation Alert

```
If |live_pnl - batch_pnl| > threshold:
  log_event(PNL_RECONCILIATION_BREAK, {
    strategy_id, client_id, date,
    live_pnl, batch_pnl,
    difference, difference_pct,
    largest_discrepancy_factor
  })
  → alerting-service → Telegram + email
  → manual investigation required
```

Threshold: 1% of gross P&L or $1,000, whichever is larger.

## PnLAttribution Schema

Per Hard Rule #4 (factor × layer dual axis), every attribution row carries BOTH `factor` and `layer`. The schema below
is the row-level shape; `factors: dict[str, Decimal]` is the rollup view (used by the per-fill helpers in this doc and
by reporting aggregators that don't need the layer split).

```python
# unified_api_contracts.internal (simplified)
class PnLLayer(StrEnum):
    STRATEGY  = "STRATEGY"   # benchmark-mode matching-engine fills (always-fill at requested price)
    EXECUTION = "EXECUTION"  # residual: live_or_simulated_fill_pnl − benchmark_fill_pnl

class PnLFactor(StrEnum):
    DELTA                       = "DELTA"
    FUNDING                     = "FUNDING"
    BASIS                       = "BASIS"
    CARRY                       = "CARRY"
    CARRY_BASE                  = "CARRY_BASE"
    CARRY_AVS_CONTINUOUS        = "CARRY_AVS_CONTINUOUS"
    CARRY_ISSUER_SEASONAL       = "CARRY_ISSUER_SEASONAL"
    REWARD_REALISATION_SLIPPAGE = "REWARD_REALISATION_SLIPPAGE"
    GREEKS                      = "GREEKS"
    FEES                        = "FEES"
    SLIPPAGE                    = "SLIPPAGE"
    SETTLEMENT                  = "SETTLEMENT"
    LIQUIDATION                 = "LIQUIDATION"
    REBATE                      = "REBATE"
    FX                          = "FX"
    RESIDUAL                    = "RESIDUAL"
    # ⚠ proposed — pending UAC PR (global_ledger_pnl_attribution_migration Phase 8)
    # These names appear in the Ledger→Attribution mapping table below; they will be
    # formally added to the UAC enum when Phase 8 of global_ledger_pnl_attribution_migration
    # lands. Until then code MUST map them to the nearest existing factor per the table in
    # § "Plan-vs-codex factor name mapping".
    CARRY_FUNDING               = "CARRY_FUNDING"    # perp funding accrual (PassiveLedger FUNDING_ACCRUAL); maps to FUNDING until Phase 8
    CARRY_DIVIDEND              = "CARRY_DIVIDEND"   # cash/stock dividend (PassiveLedger DIVIDEND); maps to CARRY until Phase 8
    REALIZED_PNL                = "REALIZED_PNL"     # terminal cash flow at close/settlement (maps to SETTLEMENT for sports/prediction; DELTA at position close)
    LOSS_LIQUIDATION            = "LOSS_LIQUIDATION" # liquidation penalty/haircut (maps to LIQUIDATION until Phase 8)

@dataclass(frozen=True)
class PnLAttributionRow:
    strategy_id: str
    client_id: str
    instrument_id: str
    archetype_id: str | None           # populated when row belongs to an archetype-tagged trade
    timestamp: datetime
    period: str                        # "fill", "funding_8h", "daily", "settlement"
    factor: PnLFactor                  # economic-driver axis
    layer: PnLLayer                    # system-layer axis
    amount: Decimal                    # signed P&L attributable to (factor, layer) for this row
    metadata: PnLMetadata              # fill_id, venue, benchmark_price, etc.

@dataclass
class PnLAttribution:
    """Aggregated rollup view — sum of PnLAttributionRows over a (strategy, client, period) bucket."""
    strategy_id: str
    client_id: str
    instrument_id: str
    timestamp: datetime
    period: str
    factors: dict[PnLFactor, Decimal]              # factor → sum across both layers
    factors_by_layer: dict[
        tuple[PnLFactor, PnLLayer], Decimal
    ]                                              # (factor, layer) → P&L amount
    total_pnl: Decimal                             # sum of all (factor, layer) cells
    strategy_alpha_total: Decimal                  # derived: sum where layer=STRATEGY
    execution_alpha_total: Decimal                 # derived: sum where layer=EXECUTION
    metadata: PnLMetadata
```

## Decomposition Invariants

The UTL helper `unified_trading_library.pnl_attribution.invariants.assert_decomposition_invariants()` enforces these on
every per-day per-client rollup. Failure raises loud — never silent placeholder.

```
1. sum(rows over both layers, all factors) == realised_total_pnl       (closed-set coverage)
2. sum(rows where layer=STRATEGY) == strategy_alpha_total               (BENCHMARK matching engine sum)
3. sum(rows where layer=EXECUTION) == execution_alpha_total             (live − BENCHMARK residual)
4. RESIDUAL factor magnitude < 1% of |total_pnl|                        (else escalate per § Reconciliation Checks)
5. Every row's factor ∈ PnLFactor closed set; every row's layer ∈ PnLLayer closed set
   (no ad-hoc "OTHER", no wrapper enum members like STRATEGY_ALPHA/EXECUTION_ALPHA)
```

## Plan-vs-codex factor name mapping

The following pre-codex names are NOT canonical. Plans drafting attribution emitters must map them to the canonical
factor + layer per this table. Adding a new factor requires the formal route: PR amends `PnLFactor` enum + extends the
[Factor Definitions](#factor-definitions) table + extends the [per-archetype relevance](#per-archetype-factor-relevance)
matrix.

| Pre-codex name                                                       | Canonical mapping                                                                                                                                                                                                                                                                                                                                                                |
| -------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `STRATEGY_ALPHA`                                                     | Derived view: `sum(layer=STRATEGY)`. Not a factor; not an enum member.                                                                                                                                                                                                                                                                                                           |
| `EXECUTION_ALPHA`                                                    | Derived view: `sum(layer=EXECUTION)`. Not a factor; not an enum member.                                                                                                                                                                                                                                                                                                          |
| `FINANCING`                                                          | `factor=CARRY` with sub-factor metadata (lending/borrow rate accrual). If the borrow side needs its own bucket distinct from yield CARRY, formally add `BORROW_INTEREST` to `PnLFactor` enum (PR + matrix update).                                                                                                                                                               |
| `BORROW`                                                             | Same as `FINANCING` — collapse to `CARRY` (or formal `BORROW_INTEREST` factor add).                                                                                                                                                                                                                                                                                              |
| `REBALANCE`                                                          | NOT a factor. Each rebalance fill decomposes into `DELTA` + `SLIPPAGE` + `FEES` per existing canonical set. `REBALANCE` belongs in `PnLMetadata.fill_reason` (fill metadata), not the attribution axis.                                                                                                                                                                          |
| `HWM_CRYSTALLIZATION`                                                | NOT in `PnLAttributionRow`. Performance-fee crystallization is recognised via a separate `FeeRecognitionRow` table emitted by `wallet_treasury_client_flow_2026_05_10` Phase 5.G's `PerformanceFeeCrystallizedEvent`. `FeeRecognitionRow` joins into the NAV waterfall but does NOT participate in factor × layer decomposition (it's a fee accounting event, not a P&L driver). |
| `STRATEGY_ALPHA + EXECUTION_ALPHA + SLIPPAGE + FEES + ...` flat enum | Hard Rule #4 violation. Two axes (factor, layer) — not one flat union.                                                                                                                                                                                                                                                                                                           |
| `PNL_FACTOR_STAKING_YIELD`                                           | `CARRY_BASE` (wrapped non-rebasing LST) or `CARRY_BASE_REBASING` (rebasing LST). See § Reward P&L Factors for lifecycle.                                                                                                                                                                                                                                                         |
| `PNL_FACTOR_RESTAKING_REWARD`                                        | `CARRY_AVS_CONTINUOUS`. See § Reward P&L Factors for lifecycle.                                                                                                                                                                                                                                                                                                                  |
| `PNL_FACTOR_SEASONAL_REWARD`                                         | `CARRY_ISSUER_SEASONAL`. See § Reward P&L Factors for lifecycle.                                                                                                                                                                                                                                                                                                                 |
| `PNL_FACTOR_REWARD_UNREALISED`                                       | `CARRY_*` unrealised slice (mark-to-market estimate of accrued but unclaimed rewards). See § Reward P&L Factors for lifecycle.                                                                                                                                                                                                                                                   |

## Share Class P&L

P&L is converted from USD to the client's share class base currency. The FX attribution factor tracks the conversion
difference, keeping trading P&L separate from currency exposure.

```
# ETH share class example
pnl_eth = pnl_usd / eth_price_at_settlement

# FX attribution
fx_factor = pnl_usd * (1/eth_price_settlement - 1/eth_price_trade)
trading_factor = pnl_usd / eth_price_trade
total_pnl_eth = trading_factor + fx_factor  # = pnl_usd / eth_price_settlement
```

For `USDT` share class, no FX conversion applies (P&L is already in USD). For `ETH` and `BTC` share classes, every
attribution factor is converted to the base currency at settlement time, and the FX component is separated as its own
factor for transparency.

This ensures clients see P&L in their chosen denomination while the system maintains USD as the internal accounting
currency. The FX factor appears in attribution reports alongside DELTA, FUNDING, CARRY, etc.

### Supported Share Classes

| Share Class | Base Asset | FX Rate Feature (MDPS) | Delta Target             |
| ----------- | ---------- | ---------------------- | ------------------------ |
| `USDT`      | USD / USDT | n/a (rate = 1.0)       | 0 (market neutral)       |
| `ETH`       | ETH        | `fx_rate_eth_usd`      | equity_in_eth (NOT zero) |
| `BTC`       | BTC        | `fx_rate_btc_usd`      | equity_in_btc (NOT zero) |

### FX Rate Source

FX rates (`fx_rate_eth_usd`, `fx_rate_btc_usd`) are produced by `DefiFxRateAdapter` in MDPS. The adapter reads spot tick
data from CeFi venues, aggregates to candle close, and applies LOCF. These features are consumed by strategy-service,
pnl-attribution-service, and risk-and-exposure-service.

### P&L Conversion in Settlement Service

`strategy-service/strategy_service/engine/core/settlement_service.py`
`convert_settlement_to_share_class(pnl, share_class, fx_rates)` converts a USD P&L dict.

For `USDT`: returns all values unchanged with `_share_class` suffixed keys equal to USD values. For `ETH/BTC`: divides
each value by the FX rate (ETH at $3500 → 1 ETH = 1/3500 USD → divide).

Output keys:

- `{factor}_usd` — original USD P&L (unchanged)
- `{factor}_share_class` — same P&L in share class denomination
- `total_pnl_usd`, `total_pnl_share_class`
- `fx_rate_used` — the FX rate applied at settlement

### ETH/BTC Share Class: Delta Target is NOT Zero

For ETH share class, the risk target is NOT zero ETH delta. A portfolio targeting ETH denomination must hold
equity_in_eth worth of ETH exposure. Zero ETH delta would mean underperforming ETH appreciation.

`evaluate_base_currency_drift()` in risk_metrics.py enforces this:

- Target ETH delta = account_equity / fx_rate_eth_usd
- Drift = |actual - target| / target × 100%
- WARNING at >2%, CRITICAL at >5%

When drift exceeds threshold, strategy emits a SWAP instruction to buy ETH back toward target.

Share-class specification: the legacy `_archived_pre_v2/cross-cutting/share-classes.md` reference was superseded
2026-05-12 per slot 8 strategy audit ST-13 — the canonical share-class definitions are now expected to live in the
strategy catalogue 3-tier doc + UAC `ConfigRegistry`. Cross-link: live operator-facing thresholds are in
[`codex/04-architecture/defi-risk-monitoring.md`](../../../04-architecture/defi-risk-monitoring.md). If a downstream
consumer needs the full share-class spec before that section is written into a live SSOT, file a ping in
`_agent_pings.md` so the migration sub-plan picks it up.

## Reward P&L Factors

> **Vocabulary consolidation note (2026-06-01):** The `PNL_FACTOR_*` names below are a **pre-codex parallel naming
> system** that duplicates concepts already covered by the canonical `PnLFactor` enum. The canonical vocabulary is the
> `PnLFactor` enum (`CARRY_BASE`, `CARRY_AVS_CONTINUOUS`, `CARRY_ISSUER_SEASONAL`, `REWARD_REALISATION_SLIPPAGE`). Use
> the canonical names in all code; the `PNL_FACTOR_*` aliases are retained here for backward-reference only. Formal
> migration to the canonical names is tracked in `global_ledger_pnl_attribution_migration` **Phase 8** — that is also
> the trigger for the UAC enum PR that will formally add `CARRY_FUNDING`, `CARRY_DIVIDEND`, `REALIZED_PNL`, and
> `LOSS_LIQUIDATION` to `PnLFactor` (see enum block above).

Four additional attribution factors for DeFi staking reward streams. These extend the canonical factor hierarchy for
strategies that involve liquid staking tokens (weETH, wstETH) and their associated reward protocols.

| Factor (pre-codex `PNL_FACTOR_*` alias) | Canonical `PnLFactor` mapping        | What It Captures                                         | Settlement Type   |
| --------------------------------------- | ------------------------------------ | -------------------------------------------------------- | ----------------- |
| `PNL_FACTOR_STAKING_YIELD`              | `CARRY_BASE` / `CARRY_BASE_REBASING` | Base staking APY contribution (weETH/wstETH rate growth) | `LST_YIELD`       |
| `PNL_FACTOR_RESTAKING_REWARD`           | `CARRY_AVS_CONTINUOUS`               | EIGEN restaking rewards (weekly from EigenLayer)         | `SEASONAL_WEEKLY` |
| `PNL_FACTOR_SEASONAL_REWARD`            | `CARRY_ISSUER_SEASONAL`              | ETHFI quarterly airdrops (from EtherFi protocol)         | `SEASONAL_WEEKLY` |
| `PNL_FACTOR_REWARD_UNREALISED`          | `CARRY_*` (unrealised slice)         | Accrued but unclaimed rewards (mark-to-market estimate)  | `MARK_TO_MARKET`  |

**Lifecycle:**

1. Rewards accrue in the protocol. Tracked as `PNL_FACTOR_REWARD_UNREALISED` (→ canonical: `CARRY_*` unrealised slice,
   estimated from expected distribution schedule).
2. On-chain claim transaction converts unrealized to realized. `PNL_FACTOR_REWARD_UNREALISED` decreases,
   `PNL_FACTOR_RESTAKING_REWARD` (→ `CARRY_AVS_CONTINUOUS`) or `PNL_FACTOR_SEASONAL_REWARD` (→ `CARRY_ISSUER_SEASONAL`)
   increases by the claimed amount.
3. If reward tokens are sold (via `SELL_REWARD` operation), the realized proceeds replace the token-denominated value
   with a USD-denominated value in the factor.

These factors are only active for strategies that use EtherFi or Lido staking. For Lido (`staking_protocol="LIDO"`),
only `PNL_FACTOR_STAKING_YIELD` (→ `CARRY_BASE` or `CARRY_BASE_REBASING`) applies — there are no separate reward tokens.

## SSOT References

| Concept                | SSOT                                | Location                                                  |
| ---------------------- | ----------------------------------- | --------------------------------------------------------- |
| PnL calculator         | PnLCalculator                       | `strategy_service/engine/core/pnl_calculator.py`          |
| Settlement service     | SettlementService                   | `strategy-service/strategy_service/settlement_service.py` |
| PnL attribution schema | UIC                                 | `unified-api-contracts (internal/)/`                      |
| Fill schema            | CanonicalFill (UIC)                 | `unified-api-contracts (internal/)/`                      |
| Funding rate features  | features-service (delta-one family) | `features-service (delta-one family)/`                    |
| Options greeks         | features-options-service            | `features-options-service/`                               |
| Cost factors           | See execution-policy                | `codex/04-architecture/execution-policy.md`               |
| PnL storage            | GCS archives                        | `gs://pnl/{strategy_id}/{client_id}/{date}/`              |
| Reporting UI           | trading-analytics-ui                | `trading-analytics-ui/`                                   |
| BigQuery reporting     | UCI DataSink                        | `unified-cloud-interface/`                                |
| **Global ledger SSOT** | **LedgerRow (UAC)**                 | `unified_api_contracts.canonical.crosscutting.ledger`     |

---

## Global Ledger Integration (2026-05-23)

> **[DELTA 2026-05-23]** UAC Phase 2 — `LedgerRow` shipped at `unified-api-contracts@008e59ce`. This section maps the
> canonical attribution factors above to their SSOT ledger rows. Full architecture:
> `codex/04-architecture/global-ledger-architecture.md`.

### Carry-as-Theta-Family Attribution Framing

Carry income (funding accruals, staking rewards, lending interest) is **structurally analogous to options theta**: it is
a time-based passive income stream that accrues while a position is held, independent of price movement. This framing
unifies CeFi / DeFi / TradFi carry attribution under a single factor taxonomy:

| Carry type              | EventType (PassiveLedger)    | Canonical attribution factor         | Theta analogy                       |
| ----------------------- | ---------------------------- | ------------------------------------ | ----------------------------------- |
| Perp funding received   | `FUNDING_ACCRUAL`            | `CARRY_FUNDING`                      | Long theta on the basis spread      |
| Perp funding paid       | `FUNDING_ACCRUAL` (delta<0)  | `CARRY_FUNDING` (negative)           | Short theta on the basis spread     |
| LST staking reward      | `STAKING_REWARD`             | `CARRY_BASE` / `CARRY_BASE_REBASING` | Theta-equivalent on staked capital  |
| Lending supply interest | `LENDING_INTEREST`           | `CARRY_LENDING_SUPPLY`               | Theta-equivalent on lent capital    |
| Borrow cost             | `LENDING_INTEREST` (delta<0) | `CARRY_LENDING_BORROW`               | Negative theta on borrowed capital  |
| Cash/stock dividend     | `DIVIDEND`                   | `CARRY_DIVIDEND`                     | Theta-equivalent on equity position |
| Settlement cash flow    | `SETTLEMENT`                 | `REALIZED_PNL` (terminal)            | Theta-at-expiry (terminal)          |

The "carry-as-theta" framing means:

- **Carry strategies optimise for positive theta** (time decay in their favour) across the DeFi + CeFi leg split.
- **Attribution decomposition**: delta-PnL (price move) + gamma-PnL (convexity) + theta-PnL (carry / time) + vega-PnL
  (IV change) + residual. Carry strategies aim to maximise theta-PnL while hedging delta.
- **PassiveLedger is the source of truth** for all carry attribution rows. Joining InstructionLedger positions with
  PassiveLedger accrual rows via `parent_event_id` gives the per-position carry attribution timeline.

### Ledger → Attribution Factor Mapping

```
InstructionLedger (EventOrigin.INSTRUCTION)
  ├── TRADE rows           → delta-PnL (price × delta) + REALIZED_PNL at close
  ├── TRANSFER/BRIDGE rows → excluded from P&L (capital movement, not income)
  ├── STAKE/UNSTAKE rows   → excluded from P&L (position transformation)
  ├── BORROW/REPAY rows    → excluded from P&L (balance sheet, not income)
  └── LIQUIDATION rows     → REALIZED_PNL (forced close) + LOSS_LIQUIDATION factor

PassiveLedger (EventOrigin.PASSIVE)
  ├── FUNDING_ACCRUAL      → CARRY_FUNDING
  ├── STAKING_REWARD       → CARRY_BASE or CARRY_BASE_REBASING
  ├── LENDING_INTEREST     → CARRY_LENDING_SUPPLY (positive) / CARRY_LENDING_BORROW (negative)
  ├── DIVIDEND             → CARRY_DIVIDEND
  ├── SETTLEMENT           → REALIZED_PNL (terminal cash flow)
  └── EXPIRY               → REALIZED_PNL = 0 (OTM expiry)

PricingLedger (EventType.MARK_UPDATE, written by MTDS)
  └── MARK_UPDATE rows     → unrealized P&L MTM: PositionLedger ⨝ PricingLedger
```

**Implementation status (last updated 2026-06-01):**

- ~~`unrealized_pnl` in strategy-service always returns 0 — MarkPrice not bridged to PnL engine.~~ **SHIPPED
  2026-05-30** — `_session_pnl_realized` and `_session_pnl_unrealized` are now wired into `BaseArchetypeEngineV2` at
  strategy-service@`8deaf28`. MarkPrice is bridged to the PnL engine.
- `fees` not deducted from realized P&L computation. _(still open)_
- PassiveLedger synthesiser not yet implemented — carry factors computed ad-hoc per archetype. _(still open)_
- Migration to join-from-ledger model tracked in `plans/active/global_ledger_pnl_attribution_discovery_2026_05_21.md`.

## Net-delta / exposure-netting SSOT (F45, 2026-06-15)

Net-delta + exposure-netting is single-canonical in **UTL `unified_trading_library/risk/net_delta.py`** (top-level
re-exported). Five pure-`Decimal` primitives: `net_underlying_delta` (LST collateral → underlying via exchange rate,
minus debt), `residual_hedge_size` (hedge notional that drives net delta to a target; `floor_zero` for short-only),
`net_signed_delta` / `net_signed_exposure` / `gross_exposure` (signed rollups). Both strategy-service
(`position/core/risk_group_aggregator`, `risk/core/exposure_aggregator`) and execution-service
(`defi_execution/helpers/perp_hedge_sizer`, `algo_library/leveraged_leg_controller`) import these — the canonical home
is UTL, not strategy-service, because the no-service↔service-import HARD RULE forbids execution-service importing a
strategy-service pipeline, and UTL is the only shared lib both depend on. **Distinct, deliberately NOT folded in**
(read-both-sides diagnosis): margin-requirement netting (`risk/v2/margin_sim._netting_factor`), the float-domain
output-schema rollup (`engine/core/output_builders._aggregate_exposure_totals` — Decimal routing would shift live
`risk_metrics` parquet precision), options-greeks delta aggregation, and pre-trade limit checks. SSOT:
`plans/active/engine_findings_remediation_2026_06_15.md` (F45).
