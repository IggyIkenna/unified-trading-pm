---
doc_type: issue
title:
  "Blocked-question UX doesn't scale and loses context once the asking agent dies — operator design input for
  escalation_and_disaster_recovery_master's E1 (deliberately NOT scoped or actioned yet)"
summary:
  Operator-reported pain, live-experienced this session (2026-07-24, the BLK-f09e9ca9/slot-2 episode) — a blocked
  question's stated question+options often don't carry enough context for an informed decision; at scale (up to ~30 open
  questions) that ambiguity compounds; the same question sometimes gets asked by multiple different agents, or multiple
  times by different sessions on the same slot; and when the operator needs to go back and ask the ORIGINATING agent for
  more context, that agent is frequently already dead. Operator's own proposed direction — a stable id per question that
  jumps straight to the asking session's transcript — is technically groundable (a durable session-transcript renderer
  already exists) but nothing wires it to the blocked-question path today. Operator explicitly deferred this — broader
  than E1's scoped-link fix, a real UX/API redesign, pick up later.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, deployment-ui]
scope: [engineer, admin]
tags: [agent-orchestrator, blocked-questions, escalation, ux, dashboard, dead-agent-context]
related:
  [
    /plans/epics/escalation_and_disaster_recovery_master.md,
    /plans/archive/issues/dispatch_sequential_gate_fix_2026_07_24.md,
    /plans/active/blocked_question_payload_quality_and_condition_retirement_2026_08_10.md,
  ]
created: 2026-07-24
author: unknown
last_updated: 2026-07-24
priority: P2
parent_epic: escalation_and_disaster_recovery_master
source: "Operator design context, relayed 2026-07-24 after the /api/escalation/{id} scope question"
assigned_vm: planning
execution_scope: orchestrator-agent
estimate_class: design
drift_direction: advance-code
resolved_by:
locked_by:
depends_on: []
context_scope:
  [
    /plans/epics/escalation_and_disaster_recovery_master.md,
    /plans/archive/issues/dispatch_sequential_gate_fix_2026_07_24.md,
    agent-orchestrator/server/transcript_log.py,
    agent-orchestrator/server/orm.py,
    /plans/archive/issues/operator_gated_blocked_answer_is_a_no_op_2026_07_30.md,
    /plans/active/blocked_question_payload_quality_and_condition_retirement_2026_08_10.md,
  ]
---

## The pain, in the operator's own framing

1. **Insufficient context to decide.** A blocked question's `question` + `options[]` text sometimes doesn't cover
   everything actually needed to make an informed call — the worker researched its own angle, but the operator may need
   context the worker never thought to include.
2. **Scale.** With up to ~30 blocked questions open at once, this ambiguity compounds — hard to tell which are urgent,
   which are duplicates, which need a real decision versus a rubber-stamp.
3. **Duplication.** The same underlying question sometimes gets asked by multiple different agents independently, or
   multiple times by different sessions that occupied the same slot (a respawn re-asking something an earlier session on
   that slot already asked) — no dedup, no "this was already answered elsewhere" surfacing.
4. **Dead-agent unreachability.** The single most disruptive pattern: the operator wants to ask the ORIGINATING agent a
   follow-up ("what did you mean by X", "why didn't you consider Y") and that agent is already dead — no live worker to
   ask, and no easy path back to what it was actually looking at when it asked.

This is not hypothetical — it is exactly what happened this session (see
[`/plans/archive/2026_07/ao_remediation_a_independent_fixes_2026_07_23.md`](/plans/archive/2026_07/ao_remediation_a_independent_fixes_2026_07_23.md),
which shows BLK-f09e9ca9 against todo -008, and the `pre-compact` summary): BLK-f09e9ca9 (task
`ao_remediation_a_independent_fixes-008`) was answered at 06:38 UTC, but the worker that asked it had already skipped
the task and gone idle at 06:35 — by the time the answer was enqueued there was no live session to receive it, and the
operator's only path to more context on what that worker actually saw would have been its transcript, not a live re-ask.

## Operator's proposed direction

