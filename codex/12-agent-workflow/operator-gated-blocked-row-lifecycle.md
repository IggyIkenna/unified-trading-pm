---
doc_type: codex-ssot
title: Operator-gated blocked-row lifecycle (BLK-op-*)
summary:
  SSOT for how an `[OPERATOR]`-tagged plan todo's synthetic blocked-queue row (`slot_id=0`, `blocked_id=BLK-op-*`)
  behaves end-to-end — seeding, the three canned options plus a structured reclassify/instruct ruling, how a ruling
  becomes a real dispatchable task via regen materialization, and the dashboard's purple-outline treatment. Before
  operator_gated_blocked_answer_is_a_no_op_2026_07_30, answering one of these rows was a mechanical no-op (dead-lettered
  notification, no TaskRow mutation, silent disappearance); this doc describes the fixed, current behavior.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [orchestrator, blocked-queue, operator-gated, dashboard, dispatch, regen, reclassify]
related:
  [
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /codex/04-architecture/agent-orchestrator-alerting.md,
    /codex/06-coding-standards/ui-testing-layers.md,
    /codex/05-infrastructure/claude-code-settings-symlink.md,
  ]
created: 2026-07-30
authoritative_for: [operator-gated-blocked-row-lifecycle, blk-op-ruling-mechanism, reclassify-instruct-ui]
referenced_by:
  [
    /plans/archive/issues/operator_gated_blocked_answer_is_a_no_op_2026_07_30.md,
    /plans/active/issues/ao_operator_gated_canned_options_bc_still_no_op_2026_08_03.md,
  ]
owner:
last_reviewed: 2026-08-03
code_refs:
  [
    agent-orchestrator/server/bootstrap.py,
    agent-orchestrator/server/operator_gated_options.py,
    agent-orchestrator/server/routes/backlog.py,
    agent-orchestrator/server/regen_backlog_from_plan.py,
    agent-orchestrator/server/state_store/activity.py,
    agent-orchestrator/dashboard/src/layout.tsx,
    agent-orchestrator/dashboard/src/App.tsx,
  ]
source:
  "operator_gated_blocked_answer_is_a_no_op_2026_07_30 — operator-directed investigation + interactive ruling session,
  2026-07-30"
---

# Operator-gated blocked-row lifecycle (`BLK-op-*`)

> Codified 2026-07-30 per `/plans/archive/issues/operator_gated_blocked_answer_is_a_no_op_2026_07_30.md`, which has the
> full root-cause writeup, the live measurements that proved the pre-fix behavior was a no-op, and the rejected
> alternatives. This doc describes the mechanism as it now works — read the issue doc for the "why", not this one.

## What triggers a `BLK-op-*` row

Any plan todo authored with an `[OPERATOR]` tag is seeded into the backlog with `TaskRow.status='blocked'` **plus** a
synthetic blocked-queue row — `blocked_id=f"BLK-op-{task.id}"`, `slot_id=0`, `authority="operator"`
(`agent-orchestrator/server/bootstrap.py`). `slot_id=0` is a sentinel — there is no real worker slot 0; it means "no
worker was ever spawned for this todo." This is distinct from a **live worker's own operator escalation** (a real worker
on a real slot hits a decision only a human should make and sets `authority="operator"` on its own blocked row) — that
shape has a live worker behind it and is not eligible for a ruling (see below).

The question text leads with the **full todo paragraph**, re-read fresh from the plan file (`get_full_todo_text()` in
`regen_backlog_from_plan.py`) — not `task.brief`, which is deliberately kept to the todo's single first physical line
(the regen matching key for orphan detection / `brief_hash` / parking-state migration; never widen it to fix a display
problem). The plan path and boilerplate explanation are demoted to a trailing line.

**Seed-time checkout race, self-healed on later regen ticks.** This read hits `_pm_repo_path()`'s local PM checkout at
the exact moment the row is first seeded, but that checkout is only refreshed by the external `pm-pull.timer` cron — a
freshly-created `[OPERATOR]` todo (in a plan that itself just landed) can race the seed against the pull and fall back
to `task.brief` alone. `get_full_todo_text()` is a thin wrapper over `get_full_todo_text_with_status()`, which also
reports whether the full continuation block was actually located; `BlockedRow.question_text_incomplete` records a
fallback at seed time, and `bootstrap._maybe_refresh_operator_gated_question_text()` retries the lookup on every later
`sync_backlog_to_db()` tick for an already-existing `TaskRow` while the flag stays set and the row is unanswered —
overwriting `question` and clearing the flag the moment a retry locates the full text. So a row that loses the seed-time
race self-heals within a few regen ticks instead of staying truncated forever.

