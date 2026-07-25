---
doc_type: plan
title: AO plain-worker context lifecycle gap — gate dispatch, enforce compact, fix the blind anomaly clock
summary: >-
  context_lifecycle.py's tier-1/tier-2 proactive compact policy explicitly excludes ordinary plan-backlog workers (only
  main/review/large-plan-todo-count carve-out are covered) under the assumption "/boot-per-shippable-unit already bounds
  them." Confirmed FALSE by both code and live telemetry 2026-07-25: `/done`'s persistent-session design
  (server/routes/slots_worker.py, "reaping them per task was the exact defect this fixes") means the SAME session drains
  many tasks back-to-back with no context reset, `/done` already receives context_used_pct on every call but nothing
  gates on it, and the one worker-scoped anomaly detector (context_burn Trigger 4) keys off hours-on-TASK which resets
  every reassignment — live: 5 slots >=80% context, 0 context_burn_suspected fires in 7h. This plan closes the loop:
  gate /done + /progress on self-reported context, return a machine-directive telling the worker to compact before
  continuing (reusing the existing messages/next_task response-field convention, not new pane-injection machinery), fix
  the anomaly clock to survive task reassignment, and stop the kicker from blindly re-nudging a frozen+saturated session
  (observed live: slot 9, ~14 "proceed now" kicks over 30min at 100% context, ping_advanced=false on nearly all,
  eventually crashed/killed). Companion, independently-dispatchable plan ao_fleet_throughput_incident_2026_07_25.md
  covers the fleet-capacity-refill side of the same live incident.
status: active
nature: process
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer]
tags: [orchestrator, context-management, compaction, worker-lifecycle, observability]
related: [/plans/active/ao_fleet_throughput_incident_2026_07_25.md, /plans/epics/orchestrator_master.md]
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 4.2
estimate_calibrated_ai_days: 3.4
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source: >-
  Operator question 2026-07-25: "how is context getting to 100% when we are supposed to be running pre-compact at 70%...
  check all this," followed by "either workers are getting more than one task without resetting their context or tasks
  arent really short enough to assume no reset context needed mid task," then "action it in full... deployed to agent
  orchestrator /autonomous." Root-caused this session via code read (server/context_lifecycle.py,
  server/routes/slots_worker.py::done_slot, agents/worker.md, server/worker_liveness_watchdog.py) plus two rounds of
  read-only SSM telemetry against the live orchestrator VM (i-0c9b283b31d6b5ca7): first pull found slot 3 at 93% context
  0.00h into a freshly-assigned task with 117 lifetime compactions, last compaction 3.93h BEFORE the task was assigned;
  second pull ~13min later found the SAME slot still climbing (100%) after shipping 2 more tasks in between with no
  compaction (`slot_done` events literally carry `context_pct: 93/95` in their own payload, unconsumed by dispatch),
  while slot 9 (also 100%) showed 14 worker_kicked "frozen"/"proceed now" cycles over 30min before eventually crashing
  (`tmux_session_lost` -> `slot_resume_skipped`: "context 100% >= resume_fresh_context_pct 90%").
assigned_role: backend_engineer
drift_direction: advance-code
sequential: true
---

# AO plain-worker context lifecycle gap

> **Why `sequential: true`**: todos 1-2 (config + response-model schema) are load-bearing for todos 3-4 (the actual
> gates, which use that schema) and todo 5 (worker.md, which documents the exact field names todos 2-4 define); todo 7
> (anomaly-clock fix) consumes todo 6's new field; several todos also share `server/routes/slots_worker.py` and
> `server/config.py`. This is a real dependency chain, not a reflexive default — see task_template.md §4.
>
> **Codex SSOTs to check against / update on completion**:
> `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`,
> `/codex/05-infrastructure/vm-launcher-runbook.md` (VM/fleet monitoring section, if the new event types belong there).

## Todos

