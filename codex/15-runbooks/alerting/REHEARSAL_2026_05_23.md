---
scope: [engineer, admin]
title: "Phase 8 Live Rehearsal Sign-off — 2026-05-23"
status: pending-operator-execution
created: 2026-05-23
operator: TBD
authoritative_for: Phase 8 live rehearsal sign-off for alerting-service May-23 cutover
referenced_by:
  - plans/active/alerting_service_live_rules_2026_05_07.md
related:
  - codex/15-runbooks/alerting/rehearsal-procedure.md
  - codex/15-runbooks/alerting/alert-code-taxonomy.md
---

# Phase 8 Live Rehearsal Sign-off — 2026-05-23

> **STATUS: PENDING OPERATOR EXECUTION**
>
> Template created 2026-05-23 by agent slot 2. Operator must run `alerting-service/scripts/inject_synthetic_alert.py`
> for each of the 15 alert codes below and fill in pass/fail + notes for each verification step.
>
> Command to run rehearsal:
>
> ```bash
> cd alerting-service
> # Standard rehearsal (15 codes):
> python3 scripts/inject_synthetic_alert.py
> # CRITICAL-severity + kill-switch verification:
> python3 scripts/inject_synthetic_alert.py --verify-kill-switch
> ```

## Instructions

For each alert code below:

1. Inject the synthetic alert via the script
2. Verify each of the 6 checks (a–f)
3. Fill in `[ ]` → `[x]` for each passing check
4. Add notes if any check fails or needs follow-up

**Verification checks:**

- **(a)** Alert lands in correct channel (Telegram ops / PagerDuty / Slack per AlertRule)
- **(b)** DART panel shows the alert (notification bell + alert detail modal)
- **(c)** Ack flow works (click Ack in DART → alert moves to `acknowledged` state)
- **(d)** Escalate flow works (synthetic PD page if CRITICAL)
- **(e)** Runbook deep-link works (opens correct `codex/15-runbooks/alerting/*.md`)
- **(f)** Auto-resolve works (alert clears after synthetic TTL)

---

## CRITICAL Kill-switch codes

### KILL_SWITCH_DEFI_LIQUIDATION_RISK (CRITICAL, GLOBAL scope)

- [ ] (a) Lands in PagerDuty + Telegram ops channel
- [ ] (b) DART shows alert with CRITICAL badge
- [ ] (c) Ack flow works
- [ ] (d) PD escalation fires
- [ ] (e) Runbook link: [kill_switch_defi_liquidation_risk.md](./kill_switch_defi_liquidation_risk.md)
- [ ] (f) Auto-resolve works
- **Notes:**

### KILL_SWITCH_PORTFOLIO_DRAWDOWN (CRITICAL, GLOBAL scope)

- [ ] (a) Lands in PagerDuty + Telegram ops channel
- [ ] (b) DART shows alert with CRITICAL badge
- [ ] (c) Ack flow works
- [ ] (d) PD escalation fires
- [ ] (e) Runbook link: [kill_switch_portfolio_drawdown.md](./kill_switch_portfolio_drawdown.md)
- [ ] (f) Auto-resolve works
- **Notes:**

### KILL_SWITCH_VENUE_DISCONNECT (CRITICAL, VENUE scope)

- [ ] (a) Lands in PagerDuty + Telegram ops channel
- [ ] (b) DART shows alert with CRITICAL badge
- [ ] (c) Ack flow works
- [ ] (d) PD escalation fires
- [ ] (e) Runbook link: [kill_switch_venue_disconnect.md](./kill_switch_venue_disconnect.md)
- [ ] (f) Auto-resolve works
- **Notes:**

### CIRCUIT_BREAKER_OPEN (CRITICAL)

- [ ] (a) Lands in PagerDuty + Telegram ops channel
- [ ] (b) DART shows alert with CRITICAL badge
- [ ] (c) Ack flow works
- [ ] (d) PD escalation fires
- [ ] (e) Runbook link: [circuit_breaker_open.md](./circuit_breaker_open.md)
- [ ] (f) Auto-resolve works
- **Notes:**

---

## CRITICAL DeFi codes

### DEFI_HEALTH_FACTOR_CRITICAL (CRITICAL)

- [ ] (a) Lands in PagerDuty + Telegram ops channel
- [ ] (b) DART shows alert with CRITICAL badge
- [ ] (c) Ack flow works
- [ ] (d) PD escalation fires
- [ ] (e) Runbook link: [defi_health_factor_critical.md](./defi_health_factor_critical.md)
- [ ] (f) Auto-resolve works
- **Notes:**

### DEFI_WEETH_DEPEG (HIGH)

- [ ] (a) Lands in PagerDuty + Telegram ops channel
- [ ] (b) DART shows alert with HIGH badge
- [ ] (c) Ack flow works
- [ ] (d) PD notification (non-paging)
- [ ] (e) Runbook link: [defi_weeth_depeg.md](./defi_weeth_depeg.md)
- [ ] (f) Auto-resolve works
- **Notes:**