## Answering the row: three paths

`POST /api/blocked/{blocked_id}/answer` (`server/routes/backlog.py`) branches on what the operator sent:

1. **Canned option A** (`"A: I'll do this — leave it open, I'm on it"`) — matched verbatim against
   `operator_gated_options.OPTION_A_IN_PROGRESS`, the single source of truth shared with `bootstrap.py`'s seeding so the
   two can never drift apart. Auto-upgrades to `disposition="partial"` (`server/state_store/activity.py`'s
   `partial_answer_blocked`) so `answered_at` stays `NULL` and the row stays in every pending view — matching what the
   option's own text promises.
2. **Canned options B/C** (already done / not needed) — as of
   `ao_operator_gated_canned_options_bc_still_no_op_2026_08_03` (agent-orchestrator@5bfde668), the dashboard submits
   these as a structured ruling too: `rulingForCannedOption()` (`dashboard/src/layout.tsx`) sends
   `ruling_action="instruct"` with a canned instruction — "verify it's actually done, then flip the checkbox with
   evidence" for B, "flip the checkbox with a one-line rationale, don't delete the line" for C — byte-identical in shape
   to what typing free text already does, so these go through the exact same materialization path as path 3 below.
   Before that fix, B/C submitted a plain final answer that nothing materialized — the D3 mechanism below only ever
   covered the reclassify dropdown and the free-text box, never the two canned buttons, despite
   `operator_gated_blocked_answer_is_a_no_op_2026_07_30`'s own investigation describing this exact failure mode for B/C
   (it just never got fixed for them specifically). Option A is untouched — it stays a plain canned answer; forcing a
   ruling onto it would incorrectly make it `disposition="final"` (see path 1 above and the endpoint's own
   `if req.ruling_action is not None: partial = False`).
3. **A structured ruling** (`ruling_action: "reclassify" | "instruct"`) — see below. Rejected with `HTTPException(400)`
   if `blocked_id` doesn't start with `BLK-op-` (a live worker's own escalation has a direct message channel already —
   nothing to materialize).

Every answer's `slot_id=0` notification routes to `agent_messages(target_role="main")` via
`ss.post_agent_message_by_role(...)` — **not** `slot_messages` (which only the task-worker `/boot`, `/heartbeat`,
`/progress`, `/messages` routes drain; main is a persistent `AgentRow`-tracked agent outside that lifecycle, so a
`slot_messages` row addressed to slot 0 was a permanent dead letter pre-fix).

## The ruling mechanism (D3): how an answer becomes a dispatchable task

An operator ruling never edits plan markdown directly and never mutates `state.db` in a way dispatch would see on its
own. Instead:

1. The endpoint stores `ruling_action` / `ruling_role` / `ruling_instruction` on the `BlockedRow` and forces
   `disposition="final"` (a structured ruling **is** the decision — "still pending" would be incoherent alongside it).
2. On its next tick, `regen_backlog_from_plan.py`'s `_materialize_operator_ruling_tasks()` queries every unconsumed
   ruling (`blocked_id LIKE 'BLK-op-%' AND ruling_action IS NOT NULL`, raw sqlite3, mirroring `_prune_stale`'s own
   direct-connection pattern) and appends a **real, dispatchable `BacklogTask`** to `backlog.tasks` — id
   `f"{orig_task_id}--ruling"`, `assigned_role` set from the reclassify dropdown or left for the general dispatcher to
   pick, carrying the original todo text plus the operator's instruction verbatim.

   This two-step (endpoint stores the ruling → regen materializes it) exists because `dispatch.py` only ever considers
   the in-memory, yaml-derived `backlog.tasks` — never the `tasks` DB table directly. A DB-only synthetic task would be
   invisible to dispatch **and** deleted within one regen tick by the orphan sweep (which GCs any DB task whose id isn't
   in the freshly-derived backlog). Regen materializing the task itself is what makes it real.

