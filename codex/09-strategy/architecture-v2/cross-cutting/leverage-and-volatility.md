---
doc_type: codex-ssot
title: "Cross-cutting: Volatility-derived leverage caps"
summary:
  "Instrument-side leverage cap: `max_safe_leverage = (1 - safety_buffer) / max_move_pct` via
  `derive_max_safe_leverage()` + `INSTRUMENT_VOLATILITY_REGISTRY`; the LeveragedLegController clamps
  `min(venue.max_leverage, instrument.max_safe_leverage)` and emits `LEVERAGE_CAP_TRIPPED`."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service]
scope: [engineer, admin]
tags: [leverage, defi, execution, risk, strategy, uac]
related:
  [
    /codex/09-strategy/architecture-v2/cross-cutting/risk-gates.md,
    /codex/09-strategy/architecture-v2/cross-cutting/restaking-reward-economics.md,
    /codex/09-strategy/architecture-v2/cross-cutting/instrument-type-leverage-matrix.md,
  ]
created: 2026-05-01
authoritative_for:
  [instrument-side volatility-derived leverage cap (derive_max_safe_leverage + INSTRUMENT_VOLATILITY_REGISTRY)]
referenced_by:
  [
    /codex/09-strategy/_archived_pre_v2/cross-cutting/margin-health.md,
    /codex/09-strategy/architecture-v2/cross-cutting/restaking-reward-economics.md,
  ]
owner:
last_reviewed:
code_refs:
ssot: true
---

# Cross-cutting: Volatility-derived leverage caps

> **SSOT:** UAC `unified_api_contracts.internal.instrument_volatility` — `MaxUnderlyingMove`,
> `INSTRUMENT_VOLATILITY_REGISTRY`, `derive_max_safe_leverage()`. Plan:
> `plans/archive/defi_pipeline_extension_2026_05_01.plan.md` Phase 1+2+3.

## Why this exists

The LeveragedLegController (codex `cross-cutting/leg-portfolio-controller.md`) clamps each leg's `target_leverage` to
the venue capability declaration (`venue.max_leverage`). That is half the story. A Hyperliquid LINK perp and a
Hyperliquid AVAX perp both cap at 50x venue-side, but AVAX moves ~2.4× as hard as LINK in stress windows; identical
leverage targets carry asymmetric liquidation risk.

This SSOT defines the **instrument-side** cap. The controller applies
`min(venue.max_leverage, instrument.max_safe_leverage)`.

## Primitive

```python
from unified_api_contracts.internal import (
    MaxUnderlyingMove,
    INSTRUMENT_VOLATILITY_REGISTRY,
    derive_max_safe_leverage,
)

cap = derive_max_safe_leverage("BTC", safety_buffer=Decimal("0.5"))
# cap = (1 - 0.5) / 0.25 = Decimal("2.0")
# (BTC max_move_pct=0.25, default buffer leaves 50% equity headroom)
```

### Formula

```
max_safe_leverage = (1 - safety_buffer) / max_move_pct
```

- `max_move_pct` — 95%-confidence one-sided 30-day adverse move per asset.
- `safety_buffer` — fraction of equity to leave untouched between adverse-move PnL and liquidation. Default `0.5` (50%
  headroom).

A 25% expected adverse move with default buffer leaves leverage at 2x; a 25% drop on a 2x position burns 50% of equity,
exactly the buffer.

### Source provenance

`MaxUnderlyingMove.source` is one of:

- `realised_30d` — empirical 95th-percentile 30-day return computed from the features-cefi/features-onchain
  `vol_realised_30d` feature group.
- `garch_forecast` — GARCH(1,1) one-month-ahead 95% one-sided shock.
- `manual_override` — operator-set value (new tokens, noisy estimates).

The seed table in `unified_api_contracts/internal/instrument_volatility.py` is heuristic; re-seed periodically via the
seed script (UAC scripts/) once the features pipelines are wired up.

## Controller integration

```python
# execution-service/.../leveraged_leg_controller.py
clamped = LeveragedLegController.clamp_to_venue_capabilities(
    state,
    venue_max_leverage={"HYPERLIQUID": Decimal("50")},
    instrument_max_leverage={leg.leg_id: derive_max_safe_leverage("AVAX")
                            for leg in state.legs},
)
```

When `instrument_max_leverage[leg_id]` is missing under a non-None mapping, the controller logs a WARNING
(`no instrument max_leverage for leg ... falling back to venue cap only`) so registry coverage gaps surface in
operations.

## Strategy integration

`ArbitragePriceDispersionHierarchicalEngine` (the cross-venue funding-arb allocator) consumes the registry directly:

```python
coin_leverage = min(
    base_leverage_param,                                # operator ceiling
    derive_max_safe_leverage(coin) * quality_multiplier # vol cap
)
```

`base_leverage` is reinterpreted as a CEILING (not a flat multiplier). Per-coin leverage actually used surfaces in
`AtomicInstruction.attestations["coin_leverage"]` for the decision trace.

Other archetype engines that do their own per-leg sizing (carry, recursive-staked, etc.) follow the same pattern: derive
the per-asset cap from the registry and clamp before submission.

## Events

- `LEVERAGE_CAP_TRIPPED` — emitted by the controller when the requested leverage exceeds the effective cap. Telemetry
  payload includes `venue_cap`, `instrument_cap`, `requested`, `applied`, `binding` (which side bound).
- `LEVERAGE_BREACH` (UAC `AlertType.LEVERAGE_BREACH`) — emitted by risk-and-exposure-service when actual_leverage
  drifts > 10% above target_leverage on a leg. Independent overlay; safety net after the controller's own rebalance has
  had a chance to act.

## Reseed cadence

`MaxUnderlyingMove.derived_at` is the canonical "last computed" timestamp. Anything older than 30 days is stale; the
seed script should re-derive from the latest realised-30d / GARCH features and overwrite the manual seeds. Coins that
dropped out of the candidate universe are pruned.

## When the registry is wrong

1. Coin missing entirely → controller warns + falls back to venue cap.
2. Coin seeded with wrong move → strategy loses money OR leaves alpha on the table. Operator overrides via
   `MANUAL_OVERRIDE` source until the seed script runs again.

Do NOT inline new caps in strategy code; the registry is the single SSOT.