- [x] ✅ [BACKEND] P0. **Add worker-scoped context-gate config to `Tuning`** in `server/config.py` (agent-orchestrator),
      mirroring the existing `context_compact_guidance_pct`/`context_recycle_compactions` `Field(...)` pattern
      immediately above them: `context_worker_compact_gate_pct: int = Field(default=70, ge=1, le=100)` (matches the
      number already documented as the honor-system threshold in `unified-trading-pm/agents/worker.md`) and
      `context_worker_directive_repeat_gate: bool = Field(default=True)` (governs whether todo 4 re-issues a directive
      every tick or only once per un-compacted stretch). **Done when**:
      `get_config().tuning.context_worker_compact_gate_pct` resolves to 70 by default and is env-overridable in a new
      unit test; `quality-gates.sh` green. — **`agent-orchestrator@9c08c61`**. **Correction to this todo's own
      Done-when**: "env-overridable" is stale — `TuningDefaults` has been deliberately env-FREE since
      `ao_config_env_var_consolidation` (2026-07-18; see the class's own docstring: "aliases stripped... env-free...
      tune by editing the default here + redeploy, never via env"), and every sibling field in this same class
      (`context_compact_guidance_pct`, `context_recycle_compactions`, etc.) follows that contract, not env override.
      Implemented + tested against the ACTUAL established contract instead: default resolves to 70/`True`, a new test
      (`test_context_worker_compact_gate_pct_default_and_bounds`, mirrors the adjacent
      `test_loop_seconds_valid_and_bounds`) asserts the default, direct-injection via the existing `set_tuning` fixture,
      and `Field` bounds validation (`ValidationError` on 0 and 101). 1648/1648 tests pass, ruff + basedpyright clean,
      full `quality-gates.sh` PASSED.
- [x] ✅ [BACKEND] P0. **Add a typed `directive` field to `DoneResponse` and `ProgressResponse`** in
      `server/models/worker_api.py` — `directive: Literal["compact_before_next"] | None = None` on `DoneResponse`,
      `directive: Literal["compact_now"] | None = None` on `ProgressResponse`. Do NOT overload the existing free-text
      `message`/`messages` fields — worker.md's new HARD RULE (todo 5) needs an unambiguous machine-checkable field the
      agent can branch on, not prose it has to parse. **Done when**: both models validate with and without the field
      set; existing callers/tests unaffected (field defaults to `None`); a new test asserts the field serializes
      correctly; `quality-gates.sh` green. — **`agent-orchestrator@5e22fab`**. Both fields added exactly as specified
      (default `None`, `Literal` typed). 2 new model-level tests
      (`test_done_response_directive_field_validates_and_serializes`,
      `test_progress_response_directive_field_validates_and_serializes`) in
      `tests/test_task_lifecycle_done_gate_resume.py`, deliberately scoped to schema-only (default/set/
      `model_dump`/`model_validate` round-trip) so they don't duplicate todos 3-4's later route-behavior tests.
      1650/1650 tests pass, full `quality-gates.sh` PASSED.
- [x] ✅ [BACKEND] P0. **Gate `done_slot`** (`server/routes/slots_worker.py`) **on self-reported context.** Before the
      existing next-task-selection path runs, compare `req.context_used_pct` (already submitted on every `/done` call —
      confirmed live, e.g. `context_pct: 95` on `slot_done` activity entries, currently unconsumed) against
      `get_config().tuning.context_worker_compact_gate_pct`. At/above threshold: do NOT dispatch a next task to this
      slot — leave the candidate task `queued` untouched, return
      `DoneResponse(next_task=None,     directive="compact_before_next", ...)`. Below threshold: existing behavior
      unchanged. Log a new activity type `worker_compact_gated` (slot_id, context_pct, threshold) on every fire,
      mirroring how `proactive_compact_guidance` is already logged for main/review in `context_lifecycle.py`. **Done
      when**: a unit test asserts `done_slot` withholds `next_task` and sets the directive when
      `context_used_pct >= threshold`, dispatches normally below it, and the candidate task remains `queued` (not
      silently dropped); `quality-gates.sh` green. — `agent-orchestrator@55148c8`. Gate inserted immediately before
      `pick_next_task` inside the existing `session_scope()` block; logs `worker_compact_gated` with
      `{context_pct, threshold}`. Two new tests added to `tests/test_task_lifecycle_done_gate_resume.py`
      (`test_done_context_gate_withholds_next_task_above_threshold`,
      `test_done_context_gate_dispatches_normally_below_threshold`) using a real `Backlog(tasks=[BacklogTask(...)])`
      candidate task (not the `empty_backlog` fixture) to assert both the above-threshold withhold + queued-untouched
      path and the below-threshold normal-dispatch path. 1652/1652 tests pass, full `quality-gates.sh` PASSED.
- [x] ✅ [BACKEND] P0. **Gate `progress_slot`** (same file as todo 3, `server/routes/slots_worker.py` — kept as a
      separate sequential todo rather than merged, since the two handlers are independently testable even though they
      share the threshold/directive contract from todos 1-2). When
      `req.context_used_pct >=     context_worker_compact_gate_pct`, set `ProgressResponse.directive="compact_now"` —
      but do not re-issue on every single tick: reuse the existing compaction-drop detection already in
      `state_store/slots.py::update_slot_ping` (`COMPACTION_DROP_THRESHOLD`) to know a prior directive was actually
      complied with (pct dropped), and suppress re-issuing until either a drop is observed or
      `context_worker_directive_repeat_gate` says otherwise. **Done when**: a unit test simulates a `/progress` sequence
      crossing the threshold, receiving exactly one directive, then compacting (pct drop observed), then not receiving
      another until climbing back over threshold; `quality-gates.sh` green. — `agent-orchestrator@3ace754`. Added
      `SlotRow.context_directive_issued` (bool, tracks whether the current over-threshold stretch already fired) cleared
      on a detected compaction drop; `progress_slot` sets `directive="compact_now"` when over threshold AND
      (`context_worker_directive_repeat_gate` is True OR the flag is unset). Two new tests in
      `tests/test_task_lifecycle_done_gate_resume.py`:
      `test_progress_context_gate_dedupes_directive_until_compaction_drop` (repeat_gate=False — cross threshold → one
      directive → suppressed → compaction drop clears it → climbs back over → fires again) and
      `test_progress_context_gate_repeats_every_tick_when_repeat_gate_on` (default True — no suppression). 1654/1654
      tests pass, full `quality-gates.sh` PASSED.
- [ ] [INFRA] P0. **Update `unified-trading-pm/agents/worker.md`'s context-discipline section** (the PROGRESS step,
      currently ending in the prose-only ">~70% used, run /compact" line) with a HARD RULE: if a `/done` or `/progress`
      response's `directive` field (todo 2's exact field name) is `compact_before_next` or `compact_now`, the agent MUST
      run the `/pre-compact` skill then `/compact` before its next tool call — for the `/done` case, MUST NOT call
      `/boot` again until compaction is confirmed done. Keep the existing prose >~70% self-discipline line as the
      earlier VOLUNTARY trigger, unchanged — the new directive is the enforced backstop, not a replacement. **Done
      when**: worker.md's PROGRESS section and the boot-loop section both reference the exact `directive` field/values
      by name; any doc-lint/prek check on `unified-trading-pm` passes.
