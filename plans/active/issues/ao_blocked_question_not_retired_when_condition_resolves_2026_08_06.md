---
doc_type: issue
title:
  "A BLOCKED question is never retired when its own condition resolves — the task is completed by another agent, the
  underlying plan/issue doc is archived, or the external blocker clears — so a worker sits in a wait-loop for hours on a
  question that no longer has an answer worth giving"
summary: >-
  Live on prod slot 2 (2026-08-06): `BLK-4781b9af` asked whether to admin-merge unified-api-contracts PR #861, whose
  quality-gates-v2 required check was never reported. It was raised 2026-08-05 21:45Z. The condition cleared on its own
  roughly 11 hours later — PR #861 was CLOSED as superseded and promote PRs #863/#864/#865/#866 all MERGED between
  08:21Z and 09:15Z with quality-gates-v2 GREEN on main (run 31088356230, 09:15:54Z) — but the question stayed OPEN in
  `blocked_queue`, and slot 2 stayed BLOCKED, looping a "/loop wakeup" wait for ~15h and reporting "STEP 8: ~6.5h
  elapsed, still no answers" then "~11 hours". Nothing in the orchestrator ever re-checks whether a standing blocked
  question still means anything. The operator's framing (2026-08-06) generalises it: when an agent posts a blocked
  question and that task is then completed by some other agent, or its issue doc / plan doc is archived, the blocked
  question should be REMOVED as no longer relevant. Today the only exit from `blocked_queue` is a human answering it, so
  the queue accumulates questions whose subject no longer exists — and each one can hold a slot hostage. At the time of
  filing the queue held 30 entries, several visibly `[OPERATOR] P2/P3` items whose parent work has moved on.
status: open
nature: issue
asset_group: [ao]
scope: [engineer]
stage: [meta]
repos: [agent-orchestrator]
tags: [agent-orchestrator, blocked-queue, worker-liveness, dispatch, staleness, operator-reported]
related:
  [
    /plans/active/issues/ao_worker_context_saturation_unrecoverable_2026_08_06.md,
    /codex/04-architecture/agent-orchestrator-alerting.md,
  ]
created: 2026-08-06
author: agent
last_updated: 2026-08-06
priority: P2
parent_epic: orchestrator_master
source:
  "operator-directed, interactive session (slot 2 host `hk`) — operator ruling while unblocking slot 2: 'when agent is
  working on task and posts a blocked question and if that task is completed by some other agent or its issue doc or
  plan doc is archived then that blocked question should be removed as its no longer relevant'"
assigned_vm: NA
execution_scope: local-only
estimate_class: brand-new
estimate_baseline_ai_days: 0.8
estimate_calibrated_ai_days: 0.8
assigned_role: infra
drift_direction: advance-code
resolved_by:
locked_by:
depends_on: []
---

# Blocked questions are never retired when their condition resolves

## Why this matters

A blocked question is the only thing standing between a worker and its next task, and it has exactly one exit today: a
human answers it. Every other way the question can stop mattering — the task got done by someone else, the doc got
archived, the external blocker cleared — leaves the question sitting in `blocked_queue` forever and the worker looping.
The cost is not the queue entry; it is the slot. Slot 2 burned ~15h of wall-clock on `BLK-4781b9af` after its answer had
become "nothing to do".

It also corrupts the operator's signal: a queue of 30 blocked questions where an unknown fraction are already moot
trains the operator to skim it, which is exactly how a genuinely urgent one gets missed.

## Todos

- [ ] [INFRA] P1. **Auto-retire a blocked question when its owning task reaches a terminal state.** Key on the
      question's `task_id` (`blocked_queue` entries already carry one, e.g. `agt-4fdce1` / `agt-d69016`): when that task
      goes `done`/`cancelled` — by ANY slot or agent, not just the one that raised the question — resolve the question
      with a machine disposition (`auto_retired_task_terminal`) rather than leaving it pending. Record who completed it
      so the audit trail shows why it was retired, and make sure retiring it releases the raising slot instead of
      leaving it BLOCKED on a question that no longer exists.

- [ ] [INFRA] P1. **Auto-retire when the question's underlying plan/issue doc is archived.** Blocked questions cite a
      plan or issue doc (`plan_ref`, or the doc named in the question text). The archival ritual
      (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`) moves the doc out of `plans/active/`; that
      move must sweep any blocked question bound to it. Decide the disposition explicitly — retiring silently is wrong
      if the question was the very thing gating the archival, so the sweep should refuse to retire a question whose doc
      was archived WITH that question still unanswered, and instead flag the archival as premature.

- [ ] [INFRA] P2. **Add a periodic staleness re-check for standing questions.** Neither trigger above would have caught
      `BLK-4781b9af`: its task was still open and no doc was archived — the external world (GitHub) simply moved on.
      Give a question an optional machine-checkable `recheck` predicate (for a CI/PR-shaped question: is the PR still
      open, is the required check still missing) evaluated on a timer, and auto-retire with evidence when the predicate
      says the condition cleared. Where no predicate is expressible, at minimum surface an age on the dashboard so a
      15h-old question is visibly abnormal.

- [ ] [INFRA] P2. **Bookend every auto-retirement in Slack.** `/codex/04-architecture/agent-orchestrator-alerting.md`
      requires that every actionable alert that paged an OPEN gets a ✅ CLOSE bookend in-channel. A question that paged
      when raised and is later auto-retired must post its close with the reason (task done by slot N / doc archived /
      condition cleared), or the channel keeps showing an open page for a question that no longer exists.

- [ ] [INFRA] P3. **Sweep the existing queue once the above lands.** 30 entries were pending at filing time, including
      several `[OPERATOR]` items whose parent work has since moved. Run the new retirement logic over the backlog as a
      one-off and report how many were already moot — that count is the honest measure of how much of the operator's
      blocked queue was noise.

## Progress Log

### 2026-08-06 — filed (interactive session, slot 2 host `hk`)

Filed on an explicit operator ruling while unblocking slot 2. Slot 2 was holding four questions; `BLK-4781b9af` was
verified moot before answering (PR #861 CLOSED/superseded, #863-#866 MERGED, quality-gates-v2 green on
unified-api-contracts main) and was answered "RESOLVED — stale question, no action needed" rather than acted on. The
other three (`BLK-136e69bf` LA_LIGA_2, `BLK-0e7e0794` UPBIT, `BLK-5eeacb63` duplicate finalize plans) were each verified
against the repo and answered on their merits — all three were genuine, so this issue is specifically about the
retirement path, not about question quality.

Incidental observation while checking the UAC promotion, NOT part of this issue and not yet triaged: the
`main-backmerge-to-ldr` run on unified-api-contracts `main` showed `pending` at 3h39m elapsed.
