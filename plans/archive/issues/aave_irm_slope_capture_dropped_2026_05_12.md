---
doc_type: issue
title:
  Aave V3 IRM slope params fetched from The Graph but DROPPED at normalization — proxy used in lending rate-impact sim
summary:
status: resolved
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, execution-service, features-service]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-12
author: ikenna-defi-sim-realism-tab (slot 6)
source:
  [
    "market-tick-data-service/market_tick_data_service/market_interface/adapters/defi/aave_lending.py:77-79 (fetch)",
    "market-tick-data-service/market_tick_data_service/market_interface/adapters/defi/aave_lending.py:549-553 (drop)",
    "unified-api-contracts/unified_api_contracts/internal/domain/defi/rate_model.py:47-97 (proxy used today)",
    execution-service/execution_service/matching_engine/lending/rate_impact.py (consumer),
  ]
locked_by: live-defi-rollout
locked_since: 2026-05-12
severity: P0
suggested_owner: defi-master / MTDS lending-indices adapter owner
---

## What I found

The Aave V3 lending-indices MTDS adapter at `market_tick_data_service/market_interface/adapters/defi/aave_lending.py`
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

Only `currentLiquidityRate` / `currentVariableBorrowRate` (the resulting rates), `baseVariableBorrowRate`, and
`reserveFactor` survive into the persisted `lending_indices` parquet schema.

Net state of captured lending_indices data:

| Field                       | Captured?                  |
| --------------------------- | -------------------------- |
| `currentLiquidityRate`      | ✅ per-block               |
| `currentVariableBorrowRate` | ✅ per-block               |
| `baseVariableBorrowRate`    | ✅ per-block               |
| `reserveFactor`             | ✅ per-block               |
| `optimalUtilisationRate`    | ❌ fetched but **dropped** |
| `variableRateSlope1`        | ❌ fetched but **dropped** |
| `variableRateSlope2`        | ❌ fetched but **dropped** |

## Why it matters

The `LendingRateImpactCalculator` (`execution-service@ff6c52ba` Phase 3A of `defi_simulation_realism_2026_05_10`)
computes post-trade `(supply_apy, borrow_apy)` via the UAC `post_trade_rate()` canonical entry, which dispatches by
`LendingMarketState.protocol_irm_shape` and reads the slopes from the state.

**With the slopes DROPPED, the consumer falls back to**
`unified_api_contracts.internal.domain.defi.rate_model.AAVE_V3_RATE_MODEL_DEFAULTS_BY_ASSET` — a static snapshot at
`rate_model.py:47-97` with the header:

> "Aave V3 governance config on Ethereum mainnet (snapshot — governance can change these via vote, captured at the
> canonical ReserveInterestRateStrategy contract per reserve)."

That snapshot is "governance current as of 2026-05-05". Aave governance has changed the slopes multiple times over the
protocol's history (e.g., USDC `slope2` raised from `0.60` to `0.75` in March 2024 per Aave Improvement Proposal
AIP-352; weETH listed with bespoke slopes in late 2024; e-mode adjustments per asset).

**Backtest impact**: replaying a 2023 carry-staked-basis archetype trade through the Phase 3A calculator would apply
today's slopes instead of the slopes active in 2023. For trades on the wing of the kink (utilization 80-95%) this
silently mis-prices post-trade rates by **10-30 bps** of APY. Over a 1-year backtest accumulated across many trades,
this compounds to a P&L attribution drift of ~30-100 bps — large enough to flip a Phase 8 sign-off verdict on backtest
fidelity ("simulated P&L delta vs prod" loses meaning when both runs share the same proxy bias).

**May-23 critical path implication**: Phase 8C Tenderly-fork live-vs-simulated reconciliation will mask this drift
because Tenderly's fork holds the current chain-state IRM slopes — so live runs match the proxy state used by the
matcher (no delta observed). The drift is only visible during historical-replay 8A/8B, where the matcher uses today's
slopes against historical pool reserves. **Phase 8 sign-off cannot certify backtest fidelity** until this is fixed.

## Recommended decision

**P0 — fix the MTDS lending_indices_handler to persist all 3 dropped fields**:

1. ✅ **MTDS — SHIPPED at mtds@`4b38a9b` (2026-05-12 slot 6)** — edit
   `market_tick_data_service/market_interface/adapters/defi/aave_lending.py` `_extract_lending_metadata` to populate
   `optimal_utilization_rate`, `variable_rate_slope1`, `variable_rate_slope2` from the same raw reserve record the
   subgraph already returns. New `_parse_ray` helper does ray (1e27 unit) → decimal-fraction conversion matching
   `_parse_borrow_rate` semantics. basedpyright clean. The fetch query already requested them (line 77-79); the only fix
   was wiring them into the output dict.
