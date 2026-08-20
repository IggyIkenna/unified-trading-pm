---
doc_type: plan
title: Strategy-service centralization fixes — finalize
summary: >-
  Gated finalize for `strategy_service_centralization_fixes_2026_08_16`. Reconciles each completed todo's evidence
  back into its true source doc (the three issue docs and the codex doc this plan executes against), re-checks
  whether any [OPERATOR]-gated todo has since cleared and needs spinning into a new tracked todo, then runs the
  standard archival ritual on the now-fully-done plan and any source issue doc left with zero open todos.
status: active
nature: process
asset_group: [defi]
stage: [execution]
repos: [strategy-service, execution-service, features-service, unified-api-contracts]
scope: [engineer]
tags: [defi, risk, centralization, finalize]
related:
  [
    /plans/active/strategy_service_centralization_fixes_2026_08_16.md,
    /plans/active/issues/defi_leverage_archetypes_health_factor_wrong_source_2026_08_16.md,
    /plans/active/issues/venue_eligibility_hardcoded_outside_carry_and_yield_2026_08_16.md,
    /plans/active/issues/per_client_config_surface_keying_and_missing_axes_2026_08_12.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
  ]
created: 2026-08-16
last_updated: "2026-08-20"
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
assigned_role: backend_engineer
effort: low
drift_direction: none
depends_on: [strategy_service_centralization_fixes_2026_08_16]
gate_on_depends: true
sequential: true
locked_by:
locked_since:
supersedes:
superseded_by:
source: Authored alongside the parent plan per this workspace's mandatory finalize-plan rule (task_template.md §4).
context_scope:
  [
    /plans/active/strategy_service_centralization_fixes_2026_08_16.md,
    /plans/active/issues/defi_leverage_archetypes_health_factor_wrong_source_2026_08_16.md,
    /plans/active/issues/per_client_config_surface_keying_and_missing_axes_2026_08_12.md,
    /plans/active/issues/venue_eligibility_hardcoded_outside_carry_and_yield_2026_08_16.md,
  ]
---

# Strategy-service centralization fixes — finalize

- [ ] [REVIEW] P2. Reconcile every completed todo in `strategy_service_centralization_fixes_2026_08_16` back into
      its true source doc's own checkbox: the health-factor/liquidation todos into
      `defi_leverage_archetypes_health_factor_wrong_source_2026_08_16`, the config-loader todo into
      `per_client_config_surface_keying_and_missing_axes_2026_08_12`, the venue-literal audit into
      `venue_eligibility_hardcoded_outside_carry_and_yield_2026_08_16`. Re-verify each cited commit exists — do not
      trust the source doc's own copy of the evidence line.
- [ ] [REVIEW] P2. Re-check every `[OPERATOR]`-tagged todo in the parent plan: has the operator ruled since
      authoring? If so, spin the ruling's follow-up work into a new tracked todo (in this plan if still open work
      remains, or note resolution if the ruling closed the question with no further work).
- [ ] [DOC] P2. Run the standard 6-step archival ritual on `strategy_service_centralization_fixes_2026_08_16` once
      every todo is `[x]` and unlocked, including the corpus-wide referrer-path fixup.
- [ ] [DOC] P3. For each of the three source issue docs touched by the first todo above: if reconciling its
      checkbox(es) left it with zero open todos, that doc is now ALSO an archival candidate — run the same 6-step
      ritual on it, not just a checkbox flip.

## Progress Log

- **2026-08-16** — Authored alongside the parent plan. `status: active` with `depends_on`+`gate_on_depends: true` —
  ingested immediately but machine-held until every parent-plan task is done, per task_template.md §4's
  already-finalized-downstream mechanism (distinct from draft-gating, which is for a NOT-yet-finalized later
  phase).
- **context-scout 2026-08-17**: refreshed context_scope (4 entries) -- added the 3 source issue docs this finalize's
  own first todo names as reconciliation targets.
- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries)