- [ ] [BACKEND] P1. **Expose worker session-start time via the API.** Add `last_spawned_at: datetime | None` to
      `SlotView` (`server/models/slots.py`) and populate it in the `/api/state` route mapping (`server/routes/state.py`)
      from the ORM `SlotRow.last_spawned_at` field, which already exists and is already read internally
      (`server/worker_liveness/__init__.py` reads `slot.last_spawned_at`) but was never serialized out — this is the
      exact field whose absence forced this session's live diagnosis to infer session-vs-task-age carryover indirectly
      from `compactions_total`/`last_compacted_at` instead of reading it directly. **Done when**: `GET /api/state`
      returns a non-null `last_spawned_at` for every slot with a live tmux session; a test asserts the field
      round-trips; `quality-gates.sh` green.
- [ ] [BACKEND] P1. **Fix the context-burn anomaly clock** in `server/worker_liveness_watchdog.py::_is_context_burning`
      (Trigger 4). Currently keyed on `hours_on_task` (derived from `assigned_at`, which resets on every reassignment —
      confirmed live 2026-07-25: 5 slots >=80% context produced zero `context_burn_suspected` fires over a 7h window
      because none had spent >=4h on their CURRENT task even though their sessions carried compaction histories hours
      older than the task). Replace/supplement that input with a session-scoped clock derived from `last_spawned_at`
      (todo 6) — "hours since this SESSION last compacted or was spawned," not "hours on this task." Keep the existing
      `context_pct >= min_pct OR compactions_total >= min_compactions` disjunct. **Done when**: a new unit test
      reproduces the exact live scenario from this session (task reassigned 0.08h ago, context 100%, last compaction >4h
      before assignment) and asserts `_is_context_burning` now returns `True` where the old task-clock version returned
      `False`; `quality-gates.sh` green.
