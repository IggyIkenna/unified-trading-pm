---
scope: [engineer, admin]
title: Alerting Playbook — Index
status: planned
created: 2026-05-07
authoritative_for:
  Index of the alerting-service playbook docs — alert taxonomy, operator response, threshold tuning, rehearsal
  procedure. Anchors every other alerting doc in this directory.
referenced_by:
  - plans/active/alerting_service_live_rules_2026_05_07.md
related:
  - codex/05-infrastructure/live-deployment-monitoring.md
  - codex/14-customer-journeys/dart/
---

# Alerting Playbook — Index

> **Status:** PLANNED — stub directory created 2026-05-07 to anchor forward-references from the alerting-service plan.
> Body of each sub-doc to be filled in as alerting-service ships.

## Severity glossary

Three vocabularies describe alert urgency in this workspace. They are aliases for the same underlying ordering, NOT
independent scales. The UAC `AlertSeverity` StrEnum is the SSOT — code declares severity using the codex enum; PagerDuty
incident-priority labels and Python `AlertSeverity.<MEMBER>` references both resolve to a single row in the table below.

| Codex enum (`AlertSeverity`) | PagerDuty incident priority | Time-to-ack     | Routing                                  | Examples                                                                                                                                                                                                       |
| ---------------------------- | --------------------------- | --------------- | ---------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CRITICAL`                   | P0 / P1                     | 5–15 min        | Telegram `live-defi` + PagerDuty primary | Kill-switch armed, data-correctness fail blocking live trades, cloud-switch validation failure, Aave HF < 1.2 emergency, T+1 audit discrepancy beyond tolerance, instruments-live preflight repeatedly failing |
| `HIGH`                       | P2                          | 1 hour          | Telegram `live-defi` + PagerDuty primary | Aave HF 1.2–1.5 (paused new entries), partial-fill compensation in flight, kill-switch auto-deactivated, circuit-breaker BACKOFF_ESCALATED, CeFi margin within pre-emptive buffer of initial-margin-call line  |
| `WARN`                       | P3                          | informational   | Telegram `live-defi` only                | Per-shard missing data > threshold, ML model staleness, position drift 2–5%, defi feature stale > SLA, Aave utilization spike above kink, perp funding regime flip, preflight rejected pre-submission          |
| `INFO`                       | P4                          | log / dashboard | Telegram `data-pipeline` only            | Coverage drop within ratchet tolerance, backfill VM auto-shutdown, individual retry / throttle, reconnection attempt + success, half-open circuit-probe                                                        |

**Notes**

- Source-of-truth: UAC `unified_api_contracts.canonical.crosscutting.alerting.codes.AlertSeverity` (CRITICAL / HIGH /
  WARN / INFO). Every alerting-service rule declares its severity via this enum.
- The PagerDuty `P0 / P1` split inside the `CRITICAL` row is an operational sub-distinction owned by
  [`pagerduty-escalation-policy.md`](pagerduty-escalation-policy.md) — kill-switch / data-correctness pages route P0
  with a 5-min ack target; the rest of `CRITICAL` routes P1 with a 15-min ack target. Both are `AlertSeverity.CRITICAL`
  at the codex layer.
- "Time-to-ack" for P0 / P1 / P2 is enforced by the PagerDuty escalation chain
  ([`pagerduty-escalation-policy.md`](pagerduty-escalation-policy.md) § "Escalation chain"). P3 / `INFO` are not paged
  and have no SLA.
- Quiet hours: there are none. P0 / P1 page 24/7. P2 pages within business-hours-aware windows per the on-call rotation.
  P3 / informational deliveries respect Telegram quiet-hours per group settings.
- Adding a new alert: pick the codex enum value from this table; the Python rule body uses
  `severity=AlertSeverity.<MEMBER>`; PagerDuty routing is automatic via the alerting-service rule engine. Do NOT
  hand-roll PagerDuty / Telegram calls in rule bodies.

The downstream docs cite this glossary instead of redefining the mapping:

- [`pagerduty-escalation-policy.md`](pagerduty-escalation-policy.md) — escalation chain, on-call rotation, ack protocol;
  references this table for the codex-enum / P-tier mapping.
- [`threshold-tuning.md`](threshold-tuning.md) — Phase-7 quietness-baseline procedure; references this table when a new
  threshold's `severity=AlertSeverity.<MEMBER>` is being chosen.
- [`../../03-observability/alerting.md`](../../03-observability/alerting.md) — autonomous-recovery alert matrix;
  references this table for severity definitions.

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
15. [`defi_feature_stale.md`](./defi_feature_stale.md) — LST-yield / on-chain feature stale > SLA; features-service
    (onchain family) restart procedure.
16. [`preflight_failed.md`](./preflight_failed.md) — execution-service preflight rejected order pre-submission.
17. [`service_degraded.md`](./service_degraded.md) — workspace service in degraded mode; restart procedure.
18. [`balance_drift.md`](./balance_drift.md) — wallet balance vs PBM ledger discrepancy > USD threshold.
19. [`order_rejection_spike.md`](./order_rejection_spike.md) — venue reject rate > threshold; rate-limit / risk-engine
    throttling.
20. [`position_drift.md`](./position_drift.md) — actual weight diverges from target > rebalance threshold.

## Cross-references

- **Plan(s) implementing this:**
  [`alerting_service_live_rules`](../../../plans/active/alerting_service_live_rules_2026_05_07.md).
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
