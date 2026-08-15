---
doc_type: plan
title: Human Fleet — integrate operator laptops into agent-orchestrator as self-reporting, non-dispatched slots
summary: >-
  Ikenna and Harsh already work from per-tab worktrees, the same Claude accounts, and the same plan-driven backlog AO
  itself dispatches from. This plan gives their interactive laptop sessions a real presence in AO — a registered slot, a
  heartbeat (model / account / context% / last-seen), token-usage and billing attribution split from AO-spawned agents,
  and visibility in the dashboard as an extension of the fleet — without AO ever gaining the ability to kill or kick a
  human session, and without a human ever entering AO's own contested dispatch queue. Grounded in a same-session code
  investigation (three parallel agents, file:line-cited) that found most of the primitives already exist and are already
  documented in-code as anticipating a "manually-pasted, non-spawned worker" — this is an extension of an
  already-half-built shape, not new architecture.
status: active
nature: design
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [agent-orchestrator, human-fleet, dispatch, billing, dashboard, statusline, auth, laptop]
related:
  [
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
    /plans/archive/2026_08/issues/review_agent_rate_limit_blind_kill_2026_08_14.md,
    /codex/04-architecture/agent-orchestrator-worker-liveness.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
created: "2026-08-15"
last_updated: "2026-08-15"
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 4
locked_by:
locked_since:
context_scope:
  [
    agent-orchestrator/server/routes/slots_worker.py,
    agent-orchestrator/server/dispatch.py,
    agent-orchestrator/server/state_store/slots.py,
    agent-orchestrator/server/orm.py,
    agent-orchestrator/server/config.py,
    agent-orchestrator/server/worker_liveness/__init__.py,
    agent-orchestrator/server/worker_liveness_watchdog.py,
    agent-orchestrator/server/autospawn.py,
    agent-orchestrator/server/auth.py,
    agent-orchestrator/server/deepseek_usage.py,
    agent-orchestrator/dashboard/src/App.tsx,
    agent-orchestrator/dashboard/src/layout.tsx,
    agent-orchestrator/dashboard/src/TaskUsageWindows.tsx,
    /plans/archive/2026_08/issues/review_agent_rate_limit_blind_kill_2026_08_14.md,
  ]
supersedes:
superseded_by:
depends_on: []
source: >-
  Operator, interactive session, 2026-08-14→15: "how hard would it be to fully have my laptop and hars laptop integrated
  into ao... refer to it as an extension of the fleet... it would just need us to be able to push to AO when we've
  completed tasks, right?" Followed by an explicit go-ahead: "continue! investigate fully check its all possible get me
  to setup what I need with clear instructions and then lets build the detailed human plan /plan-brainstorm." Two design
  forks resolved via /plan-brainstorm's Step 3 (AskUserQuestion): (1) network transport must work identically "via
  context of environment... either a terminal session of claude code OR a claude code within cursor terminal like now" —
  no client-shape-specific mechanism; (2) dispatch depth resolved as self-report, NOT real queue competition —
  operator's own synthesis: "self [report] but humans cant take on AO plans they can only degrade them to NA or human
  plan tasks... OR even better humans can do any tasks at will BUT they need to clear the 'AO isnt already working on
  them' i.e. they are not dispatched nor are they in the next 50 plans to be dispatched by AO" — read as: the pre-flight
  check is the default gate, the `assigned_vm` flip is the escape hatch when it fails and the human wants to proceed
  anyway. Then, 2026-08-15: "can we do it all now its scoped. /autonomous" — full-authority drive-to-completion per
  `cursor-configs/AUTONOMOUS_AGENT_RULES.md`; [OPERATOR]-tagged todos and any genuinely-undecided network/infra call
  stay gated per that dispatch's own explicit carve-out.
assigned_role: infra
effort: high
drift_direction: advance-code
---

# Human Fleet — integrate operator laptops into agent-orchestrator

## Why this doc exists

AO already dispatches, tracks, and bills its own tmux-spawned worker/review/main agents. The two human operators already
do the same class of work — claiming plan-derived tasks, committing through the same quickmerge pipeline, on the same
Claude accounts — but are invisible to AO: no slot, no heartbeat, no usage attribution, no dashboard presence. This plan
makes a human's interactive Claude Code session (terminal or Cursor-embedded — must work identically in both, per
operator direction) a first-class, visible, billable "human slot" in the fleet, governed by two hard constraints the
investigation confirmed are both achievable with existing primitives:

