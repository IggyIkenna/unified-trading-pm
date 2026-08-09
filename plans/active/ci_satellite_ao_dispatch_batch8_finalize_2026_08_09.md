---
doc_type: plan
title: CI satellite AO batch 8 — finalize (reconcile source doc, archive)
summary: >-
  Gated closeout for `ci_satellite_ao_dispatch_batch8_2026_08_09.md` — machine-held via `depends_on` + `gate_on_depends:
  true` until that plan's one todo is done. Reconciles the source doc's checkbox and archives batch 8 via the standard
  6-step ritual.
status: active
nature: process
asset_group:
  [ci] # corrected 2026-08-09 (/ag-closeout-audit ci) -- was [ci, cross-cutting]; mirrors batch8's own correction, a
  # finalize plan's scope is definitionally its batch's scope
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci, ao-dispatch, close-out, batch-8, satellite-docs, archival]
related:
  [
    /plans/active/ci_satellite_ao_dispatch_batch8_2026_08_09.md,
    /plans/archive/2026_08/issues/assigned_role_devops_invalid_value_corpus_wide_2026_08_08.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.08
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [ci_satellite_ao_dispatch_batch8_2026_08_09]
gate_on_depends: true
source: >-
  Authored alongside `ci_satellite_ao_dispatch_batch8_2026_08_09.md` per `plans/active/task_template.md` §4's
  finalize-plan-coverage rule. Authored `status: active` (not `draft`) per the established no-double-gate finding:
  `gate_on_depends: true` already machine-holds every task here until batch 8's own todo is `done`.
assigned_role: infra
effort: medium
sequential: true
drift_direction: none
context_scope:
  [
    /plans/active/ci_satellite_ao_dispatch_batch8_2026_08_09.md,
    /plans/archive/2026_08/issues/assigned_role_devops_invalid_value_corpus_wide_2026_08_08.md,
    /plans/active/task_template.md,
  ]
---

# CI satellite AO batch 8 — finalize

> **🔒 GATED, not draft.** `depends_on: [ci_satellite_ao_dispatch_batch8_2026_08_09]` + `gate_on_depends: true` holds
> both todos below until batch 8's one todo is `done`. `sequential: true` because archival must run after
> reconciliation.

## Todos

- [x] ✅ [REVIEW] P1. **DONE (slot 11, 2026-08-09) — source doc
      `assigned_role_devops_invalid_value_corpus_wide_2026_08_08.md` flipped `[x]` citing
      `unified-trading-pm@987cb57342` (ancestry-verified), `status: resolved`. Original ask below.** **Reconcile batch-8
      todo 1's source doc.** Batch-8 todo 1 ends with `Source:` naming
      `issues/assigned_role_devops_invalid_value_corpus_wide_2026_08_08.md`. Flip that doc's `[DOC] P3` checkbox to
      `[x]` citing the batch-8 commit that shipped it — **verify the cited commit exists and is an ancestor of
      `origin/live-defi-rollout` before citing it** (`git merge-base --is-ancestor`). This is that source doc's ONLY
      todo, so once flipped it genuinely reaches zero open work — set `status: resolved` on it too (both in the same
      edit). **Done when**: the checkbox is flipped with verified evidence and the doc's `status` reflects zero open
      work.
- [ ] [DOC] P1. **Archive `ci_satellite_ao_dispatch_batch8_2026_08_09.md`** via the standard 6-step ritual (CLAUDE.md §
      plan archival). **`issues/assigned_role_devops_invalid_value_corpus_wide_2026_08_08.md` is ALREADY archived**
      (done as part of todo 1 above, 2026-08-09 — the `check_archive_candidates`/`check_terminal_status_archived`
      pre-commit gates hard-blocked landing todo 1's flip while that doc sat `status: resolved` + 0 open todos in
      `plans/active/`, so its archival + corpus referrer repoint had to happen in the SAME commit as the flip; see that
      doc's own archive banner + this plan's Progress Log) — do NOT redo it, just verify it's already at
      `plans/archive/2026_08/issues/`. This todo now only needs: archive `ci_satellite_ao_dispatch_batch8_2026_08_09.md`
      itself → add its archive banner → grep the corpus for every remaining referrer of
      `ci_satellite_ao_dispatch_batch8_2026_08_09` and repoint each to its archived path → clear `locked_by` (already
      empty; confirm). **Done when**: the batch8 doc is in `plans/archive/2026_08/`, every corpus referrer resolves,
      `check_reference_paths.py` has not regressed, and this finalize doc is archived alongside it in the same commit.

## Codex SSOTs

- `/codex/11-project-management/doc-frontmatter-schema.md` — `assigned_role` field definition
- `/codex/11-project-management/` — archival ritual, issue-doc lifecycle
- `plans/active/task_template.md` §4 — the finalize-plan-coverage rule this plan satisfies

## Progress Log

- **2026-08-09** — Drafted alongside `ci_satellite_ao_dispatch_batch8_2026_08_09.md`. Authored `status: active` per the
  established no-double-gate precedent; batch 8 itself is also authored `status: active` per this task's explicit
  dispatch instructions.
- **2026-08-09 (review craft, slot 11)** — Todo 1 done. Verified `unified-trading-pm@987cb57342` (batch-8 todo 1's retag
  commit) is an ancestor of `origin/live-defi-rollout` before citing it; re-ran the source doc's own done-when grep
  myself (zero results, confirmed). Flipped the source doc's todo `[x]` with the verified citation and set its
  `status: resolved`. **Correction to this entry**: `status: resolved` + 0 open todos made the source doc a hard
  `check_archive_candidates`/`check_terminal_status_archived` pre-commit failure while sitting in `plans/active/` —
  could not land the todo-1 commit at all without either archiving it or `archive_exempt: true`. Archived it properly in
  the SAME commit (banner, `resolved_by` filled, referrers repointed) rather than exempting, since the work was already
  in hand. Todo 2's text updated to reflect this — it now only archives the batch8 doc + this finalize plan itself. Todo
  2 remains next, gated `sequential: true`, a separate dispatch.
