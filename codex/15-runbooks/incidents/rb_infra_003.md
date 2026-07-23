---
doc_type: codex-runbook
title: RB-INFRA-003 — Secret/Config Failure
summary:
  Operator runbook for Secret Manager access / config-registry 5xx failure — wait if transient, re-sync rotated
  credentials, fix SA permissions; enter_readonly_recon_mode on affected services, trading creds unreachable escalates
  to SEV0 kill-switch.
status: current
nature: process
asset_group: [meta]
stage: [meta]
repos: []
scope: [admin, engineer]
tags: [runbook, incident, infrastructure, secrets, config, kill-switch]
related: [/codex/15-runbooks/incidents/README.md, /codex/15-runbooks/alerting/audit-acknowledgement-flow.md]
created: 2026-05-23
owner: ikenna@odum-research.com
cadence: Monthly + post-credential-rotation
verifier: SM access smoke test
last_executed: never
code_refs:
authoritative_for: [RB-INFRA-003 operator runbook]
referenced_by:
  [
    /codex/04-architecture/incident-gateway-state-machine.md,
    /codex/04-architecture/recovery-defence-in-depth-layers.md,
    plans/active/incident_runbooks_and_evidence_store_2026_05_23.md,
  ]
---

# RB-INFRA-003 — Secret/Config Failure

> **What this is:** the on-call operator's first stop when this incident class fires. Read top-to-bottom on the page
> that comes up. First 60 seconds at the top; post-mortem at the bottom.

## TL;DR

Secret Manager access fails / config registry returns 5xx.

Category: **Infrastructure** · Runbook ID: **RB-INFRA-003**.

## First 60 seconds — acknowledge + scope

1. Identify which secret / config.
2. Check whether services are running on cached values.

## Diagnose

- GCP / AWS SM availability.
- Service account permissions.
- Credential rotation timing.

## Resolve

- Wait for SM recovery if transient.
- If credential rotated: re-sync to all services that consume.
- If SA permissions wrong: fix + redeploy.

## Rollback

Production config unknown → enter_readonly_recon_mode on affected services.

## Escalate

Trading credentials unreachable → SEV0 (kill switch).

## Success criteria

SM responsive + all services reading correct values.

## Post-incident

Document the credential rotation in the SM rotation log.

## Related

- `/codex/15-runbooks/incidents/README.md` — runbook index
- `/codex/04-architecture/incident-gateway-state-machine.md` — state machine + dedup-key + audit-ack queue
- `/codex/04-architecture/recovery-defence-in-depth-layers.md` — 5+1 layer recovery model
- `/codex/15-runbooks/alerting/audit-acknowledgement-flow.md` — 6h ack SLA + escalation ladder
