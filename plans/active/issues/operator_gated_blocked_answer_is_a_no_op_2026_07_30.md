---
doc_type: issue
title:
  Answering an [OPERATOR]-gated blocked question is a mechanical NO-OP — all 4 choices (A/B/C/free-text) store a string,
  dead-letter their notification to slot 0, and hide the todo forever without making it dispatchable
summary: >-
  Every [OPERATOR]-tagged plan todo gets a synthetic blocked_queue row (slot_id=0, BLK-op-*) rendered in the dashboard
  with 3 canned options plus free text. Measured live 2026-07-30: answering ANY of them changes nothing actionable. The
  endpoint never touches TaskRow, so the task stays status='blocked' and dispatch (queued-only) skips it forever; the
  notification is enqueued to slot 0's slot_messages, which NOTHING drains (main runs the AgentRow lifecycle, not the
  worker /boot|/heartbeat lifecycle that calls take_pending_messages); and setting answered_at drops the row out of
  /api/state (unanswered_only=True) and the dashboard's pending count, while the never-re-alert dedup guarantees it
  never pages again. Net: answering an operator-gated question makes it INVISIBLE without making it ACTIONABLE. Options
  B and C additionally promise behaviour ("flip the checkbox", "remove this todo from the backlog") that no code
  implements, and option A's text ("leave it open, I'm on it") is contradicted by its own effect. The question itself is
  also unreadable — it embeds the todo's single first PHYSICAL line, so hard-wrapped plan markdown truncates it
  mid-sentence while boilerplate fills the card. Operator ruled the fix 2026-07-30: an answer creates a DISPATCHED task
  carrying (full todo + operator instruction + target role), a new reclassify action with a role dropdown, free text
  routed to a worker that can read compound instructions, a rewritten question leading with the full todo, purple
  outlining for operator-gated cards, and explicitly NO delete/VM-launch refusal guard.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [agent-orchestrator, blocked-queue, operator-gated, dashboard, dispatch, automation-gap, dead-letter]
related:
  [
    /plans/active/issues/deployment_registry_dualwrite_flag_not_propagated_to_vm_launchers_2026_07_30.md,
    /plans/active/issues/per_slot_ff_pull_status_report_crons_stale_fleet_wide_2026_07_27.md,
    /plans/active/issues/plan_quality_four_line_defense_architecture_2026_07_23.md,
  ]
created: 2026-07-30
priority: P1
parent_epic: orchestrator_master
source:
  "operator-directed investigation 2026-07-30 — operator answered
  BLK-op-per_slot_ff_pull_status_report_crons_stale_fleet_wide-002 via the dashboard and asked what consumes the answer;
  live read-only state.db inspection proved nothing does"
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
assigned_vm: planning
sequential: false
resolved_by:
locked_by:
locked_since:
---

> **🟢 ARMED FOR DISPATCH (2026-07-30).** All design forks were ruled by the operator in an interactive session — see §
> "Decisions — RULED 2026-07-30". `sequential: true` is set deliberately, not reflexively: D1, D2 and D3 all edit
> `server/routes/backlog.py`, and this workspace's default is that independent same-priority todos dispatch CONCURRENTLY
> to different workers — which would put three workers in the same file. Same-file overlap is the sanctioned reason to
> serialise a whole plan.

# What I found

Every `[OPERATOR]`-tagged plan todo is seeded into the backlog as `status='blocked'` plus a **synthetic blocked-queue
row** (`slot_id=0`, `blocked_id=BLK-op-<task_id>`) — `agent-orchestrator/server/bootstrap.py:554`. The dashboard renders
it as a question with three canned options:

```
A: I'll do this — leave it open, I'm on it
B: Already done — flip the checkbox in the plan; this entry prunes on the next regen
C: Not needed — remove this todo from the backlog
```

plus a free-text ("Other") box. **All four choices are byte-identical in effect.** Nothing anywhere parses the option
letter — verified by grepping `server/` and `dashboard/src/` for `answer.startswith` / `"A:"` / `"B:"` / `"C:"` /
`option_letter` / `selected_option`: zero hits (the one `startswith("A")` in `server/verify.py:829` is a git status-code
check, unrelated). `dashboard/src/App.tsx:768-782` POSTs the chosen string verbatim; the canned text and free text
travel the same field.

