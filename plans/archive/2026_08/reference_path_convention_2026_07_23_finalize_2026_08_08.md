---
doc_type: plan
title: Cross-reference path convention cleanup backlog — finalize
summary: >-
  Gated closeout for `reference_path_convention_2026_07_23.md` — machine-held via `depends_on` + `gate_on_depends: true`
  until all 4 of that doc's remaining todos (format-violation backlog, existence-violation backlog, the
  sports_satellite_batch2 body-prose fix, and the 2026-08-03 baseline-drift re-measurement) are done. Confirms both
  shrinking-ratchet baselines actually reached (or were re-baselined toward) zero before archiving.
status: complete
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-hygiene, cross-doc-links, close-out, archival]
related:
  [
    /plans/archive/issues/reference_path_convention_2026_07_23.md,
    /plans/epics/agent_operating_framework_master.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-08"
last_updated: "2026-08-17"
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: infra
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
context_scope:
  [
    /plans/archive/issues/reference_path_convention_2026_07_23.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/11-project-management/cross-reference-path-convention.md,
    /plans/PLAN_FORMAT.md,
    /plans/active/task_template.md,
  ]
supersedes:
superseded_by:
depends_on: [reference_path_convention_2026_07_23]
gate_on_depends: true
source: >-
  /na-eligibility-audit round7 RECLASSIFY sweep, 2026-08-08 — required companion per `plans/active/task_template.md`
  §4's finalize-plan-coverage rule (every AO plan needs a paired gated finalize).
---

# Cross-reference path convention cleanup backlog — finalize

> **✅ ARCHIVED 2026-08-17** — all 3 todos done, parent doc closed out.

> **Machine-gated on `reference_path_convention_2026_07_23.md`** (`depends_on` + `gate_on_depends: true`) — the
> dispatcher will not queue any todo below until all 4 of the parent doc's remaining todos are `done`.

## Todos

- [x] ✅ [REVIEW] P2. **DONE 2026-08-17 (slot 17)** — **Confirm the two shrinking-ratchet baselines
      (`format_count`/`existence_count` in `scripts/plan-hygiene/reference_paths_baseline.yaml`) actually moved, and by
      how much.** Live-ran `check_reference_paths.py` at repo root: `format_count: 0 (baseline 0)`,
      `existence_count: 34 (baseline 34)` — both PASS with zero slack, matching the parent doc's own last-recorded
      numbers (2026-08-10 measurement, no drift since). Confirmed on a live run, not the parent doc's own claim taken at
      face value. `unified-trading-pm@<commit-pending>`.
- [x] ✅ [REVIEW] P2. **DONE 2026-08-17 (slot 17)** — **Verify the sports_satellite_batch2 body-prose fix was applied
      AFTER the file's split landed.** No split occurred — the source doc
      (`plans/archive/2026_07/sports_satellite_ao_dispatch_batch2_2026_07_24.md`) was archived WHOLE at 1000L (per the
      parent doc's own 2026-08-15 Progress Log entry: the split-first premise went moot because
      `check_line_caps.sh`'s 1000L hard cap is scoped to `plans/active/` + `plans/epics/` only — once archived, the cap
      no longer applies). Confirmed the fix and the archived-whole file coexist cleanly at HEAD: line 400 of that file
      reads `/plans/archive/issues/fss_bookmaker_dispersion_dead_code_overwrites_best_odds_2026_07_25.md`, and that
      target file exists on disk. `unified-trading-pm@<commit-pending>`.
- [x] ✅ [DOCS] P2. **DONE 2026-08-17 (slot 17)** — **Archived the parent doc per the 6-step ritual.** Confirmed 0 open
      `- [ ]` todos remained (all 5 already `[x]`). Added the archival banner + `status: complete`, then `git mv`'d to
      `plans/archive/issues/reference_path_convention_2026_07_23.md` (flat, per `doc_type: issue` +
      `issue-doc-lifecycle.md`). Corpus-wide referrer sweep: 33 files cite the slug; of those, 6 carried a real
      leading-slash path to the old active location (not a bare-slug prose mention) — repointed all 6 to the archived
      path: `/plans/active/infra_consolidated_closeout_2026_07_25.md`,
      `/plans/active/issues/plan_quality_four_line_defense_architecture_2026_07_23.md` (x2),
      `/codex/11-project-management/cross-reference-path-convention.md` (x2),
      `cursor-configs/skills/plan-reconcile/SKILL.md`. The remaining 27 hits are either bare-slug prose mentions with no
      matchable path (won't dangle), already-deliberately-de-fanged example text (per the parent doc's own 2026-08-16
      Progress Log), or citations inside already-archived docs (frozen historical snapshots, out of scope per this
      workspace's archival convention — only active-corpus referrers get repointed). No open lock to clear. This
      finalize doc's own `related:`/`context_scope` fields above are already repointed at the new path.
      `unified-trading-pm@<commit-pending>`.

## Codex SSOTs

`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` (6-step ritual) ·
`/codex/11-project-management/cross-reference-path-convention.md` · `plans/PLAN_FORMAT.md` ·
`plans/active/task_template.md` §4 (finalize-plan-coverage rule)

## Progress Log

- **2026-08-08**: Drafted alongside the parent doc's `na-eligibility-audit round7 RECLASSIFY` flip from
  `assigned_vm: NA` to `planning`. `status: active` immediately (not `draft`) — machine-held from actually dispatching
  via `depends_on` + `gate_on_depends: true` until the parent doc's 4 remaining todos are done.
- **2026-08-17 (slot 17)**: All 3 todos done same-session — parent doc's own 5 todos were already `[x]` (confirmed via
  a fresh `check_reference_paths.py` run, not stale claims), the sports_satellite_batch2 fix verified coexisting with
  the whole-file archival, and the parent doc archived per the 6-step ritual with a 6-referrer corpus repoint. This
  finalize doc itself now has 0 open todos and is unlocked — archived in the SAME commit as this Progress Log entry
  (single-repo/mode-1 same-commit flip+archival, sanctioned per
  `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` § "Single-repo (mode-1) finalize plans").
