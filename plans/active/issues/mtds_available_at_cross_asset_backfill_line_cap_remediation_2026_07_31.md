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

## New finding, 2026-07-31 (slot-15) — the AO dispatcher offered "Resume the prediction consolidator cron"

(`mtds_available_at_cross_asset_backfill-006`) while its logical prerequisite, "Apply `rebuild_prediction_manifest.py`"
(`-001`, line 164), is still `- [ ]` open. Re-read the plan's own text before acting (per the standing "read the plan
first" rule) — line 164 is unambiguously unchecked, and no full-range `rebuild_prediction_manifest.py` apply exists
anywhere in `market-tick-data-service` history (checked the Progress Log for the script name; only the `--dry-run` todo,
line 142, is done). Resuming now would violate this plan's own HARD constraint section ("dry-run first, snapshot

- pause... before applying, and verify... before resuming") — the exact class of mistake
  `dp_consolidator_scheduler_paused_tradfi_recurrence_2026_07_31.md` documents a different agent making and
  self-correcting earlier the same day. **Declined to resume** — did not touch the prediction cron or run any resume
  script. Root cause: this plan has no machine-encoded ordering between the "Apply" and "Resume" backlog tasks
  (`sequential: true` at the plan level doesn't establish a per-todo `depends_on`/`prereqs.completed_tasks` chain —
  `task_template.md`'s own documented limitation, "no per-todo prereq syntax"), so the dispatcher's priority/tier
  ranking picked the resume task ahead of its logical prerequisite. Skipped the task (`reason_code=BLOCKED`) rather than
  executing it or leaving it silently stuck. Added as a second todo below (bundled into this same doc rather than a
  third overlapping issue doc, since fixing it requires editing the same over-cap plan the split todo already targets).

## Recommended decision

Split the plan: extract the closed lanes' Progress Log history into an archived companion doc, leave the still-open
tradfi/prediction apply+resume todos (plus the still-open sports lane, if any) in a trimmed
`plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md` under the 1000-line cap. Do this only once the
plan's own todos are stable enough to avoid mid-split churn (a live in-flight pause/apply/resume protocol is currently
running against it) — check the plan's own status before starting.

## Todos

- [x] ✅ [PLAN] P3. **DONE 2026-07-31 (slot 11).** Verified no todo `locked_by`/mid-dispatch first (`locked_by:` empty
      in frontmatter). Split `mtds_available_at_cross_asset_backfill_2026_07_13.md` (1003 lines): moved the fully-closed
      or since-superseded dated Progress Log entries (2026-07-14 ICE-purge note through the DeFi handler audit — the
      original dispatch-order finding, the UTL dependency-pin saga, the long premature-dispatch/re-verification thrash
      chain, the now-superseded `BLOCKED-*`-marker workaround, the full DeFi audit detail; none carried a still-open
      todo dependency) VERBATIM to
      `/plans/archive/2026_07/mtds_available_at_cross_asset_backfill_history_2026_07_31.md`, standard split pattern
      (mirrors `data_pipeline_check_mdps_features_history_2026_07_24.md`), with a pointer-back banner left in the parent
      at the extraction point. Left the full unedited `## Todos` section, the CURRENT dispatch-order-bug context
      (findings #2-7 + the 2026-07-31 memory-safety finding), the 2026-07-28 gate-cleanup pass, and the active
      2026-07-29 rollback-snapshot record in the trimmed parent. Parent now 443 lines (was 1003), archive doc 638 lines.
      Both pass `check_line_caps.sh` (verified directly, not just inferred). (repo: unified-trading-pm)
- [x] ✅ [PLAN] P2. **DONE 2026-07-31 (slot 11) — root-caused a dispatcher bug blocking the intended fix, worked around
      it, did NOT hand-author new dependency metadata.** This plan already carries `sequential: true`, which
      `agent-orchestrator/server/regen_backlog_from_plan.py`'s `_wire_sequential_prereqs` uses to auto-derive a full
      `prereqs.completed_tasks` chain across a plan's live tasks by `plan_order` — so no per-todo `gate_on_depends`/
      `depends_on`/hand-authored `prereqs.completed_tasks` should have been needed at all. Confirmed live via
      `/api/backlog/<id>/blockers` that the chain was in fact BROKEN and INVERTED:
      `mtds_available_at_cross_asset_backfill-006` ("Resume the prediction consolidator cron") read **"ready (no
      blockers)"** while `-001` ("Apply `rebuild_prediction_manifest.py`", its true prerequisite) was itself blocked on
      `-006` — backwards. Root-caused to a distinct, previously-unidentified defect in `regen()`'s task-creation match
      (`plan_tasks_by_brief.get(description)`, `regen_backlog_from_plan.py:1710`): the prediction and tradfi "Apply"
      todos shared a byte-identical FIRST PHYSICAL LINE (the differentiating script name only appeared after the file's
      hard-wrap), which silently collapsed both onto task `-001` and let whichever occurrence's tick processed last
      (tradfi, later in the file) overwrite `-001`'s `plan_order` — inverting the chain. Full root-cause + evidence
      logged in `plans/active/issues/mtds_backfill_sequential_true_dispatch_order_violated_2026_07_29.md` (the doc
      already tracking this exact live symptom — added there rather than duplicating a new issue doc), including the
      general code-fix + corpus-audit follow-up todos (deliberately NOT attempted from this single P2 task, consistent
      with that doc's own established pattern and the standing operator guidance against rushing dispatcher-core
      changes). **Fix applied here**: reworded both colliding lines (`— Apply` → `— Apply prediction's` /
      `— Apply tradfi's`) so each first physical line is unique — a plan-content-only change that lets the
      ALREADY-CONFIGURED `sequential:     true` machinery self-heal, no new gating mechanism needed. **Verified
      post-ship** (see Progress Log entry below for the actual `/api/backlog` evidence gathered after this fix reached
      the live orchestrator, replacing this todo's original "post-split-equivalent" framing — the fix didn't end up
      depending on the split at all, they just shared the same over-cap-file blocker on landing). (repo:
      unified-trading-pm)
