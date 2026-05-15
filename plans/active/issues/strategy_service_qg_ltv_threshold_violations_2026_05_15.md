---
title: strategy-service QG STEP 5.37 — 3 inline LTV/HF threshold violations
created: 2026-05-15
author: slot-5-claude
source:
  - strategy-service QG run 2026-05-15 during Phase 4.5 roll_emitter commit
locked_by: live-defi-rollout
---

## What I found

`bash scripts/quality-gates.sh` in strategy-service fails STEP 5.37 (inline HF/LTV/margin thresholds should be in UAC
`LIQUIDATION_PARAMS_REGISTRY`):

```
strategy_service/engine/strategies/v2/mev/backrun.py:
    priority_gas_uplift = decimal_param(self.params, "priority_gas_uplift", Decimal("1.5"))
strategy_service/engine/core/components/math_utilities.py:
    min_health_factor: Decimal = Decimal("1.2"),
strategy_service/engine/core/components/risk_monitor.py:
    liquidation_threshold = None
    liquidation_threshold = self.risk_limits.get("ltv_max", self.default_limits["ltv_max"])
```

13 total violations; max allowed = 0.

These are pre-existing issues — none introduced by Phase 4.5 roll_emitter.py changes.

## Why it matters

STEP 5.37 enforces that risk thresholds are in the UAC registry (`LIQUIDATION_PARAMS_REGISTRY`) not hardcoded inline.
Inline thresholds are a May-23 correctness risk: they can silently diverge from the canonical on-chain values updated in
`UAC@215ed3e` (Aave V3 IRM verification, 2026-05-14).

## Recommended decision

1. `backrun.py` - `priority_gas_uplift` is a MEV gas uplift param, not an LTV threshold. Add `# CORRECT-LOCAL` exemption
   OR move to strategy config dict.
2. `math_utilities.py` - `min_health_factor: Decimal = Decimal("1.2")` is a default function parameter. Move to
   `LIQUIDATION_PARAMS_REGISTRY` or add `# CORRECT-LOCAL` if this is a safe local default.
3. `risk_monitor.py` - `ltv_max` is read from `risk_limits` config at runtime (not hardcoded). The violation might be a
   false positive (the pattern matches `ltv_max` string in the line). Investigate if `# CORRECT-LOCAL` is appropriate.

**Priority**: P2 — not blocking May-23 cutover (pre-existing); but strategy-service QG will remain red until resolved.

Owner: slot responsible for strategy-service risk monitor (likely slot 3 or slot 6 per MEV/risk theme).
