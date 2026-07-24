---
doc_type: plan
title: Sports closeout batch 1 — finalize (reconcile parent checkboxes + resolve spun-off issues + archive)
summary: >-
  Gated closeout for sports_closeout_batch1_ao_ready_2026_07_24.md — machine-held until every one of that plan's 20
  todos is done (depends_on + gate_on_depends: true, not just prose), so this never dispatches early. Reconciles the
  parent umbrella plan's corresponding checkboxes, resolves any issue doc a batch-1 todo referenced or spun off, then
  runs the standard plan-archival ritual on the now-fully-closed batch-1 plan itself.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [sports, ao-dispatch, close-out, batch-1, archival]
related:
  [
    /plans/active/sports_closeout_batch1_ao_ready_2026_07_24.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
  ]
created: "2026-07-24"
last_updated: "2026-07-24"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.5
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [sports_closeout_batch1_ao_ready_2026_07_24]
gate_on_depends: true
source: >-
  Operator request 2026-07-24: "one of the plan todos [should] include marking all associated plans and issues done once
  batch 1 is done and running the multi step archive process" — split into its own gated plan per task_template.md §4's
  "partial parallelism is NOT expressible inside one plan" rule, rather than added as a 21st todo to batch 1 itself
  (which would have either dispatched early, ungated, or forced sequential: true on the whole batch and killed its
  intended intra-plan concurrency).
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
---

# Sports closeout batch 1 — finalize

> **Machine-gated on `sports_closeout_batch1_ao_ready_2026_07_24.md`** (`depends_on` + `gate_on_depends: true`) — the
> dispatcher will not queue either todo below until every task in that plan is `done`. `sequential: true` because todo 2
> (archival) must not run before todo 1 (reconciliation) — the archive ritual's codex-alignment check needs the final,
> reconciled state.

## Todos

- [ ] [REVIEW] P1. **Reconcile parent + resolve spun-off issues.** For each of
      `sports_closeout_batch1_ao_ready_2026_     07_24.md`'s 20 now-done todos: (1) flip the corresponding checkbox in
      `sports_consolidated_closeout_2026_07_19.md` (the parent umbrella plan) to `[x]`, citing the batch-1 commit(s)
      that shipped it as evidence — do not just copy batch-1's own evidence line, verify the actual shipped commit
      exists (`git log`/`git show`) before citing it. (2) Check whether each todo referenced or was directed to create
      its own issue doc (at minimum: todo 20 explicitly creates a NEW issue doc for the QG structural finding — that doc
      should exist and stay `status: open` since it documents a still-real, unfixed workspace-infra bug, NOT resolved by
      this reconciliation pass; todo 4's `sfi_progressive_features` investigation may have spun off its own issue doc if
      the root cause needed one — check). For any PRE-EXISTING issue doc a batch-1 todo's scope fully closes (re-verify
      0 open todos remain in that doc, don't just trust the batch-1 todo's own claim), flip it `status: resolved` with
      `resolved_by` citing the closing commit. **Done when**: all 20 parent checkboxes are flipped with verified
      evidence, and every issue doc touched by batch-1's scope has an accurate, re-verified `status` (resolved only
      where genuinely 0 open todos remain — do not blanket-resolve).
- [ ] [DOC] P2. **Archive `sports_closeout_batch1_ao_ready_2026_07_24.md`** via the standard 6-step ritual (per
      CLAUDE.md's plan-archival rule): migrate any DEFERRED items to a tracked todo elsewhere (there should be none —
      batch 1 was scoped to have zero dependencies left dangling, but verify) → add the archive banner → run the
      codex-alignment check (do any codex docs need a status update now that these 20 items shipped — e.g. the Distinct
      Values canonical-vocabulary target todo 2 closes) → update CLAUDE.md/codex if any new durable contract resulted →
      grep the corpus for every referrer of `sports_closeout_batch1_ao_ready_2026_07_24` (including the cross-reference
      banner this plan's own creation added to `sports_consolidated_closeout_2026_07_19.md`) and fix each path to point
      at the archived location → clear `locked_by` (already empty here, confirm). **Done when**: the plan is moved to
      `plans/archive/2026_07/`, every corpus referrer resolves to the new path, and the parent plan's cross-reference
      banner is updated to reflect batch 1 as archived-and-complete.
