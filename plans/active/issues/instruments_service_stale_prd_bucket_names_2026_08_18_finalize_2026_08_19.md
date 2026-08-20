---
doc_type: issue
title: Finalize — instruments-service stale -prd- bucket names (2026-08-19)
summary: >-
  Gated finalize for `instruments_service_stale_prd_bucket_names_2026_08_18.md`'s RECLASSIFY whole-doc flip
  (na-eligibility-audit, cross-cutting tranche, 2026-08-19). Verifies both todos (per-file bucket verification +
  fix, CLI-docstring fix) land with real evidence, then considers archival.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ao-dispatch, close-out, finalize, na-eligibility-audit]
related:
  [
    /plans/active/issues/instruments_service_stale_prd_bucket_names_2026_08_18.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-19"
last_updated: "2026-08-20"
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.15
assigned_role: review
effort: low
resolved_by:
drift_direction: none
depends_on: [instruments_service_stale_prd_bucket_names_2026_08_18]
gate_on_depends: true
sequential: true
context_scope:
  [
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /plans/active/issues/instruments_service_stale_prd_bucket_names_2026_08_18.md,
  ]
supersedes:
superseded_by:
locked_by:
locked_since:
source: >-
  Paired finalize for instruments_service_stale_prd_bucket_names_2026_08_18.md's na-eligibility-audit RECLASSIFY
  whole-doc flip (dispatch agt-dc3dbe, slot 30, 2026-08-19).
---

# Finalize — instruments-service stale -prd- bucket names

- [ ] [REVIEW] P3. Once both todos in `instruments_service_stale_prd_bucket_names_2026_08_18.md` land, verify each
      cites a real, reachable commit. Archive the source doc via the 6-step ritual once both are verified done and
      no further follow-up is warranted.

## Progress Log

- **2026-08-19**: drafted alongside the na-eligibility-audit whole-doc RECLASSIFY flip (dispatch agt-dc3dbe, slot
  30, cross-cutting tranche).
- **context-scout 2026-08-20**: populated context_scope (3 entries).
