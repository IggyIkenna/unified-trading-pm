---
doc_type: issue
title: UAC pyproject coverage.omit blanks the Phase 8.B/8.C error-classification + validation-logic ratchet
summary:
status: resolved
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-api-contracts, unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-17
author: slot-8 (ikenna side)
source: ['unified-api-contracts/pyproject.toml:[tool.coverage.run].omit', unified-trading-pm/scripts/quality_gates/coverage_targets.yaml § validation_logic + error_classification, unified-trading-pm/plans/archive/deployment_and_qg_strategy_implementation_2026_05_13.md § Phase 8.B + 8.C]
locked_by: live-defi-rollout
---

> **🟡 SUBSUMED BY MEGA AUDIT** — findings absorbed by **Phase D cross-cutting QG ratchet plan + Phase D3 (manifest v8
> finish)** per
> [mega_audit_and_plan_beefup_progression_2026_05_20.md](mega_audit_and_plan_beefup_progression_2026_05_20.md) (slot-1
> triage 2026-05-20). UAC `[tool.coverage.run].omit` is canonically a QG-ratchet item (patterns 4+5: validation_logic +
> error_classification surfaces). Do NOT work standalone.

## What I found

`unified-api-contracts/pyproject.toml` has a `[tool.coverage.run].omit` block (citadel-phase-1 transitional) that
excludes the very surfaces the workspace coverage ratchet wants to enforce:

```toml
[tool.coverage.run]
# Transitional: exclude new-path copies until old paths are removed (citadel phase 1)
omit = [
    "unified_api_contracts/normalize_utils/*",
    "unified_api_contracts/normalize_utils/errors/*",
    "unified_api_contracts/canonical/crosscutting/*",
    "unified_api_contracts/canonical/crosscutting/errors/*",
    ...
]
```

Meanwhile `unified-trading-pm/scripts/quality_gates/coverage_targets.yaml` declares:

```yaml
validation_logic:
  target_pct: 100
  glob_patterns:
    - "unified-api-contracts/unified_api_contracts/canonical/**/*.py"
    - "unified-api-contracts/unified_api_contracts/internal/**/*.py"

error_classification:
  target_pct: 95
  glob_patterns:
    - "unified-api-contracts/unified_api_contracts/canonical/crosscutting/errors/**/*.py"
    - "**/classify_venue_error*.py"
```

**Verified 2026-05-17 (slot-8)** — `coverage.xml` in UAC has **0 `<class>` entries** for `canonical/crosscutting/...`
and `canonical/crosscutting/errors/...`. The Phase 8.D ratchet (`check_coverage_targets.py`) silently passes those
surfaces because no matching files exist in coverage data — so `coverage.xml` does not contain them at all and
`_compute_surface_result` returns `None` (surface "not present in this repo").

Net: **Phase 8.B P0 "Validation logic surface" + Phase 8.C P1 "Error classification coverage to 95%" cannot be
enforced** by the Phase 8.D ratchet until the UAC coverage exclude is lifted on these paths.

## Why it matters

- **Phase 8.B/8.C P0 status reads as "green" mechanically (no surface = no failure)** when it should be "RED"
  (canonical/crosscutting/errors/ has 0 tests against the canonical classify() functions — test_error_classification.py
  tests the older venue-namespaced exports like `BinanceError.classify()` in `binance/order_schemas.py`, NOT the
  canonical UAC error files like `defi.py` / `cefi.py` / `infra.py` / `onchain_perps.py`).
- May-23 cutover gate item from `deployment_and_qg_strategy_implementation_2026_05_13` Phase 8 cannot be honestly
  verified.
- Citadel-phase-1 transitional comment in pyproject says "until old paths are removed" — old paths
  (`unified_api_contracts/normalize_utils/`) ARE STILL PRESENT, so the omit is still load-bearing. But the canonical NEW
  paths ALSO get excluded as a side-effect, defeating the citadel goal ("canonical is the source of truth").

## Recommended decision

**Option A** (preferred for May-23 gate): split the omit between old + new path families:

```toml
omit = [
    # Old paths (still in transition; remove from omit after citadel phase 2 deletion)
    "unified_api_contracts/normalize_utils/*",
    "unified_api_contracts/normalize_utils/errors/*",
    # KEEP canonical/crosscutting + canonical/crosscutting/errors IN measurement
    # (no entry here)
    ...rest unchanged...
]
```

Then expect Phase 8.D ratchet to fire RED on `error_classification` (target 95%, actual ~0%) — that's the truthful
signal. Subsequent work is Phase 8.C P1: write tests against UAC canonical classify() functions for
defi/cefi/infra/onchain_perps/sports/tradfi/altdata error namespaces.

**Option B** (defer to citadel phase 2): add `# coverage-excluded-pending-citadel-2` to coverage_targets.yaml
`validation_logic` + `error_classification` so the ratchet declares them NOT-MEASURABLE-YET. Operator-blocking
otherwise.

**Operator decision needed** on A vs B. Slot-8 recommendation: **Option A** — citadel phase 1 moved
canonical/crosscutting INTO the canonical home; it's the new SSOT; measure it.

## Status

- 2026-05-17 (slot-8): finding filed. AWAITING operator pick A vs B.
- Phase 8.B/8.C plan-flip pending decision.

---

## Triage — 2026-05-18

**Status**: OPEN  
**Triaged by**: slot-8 triage sweep  
**Reason**: Phase 8 ratchet gap; pyproject omit-blanks investigation pending
