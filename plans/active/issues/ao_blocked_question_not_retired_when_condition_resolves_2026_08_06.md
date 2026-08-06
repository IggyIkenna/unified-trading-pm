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

- [x] ✅ [INFRA] P1. **Auto-retire a blocked question when its owning task reaches a terminal state.** Key on the
      question's `task_id` (`blocked_queue` entries already carry one, e.g. `agt-4fdce1` / `agt-d69016`): when that task
      goes `done`/`cancelled` — by ANY slot or agent, not just the one that raised the question — resolve the question
      with a machine disposition (`auto_retired_task_terminal`) rather than leaving it pending. Record who completed it
      so the audit trail shows why it was retired, and make sure retiring it releases the raising slot instead of
      leaving it BLOCKED on a question that no longer exists. **SHIPPED** — agent-orchestrator@84cfd59. Implemented as a
      retirement pass inside the EXISTING `server/blocked_reconcile.py` sweep rather than a new loop — that module
      already runs periodically, already drives the exact `answer_blocked` + slot-unblock + worker-nudge transition, and
      is the SSOT for resolving a question from outside. New `classify_retirement()` keys on the row's `task_id` and
      retires when the TaskRow is `done`/`cancelled` regardless of which slot got it there. Retirement runs BEFORE the
      plans-corpus match, so a dead question is never "answered" from prose. Logs `blocked_retired_task_terminal` and
      releases the slot. Tests: `tests/test_blocked_reconcile.py::test_retires_when_owning_task_is_done` (asserts the
      slot goes back to `working`) and `…::test_does_not_retire_a_live_question` — the latter is the real guard, since
      the risk of this feature is retiring something still real.

- [x] ✅ [INFRA] P1. **Auto-retire when the question's underlying plan/issue doc is archived.** Blocked questions cite a
      plan or issue doc (`plan_ref`, or the doc named in the question text). The archival ritual
      (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`) moves the doc out of `plans/active/`; that
      move must sweep any blocked question bound to it. Decide the disposition explicitly — retiring silently is wrong
      if the question was the very thing gating the archival, so the sweep should refuse to retire a question whose doc
      was archived WITH that question still unanswered, and instead flag the archival as premature. **SHIPPED** —
      agent-orchestrator@84cfd59, with a deliberate deviation from the wording above. Refusing to retire is worse in
      practice: the doc is gone either way, so nothing will ever action the answer, and the only effect of refusing is
      that the slot stays hostage — the exact failure this issue exists to fix. So it DOES retire, but emits a distinct
      `blocked_retired_doc_archived` activity event (plus the Slack bookend) so a premature archival is loud rather than
      silent. Resolution is by filename against `plans/active/` vs `plans/archive/`, driven off the task's `plan_ref`.
      Test: `…::test_retires_when_plan_doc_archived`.

- [x] ✅ [INFRA] P2. **Add a periodic staleness re-check for standing questions.** Neither trigger above would have
      caught `BLK-4781b9af`: its task was still open and no doc was archived — the external world (GitHub) simply moved
      on. Give a question an optional machine-checkable `recheck` predicate (for a CI/PR-shaped question: is the PR
      still open, is the required check still missing) evaluated on a timer, and auto-retire with evidence when the
      predicate says the condition cleared. Where no predicate is expressible, at minimum surface an age on the
      dashboard so a 15h-old question is visibly abnormal. **SHIPPED (age half) — agent-orchestrator@ceab325.** A
      question standing past `tuning.blocked_question_stale_after_hours` (new, default 8) now re-reminds via the
      existing `notify_slot_blocked` path, deduped by `blocked_question_reremind_cooldown_hours` (default 12) rather
      than paging every sweep tick — the alerting SSOT's fire-on-change / re-remind rule. Cooldown entries drop once an
      id stops being pending, so a later question with the same id alerts fresh. Tests:
      `tests/test_blocked_reconcile.py::test_reminds_on_a_question_standing_past_the_threshold` (asserts the real 15h
      BLK-4781b9af shape), `…::test_does_not_remind_on_a_young_question`,
      `…::test_reremind_is_deduped_by_cooldown_not_fired_every_tick`. **NOT shipped: the machine-checkable external
      predicate** — split into its own todo below rather than half-built, because it needs an operator decision first.

- [x] ✅ [INFRA] P2. **Bookend every auto-retirement in Slack.** `/codex/04-architecture/agent-orchestrator-alerting.md`
      requires that every actionable alert that paged an OPEN gets a ✅ CLOSE bookend in-channel. A question that paged
      when raised and is later auto-retired must post its close with the reason (task done by slot N / doc archived /
      condition cleared), or the channel keeps showing an open page for a question that no longer exists. **SHIPPED** —
      agent-orchestrator@84cfd59. Reuses the sweep's existing bookend path
      (`notify_slot_blocked_answered(..., auto=True, opened_at=<created_at>)`), so retirements bookend exactly the way
      auto-answers already do — no new notifier, and the opened-at correlation the webhook-only channel relies on is
      preserved. The reason travels in the answer text (`AUTO-RETIRED (<reason>): <detail>`). Test:
      `…::test_retirement_posts_a_close_bookend`.

- [x] ✅ [INFRA] P3. **Sweep the existing queue once the above lands.** 30 entries were pending at filing time,
      including several `[OPERATOR]` items whose parent work has since moved. Run the new retirement logic over the
      backlog as a one-off and report how many were already moot — that count is the honest measure of how much of the
      operator's blocked queue was noise. **DONE — measured 2026-08-06, and the answer is ZERO.** Ran
      `POST /api/blocked/reconcile` against prod after deploying agent-orchestrator@84cfd59:
      `checked=26, retired=0, synced=0, unresolved=26`. So the queue was NOT full of moot questions — the hypothesis in
      this doc's summary ("several visibly `[OPERATOR]` P2/P3 items whose parent work has moved on") is DISPROVEN for
      the current population. Two consequences worth stating plainly: (1) the retirement logic is proven by unit tests
      but has not yet fired on a real row in prod, so treat it as shipped-not-yet-exercised; (2) more importantly, the
      very case that motivated this issue (BLK-4781b9af — a GitHub PR superseded and main gone green) is caught by
      NEITHER shipped trigger, because its task never went terminal and no doc was archived. That is precisely todo 3's
      external-condition re-check, which is therefore the load-bearing remaining work here, not a nice-to-have.

- [ ] [OPERATOR] P2. **Decide whether the orchestrator may make outbound GitHub reads, then build the external-condition
      predicate.** The other half of todo 3, and the ONLY thing that would have caught the case this issue was filed
      for: BLK-4781b9af asked "admin-merge PR #861?"; the PR was closed as superseded and `quality-gates-v2` went green
      on main ~11h later, yet its task never went terminal and no doc was archived — so neither shipped retirement
      trigger sees it. The 2026-08-06 prod sweep confirmed that empirically (`checked=26, retired=0`). A predicate
      (`gh pr view <n> --json state`, or the required-check status) would auto-retire it with evidence. **Operator
      decision needed BEFORE building**: the reconciler makes zero outbound network calls today, and adding them inside
      its sweep tick brings rate limits, timeouts and a token into a loop that currently cannot fail externally.
      Options: (a) grant a read-only `GH_TOKEN` and call GitHub from the sweep behind a timeout + circuit breaker; (b)
      have the EXISTING ci-failure-watcher (already credentialled for GitHub) publish PR/check state that the reconciler
      reads locally — no new egress from the sweep; (c) stop at the age re-remind above and let a human close stale
      questions. **(b) recommended** — it reuses an already-credentialled GitHub consumer and keeps the reconciler
      network-free.

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