- [ ] [BACKEND] P1. **Add WIP preservation to `_kill_slot`** (`server/worker_liveness_watchdog.py`) — a hard
      prerequisite for enabling `context_burn_kill` at all. Confirmed by direct code read this session: `_kill_slot`
      currently just calls `kill_session(tmux_session)` and flips `status="killed"` — zero preservation of uncommitted
      worktree changes, so any real WIP in flight at kill time is lost outright. Reuse the existing `stash_dirty_repos`
      (`server/worktree_clean_check/_stash.py`), already used on the controlled `/done` exit path
      (`server/routes/slots_worker.py:640`, logged as `slot_stash_on_done`, stash refs GCS-ledger-persisted per
      `server/notifications/slack.py`'s comment) — call it from `_kill_slot` before `kill_session` fires, for every kill
      reason, not just `context_burn`. **Done when**: a unit test asserts a dirty worktree's changes are stashed (and
      the stash ref logged) before the tmux session is killed, for a simulated `context_burn` kill; existing kill-path
      tests for the other reasons (`context_full`, `stuck_at_prompt`, etc.) still pass unmodified; `quality-gates.sh`
      green.
- [ ] [BACKEND] P1. **Sharpen the kill trigger to only fire after the graceful path has already failed** — operator
      design ruling 2026-07-25: kill should require context "so high it can't take instruction anymore," not just the
      existing 80%-suspicion threshold. Add `context_burn_kill_min_pct: int = Field(default=98, ge=1, le=100)` to
      `Tuning` (`server/config.py`), distinct from `context_burn_min_pct` (stays 80, still gates the unconditional
      `context_burn_suspected` flag/Slack alert — informational, unchanged). In `_is_context_burning`'s caller
      (`server/worker_liveness_watchdog.py`), gate the actual kill (not the suspicion flag) on BOTH:
      `context_pct >=     context_burn_kill_min_pct` AND a compact directive was already sent (todo 3/4's `directive`
      field) and NOT complied with within a grace window (no `context_used_pct` drop observed across the next 2
      consecutive `/progress`or `/done` reports after the directive) — i.e. kill is the last resort after the graceful
      compact-before-next/compact-now path has demonstrably failed, not a parallel independent trigger. **Confirmed
      already true, no change needed**: the Slack alert (`notify_context_burn`, called with `killed=_CONTEXT_BURN_KILL`)
      already fires unconditionally today regardless of whether kill is enabled — nothing to add there. **Done when**: a
      unit test asserts kill does NOT fire at 85% context with no prior directive (below the new kill threshold), does
      NOT fire at 99% if a directive was sent but the grace window hasn't elapsed yet, and DOES fire at 99% once a
      directive was sent and 2 consecutive reports show no pct drop; `quality-gates.sh` green.
- [ ] [BACKEND] P2. **APPROVED 2026-07-25 (operator, in-session, verbatim: "you can do this please now")** — flip
      `context_burn_kill` (`server/config.py`) default `False` → `True`. Prerequisite: the two todos immediately above
      this one (WIP-preservation via `stash_dirty_repos` in `_kill_slot`, and the sharpened
      near-100%-and-directive-already-failed trigger) must land first — this todo's own `sequential: true` plan ordering
      already enforces that; do not dispatch this ahead of them even though it's no longer `[OPERATOR]`-gated. Once
      those ship: change `context_burn_kill: BoolEnvFalse = Field(default=False)` to `default=True` in `Tuning`
      (`server/config.py`), update the existing test(s) asserting the old default, and note the flip in this todo's own
      evidence line citing the sha. **Done when**: `get_config().tuning.context_burn_kill` resolves `True` by default,
      the WIP-preservation + sharpened-trigger prerequisites are cited by sha, and `quality-gates.sh` is green.
- [ ] [BACKEND] P2. **Stop the WorkerLivenessKicker from blindly re-nudging a frozen+context-saturated slot.** In
      `WorkerLivenessKicker._tick_once` (`server/worker_liveness/__init__.py`): when `classify_pane(pane) == "frozen"`
      AND the slot's current `context_used_pct >= context_worker_compact_gate_pct` (todo 1's threshold), skip the
      ordinary `_kick_session(..., kind="frozen")` "proceed now" injection and instead log a new activity type
      `frozen_at_high_context` (slot_id, context_pct, consecutive prior kick count from `_consecutive_kick_failures`) —
      this is the exact live pathology observed 2026-07-25: slot 9 received ~14 `worker_kicked`/`worker_kick_failed`
      "proceed now" nudges over 30 minutes at 100% context (`ping_advanced: false` on nearly every one) before
      eventually crashing. **Done when**: a unit test asserts a frozen+saturated slot gets the new log event instead of
      a kick attempt, while an ordinary frozen-but-normal-context slot's kick behavior is unaffected; `quality-gates.sh`
      green.
