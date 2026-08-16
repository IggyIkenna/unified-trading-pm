---
doc_type: issue
title: "plan_reconciler's own HTTP integration has 2 live gaps: /api/plan-health/result rejects the documented no-auth path, and a blocked-question answer never became retrievable via /api/slots/N/messages"
summary: >-
  Surfaced live during the 2026-08-16 ao-tranche plan_reconciler run (dispatch agt-3eb42b, slot 28). (1)
  `POST /api/plan-health/result` rejected with `{"detail":"invalid or missing X-Orchestrator-Secret"}` both with an
  empty header value AND with the header omitted entirely — contradicting `agents/plan_reconciler.md`'s own documented
  behavior ("ORCHESTRATOR_INTERNAL_SECRET may be EMPTY in your shell — that's fine; the result POST is same-box
  localhost, which the server trusts on the loopback bind regardless of the header"). (2) The operator answered a
  posted `/blocked` question (BLK-050d1304) — confirmed via a direct mid-turn notification from the Claude Code harness
  itself ("Operator answered your BLOCKED question") — but `GET /api/slots/28/messages` returned an actual
  `Internal Server Error` on the first call, then `{"messages":[]}` on two subsequent retries; `GET /api/activity`
  showed no resolution event for the blocked_id either. The answer never became retrievable through this worker's
  documented channel. This directly reproduces a gap a PRIOR session already flagged as worth checking:
  `plan_reconciler_dead_run_no_lock_ttl_2026_08_12.md` cites `plan_reconciler_findings_ci_2026_08_10.md`'s note that
  "Blocked-question answer retrieval may have a real gap... worth checking whether OTHER plan_reconciler/
  na-eligibility-audit runs' blocked-questions have silently never received their answers either" — this run is a live,
  reproduced instance of exactly that suspected class, not a one-off.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer]
tags:
  [
    ao,
    agent-orchestrator,
    plan_reconciler,
    blocked-question,
    result-post,
    orchestrator-secret,
    messages-endpoint,
    regression-watch,
  ]
related:
  [
    /plans/active/issues/plan_reconciler_dead_run_no_lock_ttl_2026_08_12.md,
    /plans/active/issues/plan_reconciler_findings_ao_2026_08_16.md,
    /agents/plan_reconciler.md,
  ]
created: "2026-08-16"
author: plan_reconciler
parent_epic: orchestrator_master
priority: P1
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
resolved_by:
locked_by:
locked_since:
depends_on: []
context_scope:
  [
    agent-orchestrator/server/plan_health.py,
    agent-orchestrator/server/routes/slots_worker.py,
    unified-trading-pm/agents/plan_reconciler.md,
  ]
source: "Live-encountered during ao-tranche plan_reconciler run, dispatch agt-3eb42b, slot 28, 2026-08-16"
---

# plan_reconciler's own HTTP integration: 2 live gaps found 2026-08-16

## What happened

**Gap 1 — `/api/plan-health/result` rejects the documented no-auth localhost path.** This worker's role file
(`agents/plan_reconciler.md`) explicitly says: "`ORCHESTRATOR_INTERNAL_SECRET` may be EMPTY in your shell — that's
fine; the result POST is same-box localhost, which the server trusts on the loopback bind regardless of the header."
In practice, both of the following returned `{"detail":"invalid or missing X-Orchestrator-Secret"}`:

```
curl -X POST http://localhost:8765/api/plan-health/result -H 'X-Orchestrator-Secret: ' -d '{...}'
curl -X POST http://localhost:8765/api/plan-health/result -d '{...}'   # header omitted entirely
```

Either the documented loopback-trust behavior was never actually implemented, or it regressed, or it requires a
condition this worker's environment didn't meet (a specific bind address, a specific env var actually being unset vs
empty-string, etc.). This worker's actual findings were NOT lost — they're fully captured in the committed
`plan_reconciler_findings_ao_2026_08_16.md` and the git history — but the dashboard's machine-readable summary of this
run never landed, and every other daily tranche worker likely hits the identical wall.

**Gap 2 — a real operator answer to a `/blocked` question never became retrievable.** Sequence, in order:

1. This worker posted `POST /api/slots/28/blocked` with a question about a subscription-tier contradiction —
   succeeded, returned `blocked_id: BLK-050d1304`.
2. The Claude Code harness surfaced a direct mid-turn message: "Operator answered your BLOCKED question — check your
   messages now and resume."
3. `GET /api/slots/28/messages` → **`Internal Server Error`** (a real 5xx, not empty JSON).
4. Retried `GET /api/slots/28/messages` → `{"messages":[]}`.
5. Retried a third time → `{"messages":[]}` again.
6. `GET /api/activity?limit=10` → no `blocked_resolved`/similar event referencing `BLK-050d1304` in the most recent 10
   rows.