Assign each blocked question a stable id (it already effectively has one — `BlockedRow.blocked_id` — but it isn't
surfaced as a navigable handle), and use it to jump DIRECTLY into the session that asked it, rather than only into the
live slot (which may since have respawned to a different, unrelated session).

## What already exists that this could build on

- **`server/transcript_log.py`** — the dashboard's "Show log" already renders a durable, complete transcript from
  Claude's own JSONL log file, keyed by the globally-unique `claude_session_id` (survives respawns and TUI redraws —
  built specifically because `tmux capture-pane` returns only ~24 lines of an alternate-screen TUI). The retrieval
  PRIMITIVE already works.
- **The gap**: `BlockedRow` (`server/orm.py`) stores `blocked_id`, `slot_id`, `task_id`, `question`, `options_json`,
  `recommendation`, `authority`, plus the answer fields — **it does NOT store `claude_session_id`**. So even though a
  transcript render exists, nothing captures WHICH session asked a given blocked question at creation time. Once the
  slot respawns (exactly what happened in the BLK-f09e9ca9 episode), `slot_id` alone points at the CURRENT session, not
  the one that actually asked — the one piece of information the operator would need to go "back" is silently dropped
  the moment a respawn happens.
- No existing dedup / similarity surfacing across `BlockedRow` entries, and no existing "N other open questions look
  like this one" signal.

## Why this is bigger than E1

`escalation_and_disaster_recovery_master`'s E1 (role-agnostic escalation pipeline, paused, 5 UNBUILT todos) already
plans a scoped `/escalation/{id}` link and an `open/in-progress/resolved` state machine — necessary but NOT sufficient
for this. E1 as scoped doesn't address: capturing `claude_session_id` at creation time, surfacing a transcript-jump
affordance in the resolution UI, cross-question dedup/similarity, or any policy for what to show when the transcript's
own session has ALSO expired/rotated out from under the id. Those are real, unscoped design decisions — exactly what the
operator flagged as "we can pick this up again afterwards, not now."

## Explicitly NOT actioned

No code, no UI mockup, no plan authored. This doc exists so the context isn't lost before E1 (or a wider blocked-
questions redesign) is picked up. When it is: read this doc + `escalation_and_disaster_recovery_master`'s "Why this epic
exists" section together before scoping the workstream.

## Progress Log

- **2026-07-24**: Filed verbatim from operator context, prompted by clarifying `/api/escalation/{id}`'s scope. Grounded
  the "jump to session" idea against `transcript_log.py` (retrieval already works) and `BlockedRow`'s schema (the
  missing link is `claude_session_id` capture at creation time). Deliberately deferred per operator instruction.
- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid — the doc carries a section titled `Explicitly NOT actioned`
  recording an explicit operator deferral ('pick this up again afterwards, not now'), and its one todo is a `[DESIGN]`
  scoping task (an open-ended design call, not a bounded outcome). Same ruling already recorded in
  `ao_satellite_ao_dispatch_batch1_2026_07_26.md`'s operator-decision Deferred list.
- **2026-07-31 (operator direction)**: Operator says this is resolved via
  `/plans/archive/issues/operator_gated_blocked_answer_is_a_no_op_2026_07_30.md` (D1-D5, live in prod). Cross-checked
  that doc's actual scope against this one's 4 pain points: **pain point 1 (insufficient context) is genuinely fixed**
  for operator-gated (`BLK-op-*`) rows — D5 rewrote the seeded question to lead with the full todo body instead of a
  truncated single line. D1-D3 also give operator-gated rulings a real dispatch path (not relevant to this doc's
  complaint, but adjacent). **Not obviously covered by D1-D5's scope**: pain points 2 (scale/triage across ~30 open
  questions), 3 (cross-question dedup), and 4 (dead-agent unreachability — capturing `claude_session_id` on `BlockedRow`
  at creation + a transcript-jump UI affordance) — D1-D5 is specifically about the OPERATOR-GATED answer-to-dispatch
  mechanism, and neither `BlockedRow`'s schema nor the dashboard's resolution UI appear to have gained a
  session-id/transcript-jump field per that doc's own todo list. Flagging this gap rather than silently closing it — if
  pain points 2-4 are also considered covered or no-longer-wanted, this doc should archive pointing at the resolving
  doc; if they're still real, worth splitting into a narrower follow-up scoped to just those three. Deferring the
  archive-or-split call to the operator rather than guessing.
