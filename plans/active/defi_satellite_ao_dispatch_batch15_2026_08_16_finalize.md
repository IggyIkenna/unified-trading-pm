---
doc_type: plan
title: Finalize — DeFi satellite AO batch 15
summary: >-
  Gated finalize plan for defi_satellite_ao_dispatch_batch15_2026_08_16.md. Reconciles the codex-doc-update todo's
  evidence back into the source doc's checkbox and closes the loop.
status: active
nature: process
asset_group: [defi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [defi, finalize, ao-dispatch, satellite-extraction, batch-15]
related:
  [
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/active/defi_satellite_ao_dispatch_batch15_2026_08_16.md,
    /plans/active/defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-16"
parent_epic: strategy_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.08
assigned_role: backend_engineer
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [defi_satellite_ao_dispatch_batch15_2026_08_16]
gate_on_depends: true
sequential: true
context_scope:
  [
    /plans/active/defi_satellite_ao_dispatch_batch15_2026_08_16.md,
    /plans/active/defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
effort: medium
drift_direction: advance-code
source: >-
  na-eligibility-audit 2026-08-16 (tranche=defi) — mandatory finalize companion for
  defi_satellite_ao_dispatch_batch15_2026_08_16.md per task_template.md's finalize-plan-coverage rule.
---

# Finalize — DeFi satellite AO batch 15

## Todos

- [ ] [REVIEW] P2. Reconcile batch15's codex-doc-update todo evidence back into
      `defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md`'s "Codex SSOT updates" checkbox —
      flip it `[x]` citing the actual commit sha(s) that landed the codex writeup (do not trust a copied evidence
      line; re-verify the cited commit exists on `origin/live-defi-rollout`). The source doc's other open item
      (wizard food-chain parameterization) is unaffected and stays open/NA.
- [ ] [DOC] P3. Archive `defi_satellite_ao_dispatch_batch15_2026_08_16.md` (standard 6-step ritual) once its sole
      todo is done — `git mv` to `plans/archive/2026_08/`, exact-successor banner, corpus referrer fixup — then
      archive this finalize plan alongside it. Give this todo a DIFFERENT `[TAG] P<n>` than the reconciliation
      todo above (already done: `[REVIEW]` vs `[DOC]`) so a same-commit flip+archive never collides on the AO
      done-gate's tag+priority disambiguator.

## Progress Log

- **2026-08-16 (na-eligibility-audit, defi tranche)**: drafted alongside batch15 in the same turn.
**context-scout 2026-08-17**: populated/refreshed context_scope (3 entries)
