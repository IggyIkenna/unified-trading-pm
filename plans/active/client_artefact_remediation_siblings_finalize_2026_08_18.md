---
doc_type: plan
title: Client artefact remediation (siblings) — finalize
summary: >-
  Gated finalize companion for client_artefact_remediation_siblings_2026_08_18.md. Re-verifies each claimed fix
  against the live file, re-runs the banned-term sweep across all six artefacts, and archives the parent once done.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [admin, engineer]
tags: [client-disclosure, artifact-remediation, finalize]
related:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/active/client_artefact_remediation_siblings_2026_08_18.md,
    /plans/audit/results/client_artefact_sibling_docs_audit_2026_08_18.md,
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
depends_on: [client_artefact_remediation_siblings_2026_08_18]
gate_on_depends: true
sequential: true
locked_by:
locked_since:
resolved_by:
supersedes:
superseded_by:
source: >-
  Mandatory finalize companion per task_template.md §4 (operator ruling 2026-07-24) — every assigned_vm:planning
  plan with more than one todo needs a gated finalize plan that closes only its own plan.
context_scope: [/plans/active/client_artefact_remediation_siblings_2026_08_18.md]
---

# Client artefact remediation (siblings) — finalize

Gated on [`client_artefact_remediation_siblings_2026_08_18.md`](/plans/active/client_artefact_remediation_siblings_2026_08_18.md).
Do not start before then.

- [ ] [REVIEW] P0. **Re-run the banned-term sweep across ALL SIX artefacts and confirm zero hits** — including
      inside SVG `<text>` elements, which is where one of the original 6 hits hid. Open the files; do not trust the
      parent plan's checkboxes.
- [ ] [REVIEW] P1. **Verify each claimed fix against the live file**, then update the corresponding finding's
      status in [the sibling-docs audit](/plans/audit/results/client_artefact_sibling_docs_audit_2026_08_18.md)
      from open to resolved.
- [ ] [DOC] P2. **Archive the parent plan** once every todo above is done — standard 6-step ritual (status →
      `archived`, `git mv` into the dated archive folder, corpus-wide referrer-path fixup, verify no broken links,
      confirm line caps still hold).

## Progress Log

**2026-08-18 — authored** alongside the sibling remediation child, per the mandatory finalize-companion rule.
