---
doc_type: plan
title: CI satellite AO batch 8 — finalize (reconcile source doc, archive)
summary: >-
  Gated closeout for `ci_satellite_ao_dispatch_batch8_2026_08_09.md` — machine-held via `depends_on` + `gate_on_depends:
  true` until that plan's one todo is done. Reconciles the source doc's checkbox and archives batch 8 via the standard
  6-step ritual.
status: active
nature: process
asset_group: [ci, cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci, ao-dispatch, close-out, batch-8, satellite-docs, archival]
related:
  [
    /plans/active/ci_satellite_ao_dispatch_batch8_2026_08_09.md,
    /plans/active/issues/assigned_role_devops_invalid_value_corpus_wide_2026_08_08.md,
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
    /plans/active/issues/assigned_role_devops_invalid_value_corpus_wide_2026_08_08.md,
    /plans/active/task_template.md,
  ]
---

# CI satellite AO batch 8 — finalize

> **🔒 GATED, not draft.** `depends_on: [ci_satellite_ao_dispatch_batch8_2026_08_09]` + `gate_on_depends: true` holds
> both todos below until batch 8's one todo is `done`. `sequential: true` because archival must run after
> reconciliation.

## Todos

- [ ] [REVIEW] P1. **Reconcile batch-8 todo 1's source doc.** Batch-8 todo 1 ends with `Source:` naming
      `issues/assigned_role_devops_invalid_value_corpus_wide_2026_08_08.md`. Flip that doc's `[DOC] P3` checkbox to
      `[x]` citing the batch-8 commit that shipped it — **verify the cited commit exists and is an ancestor of
      `origin/live-defi-rollout` before citing it** (`git merge-base --is-ancestor`). This is that source doc's ONLY
      todo, so once flipped it genuinely reaches zero open work — set `status: resolved` on it too (both in the same
      edit). **Done when**: the checkbox is flipped with verified evidence and the doc's `status` reflects zero open
      work.
- [ ] [DOC] P1. **Archive `ci_satellite_ao_dispatch_batch8_2026_08_09.md`** via the standard 6-step ritual (CLAUDE.md §
      plan archival) — and since todo 1 above should leave
      `issues/assigned_role_devops_invalid_value_corpus_wide_2026_08_08.md` with zero open work too, archive that doc
      alongside it (per `task_template.md` §4's "(4) for a batch-style extraction plan, also check each SOURCE doc"
      rule) → add the archive banner(s) → grep the corpus for every referrer of
      `ci_satellite_ao_dispatch_batch8_2026_08_09` AND `assigned_role_devops_invalid_value_corpus_wide_2026_08_08` and
      repoint each to its archived path → clear `locked_by` (already empty; confirm). **Done when**: both docs are in
      `plans/archive/2026_08/`, every corpus referrer resolves, `check_reference_paths.py` has not regressed, and this
      finalize doc is archived alongside them in the same commit.

## Codex SSOTs

- `/codex/11-project-management/doc-frontmatter-schema.md` — `assigned_role` field definition
- `/codex/11-project-management/` — archival ritual, issue-doc lifecycle
- `plans/active/task_template.md` §4 — the finalize-plan-coverage rule this plan satisfies

## Progress Log

- **2026-08-09** — Drafted alongside `ci_satellite_ao_dispatch_batch8_2026_08_09.md`. Authored `status: active` per the
  established no-double-gate precedent; batch 8 itself is also authored `status: active` per this task's explicit
  dispatch instructions.
