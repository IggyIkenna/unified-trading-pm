---
scope: [engineer, admin]
---

<!-- POST_PLAN_BANNER_2026_05_06_FINAL -->

> **Post-2026-05-06** — read [`../POST_PLAN_REALITY_2026_05_06.md`](../POST_PLAN_REALITY_2026_05_06.md) before code/doc
> changes informed by this doc. Active plans: writegate-honest-coverage, predictions-canonical_question_group,
> data-status-multi-axis-shard. If this doc disagrees with active plans, the plans win. Flag conflicts to user.

# Alerting

## Principle

**Every autonomous recovery action MUST generate an alert.** Autonomous recovery is by definition unusual — the system
is self-healing because something broke. Even if recovery succeeds, the operator must know it happened. Different
severities route to different channels, but nothing is silent.

Alert delivery channels: **Telegram** (primary, all alerts) and **PagerDuty** (critical trading events). Slack is
deprecated.

---

## Alert Severity Tiers

> **Severity vocabulary SSOT** — see
> [`14-playbooks/alerting/README.md` § Severity glossary](../14-playbooks/alerting/README.md#severity-glossary) for the
> canonical mapping between the UAC `AlertSeverity` codex enum (CRITICAL / HIGH / WARN / INFO), PagerDuty incident
> priorities (P0 / P1 / P2 / P3), time-to-ack targets, routing channels, and worked examples. The tier labels used in
> the recovery matrix below (`T1 CRITICAL` / `T2 HIGH` / `T3 WARNING` / `T4 INFO`) are display aliases for the codex
> enum members of the same name.

`T3 WARNING` in the matrix below corresponds to `AlertSeverity.WARN` in code (the codex enum spells it `WARN`, not
`WARNING`). All other display names match the enum.

---

## Autonomous Recovery Alert Matrix

Every autonomous recovery action the system takes, mapped to its alert tier:

### Retry & Reconnection (T3-T4)

| Event                               | Severity   | Alert                | Why                                    |
| ----------------------------------- | ---------- | -------------------- | -------------------------------------- |
| First retry on transient error      | T4 INFO    | Telegram             | Normal, but operator should see volume |
| Retry exhausted (3 attempts failed) | T3 WARNING | Telegram             | Error persisted through retries        |
| Reconnection attempt                | T3 WARNING | Telegram             | Connection was lost                    |
| Reconnection succeeded              | T4 INFO    | Telegram             | Recovery confirmation                  |
| Reconnection failed                 | T2 HIGH    | PagerDuty + Telegram | Venue unreachable                      |

### Circuit Breaker (T2-T1)

| Event                         | Severity    | Alert                       | Why                                         |
| ----------------------------- | ----------- | --------------------------- | ------------------------------------------- |
| DEGRADED (30% failure rate)   | T3 WARNING  | Telegram                    | Venue health declining, throttling orders   |
| OPEN (60% failure rate)       | T1 CRITICAL | PagerDuty P1 + Telegram     | Venue blocked, orders queued                |
| BACKOFF_ESCALATED (cycle > 1) | T2 HIGH     | PagerDuty P2 + Telegram     | Recovery failing repeatedly                 |
| HALF_OPEN probe               | T4 INFO     | Telegram                    | Testing recovery                            |
| CLOSED (recovery)             | T3 WARNING  | Telegram                    | Recovery confirmed — operator should review |
| ORDER_THROTTLED               | T4 INFO     | Telegram (suppressed >10/s) | Individual order dropped                    |

### Multi-Venue Cascade (T1)

| Event                           | Severity    | Alert                   | Why                             |
| ------------------------------- | ----------- | ----------------------- | ------------------------------- |
| >50% venues OPEN for a strategy | T1 CRITICAL | PagerDuty P1 + Telegram | Auto STOP_NEW_ONLY activated    |
| All venues OPEN                 | T1 CRITICAL | PagerDuty P1 + Telegram | Firm-wide kill switch activated |

### Kill Switch (T1)

| Event                        | Severity    | Alert                   | Why                                     |
| ---------------------------- | ----------- | ----------------------- | --------------------------------------- |
| KILL_SWITCH_ACTIVATED        | T1 CRITICAL | PagerDuty P1 + Telegram | All trading halted                      |
| KILL_SWITCH_DEACTIVATED      | T3 WARNING  | Telegram                | Trading resumed                         |
| KILL_SWITCH_AUTO_DEACTIVATED | T2 HIGH     | PagerDuty P2 + Telegram | Timer expired, trading auto-resumed     |
| KILL_SWITCH_BLOCKED_STARTUP  | T1 CRITICAL | PagerDuty P1 + Telegram | Service started with active kill switch |

### Multi-Leg Compensation (T1-T2)

| Event                         | Severity    | Alert                   | Why                                               |
| ----------------------------- | ----------- | ----------------------- | ------------------------------------------------- |
| UNHEDGED_POSITION_ALERT       | T1 CRITICAL | PagerDuty P1 + Telegram | Partial fill, compensation attempting             |
| Compensation trade succeeded  | T2 HIGH     | PagerDuty P2 + Telegram | Position unwound, but incident occurred           |
| MULTI_LEG_COMPENSATION_FAILED | T1 CRITICAL | PagerDuty P1 + Telegram | Unhedged position exists, circuit breaker tripped |

### Position Drift (T2-T1)

| Event                              | Severity    | Alert                   | Why                           |
| ---------------------------------- | ----------- | ----------------------- | ----------------------------- |
| POSITION_DRIFT_DETECTED (WARNING)  | T3 WARNING  | Telegram                | Drift 2-5%, monitoring        |
| POSITION_DRIFT_DETECTED (CRITICAL) | T1 CRITICAL | PagerDuty P1 + Telegram | Drift >5%, auto STOP_NEW_ONLY |

### Health Factor / Margin (T2-T1)

| Event                 | Severity    | Alert                   | Why                         |
| --------------------- | ----------- | ----------------------- | --------------------------- |
| HF 1.5-2.0 (ELEVATED) | T3 WARNING  | Telegram                | Strategy reducing exposure  |
| HF 1.2-1.5 (WARNING)  | T2 HIGH     | PagerDuty P2 + Telegram | Strategy paused new entries |
| HF 1.0-1.2 (CRITICAL) | T1 CRITICAL | PagerDuty P1 + Telegram | Auto-deleverage triggered   |
| HF < 1.0 (EMERGENCY)  | T1 CRITICAL | PagerDuty P1 + Telegram | Emergency close all         |

### Reconciliation (T2-T1)

| Event                                | Severity    | Alert                   | Why                               |
| ------------------------------------ | ----------- | ----------------------- | --------------------------------- |
| Reconciliation break detected        | T3 WARNING  | Telegram                | Operator should investigate       |
| RECON_DEGRADED close (closing blind) | T2 HIGH     | PagerDuty P2 + Telegram | Closing without verified state    |
| DUAL_FAILURE_DETECTED                | T1 CRITICAL | PagerDuty P1 + Telegram | Can't reconcile AND can't execute |

### Order Recovery (T2-T3)

| Event                    | Severity    | Alert                   | Why                                  |
| ------------------------ | ----------- | ----------------------- | ------------------------------------ |
| ORDER_RECOVERY_INITIATED | T3 WARNING  | Telegram                | Startup scanning for orphaned orders |
| ORDER_ORPHANED           | T2 HIGH     | PagerDuty P2 + Telegram | Found order not in our state         |
| ORDER_RECOVERY_COMPLETED | T4 INFO     | Telegram                | Recovery finished                    |
| ORDER_RECOVERY_FAILED    | T1 CRITICAL | PagerDuty P1 + Telegram | Could not resolve orphaned orders    |

---

## Alerting-Service Routing Rules

The routing rules in `alerting-service/notifiers/router.py` must map events to channels. The canonical rules:

```python
# Default routing rules (config-driven, loaded from AlertingSystemConfig)
ROUTING_RULES = [
    # T1 CRITICAL — PagerDuty P1 + Telegram
    {"event_pattern": "KILL_SWITCH_*",                "channels": ["pagerduty", "telegram"], "severity": "critical"},
    {"event_pattern": "CIRCUIT_BREAKER_OPEN",         "channels": ["pagerduty", "telegram"], "severity": "critical"},
    {"event_pattern": "MULTI_LEG_COMPENSATION_FAILED","channels": ["pagerduty", "telegram"], "severity": "critical"},
    {"event_pattern": "UNHEDGED_POSITION_ALERT",      "channels": ["pagerduty", "telegram"], "severity": "critical"},
    {"event_pattern": "DUAL_FAILURE_DETECTED",        "channels": ["pagerduty", "telegram"], "severity": "critical"},
    {"event_pattern": "ORDER_RECOVERY_FAILED",        "channels": ["pagerduty", "telegram"], "severity": "critical"},

    # T2 HIGH — PagerDuty P2 + Telegram
    {"event_pattern": "CIRCUIT_BREAKER_BACKOFF_*",    "channels": ["pagerduty", "telegram"], "severity": "warning"},
    {"event_pattern": "ORDER_ORPHANED",               "channels": ["pagerduty", "telegram"], "severity": "warning"},
    {"event_pattern": "POSITION_DRIFT_DETECTED",      "channels": ["pagerduty", "telegram"], "severity": "warning"},
    {"event_pattern": "RECON_DEGRADED_*",             "channels": ["pagerduty", "telegram"], "severity": "warning"},

    # T3 WARNING — Telegram only
    {"event_pattern": "CIRCUIT_BREAKER_DEGRADED",     "channels": ["telegram"]},
    {"event_pattern": "CIRCUIT_BREAKER_CLOSED",       "channels": ["telegram"]},
    {"event_pattern": "PREFLIGHT_FAILED",             "channels": ["telegram"]},
    {"event_pattern": "SERVICE_DEGRADED",             "channels": ["telegram"]},
    {"event_pattern": "POSITION_CORRECTION_*",        "channels": ["telegram"]},
    {"event_pattern": "PORTFOLIO_REBALANCE_*",        "channels": ["telegram"]},
    {"event_pattern": "ORDER_RECOVERY_*",             "channels": ["telegram"]},

    # T4 INFO — Telegram (fallback for everything else)
    {"event_pattern": "*",                            "channels": ["telegram"]},
]
```

First match wins. The `*` fallback ensures nothing is silent.

---

## Infrastructure Alerts

| Alert           | Trigger                        | Detection                | Response                  | Status      |
| --------------- | ------------------------------ | ------------------------ | ------------------------- | ----------- |
| OOM Death Loop  | Serial log OOM >= 5 times      | UTD v2 auto-sync (30s)   | VM terminated             | IMPLEMENTED |
| Startup Timeout | No SERVICE_STARTED after 5 min | UTD v2 auto-sync (30s)   | VM terminated             | IMPLEMENTED |
| Memory Critical | memory_percent > 90%           | PerformanceMonitor (30s) | Log ERROR, resource_alert | IMPLEMENTED |
| Memory Warning  | memory_percent > 85%           | PerformanceMonitor (30s) | Log WARNING               | IMPLEMENTED |

## Pipeline Alerts

| Alert             | Trigger                  | Detection       | Response                     | Status      |
| ----------------- | ------------------------ | --------------- | ---------------------------- | ----------- |
| Service Failed    | FAILED event             | Event parser    | Shard state failed, Telegram | IMPLEMENTED |
| Stage Timeout     | No STOPPED within 30 min | Time comparison | Investigation alert          | IMPLEMENTED |
| Validation Failed | VALIDATION_FAILED event  | Event parser    | Check upstream deps          | IMPLEMENTED |

## Live Trading Alerts

| Alert                | Trigger                | Detection               | Response                | Status      |
| -------------------- | ---------------------- | ----------------------- | ----------------------- | ----------- |
| Position Drift       | Deviation > threshold  | PBMS background loop    | Telegram + PagerDuty    | IMPLEMENTED |
| Circuit Breaker Trip | Failure rate > 60%     | Per-venue state machine | PagerDuty P1 + Telegram | IMPLEMENTED |
| Kill Switch          | Manual or automatic    | Execution-service       | PagerDuty P1 + Telegram | IMPLEMENTED |
| Unhedged Position    | Multi-leg partial fill | Compensation handler    | PagerDuty P1 + Telegram | IMPLEMENTED |
| Dual Failure         | Recon + exec both down | PBMS health check       | PagerDuty P1 + Telegram | PLANNED     |
| Margin Emergency     | HF < 1.0               | PBMS margin monitor     | PagerDuty P1 + Telegram | IMPLEMENTED |

---

## Alert Flow Architecture

```
Event Sources (execution-service, PBMS, strategy-service, etc.)
  |
  |-- log_event("EVENT_NAME", severity="...", details={...})
  |
  v
Pub/Sub topic: lifecycle-events
  |
  v
alerting-service (subscriber)
  |
  |-- Deduplication (60s TTL, same event+details hash)
  |-- Route: match event_pattern against routing rules (first match wins)
  |-- Deliver to matched channels:
  |     |
  |     +-- Telegram (HTML format, bot API)
  |     +-- PagerDuty (Events API v2, severity mapped)
  |
  |-- Persist AlertDeliveryRecord to GCS (audit trail)
  |
  v
Operator sees alert in Telegram / PagerDuty on-call
```

---

## Configuration

| Parameter             | Default        | Description                        |
| --------------------- | -------------- | ---------------------------------- |
| Telegram bot token    | Secret Manager | Primary alert channel              |
| Telegram chat ID      | Secret Manager | Target chat for alerts             |
| PagerDuty routing key | Secret Manager | For critical trading events        |
| Alert dedup TTL       | 60s            | Suppress duplicate events          |
| OOM kill threshold    | 5              | OOM patterns before VM termination |
| Startup timeout       | 300s           | Seconds before startup timeout     |

---

## Related

- `04-architecture/autonomous-recovery-matrix.md` — full decision tree for failure scenarios
- `04-architecture/kill-switch-circuit-breaker.md` — kill switch and circuit breaker mechanics
- `03-observability/lifecycle-events.md` — mandatory event sequences
- `03-observability/coordination-events.md` — service-to-service event wiring
