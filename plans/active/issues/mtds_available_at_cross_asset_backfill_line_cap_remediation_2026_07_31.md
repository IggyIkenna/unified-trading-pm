---
doc_type: issue
title:
  mtds_available_at_cross_asset_backfill_2026_07_13.md is over its 1000-line hard cap (1003/1000) — needs archival/split
summary: >-
  `plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md` is at 1003 lines, over `check_line_caps.sh`'s
  1000-line hard cap for `plans/active/*.md`. Not yet a scoped-commit blocker (the SCOPED prek gate only refuses a
  commit that stages the over-cap file itself; the full-corpus baseline mode currently tolerates it as pre-existing
  debt), but it blocks any future todo that needs to ADD content to this plan (a new P3 retrofit todo was deferred out
  of it for exactly this reason — see
  `plans/active/issues/dp_consolidator_scheduler_paused_tradfi_recurrence_2026_07_31.md`, now archived) and it is a
  genuinely large Progress Log read for every `/plan-reconcile`/`/ag-closeout-audit` sweep. Per the sibling prediction
  issue's own finding, prediction's todos all read `[x]` except the still-open apply/resume pair (gated on the same
  pause/apply/resume protocol as tradfi); tradfi is likewise all done except apply/resume — so most of the plan's
  historical Progress Log entries document already-CLOSED lanes and are archival candidates, not live work.
status: open
nature: issue
asset_group: [tradfi, prediction]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [plan-hygiene, line-cap, archival, manifest-consolidator]
related:
  [
    /plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md,
    /plans/archive/issues/dp_consolidator_scheduler_paused_tradfi_recurrence_2026_07_31.md,
    /plans/archive/issues/dp_consolidator_scheduler_paused_prediction_recurrence_2026_07_31.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: 2026-07-31
parent_epic: manifest_master
assigned_vm: planning
locked_by:
priority: P3
resolved_by:
source: >-
  Deferred from plans/active/issues/dp_consolidator_scheduler_paused_tradfi_recurrence_2026_07_31.md's "Recommended
  decision" § follow-up 2 (2026-07-31) per the archival-ritual requirement that a DEFERRED prose item be migrated into a
  real tracked todo before that doc archives.
execution_scope: orchestrator-agent
drift_direction: correct-docs
depends_on: []
last_updated: 2026-07-31
---

# mtds_available_at_cross_asset_backfill_2026_07_13.md line-cap remediation

## What I found

`plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md` is 1003 lines, 3 over `check_line_caps.sh`'s
1000-line hard cap for `plans/active/*.md` (see `/codex/11-project-management/` line-cap policy, enforced via
`scripts/plan-hygiene/check_line_caps.sh`). It is not currently a HARD gate failure (full-corpus mode tolerates
pre-existing debt against the shrinking-ratchet baseline in `line_caps_baseline.yaml`), but it already blocked one
concrete piece of work: `dp_consolidator_scheduler_paused_tradfi_recurrence_2026_07_31.md`'s pause-retrofit todo had to
be filed and resolved as a standalone issue doc instead of a todo inside this plan, purely because staging an edit to an
over-cap file trips `check_line_caps.sh`'s SCOPED (prek) mode.

The plan's own Progress Log records (per the sibling prediction issue's finding, mirrored here for tradfi): every
prediction todo reads `[x]` except the still-open apply/resume pair; every tradfi todo reads `[x]` except its own
still-open apply/resume pair. Both open pairs are gated on the same pause/apply/resume backfill protocol (currently
mid-flight, tracked live in the plan itself). The bulk of the plan's ~1000 lines is Progress Log narrative for lanes
that are already fully closed (snapshot, cron-pause, dry-run, bundled/non-bundled split, sports) — good candidates to
extract into an archived history doc per this workspace's standard split pattern, leaving the still-open apply+resume
work in a trimmed active plan.

## Why it matters

An over-cap active plan is a standing tax on every corpus-wide sweep (`/plan-reconcile`, `/ag-closeout-audit`,
`/na-eligibility-audit`) that re-reads it in full, and it structurally blocks any future todo that needs to add content
to the plan itself (as already happened once). Left alone, this will keep generating standalone-issue-doc workarounds
instead of a normal in-plan todo.

## Recommended decision

Split the plan: extract the closed lanes' Progress Log history into an archived companion doc, leave the still-open
tradfi/prediction apply+resume todos (plus the still-open sports lane, if any) in a trimmed
`plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md` under the 1000-line cap. Do this only once the
plan's own todos are stable enough to avoid mid-split churn (a live in-flight pause/apply/resume protocol is currently
running against it) — check the plan's own status before starting.

## Todos

- [ ] [PLAN] P3. Split `plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md`: extract fully-closed lanes'
      Progress Log entries into an archived history doc (standard split pattern, `superseded_by`/pointer back from the
      trimmed plan), leaving the still-open apply+resume todos (and any other still-open lane) in the active plan,
      landing it back under the 1000-line hard cap. Verify no todo is currently `locked_by`/mid-dispatch before
      splitting. (repo: unified-trading-pm)