### DEFI_AAVE_UTILIZATION_SPIKE (HIGH)

- [ ] (a) Lands in PagerDuty + Telegram ops channel
- [ ] (b) DART shows alert with HIGH badge
- [ ] (c) Ack flow works
- [ ] (d) PD notification (non-paging)
- [ ] (e) Runbook link: [defi_aave_utilization_spike.md](./defi_aave_utilization_spike.md)
- [ ] (f) Auto-resolve works
- **Notes:**

### DEFI_FUNDING_RATE_FLIP (WARN)

- [ ] (a) Lands in Telegram ops channel (no PD for WARN)
- [ ] (b) DART shows alert with WARN badge
- [ ] (c) Ack flow works
- [ ] (d) N/A (WARN severity, no PD page)
- [ ] (e) Runbook link: [defi_funding_rate_flip.md](./defi_funding_rate_flip.md)
- [ ] (f) Auto-resolve works
- **Notes:**

### DEFI_FEATURE_STALE (WARN)

- [ ] (a) Lands in Telegram ops channel (no PD for WARN)
- [ ] (b) DART shows alert with WARN badge
- [ ] (c) Ack flow works
- [ ] (d) N/A (WARN severity, no PD page)
- [ ] (e) Runbook link: [defi_feature_stale.md](./defi_feature_stale.md)
- [ ] (f) Auto-resolve works
- **Notes:**

---

## Service-level codes

### PREFLIGHT_FAILED (HIGH)

- [ ] (a) Lands in PagerDuty + Telegram ops channel
- [ ] (b) DART shows alert with HIGH badge
- [ ] (c) Ack flow works
- [ ] (d) PD notification (non-paging)
- [ ] (e) Runbook link: [preflight_failed.md](./preflight_failed.md)
- [ ] (f) Auto-resolve works
- **Notes:**

### SERVICE_DEGRADED (HIGH)

- [ ] (a) Lands in PagerDuty + Email
- [ ] (b) DART shows alert with HIGH badge
- [ ] (c) Ack flow works
- [ ] (d) PD notification (non-paging)
- [ ] (e) Runbook link: [service_degraded.md](./service_degraded.md) _(doc TBC)_
- [ ] (f) Auto-resolve works
- **Notes:**

### BALANCE_DRIFT (HIGH)

- [ ] (a) Lands in PagerDuty + Telegram ops channel
- [ ] (b) DART shows alert with HIGH badge
- [ ] (c) Ack flow works
- [ ] (d) PD notification (non-paging)
- [ ] (e) Runbook link: [balance_drift.md](./balance_drift.md)
- [ ] (f) Auto-resolve works
- **Notes:**

### ORDER_REJECTION_SPIKE (HIGH)

- [ ] (a) Lands in PagerDuty + Telegram ops channel
- [ ] (b) DART shows alert with HIGH badge
- [ ] (c) Ack flow works
- [ ] (d) PD notification (non-paging)
- [ ] (e) Runbook link: [order_rejection_spike.md](./order_rejection_spike.md)
- [ ] (f) Auto-resolve works
- **Notes:**

### MARGIN_THRESHOLD_BREACH (HIGH)

- [ ] (a) Lands in PagerDuty + Telegram ops channel
- [ ] (b) DART shows alert with HIGH badge
- [ ] (c) Ack flow works
- [ ] (d) PD notification (non-paging)
- [ ] (e) Runbook link: [margin_threshold_breach.md](./margin_threshold_breach.md)
- [ ] (f) Auto-resolve works
- **Notes:**

### POSITION_DRIFT (WARN)

- [ ] (a) Lands in Telegram ops channel
- [ ] (b) DART shows alert with WARN badge
- [ ] (c) Ack flow works
- [ ] (d) N/A (WARN severity)
- [ ] (e) Runbook link: [position_drift.md](./position_drift.md)
- [ ] (f) Auto-resolve works
- **Notes:**

---

## KILL_SWITCH End-to-End Verification (--verify-kill-switch)

Run: `python3 scripts/inject_synthetic_alert.py --verify-kill-switch`

- [ ] `KILL_SWITCH_DEFI_LIQUIDATION_RISK` → KillSwitchEvent emitted (GLOBAL scope)
- [ ] `KILL_SWITCH_PORTFOLIO_DRAWDOWN` → KillSwitchEvent emitted (GLOBAL scope)
- [ ] `KILL_SWITCH_VENUE_DISCONNECT` → KillSwitchEvent emitted (VENUE scope)
- [ ] execution-service received KillSwitchEvent + halt-orders triggered
- [ ] strategy-service received halt signal

**Notes:**

---

## Sign-off

| Field          | Value                                                               |
| -------------- | ------------------------------------------------------------------- |
| Operator name  | TBD                                                                 |
| Date           | 2026-05-23                                                          |
| Environment    | prod-equivalent staging                                             |
| Script version | alerting-service@6d4f222 (inject) + @2f63775 (--verify-kill-switch) |
| Outcome        | PENDING                                                             |
| Next action    | Operator to fill in pass/fail above and change Outcome to PASS/FAIL |
