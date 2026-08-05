---
doc_type: plan
title: AO dashboard — cache-token split on live badges + tasks-completed-per-slot counter
summary:
  Two small, related agent-orchestrator dashboard gaps found while answering an operator question about the Fleet
  table's token badge. (1) The live per-task and per-session token badges (Fleet table + Agents panel) show blended
  input+output only — the cache_creation/cache_read fields are already parsed upstream and then discarded before
  reaching SlotRow, even though the done-task drill-down and the fleet-wide window panel both already show the real
  4-way split. (2) A tmux session is reused across many sequential tasks over a slot's lifetime, but there is no counter
  anywhere showing how many tasks a given slot's session has completed — SlotHistoryRow already has one row per slot per
  completed task, nothing aggregates it into a count.
status: complete
nature: record
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, dashboard, token-usage, cache-tokens, fleet, ui]
related:
  [
    /codex/04-architecture/agent-orchestrator-overview.md,
    /codex/06-coding-standards/ui-testing-layers.md,
    /plans/active/deepseek_claude_blended_provider_routing_2026_07_28.md,
    /plans/archive/2026_08/task_usage_schema_drift_done_outage_2026_08_05.md,
  ]
created: "2026-08-05"
last_updated: 2026-08-05
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.8
assigned_role: infra
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
source: operator-question-2026-08-05
context_scope:
  [
    agent-orchestrator/server/deepseek_usage.py,
    agent-orchestrator/server/deepseek_usage_poller.py,
    agent-orchestrator/server/state_store/slots.py,
    agent-orchestrator/server/orm.py,
    agent-orchestrator/server/models/slots.py,
    agent-orchestrator/dashboard/src/components.tsx,
    agent-orchestrator/dashboard/src/layout.tsx,
    agent-orchestrator/dashboard/src/types.ts,
    /codex/06-coding-standards/ui-testing-layers.md,
  ]
---

# AO dashboard — cache-token split on live badges + tasks-completed-per-slot counter

> **🟢 ARCHIVED 2026-08-05.** All 7 todos shipped in one commit, `agent-orchestrator@956e675` (landed on
> `live-defi-rollout`, full `quality-gates.sh` green: 2423 pytest + ruff + basedpyright + tsc + vitest, plus 2 new
> Playwright specs pw:L2 ✓): the live Fleet-table and Agents-panel token badges now show a real cache-read segment
> (previously blended input+output only, even though the done-task drill-down and windowed panel already had the full
> split); a `tasks_completed` counter next to the tmux badge distinguishes a freshly-spun-up slot from one that's run
> many sequential tasks; and — the one deferred item this plan's own todo 1 created —
> `/plans/archive/2026_08/task_usage_schema_drift_done_outage_2026_08_05.md`'s open P2 systemic-gap todo is now resolved
> and cited, not left dangling. Codex-alignment: `/codex/04-architecture/agent-orchestrator-overview.md` § "Schema
> changes to an EXISTING table" is a NEW subsection documenting the `_add_missing_columns()` dict + completeness-test
> convention this plan's investigation surfaced (the mechanism already existed, hand-maintained; this plan added the
> missing `task_usage` entry + the static test that catches a future forgotten entry before it ships). No other
> follow-ons were deferred. Moved to `/plans/archive/2026_08/ao_fleet_cache_tokens_and_task_count_2026_08_05.md`; corpus
> referrers updated in the same commit.

## Background

Answering "what does ↓781.6K ↑177.4K + the tmux label mean, and is that per-task or per-tmux-session" surfaced two real
gaps, confirmed by direct code read (2026-08-05):

- `TokenUsageBadge` (`dashboard/src/components.tsx`) renders `↓input ↑output` for the CURRENT task
  (`current_task_input_tokens`/`current_task_output_tokens`, Fleet table) and separately for the whole session
  (`session_input_tokens`/`session_output_tokens`, Agents-panel row shared across the `main`/review/custom/
  plan_reconciler role tabs) — both blended, no cache split.