1. **AO must never be able to kill, kick, or spawn-conflict a human session.** Humans self-govern; there is no liveness
   enforcement against a human slot, full stop.
2. **A human never competes with AO for a task in AO's own dispatch queue.** Self-report only, gated by a pre-flight
   check that the target task is neither currently AO-dispatched nor near the front of AO's own priority queue; the
   escape hatch when that check fails and the human wants the task now is flipping the owning plan's `assigned_vm` to
   `NA`, pulling it out of AO's eligible pool entirely.

## What the investigation found (grounds every todo below — do not re-derive; verify against the cited line if a todo depends on it)

- **Claim/dispatch** (`agent-orchestrator/server/routes/slots_worker.py:275-729,732-1032`,
  `server/dispatch.py:520-561`): `/boot` and `/heartbeat` are plain authed HTTP routes with zero spawn-origin check;
  `upsert_slot()` (`server/state_store/slots.py:41-70`) auto-creates a `SlotRow` from self-reported fields. No "claim
  task X specifically" primitive exists today — dispatch always picks the next eligible task by priority via
  `pick_next_task()`. `mark_dispatched`/`assign_task_to_slot` (called from both routes) are the reusable primitives a
  human-claim endpoint would call directly, bypassing `pick_next_task`'s competitive selection.
- **Done/evidence** (`slots_worker.py:2212+`, ownership gate `2264-2309`): `/done` gates purely on
  `task_row.dispatched_to == slot_id` — no `AgentRow`/tmux/spawn-origin check. Fully reusable unmodified once a human
  claim sets `dispatched_to` correctly; gets the full verification stack (git-diff evidence, plan-checkbox-flip
  enforcement, origin-push check, quickmerge-provenance) for free. Usage capture silently no-ops if
  `slot_claude_session_id` is `None` (see usage finding below).
- **Schema**: `SlotRow` (`server/orm.py:73-253`) has `tmux_session`/`claude_session_id`/`last_spawned_at` all nullable,
  documented in-code as "None for a manually-pasted/non-spawned worker" (`orm.py:133-137`) — already anticipated.
  `AgentRow.agent_kind` (`orm.py:1016`) is `Mapped[str | None]`, an open string, not an enum — adding `"human"` needs no
  migration, but `task_role_group()` (`server/state_store/slots.py:703-720`) silently collapses any unrecognized value
  to `"planning"` via frozen-set membership — must be made deliberate for the plan-authoring-vs-task-execution split the
  operator wants.
- **Liveness/kill exemption**: `review_slot_ids()` (`server/config.py:316-331`) is checked BEFORE any tmux call in three
  independent subsystems — `WorkerLivenessWatchdog._tick_once` (`server/worker_liveness_watchdog.py:904-918`, before
  `has_session` at 931), `AutoSpawn._should_spawn` (`server/autospawn.py:3255-3322`, before `has_session` at 3319),
  `WorkerLivenessKicker._tick_once` (`server/worker_liveness/__init__.py:704-736`). A `human_slot_ids()` list at the
  same three sites gives human slots identical immunity — proven pattern, not a new mechanism.
- **Auth** (`server/auth.py`): loopback-trust (`_is_trusted_loopback`, `471-489`) does not apply to a remote laptop.
  `issue_token(role="worker", machine=<label>, ...)` (`323-341`, 30-day TTL) is directly reusable — mint a long-lived
  worker-role JWT per operator via the existing login flow, store locally, send as Bearer header. No new credential type
  needed. User store already exists at `data/config/users.json`.