7. Guessed `GET /api/blocked/BLK-050d1304` and `GET /api/slots/28/blocked` — both 404/405, not real endpoints.

The worker had no way to retrieve the answer through the documented `GET /api/slots/<N>/messages` channel. The Claude
Code-level notification proves the operator's answer was sent SOMEWHERE — the gap is between that action and this
worker's ability to read it back via the AO HTTP surface.

## Why this matters

- **Gap 1** silently breaks the dashboard's visibility into every plan_reconciler run's outcome — the operator has no
  machine-readable summary unless they read the git log / findings doc directly. Low severity on its own (the durable
  record still lands), but it means the `/api/plan-health/result` endpoint's entire purpose (dashboard sync) is
  currently dead for at least this call path.
- **Gap 2 is the more serious one.** The prior session's own note (see `related:`) already flagged this exact
  suspected failure mode: a worker's blocked-question sits unanswered from the WORKER's perspective even after the
  operator has genuinely answered, because the answer-delivery path has a gap. If this recurs on a run this session
  couldn't independently observe, it produces the EXACT class of incident already documented for the `plan_reconciler`
  self-lock mechanism (`plan_reconciler_dead_run_no_lock_ttl_2026_08_12.md`): a worker sits blocked, no automated
  signal ever unsticks it, and only an operator manually noticing salvages it — except here the operator DID answer
  and the loop still didn't close.

## Todos

- [ ] [BACKEND] P1. **Root-cause why `/api/plan-health/result` rejects an empty/omitted `X-Orchestrator-Secret` from
      localhost**, despite `agents/plan_reconciler.md`'s documented loopback-trust behavior. Read
      `server/plan_health.py`'s auth-check code path directly (don't trust the doc's claim or this finding's
      reproduction alone — confirm against the CURRENT code). Either fix the code to match the documented behavior, or
      correct the doc if the loopback-trust design was intentionally removed/never shipped. Done when: a plan_reconciler
      worker's result POST succeeds from the standard boot environment without a manually-provisioned secret, OR the
      role doc is corrected to state the secret IS required and how a worker obtains it.
- [ ] [BACKEND] P1. **Root-cause the blocked-question answer retrieval gap.** Trace what actually happens end-to-end
      when an operator answers a `/blocked` question in the dashboard: which table/row gets written, and which
      endpoint(s) a worker is supposed to poll to see it. Reproduce this run's exact sequence (post a `/blocked`
      question from a test slot, answer it via the dashboard, poll `GET /api/slots/<N>/messages` and confirm whether
      the `Internal Server Error` reproduces and whether the answer ever appears). Cross-check whether this is the SAME
      mechanism `blocked_questions_ux_redesign_context_loss_and_scale_2026_07_24.md` already fixed (that doc's own
      todos are all `[x]`, archived) — if so, this may be a REGRESSION of a previously-fixed bug, not a new gap; if not,
      it's a distinct failure mode in the same subsystem. Done when: the exact break point is identified (wrong
      endpoint, a real 500 in the messages handler, a delivery-side bug that never writes the row) and fixed, with a
      regression test proving a worker can retrieve an operator's answer end-to-end. **New lead (2026-08-16,
      plan_reconciler, 2nd post-compact investigation)**: `GET /api/state` exposes a `blocked_queue` array directly
      (schema: `blocked_id`/`slot_id`/`task_id`/`question`/`options`/`recommendation`/`created_at`/`answered_at`/
      `answer`/`answered_by`/`authority`/`paged_at`/`similar_ids`) — a DIFFERENT, apparently-healthy channel from the
      broken `/api/slots/<N>/messages` (discovered via another live session's own `ps aux`-visible polling command).
      But `BLK-050d1304` does not appear in it at all (44 entries checked, 0 matches by exact `blocked_id`), and **0 of
      the 44 entries have any `answered_at` set**, spanning a 10-day `created_at` range — one entry's own
      dashboard-facing option text says outright "this entry prunes on the next regen", suggesting answered entries get
      pruned rather than retained with `answered_at` populated. If true, an answered question's content becomes
      genuinely unrecoverable from `/api/state` too, not just `/api/slots/<N>/messages` — worth checking whether the
      answer is durably written ANYWHERE (a dedicated history table, an audit log) before concluding the content is
      truly gone once pruned.
- [ ] [BACKEND] P2. **Audit whether other plan_reconciler/na-eligibility-audit runs have silently missed answers to
      still-open blocked questions**, now that this gap is confirmed live (not just suspected). Query the escalation/
      blocked-question table for any row with a recorded operator answer but no corresponding worker-side pickup, across
      recent runs. Done when: a count of affected historical rows is reported (0 is a valid, good answer) and, if any
      are found, each is individually resolved (apply the answer now, or re-ask if too stale to trust).

## Progress Log

- **2026-08-16 (plan_reconciler, ao tranche, dispatch agt-3eb42b)**: filed during the pre-compact checkpoint of this
  run, after directly hitting both gaps live. This worker's own substantive findings/fixes for the ao tranche were
  NOT affected (fully captured in `plan_reconciler_findings_ao_2026_08_16.md` + git history) — filing this as a
  separate meta-doc about the reconciler's own tooling reliability, matching the precedent of
  `plan_reconciler_dead_run_no_lock_ttl_2026_08_12.md` and `plan_reconciler_unexplained_tmux_session_loss_2026_08_10.md`.
- **2026-08-16 (plan_reconciler, defi tranche, dispatch agt-1a88e0)**: SECOND live reproduction of Gap 2, with a new
  diagnostic clue for todo 2. Posted `/blocked` (BLK-9b43a627), got the harness-level "Operator answered your BLOCKED
  question" notification, but `GET /api/slots/6/messages` returned only an unrelated git-status-red nudge — the
  answer was NOT in the queue. Found it instead via `GET /api/activity?limit=15`:
  `{"event_type":"blocked_message_orphaned_by_reassign","slot_id":6,"task_id":"agt-1a88e0","details":{"current_task":null,"text":"[operator] BLOCKED Q answered: A"}}`.
  The event name itself is the new clue this run adds: `orphaned_by_reassign` suggests the delivery-side bug is tied
  to task/slot reassignment (`current_task":null` at the time of the orphan event) rather than a generic 500 in the
  messages handler — worth checking whether the worker's `task_id` changed or its slot was reassigned between posting
  the `/blocked` call and the operator's answer landing. `/api/activity` was a usable workaround THIS time (the answer
  text was recoverable there even though `/messages` failed) — worth considering as a fallback read path in whatever
  fix todo 2 lands, not just a diagnostic aid.