3. The ruling task's `done_definition` requires updating the plan doc **in the same commit** as doing the work — strip
   the `[OPERATOR]` tag, set `assigned_role`, flip the checkbox. This is load-bearing: `_is_live_ruling_task()` treats
   the ruling task as live for exactly as long as the _original_ task's `brief` is still an open plan todo, so both the
   original task and its `--ruling` sibling become ordinary orphans on the same regen tick once the plan edit lands, via
   the existing unmodified prune mechanism. If the plan edit is skipped, regen re-seeds the same `BLK-op-*` row next
   tick and the loop never terminates.

Two ruling shapes:

- **Reclassify** (`ruling_action="reclassify"`, `ruling_role=<role>`, no instruction) — hand the todo to a role as-is;
  the operator judged the `[OPERATOR]` tag was unnecessary and a normal worker can execute it.
- **Instruct** (`ruling_action="instruct"`, `ruling_instruction=<free text>`) — the general case. The instruction may be
  compound ("assign to infra, then do X and Y") — a worker reads prose, so no `if answer == "..."` parsing branch could
  ever have served this. **There is no content guard** (no delete/VM-launch refusal check) — the operator ruled against
  one 2026-07-30: most active plans are data-pipeline work that inherently deletes or moves data, so a guard would
  refuse nearly every real case. Reading the todo and writing sound instructions is the operator's responsibility, same
  as at plan-authoring time.

## Dashboard UI

`BlockedCard` (`dashboard/src/layout.tsx`) renders a `BLK-op-*` row with a **purple outline** + "operator-gated" badge
(`authority-operator-gated` CSS class), distinct from the amber `authority-operator` style still used for a live
worker's own escalation, and from the default style for an ordinary blocked question. It shows:

- The three canned options — A submits plain (stays open, per D2); B/C now submit as an `instruct` ruling (see path 2
  above), not plain answers.
- A **"Reclassify to role…" dropdown**, populated from `GET /api/roles` (the real role registry —
  `role_registry.load_registry()`, one row per `agents/<role>.md`) filtered client-side to exclude `project_management`
  and `review` (the two persistent supervisors, never valid ad-hoc dispatch targets — keyed by the role's declared
  `role:` frontmatter value, since `agents/main.md` declares `role: project_management`, not `"main"`). Every other
  role, including the generic `worker`, is a legitimate target.
- The existing free-text box, which for a `BLK-op-*` row submits as `ruling_action="instruct"` instead of a plain
  answer.

**`GET /api/roles` has exactly one implementation** — `agent-orchestrator/server/routes/roles.py`. A second,
thinner-shaped route was briefly added at the same path in `routes/backlog.py` during this feature's development and
silently shadowed the real one (first-registered-route-wins in `include_router()` order), crashing every authenticated
dashboard load (`RolesPanel` renders unconditionally and calls `r.skills.map(...)`, `undefined` on the shadow route's
thinner shape). It was deleted before shipping — if you're adding a new backend route, grep for the path first
(`rg -n '"/api/roles"' server/`).

## Regression coverage

- `agent-orchestrator/tests/test_operator_gated_dispatch_ruling.py` — endpoint-layer: message routing, disposition
  auto-upgrade, ruling validation (400 on non-`BLK-op-*`), forced-final disposition.
- `agent-orchestrator/tests/test_regen_backlog_from_plan.py` — regen-layer: materialization, idempotency across ticks,
  survival while the original todo is open, pruning once the plan edit lands, a stale ruling whose original task is
  already gone, `get_full_todo_text()`'s continuation-block read + fallback behavior.
- `agent-orchestrator/dashboard/tests/e2e/reclassify-blocked.spec.ts` — UI: purple styling, reclassify-to-role dispatch,
  free-text instruct, and a negative check that an ordinary blocked card is unaffected.

## Cross-references

- `/plans/archive/issues/operator_gated_blocked_answer_is_a_no_op_2026_07_30.md` — full root cause, live measurements,
  rejected alternatives, decision log.
- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` — dispatch / regen behavior this mechanism
  builds on.
- `/codex/04-architecture/agent-orchestrator-alerting.md` — the ✅-close-bookend convention
  `_alert_unanswered_ operator_gated_blocks` participates in.
- `/codex/06-coding-standards/ui-testing-layers.md` — the `[UI]` + `pw:L2` gate the dashboard change shipped under.
