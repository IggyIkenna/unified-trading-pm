---
doc_type: plan
title: W15 venue-adaptor security audit — finalize
summary: >-
  Gated finalize for w15_execution_service_venue_adaptor_security_audit_2026_08_20 — confirm every CRITICAL/HIGH
  finding resolved (not just recorded), reconcile evidence back to the epic and T4 plan, archive once done.
status: active
nature: process
asset_group: [cross-cutting]
stage: [execution]
repos: [execution-service, unified-trading-pm]
scope: [engineer]
tags: [execution, security, audit, w15, finalize]
related:
  [
    /plans/active/w15_execution_service_venue_adaptor_security_audit_2026_08_20.md,
    /plans/epics/system_readiness_master.md,
    /plans/active/code_readiness_t4_execution_settlement_2026_08_19.md,
  ]
created: 2026-08-20
last_updated: 2026-08-20
parent_epic: system_readiness_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 1
assigned_role: backend_engineer
effort: max
drift_direction: advance-code
depends_on: [w15_execution_service_venue_adaptor_security_audit_2026_08_20]
gate_on_depends: true
supersedes:
superseded_by:
locked_by:
locked_since:
sequential: true
source: Mandatory companion finalize per task_template.md's AO-plan rule (operator ruling 2026-07-24).
context_scope:
  [
    /plans/active/w15_execution_service_venue_adaptor_security_audit_2026_08_20.md,
    /plans/epics/system_readiness_master.md,
  ]
---

# W15 venue-adaptor security audit — finalize

## Todos

- [ ] [AGENT] P0. Re-verify the triage todo's own claim: independently re-check that every CRITICAL/HIGH finding
      recorded across `w15_execution_service_venue_adaptor_security_audit_2026_08_20.md`'s phase todos resolves
      to either a landed fix (the cited sha genuinely exists and is an ancestor of `origin/live-defi-rollout`) or
      a real tracked follow-up (the cited todo/issue-doc slug genuinely exists and is open) — do not trust the
      triage todo's own "done" claim without this independent check, same discipline as any other evidence-
      backed completion claim in this workspace.
- [ ] [AGENT] P0. Reconcile every completed todo's evidence back to the epic's `## W15` section
      (`/plans/epics/system_readiness_master.md`) and to
      `/plans/active/code_readiness_t4_execution_settlement_2026_08_19.md`'s own security-audit todo — both
      should point here as the real dispatch surface, not carry duplicate detail.
- [ ] [AGENT] P0. Run the standard 6-step archival ritual on
      `w15_execution_service_venue_adaptor_security_audit_2026_08_20.md` once every one of its own todos is `[x]`
      or correctly re-scoped, including the corpus-wide referrer-path fixup.