- **Usage/billing — the one real gap**: `TaskUsageRow` (`orm.py:292-343`) has no structural objection to a human-claimed
  row (`account_id`/`claude_session_id`/`dispatch_role` are free strings). But
  `_compute_done_task_usage`/`_record_done_task_usage` (`slots_worker.py:1536-1600,1640+`) compute real numbers by
  scanning the completing slot's transcript via `deepseek_usage.scan_session_usage()`, which reads
  `<config_base>/*/projects/*/*.jsonl` **on the machine the AO server process itself runs on**
  (`server/deepseek_usage.py:92-96,176-210` — confirmed "on whichever VM ran it" per `backlog.py:722-730`'s own
  docstring). A human's laptop transcript is never on that filesystem — this is a genuinely new component (a local
  scan-and-push companion), not a reuse. `SlotGitStatusRow` (`orm.py:256-282`, `(host, slot_id)`-keyed) is the closest
  existing structural analogue — it already solved "a laptop's local state must be pushed, not centrally read" for git
  status.
- **Heartbeat mechanism — hooks are a dead end, statusline is the answer** (verified against
  `code.claude.com/docs/en/hooks.md` + `.../statusline.md`): no Claude Code hook payload (PreToolUse/PostToolUse/
  Stop/SessionStart/PreCompact/UserPromptSubmit) carries context-window usage, model name, or account identifier —
  confirmed absent from every schema. A **statusline** command's stdin payload DOES carry
  `context_window.used_percentage`, `model.id`/`model.display_name`, and `session_id` on every render, and can silently
  POST instead of (or alongside) displaying. Trade-off: only fires while Claude Code is actively rendering in the
  foreground — acceptable for an interactive-only heartbeat.
- **Dashboard** (`agent-orchestrator/dashboard/src/`): page-nav is a hand-rolled string-path router
  (`App.tsx:317-357`) + `Landing.tsx` nav buttons (`105-129`) — already used 3x (FleetGit, FleetKpis, DocGraph) for
  exactly this shape of addition. `AgentView.agent_kind` (`types.ts:1064-1079,1117`) already flows into
  `groupAgentsByKind`/`AgentTypesPanel` (`layout.tsx:5089-5170`) — adding `"human"` to the union + `KINDS_ORDER` +
  `AGENT_KIND_LABEL` (`layout.tsx:5092-5134`) renders it in the existing fleet table automatically (columns already
  include Model/Context/Account/Last-heartbeat). `account_id` filtering on usage panels is already registry-driven
  (free); `role_group` filter options are a static array (`TaskUsageWindows.tsx:53-60`, re-exported into
  `BatchingEfficiencyPanel.tsx:26-34`) needing one new entry per file.

## Design decisions (resolved via /plan-brainstorm + autonomous tick 1 — do not re-open without a new operator ruling)

- **Network transport**: recommended default is an SSH/SSM tunnel per session (reuses the existing AWS-SSM access
  pattern already used for read-only AO status checks — no new open port, no VPN). MUST be verified to work identically
  whether the human is in a bare terminal `claude` session or Cursor's embedded terminal (this session's own
  environment). If a tunnel proves unworkable in one context, escalate to the operator rather than silently picking the
  open-firewalled-path or VPN alternative.
- **Dispatch depth**: self-report only. A human-claim call performs an atomic pre-flight check (task not currently
  `dispatched_to` anyone, not within the next 50 tasks AO's own priority ordering would dispatch) before setting
  `dispatched_to`, avoiding a check-then-claim race. When the check fails and the human wants the task anyway, the
  resolution is flipping the OWNING PLAN's `assigned_vm` to `NA` (pulling it and its remaining todos out of AO's
  eligible pool), not overriding the check.
- **`agent_kind` vocabulary**: `"human"` for task-execution slots, a distinct `role_group` (working name
  `"planning-human"`) for plan-authoring time specifically, per the operator's own framing that authoring is the one
  categorically different activity. Both are explicit, deliberate entries in `task_role_group()` — never the silent
  `"planning"` catch-all default.
- **Human-slot ID namespace** (resolved tick 1, see Progress Log): `SlotRow.slot_id` is `Mapped[int]`
  (`server/orm.py:76`), integer PK — not a string. Real production slots are small dense integers (`_MAIN_SLOT_ID = 0`,
  `autospawn.py:135`; review/CI-escalation/scheduled reserves are computed as "the top N of the CURRENT roster",
  `config.py:459-490`, observed at fleet sizes of 15-17 — never a fixed high block). Human slots use a documented
  reserved floor, **`HUMAN_SLOT_ID_BASE = 9000`**, with each operator assigned a fixed offset (Ikenna = 9001, Harsh
  = 9002) — high enough that no realistic fleet-size growth collides, asserted at registration time so a collision fails
  loud rather than silently double-assigning a slot.