## What answering actually does (`server/routes/backlog.py:796`)

1. `answer_blocked()` sets `answer` / `answered_by` / `answered_at` on the `BlockedRow` — and **only** those three
   fields (`server/state_store/activity.py:48-55`).
2. `enqueue_message(session, slot_id=0, ...)` writes a `slot_messages` row.
3. Unblocks the slot **only if** `SlotRow(0).status == "blocked"` — slot 0 is main, whose status reflects what main is
   itself doing; it is essentially never literally `"blocked"`, so this branch does not fire.
4. Logs `blocked_answered`, posts a Slack ✅ bookend.

**It never touches `TaskRow`.** The task stays `status='blocked'`; dispatch only ever considers `'queued'`. No worker
can be spawned for it, before or after the answer.

## The slot-0 message is a dead letter

`take_pending_messages` — the only function that drains `slot_messages` — is called from exactly 10 sites, **all inside
`server/routes/slots_worker.py`** (`/boot`, `/heartbeat`, `/progress`, `/messages`, …). Main never calls those routes:
it is a PERSISTENT agent tracked via `AgentRow`, explicitly outside the task-worker lifecycle
(`server/routes/state.py:266-272`). So a message addressed to slot 0 is never delivered to anyone.

**Measured live (server clock 2026-07-30 07:28:08):**

| msg id   | slot  | created  | delivered    |
| -------- | ----- | -------- | ------------ |
| 3566     | 7     | 07:18:25 | 07:25:20 ✅  |
| 3564     | 14    | 07:10:17 | 07:18:52 ✅  |
| 3562     | 5     | 07:00:04 | 07:21:31 ✅  |
| 3561     | 10    | 06:53:40 | 07:20:35 ✅  |
| **3563** | **0** | 07:01:36 | **never** ❌ |
| **3560** | **0** | 06:44:29 | **never** ❌ |

Every real worker slot drained its queue within minutes. Both `slot_id=0` rows — the operator's answer (27 min old) and
main's own answer to a different operator-gated row (44 min old) — sat `delivered_at=NULL`, `delivered_to_session=NULL`,
`redelivery_count=0`.

## Answering HIDES it — the silent black hole

`/api/state` returns `ss.list_blocked(session, unanswered_only=True)` (`server/routes/state.py:86`), and the dashboard's
pending count filters `!b.answered_at` (`dashboard/src/layout.tsx:306`). Setting `answered_at` therefore removes the row
from the only blocked-queue surface main watches AND from the operator's own pending list. Meanwhile
`_alert_unanswered_operator_gated_blocks` (`server/bootstrap.py:585+`) dedups on a disk-backed seen-set and selects only
`answered_at IS NULL`, so it never re-pages either.

Net state after answering: task pinned at `status='blocked'` (undispatchable), row invisible to main, invisible in the
dashboard, never re-alerted, plan checkbox still `- [ ]`. Nothing is watching it and nothing will act on it.

## Options B and C promise behaviour that does not exist

- **B** says "flip the checkbox in the plan; this entry prunes on the next regen". Nothing flips the checkbox. The prune
  in `server/regen_backlog_from_plan.py:2225-2258` only fires once a human has already flipped it — so B is a no-op
  unless the work is done manually anyway.
- **C** says "remove this todo from the backlog". Nothing removes it. **Proven live**: main answered
  `BLK-op-deployment_registry_dualwrite_flag_not_propagated_to_vm_launchers-004` with exactly
  `"C: Not needed — remove this todo from the backlog"` at 06:44:29. 44 minutes later the task row was still
  `status='blocked'` and the todo was still present in its plan doc. Even **main's own** answer went nowhere.
- **A** says "leave it open, I'm on it" — but selecting it sets `answered_at`, which is precisely what CLOSES it from
  every pending view. The text and the effect are direct opposites.
- **No option expresses "this isn't actually operator-gated — give it to a worker"**, which is the disposition the
  operator wanted on 2026-07-30 and had to type as free text.

## Why this matters

