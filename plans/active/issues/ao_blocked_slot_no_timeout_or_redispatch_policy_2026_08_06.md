---
doc_type: issue
title:
  "No kill/timeout or redispatch policy exists for a blocked slot — a worker with no continuable work can hold a slot
  hostage indefinitely, and there is no differentiated timeout by who can actually answer the question"
summary: >-
  Operator's proposed design (2026-08-06): a blocked question the orchestrator/main-agent can plausibly answer itself
  should get a short budget (operator suggested ~10 min) before the waiting agent is killed and the slot freed for other
  work; a genuinely operator-gated question (only a human can answer) may legitimately sit unanswered for hours, but the
  slot shouldn't stay tied up for that whole window either — free it, and once answered, re-dispatch the underlying work
  fresh rather than resuming a session that's been killed. Traced end-to-end in code: nothing resembling this exists.
  `worker_liveness_watchdog.py` explicitly and uniformly refuses to kill any slot with `status == "blocked"`, regardless
  of `BlockedRow.authority` — the SSOT states the rule with no exception
  (`/codex/04-architecture/agent-orchestrator-worker-liveness.md:378`, "Do NOT kill a worker whose status is
  `blocked`"). `BlockedRow.authority` exists (`orm.py:350`) but is never read by any timeout/kill decision anywhere —
  only cosmetic UI styling and one Slack-paging branch. The real worker-facing `POST /api/slots/{slot_id}/blocked`
  endpoint doesn't even let a worker declare `authority` — `BlockedRequest` (`models/worker_api.py:242-248`) has no such
  field, so in production a live blocked question can never be self-tagged "orchestrator can answer this" vs
  "operator-only." The one function whose docstring gestures at a blocked-slot timeout exemption
  (`worker_liveness/_respawn.py:: maybe_auto_respawn_stuck_slot`) isn't wired into the watchdog's tick loop at all —
  dead code with a stale comment. The system's actual designed answer to "don't waste the slot" is `continue_on`
  (`worker.md:294-340` — a worker declares other work to keep grinding on while blocked), but `blocked_slot()`
  (`routes/slots_worker.py:2196-2230`) sets `slot.status = "blocked"` unconditionally even when `can_continue=True`, so
  fleet-wide the slot still reads as idle/blocked regardless of whether the agent is actually still productive — and
  `continue_on` has no answer at all for a worker that's genuinely run out of continuable work while operator-gated.
status: open
nature: issue
asset_group: [ao]
scope: [engineer, admin]
stage: [meta]
repos: [agent-orchestrator]
tags:
  [agent-orchestrator, blocked-queue, worker-liveness, dispatch, watchdog, timeout-policy, design, operator-reported]
related:
  [
    /plans/archive/issues/ao_blocked_question_not_retired_when_condition_resolves_2026_08_06.md,
    /plans/active/issues/ao_blocked_answer_message_cross_delivered_after_slot_reassign_2026_08_06.md,
    /plans/active/issues/blocked_questions_ux_redesign_context_loss_and_scale_2026_07_24.md,
    /codex/04-architecture/agent-orchestrator-worker-liveness.md,
    /codex/12-agent-workflow/operator-gated-blocked-row-lifecycle.md,
  ]
created: 2026-08-06
author: agent
last_updated: 2026-08-06
priority: P2
parent_epic: orchestrator_master
source:
  "operator-directed, interactive session — operator's own framing: a main-agent-answerable question should free the
  slot after ~10 min if unanswered, an operator-gated question may legitimately sit for hours but shouldn't hold the
  slot hostage the whole time; the slot should be killed and the work re-dispatched fresh once answered rather than
  waiting on a dead session — this is a proposed design direction, deliberately NOT scoped or actioned yet"
assigned_vm: NA
execution_scope: local-only
estimate_class: design
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.5
assigned_role: infra
drift_direction: advance-code
resolved_by:
locked_by:
depends_on: []
context_scope:
  [
    agent-orchestrator/server/worker_liveness_watchdog.py,
    agent-orchestrator/server/worker_liveness/_respawn.py,
    agent-orchestrator/server/blocked_reconcile.py,
    agent-orchestrator/server/routes/slots_worker.py,
    agent-orchestrator/server/orm.py,
    unified-trading-pm/agents/worker.md,
    /codex/04-architecture/agent-orchestrator-worker-liveness.md,
    /codex/12-agent-workflow/operator-gated-blocked-row-lifecycle.md,
  ]
---

# No differentiated kill/timeout policy exists for blocked slots

## Why this matters

Today a blocked slot is watchdog-exempt with no time limit, full stop — an operator-gated question can hold a slot for
10 hours with nothing in the system questioning whether that's still the right trade-off. The only mitigation that
exists (`continue_on`) helps only when the worker actually has other work to fall back on, and even then the slot still
reports `status == "blocked"` fleet-wide, so there's no visibility into "blocked-but-productive" vs "blocked-and-idle."
There is no concept anywhere of "this specific question is cheap enough that the orchestrator itself could probably
answer it" versus "this one is genuinely operator-only" — the `authority` field that could carry that distinction exists
in the schema but is disconnected from both the timeout question and the worker's own `/blocked` call.

This is a design question, not a bounded bug fix — it needs an operator ruling on the thresholds and on what
"redispatch" should mean for a real occupied slot (the codebase already has one working precedent for "answer becomes
fresh dispatchable work," `/codex/12-agent-workflow/operator-gated-blocked-row-lifecycle.md`'s `BLK-op-*`
ruling-materialization mechanism — but that only exists for the synthetic `slot_id=0` sentinel row that never had a live
worker behind it in the first place; it has never been extended to a real, currently-occupied slot).

## Open design questions for the operator

- What should route a question to the "main-agent can probably answer it, budget ~10 min" bucket versus the
  "operator-only, may take hours" bucket? Is this a worker self-declaration at `/blocked` time (extend
  `BlockedRequest`/`BlockedRow.authority`, currently unused for this), a main-agent triage pass before the question ever
  pages a human, or something else?
- For the 10-min bucket: if the main agent (or nobody) answers in time, what actually happens to the slot — kill the
  tmux session outright (same mechanism `reassign_slot` already uses), or something softer? What happens to the
  in-flight task the worker was doing before it blocked — abandoned, requeued, or does the blocked question itself
  become the thing that's requeued?
- For the operator-gated bucket: is "free the slot after N hours and re-dispatch the QUESTION as fresh work once
  answered" the right model (mirroring `BLK-op-*`), or is losing the asking agent's accumulated context/reasoning too
  costly for questions that aren't simple yes/no rulings?
  `blocked_questions_ux_redesign_context_loss_and_scale_2026_07_24.md` already flags dead-agent context loss as a
  standing pain point — any kill-based policy here compounds it unless paired with that issue's proposed
  transcript-linking fix.
- Should `continue_on` remain the primary mitigation (keep the same agent productive) with killing reserved as a
  fallback only once a worker reports it has no more continuable work — or should killing become the default for the
  operator-gated bucket regardless?
- If this ships, does it require `SlotMessageRow` delivery scoping first
  (`ao_blocked_answer_message_cross_delivered_after_slot_reassign_2026_08_06.md`)? A kill-and-reuse-the-slot policy
  applied at scale will hit that cross-delivery gap far more often than the rare manual "Reassign" click does today.

## Operator ruling (2026-08-06)

- **Routing**: worker self-declares `authority` at `/blocked` time (extend `BlockedRequest` + wire the already-existing
  `BlockedRow.authority` field) — fast path, one API call, no new triage stage for every question. The main-agent gets a
  bounded first crack at answering ONLY within the `main_agent`-tagged bucket, before that bucket's timer expires — not
  a fleet-wide triage pass over every blocked question (rejected: adds latency even to obviously operator-only questions
  like wallet keys / force-push).
- **`main_agent` bucket (~10min budget, operator's own number from the doc's summary)**: unanswered at the deadline →
  kill the tmux session (same mechanism `reassign_slot` already uses) + free the slot; the in-flight task the worker was
  doing before it blocked is abandoned and **requeued as fresh backlog work**, not resumed — mirrors the existing
  `BLK-op-*` precedent, now extended to a real occupied slot instead of only the synthetic `slot_id=0` sentinel row.
- **`operator` bucket (hours-long budget)**: same model — free the slot once the budget elapses, and once the operator
  answers, **redispatch fresh** rather than resuming a killed session (accepts the context-loss tradeoff named in the
  doc as the cost of not tying up a slot for hours). `continue_on` is NOT the primary mitigation for this bucket under
  this ruling — a worker may still declare `continue_on` to stay productive while waiting, but it does not gate or
  extend the N-hour timer; killing + fresh redispatch is the default once the budget elapses regardless of `continue_on`
  state.
- **Operator-bucket threshold**: no explicit number was given for this ruling round — proposing **N = 4 hours** as the
  starting default (long enough not to prematurely kill a genuinely slow-to-answer operator question, short enough to
  bound slot-hostage time; same order of magnitude as this codebase's other backoff/TTL windows, e.g. escalation.py's
  `QUEUE_TTL_HOURS=24`/`HARD_ABANDON_HOURS=48` scaled down for a much cheaper resource — one slot, not a whole queue).
  **Flagged as adjustable, not re-litigated here** — correct via a follow-up ruling if 4h is wrong in practice.
- **Ordering**: confirmed — this ships AFTER
  `/plans/active/issues/ao_blocked_answer_message_cross_delivered_after_slot_reassign_2026_08_06.md`'s fix lands. A
  kill-and-reuse-the-slot policy applied at the cadence this design implies will hit that cross-delivery gap far more
  often than the rare manual "Reassign" click does today — shipping this first without that fix would make the known bug
  materially worse, not just leave it unaddressed.

## Todos

- [x] [OPERATOR] P2. **Rule on the design questions above** — see "Operator ruling (2026-08-06)" above.
- [x] [INFRA] P3. **Wire `authority` into the real `/blocked` path.** `agent-orchestrator@cc5961e` — added
      `authority: Literal["main_agent", "operator"] = "main_agent"` to `BlockedRequest`, threaded through
      `blocked_slot()` to `add_blocked()` and into the `slot_blocked` activity log; 2 regression tests
      (`tests/test_blocked_authority_field.py`) covering both the declared-value round-trip and the default.
- [x] [INFRA] P3. **Implement the differentiated timeout in `blocked_reconcile.py`** — `agent-orchestrator@9777c02`. Two
      new config knobs (`blocked_main_agent_timeout_minutes=10`, `blocked_operator_timeout_hours=4.0`); a third
      classification (`classify_timeout`) in `reconcile_once`'s sweep, after retirement + the plans-corpus match both
      miss, following `classify_retirement()`'s exact pattern; `_timeout_blocked_slot` kills the tmux session + frees
      the slot + requeues the task fresh via the same mechanism `POST /reassign(kill_worker=true)` uses. Guards against
      acting on an already-orphaned row (slot moved on some other way since the question was raised) by requiring
      `slot.current_task == row.task_id`. 7 regression tests (`tests/test_blocked_slot_timeout.py`) covering
      classification for both buckets, the full kill+requeue path, an operator-bucket row correctly left alone within
      budget, and the orphan guard. Shipped AFTER the cross-delivery fix per "Ordering" above (that fix shipped first,
      same session, `agent-orchestrator@365e18e`).
- [ ] [INFRA] P3. **Give the main-agent a bounded first-answer window on `main_agent`-tagged questions** before that
      bucket's kill timer fires — **NOT implemented**, deliberately deferred: the shipped timeout applies uniformly at
      the 10-minute deadline with no dedicated "main-agent gets first crack" sub-mechanism (the main agent CAN still
      answer via the normal `/answer` endpoint any time before the deadline, which loosely satisfies the spirit, but
      nothing actively prompts/triages it to do so). The specific mechanism (a dedicated triage poll vs. reusing an
      existing tick) is still an implementation detail for whoever picks this up.

## Progress Log

### 2026-08-06 — filed (interactive session)

Filed after the operator described the proposed policy and asked whether it already exists. Deep-searched
`blocked_reconcile.py`, `orm.py`, `routes/backlog.py`, `config.py`, `worker_liveness/_respawn.py`, and the codex/plan
corpus for any `authority`-differentiated timeout or "free the slot" design — confirmed none exists, including as dead
code. Filed as design/operator-ruling-needed rather than a scoped implementation todo, per the dispatch-scope
eligibility bar (an open-ended judgment call is not an AO-dispatchable todo until the operator names the shape).

### 2026-08-06 (later, interactive session) — operator ruled

Operator ruled on all open design questions via AskUserQuestion (see "Operator ruling" section above); this doc is now
implementation-ready pending the cross-delivery fix landing first. Not yet implemented — todos above are scoped but
unstarted.

### 2026-08-06 (same session, continued) — implemented + shipped

Both `[INFRA]` todos landed same session, in the correct order: cross-delivery fix first (`agent-orchestrator@365e18e`,
tracked in the companion doc), then authority-field wiring (`agent-orchestrator@cc5961e`), then the differentiated
timeout itself (`agent-orchestrator@9777c02`). Full `quality-gates.sh` green at every step (2588 tests passing after the
final ship, 0 lint/type errors). The 4th todo (a dedicated main-agent first-answer window) is explicitly NOT implemented
— left open above with the reasoning. This doc stays `open`, not archived, until that one lands or is deliberately
dropped.

Note for whoever picks up the remaining todo: `blocked_reconcile.reconcile_once` now runs on a live orchestrator that
WILL kill real workers on a timer — verify the two config knobs
(`blocked_main_agent_timeout_minutes`/`blocked_operator_timeout_hours`) are behaving as expected in production before
tuning them further.

- **na-eligibility-audit 2026-08-07** (tranche=ao, autonomous): KEEP-NA, valid — checkboxes already accurate (verified
  `cc5961e`/`9777c02` are real commits doing what's claimed). The one remaining todo (main-agent bounded first-answer
  window) is genuinely still undecided in its own text ("still an implementation detail for whoever picks this up") —
  P3, low priority, not bounded enough for RECLASSIFY without a stated done-when.
