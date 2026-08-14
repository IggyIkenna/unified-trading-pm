---
doc_type: issue
title: Live path has no stale-producer detection — a silent strategy-service triggers no execution-side action
summary: >-
  Measured 2026-08-14: if strategy-service goes down or stops publishing, execution-service does NOT detect it. It gates
  on INPUT freshness (market-data age vs venue SLA), never on PRODUCER liveness. The kill switch is armed by exactly 5
  risk conditions, none of which is "an internal service went silent". The dependency-health policy DOES classify
  INTERNAL_SERVICE with recovery/warning/escalation buffers, but it only emits WARN/SEV1/SEV0 alerts — it has ZERO
  consumers in execution-service or strategy-service, so it pages a human and halts nothing. The batch/data pipeline
  just got exactly this mechanism (alert-driven dependency revocation); live has no equivalent.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [execution-service, strategy-service, alerting-service, unified-api-contracts]
scope: [engineer, admin]
tags: [live-trading, safety, kill-switch, dependency-health, staleness, revocation]
related:
  [
    /codex/04-architecture/dependency-health-policy.md,
    /codex/04-architecture/autonomous-recovery-matrix.md,
    /codex/04-architecture/kill-switch-circuit-breaker.md,
    /plans/active/alert_driven_dependency_revocation_2026_08_12.md,
    /plans/active/revocation_arming_2026_08_14.md,
  ]
created: "2026-08-14"
last_updated: 2026-08-14
parent_epic: observability_master
assigned_vm: NA
execution_scope: local-only
priority: P0
assigned_role: infra
locked_by:
locked_since:
resolved_by:
supersedes:
superseded_by:
source: operator question 2026-08-14 — measured while arming /plans/active/revocation_arming_2026_08_14.md
drift_direction: advance-code
depends_on: []
---

# Live path has no stale-producer detection

**The operator's question, 2026-08-14:** _"The strategy service goes down. There's a delay, it doesn't send a heartbeat.
The execution service has to respond to that... it would itself do the retries or shutdowns, and that would trigger the
action downstream. Is that the flow?"_

**Measured answer: no. That flow does not exist today.** Everything below is measurement, not inference.

## What actually exists

| Mechanism                                           | What it keys on                       | What it does                                  |
| --------------------------------------------------- | ------------------------------------- | --------------------------------------------- |
| `execution_service.validation.freshness_gate`       | MARKET DATA age vs venue SLA          | raises `DataStalenessError`, blocks the order |
| `LIVE_ALERT_RULES` with `triggers_kill_switch=True` | 5 named risk conditions               | arms the kill switch via the UTL bus          |
| `dependency_health_policy` (UAC + alerting-service) | per-dependency outage seconds         | emits WARN / SEV1 / SEV0 — **alerts only**    |
| `strategy_service.supervisor.health_aggregator`     | per-ClientWorker subprocess heartbeat | strategy-service's OWN health endpoint        |

**The five kill-switch-arming rules, in full** (`triggers_kill_switch=True` in `LIVE_ALERT_RULES`):
`KILL_SWITCH_DEFI_LIQUIDATION_RISK` (global) · `KILL_SWITCH_PORTFOLIO_DRAWDOWN` (global) ·
`KILL_SWITCH_VENUE_DISCONNECT` (venue) · `KILL_SWITCH_ML_MODEL_FAILURE` (archetype) · `KILL_SWITCH_ORACLE_DIVERGENCE`
(global).

`VENUE_DISCONNECT` is the closest, and it is about an EXTERNAL venue, not an internal producer.

## The three gaps, precisely

1. **Freshness is checked on the INPUT, not on the PRODUCER.** `assert_market_data_fresh()` asks "is this tick within
   its venue's SLA". It cannot fire because strategy-service stopped publishing instructions — there is no instruction
   whose age it would be checking. A producer that goes silent produces no stale record; it produces NO record, and
   nothing on the live path treats absence as a signal. This is the live analogue of the honest-absence rule the data
   pipeline already enforces.

2. **The dependency-health policy is inert on the trading path.** It classifies `INTERNAL_SERVICE` and carries
   `expected_recovery_time` / `warning_buffer` / `hard_escalation_seconds` per dependency, and alerting-service
   evaluates it. But `rg -l 'health_policy|DependencyHealth'` over execution-service (1384 py files) and
   strategy-service (1033 py files) returns **zero** consumers. It pages a human; it changes no behaviour. This is the
   same shape as the defect just found in the batch path — a policy with no actuator — one layer up.

3. **No scope arms on internal-service silence.** The kill switch has a `STRATEGY` scope in its taxonomy, and nothing
   publishes to it for a silent strategy-service.

## Why this matters more than "no new orders"

A stopped strategy-service is not fail-safe by default. New target positions stop arriving, so execution holds — but
**existing exposure keeps running unmanaged**: no rebalancing, no exits, no deleverage instructions. The positions that
were open when the producer died stay open, at whatever the market does next, until a human notices the page. For a
delta-neutral book that is a slow bleed; for a leveraged one it is the liquidation ladder with nobody on it.

## Relationship to the batch work

`/plans/active/alert_driven_dependency_revocation_2026_08_12.md` built exactly this mechanism for the DATA PIPELINE:
alert identity → `DependentAction` → markers a dependent reads → hold admission / drain in flight. The live path has the
same shape of problem and none of the machinery. **Do not simply reuse the batch actuator**: its delivery is GCS markers
polled on a heartbeat tick, which is right for a VM doing hour-long shards and far too slow for an execution loop. The
reusable parts are the POLICY shape (an identity → action table with a machine-checked ceiling) and the lesson that a
policy without a wired actuator reads as done and does nothing.

## Proposed todos (for the operator to place)

- [ ] [CODE] P0. Decide the intended live behaviour when a producer goes silent — hold new orders only, or also flatten
      / hand existing exposure to a supervisor. This is a risk decision, not an engineering one, and everything below
      depends on it. Repo: unified-trading-pm (decision), then execution-service.
- [ ] [CODE] P0. Add producer-liveness gating to the execution path: a last-instruction-received clock per
      strategy/client with a declared SLA, checked where `assert_market_data_fresh()` is checked. Repo:
      execution-service.
- [ ] [CODE] P0. Wire `dependency_health_policy` to an actuator rather than only to alerts — at minimum, an
      `INTERNAL_SERVICE` breach at SEV0 should reach the kill-switch bus at its declared scope. Repo: alerting-service.
- [ ] [TEST] P0. An anti-inertness guard for the live path, mirroring the batch one: assert the dependency-health policy
      has a non-test consumer that changes behaviour. Repo: alerting-service.
- [ ] [DOC] P1. `/codex/04-architecture/dependency-health-policy.md` reads as though the policy governs behaviour; it
      governs alerting only. State that explicitly until an actuator exists. Repo: unified-trading-pm.

## Evidence

- `LIVE_ALERT_RULES` arming set enumerated at runtime via the deployment-service venv (5 rules, listed above).
- `rg -l 'health_policy|DependencyHealth' execution-service/ strategy-service/` → no matches, against populated trees
  (1384 / 1033 `.py` files — verified populated, because an earlier run of this same grep from the wrong working
  directory returned a misleading zero).
- `freshness_gate.py` module docstring: "checks whether the market data for an instrument is within its venue's
  freshness SLA before allowing order submission".
- `health_aggregator.py` module docstring: "per-ClientWorker heartbeat rollup... Consumed by
  `strategy_service/api/main.py`'s health endpoint" — intra-service, not cross-service.