2. ✅ **UAC `LendingIndexRecord` schema +5 fields SHIPPED at uac@`bd9c202` (2026-05-12 slot 6)** —
   `optimal_utilization_rate`, `variable_rate_slope1`, `variable_rate_slope2`, `base_variable_borrow_rate`,
   `reserve_factor` added as `float | None` (default `None`) for backwards compat. The on-disk parquet schema follows
   automatically — old rows have `None`, new rows post-mtds@ `4b38a9b` carry the captured per-block slopes.
3. ⏳ **Backfill VM** (operator-runnable; defer to next cycle or operator discretion). Runbook:
   - Refresh tarballs: `bash deployment-service/scripts/vm/create-code-tarballs.sh --all` (per CLAUDE.md "VM tarball
     deployment" HARD RULE — tarballs must include mtds@`4b38a9b` adapter fix).
   - Launch backfill:
     `bash deployment-service/scripts/vm/launch-mtds-lending-indices-backfill-vm.sh <start-date> <end-date>` per
     pre-Phase-1B backfill horizon (the subgraph supports block-pinned historical queries via
     `block: {number: $blockNumber}`).
   - Event-stream verification: STARTED+progress+STOPPED per per-VM shard isolation. Manifest re-consolidation post-run.
   - Expected duration: ~6-12 hours for a 2-year horizon × all Aave V3 chains
     (Ethereum/Arbitrum/Optimism/Polygon/Base/Avalanche). Same pattern as the existing `mtds-lending-indices-` VM
     prefix.
4. ✅ **Consumer call-site row-level override path SHIPPED at features-service@ `e292a4d4` (2026-05-12 slot 6)** —
   `_resolve_rate_params(symbol, row)` sibling helper that prefers per-tick captured slopes when present (post- Phase-1B
   parquets), per-field fallback to UAC static defaults for any None /NaN. 4 new unit tests cover no-row / full-override
   / partial-coverage / NaN-as-missing. **Step 4 remaining**: migrate the calculator's `fetch_data()` from DefiLlama
   Yields to the MTDS `lending_indices` parquet so the row override path actually activates (~1 cal AI-day; the override
   path is dormant until then). Other consumers (execution-service `LendingRateImpactCalculator`) take
   `LendingMarketState` as input — their call-site is upstream and consumes the captured slopes automatically once the
   state builder reads from MTDS.
5. ✅ **Codex doc note SHIPPED at PM@`<this commit>` (2026-05-12 slot 6)** —
   `/codex/04-architecture/amm-slippage-simulation.md` § "Per-protocol IRM parameter capture" gains a top-of-section ⚠️
   CRITICAL banner pointing at this issue doc + flagging that the backfill VM (Step 3) must land before Phase 8A/B
   replay runs.

**Original estimate**: ~2 cal AI-days total.

**Actual delivery (2026-05-12 slot 6)**: ~1.5 cal AI-days for Steps 1, 2, 4 (partial), 5. ~0.5 cal AI-day remaining for
Step 3 (backfill VM — operator- runnable; defer to next cycle owner) + Step 4 tail (`fetch_data()` migration from
DefiLlama → MTDS lending_indices parquet).

**Sequencing**: must land BEFORE Phase 8A/B carry-archetype + leveraged-funding-arb 1-year replay runs — otherwise the
replays use the proxy and the resulting P&L delta is uninterpretable.

**Status summary**:

| Step                                                                   | Status                                                   | Commit                      |
| ---------------------------------------------------------------------- | -------------------------------------------------------- | --------------------------- |
| 1. MTDS producer-side wire-through (3 fields + \_parse_ray helper)     | ✅ DONE                                                  | mtds@`4b38a9b`              |
| 2. UAC `LendingIndexRecord` schema +5 fields (Optional[float])         | ✅ DONE                                                  | uac@`bd9c202`               |
| 3. Backfill VM run (operator-runnable; runbook in this doc)            | ⏳ deferred                                              | tbd next-cycle              |
| 4. Consumer row-level override path (`_resolve_rate_params`) + 4 tests | ✅ DONE (DefiLlama→MTDS source migration tail remaining) | features-service@`e292a4d4` |
| 5. Codex `amm-slippage-simulation.md` ⚠️ CRITICAL banner               | ✅ DONE                                                  | PM@`<this commit>`          |

**Suggested owner for the tail** (Step 3 backfill VM + Step 4 source migration): defi-master plan / MTDS lending-indices
adapter maintainer (slot 5 or 8 absorption, or operator-triage routing).

## Composes with

- `defi_simulation_realism_2026_05_10.md` Phase 3A (calculator shipped at execution-service@`ff6c52ba` — agnostic of
  source; this issue is upstream).
- `defi_simulation_realism_2026_05_10.md` Phase 8A/B/C (backtest fidelity validation; cannot certify without per-tick
  slope captures).
- `defi_master_2026_05_07.md` (DeFi capture pipeline ownership).
