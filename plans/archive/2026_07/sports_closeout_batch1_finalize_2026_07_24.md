---
doc_type: plan
title: Sports closeout batch 1 — finalize (reconcile parent checkboxes + resolve spun-off issues + archive)
summary: >-
  Gated closeout for sports_closeout_batch1_ao_ready_2026_07_24.md — machine-held until every one of that plan's 20
  todos is done (depends_on + gate_on_depends: true, not just prose), so this never dispatches early. Reconciles the
  parent umbrella plan's corresponding checkboxes, resolves any issue doc a batch-1 todo referenced or spun off, then
  runs the standard plan-archival ritual on the now-fully-closed batch-1 plan itself.
status: complete
nature: process
asset_group: [sports]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [sports, ao-dispatch, close-out, batch-1, archival]
related:
  [
    /plans/archive/2026_07/sports_closeout_batch1_ao_ready_2026_07_24.md,
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

> **✅ ARCHIVED 2026-07-25 — COMPLETE.** Both todos verified `[x]` (independently re-confirmed by the
> `ag-closeout-audit-sports-2026-07-25` orphan-audit workflow, not just this doc's own claim): todo 1 reconciled all 20
> parent checkboxes in `sports_consolidated_closeout_2026_07_19.md` with independently-verified commit evidence; todo 2
> archived `sports_closeout_batch1_ao_ready_2026_07_24.md` via the full 6-step ritual, 12 referrer paths fixed. This doc
> itself was left un-archived after that — archiving it now.

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
- [x] [DOC] P2. ✅ **Archived `sports_closeout_batch1_ao_ready_2026_07_24.md`** via the standard 6-step ritual —
      `unified-trading-pm@(this commit)`. (1) DEFERRED check: zero `DEFERRED` markers found, all 21 top-level todos
      confirmed `[x]` before archiving. (2) Archive banner added (`> **✅ ARCHIVED 2026-07-24 — COMPLETE.**`) +
      `status: active` → `status: complete` in frontmatter. (3) Codex-alignment check: zero `codex/` references anywhere
      in the plan body — no codex doc needed a status update. (4) No new durable contract resulted requiring a
      CLAUDE.md/codex change. (5) Corpus-wide grep found 12 real leading-slash (`/plans/active/...`) referrers across 11
      files (`sports_closeout_batch1_finalize_2026_07_24.md`,
      `sports_closeout_batch1_task018_partial_progress_2026_07_24.md`, `fixtures_manifest_legacy_backfill_2026_07_24.md`
      (4×), `sports_fixtures_schedule_wrong_schema_day_2026_04_14.md`,
      `sports_odds_manifest_consolidator_captured_outranks_resurrection_2026_07_24.md`,
      `manifest_reader_silent_empty_on_missing_project_id_2026_07_24.md`,
      `sports_fixtures_schedule_noncanonical_raw_league_id_folders_2026_07_24.md`,
      `fixtures_manifest_duplicate_collision_residual_2026_07_24.md`,
      `sports_odds_markets_outcomes_settlements_arbitrage_expected_since_2024_zero_captured_2026_07_24.md`,
      `sports_odds_manifest_captured_outranks_blocks_legacy_leak_correction_2026_07_24.md`,
      `qg_backfill_disk_and_lint_checks_resolve_via_main_clone_not_worktree_2026_07_24.md`) — all repointed to
      `/plans/archive/2026_07/sports_closeout_batch1_ao_ready_2026_07_24.md`; the one actual markdown LINK (not a bare
      prose mention) was in the auto-generated `active_plan_inventory_dashboard_2026_07_24.md`, fixed by regenerating it
      (`regenerate_active_plan_inventory.py`, 0 orphans). The parent plan's own cross-reference banner
      (`sports_consolidated_closeout_2026_07_19.md` line 97) rewritten to state archived-and-complete, pointing at the
      new path. Bare backtick prose citations (e.g. "shipped via `sports_closeout_batch1_ao_ready_2026_07_24.md` todo
      8") were NOT touched — not navigable links, just historical evidence citations naming a file that still exists
      (just moved); `check_doc_body_links.py` only flags actual `[text](path)` markdown links, confirmed these don't
      trip it. (6) `locked_by` confirmed already empty. **Done when met**: plan moved to `plans/archive/2026_07/`, every
      corpus referrer resolves to the new path, parent plan's banner updated to archived-and-complete.
