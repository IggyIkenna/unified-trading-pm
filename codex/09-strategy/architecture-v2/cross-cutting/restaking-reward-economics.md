---
doc_type: codex-ssot
title: Restaking Reward Economics — Cross-Cutting Concern
summary:
  "Three-layer restaking reward decomposition for restaking LSTs (weETH/pufETH/ankrETH/ETHx; jitoSOL/mSOL):
  base(exchange-rate) + AVS-continuous + issuer-seasonal, each its own `CARRY_*` factor keyed by the
  `LST_REWARD_STREAMS` registry; realisation cost is simulated via the dust-conversion router, never a hardcoded
  haircut."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service, features-service, instruments-service, market-tick-data-service]
scope: [engineer, admin]
tags: [defi, features, execution, strategy, pnl-attribution, uac]
related:
  [
    /codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md,
    /codex/09-strategy/architecture-v2/cross-cutting/reward-lifecycle.md,
    ../../../04-architecture/amm-slippage-simulation.md,
    /codex/09-strategy/architecture-v2/cross-cutting/leverage-and-volatility.md,
  ]
created: 2026-05-01
authoritative_for:
  [
    three-layer restaking reward decomposition (base/AVS-continuous/issuer-seasonal) + LST_REWARD_STREAMS registry +
    simulated dust-conversion realisation,
  ]
