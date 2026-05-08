---
title:
  "DeFi protocol governance parameters frozen-at-discovery — Aave / Compound / Morpho rate-model + liquidation
  thresholds + reserve factors not refreshed when governance changes them on-chain"
created: 2026-05-08
author: ikenna
source:
  - instruments-service/instruments_service/reference_data/adapters/defi/aave_v3_adapter.py (one-shot on-chain read at
    discovery)
  - unified-api-contracts/canonical/domain/instruments/__init__.py (Aave A_TOKEN schema with liquidation_threshold +
    optimal_utilization_rate + reserve_factor as captured columns)
  - tests/integration/test_instrument_alignment.py (validates non-null + 0<x<1 but does NOT verify on-chain match)
  - operator directive 2026-05-08:
      "the parameters used for Aave and lending protocols for how they adjust their rates for utilisation in balances,
      is that information which changes over time but slowly? Is that recorded in instrument definitions, or did we just
      hard code it? ... governance decisions do change that logic"
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

# DeFi protocol governance parameters refresh

> **Severity**: P1 — affects strategy correctness when governance proposals land between discovery + execution; doesn't
> strictly block May 23 cutover if governance is stable in the May 8-23 window, but compounds risk for ongoing live
> trading. **Blast radius**: instruments-service (Aave / Compound / Morpho discovery adapters) + UAC (rate-model schema
> fields) + features-onchain-service (uses rate params for APR / utilisation features) + strategy-service (sizing
> decisions depend on liquidation_threshold + reserve_factor) + execution-service (max-borrowable depends on
> borrow_cap). **Suggested owner**: `defi_master_2026_05_07.md` Phase X (new sub-todo).

## What I found

Aave V3 (and similarly Compound V3, Morpho) governs interest-rate-model and risk parameters on-chain. Anyone reading the
contracts at discovery time sees the current values, but governance proposals (Aave Snapshot votes) can change them —
rate-curve kinks adjusted, liquidation thresholds changed, reserve factors increased, supply/borrow caps updated. Each
change is on-chain visible immediately upon vote execution.

### Q1 — On-chain read at discovery: PRESENT

[aave_v3_adapter.py](../../../instruments-service/instruments_service/reference_data/adapters/defi/aave_v3_adapter.py)
calls Aave V3 contracts at discovery time via `get_aave_reserve_data()` (or equivalent) and writes:

- `liquidation_threshold`, `liquidation_bonus`, `ltv` (per reserve)
- `optimal_utilization_rate`, `slope1`, `slope2`, `base_variable_borrow_rate` (interest rate model)
- `reserve_factor`
- `borrow_cap`, `supply_cap`
- `a_token_address`, `variable_debt_token_address`, `stable_debt_token_address`

UAC schema at `canonical/domain/instruments/__init__.py` declares these as captured columns. Tests at
`test_instrument_alignment.py` validate non-null + 0 < liquidation_threshold < 1 at write time.

### Q2 — Refresh path: GAP — frozen at discovery

**No refresh path documented.** No on-chain event listener for Aave's `ReserveInitialized` /
`CollateralConfigurationChanged` / `BorrowableInIsolationChanged` / `ReserveInterestRateStrategyChanged` events. No
scheduled re-read of reserve config. No update hook.

Parameters are **frozen at the timestamp of discovery** (first adapter run, or last manual refresh). If Aave governance
executes a proposal at T+5 days that changes (say) WETH's liquidation_threshold from 0.825 to 0.80:

- On-chain: change is live immediately.
- Our instruments-service catalog: still reads 0.825.
- Strategy-service: sizes positions using the stale 0.825 — over-leveraged for the new 0.80 threshold.
- features-onchain-service: APR computation uses stale rate-curve params; reported APR diverges from actual.
- Smoke test signal: only catches when a strategy gets liquidated unexpectedly OR when manual audit notices the drift.

### Q3 — Same problem applies to Compound v3 + Morpho + others

Compound v3 (Comet) IRM params are governance-controlled; Morpho market params are governance/curator-controlled. Same
shape of issue: on-chain values change via governance, our cache doesn't refresh.

### Q4 — Test gap

[test_instrument_alignment.py] validates that captured `liquidation_threshold` is non-null + in (0, 1). Does NOT
validate that the captured value matches the current on-chain value. Drift is undetectable at QG time.

## Why it matters

- **Strategy sizing wrong post-governance-vote**: any leveraged strategy (the master plan's `leveraged_funding_arb`
  archetype is one) sizes against `liquidation_threshold * collateral_value`. Stale threshold → over-leveraged,
  premature liquidation.
- **APR / yield features drift**: features-onchain-service computes APR from
  `(utilisation, slope1, slope2, kink, base_rate)`. If Aave votes to bend the rate curve, our APR is wrong until next
  discovery run.
