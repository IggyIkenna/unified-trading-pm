---
title: Alerting Playbook — Index
status: planned
created: 2026-05-07
authoritative_for:
  Index of the alerting-service playbook docs — alert taxonomy, operator response, threshold tuning, rehearsal
  procedure. Anchors every other alerting doc in this directory.
referenced_by:
  - plans/active/alerting_service_live_rules_2026_05_07.plan.md
related:
  - codex/05-infrastructure/live-deployment-monitoring.md
  - codex/14-playbooks/dart/
---

# Alerting Playbook — Index

> **Status:** PLANNED — stub directory created 2026-05-07 to anchor forward-references from the alerting-service plan.
> Body of each sub-doc to be filled in as alerting-service ships.

## Purpose

The alerting-service is the single workspace surface that turns live event-stream signals (heartbeat misses, SLA
breaches, fill-quality drift, risk-limit approaches) into pages. This directory is the SSOT for what alerts exist, what
an operator does about each, how thresholds are set, and how we verify the whole chain works.

## Sub-documents

### Cross-cutting

1. [`alert-code-taxonomy.md`](./alert-code-taxonomy.md) — UAC `AlertCode` StrEnum SSOT. Every alert has a stable code
   that operator runbooks reference.
2. [`operator-playbook.md`](./operator-playbook.md) — per-AlertCode operator response: ack / escalate / kill-switch /
   runbook-link.
3. [`threshold-tuning.md`](./threshold-tuning.md) — how thresholds are set, who owns, when they get reviewed.
4. [`rehearsal-procedure.md`](./rehearsal-procedure.md) — quarterly alert-rehearsal procedure to verify paging works
   end-to-end.
5. [`_template.md`](./_template.md) — canonical shape for per-AlertCode runbooks.

### Per-AlertCode runbooks (CRITICAL — kill-switch family)

6. [`kill_switch_defi_liquidation_risk.md`](./kill_switch_defi_liquidation_risk.md) — Aave HF approaching liquidation;
   auto-deleverage via flash-loan-receiver.
7. [`kill_switch_portfolio_drawdown.md`](./kill_switch_portfolio_drawdown.md) — global P&L stop; flat-only mode +
   operator-led resume.
8. [`kill_switch_venue_disconnect.md`](./kill_switch_venue_disconnect.md) — perp-hedge venue outage > 5min; halts the
   affected archetype only; hedge-roll-to-backup decision tree.

### Per-AlertCode runbooks (CRITICAL — DeFi)

9. [`circuit_breaker_open.md`](./circuit_breaker_open.md) — per-(service, venue) circuit OPEN; auto-recovers via
   half-open retry.
10. [`defi_health_factor_critical.md`](./defi_health_factor_critical.md) — Aave HF in warning band; pre-emptive
    deleverage candidate.
11. [`defi_weeth_depeg.md`](./defi_weeth_depeg.md) — weETH/ETH peg deviation; LST exposure reduction.

### Per-AlertCode runbooks (HIGH)

12. [`margin_threshold_breach.md`](./margin_threshold_breach.md) — CeFi margin within pre-emptive buffer of
    initial-margin-call line.

### Per-AlertCode runbooks (WARN — Telegram-only)

13. [`defi_aave_utilization_spike.md`](./defi_aave_utilization_spike.md) — pool utilization above kink; carry-strategy
    viability check.
14. [`defi_funding_rate_flip.md`](./defi_funding_rate_flip.md) — perp funding regime change; re-pole vs pause.
15. [`defi_feature_stale.md`](./defi_feature_stale.md) — LST-yield / on-chain feature stale > SLA;
    features-onchain-service restart procedure.
16. [`preflight_failed.md`](./preflight_failed.md) — execution-service preflight rejected order pre-submission.
17. [`service_degraded.md`](./service_degraded.md) — workspace service in degraded mode; restart procedure.
18. [`balance_drift.md`](./balance_drift.md) — wallet balance vs PBM ledger discrepancy > USD threshold.
19. [`order_rejection_spike.md`](./order_rejection_spike.md) — venue reject rate > threshold; rate-limit / risk-engine
    throttling.
20. [`position_drift.md`](./position_drift.md) — actual weight diverges from target > rebalance threshold.

## Cross-references

- **Plan(s) implementing this:**
  [`alerting_service_live_rules`](../../../plans/active/alerting_service_live_rules_2026_05_07.plan.md).
- **Related codex SSOTs:** [`live-deployment-monitoring`](../../05-infrastructure/live-deployment-monitoring.md),
  [DART playbook](../dart/).
- **Code:** `alerting-service/` (TBD).

## Reading order

For new operators: `operator-playbook.md` first (you'll get paged), then `alert-code-taxonomy.md` (the codes you'll
see), then `threshold-tuning.md` (when thresholds need changing), then `rehearsal-procedure.md` (you'll be on the
quarterly rotation).

For service authors adding a new alert: `alert-code-taxonomy.md` first (register the new code), then
`threshold-tuning.md` (set the threshold + owner), then `operator-playbook.md` (write the response runbook), then
`rehearsal-procedure.md` (add it to the next quarterly rehearsal scope).
