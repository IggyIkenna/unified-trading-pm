---
doc_type: plan
title: AO backlog id-collision — surface it (Slack + dashboard) and offer a one-click safe remediation
summary:
  The sibling-reset-guard from backlog_regen_id_reuse_stale_status_2026_07_15 / ao_backlog_regen_integrity_2026_07_20
  already refuses to silently recycle a done row on a positional task_id collision — but it only logs an ERROR nobody
  watches. A new todo can land on a stale done+done_sha id and sit invisibly un-dispatched forever unless a human goes
  digging with SSM+SQL. Give this event a Slack page, a dashboard panel, and a one-click safe fix.
status: active
nature: process
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [orchestrator, backlog, regen, id-collision, alerting, dashboard-ui, data-integrity]
related:
  [
    /plans/archive/issues/backlog_regen_id_reuse_stale_status_2026_07_15.md,
    /plans/archive/2026_07/ao_backlog_regen_integrity_2026_07_20.md,
    /plans/active/issues/slot_stale_spawn_base_role_stuck_task_less_2026_07_25.md,
  ]
created: 2026-07-26
last_updated: 2026-07-26
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: brand-new
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.5
assigned_role: backend_engineer
drift_direction: advance-code
sequential: true
depends_on: []
source:
  Live-reproduced 2026-07-26 while editing slot_stale_spawn_base_role_stuck_task_less_2026_07_25.md's own OPERATOR todo
  — the edit's new content landed on a reused task_id (`-004`) that the sibling-reset-guard correctly refused to reset
  (it was a real, already-done, unrelated fix with done_sha=41840c1), so the new todo silently read as done and would
  never dispatch. The 2026-07-20 plan's own closing note flagged this exact residual as "worth watching for in practice"
  — this plan is that watch.
locked_by: live-defi-rollout
locked_since: 2026-05-21
supersedes:
superseded_by:
---

# AO backlog id-collision — surface it and offer a one-click safe fix

## Why this, why now

`server/bootstrap.py::sync_backlog_to_db`'s sibling-reset-guard (added `agent-orchestrator@9c7a0fd`) is a deliberate,
correct tradeoff: protect a `done`+`done_sha` row's audit history over auto-fixing a positional task_id collision. The
cost the 2026-07-20 plan explicitly accepted is that the NEW content landing on that id "will now silently look done and
never dispatch until manually fixed." That happened live this session — the only way to notice was an interactive agent
cross-referencing `/api/backlog`'s title against the DB's `done_sha`/`dispatched_to` and reading source. An operator
without an agent doing that same digging would never know the todo existed, let alone that it was stuck.

This plan does NOT reopen the deliberately-declined "content-derived task IDs" redesign
(`regen_positional_task_ids_not_content_stable_2026_07_17.md` todo 3, ruled out of scope 2026-07-20). It closes the
detection/remediation gap the ruling explicitly left open instead.

## Todos

- [x] ✅ [BACKEND] P1. **Turn the sibling-reset-guard's existing `logger.error(...)` (server/bootstrap.py,
      `sync_backlog_to_db`) into a queryable record.** When the guard refuses to reset a done+done_sha row on brief_hash
      mismatch, also record the event via this codebase's existing activity-log mechanism (the same one `/api/activity`
      reads) with an event type distinguishing it from ordinary activity — capture task_id, the colliding incoming
      brief, the existing row's done_sha, and a timestamp. Definition of done: extend
      `test_sync_refuses_to_reset_a_done_row_on_id_reuse` (or add a sibling test) asserting the activity record is
      created with those fields when the guard fires, and that NO record is created on the ordinary (non-done,
      resettable) reuse path; `bash scripts/quality-gates.sh` green. — agent-orchestrator@b623c2a
      (`log_activity(...,     "backlog_sibling_reset_guard_refused", ...)` in the guard branch; QG green, 1739 passed).
- [x] ✅ [BACKEND] P1. **Page the AO alerting Slack channel on this event, deduped.** Per
      `/codex/04-architecture/agent-orchestrator-alerting.md` (actionable-only channel; failures page) — this is a
      silent-dispatch-loss failure, which the SSOT's own contract says should page. Dedup by (task_id, incoming
      brief_hash) so a repeat regen tick on the SAME still-unresolved collision doesn't re-page every cycle; a DIFFERENT
      incoming brief_hash colliding with the same task_id later (a second, distinct collision) pages again. Definition
      of done: a unit test fires the same collision twice and asserts exactly one Slack call; a third call with a
      different incoming brief on the same task_id asserts a second Slack call. — agent-orchestrator@948f395
      (`notify_backlog_sibling_reset_guard_refused()` in `server/notifications/slack.py`, called from the guard branch
      in `sync_backlog_to_db` deduped via a seen-keys set at `dedup_state.backlog_sibling_reset_guard_alerted_path()`
      keyed by `f"{task_id}:{incoming_brief_hash}"`; QG green, 1752 passed).