`[OPERATOR]` gating is used across the corpus for genuinely human-owned work (credentials, prod-GCS deletes, VM
launches). The dashboard presents a decision surface that looks like it drives automation and does not. An operator
reasonably believes they have dispatched/closed/cancelled an item; mechanically nothing happened, and the item is now
harder to find than before they answered. The only thing that currently un-sticks such a todo is a human editing the
plan markdown — which is exactly the manual step the orchestration is supposed to remove.

**The fix is NOT "the operator edits the plan."** It is to make the answer drive the same automated path any other
ruling drives.

## The question text is truncated mid-sentence — and the cap is not the cause

The seeded question embeds `task.brief[:500]`, but the operator sees far less than 500 chars. Live example:

```
[OPERATOR] approval needed — plans/active/issues/deployment_registry_dualwrite_..._2026_07_30.md:

[OPERATOR] P2. Set the AWS SSM parameter `/uts/deployment-registry/firestore-dualwrite=true` (String, region

This todo is operator-gated (no worker will be spawned for it). How do you want to proceed?
```

It stops at "(String, region" — mid-sentence. **`brief` is the todo's single first PHYSICAL line**, and this workspace
hard-wraps plan markdown, so the brief ends wherever prettier happened to wrap (`server/regen_backlog_from_plan.py`
docstring at :1994-2004 states this explicitly). The `[:500]` slice never even engages. This is the same
first-line-truncation defect class already tracked as finding A in
`/plans/active/issues/plan_quality_four_line_defense_architecture_2026_07_23.md`, surfacing in a new place.

Result: the operator is asked to approve a todo whose text they cannot read, while ~2/3 of the visible question is
boilerplate (the full plan path, plus a two-sentence explanation identical on every such row).

**HARD IMPLEMENTATION CONSTRAINT**: do NOT widen `brief` to fix this. `brief` is the regen matching key — orphan
detection, `brief_hash`, and parking-state migration all key on the single-line form
(`server/regen_backlog_from_plan.py:2079`, `:1994-2004`). Changing it silently drops operator parking gates (already
root-caused twice, 2026-07-17). The question builder must read the FULL todo paragraph separately and leave `brief`
alone.

# Decisions — RULED 2026-07-30 (operator, interactive session)

## D1. Slot-0 answers must reach a queue that is actually drained

Route operator-gated (`slot_id=0`) answers to `agent_messages` with `target_role='main'` — the table main demonstrably
DOES drain (rows 2660/2662 delivered to `agt-fd75de`, 2026-07-30). `slot_messages` stays as-is for real worker slots,
which already work correctly.

## D2. Option A must stop closing the row it promises to leave open

Submit option A through the EXISTING `disposition="partial"` path (`partial_answer_blocked`,
`server/state_store/activity.py:58-71`), which deliberately leaves `answered_at` unset so the row stays pending. No new
machinery — that disposition was built for exactly this.

## D3. An operator ruling becomes a DISPATCHED TASK — one mechanism for both new options

The answer never edits plan markdown directly. It creates a worker task carrying three things: **the original todo text
verbatim, the operator's instruction, and a target role.** A normal worker executes it through the ordinary QG →
quickmerge path.

- **Reclassify + role dropdown** = the special case where the instruction is empty and only the role is set.
- **Other / free text** = the general case; role optional, instruction is whatever the operator typed, and it may be
  compound ("assign it to infra role and then do this and do that"). A worker reads prose — which is precisely why no
  `if answer == "C"` option-parsing branch could ever have served this.

Rejected alternatives, recorded so they are not re-proposed: **(a) main edits + pushes the plan itself** — expands
main's authority (main does not push today) and races the fleet at 18-26 commits/hr on the same files; **(b) mutate
`state.db` only** — the plan keeps reading `- [ ] [OPERATOR]` forever, so every hygiene sweep, archival check and human
reader sees open work the DB believes is cancelled; a permanent SSOT disagreement.

**The dispatched task's definition of done MUST include updating the plan doc** (strip `[OPERATOR]`, set
`assigned_role`, flip the checkbox when the work lands). Otherwise the next regen re-seeds the same blocked row and the
loop never terminates.

