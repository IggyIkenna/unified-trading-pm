---
doc_type: codex-ssot
title: "Archetype: `TSMOM_BTC_CTA`"
summary: >-
  `TSMOM_BTC_CTA` archetype — a BTC-level time-series-momentum / trend-following (CTA) leg: a single directional perp
  leg (long-or-short) sized by the mean SIGN of the trailing returns that are PRESENT on the feature vector, scaled by
  an inverse-volatility (vol-target) overlay. No ML model — a fully interpretable rules-directional family member. The
  research engine proved it a true diversifier (positive in both the 2023 +1.4 and the 2026 −29% selloff +2.3; corr to
  BTC buy-and-hold +0.00 / −0.85). BTC-only by design; CeFi perp primary leg + spot secondary expression.
implementation_status: live
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: [rules, trend, momentum, tsmom, cta, btc, perp, cefi, diversifier]
related:
  [
    ../families/rules-directional.md,
    /codex/09-strategy/architecture-v2/archetypes/rules-directional-continuous.md,
    /codex/09-strategy/architecture-v2/archetypes/rules-directional-event-settled.md,
    ../../../04-architecture/artifact-versioning.md,
  ]
created: 2026-08-12
authoritative_for: [TSMOM_BTC_CTA archetype specification]
referenced_by:
  [
    /codex/09-strategy/architecture-v2/category-instrument-coverage.md,
    /codex/09-strategy/architecture-v2/families/rules-directional.md,
  ]
owner:
last_reviewed:
code_refs: [strategy-service/strategy_service/engine/strategies/v2/rules_directional/tsmom_btc_cta.py]
archetype: TSMOM_BTC_CTA
family: RULES_DIRECTIONAL
venue_universe: [BINANCE, OKX, BYBIT, HYPERLIQUID, DERIBIT]
topology_requirements:
  isolation: { execution-service: isolated, strategy-service: isolated }
  co_location: [execution-service, strategy-service]
  latency_budget_ms: 500
  min_sla_tier: premium
---

# Archetype: `TSMOM_BTC_CTA`

> **Family:** [Rules Directional](../families/rules-directional.md) **Settlement model:** Continuous (perp) / spot.
> **Code module (target):** `strategy-service/strategy_service/engine/strategies/v2/rules_directional/tsmom_btc_cta.py`

## What it does

A single BTC directional leg whose signal is the mean SIGN of the trailing returns that are present on the feature
vector, scaled by an inverse-volatility (vol-target) overlay. Unlike the other rules-directional variants (which fire on
explicit if-else feature conditions), this leg is a pure trend follower: it is long when the mean sign of trailing
returns is positive, short when negative, and flat when the mean is zero or no trailing-return features are present.

The research engine proved it a true diversifier — positive in both the 2023 (+1.4) and the 2026 (−29%) selloff (+2.3),
with correlation to BTC buy-and-hold of +0.00 / −0.85. Scope is intentionally BTC-only (the single most-liquid major),
expressed as a CeFi perp primary leg with a spot secondary expression.

## Signal

```
signal = mean(sign(r) for r in trailing_returns_present),  sign(r) in {-1, 0, +1}
```

- If NONE of the 4 trailing-return features are present → return `[]` (honest absence: no fake signal; the engine
  produces null output until features-service writes `btc_trailing_return_{1,3,6,12}m` to the corpus).
- Vol-scaling: `vol_scale = target_vol / max(realized_vol, vol_floor)` (`1.0` if the realized-vol feature is absent);
  `scaled = clamp(signal * vol_scale, -max_leverage, +max_leverage)`.
- If `scaled == 0` → return `[]` (flat).

## Sizing

```
target_units = (target_equity * scaled) / mid_price
direction = LONG if scaled > 0 else SHORT
```

Position is tracked as a single leveraged leg (`leg_id = tsmom_btc_cta`, `LegSizingStrategy.CONVICTION_WEIGHTED`,
`CashSweepPolicy.THRESHOLD`), with `target_net_delta` equal to the signed position leverage.

## Token / position flow

