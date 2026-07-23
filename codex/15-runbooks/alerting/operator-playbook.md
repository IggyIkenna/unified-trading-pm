---
doc_type: codex-runbook
title: Alerting Operator Playbook
summary:
  Canonical per-AlertCode operator playbook — the doc on-call opens when paged; it gives what the code means, the
  immediate action (5-min-to-first-action), escalation tiers (primary → secondary → strategy lead → custody), which
  kill-switch to pull, and known false-positives. STUB (planned 2026-05-07) — per-code entries fill as Phase 1/2 ship.
status: current
nature: process
asset_group: [meta]
stage: [meta]
repos: [alerting-service, execution-service]
scope: [engineer, admin]
tags: [runbook, escalation, live-trading, monitoring, ui]
related:
  [
    /codex/15-runbooks/alerting/alert-code-taxonomy.md,
    /codex/15-runbooks/alerting/threshold-tuning.md,
    codex/14-customer-journeys/dart/,
  ]
created: 2026-05-07
owner: ikenna
cadence: on-demand
verifier: operator
last_executed:
code_refs:
authoritative_for:
  Per-AlertCode operator response — ack / escalate / kill-switch / runbook-link. The doc the on-call operator opens when
  their phone rings; tells them what to do for every code.
referenced_by: [plans/active/alerting_service_live_rules_2026_05_07.md]
---

# Alerting Operator Playbook

> **Status:** PLANNED — stub created 2026-05-07 to anchor forward-references from the alerting-service plan. Body to be
> filled in per-AlertCode as alerting-service Phase 1 + Phase 2 ship.

## Purpose

When an operator gets paged at 3am, they should not have to guess what to do. This doc tells them: which alert this is,
what it means, what the immediate action is, when to escalate, and which kill-switch (if any) to flip. One canonical
runbook per AlertCode.

## Scope

- Per-`AlertCode` response: ack / escalate / page next tier / pull kill-switch / no-op (acknowledge informational).
- Escalation tiers: primary on-call → secondary on-call → strategy lead → custody contact.
- Kill-switch references — execution-service per-archetype kill-switches; never invoked unless operator is convinced.
- Manual-override / DART references for trades the operator may need to manually unwind or block.
- Excluded: alert tuning (separate doc); rehearsal procedure (separate doc).

## Outline (planned sections)

1. **Acknowledgement protocol** — within N minutes, ack the page; auto-escalate if missed.
2. **Per-AlertCode runbook entries** — table or one-page-per-code:
   - `AlertCode`
   - **Means**: 1-line plain-English description.
   - **Immediate action**: numbered steps (5 minutes max to first action).
   - **Escalation criteria**: when does this become "wake the strategy lead?"
   - **Kill-switch**: which kill-switch button if any; what it does; when to pull it.
   - **Common false-positives**: known noise patterns; do NOT page-up for these.
   - **Reference**: linked codex docs / plan files / dashboards.
3. **Cross-cutting protocols** — how to read the events UI, how to find correlation_id, how to trace upstream.
4. **DART manual-trade gate** — for live trading, every manual override must go through DART; reference the playbook.
5. **Post-incident** — write-up template, pinned in the Slack channel within 24h of an incident.

## Cross-references

- **Plan(s) implementing this:**
  [`alerting_service_live_rules`](../../../plans/active/alerting_service_live_rules_2026_05_07.md).
- **Related codex SSOTs:** [`alert-code-taxonomy`](./alert-code-taxonomy.md),
  [`threshold-tuning`](./threshold-tuning.md), [DART playbook](../dart/).
- **Code:** alerting-service (TBD), DART manual-trade-gate UI.

## Open questions

- Who is the secondary on-call for the May-23 live launch? (need named person + timezone coverage)
- Do we want a "pre-flight" version of this doc that primary on-call reads before each shift?
- How do we ensure runbook entries don't drift from the actual system behaviour over time? (recommend: rehearsal
  procedure spot-checks the playbook entry per code each quarter)