## D4. NO delete/VM-launch refusal guard — operator ruling, overriding this doc's earlier draft recommendation

An earlier revision proposed refusing reclassify on delete/VM-launch-marked todos. **Operator ruled against it
(2026-07-30)**: most active plans are data-pipeline work that inherently involves deleting or moving data, so such a
guard would refuse nearly every real case and make the feature useless. Reading the todo and writing sound instructions
is the operator's responsibility — at plan-authoring time and at answer time.

This is coherent with D5 rather than in tension with it: the guard was compensating for the operator being unable to SEE
what they were approving. Fixing the question text removes the thing the guard was protecting against.

## D5. Rewrite the question, and mark operator-gated rows visually distinct

- **Lead with the full todo body**, read from the plan (not `brief` — see the constraint above). The operator must be
  able to read exactly what they are approving.
- **Cut the boilerplate**: the full plan path and the identical-every-time two-sentence explanation currently consume
  most of the card while the actual todo is truncated. Plan path becomes secondary metadata.
- **Purple outline** on the dashboard card for operator-gated rows (`BLK-op-*` / `authority="operator"`) so they read as
  categorically different from ordinary worker `/blocked` questions.

## Todos

- [x] ✅ [INFRA] P1. Implement D1 — route `slot_id=0` blocked answers to `agent_messages` (`target_role='main'`) instead
      of the never-drained `slot_messages` queue, keeping worker-slot delivery unchanged; add a regression test
      asserting a slot-0 answer is retrievable by main's drain path (repo: agent-orchestrator). —
      agent-orchestrator@a83050b. `routes/backlog.py`'s `/answer` endpoint now branches on `row.slot_id == 0` and posts
      to `ss.post_agent_message_by_role(target_role="main", direction="to_agent", ...)` instead of `enqueue_message`;
      real worker-slot delivery is byte-for-byte unchanged (verified by a dedicated regression test asserting slot 6's
      own delivery path is untouched). Tests: `test_d1_slot_zero_answer_routes_to_agent_messages_not_dead_letter`,
      `test_d1_real_worker_slot_message_delivery_is_unaffected` (`tests/test_operator_gated_dispatch_ruling.py`).
