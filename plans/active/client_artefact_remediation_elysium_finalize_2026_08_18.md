---
doc_type: plan
title: Client artefact remediation (Elysium) — finalize
summary: >-
  Gated finalize companion for client_artefact_remediation_elysium_2026_08_18.md. Verifies each claimed edit against
  the live HTML, reconciles finding status back into the audit reports, and archives the parent once done.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [admin, engineer]
tags: [client-disclosure, elysium, artifact-remediation, finalize]
related:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/active/client_artefact_remediation_elysium_2026_08_18.md,
    /plans/audit/results/nick_ai_and_elysium_artefact_audit_2026_08_18.md,
  ]
created: 2026-08-18
last_updated: "2026-08-18"
parent_epic: system_readiness_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: infra
effort: high
drift_direction: none
depends_on: [client_artefact_remediation_elysium_2026_08_18]
gate_on_depends: true
sequential: true
locked_by:
locked_since:
resolved_by:
supersedes:
superseded_by:
source: >-
  Mandatory finalize companion per task_template.md §4 (operator ruling 2026-07-24) — a finalize plan closes only
  its own plan.
context_scope: [/plans/active/client_artefact_remediation_elysium_2026_08_18.md]
---

# Client artefact remediation (Elysium) — finalize

Gated on [`client_artefact_remediation_elysium_2026_08_18.md`](/plans/active/client_artefact_remediation_elysium_2026_08_18.md).

- [ ] [REVIEW] P1. **Verify every claimed edit against the live HTML** — open the file, do not trust checkbox text.
      Confirm specifically that the `SigningSurface` list was NOT edited (only annotated), since the original audit
      finding there was a false positive and "fixing" it would make the document wrong.
- [ ] [REVIEW] P1. **Confirm zero `live` badges remain** in this file, and that each downgraded section reads
      coherently rather than just having its pill swapped.
- [ ] [REVIEW] P1. **Reconcile finding status** back into the audit reports' summary tables, open → resolved.
- [ ] [DOC] P2. **Archive the parent plan** once every todo above is done — standard 6-step ritual.

## Progress Log

**2026-08-18 — authored** alongside the Elysium remediation child.
