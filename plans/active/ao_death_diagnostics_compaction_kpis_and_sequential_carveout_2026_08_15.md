---
doc_type: plan
title: AO Death Diagnostics Consolidation, Compaction KPIs, and Sequential-Task Carve-out
summary:
  Operator-driven follow-up from a 2026-08-14 tmux_session_lost cluster investigation (see
  ao_tmux_session_loss_mid_task_root_cause_2026_08_10.md's Progress Log) — consolidate death diagnostics into one event,
  distinguish benign session recycles from genuine losses, surface compaction/wedge KPIs on the live dashboard with
  plan-worker/escalation/scheduled visibility, and design (but not yet ship) a scoped carve-out to the 2026-08-04
  one_task_per_session ruling for sequential-plan continuations.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [ao, observability, context-lifecycle, dashboard, tmux-pruner]
related:
  [
    /plans/active/issues/ao_tmux_session_loss_mid_task_root_cause_2026_08_10.md,
    /codex/15-runbooks/tmux-death-diagnostics.md,
    /codex/04-architecture/agent-orchestrator-worker-liveness.md,
  ]
created: "2026-08-15"
last_updated: "2026-08-15"
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
effort: high
locked_by:
locked_since:
context_scope:
  [
    /plans/active/issues/ao_tmux_session_loss_mid_task_root_cause_2026_08_10.md,
    /codex/15-runbooks/tmux-death-diagnostics.md,
    /codex/04-architecture/agent-orchestrator-worker-liveness.md,
    agent-orchestrator/server/tmux_pruner.py,
    agent-orchestrator/server/context_lifecycle.py,
    agent-orchestrator/server/fleet_kpis.py,
  ]
supersedes:
superseded_by:
depends_on:
source:
assigned_role: infra
drift_direction: advance-code
---

# AO Death Diagnostics Consolidation, Compaction KPIs, and Sequential-Task Carve-out

## Why this doc exists

An interactive session investigated a 2026-08-14 23:33:47-48Z 5-slot `tmux_session_lost` cluster (full findings in
`/plans/active/issues/ao_tmux_session_loss_mid_task_root_cause_2026_08_10.md`'s Progress Log). The operator then asked
four follow-up questions and confirmed all four as work to do, plus explicitly asked for the KPI-dashboard piece to be a
**human plan** (this doc) rather than auto-dispatched. This is a LOCAL/human plan (`assigned_vm: NA`) — the operator is
driving it interactively, not the AO fleet.

## Operator's four asks (verbatim intent)

1. **Consolidation**: "was the task done" data was scattered across a separate pruner journal line and a second
   task-scoped `tmux_session_lost` row — consolidate it into the SAME event.
2. **Disambiguation**: `burst_size` conflated an ordinary `one_task_per_session` recycle-teardown with a genuine
   mid-task loss when several of each landed in the same pruner tick — distinguish them.
3. **KPI visibility**: no live-dashboard view of compaction/wedge rates (current vs. prior-24h baseline, by
   slot/role/day) — only a one-shot CLI readout existed. Also: plan-worker vs. escalation vs. scheduled craft
   compaction/wedge behavior was invisible — all three shared the generic `role=="worker"` label.
4. **Sequential-task carve-out**: sequential-plan tasks should NOT be torn down between steps the way
   `one_task_per_session_enabled` (default `True`, 2026-08-04 ruling) currently forces — instead run pre-compact→compact
   and continue in the same session when the next step is ready.

## What shipped this session (items 1-3)

- [x] 1. ✅ [INFRA] P1. Consolidate `current_task`/`task_runtime_seconds` into the `tmux_session_lost` event's own
      `details_json` (snapshotted BEFORE the requeue/resume mutation clears them), closing the "scattered across 3
      places" gap. `agent-orchestrator/server/tmux_pruner.py`'s slot-death loop. Done-when: a fresh `tmux_session_lost`
      row for a mid-task death shows non-null `current_task` + `task_runtime_seconds` without needing to cross-reference
      the journal or a second event row. — `agent-orchestrator@c46102b9b5`, `quality-gates.sh` green (3852 passed).
- [x] 2. ✅ [INFRA] P1. Add a `death_class` field (`"intentional_teardown"` vs `"unexplained"`) to the same event,
      computed by cross-referencing a curated set of already-logged, distinctly-named "intentional teardown"
      activity_log events (`worker_one_task_per_session_reset`, `context_wedge_recovered`, `watchdog_slot_killed`) for
      the same `slot_id` within a 90s lookback — this is the fix for
      `ao_tmux_session_loss_mid_task_root_cause_2026_08_10.md`'s `[INFRA] P3` todo (burst_size conflation). `burst_size`
      itself is left unchanged (still "how many OTHER slots died this tick") — `death_class` is the per-row
      disambiguator a consumer filters on. **NOT exhaustive**: only covers kill_session call sites confirmed to log
      their own distinctly-named event; a plain `reason="manual"` reclaim with only a `logger.warning` line (no DB row)
      still reads as `"unexplained"`. `check-ao-recent-deaths.sh` updated to print it. Done-when: the 2026-08-14 23:33
      cluster, if re-queried, shows `death_class="intentional_teardown"` for slots 12/18/20 and `"unexplained"` for
      slots 10/11 (matches the hand-derived Progress Log analysis). — `agent-orchestrator@c46102b9b5`.
- [x] 3. ✅ [INFRA] P1. Tag every compaction-lifecycle event (`forced_precompact`, `forced_compact`,
      `forced_compact_ineffective`, `context_wedge_recovered`) with `craft_type` — `"plan_worker"` | `"main"` |
      `"review"` | an `agent_kind`/`lifecycle` value (`"cicd"`, `"one_shot"`, `"scheduled"`, etc.) — computed once per
      tick in `context_lifecycle.py`'s `_active_worker_slot_ids` via an `AgentRow.tmux_session` join (AgentRow has no
      direct `slot_id` FK). Purely additive — does NOT change which slots are swept into the unconditional worker
      force-compact path, only what gets logged. `_TargetState.craft_type` carries it through to every log site without
      touching any control-flow branch. Done-when: `/api/fleet-kpis`'s `compaction_by_craft_type` shows more than one
      bucket once escalation/scheduled crafts have run compaction events post-deploy. — `agent-orchestrator@c46102b9b5`.
- [x] 4. ✅ [INFRA] P1. Extend `/api/fleet-kpis` (`agent-orchestrator/server/fleet_kpis.py` + `server/routes/state.py`)
      with `compaction` / `compaction_baseline` (current-vs-prior-24h, mirroring the existing dispatch-efficiency shape
      exactly) and `compaction_by_craft_type` (the craft-type breakdown from the todo above). Scoped to current-window +
      baseline + craft-type breakdown for this pass — by-slot/by-day compaction breakdowns are NOT included (see the P3
      follow-up below) to keep the change bounded. — `agent-orchestrator@c46102b9b5`.
- [x] 5. ✅ [UI] P1. Render the new compaction KPIs on `FleetKpis.tsx` — two new tile panels (current window + baseline,
      same `TileBox`/`Panel` pattern as the existing efficiency tiles) and a "Compaction by craft type" breakdown panel.
      New pure mappers `compactionTiles`/`sortedByCraftType` vitest-covered in `FleetKpis.test.ts` (4 + 1 new tests),
      matching the existing `kpiTiles`/`sortedByRole` test pattern. — `agent-orchestrator@c46102b9b5`,
      `dashboard vitest` 360/360 passed, `tsc --noEmit` clean.

_(Also fixed in the same commit:
`tests/test_context_lifecycle.py::test_active_worker_slot_ids_excludes_review_and_non_working` updated for
`_active_worker_slot_ids`'s widened return contract, `list[int]` → `dict[int, str]` — a real, expected test-contract
update caught by the Pass-1 QG run, not a regression.)_

## Not shipped this session — item 4's carve-out (design only)

- [ ] [INFRA] P0. **Design phase only — implementation intentionally deferred, see rationale below.** Add a scoped
      carve-out so a `sequential: true` plan's next-ready task does NOT get torn down by `one_task_per_session_enabled`
      (default `True`) — instead the SAME session runs pre-compact→compact (if `context_used_pct` warrants it, same
      threshold `context_worker_force_compact_pct` the unconditional worker force path already uses) and continues
      draining the next task, mirroring the PRE-2026-08-04 "case 1 — next task ready: hand it over, same live session
      drains it" path documented in `/codex/04-architecture/agent-orchestrator-worker-liveness.md`'s
      dispatch-context-driven-lifecycle table — which still exists in code, just gated off by the current default. -
      **Scope, precisely**: the carve-out applies ONLY when (a) the finishing task belongs to a plan with
      `sequential: true`, AND (b) `pick_next_task` returns the immediate next task in that SAME sequential chain for
      this slot. Every other `/done` — a non-sequential plan, or a sequential plan's LAST task — keeps the current
      one-task-per-session teardown unchanged. - **Explicit conflict with the 2026-08-04/08-05 operator ruling**
      (documented in the worker-liveness SSOT): that ruling deliberately forces a fresh session on every task boundary
      fleet-wide, reasoning "conversational carry-over was never load-bearing... costs nothing but respawn overhead."
      This carve-out does not overturn that reasoning fleet-wide — it targets specifically the case the ruling's own
      rationale doesn't cover well: a `sequential: true` chain is, by construction, a single logical unit of work an
      operator explicitly asked to serialize; forcing N fresh boots + N re-reads of the plan/Progress Log between its
      own steps is pure respawn overhead with no isolation benefit (the SAME slot claims the SAME plan's next step
      regardless). - **Why this wasn't implemented in the same pass as items 1-3 above**: it changes control flow in the
      SAME `tuning.one_task_per_session_enabled` gate that a documented incident (four plan-worker roles wrongly reaped
      after every task, 2026-07-21) already had a real regression in — see
      `/codex/04-architecture/agent-orchestrator-worker-liveness.md` § "The defect this corrects". A live orchestrator
      managing dozens of dispatched slots right now (verified this session via `/check-agent-orchestrator`) is the wrong
      place to land an unreviewed change to that exact lifecycle decision in the same pass as three lower-risk,
      purely-additive observability changes. Landing it separately, with its own quality-gate run and its own regression
      test, keeps a bug in THIS change from being masked by or blamed on the observability changes that shipped
      alongside it. - **Implementation sketch for whoever picks this up** (this session, next tick, or the operator
      interactively): 1. In the `/done` handler's case-1 lookup (`pick_next_task` returning a task for this slot), check
      whether the just-completed task's `plan_order`-adjacent successor is (a) in the same plan, (b) that plan has
      `sequential: true`. If so, skip the `one_task_per_session` teardown for this ONE transition. 2. Before handing the
      next task to the same live session, check `context_used_pct` against `context_worker_force_compact_pct` (currently
      60, same threshold `context_lifecycle.py`'s worker path uses) — if over, run the SAME two-phase
      pre-compact→compact `_force_compact_now` sequence synchronously-enough that the next task's brief isn't handed to
      a session mid-compaction. 3. New regression test: a 3-task `sequential: true` plan drains in ONE session (no
      `slot_boot` between tasks 1→2 and 2→3), while a control (non-sequential) 3-task plan still shows 3 separate
      `slot_boot`s — proves the carve-out is scoped, not a blanket revert. 4. Verify against the 2026-07-21 regression
      this codebase already fixed once: confirm a `sequential: true` chain's worker does NOT go idle/get reaped
      mid-chain (case 2 in the lifecycle table) — only case 1 (next-task-ready) changes. - Done-when: the regression
      test in step 3 above is green, `quality-gates.sh` is green, and a real `sequential:       true` plan observed live
      shows N tasks completing in fewer than N `slot_boot` events for that slot.

## Follow-ups not in scope for this doc (filed for later, not silently dropped)

- [ ] [INFRA] P3. Extend the compaction KPI breakdown to by-slot and by-day, same pattern as the existing dispatch
      efficiency breakdown in `fleet_kpis.py` — deliberately excluded from the P1 todos above to keep that change
      bounded; the exact same helper-function shape (`_fetch_compaction_rows` already exists) makes this a small
      follow-up once the P1 pass has been live long enough to be worth trend-viewing.
- [ ] [INFRA] P3. Extend the `death_class` intentional-teardown signal set beyond the 3 events currently checked
      (`worker_one_task_per_session_reset`, `context_wedge_recovered`, `watchdog_slot_killed`) to cover more
      `kill_session` call sites (`account_rotation_*`, `blocked_slot_timeout_release`, `usage_cap_resume`,
      `tier_realign`, `heartbeat_silent_resume`) — each of these already logs its OWN distinctly-named event near its
      kill_session call site; auditing which ones do and adding them to the tuple is mechanical, just not done in this
      pass to keep the initial change reviewable.

## Progress Log

- **2026-08-15 (interactive session)**: doc authored; items 1-3's five todos implemented + shipped
  (`agent-orchestrator@c46102b9b5` — `server/tmux_pruner.py`, `server/context_lifecycle.py`, `server/fleet_kpis.py`,
  `server/routes/state.py`, `dashboard/src/{FleetKpis.tsx,FleetKpis.test.ts,types.ts}`,
  `scripts/orchestrator/check-ao-recent-deaths.sh`, `tests/test_context_lifecycle.py`). Pass-1 `quality-gates.sh` caught
  one real, expected test-contract update (see above) and one `ruff format` violation in `fleet_kpis.py` (fixed with a
  scoped `ruff format` on that one file, not a tree-wide reformat) before going green (3852 passed, 6 skipped; dashboard
  360/360 passed; `tsc --noEmit` clean). Shipped via `quickmerge --agent`, landed on `live-defi-rollout`. Item 4
  deliberately left as a design-only todo per the rationale above — not implemented this session.
