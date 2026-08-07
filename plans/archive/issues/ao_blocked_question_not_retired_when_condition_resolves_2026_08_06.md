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
status: resolved
nature: issue
asset_group: [ao]
scope: [engineer]
stage: [meta]
repos: [agent-orchestrator]
tags: [agent-orchestrator, blocked-queue, worker-liveness, dispatch, staleness, operator-reported]
related:
  [
    /plans/archive/issues/ao_worker_context_saturation_unrecoverable_2026_08_06.md,
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

> **🟢 ARCHIVED 2026-08-06** — `status: resolved` with zero open todos; archived per
> [`/codex/11-project-management/issue-doc-lifecycle.md`](/codex/11-project-management/issue-doc-lifecycle.md)'s
> archive-on-resolve rule. All 6 todos shipped (agent-orchestrator@84cfd59, ceab325, bf5b735) + deployed + verified live
> on the orchestrator (blocked/reconcile returns retired/stale_reminded keys; stale re-remind fired on 23 real
> questions; PR predicate verified returning CLOSED for PR #861). Moved by the 2026-08-06 AO issue-doc archive sweep.

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

- [x] ✅ [INFRA] P2. **External-condition predicate — SHIPPED (agent-orchestrator@bf5b735).** This is the trigger for
      the case that motivated the whole issue: BLK-4781b9af asked "admin-merge PR #861?", the PR was closed as
      superseded and main went green ~11h later, while its task stayed open and no doc moved — so neither local trigger
      can see it. `classify_external_pr_condition()` shells `gh pr view` and retires when the PR is MERGED/CLOSED.
      **Correction to this doc's earlier framing**: it previously gated this on an operator ruling about "whether the
      orchestrator may make outbound network calls". That premise was WRONG and the operator challenged it — the
      orchestrator process already shells to `gh` from four modules (`gh_rate_monitor`, `ci_status`, `ci_reconcile`,
      `escalation`) and already monitors its own GitHub rate-limit pools, so this is one more call on an existing,
      already-credentialled egress path, not a new capability. No ruling was needed. Conservative by construction,
      because a false retirement closes a real operator question (cf.
      `blocked_reconcile_marker_false_positive_2026_08_03`): EXACTLY one distinct `PR #<n>` in the text (several =
      ambiguous → skip, without even looking up), a repo name from the actual workspace must appear so we never guess
      which repo a bare `#861` belongs to, only MERGED/CLOSED retire (OPEN = decision still live), and ANY lookup
      failure leaves the question alone. Knob `tuning.blocked_retire_on_pr_terminal` (default True) can disable it.
      **Verified live on the orchestrator itself**, not just unit-tested:
      `fetch_pr_state('unified-api-contracts','861')` → `CLOSED`, and the predicate returned
      `('pr_terminal', 'IggyIkenna/unified-api-contracts PR #861 is CLOSED — the merge decision this question asked     for has already been taken')`
      — i.e. exactly the verdict that would have released slot 2 fifteen hours early. The post-deploy sweep retired 0 of
      the 25 currently-pending questions, which is correct: they are all `[OPERATOR]` policy questions with no PR
      reference, so the conservative matching declines them. 5 tests:
      `tests/test_blocked_reconcile.py::test_pr_predicate_retires_on_a_closed_pr`,
      `…::test_pr_predicate_leaves_an_open_pr_alone`, `…::test_pr_predicate_skips_ambiguous_multi_pr_questions` (asserts
      no lookup even happens), `…::test_pr_predicate_requires_a_named_repo`,
      `…::test_pr_predicate_never_retires_on_a_failed_lookup`.

## Progress Log

### 2026-08-06 — shipped + deployed + verified live; one adjacent pre-existing bug found and fixed

Deployed to the orchestrator VM (pull + `systemctl restart orchestrator`, permitted without operator scheduling per the
2026-07-28 maintenance-window ruling) and verified end-to-end, not just unit-tested:

- `POST /api/blocked/reconcile` returns the new summary keys (`retired`, `stale_reminded`), proving the shipped code is
  the code running.
- The staleness re-remind fired on **23 real questions** in its first periodic sweep, standing 140h / 145h / 158h / 159h
  / **170h** — i.e. the queue's problem was never that questions were moot, it was that week-old ones were invisible.
  Retirement fired on 0, as measured in todo 5.

**Adjacent pre-existing bug found + fixed (agent-orchestrator@b2f1432).** One of the 24 re-reminds raised inside
`slack._post`: `BLK-op-cefi_derivative_ticker_tardis_resolver_aiodns_hardfail-005` carries a 4,654-char question, and
Slack rejects the ENTIRE post when any section exceeds 3,000 chars — so that row never paged at all, including its
ORIGINAL blocked page long before this work. `recommendation` was already bounded at 400 chars; `reason` (the question)
was not. Added `_clip()` and applied it to the `*Question:*` section of BOTH `notify_slot_blocked` and
`notify_operator_gated_blocked`. Verified live: at 15:02:52Z (old code) the notify still ERRORed; at 15:03:37Z
(post-restart) the same row logged "standing unanswered for 70h — re-reminded". Test:
`tests/test_blocked_reconcile.py::test_slack_question_section_is_clipped_to_slack_limit`.

Note for whoever reads the channel: the first activation posted ~23 re-reminds in one burst. That is a one-off — the
cooldown means each question re-reminds at most once per `blocked_question_reremind_cooldown_hours` (12h) thereafter.

### 2026-08-06 — filed (interactive session, slot 2 host `hk`)

Filed on an explicit operator ruling while unblocking slot 2. Slot 2 was holding four questions; `BLK-4781b9af` was
verified moot before answering (PR #861 CLOSED/superseded, #863-#866 MERGED, quality-gates-v2 green on
unified-api-contracts main) and was answered "RESOLVED — stale question, no action needed" rather than acted on. The
other three (`BLK-136e69bf` LA_LIGA_2, `BLK-0e7e0794` UPBIT, `BLK-5eeacb63` duplicate finalize plans) were each verified
against the repo and answered on their merits — all three were genuine, so this issue is specifically about the
retirement path, not about question quality.

Incidental observation while checking the UAC promotion, NOT part of this issue and not yet triaged: the
`main-backmerge-to-ldr` run on unified-api-contracts `main` showed `pending` at 3h39m elapsed.
