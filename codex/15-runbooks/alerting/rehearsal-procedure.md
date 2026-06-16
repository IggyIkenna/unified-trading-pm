---
scope: [engineer, admin]
title: Alerting Rehearsal Procedure
status: planned
created: 2026-05-07
authoritative_for:
  Quarterly alert-rehearsal procedure to verify paging works end-to-end. Synthetic events injected through the
  alerting-service must produce a real PagerDuty/phone page within SLA, and the on-call must follow the
  operator-playbook entry to the documented action.
referenced_by:
  - plans/active/alerting_service_live_rules_2026_05_07.md
related:
  - codex/15-runbooks/alerting/alert-code-taxonomy.md
  - codex/15-runbooks/alerting/operator-playbook.md
  - codex/15-runbooks/alerting/threshold-tuning.md
---

# Alerting Rehearsal Procedure

> **Status:** PLANNED — stub created 2026-05-07 to anchor forward-references from the alerting-service plan. Body to be
> filled in as the first rehearsal cycle is run (target: pre-launch dry-run before May-23).

## Purpose

An alerting system is not "real" until it has paged a human end-to-end. This doc defines the quarterly drill that
verifies (a) synthetic events trigger the right AlertCode, (b) the right severity routing fires the right notification
channel, (c) the on-call ack happens within SLA, (d) the operator follows the playbook entry, (e) the post-incident
write-up flow works.

## Scope

- Quarterly rehearsal across all live AlertCodes (rotating subset per quarter to avoid full-spectrum every time).
- Synthetic event injection (test fixtures + a dedicated `/alerting/rehearsal/inject` admin endpoint).
- On-call participation — the rotation rehearsal targets the human currently on-call.
- Excluded: load testing (separate operational concern); scheduled maintenance windows (different runbook).

## Outline (planned sections)

1. **Quarterly cadence** — first Monday of each quarter; full subset of AlertCodes covered every 4 quarters.
2. **Pre-rehearsal prep** — operator notified the day before; "this is a drill" disclaimer in the synthetic alert body;
   rollback plan if injection misbehaves.
3. **Injection mechanics** — dedicated admin-only endpoint emits synthetic event with a `rehearsal=true` tag carried
   through to the page so live ops dashboards distinguish drill from real.
4. **Per-code drill steps** — for each code in scope: inject → observe routing → time-to-ack → operator follows playbook
   → record outcomes.
5. **Pass/fail criteria** — page received within N minutes; ack within M minutes; operator action matches playbook; no
   spurious side-effects (real kill-switch not pulled accidentally).
6. **Post-rehearsal** — gaps logged: missed pages, threshold mis-tunings revealed, playbook entry corrections; owner
   assigned per gap; remediation due before next rehearsal.
7. **First rehearsal targets** — pre-May-23 dry-run scope: heartbeat-miss, risk-limit-approach, kill-switch-flipped,
   custody-balance-gap.

## Cross-references

- **Plan(s) implementing this:**
  [`alerting_service_live_rules`](../../../plans/active/alerting_service_live_rules_2026_05_07.md).
- **Related codex SSOTs:** [`alert-code-taxonomy`](./alert-code-taxonomy.md),
  [`operator-playbook`](./operator-playbook.md), [`threshold-tuning`](./threshold-tuning.md).
- **Code:** alerting-service rehearsal endpoint (TBD).

## Open questions

- Do we test the actual phone-page channel, or is PagerDuty's own delivery test sufficient? (recommend: real phone page
  once per quarter; PagerDuty internal test the other quarters)
- How do we ensure rehearsals don't drift into "operator memorises the drill scenario" rather than genuinely exercising
  the system? (recommend: rotate which codes get drilled per quarter; keep the schedule unpublished within each quarter)
- Who owns the rehearsal write-up — primary on-call or designated rehearsal coordinator?
