---
scope: [engineer]
---

# PagerDuty escalation policy

> **Severity vocabulary SSOT** — see [`README.md` § Severity glossary](README.md#severity-glossary) for the canonical
> mapping between the UAC `AlertSeverity` codex enum and PagerDuty incident priorities. This doc owns the _operational_
> escalation chain (timing, on-call rotation, ack protocol, P0 vs P1 sub-distinction within `CRITICAL`); the glossary
> owns the codex-enum ↔ P-tier ↔ routing mapping.

## Why

Live trading runs continuously. When an alerting-rule fires that requires human action (data-correctness break, kill-
switch armed, in-flight cloud switch fail, T+1 audit discrepancy beyond tolerance), the right escalation path turns a
3am page into a fix in minutes. The wrong escalation path either pages the wrong person, or worse, skips paging
entirely. This doc names the workspace escalation policy.

## Severity tiers

The codex-enum / PagerDuty-priority / routing / examples mapping lives in the glossary
([`README.md` § Severity glossary](README.md#severity-glossary)). This section captures only the operational
sub-distinction _inside_ the `CRITICAL` row that the escalation chain below depends on:

- **P0** (`AlertSeverity.CRITICAL`, kill-switch / data-correctness / cloud-switch family) — 5-min ack target.
- **P1** (`AlertSeverity.CRITICAL`, T+1 audit / instruments-live preflight / non-kill-switch CRITICAL family) — 15-min
  ack target.
- **P2** (`AlertSeverity.HIGH`) — 1-hour ack target.
- **P3** (`AlertSeverity.WARN`) — informational; no ack SLA.

`AlertSeverity.INFO` does not enter the PagerDuty escalation chain (Telegram `data-pipeline` group only). See the
glossary for the full set of routing examples per tier.

## Escalation chain (P0 / P1)

```
0 min   alert fires → Telegram + PagerDuty primary
5 min   no ack → PagerDuty primary re-pages
10 min  no ack → PagerDuty secondary
20 min  no ack → PagerDuty tertiary + on-call manager
30 min  no ack → operator phone (Ikenna)
```

## On-call rotation

**May-23 cutover rotation** (operator decision 2026-05-12; AL-14 RESOLVED):

| Operator             | Shift (UK time)  | Coverage                             |
| -------------------- | ---------------- | ------------------------------------ |
| **Ikenna** (primary) | 14:30 → 02:30 UK | Afternoon + evening + early-night    |
| **Harsh** (primary)  | 02:30 → 14:30 UK | Late-night + early-morning + morning |

**Shape**: 2-operator 12-hour split, fully-automated alert-checking workflow (no synchronous human reasoning loop —
operator just verifies the alert + acks). No tertiary tier required because the workflow is automated; the 30-min
"operator phone (Ikenna)" fallback in the escalation chain above still applies as final tier.

**Calendar source**: rotation lives in PagerDuty (synced from Google Calendar). Workspace rule: any change to the
rotation must update the calendar AND the PagerDuty service-level config — they are not auto-synced beyond the weekly
cron.

**Cross-cycle changes**: if either operator goes off-rotation (vacation / sickness / cycle handoff), the other covers
24h until the calendar update lands. No secondary/tertiary named operators today; if cutover scope expands to 3+
operators post-cutover (see `observability_master.md`), this section gets a named-tier table.

## Quiet-hours policy

There are no quiet hours for live trading. P0 / P1 page 24/7. The 12-hour split above means each operator carries the
night-shift half the time.

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
