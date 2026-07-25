---
doc_type: plan
title: Sports closeout batch 1 — finalize (reconcile parent checkboxes + resolve spun-off issues + archive)
summary: >-
  MOVED. This doc is now archived at plans/archive/2026_07/sports_closeout_batch1_finalize_2026_07_24.md — both its
  todos were verified done and it was archived via the standard 6-step ritual on 2026-07-25. This stub exists only
  because a concurrent commit (`9aed72662`) landed the archive-path copy but silently dropped the `git rm` half of the
  move, and the `git rm` needed to delete this stale duplicate is blocked for autonomous workers by agent-orchestrator's
  `block_destructive_commands.py` guardrail (correctly — the operator should confirm a delete, not an autonomous
  worker). Queued for the operator in plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md — this
  file should simply be `git rm`'d once confirmed.
status: complete
nature: process
asset_group: [sports]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [sports, ao-dispatch, close-out, batch-1, archival, stale-duplicate-stub]
related:
  [
    /plans/archive/2026_07/sports_closeout_batch1_finalize_2026_07_24.md,
    /plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md,
  ]
created: "2026-07-24"
last_updated: "2026-07-25"
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0
estimate_calibrated_ai_days: 0
locked_by:
locked_since:
supersedes:
superseded_by: sports_closeout_batch1_finalize_2026_07_24
depends_on:
source: >-
  Stale-duplicate stub created 2026-07-25 after a concurrent commit half-landed this doc's archival move — see summary.
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
---

# Sports closeout batch 1 — finalize (STALE DUPLICATE — see plans/archive/2026_07/sports_closeout_batch1_finalize_2026_07_24.md)

> **⚠️ STALE DUPLICATE.** The real, current version of this doc lives at
> `plans/archive/2026_07/sports_closeout_batch1_finalize_2026_07_24.md` (archived 2026-07-25, both todos verified done).
> This file is a leftover from a half-landed `git mv` (a concurrent commit picked up the archive-path ADD but not this
> file's DELETE). Safe to `git rm` — queued for the operator since `git rm` is guardrail-blocked for autonomous workers.

## Todos

- [ ] [OPERATOR] P3. `git rm plans/active/sports_closeout_batch1_finalize_2026_07_24.md` (this file) — the real content
      is at `plans/archive/2026_07/sports_closeout_batch1_finalize_2026_07_24.md`. **Done when**: this file no longer
      exists.
