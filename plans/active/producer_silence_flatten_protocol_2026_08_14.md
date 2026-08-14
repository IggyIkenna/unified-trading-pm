---
doc_type: plan
title: Producer-silence protocol — flatten risk when strategy-service goes quiet, and know when we cannot
summary: >-
  Operator decision 2026-08-14, answering "what should happen when a producer goes silent". If strategy-service stops
  producing the cross-cutting data an instruction needs (risk, position) then: reconciliation UP means START FLATTENING
  RISK, with the protocol owned by the execution algo and aggressiveness strategy-dependent; reconciliation DOWN means
  we do not know our position, so it is a Slack alert and an operator physically checks the venues. Flattening is NOT
  close-everything — spreads are allowed, the objective is net delta per underlying, and the trade is chosen by
  post-trade leverage. Requires real code in strategy-service and execution-service, not just monitoring: a concept of
  flattening, strategy-aware position knowledge, and cross-venue long/short selection. SLAs must be long enough that
  ordinary restarts never trigger it.
status: active
nature: design
asset_group: [cross-cutting]
stage: [meta]
repos: [execution-service, strategy-service, batch-live-reconciliation-service, alerting-service, unified-api-contracts]
scope: [engineer, admin]
tags: [live-trading, safety, flattening, deleverage, staleness, risk, reconciliation]
related:
  [
    /plans/active/issues/live_path_has_no_stale_producer_revocation_2026_08_14.md,
    /codex/04-architecture/dependency-health-policy.md,
    /codex/04-architecture/autonomous-recovery-matrix.md,
    /codex/04-architecture/kill-switch-circuit-breaker.md,
    /codex/09-strategy/operational/paper-batch-live-reconciliation.md,
    /plans/active/cross_cutting_closeout_observability_and_monitoring_2026_08_09.md,
  ]
created: "2026-08-14"
last_updated: 2026-08-14
parent_epic: observability_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: design
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 3.6
assigned_role: infra
effort: xhigh
drift_direction: advance-code
locked_by:
locked_since:
context_scope:
  [
    execution-service/execution_service/algo_library/deleverage_executor.py,
    execution-service/execution_service/validation/freshness_gate.py,
    execution-service/execution_service/engine/kill_switch_bus_bridge.py,
    strategy-service/strategy_service/supervisor/health_aggregator.py,
    deployment-service/configs/dependency_health_policies.yaml,
  ]
supersedes:
superseded_by:
depends_on:
source: operator decision 2026-08-14 (verbatim requirements captured below)
---

# Producer-silence protocol

> **This is the operator's risk decision, recorded before implementation.** The question was: when a producer goes
> silent, do we hold new orders only, or also flatten existing exposure? The answer is neither-simply — it is
> conditional on whether we still know our position.

## The protocol

**Trigger.** strategy-service stops producing the data execution-service needs for a given instruction — including the
cross-cutting inputs (risk, position), not just the instruction itself.

**Branch A — reconciliation is UP (we know our position): START FLATTENING RISK.**

- The flattening protocol lives in the **execution algo**, not in the monitor. The monitor decides THAT we flatten; the
  algo decides HOW.
- **Aggressiveness is strategy-dependent** and must be wired through, because at this moment strategy-service is
  unreachable — so whatever the algo needs to know has to have been published in advance.

**Branch B — reconciliation is DOWN too (we do NOT know our position): ALERT, do not act.**

- Slack alert now; PagerDuty later. Deliberately not automated: an operator physically logs into the venues to see the
  real positions, then either flattens manually or instructs execution-service to flatten.
- Acting on an unknown position is worse than not acting. This branch exists precisely to stop the system from
  "flattening" against a position it cannot see.

**Reconciliation-down is itself fixable, and must be fixed first.** It routes through the normal escalation path —
restart, more memory, whatever the runbook says — with **retries and waits baked in**. Flattening is a worst-case last
resort; the system must try hard not to reach it.

## What flattening MEANS (this is the part with no code today)

- **NOT close every position.** Spreads are allowed and often correct. The objective is to bring exposure down, not to
  go flat on every leg.
- **Net delta per underlying** is the target, not per-instrument or per-venue position.
- **Choose the trade by POST-TRADE LEVERAGE.** Reducing a long and increasing a short can be delta-equivalent while
  differing materially in leverage after the fact — pick the better one.
- Longs and shorts already exist **across exchanges**; selection is cross-venue.
- **Model-agnostic and strategy-agnostic where it can be, specific where it must be.** The condition-based responses all
  flow through one path.