- The tmux session (`orch-slot-{slot_id}`) is a fixed per-SLOT name, reused across every sequential task dispatched to
  that slot until a full worker reset/respawn (`tmux_spawn.py::session_name`, `reset_slot_worker_state`) — dispatch
  never creates/renames it. So the Fleet row currently gives no way to tell a slot that just spun up from one that's
  already run dozens of tasks.
- `scan_session_usage()` (`server/deepseek_usage.py`) already parses `cache_creation_input_tokens`/
  `cache_read_input_tokens` from the transcript's `message.usage` block (the exact shape `TaskUsageRow`'s per-task
  drill-down already uses — confirmed correctly shipped 2026-08-05 in `b2beadf`/the `/api/backlog/{task_id}/usage`
  route). `_sweep_slot_tokens()` (`server/deepseek_usage_poller.py`) calls the same scan but only sums `input_tokens`/
  `output_tokens` into `SlotRow.current_task_*`/`session_*` — the cache fields it already has in hand are computed then
  discarded before that write.
- `SlotHistoryRow` (`server/orm.py`, PK `slot_id + task_id + completed_at`) already gets one row per slot per completed
  task via `record_slot_history()` — nothing currently runs a `COUNT(*) GROUP BY slot_id` over it.

Operator confirmed (2026-08-05): this is a LOCAL/human plan (`assigned_vm: NA`), not AO-dispatched.

**Same-day precedent that reshaped this plan's order**: `task_usage_schema_drift_done_outage_2026_08_05.md` documents a
real ~2h fleet-wide `/done` outage today caused by adding a column to an already-live ORM table —
`create_all_tables()`/`Base.metadata.create_all()` only creates MISSING tables, never alters an existing one, so the
live orchestrator VM's `slots` table would silently keep its old shape after a code deploy until someone manually ran
`ALTER TABLE`. That issue's own systemic-fix P2 todo (framed as "no migration mechanism exists") turned out to be
narrower on inspection: `server/bootstrap.py::_add_missing_columns()` + per-table dicts (`_SLOTS_MIGRATION_COLUMNS`
etc., called from `create_all_tables()`) already implement exactly this pattern for `slots`/`agents`/`account_usage` —
nobody ever added a `task_usage` entry when `backfilled` shipped, which is the actual gap. Operator decided
(2026-08-05): reuse this existing mechanism (safer/faster than a new generic ORM-diffing migrator) — add the new
`SlotRow` cache columns to the existing dict, add the missing `task_usage` entry retroactively, and add regression tests
asserting both actually apply to an older-shape table, as the middle ground between "no test coverage" and "a whole new
migration system."

## Todos

- [x] 1. ✅ [INFRA] P1. Add a `task_usage` entry to `_add_missing_columns()` in `server/bootstrap.py`
      (`_add_missing_columns("task_usage", {"backfilled": "BOOLEAN NOT NULL DEFAULT 0"})`, matching
      `TaskUsageRow.backfilled`'s existing `server_default="0"`) — this is the retroactive code-level fix for
      `task_usage_schema_drift_done_outage_2026_08_05.md`'s still-open P2 (today's live fix was a manual `ALTER TABLE`
      via SSM, never checked into code, so any OTHER environment where `task_usage` predates `backfilled` still has the
      live bug today). Add a regression test that creates a `task_usage` table without `backfilled`, runs the migration
      step, and asserts the column is added with the correct default and existing rows survive untouched. Cite this
      commit on `task_usage_schema_drift_done_outage_2026_08_05.md`'s P2 todo once shipped. Done-when: the new test
      passes. — `agent-orchestrator@956e675` (`_TASK_USAGE_MIGRATION_COLUMNS` constant, defined as a named constant
      rather than an inline literal so `tests/test_migration_completeness.py` can statically import it —
      `test_every_task_usage_row_column_is_baseline_or_migrated` +
      `test_regression_task_usage_backfilled_column_is_migrated` both pass, full suite 2423 passed).