- [x] ✅ [INFRA] P1. Implement D2 — submit canned option A through the `disposition="partial"` path so the row stays
      open, matching its own text; add a test asserting `answered_at` stays NULL for option A and is set for B/C (repo:
      agent-orchestrator). — agent-orchestrator@a83050b. Server-side auto-upgrade (not a dashboard change): the endpoint
      compares the answer text against a new shared constant (`operator_gated_options.OPTION_A_IN_PROGRESS`, imported by
      both `bootstrap.py`'s seeding and the endpoint so they can never drift) and forces `partial=True` when it matches
      exactly, unless a structured `ruling_action` is also present (D3 is always final). Also fixed a bug this exposed:
      the endpoint's response echoed the client's raw requested `disposition` rather than what was actually applied,
      which would have self-contradicted `operator_pending` on an auto-upgrade. Tests:
      `test_d2_canned_option_a_auto_upgrades_to_partial_despite_default_final`,
      `test_d2_other_free_text_is_not_auto_upgraded`.
- [x] ✅ [INFRA] P1. Add `GET /api/roles` exposing `role_registry.all_roles()`, filtered by lifecycle so persistent
      supervisors (`main`, `review`) are not selectable dispatch targets — the source for D5's role dropdown (repo:
      agent-orchestrator). — agent-orchestrator@a83050b. Implemented with one correction from this todo's original
      wording: filtering by `lifecycle` alone would have wrongly excluded the generic `worker` role (it ALSO declares
      `lifecycle: persistent`, verified by reading every `agents/*.md` file) and wrongly INCLUDED nothing extra, so the
      endpoint instead excludes by the role's own declared `role:` value, `{"project_management", "review"}` —
      `agents/main.md` declares `role: project_management`, not `"main"` (a documented gotcha already called out in
      `role_registry.spec_for_file`'s own docstring). Every other role, including `worker`, is a legitimate dropdown
      choice per D4 below.
- [x] ✅ [INFRA] P1. Implement D3's core — extend `POST /api/blocked/{id}/answer` to accept
      `{action, role, instruction}`, and on a reclassify/instruct answer create the synthetic worker task carrying (full
      original todo text + operator instruction + target role), namespaced off the `blocked_id` so re-answering updates
      rather than duplicates a task (repo: agent-orchestrator). — agent-orchestrator@a83050b. **Corrected mechanism from
      this doc's original wording** (found while implementing, before writing any code — see the design-review note this
      todo's own text should have carried): a DB-only synthetic task would have been invisible to dispatch
      (`dispatch.py` iterates `backlog.tasks`, the yaml-derived in-memory Backlog — never the `tasks` DB table directly)
      AND deleted within one regen tick (the orphan sweep GCs any DB row whose `task_id` isn't in the freshly-derived
      backlog). Fixed by having **regen itself materialize the ruling**: `_materialize_operator_ruling_tasks` reads
      every unconsumed `ruling_action` off a `BLK-op-*` row (raw sqlite3, mirroring `_prune_stale`'s own
      direct-connection pattern) and appends a real `f"{orig_task_id}--ruling"` `BacklogTask` to `backlog.tasks` —
      genuinely dispatchable, with `assigned_role` set from the dropdown/instruction. Its `done_definition` requires the
      plan edit (strip `[OPERATOR]`, set `assigned_role`, flip the checkbox) in the SAME commit as applying the ruling —
      this is what lets `_is_live_ruling_task` (a new, narrowly-scoped orphan-sweep exemption) know when to stop
      treating the ruling task as live: it stays live exactly as long as the ORIGINAL task's own brief is still an open
      plan todo, so both tasks become ordinary orphans on the same tick once the edit lands, via the existing unmodified
      prune mechanism — never touching `brief`/`brief_hash`/orphan-matching for any other task. `AnswerRequest` gained
      `ruling_action: Literal["reclassify", "instruct"] | None`, `ruling_role`, `ruling_instruction`; the endpoint 400s
      if `ruling_action` is set on any row whose `blocked_id` doesn't start with `BLK-op-` (a live worker's own
      operator-escalation, e.g. `authority="operator"` on a real dispatched slot, has nothing to materialize — verified
      against the existing `test_blocked_partial_answer.py` fixture shape, which is exactly this other case). 9 new
      regen-layer tests in `tests/test_regen_backlog_from_plan.py` cover materialization, idempotency across ticks,
      survival while the original todo is open, pruning once the plan edit lands, and a stale ruling whose original task
      is already gone; 4 more endpoint-layer tests cover the 400 guard and forced-final disposition in
      `tests/test_operator_gated_dispatch_ruling.py`.
