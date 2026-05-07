---
title: Alerting Playbook — Index
status: planned
created: 2026-05-07
authoritative_for: Index of the alerting-service playbook docs — alert taxonomy, operator response, threshold tuning, rehearsal procedure. Anchors every other alerting doc in this directory.
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
breaches, fill-quality drift, risk-limit approaches) into pages. This directory is the SSOT for what alerts exist,
what an operator does about each, how thresholds are set, and how we verify the whole chain works.

## Sub-documents

1. [`alert-code-taxonomy.md`](./alert-code-taxonomy.md) — UAC `AlertCode` StrEnum SSOT. Every alert has a stable code
   that operator runbooks reference.
2. [`operator-playbook.md`](./operator-playbook.md) — per-AlertCode operator response: ack / escalate / kill-switch /
   runbook-link.
3. [`threshold-tuning.md`](./threshold-tuning.md) — how thresholds are set, who owns, when they get reviewed.
4. [`rehearsal-procedure.md`](./rehearsal-procedure.md) — quarterly alert-rehearsal procedure to verify paging works
   end-to-end.

## Cross-references

- **Plan(s) implementing this:** [`alerting_service_live_rules`](../../../plans/active/alerting_service_live_rules_2026_05_07.plan.md).
- **Related codex SSOTs:** [`live-deployment-monitoring`](../../05-infrastructure/live-deployment-monitoring.md), [DART playbook](../dart/).
- **Code:** `alerting-service/` (TBD).

## Reading order

For new operators: `operator-playbook.md` first (you'll get paged), then `alert-code-taxonomy.md` (the codes you'll
see), then `threshold-tuning.md` (when thresholds need changing), then `rehearsal-procedure.md` (you'll be on the
quarterly rotation).

For service authors adding a new alert: `alert-code-taxonomy.md` first (register the new code), then
`threshold-tuning.md` (set the threshold + owner), then `operator-playbook.md` (write the response runbook), then
`rehearsal-procedure.md` (add it to the next quarterly rehearsal scope).
