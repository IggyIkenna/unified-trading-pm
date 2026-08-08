---
doc_type: issue
title:
  quickmerge's rebase-conflict detection may not flag same-file, non-overlapping-line-range concurrent edits — a
  same-file, different-section near-simultaneous edit can silently blind-overwrite the earlier writer's content instead
  of hitting a structured QUICKMERGE_BLOCKED path.
summary: >
  Live-observed 2026-08-08 ~03:00-03:11 UTC: two (arguably three) near-simultaneous commits landed on the SAME file,
  `unified-trading-pm/plans/active/issues/fleet_promoter_glue_runner_stall_2026_08_06.md`, within an 11-minute window.
  Commit `c886da0f6` (2026-08-08T03:07:35Z, interactive session slot-1) landed a substantial Progress Log entry + a
  todo-closing annotation with real engineering content (sync_backlog_to_db root-cause, 12 disabled systemd timers, a
  GCP_PROJECT_ID env var fix). Commit `d52a11058` (2026-08-08T03:10:55Z, slot-4, via `Quickmerge: agent`) landed ~3
  minutes later, and its diff shows it based its edit off the PRE-`c886da0f6` version of the file — it blindly clobbered
  `c886da0f6`'s entire Progress Log entry and todo annotation with its own (also legitimate, but unrelated) finding,
  instead of hitting the expected `QUICKMERGE_BLOCKED` conflict path or an append-alongside merge. A THIRD, prior
  instance of this exact class already happened in the same file: commit `f8f3b7435` ("fix(cicd): reconcile
  make_stub.py's semver-agent.yml handling") is literally titled "(lost to concurrent-session collision)" in its own
  message, i.e. whoever landed it already noticed and named the same failure mode inline.

  Verified via direct `git show c886da0f6` / `git show d52a11058` on the same file path: nothing is destroyed in git
  HISTORY (both commits' content is fully recoverable via reflog/git-log), but the doc's CURRENT working content only
  reflected `d52a11058` — `c886da0f6`'s content was silently gone from the live file, and would have been permanently
  lost if not caught by a review discipline sweep. (`c886da0f6`'s dropped content was restored as a documentation-only
  follow-up, commit `131188f6d` — that restoration is NOT this issue's scope; this issue tracks the underlying tooling
  defect that caused the loss, not the one-off content recovery.)

  Why this matters beyond this one file: the CLAUDE.md-documented quickmerge contract
  (`/codex/08-workflows/ci-cd-flow.md`, "Behind-remote / tag conflict" section) states genuine same-file conflicts
  should hit a structured `QUICKMERGE_BLOCKED` exit for recovery, not a blind overwrite. This instance (and the two
  adjacent ones in the same file, same 11-minute window) suggests quickmerge's rebase-conflict handling may not always
  correctly detect a genuine same-file near-simultaneous edit as a conflict — possibly because both edits landed on
  DIFFERENT, non-overlapping line ranges within the same file (so git's own merge/rebase machinery sees no textual
  conflict and silently takes the later ref's full-file state), which is a distinct failure mode from a literal
  same-line conflict and may not be caught by whatever quickmerge's current conflict-detection logic checks.

  Blast radius: this affects EVERY repo and every agent using quickmerge for `docs(plans):` commits — any two agents
  editing DIFFERENT sections of the same plan/issue doc within a similar tight window could silently lose one side's
  edits the same way, without any error, warning, or `QUICKMERGE_BLOCKED` signal to either agent.
status: open
nature: notes
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [backend, git-discipline, quickmerge, cross-cutting, ci-cd, conflict-detection]
related: [/plans/active/issues/fleet_promoter_glue_runner_stall_2026_08_06.md]
created: 2026-08-08
author: main (direct instruction, relayed by data_engineering worker slot-7)
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
drift_direction: NA
source:
  review agent finding, 2026-08-08T03:19Z, during a live discipline sweep of unified-trading-pm commit history; filed
  per direct instruction from main (bypasses backlog — a real, recurring cross-cutting defect for engineering
  investigation; priority P1 given the repeat rate, not urgent-blocking since nothing is currently destroyed in git
  history).
resolved_by:
depends_on: []
locked_by:
context_scope: [/codex/08-workflows/ci-cd-flow.md, unified-trading-pm/scripts/quickmerge.sh]
---

## What I found

Three near-simultaneous commits landed on the same file
(`unified-trading-pm/plans/active/issues/fleet_promoter_glue_runner_stall_2026_08_06.md`) within an 11-minute window on
2026-08-08:

1. `f8f3b7435` — commit message itself titled "(lost to concurrent-session collision)", i.e. a prior instance of this
   same class already happened and was noted inline by whoever landed it.
2. `c886da0f6` (2026-08-08T03:07:35Z, interactive session slot-1) — landed a substantial Progress Log entry + a
   todo-closing annotation with real engineering content.
3. `d52a11058` (2026-08-08T03:10:55Z, slot-4, via `Quickmerge: agent`) — landed ~3 minutes later; its diff shows it
   based its edit off the PRE-`c886da0f6` version of the file, blindly clobbering `c886da0f6`'s entire Progress Log
   entry and todo annotation with its own (also legitimate, but unrelated) finding, instead of hitting the expected
   `QUICKMERGE_BLOCKED` conflict path or an append-alongside merge.

Verified via `git show c886da0f6 -- <path>` and `git show d52a11058 -- <path>`: both commits' content is fully
recoverable from git history (nothing destroyed at the git-object level), but the file's live working-tree content after
`d52a11058` landed only reflected `d52a11058` — `c886da0f6`'s content was silently absent from the live doc.

## Why it matters

The documented quickmerge contract (`/codex/08-workflows/ci-cd-flow.md` § "Behind-remote / tag conflict") states a
genuine same-file conflict should hit a structured `QUICKMERGE_BLOCKED` exit, recovered via the autostash recipe — never
a blind overwrite. Two edits on DIFFERENT, non-overlapping line ranges within the same file produce NO textual conflict
under git's own line-level merge/rebase machinery, so a rebase silently takes the later ref's full-file state with no
warning to either agent. This is a distinct failure mode from a literal same-line conflict, and there's no evidence
quickmerge's current conflict-detection logic (whatever it actually checks pre-push) catches it. Every repo and every
agent shipping `docs(plans):` commits through quickmerge is exposed — any two agents editing different sections of the
same plan/issue doc in a tight window can silently lose one side's edits, with zero error or `QUICKMERGE_BLOCKED` signal
raised to either party. This has now recurred at least 2-3 times in the same file in one 11-minute window, meeting the
"recurring" bar for a P1 rather than a one-off.

## Recommended decision

Investigate whether quickmerge's rebase-conflict detection correctly flags same-file, non-overlapping-line-range
concurrent edits (not just literal same-line conflicts) as requiring a structured merge/`QUICKMERGE_BLOCKED` path
instead of a silent last-writer-wins overwrite. Reproduce using two near-simultaneous quickmerge commits to different
sections of the same doc file if the mechanism is unclear from reading `quickmerge.sh` source directly. If confirmed,
the fix likely needs quickmerge to diff the target file's pre-edit state against the actual `origin` HEAD at push time
(not just rely on git's line-level rebase conflict detection) and hard-block if the file changed underneath the agent's
read, regardless of whether the specific lines textually conflict.

## Todo

- [ ] [BACKEND] P1. Investigate whether quickmerge's rebase-conflict detection correctly flags same-file,
      non-overlapping-line-range concurrent edits (not just literal same-line conflicts) as requiring a structured
      merge/`QUICKMERGE_BLOCKED` path instead of a silent last-writer-wins overwrite. Reproduce using two
      near-simultaneous quickmerge commits to different sections of the same doc file if the mechanism is unclear from
      reading the `quickmerge.sh` source. If confirmed, the fix likely needs quickmerge to diff the target file's
      pre-edit state against the actual `origin` HEAD at push time (not just rely on git's line-level rebase conflict
      detection) and hard-block if the file changed underneath the agent's read, regardless of whether the specific
      lines textually conflict. (repo: unified-trading-pm)

## Progress Log

- 2026-08-08: Issue filed per direct instruction from main, relayed to data_engineering worker slot-7 during
  `sports_taxonomy_p1_capture_and_contracts-019` boot. No investigation performed yet — todo above is unstarted.
