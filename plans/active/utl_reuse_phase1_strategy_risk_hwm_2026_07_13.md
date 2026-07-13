---
doc_type: plan
title: UTL/UAC reuse consolidation — Phase 1 strategy-service risk/HWM compose (CRITICAL)
summary:
  Compose (not delete) strategy-service's 3 risk-computation engines with UTL's rule-aggregation gate — dedupe the twin
  threshold/equity helper, migrate the legacy portfolio-gate branch to UTL RiskRules, route comparison checks through
  UTL rules.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: [utl, uac, consolidation, refactor, risk, hwm, split]
related:
  [
    plans/active/utl_uac_reuse_consolidation_remediation_2026_06_10.md,
    plans/active/utl_reuse_phase0_guardrails_2026_07_13.md,
  ]
created: "2026-07-13"
last_updated: "2026-07-13"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 1.2
locked_by: live-defi-rollout
locked_since: "2026-07-13"
supersedes:
superseded_by:
depends_on: [utl_reuse_phase0_guardrails_2026_07_13]
gate_on_depends: true
source: [split from utl_uac_reuse_consolidation_remediation_2026_06_10 tracker, operator-approved 2026-07-13]
assigned_role: backend-engineer
drift_direction: advance-code
---

# UTL/UAC reuse consolidation — Phase 1 strategy-service risk/HWM (CRITICAL) — COMPOSE, do not delete

> **Split provenance (2026-07-13):** Phase 1 of
> [`utl_uac_reuse_consolidation_remediation_2026_06_10.md`](utl_uac_reuse_consolidation_remediation_2026_06_10.md)
> (finding #1, CRITICAL). One item already shipped there (`strategy-service@67ecc156`, the `account_equity_proxy()`
> constant-5.0-leverage bug fix) — reproduced below as done. **Machine-held** until
> [`utl_reuse_phase0_guardrails_2026_07_13.md`](utl_reuse_phase0_guardrails_2026_07_13.md) lands its golden risk-eval
> fixture (`depends_on` + `gate_on_depends: true`).

> **Verified reality:** the three "duplicate engines" are the metric-**computation** layer; UTL `risk.rule_evaluator` /
> `risk_preflight` / `family_aggregator` is the **comparison/aggregation** layer (every input arrives pre-computed in
> `RuleEvalContext`). All three local engines are LIVE and feed the UTL gate — they are NOT superseded. UTL HWM
> (`post_trade.hwm_invariants`/`hwm_periods`) is **fee-crystallization HWM**, a different domain from the equity-curve
> drawdown peak — do **not** collapse them.

**Guiding rule (CLAUDE.md conflict-resolution SSOT):** _Align = the MERGED COMBINATION, never "take mine / take
theirs"._ Where two implementations both carry genuine work, keep both; where one is a strict superset, adopt it and
preserve the residual; where the lib lacks a load-bearing local control, extend the lib first, then delete local.

## Todos

- [ ] [AGENT] P0. **Dedupe the twin threshold/equity helper.** `risk/core/risk_calculator.py` and
      `risk/engine/risk_metrics.py` carry near-identical `get_threshold_status` + equity/concentration/peak computation.
      Collapse to ONE shared pure helper (keep the **stateless** `risk_metrics` form for batch=live symmetry); have
      `RiskCalculator.calculate_drawdown` wrap it with its per-`client_id` peak dict. Preserve: per-client peak store,
      UAC `RiskMetrics`/`RiskStatus` assembly, `assert_client_allowed`.
- [ ] [AGENT] P0. **Migrate the one genuine same-layer duplication** —
      `risk/v2/preflight.py:226 _run_legacy_portfolio_gates` (daily-loss / drawdown / family-cap) → UTL `RiskRule`
      registry entries (`MaxDailyLossTrigger`/`MaxDrawdownTrigger` + a family-cap trigger). After migration the legacy
      `PortfolioContext` branch reduces to the **recon-staleness** check only (explicitly NOT a RiskRule — keep local).
- [ ] [AGENT] P0. **Route the 6 comparison checks through UTL rules** where the gate already runs: feed
      `pre_trade_check_engine.py`'s already-computed position_size/leverage/gross/net/concentration into UTL
      `evaluate_rule` so the threshold **numbers** have one SSOT (UAC caps), not `RiskLimits` config + UAC rules
      diverging. Preserve local: notional math (`_compute_notional_for_qty` inverse/linear), staleness, market-hours,
      cash-reserve, VaR (`_normal_quantile`), single-instrument + venue caps, `LimitCheckResult` reject contract.
- [x] ✅ [AGENT] P0. **Fix the local quality bug found in passing** — SHIPPED `strategy-service@67ecc156` | 60 risk
      tests ✓ | basedpyright 0 ✓ | full `quality-gates.sh` exit 0 ✓ | regression:
      `tests/risk/unit/test_pre_trade_check_engine.py::test_leverage_estimate_is_upnl_sensitive_not_constant`.
      `pre_trade_check_engine.py:579` used a hardcoded `equity = new_position_value / Decimal("5")` proxy → made
      leverage a **constant 5.0** for every book, so `leverage > max_leverage` could never fire. Extracted
      `account_equity_proxy()` in `risk_calculator.py` as the equity-formula SSOT (`value/maxlev + uPnL`, floored at 1);
      both `RiskCalculator.estimate_account_equity` and the pre-trade engine now use it; pre-trade bases equity on the
      **post-trade** value (neutral uPnL → `leverage == max_leverage` baseline preserved; negative uPnL → higher
      leverage → can breach). **This also delivers the first slice of the P0 "dedupe twin equity helper" above** (the
      equity-proxy formula is now single-sourced).
- [ ] [AGENT] P1. **Extract one local `equity_curve_drawdown()` helper** for the duplicated peak/max-drawdown loop in
      `engine/core/components/pnl_monitor.py:214-222` and `engine/core/output_builders.py:153-158`. Keep it **local**
      (do NOT route to UTL `hwm_invariants` — wrong domain). Leave fee-crystallization HWM to UTL `post_trade`.
- [ ] [AGENT] P2. Keep `risk/core/correlation_matrix.py` (instrument NxN) as-is — UTL `family_aggregator` only gives
      **family-level pairwise** rhos, a different axis/shape. Optional local cleanup: unify the 3 local correlation
      shapes (instrument-matrix / family-pairwise-dict / v2 nested-dict) — local typing only, not a UTL migration.
- [ ] [VERIFY] P0. Golden risk-eval fixture from Phase 0 reproduces identically; `quality-gates.sh` green; ship via
      quickmerge.

## Success criteria

Golden risk-eval identical; 3 engines compose with UTL gate; the `/5` bug fixed; no `max(equity)` collapsed into UTL
HWM.

## Notes for the worker

- Commit + Push + Flip each shippable unit in the same turn (CLAUDE.md HARD RULE) — one checkbox per `quickmerge`.
- Full severity ledger + verified NON-findings list: see the tracker doc.
