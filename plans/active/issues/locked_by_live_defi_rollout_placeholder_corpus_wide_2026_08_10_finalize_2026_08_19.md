---
doc_type: issue
title: Finalize — locked_by live-defi-rollout placeholder-source bug hunt (2026-08-19)
summary: >-
  Gated finalize for `locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10.md`'s RECLASSIFY whole-doc flip
  (na-eligibility-audit, cross-cutting tranche, 2026-08-19), scoped ONLY to the remaining item (find + patch the
  doc-creation source still stamping the placeholder on new docs). Does not touch the doc's separate, already-closed
  corpus-wide UNLOCK action (operator-gated, HARD-STOP, resolved 2026-08-12/18).
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ao-dispatch, close-out, finalize, na-eligibility-audit, locked_by]
related:
  [
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-19"
last_updated: "2026-08-19"
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.25
assigned_role: review
effort: low
resolved_by:
drift_direction: none
depends_on: [locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10]
gate_on_depends: true
sequential: true
context_scope:
  [
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /plans/archive/issues/locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10.md,
  ]
supersedes:
superseded_by:
locked_by:
locked_since:
source: >-
  Paired finalize for locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10.md's na-eligibility-audit
  RECLASSIFY whole-doc flip (dispatch agt-dc3dbe, slot 30, 2026-08-19).
---

# Finalize — locked_by live-defi-rollout placeholder-source bug hunt

- [ ] [REVIEW] P3. Once the remaining item in `locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10.md`
      lands (the doc-creation source patched, verified via a fresh-doc creation + repeat grep showing zero NEW
      hits), verify the citation is a real, reachable commit. The source doc likely still has 0 open todos at that
      point — do NOT archive it without independently re-checking `locked_by:`/`locked_since:` are actually clear
      on this specific doc first (it is itself part of the corpus this bug touches).

## Progress Log

- **2026-08-19**: drafted alongside the na-eligibility-audit whole-doc RECLASSIFY flip (dispatch agt-dc3dbe, slot
  30, cross-cutting tranche).
- **context-scout 2026-08-20**: populated/refreshed context_scope (3 entries)