- [ ] [BACKEND] P2. **Give the reactive crash-time context-loss path its own visible event type.** In `tmux_pruner.py` /
      `resume_lifecycle.py`, the existing `resume_fresh_context_pct` skip-resume check (observed live 2026-07-25 for
      slots 5, 8, and 9 — `slot_resume_skipped`: "context 100% >= resume_fresh_context_pct 90%") currently folds into
      the generic `tmux_session_lost` event. Log a distinct, clearly-labeled activity type (e.g.
      `context_saturated_session_lost_task_requeued`) when `resume_decision != "resume"` AND the dying slot's last-known
      `context_used_pct >= 90`, so this failure mode stays separately visible/countable on the dashboard even after
      todos 3-4-7 reduce how often sessions ever reach that point. **Done when**: the new event type fires exactly under
      that condition; existing `tmux_session_lost` logging is otherwise untouched; `quality-gates.sh` green.
- [ ] [BACKEND] P2. **Regression test reproducing this session's full live scenario end-to-end.** A worker slot
      completes a task at `context_used_pct=93` with `compactions_total` far predating `assigned_at` (mirrors slot 3's
      live snapshot 2026-07-25T04:23-04:36 UTC). Assert: `done_slot` (post todo 3) withholds `next_task` and sets the
      directive; once the worker reports a post-compact `/progress` (pct drop observed), the NEXT `/done` dispatches
      normally. **Done when**: new integration test in `agent-orchestrator/tests/` passes, exercising todos 1, 3, and 4
      together end-to-end; `quality-gates.sh` green.
