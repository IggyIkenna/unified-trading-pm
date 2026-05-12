---
title: Aave V3 IRM slope params fetched from The Graph but DROPPED at normalization — proxy used in lending rate-impact sim
created: 2026-05-12
author: ikenna-defi-sim-realism-tab (slot 6)
source:
  - market-tick-data-service/market_tick_data_service/market_interface/adapters/defi/aave_lending.py:77-79 (fetch)
  - market-tick-data-service/market_tick_data_service/market_interface/adapters/defi/aave_lending.py:549-553 (drop)
  - unified-api-contracts/unified_api_contracts/internal/domain/defi/rate_model.py:47-97 (proxy used today)
  - execution-service/execution_service/matching_engine/lending/rate_impact.py (consumer)
locked_by: live-defi-rollout
locked_since: 2026-05-12
severity: P0
suggested_owner: defi-master / MTDS lending-indices adapter owner
---

## What I found

The Aave V3 lending-indices MTDS adapter at
`market_tick_data_service/market_interface/adapters/defi/aave_lending.py`
**fetches** the per-block IRM slope params from The Graph subgraph (line 77-79):

```graphql
reserveInterestRateStrategy optimalUtilisationRate
variableRateSlope1 variableRateSlope2
baseVariableBorrowRate reserveFactor
```

But the **normalized record DROPS three of them** at line 549-553:

```python
return {
    ...
    "optimal_utilization_rate": None,      # ← fetched but dropped
    "base_variable_borrow_rate": base_variable_borrow_rate,
    "variable_rate_slope1": None,          # ← fetched but dropped
    "variable_rate_slope2": None,          # ← fetched but dropped
}
```

Only `currentLiquidityRate` / `currentVariableBorrowRate` (the resulting rates),
`baseVariableBorrowRate`, and `reserveFactor` survive into the persisted
`lending_indices` parquet schema.

Net state of captured lending_indices data:

| Field | Captured? |
|---|---|
| `currentLiquidityRate` | ✅ per-block |
| `currentVariableBorrowRate` | ✅ per-block |
| `baseVariableBorrowRate` | ✅ per-block |
| `reserveFactor` | ✅ per-block |
| `optimalUtilisationRate` | ❌ fetched but **dropped** |
| `variableRateSlope1` | ❌ fetched but **dropped** |
| `variableRateSlope2` | ❌ fetched but **dropped** |

## Why it matters

The `LendingRateImpactCalculator` (`execution-service@ff6c52ba` Phase 3A of
`defi_simulation_realism_2026_05_10`) computes post-trade `(supply_apy,
borrow_apy)` via the UAC `post_trade_rate()` canonical entry, which dispatches
by `LendingMarketState.protocol_irm_shape` and reads the slopes from the state.

**With the slopes DROPPED, the consumer falls back to**
`unified_api_contracts.internal.domain.defi.rate_model.AAVE_V3_RATE_MODEL_DEFAULTS_BY_ASSET`
— a static snapshot at `rate_model.py:47-97` with the header:

> "Aave V3 governance config on Ethereum mainnet (snapshot — governance can
> change these via vote, captured at the canonical ReserveInterestRateStrategy
> contract per reserve)."

That snapshot is "governance current as of 2026-05-05". Aave governance has
changed the slopes multiple times over the protocol's history (e.g., USDC
`slope2` raised from `0.60` to `0.75` in March 2024 per Aave Improvement
Proposal AIP-352; weETH listed with bespoke slopes in late 2024; e-mode
adjustments per asset).

**Backtest impact**: replaying a 2023 carry-staked-basis archetype trade
through the Phase 3A calculator would apply today's slopes instead of the
slopes active in 2023. For trades on the wing of the kink (utilization 80-95%)
this silently mis-prices post-trade rates by **10-30 bps** of APY. Over a
1-year backtest accumulated across many trades, this compounds to a P&L
attribution drift of ~30-100 bps — large enough to flip a Phase 8 sign-off
verdict on backtest fidelity ("simulated P&L delta vs prod" loses meaning
when both runs share the same proxy bias).

**May-23 critical path implication**: Phase 8C Tenderly-fork
live-vs-simulated reconciliation will mask this drift because Tenderly's
fork holds the current chain-state IRM slopes — so live runs match the
proxy state used by the matcher (no delta observed). The drift is only
visible during historical-replay 8A/8B, where the matcher uses today's
slopes against historical pool reserves. **Phase 8 sign-off cannot certify
backtest fidelity** until this is fixed.

## Recommended decision

**P0 — fix the MTDS lending_indices_handler to persist all 3 dropped fields**:

1. **MTDS**: edit
   `market_tick_data_service/market_interface/adapters/defi/aave_lending.py`
   `_parse_historical_reserve_record()` (line 549-553) to populate
   `optimal_utilization_rate`, `variable_rate_slope1`, `variable_rate_slope2`
   from the same raw reserve record the subgraph already returns. The fetch
   query already requests them (line 77-79); the only fix is to wire them into
   the output dict.
2. **MDPS**: extend the `lending_indices` parquet schema to include the 3 new
   columns. Per CLAUDE.md "Live = batch" + "Honest absence vs fake
   placeholders" — historical rows that were captured before this fix should
   be `record_failed(SCHEMA_VALIDATION_FAILED)` or backfilled with the actual
   per-block slope values from the subgraph. Recommend backfill (the subgraph
   has historical state — re-run the lending-indices VM with the schema-extended
   adapter; ~2 cal AI-days).
3. **UAC**: extend `LendingMarketState` schema NO CHANGE — the model already
   has `optimal_utilization_rate` / `irm_slope1` / `irm_slope2` fields (uac@
   `7f978f5` Phase 1B); the gap is purely on the producer side.
4. **execution-service**: update the `LendingMarketState` builder at the
   consumer call-site (Phase 3B `BenchmarkMatcher` extension or wherever the
   state is materialised from MTDS captures) to populate the per-tick fields
   from the captured parquet instead of the static defaults. The defaults in
   `rate_model.py:AAVE_V3_RATE_MODEL_DEFAULTS_BY_ASSET` stay as a fallback for
   the (asset, block) pairs where backfill is incomplete.
5. **Document the gap** in
   `codex/04-architecture/amm-slippage-simulation.md` § "Lending rate-impact-
   from-own-trade" → "Per-protocol IRM parameter capture" — note that the
   backfill captures need to land before Phase 8C fidelity validation runs.

**Estimate**: ~2 cal AI-days total (~0.5 MTDS edit + ~0.5 schema + 1 backfill VM).

**Sequencing**: must land BEFORE Phase 8A/B carry-archetype + leveraged-funding-arb
1-year replay runs — otherwise the replays use the proxy and the resulting P&L
delta is uninterpretable.

**Suggested owner**: defi-master plan / MTDS lending-indices adapter
maintainer (slot 5 or 8 absorption, or operator-triage routing).

## Composes with

- `defi_simulation_realism_2026_05_10.md` Phase 3A (calculator shipped at
  execution-service@`ff6c52ba` — agnostic of source; this issue is upstream).
- `defi_simulation_realism_2026_05_10.md` Phase 8A/B/C (backtest fidelity
  validation; cannot certify without per-tick slope captures).
- `defi_master_2026_05_07.md` (DeFi capture pipeline ownership).
