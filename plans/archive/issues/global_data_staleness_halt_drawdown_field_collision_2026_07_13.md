---
doc_type: issue
title:
  "GLOBAL_DATA_STALENESS_HALT reuses MaxDrawdownTrigger(cap_bps=1) — collides with the real current_drawdown_bps field,
  will kill-switch on any live drawdown once account-state wiring lands"
summary:
  "unified-api-contracts/registry/risk_rules/global_rules.py seeds GLOBAL_DATA_STALENESS_HALT with
  MaxDrawdownTrigger(cap_bps=1) as a proxy for market-data staleness (comment: 'fires when MTDS / MDPS / features-*
  outputs lag freshness contract'), but the trigger reads the SAME RuleEvalContext field (current_drawdown_bps) as the
  legitimate GLOBAL_PORTFOLIO_DRAWDOWN_HALT (cap_bps=2000) and every PER_ACCOUNT MaxDrawdownTrigger. Since
  iter_applicable_rules always yields GLOBAL rules and there is no way to supply real drawdown data for the legitimate
  checks while excluding this one (same field, same required-context-key per execution-service's
  _TRIGGER_REQUIRED_CONTEXT_KEY dispatch), any real drawdown >1bps (i.e. virtually always) will fire a
  triggers_kill_switch=True BLOCK mislabeled as data staleness. Currently LATENT, not an active incident:
  execution-service/engine/orchestrator.py's only call to run_risk_preflight() does not pass account_state, so
  current_drawdown_bps is never populated in the live order path today. But
  strategy-service/position/core/rule_eval_context_builder.py (build_rule_eval_context + PeakNavTracker) exists
  specifically to supply real current_drawdown_bps — the moment that gets wired into execution-service's account_state
  (clearly the intended next step, not hypothetical), every live order past a trivial drawdown halts the whole platform."
status: resolved
nature: notes
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-api-contracts, execution-service, strategy-service]
scope: [engineer, admin]
tags: [risk, kill-switch, uac, correctness, drawdown, data-staleness, live-trading]
related:
  [
    unified_api_contracts/registry/risk_rules/global_rules.py,
    execution-service/execution_service/engine/risk/preflight_gate.py,
    strategy-service/strategy_service/position/core/rule_eval_context_builder.py,
    plans/archive/2026_07/utl_reuse_phase1_strategy_risk_hwm_2026_07_13.md,
  ]
created: 2026-07-13
parent_epic: infrastructure_master
priority: P1
source: utl_reuse_phase1_strategy_risk_hwm_2026_07_13 todo 2 (strategy-service risk/v2 preflight migration), 2026-07-13
assigned_vm: planning
resolved_by: slot-11 (2026-07-13)
locked_by:
execution_scope: orchestrator-agent
assigned_role: backend_engineer
model_tier: sonnet-doable
thinking_tier: medium
drift_direction: advance-code
depends_on: []
---

## What I found

While migrating `strategy-service/risk/v2/preflight.py`'s legacy daily-loss/drawdown gates onto the UAC `RiskRule`
registry (`utl_reuse_phase1_strategy_risk_hwm_2026_07_13` todo 2), a test populating `current_drawdown_bps` with a
normal value (100bps) alongside a real `account_id` unexpectedly REJECTED — not because of the account's own rules, but
because `GLOBAL_DATA_STALENESS_HALT` fired.

`unified_api_contracts/registry/risk_rules/global_rules.py`:

```python
RiskRule(
    rule_id=RiskRuleId.GLOBAL_DATA_STALENESS_HALT,
    scope=RiskRuleScope.GLOBAL,
    applies_to="*",
    trigger=MaxDrawdownTrigger(cap_bps=1),   # <-- reuses the drawdown trigger as a staleness proxy
    consequence=RiskRuleConsequence.BLOCK,
    alerting_severity=AlertSeverity.CRITICAL,
    description="Workspace-wide market-data staleness halt — fires when MTDS / MDPS / features-* "
                "outputs lag freshness contract by > threshold. Triggers GLOBAL kill-switch...",
    triggers_kill_switch=True,
),
```

