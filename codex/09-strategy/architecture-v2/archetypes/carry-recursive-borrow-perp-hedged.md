# CARRY_RECURSIVE_BORROW_PERP_HEDGED - Family 2 archetype

> **Sibling archetypes:** [carry-recursive-staked.md](./carry-recursive-staked.md) (Family 0) -
> [carry-recursive-borrow-lending-only.md](./carry-recursive-borrow-lending-only.md) (Family 1)

> **Status:** Design-shipped 2026-05-12 (UAC enum + ARCHETYPE_CONFIG_SEED + PerpHedgeSizer schemas). Implementation
> gated on Phase 4 Solidity + Phase 5 orchestrator + Phase 6 Hyperliquid LIVE + Phase 7 PerpHedgeSizer + Phase 8
> monitor + Phase 12 backtest per
> [`plans/active/defi_recursive_borrow_archetypes_2026_05_10.md`](../../../../plans/active/defi_recursive_borrow_archetypes_2026_05_10.md).

## What it does

Family 1 recursive supply-borrow loop PLUS a USDC-margined ETH perp short sized to neutralise the residual spot-ETH
delta carried by the LST collateral leg. Yield = `R_lend + R_fund + R_usdc - gas - slippage` where `R_fund` is perp
funding capture (positive when longs pay shorts). AD-2: USDC-margin perps only (Hyperliquid PRIMARY / Bybit SECONDARY
for May-23 cutover); borrowed ETH stays inside the lending protocol and is NEVER sold to post as perp margin (would
sever the recursion invariant by converting collateralised debt to unhedged cash).

## Token flow + closed-form delta math

For a Family 1 cell `(chain, lender, LST, ETH_debt, mode)` with own capital `base` ETH at per-loop
`ltv <= liquidation_threshold - 0.05` and recursion depth `d`:

```
Cumulative LST collateral (ETH-eq) = base x (1 - ltv^(d+1)) / (1 - ltv)
Cumulative ETH debt                = base x ltv x (1 - ltv^d) / (1 - ltv)
Net ETH-equivalent spot exposure E_actual = base   (exactly, for all finite (ltv, d))
```

Recursion amplifies the SPREAD (`R_lend`), NOT directional exposure. Implication:
`perp_short_size = max(0, E_actual - target_net_delta)`. PerpHedgeSizer (Phase 7) reads live position via Aave
`getUserAccountData` rather than relying on closed form - LST/ETH peg drift + slippage + oracle-mark gap account for
typical +/- 0.1-0.5% deviation.

## Net APR formula

```
R_lend (Family 1) = S x (1 - ltv^(d+1)) / (1 - ltv) - B x ltv x (1 - ltv^d) / (1 - ltv)
R_fund            = +f x (perp_short_size / base)        (delta=0 => +f)
R_usdc            = u x (usdc_margin_buffer / base)      (HL pays 0; Bybit flex-savings ~0 May-23)
R_net             = R_lend + R_fund + R_usdc - gas - slippage
```

Where `S` = LST staking yield, `B` = ETH borrow rate, `f` = perp funding APR, `u` = USDC supply APY at margin venue.

**Worked example** - wstETH/WETH E-Mode (`ltv=0.93, d=8, S=3.2%, B=2.4%, f=+12% APR normal regime`): `R_lend ~6.0%` +
`R_fund ~+12.0%` + `R_usdc ~0` - gas/slippage drag ~0.6% (Ethereum mainnet; 4-12 rebalances/yr) => **R_net ~17.4%**.
Confidence HIGH on `R_lend`, MED on `R_fund` (regime-variable).

## Per-cell x per-venue grid (target_net_delta = 0)

Top-3 May-23 viable cells per `expected_apr x confidence x counterparty_diversification`:

| Rank | Cell ID                                                                  | Net APR | Confidence                                                                     |
| ---- | ------------------------------------------------------------------------ | ------- | ------------------------------------------------------------------------------ |
| 1    | `aave_v3_ethereum_wsteth_weth_emode__hyperliquid_eth_perp__delta_0`      | 10-25%  | HIGH x MED-HIGH (flagship)                                                     |
| 2    | `morpho_ethereum_wsteth_weth_market_0945__hyperliquid_eth_perp__delta_0` | 12-28%  | MED-HIGH (highest APR; LLTV 0.945)                                             |
| 3    | `aave_v3_ethereum_wsteth_weth_emode__bybit_eth_perp__delta_0`            | 10-25%  | HIGH x MED (Bybit Feb-2025-hack discount; counterparty-diversification anchor) |