- **`Live = batch` violation**: live mode would naturally refresh on every block; batch's frozen-at-discovery diverges.
- **Compound effect with liquidity baseline + tick staleness**: if all three are missing (this issue +
  `mdps_liquidity_baseline_and_live_tick_staleness_2026_05_08.md` +
  `mtds_live_data_recovery_self_detect_2026_05_08.md`), strategies trade on stale prices AND stale governance params AND
  stale fills — multiplicative correctness loss.
- **Audit / compliance**: a regulated environment expects "what governance value was active at trade time T?" Without
  timestamped governance-change-history, post-trade audit can't reconstruct decision context.

## Recommended decision

### Phase 1 — Per-protocol governance event listener

For each governed protocol (Aave V3, Compound V3, Morpho, possibly Pendle / Curve gauges):

- Identify the governance events emitted on parameter change. For Aave V3 PoolConfigurator:
  `CollateralConfigurationChanged`, `ReserveInterestRateStrategyChanged`, `ReserveBorrowing`,
  `BorrowableInIsolationChanged`, `LiquidationProtocolFeeChanged`, `EModeCategoryAdded`, etc.
- Subscribe via WS RPC or batch poll-via-getLogs on a regular cadence (every 5min default).
- On event: re-read the affected reserve's config; update instruments-service catalog; emit `GOVERNANCE_PARAMS_CHANGED`
  event with `{protocol, reserve, changed_fields, old_values, new_values, block_number, tx_hash}`.

### Phase 2 — Time-versioned governance params in catalog

Instead of overwriting `liquidation_threshold` in place when governance changes, store as time-series:

```
gs://{pid}-instruments/governance_params/aave_v3/by_reserve/reserve={WETH}/asof={YYYY-MM-DD}/params.parquet
```

Each row: `(asof_block, asof_timestamp, liquidation_threshold, ltv, ..., changed_by_tx)`. Strategies reading at backtest
time T look up the row with `max(asof_timestamp <= T)` — correct historical params for reproducible backtests.

This is similar shape to the prediction-market `MarketLifecycle` pattern (gold standard) — explicit time-versioning of
slow-changing config.

### Phase 3 — Strategy + features consume time-versioned params

- features-onchain-service APR calculator reads `governance_params.parquet` for the relevant
  `asof <= compute_timestamp`.
- strategy-service sizing reads current params (live mode) or historical-asof params (batch mode).
- Add `LookaheadBiasError` check: features compute at T using params with `asof_timestamp > T - horizon` raises.

### Phase 4 — Governance-change alerting

- `GOVERNANCE_PARAMS_CHANGED` event routed through alerting-service.
- Operator notification when parameters affecting active strategies change. (E.g. carry_staked_basis depends on Aave
  reserve_factor for borrow leg → operator alerted on reserve_factor change.)
- Strategy-service can declare which governance params it depends on; only relevant changes alert.

### Phase 5 — Snapshot governance proposal monitoring (proactive)

Aave + similar protocols announce proposals on Snapshot before execution. Subscribe to relevant Snapshot spaces; alert
operator when a proposal is queued + scheduled for execution that will change params our strategies depend on. Buys time
to react before on-chain execution.

## Acceptance criteria

- [ ] Per-protocol governance event listener shipped (Aave V3, Compound V3, Morpho minimum).
- [ ] Time-versioned `governance_params.parquet` per (protocol, reserve, asof) at canonical path.
- [ ] features-onchain-service migrated off frozen catalog params to time-versioned governance params.
- [ ] strategy-service sizing reads time-versioned params (with backtest-mode asof selection).
- [ ] `GOVERNANCE_PARAMS_CHANGED` event type in UAC; alerting-service routes operator alerts.
- [ ] Smoke test: simulate Aave governance proposal changing a reserve's liquidation_threshold; verify event detected,
      params updated, alert fired, strategies' next sizing uses new value.
- [ ] LookaheadBiasError fires when feature compute uses governance params with asof later than feature timestamp.
- [ ] Backtest reproducibility: re-running a 2-year backtest produces identical results before + after a governance
      change is captured (asof lookup is deterministic).

## Open questions

- For Compound V3 + Morpho: are the governance event signatures stable across protocol upgrades, or do we need
  per-version event handlers?
- Snapshot space monitoring: which spaces? `aavedao.eth`, `comp-vote.eth`, `morpho.eth` are the obvious ones — need full
  list.
- Refresh cadence for non-EVM protocols (Solana programs, Hyperliquid governance): different event model. Phase 1
  EVM-only initially; non-EVM in Phase 1.5.
- Storage cost: time-versioned params written per change → ~10s of rows per reserve per year for stable protocols.
  Cheap. But stress test: pathological cases like emergency governance hot-fixes that revert + re-apply could spike row
  count.
- Coordination with `hard_schema_enforcement_at_write_boundary_2026_05_08.md`: hard-required governance fields in the
  new time-versioned schema (asof_block + asof_timestamp + tx_hash MUST be non-null). Folds in.