- [x] 2. ✅ [BACKEND] P2. Stop discarding cache fields in `_sweep_slot_tokens` (`server/deepseek_usage_poller.py`) — sum
      `cache_creation_input_tokens`/`cache_read_input_tokens` from `scan_session_usage()`'s per-usage results the same
      way `input_tokens`/`output_tokens` already are, for both the current-task window and the session window. Add
      matching columns to `SlotRow` (`server/orm.py`, mirroring `TaskUsageRow`'s existing 4-field naming:
      `session_cache_creation_input_tokens`, `session_cache_read_input_tokens`,
      `current_task_cache_creation_input_tokens`, `current_task_cache_read_input_tokens`, all nullable `Integer` like
      their sibling `session_input_tokens`/`current_task_input_tokens`) AND add the same 4 columns to
      `_SLOTS_MIGRATION_COLUMNS` in `server/bootstrap.py` so an already-live `slots` table picks them up on next restart
      — a column added to the ORM model with no matching dict entry is the exact class of bug that caused today's
      outage. Write them in the same call that currently sets `current_task_input_tokens`/`session_input_tokens`
      (`server/state_store/slots.py`). Add a regression test mirroring the `task_usage` one above (older-shape `slots`
      table missing the 4 new columns → migration adds them correctly). Done-when: both tests pass and a slot mid-task
      with real cache hits shows non-zero `current_task_cache_read_input_tokens` in the DB row. —
      `agent-orchestrator@956e675` (`test_every_slot_row_column_is_baseline_or_migrated` +
      `test_regression_slots_cache_token_columns_are_migrated` + `test_sweep_slot_tokens_splits_cache_and_task_windows`,
      all passing).
- [x] 3. ✅ [BACKEND] P2. Expose the new `SlotRow` cache columns on `SlotView` (`server/models/slots.py`) and add a
      `tasks_completed: int` field computed via a new `slot_task_count(session, slot_id) -> int` helper
      (`server/state_store/slots.py`, near `record_slot_history`) that runs `COUNT(*) GROUP BY slot_id` over
      `SlotHistoryRow`. Done-when: `GET` the fleet endpoint for a slot with known completed-task history and see the
      count match `SELECT COUNT(*) FROM slot_history WHERE slot_id=…`. — `agent-orchestrator@956e675` (also wired the
      matching `AgentView.session_cache_creation_input_tokens`/`session_cache_read_input_tokens` lookup in
      `server/routes/agents.py`'s `_agent_slot_token_usage`, not just the Fleet-table `SlotView` path —
      `tests/test_slot_task_count.py`, 3 tests, all passing).