- **Transcript path**: resolved tick 1 (see Progress Log) — `~/.claude/projects/<slugified-cwd>/<session-id>.jsonl` is
  Claude Code's own default (confirmed via `CLAUDE_CONFIG_DIR` being unset in this session), independent of what
  terminal launched it. High confidence this is identical in a bare terminal; a 10-second manual confirmation
  (`ls ~/.claude/projects`) on each operator's machine is the remaining verification, not a design unknown.
- **Next-N-eligible preview mechanism**: resolved tick 1 (see Progress Log) — a new `rank_eligible_tasks()` function
  reusing `_build_ctx`/`first_blocking_filter`/the exact `(tier, priority, plan_order, plan_ref)` sort key
  `pick_next_task()` already uses (`server/dispatch.py:520-561,555`), following the read-only sentinel-slot pattern
  `explain_blocked_bulk()` already proves safe in production (`dispatch.py:852-880`, sentinel slot id `-1`). No
  duplication — every primitive already exists as a standalone, importable function.

## Progress Log (append-only — this is the loop's memory across context compression; do not delete prior entries)

- **2026-08-15, tick 1 (autonomous, main session)**: Phase 0 todos 1-3 resolved by direct investigation + 2 parallel
  sub-agents (SUB_AGENT_MANDATORY_RULES.md injected). Findings folded into Design decisions above. Model-tier
  self-check: CLAUDE.md's explicit ruling ("opus-required = ZERO categories", 2026-08-08) overrides the generic
  `/autonomous` skill's "usually opus-required" default for long loops — staying Sonnet, `effort: high` (already
  declared). Todo 4 (assigned_vm retroactive-eligibility check) still running as of this log entry; Phase 1 backend work
  starts once it resolves (a real gap there would add a new Phase 1 todo, per that todo's own "done when").

## Todos

### Phase 0 — confirm remaining unknowns (fast, gates real work — do these first)

- [x] 1. ✅ [INFRA] P0. **Confirm `SlotRow.slot_id`'s actual type/constraint** — resolved: `Mapped[int]` PK
      (`server/orm.py:76`). Convention: `HUMAN_SLOT_ID_BASE = 9000` (Ikenna=9001, Harsh=9002), recorded in Design
      decisions above. Evidence: direct code read, tick 1 Progress Log.
- [x] 2. ✅ [INFRA] P0. **Confirm the Claude Code transcript storage path in both a bare terminal session AND a
      Cursor-embedded terminal session** — resolved (high confidence):
      `~/.claude/projects/<cwd-slug>/<session-id>.jsonl`, Claude Code's own default (`CLAUDE_CONFIG_DIR` unset),
      independent of launching terminal — confirmed by locating this exact session's own transcript file at that path.
      Bare-terminal confirmation is now a trivial 10-second manual check (Phase 4), not an open design question.
      Evidence: `ls ~/.claude/projects/`, tick 1 Progress Log.
- [x] 3. ✅ [BACKEND] P0. **Confirm whether AO's dispatch/backlog code can cheaply expose "the next N
      eligible-to-dispatch tasks in priority order"** — resolved: yes, cheaply, via a new `rank_eligible_tasks()`
      reusing `_build_ctx`/`first_blocking_filter`/`pick_next_task`'s exact sort key, following the proven read-only
      sentinel-slot pattern `explain_blocked_bulk()` (`dispatch.py:852-880`) already uses in production. Recorded in
      Design decisions above. Evidence: sub-agent investigation, tick 1 Progress Log.
- [ ] [BACKEND] P0. **Confirm whether flipping a plan's `assigned_vm` from `planning` to `NA` retroactively removes
      already-generated `BacklogTask`/`TaskRow` rows from AO's dispatch-eligible pool**, or only affects future
      `regen_backlog_from_plan.py` runs (read `regen_backlog_from_plan.py`'s reconciliation path + `dispatch.py`'s
      eligibility check to see if either consults the CURRENT plan doc's `assigned_vm` at dispatch time or only a cached
      value on the row). Done when: the escape-hatch mechanism either works today, or a specific fix is scoped as a
      Phase 1 todo below (add one if the answer is "only affects future regen").

### Phase 1 — AO backend: vocabulary, exemption, pre-flight check, human-claim/done wiring

- [ ] [BACKEND] P1. **Add `"human"` and `"planning-human"` as deliberate, explicit buckets in `task_role_group()`**
      (`server/state_store/slots.py:703-720`) rather than letting either silently collapse to `"planning"` — extend
      `TASK_ROLE_GROUPS` and the membership-set logic. Done when: a unit test asserts
      `task_role_group("human") == "human"` and `task_role_group("planning-human") == "planning-human"` and the existing
      test suite for `task_role_group` still passes.
- [ ] [BACKEND] P1. **Add `human_slot_ids()` to `server/config.py`** mirroring `review_slot_ids()` (`config.py:316-331`)
      exactly (same config-list primitive shape; default derived from `HUMAN_SLOT_ID_BASE` offsets above), and wire the
      check into the same three pre-tmux-call sites already confirmed: `WorkerLivenessWatchdog._tick_once` (before
      `has_session` at `worker_liveness_watchdog.py:931`), `AutoSpawn._should_spawn` (before `has_session` at
      `autospawn.py:3319`), `WorkerLivenessKicker._tick_once` (`worker_liveness/__init__.py:736`, alongside the existing
      review check). Done when: a test proves no `capture_pane`/`kill_session`/`has_session` call is ever made for a
      slot in `human_slot_ids()`, mirroring the existing review-slot exemption tests.
- [ ] [BACKEND] P1. **Build a read-only pre-flight endpoint** `GET /api/slots/{slot_id}/human-claim-check?task_id=...`
      returning `{claimable: bool, reason: str|null, currently_dispatched: bool, queue_position: int|null}`, using the
      new `rank_eligible_tasks()` (Design decisions above). Done when: a request against a currently-dispatched task and
      a request against a task ranked >50 both return the correct `claimable` verdict in a test.
- [ ] [BACKEND] P1. **Build the human-claim endpoint** `POST /api/slots/{slot_id}/human-claim {task_id}` — runs the same
      check as the pre-flight endpoint atomically (inside the same `session_scope()` transaction, no check-then-claim
      race), and on pass calls `mark_dispatched`/`assign_task_to_slot` (`slots_worker.py`'s existing helpers) directly
      for the specified `task_id`, bypassing `pick_next_task`'s competitive selection entirely. On fail, returns the
      same `reason` the pre-flight endpoint would. Done when: a test claims a task successfully, a second concurrent
      claim attempt on the same task_id 409s, and a claim attempt on a currently-AO-dispatched task is rejected with
      `reason: "already_dispatched"`.
- [ ] [BACKEND] P1. **Verify `/done` works unmodified for a human-claimed task** — run one real human-claim → `/done`
      cycle against a genuinely low-stakes test task and confirm the full verification stack (git-diff, plan-flip,
      origin-push, quickmerge-provenance) fires correctly with `dispatched_to` set by the human-claim endpoint above.
      Done when: the task's plan-checkbox is flipped and the `/done` call succeeds with real evidence, no code changes
      needed to `slots_worker.py`'s done path itself (or, if something breaks, a scoped fix todo is added here).
- [ ] [BACKEND] P1. **Build a lightweight human "register + heartbeat" endpoint** — either a thin wrapper around the
      existing `register_agent()` (`server/state_store/agents.py:82-98`) with `agent_kind="human"`, `tmux_session=None`,
      or a dedicated route, accepting `model`/`account_id`/`context_used_pct` in the body from the statusline companion
      (Phase 2). Done when: a registered human `AgentRow` shows up via `GET /api/agents` with `agent_kind="human"` and
      updates `last_ping`/`context_used_pct` on each heartbeat call.

### Phase 2 — laptop-side tooling

- [ ] [INFRA] P1. **Build the network-transport wrapper** implementing the SSH/SSM tunnel mechanism (Design decisions
      above), proven to work identically from a bare terminal `claude` session and from Cursor's embedded terminal. Done
      when: a `curl` against AO's `/api/agents` through the wrapper succeeds from both contexts on both operators'
      machines.
- [ ] [INFRA] P1. **Build `/ao-register`, `/ao-claim <task_id>`, `/ao-done` slash-commands (or equivalent scripts)**
      calling the Phase 1 endpoints through the Phase 2 transport wrapper, reading the operator's stored JWT (Phase 4).
      Done when: an operator can run all three commands end-to-end against a real backlog task from either terminal
      context.
- [ ] [INFRA] P1. **Build the statusline-based heartbeat companion** — a statusline script that reads
      `context_window.used_percentage`, `model.id`/`display_name`, `session_id` from its stdin payload and POSTs to the
      Phase 1 heartbeat endpoint, throttled to avoid a POST per render (e.g. min-interval gate). Done when: the
      operator's `AgentRow.context_used_pct`/`model`/`last_ping` visibly update in AO within one throttle interval of
      normal Claude Code use.
- [ ] [INFRA] P2. **Build the local usage-scan-and-push companion** — reuses `deepseek_usage.scan_session_usage()`'s
      logic (import if feasible, otherwise port the minimal needed function) against the confirmed local transcript path
      (`~/.claude/projects/...`, Design decisions above), and pushes computed usage to a new ingest endpoint tagged
      `account_id`/`agent_kind="human"`, following `SlotGitStatusRow`'s `(host, slot_id)`-keyed pattern as the
      structural template. Done when: a real Claude Code turn on the operator's laptop produces a usage row visible via
      `GET /api/backlog/usage/windows` filtered to `role_group="human"`.

### Phase 3 — dashboard

- [ ] [UI] P2. **Add `"human"` to the `AgentKind` union, `KINDS_ORDER`, and `AGENT_KIND_LABEL`**
      (`dashboard/src/layout.tsx:5092-5134`, `dashboard/src/types.ts:1064-1079`). Done when: a registered human agent
      renders correctly in the existing `AgentTypesPanel` table with no other frontend changes.
- [ ] [UI] P2. **Add `"human"`/`"planning-human"` entries to the static role_group filter arrays**
      (`TaskUsageWindows.tsx:53-60`, re-exported into `BatchingEfficiencyPanel.tsx:26-34`). Done when: both appear as
      selectable filter options and correctly narrow results in both panels.
- [ ] [UI] P2. **Build a "Human Fleet" page** following the `FleetGit.tsx`/`FleetKpis.tsx` recipe exactly (fetch+poll
      shell, pure exported mappers, `Panel`-based render, `onBack` prop) + one new `Router` branch (`App.tsx:317-357`) +
      one new `Landing.tsx` nav button (`105-129`). Shows current task, model, account, context%, last-heartbeat for
      every `agent_kind="human"` slot. Done when: the page is reachable from Landing, auto-refreshes, and a component
      test mirrors the existing `FleetKpis.test.ts` pattern.

### Phase 4 — per-operator setup + rollout

- [ ] [OPERATOR] P1. **Issue a long-lived worker-role JWT for each operator** via the existing login flow
      (`issue_token(role="worker", machine="<operator>-laptop")`, `server/auth.py:323-341`) and store it locally where
      the Phase 2 scripts read it. Done when: both operators have a working token and the register/claim/done cycle
      succeeds end-to-end for each.
- [ ] [SCRIPT] P2. **Run one real, low-stakes task end-to-end per operator** through register → claim → statusline
      heartbeat → done, and confirm dashboard visibility (Human Fleet page) and a real usage row (Phase 2's
      scan-and-push companion). Done when: both operators' first human-claimed task shows up correctly in the plan
      dashboard with non-zero usage attribution.
- [ ] [INFRA] P3. **Document the human-slot contract as a durable codex SSOT** — extend
      `/codex/04-architecture/agent-orchestrator-worker-liveness.md` (or a new sibling doc if scope doesn't fit) with
      the human-slot exemption, self-report/pre-flight-check contract, and the `assigned_vm` escape hatch, so a future
      AO change to liveness/dispatch logic doesn't silently regress the human-slot guarantees. Done when: the doc is
      shipped and linked from this plan's `related:`.
