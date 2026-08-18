---
doc_type: plan
title: Client artefact remediation — finalize
summary: >-
  Gated finalize companion for client_artefact_remediation_2026_08_18.md. Reconciles completed-todo evidence back
  into the audit report and the two owning artefact plans, re-checks whether any deferred system-gap gate has since
  cleared, and archives the parent plan once fully done.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [admin, engineer]
tags: [client-disclosure, nick-ai, elysium, artifact-remediation, finalize]
related:
  [
    /plans/active/client_artefact_remediation_2026_08_18.md,
    /plans/audit/results/nick_ai_and_elysium_artefact_audit_2026_08_18.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-18
last_updated: "2026-08-18"
parent_epic: system_readiness_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: infra
effort: high
drift_direction: none
depends_on: [client_artefact_remediation_2026_08_18]
gate_on_depends: true
sequential: true
locked_by:
locked_since:
resolved_by:
supersedes:
superseded_by:
source: >-
  Mandatory finalize companion per task_template.md §4 (operator ruling 2026-07-24) — every assigned_vm:planning
  plan with more than one todo needs a gated finalize plan.
context_scope:
  [
    /plans/active/client_artefact_remediation_2026_08_18.md,
    /plans/audit/results/nick_ai_and_elysium_artefact_audit_2026_08_18.md,
  ]
---

# Client artefact remediation — finalize

Gated on [`client_artefact_remediation_2026_08_18.md`](/plans/active/client_artefact_remediation_2026_08_18.md)
being fully done. Do not start before then.

- [ ] [REVIEW] P1. **Reconcile completed-todo evidence back into source docs.** For every checked todo in the
      parent plan, re-verify the cited HTML section/commit actually reflects the claimed edit (open the live file,
      don't trust the checkbox text alone) and update the corresponding finding's status in
      [`nick_ai_and_elysium_artefact_audit_2026_08_18.md`](/plans/audit/results/nick_ai_and_elysium_artefact_audit_2026_08_18.md)'s
      summary table from open to resolved. Also check whether either owning artefact plan
      ([`nick_ai_platform_disclosure_artifact_2026_08_16.md`](/plans/active/nick_ai_platform_disclosure_artifact_2026_08_16.md),
      [`elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md`](/plans/active/elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md))
      needs its own Progress Log updated to reflect that this remediation pass ran.
- [ ] [REVIEW] P1. **Re-check every item in the parent plan's "Real system gaps — already tracked, not duplicated
      here" section.** If transfer-handler wiring, capital-budget enforcement, dynamic-universe pinning, or any of
      `system_readiness_master.md` W5/W10/W12/W13/W16/W17/W18 has landed since this plan was authored, the
      corresponding artefact content can move from target-state framing to a present-deep claim — spin that into a
      new tracked todo (a new small plan or an addition here) rather than leaving the artefact under-claiming a now-
      real capability.
- [ ] [DOC] P2. **Archive the parent plan** once every todo above is done — standard 6-step ritual (status →
      `archived`, `git mv` into the dated archive folder, exact-successor banner if applicable, corpus-wide
      referrer-path fixup, verify no broken links, confirm line caps still hold).

## Progress Log

**2026-08-18 — authored** alongside the parent plan, per task_template.md §4's mandatory finalize-companion rule.
