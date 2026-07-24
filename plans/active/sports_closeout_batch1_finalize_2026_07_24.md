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

- [x] [REVIEW] P1. ✅ **Reconciled parent + resolved spun-off issues** — `unified-trading-pm@20915879b`. **Correction**:
      `sports_closeout_batch1_ao_ready_2026_07_24.md` actually carries **21** top-level done todos, not 20 (verified by
      grepping `^- \[x\]`) — its own frontmatter/description says "20 todos hand-picked", but todo 1 was split
      mid-execution (2026-07-24, `f5e38cb25`) into a CODE todo + a new DATA backfill todo, growing the real count to 21.
      Both map to the SAME parent checkbox (Track C's C1), so exactly 20 parent checkboxes were flipped — the "20 parent
      checkboxes" half of this todo's own done-when is still exactly met. (1) All 20 corresponding checkboxes flipped
      `[x]` in `sports_consolidated_closeout_2026_07_19.md` (Tracks F/C/O/H/V/K/D/X + the sports_master_closeout fold-in
      section), each citing evidence. Every cited commit SHA independently verified via `git log` across 9 repos
      (instruments-service, unified-api-contracts, market-data-processing-service, unified-trading-library,
      features-service, deployment-service, market-tick-data-service, unified-trading-pm) BEFORE citing — not copied
      from batch-1's own evidence lines; one citation (`features-service@4639106a`) was independently confirmed to NOT
      exist in the repo, matching batch-1's own note that it never reached origin (corrected citation `7ea10aaa` used
      instead). (2) Every issue doc referenced by a batch-1 todo re-verified for accurate `status` + open-todo count
      (not trusted from batch-1's own claims): `fixtures_manifest_duplicate_collision_residual_2026_07_24.md` (open, 1
      open — correct), `fixtures_manifest_legacy_backfill_2026_07_24.md` (open, 1 open — correct),
      `mdps_canonical_writer_adapter_contract_baseline_regression_2026_07_24.md` (resolved, 0 open — correct),
      `sports_odds_manifest_consolidator_captured_outranks_resurrection_2026_07_24.md` (resolved, 0 open — correct),
      `sports_odds_manifest_captured_outranks_blocks_legacy_leak_correction_2026_07_24.md` (resolved, 0 open — correct),
      `sports_fixtures_schedule_wrong_schema_day_2026_04_14.md` (open, 1 open — correct),
      `sports_fixtures_schedule_noncanonical_raw_league_id_folders_2026_07_24.md` (open, 1 open — correct),
      `sports_closeout_batch1_task018_partial_progress_2026_07_24.md` (resolved, 0 open — correct),
      `manifest_reader_silent_empty_on_missing_project_id_2026_07_24.md` (open, 1 open — correct). **One finding this
      todo's own premise got wrong**: it asserted the QG structural-finding issue doc
      (`qg_backfill_disk_and_lint_checks_resolve_via_main_clone_not_worktree_2026_07_24.md`) "should exist and stay
      `status: open`... NOT resolved by this reconciliation pass" — that premise is STALE. The doc is genuinely
      `status: resolved` (0 open todos, re-verified), root-caused + fixed by SEPARATE, later work not part of batch-1's
      own scope: `unified-trading-pm@e70a0d18e` (a worktree-identity guard in `qg-common.sh`, verified via `git log`).
      Left it `resolved` (documenting reality, not force-reverting a premise that turned out wrong) — a correctly-open
      follow-up remains: `qg_workspace_root_template_drift_12_repos_2026_07_24.md` (open, 2 open todos). No issue doc
      needed flipping — every one was already accurately maintained by prior workers. **Done-when met**: all 20 parent
      checkboxes flipped with independently-verified evidence; every touched issue doc's `status` re-verified accurate.
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