referenced_by:
  [
    /codex/04-architecture/amm-slippage-simulation.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-recursive-staked.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-staked-basis.md,
    /codex/09-strategy/architecture-v2/archetypes/yield-staking-simple.md,
    /codex/09-strategy/architecture-v2/cross-cutting/leverage-and-volatility.md,
    /codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md,
    /codex/09-strategy/architecture-v2/cross-cutting/rate-impact-model.md,
    /codex/09-strategy/architecture-v2/cross-cutting/reward-lifecycle.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Restaking Reward Economics — Cross-Cutting Concern

For restaking-eligible LSTs (`weETH`, `pufETH`, `ankrETH`, `ETHx` on Ethereum; `jitoSOL`, `mSOL` and equivalents on
Solana) the realised yield comes from **three distinct on-chain-discoverable layers**, each with its own data source,
cadence, and reward-token mix. This doc names the layers, the per-LST stream registry, the dust-conversion mechanic that
realises non-target-denomination rewards via simulated swaps, and the integration points across pnl-attribution-service,
features-service (onchain family), and execution-service algo_library.

## Hard Rules

### 1. Three reward layers — never collapse

```
Total LST yield = base_apy(exchange_rate)                 # layer 1: in lst-rates parquet
                + avs_continuous_apy_per_token            # layer 2: in eigenlayer_rewards parquet
                + issuer_seasonal_apy_per_token           # layer 3: NEW lst_seasonal_rewards parquet
```

The previous `_eigenlayer_aggregate_apy` collapsed all three into one ETH-equivalent number. That:

- masked per-LST attribution differences (weETH gets ETHFI seasonals, pufETH gets PUFFER drops — they shouldn't share);
- masked illiquidity haircuts (ARPA at $1 mid != $1 realised — selling 100k ARPA on Binance crosses 200 bps of
  slippage);
- missed lump-sum issuer-side seasonal rewards entirely (Ether.fi merkle-distributor claims, ~quarterly, not in the
  continuous stream).

Each layer feeds its own PnL attribution sub-factor: `CARRY_BASE`, `CARRY_AVS_CONTINUOUS`, `CARRY_ISSUER_SEASONAL`. See
[pnl-attribution.md](./pnl-attribution.md).

### 2. Realisation cost is simulated, not assumed

When a reward token (EIGEN, ETHFI, ANKR, PUFFER, ARPA, JTO, etc.) is converted to the target denomination (ETH, SOL,
USDC), the cost is computed by **routing the swap through the matching engine on stored tick data** — never by applying
a hardcoded haircut.

```
ConvertDustInstruction(
    input_tokens=[(EIGEN, 100), (ETHFI, 50), (ANKR, 200), ...],
    target_denomination="ETH",
    max_total_slippage_bps=200,
)
↓
LeveragedLegController-style routing through CEX (Binance/Coinbase spot ticks) +
DEX (Uniswap V3 pools) + aggregator (Jupiter for Solana) market data.
↓
DustConversionResult(
    realised_target_amount=X,
    converted=[ConvertedTokenLeg(token, input_amount, target_amount_realised, target_amount_at_mark, ...), ...]
)
↓
realised_amount - at_mark_amount = REWARD_REALISATION_SLIPPAGE PnL factor
```

The same primitive serves: restaking reward realisation, market-making rebate realisation (DYDX → USDC),
liquidity-mining realisation (CRV/BAL/JUP → ETH/SOL), sports/prediction stake-back-token realisation.
**Strategy-agnostic, asset_group-agnostic.**

### 3. Pre-TGE points are tracked but unrealisable

KING / MILES / KARAK / CARROT and EigenPie points are pre-TGE and cannot be sold. pnl-attribution-service emits
`CARRY_ISSUER_SEASONAL` rows with `value_eth=0` and a `points_pending=true` flag. On TGE, those rows reprice.
`RewardTokenEconomics.is_pre_tge_points=true` flags this in the registry.

### 4. Vesting is honoured in realisation choice

Some reward tokens (EIGEN with 4-yr cliff) vest over time. `RewardTokenEconomics.expected_vesting_months` informs the
strategy's choice; the `ConvertDustInstruction.hold_until_vested_tokens` field lets a strategy say "don't convert EIGEN
yet — wait for vest." The router skips those tokens and reports them as `held` rather than `converted`.

## Per-LST reward stream registry

Lives in `unified_api_contracts.internal.architecture_v2.restaking_rewards.LST_REWARD_STREAMS`. Each entry is an
`LSTRewardStream(lst_symbol, issuer, layer, reward_token_symbol, distributor_address, distributor_chain, distributor_kind, cadence, expected_share_pct)`.

### Ethereum-side (v0)

| LST       | Issuer   | Streams                                                                                     |
| --------- | -------- | ------------------------------------------------------------------------------------------- |
| `weETH`   | Ether.fi | CARRY_BASE→ETH, CARRY_AVS_CONTINUOUS→EIGEN, CARRY_ISSUER_SEASONAL→ETHFI (quarterly, Merkle) |
| `pufETH`  | Puffer   | CARRY_BASE→ETH, CARRY_AVS_CONTINUOUS→EIGEN, CARRY_ISSUER_SEASONAL→PUFFER + CARROT (ad-hoc)  |
| `ankrETH` | Ankr     | CARRY_BASE→ETH, CARRY_ISSUER_SEASONAL→ANKR (monthly, direct transfer)                       |
| `ETHx`    | Stader   | CARRY_BASE→ETH, CARRY_AVS_CONTINUOUS→EIGEN, CARRY_ISSUER_SEASONAL→SD (monthly, direct)      |

### Solana-side (v0)

| LST       | Issuer   | Streams                                                                         |
| --------- | -------- | ------------------------------------------------------------------------------- |
| `jitoSOL` | Jito     | CARRY_BASE→SOL, CARRY_ISSUER_SEASONAL→JTO (ad-hoc, Merkle on Solana)            |
| `mSOL`    | Marinade | CARRY_BASE→SOL, CARRY_ISSUER_SEASONAL→MNDE (monthly, direct transfer on Solana) |

Same architecture as ETH-side; conversion path uses Jupiter aggregator quotes + Orca / Raydium / Lifinity tick data via
market-tick-data-service Solana feeds.

## On-chain discovery for layer-3 (issuer seasonal)

features-service (onchain family) indexes `Transfer(from=registered_distributor, to=*)` events for every distributor in
`LST_REWARD_STREAMS`. Output: `gs://lst-seasonal-rewards-{pid}/by_date/day=YYYY-MM-DD/issuer={E}/{C}/rewards.parquet`
with schema:

```
date, block_number, distributor_address, recipient_wallet,
token_symbol, token_address, amount, amount_usd, amount_eth,
issuer_label, lst_symbol, distributor_kind, season_id (where applicable)
```

Distributor kinds:

- `merkle` — Merkle proof claim (Ether.fi seasons, Karak per-season)
- `direct_transfer` — direct ERC20 Transfer (Ankr rebates, Puffer airdrops)
- `claim_function` — `claim()` callable on rewards contract (legacy AVS)
- `exchange_rate` — no separate distribution (layer 1 — sentinel only)

## Integration with strategy archetypes

Every restaking-aware archetype (`CARRY_RECURSIVE_STAKED`, `CARRY_STAKED_BASIS`, `YIELD_STAKING_SIMPLE`, the
`REBASING_YIELD` decision tracer) consumes the per-LST reward stream decomposition rather than the v0 aggregate. The
`carry_quality(net_apy)` function used by the LeveragedLegController to scale `target_leverage` reads **all three
layers**, applies the simulated realisation cost from the dust-conversion router, and produces a per-LST total APY
estimate that strategies can compare honestly.

```python
# strategy-side, per tick:
streams = LST_REWARD_STREAMS["weETH"]
# Layer 1
base_apy = realised_returns(lst_rates_window)["weETH"]
# Layer 2
avs_apy_per_token = sum_eigenlayer_rewards_for("weETH", window)
# Layer 3
seasonal_apy_per_token = sum_lst_seasonal_rewards_for("weETH", window)
# Realisation cost simulation (NOT a haircut)
dust_result = dust_router.preview(
    ConvertDustInstruction(
        input_tokens=[(EIGEN, avs_eigen_amount), (ETHFI, seasonal_ethfi_amount)],
        target_denomination="ETH",
    )
)
# Honest total
total_apy = base_apy + dust_result.realised_target_amount / lst_holding_eth × annualisation
```

## PnL attribution flow

pnl-attribution-service emits one row per (LST_holding, layer, reward_token, accrual_period) tuple:

| timestamp        | strategy_id           | client_id | lst_symbol | layer                 | reward_token | amount_native | amount_target_at_receipt | amount_target_realised | factor                      |
| ---------------- | --------------------- | --------- | ---------- | --------------------- | ------------ | ------------- | ------------------------ | ---------------------- | --------------------------- |
| 2025-06-15 00:00 | DEFI_ETH_STAKED_BASIS | C1        | weETH      | CARRY_BASE            | ETH          | 0.0156        | 0.0156                   | 0.0156                 | CARRY_BASE                  |
| 2025-06-15 04:32 | DEFI_ETH_STAKED_BASIS | C1        | weETH      | CARRY_AVS_CONTINUOUS  | EIGEN        | 12.4          | 0.00489                  | 0.00485                | CARRY_AVS_CONTINUOUS        |
| 2025-06-15 04:32 | DEFI_ETH_STAKED_BASIS | C1        | weETH      | CARRY_AVS_CONTINUOUS  | EIGEN        | —             | —                        | -0.00004               | REWARD_REALISATION_SLIPPAGE |
| 2025-06-30 00:00 | DEFI_ETH_STAKED_BASIS | C1        | weETH      | CARRY_ISSUER_SEASONAL | ETHFI        | 8.7           | 0.00342                  | 0.00338                | CARRY_ISSUER_SEASONAL       |
| 2025-06-30 00:00 | DEFI_ETH_STAKED_BASIS | C1        | weETH      | CARRY_ISSUER_SEASONAL | ETHFI        | —             | —                        | -0.00004               | REWARD_REALISATION_SLIPPAGE |

Layer 1 has zero realisation slippage (no conversion needed — base accretes in target denomination). Layers 2+3 each
spawn one CARRY\_\* row + one REWARD_REALISATION_SLIPPAGE row per realisation.

## Data dependencies (deployment checklist)

For each new restaking-eligible LST or AVS:

1. **UAC**: add `LSTRewardStream` entries to `LST_REWARD_STREAMS` for every (layer, reward_token, distributor) tuple
2. **UAC**: add `RewardTokenEconomics` to `REWARD_TOKEN_ECONOMICS` for the new reward token
3. **instruments-service**: register the reward token's instrument record (token_address, decimals, chain) + DEX pool
   index entries for {reward_token}/USDC and {reward_token}/WETH (or {reward_token}/USDC and {reward_token}/SOL on
   Solana). Without DEX pools registered the dust router falls back to CEX-only routing.
4. **features-service (onchain family)**: add the distributor address to the layer-3 collector's scan set; verify the
   daily `lst_seasonal_rewards` parquet writes correctly
5. **market-tick-data-service**: confirm the reward token's CEX listings have spot-tick coverage in the relevant tick
   feeds (Binance / Coinbase / Bybit / OKX). For Solana tokens, confirm Jupiter aggregator quote endpoint coverage
6. **pnl-attribution-service**: no code change needed — registry is data-driven
7. **execution-service algo_library**: dust router consumes the registry; no per-LST code

## Out of scope (v0)

- Per-AVS reward attribution within `CARRY_AVS_CONTINUOUS` (currently aggregates EigenLayer, future per-AVS split)
- Karak-on-top-of-EigenLayer + Symbiotic-on-top-of-EigenLayer overlay rewards (treated as their own streams when TGEs
  land; pre-TGE is points-only)
- Dynamic vesting curves (linear assumed; cliff-then-linear is parametric in `expected_vesting_months`)
- Cross-LST netting (each LST's reward streams are independent for now)

## Forward-yield simulation (composite stochastic model)

The historical-reward-realisation registries above describe the deterministic accounting of REALISED rewards. For
FORWARD-yield projection (used by `carry_staked_basis` PnL forecast + `risk_simulations_limits_alerting` scenario
coverage), see codex
[`../../04-architecture/amm-slippage-simulation.md`](../../../04-architecture/amm-slippage-simulation.md) § "Staking +
restaking yield-stream simulators":

- **Native staking** stochastic model — per-chain (Ethereum beacon + Solana validator); calibrated against ≥ 6 months
  historical `staking_yields` data_type with attestation-efficiency-binned heteroskedasticity.
- **Restaking AVS** base+log-normal-premium model — per-LRT operator-allocation-weighted convolution of native yield +
  per-AVS premium.
- **LRT protocol-fee** discrete-event model — Ether.fi / Renzo / KelpDAO / Puffer fees historically change quarterly;
  forward fee assumption = most-recent-quarter ± σ_quarterly capped at `[0, max_observed × 1.5]`.
- **Seasonal-points** operator-tuned discount-factor model — historical points-to-token redemption ratios as calibration
  anchors (Ether.fi 60% / Renzo 50% / Puffer 50% per 2024 airdrops; new programs 70% default).
- **Composite simulator** Phase 5E — convolves all 4 layers into forward `ForwardYieldDistribution(mean, p5, p95)`
  consumed by archetype PnL projection.

Implementation lives at `execution-service/execution_service/yield_streams/` (NEW Phase 5A-E per
`defi_simulation_realism_2026_05_10.md`); design ship 2026-05-12 (PM@`ae804766`).

## See also

- [pnl-attribution.md](./pnl-attribution.md) — CARRY decomposition + REWARD_REALISATION_SLIPPAGE factor definitions
- [../../04-architecture/amm-slippage-simulation.md](../../../04-architecture/amm-slippage-simulation.md) —
  forward-yield stochastic models (Phase 5A-E) + composite simulator code skeleton
- `unified_api_contracts.internal.architecture_v2.restaking_rewards` — schema + registries
- `unified_api_contracts.internal.architecture_v2.leveraged_legs` — LeveragedLegController consumes the realised total
  APY for `target_leverage_source="carry_quality"`
- archetype docs that reference the 3-layer model: `carry-recursive-staked.md`, `carry-staked-basis.md`,
  `yield-staking-simple.md`
