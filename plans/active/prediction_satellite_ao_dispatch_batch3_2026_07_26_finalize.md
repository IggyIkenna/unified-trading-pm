---
doc_type: plan
title: Prediction satellite AO batch 3 — finalize (reconcile source docs + resolve deferrals + archive)
summary: >-
  Gated closeout for prediction_satellite_ao_dispatch_batch3_2026_07_26.md — machine-held via depends_on +
  gate_on_depends: true until both of that plan's todos are done. Mirrors batch1/batch2-finalize's pattern (reconcile
  each distinct source doc's checkboxes independently, then re-check the Deferred operator-gated/time-gated/human-only
  items for any that have since cleared — including re-checking whether sports_satellite_ao_dispatch_batch5's ml-service
  migration todo has landed, which would clear the 2 already-covered-elsewhere notes), then archives batch3 via the
  standard 6-step ritual.
status: active
nature: process
asset_group: [prediction]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [prediction, ao-dispatch, close-out, batch-3, satellite-docs, archival]
related:
  [
    /plans/active/prediction_satellite_ao_dispatch_batch3_2026_07_26.md,
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
    /plans/active/prediction_satellite_ao_dispatch_batch2_finalize_2026_07_25.md,
    /plans/active/sports_satellite_ao_dispatch_batch5_2026_07_26.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-26"
parent_epic: predictions_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [prediction_satellite_ao_dispatch_batch3_2026_07_26]
gate_on_depends: true
source: >-
  /ag-closeout-audit skill run 2026-07-26, per task_template.md §4's finalize-plan-coverage rule — every AO-dispatched
  plan needs a companion gated finalize plan, mirroring the prediction batch1/batch2 + cefi/defi/sports/tradfi
  precedent.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
---

# Prediction satellite AO batch 3 — finalize

> **Machine-gated on `prediction_satellite_ao_dispatch_batch3_2026_07_26.md`** (`depends_on` + `gate_on_depends: true`)
> — the dispatcher will not queue any todo below until both tasks in that plan are `done`. `sequential: true` because
> todo 2 (deferred re-check) needs todo 1's reconciliation done first, and todo 3 (archival) must run last.

## Todos

- [x] ✅ [REVIEW] P1. **Reconcile both distinct source docs' checkboxes.** For each of
      `prediction_satellite_ao_dispatch_batch3_2026_07_26.md`'s now-done todos: flip the corresponding checkbox/section
      in its named source doc (each todo's text ends with "Source: `<doc>.md`"), citing the batch-3 commit(s) that
      shipped it. After flipping, re-check whether the source doc now has 0 open todos remaining (checkbox AND
      prose-form). Only flip `status` to `resolved` if it genuinely reaches 0 open todos. **Done when**: both source-doc
      checkboxes/sections are flipped with verified evidence. **Done 2026-07-26**: of batch3's 2 todos, only todo 1's
      schema-drift half is actually "now-done" (its paper-order-flow half is still `BLOCKED-OPERATOR`; todo 2 is a fully
      un-started `[OPERATOR]` item, a/b/c/d all pending) — so only ONE of the two source docs had anything to reconcile.
      Flipped item 3 ("Triage the... schema-drift GitHub issue chain") in
      `plans/active/issues/kalshi_live_capture_regression_and_drift_2026_07_13.md`'s prose-form "Suggested next step"
      list to ✅ RESOLVED, citing `unified-api-contracts@c03161a1` + the closed GH issue chain (#45→#590 as duplicates
      of #673). That doc stays `status: open` — items 1 (live-stall triage) and 2 (e2e-testing host regression) are
      still genuinely open, so it does not reach 0 open items. Checked
      `plans/active/issues/prediction_phantom_reconciler_wipes_bundle_atom_2026_07_10.md` (todo 2's source doc) directly
      — confirmed zero sub-items done, so correctly left untouched (nothing to flip).
- [ ] [REVIEW] P1. **Re-check the 7 operator-gated + 1 time-gated + 1 human-only Deferred items, plus the 2
      already-covered-elsewhere notes**, now that time has passed. For the 2 already-covered-elsewhere notes
      specifically: check whether `sports_satellite_ao_dispatch_batch5_2026_07_26.md`'s ml-service odds-feature-naming
      migration todo has landed — if it has, `sports_odds_feature_naming_four_way_mismatch_2026_07_21.md` and
      `sports_odds_feature_naming_canonicalization_2026_07_21.md` should have their checkboxes/status reconciled per
      that batch's own finalize plan (do not re-do that reconciliation here, just confirm it happened). For the other 9
      Deferred items: re-read the specific gating ground to check if it has since cleared — if so, extract it as a new
      tracked todo in a follow-up `batch4`; if still genuinely unresolved, leave it explicitly deferred, do not
      re-surface an already-asked operator question a second time. **Done when**: each of the 11 Deferred/note items has
      either (a) a note that it's ready for `batch4` extraction, (b) an explicit re-verified confirmation the gate is
      still open, or (c) confirmation the already-covered-elsewhere item resolved via the other batch's own mechanism.
- [ ] [DOC] P1. **Archive `prediction_satellite_ao_dispatch_batch3_2026_07_26.md`** via the standard 6-step ritual (per
      CLAUDE.md's plan-archival rule): migrate any remaining Deferred items to a tracked todo elsewhere (todo 2 above
      should have already resolved or re-confirmed all 11 — verify none silently vanish) → add the archive banner → run
      the codex-alignment check (no new durable contract from this batch, confirm still true) → grep the corpus for
      every referrer of `prediction_satellite_ao_dispatch_batch3_2026_07_26` and fix each path to point at the archived
      location → clear `locked_by` (already empty here, confirm). **Done when**: the plan is moved to
      `plans/archive/2026_07/`, every corpus referrer resolves to the new path, and this finalize doc itself gets
      archived alongside it in the same commit.