- [x] ✅ [INFRA] P1. Fix the seeded question text per D5 — read the FULL todo paragraph from the plan doc (NOT `brief`,
      which must stay single-line as the regen matching key), lead the question with it, and demote the plan path plus
      the boilerplate explanation to secondary text (repo: agent-orchestrator). — agent-orchestrator@a83050b. New
      `get_full_todo_text(plan_ref, description)` in `regen_backlog_from_plan.py` re-reads the plan file fresh and
      returns the checkbox line + its full continuation block (mirroring `_parse_open_todos`'s own continuation-scan
      logic, kept separate rather than widening that function's return shape); falls back to `description` verbatim if
      the plan is unreadable or the line can no longer be found. `bootstrap.py`'s operator-gated seeding now leads the
      question with this full text, with the plan path + boilerplate explanation demoted to a trailing line. Tests:
      `test_get_full_todo_text_returns_full_continuation_block`,
      `test_get_full_todo_text_falls_back_to_description_when_line_not_found`,
      `test_get_full_todo_text_falls_back_when_plan_unreadable`.
- [x] ✅ [UI] P1. Dashboard: add the reclassify action with a role dropdown sourced from `GET /api/roles`, a free-text
      instruction box, and a purple outline on operator-gated (`BLK-op-*` / `authority="operator"`) cards distinguishing
      them from worker `/blocked` questions (repo: agent-orchestrator — `dashboard/src/`). — agent-orchestrator@97a4864.
      `BlockedCard` (`dashboard/src/layout.tsx`) now: (1) renders a purple `authority-operator-gated` outline +
      "operator-gated" badge for any `blocked_id` starting `BLK-op-`, distinct from the existing amber
      `authority-operator` style kept for a live worker's own operator escalation; (2) a "Reclassify to role…"
      `<select>` populated from `roles` (already fetched app-wide via the pre-existing `GET /api/roles` — **this todo's
      own earlier `GET /api/roles` addition was reverted**, see the fix commit noted below, and the role list is instead
      filtered client-side, excluding `project_management`/`review`) that submits `ruling_action="reclassify"`; (3) the
      free-text box, for these rows only, submits `ruling_action="instruct"` with no content guard, per D4. `types.ts`
      gained `BlockedRuling`; `api.ts`'s `answerBlocked` and `App.tsx`'s `onAnswerBlocked` thread it through. New spec
      `dashboard/tests/e2e/reclassify-blocked.spec.ts` (3 tests: purple styling + reclassify-to-worker dispatch,
      free-text instruct, negative check an ordinary card is unaffected) — `pw:L2 ✓`
      (`npx playwright test --project=chromium`, 12/12 passed including the 9 pre-existing specs unaffected). Evidence:
      `quality-gates.sh` green (2028 backend + 165 vitest passed, tsc clean).

      **Also found and fixed while implementing** (not part of this todo's original scope, but load-bearing for it):
                                                  this todo's OWN earlier `GET /api/roles` addition (previous todo above, `agent-orchestrator@a83050b`) registered
                                                  a SECOND route at the same path as a pre-existing `GET /api/roles` in `server/routes/roles.py`, and
                                                  `include_router()` order meant the new thin one silently shadowed the real, richer one on every dashboard page
                                                  load — `RolesPanel` (rendered unconditionally, not gated to any tab) calls `r.skills.map(...)`, so every
                                                  authenticated dashboard load threw an uncaught `TypeError` and rendered blank. Live-confirmed via the operator's
                                                  own browser console (`layout.tsx:3711`, `Cannot read properties of undefined (reading 'length')`). Fixed by
                                                  deleting the duplicate route — `agent-orchestrator@40fafaa`, shipped ahead of the UI commit above.

- [ ] [REVIEW] P1. End-to-end verification on the live orchestrator: answer a real `BLK-op-*` row with a reclassify and
      again with a compound free-text instruction; confirm a worker task is created, dispatched, the work executed, and
      the plan doc updated (tag stripped / role set / checkbox flipped) — cite fresh evidence, do not reuse this doc's
      measurements (repo: agent-orchestrator / unified-trading-pm).
- [ ] [INFRA] P2. Fix a race in `get_full_todo_text()` (D5): the full-text lookup reads `_pm_repo_path()`'s checkout at
      the exact moment a `BLK-op-*` row is first seeded, but that checkout is only kept current by `pm-pull.timer`
      (external 5-min cron) — a freshly-created `[OPERATOR]` todo (in a plan that itself just landed) can race the seed
      against the pull and silently fall back to the truncated single-line `brief` + boilerplate (`get_full_todo_text`'s
      own documented fallback path — never raises, so this is invisible unless someone reads the rendered question).
      **Measured live 2026-07-30**: all 3 currently-pending `BLK-op-*` rows
      (`tradfi_manifest_consolidator_fred_widespan_     stall-001`,
      `sports_manifest_consolidator_zero_growth_stall-004`, `defi_cefi_venue_chain_axis_contamination-006`) hit exactly
      this fallback — re-running the identical match against the same file moments later (after the next pull) found the
      exact line + all continuation lines correctly, confirming it's a timing race, not a logic bug in the
      regex/matching itself. **Worse than "transient"**: the fallback is PERMANENT, not self-healing — `bootstrap.py`
      only seeds a `blocked_id` once (`if session.get(BlockedRow, blocked_id) is None:`), so a row that loses this race
      stays truncated forever; it is never re-seeded once the checkout catches up. Fix options to weigh: (a) retry
      `get_full_todo_text()` once after a short delay / on next regen tick if the first lookup fell back, gated on the
      row still being unanswered; (b) have the operator-gated seeding step wait for `_pm_repo_path()`'s HEAD to match
      the task's own originating commit before seeding; (c) accept the fallback but make it distinguishable in the UI
      (e.g. a "full text unavailable — refreshing" state) rather than silently rendering a truncated question as if it
      were complete. Repo: agent-orchestrator.
- [x] ✅ [DOC] P2. Once the above ship, add the codex SSOT for the operator-gated blocked-row lifecycle end-to-end under
      `codex/12-agent-workflow/` — no doc currently describes it (repo: unified-trading-pm). —
      unified-trading-pm@ed9d02582. New `/codex/12-agent-workflow/operator-gated-blocked-row-lifecycle.md`: seeding, the
      three canned options + D2's auto-upgrade, the D3 ruling mechanism (endpoint stores → regen materializes → a real
      dispatchable `--ruling` task, gated on `done_definition` requiring the plan edit in the same commit so both tasks
      become ordinary orphans together), the dashboard's purple/reclassify/instruct UI, and a note on the
      duplicate-`/api/roles` regression found while building it. `docspec.py --check --soft`: hard=0 soft=0.

## E2E verification fixture for the [REVIEW] todo above (temporary, added 2026-07-30)

The only live `BLK-op-*` row in the corpus right now is a genuinely contested cross-AG architecture question
(`defi_cefi_venue_chain_axis_contamination-006`) — not appropriate for a reviewer to rule on just to exercise this
mechanism. These two todos are deliberately bounded, judgment-free, safe-to-dispatch fixtures whose sole purpose is to
seed real `BLK-op-*` rows to drive through the live reclassify + compound-instruction answer paths. Both todos (and
their materialized `--ruling` tasks) are removed from this doc once the [REVIEW] todo above cites their evidence.

**Fixture A/B (original, 2026-07-30 11:16) superseded below — do not use for evidence.** Both were regen-wired under
this plan's OWN `sequential: true` (in effect until this doc's later `eea7e1c06` flip to `false`), so their materialized
`--ruling` tasks came out permanently prereq-chained to the `[REVIEW]` todo itself (a genuine, separate regen bug —
same-plan `completed_tasks` links never get stripped when a plan flips `sequential` false, fixed at
`agent-orchestrator@93862de`, filed as its own issue at
`/plans/active/issues/ao_self_pull_wedged_by_main_inbox_untracked_file_2026_07_30.md` since the fix also turned out to
be blocked from reaching the LIVE orchestrator by an unrelated ~7h deploy-currency wedge). Fixed or not, using A/B as
this todo's evidence would be circular: their `--ruling` tasks cannot dispatch until the `[REVIEW]` todo itself is
marked done. Fixture C/D below were added AFTER the `sequential: false` flip, so they regen with no same-plan chain at
all, sequential-bug or not.

