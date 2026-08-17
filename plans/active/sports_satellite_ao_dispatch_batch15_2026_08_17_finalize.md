---
doc_type: plan
title: Sports satellite AO batch 15 — finalize (2026-08-17)
summary: >-
  Gated finalize for `sports_satellite_ao_dispatch_batch15_2026_08_17.md`. Once every batch15 todo lands: reconcile
  each item's evidence back into its true source doc's own checkbox (`sports_consolidated_closeout_2026_07_19.md` for
  6 items, `sports_odds_writer_flip_and_trades_path_retirement_2026_08_15.md` for 5), check whether either source doc
  is now fully done (neither is expected to be — both carry other, non-extracted open work), and run the standard
  6-step archival ritual on batch15 itself once fully done.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [sports, ao-dispatch, close-out, batch-15, finalize, na-eligibility-audit]
related:
  [
    /plans/active/sports_satellite_ao_dispatch_batch15_2026_08_17.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/sports_odds_writer_flip_and_trades_path_retirement_2026_08_15.md,
  ]
created: "2026-08-17"
last_updated: "2026-08-17"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.32
assigned_role: data_engineering
effort: medium
drift_direction: advance-code
sequential: true
depends_on: [sports_satellite_ao_dispatch_batch15_2026_08_17]
gate_on_depends: true
locked_by:
locked_since:
supersedes:
superseded_by:
source: task_template.md §4 "Every AO-dispatched plan needs a gated finalize plan" (operator ruling 2026-07-24).
context_scope:
  [
    /plans/active/sports_satellite_ao_dispatch_batch15_2026_08_17.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
---

# Sports satellite AO batch 15 — finalize (2026-08-17)

## Todos

- [ ] [REVIEW] P2. **Reconcile every batch15 item's landed evidence back into its true source doc's own checkbox** —
      do not trust either source doc's own copy of the evidence line; re-verify the cited commit/report/census
      actually exists before flipping. 6 items reconcile into `sports_consolidated_closeout_2026_07_19.md` (the
      PERPETUAL/football census, cutover-runbook fix, catalogue player-grain upgrade, backfill-launcher diagnostic,
      shard-splitting-flag check, 5-pipeline-check checkpoint run); 5 items reconcile into
      `sports_odds_writer_flip_and_trades_path_retirement_2026_08_15.md` (Phase 1 regression-verify, both Phase 2
      items, both Phase 3 census/restamp items). Done when: all 11 source-doc checkboxes are flipped with
      independently re-verified evidence, or explicitly left open with a stated reason if a batch15 item did not
      actually land as claimed.
- [ ] [DOC] P2. **Check whether either source doc is now fully done** after the reconciliation above. Neither is
      expected to reach 0 open todos this pass: `sports_consolidated_closeout_2026_07_19.md` carries dozens of other
      open Track items untouched by this batch and its own standing ⛔ 2026-07-23 ruling keeps it `assigned_vm: NA`
      regardless; `sports_odds_writer_flip_and_trades_path_retirement_2026_08_15.md` keeps its `[OPERATOR]`-gated
      Phase 3 delete (item 6) and its dependent script-retirement item (item 7) open by design. If either doc
      genuinely does reach 0 open todos, run the standard 6-step archival ritual on it (do not assume — verify the
      checkbox count directly). Done when: both docs' true open-todo counts are stated, and any doc that is genuinely
      at 0 is archived with evidence.
- [ ] [DOC] P1. **Archive this batch15 plan itself once every todo above is `[x]` and unlocked** — standard 6-step
      ritual (dated archive folder under `plans/archive/2026_08/`, exact-successor banner, corpus-wide referrer-path
      fixup for any doc citing `sports_satellite_ao_dispatch_batch15_2026_08_17.md`). Done when: the plan is archived
      and `regenerate_active_plan_inventory.py` shows zero dangling referrers.

## Progress Log

- **2026-08-17 (na-eligibility-audit sports, dispatch agt-555dfd, slot 26)**: drafted alongside batch15, per the
  mandatory gated-finalize-plan rule (task_template.md §4). `depends_on`+`gate_on_depends: true` machine-holds every
  task here until batch15's own 11 todos are done. Authored `status: active` (not `draft`), same no-double-gate
  reasoning as batch15 itself.
- **context-scout 2026-08-17**: populated/refreshed context_scope (2 entries) -- re-verified both entries still
  resolve on disk; no change.