- [ ] [REVIEW] P1. **Post-deploy live verification against this plan's own root-cause evidence.** Re-pull `/api/state` +
      `/api/activity` (read-only SSM, same pattern as this plan's `source` field) for slot IDs 2, 3, 5, 8, 9 (the ones
      tracked live during this session's diagnosis) and confirm: (a) no slot receives a next task while self-reporting
      `context_used_pct` at/above the gate threshold (todo 3), (b) a reproduced long-session/ short-task-age scenario
      now trips `context_burn_suspected` (todo 7), (c) the new `frozen_at_high_context` (todo 11) and
      `context_saturated_session_lost_task_requeued` (todo 12) event types appear when their trigger conditions are
      manually reproduced in a test env. **Done when**: a written verification note citing actual post-deploy event/log
      evidence for (a)-(c), attached to this plan's Progress Log.

## Progress Log

**2026-07-25 (autonomous session, ~05:00-05:20 UTC).** Fleet picked this plan up and is executing it — slot 2 completed
todos 1 (`agent-orchestrator@9c08c61`, "feat(config): add worker-scoped context-gate Tuning knobs") and 2
(`agent-orchestrator@5e22fab`, "feat(models): add typed compact directive field to DoneResponse/ProgressResponse", with
tests) via quickmerge, and is now dispatched on todo 3 (gate `done_slot`). **Deploy-currency CONFIRMED live**:
`ao-self-pull.sh` (cron, `*/15`, `AO_DIR=/home/ubuntu/unified-trading-system-repos/agent-orchestrator`) picked up the FF
from `9c08c61`→`5e22fab` and restarted the orchestrator service at `2026-07-25T05:15:01Z`
(`systemctl show orchestrator --property=ActiveEnterTimestamp` = `05:15:22 UTC`, ~21s later, consistent) — i.e. this
plan's shipped todos are ALREADY running in the live production orchestrator, not just merged to LDR. Combined with
`uvicorn --reload --reload-dir server` (hot-reloads on file change between cron ticks), this closes the "deployed to LDR
≠ deployed to AO" gap the operator flagged: no separate manual deploy step is needed for anything landing via quickmerge
to `live-defi-rollout` — verify future todos the same way (`tail /var/log/ao-self-pull.log` via SSM, looking for
`FF <old>-><new> — restarting orchestrator` citing the todo's commit).

Deliberately did NOT touch `server/config.py` / `server/models/worker_api.py` / `server/routes/slots_worker.py` myself
despite the operator's "even locally as a fallback" authorization — the fleet was already actively, successfully working
these exact files (slot 2 mid-task on todo 3 at time of writing); editing them concurrently would have been a same-file
collision, not a genuine fallback (the queue was NOT blocking completion — it was actively completing it). Reserved
local/manual intervention for genuinely non-colliding, independent work instead: see
`ao_fleet_throughput_incident_2026_07_25.md`'s Progress Log for the `check_doc_body_links` promote-escalation fix
(`unified-trading-pm@3e4c73436`), which is this exact "operator-authorized, not my plan's own scope, unblock the
pipeline" case.

**2026-07-25 ~05:35 UTC — pre-compact checkpoint (context ~81%, interactive session, operator still present but
compacting imminently).** Operator approved the `context_burn_kill` flip verbatim ("you can do this please now") —
captured above by de-gating that todo from `[OPERATOR]`/`BLOCKED-OPERATOR-DECISION` to a normal dispatchable `[BACKEND]`
todo (this plan's own `sequential: true` still correctly orders it behind the WIP-preservation + sharpened-trigger
prerequisites, so approval does not skip the safety ordering). This was the one genuinely at-risk item this session — a
verbal approval that existed only in chat until this edit.

## Deferred work after 2026-07-25

| Item                                                                                                                          | State              | Blocked on                                                                                         |
| ----------------------------------------------------------------------------------------------------------------------------- | ------------------ | -------------------------------------------------------------------------------------------------- |
| `context_burn_kill` flip (todo, now approved+dispatchable)                                                                    | Not done           | Nobody — real work, fleet will pick it up once the 2 prerequisite todos land                       |
| Todos 5-13 (worker.md, `/progress` gate, anomaly-clock fix, kicker fix, observability, regression test, final review)         | Not done           | Nobody — fleet actively working sequentially (slot 2), self-sustaining                             |
| Both gated finalize plans (`ao_worker_context_lifecycle_gap_finalize`, `ao_fleet_throughput_incident_finalize`)               | Cannot be done yet | `depends_on` + `gate_on_depends: true` — machine-held until their parent plan's todos are all done |
| `ao_fleet_throughput_incident` todo 4 (post-fix live review)                                                                  | Cannot be done yet | Sequential ordering behind todos 1-3 (all done as of this checkpoint)                              |
| `orchestrator_slots_context_directive_issued_missing_migration_2026_07_25.md` (fleet-filed issue doc, discovered mid-session) | Not done           | Nobody — not investigated this session, flagged here so it isn't missed; not yet read in full      |
| `branch_quarantine_alert_blind_to_backlog_queue_2026_07_25.md` (fleet-filed, P2)                                              | Not done           | Nobody — filed by slot 12, not yet picked up                                                       |

**Recommended next item**: nothing needs a human right now — the fleet is actively converging on the above in priority
order via normal AO dispatch, and every merge auto-deploys within ~15 min (confirmed live this session). The only
genuinely operator-shaped remaining decision was the `context_burn_kill` flip, now resolved above.

**Lessons this session (would otherwise be re-learned):**

- The AO fleet reliably self-corrects stale plan claims — todo 1 above initially said "env-overridable," which slot 2
  caught as contradicting the actual `TuningDefaults` contract (env-free by design since 2026-07-18) and fixed against
  the real contract instead of blindly implementing the stale spec. Trust the fleet to catch this class of drift rather
  than hand-verifying every todo's assumptions before dispatch.
- **Deploy is automatic and required no new mechanism**: `ao-self-pull.sh` (cron `*/15`) +
  `uvicorn --reload --reload-dir server` together mean anything merged to `live-defi-rollout` is live in production
  within ~15 minutes with zero manual step. Verify via `tail /var/log/ao-self-pull.log` on the orchestrator VM (SSM),
  not by assuming.
- **`git stash pop`/autostash conflicts on a shared, high-velocity branch**: `git checkout --theirs <file>` during an
  autostash-pop conflict did NOT reliably pick the incoming/upstream side (verified: it picked the wrong side once this
  session) — always verify post-resolution content with `git diff origin/<branch> -- <file>` before trusting which side
  you kept, never trust the flag name alone.
- This repo currently runs at extreme commit velocity (a fresh `git pull --rebase --autostash` was needed before nearly
  every commit this session, sometimes 3-4 times in a row) — this is normal operating condition today, not an error
  signal; budget for it rather than treating repeated branch-drift rejections as a problem to diagnose.