The module already ships `BinaryEventTrigger` (event_source + `active_events` frozenset context field) for exactly this
shape of boolean infrastructure-health condition — it's used correctly for `ORACLE_OUTAGE_HALT` /
`CROSS_CLOUD_EGRESS_HALT` / `CUSTODY_ENDPOINT_HALT` three rules later in the same file. `GLOBAL_DATA_STALENESS_HALT` is
the one outlier still on `MaxDrawdownTrigger`, and its `cap_bps=1` makes it fire on essentially ANY non-zero drawdown,
not on an actual staleness signal.

`iter_applicable_rules()` (`unified_api_contracts/registry/risk_rules/__init__.py:120`) unconditionally does
`yield from GLOBAL_RULES` for every call regardless of which axes are populated — there is no way to opt out of GLOBAL
rule evaluation. Any caller that populates `current_drawdown_bps` (required for the legitimate
`GLOBAL_PORTFOLIO_DRAWDOWN_HALT` / `MaxDrawdownTrigger` per-account rules to work at all) also makes
`GLOBAL_DATA_STALENESS_HALT` evaluable — same field, same
`_TRIGGER_REQUIRED_CONTEXT_KEY[MaxDrawdownTrigger] = "current_drawdown_bps"` dispatch key
(`execution-service/execution_service/engine/risk/preflight_gate.py:105`).