- [x] ✅ [BACKEND] P2. **`POST /api/backlog/{task_id}/remint-collision` — safe one-click remediation endpoint.** Given a
      task_id currently flagged (via todo 1's record) as an unresolved sibling-reset-guard collision: atomically mint a
      genuinely fresh task_id, checking uniqueness against BOTH `backlog.yaml`'s current ids AND the full historical
      `state.db` task_id space (the actual gap `_make_task_id`/`next_index` has today — it only checks yaml's current
      ids, which is why the collision happens at all); move the incoming brief/title/tier/priority/operator_gated to the
      new id with a clean `queued`/`blocked` status; leave the ORIGINAL task_id's row (status/dispatched_to/
      done_sha/done_at) completely untouched. 404 if the named task_id is not currently flagged as an unresolved
      collision — never a generic "reset any task" backdoor. Definition of done: a unit test reproduces this session's
      exact `slot_stale_spawn_base_role_stuck_task_less-004` scenario (a done+done_sha row, a colliding new brief),
      calls the endpoint, and asserts (a) a new task_id exists with the incoming content in a clean queued/blocked
      state, (b) the original task_id's terminal fields are byte-for-byte unchanged, (c) a 404 on a task_id with no
      flagged collision. — **DONE (slot-3, 2026-07-26): `agent-orchestrator@ffd0ab0`.** Reads the incoming
      brief/title/tier/priority/operator_gated straight off `backlog.yaml`'s CURRENT entry at `task_id` (regen always
      writes the new checkbox's content there positionally, even though `sync_backlog_to_db`'s guard refuses to reset
      the DB row) — cross-checked against todo 1's activity record's `new_brief_hash` to confirm the collision is still
      live (not already resolved/superseded) before acting. Mints via the SAME `_make_task_id` SSOT regen uses, checked
      against yaml ids ∪ the full historical `tasks` table. Renames the yaml entry in place (old id removed, new id
      added, content byte-identical) so future regen ticks stop re-deriving that position onto the collided id; never
      touches the original TaskRow. 5 unit tests incl. the exact `slot_stale_spawn_base_role_stuck_task_     less-004`
      scenario + a historical-DB-gap regression (a yaml-pruned-but-still-in-DB id at the next positional slot must not
      be re-collided with by the remint itself); `quality-gates.sh` green (1746 passed).
- [x] ✅ [UI] P2. **DONE (2026-07-26, slot-4, `ui_developer`).** Dashboard "Backlog Integrity" panel, pinned above the
      fold. Lists every currently-unresolved collision from todo 1's activity records (task_id, incoming brief, old
      done_sha, first-detected timestamp), each row with a "Fix" button calling todo 3's endpoint; the row disappears
      from the panel on a successful response. `agent-orchestrator@914a825`: `unresolvedBacklogCollisions()`
      (dashboard/src/layout.tsx) — a pure reducer over an `/api/activity` page that dedups by task_id (keeping the
      latest of `backlog_sibling_reset_guard_refused`/`_collision_reminted`, surfacing only rows still `_refused`);
      `BacklogIntegrityPanel` pinned above `BlockedPanel` in the rail (both desktop layout branches) and in
      `MobileTriage`'s alerts tab; `App.tsx` runs a dedicated `/api/activity` pull for both collision event types
      (independent of the category-filtered feed, which can page these events out of view) and an `onFixCollision`
      handler that treats a 404 (already resolved) the same as success. Definition of done: a Playwright `pw:L2` spec
      drives todo 3's exact fixture scenario through the live UI — panel shows the row, click Fix, row disappears, a
      follow-up API call confirms the new task_id exists clean and the original is unchanged. **Built a new isolated e2e
      backend+fixture pair** (`dashboard/tests/e2e/backlog-collision.spec.ts`, port 8792/5200, mirroring the
      `parked-tasks` pattern) whose seed script (`seed_e2e_collision_state.py`) reproduces
      `test_backlog_remint_collision.py`'s exact `_seed_collision` scenario as a DB fixture — both specs pass:
      `2 passed (44.2s)`, verified in complete isolation and re-verified after landing (not just once, per the
      unattended-worker no-optimistic-claim discipline). The follow-up API check authenticates with the page's own
      stored JWT (backend calls go straight to the isolated backend URL, not through a Vite proxy) and asserts a second
      remint call 404s (already resolved). Found the remint endpoint rewrites `backlog.yaml` in place — the launcher now
      copies the fixture into a gitignored `.tmp-collision/` dir rather than pointing at the checked-in file directly,
      so the tracked fixture never drifts across runs (caught + fixed after the first run silently renamed
      `E2E-COLLISION-004` to `-005` in the tracked file). 6 new pure-function unit tests (`backlogCollisions.test.ts`);
      full repo `quality-gates.sh` green (1746 backend + 137 dashboard tests). **Found + filed, not fixed (out of this
      todo's UI-only scope)**: 2 pre-existing, reproducible `backlog-detail.spec.ts` failures (Queue-lag column blank +
      timestamp-sort order wrong for the `E2E-DISPATCHED` fixture row), confirmed unrelated to this change via a
      stash-and-rerun on the clean tree — `issues/ao_dashboard_backlog_detail_queue_lag_e2e_flaky_2026_07_26.md`.

## Codex SSOTs

- `/codex/04-architecture/agent-orchestrator-alerting.md` — actionable-only Slack channel contract, dedup-by-state-
  transition convention this plan's todo 2 must follow.
- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` — regen/backlog derivation model, the
  positional task_id mechanism this plan surfaces (not redesigns) the failure mode of.
