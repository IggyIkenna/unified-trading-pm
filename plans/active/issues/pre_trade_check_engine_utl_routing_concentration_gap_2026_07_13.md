---
doc_type: issue
title: pre_trade_check_engine UTL routing — concentration + 6th-check spec gap (Phase 1 todo 3, partial scope)
summary:
  Phase 1 todo 3 ("route the 6 comparison checks through UTL rules") is internally inconsistent (names 5 checks,
  headline says 6) and under-specified for the `concentration` check, which has no already-computed source in
  `pre_trade_check_engine.py`. Shipped the 4 checks with a clean 1:1 UAC RiskRuleTrigger match (position_value,
  leverage, gross_exposure, net_exposure); filed this as a follow-up SPEC todo for the remainder.
status: resolved
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [strategy-service]
scope: [engineer]
created: "2026-07-13"
last_updated: "2026-07-13"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_role: backend_engineer
drift_direction: advance-code
resolved_by: "main ruling via BLK-fa2173d1 (option A) — no code change"
locked_by:
source:
  [
    plans/archive/2026_07/utl_reuse_phase1_strategy_risk_hwm_2026_07_13.md,
    plans/active/utl_uac_reuse_consolidation_remediation_2026_06_10.md,
  ]
related: [plans/archive/2026_07/utl_reuse_phase1_strategy_risk_hwm_2026_07_13.md]
tags: [utl, uac, risk, pre-trade, spec-gap]
depends_on: []
---

# pre_trade_check_engine UTL routing — concentration + 6th-check spec gap

## What I found

`utl_reuse_phase1_strategy_risk_hwm_2026_07_13.md` todo 3 ("Route the 6 comparison checks through UTL rules") is
internally inconsistent and under-specified on two points, discovered while implementing it (slot 10,
`utl_reuse_phase1_strategy_risk_hwm-003`):

1. **Count mismatch.** The todo's headline says "6 comparison checks" but the body names only 5:
   `position_size/leverage/gross/net/concentration`. I could not find a reading of `pre_trade_check_engine.py`'s
   existing checks that produces exactly 6 items with a clean 1:1 UAC `RiskRuleTrigger` match.
2. **`concentration` has no already-computed source.** The todo says to feed "already-computed" values into UTL
   `evaluate_rule`. `pre_trade_check_engine.py` has no percentage-of-NAV computation anywhere today (its
   single-instrument/venue checks are USD-absolute, and the todo explicitly keeps those **local**, not migrated).
   `MaxConcentrationTrigger` reads `current_concentration_pct` ("position size as % of portfolio NAV") — computing that
   would be NEW logic (e.g. `new_instrument_exposure / account_equity_proxy(...)`), not a wire-through of an existing
   value, and account-equity-as-NAV-proxy is itself a design choice not specified by the plan.

Separately (escalated via `/blocked` BLK-9db4a748, answered by main): routing threshold **numbers** from the static
per-axis UAC registry (`unified_api_contracts.risk.iter_applicable_rules`, the pattern `risk_preflight_gate.py` already
uses) would silently change pre-trade enforcement — registry caps for e.g. `binance` (`MAX_POSITION_SIZE_PER_VENUE` =
$20,000,000) do not match `RiskLimits` config defaults (e.g. `max_position_size` = 100 raw units in the Phase 0 golden
fixture), and unregistered clients/venues would silently lose the check entirely (no fallback rule). Main's ruling:
build ad-hoc UAC-typed `RiskRule` objects per-call, sourcing cap values from the existing `RiskLimits` object — unifies
the comparison dispatch (same `evaluate_rule` path as `risk_preflight_gate.py`) while preserving the Phase 0
golden-fixture numeric output. **Shipped** for the 4 checks with a clean 1:1 trigger match: `position_value`
(`MaxPositionSizeTrigger`), `leverage` (`MaxLeverageTrigger`), `gross_exposure` (`MaxGrossExposureTrigger`),
`net_exposure` (`MaxNetExposureTrigger`) — `strategy-service@<shipped-sha>`.

**Not migrated, kept local by design** (no matching UAC `RiskRuleTrigger`):

- raw-quantity `position_size` check (units, not USD — `MaxPositionSizeTrigger` is USD-only)
- `margin_ratio` check (no `MinMarginRatio` trigger exists in UTL's closed trigger union)
- `concentration` (no already-computed % source; see above)

## Why it matters

This is the CRITICAL last-line-of-defense pre-trade gate. Guessing at the "6th check" or inventing a new
NAV/concentration computation without a reviewed spec risks either a silent production risk-gate behaviour change or an
under-tested new formula shipping on a P0 path. The Phase 1 plan's own acceptance gate ("Golden risk-eval identical")
only protects the checks I actually touched — it does not validate a not-yet-written concentration computation.

## Recommended decision

Spec (before any code): does "concentration" mean (a) a new `new_instrument_exposure / account_equity_proxy(...)`
computation added to `pre_trade_check_engine.py` and routed through `MaxConcentrationTrigger`, replacing nothing
(additive check), or (b) something else the plan author intended but didn't write down? And what is the actual 6th check
— is `position_size` (raw units) meant to route through `MaxPositionSizeTrigger` too (unit-mismatch with its USD-only
`cap_usd` field notwithstanding), or was the "6" simply a miscount at plan-authoring time (5 is correct)?

## Resolution (2026-07-13, slot-5)

Escalated via `/blocked` BLK-fa2173d1; main ruled **option A**: the plan's "6" was a plan-authoring miscount — 5 is
correct. Closed as resolved-no-new-code: `concentration` and raw-quantity `position_size` stay **local by design**,
since neither has a matching UAC `RiskRuleTrigger` / an already-computed percentage source, consistent with the earlier
ruling on this same plan (BLK-9db4a748/BLK-66b39605) to only route the checks that cleanly match rather than inventing
new mappings. Option B (a new additive `concentration` check) and option C (forcing the units-vs-USD mismatch into
`MaxPositionSizeTrigger`) are both real design decisions that deserve their own reviewed spec — not a quiet resolution
inside this migration task. No code change. `utl_reuse_phase1_strategy_risk_hwm` todo 3 already reflects this as its
final scope (`strategy-service@1cc449d3`, 4 checks shipped).

## Todos

- [x] ✅ [SPEC] P2. Resolve the "6 vs 5 checks" count + the `concentration` computation source for
      `pre_trade_check_engine.py` UTL routing; if concentration is confirmed in-scope, add it as a new todo with the
      NAV/equity-proxy formula spelled out. (repo: strategy-service, plan: utl_reuse_phase1_strategy_risk_hwm) —
      RESOLVED: option A (5 is correct, no new code) per main's BLK-fa2173d1 ruling. See Resolution section above.