- [x] 4. ✅ [UI] P2. Mirror the new fields onto the dashboard `SlotView` type (`dashboard/src/types.ts`) and extend
      `TokenUsageBadge` (`dashboard/src/components.tsx`) to render the cache split (e.g. a third `⚡cache` segment or an
      expandable breakdown matching the done-task drill-down's Input/Cache write/Cache read/Output convention) — wire it
      into both existing call sites: the Fleet table's per-task badge (`SlotTable` in `dashboard/src/     layout.tsx`)
      and the Agents-panel per-session badge, so `main`/review/custom/plan_reconciler all pick it up from the one shared
      component. Done-when: a Fleet row with real cache hits visibly shows the split, not just blended input/output. —
      `agent-orchestrator@956e675` (an optional `⚡{cache read}` segment appears only when cache activity is non-zero —
      a zero-cache session renders byte-identical to before; full write/read breakdown moved into the tooltip).
- [x] 5. ✅ [UI] P2. Render `tasks_completed` next to the tmux badge in `SlotTable` (`dashboard/src/layout.tsx`) so a
      slot that has run many sequential tasks is visibly distinguishable from a freshly-spun-up one. Done-when: a slot
      with N recorded `SlotHistoryRow`s shows N in the Fleet table. — `agent-orchestrator@956e675`
      (`data-testid="slot-tasks-completed"`, hidden when 0 to avoid noise on idle/fresh slots).
- [x] 6. ✅ [REVIEW] P2. Add/extend a Playwright regression spec covering both new pieces of UI (cache split rendering +
      tasks-completed count) per `/codex/06-coding-standards/ui-testing-layers.md`'s pw:L2 gate — cite the spec file and
      a passing run before ticking the two `[UI]` todos above as done. — `agent-orchestrator@956e675`
      `dashboard/tests/e2e/fleet-token-cache-badge.spec.ts` (2 tests) + extended `seed_e2e_state.py`'s slot-1 fixture
      with real cache tokens + 3 `SlotHistoryRow`s. **pw:L2 ✓** —
      `npx playwright test     tests/e2e/fleet-token-cache-badge.spec.ts tests/e2e/provider-badge.spec.ts` → 4 passed
      (both specs, confirming no regression on the pre-existing provider badge sharing the same fixture row).
- [x] 7. ✅ [INFRA] P3. `bash scripts/quality-gates.sh` green in `agent-orchestrator/`, ship via
      `bash scripts/quickmerge.sh "<msg>" --agent --files '<paths>'`, cite the resulting commit sha(s) on every todo
      above, then archive this plan (6-step ritual) once all todos are `[x]` and unlocked. —
      `agent-orchestrator@956e675` landed on `live-defi-rollout` (`bash scripts/quality-gates.sh --no-fix`:
      ruff/basedpyright/2423 pytest passed/tsc/vitest all green). Plan archival deferred — see Progress Log (this plan
      doc itself is still uncommitted in unified-trading-pm, blocked by unrelated concurrent activity on this shared
      clone; see Progress Log for detail — do not archive until it lands).

## Progress Log

- **2026-08-05 (interactive session)**: All 7 todos shipped in one commit, `agent-orchestrator@956e675`, landed on
  `live-defi-rollout` — full `quality-gates.sh` green (2423 pytest + tsc + vitest + 2 Playwright specs). This plan doc
  ITSELF failed to land in `unified-trading-pm` on the first two attempts: attempt 1 hit a pre-existing
  `finalize-plan-coverage` QG failure unrelated to this doc (traced to another uncommitted doc in the same shared slot-2
  clone, not touched); attempt 2 (after that checker was apparently fixed by whatever else is active in this clone) got
  further but failed at quickmerge's Stage 5 stash/merge step:
  `error: Your local changes to the following files would be overwritten by merge: plans/active/ci_pipeline_speed_and_cost_redesign_2026_08_05.md`
  — a file this session never touched. `git stash list` at that point showed 12 pre-existing `autostash` entries plus
  the failed attempt's own `quickmerge-48573` stash, strongly indicating another process (scheduled hygiene/cron, or a
  concurrent session) is actively cycling quickmerge/pull against this exact clone right now. Per multi-agent safety
  rules (never touch a foreign dirty file, never pop/drop a stash not yours), this session did NOT attempt to resolve
  the conflict or touch `ci_pipeline_speed_and_cost_redesign_2026_08_05.md` — stopped retrying and left this doc
  uncommitted rather than risk entangling someone else's in-flight WIP. **Next session picking this up**: retry
  `bash scripts/quickmerge.sh "docs(plans): add ao_fleet_cache_tokens_and_task_count_2026_08_05 + flip todos 1-7" --agent --files "plans/active/ao_fleet_cache_tokens_and_task_count_2026_08_05.md"`
  once `git status`/`git stash list` show the tree quiet (no unfamiliar modified files, stash count not still climbing);
  if it lands clean, this plan is fully done and should go through the 6-step archival ritual immediately per the
  plan-completion-and- archival-discipline HARD RULE.
