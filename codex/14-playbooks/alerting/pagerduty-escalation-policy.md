---
scope: [engineer, operator, on-call]
---

# PagerDuty escalation policy

## Why

Live trading runs continuously. When an alerting-rule fires that requires human action (data-correctness break, kill-
switch armed, in-flight cloud switch fail, T+1 audit discrepancy beyond tolerance), the right escalation path turns a
3am page into a fix in minutes. The wrong escalation path either pages the wrong person, or worse, skips paging
entirely. This doc names the workspace escalation policy.

## Severity tiers

| Severity | Examples                                                                                        | Routing                                          | Time-to-ack |
| -------- | ----------------------------------------------------------------------------------------------- | ------------------------------------------------ | ----------- |
| P0       | Kill-switch armed; data-correctness fail blocking live trades; cloud switch validation failure  | Telegram `live-defi` group + PagerDuty primary  | 5 min       |
| P1       | T+1 audit discrepancy beyond tolerance; instruments-live preflight repeatedly failing           | Telegram `live-defi` group + PagerDuty primary  | 15 min      |
| P2       | Per-shard missing data > threshold; ML model staleness; non-critical kill-switch flag          | Telegram `live-defi` group only                  | 1 hour      |
| P3       | Coverage drop within ratchet tolerance; backfill VM auto-shutdown                               | Telegram `data-pipeline` group only             | informational|

## Escalation chain (P0 / P1)

```
0 min   alert fires → Telegram + PagerDuty primary
5 min   no ack → PagerDuty primary re-pages
10 min  no ack → PagerDuty secondary
20 min  no ack → PagerDuty tertiary + on-call manager
30 min  no ack → operator phone (Ikenna)
```

## On-call rotation

Primary / secondary / tertiary rotation lives in PagerDuty (synced from Google Calendar). Workspace rule: any change to
the rotation must update the calendar AND the PagerDuty service-level config — they are not auto-synced beyond the
weekly cron.

## Quiet-hours policy

There are no quiet hours for live trading. P0 / P1 page 24/7.

## Per-rule routing

Each alerting-service rule declares its severity in the rule definition. The rule-engine (alerting-service) routes per
this table — the rule body does not hand-roll Telegram or PagerDuty calls. Adding a new rule = pick its severity in the
rule config; the routing is automatic.

## Acknowledgement protocol

When paged, the on-call:

1. Acknowledges in PagerDuty within the SLA above (re-pages start otherwise).
2. Posts in Telegram `live-defi` with `Acked: <correlation_id>` so other operators see the page is being handled.
3. Investigates via deployment-UI events tab + the cited `correlation_id`.
4. Fixes or escalates within the time-to-resolve target.

## Cross-references

- Alert taxonomy: [`alert-code-taxonomy.md`](alert-code-taxonomy.md)
- Threshold tuning: [`threshold-tuning.md`](threshold-tuning.md)
- Live deployment monitoring (signal source):
  [`../../05-infrastructure/live-deployment-monitoring.md`](../../05-infrastructure/live-deployment-monitoring.md)
- Alerting batch-live (rule shape):
  [`../../04-architecture/alerting-batch-live.md`](../../04-architecture/alerting-batch-live.md)
- Operator playbook: [`operator-playbook.md`](operator-playbook.md)
