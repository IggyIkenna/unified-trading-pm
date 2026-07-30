---
doc_type: plan
title: Sports satellite AO batch 8 — finalize (reconcile source docs)
summary: >-
  Gated closeout for sports_satellite_ao_dispatch_batch8_2026_07_30.md — machine-held via depends_on + gate_on_depends:
  true until all 5 of that plan's todos are done. Mirrors the batch3-7-finalize pattern: reconcile each distinct source
  doc's checkboxes once its batch-8 todo lands, then archive both docs.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [sports, ao-dispatch, close-out, batch-8, satellite-docs]
related:
  [
    /plans/active/sports_satellite_ao_dispatch_batch8_2026_07_30.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/sports_satellite_ao_dispatch_batch7_2026_07_27_finalize.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-30"
last_updated: "2026-07-30"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.15
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [sports_satellite_ao_dispatch_batch8_2026_07_30]
gate_on_depends: true
source: >-
  /ag-closeout-audit-style workflow run 2026-07-30, per task_template.md §4's finalize-plan-coverage rule — every
  assigned_vm: planning plan needs a companion gated finalize plan, mirroring the batch2-7 precedent.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
---

# Sports satellite AO batch 8 — finalize

> **Status: draft.** Flip to `active` in the same commit/decision as the parent batch (`gate_on_depends: true` holds
> every todo below back until all 5 parent todos are `done`, regardless of this doc's own `status`).

> **Machine-gated on `sports_satellite_ao_dispatch_batch8_2026_07_30.md`** (`depends_on` + `gate_on_depends: true`) —
> the dispatcher will not queue any todo below until all 5 tasks in that plan are `done`. `sequential: true` because
> todo 1 needs all 5 parent todos' evidence to reconcile source docs correctly.

## Todos

- [ ] [REVIEW] P1. **Reconcile source-doc checkboxes for all 5 batch-8 todos.** Each batch-8 todo ends with a `Source:`
      line naming its specific section in `issues/sports_features_layer_findings_sweep_2026_07_18.md` — flip the
      corresponding checkbox there, citing the batch-8 commit(s) that shipped it. Verify every cited commit/evidence
      actually exists before citing it (`git merge-base --is-ancestor <sha> origin/live-defi-rollout`, or for the audit
      todo, re-run the stated read yourself rather than trusting the batch-8 todo's own claim). For the DIAG-verify todo
      (§E3), confirm it actually resolved to either a closed-with-citation state or a precisely-scoped new finding — not
      left ambiguous. **Done when**: every Source-cited section in the doc is flipped with verified evidence.
- [ ] [DOC] P2. **Archive `sports_satellite_ao_dispatch_batch8_2026_07_30.md` (and this finalize doc) once both are
      terminal**, per CLAUDE.md's plan-archival ritual: confirm the Deferred section's 3 items are still accurately
      described (re-verify, don't just carry forward) and migrate them to a tracked note for whichever future batch
      picks up `sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md` or the closeout's own
      dual-layout reconciliation → add the archive banner → confirm no new durable contract needs a codex update (this
      batch establishes none) → grep the corpus for every referrer of `sports_satellite_ao_dispatch_batch8_2026_07_30`
      and fix each path to the archived location → clear `locked_by` (already empty; confirm). **Done when**: both docs
      are in `plans/archive/2026_07/`, every corpus referrer resolves to the new path, and
      `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci` is 0-hard-failures afterwards.

## Codex SSOTs

None new — see the parent batch's own Codex SSOTs section.
