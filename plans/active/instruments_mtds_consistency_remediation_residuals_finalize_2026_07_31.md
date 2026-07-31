---
doc_type: plan
title: Finalize — instruments/MTDS F1-N9 consistency remediation residuals (na-eligibility-audit reclassify)
summary: >-
  Gated finalize twin for instruments_mtds_consistency_remediation_residuals_2026_07_24.md's 2026-07-31
  na-eligibility-audit RECLASSIFY (NA -> planning, partial: 7 of 14 open todos). Reconciles the 7 dispatched todos'
  evidence, re-verifies the 5 KEEP-NA-STALE citations still resolve once cross_cutting_satellite_ao_dispatch_batch1's
  own residual todo lands, and runs the 6-step archival ritual once the source plan is genuinely done.
status: draft
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ao-dispatch, na-eligibility-audit, finalize, instruments, mtds, plan-hygiene]
related:
  [
    /plans/active/instruments_mtds_consistency_remediation_residuals_2026_07_24.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: "2026-07-31"
last_updated: "2026-07-31"
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: data_engineering
depends_on: [instruments_mtds_consistency_remediation_residuals_2026_07_24]
gate_on_depends: true
sequential: true
locked_by:
locked_since:
supersedes:
superseded_by:
drift_direction: none
source: >-
  na-eligibility-audit cross-cutting run 2026-07-31 (dispatch agt-845699) — Phase 3 apply, finalize-plan-coverage rule
  (task_template.md § 4).
---

# Finalize — instruments/MTDS F1-N9 consistency remediation residuals

> Gated on `instruments_mtds_consistency_remediation_residuals_2026_07_24.md`'s 7 reclassified todos all reaching `[x]`.
> Do not start before that (enforced by `depends_on` + `gate_on_depends: true`).

## Todos

- [ ] [REVIEW] P2. Re-verify each of the 7 dispatched todos' evidence citation is real before this plan is treated as
      done: research `-prd-` bucket index move, tradfi legacy-straggler verify-delete, F1 CEFI Kraken-backfill-verify,
      N5r/N6r DeFi rebuild-for-real-replace, F6-reframed tradfi option-encoding unification, N1b CEFI ~698k reconcile,
      Phase D cefi legacy-dupe delete. **Done when**: each cites a resolvable commit SHA or a re-run report path, not
      just a checkmark.
- [ ] [REVIEW] P2. Re-check that `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md`'s "Close 5 small bounded
      residuals from instruments_mtds_consistency_remediation_residuals_2026_07_24.md" todo (~L339) has actually landed
      by the time this finalize runs — if that todo is still open, the 5 KEEP-NA-STALE closures in the source doc cite
      real, still-valid ground; if it has since been superseded/reworked, re-verify the citation still resolves before
      archiving. **Done when**: the citation is confirmed live, or corrected if the batch1 doc's own todo changed shape.
- [ ] [DOC] P3. Once the source doc's own 7 dispatched todos are `[x]` and unlocked, run the standard 6-step archival
      ritual (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`) on
      `instruments_mtds_consistency_remediation_residuals_2026_07_24.md`: migrate any residual deferral into a real
      todo, add the archived banner + successor pointer, codex-alignment check, fix every corpus referrer's path,
      `git     mv` to `plans/archive/2026_07/`. **Done when**: the doc lives under `plans/archive/` and every referrer
      resolves.
