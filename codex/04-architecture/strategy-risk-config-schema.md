---
doc_type: codex-ssot
title: Per-Strategy Risk Config Schema
summary:
  Per-strategy risk config schema — the 7-member drawdown-threshold ladder, expected-drawdown model, 5-flag response
  policy, liquidation detectors, and per-strategy idempotent close-all scripts; fail-loud at config load.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service, unified-api-contracts, unified-trading-system-ui]
scope: [engineer, admin]
tags: [strategy, risk, uac, escalation, data-correctness]
related:
  [
    /codex/04-architecture/autonomous-recovery-matrix.md,
    /codex/04-architecture/recovery-defence-in-depth-layers.md,
    /codex/09-strategy/architecture-v2/cross-cutting/risk-gates.md,
  ]
created: 2026-05-25
authoritative_for: [drawdown-thresholds, risk-config, close-all-scripts]
referenced_by:
  [
    /codex/04-architecture/autonomous-recovery-matrix.md,
    /codex/04-architecture/recovery-defence-in-depth-layers.md,
    /codex/09-strategy/architecture-v2/cross-cutting/risk-gates.md,
    plans/active/drawdown_liquidation_policy_and_strategy_risk_config_2026_05_23.md,
  ]
owner:
last_reviewed: 2026-05-23
code_refs:
---

# Per-Strategy Risk Config Schema

> SSOT for the 7-threshold drawdown configuration, expected drawdown model, 5-flag response policy, and per-strategy
> idempotent close-all scripts. Codified 2026-05-23 per
> `plans/active/drawdown_liquidation_policy_and_strategy_risk_config_2026_05_23.md`.

## Principle

Every live strategy MUST declare a closed-set risk configuration at load time. The strategy-service `config_loader.py`
validates all 3 blocks on every strategy load via `_validate_risk_config_blocks()` — fail-loud on missing.