- **2026-08-16 ~17:14 UTC (plan_reconciler, post-compact retry)**: re-tried `GET /api/slots/28/messages` after this
  session's context compaction completed — returned `200 {"messages":[]}` this time (the earlier call in this same run
  returned a real `Internal Server Error`; not reproduced on this attempt, so the 500 looks transient rather than a
  stable fault). Content is still empty either way — BLK-050d1304's answer remains unretrieved. Cross-checked
  `GET /api/activity?limit=10`: the 10 most recent fleet-wide events are all compaction/dispatch noise from other slots
  (ids 547096-547105); none reference `BLK-050d1304` or any blocked-question resolution for slot 28. This strengthens
  gap 2's diagnosis toward the write/delivery side (the answer never lands anywhere a worker can read) rather than a
  flaky read-side 500 — worth checking first when todo 2 below is picked up.
- **2026-08-16 ~18:03 UTC (plan_reconciler, second post-compact retry)**: re-tried `GET /api/slots/28/messages` again
  (twice, 3s apart) right after an unrelated quickmerge finally succeeded — **both attempts returned
  `Internal Server Error` again**, correcting the prior entry's "looks transient" read: the 500 has now reproduced on 2
  separate occasions across this run, not once, which reads as real recurring instability rather than a single flaky
  blip. `GET /api/activity?limit=10` at this same moment: grepped (not fully read — the payload was 1.2MB, one event
  carries a large embedded blob) for `BLK-050d1304`, `blocked_resolved`, `blocked_answered`, and `slot_id":28` — zero
  matches across all 10 rows. BLK-050d1304 remains fully unretrieved.
- **2026-08-16 ~18:15 UTC (plan_reconciler, 3rd channel checked)**: found (via another live session's `ps aux`-visible
  command) and independently queried `GET /api/state`'s `blocked_queue` array — a third, structurally different channel
  from both `/api/slots/28/messages` and `/api/activity`. Same negative result: `BLK-050d1304` is absent, and the
  queue's own evidence (0/44 entries answered across 10 days; one entry's option text says "prunes on next regen")
  points to answered-and-pruned rather than a retrieval bug in this specific channel. Full detail + the schema moved to
  todo 2 above as a concrete lead. **Conclusion**: BLK-050d1304's answer is now confirmed unretrievable across every
  channel available to this worker (3 independent surfaces checked, not 1). Re-posting the question would not help —
  the Claude Code harness's own mid-session notification confirms the ask→answer round-trip already worked once; the
  confirmed-broken leg is retrieval, which a duplicate ask would hit identically. Per `agents/plan_reconciler.md` STEP
  8, still holding — not calling `/api/slots/28/done` — but further polling of these same 3 channels is not expected to
  change the outcome. The remaining path is the one already named in `plan_reconciler_findings_ao_2026_08_16.md`'s
  Progress Log: a fresh session or the operator applying the answer directly to the 2 affected docs, or a
  [BACKEND]-scoped fix to todo 1/2 above followed by a re-check.
