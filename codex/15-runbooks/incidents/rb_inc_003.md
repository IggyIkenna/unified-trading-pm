---
title: "RB-INC-003 — Audit Acknowledgement Handling"
scope: [admin, engineer]
owner: ikenna@odum-research.com
cadence: Weekly review
verifier: Ack-queue audit
last_executed: never
authoritative_for:
  - "RB-INC-003 operator runbook"
referenced_by:
  - codex/04-architecture/incident-gateway-state-machine.md
  - codex/04-architecture/recovery-defence-in-depth-layers.md
  - plans/active/incident_runbooks_and_evidence_store_2026_05_23.md
related:
  - codex/15-runbooks/incidents/README.md
  - codex/15-runbooks/alerting/audit-acknowledgement-flow.md
---

# RB-INC-003 — Audit Acknowledgement Handling

> **What this is:** the on-call operator's first stop when this incident class fires. Read top-to-bottom on the page
> that comes up. First 60 seconds at the top; post-mortem at the bottom.

## TL;DR

Incident has reached AUDIT_REPORT_GENERATED and is in the audit-ack queue with countdown.

Category: **Core** · Runbook ID: **RB-INC-003**.

## First 60 seconds — acknowledge + scope

1. Open DART → Safety Ops tab → Audit-Ack Queue panel.
2. Sort by audit_ack_due_at ascending (due-soon first).
3. Open the incident's AuditReport link.

## Diagnose

- Review the IncidentEvidence bundle (config_hash + code_version + runbook_version + 11 optional URL fields).
- Review the AgentActionEvent rows for the incident — did Layer-0 do the right thing?
- Review the LLM RecoveryAuditSignoff verdict + narrative.
- Check if the incident matches a pattern from operator-flagged false-positives.

## Resolve

- If satisfied: click Audit Ack button. Incident transitions to HUMAN_AUDIT_ACKED → RESOLVED → CLOSED.
- If the report is INSUFFICIENT: click 'Request more evidence' which fires evidence_collector again + extends
  audit_ack_due_at.
- If you DISPUTE the automated action: file an issue doc in plans/active/issues/ + escalate to operator chat.

## Rollback

Audit ack is one-way — once acked, incident closes. To reopen, file a new incident referencing the closed one.

## Escalate

SLA breach: secondary at default_seconds, founder at founder_after_seconds (see SLA matrix).

## Success criteria

Audit-ack queue size <= 5 entries pending.

## Post-incident

If multiple incidents share a pattern, file a remediation plan in plans/active/.

## Related

- `codex/15-runbooks/incidents/README.md` — runbook index
- `codex/04-architecture/incident-gateway-state-machine.md` — state machine + dedup-key + audit-ack queue
- `codex/04-architecture/recovery-defence-in-depth-layers.md` — 5+1 layer recovery model
- `codex/15-runbooks/alerting/audit-acknowledgement-flow.md` — 6h ack SLA + escalation ladder