**No default-valued thresholds**: every strategy declares every threshold explicitly. `None` is acceptable (meaning "not
configured — do not trigger"), but it must be an explicit declaration, not an omission.

---

## UAC types

All types live in `unified_api_contracts/canonical/crosscutting/risk/drawdown.py` (shipped 2026-05-23,
unified-api-contracts@ae5771e2).

### DrawdownThresholdKind (StrEnum, 7 members — closed set)

| Kind               | Meaning                                             | Automatic action                         |
| ------------------ | --------------------------------------------------- | ---------------------------------------- |
| `WARNING`          | First sign of unusual drawdown                      | Log + emit WARN AlertCode                |
| `INVESTIGATION`    | Drawdown requires investigation                     | Trigger `DrawdownInvestigationReport`    |
| `HUMAN_ESCALATION` | Drawdown requires human attention now               | SEV1 alert + investigation report        |
| `AUTO_PAUSE`       | Suspend new entries                                 | Layer-0 `pause_strategy.py`              |
| `AUTO_REDUCE`      | Reduce position size to `max_reduce_pct` of current | Layer-0 reduce script                    |
| `AUTO_CLOSE_ALL`   | Close all positions and halt                        | Layer-0 `enter_safe_mode.py` + close-all |
| `LIQUIDATION_RISK` | Margin/HF threshold requiring immediate action      | SEV0 + Layer-0 deleverage                |

### RiskThresholds (Pydantic)

```python
class RiskThresholds(BaseModel):
    pnl_drawdown: dict[DrawdownThresholdKind, Decimal | None]
    # None = "not configured — do not trigger for this kind"
    # UnsetThresholdError raised at construct-time if any kind is missing from the dict
    # Monotonic ladder enforced: WARNING ≤ INVESTIGATION ≤ HUMAN_ESCALATION ≤ AUTO_PAUSE ...
```

All 7 `DrawdownThresholdKind` members MUST be present in `pnl_drawdown`. Missing key → `UnsetThresholdError` at
construct time.

### ExpectedDrawdownModelBasis (StrEnum, 6 members — closed set)

`HISTORICAL_BACKTEST` | `LIVE_VOLATILITY` | `VAR` | `ES` | `MAX_ADVERSE_EXCURSION` | `CUSTOM`

### ExpectedDrawdownModel (Pydantic)

```python
class ExpectedDrawdownModel(BaseModel):
    basis: ExpectedDrawdownModelBasis
    confidence_level: Decimal | None
    lookback_window: timedelta | None
    regime_adjustment: str | None
```

### ResponsePolicy (Pydantic, 5 booleans — ALL required, no defaults)

```python
class ResponsePolicy(BaseModel):
    allow_agent_investigation: bool
    allow_auto_pause: bool
    allow_auto_reduce: bool
    allow_auto_close_all: bool
    require_human_for_resume: bool
```

All 5 MUST be declared. The `strategy-service/strategy_service/config_loader.py` QG gate rejects any strategy yaml that
omits any of the 3 blocks.

---

## Strategy yaml config block format

```yaml
risk_thresholds:
  pnl_drawdown:
    WARNING: "-0.02" # -2% drawdown → warn + investigate
    INVESTIGATION: "-0.05" # -5% → investigation report triggered
    HUMAN_ESCALATION: "-0.08" # -8% → SEV1 + human escalation
    AUTO_PAUSE: "-0.10" # -10% → pause new entries
    AUTO_REDUCE: "-0.12" # -12% → reduce positions
    AUTO_CLOSE_ALL: "-0.15" # -15% → close all
    LIQUIDATION_RISK: null # not applicable for this strategy (explicit null)

expected_drawdown_model:
  basis: HISTORICAL_BACKTEST
  confidence_level: "0.99"
  lookback_window: P180D # ISO 8601 duration
  regime_adjustment: null

response_policy:
  allow_agent_investigation: true
  allow_auto_pause: true
  allow_auto_reduce: true
  allow_auto_close_all: true
  require_human_for_resume: true
```

---

## Drawdown Investigation Report

Pydantic model `DrawdownInvestigationReport` (17 fields) in
`unified_api_contracts/canonical/crosscutting/risk/drawdown.py` (shipped unified-api-contracts@1ccac60).

Auto-triggered when `INVESTIGATION` or higher threshold breaches. Written by
`strategy-service/strategy_service/drawdown_investigation_writer.py` to GCS at:
`gs://<audit-records-bucket>/incidents/{YYYY-MM-DD}/{incident_key}/drawdown_investigation.json`

DART viewer: `unified-trading-system-ui/components/widgets/risk/drawdown-investigation-viewer.tsx` (shipped
ui@9000cad9).

---

## Liquidation detection

### LiquidationEventDetector

Lives in `strategy-service/strategy_service/detectors/liquidation_event_detector.py` (shipped strategy-service@9acf34c).
Subscribes to venue-execution events. Closed-set predicates per venue family (CeFi perp, DeFi lending, DeFi perp).

Emits `LIQUIDATION_EVENT_DETECTED` AlertCode (SEV1 default). Escalates to SEV0 per 7 closed-set overrides: material
liquidation | more-risk-remains | cause-unknown | strategy-still-trading | margin-collateral-uncertain |
cross-account-may-be-affected | internal-state-did-not-predict.

### LiquidationRiskPredetector

Lives in `strategy-service/strategy_service/detectors/liquidation_risk_predetector.py` (shipped
strategy-service@9acf34c). 6 trigger conditions per `disaster_recovery.md` §9.3:

1. `margin_ratio_breach` — closed set per venue
2. `liquidation_distance_below_threshold`
3. `collateral_transfer_fail`
4. `ADL_or_insurance_fund_risk_signal`
5. `venue_API_cannot_confirm_margin_state`
6. `price_gap_exceeds_model_assumptions`

Emits `LIQUIDATION_RISK_IMMINENT` AlertCode with SEV0.

---

## Per-strategy idempotent close-all scripts

Abstract base class `StrategyCloseAllScript` in `strategy-service/strategy_service/close_all/_template.py` (shipped
strategy-service@57f620e).

**Contract invariants:**

- `dry_run(...) → CloseAllPlan` — idempotent, side-effect-free.
- `execute(...) → CloseAllResult` — venue-specific order semantics.
- **MUST NOT** close positions belonging to OTHER strategies — `strategy_id` scope enforced from position metadata.
- Re-running on already-flat strategy returns no-op result.
- Generates post-close `CloseAllReconciliationReport` linked to the parent incident.

Live implementations (shipped strategy-service@57f620e):

- `strategy-service/strategy_service/close_all/carry_staked_basis.py`
- `strategy-service/strategy_service/close_all/arbitrage_price_dispersion.py`

---

## Enforcement

- `strategy-service/strategy_service/config_loader.py` — `_validate_risk_config_blocks()` called from
  `_validate_and_cache()` + `load_config_from_path()` at every strategy load.
- `bash strategy-service/scripts/quality-gates.sh` — QG gate verifies every strategy yaml passes schema.
- Every deploy: `dry_run()` of each close-all script returns expected plan (continuous verification).

---

## Related

- `04-architecture/autonomous-recovery-matrix.md` — per-failure decision tree (HF + margin-ratio triggers)
- `04-architecture/recovery-defence-in-depth-layers.md` — Layer-0 scripts that execute close-all
- `09-strategy/architecture-v2/cross-cutting/risk-gates.md` — broader risk gate context
- `plans/archive/drawdown_liquidation_policy_and_strategy_risk_config_2026_05_23.plan.md` — implementation plan