Excluded: `morpho_ethereum_susde_usdc_market_086` (stable loop; net USDC exposure ~0 => perp would INTRODUCE delta, not
hedge it).

## Per-cell config schema

`CARRY_RECURSIVE_BORROW_PERP_HEDGED` ARCHETYPE_CONFIG_SEED row
(`unified_api_contracts/internal/architecture_v2/archetype_config.py:197`):

- `collateral_currency: "ETH"`
- `hedge_ratio: 1.0` (perp short matches base)
- `position_cap_usd: 20_000.0`
- `kill_switch_drawdown_pct: 0.045` (looser than Family 1 - perp dampens spot moves; tighter than Family 0 -
  funding-flip tail)
- `kill_switch_position_breach_pct: 0.03`

`PerpLegConfig` (UAC `recursive_loop_orchestrator.py`) fields: `perp_venue` (HYPERLIQUID | BYBIT), `perp_pair`,
`target_net_delta`, `usdc_margin_buffer_min_pct=0.30`.

## USDC margin buffer + top-up automation

`HedgeSizerConfig` from `unified_api_contracts/internal/architecture_v2/perp_hedge_sizer.py`:

- `usdc_margin_buffer_min`: 1.5x initial-margin floor
- `auto_topup_threshold`: 1.5 (top up when `available_margin / initial_margin < 1.5` - ~30% price-move headroom before
  liquidation)
- `rebalance_band_pct`: 0.05 (`|perp_short_size - E_actual| > 5% x E_actual` triggers rebalance)
- Default 10x cross-leverage; recommended USD buffer = `0.30 x S x P_eth_usd` (3x initial margin)

Bridge latencies (verify on testnet smoke):

- Hyperliquid: ~10s once Arbitrum bridge tx confirmed (HL L1 finality <1s).
- Bybit USDC deposit: 1-5min (Ethereum ~3min; Arbitrum/Base ~1min). Prefer Arbitrum route.
- 5-minute HL withdrawal dispute window encoded in kill-switch unwind timing budget.

PerpHedgeSizer polls every 5min; top-up tx only when threshold breached (typical <1x/day; several x/day during fast
moves).

## Bybit counterparty cap policy

Cap Bybit notional at <= 50% of Hyperliquid leg notional for first 30 days post-cutover. Reason: Feb-2025 hack drained
~$1.4B from cold wallet; resolved via market buyback over ~72h. Counterparty trust-premium discount persists. Codified
at strategy-service archetype config + risk-and-exposure-service venue-cap table per plan Phase 5/8.

## Kill-switch surface (additive to Family 1)

Family 2-specific alert codes (Phase 8, additive to Family 1's `DEFI_HEALTH_FACTOR_CRITICAL` /
`DEFI_LIQUIDATION_IMMINENT` / `DEFI_ORACLE_STALE_PAUSE` / `DEFI_RECURSIVE_LOOP_GAS_BUDGET_EXCEEDED`):

- `DEFI_FUNDING_RATE_FLIP` - per-block funding crosses zero against strategy direction => position-pause; 30d-avg
  crosses negative threshold => Phase 7.5 adaptive sizing.
- `DEFI_CROSS_VENUE_DELTA_DRIFT` - `|perp_short_size - E_actual| > 5% x E_actual` => auto-rebalance. Also triggers on
  cbETH/ETH or wstETH/ETH oracle move > 1% intra-day.
- `DEFI_PERP_VENUE_OUTAGE` - HL bridge halt / Bybit rate-limit / trading halt. Decision tree: HF-safe Family 1 leg =>
  maintain perp where possible + route new opens to backup venue; HF-near-threshold Family 1 leg => flash-close Family 1
  first (perp becomes outright short until venue recovers; risk escalated).