- [ ] [OPERATOR] P1. E2E fixture A (reclassify test, safe/no-judgment, temp, SUPERSEDED — see note above): print
      `RULES.md`'s line count.
- [ ] [OPERATOR] P1. E2E fixture B (free-text test, safe/no-judgment, temp, SUPERSEDED — see note above): print
      `agent-orchestrator`'s short SHA.
- [ ] [OPERATOR] P1. E2E fixture C (reclassify test, safe/no-judgment, temp): print `worker.md`'s line count.
- [ ] [OPERATOR] P1. E2E fixture D (free-text test, safe/no-judgment, temp): print the current UTC date via `date -u`.

# Codex SSOTs

`/codex/12-agent-workflow/operator-gated-blocked-row-lifecycle.md` — the SSOT this issue's `[DOC]` todo added
(unified-trading-pm@ed9d02582), describing the mechanism end-to-end as it now works.
`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`,
`/codex/04-architecture/agent-orchestrator-alerting.md` (actionable-only + ✅-close-bookend convention this gap silently
violates — the bookend fires for an answer that did nothing), `/codex/06-coding-standards/ui-testing-layers.md` (the
`[UI]` + `pw:L2` gate on the dashboard todo). Note `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` is
deliberately NOT a constraint here — see D4, the operator ruled against a delete/VM-launch refusal guard.