- **context-scout 2026-08-01**: populated context_scope (4 entries).
- **context-scout 2026-08-03**: re-verified context_scope (5 entries — corrects the 2026-08-01 marker's stale count, the
  list itself already carried 5) — all still resolve; still covers the doc's live remaining scope (pain points 2-4:
  scale/triage, dedup, dead-agent transcript-jump), unaffected by the same-day canned-options-B/C fix noted below.
- **2026-08-03**: operator asked (fresh, unprompted by this doc) why so many operator-blocking questions stay open and
  what answering them actually does — independent confirmation this doc's pain points are still live, ~9 days after the
  2026-07-31 entry above flagged them as possibly-still-open. Investigation this session also found, and fixed, a
  concrete THIRD instance of "an answer option does nothing": canned options B/C on operator-gated cards were submitting
  as plain final answers with no dispatch mechanism, unaffected by D1-D5 despite the archived doc's own text describing
  exactly this failure mode — see `/plans/active/issues/ao_operator_gated_canned_options_bc_still_no_op_ 2026_08_03.md`
  (resolved, agent-orchestrator@5bfde668). That fix does NOT touch this doc's own remaining scope (pain points 2-4:
  scale/triage, cross-question dedup, dead-agent transcript-jump) — those are still real and still unscoped. Not
  archiving this doc or auto-picking a direction on its `[DESIGN]` todo below (an open-ended scoping call, correctly
  staying a human decision per this doc's own frontmatter) — flagging the renewed operator pain as a signal it may be
  worth un-deferring, not deciding that myself.
- **context-scout 2026-08-05**: re-scouted; context_scope unchanged (5 entries), still accurate.

## Todos

- [x] ✅ [DESIGN] P2. **DECIDED — operator ruling 2026-08-08** (ao round-5 apply session, item 5 —
      /plans/active/issues/ao_round5_apply_session_operator_qa_index_2026_08_08.md): "All three: session_id capture +
      transcript-jump + dedup/similarity." Scope the blocked-question UX redesign — capture `claude_session_id` on
      `BlockedRow` at creation time, wire a transcript-jump affordance into the resolution UI, and address
      cross-question dedup/similarity; explicitly deferred by the operator 2026-07-24, renewed interest 2026-08-03,
      direction finally chosen 2026-08-08. Split into 3 concrete build todos below, each independently shippable
      (file-disjoint: schema/backend, UI, and a separate dedup query surface).
- [x] ✅ [BACKEND] P2. **Capture `claude_session_id` on `BlockedRow` at creation time.** — agent-orchestrator@37f73f9.
      Added the nullable `claude_session_id` column (orm.py) + idempotent migration
      (`_migrate_blocked_queue_claude_session_id` in bootstrap.py, mirrors
      `_migrate_slot_message_task_scoped_delivery`'s no-backfill pattern), populated at the real worker `/blocked`
      endpoint (`routes/slots_worker.py::blocked_slot`) by reading the slot's CURRENT `claude_session_id` before insert
      (the synthetic slot_id=0 rows in bootstrap.py/plan_health.py stay NULL — no originating worker session).
      `tests/test_blocked_claude_session_id_capture.py` proves: capture at creation, survival across a simulated respawn
      (the exact BLK-f09e9ca9 failure mode), and NULL-safety when the slot has no session id. `quality-gates.sh` green.
      Repo: agent-orchestrator.
- [x] ✅ [UI] P2. **Wire a transcript-jump affordance into the blocked-question resolution UI** —
      agent-orchestrator@c6273b2, using the `claude_session_id` from the todo above and the already-working
      `server/transcript_log.py` retrieval primitive (the dashboard's existing "Show log" render, keyed by
      `claude_session_id` — reuse it, don't rebuild it). Add a "View asking session's transcript" link/button on each
      open `BlockedRow` card in whichever dashboard component renders the blocked-questions queue (`deployment-ui`), so
      the operator can jump straight to what the asking agent actually saw, even if that agent/slot is now dead or
      respawned to a different session. Handle the case where the transcript file has itself rotated out
      (`claude_session_id` present but no matching JSONL) with a clear "transcript no longer available" state, not a
      silent failure. **Done when**: a live blocked question shows a working transcript-jump link, a
      dead-agent/respawned-slot case is manually verified to still resolve to the ORIGINAL session's transcript (not the
      current occupant's), `pw:L2` Playwright coverage per this workspace's UI gate, and `tsc`/`vitest` clean. Repo:
      deployment-ui. Depends on the `[BACKEND] P2` todo above (needs the column populated first) — sequence via
      `sequential: true` if these are ever pulled into their own dispatched plan.
- [ ] [BACKEND] P3. **Cross-question dedup/similarity surfacing.** Add a lightweight similarity signal across open
      `BlockedRow` entries (per this doc's pain point 3: the same underlying question sometimes gets asked by multiple
      different agents, or multiple times by different sessions on the same respawned slot) — start with an
      exact/near-exact `question` text match (normalized whitespace/case) grouped and surfaced as "N other open
      questions look like this one" on the dashboard queue, rather than a full embedding-similarity system (that's a
      much bigger build with no stated operator appetite yet — start cheap, revisit if exact-match dedup proves
      insufficient in practice). **Done when**: two blocked questions with matching normalized text are visibly
      grouped/flagged in the dashboard queue API response, a regression test covers the grouping logic, and
      `quality-gates.sh` is green. Repo: agent-orchestrator (+ `deployment-ui` render of the grouping signal, small).

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.
- **context-scout 2026-08-07**: re-scouted; context_scope unchanged (5 entries), still accurate.
- **na-eligibility-audit 2026-08-07** (ao tranche, batch3of3): KEEP-NA, valid — re-verified end-to-end; sole open item
  (`[DESIGN] P2`, blocked-question UX redesign) remains an open-ended scoping call explicitly deferred by the operator
  2026-07-24, unchanged since the 2026-08-06 marker.
- **2026-08-08 (ao round-5 operator Q&A apply session, item 5)**: operator ruling — "All three: session_id capture +
  transcript-jump + dedup/similarity." Closed the `[DESIGN]` scoping todo and filed 3 concrete build todos (backend
  `claude_session_id` column+migration, UI transcript-jump affordance depending on it, backend+UI dedup surfacing).
  Flipped `assigned_vm: NA` → `planning` / `execution_scope: local-only` → `orchestrator-agent` — the design gate is
  resolved and the remaining work is bounded, matching the operator's general preference (recorded on item 6 of this
  same apply session) to default to AO-dispatched plans once a LOCAL-vs-AO fork like this resolves.
