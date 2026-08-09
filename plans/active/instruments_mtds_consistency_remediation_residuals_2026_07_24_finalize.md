---
doc_type: plan
title: Instruments <-> MTDS F1-N9 consistency remediation residuals — finalize
summary:
  Gated finalize companion for instruments_mtds_consistency_remediation_residuals_2026_07_24.md (operator ruling
  2026-07-24 requirement) — reconciles N5r/N6r + N1b evidence back into the source doc once both land, then runs the
  6-step archival ritual once the source doc has zero open todos.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [finalize, archival, instruments, mtds, manifest]
related: [instruments_mtds_consistency_remediation_residuals_2026_07_24]
created: "2026-08-09"
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.1
assigned_role: data_engineering
effort: medium
drift_direction: none
depends_on: [instruments_mtds_consistency_remediation_residuals_2026_07_24]
gate_on_depends: true
sequential: true
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Authored 2026-08-09 to satisfy task_template.md's "every AO-dispatched plan needs a gated finalize plan" rule
  (operator ruling 2026-07-24) — the source doc was reclassified assigned_vm: NA -> planning this same session once the
  operator ruled on its two remaining operator-gated items (N5r/N6r, N1b), and the finalize-plan-coverage QG gate
  correctly caught the missing companion before commit.
context_scope:
  [
    /plans/active/instruments_mtds_consistency_remediation_residuals_2026_07_24.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/active/task_template.md,
  ]
last_updated: "2026-08-09"
---

# Instruments <-> MTDS F1-N9 consistency remediation residuals — finalize

## Todos

- [ ] [REVIEW] P2. Once both of the source doc's remaining todos (N5r/N6r DeFi manifest rebuild-for-real-replace, N1b
      CEFI ~698k-row reclassify) are done, reconcile their evidence back into
      `instruments_mtds_consistency_remediation_residuals_2026_07_24.md`'s own checkboxes — re-verify the cited
      commit/manifest-state exists, don't trust a copied evidence line. Also re-check N1b's Step-4 enumerator dependency
      (flagged as unverified at ruling time) actually cleared before treating it as done.
- [ ] [DOC] P2. Once the source doc shows zero open todos, run the standard 6-step archival ritual on it
      (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`) — migrate any deferred item, banner,
      codex-alignment check, corpus-wide referrer fixup, then `git mv` to `plans/archive/<YYYY_MM>/`. Distinct
      `[TAG]`/priority from the REVIEW todo above (per task_template.md's same-tag-collision gotcha).
