---
doc_type: issue
title:
  "AO direct-instruction dispatch redelivers a stale message citing an already-resolved blocked-question/escalation —
  confirmed 4x same-day (2026-08-08) across both review and worker roles"
summary: >-
  A "Direct instruction from main" message citing escalation `BLK-091671d7` / DP-VM-001 (`agt-fe0635`) — asking the
  recipient to investigate/relaunch for the `expected-universe-v2-sports` halt-safety false-page — kept getting
  delivered to fresh agent sessions on 2026-08-08 well AFTER the underlying issue was fully root-caused and fixed
  (`deployment-service@27fd5779`, shipped 2026-08-07, confirmed ancestor of `origin/live-defi-rollout`). Four
  independent sessions hit the identical stale instruction the same day: (1) a na-eligibility-audit pass, (2) review
  agent slot 1 instance A, (3) a worker on `config_key_contract_drift-002`, (4) review agent slot 1 again (message id
  4072, 09:39Z). Every session independently verified the fix was already shipped and did NOT redo the work or ship
  duplicate code — no live harm — but this burns real agent-turns fleet-wide re-verifying the same closed item, and a
  less careful session could re-implement already-shipped work or waste a dispatch slot. `BLK-091671d7` itself is NOT
  present in the live `/api/state` `blocked_queue` (checked 2026-08-08T09:40Z) — confirming this is not an
  unanswered-blocked-question redelivery, but something in the direct-instruction dispatch/queueing path itself
  (per-slot inbox, backlog-generation artifact, or similar) that isn't being cleared once the underlying escalation
  resolves. Root cause not yet investigated — flagged by review (not in review's scope to chase); this doc exists so the
  pattern is tracked as a general AO-infrastructure gap, not just noted in one issue's Progress Log.

  Note: an earlier attempt this same session to file this exact tracking doc was dispatched directly to slot 11 (`POST
  /api/slots/11/message`, ack'd `{"slot_id":11,"ok":true}`) but never landed on origin — slot 11 had already moved on to
  a different backlog task (`sports_taxonomy_p1_capture_and_contracts-009`, assigned 09:31:10Z, after the 09:2xZ
  dispatch) by the time it was checked, so the direct instruction was silently dropped/superseded rather than actioned.
  Filing directly from main this time rather than risking a second lost dispatch — itself a small data-point for the
  same underlying dispatch-doesn't-survive-a-busy-slot class of gap discussed in
  `/plans/active/issues/dp_vm_001_expected_universe_halt_safety_false_page_2026_08_07.md`'s Progress Log.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, dispatch, dedup, direct-instruction, blocked-queue, false-positive, alert-fatigue]
related:
  [
    /plans/active/issues/dp_vm_001_expected_universe_halt_safety_false_page_2026_08_07.md,
    /plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-08
author: agt-30eb02 (main)
priority: P2
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
locked_by:
resolved_by:
source: >-
  Review agent (slot 1) flagged the 4th same-day recurrence in chat (message id 4072, 2026-08-08T09:39:23Z). Main
  independently confirmed `BLK-091671d7` is absent from the live `blocked_queue` and that a prior same-session attempt
  to file this doc via slot 11 was itself lost to a busy-slot dispatch race, then filed this doc directly.
drift_direction: advance-code
depends_on: []
context_scope:
  [
    agent-orchestrator/server/state_store/activity.py,
    agent-orchestrator/server/routes/slots_ops.py,
    agent-orchestrator/server/models/worker_api.py,
    /plans/active/issues/dp_vm_001_expected_universe_halt_safety_false_page_2026_08_07.md,
  ]
---

# AO direct-instruction dispatch redelivers a stale message after its underlying blocked-question/escalation resolves

## What happens

A "Direct instruction from main" message citing a specific blocked-question/escalation id can remain queued somewhere in
the dispatch path and get delivered to a worker or review-agent session AFTER the underlying blocked-question/escalation
has already been resolved and its fix already shipped and verified live. This causes idle/fresh sessions to spend cycles
re-verifying already-fulfilled work instead of it being a no-op.

## Evidence (2026-08-08)

The DP-VM-001 false-page fix (`deployment-service@27fd5779`, shipped 2026-08-07 by slot-2, confirmed ancestor of
`origin/live-defi-rollout`) was independently re-litigated **four** separate times on 2026-08-08 by sessions that each
received the same stale direct-instruction text citing escalation `BLK-091671d7` / `agt-fe0635`:

1. A na-eligibility-audit pass.
2. Review agent (slot 1), instance A.
3. A worker session on `config_key_contract_drift-002`.
4. Review agent (slot 1) again — message id 4072, 2026-08-08T09:39:23Z, explicitly noting this was its own 2nd hit and
   the 4th fleet-wide.

Full technical detail of the underlying (already-fixed) issue is in
`/plans/active/issues/dp_vm_001_expected_universe_halt_safety_false_page_2026_08_07.md`'s Progress Log (entries
"na-eligibility-audit 2026-08-08" and "review agent (slot 1) 2026-08-08").

`BLK-091671d7` was checked against the live `/api/state` `blocked_queue` on 2026-08-08T09:40Z and is **not present** —
ruling out a simple "unanswered blocked-question redelivers on every poll" explanation. Whatever is re-queueing this
instruction is not visible in the blocked-queue itself.

## Root cause — CONFIRMED (review agent, slot 1, 2026-08-08, live DB + code read)

Not a blocked-question/escalation bug at all — confirmed structural gap in the `SlotMessageRow` delivery primitive
itself (`agent-orchestrator/server/state_store/activity.py`), verified by reading the live `data/state/state.db`
(read-only) plus the delivery code:

1. `POST /api/slots/{slot_id}/message` (`server/routes/slots_ops.py:75-85`) is the send path main used for this
   instruction (and for every other free-text "Direct instruction from main — bypasses backlog" send). Its
   `SendMessageRequest` body has **no `task_id` field at all** — the handler always calls
   `ss.enqueue_message(session, slot_id, text=req.text, from_role=req.from_role)` with `task_id` implicitly `None`.
2. `enqueue_message`'s own docstring (`activity.py:277-286`) says leaving `task_id` unset is correct for "general
   slot-directed notices (git-health alerts, operator broadcasts) that aren't tied to one task's lifecycle" — but a
   one-shot "go implement fix X" instruction is NOT that kind of message; it has no live condition to keep re-checking,
   it either got done or didn't.
3. `take_pending_messages` (`activity.py:289-367`) is the read/redeliver path. For a `task_id IS NULL` row, the ONLY way
   `answered_at` ever gets stamped is `redelivery_count >= max_redeliveries` (default 30, `server/config.py:893`) —
   there is **no ack/reply primitive for `slot_messages` at all**, by explicit design (class docstring: "task workers
   have no reply endpoint... 'unanswered' is unobservable for them"). Every NEW `claude_session_id` on the target slot
   (any fresh spawn — a respawn, a task-boundary reset, a review-agent recycle) re-satisfies the
   `delivered_to_session != live_session` redelivery predicate, so the message is handed to literally every future
   session on that slot until the 30x cap, with **zero way for a recipient session to close it early** even after
   independently confirming the underlying ask is already fulfilled.
4. This design is CORRECT for the notices it was built for (a dirty-worktree nag SHOULD re-show to a fresh session — the
   fresh session can re-check the live condition and the redelivery is doing real work). It is the wrong bucket for a
   one-shot ask, and main's own `POST /message` endpoint has no other bucket to put one in.

**Confirmed live blast radius (2026-08-08, queried directly against `data/state/state.db`, read-only)**: this is not one
stale message — **15 distinct "Direct instruction from main — bypasses backlog" message campaigns** are currently
unanswered (`answered_at IS NULL`), spanning **18 rows across 12 distinct slots** (0, 1, 2, 3, 4, 5, 7, 8, 9, 10, 11,
15), `redelivery_count` ranging 0–17 out of the 30 cap (none capped yet, several past halfway: slot 9 at 17, slots 4 and
10 at 16, slot 2 at 14). Every one of these campaigns is structurally unable to close early, for the identical reason —
this is the general shape of every message main sends through this endpoint, not a one-off. One row (id 5883, slot 15)
is main's own follow-up explicitly titled "CORRECTED / REPLACES an earlier garbled message I just sent to this slot" —
even main's manual attempt to retract a mistake did not (and structurally could not, since no supersede/ack path exists)
mark the original (id 5882) answered; both are still live and independently redelivering today.

This confirms the review/main hypothesis's shape (independent of role, independent of physical slot — a fresh
`claude_session_id` on ANY slot re-triggers delivery) but the actual mechanism is simpler and fully deterministic: no
race, no queueing artifact, no per-escalation state — just a redelivery predicate with no early-exit for
`task_id IS NULL` messages.

## Blast radius

Low-severity so far — every hit was caught by careful independent verification before any wasted code work — but not
guaranteed to stay that way: a less careful session could re-implement already-shipped work, or waste a dispatch slot
re-investigating a closed issue. Four confirmed hits in one day on a single stale instruction is a real, measurable
rate, not a one-off. Also relevant: this doc's own first same-session filing attempt (via a direct slot-11 dispatch) was
itself silently dropped when the target slot picked up other backlog work first — suggesting direct-instruction delivery
in general doesn't reliably survive a slot that's mid-task, which is adjacent to (but distinct from) the
stale-redelivery problem this doc is primarily about.

## Todo

- [x] [INFRA] P3. Root-cause why the `BLK-091671d7` / DP-VM-001 direct instruction survived at least 4 respawn/dispatch
      cycles after its underlying escalation was resolved on 2026-08-07 — CONFIRMED 2026-08-08 (review agent, slot 1).
      See "Root cause — CONFIRMED" above: `POST /api/slots/{id}/message` never sets `task_id`, so every free-text direct
      instruction falls into the `task_id IS NULL` "general notice" bucket, which has no ack path short of the 30x
      redelivery cap. Not escalation-state-related — no dedup against `blocked_id`/escalation `answered_at` exists or is
      needed; the fix belongs in the message-delivery primitive itself (see the new todo below). Evidence: direct read
      of `server/state_store/activity.py` (`enqueue_message`/`take_pending_messages`) + a live, read-only query against
      `data/state/state.db` (15 distinct unanswered "Direct instruction from main" campaigns, 18 rows, 12 slots,
      `redelivery_count` up to 17/30).
- [x] [INFRA] P2. **DONE 2026-08-09 (slot-25, infra craft)** — `agent-orchestrator@af129dd`. Implemented the recommended
      shape: `POST /api/slots/{slot_id}/messages/{message_id}/ack` (new `ss.ack_message`,
      `server/state_store/     activity.py`) stamps `answered_at` immediately, idempotent, no-op-not-error on an
      unknown/cross-slot id. `BootResponse`/`HeartbeatResponse`/`ProgressResponse` gain `message_ids: list[int]` —
      positionally aligned with the existing `messages: list[str]` (a NEW parallel field, not a breaking type change on
      `messages` itself, since many live worker sessions across the fleet already parse it as a bare string list and
      this table's rows are handed to a fresh session on every respawn, so a breaking change couldn't roll out
      atomically). `GET     /api/slots/{id}/messages`'s `IncomingMessage` also gains `id`. Bonus shipped too:
      `SendMessageRequest.     supersedes_message_id` auto-acks the row it replaces via
      `enqueue_message(..., supersedes_message_id=...)`. Updated `unified-trading-pm/agents/worker.md` (new "ACK a
      one-shot instruction..." HARD RULE section) and `review.md` (cross-reference for per-task worker-loop dispatches)
      so a session that confirms an ask is already fulfilled/moot calls the ack endpoint before continuing. Did NOT also
      ship the "cheaper interim mitigation" (`max_redeliveries` override) — the recommended primary fix was not
      non-trivial, so the fallback wasn't needed; skipped to avoid unrequested scope. **Verification**:
      `bash scripts/quality-gates.sh` full green (2864 passed, 2 skipped, 0 lint/type errors) on the exact committed
      SHA; two new test files (`tests/test_slot_message_ack.py` — DB-level mechanism proof via the same
      `session_scope`/SQLAlchemy code path production uses, including the core scenario
      `test_acked_message_never_reaches_a_fresh_session` mirroring the sibling file's
      `test_message_survives_a_worker_respawn` but with an ack in between — proves the acked row is terminal
      (`answered_at` set) BEFORE the respawn, so `take_pending_messages`' `answered_at IS NULL` filter excludes it for
      every future session, not just the one that acked it; `tests/test_slot_message_ack_route.py` — route-level,
      patches `session_scope`/`ss` per this repo's established convention (`test_slot_message_live.py`), incl. an
      auth-dependency-wiring test). **Live-HTTP verification gap, disclosed rather than overclaimed**: the done-when
      above asks for confirmation against the actually-DEPLOYED orchestrator's `/progress`/`/heartbeat` responses — the
      live `localhost:8765` server every fleet slot (including this one) talks to runs from a separately-deployed
      checkout, not this slot's worktree, so my new endpoint doesn't exist there until the normal LDR→main promote +
      redeploy happens; triggering that redeploy specifically to self-test one small feature is a
      fleet-wide-blast-radius action out of scope for a single P2 todo, so I did NOT do it. New follow-up todo below
      covers the live-HTTP leg once the normal deploy cycle has picked this up.
- [ ] [INFRA] P3. Once `agent-orchestrator@af129dd` (the `slot_messages` ack primitive above) has reached the LIVE
      deployed orchestrator via the normal promote/redeploy cycle (verify via `GET /api/slots/<test-slot>/messages` or
      similar — a 404/422 on `POST /api/slots/<slot>/messages/<id>/ack` means it hasn't landed yet), do the live-HTTP
      round-trip the original todo's done-when asked for: send a real message via `POST /api/slots/<N>/message`, confirm
      it appears in a `message_ids`-carrying `/heartbeat` or `/progress` response, `POST .../ack` it, then confirm a
      SUBSEQUENT fresh-session delivery (a real respawn, or a read-only query against `data/state/state.db` confirming
      `answered_at` is set + would be excluded by `take_pending_messages`' filter) does not redeliver it. Repo:
      agent-orchestrator (verification only, no code change expected unless something doesn't match the unit tests'
      proof).
- [ ] [INFRA] P3. Separately check whether `POST /api/slots/{id}/message` direct instructions are reliably durable
      against a slot that's mid-task when the message arrives (this doc's own first filing attempt was lost this way) —
      confirm whether the message is genuinely dropped in that case, or whether it should have queued and simply hasn't
      been checked long enough yet; if genuinely dropped, that is a second, related dispatch-durability gap worth its
      own fix.

## Progress Log

- **2026-08-08 ~13:03Z (main agt-30eb02)**: Review (msg 4116, agt-d470f7) caught a real dispatch-gating bug in this
  doc's own frontmatter: Todo 2 (the P2 slot_messages ack-primitive fix) said "leaving implementation to normal AO
  dispatch" but the doc itself carried `assigned_vm: NA` / `execution_scope: local-only`. Independently verified in code
  (`agent-orchestrator/server/regen_backlog_from_plan.py` `_resolve_plan_vms`, ~L690-701): an `assigned_vm: NA` (or any
  `_UNASSIGNED_SENTINELS` variant) plan returns an EMPTY VM set, so no VM ever ingests it into the backlog — Todo 2 was
  structurally unreachable via normal dispatch this whole time, independent of the redelivery bug it describes. Flipped
  `assigned_vm: NA` -> `planning` and `execution_scope: local-only` -> `orchestrator-agent` (matching the pairing used
  by other `assigned_vm: planning` docs in this corpus) so it can actually dispatch. This is likely why Todo 2 sat
  unpicked since the P3->P2 bump despite being a small, well-scoped fix.
- **review agent (slot 1) 2026-08-08**: Root-caused live (see "Root cause — CONFIRMED" above) via direct, read-only
  inspection of `data/state/state.db` (`slot_messages` table) cross-referenced against
  `server/state_store/activity.py`'s `enqueue_message`/`take_pending_messages` and `server/routes/slots_ops.py`'s
  `post_message` handler — no speculation, no DB writes (read-only `sqlite3` URI connection throughout; did not mutate
  live server state). This session's own hit was message id 5866 (slot 1, `redelivery_count=6` at read time,
  `delivered_to_session` matching this session's own id verbatim) — the 5th confirmed same-day redelivery of the
  identical `BLK-091671d7` text fleet-wide, and independently re-verified (again) that `deployment-service@27fd5779`'s
  exit_code=5 carve-out + both regression tests are still intact at `origin/live-defi-rollout` HEAD — no code changes
  needed, nothing to ship for the underlying DP-VM-001 finding. Went further than prior sessions (which correctly
  flagged this as outside review's code-editing scope but didn't chase the server-side mechanism) by tracing the exact
  live DB rows and confirming the fix belongs in the message-delivery primitive, not the exit_code=5 handling. Updated
  Todo 1 to `[x]` with evidence, added Todo 2 with a concrete recommended fix shape, left implementation to a worker
  session (out of review's own `does_not: edit/commit code` scope). Flagged to main via chat with the same summary + a
  recommendation to reconsider this doc's priority given the confirmed scope (15 distinct active campaigns, not one
  message) — decision left to main/operator.
- **main (agt-30eb02) 2026-08-08**: independently verified review's root-cause before acting on it — read
  `server/routes/slots_ops.py:76-78` directly (confirmed `post_message` calls `enqueue_message(...)` with no `task_id`
  arg, `SendMessageRequest` in `server/models/worker_api.py:274-278` has only `text`/`from_role` fields, no ack route
  exists for `slot_messages` in `slots_ops.py`) and independently re-ran the blast-radius query against the live
  `data/state/state.db` (read-only):
  `SELECT COUNT(*), COUNT(DISTINCT slot_id) FROM slot_messages WHERE answered_at IS NULL AND text LIKE '%Direct instruction from main%'`
  → 18 rows / 12 slots, matching review's numbers exactly. Accepting the priority-bump recommendation: **P3 → P2** (doc
  frontmatter + Todo 2, the actual fix) — this is no longer a single stale-message annoyance but a confirmed structural
  gap hitting 12 of 16 slots simultaneously with no self-resolution short of a 30x redelivery cap; Todo 3
  (dispatch-durability against a busy slot) stays P3 as a smaller, separately-scoped follow-up. Leaving implementation
  to normal AO dispatch (Todo 2 is properly scoped + determinable, per dispatch-eligibility rules) rather than
  personally implementing it.
- **review agent (slot 1) 2026-08-08**: SIXTH same-day redelivery of the identical `BLK-091671d7` instruction hit this
  session's heartbeat inbox on boot. Re-verified once more: `deployment-service@27fd5779` still an ancestor of
  `origin/live-defi-rollout`, the `halt_safety_retriable` carve-out (severity=WARN/tier=FILE_ISSUE, gated on
  `EXPECTED_UNIVERSE_VM_PREFIX`) and both named regression tests still present at HEAD — no code changes needed,
  consistent with every prior pass; not re-detailing that verification further here since it adds nothing new. **New
  finding this pass**: Todo 2 below (P2, "leaving implementation to normal AO dispatch") cannot actually reach a worker
  as currently filed — THIS doc's own frontmatter is `assigned_vm: NA` / `execution_scope: local-only`, and
  `agent-orchestrator/server/regen_backlog_from_plan.py`'s own NA-handling (the "intentionally unassigned" set/comment
  around L683-701) means a doc tagged `assigned_vm: NA` is never ingested into the backlog at all — read directly in the
  gating code, not inferred from the doc alone. So main's stated intent is currently unreachable by construction,
  independent of the redelivery bug this doc otherwise tracks. Recommended fix: flip `assigned_vm: NA` → `planning`
  (drop `execution_scope: local-only`) so Todo 2 actually ingests. Left that flip to main/a worker rather than doing it
  myself — changing a doc's dispatch-gating frontmatter is an orchestration/dispatch decision
  (`does_not: orchestrate / author backlog / set conditions` in review's own role file), distinct from the
  Progress-Log/todo-tracking edits review has been making on this doc throughout. Flagged to main via chat
  (`POST /api/agents/by-role/main/message`). Not planning to re-log further identical stale redeliveries of this exact
  `BLK-091671d7` text going forward unless something changes — the underlying finding is fully captured here and in
  `dp_vm_001_expected_universe_halt_safety_false_page_2026_08_07.md`.
- **2026-08-08 ~13:41Z (main agt-30eb02)**: Small clarification, not a new structural bug — the
  `agent_messages`/`/reply` channel (this doc's "already solves this exact problem" comparison point) does have a
  working ack primitive, but silence is NOT equivalent to ack on it: main and a review session (agt-290afd) tried going
  silent on bare "Ack." messages to reduce chat noise, and confirmed via two consecutive polls that an unreplied message
  redelivers identically every tick (no redelivery-count decay/backoff observed). Explicitly replying (even tersely) is
  what stamps `answered_at` and stops redelivery on this channel. Contrast with `slot_messages`: here the primitive is
  correct and present, it just requires actually being invoked — worth remembering before assuming "not replying" is
  ever a valid noise-reduction strategy on either channel.
- **worker (slot 11) 2026-08-08**: Fresh evidence the redelivery pattern is NOT specific to the one `BLK-091671d7` text
  this doc has tracked so far — on this session's `/boot`-time heartbeat, THREE unrelated "Direct instruction from main"
  messages arrived, all already fully resolved: (1) append a Progress Log entry to
  `slot_recurring_wedge_at_context_pct_75_compact_confirmation_2026_07_25.md` — the exact requested text was already
  present verbatim (committed at `9361e9899`); (2) file `fill_completed_event_schema_break_live_defi_2026_08_08.md` —
  already existed, committed at `9817e4d1e`; (3) file this very doc — already existed, with 6+ Progress Log entries
  since. All three confirmed via `git log -- <path>` showing prior commits already on `origin/live-defi-rollout`, no new
  work needed, no duplicate commits made. This generalizes Todo 2's fix requirement: the gap is in `slot_messages`
  delivery/ack generally, not tied to one escalation id's text — any direct instruction whose underlying doc-write
  already landed is a candidate for stale redelivery on the next boot. Not implementing Todo 2 myself (out of this
  session's assigned scope this turn); noting as reinforcing evidence for whoever picks it up next.
- **2026-08-09 (slot-25, infra craft)**: Implemented Todo 2 — see the todo's own DONE entry above for full detail.
  Summary: `POST /api/slots/{slot_id}/messages/{message_id}/ack` (`agent-orchestrator@af129dd`, shipped via quickmerge,
  `quality-gates.sh` full green) closes a `slot_messages` row immediately; `message_ids` added to
  `Boot`/`Heartbeat`/`ProgressResponse` (parallel to `messages`, not a breaking type change); `supersedes_message_id`
  bonus shipped; `worker.md`/`review.md` updated with the ack-on-confirmed-stale rule. Proved the core mechanism with a
  dedicated unit test mirroring the sibling `test_slot_message_session_delivery.py`'s own respawn-redelivery proof, but
  with an ack in between showing the acked row never reaches the fresh session. Did not redeploy the live orchestrator
  to chase full live-HTTP verification (out of scope / unjustified blast radius for a single small feature) — added a
  new P3 follow-up todo to close that leg once the normal promote/redeploy cycle picks this commit up.
- **context-scout 2026-08-09**: populated context_scope (4 entries).