## SLA discipline (the requirement that prevents this being a nuisance)

**The down-timeout must be long enough that ordinary breaks and short restarts never trigger flattening.** This is the
recurring operator instruction and it governs every threshold in this plan: a deploy, a rolling restart or a brief
network blip must not cost a flatten. Calibrate the SLA to observed restart duration plus margin, and state the
measurement that justified the number.

## Todos

### Phase 1 — the decision inputs must exist before they are needed

- [ ] [CODE] P0. Define what execution-service must ALREADY hold to flatten without strategy-service. At the moment of
      the trigger the producer is unreachable, so every input has to have been published ahead of time: per-strategy
      flatten aggressiveness, the strategy's own notion of which legs are hedges vs directional, and the underlying each
      instrument maps to. Write it as a UAC contract, not per-service structs. Repo: unified-api-contracts.
- [ ] [CODE] P0. Publish that contract from strategy-service on every instruction, so the last-known value is always
      available. Repo: strategy-service.
- [ ] [TEST] P0. A test proving the flatten path needs NO call to strategy-service — construct the flatten decision with
      strategy-service mocked as hard-down. If it cannot, the contract above is incomplete. Repo: execution-service.

### Phase 2 — net-delta flattening, chosen by post-trade leverage

- [ ] [CODE] P0. Net-delta-per-underlying calculator over current cross-venue positions. Spreads must survive it: the
      output is a delta reduction target per underlying, never a per-leg close list. Repo: execution-service.
- [ ] [CODE] P0. Candidate-trade generator + selector: enumerate the ways to reduce a given delta (reduce long, increase
      short, across venues) and choose by POST-TRADE leverage. Delta-equivalent candidates are the normal case; leverage
      is the tiebreak that matters. Repo: execution-service.
- [ ] [CODE] P0. Wire the selector into an execution algo, reusing `algo_library/deleverage_executor.py`'s existing
      asset-group-aware actions rather than paralleling them. That module is MarginEvent-driven today; this adds a
      second trigger with different semantics (net-delta target vs margin-severity tactic) — keep the actions, do not
      duplicate them. Repo: execution-service.
- [ ] [TEST] P0. Assert a spread is NOT closed: a delta-neutral long/short pair must survive a flatten that targets a
      different underlying. This is the test that distinguishes flattening from panic-closing. Repo: execution-service.

### Phase 3 — the trigger, and the branch that refuses to act

- [ ] [CODE] P0. Producer-liveness detection for strategy-service: a last-complete-instruction clock per
      strategy/client, checked where `assert_market_data_fresh()` is checked. Note the distinction that made this
      necessary — the existing gate checks INPUT age, and a silent producer emits no record to age. Repo:
      execution-service.
- [ ] [CODE] P0. Branch on reconciliation health: UP → flatten; DOWN → alert only, act on nothing. The DOWN branch must
      be structurally incapable of placing an order. Repo: execution-service.
- [ ] [CODE] P0. Slack alert for the DOWN branch naming what the operator must do — log into the venues, read the real
      positions, then flatten manually or instruct execution-service. PagerDuty is a later upgrade, not a blocker. Repo:
      alerting-service.
- [ ] [CODE] P1. An operator-facing flatten instruction path into execution-service, so the manual branch is a typed
      command rather than venue-by-venue clicking. Repo: execution-service.

### Phase 4 — try hard not to get here

- [ ] [CODE] P0. Reconciliation-down escalation with retries and waits BEFORE any flatten: restart, resource bump, per
      the runbook. Flattening only after the escalation path is exhausted. Repo: batch-live-reconciliation-service.
- [ ] [OPERATOR] P0. Set the SLA numbers, and record the measurement behind them: the down-timeout must exceed observed
      rolling-restart and deploy durations with margin, so routine operations never trigger a flatten. Every threshold
      in this plan inherits from this decision.
- [ ] [TEST] P0. A restart-does-not-flatten test: bounce strategy-service for a normal restart duration and assert no
      flatten is triggered. This is the regression guard for the operator's standing instruction.

### Phase 5 — do not let it go inert

- [ ] [TEST] P0. Anti-inertness guards for every component here, per the pattern established 2026-08-14: assert each new
      decision component has a non-test caller. Three separate systems in this estate were individually complete,
      individually tested, and collectively inert; this plan adds several more components to that surface. Repo:
      execution-service.