**Currently latent, not firing in production**: `execution-service/engine/orchestrator.py:213`'s only call to
`run_risk_preflight(instruction, reference_price=...)` never passes `account_state`, so `current_drawdown_bps` is never
populated in the live order path today — `_can_evaluate()` drops any rule needing a field the context doesn't carry, so
`GLOBAL_DATA_STALENESS_HALT` currently never evaluates. But
`strategy-service/position/core/rule_eval_context_builder.py` (`PortfolioRiskState` + `PeakNavTracker` +
`build_rule_eval_context`) exists specifically to compute and supply real `current_drawdown_bps` from authoritative
position-balance state — this is clearly the intended next wiring step (its own module docstring:
"risk-and-exposure-service / execution-service / strategy-service can build their pre-flight context from authoritative
position-balance state"), not a hypothetical future. The moment `account_state` includes `current_drawdown_bps` in the
live `run_risk_preflight()` call, every order past a trivial live drawdown will BLOCK + trigger the GLOBAL kill-switch,
mislabeled "data staleness" in the alert.

## Why it matters

`triggers_kill_switch=True` — a false-positive fire here doesn't just reject one order, it halts the entire platform
(human-operator-restart-required per the rule's own description) under a misleading "data staleness" label, while actual
live trading with a normal drawdown is the true cause. This is a May-23 critical-path risk-gate correctness defect: it
will fire the FIRST TIME the drawdown-state wiring (already built, just not yet threaded to the live call) is connected
— likely to happen soon since it's exactly what the position-balance → risk-gate integration work is for.

## Recommended decision

Replace `GLOBAL_DATA_STALENESS_HALT`'s trigger with a `BinaryEventTrigger(event_source="data_staleness")` — matching the
pattern already used correctly for `ORACLE_OUTAGE_HALT` / `CROSS_CLOUD_EGRESS_HALT` / `CUSTODY_ENDPOINT_HALT` three
rules below it in the same file. The caller populates `active_events` (a `frozenset[str]`) with `"data_staleness"` when
MTDS/MDPS/features-\* actually reports stale output (the freshness-contract check already exists elsewhere per the
rule's own description — this just needs to feed a boolean into `active_events` instead of overloading the drawdown
field). This is a UAC-only change (no downstream caller needs to change — `BinaryEventTrigger` already reads
`active_events` via `.get()` with a safe empty-set default, so callers that don't populate it simply never fire this
rule, same as today's default-off state).

## Todos

- [x] ✅ [BACKEND] P1. Replace `GLOBAL_DATA_STALENESS_HALT`'s trigger with
      `BinaryEventTrigger(event_source="data_staleness")` in
      `unified_api_contracts/registry/risk_rules/global_rules.py`, matching the
      `ORACLE_OUTAGE_HALT`/`CROSS_CLOUD_EGRESS_HALT`/`CUSTODY_ENDPOINT_HALT` pattern in the same file. Update the rule's
      `description` if the event_source naming needs alignment with an existing freshness-contract check. (repo:
      unified-api-contracts) — unified-api-contracts@70ccaca1
- [x] ✅ [BACKEND] P1. Verify no existing caller currently relies on `GLOBAL_DATA_STALENESS_HALT` firing via the
      `MaxDrawdownTrigger` path (grep for tests asserting on this rule_id) and update them to the new `active_events`
      shape. (repo: unified-api-contracts, execution-service, strategy-service) — no caller asserted on the old
      `MaxDrawdownTrigger` path for this rule_id; strategy-service@23bfacd5 removed two stale workaround comments in
      `tests/risk/unit/v2/test_v2_risk.py` referencing the collision (values left unchanged — they exercise the
      legitimate per-account/GLOBAL_PORTFOLIO_DRAWDOWN_HALT drawdown path, not the staleness rule).
- [x] ✅ [VERIFY] P1. Before `strategy-service`'s `PeakNavTracker`/`build_rule_eval_context` output is ever wired into
      `execution-service`'s live `run_risk_preflight(..., account_state=...)` call, confirm this fix has shipped — do
      not wire real `current_drawdown_bps` into the live order path while the bug is still open. (repo:
      execution-service) — confirmed shipped: execution-service@91970a27 adds
      `test_normal_drawdown_does_not_trip_global_data_staleness_halt()` in `tests/unit/test_risk_preflight_gate.py`,
      exercising the real (non-stubbed) UAC registry + UTL evaluator with `current_drawdown_bps=100` and no
      `active_events` populated, asserting `GLOBAL_DATA_STALENESS_HALT` is no longer in `blocked_by`. Safe to wire
      `account_state` into the live call now.

## Progress Log

- **2026-07-13 (slot-13, sonnet/high)** — Found while migrating strategy-service's legacy daily-loss/drawdown gates to
  the UAC registry (`utl_reuse_phase1_strategy_risk_hwm_2026_07_13` todo 2). Traced the field collision to
  `global_rules.py` + confirmed via `execution-service`'s `_TRIGGER_REQUIRED_CONTEXT_KEY` dispatch that
  `MaxDrawdownTrigger` always keys off `current_drawdown_bps` regardless of rule_id. Confirmed latent (not firing today)
  by checking `execution-service/engine/orchestrator.py:213`'s actual call site — `account_state` is never passed. Filed
  this issue rather than fixing UAC directly in-plan: the fix is cross-repo (UAC) and outside this todo's declared
  `repos: [strategy-service]` scope, and the trigger redesign + caller-side `active_events` wiring decision is a genuine
  scoped change of its own, not an adjacent one-line fix.
- **2026-07-13 (slot-11, sonnet/high)** — Shipped all three todos. UAC fix (`unified-api-contracts@70ccaca1`) replaces
  `GLOBAL_DATA_STALENESS_HALT`'s trigger with `BinaryEventTrigger(event_source="data_staleness")`, matching the
  `ORACLE_OUTAGE_HALT`/`CROSS_CLOUD_EGRESS_HALT`/`CUSTODY_ENDPOINT_HALT` pattern. Confirmed no caller asserted on the
  old `MaxDrawdownTrigger` path for this rule_id; `strategy-service@23bfacd5` removed two stale workaround comments
  referencing the collision (test values unchanged — they cover the legitimate drawdown path). Added a regression test
  `execution-service@91970a27` (`test_normal_drawdown_does_not_trip_global_data_staleness_halt`) exercising the real UAC
  registry + UTL evaluator to prove a normal drawdown no longer fires the rule. All three repos verified fully pushed
  (`git rev-list --count HEAD ^origin/live-defi-rollout` = 0). Status: resolved.
