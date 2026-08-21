---
doc_type: plan
title: Data-status cell-grid re-architecture — finalize (verify evidence + archive)
summary: >-
  Gated closeout for `data_status_cell_grid_rearchitecture_2026_07_18.md` — machine-held via `depends_on` +
  `gate_on_depends: true` until all 5 of its RECLASSIFY-extracted todos (3, 5, 6, 7, 8) are done. Re-verifies every
  `[x]` evidence citation (the source plan is self-contained, not a batch extraction from other docs, so this
  re-checks the plan's OWN checkboxes rather than reconciling into a different owner), re-checks whether the
  Phase-2/todo-8 dependency for todo 6's honest done-when has actually cleared, then archives the source plan via the
  standard 6-step ritual.
status: active
nature: process
asset_group: [ui]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ui, ao-dispatch, close-out, cell-grid, oom, archival]
related:
  [
    /plans/active/data_status_cell_grid_rearchitecture_2026_07_18.md,
    /plans/active/ui_consolidated_closeout_2026_07_30.md,
  ]
created: "2026-08-21"
last_updated: "2026-08-21"
parent_epic: deployment_and_user_management_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [data_status_cell_grid_rearchitecture_2026_07_18]
gate_on_depends: true
source: >-
  na-eligibility-audit 2026-08-21 (ui tranche) RECLASSIFY-whole-doc of
  `data_status_cell_grid_rearchitecture_2026_07_18.md`, per `task_template.md` §4's finalize-plan-coverage rule.
assigned_role: infra
effort: low
sequential: true
drift_direction: advance-docs
context_scope:
  [
    /plans/active/data_status_cell_grid_rearchitecture_2026_07_18.md,
    /codex/05-infrastructure/deployment-observability.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
---

# Data-status cell-grid re-architecture — finalize

> **Machine-gated on `data_status_cell_grid_rearchitecture_2026_07_18.md`** (`depends_on` + `gate_on_depends: true`) —
> holds until that plan's todos 3, 5, 6, 7, 8 are all `[x]`. `sequential: true` because evidence-verification (todo 1)
> must land before the codex-drift check (todo 2) and archival (todo 3) — same file, real ordering.

## Todos

- [ ] [REVIEW] P2. **Re-verify every evidence citation in the source plan's own checkboxes** (self-contained plan —
      no other doc's checkbox to reconcile into). For each of todos 3/5/6/7/8, confirm the cited `<repo>@<sha>` is a
      real commit and is an ancestor of `origin/live-defi-rollout` (`git log --oneline` / `git merge-base
      --is-ancestor`), that todo 6's load-test result actually cites a measured p99 < 4 GiB (do not accept "done" on
      Bound alone per that todo's own stated honest-done-when), and that todo 7's codex edit to
      `deployment-observability.md` accurately describes the shipped (not designed-but-unshipped) cell-grid
      architecture. Done-when: all 5 citations independently confirmed real, or a discrepancy is filed and the
      source checkbox corrected.
- [ ] [REVIEW] P2. **Re-check todo 6's Phase-2 dependency + any newly-surfaced follow-up.** Todo 6's own text says
      its honest done-when is unmet "until either todo 8 (streaming aggregation) ships or a real production load
      test proves the worst-case stays under the 4 GiB limit" — confirm which path actually closed it, and if todo 8
      shipped, confirm todo 6 was re-run AFTER todo 8 landed (not stale-closed against the pre-todo-8 code). If any
      deferred/excluded item surfaced during execution (e.g. a follow-up the ready-to-apply spec didn't anticipate),
      spin it into a new tracked todo/plan rather than leaving it as prose.
- [ ] [DOC] P3. **Archive the source plan** — once todos 1-2 above confirm every checkbox is real and `[x]`, run the
      standard 6-step archival ritual on `data_status_cell_grid_rearchitecture_2026_07_18.md` (move to
      `plans/archive/2026_08/`, add the exact-successor banner, fix every corpus referrer —
      `ui_consolidated_closeout_2026_07_30.md` Track 1 Sources cites it by name and needs its link updated to the
      archived path). Distinct `[DOC]` tag from todo 1/2's `[REVIEW]` tag per `task_template.md`'s same-tag-same-
      priority `/done`-collision finding (2026-07-31).

## Progress Log

- **2026-08-21**: Authored alongside the RECLASSIFY-whole-doc flip of
  `data_status_cell_grid_rearchitecture_2026_07_18.md` (na-eligibility-audit, ui tranche).
