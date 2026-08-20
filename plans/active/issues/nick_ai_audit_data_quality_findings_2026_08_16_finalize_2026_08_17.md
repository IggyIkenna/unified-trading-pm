---
doc_type: issue
title: nick_ai_audit_data_quality_findings — finalize (na-eligibility-audit reclassification close-out)
summary: >-
  Gated closeout for the 2026-08-17 na-eligibility-audit whole-doc RECLASSIFY of
  nick_ai_audit_data_quality_findings_2026_08_16.md (assigned_vm NA -> planning). Machine-held via depends_on +
  gate_on_depends until all 4 findings in that doc are done. Verifies each finding's fix, checks for zero
  open-todos, and runs the standard 6-step archival ritual once true.
status: open
nature: issue
asset_group: [sports, tradfi, prediction]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [tradfi, ao-dispatch, close-out, finalize, na-eligibility-audit, reclassification]
related:
  [
    /plans/active/issues/nick_ai_audit_data_quality_findings_2026_08_16.md,
    /plans/active/nick_ai_platform_disclosure_artifact_2026_08_16.md,
  ]
created: "2026-08-17"
last_updated: "2026-08-20"
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: review
effort: low
drift_direction: advance-code
depends_on: [nick_ai_audit_data_quality_findings_2026_08_16]
gate_on_depends: true
sequential: true
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
context_scope:
  [
    /plans/active/issues/nick_ai_audit_data_quality_findings_2026_08_16.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
source: >-
  Drafted alongside the 2026-08-17 na-eligibility-audit tradfi-tranche whole-doc RECLASSIFY of
  nick_ai_audit_data_quality_findings_2026_08_16.md (dispatch agt-d99b5c).
---

# nick_ai_audit_data_quality_findings — finalize

> Machine-held (`depends_on` + `gate_on_depends: true`) until every finding in
> `nick_ai_audit_data_quality_findings_2026_08_16.md` is done.

## Todos

- [ ] [REVIEW] P1. **Verify each of the 4 findings' fix landed with real evidence** (commit SHA resolves, a test or
      a live check proves the fix, not just the worker's own claim) — do not trust a checkbox's own copy of the
      evidence line without re-checking the cited commit/SHA exists. Findings: (1) sports FOOTBALL venue
      write-path column-swap fix, (2) tradfi tbbo/yield_curve SchemaContract registration, (3) prediction
      market_lifecycle zero-rows investigation outcome, (4) sports KALSHI classification outcome.
- [ ] [REVIEW] P2. **Check whether the source doc now has zero open todos.** If so, run the standard 6-step
      archival ritual on `nick_ai_audit_data_quality_findings_2026_08_16.md` (`doc_type: issue` → flat
      `plans/archive/issues/` per `issue-doc-lifecycle.md`), including the corpus-wide referrer-path fixup.
- [ ] [DOC] P1. **Run the standard 6-step archival ritual on this finalize plan itself** once the above is
      confirmed complete.

## Progress Log

- **na-eligibility-audit 2026-08-17** (tradfi tranche, dispatch agt-d99b5c): drafted alongside the whole-doc
  RECLASSIFY, gated on its completion per the AO-dispatched finalize-plan-coverage rule.
- **context-scout 2026-08-17**: refreshed context_scope (2 entries).
- **context-scout 2026-08-20**: refreshed context_scope (2 entries).