- `DEFI_PERP_MARGIN_CALL` - `available_margin < MM x 1.2` => top up from treasury; if treasury insufficient => partial
  unwind Family 1 + perp.

## Funding-regime degradation policy

Phase 7.5 adaptive sizing (NICE-TO-HAVE; may defer past May-23 if Phase 7 baseline ships green). Rolling 7d + 30d
funding-APR mean per `(perp_venue, perp_pair)` - feature owned by features-service (onchain family). Hysteresis 5% APR
to avoid thrashing:

- 30d-avg `< -5% APR`: REDUCE perp short by 50%.
- 30d-avg `< -15% APR`: SET perp short to 0 (cell paused; reverts to Family 1 mechanics).
- 30d-avg `> +30% APR`: maintain or INCREASE perp short toward `target_net_delta - 0.5`.

Long-term ETH-perp post-Apr-2024 median: ~+8-15% APR cross-venue; negative regimes episodic (<5% of trading days).

## Batch=live status

Single-engine-class config-driven dispatch per Phase 3 design. Family 2 reuses `CarryRecursiveStakedEngine` with
`perp_leg_enabled=True` + `staking_yield_enabled=False` branch. `factory.py:63` `_ARCHETYPE_ENGINE_MAP` dispatches the
same engine class for Family 0/1/2 archetype keys; engine internal branches via config flags. Same code path batch +
live (Live=batch workspace contract); execution-service matching engine simulates fills against MTDS historical
funding-rate ticks in batch mode.

## Backtest scenarios

See
[recursive-borrow-backtest-scenarios-2026-05.md](../../../16-strategy-playbooks/defi/recursive-borrow-backtest-scenarios-2026-05.md).
Family 2 applies **all three categories**: Cat A (funding regime — positive/negative funding regimes + funding-sign flip
mid-hold + extreme backwardation), Cat B (liquidation stress — LST/ETH depeg cascades, HF threshold crossing, oracle
staleness), and Cat C (venue/bridge failure — Aave pause, Morpho per-market pause, HL bridge halt, Bybit trading halt,
wstETH/weETH canonical bridge failure). Cat A is Family 2-exclusive (perp leg required); Cat B/C are shared with
Family 1.

Key Cat A scenarios for this archetype:

- `SCN-A1-FUNDING-POSITIVE-REGIME`: validates R_fund contribution to net APR over 30d positive-funding hold
- `SCN-A2-FUNDING-NEGATIVE-REGIME`: validates position-pause + partial perp reduction at 30d-avg < -5% APR threshold
- `SCN-A3-FUNDING-SIGN-FLIP-MID-HOLD`: validates PerpHedgeSizer rebalance fires within 1 block of delta-drift > 5%
- `SCN-A4-EXTREME-BACKWARDATION`: validates funding degradation policy (SET perp to 0, revert to Family 1 mechanics)

## See also

- [carry-recursive-staked.md](./carry-recursive-staked.md) - Family 0 (staked basis carry, hardcoded HL ETH-PERP hedge)
- [carry-recursive-borrow-lending-only.md](./carry-recursive-borrow-lending-only.md) - Family 1 (no perp leg)
- [../../../04-architecture/cefi-perp-leg-bybit.md](../../../04-architecture/cefi-perp-leg-bybit.md) - Bybit perp leg
  topology + Feb-2025-hack risk addendum
- [../../../04-architecture/flash-loan-receiver.md](../../../04-architecture/flash-loan-receiver.md) -
  flash-loan-receiver pattern (Family 1 base)

## Not in this archetype

- Pure lending (no perp leg) => [carry-recursive-borrow-lending-only.md](./carry-recursive-borrow-lending-only.md)
- LST staking yield directly (Family 0 - includes staking yield AND hardcoded HL hedge) =>
  [carry-recursive-staked.md](./carry-recursive-staked.md)
- Hardcoded Hyperliquid hedge - Family 0 bakes in `perp_venue=hyperliquid`; Family 2 supports both HYPERLIQUID and BYBIT
  via `PerpLegConfig.perp_venue` config field
- Stablecoin recursive loops (USDC debt, no ETH delta) - excluded from Family 2 cell catalog (perp would introduce
  delta, not hedge it)
