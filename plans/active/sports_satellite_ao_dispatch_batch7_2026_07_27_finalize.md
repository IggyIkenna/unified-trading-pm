---
doc_type: plan
title: Sports satellite AO batch 7 — finalize (reconcile source docs + re-check Deferred)
summary: >-
  Gated closeout for sports_satellite_ao_dispatch_batch7_2026_07_27.md — machine-held via depends_on + gate_on_depends:
  true until all 4 of that plan's todos are done. Mirrors the batch3-6-finalize pattern: reconcile each distinct source
  doc's checkboxes once its batch-7 todo lands, then re-check the 7 Deferred items for any that have since cleared
  (extract into a future batch8 if so, do not draft here).
status: active
nature: process
asset_group: [sports]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [sports, ao-dispatch, close-out, batch-7, satellite-docs]
related:
  [
    /plans/active/sports_satellite_ao_dispatch_batch7_2026_07_27.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/sports_satellite_ao_dispatch_batch6_2026_07_26_finalize.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-27"
last_updated: "2026-07-27"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.2
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [sports_satellite_ao_dispatch_batch7_2026_07_27]
gate_on_depends: true
source: >-
  /ag-closeout-audit-style workflow run 2026-07-27, per task_template.md §4's finalize-plan-coverage rule — every
  assigned_vm: planning plan needs a companion gated finalize plan, mirroring the batch2-6 precedent.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
context_scope:
  [
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/active/sports_satellite_ao_dispatch_batch7_2026_07_27.md,
    /plans/active/sports_satellite_ao_dispatch_batch6_2026_07_26_finalize.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
---

# Sports satellite AO batch 7 — finalize

> **✅ `status: active` — flipped 2026-07-27 in the same commit as its parent, on explicit operator approval.**
> `gate_on_depends: true` (below) is the mechanism that actually holds this plan's todos back until the parent's 4 todos
> are `done` — `status: active` alone does not bypass that gate.

> **Machine-gated on `sports_satellite_ao_dispatch_batch7_2026_07_27.md`** (`depends_on` + `gate_on_depends: true`) —
> the dispatcher will not queue any todo below until all 4 tasks in that plan are `done`. `sequential: true` because
> todo 1 needs all 4 parent todos' evidence to reconcile source docs correctly, and todo 2 (Deferred re-check) reads
> more cleanly once todo 1's flips are settled.

## Todos

- [ ] [REVIEW] P1. **Reconcile source-doc checkboxes for all 4 batch-7 todos.** Each batch-7 todo ends with a `Source:`
      line naming `sports_consolidated_closeout_2026_07_19.md`'s specific Track/section — flip the corresponding
      checkbox there, citing the batch-7 commit(s) that shipped it. **Verify every cited commit/evidence actually exists
      before citing it** (`git merge-base --is-ancestor <sha> origin/live-defi-rollout`, or for GCS operations, re-run
      the stated census/verify step yourself rather than trusting the batch-7 todo's own claim — this doc family has a
      real history of "immediate verify passed" claims that didn't hold, see
      `cross_ag_prediction_rows_bleed_into_sports_instruments_index_2026_07_20.md`'s ROUND 2/3). For todo 4 (DIAG,
      decision 16), confirm an issue doc was actually filed (or an existing RE-TRIAGE section actually updated) with a
      real root-cause finding — not just "investigated, inconclusive" as a way to close the checkbox without the
      substance the todo asked for. **Done when**: all 4 Track references in the closeout doc are flipped with verified
      evidence, and the duplicate-tracking issue doc for the pre-floor wipe
      (`issues/sports_pre_floor_fixtures_orphan_misclassification_2026_07_22.md`) has its todos 2-4 flipped in the same
      pass, citing the same evidence as batch-7 todo 2.

- [ ] [REVIEW] P1. **Re-check the 7 Deferred items from batch7's own doc** for cleared blockers. Specifically: has
      `sports_closeout_exchange_fixed_odds_fork_2026_07_25.md` shipped (would partially clear the QG-assertion Deferred
      item)? Has the operator ruled on the `entity=fixtures/` bare-path conflict (would clear 2 of the 7 items at once —
      Track S's eliminate/document fork AND Track E's consumer-repoint)? Has decision-12's cross-object-CAS safety
      mechanism been built by any other in-flight work (would clear CF-8's maintenance-window todo's prerequisite)? For
      each item: if the blocker cleared, extract it as a new tracked todo in a follow-up `batch8` (do not draft it here
      — this plan's scope is reconciliation, not fresh drafting); if still genuinely unresolved, leave it explicitly
      deferred with a note that the re-check happened and found no change — do not re-ask an operator question already
      asked. **Done when**: every one of the 7 Deferred bullets has either (a) a note that it is ready for `batch8`
      extraction because its blocker cleared, or (b) an explicit re-verified confirmation the conflict/decision is still
      open, dated 2026-07-27 or later.

- [ ] [DOC] P2. **Archive `sports_satellite_ao_dispatch_batch7_2026_07_27.md` (and this finalize doc) once both are
      terminal**, per CLAUDE.md's plan-archival ritual: migrate any remaining Deferred items to a tracked
      `batch8`-candidate note (todo 2 above should have resolved this) → add the archive banner → confirm no new durable
      contract needs a codex update (this batch establishes none) → grep the corpus for every referrer of
      `sports_satellite_ao_dispatch_batch7_2026_07_27` and fix each path to the archived location → clear `locked_by`
      (already empty; confirm). **Done when**: both docs are in `plans/archive/2026_07/`, every corpus referrer resolves
      to the new path, and `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci` is 0-hard-failures afterwards.

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