```
On tick:
  1. FEATURE READ: btc_trailing_return_{1m,3m,6m,12m} + btc_realized_vol from features-service
  2. TREND SIGNAL: mean sign of the present trailing returns (honest absence → flat)
  3. VOL SCALE: target_vol / max(realized_vol, vol_floor), clamped to max_leverage
  4. SIZE: target_units = (target_equity * scaled) / mid_price
  5. EMIT: StrategyInstruction.TRADE (LONG or SHORT) to target_venue
```

## Config parameters

| Param                  | Default                   | Meaning                                         |
| ---------------------- | ------------------------- | ----------------------------------------------- |
| `target_vol`           | `0.15`                    | Annualised vol target                           |
| `vol_floor`            | `0.05`                    | Floor on realized_vol to bound leverage         |
| `max_leverage`         | `1.0`                     | Clamp on `\|signal * vol_scale\|`               |
| `ret_1m_feature`       | `btc_trailing_return_1m`  | Feature key for the 1m trailing return          |
| `ret_3m_feature`       | `btc_trailing_return_3m`  | Feature key for the 3m trailing return          |
| `ret_6m_feature`       | `btc_trailing_return_6m`  | Feature key for the 6m trailing return          |
| `ret_12m_feature`      | `btc_trailing_return_12m` | Feature key for the 12m trailing return         |
| `realized_vol_feature` | `btc_realized_vol`        | Feature key for realized vol                    |
| `min_mid_price`        | `0.0001`                  | Skip ticks below this mid                       |
| `venue_routing_target` | (tick venue)              | Override the target venue (else use tick venue) |

## Determinism spine

No `datetime.now` / `uuid` — sizing reads only the tick inputs + the injected `now_utc`; the instruction id is the
deterministic `_next_instruction_id` (keyed on the run-agnostic slot_label).

## Venue patterns

**Coverage matrix:** See
[`../category-instrument-coverage.md § 19. TSMOM_BTC_CTA`](../category-instrument-coverage.md#19-tsmom_btc_cta) for the
authoritative venue table.

- **CeFi perp** (primary): Binance, OKX, Bybit, Hyperliquid, Deribit — long-or-short, inverse-vol sized.
- **CeFi spot** (secondary): Binance, OKX, Bybit, Hyperliquid — long-only when spot-constrained.
- DeFi / TradFi / Sports / Prediction: N/A — BTC-only CeFi archetype by design.

## Deployment profile

Mapped to `co_located_vm` per `ARCHETYPE_TO_DEPLOYMENT_PROFILE` (rules-directional family `Low` categorization),
matching the other rules-directional archetypes. Note: the signal is a **daily-cadence trend leg** (the representative
`slot_label`s below are `1d`), so the co-location benefit here is not the ms-realm inter-leg gap that drives the
multi-leg `Low` families — it follows the family's uniform `co_located_vm` mapping.

## Representative slot_labels

```
# CeFi perp (TSMOM trend leg — long-or-short)
TSMOM_BTC_CTA@binance-btc-perp-1d-tsmom-usdt-prod
TSMOM_BTC_CTA@hyperliquid-btc-perp-1d-tsmom-usdt-prod

# CeFi spot expression
TSMOM_BTC_CTA@binance-btc-usdt-1d-tsmom-usdt-prod
```

## Risk profile

- Single-leg directional trend exposure — drawdowns are a function of BTC trend reversals (whipsaw risk).
- `max_leverage` + `vol_floor` bound leverage; the vol-target overlay scales down exposure when realized vol rises.
- Honest absence: a missing trailing-return feature set produces no signal (flat), never a fabricated position.

## Not in this archetype

- **Explicit rule-conditioned directional** (if-else feature conditions) — `RULES_DIRECTIONAL_CONTINUOUS`
- **Sports / prediction rule-based** — `RULES_DIRECTIONAL_EVENT_SETTLED`
- **ML-predicted directional** — `ML_DIRECTIONAL_CONTINUOUS`
- **Multi-asset / non-BTC trend** — out of scope (BTC-only by design)

## See also

- Family: [rules-directional.md](../families/rules-directional.md)
- Continuous variant: [rules-directional-continuous.md](rules-directional-continuous.md)
- Event-settled variant: [rules-directional-event-settled.md](rules-directional-event-settled.md)
- Coverage: [category-instrument-coverage.md § 19](../category-instrument-coverage.md#19-tsmom_btc_cta)
