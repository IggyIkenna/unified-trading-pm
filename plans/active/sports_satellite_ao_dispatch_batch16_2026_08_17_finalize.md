---
doc_type: plan
title: Sports satellite AO batch 16 — finalize (2026-08-17)
summary: >-
  Gated finalize for `sports_satellite_ao_dispatch_batch16_2026_08_17.md`. Once both batch16 todos land: reconcile
  each item's evidence back into `sports_consolidated_closeout_2026_07_19.md`'s own checkboxes (lines 580, 582) — a
  step this batch's own extraction pass could not do directly (source doc over its 1000L line cap, no SCOPED-mode
  exception fits a multi-item citation edit) — check whether the source doc's Track S is now fully done (not
  expected; Track S and the rest of the closeout carry other open work), and run the standard 6-step archival ritual
  on batch16 itself once fully done.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [sports, ao-dispatch, close-out, batch-16, finalize, na-eligibility-audit]
related:
  [
    /plans/active/sports_satellite_ao_dispatch_batch16_2026_08_17.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
  ]
created: "2026-08-17"
last_updated: "2026-08-17"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: data_engineering
effort: medium
drift_direction: advance-code
sequential: true
depends_on: [sports_satellite_ao_dispatch_batch16_2026_08_17]
gate_on_depends: true
locked_by:
locked_since:
supersedes:
superseded_by:
source: task_template.md §4 "Every AO-dispatched plan needs a gated finalize plan" (operator ruling 2026-07-24).
context_scope:
  [
    /plans/active/sports_satellite_ao_dispatch_batch16_2026_08_17.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
---

# Sports satellite AO batch 16 — finalize (2026-08-17)

## Todos

- [ ] [REVIEW] P2. **Reconcile both batch16 items' landed evidence back into `sports_consolidated_closeout_2026_07_19.md`'s
      own checkboxes** (Track S, lines ~580 and ~582 as of 2026-08-17 — re-locate by content if the doc has shifted)
      — do not trust batch16's own copy of the evidence line; re-verify the cited commit/report/census actually
      exists before flipping. **Check the source doc's current line count before editing** — if still over the 1000L
      hard cap, the citation-flip edit must fit a SCOPED-mode `check_line_caps.sh` exception (a single-hunk
      single-checkbox flip qualifies per the 2026-08-15 BLK-a2710376 ruling; do each item as its own separate commit
      if needed) or the doc must first go through a `/plan-reconcile` line-cap-split pass. Done when: both source-doc
      checkboxes are flipped with independently re-verified evidence, or explicitly left open with a stated reason if
      a batch16 item did not actually land as claimed.
- [ ] [DOC] P2. **Check whether `sports_consolidated_closeout_2026_07_19.md`'s Track S is now fully done** after the
      reconciliation above. Not expected — the source doc carries dozens of other open Track items untouched by this
      batch and its own standing ⛔ 2026-07-23 ruling keeps it `assigned_vm: NA` regardless of any single Track's
      state. Done when: Track S's true open-todo count is stated.
- [ ] [DOC] P1. **Archive this batch16 plan itself once both todos above are `[x]` and unlocked** — standard 6-step
      ritual (dated archive folder under `plans/archive/2026_08/`, exact-successor banner, corpus-wide referrer-path
      fixup for any doc citing `sports_satellite_ao_dispatch_batch16_2026_08_17.md`). Done when: the plan is archived
      and `regenerate_active_plan_inventory.py` shows zero dangling referrers.

## Progress Log

- **2026-08-17 (na-eligibility-audit sports, dispatch agt-1c51ee, slot 29)**: drafted alongside batch16, per the
  mandatory gated-finalize-plan rule (task_template.md §4). `depends_on`+`gate_on_depends: true` machine-holds every
  task here until batch16's own 2 todos are done. Authored `status: active` (not `draft`), same no-double-gate
  reasoning as batch16 itself. This finalize plan's todo 1 additionally owns the source-doc citation-flip that
  batch16's own extraction pass could not perform directly due to the source doc's line-cap state.
- **context-scout 2026-08-17**: populated/refreshed context_scope (2 entries) -- re-verified both entries still
  resolve on disk; no change.