- **2026-08-08 (slot-11, ui_developer, dispatched onto `-002`)**: dispatcher offered the `[UI] P2` transcript-jump todo
  (task `blocked_questions_ux_redesign_context_loss_and_scale-002`) while its own stated dependency, `[BACKEND] P2`
  (`-001`, `claude_session_id` capture), was still `queued`/undispatched — confirmed live via the backlog API, and
  confirmed in code that `BlockedRow` (`agent-orchestrator/server/orm.py:334-374`) has no `claude_session_id` column
  yet. The UI todo's own text already flagged this ("sequence via `sequential: true` if these are ever pulled into their
  own dispatched plan") but no such gate exists on this doc, so the backlog derivation offered `-002` with no prereq
  enforcement. Declining via `POST /api/slots/11/skip-current-task` (`reason_code: GATED`, no `park_now` — the
  dependency is a small, actively-queued in-plan task expected to land soon, not an external gate needing a durable
  park) rather than doing the backend column work myself (out of ui_developer craft scope per `ui_developer.md`) or
  building the UI against a field that doesn't exist yet (unverifiable per the todo's own done-when). Filed the
  `[INFRA]` todo below so this doesn't silently re-happen once `-001` lands and `-002` re-dispatches.
- **2026-08-08 (slot-27, ui_developer, dispatched onto `-002`, second occurrence)**: same gate gap slot-11 hit earlier
  today — re-confirmed live via `GET /api/backlog` that `-001` is still `status: queued, dispatched_to: null` and via
  `grep -n "claude_session_id" agent-orchestrator/server/orm.py` that `BlockedRow` (line 334-382) still has no such
  column. Declined via `POST /api/slots/27/skip-current-task` (`reason_code: GATED`, no `park_now`, same rationale as
  slot-11). The `[INFRA]` todo below (attach `prereqs.completed_tasks: [-001]` to `-002`'s derived backlog row) is the
  actual fix for this recurring dispatch gap and is still unactioned — not doing it myself here since it's outside
  `ui_developer` craft scope and isn't this session's dispatched task (per worker.md, "I see related work" is not a
  valid reason to fan out to untasked work); leaving it to dispatch normally to an `infra`-capable worker.
- **2026-08-08 (slot-14, backend_engineer, dispatched onto `-001`)**: shipped the `[BACKEND] P2` `claude_session_id`
  capture todo — agent-orchestrator@37f73f9 (column + migration + population at `blocked_slot` + 3 regression tests,
  `quality-gates.sh` green). The `-002`/`-001` dispatch-gate gap slot-11 and slot-27 both hit today (this doc's
  `[INFRA] P3` todo below) is now moot for THIS specific pair — `-001` is done, so `-002` re-dispatching no longer races
  an undone dependency. The `[INFRA]` todo itself (a general fix so the same gate-gap pattern doesn't recur on a future
  todo pair) is still open and unactioned; leaving it as-is for an `infra`-capable worker, per worker.md's "I see
  related work" not being a valid reason to fan out beyond this session's dispatched task.

## Todos (continued)

- [ ] [INFRA] P3. **Gate `-002` (UI transcript-jump) behind `-001` (BACKEND `claude_session_id` capture) so the
      dispatcher can't offer the UI todo before its dependency lands** — confirmed 2026-08-08 (slot-11) that it can:
      `-002` was dispatched while `-001` was still `queued`. Per CLAUDE.md's "partial-parallelism isn't expressible in
      one plan → SPLIT" guidance, `sequential: true` on this whole doc would over-serialize (it would also block the
      independent `[BACKEND] P3` dedup todo behind the UI todo for no reason) — either split the UI todo into its own
      `depends_on`-gated companion doc, or attach a
      `prereqs.completed_tasks: [blocked_questions_ux_redesign_context_loss_and_scale-001]` tuning entry to `-002`'s
      derived backlog row (RULES.md §4/§5) once regen re-derives it. Repo: unified-trading-pm (doc restructure) or
      agent-orchestrator (if `regen_backlog_from_plan.py` needs a new per-todo `depends_on_todo` primitive to express
      this without a doc split — worth checking before hand-rolling the split).

- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (5 entries), still accurate.
- **2026-08-10 (cross-link, slot-3 interactive)**: linked
  [`/plans/active/blocked_question_payload_quality_and_condition_retirement_2026_08_10.md`](/plans/active/blocked_question_payload_quality_and_condition_retirement_2026_08_10.md)
  in both directions. That plan is a LOCAL/human companion covering a DISJOINT axis — blocked-question **payload
  sufficiency** (the `plan_health` `doc_drift` path raises undecidable questions) and **condition-derived
  auto-retirement** (a `doc_drift:<key>` row can never retire, since all three `classify_retirement` exits resolve a
  `TaskRow`). This doc's remaining scope (transcript-jump, dedup/similarity) is untouched by it; neither supersedes the
  other. **Correction owed to this doc, tracked as that plan's todo D**: the `[UI] P2` transcript-jump todo says "Repo:
  deployment-ui" and `repos:` lists `deployment-ui`, but the blocked-question queue is rendered ONLY by
  `agent-orchestrator/dashboard/src/layout.tsx` (`BlockedCard`) — `deployment-ui` has zero blocked-question code
  (verified 2026-08-10; its only `blocked` matches are `promotion_blocked` PR counters in `Cockpit.tsx`). Both
  `ui_developer` workers dispatched onto that todo (slot-11, slot-27, 2026-08-08) declined it as GATED on the backend
  dependency and neither caught the wrong repo.
