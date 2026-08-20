---
doc_type: plan
title: Client artefact remediation (Nick AI) — finalize
summary: >-
  Gated finalize companion for client_artefact_remediation_nickai_2026_08_18.md. Verifies each claimed edit against
  the live HTML, reconciles finding status back into the audit reports, and archives the parent once done.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [admin, engineer]
tags: [client-disclosure, nick-ai, artifact-remediation, finalize]
related:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/active/client_artefact_remediation_nickai_2026_08_18.md,
    /plans/audit/results/client_artefact_live_regrade_2026_08_18.md,
  ]
created: 2026-08-18
last_updated: "2026-08-19"
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
depends_on: [client_artefact_remediation_nickai_2026_08_18]
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
context_scope:
  [
    /plans/active/client_artefact_remediation_nickai_2026_08_18.md,
    /plans/audit/results/client_artefact_live_regrade_2026_08_18.md,
  ]
---

# Client artefact remediation (Nick AI) — finalize

Gated on [`client_artefact_remediation_nickai_2026_08_18.md`](/plans/active/client_artefact_remediation_nickai_2026_08_18.md).

- [ ] [REVIEW] P1. **Verify every claimed edit against the live HTML** — open the file, do not trust checkbox text.
- [x] [REVIEW] P1. ✅ **Confirm zero `live` badges remain**, and that the §2/§3 rewrite states the TRADE-only-live /
      10-of-11-types-501 reality plainly rather than burying it. **Verified against live HTML 2026-08-19: `class="st st-live"` appears only in the CSS rule (`.st-live {`) + 2 legend entries — zero section badges; §2/§3 names "only the TRADE action is live end-to-end" + "the other 10 action types return HTTP 501" plainly.**
- [x] [REVIEW] P1. ✅ **Confirm the forward claim is gone**, not merely softened. **Verified 2026-08-19 against live HTML: zero hits for "remainder of this year" / "remainder of the year" / "remainder" / "this year" / "strategies on the current plan" — cut, not softened. The lone "most venues" match (line 9200) is the unrelated manual-trade disaster-path statement, not a forward claim.**
- [ ] [REVIEW] P1. **Reconcile finding status** back into the audit reports' summary tables, open → resolved.
- [ ] [DOC] P2. **Archive the parent plan** once every todo above is done — standard 6-step ritual.

## Progress Log

**2026-08-18 — authored** alongside the Nick AI remediation child.

**context-scout 2026-08-19**: populated context_scope (2 entries) — added the live-regrade audit report this
finalize's "confirm zero live badges" todo verifies against; source-path hunt skipped (finalize gate).
